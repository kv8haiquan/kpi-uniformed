# HƯỚNG DẪN CHẠY MIGRATION TRÊN PRODUCTION

## Ngày: 27/02/2026
## Migration: `add_don_vi_snapshot_20260227`

---

## 1. VẤN ĐỀ

### Lỗi hiện tại:
```
column ke_khai_cong_viec.don_vi_id_snapshot does not exist
```

### Nguyên nhân:
Migration file `add_don_vi_snapshot_20260227.py` đã được tạo và staged nhưng **CHƯA CHẠY** trên production database.

### Tác động:
- Backend crash khi truy cập endpoint liên quan đến kê khai/đánh giá
- Không thể tạo/đọc báo cáo xếp loại đơn vị

---

## 2. MIGRATION NÀY LÀM GÌ?

Migration này thêm cột `don_vi_id_snapshot` vào 2 bảng:

### 2.1. Bảng `danh_gia_thang`
```sql
ALTER TABLE danh_gia_thang
ADD COLUMN don_vi_id_snapshot UUID REFERENCES don_vi(id);

CREATE INDEX idx_danh_gia_don_vi_snapshot
ON danh_gia_thang(don_vi_id_snapshot, thang, nam);
```

### 2.2. Bảng `ke_khai_cong_viec`
```sql
ALTER TABLE ke_khai_cong_viec
ADD COLUMN don_vi_id_snapshot UUID REFERENCES don_vi(id);

CREATE INDEX idx_ke_khai_don_vi_snapshot
ON ke_khai_cong_viec(don_vi_id_snapshot, thang, nam);
```

### 2.3. Backfill dữ liệu cũ
```sql
-- Backfill danh_gia_thang
UPDATE danh_gia_thang
SET don_vi_id_snapshot = (
    SELECT don_vi_id FROM cong_chuc
    WHERE cong_chuc.id = danh_gia_thang.cong_chuc_id
)
WHERE don_vi_id_snapshot IS NULL;

-- Backfill ke_khai_cong_viec
UPDATE ke_khai_cong_viec
SET don_vi_id_snapshot = (
    SELECT don_vi_id FROM cong_chuc
    WHERE cong_chuc.id = ke_khai_cong_viec.cong_chuc_id
)
WHERE don_vi_id_snapshot IS NULL;
```

---

## 3. TẠI SAO CẦN `don_vi_id_snapshot`?

### Vấn đề:
Khi Admin chuyển CC từ Đơn vị A → Đơn vị B:
- `cong_chuc.don_vi_id` thay đổi thành B
- Nhưng kê khai/đánh giá THÁNG TRƯỚC vẫn thuộc Đơn vị A
- Báo cáo Đơn vị A sẽ THIẾU CC này → sai số liệu

### Giải pháp:
Khi tạo kê khai/đánh giá, **snapshot** `don_vi_id` vào `don_vi_id_snapshot`:
```python
ke_khai = KeKhaiCongViec(
    cong_chuc_id=user.id,
    don_vi_id_snapshot=user.don_vi_id,  # ← Snapshot tại thời điểm kê khai
    thang=1,
    nam=2026,
    ...
)
```

Báo cáo xếp loại JOIN bằng `don_vi_id_snapshot` thay vì `cong_chuc.don_vi_id`.

---

## 4. HƯỚNG DẪN CHẠY MIGRATION

### 4.1. Kiểm tra revision hiện tại

SSH vào production server:
```bash
ssh root@79.108.216.189
cd /root/kpi-haiquan/backend
```

Kiểm tra revision:
```bash
source .venv/bin/activate
alembic current
```

Output mong đợi:
```
create_forum_schema_20260225 (head)
```

Nếu output là `add_don_vi_snapshot_20260227` → migration đã chạy rồi, KHÔNG cần làm gì.

---

### 4.2. Backup database TRƯỚC KHI CHẠY

**BẮT BUỘC backup trước khi migration:**

```bash
# Backup full database
PGPASSWORD='<production_password>' pg_dump \
  -h localhost -U kpi_user -d kpi_haiquan \
  --format=custom \
  --file=/root/backups/kpi_haiquan_before_snapshot_migration_$(date +%Y%m%d_%H%M%S).dump

# Verify backup
ls -lh /root/backups/kpi_haiquan_before_snapshot_migration_*.dump
```

---

### 4.3. Chạy migration

```bash
cd /root/kpi-haiquan/backend
source .venv/bin/activate

# Xem migrations sẽ chạy
alembic upgrade head --sql

# Nếu OK, chạy thật
alembic upgrade head
```

Output mong đợi:
```
INFO  [alembic.runtime.migration] Running upgrade create_forum_schema_20260225 -> add_don_vi_snapshot_20260227, Add don_vi_id_snapshot to DanhGiaThang and KeKhaiCongViec
```

