# PROMPT 02A — DATABASE & MIGRATION

> **Phase:** A — Database foundation cho V2_PL3.
> **Phụ thuộc:** Không có. Đây là phase đầu tiên.
> **Output mong đợi:** Migrations Alembic chạy thành công, model SQLAlchemy cập nhật, 2.812 mục PL3 đã seed vào DB.

---

## Bối cảnh

Bạn đang implement Phase A của bộ thay đổi V2_PL3 cho hệ thống KPI Hải quan v1.2.0. Hai thay đổi chính:
1. Đổi mẫu số KPI từ "ngày × 96" → "tổng SP CC kê khai".
2. Thay danh mục 46 mục + cấp độ C1-C5 bằng PL3 (2.812 mục, 5 nhóm, 15 lĩnh vực).

**Phase này CHỈ làm Database, KHÔNG động vào backend service hay frontend.**

---

## Tài liệu tham chiếu

Đọc các file sau **TRƯỚC khi bắt đầu**:

1. `IMPACT_ANALYSIS_KPI_V2_PL3.md` — Phân tích tác động đầy đủ.
2. `BUSINESS_RULES_FINAL.md` — Quy tắc nghiệp vụ gốc.
3. `DATABASE_DESIGN_v2_8_0.md` — Schema hiện tại.
4. `Danh_mục_công_việc.xlsx` (sheet `PL3`) — Nguồn dữ liệu 2.812 mục.

---

## 19 QUYẾT ĐỊNH NGHIỆP VỤ ĐÃ CHỐT (LOCKED — không chất vấn)

[Đọc file `README_BO_PROMPT_02.md` để xem đầy đủ. Phase A chỉ liên quan các quyết định 6, 7, 8, 10, 11, 13, 18.]

**Tóm tắt cho phase này:**
- **(6)** Bảng `cap_do_phuc_tap` GIỮ, soft deactivate sau cutover.
- **(7)** MỞ RỘNG bảng `danh_muc_sp_cong_viec`, KHÔNG tạo bảng mới.
- **(8)** Cột `cap_do_id` trên `ke_khai_cong_viec` thành nullable.
- **(10)(11)** Thêm cờ `version_kekhai`, `version_tinh_diem`.
- **(13)** Snapshot `he_so_quy_doi_snapshot` immutable.
- **(18)** Test env, không cần backfill dữ liệu production.

---

## NHIỆM VỤ

### Task A.1 — Migration: Mở rộng `danh_muc_sp_cong_viec`

**File:** `alembic/versions/pl3_v2_001_extend_danh_muc.py` (tên file theo convention thực tế của project)

**ALTER TABLE `danh_muc_sp_cong_viec`** thêm các cột:

| Cột | Kiểu | NULL | Default | Ghi chú |
|---|---|---|---|---|
| `linh_vuc` | VARCHAR(10) | YES | NULL | Mã lĩnh vực: 'I', 'II', ..., 'XV' |
| `ten_linh_vuc` | VARCHAR(200) | YES | NULL | Tên đầy đủ lĩnh vực |
| `nhiem_vu` | VARCHAR(500) | YES | NULL | Cột B trong Excel |
| `cong_viec_chi_tiet` | TEXT | YES | NULL | Cột C trong Excel |
| `san_pham_dau_ra` | TEXT | YES | NULL | Cột D trong Excel |
| `nhom_pl3` | SMALLINT | YES | NULL | 1-5 |
| `khung_diem_toi_da` | SMALLINT | YES | NULL | 100/200/300/400/500 |
| `diem_kho_sang_tao` | SMALLINT | YES | NULL | Cột G |
| `diem_quy_trinh_thoi_gian` | SMALLINT | YES | NULL | Cột H |
| `diem_phoi_hop` | SMALLINT | YES | NULL | Cột I |
| `diem_pham_vi_ap_dung` | SMALLINT | YES | NULL | Cột J |
| `diem_cham` | SMALLINT | YES | NULL | Cột K (= tổng 4 cột chấm) |
| `he_so_quy_doi` | NUMERIC(8,4) | YES | NULL | Cột L (= diem_cham / 25) |
| `nguon_du_lieu` | VARCHAR(20) | NO | 'V1' | 'V1' hoặc 'PL3' |

