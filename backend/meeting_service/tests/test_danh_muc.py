"""Kiểm thử Quản trị danh mục — G4.11.

Đáp yêu cầu chuyển đổi mục II.15 ("quản lý các danh mục dùng chung … loại
lịch, trạng thái và các danh mục cấu hình khác") và bảng nghiệm thu XI.9.

Bốn chỗ dễ hỏng, mỗi chỗ một nhóm test:

  1. Mục `he_thong` phải chặn được xoá/tắt/đổi mã — mã của chúng bị 62 điểm
     trong mã nguồn rẽ nhánh theo.
  2. Mã KHÔNG đổi được sau khi tạo, kể cả mục thường — dữ liệu đã ghi tham
     chiếu bằng mã, đổi là làm mồ côi hàng loạt bản ghi mà không báo ai.
  3. Đang có bản ghi dùng thì chỉ được TẮT, không được xoá.
  4. Người thường đọc được, chỉ quản trị mới ghi được.

    ./scripts/dev.sh test meeting_service/tests/test_danh_muc.py -v
"""

from __future__ import annotations

import pytest
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/hop-khong-giay/danh-muc"
BASE_LICH = "/api/v1/hop-khong-giay/lich-cong-tac"

# Tiền tố để dọn: mọi mục test tạo ra đều mang mã bắt đầu bằng chuỗi này.
TIEN_TO = "TEST_DM_"


async def _xoa_sach(db: AsyncSession) -> None:
    """Dọn cả nhật ký, không riêng dữ liệu nghiệp vụ.

    `seed_test_users` trong conftest là fixture PHẠM VI HÀM: nó xoá các
    TEST-G3-* sau MỖI test. Mà tạo lịch thì ghi `common.audit_log` với khoá
    ngoại `nguoi_thuc_hien_id` → `cong_chuc`. Bỏ sót bảng nhật ký là teardown
    của test kế tiếp vỡ vì vi phạm khoá ngoại — cả tệp đỏ dù test nào cũng
    đúng. Xoá theo người thực hiện chứ không theo đối tượng, vì nhật ký của
    thao tác danh mục không gắn với cuộc họp nào.
    """
    await db.execute(sa_text(
        "DELETE FROM common.audit_log WHERE nguoi_thuc_hien_id IN "
        "(SELECT id FROM public.cong_chuc WHERE ma_cc LIKE 'TEST-G3-%')"))
    await db.execute(sa_text(
        "DELETE FROM meeting.lanh_dao_lien_quan WHERE cuoc_hop_id IN "
        "(SELECT id FROM meeting.cuoc_hop WHERE tieu_de LIKE 'TEST G4.11%')"))
    await db.execute(sa_text(
        "DELETE FROM meeting.cuoc_hop WHERE tieu_de LIKE 'TEST G4.11%'"))
    await db.execute(sa_text(
        f"DELETE FROM meeting.danh_muc WHERE ma LIKE '{TIEN_TO}%'"))
    await db.commit()


@pytest.fixture(autouse=True)
async def don_dep(db_session: AsyncSession):
    """autouse: test nào cũng phải dọn, kể cả test chỉ đọc — vì test đọc chạy
    xen giữa hai test ghi vẫn gánh teardown của `seed_test_users`."""
    await _xoa_sach(db_session)
    yield
    await _xoa_sach(db_session)


# ════════════════════════════════════════════════════════════════════
# 1. Hạt giống — bốn nhóm đúng như hệ cũ
# ════════════════════════════════════════════════════════════════════

async def test_bon_nhom_duoc_gieo_du(client, admin_user):
    resp = await client.get(f"{BASE}/nhom")
    assert resp.status_code == 200
    d = resp.json()["data"]
    assert {n["ma"] for n in d["nhom"]} == {
        "LOAI_LICH", "TRANG_THAI_LICH", "LOAI_TAI_LIEU", "PHONG_HOP"}
    assert d["duoc_sua"] is True


async def test_loai_lich_du_bay_muc_ke_ca_tiep_doan(client, admin_user):
    """Hệ cũ (sheet SETUP › MEETING_TYPE) có 7 loại; ta từng chỉ cài 6."""
    resp = await client.get(f"{BASE}/", params={"nhom": "LOAI_LICH"})
    ma = [m["ma"] for m in resp.json()["data"]]
    assert ma == ["HOP", "TRUC_BAN", "HOI_NGHI", "LAM_VIEC", "CONG_TAC",
                  "TIEP_DOAN", "LICH_KHAC"]


