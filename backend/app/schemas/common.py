"""
app/schemas/common.py
=====================
Generic schemas dùng chung cho toàn bộ API.

Bao gồm:
- DataResponse[T]: Bọc kết quả trả về chuẩn
- PaginatedResponse[T]: Response có phân trang
- Pagination: Thông tin phân trang
- ErrorDetail: Chi tiết lỗi
"""

from typing import TypeVar, Generic, Optional, List, Any
from pydantic import BaseModel, Field


# Type variable cho Generic schemas
T = TypeVar("T")


# =============================================================================
# ERROR SCHEMAS
# =============================================================================

class ErrorDetail(BaseModel):
    """Chi tiết lỗi cho từng field (validation errors)."""
    field: str = Field(..., description="Tên field bị lỗi")
    message: str = Field(..., description="Mô tả lỗi")
    type: Optional[str] = Field(default=None, description="Loại lỗi")


class ErrorResponse(BaseModel):
    """Schema cho response lỗi."""
    code: str = Field(..., description="Mã lỗi", examples=["AUTH_001", "VAL_001"])
    message: str = Field(..., description="Mô tả lỗi")
    details: Optional[List[ErrorDetail]] = Field(
        default=None,
        description="Chi tiết lỗi (cho validation errors)"
    )


# =============================================================================
# SUCCESS RESPONSE SCHEMAS
# =============================================================================

class DataResponse(BaseModel, Generic[T]):
    """
    Generic response wrapper cho API thành công.
    
    Usage:
        return DataResponse[UserResponse](
            success=True,
            data=user_data,
            message="Thành công"
        )
    """
    success: bool = Field(default=True, description="Trạng thái thành công")
    data: T = Field(..., description="Dữ liệu trả về")
    message: Optional[str] = Field(default=None, description="Thông báo (optional)")


class DataListResponse(BaseModel, Generic[T]):
    """
    Generic response wrapper cho danh sách (không phân trang).
    
    Usage:
        return DataListResponse[DonViResponse](
            success=True,
            data=list_of_don_vi
        )
    """
    success: bool = Field(default=True, description="Trạng thái thành công")
    data: List[T] = Field(default_factory=list, description="Danh sách dữ liệu")
    message: Optional[str] = Field(default=None, description="Thông báo (optional)")


# =============================================================================
# PAGINATION SCHEMAS
# =============================================================================

class Pagination(BaseModel):
    """Thông tin phân trang."""
    page: int = Field(..., ge=1, description="Trang hiện tại (bắt đầu từ 1)")
    page_size: int = Field(..., ge=1, le=100, description="Số item mỗi trang")
    total_items: int = Field(..., ge=0, description="Tổng số item")
    total_pages: int = Field(..., ge=0, description="Tổng số trang")
    
    @classmethod
    def create(cls, page: int, page_size: int, total_items: int) -> "Pagination":
        """
        Factory method tạo Pagination object.
        Tự động tính total_pages.
        """
        total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0
        return cls(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic response wrapper cho danh sách có phân trang.
    
    Usage:
        return PaginatedResponse[CongChucResponse](
            success=True,
            data=list_of_cong_chuc,
            pagination=Pagination.create(page=1, page_size=20, total_items=548)
        )
    """
    success: bool = Field(default=True, description="Trạng thái thành công")
    data: List[T] = Field(default_factory=list, description="Danh sách dữ liệu")
    pagination: Pagination = Field(..., description="Thông tin phân trang")
    message: Optional[str] = Field(default=None, description="Thông báo (optional)")


# =============================================================================
# QUERY PARAMS SCHEMAS
# =============================================================================

class PaginationParams(BaseModel):
    """Schema cho query params phân trang."""
    page: int = Field(default=1, ge=1, description="Trang hiện tại")
    page_size: int = Field(default=20, ge=1, le=100, description="Số item mỗi trang")
    
    @property
    def offset(self) -> int:
        """Tính offset cho SQL query."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Alias cho page_size."""
        return self.page_size


class SortParams(BaseModel):
    """Schema cho query params sắp xếp."""
    sort_by: Optional[str] = Field(default=None, description="Field để sắp xếp")
    order: Optional[str] = Field(
        default="asc",
        pattern="^(asc|desc)$",
        description="Thứ tự sắp xếp: asc hoặc desc"
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def success_response(data: Any, message: Optional[str] = None) -> dict:
    """
    Helper function tạo response thành công.
    
    Usage:
        return success_response(data=user_data, message="Thành công")
    """
    response = {"success": True, "data": data}
    if message:
        response["message"] = message
    return response


def error_response(code: str, message: str, details: Optional[List[dict]] = None) -> dict:
    """
    Helper function tạo response lỗi.
    
    Usage:
        return error_response(
            code="AUTH_003",
            message="Sai tên đăng nhập hoặc mật khẩu"
        )
    """
    error = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"success": False, "error": error}
