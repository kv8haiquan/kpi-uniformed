# 05 — Vận hành hằng ngày

> Phục vụ công văn 153/CNTT ngày 08/7/2026 — Mục 14.5.
> Lập ngày 06/10/2026.

## 1. Khởi động, dừng, restart từng thành phần

### 1.1. Backend Services (PM2)

```bash
# Khởi động
pm2 start kpi-backend
pm2 start all

# Dừng
pm2 stop kpi-backend
pm2 stop all

# Restart (có downtime ngắn)
pm2 restart kpi-backend
pm2 restart all

# Reload (graceful restart, zero-downtime)
pm2 reload kpi-backend
pm2 reload all

# Reload kèm nạp lại biến môi trường
pm2 reload kpi-backend --update-env
```

**Lưu ý:** Dùng `reload` thay vì `restart` để tránh mất kết nối đang xử lý (graceful shutdown).

### 1.2. Frontend (Next.js)

```bash
pm2 restart kpi-frontend
# Hoặc
pm2 reload kpi-frontend
```

### 1.3. PostgreSQL

```bash
# Khởi động
systemctl start postgresql

# Dừng
systemctl stop postgresql

# Restart
systemctl restart postgresql

# Reload config (không ngừng dịch vụ)
systemctl reload postgresql

# Kiểm tra trạng thái
systemctl status postgresql
```

**Lưu ý:** Dừng PostgreSQL = TẤT CẢ backend chết. Chỉ restart khi cần thiết (đổi cấu hình postgresql.conf).

### 1.4. nginx

```bash
# Kiểm tra cú pháp config
nginx -t

# Reload (không ngừng dịch vụ)
systemctl reload nginx

# Restart (có downtime ngắn)
systemctl restart nginx

# Kiểm tra trạng thái
systemctl status nginx
```

**Khuyến nghị:** Dùng `reload` thay vì `restart` để không ngắt kết nối đang xử lý.

### 1.5. Khởi động toàn bộ hệ thống (sau reboot máy chủ)

```bash
# 1. PostgreSQL (tự khởi động khi boot)
systemctl status postgresql

# 2. nginx (tự khởi động khi boot)
systemctl status nginx

# 3. PM2 (tự khởi động khi boot nếu đã chạy pm2 startup)
pm2 list

# Nếu PM2 chưa chạy:
pm2 resurrect
```

**Lưu ý:** PM2 tự khởi động process đã `pm2 save` trước đó. Không cần chạy lại lệnh `pm2 start` từng service.

---

## 2. Kiểm tra trạng thái hệ thống

### 2.1. Kiểm tra nhanh (checklist hằng ngày)

```bash
# 1. Trạng thái PM2
pm2 list
# Tất cả process phải ở trạng thái "online"

# 2. Disk space
df -h
# / phải còn ít nhất 10% trống (~10GB)

# 3. RAM
free -h
# Available phải > 1GB

# 4. CPU load
uptime
# Load average < số CPU cores (VPS thường 4 cores)

# 5. PostgreSQL
systemctl status postgresql
# Active: active (running)

# 6. nginx
systemctl status nginx
# Active: active (running)

# 7. Backend health
curl -s http://localhost:8000/health | jq
# Phải ra: {"status":"ok"}

# 8. Frontend
curl -I http://localhost:3000
# HTTP/1.1 200 OK
```

### 2.2. Kiểm tra chi tiết

```bash
# PM2 monit (real-time CPU/RAM)
pm2 monit

# PM2 describe (chi tiết 1 service)
pm2 describe kpi-backend

# Số kết nối database
sudo -u postgres psql -d kpi_haiquan -c "SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'kpi_haiquan';"

# Kích thước database
sudo -u postgres psql -d kpi_haiquan -c "SELECT pg_size_pretty(pg_database_size('kpi_haiquan'));"

# Top 5 process dùng nhiều RAM nhất
ps aux --sort=-%mem | head -6

# Top 5 process dùng nhiều CPU nhất
ps aux --sort=-%cpu | head -6
```

