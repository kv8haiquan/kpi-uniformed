# 02 — Cấu hình hệ thống

> Phục vụ công văn 153/CNTT ngày 08/7/2026 — Mục 14.2.
> Lập ngày 06/10/2026.

## 1. Biến môi trường Backend (.env)

File cấu hình: `/opt/kpi-prod/backend/.env` (KHÔNG commit vào Git)

### 1.1. Cấu trúc file .env

Backend dùng Pydantic Settings, ưu tiên: **ENV vars > .env file > default values**. Mỗi service (kpi, lms, forum, legal, portal, common, meeting, chi_tieu) đều cần file `.env` riêng tại thư mục gốc của service, hoặc dùng biến môi trường toàn cục (qua PM2 `--env` hoặc shell export).

**Nguồn tham chiếu:** `backend/.env.example`, `backend/app/config.py`, `backend/shared/config.py`, các `*_service/config.py`.

### 1.2. Bảng biến môi trường

#### Nhóm 1: DATABASE

| Biến | Ý nghĩa | Giá trị mặc định | Bắt buộc | Production |
|------|---------|------------------|----------|------------|
| `DB_HOST` | Địa chỉ PostgreSQL | `localhost` | Có | `localhost` |
| `DB_PORT` | Cổng PostgreSQL | `5432` | Có | `5432` |
| `DB_NAME` | Tên database | `haiquan_kv8` | Có | `kpi_haiquan` |
| `DB_USER` | User kết nối DB | `postgres` | Có | `kpi_user` |
| `DB_PASSWORD` | Mật khẩu DB | (không có) | **Có** | `<cung cấp qua kênh bảo mật>` |

**Lưu ý:** Connection string được build tự động:
- Async: `postgresql+asyncpg://{user}:{pass}@{host}:{port}/{db}`
- Sync (Alembic): `postgresql://{user}:{pass}@{host}:{port}/{db}`

#### Nhóm 2: SECURITY

| Biến | Ý nghĩa | Giá trị mặc định | Bắt buộc | Production |
|------|---------|------------------|----------|------------|
| `SECRET_KEY` | Khóa mã JWT (HS256), ≥32 ký tự | (không có) | **Có** | `<cung cấp qua kênh bảo mật>` |
| `INTERNAL_API_KEY` | Khóa gọi API nội bộ giữa các service | (không có) | **Có** | `<cung cấp qua kênh bảo mật>` |
| `ALGORITHM` | Thuật toán JWT | `HS256` | Không | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Thời gian hết hạn JWT (phút) | `30` | Không | `480` (8 giờ) |

**Sinh khóa:**
```bash
openssl rand -hex 32
```

⚠️ **Quan trọng:** `SECRET_KEY` PHẢI giống nhau giữa tất cả các service để decode JWT thành công (SSO nội bộ).

#### Nhóm 3: APPLICATION

| Biến | Ý nghĩa | Giá trị mặc định | Bắt buộc | Production |
|------|---------|------------------|----------|------------|
| `APP_NAME` | Tên ứng dụng (log) | `Hải quan KV8 - KPI System` | Không | (giữ mặc định) |
| `APP_ENV` | Môi trường | `development` | Không | `production` |
| `DEBUG` | Bật debug mode | `true` | Không | `false` |
| `API_V1_PREFIX` | Tiền tố API | `/api/v1` | Không | (giữ mặc định) |

#### Nhóm 4: LOGGING

| Biến | Ý nghĩa | Giá trị mặc định | Bắt buộc | Production |
|------|---------|------------------|----------|------------|
| `LOG_LEVEL` | Mức log | `INFO` | Không | `INFO` |
| `LOG_FORMAT` | Định dạng log | `json` | Không | `json` |

#### Nhóm 5: FILE PATHS

| Biến | Ý nghĩa | Giá trị mặc định | Bắt buộc | Production |
|------|---------|------------------|----------|------------|
| `DATA_DIR` | Thư mục dữ liệu tạm | `./data` | Không | `./data` |
| `UPLOAD_DIR` | Thư mục upload | `./uploads` | Không | Symlink → `/var/data/kpi/uploads` |
| `HKG_UPLOAD_DIR` | Thư mục upload HKG (legacy) | (không có) | Không | `/var/data/kpi/uploads` |

