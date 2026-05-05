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
    xep_loai_quy,  # v3.6.0: Xếp loại quý
    admin, #Module admin mới
    sp_cong_viec_chuan, #SP CV CHUAN MOI
    export_bao_cao,  # v2.8.0: Xuất báo cáo DOCX/PDF
    in_bang_ke,  # v3.7.0: In bảng kê cá nhân (phiếu đánh giá + bảng kê CV)
    bao_cao_xep_loai_quy,  # v3.9.0: Báo cáo xếp loại quý
    phieu_danh_gia_quy,  # v4.1.0 (17/04/2026): Phiếu đánh giá cá nhân quý + workflow 1 cấp
    ke_khai_v2,  # PL3 V2 (28/04/2026): Kê khai công việc theo PL3
    admin_pl3,   # PL3 V2 (28/04/2026): Admin CRUD danh mục PL3 + pin version
    admin_import,  # PL3 V2 (28/04/2026): Admin import Excel PL3
    phan_cong_phu_trach,  # KPI LĐ mới (05/05/2026): Phân công CCT/PCCT phụ trách
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

# Kê khai công việc V2_PL3 (28/04/2026)
api_router.include_router(
    ke_khai_v2.router,
    prefix="/ke-khai-v2",
    tags=["Kê khai V2 (PL3)"],
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

# Báo cáo xếp loại quý (v3.9.0)
api_router.include_router(
    bao_cao_xep_loai_quy.router,
    prefix="/bao-cao-xep-loai-quy",
    tags=["Báo cáo Xếp loại quý"]
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

# Xếp loại quý (v3.6.0)
api_router.include_router(
    xep_loai_quy.router,
    prefix="/xep-loai-quy",
    tags=["Xếp loại quý"],
)

#ADMIN MODULE
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin Module"],
)

# Admin PL3 V2 (28/04/2026)
api_router.include_router(
    admin_pl3.router,
    prefix="/admin",
    tags=["Admin PL3 V2"],
)

# Admin Excel import PL3 (28/04/2026)
api_router.include_router(
    admin_import.router,
    prefix="/admin",
    tags=["Admin Import PL3"],
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

# In bảng kê cá nhân (v3.7.0 - 15/04/2026)
api_router.include_router(
    in_bang_ke.router,
    prefix="/in-bang-ke",
    tags=["In Bảng kê"],
)

# Phiếu đánh giá cá nhân quý + workflow 1 cấp (v4.1.0 - 17/04/2026)
api_router.include_router(
    phieu_danh_gia_quy.router,
    prefix="/phieu-danh-gia-quy",
    tags=["Phiếu đánh giá cá nhân quý"],
)

# Phân công CCT/PCCT phụ trách đơn vị (KPI LĐ mới - 05/05/2026)
api_router.include_router(
    phan_cong_phu_trach.router,
    prefix="/phan-cong-phu-trach",
    tags=["Phân công phụ trách"],
)