### 2.3. Kiểm tra log lỗi

```bash
# PM2 errors (tất cả services)
pm2 logs --err --lines 50

# PM2 errors (1 service cụ thể)
pm2 logs kpi-backend --err --lines 100

# nginx errors
tail -50 /var/log/nginx/error.log

# PostgreSQL errors
sudo tail -50 /var/log/postgresql/postgresql-15-main.log

# Backup log
tail -20 /var/log/backup_kpi.log
```

---

## 3. Xem log

### 3.1. Log PM2

```bash
# Xem log tất cả services (live)
pm2 logs

# Xem log 1 service cụ thể (live)
pm2 logs kpi-backend

# Xem 100 dòng cuối
pm2 logs kpi-backend --lines 100

# Chỉ xem stdout
pm2 logs kpi-backend --out

# Chỉ xem stderr
pm2 logs kpi-backend --err

# Log file paths
ls -lh ~/.pm2/logs/
```

### 3.2. Log nginx

```bash
# Access log (live)
tail -f /var/log/nginx/access.log

# Error log (live)
tail -f /var/log/nginx/error.log

# Lọc status code 500 (server error)
grep " 500 " /var/log/nginx/access.log

# Lọc status code 404 (not found)
grep " 404 " /var/log/nginx/access.log

# Top 10 IP truy cập nhiều nhất
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr | head -10
```

### 3.3. Log PostgreSQL

```bash
# Log chính
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Lọc ERROR
sudo grep ERROR /var/log/postgresql/postgresql-15-main.log | tail -20

# Lọc slow query (> 1s)
sudo grep "duration:" /var/log/postgresql/postgresql-15-main.log | awk '$3 > 1000' | tail -20
```

### 3.4. Log backup

```bash
# Database backup
tail -50 /var/log/backup_kpi.log

# GitHub backup (off-site)
tail -50 /var/log/backup_github.log

# Source backup
tail -50 /var/log/backup_source.log
```

---

## 4. Bảo trì có kế hoạch

### 4.1. Bảo trì hằng tuần

**Thứ 2 hằng tuần, 06:00 (giờ vắng người dùng):**

```bash
# 1. Kiểm tra disk space
df -h

# 2. Kiểm tra bản backup gần nhất
ls -lht /var/backup/kpi_haiquan/daily/ | head -5

# 3. Kiểm tra log lỗi
pm2 logs --err --lines 100 | grep -i "error\|exception\|failed"

# 4. VACUUM database (nếu cần)
sudo -u postgres psql -d kpi_haiquan -c "VACUUM ANALYZE;"

# 5. Kiểm tra restart count PM2
pm2 jlist | jq '.[] | {name: .name, restarts: .pm2_env.restart_time}'
# Nếu có service restart > 100 lần/tuần → cần điều tra
```

### 4.2. Bảo trì hằng tháng

**Ngày 1 hằng tháng, 06:00:**

```bash
# 1. Kiểm tra kích thước database
sudo -u postgres psql -d kpi_haiquan -c "SELECT pg_size_pretty(pg_database_size('kpi_haiquan'));"

# 2. Kiểm tra top 10 bảng lớn nhất
sudo -u postgres psql -d kpi_haiquan <<EOF
SELECT 
    schemaname || '.' || tablename AS table_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
EOF

# 3. Cập nhật hệ thống (cần reboot)
# ⚠️ CHỈ chạy khi đã thông báo người dùng trước
apt update && apt upgrade -y
# Reboot nếu cần: shutdown -r +10 "Máy chủ sẽ khởi động lại sau 10 phút"

# 4. Kiểm tra SSL certificate (còn bao lâu hết hạn)
certbot certificates
# Let's Encrypt tự gia hạn, nhưng kiểm tra để đảm bảo
```

### 4.3. Bảo trì đột xuất

Khi có thông báo lỗi, cần kiểm tra ngay:

