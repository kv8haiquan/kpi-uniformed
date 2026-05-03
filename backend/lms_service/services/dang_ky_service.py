"""
lms_service/services/dang_ky_service.py
=======================================
Business logic cho dang ky / giao khoa hoc.
"""

import math
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.models.base import CongChucRef, DonViRef
from lms_service.models.khoa_hoc import KhoaHoc
from lms_service.models.dang_ky_khoa_hoc import DangKyKhoaHoc
from lms_service.schemas.dang_ky import GiaoBaiRequest
from lms_service.services.thong_bao_helper import gui_thong_bao_bulk
from shared.auth import TokenPayload


class DangKyService:
    """Service xu ly dang ky va giao khoa hoc."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # HELPERS
    # =========================================================================
    async def _get_khoa_hoc_published(self, khoa_hoc_id: uuid.UUID) -> KhoaHoc:
        """Lay khoa hoc da xuat ban."""
        result = await self.db.execute(
            select(KhoaHoc).where(KhoaHoc.id == khoa_hoc_id)
        )
        kh = result.scalar_one_or_none()
        if kh is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy khóa học"}},
            )
        if kh.trang_thai != "DA_XUAT_BAN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "LMS_ERR_002", "message": "Khóa học chưa xuất bản"}},
            )
        return kh

    async def _check_existing(self, cong_chuc_id: uuid.UUID, khoa_hoc_id: uuid.UUID) -> Optional[DangKyKhoaHoc]:
        result = await self.db.execute(
            select(DangKyKhoaHoc).where(
                DangKyKhoaHoc.cong_chuc_id == cong_chuc_id,
                DangKyKhoaHoc.khoa_hoc_id == khoa_hoc_id,
            )
        )
        return result.scalar_one_or_none()

    def _is_manager(self, user: TokenPayload) -> bool:
        return (
            user.vai_tro == "SUPER_ADMIN"
            or "QT_DAO_TAO" in (user.platform_roles or [])
        )

    # =========================================================================
    # 1. DANG KY TU NGUYEN
    # =========================================================================
    async def dang_ky_tu_nguyen(
        self, khoa_hoc_id: uuid.UUID, user: TokenPayload
    ) -> DangKyKhoaHoc:
        """CBCC tu dang ky khoa hoc."""
        kh = await self._get_khoa_hoc_published(khoa_hoc_id)
        user_uuid = uuid.UUID(user.sub)

        # Check trung
        existing = await self._check_existing(user_uuid, khoa_hoc_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"success": False, "error": {"code": "LMS_ERR_003", "message": "Đã đăng ký khóa học này rồi"}},
            )

        # Kiem tra dieu kien tien quyet
        tien_quyet = kh.dieu_kien_tien_quyet
        if tien_quyet and isinstance(tien_quyet, list) and len(tien_quyet) > 0:
            chua_hoan_thanh = []
            for kh_tq_id in tien_quyet:
                kh_tq_uuid = uuid.UUID(str(kh_tq_id)) if not isinstance(kh_tq_id, uuid.UUID) else kh_tq_id
                dk_tq = await self._check_existing(user_uuid, kh_tq_uuid)
                if dk_tq is None or dk_tq.trang_thai != "HOAN_THANH":
                    # Lay ten khoa tien quyet
                    r = await self.db.execute(
                        select(KhoaHoc.ten_khoa_hoc).where(KhoaHoc.id == kh_tq_uuid)
                    )
                    ten = r.scalar() or str(kh_tq_uuid)
                    chua_hoan_thanh.append(ten)

            if chua_hoan_thanh:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "error": {
                            "code": "LMS_ERR_004",
                            "message": f"Chưa hoàn thành khóa tiên quyết: {', '.join(chua_hoan_thanh)}",
                        },
                    },
                )

        dk = DangKyKhoaHoc(
            cong_chuc_id=user_uuid,
            khoa_hoc_id=khoa_hoc_id,
            loai_dang_ky="TU_NGUYEN",
            trang_thai="CHO_PHE_DUYET",
        )
        self.db.add(dk)
        await self.db.flush()
        await self.db.refresh(dk)

        # Gui thong bao cho nguoi co quyen phe duyet
        from lms_service.services.thong_bao_helper import gui_thong_bao_bulk
        notify_ids = []
        if kh.giang_vien_id:
            notify_ids.append(kh.giang_vien_id)
        if notify_ids:
            cc_r = await self.db.execute(
                select(CongChucRef.ho_ten).where(CongChucRef.id == user_uuid)
            )
            ho_ten = cc_r.scalar() or "Học viên"
            await gui_thong_bao_bulk(
                nguoi_nhan_ids=notify_ids,
                tieu_de=f"Yêu cầu phê duyệt: {ho_ten} đăng ký khóa {kh.ten_khoa_hoc}",
                noi_dung=f"{ho_ten} đăng ký khóa học \"{kh.ten_khoa_hoc}\". Vui lòng phê duyệt.",
                muc_do="QUAN_TRONG",
                # Link thẳng vào tab "Học viên" của khóa — nơi GV duyệt/từ chối
                link_url=f"/dao-tao/khoa-hoc/{khoa_hoc_id}?tab=hoc-vien",
                doi_tuong_type="KHOA_HOC",
                doi_tuong_id=khoa_hoc_id,
            )

        return dk

    # =========================================================================
    # 2. GIAO BAI BAT BUOC
    # =========================================================================
    async def giao_bai(
        self, khoa_hoc_id: uuid.UUID, data: GiaoBaiRequest, user: TokenPayload
    ) -> dict:
        """Giao khoa hoc bat buoc cho danh sach CBCC hoac don vi."""
        kh = await self._get_khoa_hoc_published(khoa_hoc_id)
        user_uuid = uuid.UUID(user.sub)

        # Thu thap danh sach cong_chuc_ids
        target_ids: set[uuid.UUID] = set()

        if data.cong_chuc_ids:
            target_ids.update(data.cong_chuc_ids)

        if data.don_vi_ids:
            # SELECT cong_chuc active trong cac don vi
            cc_result = await self.db.execute(
                select(CongChucRef.id).where(
                    CongChucRef.don_vi_id.in_(data.don_vi_ids),
                    CongChucRef.is_active == True,  # noqa: E712
                )
            )
            for row in cc_result.scalars().all():
                target_ids.add(row)

        if not target_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy CBCC để giao"}},
            )

        # Lanh dao: chi giao cho CBCC trong don vi minh
        if not self._is_manager(user) and user.is_lanh_dao:
            user_don_vi = uuid.UUID(user.don_vi_id) if user.don_vi_id else None
            if user_don_vi:
                cc_check = await self.db.execute(
                    select(CongChucRef.id, CongChucRef.don_vi_id).where(
                        CongChucRef.id.in_(target_ids)
                    )
                )
                for cc_id, dv_id in cc_check.all():
                    if dv_id != user_don_vi:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail={
                                "success": False,
                                "error": {"code": "LMS_ERR_008", "message": "Lãnh đạo chỉ được giao bài cho CBCC thuộc đơn vị mình"},
                            },
                        )

        # Giao tung nguoi
        da_giao = 0
        da_co = 0
        newly_assigned_ids = []  # Collect IDs of newly assigned users
        for cc_id in target_ids:
            existing = await self._check_existing(cc_id, khoa_hoc_id)
            if existing:
                da_co += 1
                continue

            dk = DangKyKhoaHoc(
                cong_chuc_id=cc_id,
                khoa_hoc_id=khoa_hoc_id,
                loai_dang_ky=data.loai_dang_ky,
                trang_thai="CHUA_BAT_DAU",
                nguoi_giao_id=user_uuid,
                han_hoan_thanh=data.han_hoan_thanh,
            )
            self.db.add(dk)
            da_giao += 1
            newly_assigned_ids.append(cc_id)  # Track newly assigned

        await self.db.flush()

        # Gui thong bao cho CBCC duoc giao moi
        if newly_assigned_ids:
            han_text = f" (hạn: {data.han_hoan_thanh.strftime('%d/%m/%Y')})" if data.han_hoan_thanh else ""
            await gui_thong_bao_bulk(
                nguoi_nhan_ids=newly_assigned_ids,
                tieu_de=f"Bạn được giao khóa học: {kh.ten_khoa_hoc}",
                noi_dung=f"Bạn được giao tham gia khóa học \"{kh.ten_khoa_hoc}\"{han_text}. Vui lòng bắt đầu học sớm.",
                muc_do="QUAN_TRONG",
                link_url=f"/dao-tao/khoa-hoc/{khoa_hoc_id}",
                doi_tuong_type="KHOA_HOC",
                doi_tuong_id=khoa_hoc_id,
            )

        return {"da_giao": da_giao, "da_co": da_co, "tong": da_giao + da_co}

    # =========================================================================
    # 3. KHOA HOC CUA TOI
    # =========================================================================
    async def khoa_hoc_cua_toi(
        self,
        user: TokenPayload,
        page: int = 1,
        page_size: int = 20,
        trang_thai: Optional[str] = None,
    ) -> dict:
        """Danh sach khoa da dang ky cua user hien tai."""
        user_uuid = uuid.UUID(user.sub)
        gv = CongChucRef.__table__.alias("gv")

        base_where = [DangKyKhoaHoc.cong_chuc_id == user_uuid]
        if trang_thai:
            base_where.append(DangKyKhoaHoc.trang_thai == trang_thai)

        # Count
        count_stmt = select(func.count(DangKyKhoaHoc.id)).where(*base_where)
        total_result = await self.db.execute(count_stmt)
        total_items = total_result.scalar() or 0
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

        # Data
        stmt = (
            select(
                DangKyKhoaHoc,
                KhoaHoc.ten_khoa_hoc.label("khoa_hoc_ten"),
                KhoaHoc.ma_khoa_hoc.label("khoa_hoc_ma"),
                KhoaHoc.loai.label("khoa_hoc_loai"),
                gv.c.ho_ten.label("giang_vien_ho_ten"),
            )
            .join(KhoaHoc, DangKyKhoaHoc.khoa_hoc_id == KhoaHoc.id)
            .outerjoin(gv, KhoaHoc.giang_vien_id == gv.c.id)
            .where(*base_where)
            .order_by(DangKyKhoaHoc.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        items = []
        for dk, khoa_hoc_ten, khoa_hoc_ma, khoa_hoc_loai, gv_ho_ten in rows:
            items.append({
                "id": dk.id,
                "cong_chuc_id": dk.cong_chuc_id,
                "khoa_hoc_id": dk.khoa_hoc_id,
                "loai_dang_ky": dk.loai_dang_ky,
                "trang_thai": dk.trang_thai,
                "phan_tram_hoan_thanh": dk.phan_tram_hoan_thanh,
                "han_hoan_thanh": dk.han_hoan_thanh,
                "ngay_bat_dau_hoc": dk.ngay_bat_dau_hoc,
                "ngay_hoan_thanh": dk.ngay_hoan_thanh,
                "diem_cao_nhat": dk.diem_cao_nhat,
                "created_at": dk.created_at,
                "khoa_hoc_ten": khoa_hoc_ten,
                "khoa_hoc_ma": khoa_hoc_ma,
                "khoa_hoc_loai": khoa_hoc_loai,
                "giang_vien_ho_ten": gv_ho_ten,
            })

        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
            },
        }

    # =========================================================================
    # 4. DANH SACH HOC VIEN cua 1 khoa hoc
    # =========================================================================
    async def danh_sach_hoc_vien(
        self,
        khoa_hoc_id: uuid.UUID,
        user: TokenPayload,
        page: int = 1,
        page_size: int = 20,
        trang_thai: Optional[str] = None,
        don_vi_id: Optional[uuid.UUID] = None,
    ) -> dict:
        """Danh sach hoc vien cua khoa hoc."""
        # Auth check: GIANG_VIEN chi xem khoa minh
        kh_result = await self.db.execute(
            select(KhoaHoc).where(KhoaHoc.id == khoa_hoc_id)
        )
        kh = kh_result.scalar_one_or_none()
        if kh is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy khóa học"}},
            )

        if not self._is_manager(user):
            is_gv = "GIANG_VIEN" in (user.platform_roles or [])
            if not (is_gv and str(kh.giang_vien_id) == user.sub):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"success": False, "error": {"code": "LMS_ERR_008", "message": "Không có quyền xem danh sách học viên"}},
                )

        cc = CongChucRef.__table__.alias("cc")
        dv = DonViRef.__table__.alias("dv")

        base_where = [DangKyKhoaHoc.khoa_hoc_id == khoa_hoc_id, DangKyKhoaHoc.trang_thai != "BI_LOAI"]
        if trang_thai:
            base_where.append(DangKyKhoaHoc.trang_thai == trang_thai)
        if don_vi_id:
            base_where.append(cc.c.don_vi_id == don_vi_id)

        # Count
        count_stmt = (
            select(func.count(DangKyKhoaHoc.id))
            .join(cc, DangKyKhoaHoc.cong_chuc_id == cc.c.id)
            .where(*base_where)
        )
        total_result = await self.db.execute(count_stmt)
        total_items = total_result.scalar() or 0
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

        # Data
        stmt = (
            select(
                DangKyKhoaHoc,
                cc.c.ho_ten.label("ho_ten"),
                cc.c.ma_cc.label("ma_cc"),
                dv.c.ten_don_vi.label("don_vi_ten"),
            )
            .join(cc, DangKyKhoaHoc.cong_chuc_id == cc.c.id)
            .outerjoin(dv, cc.c.don_vi_id == dv.c.id)
            .where(*base_where)
            .order_by(cc.c.ho_ten.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        items = []
        for dk, ho_ten, ma_cc, don_vi_ten in rows:
            items.append({
                "dang_ky_id": dk.id,
                "cong_chuc_id": dk.cong_chuc_id,
                "ho_ten": ho_ten,
                "ma_cc": ma_cc,
                "don_vi_ten": don_vi_ten,
                "trang_thai": dk.trang_thai,
                "phan_tram_hoan_thanh": dk.phan_tram_hoan_thanh,
                "loai_dang_ky": dk.loai_dang_ky,
                "ngay_dang_ky": dk.created_at,
                "ngay_bat_dau_hoc": dk.ngay_bat_dau_hoc,
                "ngay_hoan_thanh": dk.ngay_hoan_thanh,
            })

        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
            },
        }

    # =========================================================================
    # 5. HUY DANG KY
    # =========================================================================
    async def huy_dang_ky(
        self, khoa_hoc_id: uuid.UUID, user: TokenPayload
    ) -> None:
        """Huy dang ky. Chi cho TU_NGUYEN + CHUA_BAT_DAU."""
        user_uuid = uuid.UUID(user.sub)
        dk = await self._check_existing(user_uuid, khoa_hoc_id)

        if dk is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Chưa đăng ký khóa học này"}},
            )

        if dk.loai_dang_ky != "TU_NGUYEN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "LMS_ERR_009", "message": "Không thể hủy đăng ký bắt buộc"}},
            )

        if dk.trang_thai not in ["CHUA_BAT_DAU", "CHO_PHE_DUYET"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "LMS_ERR_009", "message": "Không thể hủy khi đã bắt đầu học"}},
            )

        # Hard delete — chua co data lien quan
        await self.db.execute(
            delete(DangKyKhoaHoc).where(DangKyKhoaHoc.id == dk.id)
        )
        await self.db.flush()

    # =========================================================================
    # 6. PHE DUYET DANG KY
    # =========================================================================
    async def _check_manage_permission(self, user: TokenPayload, kh: KhoaHoc, dk: DangKyKhoaHoc) -> None:
        """Check quyen phe duyet/loai hoc vien."""
        if self._is_manager(user):
            return
        is_gv = "GIANG_VIEN" in (user.platform_roles or [])
        if is_gv and str(kh.giang_vien_id) == user.sub:
            return
        if user.is_lanh_dao and user.don_vi_id:
            cc_r = await self.db.execute(
                select(CongChucRef.don_vi_id).where(CongChucRef.id == dk.cong_chuc_id)
            )
            cc_don_vi = cc_r.scalar()
            if cc_don_vi == uuid.UUID(user.don_vi_id):
                return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "LMS_ERR_008", "message": "Không có quyền thực hiện"}},
        )

    async def phe_duyet_dang_ky(
        self,
        dang_ky_id: uuid.UUID,
        phe_duyet: bool,
        ly_do_tu_choi: Optional[str],
        user: TokenPayload,
    ) -> DangKyKhoaHoc:
        """Phe duyet hoac tu choi dang ky TU_NGUYEN."""
        from datetime import datetime
        from lms_service.services.thong_bao_helper import gui_thong_bao
        user_uuid = uuid.UUID(user.sub)

        result = await self.db.execute(
            select(DangKyKhoaHoc, KhoaHoc)
            .join(KhoaHoc, DangKyKhoaHoc.khoa_hoc_id == KhoaHoc.id)
            .where(DangKyKhoaHoc.id == dang_ky_id)
        )
        row = result.one_or_none()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy đăng ký"}},
            )
        dk, kh = row

        # Auth: QT_DAO_TAO, SUPER_ADMIN, GV chu khoa, lanh_dao (don vi minh)
        await self._check_manage_permission(user, kh, dk)

        if dk.trang_thai != "CHO_PHE_DUYET":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "LMS_ERR_010", "message": f"Đăng ký không ở trạng thái chờ phê duyệt (hiện tại: {dk.trang_thai})"}},
            )

        dk.nguoi_phe_duyet_id = user_uuid
        dk.ngay_phe_duyet = datetime.utcnow()

        if phe_duyet:
            dk.trang_thai = "CHUA_BAT_DAU"
            dk.ly_do_tu_choi = None
        else:
            dk.trang_thai = "TU_CHOI"
            dk.ly_do_tu_choi = ly_do_tu_choi

        await self.db.flush()
        await self.db.refresh(dk)

        # Thong bao cho hoc vien
        msg = f"Đăng ký khóa \"{kh.ten_khoa_hoc}\" đã được phê duyệt. Bạn có thể bắt đầu học." if phe_duyet else f"Đăng ký khóa \"{kh.ten_khoa_hoc}\" bị từ chối. Lý do: {ly_do_tu_choi or 'Không đáp ứng yêu cầu'}"
        await gui_thong_bao(
            nguoi_nhan_id=dk.cong_chuc_id,
            tieu_de=f"{'Đã duyệt' if phe_duyet else 'Từ chối'}: {kh.ten_khoa_hoc}",
            noi_dung=msg,
            muc_do="QUAN_TRONG",
            link_url=f"/dao-tao/khoa-hoc/{kh.id}",
            doi_tuong_type="KHOA_HOC",
            doi_tuong_id=kh.id,
        )

        return dk

    # =========================================================================
    # 7. LOAI HOC VIEN
    # =========================================================================
    async def remove_student(
        self,
        dang_ky_id: uuid.UUID,
        ly_do: Optional[str],
        user: TokenPayload,
    ) -> None:
        """Loai hoc vien khoi khoa hoc (soft delete → BI_LOAI)."""
        from datetime import datetime
        from lms_service.services.thong_bao_helper import gui_thong_bao
        user_uuid = uuid.UUID(user.sub)

        result = await self.db.execute(
            select(DangKyKhoaHoc, KhoaHoc)
            .join(KhoaHoc, DangKyKhoaHoc.khoa_hoc_id == KhoaHoc.id)
            .where(DangKyKhoaHoc.id == dang_ky_id)
        )
        row = result.one_or_none()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy đăng ký"}},
            )
        dk, kh = row

        if dk.trang_thai == "BI_LOAI":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "LMS_ERR_010", "message": "Học viên đã bị loại rồi"}},
            )

        await self._check_manage_permission(user, kh, dk)

        dk.trang_thai = "BI_LOAI"
        dk.ly_do_tu_choi = ly_do
        dk.nguoi_phe_duyet_id = user_uuid
        dk.ngay_phe_duyet = datetime.utcnow()
        await self.db.flush()

        await gui_thong_bao(
            nguoi_nhan_id=dk.cong_chuc_id,
            tieu_de=f"Bạn đã bị loại khỏi khóa: {kh.ten_khoa_hoc}",
            noi_dung=f"Lý do: {ly_do or 'Không rõ'}. Vui lòng liên hệ quản trị đào tạo.",
            muc_do="QUAN_TRONG",
            link_url="/dao-tao/khoa-hoc",
            doi_tuong_type="KHOA_HOC",
            doi_tuong_id=kh.id,
        )

    # =========================================================================
    # 8. DANH SACH CHO PHE DUYET
    # =========================================================================
    async def danh_sach_cho_phe_duyet(
        self,
        user: TokenPayload,
        page: int = 1,
        page_size: int = 20,
        khoa_hoc_id: Optional[uuid.UUID] = None,
    ) -> dict:
        """Danh sach dang ky CHO_PHE_DUYET."""
        cc = CongChucRef.__table__.alias("cc")
        dv = DonViRef.__table__.alias("dv")

        base_where = [DangKyKhoaHoc.trang_thai == "CHO_PHE_DUYET"]

        if not self._is_manager(user):
            is_gv = "GIANG_VIEN" in (user.platform_roles or [])
            if is_gv:
                base_where.append(KhoaHoc.giang_vien_id == uuid.UUID(user.sub))
            elif user.is_lanh_dao and user.don_vi_id:
                base_where.append(cc.c.don_vi_id == uuid.UUID(user.don_vi_id))
            else:
                return {"items": [], "pagination": {"page": page, "page_size": page_size, "total_items": 0, "total_pages": 0}}

        if khoa_hoc_id:
            base_where.append(DangKyKhoaHoc.khoa_hoc_id == khoa_hoc_id)

        count_stmt = (
            select(func.count(DangKyKhoaHoc.id))
            .join(KhoaHoc, DangKyKhoaHoc.khoa_hoc_id == KhoaHoc.id)
            .join(cc, DangKyKhoaHoc.cong_chuc_id == cc.c.id)
            .where(*base_where)
        )
        total_items = (await self.db.execute(count_stmt)).scalar() or 0
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

        stmt = (
            select(
                DangKyKhoaHoc.id.label("dang_ky_id"),
                DangKyKhoaHoc.created_at,
                cc.c.ho_ten.label("ho_ten"),
                cc.c.ma_cc.label("ma_cc"),
                dv.c.ten_don_vi.label("don_vi_ten"),
                KhoaHoc.ten_khoa_hoc,
                KhoaHoc.id.label("khoa_hoc_id"),
            )
            .join(KhoaHoc, DangKyKhoaHoc.khoa_hoc_id == KhoaHoc.id)
            .join(cc, DangKyKhoaHoc.cong_chuc_id == cc.c.id)
            .outerjoin(dv, cc.c.don_vi_id == dv.c.id)
            .where(*base_where)
            .order_by(DangKyKhoaHoc.created_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.db.execute(stmt)).all()

        items = [
            {
                "dang_ky_id": str(r.dang_ky_id),
                "ho_ten": r.ho_ten,
                "ma_cc": r.ma_cc,
                "don_vi_ten": r.don_vi_ten,
                "khoa_hoc_ten": r.ten_khoa_hoc,
                "khoa_hoc_id": str(r.khoa_hoc_id),
                "ngay_dang_ky": r.created_at,
            }
            for r in rows
        ]

        return {
            "items": items,
            "pagination": {"page": page, "page_size": page_size, "total_items": total_items, "total_pages": total_pages},
        }
