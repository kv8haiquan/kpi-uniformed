"""
storage_service.py
===================
Filesystem-based storage service cho HKG (bám pattern LMS file_service).

MVP filesystem: `uploads/meeting/{folder}/{cuoc_hop_id}/{uuid}_{filename}`.
DB cột `minio_bucket = 'meeting'`, `minio_key = 'tai-lieu/{cuoc_hop_id}/{uuid}_{name}'`
(relative path trong bucket).

Khi nâng cấp MinIO (Phase 4+) → refactor file này, DB schema không đổi.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status

from meeting_service.config import ALLOWED_EXTENSIONS, settings


BUCKET = "meeting"  # constant — match cột minio_bucket


class StorageService:
    """Quản lý file local dưới `uploads/meeting/`."""

    def __init__(self):
        # Tự tạo thư mục root khi cần
        self.bucket_root = Path(settings.upload_dir)
        self.bucket_root.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────────────────────────────
    async def save_upload(
        self,
        file: UploadFile,
        *,
        folder: str,
        cuoc_hop_id: Optional[UUID] = None,
        thu_muc_con: Optional[str] = None,
    ) -> dict:
        """
        Save file lên filesystem. Trả về dict đủ trường để insert DB.

        Args:
            file: UploadFile từ FastAPI
            folder: subfolder trong bucket — vd 'tai-lieu', 'xin-phep', 'y-kien'
            cuoc_hop_id: ID cuộc họp (dùng làm subfolder cấp 2)
            thu_muc_con: tên subfolder cấp 2 khi chủ thể KHÔNG phải cuộc họp —
                vd đính kèm ghi chú cá nhân (G5.2) dùng id ghi chú

        Returns:
            {
                "minio_bucket": "meeting",
                "minio_key": "tai-lieu/{cuoc_hop_id}/{uuid}_{filename}",
                "file_size": int,
                "mime_type": str | None,
                "extension": str,
                "original_filename": str,
            }
        """
        khoa_thu_muc = thu_muc_con or (str(cuoc_hop_id) if cuoc_hop_id else None)
        if not khoa_thu_muc:
            self._raise(400, "UPLOAD_003",
                        "Thiếu chủ thể để xác định thư mục lưu file")

        if not file.filename:
            self._raise(400, "UPLOAD_001", "Tên file không hợp lệ")

        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            self._raise(
                400, "UPLOAD_002",
                f"Định dạng '{ext}' không được hỗ trợ. "
                f"Cho phép: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )

        content = await file.read()
        size = len(content)

        max_size = settings.max_file_size_mb * 1024 * 1024
        if size > max_size:
            self._raise(
                422, "DOC_TOO_LARGE",
                f"File vượt giới hạn {settings.max_file_size_mb}MB",
            )

        # Tạo path: {bucket_root}/{folder}/{khoa_thu_muc}/{uuid}_{filename}
        rel_dir = Path(folder) / khoa_thu_muc
        full_dir = self.bucket_root / rel_dir
        full_dir.mkdir(parents=True, exist_ok=True)

        unique_name = f"{uuid4().hex}_{file.filename}"
        full_path = full_dir / unique_name

        with open(full_path, "wb") as f:
            f.write(content)

        return {
            "minio_bucket": BUCKET,
            "minio_key": str(rel_dir / unique_name),
            "file_size": size,
            "mime_type": file.content_type,
            "extension": ext.lstrip("."),
            "original_filename": file.filename,
        }

    # ──────────────────────────────────────────────────────────────────
    def resolve_path(self, minio_key: str) -> Path:
        """Resolve `minio_key` → absolute filesystem path."""
        # Đảm bảo path nằm trong bucket_root (chống path traversal)
        full_path = (self.bucket_root / minio_key).resolve()
        bucket_resolved = self.bucket_root.resolve()
        if not str(full_path).startswith(str(bucket_resolved)):
            self._raise(400, "INVALID_PATH", "Đường dẫn không hợp lệ")
        return full_path

    def file_exists(self, minio_key: str) -> bool:
        try:
            return self.resolve_path(minio_key).is_file()
        except HTTPException:
            return False

    def delete_file(self, minio_key: str) -> None:
        """Xóa file. Không raise nếu file không tồn tại."""
        try:
            path = self.resolve_path(minio_key)
            if path.is_file():
                path.unlink()
        except HTTPException:
            pass

    # ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _raise(status_code: int, code: str, message: str):
        raise HTTPException(
            status_code=status_code,
            detail={"success": False, "error": {"code": code, "message": message}},
        )
