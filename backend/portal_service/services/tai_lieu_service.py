"""
portal_service/services/tai_lieu_service.py
============================================
Business logic cho tài liệu ECM — versioning + phân quyền.

Versioning:
  - phien_ban = 1 khi upload lần đầu
  - Upload phiên bản mới: tạo record mới, phien_ban += 1,
    phien_ban_truoc_id = id record cũ
  - Lịch sử: duyệt ngược theo phien_ban_truoc_id

"Phiên bản mới nhất" (dùng trong danh sách):
  - TaiLieu X là latest nếu KHÔNG có TaiLieu Y nào trỏ Y.phien_ban_truoc_id = X.id

Phân quyền:
  - Kế thừa từ thư mục cha nếu tài liệu có quyen_truy_cap = TAT_CA
  - Override nếu tài liệu có quyen_truy_cap riêng

Validation file_type + file_size:
  - PDF / DOCX / XLSX / PPTX : ≤ 50 MB
  - IMAGE (image/*)           : ≤ 10 MB
  - ZIP                       : ≤ 100 MB
  - Các loại khác             : ≤ 50 MB (default)
"""

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from portal_service.models.tai_lieu import TaiLieu
from portal_service.models.thu_muc import ThuMuc
from portal_service.schemas.tai_lieu import TaiLieuCreate, TaiLieuUpdate, UploadPhienBanMoiRequest
from shared.auth import TokenPayload


# ---------------------------------------------------------------------------
# Hằng số giới hạn file
# ---------------------------------------------------------------------------

MB = 1024 * 1024

_FILE_SIZE_LIMITS: dict[str, int] = {
    # Theo MIME type prefix
    "application/pdf": 50 * MB,
    "application/vnd.openxmlformats-officedocument.wordprocessingml": 50 * MB,
    "application/vnd.openxmlformats-officedocument.spreadsheetml": 50 * MB,
    "application/vnd.openxmlformats-officedocument.presentationml": 50 * MB,
    "application/msword": 50 * MB,
    "application/vnd.ms-excel": 50 * MB,
    "application/vnd.ms-powerpoint": 50 * MB,
    "application/zip": 100 * MB,
    "application/x-zip-compressed": 100 * MB,
    "image/": 10 * MB,  # prefix match
}
_DEFAULT_SIZE_LIMIT = 50 * MB


def _kiem_tra_file(file_type: Optional[str], file_size_bytes: Optional[int]) -> None:
    """Kiểm tra giới hạn dung lượng theo loại file."""
    if not file_size_bytes or not file_type:
        return

    limit = _DEFAULT_SIZE_LIMIT
    ft = file_type.lower()

    # Prefix match
    for mime_prefix, max_size in _FILE_SIZE_LIMITS.items():
        if ft.startswith(mime_prefix):
            limit = max_size
            break

    if file_size_bytes > limit:
        limit_mb = limit // MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_ERR_006",
                    "message": f"File vượt quá giới hạn {limit_mb} MB cho loại {file_type}",
                },
            },
        )


# ---------------------------------------------------------------------------
# Helpers kiểm tra quyền
# ---------------------------------------------------------------------------


def _la_admin_qt(user: TokenPayload) -> bool:
    if user.vai_tro == "SUPER_ADMIN" or user.is_admin:
        return True
    return "QT_NOI_DUNG" in (user.platform_roles or [])


def _kiem_tra_quyen_entity(
    quyen_truy_cap: str,
    don_vi_ids: Optional[list],
    created_by_id: Optional[uuid.UUID],
    user: TokenPayload,
) -> bool:
    """Kiểm tra quyền truy cập theo quy tắc."""
    if _la_admin_qt(user):
        return True

    quyen = (quyen_truy_cap or "TAT_CA").upper()

    if quyen == "TAT_CA":
        return True

    if quyen == "LANH_DAO":
        return user.is_lanh_dao

    if quyen in ("DON_VI", "THEO_DON_VI"):
        if not don_vi_ids or not user.don_vi_id:
            return False
        if isinstance(don_vi_ids, list):
            return str(user.don_vi_id) in [str(d) for d in don_vi_ids]
        return False

    if quyen == "CA_NHAN":
        if not created_by_id:
            return False
        return str(created_by_id) == str(user.sub)

    if quyen == "THEO_VAI_TRO":
        return user.is_lanh_dao

    return False


