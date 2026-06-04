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

> **Quy ước dự án:** KHÔNG dùng PostgreSQL `ENUM` type. Mọi trường trạng thái/loại dùng `VARCHAR` + `CHECK` constraint (dễ migrate, không phải `ALTER TYPE` khi bổ sung giá trị). Các giá trị hợp lệ liệt kê trong CHECK và ràng buộc thêm ở tầng schema/service.

```sql
CREATE SCHEMA IF NOT EXISTS chi_tieu;
```

Các tập giá trị hợp lệ (khai báo qua `CHECK` trên từng cột, xem mục 5):

| Nhóm | Cột áp dụng | Giá trị hợp lệ |
|------|-------------|----------------|
| Mức chỉ tiêu năm (`loai_muc`) | `giao_nam.loai_muc` | `PHAP_LENH`, `PHAN_DAU` |
| Kiểu dữ liệu chỉ tiêu (`kieu_du_lieu`) | `danh_muc_chi_tieu.kieu_du_lieu` | `SO_NGUYEN`, `THAP_PHAN`, `PHAN_TRAM` |
| Trạng thái bản ghi tháng (`trang_thai`) | `dang_ky_thang.trang_thai` | `NHAP`, `CHO_DUYET_DANG_KY`, `DA_DUYET_DANG_KY`, `CHO_DUYET_SUA`, `CHO_DUYET_KET_QUA`, `DA_DUYET_KET_QUA` |
| Hành động lịch sử (`hanh_dong`) | `lich_su_duyet.hanh_dong` | `GUI_DANG_KY`, `DUYET_DANG_KY`, `TU_CHOI_DANG_KY`, `GUI_SUA`, `DUYET_SUA`, `TU_CHOI_SUA`, `GUI_KET_QUA`, `DUYET_KET_QUA`, `TU_CHOI_KET_QUA`, `MO_KHOA` |

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
    kieu_du_lieu VARCHAR(20) NOT NULL DEFAULT 'THAP_PHAN'
        CHECK (kieu_du_lieu IN ('SO_NGUYEN', 'THAP_PHAN', 'PHAN_TRAM')),
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
    loai_muc VARCHAR(20) NOT NULL DEFAULT 'PHAP_LENH'
        CHECK (loai_muc IN ('PHAP_LENH', 'PHAN_DAU')),

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
    trang_thai VARCHAR(30) NOT NULL DEFAULT 'NHAP'
        CHECK (trang_thai IN (
            'NHAP', 'CHO_DUYET_DANG_KY', 'DA_DUYET_DANG_KY',
            'CHO_DUYET_SUA', 'CHO_DUYET_KET_QUA', 'DA_DUYET_KET_QUA'
        )),

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
    hanh_dong VARCHAR(30) NOT NULL
        CHECK (hanh_dong IN (
            'GUI_DANG_KY', 'DUYET_DANG_KY', 'TU_CHOI_DANG_KY',
            'GUI_SUA', 'DUYET_SUA', 'TU_CHOI_SUA',
            'GUI_KET_QUA', 'DUYET_KET_QUA', 'TU_CHOI_KET_QUA', 'MO_KHOA'
        )),
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

Lũy kế phải **cắt theo tháng đang xem** (không cộng toàn bộ năm). View dưới đây trả về **lũy kế chạy theo TỪNG tháng** — báo cáo tháng N chỉ việc lấy dòng `thang = N`:

```sql
-- Lũy kế & Đạt% chạy theo (đơn vị, chỉ tiêu, năm, THÁNG) — tính từ kết quả ĐÃ DUYỆT
-- luy_ke_den_thang = lũy kế đầu kỳ + Σ kết quả đã duyệt của các tháng 1..thang
CREATE VIEW chi_tieu.v_luy_ke_thang AS
SELECT
    g.don_vi_id,
    g.chi_tieu_id,
    g.nam,
    g.loai_muc,
    g.gia_tri_giao,
    d.thang,
    g.luy_ke_dau_ky
      + SUM(d.gia_tri_ket_qua) OVER (
            PARTITION BY g.don_vi_id, g.chi_tieu_id, g.nam, g.loai_muc
            ORDER BY d.thang
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS luy_ke_den_thang,
    CASE WHEN g.gia_tri_giao > 0
         THEN ROUND((g.luy_ke_dau_ky
              + SUM(d.gia_tri_ket_qua) OVER (
                    PARTITION BY g.don_vi_id, g.chi_tieu_id, g.nam, g.loai_muc
                    ORDER BY d.thang
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                )) / g.gia_tri_giao * 100, 2)
         ELSE NULL END AS dat_phan_tram_den_thang
FROM chi_tieu.giao_nam g
JOIN chi_tieu.dang_ky_thang d
       ON d.don_vi_id = g.don_vi_id
      AND d.chi_tieu_id = g.chi_tieu_id
      AND d.nam = g.nam
      AND d.trang_thai = 'DA_DUYET_KET_QUA'
      AND d.is_deleted = FALSE
WHERE g.is_deleted = FALSE;
```

> Báo cáo "rà soát tháng N" lấy `WHERE thang = N`. Nếu cần tổng lũy kế cả năm thì lấy dòng `thang` lớn nhất đã chốt. View dùng `JOIN` (không `LEFT JOIN`) vì lũy kế chỉ phát sinh khi có kết quả đã duyệt; chỉ tiêu chưa có tháng nào chốt sẽ không xuất hiện — báo cáo coi như lũy kế = `luy_ke_dau_ky`.

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
| 1.1 | 04/06/2026 | Bỏ PostgreSQL ENUM → `VARCHAR` + `CHECK` (theo convention dự án); view lũy kế tính chạy theo từng tháng (`v_luy_ke_thang`) |
