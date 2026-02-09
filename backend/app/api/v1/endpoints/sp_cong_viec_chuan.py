"""
app/api/v1/endpoints/sp_cong_viec_chuan.py
==========================================
API Endpoints cho Sản phẩm công việc chuẩn (SP1-SP4).

Version: 1.0.0 (31/01/2026)
- GET /sp-cong-viec-chuan: Lấy danh sách SP chuẩn (SP1-SP4)
"""

from typing import List
from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DatabaseDep, ActiveUserDep
from app.models.task_catalog import SpCongViecChuan
from app.schemas.common import success_response

router = APIRouter()


@router.get("")
async def get_sp_chuan_list(
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Lấy danh sách Sản phẩm công việc chuẩn (SP1-SP4).
    
    Response:
    [
        {
            "id": "uuid",
            "ma_sp": "SP1",
            "ten_sp": "Tờ khai HQ được kiểm tra chi tiết hồ sơ",
            "mo_ta": "5 phút = 1 SP gốc",
            "thoi_gian_phut": 5,
            "he_so_quy_doi_sp1": 1,
            "is_sp_goc": true,
            "is_active": true
        },
        ...
    ]
    """
    stmt = (
        select(SpCongViecChuan)
        .where(SpCongViecChuan.is_active == True)
        .order_by(SpCongViecChuan.ma_sp)
    )
    
    result = await db.execute(stmt)
    sp_list = result.scalars().all()
    
    data = [
        {
            "id": sp.id,
            "ma_sp": sp.ma_sp,
            "ten_sp": sp.ten_sp,
            "mo_ta": sp.mo_ta,
            "thoi_gian_phut": sp.thoi_gian_phut,
            "he_so_quy_doi_sp1": float(sp.he_so_quy_doi_sp1),
            "is_sp_goc": sp.is_sp_goc,
            "is_active": sp.is_active,
        }
        for sp in sp_list
    ]
    
    return success_response(data=data, message="Lấy danh sách SP chuẩn thành công")