```bash
# 1. Xem log lỗi gần nhất
pm2 logs --err --lines 200

# 2. Kiểm tra service nào đang lỗi
pm2 list | grep errored

# 3. Restart service lỗi
pm2 restart <tên-service>

# 4. Nếu vẫn lỗi → xem log chi tiết
pm2 logs <tên-service> --err --lines 500

# 5. Kiểm tra disk space (thường là nguyên nhân)
df -h
```

---

## 5. Xử lý sự cố

### 5.1. Sự cố: Service không khởi động

**Triệu chứng:** `pm2 list` hiển thị service ở trạng thái `errored` hoặc `stopped`.

**Nguyên nhân thường gặp:**
1. Port đã được dùng bởi process khác
2. File `.env` sai (thiếu biến bắt buộc, mật khẩu DB sai)
3. Database không kết nối được
4. Thiếu thư viện Python

**Cách xử lý:**

```bash
# Bước 1: Xem log lỗi
pm2 logs <tên-service> --err --lines 100

# Bước 2: Kiểm tra port có bị chiếm không
netstat -tulpn | grep <port>
# Nếu có process khác đang dùng → kill hoặc đổi port

# Bước 3: Kiểm tra .env
cat /opt/kpi-prod/backend/.env | grep -E "DB_|SECRET_KEY"
# Đảm bảo tất cả biến bắt buộc có giá trị

# Bước 4: Kiểm tra kết nối DB
psql -U kpi_user -d kpi_haiquan -h localhost -c "SELECT 1;"
# Phải ra: 1 row

# Bước 5: Restart service
pm2 restart <tên-service>
```

### 5.2. Sự cố: Website không truy cập được (502 Bad Gateway)

**Triệu chứng:** Truy cập https://kpihaiquan.vn ra lỗi 502 Bad Gateway.

**Nguyên nhân thường gặp:**
1. Backend service chết
2. nginx không proxy được tới backend
3. Frontend chết

**Cách xử lý:**

```bash
# Bước 1: Kiểm tra nginx
systemctl status nginx
nginx -t

# Bước 2: Kiểm tra PM2
pm2 list
# Service nào ở trạng thái "errored" hoặc "stopped" → restart

# Bước 3: Kiểm tra backend health
curl http://localhost:8000/health
curl http://localhost:3000

# Bước 4: Nếu vẫn 502 → xem log nginx
tail -50 /var/log/nginx/error.log

# Bước 5: Restart tất cả
pm2 restart all
systemctl reload nginx
```

### 5.3. Sự cố: Database chậm / không phản hồi

**Triệu chứng:** API timeout, trang web chậm.

**Nguyên nhân thường gặp:**
1. Quá nhiều kết nối DB
2. Query chậm (missing index)
3. Disk I/O cao

**Cách xử lý:**

```bash
# Bước 1: Kiểm tra số kết nối
sudo -u postgres psql -d kpi_haiquan -c "SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'kpi_haiquan';"
# Nếu > 80 connections → có vấn đề

# Bước 2: Xem query đang chạy
sudo -u postgres psql -d kpi_haiquan -c "SELECT pid, usename, state, query_start, query FROM pg_stat_activity WHERE datname = 'kpi_haiquan' AND state = 'active' ORDER BY query_start;"

# Bước 3: Kill query chậm (nếu cần)
sudo -u postgres psql -d kpi_haiquan -c "SELECT pg_terminate_backend(<pid>);"

# Bước 4: Restart backend để reset connection pool
pm2 restart all

# Bước 5: VACUUM (nếu disk I/O cao)
sudo -u postgres psql -d kpi_haiquan -c "VACUUM ANALYZE;"
```

### 5.4. Sự cố: Disk full (hết ổ đĩa)

**Triệu chứng:** `df -h` hiển thị `/` đã dùng > 95%.

**Nguyên nhân thường gặp:**
1. Log PM2 phình to
2. Backup cũ chưa xóa
3. Uploads tăng nhanh

**Cách xử lý:**