**Lưu ý:** Production dùng symlink để tách uploads ra khỏi cây mã nguồn (18/08/2026).

#### Nhóm 6: ZALO OA (common_service/services/zalo/)

| Biến | Ý nghĩa | Giá trị mặc định | Bắt buộc | Production |
|------|---------|------------------|----------|------------|
| `ZALO_ENABLED` | Bật worker Zalo | `false` | Không | `true` |
| `ZALO_DRY_RUN` | Chế độ thử (không gửi thật) | `true` | Không | `false` |
| `ZALO_APP_ID` | App ID từ Zalo Developers | (không có) | Có (nếu bật) | `<cung cấp qua kênh bảo mật>` |
| `ZALO_OA_ID` | OA ID (chỉ để ghi chú) | (không có) | Không | (ghi chú nội bộ) |
| `ZALO_OA_SECRET` | OA Secret từ Zalo | (không có) | Có (nếu bật) | `<cung cấp qua kênh bảo mật>` |
| `ZALO_TPL_MOI_HOP` | Template ID mời họp | (không có) | Không | (Zalo cấp sau khi duyệt) |
| `ZALO_TPL_NHAC_HOP` | Template ID nhắc họp | (không có) | Không | (Zalo cấp sau khi duyệt) |
| `ZALO_TPL_THAY_DOI_HOP` | Template ID thay đổi họp | (không có) | Không | (Zalo cấp sau khi duyệt) |
| `ZALO_TPL_HUY_HOP` | Template ID hủy họp | (không có) | Không | (Zalo cấp sau khi duyệt) |
| `ZALO_LOAI_BAT` | Phạm vi bật (MEETING, KPI, LMS) | `MEETING` | Không | `MEETING` |
| `ZALO_CHU_KY_GIAY` | Chu kỳ poll worker (giây) | `60` | Không | `60` |
| `ZALO_KHONG_GUI_TRUOC_GIO` | Không gửi trước giờ (VN) | `6` | Không | `6` |
| `ZALO_KHONG_GUI_SAU_GIO` | Không gửi sau giờ (VN) | `22` | Không | `22` |

**Hai cờ an toàn:** Muốn gửi tin Zalo thật phải đặt `ZALO_ENABLED=true` **VÀ** `ZALO_DRY_RUN=false`. Bật ENABLED mà quên tắt DRY_RUN thì worker vẫn chạy nhưng chỉ ghi log.

#### Nhóm 7: CHATBOT ĐGNL (lms_service)

| Biến | Ý nghĩa | Giá trị mặc định | Bắt buộc | Production |
|------|---------|------------------|----------|------------|
| `ZALO_BOT_API_KEY` | Khóa cho chatbot Zalo gọi từ bên ngoài | (không có) | Không | `<cung cấp qua kênh bảo mật>` |
| `DGNL_DAILY_MA_LINH_VUC` | Danh sách lĩnh vực lấy câu hỏi | (mặc định 9 lĩnh vực) | Không | (dùng mặc định) |

**ĐỂ TRỐNG** `ZALO_BOT_API_KEY` = TẮT HẲN tính năng (mọi lời gọi bị từ chối 401).

#### Nhóm 8: HKG Scheduler

| Biến | Ý nghĩa | Giá trị mặc định | Bắt buộc | Production |
|------|---------|------------------|----------|------------|
| `HKG_DISABLE_SCHEDULER` | Tắt scheduler nhắc họp | `false` | Không | `false` (prod), `true` (dev) |

**Lưu ý:** Môi trường dev BẮT BUỘC đặt `true` để không gửi nhắc họp trùng với prod.

### 1.3. File .env.dev (môi trường Development)

File: `/root/kpi-haiquan/backend/.env.dev`

Khác biệt so với production:
```bash
DB_NAME=kpi_haiquan_test          # DB riêng cho dev
DEBUG=true
HKG_DISABLE_SCHEDULER=true        # TẮT scheduler
ZALO_DRY_RUN=true                 # KHÔNG gửi Zalo thật
```

Script `backend/scripts/dev.sh` tự export `DB_NAME=kpi_haiquan_test` nên không có đường ghi nhầm vào prod.

---

## 2. Cấu hình nginx

