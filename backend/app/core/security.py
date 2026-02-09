"""
app/core/security.py
====================
Xử lý bảo mật: Password hashing, JWT tokens.

Sử dụng:
- bcrypt để hash password (chậm, an toàn)
- python-jose để tạo/verify JWT tokens
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings


# =============================================================================
# PASSWORD HASHING
# =============================================================================

# CryptContext với bcrypt - chuẩn industry cho password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    # Tăng rounds để chậm hơn (an toàn hơn), mặc định là 12
    bcrypt__rounds=12,
)


def hash_password(password: str) -> str:
    """
    Hash password sử dụng bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password (60 characters)
        
    Example:
        >>> hashed = hash_password("123456")
        >>> # $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.S...
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Kiểm tra password có khớp với hash không.
    
    Args:
        plain_password: Password người dùng nhập
        hashed_password: Hash lưu trong database
        
    Returns:
        bool: True nếu khớp, False nếu không
        
    Example:
        >>> verify_password("123456", hashed)
        True
        >>> verify_password("wrong", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


# =============================================================================
# JWT TOKENS
# =============================================================================

def create_access_token(
    subject: str | Any,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict] = None,
) -> str:
    """
    Tạo JWT access token.
    
    Args:
        subject: Thường là user_id hoặc username
        expires_delta: Thời gian hết hạn (mặc định từ settings)
        additional_claims: Các claims bổ sung (role, permissions, ...)
        
    Returns:
        str: JWT token string
        
    Example:
        >>> token = create_access_token(
        ...     subject=str(user.id),
        ...     additional_claims={"role": "CCT"}
        ... )
    """
    # Thời gian hết hạn
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    # Payload chuẩn JWT
    to_encode = {
        "sub": str(subject),  # Subject (user identifier)
        "exp": expire,         # Expiration time
        "iat": datetime.now(timezone.utc),  # Issued at
        "type": "access",      # Token type
    }
    
    # Thêm claims bổ sung
    if additional_claims:
        to_encode.update(additional_claims)
    
    # Encode token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Giải mã và verify JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        dict: Payload nếu token hợp lệ
        None: Nếu token không hợp lệ hoặc hết hạn
        
    Example:
        >>> payload = decode_access_token(token)
        >>> if payload:
        ...     user_id = payload.get("sub")
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return payload
    except JWTError:
        return None


def create_refresh_token(
    subject: str | Any,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Tạo JWT refresh token (dùng để lấy access token mới).
    
    Refresh token có thời hạn dài hơn access token.
    
    Args:
        subject: User identifier
        expires_delta: Thời gian hết hạn (mặc định 7 ngày)
        
    Returns:
        str: Refresh token string
    """
    if expires_delta is None:
        expires_delta = timedelta(days=7)
    
    expire = datetime.now(timezone.utc) + expires_delta
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",  # Đánh dấu là refresh token
    }
    
    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


# =============================================================================
# HELPER CONSTANTS
# =============================================================================

# Password mặc định cho seed data
DEFAULT_PASSWORD = "123456"
DEFAULT_PASSWORD_HASH = hash_password(DEFAULT_PASSWORD)
