"""
app/api/deps.py
===============
FastAPI Dependencies cho Authentication và Database.

Dependencies:
- get_db: Yield AsyncSession cho mỗi request
- get_current_user: Xác thực JWT và trả về CongChuc object
- get_current_active_user: Kiểm tra thêm is_active
- get_current_admin: Kiểm tra quyền Super Admin
"""

from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.models.user_org import CongChuc, VaiTro, DonVi
from app.schemas.token import TokenPayload


# =============================================================================
# OAUTH2 SCHEME
# =============================================================================

# OAuth2 với Bearer token, endpoint login tại /api/v1/auth/login
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login"
)


# =============================================================================
# DATABASE DEPENDENCY
# =============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency tạo database session cho mỗi request.
    Tự động commit nếu thành công, rollback nếu có exception.
    
    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    
    Yields:
        AsyncSession: SQLAlchemy async session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Commit tự động sau khi request handler hoàn thành
            await session.commit()
        except Exception:
            # Rollback nếu có lỗi
            await session.rollback()
            raise
        finally:
            await session.close()


# Type alias cho dependency injection
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


# =============================================================================
# AUTHENTICATION DEPENDENCIES
# =============================================================================

async def get_current_user(
    db: DatabaseDep,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CongChuc:
    """
    Dependency xác thực JWT token và trả về user hiện tại.
    
    Quy trình:
    1. Decode JWT token
    2. Lấy user_id từ payload (sub)
    3. Query database lấy CongChuc với relationships
    4. Kiểm tra user tồn tại
    
    Args:
        db: Database session
        token: JWT Bearer token từ header
        
    Returns:
        CongChuc: Object user đầy đủ với don_vi và vai_tro
        
    Raises:
        HTTPException 401: Token không hợp lệ hoặc hết hạn
        HTTPException 404: User không tồn tại
        
    Usage:
        @router.get("/me")
        async def get_me(current_user: CongChuc = Depends(get_current_user)):
            return current_user
    """
    # Chuẩn bị exception cho các trường hợp lỗi
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "success": False,
            "error": {
                "code": "AUTH_001",
                "message": "Token không hợp lệ hoặc đã hết hạn"
            }
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode và validate token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # Lấy user_id từ payload
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Kiểm tra token type (phải là access token)
    token_type = payload.get("type", "access")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_001",
                    "message": "Token type không hợp lệ"
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Query user từ database với eager loading relationships
    stmt = (
        select(CongChuc)
        .options(
            selectinload(CongChuc.don_vi),  # Load đơn vị
            selectinload(CongChuc.vai_tro),  # Load vai trò
        )
        .where(CongChuc.id == user_id)
        .where(CongChuc.is_deleted == False)  # Không lấy user đã xóa
    )
    
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    # Kiểm tra user tồn tại
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Không tìm thấy người dùng"
                }
            },
        )
    
    return user


# Type alias
CurrentUserDep = Annotated[CongChuc, Depends(get_current_user)]


async def get_current_active_user(
    current_user: CurrentUserDep,
) -> CongChuc:
    """
    Dependency kiểm tra user đang active.
    Sử dụng sau get_current_user để đảm bảo tài khoản chưa bị khóa.
    
    Args:
        current_user: User từ get_current_user
        
    Returns:
        CongChuc: User đã xác thực và đang active
        
    Raises:
        HTTPException 403: Tài khoản bị khóa (is_active=False)
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_004",
                    "message": "Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên."
                }
            },
        )
    return current_user


# Type alias
ActiveUserDep = Annotated[CongChuc, Depends(get_current_active_user)]


async def get_current_admin(
    current_user: ActiveUserDep,
) -> CongChuc:
    """
    Dependency kiểm tra quyền Super Admin.
    Chỉ user có is_system_admin=True hoặc vai_tro.is_system_admin=True mới qua được.
    
    Args:
        current_user: User đã active từ get_current_active_user
        
    Returns:
        CongChuc: Super Admin user
        
    Raises:
        HTTPException 403: Không có quyền Admin
    """
    # Kiểm tra cờ is_system_admin trên CongChuc
    is_admin = getattr(current_user, 'is_system_admin', False)
    
    # Hoặc kiểm tra qua vai_tro nếu có
    if current_user.vai_tro:
        is_admin = is_admin or getattr(current_user.vai_tro, 'is_system_admin', False)
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "ADMIN_001",
                    "message": "Không có quyền Admin"
                }
            },
        )
    
    return current_user


# Type alias
AdminUserDep = Annotated[CongChuc, Depends(get_current_admin)]


# =============================================================================
# ROLE-BASED DEPENDENCIES
# =============================================================================

def require_roles(*allowed_roles: str):
    """
    Factory function tạo dependency kiểm tra vai trò.
    
    Args:
        *allowed_roles: Danh sách mã vai trò được phép (CCT, PCCT, TDV, PDV, CC)
        
    Returns:
        Dependency function
        
    Usage:
        @router.get("/approve")
        async def approve(
            user: CongChuc = Depends(require_roles("CCT", "PCCT", "TDV"))
        ):
            ...
    """
    async def role_checker(current_user: ActiveUserDep) -> CongChuc:
        # Super Admin luôn được phép
        if getattr(current_user, 'is_system_admin', False):
            return current_user
        
        # Kiểm tra vai trò
        if not current_user.vai_tro:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_001",
                        "message": "Không có quyền truy cập"
                    }
                },
            )
        
        user_role = current_user.vai_tro.ma_vai_tro
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_001",
                        "message": f"Chức năng này yêu cầu vai trò: {', '.join(allowed_roles)}"
                    }
                },
            )
        
        return current_user
    
    return role_checker


def require_leader():
    """
    Dependency kiểm tra user là lãnh đạo (is_lanh_dao=True).
    
    Returns:
        Dependency function
        
    Usage:
        @router.get("/approve-sp")
        async def approve_sp(user: CongChuc = Depends(require_leader())):
            ...
    """
    async def leader_checker(current_user: ActiveUserDep) -> CongChuc:
        # Super Admin không tham gia nghiệp vụ phê duyệt
        if getattr(current_user, 'is_system_admin', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_002",
                        "message": "Admin không tham gia quy trình phê duyệt"
                    }
                },
            )
        
        if not current_user.is_lanh_dao:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_002",
                        "message": "Chức năng này chỉ dành cho lãnh đạo"
                    }
                },
            )
        
        return current_user
    
    return leader_checker
