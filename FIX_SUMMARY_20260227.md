# TỔNG HỢP FIX 2 LỖI PRODUCTION - 27/02/2026

## Executive Summary

Branch: `fix/kpi-improvements-v2`
Commit: `a4d052d`
Status: ✅ Code đã fix, chờ deploy lên production

---

## LỖI 1: Migration chưa chạy trên production

### Triệu chứng:
```
ERROR: column ke_khai_cong_viec.don_vi_id_snapshot does not exist
```

### Root Cause:
- Migration file `add_don_vi_snapshot_20260227.py` đã được tạo và staged
- Migration chain hợp lệ: `create_forum_schema_20260225` → `add_don_vi_snapshot_20260227`
- NHƯNG chưa chạy `alembic upgrade head` trên production

### Tác động:
- Backend crash khi truy cập endpoint liên quan kê khai/đánh giá/báo cáo
- Ảnh hưởng: 549 users không thể sử dụng hệ thống

### Giải pháp:
**KHÔNG cần sửa code**, chỉ cần chạy migration trên production.

Xem chi tiết: [MIGRATION_GUIDE_20260227.md](./MIGRATION_GUIDE_20260227.md)

### Checklist deploy:
```bash
# 1. Backup database
pg_dump ... > backup.dump

# 2. Chạy migration
cd /root/kpi-haiquan/backend
source .venv/bin/activate
alembic upgrade head

# 3. Restart backend
pm2 restart kpi-backend

# 4. Verify
psql -c "\d ke_khai_cong_viec" | grep don_vi_id_snapshot
```

---

## LỖI 2: Báo cáo xếp loại vẫn hiện CC đã chuyển đơn vị

### Triệu chứng:
- Đơn vị Nghiệp vụ 2 có 74 CC trong báo cáo tháng 1/2026
- Thực tế hiện tại chỉ còn 72 CC (2 CC đã chuyển đi)
- Ngoài (trang danh sách báo cáo) hiện đúng 72, nhưng trong (chi tiết báo cáo) hiện 74

### Root Cause:
Khi admin chuyển CC từ Đơn vị A → Đơn vị B:

**Code CŨ** (backend/app/api/v1/endpoints/admin.py dòng 948-968):
```python
# Chỉ xóa khỏi báo cáo NHAP hoặc TU_CHOI
chi_tiet_to_delete_stmt = (
    select(ChiTietXepLoai.id)
    .join(BaoCaoXepLoai)
    .where(ChiTietXepLoai.cong_chuc_id == user_id)
    .where(
        or_(
            BaoCaoXepLoai.trang_thai == "NHAP",
            BaoCaoXepLoai.trang_thai == "TU_CHOI"
            # ← THIẾU: "CHO_PHE_DUYET"
        )
    )
)
```

**Kịch bản tái hiện:**
1. Đơn vị A có 74 CC
2. Đội trưởng tạo báo cáo tháng 1/2026 → 74 records trong `chi_tiet_xep_loai`
3. Đội trưởng gửi duyệt → trạng thái = `CHO_PHE_DUYET`
4. Admin chuyển 2 CC sang Đơn vị B
5. Code chỉ xóa khỏi báo cáo `NHAP`/`TU_CHOI`, KHÔNG xóa khỏi `CHO_PHE_DUYET`
6. Báo cáo vẫn có 74 CC, mặc dù đơn vị chỉ còn 72 CC

### Giải pháp:
**Code MỚI** (đã fix):
```python
# Xóa khỏi báo cáo NHAP, CHO_PHE_DUYET, hoặc TU_CHOI
chi_tiet_to_delete_stmt = (
    select(ChiTietXepLoai.id)
    .join(BaoCaoXepLoai)
    .where(ChiTietXepLoai.cong_chuc_id == user_id)
    .where(
        or_(
            BaoCaoXepLoai.trang_thai == "NHAP",
            BaoCaoXepLoai.trang_thai == "CHO_PHE_DUYET",  # ← FIX
            BaoCaoXepLoai.trang_thai == "TU_CHOI"
        )
    )
)
```

### Tác động sau fix:
- Khi CC chuyển đơn vị, sẽ bị xóa khỏi tất cả báo cáo **chưa phê duyệt** (NHAP, CHO_PHE_DUYET, TU_CHOI)
- Báo cáo **đã phê duyệt** (DA_PHE_DUYET) vẫn giữ nguyên → đúng với snapshot lịch sử
- Số lượng CC trong báo cáo = số lượng CC hiện tại của đơn vị

### Files thay đổi:
```
backend/app/api/v1/endpoints/admin.py (dòng 948-960)
```

