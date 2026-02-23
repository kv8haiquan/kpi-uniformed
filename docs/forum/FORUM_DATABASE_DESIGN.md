# DATABASE DESIGN — MODULE FORUM (DIỄN ĐÀN NGHIỆP VỤ)
## Schema: `forum` | Database: `kpi_haiquan` | PostgreSQL 15

> **Phiên bản:** 1.0 | **Ngày:** 18/02/2026
> **Trích từ:** CHIEN_LUOC_NEN_TANG_THONG_NHAT.md — Mục 3.3

---

## 1. TỔNG QUAN

| Thông tin | Giá trị |
|-----------|---------|
| **Schema** | `forum` |
| **Số bảng** | 5 |
| **Backend port** | 8002 |
| **FK chính** | `public.cong_chuc(id)` |
| **Liên quan** | `common.knowledge_base` (SOP/FAQ) |

### Danh sách bảng

| # | Bảng | Mục đích |
|---|------|----------|
| 1 | `forum.chuyen_muc` | Chuyên mục diễn đàn |
| 2 | `forum.chu_de` | Chủ đề / Thread |
| 3 | `forum.tra_loi` | Trả lời / Bình luận |
| 4 | `forum.bieu_quyet` | Upvote / Downvote |
| 5 | `forum.theo_doi` | Theo dõi chủ đề |

### ERD tóm tắt

```
chuyen_muc ──1:N──► chu_de ──1:N──► tra_loi
   │ (tự tham          │                │
   │  chiếu            │                └── (tự tham chiếu: reply lồng)
   │  parent)          │
                       ├──► bieu_quyet ◄── cong_chuc
                       └──► theo_doi ◄──── cong_chuc
```

---

## 2. KHỞI TẠO SCHEMA

```sql
CREATE SCHEMA IF NOT EXISTS forum;
GRANT ALL ON SCHEMA forum TO kpi_user;
```

---

## 3. CHI TIẾT CÁC BẢNG

### 3.1. `forum.chuyen_muc` — Chuyên mục diễn đàn

```sql
CREATE TABLE forum.chuyen_muc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ten_chuyen_muc VARCHAR(200) NOT NULL,
    mo_ta TEXT,
    icon VARCHAR(50),
    thu_tu INTEGER DEFAULT 0,
    parent_id UUID REFERENCES forum.chuyen_muc(id),   -- Phân cấp chuyên mục

    -- Cấu hình phân quyền
    chi_doc BOOLEAN DEFAULT FALSE,         -- TRUE = chỉ admin/expert mới đăng được
    yeu_cau_duyet BOOLEAN DEFAULT FALSE,   -- TRUE = bài mới cần duyệt trước khi hiện

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Dữ liệu mẫu:**

```sql
INSERT INTO forum.chuyen_muc (ten_chuyen_muc, mo_ta, icon, thu_tu) VALUES
('Thủ tục hải quan', 'Hỏi đáp về thủ tục XNK, quá cảnh, giám sát', '📋', 1),
('Kiểm tra sau thông quan', 'KTSTQ, phúc tập, thanh tra', '🔍', 2),
('Thuế XNK & Chính sách', 'Thuế suất, ưu đãi, C/O, trị giá', '💰', 3),
('Kiểm soát hải quan', 'Phòng chống buôn lậu, ma túy, gian lận', '🛡️', 4),
('CNTT & Hệ thống', 'VNACCS, V5, hệ thống nội bộ', '💻', 5),
('Pháp luật & Văn bản', 'Thảo luận văn bản mới, hướng dẫn áp dụng', '📜', 6),
('Tình huống thực tế', 'Chia sẻ case study, kinh nghiệm xử lý', '💡', 7),
('Góp ý & Đề xuất', 'Góp ý quy trình, đề xuất cải tiến', '✍️', 8);
```

### 3.2. `forum.chu_de` — Chủ đề / Thread

```sql
CREATE TABLE forum.chu_de (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chuyen_muc_id UUID NOT NULL REFERENCES forum.chuyen_muc(id),

    tieu_de VARCHAR(500) NOT NULL,
    noi_dung TEXT NOT NULL,               -- Markdown/HTML

    -- Tag phân loại
    tags JSONB DEFAULT '[]',
        -- VD: ["VNACCS", "thuế XNK", "luồng đỏ"]

    -- Tác giả
    tac_gia_id UUID NOT NULL REFERENCES public.cong_chuc(id),

    -- Trạng thái
    trang_thai VARCHAR(50) DEFAULT 'MO',
        -- 'CHO_DUYET': Chờ duyệt (nếu chuyen_muc.yeu_cau_duyet = TRUE)
        -- 'MO': Đang mở, cho phép trả lời
        -- 'DONG': Đã đóng (đã có đáp án chuẩn)
        -- 'GHIM': Ghim lên đầu chuyên mục
        -- 'AN': Ẩn (vi phạm hoặc trùng)

    is_ghim BOOLEAN DEFAULT FALSE,
    is_khoa BOOLEAN DEFAULT FALSE,        -- Khóa: không cho trả lời thêm

    -- Thống kê (cập nhật bằng trigger hoặc app logic)
    so_luot_xem INTEGER DEFAULT 0,
    so_tra_loi INTEGER DEFAULT 0,
    so_upvote INTEGER DEFAULT 0,

    -- Đáp án chuẩn (chuyên gia/điều phối chọn)
    tra_loi_chuan_id UUID,                -- FK → forum.tra_loi(id), set sau khi tạo

    -- Liên kết cross-module
    van_ban_lien_quan JSONB,              -- IDs từ legal.van_ban
        -- VD: ["uuid-vb-1", "uuid-vb-2"]
    sop_lien_quan JSONB,                  -- IDs từ common.knowledge_base
        -- VD: ["uuid-sop-1"]

    -- Điều phối
    nguoi_duyet_id UUID REFERENCES public.cong_chuc(id),
    ngay_duyet TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);
