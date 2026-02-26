# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KPI assessment system for Chi cục Hải quan Khu vực VIII (Vietnam Customs Region VIII). Manages monthly KPI declarations, multi-level approvals, performance assessments, and staff classification for civil servants.

**ĐANG MỞ RỘNG** thành Nền tảng Số Thống nhất: KPI (production) + LMS + Forum + Legal + Portal.

## Tech Stack

- **Backend:** Python 3.10+, FastAPI 0.115.6, SQLAlchemy 2.0 (async), Alembic migrations
- **Frontend:** Next.js 16.1.4, React 19, TypeScript 5, Tailwind CSS 4
- **Database:** PostgreSQL 15+ (via Docker, port 5433 mapped to 5432)
- **State management:** Zustand (frontend), React Hook Form + Zod for forms
- **Bổ sung:** Redis (cache/queue), MinIO (file storage), pg_tsvector (search)

## Common Commands

### Backend (from `backend/` directory)

```bash
# Start database
docker-compose up -d db

# Start dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run migrations
alembic upgrade head

# Create new migration after model changes
alembic revision --autogenerate -m "description"

# Check migration status
alembic current

# Run tests
pytest
pytest --cov=app --cov-report=html

# Seed data
python scripts/seed_users.py
python scripts/seed_tasks.py
python scripts/seed_admin.py

# Lint/format
black app/
isort app/
flake8 app/
```

### Frontend (from `frontend/` directory)

```bash
npm install
npm run dev      # Dev server on port 3000
npm run build    # Production build
npm run lint     # ESLint
```

## Architecture

### Backend - Layered Architecture

```
API endpoints (app/api/v1/endpoints/) → Services (app/services/) → Repository/DB (app/models/)
```

- **`app/main.py`** - FastAPI entry point, CORS config, auto-migration on startup
- **`app/api/deps.py`** - Dependency injection: `get_db` (AsyncSession), `get_current_user` (JWT auth)
- **`app/api/v1/api.py`** - Router aggregator that mounts all endpoint routers
- **`app/config.py`** - Pydantic Settings loading from `.env`
- **`app/core/security.py`** - JWT token creation/verification, password hashing (bcrypt)
- **`app/db/session.py`** - AsyncSession factory using asyncpg

All database operations are async. Models use SQLAlchemy 2.0 declarative style in `app/models/`. Pydantic schemas (DTOs) are in `app/schemas/`.

### Frontend - Next.js App Router

```
src/app/(auth)/     → Login page (unauthenticated)
src/app/(main)/     → All authenticated pages (dashboard, ke-khai, danh-gia, phe-duyet, etc.)
```

- **`src/services/`** - Axios-based API client classes (one per domain)
- **`src/stores/useAuthStore.ts`** - Zustand store for JWT token and user state
- **`src/providers/AuthProvider.tsx`** - Auth context wrapping the app
- **`src/lib/axios.ts`** - Axios instance with JWT interceptor, base URL `http://localhost:8000`
- **`src/lib/validations/`** - Centralized Zod validation schemas

## Domain Concepts (Vietnamese terms used in code)

| Term | Meaning | Used in |
|------|---------|---------|
| `don_vi` | Organizational unit (department) | Models, endpoints |
| `cong_chuc` | Civil servant (staff member) | Models, endpoints |
| `vai_tro` | Role | Auth, permissions |
| `ke_khai` | Work declaration (monthly KPI submission) | Core workflow |
| `phe_duyet` | Approval | Workflow |
| `danh_gia` | Assessment/evaluation | Monthly scoring |
| `xep_loai` | Classification (A/B/C/D rating) | Final rating |
| `nghi_phep` | Leave management | Leave tracking |
| `lanh_dao` | Leadership | Leader-specific modules |

## Role Hierarchy (RBAC)

Six roles in descending authority: Chi cục trưởng (CCT/Director) → Phó Chi cục trưởng (PCCT) → Trưởng đơn vị (TDV) → Phó đơn vị (PDV) → Công chức (CC/Staff) → Admin

## Workflow

Monthly cycle: Staff **declares** work (ke_khai) → Unit leader **reviews/approves** (phe_duyet) → System **calculates** KPI scores (danh_gia) → Directors **classify** staff A/B/C/D (xep_loai)

## Database

- Docker PostgreSQL exposed on port **5433** (not default 5432)
- Migrations in `backend/alembic/versions/` - auto-run on app startup
- Default credentials after seed: username = staff code (e.g., `20ZZ-0224`), password = `123456`
- Environment config via `backend/.env` (copy from `.env.example`)

