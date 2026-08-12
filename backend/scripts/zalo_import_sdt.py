#!/usr/bin/env python3
"""
scripts/zalo_import_sdt.py
===========================
Import danh sách số điện thoại công chức để gửi thông báo Zalo.

MẶC ĐỊNH LÀ CHẠY KHÔ (dry-run): chỉ đọc file, chuẩn hóa, đối chiếu với
public.cong_chuc và in báo cáo. KHÔNG ghi gì vào database.
Muốn ghi thật phải thêm cờ --ghi.

GHI VÀO ĐÂU
===========
Chỉ ghi vào `common.zalo_lien_ket`. KHÔNG đụng `public.cong_chuc.so_dien_thoai`
— theo quy tắc trong CLAUDE.md, module mới chỉ được ĐỌC bảng schema public.

CÁCH KHỚP NGƯỜI
===============
Ưu tiên theo thứ tự:
  1. Cột mã công chức (ma_cc) nếu file có — chính xác tuyệt đối
  2. Họ và tên (đã chuẩn hóa) — dùng khi file chỉ có tên

Khớp theo tên chỉ an toàn khi KHÔNG có tên trùng ở cả hai phía; script tự kiểm
tra điều này và từ chối khớp những tên xuất hiện nhiều lần (đưa vào diện rà tay).
Nếu cả hai phía đều có ngày sinh, script đối chiếu thêm để phát hiện trùng tên
khác người.

ĐỊNH DẠNG FILE ĐẦU VÀO
======================
Excel (.xlsx) hoặc CSV. Script tự dò dòng tiêu đề (không bắt buộc ở dòng 1 —
file thực tế thường có mấy dòng quốc hiệu/tiêu đề ở trên) và tự dò tên cột:

    Mã CC     : ma_cc | ma_cong_chuc | "Mã CC"            (không bắt buộc)
    Họ tên    : ho_ten | "Họ và tên" | "Họ tên"
    Số ĐT     : so_dien_thoai | sdt | "Số điện thoại"
    Ngày sinh : ngay_sinh | "Ngày tháng năm sinh"          (không bắt buộc)

CÁCH DÙNG
=========
    cd backend && source venv/bin/activate

    # 1. Chạy khô, xem báo cáo + xuất file kiểm tra
    PYTHONPATH=$PWD python scripts/zalo_import_sdt.py "danh_sach.xlsx" \
        --xuat-md ../docs/zalo-oa/BAO_CAO_IMPORT_SDT.md

    # 2. Ghi thật (sau khi đã xem báo cáo và đồng ý)
    PYTHONPATH=$PWD python scripts/zalo_import_sdt.py "danh_sach.xlsx" --ghi
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from sqlalchemy import select, text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from shared.database import create_db_engine, create_session_factory  # noqa: E402

from common_service.config import settings  # noqa: E402
from common_service.models.zalo import LK_CHUA_XAC_MINH, ZaloLienKet  # noqa: E402
from common_service.services.zalo.phone import (  # noqa: E402
    chuan_hoa_uu_tien,
    hien_thi,
)

_COT_MA = {"ma_cc", "ma", "ma_cong_chuc", "macc", "ma cc", "mã cc", "mã", "mã công chức"}
_COT_TEN = {"ho_ten", "ho va ten", "họ và tên", "họ tên", "ho ten", "hoten", "tên"}
_COT_SDT = {
    "so_dien_thoai", "sdt", "dien_thoai", "phone", "so dien thoai",
    "số điện thoại", "sđt", "điện thoại", "so_dt", "số đt",
}
_COT_NS = {
    "ngay_sinh", "ngày sinh", "ngày tháng năm sinh", "ngaysinh",
    "ngay thang nam sinh", "năm sinh",
}
# Nguồn được coi là chính xác hơn file Excel — không cho import ghi đè.
_NGUON_UU_TIEN = {"DINH_CHINH_DON_VI", "BO_SUNG_TAY"}

_COT_DV = {"don_vi", "đơn vị", "đơn vị công tác", "don vi cong tac", "đơn vị công tác"}


def _chuan_ten_cot(x: Any) -> str:
    return re.sub(r"\s+", " ", str(x or "").strip().lower())


def chuan_hoa_ten(ten: Any) -> str:
    """Chuẩn hóa họ tên để so khớp: NFC, bỏ khoảng trắng thừa, viết hoa."""
    s = unicodedata.normalize("NFC", str(ten or "")).strip()
    s = re.sub(r"\s+", " ", s)
    return s.upper()


def bo_dau(s: str) -> str:
    """Bỏ toàn bộ dấu tiếng Việt.

    Dùng làm khóa khớp DỰ PHÒNG cho các biến thể đặt dấu thanh khác nhau mà
    người Việt viết lẫn lộn: THỦY / THUỶ, HOÀ / HÒA, THÚY / THUÝ...
    Vì bỏ dấu làm mất thông tin nên khóa này chỉ được chấp nhận khi có
    NGÀY SINH xác nhận (xem `khop_cong_chuc`).
    """
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("Đ", "D").replace("đ", "d").upper()


# Năm sinh gắn vào tên để phân biệt người trùng tên.
# Thực tế gặp: DB ghi "NGUYỄN THỊ THANH VÂN 1990" hoặc "TRẦN TRUNG KIÊN1977";
# Excel ghi "NGUYỄN THỊ THANH VÂN(90)" hoặc "TRẦN TRUNG KIÊN (77)".
_HAU_TO_NAM = re.compile(r"\s*[\(\[]?\s*(\d{2,4})\s*[\)\]]?\s*$")


def tach_nam_sinh(ten: str) -> tuple[str, Optional[int]]:
    """Tách hậu tố năm sinh khỏi tên. Trả về (tên sạch, năm 4 chữ số hoặc None)."""
    mt = _HAU_TO_NAM.search(ten)
    if not mt:
        return ten.strip(), None
    so = mt.group(1)
    nam: Optional[int]
    if len(so) == 4:
        nam = int(so)
    elif len(so) == 2:
        # "90" → 1990, "05" → 2005 (công chức không ai sinh sau 2010)
        n = int(so)
        nam = 1900 + n if n > 10 else 2000 + n
    else:
        return ten.strip(), None
    if not (1940 <= nam <= 2010):
        return ten.strip(), None
    return ten[: mt.start()].strip(), nam


def _parse_ngay(x: Any) -> Optional[date]:
    if x is None:
        return None
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    s = str(x).strip()
    if not s or s.lower() in ("nan", "nat", "none"):
        return None
    for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, f).date()
        except ValueError:
            continue
    return None


def doc_file(duong_dan: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Đọc Excel/CSV, tự dò dòng tiêu đề và tên cột.

    Trả về (danh sách bản ghi, ánh xạ vai trò cột → tên cột gốc).
    """
    if not duong_dan.exists():
        raise SystemExit(f"Không tìm thấy file: {duong_dan}")

    suffix = duong_dan.suffix.lower()
    if suffix in (".xlsx", ".xlsm", ".xls"):
        import pandas as pd

        tho = pd.read_excel(duong_dan, header=None, dtype=object)
        bang = tho.values.tolist()
    elif suffix == ".csv":
        with duong_dan.open(encoding="utf-8-sig", newline="") as f:
            bang = [r for r in csv.reader(f)]
    else:
        raise SystemExit(f"Định dạng không hỗ trợ: {suffix}")

    if not bang:
        raise SystemExit("File rỗng")

    # --- Dò dòng tiêu đề: dòng đầu tiên có cả cột tên VÀ cột số điện thoại ---
    dong_tieu_de = None
    for i, row in enumerate(bang[:30]):
        o = {_chuan_ten_cot(c) for c in row}
        if (o & _COT_TEN or o & _COT_MA) and (o & _COT_SDT):
            dong_tieu_de = i
            break
    if dong_tieu_de is None:
        raise SystemExit(
            "Không dò được dòng tiêu đề trong 30 dòng đầu.\n"
            f"Cần một dòng có cột tên ({sorted(_COT_TEN)[:3]}...) "
            f"và cột số ({sorted(_COT_SDT)[:3]}...)."
        )

    tieu_de = [str(c).strip() if c is not None else "" for c in bang[dong_tieu_de]]
    vi_tri: dict[str, int] = {}
    for idx, c in enumerate(tieu_de):
        o = _chuan_ten_cot(c)
        if o in _COT_MA and "ma_cc" not in vi_tri:
            vi_tri["ma_cc"] = idx
        elif o in _COT_TEN and "ho_ten" not in vi_tri:
            vi_tri["ho_ten"] = idx
        elif o in _COT_SDT and "so_dien_thoai" not in vi_tri:
            vi_tri["so_dien_thoai"] = idx
        elif o in _COT_NS and "ngay_sinh" not in vi_tri:
            vi_tri["ngay_sinh"] = idx
        elif o in _COT_DV and "don_vi" not in vi_tri:
            vi_tri["don_vi"] = idx

    if "so_dien_thoai" not in vi_tri or not (vi_tri.get("ma_cc") or vi_tri.get("ho_ten")):
        raise SystemExit(f"Thiếu cột bắt buộc. Tiêu đề dò được: {tieu_de}")

    ban_ghi = []
    for row in bang[dong_tieu_de + 1 :]:
        def lay(k):
            i = vi_tri.get(k)
            if i is None or i >= len(row):
                return None
            v = row[i]
            if v is None:
                return None
            s = str(v).strip()
            return None if s.lower() in ("", "nan", "nat", "none") else s

        ten = lay("ho_ten")
        ma = lay("ma_cc")
        if not ten and not ma:
            continue
        ban_ghi.append({
            "ma_cc": ma,
            "ho_ten": ten,
            "so_dien_thoai": lay("so_dien_thoai"),
            "ngay_sinh": _parse_ngay(row[vi_tri["ngay_sinh"]]) if "ngay_sinh" in vi_tri else None,
            "don_vi": lay("don_vi"),
        })

    anh_xa = {k: tieu_de[i] for k, i in vi_tri.items()}
    return ban_ghi, anh_xa


