"""
app/db/session.py
=================
Cấu hình SQLAlchemy Async Session Factory.

Sử dụng:
- AsyncSession cho tất cả database operations
- Context manager để tự động commit/rollback
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import settings


# =============================================================================
# ENGINE
# =============================================================================

# Tạo Async Engine với connection pool
# NullPool cho development (không cache connections)
# Trong production có thể dùng pool_size, max_overflow
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL queries khi debug=True
    future=True,
    poolclass=NullPool if settings.is_development else None,
    # Production settings:
    # pool_size=5,
    # max_overflow=10,
    # pool_pre_ping=True,
)


# =============================================================================
# SESSION FACTORY
# =============================================================================

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Không expire objects sau commit
    autocommit=False,
    autoflush=False,
)


# =============================================================================
# DEPENDENCY
# =============================================================================

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection cho FastAPI.
    Tạo session mới cho mỗi request, tự động close sau khi xử lý xong.
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_async_session)):
            ...
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
