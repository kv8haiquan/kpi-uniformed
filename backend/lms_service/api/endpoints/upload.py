"""
lms_service/api/endpoints/upload.py
=====================================
Endpoints upload file tinh (tai lieu, video, anh, HTML).
Strategy: 2-step upload — upload file truoc, lay file_url, roi tao bai hoc.

Endpoints:
  POST /upload/file   Upload 1 file
  POST /upload/files  Upload nhieu file cung luc
"""

from typing import List

from fastapi import APIRouter, Depends, File, Query, UploadFile

from lms_service.dependencies import require_platform_role
from lms_service.services.file_service import FileService
from shared.auth import TokenPayload

router = APIRouter(prefix="/upload", tags=["Upload"])


# =========================================================================
# POST /upload/file — Upload 1 file
# =========================================================================

@router.post("/file")
async def upload_file(
    file: UploadFile = File(..., description="File can upload"),
    folder: str = Query(
        default="general",
        description="Sub-folder: bai-hoc | anh-bia | tai-lieu | general",
    ),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """
    Upload 1 file len server.

    Auth: GIANG_VIEN, QT_DAO_TAO, ADMIN (SUPER_ADMIN bypass tu require_platform_role).
    Content-Type: multipart/form-data

    Response:
      { success: true, data: { file_name, file_url, file_size, content_type } }
    """
    file_service = FileService()
    result = await file_service.save_file(file, sub_folder=folder)
    return {
        "success": True,
        "data": result,
        "message": f"Upload '{result['file_name']}' thanh cong",
    }


# =========================================================================
# POST /upload/files — Upload nhieu file
# =========================================================================

@router.post("/files")
async def upload_multiple_files(
    files: List[UploadFile] = File(..., description="Danh sach file can upload"),
    folder: str = Query(
        default="general",
        description="Sub-folder: bai-hoc | anh-bia | tai-lieu | general",
    ),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """
    Upload nhieu file cung luc.

    Auth: GIANG_VIEN, QT_DAO_TAO, ADMIN.
    Returns danh sach ket qua upload theo thu tu.
    """
    file_service = FileService()
    results = []
    for f in files:
        result = await file_service.save_file(f, sub_folder=folder)
        results.append(result)
    return {
        "success": True,
        "data": results,
        "message": f"Upload thanh cong {len(results)} file",
    }
