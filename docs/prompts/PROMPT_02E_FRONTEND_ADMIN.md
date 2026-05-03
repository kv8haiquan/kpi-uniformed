# PROMPT 02E — FRONTEND ADMIN + TESTS + DOCS

> **Phase:** E — Trang admin redesign cho PL3, import Excel UI, tests frontend, cập nhật tài liệu.
> **Phụ thuộc:** Phase A, B, C, D đã DONE.
> **Output mong đợi:** Admin có giao diện đầy đủ để quản lý PL3 + tài liệu cập nhật + sẵn sàng UAT.

---

## Bối cảnh

4 phase trước đã xong cả backend và frontend user-facing. Phase E hoàn thiện:
1. Trang admin: redesign cho PL3 (4 cột chấm, auto-compute), import Excel UI.
2. Trang admin pin version cho CC/đơn vị (UAT scenario).
3. Frontend tests cho component mới.
4. Cập nhật `BUSINESS_RULES_FINAL.md`, `PROJECT_STATUS.md`, viết hướng dẫn admin.
5. Smoke test toàn bộ luồng end-to-end.

---

## Tài liệu tham chiếu

1. `IMPACT_ANALYSIS_KPI_V2_PL3.md` — §4.4.
2. Phase C đã có backend admin endpoints.
3. `README_BO_PROMPT_02.md`.

---

## NHIỆM VỤ

### Task E.1 — Service admin V2

**File mới:** `frontend/src/services/admin-pl3.service.ts`

```typescript
export const adminPL3Service = {
  // CRUD danh mục PL3
  list: (filter: { linh_vuc?: string; nhom?: number; search?: string; page: number; size: number }) =>
    /* GET /api/admin/danh-muc-pl3 */,
  detail: (id: string) => /* GET /{id} */,
  create: (data: DanhMucPL3CreateRequest) => /* POST */,
  update: (id: string, data: DanhMucPL3UpdateRequest) => /* PUT */,
  deactivate: (id: string) => /* DELETE (soft) */,
  
  // Import Excel
  importDryRun: (file: File) => /* POST /import/dry-run */,
  importCommit: (file: File) => /* POST /import/commit */,
  
  // V1 read-only
  listV1: () => /* GET /api/admin/danh-muc-v1 */,
  deactivateV1: (id: string) => /* PUT /{id}/deactivate */,
  
  // Lĩnh vực mặc định
  getDonViLinhVuc: (donViId: string) => /* GET */,
  setDonViLinhVuc: (donViId: string, items: { linh_vuc: string; thu_tu: number }[]) => /* POST */,
  
  // Pin version
  setCongChucVersion: (id: string, version: 'V1' | 'V2_PL3' | null) => /* PUT */,
  setDonViVersion: (id: string, version: 'V1' | 'V2_PL3' | null) => /* PUT (bulk) */,
};
```

---

### Task E.2 — Trang admin danh mục redesign

**File:** `frontend/src/app/(main)/admin/danh-muc-cv/page.tsx` (sửa file cũ).

**Layout:**

```
┌───────────────────────────────────────────────────────┐
│ Quản lý danh mục công việc                            │
│ [Tab: V2 PL3 ✓] [Tab: V1 Legacy]                      │
├───────────────────────────────────────────────────────┤
│ ── Tab V2 PL3 ──                                      │
│                                                       │
│ [+ Thêm mục] [📥 Import Excel] [📤 Export CSV]        │
│                                                       │
│ Filter:                                               │
│ Lĩnh vực: [Dropdown 15 mục] Nhóm: [Tất cả ▼]          │
│ Tìm kiếm: [Input]                                     │
│                                                       │
│ Bảng list (pagination 50/trang):                      │
│ ┌──┬─────┬─────┬────┬─────┬───┬──────┬─────────┐      │
│ │# │Mã   │Tên  │Lĩnh│Nhóm │Hệ │Trạng │Hành     │      │
│ │  │     │CV   │vực │     │số │thái  │động     │      │
│ ├──┼─────┼─────┼────┼─────┼───┼──────┼─────────┤      │
│ │1 │PL3- │Quyết│I   │4    │8.0│Active│✏️ 🚫    │      │
│ │  │I-2.1│định │    │     │   │      │         │      │
│ └──┴─────┴─────┴────┴─────┴───┴──────┴─────────┘      │
│                                                       │
│ [< 1 2 3 ... 57 >]                                    │
└───────────────────────────────────────────────────────┘
```

**Modal thêm/sửa mục:**

