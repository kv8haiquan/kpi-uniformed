# INTEGRATION RULES
## Quy tắc tích hợp giữa các module — Nền tảng Số HQKV8

> **Phiên bản:** 1.0 | **Ngày:** 18/02/2026
> **Quản lý bởi:** Tech Lead (HUB project)

---

## I. NGUYÊN TẮC NỀN TẢNG

### Quy tắc #1: Mở rộng, không thay thế

```
⛔ KHÔNG BAO GIỜ:
- Sửa bảng / API / logic của module KPI hiện tại
- Thay đổi flow đăng nhập (POST /api/v1/auth/login)
- Sửa cấu trúc JWT hiện tại (chỉ được THÊM field)
- Xóa hoặc rename bảng trong schema public

✅ CHỈ ĐƯỢC:
- Thêm bảng mới vào schema riêng (lms, forum, legal, portal, common)
- Thêm bảng mới vào schema public (platform_role, cong_chuc_platform_role)
- Thêm field mới vào JWT payload (platform_roles)
- Tạo backend service mới trên port mới
- Thêm route mới trên Frontend
```

### Quy tắc #2: Schema isolation

```
Mỗi module SỞ HỮU schema riêng, KHÔNG ĐƯỢC:
- Đọc trực tiếp bảng của schema module khác (qua SQL join)
- Ghi trực tiếp vào bảng của schema module khác
- Tạo FK tham chiếu sang bảng của module khác (trừ public.cong_chuc)

NGOẠI LỆ cho phép FK:
- Tất cả module → public.cong_chuc(id)     ✅
- Tất cả module → public.don_vi(id)        ✅
- Tất cả module → public.platform_role(id)  ✅

MỌI trao đổi dữ liệu khác → qua Internal API (xem API_CONTRACT)
```

### Quy tắc #3: Dữ liệu cross-module lưu dạng JSONB ID reference

```sql
-- ✅ ĐÚNG: Lưu IDs tham chiếu dưới dạng JSONB
van_ban_lien_quan JSONB   -- ["uuid-vb-1", "uuid-vb-2"]
sop_lien_quan JSONB       -- ["uuid-sop-1"]

-- ❌ SAI: Tạo FK trực tiếp sang schema khác
van_ban_id UUID REFERENCES legal.van_ban(id)  -- KHÔNG ĐƯỢC
```

Khi cần hiển thị thông tin chi tiết → gọi Internal API.

---

## II. QUY TẮC XÁC THỰC & PHÂN QUYỀN

### 2.1. SSO — Một lần đăng nhập, dùng mọi module

```
Luồng xác thực:
1. CBCC đăng nhập → POST /api/v1/auth/login (KPI backend port 8000)
2. Nhận JWT access_token + refresh_token
3. Frontend gửi JWT trong header cho TẤT CẢ module:
   - /api/v1/kpi/*    → KPI backend (8000) validate JWT
   - /api/v1/lms/*    → LMS backend (8001) validate JWT
   - /api/v1/forum/*  → Forum backend (8002) validate JWT
   - /api/v1/legal/*  → Legal backend (8003) validate JWT
   - /api/v1/common/* → Common backend validate JWT

4. Mỗi backend validate JWT bằng CÙNG SECRET_KEY
```

### 2.2. JWT payload mở rộng

```json
{
  "sub": "uuid-cong-chuc",
  "ma_cc": "20ZZ-0224",
  "ho_ten": "Nguyễn Văn A",
  "vai_tro": "CONG_CHUC",
  "don_vi_id": "uuid-don-vi",
  "is_lanh_dao": false,
  "platform_roles": ["GIANG_VIEN"],   // ← MỚI: vai trò bổ sung
  "exp": 1234567890
}
```

### 2.3. Phân quyền 2 lớp

