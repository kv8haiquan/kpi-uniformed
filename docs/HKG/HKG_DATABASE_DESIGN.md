# HKG_DATABASE_DESIGN.md — Schema `meeting`

**Phiên bản:** 1.0 (MVP) · **Ngày:** 30/04/2026
**Database:** `kpi_haiquan` · **Schema:** `meeting`

> File này định nghĩa chi tiết 10 bảng cốt lõi của HKG MVP. Khi có yêu cầu sinh migration Alembic, tham chiếu file này.

---

## 1. NGUYÊN TẮC THIẾT KẾ

```
✅ TUÂN THỦ:
- PK: UUID DEFAULT gen_random_uuid()
- Soft delete: is_deleted BOOLEAN DEFAULT FALSE
- Audit trail: created_at, updated_at TIMESTAMPTZ
- Tracking: created_by UUID REFERENCES public.cong_chuc(id)
- Cross-schema FK chỉ tới: public.cong_chuc, public.don_vi, public.platform_role
- Soft enum: VARCHAR + CHECK constraint (dễ migrate hơn ENUM type)
- Index: tất cả FK + cột filter thường dùng (trang_thai, ngay_hop, don_vi_id)

⛔ TUYỆT ĐỐI KHÔNG:
- KHÔNG sửa cột public.cong_chuc, public.don_vi, public.vai_tro
- KHÔNG tạo bảng audit_log riêng — dùng common.audit_log
- KHÔNG tạo FK sang schema khác (kpi.*, lms.*)
- KHÔNG dùng SERIAL/BIGSERIAL cho PK
```

> ⚠️ **Lưu ý:** `common.audit_log` **chưa tồn tại** trong codebase (verify P0 — không có trong `create_common_schema_*.py`). Nếu vẫn chưa có khi vào G1, **tạo migration platform-level trong `common_service` TRƯỚC** — đây là trách nhiệm nền tảng, không phải scope HKG. Schema gợi ý xem **Phụ lục A** ở cuối file này.
>
> KPI hiện có `audit_log` riêng tại `backend/app/models/audit_log.py` (schema `public`, design DML-only INSERT/UPDATE/DELETE) — **không tái sử dụng được** cho HKG vì không có cột `module/hanh_dong` cho audit nghiệp vụ.

---

## 2. SCHEMA SETUP

```sql
-- Migration đầu tiên: Alembic 001_create_meeting_schema
CREATE SCHEMA IF NOT EXISTS meeting;
GRANT USAGE ON SCHEMA meeting TO kpi_user;
GRANT ALL ON SCHEMA meeting TO kpi_user;

-- Bật extension cần thiết (nếu chưa có)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- cho gen_random_uuid()
```

---

## 3. SƠ ĐỒ QUAN HỆ

```
┌──────────────────────────────────────────────────────────────────┐
│                       SCHEMA: public                              │
│  cong_chuc ──┐    don_vi ──┐    platform_role ──┐                │
└─────────────┼──────────────┼─────────────────────┼───────────────┘
              │              │                     │
              ▼              ▼                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                       SCHEMA: meeting                             │
│                                                                   │
│   cuoc_hop (1) ──┬── (N) thanh_phan ──── public.cong_chuc        │
│                  ├── (N) tai_lieu                                 │
│                  ├── (N) diem_danh ────── public.cong_chuc        │
│                  ├── (N) xin_phep_vang ── public.cong_chuc        │
│                  ├── (N) y_kien ───────── public.cong_chuc        │
│                  ├── (1) bien_ban                                 │
│                  └── (N) ket_luan ──┬── (N) tien_do               │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

Relationships:
- cuoc_hop.don_vi_to_chuc_id → public.don_vi(id)
- cuoc_hop.chu_toa_id, thu_ky_id → public.cong_chuc(id)
- thanh_phan.cong_chuc_id → public.cong_chuc(id)
- diem_danh.cong_chuc_id → public.cong_chuc(id)
- xin_phep_vang.cong_chuc_id → public.cong_chuc(id)
- ket_luan.nguoi_phu_trach_id → public.cong_chuc(id)
```

