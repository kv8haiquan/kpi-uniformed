# SHARED_DB_REFERENCE.md
## Tham chiếu Database dùng chung — Nền tảng Số Thống nhất HQKV8

> **Phiên bản:** 1.0.0 | **Ngày:** 18/02/2026  
> **Kiến trúc sư trưởng:** Architect Team  
> **Áp dụng cho:** TẤT CẢ module (LMS, Forum, Legal, Portal, Common)  
> **Database:** PostgreSQL 15 — `kpi_haiquan`  
> **Server:** VPS Viettel Cloud — 27.71.229.103

---

## 1. QUY TẮC VÀNG

```
╔═══════════════════════════════════════════════════════════════════════╗
║                        QUY TẮC BẤT DI BẤT DỊCH                      ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  1. CÁC BẢNG KPI TRONG SCHEMA PUBLIC LÀ READONLY                     ║
║     → KHÔNG INSERT, UPDATE, DELETE vào bảng KPI                       ║
║     → CHỈ SELECT / JOIN để đọc thông tin                              ║
║                                                                       ║
║  2. FOREIGN KEY → public.cong_chuc(id)                                ║
║     → Mọi bảng cần liên kết user PHẢI FK đến cong_chuc(id)           ║
║     → KHÔNG tạo bảng user riêng trong schema module                   ║
║                                                                       ║
║  3. MỖI MODULE = 1 SCHEMA RIÊNG                                      ║
║     → lms.*, forum.*, legal.*, portal.*, common.*                     ║
║     → KHÔNG tạo bảng module trong schema public                       ║
║     (trừ platform_role, cong_chuc_platform_role, platform_config)     ║
║                                                                       ║
║  4. UUID CHO MỌI PRIMARY KEY                                         ║
║     → DEFAULT gen_random_uuid()                                       ║
║     → KHÔNG dùng SERIAL / BIGSERIAL                                   ║
║                                                                       ║
║  5. MIGRATION CÓ UPGRADE() VÀ DOWNGRADE()                            ║
║     → Backup database TRƯỚC khi migrate production                    ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

## 2. SƠ ĐỒ TỔNG QUAN 6 SCHEMA

```
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL: kpi_haiquan                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  SCHEMA: public (KPI — GIỮ NGUYÊN + 3 bảng bổ sung)      │   │
│  │                                                            │   │
│  │  [READONLY — KHÔNG SỬA]          [MỚI — CÓ THỂ SỬA]     │   │
│  │  • don_vi                        • platform_role           │   │
│  │  • vai_tro                       • cong_chuc_platform_role │   │
│  │  • cong_chuc ◄─── FK ──── tất cả module                  │   │
│  │  • danh_muc_sp_cong_viec        • platform_config          │   │
│  │  • sp_chuan                                                │   │
│  │  • cap_do                                                  │   │
│  │  • ke_khai_cong_viec                                       │   │
│  │  • ke_khai_lanh_dao                                        │   │
│  │  • danh_gia_thang                                          │   │
│  │  • danh_gia_dde                                            │   │
│  │  • ket_qua_tieu_chi_chung                                  │   │
│  │  • tieu_chi_chung                                          │   │
│  │  • bao_cao_xep_loai                                        │   │
│  │  • chi_tiet_xep_loai                                       │   │
│  │  • dang_ky_nghi                                            │   │
│  │  • audit_log                                               │   │
│  │  • system_settings                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ │
│  │ lms      │ │ forum    │ │ legal    │ │ portal │ │ common │ │
│  │ (Dev B)  │ │ (Dev C)  │ │ (Dev D)  │ │(Dev E) │ │(Dev E) │ │
│  │ 10 bảng  │ │ 5 bảng   │ │ 6 bảng   │ │ 4 bảng │ │ 4 bảng │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘ └────────┘ │
│       │            │            │           │          │        │
│       └────────────┴────────────┴───────────┴──────────┘        │
│                   Tất cả FK → public.cong_chuc(id)              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. BẢNG DÙNG CHUNG — CẤU TRÚC CHI TIẾT

### 3.1. `public.don_vi` — Đơn vị tổ chức (READONLY)

