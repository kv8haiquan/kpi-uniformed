"""
app/api/v1/endpoints/xep_loai_moi.py
====================================
API Endpoints cho màn hình Xếp loại KPI mới (v2.6.0).

Tính năng chính:
1. Consolidated view cho ĐT/CCT xem tất cả CC trong đơn vị/chi cục
2. Hỗ trợ filter theo đơn vị, trạng thái
3. Chi tiết phê duyệt 2 cấp
4. API khóa dữ liệu (lock data)
5. Tab Tạm tính (v2.7.0) - tính cả công việc CHỜ PHÊ DUYỆT

Phiên bản: 2.7.0 (04/03/2026)
"""

import calendar
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, or_, case, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import DatabaseDep, ActiveUserDep, is_qldv
from app.core.kpi_calculator_v2 import calculate_kpi_score_v2
from app.core.kpi_version import resolve_kpi_version, VERSION_V2
from app.core.hdld_vb714 import is_hdld_vb714_active, tinh_diem_kpi_70_hdld_vb714
from app.models.kpi_assessment import (
    DanhGiaThang,
    TieuChiChungDanhGia,
    TrangThaiTieuChi,
    TrangThaiDanhGia,
)
from app.models.kpi_submission import KeKhaiCongViec, TrangThaiKeKhai
from app.models.leader_kpi import KeKhaiLanhDao, TrangThaiKeKhaiLD, DanhGiaDDE, TrangThaiDDE, TrangThaiHoanThanh
from app.models.leave import DangKyNghi, TrangThaiNghi
from app.models.user_org import CongChuc, VaiTro, CapBacVaiTro, DonVi
from app.models.lich_su_dieu_chinh import LichSuDieuChinh, LoaiDoiTuongDieuChinh
from app.schemas.common import success_response, error_response


router = APIRouter()