**Constraints:**
- `CHECK (nhom_pl3 IS NULL OR nhom_pl3 BETWEEN 1 AND 5)`
- `CHECK (he_so_quy_doi IS NULL OR he_so_quy_doi > 0)`
- `CHECK (nguon_du_lieu IN ('V1', 'PL3'))`

**Indexes:**
- `idx_dmsp_linh_vuc ON (linh_vuc)`
- `idx_dmsp_nhom_pl3 ON (nhom_pl3)`
- `idx_dmsp_nguon_du_lieu ON (nguon_du_lieu)`
- GIN full-text search index trên `(ten_cong_viec, cong_viec_chi_tiet)`:
  ```sql
  CREATE INDEX idx_dmsp_search ON danh_muc_sp_cong_viec
      USING gin (to_tsvector('simple', coalesce(ten_cong_viec,'') || ' ' || coalesce(cong_viec_chi_tiet,'')));
  ```

**Schema change cuối cùng:**
- `ALTER TABLE danh_muc_sp_cong_viec ALTER COLUMN sp_chuan_id DROP NOT NULL` (V2 không bắt buộc map về SP1-SP4 truyền thống).

**Downgrade:** Phải reversible — drop tất cả cột thêm vào.

---

### Task A.2 — Migration: Cờ version cho `ke_khai_cong_viec`

**File:** `alembic/versions/pl3_v2_002_add_version_to_kekhai.py`

```sql
ALTER TABLE ke_khai_cong_viec
    ALTER COLUMN cap_do_id DROP NOT NULL,
    ADD COLUMN version_kekhai VARCHAR(10) NOT NULL DEFAULT 'V1',
    ADD COLUMN he_so_quy_doi_snapshot NUMERIC(8,4),
    ADD COLUMN nhom_pl3_snapshot SMALLINT,
    ADD COLUMN linh_vuc_snapshot VARCHAR(10),
    ADD CONSTRAINT ck_kekhai_version CHECK (version_kekhai IN ('V1', 'V2_PL3')),
    ADD CONSTRAINT ck_kekhai_v2_required CHECK (
        version_kekhai <> 'V2_PL3' OR he_so_quy_doi_snapshot IS NOT NULL
    );

CREATE INDEX idx_kekhai_version ON ke_khai_cong_viec (version_kekhai, thang, nam);
```

**Lưu ý:** `cap_do_id` chỉ bắt buộc cho V1, V2 luôn NULL.

---

### Task A.3 — Migration: Cờ version cho `danh_gia_thang`

**File:** `alembic/versions/pl3_v2_003_add_version_to_danh_gia_thang.py`

```sql
ALTER TABLE danh_gia_thang
    ADD COLUMN tong_sp_ke_khai NUMERIC(12,2),
    ADD COLUMN version_tinh_diem VARCHAR(10) NOT NULL DEFAULT 'V1',
    ADD CONSTRAINT ck_dgthang_version CHECK (version_tinh_diem IN ('V1', 'V2_PL3'));
```

`tong_sp_ke_khai` là cache mẫu số V2, snapshot lúc CCT phê duyệt.

---

### Task A.4 — Migration: Tạo bảng `nhom_cong_viec_pl3`

**File:** `alembic/versions/pl3_v2_004_create_nhom_pl3.py`

```sql
CREATE TABLE nhom_cong_viec_pl3 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nhom SMALLINT UNIQUE NOT NULL CHECK (nhom BETWEEN 1 AND 5),
    ten_nhom VARCHAR(200) NOT NULL,
    diem_toi_da SMALLINT NOT NULL,
    mo_ta TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Seed 5 nhóm:**

| nhom | ten_nhom | diem_toi_da |
|---|---|---|
| 1 | Nhóm 1 - Đơn giản | 100 |
| 2 | Nhóm 2 - Thông thường | 200 |
| 3 | Nhóm 3 - Nâng cao | 300 |
| 4 | Nhóm 4 - Phức tạp | 400 |
| 5 | Nhóm 5 - Đặc thù | 500 |

---

### Task A.5 — Migration: Cờ `kpi_version_pinned` trên `cong_chuc`

**File:** `alembic/versions/pl3_v2_005_add_version_pin_to_cong_chuc.py`

```sql
ALTER TABLE cong_chuc
    ADD COLUMN kpi_version_pinned VARCHAR(10),
    ADD CONSTRAINT ck_cc_kpi_version CHECK (
        kpi_version_pinned IS NULL OR kpi_version_pinned IN ('V1', 'V2_PL3')
    );
