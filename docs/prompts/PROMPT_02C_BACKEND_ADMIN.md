# PROMPT 02C — BACKEND ADMIN + TESTS

> **Phase:** C — Backend admin CRUD danh mục PL3 + import Excel + tests đầy đủ.
> **Phụ thuộc:** Phase A và B đã DONE.
> **Output mong đợi:** Admin có thể CRUD danh mục PL3 qua API, import Excel mới khi Bộ ban hành sửa đổi, có bộ test toàn diện.

---

## Bối cảnh

Phase A đã có schema và data. Phase B đã có logic tính KPI V2. Phase C bổ sung:
1. Admin endpoints để CRUD danh mục PL3 (CRUD 14 cột mới).
2. Import Excel (dry-run + commit) — khi Bộ Nội vụ/Hải quan ban hành PL3 sửa đổi, admin có thể upload Excel mới mà không cần migration code.
3. Test suite toàn diện (unit + integration + regression V1).

---

## Tài liệu tham chiếu

1. `IMPACT_ANALYSIS_KPI_V2_PL3.md` — §3.4, §6.1.
2. `README_BO_PROMPT_02.md` — 19 LOCKED DECISIONS.
3. Phase A scripts/seed_pl3_catalog.py (tham chiếu logic parse Excel).

---

## LOCKED DECISIONS — phase này dùng

Quyết định liên quan: **2, 7, 13, 14, 15**.

**Tóm tắt:**
- **(7)** Mở rộng cùng bảng `danh_muc_sp_cong_viec`, dùng `nguon_du_lieu` để phân biệt V1/PL3.
- **(13)** Snapshot final — admin sửa hệ số KHÔNG ảnh hưởng kê khai cũ.
- **(14)** KHÔNG cho phép override hệ số ở bất kỳ đâu trong scope V2.
- **(15)** Admin có thể config "lĩnh vực mặc định" cho từng đơn vị.

---

## NHIỆM VỤ

### Task C.1 — CRUD danh mục PL3

**File:** Mở rộng `backend/app/api/v1/endpoints/admin.py` (thêm route, không sửa V1).

**Routes mới:**

```
GET    /api/admin/danh-muc-pl3                    # List với filter
POST   /api/admin/danh-muc-pl3                    # Tạo mục mới
GET    /api/admin/danh-muc-pl3/{id}               # Detail
PUT    /api/admin/danh-muc-pl3/{id}               # Sửa
DELETE /api/admin/danh-muc-pl3/{id}               # Soft delete (is_active=FALSE)

# Mục V1 cũ — read-only sau cutover
GET    /api/admin/danh-muc-v1                     # List V1 (read-only)
PUT    /api/admin/danh-muc-v1/{id}/deactivate     # Soft deactivate (admin)
```

**Validation cho POST/PUT PL3:**

```python
class DanhMucPL3Request(BaseModel):
    ten_cong_viec: str = Field(..., max_length=500)
    linh_vuc: str = Field(..., regex=r'^(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV)$')
    nhiem_vu: Optional[str]
    cong_viec_chi_tiet: str
    san_pham_dau_ra: str
    nhom_pl3: int = Field(..., ge=1, le=5)
    diem_kho_sang_tao: int = Field(..., ge=0)
    diem_quy_trinh_thoi_gian: int = Field(..., ge=0)
    diem_phoi_hop: int = Field(..., ge=0)
    diem_pham_vi_ap_dung: int = Field(..., ge=0)
    
    @validator('*', pre=False)
    def validate_consistency(cls, values):
        # Validate các điểm thành phần phải nhất quán:
        # diem_cham = sum(4 cột chấm)
        # he_so_quy_doi = diem_cham / 25
        # khung_diem_toi_da phải khớp với nhom_pl3
        ...
```

**Auto-compute trên backend:**
```python
diem_cham = (
    diem_kho_sang_tao + diem_quy_trinh_thoi_gian 
    + diem_phoi_hop + diem_pham_vi_ap_dung
)
he_so_quy_doi = Decimal(diem_cham) / Decimal("25")
khung_diem_toi_da = {1: 100, 2: 200, 3: 300, 4: 400, 5: 500}[nhom_pl3]
nguon_du_lieu = "PL3"
```

**Validation tổng:** `diem_cham <= khung_diem_toi_da` (không cho điểm chấm vượt khung của nhóm).

**Audit log mọi thao tác:** action `ADMIN_DANH_MUC_PL3_CREATE/UPDATE/DELETE`, lưu cả old value và new value cho UPDATE.

---

### Task C.2 — Import Excel với dry-run

**File:** `backend/app/api/v1/endpoints/admin_import.py` (tạo mới).

