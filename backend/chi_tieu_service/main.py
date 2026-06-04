"""
chi_tieu_service/main.py
========================
FastAPI entry point — Module Quan ly Chi tieu Don vi.
Chay: uvicorn chi_tieu_service.main:app --reload --port 8007
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chi_tieu_service.config import settings
from chi_tieu_service.api.endpoints.linh_vuc import router as linh_vuc_router
from chi_tieu_service.api.endpoints.danh_muc import router as danh_muc_router
from chi_tieu_service.api.endpoints.giao_nam import router as giao_nam_router
from chi_tieu_service.api.endpoints.dang_ky import router as dang_ky_router
from chi_tieu_service.api.endpoints.duyet import router as duyet_router
from chi_tieu_service.api.endpoints.bao_cao import router as bao_cao_router
from chi_tieu_service.api.endpoints.nguoi_theo_doi import router as nguoi_theo_doi_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting HQKV8 Chi tieu service on port {settings.service_port}...")
    yield
    print("Shutting down HQKV8 Chi tieu service...")


app = FastAPI(
    title="HQKV8 Chi tieu Don vi",
    description="Module Quan ly Chi tieu Don vi - Chi cuc Hai quan Khu vuc VIII",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_PREFIX = "/api/v1/chi-tieu"
app.include_router(linh_vuc_router, prefix=_PREFIX)
app.include_router(danh_muc_router, prefix=_PREFIX)
app.include_router(giao_nam_router, prefix=_PREFIX)
app.include_router(dang_ky_router, prefix=_PREFIX)
app.include_router(duyet_router, prefix=_PREFIX)
app.include_router(bao_cao_router, prefix=_PREFIX)
app.include_router(nguoi_theo_doi_router, prefix=_PREFIX)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "chi_tieu", "version": "0.1.0"}
