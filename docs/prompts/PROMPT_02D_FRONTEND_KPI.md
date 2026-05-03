# PROMPT 02D — FRONTEND KPI FLOW (KÊ KHAI + XẾP LOẠI)

> **Phase:** D — Frontend các trang user-facing cho V2_PL3.
> **Phụ thuộc:** Phase B đã DONE (backend API V2 đã có).
> **Output mong đợi:** CC pin V2 truy cập `/ke-khai-v2` thấy modal mới với search 2.812 mục; xem điểm xếp loại tháng V2 đúng số.

---

## Bối cảnh

Backend V2 đã sẵn sàng. Phase D xây giao diện user-facing:
1. Modal kê khai V2 với search hierarchy 3-layer (lĩnh vực → nhóm → keyword).
2. Trang `/ke-khai-v2` song song với `/ke-khai` (V1 giữ nguyên).
3. Banner "Tổng SP đã kê" cho CC nhìn được mẫu số.
4. Render điểm xếp loại theo `version_tinh_diem`.

**Nguyên tắc:**
- Code V1 cũ KHÔNG sửa nội dung. Chỉ thêm logic redirect dựa vào `kpi_version_pinned`.
- Component V2 đặt riêng với hậu tố `V2`.
- Reuse component chung được (button, table, layout) để giảm duplicate.

---

## Tài liệu tham chiếu

1. `IMPACT_ANALYSIS_KPI_V2_PL3.md` — §4.
2. `FRONTEND_FULL_20260214_2339.md` — cấu trúc frontend hiện tại.
3. `README_BO_PROMPT_02.md` — 19 LOCKED DECISIONS.

---

## LOCKED DECISIONS — phase này dùng

Quyết định liên quan: **5, 12, 14, 15, 17, 19, 20**.

**Tóm tắt:**
- **(15)** Filter lĩnh vực mềm — đơn vị có lĩnh vực mặc định nổi lên đầu, nhưng hiển thị TẤT CẢ.
- **(14)** Modal V2 KHÔNG có field "hệ số thực tế" (override).
- **(17)** Số lượng > 0, integer.
- **(19)** Route `/ke-khai-v2` riêng, KHÔNG đè `/ke-khai`.
- **(5)** Banner cảnh báo nếu mẫu số quá thấp.

---

## NHIỆM VỤ

### Task D.1 — Service & Types V2

**File mới:** `frontend/src/services/kpi-v2.service.ts`

```typescript
export interface DanhMucPL3 {
  id: string;
  ma_danh_muc: string;
  ten_cong_viec: string;
  linh_vuc: string;       // 'I'..'XV'
  ten_linh_vuc: string;
  nhiem_vu: string;
  cong_viec_chi_tiet: string;
  san_pham_dau_ra: string;
  nhom_pl3: number;       // 1..5
  khung_diem_toi_da: number;
  diem_cham: number;
  he_so_quy_doi: number;
  diem_kho_sang_tao: number;
  diem_quy_trinh_thoi_gian: number;
  diem_phoi_hop: number;
  diem_pham_vi_ap_dung: number;
}

export interface LinhVuc {
  ma: string;             // 'I'..'XV'
  ten: string;
}

export interface KeKhaiV2Request {
  danh_muc_sp_id: string;
  so_luong: number;       // > 0, integer
  thang: number;
  nam: number;
  ngay_thuc_hien?: string;
  mo_ta_cong_viec?: string;
  is_doi_moi_sang_tao?: boolean;
  ngay_deadline?: string;
  ngay_hoan_thanh?: string;
  nguoi_phe_duyet_id: string;
  // KHÔNG có cap_do_id, KHÔNG có he_so_thuc_te
}

export interface ThongKeKeKhaiThang {
  thang: number;
  nam: number;
  version_kekhai: 'V1' | 'V2_PL3';
  tong_sp_da_duyet: number;
  tong_sp_cho_duyet: number;
  tong_sp_du_kien: number;
  so_kekhai_da_duyet: number;
  so_kekhai_cho_duyet: number;
}

// API methods
export const kpiV2Service = {
  getLinhVuc: () => /* GET /api/danh-muc/linh-vuc */,
  getLinhVucMacDinh: (donViId: string) => /* GET /api/don-vi/{id}/linh-vuc-mac-dinh */,
  searchDanhMucPL3: (params: {
    linh_vuc?: string;
    nhom?: number;
    search?: string;
    page?: number;
    size?: number;
  }) => /* GET /api/danh-muc/sp-cong-viec/pl3 */,
  
  createKeKhai: (data: KeKhaiV2Request) => /* POST /api/ke-khai-v2 */,
  updateKeKhai: (id: string, data: Partial<KeKhaiV2Request>) => /* PUT */,
  deleteKeKhai: (id: string) => /* DELETE */,
  getMyKeKhai: (thang: number, nam: number) => /* GET /me */,
  createMultiDay: (data: any) => /* POST /multi-day */,
  getThongKeThang: (thang: number, nam: number) => /* GET /thong-ke/thang */,
};
```

