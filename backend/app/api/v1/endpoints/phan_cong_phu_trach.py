"""
app/api/v1/endpoints/phan_cong_phu_trach.py
===========================================
CRUD endpoints cho phân công CCT/PCCT phụ trách đơn vị.

Phục vụ tính KPI lãnh đạo công thức mới (từ tháng 4/2026):
- PCCT = gộp SP các đơn vị mình phụ trách
- CCT  = gộp SP các đơn vị mình trực tiếp phụ trách + các PCCT phụ trách

Versioned theo thời gian: tại 1 thời điểm, 1 đơn vị chỉ thuộc đúng 1 LĐ.

Permission:
- View: ActiveUserDep (mọi user đăng nhập)
- Create/Update/Delete/Kết thúc: chỉ CCT (CHI_CUC_TRUONG) hoặc Super Admin
"""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import (
    ActiveUserDep,
    DatabaseDep,
    require_roles,
)
from app.models.user_org import CapBacVaiTro, CongChuc, DonVi, LoaiDonVi, VaiTro
from app.models.phan_cong_phu_trach import PhanCongPhuTrach
from app.schemas.common import success_response
from app.schemas.phan_cong_phu_trach import (
    PhanCongCreate,
    PhanCongKetThucRequest,
    PhanCongResponse,
    PhanCongUpdate,
)


router = APIRouter()


# =============================================================================
# HELPERS
# =============================================================================

ALLOWED_LEADER_CAP_BAC = {
    CapBacVaiTro.CHI_CUC_TRUONG,
    CapBacVaiTro.PHO_CHI_CUC_TRUONG,
}

# Đơn vị KHÔNG được phép phân công (không có TDV nghiệp vụ KPI)
EXCLUDED_DON_VI_MA = {"LDCC", "DEPT-ADMIN"}


async def _validate_lanh_dao(db: AsyncSession, lanh_dao_id: UUID) -> CongChuc:
    """Kiểm tra lanh_dao_id là CCT hoặc PCCT, đang active."""
    stmt = (
        select(CongChuc)
        .options(selectinload(CongChuc.vai_tro))
        .where(CongChuc.id == lanh_dao_id, CongChuc.is_deleted == False)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {"code": "PCPT_404_LD", "message": "Không tìm thấy lãnh đạo"},
            },
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {"code": "PCPT_400_LD_INACTIVE", "message": "Lãnh đạo đã bị khóa"},
            },
        )
    if not user.vai_tro or user.vai_tro.cap_bac not in ALLOWED_LEADER_CAP_BAC:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "PCPT_400_LD_CAP_BAC",
                    "message": "Chỉ CCT hoặc PCCT mới được phân công phụ trách đơn vị",
                },
            },
        )
    return user


async def _validate_don_vi(db: AsyncSession, don_vi_id: UUID) -> DonVi:
    """Kiểm tra don_vi tồn tại, active và là đơn vị nghiệp vụ (có TDV)."""
    stmt = select(DonVi).where(DonVi.id == don_vi_id, DonVi.is_deleted == False)
    result = await db.execute(stmt)
    dv = result.scalar_one_or_none()
    if not dv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {"code": "PCPT_404_DV", "message": "Không tìm thấy đơn vị"},
            },
        )
    if not dv.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {"code": "PCPT_400_DV_INACTIVE", "message": "Đơn vị đã ngừng hoạt động"},
            },
        )
    if dv.ma_don_vi in EXCLUDED_DON_VI_MA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "PCPT_400_DV_EXCLUDED",
                    "message": f"Đơn vị {dv.ma_don_vi} không thuộc diện phân công phụ trách",
                },
            },
        )
    return dv


