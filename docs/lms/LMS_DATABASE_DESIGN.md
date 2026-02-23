# DATABASE DESIGN — MODULE LMS (ĐÀO TẠO TRỰC TUYẾN)
## Schema: `lms` | Database: `kpi_haiquan` | PostgreSQL 15

> **Phiên bản:** 1.0 | **Ngày:** 18/02/2026
> **Trích từ:** CHIEN_LUOC_NEN_TANG_THONG_NHAT.md — Mục 3.2

---

## 1. TỔNG QUAN

| Thông tin | Giá trị |
|-----------|---------|
| **Schema** | `lms` |
| **Số bảng** | 11 |
| **Backend port** | 8001 |
| **FK chính** | `public.cong_chuc(id)` |

### Danh sách bảng

| # | Bảng | Mục đích |
|---|------|----------|
| 1 | `lms.chuyen_de` | Chuyên đề đào tạo |
| 2 | `lms.khoa_hoc` | Khóa học |
| 3 | `lms.bai_hoc` | Bài học / nội dung khóa |
| 4 | `lms.cau_hoi` | Ngân hàng câu hỏi |
| 5 | `lms.bai_kiem_tra` | Bài kiểm tra |
| 6 | `lms.bai_kiem_tra_cau_hoi` | Liên kết BKT ↔ Câu hỏi |
| 7 | `lms.dang_ky_khoa_hoc` | Đăng ký / Giao khóa học |
| 8 | `lms.tien_do_bai_hoc` | Tiến độ học từng bài |
| 9 | `lms.ket_qua_bai_kiem_tra` | Kết quả làm bài |
| 10 | `lms.chung_chi` | Chứng chỉ / Chứng nhận |
| 11 | `lms.khao_sat` | Khảo sát sau khóa học |

### ERD tóm tắt

```
chuyen_de ──1:N──► khoa_hoc ──1:N──► bai_hoc
                       │
                       ├──1:N──► bai_kiem_tra ──N:N──► cau_hoi
                       │              │
                       │              └──1:N──► ket_qua_bai_kiem_tra ──► cong_chuc
                       │
                       ├──1:N──► dang_ky_khoa_hoc ──► cong_chuc
                       │
                       └──1:N──► chung_chi ──► cong_chuc

tien_do_bai_hoc ──► bai_hoc + cong_chuc
khao_sat ──► khoa_hoc + cong_chuc
```

---

## 2. KHỞI TẠO SCHEMA

```sql
CREATE SCHEMA IF NOT EXISTS lms;
GRANT ALL ON SCHEMA lms TO kpi_user;
```

---

## 3. CHI TIẾT CÁC BẢNG

### 3.1. `lms.chuyen_de` — Chuyên đề đào tạo

```sql
CREATE TABLE lms.chuyen_de (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ma_chuyen_de VARCHAR(50) NOT NULL UNIQUE,
    ten_chuyen_de VARCHAR(200) NOT NULL,
    mo_ta TEXT,
    anh_dai_dien TEXT,
    thu_tu INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES public.cong_chuc(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2. `lms.khoa_hoc` — Khóa học

```sql
CREATE TABLE lms.khoa_hoc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ma_khoa_hoc VARCHAR(50) NOT NULL UNIQUE,
    ten_khoa_hoc VARCHAR(300) NOT NULL,
    mo_ta TEXT,
    chuyen_de_id UUID REFERENCES lms.chuyen_de(id),

    -- Loại khóa học
    loai VARCHAR(50) NOT NULL DEFAULT 'TU_HOC',
        -- 'TU_HOC': Tự học theo nhu cầu
        -- 'BAT_BUOC': Bắt buộc hoàn thành
        -- 'TRUC_TUYEN': Lớp học trực tuyến
        -- 'KET_HOP': Kết hợp online + offline

    -- Nội dung
    anh_dai_dien TEXT,
    thoi_luong_phut INTEGER,          -- Tổng thời lượng ước tính
    so_bai_hoc INTEGER DEFAULT 0,

    -- Điều kiện
    dieu_kien_tien_quyet JSONB,       -- IDs khóa học phải hoàn thành trước
        -- VD: ["uuid-khoa-hoc-1", "uuid-khoa-hoc-2"]
    diem_dat_yeu_cau DECIMAL(5,2) DEFAULT 70.00,

    -- Thời gian
    ngay_bat_dau DATE,
    ngay_ket_thuc DATE,

    -- Giảng viên
    giang_vien_id UUID REFERENCES public.cong_chuc(id),

    -- Trạng thái & Workflow
    trang_thai VARCHAR(50) DEFAULT 'NHAP',
        -- 'NHAP': Đang soạn
        -- 'CHO_DUYET': Chờ QT đào tạo duyệt
        -- 'DA_XUAT_BAN': Đã mở cho học viên
        -- 'TAM_DUNG': Tạm dừng
        -- 'DA_DONG': Đã kết thúc
    nguoi_duyet_id UUID REFERENCES public.cong_chuc(id),
    ngay_duyet TIMESTAMP,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.3. `lms.bai_hoc` — Bài học (nội dung khóa học)