def _co_quyen_xem_tai_lieu(
    tai_lieu: TaiLieu,
    user: TokenPayload,
) -> bool:
    """Kiểm tra quyền xem tài liệu.

    Ưu tiên:
      1. Quyền của tài liệu (nếu khác TAT_CA)
      2. Kế thừa quyền thư mục cha (nếu tài liệu = TAT_CA và thư mục khác TAT_CA)
    """
    if _la_admin_qt(user):
        return True

    tl_quyen = (tai_lieu.quyen_truy_cap or "TAT_CA").upper()

    # Nếu tài liệu có quyền riêng (khác TAT_CA) → dùng quyền tài liệu
    if tl_quyen != "TAT_CA":
        return _kiem_tra_quyen_entity(
            tl_quyen,
            tai_lieu.don_vi_ids,
            tai_lieu.nguoi_tai_len_id,
            user,
        )

    # Kế thừa từ thư mục cha
    if tai_lieu.thu_muc:
        tm = tai_lieu.thu_muc
        tm_quyen = (tm.quyen_truy_cap or "TAT_CA").upper()
        if tm_quyen != "TAT_CA":
            return _kiem_tra_quyen_entity(
                tm_quyen,
                tm.don_vi_ids,
                tm.created_by,
                user,
            )

    # Mặc định TAT_CA
    return True


# ---------------------------------------------------------------------------
# Helper lấy tài liệu theo ID
# ---------------------------------------------------------------------------


async def _lay_theo_id(db: AsyncSession, tai_lieu_id: uuid.UUID) -> TaiLieu:
    """Lấy tài liệu theo ID, raise 404 nếu không tồn tại hoặc đã xóa."""
    stmt = select(TaiLieu).where(
        TaiLieu.id == tai_lieu_id,
        TaiLieu.is_deleted == False,  # noqa: E712
    )
    result = await db.execute(stmt)
    tl = result.scalar_one_or_none()
    if not tl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_ERR_001",
                    "message": "Không tìm thấy tài liệu",
                },
            },
        )
    return tl


# ---------------------------------------------------------------------------
# Danh sách
# ---------------------------------------------------------------------------


async def danh_sach(
    db: AsyncSession,
    user: TokenPayload,
    thu_muc_id: Optional[uuid.UUID] = None,
    file_type: Optional[str] = None,
    tags: Optional[list] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[TaiLieu], int]:
    """Danh sách tài liệu — chỉ phiên bản MỚI NHẤT.

    "Mới nhất" = không có TaiLieu nào khác trỏ phien_ban_truoc_id = id này.
    Lọc theo: thư mục, file_type, tags (JSONB contains), search (tên).
    """
    # Subquery: IDs đang là "phiên bản trước" của một bản khác → không phải latest
    previous_ids_subq = (
        select(TaiLieu.phien_ban_truoc_id)
        .where(
            TaiLieu.phien_ban_truoc_id.isnot(None),
            TaiLieu.is_deleted == False,  # noqa: E712
        )
        .scalar_subquery()
    )

    stmt = select(TaiLieu).where(
        TaiLieu.is_deleted == False,  # noqa: E712
        TaiLieu.id.not_in(previous_ids_subq),
    )

    if thu_muc_id:
        stmt = stmt.where(TaiLieu.thu_muc_id == thu_muc_id)

    if file_type:
        stmt = stmt.where(TaiLieu.file_type.ilike(f"%{file_type}%"))

    if search:
        stmt = stmt.where(TaiLieu.ten_tai_lieu.ilike(f"%{search}%"))

    if tags:
        # PostgreSQL JSONB: tags @> '["tag1"]'
        for tag in tags:
            stmt = stmt.where(TaiLieu.tags.contains([tag]))

    # Đếm total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    stmt = stmt.order_by(TaiLieu.created_at.desc())

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    items = list(result.scalars().all())

    # Lọc theo quyền
    if not _la_admin_qt(user):
        items = [tl for tl in items if _co_quyen_xem_tai_lieu(tl, user)]
        # Sau khi lọc quyền, total có thể lệch — đây là acceptable trade-off
        # vì phân quyền theo row-level security không dễ làm ở DB level
        total = len(items)

    return items, total


