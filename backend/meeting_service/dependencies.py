"""
meeting_service/dependencies.py
================================
JWT auth + db session + permission helpers HKG.

Reuse: shared.auth.decode_jwt + shared.database.create_db_engine.
KHÔNG tự implement JWT logic.
"""

import logging
import os
import sys
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

# Cho phép import shared.* và meeting_service.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.auth import decode_jwt, TokenPayload
from shared.database import create_db_engine, create_session_factory, get_db_session

from meeting_service.config import settings
from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.models.thanh_phan import ThanhPhan


logger = logging.getLogger("hkg.authz")


# OAuth2 — token lấy từ KPI login (port 8000)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8000/api/v1/auth/login")

engine = create_db_engine(settings.database_url)
session_factory = create_session_factory(engine)


async def get_db():
    async for session in get_db_session(session_factory):
        yield session


DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


# ============================================================
# AUTH
# ============================================================

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TokenPayload:
    """Decode JWT, validate access token type."""
    err = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"success": False, "error": {"code": "AUTH_001",
                "message": "Token không hợp lệ hoặc đã hết hạn"}},
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_jwt(token, settings.secret_key, settings.algorithm)
    if payload is None or payload.type != "access":
        raise err
    return payload


CurrentUserDep = Annotated[TokenPayload, Depends(get_current_user)]


# ============================================================
# PERMISSION HELPERS
# ============================================================

# Vai trò KPI có quyền xem toàn Chi cục.
# DB dùng tên ngắn (ADMIN/CCT/PCCT/TDV/PDV/CC); spec/JWT có thể có tên dài.
# Hỗ trợ cả 2 dạng để tương thích.
_VIEW_ALL_VAI_TRO = {
    "ADMIN", "SUPER_ADMIN",
    "CCT", "CHI_CUC_TRUONG",
    "PCCT", "PHO_CHI_CUC_TRUONG",
}

# Platform role HKG có quyền xem toàn Chi cục
_VIEW_ALL_PLATFORM_ROLES = {"CHANH_VP", "TRUONG_CNTT"}


def _has_view_all(user: TokenPayload) -> bool:
    """User có quyền xem toàn bộ Chi cục."""
    if user.is_admin:
        return True
    if user.vai_tro in _VIEW_ALL_VAI_TRO:
        return True
    if set(user.platform_roles or []).intersection(_VIEW_ALL_PLATFORM_ROLES):
        return True
    return False


def require_role(*allowed_roles: str):
    """Factory: kiểm tra vai_tro KPI."""
    async def checker(user: CurrentUserDep) -> TokenPayload:
        if user.is_admin or user.vai_tro in ("SUPER_ADMIN", "ADMIN"):
            return user
        if user.vai_tro in allowed_roles:
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "PERM_ROLE",
                    "message": f"Yêu cầu vai trò: {', '.join(allowed_roles)}"}},
        )
    return checker


def require_platform_role(*allowed_roles: str):
    """Factory: kiểm tra platform_roles HKG."""
    async def checker(user: CurrentUserDep) -> TokenPayload:
        if user.is_admin or user.vai_tro in ("SUPER_ADMIN", "ADMIN"):
            return user
        if set(user.platform_roles or []).intersection(allowed_roles):
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "PERM_PLATFORM",
                    "message": f"Yêu cầu platform role: {', '.join(allowed_roles)}"}},
        )
    return checker


async def _get_thu_ky_pham_vi(user_id: str, db: AsyncSession) -> set[UUID]:
    """Lấy don_vi_ids từ pham_vi của THU_KY_HOP role."""
    result = await db.execute(sa_text("""
        SELECT ccpr.pham_vi
          FROM public.cong_chuc_platform_role ccpr
          JOIN public.platform_role pr ON pr.id = ccpr.platform_role_id
         WHERE ccpr.cong_chuc_id = :uid
           AND pr.ma_role = 'THU_KY_HOP'
           AND ccpr.is_active = TRUE
           AND pr.is_active = TRUE
    """), {"uid": user_id})

    don_vi_ids: set[UUID] = set()
    for row in result.fetchall():
        pham_vi = row[0] or {}
        for dv_id in pham_vi.get("don_vi_ids", []):
            try:
                don_vi_ids.add(UUID(dv_id))
            except (ValueError, TypeError):
                continue
    return don_vi_ids


