"""
portal_service/api/endpoints/upload.py
=======================================
Endpoint upload file chung cho Portal.

Strategy 2-step: upload file truoc, lay file_url, roi tao tai lieu / bai viet.
Endpoint mo cho moi user da dang nhap (khong yeu cau platform role) — phuc vu
nhu cau "moi cong chuc deu co the upload tai lieu len thu vien".

Endpoints:
  POST /upload/file   Upload 1 file (PDF/DOC/XLSX/PPTX/anh/zip, <= 50 MB)
"""

from fastapi import APIRouter, File, Query, UploadFile

from portal_service.dependencies import CurrentUserDep
from portal_service.services.file_service import PortalFileService

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/file", summary="Upload 1 file tai lieu")
async def upload_file(
    user: CurrentUserDep,
    file: UploadFile = File(..., description="File can upload"),
    folder: str = Query(
        default="tai-lieu",
        description="Sub-folder: tai-lieu | general (default: tai-lieu)",
    ),
):
    """
    Upload 1 file len server (luu vao uploads/portal/{folder}/).

    Auth: chi can da dang nhap (moi cong chuc deu duoc upload).
    Content-Type: multipart/form-data

    Response:
      { success: true, data: { file_name, file_url, file_size, content_type } }
    """
    file_service = PortalFileService()
    result = await file_service.save_document(file, sub_folder=folder)
    return {
        "success": True,
        "data": result,
        "message": f"Upload '{result['file_name']}' thanh cong",
    }