```
Lớp 1: Vai trò KPI (vai_tro) — quyết định quyền trong module KPI
  SUPER_ADMIN > CHI_CUC_TRUONG > PHO_CHI_CUC_TRUONG >
  TRUONG_DON_VI > PHO_DON_VI > CONG_CHUC > TCCB

Lớp 2: Vai trò Platform (platform_roles) — quyết định quyền trong module mới
  GIANG_VIEN, QT_DAO_TAO, BIEN_TAP, DIEU_PHOI_FORUM,
  CHUYEN_GIA, QT_NOI_DUNG, QT_ATTT

Quy tắc:
- 1 CBCC có chính xác 1 vai_tro KPI
- 1 CBCC có thể có 0 → nhiều platform_roles
- Lãnh đạo (is_lanh_dao=TRUE) tự động có quyền XEM báo cáo đơn vị ở TẤT CẢ module
- SUPER_ADMIN có TOÀN QUYỀN ở tất cả module
```

### 2.4. Bảng phân quyền theo module

| Hành động | CBCC | Giảng viên | QT Đào tạo | Biên tập | Điều phối | Chuyên gia | Lãnh đạo | Admin |
|-----------|------|-----------|-----------|----------|----------|-----------|---------|-------|
| **LMS** |
| Xem/Đăng ký khóa học | ✅ | ✅ | ✅ | — | — | — | ✅ | ✅ |
| Tạo/sửa khóa học | — | ✅ | ✅ | — | — | — | — | ✅ |
| Giao bài bắt buộc | — | — | ✅ | — | — | — | ✅ | ✅ |
| Xem báo cáo đơn vị | — | — | ✅ | — | — | — | ✅ | ✅ |
| **Forum** |
| Đặt câu hỏi/trả lời | ✅ | ✅ | — | — | ✅ | ✅ | ✅ | ✅ |
| Ghim/Khóa/Chọn đáp án | — | — | — | — | ✅ | — | — | ✅ |
| Tạo SOP từ bài viết | — | — | — | — | ✅ | ✅ | — | ✅ |
| **Legal** |
| Xem VB / Xác nhận đọc | ✅ | — | — | ✅ | — | — | ✅ | ✅ |
| Soạn/Nhập văn bản | — | — | — | ✅ | — | — | — | ✅ |
| Duyệt xuất bản VB | — | — | — | — | — | — | ✅ | ✅ |
| Xem báo cáo đã đọc | — | — | — | — | — | — | ✅ | ✅ |
| **Portal** |
| Soạn tin tức | — | — | — | ✅ | — | — | — | ✅ |
| Duyệt đăng tin | — | — | — | — | — | — | ✅ | ✅ |

---

## III. QUY TẮC DATABASE

### 3.1. Naming convention

```
Bảng:       snake_case, tiếng Việt không dấu
                bai_hoc, khoa_hoc, van_ban, chu_de
Cột:        snake_case, tiếng Việt không dấu
                tieu_de, ngay_tao, trang_thai
Primary Key: id UUID DEFAULT gen_random_uuid()
FK user:     cong_chuc_id UUID REFERENCES public.cong_chuc(id)
FK đơn vị:   don_vi_id UUID REFERENCES public.don_vi(id)
Timestamp:   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
Soft delete: is_deleted BOOLEAN DEFAULT FALSE
ENUM dạng:   VARCHAR + comment (KHÔNG dùng PostgreSQL ENUM type)
```

### 3.2. Migration rules

```
1. Mỗi module tự viết migration cho schema của mình
2. Migration PHẢI có upgrade() VÀ downgrade()
3. KHÔNG BAO GIỜ viết migration sửa bảng schema public.*
   (trừ THÊM platform_role, cong_chuc_platform_role)
4. Test migration trên DB riêng trước
5. Gửi migration cho Tech Lead review
6. Tech Lead chạy migration trên production (sau khi backup)
7. KHÔNG tự chạy migration trên production
```

### 3.3. Seed data rules

```
- Dữ liệu danh mục (loai_van_ban, chuyen_muc) → migration hoặc seed script
- Dữ liệu test → seed script riêng, KHÔNG nhúng vào migration
- TUYỆT ĐỐI KHÔNG seed vào bảng public.cong_chuc (dữ liệu production thật)
```

---

## IV. QUY TẮC BACKEND SERVICE

### 4.1. Cấu trúc mỗi service

