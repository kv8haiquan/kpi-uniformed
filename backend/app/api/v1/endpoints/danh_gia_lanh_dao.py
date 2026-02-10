"""
app/api/v1/endpoints/danh_gia_lanh_dao.py
=========================================
API Endpoints cho Đánh giá d, đ, e của Lãnh đạo.

Các chỉ số:
- d: Kết quả đơn vị (100% hoặc 50%)
- đ: Tổ chức triển khai (100% hoặc 50%)
- e: Đoàn kết nội bộ (100% hoặc 50%)

Phiên bản: 2.5.9 (31/01/2026)
Fix:
- v2.5.8: Thêm await db.refresh() sau flush/commit
- v2.5.9: Fix endpoint /dde/lich-su - sai model DanhGiaLanhDao → DanhGiaDDE
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api.deps import DatabaseDep, ActiveUserDep
from app.models.leader_kpi import DanhGiaDDE, TrangThaiDDE
from app.models.user_org import CongChuc, VaiTro, CapBacVaiTro
from app.schemas.common import success_response, error_response, Pagination
from app.schemas.leader_kpi import DanhGiaDDECreate, GuiDuyetDDERequest, PheDuyetDDERequest

from pydantic import BaseModel, Field


class TraLaiDDERequest(BaseModel):
    """Yêu cầu trả lại đánh giá d,đ,e đã phê duyệt."""
    ly_do: str = Field(..., min_length=1, max_length=500, description="Lý do trả lại (bắt buộc)")


router = APIRouter()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def check_is_lanh_dao(user: CongChuc) -> bool:
    """Kiểm tra user có phải là Lãnh đạo không."""
    if user.is_lanh_dao:
        return True
    if user.vai_tro and user.vai_tro.cap_bac in [
        CapBacVaiTro.PHO_DON_VI, CapBacVaiTro.TRUONG_DON_VI,
        CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG,
    ]:
        return True
    return False


async def get_nguoi_phe_duyet_dde(db, current_user: CongChuc) -> tuple[List[CongChuc], str]:
    """Xác định người phê duyệt cho đánh giá d, đ, e."""
    approvers, ghi_chu = [], ""
    
    if not current_user.vai_tro:
        return [], "Không có vai trò"
    
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


def build_dde_response(dde: DanhGiaDDE) -> dict:
    """Build response dict từ model."""
    d_final = dde.d_phe_duyet if dde.d_phe_duyet is not None else dde.d_ket_qua_don_vi
    dd_final = dde.dd_phe_duyet if dde.dd_phe_duyet is not None else dde.dd_to_chuc_trien_khai
    e_final = dde.e_phe_duyet if dde.e_phe_duyet is not None else dde.e_doan_ket_noi_bo
    
    return {
        "id": dde.id, "cong_chuc_id": dde.cong_chuc_id, "thang": dde.thang, "nam": dde.nam,
        "d_ket_qua_don_vi": dde.d_ket_qua_don_vi, "d_ghi_chu": dde.d_ghi_chu,
        "dd_to_chuc_trien_khai": dde.dd_to_chuc_trien_khai, "dd_ghi_chu": dde.dd_ghi_chu,
        "e_doan_ket_noi_bo": dde.e_doan_ket_noi_bo, "e_ghi_chu": dde.e_ghi_chu,
        "trang_thai": dde.trang_thai, "nguoi_phe_duyet_id": dde.nguoi_phe_duyet_id,
        "y_kien_phe_duyet": dde.y_kien_phe_duyet, "ngay_phe_duyet": dde.ngay_phe_duyet,
        "d_phe_duyet": dde.d_phe_duyet, "dd_phe_duyet": dde.dd_phe_duyet, "e_phe_duyet": dde.e_phe_duyet,
        "d_final": d_final, "dd_final": dd_final, "e_final": e_final,
        "created_at": dde.created_at, "updated_at": dde.updated_at,
    }


# =============================================================================
# GET - Danh sách người phê duyệt (ĐẶT TRƯỚC các route có path param)
# =============================================================================

@router.get("/dde/nguoi-phe-duyet")
async def get_nguoi_phe_duyet_dde_api(db: DatabaseDep, current_user: ActiveUserDep) -> dict:
    """Lấy danh sách người phê duyệt cho đánh giá d, đ, e."""
    if not check_is_lanh_dao(current_user):
        raise HTTPException(status_code=403, detail=error_response(code="PERM_003", message="Chỉ Lãnh đạo"))
    
    approvers, ghi_chu = await get_nguoi_phe_duyet_dde(db, current_user)
    
    # Response format ĐÚNG theo yêu cầu Frontend
    data = {
        "danh_sach": [
            {
                "id": a.id, 
                "ma_cc": a.ma_cc, 
                "ho_ten": a.ho_ten, 
                "chuc_vu": a.chuc_vu,
                "vai_tro": {
                    "ma_vai_tro": a.vai_tro.ma_vai_tro, 
                    "ten_vai_tro": a.vai_tro.ten_vai_tro
                } if a.vai_tro else None,
                "don_vi": {
                    "id": a.don_vi.id, 
                    "ten_don_vi": a.don_vi.ten_don_vi
                } if a.don_vi else None
            }
            for a in approvers
        ],
        "ghi_chu": ghi_chu
    }
    
    return success_response(data=data, message="Lấy danh sách người phê duyệt thành công")


# =============================================================================
# GET - Danh sách chờ phê duyệt (cho Lãnh đạo cấp trên)
# =============================================================================

@router.get("/dde/cho-phe-duyet")
async def get_dde_cho_phe_duyet(
    db: DatabaseDep, current_user: ActiveUserDep,
    thang: Optional[int] = Query(default=None, ge=1, le=12),
    nam: Optional[int] = Query(default=None, ge=2025),
) -> dict:
    """Lấy danh sách đánh giá d, đ, e chờ phê duyệt."""
    if not check_is_lanh_dao(current_user):
        raise HTTPException(status_code=403, detail=error_response(code="PERM_003", message="Chỉ Lãnh đạo"))
    
    stmt = (
        select(DanhGiaDDE)
        .options(selectinload(DanhGiaDDE.cong_chuc))
        .where(
            DanhGiaDDE.nguoi_phe_duyet_id == current_user.id,
            DanhGiaDDE.trang_thai == TrangThaiDDE.CHO_PHE_DUYET.value,
        )
    )
    
    if thang: stmt = stmt.where(DanhGiaDDE.thang == thang)
    if nam: stmt = stmt.where(DanhGiaDDE.nam == nam)
    
    dde_list = (await db.execute(stmt)).scalars().all()
    
    data = []
    for dde in dde_list:
        item = build_dde_response(dde)
        if dde.cong_chuc:
            item["cong_chuc"] = {
                "id": dde.cong_chuc.id, "ma_cc": dde.cong_chuc.ma_cc,
                "ho_ten": dde.cong_chuc.ho_ten, "chuc_vu": dde.cong_chuc.chuc_vu,
            }
        data.append(item)
    
    return success_response(data=data, message=f"Có {len(data)} đánh giá chờ phê duyệt")


# =============================================================================
# GET - Lấy đánh giá d, đ, e của tháng
# =============================================================================

@router.get("/dde/thang/{thang}/nam/{nam}")
async def get_danh_gia_dde(
    db: DatabaseDep, current_user: ActiveUserDep,
    thang: int, nam: int,
) -> dict:
    """Lấy đánh giá d, đ, e của tháng."""
    if not check_is_lanh_dao(current_user):
        raise HTTPException(status_code=403, detail=error_response(code="PERM_003", message="Chỉ Lãnh đạo"))
    
    if thang < 1 or thang > 12:
        raise HTTPException(status_code=400, detail=error_response(code="VAL_003", message="Tháng phải từ 1-12"))
    
    stmt = select(DanhGiaDDE).where(
        DanhGiaDDE.cong_chuc_id == current_user.id,
        DanhGiaDDE.thang == thang, DanhGiaDDE.nam == nam,
    )
    dde = (await db.execute(stmt)).scalar_one_or_none()
    
    if not dde:
        # Trả về null nếu chưa có đánh giá
        return success_response(data=None, message="Chưa có đánh giá d, đ, e cho tháng này")
    
    return success_response(data=build_dde_response(dde), message="Lấy đánh giá thành công")


# =============================================================================
# POST - Tạo/Cập nhật đánh giá d, đ, e
# =============================================================================

@router.post("/dde")
async def create_or_update_dde(
    db: DatabaseDep, current_user: ActiveUserDep, payload: DanhGiaDDECreate,
) -> dict:
    """
    Tạo hoặc cập nhật đánh giá d, đ, e.
    
    - Nếu chưa có record cho tháng/năm → INSERT
    - Nếu đã có → UPDATE (chỉ khi trạng thái = NHAP hoặc không có)
    """
    if not check_is_lanh_dao(current_user):
        raise HTTPException(status_code=403, detail=error_response(code="PERM_003", message="Chỉ Lãnh đạo"))
    
    # Kiểm tra đã có chưa
    stmt = select(DanhGiaDDE).where(
        DanhGiaDDE.cong_chuc_id == current_user.id,
        DanhGiaDDE.thang == payload.thang, DanhGiaDDE.nam == payload.nam,
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    
    # Convert boolean → int (100 hoặc 50)
    db_values = payload.to_db_values()
    
    if existing:
        # Update - chỉ khi đang ở trạng thái NHAP
        if existing.trang_thai not in [TrangThaiDDE.NHAP.value, None]:
            raise HTTPException(status_code=400, detail=error_response(
                code="BIZ_001", message=f"Không thể sửa ở trạng thái {existing.trang_thai}"
            ))
        
        existing.d_ket_qua_don_vi = db_values["d_ket_qua_don_vi"]
        existing.d_ghi_chu = db_values["d_ghi_chu"]
        existing.dd_to_chuc_trien_khai = db_values["dd_to_chuc_trien_khai"]
        existing.dd_ghi_chu = db_values["dd_ghi_chu"]
        existing.e_doan_ket_noi_bo = db_values["e_doan_ket_noi_bo"]
        existing.e_ghi_chu = db_values["e_ghi_chu"]
        
        await db.flush()
        await db.refresh(existing)  # QUAN TRỌNG: refresh sau flush
        return success_response(data=build_dde_response(existing), message="Cập nhật đánh giá thành công")
    else:
        # Insert
        dde = DanhGiaDDE(
            cong_chuc_id=current_user.id,
            thang=payload.thang, nam=payload.nam,
            d_ket_qua_don_vi=db_values["d_ket_qua_don_vi"], d_ghi_chu=db_values["d_ghi_chu"],
            dd_to_chuc_trien_khai=db_values["dd_to_chuc_trien_khai"], dd_ghi_chu=db_values["dd_ghi_chu"],
            e_doan_ket_noi_bo=db_values["e_doan_ket_noi_bo"], e_ghi_chu=db_values["e_ghi_chu"],
            trang_thai=TrangThaiDDE.NHAP.value,
        )
        db.add(dde)
        await db.flush()
        await db.refresh(dde)  # QUAN TRỌNG: refresh sau flush
        return success_response(data=build_dde_response(dde), message="Tạo đánh giá thành công")


# =============================================================================
# POST - Gửi phê duyệt đánh giá d, đ, e
# =============================================================================

@router.post("/dde/thang/{thang}/nam/{nam}/gui-duyet")
async def gui_duyet_dde(
    db: DatabaseDep, current_user: ActiveUserDep,
    thang: int, nam: int, payload: GuiDuyetDDERequest,
) -> dict:
    """Gửi đánh giá d, đ, e để phê duyệt."""
    if not check_is_lanh_dao(current_user):
        raise HTTPException(status_code=403, detail=error_response(code="PERM_003", message="Chỉ Lãnh đạo"))
    
    stmt = select(DanhGiaDDE).where(
        DanhGiaDDE.cong_chuc_id == current_user.id,
        DanhGiaDDE.thang == thang, DanhGiaDDE.nam == nam,
    )
    dde = (await db.execute(stmt)).scalar_one_or_none()
    
    if not dde:
        raise HTTPException(status_code=404, detail=error_response(code="NOT_FOUND", message="Chưa có đánh giá để gửi duyệt"))
    
    if dde.trang_thai not in [TrangThaiDDE.NHAP.value, None]:
        raise HTTPException(status_code=400, detail=error_response(
            code="BIZ_001", message=f"Không thể gửi duyệt ở trạng thái {dde.trang_thai}"
        ))
    
    # Validate người phê duyệt
    approvers, _ = await get_nguoi_phe_duyet_dde(db, current_user)
    if payload.nguoi_phe_duyet_id not in [a.id for a in approvers]:
        raise HTTPException(status_code=400, detail=error_response(code="VAL_004", message="Người phê duyệt không hợp lệ"))
    
    dde.nguoi_phe_duyet_id = payload.nguoi_phe_duyet_id
    dde.trang_thai = TrangThaiDDE.CHO_PHE_DUYET.value
    
    await db.flush()
    await db.refresh(dde)  # QUAN TRỌNG
    return success_response(data=build_dde_response(dde), message="Gửi phê duyệt thành công")


# =============================================================================
# POST - Phê duyệt đánh giá d, đ, e
# =============================================================================

@router.post("/dde/{dde_id}/phe-duyet")
async def phe_duyet_dde(
    db: DatabaseDep, current_user: ActiveUserDep,
    dde_id: UUID, payload: PheDuyetDDERequest,
) -> dict:
    """Phê duyệt hoặc từ chối đánh giá d, đ, e."""
    stmt = select(DanhGiaDDE).where(DanhGiaDDE.id == dde_id)
    dde = (await db.execute(stmt)).scalar_one_or_none()
    
    if not dde:
        raise HTTPException(status_code=404, detail=error_response(code="NOT_FOUND", message="Không tìm thấy"))
    
    # Kiểm tra quyền phê duyệt
    is_cct = current_user.vai_tro and current_user.vai_tro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG
    if dde.nguoi_phe_duyet_id != current_user.id and not is_cct:
        raise HTTPException(status_code=403, detail=error_response(code="PERM_003", message="Không có quyền phê duyệt"))
    
    if dde.trang_thai != TrangThaiDDE.CHO_PHE_DUYET.value:
        raise HTTPException(status_code=400, detail=error_response(
            code="BIZ_001", message=f"Không thể phê duyệt ở trạng thái {dde.trang_thai}"
        ))
    
    now = datetime.utcnow()
    
    if payload.action == "APPROVE":
        dde.trang_thai = TrangThaiDDE.DA_PHE_DUYET.value
        dde.ngay_phe_duyet = now
        dde.y_kien_phe_duyet = payload.y_kien
        
        # Lưu giá trị điều chỉnh (nếu có)
        if payload.d_phe_duyet is not None: dde.d_phe_duyet = payload.d_phe_duyet
        if payload.dd_phe_duyet is not None: dde.dd_phe_duyet = payload.dd_phe_duyet
        if payload.e_phe_duyet is not None: dde.e_phe_duyet = payload.e_phe_duyet
        
        message = "Phê duyệt thành công"
    else:
        # REJECT - đưa về NHAP để sửa lại
        dde.trang_thai = TrangThaiDDE.NHAP.value
        dde.y_kien_phe_duyet = payload.y_kien
        message = "Đã từ chối, yêu cầu đánh giá lại"
    
    await db.flush()
    await db.refresh(dde)  # QUAN TRỌNG
    return success_response(data=build_dde_response(dde), message=message)


# =============================================================================
# POST - Trả lại đánh giá d, đ, e đã phê duyệt (MỚI v3.0.0)
# =============================================================================

@router.post("/dde/{dde_id}/tra-lai")
async def tra_lai_dde(
    db: DatabaseDep, current_user: ActiveUserDep,
    dde_id: UUID, payload: TraLaiDDERequest,
) -> dict:
    """Trả lại đánh giá d, đ, e đã phê duyệt về trạng thái NHAP."""
    stmt = select(DanhGiaDDE).where(DanhGiaDDE.id == dde_id)
    dde = (await db.execute(stmt)).scalar_one_or_none()
    
    if not dde:
        raise HTTPException(status_code=404, detail=error_response(code="NOT_FOUND", message="Không tìm thấy"))
    
    if dde.trang_thai != TrangThaiDDE.DA_PHE_DUYET.value:
        raise HTTPException(status_code=400, detail=error_response(
            code="INVALID_STATE", message=f"Chỉ trả lại được ở trạng thái DA_PHE_DUYET (hiện tại: {dde.trang_thai})"
        ))
    
    is_cct = current_user.vai_tro and current_user.vai_tro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG
    is_admin = getattr(current_user.vai_tro, 'is_system_admin', False) if current_user.vai_tro else False
    if dde.nguoi_phe_duyet_id != current_user.id and not is_cct and not is_admin:
        raise HTTPException(status_code=403, detail=error_response(code="PERM_003", message="Không có quyền trả lại"))
    
    dde.trang_thai = TrangThaiDDE.NHAP.value
    dde.y_kien_phe_duyet = f"[TRẢ LẠI] {payload.ly_do}"
    dde.d_phe_duyet = None
    dde.dd_phe_duyet = None
    dde.e_phe_duyet = None
    dde.ngay_phe_duyet = None
    
    await db.flush()
    await db.refresh(dde)
    
    return success_response(data=build_dde_response(dde), message="Đã trả lại đánh giá d,đ,e")


@router.get(
    "/dde/lich-su",
    summary="Lấy lịch sử phê duyệt đánh giá d,đ,e",
)
async def get_lich_su_danh_gia_dde(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    trang_thai: Optional[str] = Query(default=None),
    thang: Optional[int] = Query(default=None, ge=1, le=12),
    nam: Optional[int] = Query(default=None, ge=2025),
) -> dict:
    """
    Lấy lịch sử đánh giá d,đ,e đã phê duyệt.
    
    FIX v2.5.9 (31/01/2026):
    - Sửa sai tên model: DanhGiaLanhDao → DanhGiaDDE
    - Sửa sai tên enum: TrangThaiDanhGiaLD → TrangThaiDDE
    - Bỏ filter is_deleted (DanhGiaDDE không có field này)
    """
    stmt = (
        select(DanhGiaDDE)
        .options(selectinload(DanhGiaDDE.cong_chuc))
    )
    
    # Filter trạng thái - so sánh với .value (string)
    if trang_thai == "DA_PHE_DUYET":
        stmt = stmt.where(DanhGiaDDE.trang_thai == TrangThaiDDE.DA_PHE_DUYET.value)
    else:
        # Mặc định lấy tất cả đã duyệt (DDE không có trạng thái TU_CHOI, chỉ có NHAP khi bị reject)
        stmt = stmt.where(DanhGiaDDE.trang_thai == TrangThaiDDE.DA_PHE_DUYET.value)
    
    # Phân quyền: CCT thấy tất cả, còn lại chỉ thấy những gì mình phê duyệt
    is_cct = current_user.vai_tro and current_user.vai_tro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG
    if not is_cct:
        stmt = stmt.where(DanhGiaDDE.nguoi_phe_duyet_id == current_user.id)
    
    # Filter tháng/năm
    if thang:
        stmt = stmt.where(DanhGiaDDE.thang == thang)
    if nam:
        stmt = stmt.where(DanhGiaDDE.nam == nam)
    
    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0
    
    # Pagination và order
    stmt = stmt.order_by(DanhGiaDDE.ngay_phe_duyet.desc()).offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(stmt)
    dde_list = result.scalars().all()
    
    # Build response với thông tin cong_chuc
    data = []
    for dde in dde_list:
        item = build_dde_response(dde)
        if dde.cong_chuc:
            item["cong_chuc"] = {
                "id": dde.cong_chuc.id,
                "ma_cc": dde.cong_chuc.ma_cc,
                "ho_ten": dde.cong_chuc.ho_ten,
                "chuc_vu": dde.cong_chuc.chuc_vu,
            }
        data.append(item)
    
    return {
        "success": True,
        "data": data,
        "pagination": Pagination.create(page=page, page_size=page_size, total_items=total).model_dump(),
    }


# =============================================================================
# GET DDE THEO CONG CHUC (Lãnh đạo cấp trên xem)
# =============================================================================

@router.get("/dde/cong-chuc/{cong_chuc_id}/thang/{thang}/nam/{nam}")
async def get_dde_cong_chuc(
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Xem đánh giá d, đ, e của một lãnh đạo cụ thể.
    Dùng trong modal Chi tiết CC của Báo cáo xếp loại.
    
    Quyền: Lãnh đạo cấp trên hoặc Admin.
    """
    # Kiểm tra quyền
    is_admin = getattr(current_user.vai_tro, 'is_system_admin', False) if current_user.vai_tro else False
    cap_bac = current_user.vai_tro.cap_bac if current_user.vai_tro else None
    is_cct = cap_bac in [CapBacVaiTro.CHI_CUC_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG]
    is_tdv = cap_bac in [CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI]
    
    if not (is_admin or is_cct or is_tdv):
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_001", message="Không có quyền xem đánh giá d,đ,e của lãnh đạo khác"
        ))
    
    # Query - LƯU Ý: DanhGiaDDE KHÔNG có is_deleted (kế thừa BaseModel, không phải BaseModelWithSoftDelete)
    stmt = (
        select(DanhGiaDDE)
        .options(
            selectinload(DanhGiaDDE.cong_chuc),
        )
        .where(
            DanhGiaDDE.cong_chuc_id == cong_chuc_id,
            DanhGiaDDE.thang == thang,
            DanhGiaDDE.nam == nam,
        )
    )
    result = await db.execute(stmt)
    dde = result.scalar_one_or_none()
    
    if not dde:
        return success_response(data=None, message="Chưa có đánh giá d,đ,e cho tháng này")
    
    return success_response(data=build_dde_response(dde))