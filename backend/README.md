# Hải quan KV8 - Hệ thống Đánh giá KPI & Xếp loại Công chức

> **Backend API** cho Chi cục Hải quan Khu vực VIII

## 📋 Tổng quan

Phần mềm quản lý hồ sơ và tính toán KPI định kỳ hàng tháng cho công chức Hải quan.

### Tech Stack
- **Backend:** Python 3.10+, FastAPI, SQLAlchemy 2.0 (Async)
- **Database:** PostgreSQL 15+
- **Authentication:** JWT (python-jose)
- **Migration:** Alembic

---

## 🚀 Cài đặt & Chạy

### 1. Yêu cầu hệ thống
```bash
# Python 3.10+
python --version

# PostgreSQL 15+ (hoặc Docker)
docker --version
```

### 2. Cài đặt

```bash
# Clone project
git clone <repo-url>
cd haiquan_kv8_backend

# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# hoặc: venv\Scripts\activate  # Windows

# Cài đặt dependencies
pip install -r requirements.txt
```

### 3. Cấu hình môi trường

```bash
# Copy file cấu hình mẫu
cp .env.example .env

# Chỉnh sửa .env với thông tin database
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=haiquan_kv8
# DB_USER=postgres
# DB_PASSWORD=your_password
```

### 4. Khởi động Database (Docker)

```bash
# Khởi động PostgreSQL
docker-compose up -d db

# Kiểm tra logs
docker-compose logs -f db
```

### 5. Chạy Migration

```bash
# Tạo tất cả bảng
alembic upgrade head

# Kiểm tra
alembic current
```

### 6. Import Dữ liệu Công chức

```bash
# Import từ file Excel
python scripts/seed_users.py

# Kiểm tra kết quả
python scripts/verify_import.py
```

### 7. Chạy Server (Development)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📁 Cấu trúc Project

```
haiquan_kv8_backend/
├── alembic/                    # Database migrations
│   ├── versions/               # Migration files
│   └── env.py                  # Alembic config
├── app/
│   ├── api/v1/                 # API Routes
│   ├── core/                   # Security, utils
│   ├── db/                     # Database session
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic
│   └── config.py               # Settings
├── scripts/                    # Utility scripts
│   ├── seed_users.py           # Import công chức
│   └── verify_import.py        # Kiểm tra dữ liệu
├── data/                       # File Excel input
├── docker-compose.yml          # Docker config
├── requirements.txt            # Dependencies
└── MIGRATION_GUIDE.md          # Hướng dẫn migration
```

---

## 🗄️ Database Schema

### Các bảng chính

| Bảng | Mô tả |
|------|-------|
| `don_vi` | Đơn vị (Phòng/Đội/HQCK) |
| `vai_tro` | Vai trò phân quyền |
| `cong_chuc` | Danh sách công chức |
| `sp_cong_viec_chuan` | Sản phẩm chuẩn (SP1-SP4) |
| `cap_do_phuc_tap` | Cấp độ phức tạp (C1-C5) |
| `danh_muc_sp_cong_viec` | Danh mục công việc Chi cục |
| `ke_khai_cong_viec` | Kê khai công việc |
| `phe_duyet_sp` | Lịch sử phê duyệt |
| `danh_gia_thang` | Đánh giá tổng hợp tháng |
| `audit_log` | Ghi log thay đổi |

---

## 🔐 Authentication

### Default Credentials (sau seed)
- **Username:** Mã công chức (VD: `20ZZ-0224`)
- **Password:** `123456`

### Vai trò & Quyền hạn

| Vai trò | Mã | Quyền |
|---------|-----|-------|
| Chi cục trưởng | CCT | Full access, phê duyệt cuối |
| Phó Chi cục trưởng | PCCT | Phê duyệt Trưởng ĐV |
| Trưởng đơn vị | TDV | Đề xuất xếp loại CC |
| Phó đơn vị | PDV | Phê duyệt CC |
| Công chức | CC | Kê khai công việc |

---

## 📊 API Endpoints (Preview)

```
POST   /api/v1/auth/login        # Đăng nhập
GET    /api/v1/users/me          # Thông tin user hiện tại
GET    /api/v1/don-vi            # Danh sách đơn vị
GET    /api/v1/cong-chuc         # Danh sách công chức
POST   /api/v1/ke-khai           # Tạo kê khai
PATCH  /api/v1/ke-khai/{id}      # Cập nhật kê khai
POST   /api/v1/phe-duyet         # Phê duyệt SP
GET    /api/v1/danh-gia/{thang}  # Xem đánh giá tháng
```

---

## 🧪 Testing

```bash
# Chạy tất cả tests
pytest

# Chạy với coverage
pytest --cov=app --cov-report=html
```

---

## 📝 Development

### Tạo migration mới

```bash
# Sau khi thay đổi models
alembic revision --autogenerate -m "add_new_feature"

# Review và apply
alembic upgrade head
```

### Code style

```bash
# Format code
black app/
isort app/

# Lint
flake8 app/
mypy app/
```

---

## 📄 License

Internal use only - Chi cục Hải quan Khu vực VIII

---

## 👥 Contributors

- Development Team
- Anthropic Claude (Technical Assistant)
