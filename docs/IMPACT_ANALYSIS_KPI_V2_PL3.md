# BÁO CÁO PHÂN TÍCH TÁC ĐỘNG — 2 THAY ĐỔI NGHIỆP VỤ KPI

> **Phạm vi:** Phân tích impact, KHÔNG triển khai code.
> **Hệ thống:** KPI Hải quan v1.2.0 — Production tại kpi.kv08.vn
> **Ngày tạo:** 2026-04-28
> **Tài liệu nguồn:** `BUSINESS_RULES_FINAL.md`, `Phụ lục I  Đ14.docx`, codebase commit `88845b8`

---

## 1. Tóm tắt 2 thay đổi

### Thay đổi 1 — Công thức tính điểm a, b, c

**Cũ:**
```
Mẫu số = (Tổng ngày trong tháng - Ngày nghỉ) × 96
a = Tổng SP hoàn thành quy đổi SP1 / Mẫu số
b = Tổng SP đạt CL quy đổi SP1 / Mẫu số
c = Tổng SP đạt TĐ quy đổi SP1 / Mẫu số
```

**Mới:**
```
Mẫu số = Tổng SP công chức kê khai (sau khi quy đổi về SP1)
a = Tổng SP hoàn thành quy đổi SP1 / Mẫu số
b = Tổng SP đạt CL quy đổi SP1 / Mẫu số
c = Tổng SP đạt TĐ quy đổi SP1 / Mẫu số
```

- Lãnh đạo giao việc **bên ngoài phần mềm**.
- CC tự kê khai theo công việc thực tế.
- LĐ phê duyệt từng kê khai → cơ chế kiểm soát mẫu số.
- Công thức trừ điểm CL/TĐ tuyến tính `(SL - 0.25 × min(lỗi, SL × 4))` **GIỮ NGUYÊN**.

### Thay đổi 2 — Danh mục PL3

| | **Cũ** | **Mới** |
|---|---|---|
| Danh mục công việc | 46 mục (`danh_muc_sp_cong_viec`) | 2.812 mục (file `Danh_mục_công_việc.xlsx` sheet `PL3`) |
| Sản phẩm chuẩn | SP1-SP4 (`sp_chuan`) | (vẫn giữ làm tham chiếu, 1 SP1 = 25 điểm cơ sở) |
| Cấp độ phức tạp | 5 cấp C1-C5 (`cap_do`) | **Bỏ**, thay bằng 5 Nhóm (1-5) |
| Hệ số quy đổi | Tính từ ma trận `sp_chuan × cap_do` | `he_so_quy_doi = diem_cham / 25`, sẵn trong danh mục |
| Lĩnh vực | (không có) | 15 lĩnh vực I-XV |
| 4 cột chấm điểm | (không có) | `diem_kho_sang_tao`, `diem_quy_trinh_thoi_gian`, `diem_phoi_hop`, `diem_pham_vi_ap_dung` |
| Khung điểm tối đa | (không có) | 100/200/300/400/500 tương ứng nhóm 1-5 |

### Quyết định triển khai

- Triển khai trên **testing environment trước**.
- **Giữ song song** giao diện cũ + mới (feature flag).
- Sau khi UAT đạt → cutover hoàn toàn.

---

## 2. Phân tích Database

### 2.1 Bảng và cột bị ảnh hưởng

**Thay đổi 1 (Mẫu số):**

| Bảng | Cột | Citation | Tác động |
|---|---|---|---|
| `danh_gia_thang` | `so_ngay_lam_viec`, `so_sp_goc_duoc_giao` | `backend/app/models/kpi_assessment.py:144-154` | Mẫu số mới không cần `ngày × 96`; cần thêm cột cache `tong_sp_ke_khai` |
| `bao_cao_xep_loai_chi_tiet` | `so_ngay_lam_viec`, `so_ngay_nghi` | `backend/app/models/bao_cao_xep_loai.py:420-430` | Vẫn cần để hiển thị nhưng không quyết định mẫu số |
| `nghi_phep_dang_ky` | (giữ nguyên) | — | Logic tiêu thụ thay đổi |

