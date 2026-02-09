# CẤU TRÚC THƯ MỤC DỰ ÁN - BACKEND HẢI QUAN KV8

```
haiquan_kv8_backend/
│
├── alembic/                        # Database migrations
│   ├── versions/                   # Migration files
│   ├── env.py
│   └── alembic.ini
│
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI entry point
│   ├── config.py                   # Cấu hình môi trường (Settings)
│   │
│   ├── api/                        # API Routes (Controllers)
│   │   ├── __init__.py
│   │   ├── deps.py                 # Dependencies (get_db, get_current_user)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py           # Router tổng hợp
│   │       ├── auth.py             # API Đăng nhập/Logout
│   │       ├── users.py            # API Quản lý công chức
│   │       ├── don_vi.py           # API Đơn vị
│   │       ├── ke_khai.py          # API Kê khai công việc
│   │       ├── phe_duyet.py        # API Phê duyệt
│   │       └── danh_gia.py         # API Đánh giá tháng
│   │
│   ├── core/                       # Core utilities
│   │   ├── __init__.py
│   │   ├── security.py             # Hashing password, JWT
│   │   ├── exceptions.py           # Custom exceptions
│   │   └── constants.py            # Hằng số hệ thống
│   │
│   ├── models/                     # SQLAlchemy Models (ORM)
│   │   ├── __init__.py
│   │   ├── base.py                 # Base model với common fields
│   │   ├── don_vi.py               # Model đơn vị
│   │   ├── vai_tro.py              # Model vai trò
│   │   ├── cong_chuc.py            # Model công chức
│   │   ├── sp_cong_viec.py         # Model sản phẩm công việc chuẩn
│   │   ├── cap_do_phuc_tap.py      # Model cấp độ phức tạp
│   │   ├── danh_muc_sp.py          # Model danh mục SP công việc
│   │   ├── ke_khai.py              # Model kê khai công việc
│   │   ├── phe_duyet.py            # Model phê duyệt SP
│   │   ├── danh_gia_thang.py       # Model đánh giá tháng
│   │   └── audit_log.py            # Model audit log
│   │
│   ├── schemas/                    # Pydantic Schemas (DTO)
│   │   ├── __init__.py
│   │   ├── auth.py                 # Login/Token schemas
│   │   ├── user.py                 # User request/response
│   │   ├── don_vi.py
│   │   ├── ke_khai.py
│   │   ├── phe_duyet.py
│   │   └── danh_gia.py
│   │
│   ├── services/                   # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── auth_service.py         # Xử lý đăng nhập
│   │   ├── user_service.py         # Xử lý user CRUD
│   │   ├── ke_khai_service.py      # Logic kê khai
│   │   ├── phe_duyet_service.py    # Logic phê duyệt
│   │   ├── danh_gia_service.py     # Logic đánh giá
│   │   └── kpi_calculator.py       # Tính toán điểm KPI
│   │
│   ├── repositories/               # Data Access Layer
│   │   ├── __init__.py
│   │   ├── base.py                 # Base repository
│   │   ├── user_repo.py
│   │   ├── don_vi_repo.py
│   │   └── ke_khai_repo.py
│   │
│   └── db/                         # Database connection
│       ├── __init__.py
│       ├── session.py              # Async session factory
│       └── init_db.py              # Database initialization
│
├── scripts/                        # Utility scripts
│   ├── __init__.py
│   ├── seed_users.py               # Import công chức từ Excel
│   ├── seed_danh_muc_sp.py         # Import danh mục sản phẩm
│   └── generate_test_data.py       # Tạo dữ liệu test
│
├── tests/                          # Unit & Integration tests
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── test_auth.py
│   ├── test_ke_khai.py
│   └── test_kpi_calculator.py
│
├── data/                           # Thư mục chứa file Excel input
│   ├── danh_sach_cong_chuc.xlsx
│   └── danh_muc_san_pham.xlsx
│
├── .env.example                    # Template biến môi trường
├── .gitignore
├── requirements.txt                # Python dependencies
├── requirements-dev.txt            # Dev dependencies
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## NGUYÊN TẮC THIẾT KẾ

1. **Layered Architecture**: API → Service → Repository → Database
2. **Dependency Injection**: Sử dụng FastAPI Depends()
3. **Async First**: Tất cả DB operations đều async
4. **Type Hints**: 100% type hints cho IDE support
5. **Separation of Concerns**: Models (ORM) tách biệt Schemas (DTO)
