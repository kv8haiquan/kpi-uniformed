"""
common_service/schemas/search.py
=================================
Pydantic schemas cho Unified Search.

Schemas:
  - SearchResultItem: 1 ket qua tim kiem
  - SearchResponse: danh sach ket qua + phan trang + tong hop module
  - SearchSuggestion: goi y tu khoa
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """1 ket qua tim kiem."""

    module: str = Field(description="LEGAL, FORUM, LMS, PORTAL, COMMON")
    type: str = Field(description="VAN_BAN, CHU_DE, KHOA_HOC, BAI_VIET, SOP, FAQ")
    id: uuid.UUID
    title: str
    snippet: str = Field(description="Trich doan co highlight (~150 ky tu)")
    link: str = Field(description="URL frontend de navigate")
    score: float = Field(description="Diem xep hang")


class SearchResponse(BaseModel):
    """Ket qua tim kiem hop nhat tu nhieu module."""

    results: list[SearchResultItem] = []
    total_by_module: dict[str, int] = Field(
        default_factory=dict,
        description="So ket qua theo module: {'LEGAL': 5, 'PORTAL': 3, ...}",
    )
    total: int = 0
    page: int = 1
    page_size: int = 20


class SearchSuggestion(BaseModel):
    """Goi y tu khoa tim kiem."""

    suggestions: list[str] = Field(
        default_factory=list,
        description="Danh sach goi y (toi da 5)",
    )