async def _nap_cong_chuc(db: AsyncSession) -> list[dict[str, Any]]:
    kq = await db.execute(
        text(
            """
            SELECT cc.id, cc.ma_cc, cc.ho_ten, cc.ngay_sinh, cc.chuc_vu,
                   COALESCE(dv.ten_don_vi, '') AS ten_don_vi
            FROM public.cong_chuc cc
            LEFT JOIN public.don_vi dv ON dv.id = cc.don_vi_id
            WHERE cc.is_active = true AND COALESCE(cc.is_deleted, false) = false
            ORDER BY cc.ma_cc
            """
        )
    )
    return [dict(r._mapping) for r in kq]


class ChiMucCongChuc:
    """Chỉ mục tra cứu công chức, xử lý được các biến thể ghi tên trong thực tế.

    Ba vấn đề gặp phải với danh sách do đơn vị lập:

    1. **Hậu tố năm sinh phân biệt người trùng tên.** Hệ thống lưu
       "NGUYỄN THỊ THANH VÂN 1990", file Excel ghi "NGUYỄN THỊ THANH VÂN(90)".
       → Tách hậu tố ở CẢ HAI phía rồi mới so.

    2. **Sau khi tách hậu tố thì tên lại trùng nhau.** Đúng như vậy — đó chính
       là lý do người ta gắn năm vào. → Phân giải bằng NGÀY SINH (chính xác
       đến ngày), nếu không có thì bằng NĂM SINH.

    3. **Biến thể đặt dấu thanh.** "PHẠM THỊ THU THỦY" và "PHẠM THỊ THU THUỶ"
       là cùng một người. → Khóa dự phòng bỏ dấu, nhưng CHỈ chấp nhận khi có
       ngày sinh xác nhận, vì bỏ dấu làm mất thông tin.

    Nguyên tắc xuyên suốt: thà bỏ sót để người rà tay còn hơn gán nhầm số điện
    thoại của người này sang người khác.
    """

    def __init__(self, cong_chuc: list[dict[str, Any]]):
        self.theo_ma: dict[str, dict] = {}
        self.theo_ten: defaultdict[str, list[dict]] = defaultdict(list)
        self.theo_ten_bo_dau: defaultdict[str, list[dict]] = defaultdict(list)

        for c in cong_chuc:
            if c.get("ma_cc"):
                self.theo_ma[c["ma_cc"].strip().upper()] = c
            ten_sach, nam = tach_nam_sinh(chuan_hoa_ten(c["ho_ten"]))
            c["_ten_sach"] = ten_sach
            c["_nam_ten"] = nam
            self.theo_ten[ten_sach].append(c)
            self.theo_ten_bo_dau[bo_dau(ten_sach)].append(c)

    @staticmethod
    def _nam_cua(c: dict) -> Optional[int]:
        """Năm sinh của công chức: ưu tiên cột ngay_sinh, sau đó hậu tố trong tên."""
        if c.get("ngay_sinh"):
            return c["ngay_sinh"].year
        return c.get("_nam_ten")

    def _phan_giai(
        self,
        ung_vien: list[dict],
        ngay_sinh: Optional[date],
        nam: Optional[int],
        nam_ten: Optional[int],
        da_dung: set[str],
    ) -> tuple[Optional[dict], str]:
        """Chọn đúng một người trong danh sách ứng viên.

        `nam_ten` là năm ghi TƯỜNG MINH trong tên ở file, ví dụ "...(84)".
        Đây là dấu hiệu phân biệt do người lập danh sách cố ý thêm vào, nên
        nếu nó mâu thuẫn với năm tường minh phía hệ thống thì CHẮC CHẮN là
        hai người khác nhau — phải từ chối, không được đoán.
        """
        con_lai = [c for c in ung_vien if str(c["id"]) not in da_dung]
        if not con_lai:
            return None, "Tất cả người trùng tên đã được gán cho dòng khác"

        if len(con_lai) == 1:
            c = con_lai[0]
            nam_db = self._nam_cua(c)
            # Chỉ còn 1 ứng viên KHÔNG có nghĩa là đúng người.
            # Sự cố thật 10/08/2026: "Nguyễn Anh Tuấn(84)" bị gán vào
            # "Nguyễn Anh Tuấn 1972" chỉ vì lúc đó còn mỗi người này chưa dùng.
            if nam_ten and nam_db and nam_ten != nam_db:
                return None, (
                    f"Năm sinh mâu thuẫn: file ghi {nam_ten}, "
                    f"hệ thống ghi {nam_db} ({c['ma_cc']} {c['ho_ten']}) — không dám khớp"
                )
            return c, "TEN"

        # Nhiều người trùng tên → cần ngày sinh để phân biệt
        if ngay_sinh:
            khop = [c for c in con_lai if c.get("ngay_sinh") == ngay_sinh]
            if len(khop) == 1:
                return khop[0], "NAM_SINH (khớp đúng ngày sinh)"
        if nam:
            khop = [c for c in con_lai if self._nam_cua(c) == nam]
            if len(khop) == 1:
                return khop[0], "NAM_SINH (khớp năm sinh)"

        ds = ", ".join(f"{c['ma_cc']} {c['ho_ten']}" for c in con_lai)
        return None, f"Trùng tên {len(con_lai)} người, ngày sinh không phân biệt được ({ds})"

    def khop(
        self,
        ma_cc: Optional[str],
        ho_ten: Optional[str],
        ngay_sinh: Optional[date],
        da_dung: set[str],
    ) -> tuple[Optional[dict], str]:
        """Tìm công chức tương ứng. Trả về (bản ghi hoặc None, lý do/cách khớp)."""
        if ma_cc:
            c = self.theo_ma.get(ma_cc.strip().upper())
            if c is not None:
                return c, "MA_CC"

        if not ho_ten:
            return None, "Dòng không có họ tên lẫn mã công chức"

        ten_sach, nam_ten = tach_nam_sinh(chuan_hoa_ten(ho_ten))
        nam = nam_ten or (ngay_sinh.year if ngay_sinh else None)

        # 1. Khớp tên đầy đủ dấu
        if ten_sach in self.theo_ten:
            return self._phan_giai(
                self.theo_ten[ten_sach], ngay_sinh, nam, nam_ten, da_dung
            )

        # 2. Dự phòng: bỏ dấu — BẮT BUỘC có ngày sinh xác nhận
        ung_vien = self.theo_ten_bo_dau.get(bo_dau(ten_sach), [])
        if ung_vien:
            if not ngay_sinh:
                return None, "Tên chỉ khớp khi bỏ dấu nhưng thiếu ngày sinh để xác nhận"
            khop = [
                c for c in ung_vien
                if c.get("ngay_sinh") == ngay_sinh and str(c["id"]) not in da_dung
            ]
            if len(khop) == 1:
                return khop[0], f"BO_DAU (xác nhận bằng ngày sinh) ← '{khop[0]['ho_ten']}'"
            return None, "Khớp khi bỏ dấu nhưng ngày sinh không xác nhận được"

        return None, "Không tìm thấy trong hệ thống (có thể đã nghỉ/chuyển đơn vị)"