async def tinh_diem_kpi_70_v2(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
    tam_tinh: bool = False,
) -> dict:
    """
    PL3 V2 — Tính điểm KPI 70 cho CC từ kê khai V2_PL3.

    Mẫu số (LOCKED 1): SUM(so_sp_goc_quy_doi) bản đã DA_PHE_DUYET (hoặc kèm
    CHO_PHE_DUYET nếu tam_tinh=True).

    Tử số (theo pattern V1):
      - tong_hoan_thanh = SUM(so_sp_goc_quy_doi)  (mọi bản đã duyệt = đã hoàn thành)
      - sp_chat_luong   = SUM(so_sp_chat_luong)   (đã trừ lỗi CL khi phê duyệt)
      - sp_tien_do      = SUM(so_sp_tien_do)      (đã trừ lỗi TĐ khi phê duyệt)

    Trường hợp NHAP/CHO_PHE_DUYET ở chế độ tam_tinh: dùng công thức tuyến tính
    với tu_danh_gia_chat_luong/tu_danh_gia_tien_do.

    LOCKED 5: mẫu số = 0 → KPI = 0 → caller xếp D.
    """
    if tam_tinh:
        allowed = [TrangThaiKeKhai.NHAP, TrangThaiKeKhai.CHO_PHE_DUYET, TrangThaiKeKhai.DA_PHE_DUYET]
    else:
        allowed = [TrangThaiKeKhai.DA_PHE_DUYET]

    stmt = (
        select(
            KeKhaiCongViec.trang_thai,
            KeKhaiCongViec.so_luong,
            KeKhaiCongViec.so_sp_goc_quy_doi,
            KeKhaiCongViec.so_sp_chat_luong,
            KeKhaiCongViec.so_sp_tien_do,
            KeKhaiCongViec.tu_danh_gia_chat_luong,
            KeKhaiCongViec.tu_danh_gia_tien_do,
            KeKhaiCongViec.he_so_quy_doi_snapshot,
        )
        .where(KeKhaiCongViec.cong_chuc_id == cong_chuc_id)
        .where(KeKhaiCongViec.thang == thang)
        .where(KeKhaiCongViec.nam == nam)
        .where(KeKhaiCongViec.version_kekhai == "V2_PL3")
        .where(KeKhaiCongViec.is_deleted == False)  # noqa: E712
        .where(KeKhaiCongViec.trang_thai.in_(allowed))
    )
    rows = (await db.execute(stmt)).all()

    tong_sp_ke_khai = Decimal("0")
    tong_hoan_thanh = Decimal("0")
    sp_cl = Decimal("0")
    sp_td = Decimal("0")

    for trang_thai, so_luong, sp_goc, sp_cl_row, sp_td_row, tu_dg_cl, tu_dg_td, he_so in rows:
        sp_goc_d = Decimal(str(sp_goc or 0))
        so_luong_v = so_luong or 1

        # Mẫu số = mọi bản trong allowed status
        tong_sp_ke_khai += sp_goc_d
        tong_hoan_thanh += sp_goc_d  # CC: mọi bản đã duyệt = đã hoàn thành

        if trang_thai == TrangThaiKeKhai.DA_PHE_DUYET:
            sp_cl += Decimal(str(sp_cl_row or 0))
            sp_td += Decimal(str(sp_td_row or 0))
        else:
            # NHAP/CHO_PHE_DUYET (chế độ tạm tính): tính từ tu_danh_gia
            tu_dg_cl_v = tu_dg_cl or 0
            tu_dg_td_v = tu_dg_td or 0
            if sp_goc_d > 0 and so_luong_v > 0:
                sp_per_unit = sp_goc_d / Decimal(str(so_luong_v))
                max_loi = so_luong_v * 4
                loi_cl = min(tu_dg_cl_v, max_loi)
                loi_td = min(tu_dg_td_v, max_loi)
                sp_cl += max(sp_goc_d - Decimal("0.25") * Decimal(str(loi_cl)) * sp_per_unit, Decimal("0"))
                sp_td += max(sp_goc_d - Decimal("0.25") * Decimal(str(loi_td)) * sp_per_unit, Decimal("0"))
            else:
                sp_cl += sp_goc_d
                sp_td += sp_goc_d

    # Tính KPI bằng helper V2
    kpi_result = calculate_kpi_score_v2(
        tong_hoan_thanh, sp_cl, sp_td, tong_sp_ke_khai
    )

    a = float(kpi_result["a"])
    b = float(kpi_result["b"])
    c = float(kpi_result["c"])
    diem_kpi = float(kpi_result["kpi"])
    diem_70 = min(70.0, diem_kpi * 70)
    ly_do_zero = kpi_result["ly_do"]

    # Backward-compat fields cho frontend cũ:
    # V2 không dùng "ngày × 96" làm mẫu số → các field so_ngay_*, sp_duoc_giao
    # vẫn trả về 0 để tránh frontend NaN.
    return {
        "version_tinh_diem": "V2_PL3",
        "so_ngay_trong_thang": 0,
        "so_ngay_nghi": 0,
        "so_ngay_lam_viec": 0,
        "sp_duoc_giao": float(tong_sp_ke_khai),  # V2: hiển thị mẫu số = tổng SP kê khai
        "tong_sp_hoan_thanh": float(tong_hoan_thanh),
        "sp_chat_luong": float(sp_cl),
        "sp_tien_do": float(sp_td),
        "tong_sp_ke_khai": float(tong_sp_ke_khai),
        "a_so_luong": a,
        # NOTE: theo legacy V1, key b_chat_luong thực ra là tỷ lệ tiến độ;
        # c_tien_do là tỷ lệ chất lượng. Giữ legacy key naming để tránh phá frontend.
        "b_chat_luong": c,  # = tỷ lệ tiến độ trong key naming legacy
        "c_tien_do": b,     # = tỷ lệ chất lượng trong key naming legacy
        "diem_kpi": diem_kpi,
        "diem_70": diem_70,
        "ly_do_kpi_zero": ly_do_zero,  # 'MAU_SO_BANG_0' hoặc None
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def tinh_diem_kpi_70(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
    tam_tinh: bool = False,
) -> dict:
    """
    Tính điểm KPI 70 điểm từ kê khai công việc đã duyệt (hoặc tạm tính).

    Công thức (theo Phụ lục I NĐ 335/2025/NĐ-CP):
    - a = SP_hoàn_thành / SP_được_giao (tỷ lệ số lượng)
    - b = SP_đúng_tiến_độ / SP_được_giao (tỷ lệ tiến độ — key "b_chat_luong" giữ nguyên vì lý do backward-compat, xem note bên dưới)
    - c = SP_đạt_chất_lượng / SP_được_giao (tỷ lệ chất lượng — key "c_tien_do" giữ nguyên)
    - Mỗi tỷ lệ cap tại 1.0 (100%)
    - Điểm = (a + b + c) / 3 × 70

    NOTE về naming (legacy):
      Các key trả về `b_chat_luong` và `c_tien_do` đặt ngược với quy ước spec
      (spec: b=tiến độ, c=chất lượng). Không đổi tên để tránh phá frontend.
      Caller cần đảo key khi ánh xạ sang template.

    Params:
    - tam_tinh: Nếu True, tính cả công việc CHỜ PHÊ DUYỆT và nghỉ phép CHỜ PHÊ DUYỆT
    """
    # =========================================================================
    # PL3 V2 dispatcher (28/04/2026)
    # =========================================================================
    version = await resolve_kpi_version(db, cong_chuc_id, thang, nam)
    if version == VERSION_V2:
        return await tinh_diem_kpi_70_v2(db, cong_chuc_id, thang, nam, tam_tinh=tam_tinh)
    # =========================================================================
    # V1 logic (giữ nguyên)
    # =========================================================================

    # Lấy số ngày nghỉ (đã duyệt hoặc cả chờ duyệt)
    if tam_tinh:
        # Tạm tính: bao gồm cả CHO_PHE_DUYET và DA_PHE_DUYET
        stmt_nghi = (
            select(func.coalesce(func.sum(DangKyNghi.so_ngay), Decimal("0")))
            .where(DangKyNghi.cong_chuc_id == cong_chuc_id)
            .where(DangKyNghi.thang_ap_dung == thang)
            .where(DangKyNghi.nam_ap_dung == nam)
            .where(DangKyNghi.trang_thai.in_([TrangThaiNghi.CHO_PHE_DUYET, TrangThaiNghi.DA_PHE_DUYET]))
            .where(DangKyNghi.is_deleted == False)
        )
    else:
        # Chính thức: chỉ DA_PHE_DUYET
        stmt_nghi = (
            select(func.coalesce(func.sum(DangKyNghi.so_ngay), Decimal("0")))
            .where(DangKyNghi.cong_chuc_id == cong_chuc_id)
            .where(DangKyNghi.thang_ap_dung == thang)
            .where(DangKyNghi.nam_ap_dung == nam)
            .where(DangKyNghi.trang_thai == TrangThaiNghi.DA_PHE_DUYET)
            .where(DangKyNghi.is_deleted == False)
        )
    result_nghi = await db.execute(stmt_nghi)
    tong_ngay_nghi = result_nghi.scalar() or Decimal("0")
    
    # Tính số ngày làm việc và SP được giao
    so_ngay_trong_thang = calendar.monthrange(nam, thang)[1]
    so_ngay_lam_viec = max(Decimal("0"), Decimal(str(so_ngay_trong_thang)) - tong_ngay_nghi)
    sp_duoc_giao = float(so_ngay_lam_viec) * 96
    
    # Lấy tổng SP - logic tạm tính giống ke_khai.py
    # Cần lấy chi tiết từng row vì kê khai chưa duyệt phải tính SP CL/TĐ từ tu_danh_gia
    if tam_tinh:
        allowed_statuses = [TrangThaiKeKhai.NHAP, TrangThaiKeKhai.CHO_PHE_DUYET, TrangThaiKeKhai.DA_PHE_DUYET]
    else:
        allowed_statuses = [TrangThaiKeKhai.DA_PHE_DUYET]

    detail_query = (
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

    detail_result = await db.execute(detail_query)
    detail_rows = detail_result.all()

    tong_sp = Decimal("0")
    sp_chat_luong = Decimal("0")
    sp_tien_do = Decimal("0")

    for row in detail_rows:
        (trang_thai_row, so_luong_row, sp_goc, sp_cl, sp_td, tu_dg_cl, tu_dg_td) = row
        sp_goc = Decimal(str(sp_goc or 0))
        so_luong_row = so_luong_row or 1

        tong_sp += sp_goc

        if trang_thai_row == TrangThaiKeKhai.DA_PHE_DUYET:
            # Đã duyệt: dùng giá trị đã tính sẵn
            sp_chat_luong += Decimal(str(sp_cl or 0))
            sp_tien_do += Decimal(str(sp_td or 0))
        else:
            # NHAP hoặc CHO_PHE_DUYET: tính từ tu_danh_gia
            tu_dg_cl = tu_dg_cl or 0
            tu_dg_td = tu_dg_td or 0

            if sp_goc > 0 and so_luong_row > 0:
                sp_per_unit = sp_goc / Decimal(str(so_luong_row))
                max_loi = so_luong_row * 4

                loi_tinh_cl = min(tu_dg_cl, max_loi)
                sp_tru_cl = Decimal("0.25") * Decimal(str(loi_tinh_cl)) * sp_per_unit
                sp_chat_luong += max(sp_goc - sp_tru_cl, Decimal("0"))

                loi_tinh_td = min(tu_dg_td, max_loi)
                sp_tru_td = Decimal("0.25") * Decimal(str(loi_tinh_td)) * sp_per_unit
                sp_tien_do += max(sp_goc - sp_tru_td, Decimal("0"))
            else:
                sp_chat_luong += sp_goc
                sp_tien_do += sp_goc

    tong_sp = float(tong_sp)
    sp_chat_luong = float(sp_chat_luong)
    sp_tien_do = float(sp_tien_do)
    
    # Tỷ lệ — CẢ 3 ĐỀU chia cho sp_duoc_giao (TARGET) theo Phụ lục I NĐ 335/2025/NĐ-CP
    # và cap riêng ≤ 1.0 để không vượt 100% dù kê khai hơn mức được giao.
    if sp_duoc_giao > 0:
        a_so_luong = min(1.0, tong_sp / sp_duoc_giao)
        b_chat_luong = min(1.0, sp_chat_luong / sp_duoc_giao)
        c_tien_do = min(1.0, sp_tien_do / sp_duoc_giao)
    else:
        a_so_luong = 0
        b_chat_luong = 0
        c_tien_do = 0

    # Điểm KPI = (a + b + c) / 3 × 70
    diem_kpi = (a_so_luong + b_chat_luong + c_tien_do) / 3
    diem_70 = min(70, diem_kpi * 70)  # Cap at 70
    
    return {
        "so_ngay_trong_thang": so_ngay_trong_thang,
        "so_ngay_nghi": float(tong_ngay_nghi),
        "so_ngay_lam_viec": float(so_ngay_lam_viec),
        "sp_duoc_giao": sp_duoc_giao,
        "tong_sp_hoan_thanh": tong_sp,
        "sp_chat_luong": sp_chat_luong,
        "sp_tien_do": sp_tien_do,
        "a_so_luong": a_so_luong,
        "b_chat_luong": b_chat_luong,
        "c_tien_do": c_tien_do,
        "diem_kpi": diem_kpi,
        "diem_70": diem_70,
    }


async def tinh_diem_kpi_70_lanh_dao(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
    tam_tinh: bool = False,
) -> dict:
    """
    Tính điểm KPI 70 điểm cho LÃNH ĐẠO từ KeKhaiLanhDao + DanhGiaDDE.

    Công thức (6 chỉ số):
    - a = CV_hoàn_thành / Tổng_CV (tỷ lệ số lượng)
    - b = Tổng_điểm_tiến_độ / Tổng_CV (mỗi CV: max(0, 1 - lỗi×0.25))
    - c = Tổng_điểm_chất_lượng / Tổng_CV
    - d = d_ket_qua_don_vi / 100
    - đ = dd_to_chuc_trien_khai / 100
    - e = e_doan_ket_noi_bo / 100
    - Điểm = (a + b + c + d + đ + e) / 6 × 70

    Phase 3 KPI LĐ V2 (05/05/2026): từ tháng 5/2026, scope a/b/c mở rộng
    sang SP cấp dưới (calc_kpi_lanh_dao_v2 trong app.core.kpi_lanh_dao_v2).
    """
    # Phase 3 V2: tháng ≥ 5/2026 → gọi service v2 (lấy chính thức = DA_PHE_DUYET)
    from app.core.kpi_lanh_dao_v2 import (
        calc_kpi_lanh_dao_v2,
        is_kpi_lanh_dao_v2_active,
    )

    if not tam_tinh and is_kpi_lanh_dao_v2_active(thang, nam):
        try:
            v2 = await calc_kpi_lanh_dao_v2(db, cong_chuc_id, thang, nam)
            diem_kpi = v2["kpi_tong"]
            diem_70 = min(70.0, diem_kpi * 70.0)
            return {
                "is_lanh_dao": True,
                # V2 dùng SP quy đổi → "tong_cong_viec" giữ làm số bản ghi để
                # FE cũ không vỡ, nhưng các SP fields phản ánh đúng số học.
                "tong_cong_viec": v2["so_kekhai_records"],
                "tong_hoan_thanh": v2["tong_sp_hoan_thanh"],
                "tong_diem_chat_luong": v2["sp_chat_luong"],
                "tong_diem_tien_do": v2["sp_tien_do"],
                "tong_loi_chat_luong": 0,
                "tong_loi_tien_do": 0,
                "a_so_luong": v2["a"],
                # 07/05/2026: rename theo legacy convention v2.b=CL, v2.c=TĐ
                "b_tien_do": v2["c"],
                "c_chat_luong": v2["b"],
                "d_ket_qua": v2["d"],
                "dd_to_chuc": v2["dd"],
                "e_doan_ket": v2["e"],
                "diem_kpi": diem_kpi,
                "diem_70": diem_70,
                "so_ngay_trong_thang": 0,
                "so_ngay_nghi": 0,
                "so_ngay_lam_viec": 0,
                "sp_duoc_giao": v2["tong_sp_ke_khai"],
                "tong_sp_hoan_thanh": v2["tong_sp_hoan_thanh"],
                "sp_chat_luong": v2["sp_chat_luong"],
                "sp_tien_do": v2["sp_tien_do"],
                "tong_sp_ke_khai": v2["tong_sp_ke_khai"],
                "b_chat_luong": v2["b"],
                "c_tien_do": v2["c"],
            }
        except ValueError:
            pass  # fallback nhánh cũ

    # Xác định trạng thái được tính
    if tam_tinh:
        allowed_statuses = [
            TrangThaiKeKhaiLD.NHAP.value,
            TrangThaiKeKhaiLD.CHO_PHE_DUYET.value,
            TrangThaiKeKhaiLD.DA_PHE_DUYET.value,
        ]
        dde_statuses = [TrangThaiDDE.NHAP.value, TrangThaiDDE.CHO_PHE_DUYET.value, TrangThaiDDE.DA_PHE_DUYET.value]
    else:
        allowed_statuses = [TrangThaiKeKhaiLD.DA_PHE_DUYET.value]
        dde_statuses = [TrangThaiDDE.DA_PHE_DUYET.value]

    # Query kê khai lãnh đạo
    stmt_kkld = (
        select(
            KeKhaiLanhDao.trang_thai_hoan_thanh,
            KeKhaiLanhDao.so_loi_chat_luong,
            KeKhaiLanhDao.so_loi_tien_do,
        )
        .where(KeKhaiLanhDao.cong_chuc_id == cong_chuc_id)
        .where(KeKhaiLanhDao.thang == thang)
        .where(KeKhaiLanhDao.nam == nam)
        .where(KeKhaiLanhDao.is_deleted == False)
        .where(KeKhaiLanhDao.trang_thai.in_(allowed_statuses))
    )
    result_kkld = await db.execute(stmt_kkld)
    rows = result_kkld.all()

    tong_cong_viec = len(rows)
    tong_hoan_thanh = 0
    tong_diem_chat_luong = 0.0
    tong_diem_tien_do = 0.0
    tong_loi_chat_luong = 0
    tong_loi_tien_do = 0

    for row in rows:
        (trang_thai_ht, loi_cl, loi_td) = row
        # Phụ lục I NĐ 335: chỉ CV ĐÃ HOÀN THÀNH đóng góp vào số lượng / tiến độ / chất lượng.
        # CV chưa hoàn thành không tính (không thể gọi là đúng TĐ / đạt CL).
        if trang_thai_ht != TrangThaiHoanThanh.DA_HOAN_THANH:
            continue
        tong_hoan_thanh += 1
        tong_loi_chat_luong += loi_cl
        tong_loi_tien_do += loi_td
        # Mỗi CV đóng góp max(0, 1 - lỗi × 0.25) cho điểm TĐ/CL
        tong_diem_chat_luong += max(0.0, 1.0 - loi_cl * 0.25)
        tong_diem_tien_do += max(0.0, 1.0 - loi_td * 0.25)

    # Tỷ lệ a, b, c
    a = min(tong_hoan_thanh / tong_cong_viec, 1) if tong_cong_viec > 0 else 0
    b = min(tong_diem_tien_do / tong_cong_viec, 1) if tong_cong_viec > 0 else 0
    c = min(tong_diem_chat_luong / tong_cong_viec, 1) if tong_cong_viec > 0 else 0

    # Query DDE
    stmt_dde = (
        select(DanhGiaDDE)
        .where(DanhGiaDDE.cong_chuc_id == cong_chuc_id)
        .where(DanhGiaDDE.thang == thang)
        .where(DanhGiaDDE.nam == nam)
        .where(DanhGiaDDE.trang_thai.in_(dde_statuses))
    )
    result_dde = await db.execute(stmt_dde)
    dde = result_dde.scalar_one_or_none()

    if dde:
        # Nếu tạm tính: dùng giá trị tự đánh giá, nếu chính thức: dùng final (ưu tiên phê duyệt)
        if tam_tinh:
            d_val = (dde.d_phe_duyet if dde.d_phe_duyet is not None else dde.d_ket_qua_don_vi) / 100.0
            dd_val = (dde.dd_phe_duyet if dde.dd_phe_duyet is not None else dde.dd_to_chuc_trien_khai) / 100.0
            e_val = (dde.e_phe_duyet if dde.e_phe_duyet is not None else dde.e_doan_ket_noi_bo) / 100.0
        else:
            d_val = dde.d_final / 100.0
            dd_val = dde.dd_final / 100.0
            e_val = dde.e_final / 100.0
    else:
        # Mặc định 100% nếu chưa có DDE
        d_val = 1.0
        dd_val = 1.0
        e_val = 1.0

    # Điểm KPI = (a + b + c + d + đ + e) / 6 × 70
    diem_kpi = (a + b + c + d_val + dd_val + e_val) / 6
    diem_70 = min(70, diem_kpi * 70)

    return {
        "is_lanh_dao": True,
        "tong_cong_viec": tong_cong_viec,
        "tong_hoan_thanh": tong_hoan_thanh,
        "tong_diem_chat_luong": tong_diem_chat_luong,
        "tong_diem_tien_do": tong_diem_tien_do,
        "tong_loi_chat_luong": tong_loi_chat_luong,
        "tong_loi_tien_do": tong_loi_tien_do,
        "a_so_luong": a,
        "b_tien_do": b,
        "c_chat_luong": c,
        "d_ket_qua": d_val,
        "dd_to_chuc": dd_val,
        "e_doan_ket": e_val,
        "diem_kpi": diem_kpi,
        "diem_70": diem_70,
        # Backward compatibility fields (cho frontend cũ)
        "so_ngay_trong_thang": 0,
        "so_ngay_nghi": 0,
        "so_ngay_lam_viec": 0,
        "sp_duoc_giao": 0,
        "tong_sp_hoan_thanh": 0,
        "sp_chat_luong": 0,
        "sp_tien_do": 0,
        "b_chat_luong": c,  # alias
        "c_tien_do": b,  # alias
    }


async def tinh_diem_kpi_70_hd_111(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
    tam_tinh: bool = False,
) -> dict:
    """Tính điểm KPI 70 cho HĐ 111 từ KeKhaiLanhDao (chỉ 3 chỉ số a, b, c).

    Phase 3 (29/04/2026): HĐ 111 dùng form lãnh đạo nhưng KHÔNG có d/đ/e.

    Công thức:
    - a = CV_hoàn_thành / Tổng_CV
    - b = Tổng_điểm_tiến_độ / Tổng_CV (mỗi CV: max(0, 1 - lỗi×0.25))
    - c = Tổng_điểm_chất_lượng / Tổng_CV
    - Điểm = (a + b + c) / 3 × 70

    Caller chỉ nên gọi khi CC có data ke_khai_lanh_dao cho tháng đó.
    Tháng cũ (data ở ke_khai_cong_viec V1): dùng tinh_diem_kpi_70 thay thế.
    """
    if tam_tinh:
        allowed_statuses = [
            TrangThaiKeKhaiLD.NHAP.value,
            TrangThaiKeKhaiLD.CHO_PHE_DUYET.value,
            TrangThaiKeKhaiLD.DA_PHE_DUYET.value,
        ]
    else:
        allowed_statuses = [TrangThaiKeKhaiLD.DA_PHE_DUYET.value]

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
        .where(KeKhaiLanhDao.trang_thai.in_(allowed_statuses))
    )
    rows = (await db.execute(stmt)).all()

    tong_cong_viec = len(rows)
    tong_hoan_thanh = 0
    tong_diem_chat_luong = 0.0
    tong_diem_tien_do = 0.0
    tong_loi_chat_luong = 0
    tong_loi_tien_do = 0

    for row in rows:
        (trang_thai_ht, loi_cl, loi_td) = row
        if trang_thai_ht != TrangThaiHoanThanh.DA_HOAN_THANH:
            continue
        tong_hoan_thanh += 1
        tong_loi_chat_luong += loi_cl
        tong_loi_tien_do += loi_td
        tong_diem_chat_luong += max(0.0, 1.0 - loi_cl * 0.25)
        tong_diem_tien_do += max(0.0, 1.0 - loi_td * 0.25)

    a = min(tong_hoan_thanh / tong_cong_viec, 1) if tong_cong_viec > 0 else 0
    b = min(tong_diem_tien_do / tong_cong_viec, 1) if tong_cong_viec > 0 else 0
    c = min(tong_diem_chat_luong / tong_cong_viec, 1) if tong_cong_viec > 0 else 0

    # HD 111: 3 chỉ số → chia 3 (KHÔNG có d/đ/e)
    diem_kpi = (a + b + c) / 3
    diem_70 = min(70, diem_kpi * 70)

    return {
        "is_lanh_dao": False,
        "is_hd_111": True,
        "tong_cong_viec": tong_cong_viec,
        "tong_hoan_thanh": tong_hoan_thanh,
        "tong_diem_chat_luong": tong_diem_chat_luong,
        "tong_diem_tien_do": tong_diem_tien_do,
        "tong_loi_chat_luong": tong_loi_chat_luong,
        "tong_loi_tien_do": tong_loi_tien_do,
        "a_so_luong": a,
        "b_tien_do": b,
        "c_chat_luong": c,
        # KHÔNG có d, đ, e
        "diem_kpi": diem_kpi,
        "diem_70": diem_70,
        # Backward compatibility
        "so_ngay_trong_thang": 0,
        "so_ngay_nghi": 0,
        "so_ngay_lam_viec": 0,
        "sp_duoc_giao": 0,
        "tong_sp_hoan_thanh": 0,
        "sp_chat_luong": 0,
        "sp_tien_do": 0,
        "b_chat_luong": c,
        "c_tien_do": b,
    }


async def _has_ke_khai_lanh_dao(
    db: AsyncSession, cong_chuc_id: UUID, thang: int, nam: int
) -> bool:
    """Check user có bản kê khai trong ke_khai_lanh_dao cho tháng/năm này không.

    Dùng để quyết định HD 111 chấm theo công thức mới (form LĐ) hay V1 (data cũ).
    """
    stmt = (
        select(func.count(KeKhaiLanhDao.id))
        .where(KeKhaiLanhDao.cong_chuc_id == cong_chuc_id)
        .where(KeKhaiLanhDao.thang == thang)
        .where(KeKhaiLanhDao.nam == nam)
        .where(KeKhaiLanhDao.is_deleted == False)
    )
    cnt = (await db.execute(stmt)).scalar() or 0
    return cnt > 0


def xep_loai_kpi(diem_tong: float) -> str:
    """Xếp loại KPI theo điểm tổng."""
    if diem_tong >= 90:
        return "A"
    elif diem_tong >= 70:
        return "B"
    elif diem_tong >= 50:
        return "C"
    else:
        return "D"


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get("/tong-hop")
async def get_tong_hop_xep_loai(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int = Query(..., ge=1, le=12, description="Tháng"),
    nam: int = Query(..., description="Năm"),
    don_vi_id: Optional[UUID] = Query(None, description="Lọc theo đơn vị"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tam_tinh: bool = Query(False, description="Tính cả công việc chờ duyệt (tạm tính)"),
) -> dict:
    """
    Lấy danh sách tổng hợp xếp loại KPI của CC trong đơn vị/chi cục.

    Quyền:
    - ĐT: Xem CC trong đơn vị mình
    - PCCT/CCT: Xem tất cả CC trong chi cục

    Params:
    - tam_tinh: Nếu True, trả về dữ liệu tạm tính (bao gồm CHỜ PHÊ DUYỆT)
    """
    # Kiểm tra quyền
    cap_bac = None
    if current_user.vai_tro:
        cap_bac = current_user.vai_tro.cap_bac

    has_view_all = getattr(current_user, 'can_view_all_units', False)
    is_lanh_dao_chi_cuc = cap_bac in [CapBacVaiTro.CHI_CUC_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG] or has_view_all
    is_lanh_dao_don_vi = cap_bac in [CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI]
    is_quan_ly_dv = is_qldv(current_user)

    if not (is_lanh_dao_chi_cuc or is_lanh_dao_don_vi or is_quan_ly_dv):
        raise HTTPException(
            status_code=403,
            detail=error_response(code="PERM_001", message="Chỉ lãnh đạo mới được xem tổng hợp xếp loại")
        )

    # Xác định đơn vị cần lọc
    filter_don_vi_id = None
    if is_lanh_dao_chi_cuc:
        # CCT/PCCT có thể xem tất cả hoặc lọc theo đơn vị
        filter_don_vi_id = don_vi_id
    else:
        # ĐT/PĐT/QLDV chỉ xem đơn vị mình
        filter_don_vi_id = current_user.don_vi_id
    
    # Query danh sách CC (loại trừ ADMIN và QLDV khỏi báo cáo)
    _excluded_roles = [CapBacVaiTro.SUPER_ADMIN, CapBacVaiTro.QUAN_LY_DON_VI]
    stmt_cc = (
        select(CongChuc)
        .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id, isouter=True)
        .options(
            selectinload(CongChuc.don_vi),
            selectinload(CongChuc.vai_tro),
        )
        .where(CongChuc.is_deleted == False)
        .where(CongChuc.is_active == True)
        .where(
            or_(
                CongChuc.vai_tro_id == None,
                ~VaiTro.cap_bac.in_(_excluded_roles),
            )
        )
    )

    if filter_don_vi_id:
        stmt_cc = stmt_cc.where(CongChuc.don_vi_id == filter_don_vi_id)

    # FIX Issue #2 (27/02/2026): Sort theo chức vụ (cấp bậc) → họ tên
    # Dùng SQLAlchemy CASE expression để sort theo thứ tự cấp bậc
    cap_bac_order = case(
        (VaiTro.cap_bac == "CHI_CUC_TRUONG", 1),
        (VaiTro.cap_bac == "PHO_CHI_CUC_TRUONG", 2),
        (VaiTro.cap_bac == "TRUONG_DON_VI", 3),
        (VaiTro.cap_bac == "QUAN_LY_DON_VI", 4),
        (VaiTro.cap_bac == "PHO_DON_VI", 5),
        (VaiTro.cap_bac == "CONG_CHUC", 6),
        (VaiTro.cap_bac == "TCCB", 7),
        else_=99
    )
    stmt_cc = stmt_cc.order_by(cap_bac_order, CongChuc.ho_ten)

    # Count total (cũng loại trừ ADMIN và QLDV)
    count_stmt = (
        select(func.count(CongChuc.id))
        .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id, isouter=True)
        .where(CongChuc.is_deleted == False)
        .where(CongChuc.is_active == True)
        .where(
            or_(
                CongChuc.vai_tro_id == None,
                ~VaiTro.cap_bac.in_(_excluded_roles),
            )
        )
    )
    if filter_don_vi_id:
        count_stmt = count_stmt.where(CongChuc.don_vi_id == filter_don_vi_id)
    
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # Pagination
    offset = (page - 1) * page_size
    stmt_cc = stmt_cc.offset(offset).limit(page_size)
    
    result_cc = await db.execute(stmt_cc)
    cong_chucs = result_cc.scalars().all()
    
    # Build response
    items = []
    for cc in cong_chucs:
        # Lấy đánh giá tháng
        stmt_dg = (
            select(DanhGiaThang)
            .options(
                selectinload(DanhGiaThang.tieu_chi_chungs),
                selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap1),
                selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap2),
            )
            .where(DanhGiaThang.cong_chuc_id == cc.id)
            .where(DanhGiaThang.thang == thang)
            .where(DanhGiaThang.nam == nam)
            .where(DanhGiaThang.is_deleted == False)
        )
        result_dg = await db.execute(stmt_dg)
        danh_gia = result_dg.scalar_one_or_none()
        
        # Tính điểm 70 (truyền tam_tinh flag)
        # Lãnh đạo: công thức 6 chỉ số (a..e)
        # HĐ 111: công thức 3 chỉ số (a, b, c) — chỉ khi có data ke_khai_lanh_dao,
        #         tháng cũ chưa có thì fall back V1 (Phase 3 — 29/04/2026).
        # Công chức thường: V1 hoặc V2_PL3 (đã dispatch trong tinh_diem_kpi_70).
        if cc.is_lanh_dao:
            diem_70_data = await tinh_diem_kpi_70_lanh_dao(db, cc.id, thang, nam, tam_tinh=tam_tinh)
        elif cc.is_hd_111 and is_hdld_vb714_active(thang, nam) and (
            _hdld_vb714 := await tinh_diem_kpi_70_hdld_vb714(db, cc.id, thang, nam, tam_tinh=tam_tinh)
        ) is not None:
            # HĐLĐ 111 từ T5/2026: Bộ tiêu chí VB714 (3 tiêu chí × cấp quản lý)
            diem_70_data = _hdld_vb714
        elif cc.is_hd_111 and await _has_ke_khai_lanh_dao(db, cc.id, thang, nam):
            diem_70_data = await tinh_diem_kpi_70_hd_111(db, cc.id, thang, nam, tam_tinh=tam_tinh)
        else:
            diem_70_data = await tinh_diem_kpi_70(db, cc.id, thang, nam, tam_tinh=tam_tinh)

        # Điểm 30 (tiêu chí chung)
        # Nếu tam_tinh=True, lấy điểm tự chấm, nếu False lấy điểm phê duyệt
        # Nếu tam_tinh=True và CC chưa tự chấm → mặc định 20 điểm
        diem_30 = 0
        diem_30_tu_cham = 0
        trang_thai_tc = None
        if danh_gia:
            if tam_tinh:
                # Tạm tính: lấy tổng điểm tự chấm từ các tiêu chí
                if danh_gia.tieu_chi_chungs:
                    diem_30_tu_cham = sum(
                        float(tc.diem_tu_cham or 0) for tc in danh_gia.tieu_chi_chungs
                    )
                    diem_30 = diem_30_tu_cham if diem_30_tu_cham > 0 else 20
                elif danh_gia.diem_tieu_chi_chung:
                    diem_30 = float(danh_gia.diem_tieu_chi_chung)
                else:
                    # Chưa tự chấm tiêu chí → mặc định 20 điểm
                    diem_30 = 20
            else:
                # Chính thức: lấy điểm phê duyệt
                if danh_gia.diem_tieu_chi_chung:
                    diem_30 = float(danh_gia.diem_tieu_chi_chung)
            if danh_gia.trang_thai_tc:
                trang_thai_tc = danh_gia.trang_thai_tc.value
        elif tam_tinh:
            # Chưa có bản ghi đánh giá → mặc định 20 điểm cho tạm tính
            diem_30 = 20

        # Tổng điểm và xếp loại
        diem_tong = diem_30 + diem_70_data["diem_70"]
        xep_loai = xep_loai_kpi(diem_tong)

        items.append({
            "cong_chuc_id": cc.id,
            "ma_cc": cc.ma_cc,
            "ho_ten": cc.ho_ten,
            "chuc_vu": cc.chuc_vu,
            "don_vi_id": cc.don_vi_id,
            "don_vi_ten": cc.don_vi.ten_don_vi if cc.don_vi else None,
            "cap_bac": cc.vai_tro.cap_bac.value if cc.vai_tro else None,

            # Điểm số
            "diem_30": diem_30,
            "diem_70": diem_70_data["diem_70"],
            "diem_tong": diem_tong,
            "xep_loai": xep_loai,
            
            # Trạng thái
            "trang_thai_tc": trang_thai_tc,
            "is_khoa": danh_gia.is_khoa if danh_gia else False,

            # Chi tiết 70đ (đầy đủ cho tab Tạm tính)
            "so_ngay_trong_thang": diem_70_data["so_ngay_trong_thang"],
            "so_ngay_nghi": diem_70_data["so_ngay_nghi"],
            "so_ngay_lam_viec": diem_70_data["so_ngay_lam_viec"],
            "sp_duoc_giao": diem_70_data["sp_duoc_giao"],
            "tong_sp_hoan_thanh": diem_70_data["tong_sp_hoan_thanh"],
            "sp_chat_luong": diem_70_data["sp_chat_luong"],
            "sp_tien_do": diem_70_data["sp_tien_do"],
            "is_lanh_dao": cc.is_lanh_dao,
            # Phase 3 (29/04/2026): HĐ 111 — kê khai form LĐ, công thức 3 chỉ số
            "is_hd_111": cc.is_hd_111,
            "a_so_luong": diem_70_data["a_so_luong"],
            "b_chat_luong": diem_70_data["b_chat_luong"],
            "c_tien_do": diem_70_data["c_tien_do"],
            "diem_kpi": diem_70_data["diem_kpi"],
            # Leader-specific fields
            "tong_cong_viec": diem_70_data.get("tong_cong_viec"),
            "tong_hoan_thanh": diem_70_data.get("tong_hoan_thanh"),
            "tong_diem_chat_luong": diem_70_data.get("tong_diem_chat_luong"),
            "tong_diem_tien_do": diem_70_data.get("tong_diem_tien_do"),
            "d_ket_qua": diem_70_data.get("d_ket_qua"),
            "dd_to_chuc": diem_70_data.get("dd_to_chuc"),
            "e_doan_ket": diem_70_data.get("e_doan_ket"),

            # Phê duyệt 2 cấp
            "nguoi_phe_duyet_tc_cap1_id": danh_gia.nguoi_phe_duyet_tc_cap1_id if danh_gia else None,
            "nguoi_phe_duyet_tc_cap1_ten": danh_gia.nguoi_phe_duyet_tc_cap1.ho_ten if danh_gia and danh_gia.nguoi_phe_duyet_tc_cap1 else None,
            "ngay_phe_duyet_tc_cap1": danh_gia.ngay_phe_duyet_tc_cap1.isoformat() if danh_gia and danh_gia.ngay_phe_duyet_tc_cap1 else None,
            
            "nguoi_phe_duyet_tc_cap2_id": danh_gia.nguoi_phe_duyet_tc_cap2_id if danh_gia else None,
            "nguoi_phe_duyet_tc_cap2_ten": danh_gia.nguoi_phe_duyet_tc_cap2.ho_ten if danh_gia and danh_gia.nguoi_phe_duyet_tc_cap2 else None,
            "ngay_phe_duyet_tc_cap2": danh_gia.ngay_phe_duyet_tc_cap2.isoformat() if danh_gia and danh_gia.ngay_phe_duyet_tc_cap2 else None,
        })
    
    # Thống kê xếp loại
    thong_ke = {"A": 0, "B": 0, "C": 0, "D": 0}
    for item in items:
        thong_ke[item["xep_loai"]] += 1
    
    return success_response(
        data={
            "thang": thang,
            "nam": nam,
            "don_vi_id": filter_don_vi_id,
            "items": items,
            "thong_ke_xep_loai": thong_ke,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            }
        },
        message=f"Tổng hợp xếp loại KPI tháng {thang}/{nam}"
    )


