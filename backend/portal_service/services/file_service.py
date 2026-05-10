"""
portal_service/services/file_service.py
========================================
Service upload file tinh cho Portal (anh chan dung vinh danh, anh dai dien bai viet).

Chien luoc:
  - Validate extension trong ALLOWED_IMAGE_EXTENSIONS
  - Validate kich thuoc <= MAX_IMAGE_SIZE_MB
  - Sinh ten unique: {uuid12}_{ten_goc}
  - Luu vao UPLOAD_DIR/{sub_folder}/
  - Tra ve {file_name, file_url, file_size, content_type}

URL serve qua /uploads/portal/{sub_folder}/{file_name}.
"""

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_SIZE_MB = 5
UPLOAD_DIR = Path("uploads/portal")


class PortalFileService:
    """Upload va luu file tinh cho Portal."""

    def __init__(self):
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    async def save_image(self, file: UploadFile, sub_folder: str) -> dict:
        """Luu anh upload, raise 400 neu khong hop le."""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "UPLOAD_001",
                        "message": "Ten file khong hop le",
                    },
                },
            )

        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "UPLOAD_002",
                        "message": (
                            f"Dinh dang '{ext}' khong duoc ho tro. "
                            f"Cho phep: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"
                        ),
                    },
                },
            )

        content = await file.read()
        max_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "UPLOAD_003",
                        "message": f"Anh vuot qua kich thuoc cho phep ({MAX_IMAGE_SIZE_MB} MB)",
                    },
                },
            )

        safe_name = Path(file.filename).name
        unique_name = f"{uuid4().hex[:12]}_{safe_name}"

        save_dir = UPLOAD_DIR / sub_folder
        save_dir.mkdir(parents=True, exist_ok=True)

        save_path = save_dir / unique_name
        with open(save_path, "wb") as f:
            f.write(content)

        relative_url = f"/uploads/portal/{sub_folder}/{unique_name}"
        return {
            "file_name": file.filename,
            "file_url": relative_url,
            "file_size": len(content),
            "content_type": file.content_type or "application/octet-stream",
        }
