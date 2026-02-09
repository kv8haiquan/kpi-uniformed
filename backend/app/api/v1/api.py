"""
app/api/v1/api.py
=================
API Router chính cho version 1.

Tổng hợp tất cả endpoint routers và cấu hình prefix/tags.

Cập nhật v2.6.0 (29/01/2026):
- Thêm xep_loai_moi router cho màn hình xếp loại mới

Cập nhật v2.8.0 (02/02/2026):
- Thêm export_bao_cao router cho xuất DOCX/PDF
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth, don_vi, cong_chuc, danh_muc, ke_khai, phe_duyet, danh_gia, nghi_phep,
    ke_khai_lanh_dao, danh_gia_lanh_dao, bao_cao_xep_loai,
    xep_loai_moi,  # v2.6.0: Màn hình xếp loại mới
    admin, #Module admin mới
    sp_cong_viec_chuan, #SP CV CHUAN MOI
    export_bao_cao,  # v2.8.0: Xuất báo cáo DOCX/PDF
)

# =============================================================================
# MAIN ROUTER V1
# =============================================================================

api_router = APIRouter()


# -----------------------------------------------------------------------------
# AUTHENTICATION
# -----------------------------------------------------------------------------
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)


# -----------------------------------------------------------------------------
# MASTER DATA - DỮ LIỆU NỀN TẢNG
# -----------------------------------------------------------------------------

# Đơn vị
api_router.include_router(
    don_vi.router,
    prefix="/don-vi",
    tags=["Đơn vị"],
)

# Công chức
api_router.include_router(
    cong_chuc.router,
    prefix="/cong-chuc",
    tags=["Công chức"],
)

# Danh mục SP/Công việc, SP chuẩn, Cấp độ
api_router.include_router(
    danh_muc.router,
    prefix="/danh-muc",
    tags=["Danh mục SP/CV"],
)


# -----------------------------------------------------------------------------
# KÊ KHAI CÔNG VIỆC
# -----------------------------------------------------------------------------

# Kê khai công việc
api_router.include_router(
    ke_khai.router,
    prefix="/ke-khai",
    tags=["Kê khai công việc"],
)


# -----------------------------------------------------------------------------
# PHÊ DUYỆT & ĐÁNH GIÁ
# -----------------------------------------------------------------------------

# Phê duyệt kê khai
api_router.include_router(
    phe_duyet.router,
    prefix="/phe-duyet",
    tags=["Phê duyệt"],
)

# Đánh giá tháng
api_router.include_router(
    danh_gia.router,
    prefix="/danh-gia",
    tags=["Đánh giá tháng"],
)


# -----------------------------------------------------------------------------
# NGHỈ PHÉP (v2.3 - 25/01/2026)
# -----------------------------------------------------------------------------

# Quản lý nghỉ phép
api_router.include_router(
    nghi_phep.router,
    prefix="/nghi-phep",
    tags=["Nghỉ phép"],
)


# -----------------------------------------------------------------------------
# KÊ KHAI & ĐÁNH GIÁ LÃNH ĐẠO (v2.5.8 - 27/01/2026)
# -----------------------------------------------------------------------------

# Kê khai công việc Lãnh đạo
api_router.include_router(
    ke_khai_lanh_dao.router,
    prefix="/ke-khai-lanh-dao",
    tags=["Kê khai Lãnh đạo"],
)

# Đánh giá d, đ, e (năng lực lãnh đạo)
api_router.include_router(
    danh_gia_lanh_dao.router,
    prefix="/danh-gia-lanh-dao",
    tags=["Đánh giá Lãnh đạo"],
)

api_router.include_router(
    bao_cao_xep_loai.router,
    prefix="/bao-cao-xep-loai",
    tags=["Báo cáo Xếp loại"]
)


# -----------------------------------------------------------------------------
# XẾP LOẠI MỚI (v2.6.0 - 29/01/2026)
# -----------------------------------------------------------------------------

# Màn hình xếp loại tổng hợp cho ĐT/CCT
api_router.include_router(
    xep_loai_moi.router,
    prefix="/xep-loai",
    tags=["Xếp loại KPI"],
)

#ADMIN MODULE
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin Module"],
)

api_router.include_router(
    sp_cong_viec_chuan.router, 
    prefix="/sp-cong-viec-chuan", 
    tags=["sp-cong-viec-chuan"]
)


# -----------------------------------------------------------------------------
# XUẤT BÁO CÁO DOCX/PDF (v2.8.0 - 02/02/2026)
# -----------------------------------------------------------------------------

api_router.include_router(
    export_bao_cao.router,
    prefix="/export",
    tags=["Xuất Báo cáo"],
)