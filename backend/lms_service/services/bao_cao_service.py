"""
lms_service/services/bao_cao_service.py
=======================================
Business logic cho bao cao va dashboard.
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func, case, literal_column
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.models.base import CongChucRef, DonViRef
from lms_service.models.dang_ky_khoa_hoc import DangKyKhoaHoc
from lms_service.models.khoa_hoc import KhoaHoc
from lms_service.models.chung_chi import ChungChi
from lms_service.models.tien_do_bai_hoc import TienDoBaiHoc
from lms_service.models.bai_hoc import BaiHoc
from lms_service.models.ket_qua_bai_kiem_tra import KetQuaBaiKiemTra
from lms_service.models.bai_kiem_tra import BaiKiemTra
from lms_service.schemas.chung_chi import tinh_xep_loai
from shared.auth import TokenPayload

from lms_service.services.thong_bao_helper import gui_thong_bao
from lms_service.core.timezone import now_vn


class BaoCaoService:
    """Service xu ly bao cao va dashboard."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _is_manager(self, user: TokenPayload) -> bool:
        return user.vai_tro == "SUPER_ADMIN" or "QT_DAO_TAO" in (user.platform_roles or [])

    # =========================================================================
    # 1. BAO CAO CA NHAN
    # =========================================================================
    async def bao_cao_ca_nhan(self, user: TokenPayload) -> dict:
        """Bao cao ca nhan cua user hien tai."""
        user_uuid = uuid.UUID(user.sub)

        # a. Count dang_ky theo trang_thai
        status_r = await self.db.execute(
            select(
                DangKyKhoaHoc.trang_thai,
                func.count(DangKyKhoaHoc.id),
            )
            .where(DangKyKhoaHoc.cong_chuc_id == user_uuid)
            .group_by(DangKyKhoaHoc.trang_thai)
        )
        status_counts = {row[0]: row[1] for row in status_r.all()}
        tong = sum(status_counts.values())
        dang_hoc = status_counts.get("DANG_HOC", 0)
        hoan_thanh = status_counts.get("HOAN_THANH", 0)
        chua_bat_dau = status_counts.get("CHUA_BAT_DAU", 0)

        # b. Count chung chi
        cc_r = await self.db.execute(
            select(func.count(ChungChi.id)).where(ChungChi.cong_chuc_id == user_uuid)
        )
        tong_chung_chi = cc_r.scalar() or 0

        # c. Tong gio hoc
        gio_r = await self.db.execute(
            select(func.coalesce(func.sum(TienDoBaiHoc.thoi_gian_xem_giay), 0))
            .where(TienDoBaiHoc.cong_chuc_id == user_uuid)
        )
        tong_giay = gio_r.scalar() or 0
        tong_gio_hoc = tong_giay // 3600

        # d. 5 khoa hoc gan day
        recent_r = await self.db.execute(
            select(
                DangKyKhoaHoc.trang_thai,
                DangKyKhoaHoc.phan_tram_hoan_thanh,
                KhoaHoc.ten_khoa_hoc,
            )
            .join(KhoaHoc, DangKyKhoaHoc.khoa_hoc_id == KhoaHoc.id)
            .where(DangKyKhoaHoc.cong_chuc_id == user_uuid)
            .order_by(DangKyKhoaHoc.updated_at.desc())
            .limit(5)
        )
        khoa_gan_day = [
            {"ten": r[2], "trang_thai": r[0], "phan_tram": float(r[1] or 0)}
            for r in recent_r.all()
        ]

        # e. 3 chung chi gan day
        cc_recent_r = await self.db.execute(
            select(
                ChungChi.ma_chung_chi,
                ChungChi.diem_dat,
                ChungChi.ngay_cap,
                KhoaHoc.ten_khoa_hoc,
            )
            .join(KhoaHoc, ChungChi.khoa_hoc_id == KhoaHoc.id)
            .where(ChungChi.cong_chuc_id == user_uuid)
            .order_by(ChungChi.ngay_cap.desc())
            .limit(3)
        )
        chung_chi_gan_day = [
            {
                "ma": r[0], "ten_khoa": r[3],
                "xep_loai": tinh_xep_loai(r[1]) if r[1] else None,
                "ngay_cap": r[2].isoformat() if r[2] else None,
            }
            for r in cc_recent_r.all()
        ]

        return {
            "tong_khoa_da_dang_ky": tong,
            "khoa_dang_hoc": dang_hoc,
            "khoa_hoan_thanh": hoan_thanh,
            "khoa_chua_bat_dau": chua_bat_dau,
            "tong_chung_chi": tong_chung_chi,
            "tong_gio_hoc": tong_gio_hoc,
            "khoa_hoc_gan_day": khoa_gan_day,
            "chung_chi_gan_day": chung_chi_gan_day,
        }

    # =========================================================================
    # 2. BAO CAO DON VI
    # =========================================================================
    async def bao_cao_don_vi(self, don_vi_id: uuid.UUID, user: TokenPayload) -> dict:
        """Bao cao don vi. Lanh dao chi xem don vi minh."""
        # Auth check
        if not self._is_manager(user):
            if not user.is_lanh_dao:
                raise HTTPException(status_code=403, detail={"success": False, "error": {"code": "LMS_ERR_008", "message": "Không có quyền xem báo cáo đơn vị"}})
            if user.don_vi_id and uuid.UUID(user.don_vi_id) != don_vi_id:
                raise HTTPException(status_code=403, detail={"success": False, "error": {"code": "LMS_ERR_008", "message": "Lãnh đạo chỉ xem được đơn vị mình"}})

        cc = CongChucRef.__table__.alias("cc")
        dv = DonViRef.__table__.alias("dv")

        # Ten don vi
        dv_r = await self.db.execute(select(dv.c.ten_don_vi).where(dv.c.id == don_vi_id))
        ten_dv = dv_r.scalar() or ""

        # Tong CBCC active
        tong_cbcc_r = await self.db.execute(
            select(func.count(cc.c.id)).where(cc.c.don_vi_id == don_vi_id, cc.c.is_active == True)  # noqa: E712
        )
        tong_cbcc = tong_cbcc_r.scalar() or 0

        # CBCC co it nhat 1 dang_ky DANG_HOC
        dang_hoc_r = await self.db.execute(
            select(func.count(func.distinct(DangKyKhoaHoc.cong_chuc_id)))
            .join(cc, DangKyKhoaHoc.cong_chuc_id == cc.c.id)
            .where(cc.c.don_vi_id == don_vi_id, DangKyKhoaHoc.trang_thai == "DANG_HOC")
        )
        cbcc_dang_hoc = dang_hoc_r.scalar() or 0

        # CBCC hoan thanh it nhat 1 khoa
        ht_r = await self.db.execute(
            select(func.count(func.distinct(DangKyKhoaHoc.cong_chuc_id)))
            .join(cc, DangKyKhoaHoc.cong_chuc_id == cc.c.id)
            .where(cc.c.don_vi_id == don_vi_id, DangKyKhoaHoc.trang_thai == "HOAN_THANH")
        )
        cbcc_ht = ht_r.scalar() or 0

        # Tong dang ky + hoan thanh
        dk_r = await self.db.execute(
            select(
                func.count(DangKyKhoaHoc.id),
                func.count(case((DangKyKhoaHoc.trang_thai == "HOAN_THANH", DangKyKhoaHoc.id))),
            )
            .join(cc, DangKyKhoaHoc.cong_chuc_id == cc.c.id)
            .where(cc.c.don_vi_id == don_vi_id)
        )
        row = dk_r.one()
        tong_dk = row[0] or 0
        tong_ht = row[1] or 0
        ti_le = Decimal(tong_ht) / Decimal(tong_dk) * 100 if tong_dk > 0 else Decimal("0")

        # Top 3 khoa hoc nhieu nguoi dang ky
        top_r = await self.db.execute(
            select(
                KhoaHoc.ten_khoa_hoc,
                func.count(DangKyKhoaHoc.id).label("so_hv"),
                func.count(case((DangKyKhoaHoc.trang_thai == "HOAN_THANH", DangKyKhoaHoc.id))).label("so_ht"),
            )
            .join(DangKyKhoaHoc, KhoaHoc.id == DangKyKhoaHoc.khoa_hoc_id)
            .join(cc, DangKyKhoaHoc.cong_chuc_id == cc.c.id)
            .where(cc.c.don_vi_id == don_vi_id)
            .group_by(KhoaHoc.id, KhoaHoc.ten_khoa_hoc)
            .order_by(func.count(DangKyKhoaHoc.id).desc())
            .limit(3)
        )
        top_khoa = [
            {"ten": r[0], "so_hoc_vien": r[1], "ti_le_hoan_thanh": float(Decimal(r[2]) / Decimal(r[1]) * 100) if r[1] > 0 else 0}
            for r in top_r.all()
        ]

        return {
            "don_vi_id": don_vi_id,
            "ten_don_vi": ten_dv,
            "tong_cbcc": tong_cbcc,
            "cbcc_dang_hoc": cbcc_dang_hoc,
            "cbcc_hoan_thanh_it_nhat_1": cbcc_ht,
            "tong_dang_ky": tong_dk,
            "tong_hoan_thanh": tong_ht,
            "ti_le_hoan_thanh": ti_le,
            "top_khoa_hoc": top_khoa,
        }

    # =========================================================================
    # 3. BAO CAO KHOA HOC
    # =========================================================================
    async def bao_cao_khoa_hoc(self, khoa_hoc_id: uuid.UUID, user: TokenPayload) -> dict:
        """Bao cao 1 khoa hoc."""
        # Verify khoa hoc + quyen
        kh_r = await self.db.execute(select(KhoaHoc).where(KhoaHoc.id == khoa_hoc_id))
        kh = kh_r.scalar_one_or_none()
        if kh is None:
            raise HTTPException(status_code=404, detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy khóa học"}})
        if not self._is_manager(user):
            if "GIANG_VIEN" not in (user.platform_roles or []) or str(kh.giang_vien_id) != user.sub:
                raise HTTPException(status_code=403, detail={"success": False, "error": {"code": "LMS_ERR_008", "message": "Không có quyền xem báo cáo khóa này"}})

        # Count theo trang thai
        status_r = await self.db.execute(
            select(DangKyKhoaHoc.trang_thai, func.count(DangKyKhoaHoc.id))
            .where(DangKyKhoaHoc.khoa_hoc_id == khoa_hoc_id)
            .group_by(DangKyKhoaHoc.trang_thai)
        )
        phan_bo = {r[0]: r[1] for r in status_r.all()}
        tong_dk = sum(phan_bo.values())
        ht = phan_bo.get("HOAN_THANH", 0)
        ti_le = Decimal(ht) / Decimal(tong_dk) * 100 if tong_dk > 0 else Decimal("0")

        # Diem TB BKT
        diem_r = await self.db.execute(
            select(func.avg(KetQuaBaiKiemTra.diem))
            .join(BaiKiemTra, KetQuaBaiKiemTra.bai_kiem_tra_id == BaiKiemTra.id)
            .where(BaiKiemTra.khoa_hoc_id == khoa_hoc_id, KetQuaBaiKiemTra.dat_yeu_cau.isnot(None))
        )
        diem_tb = diem_r.scalar()

        return {
            "khoa_hoc_id": khoa_hoc_id,
            "ten_khoa_hoc": kh.ten_khoa_hoc,
            "ma_khoa_hoc": kh.ma_khoa_hoc,
            "tong_dang_ky": tong_dk,
            "dang_hoc": phan_bo.get("DANG_HOC", 0),
            "hoan_thanh": ht,
            "chua_bat_dau": phan_bo.get("CHUA_BAT_DAU", 0),
            "ti_le_hoan_thanh": ti_le,
            "diem_trung_binh_bkt": Decimal(str(round(diem_tb, 2))) if diem_tb else None,
            "phan_bo_trang_thai": phan_bo,
        }

    # =========================================================================
    # 4. DASHBOARD SUMMARY
    # =========================================================================
    async def dashboard_summary(self, user: TokenPayload) -> dict:
        """Dashboard summary cho widget frontend."""
        user_uuid = uuid.UUID(user.sub)
        now = now_vn()

        # Khoa dang hoc
        dh_r = await self.db.execute(
            select(func.count(DangKyKhoaHoc.id)).where(
                DangKyKhoaHoc.cong_chuc_id == user_uuid, DangKyKhoaHoc.trang_thai == "DANG_HOC"
            )
        )
        khoa_dang_hoc = dh_r.scalar() or 0

        # Khoa sap het han (7 ngay toi)
        het_han_r = await self.db.execute(
            select(
                DangKyKhoaHoc.han_hoan_thanh,
                KhoaHoc.ten_khoa_hoc,
                DangKyKhoaHoc.phan_tram_hoan_thanh,
            )
            .join(KhoaHoc, DangKyKhoaHoc.khoa_hoc_id == KhoaHoc.id)
            .where(
                DangKyKhoaHoc.cong_chuc_id == user_uuid,
                DangKyKhoaHoc.trang_thai.in_(["CHUA_BAT_DAU", "DANG_HOC"]),
                DangKyKhoaHoc.han_hoan_thanh.isnot(None),
                DangKyKhoaHoc.han_hoan_thanh <= (now + timedelta(days=7)).date(),
            )
        )
        sap_het_han = [
            {"ten": r[1], "han": r[0].isoformat() if r[0] else None, "phan_tram": float(r[2] or 0)}
            for r in het_han_r.all()
        ]

        # Bai kiem tra chua lam (khoa hoc da dang ky, BKT dang mo, user chua dat)
        from lms_service.models.bai_kiem_tra_cau_hoi import BaiKiemTraCauHoi
        # Subquery: BKT da dat cua user
        bkt_da_dat_sub = (
            select(KetQuaBaiKiemTra.bai_kiem_tra_id)
            .where(
                KetQuaBaiKiemTra.cong_chuc_id == user_uuid,
                KetQuaBaiKiemTra.dat_yeu_cau == True,  # noqa: E712
            )
            .distinct()
            .correlate_except(KetQuaBaiKiemTra)
            .subquery()
        )
        # BKT thuoc khoa hoc user da dang ky, dang active, chua dat
        bkt_r = await self.db.execute(
            select(
                BaiKiemTra.id,
                BaiKiemTra.tieu_de,
                BaiKiemTra.ngay_dong,
                BaiKiemTra.so_lan_lam_toi_da,
                KhoaHoc.ten_khoa_hoc,
                KhoaHoc.id.label("khoa_hoc_id"),
            )
            .join(KhoaHoc, BaiKiemTra.khoa_hoc_id == KhoaHoc.id)
            .join(DangKyKhoaHoc, DangKyKhoaHoc.khoa_hoc_id == KhoaHoc.id)
            .where(
                DangKyKhoaHoc.cong_chuc_id == user_uuid,
                DangKyKhoaHoc.trang_thai.in_(["CHUA_BAT_DAU", "DANG_HOC"]),
                BaiKiemTra.is_active == True,  # noqa: E712
                BaiKiemTra.id.notin_(select(bkt_da_dat_sub.c.bai_kiem_tra_id)),
            )
            .order_by(BaiKiemTra.ngay_dong.asc().nullslast())
        )
        bkt_chua_lam = []
        for row in bkt_r.all():
            ngay_dong = row[2]
            con_lai_ngay = (ngay_dong - now.date()).days if ngay_dong else None
            bkt_chua_lam.append({
                "id": str(row[0]),
                "tieu_de": row[1],
                "ngay_dong": ngay_dong.isoformat() if ngay_dong else None,
                "con_lai_ngay": con_lai_ngay,
                "ten_khoa_hoc": row[4],
                "khoa_hoc_id": str(row[5]),
                "khan_cap": con_lai_ngay is not None and con_lai_ngay <= 3,
            })

        # Chung chi moi (30 ngay)
        cc_r = await self.db.execute(
            select(ChungChi.ma_chung_chi, ChungChi.ngay_cap, KhoaHoc.ten_khoa_hoc)
            .join(KhoaHoc, ChungChi.khoa_hoc_id == KhoaHoc.id)
            .where(
                ChungChi.cong_chuc_id == user_uuid,
                ChungChi.ngay_cap >= now - timedelta(days=30),
            )
            .order_by(ChungChi.ngay_cap.desc())
        )
        chung_chi_moi = [
            {"ma": r[0], "ngay_cap": r[1].isoformat() if r[1] else None, "ten_khoa": r[2]}
            for r in cc_r.all()
        ]

        # Fire-and-forget: gui thong bao cho BKT khan cap (con <= 3 ngay)
        for bkt_item in bkt_chua_lam:
            if bkt_item.get("khan_cap"):
                con_lai = bkt_item["con_lai_ngay"]
                lbl = f"còn {con_lai} ngày" if con_lai and con_lai > 0 else "hết hạn hôm nay"
                await gui_thong_bao(
                    nguoi_nhan_id=user_uuid,
                    tieu_de=f"Bài kiểm tra sắp hết hạn: {bkt_item['tieu_de']}",
                    noi_dung=f"Bài kiểm tra \"{bkt_item['tieu_de']}\" ({lbl}). Vui lòng hoàn thành sớm.",
                    muc_do="KHAN" if (con_lai is not None and con_lai <= 1) else "QUAN_TRONG",
                    link_url=f"/dao-tao/khoa-hoc/{bkt_item['khoa_hoc_id']}",
                    doi_tuong_type="BAI_KIEM_TRA",
                    doi_tuong_id=uuid.UUID(bkt_item["id"]),
                )

        return {
            "khoa_dang_hoc": khoa_dang_hoc,
            "khoa_sap_het_han": sap_het_han,
            "bkt_chua_lam": bkt_chua_lam,
            "chung_chi_moi": chung_chi_moi,
        }