```
┌──────────────────────────────────────────────────┐
│ Thêm mục PL3                                [×]  │
├──────────────────────────────────────────────────┤
│ Tên công việc:    [Input]                        │
│ Lĩnh vực:         [Dropdown 15]                  │
│ Nhiệm vụ:         [Input]                        │
│ Công việc chi tiết: [Textarea]                   │
│ Sản phẩm đầu ra:  [Input]                        │
│ Nhóm:             [○1 ○2 ○3 ○4 ○5]               │
│                                                  │
│ ── 4 cột chấm điểm ──                            │
│ Khó/Sáng tạo:           [____] (max ?)           │
│ Quy trình/Thời gian:    [____]                   │
│ Phối hợp:               [____]                   │
│ Phạm vi áp dụng:        [____]                   │
│                                                  │
│ ── Tự tính ──                                    │
│ Điểm chấm: 170 (= tổng 4 cột)                    │
│ Hệ số quy đổi: 6.8 (= 170/25)                    │
│ Khung điểm tối đa: 200 (theo Nhóm 2)             │
│                                                  │
│ Validate: ✓ Điểm chấm trong khung Nhóm 2         │
│                                                  │
│            [Huỷ]              [Lưu]              │
└──────────────────────────────────────────────────┘
```

**Auto-compute UX:**
- Khi user gõ vào 4 cột chấm → JS tự cộng → hiện `diem_cham`.
- Khi `diem_cham` thay đổi → tự tính `he_so_quy_doi = diem_cham / 25`.
- Khi user đổi `nhom_pl3` → tự đổi `khung_diem_toi_da` (1→100, 2→200, ...).
- Validate realtime: nếu `diem_cham > khung_diem_toi_da` → highlight đỏ + message.

---

### Task E.3 — Modal Import Excel

**File mới:** `frontend/src/components/admin/ImportPL3Modal.tsx`

**Flow 3 bước:**

```
Step 1: Upload
┌──────────────────────────────────────────┐
│ Bước 1/3: Upload file Excel              │
│                                          │
│ [Drop file here hoặc Click để chọn]      │
│ (.xlsx, max 10MB)                        │
│                                          │
│ File đã chọn: PL3_2026.xlsx (2.5 MB)     │
│                                          │
│            [Huỷ]    [Tiếp →]             │
└──────────────────────────────────────────┘

Step 2: Dry-run preview
┌──────────────────────────────────────────┐
│ Bước 2/3: Xem trước                      │
│                                          │
│ Tổng số dòng:     2.812                  │
│ Hợp lệ:           2.810                  │
│ Lỗi:              2 ⚠️                   │
│ Sẽ insert:        0                      │
│ Sẽ update:        2.810                  │
│                                          │
│ ── Lỗi (2) ──                            │
│ Row 145 PL3-I-2.5: diem_cham != tổng     │
│ Row 892 PL3-V-3.2: he_so_quy_doi sai     │
│                                          │
│ ⚠ Toàn bộ import sẽ bị huỷ nếu commit    │
│   trong khi còn lỗi.                     │
│                                          │
│ ── Preview 10 dòng đầu ──                │
│ [Bảng]                                   │
│                                          │
│      [← Lùi]    [Huỷ]    [Commit →]      │
└──────────────────────────────────────────┘

Step 3: Result
┌──────────────────────────────────────────┐
│ Bước 3/3: Hoàn tất                       │
│                                          │
│ ✅ Import thành công                     │
│ - Đã insert: 0                           │
│ - Đã update: 2.810                       │
│ - Lỗi: 0                                 │
│                                          │
│ Thời gian: 12.5 giây                     │
│                                          │
│            [Đóng]                        │
└──────────────────────────────────────────┘
```

**Disabled "Commit" button** nếu dry-run còn errors. User phải sửa file Excel rồi upload lại.

---

### Task E.4 — Trang admin pin version

**File mới:** `frontend/src/app/(main)/admin/kpi-version/page.tsx`

```
┌───────────────────────────────────────────────────────┐
│ Cấu hình phiên bản KPI                                │
│                                                       │
│ ── Cấu hình mặc định hệ thống ──                      │
│ Phiên bản default cho user mới: [V1 ▼]                │
│ [Lưu]                                                 │
│                                                       │
│ ── Pin theo đơn vị ──                                 │
│ Đơn vị: [Dropdown]                                    │
│ Phiên bản: [○ V1] [○ V2_PL3] [○ Default]              │
│ [Áp dụng cho tất cả CC trong đơn vị]                  │
│                                                       │
│ ── Pin theo cá nhân ──                                │
│ [Search CC]                                           │
│ Bảng list CC + version pinned + nút sửa.              │
└───────────────────────────────────────────────────────┘
```

