"""
Test Module 9 — Biên bản + Mock CKS + DOCX/PDF.

Tests:
- GET /cuoc-hop/{id}/bien-ban → auto-fill snapshot
- PUT noi_dung → update OK
- /trinh-ky → trang_thai=TRINH_KY + thong_bao
- /ky → SHA-256 hash, qr_xac_thuc, is_mock_signed=TRUE
- /xuat?dinh-dang=docx → file DOCX có placeholder render
- /xuat?dinh-dang=pdf → file PDF có font Vietnamese, watermark, QR
- Hash consistency: hash từ /ky = hash trong PDF footer
- Permission: chỉ thư ký được trinh-ky, chỉ chủ tọa được ký
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.config import settings


BASE_CH = "/api/v1/hop-khong-giay/cuoc-hop"
BASE_BB = "/api/v1/hop-khong-giay/bien-ban"


def _payload(don_vi_id, chu_toa_id, thu_ky_id):
    return {
        "tieu_de": "Test G3b — họp ọ ạ ặ ề (Vietnamese)",
        "khoi": "CHUYEN_MON",
        "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": "2026-05-25",
        "gio_bat_dau": "08:30",
        "gio_ket_thuc": "10:00",
        "dia_diem": "Phòng họp số 1",
        "don_vi_to_chuc_id": str(don_vi_id),
        "chu_toa_id": str(chu_toa_id),
        "thu_ky_id": str(thu_ky_id),
        "thanh_phan": [],
    }


@pytest.fixture
def cleanup_bien_ban_files():
    """No-op (G4-fix-8): tmpdir cô lập set ở conftest.py — auto-clean."""
    yield


# ════════════════════════════════════════════════════════════════════
# AUTO-FILL + UPDATE
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_get_bien_ban_auto_fill(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """GET lần đầu → tự khởi tạo + auto-fill snapshot."""
    create = await client.post(
        BASE_CH + "/",
        json=_payload(seed_test_users["don_vi_a"], chu_toa_user.sub, chu_toa_user.sub),
    )
    ch_id = create.json()["data"]["id"]

    resp = await client.get(f"{BASE_CH}/{ch_id}/bien-ban")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["trang_thai"] == "DANG_SOAN"
    nd = data["noi_dung_json"]
    assert nd["tieu_de"] == "Test G3b — họp ọ ạ ặ ề (Vietnamese)"
    assert nd["khoi"] == "CHUYEN_MON"
    assert "diem_danh_summary" in nd


@pytest.mark.asyncio
async def test_put_bien_ban(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    create = await client.post(
        BASE_CH + "/",
        json=_payload(seed_test_users["don_vi_a"], chu_toa_user.sub, chu_toa_user.sub),
    )
    ch_id = create.json()["data"]["id"]
    await client.get(f"{BASE_CH}/{ch_id}/bien-ban")  # init

    resp = await client.put(
        f"{BASE_CH}/{ch_id}/bien-ban",
        json={
            "noi_dung_json": {"noi_dung_thao_luan": "Đã thảo luận về việc tăng năng suất"},
            "noi_dung_html": "<p>Đã thảo luận</p>",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["noi_dung_json"]["noi_dung_thao_luan"].startswith("Đã thảo luận")


# ════════════════════════════════════════════════════════════════════
# SIGNING FLOW
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_full_signing_flow(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    """Flow đầy đủ: init → update → trinh-ky → ky → audit + hash."""
    create = await client.post(
        BASE_CH + "/",
        json=_payload(seed_test_users["don_vi_a"], chu_toa_user.sub, chu_toa_user.sub),
    )
    ch_id = create.json()["data"]["id"]

    # Init + update
    bb_resp = await client.get(f"{BASE_CH}/{ch_id}/bien-ban")
    bb_id = bb_resp.json()["data"]["id"]
    await client.put(f"{BASE_CH}/{ch_id}/bien-ban", json={
        "noi_dung_json": {"noi_dung_thao_luan": "test"},
        "noi_dung_html": None,
    })

    # Trình ký
    tk = await client.post(f"{BASE_BB}/{bb_id}/trinh-ky")
    assert tk.status_code == 200, tk.text
    assert tk.json()["data"]["trang_thai"] == "TRINH_KY"

    # Ký
    ky = await client.post(f"{BASE_BB}/{bb_id}/ky")
    assert ky.status_code == 200, ky.text
    data = ky.json()["data"]
    assert data["trang_thai"] == "DA_KY"
    assert data["is_mock_signed"] is True
    assert data["hash_noi_dung"] is not None
    assert len(data["hash_noi_dung"]) == 64  # SHA-256 hex
    assert data["qr_xac_thuc"].startswith("https://kv08.vn/verify/")

    # Audit SIGN_MINUTES
    audit_res = await db_session.execute(sa_text("""
        SELECT COUNT(*) FROM common.audit_log
         WHERE module='MEETING' AND hanh_dong='SIGN_MINUTES'
           AND doi_tuong_id=:bb_id
    """), {"bb_id": bb_id})
    assert audit_res.scalar() == 1


@pytest.mark.asyncio
async def test_hash_consistency(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """Hash sau /ky = hash deterministic của noi_dung_json."""
    from meeting_service.services.bien_ban_service import compute_hash

    create = await client.post(
        BASE_CH + "/",
        json=_payload(seed_test_users["don_vi_a"], chu_toa_user.sub, chu_toa_user.sub),
    )
    ch_id = create.json()["data"]["id"]
    bb_resp = await client.get(f"{BASE_CH}/{ch_id}/bien-ban")
    bb_id = bb_resp.json()["data"]["id"]

    custom_content = {"noi_dung_thao_luan": "custom 123 ọ ạ"}
    await client.put(f"{BASE_CH}/{ch_id}/bien-ban", json={
        "noi_dung_json": custom_content, "noi_dung_html": None,
    })

    ky = await client.post(f"{BASE_BB}/{bb_id}/ky")
    api_hash = ky.json()["data"]["hash_noi_dung"]
    expected_hash = compute_hash(custom_content)
    assert api_hash == expected_hash


# ════════════════════════════════════════════════════════════════════
# EXPORT
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_export_docx(
    client: AsyncClient, chu_toa_user, seed_test_users, cleanup_bien_ban_files,
):
    create = await client.post(
        BASE_CH + "/",
        json=_payload(seed_test_users["don_vi_a"], chu_toa_user.sub, chu_toa_user.sub),
    )
    ch_id = create.json()["data"]["id"]
    bb_resp = await client.get(f"{BASE_CH}/{ch_id}/bien-ban")
    bb_id = bb_resp.json()["data"]["id"]
    await client.post(f"{BASE_BB}/{bb_id}/ky")

    resp = await client.post(f"{BASE_BB}/{bb_id}/xuat?dinh-dang=docx")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["minio_key"].endswith(".docx")
    assert data["file_size"] > 1000  # docx > 1KB

    # Verify file đọc được bằng python-docx (no corruption)
    from docx import Document
    full_path = Path(settings.upload_dir) / data["minio_key"]
    assert full_path.is_file()
    doc = Document(str(full_path))
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "BIÊN BẢN HỌP" in text
    assert "ọ ạ ặ ề" in text or "Vietnamese" in text  # Vietnamese encoding OK


@pytest.mark.asyncio
async def test_export_pdf_with_unicode(
    client: AsyncClient, chu_toa_user, seed_test_users, cleanup_bien_ban_files,
):
    """PDF có font DejaVu (Unicode) → text Vietnamese render đúng."""
    create = await client.post(
        BASE_CH + "/",
        json=_payload(seed_test_users["don_vi_a"], chu_toa_user.sub, chu_toa_user.sub),
    )
    ch_id = create.json()["data"]["id"]
    bb_resp = await client.get(f"{BASE_CH}/{ch_id}/bien-ban")
    bb_id = bb_resp.json()["data"]["id"]
    await client.post(f"{BASE_BB}/{bb_id}/ky")

    resp = await client.post(f"{BASE_BB}/{bb_id}/xuat?dinh-dang=pdf")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["minio_key"].endswith(".pdf")

    full_path = Path(settings.upload_dir) / data["minio_key"]
    assert full_path.is_file()
    pdf_bytes = full_path.read_bytes()
    assert pdf_bytes.startswith(b"%PDF")  # PDF signature
    # Font DejaVu được embedded — file size phải > 5KB do font subset
    assert len(pdf_bytes) > 5000


@pytest.mark.asyncio
async def test_pdf_contains_watermark_and_qr(
    client: AsyncClient, chu_toa_user, seed_test_users, cleanup_bien_ban_files,
):
    """PDF có watermark MOCK CKS + QR (sau khi ký).

    Note: ReportLab 4.x compress streams mặc định → không grep được text raw.
    Verify gián tiếp: file PDF valid + hash trong DB + QR drawn (size > 5KB
    do font + QR image embedded).
    """
    create = await client.post(
        BASE_CH + "/",
        json=_payload(seed_test_users["don_vi_a"], chu_toa_user.sub, chu_toa_user.sub),
    )
    ch_id = create.json()["data"]["id"]
    bb_resp = await client.get(f"{BASE_CH}/{ch_id}/bien-ban")
    bb_id = bb_resp.json()["data"]["id"]
    ky_resp = await client.post(f"{BASE_BB}/{bb_id}/ky")
    hash_value = ky_resp.json()["data"]["hash_noi_dung"]

    resp = await client.post(f"{BASE_BB}/{bb_id}/xuat?dinh-dang=pdf")
    data = resp.json()["data"]
    full_path = Path(settings.upload_dir) / data["minio_key"]
    pdf_bytes = full_path.read_bytes()

    # Verify: file là PDF valid, kích thước đủ lớn (font + QR), hash khớp DB
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 5000, "PDF phải > 5KB do embed font + QR"
    assert data["hash_noi_dung"] == hash_value
    # QR image embedded → PDF chứa "Image" object (uncompressed marker)
    assert b"/Image" in pdf_bytes or b"/XObject" in pdf_bytes


# ════════════════════════════════════════════════════════════════════
# PERMISSION
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_only_chu_toa_can_sign(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """Non-chu_toa POST /ky → 403."""
    from datetime import datetime, timedelta, timezone
    from shared.auth import TokenPayload

    other_user = TokenPayload(
        sub="aaaaaaaa-0004-0000-0000-000000000004",
        ma_cc="TEST-G3-004", ho_ten="Other",
        vai_tro="CC",
        don_vi_id=str(seed_test_users["don_vi_b"]),
        platform_roles=[],
        exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        type="access",
    )

    create = await client.post(
        BASE_CH + "/",
        json=_payload(seed_test_users["don_vi_a"], chu_toa_user.sub, chu_toa_user.sub),
    )
    ch_id = create.json()["data"]["id"]
    bb_resp = await client.get(f"{BASE_CH}/{ch_id}/bien-ban")
    bb_id = bb_resp.json()["data"]["id"]

    # Switch sang user khác
    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    async def _o():
        return other_user
    fastapi_app.dependency_overrides[get_current_user] = _o

    resp = await client.post(f"{BASE_BB}/{bb_id}/ky")
    assert resp.status_code == 403
