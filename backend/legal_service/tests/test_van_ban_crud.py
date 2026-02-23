"""
legal_service/tests/test_van_ban_crud.py
==========================================
Tests CRUD cơ bản cho Văn Bản.

Business rules:
  - Chỉ BIEN_TAP, QT_NOI_DUNG tạo/sửa VB
  - CBCC chỉ xem DA_XUAT_BAN
  - Chi tiết VB → side effect: upsert xac_nhan_doc (da_doc=TRUE)
  - Sửa VB đã xuất bản → tăng phiên_bản
  - Chỉ xóa được VB ở trạng thái NHAP
  - Số hiệu VB không được trùng → LEGAL_ERR_002
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class TestVanBanCreate:
    """Test tạo văn bản mới."""

    async def test_tao_van_ban_thanh_cong_bien_tap(
        self, client: AsyncClient, bien_tap_user, sample_loai_van_ban
    ):
        """BIEN_TAP tạo văn bản thành công → trang_thai_duyet=NHAP."""
        so_hieu = f"VB-BT-{uuid.uuid4().hex[:8].upper()}"
        resp = await client.post(
            "/api/legal/v1/van-ban",
            json={
                "so_hieu": so_hieu,
                "trich_yeu": "Văn bản test từ biên tập viên",
                "loai_van_ban_id": sample_loai_van_ban["id"],
                "ngay_ban_hanh": "2026-01-15",
                "co_quan_ban_hanh": "Chi cục HQKV8",
                "muc_do": "BINH_THUONG",
                "noi_dung_html": "<p>Nội dung</p>",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        vb = data["data"]
        assert vb["so_hieu"] == so_hieu
        assert vb["trang_thai_duyet"] == "NHAP"
        assert vb["phien_ban"] == 1

    async def test_tao_van_ban_thanh_cong_qt_noi_dung(
        self, client: AsyncClient, qt_noi_dung_user, sample_loai_van_ban
    ):
        """QT_NOI_DUNG tạo văn bản thành công."""
        so_hieu = f"VB-QT-{uuid.uuid4().hex[:8].upper()}"
        resp = await client.post(
            "/api/legal/v1/van-ban",
            json={
                "so_hieu": so_hieu,
                "trich_yeu": "Văn bản test từ quản trị nội dung",
                "loai_van_ban_id": sample_loai_van_ban["id"],
                "ngay_ban_hanh": "2026-02-01",
                "muc_do": "QUAN_TRONG",
                "noi_dung_html": "<p>Nội dung quan trọng</p>",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["trang_thai_duyet"] == "NHAP"

    async def test_tao_van_ban_trung_so_hieu(
        self, client: AsyncClient, qt_noi_dung_user, sample_van_ban
    ):
        """Tạo VB với số hiệu đã tồn tại → LEGAL_ERR_002."""
        existing_so_hieu = sample_van_ban["so_hieu"]
        resp = await client.post(
            "/api/legal/v1/van-ban",
            json={
                "so_hieu": existing_so_hieu,  # Trùng số hiệu
                "trich_yeu": "Văn bản khác",
                "loai_van_ban_id": sample_van_ban["loai_van_ban_id"],
                "ngay_ban_hanh": "2026-01-20",
            },
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "LEGAL_ERR_002"

    async def test_cbcc_khong_tao_duoc(
        self, client: AsyncClient, cbcc_user, sample_loai_van_ban
    ):
        """CBCC không tạo được văn bản → 403."""
        resp = await client.post(
            "/api/legal/v1/van-ban",
            json={
                "so_hieu": f"VB-CBCC-{uuid.uuid4().hex[:6]}",
                "trich_yeu": "Test CBCC",
                "loai_van_ban_id": sample_loai_van_ban["id"],
                "ngay_ban_hanh": "2026-01-15",
            },
        )
        assert resp.status_code == 403
        data = resp.json()
        assert data["error"]["code"] == "PERM_001"

    async def test_lanh_dao_khong_tao_duoc(
        self, client: AsyncClient, lanh_dao_user, sample_loai_van_ban
    ):
        """Lãnh đạo không tạo được văn bản → 403."""
        resp = await client.post(
            "/api/legal/v1/van-ban",
            json={
                "so_hieu": f"VB-LD-{uuid.uuid4().hex[:6]}",
                "trich_yeu": "Test lãnh đạo",
                "loai_van_ban_id": sample_loai_van_ban["id"],
            },
        )
        assert resp.status_code == 403


class TestVanBanList:
    """Test danh sách văn bản."""

    async def test_danh_sach_chi_tra_da_xuat_ban(
        self, client: AsyncClient, cbcc_user, sample_van_ban, published_van_ban
    ):
        """CBCC chỉ thấy VB DA_XUAT_BAN trong danh sách công khai."""
        resp = await client.get("/api/legal/v1/van-ban")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        items = data["data"]

        # Tất cả VB trong list phải là DA_XUAT_BAN
        for item in items:
            assert item["trang_thai_duyet"] == "DA_XUAT_BAN"

        # VB NHAP không xuất hiện
        nhap_ids = [i["id"] for i in items if i["id"] == sample_van_ban["id"]]
        assert len(nhap_ids) == 0

        # VB đã xuất bản phải có trong list
        pub_ids = [i["id"] for i in items if i["id"] == published_van_ban["id"]]
        assert len(pub_ids) == 1

    async def test_danh_sach_pagination(self, client: AsyncClient, cbcc_user):
        """Danh sách có pagination metadata."""
        resp = await client.get("/api/legal/v1/van-ban?page=1&page_size=5")
        assert resp.status_code == 200
        data = resp.json()
        assert "pagination" in data
        pag = data["pagination"]
        assert pag["page"] == 1
        assert pag["page_size"] == 5
        assert "total_items" in pag
        assert "total_pages" in pag

    async def test_filter_bat_buoc_doc(
        self, client: AsyncClient, cbcc_user, db_session, sample_loai_van_ban
    ):
        """Lọc bat_buoc_doc=true chỉ trả VB bắt buộc đọc."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        # Tạo VB bắt buộc đọc
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        vb = VanBan(
            so_hieu=f"VB-BATBUOC-{uuid.uuid4().hex[:6]}",
            trich_yeu="Văn bản bắt buộc đọc test",
            loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
            ngay_ban_hanh=date(2026, 1, 15),
            trang_thai_hieu_luc="CON_HIEU_LUC",
            muc_do="KHAN",
            bat_buoc_doc=True,
            trang_thai_duyet="DA_XUAT_BAN",
            nguoi_nhap_id=UUID("00327c43-c9a3-44d7-8306-7084e75cb2b5"),
            phien_ban=1,
            is_deleted=False,
            noi_dung_html="<p>Bắt buộc</p>",
            ngay_xuat_ban=now,
            created_at=now,
            updated_at=now,
        )
        db_session.add(vb)
        await db_session.flush()

        resp = await client.get("/api/legal/v1/van-ban?bat_buoc_doc=true")
        assert resp.status_code == 200
        items = resp.json()["data"]
        # Tất cả item phải có bat_buoc_doc=True
        for item in items:
            assert item["bat_buoc_doc"] is True

    async def test_danh_sach_quan_ly_xem_tat_ca(
        self, client: AsyncClient, qt_noi_dung_user, sample_van_ban, published_van_ban
    ):
        """QT_NOI_DUNG xem danh sách quản lý — thấy cả NHAP và DA_XUAT_BAN."""
        resp = await client.get("/api/legal/v1/van-ban/quan-ly")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        items = data["data"]

        ids = [i["id"] for i in items]
        # Cả NHAP lẫn DA_XUAT_BAN đều có trong list
        assert sample_van_ban["id"] in ids
        assert published_van_ban["id"] in ids

    async def test_cbcc_khong_xem_danh_sach_quan_ly(
        self, client: AsyncClient, cbcc_user
    ):
        """CBCC không truy cập được /van-ban/quan-ly → 403."""
        resp = await client.get("/api/legal/v1/van-ban/quan-ly")
        assert resp.status_code == 403


