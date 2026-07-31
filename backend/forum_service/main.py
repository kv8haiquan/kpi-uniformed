"""
forum_service/main.py
======================
FastAPI entry point cho module Dien dan.
Chay: uvicorn forum_service.main:app --reload --port 8002
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from forum_service.api.endpoints import (
    bao_cao_router,
    bieu_quyet_router,
    chu_de_router,
    chuyen_muc_router,
    dashboard_router,
    search_router,
    tags_router,
    theo_doi_router,
    tra_loi_router,
)
from forum_service.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup va shutdown events."""
    print(f"Starting HQKV8 Dien dan service on port 8002...")
    yield
    print(f"Shutting down HQKV8 Dien dan service...")


app = FastAPI(
    title="HQKV8 Dien dan",
    description="Module Dien dan - Chi cuc Hai quan Khu vuc VIII",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers — prefix /api/forum/v1
API_PREFIX = "/api/forum/v1"
app.include_router(chuyen_muc_router, prefix=API_PREFIX)
app.include_router(chu_de_router, prefix=API_PREFIX)
app.include_router(tra_loi_router, prefix=API_PREFIX)
app.include_router(bieu_quyet_router, prefix=API_PREFIX)
app.include_router(search_router, prefix=API_PREFIX)
app.include_router(tags_router, prefix=API_PREFIX)
app.include_router(theo_doi_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(bao_cao_router, prefix=API_PREFIX)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "forum",
        "version": "0.1.0",
    }
