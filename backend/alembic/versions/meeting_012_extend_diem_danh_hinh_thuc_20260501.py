"""Meeting 012: extend meeting.diem_danh.hinh_thuc CHECK với 'TU_DIEM_DANH'

Revision ID: mt_012_extend_dd_20260501
Revises: mt_011_seed_roles_20260430
Create Date: 2026-05-01

G4-fix-6.2: thêm hình thức điểm danh 'TU_DIEM_DANH' (CBCC tự click trong app
trên máy tính, không cần quét QR). Phân biệt với 'QR' để audit/thống kê.

Phase tiếp có thể thêm 'TU_DONG' (Jitsi auto-attendance).
"""

from typing import Sequence, Union

from alembic import op


revision: str = "mt_012_extend_dd_20260501"
down_revision: Union[str, None] = "mt_011_seed_roles_20260430"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE meeting.diem_danh DROP CONSTRAINT ck_diem_danh_hinh_thuc")
    op.execute("""
        ALTER TABLE meeting.diem_danh
          ADD CONSTRAINT ck_diem_danh_hinh_thuc
          CHECK (hinh_thuc IN ('QR', 'BAM_TAY', 'TU_DIEM_DANH'))
    """)


def downgrade() -> None:
    # Cảnh báo: nếu có row TU_DIEM_DANH → downgrade FAIL.
    # Khuyến nghị clean trước: UPDATE meeting.diem_danh SET hinh_thuc='QR' WHERE hinh_thuc='TU_DIEM_DANH'
    op.execute("ALTER TABLE meeting.diem_danh DROP CONSTRAINT ck_diem_danh_hinh_thuc")
    op.execute("""
        ALTER TABLE meeting.diem_danh
          ADD CONSTRAINT ck_diem_danh_hinh_thuc
          CHECK (hinh_thuc IN ('QR', 'BAM_TAY'))
    """)
