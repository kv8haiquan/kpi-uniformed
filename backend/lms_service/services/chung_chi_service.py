"""
lms_service/services/chung_chi_service.py
=========================================
Business logic cho chung chi + khao sat.
Bao gom helper tu_dong_cap_chung_chi duoc goi tu bai_hoc_service va bai_kiem_tra_service.
"""

import logging
import math
import os
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.config import settings
from lms_service.models.base import CongChucRef, DonViRef
from lms_service.models.chung_chi import ChungChi
from lms_service.models.khao_sat import KhaoSat
from lms_service.models.khoa_hoc import KhoaHoc
from lms_service.models.dang_ky_khoa_hoc import DangKyKhoaHoc
from lms_service.models.ket_qua_bai_kiem_tra import KetQuaBaiKiemTra
from lms_service.models.bai_kiem_tra import BaiKiemTra
from lms_service.schemas.chung_chi import tinh_xep_loai, KhaoSatCreate
from lms_service.services.chung_chi_pdf import generate_certificate_pdf
from lms_service.services.thong_bao_helper import gui_thong_bao
from shared.auth import TokenPayload
from lms_service.core.timezone import now_vn

logger = logging.getLogger(__name__)


class ChungChiService:
    """Service xu ly chung chi va khao sat."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _is_manager(self, user: TokenPayload) -> bool:
        return user.vai_tro == "SUPER_ADMIN" or "QT_DAO_TAO" in (user.platform_roles or [])

    # =========================================================================
    # 1. CHUNG CHI CUA TOI
    # =========================================================================
    async def chung_chi_cua_toi(
        self, user: TokenPayload, page: int = 1, page_size: int = 20
    ) -> dict:
        user_uuid = uuid.UUID(user.sub)

        count_r = await self.db.execute(
            select(func.count(ChungChi.id)).where(ChungChi.cong_chuc_id == user_uuid)
        )
        total_items = count_r.scalar() or 0
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

        stmt = (
            select(
                ChungChi,
                KhoaHoc.ten_khoa_hoc.label("khoa_hoc_ten"),
                KhoaHoc.ma_khoa_hoc.label("khoa_hoc_ma"),
            )
            .join(KhoaHoc, ChungChi.khoa_hoc_id == KhoaHoc.id)
            .where(ChungChi.cong_chuc_id == user_uuid)
            .order_by(ChungChi.ngay_cap.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        items = []
        for cc, kh_ten, kh_ma in rows:
            xep_loai = tinh_xep_loai(cc.diem_dat) if cc.diem_dat is not None else None
            items.append({
                "id": cc.id, "ma_chung_chi": cc.ma_chung_chi,
                "cong_chuc_id": cc.cong_chuc_id, "khoa_hoc_id": cc.khoa_hoc_id,
                "ten_chung_chi": cc.ten_chung_chi, "diem_dat": cc.diem_dat,
                "ngay_cap": cc.ngay_cap, "nguoi_cap_id": cc.nguoi_cap_id,
                "file_url": cc.file_url,
                "khoa_hoc_ten": kh_ten, "khoa_hoc_ma": kh_ma,
                "ho_ten": None, "ma_cc": None, "xep_loai": xep_loai,
            })

        return {"items": items, "pagination": {"page": page, "page_size": page_size, "total_items": total_items, "total_pages": total_pages}}

    # =========================================================================
    # 2. XAC MINH CHUNG CHI (PUBLIC)
    # =========================================================================
    async def xac_minh(self, ma_chung_chi: str) -> dict:
        cc_ref = CongChucRef.__table__.alias("cc")
        stmt = (
            select(
                ChungChi,
                KhoaHoc.ten_khoa_hoc.label("khoa_hoc_ten"),
                KhoaHoc.ma_khoa_hoc.label("khoa_hoc_ma"),
                cc_ref.c.ho_ten.label("ho_ten"),
                cc_ref.c.ma_cc.label("ma_cc"),
            )
            .join(KhoaHoc, ChungChi.khoa_hoc_id == KhoaHoc.id)
            .join(cc_ref, ChungChi.cong_chuc_id == cc_ref.c.id)
            .where(ChungChi.ma_chung_chi == ma_chung_chi)
        )
        result = await self.db.execute(stmt)
        row = result.one_or_none()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": {"code": "LMS_ERR_020", "message": "Mã chứng chỉ không hợp lệ"}},
            )

        cc, kh_ten, kh_ma, ho_ten, ma_cc = row
        xep_loai = tinh_xep_loai(cc.diem_dat) if cc.diem_dat is not None else None
        return {
            "id": cc.id, "ma_chung_chi": cc.ma_chung_chi,
            "cong_chuc_id": cc.cong_chuc_id, "khoa_hoc_id": cc.khoa_hoc_id,
            "ten_chung_chi": cc.ten_chung_chi, "diem_dat": cc.diem_dat,
            "ngay_cap": cc.ngay_cap, "nguoi_cap_id": cc.nguoi_cap_id,
            "file_url": cc.file_url,
            "khoa_hoc_ten": kh_ten, "khoa_hoc_ma": kh_ma,
            "ho_ten": ho_ten, "ma_cc": ma_cc, "xep_loai": xep_loai,
        }

    # =========================================================================
    # 3. TAI CHUNG CHI (PDF)
    # =========================================================================
    async def tai_chung_chi(self, chung_chi_id: uuid.UUID, user: TokenPayload) -> tuple[bytes, str]:
        """Tra ve (pdf_bytes, filename). Sinh lai PDF neu file khong ton tai."""
        result = await self.db.execute(select(ChungChi).where(ChungChi.id == chung_chi_id))
        cc = result.scalar_one_or_none()
        if cc is None:
            raise HTTPException(status_code=404, detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy chứng chỉ"}})
        if cc.cong_chuc_id != uuid.UUID(user.sub) and not self._is_manager(user):
            raise HTTPException(status_code=403, detail={"success": False, "error": {"code": "LMS_ERR_008", "message": "Không có quyền tải chứng chỉ này"}})

        # Thu doc file tu disk
        pdf_bytes: Optional[bytes] = None
        if cc.file_url:
            # file_url co dang "/uploads/lms/chung-chi/{year}/{ma}.pdf"
            rel = cc.file_url.replace("/uploads/lms/", "", 1)
            full_path = os.path.join(settings.upload_dir, rel)
            if os.path.exists(full_path):
                with open(full_path, "rb") as f:
                    pdf_bytes = f.read()

        # Neu khong co file, sinh lai
        if pdf_bytes is None:
            cc_table = CongChucRef.__table__
            dv_table = DonViRef.__table__
            info_r = await self.db.execute(
                select(cc_table.c.ho_ten, cc_table.c.ma_cc, dv_table.c.ten_don_vi, KhoaHoc.ten_khoa_hoc)
                .outerjoin(dv_table, cc_table.c.don_vi_id == dv_table.c.id)
                .select_from(cc_table)
                .join(KhoaHoc, KhoaHoc.id == cc.khoa_hoc_id)
                .where(cc_table.c.id == cc.cong_chuc_id)
            )
            row = info_r.first()
            pdf_bytes = generate_certificate_pdf(
                ma_chung_chi=cc.ma_chung_chi,
                ho_ten=row.ho_ten if row else "",
                ma_cc=row.ma_cc if row else "",
                ten_khoa_hoc=row.ten_khoa_hoc if row else "",
                diem_dat=cc.diem_dat or Decimal("0"),
                ngay_cap=cc.ngay_cap,
                don_vi=row.ten_don_vi if row else None,
            )

        return pdf_bytes, f"chung-chi-{cc.ma_chung_chi}.pdf"

    # =========================================================================
    # 4. TU DONG CAP CHUNG CHI (helper — goi tu service khac)
    # =========================================================================
    async def tu_dong_cap_chung_chi(self, dang_ky_id: uuid.UUID) -> Optional[ChungChi]:
        """Tu dong cap chung chi khi hoan thanh khoa hoc."""
        dk_r = await self.db.execute(select(DangKyKhoaHoc).where(DangKyKhoaHoc.id == dang_ky_id))
        dk = dk_r.scalar_one_or_none()
        if dk is None or dk.trang_thai != "HOAN_THANH":
            return None

        # Kiem tra da co chung chi chua
        existing_r = await self.db.execute(
            select(ChungChi).where(ChungChi.cong_chuc_id == dk.cong_chuc_id, ChungChi.khoa_hoc_id == dk.khoa_hoc_id)
        )
        if existing_r.scalar_one_or_none() is not None:
            return None

        # Tinh diem tong ket
        # Kiem tra khoa co BKT khong
        bkt_count_r = await self.db.execute(
            select(func.count(BaiKiemTra.id)).where(BaiKiemTra.khoa_hoc_id == dk.khoa_hoc_id, BaiKiemTra.is_active == True)  # noqa: E712
        )
        has_bkt = (bkt_count_r.scalar() or 0) > 0

        diem_tong_ket = Decimal("100")
        if has_bkt:
            # Lay diem cao nhat tu ket qua BKT dat
            best_r = await self.db.execute(
                select(func.max(KetQuaBaiKiemTra.diem))
                .join(BaiKiemTra, KetQuaBaiKiemTra.bai_kiem_tra_id == BaiKiemTra.id)
                .where(
                    KetQuaBaiKiemTra.cong_chuc_id == dk.cong_chuc_id,
                    BaiKiemTra.khoa_hoc_id == dk.khoa_hoc_id,
                    KetQuaBaiKiemTra.dat_yeu_cau == True,  # noqa: E712
                )
            )
            best_diem = best_r.scalar()
            if best_diem is not None:
                diem_tong_ket = best_diem

        # Lay ten khoa hoc
        kh_r = await self.db.execute(select(KhoaHoc.ten_khoa_hoc).where(KhoaHoc.id == dk.khoa_hoc_id))
        ten_kh = kh_r.scalar() or ""

        # Lay thong tin cong chuc (ho ten + don vi)
        cc_table = CongChucRef.__table__
        dv_table = DonViRef.__table__
        cc_info_r = await self.db.execute(
            select(cc_table.c.ho_ten, cc_table.c.ma_cc, dv_table.c.ten_don_vi)
            .outerjoin(dv_table, cc_table.c.don_vi_id == dv_table.c.id)
            .where(cc_table.c.id == dk.cong_chuc_id)
        )
        cc_row = cc_info_r.first()
        ho_ten = cc_row.ho_ten if cc_row else ""
        ma_cc = cc_row.ma_cc if cc_row else ""
        don_vi_ten = cc_row.ten_don_vi if cc_row else None

        # Sinh ma chung chi: CC-{year}-{seq:06d}
        ngay_cap = now_vn()
        year = ngay_cap.year
        prefix = f"CC-{year}-"
        seq_r = await self.db.execute(
            select(func.count(ChungChi.id)).where(ChungChi.ma_chung_chi.like(f"{prefix}%"))
        )
        seq = (seq_r.scalar() or 0) + 1
        ma_chung_chi = f"{prefix}{seq:06d}"

        # Sinh PDF + luu file (fire-and-forget: loi khong anh huong cap chung chi)
        file_url = None
        try:
            pdf_bytes = generate_certificate_pdf(
                ma_chung_chi=ma_chung_chi,
                ho_ten=ho_ten,
                ma_cc=ma_cc,
                ten_khoa_hoc=ten_kh,
                diem_dat=diem_tong_ket,
                ngay_cap=ngay_cap,
                don_vi=don_vi_ten,
            )
            # Luu vao uploads/lms/chung-chi/{year}/{ma_chung_chi}.pdf
            rel_path = f"chung-chi/{year}/{ma_chung_chi}.pdf"
            full_path = os.path.join(settings.upload_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(pdf_bytes)
            file_url = f"/uploads/lms/{rel_path}"
        except Exception as e:
            logger.warning("Sinh PDF chung chi that bai: %s", e)

        chung_chi = ChungChi(
            cong_chuc_id=dk.cong_chuc_id,
            khoa_hoc_id=dk.khoa_hoc_id,
            ma_chung_chi=ma_chung_chi,
            ten_chung_chi=f"Chứng nhận hoàn thành: {ten_kh}",
            diem_dat=diem_tong_ket,
            ngay_cap=ngay_cap,
            file_url=file_url,
        )
        self.db.add(chung_chi)
        await self.db.flush()
        await self.db.refresh(chung_chi)

        # Gui thong bao (fire-and-forget)
        xep_loai = tinh_xep_loai(diem_tong_ket) or ""
        await gui_thong_bao(
            nguoi_nhan_id=dk.cong_chuc_id,
            tieu_de=f"Bạn đã được cấp chứng chỉ: {ten_kh}",
            noi_dung=f"Chúc mừng! Bạn đã hoàn thành khóa học \"{ten_kh}\" với điểm {float(diem_tong_ket):.2f} — xếp loại {xep_loai}. Mã chứng chỉ: {ma_chung_chi}",
            muc_do="QUAN_TRONG",
            link_url="/dao-tao/chung-chi",
            doi_tuong_type="CHUNG_CHI",
            doi_tuong_id=chung_chi.id,
        )

        return chung_chi

    # =========================================================================
    # 5. GUI KHAO SAT
    # =========================================================================
    async def gui_khao_sat(self, data: KhaoSatCreate, user: TokenPayload) -> KhaoSat:
        user_uuid = uuid.UUID(user.sub)

        # Verify da hoan thanh khoa
        dk_r = await self.db.execute(
            select(DangKyKhoaHoc).where(
                DangKyKhoaHoc.cong_chuc_id == user_uuid,
                DangKyKhoaHoc.khoa_hoc_id == data.khoa_hoc_id,
            )
        )
        dk = dk_r.scalar_one_or_none()
        if dk is None or dk.trang_thai != "HOAN_THANH":
            raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_010", "message": "Bạn chưa hoàn thành khóa học này"}})

        # Check trung
        ks_r = await self.db.execute(
            select(KhaoSat).where(KhaoSat.cong_chuc_id == user_uuid, KhaoSat.khoa_hoc_id == data.khoa_hoc_id)
        )
        if ks_r.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail={"success": False, "error": {"code": "LMS_ERR_003", "message": "Bạn đã khảo sát khóa này rồi"}})

        ks = KhaoSat(
            khoa_hoc_id=data.khoa_hoc_id,
            cong_chuc_id=user_uuid,
            noi_dung=data.noi_dung,
        )
        self.db.add(ks)
        await self.db.flush()
        await self.db.refresh(ks)
        return ks

    # =========================================================================
    # 6. THONG KE KHAO SAT
    # =========================================================================
    async def thong_ke_khao_sat(self, khoa_hoc_id: uuid.UUID, user: TokenPayload) -> dict:
        # Auth: giang vien khoa minh hoac QT
        if not self._is_manager(user):
            kh_r = await self.db.execute(select(KhoaHoc).where(KhoaHoc.id == khoa_hoc_id))
            kh = kh_r.scalar_one_or_none()
            if kh is None or (str(kh.giang_vien_id) != user.sub and "GIANG_VIEN" not in (user.platform_roles or [])):
                raise HTTPException(status_code=403, detail={"success": False, "error": {"code": "LMS_ERR_008", "message": "Không có quyền xem thống kê"}})

        count_r = await self.db.execute(
            select(func.count(KhaoSat.id)).where(KhaoSat.khoa_hoc_id == khoa_hoc_id)
        )
        tong = count_r.scalar() or 0

        # Lay tat ca noi_dung de tong hop
        ks_r = await self.db.execute(
            select(KhaoSat.noi_dung).where(KhaoSat.khoa_hoc_id == khoa_hoc_id)
        )
        noi_dungs = ks_r.scalars().all()

        # Tong hop: dem so lan xuat hien moi gia tri
        phan_bo = {}
        for nd in noi_dungs:
            if isinstance(nd, dict):
                for k, v in nd.items():
                    if k not in phan_bo:
                        phan_bo[k] = {}
                    sv = str(v)
                    phan_bo[k][sv] = phan_bo[k].get(sv, 0) + 1

        return {"khoa_hoc_id": khoa_hoc_id, "tong_khao_sat": tong, "phan_bo": phan_bo}
