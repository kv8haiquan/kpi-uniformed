#!/bin/bash
# =============================================
# SCRIPT EXPORT DỰ ÁN KPI HẢI QUAN CHO CLAUDE AI
# Version: 1.0.0
# Updated: 2026-01-28
# =============================================
# Cách dùng:
#   cd /root/kpi-haiquan
#   ./export-for-claude.sh
#
# Output:
#   /root/kpi-export/FRONTEND_FULL_[timestamp].md
#   /root/kpi-export/BACKEND_FULL_[timestamp].md
# =============================================

set -e

EXPORT_DIR="/root/kpi-export"
PROJECT_DIR="/root/kpi-haiquan"
TIMESTAMP=$(date +%Y%m%d_%H%M)

mkdir -p $EXPORT_DIR

echo "🚀 Bắt đầu export dự án KPI Hải quan..."
echo "📁 Output: $EXPORT_DIR"
echo ""

# ============================================
# FRONTEND EXPORT
# ============================================
OUTPUT_FE="$EXPORT_DIR/FRONTEND_FULL_${TIMESTAMP}.md"

cat > $OUTPUT_FE << 'HEADER'
# FRONTEND SOURCE CODE - KPI HẢI QUAN
# ====================================
# Dự án: Phần mềm Đánh giá KPI & Xếp loại Công chức
# Đơn vị: Chi cục Hải quan Khu vực VIII
# Tech: Next.js 14, TypeScript, TailwindCSS
# ====================================

HEADER

echo "Exported: $(date '+%Y-%m-%d %H:%M:%S')" >> $OUTPUT_FE
echo "" >> $OUTPUT_FE

# Danh sách tất cả files frontend
FE_FILES=(
  # ===== APP LAYOUTS =====
  "frontend/src/app/layout.tsx"
  "frontend/src/app/page.tsx"
  "frontend/src/app/globals.css"
  
  # ===== AUTH =====
  "frontend/src/app/(auth)/layout.tsx"
  "frontend/src/app/(auth)/login/page.tsx"
  
  # ===== MAIN LAYOUT =====
  "frontend/src/app/(main)/layout.tsx"
  
  # ===== DASHBOARD =====
  "frontend/src/app/(main)/dashboard/page.tsx"
  
  # ===== KÊ KHAI =====
  "frontend/src/app/(main)/ke-khai/page.tsx"
  
  # ===== PHÊ DUYỆT SP =====
  "frontend/src/app/(main)/phe-duyet/page.tsx"
  
  # ===== ĐÁNH GIÁ / TIÊU CHÍ CHUNG =====
  "frontend/src/app/(main)/danh-gia/page.tsx"
  "frontend/src/app/(main)/danh-gia/tu-cham-diem/page.tsx"
  "frontend/src/app/(main)/danh-gia/phe-duyet/page.tsx"
  "frontend/src/app/(main)/danh-gia/phe-duyet/[id]/page.tsx"
  
  # ===== XẾP LOẠI =====
  "frontend/src/app/(main)/xep-loai/page.tsx"
  "frontend/src/app/(main)/xep-loai/phe-duyet/page.tsx"
  "frontend/src/app/(main)/xep-loai/thong-ke/page.tsx"
  
  # ===== NGHỈ PHÉP =====
  "frontend/src/app/(main)/nghi-phep/page.tsx"
  "frontend/src/app/(main)/nghi-phep/phe-duyet/page.tsx"
  
  # ===== COMPONENTS - KPI =====
  "frontend/src/components/kpi/KpiTargetModal.tsx"
  
  # ===== COMPONENTS - KÊ KHAI LÃNH ĐẠO =====
  "frontend/src/components/ke-khai/LeaderKeKhaiView.tsx"
  "frontend/src/components/ke-khai/LeaderDeclarationForm.tsx"
  "frontend/src/components/ke-khai/LeaderAssessmentDDE.tsx"
  
  # ===== COMPONENTS - ASSESSMENT =====
  "frontend/src/components/assessment/TieuChiChungForm.tsx"
  
  # ===== SERVICES =====
  "frontend/src/services/auth.service.ts"
  "frontend/src/services/kpi.service.ts"
  "frontend/src/services/leader-kpi.service.ts"
  "frontend/src/services/assessment.service.ts"
  "frontend/src/services/tieu-chi-chung.service.ts"
  "frontend/src/services/bao-cao-xep-loai.service.ts"
  "frontend/src/services/leave.service.ts"
  
  # ===== STORES =====
  "frontend/src/stores/useAuthStore.ts"
  
  # ===== TYPES =====
  "frontend/src/types/api.ts"
  "frontend/src/types/auth.ts"
  "frontend/src/types/kpi.ts"
  "frontend/src/types/leader-kpi.ts"
  "frontend/src/types/assessment.ts"
  "frontend/src/types/tieu-chi-chung.ts"
  "frontend/src/types/bao-cao-xep-loai.ts"
  "frontend/src/types/leave.ts"
  
  # ===== LIB =====
  "frontend/src/lib/axios.ts"
  "frontend/src/lib/validations/auth.ts"
  "frontend/src/lib/validations/kpi.ts"
  
  # ===== PROVIDERS =====
  "frontend/src/providers/AuthProvider.tsx"
)

echo "📦 Exporting Frontend files..."
fe_count=0

