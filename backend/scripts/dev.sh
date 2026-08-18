#!/usr/bin/env bash
# =============================================================================
# dev.sh — Chạy môi trường PHÁT TRIỂN song song với production
# =============================================================================
#   scripts/dev.sh chay [dịch-vụ...]   khởi động (mặc định: kpi meeting frontend)
#   scripts/dev.sh dung                dừng toàn bộ dịch vụ dev
#   scripts/dev.sh trang-thai          xem đang chạy gì
#   scripts/dev.sh lam-moi-db          tạo lại kpi_haiquan_test từ bản sao prod
#   scripts/dev.sh test [tham số...]   chạy pytest trên DB test
#
# Prod   : /opt/kpi-prod   · cổng 8000–8007, 3000 · DB kpi_haiquan
# Dev    : cây này         · cổng 9000–9007, 3001 · DB kpi_haiquan_test
#
# Hai môi trường chạy ĐỒNG THỜI được. Dev không đụng dữ liệu, file, hay cổng
# của prod.
# =============================================================================
set -uo pipefail

GOC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$GOC"

[ -f .env.dev ] || { echo "⛔ Thiếu $GOC/.env.dev"; exit 1; }
set -a; source .env.dev; set +a

PID_DIR="/tmp/kpi-dev-pids"
LOG_DIR="/tmp/kpi-dev-logs"
mkdir -p "$PID_DIR" "$LOG_DIR" "$(dirname "$HKG_UPLOAD_DIR")"

# tên | module | cổng
declare -A MODULE=(
  [kpi]="app.main"              [lms]="lms_service.main"
  [forum]="forum_service.main"  [legal]="legal_service.main"
  [portal]="portal_service.main" [common]="common_service.main"
  [meeting]="meeting_service.main" [chitieu]="chi_tieu_service.main"
)
declare -A CONG=(
  [kpi]="$DEV_PORT_KPI"       [lms]="$DEV_PORT_LMS"
  [forum]="$DEV_PORT_FORUM"   [legal]="$DEV_PORT_LEGAL"
  [portal]="$DEV_PORT_PORTAL" [common]="$DEV_PORT_COMMON"
  [meeting]="$DEV_PORT_MEETING" [chitieu]="$DEV_PORT_CHITIEU"
)

log() { echo "[dev] $*"; }

canh_bao_db() {
    if [ "${DB_NAME:-}" = "kpi_haiquan" ]; then
        echo "⛔ DB_NAME đang là kpi_haiquan (PRODUCTION). Kiểm lại .env.dev"
        exit 1
    fi
}

chay_mot() {
    local ten=$1 mod=${MODULE[$1]} cong=${CONG[$1]}
    if [ -f "$PID_DIR/$ten.pid" ] && kill -0 "$(cat "$PID_DIR/$ten.pid")" 2>/dev/null; then
        log "$ten đã chạy (cổng $cong)"; return
    fi
    # --reload: dev sửa file là nạp lại ngay, không phải khởi động tay
    nohup venv/bin/python -m uvicorn "$mod:app" \
        --host 127.0.0.1 --port "$cong" --reload \
        > "$LOG_DIR/$ten.log" 2>&1 &
    echo $! > "$PID_DIR/$ten.pid"
    log "$ten → cổng $cong (log: $LOG_DIR/$ten.log)"
}

case "${1:-trang-thai}" in

chay)
    canh_bao_db
    shift
    ds=("$@"); [ ${#ds[@]} -eq 0 ] && ds=(kpi meeting frontend)
    log "DB=$DB_NAME · kho file=$HKG_UPLOAD_DIR"
    for d in "${ds[@]}"; do
        if [ "$d" = "frontend" ]; then
            if [ -f "$PID_DIR/frontend.pid" ] && kill -0 "$(cat "$PID_DIR/frontend.pid")" 2>/dev/null; then
                log "frontend đã chạy"; continue
            fi
            (cd ../frontend && nohup npm run dev -- -p "$DEV_PORT_FRONTEND" \
                > "$LOG_DIR/frontend.log" 2>&1 & echo $! > "$PID_DIR/frontend.pid")
            log "frontend → cổng $DEV_PORT_FRONTEND"
        elif [ -n "${MODULE[$d]:-}" ]; then
            chay_mot "$d"
        else
            log "! không biết dịch vụ '$d'"
        fi
    done
    sleep 6
    exec "$0" trang-thai
    ;;

dung)
    for f in "$PID_DIR"/*.pid; do
        [ -e "$f" ] || continue
        ten=$(basename "$f" .pid); pid=$(cat "$f")
        pkill -P "$pid" 2>/dev/null; kill "$pid" 2>/dev/null
        rm -f "$f"; log "đã dừng $ten"
    done
    log "xong — production không bị ảnh hưởng"
    ;;

trang-thai)
    echo "── DEV (cây $GOC) ──"
    for d in "${!CONG[@]}"; do
        ma=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 \
             "http://127.0.0.1:${CONG[$d]}/health" 2>/dev/null)
        [ "$ma" = "200" ] && printf "  ✅ %-9s cổng %s\n" "$d" "${CONG[$d]}"
    done
    ma=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 \
         "http://127.0.0.1:$DEV_PORT_FRONTEND/" 2>/dev/null)
    [ "$ma" = "200" ] && printf "  ✅ %-9s cổng %s\n" "frontend" "$DEV_PORT_FRONTEND"
    echo "── PROD (cây /opt/kpi-prod) ──"
    for c in 8000 8006; do
        ma=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 \
             "http://127.0.0.1:$c/health" 2>/dev/null)
        printf "  %s cổng %s\n" "$([ "$ma" = 200 ] && echo ✅ || echo ❌)" "$c"
    done
    ;;

lam-moi-db)
    canh_bao_db
    log "Tạo lại $DB_NAME từ bản sao production (pg_dump CHỈ ĐỌC prod)…"
    sudo -u postgres psql -q -c "DROP DATABASE IF EXISTS $DB_NAME;"
    sudo -u postgres psql -q -c "CREATE DATABASE $DB_NAME OWNER kpi_user;"
    sudo -u postgres bash -c "pg_dump kpi_haiquan | psql -q -d $DB_NAME" >/dev/null 2>&1
    log "xong: $(sudo -u postgres psql -d "$DB_NAME" -tAc 'SELECT count(*) FROM public.cong_chuc;') công chức"
    ;;

test)
    canh_bao_db
    shift
    DB_NAME="$DB_NAME" ALLOW_PROD_TEST=true venv/bin/python -m pytest "$@"
    ;;

*)
    sed -n '3,14p' "$0" | sed 's/^# \{0,1\}//'
    ;;
esac
