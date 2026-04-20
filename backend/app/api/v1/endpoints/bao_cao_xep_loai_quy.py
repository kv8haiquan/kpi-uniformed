"""
app/api/v1/endpoints/bao_cao_xep_loai_quy.py
=============================================
API Endpoints cho Báo cáo Xếp loại Chất lượng Công chức theo Quý.

Endpoints:
1. GET  /don-vi/quy/{quy}/nam/{nam}  - Lấy/Tạo báo cáo quý đơn vị (Đội trưởng)
2. PUT  /chi-tiet/{chi_tiet_id}/de-xuat - Điều chỉnh xếp loại đề xuất (Đội trưởng)
3. POST /{bao_cao_id}/gui-duyet - Gửi báo cáo lên CCT (Đội trưởng)
4. GET  /cho-phe-duyet - DS báo cáo chờ phê duyệt (CCT)
5. POST /{bao_cao_id}/phe-duyet - Phê duyệt/Từ chối (CCT)

Tham chiếu:
- Mẫu: bao_cao_xep_loai.py (báo cáo tháng)
- Model: app.models.bao_cao_xep_loai_quy
- Schema: app.schemas.bao_cao_xep_loai_quy
- Helper: app.api.v1.endpoints.xep_loai_quy_helpers

Phiên bản: 1.0 (16/04/2026)
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import DatabaseDep, ActiveUserDep, is_qldv
from app.models.user_org import CongChuc, DonVi, VaiTro, CapBacVaiTro
from app.models.bao_cao_xep_loai import BaoCaoXepLoai, TrangThaiBaoCao, tinh_xep_loai
from app.models.bao_cao_xep_loai_quy import BaoCaoXepLoaiQuy, ChiTietXepLoaiQuy
from app.schemas.common import success_response, error_response, Pagination
from app.schemas.bao_cao_xep_loai_quy import (
    BaoCaoXepLoaiQuyResponse,
    ChiTietXepLoaiQuyResponse,
    DeXuatXepLoaiQuyRequest,
    PheDuyetQuyRequest,
    BaoCaoXepLoaiQuyBriefResponse,
    get_trang_thai_ten_quy,
)
from app.api.v1.endpoints.xep_loai_quy_helpers import tinh_diem_quy, QUY_TO_THANG


router = APIRouter()


# =============================================================================
# HELPER FUNCTIONS - KIỂM TRA QUYỀN
# =============================================================================

def check_is_truong_don_vi(user: CongChuc) -> bool:
    """Kiểm tra user có phải là Trưởng đơn vị không."""
    if not user.vai_tro:
        return False
    return user.vai_tro.cap_bac == CapBacVaiTro.TRUONG_DON_VI


def check_is_chi_cuc_truong(user: CongChuc) -> bool:
    """Kiểm tra user có phải là Chi cục trưởng không."""
    if not user.vai_tro:
        return False
    return user.vai_tro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG


def check_is_lanh_dao_chi_cuc(user: CongChuc) -> bool:
    """Kiểm tra user có phải là Lãnh đạo Chi cục (CCT hoặc PCCT) không."""
    if not user.vai_tro:
        return False
    return user.vai_tro.cap_bac in [
        CapBacVaiTro.CHI_CUC_TRUONG,
        CapBacVaiTro.PHO_CHI_CUC_TRUONG
    ]


def check_is_lanh_dao_don_vi(user: CongChuc) -> bool:
    """
    Kiểm tra user có phải là Lãnh đạo đơn vị (TDV hoặc PDV hoặc QLDV) không.
    """
    if not user.vai_tro:
        return False
    return user.vai_tro.cap_bac in [
        CapBacVaiTro.TRUONG_DON_VI,
        CapBacVaiTro.PHO_DON_VI,
        CapBacVaiTro.QUAN_LY_DON_VI,
    ]


def check_can_view_all_units(user: CongChuc) -> bool:
    """
    Quyền xem toàn bộ đơn vị: CCT/PCCT hoặc user có flag can_view_all_units (TCCB).
    """
    if getattr(user, "can_view_all_units", False):
        return True
    return check_is_lanh_dao_chi_cuc(user)


# =============================================================================
# ENDPOINT 1: TDV LẤY/TẠO BÁO CÁO QUÝ ĐƠN VỊ
# =============================================================================

@router.get("/don-vi/quy/{quy}/nam/{nam}")
async def get_or_create_bao_cao_quy_don_vi(
    quy: int,
    nam: int,
    db: DatabaseDep,
    current_user: ActiveUserDep,
):
    """
    Lấy hoặc tạo mới báo cáo xếp loại quý cho đơn vị (TDV/PDV/QLDV hoặc CCT/PCCT).

    Logic:
    1. Kiểm tra điều kiện: 3 tháng trong quý phải có BaoCaoXepLoai với trang_thai
       IN ('DA_PHE_DUYET', 'CHO_PHE_DUYET')
    2. Tìm BaoCaoXepLoaiQuy theo don_vi_id + quy + nam
       - Nếu đã có → trả về kèm chi_tiets
       - Nếu chưa có → tạo mới và tính điểm cho tất cả CC
    3. Return BaoCaoXepLoaiQuyResponse

    Quyền: TDV/PDV/QLDV hoặc CCT/PCCT
    """
    # =========================================================================
    # 1. Kiểm tra quyền
    # =========================================================================
    if not check_is_lanh_dao_don_vi(current_user) and not check_is_lanh_dao_chi_cuc(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                code="PERM_001",
                message="Chỉ Lãnh đạo đơn vị hoặc Lãnh đạo Chi cục mới được xem báo cáo quý"
            )
        )

    # =========================================================================
    # 2. Validate quy (1-4)
    # =========================================================================
    if quy not in [1, 2, 3, 4]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="VAL_001",
                message="Quý phải từ 1 đến 4"
            )
        )

    don_vi_id = current_user.don_vi_id
    thang_list = QUY_TO_THANG.get(quy, [])

    # =========================================================================
    # 3. Kiểm tra điều kiện: 3 tháng trong quý phải có báo cáo tháng hợp lệ
    # =========================================================================
    stmt_check = (
        select(BaoCaoXepLoai.thang)
        .where(BaoCaoXepLoai.don_vi_id == don_vi_id)
        .where(BaoCaoXepLoai.thang.in_(thang_list))
        .where(BaoCaoXepLoai.nam == nam)
        .where(BaoCaoXepLoai.trang_thai.in_([
            TrangThaiBaoCao.DA_PHE_DUYET.value,
            TrangThaiBaoCao.CHO_PHE_DUYET.value
        ]))
        .where(BaoCaoXepLoai.is_deleted == False)
    )
    result_check = await db.execute(stmt_check)
    thang_co_bao_cao = [row[0] for row in result_check.all()]

    # Ghi nhận cảnh báo nếu thiếu tháng (không block, vẫn cho tạo)
    canh_bao_thieu_thang = None
    if len(thang_co_bao_cao) < 3:
        thang_thieu = [t for t in thang_list if t not in thang_co_bao_cao]
        canh_bao_thieu_thang = f"Chưa đủ báo cáo tháng (thiếu tháng: {', '.join(map(str, thang_thieu))}). Điểm quý có thể chưa chính xác."

    # =========================================================================
    # 4. Tìm hoặc tạo mới BaoCaoXepLoaiQuy
    # =========================================================================
    stmt = (
        select(BaoCaoXepLoaiQuy)
        .options(
            selectinload(BaoCaoXepLoaiQuy.don_vi),
            selectinload(BaoCaoXepLoaiQuy.nguoi_lap),
            selectinload(BaoCaoXepLoaiQuy.nguoi_phe_duyet),
            selectinload(BaoCaoXepLoaiQuy.chi_tiets).selectinload(ChiTietXepLoaiQuy.cong_chuc),
        )
        .where(BaoCaoXepLoaiQuy.don_vi_id == don_vi_id)
        .where(BaoCaoXepLoaiQuy.quy == quy)
        .where(BaoCaoXepLoaiQuy.nam == nam)
        .where(BaoCaoXepLoaiQuy.is_deleted == False)
    )
    result = await db.execute(stmt)
    bao_cao = result.scalar_one_or_none()

    if bao_cao:
        # Đã có báo cáo → trả về
        response_data = BaoCaoXepLoaiQuyResponse.model_validate(bao_cao)
        response_data.trang_thai_ten = get_trang_thai_ten_quy(bao_cao.trang_thai)
        data = response_data.model_dump()
        if canh_bao_thieu_thang:
            data["canh_bao"] = canh_bao_thieu_thang
        return success_response(
            data=data,
            message="Lấy báo cáo quý thành công"
        )

    # =========================================================================
    # 5. Tạo mới báo cáo quý
    # =========================================================================

    # 5.1. Query tất cả CC active trong đơn vị (loại trừ ADMIN, QLDV)
    excluded_roles = [CapBacVaiTro.SUPER_ADMIN, CapBacVaiTro.QUAN_LY_DON_VI]
    stmt_cc = (
        select(CongChuc)
        .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id, isouter=True)
        .options(selectinload(CongChuc.vai_tro))
        .where(CongChuc.don_vi_id == don_vi_id)
        .where(CongChuc.is_deleted == False)
        .where(CongChuc.is_active == True)
        .where(
            (CongChuc.vai_tro_id == None) |
            (~VaiTro.cap_bac.in_(excluded_roles))
        )
    )
    result_cc = await db.execute(stmt_cc)
    cong_chucs = list(result_cc.scalars().all())

    # 5.2. Tạo BaoCaoXepLoaiQuy
    bao_cao = BaoCaoXepLoaiQuy(
        don_vi_id=don_vi_id,
        quy=quy,
        nam=nam,
        nguoi_lap_id=current_user.id,
        trang_thai="NHAP",
        tong_cong_chuc=len(cong_chucs),
    )
    db.add(bao_cao)
    await db.flush()  # Lấy ID để tạo chi tiết

    # 5.3. Tạo ChiTietXepLoaiQuy cho từng CC
    chi_tiets = []
    for cc in cong_chucs:
        # Gọi helper tinh_diem_quy
        diem_data = await tinh_diem_quy(db, cc.id, quy, nam)

        # Xử lý trường hợp chuyển đơn vị hoặc thiếu dữ liệu
        if diem_data.get("co_chuyen_don_vi"):
            # Bỏ qua CC chuyển đơn vị giữa quý
            continue

        diem_kpi_quy = Decimal(str(diem_data.get("diem_kpi_quy") or 0))
        diem_tc_quy = Decimal(str(diem_data.get("diem_tc_quy") or 0))
        diem_tong_quy = Decimal(str(diem_data.get("diem_tong_quy") or 0))
        xep_loai_quy = diem_data.get("xep_loai_quy") or "D"

        chi_tiet = ChiTietXepLoaiQuy(
            bao_cao_quy_id=bao_cao.id,
            cong_chuc_id=cc.id,
            is_lanh_dao=cc.is_lanh_dao or False,
            diem_tieu_chi_chung=diem_tc_quy,
            diem_kpi=diem_kpi_quy,
            diem_tong=diem_tong_quy,
            xep_loai_he_thong=xep_loai_quy,
        )
        db.add(chi_tiet)
        chi_tiets.append(chi_tiet)

    await db.flush()

    # 5.4. Tính thống kê (trực tiếp từ list, không dùng relationship để tránh lazy load)
    stat_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    for ct in chi_tiets:
        xl = ct.xep_loai_he_thong
        if xl in stat_counts:
            stat_counts[xl] += 1
    bao_cao.tong_cong_chuc = len(chi_tiets)
    bao_cao.so_loai_a = stat_counts["A"]
    bao_cao.so_loai_b = stat_counts["B"]
    bao_cao.so_loai_c = stat_counts["C"]
    bao_cao.so_loai_d = stat_counts["D"]
    bao_cao.so_loai_e = stat_counts["E"]
    # Cảnh báo tỷ lệ A > 20% B
    so_b = stat_counts["B"]
    bao_cao.canh_bao_ty_le_a = (stat_counts["A"] > (0.2 * so_b)) if so_b > 0 else (stat_counts["A"] > 0)

    await db.commit()

    # 5.5. Reload báo cáo với relationships
    await db.refresh(bao_cao)
    stmt_reload = (
        select(BaoCaoXepLoaiQuy)
        .options(
            selectinload(BaoCaoXepLoaiQuy.don_vi),
            selectinload(BaoCaoXepLoaiQuy.nguoi_lap),
            selectinload(BaoCaoXepLoaiQuy.chi_tiets).selectinload(ChiTietXepLoaiQuy.cong_chuc),
        )
        .where(BaoCaoXepLoaiQuy.id == bao_cao.id)
    )
    result_reload = await db.execute(stmt_reload)
    bao_cao = result_reload.scalar_one()

    response_data = BaoCaoXepLoaiQuyResponse.model_validate(bao_cao)
    response_data.trang_thai_ten = get_trang_thai_ten_quy(bao_cao.trang_thai)
    data = response_data.model_dump()
    if canh_bao_thieu_thang:
        data["canh_bao"] = canh_bao_thieu_thang

    return success_response(
        data=data,
        message="Tạo báo cáo quý thành công"
    )


# =============================================================================
# ENDPOINT 2: TDV ĐIỀU CHỈNH XẾP LOẠI ĐỀ XUẤT
# =============================================================================

@router.put("/chi-tiet/{chi_tiet_id}/de-xuat")
async def dieu_chinh_de_xuat_quy(
    chi_tiet_id: UUID,
    request: DeXuatXepLoaiQuyRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
):
    """
    Điều chỉnh xếp loại đề xuất quý (Đội trưởng).

    Logic:
    1. Tìm ChiTietXepLoaiQuy theo id
    2. Check báo cáo ở trạng thái NHAP hoặc TU_CHOI
    3. Nếu xep_loai_de_xuat != xep_loai_he_thong → bắt buộc ly_do_dieu_chinh
    4. Cập nhật xep_loai_de_xuat, ly_do_dieu_chinh_dt
    5. Cập nhật thống kê báo cáo cha

    Quyền: TDV/PDV chỉ đơn vị mình
    """
    # =========================================================================
    # 1. Tìm chi tiết
    # =========================================================================
    stmt = (
        select(ChiTietXepLoaiQuy)
        .options(
            selectinload(ChiTietXepLoaiQuy.bao_cao).selectinload(BaoCaoXepLoaiQuy.don_vi),
            selectinload(ChiTietXepLoaiQuy.bao_cao).selectinload(BaoCaoXepLoaiQuy.chi_tiets),
            selectinload(ChiTietXepLoaiQuy.cong_chuc),
        )
        .where(ChiTietXepLoaiQuy.id == chi_tiet_id)
    )
    result = await db.execute(stmt)
    chi_tiet = result.scalar_one_or_none()

    if not chi_tiet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                code="NOT_FOUND",
                message="Không tìm thấy chi tiết xếp loại quý"
            )
        )

    # =========================================================================
    # 2. Kiểm tra quyền (chỉ TDV của đơn vị này)
    # =========================================================================
    if not check_is_truong_don_vi(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                code="PERM_001",
                message="Chỉ Trưởng đơn vị mới được điều chỉnh xếp loại"
            )
        )

    bao_cao = chi_tiet.bao_cao
    if bao_cao.don_vi_id != current_user.don_vi_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                code="PERM_002",
                message="Bạn chỉ được điều chỉnh báo cáo của đơn vị mình"
            )
        )

    # =========================================================================
    # 3. Kiểm tra trạng thái báo cáo (chỉ sửa được khi NHAP hoặc TU_CHOI)
    # =========================================================================
    if bao_cao.trang_thai not in ["NHAP", "TU_CHOI"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="VAL_003",
                message="Chỉ có thể điều chỉnh khi báo cáo đang soạn hoặc bị từ chối"
            )
        )

    # =========================================================================
    # 4. Validate: nếu khác hệ thống → bắt buộc lý do
    # =========================================================================
    if request.xep_loai_de_xuat.value != chi_tiet.xep_loai_he_thong:
        if not request.ly_do_dieu_chinh or len(request.ly_do_dieu_chinh.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    code="VAL_004",
                    message="Lý do điều chỉnh là bắt buộc khi xếp loại đề xuất khác hệ thống"
                )
            )

    # =========================================================================
    # 5. Cập nhật chi tiết
    # =========================================================================
    chi_tiet.xep_loai_de_xuat = request.xep_loai_de_xuat.value
    chi_tiet.ly_do_dieu_chinh_dt = request.ly_do_dieu_chinh
    chi_tiet.ghi_chu = request.ghi_chu

    # Reset trạng thái từ chối (nếu có)
    chi_tiet.bi_tu_choi = False
    chi_tiet.ly_do_tu_choi = None

    # =========================================================================
    # 6. Cập nhật thống kê báo cáo cha
    # =========================================================================
    stats = bao_cao.tinh_thong_ke()
    bao_cao.so_loai_a = stats["so_loai_a"]
    bao_cao.so_loai_b = stats["so_loai_b"]
    bao_cao.so_loai_c = stats["so_loai_c"]
    bao_cao.so_loai_d = stats["so_loai_d"]
    bao_cao.so_loai_e = stats["so_loai_e"]
    bao_cao.canh_bao_ty_le_a = bao_cao.kiem_tra_ty_le_a()

    await db.commit()
    await db.refresh(chi_tiet)

    return success_response(
        data=ChiTietXepLoaiQuyResponse.model_validate(chi_tiet).model_dump(),
        message="Cập nhật xếp loại đề xuất thành công"
    )


# =============================================================================
# ENDPOINT 3: TDV GỬI DUYỆT BÁO CÁO QUÝ
# =============================================================================

@router.post("/{bao_cao_id}/gui-duyet")
async def gui_duyet_bao_cao_quy(
    bao_cao_id: UUID,
    db: DatabaseDep,
    current_user: ActiveUserDep,
):
    """
    Gửi báo cáo quý lên CCT để phê duyệt (Đội trưởng).

    Logic:
    1. Tìm BaoCaoXepLoaiQuy theo id
    2. Check trang_thai == NHAP hoặc TU_CHOI
    3. Auto-fill: chi tiết nào chưa có xep_loai_de_xuat → copy từ xep_loai_he_thong
    4. Cập nhật: trang_thai = CHO_PHE_DUYET, ngay_gui_duyet = now()
    5. Cập nhật thống kê

    Quyền: TDV chỉ đơn vị mình
    """
    # =========================================================================
    # 1. Tìm báo cáo
    # =========================================================================
    stmt = (
        select(BaoCaoXepLoaiQuy)
        .options(
            selectinload(BaoCaoXepLoaiQuy.chi_tiets),
        )
        .where(BaoCaoXepLoaiQuy.id == bao_cao_id)
        .where(BaoCaoXepLoaiQuy.is_deleted == False)
    )
    result = await db.execute(stmt)
    bao_cao = result.scalar_one_or_none()

    if not bao_cao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                code="NOT_FOUND",
                message="Không tìm thấy báo cáo quý"
            )
        )

    # =========================================================================
    # 2. Kiểm tra quyền
    # =========================================================================
    if not check_is_truong_don_vi(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                code="PERM_001",
                message="Chỉ Trưởng đơn vị mới được gửi duyệt báo cáo"
            )
        )

    if bao_cao.don_vi_id != current_user.don_vi_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                code="PERM_002",
                message="Bạn chỉ được gửi duyệt báo cáo của đơn vị mình"
            )
        )

    # =========================================================================
    # 3. Kiểm tra trạng thái
    # =========================================================================
    if bao_cao.trang_thai not in ["NHAP", "TU_CHOI"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="VAL_005",
                message="Báo cáo không ở trạng thái có thể gửi duyệt"
            )
        )

    # =========================================================================
    # 4. Auto-fill xep_loai_de_xuat nếu chưa có
    # =========================================================================
    for chi_tiet in bao_cao.chi_tiets:
        if not chi_tiet.xep_loai_de_xuat:
            chi_tiet.xep_loai_de_xuat = chi_tiet.xep_loai_he_thong

    # =========================================================================
    # 5. Cập nhật trạng thái
    # =========================================================================
    bao_cao.trang_thai = "CHO_PHE_DUYET"
    bao_cao.ngay_gui_duyet = datetime.now(timezone.utc)
    bao_cao.ngay_lap = datetime.now(timezone.utc)

    # Cập nhật thống kê
    stats = bao_cao.tinh_thong_ke()
    bao_cao.so_loai_a = stats["so_loai_a"]
    bao_cao.so_loai_b = stats["so_loai_b"]
    bao_cao.so_loai_c = stats["so_loai_c"]
    bao_cao.so_loai_d = stats["so_loai_d"]
    bao_cao.so_loai_e = stats["so_loai_e"]
    bao_cao.canh_bao_ty_le_a = bao_cao.kiem_tra_ty_le_a()

    await db.commit()
    await db.refresh(bao_cao)

    return success_response(
        data={
            "id": str(bao_cao.id),
            "trang_thai": bao_cao.trang_thai,
            "ngay_gui_duyet": bao_cao.ngay_gui_duyet.isoformat() if bao_cao.ngay_gui_duyet else None,
            "canh_bao_ty_le_a": bao_cao.canh_bao_ty_le_a,
            "thong_ke": stats,
        },
        message="Gửi duyệt báo cáo quý thành công"
    )


# =============================================================================
# ENDPOINT 4: CCT XEM DANH SÁCH CHỜ PHÊ DUYỆT
# =============================================================================

@router.get("/cho-phe-duyet")
async def get_danh_sach_cho_phe_duyet_quy(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    quy: Optional[int] = Query(None, ge=1, le=4),
    nam: Optional[int] = Query(None, ge=2025),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Lấy danh sách báo cáo quý chờ phê duyệt (CCT/PCCT/SUPER_ADMIN).

    Query params:
    - quy (optional): Lọc theo quý
    - nam (optional): Lọc theo năm
    - page, page_size: Phân trang

    Quyền: CCT/PCCT/SUPER_ADMIN
    """
    # =========================================================================
    # 1. Kiểm tra quyền
    # =========================================================================
    if not check_is_lanh_dao_chi_cuc(current_user):
        # Check SUPER_ADMIN
        if not getattr(current_user, 'is_system_admin', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_response(
                    code="PERM_001",
                    message="Chỉ Lãnh đạo Chi cục mới được xem danh sách chờ phê duyệt"
                )
            )

    # =========================================================================
    # 2. Build query
    # =========================================================================
    stmt_count = (
        select(func.count())
        .select_from(BaoCaoXepLoaiQuy)
        .where(BaoCaoXepLoaiQuy.trang_thai == "CHO_PHE_DUYET")
        .where(BaoCaoXepLoaiQuy.is_deleted == False)
    )

    stmt_data = (
        select(BaoCaoXepLoaiQuy)
        .options(
            selectinload(BaoCaoXepLoaiQuy.don_vi),
            selectinload(BaoCaoXepLoaiQuy.nguoi_lap),
        )
        .where(BaoCaoXepLoaiQuy.trang_thai == "CHO_PHE_DUYET")
        .where(BaoCaoXepLoaiQuy.is_deleted == False)
    )

    # Filter theo quy
    if quy:
        stmt_count = stmt_count.where(BaoCaoXepLoaiQuy.quy == quy)
        stmt_data = stmt_data.where(BaoCaoXepLoaiQuy.quy == quy)

    # Filter theo nam
    if nam:
        stmt_count = stmt_count.where(BaoCaoXepLoaiQuy.nam == nam)
        stmt_data = stmt_data.where(BaoCaoXepLoaiQuy.nam == nam)

    # Count total
    total_result = await db.execute(stmt_count)
    total_items = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    stmt_data = stmt_data.order_by(
        BaoCaoXepLoaiQuy.nam.desc(),
        BaoCaoXepLoaiQuy.quy.desc(),
        BaoCaoXepLoaiQuy.created_at.desc()
    ).offset(offset).limit(page_size)

    result_data = await db.execute(stmt_data)
    bao_caos = result_data.scalars().all()

    # =========================================================================
    # 3. Build response
    # =========================================================================
    data = [BaoCaoXepLoaiQuyBriefResponse.model_validate(bc).model_dump() for bc in bao_caos]

    pagination = Pagination.create(
        page=page,
        page_size=page_size,
        total_items=total_items
    )

    return success_response(
        data={
            "items": data,
            "pagination": pagination.model_dump(),
        },
        message="Lấy danh sách chờ phê duyệt thành công"
    )


