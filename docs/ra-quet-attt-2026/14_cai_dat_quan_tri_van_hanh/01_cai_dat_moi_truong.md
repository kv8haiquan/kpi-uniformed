# 01 — Cài đặt môi trường

> Phục vụ công văn 153/CNTT ngày 08/7/2026 — Mục 14.1.
> Lập ngày 06/10/2026.

## 1. Yêu cầu phần cứng và hệ điều hành

### 1.1. Cấu hình tối thiểu

| Thành phần | Yêu cầu | Production hiện tại |
|------------|---------|---------------------|
| CPU | 4 cores | VPS Cloud (tương đương) |
| RAM | 8 GB | 7.8 GB |
| Ổ đĩa | 100 GB | 99 GB (đã dùng ~45 GB) |
| Hệ điều hành | Ubuntu 22.04 LTS trở lên | **Ubuntu 24.04.4 LTS** |
| Địa chỉ IP | IP công cộng tĩnh | **79.108.216.189** |
| Tên miền | Đã trỏ A record | **kpihaiquan.vn** |

### 1.2. Phân vùng đĩa (production hiện tại)

```
/dev/vda2   99G   45G   50G   48%   /
```

Toàn bộ hệ thống (OS, ứng dụng, database, backup) trên một phân vùng duy nhất. **Lưu ý:** đây là điểm yếu — backup cùng ổ với dữ liệu gốc.

### 1.3. Swap

Máy có **8 GB swap** (file swap tại `/swapfile`), cấu hình `vm.min_free_kbytes=131072` (128MB) để tránh OOM. Xem chi tiết tại `docs/van-hanh/HUONG_DAN_DEV_PROD.md` mục 3.3 (sự cố 25/08/2026).

---

## 2. Cài đặt các gói phụ thuộc

### 2.1. Cập nhật hệ thống

```bash
apt update && apt upgrade -y
apt install -y build-essential git curl wget vim htop net-tools
```

### 2.2. PostgreSQL 15+

Production hiện tại: **PostgreSQL 15.16** (native install, không qua Docker).

```bash
# Thêm PostgreSQL APT repository
sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
apt update

# Cài PostgreSQL 15
apt install -y postgresql-15 postgresql-contrib-15

# Kiểm tra
systemctl status postgresql
sudo -u postgres psql -c "SELECT version();"
```

**Lưu ý múi giờ:** Session timezone mặc định là `Asia/Ho_Chi_Minh` (UTC+7), quan trọng cho các cột `TIMESTAMPTZ`. Xem `docs/van-hanh/HUONG_DAN_DEV_PROD.md`. Ghi datetime không múi giờ không bị lệch; chênh 7 giờ chỉ xuất hiện ở tầng đọc/in (chuỗi ISO trả về theo UTC).

### 2.3. Python 3.10+

Production hiện tại: **Python 3.12.7**.

```bash
# Ubuntu 24.04 đã có Python 3.12 mặc định
python3 --version

# Cài pip và venv
apt install -y python3-pip python3-venv python3-dev
```

### 2.4. Node.js 20+ và npm

Production hiện tại: **Node.js v20.18.0**, npm 10.8.2.

```bash
# Cài Node.js 20 từ NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Kiểm tra
node --version
npm --version
```

### 2.5. nginx

Production hiện tại: **nginx 1.24.0**.

```bash
apt install -y nginx

# Kiểm tra
nginx -v
systemctl status nginx
```

### 2.6. PM2 (Process Manager)

Production hiện tại: **PM2 6.0.14** (global install với pm2-logrotate).

```bash
npm install -g pm2
pm2 install pm2-logrotate

# Cấu hình logrotate (giữ log 7 ngày, xoay khi > 50MB)
pm2 set pm2-logrotate:max_size 50M
pm2 set pm2-logrotate:retain 7
pm2 set pm2-logrotate:compress true

# Tự khởi động PM2 khi boot
pm2 startup systemd
# Chạy lệnh mà PM2 in ra (thường là: env PATH=... systemctl enable pm2-root)

# Kiểm tra
pm2 --version
```

### 2.7. Certbot (Let's Encrypt SSL)

