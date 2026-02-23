# SHARED_CODING_STANDARDS.md
## Chuẩn Code & Quy ước Phát triển — Nền tảng Số Thống nhất HQKV8

> **Phiên bản:** 1.0.0 | **Ngày:** 18/02/2026  
> **Kiến trúc sư trưởng:** Architect Team  
> **Áp dụng cho:** TẤT CẢ dev team (Dev A → Dev E)  
> **Tech Stack:** FastAPI + SQLAlchemy 2.0 + Pydantic v2 + Next.js + TypeScript

---

## 1. TECH STACK BẮT BUỘC

| Layer | Công nghệ | Phiên bản | Ghi chú |
|-------|----------|-----------|---------|
| **Backend** | Python + FastAPI | 3.11+ / 0.100+ | Mỗi module = 1 FastAPI app riêng |
| **ORM** | SQLAlchemy | 2.0+ | Async session, mapped_column |
| **Validation** | Pydantic | v2 | model_validator, ConfigDict |
| **Database** | PostgreSQL | 15 | Multi-schema, pg_tsvector |
| **Migration** | Alembic | 1.12+ | upgrade() + downgrade() bắt buộc |
| **Frontend** | Next.js + TypeScript | 14+ | App Router, Server Components |
| **Cache** | Redis | 7+ | Session, queue, realtime |
| **File Storage** | MinIO | S3-compatible | Video, PDF, tài liệu |
| **Process Manager** | PM2 | latest | Multi-service management |

---

## 2. CẤU TRÚC PROJECT CHUẨN

### 2.1. Backend — Mỗi module

```
{module}-service/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app + lifespan
│   ├── config.py                  # Cấu hình từ biến môi trường
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                # Dependencies (auth, db session)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py          # Include tất cả routers
│   │       ├── khoa_hoc.py        # Endpoints khóa học
│   │       ├── bai_hoc.py         # Endpoints bài học
│   │       └── ...
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                # Base model + shared models
│   │   ├── khoa_hoc.py            # SQLAlchemy models
│   │   └── ...
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py              # Response schemas chung
│   │   ├── khoa_hoc.py            # Pydantic schemas
│   │   └── ...
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── khoa_hoc_service.py    # Business logic
│   │   └── ...
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py            # DB engine + session
│   │   └── security.py            # Auth dependencies
│   │
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
│
├── migrations/                     # Alembic migrations
│   ├── env.py
│   └── versions/
│
├── tests/
│   ├── conftest.py
│   ├── test_khoa_hoc.py
│   └── ...
│
├── alembic.ini
├── requirements.txt
├── Dockerfile
└── README.md
```

### 2.2. Frontend — Shared trong cùng Next.js app

```
frontend/
├── src/
│   ├── app/
│   │   ├── (kpi)/                 # Route group KPI (GIỮ NGUYÊN)
│   │   ├── (lms)/                 # Route group LMS
│   │   │   ├── dao-tao/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/page.tsx
│   │   │   └── layout.tsx
│   │   ├── (forum)/               # Route group Forum
│   │   ├── (legal)/               # Route group Legal
│   │   ├── (portal)/              # Route group Portal
│   │   └── layout.tsx             # Root layout (sidebar mới)
│   │
│   ├── components/
│   │   ├── shared/                # Components dùng chung
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── DataTable.tsx
│   │   │   └── ...
│   │   ├── lms/                   # Components riêng LMS
│   │   ├── forum/                 # Components riêng Forum
│   │   └── ...
│   │
│   ├── lib/
│   │   ├── api.ts                 # API client chung
│   │   ├── auth.ts                # Auth helpers
│   │   └── utils.ts
│   │
│   └── types/
│       ├── common.ts              # Types dùng chung
│       ├── lms.ts
│       └── ...
```

---

## 3. QUY ƯỚC CODE BACKEND (PYTHON)

### 3.1. Comment tiếng Việt

