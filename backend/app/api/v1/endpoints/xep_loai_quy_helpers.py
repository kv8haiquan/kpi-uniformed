"""
app/api/v1/endpoints/xep_loai_quy_helpers.py
=============================================
Helper functions cho tính điểm và xếp loại quý.

PHIÊN BẢN: 4.0.0 (17/04/2026)

Căn cứ: khoản 3 Điều 17 Nghị định 335/2025/NĐ-CP và Phụ lục I.

CÔNG THỨC QUÝ (LŨY KẾ — spec):
- Tiêu chí chung quý: TB cộng TC_chung của các tháng THỰC TẾ LÀM VIỆC.
- a, b, c (CC thường và LĐ): LŨY KẾ — chia tổng Σ trên tổng SP/CV được giao.
    + CC thường:
        a = Σ SP_hoàn_thành / Σ SP_được_giao
        b = Σ SP_đúng_tiến_độ / Σ SP_được_giao
        c = Σ SP_đạt_chất_lượng / Σ SP_được_giao
    + LĐ:
        a = Σ CV_hoàn_thành / Σ CV
        b = Σ điểm_tiến_độ_CV / Σ CV
        c = Σ điểm_chất_lượng_CV / Σ CV
- d, đ, e (chỉ LĐ): MIN 3 tháng (spec: chỉ 2 mức 100%/50%).
- Điểm KPI (70đ):
    + CC thường: (a+b+c)/3 × 70
    + LĐ:        (a+b+c+d+đ+e)/6 × 70
- Tổng điểm quý = TC_chung_quý + KPI_quý.
- Xếp loại theo ngưỡng 90/70/50 → A/B/C/D.

TRƯỜNG HỢP ĐẶC BIỆT (Phụ lục I mục II.4):
- Thai sản: tháng nghỉ THAI_SAN phủ toàn bộ ngày làm việc → loại khỏi tính.
- Mới chuyển công tác: `cc.ngay_vao_chi_cuc` sau ngày đầu tháng → tháng đó loại.
- Điểm quý CHỈ chia cho số tháng thực tế làm việc, không cứng /3.
- Nếu so_thang_thuc_te == 0 → trả về None (không đủ dữ liệu).

Các hàm chính:
- tinh_diem_quy(db, cc_id, quy, nam) -> dict
    Trả về đầy đủ a/b/c/d/đ/e để `in_bang_ke` consume thay vì tự tính lại.
- xep_loai_kpi(diem_tong) -> str
"""

import calendar
import logging
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kpi_assessment import DanhGiaThang
from app.models.kpi_submission import KeKhaiCongViec, TrangThaiKeKhai
from app.models.leader_kpi import (
    DanhGiaDDE,
    KeKhaiLanhDao,
    TrangThaiDDE,
    TrangThaiHoanThanh,
    TrangThaiKeKhaiLD,
)
from app.models.leave import DangKyNghi, LoaiNghi, TrangThaiNghi
from app.models.user_org import CongChuc

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

QUY_TO_THANG = {
    1: [1, 2, 3],
    2: [4, 5, 6],
    3: [7, 8, 9],
    4: [10, 11, 12],
}

SP_PER_DAY = 96  # Số SP quy đổi/ngày làm việc (CC thường)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def xep_loai_kpi(diem_tong: float) -> str:
    """Xếp loại theo ngưỡng 90/70/50."""
    if diem_tong >= 90:
        return "A"
    elif diem_tong >= 70:
        return "B"
    elif diem_tong >= 50:
        return "C"
    else:
        return "D"


async def _tinh_ngay_nghi_thang(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
    loai_nghi: Optional[LoaiNghi] = None,
) -> Decimal:
    """
    Tổng số ngày nghỉ ĐÃ PHÊ DUYỆT của CC trong 1 tháng.
    Nếu `loai_nghi` truyền vào → lọc theo loại (ví dụ chỉ THAI_SAN).
    """
    stmt = (
        select(func.coalesce(func.sum(DangKyNghi.so_ngay), Decimal("0")))
        .where(DangKyNghi.cong_chuc_id == cong_chuc_id)
        .where(DangKyNghi.thang_ap_dung == thang)
        .where(DangKyNghi.nam_ap_dung == nam)
        .where(DangKyNghi.trang_thai == TrangThaiNghi.DA_PHE_DUYET)
        .where(DangKyNghi.is_deleted == False)
    )
    if loai_nghi is not None:
        stmt = stmt.where(DangKyNghi.loai_nghi == loai_nghi)
    result = await db.execute(stmt)
    return result.scalar() or Decimal("0")