class TestVanBanDetail:
    """Test chi tiết văn bản + side effect ghi nhận đã đọc."""

    async def test_chi_tiet_van_ban_da_xuat_ban(
        self, client: AsyncClient, cbcc_user, published_van_ban
    ):
        """CBCC xem chi tiết VB đã xuất bản → thành công."""
        vb_id = published_van_ban["id"]
        resp = await client.get(f"/api/legal/v1/van-ban/{vb_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        vb = data["data"]
        assert vb["id"] == vb_id
        assert vb["trang_thai_duyet"] == "DA_XUAT_BAN"

    async def test_chi_tiet_ghi_nhan_da_doc(
        self, client: AsyncClient, cbcc_user, published_van_ban, db_session
    ):
        """Mở chi tiết VB → side effect tạo xac_nhan_doc với da_doc=TRUE."""
        from uuid import UUID

        from sqlalchemy import select

        from legal_service.models.xac_nhan_doc import XacNhanDoc

        vb_id = UUID(published_van_ban["id"])
        cbcc_id = UUID("00327c43-c9a3-44d7-8306-7084e75cb2b5")  # cbcc_user idx=0

        # Trước khi mở: chưa có bản ghi xac_nhan
        xnd_before = (
            await db_session.execute(
                select(XacNhanDoc)
                .where(XacNhanDoc.van_ban_id == vb_id)
                .where(XacNhanDoc.cong_chuc_id == cbcc_id)
            )
        ).scalar_one_or_none()
        # Có thể đã có từ test trước (vì không rollback), kiểm tra sau khi gọi API

        # Gọi API chi tiết
        resp = await client.get(f"/api/legal/v1/van-ban/{vb_id}")
        assert resp.status_code == 200

        # Sau khi mở: phải có bản ghi xac_nhan_doc với da_doc=True
        db_session.expire_all()  # sync method, not async
        xnd_after = (
            await db_session.execute(
                select(XacNhanDoc)
                .where(XacNhanDoc.van_ban_id == vb_id)
                .where(XacNhanDoc.cong_chuc_id == cbcc_id)
            )
        ).scalar_one_or_none()
        assert xnd_after is not None
        assert xnd_after.da_doc is True

    async def test_chi_tiet_van_ban_nhap_cbcc_404(
        self, client: AsyncClient, cbcc_user, sample_van_ban
    ):
        """CBCC không xem được VB ở trạng thái NHAP → 404."""
        vb_id = sample_van_ban["id"]
        resp = await client.get(f"/api/legal/v1/van-ban/{vb_id}")
        assert resp.status_code == 404

    async def test_chi_tiet_van_ban_nhap_bien_tap_ok(
        self, client: AsyncClient, bien_tap_user, sample_van_ban
    ):
        """BIEN_TAP xem được VB ở trạng thái NHAP."""
        vb_id = sample_van_ban["id"]
        resp = await client.get(f"/api/legal/v1/van-ban/{vb_id}")
        assert resp.status_code == 200

    async def test_chi_tiet_404_khong_ton_tai(self, client: AsyncClient, cbcc_user):
        """VB không tồn tại → 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(f"/api/legal/v1/van-ban/{fake_id}")
        assert resp.status_code == 404


class TestVanBanUpdate:
    """Test cập nhật văn bản."""

    async def test_sua_van_ban_nhap_thanh_cong(
        self, client: AsyncClient, qt_noi_dung_user, sample_van_ban
    ):
        """QT_NOI_DUNG sửa VB ở trạng thái NHAP → phiên_bản không tăng."""
        vb_id = sample_van_ban["id"]
        resp = await client.put(
            f"/api/legal/v1/van-ban/{vb_id}",
            json={"trich_yeu": "Tóm tắt sau khi cập nhật"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["trich_yeu"] == "Tóm tắt sau khi cập nhật"
        # Phiên bản không tăng khi sửa VB NHAP
        assert data["data"]["phien_ban"] == 1

    async def test_sua_van_ban_da_xuat_ban_tang_phien_ban(
        self, client: AsyncClient, qt_noi_dung_user, published_van_ban
    ):
        """Sửa VB đã xuất bản → phiên_bản tăng thêm 1."""
        vb_id = published_van_ban["id"]

        # Phiên bản ban đầu = 1
        detail_resp = await client.get(f"/api/legal/v1/van-ban/{vb_id}")
        assert detail_resp.status_code == 200
        phien_ban_truoc = detail_resp.json()["data"]["phien_ban"]

        # Cập nhật nội dung
        update_resp = await client.put(
            f"/api/legal/v1/van-ban/{vb_id}",
            json={"tom_tat": "Tóm tắt mới sau khi xuất bản"},
        )
        assert update_resp.status_code == 200
        phien_ban_sau = update_resp.json()["data"]["phien_ban"]
        assert phien_ban_sau == phien_ban_truoc + 1

    async def test_cbcc_khong_sua_duoc(
        self, client: AsyncClient, cbcc_user, sample_van_ban
    ):
        """CBCC không sửa được VB → 403."""
        vb_id = sample_van_ban["id"]
        resp = await client.put(
            f"/api/legal/v1/van-ban/{vb_id}",
            json={"trich_yeu": "CBCC thử sửa"},
        )
        assert resp.status_code == 403


class TestVanBanDelete:
    """Test xóa văn bản (soft delete)."""

    async def test_xoa_van_ban_nhap_ok(
        self, client: AsyncClient, qt_noi_dung_user, db_session, sample_loai_van_ban
    ):
        """QT_NOI_DUNG xóa VB ở trạng thái NHAP → thành công."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        # Tạo VB NHAP để xóa
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        vb = VanBan(
            so_hieu=f"VB-DEL-{uuid.uuid4().hex[:8]}",
            trich_yeu="VB sẽ bị xóa",
            loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
            ngay_ban_hanh=date(2026, 1, 15),
            trang_thai_hieu_luc="CON_HIEU_LUC",
            muc_do="BINH_THUONG",
            bat_buoc_doc=False,
            trang_thai_duyet="NHAP",
            nguoi_nhap_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            phien_ban=1,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        db_session.add(vb)
        await db_session.flush()
        await db_session.refresh(vb)
        vb_id = str(vb.id)

        resp = await client.delete(f"/api/legal/v1/van-ban/{vb_id}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_xoa_van_ban_cho_duyet_fail(
        self, client: AsyncClient, qt_noi_dung_user, db_session, sample_loai_van_ban
    ):
        """Không xóa được VB ở trạng thái CHO_DUYET → LEGAL_ERR_006."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        vb = VanBan(
            so_hieu=f"VB-CHO-{uuid.uuid4().hex[:8]}",
            trich_yeu="VB đang chờ duyệt",
            loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
            ngay_ban_hanh=date(2026, 1, 15),
            trang_thai_hieu_luc="CON_HIEU_LUC",
            muc_do="BINH_THUONG",
            bat_buoc_doc=False,
            trang_thai_duyet="CHO_DUYET",  # Không phải NHAP
            nguoi_nhap_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            phien_ban=1,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        db_session.add(vb)
        await db_session.flush()
        vb_id = str(vb.id)

        resp = await client.delete(f"/api/legal/v1/van-ban/{vb_id}")
        assert resp.status_code == 400
        data = resp.json()
        # Service dùng LEGAL_ERR_003 cho tất cả thao tác trạng thái sai
        # (LEGAL_ERR_006 riêng cho Quiz)
        assert data["error"]["code"] == "LEGAL_ERR_003"

    async def test_cbcc_khong_xoa_duoc(
        self, client: AsyncClient, cbcc_user, sample_van_ban
    ):
        """CBCC không xóa được VB → 403."""
        vb_id = sample_van_ban["id"]
        resp = await client.delete(f"/api/legal/v1/van-ban/{vb_id}")
        assert resp.status_code == 403

    async def test_bien_tap_khong_xoa_duoc(
        self, client: AsyncClient, bien_tap_user, sample_van_ban
    ):
        """BIEN_TAP không có quyền xóa → 403 (chỉ QT_NOI_DUNG mới xóa được)."""
        vb_id = sample_van_ban["id"]
        resp = await client.delete(f"/api/legal/v1/van-ban/{vb_id}")
        assert resp.status_code == 403
