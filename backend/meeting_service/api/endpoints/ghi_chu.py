"""
api/endpoints/ghi_chu.py
=========================
Ghi chú cá nhân và chia sẻ — G5.2.

Quyền nằm trọn trong `GhiChuService`: chủ ghi chú toàn quyền, người được chia
sẻ chỉ đọc, không ai khác — kể cả quản trị. Endpoint ở đây chỉ dịch lỗi nghiệp
vụ sang HTTP.

File đính kèm dùng lại đường serve của tài liệu họp
(`/tai-lieu/{id}/xem-noi-dung`) vì hai endpoint đó chỉ xác thực bằng token
ngắn hạn, không suy quyền từ cuộc họp — nên ghi chú tự kiểm quyền rồi phát
token là đủ và không phải nhân đôi tầng serve file.
"""

import os
from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)

from meeting_service.dependencies import CurrentUserDep, DatabaseDep
from meeting_service.schemas.ghi_chu import (
    PHAM_VI_VALUES,
    ChiaSeCreate,
    GhiChuCreate,
    GhiChuUpdate,
)
from meeting_service.services.ghi_chu_service import GhiChuService
from meeting_service.services.lich_cong_tac_service import LoiNghiepVu
from meeting_service.services.rate_limit import limiter
from meeting_service.services.short_lived_token import (
    PURPOSE_DOWNLOAD_DOC,
    PURPOSE_VIEW_DOC,
    issue_token,
)

router = APIRouter(prefix="/ghi-chu", tags=["Ghi chú"])

DUONG_DAN_SERVE = "/api/v1/hop-khong-giay/tai-lieu"


def _loi(e: LoiNghiepVu) -> HTTPException:
    return HTTPException(
        e.http,
        detail={"success": False,
                "error": {"code": e.ma, "message": e.thong_diep}})


# ── xem ───────────────────────────────────────────────────────────────

@router.get("", summary="Danh sách ghi chú của tôi và được chia sẻ")
async def danh_sach(
    db: DatabaseDep,
    user: CurrentUserDep,
    pham_vi: str = Query("TAT_CA", alias="pham-vi"),
    cuoc_hop_id: Optional[UUID] = Query(None, alias="cuoc-hop-id"),
    tu_khoa: Optional[str] = Query(None, alias="tu-khoa", max_length=200),
    chi_chua_doc: bool = Query(False, alias="chi-chua-doc"),
    trang: int = Query(1, ge=1),
    so_dong: int = Query(20, ge=1, le=100, alias="so-dong"),
):
    if pham_vi not in PHAM_VI_VALUES:
        raise HTTPException(
            422,
            detail={"success": False,
                    "error": {"code": "VALIDATION_ERROR",
                              "message": f"pham-vi phải thuộc {PHAM_VI_VALUES}"}})
    ds, tong = await GhiChuService(db).danh_sach(
        user, pham_vi=pham_vi, cuoc_hop_id=cuoc_hop_id, tu_khoa=tu_khoa,
        chi_chua_doc=chi_chua_doc, trang=trang, so_dong=so_dong)
    return {
        "success": True,
        "data": ds,
        "pagination": {
            "page": trang, "page_size": so_dong, "total_items": tong,
            "total_pages": (tong + so_dong - 1) // so_dong,
        },
    }


@router.get("/chua-doc", summary="Số ghi chú được chia sẻ chưa đọc")
async def chua_doc(db: DatabaseDep, user: CurrentUserDep):
    return {"success": True,
            "data": {"so_chua_doc": await GhiChuService(db).dem_chua_doc(user)}}


@router.get("/nguoi-nhan", summary="Gợi ý người nhận khi chia sẻ")
async def nguoi_nhan(
    db: DatabaseDep,
    user: CurrentUserDep,
    tu_khoa: Optional[str] = Query(None, alias="tu-khoa", max_length=200),
    gioi_han: int = Query(50, ge=1, le=200, alias="gioi-han"),
):
    return {"success": True,
            "data": await GhiChuService(db).nguoi_nhan_goi_y(
                user, tu_khoa, gioi_han)}


# ── đính kèm: đặt TRƯỚC /{ghi_chu_id} để không bị nuốt làm UUID ───────

@router.get("/tai-lieu/{tai_lieu_id}/xem", summary="URL xem file đính kèm")
async def xem_dinh_kem(
    tai_lieu_id: UUID, db: DatabaseDep, user: CurrentUserDep,
):
    try:
        tl = await GhiChuService(db).lay_tai_lieu(tai_lieu_id, user)
    except LoiNghiepVu as e:
        raise _loi(e)
    token = issue_token(purpose=PURPOSE_VIEW_DOC, subject=str(tl.id),
                        extra_claims={"viewer_id": user.sub}, ttl_seconds=3600)
    return {"success": True,
            "data": {"url": f"{DUONG_DAN_SERVE}/{tl.id}/xem-noi-dung?t={token}",
                     "expires_in_seconds": 3600}}


@router.get("/tai-lieu/{tai_lieu_id}/tai", summary="URL tải file đính kèm")
async def tai_dinh_kem(
    tai_lieu_id: UUID, db: DatabaseDep, user: CurrentUserDep,
):
    try:
        tl = await GhiChuService(db).lay_tai_lieu(tai_lieu_id, user)
    except LoiNghiepVu as e:
        raise _loi(e)
    token = issue_token(purpose=PURPOSE_DOWNLOAD_DOC, subject=str(tl.id),
                        extra_claims={"viewer_id": user.sub}, ttl_seconds=3600)
    return {"success": True,
            "data": {"url": f"{DUONG_DAN_SERVE}/{tl.id}/tai-noi-dung?t={token}",
                     "expires_in_seconds": 3600}}


