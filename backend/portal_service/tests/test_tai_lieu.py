"""
portal_service/tests/test_tai_lieu.py
=======================================
Tests cho Tài liệu API (ECM).

Business rules:
  - Danh sách: chỉ phiên bản MỚI NHẤT (không có phien_ban_truoc nào trỏ tới)
  - Upload tài liệu mới → phiên bản 1
  - Upload phiên bản mới → phiên bản tăng dần + gắn phien_ban_truoc_id
  - Lịch sử: tất cả phiên bản của tài liệu
  - Download: redirect đến file_url
  - Lọc theo thư mục, file_type, tags, tìm kiếm tên
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestTaiLieuDanhSach:
    """Test danh sách tài liệu."""

    async def test_cbcc_xem_tai_lieu_tat_ca(
        self, client: AsyncClient, cbcc_user, sample_tai_lieu
    ):
        """CBCC xem được tài liệu quyền TAT_CA."""
        resp = await client.get("/api/v1/tai-lieu")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        ids = [tl["id"] for tl in data["data"]]
        assert sample_tai_lieu["id"] in ids

    async def test_loc_theo_thu_muc(
        self, client: AsyncClient, cbcc_user, sample_tai_lieu, sample_thu_muc
    ):
        """Lọc tài liệu theo thư mục."""
        resp = await client.get(
            "/api/v1/tai-lieu",
            params={"thu_muc_id": sample_thu_muc["id"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        ids = [tl["id"] for tl in data["data"]]
        assert sample_tai_lieu["id"] in ids

    async def test_loc_theo_file_type(
        self, client: AsyncClient, cbcc_user, sample_tai_lieu
    ):
        """Lọc tài liệu theo MIME type."""
        resp = await client.get(
            "/api/v1/tai-lieu",
            params={"file_type": "application/pdf"},
        )
        assert resp.status_code == 200
        data = resp.json()
        ids = [tl["id"] for tl in data["data"]]
        assert sample_tai_lieu["id"] in ids

    async def test_tim_kiem_ten(
        self, client: AsyncClient, cbcc_user, sample_tai_lieu
    ):
        """Tìm kiếm tài liệu theo tên."""
        resp = await client.get(
            "/api/v1/tai-lieu",
            params={"search": "Tai lieu test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        ids = [tl["id"] for tl in data["data"]]
        assert sample_tai_lieu["id"] in ids

    async def test_chi_hien_thi_phien_ban_moi_nhat(
        self, client: AsyncClient, cbcc_user, sample_tai_lieu, sample_thu_muc, db_session: AsyncSession
    ):
        """Danh sách chỉ hiển thị phiên bản mới nhất (không phải phiên bản cũ)."""
        from portal_service.models.tai_lieu import TaiLieu
        from uuid import UUID
        from datetime import datetime, timezone

        # Tạo phiên bản 2 trỏ về phiên bản 1 (sample_tai_lieu)
        tl_v2 = TaiLieu(
            ten_tai_lieu="Tai lieu test",  # cùng tên
            thu_muc_id=UUID(sample_thu_muc["id"]),
            file_url="https://example.com/test-v2.pdf",
            file_name="test-v2.pdf",
            file_size_bytes=2048,
            file_type="application/pdf",
            phien_ban=2,
            phien_ban_truoc_id=UUID(sample_tai_lieu["id"]),  # trỏ về v1
            quyen_truy_cap="TAT_CA",
            nguoi_tai_len_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db_session.add(tl_v2)
        await db_session.flush()

        resp = await client.get("/api/v1/tai-lieu")
        data = resp.json()
        ids = [tl["id"] for tl in data["data"]]

        # v2 (mới nhất) phải có trong danh sách
        assert str(tl_v2.id) in ids
        # v1 (đã có phiên bản mới) không được xuất hiện
        assert sample_tai_lieu["id"] not in ids


class TestTaiLieuUpload:
    """Test upload tài liệu mới."""

    async def test_qt_upload_tai_lieu_moi(
        self, client: AsyncClient, qt_noi_dung_user, sample_thu_muc
    ):
        """QT_NOI_DUNG upload tài liệu mới → phiên bản 1."""
        resp = await client.post(
            "/api/v1/tai-lieu",
            json={
                "ten_tai_lieu": "Quy dinh 2026",
                "thu_muc_id": sample_thu_muc["id"],
                "file_url": "https://example.com/quy-dinh-2026.pdf",
                "file_name": "quy-dinh-2026.pdf",
                "file_size_bytes": 512000,
                "file_type": "application/pdf",
                "mo_ta": "Quy dinh KPI nam 2026",
                "tags": ["2026", "KPI"],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        tl = data["data"]
        assert tl["ten_tai_lieu"] == "Quy dinh 2026"
        assert tl["phien_ban"] == 1

    async def test_cbcc_upload_duoc(
        self, client: AsyncClient, cbcc_user, sample_thu_muc
    ):
        """CBCC thường (không có platform role) vẫn upload được tài liệu.

        Đây là chính sách mới: mọi công chức đã login đều có thể upload tài liệu
        vào thư viện ECM. Trước đây chỉ BIEN_TAP/QT_NOI_DUNG/ADMIN mới upload được.
        """
        resp = await client.post(
            "/api/v1/tai-lieu",
            json={
                "ten_tai_lieu": "Tai lieu CBCC tu upload",
                "thu_muc_id": sample_thu_muc["id"],
                "file_url": "/uploads/portal/tai-lieu/abc_cbcc.pdf",
                "file_name": "cbcc.pdf",
                "file_size_bytes": 1024,
                "file_type": "application/pdf",
            },
        )
        assert resp.status_code == 201
        tl = resp.json()["data"]
        assert tl["ten_tai_lieu"] == "Tai lieu CBCC tu upload"
        # nguoi_tai_len phai la cbcc_user (idx=0)
        assert tl["nguoi_tai_len"]["id"] == "00327c43-c9a3-44d7-8306-7084e75cb2b5"


class TestTaiLieuQuyenSuaXoa:
    """Test owner-based permission cho cap_nhat / xoa."""

    async def test_owner_xoa_duoc_tai_lieu_minh_tao(
        self, client: AsyncClient, db_session, sample_thu_muc, cbcc_user
    ):
        """User tự xóa được tài liệu chính mình upload."""
        from portal_service.models.tai_lieu import TaiLieu
        from datetime import datetime, timezone
        from uuid import UUID

        # cbcc_user là idx=0 → sub = 00327c43-...
        tl = TaiLieu(
            ten_tai_lieu="Tai lieu cua cbcc",
            thu_muc_id=UUID(sample_thu_muc["id"]),
            file_url="/uploads/portal/tai-lieu/abc.pdf",
            file_name="abc.pdf",
            file_size_bytes=1024,
            file_type="application/pdf",
            phien_ban=1,
            quyen_truy_cap="TAT_CA",
            nguoi_tai_len_id=UUID("00327c43-c9a3-44d7-8306-7084e75cb2b5"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db_session.add(tl)
        await db_session.flush()
        await db_session.refresh(tl)

        resp = await client.delete(f"/api/v1/tai-lieu/{tl.id}")
        assert resp.status_code == 200

    async def test_user_khac_khong_xoa_duoc(
        self, client: AsyncClient, db_session, sample_thu_muc, cbcc_user
    ):
        """User A KHÔNG xóa được tài liệu của user B."""
        from portal_service.models.tai_lieu import TaiLieu
        from datetime import datetime, timezone
        from uuid import UUID

        # cbcc_user là idx=0. Tạo tài liệu do user khác (idx=3) upload
        tl = TaiLieu(
            ten_tai_lieu="Tai lieu cua nguoi khac",
            thu_muc_id=UUID(sample_thu_muc["id"]),
            file_url="/uploads/portal/tai-lieu/other.pdf",
            file_name="other.pdf",
            file_size_bytes=1024,
            file_type="application/pdf",
            phien_ban=1,
            quyen_truy_cap="TAT_CA",
            nguoi_tai_len_id=UUID("02a492ad-fb32-430d-8c4e-e9ded9b8d964"),  # idx=3
            is_deleted=False,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db_session.add(tl)
        await db_session.flush()
        await db_session.refresh(tl)

        resp = await client.delete(f"/api/v1/tai-lieu/{tl.id}")
        assert resp.status_code == 403

    async def test_admin_xoa_duoc_moi_tai_lieu(
        self, client: AsyncClient, admin_user, sample_tai_lieu
    ):
        """Admin SUPER_ADMIN xóa được mọi tài liệu (kể cả của người khác)."""
        resp = await client.delete(f"/api/v1/tai-lieu/{sample_tai_lieu['id']}")
        assert resp.status_code == 200

    async def test_qt_noi_dung_xoa_duoc_moi_tai_lieu(
        self, client: AsyncClient, qt_noi_dung_user, db_session, sample_thu_muc
    ):
        """QT_NOI_DUNG xóa được tài liệu của user khác."""
        from portal_service.models.tai_lieu import TaiLieu
        from datetime import datetime, timezone
        from uuid import UUID

        # Tạo tài liệu của user idx=0 (cbcc), qt_noi_dung_user là idx=2 → không phải owner
        tl = TaiLieu(
            ten_tai_lieu="Tai lieu cua nguoi khac",
            thu_muc_id=UUID(sample_thu_muc["id"]),
            file_url="/uploads/portal/tai-lieu/other.pdf",
            file_name="other.pdf",
            file_size_bytes=1024,
            file_type="application/pdf",
            phien_ban=1,
            quyen_truy_cap="TAT_CA",
            nguoi_tai_len_id=UUID("00327c43-c9a3-44d7-8306-7084e75cb2b5"),  # idx=0
            is_deleted=False,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db_session.add(tl)
        await db_session.flush()
        await db_session.refresh(tl)

        resp = await client.delete(f"/api/v1/tai-lieu/{tl.id}")
        assert resp.status_code == 200

    async def test_owner_cap_nhat_duoc(
        self, client: AsyncClient, db_session, sample_thu_muc, cbcc_user
    ):
        """Owner cập nhật được metadata tài liệu của mình."""
        from portal_service.models.tai_lieu import TaiLieu
        from datetime import datetime, timezone
        from uuid import UUID

        tl = TaiLieu(
            ten_tai_lieu="Ten cu",
            thu_muc_id=UUID(sample_thu_muc["id"]),
            file_url="/uploads/portal/tai-lieu/x.pdf",
            file_name="x.pdf",
            file_size_bytes=1024,
            file_type="application/pdf",
            phien_ban=1,
            quyen_truy_cap="TAT_CA",
            nguoi_tai_len_id=UUID("00327c43-c9a3-44d7-8306-7084e75cb2b5"),  # cbcc
            is_deleted=False,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db_session.add(tl)
        await db_session.flush()
        await db_session.refresh(tl)

        resp = await client.put(
            f"/api/v1/tai-lieu/{tl.id}",
            json={"ten_tai_lieu": "Ten moi"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["ten_tai_lieu"] == "Ten moi"

    async def test_user_khac_khong_cap_nhat_duoc(
        self, client: AsyncClient, db_session, sample_thu_muc, cbcc_user
    ):
        """User A không sửa được tài liệu của user B."""
        from portal_service.models.tai_lieu import TaiLieu
        from datetime import datetime, timezone
        from uuid import UUID

        tl = TaiLieu(
            ten_tai_lieu="Ten cu",
            thu_muc_id=UUID(sample_thu_muc["id"]),
            file_url="/uploads/portal/tai-lieu/x.pdf",
            file_name="x.pdf",
            file_size_bytes=1024,
            file_type="application/pdf",
            phien_ban=1,
            quyen_truy_cap="TAT_CA",
            nguoi_tai_len_id=UUID("02a492ad-fb32-430d-8c4e-e9ded9b8d964"),  # idx=3
            is_deleted=False,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db_session.add(tl)
        await db_session.flush()
        await db_session.refresh(tl)

        resp = await client.put(
            f"/api/v1/tai-lieu/{tl.id}",
            json={"ten_tai_lieu": "Ten moi"},
        )
        assert resp.status_code == 403


class TestUploadFile:
    """Test endpoint POST /upload/file (upload file thật)."""

    async def test_cbcc_upload_file_pdf_thanh_cong(
        self, client: AsyncClient, cbcc_user, tmp_path
    ):
        """CBCC thường upload được file PDF qua POST /upload/file."""
        import io

        content = b"%PDF-1.4 test fake pdf content"
        files = {"file": ("test.pdf", io.BytesIO(content), "application/pdf")}
        resp = await client.post("/api/v1/upload/file", files=files)

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["file_name"] == "test.pdf"
        assert data["data"]["file_url"].startswith("/uploads/portal/tai-lieu/")
        assert data["data"]["file_size"] == len(content)

        # Cleanup file da ghi xuong disk
        from pathlib import Path
        file_path = Path(data["data"]["file_url"].lstrip("/"))
        if file_path.exists():
            file_path.unlink()

    async def test_upload_dinh_dang_khong_ho_tro(
        self, client: AsyncClient, cbcc_user
    ):
        """Upload file .exe → 400."""
        import io

        files = {"file": ("malware.exe", io.BytesIO(b"fake"), "application/octet-stream")}
        resp = await client.post("/api/v1/upload/file", files=files)
        assert resp.status_code == 400


class TestTaiLieuChiTiet:
    """Test chi tiết tài liệu."""

    async def test_chi_tiet_tai_lieu(
        self, client: AsyncClient, cbcc_user, sample_tai_lieu
    ):
        """Lấy chi tiết tài liệu."""
        resp = await client.get(f"/api/v1/tai-lieu/{sample_tai_lieu['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        tl = data["data"]
        assert tl["id"] == sample_tai_lieu["id"]
        assert tl["phien_ban"] == 1

    async def test_chi_tiet_404(self, client: AsyncClient, cbcc_user):
        """Tài liệu không tồn tại → 404."""
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/api/v1/tai-lieu/{fake_id}")
        assert resp.status_code == 404


class TestTaiLieuPhienBan:
    """Test upload phiên bản mới + lịch sử."""

    async def test_upload_phien_ban_moi(
        self, client: AsyncClient, qt_noi_dung_user, sample_tai_lieu
    ):
        """Upload phiên bản mới → phiên bản tăng, có phien_ban_truoc_id."""
        resp = await client.post(
            f"/api/v1/tai-lieu/{sample_tai_lieu['id']}/phien-ban-moi",
            json={
                "file_url": "https://example.com/test-v2.pdf",
                "file_name": "test-v2.pdf",
                "file_size_bytes": 2048,
                "file_type": "application/pdf",
                "mo_ta": "Cap nhat phien ban 2",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        tl_v2 = data["data"]
        assert tl_v2["phien_ban"] == 2
        assert tl_v2["phien_ban_truoc_id"] == sample_tai_lieu["id"]

    async def test_lich_su_phien_ban(
        self, client: AsyncClient, cbcc_user, sample_tai_lieu
    ):
        """Lịch sử hiển thị tất cả phiên bản của tài liệu."""
        resp = await client.get(
            f"/api/v1/tai-lieu/{sample_tai_lieu['id']}/lich-su"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        # Ít nhất có phiên bản 1 (sample_tai_lieu)
        ids = [v["id"] for v in data["data"]]
        assert sample_tai_lieu["id"] in ids

    async def test_download_redirect(
        self, client: AsyncClient, cbcc_user, sample_tai_lieu
    ):
        """Download tài liệu → redirect đến file_url."""
        resp = await client.get(
            f"/api/v1/tai-lieu/{sample_tai_lieu['id']}/download",
            follow_redirects=False,
        )
        # Redirect (307) hoặc trực tiếp nếu dùng RedirectResponse
        assert resp.status_code in (200, 302, 307)
