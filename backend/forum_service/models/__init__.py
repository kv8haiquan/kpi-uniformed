"""
forum_service/models/__init__.py
=================================
Import tat ca 5 Forum models + Base + READONLY stubs.
"""

from forum_service.models.base import Base, CongChucRef, DonViRef
from forum_service.models.chuyen_muc import ChuyenMuc
from forum_service.models.chu_de import ChuDe
from forum_service.models.tra_loi import TraLoi
from forum_service.models.bieu_quyet import BieuQuyet
from forum_service.models.theo_doi import TheoDoi

__all__ = [
    "Base",
    "CongChucRef",
    "DonViRef",
    "ChuyenMuc",
    "ChuDe",
    "TraLoi",
    "BieuQuyet",
    "TheoDoi",
]
