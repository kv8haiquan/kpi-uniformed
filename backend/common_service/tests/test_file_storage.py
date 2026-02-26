"""
common_service/tests/test_file_storage.py
==========================================
Tests cho File Storage API — 11 tests.

Business rules:
  - Upload: validate module, mime_type, file size
  - Get: 404 cho khong ton tai hoac da xoa
  - Delete: chi owner hoac ADMIN, soft delete
"""

import io
import uuid

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from common_service.tests.conftest import _REAL_CC_IDS

API = "/api/common/v1/file"


# ===========================================================================
# Helpers
# ===========================================================================


def _make_upload_data(
    filename: str = "test.pdf",
    content: bytes = b"PDF content " * 100,
    content_type: str = "application/pdf",
    module: str = "LMS",
):
    """Tao multipart form data cho upload."""
    return {
        "file": (filename, io.BytesIO(content), content_type),
    }


# ===========================================================================
# Test Upload
# ===========================================================================


class TestFileUpload:
    """Test upload file."""

    @patch("common_service.services.storage_client.upload", new_callable=AsyncMock)
    async def test_upload_file_ok(
        self, mock_upload, client: AsyncClient, cbcc_user, db_session
    ):
        """Upload PDF thanh cong, metadata luu DB."""
        mock_upload.return_value = None
        content = b"PDF content test " * 50  # ~850 bytes
        resp = await client.post(
            f"{API}/upload",
            files={"file": ("report.pdf", io.BytesIO(content), "application/pdf")},
            data={"module": "LMS"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["file_name"] == "report.pdf"
        assert data["mime_type"] == "application/pdf"
        assert data["module"] == "LMS"
        assert data["file_url"] is not None

    @patch("common_service.services.storage_client.upload", new_callable=AsyncMock)
    async def test_upload_file_qua_lon(
        self, mock_upload, client: AsyncClient, cbcc_user, db_session
    ):
        """File qua lon → 400 CMN_ERR_001."""
        # Image > 10MB
        big_content = b"x" * (11 * 1024 * 1024)
        resp = await client.post(
            f"{API}/upload",
            files={"file": ("big.png", io.BytesIO(big_content), "image/png")},
            data={"module": "PORTAL"},
        )
        assert resp.status_code == 400
        error = resp.json()["detail"]["error"]
        assert error["code"] == "CMN_ERR_001"

    async def test_upload_mime_khong_hop_le(
        self, client: AsyncClient, cbcc_user, db_session
    ):
        """File .exe → 400 CMN_ERR_002."""
        resp = await client.post(
            f"{API}/upload",
            files={"file": ("virus.exe", io.BytesIO(b"MZ..."), "application/octet-stream")},
            data={"module": "LMS"},
        )
        assert resp.status_code == 400
        error = resp.json()["detail"]["error"]
        assert error["code"] == "CMN_ERR_002"

    async def test_upload_module_khong_hop_le(
        self, client: AsyncClient, cbcc_user, db_session
    ):
        """Module=INVALID → 400 CMN_ERR_004."""
        resp = await client.post(
            f"{API}/upload",
            files={"file": ("test.pdf", io.BytesIO(b"PDF"), "application/pdf")},
            data={"module": "INVALID"},
        )
        assert resp.status_code == 400
        error = resp.json()["detail"]["error"]
        assert error["code"] == "CMN_ERR_004"

    @patch("common_service.services.storage_client.upload", new_callable=AsyncMock)
    async def test_file_size_limit_theo_loai(
        self, mock_upload, client: AsyncClient, cbcc_user, db_session
    ):
        """Document > 50MB → 400, nhung image 10MB limit khac."""
        # Doc > 50MB
        big_doc = b"x" * (51 * 1024 * 1024)
        resp = await client.post(
            f"{API}/upload",
            files={"file": ("big.pdf", io.BytesIO(big_doc), "application/pdf")},
            data={"module": "LMS"},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"]["code"] == "CMN_ERR_001"


# ===========================================================================
# Test Get file info
# ===========================================================================


class TestFileGetInfo:
    """Test lay thong tin file."""

    async def test_get_file_info(
        self, client: AsyncClient, cbcc_user, sample_file_storage
    ):
        """Tra metadata dung cho file chua xoa."""
        file_id = sample_file_storage[0]["id"]  # report.pdf, chua xoa
        resp = await client.get(f"{API}/{file_id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["file_name"] == "report.pdf"
        assert data["module"] == "LMS"
        assert data["is_deleted"] is False

    async def test_get_file_not_found(
        self, client: AsyncClient, cbcc_user
    ):
        """File khong ton tai → 404."""
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"{API}/{fake_id}")
        assert resp.status_code == 404

    async def test_get_file_da_xoa(
        self, client: AsyncClient, cbcc_user, sample_file_storage
    ):
        """File da xoa (is_deleted=True) → 404."""
        deleted_file_id = sample_file_storage[2]["id"]  # deleted.docx
        resp = await client.get(f"{API}/{deleted_file_id}")
        assert resp.status_code == 404


# ===========================================================================
# Test Delete file
# ===========================================================================


class TestFileDelete:
    """Test xoa file (soft delete)."""

    async def test_delete_file_owner(
        self, client: AsyncClient, cbcc_user, sample_file_storage
    ):
        """Nguoi upload xoa OK."""
        file_id = sample_file_storage[0]["id"]
        resp = await client.delete(f"{API}/{file_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted"] is True

        # Verify: get tra 404 sau khi xoa
        get_resp = await client.get(f"{API}/{file_id}")
        assert get_resp.status_code == 404

    async def test_delete_file_admin(
        self, client: AsyncClient, admin_user, sample_file_storage
    ):
        """ADMIN xoa file cua nguoi khac OK."""
        file_id = sample_file_storage[0]["id"]
        resp = await client.delete(f"{API}/{file_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted"] is True

    async def test_delete_file_nguoi_khac(
        self, client: AsyncClient, chuyen_gia_user, sample_file_storage
    ):
        """Nguoi khac (khong phai owner, khong phai admin) → 403."""
        file_id = sample_file_storage[0]["id"]  # upload boi cbcc_user (idx=0)
        resp = await client.delete(f"{API}/{file_id}")
        assert resp.status_code == 403