---

## 4. CHI TIẾT 10 BẢNG MVP

### 4.1. `meeting.cuoc_hop` — Cuộc họp

```sql
CREATE TABLE meeting.cuoc_hop (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Thông tin cơ bản
    tieu_de VARCHAR(500) NOT NULL,
    mo_ta TEXT,

    -- Phân loại
    khoi VARCHAR(20) NOT NULL DEFAULT 'CHUYEN_MON'
        CHECK (khoi IN ('DANG', 'CHUYEN_MON', 'HANH_CHINH', 'BAN_NHOM')),
    hinh_thuc VARCHAR(20) NOT NULL DEFAULT 'TRUC_TIEP'
        CHECK (hinh_thuc IN ('TRUC_TIEP', 'TRUC_TUYEN', 'HYBRID')),

    -- Thời gian & địa điểm
    ngay_hop DATE NOT NULL,
    gio_bat_dau TIME NOT NULL,
    gio_ket_thuc TIME,
    dia_diem VARCHAR(300),

    -- Vai trò chính
    don_vi_to_chuc_id UUID NOT NULL REFERENCES public.don_vi(id),
    chu_toa_id UUID NOT NULL REFERENCES public.cong_chuc(id),
    thu_ky_id UUID REFERENCES public.cong_chuc(id),

    -- Trạng thái
    trang_thai VARCHAR(30) NOT NULL DEFAULT 'LEN_KE_HOACH'
        CHECK (trang_thai IN (
            'LEN_KE_HOACH',  -- vừa tạo
            'DA_THONG_BAO',  -- đã gửi giấy mời
            'DANG_DIEN_RA',  -- đang họp
            'HOAN_THANH',    -- đã kết thúc
            'HUY'            -- đã hủy
        )),

    -- Họp định kỳ (optional MVP)
    la_dinh_ky BOOLEAN DEFAULT FALSE,
    chu_ky VARCHAR(20)
        CHECK (chu_ky IS NULL OR chu_ky IN ('TUAN', 'THANG', 'QUY')),

    -- Phase 8 placeholder (chưa dùng MVP, để sẵn cho sau)
    chi_bo_id UUID,  -- chỉ điền khi khoi='DANG' — phase sau

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES public.cong_chuc(id),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_cuoc_hop_ngay ON meeting.cuoc_hop(ngay_hop) WHERE is_deleted = FALSE;
CREATE INDEX idx_cuoc_hop_don_vi ON meeting.cuoc_hop(don_vi_to_chuc_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_cuoc_hop_chu_toa ON meeting.cuoc_hop(chu_toa_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_cuoc_hop_trang_thai ON meeting.cuoc_hop(trang_thai) WHERE is_deleted = FALSE;
CREATE INDEX idx_cuoc_hop_khoi ON meeting.cuoc_hop(khoi) WHERE is_deleted = FALSE;

COMMENT ON TABLE meeting.cuoc_hop IS 'Cuộc họp — bảng trung tâm của HKG';
COMMENT ON COLUMN meeting.cuoc_hop.khoi IS 'Khối họp: Đảng/Chuyên môn/Hành chính/Ban-Nhóm';
COMMENT ON COLUMN meeting.cuoc_hop.chi_bo_id IS 'Phase 8 — chỉ dùng khi khoi=DANG';
```

### 4.2. `meeting.thanh_phan` — Thành phần tham dự

