"""
chi_tieu_service/services/duyet_service.py
==========================================
Business logic duyet/tu choi cua Truong don vi + mo khoa.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chi_tieu_service.constants import (
    HANH_DONG_DUYET, HANH_DONG_TU_CHOI, HanhDong, LOAI_CHO_DUYET,
    TU_CHOI_TRANSITION, TrangThai, DUYET_TRANSITION, tinh_nhan_danh_gia_tu_dong,
)
from chi_tieu_service.models.dang_ky_thang import DangKyThang
from chi_tieu_service.models.lich_su_duyet import LichSuDuyet
from chi_tieu_service.services.audit_helper import ghi_lich_su, snapshot


def _err(code: str, msg: str, http=status.HTTP_400_BAD_REQUEST):
    return HTTPException(status_code=http, detail={"success": False, "error": {"code": code, "message": msg}})


class DuyetService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get(self, dk_id: UUID) -> DangKyThang:
        dk = (await self.db.execute(
            select(DangKyThang).where(DangKyThang.id == dk_id, DangKyThang.is_deleted == False)  # noqa: E712
        )).scalar_one_or_none()
        if not dk:
            raise _err("CT_ERR_404", "Ban ghi khong ton tai", status.HTTP_404_NOT_FOUND)
        return dk

    async def cho_xu_ly(self, loai: str, don_vi_ids: list[UUID], page: int = 1, page_size: int = 50) -> dict:
        """Hang cho duyet theo loai (DANG_KY|SUA|KET_QUA), gioi han trong cac don vi cua TDV."""
        trang_thai = LOAI_CHO_DUYET.get(loai)
        if not trang_thai:
            raise _err("CT_ERR_003", "Loai cho duyet khong hop le (DANG_KY|SUA|KET_QUA)")
        if not don_vi_ids:
            return {"items": [], "pagination": {"page": page, "page_size": page_size, "total_items": 0, "total_pages": 0}}
        conds = [
            DangKyThang.trang_thai == trang_thai,
            DangKyThang.don_vi_id.in_(don_vi_ids),
            DangKyThang.is_deleted == False,  # noqa: E712
        ]
        items = (await self.db.execute(
            select(DangKyThang).where(*conds).order_by(DangKyThang.ngay_gui_dang_ky.asc())
            .offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
        return {
            "items": items,
            "pagination": {
                "page": page, "page_size": page_size, "total_items": len(items),
                "total_pages": 1,
            },
        }

    async def duyet(self, dk_id: UUID, nguoi_duyet_id: UUID) -> DangKyThang:
        dk = await self._get(dk_id)
        sau_trang_thai = DUYET_TRANSITION.get(dk.trang_thai)
        if not sau_trang_thai:
            raise _err("CT_ERR_003", f"Khong the duyet o trang thai {dk.trang_thai}")
        truoc = snapshot(dk)
        hanh_dong = HANH_DONG_DUYET[dk.trang_thai]
        now = datetime.utcnow()

        if dk.trang_thai == TrangThai.CHO_DUYET_DANG_KY:
            dk.ngay_duyet_dang_ky = now
        elif dk.trang_thai == TrangThai.CHO_DUYET_SUA:
            # ap gia tri moi (da set khi yeu cau sua) — chi xac nhan
            dk.ngay_duyet_dang_ky = now
        elif dk.trang_thai == TrangThai.CHO_DUYET_KET_QUA:
            dk.ngay_duyet_ket_qua = now
            dk.is_khoa = True
            # tinh lai nhan khi chot
            dk.danh_gia_tu_dong = tinh_nhan_danh_gia_tu_dong(
                bool(dk.khong_dang_ky), dk.gia_tri_ket_qua, dk.gia_tri_dang_ky
            )

        dk.trang_thai = sau_trang_thai
        dk.nguoi_duyet_id = nguoi_duyet_id
        dk.ly_do_tu_choi = None
        dk.updated_at = now
        ghi_lich_su(self.db, dk.id, hanh_dong, nguoi_duyet_id, truoc, snapshot(dk))
        await self.db.commit()
        await self.db.refresh(dk)
        return dk

    async def tu_choi(self, dk_id: UUID, ly_do: str, nguoi_duyet_id: UUID) -> DangKyThang:
        dk = await self._get(dk_id)
        ve_trang_thai = TU_CHOI_TRANSITION.get(dk.trang_thai)
        if not ve_trang_thai:
            raise _err("CT_ERR_003", f"Khong the tu choi o trang thai {dk.trang_thai}")
        truoc = snapshot(dk)
        hanh_dong = HANH_DONG_TU_CHOI[dk.trang_thai]

        # Tu choi yeu cau sua: khoi phuc gia tri dang ky cu tu snapshot GUI_SUA
        if dk.trang_thai == TrangThai.CHO_DUYET_SUA:
            await self._khoi_phuc_truoc_sua(dk)
        # Tu choi ket qua: GIU gia_tri_ket_qua cu, chi reset moc gui
        if dk.trang_thai == TrangThai.CHO_DUYET_KET_QUA:
            dk.ngay_gui_ket_qua = None

        dk.trang_thai = ve_trang_thai
        dk.ly_do_tu_choi = ly_do
        dk.nguoi_duyet_id = nguoi_duyet_id
        dk.updated_at = datetime.utcnow()
        ghi_lich_su(self.db, dk.id, hanh_dong, nguoi_duyet_id, truoc, snapshot(dk), ly_do)
        await self.db.commit()
        await self.db.refresh(dk)
        return dk

    async def _khoi_phuc_truoc_sua(self, dk: DangKyThang) -> None:
        """Lay snapshot noi_dung_truoc cua hanh dong GUI_SUA gan nhat de khoi phuc gia tri cu."""
        row = (await self.db.execute(
            select(LichSuDuyet).where(
                LichSuDuyet.dang_ky_thang_id == dk.id,
                LichSuDuyet.hanh_dong == HanhDong.GUI_SUA,
            ).order_by(LichSuDuyet.created_at.desc()).limit(1)
        )).scalar_one_or_none()
        if row and row.noi_dung_truoc:
            truoc = row.noi_dung_truoc
            gtdk = truoc.get("gia_tri_dang_ky")
            dk.gia_tri_dang_ky = Decimal(gtdk) if gtdk is not None else None
            dk.khong_dang_ky = bool(truoc.get("khong_dang_ky"))

    async def mo_khoa(self, dk_id: UUID, nguoi_id: UUID) -> DangKyThang:
        dk = await self._get(dk_id)
        if dk.trang_thai != TrangThai.DA_DUYET_KET_QUA:
            raise _err("CT_ERR_003", "Chi mo khoa duoc ban ghi da chot ket qua")
        truoc = snapshot(dk)
        dk.trang_thai = TrangThai.DA_DUYET_DANG_KY
        dk.is_khoa = False
        dk.ngay_duyet_ket_qua = None
        dk.updated_at = datetime.utcnow()
        ghi_lich_su(self.db, dk.id, HanhDong.MO_KHOA, nguoi_id, truoc, snapshot(dk))
        await self.db.commit()
        await self.db.refresh(dk)
        return dk
