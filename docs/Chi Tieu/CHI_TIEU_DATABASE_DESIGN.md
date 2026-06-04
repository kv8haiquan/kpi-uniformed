# CHI_TIEU_DATABASE_DESIGN.md
## Thiết kế Cơ sở dữ liệu — Module Quản lý Chỉ tiêu Đơn vị

> **Phiên bản:** 1.0 | **Ngày:** 04/06/2026
> **DBMS:** PostgreSQL 15 | **Database:** `kpi_haiquan` (dùng chung) | **Schema:** `chi_tieu`
> **Tham chiếu:** CHI_TIEU_BUSINESS_RULES.md, INTEGRATION_RULES.md

---

## 1. NGUYÊN TẮC

- Toàn bộ bảng nghiệp vụ nằm trong schema **`chi_tieu`** (cô lập, KHÔNG đụng schema `public` hiện có).
- FK ra ngoài **chỉ** tham chiếu `public.cong_chuc(id)` và `public.don_vi(id)` — đúng ngoại lệ cho phép trong INTEGRATION_RULES.
- 2 vai trò mới thêm vào `public.platform_role` (mở rộng, không sửa bảng `vai_tro`/`cong_chuc`).
- Tên bảng/cột: tiếng Việt không dấu, snake_case. Comment: tiếng Việt.

## 2. SƠ ĐỒ QUAN HỆ (ERD)

```
 public.don_vi ───────────────┐         public.cong_chuc ──────────────┐
        ▲                      │                ▲                       │
        │ (FK)                 │ (FK)           │ (FK: người TD/người duyệt)
        │                      │                │
┌───────┴────────┐    ┌────────┴─────────┐   ┌──┴───────────────────┐
│ chi_tieu.      │    │ chi_tieu.        │   │ chi_tieu.dang_ky_thang│
│ giao_nam       │    │ dang_ky_thang    │◄──┤  (bản ghi lõi)        │
└───────┬────────┘    └────────┬─────────┘   └──────────┬───────────┘
        │ (FK chi_tieu_id)     │ (FK chi_tieu_id)       │ (FK dang_ky_thang_id)
        ▼                      ▼                ┌────────▼──────────┐
┌────────────────────────────────────┐         │ chi_tieu.         │
│ chi_tieu.danh_muc_chi_tieu          │         │ lich_su_duyet     │
└───────────────┬─────────────────────┘         └───────────────────┘
                │ (FK linh_vuc_id)
                ▼
        ┌──────────────────┐
        │ chi_tieu.linh_vuc│
        └──────────────────┘
```

---

## 3. MỞ RỘNG SCHEMA `public` (VAI TRÒ)

```sql
-- Thêm 2 vai trò bổ sung (KHÔNG sửa cấu trúc bảng, chỉ INSERT dữ liệu)
INSERT INTO public.platform_role (ma_role, ten_role, mo_ta) VALUES
('THEO_DOI_CHI_TIEU', 'Người theo dõi chỉ tiêu', 'Đăng ký chỉ tiêu đầu tháng và nhập kết quả cuối tháng cho đơn vị'),
('QT_CHI_TIEU',       'Quản trị chỉ tiêu',       'Quản lý danh mục chỉ tiêu, giao chỉ tiêu năm, xem báo cáo toàn Chi cục');

-- Gán role theo phạm vi đơn vị, ví dụ:
-- INSERT INTO public.cong_chuc_platform_role (cong_chuc_id, platform_role_id, pham_vi, assigned_by)
-- VALUES ('<uuid-cc>', '<uuid-role-THEO_DOI>', '{"don_vi_ids": ["<uuid-don-vi>"]}', '<uuid-admin>');
```

> JWT payload tự động có `platform_roles` chứa `THEO_DOI_CHI_TIEU` / `QT_CHI_TIEU` (cơ chế hiện có). Backend đọc `pham_vi.don_vi_ids` để giới hạn phạm vi.

---

## 4. SCHEMA & ENUMS

