"""
api/endpoints/tai_lieu.py
==========================
Module 3 — Tài liệu họp. 5 endpoints chính + 1 endpoint serve file (gateway).

Spec: §5 HKG_API_SPECS.md (đã cập nhật MVP filesystem + JWT short-lived).
"""

import os
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, Response

from meeting_service.dependencies import (
    DatabaseDep,
    CurrentUserDep,
    require_can_edit_meeting,
    require_can_view_meeting,
)
from meeting_service.services.rate_limit import limiter
from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.schemas.tai_lieu import (
    TaiLieuKhoItem,
    TaiLieuListItem,
    TaiLieuMetadataUpdate,
    TaiLieuResponse,
)
from meeting_service.services.short_lived_token import (
    PURPOSE_DOWNLOAD_DOC,
    PURPOSE_VIEW_DOC,
    issue_token,
    verify_token,
)
from meeting_service.services.preview_service import (
    ensure_pdf_preview,
    is_office_extension,
)
from meeting_service.services.phan_quyen_tai_lieu import (
    MO_TA as MO_TA_PHAN_QUYEN,
    NHAN as NHAN_PHAN_QUYEN,
    PHAN_QUYEN_VALUES,
    duoc_quan_ly_tai_lieu,
    loc_xem_duoc,
    muc_dat_duoc,
    xem_duoc,
)
from meeting_service.services.storage_service import StorageService
from meeting_service.services.tai_lieu_service import TaiLieuService


router = APIRouter(prefix="/tai-lieu", tags=["Tài liệu họp"])
router_cuoc_hop = APIRouter(prefix="/cuoc-hop", tags=["Tài liệu họp"])


def _loi_phan_quyen(hanh_dong: str) -> HTTPException:
    """403 dùng chung cho tài liệu bị hạn chế.

    Cùng một câu chữ cho mọi mức: nói rõ "chỉ lãnh đạo Chi cục" là tiết lộ
    đúng mức hạn chế của tài liệu, mà mức đó tự nó đã là thông tin.
    """
    return HTTPException(
        status_code=403,
        detail={"success": False, "error": {
            "code": "DOC_RESTRICTED",
            "message": f"Tài liệu này hạn chế người xem — bạn không {hanh_dong} "
                       "được. Liên hệ Văn phòng nếu cần."}},
    )


def _kiem_muc_dat_duoc(muc: Optional[str], user) -> None:
    """Chặn đặt mức cao hơn bậc của chính người đặt."""
    if muc is None:
        return
    if muc not in PHAN_QUYEN_VALUES:
        raise HTTPException(
            status_code=422,
            detail={"success": False, "error": {
                "code": "VALIDATION_ERROR",
                "message": f"phan_quyen phải thuộc {PHAN_QUYEN_VALUES}"}},
        )
    if muc not in muc_dat_duoc(user):
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {
                "code": "DOC_LEVEL_TOO_HIGH",
                "message": "Bạn không được đặt mức hạn chế cao hơn quyền xem "
                           "của chính mình — đặt xong sẽ tự mình không mở "
                           "lại được."}},
        )


