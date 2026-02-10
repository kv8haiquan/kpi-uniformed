#!/bin/bash
# ============================================================================
# CLEAR NGÀY NGHỈ - 1 CÔNG CHỨC / 1 THÁNG CỤ THỂ
# ============================================================================
# Xóa toàn bộ đơn đăng ký nghỉ (bảng dang_ky_nghi) của 1 công chức
# trong 1 tháng cụ thể. Đồng thời reset số ngày nghỉ phép trong
# bảng danh_gia_thang nếu có.
#
# CÁCH DÙNG:
#   chmod +x /root/kpi-haiquan/scripts/clear_nghi_phep_user.sh
#   /root/kpi-haiquan/scripts/clear_nghi_phep_user.sh
#
# ============================================================================

set -e

# Cấu hình DB
DB_USER="kpi_user"
DB_NAME="kpi_haiquan"
DB_HOST="localhost"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  CLEAR NGÀY NGHỈ - 1 CÔNG CHỨC / 1 THÁNG${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ============================================
# BƯỚC 1: Nhập thông tin
# ============================================

read -p "Nhập mã công chức (VD: 20ZZ-0036): " MA_CC
read -p "Nhập tháng (mặc định: 2): " THANG
read -p "Nhập năm (mặc định: 2026): " NAM

# Giá trị mặc định
THANG=${THANG:-2}
NAM=${NAM:-2026}

# Validate
if [ -z "$MA_CC" ]; then
    echo -e "${RED}❌ Vui lòng nhập mã công chức!${NC}"
    exit 1
fi

# ============================================
# BƯỚC 2: Tìm công chức
# ============================================

echo ""
echo -e "${YELLOW}🔍 Đang tìm công chức $MA_CC ...${NC}"

CC_INFO=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -F'|' -c "
    SELECT cc.id, cc.ma_cc, cc.ho_ten, cc.is_lanh_dao, 
           dv.ten_don_vi, COALESCE(NULLIF(dv.ten_viet_tat, ''), dv.ma_don_vi)
    FROM cong_chuc cc
    JOIN don_vi dv ON cc.don_vi_id = dv.id
    WHERE cc.ma_cc = '$MA_CC';
")

if [ -z "$CC_INFO" ]; then
    echo -e "${RED}❌ Không tìm thấy công chức với mã: $MA_CC${NC}"
    exit 1
fi

CC_ID=$(echo "$CC_INFO" | cut -d'|' -f1)
CC_MA=$(echo "$CC_INFO" | cut -d'|' -f2)
CC_TEN=$(echo "$CC_INFO" | cut -d'|' -f3)
CC_LD=$(echo "$CC_INFO" | cut -d'|' -f4)
DV_TEN=$(echo "$CC_INFO" | cut -d'|' -f5)
DV_VT=$(echo "$CC_INFO" | cut -d'|' -f6)

echo -e "${GREEN}✅ Tìm thấy:${NC}"
echo -e "   Họ tên:     ${BOLD}$CC_TEN${NC}"
echo -e "   Mã CC:      $CC_MA"
echo -e "   Đơn vị:     $DV_TEN ($DV_VT)"
echo -e "   Lãnh đạo:   $([ "$CC_LD" = "t" ] && echo "Có" || echo "Không")"
echo -e "   Tháng/Năm:  ${BOLD}$THANG/$NAM${NC}"

# ============================================
# BƯỚC 3: Hiển thị chi tiết đơn nghỉ hiện có
# ============================================

echo ""
echo -e "${YELLOW}📋 Đơn nghỉ phép tháng $THANG/$NAM của $CC_TEN:${NC}"
echo "─────────────────────────────────────────────────────────────"

# Hiển thị chi tiết từng đơn
psql -U $DB_USER -h $DB_HOST -d $DB_NAME -c "
    SELECT loai_nghi::text AS \"Loại nghỉ\",
           to_char(tu_ngay, 'DD/MM/YYYY') AS \"Từ ngày\",
           to_char(den_ngay, 'DD/MM/YYYY') AS \"Đến ngày\",
           so_ngay AS \"Số ngày\",
           trang_thai::text AS \"Trạng thái\",
           COALESCE(LEFT(ly_do, 30), '') AS \"Lý do\"
    FROM dang_ky_nghi 
    WHERE cong_chuc_id = '$CC_ID' 
      AND thang_ap_dung = $THANG 
      AND nam_ap_dung = $NAM
      AND is_deleted = FALSE
    ORDER BY tu_ngay;
"

# Đếm theo trạng thái
COUNT_TOTAL=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) FROM dang_ky_nghi 
    WHERE cong_chuc_id = '$CC_ID' 
      AND thang_ap_dung = $THANG AND nam_ap_dung = $NAM
      AND is_deleted = FALSE;
")

COUNT_CHO_PD=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) FROM dang_ky_nghi 
    WHERE cong_chuc_id = '$CC_ID' 
      AND thang_ap_dung = $THANG AND nam_ap_dung = $NAM
      AND trang_thai = 'CHO_PHE_DUYET' AND is_deleted = FALSE;
")

