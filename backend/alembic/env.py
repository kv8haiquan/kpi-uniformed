"""
alembic/env.py
==============
Cấu hình môi trường cho Alembic migrations.

File này được Alembic gọi mỗi khi chạy migration command.
Nhiệm vụ chính:
1. Kết nối với database
2. Load tất cả models để Alembic nhận diện
3. Thực thi migration scripts

⚠️ LƯU Ý QUAN TRỌNG:
- Alembic chạy SYNC (không phải async)
- Phải dùng database_url_sync (postgresql://) thay vì database_url (postgresql+asyncpg://)
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# =============================================================================
# THÊM PROJECT ROOT VÀO SYS.PATH
# =============================================================================
# Đây là bước quan trọng để import được app.models và app.config
# Alembic chạy từ thư mục root, nên cần thêm path

# Lấy đường dẫn thư mục chứa alembic (parent của env.py)
ALEMBIC_DIR = Path(__file__).resolve().parent
# Lấy đường dẫn project root (parent của alembic/)
PROJECT_ROOT = ALEMBIC_DIR.parent

# Thêm vào sys.path nếu chưa có
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# IMPORT APP MODULES (SAU KHI THÊM PATH)
# =============================================================================

# Import Base từ models - PHẢI import để Alembic nhận diện tất cả tables
from app.models import Base  # noqa: E402

# Import settings để lấy database URL
from app.config import settings  # noqa: E402

# =============================================================================
# ALEMBIC CONFIG
# =============================================================================

# Đối tượng config từ alembic.ini
config = context.config

# Cấu hình logging từ alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData của Base - chứa thông tin tất cả tables
target_metadata = Base.metadata

# =============================================================================
# DATABASE URL
# =============================================================================

def get_database_url() -> str:
    """
    Lấy database URL từ settings.
    
    Alembic cần SYNC driver (postgresql://) không phải ASYNC (postgresql+asyncpg://).
    
    Returns:
        str: Database URL dạng postgresql://user:pass@host:port/db
    """
    # Sử dụng sync URL cho Alembic
    url = settings.database_url_sync
    
    # Log để debug (có thể comment khi production)
    print(f"[Alembic] Connecting to: {url.replace(settings.db_password, '****')}")
    
    return url


# Override sqlalchemy.url trong config với URL từ settings
config.set_main_option("sqlalchemy.url", get_database_url())


# =============================================================================
# OFFLINE MIGRATIONS
# =============================================================================

def run_migrations_offline() -> None:
    """
    Chạy migrations trong chế độ 'offline'.
    
    Trong chế độ này, Alembic không kết nối database thực.
    Thay vào đó, nó generate SQL scripts để chạy thủ công.
    
    Sử dụng khi:
    - Muốn review SQL trước khi apply
    - Không có quyền kết nối database từ máy dev
    - CI/CD pipeline cần generate SQL artifacts
    
    Command:
        alembic upgrade head --sql > migration.sql
    """
    url = config.get_main_option("sqlalchemy.url")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,  # Render giá trị trực tiếp thay vì bind params
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detect thay đổi column type
        compare_server_default=True,  # Detect thay đổi default value
    )

    with context.begin_transaction():
        context.run_migrations()


# =============================================================================
# ONLINE MIGRATIONS
# =============================================================================

def run_migrations_online() -> None:
    """
    Chạy migrations trong chế độ 'online'.
    
    Trong chế độ này, Alembic kết nối trực tiếp đến database
    và thực thi các migrations.
    
    Đây là chế độ mặc định khi chạy:
        alembic upgrade head
        alembic downgrade -1
    """
    # Tạo engine configuration
    configuration = config.get_section(config.config_ini_section)
    
    # Override URL từ settings (đảm bảo chắc chắn)
    configuration["sqlalchemy.url"] = get_database_url()
    
    # Tạo SQLAlchemy engine
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Không dùng connection pool cho migrations
    )

    # Kết nối và chạy migrations
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Detect thay đổi column type
            compare_server_default=True,  # Detect thay đổi default value
            include_schemas=True,  # Hỗ trợ multiple schemas
            # Các options cho autogenerate
            render_as_batch=True,  # Batch mode cho SQLite (không cần cho PostgreSQL)
        )

        with context.begin_transaction():
            context.run_migrations()


# =============================================================================
# MAIN - Chọn chế độ chạy
# =============================================================================

if context.is_offline_mode():
    print("[Alembic] Running in OFFLINE mode (generating SQL)")
    run_migrations_offline()
else:
    print("[Alembic] Running in ONLINE mode (connecting to database)")
    run_migrations_online()