### Commit:
```
a4d052d - fix(admin): xóa CC khỏi báo cáo CHO_PHE_DUYET khi chuyển đơn vị
```

---

## KIẾN TRÚC DON_VI_ID_SNAPSHOT

### Tại sao cần snapshot?

**Vấn đề:**
- CC chuyển từ Đơn vị A (1/2026) → Đơn vị B (2/2026)
- `cong_chuc.don_vi_id` thay đổi → JOIN sẽ sai
- Báo cáo tháng 1/2026 của Đơn vị A THIẾU CC này

**Giải pháp:**
- Khi tạo kê khai/đánh giá, snapshot `don_vi_id` vào `don_vi_id_snapshot`
- Báo cáo JOIN bằng `don_vi_id_snapshot` thay vì `cong_chuc.don_vi_id`

### Workflow snapshot:

```python
# 1. Khi CC kê khai công việc (ke_khai.py dòng 1218)
ke_khai = KeKhaiCongViec(
    cong_chuc_id=user.id,
    don_vi_id_snapshot=user.don_vi_id,  # ← Snapshot tại thời điểm kê khai
    thang=1,
    nam=2026,
    ...
)

# 2. Khi hệ thống tạo đánh giá tháng (danh_gia.py dòng 124)
danh_gia = DanhGiaThang(
    cong_chuc_id=user.id,
    don_vi_id_snapshot=user.don_vi_id,  # ← Snapshot tại thời điểm đánh giá
    thang=1,
    nam=2026,
    ...
)

# 3. Khi tạo báo cáo xếp loại (bao_cao_xep_loai.py dòng 606-636)
cc_stmt = (
    select(CongChuc)
    .join(
        DanhGiaThang,
        and_(
            DanhGiaThang.cong_chuc_id == CongChuc.id,
            DanhGiaThang.thang == thang,
            DanhGiaThang.nam == nam,
            DanhGiaThang.don_vi_id_snapshot == don_vi_id,  # ← JOIN bằng snapshot
        )
    )
)
```

### Kịch bản cụ thể:

**Tháng 1/2026:**
- CC-A thuộc Đơn vị Nghiệp vụ 2
- Kê khai công việc → `ke_khai.don_vi_id_snapshot = "uuid-nv2"`
- Đánh giá tháng → `danh_gia.don_vi_id_snapshot = "uuid-nv2"`

**15/02/2026:**
- Admin chuyển CC-A sang Đơn vị Nghiệp vụ 3
- `cong_chuc.don_vi_id = "uuid-nv3"` (thay đổi)
- Snapshot tháng 1 VẪN GIỮ NGUYÊN: `don_vi_id_snapshot = "uuid-nv2"`

**20/02/2026:**
- Đội trưởng NV2 mở báo cáo tháng 1/2026
- Query JOIN theo `don_vi_id_snapshot = "uuid-nv2"`
- Vẫn tìm thấy CC-A trong báo cáo tháng 1/2026 ✅

**Tháng 2/2026:**
- CC-A kê khai công việc MỚI → `ke_khai.don_vi_id_snapshot = "uuid-nv3"` (đơn vị mới)
- Báo cáo NV3 tháng 2/2026 sẽ có CC-A ✅
- Báo cáo NV2 tháng 2/2026 KHÔNG có CC-A ✅

---

## FILES LIÊN QUAN

### Migration:
- `backend/alembic/versions/add_don_vi_snapshot_20260227.py` (staged, chưa chạy)

### Models (đã cập nhật):
- `backend/app/models/kpi_submission.py` (dòng 117-122: `KeKhaiCongViec.don_vi_id_snapshot`)
- `backend/app/models/kpi_assessment.py` (dòng 124-129: `DanhGiaThang.don_vi_id_snapshot`)

### Endpoints (đã sử dụng snapshot):
- `backend/app/api/v1/endpoints/ke_khai.py` (dòng 897, 1218: lưu snapshot khi CREATE)
- `backend/app/api/v1/endpoints/danh_gia.py` (dòng 124: lưu snapshot khi CREATE)
- `backend/app/api/v1/endpoints/bao_cao_xep_loai.py` (dòng 606-636: JOIN bằng snapshot)
- `backend/app/api/v1/endpoints/admin.py` (dòng 948-968: xóa khỏi báo cáo khi chuyển) ← **ĐÃ FIX**

---

## TESTING PLAN

### Test Case 1: Migration
1. SSH vào production: `ssh root@79.108.216.189`
2. Backup database
3. Chạy `alembic upgrade head`
4. Verify cột tồn tại: `\d ke_khai_cong_viec`
5. Restart backend
6. Kiểm tra không có lỗi trong logs