```sql
CREATE TABLE lms.bai_hoc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    khoa_hoc_id UUID NOT NULL REFERENCES lms.khoa_hoc(id),
    thu_tu INTEGER NOT NULL,
    tieu_de VARCHAR(300) NOT NULL,

    -- Loại nội dung
    loai_noi_dung VARCHAR(50) NOT NULL,
        -- 'VIDEO', 'PDF', 'SLIDE', 'HTML', 'SCORM', 'QUIZ'

    -- Nội dung
    noi_dung TEXT,                    -- HTML content hoặc mô tả
    file_url TEXT,                    -- URL file trên MinIO (video, PDF, slide)
    file_size_mb DECIMAL(10,2),
    thoi_luong_phut INTEGER,

    -- Điều kiện hoàn thành
    phai_xem_het BOOLEAN DEFAULT TRUE,
    thoi_gian_toi_thieu_giay INTEGER, -- Thời gian tối thiểu phải xem

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.4. `lms.cau_hoi` — Ngân hàng câu hỏi

```sql
CREATE TABLE lms.cau_hoi (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    khoa_hoc_id UUID REFERENCES lms.khoa_hoc(id),
    chuyen_de_id UUID REFERENCES lms.chuyen_de(id),

    -- Nội dung câu hỏi
    noi_dung TEXT NOT NULL,           -- Hỗ trợ HTML/Markdown
    loai VARCHAR(50) NOT NULL,
        -- 'TRAC_NGHIEM_1': Chọn 1 đáp án đúng
        -- 'TRAC_NGHIEM_NHIEU': Chọn nhiều đáp án
        -- 'DUNG_SAI': Đúng hoặc Sai
        -- 'TU_LUAN': Tự luận (chấm tay)
        -- 'GHEP_DOI': Ghép đôi

    -- Đáp án (JSONB linh hoạt theo loại)
    dap_an JSONB NOT NULL,
        -- TRAC_NGHIEM_1: {"options": ["A...", "B...", "C...", "D..."], "correct": [0], "explanation": "..."}
        -- TRAC_NGHIEM_NHIEU: {"options": [...], "correct": [0, 2], "explanation": "..."}
        -- DUNG_SAI: {"correct": true, "explanation": "..."}
        -- GHEP_DOI: {"left": [...], "right": [...], "pairs": [[0,2],[1,0]]}

    diem DECIMAL(5,2) DEFAULT 1.0,
    do_kho VARCHAR(20) DEFAULT 'TRUNG_BINH',
        -- 'DE', 'TRUNG_BINH', 'KHO'

    -- Liên kết văn bản pháp luật (cross-module reference)
    van_ban_lien_quan_ids JSONB,      -- IDs từ legal.van_ban

    nguoi_tao_id UUID REFERENCES public.cong_chuc(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.5. `lms.bai_kiem_tra` — Bài kiểm tra

```sql
CREATE TABLE lms.bai_kiem_tra (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    khoa_hoc_id UUID REFERENCES lms.khoa_hoc(id),
    tieu_de VARCHAR(300) NOT NULL,
    mo_ta TEXT,

    -- Cấu hình đề thi
    so_cau_hoi INTEGER NOT NULL,
    thoi_gian_lam_bai_phut INTEGER,   -- NULL = không giới hạn
    so_lan_lam_toi_da INTEGER DEFAULT 3,
    diem_dat DECIMAL(5,2) DEFAULT 70.00,
    tron_de BOOLEAN DEFAULT TRUE,     -- Random thứ tự câu hỏi
    tron_dap_an BOOLEAN DEFAULT TRUE, -- Random thứ tự đáp án

    -- Thời gian mở
    ngay_mo DATE,
    ngay_dong DATE,

    nguoi_tao_id UUID REFERENCES public.cong_chuc(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.6. `lms.bai_kiem_tra_cau_hoi` — Liên kết BKT ↔ Câu hỏi

```sql
CREATE TABLE lms.bai_kiem_tra_cau_hoi (
    bai_kiem_tra_id UUID NOT NULL REFERENCES lms.bai_kiem_tra(id),
    cau_hoi_id UUID NOT NULL REFERENCES lms.cau_hoi(id),
    thu_tu INTEGER,
    PRIMARY KEY (bai_kiem_tra_id, cau_hoi_id)
);
```

### 3.7. `lms.dang_ky_khoa_hoc` — Đăng ký / Giao khóa học

```sql
CREATE TABLE lms.dang_ky_khoa_hoc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cong_chuc_id UUID NOT NULL REFERENCES public.cong_chuc(id),
    khoa_hoc_id UUID NOT NULL REFERENCES lms.khoa_hoc(id),

    -- Loại đăng ký
    loai_dang_ky VARCHAR(50) DEFAULT 'TU_NGUYEN',
        -- 'TU_NGUYEN': CBCC tự đăng ký
        -- 'BAT_BUOC': QT đào tạo giao
        -- 'GIAO_VIEC': Lãnh đạo giao

    nguoi_giao_id UUID REFERENCES public.cong_chuc(id),
    han_hoan_thanh DATE,

    -- Tiến độ
    trang_thai VARCHAR(50) DEFAULT 'CHUA_BAT_DAU',
        -- 'CHUA_BAT_DAU', 'DANG_HOC', 'HOAN_THANH', 'KHONG_DAT', 'QUA_HAN'
    phan_tram_hoan_thanh DECIMAL(5,2) DEFAULT 0,
    ngay_bat_dau_hoc TIMESTAMP,
    ngay_hoan_thanh TIMESTAMP,

    -- Kết quả
    diem_cao_nhat DECIMAL(5,2),
    so_lan_lam_bai INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (cong_chuc_id, khoa_hoc_id)
);
```

### 3.8. `lms.tien_do_bai_hoc` — Tiến độ học từng bài

```sql
CREATE TABLE lms.tien_do_bai_hoc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cong_chuc_id UUID NOT NULL REFERENCES public.cong_chuc(id),
    bai_hoc_id UUID NOT NULL REFERENCES lms.bai_hoc(id),

    trang_thai VARCHAR(50) DEFAULT 'CHUA_XEM',
        -- 'CHUA_XEM', 'DANG_XEM', 'DA_HOAN_THANH'
    thoi_gian_xem_giay INTEGER DEFAULT 0,
    lan_xem_cuoi TIMESTAMP,
    ngay_hoan_thanh TIMESTAMP,

    UNIQUE (cong_chuc_id, bai_hoc_id)
);
```

### 3.9. `lms.ket_qua_bai_kiem_tra` — Kết quả làm bài

```sql
CREATE TABLE lms.ket_qua_bai_kiem_tra (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cong_chuc_id UUID NOT NULL REFERENCES public.cong_chuc(id),
    bai_kiem_tra_id UUID NOT NULL REFERENCES lms.bai_kiem_tra(id),

    lan_thu INTEGER NOT NULL DEFAULT 1,

    -- Kết quả
    diem DECIMAL(5,2),
    so_cau_dung INTEGER,
    so_cau_sai INTEGER,
    thoi_gian_lam_giay INTEGER,

    chi_tiet_tra_loi JSONB,
        -- [{"cau_hoi_id": "uuid", "tra_loi": [1], "dung": true, "diem": 1.0}, ...]

    dat_yeu_cau BOOLEAN,
    ngay_lam TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.10. `lms.chung_chi` — Chứng chỉ / Chứng nhận hoàn thành

```sql
CREATE TABLE lms.chung_chi (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cong_chuc_id UUID NOT NULL REFERENCES public.cong_chuc(id),
    khoa_hoc_id UUID NOT NULL REFERENCES lms.khoa_hoc(id),

    ma_chung_chi VARCHAR(50) NOT NULL UNIQUE,
    ten_chung_chi VARCHAR(300),
    diem_dat DECIMAL(5,2),
    ngay_cap TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    nguoi_cap_id UUID REFERENCES public.cong_chuc(id),
    file_url TEXT,                    -- URL file chứng chỉ (PDF) trên MinIO

    UNIQUE (cong_chuc_id, khoa_hoc_id)
);
```

### 3.11. `lms.khao_sat` — Khảo sát sau khóa học

```sql
CREATE TABLE lms.khao_sat (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    khoa_hoc_id UUID NOT NULL REFERENCES lms.khoa_hoc(id),
    cong_chuc_id UUID NOT NULL REFERENCES public.cong_chuc(id),

    noi_dung JSONB NOT NULL,
        -- {"rating": 4, "feedback": "Khóa học rất hữu ích", "questions": [
        --   {"q": "Nội dung phù hợp?", "score": 5},
        --   {"q": "Giảng viên tốt?", "score": 4}
        -- ]}

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (cong_chuc_id, khoa_hoc_id)
);
```

---

## 4. INDEXES

```sql
CREATE INDEX idx_lms_kh_chuyen_de ON lms.khoa_hoc(chuyen_de_id);
CREATE INDEX idx_lms_kh_giang_vien ON lms.khoa_hoc(giang_vien_id);
CREATE INDEX idx_lms_kh_trang_thai ON lms.khoa_hoc(trang_thai);
CREATE INDEX idx_lms_bh_khoa_hoc ON lms.bai_hoc(khoa_hoc_id);
CREATE INDEX idx_lms_ch_khoa_hoc ON lms.cau_hoi(khoa_hoc_id);
CREATE INDEX idx_lms_dkkh_cc ON lms.dang_ky_khoa_hoc(cong_chuc_id);
CREATE INDEX idx_lms_dkkh_kh ON lms.dang_ky_khoa_hoc(khoa_hoc_id);
CREATE INDEX idx_lms_dkkh_tt ON lms.dang_ky_khoa_hoc(trang_thai);
CREATE INDEX idx_lms_kqbkt_cc ON lms.ket_qua_bai_kiem_tra(cong_chuc_id);
CREATE INDEX idx_lms_kqbkt_bkt ON lms.ket_qua_bai_kiem_tra(bai_kiem_tra_id);
CREATE INDEX idx_lms_tdbh_cc ON lms.tien_do_bai_hoc(cong_chuc_id);
CREATE INDEX idx_lms_tdbh_bh ON lms.tien_do_bai_hoc(bai_hoc_id);
```

---

## 5. FULL-TEXT SEARCH

```sql
ALTER TABLE lms.khoa_hoc ADD COLUMN search_vector tsvector;

CREATE OR REPLACE FUNCTION lms.update_khoa_hoc_search()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('simple',
        COALESCE(NEW.ten_khoa_hoc, '') || ' ' || COALESCE(NEW.mo_ta, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_lms_khoa_hoc_search
    BEFORE INSERT OR UPDATE ON lms.khoa_hoc
    FOR EACH ROW EXECUTE FUNCTION lms.update_khoa_hoc_search();

CREATE INDEX idx_lms_kh_search ON lms.khoa_hoc USING GIN (search_vector);
```

---

## 6. MIGRATION SCRIPT (Alembic)

```python
"""create lms schema and tables

Revision ID: lms_001
"""

def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS lms")
    op.execute("GRANT ALL ON SCHEMA lms TO kpi_user")
    # Tạo từng bảng theo thứ tự dependency
    # chuyen_de → khoa_hoc → bai_hoc → cau_hoi → ...

def downgrade():
    op.execute("DROP SCHEMA lms CASCADE")
```

> ⚠️ **KHÔNG tự chạy migration trên production.** Gửi script cho Tech Lead (HUB project) review và chạy.