```sql
CREATE TABLE meeting.thanh_phan (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    cuoc_hop_id UUID NOT NULL REFERENCES meeting.cuoc_hop(id) ON DELETE CASCADE,
    cong_chuc_id UUID NOT NULL REFERENCES public.cong_chuc(id),

    loai_tham_du VARCHAR(20) NOT NULL DEFAULT 'BAT_BUOC'
        CHECK (loai_tham_du IN ('BAT_BUOC', 'THAM_KHAO')),

    -- Xác nhận tham dự
    xac_nhan VARCHAR(20) DEFAULT 'CHUA_PHAN_HOI'
        CHECK (xac_nhan IN ('CHUA_PHAN_HOI', 'THAM_DU', 'KHONG_THAM_DU', 'UY_QUYEN')),
    nguoi_uy_quyen_id UUID REFERENCES public.cong_chuc(id),  -- nếu uỷ quyền cho người khác
    ghi_chu_xac_nhan TEXT,
    thoi_gian_xac_nhan TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (cuoc_hop_id, cong_chuc_id)  -- 1 CBCC chỉ được mời 1 lần/cuộc họp
);

CREATE INDEX idx_thanh_phan_cuoc_hop ON meeting.thanh_phan(cuoc_hop_id);
CREATE INDEX idx_thanh_phan_cong_chuc ON meeting.thanh_phan(cong_chuc_id);
```

### 4.3. `meeting.tai_lieu` — Tài liệu họp

```sql
CREATE TABLE meeting.tai_lieu (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    cuoc_hop_id UUID NOT NULL REFERENCES meeting.cuoc_hop(id) ON DELETE CASCADE,

    ten_tai_lieu VARCHAR(500) NOT NULL,
    mo_ta TEXT,

    -- File trên MinIO
    minio_bucket VARCHAR(100) NOT NULL DEFAULT 'meeting',
    minio_key VARCHAR(500) NOT NULL,  -- path: {cuoc_hop_id}/{filename}
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    extension VARCHAR(10),  -- pdf, docx, xlsx, pptx

    -- Phân quyền MVP: 2 cấp (KHÔNG có cấp Mật trong MVP)
    phan_quyen VARCHAR(20) NOT NULL DEFAULT 'CONG_KHAI'
        CHECK (phan_quyen IN ('CONG_KHAI', 'HAN_CHE')),

    cho_phep_tai BOOLEAN NOT NULL DEFAULT TRUE,
    cho_phep_in BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES public.cong_chuc(id),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_tai_lieu_cuoc_hop ON meeting.tai_lieu(cuoc_hop_id) WHERE is_deleted = FALSE;
```

### 4.4. `meeting.diem_danh` — Điểm danh

```sql
CREATE TABLE meeting.diem_danh (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    cuoc_hop_id UUID NOT NULL REFERENCES meeting.cuoc_hop(id) ON DELETE CASCADE,
    cong_chuc_id UUID NOT NULL REFERENCES public.cong_chuc(id),

    hinh_thuc VARCHAR(20) NOT NULL
        CHECK (hinh_thuc IN ('QR', 'BAM_TAY')),  -- TU_DONG = phase Jitsi

    trang_thai VARCHAR(20) NOT NULL DEFAULT 'CO_MAT'
        CHECK (trang_thai IN ('CO_MAT', 'DEN_MUON', 'VANG_CO_PHEP', 'VANG_KHONG_PHEP')),

    gio_diem_danh TIMESTAMPTZ,
    ghi_chu TEXT,

    -- Người bấm điểm danh (nếu hinh_thuc=BAM_TAY)
    nguoi_diem_danh_id UUID REFERENCES public.cong_chuc(id),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (cuoc_hop_id, cong_chuc_id)
);

CREATE INDEX idx_diem_danh_cuoc_hop ON meeting.diem_danh(cuoc_hop_id);
CREATE INDEX idx_diem_danh_cong_chuc ON meeting.diem_danh(cong_chuc_id);
```

### 4.5. `meeting.xin_phep_vang` — Đơn xin phép vắng

