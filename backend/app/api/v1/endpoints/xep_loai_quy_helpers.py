"""
app/api/v1/endpoints/xep_loai_quy_helpers.py
=============================================
Helper functions cho tính điểm và xếp loại quý.

PHIÊN BẢN: 3.6.0 (14/04/2026)

Các hàm chính:
- tinh_diem_quy(db, cc_id, quy, nam) -> dict
- lay_tieu_chi_quy(db, cc_id, thang_list, nam) -> dict
- xep_loai_kpi(diem_tong) -> str (reuse từ xep_loai_moi.py)
"""

from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kpi_assessment import (
    DanhGiaThang,
    TieuChiChungDanhGia,
    TieuChiChung,
)
from app.models.lich_su_dieu_chinh import LichSuDieuChinh, LoaiDoiTuongDieuChinh


# =============================================================================
# CONSTANTS
# =============================================================================

QUY_TO_THANG = {
    1: [1, 2, 3],
    2: [4, 5, 6],
    3: [7, 8, 9],
    4: [10, 11, 12],
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def xep_loai_kpi(diem_tong: float) -> str:
    """
    Xếp loại KPI theo điểm tổng.
    Reuse logic từ xep_loai_moi.py.
    """
    if diem_tong >= 90:
        return "A"
    elif diem_tong >= 70:
        return "B"
    elif diem_tong >= 50:
        return "C"
    else:
        return "D"


async def kiem_tra_chuyen_don_vi(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang_list: List[int],
    nam: int
) -> bool:
    """
    Kiểm tra CC có chuyển đơn vị giữa quý không.

    Trả về TRUE nếu có bản ghi chuyển đơn vị trong khoảng 3 tháng của quý.
    """
    # Lấy tất cả bản ghi danh_gia_thang của 3 tháng
    stmt = (
        select(DanhGiaThang.don_vi_id_snapshot)
        .where(DanhGiaThang.cong_chuc_id == cong_chuc_id)
        .where(DanhGiaThang.thang.in_(thang_list))
        .where(DanhGiaThang.nam == nam)
        .where(DanhGiaThang.is_deleted == False)
    )
    result = await db.execute(stmt)
    don_vi_ids = [row[0] for row in result.fetchall() if row[0]]

    # Nếu có nhiều hơn 1 đơn vị → chuyển đơn vị giữa quý
    return len(set(don_vi_ids)) > 1


async def lay_tieu_chi_quy(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang_list: List[int],
    nam: int
) -> dict:
    """
    Lấy tiêu chí chung quý (deduplicate - Option Y).

    Logic:
    - Nhóm 1, 2: Vi phạm (is_achieved=FALSE) ít nhất 1 tháng → trừ điểm 1 lần
    - Nhóm 3: Đạt (is_achieved=TRUE) ít nhất 1 tháng → cộng điểm 1 lần

    Công thức:
    diem_tc_quy = max(0, min(30, 20 - sum_vi_pham + sum_dat))

    Returns:
    {
        "diem_tc_quy": Decimal,
        "tieu_chi_vi_pham": List[dict],  # Nhóm 1, 2
        "tieu_chi_dat": List[dict],      # Nhóm 3
    }
    """
    # Query tiêu chí VI PHẠM (nhóm 1, 2)
    # is_achieved_final = COALESCE(is_achieved_ld, is_achieved_cc)
    is_achieved_final_vi_pham = case(
        (TieuChiChungDanhGia.is_achieved_ld.isnot(None), TieuChiChungDanhGia.is_achieved_ld),
        else_=TieuChiChungDanhGia.is_achieved_cc
    )

    stmt_vi_pham = (
        select(
            TieuChiChungDanhGia.tieu_chi_id,
            TieuChiChung.ma_tieu_chi,
            TieuChiChung.ten_tieu_chi,
            TieuChiChung.nhom_tieu_chi,
            TieuChiChung.diem_toi_da,
            func.array_agg(DanhGiaThang.thang).label("cac_thang")
        )
        .join(DanhGiaThang, TieuChiChungDanhGia.danh_gia_thang_id == DanhGiaThang.id)
        .join(TieuChiChung, TieuChiChungDanhGia.tieu_chi_id == TieuChiChung.id)
        .where(DanhGiaThang.cong_chuc_id == cong_chuc_id)
        .where(DanhGiaThang.thang.in_(thang_list))
        .where(DanhGiaThang.nam == nam)
        .where(DanhGiaThang.is_deleted == False)
        .where(TieuChiChung.gia_tri_mac_dinh == True)  # Nhóm 1, 2
        .where(is_achieved_final_vi_pham == False)  # Vi phạm (fallback to CC nếu LĐ chưa duyệt)
        .group_by(
            TieuChiChungDanhGia.tieu_chi_id,
            TieuChiChung.ma_tieu_chi,
            TieuChiChung.ten_tieu_chi,
            TieuChiChung.nhom_tieu_chi,
            TieuChiChung.diem_toi_da
        )
    )

    result_vi_pham = await db.execute(stmt_vi_pham)
    rows_vi_pham = result_vi_pham.fetchall()

    tieu_chi_vi_pham = []
    tong_tru_diem = Decimal("0")

    for row in rows_vi_pham:
        tieu_chi_vi_pham.append({
            "tieu_chi_id": row.tieu_chi_id,
            "ma_tieu_chi": row.ma_tieu_chi,
            "ten_tieu_chi": row.ten_tieu_chi,
            "nhom": row.nhom_tieu_chi,
            "diem_toi_da": float(row.diem_toi_da),
            "cac_thang_vi_pham": sorted(row.cac_thang),
        })
        tong_tru_diem += row.diem_toi_da

    # Query tiêu chí ĐẠT (nhóm 3)
    is_achieved_final_dat = case(
        (TieuChiChungDanhGia.is_achieved_ld.isnot(None), TieuChiChungDanhGia.is_achieved_ld),
        else_=TieuChiChungDanhGia.is_achieved_cc
    )

    stmt_dat = (
        select(
            TieuChiChungDanhGia.tieu_chi_id,
            TieuChiChung.ma_tieu_chi,
            TieuChiChung.ten_tieu_chi,
            TieuChiChung.nhom_tieu_chi,
            TieuChiChung.diem_toi_da,
            func.array_agg(DanhGiaThang.thang).label("cac_thang")
        )
        .join(DanhGiaThang, TieuChiChungDanhGia.danh_gia_thang_id == DanhGiaThang.id)
        .join(TieuChiChung, TieuChiChungDanhGia.tieu_chi_id == TieuChiChung.id)
        .where(DanhGiaThang.cong_chuc_id == cong_chuc_id)
        .where(DanhGiaThang.thang.in_(thang_list))
        .where(DanhGiaThang.nam == nam)
        .where(DanhGiaThang.is_deleted == False)
        .where(TieuChiChung.gia_tri_mac_dinh == False)  # Nhóm 3
        .where(is_achieved_final_dat == True)  # Đạt (fallback to CC nếu LĐ chưa duyệt)
        .group_by(
            TieuChiChungDanhGia.tieu_chi_id,
            TieuChiChung.ma_tieu_chi,
            TieuChiChung.ten_tieu_chi,
            TieuChiChung.nhom_tieu_chi,
            TieuChiChung.diem_toi_da
        )
    )

    result_dat = await db.execute(stmt_dat)
    rows_dat = result_dat.fetchall()

    tieu_chi_dat = []
    tong_cong_diem = Decimal("0")

    for row in rows_dat:
        tieu_chi_dat.append({
            "tieu_chi_id": row.tieu_chi_id,
            "ma_tieu_chi": row.ma_tieu_chi,
            "ten_tieu_chi": row.ten_tieu_chi,
            "nhom": row.nhom_tieu_chi,
            "diem_toi_da": float(row.diem_toi_da),
            "cac_thang_dat": sorted(row.cac_thang),
        })
        tong_cong_diem += row.diem_toi_da

    # Tính điểm tiêu chí quý
    diem_tc_quy = Decimal("20") - tong_tru_diem + tong_cong_diem
    diem_tc_quy = max(Decimal("0"), min(Decimal("30"), diem_tc_quy))

    return {
        "diem_tc_quy": diem_tc_quy,
        "tieu_chi_vi_pham": tieu_chi_vi_pham,
        "tieu_chi_dat": tieu_chi_dat,
    }


async def tinh_diem_quy(
    db: AsyncSession,
    cong_chuc_id: UUID,
    quy: int,
    nam: int
) -> dict:
    """
    Tính điểm quý cho 1 công chức.

    Returns:
    {
        "diem_kpi_quy": Decimal | None,
        "diem_tc_quy": Decimal | None,
        "diem_tong_quy": Decimal | None,
        "xep_loai_quy": str | None,
        "co_chuyen_don_vi": bool,
        "ghi_chu": str | None,
        "cac_thang": List[dict],  # Chi tiết 3 tháng
        "tieu_chi_quy": dict,     # Kết quả từ lay_tieu_chi_quy()
    }
    """
    thang_list = QUY_TO_THANG.get(quy, [])
    if not thang_list:
        return {
            "diem_kpi_quy": None,
            "diem_tc_quy": None,
            "diem_tong_quy": None,
            "xep_loai_quy": None,
            "co_chuyen_don_vi": False,
            "ghi_chu": "Quý không hợp lệ",
            "cac_thang": [],
            "tieu_chi_quy": {},
        }

    # Kiểm tra chuyển đơn vị
    co_chuyen_don_vi = await kiem_tra_chuyen_don_vi(db, cong_chuc_id, thang_list, nam)

    if co_chuyen_don_vi:
        return {
            "diem_kpi_quy": None,
            "diem_tc_quy": None,
            "diem_tong_quy": None,
            "xep_loai_quy": None,
            "co_chuyen_don_vi": True,
            "ghi_chu": "Không tính do chuyển đơn vị giữa quý",
            "cac_thang": [],
            "tieu_chi_quy": {},
        }

    # Lấy điểm 3 tháng
    stmt = (
        select(DanhGiaThang)
        .where(DanhGiaThang.cong_chuc_id == cong_chuc_id)
        .where(DanhGiaThang.thang.in_(thang_list))
        .where(DanhGiaThang.nam == nam)
        .where(DanhGiaThang.is_deleted == False)
        .order_by(DanhGiaThang.thang)
    )
    result = await db.execute(stmt)
    danh_gia_rows = result.scalars().all()

    cac_thang = []
    tong_diem_kpi_70 = Decimal("0")
    so_thang_co_du_lieu = 0

    for thang in thang_list:
        dg = next((dg for dg in danh_gia_rows if dg.thang == thang), None)

        if dg:
            # ⭐ FIX: Phân biệt NULL vs 0 — chỉ cộng điểm khi diem_kpi IS NOT NULL
            if dg.diem_kpi is not None:
                diem_kpi = dg.diem_kpi
                diem_kpi_70 = diem_kpi * Decimal("70")
                tong_diem_kpi_70 += diem_kpi_70
                so_thang_co_du_lieu += 1
            else:
                diem_kpi = Decimal("0")
                diem_kpi_70 = Decimal("0")

            diem_tc = dg.diem_tieu_chi_chung or Decimal("0")
            diem_tong = dg.diem_tong or Decimal("0")

            cac_thang.append({
                "thang": thang,
                "nam": nam,
                "diem_kpi": float(diem_kpi),
                "diem_kpi_70": float(diem_kpi_70),
                "diem_tc": float(diem_tc),
                "diem_tong": float(diem_tong),
                "xep_loai": dg.muc_xep_loai_chinh_thuc.value if dg.muc_xep_loai_chinh_thuc else None,
                "is_khoa": dg.is_khoa,
                "co_danh_gia": True,
            })
        else:
            # Tháng chưa có danh_gia_thang → coi như 0
            cac_thang.append({
                "thang": thang,
                "nam": nam,
                "diem_kpi": 0,
                "diem_kpi_70": 0,
                "diem_tc": 0,
                "diem_tong": 0,
                "xep_loai": None,
                "is_khoa": False,
                "co_danh_gia": False,
            })

    # ⭐ FIX: Đổi >= 0 thành > 0 — chỉ tính khi có ít nhất 1 tháng có diem_kpi
    diem_kpi_quy = tong_diem_kpi_70 / Decimal("3") if so_thang_co_du_lieu > 0 else None

    # Tính điểm tiêu chí quý (deduplicate)
    tieu_chi_result = await lay_tieu_chi_quy(db, cong_chuc_id, thang_list, nam)
    diem_tc_quy = tieu_chi_result["diem_tc_quy"]

    # Tính điểm tổng và xếp loại
    if diem_kpi_quy is not None and diem_tc_quy is not None:
        diem_tong_quy = diem_kpi_quy + diem_tc_quy
        xep_loai_quy = xep_loai_kpi(float(diem_tong_quy))
    else:
        diem_tong_quy = None
        xep_loai_quy = None

    # Nếu chưa đủ 3 tháng có dữ liệu → ghi chú
    ghi_chu = None
    if so_thang_co_du_lieu < 3:
        ghi_chu = f"Chưa đủ dữ liệu ({so_thang_co_du_lieu}/3 tháng)"

    return {
        "diem_kpi_quy": diem_kpi_quy,
        "diem_tc_quy": diem_tc_quy,
        "diem_tong_quy": diem_tong_quy,
        "xep_loai_quy": xep_loai_quy,
        "co_chuyen_don_vi": False,
        "ghi_chu": ghi_chu,
        "cac_thang": cac_thang,
        "tieu_chi_quy": tieu_chi_result,
    }
