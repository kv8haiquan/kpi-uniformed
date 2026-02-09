# 🏛️ KPI Hải quan Frontend

Hệ thống Đánh giá và Xếp loại Công chức - Chi cục Hải quan Khu vực VIII

## 📋 Mục lục

- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt](#cài-đặt)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Các file quan trọng](#các-file-quan-trọng)
- [Development](#development)

---

## Yêu cầu hệ thống

- **Node.js**: >= 18.17.0
- **npm**: >= 9.0.0
- **Backend API**: Đang chạy tại `http://localhost:8000`

## Cài đặt

### 1. Clone và cài dependencies

```bash
# Vào thư mục dự án
cd kpi-haiquan-frontend

# Cài đặt dependencies
npm install
```

### 2. Cấu hình environment

```bash
# Copy file .env.example
cp .env.example .env.local

# Sửa file .env.local với giá trị thực tế
# NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 3. Chạy development server

```bash
npm run dev
```

Mở [http://localhost:3000](http://localhost:3000) để xem kết quả.

---

## Cấu trúc dự án

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Route group: Trang authentication
│   │   ├── login/          # Trang đăng nhập
│   │   └── layout.tsx      # Layout không sidebar
│   ├── (main)/             # Route group: Trang chính (protected)
│   │   ├── dashboard/      # Trang dashboard
│   │   └── layout.tsx      # Layout có sidebar
│   ├── globals.css         # Global styles
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Root page (redirect)
│
├── lib/                    # Utilities & configurations
│   ├── axios.ts            # Axios instance với interceptors
│   └── validations/        # Zod schemas
│       └── auth.ts         # Validation cho auth forms
│
├── providers/              # React Context Providers
│   └── AuthProvider.tsx    # Provider khởi tạo auth state
│
├── services/               # API service classes
│   ├── auth.service.ts     # Auth API calls
│   └── index.ts            # Re-export
│
├── stores/                 # Zustand stores
│   └── useAuthStore.ts     # Auth state management
│
├── types/                  # TypeScript interfaces
│   ├── api.ts              # API response types
│   ├── auth.ts             # Auth & User types
│   └── index.ts            # Re-export
│
└── middleware.ts           # Next.js middleware (route protection)
```

---

## Các file quan trọng

### Types (TypeScript Interfaces)

| File | Mô tả |
|------|-------|
| `src/types/api.ts` | Generic API response types (`IDataResponse<T>`, `IPaginatedResponse<T>`) |
| `src/types/auth.ts` | Auth & User types (`IUser`, `ILoginRequest`, `ILoginResponse`) |

### Services (API Calls)

| File | Mô tả |
|------|-------|
| `src/services/auth.service.ts` | `login()`, `getMe()`, `logout()` |

### Stores (State Management)

| File | Mô tả |
|------|-------|
| `src/stores/useAuthStore.ts` | Auth state: `user`, `token`, `isAuthenticated` |

### Lib (Utilities)

| File | Mô tả |
|------|-------|
| `src/lib/axios.ts` | Axios instance với auto token injection & error handling |
| `src/lib/validations/auth.ts` | Zod schemas cho form validation |

---

## Development

### Available Scripts

```bash
# Development
npm run dev

# Build production
npm run build

# Start production
npm start

# Lint
npm run lint
```

### API Response Format

Backend trả về response theo format:

```typescript
// Success
{
  "success": true,
  "data": { ... },
  "message": "Optional message"
}

// Error
{
  "success": false,
  "error": {
    "code": "AUTH_003",
    "message": "Sai tên đăng nhập hoặc mật khẩu"
  }
}
```

### Authentication Flow

1. User nhập username/password
2. Gọi `POST /auth/login` → Nhận `access_token`
3. Lưu token vào localStorage
4. Gọi `GET /auth/me` → Nhận user info
5. Lưu user vào Zustand store
6. Redirect về `/dashboard`

### Token Auto-refresh

- Axios interceptor tự động gắn token vào mọi request
- Khi nhận 401, tự động logout và redirect về `/login`

---

## 📝 Notes

- Code comments bằng **Tiếng Việt**
- Follow **SOLID** principles
- Sử dụng **TypeScript strict mode**
- Form validation với **Zod**
- State management với **Zustand**

---

## 🚀 Next Steps (Giai đoạn tiếp theo)

- [ ] Tạo Sidebar component
- [ ] Tạo trang Kê khai công việc
- [ ] Tạo trang Danh sách đánh giá
- [ ] Tạo trang Phê duyệt (cho Lãnh đạo)
- [ ] Tạo trang Báo cáo tổng hợp

---

© 2025 Chi cục Hải quan Khu vực VIII