```sql
CREATE TABLE meeting.xin_phep_vang (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    cuoc_hop_id UUID NOT NULL REFERENCES meeting.cuoc_hop(id) ON DELETE CASCADE,
    cong_chuc_id UUID NOT NULL REFERENCES public.cong_chuc(id),

    ly_do TEXT NOT NULL,
    nguoi_du_thay_id UUID REFERENCES public.cong_chuc(id),

    -- File đính kèm (optional)
    minio_key VARCHAR(500),

    -- Trạng thái duyệt
    trang_thai VARCHAR(30) NOT NULL DEFAULT 'CHO_DUYET'
        CHECK (trang_thai IN ('CHO_DUYET', 'DA_DUYET', 'TU_CHOI', 'TU_DONG_DUYET')),

    auto_approved BOOLEAN NOT NULL DEFAULT FALSE,
    nguoi_duyet_id UUID REFERENCES public.cong_chuc(id),
    thoi_gian_duyet TIMESTAMPTZ,
    ly_do_tu_choi TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (cuoc_hop_id, cong_chuc_id)
);

CREATE INDEX idx_xin_phep_cuoc_hop ON meeting.xin_phep_vang(cuoc_hop_id);
CREATE INDEX idx_xin_phep_trang_thai ON meeting.xin_phep_vang(trang_thai);
```

### 4.6. `meeting.y_kien` — Ý kiến của thành viên

```sql
CREATE TABLE meeting.y_kien (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    cuoc_hop_id UUID NOT NULL REFERENCES meeting.cuoc_hop(id) ON DELETE CASCADE,
    cong_chuc_id UUID NOT NULL REFERENCES public.cong_chuc(id),

    noi_dung TEXT NOT NULL,
    loai VARCHAR(20) NOT NULL DEFAULT 'TRONG_HOP'
        CHECK (loai IN ('TRUOC_HOP', 'TRONG_HOP', 'SAU_HOP')),

    -- File đính kèm (optional)
    minio_key VARCHAR(500),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_y_kien_cuoc_hop ON meeting.y_kien(cuoc_hop_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_y_kien_loai ON meeting.y_kien(loai);
```

### 4.7. `meeting.bien_ban` — Biên bản họp

```sql
CREATE TABLE meeting.bien_ban (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    cuoc_hop_id UUID NOT NULL UNIQUE REFERENCES meeting.cuoc_hop(id) ON DELETE CASCADE,

    -- Nội dung biên bản (TipTap JSON)
    noi_dung_json JSONB,
    noi_dung_html TEXT,  -- cache rendered HTML

    -- Trạng thái
    trang_thai VARCHAR(30) NOT NULL DEFAULT 'DANG_SOAN'
        CHECK (trang_thai IN ('DANG_SOAN', 'TRINH_KY', 'DA_KY', 'CONG_BO')),

    -- File xuất ra
    file_pdf_minio_key VARCHAR(500),
    file_docx_minio_key VARCHAR(500),

    -- Mock CKS (MVP) — chữ ký thật ở Phase 6
    is_mock_signed BOOLEAN NOT NULL DEFAULT FALSE,
    qr_xac_thuc VARCHAR(500),  -- URL/code QR
    hash_noi_dung VARCHAR(64),  -- SHA-256

    -- Audit
    nguoi_soan_id UUID NOT NULL REFERENCES public.cong_chuc(id),
    nguoi_ky_id UUID REFERENCES public.cong_chuc(id),
    thoi_gian_ky TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_bien_ban_trang_thai ON meeting.bien_ban(trang_thai);
```

### 4.8. `meeting.ket_luan` — Kết luận / Nhiệm vụ giao

