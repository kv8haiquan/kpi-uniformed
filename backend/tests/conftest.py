"""
tests/conftest.py
=================
Shared pytest fixtures cho tất cả test suites.

QUAN TRỌNG: pytest-asyncio mặc định tạo event loop mới cho mỗi test.
Nhưng `app.db.session.engine` (dùng asyncpg) cache connections trong loop hiện tại.
Khi test sau dùng loop mới, connection cũ bị "another operation in progress".

Giải pháp: dispose engine giữa các test để force tạo connection mới.
"""

import pytest_asyncio

from app.db.session import engine


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    """Dispose engine sau mỗi test để tránh connection-reuse conflict giữa event loops."""
    yield
    await engine.dispose()
