"""
common_service/models/__init__.py
==================================
SQLAlchemy models cho module Common (schema=common).

4 bang:
  - ThongBao: Notification Center da module
  - FileStorage: File metadata tren MinIO
  - KnowledgeBase: Kho SOP/FAQ + Full-text Search
  - KpiIntegrationLog: Tich hop diem KPI tu LMS/Forum/Legal

2 READONLY stubs (public schema):
  - CongChucRef: public.cong_chuc (chi SELECT/JOIN)
  - DonViRef: public.don_vi (chi SELECT/JOIN)
"""

from .base import Base, CongChucRef, DonViRef
from .file_storage import FileStorage
from .knowledge_base import KnowledgeBase
from .kpi_integration_log import KpiIntegrationLog
from .thong_bao import ThongBao

__all__ = [
    "Base",
    "CongChucRef",
    "DonViRef",
    "ThongBao",
    "FileStorage",
    "KnowledgeBase",
    "KpiIntegrationLog",
]
