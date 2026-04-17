"""
app/api/v1/endpoints/phieu_danh_gia_quy.py
===========================================
API Endpoints cho Phiếu theo dõi, đánh giá cá nhân theo QUÝ (Mẫu 01A/01B).

Workflow 1 cấp:
    NHAP ──(CC gửi)──► CHO_PHE_DUYET ──(duyệt)──► DA_PHE_DUYET
                                    └──(từ chối + lý do)──► BI_TU_CHOI ──(CC sửa)──► NHAP

Phân công duyệt:
    - CONG_CHUC, PHO_DON_VI              → TRUONG_DON_VI cùng đơn vị
    - TRUONG_DON_VI, PHO_CHI_CUC_TRUONG  → CHI_CUC_TRUONG
    - CHI_CUC_TRUONG: không dùng phiếu này

Endpoints:
    POST   /                      — upsert phiếu nháp (CC)
    GET    /cua-toi               — CC xem phiếu của mình
    POST   /{id}/gui-duyet        — CC gửi duyệt
    GET    /cho-duyet             — TDV/CCT danh sách phiếu chờ duyệt
    POST   /{id}/phe-duyet        — TDV/CCT chấp nhận + nhập mục 6
    POST   /{id}/tu-choi          — TDV/CCT từ chối + lý do

Phiên bản: 1.0.0 (17/04/2026)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import selectinload

from app.api.deps import ActiveUserDep, DatabaseDep
from app.models.phieu_danh_gia import PhieuDanhGiaQuy, TrangThaiPhieuDanhGia
from app.models.user_org import CapBacVaiTro, CongChuc, VaiTro
from app.schemas.common import error_response, success_response
from app.schemas.phieu_danh_gia import (
    NguoiKyResponse,
    PheDuyetPhieuRequest,
    PhieuChoPheDuyetItem,
    PhieuDanhGiaQuyResponse,
    TuChoiPhieuRequest,
    UpsertPhieuQuyRequest,
)

router = APIRouter()


# =============================================================================
# HELPERS
# =============================================================================

def _cap_bac(user: CongChuc) -> Optional[CapBacVaiTro]:
    return user.vai_tro.cap_bac if user.vai_tro else None


def _co_phieu(user: CongChuc) -> bool:
    """CC có cần phiếu đánh giá quý không? CCT thì KHÔNG."""
    cb = _cap_bac(user)
    return cb != CapBacVaiTro.CHI_CUC_TRUONG


async def _tim_nguoi_duyet(
    db, cong_chuc: CongChuc
) -> Optional[CongChuc]:
    """
    Tự động xác định người duyệt phiếu của `cong_chuc` theo quy tắc:
      - CONG_CHUC, PHO_DON_VI             → TRUONG_DON_VI cùng đơn vị
      - TRUONG_DON_VI, PHO_CHI_CUC_TRUONG → CHI_CUC_TRUONG

    Trả None nếu không tìm được (đơn vị chưa có TDV, hoặc chi cục chưa có CCT).
    """
    cb = cong_chuc.vai_tro.cap_bac if cong_chuc.vai_tro else None
    if cb in (CapBacVaiTro.CONG_CHUC, CapBacVaiTro.PHO_DON_VI):
        stmt = (
            select(CongChuc)
            .join(VaiTro, VaiTro.id == CongChuc.vai_tro_id)
            .where(
                CongChuc.don_vi_id == cong_chuc.don_vi_id,
                CongChuc.is_active == True,
                VaiTro.cap_bac == CapBacVaiTro.TRUONG_DON_VI,
            )
            .limit(1)
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    if cb in (CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_CHI_CUC_TRUONG):
        stmt = (
            select(CongChuc)
            .join(VaiTro, VaiTro.id == CongChuc.vai_tro_id)
            .where(
                CongChuc.is_active == True,
                VaiTro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG,
            )
            .limit(1)
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    return None


def _co_quyen_duyet(nguoi_duyet: CongChuc, phieu_chu: CongChuc) -> bool:
    """Kiểm tra `nguoi_duyet` có được phép duyệt phiếu của `phieu_chu` không."""
    cb_chu = phieu_chu.vai_tro.cap_bac if phieu_chu.vai_tro else None
    cb_nguoi = nguoi_duyet.vai_tro.cap_bac if nguoi_duyet.vai_tro else None

    if cb_chu in (CapBacVaiTro.CONG_CHUC, CapBacVaiTro.PHO_DON_VI):
        # Cần TDV cùng đơn vị
        return (
            cb_nguoi == CapBacVaiTro.TRUONG_DON_VI
            and nguoi_duyet.don_vi_id == phieu_chu.don_vi_id
        )
    if cb_chu in (CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_CHI_CUC_TRUONG):
        # Cần CCT
        return cb_nguoi == CapBacVaiTro.CHI_CUC_TRUONG
    # CCT không có phiếu → không ai duyệt
    return False


def _serialize(phieu: PhieuDanhGiaQuy) -> dict:
    """Convert model → dict cho response (để set from_attributes gọn)."""
    return PhieuDanhGiaQuyResponse(
        id=phieu.id,
        cong_chuc_id=phieu.cong_chuc_id,
        cong_chuc=NguoiKyResponse(
            id=phieu.cong_chuc.id,
            ma_cc=phieu.cong_chuc.ma_cc,
            ho_ten=phieu.cong_chuc.ho_ten,
            chuc_vu=phieu.cong_chuc.chuc_vu,
        ) if phieu.cong_chuc else None,
        quy=phieu.quy,
        nam=phieu.nam,
        uu_diem=phieu.uu_diem,
        han_che=phieu.han_che,
        y_kien_lanh_dao=phieu.y_kien_lanh_dao,
        trang_thai=phieu.trang_thai,
        ngay_gui_duyet=phieu.ngay_gui_duyet,
        nguoi_phe_duyet_id=phieu.nguoi_phe_duyet_id,
        nguoi_phe_duyet=NguoiKyResponse(
            id=phieu.nguoi_phe_duyet.id,
            ma_cc=phieu.nguoi_phe_duyet.ma_cc,
            ho_ten=phieu.nguoi_phe_duyet.ho_ten,
            chuc_vu=phieu.nguoi_phe_duyet.chuc_vu,
        ) if phieu.nguoi_phe_duyet else None,
        ngay_phe_duyet=phieu.ngay_phe_duyet,
        ly_do_tu_choi=phieu.ly_do_tu_choi,
        created_at=phieu.created_at,
        updated_at=phieu.updated_at,
    ).model_dump(mode="json")


# =============================================================================
# ENDPOINTS — CC
# =============================================================================

@router.post("/", response_model=dict, status_code=status.HTTP_200_OK)
async def upsert_phieu_nhap(
    payload: UpsertPhieuQuyRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    CC tạo mới hoặc cập nhật phiếu nháp (mục 4, 5).

    Quy tắc:
    - Chỉ upsert khi phiếu chưa tồn tại hoặc đang ở trạng thái NHAP / BI_TU_CHOI.
    - Nếu đã gửi duyệt (CHO_PHE_DUYET / DA_PHE_DUYET) → trả lỗi 400 (không sửa được).
    - CCT không dùng endpoint này (không có phiếu).
    """
    if not _co_phieu(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="PHIEU_001", message="CCT không sử dụng phiếu đánh giá cá nhân"),
        )

    # Tìm phiếu hiện có
    stmt = (
        select(PhieuDanhGiaQuy)
        .where(PhieuDanhGiaQuy.cong_chuc_id == current_user.id)
        .where(PhieuDanhGiaQuy.quy == payload.quy)
        .where(PhieuDanhGiaQuy.nam == payload.nam)
    )
    phieu = (await db.execute(stmt)).scalar_one_or_none()

    if phieu is None:
        phieu = PhieuDanhGiaQuy(
            cong_chuc_id=current_user.id,
            quy=payload.quy,
            nam=payload.nam,
            uu_diem=payload.uu_diem,
            han_che=payload.han_che,
            trang_thai=TrangThaiPhieuDanhGia.NHAP.value,
        )
        db.add(phieu)
        await db.flush()
    else:
        if phieu.trang_thai not in (
            TrangThaiPhieuDanhGia.NHAP.value,
            TrangThaiPhieuDanhGia.BI_TU_CHOI.value,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    code="PHIEU_002",
                    message="Phiếu đang chờ duyệt hoặc đã duyệt — không sửa được. Nếu cần sửa, yêu cầu cấp trên trả lại.",
                ),
            )
        phieu.uu_diem = payload.uu_diem
        phieu.han_che = payload.han_che
        # Nếu trước đó bị từ chối, khi sửa lại quay về NHAP và xóa ly do
        if phieu.trang_thai == TrangThaiPhieuDanhGia.BI_TU_CHOI.value:
            phieu.trang_thai = TrangThaiPhieuDanhGia.NHAP.value
            phieu.ly_do_tu_choi = None

    await db.flush()
    phieu = await _lay_phieu_after_mutate(db, phieu.id)
    return success_response(data=_serialize(phieu), message="Đã lưu phiếu nháp")


