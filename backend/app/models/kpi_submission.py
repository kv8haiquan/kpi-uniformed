"""
app/models/kpi_submission.py
============================
Models cho kê khai và phê duyệt công việc:
- KeKhaiCongViec: Bản kê khai công việc hàng ngày/tuần/tháng
- PheDuyetSp: Lịch sử phê duyệt sản phẩm

Luồng phê duyệt (QUAN TRỌNG):
1. CC kê khai → chọn Phó ĐV để phê duyệt
2. Phó ĐV phê duyệt CC
3. Trưởng ĐV kê khai → CCT phê duyệt
4. Phó CCT kê khai → CCT phê duyệt
5. CCT tự phê duyệt (báo cáo Cục HQ)

Lưu ý: Trưởng ĐV KHÔNG phê duyệt CC (chỉ Phó ĐV mới phê duyệt)

v2.7.4 (2026-02-02):
- Thêm 4 column mô tả lỗi:
  + ghi_chu_tu_dg_chat_luong: Mô tả lỗi CL tự đánh giá
  + ghi_chu_tu_dg_tien_do: Mô tả lỗi TĐ tự đánh giá
  + ghi_chu_loi_chat_luong: Mô tả lỗi CL lãnh đạo chốt
  + ghi_chu_loi_tien_do: Mô tả lỗi TĐ lãnh đạo chốt
"""

import uuid
import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String, 
    Integer, 
    Boolean, 
    Date,
    Text, 
    ForeignKey,
    Index,
    Numeric,
    CheckConstraint,
    # v2.7.3: Bỏ UniqueConstraint (đã DROP constraint uq_ke_khai_unique)
    Enum as SQLEnum,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel, BaseModelWithSoftDelete

if TYPE_CHECKING:
    from app.models.user_org import CongChuc, DonVi
    from app.models.task_catalog import DanhMucSpCongViec, CapDoPhucTap


# =============================================================================
# ENUMS
# =============================================================================

class TrangThaiKeKhai(str, enum.Enum):
    """Trạng thái của bản kê khai công việc."""
    NHAP = "NHAP"                   # Đang nhập, chưa gửi
    CHO_PHE_DUYET = "CHO_PHE_DUYET" # Đã gửi, chờ phê duyệt
    DA_PHE_DUYET = "DA_PHE_DUYET"   # Đã phê duyệt
    TU_CHOI = "TU_CHOI"             # Bị từ chối
    HUY = "HUY"                     # Đã hủy


class TrangThaiPheDuyet(str, enum.Enum):
    """Trạng thái của lượt phê duyệt."""
    CHO_XU_LY = "CHO_XU_LY"       # Chờ xử lý
    PHE_DUYET = "PHE_DUYET"       # Đã phê duyệt
    TU_CHOI = "TU_CHOI"           # Từ chối
    YEU_CAU_SUA = "YEU_CAU_SUA"   # Yêu cầu sửa lại


# =============================================================================
# MODELS
# =============================================================================

