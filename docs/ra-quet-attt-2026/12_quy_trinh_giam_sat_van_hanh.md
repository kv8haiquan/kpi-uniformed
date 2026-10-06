# Mục 12 — Quy trình giám sát vận hành và xử lý sự cố

> Phục vụ công văn 153/CNTT ngày 08/7/2026. Lập ngày **06/10/2026**, kiểm chứng trực tiếp trên môi trường production.

---

## 1. Mục đích, phạm vi và căn cứ

### 1.1. Mục đích

Quy trình này quy định các hoạt động giám sát hệ thống KPI & Nền tảng số thống nhất của Chi cục Hải quan Khu vực VIII nhằm:

- Bảo đảm hệ thống hoạt động ổn định, liên tục phục vụ 558 công chức của toàn Chi cục
- Phát hiện sớm các bất thường về hạ tầng, dịch vụ, bảo mật để xử lý kịp thời
- Ngăn chặn sự cố ảnh hưởng tới dữ liệu và hoạt động nghiệp vụ (đánh giá KPI, thi ĐGNL, họp không giấy)
- Tuân thủ các yêu cầu an toàn, an ninh thông tin theo quy định

### 1.2. Phạm vi

Quy trình áp dụng cho toàn bộ hệ thống production đang phục vụ người dùng:

