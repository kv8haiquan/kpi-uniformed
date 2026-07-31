"""
app/core/thong_bao_helper.py
============================
Helper gọi Common service Internal API để tạo thông báo cho CC khi LĐ TỪ CHỐI / TRẢ LẠI.

Fire-and-forget — lỗi tạo thông báo KHÔNG ảnh hưởng logic chính.
Pattern copy từ lms_service/services/thong_bao_helper.py.

Loại thông báo cố định = "KPI" để filter ở UI thông báo.
"""

import logging
import os
import uuid
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

COMMON_INTERNAL_URL = os.getenv("COMMON_INTERNAL_URL", "http://localhost:8005/internal/v1")
from app.config import settings as _settings

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY") or _settings.internal_api_key


async def gui_thong_bao(
    nguoi_nhan_id: uuid.UUID,
    tieu_de: str,
    noi_dung: Optional[str] = None,
    muc_do: str = "QUAN_TRONG",
    link_url: Optional[str] = None,
    doi_tuong_type: Optional[str] = None,
    doi_tuong_id: Optional[uuid.UUID] = None,
) -> None:
    """Gửi 1 thông báo qua Common internal API. Fire-and-forget."""
    payload = {
        "nguoi_nhan_id": str(nguoi_nhan_id),
        "tieu_de": tieu_de[:300],
        "noi_dung": noi_dung,
        "loai": "KPI",
        "muc_do": muc_do,
        "link_url": link_url,
        "doi_tuong_type": doi_tuong_type,
        "doi_tuong_id": str(doi_tuong_id) if doi_tuong_id else None,
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{COMMON_INTERNAL_URL}/thong-bao",
                json=payload,
                headers={"X-Internal-Key": INTERNAL_API_KEY},
            )
            if resp.status_code != 201:
                logger.warning(
                    "Tạo thông báo KPI thất bại: %s %s", resp.status_code, resp.text
                )
    except Exception as e:
        logger.warning("Không gửi được thông báo KPI: %s", e)