```sql
CREATE TABLE meeting.ket_luan (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    cuoc_hop_id UUID NOT NULL REFERENCES meeting.cuoc_hop(id) ON DELETE CASCADE,

    noi_dung TEXT NOT NULL,
    nguoi_phu_trach_id UUID NOT NULL REFERENCES public.cong_chuc(id),
    don_vi_phu_trach_id UUID REFERENCES public.don_vi(id),

    han_hoan_thanh DATE,
    muc_uu_tien VARCHAR(10) NOT NULL DEFAULT 'TRUNG_BINH'
        CHECK (muc_uu_tien IN ('CAO', 'TRUNG_BINH', 'THAP')),

    tien_do_phan_tram INTEGER NOT NULL DEFAULT 0
        CHECK (tien_do_phan_tram BETWEEN 0 AND 100),

    trang_thai VARCHAR(30) NOT NULL DEFAULT 'CHUA_BAT_DAU'
        CHECK (trang_thai IN ('CHUA_BAT_DAU', 'DANG_LAM', 'HOAN_THANH', 'TRE_HAN', 'HUY')),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_ket_luan_cuoc_hop ON meeting.ket_luan(cuoc_hop_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_ket_luan_phu_trach ON meeting.ket_luan(nguoi_phu_trach_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_ket_luan_han ON meeting.ket_luan(han_hoan_thanh) WHERE is_deleted = FALSE AND trang_thai != 'HOAN_THANH';
```

### 4.9. `meeting.tien_do` — Cập nhật tiến độ kết luận

```sql
CREATE TABLE meeting.tien_do (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    ket_luan_id UUID NOT NULL REFERENCES meeting.ket_luan(id) ON DELETE CASCADE,

    mo_ta TEXT NOT NULL,
    phan_tram_truoc INTEGER,  -- snapshot tiến độ trước khi cập nhật
    phan_tram_sau INTEGER NOT NULL CHECK (phan_tram_sau BETWEEN 0 AND 100),

    file_minh_chung_minio_key VARCHAR(500),

    nguoi_cap_nhat_id UUID NOT NULL REFERENCES public.cong_chuc(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tien_do_ket_luan ON meeting.tien_do(ket_luan_id);
```

### 4.10. `meeting.mau_bieu` — Template biên bản (MVP: 1 template chung)

```sql
CREATE TABLE meeting.mau_bieu (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    loai VARCHAR(30) NOT NULL
        CHECK (loai IN ('BIEN_BAN', 'GIAY_MOI', 'KET_LUAN', 'BAO_CAO')),

    ten_mau VARCHAR(200) NOT NULL,
    mo_ta TEXT,

    -- Áp dụng cho khối nào (MVP: dùng chung tất cả)
    ap_dung_cho VARCHAR(50) NOT NULL DEFAULT 'TAT_CA',  -- 'TAT_CA', 'DANG', 'CHUYEN_MON'

    minio_key VARCHAR(500) NOT NULL,
    phien_ban INTEGER NOT NULL DEFAULT 1,
    la_mac_dinh BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES public.cong_chuc(id),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_mau_bieu_loai ON meeting.mau_bieu(loai) WHERE is_deleted = FALSE;
```

---

## 5. SỬ DỤNG `common.audit_log`

HKG **KHÔNG** tạo bảng audit riêng. Dùng chung `common.audit_log` (xem **Phụ lục A** cuối file để tạo bảng nếu chưa có):

```sql
-- module = 'MEETING' để filter
INSERT INTO common.audit_log
    (module, hanh_dong, doi_tuong_loai, doi_tuong_id, nguoi_thuc_hien_id, chi_tiet)
VALUES (
    'MEETING',
    'CREATE_MEETING',
    'cuoc_hop',
    '{cuoc_hop_id}',
    '{user_id}',
    '{"tieu_de": "...", "khoi": "CHUYEN_MON"}'::jsonb
);
```

