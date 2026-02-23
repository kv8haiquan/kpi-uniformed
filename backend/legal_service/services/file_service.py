"""
legal_service/services/file_service.py
=========================================
Service xu ly upload va quan ly file van ban phap luat.

Logic:
  - Validate extension: chi chap nhan .pdf, .doc, .docx
  - Validate kich thuoc <= max_file_size_mb (mac dinh 50 MB)
  - Tao ten file unique: {uuid_hex}_{ten_goc}
  - Luu vao uploads/legal/van-ban/
  - Tra ve dict: { file_name, file_url, file_size, content_type }
  - Xoa file cu khi cap nhat (delete_file)
"""

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from legal_service.config import ALLOWED_LEGAL_EXTENSIONS, settings


class LegalFileService:
    """Service xu ly upload file van ban phap luat."""

    def __init__(self):
        self.base_dir = Path(settings.upload_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file: UploadFile) -> dict:
        """
        Luu file van ban len storage.

        Args:
            file: UploadFile tu FastAPI

        Returns:
            dict: { file_name, file_url, file_size, content_type }

        Raises:
            HTTPException 400: Dinh dang khong hop le | File qua lon
        """
        # --- Validate ten file
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

        # --- Validate extension
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_LEGAL_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "UPLOAD_002",
                        "message": (
                            f"Dinh dang '{ext}' khong duoc ho tro. "
                            f"Cho phep: {', '.join(sorted(ALLOWED_LEGAL_EXTENSIONS))}"
                        ),
                    },
                },
            )

        # --- Doc noi dung file
        content = await file.read()

        # --- Validate kich thuoc
        max_bytes = settings.max_file_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "UPLOAD_003",
                        "message": f"File vuot qua kich thuoc cho phep ({settings.max_file_size_mb} MB)",
                    },
                },
            )

        # --- Tao ten file unique tranh trung lap
        safe_name = Path(file.filename).name  # loai bo path traversal
        unique_name = f"{uuid4().hex[:12]}_{safe_name}"

        # --- Luu vao uploads/legal/van-ban/
        save_dir = self.base_dir / "van-ban"
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / unique_name

        with open(save_path, "wb") as f:
            f.write(content)

        file_url = f"/uploads/legal/van-ban/{unique_name}"

        return {
            "file_name":    file.filename,
            "file_url":     file_url,
            "file_size":    len(content),
            "content_type": file.content_type or "application/octet-stream",
        }

    async def delete_file(self, file_url: str) -> None:
        """
        Xoa file khoi storage neu ton tai.
        Chi xoa file bat dau bang /uploads/ de bao ve path traversal.
        """
        if not file_url or not file_url.startswith("/uploads/"):
            return
        relative_path = file_url.lstrip("/")
        file_path = Path(relative_path)
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
