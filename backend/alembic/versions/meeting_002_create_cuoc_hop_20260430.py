"""Meeting 002: meeting.cuoc_hop

Revision ID: mt_002_cuoc_hop_20260430
Revises: mt_001_schema_20260430
Create Date: 2026-04-30

Bảng trung tâm của HKG. Theo HKG_DATABASE_DESIGN.md §4.1.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mt_002_cuoc_hop_20260430"
down_revision: Union[str, None] = "mt_001_schema_20260430"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
TBL = "cuoc_hop"


def upgrade() -> None:
    op.create_table(
        TBL,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),

        # Thông tin cơ bản
        sa.Column("tieu_de", sa.String(500), nullable=False),
        sa.Column("mo_ta", sa.Text(), nullable=True),

        # Phân loại — soft enum
        sa.Column("khoi", sa.String(20), server_default="CHUYEN_MON", nullable=False),
        sa.Column("hinh_thuc", sa.String(20), server_default="TRUC_TIEP", nullable=False),

        # Thời gian & địa điểm
        sa.Column("ngay_hop", sa.Date(), nullable=False),
        sa.Column("gio_bat_dau", sa.Time(), nullable=False),
        sa.Column("gio_ket_thuc", sa.Time(), nullable=True),
        sa.Column("dia_diem", sa.String(300), nullable=True),

        # Vai trò chính — cross-schema FK đến public
        sa.Column("don_vi_to_chuc_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.don_vi.id"), nullable=False),
        sa.Column("chu_toa_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=False),
        sa.Column("thu_ky_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=True),

        # Trạng thái
        sa.Column("trang_thai", sa.String(30), server_default="LEN_KE_HOACH", nullable=False),

        # Họp định kỳ (optional MVP)
        sa.Column("la_dinh_ky", sa.Boolean(), server_default=sa.text("FALSE"), nullable=True),
        sa.Column("chu_ky", sa.String(20), nullable=True),

        # Phase 8 placeholder
        sa.Column("chi_bo_id", postgresql.UUID(as_uuid=True), nullable=True),

        # Audit
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False),

        # CHECK constraints — soft enum
        sa.CheckConstraint(
            "khoi IN ('DANG', 'CHUYEN_MON', 'HANH_CHINH', 'BAN_NHOM')",
            name="ck_cuoc_hop_khoi",
        ),
        sa.CheckConstraint(
            "hinh_thuc IN ('TRUC_TIEP', 'TRUC_TUYEN', 'HYBRID')",
            name="ck_cuoc_hop_hinh_thuc",
        ),
        sa.CheckConstraint(
            "trang_thai IN ('LEN_KE_HOACH','DA_THONG_BAO','DANG_DIEN_RA','HOAN_THANH','HUY')",
            name="ck_cuoc_hop_trang_thai",
        ),
        sa.CheckConstraint(
            "chu_ky IS NULL OR chu_ky IN ('TUAN','THANG','QUY')",
            name="ck_cuoc_hop_chu_ky",
        ),

        schema=SCHEMA,
    )

    # Partial indexes — chỉ áp dụng cho rows is_deleted=FALSE
    where_active = sa.text("is_deleted = FALSE")
    op.create_index("idx_cuoc_hop_ngay", TBL, ["ngay_hop"],
                    schema=SCHEMA, postgresql_where=where_active)
    op.create_index("idx_cuoc_hop_don_vi", TBL, ["don_vi_to_chuc_id"],
                    schema=SCHEMA, postgresql_where=where_active)
    op.create_index("idx_cuoc_hop_chu_toa", TBL, ["chu_toa_id"],
                    schema=SCHEMA, postgresql_where=where_active)
    op.create_index("idx_cuoc_hop_trang_thai", TBL, ["trang_thai"],
                    schema=SCHEMA, postgresql_where=where_active)
    op.create_index("idx_cuoc_hop_khoi", TBL, ["khoi"],
                    schema=SCHEMA, postgresql_where=where_active)


def downgrade() -> None:
    op.drop_index("idx_cuoc_hop_khoi", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_cuoc_hop_trang_thai", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_cuoc_hop_chu_toa", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_cuoc_hop_don_vi", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_cuoc_hop_ngay", table_name=TBL, schema=SCHEMA)
    op.drop_table(TBL, schema=SCHEMA)