```sql
CREATE TABLE don_vi (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ma_don_vi       VARCHAR(20) UNIQUE NOT NULL,   -- VD: "DV01"
    ten_don_vi      VARCHAR(200) NOT NULL,          -- VD: "Đội Nghiệp vụ 1"
    ten_viet_tat    VARCHAR(50),                    -- VD: "ĐNV1"
    loai_don_vi     LOAI_DON_VI NOT NULL,           -- PHONG | DOI | HAI_QUAN_CUA_KHAU
    don_vi_cha_id   UUID REFERENCES don_vi(id),     -- Phân cấp
    thu_tu          INT DEFAULT 0,                  -- Thứ tự hiển thị
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Dữ liệu production:** 15 đơn vị (Phòng/Đội/HQ Cửa khẩu)

**Cách sử dụng trong module mới:**
```python
# SQLAlchemy model (READONLY — chỉ dùng để query)
class DonVi(Base):
    __tablename__ = "don_vi"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID, primary_key=True)
    ma_don_vi = Column(String(20), unique=True)
    ten_don_vi = Column(String(200))
    ten_viet_tat = Column(String(50))
    loai_don_vi = Column(String(50))  # PHONG, DOI, HAI_QUAN_CUA_KHAU
    don_vi_cha_id = Column(UUID, ForeignKey("public.don_vi.id"))
    thu_tu = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