# ---------------------------------------------------------------------------
# Chi tiết
# ---------------------------------------------------------------------------


async def chi_tiet(
    db: AsyncSession,
    tai_lieu_id: uuid.UUID,
    user: TokenPayload,
) -> TaiLieu:
    """Chi tiết tài liệu, kiểm tra quyền truy cập."""
    tl = await _lay_theo_id(db, tai_lieu_id)

    if not _co_quyen_xem_tai_lieu(tl, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_ERR_003",
                    "message": "Bạn không có quyền truy cập tài liệu này",
                },
            },
        )

    return tl


# ---------------------------------------------------------------------------
# Upload tài liệu mới
# ---------------------------------------------------------------------------


async def upload(
    db: AsyncSession,
    data: TaiLieuCreate,
    user: TokenPayload,
) -> TaiLieu:
    """Upload tài liệu mới, phiên bản 1.

    Kiểm tra:
      - Quyền thư mục đích (nếu có thu_muc_id)
      - Validate file_type + file_size
    """
    user_id = uuid.UUID(user.sub)

    # Kiểm tra thư mục đích (nếu có)
    if data.thu_muc_id:
        stmt = select(ThuMuc).where(ThuMuc.id == data.thu_muc_id)
        result = await db.execute(stmt)
        thu_muc = result.scalar_one_or_none()
        if not thu_muc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {
                        "code": "PORTAL_ERR_001",
                        "message": "Không tìm thấy thư mục",
                    },
                },
            )
        # Kiểm tra quyền thư mục
        from portal_service.services.thu_muc_service import _kiem_tra_quyen_xem
        if not _kiem_tra_quyen_xem(thu_muc, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PORTAL_ERR_003",
                        "message": "Bạn không có quyền upload vào thư mục này",
                    },
                },
            )

    # Validate file
    _kiem_tra_file(data.file_type, data.file_size_bytes)

    tl = TaiLieu(
        ten_tai_lieu=data.ten_tai_lieu,
        mo_ta=data.mo_ta,
        thu_muc_id=data.thu_muc_id,
        file_url=data.file_url,
        file_name=data.file_name,
        file_size_bytes=data.file_size_bytes,
        file_type=data.file_type,
        phien_ban=1,
        phien_ban_truoc_id=None,
        tags=data.tags or [],
        quyen_truy_cap=data.quyen_truy_cap or "TAT_CA",
        don_vi_ids=data.don_vi_ids,
        nguoi_tai_len_id=user_id,
        is_deleted=False,
    )
    db.add(tl)
    await db.commit()
    await db.refresh(tl)
    return tl


# ---------------------------------------------------------------------------
# Cập nhật metadata
# ---------------------------------------------------------------------------


async def cap_nhat(
    db: AsyncSession,
    tai_lieu_id: uuid.UUID,
    data: TaiLieuUpdate,
    user: TokenPayload,
) -> TaiLieu:
    """Cập nhật metadata tài liệu (tên, mô tả, tags).

    KHÔNG cho cập nhật file_url — phải upload phiên bản mới.
    """
    tl = await _lay_theo_id(db, tai_lieu_id)

    if data.ten_tai_lieu is not None:
        tl.ten_tai_lieu = data.ten_tai_lieu
    if data.mo_ta is not None:
        tl.mo_ta = data.mo_ta
    if data.tags is not None:
        tl.tags = data.tags
    if data.quyen_truy_cap is not None:
        tl.quyen_truy_cap = data.quyen_truy_cap
    if data.don_vi_ids is not None:
        tl.don_vi_ids = data.don_vi_ids

    await db.commit()
    await db.refresh(tl)
    return tl


# ---------------------------------------------------------------------------
# Upload phiên bản mới
# ---------------------------------------------------------------------------