async def _can_view_cuoc_hop(
    cuoc_hop: CuocHop, user: TokenPayload, db: AsyncSession
) -> bool:
    """Logic phân quyền: ai xem được cuộc họp này."""
    user_id = UUID(user.sub)

    # 0. Sự kiện lịch công tác là lịch CÔNG KHAI NỘI BỘ — cả Chi cục xem được,
    #    đó là mục đích tồn tại của nó. Luật dưới đây viết cho cuộc họp Họp
    #    Không Giấy (chỉ người được mời); áp nguyên cho lịch công tác thì công
    #    chức thường mở tài liệu của chính lịch mình đang xem cũng bị 403.
    #    Tài liệu nhạy cảm vẫn được chặn ở tầng tài liệu bằng `phan_quyen`
    #    (G5.4), không chặn ở tầng cuộc họp.
    if cuoc_hop.nguon == "LICH_CONG_TAC":
        return True

    # 1. Toàn quyền
    if _has_view_all(user):
        return True

    # 2. Chủ tọa / Thư ký được chỉ định
    if cuoc_hop.chu_toa_id == user_id or cuoc_hop.thu_ky_id == user_id:
        return True

    # 3. Lãnh đạo đơn vị tổ chức
    if user.is_lanh_dao and user.don_vi_id:
        try:
            if cuoc_hop.don_vi_to_chuc_id == UUID(user.don_vi_id):
                return True
        except ValueError:
            pass

    # 4. Thư ký phòng/đội — kiểm tra pham_vi
    if "THU_KY_HOP" in (user.platform_roles or []):
        thu_ky_dvs = await _get_thu_ky_pham_vi(user.sub, db)
        if cuoc_hop.don_vi_to_chuc_id in thu_ky_dvs:
            return True

    # 5. Được mời tham dự
    invited = await db.execute(
        select(ThanhPhan.id).where(
            ThanhPhan.cuoc_hop_id == cuoc_hop.id,
            ThanhPhan.cong_chuc_id == user_id,
        )
    )
    if invited.scalar_one_or_none() is not None:
        return True

    return False


def log_tu_choi_cuoc_hop(hanh_dong: str, user: TokenPayload, cuoc_hop: CuocHop) -> None:
    """Log định danh mỗi khi từ chối truy cập cuộc họp (403).

    Thêm 30/07/2026: trước đây log chỉ có IP nên muốn biết ai bị 403 phải dựng
    fingerprint từ kích thước response trong nginx log (IP là NAT dùng chung cho
    gần như mọi đơn vị nên không định danh được). Nay tra bằng:
        grep 'DENY' /root/.pm2/logs/meeting-backend-out.log
    """
    logger.warning(
        "DENY %s ma_cc=%s ho_ten=%s vai_tro=%s lanh_dao=%s don_vi=%s "
        "platform_roles=%s cuoc_hop=%s dv_to_chuc=%s",
        hanh_dong,
        user.ma_cc or "?",
        user.ho_ten or "?",
        user.vai_tro or "-",
        user.is_lanh_dao,
        user.don_vi_id or "-",
        ",".join(user.platform_roles or []) or "-",
        cuoc_hop.id,
        cuoc_hop.don_vi_to_chuc_id,
    )


async def require_can_view_meeting(
    cuoc_hop_id: Annotated[UUID, Path(...)],
    user: CurrentUserDep,
    db: DatabaseDep,
) -> CuocHop:
    """Dependency: load cuoc_hop + check user xem được; raise 404/403."""
    result = await db.execute(
        select(CuocHop).where(
            CuocHop.id == cuoc_hop_id,
            CuocHop.is_deleted.is_(False),
        )
    )
    ch = result.scalar_one_or_none()
    if ch is None:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": {"code": "MEETING_NOT_FOUND",
                    "message": "Không tìm thấy cuộc họp"}},
        )
    if not await _can_view_cuoc_hop(ch, user, db):
        log_tu_choi_cuoc_hop("VIEW", user, ch)
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "NO_PERMISSION",
                    "message": "Bạn không có quyền xem cuộc họp này"}},
        )
    return ch


