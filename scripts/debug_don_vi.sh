#!/bin/bash
# Debug: Xem toàn bộ bảng don_vi
DB_USER="kpi_user"
DB_NAME="kpi_haiquan"
DB_HOST="localhost"

echo "========================================="
echo "  DEBUG: BẢNG DON_VI"
echo "========================================="
echo ""

echo "1. Cấu trúc bảng:"
psql -U $DB_USER -h $DB_HOST -d $DB_NAME -c "\d don_vi"

echo ""
echo "2. Toàn bộ dữ liệu (không filter):"
psql -U $DB_USER -h $DB_HOST -d $DB_NAME -c "
    SELECT id, ma_don_vi, ten_don_vi, ten_viet_tat, loai_don_vi, 
           is_active, is_deleted, thu_tu_hien_thi
    FROM don_vi
    ORDER BY thu_tu_hien_thi, ma_don_vi;
"

echo ""
echo "3. Tổng số đơn vị:"
psql -U $DB_USER -h $DB_HOST -d $DB_NAME -c "
    SELECT COUNT(*) AS tong,
           COUNT(*) FILTER (WHERE is_active = TRUE) AS active,
           COUNT(*) FILTER (WHERE is_deleted = TRUE) AS deleted
    FROM don_vi;
"