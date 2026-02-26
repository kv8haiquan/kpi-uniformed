"""
common_service/tests/test_knowledge_base.py
=============================================
Tests cho Knowledge Base API — 17 tests.

Business rules:
  - CBCC chi thay DA_XUAT_BAN, ADMIN/CHUYEN_GIA thay tat ca
  - Tao: CHUYEN_GIA, QT_NOI_DUNG, ADMIN (CBCC thuong 403)
  - Sua: chu so huu, QT_NOI_DUNG, ADMIN; sua noi_dung → phien_ban++
  - Workflow: NHAP→CHO_DUYET→DA_XUAT_BAN; CHO_DUYET→NHAP (tu choi)
  - Xoa: soft delete (is_deleted=True)
  - Internal: cap_nhat_van_ban → DA_XUAT_BAN → CAN_CAP_NHAT
"""

import uuid

import pytest
from httpx import AsyncClient

from common_service.tests.conftest import _REAL_CC_IDS, INTERNAL_KEY

API = "/api/common/v1/knowledge-base"
INTERNAL = "/internal/v1/knowledge-base"


# ===========================================================================
# Test Danh sach
# ===========================================================================


class TestKBDanhSach:
    """Test danh sach KB."""

    async def test_danh_sach_cbcc_chi_thay_xuat_ban(
        self, client: AsyncClient, cbcc_user, sample_knowledge_base
    ):
        """CBCC thuong chi thay DA_XUAT_BAN."""
        resp = await client.get(API)
        assert resp.status_code == 200
        items = resp.json()["data"]
        # Chi 2 bai DA_XUAT_BAN (idx=2 va idx=3)
        assert len(items) == 2
        for item in items:
            assert item["trang_thai"] == "DA_XUAT_BAN"

    async def test_danh_sach_admin_thay_tat_ca(
        self, client: AsyncClient, admin_user, sample_knowledge_base
    ):
        """ADMIN thay moi trang thai."""
        resp = await client.get(API)
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert len(items) == 4

    async def test_danh_sach_loc_loai(
        self, client: AsyncClient, admin_user, sample_knowledge_base
    ):
        """Filter loai=SOP."""
        resp = await client.get(API, params={"loai": "SOP"})
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert len(items) == 2
        for item in items:
            assert item["loai"] == "SOP"

    async def test_danh_sach_loc_tags(
        self, client: AsyncClient, admin_user, sample_knowledge_base
    ):
        """Filter tags=XNK."""
        resp = await client.get(API, params={"tags": "XNK"})
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert len(items) >= 1
        # Tag XNK co trong bai dau tien (SOP Quy trinh XNK)
        assert any("XNK" in item.get("tags", []) for item in items)

    async def test_danh_sach_chuyen_gia_thay_tat_ca(
        self, client: AsyncClient, chuyen_gia_user, sample_knowledge_base
    ):
        """CHUYEN_GIA thay moi trang thai (nam trong KB_VIEW_ALL_ROLES)."""
        resp = await client.get(API)
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert len(items) == 4


# ===========================================================================
# Test Chi tiet
# ===========================================================================


