#!/usr/bin/env bash
# cleanup_preview_cache.sh — Phase 4.1 P0 Hardening
# ─────────────────────────────────────────────────────────────────────
# Xóa file PDF preview cache cũ hơn 30 ngày để tránh phình storage.
# Preview cache do `meeting_service/services/preview_service.py` tạo từ
# Office files (DOCX/XLSX/PPTX) qua LibreOffice convert.
#
# Cron: 0 3 * * 0 root /opt/kpi/scripts/cleanup_preview_cache.sh >> /var/log/cleanup_cache.log 2>&1
#       (mỗi Chủ Nhật 03:00)
#
# Required env vars:
#   HKG_UPLOAD_DIR (production: /var/data/hkg/uploads)
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

HKG_UPLOAD_DIR="${HKG_UPLOAD_DIR:-/var/data/hkg/uploads}"
CACHE_DIR="${HKG_UPLOAD_DIR}/_preview_cache"
RETENTION_DAYS="${PREVIEW_RETENTION_DAYS:-30}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# Fail-safe: nếu thư mục không tồn tại, log và exit 0 (KHÔNG fail cron)
if [ ! -d "$CACHE_DIR" ]; then
    log "Preview cache dir không tồn tại ($CACHE_DIR), skip"
    exit 0
fi

# Đếm trước/sau để log có ích
BEFORE=$(find "$CACHE_DIR" -name '*.pdf' -type f | wc -l)
log "Tìm thấy $BEFORE file PDF trong cache"

DELETED=$(find "$CACHE_DIR" -name '*.pdf' -type f -mtime "+${RETENTION_DAYS}" -delete -print | wc -l)
log "Đã xóa $DELETED file (cũ hơn ${RETENTION_DAYS} ngày)"

AFTER=$(find "$CACHE_DIR" -name '*.pdf' -type f | wc -l)
log "Còn lại $AFTER file"
