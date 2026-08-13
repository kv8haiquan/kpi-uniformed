"""
scripts/zalo_xem_template.py
=============================
Tra cứu chi tiết template ZNS: trạng thái, danh sách tham số kèm KIỂU dữ liệu,
và dữ liệu mẫu Zalo chấp nhận.

Dùng để đối chiếu template thật với code trước khi bật gửi — sai kiểu tham số
là lỗi im lặng đắt nhất: Zalo từ chối từng tin, không báo trước.

    cd backend && source venv/bin/activate
    python scripts/zalo_xem_template.py                 # tất cả template của OA
    python scripts/zalo_xem_template.py 620450 622517   # chỉ vài ID
    python scripts/zalo_xem_template.py --doi-chieu     # KIỂM code vs template

`--doi-chieu` là cửa kiểm bắt buộc trước khi bật gửi: nó lấy các template_id
đang đặt trong .env, so bộ tham số code sinh ra với khai báo thật của Zalo,
và thoát mã 1 nếu lệch.

CHỈ ĐỌC — không gửi tin, không tốn phí. Riêng bảng common.zalo_token có thể
được ghi khi access_token hết hạn và phải refresh (đó là cơ chế bình thường).
"""

from __future__ import annotations

import asyncio
import sys
from datetime import date, time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.database import create_db_engine, create_session_factory  # noqa: E402

from common_service.config import settings  # noqa: E402
from common_service.services.zalo.token_store import lay_access_token  # noqa: E402

_URL_ALL = "https://business.openapi.zalo.me/template/all"
_URL_INFO = "https://business.openapi.zalo.me/template/info/v2"
_URL_SAMPLE = "https://business.openapi.zalo.me/template/sample-data"


async def _goi(client: httpx.AsyncClient, url: str, token: str, params: dict) -> dict:
    r = await client.get(url, headers={"access_token": token}, params=params)
    try:
        return r.json()
    except ValueError:
        return {"error": -1, "message": f"HTTP {r.status_code} không phải JSON"}


def _in_tham_so(data: dict) -> None:
    ds = data.get("listParams") or []
    if not ds:
        print("      (không khai tham số nào)")
        return
    for p in ds:
        bat_buoc = "bắt buộc" if p.get("require") else "tùy chọn"
        print(
            f"      - {p.get('name'):<16} kiểu={p.get('type'):<10} "
            f"{bat_buoc:<9} tối đa {p.get('maxLength')} ký tự"
        )


async def _doi_chieu(client: httpx.AsyncClient, token: str) -> int:
    """So bộ tham số code sinh ra với template thật đang cấu hình trong .env.

    Đây là cửa kiểm cuối trước khi bật gửi: sai một tham số là Zalo từ chối
    lặng lẽ từng tin, không có cảnh báo nào khác.
    """
    from common_service.services.zalo.templates import DANH_MUC_MAU, ThongTinGui

    mau_thu = dict(
        ho_ten="Nguyễn Văn A",
        ngay_hop=date(2026, 8, 20),
        gio_bat_dau=time(14, 0),
        link_url=None,
        cuoc_hop_id="7279683b-49fb-446d-aa48-6e66f155f314",
    )

    # Mỗi template chỉ cần kiểm 1 lần dù nhiều loại thông báo dùng chung
    da_kiem: dict[str, str] = {}
    so_loi = 0

    for loai, mau in DANH_MUC_MAU.items():
        tid = getattr(settings, mau.khoa_config, "")
        if not tid:
            print(f"⚠️  {loai:<14} — chưa đặt {mau.khoa_config.upper()} trong .env")
            so_loi += 1
            continue
        if tid in da_kiem:
            continue
        da_kiem[tid] = loai

        info = await _goi(client, _URL_INFO, token, {"template_id": tid})
        if info.get("error") != 0:
            print(f"❌ {loai:<14} [{tid}] không đọc được: {info.get('message')}")
            so_loi += 1
            continue

        d = info.get("data") or {}
        that = {p["name"]: p for p in (d.get("listParams") or [])}
        code = mau.tham_so(ThongTinGui(doi_tuong_type=loai, **mau_thu))

        thua = set(code) - set(that)
        thieu = {k for k, p in that.items() if p.get("require")} - set(code)

        # Kiểu của `thoi_gian` phải khớp cờ thoi_gian_kieu_date
        kieu_that = (that.get("thoi_gian") or {}).get("type")
        lech_kieu = kieu_that and mau.thoi_gian_kieu_date != (kieu_that == "DATE")

        if not thua and not thieu and not lech_kieu:
            gio = "có giờ" if not mau.thoi_gian_kieu_date else "chỉ ngày"
            print(f"✅ {loai:<14} [{tid}] khớp — {sorted(code)} ({gio})")
            continue

        so_loi += 1
        print(f"❌ {loai:<14} [{tid}] {d.get('templateName')}")
        if thua:
            print(f"      code gửi thừa : {sorted(thua)} → Zalo từ chối cả tin")
        if thieu:
            print(f"      code gửi thiếu: {sorted(thieu)} → Zalo từ chối cả tin")
        if lech_kieu:
            print(
                f"      thoi_gian: template khai {kieu_that}, code đang coi là "
                f"{'DATE' if mau.thoi_gian_kieu_date else 'STRING'} → sửa cờ "
                f"thoi_gian_kieu_date của {loai} trong templates.py"
            )

    print()
    if so_loi:
        print(f"❌ {so_loi} chỗ lệch — KHÔNG bật gửi cho tới khi hết lệch.")
        return 1
    print("✅ Code khớp toàn bộ template. An toàn để gửi.")
    return 0


async def main() -> int:
    tham_so = [x.strip() for x in sys.argv[1:] if x.strip()]
    che_do_doi_chieu = "--doi-chieu" in tham_so
    ids_loc = [x for x in tham_so if not x.startswith("--")]

    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    async with session_factory() as db:
        token = await lay_access_token(db)
    await engine.dispose()

    async with httpx.AsyncClient(timeout=30.0) as client:
        if che_do_doi_chieu:
            return await _doi_chieu(client, token)

        ds = await _goi(client, _URL_ALL, token, {"offset": 0, "limit": 100})
        if ds.get("error") != 0:
            print(f"Lỗi lấy danh sách template: {ds}")
            return 1

        danh_sach = ds.get("data") or []
        if ids_loc:
            danh_sach = [t for t in danh_sach if str(t.get("templateId")) in ids_loc]
            thieu = set(ids_loc) - {str(t.get("templateId")) for t in danh_sach}
            if thieu:
                print(f"⚠️  Không thấy template: {', '.join(sorted(thieu))}\n")

        print(f"Tìm thấy {len(danh_sach)} template\n" + "=" * 72)

        for t in danh_sach:
            tid = str(t.get("templateId"))
            print(f"\n[{tid}] {t.get('templateName')}")
            print(f"   Trạng thái : {t.get('status')}")
            print(f"   Chất lượng : {t.get('templateQuality')}")
            print(f"   Giá        : SĐT {t.get('price')}đ")

            info = await _goi(client, _URL_INFO, token, {"template_id": tid})
            if info.get("error") == 0:
                d = info.get("data") or {}
                print("   Tham số:")
                _in_tham_so(d)
                if d.get("timeout"):
                    print(f"   Timeout    : {d['timeout']}s")
            else:
                print(f"   ⚠️  info lỗi: {info.get('error')} {info.get('message')}")

            sm = await _goi(client, _URL_SAMPLE, token, {"template_id": tid})
            if sm.get("error") == 0 and sm.get("data"):
                print(f"   Dữ liệu mẫu: {sm['data']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
