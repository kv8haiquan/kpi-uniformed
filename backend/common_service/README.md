# Common Service — Module Dùng Chung

**Port:** 8005
**Schema:** `common`
**Status:** Skeleton Complete

## Mục đích

Module dùng chung cho toàn bộ Nền tảng Số HQKV8, bao gồm:

1. **Thông báo (thong_bao)** — Hệ thống thông báo nội bộ
2. **File Storage (file_storage)** — Quản lý file upload (MinIO integration)
3. **Knowledge Base (knowledge_base)** — Cơ sở tri thức (FAQ, Q&A, tài liệu tham khảo)
4. **KPI Integration (integration_log)** — Log và thống kê tích hợp giữa các module

## Cấu trúc

```
common_service/
├── __init__.py
├── config.py              # Cấu hình service (port 8005, schema common)
├── dependencies.py        # JWT auth, DB session, role checks
├── main.py               # FastAPI app entry point
├── requirements.txt      # Python dependencies
├── api/
│   ├── endpoints/        # External API (cho frontend)
│   └── internal/         # Internal API (cho module khác gọi)
├── models/
│   ├── __init__.py
│   └── base.py          # Base + CongChucRef + DonViRef (READONLY)
├── schemas/
│   ├── __init__.py
│   └── base.py          # SuccessResponse, ErrorResponse, PaginatedResponse
├── services/             # Business logic
└── tests/
    ├── __init__.py
    └── conftest.py      # Test fixtures (5 user roles)
```

## Database Schema

**Schema:** `common` (trong database `kpi_haiquan`)

**4 bảng chính:**

1. **thong_bao** — Thông báo hệ thống/module
   - Loại: HE_THONG, MODULE_RIENG, TONG_HOP
   - Mức độ: THONG_THUONG, QUAN_TRONG, KHAN_CAP
   - Target: user cụ thể / toàn bộ / theo đơn vị / theo vai trò

2. **file_storage** — Metadata file upload
   - Lưu file_url (MinIO), metadata (size, type, checksum)
   - Link FK tới module (bai_viet_id, tai_lieu_id, khoa_hoc_id, etc.)

3. **knowledge_base** — Cơ sở tri thức
   - Loại: FAQ, QUY_TRINH, HUONG_DAN
   - Full-text search (pg_tsvector)
   - Tags + category

4. **integration_log** — Log tích hợp giữa các module
   - Ghi lại API call giữa modules
   - Track lỗi, thời gian xử lý
   - Audit trail

## Endpoints (TODO)

### Thông báo
- `GET /api/v1/thong-bao` — Danh sách thông báo của user
- `POST /api/v1/thong-bao` — Tạo thông báo (admin/module nội bộ)
- `PUT /api/v1/thong-bao/{id}/doc` — Đánh dấu đã đọc
- `GET /api/v1/thong-bao/chua-doc` — Số thông báo chưa đọc

### File Storage
- `POST /api/v1/files/upload` — Upload file lên MinIO
- `GET /api/v1/files/{id}` — Lấy metadata + signed URL
- `DELETE /api/v1/files/{id}` — Xóa file (soft delete)

### Knowledge Base
- `GET /api/v1/knowledge-base` — Tìm kiếm trong KB
- `GET /api/v1/knowledge-base/{id}` — Chi tiết bài viết
- `POST /api/v1/knowledge-base` — Tạo bài KB (admin)
- `PUT /api/v1/knowledge-base/{id}` — Cập nhật bài KB

### Internal API (cho module khác)
- `POST /internal/notify` — Gửi thông báo từ module khác
- `POST /internal/log-integration` — Ghi log tích hợp

## Platform Roles

- **QT_ATTT** — Quản trị ATTT: toàn quyền xem logs, quản lý file
- **Tất cả user** — Đọc thông báo của mình
- **Module khác** — Gọi internal API (không qua JWT, dùng internal secret)

## Chạy Service

```bash
cd backend/common_service
source ../venv/bin/activate

# Development
uvicorn common_service.main:app --reload --port 8005

# Health check
curl http://localhost:8005/health
```

Response:
```json
{
  "status": "ok",
  "service": "common",
  "version": "0.1.0"
}
```

## Testing

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest common_service/tests/ -v

# Run with coverage
pytest common_service/tests/ --cov=common_service --cov-report=html
```

## Trạng thái

- [x] Skeleton structure (all files created)
- [x] Config + dependencies (JWT auth, DB session)
- [x] Base models (CongChucRef, DonViRef READONLY)
- [x] Base schemas (SuccessResponse, PaginatedResponse)
- [x] Test fixtures (5 user roles)
- [x] Health check endpoint
- [ ] Database migration (4 tables)
- [ ] Models (thong_bao, file_storage, knowledge_base, integration_log)
- [ ] Endpoints implementation
- [ ] MinIO integration
- [ ] Full-text search (pg_tsvector)
- [ ] Tests (unit + integration)

## Next Steps

1. Chạy migration `common_schema_init.py` để tạo 4 bảng
2. Implement models trong `models/` (thong_bao.py, file_storage.py, etc.)
3. Implement endpoints trong `api/endpoints/` và `api/internal/`
4. Viết tests trong `tests/`
5. MinIO setup (docker-compose.yml)
6. Frontend integration (thông báo notification bell)

## Notes

- KHÔNG SỬA bảng public (cong_chuc, don_vi, vai_tro)
- Tất cả FK user → `public.cong_chuc(id)` (cross-schema)
- Response format chuẩn: `{"success": bool, "data": ..., "message": ...}`
- Trạng thái dùng VARCHAR(50), KHÔNG dùng PostgreSQL ENUM
- Internal API dùng secret key riêng (không qua JWT)

## Tham khảo

- Spec: `docs/shared/SHARED_*.md`
- Portal service: `backend/portal_service/` (pattern tương tự)
- LMS service: `backend/lms_service/` (reference implementation)
