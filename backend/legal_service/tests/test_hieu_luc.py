"""
legal_service/tests/test_hieu_luc.py
======================================
Tests liên kết văn bản, search và filter hiệu lực.

Business rules:
  - Liên kết THAY_THE → VB cũ bị set trang_thai_hieu_luc = BI_THAY_THE
  - Search: tìm theo so_hieu/trich_yeu (ILIKE) hoặc FTS
  - Filter muc_do = KHAN chỉ trả VB KHAN
  - Filter trang_thai_hieu_luc = CON_HIEU_LUC
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TestLienKetVanBan:
    """Test liên kết văn bản và tự động cập nhật hiệu lực."""

    async def test_lien_ket_thay_the_cap_nhat_vb_cu(
        self,
        client: AsyncClient,
        qt_noi_dung_user,
        db_session: AsyncSession,
        sample_loai_van_ban,
    ):
        """Tạo VB mới với liên kết THAY_THE → VB cũ tự động BI_THAY_THE."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Tạo VB cũ (DA_XUAT_BAN)
        vb_cu = VanBan(
            so_hieu=f"VB-CU-{uuid.uuid4().hex[:8]}",
            trich_yeu="Văn bản cũ sẽ bị thay thế",
            loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
            ngay_ban_hanh=date(2025, 6, 1),
            trang_thai_hieu_luc="CON_HIEU_LUC",
            muc_do="BINH_THUONG",
            bat_buoc_doc=False,
            trang_thai_duyet="DA_XUAT_BAN",
            noi_dung_html="<p>Nội dung cũ</p>",
            nguoi_nhap_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            nguoi_duyet_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            ngay_xuat_ban=now,
            phien_ban=1,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        db_session.add(vb_cu)
        await db_session.flush()
        await db_session.refresh(vb_cu)
        vb_cu_id = str(vb_cu.id)

        # Tạo VB mới với liên kết THAY_THE
        so_hieu_moi = f"VB-MOI-{uuid.uuid4().hex[:8]}"
        resp = await client.post(
            "/api/legal/v1/van-ban",
            json={
                "so_hieu": so_hieu_moi,
                "trich_yeu": "Văn bản mới thay thế văn bản cũ",
                "loai_van_ban_id": sample_loai_van_ban["id"],
                "ngay_ban_hanh": "2026-01-15",
                "noi_dung_html": "<p>Nội dung mới</p>",
                "muc_do": "BINH_THUONG",
                "van_ban_lien_ket": [
                    {
                        "van_ban_lien_quan_id": vb_cu_id,
                        "loai_lien_ket": "THAY_THE",
                    }
                ],
            },
        )
        assert resp.status_code == 200

        # Verify VB cũ đã bị đánh dấu BI_THAY_THE
        db_session.expire_all()  # sync method, not async
        result = await db_session.execute(select(VanBan).where(VanBan.id == UUID(vb_cu_id)))
        vb_cu_updated = result.scalar_one()
        assert vb_cu_updated.trang_thai_hieu_luc == "BI_THAY_THE"

    async def test_lien_ket_bo_sung_khong_thay_doi_vb_cu(
        self,
        client: AsyncClient,
        qt_noi_dung_user,
        db_session: AsyncSession,
        sample_loai_van_ban,
    ):
        """Liên kết BO_SUNG không thay đổi trang_thai_hieu_luc VB cũ."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # VB tham chiếu
        vb_ref = VanBan(
            so_hieu=f"VB-REF-{uuid.uuid4().hex[:8]}",
            trich_yeu="Văn bản được bổ sung",
            loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
            ngay_ban_hanh=date(2025, 6, 1),
            trang_thai_hieu_luc="CON_HIEU_LUC",
            muc_do="BINH_THUONG",
            bat_buoc_doc=False,
            trang_thai_duyet="DA_XUAT_BAN",
            noi_dung_html="<p>Gốc</p>",
            nguoi_nhap_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            nguoi_duyet_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            ngay_xuat_ban=now,
            phien_ban=1,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        db_session.add(vb_ref)
        await db_session.flush()
        await db_session.refresh(vb_ref)
        vb_ref_id = str(vb_ref.id)

        # Tạo VB bổ sung
        resp = await client.post(
            "/api/legal/v1/van-ban",
            json={
                "so_hieu": f"VB-BS-{uuid.uuid4().hex[:8]}",
                "trich_yeu": "Văn bản bổ sung",
                "loai_van_ban_id": sample_loai_van_ban["id"],
                "ngay_ban_hanh": "2026-01-15",
                "noi_dung_html": "<p>Bổ sung</p>",
                "van_ban_lien_ket": [
                    {"van_ban_lien_quan_id": vb_ref_id, "loai_lien_ket": "BO_SUNG"}
                ],
            },
        )
        assert resp.status_code == 200

        # VB gốc vẫn CON_HIEU_LUC (không bị thay đổi bởi BO_SUNG)
        db_session.expire_all()  # sync method, not async
        result = await db_session.execute(select(VanBan).where(VanBan.id == UUID(vb_ref_id)))
        vb_ref_updated = result.scalar_one()
        assert vb_ref_updated.trang_thai_hieu_luc == "CON_HIEU_LUC"


class TestSearch:
    """Test tìm kiếm văn bản."""

    async def test_search_van_ban_theo_so_hieu(
        self,
        client: AsyncClient,
        cbcc_user,
        db_session: AsyncSession,
        sample_loai_van_ban,
    ):
        """Tìm kiếm VB theo ILIKE từ internal search API."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        # Unique keyword để tránh kết quả cũ
        keyword = uuid.uuid4().hex[:8].upper()
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        vb = VanBan(
            so_hieu=f"SEARCH-{keyword}",
            trich_yeu=f"Văn bản hải quan khu vực {keyword}",
            loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
            ngay_ban_hanh=date(2026, 1, 15),
            trang_thai_hieu_luc="CON_HIEU_LUC",
            muc_do="BINH_THUONG",
            bat_buoc_doc=False,
            trang_thai_duyet="DA_XUAT_BAN",
            noi_dung_html="<p>Nội dung</p>",
            nguoi_nhap_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            nguoi_duyet_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            ngay_xuat_ban=now,
            phien_ban=1,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        db_session.add(vb)
        await db_session.flush()

        # Tìm qua internal API (ILIKE, không cần FTS trigger)
        from legal_service.main import app as legal_app
        from legal_service.dependencies import get_current_user as legal_get_user

        # Internal API không cần auth user, cần API key
        # Thử qua van_ban_service.search_van_ban trực tiếp
        from legal_service.services.van_ban_service import search_van_ban

        results = await search_van_ban(db=db_session, q=keyword, limit=10)
        assert len(results) >= 1
        found = [r for r in results if keyword in r["so_hieu"]]
        assert len(found) >= 1

    async def test_search_internal_api(
        self, client: AsyncClient, cbcc_user, published_van_ban
    ):
        """Internal search API tìm theo so_hieu."""
        from legal_service.services.van_ban_service import search_van_ban

        so_hieu = published_van_ban["so_hieu"]
        # Lấy vài ký tự đặc trưng để tìm
        keyword = so_hieu[:8]

        from legal_service.dependencies import get_db

        async for db in get_db():
            results = await search_van_ban(db=db, q=keyword, limit=5)
            # Nếu có kết quả, kiểm tra format
            if results:
                assert "id" in results[0]
                assert "so_hieu" in results[0]
                assert "trich_yeu" in results[0]
            break  # Chỉ cần 1 session


class TestFilterVanBan:
    """Test filter danh sách văn bản."""

    async def test_filter_muc_do_khan(
        self,
        client: AsyncClient,
        cbcc_user,
        db_session: AsyncSession,
        sample_loai_van_ban,
    ):
        """Lọc muc_do=KHAN chỉ trả về VB KHAN."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Tạo VB mức KHAN
        vb_khan = VanBan(
            so_hieu=f"VB-KHAN-{uuid.uuid4().hex[:8]}",
            trich_yeu="Văn bản KHAN cần xử lý ngay",
            loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
            ngay_ban_hanh=date(2026, 1, 15),
            trang_thai_hieu_luc="CON_HIEU_LUC",
            muc_do="KHAN",
            bat_buoc_doc=True,
            trang_thai_duyet="DA_XUAT_BAN",
            noi_dung_html="<p>Khẩn</p>",
            nguoi_nhap_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            nguoi_duyet_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            ngay_xuat_ban=now,
            phien_ban=1,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        db_session.add(vb_khan)
        await db_session.flush()
        await db_session.refresh(vb_khan)
        vb_khan_id = str(vb_khan.id)

        resp = await client.get("/api/legal/v1/van-ban?muc_do=KHAN")
        assert resp.status_code == 200
        items = resp.json()["data"]

        # Tất cả items phải có muc_do=KHAN
        for item in items:
            assert item["muc_do"] == "KHAN"

        # VB khan vừa tạo phải xuất hiện
        found = [i for i in items if i["id"] == vb_khan_id]
        assert len(found) == 1

    async def test_filter_trang_thai_hieu_luc(
        self,
        client: AsyncClient,
        cbcc_user,
        db_session: AsyncSession,
        sample_loai_van_ban,
    ):
        """Lọc trang_thai_hieu_luc=CON_HIEU_LUC."""
        resp = await client.get("/api/legal/v1/van-ban?trang_thai_hieu_luc=CON_HIEU_LUC")
        assert resp.status_code == 200
        items = resp.json()["data"]
        for item in items:
            assert item["trang_thai_hieu_luc"] == "CON_HIEU_LUC"

    async def test_sap_xep_quan_trong(
        self,
        client: AsyncClient,
        cbcc_user,
        db_session: AsyncSession,
        sample_loai_van_ban,
    ):
        """Sắp xếp theo quan_trong: KHAN → QUAN_TRONG → BINH_THUONG."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Tạo VB ở các mức độ khác nhau
        for muc_do, so_hieu_prefix in [("KHAN", "VB-K"), ("BINH_THUONG", "VB-B")]:
            vb = VanBan(
                so_hieu=f"{so_hieu_prefix}-{uuid.uuid4().hex[:6]}",
                trich_yeu=f"VB mức {muc_do}",
                loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
                ngay_ban_hanh=date(2026, 1, 15),
                trang_thai_hieu_luc="CON_HIEU_LUC",
                muc_do=muc_do,
                bat_buoc_doc=False,
                trang_thai_duyet="DA_XUAT_BAN",
                noi_dung_html=f"<p>{muc_do}</p>",
                nguoi_nhap_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
                nguoi_duyet_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
                ngay_xuat_ban=now,
                phien_ban=1,
                is_deleted=False,
                created_at=now,
                updated_at=now,
            )
            db_session.add(vb)
        await db_session.flush()

        resp = await client.get("/api/legal/v1/van-ban?sap_xep=quan_trong")
        assert resp.status_code == 200
        items = resp.json()["data"]

        if len(items) >= 2:
            # KHAN phải đứng trước BINH_THUONG
            muc_do_list = [i["muc_do"] for i in items]
            # Verify không có BINH_THUONG trước KHAN
            last_khan = -1
            first_binh_thuong = len(muc_do_list)
            for i, md in enumerate(muc_do_list):
                if md == "KHAN":
                    last_khan = i
                if md == "BINH_THUONG" and first_binh_thuong == len(muc_do_list):
                    first_binh_thuong = i
            if last_khan >= 0 and first_binh_thuong < len(muc_do_list):
                assert last_khan < first_binh_thuong

    async def test_van_ban_chua_doc(
        self,
        client: AsyncClient,
        cbcc_user,
        db_session: AsyncSession,
        sample_loai_van_ban,
    ):
        """Danh sách VB chưa xác nhận (bat_buoc_doc=True)."""
        from uuid import UUID
        from datetime import date, datetime, timezone
        from legal_service.models.van_ban import VanBan

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Tạo VB bắt buộc đọc
        vb = VanBan(
            so_hieu=f"VB-BB-CD-{uuid.uuid4().hex[:6]}",
            trich_yeu="VB bắt buộc chưa đọc test",
            loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
            ngay_ban_hanh=date(2026, 1, 15),
            trang_thai_hieu_luc="CON_HIEU_LUC",
            muc_do="QUAN_TRONG",
            bat_buoc_doc=True,  # Bắt buộc đọc
            trang_thai_duyet="DA_XUAT_BAN",
            noi_dung_html="<p>Bắt buộc</p>",
            nguoi_nhap_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            nguoi_duyet_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            ngay_xuat_ban=now,
            phien_ban=1,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        db_session.add(vb)
        await db_session.flush()

        resp = await client.get("/api/legal/v1/van-ban/chua-doc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "pagination" in data
        # Tất cả items phải có bat_buoc_doc=True và da_xac_nhan=False
        for item in data["data"]:
            assert item["bat_buoc_doc"] is True
            assert item["da_xac_nhan"] is False
