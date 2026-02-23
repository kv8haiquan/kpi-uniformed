---
description: Scaffold Next.js page hoàn chỉnh cho 1 route (page + components + service + types)
argument-hint: "<route_path> (ví dụ: dao-tao/khoa-hoc)"
---

Tạo page hoàn chỉnh cho route: $ARGUMENTS

## Bước 1 — Phân tích
Tách $ARGUMENTS thành module và route. Ví dụ: "dao-tao/khoa-hoc" → module=lms, route=dao-tao/khoa-hoc.

Xem pattern hiện có:
- Đọc frontend/src/app/(main)/ → hiểu cách page KPI tổ chức
- Đọc frontend/src/components/ → hiểu components dùng chung
- Đọc frontend/src/services/ → hiểu API service pattern
- Đọc API specs module tương ứng

## Bước 2 — Tạo files

1. `frontend/src/app/(main)/$ARGUMENTS/page.tsx` — Page chính
   - Server component hoặc client component tùy logic
   - Data fetching từ API service
   - Loading state (Skeleton), Error state (Alert), Empty state
   - Responsive, mobile-first

2. `frontend/src/app/(main)/$ARGUMENTS/[id]/page.tsx` — Detail page (nếu cần)
   - Hiển thị chi tiết 1 item
   - Breadcrumb navigation

3. `frontend/src/components/{module}/` — Components riêng
   - Card, List, Form, Filter components
   - Dùng shadcn/ui: Button, Card, Dialog, Table, Form, Input, Select

4. `frontend/src/services/{module}.ts` — Thêm API calls (nếu chưa có)
   - GET, POST, PUT, DELETE functions
   - Dùng axios instance đã cấu hình JWT

5. `frontend/src/types/{module}.ts` — Thêm TypeScript interfaces (nếu chưa có)
   - Response types khớp với backend schemas

## Bước 3 — Verify
- Chạy `cd frontend && npm run build` → KHÔNG lỗi
- Chạy `npm run lint` → fix warnings
- Báo cáo: pages tạo, components tạo