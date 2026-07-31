"""
lms_service/services/ky_thi_service.py
======================================
Business logic cho ky thi DGNL + cau truc de + validate.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.models.base import CongChucRef, DonViRef
from lms_service.models.ky_thi import KyThi
from lms_service.models.cau_truc_de import CauTrucDe
from lms_service.models.thi_sinh import ThiSinh
from lms_service.models.linh_vuc import LinhVuc
from lms_service.models.vi_tri_viec_lam import ViTriViecLam
from lms_service.models.cau_hoi_dgnl import CauHoiDgnl
from lms_service.schemas.ky_thi import (
    KyThiCreate, KyThiUpdate, KyThiTrangThaiUpdate,
    CauTrucDeCreate, CauTrucDeResponse, CauTrucDeByViTri,
    ValidateItem, ValidateViTri, ValidateResponse,
    TRANG_THAI_TRANSITIONS,
)
from lms_service.services.thong_bao_helper import gui_thong_bao_bulk
from shared.auth import TokenPayload
from lms_service.core.timezone import now_vn


class KyThiService:
    """Service ky thi DGNL."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _is_manager(self, user: TokenPayload) -> bool:
        return user.vai_tro == "SUPER_ADMIN" or "QT_DAO_TAO" in (user.platform_roles or [])

    def _is_lanh_dao(self, user: TokenPayload) -> bool:
        return user.vai_tro in ("CCT", "PCCT") or getattr(user, "is_lanh_dao", False)

    # ================================================================
    # KY THI CRUD
    # ================================================================

    async def danh_sach(
        self,
        user: TokenPayload,
        trang_thai: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Danh sach ky thi. CBCC chi thay DANG_MO + duoc giao. QT/LD thay tat ca."""
        is_qt = self._is_manager(user)
        is_ld = self._is_lanh_dao(user)

        base_where = [KyThi.is_active == True]
        if trang_thai:
            base_where.append(KyThi.trang_thai == trang_thai)

        # CBCC chi thay ky thi DANG_MO hoac DA_DONG ma minh duoc giao
        if not is_qt and not is_ld:
            base_where.append(KyThi.trang_thai.in_(["DANG_MO", "DA_DONG"]))
            base_where.append(
                KyThi.id.in_(
                    select(ThiSinh.ky_thi_id).where(
                        ThiSinh.cong_chuc_id == uuid.UUID(user.sub)
                    )
                )
            )

        # Count
        count_stmt = select(func.count()).select_from(KyThi).where(*base_where)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Query with JOINs
        nt = CongChucRef.__table__.alias("nt")
        nd = CongChucRef.__table__.alias("nd")
        stmt = (
            select(
                KyThi,
                nt.c.ho_ten.label("nguoi_tao_ho_ten"),
                nd.c.ho_ten.label("nguoi_duyet_ho_ten"),
            )
            .outerjoin(nt, KyThi.nguoi_tao_id == nt.c.id)
            .outerjoin(nd, KyThi.nguoi_duyet_id == nd.c.id)
            .where(*base_where)
            .order_by(KyThi.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        # Trang thai thi sinh cua user hien tai (batch query, tranh N+1)
        kt_ids = [kt.id for kt, _, _ in rows]
        ts_status_map: dict[uuid.UUID, dict] = {}
        if kt_ids:
            ts_r = await self.db.execute(
                select(
                    ThiSinh.ky_thi_id,
                    ThiSinh.trang_thai,
                    ThiSinh.lan_thi_hien_tai,
                ).where(
                    ThiSinh.cong_chuc_id == uuid.UUID(user.sub),
                    ThiSinh.ky_thi_id.in_(kt_ids),
                )
            )
            for kt_id, tt, lan in ts_r.all():
                ts_status_map[kt_id] = {
                    "trang_thai_thi_sinh": tt,
                    "lan_thi_hien_tai": lan or 0,
                }

        items = []
        for kt, nt_ten, nd_ten in rows:
            # Dem thi sinh
            ts_count = await self.db.execute(
                select(func.count()).select_from(ThiSinh).where(ThiSinh.ky_thi_id == kt.id)
            )
            tong_ts = ts_count.scalar() or 0

            # Dem so vi tri
            vt_count = await self.db.execute(
                select(func.count(func.distinct(CauTrucDe.vi_tri_id))).where(
                    CauTrucDe.ky_thi_id == kt.id
                )
            )
            so_vt = vt_count.scalar() or 0

            ts_info = ts_status_map.get(kt.id, {})
            items.append({
                **{c.key: getattr(kt, c.key) for c in kt.__table__.columns},
                "nguoi_tao_ho_ten": nt_ten,
                "nguoi_duyet_ho_ten": nd_ten,
                "tong_thi_sinh": tong_ts,
                "so_vi_tri": so_vt,
                # Trang thai thi sinh cua user hien tai (None neu khong duoc giao)
                "trang_thai_thi_sinh": ts_info.get("trang_thai_thi_sinh"),
                "lan_thi_hien_tai": ts_info.get("lan_thi_hien_tai", 0),
            })

        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
            },
        }

    async def chi_tiet(self, ky_thi_id: uuid.UUID) -> KyThi:
        """Lay chi tiet ky thi."""
        stmt = select(KyThi).where(KyThi.id == ky_thi_id, KyThi.is_active == True)
        result = await self.db.execute(stmt)
        kt = result.scalar_one_or_none()
        if not kt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": {"code": "DGNL_010", "message": "Kỳ thi không tồn tại"}},
            )
        return kt

    async def chi_tiet_full(self, ky_thi_id: uuid.UUID, user: TokenPayload) -> dict:
        """Chi tiet ky thi voi JOIN va thong ke nhanh."""
        kt = await self.chi_tiet(ky_thi_id)

        nt = CongChucRef.__table__.alias("nt")
        nd = CongChucRef.__table__.alias("nd")
        stmt = (
            select(
                nt.c.ho_ten.label("nguoi_tao_ho_ten"),
                nd.c.ho_ten.label("nguoi_duyet_ho_ten"),
            )
            .select_from(nt)
            .outerjoin(nd, nd.c.id == kt.nguoi_duyet_id)
            .where(nt.c.id == kt.nguoi_tao_id)
        )
        r = await self.db.execute(stmt)
        row = r.first()

        ts_count = await self.db.execute(
            select(func.count()).select_from(ThiSinh).where(ThiSinh.ky_thi_id == kt.id)
        )
        vt_count = await self.db.execute(
            select(func.count(func.distinct(CauTrucDe.vi_tri_id))).where(CauTrucDe.ky_thi_id == kt.id)
        )

        # Trang thai thi sinh cua user hien tai — FE dung de quyet dinh
        # "Bat dau" vs "Tiep tuc" vs "Thi lai".
        ts_r = await self.db.execute(
            select(ThiSinh.trang_thai, ThiSinh.lan_thi_hien_tai, ThiSinh.da_xac_nhan).where(
                ThiSinh.ky_thi_id == kt.id,
                ThiSinh.cong_chuc_id == uuid.UUID(user.sub),
            )
        )
        ts_row = ts_r.first()

        return {
            **{c.key: getattr(kt, c.key) for c in kt.__table__.columns},
            "nguoi_tao_ho_ten": row.nguoi_tao_ho_ten if row else None,
            "nguoi_duyet_ho_ten": row.nguoi_duyet_ho_ten if row else None,
            "tong_thi_sinh": ts_count.scalar() or 0,
            "so_vi_tri": vt_count.scalar() or 0,
            "trang_thai_thi_sinh": ts_row.trang_thai if ts_row else None,
            "lan_thi_hien_tai": (ts_row.lan_thi_hien_tai or 0) if ts_row else 0,
            "da_xac_nhan": bool(ts_row.da_xac_nhan) if ts_row else False,
        }

    async def tao_moi(self, data: KyThiCreate, user: TokenPayload) -> KyThi:
        """Tao ky thi moi."""
        # Check ma trung
        existing = await self.db.execute(
            select(KyThi).where(KyThi.ma_ky_thi == data.ma_ky_thi)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "DGNL_011", "message": f"Mã kỳ thi '{data.ma_ky_thi}' đã tồn tại"}},
            )

        kt = KyThi(
            ma_ky_thi=data.ma_ky_thi,
            ten_ky_thi=data.ten_ky_thi,
            mo_ta=data.mo_ta,
            ngay_bat_dau=data.ngay_bat_dau,
            ngay_ket_thuc=data.ngay_ket_thuc,
            thoi_gian_lam_bai_phut=data.thoi_gian_lam_bai_phut,
            diem_dat=data.diem_dat,
            so_lan_thi_toi_da=data.so_lan_thi_toi_da,
            tron_cau_hoi=data.tron_cau_hoi,
            tron_dap_an=data.tron_dap_an,
            hien_ket_qua=data.hien_ket_qua,
            hien_dap_an=data.hien_dap_an,
            yeu_cau_toan_man_hinh=data.yeu_cau_toan_man_hinh,
            trang_thai="NHAP",
            nguoi_tao_id=uuid.UUID(user.sub),
        )
        self.db.add(kt)
        await self.db.commit()
        await self.db.refresh(kt)
        return kt

    async def cap_nhat(self, ky_thi_id: uuid.UUID, data: KyThiUpdate, user: TokenPayload) -> KyThi:
        """Cap nhat ky thi — cho phep sua o moi trang thai."""
        kt = await self.chi_tiet(ky_thi_id)

        update_data = data.model_dump(exclude_unset=True)

        # Check ma trung neu doi ma
        if "ma_ky_thi" in update_data:
            existing = await self.db.execute(
                select(KyThi).where(KyThi.ma_ky_thi == update_data["ma_ky_thi"], KyThi.id != ky_thi_id)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "error": {"code": "DGNL_011", "message": f"Mã kỳ thi '{update_data['ma_ky_thi']}' đã tồn tại"}},
                )

        # Validate ngay
        ngay_bd = update_data.get("ngay_bat_dau", kt.ngay_bat_dau)
        ngay_kt = update_data.get("ngay_ket_thuc", kt.ngay_ket_thuc)
        if ngay_kt <= ngay_bd:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "DGNL_013", "message": "Ngày kết thúc phải sau ngày bắt đầu"}},
            )

        for key, value in update_data.items():
            setattr(kt, key, value)
        kt.updated_at = now_vn()

        await self.db.commit()
        await self.db.refresh(kt)
        return kt

    async def chuyen_trang_thai(
        self, ky_thi_id: uuid.UUID, data: KyThiTrangThaiUpdate, user: TokenPayload
    ) -> KyThi:
        """Chuyen trang thai ky thi theo workflow."""
        kt = await self.chi_tiet(ky_thi_id)
        trang_thai_moi = data.trang_thai

        # Validate transition
        allowed = TRANG_THAI_TRANSITIONS.get(kt.trang_thai, [])
        if trang_thai_moi not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "DGNL_014",
                        "message": f"Không thể chuyển từ {kt.trang_thai} sang {trang_thai_moi}. "
                                   f"Cho phép: {allowed}",
                    },
                },
            )

        # CHO_DUYET -> DANG_MO: chi lanh dao duoc duyet
        if kt.trang_thai == "CHO_DUYET" and trang_thai_moi == "DANG_MO":
            if not self._is_lanh_dao(user) and not self._is_manager(user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"success": False, "error": {"code": "DGNL_015", "message": "Chỉ lãnh đạo mới được phê duyệt kỳ thi"}},
                )
            kt.nguoi_duyet_id = uuid.UUID(user.sub)
            kt.ngay_duyet = now_vn()

        # NHAP -> CHO_DUYET: validate co cau truc de
        if kt.trang_thai == "NHAP" and trang_thai_moi == "CHO_DUYET":
            ctd_count = await self.db.execute(
                select(func.count()).select_from(CauTrucDe).where(CauTrucDe.ky_thi_id == kt.id)
            )
            if (ctd_count.scalar() or 0) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "error": {"code": "DGNL_016", "message": "Kỳ thi chưa có cấu trúc đề. Vui lòng cấu hình trước khi gửi duyệt."}},
                )

        kt.trang_thai = trang_thai_moi
        kt.updated_at = now_vn()

        await self.db.commit()
        await self.db.refresh(kt)

        # Gui thong bao cho thi sinh khi mo/dong ky thi
        await self._gui_thong_bao_trang_thai(kt, trang_thai_moi)

        return kt

    async def xoa(self, ky_thi_id: uuid.UUID, user: TokenPayload) -> None:
        """Soft delete ky thi — chi khi NHAP va chua co thi sinh."""
        kt = await self.chi_tiet(ky_thi_id)
        if kt.trang_thai != "NHAP":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "DGNL_017", "message": "Chỉ được xóa kỳ thi ở trạng thái NHÁP"}},
            )

        ts_count = await self.db.execute(
            select(func.count()).select_from(ThiSinh).where(ThiSinh.ky_thi_id == kt.id)
        )
        if (ts_count.scalar() or 0) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "DGNL_018", "message": "Không thể xóa kỳ thi đã có thí sinh"}},
            )

        kt.is_active = False
        kt.updated_at = now_vn()
        await self.db.commit()

    async def _gui_thong_bao_trang_thai(self, kt: KyThi, trang_thai_moi: str) -> None:
        """Gui thong bao cho thi sinh khi chuyen trang thai ky thi."""
        # Lay danh sach thi sinh
        ts_result = await self.db.execute(
            select(ThiSinh.cong_chuc_id).where(ThiSinh.ky_thi_id == kt.id)
        )
        cc_ids = ts_result.scalars().all()
        if not cc_ids:
            return

        if trang_thai_moi == "DANG_MO":
            await gui_thong_bao_bulk(
                nguoi_nhan_ids=cc_ids,
                tieu_de=f"Kỳ thi đã mở: {kt.ten_ky_thi}",
                noi_dung=f"Kỳ thi \"{kt.ten_ky_thi}\" đã mở. Thời gian: {kt.ngay_bat_dau.strftime('%d/%m/%Y')} - {kt.ngay_ket_thuc.strftime('%d/%m/%Y')}. Vui lòng vào thi đúng hạn.",
                muc_do="KHAN",
                link_url="/dao-tao/ky-thi",
                doi_tuong_type="KY_THI",
                doi_tuong_id=kt.id,
            )
        elif trang_thai_moi == "DA_DONG":
            await gui_thong_bao_bulk(
                nguoi_nhan_ids=cc_ids,
                tieu_de=f"Kỳ thi đã đóng: {kt.ten_ky_thi}",
                noi_dung=f"Kỳ thi \"{kt.ten_ky_thi}\" đã kết thúc. Vào xem kết quả của bạn.",
                muc_do="BINH_THUONG",
                link_url="/dao-tao/ky-thi",
                doi_tuong_type="KY_THI",
                doi_tuong_id=kt.id,
            )

    # ================================================================
    # CAU TRUC DE
    # ================================================================

    async def lay_cau_truc_de(self, ky_thi_id: uuid.UUID) -> list[CauTrucDeByViTri]:
        """Lay cau truc de nhom theo vi tri."""
        await self.chi_tiet(ky_thi_id)  # validate ton tai

        stmt = (
            select(
                CauTrucDe,
                ViTriViecLam.ten_vi_tri.label("vi_tri_ten"),
                LinhVuc.ten_linh_vuc.label("linh_vuc_ten"),
            )
            .join(ViTriViecLam, CauTrucDe.vi_tri_id == ViTriViecLam.id)
            .join(LinhVuc, CauTrucDe.linh_vuc_id == LinhVuc.id)
            .where(CauTrucDe.ky_thi_id == ky_thi_id)
            .order_by(ViTriViecLam.thu_tu, LinhVuc.thu_tu)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        # Nhom theo vi_tri
        vi_tri_map: dict[str, CauTrucDeByViTri] = {}
        for ctd, vt_ten, lv_ten in rows:
            vt_key = str(ctd.vi_tri_id)
            if vt_key not in vi_tri_map:
                vi_tri_map[vt_key] = CauTrucDeByViTri(
                    vi_tri_id=ctd.vi_tri_id,
                    vi_tri_ten=vt_ten,
                    tong_cau=0,
                    chi_tiet=[],
                )
            tong = (ctd.so_cau_de or 0) + (ctd.so_cau_trung_binh or 0) + (ctd.so_cau_kho or 0)
            vi_tri_map[vt_key].tong_cau += tong
            vi_tri_map[vt_key].chi_tiet.append(CauTrucDeResponse(
                id=ctd.id,
                ky_thi_id=ctd.ky_thi_id,
                vi_tri_id=ctd.vi_tri_id,
                linh_vuc_id=ctd.linh_vuc_id,
                so_cau_de=ctd.so_cau_de,
                so_cau_trung_binh=ctd.so_cau_trung_binh,
                so_cau_kho=ctd.so_cau_kho,
                created_at=ctd.created_at,
                vi_tri_ten=vt_ten,
                linh_vuc_ten=lv_ten,
            ))

        return list(vi_tri_map.values())

    async def upsert_cau_truc_de(
        self, ky_thi_id: uuid.UUID, data: CauTrucDeCreate, user: TokenPayload
    ) -> list[CauTrucDeByViTri]:
        """Tao hoac cap nhat cau truc de cho 1 vi tri (bulk upsert)."""
        kt = await self.chi_tiet(ky_thi_id)
        if kt.trang_thai not in ("NHAP",):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "DGNL_019", "message": "Chỉ được cấu hình cấu trúc đề khi kỳ thi ở trạng thái NHÁP"}},
            )

        # Validate vi_tri ton tai
        vt = await self.db.execute(
            select(ViTriViecLam).where(ViTriViecLam.id == data.vi_tri_id, ViTriViecLam.is_active == True)
        )
        if not vt.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": {"code": "DGNL_003", "message": "Vị trí việc làm không tồn tại"}},
            )

        # Validate linh_vuc ton tai
        for item in data.cau_truc:
            lv = await self.db.execute(
                select(LinhVuc).where(LinhVuc.id == item.linh_vuc_id, LinhVuc.is_active == True)
            )
            if not lv.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"success": False, "error": {"code": "DGNL_001", "message": f"Lĩnh vực {item.linh_vuc_id} không tồn tại"}},
                )

        # Xoa cau truc cu cua vi_tri nay trong ky thi
        existing = await self.db.execute(
            select(CauTrucDe).where(
                CauTrucDe.ky_thi_id == ky_thi_id,
                CauTrucDe.vi_tri_id == data.vi_tri_id,
            )
        )
        for old in existing.scalars().all():
            await self.db.delete(old)
        await self.db.flush()

        # Tao moi
        for item in data.cau_truc:
            ctd = CauTrucDe(
                ky_thi_id=ky_thi_id,
                vi_tri_id=data.vi_tri_id,
                linh_vuc_id=item.linh_vuc_id,
                so_cau_de=item.so_cau_de,
                so_cau_trung_binh=item.so_cau_trung_binh,
                so_cau_kho=item.so_cau_kho,
            )
            self.db.add(ctd)

        await self.db.commit()
        return await self.lay_cau_truc_de(ky_thi_id)

    async def xoa_cau_truc_de_vi_tri(
        self, ky_thi_id: uuid.UUID, vi_tri_id: uuid.UUID, user: TokenPayload
    ) -> None:
        """Xoa cau truc de cua 1 vi tri."""
        kt = await self.chi_tiet(ky_thi_id)
        if kt.trang_thai != "NHAP":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "DGNL_019", "message": "Chỉ được xóa cấu trúc đề khi kỳ thi ở trạng thái NHÁP"}},
            )

        existing = await self.db.execute(
            select(CauTrucDe).where(
                CauTrucDe.ky_thi_id == ky_thi_id,
                CauTrucDe.vi_tri_id == vi_tri_id,
            )
        )
        rows = existing.scalars().all()
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": {"code": "DGNL_020", "message": "Không tìm thấy cấu trúc đề cho vị trí này"}},
            )

        for ctd in rows:
            await self.db.delete(ctd)
        await self.db.commit()

    # ================================================================
    # VALIDATE
    # ================================================================

    async def validate_ngan_hang(self, ky_thi_id: uuid.UUID) -> ValidateResponse:
        """Kiem tra ngan hang cau hoi co du cho ky thi khong."""
        await self.chi_tiet(ky_thi_id)

        # Lay tat ca cau truc de
        stmt = (
            select(
                CauTrucDe,
                ViTriViecLam.ten_vi_tri.label("vi_tri_ten"),
                LinhVuc.ten_linh_vuc.label("linh_vuc_ten"),
            )
            .join(ViTriViecLam, CauTrucDe.vi_tri_id == ViTriViecLam.id)
            .join(LinhVuc, CauTrucDe.linh_vuc_id == LinhVuc.id)
            .where(CauTrucDe.ky_thi_id == ky_thi_id)
            .order_by(ViTriViecLam.thu_tu, LinhVuc.thu_tu)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        if not rows:
            return ValidateResponse(
                ky_thi_id=ky_thi_id,
                tat_ca_du=False,
                theo_vi_tri=[],
            )

        tat_ca_du = True
        vi_tri_map: dict[str, ValidateViTri] = {}

        for ctd, vt_ten, lv_ten in rows:
            vt_key = str(ctd.vi_tri_id)
            if vt_key not in vi_tri_map:
                vi_tri_map[vt_key] = ValidateViTri(vi_tri_ten=vt_ten, du_cau_hoi=True, chi_tiet=[])

            for do_kho, so_cau in [("DE", ctd.so_cau_de), ("TRUNG_BINH", ctd.so_cau_trung_binh), ("KHO", ctd.so_cau_kho)]:
                if (so_cau or 0) <= 0:
                    continue

                # Dem cau hoi co san
                count_stmt = select(func.count()).select_from(CauHoiDgnl).where(
                    CauHoiDgnl.linh_vuc_id == ctd.linh_vuc_id,
                    CauHoiDgnl.do_kho == do_kho,
                    CauHoiDgnl.is_active == True,
                )
                co_san = (await self.db.execute(count_stmt)).scalar() or 0
                du = co_san >= so_cau

                if not du:
                    tat_ca_du = False
                    vi_tri_map[vt_key].du_cau_hoi = False

                vi_tri_map[vt_key].chi_tiet.append(ValidateItem(
                    linh_vuc_ten=lv_ten,
                    do_kho=do_kho,
                    yeu_cau=so_cau,
                    co_san=co_san,
                    du=du,
                ))

        return ValidateResponse(
            ky_thi_id=ky_thi_id,
            tat_ca_du=tat_ca_du,
            theo_vi_tri=list(vi_tri_map.values()),
        )

    # ================================================================
    # THONG KE
    # ================================================================

    async def thong_ke(self, ky_thi_id: uuid.UUID, user: TokenPayload) -> dict:
        """Thong ke ket qua ky thi."""
        kt = await self.chi_tiet(ky_thi_id)

        # Tong quan
        ts_stmt = select(ThiSinh).where(ThiSinh.ky_thi_id == ky_thi_id)
        ts_result = await self.db.execute(ts_stmt)
        all_ts = ts_result.scalars().all()

        tong = len(all_ts)
        da_thi = len([t for t in all_ts if t.trang_thai == "DA_NOP"])
        chua_thi = len([t for t in all_ts if t.trang_thai == "CHUA_THI"])
        dang_thi = len([t for t in all_ts if t.trang_thai == "DANG_THI"])
        vang = len([t for t in all_ts if t.trang_thai == "VANG"])
        dat = len([t for t in all_ts if t.xep_loai == "DAT"])
        khong_dat = len([t for t in all_ts if t.xep_loai == "KHONG_DAT"])

        diem_list = [float(t.diem_tong) for t in all_ts if t.diem_tong is not None]
        diem_tb = sum(diem_list) / len(diem_list) if diem_list else 0
        diem_cao = max(diem_list) if diem_list else 0
        diem_thap = min(diem_list) if diem_list else 0

        tong_quan = {
            "tong_thi_sinh": tong,
            "da_thi": da_thi,
            "chua_thi": chua_thi,
            "dang_thi": dang_thi,
            "vang": vang,
            "dat": dat,
            "khong_dat": khong_dat,
            "ti_le_dat": round(dat / da_thi * 100, 1) if da_thi > 0 else 0,
            "diem_trung_binh": round(diem_tb, 1),
            "diem_cao_nhat": round(diem_cao, 1),
            "diem_thap_nhat": round(diem_thap, 1),
        }

        # Theo vi tri
        theo_vi_tri = []
        vi_tri_ids = set(t.vi_tri_id for t in all_ts)
        for vt_id in vi_tri_ids:
            vt_r = await self.db.execute(select(ViTriViecLam).where(ViTriViecLam.id == vt_id))
            vt = vt_r.scalar_one_or_none()
            vt_ts = [t for t in all_ts if t.vi_tri_id == vt_id]
            vt_dat = len([t for t in vt_ts if t.xep_loai == "DAT"])
            vt_kdat = len([t for t in vt_ts if t.xep_loai == "KHONG_DAT"])
            vt_diem = [float(t.diem_tong) for t in vt_ts if t.diem_tong is not None]
            theo_vi_tri.append({
                "vi_tri": vt.ten_vi_tri if vt else str(vt_id),
                "tong": len(vt_ts),
                "dat": vt_dat,
                "khong_dat": vt_kdat,
                "diem_tb": round(sum(vt_diem) / len(vt_diem), 1) if vt_diem else 0,
            })

        # Theo don vi
        theo_don_vi = []
        cc_ids = [t.cong_chuc_id for t in all_ts]
        if cc_ids:
            cc_table = CongChucRef.__table__
            dv_table = DonViRef.__table__
            cc_r = await self.db.execute(
                select(cc_table.c.id, cc_table.c.don_vi_id, dv_table.c.ten_don_vi)
                .outerjoin(dv_table, cc_table.c.don_vi_id == dv_table.c.id)
                .where(cc_table.c.id.in_(cc_ids))
            )
            cc_dv_map = {row.id: (row.don_vi_id, row.ten_don_vi) for row in cc_r.all()}

            dv_groups: dict[str, list] = {}
            for t in all_ts:
                dv_info = cc_dv_map.get(t.cong_chuc_id, (None, "Không xác định"))
                dv_ten = dv_info[1] or "Không xác định"
                dv_groups.setdefault(dv_ten, []).append(t)

            for dv_ten, dv_ts in dv_groups.items():
                dv_dat = len([t for t in dv_ts if t.xep_loai == "DAT"])
                dv_diem = [float(t.diem_tong) for t in dv_ts if t.diem_tong is not None]
                theo_don_vi.append({
                    "don_vi": dv_ten,
                    "tong": len(dv_ts),
                    "dat": dv_dat,
                    "ti_le_dat": round(dv_dat / len(dv_ts) * 100, 1) if dv_ts else 0,
                    "diem_tb": round(sum(dv_diem) / len(dv_diem), 1) if dv_diem else 0,
                })

        return {
            "tong_quan": tong_quan,
            "theo_vi_tri": theo_vi_tri,
            "theo_don_vi": theo_don_vi,
        }
