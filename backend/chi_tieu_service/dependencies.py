"""
chi_tieu_service/dependencies.py
================================
Dependencies: JWT auth, platform role check, database session.
Cung co che voi cac service khac (lms, forum...).
"""

import sys
import os
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Them backend/ vao sys.path de import shared
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.auth import decode_jwt, TokenPayload
from shared.database import create_db_engine, create_session_factory, get_db_session
from chi_tieu_service.config import settings


# OAuth2 scheme — tro ve KPI login endpoint
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="http://localhost:8000/api/v1/auth/login"
)

# Database engine va session factory
engine = create_db_engine(settings.database_url)
session_factory = create_session_factory(engine)


async def get_db():
    """Dependency tao database session."""
    async for session in get_db_session(session_factory):
        yield session


DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TokenPayload:
    """Decode JWT va tra ve thong tin user (khong query DB)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "success": False,
            "error": {"code": "AUTH_001", "message": "Token khong hop le hoac da het han"},
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_jwt(token, settings.secret_key, settings.algorithm)
    if payload is None or payload.type != "access":
        raise credentials_exception
    return payload


CurrentUserDep = Annotated[TokenPayload, Depends(get_current_user)]


def require_platform_role(*allowed_roles: str):
    """Factory tao dependency kiem tra platform role."""

    async def role_checker(current_user: CurrentUserDep) -> TokenPayload:
        # SUPER_ADMIN luon bypass
        if current_user.vai_tro == "SUPER_ADMIN" or current_user.is_admin:
            return current_user

        user_roles = set(current_user.platform_roles or [])
        if not user_roles.intersection(set(allowed_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {"code": "PERM_001", "message": f"Yeu cau vai tro: {', '.join(allowed_roles)}"},
                },
            )
        return current_user

    return role_checker


async def get_pham_vi_don_vi_ids(
    db: AsyncSession, cong_chuc_id: str, ma_role: str
) -> list[str]:
    """
    Doc pham_vi.don_vi_ids cua 1 cong chuc cho 1 platform_role cu the.
    Tra ve list UUID string cac don vi nguoi do duoc gan theo doi.

    JWT chi mang platform_roles (list ma role), KHONG mang pham_vi —
    nen phai query public.cong_chuc_platform_role de lay don_vi_ids.
    """
    stmt = text("""
        SELECT cpr.pham_vi
        FROM public.cong_chuc_platform_role cpr
        JOIN public.platform_role pr ON pr.id = cpr.platform_role_id
        WHERE cpr.cong_chuc_id = :cc_id
          AND pr.ma_role = :ma_role
          AND cpr.is_active = TRUE
    """)
    rows = (await db.execute(stmt, {"cc_id": cong_chuc_id, "ma_role": ma_role})).fetchall()

    don_vi_ids: set[str] = set()
    for (pham_vi,) in rows:
        if isinstance(pham_vi, dict):
            for dv in pham_vi.get("don_vi_ids", []) or []:
                don_vi_ids.add(str(dv))
    return list(don_vi_ids)