async def _check_overlap(
    db: AsyncSession,
    don_vi_id: UUID,
    hieu_luc_tu: date,
    hieu_luc_den: Optional[date],
    exclude_id: Optional[UUID] = None,
) -> Optional[PhanCongPhuTrach]:
    """
    Kiểm tra overlap với phân công khác cho cùng don_vi_id.

    Hai khoảng [a1, a2] và [b1, b2] OVERLAP khi: a1 <= b2 AND b1 <= a2
    Với a2/b2 NULL → coi như +∞ (vẫn còn hiệu lực).
    """
    stmt = (
        select(PhanCongPhuTrach)
        .where(
            PhanCongPhuTrach.don_vi_id == don_vi_id,
            PhanCongPhuTrach.is_deleted == False,
        )
    )
    if exclude_id:
        stmt = stmt.where(PhanCongPhuTrach.id != exclude_id)

    result = await db.execute(stmt)
    rows = result.scalars().all()

    for r in rows:
        # r.hieu_luc_tu .. r.hieu_luc_den (None = +∞)
        # new: hieu_luc_tu .. hieu_luc_den (None = +∞)
        # overlap: r.tu <= new.den AND new.tu <= r.den
        new_den_for_check = hieu_luc_den if hieu_luc_den is not None else date(9999, 12, 31)
        r_den_for_check = r.hieu_luc_den if r.hieu_luc_den is not None else date(9999, 12, 31)

        if r.hieu_luc_tu <= new_den_for_check and hieu_luc_tu <= r_den_for_check:
            return r
    return None


# =============================================================================
# LIST / FILTER
# =============================================================================

@router.get(
    "",
    summary="Danh sách phân công phụ trách",
    description=(
        "Trả về tất cả phân công CCT/PCCT phụ trách đơn vị. "
        "Có thể filter theo lanh_dao_id, don_vi_id, hoặc ngay (chỉ lấy phân công có hiệu lực tại ngày đó)."
    ),
)
async def list_phan_cong(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    lanh_dao_id: Optional[UUID] = Query(default=None),
    don_vi_id: Optional[UUID] = Query(default=None),
    ngay: Optional[date] = Query(default=None, description="Chỉ lấy phân công có hiệu lực tại ngày này"),
    include_deleted: bool = Query(default=False),
):
    stmt = select(PhanCongPhuTrach).options(
        selectinload(PhanCongPhuTrach.lanh_dao),
        selectinload(PhanCongPhuTrach.don_vi),
    )

    if not include_deleted:
        stmt = stmt.where(PhanCongPhuTrach.is_deleted == False)
    if lanh_dao_id:
        stmt = stmt.where(PhanCongPhuTrach.lanh_dao_id == lanh_dao_id)
    if don_vi_id:
        stmt = stmt.where(PhanCongPhuTrach.don_vi_id == don_vi_id)
    if ngay:
        stmt = stmt.where(
            PhanCongPhuTrach.hieu_luc_tu <= ngay,
            or_(
                PhanCongPhuTrach.hieu_luc_den.is_(None),
                PhanCongPhuTrach.hieu_luc_den >= ngay,
            ),
        )

    stmt = stmt.order_by(
        PhanCongPhuTrach.hieu_luc_tu.desc(),
        PhanCongPhuTrach.created_at.desc(),
    )

    result = await db.execute(stmt)
    rows = result.scalars().unique().all()
    data = [PhanCongResponse.model_validate(r).model_dump(mode="json") for r in rows]
    return success_response(data=data)


# =============================================================================
# GET BY ID
# =============================================================================

@router.get(
    "/{pc_id}",
    summary="Xem chi tiết 1 phân công",
)
async def get_phan_cong(
    pc_id: UUID,
    db: DatabaseDep,
    current_user: ActiveUserDep,
):
    stmt = (
        select(PhanCongPhuTrach)
        .options(
            selectinload(PhanCongPhuTrach.lanh_dao),
            selectinload(PhanCongPhuTrach.don_vi),
        )
        .where(PhanCongPhuTrach.id == pc_id)
    )
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {"code": "PCPT_404", "message": "Không tìm thấy phân công"},
            },
        )
    data = PhanCongResponse.model_validate(row).model_dump(mode="json")
    return success_response(data=data)


