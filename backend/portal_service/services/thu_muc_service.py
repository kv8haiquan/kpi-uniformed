"""
portal_service/services/thu_muc_service.py
===========================================
Business logic cho thư mục tài liệu ECM — cấu trúc cây + phân quyền.

Phân quyền truy cập thư mục:
  - ADMIN / QT_NOI_DUNG → luôn có quyền
  - TAT_CA              → tất cả CBCC
  - LANH_DAO            → user.is_lanh_dao = True
  - DON_VI / THEO_DON_VI → user.don_vi_id nằm trong entity.don_vi_ids
  - CA_NHAN             → user.id == entity.created_by

Xóa thư mục:
  - Chỉ xóa thư mục RỖNG (không có tài liệu, không có thư mục con)
"""

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from portal_service.models.tai_lieu import TaiLieu
from portal_service.models.thu_muc import ThuMuc
from portal_service.schemas.thu_muc import ThuMucCreate, ThuMucTreeResponse, ThuMucUpdate
from shared.auth import TokenPayload


# ---------------------------------------------------------------------------
# Helper: kiểm tra quyền truy cập
# ---------------------------------------------------------------------------


def _la_admin_qt(user: TokenPayload) -> bool:
    """Kiểm tra user là SUPER_ADMIN / is_admin / QT_NOI_DUNG."""
    if user.vai_tro == "SUPER_ADMIN" or user.is_admin:
        return True
    return "QT_NOI_DUNG" in (user.platform_roles or [])


def _kiem_tra_quyen_xem(entity: ThuMuc, user: TokenPayload) -> bool:
    """Kiểm tra user có quyền xem thư mục hay không.

    Thứ tự ưu tiên:
      1. ADMIN / QT_NOI_DUNG → luôn True
      2. TAT_CA              → True
      3. LANH_DAO            → user.is_lanh_dao
      4. DON_VI / THEO_DON_VI → user.don_vi_id in entity.don_vi_ids
      5. CA_NHAN             → user.id == entity.created_by
    """
    if _la_admin_qt(user):
        return True

    quyen = (entity.quyen_truy_cap or "TAT_CA").upper()

    if quyen == "TAT_CA":
        return True

    if quyen == "LANH_DAO":
        return user.is_lanh_dao

    if quyen in ("DON_VI", "THEO_DON_VI"):
        if not entity.don_vi_ids or not user.don_vi_id:
            return False
        # don_vi_ids là JSONB array of UUID strings
        don_vi_list = entity.don_vi_ids
        if isinstance(don_vi_list, list):
            return str(user.don_vi_id) in [str(d) for d in don_vi_list]
        return False

    if quyen == "CA_NHAN":
        if not entity.created_by:
            return False
        return str(entity.created_by) == str(user.sub)

    # THEO_VAI_TRO (legacy) — không hỗ trợ chi tiết, chỉ lãnh đạo mới thấy
    if quyen == "THEO_VAI_TRO":
        return user.is_lanh_dao

    return False


# ---------------------------------------------------------------------------
# Helpers lấy dữ liệu
# ---------------------------------------------------------------------------


async def _lay_theo_id(db: AsyncSession, thu_muc_id: uuid.UUID) -> ThuMuc:
    """Lấy thư mục theo ID, raise 404 nếu không tồn tại."""
    stmt = select(ThuMuc).where(ThuMuc.id == thu_muc_id)
    result = await db.execute(stmt)
    tm = result.scalar_one_or_none()
    if not tm:
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
    return tm


async def _dem_thu_muc_con(db: AsyncSession, thu_muc_id: uuid.UUID) -> int:
    """Đếm số thư mục con trực tiếp."""
    stmt = select(func.count()).where(ThuMuc.parent_id == thu_muc_id)
    result = await db.execute(stmt)
    return result.scalar() or 0


