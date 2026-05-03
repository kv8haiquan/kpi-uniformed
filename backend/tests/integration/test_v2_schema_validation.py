"""
tests/integration/test_v2_schema_validation.py
==============================================
Validate Pydantic schema V2 reject các trường hợp:
- Extra field không được phép (vd: he_so_thuc_te, cap_do_id từ V1).
- so_luong ≤ 0.
- thang/nam ngoài range.
"""

import pytest
from pydantic import ValidationError

from app.schemas.kpi_submission_v2 import (
    KeKhaiV2Create,
    KeKhaiV2NhieuNgayCreate,
    KeKhaiV2Update,
)


def _base_payload():
    return {
        "danh_muc_sp_id": "00000000-0000-0000-0000-000000000001",
        "so_luong": 5,
        "thang": 4,
        "nam": 2026,
        "nguoi_phe_duyet_id": "00000000-0000-0000-0000-000000000002",
    }


class TestExtraFieldRejection:
    """LOCKED 14 + decision Phase C: V2 không cho extra fields."""

    def test_reject_he_so_thuc_te_in_create(self):
        payload = _base_payload()
        payload["he_so_thuc_te"] = "1.5"  # field V1, không có trong V2
        with pytest.raises(ValidationError) as exc:
            KeKhaiV2Create(**payload)
        assert "he_so_thuc_te" in str(exc.value)
        assert "extra" in str(exc.value).lower() or "forbidden" in str(exc.value).lower()

    def test_reject_cap_do_id_in_create(self):
        payload = _base_payload()
        payload["cap_do_id"] = "00000000-0000-0000-0000-000000000003"
        with pytest.raises(ValidationError) as exc:
            KeKhaiV2Create(**payload)
        assert "cap_do_id" in str(exc.value)

    def test_reject_random_field(self):
        payload = _base_payload()
        payload["foo_bar"] = "anything"
        with pytest.raises(ValidationError):
            KeKhaiV2Create(**payload)

    def test_reject_he_so_thuc_te_in_update(self):
        with pytest.raises(ValidationError):
            KeKhaiV2Update(he_so_thuc_te="1.5")

    def test_reject_cap_do_id_in_multi_day(self):
        with pytest.raises(ValidationError):
            KeKhaiV2NhieuNgayCreate(
                danh_muc_sp_id="00000000-0000-0000-0000-000000000001",
                so_luong=1,
                ngay_thuc_hien_list=["2026-04-01"],
                nguoi_phe_duyet_id="00000000-0000-0000-0000-000000000002",
                cap_do_id="00000000-0000-0000-0000-000000000003",
            )


class TestNumericValidation:
    def test_reject_so_luong_zero(self):
        payload = _base_payload()
        payload["so_luong"] = 0
        with pytest.raises(ValidationError):
            KeKhaiV2Create(**payload)

    def test_reject_so_luong_negative(self):
        payload = _base_payload()
        payload["so_luong"] = -1
        with pytest.raises(ValidationError):
            KeKhaiV2Create(**payload)

    def test_reject_thang_out_of_range(self):
        payload = _base_payload()
        payload["thang"] = 13
        with pytest.raises(ValidationError):
            KeKhaiV2Create(**payload)

    def test_reject_nam_too_old(self):
        payload = _base_payload()
        payload["nam"] = 2020
        with pytest.raises(ValidationError):
            KeKhaiV2Create(**payload)


class TestValidPayload:
    """Smoke: payload đầy đủ field hợp lệ → pass."""

    def test_minimal_valid(self):
        kk = KeKhaiV2Create(**_base_payload())
        assert kk.so_luong == 5
        assert kk.thang == 4

    def test_with_optional_fields(self):
        payload = _base_payload()
        payload.update({
            "ngay_thuc_hien": "2026-04-15",
            "mo_ta_cong_viec": "Test V2",
            "is_doi_moi_sang_tao": True,
            "tu_danh_gia_chat_luong": 1,
            "tu_danh_gia_tien_do": 0,
        })
        kk = KeKhaiV2Create(**payload)
        assert kk.tu_danh_gia_chat_luong == 1
        assert kk.is_doi_moi_sang_tao is True
