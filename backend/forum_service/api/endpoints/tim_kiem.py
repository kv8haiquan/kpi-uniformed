"""
forum_service/api/endpoints/tim_kiem.py
========================================
Endpoints Tim kiem va Tag suggestions.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from forum_service.dependencies import (
    CurrentUserDep,
    DatabaseDep,
    get_current_user,
    get_db,
)
from forum_service.models import ChuDe
from forum_service.services import chu_de_service

# Router cho tim kiem full-text
search_router = APIRouter(prefix="/tim-kiem", tags=["Tìm kiếm"])

# Router rieng cho tags
tags_router = APIRouter(prefix="/tags", tags=["Tìm kiếm"])


@search_router.get("")
async def tim_kiem_chu_de(
    db: DatabaseDep,
    current_user: CurrentUserDep,
    q: str = Query(..., min_length=2),
    chuyen_muc_id: Optional[UUID] = Query(default=None),
    tags: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    """
    Full-text search cho chu de.

    Query params:
      - q: search query (required, min 2 chars)
      - chuyen_muc_id: filter theo chuyen muc
      - tags: comma-separated tags
      - page, page_size: phan trang
    """
    # Parse tags from comma-separated string
    tags_list = None
    if tags:
        tags_list = [t.strip() for t in tags.split(",") if t.strip()]

    # Su dung service chu_de.danh_sach voi search param
    result = await chu_de_service.danh_sach(
        db=db,
        user=current_user,
        chuyen_muc_id=chuyen_muc_id,
        tags=tags_list,
        search=q,
        sap_xep="moi_nhat",
        page=page,
        page_size=page_size,
    )
    return {
        "success": True,
        "data": result["items"],
        "pagination": result["pagination"],
    }


@tags_router.get("/goi-y")
async def tag_suggestions(
    db: DatabaseDep,
    current_user: CurrentUserDep,
    q: str = Query(..., min_length=1),
) -> dict:
    """
    Lay danh sach tag goi y dua tren prefix match.

    Query:
      - q: prefix tim kiem (VD: "hai" → ["haiquan", "haiphong"])

    Implementation:
      - Query distinct tags tu chu_de.tags (JSONB)
      - Filter prefix match (case-insensitive)
      - Limit 20 suggestions
    """
    # Query distinct tags from JSONB array
    # PostgreSQL: jsonb_array_elements_text(tags) to flatten array
    stmt = (
        select(func.distinct(func.jsonb_array_elements_text(ChuDe.tags)).label("tag"))
        .where(ChuDe.is_deleted == False)
        .where(ChuDe.trang_thai.in_(["MO", "DONG"]))
        .where(text(f"EXISTS (SELECT 1 FROM jsonb_array_elements_text(forum.chu_de.tags) t WHERE LOWER(t::text) LIKE LOWER(:prefix))"))
    )
    stmt = stmt.params(prefix=f"{q}%")
    stmt = stmt.limit(20)

    result = await db.execute(stmt)
    tags = [row[0] for row in result.fetchall() if row[0]]

    return {
        "success": True,
        "data": tags,
        "message": "Lay goi y tag thanh cong",
    }
