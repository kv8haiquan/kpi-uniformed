"""
app/api/v1/endpoints/xep_loai_moi.py
====================================
API Endpoints cho màn hình Xếp loại KPI mới (v2.6.0).

Tính năng chính:
1. Consolidated view cho ĐT/CCT xem tất cả CC trong đơn vị/chi cục
2. Hỗ trợ filter theo đơn vị, trạng thái
3. Chi tiết phê duyệt 2 cấp
4. API khóa dữ liệu (lock data)

Phiên bản: 2.6.0 (29/01/2026)
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
from app.models.kpi_assessment import (
    DanhGiaThang,
    TieuChiChungDanhGia,
    TrangThaiTieuChi,
    TrangThaiDanhGia,
)
from app.models.kpi_submission import KeKhaiCongViec, TrangThaiPheDuyet
from app.models.leave import DangKyNghi, TrangThaiNghi
from app.models.user_org import CongChuc, VaiTro, CapBacVaiTro, DonVi
from app.models.lich_su_dieu_chinh import LichSuDieuChinh, LoaiDoiTuongDieuChinh
from app.schemas.common import success_response, error_response


router = APIRouter()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def tinh_diem_kpi_70(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
) -> dict:
    """
    Tính điểm KPI 70 điểm từ kê khai công việc đã duyệt.
    
    Công thức:
    - a = SP_hoàn_thành / SP_được_giao (tỷ lệ số lượng)
    - b = SP_chất_lượng / SP_hoàn_thành (tỷ lệ chất lượng)
    - c = SP_tiến_độ / SP_hoàn_thành (tỷ lệ tiến độ)
    - Điểm = (a + b + c) / 3 × 70
    """
    # Lấy số ngày nghỉ đã duyệt
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
    
    # Lấy tổng SP đã duyệt
    stmt_sp = (
        select(
            func.coalesce(func.sum(KeKhaiCongViec.so_luong_quy_doi), Decimal("0")).label("tong_sp"),
            func.coalesce(func.sum(
                case(
                    (KeKhaiCongViec.ket_qua_chat_luong == True, KeKhaiCongViec.so_luong_quy_doi),
                    else_=Decimal("0")
                )
            ), Decimal("0")).label("sp_chat_luong"),
            func.coalesce(func.sum(
                case(
                    (KeKhaiCongViec.dung_han == True, KeKhaiCongViec.so_luong_quy_doi),
                    else_=Decimal("0")
                )
            ), Decimal("0")).label("sp_tien_do"),
        )
        .where(KeKhaiCongViec.cong_chuc_id == cong_chuc_id)
        .where(KeKhaiCongViec.thang == thang)
        .where(KeKhaiCongViec.nam == nam)
        .where(KeKhaiCongViec.trang_thai_phe_duyet == TrangThaiPheDuyet.DA_PHE_DUYET)
        .where(KeKhaiCongViec.is_deleted == False)
    )
    result_sp = await db.execute(stmt_sp)
    row_sp = result_sp.one()
    
    tong_sp = float(row_sp.tong_sp or 0)
    sp_chat_luong = float(row_sp.sp_chat_luong or 0)
    sp_tien_do = float(row_sp.sp_tien_do or 0)
    
    # Tính tỷ lệ
    a_so_luong = tong_sp / sp_duoc_giao if sp_duoc_giao > 0 else 0
    b_chat_luong = sp_chat_luong / tong_sp if tong_sp > 0 else 0
    c_tien_do = sp_tien_do / tong_sp if tong_sp > 0 else 0
    
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
) -> dict:
    """
    Lấy danh sách tổng hợp xếp loại KPI của CC trong đơn vị/chi cục.
    
    Quyền:
    - ĐT: Xem CC trong đơn vị mình
    - PCCT/CCT: Xem tất cả CC trong chi cục
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
        
        # Tính điểm 70
        diem_70_data = await tinh_diem_kpi_70(db, cc.id, thang, nam)
        
        # Điểm 30 (tiêu chí chung)
        diem_30 = 0
        trang_thai_tc = None
        if danh_gia and danh_gia.diem_tieu_chi_chung:
            diem_30 = float(danh_gia.diem_tieu_chi_chung)
        if danh_gia and danh_gia.trang_thai_tc:
            trang_thai_tc = danh_gia.trang_thai_tc.value
        
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
            
            # Chi tiết 70đ
            "sp_duoc_giao": diem_70_data["sp_duoc_giao"],
            "tong_sp_hoan_thanh": diem_70_data["tong_sp_hoan_thanh"],
            
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
            diem = float(tc_dg.diem_phe_duyet) if tc_dg.diem_phe_duyet else float(tc_dg.diem_tu_cham)
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
        stmt_dg = stmt_dg.where(DanhGiaThang.don_vi_id_snapshot == filter_don_vi_id)
    
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
        stmt_kk = stmt_kk.where(KeKhaiCongViec.don_vi_id_snapshot == filter_don_vi_id)
    
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