"""
legal_service/main.py
======================
FastAPI entry point cho module Phap luat.
Chay: uvicorn legal_service.main:app --reload --port 8003

Prefix:
  External API: /api/legal/v1
  Internal API: /internal/v1/legal

Endpoints tong cong: 25+
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from legal_service.api.endpoints.bao_cao import router as bao_cao_router
from legal_service.api.endpoints.don_vi import router as don_vi_router
from legal_service.api.endpoints.loai_van_ban import router as loai_vb_router
from legal_service.api.endpoints.quiz import router as quiz_router
from legal_service.api.endpoints.van_ban import router as van_ban_router
from legal_service.api.endpoints.xac_nhan_doc import router as xac_nhan_router
from legal_service.api.internal.van_ban import router as internal_vb_router
from legal_service.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup va shutdown events."""
    print("Starting HQKV8 Phap luat service on port 8003...")
    yield
    print("Shutting down HQKV8 Phap luat service...")


app = FastAPI(
    title="HQKV8 Phap luat",
    description="Module Phap luat - Chi cuc Hai quan Khu vuc VIII",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler chuan hoa error response
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Xu ly HTTPException: giu nguyen status_code va detail co san."""
    # Detail co the la dict (format chuan) hoac string
    if isinstance(exc.detail, dict):
        content = exc.detail
    else:
        content = {
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": str(exc.detail),
            },
        }
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Bat loi khong mong doi va tra ve error format chuan.
    Log loi chi tiet de debug nhung KHONG expose ra client.
    """
    import logging
    logging.error(f"Loi khong mong doi: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Da xay ra loi he thong. Vui long thu lai sau.",
            },
        },
    )


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "legal",
        "version": "1.0.0",
    }


# -----------------------------------------------------------------------
# External API routers — dung cho frontend
# -----------------------------------------------------------------------
app.include_router(loai_vb_router, prefix="/api/legal/v1")
app.include_router(don_vi_router, prefix="/api/legal/v1")
app.include_router(van_ban_router, prefix="/api/legal/v1")
app.include_router(xac_nhan_router, prefix="/api/legal/v1")
app.include_router(bao_cao_router, prefix="/api/legal/v1")
app.include_router(quiz_router, prefix="/api/legal/v1")

# -----------------------------------------------------------------------
# Internal API routers — dung cho cac module khac goi
# -----------------------------------------------------------------------
app.include_router(internal_vb_router, prefix="/internal/v1/legal")

# -----------------------------------------------------------------------
# Static files — serve file upload van ban phap luat
# -----------------------------------------------------------------------
_upload_dir = Path("uploads/legal")
_upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads/legal", StaticFiles(directory=str(_upload_dir)), name="uploads_legal")