```

### 3.2. `public.vai_tro` — Vai trò KPI (READONLY)

```sql
CREATE TABLE vai_tro (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ma_vai_tro      VARCHAR(20) UNIQUE NOT NULL,   -- VD: "CC" (Công chức)
    ten_vai_tro     VARCHAR(100) NOT NULL,
    cap_bac         CAP_BAC NOT NULL,               -- Enum: CHI_CUC_TRUONG → CONG_CHUC
    is_lanh_dao     BOOLEAN DEFAULT FALSE,
    mo_ta           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Dữ liệu production:** 7 vai trò

| ma_vai_tro | cap_bac | is_lanh_dao |
|-----------|---------|-------------|
| SUPER_ADMIN | SUPER_ADMIN | ✅ |
| CCT | CHI_CUC_TRUONG | ✅ |
| PCCT | PHO_CHI_CUC_TRUONG | ✅ |
| TDV | TRUONG_DON_VI | ✅ |
| PDV | PHO_DON_VI | ✅ |
| CC | CONG_CHUC | ❌ |
| TCCB | TCCB | ❌ |

### 3.3. `public.cong_chuc` — Công chức / User (READONLY)

```sql
CREATE TABLE cong_chuc (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ma_cc           VARCHAR(20) UNIQUE NOT NULL,    -- VD: "20ZZ-0224"
    ho_ten          VARCHAR(100) NOT NULL,
    ngay_sinh       DATE,
    gioi_tinh       VARCHAR(10),                    -- "Nam" | "Nữ"
    so_dien_thoai   VARCHAR(20),
    email           VARCHAR(100),
    
    -- Quan hệ
    don_vi_id       UUID NOT NULL REFERENCES don_vi(id),
    vai_tro_id      UUID NOT NULL REFERENCES vai_tro(id),
    
    -- Chức vụ
    chuc_vu         VARCHAR(100),                   -- VD: "Công chức", "Đội trưởng"
    is_lanh_dao     BOOLEAN DEFAULT FALSE,
    
    -- Authentication (KHÔNG ĐỌC — chỉ KPI backend sử dụng)
    password_hash   VARCHAR(255) NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    last_login      TIMESTAMP,
    
    -- Thông tin bổ sung
    ngay_vao_nganh  DATE,
    ngay_vao_chi_cuc DATE,
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted      BOOLEAN DEFAULT FALSE
);
```

**Dữ liệu production:** 549 người dùng (bao gồm 1 admin, 56 lãnh đạo)

**SQLAlchemy model cho module mới:**
```python
class CongChuc(Base):
    """Model READONLY — KHÔNG INSERT/UPDATE/DELETE.
    Sử dụng để JOIN lấy thông tin user.
    """
    __tablename__ = "cong_chuc"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID, primary_key=True)
    ma_cc = Column(String(20), unique=True)
    ho_ten = Column(String(100))
    email = Column(String(100))
    so_dien_thoai = Column(String(20))
    
    don_vi_id = Column(UUID, ForeignKey("public.don_vi.id"))
    vai_tro_id = Column(UUID, ForeignKey("public.vai_tro.id"))
    chuc_vu = Column(String(100))
    is_lanh_dao = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # ⚠️ KHÔNG map password_hash — Module mới KHÔNG CẦN đọc
    
    # Relationships (readonly)
    don_vi = relationship("DonVi", lazy="joined")
    vai_tro = relationship("VaiTro", lazy="joined")
```

---

## 4. BẢNG BỔ SUNG PLATFORM (CÓ QUYỀN GHI)

### 4.1. `public.platform_role`

```sql
CREATE TABLE public.platform_role (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ma_role     VARCHAR(50) NOT NULL UNIQUE,
    ten_role    VARCHAR(100) NOT NULL,
    mo_ta       TEXT,
    quyen_han   JSONB DEFAULT '{}',
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2. `public.cong_chuc_platform_role`

```sql
CREATE TABLE public.cong_chuc_platform_role (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cong_chuc_id     UUID NOT NULL REFERENCES public.cong_chuc(id),
    platform_role_id UUID NOT NULL REFERENCES public.platform_role(id),
    pham_vi          JSONB,
    assigned_by      UUID REFERENCES public.cong_chuc(id),
    assigned_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active        BOOLEAN DEFAULT TRUE,
    UNIQUE (cong_chuc_id, platform_role_id)
);
```

### 4.3. `public.platform_config`

```sql
CREATE TABLE public.platform_config (
    key         VARCHAR(100) PRIMARY KEY,
    value       JSONB NOT NULL,
    mo_ta       TEXT,
    updated_by  UUID REFERENCES public.cong_chuc(id),
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. QUY TẮC FOREIGN KEY

### 5.1. Mẫu FK chuẩn cho module mới

Mọi bảng trong module cần liên kết user PHẢI dùng mẫu sau:

```sql
-- ✅ ĐÚNG: FK trực tiếp đến public.cong_chuc(id)
CREATE TABLE lms.khoa_hoc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ...
    giang_vien_id UUID REFERENCES public.cong_chuc(id),   -- FK đến cong_chuc
    nguoi_duyet_id UUID REFERENCES public.cong_chuc(id),  -- FK đến cong_chuc
    ...
);

-- ❌ SAI: Tạo bảng user riêng
CREATE TABLE lms.nguoi_dung (    -- ❌ KHÔNG ĐƯỢC TẠO
    id UUID PRIMARY KEY,
    cong_chuc_id UUID,
    ...
);
```

### 5.2. Mẫu FK đến don_vi (nếu cần)

```sql
-- Nếu cần lọc theo đơn vị
CREATE TABLE lms.bao_cao_dao_tao (
    ...
    don_vi_id UUID REFERENCES public.don_vi(id),   -- FK đến don_vi
    ...
);
```

### 5.3. Cross-schema JOIN

PostgreSQL cho phép JOIN giữa các schema trong cùng database:

```sql
-- Lấy danh sách khóa học kèm thông tin giảng viên
SELECT 
    kh.ten_khoa_hoc,
    kh.trang_thai,
    cc.ho_ten AS giang_vien,
    cc.chuc_vu,
    dv.ten_don_vi
FROM lms.khoa_hoc kh
JOIN public.cong_chuc cc ON kh.giang_vien_id = cc.id
JOIN public.don_vi dv ON cc.don_vi_id = dv.id
WHERE kh.is_active = TRUE;
```

---

## 6. DANH SÁCH BẢNG THEO SCHEMA

### 6.1. Schema `lms` — Module Đào tạo (Dev B)

| Bảng | Mục đích | FK đến public |
|------|---------|---------------|
| `chuyen_de` | Chuyên đề đào tạo | `created_by → cong_chuc(id)` |
| `khoa_hoc` | Khóa học | `giang_vien_id, nguoi_duyet_id → cong_chuc(id)` |
| `bai_hoc` | Bài học/nội dung | — (qua khoa_hoc) |
| `cau_hoi` | Ngân hàng câu hỏi | `nguoi_tao_id → cong_chuc(id)` |
| `bai_kiem_tra` | Bài kiểm tra | `nguoi_tao_id → cong_chuc(id)` |
| `bai_kiem_tra_cau_hoi` | Liên kết BKT-CH | — |
| `dang_ky_khoa_hoc` | Đăng ký/giao khóa | `cong_chuc_id, nguoi_giao_id → cong_chuc(id)` |
| `tien_do_bai_hoc` | Tiến độ từng bài | `cong_chuc_id → cong_chuc(id)` |
| `ket_qua_bai_kiem_tra` | Kết quả thi | `cong_chuc_id → cong_chuc(id)` |
| `chung_chi` | Chứng nhận hoàn thành | `cong_chuc_id, nguoi_cap_id → cong_chuc(id)` |
| `khao_sat` | Khảo sát sau khóa | `cong_chuc_id → cong_chuc(id)` |

### 6.2. Schema `forum` — Module Diễn đàn (Dev C)

| Bảng | Mục đích | FK đến public |
|------|---------|---------------|
| `chuyen_muc` | Chuyên mục diễn đàn | — |
| `chu_de` | Chủ đề/thread | `tac_gia_id, nguoi_duyet_id → cong_chuc(id)` |
| `tra_loi` | Trả lời/bình luận | `tac_gia_id → cong_chuc(id)` |
| `bieu_quyet` | Upvote/Downvote | `cong_chuc_id → cong_chuc(id)` |
| `theo_doi` | Theo dõi chủ đề | `cong_chuc_id → cong_chuc(id)` |

### 6.3. Schema `legal` — Module Pháp luật (Dev D)

| Bảng | Mục đích | FK đến public |
|------|---------|---------------|
| `loai_van_ban` | Loại văn bản | — |
| `van_ban` | Kho văn bản PL | `nguoi_nhap_id, nguoi_duyet_id → cong_chuc(id)` |
| `van_ban_lien_ket` | Liên kết VB | — |
| `xac_nhan_doc` | Xác nhận đã đọc | `cong_chuc_id → cong_chuc(id)` |
| `quiz_van_ban` | Quiz kiểm tra VB | `nguoi_tao_id → cong_chuc(id)` |
| `ket_qua_quiz` | Kết quả quiz | `cong_chuc_id → cong_chuc(id)` |

### 6.4. Schema `portal` — Portal/CMS (Dev E)

| Bảng | Mục đích | FK đến public |
|------|---------|---------------|
| `chuyen_muc` | Chuyên mục tin tức | — |
| `bai_viet` | Tin tức/Bài viết | `nguoi_soan_id, nguoi_duyet_id → cong_chuc(id)` |
| `thu_muc` | Thư mục tài liệu | — |
| `tai_lieu` | Tài liệu ECM | `nguoi_tai_len_id → cong_chuc(id)` |

### 6.5. Schema `common` — Module dùng chung (Dev E)

| Bảng | Mục đích | FK đến public |
|------|---------|---------------|
| `thong_bao` | Thông báo | `nguoi_nhan_id → cong_chuc(id)` |
| `file_storage` | Metadata file | `nguoi_tai_len_id → cong_chuc(id)` |
| `knowledge_base` | SOP/FAQ | `chu_so_huu_id → cong_chuc(id)` |
| `kpi_integration_log` | Tích hợp KPI | `cong_chuc_id → cong_chuc(id)` |

---

## 7. QUY TẮC KIỂU DỮ LIỆU & NAMING

### 7.1. Kiểu dữ liệu chuẩn

| Loại | Kiểu dữ liệu | Ví dụ |
|------|--------------|-------|
| Primary Key | `UUID DEFAULT gen_random_uuid()` | `id` |
| Foreign Key | `UUID REFERENCES schema.table(id)` | `cong_chuc_id` |
| Tên/Tiêu đề ngắn | `VARCHAR(100-500)` | `ten_khoa_hoc` |
| Nội dung dài | `TEXT` | `noi_dung`, `mo_ta` |
| Trạng thái | `VARCHAR(50)` | `trang_thai` |
| Số nguyên | `INTEGER` | `so_luong`, `thu_tu` |
| Số thập phân | `DECIMAL(5,2)` | `diem`, `phan_tram` |
| Boolean | `BOOLEAN DEFAULT FALSE/TRUE` | `is_active`, `da_doc` |
| Thời gian | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | `created_at` |
| Ngày | `DATE` | `ngay_bat_dau` |
| JSON linh hoạt | `JSONB DEFAULT '{}'` hoặc `'[]'` | `tags`, `metadata` |

### 7.2. Naming convention

| Thành phần | Quy tắc | Ví dụ |
|-----------|---------|-------|
| Schema | `snake_case`, tiếng Anh | `lms`, `forum`, `legal` |
| Bảng | `snake_case`, tiếng Việt (không dấu) | `khoa_hoc`, `chu_de` |
| Cột | `snake_case`, tiếng Việt (không dấu) | `ten_khoa_hoc`, `ngay_tao` |
| FK column | `{bảng_ref}_id` | `cong_chuc_id`, `khoa_hoc_id` |
| Boolean column | `is_*` hoặc `da_*` | `is_active`, `da_doc` |
| Timestamp column | `*_at` | `created_at`, `updated_at` |
| Index | `idx_{schema}_{bảng}_{cột}` | `idx_lms_dkkh_cc` |
| Enum values | `UPPER_SNAKE_CASE` | `'DANG_HOC'`, `'DA_XUAT_BAN'` |

### 7.3. Các cột bắt buộc cho mọi bảng mới

```sql
CREATE TABLE {schema}.{ten_bang} (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),   -- BẮT BUỘC
    ...
    -- Các cột nghiệp vụ
    ...
    is_active   BOOLEAN DEFAULT TRUE,                          -- KHUYẾN NGHỊ
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,           -- BẮT BUỘC
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP            -- KHUYẾN NGHỊ
);
```

---

## 8. TÍCH HỢP KPI — BẢNG `common.kpi_integration_log`

Đây là bảng **DUY NHẤT** để các module ghi dữ liệu ngược về phục vụ KPI:

```sql
CREATE TABLE common.kpi_integration_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cong_chuc_id    UUID NOT NULL REFERENCES public.cong_chuc(id),
    thang           INTEGER NOT NULL,    -- 1-12
    nam             INTEGER NOT NULL,    -- 2026+
    module          VARCHAR(50) NOT NULL, -- 'LMS' | 'FORUM' | 'LEGAL'
    metrics         JSONB NOT NULL,       -- Dữ liệu metrics
    diem_quy_doi    DECIMAL(5,2),
    synced_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (cong_chuc_id, thang, nam, module)
);
```

**Ví dụ metrics theo module:**

```json
// LMS
{"khoa_hoc_hoan_thanh": 3, "diem_tb": 85.5, "chung_chi": 1, "gio_hoc": 12}

// FORUM  
{"bai_dang": 5, "tra_loi": 12, "upvote": 30, "bai_chuan": 2}

// LEGAL
{"vb_da_doc": 8, "vb_chua_doc": 2, "quiz_diem_tb": 90.0, "vb_qua_han": 0}
```

> **Lưu ý:** Dữ liệu từ `kpi_integration_log` được sử dụng làm **THÔNG TIN THAM KHẢO** cho lãnh đạo khi đánh giá — KHÔNG tự động thay đổi điểm KPI.

---

## 9. MIGRATION TEMPLATE

```python
"""
Migration: {mô_tả_ngắn}
Schema: {tên_schema}
Author: {tên_dev}
Date: {ngày}
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# Revision identifiers
revision = '{revision_id}'
down_revision = '{previous_revision}'
branch_labels = None
depends_on = None


def upgrade():
    # BẮT BUỘC: Kiểm tra schema tồn tại
    op.execute("CREATE SCHEMA IF NOT EXISTS {schema_name}")
    
    op.create_table(
        '{ten_bang}',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('cong_chuc_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=False),
        # ... thêm các cột ...
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        schema='{schema_name}'
    )
    
    # Index
    op.create_index('idx_{schema}_{bang}_{col}', '{ten_bang}', ['{col}'], schema='{schema_name}')


def downgrade():
    op.drop_index('idx_{schema}_{bang}_{col}', table_name='{ten_bang}', schema='{schema_name}')
    op.drop_table('{ten_bang}', schema='{schema_name}')
```

---

## 10. CHECKLIST CHO DEV

```
□ Đã đọc và hiểu toàn bộ file này
□ Model SQLAlchemy cho cong_chuc/don_vi/vai_tro là READONLY
□ Không map password_hash trong model CongChuc
□ Mọi bảng mới đều có: id (UUID), created_at, updated_at  
□ FK user luôn → public.cong_chuc(id)
□ Bảng mới nằm trong schema riêng (lms/forum/legal/portal/common)
□ Migration có cả upgrade() và downgrade()
□ Naming convention đúng theo mục 7.2
□ Ghi kpi_integration_log khi có metrics cần báo cáo
□ Test cross-schema JOIN hoạt động đúng
```

---

> **Liên hệ:** Mọi thắc mắc về Database → Kiến trúc sư trưởng  
> **Cập nhật:** File này được quản lý tập trung. KHÔNG fork/copy riêng.
