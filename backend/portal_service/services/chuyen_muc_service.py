"""
portal_service/services/chuyen_muc_service.py
==============================================
Business logic cho chuyên mục bài viết portal.

CRUD:
  - danh_sach(): lọc is_active, sắp theo thu_tu
  - lay_theo_id(): raise 404 nếu không tồn tại
  - tao(): auto-gen slug từ tên
  - sua(): validate slug unique
  - xoa(): soft delete nếu có bài viết, hard delete nếu trống
"""

import re
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from portal_service.models.bai_viet import BaiViet
from portal_service.models.chuyen_muc import ChuyenMuc
from portal_service.schemas.chuyen_muc import ChuyenMucCreate, ChuyenMucUpdate


# ---------------------------------------------------------------------------
# Helper: tạo slug từ chuỗi tiếng Việt
# ---------------------------------------------------------------------------

_VIET_MAP = {
    "à": "a", "á": "a", "ả": "a", "ã": "a", "ạ": "a",
    "ă": "a", "ắ": "a", "ằ": "a", "ẳ": "a", "ẵ": "a", "ặ": "a",
    "â": "a", "ấ": "a", "ầ": "a", "ẩ": "a", "ẫ": "a", "ậ": "a",
    "è": "e", "é": "e", "ẻ": "e", "ẽ": "e", "ẹ": "e",
    "ê": "e", "ế": "e", "ề": "e", "ể": "e", "ễ": "e", "ệ": "e",
    "ì": "i", "í": "i", "ỉ": "i", "ĩ": "i", "ị": "i",
    "ò": "o", "ó": "o", "ỏ": "o", "õ": "o", "ọ": "o",
    "ô": "o", "ố": "o", "ồ": "o", "ổ": "o", "ỗ": "o", "ộ": "o",
    "ơ": "o", "ớ": "o", "ờ": "o", "ở": "o", "ỡ": "o", "ợ": "o",
    "ù": "u", "ú": "u", "ủ": "u", "ũ": "u", "ụ": "u",
    "ư": "u", "ứ": "u", "ừ": "u", "ử": "u", "ữ": "u", "ự": "u",
    "ỳ": "y", "ý": "y", "ỷ": "y", "ỹ": "y", "ỵ": "y",
    "đ": "d",
    # Uppercase
    "À": "a", "Á": "a", "Ả": "a", "Ã": "a", "Ạ": "a",
    "Ă": "a", "Ắ": "a", "Ằ": "a", "Ẳ": "a", "Ẵ": "a", "Ặ": "a",
    "Â": "a", "Ấ": "a", "Ầ": "a", "Ẩ": "a", "Ẫ": "a", "Ậ": "a",
    "È": "e", "É": "e", "Ẻ": "e", "Ẽ": "e", "Ẹ": "e",
    "Ê": "e", "Ế": "e", "Ề": "e", "Ể": "e", "Ễ": "e", "Ệ": "e",
    "Ì": "i", "Í": "i", "Ỉ": "i", "Ĩ": "i", "Ị": "i",
    "Ò": "o", "Ó": "o", "Ỏ": "o", "Õ": "o", "Ọ": "o",
    "Ô": "o", "Ố": "o", "Ồ": "o", "Ổ": "o", "Ỗ": "o", "Ộ": "o",
    "Ơ": "o", "Ớ": "o", "Ờ": "o", "Ở": "o", "Ỡ": "o", "Ợ": "o",
    "Ù": "u", "Ú": "u", "Ủ": "u", "Ũ": "u", "Ụ": "u",
    "Ư": "u", "Ứ": "u", "Ừ": "u", "Ử": "u", "Ữ": "u", "Ự": "u",
    "Ỳ": "y", "Ý": "y", "Ỷ": "y", "Ỹ": "y", "Ỵ": "y",
    "Đ": "d",
}


def _tao_slug(ten: str) -> str:
    """Sinh slug từ tên tiếng Việt.

    Quy trình:
      1. Chuyển ký tự có dấu sang không dấu (bảng _VIET_MAP)
      2. Lowercase
      3. Loại bỏ ký tự đặc biệt (giữ a-z, 0-9, khoảng trắng)
      4. Thay khoảng trắng bằng '-'
      5. Gộp nhiều '-' liên tiếp
    """
    result = "".join(_VIET_MAP.get(ch, ch) for ch in ten)
    result = result.lower()
    result = re.sub(r"[^a-z0-9\s-]", "", result)
    result = re.sub(r"\s+", "-", result.strip())
    result = re.sub(r"-+", "-", result)
    return result or "chuyen-muc"


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def danh_sach(
    db: AsyncSession,
    chi_active: bool = True,
) -> list[ChuyenMuc]:
    """Lấy danh sách chuyên mục, sắp theo thu_tu tăng dần."""
    stmt = select(ChuyenMuc)
    if chi_active:
        stmt = stmt.where(ChuyenMuc.is_active == True)  # noqa: E712
    stmt = stmt.order_by(ChuyenMuc.thu_tu.asc(), ChuyenMuc.created_at.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def lay_theo_id(db: AsyncSession, chuyen_muc_id: uuid.UUID) -> ChuyenMuc:
    """Lấy chuyên mục theo ID, raise 404 nếu không tồn tại."""
    stmt = select(ChuyenMuc).where(ChuyenMuc.id == chuyen_muc_id)
    result = await db.execute(stmt)
    cm = result.scalar_one_or_none()
    if not cm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_ERR_001",
                    "message": "Không tìm thấy chuyên mục",
                },
            },
        )
    return cm