async def _xac_dinh_thang_thuc_te(
    db: AsyncSession,
    cc: CongChuc,
    thang_list: List[int],
    nam: int,
) -> tuple[List[int], List[dict]]:
    """
    Xác định các tháng "thực tế làm việc" theo Phụ lục I mục II.4:
      - CC phải đã về Chi cục trước ngày đầu tháng (ngay_vao_chi_cuc ≤ 01/MM/YYYY).
      - Không bị nghỉ THAI_SAN phủ toàn bộ ngày làm việc trong tháng.
      - Có số ngày làm việc > 0 sau khi trừ tất cả nghỉ phép đã duyệt.

    Trả về (thang_thuc_te, chi_tiet_tung_thang).
    chi_tiet_tung_thang: list dict có:
        thang, so_ngay_trong_thang, so_ngay_nghi, so_ngay_nghi_thai_san,
        so_ngay_lam_viec, ly_do_loai ("" hoặc "chua_ve_chi_cuc"/"thai_san"/"nghi_tron_thang")
    """
    thang_thuc_te: List[int] = []
    chi_tiet = []

    for thang in thang_list:
        so_ngay_thang = calendar.monthrange(nam, thang)[1]
        ngay_dau_thang = None
        try:
            from datetime import date as _date
            ngay_dau_thang = _date(nam, thang, 1)
        except Exception:
            ngay_dau_thang = None

        ly_do_loai = ""

        # Check CC đã về Chi cục chưa
        if (
            cc.ngay_vao_chi_cuc is not None
            and ngay_dau_thang is not None
            and cc.ngay_vao_chi_cuc > ngay_dau_thang
        ):
            ly_do_loai = "chua_ve_chi_cuc"
            chi_tiet.append({
                "thang": thang,
                "so_ngay_trong_thang": so_ngay_thang,
                "so_ngay_nghi": 0.0,
                "so_ngay_nghi_thai_san": 0.0,
                "so_ngay_lam_viec": 0.0,
                "ly_do_loai": ly_do_loai,
            })
            continue

        # Tổng ngày nghỉ đã duyệt
        so_ngay_nghi = await _tinh_ngay_nghi_thang(db, cc.id, thang, nam)
        so_ngay_nghi_thai_san = await _tinh_ngay_nghi_thang(
            db, cc.id, thang, nam, loai_nghi=LoaiNghi.THAI_SAN
        )
        so_ngay_lam_viec = max(
            Decimal("0"), Decimal(str(so_ngay_thang)) - so_ngay_nghi
        )

        if so_ngay_lam_viec <= 0:
            # Nghỉ trọn tháng — nếu toàn phần là thai sản thì ghi rõ
            if so_ngay_nghi_thai_san >= so_ngay_nghi and so_ngay_nghi_thai_san > 0:
                ly_do_loai = "thai_san"
            else:
                ly_do_loai = "nghi_tron_thang"
            chi_tiet.append({
                "thang": thang,
                "so_ngay_trong_thang": so_ngay_thang,
                "so_ngay_nghi": float(so_ngay_nghi),
                "so_ngay_nghi_thai_san": float(so_ngay_nghi_thai_san),
                "so_ngay_lam_viec": 0.0,
                "ly_do_loai": ly_do_loai,
            })
            continue

        thang_thuc_te.append(thang)
        chi_tiet.append({
            "thang": thang,
            "so_ngay_trong_thang": so_ngay_thang,
            "so_ngay_nghi": float(so_ngay_nghi),
            "so_ngay_nghi_thai_san": float(so_ngay_nghi_thai_san),
            "so_ngay_lam_viec": float(so_ngay_lam_viec),
            "ly_do_loai": ly_do_loai,
        })

    return thang_thuc_te, chi_tiet