async def _dem_tai_lieu(db: AsyncSession, thu_muc_id: uuid.UUID) -> int:
    """Đếm số tài liệu trong thư mục (chưa xóa, chỉ phiên bản mới nhất)."""
    stmt = select(func.count()).where(
        TaiLieu.thu_muc_id == thu_muc_id,
        TaiLieu.is_deleted == False,  # noqa: E712
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def danh_sach(
    db: AsyncSession,
    user: TokenPayload,
    parent_id: Optional[uuid.UUID] = None,
) -> list[ThuMuc]:
    """Lấy danh sách thư mục theo parent_id, lọc theo quyền.

    parent_id = None → thư mục gốc (root)
    parent_id = uuid → thư mục con của parent đó
    """
    if parent_id is None:
        stmt = select(ThuMuc).where(ThuMuc.parent_id.is_(None))
    else:
        stmt = select(ThuMuc).where(ThuMuc.parent_id == parent_id)

    stmt = stmt.order_by(ThuMuc.thu_tu.asc(), ThuMuc.ten.asc())
    result = await db.execute(stmt)
    all_folders = list(result.scalars().all())

    # Lọc theo quyền
    if _la_admin_qt(user):
        return all_folders
    return [tm for tm in all_folders if _kiem_tra_quyen_xem(tm, user)]


async def lay_cay_thu_muc(db: AsyncSession, user: TokenPayload) -> list[ThuMucTreeResponse]:
    """Lấy toàn bộ cây thư mục (recursive), lọc theo quyền.

    Thuật toán:
      1. Load ALL thư mục từ DB
      2. Lọc theo quyền
      3. Build tree structure trong Python (tránh N+1 query)
      4. Trả về list root nodes (parent_id = None)
    """
    # Load tất cả thư mục một lần
    stmt = select(ThuMuc).order_by(ThuMuc.thu_tu.asc(), ThuMuc.ten.asc())
    result = await db.execute(stmt)
    all_folders = list(result.scalars().all())

    # Lọc theo quyền
    if not _la_admin_qt(user):
        all_folders = [tm for tm in all_folders if _kiem_tra_quyen_xem(tm, user)]

    # Build lookup dict
    accessible_ids = {str(tm.id) for tm in all_folders}

    def _build_node(folder: ThuMuc) -> ThuMucTreeResponse:
        children = [
            tm for tm in all_folders
            if tm.parent_id is not None and str(tm.parent_id) == str(folder.id)
        ]
        children.sort(key=lambda x: (x.thu_tu, x.ten))
        return ThuMucTreeResponse(
            id=folder.id,
            ten=folder.ten,
            thu_tu=folder.thu_tu,
            quyen_truy_cap=folder.quyen_truy_cap,
            children=[_build_node(c) for c in children],
        )

    # Root nodes: parent_id là None HOẶC parent không có trong accessible set
    roots = [
        tm for tm in all_folders
        if tm.parent_id is None or str(tm.parent_id) not in accessible_ids
    ]
    roots.sort(key=lambda x: (x.thu_tu, x.ten))
    return [_build_node(r) for r in roots]


async def tao(
    db: AsyncSession,
    data: ThuMucCreate,
    user: TokenPayload,
) -> ThuMuc:
    """Tạo thư mục mới.

    - Kiểm tra parent_id tồn tại (nếu cung cấp)
    - Gán created_by = user.id
    """
    user_id = uuid.UUID(user.sub)

    # Kiểm tra parent tồn tại
    if data.parent_id:
        await _lay_theo_id(db, data.parent_id)

    # Chuẩn bị don_vi_ids (list[str] → JSONB)
    don_vi_ids = data.don_vi_ids if data.don_vi_ids else None

    tm = ThuMuc(
        ten=data.ten,
        parent_id=data.parent_id,
        thu_tu=data.thu_tu if data.thu_tu is not None else 0,
        quyen_truy_cap=data.quyen_truy_cap or "TAT_CA",
        don_vi_ids=don_vi_ids,
        created_by=user_id,
    )
    db.add(tm)
    await db.commit()
    await db.refresh(tm)
    return tm


async def sua(
    db: AsyncSession,
    thu_muc_id: uuid.UUID,
    data: ThuMucUpdate,
    user: TokenPayload,
) -> ThuMuc:
    """Cập nhật thư mục.

    Kiểm tra tránh circular dependency:
    - Không cho parent_id = chính mình
    - Không cho parent_id = con cháu (tránh vòng lặp)
    """
    tm = await _lay_theo_id(db, thu_muc_id)

    if data.parent_id is not None:
        # Không cho parent = chính mình
        if data.parent_id == thu_muc_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "PORTAL_ERR_005",
                        "message": "Không thể đặt thư mục là thư mục cha của chính nó",
                    },
                },
            )

        # Kiểm tra parent_id không phải là con/cháu của thư mục hiện tại
        await _kiem_tra_khong_phai_con(db, thu_muc_id, data.parent_id)

        # Kiểm tra parent tồn tại
        await _lay_theo_id(db, data.parent_id)
        tm.parent_id = data.parent_id

    if data.ten is not None:
        tm.ten = data.ten
    if data.thu_tu is not None:
        tm.thu_tu = data.thu_tu
    if data.quyen_truy_cap is not None:
        tm.quyen_truy_cap = data.quyen_truy_cap
    if data.don_vi_ids is not None:
        tm.don_vi_ids = data.don_vi_ids

    await db.commit()
    await db.refresh(tm)
    return tm


