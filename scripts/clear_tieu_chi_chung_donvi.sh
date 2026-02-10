#!/bin/bash
# ============================================================================
# CLEAR TIÊU CHÍ CHUNG - TOÀN BỘ CÔNG CHỨC TRONG 1 ĐƠN VỊ / 1 THÁNG
# ============================================================================
# Xóa toàn bộ dữ liệu tiêu chí chung đã nhập (bảng tieu_chi_chung_danh_gia)
# của TẤT CẢ công chức thuộc 1 đơn vị trong 1 tháng cụ thể.
#
# Đồng thời reset lại điểm tiêu chí chung trong bảng danh_gia_thang
# và cập nhật trạng thái đánh giá nếu cần.
#
# CÁCH DÙNG:
#   chmod +x /root/kpi-haiquan/scripts/clear_tieu_chi_chung_donvi.sh
#   /root/kpi-haiquan/scripts/clear_tieu_chi_chung_donvi.sh
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
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  CLEAR TIÊU CHÍ CHUNG - TOÀN BỘ CC TRONG 1 ĐƠN VỊ${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# ============================================
# BƯỚC 1: Hiển thị danh sách đơn vị
# ============================================

echo -e "${CYAN}📋 Danh sách đơn vị:${NC}"
echo "─────────────────────────────────────────────────────────────"

psql -U $DB_USER -h $DB_HOST -d $DB_NAME -c "
    SELECT dv.ma_don_vi AS \"Mã ĐV\", 
           dv.ten_don_vi AS \"Tên đơn vị\",
           dv.loai_don_vi::text AS \"Loại\",
           COUNT(cc.id) AS \"Số CC\"
    FROM don_vi dv
    LEFT JOIN cong_chuc cc ON cc.don_vi_id = dv.id 
         AND cc.is_active = TRUE AND cc.is_deleted = FALSE
    WHERE dv.is_active = TRUE
      AND dv.ma_don_vi != 'DEPT-ADMIN'
    GROUP BY dv.id, dv.ma_don_vi, dv.ten_don_vi, 
             dv.loai_don_vi, dv.thu_tu_hien_thi
    ORDER BY dv.thu_tu_hien_thi, dv.ma_don_vi;
"

echo ""

# ============================================
# BƯỚC 2: Nhập thông tin
# ============================================

read -p "Nhập mã đơn vị (VD: DNV01): " MA_DV
read -p "Nhập tháng (mặc định: 2): " THANG
read -p "Nhập năm (mặc định: 2026): " NAM

# Giá trị mặc định
THANG=${THANG:-2}
NAM=${NAM:-2026}

# Validate
if [ -z "$MA_DV" ]; then
    echo -e "${RED}❌ Vui lòng nhập mã đơn vị!${NC}"
    exit 1
fi

# ============================================
# BƯỚC 3: Tìm đơn vị
# ============================================

echo ""
echo -e "${YELLOW}🔍 Đang tìm đơn vị $MA_DV ...${NC}"

DV_INFO=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -F'|' -c "
    SELECT id, ma_don_vi, ten_don_vi, COALESCE(NULLIF(ten_viet_tat, ''), ma_don_vi)
    FROM don_vi 
    WHERE ma_don_vi = '$MA_DV' AND is_active = TRUE;
")

if [ -z "$DV_INFO" ]; then
    echo -e "${RED}❌ Không tìm thấy đơn vị với mã: $MA_DV${NC}"
    exit 1
fi

DV_ID=$(echo "$DV_INFO" | cut -d'|' -f1)
DV_MA=$(echo "$DV_INFO" | cut -d'|' -f2)
DV_TEN=$(echo "$DV_INFO" | cut -d'|' -f3)
DV_VT=$(echo "$DV_INFO" | cut -d'|' -f4)

echo -e "${GREEN}✅ Tìm thấy:${NC}"
echo -e "   Đơn vị:    ${BOLD}$DV_TEN ($DV_VT)${NC}"
echo -e "   Mã ĐV:     $DV_MA"
echo -e "   Tháng/Năm:  ${BOLD}$THANG/$NAM${NC}"

# ============================================
# BƯỚC 4: Liệt kê công chức trong đơn vị
# ============================================

echo ""
echo -e "${YELLOW}👥 Danh sách công chức trong $DV_VT:${NC}"
echo "─────────────────────────────────────────────────────────────"

psql -U $DB_USER -h $DB_HOST -d $DB_NAME -c "
    SELECT ma_cc AS \"Mã CC\", 
           ho_ten AS \"Họ tên\",
           CASE WHEN is_lanh_dao THEN 'Có' ELSE 'Không' END AS \"Lãnh đạo\"
    FROM cong_chuc 
    WHERE don_vi_id = '$DV_ID' 
      AND is_active = TRUE 
      AND is_deleted = FALSE
    ORDER BY is_lanh_dao DESC, ho_ten;
"

SO_CC=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) FROM cong_chuc 
    WHERE don_vi_id = '$DV_ID' AND is_active = TRUE AND is_deleted = FALSE;