async def _tinh_sp_cc_thuong_thang(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
    tam_tinh: bool = True,
) -> dict:
    """
    Tổng SP của CC thường trong 1 tháng.

    Tuân thủ: với hàng DA_PHE_DUYET dùng so_sp_chat_luong/so_sp_tien_do đã chốt;
    với CHO_PHE_DUYET suy ra từ tu_danh_gia (y hệt `tinh_diem_kpi_70`).

    Params:
        tam_tinh: True → bao gồm CHO_PHE_DUYET (mặc định, giữ nguyên hành vi cũ
                  để các caller quý tạm tính không bị ảnh hưởng).
                  False → CHỈ DA_PHE_DUYET (dùng khi in phiếu/bảng kê chính thức).

    Trả về: {"tong_sp", "sp_chat_luong", "sp_tien_do"} (đều Decimal, đơn vị SP).
    """
    if tam_tinh:
        allowed_statuses = [TrangThaiKeKhai.CHO_PHE_DUYET, TrangThaiKeKhai.DA_PHE_DUYET]
    else:
        allowed_statuses = [TrangThaiKeKhai.DA_PHE_DUYET]
    stmt = (
        select(
            KeKhaiCongViec.trang_thai,
            KeKhaiCongViec.so_luong,
            KeKhaiCongViec.so_sp_goc_quy_doi,
            KeKhaiCongViec.so_sp_chat_luong,
            KeKhaiCongViec.so_sp_tien_do,
            KeKhaiCongViec.tu_danh_gia_chat_luong,
            KeKhaiCongViec.tu_danh_gia_tien_do,
        )
        .where(KeKhaiCongViec.cong_chuc_id == cong_chuc_id)
        .where(KeKhaiCongViec.thang == thang)
        .where(KeKhaiCongViec.nam == nam)
        .where(KeKhaiCongViec.is_deleted == False)
        .where(KeKhaiCongViec.trang_thai.in_(allowed_statuses))
    )
    rows = (await db.execute(stmt)).all()

    tong_sp = Decimal("0")
    sp_cl = Decimal("0")
    sp_td = Decimal("0")

    for row in rows:
        (trang_thai_row, so_luong_row, sp_goc, r_sp_cl, r_sp_td, tu_dg_cl, tu_dg_td) = row
        sp_goc = Decimal(str(sp_goc or 0))
        so_luong_row = so_luong_row or 1
        tong_sp += sp_goc

        if trang_thai_row == TrangThaiKeKhai.DA_PHE_DUYET:
            sp_cl += Decimal(str(r_sp_cl or 0))
            sp_td += Decimal(str(r_sp_td or 0))
        else:
            tu_dg_cl = tu_dg_cl or 0
            tu_dg_td = tu_dg_td or 0
            if sp_goc > 0 and so_luong_row > 0:
                sp_per_unit = sp_goc / Decimal(str(so_luong_row))
                max_loi = so_luong_row * 4

                loi_cl = min(tu_dg_cl, max_loi)
                sp_cl += max(sp_goc - Decimal("0.25") * Decimal(str(loi_cl)) * sp_per_unit, Decimal("0"))

                loi_td = min(tu_dg_td, max_loi)
                sp_td += max(sp_goc - Decimal("0.25") * Decimal(str(loi_td)) * sp_per_unit, Decimal("0"))
            else:
                sp_cl += sp_goc
                sp_td += sp_goc

    return {"tong_sp": tong_sp, "sp_chat_luong": sp_cl, "sp_tien_do": sp_td}


