"""
Phân quyền tài liệu hai mức hạn chế — G5.4.

Cơ chế này chưa từng vận hành ở hệ cũ (587 file, không dòng nào mang giá trị
`LEADER_*`), nên không có hành vi cũ để đối chiếu — chỉ có một yêu cầu phải
làm cho đúng. Vì thế phần lớn test dưới đây là test rò rỉ: mỗi đường ra của
một tài liệu đều phải bị chặn, không chỉ nút bấm trên giao diện.

Đường ra đã biết của một tài liệu:
  1. danh sách tài liệu cuộc họp (nhúng sẵn token xem)
  2. /tai-lieu/{id}/xem  → cấp token xem
  3. /tai-lieu/{id}/tai  → cấp token tải
  4. trình chiếu (đẩy nội dung ra cả phòng họp)
  5. xoá và sửa siêu dữ liệu
"""

from __future__ import annotations

import io

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.tests.conftest import _make_user, _set_user

BASE_CUOC_HOP = "/api/v1/hop-khong-giay/cuoc-hop"
BASE = "/api/v1/hop-khong-giay/tai-lieu"


def _doi_user(ma_cc: str, don_vi_id, **kw):
    u = _make_user(ma_cc, don_vi_id, **kw)
    _set_user(u)
    return u


def _payload_hop(don_vi_id, chu_toa_id):
    return {
        "tieu_de": "Test G5.4 — phân quyền tài liệu",
        "khoi": "CHUYEN_MON",
        "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": "2026-09-15",
        "gio_bat_dau": "08:30",
        "don_vi_to_chuc_id": str(don_vi_id),
        "chu_toa_id": str(chu_toa_id),
        "thanh_phan": [],
    }


async def _tao_hop(client: AsyncClient, don_vi_id, chu_toa_id) -> str:
    r = await client.post(BASE_CUOC_HOP + "/",
                          json=_payload_hop(don_vi_id, chu_toa_id))
    assert r.status_code in (200, 201), r.text
    return r.json()["data"]["id"]


async def _tai_len(client: AsyncClient, ch_id: str, muc: str,
                   ten="tai-lieu-mat.pdf") -> str:
    r = await client.post(
        BASE + "/upload",
        data={"cuoc_hop_id": ch_id, "phan_quyen": muc},
        files={"file": (ten, io.BytesIO(b"%PDF-1.4 noi dung"),
                        "application/pdf")})
    assert r.status_code == 201, r.text
    assert r.json()["data"]["phan_quyen"] == muc
    return r.json()["data"]["id"]


async def _moi_du_hop(db: AsyncSession, ch_id: str, cong_chuc_id) -> None:
    """Mời một người vào cuộc họp để họ qua được `_can_view_cuoc_hop`.

    Không mời thì test sẽ đỏ vì 403 quyền xem CUỘC HỌP, che mất điều đang
    muốn kiểm là quyền xem TÀI LIỆU.
    """
    await db.execute(sa_text("""
        INSERT INTO meeting.thanh_phan (cuoc_hop_id, cong_chuc_id,
                                        loai_tham_du)
        VALUES (:ch, :cc, 'BAT_BUOC')
        ON CONFLICT DO NOTHING
    """), {"ch": ch_id, "cc": str(cong_chuc_id)})
    await db.flush()


# ── danh mục mức ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_muc_dat_duoc_theo_vai_tro(
    client: AsyncClient, cbcc_user, seed_test_users,
):
    """Không ai được đặt mức cao hơn quyền xem của chính mình."""
    ds = (await client.get(BASE + "/muc-phan-quyen")).json()["data"]
    duoc = {x["ma"] for x in ds if x["dat_duoc"]}
    assert duoc == {"CONG_KHAI"}, "Công chức thường chỉ đặt được mức công khai"

    _doi_user("TEST-G3-002", seed_test_users["don_vi_a"], is_lanh_dao=True)
    ds = (await client.get(BASE + "/muc-phan-quyen")).json()["data"]
    duoc = {x["ma"] for x in ds if x["dat_duoc"]}
    assert duoc == {"CONG_KHAI", "LANH_DAO_DON_VI"}

    _doi_user("TEST-G3-003", seed_test_users["don_vi_b"], vai_tro="PCCT",
              is_lanh_dao=True)
    ds = (await client.get(BASE + "/muc-phan-quyen")).json()["data"]
    assert all(x["dat_duoc"] for x in ds)


