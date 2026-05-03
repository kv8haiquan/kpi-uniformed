"""PL3 V2 - 006: Seed platform_config kpi_version_default = 'V2_PL3'

Revision ID: pl3_v2_006_seed_kpi_version_default_20260428
Revises: pl3_v2_005_cong_chuc_pin_version_20260428
Create Date: 2026-04-28

Phase A.5b — Seed default version cho hệ thống.

Quyết định LOCKED 18: test env trước, mặc định V2_PL3.
Cách lưu (DB-driven): row platform_config(key='kpi_version_default') với value JSONB.
  - Ưu điểm: cutover/rollback chỉ cần 1 SQL UPDATE, không phải redeploy.

Bảng `platform_config` có schema (key VARCHAR PK, value JSONB NOT NULL, mo_ta, ...)
nên giá trị phải nằm trong JSONB string: `'"V2_PL3"'::jsonb`.

Idempotent: dùng ON CONFLICT để re-run an toàn.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "pl3_v2_006_seed_def_20260428"
down_revision: Union[str, None] = "pl3_v2_005_cc_pin_20260428"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO public.platform_config (key, value, mo_ta)
        VALUES (
            'kpi_version_default',
            '"V2_PL3"'::jsonb,
            'Phiên bản KPI mặc định khi cong_chuc.kpi_version_pinned IS NULL. Giá trị: V1 hoặc V2_PL3.'
        )
        ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value,
                mo_ta = EXCLUDED.mo_ta,
                updated_at = NOW()
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM public.platform_config WHERE key = 'kpi_version_default'
    """)
