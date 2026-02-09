# HƯỚNG DẪN CHẠY DATABASE MIGRATION

## 📋 Yêu cầu trước khi chạy

### 1. Cài đặt PostgreSQL
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql

# Docker (khuyến nghị cho development)
docker run --name haiquan_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres123 \
  -e POSTGRES_DB=haiquan_kv8 \
  -p 5432:5432 \
  -d postgres:15
```

### 2. Tạo Database
```bash
# Kết nối PostgreSQL
psql -U postgres

# Tạo database
CREATE DATABASE haiquan_kv8;

# Thoát
\q
```

### 3. Cấu hình môi trường
```bash
# Copy file .env.example thành .env
cp .env.example .env

# Chỉnh sửa thông tin kết nối trong .env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=haiquan_kv8
DB_USER=postgres
DB_PASSWORD=your_password
```

### 4. Cài đặt dependencies
```bash
# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# hoặc: venv\Scripts\activate  # Windows

# Cài đặt packages
pip install -r requirements.txt
```

---

## 🚀 Chạy Migration

### Lệnh cơ bản

```bash
# Di chuyển vào thư mục project
cd haiquan_kv8_backend

# Kiểm tra trạng thái hiện tại
alembic current

# Xem lịch sử migrations
alembic history

# Chạy tất cả migrations (upgrade lên version mới nhất)
alembic upgrade head

# Rollback 1 version
alembic downgrade -1

# Rollback về version cụ thể
alembic downgrade 001_init_tables

# Reset về trạng thái ban đầu (⚠️ XÓA TẤT CẢ DỮ LIỆU!)
alembic downgrade base
```

### Tạo migration mới (khi thay đổi models)

```bash
# Tự động detect thay đổi từ models
alembic revision --autogenerate -m "add_new_column"

# Tạo migration trống để viết thủ công
alembic revision -m "custom_migration"
```

### Generate SQL (không chạy trực tiếp)

```bash
# Xuất SQL để review trước khi apply
alembic upgrade head --sql > migration.sql

# Xuất SQL cho một version cụ thể
alembic upgrade 001_init_tables --sql > init.sql
```

---

## 📊 Kiểm tra sau khi chạy Migration

### Kết nối và xem bảng
```bash
# Kết nối database
psql -U postgres -d haiquan_kv8

# Liệt kê tất cả bảng
\dt

# Xem cấu trúc một bảng
\d cong_chuc

# Xem dữ liệu seed
SELECT * FROM vai_tro;
SELECT * FROM sp_cong_viec_chuan;
SELECT * FROM cap_do_phuc_tap;
```

### Kết quả mong đợi (12 bảng)

| # | Tên bảng | Mô tả |
|---|----------|-------|
| 1 | `don_vi` | Đơn vị (Phòng/Đội/HQCK) |
| 2 | `vai_tro` | Vai trò phân quyền |
| 3 | `cong_chuc` | Công chức |
| 4 | `sp_cong_viec_chuan` | SP chuẩn (SP1-SP4) |
| 5 | `cap_do_phuc_tap` | Cấp độ (C1-C5) |
| 6 | `danh_muc_sp_cong_viec` | Danh mục công việc |
| 7 | `ke_khai_cong_viec` | Kê khai công việc |
| 8 | `phe_duyet_sp` | Lịch sử phê duyệt |
| 9 | `danh_gia_thang` | Đánh giá tháng |
| 10 | `tieu_chi_chung_danh_gia` | Chi tiết tiêu chí chung |
| 11 | `lanh_dao_chi_so` | Chỉ số d, đ, e |
| 12 | `audit_log` | Audit trail |
| - | `alembic_version` | Version tracking |

---

## 🔧 Troubleshooting

### Lỗi: "Target database is not up to date"
```bash
# Stamp database với version hiện tại
alembic stamp head
```

### Lỗi: "Can't locate revision"
```bash
# Xóa alembic_version và chạy lại
psql -U postgres -d haiquan_kv8 -c "DROP TABLE IF EXISTS alembic_version;"
alembic upgrade head
```

### Lỗi: "ENUM type already exists"
```bash
# Xóa các ENUM types cũ
psql -U postgres -d haiquan_kv8 << EOF
DROP TYPE IF EXISTS loai_don_vi_enum CASCADE;
DROP TYPE IF EXISTS cap_bac_vai_tro_enum CASCADE;
DROP TYPE IF EXISTS gioi_tinh_enum CASCADE;
DROP TYPE IF EXISTS trang_thai_ke_khai_enum CASCADE;
DROP TYPE IF EXISTS trang_thai_phe_duyet_enum CASCADE;
DROP TYPE IF EXISTS muc_xep_loai_enum CASCADE;
DROP TYPE IF EXISTS trang_thai_danh_gia_enum CASCADE;
DROP TYPE IF EXISTS audit_action_enum CASCADE;
EOF

# Chạy lại migration
alembic upgrade head
```

### Lỗi: Connection refused
```bash
# Kiểm tra PostgreSQL đang chạy
sudo systemctl status postgresql
# hoặc
docker ps | grep postgres

# Kiểm tra thông tin kết nối trong .env
cat .env | grep DB_
```

---

## 📦 Docker Compose (Khuyến nghị cho Development)

Tạo file `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    container_name: haiquan_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres123
      POSTGRES_DB: haiquan_kv8
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

Chạy:
```bash
# Khởi động database
docker-compose up -d

# Chạy migration
alembic upgrade head

# Xem logs
docker-compose logs -f db
```

---

## ✅ Checklist sau Migration

- [ ] Tất cả 12 bảng đã được tạo
- [ ] 8 ENUM types đã được tạo
- [ ] Dữ liệu seed đã được insert:
  - [ ] 6 vai trò trong `vai_tro`
  - [ ] 4 SP chuẩn trong `sp_cong_viec_chuan`
  - [ ] 5 cấp độ trong `cap_do_phuc_tap`
- [ ] Các indexes đã được tạo
- [ ] Các constraints (FK, UK, CHECK) hoạt động

---

> **Tiếp theo:** Chạy `scripts/seed_users.py` để import danh sách công chức từ Excel.