def _che(so: Any) -> str:
    """Che 3 chữ số cuối khi đưa số vào báo cáo.

    Báo cáo được commit vào git nên KHÔNG được chứa số điện thoại đầy đủ —
    dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP. Giữ lại phần đầu để đơn vị
    vẫn nhận ra được số nào cần đính chính.
    """
    s = str(so or "").strip()
    if not s:
        return ""
    chu_so = re.sub(r"\D", "", s)
    if len(chu_so) < 6:
        return "***"
    return re.sub(r"\d(?=\d{0,2}$)", "*", s)


def _xuat_md(
    duong_dan: Path,
    nguon: Path,
    thong_ke: Counter,
    thieu_sdt: list[dict],
    loi_dong: list[dict],
    trung_so: dict,
    lech_ngay_sinh: list[dict],
    tong_cc: int,
    da_phu: int,
) -> None:
    d = []
    a = d.append
    a("# Báo cáo đối chiếu số điện thoại — kênh Zalo OA\n")
    a(f"**Nguồn:** `{nguon.name}`  ")
    a(f"**Đối chiếu với:** `public.cong_chuc` ({tong_cc} công chức đang hoạt động)  ")
    a("**Chế độ:** đối chiếu, chưa ghi database\n")
    a("> Khớp theo **họ và tên** vì file nguồn không có cột mã công chức.")
    a("> Đã kiểm tra: không có tên trùng ở cả hai phía nên cách khớp này an toàn.\n")
    a("---\n")
    a("## 1. Tổng quan\n")
    a("| Chỉ số | Số lượng |")
    a("|---|---:|")
    a(f"| Công chức đang hoạt động trong hệ thống | {tong_cc} |")
    a(f"| Dòng đọc được từ file | {thong_ke['tong_dong']} |")
    a(f"| Khớp được từ file này | {thong_ke['hop_le']} |")
    a(f"| **Đã có số trong hệ thống (gồm cả bổ sung tay)** | **{da_phu}** |")
    a(f"| Số điện thoại không dùng được | {thong_ke['so_khong_dung']} |")
    a(f"| Có trong file nhưng không tìm thấy trong hệ thống | {thong_ke['khong_khop']} |")
    a(f"| **Công chức CHƯA có số điện thoại** | **{len(thieu_sdt)}** |")
    phu = da_phu / tong_cc * 100 if tong_cc else 0
    a(f"\n**Độ phủ: {da_phu}/{tong_cc} = {phu:.1f}%**\n")
    if phu >= 95:
        a("> ✅ Độ phủ rất tốt, đủ điều kiện triển khai.\n")
    elif phu >= 70:
        a("> ⚠️ Độ phủ khá, nhưng một số người sẽ không nhận được thông báo.\n")
    else:
        a("> ❌ Độ phủ thấp — nên bổ sung trước khi bật kênh Zalo.\n")

    a("---\n")
    a(f"## 2. Công chức CHƯA có số điện thoại ({len(thieu_sdt)} người)\n")
    if thieu_sdt:
        a("Những người này sẽ **không nhận được** thông báo họp qua Zalo.\n")
        a("| # | Mã CC | Họ và tên | Chức vụ | Đơn vị |")
        a("|---:|---|---|---|---|")
        for i, r in enumerate(sorted(thieu_sdt, key=lambda x: (x["ten_don_vi"] or "", x["ho_ten"] or "")), 1):
            a(f"| {i} | {r['ma_cc']} | {r['ho_ten']} | {r.get('chuc_vu') or ''} | {r['ten_don_vi']} |")
        a("")
        theo_dv = Counter(r["ten_don_vi"] or "(không rõ)" for r in thieu_sdt)
        a("**Gom theo đơn vị:**\n")
        a("| Đơn vị | Số người thiếu |")
        a("|---|---:|")
        for k, v in theo_dv.most_common():
            a(f"| {k} | {v} |")
        a("")
    else:
        a("✅ Không thiếu ai — toàn bộ công chức đều có số điện thoại.\n")

    a("---\n")
    a(f"## 3. Dòng trong file không khớp được ({len(loi_dong)} dòng)\n")
    a("> Đơn vị xác nhận: đây là những người **đã chuyển công tác sang chi cục**\n"
      "> **khác**, nên không còn trong danh sách công chức đang hoạt động.\n")
    if loi_dong:
        a("| Họ và tên (trong file) | Số trong file | Lý do |")
        a("|---|---|---|")
        for r in loi_dong:
            a(f"| {r['ho_ten']} | `{_che(r['so'])}` | {r['ly_do']} |")
        a("")
    else:
        a("✅ Mọi dòng đều dùng được.\n")

    a("---\n")
    a(f"## 4. Số điện thoại trùng giữa nhiều người ({len(trung_so)} số)\n")
    if trung_so:
        a("Thường là nhập nhầm — cần đơn vị xác nhận lại.\n")
        a("| Số | Những người cùng khai |")
        a("|---|---|")
        for so, ds in trung_so.items():
            a(f"| {_che(hien_thi(so))} | {', '.join(ds)} |")
        a("")
    else:
        a("✅ Không có số nào bị trùng.\n")

    a("---\n")
    a(f"## 5. Lệch ngày sinh ({len(lech_ngay_sinh)} trường hợp)\n")
    if lech_ngay_sinh:
        a("Tên khớp nhưng ngày sinh khác — **có thể là trùng tên khác người**.")
        a("Cần kiểm tra tay trước khi tin kết quả khớp.\n")
        a("| Mã CC | Họ và tên | Ngày sinh trong hệ thống | Ngày sinh trong file |")
        a("|---|---|---|---|")
        for r in lech_ngay_sinh:
            a(f"| {r['ma_cc']} | {r['ho_ten']} | {r['ns_db']} | {r['ns_file']} |")
        a("")
    else:
        a("✅ Mọi trường hợp khớp tên đều khớp cả ngày sinh.\n")

    duong_dan.write_text("\n".join(d), encoding="utf-8")


