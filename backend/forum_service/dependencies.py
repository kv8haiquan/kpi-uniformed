"""
forum_service/dependencies.py
==============================
Dependencies: JWT auth, platform role check, database session.
"""

import sys
import os
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

# Them backend/ vao sys.path de import shared
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.auth import decode_jwt, TokenPayload
from shared.database import create_db_engine, create_session_factory, get_db_session
from forum_service.config import settings


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
    """
    Decode JWT va tra ve thong tin user.
    Khong query database — chi doc tu token payload.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "success": False,
            "error": {
                "code": "AUTH_001",
                "message": "Token khong hop le hoac da het han",
            },
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_jwt(token, settings.secret_key, settings.algorithm)
    if payload is None:
        raise credentials_exception

    if payload.type != "access":
        raise credentials_exception

    return payload


CurrentUserDep = Annotated[TokenPayload, Depends(get_current_user)]


def require_platform_role(*allowed_roles: str):
    """
    Factory tao dependency kiem tra platform role.

    Usage:
        @router.get("/admin")
        async def admin_only(user = Depends(require_platform_role("QT_DAO_TAO"))):
            ...
    """
    async def role_checker(current_user: CurrentUserDep) -> TokenPayload:
        user_roles = set(current_user.platform_roles or [])
        required_roles = set(allowed_roles)

        if not user_roles.intersection(required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_001",
                        "message": f"Yeu cau vai tro: {', '.join(allowed_roles)}",
                    },
                },
            )
        return current_user

    return role_checker