async def require_can_edit_meeting(
    cuoc_hop_id: Annotated[UUID, Path(...)],
    user: CurrentUserDep,
    db: DatabaseDep,
) -> CuocHop:
    """Chỉ chu_toa | thu_ky của cuộc họp | SUPER_ADMIN | TRUONG_CNTT.

    G4-fix-5 (01/05/2026): block 409 cho cuộc họp đã HUY (kể cả admin) —
    bảo vệ audit trail. Cuộc họp HUY chỉ đọc; muốn sửa phải tạo mới.
    """
    result = await db.execute(
        select(CuocHop).where(
            CuocHop.id == cuoc_hop_id,
            CuocHop.is_deleted.is_(False),
        )
    )
    ch = result.scalar_one_or_none()
    if ch is None:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": {"code": "MEETING_NOT_FOUND",
                    "message": "Không tìm thấy cuộc họp"}},
        )

    # Block edit cho cuộc họp HUY — kể cả admin (audit trail)
    if ch.trang_thai == "HUY":
        raise HTTPException(
            status_code=409,
            detail={"success": False, "error": {"code": "MEETING_CANCELLED",
                    "message": "Cuộc họp đã hủy — không thể chỉnh sửa. Vui lòng tạo cuộc họp mới."}},
        )

    user_id = UUID(user.sub)
    if user.is_admin or user.vai_tro in ("SUPER_ADMIN", "ADMIN"):
        return ch
    if "TRUONG_CNTT" in (user.platform_roles or []):
        return ch
    if ch.chu_toa_id == user_id or ch.thu_ky_id == user_id:
        return ch

    log_tu_choi_cuoc_hop("EDIT", user, ch)
    raise HTTPException(
        status_code=403,
        detail={"success": False, "error": {"code": "NO_PERMISSION",
                "message": "Bạn không có quyền chỉnh sửa cuộc họp này"}},
    )


async def require_can_manage_diem_danh(
    cuoc_hop_id: Annotated[UUID, Path(...)],
    user: CurrentUserDep,
    db: DatabaseDep,
) -> CuocHop:
    """Xem bảng điểm danh chi tiết: ban tổ chức + lãnh đạo xem-toàn-Chi-cục.

    KHÁC `require_can_edit_meeting` ở hai điểm, cả hai đều có lý do:

    1. KHÔNG chặn 409 cuộc họp HUY. Đây là dependency cho endpoint CHỈ ĐỌC —
       bảng điểm danh của cuộc họp đã hủy vẫn phải tra được để đối chiếu.
    2. CÓ tính cả CCT/PCCT/CHANH_VP (qua `_has_view_all`). Nhờ vậy tập quyền
       khớp 1:1 với cờ `canEdit` phía giao diện, tránh cảnh bảng hiện ra rồi
       mọi request đều 403.

    Quyền BẤM TAY hẹp hơn quyền xem này (chỉ chủ tọa/thư ký/admin/TRUONG_CNTT
    theo ma trận docs/HKG/HKG_PLATFORM_ROLES.md) — xem `co_the_bam_tay` trong
    DiemDanhService.chi_tiet().
    """
    result = await db.execute(
        select(CuocHop).where(
            CuocHop.id == cuoc_hop_id,
            CuocHop.is_deleted.is_(False),
        )
    )
    ch = result.scalar_one_or_none()
    if ch is None:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": {"code": "MEETING_NOT_FOUND",
                    "message": "Không tìm thấy cuộc họp"}},
        )

    user_id = UUID(user.sub)
    if _has_view_all(user):
        return ch
    if ch.chu_toa_id == user_id or ch.thu_ky_id == user_id:
        return ch

    log_tu_choi_cuoc_hop("VIEW", user, ch)
    raise HTTPException(
        status_code=403,
        detail={"success": False, "error": {"code": "NO_PERMISSION",
                "message": "Chỉ ban tổ chức cuộc họp mới xem được bảng điểm danh"}},
    )