async def upload_phien_ban_moi(
    db: AsyncSession,
    tai_lieu_id: uuid.UUID,
    data: UploadPhienBanMoiRequest,
    user: TokenPayload,
) -> TaiLieu:
    """Upload phiên bản mới của tài liệu.

    Quyền: người upload gốc, QT_NOI_DUNG, ADMIN.
    Tạo record MỚI với:
      - phien_ban = phien_ban_cu + 1
      - phien_ban_truoc_id = tai_lieu_id
      - Copy ten_tai_lieu, thu_muc_id, tags từ bản cũ (nếu không truyền mới)
    KHÔNG xóa bản cũ.
    """
    user_id = uuid.UUID(user.sub)
    tl_cu = await _lay_theo_id(db, tai_lieu_id)

    # Kiểm tra quyền
    is_nguoi_goc = str(tl_cu.nguoi_tai_len_id) == str(user.sub) if tl_cu.nguoi_tai_len_id else False
    if not _la_admin_qt(user) and not is_nguoi_goc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_003",
                    "message": "Chỉ người upload gốc hoặc quản trị viên mới có thể upload phiên bản mới",
                },
            },
        )

    # Validate file mới
    _kiem_tra_file(data.file_type, data.file_size_bytes)

    tl_moi = TaiLieu(
        ten_tai_lieu=tl_cu.ten_tai_lieu,
        mo_ta=data.mo_ta if data.mo_ta is not None else tl_cu.mo_ta,
        thu_muc_id=tl_cu.thu_muc_id,
        file_url=data.file_url,
        file_name=data.file_name or tl_cu.file_name,
        file_size_bytes=data.file_size_bytes,
        file_type=data.file_type or tl_cu.file_type,
        phien_ban=tl_cu.phien_ban + 1,
        phien_ban_truoc_id=tai_lieu_id,
        tags=tl_cu.tags,
        quyen_truy_cap=tl_cu.quyen_truy_cap,
        don_vi_ids=tl_cu.don_vi_ids,
        nguoi_tai_len_id=user_id,
        is_deleted=False,
    )
    db.add(tl_moi)
    await db.commit()
    await db.refresh(tl_moi)
    return tl_moi


# ---------------------------------------------------------------------------
# Lịch sử phiên bản
# ---------------------------------------------------------------------------


async def lich_su_phien_ban(
    db: AsyncSession,
    tai_lieu_id: uuid.UUID,
    user: TokenPayload,
) -> list[TaiLieu]:
    """Trả danh sách tất cả phiên bản, đi ngược theo phien_ban_truoc_id.

    Bắt đầu từ tai_lieu_id (thường là phiên bản mới nhất),
    duyệt ngược đến phiên bản đầu tiên (phien_ban_truoc_id = None).

    Trả về sorted phien_ban DESC (mới nhất trước).
    """
    # Kiểm tra quyền xem phiên bản đầu vào
    start_stmt = select(TaiLieu).where(TaiLieu.id == tai_lieu_id)
    result = await db.execute(start_stmt)
    start_tl = result.scalar_one_or_none()

    if not start_tl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_ERR_001",
                    "message": "Không tìm thấy tài liệu",
                },
            },
        )

    if not _co_quyen_xem_tai_lieu(start_tl, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_ERR_003",
                    "message": "Bạn không có quyền xem lịch sử tài liệu này",
                },
            },
        )

    # Duyệt ngược theo phien_ban_truoc_id
    versions = []
    current_id: Optional[uuid.UUID] = tai_lieu_id
    visited = set()

    while current_id and str(current_id) not in visited:
        visited.add(str(current_id))
        stmt = select(TaiLieu).where(TaiLieu.id == current_id)
        result = await db.execute(stmt)
        tl = result.scalar_one_or_none()
        if not tl:
            break
        versions.append(tl)
        current_id = tl.phien_ban_truoc_id

    # Sắp xếp: phiên bản mới nhất trước
    versions.sort(key=lambda x: x.phien_ban, reverse=True)
    return versions


# ---------------------------------------------------------------------------
# Xóa mềm
# ---------------------------------------------------------------------------


async def xoa(
    db: AsyncSession,
    tai_lieu_id: uuid.UUID,
    user: TokenPayload,
) -> dict:
    """Xóa mềm tài liệu (is_deleted = True).

    Chỉ xóa phiên bản được trỏ đến, KHÔNG ảnh hưởng chain versioning.
    """
    tl = await _lay_theo_id(db, tai_lieu_id)

    tl.is_deleted = True
    await db.commit()
    return {"message": f"Đã xóa tài liệu '{tl.ten_tai_lieu}' (phiên bản {tl.phien_ban})"}