")

echo -e "   ${BOLD}Tổng: $SO_CC công chức${NC}"

# ============================================
# BƯỚC 5: Đếm dữ liệu tiêu chí chung hiện có
# ============================================

echo ""
echo -e "${YELLOW}📋 Dữ liệu tiêu chí chung tháng $THANG/$NAM của $DV_VT:${NC}"
echo "─────────────────────────────────────────────────────────────"

# Đếm tổng bản ghi tiêu chí chung đánh giá
COUNT_TC=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) 
    FROM tieu_chi_chung_danh_gia tcd
    JOIN danh_gia_thang dt ON tcd.danh_gia_thang_id = dt.id
    JOIN cong_chuc cc ON dt.cong_chuc_id = cc.id
    WHERE cc.don_vi_id = '$DV_ID'
      AND dt.thang = $THANG 
      AND dt.nam = $NAM;
")

# Đếm theo trạng thái
COUNT_NHAP=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) 
    FROM tieu_chi_chung_danh_gia tcd
    JOIN danh_gia_thang dt ON tcd.danh_gia_thang_id = dt.id
    JOIN cong_chuc cc ON dt.cong_chuc_id = cc.id
    WHERE cc.don_vi_id = '$DV_ID'
      AND dt.thang = $THANG AND dt.nam = $NAM
      AND tcd.trang_thai = 'NHAP';
")

COUNT_CHO_PD=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) 
    FROM tieu_chi_chung_danh_gia tcd
    JOIN danh_gia_thang dt ON tcd.danh_gia_thang_id = dt.id
    JOIN cong_chuc cc ON dt.cong_chuc_id = cc.id
    WHERE cc.don_vi_id = '$DV_ID'
      AND dt.thang = $THANG AND dt.nam = $NAM
      AND tcd.trang_thai = 'CHO_PHE_DUYET';
")

COUNT_DA_PD=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) 
    FROM tieu_chi_chung_danh_gia tcd
    JOIN danh_gia_thang dt ON tcd.danh_gia_thang_id = dt.id
    JOIN cong_chuc cc ON dt.cong_chuc_id = cc.id
    WHERE cc.don_vi_id = '$DV_ID'
      AND dt.thang = $THANG AND dt.nam = $NAM
      AND tcd.trang_thai = 'DA_PHE_DUYET';
")

# Đếm số danh_gia_thang bị ảnh hưởng
COUNT_DG=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) 
    FROM danh_gia_thang dt
    JOIN cong_chuc cc ON dt.cong_chuc_id = cc.id
    WHERE cc.don_vi_id = '$DV_ID'
      AND dt.thang = $THANG AND dt.nam = $NAM
      AND dt.diem_tieu_chi_chung IS NOT NULL;
")

# Chi tiết theo công chức
echo -e "${CYAN}  Chi tiết theo công chức:${NC}"
psql -U $DB_USER -h $DB_HOST -d $DB_NAME -c "
    SELECT cc.ma_cc AS \"Mã CC\",
           cc.ho_ten AS \"Họ tên\",
           COUNT(tcd.id) AS \"Số TC đã nhập\",
           STRING_AGG(DISTINCT tcd.trang_thai::text, ', ') AS \"Trạng thái\",
           COALESCE(dt.diem_tieu_chi_chung::text, 'NULL') AS \"Điểm TC chung\"
    FROM cong_chuc cc
    JOIN danh_gia_thang dt ON dt.cong_chuc_id = cc.id 
         AND dt.thang = $THANG AND dt.nam = $NAM
    LEFT JOIN tieu_chi_chung_danh_gia tcd ON tcd.danh_gia_thang_id = dt.id
    WHERE cc.don_vi_id = '$DV_ID'
      AND cc.is_active = TRUE AND cc.is_deleted = FALSE
    GROUP BY cc.ma_cc, cc.ho_ten, dt.diem_tieu_chi_chung
    HAVING COUNT(tcd.id) > 0
    ORDER BY cc.ho_ten;
"

echo ""
echo -e "  ${RED}🔴 Tổng bản ghi tieu_chi_chung_danh_gia:  $COUNT_TC${NC}"
echo -e "     - Trạng thái NHAP:                      $COUNT_NHAP"
echo -e "     - Trạng thái CHO_PHE_DUYET:             $COUNT_CHO_PD"
echo -e "     - Trạng thái DA_PHE_DUYET:              $COUNT_DA_PD"
echo -e "  ${RED}🔴 Số danh_gia_thang cần reset điểm TC:    $COUNT_DG${NC}"