```python
# ✅ ĐÚNG — Comment tiếng Việt cho logic nghiệp vụ
class KhoaHocService:
    """Service xử lý logic khóa học."""
    
    async def tao_khoa_hoc(self, data: KhoaHocCreate, user: CurrentUser):
        """Tạo khóa học mới.
        
        Quy tắc:
        - Chỉ GIANG_VIEN hoặc QT_DAO_TAO mới được tạo
        - Mã khóa học tự sinh theo format: KH-{năm}-{số tự tăng}
        - Trạng thái mặc định: NHAP
        """
        # Kiểm tra quyền tạo khóa học
        if not self._co_quyen_tao(user):
            raise HTTPException(status_code=403, detail="Không có quyền tạo khóa học")
        
        # Sinh mã khóa học tự động
        ma_khoa_hoc = await self._sinh_ma_khoa_hoc()
        
        # Tạo bản ghi trong database
        khoa_hoc = KhoaHoc(
            ma_khoa_hoc=ma_khoa_hoc,
            ten_khoa_hoc=data.ten_khoa_hoc,
            giang_vien_id=user.id,      # Người tạo = giảng viên
            trang_thai="NHAP"
        )
        ...
```

### 3.2. FastAPI Router pattern

```python
# File: app/api/v1/khoa_hoc.py

from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_user, get_db
from app.schemas.khoa_hoc import KhoaHocCreate, KhoaHocUpdate, KhoaHocResponse
from app.schemas.common import SuccessResponse, PaginatedResponse
from app.services.khoa_hoc_service import KhoaHocService

router = APIRouter(prefix="/khoa-hoc", tags=["Khóa học"])


@router.get("", response_model=PaginatedResponse)
async def danh_sach_khoa_hoc(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    trang_thai: Optional[str] = None,
    chuyen_de_id: Optional[UUID] = None,
    search: Optional[str] = None,
    db=Depends(get_db),
    user=Depends(get_current_user)
):
    """Lấy danh sách khóa học có phân trang."""
    service = KhoaHocService(db)
    result = await service.danh_sach(
        page=page,
        page_size=page_size,
        trang_thai=trang_thai,
        chuyen_de_id=chuyen_de_id,
        search=search,
        user=user
    )
    return result


@router.post("", response_model=SuccessResponse, status_code=201)
async def tao_khoa_hoc(
    data: KhoaHocCreate,
    db=Depends(get_db),
    user=Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO"))
):
    """Tạo khóa học mới. Yêu cầu: GIANG_VIEN hoặc QT_DAO_TAO."""
    service = KhoaHocService(db)
    khoa_hoc = await service.tao_khoa_hoc(data, user)
    return SuccessResponse(
        data=KhoaHocResponse.model_validate(khoa_hoc),
        message="Tạo khóa học thành công"
    )


@router.get("/{khoa_hoc_id}", response_model=SuccessResponse)
async def chi_tiet_khoa_hoc(
    khoa_hoc_id: UUID,
    db=Depends(get_db),
    user=Depends(get_current_user)
):
    """Chi tiết khóa học."""
    service = KhoaHocService(db)
    khoa_hoc = await service.chi_tiet(khoa_hoc_id, user)
    if not khoa_hoc:
        raise HTTPException(status_code=404, detail="Không tìm thấy khóa học")
    return SuccessResponse(data=KhoaHocResponse.model_validate(khoa_hoc))
```

### 3.3. Pydantic Schemas (v2)

```python
# File: app/schemas/common.py
# Schemas dùng chung cho TẤT CẢ module

from pydantic import BaseModel, ConfigDict
from typing import Any, Optional, Generic, TypeVar
from datetime import datetime
from uuid import UUID

T = TypeVar('T')


class SuccessResponse(BaseModel):
    """Response thành công chuẩn."""
    success: bool = True
    data: Any = None
    message: str = "Thao tác thành công"


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    """Response lỗi chuẩn."""
    success: bool = False
    error: dict  # {"code": "...", "message": "...", "details": [...]}


class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class PaginatedResponse(BaseModel):
    """Response có phân trang."""
    success: bool = True
    data: list = []
    pagination: PaginationInfo


# --- Base schemas cho các module ---

class BaseSchema(BaseModel):
    """Base schema với cấu hình chung."""
    model_config = ConfigDict(
        from_attributes=True,       # Cho phép tạo từ ORM model
        populate_by_name=True,
        str_strip_whitespace=True   # Tự động strip whitespace
    )


class TimestampMixin(BaseModel):
    """Mixin cho created_at, updated_at."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserBriefSchema(BaseSchema):
    """Thông tin user tóm tắt — dùng khi trả về kèm entity."""
    id: UUID
    ma_cc: str
    ho_ten: str
    chuc_vu: Optional[str] = None
    don_vi_ten: Optional[str] = None
```

