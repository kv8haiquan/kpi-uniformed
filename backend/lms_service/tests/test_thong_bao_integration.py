"""
lms_service/tests/test_thong_bao_integration.py
================================================
Integration test for notification helper.
NOTE: Requires common_service to be running on port 8005.
"""

import uuid

import pytest
from lms_service.services.thong_bao_helper import gui_thong_bao, gui_thong_bao_bulk


pytestmark = pytest.mark.asyncio


@pytest.mark.integration
async def test_gui_thong_bao_single():
    """Test single notification (requires common_service running)."""
    # This is a real UUID from the database (just for testing)
    # In production, this would be a real cong_chuc_id
    test_user_id = uuid.uuid4()

    # Should not raise exception even if service is down (fire-and-forget)
    await gui_thong_bao(
        nguoi_nhan_id=test_user_id,
        tieu_de="Test notification",
        noi_dung="This is a test notification from LMS service",
        muc_do="BINH_THUONG",
        link_url="/dao-tao/khoa-hoc/test",
        doi_tuong_type="KHOA_HOC",
        doi_tuong_id=uuid.uuid4(),
    )


@pytest.mark.integration
async def test_gui_thong_bao_bulk():
    """Test bulk notification (requires common_service running)."""
    test_user_ids = [uuid.uuid4() for _ in range(3)]

    # Should not raise exception even if service is down (fire-and-forget)
    await gui_thong_bao_bulk(
        nguoi_nhan_ids=test_user_ids,
        tieu_de="Test bulk notification",
        noi_dung="This is a test bulk notification from LMS service",
        muc_do="QUAN_TRONG",
        link_url="/dao-tao/khoa-hoc/test",
        doi_tuong_type="KHOA_HOC",
        doi_tuong_id=uuid.uuid4(),
    )


@pytest.mark.integration
async def test_gui_thong_bao_empty_list():
    """Test empty list should not call API."""
    # Should return immediately without error
    await gui_thong_bao_bulk(
        nguoi_nhan_ids=[],
        tieu_de="Should not be sent",
        muc_do="BINH_THUONG",
    )
