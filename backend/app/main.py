"""
app/main.py
===========
FastAPI Application Entry Point.

Khởi tạo và cấu hình ứng dụng:
- CORS middleware
- API routes
- Exception handlers
- Startup/shutdown events
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.api.v1.api import api_router


# =============================================================================
# LIFESPAN (Startup/Shutdown Events)
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Quản lý vòng đời ứng dụng.
    
    Startup:
    - Khởi tạo database connection pool
    - Load configurations
    - Initialize services
    
    Shutdown:
    - Close database connections
    - Cleanup resources
    """
    # -------------------------------------------------------------------------
    # STARTUP
    # -------------------------------------------------------------------------
    print("=" * 60)
    print(f"🚀 Starting {settings.app_name}...")
    print(f"📍 Environment: {settings.app_env}")
    print(f"🔧 Debug mode: {settings.debug}")
    print(f"🗄️  Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    print("=" * 60)
    
    # Khởi tạo resources nếu cần
    # Ví dụ: cache, message queue, etc.
    
    yield  # Application is running
    
    # -------------------------------------------------------------------------
    # SHUTDOWN
    # -------------------------------------------------------------------------
    print("=" * 60)
    print("👋 Shutting down application...")
    print("=" * 60)
    
    # Cleanup resources nếu cần
    # Ví dụ: close connections, flush buffers, etc.


# =============================================================================
# APPLICATION FACTORY
# =============================================================================

def create_application() -> FastAPI:
    """
    Factory function tạo FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    application = FastAPI(
        title=settings.app_name,
        description="""
## Hệ thống Đánh giá KPI & Xếp loại Công chức
### Chi cục Hải quan Khu vực VIII

**Tính năng chính:**
- 🔐 Xác thực JWT với phân quyền RBAC
- 📝 Kê khai sản phẩm/công việc hàng tháng
- ✅ Phê duyệt theo luồng nghiệp vụ
- 📊 Đánh giá và xếp loại công chức
- 📈 Báo cáo và thống kê

**Tài liệu tham chiếu:**
- Nghị định 335/2025/NĐ-CP
- Quy chế KPI Chi cục HQKV8
        """,
        version="0.4.0-alpha",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url="/docs" if settings.debug else None,  # Ẩn docs trong production
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )
    
    # -------------------------------------------------------------------------
    # CORS MIDDLEWARE
    # -------------------------------------------------------------------------
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # -------------------------------------------------------------------------
    # INCLUDE API ROUTERS
    # -------------------------------------------------------------------------
    application.include_router(
        api_router,
        prefix=settings.api_v1_prefix,
    )
    
    return application


# =============================================================================
# CREATE APP INSTANCE
# =============================================================================

app = create_application()


# =============================================================================
# ROOT ENDPOINT
# =============================================================================

@app.get(
    "/",
    tags=["Root"],
    summary="API Health Check",
    description="Kiểm tra trạng thái API server",
)
async def root():
    """
    Root endpoint - Health check.
    
    Returns:
        dict: Thông tin cơ bản về API
    """
    return {
        "success": True,
        "message": f"Chào mừng đến với {settings.app_name}",
        "version": "0.4.0-alpha",
        "docs": "/docs" if settings.debug else "Disabled in production",
        "api_prefix": settings.api_v1_prefix,
    }


@app.get(
    "/health",
    tags=["Root"],
    summary="Health Check",
)
async def health_check():
    """
    Health check endpoint cho monitoring.
    
    Returns:
        dict: Status và environment info
    """
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "debug": settings.debug,
    }


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    """
    Custom handler cho validation errors.
    Trả về format chuẩn với chi tiết lỗi từng field.
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])  # Bỏ "body" prefix
        errors.append({
            "field": field or "unknown",
            "message": error["msg"],
            "type": error["type"],
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VAL_001",
                "message": "Dữ liệu không hợp lệ",
                "details": errors,
            }
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
):
    """
    Global exception handler - catch all unhandled exceptions.
    
    Trong production:
    - Log chi tiết lỗi
    - Trả về message chung chung (không leak thông tin)
    
    Trong development:
    - Trả về chi tiết lỗi để debug
    """
    # TODO: Implement proper logging
    # logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    if settings.debug:
        # Development: Trả về chi tiết lỗi
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(exc),
                    "type": type(exc).__name__,
                }
            },
        )
    else:
        # Production: Message chung
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau.",
                }
            },
        )


# =============================================================================
# RUN WITH UVICORN (Development)
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
