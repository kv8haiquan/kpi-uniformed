"""
lms_service/tests/test_upload.py
==================================
Tests cho upload endpoints:
  POST /api/v1/lms/upload/file
  POST /api/v1/lms/upload/files

Dung monkeypatch de redirect upload_dir sang tmp_path, khong can cleanup thu cong.
"""

import io
import pytest
import lms_service.config as lms_config
from httpx import AsyncClient

# URL goc cua endpoint
UPLOAD_FILE_URL = "/api/v1/lms/upload/file"
UPLOAD_FILES_URL = "/api/v1/lms/upload/files"


# =========================================================================
# HELPER
# =========================================================================

def _pdf_file(name: str = "test.pdf", content: bytes = b"%PDF-1.4 test"):
    """Tao tuple file de dung trong httpx multipart."""
    return (name, io.BytesIO(content), "application/pdf")


def _png_file(name: str = "cover.png"):
    return (name, io.BytesIO(b"\x89PNG\r\n\x1a\n fake png"), "image/png")


# =========================================================================
# TEST: Upload 1 file — thanh cong
# =========================================================================

@pytest.mark.asyncio
async def test_upload_pdf_success(client: AsyncClient, qt_dao_tao_user, tmp_path, monkeypatch):
    """Upload file PDF hop le — tra ve 200 voi thong tin file."""
    monkeypatch.setattr(lms_config.settings, "upload_dir", str(tmp_path))

    content = b"%PDF-1.4 noi dung test"
    resp = await client.post(
        f"{UPLOAD_FILE_URL}?folder=bai-hoc",
        files={"file": _pdf_file(content=content)},
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["file_name"] == "test.pdf"
    assert data["data"]["file_url"].startswith("/uploads/lms/bai-hoc/")
    assert data["data"]["file_size"] == len(content)
    assert data["data"]["content_type"] == "application/pdf"


@pytest.mark.asyncio
async def test_upload_image_success(client: AsyncClient, giang_vien_user, tmp_path, monkeypatch):
    """GIANG_VIEN co the upload anh PNG."""
    monkeypatch.setattr(lms_config.settings, "upload_dir", str(tmp_path))

    resp = await client.post(
        f"{UPLOAD_FILE_URL}?folder=anh-bia",
        files={"file": _png_file()},
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["file_url"].startswith("/uploads/lms/anh-bia/")


@pytest.mark.asyncio
async def test_upload_default_folder(client: AsyncClient, qt_dao_tao_user, tmp_path, monkeypatch):
    """Khong truyen folder — luu vao sub-folder 'general'."""
    monkeypatch.setattr(lms_config.settings, "upload_dir", str(tmp_path))

    resp = await client.post(
        UPLOAD_FILE_URL,
        files={"file": _pdf_file()},
    )

    assert resp.status_code == 200
    assert "/uploads/lms/general/" in resp.json()["data"]["file_url"]


# =========================================================================
# TEST: Upload 1 file — loi
# =========================================================================

@pytest.mark.asyncio
async def test_upload_invalid_extension(client: AsyncClient, qt_dao_tao_user, tmp_path, monkeypatch):
    """File .exe khong duoc ho tro — tra ve 400."""
    monkeypatch.setattr(lms_config.settings, "upload_dir", str(tmp_path))

    resp = await client.post(
        UPLOAD_FILE_URL,
        files={"file": ("malware.exe", io.BytesIO(b"MZ..."), "application/octet-stream")},
    )

    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert detail["error"]["code"] == "UPLOAD_002"


@pytest.mark.asyncio
async def test_upload_file_too_large(client: AsyncClient, qt_dao_tao_user, tmp_path, monkeypatch):
    """File vuot qua MAX_FILE_SIZE_MB — tra ve 400."""
    monkeypatch.setattr(lms_config.settings, "upload_dir", str(tmp_path))
    # Dat gio han xuong 1 byte de test
    monkeypatch.setattr(lms_config.settings, "max_file_size_mb", 0)

    resp = await client.post(
        UPLOAD_FILE_URL,
        files={"file": _pdf_file(content=b"%PDF large content")},
    )

    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert detail["error"]["code"] == "UPLOAD_003"


# =========================================================================
# TEST: Phan quyen
# =========================================================================

@pytest.mark.asyncio
async def test_upload_forbidden_for_cbcc(client: AsyncClient, cbcc_user):
    """CBCC thuong khong co quyen upload — 403."""
    resp = await client.post(
        UPLOAD_FILE_URL,
        files={"file": _pdf_file()},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_upload_forbidden_for_lanh_dao(client: AsyncClient, lanh_dao_user):
    """Lanh dao khong co platform role GIANG_VIEN/QT_DAO_TAO — 403."""
    resp = await client.post(
        UPLOAD_FILE_URL,
        files={"file": _pdf_file()},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_upload_allowed_for_admin(client: AsyncClient, admin_user, tmp_path, monkeypatch):
    """Admin (SUPER_ADMIN) bypass kiem tra role — 200."""
    monkeypatch.setattr(lms_config.settings, "upload_dir", str(tmp_path))

    resp = await client.post(
        UPLOAD_FILE_URL,
        files={"file": _pdf_file()},
    )
    assert resp.status_code == 200


# =========================================================================
# TEST: Upload nhieu file
# =========================================================================

@pytest.mark.asyncio
async def test_upload_multiple_files(client: AsyncClient, qt_dao_tao_user, tmp_path, monkeypatch):
    """Upload 2 file cung luc — tra ve danh sach 2 ket qua."""
    monkeypatch.setattr(lms_config.settings, "upload_dir", str(tmp_path))

    resp = await client.post(
        f"{UPLOAD_FILES_URL}?folder=tai-lieu",
        files=[
            ("files", _pdf_file("doc1.pdf", b"PDF content 1")),
            ("files", _pdf_file("doc2.pdf", b"PDF content 2")),
        ],
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert len(data["data"]) == 2
    names = [r["file_name"] for r in data["data"]]
    assert "doc1.pdf" in names
    assert "doc2.pdf" in names


@pytest.mark.asyncio
async def test_upload_multiple_files_forbidden(client: AsyncClient, cbcc_user):
    """CBCC khong duoc upload nhieu file — 403."""
    resp = await client.post(
        UPLOAD_FILES_URL,
        files=[("files", _pdf_file())],
    )
    assert resp.status_code == 403


# =========================================================================
# TEST: File name uniqueness
# =========================================================================

@pytest.mark.asyncio
async def test_upload_same_file_twice_unique_url(
    client: AsyncClient, qt_dao_tao_user, tmp_path, monkeypatch
):
    """Upload cung ten file 2 lan — file_url phai khac nhau (uuid prefix)."""
    monkeypatch.setattr(lms_config.settings, "upload_dir", str(tmp_path))

    resp1 = await client.post(
        UPLOAD_FILE_URL,
        files={"file": _pdf_file("same.pdf")},
    )
    resp2 = await client.post(
        UPLOAD_FILE_URL,
        files={"file": _pdf_file("same.pdf")},
    )

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    url1 = resp1.json()["data"]["file_url"]
    url2 = resp2.json()["data"]["file_url"]
    assert url1 != url2, "Hai file cung ten phai co URL khac nhau"
