"""
lms_service/main.py
======================
FastAPI entry point cho module Dao tao.
Chay: uvicorn lms_service.main:app --reload --port 8001
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from lms_service.config import settings
from lms_service.api.endpoints.chuyen_de import router as chuyen_de_router
from lms_service.api.endpoints.khoa_hoc import router as khoa_hoc_router
from lms_service.api.endpoints.bai_hoc import router as bai_hoc_router
from lms_service.api.endpoints.dang_ky import router as dang_ky_router
from lms_service.api.endpoints.cau_hoi import router as cau_hoi_router
from lms_service.api.endpoints.bai_kiem_tra import router as bai_kiem_tra_router
from lms_service.api.endpoints.chung_chi import router as chung_chi_router
from lms_service.api.endpoints.bao_cao import router as bao_cao_router
from lms_service.api.endpoints.cbcc import router as cbcc_router
from lms_service.api.endpoints.upload import router as upload_router
# DGNL routers
from lms_service.api.endpoints.linh_vuc import router as linh_vuc_router
from lms_service.api.endpoints.vi_tri_viec_lam import router as vi_tri_viec_lam_router
from lms_service.api.endpoints.ky_thi import router as ky_thi_router
from lms_service.api.endpoints.thi_sinh import router as thi_sinh_router
from lms_service.api.endpoints.cau_truc_de_template import router as cau_truc_de_template_router
from lms_service.api.endpoints.cau_hoi_dgnl import router as cau_hoi_dgnl_router

# Tao thu muc uploads truoc khi mount StaticFiles (tranh loi khoi dong)
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs("uploads", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup va shutdown events."""
    print("Starting HQKV8 Dao tao service on port 8001...")
    yield
    print("Shutting down HQKV8 Dao tao service...")


app = FastAPI(
    title="HQKV8 Dao tao",
    description="Module Dao tao - Chi cuc Hai quan Khu vuc VIII",
    version="0.1.0",
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

# Static files — serve uploads qua /uploads/lms/...
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Routers
app.include_router(chuyen_de_router, prefix="/api/v1/lms")
app.include_router(khoa_hoc_router, prefix="/api/v1/lms")
app.include_router(bai_hoc_router, prefix="/api/v1/lms")
app.include_router(dang_ky_router, prefix="/api/v1/lms")
app.include_router(cau_hoi_router, prefix="/api/v1/lms")
app.include_router(bai_kiem_tra_router, prefix="/api/v1/lms")
app.include_router(chung_chi_router, prefix="/api/v1/lms")
app.include_router(bao_cao_router, prefix="/api/v1/lms")
app.include_router(cbcc_router, prefix="/api/v1/lms")
app.include_router(upload_router, prefix="/api/v1/lms")
# DGNL routers
app.include_router(linh_vuc_router, prefix="/api/v1/lms")
app.include_router(vi_tri_viec_lam_router, prefix="/api/v1/lms")
app.include_router(ky_thi_router, prefix="/api/v1/lms")
app.include_router(thi_sinh_router, prefix="/api/v1/lms")
app.include_router(cau_truc_de_template_router, prefix="/api/v1/lms")
app.include_router(cau_hoi_dgnl_router, prefix="/api/v1/lms")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "lms",
        "version": "0.1.0",
    }
