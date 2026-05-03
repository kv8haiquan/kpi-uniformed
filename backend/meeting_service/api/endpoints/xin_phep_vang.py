"""
api/endpoints/xin_phep_vang.py
================================
Module 5 — Xin phép vắng. 3 endpoints:
- POST  /xin-phep-vang/         CBCC gửi đơn
- GET   /xin-phep-vang/cho-duyet  Chủ tọa xem chờ duyệt
- POST  /xin-phep-vang/{id}/duyet  Chủ tọa approve/reject

Auto-approve sau 4h chạy qua APScheduler (xem `meeting_service/scheduler.py`).
"""

from uuid import UUID

from fastapi import APIRouter

from meeting_service.dependencies import CurrentUserDep, DatabaseDep
from meeting_service.schemas.xin_phep_vang import (
    XinPhepVangCreate,
    XinPhepVangDuyet,
    XinPhepVangResponse,
)
from meeting_service.services.xin_phep_vang_service import XinPhepVangService


router = APIRouter(prefix="/xin-phep-vang", tags=["Xin phép vắng"])


@router.post("/", status_code=201, summary="CBCC gửi đơn xin vắng")
async def gui_don(
    data: XinPhepVangCreate,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = XinPhepVangService(db)
    xpv = await service.create(data, user)
    return {
        "success": True,
        "data": XinPhepVangResponse.model_validate(xpv).model_dump(mode="json"),
    }


@router.get("/cho-duyet", summary="Chủ tọa xem các đơn chờ duyệt")
async def list_cho_duyet(
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = XinPhepVangService(db)
    items = await service.list_cho_duyet(user)
    return {
        "success": True,
        "data": [
            XinPhepVangResponse.model_validate(x).model_dump(mode="json")
            for x in items
        ],
    }


@router.post("/{xpv_id}/duyet", summary="Chủ tọa duyệt / từ chối đơn")
async def duyet_don(
    xpv_id: UUID,
    payload: XinPhepVangDuyet,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = XinPhepVangService(db)
    xpv = await service.duyet(xpv_id, payload, user)
    return {
        "success": True,
        "data": XinPhepVangResponse.model_validate(xpv).model_dump(mode="json"),
    }
