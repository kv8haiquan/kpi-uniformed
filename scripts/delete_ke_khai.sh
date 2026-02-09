#!/bin/bash
# ============================================================================
# XÓA CÔNG VIỆC KÊ KHAI CỤ THỂ
# ============================================================================
# Xóa công việc đã kê khai (và đã duyệt) theo:
#   - Mã công chức
#   - Mã danh mục công việc (VD: DM-037)
#   - Tháng/Năm
#
# CÁCH DÙNG:
#   chmod +x /root/kpi-haiquan/scripts/delete_ke_khai.sh
#   /root/kpi-haiquan/scripts/delete_ke_khai.sh
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
echo -e "${BLUE}  XÓA CÔNG VIỆC KÊ KHAI CỤ THỂ${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ============================================
# BƯỚC 1: Nhập thông tin
# ============================================

read -p "Nhập mã công chức (VD: 20ZZ-0036): " MA_CC
read -p "Nhập mã danh mục công việc (VD: DM-037): " MA_DM
read -p "Nhập tháng (1-12): " THANG
read -p "Nhập năm (VD: 2026): " NAM

# Validate
if [ -z "$MA_CC" ] || [ -z "$MA_DM" ] || [ -z "$THANG" ] || [ -z "$NAM" ]; then
    echo -e "${RED}❌ Vui lòng nhập đầy đủ thông tin!${NC}"
    exit 1
fi

# ============================================
# BƯỚC 2: Tìm công chức
# ============================================

echo ""
echo -e "${YELLOW}🔍 Đang tìm công chức $MA_CC ...${NC}"

CC_INFO=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -F'|' -c "
    SELECT id, ma_cc, ho_ten 
    FROM cong_chuc 
    WHERE ma_cc = '$MA_CC';
")

if [ -z "$CC_INFO" ]; then
    echo -e "${RED}❌ Không tìm thấy công chức với mã: $MA_CC${NC}"
    exit 1
fi

CC_ID=$(echo "$CC_INFO" | cut -d'|' -f1)
CC_MA=$(echo "$CC_INFO" | cut -d'|' -f2)
CC_TEN=$(echo "$CC_INFO" | cut -d'|' -f3)

echo -e "${GREEN}✅ Công chức: ${BOLD}$CC_TEN${NC} ($CC_MA)"

# ============================================
# BƯỚC 3: Tìm danh mục công việc
# ============================================

echo -e "${YELLOW}🔍 Đang tìm danh mục $MA_DM ...${NC}"

DM_INFO=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -F'|' -c "
    SELECT id, ma_danh_muc, ten_cong_viec 
    FROM danh_muc_sp_cong_viec 
    WHERE ma_danh_muc = '$MA_DM';
")

if [ -z "$DM_INFO" ]; then
    echo -e "${RED}❌ Không tìm thấy danh mục với mã: $MA_DM${NC}"
    echo -e "${YELLOW}💡 Gợi ý: Chạy lệnh sau để tìm kiếm:${NC}"
    echo "   psql -U $DB_USER -h $DB_HOST -d $DB_NAME -c \"SELECT ma_danh_muc, ten_cong_viec FROM danh_muc_sp_cong_viec WHERE ma_danh_muc LIKE '%037%' OR ten_cong_viec ILIKE '%keyword%';\""
    exit 1
fi

DM_ID=$(echo "$DM_INFO" | cut -d'|' -f1)
DM_MA=$(echo "$DM_INFO" | cut -d'|' -f2)
DM_TEN=$(echo "$DM_INFO" | cut -d'|' -f3)

echo -e "${GREEN}✅ Danh mục: ${BOLD}$DM_MA${NC} - $DM_TEN"

# ============================================
# BƯỚC 4: Tìm các bản ghi kê khai
# ============================================

echo ""
echo -e "${YELLOW}📋 Các bản ghi kê khai tìm thấy:${NC}"
echo "─────────────────────────────────────────────────────────────────────────────"

psql -U $DB_USER -h $DB_HOST -d $DB_NAME -c "
SELECT 
    kk.id,
    kk.ngay_thuc_hien as ngay,
    kk.so_luong as sl,
    cd.ma_cap_do as cap_do,
    kk.trang_thai,
    CASE WHEN kk.is_khoa THEN 'Khóa' ELSE '' END as khoa,
    kk.so_loi_chat_luong as loi_cl,
    kk.so_loi_tien_do as loi_td
FROM ke_khai_cong_viec kk
JOIN cap_do_phuc_tap cd ON kk.cap_do_id = cd.id
WHERE kk.cong_chuc_id = '$CC_ID'
  AND kk.danh_muc_sp_id = '$DM_ID'
  AND kk.thang = $THANG
  AND kk.nam = $NAM
  AND kk.is_deleted = false
ORDER BY kk.ngay_thuc_hien, kk.created_at;
"

# Đếm số bản ghi
COUNT_KK=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) FROM ke_khai_cong_viec 
    WHERE cong_chuc_id = '$CC_ID'
      AND danh_muc_sp_id = '$DM_ID'
      AND thang = $THANG
      AND nam = $NAM
      AND is_deleted = false;
")

if [ "$COUNT_KK" -eq 0 ]; then
    echo -e "\n${GREEN}✅ Không có bản ghi kê khai nào!${NC}"
    exit 0
fi