@router.get("/cua-toi", response_model=dict)
async def get_phieu_cua_toi(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    quy: int = Query(..., ge=1, le=4),
    nam: int = Query(..., ge=2020, le=2100),
) -> dict:
    """CC xem phiếu của mình cho 1 quý. Nếu chưa có → trả data=null."""
    if not _co_phieu(current_user):
        return success_response(data=None, message="CCT không sử dụng phiếu đánh giá cá nhân")

    stmt = (
        select(PhieuDanhGiaQuy)
        .options(
            selectinload(PhieuDanhGiaQuy.cong_chuc),
            selectinload(PhieuDanhGiaQuy.nguoi_phe_duyet),
        )
        .where(PhieuDanhGiaQuy.cong_chuc_id == current_user.id)
        .where(PhieuDanhGiaQuy.quy == quy)
        .where(PhieuDanhGiaQuy.nam == nam)
    )
    phieu = (await db.execute(stmt)).scalar_one_or_none()
    if phieu is None:
        return success_response(data=None)
    return success_response(data=_serialize(phieu))


@router.post("/{phieu_id}/gui-duyet", response_model=dict)
async def gui_duyet_phieu(
    phieu_id: UUID,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    CC gửi phiếu duyệt.
    Chỉ gửi được khi trạng thái là NHAP hoặc BI_TU_CHOI.
    """
    phieu = await _lay_phieu(db, phieu_id)
    if phieu.cong_chuc_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="PHIEU_003", message="Không phải phiếu của bạn"),
        )
    if phieu.trang_thai not in (
        TrangThaiPhieuDanhGia.NHAP.value,
        TrangThaiPhieuDanhGia.BI_TU_CHOI.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="PHIEU_004",
                message=f"Phiếu đang ở trạng thái {phieu.trang_thai}, không thể gửi duyệt",
            ),
        )

    # Phải có ưu điểm + hạn chế
    if not (phieu.uu_diem or "").strip() and not (phieu.han_che or "").strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="PHIEU_005",
                message="Cần nhập ít nhất Ưu điểm hoặc Hạn chế trước khi gửi duyệt",
            ),
        )

    phieu.trang_thai = TrangThaiPhieuDanhGia.CHO_PHE_DUYET.value
    phieu.ngay_gui_duyet = datetime.utcnow()
    # Reset trạng thái cũ (nếu đã bị từ chối lần trước)
    phieu.ngay_phe_duyet = None
    phieu.ly_do_tu_choi = None
    phieu.nguoi_phe_duyet_id = None

    await db.flush()
    phieu = await _lay_phieu_after_mutate(db, phieu.id)
    return success_response(data=_serialize(phieu), message="Đã gửi duyệt")


# =============================================================================
# ENDPOINTS — TDV / CCT
# =============================================================================

@router.get("/cho-duyet", response_model=dict)
async def list_phieu_cho_duyet(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    quy: Optional[int] = Query(None, ge=1, le=4),
    nam: Optional[int] = Query(None, ge=2020, le=2100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """
    TDV/CCT xem danh sách phiếu đang CHO_PHE_DUYET trong phạm vi mình duyệt.

    - TDV: chỉ thấy phiếu của CC + PDV cùng đơn vị.
    - CCT: thấy tất cả phiếu của TDV + PCCT trên toàn chi cục.
    """
    cb = _cap_bac(current_user)
    if cb == CapBacVaiTro.TRUONG_DON_VI:
        cap_bac_chu_phieu = [CapBacVaiTro.CONG_CHUC, CapBacVaiTro.PHO_DON_VI]
        don_vi_filter = current_user.don_vi_id
    elif cb == CapBacVaiTro.CHI_CUC_TRUONG:
        cap_bac_chu_phieu = [CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_CHI_CUC_TRUONG]
        don_vi_filter = None
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="PHIEU_006", message="Chỉ TDV/CCT mới có danh sách phiếu chờ duyệt"),
        )

    stmt = (
        select(PhieuDanhGiaQuy)
        .options(
            selectinload(PhieuDanhGiaQuy.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(PhieuDanhGiaQuy.cong_chuc).selectinload(CongChuc.vai_tro),
        )
        .join(CongChuc, CongChuc.id == PhieuDanhGiaQuy.cong_chuc_id)
        .join(VaiTro, VaiTro.id == CongChuc.vai_tro_id)
        .where(PhieuDanhGiaQuy.trang_thai == TrangThaiPhieuDanhGia.CHO_PHE_DUYET.value)
        .where(VaiTro.cap_bac.in_(cap_bac_chu_phieu))
    )
    if don_vi_filter is not None:
        stmt = stmt.where(CongChuc.don_vi_id == don_vi_filter)
    if quy is not None:
        stmt = stmt.where(PhieuDanhGiaQuy.quy == quy)
    if nam is not None:
        stmt = stmt.where(PhieuDanhGiaQuy.nam == nam)

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(count_stmt) or 0

    # Page
    stmt = stmt.order_by(PhieuDanhGiaQuy.ngay_gui_duyet.desc().nullslast())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    phieus = (await db.execute(stmt)).scalars().all()

    items = []
    for p in phieus:
        items.append(
            PhieuChoPheDuyetItem(
                id=p.id,
                cong_chuc_id=p.cong_chuc_id,
                ma_cc=p.cong_chuc.ma_cc,
                ho_ten=p.cong_chuc.ho_ten,
                chuc_vu=p.cong_chuc.chuc_vu,
                don_vi_ten=p.cong_chuc.don_vi.ten_don_vi if p.cong_chuc.don_vi else None,
                quy=p.quy,
                nam=p.nam,
                trang_thai=p.trang_thai,
                ngay_gui_duyet=p.ngay_gui_duyet,
                uu_diem=p.uu_diem,
                han_che=p.han_che,
            ).model_dump(mode="json")
        )

    return success_response(
        data={
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": (total + page_size - 1) // page_size if page_size else 0,
            },
        }
    )


@router.post("/{phieu_id}/phe-duyet", response_model=dict)
async def phe_duyet_phieu(
    phieu_id: UUID,
    payload: PheDuyetPhieuRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """TDV/CCT chấp nhận phiếu + nhập ý kiến mục 6."""
    phieu = await _lay_phieu(db, phieu_id)

    if phieu.trang_thai != TrangThaiPhieuDanhGia.CHO_PHE_DUYET.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="PHIEU_007", message="Phiếu không ở trạng thái chờ duyệt"),
        )

    if not _co_quyen_duyet(current_user, phieu.cong_chuc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="PHIEU_008", message="Bạn không có quyền duyệt phiếu này"),
        )

    phieu.y_kien_lanh_dao = payload.y_kien_lanh_dao
    phieu.trang_thai = TrangThaiPhieuDanhGia.DA_PHE_DUYET.value
    phieu.nguoi_phe_duyet_id = current_user.id
    phieu.ngay_phe_duyet = datetime.utcnow()
    phieu.ly_do_tu_choi = None

    await db.flush()
    phieu = await _lay_phieu_after_mutate(db, phieu.id)
    return success_response(data=_serialize(phieu), message="Đã duyệt phiếu")


@router.post("/{phieu_id}/tu-choi", response_model=dict)
async def tu_choi_phieu(
    phieu_id: UUID,
    payload: TuChoiPhieuRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """TDV/CCT từ chối phiếu + bắt buộc lý do. Phiếu → BI_TU_CHOI."""
    phieu = await _lay_phieu(db, phieu_id)

    if phieu.trang_thai != TrangThaiPhieuDanhGia.CHO_PHE_DUYET.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="PHIEU_007", message="Phiếu không ở trạng thái chờ duyệt"),
        )

    if not _co_quyen_duyet(current_user, phieu.cong_chuc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="PHIEU_008", message="Bạn không có quyền từ chối phiếu này"),
        )

    phieu.trang_thai = TrangThaiPhieuDanhGia.BI_TU_CHOI.value
    phieu.nguoi_phe_duyet_id = current_user.id
    phieu.ngay_phe_duyet = datetime.utcnow()
    phieu.ly_do_tu_choi = payload.ly_do_tu_choi

    await db.flush()
    phieu = await _lay_phieu_after_mutate(db, phieu.id)
    return success_response(data=_serialize(phieu), message="Đã từ chối phiếu")


# =============================================================================
# INTERNAL
# =============================================================================

async def _lay_phieu(db, phieu_id: UUID) -> PhieuDanhGiaQuy:
    stmt = (
        select(PhieuDanhGiaQuy)
        .options(
            selectinload(PhieuDanhGiaQuy.cong_chuc).selectinload(CongChuc.vai_tro),
            selectinload(PhieuDanhGiaQuy.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(PhieuDanhGiaQuy.nguoi_phe_duyet),
        )
        .where(PhieuDanhGiaQuy.id == phieu_id)
    )
    phieu = (await db.execute(stmt)).scalar_one_or_none()
    if phieu is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="PHIEU_404", message="Phiếu không tồn tại"),
        )
    return phieu


async def _lay_phieu_after_mutate(db, phieu_id: UUID) -> PhieuDanhGiaQuy:
    """Reload phiếu với quan hệ sau khi thay đổi — tránh lỗi lazy load async.
    Dùng populate_existing=True để force re-populate object từ DB với relationships."""
    stmt = (
        select(PhieuDanhGiaQuy)
        .options(
            selectinload(PhieuDanhGiaQuy.cong_chuc).selectinload(CongChuc.vai_tro),
            selectinload(PhieuDanhGiaQuy.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(PhieuDanhGiaQuy.nguoi_phe_duyet),
        )
        .where(PhieuDanhGiaQuy.id == phieu_id)
        .execution_options(populate_existing=True)
    )
    phieu = (await db.execute(stmt)).scalar_one()
    return phieu