**Thay đổi 2 (Danh mục PL3):**

| Bảng | Citation | Tác động |
|---|---|---|
| `sp_cong_viec_chuan` | `task_catalog.py:47-130` | Giữ làm fallback / neo SP1 = 25 điểm |
| `cap_do_phuc_tap` | `task_catalog.py:133-225` | KHÔNG dùng cho V2 — soft deactivate |
| `danh_muc_sp_cong_viec` | `task_catalog.py:228-333` | Mở rộng 12 cột PL3 + nullable `sp_chuan_id` |
| `ke_khai_cong_viec` | `kpi_submission.py:158-163` | `cap_do_id` nới `nullable=True`, thêm `version_kekhai`, snapshot |

### 2.2 Schema mới đề xuất (DDL)

```sql
-- 2.1) Mở rộng danh_muc_sp_cong_viec để chứa 2.812 mục PL3
ALTER TABLE danh_muc_sp_cong_viec
    ADD COLUMN linh_vuc                VARCHAR(10),
    ADD COLUMN ten_linh_vuc            VARCHAR(200),
    ADD COLUMN nhiem_vu                VARCHAR(500),
    ADD COLUMN cong_viec_chi_tiet      TEXT,
    ADD COLUMN san_pham_dau_ra         TEXT,
    ADD COLUMN nhom_pl3                SMALLINT,
    ADD COLUMN khung_diem_toi_da       SMALLINT,
    ADD COLUMN diem_kho_sang_tao       SMALLINT,
    ADD COLUMN diem_quy_trinh_thoi_gian SMALLINT,
    ADD COLUMN diem_phoi_hop           SMALLINT,
    ADD COLUMN diem_pham_vi_ap_dung    SMALLINT,
    ADD COLUMN diem_cham               SMALLINT,
    ADD COLUMN he_so_quy_doi           NUMERIC(8,4),
    ADD COLUMN nguon_du_lieu           VARCHAR(20) DEFAULT 'V1' NOT NULL,
    ADD CONSTRAINT ck_dmsp_nhom_pl3 CHECK (nhom_pl3 IS NULL OR nhom_pl3 BETWEEN 1 AND 5),
    ADD CONSTRAINT ck_dmsp_he_so_pos CHECK (he_so_quy_doi IS NULL OR he_so_quy_doi > 0);

CREATE INDEX idx_dmsp_linh_vuc ON danh_muc_sp_cong_viec (linh_vuc);
CREATE INDEX idx_dmsp_nhom_pl3 ON danh_muc_sp_cong_viec (nhom_pl3);
CREATE INDEX idx_dmsp_search ON danh_muc_sp_cong_viec
    USING gin (to_tsvector('simple', coalesce(ten_cong_viec,'') || ' ' || coalesce(cong_viec_chi_tiet,'')));

ALTER TABLE danh_muc_sp_cong_viec
    ALTER COLUMN sp_chuan_id DROP NOT NULL;

-- 2.2) Bảng nhóm PL3 (thay 5 cấp độ C1-C5)
CREATE TABLE nhom_cong_viec_pl3 (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nhom            SMALLINT UNIQUE NOT NULL CHECK (nhom BETWEEN 1 AND 5),
    ten_nhom        VARCHAR(200) NOT NULL,
    diem_toi_da     SMALLINT NOT NULL,
    mo_ta           TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.3) Mở rộng ke_khai để biết version
ALTER TABLE ke_khai_cong_viec
    ALTER COLUMN cap_do_id DROP NOT NULL,
    ADD COLUMN version_kekhai      VARCHAR(10) NOT NULL DEFAULT 'V1',
    ADD COLUMN he_so_quy_doi_snapshot NUMERIC(8,4),
    ADD COLUMN nhom_pl3_snapshot   SMALLINT,
    ADD CONSTRAINT ck_kekhai_version CHECK (version_kekhai IN ('V1','V2_PL3')),
    ADD CONSTRAINT ck_kekhai_v2_required CHECK (
        version_kekhai <> 'V2_PL3' OR he_so_quy_doi_snapshot IS NOT NULL
    );

CREATE INDEX idx_kekhai_version ON ke_khai_cong_viec (version_kekhai, thang, nam);

-- 2.4) Cache mẫu số mới
ALTER TABLE danh_gia_thang
    ADD COLUMN tong_sp_ke_khai     NUMERIC(12,2),
    ADD COLUMN version_tinh_diem   VARCHAR(10) DEFAULT 'V1' NOT NULL
        CHECK (version_tinh_diem IN ('V1','V2_PL3'));
```