COUNT_DA_PD=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) FROM dang_ky_nghi 
    WHERE cong_chuc_id = '$CC_ID' 
      AND thang_ap_dung = $THANG AND nam_ap_dung = $NAM
      AND trang_thai = 'DA_PHE_DUYET' AND is_deleted = FALSE;
")

COUNT_TU_CHOI=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) FROM dang_ky_nghi 
    WHERE cong_chuc_id = '$CC_ID' 
      AND thang_ap_dung = $THANG AND nam_ap_dung = $NAM
      AND trang_thai = 'TU_CHOI' AND is_deleted = FALSE;
")

TONG_NGAY=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COALESCE(SUM(so_ngay), 0) FROM dang_ky_nghi 
    WHERE cong_chuc_id = '$CC_ID' 
      AND thang_ap_dung = $THANG AND nam_ap_dung = $NAM
      AND is_deleted = FALSE;
")

# Số ngày nghỉ trong danh_gia_thang
NGHI_DG=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COALESCE(so_ngay_nghi_phep::text, 'NULL') 
    FROM danh_gia_thang 
    WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM;
")

echo ""
echo -e "  ${RED}🔴 Tổng đơn nghỉ:          $COUNT_TOTAL${NC}"
echo -e "     - Chờ phê duyệt:        $COUNT_CHO_PD"
echo -e "     - Đã phê duyệt:         $COUNT_DA_PD"
echo -e "     - Từ chối:               $COUNT_TU_CHOI"
echo -e "  ${RED}🔴 Tổng số ngày nghỉ:      $TONG_NGAY ngày${NC}"
echo -e "  ${CYAN}📊 Số ngày nghỉ trong đánh giá tháng: $NGHI_DG${NC}"

if [ "$COUNT_TOTAL" -eq 0 ]; then
    echo -e "\n${GREEN}✅ Không có đơn nghỉ phép để xóa!${NC}"
    exit 0
fi

# ============================================
# BƯỚC 4: Xác nhận
# ============================================

echo ""
echo -e "${RED}⚠️  CẢNH BÁO: Sẽ xóa TẤT CẢ đơn nghỉ phép tháng $THANG/$NAM${NC}"
echo -e "${RED}   của $CC_TEN ($CC_MA)${NC}"
echo -e "${RED}   Bao gồm:${NC}"
echo -e "${RED}   - $COUNT_TOTAL đơn nghỉ ($TONG_NGAY ngày)${NC}"
echo -e "${RED}   - Reset so_ngay_nghi_phep = 0 trong đánh giá tháng${NC}"
echo ""
read -p "Bạn chắc chắn? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}❌ Đã hủy.${NC}"
    exit 0
fi

# ============================================
# BƯỚC 5: Xóa dữ liệu (trong transaction)
# ============================================

echo ""
echo -e "${YELLOW}🗑️  Đang xóa...${NC}"

psql -U $DB_USER -h $DB_HOST -d $DB_NAME << EOF

BEGIN;

-- 1. Xóa đơn nghỉ phép (hard delete)
DELETE FROM dang_ky_nghi 
WHERE cong_chuc_id = '$CC_ID' 
  AND thang_ap_dung = $THANG 
  AND nam_ap_dung = $NAM
  AND is_deleted = FALSE;

-- 2. Reset số ngày nghỉ phép trong đánh giá tháng
UPDATE danh_gia_thang 
SET so_ngay_nghi_phep = 0,
    updated_at = CURRENT_TIMESTAMP
WHERE cong_chuc_id = '$CC_ID' 
  AND thang = $THANG 
  AND nam = $NAM;

COMMIT;

EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Xóa thành công!${NC}"
else
    echo -e "${RED}❌ Có lỗi! Transaction đã rollback.${NC}"
    exit 1
fi

# ============================================
# BƯỚC 6: Kiểm tra sau khi xóa
# ============================================

echo ""
echo -e "${YELLOW}📋 Kiểm tra sau khi xóa:${NC}"
echo "─────────────────────────────────────────────────────────────"

AFTER_NGHI=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) FROM dang_ky_nghi 
    WHERE cong_chuc_id = '$CC_ID' 
      AND thang_ap_dung = $THANG AND nam_ap_dung = $NAM
      AND is_deleted = FALSE;
")

AFTER_DG=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COALESCE(so_ngay_nghi_phep::text, 'NULL') 
    FROM danh_gia_thang 
    WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM;
")

echo -e "  ✅ Đơn nghỉ phép còn lại:           $AFTER_NGHI"
echo -e "  ✅ Số ngày nghỉ trong đánh giá tháng: $AFTER_DG"

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  ✅ ĐÃ XÓA SẠCH NGÀY NGHỈ${NC}"
echo -e "${GREEN}  👤 $CC_TEN ($CC_MA)${NC}"
echo -e "${GREEN}  🏢 $DV_TEN${NC}"
echo -e "${GREEN}  📅 Tháng $THANG/$NAM${NC}"
echo -e "${GREEN}  📊 Đã xóa: $COUNT_TOTAL đơn ($TONG_NGAY ngày)${NC}"
echo -e "${GREEN}  💡 Công chức có thể đăng ký nghỉ lại từ đầu${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""