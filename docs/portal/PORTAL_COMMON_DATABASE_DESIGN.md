# DATABASE DESIGN — MODULE PORTAL & COMMON
## Schema: `portal` + `common` | Database: `kpi_haiquan` | PostgreSQL 15

> **Phiên bản:** 1.0 | **Ngày:** 18/02/2026
> **Trích từ:** CHIEN_LUOC_NEN_TANG_THONG_NHAT.md — Mục 3.5 + 3.6

---

## 1. TỔNG QUAN

| Thông tin | Giá trị |
|-----------|---------|
| **Schema** | `portal` + `common` |
| **Số bảng** | 4 (portal) + 4 (common) = 8 |
| **FK chính** | `public.cong_chuc(id)` |

### Danh sách bảng

| # | Schema | Bảng | Mục đích |
|---|--------|------|----------|
| 1 | portal | `chuyen_muc` | Chuyên mục tin tức/CMS |
| 2 | portal | `bai_viet` | Tin tức / Bài viết |
| 3 | portal | `thu_muc` | Thư mục tài liệu ECM |
| 4 | portal | `tai_lieu` | Tài liệu ECM (versioning) |
| 5 | common | `thong_bao` | Notification center |
| 6 | common | `file_storage` | Metadata file trên MinIO |
| 7 | common | `knowledge_base` | Kho SOP / FAQ |
| 8 | common | `kpi_integration_log` | Dữ liệu tích hợp KPI ← module mới |

---

## 2. KHỞI TẠO SCHEMA

```sql
CREATE SCHEMA IF NOT EXISTS portal;
CREATE SCHEMA IF NOT EXISTS common;
GRANT ALL ON SCHEMA portal, common TO kpi_user;
```

---

## 3. SCHEMA PORTAL — Trang chủ / CMS / ECM

### 3.1. `portal.chuyen_muc` — Chuyên mục tin tức

```sql
CREATE TABLE portal.chuyen_muc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ten VARCHAR(200) NOT NULL,
    slug VARCHAR(200) NOT NULL UNIQUE,     -- URL-friendly: "tin-chi-dao"
    mo_ta TEXT,
    thu_tu INTEGER DEFAULT 0,
    loai VARCHAR(50) DEFAULT 'TIN_TUC',
        -- 'TIN_TUC': Tin tức chung
        -- 'CHI_DAO': Tin chỉ đạo điều hành
        -- 'THONG_BAO': Thông báo nội bộ
        -- 'LEGAL_UPDATE': Cập nhật pháp luật (link sang module Legal)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO portal.chuyen_muc (ten, slug, loai, thu_tu) VALUES
('Tin chỉ đạo', 'tin-chi-dao', 'CHI_DAO', 1),
('Thông báo', 'thong-bao', 'THONG_BAO', 2),
('Tin hoạt động', 'tin-hoat-dong', 'TIN_TUC', 3),
('Cập nhật pháp luật', 'cap-nhat-phap-luat', 'LEGAL_UPDATE', 4);
```

### 3.2. `portal.bai_viet` — Tin tức / Bài viết

```sql
CREATE TABLE portal.bai_viet (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chuyen_muc_id UUID REFERENCES portal.chuyen_muc(id),

    tieu_de VARCHAR(500) NOT NULL,
    tom_tat TEXT,
    noi_dung TEXT NOT NULL,               -- HTML content (WYSIWYG editor)
    anh_dai_dien TEXT,                    -- URL ảnh đại diện

    -- Workflow duyệt: NHAP → KIEM_TRA → DUYET → XUAT_BAN
    trang_thai VARCHAR(50) DEFAULT 'NHAP',
        -- 'NHAP': Biên tập đang soạn
        -- 'KIEM_TRA': Chờ kiểm tra nội dung
        -- 'DUYET': Chờ lãnh đạo duyệt đăng
        -- 'XUAT_BAN': Đã xuất bản
        -- 'THU_HOI': Đã thu hồi

    nguoi_soan_id UUID REFERENCES public.cong_chuc(id),
    nguoi_kiem_tra_id UUID REFERENCES public.cong_chuc(id),
    nguoi_duyet_id UUID REFERENCES public.cong_chuc(id),

    ngay_xuat_ban TIMESTAMP,
    is_ghim BOOLEAN DEFAULT FALSE,        -- Ghim lên đầu
    so_luot_xem INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);
```

### 3.3. `portal.thu_muc` — Thư mục tài liệu