async def test_loai_tai_lieu_dung_nguyen_van_file_type(client, admin_user):
    resp = await client.get(f"{BASE}/", params={"nhom": "LOAI_TAI_LIEU"})
    nhan = [m["nhan"] for m in resp.json()["data"]]
    assert nhan == ["Giấy mời", "Tài liệu họp", "Báo cáo", "Chương trình",
                    "Biên bản", "Kết luận", "Tài liệu khác"]


async def test_trang_thai_toan_bo_la_muc_he_thong(client, admin_user):
    """62 điểm trong mã nguồn rẽ nhánh theo mã trạng thái."""
    resp = await client.get(f"{BASE}/", params={"nhom": "TRANG_THAI_LICH"})
    muc = resp.json()["data"]
    assert len(muc) == 5
    assert all(m["he_thong"] for m in muc)


async def test_nhom_khong_hop_le_bi_tu_choi(client, admin_user):
    resp = await client.get(f"{BASE}/", params={"nhom": "ROLE_LIST"})
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "DM_NHOM_KHONG_HOP_LE"


# ════════════════════════════════════════════════════════════════════
# 2. Mục hệ thống — sửa được nhãn, không đụng được phần còn lại
# ════════════════════════════════════════════════════════════════════

async def _lay_muc(client, nhom: str, ma: str) -> dict:
    resp = await client.get(f"{BASE}/", params={"nhom": nhom, "gom-ca-tat": True})
    return next(m for m in resp.json()["data"] if m["ma"] == ma)


