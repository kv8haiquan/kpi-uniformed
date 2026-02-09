#!/bin/bash
# ============================================================================
# CLEAR DATA TEST - Xóa dữ liệu nhập vào, giữ master data
# ============================================================================
# Ngày: 01/02/2026
# Dùng: Xóa sạch data test, chuẩn bị cho kê khai thật
#
# CÁCH CHẠY:
#   chmod +x /root/kpi-haiquan/scripts/clear_data_test.sh
#   /root/kpi-haiquan/scripts/clear_data_test.sh
#
# ============================================================================

set -e

# Cấu hình
DB_USER="kpi_user"
DB_NAME="kpi_haiquan"
DB_HOST="localhost"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  CLEAR DATA TEST - KPI Hải quan${NC}"
echo -e "${BLUE}  $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ============================================
# BƯỚC 1: Đếm bản ghi hiện tại
# ============================================

echo -e "${YELLOW}📋 BƯỚC 1: Đếm bản ghi hiện tại${NC}"
echo "─────────────────────────────────────────────"

psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -c "
SELECT '  🔴 ke_khai_cong_viec:      ' || COUNT(*) FROM ke_khai_cong_viec
UNION ALL SELECT '  🔴 phe_duyet_sp:            ' || COUNT(*) FROM phe_duyet_sp
UNION ALL SELECT '  🔴 danh_gia_thang:          ' || COUNT(*) FROM danh_gia_thang
UNION ALL SELECT '  🔴 tieu_chi_chung_danh_gia: ' || COUNT(*) FROM tieu_chi_chung_danh_gia
UNION ALL SELECT '  🔴 lanh_dao_chi_so:         ' || COUNT(*) FROM lanh_dao_chi_so
UNION ALL SELECT '  🔴 danh_gia_dde:            ' || COUNT(*) FROM danh_gia_dde
UNION ALL SELECT '  🔴 ke_khai_lanh_dao:        ' || COUNT(*) FROM ke_khai_lanh_dao
UNION ALL SELECT '  🔴 bao_cao_xep_loai:        ' || COUNT(*) FROM bao_cao_xep_loai
UNION ALL SELECT '  🔴 chi_tiet_xep_loai:       ' || COUNT(*) FROM chi_tiet_xep_loai
UNION ALL SELECT '  🔴 dang_ky_nghi:            ' || COUNT(*) FROM dang_ky_nghi
UNION ALL SELECT '  🔴 lich_su_dieu_chinh:      ' || COUNT(*) FROM lich_su_dieu_chinh;
"

echo ""
echo -e "${GREEN}📋 BẢNG GIỮ NGUYÊN:${NC}"
psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -c "
SELECT '  🟢 cong_chuc:               ' || COUNT(*) FROM cong_chuc
UNION ALL SELECT '  🟢 don_vi:                  ' || COUNT(*) FROM don_vi
UNION ALL SELECT '  🟢 vai_tro:                 ' || COUNT(*) FROM vai_tro
UNION ALL SELECT '  🟢 tieu_chi_chung:          ' || COUNT(*) FROM tieu_chi_chung
UNION ALL SELECT '  🟢 sp_cong_viec_chuan:      ' || COUNT(*) FROM sp_cong_viec_chuan
UNION ALL SELECT '  🟢 cap_do_phuc_tap:         ' || COUNT(*) FROM cap_do_phuc_tap
UNION ALL SELECT '  🟢 danh_muc_sp_cong_viec:   ' || COUNT(*) FROM danh_muc_sp_cong_viec
UNION ALL SELECT '  🟢 audit_log:               ' || COUNT(*) FROM audit_log
UNION ALL SELECT '  🟢 lich_su_dieu_chuyen:     ' || COUNT(*) FROM lich_su_dieu_chuyen;
"

# ============================================
# BƯỚC 2: Xác nhận
# ============================================

echo ""
echo -e "${RED}⚠️  CẢNH BÁO: Sẽ xóa TẤT CẢ dữ liệu các bảng 🔴 ở trên!${NC}"
echo -e "${GREEN}    Các bảng 🟢 sẽ KHÔNG bị ảnh hưởng.${NC}"
echo ""
read -p "Bạn chắc chắn muốn xóa? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${YELLOW}❌ Đã hủy. Không xóa gì cả.${NC}"
    exit 0