```bash
# Bước 1: Kiểm tra thư mục chiếm nhiều dung lượng nhất
du -sh /var/* | sort -rh | head -10
du -sh /root/* | sort -rh | head -10
du -sh ~/.pm2/logs/* | sort -rh | head -10

# Bước 2: Xóa log PM2 cũ
pm2 flush

# Bước 3: Xóa backup cũ hơn 30 ngày (thủ công)
find /var/backup/kpi_haiquan/daily/ -name "db_*.sql.gz" -mtime +30 -delete

# Bước 4: Xóa uploads cũ (nếu có policy)
# ⚠️ KHÔNG xóa tùy tiện, phải có policy từ trước

# Bước 5: Tăng kích thước ổ đĩa (liên hệ nhà cung cấp VPS)
```

### 5.5. Sự cố: OOM (Out of Memory) khi build frontend

**Triệu chứng:** `npm run build` treo hoặc bị kill, máy đóng băng.

**Nguyên nhân:** Build Next.js ngốn ~1,4GB RAM, máy chỉ có 7,8GB và không có swap (hoặc swap quá nhỏ).

**Giải pháp:** ĐÃ VÁ từ 25/08/2026.

```bash
# 1. Swap đã tăng lên 8GB
swapon --show
# Phải ra: /swapfile ... 8G

# 2. LUÔN dùng build_frontend.sh (có giới hạn RAM)
/opt/kpi-prod/backend/scripts/build_frontend.sh /opt/kpi-prod

# 3. KHÔNG chạy npm run build trần
```

Nếu vẫn gặp OOM:

```bash
# Giải phóng RAM trước khi build
pm2 stop all
npm run build
pm2 start all
```

### 5.6. Sự cố: Kỳ thi ĐGNL đang diễn ra, cần deploy gấp

**⚠️ TUYỆT ĐỐI KHÔNG** deploy khi đang có người thi. Script `trien_khai.sh` sẽ chặn.

**Nếu buộc phải deploy gấp:**

```bash
# Kiểm tra ai đang thi
/opt/kpi-prod/backend/scripts/kiem_tra_ky_thi.sh

# Nếu thật sự cần thiết (hotfix lỗi nghiêm trọng), bypass:
BO_QUA_KIEM_TRA_KY_THI=1 /opt/kpi-prod/backend/scripts/trien_khai.sh <SHA>
```

**Lưu ý:** Bypass chỉ dùng trong trường hợp khẩn cấp, đã báo lãnh đạo.

---

## 6. Giám sát và cảnh báo

### 6.1. Giám sát thủ công (checklist hằng ngày)

Xem mục 2.1.

### 6.2. Giám sát tự động (đang phát triển)

**Hiện trạng:** Chưa có hệ thống giám sát tự động gửi cảnh báo qua Zalo OA khi có lỗi.

**Kế hoạch:** Tích hợp cảnh báo qua Zalo OA (đã có module Zalo worker) khi:
- PM2 service restart liên tục
- Disk space < 10%
- Backup hỏng
- Database kết nối thất bại

Xem chi tiết: `docs/ra-quet-attt-2026/12_quy_trinh_giam_sat_van_hanh.md` (đang soạn).

---

## 7. Lưu ý quan trọng

### 7.1. Thời điểm an toàn để bảo trì

- **06:00 - 07:00** — ít người dùng nhất (trước giờ làm việc)
- **12:00 - 13:00** — giờ nghỉ trưa (nhưng vẫn có người online)
- **Cuối tuần** — ít người online, nhưng CHỈ khi không có kỳ thi ĐGNL

**TRÁNH:**
- **08:00 - 11:30** và **13:30 - 16:30** — giờ làm việc cao điểm
- **Đầu tháng** và **cuối tháng** — đang kê khai KPI
- **Trong kỳ thi ĐGNL** — kiểm tra bằng `kiem_tra_ky_thi.sh`

### 7.2. Backup trước khi làm gì

