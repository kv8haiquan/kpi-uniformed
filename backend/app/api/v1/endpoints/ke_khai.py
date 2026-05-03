"""
app/api/v1/endpoints/ke_khai.py
===============================
API Endpoints cho Kê khai công việc.

Cập nhật v3 (2026-01-25):
- Thêm endpoint GET /nguoi-phe-duyet để lấy danh sách người phê duyệt phù hợp

Endpoints:
- GET /ke-khai/nguoi-phe-duyet: Lấy danh sách người phê duyệt phù hợp
- GET /ke-khai: Danh sách kê khai của user
- GET /ke-khai/{id}: Chi tiết kê khai
- POST /ke-khai: Tạo kê khai mới
- PUT /ke-khai/{id}: Cập nhật kê khai
- DELETE /ke-khai/{id}: Xóa kê khai
- POST /ke-khai/{id}/gui-duyet: Gửi phê duyệt
- GET /ke-khai/thong-ke/thang: Thống kê kê khai theo tháng

Quy tắc:
- User chỉ được xem/sửa/xóa kê khai của chính mình
- Chỉ sửa được khi trạng thái NHAP hoặc TU_CHOI
- Chỉ xóa được khi trạng thái NHAP hoặc TU_CHOI
"""

from datetime import date
from decimal import Decimal
from typing import Optional, Tuple, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import DatabaseDep, ActiveUserDep, is_qldv
from app.models.kpi_submission import KeKhaiCongViec, TrangThaiKeKhai
from app.models.task_catalog import DanhMucSpCongViec, CapDoPhucTap, SpCongViecChuan
from app.models.user_org import CongChuc, VaiTro, CapBacVaiTro
from app.schemas.common import (
    DataResponse,
    PaginatedResponse,
    Pagination,
    success_response,
    error_response,
)
from app.schemas.kpi_submission import (
    KeKhaiCreate,
    KeKhaiUpdate,
    KeKhaiResponse,
    ThongKeKeKhaiResponse,
    GuiDuyetRequest,
    KeKhaiNhieuNgayCreate,
    KeKhaiNhieuNgayResponse,
    GuiDuyetBulkRequest,
)


router = APIRouter()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def calculate_kpi_score(
    db: AsyncSession,
    danh_muc_sp_id: UUID,
    cap_do_id: UUID,
    so_luong: int,
    he_so_thuc_te: Optional[Decimal] = None,
) -> Tuple[Decimal, str]:
    """
    Tính điểm KPI quy đổi về SP gốc (SP1).
    
    Công thức:
    - Lấy SpChuan từ DanhMucSpCongViec
    - Lấy CapDo
    - Nếu SP chuẩn là SP1: he_so_cap_do = CapDo.he_so_sp1
    - Nếu SP chuẩn là SP2/3/4: he_so_cap_do = CapDo.he_so_sp2
    - Nếu CapDo là C5 (theo thực tế): dùng he_so_thuc_te
    - Kết quả = so_luong × SpChuan.he_so_quy_doi_sp1 × he_so_cap_do
    
    LƯU Ý: Logic tính điểm GIỮ NGUYÊN - việc trừ điểm theo lỗi sẽ xử lý sau
    
    Returns:
        Tuple[Decimal, str]: (so_sp_goc_quy_doi, ma_sp)
    
    Raises:
        HTTPException: Nếu không tìm thấy danh mục hoặc cấp độ
    """
    # Lấy DanhMucSpCongViec + SpChuan
    dm_stmt = (
        select(DanhMucSpCongViec)
        .options(selectinload(DanhMucSpCongViec.sp_chuan))
        .where(DanhMucSpCongViec.id == danh_muc_sp_id)
        .where(DanhMucSpCongViec.is_deleted == False)
    )
    dm_result = await db.execute(dm_stmt)
    danh_muc = dm_result.scalar_one_or_none()
    
    if not danh_muc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_DANH_MUC",
                    "message": "Không tìm thấy danh mục sản phẩm/công việc"
                }
            }
        )
    
    if not danh_muc.sp_chuan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_SP_CHUAN",
                    "message": "Danh mục chưa được gán loại SP chuẩn"
                }
            }
        )
    
    # Lấy CapDoPhucTap
    cd_stmt = (
        select(CapDoPhucTap)
        .where(CapDoPhucTap.id == cap_do_id)
    )
    cd_result = await db.execute(cd_stmt)
    cap_do = cd_result.scalar_one_or_none()
    
    if not cap_do:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_CAP_DO",
                    "message": "Không tìm thấy cấp độ phức tạp"
                }
            }
        )
    
    # Xác định hệ số cấp độ
    sp_chuan = danh_muc.sp_chuan
    ma_sp = sp_chuan.ma_sp  # SP1, SP2, SP3, SP4
    
    if cap_do.is_theo_thuc_te:
        # C5: Dùng hệ số thực tế do lãnh đạo nhập
        if he_so_thuc_te is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "MISSING_HE_SO_THUC_TE",
                        "message": "Cấp độ C5 yêu cầu nhập hệ số thực tế"
                    }
                }
            )
        he_so_cap_do = he_so_thuc_te
    else:
        # C1-C4: Dùng hệ số từ bảng
        if ma_sp == "SP1":
            # SP1: Dùng he_so_sp1
            he_so_cap_do = cap_do.he_so_sp1
        else:
            # SP2, SP3, SP4: Dùng he_so_sp2
            he_so_cap_do = cap_do.he_so_sp2
    
    # Tính kết quả
    # so_sp_goc_quy_doi = so_luong × he_so_quy_doi_sp1 × he_so_cap_do
    so_sp_goc_quy_doi = Decimal(so_luong) * sp_chuan.he_so_quy_doi_sp1 * Decimal(str(he_so_cap_do))
    
    return so_sp_goc_quy_doi, ma_sp


async def _assert_v1_writable(db: AsyncSession, user: CongChuc) -> None:
    """
    PL3 V2 (02/05/2026) — Chặn TẠO MỚI bản V1 cho công chức V2_PL3.

    Dùng cho endpoint CREATE (POST `/`, POST `/nhieu-ngay`) — vì khi tạo mới
    bản kê khai sẽ mặc định version_kekhai='V1' (server_default), nên chặn theo
    user effective version. Lãnh đạo + HĐ 111 dùng endpoint riêng, không qua đây.

    Với endpoint sửa/xoá/gửi duyệt một bản đã tồn tại, dùng `_assert_kekhai_not_v1`
    để check theo bản kê khai (vì frontend V2 vẫn gọi `/ke-khai/{id}/gui-duyet`
    cho bản V2).
    """
    if user.is_lanh_dao or user.is_hd_111:
        return
    pinned = getattr(user, "kpi_version_pinned", None)
    if pinned == "V1":
        return
    if pinned == "V2_PL3":
        effective = "V2_PL3"
    else:
        from sqlalchemy import text
        row = (await db.execute(
            text("SELECT value FROM public.platform_config WHERE key='kpi_version_default'")
        )).scalar_one_or_none()
        effective = (row if isinstance(row, str) else str(row).strip('"')) if row else "V1"
    if effective == "V2_PL3":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "V1_CLOSED",
                    "message": (
                        "Kê khai V1 đã đóng. Vui lòng kê khai mới tại /ke-khai-v2 "
                        "(phiên bản V2_PL3)."
                    ),
                },
            },
        )


def _assert_kekhai_not_v1(ke_khai: KeKhaiCongViec) -> None:
    """
    PL3 V2 (02/05/2026) — Chặn thao tác trên bản kê khai V1 đã tồn tại.

    Dùng cho endpoint sửa/xoá/gửi duyệt: chặn theo `ke_khai.version_kekhai`
    (không phải theo user). Bản V2 (gồm cả khi V2 frontend gọi nhầm endpoint
    V1 do backend V2 chưa có route tương ứng) vẫn pass.
    """
    if getattr(ke_khai, "version_kekhai", "V1") == "V1":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "V1_CLOSED",
                    "message": (
                        "Bản kê khai này thuộc phiên bản V1 đã đóng. Vui lòng "
                        "kê khai lại trên /ke-khai-v2."
                    ),
                },
            },
        )


