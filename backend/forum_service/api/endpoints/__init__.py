"""
forum_service/api/endpoints/__init__.py
========================================
Export all endpoint routers.
"""

from forum_service.api.endpoints.bieu_quyet import router as bieu_quyet_router
from forum_service.api.endpoints.chu_de import router as chu_de_router
from forum_service.api.endpoints.chuyen_muc import router as chuyen_muc_router
from forum_service.api.endpoints.dashboard import (
    bao_cao_router,
    dashboard_router,
)
from forum_service.api.endpoints.theo_doi import router as theo_doi_router
from forum_service.api.endpoints.tim_kiem import (
    search_router,
    tags_router,
)
from forum_service.api.endpoints.tra_loi import router as tra_loi_router

__all__ = [
    "chuyen_muc_router",
    "chu_de_router",
    "tra_loi_router",
    "bieu_quyet_router",
    "search_router",
    "tags_router",
    "theo_doi_router",
    "dashboard_router",
    "bao_cao_router",
]