**Các giá trị `hanh_dong` cần ghi log trong HKG:**
- `LOGIN_HKG` — vào module HKG
- `CREATE_MEETING`, `UPDATE_MEETING`, `CANCEL_MEETING`
- `UPLOAD_DOC`, `DELETE_DOC`, `VIEW_DOC`, `DOWNLOAD_DOC`
- `CHECKIN_QR`, `CHECKIN_MANUAL`
- `SUBMIT_LEAVE`, `APPROVE_LEAVE`, `REJECT_LEAVE`, `AUTO_APPROVE_LEAVE`
- `CREATE_OPINION`
- `CREATE_MINUTES`, `SIGN_MINUTES`, `EXPORT_MINUTES`
- `CREATE_CONCLUSION`, `UPDATE_PROGRESS`

---

## 6. SỬ DỤNG `common.thong_bao`

> **Schema thật `common.thong_bao`** (verify P0 từ `backend/common_service/models/thong_bao.py`):
> `id, nguoi_nhan_id, tieu_de, noi_dung, loai(VARCHAR 50), link_url(TEXT), doi_tuong_type, doi_tuong_id, da_doc, ngay_doc, muc_do, created_at`.
>
> **KHÔNG có cột `module`** — chỉ có `loai`. **KHÔNG có CHECK constraint** trên `loai` → có thể dùng giá trị `'MEETING'` ngay, không cần migration mở rộng.

```sql
-- Pattern HKG: loai='MEETING' (module level), doi_tuong_type=sub-loại notification
INSERT INTO common.thong_bao
    (nguoi_nhan_id, tieu_de, noi_dung, loai, link_url, doi_tuong_type, doi_tuong_id, muc_do)
VALUES (
    '{cong_chuc_id}',
    'Giấy mời họp giao ban tuần',
    'Bạn được mời tham dự cuộc họp...',
    'MEETING',
    '/hop-khong-giay/chi-tiet/{cuoc_hop_id}',
    'GIAY_MOI_HOP',     -- sub-loại notification (lưu vào doi_tuong_type)
    '{cuoc_hop_id}',
    'BINH_THUONG'        -- KHAN | QUAN_TRONG | BINH_THUONG
);
```

**Sub-loại notification HKG (lưu vào `doi_tuong_type`):**
- `GIAY_MOI_HOP` — giấy mời họp mới
- `NHAC_HOP_24H`, `NHAC_HOP_1H`, `NHAC_HOP_30P` — nhắc lịch
- `THAY_DOI_HOP`, `HUY_HOP` — cập nhật (`muc_do=QUAN_TRONG`)
- `XIN_PHEP_CHO_DUYET` — Chủ tọa nhận đơn xin vắng
- `KET_LUAN_GIAO` — CBCC nhận nhiệm vụ
- `NHAC_HAN_3_NGAY` — sắp đến hạn nhiệm vụ
- `BIEN_BAN_TRINH_KY` — Chủ tọa nhận biên bản chờ ký
- `BIEN_BAN_CONG_BO` — biên bản hoàn tất

**Truy vấn thông báo HKG của 1 user:**

```sql
SELECT * FROM common.thong_bao
WHERE nguoi_nhan_id = '{user_id}'
  AND loai = 'MEETING'
  AND da_doc = FALSE
ORDER BY created_at DESC;
```

---

## 7. STORAGE LAYOUT

> **MVP filesystem-based** (quyết định 01/05/2026 — verify P0 phát hiện MinIO server không chạy, LMS đang dùng filesystem). Schema cột `minio_bucket`/`minio_key` giữ tên legacy nhưng nội dung là **local filesystem path**. Khi nâng cấp MinIO ở Phase 4+, refactor service layer; DB schema không đổi.

```
Storage root: backend/uploads/meeting/

Folder structure (giữ logic giống MinIO bucket):
uploads/meeting/
├── tai-lieu/{cuoc_hop_id}/{uuid}_{filename}        # Module 3
├── xin-phep/{cuoc_hop_id}/{uuid}_{filename}        # Module 5 đính kèm
├── y-kien/{cuoc_hop_id}/{uuid}_{filename}          # Module 7
├── bien-ban/{cuoc_hop_id}/{uuid}_{filename}.pdf    # Module 9 xuất
├── bien-ban/{cuoc_hop_id}/{uuid}_{filename}.docx
├── tien-do/{ket_luan_id}/{uuid}_{filename}         # Module 10 minh chứng
└── mau-bieu/{template_id}/{uuid}_{filename}.docx
```

