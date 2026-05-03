"""
Test Module 3 — Tài liệu họp (filesystem MVP).

Tests verify:
- Upload PDF → DB row + file vật lý tạo trong uploads/meeting/
- List trả URL_xem có short-lived token
- View → audit VIEW_DOC
- Download có check cho_phep_tai
- Soft delete chỉ flag is_deleted
"""

from __future__ import annotations

import io
import os
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.config import settings


BASE_CUOC_HOP = "/api/v1/hop-khong-giay/cuoc-hop"
BASE_TAI_LIEU = "/api/v1/hop-khong-giay/tai-lieu"


def _create_meeting_payload(don_vi_id, chu_toa_id):
    return {
        "tieu_de": "Test G3 — Họp upload tài liệu",
        "khoi": "CHUYEN_MON",
        "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": "2026-05-20",
        "gio_bat_dau": "08:30",
        "don_vi_to_chuc_id": str(don_vi_id),
        "chu_toa_id": str(chu_toa_id),
        "thanh_phan": [],
    }


@pytest.fixture
def cleanup_uploads():
    """No-op fixture (giữ signature cho backward compat).

    G4-fix-8: tmpdir cô lập đã được set ở conftest.py — toàn bộ test
    upload vào tmpdir và auto-clean khi session end. Fixture này không
    cần xóa gì nữa.
    """
    yield


# ════════════════════════════════════════════════════════════════════
# HAPPY PATH
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_upload_pdf_creates_db_row_and_file(
    client: AsyncClient, chu_toa_user, seed_test_users, cleanup_uploads,
):
    # Tạo cuộc họp trước
    create = await client.post(
        BASE_CUOC_HOP + "/",
        json=_create_meeting_payload(seed_test_users["don_vi_a"], chu_toa_user.sub),
    )
    ch_id = create.json()["data"]["id"]

    # Upload 1 file giả
    fake_pdf = b"%PDF-1.4 fake content for test\n"
    files = {"file": ("smoke.pdf", io.BytesIO(fake_pdf), "application/pdf")}
    data = {"cuoc_hop_id": ch_id, "phan_quyen": "CONG_KHAI"}

    resp = await client.post(BASE_TAI_LIEU + "/upload", data=data, files=files)
    assert resp.status_code == 201, resp.text

    body = resp.json()["data"]
    assert body["ten_tai_lieu"] == "smoke.pdf"
    assert body["file_size"] == len(fake_pdf)
    assert body["minio_bucket"] == "meeting"
    assert body["minio_key"].startswith(f"tai-lieu/{ch_id}/")
    assert body["extension"] == "pdf"

    # Verify file vật lý tồn tại
    full_path = Path(settings.upload_dir) / body["minio_key"]
    assert full_path.is_file(), f"File not on disk: {full_path}"
    assert full_path.read_bytes() == fake_pdf


@pytest.mark.asyncio
async def test_list_tai_lieu_includes_url_xem(
    client: AsyncClient, chu_toa_user, seed_test_users, cleanup_uploads,
):
    create = await client.post(
        BASE_CUOC_HOP + "/",
        json=_create_meeting_payload(seed_test_users["don_vi_a"], chu_toa_user.sub),
    )
    ch_id = create.json()["data"]["id"]

    files = {"file": ("a.pdf", io.BytesIO(b"%PDF-1"), "application/pdf")}
    await client.post(BASE_TAI_LIEU + "/upload",
                       data={"cuoc_hop_id": ch_id}, files=files)

    resp = await client.get(f"{BASE_CUOC_HOP}/{ch_id}/tai-lieu")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert len(items) == 1
    assert items[0]["url_xem"].startswith(
        f"/api/v1/hop-khong-giay/tai-lieu/{items[0]['id']}/xem-noi-dung?t="
    )


