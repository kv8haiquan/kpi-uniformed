"""
app/models/phieu_danh_gia.py
=============================
Model cho Phiếu theo dõi, đánh giá công chức theo QUÝ (Mẫu 01A/01B).

Tương ứng với mục 4 (Ưu điểm), 5 (Hạn chế), 6 (Ý kiến cấp có thẩm quyền)
trong Phụ lục I Nghị định 335/2025/NĐ-CP.

Workflow 1 cấp:
    NHAP ──(CC gửi)──► CHO_PHE_DUYET ──(duyệt)──► DA_PHE_DUYET
                                    └──(từ chối + lý do)──► BI_TU_CHOI ──(CC sửa)──► NHAP

Phân công người duyệt:
    - CONG_CHUC, PHO_DON_VI      → TRUONG_DON_VI cùng đơn vị
    - TRUONG_DON_VI, PHO_CHI_CUC_TRUONG → CHI_CUC_TRUONG
    - CHI_CUC_TRUONG: không có phiếu

Phiên bản: 1.0.0 (17/04/2026)
"""

import enum
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user_org import CongChuc


class TrangThaiPhieuDanhGia(str, enum.Enum):
    """Trạng thái phiếu đánh giá cá nhân (workflow 1 cấp)."""

    NHAP = "NHAP"
    CHO_PHE_DUYET = "CHO_PHE_DUYET"
    DA_PHE_DUYET = "DA_PHE_DUYET"
    BI_TU_CHOI = "BI_TU_CHOI"


TRANG_THAI_PHIEU_VALUES = [t.value for t in TrangThaiPhieuDanhGia]


class PhieuDanhGiaQuy(BaseModel):
    """
    Phiếu theo dõi, đánh giá công chức theo quý.

    Lưu nội dung mục 4/5/6 của Mẫu 01A (CC) và 01B (LĐ),
    cùng workflow phê duyệt 1 cấp.
    """

    __tablename__ = "phieu_danh_gia_quy"

    # -------------------------------------------------------------------------
    # FOREIGN KEYS & KỲ ĐÁNH GIÁ
    # -------------------------------------------------------------------------

    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID công chức sở hữu phiếu",
    )

    quy: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment="Quý đánh giá (1-4)",
    )

    nam: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment="Năm đánh giá",
    )

    # -------------------------------------------------------------------------
    # NỘI DUNG TỰ NHẬN XÉT (CC nhập)
    # -------------------------------------------------------------------------

    uu_diem: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mục 4: Ưu điểm — CC tự nhập",
    )

    han_che: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mục 5: Hạn chế, khuyết điểm — CC tự nhập",
    )

    # -------------------------------------------------------------------------
    # Ý KIẾN LÃNH ĐẠO (TDV/CCT nhập khi duyệt)
    # -------------------------------------------------------------------------

    y_kien_lanh_dao: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mục 6: Ý kiến nhận xét của cấp có thẩm quyền",
    )

    # -------------------------------------------------------------------------
    # WORKFLOW
    # -------------------------------------------------------------------------

    trang_thai: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TrangThaiPhieuDanhGia.NHAP.value,
        server_default=TrangThaiPhieuDanhGia.NHAP.value,
        index=True,
        comment="Trạng thái: NHAP | CHO_PHE_DUYET | DA_PHE_DUYET | BI_TU_CHOI",
    )

    ngay_gui_duyet: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ngày CC nhấn gửi duyệt lần gần nhất",
    )

    nguoi_phe_duyet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID người đã duyệt/từ chối (TDV hoặc CCT)",
    )

    ngay_phe_duyet: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ngày duyệt/từ chối gần nhất",
    )

    ly_do_tu_choi: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Lý do từ chối (bắt buộc khi trang_thai=BI_TU_CHOI)",
    )

    # -------------------------------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------------------------------

    cong_chuc: Mapped["CongChuc"] = relationship(
        "CongChuc",
        foreign_keys=[cong_chuc_id],
        lazy="joined",
    )

    nguoi_phe_duyet: Mapped[Optional["CongChuc"]] = relationship(
        "CongChuc",
        foreign_keys=[nguoi_phe_duyet_id],
        lazy="joined",
    )

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------

    __table_args__ = (
        UniqueConstraint(
            "cong_chuc_id", "quy", "nam",
            name="uq_phieu_quy_cc_quy_nam",
        ),
        CheckConstraint("quy BETWEEN 1 AND 4", name="ck_phieu_quy_quy"),
        CheckConstraint("nam BETWEEN 2020 AND 2100", name="ck_phieu_quy_nam"),
        CheckConstraint(
            "trang_thai IN ('NHAP','CHO_PHE_DUYET','DA_PHE_DUYET','BI_TU_CHOI')",
            name="ck_phieu_quy_trang_thai",
        ),
        Index("idx_phieu_quy_cc_quy_nam", "cong_chuc_id", "quy", "nam"),
        Index("idx_phieu_quy_trang_thai", "trang_thai"),
    )

    def __repr__(self) -> str:
        return (
            f"<PhieuDanhGiaQuy(id={self.id}, "
            f"cc_id={self.cong_chuc_id}, "
            f"Q{self.quy}/{self.nam}, "
            f"trang_thai={self.trang_thai})>"
        )