### 2.3 Quyết định kiến trúc

| Vấn đề | Quyết định | Lý do |
|---|---|---|
| Bảng `cap_do_phuc_tap` (C1-C5) | **GIỮ + soft deactivate** | 549 CC có lịch sử FK, xoá phá báo cáo quý/năm |
| Bảng `danh_muc_sp_cong_viec` 46 mục | **MỞ RỘNG cùng bảng**, đánh `nguon_du_lieu='V1'` / `'PL3'` | FK đã trỏ vào bảng này; tránh polymorphic |
| Cột `tong_sp_ke_khai` trên `danh_gia_thang` | **CÓ**, snapshot lúc CCT phê duyệt (cùng `is_khoa=TRUE`) | Tránh recompute mỗi request, đảm bảo điểm bất biến sau cutover |

### 2.4 Migration plan (Alembic)

1. `add_pl3_columns_to_danh_muc_20260501.py` — ALTER 12 cột + indexes (rollback OK).
2. `create_nhom_pl3_table_20260501.py` — Tạo bảng + seed 5 nhóm.
3. `add_version_to_kekhai_20260501.py` — `version_kekhai`, snapshot fields, nullable `cap_do_id`.
4. `add_tong_sp_ke_khai_20260501.py` — `version_tinh_diem` + cache.
5. `seed_pl3_catalog_20260502.py` — Bulk insert 2.812 mục, idempotent (`ON CONFLICT (ma_danh_muc) DO UPDATE`).
6. `deactivate_v1_catalog_after_cutover_20260601.py` — Sau UAT: `is_active=FALSE` cho V1.

**Backfill khuyến nghị** trước cutover: `version_kekhai='V1'` (đã default), `he_so_quy_doi_snapshot = sp_goc / so_luong` cho mọi bản ghi cũ.

---

## 3. Phân tích Backend

### 3.1 Service / endpoint bị ảnh hưởng

| Endpoint / Helper | Citation | Tác động |
|---|---|---|
| `calculate_kpi_score` | `ke_khai.py:65-176` | **Viết lại cho V2**: bỏ `cap_do.he_so_sp1/sp2`, dùng `danh_muc.he_so_quy_doi` trực tiếp |
| `POST /ke-khai`, `PUT /ke-khai/{id}`, multi-day, target | `ke_khai.py:879, 1207, 1386` | Phân nhánh theo `version_kekhai` |
| `tinh_so_sp_dat_cl_td` | `phe_duyet.py:90-154` | **Giữ công thức tuyến tính**, hoạt động đúng với `sp_per_unit` thập phân |
| `apply_cap_do_change` | `phe_duyet.py:180-247` | Chỉ áp V1; V2 cần helper `apply_danh_muc_change` mới |
| Phê duyệt CC, bulk approve | `phe_duyet.py:577-586, 774-775` | Tính lại SP CL/TĐ với hệ số V2 |
| `tinh_diem_kpi_70` | `xep_loai_moi.py:49-197` | **Phân nhánh theo `version_tinh_diem`**: V1 dùng `ngày×96`, V2 dùng `SUM(so_sp_goc_quy_doi)` |
| `tinh_diem_kpi_70_lanh_dao` | `xep_loai_moi.py:200-329` | **KHÔNG bị ảnh hưởng** — đã dùng N công việc làm mẫu số |
| Tab tạm tính, target CC | `danh_gia.py:405, 432, 458, 1817, 1846, 1872, 1906, 1995` | 8 chỗ hardcode `* 96` → switch hoặc bỏ |
| Tính SP được giao | `nghi_phep.py:1591, 1669-1674, 1712` | Bỏ cho V2 |
| Báo cáo xếp loại tháng | `bao_cao_xep_loai.py:222-292, 331-414, 507-541, 668, 747` | Phân nhánh theo `version_tinh_diem` |
| Báo cáo quý | `bao_cao_xep_loai_quy.py`, `xep_loai_quy_helpers.py` | Theo PL Đ14: lũy kế tổng SP 3 tháng — đọc từ `tong_sp_ke_khai` |
| In bảng kê | `in_bang_ke.py` | V1 hiển thị `ngày×96`; V2 hiển thị `tong_sp_ke_khai` |
| Admin CRUD danh mục | `admin.py` | Thêm 12 cột PL3 |
| Master data dropdown | `danh_muc.py:131-410` | Thêm `/linh-vuc`, filter `nhom_pl3`, `linh_vuc`, `nguon_du_lieu` |