```python
# File: app/schemas/khoa_hoc.py
# Ví dụ schema cho module LMS

from pydantic import Field
from typing import Optional
from datetime import date
from uuid import UUID
from .common import BaseSchema, TimestampMixin, UserBriefSchema


class KhoaHocCreate(BaseSchema):
    """Schema tạo khóa học mới."""
    ten_khoa_hoc: str = Field(..., min_length=1, max_length=300)
    mo_ta: Optional[str] = None
    chuyen_de_id: Optional[UUID] = None
    loai: str = Field(default="TU_HOC", pattern="^(TU_HOC|BAT_BUOC|TRUC_TUYEN|KET_HOP)$")
    thoi_luong_phut: Optional[int] = Field(None, ge=0)
    diem_dat_yeu_cau: float = Field(default=70.00, ge=0, le=100)
    ngay_bat_dau: Optional[date] = None
    ngay_ket_thuc: Optional[date] = None


class KhoaHocUpdate(BaseSchema):
    """Schema cập nhật khóa học."""
    ten_khoa_hoc: Optional[str] = Field(None, min_length=1, max_length=300)
    mo_ta: Optional[str] = None
    loai: Optional[str] = None
    trang_thai: Optional[str] = None


class KhoaHocResponse(BaseSchema, TimestampMixin):
    """Schema response khóa học."""
    id: UUID
    ma_khoa_hoc: str
    ten_khoa_hoc: str
    mo_ta: Optional[str] = None
    chuyen_de_id: Optional[UUID] = None
    loai: str
    trang_thai: str
    so_bai_hoc: int = 0
    thoi_luong_phut: Optional[int] = None
    diem_dat_yeu_cau: float
    giang_vien: Optional[UserBriefSchema] = None
```

### 3.4. SQLAlchemy Model (2.0 style)

```python
# File: app/models/base.py

from sqlalchemy import Column, Boolean, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
import uuid


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Mixin thêm created_at, updated_at cho mọi bảng."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow
    )


class SoftDeleteMixin:
    """Mixin soft delete."""
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
```

```python
# File: app/models/khoa_hoc.py (Ví dụ cho LMS)

from sqlalchemy import String, Integer, ForeignKey, Text, Date, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin, SoftDeleteMixin
from uuid import uuid4
from typing import Optional
from datetime import date


class KhoaHoc(Base, TimestampMixin):
    """Bảng khóa học — Schema: lms"""
    __tablename__ = "khoa_hoc"
    __table_args__ = {"schema": "lms"}   # ← CHỈ ĐỊNH SCHEMA
    
    id: Mapped[uuid4] = mapped_column(UUID, primary_key=True, default=uuid4)
    ma_khoa_hoc: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    ten_khoa_hoc: Mapped[str] = mapped_column(String(300), nullable=False)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text)
    chuyen_de_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID, ForeignKey("lms.chuyen_de.id")
    )
    loai: Mapped[str] = mapped_column(String(50), default="TU_HOC")
    trang_thai: Mapped[str] = mapped_column(String(50), default="NHAP")
    so_bai_hoc: Mapped[int] = mapped_column(Integer, default=0)
    thoi_luong_phut: Mapped[Optional[int]] = mapped_column(Integer)
    diem_dat_yeu_cau: Mapped[float] = mapped_column(Numeric(5, 2), default=70.00)
    ngay_bat_dau: Mapped[Optional[date]] = mapped_column(Date)
    ngay_ket_thuc: Mapped[Optional[date]] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # FK đến public.cong_chuc
    giang_vien_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID, ForeignKey("public.cong_chuc.id")    # ← cross-schema FK
    )
    nguoi_duyet_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID, ForeignKey("public.cong_chuc.id")
    )
    
    # Relationships
    giang_vien = relationship("CongChuc", foreign_keys=[giang_vien_id], lazy="joined")
    bai_hocs = relationship("BaiHoc", back_populates="khoa_hoc", lazy="selectin")
```

### 3.5. Database Session

