"""
app/api/v1/endpoints/phieu_danh_gia_thang.py
=============================================
API Endpoints cho Phiếu theo dõi, đánh giá cá nhân theo THÁNG (Mẫu 01A/01B).

Workflow 1 cấp:
    NHAP ──(CC gửi)──► CHO_PHE_DUYET ──(duyệt)──► DA_PHE_DUYET
                                    └──(từ chối + lý do)──► BI_TU_CHOI ──(CC sửa)──► NHAP

Phân công duyệt: giống phiếu quý
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
    POST   /{id}/tra-lai          — TDV/CCT trả lại phiếu đã duyệt
    GET    /kiem-tra-du-dieu-kien — CC pre-check điều kiện gửi

Phiên bản: 1.0.0 (08/05/2026)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import ActiveUserDep, DatabaseDep
from app.models.kpi_assessment import (
    DanhGiaThang,
    TieuChiChungDanhGia,
    TrangThaiTieuChi,
)
from app.models.kpi_submission import KeKhaiCongViec, TrangThaiKeKhai
from app.models.leader_kpi import KeKhaiLanhDao, TrangThaiKeKhaiLD
from app.models.phieu_danh_gia import PhieuDanhGiaThang, TrangThaiPhieuDanhGia
from app.models.user_org import CapBacVaiTro, CongChuc, VaiTro
from app.schemas.common import error_response, success_response
from app.schemas.phieu_danh_gia import (
    KiemTraDuDieuKienThangResponse,
    NguoiKyResponse,
    PheDuyetPhieuRequest,
    PhieuDanhGiaThangResponse,
    PhieuThangChoPheDuyetItem,
    TraLaiPhieuRequest,
    TuChoiPhieuRequest,
    UpsertPhieuThangRequest,
)


router = APIRouter()


# =============================================================================
# HELPERS
# =============================================================================

def _cap_bac(user: CongChuc) -> Optional[CapBacVaiTro]:
    return user.vai_tro.cap_bac if user.vai_tro else None


def _co_phieu(user: CongChuc) -> bool:
    """CC có cần phiếu đánh giá tháng không? CCT thì KHÔNG."""
    return _cap_bac(user) != CapBacVaiTro.CHI_CUC_TRUONG


def _co_quyen_duyet(nguoi_duyet: CongChuc, phieu_chu: CongChuc) -> bool:
    """Kiểm tra `nguoi_duyet` có được phép duyệt phiếu của `phieu_chu` không."""
    cb_chu = phieu_chu.vai_tro.cap_bac if phieu_chu.vai_tro else None
    cb_nguoi = nguoi_duyet.vai_tro.cap_bac if nguoi_duyet.vai_tro else None

    if cb_chu in (CapBacVaiTro.CONG_CHUC, CapBacVaiTro.PHO_DON_VI):
        return (
            cb_nguoi == CapBacVaiTro.TRUONG_DON_VI
            and nguoi_duyet.don_vi_id == phieu_chu.don_vi_id
        )
    if cb_chu in (CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_CHI_CUC_TRUONG):
        return cb_nguoi == CapBacVaiTro.CHI_CUC_TRUONG
    return False


def _serialize(phieu: PhieuDanhGiaThang) -> dict:
    return PhieuDanhGiaThangResponse(
        id=phieu.id,
        cong_chuc_id=phieu.cong_chuc_id,
        cong_chuc=NguoiKyResponse(
            id=phieu.cong_chuc.id,
            ma_cc=phieu.cong_chuc.ma_cc,
            ho_ten=phieu.cong_chuc.ho_ten,
            chuc_vu=phieu.cong_chuc.chuc_vu,
        ) if phieu.cong_chuc else None,
        thang=phieu.thang,
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


async def _lay_phieu(db, phieu_id: UUID) -> PhieuDanhGiaThang:
    stmt = (
        select(PhieuDanhGiaThang)
        .options(
            selectinload(PhieuDanhGiaThang.cong_chuc).selectinload(CongChuc.vai_tro),
            selectinload(PhieuDanhGiaThang.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(PhieuDanhGiaThang.nguoi_phe_duyet),
        )
        .where(PhieuDanhGiaThang.id == phieu_id)
    )
    phieu = (await db.execute(stmt)).scalar_one_or_none()
    if phieu is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="PHIEU_T_404", message="Phiếu không tồn tại"),
        )
    return phieu


async def _lay_phieu_after_mutate(db, phieu_id: UUID) -> PhieuDanhGiaThang:
    stmt = (
        select(PhieuDanhGiaThang)
        .options(
            selectinload(PhieuDanhGiaThang.cong_chuc).selectinload(CongChuc.vai_tro),
            selectinload(PhieuDanhGiaThang.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(PhieuDanhGiaThang.nguoi_phe_duyet),
        )
        .where(PhieuDanhGiaThang.id == phieu_id)
        .execution_options(populate_existing=True)
    )
    return (await db.execute(stmt)).scalar_one()


# =============================================================================
# ENDPOINTS — CC
# =============================================================================

@router.post("/", response_model=dict, status_code=status.HTTP_200_OK)
async def upsert_phieu_nhap(
    payload: UpsertPhieuThangRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """CC tạo mới hoặc cập nhật phiếu nháp tháng (mục 4, 5)."""
    if not _co_phieu(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                code="PHIEU_T_001",
                message="CCT không sử dụng phiếu đánh giá cá nhân",
            ),
        )

    stmt = (
        select(PhieuDanhGiaThang)
        .where(PhieuDanhGiaThang.cong_chuc_id == current_user.id)
        .where(PhieuDanhGiaThang.thang == payload.thang)
        .where(PhieuDanhGiaThang.nam == payload.nam)
    )
    phieu = (await db.execute(stmt)).scalar_one_or_none()

    if phieu is None:
        phieu = PhieuDanhGiaThang(
            cong_chuc_id=current_user.id,
            thang=payload.thang,
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
                    code="PHIEU_T_002",
                    message="Phiếu đang chờ duyệt hoặc đã duyệt — không sửa được. Nếu cần sửa, yêu cầu cấp trên trả lại.",
                ),
            )
        phieu.uu_diem = payload.uu_diem
        phieu.han_che = payload.han_che
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
    thang: int = Query(..., ge=1, le=12),
    nam: int = Query(..., ge=2020, le=2100),
) -> dict:
    """CC xem phiếu của mình cho 1 tháng. Nếu chưa có → trả data=null."""
    if not _co_phieu(current_user):
        return success_response(data=None, message="CCT không sử dụng phiếu đánh giá cá nhân")

    stmt = (
        select(PhieuDanhGiaThang)
        .options(
            selectinload(PhieuDanhGiaThang.cong_chuc),
            selectinload(PhieuDanhGiaThang.nguoi_phe_duyet),
        )
        .where(PhieuDanhGiaThang.cong_chuc_id == current_user.id)
        .where(PhieuDanhGiaThang.thang == thang)
        .where(PhieuDanhGiaThang.nam == nam)
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
    """CC gửi phiếu duyệt. Chỉ gửi được khi NHAP hoặc BI_TU_CHOI."""
    phieu = await _lay_phieu(db, phieu_id)
    if phieu.cong_chuc_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="PHIEU_T_003", message="Không phải phiếu của bạn"),
        )
    if phieu.trang_thai not in (
        TrangThaiPhieuDanhGia.NHAP.value,
        TrangThaiPhieuDanhGia.BI_TU_CHOI.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="PHIEU_T_004",
                message=f"Phiếu đang ở trạng thái {phieu.trang_thai}, không thể gửi duyệt",
            ),
        )
    if not (phieu.uu_diem or "").strip() and not (phieu.han_che or "").strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="PHIEU_T_005",
                message="Cần nhập ít nhất Ưu điểm hoặc Hạn chế trước khi gửi duyệt",
            ),
        )

    phieu.trang_thai = TrangThaiPhieuDanhGia.CHO_PHE_DUYET.value
    phieu.ngay_gui_duyet = datetime.utcnow()
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
    thang: Optional[int] = Query(None, ge=1, le=12),
    nam: Optional[int] = Query(None, ge=2020, le=2100),
    trang_thai: Optional[str] = Query(
        None,
        description=(
            "Lọc theo trạng thái: NHAP | CHO_PHE_DUYET | DA_PHE_DUYET | "
            "BI_TU_CHOI. Bỏ trống → trả về toàn bộ CC trong phạm vi (kèm "
            "placeholder NHAP cho người chưa soạn phiếu)."
        ),
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
) -> dict:
    """TDV/CCT xem danh sách phiếu tháng trong phạm vi mình duyệt."""
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
            detail=error_response(
                code="PHIEU_T_006",
                message="Chỉ TDV/CCT mới có danh sách phiếu chờ duyệt",
            ),
        )

    allowed_trang_thai = {t.value for t in TrangThaiPhieuDanhGia}
    if trang_thai is None:
        trang_thai_filter: Optional[str] = None
    elif trang_thai in allowed_trang_thai:
        trang_thai_filter = trang_thai
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="PHIEU_T_009",
                message=f"Trạng thái không hợp lệ: {trang_thai}",
            ),
        )

    full_listing = (
        trang_thai_filter is None and thang is not None and nam is not None
    )

    if full_listing:
        cc_stmt = (
            select(CongChuc)
            .options(
                selectinload(CongChuc.don_vi),
                selectinload(CongChuc.vai_tro),
            )
            .join(VaiTro, VaiTro.id == CongChuc.vai_tro_id)
            .where(CongChuc.is_active == True)
            .where(VaiTro.cap_bac.in_(cap_bac_chu_phieu))
        )
        if don_vi_filter is not None:
            cc_stmt = cc_stmt.where(CongChuc.don_vi_id == don_vi_filter)
        all_cc = (await db.execute(cc_stmt)).scalars().all()

        if all_cc:
            phieu_stmt = (
                select(PhieuDanhGiaThang)
                .options(selectinload(PhieuDanhGiaThang.nguoi_phe_duyet))
                .where(PhieuDanhGiaThang.thang == thang)
                .where(PhieuDanhGiaThang.nam == nam)
                .where(PhieuDanhGiaThang.cong_chuc_id.in_([c.id for c in all_cc]))
            )
            phieus = (await db.execute(phieu_stmt)).scalars().all()
        else:
            phieus = []
        phieu_by_cc = {p.cong_chuc_id: p for p in phieus}

        raw_items: list[tuple[Optional[datetime], PhieuThangChoPheDuyetItem]] = []
        for cc in all_cc:
            p = phieu_by_cc.get(cc.id)
            if p is None:
                item = PhieuThangChoPheDuyetItem(
                    id=None,
                    cong_chuc_id=cc.id,
                    ma_cc=cc.ma_cc,
                    ho_ten=cc.ho_ten,
                    chuc_vu=cc.chuc_vu,
                    don_vi_ten=cc.don_vi.ten_don_vi if cc.don_vi else None,
                    thang=thang,
                    nam=nam,
                    trang_thai=TrangThaiPhieuDanhGia.NHAP.value,
                )
                sort_ts = None
            else:
                item = PhieuThangChoPheDuyetItem(
                    id=p.id,
                    cong_chuc_id=p.cong_chuc_id,
                    ma_cc=cc.ma_cc,
                    ho_ten=cc.ho_ten,
                    chuc_vu=cc.chuc_vu,
                    don_vi_ten=cc.don_vi.ten_don_vi if cc.don_vi else None,
                    thang=p.thang,
                    nam=p.nam,
                    trang_thai=p.trang_thai,
                    ngay_gui_duyet=p.ngay_gui_duyet,
                    ngay_phe_duyet=p.ngay_phe_duyet,
                    uu_diem=p.uu_diem,
                    han_che=p.han_che,
                    y_kien_lanh_dao=p.y_kien_lanh_dao,
                )
                sort_ts = p.ngay_gui_duyet or p.updated_at
            raw_items.append((sort_ts, item))

        group_order = {
            TrangThaiPhieuDanhGia.CHO_PHE_DUYET.value: 0,
            TrangThaiPhieuDanhGia.DA_PHE_DUYET.value: 1,
            TrangThaiPhieuDanhGia.BI_TU_CHOI.value: 2,
            TrangThaiPhieuDanhGia.NHAP.value: 3,
        }
        raw_items.sort(
            key=lambda pair: (
                group_order.get(pair[1].trang_thai, 99),
                -(pair[0].timestamp() if pair[0] else 0),
                pair[1].ho_ten or "",
            )
        )

        total = len(raw_items)
        start = (page - 1) * page_size
        end = start + page_size
        items = [it.model_dump(mode="json") for _, it in raw_items[start:end]]

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

    # Chế độ lọc theo trạng thái cụ thể
    stmt = (
        select(PhieuDanhGiaThang)
        .options(
            selectinload(PhieuDanhGiaThang.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(PhieuDanhGiaThang.cong_chuc).selectinload(CongChuc.vai_tro),
        )
        .join(CongChuc, CongChuc.id == PhieuDanhGiaThang.cong_chuc_id)
        .join(VaiTro, VaiTro.id == CongChuc.vai_tro_id)
        .where(VaiTro.cap_bac.in_(cap_bac_chu_phieu))
    )
    if trang_thai_filter is not None:
        stmt = stmt.where(PhieuDanhGiaThang.trang_thai == trang_thai_filter)
    if don_vi_filter is not None:
        stmt = stmt.where(CongChuc.don_vi_id == don_vi_filter)
    if thang is not None:
        stmt = stmt.where(PhieuDanhGiaThang.thang == thang)
    if nam is not None:
        stmt = stmt.where(PhieuDanhGiaThang.nam == nam)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(count_stmt) or 0

    if trang_thai_filter == TrangThaiPhieuDanhGia.DA_PHE_DUYET.value:
        stmt = stmt.order_by(PhieuDanhGiaThang.ngay_phe_duyet.desc().nullslast())
    else:
        stmt = stmt.order_by(
            PhieuDanhGiaThang.ngay_gui_duyet.desc().nullslast(),
            PhieuDanhGiaThang.updated_at.desc(),
        )
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    phieus = (await db.execute(stmt)).scalars().all()

    items = []
    for p in phieus:
        items.append(
            PhieuThangChoPheDuyetItem(
                id=p.id,
                cong_chuc_id=p.cong_chuc_id,
                ma_cc=p.cong_chuc.ma_cc,
                ho_ten=p.cong_chuc.ho_ten,
                chuc_vu=p.cong_chuc.chuc_vu,
                don_vi_ten=p.cong_chuc.don_vi.ten_don_vi if p.cong_chuc.don_vi else None,
                thang=p.thang,
                nam=p.nam,
                trang_thai=p.trang_thai,
                ngay_gui_duyet=p.ngay_gui_duyet,
                ngay_phe_duyet=p.ngay_phe_duyet,
                uu_diem=p.uu_diem,
                han_che=p.han_che,
                y_kien_lanh_dao=p.y_kien_lanh_dao,
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
            detail=error_response(code="PHIEU_T_007", message="Phiếu không ở trạng thái chờ duyệt"),
        )

    if not _co_quyen_duyet(current_user, phieu.cong_chuc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="PHIEU_T_008", message="Bạn không có quyền duyệt phiếu này"),
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
    """TDV/CCT từ chối phiếu + bắt buộc lý do."""
    phieu = await _lay_phieu(db, phieu_id)

    if phieu.trang_thai != TrangThaiPhieuDanhGia.CHO_PHE_DUYET.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="PHIEU_T_007", message="Phiếu không ở trạng thái chờ duyệt"),
        )

    if not _co_quyen_duyet(current_user, phieu.cong_chuc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="PHIEU_T_008", message="Bạn không có quyền từ chối phiếu này"),
        )

    phieu.trang_thai = TrangThaiPhieuDanhGia.BI_TU_CHOI.value
    phieu.nguoi_phe_duyet_id = current_user.id
    phieu.ngay_phe_duyet = datetime.utcnow()
    phieu.ly_do_tu_choi = payload.ly_do_tu_choi

    await db.flush()
    phieu = await _lay_phieu_after_mutate(db, phieu.id)
    return success_response(data=_serialize(phieu), message="Đã từ chối phiếu")


@router.post("/{phieu_id}/tra-lai", response_model=dict)
async def tra_lai_phieu(
    phieu_id: UUID,
    payload: TraLaiPhieuRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """TDV/CCT trả lại phiếu đã phê duyệt (đảo ngược phê duyệt nhầm)."""
    phieu = await _lay_phieu(db, phieu_id)

    if phieu.trang_thai != TrangThaiPhieuDanhGia.DA_PHE_DUYET.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="PHIEU_T_010",
                message="Chỉ trả lại được phiếu đang ở trạng thái 'Đã phê duyệt'",
            ),
        )

    if not _co_quyen_duyet(current_user, phieu.cong_chuc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                code="PHIEU_T_011",
                message="Bạn không có quyền trả lại phiếu này",
            ),
        )

    phieu.trang_thai = TrangThaiPhieuDanhGia.NHAP.value
    phieu.y_kien_lanh_dao = None
    phieu.ngay_gui_duyet = None
    phieu.nguoi_phe_duyet_id = None
    phieu.ngay_phe_duyet = None
    phieu.ly_do_tu_choi = (payload.ly_do or "").strip() or None

    await db.flush()
    phieu = await _lay_phieu_after_mutate(db, phieu.id)
    return success_response(data=_serialize(phieu), message="Đã trả lại phiếu")


# =============================================================================
# ENDPOINT — CC: KIỂM TRA ĐIỀU KIỆN GỬI DUYỆT
# =============================================================================

@router.get("/kiem-tra-du-dieu-kien", response_model=dict)
async def kiem_tra_du_dieu_kien(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int = Query(..., ge=1, le=12),
    nam: int = Query(..., ge=2020, le=2100),
) -> dict:
    """CC pre-check số CV/TC còn chưa duyệt trong tháng."""
    if not _co_phieu(current_user):
        return success_response(
            data=KiemTraDuDieuKienThangResponse(
                thang=thang, nam=nam, co_van_de=False
            ).model_dump(mode="json"),
            message="CCT không dùng phiếu",
        )

    is_lanh_dao = bool(current_user.is_lanh_dao)

    cv_cc_dang_tam_tinh = [
        TrangThaiKeKhai.NHAP,
        TrangThaiKeKhai.CHO_PHE_DUYET,
    ]
    cv_ld_dang_tam_tinh = [
        TrangThaiKeKhaiLD.NHAP.value,
        TrangThaiKeKhaiLD.CHO_PHE_DUYET.value,
    ]
    tc_dang_tam_tinh = [
        TrangThaiTieuChi.NHAP,
        TrangThaiTieuChi.CHO_PHE_DUYET,
        TrangThaiTieuChi.CHO_CAP2,
    ]

    if is_lanh_dao:
        cv_stmt = (
            select(func.count())
            .select_from(KeKhaiLanhDao)
            .where(KeKhaiLanhDao.cong_chuc_id == current_user.id)
            .where(KeKhaiLanhDao.thang == thang)
            .where(KeKhaiLanhDao.nam == nam)
            .where(KeKhaiLanhDao.is_deleted == False)
            .where(KeKhaiLanhDao.trang_thai.in_(cv_ld_dang_tam_tinh))
        )
    else:
        cv_stmt = (
            select(func.count())
            .select_from(KeKhaiCongViec)
            .where(KeKhaiCongViec.cong_chuc_id == current_user.id)
            .where(KeKhaiCongViec.thang == thang)
            .where(KeKhaiCongViec.nam == nam)
            .where(KeKhaiCongViec.is_deleted == False)
            .where(KeKhaiCongViec.trang_thai.in_(cv_cc_dang_tam_tinh))
        )
    cv_chua = (await db.scalar(cv_stmt)) or 0

    tc_stmt = (
        select(func.count())
        .select_from(TieuChiChungDanhGia)
        .join(DanhGiaThang, DanhGiaThang.id == TieuChiChungDanhGia.danh_gia_thang_id)
        .where(DanhGiaThang.cong_chuc_id == current_user.id)
        .where(DanhGiaThang.thang == thang)
        .where(DanhGiaThang.nam == nam)
        .where(DanhGiaThang.is_deleted == False)
        .where(TieuChiChungDanhGia.trang_thai.in_(tc_dang_tam_tinh))
    )
    tc_chua = (await db.scalar(tc_stmt)) or 0

    resp = KiemTraDuDieuKienThangResponse(
        thang=thang,
        nam=nam,
        co_van_de=(cv_chua > 0 or tc_chua > 0),
        so_cv_chua_duyet=cv_chua,
        so_tc_chua_duyet=tc_chua,
    )
    return success_response(data=resp.model_dump(mode="json"))