```
{module}_service/
├── main.py                     # FastAPI app + CORS + lifespan
├── config.py                   # Đọc .env, SECRET_KEY
├── dependencies.py             # JWT decode, get_current_user
├── models/                     # SQLAlchemy models (CHỈ schema của mình)
├── schemas/                    # Pydantic v2 request/response
├── api/
│   ├── endpoints/              # External API (cho Frontend)
│   └── internal/               # Internal API (cho module khác)
├── services/                   # Business logic
└── utils/                      # Helpers
```

### 4.2. Shared configuration

Tất cả service đọc cùng file `.env` hoặc cùng biến môi trường:

```env
# Database (CHUNG)
DATABASE_URL=postgresql://kpi_user:password@localhost:5432/kpi_haiquan

# JWT (CHUNG — phải giống KPI)
SECRET_KEY=same-as-kpi-backend
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# MinIO (CHUNG)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=xxx
MINIO_SECRET_KEY=xxx
MINIO_BUCKET=kv08-files

# Redis (CHUNG)
REDIS_URL=redis://localhost:6379/0

# Internal API key
INTERNAL_API_KEY=shared-secret-between-services
```

### 4.3. Dependency: get_current_user

Mỗi service copy (hoặc import) hàm decode JWT giống nhau:

```python
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return {
        "id": payload["sub"],
        "ma_cc": payload["ma_cc"],
        "vai_tro": payload["vai_tro"],
        "don_vi_id": payload["don_vi_id"],
        "is_lanh_dao": payload.get("is_lanh_dao", False),
        "platform_roles": payload.get("platform_roles", [])
    }
```

---

## V. QUY TẮC FRONTEND

### 5.1. Routing

```
Tất cả module dùng CHUNG 1 Next.js app (port 3000).
Không tạo app riêng cho mỗi module.

src/app/(dashboard)/
├── dashboard/        ← Tổng hợp (widget từ mỗi module)
├── ke-khai/          ← KPI (GIỮ NGUYÊN)
├── phe-duyet/        ← KPI (GIỮ NGUYÊN)
├── danh-gia/         ← KPI (GIỮ NGUYÊN)
├── xep-loai/         ← KPI (GIỮ NGUYÊN)
├── nghi-phep/        ← KPI (GIỮ NGUYÊN)
├── dao-tao/          ← LMS (MỚI)
├── dien-dan/         ← Forum (MỚI)
├── phap-luat/        ← Legal (MỚI)
├── tai-lieu/         ← Portal ECM (MỚI)
├── thong-bao/        ← Common (MỚI)
└── admin/            ← Mở rộng
```

### 5.2. API service layer

```typescript
// Mỗi module có 1 file service riêng
// src/services/lms.ts → gọi /api/v1/lms/*
// src/services/forum.ts → gọi /api/v1/forum/*
// src/services/legal.ts → gọi /api/v1/legal/*

// Base URL config:
const API_URLS = {
  KPI: '/api/v1',           // proxy → port 8000
  LMS: '/api/v1/lms',       // proxy → port 8001
  FORUM: '/api/v1/forum',   // proxy → port 8002
  LEGAL: '/api/v1/legal',   // proxy → port 8003
  COMMON: '/api/v1/common',
};
```

### 5.3. Sidebar navigation (thêm module mới)

```
Quy tắc: Sửa 1 file layout duy nhất để thêm menu.
KHÔNG sửa component sidebar hiện tại — THÊM items mới.

Thứ tự sidebar:
1. Tổng quan (dashboard mới)
2. KPI & Thi đua (giữ nguyên menu cũ)
3. Đào tạo
4. Diễn đàn
5. Pháp luật
6. Tài liệu
7. Thông báo
8. Quản trị
```

---

## VI. QUY TẮC NOTIFICATION

### 6.1. Khi nào phải gửi notification

