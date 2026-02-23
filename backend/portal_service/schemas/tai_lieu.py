"""
portal_service/schemas/tai_lieu.py
====================================
Schemas Pydantic cho tài liệu ECM (Electronic Content Management).

Versioning:
  - phien_ban = 1 khi tạo mới
  - Mỗi lần upload phiên bản mới: tạo record MỚI với phien_ban += 1
    và phien_ban_truoc_id trỏ về record cũ

Validation file:
  - PDF/DOCX/XLSX/PPTX ≤ 50 MB
  - IMAGE          ≤ 10 MB
  - ZIP            ≤ 100 MB
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-schemas nhúng trong response
# ---------------------------------------------------------------------------


class UserBriefTL(BaseModel):
    """Thông tin tóm tắt người dùng (cho tài liệu)."""

    id: uuid.UUID
    ma_cc: str
    ho_ten: str

    model_config = {"from_attributes": True}


class ThuMucBrief(BaseModel):
    """Thông tin tóm tắt thư mục (nhúng trong TaiLieuResponse)."""

    id: uuid.UUID
    ten: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------


class TaiLieuCreate(BaseModel):
    """Upload tài liệu mới vào thư viện ECM.

    file_url: URL file đã upload qua Common file API / MinIO.
    """

    ten_tai_lieu: str = Field(..., min_length=1, max_length=300, description="Tên tài liệu")
    mo_ta: Optional[str] = Field(None, description="Mô tả ngắn về tài liệu")
    thu_muc_id: Optional[uuid.UUID] = Field(None, description="UUID thư mục chứa tài liệu")
    file_url: str = Field(..., min_length=1, description="URL file trên MinIO / CDN")
    file_name: Optional[str] = Field(None, max_length=500, description="Tên file gốc")
    file_size_bytes: Optional[int] = Field(None, ge=0, description="Dung lượng file (bytes)")
    file_type: Optional[str] = Field(
        None, max_length=100, description="MIME type, VD: application/pdf"
    )
    tags: Optional[List[str]] = Field(None, description="Tags tự do, VD: ['2026', 'KPI']")
    quyen_truy_cap: Optional[str] = Field(
        "TAT_CA",
        description="Quyền truy cập: TAT_CA | LANH_DAO | DON_VI | CA_NHAN",
    )
    don_vi_ids: Optional[List[str]] = Field(
        None, description="Danh sách UUID đơn vị được phép xem"
    )


class TaiLieuUpdate(BaseModel):
    """Cập nhật metadata tài liệu.

    Lưu ý: KHÔNG cho sửa file_url — upload phiên bản mới thay thế.
    """

    ten_tai_lieu: Optional[str] = Field(None, min_length=1, max_length=300)
    mo_ta: Optional[str] = None
    tags: Optional[List[str]] = None
    quyen_truy_cap: Optional[str] = None
    don_vi_ids: Optional[List[str]] = None


class UploadPhienBanMoiRequest(BaseModel):
    """Request upload phiên bản mới của tài liệu hiện có."""

    file_url: str = Field(..., min_length=1, description="URL file mới trên MinIO / CDN")
    file_name: Optional[str] = Field(None, max_length=500)
    file_size_bytes: Optional[int] = Field(None, ge=0)
    file_type: Optional[str] = Field(None, max_length=100)
    mo_ta: Optional[str] = Field(None, description="Ghi chú cho phiên bản mới này")


# ---------------------------------------------------------------------------
# Output schemas
# ---------------------------------------------------------------------------


class TaiLieuVersionResponse(BaseModel):
    """Thông tin tóm tắt một phiên bản tài liệu (dùng cho lịch sử version)."""

    id: uuid.UUID
    phien_ban: int
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_type: Optional[str] = None
    mo_ta: Optional[str] = None
    created_at: Optional[datetime] = None
    nguoi_tai_len: Optional[UserBriefTL] = None

    model_config = {"from_attributes": True}


class TaiLieuResponse(BaseModel):
    """Response đầy đủ tài liệu kèm thư mục và người tải."""

    id: uuid.UUID
    ten_tai_lieu: str
    mo_ta: Optional[str] = None
    file_url: str
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_type: Optional[str] = None
    phien_ban: int
    phien_ban_truoc_id: Optional[uuid.UUID] = None
    tags: Optional[list] = None
    quyen_truy_cap: str
    don_vi_ids: Optional[list] = None
    is_deleted: bool
    created_at: Optional[datetime] = None

    # Nested objects
    thu_muc: Optional[ThuMucBrief] = None
    nguoi_tai_len: Optional[UserBriefTL] = None

    model_config = {"from_attributes": True}


class TaiLieuListResponse(BaseModel):
    """Response tóm tắt tài liệu (dùng cho danh sách)."""

    id: uuid.UUID
    ten_tai_lieu: str
    mo_ta: Optional[str] = None
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_type: Optional[str] = None
    phien_ban: int
    tags: Optional[list] = None
    quyen_truy_cap: str
    created_at: Optional[datetime] = None

    # Nested objects
    thu_muc: Optional[ThuMucBrief] = None
    nguoi_tai_len: Optional[UserBriefTL] = None

    model_config = {"from_attributes": True}
