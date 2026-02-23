"""
portal_service/schemas/base.py
==============================
Base response schemas cho module Tai lieu.
Re-export tu shared.schemas.
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