# =============================================================================
# ENDPOINT 4B: DANH SÁCH BÁO CÁO QUÝ (MỌI TRẠNG THÁI)
# =============================================================================

@router.get("/danh-sach")
async def get_danh_sach_bao_cao_quy(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    quy: Optional[int] = Query(None, ge=1, le=4),
    nam: Optional[int] = Query(None, ge=2025),
    trang_thai: Optional[str] = Query(
        None,
        description="Lọc theo trạng thái: NHAP | CHO_PHE_DUYET | DA_PHE_DUYET | TU_CHOI",
    ),
    don_vi_id: Optional[UUID] = Query(None, description="Lọc theo đơn vị"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """
    Lấy danh sách báo cáo xếp loại quý của tất cả đơn vị (mọi trạng thái).

    Dành cho CCT/PCCT/TCCB (can_view_all_units) theo dõi toàn Chi cục.

    Quyền:
    - CCT/PCCT/TCCB (can_view_all_units): xem toàn bộ đơn vị.
    - TDV/PDV/QLDV: chỉ xem đơn vị mình (bỏ qua param don_vi_id).
    """
    is_chi_cuc = check_can_view_all_units(current_user)
    is_don_vi = check_is_lanh_dao_don_vi(current_user)
    if not is_chi_cuc and not is_don_vi:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                code="PERM_001",
                message="Bạn không có quyền xem danh sách báo cáo quý",
            ),
        )

    if trang_thai and trang_thai not in ["NHAP", "CHO_PHE_DUYET", "DA_PHE_DUYET", "TU_CHOI"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="VAL_001",
                message="trang_thai không hợp lệ",
            ),
        )

    stmt_count = (
        select(func.count())
        .select_from(BaoCaoXepLoaiQuy)
        .where(BaoCaoXepLoaiQuy.is_deleted == False)
    )
    stmt_data = (
        select(BaoCaoXepLoaiQuy)
        .options(
            selectinload(BaoCaoXepLoaiQuy.don_vi),
            selectinload(BaoCaoXepLoaiQuy.nguoi_lap),
        )
        .where(BaoCaoXepLoaiQuy.is_deleted == False)
    )

    # Scope theo quyền
    if not is_chi_cuc:
        # TDV/PDV/QLDV: chỉ đơn vị mình
        stmt_count = stmt_count.where(BaoCaoXepLoaiQuy.don_vi_id == current_user.don_vi_id)
        stmt_data = stmt_data.where(BaoCaoXepLoaiQuy.don_vi_id == current_user.don_vi_id)
    elif don_vi_id:
        stmt_count = stmt_count.where(BaoCaoXepLoaiQuy.don_vi_id == don_vi_id)
        stmt_data = stmt_data.where(BaoCaoXepLoaiQuy.don_vi_id == don_vi_id)

    if quy:
        stmt_count = stmt_count.where(BaoCaoXepLoaiQuy.quy == quy)
        stmt_data = stmt_data.where(BaoCaoXepLoaiQuy.quy == quy)
    if nam:
        stmt_count = stmt_count.where(BaoCaoXepLoaiQuy.nam == nam)
        stmt_data = stmt_data.where(BaoCaoXepLoaiQuy.nam == nam)
    if trang_thai:
        stmt_count = stmt_count.where(BaoCaoXepLoaiQuy.trang_thai == trang_thai)
        stmt_data = stmt_data.where(BaoCaoXepLoaiQuy.trang_thai == trang_thai)

    total_result = await db.execute(stmt_count)
    total_items = total_result.scalar() or 0

    offset = (page - 1) * page_size
    stmt_data = (
        stmt_data.order_by(
            BaoCaoXepLoaiQuy.nam.desc(),
            BaoCaoXepLoaiQuy.quy.desc(),
            BaoCaoXepLoaiQuy.created_at.desc(),
        )
        .offset(offset)
        .limit(page_size)
    )
    result_data = await db.execute(stmt_data)
    bao_caos = result_data.scalars().all()

    data = [
        BaoCaoXepLoaiQuyBriefResponse.model_validate(bc).model_dump()
        for bc in bao_caos
    ]
    pagination = Pagination.create(
        page=page, page_size=page_size, total_items=total_items
    )

    return success_response(
        data={"items": data, "pagination": pagination.model_dump()},
        message="Lấy danh sách báo cáo quý thành công",
    )


