#!/usr/bin/env bash
# =============================================================================
# backup_source.sh — Auto-backup SOURCE CODE lên GitHub (snapshot an toàn)
# =============================================================================
# Snapshot TOÀN BỘ working tree (KỂ CẢ thay đổi chưa commit) vào branch riêng
# 'auto-backup' rồi push. KHÔNG đụng chạm branch đang làm việc / index / file.
# Mục đích: nếu đĩa hỏng, code chưa kịp commit cũng không mất.
#
# Cron gợi ý (sau DB backup): 45 2 * * * root /opt/kpi/scripts/backup_source.sh
# Tôn trọng .gitignore (venv/, node_modules/, .env... KHÔNG bị đẩy).
# =============================================================================
set -euo pipefail

REPO="${REPO:-/root/kpi-haiquan}"
BACKUP_BRANCH="${BACKUP_BRANCH:-auto-backup}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

cd "$REPO"
CUR_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"

# ===== Snapshot working tree vào 1 tree object qua INDEX TẠM =====
# GIT_INDEX_FILE trỏ index tạm -> KHÔNG đụng .git/index thật của anh.
TMP_INDEX="$(mktemp)"
export GIT_INDEX_FILE="$TMP_INDEX"
git read-tree HEAD            # khởi tạo index tạm = HEAD
git add -A                    # stage mọi thay đổi working tree vào index tạm (theo .gitignore)
TREE="$(git write-tree)"
unset GIT_INDEX_FILE
rm -f "$TMP_INDEX"

# ===== Parent = commit auto-backup trước (nối lịch sử), lần đầu = HEAD =====
PARENT="$(git rev-parse --verify --quiet "refs/heads/${BACKUP_BRANCH}" || true)"
[ -n "$PARENT" ] || PARENT="$(git rev-parse HEAD)"

# ===== Bỏ qua nếu không có gì thay đổi so với snapshot trước =====
if [ "$TREE" = "$(git rev-parse "${PARENT}^{tree}")" ]; then
    log "Source không đổi so với snapshot trước → bỏ qua"
    exit 0
fi

MSG="Auto backup source: $(date +%Y%m%d_%H%M%S) (từ branch ${CUR_BRANCH})"
COMMIT="$(git commit-tree "$TREE" -p "$PARENT" -m "$MSG")"
git update-ref "refs/heads/${BACKUP_BRANCH}" "$COMMIT"

git push -q origin "${BACKUP_BRANCH}" && log "Đã push '${BACKUP_BRANCH}': $MSG"

# =============================================================================
# XEM / KHÔI PHỤC snapshot:
#   git fetch origin auto-backup
#   git log origin/auto-backup            # xem các bản snapshot
#   git checkout origin/auto-backup -- <đường/dẫn/file>   # lấy lại 1 file
# =============================================================================
