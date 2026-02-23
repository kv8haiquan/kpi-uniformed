"""
lms_service/services/file_service.py
======================================
Service xu ly upload va quan ly file tinh.

Logic:
  - Validate extension theo ALLOWED_EXTENSIONS
  - Validate kich thuoc <= MAX_FILE_SIZE_MB
  - Tao ten file unique: {uuid_hex}_{ten_goc}
  - Luu vao UPLOAD_DIR/{sub_folder}/
  - Tra ve dict: { file_name, file_url, file_size, content_type }
  - Xoa file khi can (delete_file)
"""

import subprocess
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from lms_service.config import settings, ALLOWED_EXTENSIONS


class FileService:
    """Service xu ly upload va quan ly file tren he thong."""

    def __init__(self):
        self.base_dir = Path(settings.upload_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # SAVE FILE
    # =========================================================================

    async def save_file(self, file: UploadFile, sub_folder: str = "") -> dict:
        """
        Luu file upload len storage.

        Args:
            file:       UploadFile tu FastAPI
            sub_folder: Thu muc con (vi du: "bai-hoc", "anh-bia", "tai-lieu")

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
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "UPLOAD_002",
                        "message": f"Dinh dang '{ext}' khong duoc ho tro. "
                                   f"Cho phep: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
                    },
                },
            )

        # --- Doc noi dung file (doc het vao bo nho de kiem tra size)
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
                        "message": f"File vuot qua kich thuoc cho phep "
                                   f"({settings.max_file_size_mb} MB)",
                    },
                },
            )

        # --- Tao ten file unique tranh trung lap
        safe_name = Path(file.filename).name  # loai bo path traversal
        unique_name = f"{uuid4().hex[:12]}_{safe_name}"

        # --- Chon thu muc luu
        if sub_folder:
            save_dir = self.base_dir / sub_folder
        else:
            save_dir = self.base_dir
        save_dir.mkdir(parents=True, exist_ok=True)

        # --- Ghi file xuong disk
        save_path = save_dir / unique_name
        with open(save_path, "wb") as f:
            f.write(content)

        # --- Xay dung URL tuong doi de serve qua StaticFiles
        if sub_folder:
            relative_url = f"/uploads/lms/{sub_folder}/{unique_name}"
        else:
            relative_url = f"/uploads/lms/{unique_name}"

        result = {
            "file_name":    file.filename,
            "file_url":     relative_url,
            "file_size":    len(content),
            "content_type": file.content_type or "application/octet-stream",
        }

        # --- Auto-convert PPTX/PPT sang PDF (neu LibreOffice co san)
        ext = Path(file.filename).suffix.lower()
        if ext in (".pptx", ".ppt"):
            pdf_path = await self.convert_to_pdf(str(save_path))
            if pdf_path:
                # URL cua ban PDF (thay duoi file)
                pdf_relative = relative_url.rsplit(".", 1)[0] + ".pdf"
                result["pdf_url"] = pdf_relative
                result["original_url"] = relative_url  # ban goc de download

        return result

    # =========================================================================
    # CONVERT TO PDF
    # =========================================================================

    async def convert_to_pdf(self, file_path: str) -> str | None:
        """
        Convert PPTX/PPT → PDF bang LibreOffice headless.

        Tra ve duong dan file PDF moi neu thanh cong, None neu loi hoac
        LibreOffice chua cai dat (graceful fallback).
        """
        input_path = Path(file_path)
        if input_path.suffix.lower() not in (".pptx", ".ppt", ".docx", ".doc"):
            return None

        output_dir = input_path.parent
        try:
            result = subprocess.run(
                [
                    "libreoffice", "--headless", "--convert-to", "pdf",
                    "--outdir", str(output_dir),
                    str(input_path),
                ],
                capture_output=True,
                timeout=60,
                text=True,
            )
            if result.returncode == 0:
                pdf_path = output_dir / f"{input_path.stem}.pdf"
                if pdf_path.exists():
                    return str(pdf_path)
            else:
                print(f"[FileService] LibreOffice convert error: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("[FileService] Convert timeout (>60s) — skip")
        except FileNotFoundError:
            print("[FileService] LibreOffice chua cai dat — skip convert")
        return None

    # =========================================================================
    # DELETE FILE
    # =========================================================================

    async def delete_file(self, file_url: str) -> None:
        """
        Xoa file khoi storage neu ton tai.

        Args:
            file_url: URL tuong doi, vi du /uploads/lms/bai-hoc/abc_test.pdf
                      Chi xoa neu bat dau bang /uploads/ (bao ve path traversal)
        """
        if not file_url or not file_url.startswith("/uploads/"):
            return
        # Chuyen URL thanh duong dan he thong (cat dau /)
        relative_path = file_url.lstrip("/")
        file_path = Path(relative_path)
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
