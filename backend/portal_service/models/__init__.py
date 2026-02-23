"""
portal_service/models/__init__.py
==================================
Export tat ca models cho Portal service.

Models:
  - Base: DeclarativeBase
  - CongChucRef, DonViRef: READONLY stub cho cross-schema FK
  - ChuyenMuc: 4 chuyen muc (Tin chi dao, Thong bao, Tin hoat dong, Cap nhat phap luat)
  - ThuMuc: Tree structure thu muc tai lieu (Van ban noi bo, Tai lieu dao tao, ...)
  - BaiViet: Workflow NHAP → KIEM_TRA → DUYET → XUAT_BAN → THU_HOI
  - TaiLieu: Versioning + JSONB tags/metadata + phan quyen theo don vi
"""

from portal_service.models.base import Base, CongChucRef, DonViRef
from portal_service.models.chuyen_muc import ChuyenMuc
from portal_service.models.thu_muc import ThuMuc
from portal_service.models.bai_viet import BaiViet
from portal_service.models.tai_lieu import TaiLieu

__all__ = [
    "Base",
    "CongChucRef",
    "DonViRef",
    "ChuyenMuc",
    "ThuMuc",
    "BaiViet",
    "TaiLieu",
]