async def _tinh_cv_lanh_dao_thang(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
    tam_tinh: bool = True,
) -> dict:
    """
    Tổng hợp công việc lãnh đạo trong 1 tháng.

    Theo Phụ lục I:
    - Chỉ CV ĐÃ HOÀN THÀNH mới được tính vào điểm tiến độ / chất lượng.
      CV chưa hoàn thành đóng góp 0 (không thể gọi là đúng tiến độ / đạt chất lượng).
    - Mỗi CV hoàn thành đóng góp:
        1 vào số lượng (hoan_thanh),
        max(0, 1 - so_loi_tien_do × 0.25) vào điểm tiến độ,
        max(0, 1 - so_loi_chat_luong × 0.25) vào điểm chất lượng.

    Params:
        tam_tinh: True → gộp CHO_PHE_DUYET + DA_PHE_DUYET (mặc định).
                  False → CHỈ DA_PHE_DUYET (khi in phiếu/bảng kê chính thức).

    Trả về tổng thô: {"tong_cv", "hoan_thanh", "diem_tien_do", "diem_chat_luong"}.
    """
    if tam_tinh:
        allowed = [TrangThaiKeKhaiLD.CHO_PHE_DUYET.value, TrangThaiKeKhaiLD.DA_PHE_DUYET.value]
    else:
        allowed = [TrangThaiKeKhaiLD.DA_PHE_DUYET.value]
    stmt = (
        select(
            KeKhaiLanhDao.trang_thai_hoan_thanh,
            KeKhaiLanhDao.so_loi_chat_luong,
            KeKhaiLanhDao.so_loi_tien_do,
        )
        .where(KeKhaiLanhDao.cong_chuc_id == cong_chuc_id)
        .where(KeKhaiLanhDao.thang == thang)
        .where(KeKhaiLanhDao.nam == nam)
        .where(KeKhaiLanhDao.is_deleted == False)
        .where(KeKhaiLanhDao.trang_thai.in_(allowed))
    )
    rows = (await db.execute(stmt)).all()

    tong_cv = len(rows)
    hoan_thanh = 0
    diem_td = 0.0
    diem_cl = 0.0

    for trang_thai_ht, loi_cl, loi_td in rows:
        if trang_thai_ht != TrangThaiHoanThanh.DA_HOAN_THANH:
            continue
        hoan_thanh += 1
        loi_cl = loi_cl or 0
        loi_td = loi_td or 0
        diem_cl += max(0.0, 1.0 - loi_cl * 0.25)
        diem_td += max(0.0, 1.0 - loi_td * 0.25)

    return {
        "tong_cv": tong_cv,
        "hoan_thanh": hoan_thanh,
        "diem_tien_do": diem_td,
        "diem_chat_luong": diem_cl,
    }


async def _lay_dde_thang(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
) -> Optional[dict]:
    """Lấy d/đ/e đã duyệt của 1 tháng (scale 0-1). Trả None nếu không có."""
    stmt = (
        select(DanhGiaDDE)
        .where(DanhGiaDDE.cong_chuc_id == cong_chuc_id)
        .where(DanhGiaDDE.thang == thang)
        .where(DanhGiaDDE.nam == nam)
        .where(DanhGiaDDE.trang_thai == TrangThaiDDE.DA_PHE_DUYET.value)
    )
    dde = (await db.execute(stmt)).scalar_one_or_none()
    if dde is None:
        return None
    return {
        "d": float(dde.d_final) / 100.0,
        "dd": float(dde.dd_final) / 100.0,
        "e": float(dde.e_final) / 100.0,
    }


async def _lay_tc_chung_thang(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
) -> Decimal:
    """Điểm tiêu chí chung đã phê duyệt của 1 tháng (scale 0-30). 0 nếu không có."""
    stmt = (
        select(DanhGiaThang.diem_tieu_chi_chung)
        .where(DanhGiaThang.cong_chuc_id == cong_chuc_id)
        .where(DanhGiaThang.thang == thang)
        .where(DanhGiaThang.nam == nam)
        .where(DanhGiaThang.is_deleted == False)
    )
    return (await db.execute(stmt)).scalar() or Decimal("0")


# =============================================================================
# MAIN ENTRY — tinh_diem_quy
# =============================================================================