---

### Task D.2 — Component LinhVucNhomFilter

**File mới:** `frontend/src/components/kpi-v2/LinhVucNhomFilter.tsx`

Component filter dùng chung cho modal kê khai và trang admin.

**Layout:**
```
┌────────────────────────────────────────────┐
│ Lĩnh vực: [Dropdown 15 mục, ưu tiên gợi ý] │
│                                            │
│ Nhóm:    [○ Tất cả] [○ 1] [○ 2] [○ 3]     │
│          [○ 4] [○ 5]                       │
│                                            │
│ Tìm kiếm: [Input full-text]                │
└────────────────────────────────────────────┘
```

**Logic dropdown lĩnh vực:**

1. Load `getLinhVucMacDinh(donViId)` → 3-5 lĩnh vực mặc định của đơn vị CC.
2. Load `getLinhVuc()` → 15 lĩnh vực toàn bộ.
3. Render dropdown chia 2 section:
   ```
   ── Lĩnh vực gợi ý cho đơn vị bạn ──
   X. Giám sát quản lý
   XI. Thuế XNK
   I. Quản lý điều hành
   ── Tất cả lĩnh vực ──
   I. Quản lý điều hành...
   II. Hợp tác quốc tế
   ... (15 mục đầy đủ)
   ```

Default selection = lĩnh vực gợi ý đầu tiên của đơn vị (nếu có), hoặc rỗng.

**Props:**
```typescript
interface Props {
  value: { linh_vuc?: string; nhom?: number; search?: string };
  onChange: (value: any) => void;
  donViId: string;
}
```

---

### Task D.3 — Component DanhMucSearchCombobox

**File mới:** `frontend/src/components/kpi-v2/DanhMucSearchCombobox.tsx`

Dùng `cmdk` hoặc Headless UI Combobox. Search server-side, debounce 300ms.

**Behavior:**
- Khi user gõ vào input → debounce → call `searchDanhMucPL3({linh_vuc, nhom, search})`.
- Hiển thị max 50 kết quả, có "Hiển thị thêm" để load thêm.
- Mỗi kết quả hiển thị:
  ```
  ┌─────────────────────────────────────────────┐
  │ Quyết định                       [Nhóm 4]   │
  │ Phối hợp với nhiều đơn vị, có sự...          │
  │ Sản phẩm: Quyết định                        │
  │ Hệ số quy đổi: 8.0                          │
  └─────────────────────────────────────────────┘
  ```

**Empty state:**
- Không kết quả → "Không tìm thấy. Thử mở rộng tìm kiếm bằng cách bỏ filter Nhóm hoặc đổi từ khoá."

**Selection:** Click → return full DanhMucPL3 object cho parent.

---

### Task D.4 — Modal kê khai V2 (KpiTargetModalV2)

**File mới:** `frontend/src/components/kpi-v2/KpiTargetModalV2.tsx`

Tham chiếu (KHÔNG sửa) `KpiTargetModal.tsx` (V1, 635 dòng).

**Layout:**

```
┌──────────────────────────────────────────────────┐
│ Kê khai công việc V2_PL3                    [×]  │
├──────────────────────────────────────────────────┤
│ Tháng: [4] Năm: [2026]                           │
│                                                  │
│ ── Chọn công việc ──                             │
│ [LinhVucNhomFilter component]                    │
│ [DanhMucSearchCombobox component]                │
│                                                  │
│ ── Đã chọn ──                                    │
│ ┌────────────────────────────────────────────┐   │
│ │ Quyết định                                 │   │
│ │ Lĩnh vực I, Nhóm 4, Hệ số 8.0              │   │
│ │ Sản phẩm: Quyết định                       │   │
│ └────────────────────────────────────────────┘   │
│                                                  │
│ Số lượng: [5] (số nguyên > 0)                    │
│ Ngày thực hiện: [date picker, optional]          │
│ Mô tả: [textarea]                                │
│ ☐ Đổi mới sáng tạo                               │
│ Người phê duyệt: [dropdown lãnh đạo trực tiếp]   │
│                                                  │
│ ── Tự tính ──                                    │
│ Tổng SP quy đổi: 5 × 8.0 = 40.0 SP1              │
│                                                  │
│            [Huỷ]  [Lưu nháp]  [Gửi duyệt]        │
└──────────────────────────────────────────────────┘
```

