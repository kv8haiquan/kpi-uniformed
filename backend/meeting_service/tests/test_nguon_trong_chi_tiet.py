"""Chi tiết cuộc họp phải nói rõ nó thuộc nguồn nào.

Bảng `meeting.cuoc_hop` chứa CẢ cuộc họp HKG lẫn sự kiện Lịch công tác, phân
biệt bằng `nguon`. Trước đây `CuocHopResponse` không trả cột này, nên màn hình
Họp Không Giấy không biết mình đang mở nhầm một sự kiện Lịch công tác — nó vẽ
đủ nút "Xác nhận tham dự" / "Huỷ", bấm vào là 403.

Sự cố thật ngày 22/08/2026: tin nhắc họp Zalo dùng chung mẫu ZNS 623236
("Nhắc họp không giấy") cho cả hai nguồn, mà mẫu đó chỉ nhận `ma_hop` nên nút
trong tin luôn trỏ `/hop-khong-giay/chi-tiet/`. Một Phó Chi cục trưởng bấm tin
nhắc của LH0503 (Lịch công tác), rơi vào màn hình HKG, bấm "Xác nhận tham dự"
5 lần và nhận 403 — sự kiện Lịch công tác không có `thanh_phan`, người liên
quan nằm ở `lanh_dao_lien_quan`.

    DB_NAME=kpi_haiquan_test ALLOW_PROD_TEST=true \
    pytest meeting_service/tests/test_nguon_trong_chi_tiet.py -v
"""

from __future__ import annotations

import uuid
from datetime import date, time, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.tests.conftest import TEST_USERS

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/hop-khong-giay/cuoc-hop"
NGAY = date.today() + timedelta(days=800)


async def _tao(db: AsyncSession, seed, nguon: str) -> uuid.UUID:
    ch_id = uuid.uuid4()
    nguoi = TEST_USERS["TEST-G3-001"]
    await db.execute(sa_text("""
        INSERT INTO meeting.cuoc_hop
            (id, tieu_de, ngay_hop, gio_bat_dau, trang_thai, nguon, ma_lich,
             loai_lich, created_by, don_vi_to_chuc_id, chu_toa_id)
        VALUES (:id, :td, :ngay, :gio, 'DA_THONG_BAO', :nguon, :ma,
                :loai, :nt, :dv, :ct)
    """), {
        "id": str(ch_id), "td": f"TEST-NGUON {nguon}", "ngay": NGAY,
        "gio": time.fromisoformat("08:30"), "nguon": nguon,
        "ma": f"LH7{uuid.uuid4().hex[:5]}",
        # Sự kiện Lịch công tác thường KHÔNG có đơn vị tổ chức lẫn chủ tọa —
        # đúng như LH0503 ngoài thực tế.
        "loai": "HOP" if nguon == "LICH_CONG_TAC" else None,
        "ct": str(nguoi) if nguon == "HKG" else None,
        "nt": str(nguoi),
        "dv": str(seed["don_vi_a"]) if nguon == "HKG" else None,
    })
    await db.flush()
    return ch_id


async def test_chi_tiet_tra_ve_nguon_va_ma_lich(
    client: AsyncClient, db_session: AsyncSession, seed_test_users, admin_user,
):
    """Thiếu `nguon` là màn hình HKG không có cách nào biết để tránh."""
    ch = await _tao(db_session, seed_test_users, "LICH_CONG_TAC")
    r = await client.get(f"{BASE}/{ch}")
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["nguon"] == "LICH_CONG_TAC"
    assert d["ma_lich"], "mã lịch phải có để màn hình hiện được cho người dùng"


async def test_cuoc_hop_hkg_van_bao_dung_nguon(
    client: AsyncClient, db_session: AsyncSession, seed_test_users, admin_user,
):
    ch = await _tao(db_session, seed_test_users, "HKG")
    d = (await client.get(f"{BASE}/{ch}")).json()["data"]
    assert d["nguon"] == "HKG"


async def test_xac_nhan_tham_du_tren_su_kien_lich_cong_tac_bi_tu_choi(
    client: AsyncClient, db_session: AsyncSession, seed_test_users, cbcc_user,
):
    """Khoá lại đúng hành vi đã gây sự cố.

    403 ở đây là ĐÚNG — sự kiện Lịch công tác không có thành phần để xác
    nhận. Cái sai nằm ở chỗ giao diện HKG vẽ ra cái nút đó; nay giao diện
    chuyển hướng sang màn hình Lịch công tác trước khi người dùng bấm được.
    """
    ch = await _tao(db_session, seed_test_users, "LICH_CONG_TAC")
    r = await client.post(f"{BASE}/{ch}/xac-nhan", json={"xac_nhan": "THAM_DU"})
    assert r.status_code == 403
    assert r.json()["detail"]["error"]["code"] == "NOT_INVITED"
