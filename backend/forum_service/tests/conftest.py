"""
forum_service/tests/conftest.py
================================
Test fixtures cho module Dien dan.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from shared.auth import TokenPayload


@pytest.fixture
def mock_cong_chuc() -> TokenPayload:
    """Mock user: Cong chuc thuong."""
    return TokenPayload(
        sub="00000000-0000-0000-0000-000000000001",
        ma_cc="20ZZ-0001",
        vai_tro="CC",
        don_vi_id="00000000-0000-0000-0000-000000000101",
        is_lanh_dao=False,
        platform_roles=[],
    )


@pytest.fixture
def mock_giang_vien() -> TokenPayload:
    """Mock user: Giang vien kiem nhiem."""
    return TokenPayload(
        sub="00000000-0000-0000-0000-000000000002",
        ma_cc="20ZZ-0002",
        vai_tro="CC",
        don_vi_id="00000000-0000-0000-0000-000000000101",
        is_lanh_dao=False,
        platform_roles=["GIANG_VIEN"],
    )


@pytest.fixture
def mock_lanh_dao() -> TokenPayload:
    """Mock user: Lanh dao don vi."""
    return TokenPayload(
        sub="00000000-0000-0000-0000-000000000003",
        ma_cc="20ZZ-0003",
        vai_tro="TDV",
        don_vi_id="00000000-0000-0000-0000-000000000101",
        is_lanh_dao=True,
        platform_roles=[],
    )


@pytest.fixture
def mock_admin() -> TokenPayload:
    """Mock user: Quan tri he thong."""
    return TokenPayload(
        sub="00000000-0000-0000-0000-000000000004",
        ma_cc="admin",
        vai_tro="SUPER_ADMIN",
        don_vi_id=None,
        is_lanh_dao=False,
        platform_roles=["QT_ATTT"],
    )