def ke_khai_to_response(kk: KeKhaiCongViec) -> dict:
    """
    Convert KeKhaiCongViec model to response dict.
    Flatten và xử lý nested relationships.
    
    Bao gồm:
    - Thông tin cơ bản
    - Tự đánh giá của CC (tu_danh_gia_*)
    - Phản hồi của Lãnh đạo (so_loi_*, y_kien_lanh_dao)
    """
    response = {
        "id": kk.id,
        "cong_chuc_id": kk.cong_chuc_id,
        "cong_chuc": None,
        "thang": kk.thang,
        "nam": kk.nam,
        "ngay_thuc_hien": kk.ngay_thuc_hien,
        "danh_muc_sp": None,
        "cap_do": None,
        "so_luong": kk.so_luong,
        "he_so_thuc_te": float(kk.he_so_thuc_te) if kk.he_so_thuc_te else None,
        "nguoi_phe_duyet_id": kk.nguoi_phe_duyet_id,
        "nguoi_phe_duyet": None,
        "mo_ta_cong_viec": kk.mo_ta_cong_viec,
        "is_doi_moi_sang_tao": kk.is_doi_moi_sang_tao,
        "ngay_deadline": kk.ngay_deadline,
        "ngay_hoan_thanh": kk.ngay_hoan_thanh,
        "trang_thai": kk.trang_thai.value if kk.trang_thai else "NHAP",
        
        # =====================================================================
        # TỰ ĐÁNH GIÁ CỦA CÔNG CHỨC
        # =====================================================================
        "tu_danh_gia_chat_luong": kk.tu_danh_gia_chat_luong or 0,
        "tu_danh_gia_tien_do": kk.tu_danh_gia_tien_do or 0,
        "ghi_chu_tu_danh_gia": kk.ghi_chu_tu_danh_gia,
        # v2.7.4: Mô tả lỗi tự đánh giá
        "ghi_chu_tu_dg_chat_luong": kk.ghi_chu_tu_dg_chat_luong,
        "ghi_chu_tu_dg_tien_do": kk.ghi_chu_tu_dg_tien_do,
        
        # =====================================================================
        # PHẢN HỒI CỦA LÃNH ĐẠO (Lãnh đạo xác nhận khi phê duyệt)
        # =====================================================================
        "so_loi_chat_luong": kk.so_loi_chat_luong or 0,
        "so_loi_tien_do": kk.so_loi_tien_do or 0,
        "y_kien_lanh_dao": kk.y_kien_lanh_dao,
        # v2.7.4: Mô tả lỗi lãnh đạo chốt
        "ghi_chu_loi_chat_luong": kk.ghi_chu_loi_chat_luong,
        "ghi_chu_loi_tien_do": kk.ghi_chu_loi_tien_do,
        
        # =====================================================================
        # KẾT QUẢ QUY ĐỔI
        # =====================================================================
        "so_sp_goc_quy_doi": float(kk.so_sp_goc_quy_doi) if kk.so_sp_goc_quy_doi else None,
        "so_sp_chat_luong": float(kk.so_sp_chat_luong) if kk.so_sp_chat_luong else None,
        "so_sp_tien_do": float(kk.so_sp_tien_do) if kk.so_sp_tien_do else None,
        
        "created_at": kk.created_at,
        "updated_at": kk.updated_at,
    }
    
    # Nested: Người kê khai
    if kk.cong_chuc:
        response["cong_chuc"] = {
            "id": kk.cong_chuc.id,
            "ma_cc": kk.cong_chuc.ma_cc,
            "ho_ten": kk.cong_chuc.ho_ten,
        }
    
    # Nested: Danh mục SP
    if kk.danh_muc_sp:
        dm = kk.danh_muc_sp
        response["danh_muc_sp"] = {
            "id": dm.id,
            "ma_danh_muc": dm.ma_danh_muc,
            "ten_cong_viec": dm.ten_cong_viec,
            "ma_sp": dm.sp_chuan.ma_sp if dm.sp_chuan else None,
            "he_so_quy_doi": float(dm.sp_chuan.he_so_quy_doi_sp1) if dm.sp_chuan else None,
        }
    
    # Nested: Cấp độ
    if kk.cap_do:
        cd = kk.cap_do
        response["cap_do"] = {
            "id": cd.id,
            "ma_cap_do": cd.ma_cap_do,
            "ten_cap_do": cd.ten_cap_do,
            "he_so_sp1": float(cd.he_so_sp1),
            "he_so_sp2": float(cd.he_so_sp2),
            "is_theo_thuc_te": cd.is_theo_thuc_te,
        }
    
    # Nested: Người phê duyệt
    if kk.nguoi_phe_duyet:
        npd = kk.nguoi_phe_duyet
        response["nguoi_phe_duyet"] = {
            "id": npd.id,
            "ma_cc": npd.ma_cc,
            "ho_ten": npd.ho_ten,
            "chuc_vu": npd.chuc_vu,
        }
    
    return response


# =============================================================================
# GET NGUOI PHE DUYET (PHẢI ĐẶT TRƯỚC /{ke_khai_id})
# =============================================================================