**Pattern access:**
- Lưu vào DB: `minio_bucket = 'meeting'` (constant), `minio_key = 'tai-lieu/{cuoc_hop_id}/{uuid}_{filename}'` (relative path bên trong bucket).
- Đọc file: resolve `<UPLOAD_ROOT>/{minio_key}` → stream qua FastAPI.
- Mã giả: `path = settings.upload_dir / minio_bucket / minio_key`.

**Lifecycle policy đề xuất** (Phase sau, không cần MVP):
- `tai-lieu/`: giữ vĩnh viễn
- `xin-phep/`: giữ 2 năm
- `bien-ban/`: giữ vĩnh viễn (pháp lý)
- `tien-do/`: giữ 2 năm

---

## 8. SEED DATA BAN ĐẦU

### 8.1. Platform roles (chi tiết xem HKG_PLATFORM_ROLES.md §4)

> **Schema thật `public.platform_role`:** `id, ma_role, ten_role, mo_ta, quyen_han(JSONB), is_active, created_at`. Không có cột `module` riêng — encode `{"module": "MEETING"}` vào `quyen_han`.
>
> Seed **6 role static** (CHU_TOA_HOP là dynamic, không seed):

```sql
INSERT INTO public.platform_role (ma_role, ten_role, mo_ta, quyen_han, is_active) VALUES
('THU_KY_HOP',     'Thư ký cuộc họp',     'Ghi biên bản, hỗ trợ điều hành',  '{"module":"MEETING","type":"static","scoped":true}'::jsonb,  TRUE),
('CHANH_VP',       'Chánh Văn phòng',     'Xem toàn bộ cuộc họp Chi cục',    '{"module":"MEETING","type":"static"}'::jsonb,                TRUE),
('TRUONG_CNTT',    'Trưởng phòng CNTT',   'Quản trị + xem toàn bộ',          '{"module":"MEETING","type":"static"}'::jsonb,                TRUE),
('DANG_VIEN',      'Đảng viên',           'Tham dự họp Đảng',                '{"module":"MEETING","type":"static"}'::jsonb,                TRUE),
('BI_THU_CHI_BO',  'Bí thư Chi bộ',       'Chủ trì họp Chi bộ',              '{"module":"MEETING","type":"static","scoped":true}'::jsonb,  TRUE),
('PHO_BI_THU',     'Phó Bí thư Chi bộ',   'Hỗ trợ họp Chi bộ',               '{"module":"MEETING","type":"static","scoped":true}'::jsonb,  TRUE)
ON CONFLICT (ma_role) DO NOTHING;
```

**Filter HKG roles:** `WHERE quyen_han->>'module' = 'MEETING'`.

### 8.2. Template biên bản mặc định (MVP: 1 template chung)

Upload 1 file template `bien_ban_chung.docx` lên MinIO + insert vào `meeting.mau_bieu`:
```sql
INSERT INTO meeting.mau_bieu (loai, ten_mau, ap_dung_cho, minio_key, la_mac_dinh, created_by)
VALUES ('BIEN_BAN', 'Biên bản họp chung (MVP)', 'TAT_CA',
        'mau-bieu/{uuid}/bien_ban_chung.docx', TRUE, '{admin_id}');
```

---

## 9. CHECKLIST MIGRATION

