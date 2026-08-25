#!/usr/bin/env bash
# =============================================================================
# build_frontend.sh — Build frontend an toàn trên máy đang phục vụ người dùng
# =============================================================================
#   backend/scripts/build_frontend.sh            # build cây chứa script này
#   backend/scripts/build_frontend.sh /opt/kpi-prod
#
# DÙNG LỆNH NÀY THAY CHO `npm run build`.
#
# ── Vì sao ───────────────────────────────────────────────────────────────────
# Sự cố 25/08/2026: `npm run build` chạy trần trong /root/kpi-haiquan/frontend
# lúc 10:03:43, đúng lúc 13 thí sinh đang thi ĐGNL. Hai tiến trình build ngốn
# ~1,4GB; cộng với next-server dev 1,24GB, lms-backend 1,23GB, PostgreSQL 1,2GB,
# hai phiên Claude Code 0,8GB và VSCode Server 0,4GB thì 7,8GB RAM cạn sạch.
# Vùng Normal tụt xuống dưới ngưỡng min của kernel → fork() treo, SSH không vào
# được, nginx gần như câm suốt 12 phút, OOM-killer bắn chết next-server.
#
# Bản thân máy dev và máy prod là MỘT (79.108.216.189). Build ở cây dev vẫn
# giết prod. Vì vậy script này áp dụng cho cả hai cây.
#
# ── Hai lớp bảo vệ ───────────────────────────────────────────────────────────
# 1. Không build khi đang có người thi          → kiem_tra_ky_thi.sh
# 2. Nhốt build trong cgroup có trần bộ nhớ     → systemd-run --scope
#    Vượt trần thì CHỈ build chết, máy vẫn sống. Trước đây thì ngược lại.
# =============================================================================
set -euo pipefail

GOC="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
CHAN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/kiem_tra_ky_thi.sh"

# Trần bộ nhớ cho tiến trình build. Đợt build 25/08 dùng ~1,4GB nên 3G là rộng
# rãi; MemoryHigh ép nó nhả sớm trước khi chạm trần cứng.
TRAN_CUNG="${TRAN_CUNG:-3G}"
TRAN_MEM="${TRAN_MEM:-2G}"

# Trần swap — BẮT BUỘC phải đặt, không được bỏ.
# Kiểm chứng 25/08: chỉ đặt MemoryMax=200M thì tiến trình xin 500MB VẪN CHẠY
# trót lọt, vì memory.swap.max mặc định là `max` nên phần vượt trần trôi hết
# xuống swap. RAM chủ được bảo vệ, nhưng build có thể nuốt sạch 8GB swap và
# làm cả máy giật vì đảo trang. Đặt thêm MemorySwapMax=1G thì tiến trình vi
# phạm bị cgroup giết bằng SIGKILL (mã 137) còn máy chủ không suy suyển.
TRAN_SWAP="${TRAN_SWAP:-1G}"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

[ -d "$GOC/frontend" ] || { echo "⛔ Không thấy $GOC/frontend" >&2; exit 1; }

# ── 1. Chốt chặn kỳ thi ──────────────────────────────────────────────────────
log "Kiểm tra kỳ thi đang diễn ra…"
MOI_TRUONG="$GOC/backend/.env" "$CHAN"

# ── 2. Cảnh báo nếu RAM đã eo hẹp ────────────────────────────────────────────
KHA_DUNG=$(awk '/^MemAvailable:/{print int($2/1024)}' /proc/meminfo)
log "RAM khả dụng: ${KHA_DUNG}MB — swap: $(awk '/^SwapTotal:/{print int($2/1024)}' /proc/meminfo)MB"
if [ "$KHA_DUNG" -lt 1500 ]; then
    log "⚠️  Dưới 1,5GB khả dụng. Build vẫn chạy (đã có trần $TRAN_MEM) nhưng sẽ chậm."
fi

# ── 3. Build trong hộp giới hạn ──────────────────────────────────────────────
cd "$GOC/frontend"
if command -v systemd-run >/dev/null 2>&1; then
    log "Build trong cgroup: RAM≤$TRAN_CUNG (ép nhả từ $TRAN_MEM), swap≤$TRAN_SWAP"
    if ! systemd-run --scope --quiet --collect \
            --unit="build-frontend-$$" \
            -p MemoryHigh="$TRAN_MEM" \
            -p MemoryMax="$TRAN_CUNG" \
            -p MemorySwapMax="$TRAN_SWAP" \
            -p CPUWeight=20 \
            -p IOWeight=20 \
            nice -n 19 npm run build; then
        MA=$?
        if [ "$MA" -eq 137 ]; then
            echo "⛔ Build vượt trần bộ nhớ và đã bị dừng — MÁY CHỦ VẪN AN TOÀN." >&2
            echo "   Nới trần rồi chạy lại, ví dụ:" >&2
            echo "   TRAN_CUNG=4G TRAN_MEM=3G $0 $GOC" >&2
        fi
        exit "$MA"
    fi
else
    log "⚠️  Không có systemd-run — chỉ hạ ưu tiên, KHÔNG có trần bộ nhớ."
    nice -n 19 npm run build
fi

log "✅ Build xong: $GOC/frontend/.next"
