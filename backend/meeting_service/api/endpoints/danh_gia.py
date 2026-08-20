"""
api/endpoints/danh_gia.py
==========================
Chấm sao công tác chuẩn bị cuộc họp — G5.3.

Xem thì ai cũng được, chấm thì chỉ lãnh đạo Chi cục và quản trị. Cờ
`duoc_cham` trả kèm mọi phản hồi để giao diện biết hiện sao đặc (chỉ đọc) hay
sao rỗng bấm được, thay vì hiện nút rồi báo lỗi khi bấm.
"""

from datetime import date as date_type
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from meeting_service.dependencies import CurrentUserDep, DatabaseDep
from meeting_service.schemas.danh_gia import DanhGiaGhi
from meeting_service.services.danh_gia_service import (
    DanhGiaService,
    duoc_cham_diem,
)
from meeting_service.services.lich_cong_tac_service import LoiNghiepVu

router = APIRouter(prefix="/danh-gia-chuan-bi", tags=["Đánh giá chuẩn bị họp"])


def _loi(e: LoiNghiepVu) -> HTTPException:
    return HTTPException(
        e.http,
        detail={"success": False,
                "error": {"code": e.ma, "message": e.thong_diep}})


@router.get("/quyen", summary="Người đang đăng nhập có được chấm điểm không")
async def quyen(user: CurrentUserDep):
    return {"success": True, "data": {"duoc_cham": duoc_cham_diem(user)}}


@router.get("/tong-hop", summary="Tổng hợp điểm chuẩn bị theo đơn vị")
async def tong_hop(
    db: DatabaseDep,
    _: CurrentUserDep,
    tu_ngay: Optional[date_type] = Query(None, alias="tu-ngay"),
    den_ngay: Optional[date_type] = Query(None, alias="den-ngay"),
    gioi_han: int = Query(200, ge=1, le=1000, alias="gioi-han"),
):
    return {"success": True,
            "data": await DanhGiaService(db).tong_hop(
                tu_ngay, den_ngay, gioi_han)}


@router.get("/{cuoc_hop_id}", summary="Điểm chuẩn bị của một cuộc họp")
async def cua_cuoc_hop(
    cuoc_hop_id: UUID, db: DatabaseDep, user: CurrentUserDep,
):
    try:
        return {"success": True,
                "data": await DanhGiaService(db).cua_cuoc_hop(
                    cuoc_hop_id, user)}
    except LoiNghiepVu as e:
        raise _loi(e)


@router.put("/{cuoc_hop_id}", summary="Chấm hoặc sửa điểm của chính mình")
async def cham(
    cuoc_hop_id: UUID, du_lieu: DanhGiaGhi, db: DatabaseDep,
    user: CurrentUserDep,
):
    try:
        kq = await DanhGiaService(db).cham(
            cuoc_hop_id, du_lieu.diem, du_lieu.ghi_chu, user)
    except LoiNghiepVu as e:
        raise _loi(e)
    return {"success": True, "data": kq, "message": "Đã ghi nhận đánh giá"}


@router.delete("/{cuoc_hop_id}", summary="Rút lại điểm của chính mình")
async def bo_cham(
    cuoc_hop_id: UUID, db: DatabaseDep, user: CurrentUserDep,
):
    try:
        kq = await DanhGiaService(db).bo_cham(cuoc_hop_id, user)
    except LoiNghiepVu as e:
        raise _loi(e)
    return {"success": True, "data": kq, "message": "Đã rút lại đánh giá"}