@router.get("/kho", summary="Duyệt cả kho tài liệu họp (cho Thư viện tài liệu)")
async def kho_tai_lieu(
    db: DatabaseDep,
    user: CurrentUserDep,
    nguon: Optional[str] = Query(
        None, description="HKG | LICH_CONG_TAC. Bỏ trống là cả hai."),
    tim_kiem: Optional[str] = Query(None, alias="tim-kiem"),
    # Phải khai kiểu `date`, không phải `str`: cột `ngay_hop` là DATE và
    # asyncpg không tự ép chuỗi sang ngày — để `str` là câu truy vấn nổ
    # "operator does not exist: date >= character varying".
    tu_ngay: Optional[date] = Query(None, alias="tu-ngay"),
    den_ngay: Optional[date] = Query(None, alias="den-ngay"),
    trang: int = Query(1, ge=1),
    so_dong: int = Query(24, ge=1, le=100, alias="so-dong"),
):
    """Kho tài liệu họp, duyệt như duyệt thư mục Drive.

    Trước màn hình này, tài liệu chỉ mở được khi biết trước nó thuộc cuộc họp
    nào — muốn tìm một văn bản mà quên mất họp hôm nào thì chịu. Đây là chỗ
    duy nhất xem được cả kho.

    Phân quyền giữ nguyên hai tầng đang có, KHÔNG nới:
      1. Cuộc họp — `_can_view_cuoc_hop`. Sự kiện Lịch công tác là lịch công
         khai nội bộ nên cả Chi cục xem được; cuộc họp HKG chỉ người được mời.
      2. Tài liệu — `loc_xem_duoc` (G5.4). Lọc TRƯỚC khi phát token xem, vì
         danh sách này nhúng sẵn `url_xem`.

    Vì luật quyền của tầng 1 phụ thuộc từng cuộc họp, không viết được thành
    một câu SQL — phải duyệt theo lô rồi lọc trong Python. Lấy dư một ít mỗi
    lô để bù phần bị lọc, thay vì phân trang thẳng trên SQL (sẽ ra trang thiếu).
    """
    from sqlalchemy import String, and_, cast, desc, func, or_, select

    from meeting_service.dependencies import _can_view_cuoc_hop
    from meeting_service.models.cuoc_hop import CuocHop as CH
    from meeting_service.models.tai_lieu import TaiLieu

    if nguon and nguon not in ("HKG", "LICH_CONG_TAC"):
        raise HTTPException(422, detail={"success": False, "error": {
            "code": "VALIDATION_ERROR",
            "message": "nguon phải là HKG hoặc LICH_CONG_TAC"}})

    dk = [TaiLieu.is_deleted.is_(False), TaiLieu.cuoc_hop_id.isnot(None),
          CH.is_deleted.is_(False)]
    if nguon:
        dk.append(CH.nguon == nguon)
    if tu_ngay:
        dk.append(CH.ngay_hop >= tu_ngay)
    if den_ngay:
        dk.append(CH.ngay_hop <= den_ngay)
    if tim_kiem:
        tu = f"%{tim_kiem.strip()}%"
        # Tìm cả trên tên file lẫn nội dung cuộc họp và mã lịch: người dùng
        # nhớ "họp giao ban tháng 5" nhiều hơn là nhớ tên file.
        dk.append(or_(TaiLieu.ten_tai_lieu.ilike(tu), CH.tieu_de.ilike(tu),
                      CH.ma_lich.ilike(tu)))

    cau = (select(TaiLieu, CH).join(CH, CH.id == TaiLieu.cuoc_hop_id)
           .where(and_(*dk))
           .order_by(desc(CH.ngay_hop), desc(TaiLieu.created_at)))

    bo_qua = (trang - 1) * so_dong
    can = bo_qua + so_dong
    duoc_xem: list[tuple] = []
    quyen_hop: dict = {}      # nhớ kết quả theo cuộc họp, đỡ hỏi lại
    offset, LO = 0, 200
    het = False

    while len(duoc_xem) < can + 1 and not het:
        rows = (await db.execute(cau.offset(offset).limit(LO))).all()
        if len(rows) < LO:
            het = True
        offset += LO
        for tl, ch in rows:
            if ch.id not in quyen_hop:
                quyen_hop[ch.id] = await _can_view_cuoc_hop(ch, user, db)
            if not quyen_hop[ch.id]:
                continue
            if not xem_duoc(tl.phan_quyen, user,
                            nguoi_tai_len_id=tl.created_by):
                continue
            duoc_xem.append((tl, ch))

    # `+1` ở trên để biết còn trang sau hay không mà không phải đếm cả kho.
    con_nua = len(duoc_xem) > can
    trang_nay = duoc_xem[bo_qua:can]

    out = []
    for tl, ch in trang_nay:
        token = issue_token(
            purpose=PURPOSE_VIEW_DOC, subject=str(tl.id),
            extra_claims={"viewer_id": user.sub}, ttl_seconds=3600,
        )
        item = TaiLieuKhoItem.model_validate({
            **{c: getattr(tl, c) for c in (
                "id", "ten_tai_lieu", "mo_ta", "extension", "file_size",
                "mime_type", "phan_quyen", "cho_phep_tai", "created_at")},
            "cuoc_hop_id": ch.id, "nguon": ch.nguon, "ma_lich": ch.ma_lich,
            "tieu_de": ch.tieu_de, "ngay_hop": ch.ngay_hop,
            "duong_dan_cuoc_hop": (
                f"/lich-cong-tac/{ch.id}" if ch.nguon == "LICH_CONG_TAC"
                else f"/hop-khong-giay/chi-tiet/{ch.id}"),
        }).model_dump(mode="json")
        item["url_xem"] = (
            f"/api/v1/hop-khong-giay/tai-lieu/{tl.id}/xem-noi-dung?t={token}")
        out.append(item)

    return {"success": True, "data": out,
            "pagination": {"trang": trang, "so_dong": so_dong,
                           "con_nua": con_nua}}


