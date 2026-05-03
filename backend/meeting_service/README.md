# meeting_service — HKG (Họp Không Giấy)

Module phòng họp không giấy tờ. **Trạng thái: G2 — Module 1 only.**

## ⚠️ Internal-only

Service hiện chạy **internal-only**, **KHÔNG expose** ra Nginx public. Sẽ mở public ở giai đoạn UAT (sau G4).

- Bind: `127.0.0.1:8006`
- Test bằng `curl localhost:8006` hoặc Postman trên máy dev
- KHÔNG cấu hình Nginx reverse proxy cho `:8006` cho tới khi G4 done + UAT pass

## Run

```bash
# Yêu cầu: backend/.env có SECRET_KEY trùng KPI
cd backend
source venv/bin/activate
uvicorn meeting_service.main:app --reload --host 127.0.0.1 --port 8006
```

Health check:

```bash
curl http://localhost:8006/health
# → {"status":"ok","service":"meeting","version":"0.1.0-G2", "modules": {...}}
```

Swagger UI: <http://localhost:8006/docs>

## Test

DB là production đào tạo → bắt buộc opt-in:

```bash
ALLOW_PROD_TEST=true pytest meeting_service/tests/ -v
```

Methodology:
- TX rollback per test (không persist data)
- TEST-G2-* dedicated accounts (không dùng user thật)
- Auto cleanup teardown — xóa hết TEST-G2-* sau session

## Endpoints (Module 1 — 7 endpoints)

| Method | Path |
|---|---|
| POST | `/api/v1/hop-khong-giay/cuoc-hop/` |
| GET | `/api/v1/hop-khong-giay/cuoc-hop/` |
| GET | `/api/v1/hop-khong-giay/cuoc-hop/{id}` |
| PATCH | `/api/v1/hop-khong-giay/cuoc-hop/{id}` |
| POST | `/api/v1/hop-khong-giay/cuoc-hop/{id}/huy` |
| POST | `/api/v1/hop-khong-giay/cuoc-hop/{id}/gui-giay-moi` |
| POST | `/api/v1/hop-khong-giay/cuoc-hop/{id}/xac-nhan` |

Module 3, 4, 5, 9, 10 → G3.

## Architecture

```
meeting_service/
├── main.py                  # FastAPI port 8006
├── config.py                # Settings từ .env
├── dependencies.py          # JWT + permission helpers
├── models/                  # 10 SQLAlchemy models (schema meeting)
├── schemas/                 # Pydantic schemas
├── services/
│   ├── audit_log_service.py     # → common.audit_log (module='MEETING')
│   ├── notification_service.py  # → common.thong_bao (loai='MEETING')
│   ├── minio_service.py         # SKELETON — G3 implement
│   └── cuoc_hop_service.py      # Business logic Module 1
├── api/endpoints/
│   └── cuoc_hop.py
└── tests/
    ├── conftest.py          # Production guard + fixtures
    └── test_cuoc_hop.py
```

## Phân quyền (2 lớp)

- **Lớp 1 — vai_tro KPI**: `SUPER_ADMIN, CHI_CUC_TRUONG, PHO_CHI_CUC_TRUONG, TRUONG_DON_VI, PHO_DON_VI, CONG_CHUC, TCCB`.
- **Lớp 2 — platform_role HKG**: `THU_KY_HOP, CHANH_VP, TRUONG_CNTT, DANG_VIEN, BI_THU_CHI_BO, PHO_BI_THU` (`CHU_TOA_HOP` là dynamic, không seed).

Helpers trong `dependencies.py`:
- `require_role(*vai_tro)` — vai_tro KPI
- `require_platform_role(*ma_role)` — platform role HKG
- `require_can_view_meeting(cuoc_hop_id)` — load + check view
- `require_can_edit_meeting(cuoc_hop_id)` — load + check edit (chu_toa | thu_ky | SUPER_ADMIN | TRUONG_CNTT)