### 3.2 Logic `so_sp_goc_quy_doi` mới

**V1 (giữ nguyên cho `version='V1'`):**
```
so_sp_goc_quy_doi = so_luong × sp_chuan.he_so_quy_doi_sp1 × cap_do.he_so_sp1_or_sp2
```
(`ke_khai.py:174`)

**V2 (mới, `version='V2_PL3'`):**
```
so_sp_goc_quy_doi = so_luong × danh_muc.he_so_quy_doi
                  = so_luong × (diem_cham / 25)
```

Snapshot `he_so_quy_doi_snapshot` lưu vào `ke_khai_cong_viec` ngay khi tạo (đồng pattern với `don_vi_id_snapshot` ở `kpi_submission.py:117`).

### 3.3 Công thức trừ điểm CL/TĐ với hệ số thập phân

Công thức (`phe_duyet.py:137-152`):
```python
sp_per_unit = sp_goc / Decimal(str(so_luong))
max_loi = so_luong * 4
sp_tru = Decimal("0.25") * loi × sp_per_unit
sp_chat_luong = max(sp_goc - sp_tru, 0)
```

**KHÔNG cần điều chỉnh.**
- Tuyến tính, không phụ thuộc nguyên/thập phân.
- Ví dụ V2: `he_so=6.4`, `so_luong=5`, `loi=3` → `sp_goc=32`, `sp_per_unit=6.4`, `sp_tru=4.8`, `sp_dat=27.2` ✓
- `Decimal` xuyên suốt nên không mất chính xác.
- `Numeric(10,2)` ở `kpi_submission.py:310-326` đủ scale.

PL Đ14 docx xác nhận: "1 SP chậm tiến độ → còn 0,75 SP" = `1 - 0.25 × 1`.

### 3.4 API kê khai V2

**Request body** (`app/schemas/kpi_submission.py:42-62`):
```python
version_kekhai: Literal["V1","V2_PL3"] = "V1"
# V1: danh_muc_sp_id, cap_do_id (required), so_luong, he_so_thuc_te
# V2: danh_muc_sp_id (PL3 row), cap_do_id=None, so_luong
```

**Validation mới:**
- `V2_PL3`: `danh_muc.nguon_du_lieu='PL3'`, `cap_do_id IS NULL`, `he_so_quy_doi NOT NULL`.
- `V1`: `danh_muc.nguon_du_lieu='V1'`, `cap_do_id` required.
- Reject mixing trong cùng `(cong_chuc, thang, nam)`.

**Response thêm:** `nhom_pl3`, `khung_diem_toi_da`, `linh_vuc`, `he_so_quy_doi_snapshot`.

### 3.5 KPI lãnh đạo

**KHÔNG bị ảnh hưởng.** `tinh_diem_kpi_70_lanh_dao` (`xep_loai_moi.py:200-329`) đã dùng `tong_cong_viec` (đếm N) làm mẫu số, không dùng 96.

---

## 4. Phân tích Frontend

### 4.1 Trang/component bị ảnh hưởng

