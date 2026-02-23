# DATABASE DESIGN — MODULE LEGAL (PHỔ BIẾN PHÁP LUẬT)
## Schema: `legal` | Database: `kpi_haiquan` | PostgreSQL 15

> **Phiên bản:** 1.0 | **Ngày:** 18/02/2026
> **Trích từ:** CHIEN_LUOC_NEN_TANG_THONG_NHAT.md — Mục 3.4

---

## 1. TỔNG QUAN

| Thông tin | Giá trị |
|-----------|---------|
| **Schema** | `legal` |
| **Số bảng** | 6 |
| **Backend port** | 8003 |
| **FK chính** | `public.cong_chuc(id)` |

### Danh sách bảng

| # | Bảng | Mục đích |
|---|------|----------|
| 1 | `legal.loai_van_ban` | Danh mục loại văn bản |
| 2 | `legal.van_ban` | Kho văn bản pháp luật |
| 3 | `legal.van_ban_lien_ket` | Liên kết giữa các văn bản |
| 4 | `legal.xac_nhan_doc` | Xác nhận đã đọc |
| 5 | `legal.quiz_van_ban` | Quiz kiến thức pháp luật |
| 6 | `legal.ket_qua_quiz` | Kết quả quiz |

### ERD tóm tắt

```
loai_van_ban ──1:N──► van_ban ──1:N──► xac_nhan_doc ──► cong_chuc
                         │
                         ├── van_ban_lien_ket (tự tham chiếu N:N)
                         │
                         └──1:N──► quiz_van_ban ──1:N──► ket_qua_quiz ──► cong_chuc
```

---

## 2. KHỞI TẠO SCHEMA

```sql
CREATE SCHEMA IF NOT EXISTS legal;
GRANT ALL ON SCHEMA legal TO kpi_user;
```

---

## 3. CHI TIẾT CÁC BẢNG

### 3.1. `legal.loai_van_ban` — Danh mục loại văn bản

```sql
CREATE TABLE legal.loai_van_ban (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ma VARCHAR(50) NOT NULL UNIQUE,
    ten VARCHAR(200) NOT NULL,
    thu_tu INTEGER DEFAULT 0
);

INSERT INTO legal.loai_van_ban (ma, ten, thu_tu) VALUES
('LUAT', 'Luật', 1),
('NGHI_DINH', 'Nghị định', 2),
('THONG_TU', 'Thông tư', 3),
('QUYET_DINH', 'Quyết định', 4),
('CONG_VAN', 'Công văn', 5),
('CHI_THI', 'Chỉ thị', 6),
('HUONG_DAN', 'Hướng dẫn', 7),
('NOI_BO', 'Văn bản nội bộ', 8);
```

### 3.2. `legal.van_ban` — Kho văn bản pháp luật

```sql
CREATE TABLE legal.van_ban (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Thông tin văn bản
    so_hieu VARCHAR(100) NOT NULL,            -- VD: "335/2025/NĐ-CP"
    trich_yeu VARCHAR(500) NOT NULL,          -- Trích yếu nội dung
    loai_van_ban_id UUID REFERENCES legal.loai_van_ban(id),

    co_quan_ban_hanh VARCHAR(200),
    ngay_ban_hanh DATE,
    ngay_hieu_luc DATE,
    ngay_het_hieu_luc DATE,                   -- NULL = còn hiệu lực

    -- Hiệu lực
    trang_thai_hieu_luc VARCHAR(50) DEFAULT 'CON_HIEU_LUC',
        -- 'CON_HIEU_LUC': Đang có hiệu lực
        -- 'HET_HIEU_LUC': Đã hết hiệu lực
        -- 'BI_THAY_THE': Bị văn bản khác thay thế
        -- 'DANG_SUA_DOI': Đang trong quá trình sửa đổi

    van_ban_thay_the_id UUID REFERENCES legal.van_ban(id),

    -- Nội dung
    tom_tat TEXT,                              -- Tóm tắt nội dung chính
    noi_dung_html TEXT,                        -- Nội dung đầy đủ (HTML)
    file_goc_url TEXT,                         -- File PDF/Word gốc trên MinIO

    -- Phân loại
    chuyen_de JSONB DEFAULT '[]',
        -- VD: ["thuế XNK", "giám sát", "KTSTQ"]
    doi_tuong_ap_dung JSONB DEFAULT '[]',
        -- VD: ["Đội thủ tục", "Đội KTSTQ"] hoặc ["TAT_CA"]
    tags JSONB DEFAULT '[]',

    -- ⭐ ĐIỂM MỚI QUY ĐỊNH (tính năng đặc thù)
    diem_moi TEXT,                             -- Nội dung điểm mới so với VB cũ
    viec_can_lam TEXT,                         -- Việc CBCC cần làm sau khi đọc

    -- Mức độ quan trọng
    muc_do VARCHAR(50) DEFAULT 'BINH_THUONG',
        -- 'KHAN': Khẩn (cần đọc trong 24h)
        -- 'QUAN_TRONG': Quan trọng (cần đọc trong 3 ngày)
        -- 'BINH_THUONG': Bình thường
    bat_buoc_doc BOOLEAN DEFAULT FALSE,
    han_xac_nhan DATE,                         -- Hạn cuối phải xác nhận đã đọc

    -- Workflow duyệt đăng: NHAP → CHO_DUYET → DA_DUYET → DA_XUAT_BAN
    nguoi_nhap_id UUID REFERENCES public.cong_chuc(id),
    nguoi_duyet_id UUID REFERENCES public.cong_chuc(id),
    trang_thai_duyet VARCHAR(50) DEFAULT 'NHAP',
        -- 'NHAP', 'CHO_DUYET', 'DA_DUYET', 'DA_XUAT_BAN'
    ngay_xuat_ban TIMESTAMP,

    -- Versioning
    phien_ban INTEGER DEFAULT 1,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);
```