**Logic submit:**
- "Lưu nháp" → POST `/api/ke-khai-v2` với trạng thái `NHAP`.
- "Gửi duyệt" → POST với trạng thái `CHO_PHE_DUYET`.
- Snapshot fields được backend tự lấy từ `danh_muc_sp_id` — frontend KHÔNG cần gửi.

**Validation client-side:**
- `so_luong` phải là integer > 0.
- `danh_muc_sp_id` phải được chọn.
- `nguoi_phe_duyet_id` phải có.

**Error handling:**
- Backend trả `MIXED_VERSION_NOT_ALLOWED` → hiện banner "Tháng này đã có kê khai V1. Liên hệ TCCB nếu muốn chuyển sang V2."
- Backend trả `INVALID_CATALOG_VERSION` → hiện "Mục đã chọn không hợp lệ với phiên bản kê khai. Vui lòng chọn lại."

---

### Task D.5 — Modal kê khai nhiều ngày V2 (KpiMultiDayModalV2)

**File mới:** `frontend/src/components/kpi-v2/KpiMultiDayModalV2.tsx`

Tham chiếu V1 `KpiMultiDayModal.tsx` (590 dòng) cho UX tương đương. Khác biệt V1:
- Không chọn cấp độ.
- Search trong 2.812 mục PL3.
- Hệ số tự fill từ danh mục.

---

### Task D.6 — Trang /ke-khai-v2

**File mới:** `frontend/src/app/(main)/ke-khai-v2/page.tsx`

Tham chiếu V1 `app/(main)/ke-khai/page.tsx` (clone layout, đổi modal V1 → V2).

**Layout chính:**

```
┌──────────────────────────────────────────────────┐
│ Kê khai công việc — V2_PL3                       │
│ Tháng: [4 ▼] Năm: [2026 ▼]                       │
│                                                  │
│ ┌─ Banner Tổng SP ────────────────────────────┐ │
│ │ Tổng SP đã kê tháng 04/2026: 285.6 SP       │ │
│ │  • Đã duyệt:    240.0 SP (mẫu số chính thức)│ │
│ │  • Chờ duyệt:    45.6 SP                    │ │
│ │  ⚠ KPI tính trên mẫu số "Đã duyệt"          │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ [+ Thêm kê khai] [+ Kê khai nhiều ngày]          │
│                                                  │
│ Bảng list kê khai:                               │
│ ┌────┬──────┬──────┬──────┬──────┬─────────┐    │
│ │ STT│ CV   │ Lĩnh │ Nhóm │ Hệ   │ Trạng   │    │
│ │    │      │ vực  │      │ số   │ thái    │    │
│ ├────┼──────┼──────┼──────┼──────┼─────────┤    │
│ │ 1  │ ...  │ I    │ 4    │ 8.0  │ Duyệt   │    │
│ └────┴──────┴──────┴──────┴──────┴─────────┘    │
└──────────────────────────────────────────────────┘
```

**Logic mở trang:**
1. Check `cong_chuc.kpi_version_pinned`. Nếu == 'V1' → redirect `/ke-khai`. Nếu 'V2_PL3' hoặc null (default V2 trên test env) → render trang này.
2. Load `getThongKeThang()` → render banner.
3. Load `getMyKeKhai(thang, nam)` → render bảng.

---

### Task D.7 — Routing & sidebar

**File:** `frontend/src/app/(main)/layout.tsx` hoặc component sidebar.

**Logic menu sidebar:**

```typescript
const userVersion = useUserKpiVersion(); // hook đọc cong_chuc.kpi_version_pinned

const menuItems = [
  userVersion === 'V2_PL3' 
    ? { label: 'Kê khai (V2)', href: '/ke-khai-v2' }
    : { label: 'Kê khai', href: '/ke-khai' },
  // ... các item khác
];
```

**KHÔNG xoá** route `/ke-khai` — giữ cho V1. Test env có thể truy cập cả 2 route nếu admin, để đối chiếu.

---

### Task D.8 — Render trang đánh giá theo version

**File:** Sửa `frontend/src/app/(main)/danh-gia/page.tsx` (V1 hiện tại có 8 chỗ hardcode `* 96`).