```sql
CREATE TABLE portal.thu_muc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ten VARCHAR(200) NOT NULL,
    parent_id UUID REFERENCES portal.thu_muc(id),  -- Phân cấp thư mục
    thu_tu INTEGER DEFAULT 0,

    -- Phân quyền truy cập
    quyen_truy_cap VARCHAR(50) DEFAULT 'TAT_CA',
        -- 'TAT_CA': Tất cả CBCC
        -- 'LANH_DAO': Chỉ lãnh đạo
        -- 'DON_VI': Chỉ đơn vị chỉ định
    don_vi_ids JSONB,                      -- Nếu quyền = 'DON_VI'

    created_by UUID REFERENCES public.cong_chuc(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO portal.thu_muc (ten, thu_tu) VALUES
('Văn bản nội bộ', 1),
('Tài liệu đào tạo', 2),
('Biểu mẫu', 3),
('Quy trình nghiệp vụ', 4),
('Tài liệu tham khảo', 5);
```

### 3.4. `portal.tai_lieu` — Tài liệu ECM

```sql
CREATE TABLE portal.tai_lieu (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ten_tai_lieu VARCHAR(300) NOT NULL,
    mo_ta TEXT,
    thu_muc_id UUID REFERENCES portal.thu_muc(id),

    -- File
    file_url TEXT NOT NULL,                -- URL trên MinIO/S3
    file_name VARCHAR(300),
    file_size_bytes BIGINT,
    file_type VARCHAR(50),
        -- 'PDF', 'DOCX', 'XLSX', 'PPTX', 'ZIP', 'IMAGE', 'OTHER'

    -- Versioning
    phien_ban INTEGER DEFAULT 1,
    phien_ban_truoc_id UUID REFERENCES portal.tai_lieu(id),

    -- Phân loại
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',

    -- Phân quyền (kế thừa từ thư mục, hoặc override)
    quyen_truy_cap VARCHAR(50) DEFAULT 'TAT_CA',
    don_vi_ids JSONB,

    nguoi_tai_len_id UUID REFERENCES public.cong_chuc(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);
```

---

## 4. SCHEMA COMMON — Dịch vụ dùng chung

### 4.1. `common.thong_bao` — Notification Center

```sql
CREATE TABLE common.thong_bao (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Người nhận
    nguoi_nhan_id UUID NOT NULL REFERENCES public.cong_chuc(id),

    -- Nội dung
    tieu_de VARCHAR(300) NOT NULL,
    noi_dung TEXT,
    loai VARCHAR(50) NOT NULL,
        -- 'KPI': Từ module KPI
        -- 'LMS': Từ module Đào tạo
        -- 'FORUM': Từ module Diễn đàn
        -- 'LEGAL': Từ module Pháp luật
        -- 'PORTAL': Từ module Portal
        -- 'HE_THONG': Thông báo hệ thống

    -- Liên kết (click để chuyển đến)
    link_url TEXT,
    doi_tuong_type VARCHAR(50),
        -- 'KHOA_HOC', 'BAI_KIEM_TRA', 'CHU_DE', 'TRA_LOI', 'VAN_BAN', 'BAI_VIET', ...
    doi_tuong_id UUID,

    -- Trạng thái
    da_doc BOOLEAN DEFAULT FALSE,
    ngay_doc TIMESTAMP,

    -- Mức độ
    muc_do VARCHAR(20) DEFAULT 'BINH_THUONG',
        -- 'KHAN': Hiển thị nổi bật, gửi email
        -- 'QUAN_TRONG': Hiển thị nổi bật
        -- 'BINH_THUONG': Bình thường

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2. `common.file_storage` — Metadata file trên MinIO

```sql
CREATE TABLE common.file_storage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    file_name VARCHAR(500) NOT NULL,
    file_path TEXT NOT NULL,              -- Path trên MinIO: "lms/videos/uuid.mp4"
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),

    -- Nguồn gốc
    module VARCHAR(50) NOT NULL,
        -- 'LMS', 'FORUM', 'LEGAL', 'PORTAL'
    doi_tuong_type VARCHAR(50),           -- 'BAI_HOC', 'CHU_DE', 'VAN_BAN', 'BAI_VIET'
    doi_tuong_id UUID,

    nguoi_tai_len_id UUID REFERENCES public.cong_chuc(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);