```

### 3.3. `forum.tra_loi` — Trả lời / Bình luận

```sql
CREATE TABLE forum.tra_loi (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chu_de_id UUID NOT NULL REFERENCES forum.chu_de(id),
    parent_id UUID REFERENCES forum.tra_loi(id),   -- Reply lồng nhau (threaded)

    noi_dung TEXT NOT NULL,                -- Markdown/HTML
    tac_gia_id UUID NOT NULL REFERENCES public.cong_chuc(id),

    -- Trạng thái
    is_dap_an_chuan BOOLEAN DEFAULT FALSE, -- Được chọn là đáp án chuẩn
    is_an BOOLEAN DEFAULT FALSE,           -- Bị ẩn (vi phạm)

    -- Thống kê
    so_upvote INTEGER DEFAULT 0,

    -- Căn cứ pháp lý đính kèm
    can_cu_phap_ly JSONB,
        -- VD: [
        --   {"loai": "VAN_BAN", "id": "uuid-vb", "trich_dan": "Điều 5 khoản 2..."},
        --   {"loai": "SOP", "id": "uuid-sop", "trich_dan": "Bước 3 quy trình..."}
        -- ]

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);
```

### 3.4. `forum.bieu_quyet` — Upvote / Downvote

```sql
CREATE TABLE forum.bieu_quyet (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cong_chuc_id UUID NOT NULL REFERENCES public.cong_chuc(id),

    -- Đối tượng vote (polymorphic)
    doi_tuong_type VARCHAR(20) NOT NULL,   -- 'CHU_DE' hoặc 'TRA_LOI'
    doi_tuong_id UUID NOT NULL,

    loai VARCHAR(10) NOT NULL,             -- 'UP' hoặc 'DOWN'

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (cong_chuc_id, doi_tuong_type, doi_tuong_id)
);
```

### 3.5. `forum.theo_doi` — Theo dõi chủ đề

```sql
CREATE TABLE forum.theo_doi (
    cong_chuc_id UUID NOT NULL REFERENCES public.cong_chuc(id),
    chu_de_id UUID NOT NULL REFERENCES forum.chu_de(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cong_chuc_id, chu_de_id)
);
```

---

## 4. INDEXES

```sql
CREATE INDEX idx_forum_cd_cm ON forum.chu_de(chuyen_muc_id);
CREATE INDEX idx_forum_cd_tg ON forum.chu_de(tac_gia_id);
CREATE INDEX idx_forum_cd_tt ON forum.chu_de(trang_thai);
CREATE INDEX idx_forum_cd_tags ON forum.chu_de USING GIN (tags);
CREATE INDEX idx_forum_cd_created ON forum.chu_de(created_at DESC);
CREATE INDEX idx_forum_tl_cd ON forum.tra_loi(chu_de_id);
CREATE INDEX idx_forum_tl_tg ON forum.tra_loi(tac_gia_id);
CREATE INDEX idx_forum_tl_parent ON forum.tra_loi(parent_id);
CREATE INDEX idx_forum_bq_dt ON forum.bieu_quyet(doi_tuong_type, doi_tuong_id);
```

---

## 5. FULL-TEXT SEARCH

```sql
ALTER TABLE forum.chu_de ADD COLUMN search_vector tsvector;

CREATE OR REPLACE FUNCTION forum.update_chu_de_search()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('simple',
        COALESCE(NEW.tieu_de, '') || ' ' || COALESCE(NEW.noi_dung, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_forum_chu_de_search
    BEFORE INSERT OR UPDATE ON forum.chu_de
    FOR EACH ROW EXECUTE FUNCTION forum.update_chu_de_search();

CREATE INDEX idx_forum_cd_search ON forum.chu_de USING GIN (search_vector);
```