**Logic:**
1. Khi load đánh giá tháng → đọc `version_tinh_diem` từ response.
2. Nếu `'V2_PL3'`:
   - Cột "Số ngày làm việc" → hiển thị nhưng note "(không quyết định mẫu số)".
   - Cột "Tổng SP được giao" → đổi thành "Tổng SP kê khai" = `tong_sp_ke_khai`.
   - Bỏ hiển thị `× 96`.
3. Nếu `'V1'`: giữ nguyên.

**Áp dụng cho:**
- `app/(main)/danh-gia/page.tsx`
- `components/xep-loai/tabs/TabTamTinh.tsx`
- `components/xep-loai/tabs/TabBaoCao.tsx`
- `components/xep-loai/tabs/TabCongViec.tsx`

**Cách làm:** Tạo helper component `<MauSoDisplay version={...} ... />` để dùng chung 4 chỗ.

---

### Task D.9 — Cảnh báo mẫu số bất thường

Trong banner Tổng SP (Task D.6) và Tab tạm tính:

- Nếu `tong_sp_da_duyet < 800` SP → banner màu vàng "⚠ Tổng SP kê khai thấp hơn ngưỡng 800 SP. Kết quả KPI có thể không phản ánh đúng khối lượng công việc."
- Nếu `tong_sp_da_duyet == 0` ở giữa tháng → banner đỏ "🚨 Bạn chưa có bản kê khai nào được duyệt. Nếu không kê khai trong tháng, KPI sẽ tự xếp mức D."

(Ngưỡng 800 = ~80% × 22 ngày × 96 / 2 — tính tham chiếu, có thể config sau).

---

## ACCEPTANCE CRITERIA

Phase D coi là DONE khi:

- [ ] CC pin V2 đăng nhập, sidebar redirect sang `/ke-khai-v2` đúng.
- [ ] Modal V2 search được trong 2.812 mục, filter theo lĩnh vực + nhóm hoạt động.
- [ ] Lĩnh vực mặc định của đơn vị nổi lên đầu dropdown.
- [ ] Nhập số lượng + chọn danh mục → "Tổng SP quy đổi" tự tính đúng (`so_luong × he_so`).
- [ ] Submit kê khai V2 thành công, hiện trong bảng list.
- [ ] Modal V2 KHÔNG có field "hệ số thực tế" hay tương tự.
- [ ] Modal V2 KHÔNG có dropdown cấp độ C1-C5.
- [ ] Banner Tổng SP hiện đúng số `tong_sp_da_duyet` từ API.
- [ ] Trang `/danh-gia` hiển thị mẫu số = `tong_sp_ke_khai` cho CC version V2_PL3.
- [ ] CC pin V1 đăng nhập, vào `/ke-khai` (V1) — hoạt động bình thường, KHÔNG bị thay đổi.
- [ ] Modal V2 multi-day kê khai được nhiều ngày liền.

---

## STOP và báo cáo

Báo cáo:

```
## Phase D Report

### Files created
- frontend/src/services/kpi-v2.service.ts
- frontend/src/components/kpi-v2/LinhVucNhomFilter.tsx
- frontend/src/components/kpi-v2/DanhMucSearchCombobox.tsx
- frontend/src/components/kpi-v2/KpiTargetModalV2.tsx
- frontend/src/components/kpi-v2/KpiMultiDayModalV2.tsx
- frontend/src/app/(main)/ke-khai-v2/page.tsx
- frontend/src/components/common/MauSoDisplay.tsx
- ... (list)

### Files modified
- frontend/src/app/(main)/layout.tsx (sidebar logic)
- frontend/src/app/(main)/danh-gia/page.tsx (line ranges)
- frontend/src/components/xep-loai/tabs/TabTamTinh.tsx (line ranges)
- frontend/src/components/xep-loai/tabs/TabBaoCao.tsx (line ranges)
- frontend/src/components/xep-loai/tabs/TabCongViec.tsx (line ranges)

### Manual smoke test (screenshots / step-by-step)
1. Pin user test sang V2_PL3
2. Login với user test → sidebar hiện "Kê khai (V2)"
3. Click → vào /ke-khai-v2
4. Mở modal kê khai → filter "Lĩnh vực: I", "Nhóm: 4", search "Quyết định" → kết quả hiện
5. Chọn 1 mục, nhập so_luong=5 → "Tổng SP quy đổi: 40.0" tự tính
6. Submit → kê khai xuất hiện trong bảng
7. Banner Tổng SP cập nhật: chờ duyệt 40.0

### V1 regression
- Login user pin V1 → /ke-khai → modal cũ hoạt động không lỗi.

### Issues
[...]

### Ready for Phase E?
[YES / NO]
```

KHÔNG động vào trang admin (Phase E).
