"""
preview_service.py
==================
Convert Office documents (.docx/.doc/.xlsx/.xls/.pptx/.ppt) sang PDF
bằng LibreOffice headless để browser preview inline (browser native không
render được Office formats).

- Cache PDF tại `<upload_dir>/_preview_cache/<tai_lieu_id>.pdf`
- Cache key check bằng mtime — file gốc thay đổi → re-convert
- Per-file lock (in-process) tránh 2 request cùng convert 1 file
- LibreOffice user profile riêng cho mỗi call → cho phép concurrency
- Graceful fallback: nếu binary không có hoặc convert fail → raise 503
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from meeting_service.config import settings


OFFICE_EXTENSIONS = frozenset({"docx", "doc", "xlsx", "xls", "pptx", "ppt"})

_CACHE_SUBDIR = "_preview_cache"
_CONVERT_TIMEOUT_SEC = 90

# Lock per-file_id để tránh duplicate conversion khi nhiều user cùng xem
_locks: dict[str, asyncio.Lock] = {}
_locks_guard = asyncio.Lock()


def is_office_extension(ext: Optional[str]) -> bool:
    """Check extension (lowercase, no dot) có cần convert sang PDF không."""
    if not ext:
        return False
    return ext.lower().lstrip(".") in OFFICE_EXTENSIONS


def _cache_path(tai_lieu_id: str) -> Path:
    cache_dir = Path(settings.upload_dir) / _CACHE_SUBDIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{tai_lieu_id}.pdf"


def _cache_valid(cache: Path, source: Path) -> bool:
    """Cache còn fresh nếu PDF tồn tại và mtime >= source mtime."""
    if not cache.is_file():
        return False
    try:
        return cache.stat().st_mtime >= source.stat().st_mtime
    except OSError:
        return False


async def _get_lock(tai_lieu_id: str) -> asyncio.Lock:
    async with _locks_guard:
        lock = _locks.get(tai_lieu_id)
        if lock is None:
            lock = asyncio.Lock()
            _locks[tai_lieu_id] = lock
        return lock


def _run_libreoffice(source: Path, out_dir: Path) -> Path:
    """
    Spawn `libreoffice --headless --convert-to pdf`. Trả về path PDF mới.
    Raise RuntimeError nếu fail.
    """
    # User profile riêng tránh concurrent collision
    with tempfile.TemporaryDirectory(prefix="lo_profile_") as profile_dir:
        cmd = [
            "libreoffice",
            f"-env:UserInstallation=file://{profile_dir}",
            "--headless",
            "--norestore",
            "--nolockcheck",
            "--convert-to", "pdf",
            "--outdir", str(out_dir),
            str(source),
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=_CONVERT_TIMEOUT_SEC,
                text=True,
            )
        except FileNotFoundError as e:
            raise RuntimeError("LibreOffice chưa được cài đặt trên server") from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Convert timeout sau {_CONVERT_TIMEOUT_SEC}s") from e

        if result.returncode != 0:
            raise RuntimeError(
                f"LibreOffice exit {result.returncode}: {result.stderr.strip()[:500]}"
            )

        pdf_path = out_dir / f"{source.stem}.pdf"
        if not pdf_path.is_file():
            raise RuntimeError(
                f"Convert OK nhưng không tìm thấy PDF output: {pdf_path}"
            )
        return pdf_path


async def ensure_pdf_preview(tai_lieu_id: str, source_path: Path) -> Path:
    """
    Đảm bảo có file PDF preview cho `source_path`. Trả về path PDF.

    - Nếu cache còn fresh → trả về luôn
    - Nếu chưa có / stale → convert (under per-file lock)
    """
    cache = _cache_path(tai_lieu_id)
    if _cache_valid(cache, source_path):
        return cache

    lock = await _get_lock(tai_lieu_id)
    async with lock:
        # Re-check sau khi acquire lock (request khác có thể vừa convert xong)
        if _cache_valid(cache, source_path):
            return cache

        # Convert vào tmpdir trước, atomic move sang cache
        with tempfile.TemporaryDirectory(prefix="lo_out_") as tmp_out:
            tmp_out_path = Path(tmp_out)
            pdf_tmp = await asyncio.to_thread(_run_libreoffice, source_path, tmp_out_path)
            shutil.move(str(pdf_tmp), str(cache))
        return cache


def invalidate_cache(tai_lieu_id: str) -> None:
    """Xóa cache PDF (gọi khi file gốc bị soft-delete hoặc replace)."""
    cache = _cache_path(tai_lieu_id)
    try:
        if cache.is_file():
            cache.unlink()
    except OSError:
        pass
