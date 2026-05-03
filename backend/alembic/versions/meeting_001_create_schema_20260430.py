"""Meeting 001: CREATE SCHEMA meeting

Revision ID: mt_001_schema_20260430
Revises: common_001_audit_log_20260430
Create Date: 2026-04-30

Tạo schema `meeting` cho module HKG (Họp Không Giấy).
Schema này độc lập với KPI/LMS, FK chỉ tới public.cong_chuc, public.don_vi,
public.platform_role.

Tham chiếu: docs/HKG/HKG_DATABASE_DESIGN.md §2 và §9.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "mt_001_schema_20260430"
down_revision: Union[str, None] = "common_001_audit_log_20260430"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    # Đảm bảo extension cần thiết — pgcrypto cho gen_random_uuid()
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')


def downgrade() -> None:
    # CASCADE để đảm bảo drop được nếu còn object lẻ
    op.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