| File | Tác động |
|---|---|
| `components/kpi/KpiTargetModal.tsx` (635 dòng) | Form kê khai 1 dòng — viết V2 song song |
| `components/kpi/KpiMultiDayModal.tsx` (590 dòng) | Form kê khai nhiều ngày — viết V2 song song |
| `app/(main)/ke-khai/page.tsx:644-704` | Bảng list — thêm cột Nhóm/Lĩnh vực/Hệ số |
| `app/(main)/admin/danh-muc-cv/page.tsx` (614 dòng) | Redesign cho 12 cột PL3 + import Excel |
| `app/(main)/admin/cap-do/page.tsx` (498 dòng) | Đánh dấu deprecated |
| `app/(main)/admin/sp-chuan/page.tsx` (408 dòng) | Read-only sau cutover |
| `app/(main)/danh-gia/page.tsx:312, 317, 321` | `soNgayLamViec * 96` → switch theo version |
| `components/xep-loai/tabs/TabTamTinh.tsx:172-193, 583-586` | Hiển thị mẫu số mới |
| `components/xep-loai/tabs/TabBaoCao.tsx:1235` | Cột "ngày làm việc" giữ nhưng không quyết định mẫu số |
| `components/xep-loai/tabs/TabCongViec.tsx` | Bảng SP — thêm cột nhóm/lĩnh vực |
| `services/kpi.service.ts:42-44, 158, 781-833` | Thêm `getLinhVuc`, `getDanhMucCongViecPL3({linh_vuc, nhom_pl3, search})` |
| `services/admin.service.ts:358-377` | Thêm field PL3 vào DTO admin |

### 4.2 UX search 2.812 mục

**Khuyến nghị:** Hierarchical 3-layer, KHÔNG dropdown đơn.
1. **Lĩnh vực (15 mục I-XV)**: dropdown bắt buộc, persist trong session.
2. **Nhóm (1-5)**: chip filter optional.
3. **Search box**: debounced server-side autocomplete `/danh-muc-sp?linh_vuc=I&nhom_pl3=2&search=...`.

KHÔNG client-side filter 2.812 mục (~300KB+, chậm trên cửa khẩu mạng yếu). Component: `Combobox` (Headless UI) hoặc `cmdk`.

### 4.3 Banner "Tổng SP kê khai" cho CC

Trong `app/(main)/ke-khai/page.tsx`, banner top:
```
[Tổng SP của bạn tháng 04/2026: 285.6 SP]   (= mẫu số tính KPI)
- Đã duyệt: 240.0 SP
- Chờ duyệt: 45.6 SP
```

Mở rộng `/ke-khai/thong-ke/thang` (`ke_khai.py:533`) trả `tong_sp_da_duyet`, `tong_sp_cho_duyet`, `tong_sp_du_kien`.

### 4.4 Redesign admin danh mục

**Bắt buộc.** Layout mới:
1. **Tab "V2 — PL3"** (default): filter lĩnh vực + nhóm + keyword; bảng với 4 cột chấm + auto-compute `diem_cham`/`he_so_quy_doi`.
2. **Tab "V1 — Legacy"**: read-only sau cutover.
3. **Nút "Import Excel PL3"**: upload → dry-run → confirm → `POST /admin/danh-muc-sp/import-pl3`.

---

## 5. Quản lý 2 hệ thống song song

### 5.1 Cơ chế feature flag

**Khuyến nghị: 2 route riêng + cờ DB.**

```
/ke-khai           → V1 (giữ nguyên)
/ke-khai-v2        → V2 (mới)
```

Cờ `cong_chuc.kpi_version_pinned VARCHAR(10)` (NULL = dùng `platform_config.kpi_version_default`):
- Admin pin 1 đơn vị test V2: `UPDATE cong_chuc SET kpi_version_pinned='V2_PL3' WHERE don_vi_id=...`
- Sidebar (`layout.tsx`) render menu theo cờ.
- 2 endpoint riêng, dùng chung helper trừ điểm CL/TĐ.

**Lý do bỏ env flag / query param:**
- Env flag → phải redeploy cho mỗi rollout đợt.
- Query param → URL bookmarked dẫn về sai version.

### 5.2 Phân biệt V1 vs V2 trong DB

**Cột `version_kekhai` trên `ke_khai_cong_viec`.**

