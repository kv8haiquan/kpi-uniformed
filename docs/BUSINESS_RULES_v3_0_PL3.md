# BUSINESS RULES v3.0 — PL3 V2 Extension

> **Ngày tạo:** 2026-04-29
> **Phạm vi:** Bổ sung rules cho phiên bản V2_PL3, không thay thế `BUSINESS_RULES_FINAL.md` cũ (V1).
> **Trạng thái:** Phase A-E của V2_PL3 đã hoàn thiện, sẵn sàng UAT.

---

## 1. Bối cảnh

Hệ thống KPI Hải quan KV8 đang vận hành phiên bản V1 (mẫu số = ngày × 96 SP/ngày). Theo chỉ đạo mới (Phụ lục III Sổ tay hướng dẫn của Bộ Nội vụ), nghiệp vụ chuyển sang công thức:

```
Mẫu số V2 = Tổng SP công chức kê khai (đã được lãnh đạo phê duyệt)
```

Với 2.812 mục công việc PL3 chia thành 15 lĩnh vực × 5 nhóm. Mỗi mục có hệ số quy đổi cố định = `điểm chấm / 25`.

---

## 2. 19+1 Quyết định LOCKED đã chốt

Tham chiếu đầy đủ trong `docs/prompts/README_BO_PROMPT_02.md`. Trích các điểm cốt lõi:

| ID | Quyết định |
|---|---|
| 1 | Mẫu số V2 = SUM(`so_sp_goc_quy_doi`) bản kê khai DA_PHE_DUYET trong tháng |
| 2 | Hệ số V2 đọc thẳng từ `danh_muc_sp_cong_viec.he_so_quy_doi` (không nhân `cap_do`) |
| 3 | Công thức trừ điểm CL/TĐ tuyến tính `(SL − 0.25 × min(lỗi, SL × 4))` GIỮ NGUYÊN từ V1 |
| 4 | KPI lãnh đạo (a, b, c, d, đ, e) GIỮ NGUYÊN — V2 chỉ áp cho công chức |
| 5 | CC kê khai 0 SP → mẫu số = 0 → KPI = 0 → tự xếp **mức D** |
| 6 | Bảng `cap_do_phuc_tap` GIỮ + soft deactivate (data lịch sử) |
| 7 | MỞ RỘNG bảng `danh_muc_sp_cong_viec`, KHÔNG tạo bảng mới (cờ `nguon_du_lieu`) |
| 8 | Cột `cap_do_id` trên `ke_khai_cong_viec` thành **nullable** |
| 9 | Tiêu chí chung KHÔNG đổi |
| 10 | `version_kekhai` IN ('V1', 'V2_PL3'), default 'V1', NOT NULL |
| 11 | `version_tinh_diem` IN ('V1', 'V2_PL3'), default 'V1', NOT NULL |
| 12 | **1 tháng = 1 version** — không cho mix V1 + V2 trong cùng (CC, tháng, năm) |
| 13 | `he_so_quy_doi_snapshot` lưu lúc tạo kê khai → **immutable** |
| 14 | KHÔNG cho lãnh đạo override `he_so_quy_doi` trong V2 |
| 15 | Filter lĩnh vực **mềm** (gợi ý nổi lên đầu nhưng vẫn hiện 15 lĩnh vực) |
| 16 | `khung_diem_toi_da` chỉ tham khảo, KHÔNG ràng buộc trần lúc kê khai |
| 17 | `so_luong` > 0, **số nguyên** |
| 18 | Test environment trước, không cần backfill production data |
| 19 | Route song song: `/ke-khai` (V1) + `/ke-khai-v2` (V2). Cờ `cong_chuc.kpi_version_pinned` |
| 20 | Số ngày làm việc / nghỉ phép vẫn track. Mức **E = nghỉ thai sản** (không xếp loại) |

---

## 3. Công thức tính KPI

### 3.1 V1 (giữ nguyên)

```
mẫu_số = (Tổng ngày trong tháng − ngày nghỉ) × 96
a = SUM(so_sp_goc_quy_doi đã duyệt) / mẫu_số           # số lượng
b = SUM(so_sp_chat_luong)         / mẫu_số             # chất lượng
c = SUM(so_sp_tien_do)            / mẫu_số             # tiến độ
KPI = (a + b + c) / 3 × 70
Điểm tổng = Tiêu chí chung (max 30) + KPI (max 70)
```