Mục đích: Admin chọn 1-2 đơn vị thử V2_PL3 trong tháng UAT, các đơn vị khác giữ V1.

---

### Task E.5 — Trang admin lĩnh vực mặc định

**File mới:** `frontend/src/app/(main)/admin/don-vi-linh-vuc/page.tsx`

```
┌───────────────────────────────────────────────────────┐
│ Lĩnh vực mặc định cho từng đơn vị                     │
│                                                       │
│ Đơn vị: [Dropdown Hải quan cửa khẩu Móng Cái ▼]       │
│                                                       │
│ ── Lĩnh vực ưu tiên (gợi ý đầu dropdown khi CC kê) ──│
│ Drag để sắp xếp:                                      │
│ ┌──┬─────────────────────────────────────────────┐    │
│ │# │ Lĩnh vực                                    │    │
│ ├──┼─────────────────────────────────────────────┤    │
│ │1 │ X. Giám sát quản lý                  [×]   │    │
│ │2 │ XI. Thuế XNK                         [×]   │    │
│ │3 │ I. Quản lý điều hành                 [×]   │    │
│ └──┴─────────────────────────────────────────────┘    │
│                                                       │
│ [+ Thêm lĩnh vực gợi ý]                               │
│                                                       │
│            [Huỷ]              [Lưu]                   │
└───────────────────────────────────────────────────────┘
```

Dùng react-beautiful-dnd hoặc dnd-kit cho drag-and-drop.

---

### Task E.6 — Trang admin V1 cấp độ deprecated

**File:** Sửa `frontend/src/app/(main)/admin/cap-do/page.tsx`.

Thêm banner trên cùng:
```
⚠ Trang này thuộc hệ thống V1. Sau cutover V2_PL3, các bản ghi
mới sẽ không dùng cấp độ. Trang giữ ở chế độ READ-ONLY để xem
lại cấu hình lịch sử.
```

Disable tất cả nút thao tác (chỉ giữ View/Search).

Áp dụng tương tự cho `admin/sp-chuan/page.tsx`.

---

### Task E.7 — Frontend tests

**Tests cho:**

1. **Component test** (Vitest + React Testing Library):
   - `LinhVucNhomFilter`: render dropdown, callback onChange đúng.
   - `DanhMucSearchCombobox`: debounce search, render kết quả, empty state.
   - `KpiTargetModalV2`: validate so_luong > 0, submit gọi API đúng.
   - `ImportPL3Modal`: 3 bước flow, disabled commit khi có errors.

2. **Snapshot test:**
   - Modal V2 (target + multi-day) — snapshot UI.
   - Banner Tổng SP — snapshot.

3. **Integration test (Playwright nếu có sẵn, không bắt buộc nếu không có infra):**
   - User pin V2 → login → tạo kê khai → submit → thấy trong list.

---

### Task E.8 — Cập nhật tài liệu

**File:** `BUSINESS_RULES_FINAL.md` (TẠO BẢN MỚI: `BUSINESS_RULES_v3_0_PL3.md`, KHÔNG sửa file cũ).

Thêm mục:
```markdown
## 15. PHIÊN BẢN V2_PL3 (từ tháng X/2026)

### 15.1 Thay đổi công thức
Mẫu số KPI = Tổng SP công chức kê khai (đã duyệt) trong tháng,
thay cho công thức cũ `(ngày làm việc - nghỉ phép) × 96`.

### 15.2 Danh mục mới
2.812 mục PL3 chia 15 lĩnh vực và 5 nhóm. Hệ số quy đổi tính sẵn
theo công thức diem_cham / 25.

### 15.3 Cấu trúc song song
Hệ thống chạy song song V1 và V2_PL3. Mỗi công chức được pin
một version trong tháng. 1 tháng = 1 version, không cho mix.

[... chi tiết từng quy tắc đã chốt ở 19 LOCKED DECISIONS ...]
```

**File:** `PROJECT_STATUS_v2_0_PL3.md` (TẠO MỚI).

```markdown
# Project Status v2.0 PL3

## Phase hoàn thành
- [x] Phase A — Database & Migration
- [x] Phase B — Backend KPI Logic
- [x] Phase C — Backend Admin + Tests
- [x] Phase D — Frontend KPI Flow
- [x] Phase E — Frontend Admin + Docs

## Trạng thái UAT
- Test env: deploying...
- Đơn vị thử nghiệm: [TBD]
- Tháng thử nghiệm: [TBD]
```

**File mới:** `docs/HUONG_DAN_ADMIN_PL3.md`