KHÔNG tạo bảng riêng vì:
- 90% logic chung (cong_chuc, phê duyệt, lỗi CL/TĐ).
- Tránh duplicate `phe_duyet_sp`, audit log, indexes.
- Báo cáo quý phải UNION ALL → phá pattern.
- Query thêm `WHERE version_kekhai=$1` < 1ms với index.

### 5.3 Quy tắc per-tháng

**1 tháng = 1 version.** Ràng buộc:
- `danh_gia_thang.version_tinh_diem` xác định version cho cả tháng.
- Bản kê khai đầu tiên trong tháng → set `version_tinh_diem`; bản sau phải cùng version.
- Validation backend reject `MIXED_VERSION_NOT_ALLOWED`.
- Migration giữa 2 version trong cùng tháng: chỉ TCCB xoá toàn bộ kê khai tháng đó (giống `is_khoa` hiện tại).

---

## 6. Rủi ro & Câu hỏi nghiệp vụ

### 6.1 5 rủi ro lớn nhất

1. **Mẫu số = 0** khi CC không kê khai → chia cho 0 (`xep_loai_moi.py:171`). Cần policy: "Không đánh giá" hay D.
2. **Lạm phát kê khai để tăng mẫu số/giảm tỷ lệ trừ điểm**. Cơ chế kiểm soát = LĐ từ chối; cần audit dashboard cho TCCB (top CC tăng kê khai bất thường).
3. **Hệ số `diem_cham/25` thập phân** → tích lũy rounding error. Khắc phục: `Decimal(8,4)` xuyên suốt, làm tròn chỉ ở display.
4. **Migration 2.812 mục Excel sai format**. Validate cứng: tổng 4 cột chấm = `diem_cham`; `he_so_quy_doi = diem_cham/25` (tolerance 0.001); `khung_diem_toi_da` ∈ {100,200,300,400,500} match `nhom_pl3`.
5. **Báo cáo quý lẫn V1+V2** trong giai đoạn cutover. PL Đ14 yêu cầu lũy kế 3 tháng. Cần policy: ép cả quý cùng version, hoặc TB điểm 3 tháng theo từng version riêng (KHÔNG lũy kế tử/mẫu).

### 6.2 12 câu hỏi nghiệp vụ cần PM chốt TRƯỚC khi code

1. **Mẫu số = 0**: KPI = 0 (D) / "Không đánh giá" (NULL) / miễn trừ?
2. **Phân quyền 2.812 mục theo lĩnh vực/đơn vị**: HQ cửa khẩu chỉ thấy mục nào? Có map sẵn không?
3. **`khung_diem_toi_da`**: trần `so_luong × diem_cham ≤ khung` mỗi tháng/quý? Hay tham khảo?
4. **Lãnh đạo override `he_so_quy_doi`** (như C5 hiện tại) hay cố định 100%?
5. **Lãnh đạo có dùng PL3** hay giữ "1 công việc = 1 đơn vị" (`xep_loai_moi.py:200-329`)?
6. **Báo cáo quý cutover**: ép cùng version, hay trộn? Lũy kế ra sao theo PL Đ14?
7. **Tiêu chí chung Nhóm I/II/III max 10đ** trong PL Đ14 docx khác cấu trúc cũ (5+5/4×2.5/4×2.5) (`kpi_assessment.py:751-762`). **Đề nghị tách scope**.
8. **Cấp độ C5 "theo thực tế"** (`task_catalog.py:182-186`) còn giữ trong V2?
9. **Audit retroactive**: admin sửa `he_so_quy_doi` → rebuild snapshot hay snapshot final?
10. **Cutover date**: prod khi nào? Toàn cục hay rollout từng đơn vị?
11. **Số ngày làm việc/nghỉ phép**: V2 vẫn track? Vẫn affect KPI (nghỉ >X tự xếp D)?
12. **Min `so_luong`**: hiện `> 0` (`kpi_submission.py:393`). V2 cho phép `0.5`?

### 6.3 Ước lượng effort