# =============================================================================
# ENDPOINT 4C: CHI TIẾT 1 BÁO CÁO QUÝ THEO ID
# =============================================================================

@router.get("/{bao_cao_id}")
async def get_chi_tiet_bao_cao_quy(
    bao_cao_id: UUID,
    db: DatabaseDep,
    current_user: ActiveUserDep,
):
    """
    Lấy chi tiết đầy đủ 1 báo cáo quý theo id (kèm chi_tiets).

    Dùng cho CCT/PCCT/TCCB xem chi tiết báo cáo đơn vị sau khi chọn từ danh sách.

    Quyền:
    - CCT/PCCT/TCCB: xem mọi đơn vị.
    - TDV/PDV/QLDV: chỉ xem báo cáo của đơn vị mình.
    """
    stmt = (
        select(BaoCaoXepLoaiQuy)
        .options(
            selectinload(BaoCaoXepLoaiQuy.don_vi),
            selectinload(BaoCaoXepLoaiQuy.nguoi_lap),
            selectinload(BaoCaoXepLoaiQuy.nguoi_phe_duyet),
            selectinload(BaoCaoXepLoaiQuy.chi_tiets).selectinload(
                ChiTietXepLoaiQuy.cong_chuc
            ),
        )
        .where(BaoCaoXepLoaiQuy.id == bao_cao_id)
        .where(BaoCaoXepLoaiQuy.is_deleted == False)
    )
    result = await db.execute(stmt)
    bao_cao = result.scalar_one_or_none()

    if not bao_cao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                code="NOT_FOUND", message="Không tìm thấy báo cáo quý"
            ),
        )

    # Kiểm tra quyền truy cập
    is_chi_cuc = check_can_view_all_units(current_user)
    if not is_chi_cuc:
        if not check_is_lanh_dao_don_vi(current_user) or bao_cao.don_vi_id != current_user.don_vi_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_response(
                    code="PERM_002",
                    message="Bạn chỉ được xem báo cáo của đơn vị mình",
                ),
            )

    response_data = BaoCaoXepLoaiQuyResponse.model_validate(bao_cao)
    response_data.trang_thai_ten = get_trang_thai_ten_quy(bao_cao.trang_thai)
    return success_response(
        data=response_data.model_dump(),
        message="Lấy chi tiết báo cáo quý thành công",
    )