async def _kiem_tra_khong_phai_con(
    db: AsyncSession,
    thu_muc_id: uuid.UUID,
    potential_parent_id: uuid.UUID,
) -> None:
    """Kiểm tra potential_parent_id không phải là con cháu của thu_muc_id.

    Duyệt BFS từ thu_muc_id xuống, nếu gặp potential_parent_id → raise 400.
    """
    # Load all descendants of thu_muc_id
    visited = set()
    queue = [thu_muc_id]

    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)

        # Lấy children
        stmt = select(ThuMuc.id).where(ThuMuc.parent_id == current)
        result = await db.execute(stmt)
        children_ids = [row[0] for row in result.all()]

        for child_id in children_ids:
            if child_id == potential_parent_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "error": {
                            "code": "PORTAL_ERR_005",
                            "message": "Không thể chuyển thư mục vào một thư mục con của nó (vòng lặp)",
                        },
                    },
                )
            queue.append(child_id)


async def xoa(
    db: AsyncSession,
    thu_muc_id: uuid.UUID,
    user: TokenPayload,
) -> dict:
    """Xóa thư mục.

    Điều kiện:
      - Không có thư mục con
      - Không có tài liệu (chưa xóa)
      - Nếu vi phạm → 400 PORTAL_ERR_004
    """
    tm = await _lay_theo_id(db, thu_muc_id)

    # Kiểm tra thư mục con
    so_con = await _dem_thu_muc_con(db, thu_muc_id)
    if so_con > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_ERR_004",
                    "message": f"Không thể xóa thư mục đang có {so_con} thư mục con",
                },
            },
        )

    # Kiểm tra tài liệu trong thư mục
    so_tai_lieu = await _dem_tai_lieu(db, thu_muc_id)
    if so_tai_lieu > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_ERR_004",
                    "message": f"Không thể xóa thư mục đang có {so_tai_lieu} tài liệu",
                },
            },
        )

    await db.delete(tm)
    await db.commit()
    return {"message": f"Đã xóa thư mục '{tm.ten}'"}


async def enrichment_counts(
    db: AsyncSession, thu_muc_id: uuid.UUID
) -> tuple[int, int]:
    """Trả về (so_thu_muc_con, so_tai_lieu) cho một thư mục."""
    so_con = await _dem_thu_muc_con(db, thu_muc_id)
    so_tl = await _dem_tai_lieu(db, thu_muc_id)
    return so_con, so_tl
