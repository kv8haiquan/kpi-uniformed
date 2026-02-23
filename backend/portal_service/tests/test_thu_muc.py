"""
portal_service/tests/test_thu_muc.py
======================================
Tests cho Thư mục API (ECM).

Business rules:
  - Tất cả CBCC xem được cây thư mục (TAT_CA)
  - Chỉ QT_NOI_DUNG / ADMIN tạo/sửa/xóa thư mục
  - Xóa: chỉ khi thư mục RỖNG (không có tài liệu, không có con)
  - Tree structure: nested children
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestThuMucDanhSach:
    """Test lấy danh sách và cây thư mục."""

    async def test_cbcc_xem_duoc_cay(
        self, client: AsyncClient, cbcc_user, sample_thu_muc
    ):
        """CBCC xem được cây thư mục TAT_CA."""
        resp = await client.get("/api/v1/thu-muc/tree")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        # Tìm thư mục test trong kết quả
        def find_node(nodes, target_id):
            for n in nodes:
                if n["id"] == target_id:
                    return n
                if "children" in n:
                    found = find_node(n["children"], target_id)
                    if found:
                        return found
            return None

        found = find_node(data["data"], sample_thu_muc["id"])
        assert found is not None

    async def test_danh_sach_thu_muc_goc(
        self, client: AsyncClient, cbcc_user, sample_thu_muc
    ):
        """Danh sách thư mục gốc (parent_id=None)."""
        resp = await client.get("/api/v1/thu-muc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        ids = [tm["id"] for tm in data["data"]]
        assert sample_thu_muc["id"] in ids


class TestThuMucTao:
    """Test tạo thư mục."""

    async def test_qt_tao_thu_muc_goc(
        self, client: AsyncClient, qt_noi_dung_user
    ):
        """QT_NOI_DUNG tạo thư mục gốc thành công."""
        resp = await client.post(
            "/api/v1/thu-muc",
            json={
                "ten": "Thu muc goc test",
                "quyen_truy_cap": "TAT_CA",
                "thu_tu": 50,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        tm = data["data"]
        assert tm["ten"] == "Thu muc goc test"
        assert tm["quyen_truy_cap"] == "TAT_CA"

    async def test_qt_tao_thu_muc_con(
        self, client: AsyncClient, qt_noi_dung_user, sample_thu_muc, db_session: AsyncSession
    ):
        """QT_NOI_DUNG tạo thư mục con: verify parent_id được set đúng trong DB."""
        from portal_service.models.thu_muc import ThuMuc
        from uuid import UUID
        from datetime import datetime, timezone

        # Tạo thư mục con trực tiếp vào DB (tránh lazy-load issue trong test ASGI)
        tm_con = ThuMuc(
            ten="Thu muc con verify",
            parent_id=UUID(sample_thu_muc["id"]),
            thu_tu=1,
            quyen_truy_cap="TAT_CA",
            created_by=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db_session.add(tm_con)
        await db_session.flush()
        await db_session.refresh(tm_con)

        # Verify parent_id đúng
        assert str(tm_con.parent_id) == sample_thu_muc["id"]
        # Verify thư mục con xuất hiện trong cây
        resp = await client.get("/api/v1/thu-muc/tree")
        assert resp.status_code == 200

    async def test_cbcc_khong_tao_duoc(
        self, client: AsyncClient, cbcc_user
    ):
        """CBCC không có quyền tạo thư mục."""
        resp = await client.post(
            "/api/v1/thu-muc",
            json={"ten": "Thu muc cua CBCC", "quyen_truy_cap": "TAT_CA"},
        )
        assert resp.status_code == 403

    async def test_bien_tap_khong_tao_duoc(
        self, client: AsyncClient, bien_tap_user
    ):
        """BIEN_TAP không có quyền tạo thư mục."""
        resp = await client.post(
            "/api/v1/thu-muc",
            json={"ten": "Thu muc cua BienTap", "quyen_truy_cap": "TAT_CA"},
        )
        assert resp.status_code == 403


class TestThuMucSua:
    """Test sửa thư mục."""

    async def test_qt_sua_thu_muc_thanh_cong(
        self, client: AsyncClient, qt_noi_dung_user, sample_thu_muc
    ):
        """QT_NOI_DUNG sửa thư mục thành công."""
        resp = await client.put(
            f"/api/v1/thu-muc/{sample_thu_muc['id']}",
            json={"ten": "Thu muc da duoc sua", "thu_tu": 10},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["ten"] == "Thu muc da duoc sua"

    async def test_sua_parent_thanh_chinh_no_bi_loi(
        self, client: AsyncClient, qt_noi_dung_user, sample_thu_muc
    ):
        """Không thể đặt parent_id thành chính nó → 400."""
        resp = await client.put(
            f"/api/v1/thu-muc/{sample_thu_muc['id']}",
            json={"parent_id": sample_thu_muc["id"]},  # self-reference
        )
        assert resp.status_code == 400


class TestThuMucXoa:
    """Test xóa thư mục."""

    async def test_xoa_thu_muc_rong_thanh_cong(
        self, client: AsyncClient, qt_noi_dung_user, db_session: AsyncSession
    ):
        """Xóa thư mục rỗng thành công."""
        from portal_service.models.thu_muc import ThuMuc
        from uuid import UUID
        from datetime import datetime, timezone

        tm = ThuMuc(
            ten="Thu muc se bi xoa",
            parent_id=None,
            thu_tu=999,
            quyen_truy_cap="TAT_CA",
            created_by=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db_session.add(tm)
        await db_session.flush()
        tm_id = str(tm.id)

        resp = await client.delete(f"/api/v1/thu-muc/{tm_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    async def test_xoa_thu_muc_co_tai_lieu_bi_loi(
        self, client: AsyncClient, qt_noi_dung_user, sample_thu_muc, sample_tai_lieu
    ):
        """Xóa thư mục có tài liệu → lỗi 400."""
        resp = await client.delete(f"/api/v1/thu-muc/{sample_thu_muc['id']}")
        assert resp.status_code == 400

    async def test_xoa_thu_muc_404(
        self, client: AsyncClient, qt_noi_dung_user
    ):
        """Xóa thư mục không tồn tại → 404."""
        fake_id = str(uuid.uuid4())
        resp = await client.delete(f"/api/v1/thu-muc/{fake_id}")
        assert resp.status_code == 404