@router.get("/kho/thong-ke", summary="Số tài liệu mỗi nguồn (cho cây thư mục)")
async def kho_thong_ke(db: DatabaseDep, user: CurrentUserDep):
    """Đếm nhanh để cây thư mục hiện được số bên cạnh tên.

    Cố tình KHÔNG lọc theo quyền: đây chỉ là con số trên nhãn thư mục, mà đếm
    đúng theo quyền thì phải duyệt cả kho cho mỗi lần vẽ cây. Số hiển thị có
    thể lớn hơn số tài liệu người dùng thật sự mở được — chấp nhận, vì bản
    thân con số không tiết lộ gì.
    """
    from sqlalchemy import func, select

    from meeting_service.models.cuoc_hop import CuocHop as CH
    from meeting_service.models.tai_lieu import TaiLieu

    rows = (await db.execute(
        select(CH.nguon, func.count())
        .join(TaiLieu, TaiLieu.cuoc_hop_id == CH.id)
        .where(TaiLieu.is_deleted.is_(False), CH.is_deleted.is_(False))
        .group_by(CH.nguon)
    )).all()
    theo_nguon = {n: c for n, c in rows}
    return {"success": True, "data": {
        "HKG": theo_nguon.get("HKG", 0),
        "LICH_CONG_TAC": theo_nguon.get("LICH_CONG_TAC", 0),
        "tong": sum(theo_nguon.values()),
    }}


@router.get("/muc-phan-quyen", summary="Danh mục mức phân quyền tài liệu")
async def muc_phan_quyen(user: CurrentUserDep):
    """Kèm cờ `dat_duoc` để giao diện làm mờ mức người dùng không được chọn."""
    cho_phep = set(muc_dat_duoc(user))
    return {"success": True, "data": [
        {"ma": m, "ten": NHAN_PHAN_QUYEN[m], "mo_ta": MO_TA_PHAN_QUYEN[m],
         "dat_duoc": m in cho_phep}
        for m in PHAN_QUYEN_VALUES
    ]}


# ─── 1. UPLOAD ────────────────────────────────────────────────────────
# Rate-limit: 60/5minutes per user (~12/phút) — cuộc họp công vụ thường có
# 10-30 tài liệu, limit cũ 10/5min đã từng false-positive (sự cố 11/05/2026).
# Override qua env HKG_UPLOAD_RATE_LIMIT khi cần (vd "30/minute").
@router.post("/upload", status_code=201, summary="Upload tài liệu họp")
@limiter.limit(os.getenv("HKG_UPLOAD_RATE_LIMIT", "60/5minutes"))
async def upload_tai_lieu(
    request: Request,
    db: DatabaseDep,
    user: CurrentUserDep,
    cuoc_hop_id: UUID = Form(...),
    file: UploadFile = File(...),
    ten_tai_lieu: Optional[str] = Form(None),
    mo_ta: Optional[str] = Form(None),
    phan_quyen: str = Form("CONG_KHAI"),
    cho_phep_tai: bool = Form(True),
    cho_phep_in: bool = Form(True),
):
    """Upload 1 file vào cuộc họp. Permission: chu_toa | thu_ky | admin."""
    # Tự kiểm tra edit-permission ở đây vì cuoc_hop_id từ Form không phải Path
    from sqlalchemy import select
    from meeting_service.models.cuoc_hop import CuocHop as CuocHopModel
    res = await db.execute(
        select(CuocHopModel).where(
            CuocHopModel.id == cuoc_hop_id, CuocHopModel.is_deleted.is_(False)
        )
    )
    ch = res.scalar_one_or_none()
    if ch is None:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": {"code": "MEETING_NOT_FOUND",
                    "message": "Không tìm thấy cuộc họp"}},
        )
    # G4-fix-5: chặn upload cho cuộc họp đã hủy (audit trail)
    if ch.trang_thai == "HUY":
        raise HTTPException(
            status_code=409,
            detail={"success": False, "error": {"code": "MEETING_CANCELLED",
                    "message": "Cuộc họp đã hủy — không thể upload tài liệu"}},
        )
    if not duoc_quan_ly_tai_lieu(ch, user):
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "NO_PERMISSION",
                    "message": "Bạn không có quyền tải tài liệu lên cho cuộc "
                               "họp / sự kiện này"}},
        )

    _kiem_muc_dat_duoc(phan_quyen, user)

    service = TaiLieuService(db)
    tl = await service.upload(
        ch, file, user,
        ten_tai_lieu=ten_tai_lieu,
        mo_ta=mo_ta,
        phan_quyen=phan_quyen,
        cho_phep_tai=cho_phep_tai,
        cho_phep_in=cho_phep_in,
    )
    return {
        "success": True,
        "data": TaiLieuResponse.model_validate(tl).model_dump(mode="json"),
    }


