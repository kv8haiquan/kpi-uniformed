"""
scheduler_helpers.py
=====================
Pure-logic functions cho 4 scheduled jobs HKG. Tách khỏi `scheduler.py` để test
trực tiếp với freezegun (không phải đợi APScheduler tick).

Tracking decision (xem SPEC_CHANGELOG 2026-05-01):
  Tracking nhắc họp 24h/1h/30p được lưu DUY NHẤT trong `common.thong_bao`
  (dùng cột `doi_tuong_id`+`doi_tuong_type`). KHÔNG thêm cột mới vào
  `meeting.cuoc_hop` — tránh state đồng bộ 2 nơi.

Optimizations:
  1. Cache RAM 1 phút: scheduler chạy mỗi phút, mỗi tick query `thong_bao` 1 lần
     thay vì 3 lần (1 cho mỗi window).
  2. Batch IN(...): query tất cả cuộc họp trong scope cùng lúc.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable
from uuid import UUID

from sqlalchemy import and_, or_, select, text as sa_text, update
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.models.ket_luan import KetLuan
from meeting_service.services.audit_log_service import ghi_audit
from meeting_service.services.notification_service import (
    gui_thong_bao,
    gui_thong_bao_bulk,
)


logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════
# 1. NHẮC HỌP 3 TẦNG — 24h / 1h / 30p
# ════════════════════════════════════════════════════════════════════

# Window chấp nhận để trigger: gio_bat_dau − offset ± WINDOW_TOLERANCE
WINDOW_TOLERANCE = timedelta(minutes=5)

# 🔴 GIỜ HỌP LÀ GIỜ VIỆT NAM, KHÔNG PHẢI UTC.
#
# `cuoc_hop.ngay_hop` là DATE và `gio_bat_dau` là TIME, đều KHÔNG mang múi giờ.
# Người nhập gõ "14:30" nghĩa là 14:30 giờ ta. Cho tới 21/08/2026 chỗ này ghép
# hai cột đó với `tzinfo=timezone.utc` — tức là hiểu thành 21:30 giờ ta, lệch
# đúng 7 tiếng. Hậu quả đo được trên dữ liệu thật: tin "nhắc trước 30 phút"
# của cuộc họp 09:00 ngày 17/08 được gửi lúc 15:25 cùng ngày — SAU khi họp đã
# tan 6,4 giờ. Nhắc kiểu đó tệ hơn không nhắc.
#
# Không sửa được bằng cách đổi `now` sang giờ VN: `now` vốn đã đúng (có múi
# giờ), sai là ở phía giờ họp. Phải gắn đúng múi cho giờ họp.
GIO_VN = timezone(timedelta(hours=7))


def gio_bat_dau_utc(ngay_hop, gio_bat_dau) -> datetime:
    """Ghép ngày + giờ họp thành mốc thời gian THẬT (đổi sang UTC để so sánh)."""
    return datetime.combine(ngay_hop, gio_bat_dau, tzinfo=GIO_VN).astimezone(
        timezone.utc)


# Ba mốc nhắc. Lãnh đạo chốt giữ đủ ba (21/08/2026), có thể rút còn một sau —
# khi đó bỏ bớt dòng ở đây là xong, không phải sửa chỗ nào khác. Cả ba dùng
# CHUNG một template ZNS đã được Zalo duyệt, khác nhau ở tham số `moc`.
WINDOWS = [
    ("NHAC_HOP_24H", timedelta(hours=24)),
    ("NHAC_HOP_1H", timedelta(hours=1)),
    ("NHAC_HOP_30P", timedelta(minutes=30)),
]

# Sự kiện Lịch công tác giữ người nhận ở bảng KHÁC với cuộc họp HKG:
#   HKG           → meeting.thanh_phan       (người được mời, có điểm danh)
#   LICH_CONG_TAC → meeting.lanh_dao_lien_quan (lãnh đạo có mặt trong chương
#                                              trình công tác)
# Đường dẫn trong thông báo cũng khác, vì hai nguồn có hai màn hình riêng.
NGUON_NHAC = {
    "HKG": {
        "bang_nguoi_nhan": "meeting.thanh_phan",
        "duong_dan": "/hop-khong-giay/chi-tiet/{id}",
    },
    "LICH_CONG_TAC": {
        "bang_nguoi_nhan": "meeting.lanh_dao_lien_quan",
        "duong_dan": "/lich-cong-tac/{id}",
    },
}


@dataclass
class _NhacHopCache:
    """Cache TTL cho query thong_bao đã gửi. Tránh stale, TTL = 60s."""

    timestamp: datetime
    sent_pairs: set[tuple[UUID, str]]


_cache: _NhacHopCache | None = None


def reset_cache() -> None:
    """Cho test — clear cache giữa các invocation."""
    global _cache
    _cache = None


async def _query_sent_pairs(
    db: AsyncSession, cuoc_hop_ids: Iterable[UUID]
) -> set[tuple[UUID, str]]:
    """Batch query — trả về tập (cuoc_hop_id, sub_loai) đã gửi notif."""
    ids = list(cuoc_hop_ids)
    if not ids:
        return set()

    result = await db.execute(sa_text("""
        SELECT doi_tuong_id, doi_tuong_type
          FROM common.thong_bao
         WHERE loai = 'MEETING'
           AND doi_tuong_id = ANY(:ids)
           AND doi_tuong_type IN ('NHAC_HOP_24H','NHAC_HOP_1H','NHAC_HOP_30P')
    """), {"ids": [str(i) for i in ids]})
    return {(UUID(str(row[0])), row[1]) for row in result.fetchall()}


async def nhac_hop_3_tang_logic(
    db: AsyncSession,
    *,
    now: datetime | None = None,
) -> int:
    """
    Logic chính của nhac_hop_3_tang.

    Args:
        db: AsyncSession (caller chịu trách nhiệm commit)
        now: thời điểm hiện tại — None = datetime.now(UTC). Test pass mock value.

    Returns:
        Số notification đã gửi trong tick này.
    """
    global _cache
    now = now or datetime.now(timezone.utc)

    # 1. Lấy cuộc họp đã thông báo, chưa diễn ra (gio_bat_dau từ now → now+25h)
    upper = now + timedelta(hours=25)
    result = await db.execute(
        select(CuocHop).where(
            CuocHop.is_deleted.is_(False),
            CuocHop.trang_thai == "DA_THONG_BAO",
            # Nhắc cả cuộc họp HKG lẫn sự kiện Lịch công tác (21/08/2026).
            # Trước đây chỉ HKG, kèm ghi chú "Lịch công tác không có thành phần
            # dự để gửi nhắc" — đúng vào lúc viết, nhưng G4.3 đã thêm danh sách
            # lãnh đạo tham dự: 448/490 sự kiện (91%) nay có người để nhắc.
            CuocHop.nguon.in_(tuple(NGUON_NHAC)),
        )
    )
    candidates: list[CuocHop] = []
    for ch in result.scalars().all():
        if ch.gio_bat_dau is None:
            continue  # sự kiện cả ngày, không có mốc để đếm ngược
        gio_bd = gio_bat_dau_utc(ch.ngay_hop, ch.gio_bat_dau)
        if now <= gio_bd <= upper + timedelta(hours=1):  # buffer
            candidates.append(ch)

    if not candidates:
        return 0

    # 2. Cache RAM TTL=60s
    if _cache is None or (now - _cache.timestamp) > timedelta(seconds=60):
        sent_pairs = await _query_sent_pairs(db, [c.id for c in candidates])
        _cache = _NhacHopCache(timestamp=now, sent_pairs=sent_pairs)
    else:
        sent_pairs = _cache.sent_pairs

    # 3. Mỗi cuộc họp × 3 windows: check trong window + chưa gửi
    sent_count = 0
    for ch in candidates:
        gio_bd = gio_bat_dau_utc(ch.ngay_hop, ch.gio_bat_dau)
        cau_hinh = NGUON_NHAC[ch.nguon]
        # Người nhận lấy ở bảng nào là tuỳ nguồn — xem NGUON_NHAC. Tên bảng
        # lấy từ hằng số trong mã, không phải đầu vào người dùng.
        tp_res = await db.execute(sa_text(f"""
            SELECT DISTINCT cong_chuc_id FROM {cau_hinh['bang_nguoi_nhan']}
             WHERE cuoc_hop_id = :ch_id
        """), {"ch_id": str(ch.id)})
        tp_ids = [UUID(str(r[0])) for r in tp_res.fetchall()]
        if not tp_ids:
            continue

        for sub_loai, offset in WINDOWS:
            target_time = gio_bd - offset
            in_window = (
                target_time - WINDOW_TOLERANCE
                <= now
                <= target_time + WINDOW_TOLERANCE
            )
            if not in_window:
                continue
            if (ch.id, sub_loai) in sent_pairs:
                continue

            label = {
                "NHAC_HOP_24H": "24 giờ", "NHAC_HOP_1H": "1 giờ",
                "NHAC_HOP_30P": "30 phút",
            }[sub_loai]
            viec = "Cuộc họp" if ch.nguon == "HKG" else "Lịch công tác"
            n = await gui_thong_bao_bulk(
                db,
                nguoi_nhan_ids=tp_ids,
                tieu_de=f"Nhắc lịch ({label}): {ch.tieu_de}",
                noi_dung=(f"{viec} bắt đầu lúc "
                          f"{ch.gio_bat_dau.strftime('%H:%M')} ngày "
                          f"{ch.ngay_hop.strftime('%d/%m/%Y')}."),
                sub_loai=sub_loai,
                link_url=cau_hinh["duong_dan"].format(id=ch.id),
                doi_tuong_id=ch.id,
            )
            sent_count += n
            # Cập nhật cache để cùng tick không re-trigger
            sent_pairs.add((ch.id, sub_loai))

    await db.flush()
    return sent_count


# ════════════════════════════════════════════════════════════════════
# 2. NHẮC HẠN KẾT LUẬN — cron 8AM hằng ngày
# ════════════════════════════════════════════════════════════════════

async def nhac_han_ket_luan_logic(
    db: AsyncSession, *, today: datetime | None = None
) -> int:
    """
    Tìm ket_luan han = today + 3 days, trang_thai chưa hoàn thành → gửi nhắc.

    Idempotent: dùng query thong_bao tránh duplicate.

    `today` arg: nếu None → dùng `date.today()` (local time). Logic nghiệp vụ
    chạy theo local date của server (Asia/Ho_Chi_Minh dự kiến). Test có thể
    pass datetime cụ thể.
    """
    if today is None:
        today_dt = date.today()
    else:
        today_dt = today.date() if hasattr(today, "date") else today
    target_date = today_dt + timedelta(days=3)

    result = await db.execute(
        select(KetLuan).where(
            KetLuan.han_hoan_thanh == target_date,
            KetLuan.trang_thai.notin_(["HOAN_THANH", "HUY"]),
            KetLuan.is_deleted.is_(False),
        )
    )
    candidates = list(result.scalars().all())
    if not candidates:
        return 0

    # Check đã gửi NHAC_HAN_3_NGAY chưa
    ids = [str(k.id) for k in candidates]
    sent_res = await db.execute(sa_text("""
        SELECT doi_tuong_id FROM common.thong_bao
         WHERE loai='MEETING' AND doi_tuong_type='NHAC_HAN_3_NGAY'
           AND doi_tuong_id = ANY(:ids)
    """), {"ids": ids})
    already_sent = {UUID(str(row[0])) for row in sent_res.fetchall()}

    sent_count = 0
    for kl in candidates:
        if kl.id in already_sent:
            continue
        await gui_thong_bao(
            db,
            nguoi_nhan_id=kl.nguoi_phu_trach_id,
            tieu_de=f"Sắp đến hạn nhiệm vụ (3 ngày): {kl.noi_dung[:80]}",
            noi_dung=f"Hạn: {kl.han_hoan_thanh}, Tiến độ: {kl.tien_do_phan_tram}%",
            sub_loai="NHAC_HAN_3_NGAY",
            link_url=f"/hop-khong-giay/chi-tiet/{kl.cuoc_hop_id}/ket-luan",
            doi_tuong_id=kl.id,
            muc_do="QUAN_TRONG",
        )
        sent_count += 1

    await db.flush()
    return sent_count


# ════════════════════════════════════════════════════════════════════
# 3. MARK TRỄ HẠN KẾT LUẬN — cron 0AM hằng ngày
# ════════════════════════════════════════════════════════════════════

async def mark_tre_han_logic(
    db: AsyncSession, *, today: datetime | None = None
) -> int:
    """
    UPDATE ket_luan SET trang_thai='TRE_HAN'
      WHERE han < today AND trang_thai NOT IN ('HOAN_THANH','TRE_HAN','HUY')
        AND tien_do_phan_tram < 100.

    Trả về số rows affected. `today` None → dùng `date.today()` (local).
    """
    if today is None:
        today_dt = date.today()
    else:
        today_dt = today.date() if hasattr(today, "date") else today
    result = await db.execute(
        update(KetLuan)
        .where(
            KetLuan.han_hoan_thanh < today_dt,
            KetLuan.trang_thai.notin_(["HOAN_THANH", "TRE_HAN", "HUY"]),
            KetLuan.tien_do_phan_tram < 100,
            KetLuan.is_deleted.is_(False),
        )
        .values(trang_thai="TRE_HAN", updated_at=datetime.now(timezone.utc))
    )
    await db.flush()
    return result.rowcount or 0