**Routes:**

```
POST /api/admin/danh-muc-pl3/import/dry-run    # Multipart upload, validate, KHÔNG insert
POST /api/admin/danh-muc-pl3/import/commit     # Multipart upload, validate, INSERT
```

**Logic:**

1. **Dry-run:**
   - User upload file `.xlsx`.
   - Backend đọc sheet `PL3`, parse 2.812+ rows (logic giống Phase A Task A.7).
   - Validate từng row.
   - **KHÔNG insert vào DB.**
   - Trả về JSON:
     ```json
     {
       "summary": {
         "total_rows": 2812,
         "valid": 2810,
         "invalid": 2,
         "will_insert": 0,
         "will_update": 2810,
         "will_delete": 0
       },
       "errors": [
         {"row": 145, "ma_danh_muc": "PL3-I-2.5", "error": "diem_cham != sum(4 cột chấm): 170 vs 165"},
         {"row": 892, "ma_danh_muc": "PL3-V-3.2", "error": "he_so_quy_doi != diem_cham/25: 6.4 vs 6.8"}
       ],
       "preview": [/* 10 rows đầu để user xem */]
     }
     ```

2. **Commit:**
   - User upload lại file (hoặc gửi token từ dry-run, tùy implementation).
   - Backend parse lại, validate lại.
   - Nếu có error → reject toàn bộ (atomic).
   - Insert/update trong 1 transaction (rollback nếu fail).
   - Audit log: action `ADMIN_IMPORT_PL3`, lưu file hash + summary.

**Strategy update:** Dùng `ON CONFLICT (ma_danh_muc) DO UPDATE` — idempotent, không tạo trùng.

**KHÔNG xoá** mục cũ trong V2 không có trong file mới (admin tự `is_active=FALSE` riêng nếu cần). Lý do: tránh phá FK của kê khai cũ.

**Giới hạn:** File size ≤ 10MB, max 5000 rows.

---

### Task C.3 — Endpoint config "lĩnh vực mặc định" cho đơn vị

**File:** Mở rộng `backend/app/api/v1/endpoints/admin.py`.

**Routes:**

```
GET  /api/admin/don-vi/{id}/linh-vuc-mac-dinh    # List
POST /api/admin/don-vi/{id}/linh-vuc-mac-dinh    # Set list (replace all)
```

**Request body POST:**
```json
{
  "linh_vucs": [
    {"linh_vuc": "X", "thu_tu": 1},   # Giám sát quản lý - ưu tiên 1
    {"linh_vuc": "XI", "thu_tu": 2},  # Thuế XNK - ưu tiên 2
    {"linh_vuc": "I", "thu_tu": 3}    # Quản lý điều hành - ưu tiên 3
  ]
}
```

Ý nghĩa: Khi CC thuộc đơn vị này mở dropdown chọn lĩnh vực để kê khai, các lĩnh vực được liệt kê ở đây sẽ hiện lên đầu danh sách (theo `thu_tu`). Các lĩnh vực khác vẫn xem được nhưng nằm dưới.

**Logic:**
- DELETE tất cả config cũ của đơn vị này.
- INSERT theo list mới.
- Audit log.

---

### Task C.4 — Endpoint quản lý cờ `kpi_version_pinned`

**File:** Mở rộng `backend/app/api/v1/endpoints/admin.py`.

**Routes:**

```
PUT /api/admin/cong-chuc/{id}/kpi-version    # Set version pin
PUT /api/admin/don-vi/{id}/kpi-version       # Bulk set cho cả đơn vị
```

**Request body:**
```json
{ "kpi_version_pinned": "V2_PL3" }    # hoặc "V1" hoặc null (dùng default)
```

**Logic bulk:** UPDATE all cong_chuc thuộc đơn vị đó. Audit log từng record.

**Use case:** Trên test env, admin pin 1 đơn vị thử V2_PL3 trong tháng 5/2026, các đơn vị khác vẫn V1 → chạy song song.

---

### Task C.5 — Unit tests

**File:** `backend/tests/services/test_kpi_calculator_v2.py`

Test các case:

| Case | Input | Expected |
|---|---|---|
| Normal | `so_luong=5, he_so=8.0, loi=0` | `sp_dat = 40.0` |
| Có lỗi | `so_luong=5, he_so=8.0, loi=3` | `sp_dat = 8.0 × (5 - 0.25×3) = 34.0` |
| Cap lỗi | `so_luong=5, he_so=8.0, loi=25` | loi cap ở 20 → `sp_dat = 0` |
| Hệ số thập phân | `so_luong=5, he_so=6.4, loi=3` | `sp_dat = 6.4 × (5 - 0.75) = 27.2` |
| Số lượng = 1 | `so_luong=1, he_so=20.0, loi=2` | `sp_dat = 20 × (1 - 0.5) = 10.0` |
| Mẫu số = 0 | `tong_sp_ke_khai=0` | `kpi=0, ly_do='MAU_SO_BANG_0'` |
| KPI bình thường | a=0.9, b=0.85, c=0.95, mẫu số đủ | `kpi = (a+b+c)/3` |