class TestKBChiTiet:
    """Test chi tiet KB."""

    async def test_chi_tiet(
        self, client: AsyncClient, cbcc_user, sample_knowledge_base
    ):
        """Tra day du fields + lien ket cheo."""
        kb_id = sample_knowledge_base[3]["id"]  # FAQ voi van_ban_lien_quan
        resp = await client.get(f"{API}/{kb_id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["tieu_de"] == "FAQ Ve quy dinh phap luat moi"
        assert data["loai"] == "FAQ"
        assert data["phien_ban"] == 1
        assert data["van_ban_lien_quan"] is not None
        assert len(data["van_ban_lien_quan"]) == 1


# ===========================================================================
# Test Tao KB
# ===========================================================================


class TestKBTao:
    """Test tao KB moi."""

    async def test_tao_chuyen_gia(
        self, client: AsyncClient, chuyen_gia_user, db_session
    ):
        """CHUYEN_GIA tao KB thanh cong → trang_thai=NHAP."""
        resp = await client.post(
            API,
            json={
                "loai": "SOP",
                "tieu_de": "SOP moi cua chuyen gia",
                "noi_dung": "<p>Noi dung SOP moi</p>",
                "tags": ["test_tag"],
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["trang_thai"] == "NHAP"
        assert data["phien_ban"] == 1
        assert data["loai"] == "SOP"

    async def test_tao_cbcc_thuong(
        self, client: AsyncClient, cbcc_user, db_session
    ):
        """CBCC thuong khong co quyen tao → 403."""
        resp = await client.post(
            API,
            json={
                "loai": "FAQ",
                "tieu_de": "FAQ tu CBCC",
                "noi_dung": "<p>Noi dung</p>",
            },
        )
        assert resp.status_code == 403


# ===========================================================================
# Test Sua KB
# ===========================================================================


class TestKBSua:
    """Test sua KB."""

    async def test_sua_chu_so_huu(
        self, client: AsyncClient, chuyen_gia_user, sample_knowledge_base
    ):
        """Chu so huu sua KB cua minh OK."""
        kb_id = sample_knowledge_base[0]["id"]  # NHAP, owner = chuyen_gia (idx=1)
        resp = await client.put(
            f"{API}/{kb_id}",
            json={"tieu_de": "SOP da sua tieu de"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["tieu_de"] == "SOP da sua tieu de"

    async def test_sua_nguoi_khac(
        self, client: AsyncClient, cbcc_user, sample_knowledge_base
    ):
        """CBCC khac sua KB cua chuyen_gia → 403."""
        kb_id = sample_knowledge_base[0]["id"]
        resp = await client.put(
            f"{API}/{kb_id}",
            json={"tieu_de": "Sua trai phep"},
        )
        assert resp.status_code == 403

    async def test_sua_tang_phien_ban(
        self, client: AsyncClient, chuyen_gia_user, sample_knowledge_base
    ):
        """Sua noi_dung → phien_ban tang 1."""
        kb_id = sample_knowledge_base[0]["id"]  # phien_ban = 1
        resp = await client.put(
            f"{API}/{kb_id}",
            json={"noi_dung": "<p>Noi dung moi da cap nhat</p>"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["phien_ban"] == 2  # 1 → 2


# ===========================================================================
# Test Workflow
# ===========================================================================


class TestKBWorkflow:
    """Test doi trang thai — workflow."""

    async def test_workflow_happy(
        self, client: AsyncClient, chuyen_gia_user, qt_noi_dung_user, sample_knowledge_base, db_session
    ):
        """Happy path: NHAP → CHO_DUYET → DA_XUAT_BAN."""
        kb_id = sample_knowledge_base[0]["id"]  # NHAP, owner = chuyen_gia (idx=1)

        # Step 1: NHAP → CHO_DUYET (chu so huu gui duyet)
        from common_service.dependencies import get_current_user
        from common_service.tests.conftest import _make_user, _set_user

        cg = _make_user("CC", ["CHUYEN_GIA"], idx=1)
        _set_user(cg)
        resp1 = await client.patch(
            f"{API}/{kb_id}/trang-thai",
            json={"trang_thai_moi": "CHO_DUYET"},
        )
        assert resp1.status_code == 200
        assert resp1.json()["data"]["trang_thai"] == "CHO_DUYET"

        # Step 2: CHO_DUYET → DA_XUAT_BAN (QT_NOI_DUNG duyet)
        qtn = _make_user("CC", ["QT_NOI_DUNG"], idx=2)
        _set_user(qtn)
        resp2 = await client.patch(
            f"{API}/{kb_id}/trang-thai",
            json={"trang_thai_moi": "DA_XUAT_BAN"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["data"]["trang_thai"] == "DA_XUAT_BAN"

    async def test_workflow_tu_choi(
        self, client: AsyncClient, sample_knowledge_base, db_session
    ):
        """CHO_DUYET → NHAP (QT_NOI_DUNG tu choi)."""
        kb_id = sample_knowledge_base[1]["id"]  # CHO_DUYET
        from common_service.tests.conftest import _make_user, _set_user

        qtn = _make_user("CC", ["QT_NOI_DUNG"], idx=2)
        _set_user(qtn)
        resp = await client.patch(
            f"{API}/{kb_id}/trang-thai",
            json={"trang_thai_moi": "NHAP"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["trang_thai"] == "NHAP"

    async def test_workflow_can_cap_nhat(
        self, client: AsyncClient, admin_user, sample_knowledge_base
    ):
        """DA_XUAT_BAN → CAN_CAP_NHAT."""
        kb_id = sample_knowledge_base[2]["id"]  # DA_XUAT_BAN
        resp = await client.patch(
            f"{API}/{kb_id}/trang-thai",
            json={"trang_thai_moi": "CAN_CAP_NHAT"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["trang_thai"] == "CAN_CAP_NHAT"

    async def test_workflow_sai_buoc(
        self, client: AsyncClient, admin_user, sample_knowledge_base
    ):
        """NHAP → DA_XUAT_BAN truc tiep → loi 400 (phai qua CHO_DUYET)."""
        kb_id = sample_knowledge_base[0]["id"]  # NHAP
        resp = await client.patch(
            f"{API}/{kb_id}/trang-thai",
            json={"trang_thai_moi": "DA_XUAT_BAN"},
        )
        assert resp.status_code == 400


# ===========================================================================
# Test Xoa
# ===========================================================================


class TestKBXoa:
    """Test soft delete."""

    async def test_xoa_soft(
        self, client: AsyncClient, chuyen_gia_user, sample_knowledge_base
    ):
        """Chu so huu xoa → is_deleted=True, get tra 404."""
        kb_id = sample_knowledge_base[0]["id"]
        resp = await client.delete(f"{API}/{kb_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted"] is True

        # Verify: get tra 404
        get_resp = await client.get(f"{API}/{kb_id}")
        assert get_resp.status_code == 404


# ===========================================================================
# Test Internal API
# ===========================================================================


class TestKBInternal:
    """Test Internal API — cap nhat van ban."""

    async def test_internal_cap_nhat_van_ban(
        self, client: AsyncClient, sample_knowledge_base, db_session
    ):
        """Van ban thay doi → KB lien quan DA_XUAT_BAN → CAN_CAP_NHAT."""
        # KB idx=3 co van_ban_lien_quan chua "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        resp = await client.post(
            f"{INTERNAL}/cap-nhat-van-ban",
            json={"van_ban_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"},
            headers={"X-Internal-Key": INTERNAL_KEY},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["updated_count"] >= 1

        # Verify: KB idx=3 da chuyen sang CAN_CAP_NHAT
        from common_service.tests.conftest import _make_user, _set_user
        admin = _make_user("SUPER_ADMIN", [], idx=4)
        _set_user(admin)

        kb_resp = await client.get(f"{API}/{sample_knowledge_base[3]['id']}")
        assert kb_resp.status_code == 200
        assert kb_resp.json()["data"]["trang_thai"] == "CAN_CAP_NHAT"
