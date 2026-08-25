# Cài đặt P0 Hardening (Phase 4.1)

Hướng dẫn deploy lên server **production** (chạy 1 lần khi go-live Phase 4.1).
Các file scripts trong repo CHƯA hoạt động cho tới khi làm các bước dưới.

---

## ⚠️ `/opt/kpi/scripts/` KHÔNG do `trien_khai.sh` quản

Cron chạy bản ở `/opt/kpi/scripts/`, không phải bản trong cây git. Phát hành
code bình thường **không** cập nhật nó. Sửa script backup xong phải cài tay:

```bash
cp -a /opt/kpi/scripts/backup_daily.sh /opt/kpi/scripts/backup_daily.sh.truoc-$(date +%Y%m%d)
sudo install -m 700 -o root -g root /opt/kpi-prod/scripts/backup_daily.sh /opt/kpi/scripts/backup_daily.sh
diff -q /opt/kpi/scripts/backup_daily.sh /opt/kpi-prod/scripts/backup_daily.sh && echo KHỚP
```

Kiểm định kỳ xem bản đang chạy có lệch repo không:

```bash
for f in backup_daily.sh backup_to_github.sh backup_source.sh cleanup_preview_cache.sh; do
    diff -q "/opt/kpi/scripts/$f" "/opt/kpi-prod/scripts/$f" >/dev/null 2>&1 \
        && echo "  $f KHỚP" || echo "  $f ⚠️ LỆCH repo"
done
```

---

## Lịch sử phiên bản uploads

Từ 25/08/2026 `backup_daily.sh` chụp ảnh hardlink gương uploads **trước** mỗi
lần rsync, giữ 60 bản (= 30 ngày ở nhịp 2 lần/ngày):

```
/var/backup/kpi_haiquan/uploads/                gương hiện tại (rsync --delete)
/var/backup/kpi_haiquan/uploads_snapshots/<ts>/ ảnh trước mỗi lần chạy
```

**Khôi phục một file bị xóa nhầm hoặc ghi đè hỏng:**

```bash
ls /var/backup/kpi_haiquan/uploads_snapshots/          # chọn mốc TRƯỚC lúc hỏng
SNAP=/var/backup/kpi_haiquan/uploads_snapshots/20260825_0933
find "$SNAP" -name '<tên-file>*'                       # tìm đúng đường dẫn
cp -a "$SNAP/<đường/dẫn>" /var/data/kpi/uploads/<đường/dẫn>
```

> Ảnh dùng hardlink nên `du -sh` từng thư mục sẽ **cộng dồn sai** (mỗi ảnh trông
> như 6,9 GB). Xem dung lượng thật của cả kho:
> `du -sh --one-file-system /var/backup/kpi_haiquan`

Đổi số bản giữ lại bằng biến `UPLOADS_SNAPSHOT_KEEP` (mặc định 60).

⚠️ **Không bao giờ thêm cờ `--inplace` vào lệnh rsync** trong script. Lịch sử an
toàn được là nhờ rsync ghi file tạm rồi đổi tên (tạo inode mới); `--inplace` ghi
đè thẳng vào inode đang được các ảnh chia sẻ và làm hỏng toàn bộ lịch sử.

---

## 1. Backup daily — `backup_daily.sh`

### 1.1. Tạo target directory + permission

```bash
sudo mkdir -p /var/backup/kpi_haiquan/{daily,monthly,uploads}
sudo chown root:root /var/backup/kpi_haiquan
sudo chmod 700 /var/backup/kpi_haiquan
```

### 1.2. Copy script + set permission

```bash
sudo mkdir -p /opt/kpi/scripts
sudo cp /root/kpi-haiquan/scripts/backup_daily.sh /opt/kpi/scripts/
sudo cp /root/kpi-haiquan/scripts/cleanup_preview_cache.sh /opt/kpi/scripts/
sudo chmod 700 /opt/kpi/scripts/*.sh
sudo chown root:root /opt/kpi/scripts/*.sh
```

### 1.3. Đặt PGPASSWORD an toàn