File cấu hình: `/etc/nginx/sites-available/kpi-haiquan` → symlink `/etc/nginx/sites-enabled/kpi-haiquan`

### 2.1. Cấu trúc routing

| Path | Backend | Port | Ghi chú |
|------|---------|------|---------|
| `/api/v1/` (trừ các prefix dưới) | KPI Backend | 8000 | Mặc định, gồm auth, kê khai, đánh giá |
| `/api/v1/lms/` | LMS Backend | 8001 | Đào tạo, kỳ thi ĐGNL |
| `/api/v1/chi-tieu/` | Chỉ tiêu Backend | 8007 | Chỉ tiêu đơn vị |
| `/api/v1/hop-khong-giay/` | HKG Backend | 8006 | Họp Không Giấy REST API |
| `/ws/hop-khong-giay/` | HKG Backend | 8006 | WebSocket trình chiếu |
| `/api/forum/v1/` | Forum Backend | 8002 | Diễn đàn |
| `/api/legal/v1/` | Legal Backend | 8003 | Pháp luật |
| `/api/portal/v1/` | Portal Backend | 8004 | Portal/CMS |
| `/api/common/` | Common Backend | 8005 | Thông báo, File, KB |
| `/internal/` | Common Backend | 8005 | API nội bộ (chỉ localhost) |
| `/uploads/lms/` | LMS Backend | 8001 | File upload LMS |
| `/uploads/legal/` | Legal Backend | 8003 | File upload Legal |
| `/uploads/portal/` | Portal Backend | 8004 | File upload Portal |
| `/files/` | nginx static | - | Alias `/opt/kpihaiquan/data/uploads/` |
| `/` | Frontend Next.js | 3000 | SPA routing |

### 2.2. Các tham số quan trọng

```nginx
# Giới hạn upload 500MB (cho video LMS)
client_max_body_size 500M;

# Proxy read timeout (API thường 300s, WebSocket 3600s)
proxy_read_timeout 300s;

# WebSocket — PHẢI có header Upgrade
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

### 2.3. WebSocket HKG

⚠️ **Quan trọng:** `/ws/hop-khong-giay/` là prefix RIÊNG, KHÔNG nằm dưới `/api/v1/hop-khong-giay/`.

Location block đã thêm 30/07/2026 sau phát hiện thiếu trong repo.

```nginx
location /ws/hop-khong-giay/ {
    proxy_pass http://localhost:8006;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
}
```

### 2.4. Internal API (chỉ localhost)

```nginx
location /internal/ {
    allow 127.0.0.1;
    allow ::1;
    deny all;
    proxy_pass http://localhost:8005/internal/;
}
```

### 2.5. SSL/TLS (Let's Encrypt)

```nginx
listen 443 ssl;
ssl_certificate /etc/letsencrypt/live/kpihaiquan.vn/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/kpihaiquan.vn/privkey.pem;
include /etc/letsencrypt/options-ssl-nginx.conf;
ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
```

Certbot tự gia hạn qua systemd timer `certbot.timer` (chạy 2 lần/ngày).

### 2.6. Kiểm tra và reload nginx

```bash
# Kiểm tra cú pháp
nginx -t

# Reload (không ngừng dịch vụ)
systemctl reload nginx

# Xem log
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

---

## 3. Cấu hình PM2

### 3.1. Cấu trúc PM2 hiện tại

Production đang chạy 10 process ứng dụng (+ module `pm2-logrotate`). Phần lớn được khởi động qua CLI rồi `pm2 save`; file `/opt/kpi-prod/ecosystem.config.js` (tạo 01/05/2026) document hoá cấu hình và dùng cho service mới — **chỉ dùng kèm `--only <tên>`**, không `pm2 reload ecosystem.config.js` trần vì sẽ khởi động lại toàn bộ.

Số liệu đọc trực tiếp từ `pm2 jlist` ngày 06/10/2026:

