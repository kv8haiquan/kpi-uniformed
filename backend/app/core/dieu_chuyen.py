"""
app/core/dieu_chuyen.py
=======================
Phần dùng chung giữa điều chuyển LẺ (`admin.transfer_user`) và điều chuyển
HÀNG LOẠT (`admin_dieu_chuyen_hang_loat`).

Tách ra vì hai luồng phải sinh CÙNG một hệ quả. Nếu để mỗi bên một bản, chỉ cần
sửa một bên là dữ liệu hai đường đi bắt đầu lệch nhau — mà lệch ở đây nghĩa là
kê khai/xếp loại của người vừa chuyển đơn vị bị xử lý khác nhau tuỳ theo admin
bấm nút nào.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bao_cao_xep_loai import BaoCaoXepLoai, ChiTietXepLoai
from app.models.kpi_assessment import DanhGiaThang
from app.models.kpi_submission import KeKhaiCongViec, TrangThaiKeKhai


async def don_dep_du_lieu_khi_chuyen_don_vi(
    db: AsyncSession,
    cong_chuc_id: UUID,
    hom_nay: date | None = None,
) -> None:
    """
    Ba việc phải làm khi một công chức ĐỔI ĐƠN VỊ.

    1. KHOÁ đánh giá tháng hiện tại trở về trước — các tháng đó thuộc trách
       nhiệm đơn vị cũ, không để đơn vị mới sửa lùi.
    2. XOÁ MỀM kê khai còn ở trạng thái NHAP — bản nháp gắn với công việc của
       đơn vị cũ, mang sang đơn vị mới là vô nghĩa. Bản đã gửi/đã duyệt giữ nguyên.
    3. GỠ khỏi chi tiết xếp loại của báo cáo CHƯA duyệt (NHAP / CHO_PHE_DUYET /
       TU_CHOI) để báo cáo dựng lại theo đơn vị mới. Báo cáo ĐÃ duyệt thì giữ —
       đó là số liệu đã chốt.

    Gọi hàm này TRƯỚC khi ghi bản ghi `lich_su_dieu_chuyen`, và chỉ gọi khi đơn
    vị thực sự đổi. Hàm KHÔNG tự `commit` — để nơi gọi gộp vào transaction của nó.
    """
    hom_nay = hom_nay or date.today()

    # 1. Khoá đánh giá tháng hiện tại trở về trước
    await db.execute(
        sa.update(DanhGiaThang)
        .where(DanhGiaThang.cong_chuc_id == cong_chuc_id)
        .where(DanhGiaThang.is_khoa == False)  # noqa: E712
        .where(
            or_(
                DanhGiaThang.nam < hom_nay.year,
                and_(
                    DanhGiaThang.nam == hom_nay.year,
                    DanhGiaThang.thang <= hom_nay.month,
                ),
            )
        )
        .values(is_khoa=True)
    )

    # 2. Xoá mềm kê khai còn là bản nháp
    await db.execute(
        sa.update(KeKhaiCongViec)
        .where(KeKhaiCongViec.cong_chuc_id == cong_chuc_id)
        .where(KeKhaiCongViec.trang_thai == TrangThaiKeKhai.NHAP)
        .where(KeKhaiCongViec.is_deleted == False)  # noqa: E712
        .values(is_deleted=True, is_khoa=True)
    )

    # 3. Gỡ khỏi chi tiết xếp loại của báo cáo chưa duyệt
    chi_tiet_ids = (await db.execute(
        select(ChiTietXepLoai.id)
        .join(BaoCaoXepLoai)
        .where(ChiTietXepLoai.cong_chuc_id == cong_chuc_id)
        .where(
            BaoCaoXepLoai.trang_thai.in_(("NHAP", "CHO_PHE_DUYET", "TU_CHOI"))
        )
    )).scalars().all()

    if chi_tiet_ids:
        await db.execute(
            sa.delete(ChiTietXepLoai).where(ChiTietXepLoai.id.in_(chi_tiet_ids))
        )

    await db.flush()
