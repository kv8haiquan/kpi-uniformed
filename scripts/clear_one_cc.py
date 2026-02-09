#!/bin/bash
# ============================================================================
# CLEAR DATA 1 CÔNG CHỨC - 1 THÁNG CỤ THỂ
# ============================================================================
# Xóa toàn bộ dữ liệu kê khai, phê duyệt, đánh giá, tiêu chí chung,
# nghỉ phép, xếp loại của 1 công chức trong 1 tháng.
#
# CÁCH DÙNG:
#   chmod +x /root/kpi-haiquan/scripts/clear_user_month.sh
#   /root/kpi-haiquan/scripts/clear_user_month.sh
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
echo -e "${BLUE}  CLEAR DATA - 1 CÔNG CHỨC / 1 THÁNG${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ============================================
# BƯỚC 1: Nhập thông tin
# ============================================

read -p "Nhập mã công chức (VD: 20ZZ-0036): " MA_CC
read -p "Nhập tháng (1-12): " THANG
read -p "Nhập năm (VD: 2026): " NAM

# Validate
if [ -z "$MA_CC" ] || [ -z "$THANG" ] || [ -z "$NAM" ]; then
    echo -e "${RED}❌ Vui lòng nhập đầy đủ thông tin!${NC}"
    exit 1
fi

# ============================================
# BƯỚC 2: Tìm công chức
# ============================================

echo ""
echo -e "${YELLOW}🔍 Đang tìm công chức $MA_CC ...${NC}"

CC_INFO=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -F'|' -c "
    SELECT id, ma_cc, ho_ten, is_lanh_dao 
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
CC_LD=$(echo "$CC_INFO" | cut -d'|' -f4)

echo -e "${GREEN}✅ Tìm thấy:${NC}"
echo -e "   Họ tên:     ${BOLD}$CC_TEN${NC}"
echo -e "   Mã CC:      $CC_MA"
echo -e "   Lãnh đạo:   $([ "$CC_LD" = "t" ] && echo "Có" || echo "Không")"
echo -e "   Tháng/Năm:  ${BOLD}$THANG/$NAM${NC}"

# ============================================
# BƯỚC 3: Đếm dữ liệu hiện có
# ============================================

echo ""
echo -e "${YELLOW}📋 Dữ liệu hiện có trong tháng $THANG/$NAM:${NC}"
echo "─────────────────────────────────────────────"

# Lấy danh_gia_thang_id
DG_ID=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT id FROM danh_gia_thang 
    WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM
    LIMIT 1;
")

# Đếm từng bảng
COUNT_KE_KHAI=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) FROM ke_khai_cong_viec 
    WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM;
")

COUNT_PHE_DUYET=0
if [ "$COUNT_KE_KHAI" -gt 0 ]; then
    COUNT_PHE_DUYET=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
        SELECT COUNT(*) FROM phe_duyet_sp 
        WHERE ke_khai_id IN (
            SELECT id FROM ke_khai_cong_viec 
            WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM
        );
    ")
fi

COUNT_KK_LD=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) FROM ke_khai_lanh_dao 
    WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM;
")

COUNT_DG_THANG=0
COUNT_TC_DG=0
COUNT_LD_CS=0
if [ -n "$DG_ID" ]; then
    COUNT_DG_THANG=1
    COUNT_TC_DG=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
        SELECT COUNT(*) FROM tieu_chi_chung_danh_gia 
        WHERE danh_gia_thang_id = '$DG_ID';
    ")
    COUNT_LD_CS=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
        SELECT COUNT(*) FROM lanh_dao_chi_so 
        WHERE danh_gia_thang_id = '$DG_ID';
    ")
fi

COUNT_DG_DDE=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) FROM danh_gia_dde 
    WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM;
")

COUNT_NGHI=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) FROM dang_ky_nghi 
    WHERE cong_chuc_id = '$CC_ID' AND thang_ap_dung = $THANG AND nam_ap_dung = $NAM;
")

COUNT_XL=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) FROM chi_tiet_xep_loai 
    WHERE cong_chuc_id = '$CC_ID' 
      AND bao_cao_id IN (
          SELECT id FROM bao_cao_xep_loai WHERE thang = $THANG AND nam = $NAM
      );
")

# Hiển thị
echo -e "  ${RED}🔴 ke_khai_cong_viec:       $COUNT_KE_KHAI${NC}"
echo -e "  ${RED}🔴 phe_duyet_sp:             $COUNT_PHE_DUYET${NC}"
echo -e "  ${RED}🔴 ke_khai_lanh_dao:         $COUNT_KK_LD${NC}"
echo -e "  ${RED}🔴 danh_gia_thang:           $COUNT_DG_THANG${NC}"
echo -e "  ${RED}🔴 tieu_chi_chung_danh_gia:  $COUNT_TC_DG${NC}"
echo -e "  ${RED}🔴 lanh_dao_chi_so:          $COUNT_LD_CS${NC}"
echo -e "  ${RED}🔴 danh_gia_dde:             $COUNT_DG_DDE${NC}"
echo -e "  ${RED}🔴 dang_ky_nghi:             $COUNT_NGHI${NC}"
echo -e "  ${RED}🔴 chi_tiet_xep_loai:        $COUNT_XL${NC}"