class KeKhaiCongViec(BaseModelWithSoftDelete):
    """
    Bản kê khai công việc của công chức.
    
    Mỗi bản kê khai ghi nhận:
    - Ai làm (cong_chuc_id)
    - Làm việc gì (danh_muc_sp_id)
    - Độ khó (cap_do_id)
    - Số lượng (kê khai gộp)
    - Ai phê duyệt (nguoi_phe_duyet_id - CC chọn khi kê khai)
    
    Công thức tính SP quy đổi:
    SP_quy_doi = so_luong × he_so_sp × he_so_cap_do
    
    Relationships:
    - cong_chuc: Người kê khai
    - danh_muc_sp: Công việc thực hiện
    - cap_do: Cấp độ phức tạp
    - nguoi_phe_duyet: Người được chọn phê duyệt
    - phe_duyets: Lịch sử các lượt phê duyệt
    """
    
    __tablename__ = "ke_khai_cong_viec"
    
    # -------------------------------------------------------------------------
    # NGƯỜI KÊ KHAI
    # -------------------------------------------------------------------------
    
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="ID công chức kê khai"
    )

    don_vi_id_snapshot: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("don_vi.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        comment="Snapshot đơn vị tại thời điểm kê khai (dùng cho báo cáo)"
    )

    # -------------------------------------------------------------------------
    # THỜI GIAN
    # -------------------------------------------------------------------------

    thang: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Tháng kê khai (1-12)"
    )
    
    nam: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Năm kê khai"
    )
    
    ngay_thuc_hien: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Ngày thực hiện công việc"
    )
    
    # -------------------------------------------------------------------------
    # CÔNG VIỆC
    # -------------------------------------------------------------------------
    
    danh_muc_sp_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("danh_muc_sp_cong_viec.id", ondelete="RESTRICT"),
        nullable=False,
        comment="ID công việc trong danh mục"
    )
    
    # V1: bắt buộc; V2_PL3: NULL (LOCKED 8)
    cap_do_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cap_do_phuc_tap.id", ondelete="RESTRICT"),
        nullable=True,
        comment="V1: ID cấp độ phức tạp (C1-C5). V2_PL3: NULL"
    )
    
    so_luong: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
        comment="Số lượng (kê khai gộp)"
    )
    
    # Hệ số thực tế - chỉ dùng khi cấp độ C5
    he_so_thuc_te: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Hệ số thực tế (chỉ dùng cho C5)"
    )
    
    # -------------------------------------------------------------------------
    # NGƯỜI PHÊ DUYỆT (CC CHỌN KHI KÊ KHAI)
    # -------------------------------------------------------------------------
    
    nguoi_phe_duyet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID người phê duyệt (CC chọn Phó ĐV)"
    )
    
    # -------------------------------------------------------------------------
    # THÔNG TIN BỔ SUNG
    # -------------------------------------------------------------------------
    
    mo_ta_cong_viec: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả chi tiết công việc"
    )
    
    is_doi_moi_sang_tao: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        comment="Có tính đổi mới sáng tạo không"
    )
    
    ngay_deadline: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Hạn hoàn thành"
    )
    
    ngay_hoan_thanh: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Ngày hoàn thành thực tế"
    )
    
    # -------------------------------------------------------------------------
    # TỰ ĐÁNH GIÁ CỦA CÔNG CHỨC (CC tự nhập khi kê khai)
    # -------------------------------------------------------------------------
    
    tu_danh_gia_chat_luong: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        comment="Số lỗi chất lượng do CC tự đánh giá"
    )
    
    tu_danh_gia_tien_do: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        comment="Số lần chậm tiến độ do CC tự đánh giá"
    )
    
    ghi_chu_tu_danh_gia: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Giải trình của CC về lỗi tự đánh giá"
    )
    
    # v2.7.4: Mô tả lỗi tự đánh giá - tách riêng CL và TĐ
    ghi_chu_tu_dg_chat_luong: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả lỗi chất lượng do CC tự đánh giá"
    )
    
    ghi_chu_tu_dg_tien_do: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả lỗi tiến độ do CC tự đánh giá"
    )
    
    # -------------------------------------------------------------------------
    # SỐ LỖI CHỐT CUỐI (Lãnh đạo xác nhận khi phê duyệt - dùng để tính điểm)
    # -------------------------------------------------------------------------
    
    so_loi_chat_luong: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        comment="Số lỗi CL chốt cuối (do lãnh đạo xác nhận)"
    )
    
    so_loi_tien_do: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        comment="Số lỗi TĐ chốt cuối (do lãnh đạo xác nhận)"
    )
    
    y_kien_lanh_dao: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Ý kiến phản hồi của lãnh đạo khi duyệt"
    )
    
    # v2.7.4: Mô tả lỗi lãnh đạo chốt - tách riêng CL và TĐ
    ghi_chu_loi_chat_luong: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả lỗi chất lượng do lãnh đạo chốt"
    )
    
    ghi_chu_loi_tien_do: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả lỗi tiến độ do lãnh đạo chốt"
    )
    
    # -------------------------------------------------------------------------
    # TRẠNG THÁI
    # -------------------------------------------------------------------------
    
    trang_thai: Mapped[TrangThaiKeKhai] = mapped_column(
        SQLEnum(TrangThaiKeKhai, name="trang_thai_ke_khai_enum", create_type=True),
        nullable=False,
        server_default="NHAP",
        index=True,
        comment="Trạng thái kê khai"
    )
    
    # -------------------------------------------------------------------------
    # KẾT QUẢ QUY ĐỔI (TÍNH SAU KHI PHÊ DUYỆT)
    # -------------------------------------------------------------------------
    
    so_sp_goc_quy_doi: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Số SP gốc sau quy đổi"
    )
    
    so_sp_chat_luong: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="SP sau khi trừ lỗi chất lượng"
    )
    
    so_sp_tien_do: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="SP sau khi trừ lỗi tiến độ"
    )
    
    # -------------------------------------------------------------------------
    # KHÓA DỮ LIỆU (v2.5 - 29/01/2026)
    # -------------------------------------------------------------------------
    
    is_khoa: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        comment="Khóa dữ liệu sau khi CCT phê duyệt báo cáo xếp loại tháng"
    )

    # Yêu cầu 2 (06/05/2026): LĐ đánh dấu CV chưa hoàn thành.
    # CV vẫn vào mẫu số nhưng đóng 0 vào tử số a/b/c → cả 3 chỉ số đều giảm.
    is_chua_hoan_thanh: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        comment="CV chưa hoàn thành (LĐ điều chỉnh): vẫn vào mẫu số, đóng 0 vào a/b/c"
    )

    # -------------------------------------------------------------------------
    # PL3 V2 (28/04/2026) — VERSION + SNAPSHOT (LOCKED 10, 13)
    # -------------------------------------------------------------------------

    version_kekhai: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        server_default="V1",
        comment="Phiên bản công thức: V1 (ngày×96) hoặc V2_PL3 (tổng SP kê khai)",
    )

    he_so_quy_doi_snapshot: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 4),
        nullable=True,
        comment="V2: snapshot he_so_quy_doi tại thời điểm kê khai (immutable)",
    )

    nhom_pl3_snapshot: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="V2: snapshot nhóm 1-5",
    )

    linh_vuc_snapshot: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="V2: snapshot lĩnh vực I-XV",
    )

    # -------------------------------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------------------------------

    # Người kê khai
    cong_chuc: Mapped["CongChuc"] = relationship(
        "CongChuc",
        back_populates="ke_khais",
        foreign_keys=[cong_chuc_id],
        lazy="joined"
    )

    don_vi_snapshot: Mapped[Optional["DonVi"]] = relationship(
        "DonVi",
        foreign_keys=[don_vi_id_snapshot],
        lazy="joined"
    )

    # Công việc
    danh_muc_sp: Mapped["DanhMucSpCongViec"] = relationship(
        "DanhMucSpCongViec",
        back_populates="ke_khais",
        lazy="joined"
    )
    
    # Cấp độ phức tạp — V1 only (V2_PL3 NULL)
    cap_do: Mapped[Optional["CapDoPhucTap"]] = relationship(
        "CapDoPhucTap",
        back_populates="ke_khais",
        lazy="joined"
    )
    
    # Người phê duyệt (được CC chọn)
    nguoi_phe_duyet: Mapped[Optional["CongChuc"]] = relationship(
        "CongChuc",
        foreign_keys=[nguoi_phe_duyet_id],
        lazy="joined"
    )
    
    # Lịch sử phê duyệt
    phe_duyets: Mapped[List["PheDuyetSp"]] = relationship(
        "PheDuyetSp",
        back_populates="ke_khai",
        lazy="selectin",
        order_by="PheDuyetSp.created_at.desc()"
    )
    
    # -------------------------------------------------------------------------
    # INDEXES & CONSTRAINTS
    # -------------------------------------------------------------------------
    __table_args__ = (
        # Constraints
        CheckConstraint("thang BETWEEN 1 AND 12", name="ck_ke_khai_thang"),
        CheckConstraint("nam >= 2025", name="ck_ke_khai_nam"),
        CheckConstraint("so_luong > 0", name="ck_ke_khai_so_luong"),
        CheckConstraint("tu_danh_gia_chat_luong >= 0", name="ck_ke_khai_tu_dg_cl"),
        CheckConstraint("tu_danh_gia_tien_do >= 0", name="ck_ke_khai_tu_dg_td"),
        CheckConstraint("so_loi_chat_luong >= 0", name="ck_ke_khai_loi_cl"),
        CheckConstraint("so_loi_tien_do >= 0", name="ck_ke_khai_loi_td"),
        
        # v2.7.3: Đã bỏ UniqueConstraint - cho phép CC kê khai cùng công việc
        # cùng cấp độ cùng ngày nhiều lần (VD: thanh tra sáng + chiều)
        # Constraint đã DROP bằng migration drop_uq_ke_khai_20260201

        # PL3 V2 (28/04/2026) — LOCKED 10, 13
        CheckConstraint(
            "version_kekhai IN ('V1', 'V2_PL3')",
            name="ck_kekhai_version",
        ),
        CheckConstraint(
            "version_kekhai <> 'V2_PL3' OR he_so_quy_doi_snapshot IS NOT NULL",
            name="ck_kekhai_v2_required",
        ),

        # Indexes
        Index("idx_ke_khai_cc", "cong_chuc_id"),
        Index("idx_ke_khai_thang_nam", "thang", "nam"),
        Index("idx_ke_khai_trang_thai", "trang_thai"),
        Index("idx_ke_khai_phe_duyet", "nguoi_phe_duyet_id"),
        Index("idx_ke_khai_cc_thang_nam", "cong_chuc_id", "thang", "nam"),
        Index("idx_ke_khai_don_vi_snapshot", "don_vi_id_snapshot", "thang", "nam"),
        Index("idx_kekhai_version", "version_kekhai", "thang", "nam"),
    )
    
    def __repr__(self) -> str:
        loi_info = ""
        if self.so_loi_chat_luong or self.so_loi_tien_do:
            loi_info = f", loi_cl={self.so_loi_chat_luong}, loi_td={self.so_loi_tien_do}"
        return (
            f"<KeKhaiCongViec(id={self.id}, "
            f"cc_id={self.cong_chuc_id}, "
            f"thang={self.thang}/{self.nam}, "
            f"trang_thai={self.trang_thai.value}{loi_info})>"
        )