# =============================================================================
# CREATE (CCT + Admin)
# =============================================================================

@router.post(
    "",
    summary="Tạo phân công mới",
    description="Chỉ CCT (CHI_CUC_TRUONG) hoặc Super Admin được tạo.",
    status_code=status.HTTP_201_CREATED,
)
async def create_phan_cong(
    payload: PhanCongCreate,
    db: DatabaseDep,
    current_user: CongChuc = Depends(require_roles("CCT")),
):
    # Validate LĐ + đơn vị
    await _validate_lanh_dao(db, payload.lanh_dao_id)
    await _validate_don_vi(db, payload.don_vi_id)

    # Check overlap
    overlap = await _check_overlap(
        db,
        payload.don_vi_id,
        payload.hieu_luc_tu,
        payload.hieu_luc_den,
    )
    if overlap:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "error": {
                    "code": "PCPT_409_OVERLAP",
                    "message": (
                        f"Đơn vị này đã có phân công khác trùng thời gian "
                        f"(từ {overlap.hieu_luc_tu} đến {overlap.hieu_luc_den or 'nay'})"
                    ),
                },
            },
        )

    pc = PhanCongPhuTrach(
        lanh_dao_id=payload.lanh_dao_id,
        don_vi_id=payload.don_vi_id,
        hieu_luc_tu=payload.hieu_luc_tu,
        hieu_luc_den=payload.hieu_luc_den,
        ghi_chu=payload.ghi_chu,
    )
    db.add(pc)
    await db.flush()
    await db.refresh(pc, ["lanh_dao", "don_vi"])

    data = PhanCongResponse.model_validate(pc).model_dump(mode="json")
    return success_response(data=data, message="Tạo phân công thành công")


# =============================================================================
# UPDATE (CCT + Admin)
# =============================================================================

@router.put(
    "/{pc_id}",
    summary="Cập nhật phân công (chỉ hieu_luc_den + ghi_chu)",
    description="Chỉ CCT hoặc Super Admin. Không cho đổi LĐ/đơn vị/ngày bắt đầu (tạo bản ghi mới thay thế).",
)
async def update_phan_cong(
    pc_id: UUID,
    payload: PhanCongUpdate,
    db: DatabaseDep,
    current_user: CongChuc = Depends(require_roles("CCT")),
):
    stmt = select(PhanCongPhuTrach).where(PhanCongPhuTrach.id == pc_id)
    result = await db.execute(stmt)
    pc = result.scalar_one_or_none()
    if not pc or pc.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {"code": "PCPT_404", "message": "Không tìm thấy phân công"},
            },
        )

    new_hieu_luc_den = payload.hieu_luc_den if payload.hieu_luc_den is not None else pc.hieu_luc_den
    if new_hieu_luc_den is not None and new_hieu_luc_den < pc.hieu_luc_tu:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "PCPT_400_DATE",
                    "message": "hieu_luc_den phải >= hieu_luc_tu",
                },
            },
        )

    # Nếu thay đổi hieu_luc_den → check overlap lại
    if payload.hieu_luc_den != pc.hieu_luc_den:
        overlap = await _check_overlap(
            db,
            pc.don_vi_id,
            pc.hieu_luc_tu,
            new_hieu_luc_den,
            exclude_id=pc.id,
        )
        if overlap:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "error": {
                        "code": "PCPT_409_OVERLAP",
                        "message": (
                            f"Trùng thời gian với phân công khác (từ {overlap.hieu_luc_tu} "
                            f"đến {overlap.hieu_luc_den or 'nay'})"
                        ),
                    },
                },
            )

    pc.hieu_luc_den = new_hieu_luc_den
    if payload.ghi_chu is not None:
        pc.ghi_chu = payload.ghi_chu

    await db.flush()
    await db.refresh(pc, ["lanh_dao", "don_vi"])

    data = PhanCongResponse.model_validate(pc).model_dump(mode="json")
    return success_response(data=data, message="Cập nhật thành công")


