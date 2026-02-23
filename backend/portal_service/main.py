"""
portal_service/main.py
======================
FastAPI entry point cho module Portal (CMS tin tức nội bộ + Tài liệu).
Chạy: uvicorn portal_service.main:app --reload --port 8004
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from portal_service.api.endpoints import bai_viet, chuyen_muc, dashboard, tai_lieu, thu_muc
from portal_service.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup và shutdown events."""
    print("Starting HQKV8 Portal service on port 8004...")
    yield
    print("Shutting down HQKV8 Portal service...")


app = FastAPI(
    title="HQKV8 Portal",
    description="Module Portal — CMS tin tức nội bộ & Tài liệu — Chi cục Hải quan KV8",
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
        "service": "portal",
        "version": "0.1.0",
    }


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
API_PREFIX = "/api/v1"

app.include_router(chuyen_muc.router, prefix=API_PREFIX)
app.include_router(bai_viet.router, prefix=API_PREFIX)
app.include_router(thu_muc.router, prefix=API_PREFIX)
app.include_router(tai_lieu.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
