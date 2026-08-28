"""
scripts/zalo_bao_cao_chua_follow.py
====================================
Xuất báo cáo Markdown: công chức CHƯA quan tâm OA và các số điện thoại HỎNG,
gom theo đơn vị, để gửi các đơn vị rà soát.

VÌ SAO CẦN
==========
Tin ôn tập hằng ngày chỉ tới được người đã quan tâm OA. Tính đến 28/08/2026 chỉ
327/543 công chức (60,2%) nhận được. Gắn nhãn không sửa được điều này — phải để
các đơn vị nhắc người của mình quan tâm OA, và rà lại những số sai trong danh bạ.

VÌ SAO PHẢI GỌI LẠI ZALO
========================
`zalo_tra_uid.py` chỉ lưu `zalo_user_id`, không lưu lý do thất bại. Nên không
phân biệt được trong cơ sở dữ liệu ai là "chưa quan tâm" và ai là "số hỏng" —
phải hỏi lại Zalo. Chỉ hỏi những người chưa có `user_id` nên nhanh.

Ba trạng thái Zalo trả về (giống `zalo_tra_uid.py`):
    error = 0     → đã quan tâm OA (không xuất hiện trong báo cáo này)
    error = -213  → có Zalo nhưng CHƯA quan tâm OA
    error = -201  → số không hợp lệ / không có tài khoản Zalo

CHẠY
====
    cd backend && source venv/bin/activate
    python scripts/zalo_bao_cao_chua_follow.py

    # đổi nơi lưu
    python scripts/zalo_bao_cao_chua_follow.py --ra docs/zalo-oa/bao-cao.md

⚠️ CHỈ ĐỌC. Không ghi cơ sở dữ liệu, không ghi gì lên OA, không tốn phí.

⚠️ DỮ LIỆU CÁ NHÂN (Nghị định 13/2023/NĐ-CP): file kết quả chứa họ tên và số
   điện thoại thật của công chức. File này KHÔNG được commit — đã có luật trong
   `.gitignore`. Gửi cho đơn vị qua kênh nội bộ, đừng đưa lên chỗ công khai.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from shared.database import create_db_engine, create_session_factory  # noqa: E402

from common_service.config import settings  # noqa: E402
from common_service.services.zalo.token_store import lay_access_token  # noqa: E402

_URL_PROFILE = "https://openapi.zalo.me/v2.0/oa/getprofile"
_NHIP_GIAY = 0.3

CHUA_FOLLOW = "CHUA_FOLLOW"
SO_HONG = "SO_HONG"
LOI_KHAC = "LOI_KHAC"

_SQL = text(
    """
    SELECT lk.so_dien_thoai,
           cc.ma_cc,
           cc.ho_ten,
           cc.chuc_vu,
           cc.is_active,
           COALESCE(dv.ten_don_vi, '(chưa rõ đơn vị)') AS ten_don_vi
      FROM common.zalo_lien_ket lk
      JOIN public.cong_chuc cc ON cc.id = lk.cong_chuc_id
      LEFT JOIN public.don_vi dv ON dv.id = cc.don_vi_id
     WHERE lk.zalo_user_id IS NULL
       AND lk.so_dien_thoai IS NOT NULL
     ORDER BY dv.ten_don_vi, cc.ho_ten
    """
)


async def _tra(client: httpx.AsyncClient, token: str, so: str) -> str:
    try:
        r = await client.get(
            _URL_PROFILE,
            headers={"access_token": token},
            params={"data": json.dumps({"phone": so})},
        )
        ma = r.json().get("error")
    except (httpx.HTTPError, ValueError):
        return LOI_KHAC
    if ma == -213:
        return CHUA_FOLLOW
    if ma == -201:
        return SO_HONG
    return LOI_KHAC if ma != 0 else CHUA_FOLLOW


def _bang(rows: list[dict]) -> list[str]:
    d: list[str] = [
        "| # | Mã CC | Họ tên | Chức vụ | Số điện thoại |",
        "|---:|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        ten = r["ho_ten"] + ("" if r["is_active"] else " _(đã nghỉ/chuyển)_")
        d.append(
            f"| {i} | {r['ma_cc']} | {ten} | {r['chuc_vu'] or ''} | `{r['so_dien_thoai']}` |"
        )
    return d


def _theo_don_vi(rows: list[dict]) -> list[str]:
    nhom: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        nhom[r["ten_don_vi"]].append(r)
    ra: list[str] = []
    for dv in sorted(nhom):
        ra += [f"#### {dv} — {len(nhom[dv])} người", ""] + _bang(nhom[dv]) + [""]
    return ra


async def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Báo cáo công chức chưa quan tâm OA")
    p.add_argument(
        "--ra",
        default="docs/zalo-oa/BAO_CAO_CHUA_QUAN_TAM_OA.md",
        help="Đường dẫn file kết quả",
    )
    p.add_argument("--ngay", default=None, help="Ngày ghi trên báo cáo (dd/mm/yyyy)")
    a = p.parse_args(argv)

    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    try:
        async with session_factory() as db:
            token = await lay_access_token(db)
            rows = [dict(r) for r in (await db.execute(_SQL)).mappings().all()]

        if not rows:
            print("Không còn ai thiếu user_id — mọi công chức đã quan tâm OA.")
            return 0

        print(f"Đang hỏi lại Zalo {len(rows)} số "
              f"(~{int(len(rows) * _NHIP_GIAY // 60)}p{int(len(rows) * _NHIP_GIAY % 60)}s)…")

        chua: list[dict] = []
        hong: list[dict] = []
        khac: list[dict] = []
        async with httpx.AsyncClient(timeout=25.0) as client:
            for i, r in enumerate(rows, 1):
                tt = await _tra(client, token, r["so_dien_thoai"])
                {CHUA_FOLLOW: chua, SO_HONG: hong}.get(tt, khac).append(r)
                if i % 50 == 0:
                    print(f"   {i}/{len(rows)}")
                await asyncio.sleep(_NHIP_GIAY)

        ngay = a.ngay or "____"
        md: list[str] = [
            "# Công chức chưa nhận được tin ôn tập qua Zalo OA",
            "",
            f"Ngày rà: **{ngay}** · Nguồn: Official Account Chi cục Hải quan Khu vực VIII",
            "",
            "> ⚠️ Văn bản chứa số điện thoại cá nhân của công chức. Gửi qua kênh nội bộ,",
            "> không đăng nơi công khai (Nghị định 13/2023/NĐ-CP).",
            "",
            "## 1. Vì sao có văn bản này",
            "",
            "Từ 8h sáng hằng ngày, hệ thống gửi 1 câu hỏi ôn tập đánh giá năng lực qua",
            "Zalo. Tin **chỉ tới được người đã quan tâm (follow) Official Account** của",
            "Chi cục. Những người trong danh sách dưới đây hiện **không nhận được**.",
            "",
            "## 2. Tổng hợp",
            "",
            "| Nhóm | Số người | Đơn vị cần làm gì |",
            "|---|---:|---|",
            f"| Chưa quan tâm OA | **{len(chua)}** | Nhắc công chức tìm và quan tâm OA |",
            f"| Số điện thoại hỏng | **{len(hong)}** | Rà lại số trong danh bạ, báo về để cập nhật |",
        ]
        if khac:
            md.append(f"| Chưa xác định | {len(khac)} | Hệ thống sẽ rà lại |")
        md += [
            f"| **Cộng** | **{len(rows)}** | |",
            "",
            "## 3. Cách quan tâm OA",
            "",
            "Mở Zalo → **Tìm kiếm** → gõ **Chi cục Hải quan khu vực VIII** → chọn tài",
            "khoản có dấu tích cam → bấm **Quan tâm**.",
            "",
            "Quan tâm xong, tin ôn tập sẽ tự đến từ sáng hôm sau, không phải đăng ký gì thêm.",
            "",
            "## 4. Danh sách chưa quan tâm OA",
            "",
        ]
        md += _theo_don_vi(chua) if chua else ["_(không có)_", ""]
        md += ["## 5. Danh sách số điện thoại hỏng", "",
               "Số không tồn tại trên Zalo — nhiều khả năng ghi sai trong danh bạ hoặc",
               "công chức đã đổi số. Đơn vị rà lại và báo về để cập nhật.", ""]
        md += _theo_don_vi(hong) if hong else ["_(không có)_", ""]
        if khac:
            md += ["## 6. Chưa xác định được", "",
                   "Zalo trả lỗi khác khi tra. Hệ thống sẽ rà lại ở lần chạy sau.", ""]
            md += _theo_don_vi(khac)

        ra = Path(a.ra)
        ra.parent.mkdir(parents=True, exist_ok=True)
        ra.write_text("\n".join(md) + "\n", encoding="utf-8")

        print("─" * 72)
        print(f"Chưa quan tâm OA : {len(chua)}")
        print(f"Số hỏng          : {len(hong)}")
        if khac:
            print(f"Chưa xác định    : {len(khac)}")
        print(f"→ đã ghi {ra}")
        return 0

    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1:])))