| Process | Lệnh chạy (cwd `/opt/kpi-prod/backend`) | Host:Port | Số lần restart |
|---|---|---|---|
| `kpi-backend` | `venv/bin/python -m uvicorn app.main:app` | 0.0.0.0:8000 | 20 |
| `lms-backend` | `venv/bin/python -m uvicorn lms_service.main:app` | 0.0.0.0:8001 | 20 |
| `forum-backend` | `venv/bin/python -m uvicorn forum_service.main:app` | 0.0.0.0:8002 | 20 |
| `legal-backend` | `venv/bin/python -m uvicorn legal_service.main:app` | 0.0.0.0:8003 | 20 |
| `portal-backend` | `venv/bin/python -m uvicorn portal_service.main:app` | 0.0.0.0:8004 | 20 |
| `common-backend` | `venv/bin/python -m uvicorn common_service.main:app` | 0.0.0.0:8005 | 20 |
| `meeting-backend` | `venv/bin/python -m uvicorn meeting_service.main:app` | 127.0.0.1:8006 | 29 |
| `chi-tieu-backend` | `venv/bin/python -m uvicorn chi_tieu_service.main:app` | 127.0.0.1:8007 | 20 |
| `zalo-worker` | `venv/bin/python -m common_service.workers.zalo_worker` | — (không mở cổng) | 20 |
| `kpi-frontend` | `npm start -- -p 3000` (cwd `/opt/kpi-prod/frontend`) | *:3000 | 27 |

Số lần restart chủ yếu do các đợt phát hành phiên bản (mỗi lần `pm2 restart`), không phải lỗi; `unstable_restarts` = 0 với mọi process ứng dụng.

> ⚠️ **Khác biệt cấu hình cần khắc phục:** 6 backend (8000–8005) và frontend (3000) đang lắng nghe trên **mọi giao diện mạng** (`0.0.0.0` / `*`), chỉ HKG (8006) và Chỉ tiêu (8007) bind `127.0.0.1`. Kiểm tra 06/10/2026 qua IP công khai: 80/443 phản hồi, các cổng 3000/3001/8000/8005/5432 **bị chặn (timeout)** — tức hiện đang được che bởi tường lửa phía nhà cung cấp; nhưng tường lửa trên máy (ufw) đang tắt nên **chỉ còn một lớp bảo vệ**. Khuyến nghị: chuyển `--host` về `127.0.0.1` cho 6 backend + `-H 127.0.0.1` cho frontend và bật ufw (mục 6). PostgreSQL 5432 đã bind `127.0.0.1`.

**Thư mục làm việc:** `/opt/kpi-prod/backend` (backend), `/opt/kpi-prod/frontend` (frontend).

### 3.2. Các lệnh PM2 thường dùng

```bash
# Xem trạng thái
pm2 list
pm2 jlist                          # JSON format

# Xem log
pm2 logs                           # Tất cả
pm2 logs kpi-backend --lines 100   # Một service cụ thể
pm2 logs --err                     # Chỉ stderr

# Restart
pm2 restart kpi-backend
pm2 restart all

# Reload (graceful restart, zero-downtime)
pm2 reload kpi-backend
pm2 reload all --update-env        # Reload + nạp lại .env

# Stop/Start
pm2 stop kpi-backend
pm2 start kpi-backend

# Xem chi tiết
pm2 describe kpi-backend
pm2 monit                          # Real-time monitor

# Lưu cấu hình hiện tại
pm2 save

# Xóa process
pm2 delete kpi-backend
```

### 3.3. PM2 Logrotate

Module `pm2-logrotate` tự xoay vòng log, cấu hình:

```bash
pm2 set pm2-logrotate:max_size 50M    # Xoay khi log > 50MB
pm2 set pm2-logrotate:retain 7        # Giữ 7 bản log cũ
pm2 set pm2-logrotate:compress true   # Nén log cũ
pm2 set pm2-logrotate:rotateInterval "0 0 * * *"  # Cron: mỗi ngày 00:00
```

Log lưu tại: `~/.pm2/logs/<tên-process>-out.log` và `<tên-process>-error.log`.

### 3.4. PM2 Startup (tự khởi động khi boot)

```bash
# Tạo script systemd (chạy 1 lần khi cài đặt)
pm2 startup systemd
# Chạy lệnh mà PM2 in ra

# Sau mỗi lần thay đổi danh sách process, chạy:
pm2 save
```

---

## 4. Cấu hình cron jobs (backup tự động)

File cấu hình: `/etc/cron.d/hkg-backups`

### 4.1. Lịch backup

