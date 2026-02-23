---
description: Scaffold CRUD API hoàn chỉnh cho 1 resource (model + schema + endpoint + service + test)
argument-hint: "<module> <resource_name>"
---

Tạo CRUD API hoàn chỉnh cho resource: $ARGUMENTS

## Bước 1 — Đọc specs
Tách $ARGUMENTS thành <module> và <resource_name>.
- Đọc docs/<module>/<MODULE>_DATABASE_DESIGN.md → tìm bảng <resource_name>
- Đọc docs/<module>/<MODULE>_API_SPECS.md → tìm endpoints cho <resource_name>
- Đọc docs/<module>/<MODULE>_BUSINESS_RULES.md → tìm logic tương ứng
- Đọc docs/shared/SHARED_AUTH_SPECS.md → tìm permission cho resource

## Bước 2 — Tạo files
Tạo 5 file trong backend/<module>_service/:

1. `models/<resource_name>.py` — SQLAlchemy 2.0 model
   - __table_args__ = {"schema": "<module>"}
   - PK: UUID gen_random_uuid()
   - FK user: ForeignKey("public.cong_chuc.id")
   - Trạng thái: String(50), KHÔNG ENUM

2. `schemas/<resource_name>.py` — Pydantic v2
   - CreateSchema (input validation, Field validators)
   - UpdateSchema (Optional fields)
   - ResponseSchema (from_attributes=True)
   - ListResponseSchema (pagination)

3. `api/endpoints/<resource_name>.py` — FastAPI router
   - GET /<resource> (list, pagination, filter)
   - GET /<resource>/{id} (detail)
   - POST /<resource> (create, auth required)
   - PUT /<resource>/{id} (update, auth + owner/role check)
   - DELETE /<resource>/{id} (soft delete, auth + role check)
   - Depends(get_current_user), Depends(require_platform_role(...)) theo specs

4. `services/<resource_name>.py` — Business logic
   - Tách logic khỏi endpoint
   - Validation, business rules, permission check
   - Return data hoặc raise HTTPException

5. `tests/test_<resource_name>.py` — Tests
   - Test CRUD thành công
   - Test phân quyền (CBCC vs Giảng viên vs Admin)
   - Test validation lỗi
   - Test business rules

## Bước 3 — Đăng ký router
Thêm router vào <module>_service/main.py

## Bước 4 — Verify
- Chạy pytest backend/<module>_service/tests/test_<resource_name>.py -v
- Báo cáo: endpoints tạo, tests pass/fail