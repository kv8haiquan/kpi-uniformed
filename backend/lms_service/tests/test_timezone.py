"""
Tests cho helper timezone gio VN (lms_service/core/timezone.py).
Unit test thuan — khong cham DB.
"""
from datetime import datetime, timezone, timedelta

from lms_service.core.timezone import (
    VN_TZ,
    fmt_vn,
    localize_vn,
    now_vn,
    parse_legacy_utc,
    parse_vn_naive,
    to_vn,
)


class TestNowVn:
    def test_now_vn_aware_gio_vn(self):
        dt = now_vn()
        assert dt.tzinfo is not None
        assert dt.utcoffset() == timedelta(hours=7)


class TestLocalizeParse:
    def test_localize_vn_gan_offset_khong_doi_wall_time(self):
        naive = datetime(2026, 7, 30, 14, 0)
        aware = localize_vn(naive)
        assert aware.hour == 14
        assert aware.utcoffset() == timedelta(hours=7)

    def test_parse_vn_naive_tu_datetime_local(self):
        dt = parse_vn_naive("2026-07-30T21:00")
        assert dt.hour == 21
        assert dt.utcoffset() == timedelta(hours=7)

    def test_parse_vn_naive_giu_offset_neu_co(self):
        dt = parse_vn_naive("2026-07-30T14:00:00+00:00")
        assert dt.hour == 21  # 14h UTC = 21h VN
        assert dt.utcoffset() == timedelta(hours=7)

    def test_to_vn_chuyen_tu_utc(self):
        utc = datetime(2026, 7, 30, 14, 0, tzinfo=timezone.utc)
        vn = to_vn(utc)
        assert vn.hour == 21


class TestLegacyJsonb:
    """Chuoi cu trong lich_su_thi (utcnow naive isoformat) phai duoc hieu la UTC."""

    def test_chuoi_naive_coi_la_utc(self):
        dt = parse_legacy_utc("2026-07-30T07:30:00")
        assert dt.hour == 14  # 07:30 UTC = 14:30 VN
        assert dt.minute == 30

    def test_chuoi_moi_co_offset_giu_instant(self):
        dt = parse_legacy_utc("2026-07-30T14:30:00+07:00")
        assert dt.hour == 14
        assert dt.utcoffset() == timedelta(hours=7)

    def test_chuoi_z_suffix(self):
        dt = parse_legacy_utc("2026-07-30T07:30:00Z")
        assert dt.hour == 14


class TestFmtVn:
    def test_fmt_chuoi_legacy_utc(self):
        assert fmt_vn("2026-07-30T07:30:00") == "30/07/2026 14:30"

    def test_fmt_chuoi_moi_offset_vn(self):
        assert fmt_vn("2026-07-30T14:30:00+07:00") == "30/07/2026 14:30"

    def test_fmt_datetime_aware(self):
        dt = datetime(2026, 7, 30, 7, 30, tzinfo=timezone.utc)
        assert fmt_vn(dt) == "30/07/2026 14:30"

    def test_fmt_none_rong(self):
        assert fmt_vn(None) == ""