```

NULL nghĩa là dùng default của hệ thống (V1 cho đến cutover).

---

### Task A.6 — Cập nhật SQLAlchemy Models

Cập nhật các model sau (giữ nguyên model cũ, chỉ thêm field mới):

| File | Thay đổi |
|---|---|
| `backend/app/models/task_catalog.py` | Thêm 14 field PL3 vào `DanhMucSpCongViec`. Tạo model mới `NhomCongViecPL3`. |
| `backend/app/models/kpi_submission.py` | Thêm `version_kekhai`, `he_so_quy_doi_snapshot`, `nhom_pl3_snapshot`, `linh_vuc_snapshot`. Đổi `cap_do_id` thành nullable. |
| `backend/app/models/kpi_assessment.py` | Thêm `tong_sp_ke_khai`, `version_tinh_diem`. |
| `backend/app/models/cong_chuc.py` | Thêm `kpi_version_pinned`. |

Mỗi model phải có docstring mô tả nguồn gốc field (V1 hay V2_PL3) để dev sau dễ hiểu.

---

### Task A.7 — Script seed PL3 từ Excel

**File:** `scripts/seed_pl3_catalog.py` (chạy độc lập, không phải Alembic migration vì data lớn).

**Logic:**

1. **Đọc** file `Danh_mục_công_việc.xlsx`, sheet `PL3`, từ row 8 trở đi.

2. **Parse 15 lĩnh vực** từ section header rows. Lĩnh vực nằm ở **dòng tiêu đề** (cột A bắt đầu bằng La Mã: 'I.', 'II.', ..., 'XV.'). Phải dùng biến `current_linh_vuc` cập nhật khi gặp section header, gán cho mọi sản phẩm phía dưới cho đến section tiếp theo.

   Mapping section header → mã:
   ```
   Row 9   → I
   Row 374 → II
   Row 426 → III
   Row 585 → IV
   Row 876 → V
   Row 1023 → VI
   Row 1534 → VII
   Row 2176 → VIII
   Row 2247 → IX
   Row 2512 → X
   Row 2727 → XI
   Row 2956 → XII
   Row 3040 → XIII
   Row 3159 → XIV
   Row 3300 → XV
   ```
   (Verify lại bằng cách parse từ `re.match(r'^([IVXLCDM]+)\.', val_a.strip())` — KHÔNG hardcode, chỉ dùng row numbers ở trên để verify khớp)

3. **Skip dòng nhiệm vụ** (cột A có số `1.0`, `2.0`, ..., không phải mã con). Chỉ lấy dòng có `cong_viec_chi_tiet` (cột C) và `san_pham_dau_ra` (cột D).

4. **Tạo `ma_danh_muc`** unique cho từng row: pattern `PL3-{linh_vuc}-{stt}` (ví dụ: `PL3-I-2.1`).

5. **Validate cứng** trước khi insert:
   - `diem_kho_sang_tao + diem_quy_trinh_thoi_gian + diem_phoi_hop + diem_pham_vi_ap_dung == diem_cham` (tolerance 0)
   - `abs(he_so_quy_doi - diem_cham / 25) < 0.001`
   - `khung_diem_toi_da` ∈ {100, 200, 300, 400, 500} match `nhom_pl3` (100 → 1, 200 → 2, ...)
   - Nếu sai → **dừng**, log row bị lỗi, KHÔNG insert.

6. **Insert** với `nguon_du_lieu='PL3'`, `sp_chuan_id=NULL`, `is_active=TRUE`. Idempotent: `ON CONFLICT (ma_danh_muc) DO UPDATE SET ...`.

7. **Output cuối:** Báo cáo tổng số mục đã insert / update / skip / error.

**Kỳ vọng:** ~2.812 mục thành công.

---

### Task A.8 — Verification queries

Sau khi chạy xong tất cả migration + seed, **chạy các query sau** và in kết quả ra console:

```sql
-- 1. Đếm tổng số mục PL3
SELECT nguon_du_lieu, COUNT(*) FROM danh_muc_sp_cong_viec GROUP BY nguon_du_lieu;
-- Kỳ vọng: V1 = 46 (giữ nguyên), PL3 ≈ 2.812

