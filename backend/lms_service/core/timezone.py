"""
lms_service/core/timezone.py
============================
Helper mui gio Viet Nam (GMT+7) dung chung cho toan bo LMS service.

Quy uoc sau chuan hoa (07/2026):
- Moi cot datetime trong schema lms la TIMESTAMPTZ.
- Code Python luon lam viec voi datetime timezone-aware theo gio VN (now_vn()).
- Input tu FE (input datetime-local, khong co offset) duoc hieu la gio VN.
- Chuoi datetime cu trong JSONB (lich_su_thi...) khong co offset la gio UTC
  (di san tu datetime.utcnow()) — parse bang parse_legacy_utc().
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def now_vn() -> datetime:
    """Thoi diem hien tai theo gio Viet Nam (timezone-aware)."""
    return datetime.now(VN_TZ)


def localize_vn(dt: datetime) -> datetime:
    """Gan tzinfo VN cho datetime naive (coi dt da la gio VN local)."""
    if dt.tzinfo is not None:
        return dt.astimezone(VN_TZ)
    return dt.replace(tzinfo=VN_TZ)


def to_vn(dt: datetime) -> datetime:
    """Chuyen datetime aware bat ky ve gio VN. Naive thi coi nhu gio VN."""
    if dt.tzinfo is None:
        return localize_vn(dt)
    return dt.astimezone(VN_TZ)


def parse_vn_naive(s: str) -> datetime:
    """Parse chuoi datetime tu FE (datetime-local, khong offset) -> aware gio VN."""
    dt = datetime.fromisoformat(s)
    return localize_vn(dt) if dt.tzinfo is None else dt.astimezone(VN_TZ)


def parse_legacy_utc(s: str) -> datetime:
    """Parse chuoi datetime tu JSONB cu: khong offset -> coi la UTC, co offset -> giu.

    Tra ve datetime aware da chuyen sang gio VN (dung cho hien thi/export).
    """
    dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(VN_TZ)


def fmt_vn(dt: datetime | str | None, fmt: str = "%d/%m/%Y %H:%M") -> str:
    """Format datetime/chuoi ISO ve gio VN. Chuoi naive coi la UTC (di san JSONB cu)."""
    if not dt:
        return ""
    if isinstance(dt, str):
        dt = parse_legacy_utc(dt)
    elif dt.tzinfo is None:
        # Cot DB cu chua migrate (khong xay ra sau khi chay migration) — coi la UTC
        dt = dt.replace(tzinfo=timezone.utc).astimezone(VN_TZ)
    else:
        dt = dt.astimezone(VN_TZ)
    return dt.strftime(fmt)