async def tinh_diem_quy(
    db: AsyncSession,
    cong_chuc_id: UUID,
    quy: int,
    nam: int,
    tam_tinh: bool = True,
) -> dict:
    """
    Tính điểm quý theo spec Phụ lục I NĐ 335/2025/NĐ-CP (lũy kế).

    Params:
        tam_tinh: True (mặc định) → gộp CHO_PHE_DUYET + DA_PHE_DUYET cho SP/CV
                  (phù hợp với tab xếp loại quý hiện tại cho CC chưa chốt báo cáo).
                  False → chỉ lấy DA_PHE_DUYET (dùng khi in phiếu/bảng kê chính
                  thức: spec yêu cầu data phải đã được phê duyệt).

    LƯU Ý (20/04/2026): caller nên truyền `tam_tinh=True` khi CC là Trưởng đơn
    vị hoặc Phó Chi cục trưởng — kê khai của 2 cấp này do CCT duyệt, thường là
    bottleneck; ép `tam_tinh=False` sẽ làm điểm quý tụt giả tạo. Tham khảo
    `in_bang_ke.export_phieu_danh_gia_quy` để xem mẫu.

    Trả về dict:
        diem_kpi_quy, diem_tc_quy, diem_tong_quy, xep_loai_quy  (None nếu không đủ dữ liệu)
        a_so_luong, b_tien_do, c_chat_luong                     (0-1, cho cả CC và LĐ)
        d_ket_qua, dd_to_chuc, e_doan_ket                       (0-1, chỉ LĐ; None với CC thường)
        is_lanh_dao, so_thang_thuc_te, so_thang_co_du_lieu
        co_chuyen_don_vi, co_thai_san, ghi_chu
        cac_thang       : list chi tiết điểm từng tháng (hiển thị)
        tieu_chi_quy    : {"diem_tc_quy", "chi_tiet_thang"}
        chi_tiet_thuc_te: list dict phân tích thai sản / chưa về Chi cục / nghỉ trọn tháng
    """
    thang_list = QUY_TO_THANG.get(quy, [])
    if not thang_list:
        return _empty_result(ghi_chu="Quý không hợp lệ")

    # 1. Lấy công chức
    cc = (
        await db.execute(select(CongChuc).where(CongChuc.id == cong_chuc_id))
    ).scalar_one_or_none()
    if cc is None:
        return _empty_result(ghi_chu="Không tìm thấy công chức")

    is_lanh_dao = bool(cc.is_lanh_dao)

    # 2. Xác định các tháng thực tế làm việc (thai sản, mới chuyển công tác)
    thang_thuc_te, chi_tiet_thuc_te = await _xac_dinh_thang_thuc_te(
        db, cc, thang_list, nam
    )
    so_thang_thuc_te = len(thang_thuc_te)
    co_thai_san = any(c["ly_do_loai"] == "thai_san" for c in chi_tiet_thuc_te)
    co_chuyen_don_vi = any(
        c["ly_do_loai"] == "chua_ve_chi_cuc" for c in chi_tiet_thuc_te
    )
    thang_bi_loai = [c["thang"] for c in chi_tiet_thuc_te if c["ly_do_loai"]]

    if so_thang_thuc_te == 0:
        return _empty_result(
            ghi_chu="Không có tháng thực tế làm việc trong quý",
            chi_tiet_thuc_te=chi_tiet_thuc_te,
            co_thai_san=co_thai_san,
            co_chuyen_don_vi=co_chuyen_don_vi,
            is_lanh_dao=is_lanh_dao,
        )

    # 3. Build map thang → chi tiết ngày làm việc
    thang_info = {c["thang"]: c for c in chi_tiet_thuc_te}

    # 4. Lũy kế a/b/c qua các tháng thực tế
    cac_thang = []
    so_thang_co_du_lieu = 0

    if is_lanh_dao:
        tong_cv = 0
        tong_ht = 0
        tong_diem_td = 0.0
        tong_diem_cl = 0.0
        d_values: List[Optional[float]] = []
        dd_values: List[Optional[float]] = []
        e_values: List[Optional[float]] = []

        for thang in thang_list:
            info = thang_info[thang]
            if info["ly_do_loai"]:
                # Tháng bị loại — chỉ show chi tiết, không cộng dồn
                cac_thang.append(_thang_placeholder(thang, info))
                continue

            cv_data = await _tinh_cv_lanh_dao_thang(db, cong_chuc_id, thang, nam, tam_tinh=tam_tinh)
            tong_cv += cv_data["tong_cv"]
            tong_ht += cv_data["hoan_thanh"]
            tong_diem_td += cv_data["diem_tien_do"]
            tong_diem_cl += cv_data["diem_chat_luong"]

            dde = await _lay_dde_thang(db, cong_chuc_id, thang, nam)
            d_values.append(dde["d"] if dde else None)
            dd_values.append(dde["dd"] if dde else None)
            e_values.append(dde["e"] if dde else None)

            diem_tc_thang = await _lay_tc_chung_thang(db, cong_chuc_id, thang, nam)
            if cv_data["tong_cv"] > 0 or dde is not None or diem_tc_thang > 0:
                so_thang_co_du_lieu += 1

            # Chỉ số tháng
            a_t = min(cv_data["hoan_thanh"] / cv_data["tong_cv"], 1.0) if cv_data["tong_cv"] > 0 else 0.0
            b_t = min(cv_data["diem_tien_do"] / cv_data["tong_cv"], 1.0) if cv_data["tong_cv"] > 0 else 0.0
            c_t = min(cv_data["diem_chat_luong"] / cv_data["tong_cv"], 1.0) if cv_data["tong_cv"] > 0 else 0.0
            d_t = dde["d"] if dde else 1.0
            dd_t = dde["dd"] if dde else 1.0
            e_t = dde["e"] if dde else 1.0
            kpi_t = (a_t + b_t + c_t + d_t + dd_t + e_t) / 6
            diem_70_t = min(70.0, kpi_t * 70)
            diem_tong_t = float(diem_tc_thang) + diem_70_t

            cac_thang.append({
                "thang": thang,
                "diem_kpi": diem_70_t,
                "diem_tc": float(diem_tc_thang),
                "diem_tong": diem_tong_t,
                "xep_loai_thang": xep_loai_kpi(diem_tong_t) if diem_70_t > 0 or diem_tc_thang > 0 else None,
                "co_du_lieu": cv_data["tong_cv"] > 0,
                "nguon": "real_time",
                "a_so_luong": a_t,
                "b_tien_do": b_t,
                "c_chat_luong": c_t,
                "d_ket_qua": d_t,
                "dd_to_chuc": dd_t,
                "e_doan_ket": e_t,
            })

        # Lũy kế
        a_quy = min(tong_ht / tong_cv, 1.0) if tong_cv > 0 else 0.0
        b_quy = min(tong_diem_td / tong_cv, 1.0) if tong_cv > 0 else 0.0
        c_quy = min(tong_diem_cl / tong_cv, 1.0) if tong_cv > 0 else 0.0

        # d/đ/e QUÝ = MIN các tháng thực tế; NULL coi như 100% (tháng chưa có DDE)
        d_quy = min((v if v is not None else 1.0) for v in d_values) if d_values else 1.0
        dd_quy = min((v if v is not None else 1.0) for v in dd_values) if dd_values else 1.0
        e_quy = min((v if v is not None else 1.0) for v in e_values) if e_values else 1.0

        kpi_quy_ratio = (a_quy + b_quy + c_quy + d_quy + dd_quy + e_quy) / 6
        diem_kpi_quy = min(70.0, kpi_quy_ratio * 70)

        chi_tiet_metrics = {
            "a_so_luong": a_quy,
            "b_tien_do": b_quy,
            "c_chat_luong": c_quy,
            "d_ket_qua": d_quy,
            "dd_to_chuc": dd_quy,
            "e_doan_ket": e_quy,
        }

    else:
        # CC thường — lũy kế SP
        tong_sp_giao = Decimal("0")
        tong_sp_ht = Decimal("0")
        tong_sp_td = Decimal("0")
        tong_sp_cl = Decimal("0")

        for thang in thang_list:
            info = thang_info[thang]
            if info["ly_do_loai"]:
                cac_thang.append(_thang_placeholder(thang, info))
                continue

            sp_giao_thang = Decimal(str(info["so_ngay_lam_viec"])) * Decimal(str(SP_PER_DAY))
            sp_data = await _tinh_sp_cc_thuong_thang(db, cong_chuc_id, thang, nam, tam_tinh=tam_tinh)

            tong_sp_giao += sp_giao_thang
            tong_sp_ht += sp_data["tong_sp"]
            tong_sp_td += sp_data["sp_tien_do"]
            tong_sp_cl += sp_data["sp_chat_luong"]

            diem_tc_thang = await _lay_tc_chung_thang(db, cong_chuc_id, thang, nam)
            if sp_data["tong_sp"] > 0 or diem_tc_thang > 0:
                so_thang_co_du_lieu += 1

            # Chỉ số tháng (hiển thị)
            if sp_giao_thang > 0:
                a_t = min(1.0, float(sp_data["tong_sp"] / sp_giao_thang))
                b_t = min(1.0, float(sp_data["sp_tien_do"] / sp_giao_thang))
                c_t = min(1.0, float(sp_data["sp_chat_luong"] / sp_giao_thang))
            else:
                a_t = b_t = c_t = 0.0
            kpi_t = (a_t + b_t + c_t) / 3
            diem_70_t = min(70.0, kpi_t * 70)
            diem_tong_t = float(diem_tc_thang) + diem_70_t

            cac_thang.append({
                "thang": thang,
                "diem_kpi": diem_70_t,
                "diem_tc": float(diem_tc_thang),
                "diem_tong": diem_tong_t,
                "xep_loai_thang": xep_loai_kpi(diem_tong_t) if diem_70_t > 0 or diem_tc_thang > 0 else None,
                "co_du_lieu": sp_data["tong_sp"] > 0,
                "nguon": "real_time",
                "a_so_luong": a_t,
                "b_tien_do": b_t,
                "c_chat_luong": c_t,
            })

        if tong_sp_giao > 0:
            a_quy = min(1.0, float(tong_sp_ht / tong_sp_giao))
            b_quy = min(1.0, float(tong_sp_td / tong_sp_giao))
            c_quy = min(1.0, float(tong_sp_cl / tong_sp_giao))
        else:
            a_quy = b_quy = c_quy = 0.0

        kpi_quy_ratio = (a_quy + b_quy + c_quy) / 3
        diem_kpi_quy = min(70.0, kpi_quy_ratio * 70)

        chi_tiet_metrics = {
            "a_so_luong": a_quy,
            "b_tien_do": b_quy,
            "c_chat_luong": c_quy,
            "d_ket_qua": None,
            "dd_to_chuc": None,
            "e_doan_ket": None,
        }

    # 5. Điểm tiêu chí chung quý = TB các tháng thực tế
    tong_tc = Decimal("0")
    tc_chi_tiet_thang = []
    for thang in thang_list:
        diem_tc_thang = await _lay_tc_chung_thang(db, cong_chuc_id, thang, nam)
        tc_chi_tiet_thang.append({"thang": thang, "diem_tc": float(diem_tc_thang)})
        if thang in thang_thuc_te:
            tong_tc += diem_tc_thang

    diem_tc_quy = (
        tong_tc / Decimal(str(so_thang_thuc_te)) if so_thang_thuc_te > 0 else Decimal("0")
    )
    diem_tc_quy = max(Decimal("0"), min(Decimal("30"), diem_tc_quy))

    # 6. Điểm tổng + xếp loại
    diem_tong_quy = float(diem_tc_quy) + float(diem_kpi_quy)
    xep_loai = xep_loai_kpi(diem_tong_quy)

    # 7. Ghi chú
    ghi_chu_parts = []
    if co_chuyen_don_vi:
        ghi_chu_parts.append(
            f"CC mới chuyển công tác — loại tháng: "
            f"{', '.join(str(c['thang']) for c in chi_tiet_thuc_te if c['ly_do_loai'] == 'chua_ve_chi_cuc')}"
        )
    if co_thai_san:
        ghi_chu_parts.append(
            f"CC nghỉ thai sản — loại tháng: "
            f"{', '.join(str(c['thang']) for c in chi_tiet_thuc_te if c['ly_do_loai'] == 'thai_san')}"
        )
    thang_nghi_tron = [c["thang"] for c in chi_tiet_thuc_te if c["ly_do_loai"] == "nghi_tron_thang"]
    if thang_nghi_tron:
        ghi_chu_parts.append(
            f"Nghỉ trọn tháng — loại tháng: {', '.join(str(t) for t in thang_nghi_tron)}"
        )
    if so_thang_co_du_lieu < so_thang_thuc_te:
        ghi_chu_parts.append(
            f"Chỉ có dữ liệu {so_thang_co_du_lieu}/{so_thang_thuc_te} tháng thực tế"
        )
    ghi_chu = " | ".join(ghi_chu_parts) if ghi_chu_parts else None

    return {
        "diem_kpi_quy": float(diem_kpi_quy),
        "diem_tc_quy": float(diem_tc_quy),
        "diem_tong_quy": diem_tong_quy,
        "xep_loai_quy": xep_loai,
        "is_lanh_dao": is_lanh_dao,
        "so_thang_thuc_te": so_thang_thuc_te,
        "so_thang_co_du_lieu": so_thang_co_du_lieu,
        "co_chuyen_don_vi": co_chuyen_don_vi,
        "co_thai_san": co_thai_san,
        "thang_bi_loai": thang_bi_loai,
        "ghi_chu": ghi_chu,
        "cac_thang": cac_thang,
        "tieu_chi_quy": {
            "diem_tc_quy": diem_tc_quy,
            "chi_tiet_thang": tc_chi_tiet_thang,
        },
        "chi_tiet_thuc_te": chi_tiet_thuc_te,
        **chi_tiet_metrics,
    }


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _empty_result(
    ghi_chu: str,
    chi_tiet_thuc_te: Optional[list] = None,
    co_thai_san: bool = False,
    co_chuyen_don_vi: bool = False,
    is_lanh_dao: bool = False,
) -> dict:
    """Kết quả rỗng khi không đủ dữ liệu để tính quý."""
    return {
        "diem_kpi_quy": None,
        "diem_tc_quy": None,
        "diem_tong_quy": None,
        "xep_loai_quy": None,
        "is_lanh_dao": is_lanh_dao,
        "so_thang_thuc_te": 0,
        "so_thang_co_du_lieu": 0,
        "co_chuyen_don_vi": co_chuyen_don_vi,
        "co_thai_san": co_thai_san,
        "thang_bi_loai": [c["thang"] for c in (chi_tiet_thuc_te or []) if c.get("ly_do_loai")],
        "ghi_chu": ghi_chu,
        "cac_thang": [],
        "tieu_chi_quy": {"diem_tc_quy": Decimal("0"), "chi_tiet_thang": []},
        "chi_tiet_thuc_te": chi_tiet_thuc_te or [],
        "a_so_luong": 0.0,
        "b_tien_do": 0.0,
        "c_chat_luong": 0.0,
        "d_ket_qua": None,
        "dd_to_chuc": None,
        "e_doan_ket": None,
    }