### 3.2 V2_PL3 (mới)

```
mẫu_số = SUM(so_sp_goc_quy_doi đã DA_PHE_DUYET trong tháng)
a = SUM(so_sp_goc_quy_doi)  / mẫu_số  # = 1.0 nếu mọi bản đã duyệt = đã hoàn thành
b = SUM(so_sp_chat_luong)   / mẫu_số  # đã trừ lỗi CL khi phê duyệt
c = SUM(so_sp_tien_do)      / mẫu_số  # đã trừ lỗi TĐ khi phê duyệt
KPI = (a + b + c) / 3 × 70

# Edge case (LOCKED 5):
nếu mẫu_số == 0:
    KPI = 0, ly_do = "MAU_SO_BANG_0", xếp mức D (hoặc E nếu nghỉ thai sản)
```

### 3.3 Quy đổi SP gốc

V1:
```
so_sp_goc_quy_doi = so_luong × sp_chuan.he_so_quy_doi_sp1 × cap_do.he_so_sp1
```

V2:
```
so_sp_goc_quy_doi = so_luong × danh_muc.he_so_quy_doi
                  = so_luong × (diem_cham / 25)
```

### 3.4 Trừ điểm chất lượng/tiến độ (GIỮ NGUYÊN cả V1 + V2)

```
sp_per_unit = so_sp_goc_quy_doi / so_luong  # = he_so_quy_doi
max_loi     = so_luong × 4  # mỗi đơn vị tối đa 4 lỗi (= -100%)
loi_tinh    = min(so_lan_loi, max_loi)
sp_tru      = 0.25 × loi_tinh × sp_per_unit
sp_dat      = max(so_sp_goc_quy_doi − sp_tru, 0)
```

Hoạt động đúng với hệ số thập phân (vd `he_so_quy_doi=6.4`).

---

## 4. Cấu trúc danh mục PL3

### 4.1 Tổng quan
- 2.812 mục đã seed từ file `Danh mục công việc.xlsx` sheet `PL3`.
- 15 lĩnh vực La Mã I-XV (vd: I. Quản lý điều hành, X. Giám sát quản lý...).
- 5 nhóm 1-5 với khung điểm tối đa 100/200/300/400/500.
- 18 cặp duplicate `stt` được rename suffix `-r{row}` để giữ unique.

### 4.2 Schema bảng `danh_muc_sp_cong_viec` mở rộng

Cột mới (Phase A.1 + A.7b drop 4 cột chấm chi tiết):
- `nguon_du_lieu` VARCHAR(20): `'V1'` (46 mục cũ) hoặc `'PL3'` (2.812 mục mới)
- `linh_vuc` VARCHAR(10): I-XV (V2 only)
- `ten_linh_vuc` VARCHAR(200)
- `nhiem_vu`, `cong_viec_chi_tiet`, `san_pham_dau_ra`
- `nhom_pl3` SMALLINT 1-5
- `khung_diem_toi_da` SMALLINT (auto từ nhóm)
- `diem_cham` SMALLINT 1-500
- `he_so_quy_doi` NUMERIC(8,4)

### 4.3 Bảng `nhom_cong_viec_pl3` (mới)

5 row seed cứng:
| nhom | ten_nhom | diem_toi_da |
|---|---|---|
| 1 | Nhóm 1 - Đơn giản | 100 |
| 2 | Nhóm 2 - Thông thường | 200 |
| 3 | Nhóm 3 - Nâng cao | 300 |
| 4 | Nhóm 4 - Phức tạp | 400 |
| 5 | Nhóm 5 - Đặc thù | 500 |

---

## 5. Pin version

### 5.1 Logic resolve (`app/core/kpi_version.py`)

Thứ tự ưu tiên khi xác định version:
1. `danh_gia_thang.version_tinh_diem` (nếu đã tạo row đánh giá tháng).
2. `version_kekhai` của bản kê khai đầu tiên trong tháng (nếu CC đã kê).
3. `cong_chuc.kpi_version_pinned` (admin pin riêng cho CC).
4. `platform_config('kpi_version_default')` — mặc định seed `'V2_PL3'` ở test env.

### 5.2 Cutover production

