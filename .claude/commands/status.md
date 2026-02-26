---
description: Xem trạng thái hiện tại của dự án và từng module
argument-hint: "(không cần argument, hoặc tên module: lms, forum, legal, portal)"
---

Kiểm tra trạng thái dự án: $ARGUMENTS

## Thực hiện

1. Đọc CLAUDE.md phần "Trạng thái hiện tại"

2. Kiểm tra thực tế từng phần:

### Backend
- Folder tồn tại? `ls backend/lms_service/ backend/forum_service/ backend/legal_service/ backend/portal_service/`
- Models đã tạo? `find backend/{module}_service/models/ -name "*.py" ! -name "__init__.py"`
- Endpoints đã tạo? `find backend/{module}_service/api/endpoints/ -name "*.py" ! -name "__init__.py"`
- Tests? `find backend/{module}_service/tests/ -name "test_*.py"`
- Chạy test: `pytest backend/{module}_service/tests/ -v --tb=short 2>/dev/null || echo "Chưa có test"`

### Frontend
- Pages tồn tại? `find frontend/src/app/\(main\)/{route}/ -name "page.tsx"`
- Components? `find frontend/src/components/{module}/ -name "*.tsx" 2>/dev/null`
- Build OK? `cd frontend && npm run build 2>&1 | tail -5`

### Database
- Schema tồn tại? `alembic current`
- Migration pending? `alembic heads`

3. Báo cáo dạng:
```
📊 TRẠNG THÁI DỰ ÁN — [ngày]

KPI:     ✅ Production (kpihaiquan.vn)
LMS:     🔄 Backend X/11 endpoints | Frontend X/Y pages | Tests: X pass
Forum:   ⏳ Chưa bắt đầu
Legal:   ⏳ Chưa bắt đầu
Portal:  ⏳ Chưa bắt đầu

Migrations: X applied | Y pending
Frontend build: ✅/❌
```

4. Cập nhật CLAUDE.md phần "Trạng thái hiện tại" nếu có thay đổi