### 3.3. `legal.van_ban_lien_ket` — Liên kết giữa các văn bản

```sql
CREATE TABLE legal.van_ban_lien_ket (
    van_ban_id UUID NOT NULL REFERENCES legal.van_ban(id),
    van_ban_lien_quan_id UUID NOT NULL REFERENCES legal.van_ban(id),
    loai_lien_ket VARCHAR(50),
        -- 'THAY_THE': VB này thay thế VB kia
        -- 'BO_SUNG': VB này bổ sung VB kia
        -- 'HUONG_DAN': VB này hướng dẫn VB kia
        -- 'LIEN_QUAN': Liên quan chung
    PRIMARY KEY (van_ban_id, van_ban_lien_quan_id)
);
```

### 3.4. `legal.xac_nhan_doc` — Xác nhận đã đọc văn bản

```sql
CREATE TABLE legal.xac_nhan_doc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    van_ban_id UUID NOT NULL REFERENCES legal.van_ban(id),
    cong_chuc_id UUID NOT NULL REFERENCES public.cong_chuc(id),

    da_doc BOOLEAN DEFAULT FALSE,
    ngay_doc TIMESTAMP,
    thoi_gian_doc_giay INTEGER,               -- Thời gian đọc thực tế (tracking)

    da_xac_nhan BOOLEAN DEFAULT FALSE,        -- CBCC xác nhận "đã đọc và hiểu"
    ngay_xac_nhan TIMESTAMP,
    ghi_chu TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (van_ban_id, cong_chuc_id)
);
```

### 3.5. `legal.quiz_van_ban` — Quiz kiến thức pháp luật

```sql
CREATE TABLE legal.quiz_van_ban (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    van_ban_id UUID NOT NULL REFERENCES legal.van_ban(id),

    tieu_de VARCHAR(300) NOT NULL,
    so_cau_hoi INTEGER NOT NULL,
    thoi_gian_phut INTEGER,                   -- NULL = không giới hạn
    diem_dat DECIMAL(5,2) DEFAULT 70.00,

    -- Câu hỏi nhúng trực tiếp (quiz nhẹ, không cần ngân hàng riêng)
    cau_hoi JSONB NOT NULL,
        -- [
        --   {"noi_dung": "Nghị định 335 có hiệu lực từ ngày nào?",
        --    "dap_an": ["01/01/2025", "01/03/2025", "01/06/2025", "01/09/2025"],
        --    "correct": 1,
        --    "giai_thich": "Theo Điều 45..."},
        --   ...
        -- ]

    nguoi_tao_id UUID REFERENCES public.cong_chuc(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.6. `legal.ket_qua_quiz` — Kết quả quiz

```sql
CREATE TABLE legal.ket_qua_quiz (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID NOT NULL REFERENCES legal.quiz_van_ban(id),
    cong_chuc_id UUID NOT NULL REFERENCES public.cong_chuc(id),

    diem DECIMAL(5,2),
    so_cau_dung INTEGER,
    dat_yeu_cau BOOLEAN,
    chi_tiet JSONB,
        -- [{"cau": 0, "tra_loi": 2, "dung": false}, ...]

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. INDEXES

```sql
CREATE INDEX idx_legal_vb_so_hieu ON legal.van_ban(so_hieu);
CREATE INDEX idx_legal_vb_loai ON legal.van_ban(loai_van_ban_id);
CREATE INDEX idx_legal_vb_hieu_luc ON legal.van_ban(trang_thai_hieu_luc);
CREATE INDEX idx_legal_vb_duyet ON legal.van_ban(trang_thai_duyet);
CREATE INDEX idx_legal_vb_muc_do ON legal.van_ban(muc_do);
CREATE INDEX idx_legal_vb_tags ON legal.van_ban USING GIN (tags);
CREATE INDEX idx_legal_vb_chuyen_de ON legal.van_ban USING GIN (chuyen_de);
CREATE INDEX idx_legal_xnd_vb ON legal.xac_nhan_doc(van_ban_id);
CREATE INDEX idx_legal_xnd_cc ON legal.xac_nhan_doc(cong_chuc_id);
CREATE INDEX idx_legal_xnd_chua_doc ON legal.xac_nhan_doc(da_doc) WHERE da_doc = FALSE;
CREATE INDEX idx_legal_kqq_quiz ON legal.ket_qua_quiz(quiz_id);
CREATE INDEX idx_legal_kqq_cc ON legal.ket_qua_quiz(cong_chuc_id);
```

---

## 5. FULL-TEXT SEARCH

```sql
ALTER TABLE legal.van_ban ADD COLUMN search_vector tsvector;

CREATE OR REPLACE FUNCTION legal.update_van_ban_search()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('simple',
        COALESCE(NEW.so_hieu, '') || ' ' ||
        COALESCE(NEW.trich_yeu, '') || ' ' ||
        COALESCE(NEW.tom_tat, '') || ' ' ||
        COALESCE(NEW.diem_moi, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_legal_van_ban_search
    BEFORE INSERT OR UPDATE ON legal.van_ban
    FOR EACH ROW EXECUTE FUNCTION legal.update_van_ban_search();

CREATE INDEX idx_legal_vb_search ON legal.van_ban USING GIN (search_vector);
```