### Test Case 2: Snapshot khi kê khai mới
1. User kê khai công việc tháng 2/2026
2. Query database:
   ```sql
   SELECT cong_chuc_id, don_vi_id_snapshot, thang, nam
   FROM ke_khai_cong_viec
   WHERE thang = 2 AND nam = 2026
   ORDER BY created_at DESC LIMIT 1;
   ```
3. `don_vi_id_snapshot` PHẢI = `cong_chuc.don_vi_id` hiện tại

### Test Case 3: Chuyển đơn vị
1. Đơn vị A có báo cáo tháng 2/2026 trạng thái `CHO_PHE_DUYET` với 10 CC
2. Admin chuyển 1 CC từ Đơn vị A → Đơn vị B
3. Mở lại báo cáo tháng 2/2026 của Đơn vị A
4. Báo cáo phải còn 9 CC (đã xóa CC chuyển đi)

### Test Case 4: Báo cáo đã phê duyệt
1. Đơn vị A có báo cáo tháng 1/2026 trạng thái `DA_PHE_DUYET` với 10 CC
2. Admin chuyển 1 CC từ Đơn vị A → Đơn vị B
3. Mở lại báo cáo tháng 1/2026 của Đơn vị A
4. Báo cáo VẪN có 10 CC (KHÔNG xóa vì đã phê duyệt - snapshot lịch sử)

---

## DEPLOY CHECKLIST

### Pre-deployment:
- [x] Code đã commit: `a4d052d`
- [x] Migration file tồn tại: `add_don_vi_snapshot_20260227.py`
- [x] Tài liệu migration: `MIGRATION_GUIDE_20260227.md`
- [x] Models đã cập nhật: `kpi_submission.py`, `kpi_assessment.py`
- [x] Endpoints đã sử dụng snapshot: `ke_khai.py`, `danh_gia.py`, `bao_cao_xep_loai.py`
- [x] Fix transfer_user logic: `admin.py`

### Deployment steps:
1. [ ] Backup production database
2. [ ] Git pull trên production: `git pull origin fix/kpi-improvements-v2`
3. [ ] Chạy migration: `alembic upgrade head`
4. [ ] Restart backend: `pm2 restart kpi-backend`
5. [ ] Verify logs: `pm2 logs kpi-backend --lines 100`
6. [ ] Test tạo kê khai mới
7. [ ] Test mở báo cáo xếp loại
8. [ ] Test chuyển CC giữa các đơn vị

### Post-deployment:
- [ ] Monitor logs 30 phút
- [ ] Kiểm tra không có lỗi `column does not exist`
- [ ] User feedback: CC kê khai/báo cáo hoạt động bình thường
- [ ] Báo cáo số lượng CC đúng với thực tế

---

## ROLLBACK PLAN

Nếu có vấn đề nghiêm trọng:

```bash
# 1. Rollback code
git checkout main
pm2 restart kpi-backend

# 2. Rollback migration (nếu đã chạy)
cd backend
source .venv/bin/activate
alembic downgrade create_forum_schema_20260225

# 3. Restore database (nếu cần)
pg_restore -d kpi_haiquan backup.dump
```

**LƯU Ý:** Rollback migration sẽ DROP cột `don_vi_id_snapshot` → backend crash nếu code vẫn sử dụng.

---

## IMPACT ANALYSIS

### Người dùng ảnh hưởng:
- **Tất cả 549 users** (hiện tại không thể kê khai/xem báo cáo vì lỗi migration)
- **15 Đội trưởng** (không thể lập báo cáo xếp loại)
- **CCT** (không thể phê duyệt báo cáo)

### Chức năng ảnh hưởng:
- ❌ Kê khai công việc (crash)
- ❌ Phê duyệt kê khai (crash)
- ❌ Đánh giá tháng (crash)
- ❌ Báo cáo xếp loại (crash hoặc hiện sai số liệu)
- ✅ Đăng nhập (OK)
- ✅ Quản lý user (OK)
- ✅ Nghỉ phép (OK)

### Ưu tiên:
**P0 - CRITICAL** - Hệ thống không sử dụng được

### Timeline:
- 27/02/2026 10:00 - Phát hiện lỗi
- 27/02/2026 12:00 - Phân tích root cause
- 27/02/2026 14:00 - Fix code + tạo tài liệu
- 27/02/2026 15:00 - **Chờ deploy lên production**

---

**Người thực hiện:** KPI Specialist (Claude Opus 4.6)
**Ngày:** 27/02/2026
**Branch:** fix/kpi-improvements-v2
**Commit:** a4d052d
