"""
forum_service/api/endpoints/theo_doi.py
========================================
Endpoints Theo doi chu de.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from fastapi import APIRouter, Depends, Query

from forum_service.dependencies import (
    CurrentUserDep,
    DatabaseDep,
    get_current_user,
    get_db,
)
from forum_service.services import theo_doi_service

router = APIRouter(prefix="/theo-doi", tags=["Theo dõi"])


@router.get("/cua-toi")
async def danh_sach_theo_doi_cua_toi(
    db: DatabaseDep,
    current_user: CurrentUserDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    """
    Lay danh sach chu de dang theo doi cua user hien tai.

    Returns:
        Paginated response with ChuDeListItem
    """
    result = await theo_doi_service.danh_sach_cua_toi(
        db=db,
        user=current_user,
        page=page,
        page_size=page_size,
    )
    return {
        "success": True,
        "data": result["items"],
        "pagination": result["pagination"],
    }
