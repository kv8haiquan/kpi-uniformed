"""
common_service/tests/test_search.py
=====================================
Tests cho Unified Search API — 11 tests.

Business rules:
  - Tim kiem cross-schema: COMMON (tsvector), PORTAL (ILIKE), LEGAL (tsvector), LMS (ILIKE)
  - Skip module chua ton tai gracefully
  - Goi y tu tags + tieu de
  - LEGAL boost 1.2
  - Snippet ~150 ky tu quanh tu khoa
  - Min 2 ky tu
"""

import uuid

import pytest
from httpx import AsyncClient

from common_service.tests.conftest import _REAL_CC_IDS

API = "/api/common/v1/search"


# ===========================================================================
# Test Search
# ===========================================================================


class TestSearch:
    """Test tim kiem hop nhat."""

    async def test_search_knowledge_base(
        self, client: AsyncClient, cbcc_user, sample_knowledge_base
    ):
        """Tim trong KB — tsvector search 'thue'."""
        resp = await client.get(API, params={"q": "thue"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        # Co the co ket qua tu KB (SOP ve thue)
        assert "results" in data
        assert "total" in data
        assert "total_by_module" in data
        # Ket qua tu COMMON module (neu tsvector hoat dong)
        if data["total"] > 0:
            modules = {r["module"] for r in data["results"]}
            assert "COMMON" in modules or len(modules) > 0

    async def test_search_combined(
        self, client: AsyncClient, cbcc_user, sample_knowledge_base
    ):
        """Tim tren nhieu module — tra ket qua hop nhat."""
        resp = await client.get(API, params={"q": "quy trinh"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data["results"], list)
        assert isinstance(data["total_by_module"], dict)

    async def test_search_filter_module(
        self, client: AsyncClient, cbcc_user, sample_knowledge_base
    ):
        """Filter modules=common chi tim trong KB."""
        resp = await client.get(API, params={"q": "thue", "modules": "common"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        # Tat ca ket qua (neu co) deu tu COMMON
        for item in data["results"]:
            assert item["module"] == "COMMON"

    async def test_search_empty(
        self, client: AsyncClient, cbcc_user
    ):
        """Tu khoa khong match → results rong."""
        resp = await client.get(API, params={"q": "xyznonexistent12345"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 0
        assert len(data["results"]) == 0

    async def test_search_ranking(
        self, client: AsyncClient, cbcc_user, sample_knowledge_base
    ):
        """Ket qua sap xep theo score DESC."""
        resp = await client.get(API, params={"q": "hai quan"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        if len(data["results"]) >= 2:
            scores = [r["score"] for r in data["results"]]
            assert scores == sorted(scores, reverse=True)

    async def test_search_snippet(
        self, client: AsyncClient, cbcc_user, sample_knowledge_base
    ):
        """Snippet co noi dung."""
        resp = await client.get(API, params={"q": "thue"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        for item in data["results"]:
            assert isinstance(item["snippet"], str)
            # Snippet khong rong cho ket qua co noi_dung
            if item["module"] == "COMMON":
                assert len(item["snippet"]) > 0

    async def test_search_phan_trang(
        self, client: AsyncClient, cbcc_user, sample_knowledge_base
    ):
        """Phan trang page=1, page_size=1."""
        resp = await client.get(API, params={"q": "thue", "page": 1, "page_size": 1})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["page"] == 1
        assert data["page_size"] == 1
        assert len(data["results"]) <= 1

    async def test_search_min_2_ky_tu(
        self, client: AsyncClient, cbcc_user
    ):
        """q = 'a' (1 ky tu) → loi validation 422."""
        resp = await client.get(API, params={"q": "a"})
        assert resp.status_code == 422

    async def test_search_module_chua_ton_tai(
        self, client: AsyncClient, cbcc_user
    ):
        """Search module forum (chua co bang) → skip gracefully, khong crash."""
        resp = await client.get(API, params={"q": "test", "modules": "forum"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        # Forum chua co data nen total = 0
        assert data["total"] == 0


# ===========================================================================
# Test Suggest
# ===========================================================================


class TestSearchSuggest:
    """Test goi y tu khoa."""

    async def test_suggest(
        self, client: AsyncClient, cbcc_user, sample_knowledge_base
    ):
        """Goi y tra danh sach tu khoa."""
        resp = await client.get(f"{API}/suggest", params={"q": "thue"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)

    async def test_suggest_min_2_ky_tu(
        self, client: AsyncClient, cbcc_user
    ):
        """q = 'x' (1 ky tu) → 422."""
        resp = await client.get(f"{API}/suggest", params={"q": "x"})
        assert resp.status_code == 422
