"""
app/models/base.py
==================
Base model cho tất cả SQLAlchemy models.
Sử dụng SQLAlchemy 2.0+ style với AsyncAttrs để hỗ trợ async operations.

Các tính năng:
- UUID làm Primary Key mặc định
- Tự động quản lý created_at, updated_at
- Soft delete pattern với is_deleted
- Audit fields: created_by, updated_by
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Boolean, UUID as SA_UUID, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    declared_attr,
)


class Base(AsyncAttrs, DeclarativeBase):
    """
    Base class cho tất cả models trong hệ thống.
    
    Kế thừa:
    - AsyncAttrs: Hỗ trợ lazy loading trong async context
    - DeclarativeBase: SQLAlchemy 2.0 declarative base
    
    Usage:
        class MyModel(Base):
            __tablename__ = "my_table"
            # ... columns
    """
    
    # Cho phép sử dụng type annotation trong relationships
    # mà không cần quotes
    __abstract__ = True
    
    # Quy ước đặt tên cho constraints và indexes
    # Giúp Alembic tự động tạo tên có ý nghĩa
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Tự động tạo tên bảng từ tên class (snake_case).
        VD: CongChuc -> cong_chuc
        """
        import re
        name = cls.__name__
        # Convert CamelCase to snake_case
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


class TimestampMixin:
    """
    Mixin cung cấp các trường timestamp tự động.
    Sử dụng server_default để PostgreSQL tự set giá trị.
    """
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Thời gian tạo record"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Thời gian cập nhật cuối"
    )


class SoftDeleteMixin:
    """
    Mixin cho soft delete pattern.
    Thay vì xóa vật lý, chỉ đánh dấu is_deleted = True.
    """
    
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        index=True,
        comment="Đánh dấu đã xóa (soft delete)"
    )


class AuditMixin:
    """
    Mixin cho audit trail - theo dõi ai tạo/sửa record.
    """
    
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        SA_UUID(as_uuid=True),
        nullable=True,
        comment="ID người tạo record"
    )
    
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        SA_UUID(as_uuid=True),
        nullable=True,
        comment="ID người cập nhật cuối"
    )


class UUIDPrimaryKeyMixin:
    """
    Mixin cung cấp UUID làm Primary Key.
    Sử dụng gen_random_uuid() của PostgreSQL để tạo UUID.
    """
    
    id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Primary Key (UUID)"
    )


class BaseModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Base model tiêu chuẩn với:
    - UUID Primary Key
    - Timestamps (created_at, updated_at)
    
    Sử dụng cho các bảng không cần soft delete.
    
    Usage:
        class MyTable(BaseModel):
            __tablename__ = "my_table"
            name: Mapped[str] = mapped_column(String(100))
    """
    __abstract__ = True


class BaseModelWithSoftDelete(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """
    Base model với soft delete:
    - UUID Primary Key
    - Timestamps (created_at, updated_at)
    - Soft delete (is_deleted)
    
    Sử dụng cho các bảng quan trọng cần giữ lại lịch sử.
    
    Usage:
        class CongChuc(BaseModelWithSoftDelete):
            __tablename__ = "cong_chuc"
            ho_ten: Mapped[str] = mapped_column(String(100))
    """
    __abstract__ = True


class BaseModelFull(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    Base model đầy đủ với:
    - UUID Primary Key
    - Timestamps (created_at, updated_at)
    - Soft delete (is_deleted)
    - Audit fields (created_by, updated_by)
    
    Sử dụng cho các bảng cần audit trail đầy đủ.
    
    Usage:
        class KeKhaiCongViec(BaseModelFull):
            __tablename__ = "ke_khai_cong_viec"
            # ...
    """
    __abstract__ = True