```markdown
# Hướng dẫn Admin — Quản lý KPI V2_PL3

## 1. Cập nhật danh mục PL3 từ Excel
[Step-by-step có screenshot]

## 2. Pin đơn vị/CC sang V2_PL3
[Step-by-step]

## 3. Cấu hình lĩnh vực mặc định cho đơn vị
[Step-by-step]

## 4. Xử lý lỗi thường gặp
- Mixed version: [...]
- Import Excel báo lỗi diem_cham: [...]
- Mẫu số = 0: [...]
```

---

### Task E.9 — Smoke test end-to-end

Chạy thủ công trên test env (có thể automate sau):

**Scenario 1: Setup**
1. Admin login → trang `/admin/danh-muc-cv` → tab V2 → có 2.812 mục.
2. Admin trang `/admin/don-vi-linh-vuc` → set "HQCK Móng Cái" có lĩnh vực mặc định X, XI, XII.
3. Admin trang `/admin/kpi-version` → pin tất cả CC của HQCK Móng Cái sang V2_PL3.

**Scenario 2: CC kê khai**
4. Login với CC thuộc HQCK Móng Cái.
5. Sidebar hiện "Kê khai (V2)" → click → vào `/ke-khai-v2`.
6. Click "Thêm kê khai" → modal V2 mở.
7. Dropdown lĩnh vực → 3 mục X, XI, XII hiện ở section "Gợi ý cho đơn vị bạn".
8. Chọn lĩnh vực X, nhóm 4, search "kiểm tra" → kết quả hiện.
9. Chọn 1 mục, so_luong=10 → "Tổng SP quy đổi" tự tính.
10. Submit → bản kê khai vào trạng thái CHO_PHE_DUYET.

**Scenario 3: Lãnh đạo phê duyệt**
11. Login lãnh đạo → trang `/phe-duyet` → thấy bản của CC.
12. Phê duyệt với 0 lỗi → trạng thái DA_PHE_DUYET.

**Scenario 4: Tính KPI**
13. CC vào `/danh-gia` → KPI tháng tự tính.
14. Mẫu số = 10 × hệ số (ví dụ 8.0) = 80 SP.
15. Tử số = 80 (vì hoàn thành đúng tiến độ + chất lượng).
16. KPI = 100% → mức A (nếu tiêu chí chung đạt).

**Scenario 5: Regression V1**
17. Login CC khác (không pin V2) → vào `/ke-khai` (V1) → modal cũ → kê khai như cũ → mọi thứ hoạt động.

---

## ACCEPTANCE CRITERIA

Phase E coi là DONE khi:

- [ ] Admin trang danh mục có tab V2 và V1, switch đúng.
- [ ] Modal thêm/sửa mục PL3 auto-compute `diem_cham`, `he_so`, `khung` đúng.
- [ ] Import Excel 3 bước hoạt động: dry-run → preview → commit.
- [ ] Trang pin version hoạt động cho cả CC và đơn vị (bulk).
- [ ] Trang lĩnh vực mặc định hoạt động với drag-drop.
- [ ] Tất cả 5 scenarios smoke test pass.
- [ ] V1 admin cấp độ + SP chuẩn hiện banner deprecated, read-only.
- [ ] Tài liệu mới đầy đủ: `BUSINESS_RULES_v3_0_PL3.md`, `PROJECT_STATUS_v2_0_PL3.md`, `docs/HUONG_DAN_ADMIN_PL3.md`.
- [ ] Frontend tests pass: ≥ 90%.

---

## STOP và báo cáo

Báo cáo cuối cùng:

```
## Phase E Report — FINAL

### Files created
[full list]

### Files modified
[full list with line ranges]

### Test results
| Suite | Total | Passed | Failed |
|---|---|---|---|
| Backend unit | | | |
| Backend integration | | | |
| Backend regression V1 | | | |
| Frontend component | | | |
| Frontend snapshot | | | |
| End-to-end smoke | 5 scenarios | | |

### Documentation
- [ ] BUSINESS_RULES_v3_0_PL3.md
- [ ] PROJECT_STATUS_v2_0_PL3.md
- [ ] docs/HUONG_DAN_ADMIN_PL3.md

### V2_PL3 Production Readiness
- [ ] Tất cả 5 phase DONE
- [ ] Toàn bộ regression V1 pass
- [ ] Smoke test end-to-end pass
- [ ] Documentation đầy đủ
- [ ] Sẵn sàng UAT trên test env

### Next steps
- UAT 1-2 tuần với 1-2 đơn vị thử nghiệm.
- Thu feedback, fix bugs.
- Quyết định cutover production date.

### Issues / Outstanding
[...]
```

Sau Phase E, hệ thống V2_PL3 SẴN SÀNG UAT.