```
□ 001_create_meeting_schema.py         — CREATE SCHEMA meeting
□ 002_create_cuoc_hop.py               — Bảng 4.1
□ 003_create_thanh_phan.py             — Bảng 4.2
□ 004_create_tai_lieu.py               — Bảng 4.3
□ 005_create_diem_danh.py              — Bảng 4.4
□ 006_create_xin_phep_vang.py          — Bảng 4.5
□ 007_create_y_kien.py                 — Bảng 4.6
□ 008_create_bien_ban.py               — Bảng 4.7
□ 009_create_ket_luan_tien_do.py       — Bảng 4.8 + 4.9
□ 010_create_mau_bieu.py               — Bảng 4.10
□ 011_seed_platform_roles_meeting.py   — Seed 6 platform roles (CHU_TOA_HOP dynamic)
□ 012_seed_default_template.py         — Insert template mặc định
□ 013_create_minio_bucket_meeting.py   — Tạo bucket MinIO (script Python)
```

**Quy ước đặt tên migration:** `{timestamp}_meeting_{action}.py` để Alembic không xung đột với migration của KPI/LMS.

---

## PHỤ LỤC A — Schema gợi ý cho `common.audit_log` (nếu chưa có)

> **Áp dụng khi:** Pre-flight kiểm tra `SELECT to_regclass('common.audit_log')` trả về NULL.
>
> Migration này **thuộc scope `common_service`**, KHÔNG nằm trong scope HKG. Đặt vào `backend/alembic/versions/common_create_audit_log_YYYYMMDD.py`. Phải chạy **TRƯỚC** migration của HKG.

```sql
CREATE TABLE common.audit_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Phân loại
    module              VARCHAR(20) NOT NULL,
        -- 'KPI', 'LMS', 'FORUM', 'LEGAL', 'PORTAL', 'MEETING', 'HE_THONG'
    hanh_dong           VARCHAR(50) NOT NULL,
        -- 'CREATE_MEETING', 'UPLOAD_DOC', 'CHECKIN_QR', 'SIGN_MINUTES', ...

    -- Đối tượng tác động
    doi_tuong_loai      VARCHAR(50),
        -- 'cuoc_hop', 'tai_lieu', 'bien_ban', ...
    doi_tuong_id        UUID,

    -- Ai thực hiện
    nguoi_thuc_hien_id  UUID NOT NULL REFERENCES public.cong_chuc(id),

    -- Metadata request
    ip_address          INET,
    user_agent          TEXT,
    chi_tiet            JSONB,
        -- { "old_value": {...}, "new_value": {...}, "context": {...} }

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_log_module       ON common.audit_log(module);
CREATE INDEX idx_audit_log_doi_tuong    ON common.audit_log(doi_tuong_loai, doi_tuong_id);
CREATE INDEX idx_audit_log_nguoi        ON common.audit_log(nguoi_thuc_hien_id);
CREATE INDEX idx_audit_log_thoi_gian    ON common.audit_log(created_at DESC);
CREATE INDEX idx_audit_log_module_time  ON common.audit_log(module, created_at DESC);
```

**Sử dụng từ HKG (mẫu insert đã chỉnh khớp với phụ lục):**

```sql
INSERT INTO common.audit_log
    (module, hanh_dong, doi_tuong_loai, doi_tuong_id, nguoi_thuc_hien_id, chi_tiet)
VALUES (
    'MEETING',
    'CREATE_MEETING',
    'cuoc_hop',
    '{cuoc_hop_id}',
    '{user_id}',
    '{"tieu_de": "...", "khoi": "CHUYEN_MON"}'::jsonb
);
```

**Quan hệ với `app/models/audit_log.py` (KPI):**
- KPI audit_log dùng cho DML triggers (INSERT/UPDATE/DELETE row-level), giữ nguyên không đổi.
- `common.audit_log` dùng cho audit nghiệp vụ đa module (LOGIN, EXPORT, SIGN, ...).
- Hai bảng tồn tại độc lập, không hợp nhất.

---

*File này được sử dụng làm authoritative reference khi sinh migration. Khi cần thêm bảng mới, cập nhật file này TRƯỚC.*