@router.get("/chi-tiet/{cong_chuc_id}")
async def get_chi_tiet_xep_loai(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    cong_chuc_id: UUID,
    thang: int = Query(..., ge=1, le=12),
    nam: int = Query(...),
) -> dict:
    """
    Lấy chi tiết xếp loại KPI của 1 CC.
    
    Bao gồm:
    - Điểm tiêu chí chung (30đ) với chi tiết từng tiêu chí
    - Điểm kê khai (70đ) với chi tiết SP
    - Thông tin phê duyệt 2 cấp
    - Lịch sử điều chỉnh
    """
    # Kiểm tra quyền
    cap_bac = None
    if current_user.vai_tro:
        cap_bac = current_user.vai_tro.cap_bac
    
    is_self = cong_chuc_id == current_user.id
    has_view_all = getattr(current_user, 'can_view_all_units', False)
    is_lanh_dao_chi_cuc = cap_bac in [CapBacVaiTro.CHI_CUC_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG] or has_view_all
    # Lấy thông tin CC
    stmt_cc = (
        select(CongChuc)
        .options(selectinload(CongChuc.don_vi), selectinload(CongChuc.vai_tro))
        .where(CongChuc.id == cong_chuc_id)
    )
    result_cc = await db.execute(stmt_cc)
    cc = result_cc.scalar_one_or_none()

    if not cc:
        raise HTTPException(status_code=404, detail=error_response(code="NOT_FOUND", message="Công chức không tồn tại"))

    is_same_don_vi = cc.don_vi_id == current_user.don_vi_id
    is_lanh_dao_don_vi = is_same_don_vi and cap_bac in [CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI]
    is_quan_ly_dv = is_same_don_vi and is_qldv(current_user)

    if not (is_self or is_lanh_dao_chi_cuc or is_lanh_dao_don_vi or is_quan_ly_dv):
        raise HTTPException(status_code=403, detail=error_response(code="PERM_001", message="Không có quyền xem"))
    
    # Lấy đánh giá tháng
    stmt_dg = (
        select(DanhGiaThang)
        .options(
            selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(TieuChiChungDanhGia.tieu_chi),
            selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap1),
            selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap2),
        )
        .where(DanhGiaThang.cong_chuc_id == cong_chuc_id)
        .where(DanhGiaThang.thang == thang)
        .where(DanhGiaThang.nam == nam)
        .where(DanhGiaThang.is_deleted == False)
    )
    result_dg = await db.execute(stmt_dg)
    danh_gia = result_dg.scalar_one_or_none()
    
    # Tính điểm 70
    diem_70_data = await tinh_diem_kpi_70(db, cong_chuc_id, thang, nam)
    
    # Build tiêu chí chung
    tieu_chi_list = []
    diem_30 = 0
    if danh_gia and danh_gia.tieu_chi_chungs:
        for tc_dg in danh_gia.tieu_chi_chungs:
            tc = tc_dg.tieu_chi
            # Ưu tiên điểm "Đánh giá tháng" (override của LĐ) nếu có.
            if tc_dg.diem_danh_gia_thang is not None:
                diem = float(tc_dg.diem_danh_gia_thang)
            elif tc_dg.diem_phe_duyet:
                diem = float(tc_dg.diem_phe_duyet)
            else:
                diem = float(tc_dg.diem_tu_cham)
            diem_30 += diem
            
            tieu_chi_list.append({
                "ma_tieu_chi": tc.ma_tieu_chi,
                "ten_tieu_chi": tc.ten_tieu_chi,
                "nhom_tieu_chi": tc.nhom_tieu_chi,
                "diem_toi_da": float(tc.diem_toi_da),
                "is_achieved_cc": tc_dg.is_achieved_cc,
                "is_achieved_ld": tc_dg.is_achieved_ld,
                "diem_tu_cham": float(tc_dg.diem_tu_cham),
                "diem_phe_duyet": float(tc_dg.diem_phe_duyet) if tc_dg.diem_phe_duyet else None,
                "diem": diem,
                "ghi_chu_cc": tc_dg.ghi_chu_cc,
                "ghi_chu_ld": tc_dg.ghi_chu_ld,
                "ly_do_dieu_chinh": tc_dg.ly_do_dieu_chinh,
            })
    
    # Tổng điểm
    diem_tong = diem_30 + diem_70_data["diem_70"]
    xep_loai = xep_loai_kpi(diem_tong)
    
    # Lấy lịch sử điều chỉnh
    lich_su = []
    if danh_gia:
        stmt_ls = (
            select(LichSuDieuChinh)
            .options(selectinload(LichSuDieuChinh.nguoi_dieu_chinh))
            .where(LichSuDieuChinh.loai_doi_tuong == LoaiDoiTuongDieuChinh.DANH_GIA_THANG)
            .where(LichSuDieuChinh.doi_tuong_id == danh_gia.id)
            .order_by(LichSuDieuChinh.ngay_dieu_chinh.desc())
        )
        result_ls = await db.execute(stmt_ls)
        for ls in result_ls.scalars().all():
            lich_su.append({
                "id": ls.id,
                "truong_du_lieu": ls.truong_du_lieu,
                "gia_tri_cu": ls.gia_tri_cu,
                "gia_tri_moi": ls.gia_tri_moi,
                "ly_do": ls.ly_do,
                "nguoi_dieu_chinh_id": ls.nguoi_dieu_chinh_id,
                "nguoi_dieu_chinh_ten": ls.nguoi_dieu_chinh.ho_ten if ls.nguoi_dieu_chinh else None,
                "ngay_dieu_chinh": ls.ngay_dieu_chinh.isoformat(),
            })
    
    return success_response(
        data={
            # Thông tin CC
            "cong_chuc": {
                "id": cc.id,
                "ma_cc": cc.ma_cc,
                "ho_ten": cc.ho_ten,
                "chuc_vu": cc.chuc_vu,
                "don_vi_id": cc.don_vi_id,
                "don_vi_ten": cc.don_vi.ten_don_vi if cc.don_vi else None,
            },
            "thang": thang,
            "nam": nam,
            
            # Điểm số
            "diem_30": diem_30,
            "diem_70": diem_70_data["diem_70"],
            "diem_tong": diem_tong,
            "xep_loai": xep_loai,
            
            # Chi tiết 30đ
            "tieu_chi_chung": {
                "danh_gia_thang_id": danh_gia.id if danh_gia else None,
                "trang_thai_tc": danh_gia.trang_thai_tc.value if danh_gia and danh_gia.trang_thai_tc else None,
                "tieu_chi": tieu_chi_list,
            },
            
            # Chi tiết 70đ
            "ke_khai_cong_viec": diem_70_data,
            
            # Phê duyệt 2 cấp
            "phe_duyet": {
                "nguoi_phe_duyet_tc_cap1_id": danh_gia.nguoi_phe_duyet_tc_cap1_id if danh_gia else None,
                "nguoi_phe_duyet_tc_cap1_ten": danh_gia.nguoi_phe_duyet_tc_cap1.ho_ten if danh_gia and danh_gia.nguoi_phe_duyet_tc_cap1 else None,
                "ngay_phe_duyet_tc_cap1": danh_gia.ngay_phe_duyet_tc_cap1.isoformat() if danh_gia and danh_gia.ngay_phe_duyet_tc_cap1 else None,
                "diem_tc_cap1": float(danh_gia.diem_tc_cap1) if danh_gia and danh_gia.diem_tc_cap1 else None,
                
                "nguoi_phe_duyet_tc_cap2_id": danh_gia.nguoi_phe_duyet_tc_cap2_id if danh_gia else None,
                "nguoi_phe_duyet_tc_cap2_ten": danh_gia.nguoi_phe_duyet_tc_cap2.ho_ten if danh_gia and danh_gia.nguoi_phe_duyet_tc_cap2 else None,
                "ngay_phe_duyet_tc_cap2": danh_gia.ngay_phe_duyet_tc_cap2.isoformat() if danh_gia and danh_gia.ngay_phe_duyet_tc_cap2 else None,
                "diem_tc_cap2": float(danh_gia.diem_tc_cap2) if danh_gia and danh_gia.diem_tc_cap2 else None,
            },
            
            # Khóa dữ liệu
            "is_khoa": danh_gia.is_khoa if danh_gia else False,
            
            # Lịch sử điều chỉnh
            "lich_su_dieu_chinh": lich_su,
        },
        message=f"Chi tiết xếp loại KPI {cc.ho_ten} tháng {thang}/{nam}"
    )


