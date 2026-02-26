"""
common_service/services/file_storage_service.py
=================================================
Business logic cho File Storage.

Methods:
  - upload_file: upload file + luu metadata
  - get_file_info: lay thong tin file
  - delete_file: soft delete file
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common_service.models.file_storage import FileStorage
from common_service.schemas.file_storage import ALLOWED_MODULES
from common_service.services import storage_client


# ---------------------------------------------------------------------------
# Mime type mapping va file size limits
# ---------------------------------------------------------------------------

ALLOWED_MIME_TYPES: dict[str, tuple[str, str]] = {
    # Tai lieu
    "application/pdf": ("documents", "PDF"),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ("documents", "DOCX"),
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ("documents", "XLSX"),
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ("documents", "PPTX"),
    # Hinh anh
    "image/jpeg": ("images", "IMAGE"),
    "image/png": ("images", "IMAGE"),
    "image/gif": ("images", "IMAGE"),
    # Video
    "video/mp4": ("videos", "VIDEO"),
    # Nen
    "application/zip": ("archives", "ZIP"),
    "application/x-rar-compressed": ("archives", "ZIP"),
}

# Gioi han kich thuoc theo loai (bytes)
FILE_SIZE_LIMITS: dict[str, int] = {
    "documents": 50 * 1024 * 1024,    # 50MB
    "images": 10 * 1024 * 1024,       # 10MB
    "videos": 500 * 1024 * 1024,      # 500MB
    "archives": 100 * 1024 * 1024,    # 100MB
}


# ---------------------------------------------------------------------------
# Public methods
# ---------------------------------------------------------------------------


async def upload_file(
    db: AsyncSession,
    file: UploadFile,
    module: str,
    user_id: str,
    *,
    doi_tuong_type: Optional[str] = None,
    doi_tuong_id: Optional[uuid.UUID] = None,
) -> FileStorage:
    """Upload file va luu metadata vao DB.

    Flow:
    1. Validate module
    2. Validate mime_type
    3. Doc file data va validate size
    4. Tao file_path: {module}/{loai}/{uuid}.{ext}
    5. Upload len storage (MinIO hoac local)
    6. Tao record trong common.file_storage
    """
    # 1. Validate module
    if module not in ALLOWED_MODULES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "CMN_ERR_004",
                    "message": f"Module không hợp lệ: {module}. "
                    f"Chấp nhận: {', '.join(sorted(ALLOWED_MODULES))}",
                },
            },
        )

    # 2. Validate mime_type
    mime_type = file.content_type or "application/octet-stream"
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "CMN_ERR_002",
                    "message": f"Định dạng file không được hỗ trợ: {mime_type}. "
                    f"Cho phép: PDF, DOCX, XLSX, PPTX, JPG, PNG, GIF, MP4, ZIP, RAR",
                },
            },
        )

    loai_folder, _ = ALLOWED_MIME_TYPES[mime_type]

    # 3. Doc file data va validate size
    file_data = await file.read()
    file_size = len(file_data)
    max_size = FILE_SIZE_LIMITS.get(loai_folder, 100 * 1024 * 1024)

    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "CMN_ERR_001",
                    "message": f"File quá lớn ({file_size / (1024 * 1024):.1f}MB). "
                    f"Giới hạn cho {loai_folder}: {max_mb:.0f}MB",
                },
            },
        )

    # 4. Tao file_path
    file_ext = _get_extension(file.filename or "file")
    file_id = uuid.uuid4()
    file_path = f"{module.lower()}/{loai_folder}/{file_id}{file_ext}"

    # 5. Upload len storage
    await storage_client.upload(file_path, file_data)

    # 6. Tao record DB
    record = FileStorage(
        id=file_id,
        file_name=file.filename or "untitled",
        file_path=file_path,
        file_size_bytes=file_size,
        mime_type=mime_type,
        module=module,
        doi_tuong_type=doi_tuong_type,
        doi_tuong_id=doi_tuong_id,
        nguoi_tai_len_id=uuid.UUID(user_id),
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def get_file_info(
    db: AsyncSession,
    file_id: uuid.UUID,
) -> FileStorage:
    """Lay thong tin chi tiet 1 file.

    - 404 neu khong tim thay hoac da xoa
    """
    q = select(FileStorage).where(
        FileStorage.id == file_id,
        FileStorage.is_deleted == False,  # noqa: E712
    )
    result = await db.execute(q)
    record = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "CMN_ERR_003",
                    "message": "File không tồn tại hoặc đã bị xóa",
                },
            },
        )

    return record


async def delete_file(
    db: AsyncSession,
    file_id: uuid.UUID,
    user_id: str,
    *,
    is_admin: bool = False,
) -> FileStorage:
    """Soft delete file.

    Quyen: nguoi upload hoac ADMIN.
    KHONG xoa file vat ly tren MinIO (cron job don sau 30 ngay).
    """
    q = select(FileStorage).where(
        FileStorage.id == file_id,
        FileStorage.is_deleted == False,  # noqa: E712
    )
    result = await db.execute(q)
    record = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "CMN_ERR_003",
                    "message": "File không tồn tại hoặc đã bị xóa",
                },
            },
        )

    # Kiem tra quyen: nguoi upload hoac admin
    if not is_admin and str(record.nguoi_tai_len_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_001",
                    "message": "Bạn không có quyền xóa file này",
                },
            },
        )

    record.is_deleted = True
    await db.flush()
    return record


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_extension(filename: str) -> str:
    """Lay phan mo rong tu ten file. VD: 'report.pdf' -> '.pdf'"""
    if "." in filename:
        return "." + filename.rsplit(".", 1)[1].lower()
    return ""
