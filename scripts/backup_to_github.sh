#!/usr/bin/env bash
# =============================================================================
# backup_to_github.sh — Đẩy backup DB ĐÃ MÃ HÓA lên private GitHub repo (off-site)
# =============================================================================
# Chạy SAU backup_daily.sh. CHỈ đẩy file .gpg — KHÔNG BAO GIỜ đẩy dump thô (PII).
# Phòng hỏng đĩa: backup hiện nằm cùng đĩa với DB, copy này nằm trên GitHub.
#
# ┌─ TRƯỚC KHI DÙNG, phải chuẩn bị (xem hướng dẫn cuối file): ──────────────┐
# │ 1. Tạo repo PRIVATE rỗng trên GitHub (vd: kpi-db-backups)               │
# │ 2. Tạo passphrase mã hóa + LƯU OFFLINE (mất passphrase = mất backup):   │
# │      openssl rand -base64 32 > /root/.kpi_backup_passphrase             │
# │      chmod 600 /root/.kpi_backup_passphrase                             │
# │ 3. Clone repo private đó về GH_REPO_DIR (auth bằng SSH key, xem #3)     │
# └────────────────────────────────────────────────────────────────────────┘
set -euo pipefail

# ===== Config (override qua env nếu cần) =====
BACKUP_SRC_DIR="${BACKUP_SRC_DIR:-/var/backup/kpi_haiquan/daily}"
GH_REPO_DIR="${GH_REPO_DIR:-/var/backup/kpi-db-backups-git}"      # local clone repo private
GPG_PASSPHRASE_FILE="${GPG_PASSPHRASE_FILE:-/root/.kpi_backup_passphrase}"
KEEP_ON_GITHUB="${KEEP_ON_GITHUB:-14}"                            # giữ N bản .gpg gần nhất

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
die() { echo "FATAL: $*" >&2; exit 1; }

# ===== Pre-check =====
[ -f "$GPG_PASSPHRASE_FILE" ] || die "Thiếu passphrase file: $GPG_PASSPHRASE_FILE (xem hướng dẫn)"
[ -d "$GH_REPO_DIR/.git" ]    || die "Chưa clone repo private vào $GH_REPO_DIR (xem hướng dẫn)"

# ===== 1. Lấy dump mới nhất =====
LATEST="$(ls -t "$BACKUP_SRC_DIR"/db_*.sql.gz 2>/dev/null | head -1 || true)"
[ -n "$LATEST" ] || die "Không tìm thấy dump nào trong $BACKUP_SRC_DIR"
BASE="$(basename "$LATEST" .sql.gz)"
ENC_FILE="${GH_REPO_DIR}/${BASE}.sql.gz.gpg"

# Idempotent: dump này đã được đẩy lên (đã commit) thì bỏ qua — tránh commit thừa
if git -C "$GH_REPO_DIR" ls-files --error-unmatch "${BASE}.sql.gz.gpg" >/dev/null 2>&1; then
    log "Dump ${BASE} đã có trên GitHub — bỏ qua"
    exit 0
fi

# ===== 2. Mã hóa AES256 (chỉ file .gpg vào repo) =====
log "Mã hóa $LATEST → ${BASE}.sql.gz.gpg"
gpg --batch --yes --symmetric --cipher-algo AES256 \
    --passphrase-file "$GPG_PASSPHRASE_FILE" \
    -o "$ENC_FILE" "$LATEST"

# ===== 3. Prune: giữ N bản .gpg gần nhất =====
ls -t "${GH_REPO_DIR}"/db_*.sql.gz.gpg 2>/dev/null | tail -n +$((KEEP_ON_GITHUB + 1)) | while read -r old; do
    rm -f "$old"; log "prune $(basename "$old")"
done

# ===== 4. Commit + push =====
cd "$GH_REPO_DIR"
git add -A
if git diff --cached --quiet; then
    log "Không có thay đổi để push"
else
    git commit -q -m "Backup DB ${BASE} (encrypted AES256)"
    git push -q origin HEAD && log "Đã push lên GitHub OK"
fi
log "Hoàn tất off-site backup"

# =============================================================================
# GIẢI MÃ KHI CẦN KHÔI PHỤC:
#   gpg --batch --decrypt --passphrase-file /root/.kpi_backup_passphrase \
#       db_YYYYMMDD_HHMM.sql.gz.gpg > db.sql.gz
#   zcat db.sql.gz | sudo -u postgres psql -d kpi_restore   # LUÔN vào DB tạm
# =============================================================================
