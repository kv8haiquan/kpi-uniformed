"""
forum_service/main.py
======================
FastAPI entry point cho module Dien dan.
Chay: uvicorn forum_service.main:app --reload --port 8002
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "forum",
        "version": "0.1.0",
    }
