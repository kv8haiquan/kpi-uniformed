"""
app/api/v1/endpoints/auth.py
============================
API Endpoints cho Authentication.

Endpoints:
- POST /login: Đăng nhập với username/password, trả về JWT token
- POST /logout: (Optional) Đánh dấu logout
- GET /me: Lấy thông tin user hiện tại
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import (
    DatabaseDep,
    ActiveUserDep,
    get_current_active_user,
)
from pydantic import BaseModel, Field

from app.core.security import verify_password, hash_password, create_access_token
from app.models.user_org import CongChuc
from app.schemas.token import Token


router = APIRouter()


# =============================================================================
# LOGIN ENDPOINT
# =============================================================================

@router.post(
    "/login",
    response_model=Token,
    summary="Đăng nhập hệ thống",
    description="""
    Đăng nhập với username và password để lấy JWT access token.
    
    - **Username**: Mã công chức (VD: 20ZZ-0224) hoặc 'admin'
    - **Password**: Mật khẩu (mặc định: 123456)
    
    Token có hiệu lực trong 8 tiếng (480 phút).
    """,
    responses={
        200: {
            "description": "Đăng nhập thành công",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIs...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {
            "description": "Sai username hoặc password",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "AUTH_003",
                            "message": "Sai tên đăng nhập hoặc mật khẩu"
                        }
                    }
                }
            }
        },
        403: {
            "description": "Tài khoản bị khóa",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "AUTH_004",
                            "message": "Tài khoản đã bị khóa"
                        }
                    }
                }
            }
        }
    }
)
async def login_access_token(
    db: DatabaseDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """
    Xác thực user và trả về JWT access token.
    
    **Quy trình:**
    1. Tìm user theo username (hỗ trợ cả ma_cc và username)
    2. Verify password
    3. Kiểm tra is_active
    4. Tạo JWT token với claims: sub (user_id), role, is_admin
    5. Cập nhật last_login
    6. Trả về token
    
    **Lưu ý:**
    - Super Admin (is_system_admin=True) đăng nhập bình thường
    - Admin không tham gia nghiệp vụ, chỉ quản trị hệ thống
    """
    # Chuẩn hóa username về lowercase để hỗ trợ đăng nhập không phân biệt hoa/thường
    # VD: "20zz-0224", "20Zz-0224", "20ZZ-0224" đều hợp lệ
    input_username = form_data.username.strip().lower()
    
    # Tìm user theo username hoặc ma_cc (case-insensitive)
    stmt = (
        select(CongChuc)
        .options(
            selectinload(CongChuc.vai_tro),
            selectinload(CongChuc.don_vi),
        )
        .where(
            # Tìm theo username HOẶC ma_cc, không phân biệt hoa/thường
            ((func.lower(CongChuc.username) == input_username) | 
             (func.lower(CongChuc.ma_cc) == input_username))
        )
        .where(CongChuc.is_deleted == False)
    )
    
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    # Kiểm tra user tồn tại
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_003",
                    "message": "Sai tên đăng nhập hoặc mật khẩu"
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Kiểm tra password
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_003",
                    "message": "Tài khoản chưa được thiết lập mật khẩu"
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_003",
                    "message": "Sai tên đăng nhập hoặc mật khẩu"
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Kiểm tra tài khoản bị khóa
    if not user.is_active:
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
    
    # Chuẩn bị claims bổ sung cho token
    additional_claims = {}
    
    # Thêm role nếu có
    if user.vai_tro:
        additional_claims["role"] = user.vai_tro.ma_vai_tro
    
    # Đánh dấu Super Admin
    is_admin = getattr(user, 'is_system_admin', False)
    if user.vai_tro and getattr(user.vai_tro, 'is_system_admin', False):
        is_admin = True
    additional_claims["is_admin"] = is_admin
    
    # Thêm thông tin bổ sung
    additional_claims["ma_cc"] = user.ma_cc
    additional_claims["ho_ten"] = user.ho_ten
    if user.don_vi:
        additional_claims["don_vi_id"] = str(user.don_vi.id)
    # THÊM NGAY BÊN DƯỚI:
    # v1.1.0 - Flag xem toàn chi cục
    additional_claims["can_view_all_units"] = getattr(user, 'can_view_all_units', False) or False

    # --- MO RONG PLATFORM (3 fields moi) ---
    # vai_tro: alias cho "role" — LMS doc field nay (backward compatible, "role" van giu)
    if user.vai_tro:
        additional_claims["vai_tro"] = user.vai_tro.ma_vai_tro
    # is_lanh_dao: flag lanh dao
    additional_claims["is_lanh_dao"] = getattr(user, 'is_lanh_dao', False) or False
    # platform_roles: query tu bang cong_chuc_platform_role
    try:
        from sqlalchemy import text as sa_text
        pr_result = await db.execute(sa_text(
            "SELECT pr.ma_role FROM public.platform_role pr "
            "JOIN public.cong_chuc_platform_role ccpr ON pr.id = ccpr.platform_role_id "
            "WHERE ccpr.cong_chuc_id = :uid AND ccpr.is_active = true AND pr.is_active = true"
        ), {"uid": str(user.id)})
        additional_claims["platform_roles"] = [r[0] for r in pr_result.fetchall()]
    except Exception:
        additional_claims["platform_roles"] = []

    # Tạo access token
    access_token = create_access_token(
        subject=str(user.id),
        additional_claims=additional_claims,
    )
    
    # Cập nhật last_login (non-blocking)
    try:
        stmt_update = (
            update(CongChuc)
            .where(CongChuc.id == user.id)
            .values(last_login=datetime.now(timezone.utc))
        )
        await db.execute(stmt_update)
        # Commit sẽ được xử lý bởi dependency get_db
    except Exception:
        # Không raise lỗi nếu update last_login thất bại
        # Log lỗi trong production
        pass
    
    return Token(
        access_token=access_token,
        token_type="bearer",
    )


# =============================================================================
# GET CURRENT USER INFO
# =============================================================================

@router.get(
    "/me",
    summary="Lấy thông tin user hiện tại",
    description="Trả về thông tin chi tiết của user đang đăng nhập",
    responses={
        200: {
            "description": "Thông tin user",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "ma_cc": "20ZZ-0224",
                            "ho_ten": "Nguyễn Văn A",
                            "email": "nva@customs.gov.vn",
                            "don_vi": {
                                "id": "...",
                                "ten_don_vi": "Đội Nghiệp vụ 1"
                            },
                            "vai_tro": {
                                "ma_vai_tro": "CC",
                                "ten_vai_tro": "Công chức"
                            },
                            "is_lanh_dao": False,
                            "is_system_admin": False
                        }
                    }
                }
            }
        },
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"}
    }
)
async def get_current_user_info(
    current_user: ActiveUserDep,
) -> dict[str, Any]:
    """
    Lấy thông tin chi tiết của user hiện tại.
    
    **Response bao gồm:**
    - Thông tin cá nhân (mã CC, họ tên, email, SĐT)
    - Đơn vị công tác
    - Vai trò trong hệ thống
    - Cờ is_lanh_dao, is_system_admin
    """
    # Chuẩn bị response data
    user_data = {
        "id": str(current_user.id),
        "ma_cc": current_user.ma_cc,
        "ho_ten": current_user.ho_ten,
        "email": current_user.email,
        "so_dien_thoai": current_user.so_dien_thoai,
        "ngay_sinh": current_user.ngay_sinh.isoformat() if current_user.ngay_sinh else None,
        "gioi_tinh": current_user.gioi_tinh.value if current_user.gioi_tinh else None,
        "chuc_vu": current_user.chuc_vu,
        "is_lanh_dao": current_user.is_lanh_dao,
        "is_system_admin": getattr(current_user, 'is_system_admin', False),
        "can_view_all_units": getattr(current_user, 'can_view_all_units', False) or False,
        "is_active": current_user.is_active,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
    }
    
    # Thêm thông tin đơn vị
    if current_user.don_vi:
        user_data["don_vi"] = {
            "id": str(current_user.don_vi.id),
            "ma_don_vi": current_user.don_vi.ma_don_vi,
            "ten_don_vi": current_user.don_vi.ten_don_vi,
            "loai_don_vi": current_user.don_vi.loai_don_vi.value if current_user.don_vi.loai_don_vi else None,
        }
    else:
        user_data["don_vi"] = None
    
    # Thêm thông tin vai trò
    if current_user.vai_tro:
        user_data["vai_tro"] = {
            "id": str(current_user.vai_tro.id),
            "ma_vai_tro": current_user.vai_tro.ma_vai_tro,
            "ten_vai_tro": current_user.vai_tro.ten_vai_tro,
            "cap_bac": current_user.vai_tro.cap_bac.value if current_user.vai_tro.cap_bac else None,
        }
        # Cập nhật is_system_admin từ vai_tro
        if getattr(current_user.vai_tro, 'is_system_admin', False):
            user_data["is_system_admin"] = True
    else:
        user_data["vai_tro"] = None
    
    return {
        "success": True,
        "data": user_data,
    }


# =============================================================================
# CHANGE PASSWORD
# =============================================================================


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=100)


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: ActiveUserDep,
    db: DatabaseDep,
):
    """Đổi mật khẩu user hiện tại."""
    # Verify mật khẩu hiện tại
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu hiện tại không đúng",
        )

    # Hash mật khẩu mới và cập nhật
    current_user.password_hash = hash_password(body.new_password)
    db.add(current_user)
    await db.commit()

    return {"success": True, "message": "Đổi mật khẩu thành công"}


# =============================================================================
# UPDATE PROFILE (Email, Số điện thoại)
# =============================================================================


class UpdateProfileRequest(BaseModel):
    email: str | None = Field(None, max_length=100)
    so_dien_thoai: str | None = Field(None, max_length=20)


@router.put("/update-profile")
async def update_profile(
    body: UpdateProfileRequest,
    current_user: ActiveUserDep,
    db: DatabaseDep,
):
    """Cập nhật thông tin liên hệ (email, số điện thoại)."""
    if body.email is not None:
        current_user.email = body.email.strip() or None
    if body.so_dien_thoai is not None:
        current_user.so_dien_thoai = body.so_dien_thoai.strip() or None

    db.add(current_user)
    await db.commit()

    return {
        "success": True,
        "message": "Cập nhật thông tin thành công",
        "data": {
            "email": current_user.email,
            "so_dien_thoai": current_user.so_dien_thoai,
        },
    }