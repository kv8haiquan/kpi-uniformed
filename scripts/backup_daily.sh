#!/usr/bin/env bash
# backup_daily.sh — Phase 4.1 P0 Hardening
# ─────────────────────────────────────────────────────────────────────
# Backup hàng ngày: pg_dump DB kpi_haiquan + rsync HKG_UPLOAD_DIR.
# Daily retention 30 ngày + monthly snapshot 12 tháng.
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

DAILY_RETENTION_DAYS=30
MONTHLY_RETENTION_DAYS=400  # ~12 tháng + buffer

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

mkdir -p "$DAILY_DIR" "$MONTHLY_DIR" "$UPLOADS_DIR"

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

# Verify dump không corrupt — size > 1MB (DB thật chắc chắn lớn hơn)
DUMP_SIZE=$(stat -c%s "$DUMP_FILE")
if [ "$DUMP_SIZE" -lt 1048576 ]; then
    die "Dump corrupt hoặc DB rỗng — size=${DUMP_SIZE}B (<1MB)"
fi
log "pg_dump OK (${DUMP_SIZE}B)"

# ─── 2. rsync uploads (loại trừ preview cache) ───────────────────────
if [ -d "$HKG_UPLOAD_DIR" ]; then
    log "rsync $HKG_UPLOAD_DIR → $UPLOADS_DIR"
    rsync -a --delete \
        --exclude='_preview_cache/' \
        "${HKG_UPLOAD_DIR}/" "${UPLOADS_DIR}/"
    log "rsync OK"
else
    log "WARN: HKG_UPLOAD_DIR không tồn tại ($HKG_UPLOAD_DIR), skip rsync"
fi

# ─── 3. Monthly snapshot ngày 1 ──────────────────────────────────────
if [ "$DAY_OF_MONTH" = "01" ]; then
    MONTHLY_FILE="${MONTHLY_DIR}/db_$(date +%Y%m).sql.gz"
    log "Tạo monthly snapshot → $MONTHLY_FILE"
    cp "$DUMP_FILE" "$MONTHLY_FILE"
fi

# ─── 4. Retention ────────────────────────────────────────────────────
DAILY_DELETED=$(find "$DAILY_DIR" -name 'db_*.sql.gz' -mtime "+${DAILY_RETENTION_DAYS}" -delete -print | wc -l)
log "Cleanup daily older than ${DAILY_RETENTION_DAYS} days: deleted ${DAILY_DELETED} file(s)"

MONTHLY_DELETED=$(find "$MONTHLY_DIR" -name 'db_*.sql.gz' -mtime "+${MONTHLY_RETENTION_DAYS}" -delete -print | wc -l)
log "Cleanup monthly older than ${MONTHLY_RETENTION_DAYS} days: deleted ${MONTHLY_DELETED} file(s)"

log "Backup completed successfully"
