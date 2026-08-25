#!/usr/bin/env bash
# backup_daily.sh — Phase 4.1 P0 Hardening
# ─────────────────────────────────────────────────────────────────────
# Backup hàng ngày: pg_dump DB kpi_haiquan + rsync HKG_UPLOAD_DIR.
# Daily retention 30 ngày + monthly snapshot 12 tháng.
#
# Uploads có 2 lớp:
#   uploads/                      gương hiện tại (rsync --delete)
#   uploads_snapshots/<ts>/       ảnh hardlink TRƯỚC mỗi lần rsync, giữ 60 bản
#                                 (= 30 ngày ở nhịp 2 lần/ngày)
# Khôi phục 1 file đã xóa nhầm:
#   ls /var/backup/kpi_haiquan/uploads_snapshots/            # chọn mốc thời gian
#   cp -a /var/backup/kpi_haiquan/uploads_snapshots/<ts>/<đường/dẫn/file> \
#         /var/data/kpi/uploads/<đường/dẫn/file>
# Ảnh dùng hardlink nên `du -sh` từng thư mục sẽ CỘNG DỒN sai; xem dung lượng
# thật của cả kho bằng: du -sh --one-file-system /var/backup/kpi_haiquan
#
# Cron: 0 2 * * * root /opt/kpi/scripts/backup_daily.sh >> /var/log/backup_kpi.log 2>&1
#
# Required env vars (override khi gọi để test ở local):
#   DB_NAME       (default kpi_haiquan)
#   DB_USER       (default kpi_user)
#   DB_HOST       (default localhost)
#   DB_PORT       (default 5432)
#   PGPASSWORD    (REQUIRED — prod đặt trong /etc/pgpass.conf hoặc env)
#   HKG_UPLOAD_DIR (production: /var/data/hkg/uploads)
#   BACKUP_ROOT   (default /var/backup/kpi_haiquan; override khi smoke-test)
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

# ─── Config ──────────────────────────────────────────────────────────
DB_NAME="${DB_NAME:-kpi_haiquan}"
DB_USER="${DB_USER:-kpi_user}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
HKG_UPLOAD_DIR="${HKG_UPLOAD_DIR:-/var/data/hkg/uploads}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backup/kpi_haiquan}"

DAILY_DIR="${BACKUP_ROOT}/daily"
MONTHLY_DIR="${BACKUP_ROOT}/monthly"
UPLOADS_DIR="${BACKUP_ROOT}/uploads"
UPLOADS_SNAP_DIR="${BACKUP_ROOT}/uploads_snapshots"

DAILY_RETENTION_DAYS=30
MONTHLY_RETENTION_DAYS=400  # ~12 tháng + buffer
UPLOADS_SNAPSHOT_KEEP="${UPLOADS_SNAPSHOT_KEEP:-60}"  # 2 lần/ngày × 30 ngày

TIMESTAMP="$(date +%Y%m%d_%H%M)"
DAY_OF_MONTH="$(date +%d)"

# ─── Helpers ─────────────────────────────────────────────────────────
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
die() { log "FATAL: $*"; exit 1; }

# Auth: chấp nhận PGPASSWORD env HOẶC ~/.pgpass file (chuẩn PostgreSQL).
# Production khuyến nghị dùng .pgpass (chmod 600) thay vì hardcode env.
if [ -z "${PGPASSWORD:-}" ] && [ ! -f "$HOME/.pgpass" ]; then
    die "Thiếu auth: set PGPASSWORD env HOẶC tạo $HOME/.pgpass (chmod 600)"
fi

mkdir -p "$DAILY_DIR" "$MONTHLY_DIR" "$UPLOADS_DIR" "$UPLOADS_SNAP_DIR"

# ─── Pre-check: disk space ───────────────────────────────────────────
log "Pre-check disk space..."
DB_SIZE_BYTES=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT pg_database_size('$DB_NAME')")
AVAIL_BYTES=$(df -B1 "$BACKUP_ROOT" | awk 'NR==2 {print $4}')
REQUIRED=$((DB_SIZE_BYTES * 2))

if [ "$AVAIL_BYTES" -lt "$REQUIRED" ]; then
    die "Không đủ disk space. DB size=${DB_SIZE_BYTES}B, cần=${REQUIRED}B, còn=${AVAIL_BYTES}B"
fi
log "Disk OK: DB=${DB_SIZE_BYTES}B, available=${AVAIL_BYTES}B"

# ─── 1. pg_dump ──────────────────────────────────────────────────────
DUMP_FILE="${DAILY_DIR}/db_${TIMESTAMP}.sql.gz"
log "pg_dump → $DUMP_FILE"
pg_dump \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
    --no-owner --no-acl --clean --if-exists \
    "$DB_NAME" \
    | gzip -9 > "$DUMP_FILE"

# Verify dump không corrupt — gzip integrity (gzip -t) + size > 1MB
if ! gzip -t "$DUMP_FILE" 2>/dev/null; then
    die "Dump corrupt — gzip integrity check FAIL ($DUMP_FILE)"