@pytest.mark.asyncio
async def test_khong_dat_duoc_muc_cao_hon_minh(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """`chu_toa_user` là TDV — lãnh đạo đơn vị, không phải lãnh đạo Chi cục."""
    ch = await _tao_hop(client, seed_test_users["don_vi_a"], chu_toa_user.sub)
    r = await client.post(
        BASE + "/upload",
        data={"cuoc_hop_id": ch, "phan_quyen": "LANH_DAO_CHI_CUC"},
        files={"file": ("a.pdf", io.BytesIO(b"x"), "application/pdf")})
    assert r.status_code == 403
    assert r.json()["detail"]["error"]["code"] == "DOC_LEVEL_TOO_HIGH"


@pytest.mark.asyncio
async def test_muc_khong_hop_le_bi_chan(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """`HAN_CHE` của bản cũ đã bị loại khỏi danh mục (migration meeting_023)."""
    ch = await _tao_hop(client, seed_test_users["don_vi_a"], chu_toa_user.sub)
    r = await client.post(
        BASE + "/upload",
        data={"cuoc_hop_id": ch, "phan_quyen": "HAN_CHE"},
        files={"file": ("a.pdf", io.BytesIO(b"x"), "application/pdf")})
    assert r.status_code == 422


# ── đường ra 1: danh sách tài liệu ────────────────────────────────────

@pytest.mark.asyncio
async def test_danh_sach_khong_lo_tai_lieu_han_che(
    client: AsyncClient, db_session: AsyncSession, chu_toa_user,
    seed_test_users,
):
    """Danh sách nhúng sẵn token xem, nên phải lọc TRƯỚC khi phát token."""
    from meeting_service.tests.conftest import TEST_USERS

    ch = await _tao_hop(client, seed_test_users["don_vi_a"], chu_toa_user.sub)
    await _tai_len(client, ch, "CONG_KHAI", "cong-khai.pdf")
    await _tai_len(client, ch, "LANH_DAO_DON_VI", "han-che.pdf")
    await _moi_du_hop(db_session, ch, TEST_USERS["TEST-G3-004"])

    # Chủ toạ (TDV, là lãnh đạo) thấy cả hai.
    ds = (await client.get(f"{BASE_CUOC_HOP}/{ch}/tai-lieu")).json()["data"]
    assert {x["ten_tai_lieu"] for x in ds} == {"cong-khai.pdf", "han-che.pdf"}

    # Công chức thường được mời họp chỉ thấy file công khai — và quan trọng
    # hơn: không nhận được `url_xem` của file hạn chế.
    _doi_user("TEST-G3-004", seed_test_users["don_vi_b"])
    ds = (await client.get(f"{BASE_CUOC_HOP}/{ch}/tai-lieu")).json()["data"]
    assert {x["ten_tai_lieu"] for x in ds} == {"cong-khai.pdf"}
    assert all("han-che" not in (x.get("url_xem") or "") for x in ds)


# ── đường ra 2 và 3: cấp token xem / tải ──────────────────────────────

@pytest.mark.asyncio
async def test_xem_va_tai_bi_chan_dung_muc(
    client: AsyncClient, db_session: AsyncSession, chu_toa_user,
    seed_test_users,
):
    from meeting_service.tests.conftest import TEST_USERS

    ch = await _tao_hop(client, seed_test_users["don_vi_a"], chu_toa_user.sub)
    tl = await _tai_len(client, ch, "LANH_DAO_DON_VI")
    await _moi_du_hop(db_session, ch, TEST_USERS["TEST-G3-004"])

    _doi_user("TEST-G3-004", seed_test_users["don_vi_b"])
    for duong in ("xem", "tai"):
        r = await client.get(f"{BASE}/{tl}/{duong}")
        assert r.status_code == 403, duong
        assert r.json()["detail"]["error"]["code"] == "DOC_RESTRICTED"

    # Cùng người đó, nhưng là lãnh đạo đơn vị → qua được.
    _doi_user("TEST-G3-004", seed_test_users["don_vi_b"], is_lanh_dao=True)
    await _moi_du_hop(db_session, ch, TEST_USERS["TEST-G3-004"])
    assert (await client.get(f"{BASE}/{tl}/xem")).status_code == 200


@pytest.mark.asyncio
async def test_lanh_dao_don_vi_khong_voi_toi_muc_chi_cuc(
    client: AsyncClient, db_session: AsyncSession, seed_test_users,
):
    from meeting_service.tests.conftest import TEST_USERS

    # Chủ toạ là PCCT để đặt được mức cao nhất.
    cct = _doi_user("TEST-G3-001", seed_test_users["don_vi_a"], vai_tro="PCCT",
                    is_lanh_dao=True)
    ch = await _tao_hop(client, seed_test_users["don_vi_a"], cct.sub)
    tl = await _tai_len(client, ch, "LANH_DAO_CHI_CUC")
    await _moi_du_hop(db_session, ch, TEST_USERS["TEST-G3-002"])

    _doi_user("TEST-G3-002", seed_test_users["don_vi_a"], vai_tro="TDV",
              is_lanh_dao=True)
    r = await client.get(f"{BASE}/{tl}/xem")
    assert r.status_code == 403
    assert r.json()["detail"]["error"]["code"] == "DOC_RESTRICTED"


@pytest.mark.asyncio
async def test_nguoi_tai_len_luon_xem_lai_duoc(
    client: AsyncClient, db_session: AsyncSession, seed_test_users,
):
    """Thư ký nâng mức file rồi không mở lại được để kiểm tra là vô lý."""
    from meeting_service.tests.conftest import TEST_USERS

    cct = _doi_user("TEST-G3-001", seed_test_users["don_vi_a"], vai_tro="PCCT",
                    is_lanh_dao=True)
    ch = await _tao_hop(client, seed_test_users["don_vi_a"], cct.sub)
    await client.patch(
        f"{BASE_CUOC_HOP}/{ch}",
        json={"thu_ky_id": str(TEST_USERS["TEST-G3-002"])})

    # Thư ký (công chức thường) tải lên file công khai…
    thu_ky = _doi_user("TEST-G3-002", seed_test_users["don_vi_a"],
                       platform_roles=["THU_KY_HOP"])
    tl = await _tai_len(client, ch, "CONG_KHAI")

    # …rồi lãnh đạo Chi cục nâng lên mức cao nhất.
    _set_user(cct)
    r = await client.patch(f"{BASE}/{tl}",
                           json={"phan_quyen": "LANH_DAO_CHI_CUC"})
    assert r.status_code == 200, r.text

    # Người tải lên vẫn mở lại được file của chính mình.
    _set_user(thu_ky)
    assert (await client.get(f"{BASE}/{tl}/xem")).status_code == 200

    # Người khác cùng bậc thì không.
    await _moi_du_hop(db_session, ch, TEST_USERS["TEST-G3-004"])
    _doi_user("TEST-G3-004", seed_test_users["don_vi_b"])
    assert (await client.get(f"{BASE}/{tl}/xem")).status_code == 403


# ── đường ra 4: trình chiếu ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_tai_lieu_han_che_khong_trinh_chieu_duoc(
    client: AsyncClient, db_session: AsyncSession, chu_toa_user,
    seed_test_users,
):
    """Trình chiếu là đẩy nội dung ra cả phòng — chặn tại thao tác chủ toạ."""
    from meeting_service.services.presentation_manager import PresentationManager
    from meeting_service.services.broadcast_backend import InMemoryBackend

    ch = await _tao_hop(client, seed_test_users["don_vi_a"], chu_toa_user.sub)
    cong_khai = await _tai_len(client, ch, "CONG_KHAI", "a.pdf")
    # Chủ toạ là TDV nên chỉ đặt tới mức lãnh đạo đơn vị — vẫn là hạn chế.
    han_che = await _tai_len(client, ch, "LANH_DAO_DON_VI", "b.pdf")

    from uuid import UUID
    pm = PresentationManager(InMemoryBackend())
    assert await pm._validate_tai_lieu(db_session, UUID(ch), UUID(cong_khai))
    assert not await pm._validate_tai_lieu(db_session, UUID(ch), UUID(han_che))

    loi = await pm._kiem_tai_lieu(db_session, UUID(ch), UUID(han_che))
    assert loi is not None and loi[0] == "DOCUMENT_RESTRICTED"


# ── đường ra 5: xoá và sửa ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_khong_xem_duoc_thi_khong_xoa_duoc(
    client: AsyncClient, db_session: AsyncSession, seed_test_users,
):
    from meeting_service.tests.conftest import TEST_USERS

    cct = _doi_user("TEST-G3-001", seed_test_users["don_vi_a"], vai_tro="PCCT",
                    is_lanh_dao=True)
    ch = await _tao_hop(client, seed_test_users["don_vi_a"], cct.sub)
    tl = await _tai_len(client, ch, "LANH_DAO_CHI_CUC")
    await client.patch(
        f"{BASE_CUOC_HOP}/{ch}",
        json={"thu_ky_id": str(TEST_USERS["TEST-G3-004"])})

    # Thư ký có quyền xoá tài liệu cuộc họp, nhưng không với tới mức này.
    _doi_user("TEST-G3-004", seed_test_users["don_vi_b"],
              platform_roles=["THU_KY_HOP"])
    r = await client.delete(f"{BASE}/{tl}")
    assert r.status_code == 403
    assert r.json()["detail"]["error"]["code"] == "DOC_RESTRICTED"