```bash
apt install -y certbot python3-certbot-nginx

# Sau khi cài nginx và trỏ DNS, chạy:
certbot --nginx -d kpihaiquan.vn -d www.kpihaiquan.vn
# Certbot tự gia hạn qua systemd timer
systemctl status certbot.timer
```

---

## 3. Lấy mã nguồn

### 3.1. Clone repository

⚠️ **Repository là PRIVATE.** Cần SSH key hoặc Personal Access Token.

```bash
# Tạo SSH key nếu chưa có
ssh-keygen -t ed25519 -C "<email-quan-tri>"
cat ~/.ssh/id_ed25519.pub
# Thêm public key vào GitHub repository Settings → Deploy keys

# Clone
git clone git@github.com:<organization>/kpi-haiquan.git /root/kpi-haiquan
cd /root/kpi-haiquan
```

### 3.2. Tạo cây production (git worktree)

Production chạy từ `/opt/kpi-prod` (git worktree nhánh `prod`), KHÔNG phải từ `/root/kpi-haiquan`. Xem `docs/van-hanh/HUONG_DAN_DEV_PROD.md`.

```bash
# Tạo nhánh prod từ commit đang chạy (hoặc từ tag v20XX.XX.XX)
cd /root/kpi-haiquan
git branch prod <commit-hoặc-tag>

# Tạo worktree
git worktree add /opt/kpi-prod prod

# Kiểm tra
cd /opt/kpi-prod && git status -sb | head -1
# Phải ra: ## prod...origin/prod
```

---

## 4. Cấu hình database

### 4.1. Tạo database và user

```bash
sudo -u postgres psql
```

```sql
-- Tạo user ứng dụng (KHÔNG dùng superuser postgres)
CREATE USER kpi_user WITH PASSWORD '<cung cấp qua kênh bảo mật>';

-- Tạo database
CREATE DATABASE kpi_haiquan OWNER kpi_user;

-- Kết nối vào database
\c kpi_haiquan

-- Tạo extension (cần superuser)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tạo các schema cho từng module
CREATE SCHEMA IF NOT EXISTS lms;
CREATE SCHEMA IF NOT EXISTS forum;
CREATE SCHEMA IF NOT EXISTS legal;
CREATE SCHEMA IF NOT EXISTS portal;
CREATE SCHEMA IF NOT EXISTS common;
CREATE SCHEMA IF NOT EXISTS meeting;
CREATE SCHEMA IF NOT EXISTS chi_tieu;

-- Cấp quyền cho kpi_user trên các schema
GRANT ALL ON SCHEMA lms TO kpi_user;
GRANT ALL ON SCHEMA forum TO kpi_user;
GRANT ALL ON SCHEMA legal TO kpi_user;
GRANT ALL ON SCHEMA portal TO kpi_user;
GRANT ALL ON SCHEMA common TO kpi_user;
GRANT ALL ON SCHEMA meeting TO kpi_user;
GRANT ALL ON SCHEMA chi_tieu TO kpi_user;

\q
```

⚠️ **Lưu ý quan trọng:** 17/37 bảng trong schema `public` thuộc sở hữu của user `postgres` thay vì `kpi_user`. Điều này gây lỗi khi chạy Alembic migration. Xem `04_quan_tri_csdl.md` mục 1.3 để biết cách xử lý.

### 4.2. Cấu hình PostgreSQL

File cấu hình: `/etc/postgresql/15/main/postgresql.conf`

```bash
# Chỉnh tham số (tùy theo RAM, production hiện tại 7.8GB):
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
work_mem = 64MB
max_connections = 100

# Restart PostgreSQL
systemctl restart postgresql
```

### 4.3. Cấu hình múi giờ

```bash
# Đặt múi giờ hệ thống
timedatectl set-timezone Asia/Ho_Chi_Minh

# Kiểm tra
timedatectl
# Phải ra: Time zone: Asia/Ho_Chi_Minh (ICT, +0700)
```

PostgreSQL session timezone mặc định đã là `Asia/Ho_Chi_Minh`. Kiểm tra:

```sql
SHOW timezone;  -- Phải ra: Asia/Ho_Chi_Minh
```

---

## 5. Cài đặt Backend

### 5.1. Tạo virtual environment

