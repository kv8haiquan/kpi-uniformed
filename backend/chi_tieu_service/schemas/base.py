"""
chi_tieu_service/schemas/base.py
================================
Re-export base response schemas tu shared.schemas.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.schemas import (
    SuccessResponse,
    PaginatedResponse,
    PaginationInfo,
    ErrorDetail,
    ErrorResponse,
)

__all__ = [
    "SuccessResponse",
    "PaginatedResponse",
    "PaginationInfo",
    "ErrorDetail",
    "ErrorResponse",
]
