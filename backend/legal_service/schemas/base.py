"""
legal_service/schemas/base.py
==============================
Base response schemas cho module Phap luat.
Re-export tu shared.schemas.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.schemas import (
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    PaginationInfo,
    SuccessResponse,
)

__all__ = [
    "SuccessResponse",
    "PaginatedResponse",
    "PaginationInfo",
    "ErrorDetail",
    "ErrorResponse",
]