```bash
cd /opt/kpi-prod/backend
python3 -m venv venv
source venv/bin/activate

# Cài dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**Lưu ý:** `requirements.txt` không còn gói nào có lỗ hổng bảo mật sau đợt vá 31/07/2026.

### 5.2. Tạo file cấu hình .env

```bash
cd /opt/kpi-prod/backend
cp .env.example .env
vim .env
```

Các biến BẮT BUỘC (xem chi tiết tại `02_cau_hinh.md`):

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kpi_haiquan
DB_USER=kpi_user
DB_PASSWORD=<cung cấp qua kênh bảo mật>

SECRET_KEY=<sinh bằng: openssl rand -hex 32>
INTERNAL_API_KEY=<sinh bằng: openssl rand -hex 32>

APP_ENV=production
DEBUG=false
```

### 5.3. Chạy migration

⚠️ **PHẢI chạy từ cây prod `/opt/kpi-prod/backend`**, không phải từ `/root/kpi-haiquan/backend`.

```bash
cd /opt/kpi-prod/backend
source venv/bin/activate
alembic upgrade head

# Kiểm tra
alembic current
```

Nếu gặp lỗi `"must be owner of table"`, xem `04_quan_tri_csdl.md` mục 1.3.

### 5.4. Seed dữ liệu khởi tạo

```bash
cd /opt/kpi-prod/backend

# Seed vai trò, đơn vị, công chức (từ file Excel)
python scripts/seed_users.py

# Seed danh mục SP công việc, cấp độ phức tạp
python scripts/seed_tasks.py

# Tạo tài khoản admin (nếu cần)
python scripts/seed_admin.py

# Kiểm tra
python scripts/verify_import.py
```

**Mật khẩu mặc định:** `123456` (người dùng tự đổi qua chức năng đổi mật khẩu).

---

## 6. Cài đặt Frontend

### 6.1. Cài dependencies

```bash
cd /opt/kpi-prod/frontend
npm ci
```

**Lưu ý:** Dùng `npm ci` (clean install) thay vì `npm install` để đảm bảo khớp với `package-lock.json`.

### 6.2. Tạo file cấu hình .env.local

```bash
cd /opt/kpi-prod/frontend
vim .env.local
```

```bash
NEXT_PUBLIC_API_URL=https://kpihaiquan.vn
NEXT_PUBLIC_APP_ENV=production
```

### 6.3. Build production

⚠️ **KHÔNG chạy `npm run build` trần** — dùng script có giới hạn bộ nhớ.

```bash
cd /opt/kpi-prod
backend/scripts/build_frontend.sh /opt/kpi-prod
```

Script này:
- Kiểm tra có ai đang thi ĐGNL không
- Chạy build trong cgroup có trần RAM
- Dừng nếu gặp lỗi

**Lý do:** `npm run build` trần đã làm đóng băng máy 12 phút ngày 25/08/2026.

---

## 7. Cấu hình nginx

### 7.1. Sao chép cấu hình

```bash
cp /root/kpi-haiquan/nginx/default.conf /etc/nginx/sites-available/kpi-haiquan

# Tạo symlink
ln -sf /etc/nginx/sites-available/kpi-haiquan /etc/nginx/sites-enabled/kpi-haiquan

# Xóa default nginx config nếu còn
rm -f /etc/nginx/sites-enabled/default
```

### 7.2. Kiểm tra và reload

```bash
nginx -t
# Phải ra: syntax is ok ... test is successful

systemctl reload nginx
```

Chi tiết cấu hình nginx: xem `02_cau_hinh.md` mục 2.

---

## 8. Khởi động các service với PM2

### 8.1. Tạo thư mục logs (nếu chưa có)

```bash
mkdir -p ~/.pm2/logs
```

### 8.2. Khởi động backend services

Các lệnh dưới đây là cấu hình **khuyến nghị** khi cài mới (mọi backend bind `127.0.0.1`, chỉ nginx mở ra ngoài). Production hiện tại dùng dạng `bash -c 'venv/bin/python -m uvicorn …'` và còn 6 backend + frontend bind `0.0.0.0` — xem `02_cau_hinh.md` mục 3.1. Có thể dùng `/opt/kpi-prod/ecosystem.config.js` với `--only <tên>`. Các lệnh:

