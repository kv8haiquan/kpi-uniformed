# SHARED_AUTH_SPECS.md
## Đặc tả Xác thực & Phân quyền — Nền tảng Số Thống nhất HQKV8

> **Phiên bản:** 1.0.0 | **Ngày:** 18/02/2026  
> **Kiến trúc sư trưởng:** Architect Team  
> **Áp dụng cho:** TẤT CẢ module (LMS, Forum, Legal, Portal, Common)  
> **Tham chiếu:** CHIEN_LUOC_NEN_TANG_THONG_NHAT.md, API_SPECS_v1_8_0.md, DATABASE_DESIGN_v2_8_0.md

---

## 1. NGUYÊN TẮC BẤT DI BẤT DỊCH

```
╔══════════════════════════════════════════════════════════════════╗
║  ⛔ KHÔNG sửa/xóa/thêm cột vào bảng: cong_chuc, vai_tro       ║
║  ⛔ KHÔNG sửa code backend KPI (port 8000)                      ║
║  ⛔ KHÔNG thay đổi login flow hiện tại (/api/v1/auth/login)     ║
║  ✅ CHỈ ĐỌC bảng cong_chuc, vai_tro, don_vi                    ║
║  ✅ THÊM bảng platform_role, cong_chuc_platform_role vào public ║
║  ✅ MỞ RỘNG JWT payload (thêm field, không xóa field cũ)        ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 2. HỆ THỐNG XÁC THỰC HIỆN TẠI (GIỮ NGUYÊN)

### 2.1. Thông số JWT hiện tại

| Thông số | Giá trị |
|----------|---------|
| **Algorithm** | HS256 |
| **Access Token TTL** | 30 phút |
| **Refresh Token TTL** | 7 ngày |
| **Login Endpoint** | `POST /api/v1/auth/login` |
| **Header** | `Authorization: Bearer <token>` |
| **Username** | Mã CBCC (VD: `20ZZ-0224`) hoặc `admin` |

### 2.2. JWT Payload hiện tại (GIỮ NGUYÊN — chỉ THÊM field mới)

```json
{
  "sub": "uuid-cong-chuc-id",
  "ma_cc": "20ZZ-0224",
  "vai_tro": "CONG_CHUC",
  "don_vi_id": "uuid-don-vi",
  "exp": 1708300000
}
```

### 2.3. RBAC hiện tại — 7 vai trò KPI

| Thứ tự | Mã vai trò | Tên | is_lanh_dao |
|--------|-----------|-----|-------------|
| 1 | `SUPER_ADMIN` | Admin hệ thống | ✅ |
| 2 | `CHI_CUC_TRUONG` | Chi cục trưởng | ✅ |
| 3 | `PHO_CHI_CUC_TRUONG` | Phó Chi cục trưởng | ✅ |
| 4 | `TRUONG_DON_VI` | Trưởng đơn vị | ✅ |
| 5 | `PHO_DON_VI` | Phó đơn vị | ✅ |
| 6 | `CONG_CHUC` | Công chức | ❌ |
| 7 | `TCCB` | Tổ chức cán bộ | ❌ |

---

## 3. MỞ RỘNG SSO CHO NỀN TẢNG MỚI

### 3.1. JWT Payload mở rộng

```json
{
  "sub": "uuid-cong-chuc-id",
  "ma_cc": "20ZZ-0224",
  "vai_tro": "CONG_CHUC",
  "don_vi_id": "uuid-don-vi",
  "is_lanh_dao": false,

  "platform_roles": ["GIANG_VIEN", "DIEU_PHOI_FORUM"],

  "exp": 1708300000,
  "iat": 1708298200,
  "iss": "kv08.vn"
}
```

> **Quy tắc:** Field `platform_roles` là **mảng rỗng** `[]` nếu user không có vai trò nền tảng bổ sung. Tất cả field cũ (`sub`, `ma_cc`, `vai_tro`, `don_vi_id`) GIỮA NGUYÊN — KHÔNG ĐỔI TÊN, KHÔNG XÓA.

### 3.2. Bảng platform_role (MỚI — schema public)

```sql
CREATE TABLE public.platform_role (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ma_role VARCHAR(50) NOT NULL UNIQUE,      -- Mã enum
    ten_role VARCHAR(100) NOT NULL,            -- Tên hiển thị
    mo_ta TEXT,                                -- Mô tả chức năng
    quyen_han JSONB DEFAULT '{}',             -- Chi tiết quyền
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Dữ liệu seed:**

| ma_role | ten_role | Mô tả | Module liên quan |
|---------|----------|-------|-----------------|
| `GIANG_VIEN` | Giảng viên kiêm nhiệm | Tạo/quản lý khóa học, bài giảng | LMS |
| `QT_DAO_TAO` | Quản trị đào tạo | Quản lý toàn bộ module LMS | LMS |
| `BIEN_TAP` | Biên tập viên | Soạn/duyệt tin tức, văn bản PL | Legal, Portal |
| `DIEU_PHOI_FORUM` | Điều phối diễn đàn | Ghim/khóa chủ đề, chọn đáp án chuẩn | Forum |
| `CHUYEN_GIA` | Chuyên gia nghiệp vụ | Trả lời chuyên sâu, tạo SOP/FAQ | Forum, Common |
| `QT_NOI_DUNG` | Quản trị nội dung | Quản lý portal, thư viện tài liệu | Portal |
| `QT_ATTT` | Quản trị ATTT | Bảo mật, kiểm thử, audit | ALL |

### 3.3. Bảng cong_chuc_platform_role (MỚI — schema public)

```sql
CREATE TABLE public.cong_chuc_platform_role (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cong_chuc_id UUID NOT NULL REFERENCES public.cong_chuc(id),
    platform_role_id UUID NOT NULL REFERENCES public.platform_role(id),
    pham_vi JSONB,            -- Phạm vi áp dụng
    assigned_by UUID REFERENCES public.cong_chuc(id),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE (cong_chuc_id, platform_role_id)
);
```

**Ví dụ `pham_vi`:**
```json
{
  "don_vi_ids": ["uuid-doi-1", "uuid-doi-2"],
  "chuyen_de_ids": ["uuid-cd-hai-quan"],
  "chuyen_muc_ids": ["uuid-cm-thue"]
}
```

---

## 4. HƯỚNG DẪN TÍCH HỢP CHO TỪNG MODULE

### 4.1. Cách lấy thông tin user hiện tại

Mọi module PHẢI sử dụng chung **dependency injection** sau:

```python
# File: shared/dependencies/auth.py
# Tất cả module import từ đây

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()
SECRET_KEY = "..."  # Đọc từ biến môi trường PLATFORM_SECRET_KEY
ALGORITHM = "HS256"


class CurrentUser:
    """Thông tin user đã xác thực — READONLY."""
    def __init__(self, payload: dict):
        self.id: str = payload["sub"]
        self.ma_cc: str = payload["ma_cc"]
        self.vai_tro: str = payload["vai_tro"]          # Vai trò KPI (GIỮ NGUYÊN)
        self.don_vi_id: str = payload["don_vi_id"]
        self.is_lanh_dao: bool = payload.get("is_lanh_dao", False)
        # MỚI — Platform roles
        self.platform_roles: list[str] = payload.get("platform_roles", [])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """Dependency chung — decode JWT và trả về CurrentUser."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return CurrentUser(payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token đã hết hạn"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ"
        )
```

### 4.2. Cách kiểm tra quyền trong router

```python
# --- Kiểm tra vai trò KPI (cho chức năng liên quan KPI) ---
def require_kpi_role(*roles: str):
    """Yêu cầu vai trò KPI cụ thể."""
    async def checker(user: CurrentUser = Depends(get_current_user)):
        if user.vai_tro not in roles:
            raise HTTPException(status_code=403, detail="Không có quyền")
        return user
    return checker

# Sử dụng:
@router.get("/bao-cao")
async def get_bao_cao(user=Depends(require_kpi_role("CHI_CUC_TRUONG", "TCCB"))):
    ...


# --- Kiểm tra vai trò Platform (cho chức năng module mới) ---
def require_platform_role(*roles: str):
    """Yêu cầu platform role bổ sung."""
    async def checker(user: CurrentUser = Depends(get_current_user)):
        if not any(r in user.platform_roles for r in roles):
            # Fallback: SUPER_ADMIN luôn có quyền
            if user.vai_tro != "SUPER_ADMIN":
                raise HTTPException(status_code=403, detail="Không có quyền nền tảng")
        return user
    return checker

# Sử dụng:
@router.post("/khoa-hoc")
async def tao_khoa_hoc(user=Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO"))):
    ...


# --- Kiểm tra kết hợp (vai trò KPI HOẶC platform role) ---
def require_any_role(kpi_roles: list[str] = None, platform_roles: list[str] = None):
    """Cho phép nếu có BẤT KỲ vai trò nào phù hợp."""
    async def checker(user: CurrentUser = Depends(get_current_user)):
        has_kpi = kpi_roles and user.vai_tro in kpi_roles
        has_platform = platform_roles and any(r in user.platform_roles for r in platform_roles)
        if not has_kpi and not has_platform and user.vai_tro != "SUPER_ADMIN":
            raise HTTPException(status_code=403, detail="Không có quyền")
        return user
    return checker
```

### 4.3. Hàm helper tạo JWT mở rộng

```python
# File: shared/core/security.py
# Chỉ được gọi từ Auth Service — KHÔNG gọi từ module khác

from datetime import datetime, timedelta
from sqlalchemy import select
from models import CongChucPlatformRole, PlatformRole

def get_platform_roles(db, cong_chuc_id: str) -> list[str]:
    """Lấy danh sách platform_role.ma_role của user."""
    stmt = (
        select(PlatformRole.ma_role)
        .join(CongChucPlatformRole)
        .where(
            CongChucPlatformRole.cong_chuc_id == cong_chuc_id,
            CongChucPlatformRole.is_active == True,
            PlatformRole.is_active == True
        )
    )
    result = db.execute(stmt).scalars().all()
    return list(result)


def create_access_token(cong_chuc, db) -> str:
    """Tạo JWT với payload mở rộng."""
    payload = {
        # --- GIỮ NGUYÊN (backward compatible) ---
        "sub": str(cong_chuc.id),
        "ma_cc": cong_chuc.ma_cc,
        "vai_tro": cong_chuc.vai_tro.ma_vai_tro,
        "don_vi_id": str(cong_chuc.don_vi_id),
        # --- THÊM MỚI ---
        "is_lanh_dao": cong_chuc.is_lanh_dao,
        "platform_roles": get_platform_roles(db, cong_chuc.id),
        # --- Timestamps ---
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "iss": "kv08.vn"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
```

---

## 5. MA TRẬN PHÂN QUYỀN THEO MODULE

### 5.1. Module LMS (schema: lms)

| Chức năng | CONG_CHUC | GIANG_VIEN | QT_DAO_TAO | SUPER_ADMIN |
|-----------|:---------:|:----------:|:----------:|:-----------:|
| Xem danh sách khóa học | ✅ | ✅ | ✅ | ✅ |
| Đăng ký khóa học | ✅ | ✅ | ✅ | ✅ |
| Học bài / Làm bài kiểm tra | ✅ | ✅ | ✅ | ✅ |
| Tạo/sửa khóa học | ❌ | ✅ | ✅ | ✅ |
| Tạo câu hỏi / bài kiểm tra | ❌ | ✅ | ✅ | ✅ |
| Giao khóa học bắt buộc | ❌ | ❌ | ✅ | ✅ |
| Xem báo cáo toàn bộ LMS | ❌ | ❌ | ✅ | ✅ |
| Duyệt khóa học | ❌ | ❌ | ✅ | ✅ |

### 5.2. Module Forum (schema: forum)

| Chức năng | CONG_CHUC | CHUYEN_GIA | DIEU_PHOI_FORUM | SUPER_ADMIN |
|-----------|:---------:|:----------:|:---------------:|:-----------:|
| Xem chủ đề | ✅ | ✅ | ✅ | ✅ |
| Tạo chủ đề | ✅ | ✅ | ✅ | ✅ |
| Trả lời / Bình luận | ✅ | ✅ | ✅ | ✅ |
| Upvote/Downvote | ✅ | ✅ | ✅ | ✅ |
| Đánh dấu đáp án chuẩn | ❌ | ✅ | ✅ | ✅ |
| Ghim / Khóa chủ đề | ❌ | ❌ | ✅ | ✅ |
| Ẩn / Xóa bài | ❌ | ❌ | ✅ | ✅ |
| Duyệt bài (nếu yêu cầu) | ❌ | ❌ | ✅ | ✅ |

### 5.3. Module Legal (schema: legal)

| Chức năng | CONG_CHUC | BIEN_TAP | Lãnh đạo (KPI) | SUPER_ADMIN |
|-----------|:---------:|:--------:|:--------------:|:-----------:|
| Xem văn bản đã xuất bản | ✅ | ✅ | ✅ | ✅ |
| Xác nhận đã đọc | ✅ | ✅ | ✅ | ✅ |
| Làm quiz pháp luật | ✅ | ✅ | ✅ | ✅ |
| Soạn / nhập văn bản | ❌ | ✅ | ❌ | ✅ |
| Duyệt / xuất bản VB | ❌ | ❌ | ✅ | ✅ |
| Xem dashboard xác nhận đọc | ❌ | ✅ | ✅ | ✅ |
| Tạo quiz pháp luật | ❌ | ✅ | ❌ | ✅ |

### 5.4. Module Portal (schema: portal)

| Chức năng | CONG_CHUC | QT_NOI_DUNG | BIEN_TAP | SUPER_ADMIN |
|-----------|:---------:|:-----------:|:--------:|:-----------:|
| Xem tin tức / tài liệu | ✅ | ✅ | ✅ | ✅ |
| Soạn bài viết | ❌ | ✅ | ✅ | ✅ |
| Duyệt / xuất bản bài viết | ❌ | ✅ | ❌ | ✅ |
| Quản lý thư viện tài liệu | ❌ | ✅ | ❌ | ✅ |
| Upload tài liệu | ❌ | ✅ | ✅ | ✅ |

---

## 6. API ENDPOINT CONVENTION CHO AUTH

### 6.1. Các endpoint module mới PHẢI tuân theo

```
Base URLs:
  KPI (giữ nguyên):  https://kv08.vn/api/v1/...         → port 8000
  LMS:               https://kv08.vn/api/lms/v1/...      → port 8001
  Forum:             https://kv08.vn/api/forum/v1/...     → port 8002
  Legal:             https://kv08.vn/api/legal/v1/...     → port 8003
  Portal:            https://kv08.vn/api/portal/v1/...    → port 8004
  Common:            https://kv08.vn/api/common/v1/...    → port 8005
```

### 6.2. Response format lỗi xác thực

```json
// 401 — Chưa đăng nhập hoặc token hết hạn
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Token đã hết hạn. Vui lòng đăng nhập lại."
  }
}

// 403 — Không có quyền
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Bạn không có quyền thực hiện thao tác này.",
    "required_roles": ["GIANG_VIEN", "QT_DAO_TAO"]
  }
}
```

### 6.3. Header bắt buộc cho mọi request đã xác thực

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json
Accept: application/json
```

---

## 7. LUỒNG XÁC THỰC END-TO-END

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Browser   │     │  Nginx Proxy │     │  KPI Backend │
│  (Next.js)  │     │  (Gateway)   │     │  (port 8000) │
└──────┬──────┘     └──────┬───────┘     └──────┬───────┘
       │                   │                     │
       │  1. POST /api/v1/auth/login             │
       │──────────────────►│────────────────────►│
       │                   │                     │
       │                   │    JWT (mở rộng)    │
       │◄──────────────────│◄────────────────────│
       │                   │                     │
       │  2. GET /api/lms/v1/khoa-hoc            │
       │  Authorization: Bearer <JWT>            │
       │──────────────────►│                     │
       │                   │                     │
       │                   │  ┌──────────────┐   │
       │                   │  │ LMS Backend  │   │
       │                   │──│ (port 8001)  │   │
       │                   │  │              │   │
       │                   │  │ Decode JWT   │   │
       │                   │  │ Check roles  │   │
       │                   │  │ Return data  │   │
       │                   │  └──────────────┘   │
       │                   │                     │
       │   Response data   │                     │
       │◄──────────────────│                     │
```

**Quan trọng:**
- Bước 1 (Login) luôn đi qua KPI Backend (port 8000) — KHÔNG ĐỔI
- Bước 2+ (API calls) đi đến module tương ứng — Nginx routing
- Mỗi module TỰ decode JWT, KHÔNG gọi lại KPI Backend để verify

---

## 8. CHECKLIST CHO DEV KHI TÍCH HỢP AUTH

```
□ Import get_current_user từ shared/dependencies/auth.py
□ Sử dụng CurrentUser (KHÔNG tự decode JWT)
□ Kiểm tra vai_tro (KPI) HOẶC platform_roles tùy chức năng
□ SUPER_ADMIN luôn bypass mọi kiểm tra quyền
□ Trả về 401 khi token thiếu/hết hạn
□ Trả về 403 khi không đủ quyền (kèm required_roles)
□ KHÔNG lưu password, KHÔNG hash token
□ KHÔNG gọi API KPI backend để verify user
□ Log audit khi thao tác quan trọng (tạo/sửa/xóa)
□ Test với các vai trò: CONG_CHUC, lãnh đạo, platform_role, SUPER_ADMIN
```

---

> **Liên hệ:** Mọi thắc mắc về Auth/SSO → Kiến trúc sư trưởng  
> **Cập nhật:** File này được quản lý tập trung. KHÔNG fork/copy riêng.
