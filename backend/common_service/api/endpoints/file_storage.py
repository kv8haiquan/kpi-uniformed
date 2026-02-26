"""
common_service/api/endpoints/file_storage.py
=============================================
Public API cho File Storage.
Prefix: /api/common/v1/file
Auth: JWT Bearer token

Endpoints:
  POST   /file/upload     — Upload file (multipart/form-data)
  GET    /file/{id}       — Lay thong tin file
  DELETE /file/{id}       — Xoa file (soft delete)
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile

from common_service.dependencies import CurrentUserDep, DatabaseDep
from common_service.schemas.base import SuccessResponse
from common_service.schemas.file_storage import FileInfoResponse, FileUploadResponse
from common_service.services import file_storage_service

router = APIRouter(prefix="/file", tags=["File Storage"])


@router.post("/upload", response_model=SuccessResponse[FileUploadResponse], status_code=201)
async def upload_file(
    db: DatabaseDep,
    user: CurrentUserDep,
    file: UploadFile = File(..., description="File can upload"),
    module: str = Form(..., description="Module: LMS, FORUM, LEGAL, PORTAL"),
    doi_tuong_type: Optional[str] = Form(default=None, description="Loai doi tuong: BAI_HOC, CHU_DE, ..."),
    doi_tuong_id: Optional[uuid.UUID] = Form(default=None, description="UUID doi tuong cha"),
):
    """Upload file — luu metadata trong DB, file tren MinIO/local.

    Gioi han kich thuoc:
      - Documents (PDF, DOCX, XLSX, PPTX): 50MB
      - Images (JPG, PNG, GIF): 10MB
      - Videos (MP4): 500MB
      - Archives (ZIP, RAR): 100MB
    """
    record = await file_storage_service.upload_file(
        db, file, module, user.sub,
        doi_tuong_type=doi_tuong_type,
        doi_tuong_id=doi_tuong_id,
    )
    return SuccessResponse(
        data=FileUploadResponse(
            id=record.id,
            file_url=record.file_url,
            file_name=record.file_name,
            file_size_bytes=record.file_size_bytes,
            mime_type=record.mime_type,
            module=record.module,
            created_at=record.created_at,
        ),
        message="Upload file thành công",
    )


@router.get("/{file_id}", response_model=SuccessResponse[FileInfoResponse])
async def get_file_info(
    file_id: uuid.UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """Lay thong tin chi tiet 1 file."""
    record = await file_storage_service.get_file_info(db, file_id)
    return SuccessResponse(
        data=FileInfoResponse.model_validate(record),
    )


@router.delete("/{file_id}", response_model=SuccessResponse[dict])
async def delete_file(
    file_id: uuid.UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """Xoa file (soft delete).

    Quyen: nguoi upload hoac ADMIN.
    File vat ly tren MinIO giu lai 30 ngay truoc khi don.
    """
    is_admin = user.vai_tro == "SUPER_ADMIN" or user.is_admin
    await file_storage_service.delete_file(
        db, file_id, user.sub, is_admin=is_admin,
    )
    return SuccessResponse(
        data={"deleted": True},
        message="Đã xóa file",
    )