# ─── 2. LIST của 1 cuộc họp ───────────────────────────────────────────
@router_cuoc_hop.get(
    "/{cuoc_hop_id}/tai-lieu",
    summary="Danh sách tài liệu của cuộc họp",
)
async def list_tai_lieu(
    db: DatabaseDep,
    user: CurrentUserDep,
    ch: CuocHop = Depends(require_can_view_meeting),
):
    """Trả về danh sách tài liệu + URL xem (kèm short-lived token)."""
    service = TaiLieuService(db)
    items = await service.list_for_cuoc_hop(ch.id)

    # G5.4 — lọc TRƯỚC khi phát token. Danh sách này nhúng sẵn `url_xem` kèm
    # token xem file, nên trả về rồi mới để giao diện ẩn đi là vô nghĩa: token
    # đã nằm trong tay người không được xem.
    items = loc_xem_duoc(items, user)

    out = []
    for tl in items:
        token = issue_token(
            purpose=PURPOSE_VIEW_DOC,
            subject=str(tl.id),
            extra_claims={"viewer_id": user.sub},
            ttl_seconds=3600,
        )
        item = TaiLieuListItem.model_validate(tl).model_dump(mode="json")
        item["url_xem"] = f"/api/v1/hop-khong-giay/tai-lieu/{tl.id}/xem-noi-dung?t={token}"
        out.append(item)

    return {"success": True, "data": out}


# ─── 3. ISSUE VIEW URL (302 redirect) ─────────────────────────────────
@router.get("/{tai_lieu_id}/xem", summary="Sinh URL xem tài liệu (1h)")
async def xem_tai_lieu(
    tai_lieu_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """
    Sinh URL ngắn hạn để client GET /xem-noi-dung. Audit VIEW_DOC.
    """
    service = TaiLieuService(db)
    tl = await service.get(tai_lieu_id)

    # Check user xem được cuộc họp chứa tài liệu không
    from meeting_service.dependencies import _can_view_cuoc_hop
    from sqlalchemy import select
    from meeting_service.models.cuoc_hop import CuocHop as CuocHopModel
    res = await db.execute(
        select(CuocHopModel).where(CuocHopModel.id == tl.cuoc_hop_id)
    )
    ch = res.scalar_one_or_none()
    if ch is None or not await _can_view_cuoc_hop(ch, user, db):
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "NO_PERMISSION",
                    "message": "Không có quyền xem tài liệu này"}},
        )
    if not xem_duoc(tl.phan_quyen, user, nguoi_tai_len_id=tl.created_by):
        raise _loi_phan_quyen("xem")

    await service.audit_view(tl, UUID(user.sub))

    token = issue_token(
        purpose=PURPOSE_VIEW_DOC,
        subject=str(tl.id),
        extra_claims={"viewer_id": user.sub},
        ttl_seconds=3600,
    )
    return {
        "success": True,
        "data": {
            "url": f"/api/v1/hop-khong-giay/tai-lieu/{tl.id}/xem-noi-dung?t={token}",
            "expires_in_seconds": 3600,
        },
    }


