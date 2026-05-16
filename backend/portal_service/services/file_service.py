"""
portal_service/services/file_service.py
========================================
Service upload file tinh cho Portal.

Hai loai upload:
  - Anh chan dung (vinh danh, anh bia bai viet): save_image()
    + Chi cho phep .jpg/.jpeg/.png/.webp/.gif, <= 5 MB
  - Tai lieu thu vien (PDF/DOC/XLSX/PPTX/ZIP/anh...): save_document()
    + Cho phep nhieu dinh dang, <= 50 MB

Chien luoc chung:
  - Validate extension theo whitelist
  - Validate kich thuoc <= MAX_SIZE_MB
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

# Dinh dang cho phep upload vao thu vien tai lieu (ECM)
ALLOWED_DOCUMENT_EXTENSIONS = {
    # Tai lieu
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".csv", ".rtf",
    # Anh
    ".jpg", ".jpeg", ".png", ".webp", ".gif",
    # Nen
    ".zip", ".rar", ".7z",
}
MAX_DOCUMENT_SIZE_MB = 50

UPLOAD_DIR = Path("uploads/portal")


class PortalFileService:
    """Upload va luu file tinh cho Portal."""

    def __init__(self):
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Anh chan dung / anh bia
    # ------------------------------------------------------------------

    async def save_image(self, file: UploadFile, sub_folder: str) -> dict:
        """Luu anh upload, raise 400 neu khong hop le."""
        return await self._save_file(
            file=file,
            sub_folder=sub_folder,
            allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
            max_size_mb=MAX_IMAGE_SIZE_MB,
            kind_label="Anh",
        )

    # ------------------------------------------------------------------
    # Tai lieu thu vien ECM
    # ------------------------------------------------------------------

    async def save_document(self, file: UploadFile, sub_folder: str = "tai-lieu") -> dict:
        """Luu file tai lieu (PDF/DOC/XLSX/PPTX/anh/zip), raise 400 neu khong hop le."""
        return await self._save_file(
            file=file,
            sub_folder=sub_folder,
            allowed_extensions=ALLOWED_DOCUMENT_EXTENSIONS,
            max_size_mb=MAX_DOCUMENT_SIZE_MB,
            kind_label="Tai lieu",
        )

    # ------------------------------------------------------------------
    # Helper chung
    # ------------------------------------------------------------------

    async def _save_file(
        self,
        file: UploadFile,
        sub_folder: str,
        allowed_extensions: set[str],
        max_size_mb: int,
        kind_label: str,
    ) -> dict:
        """Luu file len disk + validate ext / size. Tra ve dict thong tin file."""
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
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "UPLOAD_002",
                        "message": (
                            f"Dinh dang '{ext}' khong duoc ho tro. "
                            f"Cho phep: {', '.join(sorted(allowed_extensions))}"
                        ),
                    },
                },
            )

        content = await file.read()
        max_bytes = max_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "UPLOAD_003",
                        "message": f"{kind_label} vuot qua kich thuoc cho phep ({max_size_mb} MB)",
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