class PheDuyetSp(BaseModel):
    """
    Lịch sử phê duyệt sản phẩm.
    
    Mỗi lần phê duyệt/từ chối/yêu cầu sửa đều tạo 1 record.
    Ghi nhận:
    - Ai phê duyệt
    - Kết quả (phê duyệt/từ chối/yêu cầu sửa)
    - Số lần lỗi chất lượng/tiến độ (nếu có)
    - Ghi chú, lý do
    
    Relationships:
    - ke_khai: Bản kê khai được phê duyệt
    - nguoi_phe_duyet: Người thực hiện phê duyệt
    """
    
    __tablename__ = "phe_duyet_sp"
    
    # -------------------------------------------------------------------------
    # FOREIGN KEYS
    # -------------------------------------------------------------------------
    
    ke_khai_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ke_khai_cong_viec.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID bản kê khai"
    )
    
    nguoi_phe_duyet_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="ID người phê duyệt"
    )
    
    # -------------------------------------------------------------------------
    # KẾT QUẢ PHÊ DUYỆT
    # -------------------------------------------------------------------------
    
    trang_thai: Mapped[TrangThaiPheDuyet] = mapped_column(
        SQLEnum(TrangThaiPheDuyet, name="trang_thai_phe_duyet_enum", create_type=True),
        nullable=False,
        comment="Kết quả phê duyệt"
    )
    
    # -------------------------------------------------------------------------
    # ĐÁNH GIÁ CHẤT LƯỢNG & TIẾN ĐỘ
    # -------------------------------------------------------------------------
    
    lan_loi_chat_luong: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        comment="Số lần lỗi chất lượng"
    )
    
    lan_loi_tien_do: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        comment="Số lần lỗi tiến độ"
    )
    
    # -------------------------------------------------------------------------
    # GHI CHÚ
    # -------------------------------------------------------------------------
    
    ghi_chu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Ghi chú của người phê duyệt"
    )
    
    ly_do_tu_choi: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Lý do từ chối (nếu từ chối)"
    )
    
    # -------------------------------------------------------------------------
    # THỜI GIAN
    # -------------------------------------------------------------------------
    
    ngay_phe_duyet: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Thời điểm phê duyệt"
    )
    
    # -------------------------------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------------------------------
    
    # Bản kê khai
    ke_khai: Mapped["KeKhaiCongViec"] = relationship(
        "KeKhaiCongViec",
        back_populates="phe_duyets",
        lazy="joined"
    )
    
    # Người phê duyệt
    nguoi_phe_duyet: Mapped["CongChuc"] = relationship(
        "CongChuc",
        lazy="joined"
    )
    
    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------
    __table_args__ = (
        CheckConstraint("lan_loi_chat_luong >= 0", name="ck_phe_duyet_loi_cl"),
        CheckConstraint("lan_loi_tien_do >= 0", name="ck_phe_duyet_loi_td"),
        Index("idx_phe_duyet_ke_khai", "ke_khai_id"),
        Index("idx_phe_duyet_nguoi", "nguoi_phe_duyet_id"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<PheDuyetSp(id={self.id}, "
            f"ke_khai_id={self.ke_khai_id}, "
            f"trang_thai={self.trang_thai.value})>"
        )