-- 2. Phân bố theo lĩnh vực
SELECT linh_vuc, COUNT(*) FROM danh_muc_sp_cong_viec
WHERE nguon_du_lieu='PL3' GROUP BY linh_vuc ORDER BY linh_vuc;
-- Kỳ vọng: 15 lĩnh vực, không có NULL

-- 3. Phân bố theo nhóm
SELECT nhom_pl3, COUNT(*), MIN(he_so_quy_doi), MAX(he_so_quy_doi)
FROM danh_muc_sp_cong_viec WHERE nguon_du_lieu='PL3' GROUP BY nhom_pl3 ORDER BY nhom_pl3;

-- 4. Validate constraint
SELECT COUNT(*) FROM danh_muc_sp_cong_viec
WHERE nguon_du_lieu='PL3' AND (
    diem_kho_sang_tao + diem_quy_trinh_thoi_gian + diem_phoi_hop + diem_pham_vi_ap_dung != diem_cham
    OR ABS(he_so_quy_doi - diem_cham::numeric / 25) > 0.001
);
-- Kỳ vọng: 0

-- 5. Check version flag default
SELECT version_kekhai, COUNT(*) FROM ke_khai_cong_viec GROUP BY version_kekhai;
SELECT version_tinh_diem, COUNT(*) FROM danh_gia_thang GROUP BY version_tinh_diem;
-- Kỳ vọng: tất cả là V1 (vì test env có sẵn dữ liệu V1)
```

---

## ACCEPTANCE CRITERIA

Phase A coi là DONE khi tất cả các điều kiện sau đúng:

- [ ] 5 file migration Alembic tồn tại trong `alembic/versions/`, đều reversible (có `downgrade()` đầy đủ).
- [ ] `alembic upgrade head` chạy thành công không lỗi.
- [ ] `alembic downgrade -5` rồi `alembic upgrade head` lại — chạy thành công (test reversibility).
- [ ] 4 file model SQLAlchemy đã cập nhật, import được không lỗi.
- [ ] Script seed chạy thành công, in báo cáo "X mục inserted, Y mục updated, 0 errors".
- [ ] Tất cả 5 verification query trả kết quả ĐÚNG kỳ vọng.
- [ ] Bảng `nhom_cong_viec_pl3` có đúng 5 row với `nhom` từ 1-5.

---

## STOP và báo cáo

Sau khi xong Task A.8, **DỪNG LẠI**. KHÔNG sang Phase B. Báo cáo cho user:

```
## Phase A Report

### Migrations applied
- [ ] pl3_v2_001_extend_danh_muc — applied at <timestamp>
- [ ] pl3_v2_002_add_version_to_kekhai — applied at <timestamp>
- [ ] pl3_v2_003_add_version_to_danh_gia_thang — applied at <timestamp>
- [ ] pl3_v2_004_create_nhom_pl3 — applied at <timestamp>
- [ ] pl3_v2_005_add_version_pin_to_cong_chuc — applied at <timestamp>

### Seed result
- Total inserted: <N>
- Total updated: <N>
- Errors: <N> (chi tiết nếu có)

### Verification query output
[paste output of 5 queries]

### Issues encountered
[Liệt kê mọi vấn đề: schema conflict, data inconsistency, anything cần user quyết]

### Ready for Phase B?
[YES / NO + lý do]
```

KHÔNG implement bất cứ logic nghiệp vụ nào (không sửa service, không sửa endpoint, không sửa frontend) trong phase này.