| Phase | Effort |
|---|---|
| Database migration | 16h |
| Backend V2 endpoints | 32h |
| Backend xếp loại/báo cáo | 24h |
| Backend admin CRUD PL3 | 16h |
| Backend tests | 16h |
| Frontend ke-khai-v2 | 32h |
| Frontend admin redesign | 20h |
| Frontend xep-loai/danh-gia | 16h |
| Frontend tests | 8h |
| QA / UAT / regression | 24h |
| Buffer 20% | 41h |
| **TỔNG** | **~245h ≈ 6 tuần × 1 fullstack** |

---

## 7. Roadmap

| # | Milestone | Mô tả ngắn | File/module ảnh hưởng | Giờ |
|---|---|---|---|---|
| M0 | **Spec lock** | Chốt 12 câu hỏi §6.2 | `docs/` | 8h |
| M1 | **DB schema PL3** | 4 ALTER + 1 seed Excel + indexes | `alembic/versions/*_pl3_*.py`, `models/task_catalog.py`, `models/kpi_submission.py`, `models/kpi_assessment.py` | 16h |
| M2 | **Backend kê khai V2** | `calculate_kpi_score` V2, validation, /ke-khai-v2, snapshot | `endpoints/ke_khai.py`, `schemas/kpi_submission.py` | 32h |
| M3 | **Backend phê duyệt V2** | `apply_danh_muc_change` V2, công thức trừ điểm `Decimal` | `endpoints/phe_duyet.py` | 12h |
| M4 | **Backend xếp loại nhánh** | `tinh_diem_kpi_70` switch theo `version_tinh_diem`, cache `tong_sp_ke_khai` | `endpoints/xep_loai_moi.py`, `endpoints/danh_gia.py`, `endpoints/bao_cao_xep_loai.py` | 24h |
| M5 | **Backend admin + import Excel** | CRUD 12 cột, upload Excel với dry-run + audit | `endpoints/admin.py`, `endpoints/danh_muc.py` | 16h |
| M6 | **Backend tests** | V2 happy-path, mixed-version reject, mẫu số=0, rounding | `tests/test_kekhai_v2.py`, `tests/test_xep_loai_v2.py` | 16h |
| M7 | **Frontend services + types** | `getLinhVuc`, `getDanhMucPL3`, type V2 | `services/kpi.service.ts`, `services/admin.service.ts`, `types/` | 8h |
| M8 | **Frontend kê khai V2** | `KpiTargetModalV2`, `KpiMultiDayModalV2`, /ke-khai-v2, banner Tổng SP | `components/kpi/*V2.tsx`, `app/(main)/ke-khai-v2/page.tsx` | 32h |
| M9 | **Frontend admin PL3** | Tab V1/V2, edit modal 12 cột auto-compute, Import Excel UI | `app/(main)/admin/danh-muc-cv/page.tsx` | 20h |
| M10 | **Frontend xếp loại/báo cáo** | TabTamTinh, TabBaoCao, TabCongViec render theo version | `components/xep-loai/tabs/*.tsx`, `app/(main)/danh-gia/page.tsx` | 16h |
| M11 | **Frontend tests** | Modal V2, snapshot client-side | `__tests__/`, vitest config | 8h |
| M12 | **UAT test env** | Pin 1 đơn vị V2 trong tháng 5/2026; song song V1 cho 14 đơn vị | toàn module | 24h |
| M13 | **Cutover** | Migration deactivate V1, đổi default config V2_PL3, smoke test | DB + config | 8h |
| M14 | **Tài liệu + đào tạo** | Update PROGRESS.md, BUSINESS_RULES, hướng dẫn admin import | `docs/`, README | 8h |
| | **TỔNG** | | | **~248h** |

---

## 8. Nguyên tắc thực thi

- KHÔNG sửa file V1 hiện hành (giữ test env regression-free).
- Mỗi bước tạo file/route/component mới có hậu tố `_v2` hoặc `V2`.
- Cờ `version_kekhai` / `version_tinh_diem` là **single source of truth** — mọi nhánh logic đều đọc cờ, không đoán theo `cap_do_id IS NULL`.
- Migration Alembic phải reversible; mỗi bước có downgrade test.
- `Decimal` xuyên suốt mọi tính toán; làm tròn chỉ ở display layer.
