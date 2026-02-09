"""
app/models/audit_log.py
=======================
Model cho Audit Log - ghi lại mọi thay đổi dữ liệu quan trọng.

Được trigger tự động bởi PostgreSQL trigger function khi:
- INSERT: Ghi nhận record mới
- UPDATE: Ghi nhận giá trị cũ và mới
- DELETE: Ghi nhận record bị xóa

Sử dụng cho:
- Truy vết ai sửa điểm/kết quả đánh giá
- Audit compliance
- Debug/troubleshooting
"""

import uuid
import enum
from datetime import datetime
from typing import Optional, Any

from sqlalchemy import (
    String, 
    Text, 
    DateTime,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base, UUIDPrimaryKeyMixin


class AuditAction(str, enum.Enum):
    """Loại hành động được ghi log."""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """
    Bảng ghi log audit cho tất cả các thay đổi quan trọng.
    
    Được tự động ghi bởi PostgreSQL triggers trên các bảng:
    - ke_khai_cong_viec
    - phe_duyet_sp
    - danh_gia_thang
    
    Fields:
    - table_name: Tên bảng bị thay đổi
    - record_id: ID của record bị thay đổi
    - action: INSERT/UPDATE/DELETE
    - old_value: Giá trị cũ (JSONB) - cho UPDATE/DELETE
    - new_value: Giá trị mới (JSONB) - cho INSERT/UPDATE
    - user_id: ID người thực hiện (từ session)
    - ip_address: IP address của request
    
    Không có relationships để tránh ảnh hưởng performance.
    """
    
    __tablename__ = "audit_log"
    
    # Thông tin bảng/record
    table_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Tên bảng bị thay đổi"
    )
    
    record_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="ID của record bị thay đổi"
    )
    
    # Loại hành động
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction, name="audit_action_enum", create_type=True),
        nullable=False,
        index=True,
        comment="Loại hành động: INSERT/UPDATE/DELETE"
    )
    
    # Giá trị cũ và mới (JSONB)
    old_value: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Giá trị cũ (cho UPDATE/DELETE)"
    )
    
    new_value: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Giá trị mới (cho INSERT/UPDATE)"
    )
    
    # Người thực hiện
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="ID người thực hiện (từ app.current_user_id)"
    )
    
    # Metadata
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="IP address của request"
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User agent của request"
    )
    
    # Thời gian
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Thời điểm thay đổi"
    )
    
    # -------------------------------------------------------------------------
    # INDEXES
    # -------------------------------------------------------------------------
    __table_args__ = (
        # Composite index cho truy vấn theo bảng + thời gian
        Index("idx_audit_table_time", "table_name", "created_at"),
        # Composite index cho truy vấn theo user + thời gian
        Index("idx_audit_user_time", "user_id", "created_at"),
        # Composite index cho truy vấn theo record
        Index("idx_audit_record", "table_name", "record_id"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, "
            f"table={self.table_name}, "
            f"action={self.action.value}, "
            f"record_id={self.record_id})>"
        )
    
    @classmethod
    def create_log(
        cls,
        table_name: str,
        record_id: uuid.UUID,
        action: AuditAction,
        user_id: Optional[uuid.UUID] = None,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> "AuditLog":
        """
        Factory method để tạo AuditLog record.
        
        Usage:
            log = AuditLog.create_log(
                table_name="ke_khai_cong_viec",
                record_id=ke_khai.id,
                action=AuditAction.UPDATE,
                user_id=current_user.id,
                old_value={"diem": 80},
                new_value={"diem": 85},
            )
            session.add(log)
        """
        return cls(
            table_name=table_name,
            record_id=record_id,
            action=action,
            user_id=user_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
        )