```cron
# Biến môi trường
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOME=/root
HKG_UPLOAD_DIR=/var/data/kpi/uploads

# 02:00 + 14:00 — Full DB dump + rsync uploads
0 2,14 * * * root /opt/kpi/scripts/backup_daily.sh >> /var/log/backup_kpi.log 2>&1

# 02:30 + 14:30 — Đẩy backup đã mã hóa lên GitHub
30 2,14 * * * root /opt/kpi/scripts/backup_to_github.sh >> /var/log/backup_github.log 2>&1

# 02:45 + 14:45 — Snapshot mã nguồn sang branch auto-backup
45 2,14 * * * root /opt/kpi/scripts/backup_source.sh >> /var/log/backup_source.log 2>&1

# Chủ nhật 03:00 — Cleanup preview cache cũ hơn 30 ngày
0 3 * * 0 root /opt/kpi/scripts/cleanup_preview_cache.sh >> /var/log/cleanup_cache.log 2>&1
```

### 4.2. Script backup

#### backup_daily.sh

```bash
# pg_dump database
sudo -u postgres pg_dump kpi_haiquan | gzip > /var/backup/kpi_haiquan/daily/db_$(date +%Y%m%d_%H%M%S).sql.gz

# rsync uploads với hardlink snapshot (tiết kiệm dung lượng)
rsync -a --link-dest=../uploads /var/data/kpi/uploads/ /var/backup/kpi_haiquan/uploads_snapshots/$(date +%Y%m%d_%H%M%S)/
rsync -a --delete /var/data/kpi/uploads/ /var/backup/kpi_haiquan/uploads/

# Cleanup bản cũ: giữ 30 ngày cho daily, 400 ngày cho monthly
find /var/backup/kpi_haiquan/daily/ -name "db_*.sql.gz" -mtime +30 -delete
find /var/backup/kpi_haiquan/monthly/ -name "db_*.sql.gz" -mtime +400 -delete
```

#### backup_to_github.sh

```bash
# Mã hóa bản backup mới nhất bằng GPG
gpg --symmetric --cipher-algo AES256 --output <file>.gpg <file>.sql.gz

# Đẩy lên private GitHub repository
cd <repo-backup> && git add . && git commit -m "Backup $(date)" && git push
```

**Lưu ý:** Passphrase GPG lưu trong biến môi trường hoặc file riêng, KHÔNG hardcode trong script.

#### backup_source.sh

```bash
# Chụp cây làm việc (gồm cả file chưa commit) sang nhánh auto-backup
cd /opt/kpi-prod
git add -A
git commit -m "Auto-backup $(date '+%Y-%m-%d %H:%M:%S')" --allow-empty
git push origin auto-backup --force
```

### 4.3. Xem log backup

```bash
tail -f /var/log/backup_kpi.log
tail -f /var/log/backup_github.log
tail -f /var/log/backup_source.log
```

### 4.4. Lỗ hổng còn lại (tính đến 06/10/2026)

1. **Uploads không có bản off-site** — 6,9 GB uploads chỉ sao lưu local, chưa từng rời máy
2. **Backup cùng ổ đĩa với dữ liệu gốc** — `/var/data` và `/var/backup` đều trên `/dev/vda2`
3. **Không có cảnh báo khi backup hỏng** — chỉ ghi log, không thông báo qua Zalo OA


---

## 5. Logrotate (log ứng dụng)

### 5.1. PM2 Logrotate

Đã cấu hình ở mục 3.3, tự động xoay vòng log của tất cả PM2 processes.

### 5.2. nginx Logrotate

Ubuntu 24.04 đã có logrotate cho nginx sẵn: `/etc/logrotate.d/nginx`

```
/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        if [ -f /var/run/nginx.pid ]; then
            kill -USR1 `cat /var/run/nginx.pid`
        fi
    endscript
}
```

Giữ 14 ngày log nginx.

---

## 6. Tường lửa (ufw)

### 6.1. Kiểm tra trạng thái

```bash
ufw status
```

**Production hiện tại (06/10/2026):** ufw **inactive**, iptables INPUT policy ACCEPT — việc lọc cổng hiện chỉ dựa vào tường lửa của nhà cung cấp VPS (đã kiểm chứng: cổng nội bộ bị chặn khi gọi qua IP công khai).