@pytest.mark.asyncio
async def test_nang_ha_muc_ghi_nhat_ky_ca_gia_tri_cu(
    client: AsyncClient, db_session: AsyncSession, seed_test_users,
):
    cct = _doi_user("TEST-G3-001", seed_test_users["don_vi_a"], vai_tro="PCCT",
                    is_lanh_dao=True)
    ch = await _tao_hop(client, seed_test_users["don_vi_a"], cct.sub)
    tl = await _tai_len(client, ch, "CONG_KHAI")

    r = await client.patch(f"{BASE}/{tl}",
                           json={"phan_quyen": "LANH_DAO_CHI_CUC"})
    assert r.status_code == 200
    assert r.json()["data"]["phan_quyen"] == "LANH_DAO_CHI_CUC"

    chi_tiet = await db_session.scalar(sa_text("""
        SELECT chi_tiet FROM common.audit_log
         WHERE doi_tuong_id = :i AND hanh_dong = 'UPDATE_DOC'
         ORDER BY created_at DESC LIMIT 1
    """), {"i": tl})
    assert chi_tiet["phan_quyen_cu"] == "CONG_KHAI"
    assert chi_tiet["new_value"]["phan_quyen"] == "LANH_DAO_CHI_CUC"


@pytest.mark.asyncio
async def test_ha_muc_thi_nguoi_thuong_lai_xem_duoc(
    client: AsyncClient, db_session: AsyncSession, seed_test_users,
):
    from meeting_service.tests.conftest import TEST_USERS

    cct = _doi_user("TEST-G3-001", seed_test_users["don_vi_a"], vai_tro="PCCT",
                    is_lanh_dao=True)
    ch = await _tao_hop(client, seed_test_users["don_vi_a"], cct.sub)
    tl = await _tai_len(client, ch, "LANH_DAO_CHI_CUC")
    await _moi_du_hop(db_session, ch, TEST_USERS["TEST-G3-004"])

    _doi_user("TEST-G3-004", seed_test_users["don_vi_b"])
    assert (await client.get(f"{BASE}/{tl}/xem")).status_code == 403

    _set_user(cct)
    await client.patch(f"{BASE}/{tl}", json={"phan_quyen": "CONG_KHAI"})

    _doi_user("TEST-G3-004", seed_test_users["don_vi_b"])
    assert (await client.get(f"{BASE}/{tl}/xem")).status_code == 200


