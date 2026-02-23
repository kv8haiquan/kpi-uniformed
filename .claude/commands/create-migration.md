---
description: Tạo Alembic migration cho bảng hoặc schema mới
argument-hint: "<module> <table_name hoặc 'all'>"
---

Tạo migration cho: $ARGUMENTS

## Bước 1 — Đọc specs
Tách $ARGUMENTS thành <module> và <target>.
- Đọc docs/<module>/<MODULE>_DATABASE_DESIGN.md (hoặc docs/shared/SHARED_DB_REFERENCE.md nếu platform)
- Xem backend/alembic/versions/ → migration cuối cùng là gì

## Bước 2 — Tạo migration

Nếu target = "all": tạo migration cho TẤT CẢ bảng trong schema đó (theo thứ tự dependency).
Nếu target = tên bảng: tạo migration cho 1 bảng cụ thể.

Quy tắc:
- CREATE SCHEMA IF NOT EXISTS <module> (đầu migration đầu tiên)
- PK: UUID DEFAULT gen_random_uuid()
- FK user: REFERENCES public.cong_chuc(id)
- Trạng thái: VARCHAR(50), KHÔNG PostgreSQL ENUM
- Timestamp: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- PHẢI có upgrade() VÀ downgrade()
- Tạo index cho FK columns và status columns

## Bước 3 — Verify
- Chạy `alembic upgrade head`
- Kiểm tra bảng tồn tại: `\dt <module>.*`
- Test rollback: `alembic downgrade -1`
- Báo cáo kết quả