```bash
cd /opt/kpi-prod/backend

# KPI Backend (port 8000)
pm2 start venv/bin/uvicorn --name kpi-backend \
  --interpreter none \
  -- app.main:app --host 127.0.0.1 --port 8000

# LMS Backend (port 8001)
pm2 start venv/bin/uvicorn --name lms-backend \
  --interpreter none \
  -- lms_service.main:app --host 127.0.0.1 --port 8001

# Forum Backend (port 8002)
pm2 start venv/bin/uvicorn --name forum-backend \
  --interpreter none \
  -- forum_service.main:app --host 127.0.0.1 --port 8002

# Legal Backend (port 8003)
pm2 start venv/bin/uvicorn --name legal-backend \
  --interpreter none \
  -- legal_service.main:app --host 127.0.0.1 --port 8003

# Portal Backend (port 8004)
pm2 start venv/bin/uvicorn --name portal-backend \
  --interpreter none \
  -- portal_service.main:app --host 127.0.0.1 --port 8004

# Common Backend (port 8005)
pm2 start venv/bin/uvicorn --name common-backend \
  --interpreter none \
  -- common_service.main:app --host 127.0.0.1 --port 8005

# HKG/Meeting Backend (port 8006)
pm2 start venv/bin/uvicorn --name meeting-backend \
  --interpreter none \
  -- meeting_service.main:app --host 127.0.0.1 --port 8006

# Chỉ tiêu Backend (port 8007)
pm2 start venv/bin/uvicorn --name chi-tieu-backend \
  --interpreter none \
  -- chi_tieu_service.main:app --host 127.0.0.1 --port 8007

# Zalo Worker (background job, không mở cổng)
pm2 start venv/bin/python --name zalo-worker \
  --interpreter none \
  -- -m common_service.workers.zalo_worker
```

### 8.3. Khởi động frontend

```bash
cd /opt/kpi-prod/frontend
pm2 start npm --name kpi-frontend -- start
```

### 8.4. Lưu cấu hình PM2

```bash
pm2 save
```

### 8.5. Kiểm tra trạng thái

```bash
pm2 list
pm2 logs --lines 50
```

Tất cả service phải ở trạng thái `online`.

---

## 9. Cấu hình cron jobs (backup tự động)

### 9.1. Sao chép scripts backup

```bash
mkdir -p /opt/kpi/scripts
cp /root/kpi-haiquan/backend/scripts/backup_*.sh /opt/kpi/scripts/
chmod 700 /opt/kpi/scripts/backup_*.sh
```

### 9.2. Cấu hình cron

```bash
cp /root/kpi-haiquan/docs/van-hanh/cron-hkg-backups.txt /etc/cron.d/hkg-backups
chmod 644 /etc/cron.d/hkg-backups
```

Nội dung cron (xem chi tiết tại `02_cau_hinh.md` mục 4):

- 02:00 + 14:00 — Full DB dump + rsync uploads
- 02:30 + 14:30 — Đẩy backup đã mã hóa lên GitHub
- 02:45 + 14:45 — Snapshot mã nguồn → branch `auto-backup`

### 9.3. Tạo thư mục backup

```bash
mkdir -p /var/backup/kpi_haiquan/daily
mkdir -p /var/backup/kpi_haiquan/monthly
mkdir -p /var/backup/kpi_haiquan/uploads
chown -R root:root /var/backup/kpi_haiquan
chmod 700 /var/backup/kpi_haiquan
```

---

## 10. Kiểm tra hệ thống

### 10.1. Kiểm tra các endpoint

```bash
# Backend health checks
curl -s http://localhost:8000/health    # KPI
curl -s http://localhost:8001/health    # LMS
curl -s http://localhost:8006/health    # HKG
# ... tương tự cho các service khác

# Frontend
curl -s http://localhost:3000 | head -20
```

### 10.2. Kiểm tra qua HTTPS

```bash
curl -I https://kpihaiquan.vn
# Phải ra: HTTP/2 200
```

### 10.3. Thử đăng nhập