KHÔNG hardcode PGPASSWORD trong script. Dùng `.pgpass`:

```bash
sudo bash -c 'cat > /root/.pgpass <<EOF
localhost:5432:kpi_haiquan:kpi_user:<PASSWORD_THẬT>
EOF'
sudo chmod 600 /root/.pgpass
```

Cập nhật `backup_daily.sh` để KHÔNG cần `PGPASSWORD` env (đã dùng .pgpass tự động). Hoặc giữ nguyên + export trước khi cron chạy:

```bash
sudo bash -c 'cat > /etc/profile.d/kpi_backup.sh <<EOF
export PGPASSWORD="<PASSWORD_THẬT>"
EOF'
sudo chmod 600 /etc/profile.d/kpi_backup.sh
```

### 1.4. Test thủ công lần đầu

```bash
sudo HKG_UPLOAD_DIR=/var/data/hkg/uploads /opt/kpi/scripts/backup_daily.sh
ls -lh /var/backup/kpi_haiquan/daily/
# Verify: file db_<TIMESTAMP>.sql.gz tồn tại, size > 1MB
```

Verify dump không corrupt:
```bash
gunzip -c /var/backup/kpi_haiquan/daily/db_*.sql.gz | head -20
# Phải thấy "PostgreSQL database dump"
```

### 1.5. Cài cron

```bash
sudo bash -c 'cat > /etc/cron.d/hkg-backups <<EOF
# Phase 4.1 P0 — KPI/HKG backup + cleanup
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HKG_UPLOAD_DIR=/var/data/hkg/uploads

# Daily 02:00 — full DB + uploads backup
0 2 * * * root /opt/kpi/scripts/backup_daily.sh >> /var/log/backup_kpi.log 2>&1

# Sunday 03:00 — cleanup preview cache cũ
0 3 * * 0 root /opt/kpi/scripts/cleanup_preview_cache.sh >> /var/log/cleanup_cache.log 2>&1
EOF'
sudo chmod 644 /etc/cron.d/hkg-backups
sudo systemctl restart cron
```

### 1.6. Verify cron

```bash
sudo crontab -l -u root  # /etc/cron.d/hkg-backups visible
sudo grep CRON /var/log/syslog | tail -5
```

---

## 2. PM2 logrotate

### 2.1. Cài plugin

```bash
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 50M
pm2 set pm2-logrotate:retain 7
pm2 set pm2-logrotate:compress true
pm2 set pm2-logrotate:rotateInterval '0 0 * * *'  # daily 00:00
pm2 save
```

### 2.2. Verify

```bash
pm2 list                   # thấy pm2-logrotate online
pm2 conf pm2-logrotate     # config đúng
```

---

## 3. Rate limit upload

Đã tích hợp sẵn trong `meeting_service`:
- Decorator `@limiter.limit("10/5minutes")` trên `POST /tai-lieu/upload`
- Limit theo IP (fallback) hoặc user_id nếu middleware populate
- Disable trong test bằng `HKG_DISABLE_RATE_LIMIT=true`

### 3.1. Verify thủ công sau deploy

```bash
# Login lấy JWT
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -d 'username=...&password=...' | jq -r '.access_token')

# Spam 11 upload trong vòng 5 phút
for i in $(seq 1 11); do
  echo "Upload $i:"
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8006/api/v1/hop-khong-giay/tai-lieu/upload \
    -H "Authorization: Bearer $TOKEN" \
    -F "cuoc_hop_id=<UUID>" \
    -F "file=@test.pdf"
done
# Expected: 1-10 → 201, 11 → 429
```

---

## 4. Rollback

### Tắt cron tạm thời

```bash
sudo rm /etc/cron.d/hkg-backups
sudo systemctl restart cron
```

### Tắt rate limit (emergency)

Set env `HKG_DISABLE_RATE_LIMIT=true` trong `ecosystem.config.js` cho `meeting_service` rồi `pm2 reload meeting_service`.

### Uninstall pm2-logrotate

```bash
pm2 uninstall pm2-logrotate
pm2 save
```
