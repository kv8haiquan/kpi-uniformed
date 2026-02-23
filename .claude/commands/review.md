---
description: Review tất cả thay đổi hiện tại trước khi commit
argument-hint: "(không cần argument)"
---

Review toàn bộ code thay đổi hiện tại. Dùng code-reviewer agent.

## Thực hiện

1. Chạy `git diff --name-only` → liệt kê files changed
2. Chạy `git diff` → xem nội dung thay đổi

3. Kiểm tra ĐẦU TIÊN — Bảo vệ KPI:
   - ❌ Có file trong backend/app/ bị sửa?
   - ❌ Có thay đổi bảng schema public?
   - ❌ Có hardcode credentials?
   → Nếu có → DỪNG, báo lỗi nghiêm trọng

4. Review theo checklist:
   - Spec compliance (đúng API_SPECS, BUSINESS_RULES?)
   - Security (JWT, role check, SQL injection?)
   - Convention (snake_case, comment tiếng Việt, response format?)
   - Code quality (service layer tách riêng, error handling?)
   - Database (đúng schema, migration có downgrade?)

5. Chạy kiểm tra tự động:
   ```bash
   black --check backend/
   isort --check backend/
   pytest backend/ -v --tb=short
   cd frontend && npm run build && npm run lint
   ```

6. Báo cáo:
   ```
   📄 [file] — ✅/⚠️/❌ [chi tiết]
   📊 Tổng kết: Pass X/Y | Cần sửa: [danh sách]
   💡 Gợi ý commit message: feat(module): mô tả
   ```