@router.get(
    "/nguoi-phe-duyet",
    summary="Lấy danh sách người phê duyệt phù hợp",
    description="""
    Trả về danh sách người phê duyệt phù hợp với cấp bậc của user hiện tại.
    
    **Logic nghiệp vụ theo Quy chế KPI:**
    - **Công chức (CC)** → Trả về danh sách **Phó Đơn vị (PDV)** cùng đơn vị
    - **Phó Đơn vị (PDV)** → Trả về **Trưởng Đơn vị (TDV)** cùng đơn vị
    - **Trưởng Đơn vị (TDV)** → Trả về **Chi cục trưởng (CCT)**
    - **Phó Chi cục trưởng (PCCT)** → Trả về **Chi cục trưởng (CCT)**
    - **Admin** → Trả về tất cả Lãnh đạo (để test)
    
    **Response:**
    ```json
    {
      "success": true,
      "data": [
        { "id": "uuid", "ma_cc": "CC001", "ho_ten": "Nguyễn Văn A", "chuc_vu": "Phó Đội trưởng" }
      ]
    }
    ```
    
    **Quyền truy cập:** Tất cả user đã đăng nhập.
    """,
    response_model=DataResponse[List[dict]],
)
async def get_nguoi_phe_duyet(
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Lấy danh sách người phê duyệt phù hợp với cấp bậc của user.
    """
    # Lấy cấp bậc của user hiện tại
    user_cap_bac = None
    is_admin = False
    
    if current_user.vai_tro:
        user_cap_bac = current_user.vai_tro.cap_bac
        is_admin = current_user.vai_tro.is_system_admin or False
    
    # =========================================================================
    # CASE 1: Admin → Trả về tất cả Lãnh đạo
    # =========================================================================
    if is_admin:
        stmt = (
            select(CongChuc)
            .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id)
            .where(CongChuc.is_deleted == False)
            .where(CongChuc.is_active == True)
            .where(VaiTro.is_lanh_dao == True)
            .order_by(VaiTro.cap_bac, CongChuc.ho_ten)
        )
        result = await db.execute(stmt)
        approvers = result.scalars().all()
        
        data = [
            {
                "id": cc.id,
                "ma_cc": cc.ma_cc,
                "ho_ten": cc.ho_ten,
                "chuc_vu": cc.chuc_vu,
                "don_vi_ten": cc.don_vi.ten_don_vi if cc.don_vi else None,
                "cap_bac": cc.vai_tro.cap_bac.value if cc.vai_tro else None,
            }
            for cc in approvers
        ]
        return success_response(data=data, message="Danh sách tất cả lãnh đạo (Admin)")
    
    # =========================================================================
    # CASE 2: Chi cục trưởng → Không cần người phê duyệt (tự phê duyệt)
    # =========================================================================
    if user_cap_bac == CapBacVaiTro.CHI_CUC_TRUONG:
        return success_response(
            data=[],
            message="Chi cục trưởng tự phê duyệt cho bản thân"
        )
    
    # =========================================================================
    # CASE 3: Phó CCT hoặc Trưởng ĐV → Trả về Chi cục trưởng (CCT)
    # =========================================================================
    if user_cap_bac in [CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.TRUONG_DON_VI]:
        stmt = (
            select(CongChuc)
            .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id)
            .where(CongChuc.is_deleted == False)
            .where(CongChuc.is_active == True)
            .where(VaiTro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG)
        )
        result = await db.execute(stmt)
        approvers = result.scalars().all()
        
        data = [
            {
                "id": cc.id,
                "ma_cc": cc.ma_cc,
                "ho_ten": cc.ho_ten,
                "chuc_vu": cc.chuc_vu,
            }
            for cc in approvers
        ]
        return success_response(data=data, message="Chi cục trưởng")
    
    # =========================================================================
    # CASE 4: Phó Đơn vị (PDV) → Trả về Trưởng Đơn vị (TDV) cùng đơn vị
    # =========================================================================
    if user_cap_bac == CapBacVaiTro.PHO_DON_VI:
        stmt = (
            select(CongChuc)
            .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id)
            .where(CongChuc.is_deleted == False)
            .where(CongChuc.is_active == True)
            .where(CongChuc.don_vi_id == current_user.don_vi_id)  # Cùng đơn vị
            .where(VaiTro.cap_bac == CapBacVaiTro.TRUONG_DON_VI)
        )
        result = await db.execute(stmt)
        approvers = result.scalars().all()
        
        data = [
            {
                "id": cc.id,
                "ma_cc": cc.ma_cc,
                "ho_ten": cc.ho_ten,
                "chuc_vu": cc.chuc_vu,
            }
            for cc in approvers
        ]
        return success_response(data=data, message="Trưởng đơn vị cùng phòng/đội")
    
    # =========================================================================
    # CASE 5: Công chức (CC) → Trả về Phó Đơn vị (PDV) cùng đơn vị
    # QUAN TRỌNG: KHÔNG trả về Trưởng ĐV (theo quy chế)
    # =========================================================================
    if user_cap_bac == CapBacVaiTro.CONG_CHUC:
        stmt = (
            select(CongChuc)
            .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id)
            .where(CongChuc.is_deleted == False)
            .where(CongChuc.is_active == True)
            .where(CongChuc.don_vi_id == current_user.don_vi_id)  # Cùng đơn vị
            .where(
                or_(
                    VaiTro.cap_bac == CapBacVaiTro.PHO_DON_VI,    # Phó ĐV
                    VaiTro.cap_bac == CapBacVaiTro.TRUONG_DON_VI,  # Trưởng ĐV
                )
            )
            .order_by(VaiTro.cap_bac)  # Trưởng ĐV hiện trước (cap_bac nhỏ hơn)
        )
        result = await db.execute(stmt)
        approvers = result.scalars().all()
        
        data = [
            {
                "id": cc.id,
                "ma_cc": cc.ma_cc,
                "ho_ten": cc.ho_ten,
                "chuc_vu": cc.chuc_vu,
            }
            for cc in approvers
        ]
        return success_response(data=data, message="Lãnh đạo đơn vị (Trưởng/Phó)")

    # =========================================================================
    # CASE 6: TCCB hoặc các role khác → Trả về tất cả PDV + TDV
    # =========================================================================
    stmt = (
        select(CongChuc)
        .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id)
        .where(CongChuc.is_deleted == False)
        .where(CongChuc.is_active == True)
        .where(CongChuc.don_vi_id == current_user.don_vi_id)  # Cùng đơn vị
        .where(
            or_(
                VaiTro.cap_bac == CapBacVaiTro.PHO_DON_VI,
                VaiTro.cap_bac == CapBacVaiTro.TRUONG_DON_VI,
            )
        )
        .order_by(VaiTro.cap_bac)
    )
    result = await db.execute(stmt)
    approvers = result.scalars().all()
    
    data = [
        {
            "id": cc.id,
            "ma_cc": cc.ma_cc,
            "ho_ten": cc.ho_ten,
            "chuc_vu": cc.chuc_vu,
        }
        for cc in approvers
    ]
    return success_response(data=data, message="Lãnh đạo cùng đơn vị")


# =============================================================================
# GET THONG KE KE KHAI (PHẢI ĐẶT TRƯỚC /{ke_khai_id})
# =============================================================================

@router.get(
    "/thong-ke/thang",
    summary="Thống kê kê khai theo tháng",
    description="""
    Lấy thống kê kê khai của user trong một tháng cụ thể.
    
    **v2.6.3 UPDATE:** Thêm các fields tạm tính để hỗ trợ 2-tab UI
    
    **Thông tin trả về:**
    - Tổng số bản kê khai
    - Phân loại theo trạng thái (tong_nhap, tong_cho_duyet, tong_da_duyet, tong_tu_choi)
    - Tổng SP quy đổi (chính thức - chỉ DA_PHE_DUYET)
    - **MỚI:** Tổng SP tạm tính (NHAP + CHO_PHE_DUYET + DA_PHE_DUYET)
    - Thống kê lỗi (tự đánh giá và lãnh đạo chốt)
    
    **Response keys:**
    - `tong_sp_quy_doi`: SP chính thức (chỉ DA_PHE_DUYET)
    - `tong_sp_chat_luong`: SP đạt CL chính thức
    - `tong_sp_tien_do`: SP đạt TĐ chính thức
    - `tam_tinh_sp_quy_doi`: SP tạm tính (tất cả trạng thái trừ TU_CHOI)
    - `tam_tinh_sp_chat_luong`: SP đạt CL tạm tính
    - `tam_tinh_sp_tien_do`: SP đạt TĐ tạm tính
    
    **Quyền truy cập:** Tất cả user đã đăng nhập.
    """,
    response_model=DataResponse[ThongKeKeKhaiResponse],
)
async def get_thong_ke_ke_khai(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int = Query(..., ge=1, le=12, description="Tháng thống kê"),
    nam: int = Query(..., ge=2025, description="Năm thống kê"),
) -> dict:
    """
    Thống kê kê khai theo tháng của user hiện tại.
    
    v2.6.3: Thêm fields tạm tính cho 2-tab UI
    """
    from decimal import Decimal
    
    # =========================================================================
    # QUERY 1: Thống kê theo trạng thái (giữ nguyên logic cũ)
    # =========================================================================
    stats_query = (
        select(
            KeKhaiCongViec.trang_thai,
            func.count(KeKhaiCongViec.id).label("count"),
            func.sum(KeKhaiCongViec.so_sp_goc_quy_doi).label("tong_sp"),
            func.sum(KeKhaiCongViec.so_sp_chat_luong).label("tong_sp_cl"),
            func.sum(KeKhaiCongViec.so_sp_tien_do).label("tong_sp_td"),
            # Thống kê lỗi tự đánh giá
            func.sum(KeKhaiCongViec.tu_danh_gia_chat_luong).label("tong_tu_dg_cl"),
            func.sum(KeKhaiCongViec.tu_danh_gia_tien_do).label("tong_tu_dg_td"),
            # Thống kê lỗi chốt cuối
            func.sum(KeKhaiCongViec.so_loi_chat_luong).label("tong_loi_cl"),
            func.sum(KeKhaiCongViec.so_loi_tien_do).label("tong_loi_td"),
        )
        .where(KeKhaiCongViec.cong_chuc_id == current_user.id)
        .where(KeKhaiCongViec.thang == thang)
        .where(KeKhaiCongViec.nam == nam)
        .where(KeKhaiCongViec.is_deleted == False)
        # PL3 V2 (02/05/2026): /ke-khai/thong-ke/thang chỉ tính bản V1
        # (V2 dùng /ke-khai-v2/thong-ke/thang riêng).
        .where(KeKhaiCongViec.version_kekhai == "V1")
        .group_by(KeKhaiCongViec.trang_thai)
    )

    result = await db.execute(stats_query)
    stats = result.all()
    
    # =========================================================================
    # QUERY 2: Lấy chi tiết từng kê khai để tính SP tạm tính
    # (cần chi tiết vì phải tính SP CL/TD từ tu_danh_gia cho kê khai chưa duyệt)
    # =========================================================================
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
        .where(KeKhaiCongViec.cong_chuc_id == current_user.id)
        .where(KeKhaiCongViec.thang == thang)
        .where(KeKhaiCongViec.nam == nam)
        .where(KeKhaiCongViec.is_deleted == False)
        .where(KeKhaiCongViec.version_kekhai == "V1")
        .where(KeKhaiCongViec.trang_thai.in_([
            TrangThaiKeKhai.NHAP,
            TrangThaiKeKhai.CHO_PHE_DUYET,
            TrangThaiKeKhai.DA_PHE_DUYET,
        ]))
    )

    detail_result = await db.execute(detail_query)
    detail_rows = detail_result.all()
    
    # =========================================================================
    # KHỞI TẠO RESPONSE
    # =========================================================================
    response_data = {
        "thang": thang,
        "nam": nam,
        "so_sp_duoc_giao": None,
        "tong_ke_khai": 0,
        # Phân loại theo trạng thái
        "tong_da_duyet": 0,
        "tong_cho_duyet": 0,
        "tong_tu_choi": 0,
        "tong_nhap": 0,
        # =====================================================================
        # CHÍNH THỨC (chỉ DA_PHE_DUYET)
        # =====================================================================
        "tong_sp_quy_doi": 0,
        "tong_sp_chat_luong": 0,
        "tong_sp_tien_do": 0,
        "ty_le_hoan_thanh": None,
        # =====================================================================
        # TẠM TÍNH (NHAP + CHO_PHE_DUYET + DA_PHE_DUYET) - v2.6.3 NEW
        # =====================================================================
        "tam_tinh_sp_quy_doi": 0,
        "tam_tinh_sp_chat_luong": 0,
        "tam_tinh_sp_tien_do": 0,
        # Thống kê lỗi
        "tong_loi_cl_tu_danh_gia": 0,
        "tong_loi_td_tu_danh_gia": 0,
        "tong_loi_cl_chot": 0,
        "tong_loi_td_chot": 0,
    }
    
    # =========================================================================
    # AGGREGATE DATA - Xử lý stats theo trạng thái
    # =========================================================================
    for row in stats:
        (
            trang_thai, count, tong_sp, tong_sp_cl, tong_sp_td,
            tong_tu_dg_cl, tong_tu_dg_td, tong_loi_cl, tong_loi_td
        ) = row
        
        response_data["tong_ke_khai"] += count
        response_data["tong_loi_cl_tu_danh_gia"] += int(tong_tu_dg_cl or 0)
        response_data["tong_loi_td_tu_danh_gia"] += int(tong_tu_dg_td or 0)
        response_data["tong_loi_cl_chot"] += int(tong_loi_cl or 0)
        response_data["tong_loi_td_chot"] += int(tong_loi_td or 0)
        
        # Phân loại theo trạng thái
        if trang_thai == TrangThaiKeKhai.DA_PHE_DUYET:
            response_data["tong_da_duyet"] = count
            # CHÍNH THỨC: Chỉ từ kê khai đã duyệt
            response_data["tong_sp_quy_doi"] = float(tong_sp) if tong_sp else 0
            response_data["tong_sp_chat_luong"] = float(tong_sp_cl) if tong_sp_cl else 0
            response_data["tong_sp_tien_do"] = float(tong_sp_td) if tong_sp_td else 0
        elif trang_thai == TrangThaiKeKhai.CHO_PHE_DUYET:
            response_data["tong_cho_duyet"] = count
        elif trang_thai == TrangThaiKeKhai.TU_CHOI:
            response_data["tong_tu_choi"] = count
        elif trang_thai == TrangThaiKeKhai.NHAP:
            response_data["tong_nhap"] = count
    
    # =========================================================================
    # TÍNH SP TẠM TÍNH (v2.6.3)
    # - Với kê khai DA_PHE_DUYET: dùng so_sp_chat_luong, so_sp_tien_do đã tính
    # - Với kê khai NHAP/CHO_PHE_DUYET: tính từ tu_danh_gia_*
    # =========================================================================
    tam_tinh_sp_quy_doi = Decimal("0")
    tam_tinh_sp_chat_luong = Decimal("0")
    tam_tinh_sp_tien_do = Decimal("0")
    
    for row in detail_rows:
        (
            trang_thai, so_luong, sp_goc, sp_cl, sp_td,
            tu_dg_cl, tu_dg_td
        ) = row
        
        sp_goc = Decimal(str(sp_goc or 0))
        so_luong = so_luong or 1
        
        # Cộng vào tổng SP quy đổi tạm tính
        tam_tinh_sp_quy_doi += sp_goc
        
        if trang_thai == TrangThaiKeKhai.DA_PHE_DUYET:
            # Đã duyệt: dùng giá trị đã tính sẵn
            tam_tinh_sp_chat_luong += Decimal(str(sp_cl or 0))
            tam_tinh_sp_tien_do += Decimal(str(sp_td or 0))
        else:
            # NHAP hoặc CHO_PHE_DUYET: tính từ tu_danh_gia
            # Công thức: SP_đạt = SP_gốc - (0.25 × min(lỗi, SL×4) × SP_per_unit)
            tu_dg_cl = tu_dg_cl or 0
            tu_dg_td = tu_dg_td or 0
            
            if sp_goc > 0 and so_luong > 0:
                sp_per_unit = sp_goc / Decimal(str(so_luong))
                max_loi = so_luong * 4
                
                # Tính SP chất lượng tạm
                loi_tinh_cl = min(tu_dg_cl, max_loi)
                sp_tru_cl = Decimal("0.25") * Decimal(str(loi_tinh_cl)) * sp_per_unit
                sp_cl_tam = max(sp_goc - sp_tru_cl, Decimal("0"))
                tam_tinh_sp_chat_luong += sp_cl_tam
                
                # Tính SP tiến độ tạm
                loi_tinh_td = min(tu_dg_td, max_loi)
                sp_tru_td = Decimal("0.25") * Decimal(str(loi_tinh_td)) * sp_per_unit
                sp_td_tam = max(sp_goc - sp_tru_td, Decimal("0"))
                tam_tinh_sp_tien_do += sp_td_tam
            else:
                # Không có SP hoặc số lượng = 0
                tam_tinh_sp_chat_luong += sp_goc
                tam_tinh_sp_tien_do += sp_goc
    
    # Cập nhật response với giá trị tạm tính
    response_data["tam_tinh_sp_quy_doi"] = float(tam_tinh_sp_quy_doi)
    response_data["tam_tinh_sp_chat_luong"] = float(tam_tinh_sp_chat_luong)
    response_data["tam_tinh_sp_tien_do"] = float(tam_tinh_sp_tien_do)
    
    # Tính tỷ lệ hoàn thành nếu có SP được giao
    if response_data["so_sp_duoc_giao"] and response_data["so_sp_duoc_giao"] > 0:
        response_data["ty_le_hoan_thanh"] = round(
            (response_data["tong_sp_quy_doi"] / response_data["so_sp_duoc_giao"]) * 100, 2
        )
    
    return success_response(data=response_data)

# =============================================================================
# GET LIST KE KHAI (Current User)
# =============================================================================

@router.get(
    "",
    summary="Lấy danh sách kê khai của bản thân",
    description="""
    Lấy danh sách bản kê khai công việc của user hiện tại.
    
    **Filter options:**
    - `thang`: Lọc theo tháng (1-12)
    - `nam`: Lọc theo năm (mặc định: năm hiện tại)
    - `trang_thai`: Lọc theo trạng thái
    - `co_loi`: Lọc các bản kê khai có lỗi (tự đánh giá hoặc lãnh đạo chốt)
    
    **Quyền truy cập:** Tất cả user đã đăng nhập.
    """,
    response_model=PaginatedResponse[KeKhaiResponse],
)
async def get_ke_khai_list(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    # Pagination
    page: int = Query(default=1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(default=20, ge=1, le=100, description="Số item mỗi trang"),
    # Filters
    thang: Optional[int] = Query(default=None, ge=1, le=12, description="Filter theo tháng"),
    nam: Optional[int] = Query(default=None, ge=2025, description="Filter theo năm"),
    trang_thai: Optional[str] = Query(
        default=None,
        pattern="^(NHAP|CHO_PHE_DUYET|DA_PHE_DUYET|TU_CHOI|HUY)$",
        description="Filter theo trạng thái"
    ),
    co_loi: Optional[bool] = Query(
        default=None,
        description="Filter các bản kê khai có lỗi"
    ),
) -> dict:
    """
    Lấy danh sách kê khai của user hiện tại với phân trang.
    """
    # Base query - chỉ lấy kê khai của user hiện tại
    # PL3 V2 (02/05/2026): trang /ke-khai chỉ hiển thị bản V1 (đối chiếu);
    # bản V2_PL3 đã có trang /ke-khai-v2 riêng.
    base_query = (
        select(KeKhaiCongViec)
        .options(
            selectinload(KeKhaiCongViec.cong_chuc),
            selectinload(KeKhaiCongViec.danh_muc_sp).selectinload(DanhMucSpCongViec.sp_chuan),
            selectinload(KeKhaiCongViec.cap_do),
            selectinload(KeKhaiCongViec.nguoi_phe_duyet),
        )
        .where(KeKhaiCongViec.cong_chuc_id == current_user.id)
        .where(KeKhaiCongViec.is_deleted == False)
        .where(KeKhaiCongViec.version_kekhai == "V1")
    )

    # Count query
    count_query = (
        select(func.count(KeKhaiCongViec.id))
        .where(KeKhaiCongViec.cong_chuc_id == current_user.id)
        .where(KeKhaiCongViec.is_deleted == False)
        .where(KeKhaiCongViec.version_kekhai == "V1")
    )
    
    # Apply filters
    if thang:
        base_query = base_query.where(KeKhaiCongViec.thang == thang)
        count_query = count_query.where(KeKhaiCongViec.thang == thang)
    
    if nam:
        base_query = base_query.where(KeKhaiCongViec.nam == nam)
        count_query = count_query.where(KeKhaiCongViec.nam == nam)
    
    if trang_thai:
        base_query = base_query.where(KeKhaiCongViec.trang_thai == TrangThaiKeKhai(trang_thai))
        count_query = count_query.where(KeKhaiCongViec.trang_thai == TrangThaiKeKhai(trang_thai))
    
    # Filter có lỗi (tự đánh giá hoặc lãnh đạo chốt)
    if co_loi is True:
        loi_filter = or_(
            KeKhaiCongViec.tu_danh_gia_chat_luong > 0,
            KeKhaiCongViec.tu_danh_gia_tien_do > 0,
            KeKhaiCongViec.so_loi_chat_luong > 0,
            KeKhaiCongViec.so_loi_tien_do > 0,
        )
        base_query = base_query.where(loi_filter)
        count_query = count_query.where(loi_filter)
    elif co_loi is False:
        khong_loi_filter = and_(
            KeKhaiCongViec.tu_danh_gia_chat_luong == 0,
            KeKhaiCongViec.tu_danh_gia_tien_do == 0,
            KeKhaiCongViec.so_loi_chat_luong == 0,
            KeKhaiCongViec.so_loi_tien_do == 0,
        )
        base_query = base_query.where(khong_loi_filter)
        count_query = count_query.where(khong_loi_filter)
    
    # Get total count
    count_result = await db.execute(count_query)
    total_items = count_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    base_query = (
        base_query
        .order_by(KeKhaiCongViec.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    
    # Execute query
    result = await db.execute(base_query)
    ke_khai_list = result.scalars().all()
    
    # Convert to response
    data = [ke_khai_to_response(kk) for kk in ke_khai_list]
    
    # Build pagination
    pagination = Pagination.create(
        page=page,
        page_size=page_size,
        total_items=total_items,
    )
    
    return {
        "success": True,
        "data": data,
        "pagination": pagination.model_dump(),
    }


# =============================================================================
# KÊ KHAI NHIỀU NGÀY (Multi-day Declaration)
# IMPORTANT: Đặt trước /{ke_khai_id} để tránh FastAPI path matching issue
# =============================================================================

@router.post(
    "/nhieu-ngay",
    summary="Tạo kê khai cho nhiều ngày cùng lúc",
    description="""
    Tạo nhiều bản kê khai cùng công việc, cùng cấp độ cho nhiều ngày.
    Mỗi ngày trong danh sách sẽ tạo 1 bản kê khai riêng.

    **Validation:**
    - Tất cả ngày phải cùng tháng/năm
    - Không cho trùng ngày
    - Không cho ngày tương lai
    - Tối đa 31 ngày

    **Quyền truy cập:** Tất cả user đã đăng nhập (trừ QLDV).
    """,
    response_model=DataResponse[KeKhaiNhieuNgayResponse],
    status_code=status.HTTP_201_CREATED,
)
async def ke_khai_nhieu_ngay(
    payload: KeKhaiNhieuNgayCreate,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """Tạo kê khai cho nhiều ngày cùng lúc."""
    # QLDV không có quyền tạo kê khai
    if is_qldv(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_QLDV",
                    "message": "QLDV không có quyền tạo kê khai"
                }
            }
        )
    await _assert_v1_writable(db, current_user)

    # Tính điểm KPI quy đổi (chung cho tất cả ngày)
    so_sp_goc_quy_doi, ma_sp = await calculate_kpi_score(
        db=db,
        danh_muc_sp_id=payload.danh_muc_sp_id,
        cap_do_id=payload.cap_do_id,
        so_luong=payload.so_luong,
        he_so_thuc_te=payload.he_so_thuc_te,
    )

    # Lấy tháng/năm từ ngày đầu tiên
    first_date = payload.ngay_thuc_hien_list[0]
    thang = first_date.month
    nam = first_date.year

    # Tạo N bản kê khai
    created_records = []
    for ngay in payload.ngay_thuc_hien_list:
        ke_khai = KeKhaiCongViec(
            cong_chuc_id=current_user.id,
            don_vi_id_snapshot=current_user.don_vi_id,
            thang=thang,
            nam=nam,
            ngay_thuc_hien=ngay,
            danh_muc_sp_id=payload.danh_muc_sp_id,
            cap_do_id=payload.cap_do_id,
            so_luong=payload.so_luong,
            he_so_thuc_te=payload.he_so_thuc_te,
            nguoi_phe_duyet_id=payload.nguoi_phe_duyet_id,
            mo_ta_cong_viec=payload.mo_ta_cong_viec,
            is_doi_moi_sang_tao=payload.is_doi_moi_sang_tao,
            trang_thai=TrangThaiKeKhai.NHAP,
            so_sp_goc_quy_doi=so_sp_goc_quy_doi,
            tu_danh_gia_chat_luong=payload.tu_danh_gia_chat_luong,
            tu_danh_gia_tien_do=payload.tu_danh_gia_tien_do,
            ghi_chu_tu_danh_gia=payload.ghi_chu_tu_danh_gia,
        )
        db.add(ke_khai)
        created_records.append(ke_khai)

    try:
        await db.flush()
        ke_khai_ids = [kk.id for kk in created_records]
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "CREATE_FAILED",
                    "message": f"Không thể tạo kê khai nhiều ngày: {str(e)}"
                }
            }
        )

    return success_response(
        data={
            "total_created": len(ke_khai_ids),
            "ke_khai_ids": ke_khai_ids,
            "thang": thang,
            "nam": nam,
        },
        message=f"Đã tạo {len(ke_khai_ids)} bản kê khai cho tháng {thang}/{nam}"
    )


@router.post(
    "/gui-duyet-bulk",
    summary="Gửi duyệt nhiều kê khai cùng lúc",
    description="""
    Chuyển trạng thái nhiều kê khai từ NHAP → CHO_PHE_DUYET.

    **Validation:**
    - Tất cả kê khai phải thuộc current_user
    - Tất cả phải ở trạng thái NHAP

    **Quyền truy cập:** Chủ sở hữu.
    """,
    response_model=DataResponse[dict],
)
async def gui_duyet_bulk(
    payload: GuiDuyetBulkRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """Gửi duyệt nhiều kê khai cùng lúc."""
    stmt = (
        select(KeKhaiCongViec)
        .where(KeKhaiCongViec.id.in_(payload.ke_khai_ids))
        .where(KeKhaiCongViec.is_deleted == False)
    )
    result = await db.execute(stmt)
    ke_khai_list = result.scalars().all()

    if not ke_khai_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Không tìm thấy bản kê khai nào"
                }
            }
        )

    # Kiểm tra người phê duyệt tồn tại
    npd_stmt = (
        select(CongChuc)
        .where(CongChuc.id == payload.nguoi_phe_duyet_id)
        .where(CongChuc.is_deleted == False)
        .where(CongChuc.is_active == True)
    )
    npd_result = await db.execute(npd_stmt)
    nguoi_phe_duyet = npd_result.scalar_one_or_none()

    if not nguoi_phe_duyet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_APPROVER",
                    "message": "Người phê duyệt không tồn tại hoặc không hoạt động"
                }
            }
        )

    processed_ids = []
    errors = []

    for kk in ke_khai_list:
        if getattr(kk, "version_kekhai", "V1") == "V1":
            errors.append(f"KK {kk.id}: V1 đã đóng — không thể gửi duyệt")
            continue
        if kk.cong_chuc_id != current_user.id:
            errors.append(f"KK {kk.id}: không phải kê khai của bạn")
            continue
        if kk.trang_thai != TrangThaiKeKhai.NHAP:
            errors.append(f"KK {kk.id}: không ở trạng thái NHAP (hiện: {kk.trang_thai.value})")
            continue

        kk.nguoi_phe_duyet_id = payload.nguoi_phe_duyet_id
        kk.trang_thai = TrangThaiKeKhai.CHO_PHE_DUYET
        processed_ids.append(kk.id)

    if not processed_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "PROCESS_FAILED",
                    "message": "Không gửi duyệt được bản nào",
                    "details": errors,
                }
            }
        )

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "DB_ERROR",
                    "message": f"Lỗi khi gửi duyệt: {str(e)}"
                }
            }
        )

    response_data = {
        "processed_count": len(processed_ids),
        "ke_khai_ids": processed_ids,
        "trang_thai_moi": "CHO_PHE_DUYET",
    }
    if errors:
        response_data["warnings"] = errors

    return success_response(
        data=response_data,
        message=f"Đã gửi duyệt {len(processed_ids)} bản kê khai"
    )


# =============================================================================
# GET KE KHAI BY ID
# =============================================================================

@router.get(
    "/{ke_khai_id}",
    summary="Lấy chi tiết kê khai",
    description="""
    Lấy thông tin chi tiết của một bản kê khai.
    
    **Response bao gồm:**
    - Thông tin kê khai cơ bản
    - Tự đánh giá của CC (tu_danh_gia_chat_luong, tu_danh_gia_tien_do, ghi_chu_tu_danh_gia)
    - Phản hồi của Lãnh đạo (so_loi_chat_luong, so_loi_tien_do, y_kien_lanh_dao)
    
    **Quyền truy cập:** Chủ sở hữu hoặc người phê duyệt.
    """,
    response_model=DataResponse[KeKhaiResponse],
    responses={
        404: {"description": "Không tìm thấy kê khai"},
        403: {"description": "Không có quyền xem"},
    }
)
async def get_ke_khai_detail(
    ke_khai_id: UUID,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Lấy chi tiết một kê khai theo ID.
    """
    # Query với eager loading
    stmt = (
        select(KeKhaiCongViec)
        .options(
            selectinload(KeKhaiCongViec.cong_chuc),
            selectinload(KeKhaiCongViec.danh_muc_sp).selectinload(DanhMucSpCongViec.sp_chuan),
            selectinload(KeKhaiCongViec.cap_do),
            selectinload(KeKhaiCongViec.nguoi_phe_duyet),
        )
        .where(KeKhaiCongViec.id == ke_khai_id)
        .where(KeKhaiCongViec.is_deleted == False)
    )
    
    result = await db.execute(stmt)
    ke_khai = result.scalar_one_or_none()
    
    if not ke_khai:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Không tìm thấy bản kê khai"
                }
            }
        )
    
    # Kiểm tra quyền xem: chủ sở hữu, người phê duyệt, QLDV cùng đơn vị, hoặc Admin
    is_owner = ke_khai.cong_chuc_id == current_user.id
    is_approver = ke_khai.nguoi_phe_duyet_id == current_user.id
    is_admin = getattr(current_user.vai_tro, 'is_system_admin', False) if current_user.vai_tro else False
    is_qldv_user = is_qldv(current_user)
    is_same_don_vi = (ke_khai.cong_chuc and ke_khai.cong_chuc.don_vi_id == current_user.don_vi_id)

    if not (is_owner or is_approver or is_admin or (is_qldv_user and is_same_don_vi)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_001",
                    "message": "Bạn không có quyền xem bản kê khai này"
                }
            }
        )
    
    data = ke_khai_to_response(ke_khai)
    return success_response(data=data)


