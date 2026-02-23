"""
portal_service/services/bai_viet_service.py
============================================
Business logic cho bài viết portal — workflow duyệt 4 bước.

Workflow trạng thái hợp lệ:
  NHAP      → KIEM_TRA   Người soạn (BIEN_TAP) gửi kiểm tra
  KIEM_TRA  → DUYET      QT_NOI_DUNG kiểm tra OK
  KIEM_TRA  → NHAP       QT_NOI_DUNG từ chối / trả lại
  DUYET     → XUAT_BAN   Lãnh đạo (is_lanh_dao=True) duyệt đăng
  DUYET     → NHAP       Lãnh đạo từ chối
  XUAT_BAN  → THU_HOI    QT_NOI_DUNG / ADMIN thu hồi
  THU_HOI   → NHAP       Người soạn sửa và gửi lại

Quy tắc ghim:
  - Tối đa 3 bài ghim cùng lúc
  - Chỉ QT_NOI_DUNG / ADMIN có quyền ghim
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from portal_service.models.bai_viet import BaiViet
from portal_service.schemas.bai_viet import BaiVietCreate, BaiVietUpdate
from shared.auth import TokenPayload


# ---------------------------------------------------------------------------
# Bảng quy tắc workflow
# ---------------------------------------------------------------------------

# (trang_thai_hien_tai, trang_thai_moi) → dict quy tắc
WORKFLOW_TRANSITIONS: dict[tuple[str, str], dict] = {
    # Người soạn gửi duyệt (BIEN_TAP hoặc QT_NOI_DUNG)
    ("NHAP", "KIEM_TRA"): {
        "roles": ["BIEN_TAP", "QT_NOI_DUNG"],
        "lanh_dao": False,
        "chi_nguoi_soan": True,  # BIEN_TAP chỉ gửi bài mình soạn
    },
    # QT_NOI_DUNG kiểm tra OK → chuyển Duyệt
    ("KIEM_TRA", "DUYET"): {
        "roles": ["QT_NOI_DUNG"],
        "lanh_dao": False,
        "chi_nguoi_soan": False,
    },
    # QT_NOI_DUNG từ chối → trả về Nháp
    ("KIEM_TRA", "NHAP"): {
        "roles": ["QT_NOI_DUNG"],
        "lanh_dao": False,
        "chi_nguoi_soan": False,
    },
    # Lãnh đạo duyệt đăng
    ("DUYET", "XUAT_BAN"): {
        "roles": [],  # Không cần platform role
        "lanh_dao": True,  # Bắt buộc is_lanh_dao=True
        "chi_nguoi_soan": False,
    },
    # Lãnh đạo từ chối → trả về Nháp
    ("DUYET", "NHAP"): {
        "roles": [],
        "lanh_dao": True,
        "chi_nguoi_soan": False,
    },
    # QT_NOI_DUNG / ADMIN thu hồi bài đã đăng
    ("XUAT_BAN", "THU_HOI"): {
        "roles": ["QT_NOI_DUNG"],
        "lanh_dao": False,
        "chi_nguoi_soan": False,
    },
    # Người soạn sửa và gửi lại sau khi bị thu hồi
    ("THU_HOI", "NHAP"): {
        "roles": ["BIEN_TAP", "QT_NOI_DUNG"],
        "lanh_dao": False,
        "chi_nguoi_soan": True,
    },
}


# ---------------------------------------------------------------------------
# Helpers kiểm tra quyền
# ---------------------------------------------------------------------------


def _la_admin_qt(user: TokenPayload) -> bool:
    """Kiểm tra user là SUPER_ADMIN, is_admin, hoặc QT_NOI_DUNG."""
    if user.vai_tro == "SUPER_ADMIN" or user.is_admin:
        return True
    return "QT_NOI_DUNG" in (user.platform_roles or [])


def _la_super(user: TokenPayload) -> bool:
    """Kiểm tra user là SUPER_ADMIN hoặc is_admin."""
    return user.vai_tro == "SUPER_ADMIN" or user.is_admin


# ---------------------------------------------------------------------------
# Helper lấy bài viết theo ID
# ---------------------------------------------------------------------------


async def _lay_theo_id(db: AsyncSession, bai_viet_id: uuid.UUID) -> BaiViet:
    """Lấy bài viết theo ID, raise 404 nếu không tồn tại hoặc đã xóa mềm."""
    stmt = select(BaiViet).where(
        BaiViet.id == bai_viet_id,
        BaiViet.is_deleted == False,  # noqa: E712
    )
    result = await db.execute(stmt)
    bv = result.scalar_one_or_none()
    if not bv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_ERR_001",
                    "message": "Không tìm thấy bài viết",
                },
            },
        )
    return bv


# ---------------------------------------------------------------------------
# Danh sách
# ---------------------------------------------------------------------------


async def danh_sach_cong_khai(
    db: AsyncSession,
    chuyen_muc_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[BaiViet], int]:
    """Danh sách bài viết công khai (chỉ XUAT_BAN).

    Sắp xếp: is_ghim DESC (bài ghim đầu), ngay_xuat_ban DESC (mới nhất).
    """
    stmt = select(BaiViet).where(
        BaiViet.trang_thai == "XUAT_BAN",
        BaiViet.is_deleted == False,  # noqa: E712
    )

    if chuyen_muc_id:
        stmt = stmt.where(BaiViet.chuyen_muc_id == chuyen_muc_id)

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                BaiViet.tieu_de.ilike(pattern),
                BaiViet.tom_tat.ilike(pattern),
            )
        )

    # Đếm tổng số bản ghi
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    # Sắp xếp: ghim trước → ngày xuất bản mới nhất
    stmt = stmt.order_by(
        BaiViet.is_ghim.desc(),
        BaiViet.ngay_xuat_ban.desc(),
    )

    # Phân trang
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def danh_sach_quan_ly(
    db: AsyncSession,
    user: TokenPayload,
    trang_thai: Optional[str] = None,
    chuyen_muc_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[BaiViet], int]:
    """Danh sách bài viết cho quản lý.

    Phân quyền:
      - BIEN_TAP: chỉ thấy bài mình soạn
      - QT_NOI_DUNG / ADMIN: thấy tất cả bài
    """
    stmt = select(BaiViet).where(BaiViet.is_deleted == False)  # noqa: E712

    # Phân quyền lọc theo người soạn
    if not _la_admin_qt(user):
        user_id = uuid.UUID(user.sub)
        stmt = stmt.where(BaiViet.nguoi_soan_id == user_id)

    if trang_thai:
        stmt = stmt.where(BaiViet.trang_thai == trang_thai)

    if chuyen_muc_id:
        stmt = stmt.where(BaiViet.chuyen_muc_id == chuyen_muc_id)

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                BaiViet.tieu_de.ilike(pattern),
                BaiViet.tom_tat.ilike(pattern),
            )
        )

    # Đếm tổng
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    stmt = stmt.order_by(BaiViet.updated_at.desc(), BaiViet.created_at.desc())

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    return list(result.scalars().all()), total


# ---------------------------------------------------------------------------
# Chi tiết
# ---------------------------------------------------------------------------


async def chi_tiet(
    db: AsyncSession,
    bai_viet_id: uuid.UUID,
) -> BaiViet:
    """Lấy chi tiết bài viết. Side effect: tăng so_luot_xem += 1."""
    bv = await _lay_theo_id(db, bai_viet_id)
    bv.so_luot_xem = (bv.so_luot_xem or 0) + 1
    await db.commit()
    await db.refresh(bv)
    return bv


# ---------------------------------------------------------------------------
# Tạo
# ---------------------------------------------------------------------------


async def tao_bai_viet(
    db: AsyncSession,
    data: BaiVietCreate,
    user: TokenPayload,
) -> BaiViet:
    """Tạo bài viết mới ở trạng thái NHAP."""
    user_id = uuid.UUID(user.sub)
    bv = BaiViet(
        chuyen_muc_id=data.chuyen_muc_id,
        tieu_de=data.tieu_de,
        tom_tat=data.tom_tat,
        noi_dung=data.noi_dung,
        anh_dai_dien=data.anh_dai_dien,
        trang_thai="NHAP",
        nguoi_soan_id=user_id,
        is_ghim=False,
        so_luot_xem=0,
        is_deleted=False,
    )
    db.add(bv)
    await db.commit()
    await db.refresh(bv)
    return bv


# ---------------------------------------------------------------------------
# Workflow: Đổi trạng thái
# ---------------------------------------------------------------------------


async def doi_trang_thai(
    db: AsyncSession,
    bai_viet_id: uuid.UUID,
    trang_thai_moi: str,
    user: TokenPayload,
    ly_do: Optional[str] = None,
) -> BaiViet:
    """Đổi trạng thái workflow bài viết.

    Logic:
      1. Kiểm tra chuyển đổi hợp lệ (theo WORKFLOW_TRANSITIONS)
      2. Kiểm tra quyền (role / lãnh đạo / người soạn)
      3. Thực hiện chuyển đổi + side effects (gán nguoi_kiem_tra/nguoi_duyet/ngay_xuat_ban)
    """
    bv = await _lay_theo_id(db, bai_viet_id)
    trang_thai_hien_tai = bv.trang_thai
    user_id = uuid.UUID(user.sub)

    # -----------------------------------------------------------------------
    # Bước 1: Kiểm tra chuyển đổi có hợp lệ không
    # -----------------------------------------------------------------------
    transition_key = (trang_thai_hien_tai, trang_thai_moi)
    if transition_key not in WORKFLOW_TRANSITIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_ERR_002",
                    "message": (
                        f"Không thể chuyển trạng thái từ '{trang_thai_hien_tai}' "
                        f"sang '{trang_thai_moi}'"
                    ),
                },
            },
        )

    rule = WORKFLOW_TRANSITIONS[transition_key]

    # -----------------------------------------------------------------------
    # Bước 2: Kiểm tra quyền
    # -----------------------------------------------------------------------
    is_super = _la_super(user)
    user_roles = set(user.platform_roles or [])

    if not is_super:
        # Kiểm tra yêu cầu lãnh đạo
        if rule["lanh_dao"] and not user.is_lanh_dao:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_002",
                        "message": "Chỉ lãnh đạo mới có thể thực hiện thao tác này",
                    },
                },
            )

        # Kiểm tra platform roles (chỉ khi transition cần role cụ thể)
        if rule["roles"] and not user_roles.intersection(set(rule["roles"])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_001",
                        "message": f"Yêu cầu vai trò: {', '.join(rule['roles'])}",
                    },
                },
            )

        # Kiểm tra giới hạn chỉ người soạn
        if rule["chi_nguoi_soan"]:
            # QT_NOI_DUNG được miễn điều kiện này
            if "QT_NOI_DUNG" not in user_roles and bv.nguoi_soan_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "error": {
                            "code": "PERM_003",
                            "message": "Chỉ người soạn bài mới có thể thực hiện thao tác này",
                        },
                    },
                )

    # -----------------------------------------------------------------------
    # Bước 3: Thực hiện chuyển đổi + side effects
    # -----------------------------------------------------------------------
    bv.trang_thai = trang_thai_moi

    if trang_thai_moi == "DUYET":
        # Gán người kiểm tra khi chuyển KIEM_TRA → DUYET
        bv.nguoi_kiem_tra_id = user_id

    elif trang_thai_moi == "XUAT_BAN":
        # Gán người duyệt và ngày xuất bản khi chuyển DUYET → XUAT_BAN
        bv.nguoi_duyet_id = user_id
        bv.ngay_xuat_ban = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(bv)
    return bv


# ---------------------------------------------------------------------------
# Ghim bài viết
# ---------------------------------------------------------------------------


async def ghim_bai_viet(
    db: AsyncSession,
    bai_viet_id: uuid.UUID,
    is_ghim: bool,
    user: TokenPayload,
) -> BaiViet:
    """Ghim / bỏ ghim bài viết.

    Quy tắc:
      - Chỉ QT_NOI_DUNG / ADMIN có quyền ghim
      - Tối đa 3 bài ghim cùng lúc
      - Nếu ghim bài mới khi đã có đủ 3 → lỗi 400
    """
    bv = await _lay_theo_id(db, bai_viet_id)

    if is_ghim:
        # Đếm số bài đang ghim (trừ chính bài này nếu nó đang được ghim)
        stmt = select(func.count()).where(
            BaiViet.is_ghim == True,  # noqa: E712
            BaiViet.is_deleted == False,  # noqa: E712
            BaiViet.id != bai_viet_id,
        )
        result = await db.execute(stmt)
        so_ghim_hien_tai = result.scalar() or 0

        if so_ghim_hien_tai >= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "PORTAL_ERR_004",
                        "message": (
                            "Đã đạt giới hạn 3 bài ghim. "
                            "Vui lòng bỏ ghim bài khác trước khi ghim bài mới."
                        ),
                    },
                },
            )

    bv.is_ghim = is_ghim
    await db.commit()
    await db.refresh(bv)
    return bv


# ---------------------------------------------------------------------------
# Sửa bài viết
# ---------------------------------------------------------------------------


async def sua_bai_viet(
    db: AsyncSession,
    bai_viet_id: uuid.UUID,
    data: BaiVietUpdate,
    user: TokenPayload,
) -> BaiViet:
    """Cập nhật nội dung bài viết.

    Điều kiện:
      - Bài phải ở trạng thái NHAP
      - BIEN_TAP: chỉ sửa bài mình soạn
      - QT_NOI_DUNG / ADMIN: sửa tất cả
    """
    bv = await _lay_theo_id(db, bai_viet_id)
    user_id = uuid.UUID(user.sub)

    # Kiểm tra trạng thái
    if bv.trang_thai != "NHAP":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_ERR_002",
                    "message": "Chỉ có thể sửa bài viết ở trạng thái NHAP",
                },
            },
        )

    # Kiểm tra quyền sửa
    if not _la_super(user) and not _la_admin_qt(user):
        # BIEN_TAP chỉ sửa bài mình soạn
        if bv.nguoi_soan_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_003",
                        "message": "Chỉ người soạn bài mới có thể sửa bài viết này",
                    },
                },
            )

    # Cập nhật các field được cung cấp
    if data.chuyen_muc_id is not None:
        bv.chuyen_muc_id = data.chuyen_muc_id
    if data.tieu_de is not None:
        bv.tieu_de = data.tieu_de
    if data.tom_tat is not None:
        bv.tom_tat = data.tom_tat
    if data.noi_dung is not None:
        bv.noi_dung = data.noi_dung
    if data.anh_dai_dien is not None:
        bv.anh_dai_dien = data.anh_dai_dien

    bv.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(bv)
    return bv


# ---------------------------------------------------------------------------
# Xóa mềm bài viết
# ---------------------------------------------------------------------------


async def xoa_bai_viet(
    db: AsyncSession,
    bai_viet_id: uuid.UUID,
    user: TokenPayload,
) -> dict:
    """Xóa mềm bài viết (is_deleted=True).

    Điều kiện:
      - Chỉ xóa được khi NHAP
      - BIEN_TAP: chỉ xóa bài mình soạn
      - QT_NOI_DUNG / ADMIN: xóa tất cả
    """
    bv = await _lay_theo_id(db, bai_viet_id)
    user_id = uuid.UUID(user.sub)

    # Kiểm tra trạng thái
    if bv.trang_thai != "NHAP":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_ERR_002",
                    "message": "Chỉ có thể xóa bài viết ở trạng thái NHAP",
                },
            },
        )

    # Kiểm tra quyền xóa
    if not _la_super(user) and not _la_admin_qt(user):
        if bv.nguoi_soan_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_003",
                        "message": "Chỉ người soạn bài mới có thể xóa bài viết này",
                    },
                },
            )

    bv.is_deleted = True
    bv.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    return {"message": "Đã xóa bài viết"}