---

### Task C.6 — Integration tests

**File:** `backend/tests/integration/test_kekhai_v2_flow.py`

Tests end-to-end:

1. **Happy path:**
   - Tạo CC test, đơn vị test.
   - POST kê khai V2 → 201, có snapshot.
   - GET danh sách → thấy bản kê khai.
   - POST phê duyệt với 0 lỗi → trạng thái = DA_PHE_DUYET.
   - GET tính KPI tháng → đúng số.

2. **Mixed version reject:**
   - Tạo 1 kê khai V1 cho tháng 5/2026.
   - POST kê khai V2 cho cùng tháng → reject với code `MIXED_VERSION_NOT_ALLOWED`.

3. **Override reject:**
   - POST kê khai V2 với body có field `he_so_thuc_te` → reject 400.

4. **Snapshot immutable:**
   - Tạo kê khai V2 với danh mục có `he_so=8.0`.
   - Admin sửa danh mục đó thành `he_so=6.0`.
   - Tính KPI tháng → vẫn dùng `he_so=8.0` (snapshot).

5. **Mẫu số = 0:**
   - Tháng có CC pin V2 nhưng không kê khai gì.
   - Tính KPI → KPI = 0, mức xếp loại = D.

6. **Bulk approve V2:**
   - Tạo 5 kê khai V2 cùng lúc.
   - POST bulk approve → tất cả đều có `sp_dat_chat_luong` và `sp_dat_tien_do` đúng.

---

### Task C.7 — Regression tests V1

**File:** `backend/tests/regression/test_v1_unchanged.py`

**Mục đích:** Đảm bảo Phase A và B KHÔNG phá V1.

Tests:
1. Tạo kê khai V1 (như cũ) → tất cả endpoints V1 hoạt động bình thường.
2. Tính KPI V1 cho 1 CC có sẵn → kết quả số khớp với baseline (lưu baseline trước phase A).
3. Báo cáo Mẫu 01 V1 → output docx khớp baseline.

**Lưu ý:** Lưu baseline file `tests/baselines/v1_kpi_results.json` trước khi chạy migration phase A để có cơ sở so sánh.

---

### Task C.8 — Import Excel test

**File:** `backend/tests/integration/test_import_excel.py`

Tests:
1. Upload file Excel hợp lệ → dry-run trả về summary đúng.
2. Upload file có row sai (sửa 1 cell `diem_cham` lệch) → dry-run liệt kê error.
3. Commit → DB cập nhật đúng.
4. Commit lại file cũ → idempotent (update, không insert mới).
5. File quá lớn (>10MB) → reject 413.

---

## ACCEPTANCE CRITERIA

Phase C coi là DONE khi:

- [ ] Admin có thể CRUD danh mục PL3 qua API (test bằng curl/Postman).
- [ ] Auto-compute hoạt động đúng: nhập 4 điểm thành phần → tự tính `diem_cham`, `he_so_quy_doi`, `khung_diem_toi_da`.
- [ ] Import Excel dry-run trả về preview + errors đầy đủ.
- [ ] Import Excel commit thành công, idempotent.
- [ ] Endpoint config lĩnh vực mặc định cho đơn vị hoạt động.
- [ ] Endpoint set `kpi_version_pinned` cho CC và đơn vị hoạt động.
- [ ] Unit tests: ≥ 95% pass.
- [ ] Integration tests V2: 100% pass.
- [ ] Regression tests V1: 100% pass (KHÔNG được fail bất cứ test V1 nào).
- [ ] Import Excel test: 100% pass.

---

## STOP và báo cáo

Báo cáo cho user:

```
## Phase C Report

### Files created
- ...

### Files modified
- ...

### Test results
| Suite | Total | Passed | Failed | Skipped |
|---|---|---|---|---|
| Unit (kpi_calculator_v2) | | | | |
| Integration (kekhai V2 flow) | | | | |
| Regression V1 | | | | |
| Import Excel | | | | |

### Test failures (if any)
[Chi tiết các test fail]

### Manual smoke
[Test bằng curl: tạo danh mục, dry-run import, commit import]

### Issues encountered
[...]

### Ready for Phase D?
[YES / NO + lý do]
```

KHÔNG động vào frontend.
