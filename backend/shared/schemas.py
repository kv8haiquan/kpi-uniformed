"""
shared/schemas.py
=================
Base response schemas dùng chung cho tất cả service.
Tương ứng với format chuẩn trong CLAUDE.md.
"""

from typing import Generic, TypeVar, Optional, List

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Response thành công với data."""
    success: bool = True
    data: T
    message: Optional[str] = "Thao tác thành công"


class PaginationInfo(BaseModel):
    """Thông tin phân trang."""
    page: int
    page_size: int
    total_items: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    """Response thành công có phân trang."""
    success: bool = True
    data: List[T]
    pagination: PaginationInfo
    message: Optional[str] = None


class ErrorDetail(BaseModel):
    """Chi tiết lỗi."""
    code: str
    message: str
    details: Optional[list] = None


class ErrorResponse(BaseModel):
    """Response lỗi."""
    success: bool = False
    error: ErrorDetail
