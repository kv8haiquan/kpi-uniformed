"""Meeting 011: Seed 6 platform_role HKG (CHU_TOA_HOP dynamic, không seed)

Revision ID: mt_011_seed_roles_20260430
Revises: mt_010_mau_bieu_20260430
Create Date: 2026-04-30

Seed các role static cho HKG vào public.platform_role:
  - THU_KY_HOP, CHANH_VP, TRUONG_CNTT
  - DANG_VIEN, BI_THU_CHI_BO, PHO_BI_THU

CHU_TOA_HOP là DYNAMIC role — suy ra từ meeting.cuoc_hop.chu_toa_id mỗi cuộc họp.
KHÔNG seed (theo HKG_PLATFORM_ROLES.md §3.2 + §4 và HKG_DATABASE_DESIGN.md §8.1).

Filter HKG roles: WHERE quyen_han->>'module' = 'MEETING'

Schema thật public.platform_role:
  id, ma_role, ten_role, mo_ta, quyen_han(JSONB), is_active, created_at
"""

import json
from typing import Sequence, Union

from alembic import op


revision: str = "mt_011_seed_roles_20260430"
down_revision: Union[str, None] = "mt_010_mau_bieu_20260430"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PLATFORM_ROLES_HKG = [
    {
        "ma_role": "THU_KY_HOP",
        "ten_role": "Thư ký cuộc họp",
        "mo_ta": "Ghi biên bản, hỗ trợ điều hành",
        "quyen_han": {"module": "MEETING", "type": "static", "scoped": True},
    },
    {
        "ma_role": "CHANH_VP",
        "ten_role": "Chánh Văn phòng",
        "mo_ta": "Xem toàn bộ cuộc họp Chi cục, điều phối lịch",
        "quyen_han": {"module": "MEETING", "type": "static"},
    },
    {
        "ma_role": "TRUONG_CNTT",
        "ten_role": "Trưởng phòng CNTT",
        "mo_ta": "Quản trị kỹ thuật HKG + xem toàn bộ",
        "quyen_han": {"module": "MEETING", "type": "static"},
    },
    {
        "ma_role": "DANG_VIEN",
        "ten_role": "Đảng viên",
        "mo_ta": "Tham dự họp Đảng",
        "quyen_han": {"module": "MEETING", "type": "static"},
    },
    {
        "ma_role": "BI_THU_CHI_BO",
        "ten_role": "Bí thư Chi bộ",
        "mo_ta": "Chủ trì họp Chi bộ",
        "quyen_han": {"module": "MEETING", "type": "static", "scoped": True},
    },
    {
        "ma_role": "PHO_BI_THU",
        "ten_role": "Phó Bí thư Chi bộ",
        "mo_ta": "Hỗ trợ Bí thư",
        "quyen_han": {"module": "MEETING", "type": "static", "scoped": True},
    },
]


def upgrade() -> None:
    conn = op.get_bind()
    from sqlalchemy import text as sa_text

    for role in PLATFORM_ROLES_HKG:
        conn.execute(
            sa_text("""
                INSERT INTO public.platform_role
                    (id, ma_role, ten_role, mo_ta, quyen_han, is_active, created_at)
                VALUES
                    (gen_random_uuid(), :ma_role, :ten_role, :mo_ta,
                     CAST(:quyen_han AS JSONB), TRUE, NOW())
                ON CONFLICT (ma_role) DO NOTHING
            """),
            {
                "ma_role": role["ma_role"],
                "ten_role": role["ten_role"],
                "mo_ta": role["mo_ta"],
                "quyen_han": json.dumps(role["quyen_han"]),
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    from sqlalchemy import text as sa_text

    ma_roles = [r["ma_role"] for r in PLATFORM_ROLES_HKG]
    conn.execute(
        sa_text("""
            DELETE FROM public.platform_role
            WHERE ma_role = ANY(:ma_roles)
              AND quyen_han->>'module' = 'MEETING'
        """),
        {"ma_roles": ma_roles},
    )
