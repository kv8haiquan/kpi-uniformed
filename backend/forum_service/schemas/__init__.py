"""
forum_service/schemas/__init__.py
==================================
Import tat ca Forum schemas.
"""

# Base response schemas
from forum_service.schemas.base import (
    SuccessResponse,
    PaginatedResponse,
    PaginationInfo,
    ErrorDetail,
    ErrorResponse,
)

# Chuyen muc schemas
from forum_service.schemas.chuyen_muc import (
    ChuyenMucCreate,
    ChuyenMucUpdate,
    ChuDeMoiNhat,
    ChuyenMucResponse,
)

# Chu de schemas
from forum_service.schemas.chu_de import (
    UserBrief,
    ChuDeCreate,
    ChuDeUpdate,
    HanhDongChuDe,
    ChonDapAnChuan,
    ChuDeListItem,
    TraLoiInChuDe,
    ChuDeDetail,
)

# Tra loi schemas
from forum_service.schemas.tra_loi import (
    TraLoiCreate,
    TraLoiUpdate,
    TraLoiResponse,
)

# Bieu quyet schemas
from forum_service.schemas.bieu_quyet import (
    BieuQuyetCreate,
    BieuQuyetDelete,
    BieuQuyetResponse,
)

# Theo doi schemas
from forum_service.schemas.theo_doi import (
    TheoDoiResponse,
)

# Dashboard schemas
from forum_service.schemas.dashboard import (
    DashboardSummary,
    BaoCaoCaNhan,
    BaoCaoDonVi,
    TopContributor,
)

__all__ = [
    # Base
    "SuccessResponse",
    "PaginatedResponse",
    "PaginationInfo",
    "ErrorDetail",
    "ErrorResponse",
    # Chuyen muc
    "ChuyenMucCreate",
    "ChuyenMucUpdate",
    "ChuDeMoiNhat",
    "ChuyenMucResponse",
    # Chu de
    "UserBrief",
    "ChuDeCreate",
    "ChuDeUpdate",
    "HanhDongChuDe",
    "ChonDapAnChuan",
    "ChuDeListItem",
    "TraLoiInChuDe",
    "ChuDeDetail",
    # Tra loi
    "TraLoiCreate",
    "TraLoiUpdate",
    "TraLoiResponse",
    # Bieu quyet
    "BieuQuyetCreate",
    "BieuQuyetDelete",
    "BieuQuyetResponse",
    # Theo doi
    "TheoDoiResponse",
    # Dashboard
    "DashboardSummary",
    "BaoCaoCaNhan",
    "BaoCaoDonVi",
    "TopContributor",
]
