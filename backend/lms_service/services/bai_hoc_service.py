"""
lms_service/services/bai_hoc_service.py
=======================================
Business logic cho CRUD bai hoc + cap nhat tien do hoc tap.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.models.bai_hoc import BaiHoc
from lms_service.models.khoa_hoc import KhoaHoc
from lms_service.models.tien_do_bai_hoc import TienDoBaiHoc
from lms_service.models.dang_ky_khoa_hoc import DangKyKhoaHoc
from lms_service.schemas.bai_hoc import BaiHocCreate, BaiHocUpdate, SapXepItem, TienDoUpdate
from shared.auth import TokenPayload


class BaiHocService:
    """Service xu ly logic bai hoc va tien do hoc tap."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # HELPERS
    # =========================================================================
    def _is_manager(self, user: TokenPayload) -> bool:
        """Kiem tra user co quyen quan ly (QT_DAO_TAO hoac SUPER_ADMIN)."""
        return (
            user.vai_tro == "SUPER_ADMIN"
            or "QT_DAO_TAO" in (user.platform_roles or [])
        )

    def _is_giang_vien(self, user: TokenPayload) -> bool:
        return "GIANG_VIEN" in (user.platform_roles or [])

    async def _get_khoa_hoc(self, khoa_hoc_id: uuid.UUID) -> KhoaHoc:
        result = await self.db.execute(
            select(KhoaHoc).where(KhoaHoc.id == khoa_hoc_id)
        )
        kh = result.scalar_one_or_none()
        if kh is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy khóa học"}},
            )
        return kh

    async def _get_bai_hoc(self, bai_hoc_id: uuid.UUID) -> BaiHoc:
        result = await self.db.execute(
            select(BaiHoc).where(BaiHoc.id == bai_hoc_id, BaiHoc.is_active == True)  # noqa: E712
        )
        bh = result.scalar_one_or_none()
        if bh is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy bài học"}},
            )
        return bh

    async def _check_gv_quyen(self, kh: KhoaHoc, user: TokenPayload):
        """Kiem tra giang vien chi thao tac khoa cua minh."""
        if self._is_manager(user):
            return
        if self._is_giang_vien(user) and str(kh.giang_vien_id) == user.sub:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "LMS_ERR_008", "message": "Bạn chỉ được thao tác khóa học của mình"}},
        )

    async def _get_dang_ky(self, cong_chuc_id: uuid.UUID, khoa_hoc_id: uuid.UUID) -> Optional[DangKyKhoaHoc]:
        result = await self.db.execute(
            select(DangKyKhoaHoc).where(
                DangKyKhoaHoc.cong_chuc_id == cong_chuc_id,
                DangKyKhoaHoc.khoa_hoc_id == khoa_hoc_id,
            )
        )
        return result.scalar_one_or_none()

    def _bai_hoc_to_dict(self, bh: BaiHoc, tien_do: Optional[TienDoBaiHoc] = None) -> dict:
        data = {
            "id": bh.id,
            "khoa_hoc_id": bh.khoa_hoc_id,
            "thu_tu": bh.thu_tu,
            "tieu_de": bh.tieu_de,
            "loai_noi_dung": bh.loai_noi_dung,
            "noi_dung": bh.noi_dung,
            "file_url": bh.file_url,
            "pdf_url": bh.pdf_url,
            "file_size_mb": bh.file_size_mb,
            "thoi_luong_phut": bh.thoi_luong_phut,
            "phai_xem_het": bh.phai_xem_het,
            "thoi_gian_toi_thieu_giay": bh.thoi_gian_toi_thieu_giay,
            "is_active": bh.is_active,
            "created_at": bh.created_at,
            "tien_do_ca_nhan": None,
        }
        if tien_do:
            data["tien_do_ca_nhan"] = {
                "trang_thai": tien_do.trang_thai or "CHUA_XEM",
                "thoi_gian_xem_giay": tien_do.thoi_gian_xem_giay or 0,
                "ngay_hoan_thanh": tien_do.ngay_hoan_thanh,
            }
        return data

    # =========================================================================
    # 1. DANH SACH BAI HOC cua 1 khoa hoc
    # =========================================================================
    async def danh_sach(self, khoa_hoc_id: uuid.UUID, user: TokenPayload) -> list[dict]:
        """Danh sach bai hoc cua khoa hoc, kem tien do ca nhan."""
        kh = await self._get_khoa_hoc(khoa_hoc_id)

        # Kiem tra quyen xem
        if kh.trang_thai not in ("DA_XUAT_BAN", "TAM_DUNG", "DA_DONG"):
            if not self._is_manager(user):
                if not (self._is_giang_vien(user) and str(kh.giang_vien_id) == user.sub):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={"success": False, "error": {"code": "LMS_ERR_008", "message": "Khóa học chưa xuất bản"}},
                    )

        user_uuid = uuid.UUID(user.sub)

        # Query bai hoc + LEFT JOIN tien do ca nhan
        stmt = (
            select(BaiHoc, TienDoBaiHoc)
            .outerjoin(
                TienDoBaiHoc,
                (BaiHoc.id == TienDoBaiHoc.bai_hoc_id) & (TienDoBaiHoc.cong_chuc_id == user_uuid),
            )
            .where(BaiHoc.khoa_hoc_id == khoa_hoc_id, BaiHoc.is_active == True)  # noqa: E712
            .order_by(BaiHoc.thu_tu.asc())
        )

        result = await self.db.execute(stmt)
        rows = result.all()
        return [self._bai_hoc_to_dict(bh, td) for bh, td in rows]

    # =========================================================================
    # 2. CHI TIET BAI HOC
    # =========================================================================
    async def chi_tiet(self, bai_hoc_id: uuid.UUID, user: TokenPayload) -> dict:
        """Chi tiet bai hoc kem tien do ca nhan."""
        bh = await self._get_bai_hoc(bai_hoc_id)
        kh = await self._get_khoa_hoc(bh.khoa_hoc_id)
        user_uuid = uuid.UUID(user.sub)

        # Kiem tra quyen: da dang ky hoac la GIANG_VIEN/QT_DAO_TAO
        if not self._is_manager(user):
            if not (self._is_giang_vien(user) and str(kh.giang_vien_id) == user.sub):
                dk = await self._get_dang_ky(user_uuid, bh.khoa_hoc_id)
                if dk is None:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={"success": False, "error": {"code": "LMS_ERR_008", "message": "Bạn chưa đăng ký khóa học này"}},
                    )

        # Lay tien do ca nhan
        td_result = await self.db.execute(
            select(TienDoBaiHoc).where(
                TienDoBaiHoc.bai_hoc_id == bai_hoc_id,
                TienDoBaiHoc.cong_chuc_id == user_uuid,
            )
        )
        tien_do = td_result.scalar_one_or_none()
        return self._bai_hoc_to_dict(bh, tien_do)

    # =========================================================================
    # 3. TAO MOI
    # =========================================================================
    async def tao_moi(
        self, khoa_hoc_id: uuid.UUID, data: BaiHocCreate, user: TokenPayload
    ) -> BaiHoc:
        """Tao bai hoc moi. Tu dong tang so_bai_hoc cua khoa."""
        kh = await self._get_khoa_hoc(khoa_hoc_id)
        await self._check_gv_quyen(kh, user)

        # Tu dong set thu_tu = MAX + 1 neu khong truyen
        thu_tu = data.thu_tu
        if thu_tu is None:
            max_result = await self.db.execute(
                select(func.coalesce(func.max(BaiHoc.thu_tu), 0)).where(
                    BaiHoc.khoa_hoc_id == khoa_hoc_id,
                    BaiHoc.is_active == True,  # noqa: E712
                )
            )
            thu_tu = (max_result.scalar() or 0) + 1

        bh = BaiHoc(
            khoa_hoc_id=khoa_hoc_id,
            tieu_de=data.tieu_de,
            loai_noi_dung=data.loai_noi_dung,
            noi_dung=data.noi_dung,
            file_url=data.file_url,
            pdf_url=data.pdf_url,
            file_size_mb=data.file_size_mb,
            thoi_luong_phut=data.thoi_luong_phut,
            thu_tu=thu_tu,
            phai_xem_het=data.phai_xem_het,
            thoi_gian_toi_thieu_giay=data.thoi_gian_toi_thieu_giay,
        )
        self.db.add(bh)
        await self.db.flush()

        # Side effect: tang so_bai_hoc cua khoa hoc
        kh.so_bai_hoc = (kh.so_bai_hoc or 0) + 1
        await self.db.flush()
        await self.db.refresh(bh)
        return bh

    # =========================================================================
    # 4. CAP NHAT
    # =========================================================================
    async def cap_nhat(
        self, bai_hoc_id: uuid.UUID, data: BaiHocUpdate, user: TokenPayload
    ) -> BaiHoc:
        """Cap nhat bai hoc — chi update fields khong None."""
        bh = await self._get_bai_hoc(bai_hoc_id)
        kh = await self._get_khoa_hoc(bh.khoa_hoc_id)
        await self._check_gv_quyen(kh, user)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(bh, field, value)

        await self.db.flush()
        await self.db.refresh(bh)
        return bh

    # =========================================================================
    # 5. XOA (soft delete)
    # =========================================================================
    async def xoa(self, bai_hoc_id: uuid.UUID, user: TokenPayload) -> None:
        """Soft delete bai hoc. Giam so_bai_hoc cua khoa."""
        bh = await self._get_bai_hoc(bai_hoc_id)
        kh = await self._get_khoa_hoc(bh.khoa_hoc_id)
        await self._check_gv_quyen(kh, user)

        bh.is_active = False
        # Side effect: giam so_bai_hoc
        kh.so_bai_hoc = max((kh.so_bai_hoc or 1) - 1, 0)
        await self.db.flush()

    # =========================================================================
    # 6. CAP NHAT TIEN DO
    # =========================================================================
    async def cap_nhat_tien_do(
        self, bai_hoc_id: uuid.UUID, data: TienDoUpdate, user: TokenPayload
    ) -> dict:
        """Cap nhat tien do hoc bai.

        Logic:
        - Kiem tra user da dang ky khoa hoc
        - UPSERT tien_do_bai_hoc
        - Cong don thoi_gian_xem_giay
        - Neu hoan_thanh: set DA_HOAN_THANH, tinh lai phan_tram
        - Side effect: cap nhat dang_ky_khoa_hoc (trang_thai, phan_tram)
        """
        bh = await self._get_bai_hoc(bai_hoc_id)
        user_uuid = uuid.UUID(user.sub)

        # Kiem tra da dang ky khoa hoc chua
        dk = await self._get_dang_ky(user_uuid, bh.khoa_hoc_id)
        if dk is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "LMS_ERR_003", "message": "Bạn chưa đăng ký khóa học này"}},
            )

        now = datetime.utcnow()

        # Side effect: lan dau xem bai → chuyen dang_ky sang DANG_HOC
        if dk.trang_thai == "CHUA_BAT_DAU":
            dk.trang_thai = "DANG_HOC"
            dk.ngay_bat_dau_hoc = now

        # Tim hoac tao tien_do_bai_hoc (UPSERT)
        td_result = await self.db.execute(
            select(TienDoBaiHoc).where(
                TienDoBaiHoc.cong_chuc_id == user_uuid,
                TienDoBaiHoc.bai_hoc_id == bai_hoc_id,
            )
        )
        tien_do = td_result.scalar_one_or_none()

        if tien_do is None:
            tien_do = TienDoBaiHoc(
                cong_chuc_id=user_uuid,
                bai_hoc_id=bai_hoc_id,
                trang_thai="DANG_XEM",
                thoi_gian_xem_giay=data.thoi_gian_xem_giay,
                lan_xem_cuoi=now,
            )
            self.db.add(tien_do)
        else:
            # Cong don thoi gian xem
            tien_do.thoi_gian_xem_giay = (tien_do.thoi_gian_xem_giay or 0) + data.thoi_gian_xem_giay
            tien_do.lan_xem_cuoi = now
            if tien_do.trang_thai == "CHUA_XEM":
                tien_do.trang_thai = "DANG_XEM"

        # Neu hoan thanh bai hoc
        if data.hoan_thanh and tien_do.trang_thai != "DA_HOAN_THANH":
            tien_do.trang_thai = "DA_HOAN_THANH"
            tien_do.ngay_hoan_thanh = now

        await self.db.flush()

        # Tinh lai phan_tram hoan thanh cua dang_ky
        await self._tinh_lai_phan_tram(dk, bh.khoa_hoc_id, user_uuid)

        await self.db.refresh(tien_do)
        return self._bai_hoc_to_dict(bh, tien_do)

    async def _tinh_lai_phan_tram(
        self, dk: DangKyKhoaHoc, khoa_hoc_id: uuid.UUID, cong_chuc_id: uuid.UUID
    ):
        """Tinh lai phan tram hoan thanh cho dang ky khoa hoc.

        Formula:
        - phan_tram = (bai_xong + bkt_dat) / (tong_bai + tong_bkt) * 100
        - HOAN_THANH khi: tat ca bai hoc xong VA tat ca BKT dat (hoac khong co BKT)
        """
        from lms_service.models.bai_kiem_tra import BaiKiemTra
        from lms_service.models.ket_qua_bai_kiem_tra import KetQuaBaiKiemTra

        # Dem tong bai hoc active
        total_result = await self.db.execute(
            select(func.count(BaiHoc.id)).where(
                BaiHoc.khoa_hoc_id == khoa_hoc_id,
                BaiHoc.is_active == True,  # noqa: E712
            )
        )
        tong_bai = total_result.scalar() or 0

        # Dem bai da hoan thanh
        done_result = await self.db.execute(
            select(func.count(TienDoBaiHoc.id))
            .join(BaiHoc, TienDoBaiHoc.bai_hoc_id == BaiHoc.id)
            .where(
                TienDoBaiHoc.cong_chuc_id == cong_chuc_id,
                BaiHoc.khoa_hoc_id == khoa_hoc_id,
                BaiHoc.is_active == True,  # noqa: E712
                TienDoBaiHoc.trang_thai == "DA_HOAN_THANH",
            )
        )
        bai_xong = done_result.scalar() or 0

        # Dem tong BKT active cua khoa
        bkt_count_r = await self.db.execute(
            select(func.count(BaiKiemTra.id)).where(
                BaiKiemTra.khoa_hoc_id == khoa_hoc_id,
                BaiKiemTra.is_active == True,  # noqa: E712
            )
        )
        tong_bkt = bkt_count_r.scalar() or 0

        # Dem BKT user da dat (distinct bai_kiem_tra_id co it nhat 1 lan dat_yeu_cau=True)
        bkt_dat = 0
        if tong_bkt > 0:
            bkt_ids_r = await self.db.execute(
                select(BaiKiemTra.id).where(
                    BaiKiemTra.khoa_hoc_id == khoa_hoc_id,
                    BaiKiemTra.is_active == True,  # noqa: E712
                )
            )
            bkt_ids = [row[0] for row in bkt_ids_r.all()]
            bkt_dat_r = await self.db.execute(
                select(func.count(func.distinct(KetQuaBaiKiemTra.bai_kiem_tra_id)))
                .where(
                    KetQuaBaiKiemTra.cong_chuc_id == cong_chuc_id,
                    KetQuaBaiKiemTra.bai_kiem_tra_id.in_(bkt_ids),
                    KetQuaBaiKiemTra.dat_yeu_cau == True,  # noqa: E712
                )
            )
            bkt_dat = bkt_dat_r.scalar() or 0

        # Tinh phan tram tong hop
        tong_items = tong_bai + tong_bkt
        if tong_items == 0:
            return

        done_items = bai_xong + bkt_dat
        phan_tram = Decimal(done_items) / Decimal(tong_items) * Decimal(100)
        dk.phan_tram_hoan_thanh = min(phan_tram, Decimal(100))

        # HOAN_THANH: tat ca bai hoc xong VA tat ca BKT dat (hoac khong co BKT)
        tat_ca_bai_xong = (tong_bai == 0 or bai_xong >= tong_bai)
        tat_ca_bkt_dat = (tong_bkt == 0 or bkt_dat >= tong_bkt)
        if tat_ca_bai_xong and tat_ca_bkt_dat:
            dk.trang_thai = "HOAN_THANH"
            dk.ngay_hoan_thanh = datetime.utcnow()
            await self.db.flush()
            # Tu dong cap chung chi
            from lms_service.services.chung_chi_service import ChungChiService
            cc_svc = ChungChiService(self.db)
            await cc_svc.tu_dong_cap_chung_chi(dk.id)

        await self.db.flush()

    # =========================================================================
    # 7. SAP XEP LAI BAI HOC
    # =========================================================================
    async def sap_xep(
        self, khoa_hoc_id: uuid.UUID, items: list[SapXepItem], user: TokenPayload
    ) -> None:
        """Sap xep lai thu tu bai hoc."""
        kh = await self._get_khoa_hoc(khoa_hoc_id)
        await self._check_gv_quyen(kh, user)

        for item in items:
            await self.db.execute(
                update(BaiHoc)
                .where(BaiHoc.id == item.bai_hoc_id, BaiHoc.khoa_hoc_id == khoa_hoc_id)
                .values(thu_tu=item.thu_tu)
            )
        await self.db.flush()