TOTAL=$((COUNT_TC))

echo ""
echo -e "  ${BOLD}Tổng cộng: $TOTAL bản ghi tiêu chí chung sẽ bị xóa${NC}"
echo -e "  ${BOLD}         + $COUNT_DG bản ghi danh_gia_thang sẽ reset điểm TC chung${NC}"

if [ "$TOTAL" -eq 0 ]; then
    echo -e "\n${GREEN}✅ Không có dữ liệu tiêu chí chung để xóa!${NC}"
    exit 0
fi

# ============================================
# BƯỚC 6: Xác nhận
# ============================================

echo ""
echo -e "${RED}⚠️  CẢNH BÁO: Sẽ xóa TẤT CẢ dữ liệu tiêu chí chung tháng $THANG/$NAM${NC}"
echo -e "${RED}   của TOÀN BỘ công chức trong $DV_TEN ($DV_MA)${NC}"
echo -e "${RED}   Bao gồm:${NC}"
echo -e "${RED}   - $COUNT_TC bản ghi tieu_chi_chung_danh_gia${NC}"
echo -e "${RED}   - Reset diem_tieu_chi_chung = NULL trong $COUNT_DG bản ghi danh_gia_thang${NC}"
echo ""
read -p "Bạn chắc chắn? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}❌ Đã hủy.${NC}"
    exit 0
fi

# ============================================
# BƯỚC 7: Xóa dữ liệu (trong transaction)
# ============================================

echo ""
echo -e "${YELLOW}🗑️  Đang xóa...${NC}"

psql -U $DB_USER -h $DB_HOST -d $DB_NAME << EOF

BEGIN;

-- 1. Xóa tieu_chi_chung_danh_gia (bảng con - xóa trước)
DELETE FROM tieu_chi_chung_danh_gia 
WHERE danh_gia_thang_id IN (
    SELECT dt.id 
    FROM danh_gia_thang dt
    JOIN cong_chuc cc ON dt.cong_chuc_id = cc.id
    WHERE cc.don_vi_id = '$DV_ID'
      AND dt.thang = $THANG 
      AND dt.nam = $NAM
);

-- 2. Reset điểm tiêu chí chung trong danh_gia_thang
-- (để CC có thể nhập lại từ đầu)
UPDATE danh_gia_thang 
SET diem_tieu_chi_chung = NULL,
    updated_at = CURRENT_TIMESTAMP
WHERE id IN (
    SELECT dt.id 
    FROM danh_gia_thang dt
    JOIN cong_chuc cc ON dt.cong_chuc_id = cc.id
    WHERE cc.don_vi_id = '$DV_ID'
      AND dt.thang = $THANG 
      AND dt.nam = $NAM
);

COMMIT;

EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Xóa thành công!${NC}"
else
    echo -e "${RED}❌ Có lỗi! Transaction đã rollback.${NC}"
    exit 1
fi

# ============================================
# BƯỚC 8: Kiểm tra sau khi xóa
# ============================================

echo ""
echo -e "${YELLOW}📋 Kiểm tra sau khi xóa:${NC}"
echo "─────────────────────────────────────────────────────────────"

AFTER_TC=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) 
    FROM tieu_chi_chung_danh_gia tcd
    JOIN danh_gia_thang dt ON tcd.danh_gia_thang_id = dt.id
    JOIN cong_chuc cc ON dt.cong_chuc_id = cc.id
    WHERE cc.don_vi_id = '$DV_ID'
      AND dt.thang = $THANG AND dt.nam = $NAM;
")

AFTER_DIEM=$(psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -A -c "
    SELECT COUNT(*) 
    FROM danh_gia_thang dt
    JOIN cong_chuc cc ON dt.cong_chuc_id = cc.id
    WHERE cc.don_vi_id = '$DV_ID'
      AND dt.thang = $THANG AND dt.nam = $NAM
      AND dt.diem_tieu_chi_chung IS NOT NULL;
")

echo -e "  ✅ tieu_chi_chung_danh_gia còn lại:  $AFTER_TC"
echo -e "  ✅ danh_gia_thang có điểm TC chung:   $AFTER_DIEM"

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  ✅ ĐÃ XÓA SẠCH TIÊU CHÍ CHUNG${NC}"
echo -e "${GREEN}  🏢 Đơn vị: $DV_TEN ($DV_MA)${NC}"
echo -e "${GREEN}  📅 Tháng $THANG/$NAM${NC}"
echo -e "${GREEN}  📊 Đã xóa: $COUNT_TC bản ghi tiêu chí chung${NC}"
echo -e "${GREEN}  📊 Đã reset: $COUNT_DG bản ghi điểm TC trong đánh giá tháng${NC}"
echo -e "${GREEN}  💡 Công chức có thể nhập lại tiêu chí chung từ đầu${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""