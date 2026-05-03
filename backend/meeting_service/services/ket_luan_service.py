"""
ket_luan_service.py
=====================
Module 10 — Kết luận / nhiệm vụ + dashboard 1 cấp.

Auto trang_thai:
- POST /tien-do với phan_tram=100 → HOAN_THANH
- POST /tien-do với phan_tram>0 (CHUA_BAT_DAU) → DANG_LAM
"""

from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.models.diem_danh import DiemDanh
from meeting_service.models.ket_luan import KetLuan
from meeting_service.models.thanh_phan import ThanhPhan
from meeting_service.models.tien_do import TienDo
from meeting_service.schemas.ket_luan import (
    KetLuanCreate,
    KetLuanUpdate,
    TienDoCreate,
)
from meeting_service.services.audit_log_service import ghi_audit
from meeting_service.services.notification_service import gui_thong_bao
from shared.auth import TokenPayload


class KetLuanService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ──────────────────────────────────────────────────────────────────
    # CREATE
    # ──────────────────────────────────────────────────────────────────
    async def tao(
        self, cuoc_hop_id: UUID, data: KetLuanCreate, user: TokenPayload
    ) -> KetLuan:
        kl = KetLuan(
            cuoc_hop_id=cuoc_hop_id,
            noi_dung=data.noi_dung,
            nguoi_phu_trach_id=data.nguoi_phu_trach_id,
            don_vi_phu_trach_id=data.don_vi_phu_trach_id,
            han_hoan_thanh=data.han_hoan_thanh,
            muc_uu_tien=data.muc_uu_tien,
        )
        self.db.add(kl)
        await self.db.flush()

        # Notify nguoi_phu_trach
        await gui_thong_bao(
            self.db,
            nguoi_nhan_id=data.nguoi_phu_trach_id,
            tieu_de=f"Bạn được giao nhiệm vụ: {data.noi_dung[:80]}",
            noi_dung=f"Hạn: {data.han_hoan_thanh or '—'}, Ưu tiên: {data.muc_uu_tien}",
            sub_loai="KET_LUAN_GIAO",
            link_url=f"/hop-khong-giay/chi-tiet/{cuoc_hop_id}/ket-luan",
            doi_tuong_id=kl.id,
            muc_do="QUAN_TRONG" if data.muc_uu_tien == "CAO" else "BINH_THUONG",
        )

        await ghi_audit(
            self.db,
            hanh_dong="CREATE_TASK",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="ket_luan",
            doi_tuong_id=kl.id,
            chi_tiet={
                "cuoc_hop_id": str(cuoc_hop_id),
                "nguoi_phu_trach_id": str(data.nguoi_phu_trach_id),
                "han_hoan_thanh": data.han_hoan_thanh.isoformat() if data.han_hoan_thanh else None,
                "muc_uu_tien": data.muc_uu_tien,
            },
        )
        await self.db.flush()
        return kl

    # ──────────────────────────────────────────────────────────────────
    # LIST OF MEETING
    # ──────────────────────────────────────────────────────────────────
    async def list_for_cuoc_hop(self, cuoc_hop_id: UUID) -> list[KetLuan]:
        result = await self.db.execute(
            select(KetLuan)
            .where(
                KetLuan.cuoc_hop_id == cuoc_hop_id,
                KetLuan.is_deleted.is_(False),
            )
            .order_by(KetLuan.created_at.asc())
        )
        return list(result.scalars().all())

    # ──────────────────────────────────────────────────────────────────
    # UPDATE METADATA
    # ──────────────────────────────────────────────────────────────────
    async def cap_nhat(
        self, kl_id: UUID, data: KetLuanUpdate, user: TokenPayload
    ) -> KetLuan:
        kl = await self._get(kl_id)

        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return kl
        for k, v in changes.items():
            setattr(kl, k, v)
        kl.updated_at = datetime.now(timezone.utc)

        await ghi_audit(
            self.db,
            hanh_dong="UPDATE_TASK",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="ket_luan",
            doi_tuong_id=kl.id,
            chi_tiet={"new_value": {
                k: (v.isoformat() if hasattr(v, "isoformat") else str(v) if v is not None else None)
                for k, v in changes.items()
            }},
        )
        await self.db.flush()
        return kl

    # ──────────────────────────────────────────────────────────────────
    # CAP NHAT TIEN DO
    # ──────────────────────────────────────────────────────────────────
    async def cap_nhat_tien_do(
        self, kl_id: UUID, data: TienDoCreate, user: TokenPayload
    ) -> TienDo:
        kl = await self._get(kl_id)
        user_id = UUID(user.sub)

        # Quyền: nguoi_phu_trach, hoặc admin/TRUONG_CNTT
        if kl.nguoi_phu_trach_id != user_id and not (
            user.is_admin or user.vai_tro in ("SUPER_ADMIN", "ADMIN")
            or "TRUONG_CNTT" in (user.platform_roles or [])
        ):
            raise HTTPException(
                status_code=403,
                detail={"success": False, "error": {"code": "NO_PERMISSION",
                        "message": "Chỉ người phụ trách mới được cập nhật tiến độ"}},
            )

        td = TienDo(
            ket_luan_id=kl.id,
            mo_ta=data.mo_ta,
            phan_tram_truoc=kl.tien_do_phan_tram,
            phan_tram_sau=data.phan_tram_sau,
            file_minh_chung_minio_key=data.file_minh_chung_minio_key,
            nguoi_cap_nhat_id=user_id,
        )
        self.db.add(td)

        # Auto trang_thai
        kl.tien_do_phan_tram = data.phan_tram_sau
        kl.updated_at = datetime.now(timezone.utc)
        if data.phan_tram_sau == 100:
            kl.trang_thai = "HOAN_THANH"
        elif data.phan_tram_sau > 0 and kl.trang_thai == "CHUA_BAT_DAU":
            kl.trang_thai = "DANG_LAM"

        await ghi_audit(
            self.db,
            hanh_dong="UPDATE_PROGRESS",
            nguoi_thuc_hien_id=user_id,
            doi_tuong_loai="ket_luan",
            doi_tuong_id=kl.id,
            chi_tiet={
                "phan_tram_truoc": td.phan_tram_truoc,
                "phan_tram_sau": td.phan_tram_sau,
                "trang_thai_moi": kl.trang_thai,
            },
        )
        await self.db.flush()
        return td

    # ──────────────────────────────────────────────────────────────────
    # CỦA TÔI
    # ──────────────────────────────────────────────────────────────────
    async def cua_toi(
        self,
        user: TokenPayload,
        trang_thai: Optional[str] = None,
    ) -> list[KetLuan]:
        user_id = UUID(user.sub)
        stmt = select(KetLuan).where(
            KetLuan.nguoi_phu_trach_id == user_id,
            KetLuan.is_deleted.is_(False),
        )
        if trang_thai:
            stmt = stmt.where(KetLuan.trang_thai == trang_thai)
        stmt = stmt.order_by(KetLuan.han_hoan_thanh.asc().nullslast(), KetLuan.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ──────────────────────────────────────────────────────────────────
    # CỦA ĐƠN VỊ
    # ──────────────────────────────────────────────────────────────────
    async def cua_don_vi(
        self,
        don_vi_id: UUID,
        user: TokenPayload,
    ) -> list[KetLuan]:
        # Permission check
        from meeting_service.dependencies import _has_view_all
        user_don_vi = UUID(user.don_vi_id) if user.don_vi_id else None
        if not _has_view_all(user):
            if not (user.is_lanh_dao and user_don_vi == don_vi_id):
                raise HTTPException(
                    status_code=403,
                    detail={"success": False, "error": {"code": "NO_PERMISSION",
                            "message": "Bạn không có quyền xem nhiệm vụ đơn vị này"}},
                )

        result = await self.db.execute(
            select(KetLuan)
            .where(
                KetLuan.don_vi_phu_trach_id == don_vi_id,
                KetLuan.is_deleted.is_(False),
            )
            .order_by(KetLuan.han_hoan_thanh.asc().nullslast())
        )
        return list(result.scalars().all())

    # ──────────────────────────────────────────────────────────────────
    # DASHBOARD CÁ NHÂN
    # ──────────────────────────────────────────────────────────────────
    async def dashboard_ca_nhan(self, user: TokenPayload) -> dict:
        user_id = UUID(user.sub)
        today = date.today()
        thang_dau = today.replace(day=1)

        # Cuộc họp được mời tháng này
        invited_stmt = (
            select(func.count(ThanhPhan.id))
            .join(CuocHop, CuocHop.id == ThanhPhan.cuoc_hop_id)
            .where(
                ThanhPhan.cong_chuc_id == user_id,
                CuocHop.ngay_hop >= thang_dau,
                CuocHop.is_deleted.is_(False),
            )
        )
        so_invited = (await self.db.execute(invited_stmt)).scalar() or 0

        # Đã điểm danh CO_MAT/DEN_MUON
        present_stmt = (
            select(func.count(DiemDanh.id))
            .join(CuocHop, CuocHop.id == DiemDanh.cuoc_hop_id)
            .where(
                DiemDanh.cong_chuc_id == user_id,
                DiemDanh.trang_thai.in_(["CO_MAT", "DEN_MUON"]),
                CuocHop.ngay_hop >= thang_dau,
            )
        )
        so_present = (await self.db.execute(present_stmt)).scalar() or 0

        # Vắng = invited - present (đã có row diem_danh) — tạm tính đơn giản
        absent_stmt = (
            select(func.count(DiemDanh.id))
            .join(CuocHop, CuocHop.id == DiemDanh.cuoc_hop_id)
            .where(
                DiemDanh.cong_chuc_id == user_id,
                DiemDanh.trang_thai.in_(["VANG_CO_PHEP", "VANG_KHONG_PHEP"]),
                CuocHop.ngay_hop >= thang_dau,
            )
        )
        so_absent = (await self.db.execute(absent_stmt)).scalar() or 0

        # Nhiệm vụ
        nv_dl_stmt = select(func.count(KetLuan.id)).where(
            KetLuan.nguoi_phu_trach_id == user_id,
            KetLuan.trang_thai.in_(["DANG_LAM", "CHUA_BAT_DAU"]),
            KetLuan.is_deleted.is_(False),
        )
        nv_dang_lam = (await self.db.execute(nv_dl_stmt)).scalar() or 0

        nv_qh_stmt = select(func.count(KetLuan.id)).where(
            KetLuan.nguoi_phu_trach_id == user_id,
            KetLuan.trang_thai == "TRE_HAN",
            KetLuan.is_deleted.is_(False),
        )
        nv_qua_han = (await self.db.execute(nv_qh_stmt)).scalar() or 0

        ty_le = round(so_present / so_invited * 100, 1) if so_invited else 0.0

        return {
            "so_cuoc_hop_thang_nay": so_invited,
            "so_cuoc_hop_tham_du": so_present,
            "so_lan_vang": so_absent,
            "ty_le_tham_du": ty_le,
            "nhiem_vu_dang_lam": nv_dang_lam,
            "nhiem_vu_qua_han": nv_qua_han,
        }

    # ──────────────────────────────────────────────────────────────────
    # DASHBOARD ĐƠN VỊ
    # ──────────────────────────────────────────────────────────────────
    async def dashboard_don_vi(
        self,
        don_vi_id: UUID,
        user: TokenPayload,
    ) -> dict:
        from meeting_service.dependencies import _has_view_all
        user_don_vi = UUID(user.don_vi_id) if user.don_vi_id else None
        if not _has_view_all(user):
            if not (user.is_lanh_dao and user_don_vi == don_vi_id):
                raise HTTPException(
                    status_code=403,
                    detail={"success": False, "error": {"code": "NO_PERMISSION",
                            "message": "Bạn không có quyền xem dashboard đơn vị này"}},
                )

        # Cuộc họp tổ chức bởi đơn vị
        ch_count = (await self.db.execute(
            select(func.count(CuocHop.id)).where(
                CuocHop.don_vi_to_chuc_id == don_vi_id,
                CuocHop.is_deleted.is_(False),
            )
        )).scalar() or 0

        # Nhiệm vụ giao cho đơn vị
        nv_total = (await self.db.execute(
            select(func.count(KetLuan.id)).where(
                KetLuan.don_vi_phu_trach_id == don_vi_id,
                KetLuan.is_deleted.is_(False),
            )
        )).scalar() or 0

        nv_done = (await self.db.execute(
            select(func.count(KetLuan.id)).where(
                KetLuan.don_vi_phu_trach_id == don_vi_id,
                KetLuan.trang_thai == "HOAN_THANH",
                KetLuan.is_deleted.is_(False),
            )
        )).scalar() or 0

        nv_overdue = (await self.db.execute(
            select(func.count(KetLuan.id)).where(
                KetLuan.don_vi_phu_trach_id == don_vi_id,
                KetLuan.trang_thai == "TRE_HAN",
                KetLuan.is_deleted.is_(False),
            )
        )).scalar() or 0

        ty_le = round(nv_done / nv_total * 100, 1) if nv_total else 0.0

        return {
            "don_vi_id": don_vi_id,
            "so_cuoc_hop": ch_count,
            "so_nhiem_vu_giao": nv_total,
            "so_nhiem_vu_hoan_thanh": nv_done,
            "so_nhiem_vu_qua_han": nv_overdue,
            "ty_le_hoan_thanh": ty_le,
        }

    # ──────────────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────────────
    async def _get(self, kl_id: UUID) -> KetLuan:
        result = await self.db.execute(
            select(KetLuan).where(
                KetLuan.id == kl_id, KetLuan.is_deleted.is_(False)
            )
        )
        kl = result.scalar_one_or_none()
        if kl is None:
            raise HTTPException(
                status_code=404,
                detail={"success": False, "error": {"code": "TASK_NOT_FOUND",
                        "message": "Không tìm thấy nhiệm vụ"}},
            )
        return kl
