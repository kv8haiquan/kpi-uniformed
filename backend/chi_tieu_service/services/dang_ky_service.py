"""
chi_tieu_service/services/dang_ky_service.py
============================================
Business logic dang ky + ket qua theo thang (luong nguoi theo doi).
Trang thai: NHAP -> CHO_DUYET_DANG_KY -> DA_DUYET_DANG_KY
            -> (CHO_DUYET_SUA) / CHO_DUYET_KET_QUA -> DA_DUYET_KET_QUA.
"""

from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chi_tieu_service.constants import (
    HanhDong, TrangThai, tinh_nhan_danh_gia_tu_dong,
)
from chi_tieu_service.models.dang_ky_thang import DangKyThang
from chi_tieu_service.models.giao_nam import GiaoNam
from chi_tieu_service.schemas.dang_ky import (
    DangKyCreate, DangKyUpdate, NhapKetQuaRequest, YeuCauSuaRequest,
)
from chi_tieu_service.services.audit_helper import ghi_lich_su, snapshot


def _err(code: str, msg: str, http=status.HTTP_400_BAD_REQUEST):
    return HTTPException(status_code=http, detail={"success": False, "error": {"code": code, "message": msg}})


class DangKyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ----- helpers -----
    async def chi_tiet(self, dk_id: UUID) -> DangKyThang:
        """Lay 1 ban ghi (public — dung de check pham vi truoc khi thao tac)."""
        return await self._get(dk_id)

    async def _get(self, dk_id: UUID) -> DangKyThang:
        dk = (await self.db.execute(
            select(DangKyThang).where(DangKyThang.id == dk_id, DangKyThang.is_deleted == False)  # noqa: E712
        )).scalar_one_or_none()
        if not dk:
            raise _err("CT_ERR_404", "Ban ghi dang ky khong ton tai", status.HTTP_404_NOT_FOUND)
        return dk

    def _recompute_nhan(self, dk: DangKyThang) -> None:
        """Tinh lai danh_gia_tu_dong moi khi so lieu thay doi (giu danh_gia_ghi_chu)."""
        dk.danh_gia_tu_dong = tinh_nhan_danh_gia_tu_dong(
            bool(dk.khong_dang_ky), dk.gia_tri_ket_qua, dk.gia_tri_dang_ky
        )

    # ----- doc danh sach can dang ky trong thang -----
    async def danh_sach_can_dang_ky(self, don_vi_id: UUID, thang: int, nam: int) -> list[dict]:
        """Tra ve moi chi tieu don vi CO giao nam, kem ban ghi dang ky (neu da tao)."""
        # Cac chi tieu co giao nam (distinct chi_tieu_id)
        giao = (await self.db.execute(
            select(GiaoNam).where(
                GiaoNam.don_vi_id == don_vi_id, GiaoNam.nam == nam,
                GiaoNam.is_deleted == False,  # noqa: E712
            )
        )).scalars().all()
        if not giao:
            return []

        # Ban ghi dang ky thang hien co
        existing = (await self.db.execute(
            select(DangKyThang).where(
                DangKyThang.don_vi_id == don_vi_id,
                DangKyThang.thang == thang, DangKyThang.nam == nam,
                DangKyThang.is_deleted == False,  # noqa: E712
            )
        )).scalars().all()
        dk_map = {str(d.chi_tieu_id): d for d in existing}

        # Gom theo chi_tieu_id (mot chi tieu co the co 2 muc giao)
        seen: dict[str, dict] = {}
        for g in giao:
            key = str(g.chi_tieu_id)
            if key not in seen:
                seen[key] = {
                    "chi_tieu_id": g.chi_tieu_id,
                    "muc_giao": [],
                    "dang_ky": dk_map.get(key),
                }
            seen[key]["muc_giao"].append({
                "loai_muc": g.loai_muc,
                "gia_tri_giao": g.gia_tri_giao,
                "luy_ke_dau_ky": g.luy_ke_dau_ky,
            })
        return list(seen.values())

    # ----- tao moi (NHAP) -----
    async def tao_moi(self, data: DangKyCreate, nguoi_theo_doi_id: UUID) -> DangKyThang:
        # Phai co giao nam cho chi tieu nay
        giao = (await self.db.execute(
            select(GiaoNam).where(
                GiaoNam.don_vi_id == data.don_vi_id,
                GiaoNam.chi_tieu_id == data.chi_tieu_id,
                GiaoNam.nam == data.nam, GiaoNam.is_deleted == False,  # noqa: E712
            )
        )).first()
        if not giao:
            raise _err("CT_ERR_005", "Don vi chua duoc giao chi tieu nam cho chi tieu nay")

        # Trung (don_vi, chi_tieu, thang, nam)
        dup = (await self.db.execute(
            select(DangKyThang).where(
                DangKyThang.don_vi_id == data.don_vi_id,
                DangKyThang.chi_tieu_id == data.chi_tieu_id,
                DangKyThang.thang == data.thang, DangKyThang.nam == data.nam,
                DangKyThang.is_deleted == False,  # noqa: E712
            )
        )).scalar_one_or_none()
        if dup:
            raise _err("CT_ERR_006", "Da ton tai dang ky cho (don vi, chi tieu, thang, nam) nay")

        dk = DangKyThang(
            don_vi_id=data.don_vi_id, chi_tieu_id=data.chi_tieu_id,
            thang=data.thang, nam=data.nam,
            khong_dang_ky=data.khong_dang_ky,
            gia_tri_dang_ky=None if data.khong_dang_ky else data.gia_tri_dang_ky,
            trang_thai=TrangThai.NHAP, nguoi_theo_doi_id=nguoi_theo_doi_id,
        )
        self.db.add(dk)
        await self.db.commit()
        await self.db.refresh(dk)
        return dk

    # ----- sua (chi khi NHAP) -----
    async def cap_nhat(self, dk_id: UUID, data: DangKyUpdate) -> DangKyThang:
        dk = await self._get(dk_id)
        if dk.is_khoa:
            raise _err("CT_ERR_002", "Ban ghi da khoa, khong sua duoc")
        if dk.trang_thai != TrangThai.NHAP:
            raise _err("CT_ERR_003", "Chi sua duoc khi ban ghi o trang thai NHAP")
        upd = data.model_dump(exclude_unset=True)
        for k, v in upd.items():
            setattr(dk, k, v)
        if dk.khong_dang_ky:
            dk.gia_tri_dang_ky = None
        dk.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(dk)
        return dk

    # ----- gui duyet dang ky -----
    async def gui_duyet(self, dk_id: UUID, nguoi_id: UUID) -> DangKyThang:
        dk = await self._get(dk_id)
        if dk.trang_thai != TrangThai.NHAP:
            raise _err("CT_ERR_003", "Chi gui duyet duoc khi o trang thai NHAP")
        truoc = snapshot(dk)
        dk.trang_thai = TrangThai.CHO_DUYET_DANG_KY
        dk.ngay_gui_dang_ky = datetime.utcnow()
        dk.ly_do_tu_choi = None
        dk.updated_at = datetime.utcnow()
        ghi_lich_su(self.db, dk.id, HanhDong.GUI_DANG_KY, nguoi_id, truoc, snapshot(dk))
        await self.db.commit()
        await self.db.refresh(dk)
        return dk

    # ----- yeu cau sua dang ky da duyet -----
    async def yeu_cau_sua(self, dk_id: UUID, data: YeuCauSuaRequest, nguoi_id: UUID) -> DangKyThang:
        dk = await self._get(dk_id)
        if dk.trang_thai != TrangThai.DA_DUYET_DANG_KY:
            raise _err("CT_ERR_003", "Chi yeu cau sua khi dang ky da duyet")
        if dk.is_khoa:
            raise _err("CT_ERR_002", "Ban ghi da khoa, khong sua duoc")
        truoc = snapshot(dk)  # giu gia tri cu de khoi phuc neu bi tu choi
        dk.gia_tri_dang_ky = data.gia_tri_dang_ky_moi
        dk.khong_dang_ky = False
        dk.trang_thai = TrangThai.CHO_DUYET_SUA
        dk.updated_at = datetime.utcnow()
        ghi_lich_su(self.db, dk.id, HanhDong.GUI_SUA, nguoi_id, truoc, snapshot(dk), data.ly_do)
        await self.db.commit()
        await self.db.refresh(dk)
        return dk

    # ----- nhap (luu nhap) ket qua -----
    async def nhap_ket_qua(self, dk_id: UUID, data: NhapKetQuaRequest) -> DangKyThang:
        dk = await self._get(dk_id)
        if dk.trang_thai != TrangThai.DA_DUYET_DANG_KY:
            raise _err("CT_ERR_003", "Chi nhap ket qua khi dang ky da duyet (DA_DUYET_DANG_KY)")
        if dk.is_khoa:
            raise _err("CT_ERR_002", "Ban ghi da khoa, khong sua duoc")
        dk.gia_tri_ket_qua = data.gia_tri_ket_qua
        if data.danh_gia_ghi_chu is not None:
            dk.danh_gia_ghi_chu = data.danh_gia_ghi_chu
        self._recompute_nhan(dk)  # tinh lai nhan ngay khi so lieu doi
        dk.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(dk)
        return dk

    # ----- gui duyet ket qua -----
    async def gui_ket_qua(self, dk_id: UUID, nguoi_id: UUID) -> DangKyThang:
        dk = await self._get(dk_id)
        if dk.trang_thai != TrangThai.DA_DUYET_DANG_KY:
            raise _err("CT_ERR_003", "Chi gui ket qua khi o trang thai DA_DUYET_DANG_KY")
        if dk.gia_tri_ket_qua is None:
            raise _err("CT_ERR_003", "Chua nhap ket qua, khong the gui duyet")
        truoc = snapshot(dk)
        self._recompute_nhan(dk)
        dk.trang_thai = TrangThai.CHO_DUYET_KET_QUA
        dk.ngay_gui_ket_qua = datetime.utcnow()
        dk.ly_do_tu_choi = None
        dk.updated_at = datetime.utcnow()
        ghi_lich_su(self.db, dk.id, HanhDong.GUI_KET_QUA, nguoi_id, truoc, snapshot(dk))
        await self.db.commit()
        await self.db.refresh(dk)
        return dk

    # ----- lich su 1 ban ghi -----
    async def lich_su(self, dk_id: UUID):
        from chi_tieu_service.models.lich_su_duyet import LichSuDuyet
        rows = (await self.db.execute(
            select(LichSuDuyet).where(LichSuDuyet.dang_ky_thang_id == dk_id)
            .order_by(LichSuDuyet.created_at.asc())
        )).scalars().all()
        return rows