- **Hạ tầng:** máy chủ cloud VPS (79.108.216.189), CPU 4 core, RAM 7,8GB + swap 8GB, disk 99GB
- **10 dịch vụ ứng dụng:** KPI (port 8000), LMS (8001), Forum (8002), Legal (8003), Portal (8004), Common (8005), Họp Không Giấy/HKG (8006), Chỉ tiêu (8007), Zalo worker, Frontend Next.js (3000)
- **Hệ quản trị CSDL:** PostgreSQL 15.16, database `kpi_haiquan` (218 MB, 111 bảng / 8 schema)
- **Dịch vụ nền:** nginx 1.24.0, PM2 6.0.14, certbot (SSL Let's Encrypt), cron backup

### 1.3. Căn cứ

- Quy chế bảo đảm an toàn thông tin mạng, bảo vệ an ninh mạng của Tổng cục Hải quan ban hành kèm theo Quyết định số 1804/QĐ-TCHQ ngày 31/7/2024.
- Quy trình quản lý vận hành an toàn, an ninh hệ thống thông tin ban hành kèm theo Quyết định số 330/QĐ-HQKV8 ngày 10/7/2025 của Chi cục trưởng Chi cục Hải quan khu vực VIII.
- Công văn 153/CNTT ngày 08/7/2026 yêu cầu bàn giao hồ sơ hệ thống
- Tài liệu vận hành nội bộ: `docs/van-hanh/HUONG_DAN_DEV_PROD.md`, `docs/HKG/PM2_DEPLOY.md`

---

## 2. Đối tượng giám sát

### 2.1. Hạ tầng máy chủ

**Kiểm chứng 06/10/2026:**

| Chỉ số | Giá trị hiện tại | Ngưỡng cảnh báo | Công cụ/lệnh |
|--------|------------------|-----------------|--------------|
| CPU | 4 vCPU | > 85% liên tục 10 phút | `top`, `htop`, `uptime` (load average) |
| RAM | 7,8GB total / 5,1GB used (65%) | > 90% | `free -h` |
| Swap | 8GB / 1,9GB used (24%) | > 80% | `free -h` |
| Disk `/` | 99GB / 67GB used (71%) | > 85% | `df -h` |
| Uploads | `/var/data/kpi/uploads` 7,4GB | > 80GB | `du -sh /var/data/kpi/uploads` |
| Uptime | 224 ngày (khởi động lần cuối: 26/02/2026) | Theo dõi khởi động bất thường | `uptime` |
| Swap availability | **Đã có** 8GB từ 25/08/2026 | Bắt buộc phải có | Kiểm tra `/swapfile`, `/etc/fstab` |

**Ghi chú quan trọng:**
- Swap 8GB được bổ sung sau sự cố OOM ngày 25/08/2026 (build đè lên kỳ thi ĐGNL). Tham số kernel đã điều chỉnh: `vm.swappiness=10`, `vm.min_free_kbytes=131072` tại `/etc/sysctl.d/99-kpi-oom.conf`.
- Disk đang ở **71%** — gần ngưỡng cảnh báo. Chủ yếu do thư mục uploads (7,4GB) và logs PM2.

### 2.2. Dịch vụ ứng dụng

**Kiểm chứng 06/10/2026 lúc 15:26 — tất cả dịch vụ đang online:**

| Dịch vụ | PM2 ID | Trạng thái | RAM | CPU | Uptime | Health endpoint |
|---------|--------|------------|-----|-----|--------|-----------------|
| kpi-backend | 19 | online | 392 MB | 0,1% | 35 ngày | http://localhost:8000/health → **200** |
| lms-backend | 18 | online | 673 MB | 0,1% | 35 ngày | http://localhost:8001/health → **200** |
| forum-backend | 12 | online | 101 MB | 0,2% | 35 ngày | http://localhost:8002/health → **200** |
| legal-backend | 11 | online | 90 MB | 0,1% | 35 ngày | http://localhost:8003/health → **200** |
| portal-backend | 13 | online | 111 MB | 0,2% | 35 ngày | http://localhost:8004/health → **200** |
| common-backend | 14 | online | 105 MB | 0,3% | 35 ngày | http://localhost:8005/health → **200** |
| meeting-backend (HKG) | 16 | online | 158 MB | 0,2% | 35 ngày | http://localhost:8006/health → **200** |
| chi-tieu-backend | 15 | online | 89 MB | 0,1% | 35 ngày | http://localhost:8007/health → **200** |
| zalo-worker | 17 | online | 81 MB | 0% | 35 ngày | *(không có /health, kiểm tra log PM2)* |
| kpi-frontend | 20 | online | 63 MB | 0,2% | 35 ngày | http://localhost:3000 → **200** |
| pm2-logrotate | 8 | online | 47 MB | 0,2% | 56 ngày | *(quản lý log PM2)* |

**Lưu ý đặc biệt:**
- **LMS backend ngốn 673 MB** — chiếm nhiều nhất, là bình thường khi đang phục vụ kỳ thi ĐGNL hoặc sau kỳ thi. Tuy nhiên đã ghi nhận LMS không trả lại RAM sau khi kỳ thi kết thúc (tích lũy ~90MB/thí sinh), cần theo dõi và restart định kỳ sau kỳ thi lớn.
- **Zalo worker** không có health endpoint HTTP, kiểm tra bằng `pm2 logs zalo-worker --lines 20` để xác nhận worker đang chạy scheduler và chưa vượt trần chi tiêu Zalo OA.

**Công cụ kiểm tra:**
```bash
pm2 list                                      # Danh sách ngắn gọn
pm2 jlist | jq -r '.[] | "\(.name)|\(.pm2_env.status)|\(.monit.memory / 1024 / 1024 | floor)MB"'
pm2 logs <tên-service> --lines 50            # Log của từng service
pm2 monit                                     # Giao diện monitor thời gian thực
```

### 2.3. Hệ quản trị CSDL

**Kiểm chứng 06/10/2026:**

| Chỉ số | Giá trị | Ngưỡng cảnh báo |
|--------|---------|-----------------|
| Version | PostgreSQL 15.16 (Ubuntu) | Theo dõi security update |
| Database size | 218 MB | > 10GB (nên review schema) |
| Số bảng | 111 bảng / 8 schema | N/A |
| Trạng thái | active (systemctl) | Không được stopped |
| Kết nối | localhost:5432 (không mở public) | Bắt buộc chỉ localhost |
| Số schema | public (37 bảng), lms (22), meeting (23), common (8), legal (6), portal (5), forum (5), chi_tieu (5) | N/A |

**Phân bố dữ liệu theo bảng lớn:**
- `public.ke_khai_cong_viec`: 44.552 dòng
- `public.tieu_chi_chung_danh_gia`: 26.020 dòng
- `public.dang_ky_nghi`: 16.448 dòng
- `public.danh_gia_thang`: 2.614 dòng
- `public.cong_chuc`: 558 người dùng (15 đơn vị)

**Công cụ kiểm tra:**
```bash
systemctl status postgresql                   # Trạng thái service
sudo -u postgres psql -c "SELECT version();"
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('kpi_haiquan'));"
sudo -u postgres psql -d kpi_haiquan -c "SELECT schemaname, count(*) FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema') GROUP BY schemaname;"
```

### 2.4. Dịch vụ nền (nginx, certbot)

**Kiểm chứng 06/10/2026:**

| Dịch vụ | Trạng thái | Chi tiết |
|---------|-----------|----------|
| nginx 1.24.0 | active | HTTPS 443 (SSL), HTTP 80 → redirect 443 |
| Reverse proxy | OK | 10 upstream backends (3000, 8000–8007) |
| Access log | active | `/var/log/nginx/access.log` — 42.690 dòng, 12MB |
| Error log | empty (0 byte) | `/var/log/nginx/error.log` — không có lỗi ghi nhận ngày 06/10 |
| SSL kpihaiquan.vn | VALID | Hết hạn **21/11/2026** (còn **46 ngày**) |
| SSL dev.kpihaiquan.vn | VALID | Hết hạn **17/11/2026** (còn **42 ngày**) |
| certbot timer | active | Lần chạy tiếp theo: **07/10/2026 05:52** |

**Công cụ kiểm tra:**
```bash
systemctl status nginx
sudo certbot certificates
systemctl list-timers --no-pager | grep certbot
curl -sI https://kpihaiquan.vn | head -3       # Kiểm tra web từ bên ngoài
tail -50 /var/log/nginx/error.log              # Kiểm tra lỗi nginx
```

⚠️ **Lưu ý:** Không dùng `ping 79.108.216.189` để kiểm tra máy sống — ICMP bị chặn ở nhà cung cấp, luôn timeout kể cả khi máy hoàn toàn khoẻ. Dùng `curl -I https://kpihaiquan.vn` để kiểm tra.

### 2.5. Sao lưu tự động

**Kiểm chứng 06/10/2026:**

| Công việc | Script | Cron | Bản mới nhất | Trạng thái |
|-----------|--------|------|--------------|------------|
| Backup DB + uploads | `/opt/kpi/scripts/backup_daily.sh` | 02:00, 14:00 | `db_20261006_1400.sql.gz` (45MB) | ✅ Chạy đều |
| Off-site backup (GitHub) | `/opt/kpi/scripts/backup_to_github.sh` | 02:30, 14:30 | `db_20261006_1400.sql.gz.gpg` | ✅ Đã push lên GitHub |
| Snapshot mã nguồn | `/opt/kpi/scripts/backup_source.sh` | 02:45, 14:45 | nhánh `auto-backup` | ✅ Chạy đều |
| Cleanup cache | `/opt/kpi/scripts/cleanup_preview_cache.sh` | CN 03:00 | N/A | ✅ Hằng tuần |

**Cấu hình cron:** `/etc/cron.d/hkg-backups`

**Đích lưu trữ:**
- Local: `/var/backup/kpi_haiquan/` (⚠️ **ĐỊA CHỈ ÍT SỐ**, không phải `/var/backups/` nhiều số)
  - `daily/` — giữ 30 bản gần nhất
  - `monthly/` — giữ 400 ngày (~13 tháng)
  - `uploads/` — rsync mirror của `/var/data/kpi/uploads` (7,4GB)
  - `uploads_snapshots/<timestamp>/` — ảnh hardlink trước mỗi lần rsync, giữ 60 bản (thêm 25/08/2026), chỉ tốn ~1,7MB vì chia sẻ inode
- Off-site: GitHub private repository (DB dump đã mã hóa AES256-CBC, giữ 14 bản)

**Công cụ kiểm tra:**
```bash
ls -lht /var/backup/kpi_haiquan/daily/ | head -10     # 10 bản mới nhất
tail -20 /var/log/backup_kpi.log                      # Log backup DB
tail -20 /var/log/backup_github.log                   # Log off-site
```

**RPO (Recovery Point Objective):** 12 giờ (2 bản/ngày)  
**RTO (Recovery Time Objective):** < 30 phút (DB ~218 MB)

**Lỗ hổng còn lại (ghi nhận để khắc phục):**
1. ❌ Uploads (7,4GB) **chưa có bản off-site** — `backup_to_github.sh` chỉ đẩy DB dump, chưa đẩy uploads
2. ❌ Backup cục bộ cùng ổ đĩa với production — `/var/data` và `/var/backup` đều trên `/dev/vda2`
3. ❌ Không có cảnh báo tự động khi backup thất bại — script ghi log nhưng không ai đọc (có sẵn Zalo OA để đẩy cảnh báo)

### 2.6. An ninh

**Giám sát đăng nhập và tấn công:**

| Nguồn | Vị trí | Nội dung |
|-------|--------|----------|
| Log đăng nhập sai | PM2 log `kpi-backend` (logger `app.security`) | Từng lần đăng nhập sai (tài khoản, lần thứ mấy, IP), sự kiện khóa tạm tài khoản (15 phút sau 10 lần sai) |
| nginx access log | `/var/log/nginx/access.log` | Toàn bộ request HTTP/HTTPS (IP, thời điểm, method, URL, status code, User-Agent) |
| nginx error log | `/var/log/nginx/error.log` | Lỗi tầng web (502, 504, upstream timeout) |
| SSH login | `/var/log/auth.log` | Đăng nhập SSH, sudo, su |
| Log 403 truy cập họp | PM2 log `meeting-backend` | Định danh người bị từ chối truy cập cuộc họp (không có quyền) |

**Cơ chế bảo vệ đã triển khai (từ 31/07/2026):**
- Rate limit: 30 request/phút/IP tại endpoint `/api/v1/auth/login`
- Account lockout: khóa tạm 15 phút sau 10 lần đăng nhập sai liên tiếp
- Mật khẩu: hash bcrypt, không lưu plaintext
- JWT: HS256, TTL 480 phút (8 giờ), SECRET_KEY qua biến môi trường

**Công cụ kiểm tra:**
```bash
pm2 logs kpi-backend --lines 50 | grep -i "login\|failed\|locked"
tail -100 /var/log/nginx/access.log | grep -E ' 4(0[13]|29) '    # 401, 403, 429
tail -100 /var/log/auth.log | grep -i failed
```

### 2.7. Giám sát đặc thù theo nghiệp vụ

#### a) Kỳ thi ĐGNL (LMS)

**Chốt chặn tự động:** script `/opt/kpi-prod/backend/scripts/kiem_tra_ky_thi.sh` — cấm build/deploy khi đang có người thi (dựa vào `lms.phien_thi.last_seen` cập nhật liên tục).

**Chỉ số theo dõi khi có kỳ thi đang mở:**
- Số thí sinh DANG_THI: truy vấn `lms.thi_sinh WHERE trang_thai = 'DANG_THI' AND ky_thi_id = <id>`
- Số phiên thi active: `lms.phien_thi WHERE last_seen > NOW() - INTERVAL '5 minutes'`
- RAM của lms-backend: ~90MB/thí sinh, cần theo dõi và restart sau kỳ thi lớn
- Lỗi 499 trong nginx log (client closed connection — thí sinh mất kết nối khi nộp bài)

**Công cụ:**
```bash
/opt/kpi-prod/backend/scripts/kiem_tra_ky_thi.sh             # Kiểm tra có người thi không
pm2 logs lms-backend | grep -i "vi_pham\|nop_bai\|timeout"
```

**Sự cố tham khảo:** 25/08/2026 — `npm run build` chạy đè lên kỳ thi ĐGNL, 13 thí sinh mất 12 phút cuối bài thi 45 phút do máy đóng băng vì OOM. Đã xử lý bằng swap 8GB + script chốt chặn.

#### b) Zalo OA worker (nhắc họp + câu hỏi ĐGNL)

**Trần chi tiêu Zalo OA:**
- 500.000 VNĐ/ngày
- 2.000.000 VNĐ/tháng

**Giám sát:**
```bash
pm2 logs zalo-worker --lines 50 | grep -E "chi_tieu|quota|error|sent"
```

**Lưu ý:** Zalo worker LIVE từ 21/08/2026 (nhắc lịch công tác) và 28/08/2026 (câu hỏi ĐGNL hằng ngày).

---

## 3. Ma trận giám sát — chỉ số, công cụ, tần suất, ngưỡng, hành động

| # | Chỉ số | Công cụ/Lệnh | Tần suất | Ngưỡng cảnh báo | Người chịu trách nhiệm | Hành động khi vượt ngưỡng |
|---|--------|--------------|----------|-----------------|------------------------|---------------------------|
| **HẠ TẦNG** |
| 1 | CPU load average | `uptime` | Hằng ngày | > 4.0 liên tục 10 phút | Quản trị hệ thống | Kiểm tra `top`, tìm tiến trình ngốn CPU, xem log PM2; cân nhắc restart service hoặc nâng cấp máy |
| 2 | RAM used | `free -h` | Hằng ngày | > 90% | Quản trị hệ thống | Kiểm tra `pm2 list`, restart service ngốn nhiều RAM (đặc biệt LMS sau kỳ thi); xem swap usage |
| 3 | Swap used | `free -h` | Hằng ngày | > 80% (> 6.4GB) | Quản trị hệ thống | Kiểm tra RAM, restart service; nếu lặp lại thì nâng cấp RAM máy chủ |
| 4 | Disk `/` | `df -h` | Hằng tuần | > 85% | Quản trị hệ thống | Dọn log cũ PM2 (`~/.pm2/logs/*.log`), nginx log, xoá backup cũ thủ công nếu cần |
| 5 | Uploads size | `du -sh /var/data/kpi/uploads` | Hằng tuần | > 80GB | Quản trị hệ thống | Review file cũ, xoá file test/demo; cân nhắc mount thêm ổ đĩa |
| 6 | Uptime | `uptime` | Hằng ngày | Khởi động bất thường | Quản trị hệ thống | Xem `/var/log/syslog`, `/var/log/kern.log` để tìm nguyên nhân reboot |
| **DỊCH VỤ ỨNG DỤNG** |
| 7 | PM2 process status | `pm2 list` | Hằng ngày | Bất kỳ service nào `stopped`, `errored`, `one-launch-status` | Quản trị ứng dụng | `pm2 logs <service>` xem lỗi, `pm2 restart <service>`, kiểm tra config/env |
| 8 | LMS backend RAM | `pm2 jlist \| jq '.[] \| select(.name=="lms-backend") \| .monit.memory'` | Sau mỗi kỳ thi | > 1.5GB | Quản trị ứng dụng | Restart lms-backend: `pm2 restart lms-backend` |
| 9 | Health endpoints | `curl -s localhost:800x/health` | Hằng ngày | Bất kỳ endpoint nào ≠ 200 | Quản trị ứng dụng | Xem log service, restart, kiểm tra DB connection |
| 10 | Web accessibility | `curl -I https://kpihaiquan.vn` | Hằng ngày | ≠ 200 hoặc timeout | Quản trị hệ thống | Kiểm tra nginx status, PM2 frontend, firewall, DNS |
| **CƠ SỞ DỮ LIỆU** |
| 11 | PostgreSQL status | `systemctl status postgresql` | Hằng ngày | Không `active` | Quản trị CSDL | `systemctl start postgresql`, xem log `/var/log/postgresql/`, kiểm tra disk space |
| 12 | DB size | `sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('kpi_haiquan'));"` | Hằng tuần | > 10GB | Quản trị CSDL | Review schema, cân nhắc archive dữ liệu cũ, VACUUM FULL |
| 13 | DB connection | `sudo -u postgres psql -d kpi_haiquan -c "SELECT 1;"` | Hằng ngày | Lỗi kết nối | Quản trị CSDL | Kiểm tra PostgreSQL status, số connection (`pg_stat_activity`), restart nếu cần |
| **SSL & NGINX** |
| 14 | SSL expiry | `sudo certbot certificates` | Hằng tuần | < 30 ngày | Quản trị hệ thống | Certbot tự gia hạn; nếu < 14 ngày mà chưa gia hạn thì chạy `sudo certbot renew` thủ công |
| 15 | Certbot timer | `systemctl list-timers \| grep certbot` | Hằng tuần | Timer không active | Quản trị hệ thống | `systemctl start certbot.timer`, kiểm tra log certbot |
| 16 | nginx status | `systemctl status nginx` | Hằng ngày | Không `active` | Quản trị hệ thống | `systemctl start nginx`, kiểm tra config `/etc/nginx/sites-enabled/`, xem error log |
| 17 | nginx error log | `tail -50 /var/log/nginx/error.log` | Hằng ngày | Có lỗi 502, 504, upstream timeout | Quản trị hệ thống | Xem backend service tương ứng, restart service, kiểm tra PM2 |
| **SAO LƯU** |
| 18 | Backup daily DB | `ls -lt /var/backup/kpi_haiquan/daily/ \| head -1` | Hằng ngày | Không có bản mới trong 24h | Quản trị hệ thống | Xem log `/var/log/backup_kpi.log`, chạy thủ công `/opt/kpi/scripts/backup_daily.sh` |
| 19 | Backup off-site | `tail -20 /var/log/backup_github.log` | Hằng ngày | Không thấy "Hoàn tất off-site backup" trong 24h | Quản trị hệ thống | Kiểm tra kết nối GitHub, SSH key, chạy thủ công `/opt/kpi/scripts/backup_to_github.sh` |
| 20 | Cron backup | `cat /etc/cron.d/hkg-backups` | Hằng tuần | File không tồn tại hoặc cron tắt | Quản trị hệ thống | Khôi phục file cron, restart cron: `systemctl restart cron` |
| **AN NINH** |
| 21 | Đăng nhập sai liên tiếp | `pm2 logs kpi-backend --lines 100 \| grep -i "failed login"` | Hằng ngày | > 50 lần sai/ngày từ cùng IP | Quản trị an ninh | Xem IP, xem xét chặn IP tại nginx hoặc firewall; kiểm tra account lockout đang hoạt động |
| 22 | Tài khoản bị khóa tạm | `pm2 logs kpi-backend --lines 100 \| grep -i locked` | Hằng ngày | > 5 tài khoản khóa/ngày | Quản trị an ninh | Liên hệ người dùng, xác nhận có phải đánh nhầm mật khẩu; mở khóa nếu cần |
| 23 | HTTP 401/403/429 | `tail -100 /var/log/nginx/access.log \| grep -E ' 4(0[13]|29) '` | Hằng ngày | > 200 request 401/403 trong 1 giờ | Quản trị an ninh | Xem IP nguồn, pattern URL; có thể là bot scan — chặn IP nếu cần |
| 24 | SSH login failures | `grep -i failed /var/log/auth.log \| tail -20` | Hằng tuần | > 10 lần sai/ngày | Quản trị hệ thống | Xem IP nguồn, cân nhắc cài fail2ban, tắt SSH password authentication (chỉ dùng key) |
| **NGHIỆP VỤ ĐẶC THÙ** |
| 25 | Kỳ thi ĐGNL đang diễn ra | `backend/scripts/kiem_tra_ky_thi.sh` | Trước mỗi lần deploy/build | Có người thi | Lập trình viên | **KHÔNG deploy/build** — đợi kỳ thi kết thúc; nếu khẩn cấp thì `BO_QUA_KIEM_TRA_KY_THI=1` |
| 26 | Zalo worker chi tiêu | `pm2 logs zalo-worker \| grep chi_tieu` | Hằng ngày | > 400k/ngày hoặc > 1.8tr/tháng | Quản trị ứng dụng | Tạm dừng gửi tin không khẩn cấp, xem log tìm nguyên nhân gửi nhiều |
| 27 | Zalo worker status | `pm2 list \| grep zalo-worker` | Hằng ngày | `stopped` hoặc `errored` | Quản trị ứng dụng | Xem log, restart: `pm2 restart zalo-worker` |

---

## 4. Quy trình giám sát định kỳ

### 4.1. Giám sát hằng ngày (checklist)

**Thời gian:** 09:00 hằng ngày (sau khi backup đêm chạy xong)

**Người thực hiện:** Quản trị hệ thống / Lập trình viên trực

**Checklist:**

```bash
# 1. Kiểm tra hạ tầng
free -h                           # RAM > 90%?
df -h | grep -E '^/dev'           # Disk > 85%?
uptime                            # Load average > 4.0?

# 2. Kiểm tra PM2 processes
pm2 list                          # Có service nào stopped/errored?

# 3. Kiểm tra health endpoints
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do 
  echo -n "Port $port: "; curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health || echo "FAIL"
done
curl -I https://kpihaiquan.vn | head -3   # Web truy cập được từ bên ngoài?

# 4. Kiểm tra PostgreSQL
systemctl status postgresql       # Active?

# 5. Kiểm tra nginx
systemctl status nginx            # Active?
tail -20 /var/log/nginx/error.log # Có lỗi mới?

# 6. Kiểm tra backup
ls -lht /var/backup/kpi_haiquan/daily/ | head -3   # Có bản mới trong 24h?
tail -10 /var/log/backup_kpi.log                   # "Backup completed successfully"?
tail -10 /var/log/backup_github.log                # "Hoàn tất off-site backup"?

# 7. Kiểm tra an ninh
pm2 logs kpi-backend --lines 100 | grep -i "failed login" | tail -10
tail -50 /var/log/nginx/access.log | grep -E ' 4(0[13]|29) ' | tail -10

# 8. Kiểm tra sức khỏe production git tree
cd /opt/kpi-prod && git status -sb | head -1      # Phải là "## prod...origin/prod"
```

**Ghi nhận:** Nếu tất cả check đều PASS, ghi một dòng vào sổ nhật ký "Giám sát ngày DD/MM/YYYY: Bình thường". Nếu có bất thường, ghi chi tiết và hành động đã thực hiện.

### 4.2. Giám sát hằng tuần (checklist)

**Thời gian:** Thứ Hai 09:00 hằng tuần

**Checklist bổ sung (ngoài checklist hằng ngày):**

```bash
# 1. Kiểm tra SSL certificate expiry
sudo certbot certificates          # < 30 ngày?

# 2. Kiểm tra DB size
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('kpi_haiquan'));"

# 3. Kiểm tra uploads size
du -sh /var/data/kpi/uploads       # > 80GB?

# 4. Kiểm tra cron backup
cat /etc/cron.d/hkg-backups        # File tồn tại?
systemctl status cron              # Active?

# 5. Kiểm tra SSH login failures
grep -i failed /var/log/auth.log | wc -l    # Đếm số lần sai trong 7 ngày qua

# 6. Review PM2 logs size
du -sh ~/.pm2/logs/                # > 5GB thì cân nhắc xoá log cũ thủ công

# 7. Kiểm tra certbot timer
systemctl list-timers --no-pager | grep certbot   # Active?

# 8. Kiểm tra main và prod có khớp không
cd /root/kpi-haiquan && git rev-parse main prod | uniq | wc -l   # Phải ra 1
```

### 4.3. Giám sát hằng tháng (checklist)

**Thời gian:** Ngày 01 hằng tháng

**Checklist bổ sung:**

```bash
# 1. Review backup monthly
ls -lh /var/backup/kpi_haiquan/monthly/    # Có bản tháng trước?

# 2. Review disk usage theo thư mục
du -sh /var/data/kpi/uploads /var/backup /root/.pm2/logs /var/log/nginx

# 3. Kiểm tra số lượng bảng DB (phát hiện migration bị bỏ sót)
sudo -u postgres psql -d kpi_haiquan -c "SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema');"

# 4. Review security log
grep -i "failed login" ~/.pm2/logs/kpi-backend-out.log | wc -l    # Tổng số lần sai tháng trước
grep -i "locked" ~/.pm2/logs/kpi-backend-out.log | wc -l          # Tổng số tài khoản bị khóa

# 5. Kiểm tra phiên bản production hiện tại
cd /opt/kpi-prod && git log --oneline -1
cat /root/kpi-haiquan/docs/van-hanh/PHIEN_BAN_PROD.md | head -20  # Có khớp?

# 6. Review uptime và lần reboot gần nhất
uptime
last reboot | head -5
```

---

## 5. Quy trình xử lý sự cố

### 5.1. Phân cấp sự cố

| Cấp độ | Định nghĩa | Thời gian phản hồi | Thời gian khắc phục | Ví dụ |
|--------|------------|-------------------|---------------------|-------|
| **P0 - Nghiêm trọng** | Toàn bộ hệ thống không truy cập được, hoặc mất dữ liệu | Lập tức | < 1 giờ | Web down, DB bị xoá, tất cả service PM2 chết |
| **P1 - Cao** | Một module chính không hoạt động, ảnh hưởng > 50% người dùng | < 30 phút | < 4 giờ | Module KPI down trong kỳ đánh giá, kỳ thi ĐGNL bị gián đoạn |
| **P2 - Trung bình** | Một tính năng quan trọng lỗi, ảnh hưởng một nhóm người dùng | < 2 giờ | < 1 ngày | In phiếu đánh giá lỗi, xuất Excel báo cáo sai số liệu |
| **P3 - Thấp** | Lỗi nhỏ, workaround có thể thực hiện | < 1 ngày | < 1 tuần | Lỗi hiển thị UI, lỗi chính tả, link tài liệu 404 |

### 5.2. Quy trình 6 bước xử lý sự cố

Áp dụng quy trình đã mô tả tại **`09_kiem_thu_van_hanh_phien_ban.md` mục 4.2**:

**Bước 1 — Ghi nhận (Log the incident)**

- Nguồn: người dùng phản ánh / giám sát phát hiện / log hệ thống cảnh báo
- Ghi vào sổ: thời điểm, hiện tượng, ảnh hưởng, người báo cáo
- Phân cấp sự cố (P0/P1/P2/P3)

**Bước 2 — Chẩn đoán (Diagnose)**

- Thu thập log: PM2 log của service liên quan, nginx log, PostgreSQL log
- Tái hiện lỗi trên môi trường dev hoặc database test `kpi_haiquan_test` (KHÔNG thao tác trực tiếp production nếu không khẩn cấp)
- Xác định gốc rễ (root cause), không chỉ triệu chứng

**Bước 3 — Sửa lỗi (Fix)**

- Sửa trên nhánh `feature/fix-<mô-tả>` trong cây phát triển `/root/kpi-haiquan`
- Chạy test: `DB_NAME=kpi_haiquan_test pytest <thư-mục-test-liên-quan>`
- Nếu ảnh hưởng dữ liệu cũ: viết script backfill + query kiểm chứng
- Commit: `fix(<module>): mô tả gốc rễ + cách kiểm chứng`

**Bước 4 — Triển khai (Deploy)**

- `git push origin feature/fix-<mô-tả>`
- Chạy script triển khai: `/opt/kpi-prod/backend/scripts/trien_khai.sh <sha>`
- Script tự động: fetch code → cài thư viện (nếu cần) → **chạy migration trước** → build frontend → reload PM2 → kiểm tra health
- Downtime ≈ 0 do các service độc lập (chỉ reload service bị lỗi)
- Đẩy nhánh lên remote: `cd /opt/kpi-prod && git push origin prod`, sau đó `cd /root/kpi-haiquan && git branch -f main prod && git push origin main`

**Bước 5 — Kiểm chứng (Verify)**

- Kiểm tra lại hiện tượng đã hết chưa
- Chạy query đối soát dữ liệu (nếu có backfill)
- Liên hệ người báo cáo để xác nhận

**Bước 6 — Báo cáo (Document)**

- Sự cố lớn (P0/P1): lập báo cáo tổng kết lưu `docs/Fix-Bao-Cao/`
- Cập nhật `docs/van-hanh/PHIEN_BAN_PROD.md` với commit vừa deploy
- Sự cố hạ tầng: ghi vào sổ nhật ký vận hành (mẫu bên dưới mục 7)

### 5.3. Leo thang sự cố

| Cấp độ | Điều kiện leo thang | Người nhận |
|--------|---------------------|------------|
| P0 | Ngay lập tức | Chi cục trưởng + Phó Chi cục trưởng + Trưởng phòng CNTT |
| P1 | Nếu không khắc phục được trong 1 giờ | Phó Chi cục trưởng + Trưởng phòng CNTT |
| P2 | Nếu không khắc phục được trong 4 giờ | Trưởng phòng CNTT |
| P3 | Không cần leo thang | Ghi vào backlog |

### 5.4. Tham chiếu tài liệu lỗi thường gặp

Xem tài liệu **`16_loi_thuong_gap_khac_phuc.md`** (đang soạn song song) cho danh sách các lỗi thường gặp và cách khắc phục cụ thể:

- Lỗi kết nối PostgreSQL
- PM2 service restart liên tục
- nginx 502 Bad Gateway
- Alembic migration conflict
- Frontend build OOM (Out of Memory)
- Đăng nhập không thành công sau deploy
- Lỗi CORS khi gọi API từ frontend

---

## 6. Quy trình giám sát trong các tình huống đặc biệt

### 6.1. Giám sát khi phát hành phiên bản mới

**Trước khi phát hành (Pre-deployment checks):**

1. Kiểm tra kỳ thi ĐGNL: `/opt/kpi-prod/backend/scripts/kiem_tra_ky_thi.sh` — **KHÔNG deploy nếu đang có người thi**
2. Kiểm tra backup gần nhất: `ls -lht /var/backup/kpi_haiquan/daily/ | head -1` — phải có bản trong 24h
3. Kiểm tra git status của prod tree: `cd /opt/kpi-prod && git status -sb | head -1` — phải là `## prod...origin/prod`, không được `HEAD (no branch)`
4. Kiểm tra main và prod có khớp: `cd /root/kpi-haiquan && git rev-parse main prod | uniq | wc -l` — phải ra `1`
5. Xác nhận SHA commit cần deploy: `git log --oneline -1 <sha>`
6. Ghi nhận điểm quay lui: `git rev-parse HEAD` tại `/opt/kpi-prod`

**Trong khi phát hành:**

Script `/opt/kpi-prod/backend/scripts/trien_khai.sh <sha>` tự động thực hiện:

- Lấy code từ remote
- Cài thư viện nếu `requirements.txt` hoặc `package-lock.json` thay đổi
- **Chạy migration TRƯỚC KHI nạp code mới** (thứ tự bắt buộc — sự cố 18/08/2026 xảy ra vì làm ngược)
- Build frontend nếu thư mục `frontend/` thay đổi (qua `build_frontend.sh` có giới hạn RAM)
- Reload PM2 services
- Kiểm tra health endpoint của 8 backend

Nếu bất kỳ bước nào lỗi, script dừng ngay và in lệnh quay lui.

**Sau khi phát hành (Post-deployment checks):**

```bash
# 1. Kiểm tra tất cả health endpoints
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do 
  echo -n "Port $port: "; curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health
done

# 2. Kiểm tra web từ bên ngoài
curl -I https://kpihaiquan.vn | head -3

# 3. Kiểm tra PM2 processes
pm2 list

# 4. Kiểm tra git status prod tree
cd /opt/kpi-prod && git status -sb | head -1    # Phải là "## prod...origin/prod"

# 5. Xem log PM2 của service vừa deploy
pm2 logs <service-name> --lines 50

# 6. Đẩy nhánh prod lên remote
cd /opt/kpi-prod && git push origin prod

# 7. Fast-forward main theo prod
cd /root/kpi-haiquan && git branch -f main prod && git push origin main

# 8. Cập nhật sổ phiên bản
# Ghi commit SHA + nội dung vào docs/van-hanh/PHIEN_BAN_PROD.md
```

**Giám sát sau phát hành:**

- **30 phút đầu:** theo dõi sát PM2 logs, nginx access log, kiểm tra có lỗi 500/502/504 không
- **2 giờ đầu:** theo dõi phản hồi người dùng qua các kênh (Zalo, email)
- **24 giờ đầu:** xem log đăng nhập, kiểm tra chức năng nghiệp vụ chính (kê khai, phê duyệt, xem báo cáo)

**Lưu ý đặc biệt khi migration có sửa dữ liệu:**

- Chạy query kiểm chứng trước và sau migration
- Lưu kết quả vào file để đối chiếu
- Backup thủ công trước migration: `sudo -u postgres pg_dump kpi_haiquan | gzip > /var/backup/kpi_haiquan/daily/db_premig_<mô-tả>_$(date +%Y%m%d_%H%M%S).sql.gz`

### 6.2. Giám sát trong kỳ thi ĐGNL

**Trước kỳ thi (1 ngày trước):**

1. Kiểm tra RAM của lms-backend: `pm2 jlist | jq '.[] | select(.name=="lms-backend") | .monit.memory'` — nếu > 1GB thì restart: `pm2 restart lms-backend`
2. Kiểm tra backup gần nhất
3. Xác nhận swap 8GB đang hoạt động: `free -h`
4. Xác nhận script chốt chặn hoạt động: `/opt/kpi-prod/backend/scripts/kiem_tra_ky_thi.sh`
5. Thông báo lập trình viên: **KHÔNG deploy/build trong thời gian thi**

**Trong kỳ thi:**

```bash
# 1. Giám sát số thí sinh đang thi (5 phút/lần)
sudo -u postgres psql -d kpi_haiquan -c "SELECT COUNT(*) FROM lms.phien_thi WHERE last_seen > NOW() - INTERVAL '5 minutes';"

# 2. Giám sát RAM của lms-backend
pm2 jlist | jq '.[] | select(.name=="lms-backend") | .monit.memory / 1024 / 1024 | floor'

# 3. Giám sát nginx access log (lỗi 499 = client closed connection)
tail -f /var/log/nginx/access.log | grep -E '/luu-nhap|/nop-bai|/xac-nhan'

# 4. Giám sát PM2 log lms-backend
pm2 logs lms-backend --lines 20

# 5. Giám sát RAM/swap tổng thể
watch -n 10 free -h
```

**Sau kỳ thi:**

1. Restart lms-backend để giải phóng RAM: `pm2 restart lms-backend`
2. Kiểm tra log có lỗi không: `pm2 logs lms-backend --lines 100 | grep -i error`
3. Xác nhận số thí sinh đã nộp bài: truy vấn `lms.thi_sinh WHERE trang_thai = 'DA_NOP'`

**Chốt chặn tự động:**

Script `/opt/kpi-prod/backend/scripts/kiem_tra_ky_thi.sh` tự động chặn build/deploy khi:
- Có phiên thi (`lms.phien_thi`) với `last_seen` trong vòng 3 phút qua
- Hoặc có thí sinh (`lms.thi_sinh`) ở trạng thái `DANG_THI` chưa quá thời lượng bài thi + 10 phút ân hạn
- Hoặc có thí sinh đã xác nhận ca thi (`da_xac_nhan = true`) nhưng chưa bắt đầu làm bài (trong vòng 15 phút)

Lập trình viên có thể bỏ qua chốt này bằng `BO_QUA_KIEM_TRA_KY_THI=1` **chỉ khi thật khẩn cấp** (ví dụ sự cố P0).

### 6.3. Giám sát khi phát hiện tấn công

**Dấu hiệu tấn công:**

- > 100 request 401/403/429 từ cùng IP trong 5 phút
- > 50 lần đăng nhập sai liên tiếp từ cùng IP
- Request với User-Agent chứa từ khoá bot scan (`nikto`, `sqlmap`, `nmap`, `masscan`)
- Request đến URL không tồn tại với pattern SQL injection (`' OR 1=1`, `UNION SELECT`)

**Hành động:**

```bash
# 1. Xác định IP tấn công
tail -500 /var/log/nginx/access.log | grep -E ' 4(0[13]|29) ' | awk '{print $1}' | sort | uniq -c | sort -rn | head -10

# 2. Chặn IP tạm thời tại nginx (thêm vào /etc/nginx/sites-enabled/kpihaiquan.vn)
# deny <IP>;
# sudo nginx -t && sudo systemctl reload nginx

# 3. Kiểm tra log đăng nhập sai
pm2 logs kpi-backend --lines 200 | grep -i "failed login" | tail -20

# 4. Kiểm tra có tài khoản nào bị đột nhập không (last_login bất thường)
sudo -u postgres psql -d kpi_haiquan -c "SELECT ma_cc, ho_ten, last_login FROM public.cong_chuc WHERE last_login > NOW() - INTERVAL '1 hour' ORDER BY last_login DESC LIMIT 20;"

# 5. Cân nhắc cài fail2ban hoặc nâng rate-limit nginx
```

**Leo thang:** Báo ngay Phó Chi cục trưởng + Trưởng phòng CNTT nếu:
- Phát hiện tài khoản bị đột nhập
- IP tấn công nằm trong dải IP của cơ quan (27.71.x.x)
- Có dấu hiệu SQL injection thành công (lỗi PostgreSQL trong nginx log)

---

## 7. Lưu hồ sơ giám sát — Mẫu sổ nhật ký vận hành

### 7.1. Mẫu sổ nhật ký dạng bảng

Lưu tại: `docs/van-hanh/SO_NHAT_KY_VAN_HANH.md` hoặc Google Sheets/Excel

| Ngày | Người giám sát | Nội dung kiểm tra | Kết quả | Ghi chú / Hành động |
|------|----------------|-------------------|---------|---------------------|
| 06/10/2026 | Đ/c Huy | Checklist hằng ngày | ✅ Bình thường | RAM 65%, disk 71%, tất cả service online, backup 14:00 chạy đều |
| 05/10/2026 | Đ/c Hiếu | Checklist hằng ngày | ⚠️ LMS RAM cao | lms-backend 1.2GB sau kỳ thi ĐGNL sáng — đã restart, về 110MB |
| 04/10/2026 | Đ/c Huy | Checklist tuần | ✅ Bình thường | SSL còn 46 ngày, DB 218MB, uploads 7.4GB, certbot timer active |
| 03/10/2026 | Đ/c Hiếu | Checklist hằng ngày | ❌ Sự cố | meeting-backend stopped lúc 14:32 — restart OK, xem log phát hiện lỗi ORM; đã tạo issue |

### 7.2. Mẫu báo cáo sự cố

Lưu tại: `docs/Fix-Bao-Cao/BAO_CAO_SU_CO_<YYYYMMDD>_<mo-ta>.md`

```markdown
# Báo cáo sự cố: <Tiêu đề ngắn gọn>

**Mức độ:** P0 / P1 / P2 / P3  
**Thời gian phát hiện:** DD/MM/YYYY HH:MM  
**Thời gian khắc phục:** DD/MM/YYYY HH:MM  
**Thời gian downtime:** X phút / X giờ  
**Người xử lý:** Đ/c <Họ tên>

## 1. Hiện tượng

Mô tả hiện tượng người dùng gặp phải / hệ thống báo lỗi.

## 2. Tác động

- Số người dùng ảnh hưởng: X người / X%
- Module ảnh hưởng: KPI / LMS / HKG / ...
- Dữ liệu bị mất: Có/Không

## 3. Gốc rễ (Root cause)

Nguyên nhân sâu xa dẫn tới sự cố (KHÔNG chỉ triệu chứng).

## 4. Hành động đã thực hiện

1. Bước 1: ...
2. Bước 2: ...
3. Bước 3: ...

## 5. Commit sửa lỗi

- SHA: `<sha>`
- Nhánh: `feature/fix-<mo-ta>`
- Link: https://github.com/.../commit/<sha>

## 6. Kiểm chứng

Query/test case chạy để xác nhận lỗi đã hết.

## 7. Bài học rút ra (Lessons learned)

Cách phòng tránh sự cố tương tự trong tương lai.
```

---

## 8. Hiện trạng và khoảng trống

### 8.1. Đã có (kiểm chứng 06/10/2026)

✅ **Sao lưu tự động:**
- DB + uploads: 2 lần/ngày (02:00, 14:00), RPO 12 giờ
- Off-site backup (GitHub): 2 lần/ngày (02:30, 14:30), đã mã hóa AES256-CBC
- Snapshot mã nguồn: 2 lần/ngày (02:45, 14:45), nhánh `auto-backup`
- Retention: daily 30 ngày, monthly 400 ngày
- Uploads snapshot: 60 bản gần nhất (hardlink), giữ lịch sử 30 ngày

✅ **Swap 8GB:**
- Bổ sung sau sự cố OOM 25/08/2026
- Tham số kernel đã điều chỉnh (`vm.swappiness=10`, `vm.min_free_kbytes=131072`)

✅ **Chốt chặn build khi thi:**
- Script `backend/scripts/kiem_tra_ky_thi.sh`
- `trien_khai.sh` tự động gọi chốt này trước khi deploy
- `build_frontend.sh` giới hạn RAM build bằng systemd cgroup (trần 3GB)

✅ **Giám sát dịch vụ:**
- PM2 tự restart khi service crash
- Health endpoints `/health` cho 8 backend
- pm2-logrotate quản lý log

✅ **An ninh:**
- Rate limit: 30 request/phút/IP tại endpoint login (từ 31/07/2026)
- Account lockout: 15 phút sau 10 lần sai (từ 31/07/2026)
- Log đăng nhập sai + khóa tạm tài khoản (logger `app.security`)
- Mật khẩu: hash bcrypt
- JWT: HS256, TTL 480 phút
- SECRET_KEY, INTERNAL_API_KEY qua biến môi trường; INTERNAL_API_KEY đã rotate 31/07/2026, SECRET_KEY và mật khẩu DB chưa rotate

✅ **SSL tự động:**
- Let's Encrypt, certbot timer tự gia hạn
- kpihaiquan.vn: hết hạn 21/11/2026 (còn 46 ngày)

✅ **Quy trình phát hành:**
- Script `trien_khai.sh` tự động: fetch → cài thư viện → **migration trước** → build → reload → health check
- Thứ tự bắt buộc (tránh sự cố 18/08/2026): migration PHẢI chạy trước khi nạp code mới
- Downtime ≈ 0 do các service độc lập
- Git worktree `/opt/kpi-prod` (nhánh `prod`), tách khỏi cây phát triển

✅ **Kết nối outbound:**
- GitHub (backup off-site, snapshot mã nguồn)
- Let's Encrypt (gia hạn SSL)
- **Zalo OA API** (nhắc lịch công tác + câu hỏi ĐGNL hằng ngày) — LIVE từ 21/08/2026

### 8.2. Khoảng trống và đề xuất khắc phục

❌ **Chưa có hệ thống cảnh báo tự động:**
- Script backup ghi log nhưng không ai đọc
- Không có alert khi backup thất bại, disk đầy, service down
- **Đề xuất:** Tích hợp Zalo OA worker để gửi cảnh báo qua Zalo đến 2-3 quản trị viên (đã có sẵn Zalo OA, chỉ cần thêm template tin nhắn cảnh báo và scheduler kiểm tra)
- **Lộ trình:** Q4/2026

❌ **Uploads chưa có bản off-site:**
- 7,4GB uploads chỉ lưu cục bộ tại `/var/backup/kpi_haiquan/uploads/` (hardlink snapshot 60 bản)
- `backup_to_github.sh` chỉ đẩy DB dump, chưa đẩy uploads
- **Đề xuất:** Dùng `rclone` đồng bộ uploads lên Google Drive hoặc mount NAS của cơ quan
- **Lộ trình:** Q1/2027 (sau khi có hạ tầng lưu trữ bổ sung)

❌ **Backup cục bộ cùng ổ đĩa với production:**
- `/var/data` và `/var/backup` đều trên `/dev/vda2` (ổ duy nhất, 99GB)
- Ổ hỏng là mất cả production lẫn backup cục bộ
- **Đề xuất:** Mount thêm ổ đĩa riêng cho `/var/backup`, hoặc đẩy backup sang NAS
- **Lộ trình:** Khi có ngân sách nâng cấp hạ tầng

❌ **Dev và prod chung máy:**
- `/root/kpi-haiquan` (dev) và `/opt/kpi-prod` cùng máy 79.108.216.189
- Build ở dev vẫn có thể giết prod nếu không dùng `build_frontend.sh`
- **Đề xuất:** Tách máy dev riêng (đã có kế hoạch tại `docs/van-hanh/KE_HOACH_TACH_MOI_TRUONG.md`)
- **Lộ trình:** Khi có máy chủ bổ sung

❌ **Bắt buộc đổi mật khẩu lần đầu:**
- Cờ `must_change_password` chưa kích hoạt
- Mật khẩu khởi tạo `123456`, người dùng không bắt buộc đổi
- Chính sách mật khẩu chỉ yêu cầu ≥ 6 ký tự, chưa có yêu cầu phức tạp (≥ 8 ký tự + hoa/thường/số/ký tự đặc biệt)
- **Đề xuất:** Kích hoạt cờ `must_change_password`, nâng chuẩn mật khẩu ≥ 8 ký tự đủ 4 nhóm
- **Lộ trình:** Q4/2026 (đã ghi nhận trong `10_HOI_DAP_BO_SUNG.md` mục 2.3)

❌ **Audit log trigger chưa kích hoạt:**
- Bảng `public.audit_log` có cấu trúc sẵn (table_name, record_id, action, old/new JSONB, user_id, ip_address, timestamp)
- Trigger tự động ghi cho các bảng nghiệp vụ chưa kích hoạt trên production
- Vết thay đổi đang nằm phân tán trong từng bảng nghiệp vụ (ví dụ `lich_su_dieu_chinh`, `lich_su_dieu_chuyen`)
- **Đề xuất:** Kích hoạt trigger audit cho nhóm bảng trọng yếu (cong_chuc, danh_gia_thang, tieu_chi_chung_danh_gia, ke_khai_cong_viec)
- **Lộ trình:** Q1/2027 (gộp vào đợt cập nhật `must_change_password`)

❌ **Nhật ký đăng nhập thành công:**
- Chỉ ghi `last_login` gần nhất vào bảng `cong_chuc`
- Không có bảng riêng lưu lịch sử từng lần đăng nhập thành công (thời điểm, IP, User-Agent)
- **Đề xuất:** Bổ sung bảng `public.login_history` (thời điểm, tài khoản, IP, kết quả đúng/sai)
- **Lộ trình:** Q1/2027

❌ **LMS không trả lại RAM sau kỳ thi:**
- lms-backend tích lũy ~90MB/thí sinh, không giải phóng sau khi kỳ thi kết thúc
- **Đề xuất tạm thời:** Restart lms-backend sau mỗi kỳ thi lớn (> 30 thí sinh)
- **Đề xuất lâu dài:** Profiling Python code để tìm memory leak, cân nhắc đặt `max_memory_restart` cho PM2
- **Lộ trình:** Profiling Q1/2027

❌ **Không có tài liệu HDSD cho người dùng cuối:**
- Đã có tài liệu quản trị nghiệp vụ (`HUONG_DAN_ADMIN_PL3.md`), vận hành hệ thống (PM2_DEPLOY.md, MIGRATION_GUIDE.md)
- Chưa có HDSD theo vai trò: (1) Công chức — kê khai, tự chấm tiêu chí chung; (2) Lãnh đạo — phê duyệt, đánh giá, xếp loại; (3) TCCB — báo cáo, đối soát; (4) Học viên/Giảng viên LMS
- **Đề xuất:** Biên soạn HDSD người dùng cuối kèm ảnh chụp màn hình
- **Lộ trình:** Cùng đợt bàn giao hồ sơ cuối cùng

### 8.3. Mâu thuẫn với hồ sơ cũ (10_HOI_DAP_BO_SUNG.md)

**Kết nối outbound:**
- Hồ sơ cũ (mục 4.2, lập 05/08/2026) ghi: *"Ra Internet (outbound) chỉ có duy nhất: đẩy backup mã hóa + snapshot mã nguồn lên GitHub private (cron). Không tích hợp/gọi bất kỳ hệ thống bên ngoài nào khác"*
- **Hiện trạng mới:** Từ 21/08/2026, hệ thống đã có **Zalo worker** gọi **Zalo OA API** (api.zalo.me) để:
  - Gửi nhắc lịch công tác (3 mốc: 24 giờ, 1 giờ, 30 phút trước giờ họp — `meeting_service/services/scheduler_helpers.py`)
  - Gửi câu hỏi ĐGNL hằng ngày (mỗi ngày 1 câu hỏi trắc nghiệm đến 327 công chức)
  - Trần chi tiêu: 500k/ngày, 2tr/tháng
- **Kết luận:** Hồ sơ cũ đã lỗi thời, cần cập nhật mục 4.2 để phản ánh kết nối Zalo OA.

---

## 9. Tham chiếu

### 9.1. Tài liệu nội bộ liên quan

- `05_kien_truc_he_thong.md` — Kiến trúc tổng thể, port mapping, dịch vụ
- `06_co_so_du_lieu_sao_luu.md` — CSDL, schema, backup/restore
- `07_tai_khoan_phan_quyen_nhat_ky.md` — RBAC, JWT, audit log
- `09_kiem_thu_van_hanh_phien_ban.md` — Quy trình 6 bước xử lý sự cố, kiểm thử, cập nhật phiên bản
- `10_HOI_DAP_BO_SUNG.md` — Hiện trạng sau đợt vá 31/07/2026, kết nối outbound
- `docs/van-hanh/HUONG_DAN_DEV_PROD.md` — Quy trình dev/prod, ba chốt an toàn, script triển khai
- `docs/van-hanh/PHIEN_BAN_PROD.md` — Lịch sử phiên bản production
- `docs/van-hanh/KE_HOACH_TACH_MOI_TRUONG.md` — Kế hoạch tách máy dev riêng
- `docs/van-hanh/cron-hkg-backups.txt` — Cấu hình cron backup (bản cũ, xem `/etc/cron.d/hkg-backups` mới nhất)
- `docs/HKG/PM2_DEPLOY.md` — Triển khai PM2, quản lý processes
- `backend/scripts/trien_khai.sh` — Script triển khai chính
- `backend/scripts/kiem_tra_ky_thi.sh` — Chốt chặn build khi thi
- `backend/scripts/build_frontend.sh` — Build frontend an toàn với giới hạn RAM

### 9.2. Memory dự án (lịch sử sự cố và bài học)

- `project_db_backup_automation.md` — Sao lưu tự động, 3 lỗ hổng còn lại
- `project_su_co_oom_build_khi_thi.md` — Sự cố OOM 25/08/2026, swap 8GB, chốt chặn
- `project_deploy_prod_worktree.md` — Git worktree prod, sự cố detached HEAD 25/08
- `project_zalo_oa_hkg.md` — Zalo OA LIVE 21/08, trần chi tiêu, 44 số hỏng
- `reference_ping_khong_dung_duoc.md` — ICMP bị chặn ở nhà cung cấp, dùng curl thay ping

### 9.3. Công cụ hỗ trợ

**Trên máy chủ:**
```bash
pm2                                # Quản lý processes
systemctl                          # Quản lý systemd services
certbot                            # Quản lý SSL certificates
sudo -u postgres psql              # Truy vấn PostgreSQL
nginx -t && systemctl reload nginx # Kiểm tra cấu hình nginx
free -h, df -h, uptime, top        # Giám sát hạ tầng
journalctl -u <service>            # Xem log systemd
tail -f /var/log/nginx/*.log       # Theo dõi nginx log real-time
```

**Script nội bộ:**
```bash
/opt/kpi-prod/backend/scripts/trien_khai.sh <sha>           # Triển khai
/opt/kpi-prod/backend/scripts/kiem_tra_ky_thi.sh            # Kiểm tra kỳ thi
/opt/kpi-prod/backend/scripts/build_frontend.sh             # Build frontend an toàn
/opt/kpi-prod/scripts/backup_daily.sh                       # Backup thủ công (nếu có)
# Lưu ý: một số script có thể ở /opt/kpi/ hoặc /opt/kpi-prod/ tùy cấu hình
```

---

## 10. Lịch sử tài liệu

| Phiên bản | Ngày | Người soạn | Nội dung thay đổi |
|-----------|------|------------|-------------------|
| 1.0 | 06/10/2026 | Claude Sonnet 4.5 | Phiên bản đầu tiên — kiểm chứng toàn bộ trên môi trường production |

---

**Người soạn:** Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)  
**Ngày kiểm chứng:** 06/10/2026  
**Máy chủ production:** 79.108.216.189 (kpihaiquan.vn)  
**Commit production hiện tại:** `9534f17` (29/09/2026)