Truy cập https://kpihaiquan.vn, đăng nhập bằng:
- Username: mã công chức (vd: `20ZZ-xxxx`)
- Password: `123456`

---

## 11. Kịch bản cài đặt lại toàn bộ (Disaster Recovery)

Trong trường hợp phải dựng lại hệ thống từ đầu trên máy chủ mới:

### Bước 1: Chuẩn bị máy chủ mới
- Ubuntu 24.04 LTS, RAM ≥ 8GB, Disk ≥ 100GB
- Cấu hình IP tĩnh, trỏ DNS `kpihaiquan.vn` về IP mới

### Bước 2: Cài đặt gói phụ thuộc
- Làm theo mục 2 (PostgreSQL, Python, Node.js, nginx, PM2, Certbot)

### Bước 3: Phục hồi database
```bash
# Lấy bản backup gần nhất (từ GitHub private hoặc bản local)
cd /var/backup/kpi_haiquan/daily
ls -lh db_*.sql.gz | tail -1

# Giải mã (nếu là bản từ GitHub)
gpg -d db_YYYYMMDD_HHMMSS.sql.gz.gpg > db_YYYYMMDD_HHMMSS.sql.gz

# Giải nén và restore
gunzip db_YYYYMMDD_HHMMSS.sql.gz
sudo -u postgres psql -d kpi_haiquan < db_YYYYMMDD_HHMMSS.sql
```

### Bước 4: Phục hồi uploads
```bash
# Từ backup local hoặc rsync từ máy cũ
rsync -avz <nguồn>/uploads/ /var/data/kpi/uploads/
```

### Bước 5: Lấy mã nguồn và cấu hình
- Làm theo mục 3, 5, 6, 7
- **Quan trọng:** Sao chép file `.env` từ máy cũ hoặc tạo lại với các giá trị secret cũ (SECRET_KEY, INTERNAL_API_KEY, mật khẩu DB)

### Bước 6: Khởi động PM2
- Làm theo mục 8

### Bước 7: Cấu hình backup
- Làm theo mục 9
- Đảm bảo GPG key cho mã hóa backup đã được import

### Bước 8: Kiểm tra và chuyển đổi
- Kiểm tra theo mục 10
- Cập nhật DNS nếu cần
- Thông báo người dùng

**Thời gian ước tính:** 2-4 giờ (tùy kích thước backup và tốc độ mạng).

---

## 12. Lưu ý quan trọng

### 12.1. An ninh

- **KHÔNG** commit file `.env` vào git
- Thư mục `/var/backup` chỉ root mới đọc được (`chmod 700`)
- Backup đẩy lên GitHub đã được mã hóa AES256 bằng GPG
- Đổi mật khẩu `kpi_user` của PostgreSQL ngay sau khi cài đặt

### 12.2. Production vs Development

- Production: `/opt/kpi-prod` (nhánh `prod`)
- Development: `/root/kpi-haiquan` (nhánh feature)
- **KHÔNG BAO GIỜ** sửa file trực tiếp trong `/opt/kpi-prod` — sẽ mất ở lần triển khai sau
- Xem chi tiết: `docs/van-hanh/HUONG_DAN_DEV_PROD.md`

### 12.3. Migration

- **LUÔN** chạy migration TRƯỚC khi nạp code mới
- Chỉ chạy migration từ `/opt/kpi-prod/backend`, không từ cây dev
- Xem chi tiết: `04_quan_tri_csdl.md` mục 3

### 12.4. Build Frontend

- **LUÔN** dùng `backend/scripts/build_frontend.sh`, KHÔNG chạy `npm run build` trần
- Script kiểm tra kỳ thi ĐGNL trước khi build
- Xem chi tiết: `05_van_hanh_hang_ngay.md` mục 4

---

## Tham khảo

- `backend/README.md` — Hướng dẫn kỹ thuật backend
- `frontend/README.md` — Hướng dẫn kỹ thuật frontend
- `docs/van-hanh/HUONG_DAN_DEV_PROD.md` — Môi trường Dev/Prod
- `docs/ra-quet-attt-2026/05_kien_truc_he_thong.md` — Kiến trúc tổng thể
- Memory `project_su_co_oom_build_khi_thi.md` — Sự cố OOM 25/08/2026