# ── tài liệu của sự kiện lịch công tác ────────────────────────────────
# Luật của Họp Không Giấy không dùng được cho lịch công tác: sự kiện lịch
# thường không có thư ký, chủ toạ là lãnh đạo chủ trì chứ không phải người đi
# nộp tài liệu, và lịch thì cả Chi cục đều xem.

async def _tao_su_kien_lich(db: AsyncSession, nguoi_tao) -> str:
    row = await db.execute(sa_text("""
        INSERT INTO meeting.cuoc_hop
            (tieu_de, ngay_hop, gio_bat_dau, nguon, ma_lich, loai_lich,
             ngay_hien_thi, trang_thai, created_by)
        VALUES ('Test G5 — tài liệu lịch công tác', '2026-09-20', '08:00',
                'LICH_CONG_TAC', 'LHTESTTL', 'HOP', '2026-09-20',
                'DA_THONG_BAO', :nguoi)
        RETURNING id
    """), {"nguoi": str(nguoi_tao)})
    await db.flush()
    return str(row.scalar_one())


@pytest.mark.asyncio
async def test_cong_chuc_thuong_xem_duoc_tai_lieu_lich_cong_tac(
    client: AsyncClient, db_session: AsyncSession, cbcc_user, seed_test_users,
):
    """Lịch công tác là lịch công khai nội bộ — không mời ai cả vẫn xem được.

    Trước đây danh sách tài liệu dùng chung luật với cuộc họp HKG nên công
    chức thường mở tài liệu của chính lịch mình đang xem cũng nhận 403.
    """
    from meeting_service.tests.conftest import TEST_USERS

    ch = await _tao_su_kien_lich(db_session, TEST_USERS["TEST-G3-001"])
    r = await client.get(f"{BASE_CUOC_HOP}/{ch}/tai-lieu")
    assert r.status_code == 200, r.text
    assert r.json()["data"] == []


