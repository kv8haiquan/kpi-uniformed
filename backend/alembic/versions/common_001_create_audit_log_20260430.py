"""Common 001: Tạo bảng common.audit_log

Revision ID: common_001_audit_log_20260430
Revises: fav_001_create_cvyt_20260430
Create Date: 2026-04-30

Bảng audit log nghiệp vụ đa module — phục vụ:
- KPI: ngoài audit_log DML đã có (public.audit_log) — bảng này dùng cho audit
  cấp nghiệp vụ (LOGIN, EXPORT, ...) khi cần.
- LMS / FORUM / LEGAL / PORTAL: audit hành động người dùng đa module.
- MEETING (HKG sắp triển khai G1): bắt buộc theo HKG_DATABASE_DESIGN.md §5 +
  Phụ lục A.

Schema (theo Phụ lục A của docs/HKG/HKG_DATABASE_DESIGN.md):
    id                  UUID PK
    module              VARCHAR(20) NOT NULL  -- KPI/LMS/FORUM/LEGAL/PORTAL/MEETING/HE_THONG
    hanh_dong           VARCHAR(50) NOT NULL  -- CREATE_MEETING, UPLOAD_DOC, ...
    doi_tuong_loai      VARCHAR(50)           -- 'cuoc_hop', 'tai_lieu', ...
    doi_tuong_id        UUID
    nguoi_thuc_hien_id  UUID FK → public.cong_chuc(id)
    ip_address          INET
    user_agent          TEXT
    chi_tiet            JSONB
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()

Indexes: 5 (module, doi_tuong, nguoi, thoi_gian DESC, module+thoi_gian DESC).

LƯU Ý SCOPE:
- Migration này thuộc common_service (platform-level), KHÔNG thuộc HKG.
- KPI hiện có public.audit_log (DML triggers, INSERT/UPDATE/DELETE) — KHÔNG đụng.
- Hai bảng tồn tại độc lập, không hợp nhất.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "common_001_audit_log_20260430"
down_revision: Union[str, None] = "fav_001_create_cvyt_20260430"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "common"
TBL = "audit_log"


def upgrade() -> None:
    # Schema common đã được tạo bởi create_common_schema_20260224.py — KHÔNG tạo lại.
    # Chỉ thêm bảng audit_log.

    op.create_table(
        TBL,
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "module",
            sa.String(20),
            nullable=False,
            comment="KPI | LMS | FORUM | LEGAL | PORTAL | MEETING | HE_THONG",
        ),
        sa.Column(
            "hanh_dong",
            sa.String(50),
            nullable=False,
            comment="CREATE_MEETING, UPLOAD_DOC, CHECKIN_QR, SIGN_MINUTES, ...",
        ),
        sa.Column(
            "doi_tuong_loai",
            sa.String(50),
            nullable=True,
            comment="Loại đối tượng tác động (cuoc_hop, tai_lieu, bien_ban, ...)",
        ),
        sa.Column(
            "doi_tuong_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "nguoi_thuc_hien_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("public.cong_chuc.id"),
            nullable=False,
        ),
        sa.Column(
            "ip_address",
            postgresql.INET(),
            nullable=True,
        ),
        sa.Column(
            "user_agent",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "chi_tiet",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='{"old_value": {...}, "new_value": {...}, "context": {...}}',
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        schema=SCHEMA,
    )

    # 5 indexes theo Phụ lục A
    op.create_index(
        "idx_audit_log_module",
        TBL,
        ["module"],
        schema=SCHEMA,
    )
    op.create_index(
        "idx_audit_log_doi_tuong",
        TBL,
        ["doi_tuong_loai", "doi_tuong_id"],
        schema=SCHEMA,
    )
    op.create_index(
        "idx_audit_log_nguoi",
        TBL,
        ["nguoi_thuc_hien_id"],
        schema=SCHEMA,
    )
    op.create_index(
        "idx_audit_log_thoi_gian",
        TBL,
        [sa.text("created_at DESC")],
        schema=SCHEMA,
    )
    op.create_index(
        "idx_audit_log_module_time",
        TBL,
        ["module", sa.text("created_at DESC")],
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("idx_audit_log_module_time", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_audit_log_thoi_gian", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_audit_log_nguoi", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_audit_log_doi_tuong", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_audit_log_module", table_name=TBL, schema=SCHEMA)
    op.drop_table(TBL, schema=SCHEMA)
