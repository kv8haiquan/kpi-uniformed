"""
portal_service/tests/test_bai_viet.py
=======================================
Tests cho Bài viết API — CRUD + Workflow đầy đủ.

Business rules:
  - BIEN_TAP, QT_NOI_DUNG tạo bài viết (trạng thái NHAP)
  - Danh sách công khai: chỉ XUAT_BAN, is_ghim=True đứng đầu
  - Danh sách quản lý: BIEN_TAP chỉ thấy bài mình, QT_NOI_DUNG thấy tất cả
  - Chi tiết bài → tăng so_luot_xem += 1
  - Sửa/xóa: chỉ khi NHAP; BIEN_TAP chỉ bài mình soạn
  - Workflow: NHAP→KIEM_TRA (BIEN_TAP người soạn), KIEM_TRA→DUYET (QT),
              DUYET→XUAT_BAN (Lãnh đạo), XUAT_BAN→THU_HOI (QT)
  - Ghim tối đa 3 bài; chỉ QT_NOI_DUNG/ADMIN
"""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from portal_service.main import app
from portal_service.models.bai_viet import BaiViet

# Real cong chuc IDs (FK constraint)
_REAL_CC_IDS = [
    "00327c43-c9a3-44d7-8306-7084e75cb2b5",
    "01014af6-1505-495b-95ab-8c1503cfa061",
    "01abd5c1-5c34-475b-8ea8-803ad461f66d",
    "02a492ad-fb32-430d-8c4e-e9ded9b8d964",
    "02fed37c-1c82-4250-a6ea-7bf9db7b6955",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_bai_viet(client: AsyncClient, chuyen_muc_id: str = None, tieu_de: str = "Bai viet test") -> dict:
    """Helper: tạo bài viết qua API (yêu cầu bien_tap hoặc qt_noi_dung user đã set)."""
    payload = {
        "tieu_de": tieu_de,
        "noi_dung": "<p>Noi dung test</p>",
        "tom_tat": "Tom tat",
    }
    if chuyen_muc_id:
        payload["chuyen_muc_id"] = chuyen_muc_id

    resp = await client.post("/api/v1/bai-viet", json=payload)
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    return resp.json()["data"]


async def _doi_trang_thai(client: AsyncClient, bai_viet_id: str, trang_thai_moi: str):
    """Helper: đổi trạng thái bài viết."""
    return await client.patch(
        f"/api/v1/bai-viet/{bai_viet_id}/trang-thai",
        json={"trang_thai_moi": trang_thai_moi},
    )


# ===========================================================================
# Test Tạo bài viết
# ===========================================================================


class TestBaiVietTao:
    """Test tạo bài viết."""

    async def test_bien_tap_tao_thanh_cong(
        self, client: AsyncClient, bien_tap_user, sample_chuyen_muc
    ):
        """BIEN_TAP tạo bài viết → trạng thái NHAP."""
        resp = await client.post(
            "/api/v1/bai-viet",
            json={
                "chuyen_muc_id": sample_chuyen_muc["id"],
                "tieu_de": "Bai viet moi cua bien tap",
                "noi_dung": "<p>Noi dung bai viet</p>",
                "tom_tat": "Tom tat ngan",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        bv = data["data"]
        assert bv["tieu_de"] == "Bai viet moi cua bien tap"
        assert bv["trang_thai"] == "NHAP"
        assert bv["is_ghim"] is False

    async def test_qt_noi_dung_tao_thanh_cong(
        self, client: AsyncClient, qt_noi_dung_user, sample_chuyen_muc
    ):
        """QT_NOI_DUNG tạo bài viết thành công."""
        resp = await client.post(
            "/api/v1/bai-viet",
            json={
                "tieu_de": "Bai viet cua QT",
                "noi_dung": "<p>Noi dung</p>",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["trang_thai"] == "NHAP"

    async def test_cbcc_khong_tao_duoc(
        self, client: AsyncClient, cbcc_user, sample_chuyen_muc
    ):
        """CBCC không có quyền tạo bài viết."""
        resp = await client.post(
            "/api/v1/bai-viet",
            json={
                "tieu_de": "Bai cua CBCC",
                "noi_dung": "<p>Noi dung</p>",
            },
        )
        assert resp.status_code == 403


# ===========================================================================
# Test Danh sách
# ===========================================================================


class TestBaiVietDanhSach:
    """Test danh sách bài viết."""

    async def test_danh_sach_cong_khai_chi_xuat_ban(
        self, client: AsyncClient, cbcc_user, sample_bai_viet_nhap, sample_bai_viet_xuat_ban
    ):
        """Danh sách công khai chỉ trả XUAT_BAN, không trả NHAP."""
        resp = await client.get("/api/v1/bai-viet")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        ids = [bv["id"] for bv in data["data"]]
        assert sample_bai_viet_xuat_ban["id"] in ids
        assert sample_bai_viet_nhap["id"] not in ids

    async def test_danh_sach_quan_ly_bien_tap_chi_thay_bai_minh(
        self, client: AsyncClient, bien_tap_user, sample_bai_viet_nhap, db_session: AsyncSession
    ):
        """BIEN_TAP chỉ thấy bài mình soạn trong danh sách quản lý."""
        from uuid import UUID
        # Tạo bài của qt_noi_dung_user (idx=2) — bien_tap_user không được thấy
        bv_khac = BaiViet(
            tieu_de="Bai cua nguoi khac",
            noi_dung="<p>noi dung</p>",
            trang_thai="NHAP",
            nguoi_soan_id=UUID(_REAL_CC_IDS[2]),  # qt_noi_dung
            is_ghim=False,
            so_luot_xem=0,
            is_deleted=False,
        )
        db_session.add(bv_khac)
        await db_session.flush()

        resp = await client.get("/api/v1/bai-viet/quan-ly")
        assert resp.status_code == 200
        data = resp.json()
        ids = [bv["id"] for bv in data["data"]]
        # Thấy bài mình
        assert sample_bai_viet_nhap["id"] in ids
        # Không thấy bài người khác
        assert str(bv_khac.id) not in ids

    async def test_danh_sach_quan_ly_qt_thay_tat_ca(
        self, client: AsyncClient, qt_noi_dung_user, sample_bai_viet_nhap
    ):
        """QT_NOI_DUNG thấy tất cả bài trong danh sách quản lý."""
        resp = await client.get("/api/v1/bai-viet/quan-ly")
        assert resp.status_code == 200
        data = resp.json()
        ids = [bv["id"] for bv in data["data"]]
        assert sample_bai_viet_nhap["id"] in ids


# ===========================================================================
# Test Chi tiết
# ===========================================================================


class TestBaiVietChiTiet:
    """Test chi tiết bài viết."""

    async def test_chi_tiet_tang_luot_xem(
        self, client: AsyncClient, cbcc_user, sample_bai_viet_xuat_ban, db_session: AsyncSession
    ):
        """Xem chi tiết bài viết → so_luot_xem tăng lên 1."""
        bv_id = sample_bai_viet_xuat_ban["id"]
        stmt = select(BaiViet).where(BaiViet.id == uuid.UUID(bv_id))
        result = await db_session.execute(stmt)
        bv_before = result.scalar_one()
        luot_xem_truoc = bv_before.so_luot_xem

        resp = await client.get(f"/api/v1/bai-viet/{bv_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["so_luot_xem"] == luot_xem_truoc + 1

    async def test_chi_tiet_404(self, client: AsyncClient, cbcc_user):
        """Chi tiết bài không tồn tại → 404."""
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/api/v1/bai-viet/{fake_id}")
        assert resp.status_code == 404


# ===========================================================================
# Test Sửa + Xóa
# ===========================================================================


class TestBaiVietSuaXoa:
    """Test sửa và xóa bài viết."""

    async def test_sua_bai_nhap_thanh_cong(
        self, client: AsyncClient, bien_tap_user, sample_bai_viet_nhap
    ):
        """BIEN_TAP sửa bài mình soạn ở NHAP thành công."""
        resp = await client.put(
            f"/api/v1/bai-viet/{sample_bai_viet_nhap['id']}",
            json={"tieu_de": "Tieu de da duoc cap nhat"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["tieu_de"] == "Tieu de da duoc cap nhat"

    async def test_bien_tap_khong_sua_bai_nguoi_khac(
        self, client: AsyncClient, bien_tap_user, db_session: AsyncSession
    ):
        """BIEN_TAP không sửa được bài người khác."""
        from uuid import UUID
        bv = BaiViet(
            tieu_de="Bai cua QT",
            noi_dung="<p>noi dung</p>",
            trang_thai="NHAP",
            nguoi_soan_id=UUID(_REAL_CC_IDS[2]),  # qt_noi_dung
            is_ghim=False,
            so_luot_xem=0,
            is_deleted=False,
        )
        db_session.add(bv)
        await db_session.flush()

        resp = await client.put(
            f"/api/v1/bai-viet/{bv.id}",
            json={"tieu_de": "Bien tap co gang sua"},
        )
        assert resp.status_code == 403

    async def test_xoa_bai_nhap_thanh_cong(
        self, client: AsyncClient, bien_tap_user, sample_bai_viet_nhap
    ):
        """BIEN_TAP xóa bài mình ở trạng thái NHAP."""
        resp = await client.delete(
            f"/api/v1/bai-viet/{sample_bai_viet_nhap['id']}"
        )
        assert resp.status_code == 200

    async def test_khong_xoa_bai_xuat_ban(
        self, client: AsyncClient, qt_noi_dung_user, sample_bai_viet_xuat_ban
    ):
        """Không xóa được bài đã xuất bản (phải thu hồi trước)."""
        resp = await client.delete(
            f"/api/v1/bai-viet/{sample_bai_viet_xuat_ban['id']}"
        )
        assert resp.status_code == 400


# ===========================================================================
# Test Workflow đầy đủ
# ===========================================================================


class TestBaiVietWorkflow:
    """Test workflow chuyển trạng thái bài viết."""

    async def test_workflow_day_du(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        sample_chuyen_muc,
    ):
        """Happy path: NHAP → KIEM_TRA → DUYET → XUAT_BAN.

        Chú ý: test này dùng app.dependency_overrides trực tiếp để chuyển user.
        """
        from portal_service.dependencies import get_current_user
        from shared.auth import TokenPayload
        from datetime import timedelta

        def _set_override(user: TokenPayload):
            async def _override():
                return user
            app.dependency_overrides[get_current_user] = _override

        _exp = int((datetime.now(timezone.utc).timestamp()) + 3600)

        # Bước 1: BIEN_TAP tạo bài
        bien_tap = TokenPayload(
            sub=_REAL_CC_IDS[1], exp=_exp, type="access",
            ma_cc="BT-01", vai_tro="CC", don_vi_id=None,
            is_lanh_dao=False, platform_roles=["BIEN_TAP"],
        )
        _set_override(bien_tap)
        bv = await _create_bai_viet(client, sample_chuyen_muc["id"])
        bv_id = bv["id"]
        assert bv["trang_thai"] == "NHAP"

        # Bước 2: BIEN_TAP gửi duyệt
        resp = await _doi_trang_thai(client, bv_id, "KIEM_TRA")
        assert resp.status_code == 200
        assert resp.json()["data"]["trang_thai"] == "KIEM_TRA"

        # Bước 3: QT_NOI_DUNG duyệt
        qt = TokenPayload(
            sub=_REAL_CC_IDS[2], exp=_exp, type="access",
            ma_cc="QT-02", vai_tro="CC", don_vi_id=None,
            is_lanh_dao=False, platform_roles=["QT_NOI_DUNG"],
        )
        _set_override(qt)
        resp = await _doi_trang_thai(client, bv_id, "DUYET")
        assert resp.status_code == 200
        assert resp.json()["data"]["trang_thai"] == "DUYET"

        # Bước 4: Lãnh đạo xuất bản
        lanh_dao = TokenPayload(
            sub=_REAL_CC_IDS[3], exp=_exp, type="access",
            ma_cc="LD-03", vai_tro="TDV", don_vi_id=None,
            is_lanh_dao=True, platform_roles=[],
        )
        _set_override(lanh_dao)
        resp = await _doi_trang_thai(client, bv_id, "XUAT_BAN")
        assert resp.status_code == 200
        bv_final = resp.json()["data"]
        assert bv_final["trang_thai"] == "XUAT_BAN"
        assert bv_final["ngay_xuat_ban"] is not None

    async def test_workflow_thu_hoi(
        self,
        client: AsyncClient,
        qt_noi_dung_user,
        sample_bai_viet_xuat_ban,
    ):
        """QT_NOI_DUNG thu hồi bài đã xuất bản."""
        resp = await _doi_trang_thai(
            client, sample_bai_viet_xuat_ban["id"], "THU_HOI"
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["trang_thai"] == "THU_HOI"

    async def test_workflow_tu_choi_kiem_tra(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        sample_chuyen_muc,
    ):
        """QT_NOI_DUNG từ chối bài KIEM_TRA → trả về NHAP."""
        from portal_service.dependencies import get_current_user
        from shared.auth import TokenPayload

        _exp = int(datetime.now(timezone.utc).timestamp()) + 3600

        bien_tap = TokenPayload(
            sub=_REAL_CC_IDS[1], exp=_exp, type="access",
            ma_cc="BT-01", vai_tro="CC", don_vi_id=None,
            is_lanh_dao=False, platform_roles=["BIEN_TAP"],
        )

        async def _set_bt():
            return bien_tap

        app.dependency_overrides[get_current_user] = _set_bt
        bv = await _create_bai_viet(client, sample_chuyen_muc["id"])
        await _doi_trang_thai(client, bv["id"], "KIEM_TRA")

        # QT từ chối
        qt = TokenPayload(
            sub=_REAL_CC_IDS[2], exp=_exp, type="access",
            ma_cc="QT-02", vai_tro="CC", don_vi_id=None,
            is_lanh_dao=False, platform_roles=["QT_NOI_DUNG"],
        )

        async def _set_qt():
            return qt

        app.dependency_overrides[get_current_user] = _set_qt
        resp = await _doi_trang_thai(client, bv["id"], "NHAP")
        assert resp.status_code == 200
        assert resp.json()["data"]["trang_thai"] == "NHAP"

    async def test_workflow_invalid_nhap_xuat_ban(
        self, client: AsyncClient, lanh_dao_user, sample_bai_viet_nhap
    ):
        """Chuyển thẳng NHAP → XUAT_BAN → 400 (không hợp lệ)."""
        resp = await _doi_trang_thai(
            client, sample_bai_viet_nhap["id"], "XUAT_BAN"
        )
        assert resp.status_code == 400

    async def test_bien_tap_khong_gui_duyet_bai_nguoi_khac(
        self,
        client: AsyncClient,
        bien_tap_user,
        db_session: AsyncSession,
    ):
        """BIEN_TAP không gửi duyệt bài người khác."""
        from uuid import UUID
        bv = BaiViet(
            tieu_de="Bai cua nguoi khac",
            noi_dung="<p>noi dung</p>",
            trang_thai="NHAP",
            nguoi_soan_id=UUID(_REAL_CC_IDS[2]),  # qt
            is_ghim=False,
            so_luot_xem=0,
            is_deleted=False,
        )
        db_session.add(bv)
        await db_session.flush()

        resp = await _doi_trang_thai(client, str(bv.id), "KIEM_TRA")
        assert resp.status_code == 403

    async def test_cbcc_khong_doi_trang_thai(
        self, client: AsyncClient, cbcc_user, sample_bai_viet_nhap
    ):
        """CBCC không thể đổi trạng thái bài viết."""
        resp = await _doi_trang_thai(
            client, sample_bai_viet_nhap["id"], "KIEM_TRA"
        )
        assert resp.status_code == 403

    async def test_lanh_dao_khong_xuat_ban_tu_kiem_tra(
        self,
        client: AsyncClient,
        lanh_dao_user,
        db_session: AsyncSession,
    ):
        """Lãnh đạo không thể xuất bản bài đang ở KIEM_TRA (cần qua DUYET)."""
        from uuid import UUID
        bv = BaiViet(
            tieu_de="Bai o KIEM_TRA",
            noi_dung="<p>noi dung</p>",
            trang_thai="KIEM_TRA",
            nguoi_soan_id=UUID(_REAL_CC_IDS[1]),
            is_ghim=False,
            so_luot_xem=0,
            is_deleted=False,
        )
        db_session.add(bv)
        await db_session.flush()

        resp = await _doi_trang_thai(client, str(bv.id), "XUAT_BAN")
        assert resp.status_code == 400


# ===========================================================================
# Test Ghim bài viết
# ===========================================================================


class TestBaiVietGhim:
    """Test ghim / bỏ ghim bài viết."""

    async def test_qt_noi_dung_ghim_thanh_cong(
        self, client: AsyncClient, qt_noi_dung_user, sample_bai_viet_xuat_ban
    ):
        """QT_NOI_DUNG ghim bài thành công."""
        resp = await client.patch(
            f"/api/v1/bai-viet/{sample_bai_viet_xuat_ban['id']}/ghim",
            json={"is_ghim": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["is_ghim"] is True

    async def test_ghim_qua_3_bai_bi_loi(
        self, client: AsyncClient, qt_noi_dung_user, db_session: AsyncSession
    ):
        """Ghim quá 3 bài cùng lúc → 400."""
        from uuid import UUID
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Tạo 3 bài đã ghim
        for i in range(3):
            bv = BaiViet(
                tieu_de=f"Bai ghim {i}",
                noi_dung=f"<p>noi dung {i}</p>",
                trang_thai="XUAT_BAN",
                nguoi_soan_id=UUID(_REAL_CC_IDS[1]),
                is_ghim=True,
                ngay_xuat_ban=now,
                so_luot_xem=0,
                is_deleted=False,
            )
            db_session.add(bv)
        await db_session.flush()

        # Tạo bài thứ 4 (chưa ghim) và thử ghim → lỗi
        bv_new = BaiViet(
            tieu_de="Bai muon ghim thu 4",
            noi_dung="<p>noi dung</p>",
            trang_thai="XUAT_BAN",
            nguoi_soan_id=UUID(_REAL_CC_IDS[1]),
            is_ghim=False,
            ngay_xuat_ban=now,
            so_luot_xem=0,
            is_deleted=False,
        )
        db_session.add(bv_new)
        await db_session.flush()

        resp = await client.patch(
            f"/api/v1/bai-viet/{bv_new.id}/ghim",
            json={"is_ghim": True},
        )
        assert resp.status_code == 400

    async def test_cbcc_khong_ghim_duoc(
        self, client: AsyncClient, cbcc_user, sample_bai_viet_xuat_ban
    ):
        """CBCC không có quyền ghim bài."""
        resp = await client.patch(
            f"/api/v1/bai-viet/{sample_bai_viet_xuat_ban['id']}/ghim",
            json={"is_ghim": True},
        )
        assert resp.status_code == 403