```python
# File: app/core/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

# Engine — dùng chung 1 database, khác schema
engine = create_async_engine(
    settings.DATABASE_URL,   # postgresql+asyncpg://user:pass@localhost/kpi_haiquan
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    echo=settings.DEBUG      # Log SQL queries khi debug
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    """Dependency injection cho database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

---

## 4. RESPONSE FORMAT CHUẨN

### 4.1. Thành công (không phân trang)

```json
{
  "success": true,
  "data": {
    "id": "uuid-...",
    "ten_khoa_hoc": "Nghiệp vụ hải quan cơ bản",
    "trang_thai": "DA_XUAT_BAN"
  },
  "message": "Thao tác thành công"
}
```

### 4.2. Thành công (có phân trang)

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 156,
    "total_pages": 8
  }
}
```

### 4.3. Lỗi

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dữ liệu không hợp lệ",
    "details": [
      {"field": "ten_khoa_hoc", "message": "Tên khóa học không được để trống"}
    ]
  }
}
```

### 4.4. Mã lỗi chuẩn

| Code | HTTP Status | Mô tả |
|------|------------|-------|
| `VALIDATION_ERROR` | 422 | Dữ liệu đầu vào không hợp lệ |
| `NOT_FOUND` | 404 | Không tìm thấy tài nguyên |
| `UNAUTHORIZED` | 401 | Chưa đăng nhập / Token hết hạn |
| `FORBIDDEN` | 403 | Không có quyền |
| `CONFLICT` | 409 | Xung đột dữ liệu (trùng mã, ...) |
| `INTERNAL_ERROR` | 500 | Lỗi server |
| `BUSINESS_RULE_ERROR` | 400 | Vi phạm quy tắc nghiệp vụ |

---

## 5. QUY ƯỚC FRONTEND (TYPESCRIPT / NEXT.JS)

### 5.1. API Client chuẩn

```typescript
// File: src/lib/api.ts

const BASE_URLS = {
  kpi: '/api/v1',
  lms: '/api/lms/v1',
  forum: '/api/forum/v1',
  legal: '/api/legal/v1',
  portal: '/api/portal/v1',
  common: '/api/common/v1',
} as const;

type Module = keyof typeof BASE_URLS;

interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: {
    code: string;
    message: string;
    details?: Array<{ field: string; message: string }>;
  };
  pagination?: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
  };
}

export async function apiCall<T>(
  module: Module,
  path: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  const token = getAccessToken(); // Lấy từ cookie/localStorage
  
  const response = await fetch(`${BASE_URLS[module]}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : '',
      ...options?.headers,
    },
  });

  if (response.status === 401) {
    // Token hết hạn → redirect login
    redirectToLogin();
    throw new Error('Unauthorized');
  }

  return response.json();
}

// Ví dụ sử dụng:
// const { data } = await apiCall<KhoaHoc[]>('lms', '/khoa-hoc?page=1');
```

### 5.2. TypeScript Types chuẩn

```typescript
// File: src/types/common.ts

// User info từ JWT
export interface CurrentUser {
  id: string;
  ma_cc: string;
  ho_ten: string;
  vai_tro: string;         // Vai trò KPI
  don_vi_id: string;
  is_lanh_dao: boolean;
  platform_roles: string[]; // Vai trò nền tảng
}

// User tóm tắt (kèm entity)
export interface UserBrief {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu?: string;
  don_vi_ten?: string;
}

// Đơn vị
export interface DonVi {
  id: string;
  ma_don_vi: string;
  ten_don_vi: string;
  ten_viet_tat?: string;
  loai_don_vi: 'PHONG' | 'DOI' | 'HAI_QUAN_CUA_KHAU';
}
```

### 5.3. Component Naming

```
Tên component:    PascalCase         → KhoaHocList.tsx
Tên hook:         camelCase + "use"  → useKhoaHoc.ts
Tên utils:        camelCase          → formatDate.ts
Tên route:        kebab-case         → /dao-tao/khoa-hoc/[id]
Tên API path:     kebab-case         → /api/lms/v1/khoa-hoc
```

---

## 6. GIT WORKFLOW

### 6.1. Branch naming

```
main                          # Production — KHÔNG push trực tiếp
├── develop                   # Integration branch
├── feature/lms-khoa-hoc      # Feature branch
├── feature/forum-chu-de
├── fix/lms-diem-khong-tinh
├── hotfix/auth-token-expire
└── release/v1.1.0
```

### 6.2. Commit message

```
<type>(<scope>): <mô tả tiếng Việt>

Ví dụ:
feat(lms): thêm API tạo khóa học mới
fix(forum): sửa lỗi upvote không cập nhật số lượng
docs(shared): cập nhật SHARED_AUTH_SPECS
refactor(legal): tách service xác nhận đọc
test(lms): thêm unit test cho bài kiểm tra
chore(infra): cập nhật nginx config routing
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `style`, `perf`

**Scopes:** `lms`, `forum`, `legal`, `portal`, `common`, `shared`, `infra`, `auth`

---

## 7. ERROR HANDLING & LOGGING

### 7.1. Exception handler chuẩn

```python
# File: app/main.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="LMS Service", version="1.0.0")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": _map_status_to_code(exc.status_code),
                "message": exc.detail
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Log lỗi chi tiết cho debug
    import logging
    logging.error(f"Lỗi không mong muốn: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau."
            }
        }
    )
