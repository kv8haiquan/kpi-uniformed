"""
app/core/kpi_version.py
=======================
Helper resolve version KPI cho 1 (CC, tháng, năm).

Logic ưu tiên (cập nhật 02/05/2026):
0. cong_chuc.is_lanh_dao OR HD_111 → luôn 'V1' (LOCKED 4 / Phase 3).
1. danh_gia_thang.version_tinh_diem nếu đã tồn tại row.
2. cong_chuc.kpi_version_pinned (LOCKED 19).
3. platform_config('kpi_version_default') — mặc định 'V2_PL3'.

CẬP NHẬT 02/05/2026: Đã loại bỏ bước "đọc version_kekhai của bản đầu tiên
trong tháng". Lý do: nếu CC V2 lỡ kê khai V1 (form cũ), bước này sẽ ép
toàn bộ tháng tính theo V1. Sau khi đóng kê khai V1 (xem _assert_v1_writable
trong endpoints/ke_khai.py), version chỉ phụ thuộc vào pin của user và
platform_config — bản V1 cũ giữ làm tham khảo, không tham gia tính điểm.

Trả về 'V1' hoặc 'V2_PL3'.
"""

from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kpi_assessment import DanhGiaThang
from app.models.user_org import CongChuc


VERSION_V1 = "V1"
VERSION_V2 = "V2_PL3"


async def resolve_kpi_version(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
) -> str:
    """Quyết định phiên bản KPI cho (CC, tháng, năm)."""
    # 0. Lãnh đạo VÀ Hợp đồng 111 luôn dùng V1
    #    LOCKED 4: V2_PL3 chỉ áp cho công chức thường.
    #    Phase 3 (29/04/2026): HD_111 cũng kê khai theo form lãnh đạo, dùng V1.
    from app.models.user_org import VaiTro  # tránh circular import
    stmt_user = (
        select(CongChuc.is_lanh_dao, VaiTro.ma_vai_tro)
        .join(VaiTro, VaiTro.id == CongChuc.vai_tro_id, isouter=True)
        .where(CongChuc.id == cong_chuc_id)
    )
    row = (await db.execute(stmt_user)).first()
    if row:
        is_ld, ma_vt = row
        if is_ld or ma_vt == "HD_111":
            return VERSION_V1

    # 1. danh_gia_thang
    stmt_dg = (
        select(DanhGiaThang.version_tinh_diem)
        .where(DanhGiaThang.cong_chuc_id == cong_chuc_id)
        .where(DanhGiaThang.thang == thang)
        .where(DanhGiaThang.nam == nam)
        .where(DanhGiaThang.is_deleted == False)  # noqa: E712
        .limit(1)
    )
    v = (await db.execute(stmt_dg)).scalar_one_or_none()
    if v:
        return v

    # 2. Pin của CC (LOCKED 19) — bỏ bước đọc version_kekhai (02/05/2026).
    stmt_cc = select(CongChuc.kpi_version_pinned).where(CongChuc.id == cong_chuc_id)
    pinned = (await db.execute(stmt_cc)).scalar_one_or_none()
    if pinned:
        return pinned

    # 3. platform_config default
    stmt_cfg = text(
        "SELECT value FROM public.platform_config WHERE key='kpi_version_default'"
    )
    row = (await db.execute(stmt_cfg)).scalar_one_or_none()
    if row:
        if isinstance(row, str):
            return row
        return str(row).strip('"')
    return VERSION_V1
