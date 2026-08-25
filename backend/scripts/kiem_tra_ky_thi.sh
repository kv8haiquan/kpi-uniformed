#!/usr/bin/env bash
# =============================================================================
# kiem_tra_ky_thi.sh — Chặn build/triển khai khi đang có người thi
# =============================================================================
# Trả về 0 nếu AN TOÀN để build/nạp lại dịch vụ, khác 0 nếu ĐANG CÓ người thi.
#
#   backend/scripts/kiem_tra_ky_thi.sh          # kiểm tra rồi thoát theo mã
#   BO_QUA_KIEM_TRA_KY_THI=1 …                  # bỏ qua (chỉ khi thật cần)
#
# ── Vì sao có file này ───────────────────────────────────────────────────────
# Sự cố 25/08/2026: `npm run build` khởi động lúc 10:03:43 trong khi 13 thí sinh
# đang ở phút thứ 30 của bài thi 45 phút. Build ngốn ~1,4GB trên máy 7,8GB
# KHÔNG có swap → cả máy đóng băng 12 phút. nginx ghi 59 request 499 trên
# /luu-nhap, /nop-bai, /xac-nhan. Không ai mất bài, nhưng đó là may.
#
# ── Vì sao KHÔNG chặn theo `ky_thi.trang_thai = 'DANG_MO'` ───────────────────
# Vì tại thời điểm viết có 15 kỳ ở trạng thái DANG_MO cùng lúc — kỳ mở suốt
# nhiều tuần. Chặn theo đó thì không bao giờ triển khai được nữa.
#
# ── Vì sao KHÔNG chặn chỉ theo `thi_sinh.trang_thai = 'DANG_THI'` ────────────
# Vì bản ghi này kẹt lại vĩnh viễn khi thí sinh bỏ ngang: đóng trình duyệt là
# không bao giờ chuyển sang DA_NOP. Chặn theo đó sẽ hoá thành chặn vĩnh viễn.
#
# Tín hiệu dùng ở đây là `lms.phien_thi.last_seen` — do cơ chế phiên-đơn cập
# nhật liên tục khi thí sinh còn mở bài. Ai đóng máy thì last_seen ngừng tươi,
# chốt chặn tự mở lại. Kèm một vế dự phòng theo DANG_THI có giới hạn thời lượng
# bài thi, phòng khi polling hỏng.
# =============================================================================
set -euo pipefail

GOC="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MOI_TRUONG="${MOI_TRUONG:-$GOC/backend/.env}"

# Ngưỡng coi là "còn đang mở bài" — phiên nào có tín hiệu trong ngần này phút.
NGUONG_PHUT="${NGUONG_PHUT:-3}"
# Ân hạn sau khi hết giờ làm bài, để thí sinh kịp bấm nộp.
AN_HAN_PHUT="${AN_HAN_PHUT:-10}"
# Thí sinh đã xác nhận ca thi nhưng chưa bấm bắt đầu — sắp vào thi.
SAP_THI_PHUT="${SAP_THI_PHUT:-15}"

if [ "${BO_QUA_KIEM_TRA_KY_THI:-0}" = "1" ]; then
    echo "⚠️  BO_QUA_KIEM_TRA_KY_THI=1 — bỏ qua kiểm tra kỳ thi."
    exit 0
fi

[ -f "$MOI_TRUONG" ] || { echo "⛔ Không thấy $MOI_TRUONG" >&2; exit 1; }

# shellcheck disable=SC1090
set -a; . "$MOI_TRUONG"; set +a

export PGPASSWORD="${DB_PASSWORD:-}"
psql_ro() {
    psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" \
         -U "${DB_USER:?thiếu DB_USER}" -d "${DB_NAME:?thiếu DB_NAME}" \
         -v ON_ERROR_STOP=1 -tA "$@"
}

# Một truy vấn dùng chung cho cả đếm lẫn liệt kê, để con số và danh sách không
# bao giờ vênh nhau. Ba vế OR đều quy về CÙNG một thí sinh nên phải gộp bằng
# DISTINCT: bản thử đầu tiên cộng ba subquery rời nhau và báo "3 lượt" trong khi
# thực tế chỉ có 2 người — cùng một người khớp hai vế bị đếm hai lần.
#
# `trang_thai <> 'DA_NOP'` là điều kiện then chốt: thí sinh vừa nộp xong vẫn
# nằm lại trang kết quả nên last_seen vẫn tươi. Không loại ra thì chốt chặn kêu
# oan và người vận hành sẽ tập thói quen bỏ qua nó.
DIEU_KIEN="
    ts.trang_thai <> 'DA_NOP'
    AND (
         pt.last_seen > now() - make_interval(mins => $NGUONG_PHUT)
      OR (ts.trang_thai = 'DANG_THI'
          AND ts.thoi_gian_bat_dau IS NOT NULL
          AND now() < ts.thoi_gian_bat_dau
                    + make_interval(mins => kt.thoi_gian_lam_bai_phut + $AN_HAN_PHUT))
      OR (ts.da_xac_nhan IS TRUE
          AND ts.trang_thai = 'CHUA_THI'
          AND ts.thoi_gian_xac_nhan > now() - make_interval(mins => $SAP_THI_PHUT))
    )"

TRUY_VAN="
    SELECT DISTINCT ON (ts.id)
           ts.id, cc.ma_cc, cc.ho_ten, kt.ma_ky_thi,
           coalesce(to_char(max(pt.last_seen) OVER (PARTITION BY ts.id),
                            'HH24:MI:SS'), '—') AS tin_hieu_cuoi,
           ts.trang_thai
      FROM lms.thi_sinh ts
      JOIN lms.ky_thi kt       ON kt.id = ts.ky_thi_id
      JOIN public.cong_chuc cc ON cc.id = ts.cong_chuc_id
      LEFT JOIN lms.phien_thi pt ON pt.thi_sinh_id = ts.id
     WHERE $DIEU_KIEN"

# Nếu không hỏi được DB thì CHẶN, không đoán bừa: người vận hành đang ngồi
# trước máy và đọc được thông báo, còn thí sinh thì không.
if ! TONG=$(psql_ro -c "SELECT count(*) FROM ($TRUY_VAN) t;" 2>&1); then
    echo "⛔ Không truy vấn được CSDL để kiểm tra kỳ thi:" >&2
    echo "$TONG" | sed 's/^/   /' >&2
    echo "   Chặn để an toàn. Nếu chắc chắn không có ai thi:" >&2
    echo "   BO_QUA_KIEM_TRA_KY_THI=1 $0" >&2
    exit 1
fi

if [ "$TONG" -eq 0 ]; then
    echo "✅ Không có ai đang thi — an toàn để build/triển khai."
    exit 0
fi

echo "⛔ ĐANG CÓ $TONG người thi — KHÔNG build/triển khai lúc này." >&2
echo >&2
psql_ro -F' | ' -c "
    SELECT ma_cc, ho_ten, ma_ky_thi, tin_hieu_cuoi, trang_thai
      FROM ($TRUY_VAN) t
     ORDER BY tin_hieu_cuoi DESC;" 2>/dev/null | sed 's/^/   /' >&2

echo >&2
echo "   Đợi thi xong rồi chạy lại. Nếu buộc phải làm ngay:" >&2
echo "   BO_QUA_KIEM_TRA_KY_THI=1 <lệnh của bạn>" >&2
exit 1