```

### 7.2. Logging format

```python
# Cấu hình logging
import logging

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)

# Ví dụ log:
# 2026-02-18 10:30:00 | INFO  | lms.service | Tạo khóa học: KH-2026-001
# 2026-02-18 10:30:05 | ERROR | forum.api   | Lỗi upvote: IntegrityError
```

---

## 8. BIẾN MÔI TRƯỜNG

### 8.1. File `.env` mẫu

```env
# Database — CHUNG cho tất cả module (cùng database, khác schema)
DATABASE_URL=postgresql+asyncpg://kpi_user:password@localhost:5432/kpi_haiquan

# JWT — CHUNG (phải giống nhau giữa các module)
PLATFORM_SECRET_KEY=your-shared-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=kv08-files

# Module-specific
SERVICE_NAME=lms-service
SERVICE_PORT=8001
DEBUG=false
LOG_LEVEL=INFO
```

> **⚠️ QUAN TRỌNG:** `PLATFORM_SECRET_KEY` PHẢI GIỐNG NHAU giữa KPI Backend và tất cả module mới. Nếu khác nhau, JWT decode sẽ thất bại.

---

## 9. NGINX ROUTING

```nginx
# /etc/nginx/sites-available/kv08.vn

server {
    listen 443 ssl;
    server_name kv08.vn *.kv08.vn;
    
    # SSL config...
    
    # KPI Backend (GIỮ NGUYÊN — port 8000)
    location /api/v1/ {
        proxy_pass http://127.0.0.1:8000/api/v1/;
    }
    
    # LMS Backend (MỚI — port 8001)
    location /api/lms/ {
        proxy_pass http://127.0.0.1:8001/api/lms/;
    }
    
    # Forum Backend (MỚI — port 8002)
    location /api/forum/ {
        proxy_pass http://127.0.0.1:8002/api/forum/;
    }
    
    # Legal Backend (MỚI — port 8003)
    location /api/legal/ {
        proxy_pass http://127.0.0.1:8003/api/legal/;
    }
    
    # Portal Backend (MỚI — port 8004)
    location /api/portal/ {
        proxy_pass http://127.0.0.1:8004/api/portal/;
    }
    
    # Common Backend (MỚI — port 8005)
    location /api/common/ {
        proxy_pass http://127.0.0.1:8005/api/common/;
    }
    
    # Frontend (Next.js — port 3000)
    location / {
        proxy_pass http://127.0.0.1:3000;
    }
}
```

---

## 10. CHECKLIST TRƯỚC KHI TẠO PR

```
□ Code chạy được local, không lỗi
□ Comment tiếng Việt cho logic nghiệp vụ
□ UUID cho primary key, FK → public.cong_chuc(id)
□ Response format đúng chuẩn (success/data/message)
□ Auth dependency đúng (get_current_user / require_platform_role)
□ Migration có upgrade() VÀ downgrade()
□ Pydantic schema có validation (Field, min_length, ...)
□ Error handling đúng format (error code + message)
□ Không sửa/xóa bảng KPI trong schema public
□ Đã test với ít nhất 3 vai trò khác nhau
□ Commit message đúng convention
□ Không commit .env, secret key, password
□ Đã chạy linting (ruff/black cho Python, eslint cho TS)
```

---

> **Liên hệ:** Mọi thắc mắc về Coding Standards → Kiến trúc sư trưởng  
> **Cập nhật:** File này được quản lý tập trung. KHÔNG fork/copy riêng.