async def _kiem_tra_slug_unique(
    db: AsyncSession,
    slug: str,
    exclude_id: Optional[uuid.UUID] = None,
) -> None:
    """Kiểm tra slug chưa bị trùng, raise 400 nếu trùng."""
    stmt = select(ChuyenMuc).where(ChuyenMuc.slug == slug)
    if exclude_id:
        stmt = stmt.where(ChuyenMuc.id != exclude_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_ERR_003",
                    "message": f"Slug '{slug}' đã tồn tại, vui lòng chọn slug khác",
                },
            },
        )


async def tao(db: AsyncSession, data: ChuyenMucCreate) -> ChuyenMuc:
    """Tạo chuyên mục mới.

    - Tự sinh slug từ tên nếu không cung cấp
    - Kiểm tra slug unique
    """
    slug = (data.slug or "").strip() or _tao_slug(data.ten)
    await _kiem_tra_slug_unique(db, slug)

    cm = ChuyenMuc(
        ten=data.ten,
        slug=slug,
        mo_ta=data.mo_ta,
        loai=data.loai or "TIN_TUC",
        thu_tu=data.thu_tu if data.thu_tu is not None else 0,
        is_active=True,
    )
    db.add(cm)
    await db.commit()
    await db.refresh(cm)
    return cm


async def sua(
    db: AsyncSession,
    chuyen_muc_id: uuid.UUID,
    data: ChuyenMucUpdate,
) -> ChuyenMuc:
    """Cập nhật chuyên mục.

    - Nếu cập nhật slug: kiểm tra unique (trừ bản thân)
    - Nếu cập nhật tên nhưng KHÔNG cập nhật slug: tự sinh slug từ tên mới
      (chỉ ghi đè nếu slug mới chưa bị trùng)
    """
    cm = await lay_theo_id(db, chuyen_muc_id)

    if data.slug is not None:
        new_slug = data.slug.strip()
        if new_slug != cm.slug:
            await _kiem_tra_slug_unique(db, new_slug, exclude_id=chuyen_muc_id)
        cm.slug = new_slug
    elif data.ten is not None:
        # Tự sinh slug từ tên mới, nhưng chỉ thay thế nếu chưa trùng
        new_slug = _tao_slug(data.ten)
        if new_slug != cm.slug:
            stmt = select(ChuyenMuc).where(
                ChuyenMuc.slug == new_slug,
                ChuyenMuc.id != chuyen_muc_id,
            )
            existing = await db.execute(stmt)
            if not existing.scalar_one_or_none():
                cm.slug = new_slug

    if data.ten is not None:
        cm.ten = data.ten
    if data.mo_ta is not None:
        cm.mo_ta = data.mo_ta
    if data.loai is not None:
        cm.loai = data.loai
    if data.thu_tu is not None:
        cm.thu_tu = data.thu_tu
    if data.is_active is not None:
        cm.is_active = data.is_active

    await db.commit()
    await db.refresh(cm)
    return cm


async def xoa(db: AsyncSession, chuyen_muc_id: uuid.UUID) -> dict:
    """Xóa chuyên mục.

    - Có bài viết (chưa xóa): soft delete (is_active=False)
    - Không có bài viết: hard delete
    """
    cm = await lay_theo_id(db, chuyen_muc_id)

    # Kiểm tra số bài viết còn tồn tại thuộc chuyên mục này
    stmt = select(func.count()).where(
        BaiViet.chuyen_muc_id == chuyen_muc_id,
        BaiViet.is_deleted == False,  # noqa: E712
    )
    result = await db.execute(stmt)
    so_bai_viet = result.scalar() or 0

    if so_bai_viet > 0:
        # Soft delete — giữ lại bài viết
        cm.is_active = False
        await db.commit()
        return {
            "deleted": False,
            "message": f"Đã ẩn chuyên mục (còn {so_bai_viet} bài viết liên quan)",
        }
    else:
        # Hard delete
        await db.delete(cm)
        await db.commit()
        return {"deleted": True, "message": "Đã xóa chuyên mục"}