```sql
CREATE SCHEMA IF NOT EXISTS chi_tieu;

-- Mức chỉ tiêu năm
CREATE TYPE chi_tieu.LOAI_MUC AS ENUM ('PHAP_LENH', 'PHAN_DAU');

-- Kiểu dữ liệu của chỉ tiêu (để format & validate)
CREATE TYPE chi_tieu.KIEU_DU_LIEU AS ENUM ('SO_NGUYEN', 'THAP_PHAN', 'PHAN_TRAM');

-- Trạng thái vòng đời bản ghi tháng
CREATE TYPE chi_tieu.TRANG_THAI AS ENUM (
    'NHAP',                -- Đang soạn đăng ký
    'CHO_DUYET_DANG_KY',   -- Gửi TĐV duyệt đăng ký đầu tháng
    'DA_DUYET_DANG_KY',    -- TĐV đã duyệt đăng ký
    'CHO_DUYET_SUA',       -- Gửi TĐV duyệt yêu cầu sửa đăng ký
    'CHO_DUYET_KET_QUA',   -- Gửi TĐV duyệt kết quả cuối tháng
    'DA_DUYET_KET_QUA'     -- TĐV đã duyệt kết quả → chốt, đã khóa
);

-- Hành động trong lịch sử duyệt
CREATE TYPE chi_tieu.HANH_DONG AS ENUM (
    'GUI_DANG_KY', 'DUYET_DANG_KY', 'TU_CHOI_DANG_KY',
    'GUI_SUA', 'DUYET_SUA', 'TU_CHOI_SUA',
    'GUI_KET_QUA', 'DUYET_KET_QUA', 'TU_CHOI_KET_QUA',
    'MO_KHOA'
);
```

---

## 5. CÁC BẢNG

### 5.1. `chi_tieu.linh_vuc` — Lĩnh vực công tác

