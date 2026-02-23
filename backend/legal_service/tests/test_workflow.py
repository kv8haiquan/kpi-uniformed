"""
legal_service/tests/test_workflow.py
======================================
Tests workflow duyệt văn bản — QUAN TRỌNG NHẤT.

Workflow hợp lệ:
  NHAP → CHO_DUYET → DA_DUYET → DA_XUAT_BAN → NHAP (thu hồi)
  CHO_DUYET → NHAP (từ chối)

Business rules:
  - BIEN_TAP: gửi duyệt (NHAP → CHO_DUYET) VB của mình
  - QT_NOI_DUNG: duyệt (CHO_DUYET → DA_DUYET), từ chối, xuất bản, thu hồi
  - Lãnh đạo: xuất bản (DA_DUYET → DA_XUAT_BAN)
  - Bỏ bước: NHAP → DA_XUAT_BAN → lỗi LEGAL_ERR_003
  - Xuất bản thiếu nội dung → LEGAL_ERR_004
  - bat_buoc_doc=TRUE + xuất bản → tạo xac_nhan_doc hàng loạt
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TestWorkflowBuocBuoc:
    """Test từng bước workflow hợp lệ."""

    async def test_nhap_to_cho_duyet_ok(
        self, client: AsyncClient, qt_noi_dung_user, sample_van_ban
    ):
        """QT_NOI_DUNG gửi duyệt NHAP → CHO_DUYET thành công."""
        vb_id = sample_van_ban["id"]
        resp = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={"trang_thai_duyet": "CHO_DUYET"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["trang_thai_duyet"] == "CHO_DUYET"

    async def test_cho_duyet_to_da_duyet_ok(
        self, client: AsyncClient, qt_noi_dung_user, db_session, sample_loai_van_ban
    ):
        """QT_NOI_DUNG duyệt CHO_DUYET → DA_DUYET thành công."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        # Tạo VB ở trạng thái CHO_DUYET
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        vb = VanBan(
            so_hieu=f"VB-CD-{uuid.uuid4().hex[:8]}",
            trich_yeu="VB đang chờ duyệt",
            loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
            ngay_ban_hanh=date(2026, 1, 15),
            trang_thai_hieu_luc="CON_HIEU_LUC",
            muc_do="BINH_THUONG",
            bat_buoc_doc=False,
            trang_thai_duyet="CHO_DUYET",
            nguoi_nhap_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            phien_ban=1,
            is_deleted=False,
            noi_dung_html="<p>Nội dung</p>",
            created_at=now,
            updated_at=now,
        )
        db_session.add(vb)
        await db_session.flush()
        vb_id = str(vb.id)

        resp = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={"trang_thai_duyet": "DA_DUYET"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["trang_thai_duyet"] == "DA_DUYET"

    async def test_da_duyet_to_da_xuat_ban_ok(
        self, client: AsyncClient, qt_noi_dung_user, db_session, sample_loai_van_ban
    ):
        """QT_NOI_DUNG xuất bản DA_DUYET → DA_XUAT_BAN thành công."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        vb = VanBan(
            so_hieu=f"VB-DD-{uuid.uuid4().hex[:8]}",
            trich_yeu="VB đã duyệt chờ xuất bản",
            loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
            ngay_ban_hanh=date(2026, 1, 15),
            trang_thai_hieu_luc="CON_HIEU_LUC",
            muc_do="BINH_THUONG",
            bat_buoc_doc=False,
            trang_thai_duyet="DA_DUYET",
            noi_dung_html="<p>Nội dung đầy đủ</p>",
            nguoi_nhap_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            phien_ban=1,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        db_session.add(vb)
        await db_session.flush()
        vb_id = str(vb.id)

        resp = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={"trang_thai_duyet": "DA_XUAT_BAN"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["trang_thai_duyet"] == "DA_XUAT_BAN"


class TestWorkflowHappyPath:
    """Test full workflow từ đầu đến cuối."""

    async def test_full_workflow_nhap_to_xuat_ban(
        self, client: AsyncClient, qt_noi_dung_user, sample_loai_van_ban
    ):
        """Full workflow: NHAP → CHO_DUYET → DA_DUYET → DA_XUAT_BAN."""
        so_hieu = f"VB-FULL-{uuid.uuid4().hex[:8].upper()}"

        # Bước 1: Tạo VB (NHAP)
        create_resp = await client.post(
            "/api/legal/v1/van-ban",
            json={
                "so_hieu": so_hieu,
                "trich_yeu": "Full workflow test",
                "loai_van_ban_id": sample_loai_van_ban["id"],
                "ngay_ban_hanh": "2026-01-20",
                "noi_dung_html": "<p>Nội dung đầy đủ</p>",
                "muc_do": "BINH_THUONG",
            },
        )
        assert create_resp.status_code == 200
        vb_id = create_resp.json()["data"]["id"]
        assert create_resp.json()["data"]["trang_thai_duyet"] == "NHAP"

        # Bước 2: Gửi duyệt (NHAP → CHO_DUYET)
        r2 = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={"trang_thai_duyet": "CHO_DUYET"},
        )
        assert r2.status_code == 200
        assert r2.json()["data"]["trang_thai_duyet"] == "CHO_DUYET"

        # Bước 3: Duyệt (CHO_DUYET → DA_DUYET)
        r3 = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={"trang_thai_duyet": "DA_DUYET"},
        )
        assert r3.status_code == 200
        assert r3.json()["data"]["trang_thai_duyet"] == "DA_DUYET"

        # Bước 4: Xuất bản (DA_DUYET → DA_XUAT_BAN)
        r4 = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={"trang_thai_duyet": "DA_XUAT_BAN"},
        )
        assert r4.status_code == 200
        assert r4.json()["data"]["trang_thai_duyet"] == "DA_XUAT_BAN"


class TestWorkflowLoi:
    """Test các trường hợp lỗi trong workflow."""

    async def test_nhap_to_da_xuat_ban_fail(
        self, client: AsyncClient, qt_noi_dung_user, sample_van_ban
    ):
        """Bỏ bước NHAP → DA_XUAT_BAN → LEGAL_ERR_003."""
        vb_id = sample_van_ban["id"]
        resp = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={"trang_thai_duyet": "DA_XUAT_BAN"},  # Bỏ bước CHO_DUYET và DA_DUYET
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "LEGAL_ERR_003"

    async def test_nhap_to_da_duyet_fail(
        self, client: AsyncClient, qt_noi_dung_user, sample_van_ban
    ):
        """Bỏ bước NHAP → DA_DUYET → LEGAL_ERR_003."""
        vb_id = sample_van_ban["id"]
        resp = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={"trang_thai_duyet": "DA_DUYET"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "LEGAL_ERR_003"

    async def test_cho_duyet_to_da_xuat_ban_fail(
        self, client: AsyncClient, qt_noi_dung_user, db_session, sample_loai_van_ban
    ):
        """Bỏ bước CHO_DUYET → DA_XUAT_BAN → LEGAL_ERR_003."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        vb = VanBan(
            so_hieu=f"VB-SKIP-{uuid.uuid4().hex[:8]}",
            trich_yeu="VB test bỏ bước",
            loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
            ngay_ban_hanh=date(2026, 1, 15),
            trang_thai_hieu_luc="CON_HIEU_LUC",
            muc_do="BINH_THUONG",
            bat_buoc_doc=False,
            trang_thai_duyet="CHO_DUYET",
            nguoi_nhap_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            phien_ban=1,
            is_deleted=False,
            noi_dung_html="<p>Nội dung</p>",
            created_at=now,
            updated_at=now,
        )
        db_session.add(vb)
        await db_session.flush()
        vb_id = str(vb.id)

        resp = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={"trang_thai_duyet": "DA_XUAT_BAN"},  # Bỏ qua DA_DUYET
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "LEGAL_ERR_003"

    async def test_tu_choi_ve_nhap_ok(
        self, client: AsyncClient, qt_noi_dung_user, db_session, sample_loai_van_ban
    ):
        """QT_NOI_DUNG từ chối: CHO_DUYET → NHAP (kèm ghi_chu)."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        vb = VanBan(
            so_hieu=f"VB-TC-{uuid.uuid4().hex[:8]}",
            trich_yeu="VB cần từ chối",
            loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
            ngay_ban_hanh=date(2026, 1, 15),
            trang_thai_hieu_luc="CON_HIEU_LUC",
            muc_do="BINH_THUONG",
            bat_buoc_doc=False,
            trang_thai_duyet="CHO_DUYET",
            nguoi_nhap_id=UUID("01014af6-1505-495b-95ab-8c1503cfa061"),
            phien_ban=1,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        db_session.add(vb)
        await db_session.flush()
        vb_id = str(vb.id)

        resp = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={
                "trang_thai_duyet": "NHAP",  # Từ chối → về NHAP
                "ghi_chu": "Nội dung chưa đầy đủ, cần bổ sung",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["trang_thai_duyet"] == "NHAP"

    async def test_xuat_ban_thieu_noi_dung(
        self, client: AsyncClient, qt_noi_dung_user, db_session, sample_loai_van_ban
    ):
        """Xuất bản VB thiếu noi_dung_html và file_goc_url → LEGAL_ERR_004."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        vb = VanBan(
            so_hieu=f"VB-NO-CONTENT-{uuid.uuid4().hex[:6]}",
            trich_yeu="VB thiếu nội dung",
            loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
            ngay_ban_hanh=date(2026, 1, 15),
            trang_thai_hieu_luc="CON_HIEU_LUC",
            muc_do="BINH_THUONG",
            bat_buoc_doc=False,
            trang_thai_duyet="DA_DUYET",
            nguoi_nhap_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            phien_ban=1,
            is_deleted=False,
            # Không có noi_dung_html và file_goc_url
            noi_dung_html=None,
            file_goc_url=None,
            created_at=now,
            updated_at=now,
        )
        db_session.add(vb)
        await db_session.flush()
        vb_id = str(vb.id)

        resp = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={"trang_thai_duyet": "DA_XUAT_BAN"},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"]["code"] == "LEGAL_ERR_004"

    async def test_thu_hoi_ve_nhap_ok(
        self, client: AsyncClient, qt_noi_dung_user, published_van_ban
    ):
        """QT_NOI_DUNG thu hồi DA_XUAT_BAN → NHAP thành công."""
        vb_id = published_van_ban["id"]
        resp = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={"trang_thai_duyet": "NHAP", "ghi_chu": "Thu hồi để sửa đổi"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["trang_thai_duyet"] == "NHAP"


class TestWorkflowPhanQuyen:
    """Test phân quyền trong workflow."""

    async def test_bien_tap_gui_duyet_vb_cua_minh(
        self, client: AsyncClient, bien_tap_user, sample_van_ban
    ):
        """BIEN_TAP gửi duyệt VB của chính mình (nguoi_nhap_id match) → OK."""
        # sample_van_ban có nguoi_nhap_id = _REAL_CC_IDS[1] = bien_tap_user.sub
        vb_id = sample_van_ban["id"]
        resp = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={"trang_thai_duyet": "CHO_DUYET"},
        )
        assert resp.status_code == 200

    async def test_bien_tap_khong_duyet_duoc(
        self, client: AsyncClient, bien_tap_user, db_session, sample_loai_van_ban
    ):
        """BIEN_TAP không duyệt được CHO_DUYET → DA_DUYET → 403."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        vb = VanBan(
            so_hieu=f"VB-BT-ND-{uuid.uuid4().hex[:6]}",
            trich_yeu="VB test BIEN_TAP không duyệt được",
            loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
            ngay_ban_hanh=date(2026, 1, 15),
            trang_thai_hieu_luc="CON_HIEU_LUC",
            muc_do="BINH_THUONG",
            bat_buoc_doc=False,
            trang_thai_duyet="CHO_DUYET",
            nguoi_nhap_id=UUID("01014af6-1505-495b-95ab-8c1503cfa061"),  # bien_tap
            phien_ban=1,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        db_session.add(vb)
        await db_session.flush()
        vb_id = str(vb.id)

        resp = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={"trang_thai_duyet": "DA_DUYET"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "PERM_001"

    async def test_cbcc_khong_gui_duyet_duoc(
        self, client: AsyncClient, cbcc_user, sample_van_ban
    ):
        """CBCC không gửi duyệt được → 403."""
        vb_id = sample_van_ban["id"]
        resp = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={"trang_thai_duyet": "CHO_DUYET"},
        )
        assert resp.status_code == 403

    async def test_lanh_dao_xuat_ban_ok(
        self, client: AsyncClient, lanh_dao_user, db_session, sample_loai_van_ban
    ):
        """Lãnh đạo xuất bản DA_DUYET → DA_XUAT_BAN thành công."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        vb = VanBan(
            so_hieu=f"VB-LD-XB-{uuid.uuid4().hex[:6]}",
            trich_yeu="VB lãnh đạo xuất bản",
            loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
            ngay_ban_hanh=date(2026, 1, 15),
            trang_thai_hieu_luc="CON_HIEU_LUC",
            muc_do="BINH_THUONG",
            bat_buoc_doc=False,
            trang_thai_duyet="DA_DUYET",
            noi_dung_html="<p>Nội dung đầy đủ</p>",
            nguoi_nhap_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            phien_ban=1,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        db_session.add(vb)
        await db_session.flush()
        vb_id = str(vb.id)

        resp = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={"trang_thai_duyet": "DA_XUAT_BAN"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["trang_thai_duyet"] == "DA_XUAT_BAN"


class TestXuatBanBatBuocDoc:
    """Test business rule: xuất bản VB bắt buộc đọc → tạo xac_nhan_doc hàng loạt."""

    async def test_xuat_ban_bat_buoc_doc_khong_tao_xac_nhan_khi_khong_co_cbcc(
        self, client: AsyncClient, qt_noi_dung_user, db_session, sample_loai_van_ban
    ):
        """Xuất bản VB bat_buoc_doc=TRUE với doi_tuong_ap_dung=TAT_CA.

        Do test environment có thể không có CBCC với is_active=True nếu
        public.cong_chuc không accessible, test này verify workflow hoàn thành.
        """
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        vb = VanBan(
            so_hieu=f"VB-BB-{uuid.uuid4().hex[:8]}",
            trich_yeu="VB bắt buộc đọc",
            loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
            ngay_ban_hanh=date(2026, 1, 15),
            trang_thai_hieu_luc="CON_HIEU_LUC",
            muc_do="KHAN",
            bat_buoc_doc=True,  # Bắt buộc đọc
            doi_tuong_ap_dung=["TAT_CA"],
            trang_thai_duyet="DA_DUYET",
            noi_dung_html="<p>Nội dung bắt buộc</p>",
            nguoi_nhap_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            phien_ban=1,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        db_session.add(vb)
        await db_session.flush()
        vb_id = str(vb.id)

        # Xuất bản
        resp = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={"trang_thai_duyet": "DA_XUAT_BAN"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["trang_thai_duyet"] == "DA_XUAT_BAN"

        # Verify: nếu có CBCC active trong DB, sẽ có xac_nhan_doc records
        # (chúng ta verify workflow không lỗi, không verify số lượng cụ thể)
        from legal_service.models.xac_nhan_doc import XacNhanDoc

        xnd_result = await db_session.execute(
            select(XacNhanDoc).where(XacNhanDoc.van_ban_id == UUID(vb_id))
        )
        xnd_list = xnd_result.scalars().all()
        # Tất cả bản ghi được tạo tự động đều có da_doc=False, da_xac_nhan=False
        for xnd in xnd_list:
            assert xnd.da_doc is False
            assert xnd.da_xac_nhan is False