# =============================================================================
# CREATE KE KHAI
# =============================================================================

@router.post(
    "",
    summary="Tạo kê khai mới",
    description="""
    Tạo bản kê khai công việc mới.
    
    **Trạng thái mặc định:** NHAP
    
    **Tự động tính toán:**
    - `thang`, `nam` từ ngày thực hiện hoặc ngày hiện tại
    - `so_sp_goc_quy_doi` theo công thức quy đổi
    
    **Tự đánh giá lỗi (CC tự nhập):**
    - `tu_danh_gia_chat_luong`: Số lỗi CL do CC tự đánh giá (mặc định: 0)
    - `tu_danh_gia_tien_do`: Số lần chậm TĐ do CC tự đánh giá (mặc định: 0)
    - `ghi_chu_tu_danh_gia`: Giải trình của CC về lỗi (optional)
    
    **Validation:**
    - Ngày thực hiện không được trong tương lai
    - Cấp độ C5 yêu cầu nhập hệ số thực tế
    
    **Quyền truy cập:** Tất cả user đã đăng nhập.
    """,
    response_model=DataResponse[KeKhaiResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_ke_khai(
    payload: KeKhaiCreate,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Tạo bản kê khai công việc mới.
    """
    # Block QLDV: QLDV không có quyền tạo kê khai
    if is_qldv(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_003",
                    "message": "QLDV không có quyền tạo kê khai. Chức năng này chỉ dành cho Công chức."
                }
            }
        )
    await _assert_v1_writable(db, current_user)

    # Xác định tháng/năm
    if payload.ngay_thuc_hien:
        thang = payload.ngay_thuc_hien.month
        nam = payload.ngay_thuc_hien.year
    else:
        today = date.today()
        thang = today.month
        nam = today.year
    
    # Tính điểm KPI quy đổi
    so_sp_goc_quy_doi, ma_sp = await calculate_kpi_score(
        db=db,
        danh_muc_sp_id=payload.danh_muc_sp_id,
        cap_do_id=payload.cap_do_id,
        so_luong=payload.so_luong,
        he_so_thuc_te=payload.he_so_thuc_te,
    )
    
    # Tạo bản kê khai
    ke_khai = KeKhaiCongViec(
        cong_chuc_id=current_user.id,
        don_vi_id_snapshot=current_user.don_vi_id,
        thang=thang,
        nam=nam,
        ngay_thuc_hien=payload.ngay_thuc_hien,
        danh_muc_sp_id=payload.danh_muc_sp_id,
        cap_do_id=payload.cap_do_id,
        so_luong=payload.so_luong,
        he_so_thuc_te=payload.he_so_thuc_te,
        nguoi_phe_duyet_id=payload.nguoi_phe_duyet_id,
        mo_ta_cong_viec=payload.mo_ta_cong_viec,
        is_doi_moi_sang_tao=payload.is_doi_moi_sang_tao,
        ngay_deadline=payload.ngay_deadline,
        ngay_hoan_thanh=payload.ngay_hoan_thanh,
        trang_thai=TrangThaiKeKhai.NHAP,
        so_sp_goc_quy_doi=so_sp_goc_quy_doi,
        # =====================================================================
        # TỰ ĐÁNH GIÁ CỦA CÔNG CHỨC (lưu từ body)
        # =====================================================================
        tu_danh_gia_chat_luong=payload.tu_danh_gia_chat_luong,
        tu_danh_gia_tien_do=payload.tu_danh_gia_tien_do,
        ghi_chu_tu_danh_gia=payload.ghi_chu_tu_danh_gia,
        # v2.7.4: Mô tả lỗi tự đánh giá
        ghi_chu_tu_dg_chat_luong=payload.ghi_chu_tu_dg_chat_luong,
        ghi_chu_tu_dg_tien_do=payload.ghi_chu_tu_dg_tien_do,
    )
    
    db.add(ke_khai)
    
    # v2.7.3: Đã bỏ unique constraint - cho phép cùng CV + cấp độ + ngày
    try:
        await db.commit()
        await db.refresh(ke_khai)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "CREATE_FAILED",
                    "message": f"Không thể tạo kê khai: {str(e)}"
                }
            }
        )
    
    # Load relationships để response
    stmt = (
        select(KeKhaiCongViec)
        .options(
            selectinload(KeKhaiCongViec.cong_chuc),
            selectinload(KeKhaiCongViec.danh_muc_sp).selectinload(DanhMucSpCongViec.sp_chuan),
            selectinload(KeKhaiCongViec.cap_do),
            selectinload(KeKhaiCongViec.nguoi_phe_duyet),
        )
        .where(KeKhaiCongViec.id == ke_khai.id)
    )
    result = await db.execute(stmt)
    ke_khai_full = result.scalar_one()
    
    data = ke_khai_to_response(ke_khai_full)
    return success_response(data=data, message="Tạo kê khai thành công")


# =============================================================================
# UPDATE KE KHAI
# =============================================================================

@router.put(
    "/{ke_khai_id}",
    summary="Cập nhật kê khai",
    description="""
    Cập nhật bản kê khai công việc.
    
    **Constraint:** Chỉ cho phép sửa khi trạng thái là:
    - NHAP (đang nháp)
    - TU_CHOI (bị từ chối, cho phép sửa lại)
    
    **Có thể cập nhật tự đánh giá:**
    - `tu_danh_gia_chat_luong`: Số lỗi CL do CC tự đánh giá
    - `tu_danh_gia_tien_do`: Số lần chậm TĐ do CC tự đánh giá
    - `ghi_chu_tu_danh_gia`: Giải trình của CC về lỗi
    
    **Quyền truy cập:** Chỉ chủ sở hữu.
    """,
    response_model=DataResponse[KeKhaiResponse],
    responses={
        404: {"description": "Không tìm thấy kê khai"},
        403: {"description": "Không có quyền sửa"},
        400: {"description": "Không thể sửa với trạng thái hiện tại"},
    }
)
async def update_ke_khai(
    ke_khai_id: UUID,
    payload: KeKhaiUpdate,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Cập nhật bản kê khai.
    """
    # Lấy kê khai
    stmt = (
        select(KeKhaiCongViec)
        .where(KeKhaiCongViec.id == ke_khai_id)
        .where(KeKhaiCongViec.is_deleted == False)
    )
    result = await db.execute(stmt)
    ke_khai = result.scalar_one_or_none()

    if not ke_khai:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Không tìm thấy bản kê khai"
                }
            }
        )

    _assert_kekhai_not_v1(ke_khai)

    # Kiểm tra quyền: chỉ chủ sở hữu
    if ke_khai.cong_chuc_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_002",
                    "message": "Bạn không có quyền sửa bản kê khai này"
                }
            }
        )
    
    # Kiểm tra trạng thái: chỉ sửa được khi NHAP hoặc TU_CHOI
    allowed_states = [TrangThaiKeKhai.NHAP, TrangThaiKeKhai.TU_CHOI]
    if ke_khai.trang_thai not in allowed_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_STATE",
                    "message": f"Không thể sửa kê khai ở trạng thái '{ke_khai.trang_thai.value}'. Chỉ được sửa khi ở trạng thái NHAP hoặc TU_CHOI."
                }
            }
        )
    
    # Update các trường được phép
    update_data = payload.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(ke_khai, field, value)
    
    # Nếu có thay đổi ngày thực hiện, cập nhật tháng/năm
    if payload.ngay_thuc_hien is not None:
        ke_khai.thang = payload.ngay_thuc_hien.month
        ke_khai.nam = payload.ngay_thuc_hien.year
    
    # Tính lại điểm nếu có thay đổi liên quan
    need_recalc = any([
        payload.danh_muc_sp_id is not None,
        payload.cap_do_id is not None,
        payload.so_luong is not None,
        payload.he_so_thuc_te is not None,
    ])
    
    if need_recalc:
        so_sp_goc_quy_doi, _ = await calculate_kpi_score(
            db=db,
            danh_muc_sp_id=ke_khai.danh_muc_sp_id,
            cap_do_id=ke_khai.cap_do_id,
            so_luong=ke_khai.so_luong,
            he_so_thuc_te=ke_khai.he_so_thuc_te,
        )
        ke_khai.so_sp_goc_quy_doi = so_sp_goc_quy_doi
    
    # Nếu đang TU_CHOI, chuyển về NHAP sau khi sửa
    if ke_khai.trang_thai == TrangThaiKeKhai.TU_CHOI:
        ke_khai.trang_thai = TrangThaiKeKhai.NHAP
    
    # v2.7.3: Đã bỏ duplicate check - cho phép cùng CV + cấp độ + ngày
    try:
        await db.commit()
        await db.refresh(ke_khai)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "UPDATE_FAILED",
                    "message": f"Không thể cập nhật kê khai: {str(e)}"
                }
            }
        )
    
    # Load relationships để response
    stmt = (
        select(KeKhaiCongViec)
        .options(
            selectinload(KeKhaiCongViec.cong_chuc),
            selectinload(KeKhaiCongViec.danh_muc_sp).selectinload(DanhMucSpCongViec.sp_chuan),
            selectinload(KeKhaiCongViec.cap_do),
            selectinload(KeKhaiCongViec.nguoi_phe_duyet),
        )
        .where(KeKhaiCongViec.id == ke_khai.id)
    )
    result = await db.execute(stmt)
    ke_khai_full = result.scalar_one()
    
    data = ke_khai_to_response(ke_khai_full)
    return success_response(data=data, message="Cập nhật kê khai thành công")


