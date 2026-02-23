"""
lms_service/services/khoa_hoc_service.py
========================================
Business logic cho CRUD + workflow khoa hoc.
Bao gom: danh sach, quan ly, chi tiet, tao moi, cap nhat, chuyen trang thai, xoa.
"""

import math
import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.models.base import CongChucRef
from lms_service.models.khoa_hoc import KhoaHoc
from lms_service.models.chuyen_de import ChuyenDe
from lms_service.models.bai_hoc import BaiHoc
from lms_service.models.dang_ky_khoa_hoc import DangKyKhoaHoc
from lms_service.schemas.khoa_hoc import KhoaHocCreate, KhoaHocUpdate
from shared.auth import TokenPayload


# Cac transition hop le trong workflow trang thai
VALID_TRANSITIONS = {
    "NHAP": ["CHO_DUYET"],
    "CHO_DUYET": ["DA_XUAT_BAN", "NHAP"],  # NHAP = tu choi
    "DA_XUAT_BAN": ["TAM_DUNG", "DA_DONG"],
    "TAM_DUNG": ["DA_XUAT_BAN"],
    "DA_DONG": [],
}


class KhoaHocService:
    """Service xu ly logic khoa hoc."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # HELPER: Build base query voi JOIN giang_vien, chuyen_de, count hoc_vien
    # =========================================================================
    def _base_list_query(self):
        """Tao base query voi LEFT JOIN va subquery dem hoc vien."""
        # Alias cho giang_vien va nguoi_duyet
        gv = CongChucRef.__table__.alias("gv")
        # Subquery dem so hoc vien active
        so_hv_subq = (
            select(
                DangKyKhoaHoc.khoa_hoc_id,
                func.count(DangKyKhoaHoc.id).label("so_hoc_vien"),
            )
            .group_by(DangKyKhoaHoc.khoa_hoc_id)
            .subquery()
        )

        stmt = (
            select(
                KhoaHoc,
                ChuyenDe.ten_chuyen_de.label("chuyen_de_ten"),
                gv.c.ho_ten.label("giang_vien_ho_ten"),
                func.coalesce(so_hv_subq.c.so_hoc_vien, 0).label("so_hoc_vien"),
            )
            .outerjoin(ChuyenDe, KhoaHoc.chuyen_de_id == ChuyenDe.id)
            .outerjoin(gv, KhoaHoc.giang_vien_id == gv.c.id)
            .outerjoin(so_hv_subq, KhoaHoc.id == so_hv_subq.c.khoa_hoc_id)
        )
        return stmt

    def _row_to_dict(self, kh: KhoaHoc, chuyen_de_ten, giang_vien_ho_ten, so_hoc_vien) -> dict:
        """Chuyen row thanh dict cho response."""
        return {
            "id": kh.id,
            "ma_khoa_hoc": kh.ma_khoa_hoc,
            "ten_khoa_hoc": kh.ten_khoa_hoc,
            "mo_ta": kh.mo_ta,
            "chuyen_de_id": kh.chuyen_de_id,
            "loai": kh.loai,
            "anh_dai_dien": kh.anh_dai_dien,
            "thoi_luong_phut": kh.thoi_luong_phut,
            "so_bai_hoc": kh.so_bai_hoc,
            "dieu_kien_tien_quyet": kh.dieu_kien_tien_quyet,
            "diem_dat_yeu_cau": kh.diem_dat_yeu_cau,
            "ngay_bat_dau": kh.ngay_bat_dau,
            "ngay_ket_thuc": kh.ngay_ket_thuc,
            "giang_vien_id": kh.giang_vien_id,
            "trang_thai": kh.trang_thai,
            "nguoi_duyet_id": kh.nguoi_duyet_id,
            "ngay_duyet": kh.ngay_duyet,
            "is_active": kh.is_active,
            "created_at": kh.created_at,
            "updated_at": kh.updated_at,
            "chuyen_de_ten": chuyen_de_ten,
            "giang_vien_ho_ten": giang_vien_ho_ten,
            "so_hoc_vien": so_hoc_vien,
        }

    # =========================================================================
    # 1. DANH SACH (cho hoc vien — chi DA_XUAT_BAN)
    # =========================================================================
    async def danh_sach(
        self,
        page: int = 1,
        page_size: int = 20,
        trang_thai: Optional[str] = None,
        chuyen_de_id: Optional[uuid.UUID] = None,
        loai: Optional[str] = None,
        search: Optional[str] = None,
        user: Optional[TokenPayload] = None,
    ) -> dict:
        """Danh sach khoa hoc cho hoc vien.
        CBCC thuong chi thay DA_XUAT_BAN. QT_DAO_TAO/ADMIN thay tat ca.
        """
        stmt = self._base_list_query()
        count_stmt = select(func.count(KhoaHoc.id))

        # Loc: CBCC thuong chi thay khoa da xuat ban
        is_manager = user and (
            user.vai_tro == "SUPER_ADMIN"
            or "QT_DAO_TAO" in (user.platform_roles or [])
        )
        if not is_manager:
            stmt = stmt.where(KhoaHoc.trang_thai == "DA_XUAT_BAN")
            count_stmt = count_stmt.where(KhoaHoc.trang_thai == "DA_XUAT_BAN")

        stmt = stmt.where(KhoaHoc.is_active == True)  # noqa: E712
        count_stmt = count_stmt.where(KhoaHoc.is_active == True)  # noqa: E712

        # Filter trang_thai (override cho manager)
        if trang_thai and is_manager:
            stmt = stmt.where(KhoaHoc.trang_thai == trang_thai)
            count_stmt = count_stmt.where(KhoaHoc.trang_thai == trang_thai)

        if chuyen_de_id:
            stmt = stmt.where(KhoaHoc.chuyen_de_id == chuyen_de_id)
            count_stmt = count_stmt.where(KhoaHoc.chuyen_de_id == chuyen_de_id)

        if loai:
            stmt = stmt.where(KhoaHoc.loai == loai)
            count_stmt = count_stmt.where(KhoaHoc.loai == loai)

        # Full-text search dung tsvector
        if search:
            search_clause = sa_text(
                "lms.khoa_hoc.search_vector @@ plainto_tsquery('simple', :search)"
            )
            stmt = stmt.where(search_clause).params(search=search)
            count_stmt = count_stmt.where(search_clause).params(search=search)

        # Count total
        total_result = await self.db.execute(count_stmt)
        total_items = total_result.scalar() or 0
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

        # Pagination
        stmt = stmt.order_by(KhoaHoc.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)
        rows = result.all()

        items = [self._row_to_dict(*row) for row in rows]

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
    # 2. DANH SACH QUAN LY (cho giang vien / QT dao tao)
    # =========================================================================
    async def danh_sach_quan_ly(
        self,
        page: int = 1,
        page_size: int = 20,
        trang_thai: Optional[str] = None,
        search: Optional[str] = None,
        user: Optional[TokenPayload] = None,
    ) -> dict:
        """Danh sach quan ly — tat ca trang thai.
        GIANG_VIEN: chi khoa cua minh.
        QT_DAO_TAO/SUPER_ADMIN: tat ca.
        """
        stmt = self._base_list_query()
        count_stmt = select(func.count(KhoaHoc.id))

        # GIANG_VIEN chi thay khoa cua minh
        is_qt = user and (
            user.vai_tro == "SUPER_ADMIN"
            or "QT_DAO_TAO" in (user.platform_roles or [])
        )
        if not is_qt and user:
            user_uuid = uuid.UUID(user.sub)
            stmt = stmt.where(KhoaHoc.giang_vien_id == user_uuid)
            count_stmt = count_stmt.where(KhoaHoc.giang_vien_id == user_uuid)

        if trang_thai:
            stmt = stmt.where(KhoaHoc.trang_thai == trang_thai)
            count_stmt = count_stmt.where(KhoaHoc.trang_thai == trang_thai)

        if search:
            search_clause = sa_text(
                "lms.khoa_hoc.search_vector @@ plainto_tsquery('simple', :search)"
            )
            stmt = stmt.where(search_clause).params(search=search)
            count_stmt = count_stmt.where(search_clause).params(search=search)

        # Count total
        total_result = await self.db.execute(count_stmt)
        total_items = total_result.scalar() or 0
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

        # Pagination
        stmt = stmt.order_by(KhoaHoc.updated_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)
        rows = result.all()
        items = [self._row_to_dict(*row) for row in rows]

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
    # 3. CHI TIET
    # =========================================================================
    async def chi_tiet(self, id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> dict:
        """Lay chi tiet khoa hoc voi JOIN giang vien, chuyen de, nguoi duyet.
        Neu co user_id → query them trang thai dang ky cua user hien tai.
        """
        gv = CongChucRef.__table__.alias("gv")
        nd = CongChucRef.__table__.alias("nd")
        so_hv_subq = (
            select(
                DangKyKhoaHoc.khoa_hoc_id,
                func.count(DangKyKhoaHoc.id).label("so_hoc_vien"),
            )
            .group_by(DangKyKhoaHoc.khoa_hoc_id)
            .subquery()
        )

        stmt = (
            select(
                KhoaHoc,
                ChuyenDe.ten_chuyen_de.label("chuyen_de_ten"),
                gv.c.ho_ten.label("giang_vien_ho_ten"),
                nd.c.ho_ten.label("nguoi_duyet_ho_ten"),
                func.coalesce(so_hv_subq.c.so_hoc_vien, 0).label("so_hoc_vien"),
            )
            .outerjoin(ChuyenDe, KhoaHoc.chuyen_de_id == ChuyenDe.id)
            .outerjoin(gv, KhoaHoc.giang_vien_id == gv.c.id)
            .outerjoin(nd, KhoaHoc.nguoi_duyet_id == nd.c.id)
            .outerjoin(so_hv_subq, KhoaHoc.id == so_hv_subq.c.khoa_hoc_id)
            .where(KhoaHoc.id == id)
        )

        result = await self.db.execute(stmt)
        row = result.one_or_none()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {
                        "code": "LMS_ERR_001",
                        "message": "Không tìm thấy khóa học",
                    },
                },
            )

        kh, chuyen_de_ten, giang_vien_ho_ten, nguoi_duyet_ho_ten, so_hoc_vien = row
        data = self._row_to_dict(kh, chuyen_de_ten, giang_vien_ho_ten, so_hoc_vien)
        data["nguoi_duyet_ho_ten"] = nguoi_duyet_ho_ten

        # Query trang thai dang ky cua user hien tai
        dang_ky_data = None
        if user_id:
            dk_r = await self.db.execute(
                select(DangKyKhoaHoc).where(
                    DangKyKhoaHoc.khoa_hoc_id == id,
                    DangKyKhoaHoc.cong_chuc_id == user_id,
                )
            )
            dk = dk_r.scalar_one_or_none()
            if dk:
                dang_ky_data = {
                    "trang_thai": dk.trang_thai or "CHUA_BAT_DAU",
                    "phan_tram_hoan_thanh": float(dk.phan_tram_hoan_thanh or 0),
                    "loai_dang_ky": dk.loai_dang_ky or "TU_NGUYEN",
                    "han_hoan_thanh": dk.han_hoan_thanh,
                }
        data["dang_ky"] = dang_ky_data
        return data

    async def _get_khoa_hoc(self, id: uuid.UUID) -> KhoaHoc:
        """Helper lay model KhoaHoc — dung cho update/delete."""
        stmt = select(KhoaHoc).where(KhoaHoc.id == id)
        result = await self.db.execute(stmt)
        kh = result.scalar_one_or_none()
        if kh is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy khóa học"},
                },
            )
        return kh

    # =========================================================================
    # 4. TAO MOI
    # =========================================================================
    async def tao_moi(self, data: KhoaHocCreate, user: TokenPayload) -> KhoaHoc:
        """Tao khoa hoc moi. Luon bat dau trang thai NHAP."""
        # Kiem tra trung ma_khoa_hoc
        stmt = select(KhoaHoc).where(KhoaHoc.ma_khoa_hoc == data.ma_khoa_hoc)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "error": {"code": "LMS_ERR_002", "message": "Mã khóa học đã tồn tại"},
                },
            )

        # Verify chuyen_de ton tai (neu co)
        if data.chuyen_de_id:
            cd_stmt = select(ChuyenDe.id).where(ChuyenDe.id == data.chuyen_de_id)
            cd_result = await self.db.execute(cd_stmt)
            if cd_result.scalar_one_or_none() is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy chuyên đề"},
                    },
                )

        kh = KhoaHoc(
            ma_khoa_hoc=data.ma_khoa_hoc,
            ten_khoa_hoc=data.ten_khoa_hoc,
            mo_ta=data.mo_ta,
            chuyen_de_id=data.chuyen_de_id,
            loai=data.loai,
            thoi_luong_phut=data.thoi_luong_phut,
            diem_dat_yeu_cau=data.diem_dat_yeu_cau,
            ngay_bat_dau=data.ngay_bat_dau,
            ngay_ket_thuc=data.ngay_ket_thuc,
            dieu_kien_tien_quyet=data.dieu_kien_tien_quyet,
            giang_vien_id=uuid.UUID(user.sub),
            trang_thai="NHAP",
        )
        self.db.add(kh)
        await self.db.flush()
        await self.db.refresh(kh)
        return kh

    # =========================================================================
    # 5. CAP NHAT
    # =========================================================================
    async def cap_nhat(
        self, id: uuid.UUID, data: KhoaHocUpdate, user: TokenPayload
    ) -> KhoaHoc:
        """Cap nhat khoa hoc.
        GIANG_VIEN: chi khoa cua minh, trang_thai == NHAP.
        QT_DAO_TAO/SUPER_ADMIN: bat ky (tru DA_DONG).
        """
        kh = await self._get_khoa_hoc(id)

        is_qt = (
            user.vai_tro == "SUPER_ADMIN"
            or "QT_DAO_TAO" in (user.platform_roles or [])
        )

        if not is_qt:
            # GIANG_VIEN chi sua khoa cua minh va o trang thai NHAP
            if str(kh.giang_vien_id) != user.sub:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "error": {"code": "LMS_ERR_008", "message": "Bạn chỉ được sửa khóa học của mình"},
                    },
                )
            if kh.trang_thai != "NHAP":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "error": {"code": "LMS_ERR_010", "message": "Chỉ được sửa khóa học ở trạng thái NHÁP"},
                    },
                )
        else:
            if kh.trang_thai == "DA_DONG":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "error": {"code": "LMS_ERR_010", "message": "Không thể sửa khóa học đã đóng"},
                    },
                )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(kh, field, value)

        await self.db.flush()
        await self.db.refresh(kh)
        return kh

    # =========================================================================
    # 6. CHUYEN TRANG THAI (WORKFLOW)
    # =========================================================================
    async def chuyen_trang_thai(
        self,
        id: uuid.UUID,
        trang_thai_moi: str,
        ghi_chu: Optional[str],
        user: TokenPayload,
    ) -> KhoaHoc:
        """Chuyen trang thai khoa hoc theo workflow.

        Transition hop le:
          NHAP → CHO_DUYET
          CHO_DUYET → DA_XUAT_BAN | NHAP (tu choi, can ghi_chu)
          DA_XUAT_BAN → TAM_DUNG | DA_DONG
          TAM_DUNG → DA_XUAT_BAN
        """
        kh = await self._get_khoa_hoc(id)
        current = kh.trang_thai or "NHAP"

        # Kiem tra transition hop le
        allowed = VALID_TRANSITIONS.get(current, [])
        if trang_thai_moi not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "LMS_ERR_010",
                        "message": f"Chuyển trạng thái không hợp lệ: {current} → {trang_thai_moi}",
                    },
                },
            )

        is_qt = (
            user.vai_tro == "SUPER_ADMIN"
            or "QT_DAO_TAO" in (user.platform_roles or [])
        )

        # === NHAP → CHO_DUYET ===
        if current == "NHAP" and trang_thai_moi == "CHO_DUYET":
            # GIANG_VIEN chi gui duyet khoa cua minh
            if not is_qt and str(kh.giang_vien_id) != user.sub:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "error": {"code": "LMS_ERR_008", "message": "Bạn chỉ được gửi duyệt khóa học của mình"},
                    },
                )
            # Dieu kien: phai co it nhat 1 bai hoc
            bh_count = await self.db.execute(
                select(func.count(BaiHoc.id)).where(
                    BaiHoc.khoa_hoc_id == id,
                    BaiHoc.is_active == True,  # noqa: E712
                )
            )
            if (bh_count.scalar() or 0) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "error": {
                            "code": "LMS_ERR_010",
                            "message": "Khóa học phải có ít nhất 1 bài học trước khi gửi duyệt",
                        },
                    },
                )

        # === CHO_DUYET → DA_XUAT_BAN (duyet) ===
        elif current == "CHO_DUYET" and trang_thai_moi == "DA_XUAT_BAN":
            if not is_qt:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "error": {"code": "LMS_ERR_008", "message": "Chỉ QT đào tạo mới được duyệt khóa học"},
                    },
                )
            kh.nguoi_duyet_id = uuid.UUID(user.sub)
            kh.ngay_duyet = datetime.utcnow()

        # === CHO_DUYET → NHAP (tu choi) ===
        elif current == "CHO_DUYET" and trang_thai_moi == "NHAP":
            if not is_qt:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "error": {"code": "LMS_ERR_008", "message": "Chỉ QT đào tạo mới được từ chối khóa học"},
                    },
                )
            if not ghi_chu or not ghi_chu.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "error": {
                            "code": "LMS_ERR_010",
                            "message": "Phải nhập lý do từ chối",
                        },
                    },
                )

        # === DA_XUAT_BAN → TAM_DUNG / DA_DONG, TAM_DUNG → DA_XUAT_BAN ===
        else:
            if not is_qt:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "error": {"code": "LMS_ERR_008", "message": "Chỉ QT đào tạo mới thực hiện thao tác này"},
                    },
                )

        kh.trang_thai = trang_thai_moi
        await self.db.flush()
        await self.db.refresh(kh)
        return kh

    # =========================================================================
    # 7. XOA (soft delete)
    # =========================================================================
    async def xoa(self, id: uuid.UUID, user: TokenPayload) -> None:
        """Soft delete khoa hoc.
        Chi xoa neu trang_thai == NHAP va chua co ai dang ky.
        """
        kh = await self._get_khoa_hoc(id)

        if kh.trang_thai != "NHAP":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "LMS_ERR_009",
                        "message": "Chỉ xóa được khóa học ở trạng thái NHÁP",
                    },
                },
            )

        # Kiem tra co ai dang ky khong
        dk_count = await self.db.execute(
            select(func.count(DangKyKhoaHoc.id)).where(
                DangKyKhoaHoc.khoa_hoc_id == id
            )
        )
        if (dk_count.scalar() or 0) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "LMS_ERR_009",
                        "message": "Không thể xóa khóa học đã có người đăng ký",
                    },
                },
            )

        kh.is_active = False
        await self.db.flush()