@router.delete("/tai-lieu/{tai_lieu_id}", summary="Xoá file đính kèm")
async def xoa_dinh_kem(
    tai_lieu_id: UUID, db: DatabaseDep, user: CurrentUserDep,
):
    try:
        await GhiChuService(db).xoa_tai_lieu(tai_lieu_id, user)
    except LoiNghiepVu as e:
        raise _loi(e)
    return {"success": True, "data": {"id": str(tai_lieu_id), "is_deleted": True}}


@router.get("/{ghi_chu_id}", summary="Chi tiết ghi chú")
async def chi_tiet(ghi_chu_id: UUID, db: DatabaseDep, user: CurrentUserDep):
    try:
        return {"success": True,
                "data": await GhiChuService(db).chi_tiet(ghi_chu_id, user)}
    except LoiNghiepVu as e:
        raise _loi(e)


# ── ghi ───────────────────────────────────────────────────────────────

@router.post("", status_code=201, summary="Tạo ghi chú")
async def tao(du_lieu: GhiChuCreate, db: DatabaseDep, user: CurrentUserDep):
    svc = GhiChuService(db)
    try:
        gc = await svc.tao(du_lieu.model_dump(), user)
        chi_tiet_gc = await svc.chi_tiet(gc.id, user)
    except LoiNghiepVu as e:
        raise _loi(e)
    return {"success": True, "data": chi_tiet_gc,
            "message": "Đã tạo ghi chú"}


@router.patch("/{ghi_chu_id}", summary="Sửa ghi chú")
async def cap_nhat(
    ghi_chu_id: UUID, thay_doi: GhiChuUpdate, db: DatabaseDep,
    user: CurrentUserDep,
):
    svc = GhiChuService(db)
    try:
        # exclude_unset: gửi `cuoc_hop_id: null` là GỠ khỏi cuộc họp, còn
        # không gửi trường đó là giữ nguyên — hai ý nghĩa khác nhau.
        await svc.cap_nhat(ghi_chu_id, thay_doi.model_dump(exclude_unset=True),
                           user)
        chi_tiet_gc = await svc.chi_tiet(ghi_chu_id, user)
    except LoiNghiepVu as e:
        raise _loi(e)
    return {"success": True, "data": chi_tiet_gc, "message": "Đã lưu"}


@router.delete("/{ghi_chu_id}", summary="Xoá ghi chú")
async def xoa(ghi_chu_id: UUID, db: DatabaseDep, user: CurrentUserDep):
    try:
        await GhiChuService(db).xoa(ghi_chu_id, user)
    except LoiNghiepVu as e:
        raise _loi(e)
    return {"success": True, "data": {"id": str(ghi_chu_id), "is_deleted": True},
            "message": "Đã xoá ghi chú"}


# ── chia sẻ ───────────────────────────────────────────────────────────

@router.post("/{ghi_chu_id}/chia-se", summary="Chia sẻ ghi chú cho người khác")
async def chia_se(
    ghi_chu_id: UUID, du_lieu: ChiaSeCreate, db: DatabaseDep,
    user: CurrentUserDep,
):
    try:
        ket_qua = await GhiChuService(db).chia_se(
            ghi_chu_id, du_lieu.nguoi_nhan_ids, du_lieu.loi_nhan, user)
    except LoiNghiepVu as e:
        raise _loi(e)
    moi = sum(1 for k in ket_qua if k["moi"])
    return {"success": True,
            "data": [{"nguoi_nhan_id": str(k["nguoi_nhan_id"]), "moi": k["moi"]}
                     for k in ket_qua],
            "message": (f"Đã chia sẻ cho {moi} người"
                        if moi else "Những người này đã được chia sẻ từ trước")}


@router.delete("/{ghi_chu_id}/chia-se/{chia_se_id}",
               summary="Thu hồi một lượt chia sẻ")
async def thu_hoi(
    ghi_chu_id: UUID, chia_se_id: UUID, db: DatabaseDep, user: CurrentUserDep,
):
    try:
        await GhiChuService(db).thu_hoi_chia_se(ghi_chu_id, chia_se_id, user)
    except LoiNghiepVu as e:
        raise _loi(e)
    return {"success": True, "data": {"id": str(chia_se_id)},
            "message": "Đã thu hồi"}


@router.post("/{ghi_chu_id}/da-doc", summary="Đánh dấu đã đọc")
async def da_doc(ghi_chu_id: UUID, db: DatabaseDep, user: CurrentUserDep):
    try:
        thay_doi = await GhiChuService(db).danh_dau_da_doc(ghi_chu_id, user)
    except LoiNghiepVu as e:
        raise _loi(e)
    return {"success": True, "data": {"da_doc": True, "vua_doi": thay_doi}}


# ── đính kèm: upload ──────────────────────────────────────────────────

@router.post("/{ghi_chu_id}/tai-lieu", status_code=201,
             summary="Đính kèm file vào ghi chú")
@limiter.limit(os.getenv("HKG_UPLOAD_RATE_LIMIT", "60/5minutes"))
async def them_dinh_kem(
    request: Request,
    ghi_chu_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
    file: UploadFile = File(...),
    mo_ta: Optional[str] = Form(None),
):
    try:
        tl = await GhiChuService(db).them_tai_lieu(
            ghi_chu_id, file, user, mo_ta=mo_ta)
        du_lieu = {"id": str(tl.id), "ten_tai_lieu": tl.ten_tai_lieu,
                   "file_size": tl.file_size, "extension": tl.extension,
                   "mime_type": tl.mime_type, "mo_ta": tl.mo_ta}
    except LoiNghiepVu as e:
        raise _loi(e)
    return {"success": True, "data": du_lieu, "message": "Đã đính kèm"}