| Event | Module | Mức độ | Người nhận |
|-------|--------|--------|-----------|
| Giao khóa bắt buộc | LMS | QUAN_TRONG | CBCC được giao |
| Hoàn thành khóa | LMS | BINH_THUONG | CBCC + Lãnh đạo ĐV |
| Sắp hết hạn khóa (3 ngày) | LMS | QUAN_TRONG | CBCC |
| Trả lời mới cho chủ đề | Forum | BINH_THUONG | Tác giả + Người theo dõi |
| Bài được chọn đáp án chuẩn | Forum | BINH_THUONG | Tác giả trả lời |
| VB mới xuất bản (bắt buộc) | Legal | KHAN/QUAN_TRONG | Theo doi_tuong_ap_dung |
| Sắp hết hạn xác nhận VB | Legal | KHAN | CBCC chưa xác nhận |
| Tin tức mới | Portal | BINH_THUONG | Tất cả |

### 6.2. Format notification

```
Tieu_de: ngắn gọn, rõ ràng (<100 ký tự)
Noi_dung: chi tiết hơn nếu cần (<300 ký tự)
Link_url: đường dẫn frontend để click vào
```

---

## VII. QUY TẮC KPI INTEGRATION

### 7.1. Dữ liệu từ module mới → KPI = THAM KHẢO

```
⚠️ NGUYÊN TẮC VÀNG:
Dữ liệu từ LMS/Forum/Legal ghi vào common.kpi_integration_log
→ Hiển thị BÊN CẠNH kết quả KPI trên Dashboard
→ Lãnh đạo THAM KHẢO khi phê duyệt điểm
→ KHÔNG TỰ ĐỘNG thay đổi điểm KPI

Lý do: Điểm KPI tính theo công thức (a+b+c)/3 × 70 + TC chung (30đ)
  đã được Quy chế quy định. Thêm yếu tố mới cần sửa Quy chế trước.
```

### 7.2. Metrics format cho từng module

Xem chi tiết trong `common.kpi_integration_log.metrics` tại file PORTAL_COMMON_DATABASE_DESIGN.md.

### 7.3. Thời điểm sync

```
- LMS: Ghi ngay khi CBCC hoàn thành khóa + Cron cuối tháng tổng hợp
- Forum: Cron cuối tháng (đếm bài/trả lời/upvote trong tháng)
- Legal: Cron cuối tháng (đếm VB đã đọc, quiz đã làm)
```

---

## VIII. QUY TẮC DEPLOY & VẬN HÀNH

### 8.1. Port allocation

| Service | Port | PM2 name |
|---------|------|----------|
| KPI Backend | 8000 | kpi-backend |
| LMS Backend | 8001 | lms-backend |
| Forum Backend | 8002 | forum-backend |
| Legal Backend | 8003 | legal-backend |
| Frontend | 3000 | kpi-frontend |
| Redis | 6379 | — |
| MinIO | 9000 (API), 9001 (Console) | — |
| PostgreSQL | 5432 | — |

### 8.2. Nginx routing

```nginx
server {
    listen 80;
    server_name kv08.vn;

    # Frontend (giữ nguyên)
    location / {
        proxy_pass http://localhost:3000;
    }

    # KPI API (giữ nguyên)
    location /api/v1/auth/ {
        proxy_pass http://localhost:8000;
    }
    location /api/v1/kpi/ {
        proxy_pass http://localhost:8000;
    }

    # LMS API (mới)
    location /api/v1/lms/ {
        proxy_pass http://localhost:8001;
    }

    # Forum API (mới)
    location /api/v1/forum/ {
        proxy_pass http://localhost:8002;
    }

    # Legal API (mới)
    location /api/v1/legal/ {
        proxy_pass http://localhost:8003;
    }

    # Common API
    location /api/v1/common/ {
        proxy_pass http://localhost:8001;  # hoặc service riêng
    }

    # Block Internal API từ bên ngoài
    location /internal/ {
        deny all;
        return 403;
    }
}
```

### 8.3. Deploy quy trình

```
1. Developer push code → branch feature/[module]-xxx
2. Tech Lead review → merge vào develop
3. Test trên develop (port test)
4. Tech Lead merge develop → main
5. SSH vào VPS → git pull → pm2 restart [service]
6. Kiểm tra logs → pm2 logs [service] --lines 20
```