## Migration Troubleshooting

```bash
# "Target database is not up to date"
alembic stamp head

# "ENUM type already exists" - drop old types then re-run
# "Can't locate revision" - drop alembic_version table then re-run
```

---

# ═══════════════════════════════════════════════════════════
# PHẦN MỞ RỘNG — NỀN TẢNG SỐ THỐNG NHẤT (Digital Learning Platform)
# ═══════════════════════════════════════════════════════════

## QUY TẮC TUYỆT ĐỐI

```
⛔ KHÔNG BAO GIỜ sửa/xóa code trong backend/app/ (KPI production)
⛔ KHÔNG BAO GIỜ sửa/xóa bảng trong schema public (cong_chuc, vai_tro, don_vi, ...)
⛔ KHÔNG BAO GIỜ chạy migration trên production database (27.71.229.103)
⛔ KHÔNG BAO GIỜ commit trực tiếp vào branch main hoặc develop
⛔ KHÔNG BAO GIỜ hardcode SECRET_KEY, password, hoặc database credential

✅ CHỈ ĐỌC bảng public.cong_chuc, public.don_vi, public.vai_tro (FK reference)
✅ CHỈ THÊM bảng mới vào schema riêng (lms.*, forum.*, legal.*, portal.*, common.*)
✅ CHỈ THÊM 3 bảng vào public: platform_role, cong_chuc_platform_role, platform_config
✅ LUÔN đọc file spec tương ứng TRƯỚC KHI implement feature mới
✅ LUÔN tạo branch feature/[module]-[feature] trước khi code
```

## Chiến lược Multi-Schema

Tất cả module MỚI dùng PostgreSQL schema riêng trong CÙNG database `kpi_haiquan`:

```
kpi_haiquan (database)
├── public     ← KPI tables (GIỮ NGUYÊN) + 3 bảng platform bổ sung
├── lms        ← Module Đào tạo (11 bảng)
├── forum      ← Module Diễn đàn (5 bảng)
├── legal      ← Module Pháp luật (6 bảng)
├── portal     ← Module Portal/CMS (4 bảng)
└── common     ← Module dùng chung (4 bảng)
```

Lý do: Cross-schema JOIN hoạt động bình thường, 1 connection pool, FK trực tiếp đến public.cong_chuc(id).

## Port Mapping — Multi-Service

| Service | Port | Folder | Status |
|---------|------|--------|--------|
| KPI Backend | 8000 | backend/app/ | ✅ Production |
| LMS Backend | 8001 | (project riêng) | 🔄 Đang build |
| Forum Backend | 8002 | (project riêng) | ⏳ Chưa bắt đầu |
| Legal Backend | 8003 | (project riêng) | ⏳ Chưa bắt đầu |
| Frontend | 3000 | frontend/ | ✅ Production |

## Bảng dùng chung — CHỈ ĐỌC

Mọi module mới FK user → public.cong_chuc(id). Cấu trúc bảng chính:

```sql
-- public.cong_chuc (549 người dùng — READONLY)
id              UUID PK
ma_cc           VARCHAR(20) UNIQUE    -- "20ZZ-0224"
ho_ten          VARCHAR(100)          -- "Nguyễn Văn A"
don_vi_id       UUID FK → don_vi(id)
vai_tro_id      UUID FK → vai_tro(id)
chuc_vu         VARCHAR(100)          -- "Công chức", "Đội trưởng"
is_lanh_dao     BOOLEAN
is_active       BOOLEAN
email           VARCHAR(100)
so_dien_thoai   VARCHAR(20)

-- public.don_vi (15 đơn vị — READONLY)
id              UUID PK
ma_don_vi       VARCHAR(20) UNIQUE    -- "DV01"
ten_don_vi      VARCHAR(200)          -- "Đội Nghiệp vụ 1"
loai_don_vi     LOAI_DON_VI           -- PHONG | DOI | HAI_QUAN_CUA_KHAU

-- public.vai_tro (7 vai trò — READONLY)
id              UUID PK
ma_vai_tro      VARCHAR(20) UNIQUE    -- SUPER_ADMIN, CCT, PCCT, TDV, PDV, CC, TCCB
cap_bac         CAP_BAC
is_lanh_dao     BOOLEAN
```

## SSO — JWT mở rộng

Login endpoint GIỮ NGUYÊN: `POST /api/v1/auth/login` (KPI backend port 8000).

