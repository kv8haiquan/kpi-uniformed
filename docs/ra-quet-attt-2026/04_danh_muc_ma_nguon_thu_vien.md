# Mục 4 — Danh mục mã nguồn, thư viện, framework, phiên bản phần mềm

> Phục vụ công văn 153/CNTT ngày 08/7/2026 — kiểm tra, đánh giá an toàn, an ninh thông tin.
> Lập ngày 30/07/2026.

## 1. Tổng quan mã nguồn

| Thành phần | Ngôn ngữ / Framework | Thư mục | Ghi chú |
|---|---|---|---|
| KPI Backend | Python 3.12 / FastAPI | `backend/app/` | Production, 239 endpoints |
| LMS Backend (Đào tạo) | Python 3.12 / FastAPI | `backend/lms_service/` | 111 endpoints |
| Forum Backend | Python 3.12 / FastAPI | `backend/forum_service/` | 27 endpoints |
| Legal Backend (Pháp luật) | Python 3.12 / FastAPI | `backend/legal_service/` | 29 endpoints |
| Portal Backend | Python 3.12 / FastAPI | `backend/portal_service/` | 38 endpoints |
| Common Backend | Python 3.12 / FastAPI | `backend/common_service/` | 23 endpoints |
| HKG Backend (Họp Không Giấy) | Python 3.12 / FastAPI | `backend/meeting_service/` | 55 endpoints |
| Chỉ tiêu Backend | Python 3.12 / FastAPI | `backend/chi_tieu_service/` | 33 endpoints |
| Module dùng chung backend | Python 3.12 | `backend/shared/` | Auth/JWT, schemas, DB session |
| Frontend | TypeScript 5 / Next.js 16 / React 19 | `frontend/` | Toàn bộ giao diện người dùng |
| Migrations | Alembic | `backend/alembic/` | Quản lý schema DB |

Quản lý phiên bản mã nguồn: **Git** (local repository + backup mã nguồn tự động 2 lần/ngày lên private GitHub — xem Mục 6).

## 2. Thư viện Backend (Python) — `backend/requirements.txt`

| Thư viện | Phiên bản | Công dụng |
|---|---|---|
| fastapi | 0.115.6 | Web framework (API) |
| uvicorn[standard] | 0.34.0 | ASGI server |
| python-multipart | 0.0.20 | Xử lý form/upload |
| python-jose[cryptography] | 3.3.0 | JWT (ký/verify token) |
| passlib[bcrypt] | 1.7.4 | Hash mật khẩu |
| bcrypt | 4.2.1 | Thuật toán bcrypt |
| sqlalchemy[asyncio] | 2.0.36 | ORM (async) |
| asyncpg | 0.30.0 | Driver PostgreSQL async |
| psycopg2-binary | (mới nhất) | Driver PostgreSQL sync (scripts) |
| alembic | 1.14.0 | Database migration |
| greenlet | 3.1.1 | Hỗ trợ SQLAlchemy async |
| pydantic | 2.10.4 | Validation dữ liệu |
| pydantic-settings | 2.7.0 / 2.7.1 | Đọc cấu hình `.env` |
| email-validator | 2.2.0 | Validate email |
| python-dotenv | 1.0.1 | Load biến môi trường |
| pandas | 2.2.3 | Xử lý dữ liệu, báo cáo |
| openpyxl | 3.1.5 | Xuất/nhập Excel |
| xlrd | 2.0.1 | Đọc Excel định dạng cũ |
| reportlab | 4.4.10 | Xuất PDF |
| python-docx | 1.1.2 | Xuất Word (mẫu phiếu) |
| httpx | 0.28.1 | HTTP client |
| orjson | 3.10.12 | JSON hiệu năng cao |
| loguru | 0.7.3 | Ghi log |
| rich | 13.9.4 | Console output |
| python-dateutil | 2.9.0 | Xử lý ngày tháng |
| pytz | 2024.2 | Múi giờ |
| slowapi | 0.1.9 | Rate limiting (chống spam upload) |
| pytest / pytest-asyncio | 8.3.4 / 0.25.0 | Kiểm thử (dev, không chạy production) |

Các service phụ (`lms_service`, `forum_service`, `legal_service`, `portal_service`, `common_service`) dùng chung danh mục trên (chênh lệch duy nhất: `pydantic-settings==2.7.1` và bộ pytest phục vụ test).

## 3. Thư viện Frontend (Node.js) — `frontend/package.json`

### Dependencies (chạy production)

| Thư viện | Phiên bản | Công dụng |
|---|---|---|
| next | 16.1.4 | Framework React SSR |
| react / react-dom | 19.2.3 | Thư viện UI |
| typescript | ^5 | Ngôn ngữ |
| axios | ^1.13.2 | HTTP client (gọi API) |
| zustand | ^5.0.10 | Quản lý state (JWT, user) |
| react-hook-form | ^7.71.1 | Form |
| @hookform/resolvers | ^5.2.2 | Kết nối form + Zod |
| zod | ^4.3.6 | Validation schema |
| tailwindcss | ^4 | CSS framework |
| tailwind-merge / clsx | ^3.4.0 / ^2.1.1 | Tiện ích CSS |
| lucide-react | ^0.563.0 | Bộ icon |
| date-fns | ^4.1.0 | Xử lý ngày tháng |
| xlsx | ^0.18.5 | Xuất Excel phía client |
| pdfjs-dist | ^4.10.38 | Xem PDF (HKG trình chiếu) |
| @tiptap/* | ^3.22.5 | Trình soạn thảo văn bản |
| qrcode.react | ^4.2.0 | Sinh mã QR |

### DevDependencies (chỉ dùng khi build/test, không chạy production)

eslint 9, eslint-config-next 16.1.4, vitest 4.1.5, @testing-library/*, jsdom, @vitejs/plugin-react, @tailwindcss/postcss, @types/*.

## 4. Nền tảng vận hành

| Thành phần | Phiên bản |
|---|---|
| Hệ điều hành | Ubuntu 24.04.4 LTS (kernel 6.8.0-60-generic) |
| Python | 3.12.3 (virtualenv riêng tại `backend/venv/`) |
| Node.js | 20.20.0 LTS |
| PostgreSQL | 15.16 (Ubuntu 15.16-1.pgdg24.04+1) |
| nginx | 1.24.0 (reverse proxy + SSL) |
| PM2 | 6.0.14 (process manager, tự khởi động lại service) |
| Certbot / Let's Encrypt | Tự động gia hạn chứng thư SSL |

## 5. File cấu hình triển khai

| File | Nội dung | Ghi chú bảo mật |
|---|---|---|
| `backend/.env` | DB credential, SECRET_KEY JWT | **KHÔNG bàn giao** — chỉ bàn giao `.env.example` |
| `backend/.env.example` | Mẫu cấu hình (không chứa secret) | Bàn giao kèm mã nguồn |
| `frontend/.env` | URL API public | Không chứa secret |
| `nginx/default.conf` | Routing 8 service + SSL | Bàn giao |
| `backend/alembic.ini` | Cấu hình migration | Bàn giao |
| `backend/docker-compose.yml` | DB dev (không dùng production) | Bàn giao |
| Cấu hình PM2 (ecosystem) | Khai báo 9 process | Bàn giao |

> **Nguyên tắc bàn giao mã nguồn:** gói bàn giao được tạo bằng `git archive` từ bản tag cố định, **loại trừ** `.env`, thư mục backup, dump database, `venv/`, `node_modules/`. SECRET_KEY và mật khẩu DB bàn giao riêng qua kênh bảo mật nếu đoàn kiểm tra yêu cầu.