@router.post("/khoa-du-lieu")
async def khoa_du_lieu(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int = Query(..., ge=1, le=12),
    nam: int = Query(...),
    don_vi_id: Optional[UUID] = Query(None, description="Khóa theo đơn vị (CCT khóa toàn chi cục nếu None)"),
) -> dict:
    """
    Khóa dữ liệu KPI tháng.
    
    Quyền:
    - ĐT: Khóa đơn vị mình
    - CCT: Khóa toàn chi cục
    
    Sau khi khóa:
    - Không thể chỉnh sửa kê khai công việc
    - Không thể chỉnh sửa đánh giá tiêu chí
    - Không thể chỉnh sửa đăng ký nghỉ
    """
    cap_bac = None
    if current_user.vai_tro:
        cap_bac = current_user.vai_tro.cap_bac

    is_cct = cap_bac == CapBacVaiTro.CHI_CUC_TRUONG
    is_dt = cap_bac == CapBacVaiTro.TRUONG_DON_VI

    # QLDV không có quyền khóa
    if is_qldv(current_user):
        raise HTTPException(
            status_code=403,
            detail=error_response(code="PERM_001", message="QLDV không có quyền khóa dữ liệu")
        )

    if not (is_cct or is_dt):
        raise HTTPException(
            status_code=403,
            detail=error_response(code="PERM_001", message="Chỉ CCT hoặc ĐT mới được khóa dữ liệu")
        )
    
    # Xác định phạm vi khóa
    if is_dt:
        # ĐT chỉ khóa đơn vị mình
        filter_don_vi_id = current_user.don_vi_id
    else:
        # CCT có thể khóa theo đơn vị hoặc toàn chi cục
        filter_don_vi_id = don_vi_id
    
    # Khóa DanhGiaThang
    stmt_dg = select(DanhGiaThang).where(
        DanhGiaThang.thang == thang,
        DanhGiaThang.nam == nam,
        DanhGiaThang.is_deleted == False
    )
    if filter_don_vi_id:
        # FIX v2.8.0 (27/02/2026): Dùng don_vi_id_snapshot để khóa đúng đơn vị lúc đánh giá
        stmt_dg = stmt_dg.where(DanhGiaThang.don_vi_id_snapshot == filter_don_vi_id)
    
    result_dg = await db.execute(stmt_dg)
    dg_list = result_dg.scalars().all()
    
    count_dg = 0
    for dg in dg_list:
        if not dg.is_khoa:
            dg.is_khoa = True
            count_dg += 1
    
    # Khóa KeKhaiCongViec
    stmt_kk = select(KeKhaiCongViec).where(
        KeKhaiCongViec.thang == thang,
        KeKhaiCongViec.nam == nam,
        KeKhaiCongViec.is_deleted == False
    )
    if filter_don_vi_id:
        # FIX v2.8.0 (27/02/2026): Dùng don_vi_id_snapshot để khóa đúng đơn vị lúc kê khai
        stmt_kk = stmt_kk.where(KeKhaiCongViec.don_vi_id_snapshot == filter_don_vi_id)
    
    result_kk = await db.execute(stmt_kk)
    kk_list = result_kk.scalars().all()
    
    count_kk = 0
    for kk in kk_list:
        if not kk.is_khoa:
            kk.is_khoa = True
            count_kk += 1
    
    # Khóa DangKyNghi
    stmt_np = select(DangKyNghi).where(
        DangKyNghi.thang_ap_dung == thang,
        DangKyNghi.nam_ap_dung == nam,
        DangKyNghi.is_deleted == False
    )
    if filter_don_vi_id:
        stmt_np = stmt_np.join(CongChuc).where(CongChuc.don_vi_id == filter_don_vi_id)
    
    result_np = await db.execute(stmt_np)
    np_list = result_np.scalars().all()
    
    count_np = 0
    for np in np_list:
        if not np.is_khoa:
            np.is_khoa = True
            count_np += 1
    
    await db.flush()
    
    return success_response(
        data={
            "thang": thang,
            "nam": nam,
            "don_vi_id": filter_don_vi_id,
            "so_danh_gia_khoa": count_dg,
            "so_ke_khai_khoa": count_kk,
            "so_nghi_phep_khoa": count_np,
        },
        message=f"Đã khóa dữ liệu tháng {thang}/{nam}"
    )