---

### 4.4. Verify migration

Kiểm tra cột đã tồn tại:
```bash
PGPASSWORD='<production_password>' psql \
  -h localhost -U kpi_user -d kpi_haiquan \
  -c "\d danh_gia_thang" | grep don_vi_id_snapshot

PGPASSWORD='<production_password>' psql \
  -h localhost -U kpi_user -d kpi_haiquan \
  -c "\d ke_khai_cong_viec" | grep don_vi_id_snapshot
```

Output mong đợi:
```
don_vi_id_snapshot | uuid | | |
```

Kiểm tra backfill data:
```sql
-- Đếm records có snapshot
SELECT
  (SELECT COUNT(*) FROM danh_gia_thang WHERE don_vi_id_snapshot IS NOT NULL) as dg_filled,
  (SELECT COUNT(*) FROM ke_khai_cong_viec WHERE don_vi_id_snapshot IS NOT NULL) as kk_filled;
```

Tất cả records cũ phải có `don_vi_id_snapshot IS NOT NULL`.

---

### 4.5. Restart backend

```bash
pm2 restart kpi-backend
pm2 logs kpi-backend --lines 50
```

Kiểm tra log KHÔNG có lỗi `column don_vi_id_snapshot does not exist`.

---

## 5. ROLLBACK (NẾU CẦN)

**Chỉ rollback nếu migration gây lỗi nghiêm trọng.**

```bash
cd /root/kpi-haiquan/backend
source .venv/bin/activate

# Rollback 1 bước
alembic downgrade -1

# Hoặc rollback về revision cụ thể
alembic downgrade create_forum_schema_20260225
```

Migration `downgrade()` sẽ:
- Drop indexes `idx_danh_gia_don_vi_snapshot` và `idx_ke_khai_don_vi_snapshot`
- Drop foreign key constraints
- Drop columns `don_vi_id_snapshot`

**LƯU Ý:** Sau khi rollback, backend SẼ CRASH vì code đã sử dụng `don_vi_id_snapshot`.

---

## 6. TESTING SAU KHI MIGRATION

### Test 1: Tạo kê khai mới
```bash
curl -X POST https://kpihaiquan.vn/api/v1/ke-khai \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "thang": 2,
    "nam": 2026,
    "ngay_thuc_hien": "2026-02-27",
    "danh_muc_sp_id": "<uuid>",
    "cap_do_id": "<uuid>",
    "so_luong": 1,
    "nguoi_phe_duyet_id": "<uuid>"
  }'
```

Kiểm tra database:
```sql
SELECT cong_chuc_id, don_vi_id_snapshot, thang, nam
FROM ke_khai_cong_viec
WHERE thang = 2 AND nam = 2026
ORDER BY created_at DESC LIMIT 5;
```

`don_vi_id_snapshot` PHẢI KHÔNG NULL.

---

### Test 2: Mở báo cáo xếp loại
```bash
curl https://kpihaiquan.vn/api/v1/bao-cao-xep-loai/don-vi/thang/1/nam/2026 \
  -H "Authorization: Bearer <token>"
```

Response PHẢI thành công, KHÔNG có lỗi `column does not exist`.

---

## 7. CHECKLIST

- [ ] Backup database
- [ ] Verify file migration tồn tại: `backend/alembic/versions/add_don_vi_snapshot_20260227.py`
- [ ] Chạy `alembic current` → hiện `create_forum_schema_20260225`
- [ ] Chạy `alembic upgrade head`
- [ ] Verify cột `don_vi_id_snapshot` đã tồn tại
- [ ] Verify backfill data (tất cả records cũ có snapshot)
- [ ] Restart backend: `pm2 restart kpi-backend`
- [ ] Test tạo kê khai mới
- [ ] Test mở báo cáo xếp loại
- [ ] Monitor logs 30 phút sau khi deploy

---

## 8. LIÊN HỆ

Nếu có vấn đề khi chạy migration:

1. Kiểm tra logs: `pm2 logs kpi-backend --err --lines 100`
2. Rollback nếu cần: `alembic downgrade -1`
3. Restore backup database nếu cần:
   ```bash
   PGPASSWORD='<password>' pg_restore \
     -h localhost -U kpi_user -d kpi_haiquan \
     --clean --if-exists \
     /root/backups/kpi_haiquan_before_snapshot_migration_*.dump
   ```

---

**Người tạo:** KPI Specialist (Claude Opus 4.6)
**Ngày:** 27/02/2026
**Branch:** fix/kpi-improvements-v2
**Commit:** a4d052d (fix transfer_user logic)