Khi cần đổi default toàn cụ:
```sql
UPDATE platform_config
SET value = '"V2_PL3"'::jsonb
WHERE key = 'kpi_version_default';
```

Rollback: đổi lại thành `'"V1"'::jsonb`.

### 5.3 Pin riêng (admin UI)

Trang `/admin/kpi-version`:
- Pin theo CC: chọn CC → set V1/V2_PL3/Default.
- Pin theo đơn vị (bulk): chọn đơn vị → áp dụng cho tất cả CC trong đơn vị.

---

## 6. Mức xếp loại (mở rộng)

| Mức | Tiêu chí | Ghi chú |
|---|---|---|
| A | Điểm tổng ≥ 90 | Hoàn thành xuất sắc |
| B | 70-89 | Hoàn thành tốt |
| C | 50-69 | Hoàn thành |
| D | < 50 hoặc CC kê 0 SP làm việc bình thường | Không hoàn thành |
| **E** | **CC nghỉ thai sản** | **Không xếp loại** — thêm 28/04/2026 (LOCKED 20) |

Enum `muc_xep_loai_enum` đã thêm value `'E'` (migration `pl3_v2_007`).

---

## 7. Validation guardrails

### 7.1 Backend
- Endpoint `POST /ke-khai-v2` reject:
  - `MIXED_VERSION_NOT_ALLOWED` nếu tháng đã có kê khai V1.
  - `INVALID_CATALOG_VERSION` nếu mục có `nguon_du_lieu='V1'`.
  - `MISSING_HE_SO` nếu mục PL3 thiếu `he_so_quy_doi`.
- Endpoint `POST /phe-duyet/{id}` reject `V2_NO_OVERRIDE` nếu LĐ gửi `cap_do_ma` cho bản V2.
- Schema V2 dùng Pydantic `extra='forbid'` → reject mọi field lạ (vd `he_so_thuc_te`, `cap_do_id`).

### 7.2 Frontend
- Modal V2 KHÔNG có dropdown C1-C5, KHÔNG có input "hệ số thực tế".
- `so_luong` validate `> 0`, integer (Zod preprocess).
- Auto-compute `Tổng SP quy đổi = so_luong × he_so_quy_doi` realtime.

---

## 8. Outstanding (chưa làm)

Các phần đã defer khỏi Phase A-E:
- **Bảng `don_vi_linh_vuc_mac_dinh`**: Lĩnh vực mặc định cho từng đơn vị (UI gợi ý dropdown). Defer đến sau UAT khi nghiệp vụ chốt mapping 15 đơn vị → lĩnh vực.
- **Báo cáo quý cross-version**: Khi quý trộn V1+V2 — chưa có rule. Bỏ qua trong Phase này.
- **UI default hệ thống**: Cutover qua SQL (`UPDATE platform_config`) thay vì UI.
- **Frontend tests automated**: Chưa có infra Vitest/Playwright. Smoke test thủ công.
- **Replace label "ngày × 96"** chi tiết ở trang `/danh-gia` và 3 tabs xếp loại: chỉ thêm banner V2 cảnh báo, không sửa toàn bộ label client-side.

---

## 9. Tham chiếu code

| Module | File | Phase |
|---|---|---|
| Helper tính KPI V2 | `backend/app/core/kpi_calculator_v2.py` | B |
| Resolve version | `backend/app/core/kpi_version.py` | B |
| Parser Excel PL3 | `backend/app/core/pl3_excel_parser.py` | C |
| Endpoint kê khai V2 | `backend/app/api/v1/endpoints/ke_khai_v2.py` | B |
| Endpoint admin V2 | `backend/app/api/v1/endpoints/admin_pl3.py` + `admin_import.py` | C |
| Dispatcher KPI 70 | `backend/app/api/v1/endpoints/xep_loai_moi.py:tinh_diem_kpi_70_v2` | B |
| Service FE V2 | `frontend/src/services/kpi-v2.service.ts` + `admin-pl3.service.ts` | D-E |
| Trang FE V2 | `frontend/src/app/(main)/ke-khai-v2/page.tsx` | D |
| Trang admin V2 | `frontend/src/app/(main)/admin/danh-muc-pl3/page.tsx` + `kpi-version` | E |

Migration Alembic: 9 migrations prefix `pl3_v2_*` ngày 2026-04-28.
