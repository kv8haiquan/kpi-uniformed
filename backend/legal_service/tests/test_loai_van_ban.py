"""
legal_service/tests/test_loai_van_ban.py
=========================================
Tests cho danh mục Loại Văn Bản.

Business rules:
  - Mọi user đăng nhập đều xem được danh sách
  - Chỉ QT_NOI_DUNG (hoặc SUPER_ADMIN) mới tạo/sửa/xóa
  - CBCC, BIEN_TAP → 403 khi tạo/sửa/xóa
"""

import uuid

import pytest
from httpx import AsyncClient


class TestLoaiVanBanList:
    """Test endpoint GET /api/legal/v1/loai-van-ban."""

    async def test_list_returns_data(self, client: AsyncClient, cbcc_user, sample_loai_van_ban):
        """CBCC xem danh sách loại VB thành công."""
        resp = await client.get("/api/legal/v1/loai-van-ban")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        # Ít nhất 1 item (sample_loai_van_ban đã tạo)
        assert len(data["data"]) >= 1

    async def test_list_item_has_required_fields(
        self, client: AsyncClient, admin_user, sample_loai_van_ban
    ):
        """Mỗi item trong danh sách có đủ các trường cần thiết."""
        resp = await client.get("/api/legal/v1/loai-van-ban")
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert len(items) >= 1
        # Kiểm tra item vừa tạo
        found = [i for i in items if i["ma"] == sample_loai_van_ban["ma"]]
        assert len(found) == 1
        item = found[0]
        assert "id" in item
        assert "ma" in item
        assert "ten" in item
        assert "thu_tu" in item

    async def test_list_requires_auth(self, client: AsyncClient):
        """Không có token → 401 (test basic auth requirement)."""
        # Xóa override user để endpoint yêu cầu real JWT
        from legal_service.dependencies import get_current_user
        from legal_service.main import app

        app.dependency_overrides.pop(get_current_user, None)
        resp = await client.get("/api/legal/v1/loai-van-ban")
        # 401 vì không có token hợp lệ
        assert resp.status_code == 401


class TestLoaiVanBanCRUD:
    """Test tạo/sửa/xóa loại văn bản theo phân quyền."""

    async def test_create_success_qt_noi_dung(self, client: AsyncClient, qt_noi_dung_user):
        """QT_NOI_DUNG tạo loại VB thành công."""
        ma = f"LVB-{uuid.uuid4().hex[:6].upper()}"
        resp = await client.post(
            "/api/legal/v1/loai-van-ban",
            json={"ma": ma, "ten": "Nghị định test", "thu_tu": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["ma"] == ma
        assert data["data"]["ten"] == "Nghị định test"

    async def test_create_success_admin(self, client: AsyncClient, admin_user):
        """SUPER_ADMIN tạo loại VB thành công (bypass)."""
        ma = f"LVB-ADM-{uuid.uuid4().hex[:4].upper()}"
        resp = await client.post(
            "/api/legal/v1/loai-van-ban",
            json={"ma": ma, "ten": "Admin created"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_create_forbidden_cbcc(self, client: AsyncClient, cbcc_user):
        """CBCC không tạo được loại VB → 403."""
        resp = await client.post(
            "/api/legal/v1/loai-van-ban",
            json={"ma": "TEST-CBCC", "ten": "Test"},
        )
        assert resp.status_code == 403
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PERM_001"

    async def test_create_forbidden_bien_tap(self, client: AsyncClient, bien_tap_user):
        """BIEN_TAP không tạo được loại VB → 403."""
        resp = await client.post(
            "/api/legal/v1/loai-van-ban",
            json={"ma": "TEST-BT", "ten": "Test"},
        )
        assert resp.status_code == 403

    async def test_update_success(
        self, client: AsyncClient, qt_noi_dung_user, sample_loai_van_ban
    ):
        """QT_NOI_DUNG cập nhật loại VB thành công."""
        lvb_id = sample_loai_van_ban["id"]
        resp = await client.put(
            f"/api/legal/v1/loai-van-ban/{lvb_id}",
            json={"ten": "Tên mới sau khi cập nhật", "thu_tu": 10},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["ten"] == "Tên mới sau khi cập nhật"

    async def test_update_forbidden_cbcc(
        self, client: AsyncClient, cbcc_user, sample_loai_van_ban
    ):
        """CBCC không sửa được loại VB → 403."""
        lvb_id = sample_loai_van_ban["id"]
        resp = await client.put(
            f"/api/legal/v1/loai-van-ban/{lvb_id}",
            json={"ten": "Thay đổi"},
        )
        assert resp.status_code == 403

    async def test_delete_success(self, client: AsyncClient, qt_noi_dung_user, db_session):
        """QT_NOI_DUNG xóa loại VB không có VB liên kết thành công."""
        # Tạo loại VB mới để xóa (không có VB nào liên kết)
        from legal_service.models.loai_van_ban import LoaiVanBan

        lvb = LoaiVanBan(
            ma=f"DEL-{uuid.uuid4().hex[:6].upper()}", ten="Sẽ bị xóa", thu_tu=98
        )
        db_session.add(lvb)
        await db_session.flush()
        await db_session.refresh(lvb)
        lvb_id = str(lvb.id)

        resp = await client.delete(f"/api/legal/v1/loai-van-ban/{lvb_id}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_delete_forbidden_cbcc(
        self, client: AsyncClient, cbcc_user, sample_loai_van_ban
    ):
        """CBCC không xóa được loại VB → 403."""
        lvb_id = sample_loai_van_ban["id"]
        resp = await client.delete(f"/api/legal/v1/loai-van-ban/{lvb_id}")
        assert resp.status_code == 403

    async def test_delete_with_van_ban_returns_error(
        self, client: AsyncClient, qt_noi_dung_user, sample_loai_van_ban, sample_van_ban
    ):
        """Xóa loại VB khi có VB liên kết → lỗi."""
        # sample_van_ban sử dụng sample_loai_van_ban → không thể xóa
        lvb_id = sample_loai_van_ban["id"]
        resp = await client.delete(f"/api/legal/v1/loai-van-ban/{lvb_id}")
        # Phải lỗi vì có VB đang dùng loại này
        assert resp.status_code in (400, 409, 500)