### 6.2. Cấu hình khuyến nghị (nếu bật)

```bash
# Cho phép SSH
ufw allow 22/tcp

# Cho phép HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Bật tường lửa
ufw enable
```

**Lưu ý:** Hiện chỉ 5432, 8006, 8007 bind `127.0.0.1`; các cổng 3000 (và 3001 của môi trường dev), 8000–8005 đang bind mọi giao diện (xem cảnh báo mục 3.1). Bật ufw với chính sách mặc định `deny incoming` + 3 rule trên sẽ chặn các cổng này ở tầng máy chủ. **Trước khi `ufw enable` phải chắc chắn đã `allow 22/tcp`**, nếu không sẽ mất kết nối SSH.

---

## 7. Múi giờ và TIMESTAMPTZ

### 7.1. Múi giờ hệ thống

```bash
timedatectl set-timezone Asia/Ho_Chi_Minh
timedatectl
# Phải ra: Time zone: Asia/Ho_Chi_Minh (ICT, +0700)
```

### 7.2. Múi giờ PostgreSQL

```bash
sudo -u postgres psql -c "SHOW timezone;"
# Phải ra: Asia/Ho_Chi_Minh
```

Nếu không đúng:

```sql
ALTER DATABASE kpi_haiquan SET timezone = 'Asia/Ho_Chi_Minh';
```

### 7.3. Lưu ý về TIMESTAMPTZ

- Cột `TIMESTAMPTZ` lưu giá trị theo UTC trong database
- Ghi `datetime.now()` (naive) từ Python KHÔNG lệch giờ (session TZ là Asia/Ho_Chi_Minh)
- Đọc ra dạng ISO string thì Pydantic serialize theo UTC (+00:00)
- Lỗi "lệch 7 giờ" KHÔNG nằm ở tầng GHI mà nằm ở tầng ĐỌC/HIỂN THỊ


---

## 8. Biến môi trường Frontend (.env.local)

File cấu hình: `/opt/kpi-prod/frontend/.env.local`

```bash
NEXT_PUBLIC_API_URL=https://kpihaiquan.vn
NEXT_PUBLIC_APP_ENV=production
```

Next.js build tại compile time, nên **PHẢI BUILD LẠI** khi đổi biến `NEXT_PUBLIC_*`.

---

## 9. Tổng hợp đường dẫn cấu hình quan trọng

| File/Thư mục | Mô tả |
|--------------|-------|
| `/opt/kpi-prod/backend/.env` | Biến môi trường backend (KHÔNG commit) |
| `/opt/kpi-prod/frontend/.env.local` | Biến môi trường frontend (KHÔNG commit) |
| `/etc/nginx/sites-available/kpi-haiquan` | Cấu hình nginx |
| `/etc/cron.d/hkg-backups` | Cron jobs backup |
| `/opt/kpi/scripts/` | Scripts backup (install thủ công, không theo git) |
| `/var/backup/kpi_haiquan/` | Thư mục lưu backup (local) |
| `/var/data/kpi/uploads/` | Thư mục uploads (6,9 GB) |
| `/var/log/backup_kpi.log` | Log backup database |
| `/var/log/nginx/access.log` | Log truy cập web |
| `~/.pm2/logs/` | Log PM2 processes |

---

## 10. Checklist sau khi thay đổi cấu hình

- [ ] Backend `.env` — restart service liên quan (`pm2 restart <tên>`)
- [ ] Frontend `.env.local` — **build lại** và restart (`npm run build && pm2 restart kpi-frontend`)
- [ ] nginx — kiểm tra `nginx -t` rồi `systemctl reload nginx`
- [ ] cron — kiểm tra syntax và test chạy thủ công
- [ ] PM2 — `pm2 save` sau khi thay đổi danh sách process
- [ ] Database — không cần restart PostgreSQL trừ khi đổi `postgresql.conf`

---

## Tham khảo

- `backend/.env.example` — Danh sách đầy đủ biến môi trường
- `backend/app/config.py` — Code đọc biến môi trường
- `docs/van-hanh/HUONG_DAN_DEV_PROD.md` — Môi trường Dev/Prod
- Memory `project_deploy_prod_worktree.md` — Quy trình triển khai
- Memory `project_db_backup_automation.md` — Chi tiết backup
