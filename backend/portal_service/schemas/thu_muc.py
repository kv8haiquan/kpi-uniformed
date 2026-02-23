"""
portal_service/schemas/thu_muc.py
===================================
Schemas Pydantic cho thư mục tài liệu ECM.

Cấu trúc cây (tree):
  - parent_id = None → thư mục gốc
  - parent_id = uuid → thư mục con

Phân quyền truy cập:
  - TAT_CA      → mọi CBCC
  - LANH_DAO    → chỉ user.is_lanh_dao = True
  - DON_VI      → user.don_vi_id nằm trong don_vi_ids
  - CA_NHAN     → user.id == created_by
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------


class ThuMucCreate(BaseModel):
    """Tạo thư mục mới."""

    ten: str = Field(..., min_length=1, max_length=200, description="Tên thư mục")
    parent_id: Optional[uuid.UUID] = Field(
        None, description="UUID thư mục cha (None = thư mục gốc)"
    )
    thu_tu: Optional[int] = Field(0, ge=0, description="Thứ tự hiển thị (tăng dần)")
    quyen_truy_cap: Optional[str] = Field(
        "TAT_CA",
        description="Quyền truy cập: TAT_CA | LANH_DAO | DON_VI | CA_NHAN",
    )
    don_vi_ids: Optional[List[str]] = Field(
        None,
        description="Danh sách UUID đơn vị được phép xem (dùng khi quyen=DON_VI)",
    )


class ThuMucUpdate(BaseModel):
    """Cập nhật thư mục — tất cả field optional."""

    ten: Optional[str] = Field(None, min_length=1, max_length=200)
    parent_id: Optional[uuid.UUID] = None
    thu_tu: Optional[int] = Field(None, ge=0)
    quyen_truy_cap: Optional[str] = None
    don_vi_ids: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Output schemas
# ---------------------------------------------------------------------------


class ThuMucParentBrief(BaseModel):
    """Thông tin tóm tắt thư mục cha (nhúng trong ThuMucResponse)."""

    id: uuid.UUID
    ten: str

    model_config = {"from_attributes": True}


class ThuMucResponse(BaseModel):
    """Response đầy đủ thông tin thư mục."""

    id: uuid.UUID
    ten: str
    parent_id: Optional[uuid.UUID] = None
    thu_tu: int
    quyen_truy_cap: str
    don_vi_ids: Optional[list] = None
    created_by: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None

    # Thông tin cha (nếu có)
    parent: Optional[ThuMucParentBrief] = None

    # Số lượng (tính từ query riêng, không eager load)
    so_thu_muc_con: int = 0
    so_tai_lieu: int = 0

    model_config = {"from_attributes": True}


class ThuMucTreeResponse(BaseModel):
    """Response cấu trúc cây thư mục (nested, recursive)."""

    id: uuid.UUID
    ten: str
    thu_tu: int
    quyen_truy_cap: str
    children: List["ThuMucTreeResponse"] = []

    model_config = {"from_attributes": True}


# Cần gọi model_rebuild() sau khi định nghĩa class vì có self-reference
ThuMucTreeResponse.model_rebuild()