TOTAL=$((COUNT_KE_KHAI + COUNT_PHE_DUYET + COUNT_KK_LD + COUNT_DG_THANG + COUNT_TC_DG + COUNT_LD_CS + COUNT_DG_DDE + COUNT_NGHI + COUNT_XL))

echo ""
echo -e "  ${BOLD}Tổng cộng: $TOTAL bản ghi sẽ bị xóa${NC}"

if [ "$TOTAL" -eq 0 ]; then
    echo -e "\n${GREEN}✅ Không có dữ liệu để xóa!${NC}"
    exit 0
fi

# ============================================
# BƯỚC 4: Xác nhận
# ============================================

echo ""
echo -e "${RED}⚠️  CẢNH BÁO: Xóa TẤT CẢ dữ liệu tháng $THANG/$NAM của $CC_TEN ($CC_MA)${NC}"
echo -e "${RED}   Bao gồm: kê khai, phê duyệt, tiêu chí chung, đánh giá, nghỉ phép, xếp loại${NC}"
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

-- 1. Xóa phê duyệt SP (FK → ke_khai_cong_viec)
DELETE FROM phe_duyet_sp 
WHERE ke_khai_id IN (
    SELECT id FROM ke_khai_cong_viec 
    WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM
);

-- 2. Xóa kê khai công việc
DELETE FROM ke_khai_cong_viec 
WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM;

-- 3. Xóa kê khai lãnh đạo
DELETE FROM ke_khai_lanh_dao 
WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM;

-- 4. Xóa tiêu chí chung đánh giá (FK → danh_gia_thang)
DELETE FROM tieu_chi_chung_danh_gia 
WHERE danh_gia_thang_id IN (
    SELECT id FROM danh_gia_thang 
    WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM
);

-- 5. Xóa lãnh đạo chỉ số (FK → danh_gia_thang)
DELETE FROM lanh_dao_chi_so 
WHERE danh_gia_thang_id IN (
    SELECT id FROM danh_gia_thang 
    WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM
);

-- 6. Xóa đánh giá d,đ,e
DELETE FROM danh_gia_dde 
WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM;

-- 7. Xóa chi tiết xếp loại
DELETE FROM chi_tiet_xep_loai 
WHERE cong_chuc_id = '$CC_ID' 
  AND bao_cao_id IN (
      SELECT id FROM bao_cao_xep_loai WHERE thang = $THANG AND nam = $NAM
  );

-- 8. Xóa đăng ký nghỉ
DELETE FROM dang_ky_nghi 
WHERE cong_chuc_id = '$CC_ID' AND thang_ap_dung = $THANG AND nam_ap_dung = $NAM;

-- 9. Xóa đánh giá tháng (bảng cha - xóa cuối cùng)
DELETE FROM danh_gia_thang 
WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM;

COMMIT;

EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Xóa thành công!${NC}"
else
    echo -e "${RED}❌ Có lỗi! Transaction đã rollback.${NC}"
    exit 1
fi

# ============================================
# BƯỚC 6: Kiểm tra
# ============================================

echo ""
echo -e "${YELLOW}📋 Kiểm tra sau khi xóa:${NC}"
echo "─────────────────────────────────────────────"

psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -c "
SELECT '  ✅ ke_khai_cong_viec:       ' || COUNT(*) FROM ke_khai_cong_viec 
    WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM
UNION ALL 
SELECT '  ✅ danh_gia_thang:           ' || COUNT(*) FROM danh_gia_thang 
    WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM
UNION ALL 
SELECT '  ✅ ke_khai_lanh_dao:         ' || COUNT(*) FROM ke_khai_lanh_dao 
    WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM
UNION ALL 
SELECT '  ✅ danh_gia_dde:             ' || COUNT(*) FROM danh_gia_dde 
    WHERE cong_chuc_id = '$CC_ID' AND thang = $THANG AND nam = $NAM
UNION ALL 
SELECT '  ✅ dang_ky_nghi:             ' || COUNT(*) FROM dang_ky_nghi 
    WHERE cong_chuc_id = '$CC_ID' AND thang_ap_dung = $THANG AND nam_ap_dung = $NAM;
"

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  ✅ ĐÃ XÓA SẠCH DATA${NC}"
echo -e "${GREEN}  👤 $CC_TEN ($CC_MA)${NC}"
echo -e "${GREEN}  📅 Tháng $THANG/$NAM${NC}"
echo -e "${GREEN}  💡 Công chức có thể nhập lại từ đầu${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""