async def chay(duong_dan: Path, ghi: bool, xuat_md: Optional[Path]) -> int:
    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    dong, anh_xa = doc_file(duong_dan)
    print(f"Đọc {len(dong)} dòng từ {duong_dan.name}")
    print(f"Cột nhận diện được: {anh_xa}\n")

    async with session_factory() as db:
        cong_chuc = await _nap_cong_chuc(db)
        print(f"Đối chiếu với {len(cong_chuc)} công chức đang hoạt động\n")

        chi_muc = ChiMucCongChuc(cong_chuc)

        kq = await db.execute(select(ZaloLienKet))
        da_co = {str(lk.cong_chuc_id): lk for lk in kq.scalars().all()}

        tk: Counter = Counter({"tong_dong": len(dong)})
        loi_dong: list[dict] = []
        lech_ns: list[dict] = []
        theo_so: defaultdict[str, list[str]] = defaultdict(list)
        se_ghi: list[tuple[dict, Any, list[str]]] = []
        da_khop_ids: set[str] = set()

        for r in dong:
            cc, ly_do_khop = chi_muc.khop(
                r["ma_cc"], r["ho_ten"], r["ngay_sinh"], da_khop_ids
            )
            if ly_do_khop.startswith("BO_DAU"):
                tk["khop_bo_dau"] += 1
            elif ly_do_khop.startswith("NAM_SINH"):
                tk["khop_nam_sinh"] += 1

            if cc is None:
                tk["khong_khop"] += 1
                loi_dong.append({
                    "ho_ten": r["ho_ten"] or r["ma_cc"] or "?",
                    "so": r["so_dien_thoai"] or "",
                    "ly_do": ly_do_khop,
                })
                continue

            # Đối chiếu ngày sinh nếu cả hai phía đều có
            if r["ngay_sinh"] and cc["ngay_sinh"] and r["ngay_sinh"] != cc["ngay_sinh"]:
                lech_ns.append({
                    "ma_cc": cc["ma_cc"], "ho_ten": cc["ho_ten"],
                    "ns_db": cc["ngay_sinh"], "ns_file": r["ngay_sinh"],
                })

            # Ô có thể chứa 2 số (56/548 người khai vậy) — lấy số hợp lệ đầu tiên
            kq_ch, so_phu = chuan_hoa_uu_tien(r["so_dien_thoai"])
            if not kq_ch.hop_le:
                tk["so_khong_dung"] += 1
                loi_dong.append({
                    "ho_ten": f"{cc['ma_cc']} — {cc['ho_ten']}",
                    "so": r["so_dien_thoai"] or "",
                    "ly_do": f"{kq_ch.trang_thai}: {kq_ch.ghi_chu}",
                })
                continue

            theo_so[kq_ch.so_chuan].append(f"{cc['ma_cc']} {cc['ho_ten']}")
            tk["hop_le"] += 1
            if kq_ch.trang_thai == "OK_SO_CU":
                tk["so_cu"] += 1
            if so_phu:
                tk["co_so_phu"] += 1
            da_khop_ids.add(str(cc["id"]))
            se_ghi.append((cc, kq_ch, so_phu))

        # Trùng số phải soi theo TRẠNG THÁI CUỐI trong DB, không chỉ theo file:
        # số bị gán nhầm có thể đã được đơn vị đính chính bằng tay sau đó.
        ten_theo_id = {str(c["id"]): f"{c['ma_cc']} {c['ho_ten']}" for c in cong_chuc}
        cuoi_cung: dict[str, str] = {
            cid: lk.so_dien_thoai for cid, lk in da_co.items() if lk.so_dien_thoai
        }
        for c, kq_ch, _ in se_ghi:
            cid = str(c["id"])
            lk_cu = da_co.get(cid)
            if lk_cu is not None and lk_cu.nguon in _NGUON_UU_TIEN:
                continue  # giữ số đã đính chính tay
            cuoi_cung[cid] = kq_ch.so_chuan
        gom: defaultdict[str, list[str]] = defaultdict(list)
        for cid, so in cuoi_cung.items():
            if cid in ten_theo_id:
                gom[so].append(ten_theo_id[cid])
        trung_so = {s: m for s, m in gom.items() if len(m) > 1}
        # "Thiếu số" tính theo THỰC TẾ trong DB: không khớp ở file này VÀ cũng
        # chưa có liên kết từ trước (ví dụ số bổ sung tay ngoài file Excel).
        thieu_sdt = [
            c for c in cong_chuc
            if str(c["id"]) not in da_khop_ids and str(c["id"]) not in da_co
        ]
        da_phu = len(cong_chuc) - len(thieu_sdt)

        # ---------------- Báo cáo ----------------
        print("=" * 64)
        print("KẾT QUẢ ĐỐI CHIẾU")
        print("=" * 64)
        print(f"  Khớp được, số hợp lệ         : {tk['hop_le']:>4}")
        if tk["so_cu"]:
            print(f"    (số 11 chữ số cũ đã quy đổi: {tk['so_cu']})")
        print(f"  Có khai 2 số (lấy số đầu)    : {tk['co_so_phu']:>4}")
        print(f"  Số không dùng được           : {tk['so_khong_dung']:>4}")
        print(f"  Không tìm thấy trong hệ thống: {tk['khong_khop']:>4}")
        print(f"  Số trùng giữa nhiều người    : {len(trung_so):>4}")
        print(f"  Lệch ngày sinh (cần soát)    : {len(lech_ns):>4}")
        print(f"  CÔNG CHỨC CHƯA CÓ SỐ         : {len(thieu_sdt):>4}")
        phu = da_phu / len(cong_chuc) * 100 if cong_chuc else 0
        print(f"\n  ĐỘ PHỦ THỰC TẾ: {da_phu}/{len(cong_chuc)} = {phu:.1f}%")

        if xuat_md:
            _xuat_md(xuat_md, duong_dan, tk, thieu_sdt, loi_dong, trung_so,
                     lech_ns, len(cong_chuc), da_phu)
            print(f"\n  📄 Đã xuất báo cáo → {xuat_md}")

        if not ghi:
            print("\n" + "=" * 64)
            print("ĐANG CHẠY KHÔ — KHÔNG GHI GÌ VÀO DATABASE.")
            print("Xem báo cáo, nếu đồng ý thì chạy lại với cờ --ghi")
            print("=" * 64)
            await engine.dispose()
            return 0

        them, cap_nhat, giu_nguyen = 0, 0, 0
        for cc, kq_ch, so_phu in se_ghi:
            # Giữ lại số phụ trong ghi chú: khi số chính báo lỗi, đơn vị có sẵn
            # số thứ hai để thử mà không phải mở lại file Excel.
            ghi_chu = f"Số phụ: {', '.join(hien_thi(s) for s in so_phu)}" if so_phu else None
            lk = da_co.get(str(cc["id"]))
            if lk is None:
                db.add(ZaloLienKet(
                    cong_chuc_id=cc["id"],
                    so_dien_thoai=kq_ch.so_chuan,
                    so_goc=kq_ch.so_goc[:30],
                    trang_thai=LK_CHUA_XAC_MINH,
                    nguon="IMPORT_EXCEL",
                    ghi_chu=ghi_chu,
                ))
                them += 1
            elif lk.nguon in _NGUON_UU_TIEN:
                # Số do đơn vị đính chính/bổ sung tay là NGUỒN CHÍNH XÁC NHẤT.
                # File Excel cũ chạy lại KHÔNG được phép ghi đè lên nó, nếu
                # không mọi công sức đính chính sẽ mất im lặng.
                if lk.so_dien_thoai != kq_ch.so_chuan:
                    giu_nguyen += 1
            elif lk.so_dien_thoai != kq_ch.so_chuan:
                lk.so_dien_thoai = kq_ch.so_chuan
                lk.so_goc = kq_ch.so_goc[:30]
                lk.nguon = "IMPORT_EXCEL"
                lk.ghi_chu = ghi_chu
                if lk.trang_thai == "SO_LOI":
                    lk.trang_thai = LK_CHUA_XAC_MINH
                cap_nhat += 1

        await db.commit()
        print(f"\n✅ Đã ghi: thêm mới {them}, cập nhật {cap_nhat} liên kết.")
        if giu_nguyen:
            print(f"   Giữ nguyên {giu_nguyen} số đã đính chính tay "
                  f"(không để file cũ ghi đè).")

    await engine.dispose()
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="Import số điện thoại cho kênh Zalo (mặc định chạy khô)"
    )
    p.add_argument("file", type=Path)
    p.add_argument("--ghi", action="store_true",
                   help="GHI THẬT vào common.zalo_lien_ket")
    p.add_argument("--xuat-md", type=Path, default=None,
                   help="Xuất báo cáo Markdown để kiểm tra")
    a = p.parse_args()

    print(f"DB: {settings.db_name} @ {settings.db_host}:{settings.db_port}")
    if a.ghi:
        print("⚠️  CHẾ ĐỘ GHI THẬT\n")
    return asyncio.run(chay(a.file, a.ghi, a.xuat_md))


if __name__ == "__main__":
    raise SystemExit(main())