async def test_muc_he_thong_doi_duoc_nhan(client, admin_user, db_session):
    """Đổi "Đã đăng" thành cách gọi khác là vô hại — chỉ là chữ hiển thị."""
    muc = await _lay_muc(client, "TRANG_THAI_LICH", "DA_THONG_BAO")
    cu = muc["nhan"]
    try:
        resp = await client.patch(f"{BASE}/{muc['id']}",
                                  json={"nhan": "Đã công bố"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["nhan"] == "Đã công bố"
    finally:
        await client.patch(f"{BASE}/{muc['id']}", json={"nhan": cu})


async def test_muc_he_thong_khong_tat_duoc(client, admin_user):
    muc = await _lay_muc(client, "TRANG_THAI_LICH", "HUY")
    resp = await client.patch(f"{BASE}/{muc['id']}", json={"is_active": False})
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "DM_MUC_HE_THONG"


async def test_muc_he_thong_khong_xoa_duoc(client, admin_user):
    muc = await _lay_muc(client, "LOAI_LICH", "HOP")
    resp = await client.delete(f"{BASE}/{muc['id']}")
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "DM_MUC_HE_THONG"


# ════════════════════════════════════════════════════════════════════
# 3. Mã bất biến
# ════════════════════════════════════════════════════════════════════

async def test_khong_doi_duoc_ma_ke_ca_muc_thuong(client, admin_user, don_dep):
    tao = await client.post(f"{BASE}/", json={
        "nhom": "LOAI_TAI_LIEU", "ma": f"{TIEN_TO}A", "nhan": "Thử A"})
    assert tao.status_code == 201, tao.text
    dm_id = tao.json()["data"]["id"]

    # Schema không khai `ma` nên pydantic bỏ qua — mã phải giữ nguyên chứ
    # không được âm thầm đổi.
    resp = await client.patch(f"{BASE}/{dm_id}", json={"ma": f"{TIEN_TO}B"})
    assert resp.status_code == 200
    assert resp.json()["data"]["ma"] == f"{TIEN_TO}A"


async def test_ma_co_dau_hoac_khoang_trang_bi_tu_choi(client, admin_user, don_dep):
    resp = await client.post(f"{BASE}/", json={
        "nhom": "LOAI_TAI_LIEU", "ma": "Tờ trình", "nhan": "Tờ trình"})
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "DM_MA_KHONG_HOP_LE"


async def test_ma_thuong_duoc_tu_nang_len_hoa(client, admin_user, don_dep):
    resp = await client.post(f"{BASE}/", json={
        "nhom": "LOAI_TAI_LIEU", "ma": f"{TIEN_TO.lower()}to trinh",
        "nhan": "Tờ trình"})
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["ma"] == f"{TIEN_TO}TO_TRINH"


async def test_ma_trung_bi_tu_choi(client, admin_user, don_dep):
    goi = {"nhom": "LOAI_TAI_LIEU", "ma": f"{TIEN_TO}C", "nhan": "Thử C"}
    assert (await client.post(f"{BASE}/", json=goi)).status_code == 201
    lai = await client.post(f"{BASE}/", json=goi)
    assert lai.status_code == 409
    assert lai.json()["detail"]["error"]["code"] == "DM_MA_TRUNG"


async def test_them_lai_ma_da_tat_thi_bat_lai_muc_cu(client, admin_user, don_dep):
    """Đơn vị tắt một loại rồi cần lại — bật lại đúng mục cũ, KHÔNG báo lỗi
    cụt và cũng không đẻ mục thứ hai. Dữ liệu cũ mang mã này hiện đúng ngay."""
    tao = await client.post(f"{BASE}/", json={
        "nhom": "LOAI_TAI_LIEU", "ma": f"{TIEN_TO}D", "nhan": "Thử D"})
    dm_id = tao.json()["data"]["id"]
    await client.patch(f"{BASE}/{dm_id}", json={"is_active": False})

    lai = await client.post(f"{BASE}/", json={
        "nhom": "LOAI_TAI_LIEU", "ma": f"{TIEN_TO}D", "nhan": "Thử D sửa"})
    assert lai.status_code == 201, lai.text
    assert lai.json()["data"]["id"] == dm_id      # đúng mục cũ
    assert lai.json()["data"]["is_active"] is True
    assert lai.json()["data"]["nhan"] == "Thử D sửa"


# ════════════════════════════════════════════════════════════════════
# 4. Đang dùng thì chỉ được tắt
# ════════════════════════════════════════════════════════════════════

async def test_loai_lich_dang_co_su_kien_thi_khong_xoa_duoc(
    client, admin_user, don_dep
):
    tao = await client.post(f"{BASE}/", json={
        "nhom": "LOAI_LICH", "ma": f"{TIEN_TO}HOI_THAO", "nhan": "Hội thảo"})
    dm_id = tao.json()["data"]["id"]

    lich = await client.post(f"{BASE_LICH}/", json={
        "tieu_de": "TEST G4.11 — hội thảo thử",
        "loai_lich": f"{TIEN_TO}HOI_THAO",
        "ngay_hop": "2026-09-20", "gio_bat_dau": "08:00:00"})
    assert lich.status_code == 201, lich.text

    xoa = await client.delete(f"{BASE}/{dm_id}")
    assert xoa.status_code == 409
    assert xoa.json()["detail"]["error"]["code"] == "DM_DANG_SU_DUNG"

    # Tắt thì được — dữ liệu cũ giữ nguyên, chỉ không chọn mới được nữa.
    tat = await client.patch(f"{BASE}/{dm_id}", json={"is_active": False})
    assert tat.status_code == 200
    assert tat.json()["data"]["is_active"] is False


async def test_muc_chua_ai_dung_thi_xoa_han(client, admin_user, don_dep):
    tao = await client.post(f"{BASE}/", json={
        "nhom": "PHONG_HOP", "ma": f"{TIEN_TO}P999", "nhan": "Phòng 999"})
    dm_id = tao.json()["data"]["id"]
    xoa = await client.delete(f"{BASE}/{dm_id}")
    assert xoa.status_code == 200
    assert xoa.json()["data"]["da_xoa"] is True

    con = await client.get(f"{BASE}/", params={"nhom": "PHONG_HOP",
                                               "gom-ca-tat": True})
    assert all(m["id"] != dm_id for m in con.json()["data"])


async def test_dem_su_dung_dung_so(client, admin_user, don_dep):
    tao = await client.post(f"{BASE}/", json={
        "nhom": "LOAI_LICH", "ma": f"{TIEN_TO}TAP_HUAN", "nhan": "Tập huấn"})
    dm_id = tao.json()["data"]["id"]
    for i in range(2):
        await client.post(f"{BASE_LICH}/", json={
            "tieu_de": f"TEST G4.11 — tập huấn {i}",
            "loai_lich": f"{TIEN_TO}TAP_HUAN",
            "ngay_hop": "2026-09-21", "gio_bat_dau": "08:00:00"})

    resp = await client.get(f"{BASE}/", params={
        "nhom": "LOAI_LICH", "dem-su-dung": True, "gom-ca-tat": True})
    muc = next(m for m in resp.json()["data"] if m["id"] == dm_id)
    assert muc["dang_su_dung"] == 2


# ════════════════════════════════════════════════════════════════════
# 5. Quyền
# ════════════════════════════════════════════════════════════════════

async def test_nguoi_thuong_doc_duoc(client, cbcc_user):
    """Mọi màn hình lịch cần danh mục để đổ ô chọn — chặn đọc là hỏng cả
    trang, không phải bảo mật thêm được gì."""
    resp = await client.get(f"{BASE}/", params={"nhom": "LOAI_LICH"})
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 7


async def test_nguoi_thuong_khong_ghi_duoc(client, cbcc_user, don_dep):
    resp = await client.post(f"{BASE}/", json={
        "nhom": "LOAI_TAI_LIEU", "ma": f"{TIEN_TO}X", "nhan": "Thử X"})
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"]["code"] == "DM_KHONG_DU_QUYEN"


async def test_nguoi_thuong_khong_thay_muc_da_tat(
    client, admin_user, don_dep, seed_test_users
):
    """`gom-ca-tat` chỉ có tác dụng với quản trị. Người thường mà thấy mục đã
    tắt thì việc tắt trở nên vô nghĩa."""
    from meeting_service.tests.conftest import _make_user, _set_user

    tao = await client.post(f"{BASE}/", json={
        "nhom": "PHONG_HOP", "ma": f"{TIEN_TO}P888", "nhan": "Phòng 888"})
    dm_id = tao.json()["data"]["id"]
    await client.patch(f"{BASE}/{dm_id}", json={"is_active": False})

    try:
        _set_user(_make_user("TEST-G3-004", seed_test_users["don_vi_b"]))
        resp = await client.get(f"{BASE}/", params={"nhom": "PHONG_HOP",
                                                    "gom-ca-tat": True})
        assert all(m["id"] != dm_id for m in resp.json()["data"])
    finally:
        # Trả lại quyền quản trị để fixture `don_dep` dọn được.
        _set_user(admin_user)


# ════════════════════════════════════════════════════════════════════
# 6. Nối vào nghiệp vụ lịch
# ════════════════════════════════════════════════════════════════════

async def test_danh_muc_loai_lich_cu_doc_tu_bang(client, admin_user, don_dep):
    """Đường dẫn `/lich-cong-tac/danh-muc` giữ nguyên nhưng nguồn đã đổi —
    thêm loại mới là ô chọn trên giao diện có ngay, không phải sửa mã."""
    truoc = await client.get(f"{BASE_LICH}/danh-muc")
    assert len(truoc.json()["data"]) == 7

    await client.post(f"{BASE}/", json={
        "nhom": "LOAI_LICH", "ma": f"{TIEN_TO}TOA_DAM", "nhan": "Toạ đàm"})

    sau = await client.get(f"{BASE_LICH}/danh-muc")
    assert {m["ma"] for m in sau.json()["data"]} & {f"{TIEN_TO}TOA_DAM"}


async def test_doi_nhan_loai_lich_thi_su_kien_hien_ten_moi(
    client, admin_user, don_dep
):
    muc = await _lay_muc(client, "LOAI_LICH", "TIEP_DOAN")
    lich = await client.post(f"{BASE_LICH}/", json={
        "tieu_de": "TEST G4.11 — tiếp đoàn thử",
        "loai_lich": "TIEP_DOAN",
        "ngay_hop": "2026-09-22", "gio_bat_dau": "08:00:00"})
    assert lich.json()["data"]["loai_lich_nhan"] == "Tiếp đoàn"

    try:
        await client.patch(f"{BASE}/{muc['id']}", json={"nhan": "Đón tiếp đoàn"})
        lai = await client.get(f"{BASE_LICH}/{lich.json()['data']['id']}")
        assert lai.json()["data"]["loai_lich_nhan"] == "Đón tiếp đoàn"
    finally:
        await client.patch(f"{BASE}/{muc['id']}", json={"nhan": "Tiếp đoàn"})


async def test_danh_muc_phong_hop_tra_nhan(client, admin_user):
    """Địa điểm là chuỗi tự do nên danh mục trả nhãn để gợi ý, không trả mã."""
    resp = await client.get(f"{BASE_LICH}/danh-muc-phong-hop")
    assert resp.status_code == 200
    assert "Phòng họp 701" in resp.json()["data"]