# =============================================================================
# KẾT THÚC PHÂN CÔNG (shortcut)
# =============================================================================

@router.post(
    "/{pc_id}/ket-thuc",
    summary="Kết thúc phân công tại 1 ngày",
)
async def ket_thuc_phan_cong(
    pc_id: UUID,
    payload: PhanCongKetThucRequest,
    db: DatabaseDep,
    current_user: CongChuc = Depends(require_roles("CCT")),
):
    return await update_phan_cong(
        pc_id=pc_id,
        payload=PhanCongUpdate(hieu_luc_den=payload.hieu_luc_den),
        db=db,
        current_user=current_user,
    )


# =============================================================================
# SOFT DELETE
# =============================================================================

@router.delete(
    "/{pc_id}",
    summary="Xóa phân công (soft delete)",
)
async def delete_phan_cong(
    pc_id: UUID,
    db: DatabaseDep,
    current_user: CongChuc = Depends(require_roles("CCT")),
):
    stmt = select(PhanCongPhuTrach).where(PhanCongPhuTrach.id == pc_id)
    result = await db.execute(stmt)
    pc = result.scalar_one_or_none()
    if not pc or pc.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {"code": "PCPT_404", "message": "Không tìm thấy phân công"},
            },
        )
    pc.is_deleted = True
    await db.flush()
    return success_response(data={"id": str(pc_id)}, message="Đã xóa phân công")


# =============================================================================
# DANH SÁCH LĐ KHẢ DỤNG (CCT + PCCT)
# =============================================================================

@router.get(
    "/_meta/lanh-dao-kha-dung",
    summary="Danh sách CCT/PCCT có thể được phân công",
)
async def list_lanh_dao_kha_dung(
    db: DatabaseDep,
    current_user: ActiveUserDep,
):
    stmt = (
        select(CongChuc)
        .join(VaiTro, VaiTro.id == CongChuc.vai_tro_id)
        .where(
            CongChuc.is_deleted == False,
            CongChuc.is_active == True,
            VaiTro.cap_bac.in_(list(ALLOWED_LEADER_CAP_BAC)),
        )
        .options(selectinload(CongChuc.vai_tro))
        .order_by(VaiTro.cap_bac, CongChuc.ho_ten)
    )
    result = await db.execute(stmt)
    rows = result.scalars().unique().all()
    data = [
        {
            "id": str(r.id),
            "ma_cc": r.ma_cc,
            "ho_ten": r.ho_ten,
            "chuc_vu": r.chuc_vu,
            "ma_vai_tro": r.vai_tro.ma_vai_tro if r.vai_tro else None,
            "cap_bac": r.vai_tro.cap_bac.value if r.vai_tro else None,
        }
        for r in rows
    ]
    return success_response(data=data)


# =============================================================================
# DANH SÁCH ĐƠN VỊ KHẢ DỤNG (loại trừ LDCC, DEPT-ADMIN)
# =============================================================================

@router.get(
    "/_meta/don-vi-kha-dung",
    summary="Danh sách đơn vị có thể được phân công phụ trách",
)
async def list_don_vi_kha_dung(
    db: DatabaseDep,
    current_user: ActiveUserDep,
):
    stmt = (
        select(DonVi)
        .where(
            DonVi.is_deleted == False,
            DonVi.is_active == True,
            DonVi.ma_don_vi.notin_(EXCLUDED_DON_VI_MA),
        )
        .order_by(DonVi.thu_tu_hien_thi, DonVi.ma_don_vi)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    data = [
        {
            "id": str(r.id),
            "ma_don_vi": r.ma_don_vi,
            "ten_don_vi": r.ten_don_vi,
            "loai_don_vi": r.loai_don_vi.value,
        }
        for r in rows
    ]
    return success_response(data=data)
