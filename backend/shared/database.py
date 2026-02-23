"""
shared/database.py
==================
Database engine và session factory dùng chung.
Tất cả service dùng CÙNG database kpi_haiquan, mỗi module dùng schema riêng.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_db_engine(database_url: str, echo: bool = False):
    """Tạo async engine cho database."""
    return create_async_engine(
        database_url,
        echo=echo,
        future=True,
    )


def create_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    """Tạo async session factory."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def get_db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency tạo database session cho mỗi request.
    Dùng trong FastAPI Depends.
    """
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