def _thang_placeholder(thang: int, info: dict) -> dict:
    """Row hiển thị cho tháng bị loại khỏi tính quý."""
    ly_do_map = {
        "chua_ve_chi_cuc": "Chưa về Chi cục",
        "thai_san": "Nghỉ thai sản",
        "nghi_tron_thang": "Nghỉ trọn tháng",
    }
    return {
        "thang": thang,
        "diem_kpi": 0.0,
        "diem_tc": 0.0,
        "diem_tong": 0.0,
        "xep_loai_thang": None,
        "co_du_lieu": False,
        "nguon": ly_do_map.get(info["ly_do_loai"], "loai_khoi_tinh"),
        "a_so_luong": 0.0,
        "b_tien_do": 0.0,
        "c_chat_luong": 0.0,
        "d_ket_qua": None,
        "dd_to_chuc": None,
        "e_doan_ket": None,
    }


# =============================================================================
# BACKWARD-COMPAT STUBS
# =============================================================================

async def lay_tieu_chi_quy(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang_list: List[int],
    nam: int,
) -> dict:
    """
    DEPRECATED — dùng `tinh_diem_quy()` thay thế (field `tieu_chi_quy`).
    Giữ lại để không phá caller khác nếu có. Luôn chia `len(thang_list)`.
    """
    tong = Decimal("0")
    chi_tiet = []
    for thang in thang_list:
        diem = await _lay_tc_chung_thang(db, cong_chuc_id, thang, nam)
        chi_tiet.append({"thang": thang, "diem_tc": float(diem)})
        tong += diem
    n = max(1, len(thang_list))
    diem_quy = max(Decimal("0"), min(Decimal("30"), tong / Decimal(str(n))))
    return {"diem_tc_quy": diem_quy, "chi_tiet_thang": chi_tiet}


async def kiem_tra_chuyen_don_vi(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang_list: List[int],
    nam: int,
) -> bool:
    """
    DEPRECATED — tinh_diem_quy giờ xử lý trực tiếp qua `cc.ngay_vao_chi_cuc`.
    Giữ lại chữ ký cũ: trả True nếu `DanhGiaThang` có >1 don_vi_id_snapshot khác nhau.
    """
    stmt = (
        select(DanhGiaThang.don_vi_id_snapshot)
        .where(DanhGiaThang.cong_chuc_id == cong_chuc_id)
        .where(DanhGiaThang.thang.in_(thang_list))
        .where(DanhGiaThang.nam == nam)
        .where(DanhGiaThang.is_deleted == False)
    )
    result = await db.execute(stmt)
    don_vi_ids = [row[0] for row in result.fetchall() if row[0]]
    return len(set(don_vi_ids)) > 1
