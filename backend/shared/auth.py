"""
shared/auth.py
==============
Decode JWT dùng chung cho tất cả service.
Sử dụng cùng SECRET_KEY với KPI backend (port 8000).

Backward compatible: KPI gui "role" (cu) + "vai_tro" (moi).
"""

from typing import Optional

from jose import jwt, JWTError
from pydantic import BaseModel


class TokenPayload(BaseModel):
    """JWT payload structure — tuong thich voi ca KPI cu va moi."""
    sub: str  # cong_chuc_id (UUID string)
    ma_cc: Optional[str] = None
    ho_ten: Optional[str] = None

    # KPI gui ca "role" (cu) va "vai_tro" (moi) — cung gia tri
    vai_tro: Optional[str] = None
    role: Optional[str] = None

    don_vi_id: Optional[str] = None
    is_lanh_dao: bool = False
    is_admin: bool = False
    can_view_all_units: bool = False
    platform_roles: list[str] = []
    exp: Optional[int] = None
    type: str = "access"


def decode_jwt(
    token: str,
    secret_key: str,
    algorithm: str = "HS256",
) -> Optional[TokenPayload]:
    """
    Decode va verify JWT token.
    Normalize: vai_tro luon co gia tri dung (tu "vai_tro" hoac fallback "role").
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        token_data = TokenPayload(**payload)

        # Normalize: neu vai_tro rong thi lay tu role (backward compatible)
        if not token_data.vai_tro and token_data.role:
            token_data.vai_tro = token_data.role

        # Normalize: is_admin = SUPER_ADMIN
        if token_data.is_admin and not token_data.vai_tro:
            token_data.vai_tro = "SUPER_ADMIN"

        return token_data
    except JWTError:
        return None
