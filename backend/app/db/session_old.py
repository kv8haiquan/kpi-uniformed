"""
app/db/session.py
=================
Cấu hình database connection và session factory cho async operations.

Sử dụng:
- AsyncSession cho FastAPI endpoints
- Dependency injection với FastAPI Depends()

Lưu ý:
- Alembic dùng SYNC connection (trong env.py)
- App dùng ASYNC connection (file này)
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from app.config import settings


# =============================================================================
# ASYNC ENGINE
# =============================================================================

def create_engine() -> AsyncEngine:
    """
    Tạo SQLAlchemy async engine.
    
    Returns:
        AsyncEngine: Engine để kết nối PostgreSQL qua asyncpg
    """
    return create_async_engine(
        settings.database_url,  # postgresql+asyncpg://...
        echo=settings.debug,    # Log SQL queries khi debug=True
        future=True,            # Sử dụng SQLAlchemy 2.0 style
        pool_pre_ping=True,     # Kiểm tra connection trước khi sử dụng
        # Pool settings cho production
        pool_size=5,            # Số connections trong pool
        max_overflow=10,        # Số connections tối đa vượt pool
        pool_recycle=3600,      # Recycle connection sau 1 giờ
    )


# Tạo engine instance
engine = create_engine()


# =============================================================================
# ASYNC SESSION FACTORY
# =============================================================================

# Session factory - tạo session mới cho mỗi request
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Không expire objects sau commit (cần cho async)
    autocommit=False,        # Không tự động commit
    autoflush=False,         # Không tự động flush (flush thủ công khi cần)
)


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency để inject database session vào FastAPI endpoints.
    
    Tự động:
    - Tạo session mới cho mỗi request
    - Đóng session sau khi request hoàn thành
    - Rollback nếu có exception
    
    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    
    Yields:
        AsyncSession: Database session cho request hiện tại
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Commit nếu không có lỗi
        except Exception:
            await session.rollback()  # Rollback nếu có lỗi
            raise
        finally:
            await session.close()  # Đảm bảo đóng session


async def get_db_no_commit() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency cho các operations chỉ đọc (không cần commit).
    
    Yields:
        AsyncSession: Database session (read-only pattern)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

async def init_db() -> None:
    """
    Khởi tạo database connection.
    Gọi khi startup FastAPI app.
    
    Usage trong main.py:
        @app.on_event("startup")
        async def startup():
            await init_db()
    """
    # Test connection
    async with engine.begin() as conn:
        # Chạy raw SQL để test
        await conn.execute("SELECT 1")
    
    print("[Database] Connection established successfully")


async def close_db() -> None:
    """
    Đóng tất cả database connections.
    Gọi khi shutdown FastAPI app.
    
    Usage trong main.py:
        @app.on_event("shutdown")
        async def shutdown():
            await close_db()
    """
    await engine.dispose()
    print("[Database] All connections closed")
