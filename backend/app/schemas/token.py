"""
app/schemas/token.py
====================
Pydantic schemas cho JWT Authentication.

Định nghĩa cấu trúc dữ liệu cho:
- Token response sau khi đăng nhập
- Token payload (decoded từ JWT)
"""

from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    """
    Schema response khi đăng nhập thành công.
    
    Attributes:
        access_token: JWT access token string
        token_type: Loại token, mặc định "bearer"
    """
    access_token: str = Field(
        ...,
        description="JWT access token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    token_type: str = Field(
        default="bearer",
        description="Loại token (bearer)",
        examples=["bearer"]
    )


class TokenPayload(BaseModel):
    """
    Schema cho nội dung payload sau khi decode JWT token.
    
    Attributes:
        sub: Subject - thường là user_id (UUID string)
        exp: Expiration time (Unix timestamp)
        iat: Issued at time (Unix timestamp)
        type: Loại token ("access" hoặc "refresh")
        role: Mã vai trò của user (optional)
        is_admin: Cờ đánh dấu Super Admin (optional)
    """
    sub: str = Field(
        ...,
        description="User ID (UUID string)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    exp: Optional[int] = Field(
        default=None,
        description="Thời điểm hết hạn (Unix timestamp)"
    )
    iat: Optional[int] = Field(
        default=None,
        description="Thời điểm phát hành (Unix timestamp)"
    )
    type: Optional[str] = Field(
        default="access",
        description="Loại token",
        examples=["access", "refresh"]
    )
    # Claims bổ sung cho ứng dụng
    role: Optional[str] = Field(
        default=None,
        description="Mã vai trò (CCT, PCCT, TDV, PDV, CC, ADMIN)",
        examples=["CC", "TDV", "CCT"]
    )
    is_admin: Optional[bool] = Field(
        default=False,
        description="Cờ đánh dấu Super Admin"
    )


class TokenData(BaseModel):
    """
    Schema đơn giản hóa để truyền dữ liệu token giữa các layer.
    Sử dụng trong dependency get_current_user.
    
    Attributes:
        user_id: UUID của user (string format)
        username: Tên đăng nhập (optional)
    """
    user_id: Optional[str] = Field(
        default=None,
        description="User ID từ token payload (sub)"
    )
    username: Optional[str] = Field(
        default=None,
        description="Username nếu có trong token"
    )