# ─── 4. DOWNLOAD URL ──────────────────────────────────────────────────
@router.get("/{tai_lieu_id}/tai", summary="Sinh URL tải tài liệu")
async def tai_tai_lieu(
    tai_lieu_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = TaiLieuService(db)
    tl = await service.get(tai_lieu_id)

    if not tl.cho_phep_tai:
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "DOWNLOAD_DISABLED",
                    "message": "Tài liệu không cho phép tải về"}},
        )

    # View permission cũng phải có
    from meeting_service.dependencies import _can_view_cuoc_hop
    from sqlalchemy import select
    from meeting_service.models.cuoc_hop import CuocHop as CuocHopModel
    res = await db.execute(select(CuocHopModel).where(CuocHopModel.id == tl.cuoc_hop_id))
    ch = res.scalar_one_or_none()
    if ch is None or not await _can_view_cuoc_hop(ch, user, db):
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "NO_PERMISSION",
                    "message": "Không có quyền tải tài liệu này"}},
        )
    if not xem_duoc(tl.phan_quyen, user, nguoi_tai_len_id=tl.created_by):
        raise _loi_phan_quyen("tải")

    await service.audit_download(tl, UUID(user.sub))

    token = issue_token(
        purpose=PURPOSE_DOWNLOAD_DOC,
        subject=str(tl.id),
        extra_claims={"viewer_id": user.sub},
        ttl_seconds=3600,
    )
    return {
        "success": True,
        "data": {
            "url": f"/api/v1/hop-khong-giay/tai-lieu/{tl.id}/tai-noi-dung?t={token}",
            "expires_in_seconds": 3600,
        },
    }


# ─── 5. SOFT DELETE ───────────────────────────────────────────────────
@router.delete("/{tai_lieu_id}", summary="Xóa tài liệu (soft delete)")
async def xoa_tai_lieu(
    tai_lieu_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = TaiLieuService(db)
    tl = await service.get(tai_lieu_id)

    # Check edit permission via cuoc_hop
    from sqlalchemy import select
    from meeting_service.models.cuoc_hop import CuocHop as CuocHopModel
    res = await db.execute(select(CuocHopModel).where(CuocHopModel.id == tl.cuoc_hop_id))
    ch = res.scalar_one_or_none()
    if ch is None:
        raise HTTPException(404)
    if not duoc_quan_ly_tai_lieu(ch, user):
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "NO_PERMISSION",
                    "message": "Bạn không có quyền xóa tài liệu này"}},
        )
    # Không xem được thì cũng không xoá được: xoá tài liệu mình chưa từng thấy
    # nội dung là thao tác mù, và là đường vòng để phá tài liệu hạn chế.
    if not xem_duoc(tl.phan_quyen, user, nguoi_tai_len_id=tl.created_by):
        raise _loi_phan_quyen("xoá")

    await service.soft_delete(tl, user)
    return {"success": True, "data": {"id": str(tl.id), "is_deleted": True}}


# ─── 5b. SỬA MỨC PHÂN QUYỀN / METADATA (G5.4) ─────────────────────────
# Trước G5.4 không có đường nào sửa `phan_quyen` sau khi tải lên — hàm
# `TaiLieuService.update_metadata` đã có nhưng chưa endpoint nào gọi tới. Mà
# yêu cầu là "587 file lịch sử mặc định công khai nội bộ; Văn phòng nâng mức
# từng file nếu cần", nên phải có đường nâng mức.
@router.patch("/{tai_lieu_id}", summary="Sửa mức phân quyền / metadata tài liệu")
async def sua_tai_lieu(
    tai_lieu_id: UUID,
    du_lieu: TaiLieuMetadataUpdate,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = TaiLieuService(db)
    tl = await service.get(tai_lieu_id)

    from sqlalchemy import select
    from meeting_service.models.cuoc_hop import CuocHop as CuocHopModel
    res = await db.execute(
        select(CuocHopModel).where(CuocHopModel.id == tl.cuoc_hop_id))
    ch = res.scalar_one_or_none()
    if ch is None:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": {"code": "MEETING_NOT_FOUND",
                    "message": "Không tìm thấy cuộc họp của tài liệu"}},
        )

    if not duoc_quan_ly_tai_lieu(ch, user):
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "NO_PERMISSION",
                    "message": "Bạn không có quyền sửa tài liệu này"}},
        )
    # Phải xem được mức HIỆN TẠI mới sửa được, và mức MỚI không được vượt bậc
    # của chính mình.
    if not xem_duoc(tl.phan_quyen, user, nguoi_tai_len_id=tl.created_by):
        raise _loi_phan_quyen("sửa")
    _kiem_muc_dat_duoc(du_lieu.phan_quyen, user)

    tl = await service.update_metadata(tl, du_lieu, user)
    return {"success": True,
            "data": TaiLieuResponse.model_validate(tl).model_dump(mode="json"),
            "message": "Đã cập nhật tài liệu"}