# =============================================================================
# DELETE KE KHAI
# =============================================================================

@router.delete(
    "/{ke_khai_id}",
    summary="Xóa kê khai",
    description="""
    Xóa bản kê khai (soft delete).
    
    **Constraint:** Chỉ xóa được khi trạng thái là NHAP hoặc TU_CHOI.
    
    **Quyền truy cập:** Chỉ chủ sở hữu.
    """,
    response_model=DataResponse[dict],
    responses={
        404: {"description": "Không tìm thấy kê khai"},
        403: {"description": "Không có quyền xóa"},
        400: {"description": "Không thể xóa với trạng thái hiện tại"},
    }
)
async def delete_ke_khai(
    ke_khai_id: UUID,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Xóa bản kê khai (soft delete).
    """
    # Lấy kê khai
    stmt = (
        select(KeKhaiCongViec)
        .where(KeKhaiCongViec.id == ke_khai_id)
        .where(KeKhaiCongViec.is_deleted == False)
    )
    result = await db.execute(stmt)
    ke_khai = result.scalar_one_or_none()

    if not ke_khai:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Không tìm thấy bản kê khai"
                }
            }
        )

    _assert_kekhai_not_v1(ke_khai)

    # Kiểm tra quyền: chỉ chủ sở hữu
    if ke_khai.cong_chuc_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_002",
                    "message": "Bạn không có quyền xóa bản kê khai này"
                }
            }
        )
    
    # Kiểm tra trạng thái: chỉ xóa được khi NHAP hoặc TU_CHOI
    # FIX (02/03/2026): Cho phép xóa kê khai bị từ chối (nhất quán với logic sửa)
    allowed_delete_states = [TrangThaiKeKhai.NHAP, TrangThaiKeKhai.TU_CHOI]
    if ke_khai.trang_thai not in allowed_delete_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_STATE",
                    "message": f"Không thể xóa kê khai ở trạng thái '{ke_khai.trang_thai.value}'. Chỉ được xóa khi ở trạng thái NHAP hoặc TU_CHOI."
                }
            }
        )
    
    # Soft delete
    ke_khai.is_deleted = True
    
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "DELETE_FAILED",
                    "message": f"Không thể xóa kê khai: {str(e)}"
                }
            }
        )
    
    return success_response(
        data={"id": ke_khai_id, "deleted": True},
        message="Xóa kê khai thành công"
    )


# =============================================================================
# GUI DUYET (Gửi phê duyệt)
# =============================================================================

@router.post(
    "/{ke_khai_id}/gui-duyet",
    summary="Gửi kê khai đi phê duyệt",
    description="""
    Chuyển trạng thái kê khai từ NHAP → CHO_PHE_DUYET.
    
    **Yêu cầu:** Phải chọn người phê duyệt (Phó đơn vị).
    
    **Quyền truy cập:** Chỉ chủ sở hữu.
    """,
    response_model=DataResponse[dict],
    responses={
        404: {"description": "Không tìm thấy kê khai"},
        403: {"description": "Không có quyền"},
        400: {"description": "Không thể gửi duyệt"},
    }
)
async def gui_duyet_ke_khai(
    ke_khai_id: UUID,
    payload: GuiDuyetRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Gửi kê khai đi phê duyệt.
    """
    # Lấy kê khai
    stmt = (
        select(KeKhaiCongViec)
        .where(KeKhaiCongViec.id == ke_khai_id)
        .where(KeKhaiCongViec.is_deleted == False)
    )
    result = await db.execute(stmt)
    ke_khai = result.scalar_one_or_none()

    if not ke_khai:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Không tìm thấy bản kê khai"
                }
            }
        )

    _assert_kekhai_not_v1(ke_khai)

    # Kiểm tra quyền: chỉ chủ sở hữu
    if ke_khai.cong_chuc_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_002",
                    "message": "Bạn không có quyền thao tác với bản kê khai này"
                }
            }
        )
    
    # Kiểm tra trạng thái: chỉ gửi duyệt được khi NHAP
    if ke_khai.trang_thai != TrangThaiKeKhai.NHAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_STATE",
                    "message": f"Không thể gửi duyệt kê khai ở trạng thái '{ke_khai.trang_thai.value}'. Chỉ được gửi khi ở trạng thái NHAP."
                }
            }
        )
    
    # Kiểm tra người phê duyệt tồn tại
    npd_stmt = (
        select(CongChuc)
        .where(CongChuc.id == payload.nguoi_phe_duyet_id)
        .where(CongChuc.is_deleted == False)
        .where(CongChuc.is_active == True)
    )
    npd_result = await db.execute(npd_stmt)
    nguoi_phe_duyet = npd_result.scalar_one_or_none()
    
    if not nguoi_phe_duyet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_APPROVER",
                    "message": "Người phê duyệt không tồn tại hoặc không hoạt động"
                }
            }
        )
    
    # Cập nhật trạng thái và người phê duyệt
    ke_khai.nguoi_phe_duyet_id = payload.nguoi_phe_duyet_id
    ke_khai.trang_thai = TrangThaiKeKhai.CHO_PHE_DUYET
    
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "UPDATE_FAILED",
                    "message": f"Không thể gửi phê duyệt: {str(e)}"
                }
            }
        )
    
    return success_response(
        data={
            "ke_khai_id": ke_khai_id,
            "nguoi_phe_duyet_id": payload.nguoi_phe_duyet_id,
            "trang_thai_moi": "CHO_PHE_DUYET",
        },
        message="Đã gửi kê khai đi phê duyệt thành công"
    )


