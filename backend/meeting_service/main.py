"""
meeting_service/main.py
========================
FastAPI entry point cho HKG service.
Run: uvicorn meeting_service.main:app --reload --port 8006 --host 127.0.0.1

LƯU Ý: G2/G3a chạy INTERNAL ONLY (host=127.0.0.1). Không expose ra Nginx public
cho tới khi G4 done + UAT pass.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from shared.auth import decode_jwt

# Cho phép import shared.* trước khi import nội bộ
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from meeting_service.config import settings

# ─── Logging cho namespace "hkg.*" ──────────────────────────────────────────
# Thêm 30/07/2026: uvicorn chỉ cấu hình logger của chính nó, không có handler ở
# root, nên mọi logger hkg.* (hkg.authz, hkg.ws, hkg.broadcast, hkg.presentation)
# trước đây KHÔNG in ra dòng nào trong log pm2. Gắn handler stdout để pm2 bắt được.
_hkg_logger = logging.getLogger("hkg")
if not _hkg_logger.handlers:
    _hkg_handler = logging.StreamHandler(sys.stdout)
    _hkg_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    _hkg_logger.addHandler(_hkg_handler)
    _hkg_logger.setLevel(logging.INFO)
    _hkg_logger.propagate = False  # tránh in trùng qua logging.lastResort

from meeting_service.services.rate_limit import limiter
from meeting_service.api.endpoints.cuoc_hop import router as cuoc_hop_router
from meeting_service.api.endpoints.lich_cong_tac import router as lich_cong_tac_router
from meeting_service.api.endpoints.thong_ke_tai_lieu import router as thong_ke_tai_lieu_router
from meeting_service.api.endpoints.truc_ban import router as truc_ban_router
from meeting_service.api.endpoints.doi_soat import router as doi_soat_router
from meeting_service.api.endpoints.ghi_chu import router as ghi_chu_router
from meeting_service.api.endpoints.tai_lieu import (
    router as tai_lieu_router,
    router_cuoc_hop as tai_lieu_cuoc_hop_router,
)
from meeting_service.api.endpoints.diem_danh import (
    router as diem_danh_router,
    router_cuoc_hop as diem_danh_cuoc_hop_router,
)
from meeting_service.api.endpoints.xin_phep_vang import (
    router as xin_phep_vang_router,
)
from meeting_service.api.endpoints.bien_ban import (
    router as bien_ban_router,
    router_cuoc_hop as bien_ban_cuoc_hop_router,
)
from meeting_service.api.endpoints.ket_luan import (
    router as ket_luan_router,
    router_cuoc_hop as ket_luan_cuoc_hop_router,
    router_thong_ke as thong_ke_router,
)
from meeting_service.api.endpoints.cong_chuc import router as cong_chuc_router
from meeting_service.api.endpoints.nhom_thanh_phan import (
    router as nhom_thanh_phan_router,
    router_cuoc_hop as nhom_thanh_phan_cuoc_hop_router,
)
from meeting_service.api.endpoints.presentation_rest import (
    router as presentation_rest_router,
)
from meeting_service.api.endpoints.presentation_ws import (
    router as presentation_ws_router,
)
from meeting_service.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting HQKV8 HKG service on port {settings.service_port} (internal-only)...")
    # APScheduler — chỉ start khi không phải mode test
    if os.getenv("HKG_DISABLE_SCHEDULER") != "true":
        start_scheduler()
    yield
    stop_scheduler()
    print("Shutting down HQKV8 HKG service...")


app = FastAPI(
    title="HQKV8 HKG (Họp Không Giấy)",
    description=(
        "Module quản lý phòng họp không giấy tờ — Chi cục Hải quan KV VIII.\n\n"
        "**G3b status:** Module 1, 3, 4, 5, 9, 10 — đầy đủ endpoints + 4 jobs scheduler."
    ),
    version="0.1.0-G3b",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# Rate limit (Phase 4.1 P0)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ──────────────────────────────────────────────────────────────────
# Middleware decode JWT → set request.state.user_id để rate_limit
# (_key_func) phân biệt per-user thay vì gom toàn cơ quan vào 1 IP NAT.
# Silent-fail nếu token sai/thiếu — auth thật vẫn do CurrentUserDep.
# Phase 4.1 hotfix sau sự cố 429 ngày 11/05/2026: 1 IP công cộng share
# quota dẫn đến chủ tọa upload 10+ tài liệu bị block.
# ──────────────────────────────────────────────────────────────────
class JWTUserIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()
            try:
                payload = decode_jwt(token, settings.secret_key, settings.algorithm)
                if payload and payload.type == "access":
                    request.state.user_id = payload.sub
            except Exception:
                pass  # silent — CurrentUserDep sẽ trả 401 đúng nghĩa
        return await call_next(request)


app.add_middleware(JWTUserIdMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers — Module 1 + 3 + 4 + 5
app.include_router(cuoc_hop_router, prefix="/api/v1/hop-khong-giay")
app.include_router(lich_cong_tac_router, prefix="/api/v1/hop-khong-giay")
app.include_router(thong_ke_tai_lieu_router, prefix="/api/v1/hop-khong-giay")
app.include_router(truc_ban_router, prefix="/api/v1/hop-khong-giay")
app.include_router(doi_soat_router, prefix="/api/v1/hop-khong-giay")
app.include_router(ghi_chu_router, prefix="/api/v1/hop-khong-giay")
app.include_router(tai_lieu_router, prefix="/api/v1/hop-khong-giay")
app.include_router(tai_lieu_cuoc_hop_router, prefix="/api/v1/hop-khong-giay")
app.include_router(diem_danh_router, prefix="/api/v1/hop-khong-giay")
app.include_router(diem_danh_cuoc_hop_router, prefix="/api/v1/hop-khong-giay")
app.include_router(xin_phep_vang_router, prefix="/api/v1/hop-khong-giay")
app.include_router(bien_ban_router, prefix="/api/v1/hop-khong-giay")
app.include_router(bien_ban_cuoc_hop_router, prefix="/api/v1/hop-khong-giay")
app.include_router(ket_luan_router, prefix="/api/v1/hop-khong-giay")
app.include_router(ket_luan_cuoc_hop_router, prefix="/api/v1/hop-khong-giay")
app.include_router(thong_ke_router, prefix="/api/v1/hop-khong-giay")
app.include_router(cong_chuc_router, prefix="/api/v1/hop-khong-giay")
app.include_router(nhom_thanh_phan_router, prefix="/api/v1/hop-khong-giay")
app.include_router(nhom_thanh_phan_cuoc_hop_router, prefix="/api/v1/hop-khong-giay")

# Phase 4.1 — Page-Sync REST endpoint
app.include_router(presentation_rest_router, prefix="/api/v1/hop-khong-giay")

# Phase 4.1 — Page-Sync WebSocket endpoint (BE_P5)
app.include_router(presentation_ws_router, prefix="/ws/hop-khong-giay")


@app.get("/health", tags=["System"])
async def health_check():
    from meeting_service.scheduler import get_scheduler
    sched = get_scheduler()
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": "0.1.0-G3a",
        "scheduler": {
            "running": sched is not None and sched.running if sched else False,
            "jobs": (
                [j.id for j in sched.get_jobs()] if sched and sched.running else []
            ),
        },
        "modules": {
            "1_cuoc_hop": "ready",
            "3_tai_lieu": "ready (filesystem MVP)",
            "4_diem_danh": "ready",
            "5_xin_phep_vang": "ready (APScheduler auto-approve)",
            "9_bien_ban": "ready (Mock CKS, DOCX/PDF via ReportLab)",
            "10_ket_luan": "ready (dashboard 1 cấp)",
        },
    }