```

### 4.3. `common.knowledge_base` — Kho SOP / FAQ

```sql
CREATE TABLE common.knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    loai VARCHAR(20) NOT NULL,
        -- 'SOP': Quy trình thao tác chuẩn
        -- 'FAQ': Câu hỏi thường gặp

    tieu_de VARCHAR(500) NOT NULL,
    noi_dung TEXT NOT NULL,               -- HTML/Markdown

    -- Phân loại
    chuyen_de JSONB DEFAULT '[]',
    tags JSONB DEFAULT '[]',

    -- Chủ sở hữu (chuyên gia phụ trách)
    chu_so_huu_id UUID REFERENCES public.cong_chuc(id),

    trang_thai VARCHAR(50) DEFAULT 'NHAP',
        -- 'NHAP': Đang soạn
        -- 'CHO_DUYET': Chờ duyệt
        -- 'DA_XUAT_BAN': Đã công bố
        -- 'CAN_CAP_NHAT': Cần cập nhật (VB liên quan thay đổi)

    -- Liên kết chéo cross-module
    van_ban_lien_quan JSONB,              -- IDs legal.van_ban
    chu_de_forum_lien_quan JSONB,         -- IDs forum.chu_de

    -- Versioning
    phien_ban INTEGER DEFAULT 1,
    ngay_cap_nhat_cuoi TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);
```

### 4.4. `common.kpi_integration_log` — Tích hợp dữ liệu ← Module mới → KPI

> ⭐ **Bảng quan trọng nhất cho tích hợp:** Mỗi module ghi metrics vào đây, Dashboard lãnh đạo đọc từ đây.

```sql
CREATE TABLE common.kpi_integration_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cong_chuc_id UUID NOT NULL REFERENCES public.cong_chuc(id),
    thang INTEGER NOT NULL CHECK (thang BETWEEN 1 AND 12),
    nam INTEGER NOT NULL CHECK (nam >= 2025),

    -- Nguồn dữ liệu
    module VARCHAR(50) NOT NULL,
        -- 'LMS', 'FORUM', 'LEGAL'

    -- Metrics (JSONB linh hoạt theo module)
    metrics JSONB NOT NULL,
        -- LMS: {
        --   "khoa_hoc_hoan_thanh": 3,
        --   "khoa_hoc_dang_hoc": 1,
        --   "diem_trung_binh": 85.5,
        --   "chung_chi_dat": 2,
        --   "tong_thoi_gian_hoc_phut": 480
        -- }
        -- FORUM: {
        --   "bai_dang": 5,
        --   "tra_loi": 12,
        --   "upvote_nhan_duoc": 30,
        --   "bai_ghim": 2,
        --   "dap_an_chuan": 1
        -- }
        -- LEGAL: {
        --   "vb_da_doc": 8,
        --   "vb_chua_doc": 2,
        --   "vb_qua_han": 0,
        --   "quiz_hoan_thanh": 3,
        --   "quiz_diem_tb": 90.0
        -- }

    -- Điểm quy đổi (tùy cấu hình nền tảng)
    diem_quy_doi DECIMAL(5,2),

    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (cong_chuc_id, thang, nam, module)
);
```

---

## 5. INDEXES

```sql
-- Portal
CREATE INDEX idx_portal_bv_cm ON portal.bai_viet(chuyen_muc_id);
CREATE INDEX idx_portal_bv_tt ON portal.bai_viet(trang_thai);
CREATE INDEX idx_portal_bv_xb ON portal.bai_viet(ngay_xuat_ban DESC);
CREATE INDEX idx_portal_tl_tm ON portal.tai_lieu(thu_muc_id);
CREATE INDEX idx_portal_tl_tags ON portal.tai_lieu USING GIN (tags);

-- Common
CREATE INDEX idx_common_tb_nn ON common.thong_bao(nguoi_nhan_id);
CREATE INDEX idx_common_tb_chua_doc ON common.thong_bao(da_doc) WHERE da_doc = FALSE;
CREATE INDEX idx_common_tb_loai ON common.thong_bao(loai);
CREATE INDEX idx_common_tb_time ON common.thong_bao(created_at DESC);
CREATE INDEX idx_common_fs_module ON common.file_storage(module, doi_tuong_type, doi_tuong_id);
CREATE INDEX idx_common_kb_loai ON common.knowledge_base(loai);
CREATE INDEX idx_common_kb_tags ON common.knowledge_base USING GIN (tags);
CREATE INDEX idx_common_kb_tt ON common.knowledge_base(trang_thai);
CREATE INDEX idx_common_kpi_cc ON common.kpi_integration_log(cong_chuc_id, thang, nam);
CREATE INDEX idx_common_kpi_module ON common.kpi_integration_log(module);
```

---

## 6. FULL-TEXT SEARCH

```sql
ALTER TABLE common.knowledge_base ADD COLUMN search_vector tsvector;

CREATE OR REPLACE FUNCTION common.update_kb_search()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('simple',
        COALESCE(NEW.tieu_de, '') || ' ' || COALESCE(NEW.noi_dung, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_common_kb_search
    BEFORE INSERT OR UPDATE ON common.knowledge_base
    FOR EACH ROW EXECUTE FUNCTION common.update_kb_search();

CREATE INDEX idx_common_kb_search ON common.knowledge_base USING GIN (search_vector);
```