# =============================================================================
# ENDPOINT 5: CCT PHÊ DUYỆT/TỪ CHỐI BÁO CÁO QUÝ
# =============================================================================

@router.post("/{bao_cao_id}/phe-duyet")
async def phe_duyet_bao_cao_quy(
    bao_cao_id: UUID,
    request: PheDuyetQuyRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
):
    """
    Phê duyệt hoặc từ chối báo cáo quý (CCT/PCCT/SUPER_ADMIN).

    Logic:
    - APPROVE: Phê duyệt toàn bộ báo cáo
      + Auto-fill: chi tiết nào chưa có xep_loai_quyet_dinh → copy từ xep_loai_de_xuat
      + trang_thai = DA_PHE_DUYET
      + ngay_phe_duyet = now()
    - REJECT: Từ chối
      + trang_thai = TU_CHOI
      + y_kien_phe_duyet = y_kien
      + Mark chi_tiet_tu_choi: bi_tu_choi = True
      + Reset xep_loai_de_xuat, xep_loai_quyet_dinh về None (cho TDV sửa lại)

    Quyền: CCT/PCCT/SUPER_ADMIN
    """
    # =========================================================================
    # 1. Kiểm tra quyền
    # =========================================================================
    if not check_is_lanh_dao_chi_cuc(current_user):
        if not getattr(current_user, 'is_system_admin', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_response(
                    code="PERM_001",
                    message="Chỉ Lãnh đạo Chi cục mới được phê duyệt báo cáo quý"
                )
            )

    # =========================================================================
    # 2. Tìm báo cáo
    # =========================================================================
    stmt = (
        select(BaoCaoXepLoaiQuy)
        .options(
            selectinload(BaoCaoXepLoaiQuy.chi_tiets),
        )
        .where(BaoCaoXepLoaiQuy.id == bao_cao_id)
        .where(BaoCaoXepLoaiQuy.is_deleted == False)
    )
    result = await db.execute(stmt)
    bao_cao = result.scalar_one_or_none()

    if not bao_cao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                code="NOT_FOUND",
                message="Không tìm thấy báo cáo quý"
            )
        )

    # =========================================================================
    # 3. Kiểm tra trạng thái
    # =========================================================================
    if bao_cao.trang_thai != "CHO_PHE_DUYET":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="VAL_006",
                message="Chỉ có thể phê duyệt báo cáo đang chờ duyệt"
            )
        )

    # =========================================================================
    # 4. Xử lý APPROVE
    # =========================================================================
    if request.action == "APPROVE":
        # Auto-fill xep_loai_quyet_dinh nếu chưa có
        for chi_tiet in bao_cao.chi_tiets:
            if not chi_tiet.xep_loai_quyet_dinh:
                chi_tiet.xep_loai_quyet_dinh = chi_tiet.xep_loai_de_xuat or chi_tiet.xep_loai_he_thong

        bao_cao.trang_thai = "DA_PHE_DUYET"
        bao_cao.ngay_phe_duyet = datetime.now(timezone.utc)
        bao_cao.nguoi_phe_duyet_id = current_user.id
        bao_cao.y_kien_phe_duyet = request.y_kien

        # Cập nhật thống kê
        stats = bao_cao.tinh_thong_ke()
        bao_cao.so_loai_a = stats["so_loai_a"]
        bao_cao.so_loai_b = stats["so_loai_b"]
        bao_cao.so_loai_c = stats["so_loai_c"]
        bao_cao.so_loai_d = stats["so_loai_d"]
        bao_cao.so_loai_e = stats["so_loai_e"]
        bao_cao.canh_bao_ty_le_a = bao_cao.kiem_tra_ty_le_a()

        await db.commit()
        await db.refresh(bao_cao)

        return success_response(
            data={
                "id": str(bao_cao.id),
                "trang_thai": bao_cao.trang_thai,
                "ngay_phe_duyet": bao_cao.ngay_phe_duyet.isoformat() if bao_cao.ngay_phe_duyet else None,
                "so_cc_bi_tu_choi": 0,
            },
            message="Phê duyệt báo cáo quý thành công"
        )

    # =========================================================================
    # 5. Xử lý REJECT
    # =========================================================================
    elif request.action == "REJECT":
        bao_cao.trang_thai = "TU_CHOI"
        bao_cao.y_kien_phe_duyet = request.y_kien

        # Mark chi tiết bị từ chối
        so_cc_bi_tu_choi = 0
        if request.chi_tiet_tu_choi:
            chi_tiet_ids = {ct.chi_tiet_id for ct in request.chi_tiet_tu_choi}
            chi_tiet_ly_do = {ct.chi_tiet_id: ct.ly_do for ct in request.chi_tiet_tu_choi}

            for chi_tiet in bao_cao.chi_tiets:
                if chi_tiet.id in chi_tiet_ids:
                    chi_tiet.bi_tu_choi = True
                    chi_tiet.ly_do_tu_choi = chi_tiet_ly_do.get(chi_tiet.id)
                    # Reset xếp loại để TDV sửa lại
                    chi_tiet.xep_loai_de_xuat = None
                    chi_tiet.xep_loai_quyet_dinh = None
                    chi_tiet.ly_do_dieu_chinh_dt = None
                    chi_tiet.ly_do_dieu_chinh_cct = None
                    so_cc_bi_tu_choi += 1

        await db.commit()
        await db.refresh(bao_cao)

        return success_response(
            data={
                "id": str(bao_cao.id),
                "trang_thai": bao_cao.trang_thai,
                "ngay_phe_duyet": None,
                "so_cc_bi_tu_choi": so_cc_bi_tu_choi,
            },
            message="Từ chối báo cáo quý thành công"
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="VAL_007",
                message="Action không hợp lệ (phải là APPROVE hoặc REJECT)"
            )
        )
