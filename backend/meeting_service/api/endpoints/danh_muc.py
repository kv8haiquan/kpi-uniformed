"""
api/endpoints/danh_muc.py
==========================
Quản trị danh mục dùng chung của Lịch công tác (G4.11).

Đáp yêu cầu chuyển đổi mục II.15 và bảng nghiệm thu XI.9. Thay sheet `SETUP`
của lichkv8 — xem migration meeting_024 để biết vì sao chỉ mang 4 trong 12
nhóm của hệ cũ.

Đọc: ai cũng đọc được (mọi màn hình lịch cần để đổ ô chọn).
Ghi: chỉ quản trị Lịch công tác.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from meeting_service.dependencies import CurrentUserDep, DatabaseDep
from meeting_service.models.danh_muc import NHAN_NHOM, NHOM_HOP_LE
from meeting_service.schemas.danh_muc import (
    DanhMucCreate,
    DanhMucItem,
    DanhMucSapXep,
    DanhMucUpdate,
)
from meeting_service.services.danh_muc_service import DanhMucService
from meeting_service.services.lich_cong_tac_service import (
    LoiNghiepVu,
    la_quan_tri_lich,
)

router = APIRouter(prefix="/danh-muc", tags=["Quản trị danh mục"])


def _loi(e: LoiNghiepVu) -> HTTPException:
    return HTTPException(
        e.http,
        detail={"success": False,
                "error": {"code": e.ma, "message": e.thong_diep}})


@router.get("/nhom", summary="Các nhóm danh mục quản trị được")
async def nhom(user: CurrentUserDep):
    """Kèm cờ `duoc_sua` để giao diện ẩn nút sửa thay vì để người dùng bấm
    rồi mới nhận 403."""
    return {"success": True, "data": {
        "nhom": [{"ma": n, "ten": NHAN_NHOM[n]} for n in NHOM_HOP_LE],
        "duoc_sua": la_quan_tri_lich(user),
    }}


@router.get("/", summary="Danh sách mục theo nhóm")
async def danh_sach(
    db: DatabaseDep,
    user: CurrentUserDep,
    nhom: Optional[str] = Query(None, description="Bỏ trống để lấy tất cả nhóm"),
    gom_ca_tat: bool = Query(
        False, alias="gom-ca-tat",
        description="Lấy cả mục đã tắt — chỉ dùng cho màn hình quản trị"),
    dem_su_dung: bool = Query(
        False, alias="dem-su-dung",
        description="Kèm số bản ghi đang dùng từng mục (tốn thêm truy vấn)"),
):
    svc = DanhMucService(db)
    try:
        # Chỉ quản trị mới được xem mục đã tắt: người dùng thường thấy mục tắt
        # thì tắt cũng như không.
        ca_tat = gom_ca_tat and la_quan_tri_lich(user)
        items = await svc.danh_sach(nhom=nhom, gom_ca_tat=ca_tat)
        ra = [DanhMucItem.model_validate(x).model_dump(mode="json") for x in items]
        if dem_su_dung and la_quan_tri_lich(user):
            for goc, dong in zip(items, ra):
                dong["dang_su_dung"] = await svc.dem_su_dung(goc)
        return {"success": True, "data": ra}
    except LoiNghiepVu as e:
        raise _loi(e)


@router.post("/", status_code=201, summary="Thêm mục danh mục")
async def tao(db: DatabaseDep, user: CurrentUserDep, payload: DanhMucCreate):
    try:
        dm = await DanhMucService(db).tao(
            payload.nhom, payload.ma, payload.nhan, user,
            thu_tu=payload.thu_tu, mo_ta=payload.mo_ta,
        )
        return {"success": True,
                "data": DanhMucItem.model_validate(dm).model_dump(mode="json"),
                "message": "Đã thêm vào danh mục"}
    except LoiNghiepVu as e:
        raise _loi(e)


@router.patch("/{dm_id}", summary="Sửa tên, thứ tự hoặc bật/tắt một mục")
async def cap_nhat(
    db: DatabaseDep, user: CurrentUserDep, dm_id: UUID, payload: DanhMucUpdate
):
    try:
        dm = await DanhMucService(db).cap_nhat(
            dm_id, payload.model_dump(exclude_unset=True), user)
        return {"success": True,
                "data": DanhMucItem.model_validate(dm).model_dump(mode="json"),
                "message": "Đã lưu"}
    except LoiNghiepVu as e:
        raise _loi(e)


@router.put("/sap-xep", summary="Đặt lại thứ tự nhiều mục một lượt")
async def sap_xep(db: DatabaseDep, user: CurrentUserDep, payload: DanhMucSapXep):
    try:
        n = await DanhMucService(db).sap_xep(
            [d.model_dump() for d in payload.thu_tu], user)
        return {"success": True, "data": {"so_muc_doi": n},
                "message": f"Đã đổi thứ tự {n} mục"}
    except LoiNghiepVu as e:
        raise _loi(e)


@router.delete("/{dm_id}", summary="Xoá một mục (chỉ khi chưa ai dùng)")
async def xoa(db: DatabaseDep, user: CurrentUserDep, dm_id: UUID):
    try:
        return {"success": True,
                "data": await DanhMucService(db).xoa(dm_id, user),
                "message": "Đã xoá khỏi danh mục"}
    except LoiNghiepVu as e:
        raise _loi(e)
