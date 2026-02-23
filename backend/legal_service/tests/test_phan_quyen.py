"""
legal_service/tests/test_phan_quyen.py — BẮT BUỘC
====================================================
Tests phân quyền toàn diện cho module Legal.

Matrix phân quyền:
  ENDPOINT                  | CBCC | BIEN_TAP | QT_NOI_DUNG | LANH_DAO | ADMIN
  --------------------------|------|----------|-------------|----------|-------
  GET /van-ban              |  ✅  |    ✅    |     ✅      |    ✅    |  ✅
  POST /van-ban             |  ❌  |    ✅    |     ✅      |    ❌    |  ✅
  PATCH /trang-thai NHAP→CD |  ❌  | ✅(own) |     ✅      |    ❌    |  ✅
  PATCH /trang-thai CD→DD   |  ❌  |    ❌   |     ✅      |    ❌    |  ✅
  PATCH /trang-thai DD→DXB  |  ❌  |    ❌   |     ✅      |    ✅    |  ✅
  PATCH /trang-thai DXB→N   |  ❌  |    ❌   |     ✅      |    ❌    |  ✅
  DELETE /van-ban           |  ❌  |    ❌   |     ✅      |    ❌    |  ✅
  GET /bao-cao/don-vi       |  ❌  |    ❌   |     ✅      | ✅(own) |  ✅
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestPhanQuyenTaoVanBan:
    """Test phân quyền tạo văn bản."""

    async def test_cbcc_khong_tao_van_ban(
        self, client: AsyncClient, cbcc_user, sample_loai_van_ban
    ):
        """CBCC không tạo được VB → 403."""
        resp = await client.post(
            "/api/legal/v1/van-ban",
            json={
                "so_hieu": f"VB-CBCC-{uuid.uuid4().hex[:6]}",
                "trich_yeu": "CBCC tạo VB",
                "loai_van_ban_id": sample_loai_van_ban["id"],
            },
        )
        assert resp.status_code == 403
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PERM_001"

    async def test_bien_tap_tao_duoc(
        self, client: AsyncClient, bien_tap_user, sample_loai_van_ban
    ):
        """BIEN_TAP tạo được VB → 200."""
        resp = await client.post(
            "/api/legal/v1/van-ban",
            json={
                "so_hieu": f"VB-BT-{uuid.uuid4().hex[:8]}",
                "trich_yeu": "BIEN_TAP tạo VB",
                "loai_van_ban_id": sample_loai_van_ban["id"],
                "ngay_ban_hanh": "2026-01-15",
                "noi_dung_html": "<p>Nội dung</p>",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_qt_noi_dung_tao_duoc(
        self, client: AsyncClient, qt_noi_dung_user, sample_loai_van_ban
    ):
        """QT_NOI_DUNG tạo được VB → 200."""
        resp = await client.post(
            "/api/legal/v1/van-ban",
            json={
                "so_hieu": f"VB-QT-{uuid.uuid4().hex[:8]}",
                "trich_yeu": "QT_NOI_DUNG tạo VB",
                "loai_van_ban_id": sample_loai_van_ban["id"],
                "ngay_ban_hanh": "2026-01-15",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_lanh_dao_khong_tao_duoc(
        self, client: AsyncClient, lanh_dao_user, sample_loai_van_ban
    ):
        """Lãnh đạo không tạo được VB → 403."""
        resp = await client.post(
            "/api/legal/v1/van-ban",
            json={
                "so_hieu": f"VB-LD-{uuid.uuid4().hex[:6]}",
                "trich_yeu": "Lãnh đạo tạo VB",
                "loai_van_ban_id": sample_loai_van_ban["id"],
            },
        )
        assert resp.status_code == 403

    async def test_admin_bypass_tat_ca(
        self, client: AsyncClient, admin_user, sample_loai_van_ban
    ):
        """SUPER_ADMIN tạo được VB dù không có BIEN_TAP/QT_NOI_DUNG role → 200."""
        resp = await client.post(
            "/api/legal/v1/van-ban",
            json={
                "so_hieu": f"VB-ADMIN-{uuid.uuid4().hex[:8]}",
                "trich_yeu": "Admin bypass tạo VB",
                "loai_van_ban_id": sample_loai_van_ban["id"],
                "ngay_ban_hanh": "2026-01-15",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True


class TestPhanQuyenDuyet:
    """Test phân quyền duyệt văn bản."""

    async def test_bien_tap_khong_duyet(
        self, client: AsyncClient, bien_tap_user, db_session: AsyncSession, sample_loai_van_ban
    ):
        """BIEN_TAP không duyệt được (CHO_DUYET → DA_DUYET) → 403."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        vb = VanBan(
            so_hieu=f"VB-BT-ND-{uuid.uuid4().hex[:6]}",
            trich_yeu="VB cần duyệt",
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

    async def test_qt_noi_dung_duyet_ok(
        self, client: AsyncClient, qt_noi_dung_user, db_session: AsyncSession, sample_loai_van_ban
    ):
        """QT_NOI_DUNG duyệt được (CHO_DUYET → DA_DUYET) → 200."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        vb = VanBan(
            so_hieu=f"VB-QT-D-{uuid.uuid4().hex[:6]}",
            trich_yeu="VB QT duyệt",
            loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
            ngay_ban_hanh=date(2026, 1, 15),
            trang_thai_hieu_luc="CON_HIEU_LUC",
            muc_do="BINH_THUONG",
            bat_buoc_doc=False,
            trang_thai_duyet="CHO_DUYET",
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
            json={"trang_thai_duyet": "DA_DUYET"},
        )
        assert resp.status_code == 200

    async def test_cbcc_khong_gui_duyet(
        self, client: AsyncClient, cbcc_user, sample_van_ban
    ):
        """CBCC không gửi duyệt được → 403."""
        vb_id = sample_van_ban["id"]
        resp = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/trang-thai",
            json={"trang_thai_duyet": "CHO_DUYET"},
        )
        assert resp.status_code == 403

    async def test_lanh_dao_xuat_ban_duoc(
        self, client: AsyncClient, lanh_dao_user, db_session: AsyncSession, sample_loai_van_ban
    ):
        """Lãnh đạo xuất bản được (DA_DUYET → DA_XUAT_BAN) → 200."""
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
            noi_dung_html="<p>Nội dung</p>",
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


class TestPhanQuyenBaoCaoDonVi:
    """Test phân quyền báo cáo đơn vị."""

    async def test_cbcc_khong_xem_bao_cao_don_vi(
        self, client: AsyncClient, cbcc_user
    ):
        """CBCC không xem được báo cáo đơn vị → 403."""
        don_vi_id = "a0000000-0000-0000-0000-000000000001"
        resp = await client.get(
            f"/api/legal/v1/bao-cao/don-vi/{don_vi_id}?thang=2&nam=2026"
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "PERM_001"

    async def test_bien_tap_khong_xem_bao_cao_don_vi(
        self, client: AsyncClient, bien_tap_user
    ):
        """BIEN_TAP không xem được báo cáo đơn vị → 403."""
        don_vi_id = "a0000000-0000-0000-0000-000000000001"
        resp = await client.get(
            f"/api/legal/v1/bao-cao/don-vi/{don_vi_id}?thang=2&nam=2026"
        )
        assert resp.status_code == 403

    async def test_lanh_dao_khong_xem_don_vi_khac(
        self, client: AsyncClient, lanh_dao_user
    ):
        """Lãnh đạo không xem báo cáo đơn vị khác → 403.

        lanh_dao_user có don_vi_id = _LANH_DAO_DON_VI_ID (a000...)
        Truy cập don_vi_id = _OTHER_DON_VI_ID (b000...) → 403
        """
        other_don_vi = "b0000000-0000-0000-0000-000000000002"
        resp = await client.get(
            f"/api/legal/v1/bao-cao/don-vi/{other_don_vi}?thang=2&nam=2026"
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "PERM_006"

    async def test_lanh_dao_xem_bao_cao_don_vi_minh(
        self, client: AsyncClient, lanh_dao_user
    ):
        """Lãnh đạo xem báo cáo đơn vị của mình → permission OK (có thể 404 nếu don_vi không tồn tại trong DB test).

        Permission check xảy ra TRƯỚC khi kiểm tra don_vi trong DB.
        Nếu don_vi không tồn tại → 404 (không phải 403).
        """
        # don_vi_id của lanh_dao_user
        don_vi_id = "a0000000-0000-0000-0000-000000000001"
        resp = await client.get(
            f"/api/legal/v1/bao-cao/don-vi/{don_vi_id}?thang=2&nam=2026"
        )
        # Không phải 403 (permission OK)
        # Có thể 200 (nếu don_vi tồn tại) hoặc 404 (nếu don_vi test không tồn tại)
        assert resp.status_code != 403, "Lãnh đạo PHẢI được phép xem đơn vị của mình"

    async def test_qt_noi_dung_xem_bat_ky_don_vi(
        self, client: AsyncClient, qt_noi_dung_user
    ):
        """QT_NOI_DUNG xem được báo cáo bất kỳ đơn vị nào → không 403."""
        don_vi_id = "b0000000-0000-0000-0000-000000000002"
        resp = await client.get(
            f"/api/legal/v1/bao-cao/don-vi/{don_vi_id}?thang=2&nam=2026"
        )
        # Không phải 403 (permission OK), có thể 404 nếu don_vi không tồn tại
        assert resp.status_code != 403


class TestPhanQuyenLoaiVanBan:
    """Test phân quyền CRUD loại văn bản."""

    async def test_cbcc_chi_xem_loai_van_ban(self, client: AsyncClient, cbcc_user):
        """CBCC chỉ xem được, không tạo/sửa/xóa."""
        # Xem: OK
        get_resp = await client.get("/api/legal/v1/loai-van-ban")
        assert get_resp.status_code == 200

        # Tạo: 403
        post_resp = await client.post(
            "/api/legal/v1/loai-van-ban", json={"ma": "XXX", "ten": "Test"}
        )
        assert post_resp.status_code == 403

    async def test_bien_tap_chi_xem_loai_van_ban(
        self, client: AsyncClient, bien_tap_user
    ):
        """BIEN_TAP chỉ xem được, không tạo loại VB."""
        post_resp = await client.post(
            "/api/legal/v1/loai-van-ban", json={"ma": "XXX", "ten": "Test"}
        )
        assert post_resp.status_code == 403

    async def test_qt_noi_dung_toan_quyen_loai_van_ban(
        self, client: AsyncClient, qt_noi_dung_user
    ):
        """QT_NOI_DUNG tạo/sửa loại VB được."""
        ma = f"NEW-{uuid.uuid4().hex[:4].upper()}"
        resp = await client.post(
            "/api/legal/v1/loai-van-ban", json={"ma": ma, "ten": "Loại mới"}
        )
        assert resp.status_code == 200

    async def test_admin_bypass_loai_van_ban(self, client: AsyncClient, admin_user):
        """SUPER_ADMIN tạo loại VB được (bypass)."""
        ma = f"ADM-{uuid.uuid4().hex[:4].upper()}"
        resp = await client.post(
            "/api/legal/v1/loai-van-ban", json={"ma": ma, "ten": "Admin loại mới"}
        )
        assert resp.status_code == 200


class TestPhanQuyenQuanLy:
    """Test phân quyền xem danh sách quản lý."""

    async def test_bien_tap_chi_xem_vb_cua_minh_trong_quan_ly(
        self, client: AsyncClient, bien_tap_user, sample_van_ban, published_van_ban
    ):
        """BIEN_TAP xem /van-ban/quan-ly → chỉ thấy VB do mình tạo.

        sample_van_ban có nguoi_nhap_id = _REAL_CC_IDS[1] = bien_tap_user.sub
        published_van_ban có nguoi_nhap_id = _REAL_CC_IDS[2] = qt_noi_dung_user.sub
        """
        resp = await client.get("/api/legal/v1/van-ban/quan-ly")
        assert resp.status_code == 200
        items = resp.json()["data"]

        # VB của mình (bien_tap) phải có
        own_ids = [i["id"] for i in items if i["id"] == sample_van_ban["id"]]
        assert len(own_ids) == 1, "BIEN_TAP phải thấy VB của mình"

        # VB của QT_NOI_DUNG không có trong list
        other_ids = [i["id"] for i in items if i["id"] == published_van_ban["id"]]
        assert len(other_ids) == 0, "BIEN_TAP không được thấy VB của người khác"

    async def test_qt_noi_dung_xem_tat_ca_trong_quan_ly(
        self, client: AsyncClient, qt_noi_dung_user, sample_van_ban, published_van_ban
    ):
        """QT_NOI_DUNG xem tất cả VB trong /van-ban/quan-ly."""
        resp = await client.get("/api/legal/v1/van-ban/quan-ly")
        assert resp.status_code == 200
        items = resp.json()["data"]
        ids = [i["id"] for i in items]

        # Cả hai VB đều phải xuất hiện
        assert sample_van_ban["id"] in ids
        assert published_van_ban["id"] in ids