# ─── 6. SERVE FILE NỘI DUNG (gateway) ─────────────────────────────────
@router.get(
    "/{tai_lieu_id}/xem-noi-dung",
    summary="Serve file nội dung — yêu cầu short-lived token",
    response_class=FileResponse,
)
async def serve_view(
    tai_lieu_id: UUID,
    db: DatabaseDep,
    t: str = Query(..., description="Short-lived token từ /xem"),
):
    """Serve file để xem inline. KHÔNG audit (audit đã ghi ở /xem)."""
    payload = verify_token(t, expected_purpose=PURPOSE_VIEW_DOC)
    if payload.get("sub") != str(tai_lieu_id):
        raise HTTPException(
            status_code=401,
            detail={"success": False, "error": {"code": "TOKEN_MISMATCH",
                    "message": "Token không đúng tài liệu"}},
        )

    service = TaiLieuService(db)
    tl = await service.get(tai_lieu_id)

    storage = StorageService()
    if not storage.file_exists(tl.minio_key):
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": {"code": "FILE_NOT_FOUND",
                    "message": "File vật lý không tồn tại"}},
        )

    source_path = storage.resolve_path(tl.minio_key)

    # Browser không render native được Office formats — convert sang PDF rồi
    # serve inline. Cache PDF tại _preview_cache/<id>.pdf.
    if is_office_extension(tl.extension):
        try:
            pdf_path = await ensure_pdf_preview(str(tl.id), source_path)
        except RuntimeError as e:
            raise HTTPException(
                status_code=503,
                detail={"success": False, "error": {
                    "code": "PREVIEW_UNAVAILABLE",
                    "message": f"Không thể chuyển đổi file sang PDF: {e}",
                }},
            )
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"{tl.ten_tai_lieu}.pdf",
            content_disposition_type="inline",
        )

    return FileResponse(
        path=source_path,
        media_type=tl.mime_type or "application/octet-stream",
        filename=tl.ten_tai_lieu,
        content_disposition_type="inline",
    )


@router.get(
    "/{tai_lieu_id}/tai-noi-dung",
    summary="Serve file để tải xuống — yêu cầu short-lived token",
    response_class=FileResponse,
)
async def serve_download(
    tai_lieu_id: UUID,
    db: DatabaseDep,
    t: str = Query(...),
):
    payload = verify_token(t, expected_purpose=PURPOSE_DOWNLOAD_DOC)
    if payload.get("sub") != str(tai_lieu_id):
        raise HTTPException(
            status_code=401,
            detail={"success": False, "error": {"code": "TOKEN_MISMATCH",
                    "message": "Token không đúng tài liệu"}},
        )

    service = TaiLieuService(db)
    tl = await service.get(tai_lieu_id)

    if not tl.cho_phep_tai:
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "DOWNLOAD_DISABLED",
                    "message": "Tài liệu không cho phép tải về"}},
        )

    storage = StorageService()
    if not storage.file_exists(tl.minio_key):
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": {"code": "FILE_NOT_FOUND",
                    "message": "File vật lý không tồn tại"}},
        )

    return FileResponse(
        path=storage.resolve_path(tl.minio_key),
        media_type="application/octet-stream",
        filename=tl.ten_tai_lieu,
    )
