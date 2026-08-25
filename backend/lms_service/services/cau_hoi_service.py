"""
lms_service/services/cau_hoi_service.py
=======================================
Business logic cho CRUD ngan hang cau hoi.
"""

import math
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.models.base import CongChucRef
from lms_service.models.cau_hoi import CauHoi
from lms_service.models.khoa_hoc import KhoaHoc
from lms_service.models.chuyen_de import ChuyenDe
from lms_service.models.bai_kiem_tra import BaiKiemTra
from lms_service.models.bai_kiem_tra_cau_hoi import BaiKiemTraCauHoi
from lms_service.models.linh_vuc import LinhVuc
from lms_service.schemas.cau_hoi import CauHoiCreate, CauHoiUpdate
from shared.auth import TokenPayload


class CauHoiService:
    """Service xu ly ngan hang cau hoi."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _is_manager(self, user: TokenPayload) -> bool:
        return user.vai_tro == "SUPER_ADMIN" or "QT_DAO_TAO" in (user.platform_roles or [])

    async def danh_sach(
        self,
        khoa_hoc_id: Optional[uuid.UUID] = None,
        chuyen_de_id: Optional[uuid.UUID] = None,
        bai_kiem_tra_id: Optional[uuid.UUID] = None,
        linh_vuc_id: Optional[uuid.UUID] = None,
        loai: Optional[str] = None,
        do_kho: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Danh sach cau hoi voi filter va pagination."""
        nt = CongChucRef.__table__.alias("nt")

        base_where = [CauHoi.is_active == True]  # noqa: E712
        if khoa_hoc_id:
            base_where.append(CauHoi.khoa_hoc_id == khoa_hoc_id)
        if chuyen_de_id:
            base_where.append(CauHoi.chuyen_de_id == chuyen_de_id)
        if bai_kiem_tra_id:
            base_where.append(CauHoi.bai_kiem_tra_id == bai_kiem_tra_id)
        if loai:
            base_where.append(CauHoi.loai == loai)
        if linh_vuc_id:
            base_where.append(CauHoi.linh_vuc_id == linh_vuc_id)
        if do_kho:
            base_where.append(CauHoi.do_kho == do_kho)

        count_stmt = select(func.count(CauHoi.id)).where(*base_where)
        total_result = await self.db.execute(count_stmt)
        total_items = total_result.scalar() or 0
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

        bkt_alias = BaiKiemTra.__table__.alias("bkt")
        lv_alias = LinhVuc.__table__.alias("lv")
        stmt = (
            select(
                CauHoi,
                KhoaHoc.ten_khoa_hoc.label("khoa_hoc_ten"),
                ChuyenDe.ten_chuyen_de.label("chuyen_de_ten"),
                bkt_alias.c.tieu_de.label("bai_kiem_tra_ten"),
                nt.c.ho_ten.label("nguoi_tao_ho_ten"),
                lv_alias.c.ten_linh_vuc.label("linh_vuc_ten"),
            )
            .outerjoin(KhoaHoc, CauHoi.khoa_hoc_id == KhoaHoc.id)
            .outerjoin(ChuyenDe, CauHoi.chuyen_de_id == ChuyenDe.id)
            .outerjoin(bkt_alias, CauHoi.bai_kiem_tra_id == bkt_alias.c.id)
            .outerjoin(nt, CauHoi.nguoi_tao_id == nt.c.id)
            .outerjoin(lv_alias, CauHoi.linh_vuc_id == lv_alias.c.id)
            .where(*base_where)
            .order_by(CauHoi.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        items = []
        for ch, kh_ten, cd_ten, bkt_ten, nt_ten, lv_ten in rows:
            items.append({
                "id": ch.id, "khoa_hoc_id": ch.khoa_hoc_id, "chuyen_de_id": ch.chuyen_de_id,
                "bai_kiem_tra_id": ch.bai_kiem_tra_id, "linh_vuc_id": ch.linh_vuc_id,
                "noi_dung": ch.noi_dung, "giai_thich": ch.giai_thich, "loai": ch.loai, "dap_an": ch.dap_an,
                "diem": ch.diem, "do_kho": ch.do_kho, "van_ban_lien_quan_ids": ch.van_ban_lien_quan_ids,
                "nguoi_tao_id": ch.nguoi_tao_id, "is_active": ch.is_active, "created_at": ch.created_at,
                "khoa_hoc_ten": kh_ten, "chuyen_de_ten": cd_ten, "bai_kiem_tra_ten": bkt_ten,
                "nguoi_tao_ho_ten": nt_ten, "linh_vuc_ten": lv_ten,
            })

        return {"items": items, "pagination": {"page": page, "page_size": page_size, "total_items": total_items, "total_pages": total_pages}}

    async def chi_tiet(self, id: uuid.UUID) -> CauHoi:
        result = await self.db.execute(select(CauHoi).where(CauHoi.id == id, CauHoi.is_active == True))  # noqa: E712
        ch = result.scalar_one_or_none()
        if ch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy câu hỏi"}})
        return ch

    async def tao_moi(self, data: CauHoiCreate, user: TokenPayload) -> CauHoi:
        if data.khoa_hoc_id:
            r = await self.db.execute(select(KhoaHoc.id).where(KhoaHoc.id == data.khoa_hoc_id))
            if r.scalar_one_or_none() is None:
                raise HTTPException(status_code=404, detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy khóa học"}})
        if data.chuyen_de_id:
            r = await self.db.execute(select(ChuyenDe.id).where(ChuyenDe.id == data.chuyen_de_id))
            if r.scalar_one_or_none() is None:
                raise HTTPException(status_code=404, detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy chuyên đề"}})

        ch = CauHoi(
            khoa_hoc_id=data.khoa_hoc_id, chuyen_de_id=data.chuyen_de_id,
            bai_kiem_tra_id=data.bai_kiem_tra_id, linh_vuc_id=data.linh_vuc_id,
            noi_dung=data.noi_dung, giai_thich=data.giai_thich,
            loai=data.loai, dap_an=data.dap_an,
            diem=data.diem, do_kho=data.do_kho, van_ban_lien_quan_ids=data.van_ban_lien_quan_ids,
            nguoi_tao_id=uuid.UUID(user.sub),
        )
        self.db.add(ch)
        await self.db.flush()
        await self.db.refresh(ch)

        # Tao junction record lien ket cau hoi voi bai kiem tra
        # Tinh thu_tu = so cau hoi hien tai + 1
        # BaiKiemTraCauHoi dung composite PK (bai_kiem_tra_id + cau_hoi_id),
        # KHONG co cot `id` — count(BaiKiemTraCauHoi.id) nem AttributeError va
        # lam POST /cau-hoi tra 500.
        count_r = await self.db.execute(
            select(func.count()).select_from(BaiKiemTraCauHoi).where(
                BaiKiemTraCauHoi.bai_kiem_tra_id == data.bai_kiem_tra_id
            )
        )
        thu_tu = (count_r.scalar() or 0) + 1

        link = BaiKiemTraCauHoi(
            bai_kiem_tra_id=data.bai_kiem_tra_id,
            cau_hoi_id=ch.id,
            thu_tu=thu_tu,
        )
        self.db.add(link)

        # Cap nhat so_cau_hoi cua bai_kiem_tra
        bkt_r = await self.db.execute(select(BaiKiemTra).where(BaiKiemTra.id == data.bai_kiem_tra_id))
        bkt = bkt_r.scalar_one_or_none()
        if bkt:
            bkt.so_cau_hoi = thu_tu

        await self.db.flush()
        return ch

    async def cap_nhat(self, id: uuid.UUID, data: CauHoiUpdate, user: TokenPayload) -> CauHoi:
        ch = await self.chi_tiet(id)
        if not self._is_manager(user) and str(ch.nguoi_tao_id) != user.sub:
            raise HTTPException(status_code=403, detail={"success": False, "error": {"code": "LMS_ERR_008", "message": "Bạn chỉ được sửa câu hỏi của mình"}})
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(ch, field, value)
        await self.db.flush()
        await self.db.refresh(ch)
        return ch

    async def xoa(self, id: uuid.UUID, user: TokenPayload) -> None:
        ch = await self.chi_tiet(id)
        # Kiem tra khong dang gan vao BKT nao
        link_count = await self.db.execute(select(func.count()).where(BaiKiemTraCauHoi.cau_hoi_id == id))
        if (link_count.scalar() or 0) > 0:
            raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_009", "message": "Không thể xóa câu hỏi đang gắn với bài kiểm tra"}})
        ch.is_active = False
        await self.db.flush()