@router.post("/mo-khoa-du-lieu")
async def mo_khoa_du_lieu(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int = Query(..., ge=1, le=12),
    nam: int = Query(...),
    don_vi_id: Optional[UUID] = Query(None),
) -> dict:
    """
    Mở khóa dữ liệu KPI tháng.
    
    Chỉ CCT mới được mở khóa.
    """
    cap_bac = None
    if current_user.vai_tro:
        cap_bac = current_user.vai_tro.cap_bac

    # QLDV không có quyền mở khóa
    if is_qldv(current_user):
        raise HTTPException(
            status_code=403,
            detail=error_response(code="PERM_001", message="QLDV không có quyền mở khóa dữ liệu")
        )

    if cap_bac != CapBacVaiTro.CHI_CUC_TRUONG:
        raise HTTPException(
            status_code=403,
            detail=error_response(code="PERM_001", message="Chỉ Chi cục trưởng mới được mở khóa dữ liệu")
        )
    
    filter_don_vi_id = don_vi_id
    
    # Mở khóa DanhGiaThang
    stmt_dg = select(DanhGiaThang).where(
        DanhGiaThang.thang == thang,
        DanhGiaThang.nam == nam,
        DanhGiaThang.is_deleted == False
    )
    if filter_don_vi_id:
        # FIX v2.8.0 (27/02/2026): Dùng don_vi_id_snapshot để mở khóa đúng đơn vị lúc đánh giá
        # FIX v3.8 (07/07/2026): Mở khóa CẢ công chức chuyển đơn vị — khớp theo snapshot HOẶC
        # đơn vị HIỆN TẠI của CC. Trước đây chỉ lọc snapshot → CC chuyển VÀO đơn vị sau kỳ đánh
        # giá (bản ghi snapshot còn trỏ đơn vị cũ) không được mở khóa khi LĐ đơn vị mới mở khóa
        # → kẹt duyệt tiêu chí chung (BIZ_002 "Dữ liệu đã bị khóa"). Đồng bộ hướng v3.7 (luồng
        # duyệt đã route theo đơn vị hiện tại).
        stmt_dg = stmt_dg.join(CongChuc, CongChuc.id == DanhGiaThang.cong_chuc_id).where(
            or_(
                DanhGiaThang.don_vi_id_snapshot == filter_don_vi_id,
                CongChuc.don_vi_id == filter_don_vi_id,
            )
        )

    result_dg = await db.execute(stmt_dg)
    dg_list = result_dg.scalars().all()
    
    count_dg = 0
    for dg in dg_list:
        if dg.is_khoa:
            dg.is_khoa = False
            count_dg += 1
    
    # Mở khóa KeKhaiCongViec
    stmt_kk = select(KeKhaiCongViec).where(
        KeKhaiCongViec.thang == thang,
        KeKhaiCongViec.nam == nam,
        KeKhaiCongViec.is_deleted == False
    )
    if filter_don_vi_id:
        # FIX v2.8.0 (27/02/2026): Dùng don_vi_id_snapshot để mở khóa đúng đơn vị lúc kê khai
        # FIX v3.8 (07/07/2026): Mở khóa cả CC chuyển đơn vị — snapshot HOẶC đơn vị hiện tại
        # (xem giải thích ở phần mở khóa DanhGiaThang).
        stmt_kk = stmt_kk.join(CongChuc, CongChuc.id == KeKhaiCongViec.cong_chuc_id).where(
            or_(
                KeKhaiCongViec.don_vi_id_snapshot == filter_don_vi_id,
                CongChuc.don_vi_id == filter_don_vi_id,
            )
        )

    result_kk = await db.execute(stmt_kk)
    kk_list = result_kk.scalars().all()
    
    count_kk = 0
    for kk in kk_list:
        if kk.is_khoa:
            kk.is_khoa = False
            count_kk += 1
    
    # Mở khóa DangKyNghi
    stmt_np = select(DangKyNghi).where(
        DangKyNghi.thang_ap_dung == thang,
        DangKyNghi.nam_ap_dung == nam,
        DangKyNghi.is_deleted == False
    )
    if filter_don_vi_id:
        stmt_np = stmt_np.join(CongChuc).where(CongChuc.don_vi_id == filter_don_vi_id)
    
    result_np = await db.execute(stmt_np)
    np_list = result_np.scalars().all()
    
    count_np = 0
    for np in np_list:
        if np.is_khoa:
            np.is_khoa = False
            count_np += 1
    
    await db.flush()
    
    return success_response(
        data={
            "thang": thang,
            "nam": nam,
            "don_vi_id": filter_don_vi_id,
            "so_danh_gia_mo_khoa": count_dg,
            "so_ke_khai_mo_khoa": count_kk,
            "so_nghi_phep_mo_khoa": count_np,
        },
        message=f"Đã mở khóa dữ liệu tháng {thang}/{nam}"
    )


