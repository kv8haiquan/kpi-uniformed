"""
app/api/v1/endpoints/ke_khai_lanh_dao.py
========================================
API Endpoints cho Kê khai công việc Lãnh đạo.

Phiên bản: 2.7.4 (02/02/2026)
Cập nhật:
- v2.7.4: Thêm ghi_chu_loi_chat_luong, ghi_chu_loi_tien_do (mô tả lỗi)
- v2.6.0: Thêm GET /cho-phe-duyet, POST /{id}/phe-duyet
- v2.6.1: Fix MissingGreenlet - refresh object trước, relationship sau
- v2.6.2: Fix endpoint /lich-su không trả về data - so sánh enum.value thay vì enum
- v2.6.4: Thêm tong_loi_chat_luong, tong_loi_tien_do vào thống kê
- v2.6.5: Thêm tong_diem_chat_luong, tong_diem_tien_do để tính b, c đúng công thức
         Công thức: b = Σ(max(0, 1 - lỗi_i × 0.25)) / Tổng CV
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import DatabaseDep, ActiveUserDep, is_qldv
from app.models.leader_kpi import (
    KeKhaiLanhDao,
    TrangThaiKeKhaiLD,
    TrangThaiHoanThanh
)
from app.models.user_org import CongChuc, VaiTro, CapBacVaiTro
from app.schemas.common import success_response, error_response, Pagination
from app.schemas.leader_kpi import (
    KeKhaiLanhDaoCreate, KeKhaiLanhDaoUpdate, GuiDuyetRequest,
    PheDuyetKeKhaiLDRequest, ThongKeKeKhaiLDResponse,
)


class TraLaiKeKhaiLDRequest(BaseModel):
    """Yêu cầu trả lại kê khai lãnh đạo đã phê duyệt."""
    ly_do: str = Field(..., min_length=1, max_length=500, description="Lý do trả lại")

router = APIRouter()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def check_is_lanh_dao(user: CongChuc) -> bool:
    """Kiểm tra user có quyền dùng form ke_khai_lanh_dao.
    Phase 3 (29/04/2026): mở rộng cho HĐ 111 — dùng cùng form."""
    if user.is_lanh_dao or user.is_hd_111:
        return True
    if user.vai_tro and user.vai_tro.cap_bac in [
        CapBacVaiTro.PHO_DON_VI, CapBacVaiTro.TRUONG_DON_VI,
        CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG,
    ]:
        return True
    return False


async def get_nguoi_phe_duyet_cho_lanh_dao(db: AsyncSession, current_user: CongChuc) -> tuple[List[CongChuc], str]:
    """Xác định danh sách người phê duyệt cho Lãnh đạo (hoặc HĐ 111).

    Phase 3 (29/04/2026): HĐ 111 chọn TDV/PDV trong cùng đơn vị (giống CC).
    """
    approvers, ghi_chu = [], ""
    if not current_user.vai_tro:
        return [], "Không có vai trò"

    # HĐ 111: chọn TDV/PDV cùng đơn vị (giống flow CC thường)
    if current_user.is_hd_111:
        stmt = select(CongChuc).join(VaiTro).where(
            CongChuc.is_active == True,
            CongChuc.don_vi_id == current_user.don_vi_id,
            VaiTro.cap_bac.in_([CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI]),
        )
        result = await db.execute(stmt)
        approvers = list(result.scalars().all())
        return approvers, "Người phê duyệt: Trưởng/Phó đơn vị"

    cap_bac = current_user.vai_tro.cap_bac

    if cap_bac == CapBacVaiTro.CHI_CUC_TRUONG:
        approvers, ghi_chu = [current_user], "Chi cục trưởng tự phê duyệt"
    elif cap_bac in [CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.TRUONG_DON_VI]:
        stmt = select(CongChuc).join(VaiTro).where(
            CongChuc.is_active == True, VaiTro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG
        )
        result = await db.execute(stmt)
        approvers, ghi_chu = list(result.scalars().all()), "Người phê duyệt: Chi cục trưởng"
    elif cap_bac == CapBacVaiTro.PHO_DON_VI:
        stmt = select(CongChuc).join(VaiTro).where(
            CongChuc.is_active == True, CongChuc.don_vi_id == current_user.don_vi_id,
            VaiTro.cap_bac == CapBacVaiTro.TRUONG_DON_VI
        )
        result = await db.execute(stmt)
        approvers, ghi_chu = list(result.scalars().all()), "Người phê duyệt: Trưởng đơn vị"

    return approvers, ghi_chu


async def refresh_ke_khai_full(db: AsyncSession, ke_khai: KeKhaiLanhDao, include_cong_chuc: bool = False) -> None:
    """
    Refresh đầy đủ object KeKhaiLanhDao.
    
    FIX MissingGreenlet: Phải refresh object TRƯỚC, rồi mới refresh relationships.
    Nếu không, các scalar attributes (created_at, updated_at) chưa được load
    sẽ gây lỗi khi truy cập trong build_ke_khai_response().
    
    Args:
        db: Database session
        ke_khai: Object cần refresh
        include_cong_chuc: Có refresh relationship cong_chuc không (cho endpoint phê duyệt)
    """
    # Bước 1: Refresh toàn bộ scalar attributes
    await db.refresh(ke_khai)
    
    # Bước 2: Refresh relationships (nếu có)
    if ke_khai.nguoi_phe_duyet_id:
        await db.refresh(ke_khai, ["nguoi_phe_duyet"])
    
    if include_cong_chuc and ke_khai.cong_chuc_id:
        await db.refresh(ke_khai, ["cong_chuc"])


def build_ke_khai_response(kk: KeKhaiLanhDao, include_cong_chuc: bool = False) -> dict:
    """Build response dict từ model."""
    # Xử lý trang_thai_hoan_thanh - có thể là enum hoặc string
    trang_thai_ht = kk.trang_thai_hoan_thanh
    if hasattr(trang_thai_ht, 'value'):
        trang_thai_ht = trang_thai_ht.value
    
    response = {
        "id": kk.id, "cong_chuc_id": kk.cong_chuc_id, "thang": kk.thang, "nam": kk.nam,
        "ten_cong_viec": kk.ten_cong_viec, "mo_ta": kk.mo_ta,
        "ngay_thuc_hien": kk.ngay_thuc_hien, 
        "trang_thai_hoan_thanh": trang_thai_ht,
        "so_luong": kk.so_luong, "nguoi_phe_duyet_id": kk.nguoi_phe_duyet_id,
        "nguoi_phe_duyet": None, "trang_thai": kk.trang_thai,
        "so_loi_chat_luong": kk.so_loi_chat_luong, "so_loi_tien_do": kk.so_loi_tien_do,
        # v2.7.4: Mô tả lỗi
        "ghi_chu_loi_chat_luong": kk.ghi_chu_loi_chat_luong,
        "ghi_chu_loi_tien_do": kk.ghi_chu_loi_tien_do,
        "y_kien_lanh_dao": kk.y_kien_lanh_dao,
        "created_at": kk.created_at, "updated_at": kk.updated_at,
    }
    
    # Thông tin người phê duyệt
    if kk.nguoi_phe_duyet:
        response["nguoi_phe_duyet"] = {
            "id": kk.nguoi_phe_duyet.id, "ma_cc": kk.nguoi_phe_duyet.ma_cc,
            "ho_ten": kk.nguoi_phe_duyet.ho_ten, "chuc_vu": kk.nguoi_phe_duyet.chuc_vu,
        }
    
    # Thông tin người kê khai (cho endpoint phê duyệt)
    if include_cong_chuc and kk.cong_chuc:
        response["cong_chuc"] = {
            "id": kk.cong_chuc.id, "ma_cc": kk.cong_chuc.ma_cc,
            "ho_ten": kk.cong_chuc.ho_ten, "chuc_vu": kk.cong_chuc.chuc_vu,
            # Phase 3 (29/04/2026): phân biệt HĐ 111 vs LĐ thật trong UI duyệt
            "is_hd_111": kk.cong_chuc.is_hd_111,
            "is_lanh_dao": kk.cong_chuc.is_lanh_dao,
        }

    return response


# =============================================================================
# GET - Danh sách người phê duyệt (ĐẶT TRƯỚC route có path param)
# =============================================================================

@router.get("/nguoi-phe-duyet")
async def get_nguoi_phe_duyet(db: DatabaseDep, current_user: ActiveUserDep) -> dict:
    """Lấy danh sách người phê duyệt cho Lãnh đạo hiện tại."""
    if not check_is_lanh_dao(current_user):
        raise HTTPException(status_code=403, detail=error_response(code="PERM_003", message="Chỉ Lãnh đạo"))
    
    approvers, ghi_chu = await get_nguoi_phe_duyet_cho_lanh_dao(db, current_user)
    
    data = {
        "danh_sach": [
            {
                "id": a.id, "ma_cc": a.ma_cc, "ho_ten": a.ho_ten, "chuc_vu": a.chuc_vu,
                "vai_tro": {"ma_vai_tro": a.vai_tro.ma_vai_tro, "ten_vai_tro": a.vai_tro.ten_vai_tro} if a.vai_tro else None,
                "don_vi": {"id": a.don_vi.id, "ten_don_vi": a.don_vi.ten_don_vi} if a.don_vi else None
            }
            for a in approvers
        ],
        "ghi_chu": ghi_chu
    }
    return success_response(data=data, message="Lấy danh sách người phê duyệt thành công")


# =============================================================================
# GET - Danh sách kê khai chờ phê duyệt (v2.6.0)
# =============================================================================

@router.get("/cho-phe-duyet")
async def get_ke_khai_cho_phe_duyet(
    db: DatabaseDep, current_user: ActiveUserDep,
    thang: Optional[int] = Query(default=None, ge=1, le=12),
    nam: Optional[int] = Query(default=None, ge=2025),
) -> dict:
    """
    Lấy danh sách kê khai công việc Lãnh đạo chờ tôi phê duyệt.

    Logic:
    - Lấy các kê khai có nguoi_phe_duyet_id = current_user.id
    - Và trang_thai = CHO_PHE_DUYET
    - QLDV chỉ xem, KHÔNG phê duyệt
    """
    if not check_is_lanh_dao(current_user) and not is_qldv(current_user):
        raise HTTPException(status_code=403, detail=error_response(code="PERM_003", message="Chỉ Lãnh đạo"))
    
    stmt = (
        select(KeKhaiLanhDao)
        .options(
            selectinload(KeKhaiLanhDao.cong_chuc),
            selectinload(KeKhaiLanhDao.nguoi_phe_duyet)
        )
        .where(
            KeKhaiLanhDao.nguoi_phe_duyet_id == current_user.id,
            KeKhaiLanhDao.trang_thai == TrangThaiKeKhaiLD.CHO_PHE_DUYET.value,
            KeKhaiLanhDao.is_deleted == False,
        )
    )
    
    if thang:
        stmt = stmt.where(KeKhaiLanhDao.thang == thang)
    if nam:
        stmt = stmt.where(KeKhaiLanhDao.nam == nam)
    
    stmt = stmt.order_by(KeKhaiLanhDao.created_at.desc())
    
    result = await db.execute(stmt)
    data = [build_ke_khai_response(kk, include_cong_chuc=True) for kk in result.scalars().all()]
    
    return success_response(data=data, message=f"Có {len(data)} kê khai chờ phê duyệt")


# =============================================================================
# GET - Thống kê theo tháng
# =============================================================================

@router.get("/thong-ke/thang")
async def get_thong_ke(db: DatabaseDep, current_user: ActiveUserDep,
    thang: int = Query(..., ge=1, le=12), nam: int = Query(..., ge=2025)) -> dict:
    """
    Thống kê kê khai theo tháng cho Lãnh đạo.

    v2.6.3 UPDATE: Thêm fields tạm tính để hỗ trợ 2-tab UI

    **Response mới:**
    - Chính thức (chỉ DA_PHE_DUYET): tong_da_duyet, tong_hoan_thanh, tong_dat_chat_luong, tong_dung_tien_do
    - Tạm tính (tất cả): tam_tinh_*, dùng để hiển thị tab "Tạm tính" trước khi duyệt
    - QLDV chỉ xem thống kê
    """
    if not check_is_lanh_dao(current_user) and not is_qldv(current_user):
        raise HTTPException(status_code=403, detail=error_response(code="PERM_003", message="Chỉ Lãnh đạo"))
    
    stmt = select(KeKhaiLanhDao).where(
        KeKhaiLanhDao.cong_chuc_id == current_user.id, KeKhaiLanhDao.thang == thang,
        KeKhaiLanhDao.nam == nam, KeKhaiLanhDao.is_deleted == False,
    )
    ke_khai_list = (await db.execute(stmt)).scalars().all()
    
    # =========================================================================
    # PHÂN LOẠI KÊ KHAI THEO TRẠNG THÁI
    # =========================================================================
    kk_da_duyet = [k for k in ke_khai_list if k.trang_thai == TrangThaiKeKhaiLD.DA_PHE_DUYET.value]
    kk_cho_duyet = [k for k in ke_khai_list if k.trang_thai == TrangThaiKeKhaiLD.CHO_PHE_DUYET.value]
    kk_nhap = [k for k in ke_khai_list if k.trang_thai == TrangThaiKeKhaiLD.NHAP.value]
    kk_tu_choi = [k for k in ke_khai_list if k.trang_thai == TrangThaiKeKhaiLD.TU_CHOI.value]
    
    # Tạm tính = NHAP + CHO_PHE_DUYET + DA_PHE_DUYET (không tính TU_CHOI)
    kk_tam_tinh = kk_nhap + kk_cho_duyet + kk_da_duyet
    
    # =========================================================================
    # TÍNH TOÁN CHO PHẦN CHÍNH THỨC (chỉ DA_PHE_DUYET)
    # =========================================================================
    tong_hoan_thanh = sum(1 for k in kk_da_duyet if k.trang_thai_hoan_thanh == TrangThaiHoanThanh.DA_HOAN_THANH)
    tong_dat_chat_luong = sum(1 for k in kk_da_duyet if k.so_loi_chat_luong == 0)
    tong_dung_tien_do = sum(1 for k in kk_da_duyet if k.so_loi_tien_do == 0)
    
    # v2.6.4: Tính tổng số lỗi để hiển thị
    tong_loi_chat_luong = sum(k.so_loi_chat_luong or 0 for k in kk_da_duyet)
    tong_loi_tien_do = sum(k.so_loi_tien_do or 0 for k in kk_da_duyet)
    
    # v2.6.5: Tính tổng điểm chất lượng & tiến độ theo công thức mới
    # Mỗi CV: điểm = max(0, 1 - số_lỗi × 0.25)
    # b = Tổng điểm tiến độ các CV / Tổng CV
    # c = Tổng điểm chất lượng các CV / Tổng CV
    tong_diem_chat_luong = sum(max(0, 1 - (k.so_loi_chat_luong or 0) * 0.25) for k in kk_da_duyet)
    tong_diem_tien_do = sum(max(0, 1 - (k.so_loi_tien_do or 0) * 0.25) for k in kk_da_duyet)
    
    # =========================================================================
    # TÍNH TOÁN CHO PHẦN TẠM TÍNH (v2.6.3, FIX v2.7.3)
    # v2.7.3: Đọc so_loi từ DB cho MỌI trạng thái (NHAP cũng có so_loi
    #         vì Lãnh đạo tự nhập khi kê khai)
    # =========================================================================
    tam_tinh_tong_cong_viec = len(kk_tam_tinh)
    tam_tinh_hoan_thanh = sum(1 for k in kk_tam_tinh if k.trang_thai_hoan_thanh == TrangThaiHoanThanh.DA_HOAN_THANH)
    
    # CV đạt CL tạm tính:
    # - DA_PHE_DUYET: so_loi_chat_luong == 0
    # - NHAP/CHO_PHE_DUYET: chưa có đánh giá → coi như đạt (lạc quan)
    tam_tinh_dat_chat_luong = 0
    tam_tinh_dung_tien_do = 0
    
    # v2.6.4: Thêm tổng số lỗi tạm tính
    tam_tinh_loi_chat_luong = 0
    tam_tinh_loi_tien_do = 0
    
    # v2.6.5: Tính tổng điểm tạm tính
    tam_tinh_diem_chat_luong = 0.0
    tam_tinh_diem_tien_do = 0.0
    
    for k in kk_tam_tinh:
        # v2.7.3: Đọc số lỗi tự đánh giá từ DB cho MỌI trạng thái
        # (Lãnh đạo tự nhập so_loi khi kê khai, dù chưa duyệt vẫn có giá trị)
        loi_cl = k.so_loi_chat_luong or 0
        loi_td = k.so_loi_tien_do or 0
        tam_tinh_loi_chat_luong += loi_cl
        tam_tinh_loi_tien_do += loi_td
        # Tính điểm: max(0, 1 - lỗi × 0.25)
        tam_tinh_diem_chat_luong += max(0, 1 - loi_cl * 0.25)
        tam_tinh_diem_tien_do += max(0, 1 - loi_td * 0.25)
        if loi_cl == 0:
            tam_tinh_dat_chat_luong += 1
        if loi_td == 0:
            tam_tinh_dung_tien_do += 1
    
    # =========================================================================
    # BUILD RESPONSE
    # =========================================================================
    data = {
        "thang": thang, 
        "nam": nam, 
        "tong_cong_viec": len(ke_khai_list),
        
        # Phân loại theo trạng thái kê khai
        "tong_da_duyet": len(kk_da_duyet),
        "tong_cho_duyet": len(kk_cho_duyet),
        "tong_tu_choi": len(kk_tu_choi),
        "tong_nhap": len(kk_nhap),
        
        # =====================================================================
        # CHÍNH THỨC (chỉ DA_PHE_DUYET)
        # =====================================================================
        "tong_hoan_thanh": tong_hoan_thanh,
        "tong_chua_hoan_thanh": len(kk_da_duyet) - tong_hoan_thanh,
        "tong_dat_chat_luong": tong_dat_chat_luong,
        "tong_dung_tien_do": tong_dung_tien_do,
        # v2.6.4: Thêm tổng số lỗi (để hiển thị)
        "tong_loi_chat_luong": tong_loi_chat_luong,
        "tong_loi_tien_do": tong_loi_tien_do,
        # v2.6.5: Thêm tổng điểm (để tính b, c chính xác)
        # b = tong_diem_tien_do / tong_da_duyet
        # c = tong_diem_chat_luong / tong_da_duyet
        "tong_diem_chat_luong": round(tong_diem_chat_luong, 4),
        "tong_diem_tien_do": round(tong_diem_tien_do, 4),
        
        # =====================================================================
        # TẠM TÍNH (NHAP + CHO_PHE_DUYET + DA_PHE_DUYET) - v2.6.3 NEW
        # =====================================================================
        "tam_tinh_tong_cong_viec": tam_tinh_tong_cong_viec,
        "tam_tinh_hoan_thanh": tam_tinh_hoan_thanh,
        "tam_tinh_chua_hoan_thanh": tam_tinh_tong_cong_viec - tam_tinh_hoan_thanh,
        "tam_tinh_dat_chat_luong": tam_tinh_dat_chat_luong,
        "tam_tinh_dung_tien_do": tam_tinh_dung_tien_do,
        # v2.6.4: Thêm tổng số lỗi tạm tính
        "tam_tinh_loi_chat_luong": tam_tinh_loi_chat_luong,
        "tam_tinh_loi_tien_do": tam_tinh_loi_tien_do,
        # v2.6.5: Thêm tổng điểm tạm tính
        "tam_tinh_diem_chat_luong": round(tam_tinh_diem_chat_luong, 4),
        "tam_tinh_diem_tien_do": round(tam_tinh_diem_tien_do, 4),
    }
    
    return success_response(data=data, message="Thống kê thành công")


# =============================================================================
# GET - Danh sách kê khai của tôi
# =============================================================================

@router.get("")
async def get_ke_khai_lanh_dao(
    db: DatabaseDep, current_user: ActiveUserDep,
    thang: int = Query(..., ge=1, le=12), nam: int = Query(..., ge=2025),
    trang_thai: Optional[str] = Query(default=None),
) -> dict:
    """Lấy danh sách kê khai công việc của Lãnh đạo (của chính mình). QLDV chỉ xem."""
    if not check_is_lanh_dao(current_user) and not is_qldv(current_user):
        raise HTTPException(status_code=403, detail=error_response(code="PERM_003", message="Chỉ Lãnh đạo"))
    
    stmt = select(KeKhaiLanhDao).options(selectinload(KeKhaiLanhDao.nguoi_phe_duyet)).where(
        KeKhaiLanhDao.cong_chuc_id == current_user.id, KeKhaiLanhDao.thang == thang,
        KeKhaiLanhDao.nam == nam, KeKhaiLanhDao.is_deleted == False,
    )
    if trang_thai:
        stmt = stmt.where(KeKhaiLanhDao.trang_thai == trang_thai)
    stmt = stmt.order_by(KeKhaiLanhDao.ngay_thuc_hien.desc())
    
    result = await db.execute(stmt)
    data = [build_ke_khai_response(kk) for kk in result.scalars().all()]
    return success_response(data=data, message=f"Lấy danh sách kê khai tháng {thang}/{nam} thành công")


# =============================================================================
# POST - Tạo kê khai mới
# =============================================================================

@router.post("")
async def create_ke_khai_lanh_dao(
    db: DatabaseDep, current_user: ActiveUserDep, payload: KeKhaiLanhDaoCreate,
) -> dict:
    """Tạo kê khai công việc mới cho Lãnh đạo. QLDV KHÔNG được tạo."""
    # QLDV không có quyền tạo
    if is_qldv(current_user):
        raise HTTPException(status_code=403, detail=error_response(code="PERM_003", message="QLDV không có quyền tạo kê khai"))

    if not check_is_lanh_dao(current_user):
        raise HTTPException(status_code=403, detail=error_response(code="PERM_003", message="Chỉ Lãnh đạo"))

    # Phase 3 (05/05/2026): LĐ thật từ tháng 4/2026 phải kê khai trên /ke-khai-v2
    # (HĐ 111 vẫn dùng form này như cũ)
    from app.core.kpi_lanh_dao_v2 import is_kpi_lanh_dao_v2_active
    if current_user.is_lanh_dao and is_kpi_lanh_dao_v2_active(payload.thang, payload.nam):
        raise HTTPException(
            status_code=400,
            detail=error_response(
                code="LD_USE_V2",
                message=(
                    "Từ tháng 4/2026 lãnh đạo kê khai theo form mới (V2). "
                    "Vui lòng dùng /ke-khai-v2."
                ),
            ),
        )

    # Validate ngày thực hiện
    if payload.ngay_thuc_hien.month != payload.thang or payload.ngay_thuc_hien.year != payload.nam:
        raise HTTPException(status_code=400, detail=error_response(
            code="VAL_003", message=f"Ngày thực hiện phải trong tháng {payload.thang}/{payload.nam}"
        ))
    
    # Validate người phê duyệt
    if payload.nguoi_phe_duyet_id:
        approvers, _ = await get_nguoi_phe_duyet_cho_lanh_dao(db, current_user)
        if payload.nguoi_phe_duyet_id not in [a.id for a in approvers]:
            raise HTTPException(status_code=400, detail=error_response(code="VAL_004", message="Người phê duyệt không hợp lệ"))
    
    # Convert string enum value → Python Enum object
    trang_thai_ht = TrangThaiHoanThanh(payload.trang_thai_hoan_thanh.value)
    
    ke_khai = KeKhaiLanhDao(
        cong_chuc_id=current_user.id, thang=payload.thang, nam=payload.nam,
        ten_cong_viec=payload.ten_cong_viec, mo_ta=payload.mo_ta,
        ngay_thuc_hien=payload.ngay_thuc_hien, 
        trang_thai_hoan_thanh=trang_thai_ht,
        so_luong=payload.so_luong, nguoi_phe_duyet_id=payload.nguoi_phe_duyet_id,
        trang_thai=TrangThaiKeKhaiLD.NHAP.value,
        # v2.7.3: Lưu số lỗi tự đánh giá
        so_loi_chat_luong=getattr(payload, 'so_loi_chat_luong', 0) or 0,
        so_loi_tien_do=getattr(payload, 'so_loi_tien_do', 0) or 0,
        # v2.7.4: Mô tả lỗi
        ghi_chu_loi_chat_luong=getattr(payload, 'ghi_chu_loi_chat_luong', None),
        ghi_chu_loi_tien_do=getattr(payload, 'ghi_chu_loi_tien_do', None),
    )
    db.add(ke_khai)
    await db.flush()
    
    # FIX v2.6.1: Refresh đầy đủ object
    await refresh_ke_khai_full(db, ke_khai)
    
    return success_response(data=build_ke_khai_response(ke_khai), message="Tạo kê khai công việc thành công")


# =============================================================================
# PUT - Cập nhật kê khai
# =============================================================================

@router.put("/{ke_khai_id}")
async def update_ke_khai_lanh_dao(
    db: DatabaseDep, current_user: ActiveUserDep, ke_khai_id: UUID, payload: KeKhaiLanhDaoUpdate,
) -> dict:
    """Cập nhật kê khai. Chỉ được sửa khi trạng thái = NHAP hoặc TU_CHOI. QLDV KHÔNG được sửa."""
    # QLDV không có quyền sửa
    if is_qldv(current_user):
        raise HTTPException(status_code=403, detail=error_response(code="PERM_003", message="QLDV không có quyền cập nhật kê khai"))

    stmt = select(KeKhaiLanhDao).where(
        KeKhaiLanhDao.id == ke_khai_id, KeKhaiLanhDao.cong_chuc_id == current_user.id,
        KeKhaiLanhDao.is_deleted == False,
    )
    ke_khai = (await db.execute(stmt)).scalar_one_or_none()
    if not ke_khai:
        raise HTTPException(status_code=404, detail=error_response(code="NOT_FOUND", message="Không tìm thấy"))
    if ke_khai.trang_thai not in [TrangThaiKeKhaiLD.NHAP.value, TrangThaiKeKhaiLD.TU_CHOI.value]:
        raise HTTPException(status_code=400, detail=error_response(code="BIZ_001", message=f"Không thể sửa ở trạng thái {ke_khai.trang_thai}"))
    
    if payload.ten_cong_viec is not None: ke_khai.ten_cong_viec = payload.ten_cong_viec
    if payload.mo_ta is not None: ke_khai.mo_ta = payload.mo_ta
    if payload.ngay_thuc_hien is not None:
        if payload.ngay_thuc_hien.month != ke_khai.thang or payload.ngay_thuc_hien.year != ke_khai.nam:
            raise HTTPException(status_code=400, detail=error_response(code="VAL_003", message=f"Ngày phải trong tháng {ke_khai.thang}/{ke_khai.nam}"))
        ke_khai.ngay_thuc_hien = payload.ngay_thuc_hien
    if payload.trang_thai_hoan_thanh is not None: 
        ke_khai.trang_thai_hoan_thanh = TrangThaiHoanThanh(payload.trang_thai_hoan_thanh.value)
    if payload.so_luong is not None: ke_khai.so_luong = payload.so_luong
    if payload.nguoi_phe_duyet_id is not None: ke_khai.nguoi_phe_duyet_id = payload.nguoi_phe_duyet_id
    # v2.7.3: Cập nhật số lỗi tự đánh giá
    if getattr(payload, 'so_loi_chat_luong', None) is not None: ke_khai.so_loi_chat_luong = payload.so_loi_chat_luong
    if getattr(payload, 'so_loi_tien_do', None) is not None: ke_khai.so_loi_tien_do = payload.so_loi_tien_do
    # v2.7.4: Cập nhật mô tả lỗi
    if getattr(payload, 'ghi_chu_loi_chat_luong', None) is not None: ke_khai.ghi_chu_loi_chat_luong = payload.ghi_chu_loi_chat_luong
    if getattr(payload, 'ghi_chu_loi_tien_do', None) is not None: ke_khai.ghi_chu_loi_tien_do = payload.ghi_chu_loi_tien_do
    if ke_khai.trang_thai == TrangThaiKeKhaiLD.TU_CHOI.value: ke_khai.trang_thai = TrangThaiKeKhaiLD.NHAP.value
    
    await db.flush()
    
    # FIX v2.6.1: Refresh đầy đủ object
    await refresh_ke_khai_full(db, ke_khai)
    
    return success_response(data=build_ke_khai_response(ke_khai), message="Cập nhật thành công")


# =============================================================================
# DELETE - Xóa kê khai
# =============================================================================

@router.delete("/{ke_khai_id}")
async def delete_ke_khai_lanh_dao(db: DatabaseDep, current_user: ActiveUserDep, ke_khai_id: UUID) -> dict:
    """Xóa kê khai (soft delete). Chỉ được xóa khi trạng thái = NHAP hoặc TU_CHOI. QLDV KHÔNG được xóa."""
    # QLDV không có quyền xóa
    if is_qldv(current_user):
        raise HTTPException(status_code=403, detail=error_response(code="PERM_003", message="QLDV không có quyền xóa kê khai"))

    stmt = select(KeKhaiLanhDao).where(
        KeKhaiLanhDao.id == ke_khai_id, KeKhaiLanhDao.cong_chuc_id == current_user.id,
        KeKhaiLanhDao.is_deleted == False,
    )
    ke_khai = (await db.execute(stmt)).scalar_one_or_none()
    if not ke_khai:
        raise HTTPException(status_code=404, detail=error_response(code="NOT_FOUND", message="Không tìm thấy"))
    if ke_khai.trang_thai not in [TrangThaiKeKhaiLD.NHAP.value, TrangThaiKeKhaiLD.TU_CHOI.value]:
        raise HTTPException(status_code=400, detail=error_response(code="BIZ_001", message=f"Không thể xóa ở trạng thái {ke_khai.trang_thai}"))
    
    ke_khai.is_deleted = True
    await db.flush()
    return success_response(data={"id": ke_khai_id}, message="Xóa thành công")


# =============================================================================
# POST - Gửi phê duyệt
# =============================================================================

@router.post("/{ke_khai_id}/gui-duyet")
async def gui_duyet_ke_khai(db: DatabaseDep, current_user: ActiveUserDep, ke_khai_id: UUID, payload: GuiDuyetRequest) -> dict:
    """Gửi kê khai để phê duyệt. QLDV KHÔNG được gửi duyệt."""
    # QLDV không có quyền gửi duyệt
    if is_qldv(current_user):
        raise HTTPException(status_code=403, detail=error_response(code="PERM_003", message="QLDV không có quyền gửi phê duyệt"))

    stmt = select(KeKhaiLanhDao).where(
        KeKhaiLanhDao.id == ke_khai_id, KeKhaiLanhDao.cong_chuc_id == current_user.id,
        KeKhaiLanhDao.is_deleted == False,
    )
    ke_khai = (await db.execute(stmt)).scalar_one_or_none()
    if not ke_khai:
        raise HTTPException(status_code=404, detail=error_response(code="NOT_FOUND", message="Không tìm thấy"))
    if ke_khai.trang_thai not in [TrangThaiKeKhaiLD.NHAP.value, TrangThaiKeKhaiLD.TU_CHOI.value]:
        raise HTTPException(status_code=400, detail=error_response(code="BIZ_001", message=f"Không thể gửi duyệt ở trạng thái {ke_khai.trang_thai}"))
    
    approvers, _ = await get_nguoi_phe_duyet_cho_lanh_dao(db, current_user)
    if payload.nguoi_phe_duyet_id not in [a.id for a in approvers]:
        raise HTTPException(status_code=400, detail=error_response(code="VAL_004", message="Người phê duyệt không hợp lệ"))
    
    ke_khai.nguoi_phe_duyet_id = payload.nguoi_phe_duyet_id
    ke_khai.trang_thai = TrangThaiKeKhaiLD.CHO_PHE_DUYET.value
    await db.flush()
    
    # FIX v2.6.1: Refresh đầy đủ object
    await refresh_ke_khai_full(db, ke_khai)
    
    return success_response(data=build_ke_khai_response(ke_khai), message="Gửi phê duyệt thành công")


# =============================================================================
# POST - Phê duyệt/Từ chối kê khai (v2.6.0)
# =============================================================================

@router.post("/{ke_khai_id}/phe-duyet")
async def phe_duyet_ke_khai_lanh_dao(
    db: DatabaseDep, current_user: ActiveUserDep,
    ke_khai_id: UUID, payload: PheDuyetKeKhaiLDRequest,
) -> dict:
    """
    Phê duyệt hoặc từ chối kê khai công việc Lãnh đạo.

    Payload:
    {
        "action": "APPROVE" | "REJECT",
        "so_loi_chat_luong": 0,  // Chỉ khi APPROVE
        "so_loi_tien_do": 0,     // Chỉ khi APPROVE
        "y_kien": "..."          // Optional
    }

    QLDV KHÔNG có quyền phê duyệt.
    """
    # QLDV không có quyền phê duyệt
    if is_qldv(current_user):
        raise HTTPException(status_code=403, detail=error_response(code="PERM_003", message="QLDV không có quyền phê duyệt"))

    # Lấy kê khai (kèm relationship)
    stmt = (
        select(KeKhaiLanhDao)
        .options(
            selectinload(KeKhaiLanhDao.cong_chuc),
            selectinload(KeKhaiLanhDao.nguoi_phe_duyet)
        )
        .where(
            KeKhaiLanhDao.id == ke_khai_id,
            KeKhaiLanhDao.is_deleted == False,
        )
    )
    ke_khai = (await db.execute(stmt)).scalar_one_or_none()
    
    if not ke_khai:
        raise HTTPException(status_code=404, detail=error_response(code="NOT_FOUND", message="Không tìm thấy kê khai"))
    
    # Kiểm tra quyền phê duyệt
    is_cct = current_user.vai_tro and current_user.vai_tro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG
    if ke_khai.nguoi_phe_duyet_id != current_user.id and not is_cct:
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_003", message="Bạn không có quyền phê duyệt kê khai này"
        ))
    
    # Kiểm tra trạng thái
    if ke_khai.trang_thai != TrangThaiKeKhaiLD.CHO_PHE_DUYET.value:
        raise HTTPException(status_code=400, detail=error_response(
            code="BIZ_001", message=f"Không thể phê duyệt ở trạng thái {ke_khai.trang_thai}"
        ))
    
    # Xử lý theo action
    if payload.action == "APPROVE":
        ke_khai.trang_thai = TrangThaiKeKhaiLD.DA_PHE_DUYET.value
        ke_khai.so_loi_chat_luong = payload.so_loi_chat_luong or 0
        ke_khai.so_loi_tien_do = payload.so_loi_tien_do or 0
        ke_khai.y_kien_lanh_dao = payload.y_kien
        message = "Phê duyệt thành công"
    else:  # REJECT
        ke_khai.trang_thai = TrangThaiKeKhaiLD.TU_CHOI.value
        ke_khai.y_kien_lanh_dao = payload.y_kien
        message = "Đã từ chối, yêu cầu kê khai lại"
    
    await db.flush()
    
    # FIX v2.6.1: Refresh đầy đủ object (bao gồm cả cong_chuc cho response)
    await refresh_ke_khai_full(db, ke_khai, include_cong_chuc=True)
    
    return success_response(data=build_ke_khai_response(ke_khai, include_cong_chuc=True), message=message)


# =============================================================================
# TRẢ LẠI KÊ KHAI LÃNH ĐẠO ĐÃ PHÊ DUYỆT
# =============================================================================

@router.post("/{ke_khai_id}/tra-lai")
async def tra_lai_ke_khai_lanh_dao(
    db: DatabaseDep, current_user: ActiveUserDep,
    ke_khai_id: UUID, payload: TraLaiKeKhaiLDRequest,
) -> dict:
    """
    Trả lại kê khai lãnh đạo đã phê duyệt về trạng thái NHAP.
    Quyền: Người đã phê duyệt hoặc CCT. QLDV không có quyền.
    """
    if is_qldv(current_user):
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_003", message="QLDV không có quyền trả lại kê khai lãnh đạo"
        ))

    stmt = (
        select(KeKhaiLanhDao)
        .options(
            selectinload(KeKhaiLanhDao.cong_chuc),
            selectinload(KeKhaiLanhDao.nguoi_phe_duyet)
        )
        .where(
            KeKhaiLanhDao.id == ke_khai_id,
            KeKhaiLanhDao.is_deleted == False,
        )
    )
    ke_khai = (await db.execute(stmt)).scalar_one_or_none()

    if not ke_khai:
        raise HTTPException(status_code=404, detail=error_response(
            code="NOT_FOUND", message="Không tìm thấy kê khai"
        ))

    if ke_khai.trang_thai != TrangThaiKeKhaiLD.DA_PHE_DUYET.value:
        raise HTTPException(status_code=400, detail=error_response(
            code="INVALID_STATE",
            message=f"Chỉ trả lại được kê khai ở trạng thái ĐÃ PHÊ DUYỆT (hiện tại: {ke_khai.trang_thai})"
        ))

    is_cct = current_user.vai_tro and current_user.vai_tro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG
    if ke_khai.nguoi_phe_duyet_id != current_user.id and not is_cct:
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_003", message="Bạn không phải người đã phê duyệt kê khai này"
        ))

    # Trả lại
    ke_khai.trang_thai = TrangThaiKeKhaiLD.NHAP.value
    ke_khai.y_kien_lanh_dao = f"[TRẢ LẠI] {payload.ly_do}"
    ke_khai.so_loi_chat_luong = 0
    ke_khai.so_loi_tien_do = 0

    await db.flush()
    await refresh_ke_khai_full(db, ke_khai, include_cong_chuc=True)

    return success_response(
        data=build_ke_khai_response(ke_khai, include_cong_chuc=True),
        message="Đã trả lại kê khai thành công. Lãnh đạo có thể sửa và gửi lại."
    )


@router.get(
    "/lich-su",
    summary="Lấy lịch sử phê duyệt kê khai lãnh đạo",
)
async def get_lich_su_ke_khai_lanh_dao(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    trang_thai: Optional[str] = Query(default=None),
    thang: Optional[int] = Query(default=None, ge=1, le=12),
    nam: Optional[int] = Query(default=None, ge=2025),
) -> dict:
    stmt = (
        select(KeKhaiLanhDao)
        .options(selectinload(KeKhaiLanhDao.cong_chuc).selectinload(CongChuc.don_vi))
        .where(KeKhaiLanhDao.is_deleted == False)
    )
    
    if trang_thai == "DA_PHE_DUYET":
        stmt = stmt.where(KeKhaiLanhDao.trang_thai == TrangThaiKeKhaiLD.DA_PHE_DUYET.value)
    elif trang_thai == "TU_CHOI":
        stmt = stmt.where(KeKhaiLanhDao.trang_thai == TrangThaiKeKhaiLD.TU_CHOI.value)
    else:
        # FIX: So sánh với .value (string) thay vì enum object
        stmt = stmt.where(KeKhaiLanhDao.trang_thai.in_([
            TrangThaiKeKhaiLD.DA_PHE_DUYET.value, 
            TrangThaiKeKhaiLD.TU_CHOI.value
        ]))
    
    is_cct = current_user.vai_tro and current_user.vai_tro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG
    if not is_cct:
        stmt = stmt.where(KeKhaiLanhDao.nguoi_phe_duyet_id == current_user.id)
    
    if thang:
        stmt = stmt.where(KeKhaiLanhDao.thang == thang)
    if nam:
        stmt = stmt.where(KeKhaiLanhDao.nam == nam)
    
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    stmt = stmt.order_by(KeKhaiLanhDao.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(stmt)
    kk_list = result.scalars().all()
    
    data = [build_ke_khai_response(kk, include_cong_chuc=True) for kk in kk_list]
    
    return {
        "success": True,
        "data": data,
        "pagination": Pagination.create(page=page, page_size=page_size, total_items=total).model_dump(),
    }


# =============================================================================
# GET KE KHAI LANH DAO THEO CONG CHUC (Lãnh đạo cấp trên xem)
# =============================================================================

@router.get("/cong-chuc/{cong_chuc_id}")
async def get_ke_khai_ld_cong_chuc(
    cong_chuc_id: UUID,
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: Optional[int] = Query(None, ge=1, le=12),
    nam: Optional[int] = Query(None, ge=2025),
) -> dict:
    """
    Xem kê khai công việc lãnh đạo của một CC cụ thể.
    Dùng trong modal Chi tiết CC của Báo cáo xếp loại.

    Quyền: Lãnh đạo cấp trên hoặc Admin hoặc QLDV (cùng đơn vị).
    """
    # Kiểm tra quyền
    is_admin = getattr(current_user.vai_tro, 'is_system_admin', False) if current_user.vai_tro else False
    cap_bac = current_user.vai_tro.cap_bac if current_user.vai_tro else None
    is_cct = cap_bac in [CapBacVaiTro.CHI_CUC_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG]
    is_tdv = cap_bac in [CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI]
    is_quan_ly_dv = is_qldv(current_user)

    if not (is_admin or is_cct or is_tdv or is_quan_ly_dv):
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_001", message="Không có quyền xem kê khai của lãnh đạo khác"
        ))
    
    # Query
    stmt = (
        select(KeKhaiLanhDao)
        .options(
            selectinload(KeKhaiLanhDao.cong_chuc),
            selectinload(KeKhaiLanhDao.nguoi_phe_duyet),
        )
        .where(
            KeKhaiLanhDao.cong_chuc_id == cong_chuc_id,
            KeKhaiLanhDao.is_deleted == False,
        )
    )
    if thang:
        stmt = stmt.where(KeKhaiLanhDao.thang == thang)
    if nam:
        stmt = stmt.where(KeKhaiLanhDao.nam == nam)
    
    stmt = stmt.order_by(KeKhaiLanhDao.created_at.desc())
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    data = [build_ke_khai_response(kk, include_cong_chuc=True) for kk in items]
    
    return success_response(data=data)