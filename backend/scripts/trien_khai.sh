#!/usr/bin/env bash
# =============================================================================
# trien_khai.sh — Triển khai lên production
# =============================================================================
# Chạy TỪ cây prod (/opt/kpi-prod), không phải từ cây phát triển.
#
#   /opt/kpi-prod/backend/scripts/trien_khai.sh <commit-hoặc-tag>
#
# THỨ TỰ BẮT BUỘC: lấy code → cài thư viện → CHẠY MIGRATION → nạp code mới.
# Sự cố 18/08/2026 xảy ra vì làm ngược: code mới lên trước migration, model
# tham chiếu cột chưa tồn tại, cả module Họp Không Giấy ngừng hoạt động.
#
# Script dừng ngay khi có bước lỗi (set -e), không nạp code nửa vời.
# =============================================================================
set -euo pipefail

CAY_PROD="${CAY_PROD:-/opt/kpi-prod}"
DICH="${1:-}"

DICH_VU_BE=(kpi-backend lms-backend forum-backend legal-backend
            portal-backend common-backend meeting-backend chi-tieu-backend
            zalo-worker)

log() { echo "[$(date '+%H:%M:%S')] $*"; }
loi() { echo "⛔ $*" >&2; exit 1; }

[ -n "$DICH" ] || loi "Thiếu tham số. Dùng: trien_khai.sh <commit|tag>"
[ -d "$CAY_PROD/.git" ] || [ -f "$CAY_PROD/.git" ] || loi "$CAY_PROD không phải cây git"

cd "$CAY_PROD"

# ── 0. Ghi mốc để quay lui ───────────────────────────────────────────────
TRUOC=$(git rev-parse HEAD)
log "Đang chạy : $(git rev-parse --short HEAD)"
log "Sẽ chuyển : $DICH"
log "Quay lui  : $CAY_PROD/backend/scripts/trien_khai.sh $TRUOC"

# ── 1. Lấy code ──────────────────────────────────────────────────────────
log "Lấy code từ remote…"
git fetch --all --tags --quiet
git checkout --quiet "$DICH"
log "Đã ở $(git rev-parse --short HEAD) — $(git log -1 --format=%s)"

# ── 2. Thư viện ──────────────────────────────────────────────────────────
if ! git diff --quiet "$TRUOC" HEAD -- backend/requirements.txt; then
    log "requirements.txt có thay đổi → cài lại"
    backend/venv/bin/pip install -q -r backend/requirements.txt
fi

if ! git diff --quiet "$TRUOC" HEAD -- frontend/package-lock.json; then
    log "package-lock.json có thay đổi → npm ci"
    (cd frontend && npm ci --silent)
fi

# ── 3. MIGRATION — trước khi nạp code mới ────────────────────────────────
log "Alembic hiện tại: $(cd backend && venv/bin/alembic current 2>/dev/null | tail -1)"
log "Chạy migration…"
(cd backend && venv/bin/alembic upgrade head)
log "Alembic sau khi chạy: $(cd backend && venv/bin/alembic current 2>/dev/null | tail -1)"

# ── 4. Build frontend ────────────────────────────────────────────────────
if ! git diff --quiet "$TRUOC" HEAD -- frontend/; then
    log "Frontend có thay đổi → build"
    (cd frontend && npm run build)
fi

# ── 5. Nạp code mới ──────────────────────────────────────────────────────
log "Nạp lại các dịch vụ…"
for dv in "${DICH_VU_BE[@]}"; do
    pm2 reload "$dv" --update-env >/dev/null 2>&1 || log "  ! không reload được $dv"
done
pm2 reload kpi-frontend --update-env >/dev/null 2>&1 || log "  ! không reload được kpi-frontend"
sleep 8

# ── 6. Kiểm tra ──────────────────────────────────────────────────────────
log "Kiểm tra sức khoẻ…"
declare -A CONG=([kpi-backend]=8000 [lms-backend]=8001 [forum-backend]=8002
                 [legal-backend]=8003 [portal-backend]=8004 [common-backend]=8005
                 [meeting-backend]=8006 [chi-tieu-backend]=8007)
that_bai=0
for dv in "${!CONG[@]}"; do
    ma=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 \
         "http://127.0.0.1:${CONG[$dv]}/health" 2>/dev/null || echo 000)
    if [ "$ma" = "200" ]; then
        printf "   ✅ %-20s %s\n" "$dv" "$ma"
    else
        printf "   ❌ %-20s %s\n" "$dv" "$ma"
        that_bai=$((that_bai + 1))
    fi
done

if [ "$that_bai" -gt 0 ]; then
    echo
    loi "$that_bai dịch vụ không lên. Quay lui: $0 $TRUOC"
fi

# ── 7. Gắn nhánh prod vào đúng code vừa nạp ──────────────────────────────
# Triển khai bằng SHA/tag thì `git checkout` ở bước 1 để lại detached HEAD —
# code phục vụ người dùng nằm NGOÀI mọi nhánh. Sự cố 25/08/2026: cây prod ở
# 40de07e trong khi nhánh prod còn 73c994f; lần `git checkout prod` kế tiếp
# sẽ âm thầm quay lui, mất bản vá đang chạy.
MOI=$(git rev-parse HEAD)
if [ "$(git rev-parse --verify --quiet prod || true)" != "$MOI" ]; then
    if git merge-base --is-ancestor prod "$MOI" 2>/dev/null; then
        log "Dời nhánh prod tới $(git rev-parse --short "$MOI") (fast-forward)"
    else
        log "⚠️  $(git rev-parse --short "$MOI") KHÔNG phải hậu duệ của prod —"
        log "    đây là quay lui hoặc rẽ nhánh. Nhánh prod sẽ trỏ lại mốc này."
    fi
    git branch -f prod "$MOI"
fi
git checkout --quiet prod
log "Đã gắn nhánh: $(git rev-parse --abbrev-ref HEAD) → $(git rev-parse --short HEAD)"

# ── 8. Ghi mốc ───────────────────────────────────────────────────────────
log "✅ Triển khai xong: $(git rev-parse --short HEAD)"
log "Còn 2 việc thủ công:"
log "  1. git push origin prod   (và ff main theo prod)"
log "  2. cập nhật docs/van-hanh/PHIEN_BAN_PROD.md"
pm2 save >/dev/null 2>&1 || true