```bash
# Backup database trước khi:
# - Chạy migration quan trọng
# - Sửa dữ liệu thủ công
# - Upgrade PostgreSQL
# - Restore database

sudo -u postgres pg_dump kpi_haiquan | gzip > /var/backup/kpi_haiquan/daily/db_manual_$(date +%Y%m%d_%H%M%S).sql.gz
```

### 7.3. Thông báo người dùng trước khi bảo trì

Nếu cần downtime (restart PostgreSQL, reboot máy chủ):

1. Thông báo qua Zalo OA hoặc email **ít nhất 1 ngày trước**
2. Ghi rõ thời gian bắt đầu và thời gian dự kiến hoàn tất
3. Dán thông báo trên trang chủ (nếu có banner)

---

## 8. Tài liệu liên quan

### 8.1. Tài liệu bổ sung

- `docs/ra-quet-attt-2026/12_quy_trinh_giam_sat_van_hanh.md` — Quy trình giám sát (đang soạn)
- `docs/ra-quet-attt-2026/16_loi_thuong_gap_khac_phuc.md` — Lỗi thường gặp (đang soạn)
- `docs/van-hanh/HUONG_DAN_DEV_PROD.md` — Môi trường Dev/Prod
- Memory `project_su_co_oom_build_khi_thi.md` — Sự cố OOM 25/08/2026

### 8.2. Scripts hỗ trợ

| Script | Đường dẫn | Mục đích |
|--------|-----------|----------|
| `trien_khai.sh` | `/opt/kpi-prod/backend/scripts/` | Triển khai phiên bản |
| `kiem_tra_ky_thi.sh` | `/opt/kpi-prod/backend/scripts/` | Kiểm tra có ai đang thi không |
| `build_frontend.sh` | `/opt/kpi-prod/backend/scripts/` | Build frontend có giới hạn RAM |
| `dev.sh` | `/root/kpi-haiquan/backend/scripts/` | Chạy môi trường dev |
| `backup_daily.sh` | `/opt/kpi/scripts/` | Backup tự động (cron) |

---

## 9. Hotline và liên hệ khẩn cấp

### 9.1. Người liên hệ

| Vai trò | Tên | Liên hệ | Khi nào gọi |
|---------|-----|---------|-------------|
| Quản trị hệ thống | (cung cấp nội bộ) | (cung cấp nội bộ) | Lỗi kỹ thuật, hệ thống chết |
| Chủ dự án | (cung cấp nội bộ) | (cung cấp nội bộ) | Quyết định downtime, rollback |
| Nhà cung cấp VPS | (cung cấp nội bộ) | (cung cấp nội bộ) | Lỗi mạng, lỗi phần cứng |

### 9.2. Quy trình báo cáo sự cố

1. **Phát hiện lỗi** — qua giám sát hoặc người dùng báo
2. **Đánh giá mức độ nghiêm trọng:**
   - **P0 (Khẩn cấp):** Toàn bộ hệ thống chết, không ai truy cập được
   - **P1 (Cao):** 1 module quan trọng chết (KPI, LMS kỳ thi)
   - **P2 (Trung bình):** 1 tính năng lỗi, không ảnh hưởng toàn bộ
   - **P3 (Thấp):** Lỗi giao diện, hiệu năng chậm
3. **Xử lý:**
   - P0/P1: Gọi ngay quản trị hệ thống + chủ dự án
   - P2: Xử lý trong vòng 2 giờ
   - P3: Lên kế hoạch sửa trong tuần
4. **Ghi log sự cố** — vào file `docs/van-hanh/LICH_SU_SU_CO.md` (nếu có)

---

## 10. Checklist cuối ngày

- [ ] `pm2 list` — tất cả service "online"
- [ ] `df -h` — disk < 90%
- [ ] `tail /var/log/backup_kpi.log` — backup chạy thành công
- [ ] `pm2 logs --err --lines 50` — không có lỗi mới
- [ ] Kiểm tra email/Zalo — có báo cáo lỗi từ người dùng không

---

**Tài liệu này giúp người vận hành xử lý các tình huống hằng ngày một cách an toàn và hiệu quả.**