# Đếm phê duyệt liên quan
COUNT_PD=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) FROM phe_duyet_sp 
    WHERE ke_khai_id IN (
        SELECT id FROM ke_khai_cong_viec 
        WHERE cong_chuc_id = '$CC_ID'
          AND danh_muc_sp_id = '$DM_ID'
          AND thang = $THANG
          AND nam = $NAM
          AND is_deleted = false
    );
")

echo ""
echo -e "${CYAN}📊 Tổng kết:${NC}"
echo -e "   Kê khai công việc: ${BOLD}$COUNT_KK${NC} bản ghi"
echo -e "   Phê duyệt liên quan: ${BOLD}$COUNT_PD${NC} bản ghi"

# ============================================
# BƯỚC 5: Chọn cách xóa
# ============================================

echo ""
echo -e "${YELLOW}Bạn muốn xóa thế nào?${NC}"
echo "  1) Xóa TẤT CẢ $COUNT_KK bản ghi ở trên"
echo "  2) Xóa theo NGÀY cụ thể"
echo "  3) Xóa theo ID cụ thể"
echo "  0) Hủy, không xóa gì"
echo ""
read -p "Chọn (0-3): " CHOICE

case $CHOICE in
    1)
        # Xóa tất cả
        WHERE_CLAUSE="cong_chuc_id = '$CC_ID' AND danh_muc_sp_id = '$DM_ID' AND thang = $THANG AND nam = $NAM AND is_deleted = false"
        ;;
    2)
        # Xóa theo ngày
        read -p "Nhập ngày thực hiện (YYYY-MM-DD): " NGAY
        WHERE_CLAUSE="cong_chuc_id = '$CC_ID' AND danh_muc_sp_id = '$DM_ID' AND thang = $THANG AND nam = $NAM AND ngay_thuc_hien = '$NGAY' AND is_deleted = false"
        
        # Kiểm tra có bản ghi không
        CHECK=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
            SELECT COUNT(*) FROM ke_khai_cong_viec WHERE $WHERE_CLAUSE;
        ")
        if [ "$CHECK" -eq 0 ]; then
            echo -e "${RED}❌ Không tìm thấy bản ghi ngày $NGAY${NC}"
            exit 1
        fi
        COUNT_KK=$CHECK
        ;;
    3)
        # Xóa theo ID
        read -p "Nhập ID bản ghi (UUID): " KK_ID
        WHERE_CLAUSE="id = '$KK_ID' AND is_deleted = false"
        
        # Kiểm tra có bản ghi không
        CHECK=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
            SELECT COUNT(*) FROM ke_khai_cong_viec WHERE $WHERE_CLAUSE;
        ")
        if [ "$CHECK" -eq 0 ]; then
            echo -e "${RED}❌ Không tìm thấy bản ghi với ID: $KK_ID${NC}"
            exit 1
        fi
        COUNT_KK=1
        ;;
    0|*)
        echo -e "${YELLOW}❌ Đã hủy.${NC}"
        exit 0
        ;;
esac

# ============================================
# BƯỚC 6: Xác nhận
# ============================================

echo ""
echo -e "${RED}⚠️  CẢNH BÁO: Sẽ xóa $COUNT_KK bản ghi kê khai + phê duyệt liên quan${NC}"
echo -e "   Công chức: $CC_TEN ($CC_MA)"
echo -e "   Công việc: $DM_MA - $DM_TEN"
echo -e "   Tháng/Năm: $THANG/$NAM"
echo ""
read -p "Xác nhận xóa? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}❌ Đã hủy.${NC}"
    exit 0
fi

# ============================================
# BƯỚC 7: Xóa dữ liệu
# ============================================

echo ""
echo -e "${YELLOW}🗑️  Đang xóa...${NC}"

psql -U $DB_USER -h $DB_HOST -d $DB_NAME << EOF

BEGIN;

-- 1. Xóa phê duyệt SP trước (FK → ke_khai_cong_viec)
DELETE FROM phe_duyet_sp 
WHERE ke_khai_id IN (
    SELECT id FROM ke_khai_cong_viec WHERE $WHERE_CLAUSE
);

-- 2. Xóa kê khai công việc
DELETE FROM ke_khai_cong_viec WHERE $WHERE_CLAUSE;

COMMIT;

EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Xóa thành công!${NC}"
else
    echo -e "${RED}❌ Có lỗi! Transaction đã rollback.${NC}"
    exit 1
fi

# ============================================
# BƯỚC 8: Kiểm tra
# ============================================

echo ""
echo -e "${YELLOW}📋 Kiểm tra sau khi xóa:${NC}"

REMAIN=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) FROM ke_khai_cong_viec 
    WHERE cong_chuc_id = '$CC_ID'
      AND danh_muc_sp_id = '$DM_ID'
      AND thang = $THANG
      AND nam = $NAM
      AND is_deleted = false;
")

echo -e "   Còn lại: $REMAIN bản ghi $DM_MA của $CC_MA trong tháng $THANG/$NAM"

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  ✅ XÓA THÀNH CÔNG${NC}"
echo -e "${GREEN}  👤 $CC_TEN ($CC_MA)${NC}"
echo -e "${GREEN}  📄 $DM_MA - $DM_TEN${NC}"
echo -e "${GREEN}  📅 Tháng $THANG/$NAM${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""