for file in "${FE_FILES[@]}"; do
  full_path="$PROJECT_DIR/$file"
  if [ -f "$full_path" ]; then
    # Xác định ngôn ngữ cho syntax highlight
    ext="${file##*.}"
    lang="tsx"
    if [ "$ext" = "ts" ]; then
      lang="typescript"
    elif [ "$ext" = "css" ]; then
      lang="css"
    fi
    
    echo -e "\n\n---\n## 📄 FILE: $file\n\`\`\`$lang" >> $OUTPUT_FE
    cat "$full_path" >> $OUTPUT_FE
    echo -e "\n\`\`\`" >> $OUTPUT_FE
    fe_count=$((fe_count + 1))
    echo "  ✅ $file"
  else
    echo "  ⚠️  KHÔNG TÌM THẤY: $file"
  fi
done

echo ""
echo "✅ Frontend: $fe_count files exported"
echo "📄 Output: $OUTPUT_FE"

# ============================================
# BACKEND EXPORT
# ============================================
OUTPUT_BE="$EXPORT_DIR/BACKEND_FULL_${TIMESTAMP}.md"

cat > $OUTPUT_BE << 'HEADER'
# BACKEND SOURCE CODE - KPI HẢI QUAN
# ====================================
# Dự án: Phần mềm Đánh giá KPI & Xếp loại Công chức
# Đơn vị: Chi cục Hải quan Khu vực VIII
# Tech: FastAPI, SQLAlchemy, PostgreSQL
# ====================================

HEADER

echo "Exported: $(date '+%Y-%m-%d %H:%M:%S')" >> $OUTPUT_BE
echo "" >> $OUTPUT_BE

# Danh sách tất cả files backend
BE_FILES=(
  # ===== MAIN & CONFIG =====
  "backend/app/main.py"
  "backend/app/config.py"
  
  # ===== CORE =====
  "backend/app/core/security.py"
  
  # ===== DATABASE =====
  "backend/app/db/session.py"
  
  # ===== API DEPENDENCIES =====
  "backend/app/api/deps.py"
  "backend/app/api/v1/api.py"
  
  # ===== ENDPOINTS =====
  "backend/app/api/v1/endpoints/auth.py"
  "backend/app/api/v1/endpoints/ke_khai.py"
  "backend/app/api/v1/endpoints/ke_khai_lanh_dao.py"
  "backend/app/api/v1/endpoints/phe_duyet.py"
  "backend/app/api/v1/endpoints/danh_gia.py"
  "backend/app/api/v1/endpoints/danh_gia_lanh_dao.py"
  "backend/app/api/v1/endpoints/bao_cao_xep_loai.py"
  "backend/app/api/v1/endpoints/danh_muc.py"
  "backend/app/api/v1/endpoints/cong_chuc.py"
  "backend/app/api/v1/endpoints/don_vi.py"
  "backend/app/api/v1/endpoints/nghi_phep.py"
  
  # ===== MODELS =====
  "backend/app/models/base.py"
  "backend/app/models/user_org.py"
  "backend/app/models/task_catalog.py"
  "backend/app/models/kpi_submission.py"
  "backend/app/models/kpi_assessment.py"
  "backend/app/models/leader_kpi.py"
  "backend/app/models/bao_cao_xep_loai.py"
  "backend/app/models/leave.py"
  "backend/app/models/audit_log.py"
  
  # ===== SCHEMAS =====
  "backend/app/schemas/common.py"
  "backend/app/schemas/token.py"
  "backend/app/schemas/master_data.py"
  "backend/app/schemas/kpi_submission.py"
  "backend/app/schemas/kpi_assessment.py"
  "backend/app/schemas/assessment.py"
  "backend/app/schemas/leader_kpi.py"
  "backend/app/schemas/bao_cao_xep_loai.py"
  "backend/app/schemas/leave.py"
)

echo ""
echo "📦 Exporting Backend files..."
be_count=0

for file in "${BE_FILES[@]}"; do
  full_path="$PROJECT_DIR/$file"
  if [ -f "$full_path" ]; then
    echo -e "\n\n---\n## 📄 FILE: $file\n\`\`\`python" >> $OUTPUT_BE
    cat "$full_path" >> $OUTPUT_BE
    echo -e "\n\`\`\`" >> $OUTPUT_BE
    be_count=$((be_count + 1))
    echo "  ✅ $file"
  else
    echo "  ⚠️  KHÔNG TÌM THẤY: $file"
  fi
done

echo ""
echo "✅ Backend: $be_count files exported"
echo "📄 Output: $OUTPUT_BE"

# ============================================
# SUMMARY
# ============================================
echo ""
echo "======================================"
echo "📊 EXPORT HOÀN TẤT!"
echo "======================================"
echo "📁 Thư mục: $EXPORT_DIR"
echo ""
echo "📄 Files đã tạo:"
ls -lh $EXPORT_DIR/*_${TIMESTAMP}.md
echo ""
echo "📋 Tổng cộng: $((fe_count + be_count)) files"
echo ""
echo "💡 Hướng dẫn tiếp theo:"
echo "   1. Download files về máy local:"
echo "      scp root@27.71.229.103:$EXPORT_DIR/*_${TIMESTAMP}.md ./"
echo ""
echo "   2. Upload vào Claude Project Knowledge"
echo "      hoặc đính kèm trực tiếp vào chat"
echo "======================================"