@router.get("/danh-sach-don-vi")
async def get_danh_sach_don_vi(
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Lấy danh sách đơn vị để filter.
    Dành cho CCT/PCCT.
    """
    cap_bac = None
    if current_user.vai_tro:
        cap_bac = current_user.vai_tro.cap_bac
    
    has_view_all = getattr(current_user, 'can_view_all_units', False)
    is_lanh_dao_chi_cuc = cap_bac in [CapBacVaiTro.CHI_CUC_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG] or has_view_all
    
    if not is_lanh_dao_chi_cuc:
        # ĐT/PĐT chỉ thấy đơn vị mình
        if current_user.don_vi:
            return success_response(
                data=[{
                    "id": current_user.don_vi.id,
                    "ma_don_vi": current_user.don_vi.ma_don_vi,
                    "ten_don_vi": current_user.don_vi.ten_don_vi,
                }],
                message="Danh sách đơn vị"
            )
        return success_response(data=[], message="Không có đơn vị")
    
    # CCT/PCCT thấy tất cả
    stmt = (
        select(DonVi)
        .where(DonVi.is_deleted == False)
        .where(DonVi.is_active == True)
        .order_by(DonVi.thu_tu, DonVi.ten_don_vi)
    )
    result = await db.execute(stmt)
    don_vis = result.scalars().all()
    
    return success_response(
        data=[{
            "id": dv.id,
            "ma_don_vi": dv.ma_don_vi,
            "ten_don_vi": dv.ten_don_vi,
        } for dv in don_vis],
        message=f"Danh sách {len(don_vis)} đơn vị"
    )