# =============================================================================
# GET KE KHAI CUA CONG CHUC (Lãnh đạo/Admin xem kê khai CC khác)
# =============================================================================

@router.get(
    "/cong-chuc/{cong_chuc_id}",
    summary="Xem kê khai của công chức (dành cho Lãnh đạo/Admin)",
    description="""
    Lấy danh sách kê khai công việc của một công chức cụ thể.
    
    **Mục đích:** Dùng trong modal "Chi tiết công chức" của Báo cáo xếp loại,
    cho phép Đội trưởng/CCT xem chi tiết kê khai của CC trong đơn vị.
    
    **Quyền truy cập:**
    - Lãnh đạo đơn vị (TDV, PDV): Chỉ xem CC cùng đơn vị
    - Chi cục trưởng (CCT), Phó CCT: Xem tất cả CC
    - Admin: Xem tất cả CC
    
    **Filter options:**
    - `thang`: Lọc theo tháng (1-12)
    - `nam`: Lọc theo năm
    - `trang_thai`: Lọc theo trạng thái (mặc định: DA_PHE_DUYET)
    
    **Response:** Danh sách kê khai kèm thông tin danh mục SP, cấp độ.
    """,
    response_model=DataResponse[List[dict]],
    responses={
        403: {"description": "Không có quyền xem"},
        404: {"description": "Không tìm thấy công chức"},
    }
)
async def get_ke_khai_cong_chuc(
    cong_chuc_id: UUID,
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: Optional[int] = Query(default=None, ge=1, le=12, description="Filter theo tháng"),
    nam: Optional[int] = Query(default=None, ge=2025, description="Filter theo năm"),
    trang_thai: Optional[str] = Query(
        default=None,
        pattern="^(NHAP|CHO_PHE_DUYET|DA_PHE_DUYET|TU_CHOI|HUY)$",
        description="Filter theo trạng thái (mặc định: tất cả)"
    ),
) -> dict:
    """
    Lấy danh sách kê khai của một công chức cụ thể.
    Dành cho Lãnh đạo/Admin xem trong Báo cáo xếp loại.
    """
    # =========================================================================
    # 1. Kiểm tra quyền truy cập
    # =========================================================================
    is_admin = getattr(current_user.vai_tro, 'is_system_admin', False) if current_user.vai_tro else False
    cap_bac = current_user.vai_tro.cap_bac if current_user.vai_tro else None
    
    is_cct_or_pcct = cap_bac in [CapBacVaiTro.CHI_CUC_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG]
    is_lanh_dao_don_vi = cap_bac in [CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI]
    
    if not (is_admin or is_cct_or_pcct or is_lanh_dao_don_vi):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_001",
                    "message": "Chỉ Lãnh đạo hoặc Admin mới được xem kê khai của công chức khác"
                }
            }
        )
    
    # =========================================================================
    # 2. Kiểm tra công chức tồn tại
    # =========================================================================
    cc_stmt = (
        select(CongChuc)
        .where(CongChuc.id == cong_chuc_id)
        .where(CongChuc.is_deleted == False)
    )
    cc_result = await db.execute(cc_stmt)
    cong_chuc = cc_result.scalar_one_or_none()
    
    if not cong_chuc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Không tìm thấy công chức"
                }
            }
        )
    
    # =========================================================================
    # 3. Kiểm tra cùng đơn vị (nếu là lãnh đạo đơn vị)
    # =========================================================================
    if is_lanh_dao_don_vi and not is_admin and not is_cct_or_pcct:
        if cong_chuc.don_vi_id != current_user.don_vi_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_002",
                        "message": "Lãnh đạo đơn vị chỉ được xem kê khai của CC cùng đơn vị"
                    }
                }
            )
    
    # =========================================================================
    # 4. Query kê khai
    # =========================================================================
    base_query = (
        select(KeKhaiCongViec)
        .options(
            selectinload(KeKhaiCongViec.cong_chuc),
            selectinload(KeKhaiCongViec.danh_muc_sp).selectinload(DanhMucSpCongViec.sp_chuan),
            selectinload(KeKhaiCongViec.cap_do),
            selectinload(KeKhaiCongViec.nguoi_phe_duyet),
        )
        .where(KeKhaiCongViec.cong_chuc_id == cong_chuc_id)
        .where(KeKhaiCongViec.is_deleted == False)
    )
    
    # Apply filters
    if thang:
        base_query = base_query.where(KeKhaiCongViec.thang == thang)
    if nam:
        base_query = base_query.where(KeKhaiCongViec.nam == nam)
    if trang_thai:
        base_query = base_query.where(KeKhaiCongViec.trang_thai == TrangThaiKeKhai(trang_thai))
    
    base_query = base_query.order_by(KeKhaiCongViec.created_at.desc())
    
    # Execute
    result = await db.execute(base_query)
    ke_khai_list = result.scalars().all()
    
    # Convert to response
    data = [ke_khai_to_response(kk) for kk in ke_khai_list]
    
    return success_response(
        data=data,
        message=f"Danh sách kê khai của {cong_chuc.ho_ten} ({len(data)} bản ghi)"
    )