"""
common_service/services/storage_client.py
==========================================
File storage client — MinIO hoac local fallback.

Neu co bien moi truong MINIO_ENDPOINT → dung MinIO SDK.
Neu khong → luu file local vao data/uploads/.

Methods:
  upload(file_path, file_data) -> str
  get_url(file_path) -> str
  delete(file_path) -> bool
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# MinIO config tu environment
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "kv08-files")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# Local fallback directory
LOCAL_UPLOAD_DIR = Path(
    os.getenv("LOCAL_UPLOAD_DIR", os.path.join(os.path.dirname(__file__), "..", "data", "uploads"))
)

# Flag — co dung MinIO khong
_use_minio = bool(MINIO_ENDPOINT and MINIO_ACCESS_KEY and MINIO_SECRET_KEY)
_minio_client = None


def _get_minio():
    """Lazy init MinIO client."""
    global _minio_client
    if _minio_client is not None:
        return _minio_client

    try:
        from minio import Minio

        _minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE,
        )
        # Dam bao bucket ton tai
        if not _minio_client.bucket_exists(MINIO_BUCKET):
            _minio_client.make_bucket(MINIO_BUCKET)
            logger.info("Tao MinIO bucket: %s", MINIO_BUCKET)
        return _minio_client
    except ImportError:
        logger.warning("MinIO SDK chua cai dat (pip install minio). Dung local storage.")
        return None
    except Exception as e:
        logger.warning("Khong ket noi duoc MinIO: %s. Dung local storage.", e)
        return None


async def upload(file_path: str, file_data: bytes) -> str:
    """Upload file len MinIO hoac luu local.

    Args:
        file_path: Duong dan relative (vd: "lms/videos/uuid.mp4")
        file_data: Noi dung file (bytes)

    Returns:
        URL truy cap file.
    """
    if _use_minio:
        client = _get_minio()
        if client is not None:
            import io
            data_stream = io.BytesIO(file_data)
            client.put_object(
                MINIO_BUCKET,
                file_path,
                data_stream,
                length=len(file_data),
            )
            logger.info("Upload MinIO: %s/%s (%d bytes)", MINIO_BUCKET, file_path, len(file_data))
            return f"/files/{file_path}"

    # Fallback: luu local
    local_path = LOCAL_UPLOAD_DIR / file_path
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(file_data)
    logger.warning("MinIO chua cau hinh, luu file local: %s", local_path)
    return f"/files/{file_path}"


async def get_url(file_path: str) -> str:
    """Lay URL truy cap file."""
    return f"/files/{file_path}"


async def delete(file_path: str) -> bool:
    """Xoa file vat ly (MinIO hoac local).

    NOTE: Hien tai chi soft delete trong DB.
    File vat ly se duoc cron job don dep sau 30 ngay.
    """
    if _use_minio:
        client = _get_minio()
        if client is not None:
            try:
                client.remove_object(MINIO_BUCKET, file_path)
                return True
            except Exception as e:
                logger.error("Loi xoa file MinIO %s: %s", file_path, e)
                return False

    # Fallback: xoa local
    local_path = LOCAL_UPLOAD_DIR / file_path
    if local_path.exists():
        local_path.unlink()
        return True
    return False
