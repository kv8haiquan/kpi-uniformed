"""
cuoc_hop_service.py
=====================
Business logic Module 1 — Quản lý cuộc họp.

Phân quyền:
- list visible: theo §7 HKG_PLATFORM_ROLES.md
- create: TDV/PDV/CCT/PCCT/SUPER_ADMIN/CHANH_VP/TRUONG_CNTT/THU_KY_HOP
- edit/cancel/send-invitation: chu_toa | thu_ky | SUPER_ADMIN | TRUONG_CNTT (qua require_can_edit_meeting)
"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.dependencies import _get_thu_ky_pham_vi, _has_view_all
from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.models.thanh_phan import ThanhPhan
from meeting_service.schemas.cuoc_hop import CuocHopCreate, CuocHopUpdate, XacNhanThamDu
from meeting_service.services.audit_log_service import ghi_audit
from meeting_service.services.notification_service import gui_thong_bao_bulk, gui_thong_bao
from shared.auth import TokenPayload


class CuocHopService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ──────────────────────────────────────────────────────────────────
    # CREATE
    # ──────────────────────────────────────────────────────────────────
    async def tao_moi(self, data: CuocHopCreate, user: TokenPayload) -> CuocHop:
        ch = CuocHop(
            tieu_de=data.tieu_de,
            mo_ta=data.mo_ta,
            khoi=data.khoi,
            hinh_thuc=data.hinh_thuc,
            ngay_hop=data.ngay_hop,
            gio_bat_dau=data.gio_bat_dau,
            gio_ket_thuc=data.gio_ket_thuc,
            dia_diem=data.dia_diem,
            don_vi_to_chuc_id=data.don_vi_to_chuc_id,
            chu_toa_id=data.chu_toa_id,
            thu_ky_id=data.thu_ky_id,
            created_by=UUID(user.sub),
        )
        self.db.add(ch)
        await self.db.flush()  # lấy ch.id

        # Insert thành phần
        for tp in data.thanh_phan:
            self.db.add(ThanhPhan(
                cuoc_hop_id=ch.id,
                cong_chuc_id=tp.cong_chuc_id,
                loai_tham_du=tp.loai_tham_du,
            ))

        # Audit
        await ghi_audit(
            self.db,
            hanh_dong="CREATE_MEETING",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="cuoc_hop",
            doi_tuong_id=ch.id,
            chi_tiet={
                "tieu_de": data.tieu_de,
                "khoi": data.khoi,
                "ngay_hop": data.ngay_hop.isoformat(),
                "so_thanh_phan": len(data.thanh_phan),
            },
        )
        await self.db.flush()
        return ch

    # ──────────────────────────────────────────────────────────────────
    # LIST
    # ──────────────────────────────────────────────────────────────────
    async def danh_sach(
        self,
        user: TokenPayload,
        *,
        page: int = 1,
        limit: int = 20,
        ngay_tu: Optional[Any] = None,
        ngay_den: Optional[Any] = None,
        don_vi_id: Optional[UUID] = None,
        khoi: Optional[str] = None,
        trang_thai: Optional[str] = None,
    ) -> dict:
        stmt = select(CuocHop).where(CuocHop.is_deleted.is_(False))

        # Filter
        if ngay_tu:
            stmt = stmt.where(CuocHop.ngay_hop >= ngay_tu)
        if ngay_den:
            stmt = stmt.where(CuocHop.ngay_hop <= ngay_den)
        if don_vi_id:
            stmt = stmt.where(CuocHop.don_vi_to_chuc_id == don_vi_id)
        if khoi:
            stmt = stmt.where(CuocHop.khoi == khoi)
        if trang_thai:
            stmt = stmt.where(CuocHop.trang_thai == trang_thai)

        # Permission filter
        stmt = await self._apply_visibility(stmt, user)

        # Pagination
        offset = (page - 1) * limit
        stmt = stmt.order_by(CuocHop.ngay_hop.desc(), CuocHop.gio_bat_dau.desc())
        stmt = stmt.limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        # Count thành phần cho từng cuoc_hop
        ch_ids = [ch.id for ch in items]
        so_tp_map: dict[UUID, int] = {}
        if ch_ids:
            cnt_stmt = (
                select(ThanhPhan.cuoc_hop_id, func.count(ThanhPhan.id))
                .where(ThanhPhan.cuoc_hop_id.in_(ch_ids))
                .group_by(ThanhPhan.cuoc_hop_id)
            )
            cnt_res = await self.db.execute(cnt_stmt)
            so_tp_map = {row[0]: row[1] for row in cnt_res.fetchall()}

        # Total count for pagination
        count_stmt = select(func.count()).select_from(
            (await self._apply_visibility(
                select(CuocHop.id).where(CuocHop.is_deleted.is_(False)), user
            )).subquery()
        )
        total = (await self.db.execute(count_stmt)).scalar() or 0

        return {
            "items": items,
            "so_thanh_phan_map": so_tp_map,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if limit else 1,
            },
        }

    async def _apply_visibility(self, stmt, user: TokenPayload):
        """Apply visibility filter theo §7 HKG_PLATFORM_ROLES.md."""
        if _has_view_all(user):
            return stmt

        user_id = UUID(user.sub)
        conditions = [
            CuocHop.chu_toa_id == user_id,
            CuocHop.thu_ky_id == user_id,
            CuocHop.id.in_(
                select(ThanhPhan.cuoc_hop_id).where(
                    ThanhPhan.cong_chuc_id == user_id
                )
            ),
        ]

        # Lãnh đạo đơn vị
        if user.is_lanh_dao and user.don_vi_id:
            try:
                conditions.append(
                    CuocHop.don_vi_to_chuc_id == UUID(user.don_vi_id)
                )
            except ValueError:
                pass

        # Thư ký đơn vị
        if "THU_KY_HOP" in (user.platform_roles or []):
            tk_dvs = await _get_thu_ky_pham_vi(user.sub, self.db)
            if tk_dvs:
                conditions.append(CuocHop.don_vi_to_chuc_id.in_(tk_dvs))

        return stmt.where(or_(*conditions))

    # ──────────────────────────────────────────────────────────────────
    # GET DETAIL — caller đã verify permission qua require_can_view_meeting
    # ──────────────────────────────────────────────────────────────────
    async def chi_tiet(self, cuoc_hop_id: UUID) -> CuocHop:
        result = await self.db.execute(
            select(CuocHop).where(
                CuocHop.id == cuoc_hop_id, CuocHop.is_deleted.is_(False)
            )
        )
        return result.scalar_one()

    # ──────────────────────────────────────────────────────────────────
    # UPDATE
    # ──────────────────────────────────────────────────────────────────
    async def cap_nhat(
        self, ch: CuocHop, data: CuocHopUpdate, user: TokenPayload
    ) -> CuocHop:
        changes = data.model_dump(exclude_unset=True)
        old_snap = {k: getattr(ch, k) for k in changes.keys()}

        for k, v in changes.items():
            setattr(ch, k, v)
        ch.updated_at = datetime.now(timezone.utc)

        # Notify thành phần nếu cuộc họp đã thông báo
        if ch.trang_thai == "DA_THONG_BAO":
            tp_ids = await self._lay_thanh_phan_ids(ch.id)
            await gui_thong_bao_bulk(
                self.db,
                nguoi_nhan_ids=tp_ids,
                tieu_de=f"Cuộc họp đã được cập nhật: {ch.tieu_de}",
                noi_dung="Thông tin cuộc họp đã có thay đổi.",
                sub_loai="THAY_DOI_HOP",
                link_url=f"/hop-khong-giay/chi-tiet/{ch.id}",
                doi_tuong_id=ch.id,
                muc_do="QUAN_TRONG",
            )

        await ghi_audit(
            self.db,
            hanh_dong="UPDATE_MEETING",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="cuoc_hop",
            doi_tuong_id=ch.id,
            chi_tiet={
                "old_value": {k: _serialize(v) for k, v in old_snap.items()},
                "new_value": {k: _serialize(v) for k, v in changes.items()},
            },
        )
        await self.db.flush()
        return ch

    # ──────────────────────────────────────────────────────────────────
    # CANCEL
    # ──────────────────────────────────────────────────────────────────
    async def huy(self, ch: CuocHop, ly_do: str, user: TokenPayload) -> CuocHop:
        if ch.trang_thai == "HUY":
            return ch
        was_dang_dien_ra = ch.trang_thai == "DANG_DIEN_RA"
        now = datetime.now(timezone.utc)
        ch.trang_thai = "HUY"
        ch.updated_at = now

        # BE_P6: cleanup phiên trình chiếu defensive nếu đang active
        # (cuộc họp bị hủy giữa lúc đang trình chiếu).
        from sqlalchemy import update
        from meeting_service.models.trang_thai_trinh_chieu import TrangThaiTrinhChieu
        await self.db.execute(
            update(TrangThaiTrinhChieu)
            .where(
                TrangThaiTrinhChieu.cuoc_hop_id == ch.id,
                TrangThaiTrinhChieu.is_active.is_(True),
            )
            .values(is_active=False, ket_thuc_luc=now, cap_nhat_luc=now)
        )

        tp_ids = await self._lay_thanh_phan_ids(ch.id)
        await gui_thong_bao_bulk(
            self.db,
            nguoi_nhan_ids=tp_ids,
            tieu_de=f"Cuộc họp đã hủy: {ch.tieu_de}",
            noi_dung=f"Lý do: {ly_do}",
            sub_loai="HUY_HOP",
            link_url=f"/hop-khong-giay/chi-tiet/{ch.id}",
            doi_tuong_id=ch.id,
            muc_do="QUAN_TRONG",
        )

        await ghi_audit(
            self.db,
            hanh_dong="CANCEL_MEETING",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="cuoc_hop",
            doi_tuong_id=ch.id,
            chi_tiet={"ly_do": ly_do},
        )
        await self.db.flush()

        # BE_P6: notify WS clients nếu cuộc họp bị hủy lúc đang DIEN_RA.
        # Không cần broadcast nếu cuộc họp chưa start (LEN_KE_HOACH/DA_THONG_BAO)
        # — không có WS client nào đang connect (REST chỉ cấp token cho
        # DA_THONG_BAO trở lên, nhưng client thường chỉ connect khi DANG_DIEN_RA).
        if was_dang_dien_ra:
            from meeting_service.services.presentation_singletons import manager
            await manager.close_channel(ch.id, reason="cancelled")

        return ch

    # ──────────────────────────────────────────────────────────────────
    # LIFECYCLE — BAT_DAU / KET_THUC (Phase 4.1 BE_P2)
    # ──────────────────────────────────────────────────────────────────
    async def bat_dau(self, ch: CuocHop, user: TokenPayload) -> CuocHop:
        """Chuyển trạng thái DA_THONG_BAO → DANG_DIEN_RA.

        Blocker của page-sync: client chỉ kết nối WS được khi cuộc họp ở
        trạng thái DA_THONG_BAO/DANG_DIEN_RA. State machine chặt:
        chỉ accept transition từ DA_THONG_BAO. Các status khác → 400.
        """
        from fastapi import HTTPException
        if ch.trang_thai != "DA_THONG_BAO":
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": {
                        "code": "INVALID_STATE_TRANSITION",
                        "message": (
                            f"Chỉ bắt đầu cuộc họp ở trạng thái DA_THONG_BAO. "
                            f"Hiện tại: {ch.trang_thai}."
                        ),
                    },
                },
            )

        ch.trang_thai = "DANG_DIEN_RA"
        ch.updated_at = datetime.now(timezone.utc)

        await ghi_audit(
            self.db,
            hanh_dong="CUOC_HOP_BAT_DAU",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="cuoc_hop",
            doi_tuong_id=ch.id,
        )
        await self.db.flush()
        return ch

    async def ket_thuc(self, ch: CuocHop, user: TokenPayload) -> CuocHop:
        """Chuyển trạng thái DANG_DIEN_RA → HOAN_THANH.

        Side effects:
        - Cleanup trang_thai_trinh_chieu (set is_active=FALSE + ket_thuc_luc=NOW)
          nếu phiên trình chiếu vẫn đang chạy.
        - Hook BE_P6: gọi manager.close_channel('completed') để broadcast
          meeting_ended tới mọi WS client + close graceful.
        """
        from fastapi import HTTPException
        from sqlalchemy import update
        from meeting_service.models.trang_thai_trinh_chieu import TrangThaiTrinhChieu

        if ch.trang_thai != "DANG_DIEN_RA":
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": {
                        "code": "INVALID_STATE_TRANSITION",
                        "message": (
                            f"Chỉ kết thúc cuộc họp ở trạng thái DANG_DIEN_RA. "
                            f"Hiện tại: {ch.trang_thai}."
                        ),
                    },
                },
            )

        now = datetime.now(timezone.utc)
        ch.trang_thai = "HOAN_THANH"
        ch.updated_at = now

        # Cleanup phiên trình chiếu nếu đang active.
        await self.db.execute(
            update(TrangThaiTrinhChieu)
            .where(
                TrangThaiTrinhChieu.cuoc_hop_id == ch.id,
                TrangThaiTrinhChieu.is_active.is_(True),
            )
            .values(is_active=False, ket_thuc_luc=now, cap_nhat_luc=now)
        )

        await ghi_audit(
            self.db,
            hanh_dong="CUOC_HOP_KET_THUC",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="cuoc_hop",
            doi_tuong_id=ch.id,
        )
        await self.db.flush()

        # BE_P6: notify mọi WS client cuộc họp đã kết thúc → close graceful.
        from meeting_service.services.presentation_singletons import manager
        await manager.close_channel(ch.id, reason="completed")

        return ch

    # ──────────────────────────────────────────────────────────────────
    # SEND INVITATION
    # ──────────────────────────────────────────────────────────────────
    async def gui_giay_moi(self, ch: CuocHop, user: TokenPayload) -> int:
        ch.trang_thai = "DA_THONG_BAO"
        ch.updated_at = datetime.now(timezone.utc)

        tp_ids = await self._lay_thanh_phan_ids(ch.id)
        so_gui = await gui_thong_bao_bulk(
            self.db,
            nguoi_nhan_ids=tp_ids,
            tieu_de=f"Giấy mời họp: {ch.tieu_de}",
            noi_dung=f"Mời tham dự cuộc họp ngày {ch.ngay_hop} lúc {ch.gio_bat_dau}.",
            sub_loai="GIAY_MOI_HOP",
            link_url=f"/hop-khong-giay/chi-tiet/{ch.id}",
            doi_tuong_id=ch.id,
            muc_do="BINH_THUONG",
        )

        await ghi_audit(
            self.db,
            hanh_dong="SEND_INVITATION",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="cuoc_hop",
            doi_tuong_id=ch.id,
            chi_tiet={"so_giay_moi": so_gui},
        )
        await self.db.flush()
        return so_gui

    # ──────────────────────────────────────────────────────────────────
    # SỬA THÀNH PHẦN (replace list — diff add/remove)
    # ──────────────────────────────────────────────────────────────────
    async def sua_thanh_phan(
        self,
        ch: CuocHop,
        new_list: list,  # list[ThanhPhanCreate] from schema
        user: TokenPayload,
    ) -> dict:
        """
        Replace toàn bộ thành phần. Diff:
        - added: cong_chuc_id mới → INSERT + (notify GIAY_MOI nếu DA_THONG_BAO)
        - removed: KHÔNG còn trong new_list → DELETE
                   (KHÔNG cho remove chu_toa_id/thu_ky_id → 409)
        - kept (overlap): update loai_tham_du nếu đổi
        """
        from fastapi import HTTPException

        # Lấy current
        result = await self.db.execute(
            select(ThanhPhan).where(ThanhPhan.cuoc_hop_id == ch.id)
        )
        current = list(result.scalars().all())
        current_map = {tp.cong_chuc_id: tp for tp in current}

        new_map = {tp.cong_chuc_id: tp for tp in new_list}
        new_ids = set(new_map.keys())
        current_ids = set(current_map.keys())

        added_ids = new_ids - current_ids
        removed_ids = current_ids - new_ids
        kept_ids = current_ids & new_ids

        # Block remove chu_toa/thu_ky
        protected = {ch.chu_toa_id}
        if ch.thu_ky_id:
            protected.add(ch.thu_ky_id)
        violated = removed_ids & protected
        if violated:
            raise HTTPException(
                status_code=409,
                detail={"success": False, "error": {"code": "CANNOT_REMOVE_CORE",
                        "message": (
                            f"Không thể bỏ chủ tọa/thư ký khỏi thành phần "
                            f"({len(violated)} người). Đổi vai trò trước nếu cần."
                        )}},
            )

        # 1. Add
        added_objs = []
        for cc_id in added_ids:
            new_tp = new_map[cc_id]
            tp = ThanhPhan(
                cuoc_hop_id=ch.id,
                cong_chuc_id=cc_id,
                loai_tham_du=new_tp.loai_tham_du,
            )
            self.db.add(tp)
            added_objs.append(tp)

        # 2. Remove
        for cc_id in removed_ids:
            await self.db.delete(current_map[cc_id])

        # 3. Update loai_tham_du nếu đổi (kept)
        for cc_id in kept_ids:
            existing = current_map[cc_id]
            new_tp = new_map[cc_id]
            if existing.loai_tham_du != new_tp.loai_tham_du:
                existing.loai_tham_du = new_tp.loai_tham_du

        await self.db.flush()

        # 4. Notify added users (chỉ nếu cuộc họp đã DA_THONG_BAO trở lên)
        if added_ids and ch.trang_thai in ("DA_THONG_BAO", "DANG_DIEN_RA"):
            await gui_thong_bao_bulk(
                self.db,
                nguoi_nhan_ids=list(added_ids),
                tieu_de=f"Bạn vừa được thêm vào cuộc họp: {ch.tieu_de}",
                noi_dung=f"Cuộc họp diễn ra ngày {ch.ngay_hop} lúc {ch.gio_bat_dau}.",
                sub_loai="GIAY_MOI_HOP",
                link_url=f"/hop-khong-giay/chi-tiet/{ch.id}",
                doi_tuong_id=ch.id,
                muc_do="QUAN_TRONG",
            )

        # 5. Audit
        if added_ids:
            await ghi_audit(
                self.db,
                hanh_dong="ADD_PARTICIPANT",
                nguoi_thuc_hien_id=UUID(user.sub),
                doi_tuong_loai="cuoc_hop",
                doi_tuong_id=ch.id,
                chi_tiet={"so_them": len(added_ids),
                          "cong_chuc_ids": [str(i) for i in added_ids]},
            )
        if removed_ids:
            await ghi_audit(
                self.db,
                hanh_dong="REMOVE_PARTICIPANT",
                nguoi_thuc_hien_id=UUID(user.sub),
                doi_tuong_loai="cuoc_hop",
                doi_tuong_id=ch.id,
                chi_tiet={"so_bo": len(removed_ids),
                          "cong_chuc_ids": [str(i) for i in removed_ids]},
            )

        ch.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

        return {
            "so_them": len(added_ids),
            "so_bo": len(removed_ids),
            "tong_thanh_phan": len(new_ids),
        }

    # ──────────────────────────────────────────────────────────────────
    # CONFIRM ATTENDANCE
    # ──────────────────────────────────────────────────────────────────
    async def xac_nhan_tham_du(
        self, cuoc_hop_id: UUID, payload: XacNhanThamDu, user: TokenPayload
    ) -> ThanhPhan:
        user_id = UUID(user.sub)
        result = await self.db.execute(
            select(ThanhPhan).where(
                and_(
                    ThanhPhan.cuoc_hop_id == cuoc_hop_id,
                    ThanhPhan.cong_chuc_id == user_id,
                )
            )
        )
        tp = result.scalar_one_or_none()
        if tp is None:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=403,
                detail={"success": False, "error": {"code": "NOT_INVITED",
                        "message": "Bạn không có trong danh sách mời cuộc họp này"}},
            )

        tp.xac_nhan = payload.xac_nhan
        tp.nguoi_uy_quyen_id = payload.nguoi_uy_quyen_id
        tp.ghi_chu_xac_nhan = payload.ghi_chu
        tp.thoi_gian_xac_nhan = datetime.now(timezone.utc)

        await ghi_audit(
            self.db,
            hanh_dong="CONFIRM_ATTENDANCE",
            nguoi_thuc_hien_id=user_id,
            doi_tuong_loai="cuoc_hop",
            doi_tuong_id=cuoc_hop_id,
            chi_tiet={"xac_nhan": payload.xac_nhan},
        )
        await self.db.flush()
        return tp

    # ──────────────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────────────
    async def _lay_thanh_phan_ids(self, cuoc_hop_id: UUID) -> list[UUID]:
        result = await self.db.execute(
            select(ThanhPhan.cong_chuc_id).where(ThanhPhan.cuoc_hop_id == cuoc_hop_id)
        )
        return [row[0] for row in result.fetchall()]


def _serialize(v):
    """JSON-safe serialize cho audit log."""
    if v is None:
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()
    if hasattr(v, "hex"):
        return str(v)
    return v
