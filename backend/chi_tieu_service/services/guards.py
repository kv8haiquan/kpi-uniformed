"""
chi_tieu_service/services/guards.py
===================================
Kiem tra pham vi: nguoi theo doi chi thao tac don vi duoc gan;
Truong don vi chi duyet ban ghi don vi minh.
"""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status

from shared.auth import TokenPayload
from chi_tieu_service.constants import (
    ROLE_QUAN_TRI, ROLE_THEO_DOI, VAI_TRO_DUYET, VAI_TRO_LANH_DAO_CHI_CUC,
)
from chi_tieu_service.dependencies import get_pham_vi_don_vi_ids


def _is_admin(user: TokenPayload) -> bool:
    return user.is_admin or user.vai_tro == "SUPER_ADMIN"


def _err(code: str, msg: str, http=status.HTTP_403_FORBIDDEN):
    return HTTPException(status_code=http, detail={"success": False, "error": {"code": code, "message": msg}})


async def assert_theo_doi_don_vi(db, user: TokenPayload, don_vi_id: UUID) -> None:
    """Nguoi theo doi chi thao tac trong pham_vi.don_vi_ids. Admin/QT_CHI_TIEU bypass."""
    if _is_admin(user) or ROLE_QUAN_TRI in (user.platform_roles or []):
        return
    if ROLE_THEO_DOI not in (user.platform_roles or []):
        raise _err("CT_ERR_001", "Khong co quyen theo doi chi tieu")
    allowed = await get_pham_vi_don_vi_ids(db, user.sub, ROLE_THEO_DOI)
    if str(don_vi_id) not in allowed:
        raise _err("CT_ERR_001", "Khong co quyen theo doi don vi nay")


def assert_truong_don_vi(user: TokenPayload, record_don_vi_id: UUID) -> None:
    """Chi Truong DV dung don vi (hoac LD Chi cuc/admin) moi duyet."""
    if _is_admin(user) or (user.vai_tro in VAI_TRO_LANH_DAO_CHI_CUC):
        return
    if user.vai_tro in VAI_TRO_DUYET and str(user.don_vi_id) == str(record_don_vi_id):
        return
    raise _err("CT_ERR_004", "Chi Truong don vi cua don vi nay moi duoc duyet")


async def allowed_view_don_vi_ids(db, user: TokenPayload):
    """
    Pham vi XEM bao cao/giao nam cua user.
      - None         = toan Chi cuc (admin / QT_CHI_TIEU / CCT / PCCT)
      - list[str]    = chi cac don vi nay (TDV: don vi minh; THEO_DOI: pham_vi.don_vi_ids;
                       cong chuc thuong: don vi minh). [] = khong thay don vi nao.
    """
    roles = set(user.platform_roles or [])
    if _is_admin(user) or (user.vai_tro in VAI_TRO_LANH_DAO_CHI_CUC) or ROLE_QUAN_TRI in roles:
        return None
    allowed: set[str] = set()
    if user.don_vi_id:
        allowed.add(str(user.don_vi_id))
    if ROLE_THEO_DOI in roles:
        allowed |= set(await get_pham_vi_don_vi_ids(db, user.sub, ROLE_THEO_DOI))
    return list(allowed)


def loc_don_vi_theo_pham_vi(allowed, don_vi_id_yeu_cau: Optional[UUID]):
    """
    Tra ve list don_vi_ids hieu luc de loc (hoac None = khong gioi han).
    Raise 403 neu yeu cau don vi ngoai pham vi.
    """
    if allowed is None:
        return [str(don_vi_id_yeu_cau)] if don_vi_id_yeu_cau else None
    if don_vi_id_yeu_cau is not None:
        if str(don_vi_id_yeu_cau) not in allowed:
            raise _err("CT_ERR_001", "Khong co quyen xem don vi nay")
        return [str(don_vi_id_yeu_cau)]
    return allowed


async def don_vi_ids_duyet(db, user: TokenPayload) -> list[UUID]:
    """Danh sach don vi ma user duoc duyet (cho hang cho)."""
    # Admin/LD chi cuc: tra rong -> caller xu ly nhu xem tat ca (de don gian:
    # hang cho duyet dung cho TDV; LD/admin truyen don_vi cu the qua filter).
    if user.don_vi_id:
        return [UUID(user.don_vi_id)]
    return []
