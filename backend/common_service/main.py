"""
common_service/main.py
======================
FastAPI entry point cho module Common (Thông báo, File Storage, Knowledge Base, KPI Integration).
Chạy: uvicorn common_service.main:app --reload --port 8005
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from common_service.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup và shutdown events."""
    print("Starting HQKV8 Common service on port 8005...")
    yield
    print("Shutting down HQKV8 Common service...")


app = FastAPI(
    title="HQKV8 Common Service",
    description="Module dùng chung — Thông báo, File Storage, Knowledge Base, KPI Integration — Chi cục Hải quan KV8",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Exception handler — chuẩn hóa lỗi không xử lý
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Lỗi hệ thống, vui lòng thử lại sau",
            },
        },
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "common",
        "version": "0.1.0",
    }


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
API_PREFIX = "/api/common/v1"
INTERNAL_PREFIX = "/internal/v1"

# Public API — Frontend goi (JWT Bearer token)
from common_service.api.endpoints.thong_bao import router as thong_bao_router
from common_service.api.endpoints.file_storage import router as file_storage_router
from common_service.api.endpoints.knowledge_base import router as kb_router
from common_service.api.endpoints.kpi_log import router as kpi_log_router
from common_service.api.endpoints.search import router as search_router

app.include_router(thong_bao_router, prefix=API_PREFIX)
app.include_router(file_storage_router, prefix=API_PREFIX)
app.include_router(kb_router, prefix=API_PREFIX)
app.include_router(kpi_log_router, prefix=API_PREFIX)
app.include_router(search_router, prefix=API_PREFIX)

# Internal API — Module khac goi (X-Internal-Key header)
from common_service.api.internal.thong_bao import router as thong_bao_internal_router
from common_service.api.internal.knowledge_base import router as kb_internal_router
from common_service.api.internal.kpi_log import router as kpi_log_internal_router

app.include_router(thong_bao_internal_router, prefix=INTERNAL_PREFIX)
app.include_router(kb_internal_router, prefix=INTERNAL_PREFIX)
app.include_router(kpi_log_internal_router, prefix=INTERNAL_PREFIX)
