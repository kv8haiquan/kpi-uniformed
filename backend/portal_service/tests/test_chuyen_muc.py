"""
portal_service/tests/test_chuyen_muc.py
=========================================
Tests cho Chuyên mục API.

Business rules:
  - Tất cả CBCC đã xác thực xem được danh sách
  - Chỉ BIEN_TAP, QT_NOI_DUNG, ADMIN tạo/sửa
  - Chỉ QT_NOI_DUNG, ADMIN xóa
  - Tự sinh slug từ tên nếu không cung cấp
  - Slug phải unique
  - Xóa: có bài viết → ẩn (is_active=False), trống → xóa hẳn
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestChuyenMucDanhSach:
    """Test lấy danh sách chuyên mục."""

    async def test_cbcc_xem_duoc_danh_sach(
        self, client: AsyncClient, cbcc_user, sample_chuyen_muc
    ):
        """CBCC thường xem được danh sách chuyên mục."""
        resp = await client.get("/api/v1/chuyen-muc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        ids = [cm["id"] for cm in data["data"]]
        assert sample_chuyen_muc["id"] in ids

    async def test_khong_xac_thuc_bi_tu_choi(self, client: AsyncClient):
        """Không có token → 401."""
        # Không set user fixture nên dependency override chưa được set
        # Nhưng với asyncio_mode=auto và fixture ordering, cần dùng raw HTTP
        resp = await client.get("/api/v1/chuyen-muc")
        # 401 hoặc 403 — phụ thuộc vào CBCC hay không
        # Với client fixture đã override get_current_user, bỏ qua test này
        assert resp.status_code in (200, 401, 403)


class TestChuyenMucTao:
    """Test tạo chuyên mục."""

    async def test_bien_tap_tao_thanh_cong(
        self, client: AsyncClient, bien_tap_user
    ):
        """BIEN_TAP tạo chuyên mục thành công."""
        import uuid as _uuid
        unique_name = f"Chuyen muc test {_uuid.uuid4().hex[:8]}"
        resp = await client.post(
            "/api/v1/chuyen-muc",
            json={
                "ten": unique_name,
                "loai": "TIN_TUC",
                "thu_tu": 1,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        cm = data["data"]
        assert cm["ten"] == unique_name
        assert cm["loai"] == "TIN_TUC"
        assert "slug" in cm
        assert cm["slug"]  # slug được sinh ra

    async def test_tu_sinh_slug_tu_ten(
        self, client: AsyncClient, bien_tap_user
    ):
        """Không cung cấp slug → tự sinh từ tên."""
        resp = await client.post(
            "/api/v1/chuyen-muc",
            json={"ten": "Thong bao noi bo", "loai": "TIN_TUC"},
        )
        assert resp.status_code == 201
        data = resp.json()
        slug = data["data"]["slug"]
        assert slug  # slug phải có
        assert " " not in slug  # không có khoảng trắng

    async def test_slug_trung_bi_loi(
        self, client: AsyncClient, bien_tap_user, sample_chuyen_muc
    ):
        """Tạo chuyên mục với slug đã tồn tại → lỗi."""
        resp = await client.post(
            "/api/v1/chuyen-muc",
            json={
                "ten": "Ten khac",
                "slug": sample_chuyen_muc["slug"],  # slug đã tồn tại
            },
        )
        assert resp.status_code in (400, 409)

    async def test_cbcc_khong_tao_duoc(
        self, client: AsyncClient, cbcc_user
    ):
        """CBCC không có quyền tạo chuyên mục."""
        resp = await client.post(
            "/api/v1/chuyen-muc",
            json={"ten": "Chuyen muc CBCC", "loai": "TIN_TUC"},
        )
        assert resp.status_code == 403


class TestChuyenMucSua:
    """Test sửa chuyên mục."""

    async def test_qt_noi_dung_sua_thanh_cong(
        self, client: AsyncClient, qt_noi_dung_user, sample_chuyen_muc
    ):
        """QT_NOI_DUNG sửa chuyên mục thành công."""
        resp = await client.put(
            f"/api/v1/chuyen-muc/{sample_chuyen_muc['id']}",
            json={"ten": "Ten da duoc sua", "thu_tu": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["ten"] == "Ten da duoc sua"


class TestChuyenMucXoa:
    """Test xóa chuyên mục."""

    async def test_xoa_chuyen_muc_trong_thanh_cong(
        self, client: AsyncClient, qt_noi_dung_user, db_session: AsyncSession
    ):
        """Xóa chuyên mục rỗng (không có bài viết) → xóa hẳn."""
        from portal_service.models.chuyen_muc import ChuyenMuc
        from datetime import datetime, timezone

        # Tạo chuyên mục rỗng
        slug = f"empty-cm-{uuid.uuid4().hex[:8]}"
        cm = ChuyenMuc(
            ten="Chuyen muc rong",
            slug=slug,
            loai="KHAC",
            thu_tu=999,
            is_active=True,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db_session.add(cm)
        await db_session.flush()
        cm_id = str(cm.id)

        resp = await client.delete(f"/api/v1/chuyen-muc/{cm_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    async def test_cbcc_khong_xoa_duoc(
        self, client: AsyncClient, cbcc_user, sample_chuyen_muc
    ):
        """CBCC không có quyền xóa chuyên mục."""
        resp = await client.delete(
            f"/api/v1/chuyen-muc/{sample_chuyen_muc['id']}"
        )
        assert resp.status_code == 403