fi
DUMP_SIZE=$(stat -c%s "$DUMP_FILE")
if [ "$DUMP_SIZE" -lt 1048576 ]; then
    die "Dump corrupt hoặc DB rỗng — size=${DUMP_SIZE}B (<1MB)"
fi
log "pg_dump OK (${DUMP_SIZE}B, gzip integrity OK)"

# ─── 2. Chụp ảnh gương uploads TRƯỚC khi ghi đè ──────────────────────
# rsync --delete biến $UPLOADS_DIR thành GƯƠNG, không phải kho lưu trữ: file bị
# xóa nhầm hay ghi đè hỏng lúc 08:00 thì 14:00 backup mất theo, không có bản cũ
# để quay lui. Chụp ảnh bằng hardlink (cp -al) trước mỗi lần rsync: file không
# đổi chỉ tốn thêm inode + mục thư mục, nên 30 ngày lịch sử gần như miễn phí đĩa.
#
# An toàn được là nhờ rsync ghi ra file tạm rồi đổi tên (inode MỚI), không sửa
# tại chỗ — ảnh cũ giữ nguyên nội dung. TUYỆT ĐỐI không thêm cờ --inplace vào
# lệnh rsync bên dưới: nó sẽ ghi đè thẳng vào inode đang được ảnh chia sẻ và
# làm hỏng toàn bộ lịch sử.
if [ -d "$UPLOADS_DIR" ] && find "$UPLOADS_DIR" -mindepth 1 -print -quit | grep -q .; then
    SNAP_DEST="${UPLOADS_SNAP_DIR}/${TIMESTAMP}"
    if [ -e "$SNAP_DEST" ]; then
        log "WARN: ảnh $TIMESTAMP đã tồn tại, bỏ qua (script chạy 2 lần trong cùng phút?)"
    elif cp -al "$UPLOADS_DIR" "$SNAP_DEST" 2>/dev/null; then
        log "Ảnh uploads → $SNAP_DEST ($(find "$SNAP_DEST" -type f | wc -l) file, hardlink)"
    else
        log "WARN: không tạo được ảnh hardlink ($SNAP_DEST) — vẫn tiếp tục rsync"
        rm -rf "$SNAP_DEST" 2>/dev/null || true
    fi
else
    log "Gương uploads còn rỗng — lần chạy đầu, chưa có gì để chụp ảnh"
fi

# ─── 3. rsync uploads (loại trừ preview cache) ───────────────────────
if [ -d "$HKG_UPLOAD_DIR" ]; then
    log "rsync $HKG_UPLOAD_DIR → $UPLOADS_DIR"
    rsync -a --delete \
        --exclude='_preview_cache/' \
        "${HKG_UPLOAD_DIR}/" "${UPLOADS_DIR}/"
    log "rsync OK"
else
    log "WARN: HKG_UPLOAD_DIR không tồn tại ($HKG_UPLOAD_DIR), skip rsync"
fi

# ─── 4. Monthly snapshot ngày 1 ──────────────────────────────────────
if [ "$DAY_OF_MONTH" = "01" ]; then
    MONTHLY_FILE="${MONTHLY_DIR}/db_$(date +%Y%m).sql.gz"
    log "Tạo monthly snapshot → $MONTHLY_FILE"
    cp "$DUMP_FILE" "$MONTHLY_FILE"
fi

# ─── 5. Retention ────────────────────────────────────────────────────
DAILY_DELETED=$(find "$DAILY_DIR" -name 'db_*.sql.gz' -mtime "+${DAILY_RETENTION_DAYS}" -delete -print | wc -l)
log "Cleanup daily older than ${DAILY_RETENTION_DAYS} days: deleted ${DAILY_DELETED} file(s)"

MONTHLY_DELETED=$(find "$MONTHLY_DIR" -name 'db_*.sql.gz' -mtime "+${MONTHLY_RETENTION_DAYS}" -delete -print | wc -l)
log "Cleanup monthly older than ${MONTHLY_RETENTION_DAYS} days: deleted ${MONTHLY_DELETED} file(s)"

# Ảnh uploads: cắt theo SỐ LƯỢNG, sắp theo TÊN — không dùng -mtime vì cp -al giữ
# nguyên mtime của thư mục nguồn, ngày sửa không phản ánh lúc chụp ảnh.
SNAP_DELETED=0
while IFS= read -r old_snap; do
    [ -n "$old_snap" ] || continue
    rm -rf "${UPLOADS_SNAP_DIR:?}/${old_snap}"
    SNAP_DELETED=$((SNAP_DELETED + 1))
done < <(ls -1 "$UPLOADS_SNAP_DIR" 2>/dev/null | sort | head -n "-${UPLOADS_SNAPSHOT_KEEP}")
SNAP_LEFT=$(ls -1 "$UPLOADS_SNAP_DIR" 2>/dev/null | wc -l)
log "Cleanup ảnh uploads (giữ ${UPLOADS_SNAPSHOT_KEEP} bản gần nhất): xóa ${SNAP_DELETED}, còn ${SNAP_LEFT}"

log "Backup completed successfully"