```sql
CREATE TABLE chi_tieu.linh_vuc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ma_linh_vuc VARCHAR(30) UNIQUE NOT NULL,        -- GSQL, THUE, KTSTQ...
    ten_linh_vuc VARCHAR(200) NOT NULL,
    van_ban_ke_hoach VARCHAR(300),                  -- "KH 24/KH-HQKV8 ngày 06/01/2026"
    thu_tu INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2. `chi_tieu.danh_muc_chi_tieu` — Danh mục chỉ tiêu

```sql
CREATE TABLE chi_tieu.danh_muc_chi_tieu (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    linh_vuc_id UUID NOT NULL REFERENCES chi_tieu.linh_vuc(id),
    ma_chi_tieu VARCHAR(30) UNIQUE NOT NULL,        -- GSQL_01, THUE_PL...
    ten_chi_tieu VARCHAR(500) NOT NULL,             -- "Kim ngạch XNK (không gồm KNQ, TNTX)"
    don_vi_tinh VARCHAR(50) NOT NULL,               -- "triệu USD", "tỷ đồng", "số vụ", "%"...
    kieu_du_lieu chi_tieu.KIEU_DU_LIEU DEFAULT 'THAP_PHAN',
    co_phan_dau BOOLEAN DEFAULT FALSE,              -- TRUE nếu chỉ tiêu có 2 mức
    van_ban_giao VARCHAR(300),                      -- văn bản riêng nếu khác lĩnh vực
    mo_ta TEXT,
    thu_tu INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ct_danhmuc_linhvuc ON chi_tieu.danh_muc_chi_tieu(linh_vuc_id);
```

### 5.3. `chi_tieu.giao_nam` — Chỉ tiêu giao năm cho đơn vị

```sql
CREATE TABLE chi_tieu.giao_nam (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    don_vi_id UUID NOT NULL REFERENCES public.don_vi(id),
    chi_tieu_id UUID NOT NULL REFERENCES chi_tieu.danh_muc_chi_tieu(id),
    nam INT NOT NULL CHECK (nam >= 2025),
    loai_muc chi_tieu.LOAI_MUC NOT NULL DEFAULT 'PHAP_LENH',

    gia_tri_giao DECIMAL(18,3) NOT NULL,            -- chỉ tiêu giao năm
    luy_ke_dau_ky DECIMAL(18,3) DEFAULT 0,          -- số liệu mang sang khi nhập giữa năm

    nguoi_giao_id UUID REFERENCES public.cong_chuc(id),
    ghi_chu TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,

    UNIQUE (don_vi_id, chi_tieu_id, nam, loai_muc)
);

CREATE INDEX idx_ct_giaonam_donvi ON chi_tieu.giao_nam(don_vi_id, nam);
CREATE INDEX idx_ct_giaonam_chitieu ON chi_tieu.giao_nam(chi_tieu_id);
```

### 5.4. `chi_tieu.dang_ky_thang` — Đăng ký + kết quả theo tháng (BẢNG LÕI)

```sql
CREATE TABLE chi_tieu.dang_ky_thang (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    don_vi_id UUID NOT NULL REFERENCES public.don_vi(id),
    chi_tieu_id UUID NOT NULL REFERENCES chi_tieu.danh_muc_chi_tieu(id),
    thang INT NOT NULL CHECK (thang BETWEEN 1 AND 12),
    nam INT NOT NULL CHECK (nam >= 2025),

    -- Đăng ký đầu tháng
    khong_dang_ky BOOLEAN DEFAULT FALSE,            -- TRUE = "Không đăng ký"
    gia_tri_dang_ky DECIMAL(18,3),                  -- NULL nếu không đăng ký

    -- Kết quả cuối tháng
    gia_tri_ket_qua DECIMAL(18,3),

    -- Đánh giá: % tự tính + nhãn chữ ghi đè
    danh_gia_tu_dong VARCHAR(100),                  -- "Đạt 142%" (hệ thống điền)
    danh_gia_ghi_chu VARCHAR(200),                  -- "Vượt chỉ tiêu", "Đã thực hiện T3"...

    -- Trạng thái vòng đời
    trang_thai chi_tieu.TRANG_THAI NOT NULL DEFAULT 'NHAP',

    -- Người liên quan
    nguoi_theo_doi_id UUID NOT NULL REFERENCES public.cong_chuc(id),
    nguoi_duyet_id UUID REFERENCES public.cong_chuc(id),

    -- Mốc thời gian quy trình
    ngay_gui_dang_ky TIMESTAMP,
    ngay_duyet_dang_ky TIMESTAMP,
    ngay_gui_ket_qua TIMESTAMP,
    ngay_duyet_ket_qua TIMESTAMP,
    ly_do_tu_choi TEXT,

    -- Khóa sau khi chốt
    is_khoa BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,

    UNIQUE (don_vi_id, chi_tieu_id, thang, nam)
);

CREATE INDEX idx_ct_dk_donvi ON chi_tieu.dang_ky_thang(don_vi_id, thang, nam);
CREATE INDEX idx_ct_dk_chitieu ON chi_tieu.dang_ky_thang(chi_tieu_id);
CREATE INDEX idx_ct_dk_trangthai ON chi_tieu.dang_ky_thang(trang_thai);
CREATE INDEX idx_ct_dk_nguoiduyet ON chi_tieu.dang_ky_thang(nguoi_duyet_id);
```

### 5.5. `chi_tieu.lich_su_duyet` — Lịch sử thao tác/duyệt (audit)

```sql
CREATE TABLE chi_tieu.lich_su_duyet (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dang_ky_thang_id UUID NOT NULL REFERENCES chi_tieu.dang_ky_thang(id),
    hanh_dong chi_tieu.HANH_DONG NOT NULL,
    nguoi_thuc_hien_id UUID NOT NULL REFERENCES public.cong_chuc(id),
    noi_dung_truoc JSONB,                           -- snapshot trước
    noi_dung_sau JSONB,                             -- snapshot sau
    ghi_chu TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ct_lichsu_dangky ON chi_tieu.lich_su_duyet(dang_ky_thang_id);
```

---

## 6. VIEW HỖ TRỢ BÁO CÁO

```sql
-- Lũy kế & Đạt% theo (đơn vị, chỉ tiêu, năm) — tính từ kết quả ĐÃ DUYỆT
CREATE VIEW chi_tieu.v_luy_ke_nam AS
SELECT
    g.don_vi_id,
    g.chi_tieu_id,
    g.nam,
    g.loai_muc,
    g.gia_tri_giao,
    g.luy_ke_dau_ky + COALESCE(SUM(d.gia_tri_ket_qua), 0) AS luy_ke_nam,
    CASE WHEN g.gia_tri_giao > 0
         THEN ROUND((g.luy_ke_dau_ky + COALESCE(SUM(d.gia_tri_ket_qua),0)) / g.gia_tri_giao * 100, 2)
         ELSE NULL END AS dat_phan_tram_nam
FROM chi_tieu.giao_nam g
LEFT JOIN chi_tieu.dang_ky_thang d
       ON d.don_vi_id = g.don_vi_id
      AND d.chi_tieu_id = g.chi_tieu_id
      AND d.nam = g.nam
      AND d.trang_thai = 'DA_DUYET_KET_QUA'
      AND d.is_deleted = FALSE
WHERE g.is_deleted = FALSE
GROUP BY g.don_vi_id, g.chi_tieu_id, g.nam, g.loai_muc, g.gia_tri_giao, g.luy_ke_dau_ky;
```

---

## 7. CẤU HÌNH (dùng `public.platform_config`)

| Key | Value mẫu | Ý nghĩa |
|-----|-----------|---------|
| `chi_tieu.han_dang_ky_ngay` | `{"ngay": 5}` | Hạn đăng ký chỉ tiêu trong tháng |
| `chi_tieu.han_ket_qua_ngay` | `{"ngay": 3}` | Hạn nhập kết quả (tháng sau) |
| `chi_tieu.nguong_canh_bao_dat` | `{"phan_tram": 50}` | Đạt% năm dưới ngưỡng → cảnh báo |

---

## 8. LỊCH SỬ THAY ĐỔI

| Phiên bản | Ngày | Nội dung |
|-----------|------|----------|
| 1.0 | 04/06/2026 | Thiết kế schema `chi_tieu` (5 bảng + 1 view) + 2 platform_role |
