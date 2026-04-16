"""
app/models/bao_cao_xep_loai_quy.py
===================================
Models cho Báo cáo Xếp loại Chất lượng Công chức theo Quý.

Module này hỗ trợ:
- Đội trưởng lập báo cáo xếp loại quý cho đơn vị
- CCT phê duyệt báo cáo
- Tích hợp cả Lãnh đạo và CC thường trong cùng báo cáo

Khác với báo cáo tháng:
- Theo quý (1-4) thay vì tháng (1-12)
- Điểm là trung bình 3 tháng trong quý
- KHÔNG có so_ngay_lam_viec, so_ngay_nghi

Tham chiếu: Báo cáo xếp loại tháng (bao_cao_xep_loai.py)

Phiên bản: 1.0 (16/04/2026)
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    Text,
    ForeignKey,
    Index,
    Numeric,
    CheckConstraint,
    UniqueConstraint,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, BaseModelWithSoftDelete
from app.models.bao_cao_xep_loai import (
    TrangThaiBaoCao,
    XepLoaiChatLuong,
    tinh_xep_loai,
)

if TYPE_CHECKING:
    from app.models.user_org import CongChuc, DonVi


# =============================================================================
# MODELS
# =============================================================================

class BaoCaoXepLoaiQuy(BaseModelWithSoftDelete):
    """
    Báo cáo xếp loại chất lượng công chức theo đơn vị/quý.

    Mỗi đơn vị có duy nhất 1 báo cáo cho mỗi quý.
    Đội trưởng lập báo cáo, CCT phê duyệt.

    Luồng xử lý:
    1. Đội trưởng mở báo cáo → Hệ thống tự động tạo với dữ liệu trung bình 3 tháng
    2. Đội trưởng điều chỉnh xếp loại (nếu cần) → Nhập lý do
    3. Đội trưởng gửi duyệt → CHO_PHE_DUYET
    4. CCT xem xét, điều chỉnh (nếu cần) → Phê duyệt/Từ chối
    5. DA_PHE_DUYET (khóa) hoặc TU_CHOI (sửa và gửi lại)

    Đặc biệt:
    - Đơn vị "Lãnh đạo Chi cục": CCT tự lập và tự phê duyệt

    Relationships:
    - don_vi: Đơn vị của báo cáo
    - nguoi_lap: Người lập (Đội trưởng hoặc CCT)
    - nguoi_phe_duyet: Người phê duyệt (CCT)
    - chi_tiets: Danh sách chi tiết xếp loại từng CC
    """

    __tablename__ = "bao_cao_xep_loai_quy"

    # -------------------------------------------------------------------------
    # THÔNG TIN BÁO CÁO
    # -------------------------------------------------------------------------

    don_vi_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("don_vi.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="ID đơn vị"
    )

    quy: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Quý đánh giá (1-4)"
    )

    nam: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Năm đánh giá"
    )

    # -------------------------------------------------------------------------
    # NGƯỜI LẬP
    # -------------------------------------------------------------------------

    nguoi_lap_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="ID người lập báo cáo (Đội trưởng hoặc CCT)"
    )

    ngay_lap: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ngày lập (thời điểm gửi duyệt)"
    )

    ngay_gui_duyet: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ngày gửi phê duyệt (Đội trưởng gửi lên CCT)"
    )

    # -------------------------------------------------------------------------
    # TRẠNG THÁI
    # -------------------------------------------------------------------------

    trang_thai: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="NHAP",
        index=True,
        comment="Trạng thái: NHAP, CHO_PHE_DUYET, DA_PHE_DUYET, TU_CHOI"
    )

    # -------------------------------------------------------------------------
    # PHÊ DUYỆT (CCT)
    # -------------------------------------------------------------------------

    nguoi_phe_duyet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID người phê duyệt (CCT)"
    )

    ngay_phe_duyet: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ngày phê duyệt"
    )

    y_kien_phe_duyet: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Ý kiến của CCT khi phê duyệt/từ chối"
    )

    # -------------------------------------------------------------------------
    # THỐNG KÊ
    # -------------------------------------------------------------------------

    tong_cong_chuc: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        comment="Tổng số CC trong báo cáo"
    )

    so_loai_a: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        comment="Số CC loại A"
    )

    so_loai_b: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        comment="Số CC loại B"
    )

    so_loai_c: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        comment="Số CC loại C"
    )

    so_loai_d: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        comment="Số CC loại D"
    )

    so_loai_e: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        comment="Số CC loại E"
    )

    canh_bao_ty_le_a: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        comment="Cảnh báo nếu loại A > 20% loại B"
    )

    # -------------------------------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------------------------------

    don_vi: Mapped["DonVi"] = relationship(
        "DonVi",
        foreign_keys=[don_vi_id],
        lazy="joined"
    )

    nguoi_lap: Mapped["CongChuc"] = relationship(
        "CongChuc",
        foreign_keys=[nguoi_lap_id],
        lazy="joined"
    )

    nguoi_phe_duyet: Mapped[Optional["CongChuc"]] = relationship(
        "CongChuc",
        foreign_keys=[nguoi_phe_duyet_id],
        lazy="joined"
    )

    chi_tiets: Mapped[List["ChiTietXepLoaiQuy"]] = relationship(
        "ChiTietXepLoaiQuy",
        back_populates="bao_cao",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------

    __table_args__ = (
        UniqueConstraint("don_vi_id", "quy", "nam", name="uq_bao_cao_quy_don_vi_quy_nam"),
        CheckConstraint("quy >= 1 AND quy <= 4", name="ck_bao_cao_quy_quy"),
        CheckConstraint("nam >= 2025", name="ck_bao_cao_quy_nam"),
        Index("idx_bao_cao_quy_don_vi_quy_nam", "don_vi_id", "quy", "nam"),
        Index("idx_bao_cao_quy_trang_thai", "trang_thai"),
    )

    def __repr__(self) -> str:
        return (
            f"<BaoCaoXepLoaiQuy(id={self.id}, "
            f"don_vi={self.don_vi_id}, "
            f"quy={self.quy}/{self.nam}, "
            f"trang_thai={self.trang_thai})>"
        )

    # -------------------------------------------------------------------------
    # HELPER METHODS
    # -------------------------------------------------------------------------

    def tinh_thong_ke(self) -> dict:
        """
        Tính toán thống kê từ danh sách chi tiết.

        Returns:
            dict: {tong_cong_chuc, so_loai_a, so_loai_b, ...}
        """
        stats = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}

        for ct in self.chi_tiets:
            # Ưu tiên: quyet_dinh > de_xuat > he_thong
            xep_loai = ct.xep_loai_quyet_dinh or ct.xep_loai_de_xuat or ct.xep_loai_he_thong
            if xep_loai in stats:
                stats[xep_loai] += 1

        return {
            "tong_cong_chuc": len(self.chi_tiets),
            "so_loai_a": stats["A"],
            "so_loai_b": stats["B"],
            "so_loai_c": stats["C"],
            "so_loai_d": stats["D"],
            "so_loai_e": stats["E"],
        }

    def kiem_tra_ty_le_a(self) -> bool:
        """
        Kiểm tra tỷ lệ loại A có vượt 20% loại B không.

        Quy tắc: Số CC loại A ≤ 20% số CC loại B

        Returns:
            bool: True nếu vi phạm (cần cảnh báo)
        """
        stats = self.tinh_thong_ke()
        so_a = stats["so_loai_a"]
        so_b = stats["so_loai_b"]

        if so_b == 0:
            return so_a > 0  # Có A mà không có B → vi phạm

        return so_a > (0.2 * so_b)


class ChiTietXepLoaiQuy(BaseModel):
    """
    Chi tiết xếp loại từng công chức trong báo cáo quý.

    Lưu trữ:
    - Điểm snapshot từ hệ thống tại thời điểm tạo báo cáo (trung bình 3 tháng)
    - Xếp loại đề xuất của Đội trưởng
    - Xếp loại quyết định của CCT
    - Trạng thái từ chối riêng (nếu CCT từ chối 1 CC cụ thể)

    Quy tắc:
    - Nếu điều chỉnh xếp loại khác hệ thống → BẮT BUỘC nhập lý do
    - Đội trưởng điều chỉnh → ly_do_dieu_chinh_dt
    - CCT điều chỉnh → ly_do_dieu_chinh_cct

    Khác với chi tiết tháng:
    - KHÔNG có so_ngay_lam_viec, so_ngay_nghi
    - Điểm là trung bình 3 tháng trong quý

    Relationships:
    - bao_cao: Báo cáo chứa chi tiết này
    - cong_chuc: Công chức được đánh giá
    """

    __tablename__ = "chi_tiet_xep_loai_quy"

    # -------------------------------------------------------------------------
    # FOREIGN KEYS
    # -------------------------------------------------------------------------

    bao_cao_quy_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("bao_cao_xep_loai_quy.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID báo cáo quý"
    )

    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="ID công chức"
    )

    # -------------------------------------------------------------------------
    # PHÂN LOẠI ĐỐI TƯỢNG
    # -------------------------------------------------------------------------

    is_lanh_dao: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        index=True,
        comment="Có phải lãnh đạo không (để phân biệt nguồn tính điểm)"
    )

    # -------------------------------------------------------------------------
    # ĐIỂM TỪ HỆ THỐNG (SNAPSHOT - TRUNG BÌNH 3 THÁNG)
    # -------------------------------------------------------------------------

    diem_tieu_chi_chung: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0"),
        server_default="0",
        comment="Điểm tiêu chí chung (0-30) - trung bình 3 tháng"
    )

    diem_kpi: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0"),
        server_default="0",
        comment="Điểm KPI đã nhân 70 (0-70) - trung bình 3 tháng"
    )

    diem_tong: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0"),
        server_default="0",
        comment="Điểm tổng = tiêu chí chung + KPI (0-100) - trung bình 3 tháng"
    )

    xep_loai_he_thong: Mapped[str] = mapped_column(
        String(1),
        nullable=False,
        index=True,
        comment="Xếp loại hệ thống tự tính (A/B/C/D/E)"
    )

    # -------------------------------------------------------------------------
    # ĐỀ XUẤT CỦA ĐỘI TRƯỞNG
    # -------------------------------------------------------------------------

    xep_loai_de_xuat: Mapped[Optional[str]] = mapped_column(
        String(1),
        nullable=True,
        comment="Xếp loại Đội trưởng đề xuất"
    )

    ly_do_dieu_chinh_dt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Lý do điều chỉnh của Đội trưởng (bắt buộc nếu khác hệ thống)"
    )

    # -------------------------------------------------------------------------
    # QUYẾT ĐỊNH CỦA CCT
    # -------------------------------------------------------------------------

    xep_loai_quyet_dinh: Mapped[Optional[str]] = mapped_column(
        String(1),
        nullable=True,
        comment="Xếp loại CCT quyết định"
    )

    ly_do_dieu_chinh_cct: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Lý do điều chỉnh của CCT (bắt buộc nếu khác đề xuất)"
    )

    # -------------------------------------------------------------------------
    # TRẠNG THÁI TỪ CHỐI RIÊNG
    # -------------------------------------------------------------------------

    bi_tu_choi: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        comment="CC này bị CCT từ chối (cần sửa riêng)"
    )

    ly_do_tu_choi: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Lý do CCT từ chối CC này"
    )

    # -------------------------------------------------------------------------
    # GHI CHÚ
    # -------------------------------------------------------------------------

    ghi_chu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Ghi chú bổ sung"
    )

    # -------------------------------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------------------------------

    bao_cao: Mapped["BaoCaoXepLoaiQuy"] = relationship(
        "BaoCaoXepLoaiQuy",
        back_populates="chi_tiets",
        lazy="joined"
    )

    cong_chuc: Mapped["CongChuc"] = relationship(
        "CongChuc",
        lazy="joined"
    )

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------

    __table_args__ = (
        CheckConstraint(
            "xep_loai_he_thong IN ('A', 'B', 'C', 'D', 'E')",
            name="ck_ctxl_quy_xep_loai_ht"
        ),
        CheckConstraint(
            "xep_loai_de_xuat IS NULL OR xep_loai_de_xuat IN ('A', 'B', 'C', 'D', 'E')",
            name="ck_ctxl_quy_xep_loai_dx"
        ),
        CheckConstraint(
            "xep_loai_quyet_dinh IS NULL OR xep_loai_quyet_dinh IN ('A', 'B', 'C', 'D', 'E')",
            name="ck_ctxl_quy_xep_loai_qd"
        ),
        UniqueConstraint("bao_cao_quy_id", "cong_chuc_id", name="uq_ctxl_quy_bao_cao_cc"),
        Index("idx_ctxl_quy_bao_cao", "bao_cao_quy_id"),
        Index("idx_ctxl_quy_cong_chuc", "cong_chuc_id"),
        Index("idx_ctxl_quy_xep_loai_ht", "xep_loai_he_thong"),
        Index("idx_ctxl_quy_is_lanh_dao", "is_lanh_dao"),
    )

    def __repr__(self) -> str:
        return (
            f"<ChiTietXepLoaiQuy(id={self.id}, "
            f"cc_id={self.cong_chuc_id}, "
            f"he_thong={self.xep_loai_he_thong}, "
            f"de_xuat={self.xep_loai_de_xuat}, "
            f"quyet_dinh={self.xep_loai_quyet_dinh})>"
        )

    # -------------------------------------------------------------------------
    # HELPER PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def xep_loai_cuoi_cung(self) -> str:
        """
        Lấy xếp loại cuối cùng (ưu tiên quyết định > đề xuất > hệ thống).
        """
        return self.xep_loai_quyet_dinh or self.xep_loai_de_xuat or self.xep_loai_he_thong

    @property
    def da_dieu_chinh(self) -> bool:
        """
        Kiểm tra xem có điều chỉnh so với hệ thống không.
        """
        xep_loai = self.xep_loai_de_xuat or self.xep_loai_quyet_dinh
        return xep_loai is not None and xep_loai != self.xep_loai_he_thong
