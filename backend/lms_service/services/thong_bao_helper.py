"""
lms_service/services/thong_bao_helper.py
==========================================
Helper goi Common internal API de tao thong bao.
Fire-and-forget — loi tao thong bao KHONG anh huong logic chinh.
"""

import logging
import uuid
from typing import Optional

import httpx

from lms_service.config import settings

logger = logging.getLogger(__name__)

COMMON_INTERNAL_URL = getattr(settings, 'common_internal_url', 'http://localhost:8005/internal/v1')
INTERNAL_API_KEY = getattr(settings, 'internal_api_key', 'kv08-internal-secret-key')


async def gui_thong_bao_bulk(
    nguoi_nhan_ids: list[uuid.UUID],
    tieu_de: str,
    noi_dung: Optional[str] = None,
    muc_do: str = "BINH_THUONG",
    link_url: Optional[str] = None,
    doi_tuong_type: Optional[str] = None,
    doi_tuong_id: Optional[uuid.UUID] = None,
):
    """Gui thong bao hang loat qua Common internal API. Fire-and-forget."""
    if not nguoi_nhan_ids:
        return

    payload = {
        "nguoi_nhan_ids": [str(uid) for uid in nguoi_nhan_ids],
        "tieu_de": tieu_de[:300],
        "noi_dung": noi_dung,
        "loai": "LMS",
        "muc_do": muc_do,
        "link_url": link_url,
        "doi_tuong_type": doi_tuong_type,
        "doi_tuong_id": str(doi_tuong_id) if doi_tuong_id else None,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{COMMON_INTERNAL_URL}/thong-bao/bulk",
                json=payload,
                headers={"X-Internal-Key": INTERNAL_API_KEY},
            )
            if resp.status_code != 201:
                logger.warning("Tao thong bao bulk that bai: %s %s", resp.status_code, resp.text)
    except Exception as e:
        logger.warning("Khong the gui thong bao: %s", e)


async def gui_thong_bao(
    nguoi_nhan_id: uuid.UUID,
    tieu_de: str,
    noi_dung: Optional[str] = None,
    muc_do: str = "BINH_THUONG",
    link_url: Optional[str] = None,
    doi_tuong_type: Optional[str] = None,
    doi_tuong_id: Optional[uuid.UUID] = None,
):
    """Gui 1 thong bao qua Common internal API. Fire-and-forget."""
    payload = {
        "nguoi_nhan_id": str(nguoi_nhan_id),
        "tieu_de": tieu_de[:300],
        "noi_dung": noi_dung,
        "loai": "LMS",
        "muc_do": muc_do,
        "link_url": link_url,
        "doi_tuong_type": doi_tuong_type,
        "doi_tuong_id": str(doi_tuong_id) if doi_tuong_id else None,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{COMMON_INTERNAL_URL}/thong-bao",
                json=payload,
                headers={"X-Internal-Key": INTERNAL_API_KEY},
            )
            if resp.status_code != 201:
                logger.warning("Tao thong bao that bai: %s %s", resp.status_code, resp.text)
    except Exception as e:
        logger.warning("Khong the gui thong bao: %s", e)