@pytest.mark.asyncio
async def test_view_endpoint_audit_view_doc(
    client: AsyncClient, chu_toa_user, seed_test_users,
    db_session: AsyncSession, cleanup_uploads,
):
    create = await client.post(
        BASE_CUOC_HOP + "/",
        json=_create_meeting_payload(seed_test_users["don_vi_a"], chu_toa_user.sub),
    )
    ch_id = create.json()["data"]["id"]

    files = {"file": ("b.pdf", io.BytesIO(b"%PDF-1"), "application/pdf")}
    up = await client.post(BASE_TAI_LIEU + "/upload",
                            data={"cuoc_hop_id": ch_id}, files=files)
    tl_id = up.json()["data"]["id"]

    resp = await client.get(f"{BASE_TAI_LIEU}/{tl_id}/xem")
    assert resp.status_code == 200, resp.text
    assert "url" in resp.json()["data"]

    # Verify audit
    res = await db_session.execute(sa_text("""
        SELECT COUNT(*) FROM common.audit_log
         WHERE module='MEETING' AND hanh_dong='VIEW_DOC'
           AND doi_tuong_id=:tl_id
    """), {"tl_id": tl_id})
    assert res.scalar() == 1


@pytest.mark.asyncio
async def test_download_blocked_when_cho_phep_tai_false(
    client: AsyncClient, chu_toa_user, seed_test_users, cleanup_uploads,
):
    create = await client.post(
        BASE_CUOC_HOP + "/",
        json=_create_meeting_payload(seed_test_users["don_vi_a"], chu_toa_user.sub),
    )
    ch_id = create.json()["data"]["id"]

    files = {"file": ("c.pdf", io.BytesIO(b"x"), "application/pdf")}
    up = await client.post(
        BASE_TAI_LIEU + "/upload",
        data={"cuoc_hop_id": ch_id, "cho_phep_tai": "false"},
        files=files,
    )
    tl_id = up.json()["data"]["id"]

    resp = await client.get(f"{BASE_TAI_LIEU}/{tl_id}/tai")
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"]["code"] == "DOWNLOAD_DISABLED"


@pytest.mark.asyncio
async def test_soft_delete_marks_is_deleted(
    client: AsyncClient, chu_toa_user, seed_test_users,
    db_session: AsyncSession, cleanup_uploads,
):
    create = await client.post(
        BASE_CUOC_HOP + "/",
        json=_create_meeting_payload(seed_test_users["don_vi_a"], chu_toa_user.sub),
    )
    ch_id = create.json()["data"]["id"]

    files = {"file": ("d.pdf", io.BytesIO(b"x"), "application/pdf")}
    up = await client.post(BASE_TAI_LIEU + "/upload",
                            data={"cuoc_hop_id": ch_id}, files=files)
    tl_id = up.json()["data"]["id"]

    resp = await client.delete(f"{BASE_TAI_LIEU}/{tl_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["is_deleted"] is True

    # Verify list không còn trả về
    list_resp = await client.get(f"{BASE_CUOC_HOP}/{ch_id}/tai-lieu")
    assert all(item["id"] != tl_id for item in list_resp.json()["data"])


# ════════════════════════════════════════════════════════════════════
# PERMISSION
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_upload_blocked_for_non_chu_toa_thu_ky(
    client: AsyncClient, admin_user, seed_test_users, cbcc_user, cleanup_uploads,
):
    # admin tạo cuộc họp
    create = await client.post(
        BASE_CUOC_HOP + "/",
        json=_create_meeting_payload(seed_test_users["don_vi_a"], admin_user.sub),
    )
    ch_id = create.json()["data"]["id"]

    # Switch → cbcc_user (không phải chu_toa/thu_ky/admin)
    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    async def _override():
        return cbcc_user
    fastapi_app.dependency_overrides[get_current_user] = _override

    files = {"file": ("hack.pdf", io.BytesIO(b"x"), "application/pdf")}
    resp = await client.post(BASE_TAI_LIEU + "/upload",
                              data={"cuoc_hop_id": ch_id}, files=files)
    assert resp.status_code == 403


# ════════════════════════════════════════════════════════════════════
# VALIDATION
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_upload_reject_invalid_extension(
    client: AsyncClient, chu_toa_user, seed_test_users, cleanup_uploads,
):
    create = await client.post(
        BASE_CUOC_HOP + "/",
        json=_create_meeting_payload(seed_test_users["don_vi_a"], chu_toa_user.sub),
    )
    ch_id = create.json()["data"]["id"]

    files = {"file": ("evil.exe", io.BytesIO(b"MZ"), "application/x-msdownload")}
    resp = await client.post(BASE_TAI_LIEU + "/upload",
                              data={"cuoc_hop_id": ch_id}, files=files)
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "UPLOAD_002"
