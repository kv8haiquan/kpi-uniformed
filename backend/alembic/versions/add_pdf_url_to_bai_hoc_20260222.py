"""add pdf_url to lms.bai_hoc

Revision ID: add_pdf_url_bai_hoc_20260222
Revises: add_che_do_xem_bkt_20260222
Create Date: 2026-02-22 14:00:00.000000

Them cot pdf_url vao bang lms.bai_hoc.
Luu URL ban PDF duoc convert tu PPTX/PPT bang LibreOffice headless.
"""

from alembic import op
import sqlalchemy as sa

revision = 'add_pdf_url_bai_hoc_20260222'
down_revision = 'add_che_do_xem_bkt_20260222'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'bai_hoc',
        sa.Column(
            'pdf_url',
            sa.String(500),
            nullable=True,
            comment='URL ban PDF convert tu PPTX/DOCX, dung de xem tren web',
        ),
        schema='lms',
    )


def downgrade() -> None:
    op.drop_column('bai_hoc', 'pdf_url', schema='lms')