@pytest.mark.asyncio
async def test_nguoi_tao_lich_tai_duoc_tai_lieu_len(
    client: AsyncClient, db_session: AsyncSession, seed_test_users,
):
    """Người nộp tài liệu là Văn phòng — tức người đã tạo dòng lịch."""
    from meeting_service.tests.conftest import TEST_USERS

    nguoi_tao = _doi_user("TEST-G3-004", seed_test_users["don_vi_b"])
    ch = await _tao_su_kien_lich(db_session, TEST_USERS["TEST-G3-004"])

    tl = await _tai_len(client, ch, "CONG_KHAI", "bao-cao.pdf")
    ds = (await client.get(f"{BASE_CUOC_HOP}/{ch}/tai-lieu")).json()["data"]
    assert [x["id"] for x in ds] == [tl]
    assert nguoi_tao.sub == str(TEST_USERS["TEST-G3-004"])

    # Người khác, không quản trị lịch, không phải người tạo → không nộp được.
    _doi_user("TEST-G3-002", seed_test_users["don_vi_a"])
    r = await client.post(
        BASE + "/upload",
        data={"cuoc_hop_id": ch, "phan_quyen": "CONG_KHAI"},
        files={"file": ("x.pdf", io.BytesIO(b"x"), "application/pdf")})
    assert r.status_code == 403
    assert r.json()["detail"]["error"]["code"] == "NO_PERMISSION"

    # Quản trị lịch thì nộp được.
    _doi_user("TEST-G3-003", seed_test_users["don_vi_b"], vai_tro="PCCT",
              is_lanh_dao=True)
    assert await _tai_len(client, ch, "CONG_KHAI", "cua-quan-tri.pdf")
