"""
common_service/api/endpoints/search.py
=======================================
Public API cho Unified Search.
Prefix: /api/common/v1/search
Auth: JWT Bearer token

Endpoints:
  GET /search          — Tim kiem hop nhat cross-module
  GET /search/suggest  — Goi y tu khoa
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from common_service.dependencies import CurrentUserDep, DatabaseDep
from common_service.schemas.base import SuccessResponse
from common_service.schemas.search import SearchResponse, SearchSuggestion
from common_service.services import search_service

router = APIRouter(prefix="/search", tags=["Tìm kiếm"])


@router.get("", response_model=SuccessResponse[SearchResponse])
async def tim_kiem(
    db: DatabaseDep,
    user: CurrentUserDep,
    q: str = Query(..., min_length=2, description="Tu khoa tim kiem (min 2 ky tu)"),
    modules: Optional[str] = Query(
        default=None,
        description="Comma-separated: lms,forum,legal,portal,common. Mac dinh: tat ca",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """Tim kiem hop nhat cross-module.

    Search trong: Knowledge Base (tsvector), Portal (ILIKE),
    Legal (tsvector), LMS (ILIKE).
    Module chua ton tai se duoc skip (khong loi).
    """
    data = await search_service.tim_kiem(
        db, q,
        modules=modules,
        page=page,
        page_size=page_size,
    )
    return SuccessResponse(data=data)


@router.get("/suggest", response_model=SuccessResponse[SearchSuggestion])
async def goi_y(
    db: DatabaseDep,
    user: CurrentUserDep,
    q: str = Query(..., min_length=2, description="Tu khoa goi y (min 2 ky tu)"),
):
    """Goi y tu khoa tim kiem.

    Goi y tu: tags pho bien, tieu de gan day.
    Toi da 5 goi y.
    """
    data = await search_service.goi_y(db, q)
    return SuccessResponse(data=data)