JWT payload mở rộng (thêm field, KHÔNG xóa field cũ):
```json
{
  "sub": "uuid-cong-chuc-id",
  "ma_cc": "20ZZ-0224",
  "vai_tro": "CONG_CHUC",
  "don_vi_id": "uuid-don-vi",
  "is_lanh_dao": false,
  "platform_roles": ["GIANG_VIEN"],
  "exp": 1708300000
}
```

Mỗi module mới TỰ decode JWT bằng CÙNG SECRET_KEY. KHÔNG gọi lại KPI backend để verify.

## Platform Roles (vai trò bổ sung)

| ma_role | Tên | Module |
|---------|-----|--------|
| GIANG_VIEN | Giảng viên kiêm nhiệm | LMS |
| QT_DAO_TAO | Quản trị đào tạo | LMS |
| BIEN_TAP | Biên tập viên | Legal, Portal |
| DIEU_PHOI_FORUM | Điều phối diễn đàn | Forum |
| CHUYEN_GIA | Chuyên gia nghiệp vụ | Forum, Common |
| QT_NOI_DUNG | Quản trị nội dung | Portal |
| QT_ATTT | Quản trị ATTT | ALL |

## Coding Convention cho module mới

```
File/folder:      snake_case
Class:            PascalCase  
Biến/hàm:        snake_case
Comment:          TIẾNG VIỆT
Tên bảng/cột DB: tiếng Việt không dấu (khoa_hoc, bai_hoc, cong_chuc_id)
Primary Key:      id UUID DEFAULT gen_random_uuid()
FK user:          cong_chuc_id UUID REFERENCES public.cong_chuc(id)
Trạng thái:       VARCHAR(50) — KHÔNG dùng PostgreSQL ENUM type
Timestamp:        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
Git commit:       feat(lms): thêm CRUD khóa học
Git branch:       feature/lms-khoa-hoc
```

## Response Format chuẩn

```json
// Thành công
{"success": true, "data": {...}, "message": "Thao tác thành công"}

// Thành công (phân trang)
{"success": true, "data": [...], "pagination": {"page": 1, "page_size": 20, "total_items": 100, "total_pages": 5}}

// Lỗi
{"success": false, "error": {"code": "VALIDATION_ERROR", "message": "Tên khóa học không được để trống"}}
```

## Tài liệu tham chiếu

TRƯỚC KHI implement bất kỳ feature nào, ĐỌC file specs tương ứng:

| Module | Files cần đọc |
|--------|--------------|
| Kiến trúc tổng thể | docs/CHIEN_LUOC_NEN_TANG_THONG_NHAT.md |
| Auth/SSO | docs/shared/SHARED_AUTH_SPECS.md |
| Database reference | docs/shared/SHARED_DB_REFERENCE.md |
| Coding standards | docs/shared/SHARED_CODING_STANDARDS.md |
| LMS | docs/lms/LMS_DATABASE_DESIGN.md + LMS_API_SPECS.md |
| Forum | docs/forum/FORUM_*.md |
| Legal | docs/legal/LEGAL_*.md |
| Cross-module | docs/API_CONTRACT_BETWEEN_MODULES.md |

## Trạng thái hiện tại

(Cập nhật mỗi khi hoàn thành milestone)

- [x] KPI module — ✅ Production (kpihaiquan.vn)
- [x] Tài liệu kiến trúc mở rộng — ✅ Hoàn thành
- [x] SHARED specs (Auth, DB, Coding Standards) — ✅ Hoàn thành
- [x] Shared backend module (auth, schemas, database, constants) — ✅ Hoàn thành
- [x] Cấu trúc thư mục 4 service (lms, forum, legal, portal) — ✅ Skeleton
- [x] Frontend placeholder pages (dao-tao, dien-dan, phap-luat, tai-lieu) — ✅ Hoàn thành
- [x] Frontend services + types (lms, forum, legal, portal) — ✅ Skeleton
- [x] Nginx routing multi-service — ✅ Cấu hình xong (nginx/default.conf)
- [x] Platform tables (platform_role, cong_chuc_platform_role, platform_config) — ✅ Migrated + seeded
- [ ] JWT mở rộng (thêm platform_roles) — Chưa implement
- [x] LMS module — ✅ DONE (45 endpoints, 7 pages, 11 bảng, 49 tests, build PASS)
- [ ] Forum module — 🔄 Skeleton xong, chưa có models/endpoints/tests
- [ ] Legal module — 🔄 Skeleton xong, chưa có models/endpoints/tests
- [ ] Portal module — 🔄 Skeleton xong, chưa có models/endpoints/tests