fi

# ============================================
# BƯỚC 3: Xóa dữ liệu (trong transaction)
# ============================================

echo ""
echo -e "${YELLOW}🗑️  BƯỚC 3: Đang xóa dữ liệu...${NC}"

psql -U $DB_USER -h $DB_HOST -d $DB_NAME << 'SQL'

BEGIN;

-- Xóa con trước, cha sau (theo thứ tự FK)
DELETE FROM chi_tiet_xep_loai;
DELETE FROM bao_cao_xep_loai;
DELETE FROM lanh_dao_chi_so;
DELETE FROM tieu_chi_chung_danh_gia;
DELETE FROM danh_gia_dde;
DELETE FROM phe_duyet_sp;
DELETE FROM lich_su_dieu_chinh;
DELETE FROM ke_khai_cong_viec;
DELETE FROM ke_khai_lanh_dao;
DELETE FROM danh_gia_thang;
DELETE FROM dang_ky_nghi;

COMMIT;

SQL

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Xóa thành công!${NC}"
else
    echo -e "${RED}❌ Có lỗi! Transaction đã rollback, không mất dữ liệu.${NC}"
    exit 1
fi

# ============================================
# BƯỚC 4: Kiểm tra sau khi xóa
# ============================================

echo ""
echo -e "${YELLOW}📋 BƯỚC 4: Kiểm tra sau khi xóa${NC}"
echo "─────────────────────────────────────────────"

psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -c "
SELECT '  ✅ ke_khai_cong_viec:      ' || COUNT(*) FROM ke_khai_cong_viec
UNION ALL SELECT '  ✅ phe_duyet_sp:            ' || COUNT(*) FROM phe_duyet_sp
UNION ALL SELECT '  ✅ danh_gia_thang:          ' || COUNT(*) FROM danh_gia_thang
UNION ALL SELECT '  ✅ tieu_chi_chung_danh_gia: ' || COUNT(*) FROM tieu_chi_chung_danh_gia
UNION ALL SELECT '  ✅ lanh_dao_chi_so:         ' || COUNT(*) FROM lanh_dao_chi_so
UNION ALL SELECT '  ✅ danh_gia_dde:            ' || COUNT(*) FROM danh_gia_dde
UNION ALL SELECT '  ✅ ke_khai_lanh_dao:        ' || COUNT(*) FROM ke_khai_lanh_dao
UNION ALL SELECT '  ✅ bao_cao_xep_loai:        ' || COUNT(*) FROM bao_cao_xep_loai
UNION ALL SELECT '  ✅ chi_tiet_xep_loai:       ' || COUNT(*) FROM chi_tiet_xep_loai
UNION ALL SELECT '  ✅ dang_ky_nghi:            ' || COUNT(*) FROM dang_ky_nghi
UNION ALL SELECT '  ✅ lich_su_dieu_chinh:      ' || COUNT(*) FROM lich_su_dieu_chinh;
"

echo ""
echo -e "${GREEN}🟢 Master data (phải còn nguyên):${NC}"
psql -U $DB_USER -h $DB_HOST -d $DB_NAME -t -c "
SELECT '  🟢 cong_chuc:               ' || COUNT(*) FROM cong_chuc
UNION ALL SELECT '  🟢 don_vi:                  ' || COUNT(*) FROM don_vi
UNION ALL SELECT '  🟢 vai_tro:                 ' || COUNT(*) FROM vai_tro
UNION ALL SELECT '  🟢 tieu_chi_chung:          ' || COUNT(*) FROM tieu_chi_chung
UNION ALL SELECT '  🟢 danh_muc_sp_cong_viec:   ' || COUNT(*) FROM danh_muc_sp_cong_viec;
"

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  ✅ HOÀN THÀNH - Sẵn sàng kê khai thật!${NC}"
echo -e "${GREEN}  📦 Backup tại: /root/kpi-backup/${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""