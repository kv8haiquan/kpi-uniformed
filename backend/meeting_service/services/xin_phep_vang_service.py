"""
xin_phep_vang_service.py
==========================
Module 5 — Xin phép vắng. Logic gửi đơn / duyệt / auto-approve.

Auto-approve qua APScheduler (xem `meeting_service/scheduler.py`):
- Chạy interval 10 phút
- Tìm các đơn `CHO_DUYET` mà `created_at + 4h < now` → set `TU_DONG_DUYET`
- Test gọi function `auto_approve_overdue_logic(...)` trực tiếp
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.models.thanh_phan import ThanhPhan
from meeting_service.models.xin_phep_vang import XinPhepVang
from meeting_service.schemas.xin_phep_vang import (
    XinPhepVangCreate,
    XinPhepVangDuyet,
)
from meeting_service.services.audit_log_service import ghi_audit
from meeting_service.services.notification_service import gui_thong_bao
from shared.auth import TokenPayload


AUTO_APPROVE_AFTER_HOURS = 4


class XinPhepVangService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ──────────────────────────────────────────────────────────────────
    # CREATE — CBCC gửi đơn
    # ──────────────────────────────────────────────────────────────────
    async def create(
        self, data: XinPhepVangCreate, user: TokenPayload
    ) -> XinPhepVang:
        # CBCC phải có trong thành phần cuộc họp
        user_id = UUID(user.sub)
        res = await self.db.execute(
            select(ThanhPhan.id).where(
                ThanhPhan.cuoc_hop_id == data.cuoc_hop_id,
                ThanhPhan.cong_chuc_id == user_id,
            )
        )
        if res.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=403,
                detail={"success": False, "error": {"code": "NOT_INVITED",
                        "message": "Bạn không có trong danh sách mời cuộc họp này"}},
            )

        # Check trùng (UNIQUE constraint sẽ raise — handle gracefully)
        res = await self.db.execute(
            select(XinPhepVang).where(
                XinPhepVang.cuoc_hop_id == data.cuoc_hop_id,
                XinPhepVang.cong_chuc_id == user_id,
            )
        )
        existing = res.scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail={"success": False, "error": {"code": "ALREADY_REQUESTED",
                        "message": "Bạn đã gửi đơn xin vắng cho cuộc họp này"}},
            )

        # Lấy cuoc_hop để có chu_toa_id
        ch_res = await self.db.execute(
            select(CuocHop).where(CuocHop.id == data.cuoc_hop_id)
        )
        ch = ch_res.scalar_one_or_none()
        if ch is None:
            raise HTTPException(
                status_code=404,
                detail={"success": False, "error": {"code": "MEETING_NOT_FOUND",
                        "message": "Không tìm thấy cuộc họp"}},
            )

        xpv = XinPhepVang(
            cuoc_hop_id=data.cuoc_hop_id,
            cong_chuc_id=user_id,
            ly_do=data.ly_do,
            nguoi_du_thay_id=data.nguoi_du_thay_id,
            minio_key=data.minio_key,
            trang_thai="CHO_DUYET",
        )
        self.db.add(xpv)
        await self.db.flush()

        # Notify chu_toa
        await gui_thong_bao(
            self.db,
            nguoi_nhan_id=ch.chu_toa_id,
            tieu_de=f"Đơn xin vắng họp: {ch.tieu_de}",
            noi_dung=f"CBCC {user.ho_ten or user.ma_cc} xin vắng. Lý do: {data.ly_do[:200]}",
            sub_loai="XIN_PHEP_CHO_DUYET",
            link_url=f"/hop-khong-giay/chi-tiet/{ch.id}",
            doi_tuong_id=xpv.id,
            muc_do="QUAN_TRONG",
        )

        await ghi_audit(
            self.db,
            hanh_dong="REQUEST_LEAVE",
            nguoi_thuc_hien_id=user_id,
            doi_tuong_loai="xin_phep_vang",
            doi_tuong_id=xpv.id,
            chi_tiet={
                "cuoc_hop_id": str(ch.id),
                "ly_do": data.ly_do[:500],
            },
        )
        await self.db.flush()
        return xpv

    # ──────────────────────────────────────────────────────────────────
    # LIST CHO_DUYET — Chủ tọa xem
    # ──────────────────────────────────────────────────────────────────
    async def list_cho_duyet(self, user: TokenPayload) -> list[XinPhepVang]:
        user_id = UUID(user.sub)
        # Đơn của các cuộc họp mà user là chu_toa
        result = await self.db.execute(
            select(XinPhepVang)
            .join(CuocHop, CuocHop.id == XinPhepVang.cuoc_hop_id)
            .where(
                XinPhepVang.trang_thai == "CHO_DUYET",
                CuocHop.chu_toa_id == user_id,
            )
            .order_by(XinPhepVang.created_at.desc())
        )
        return list(result.scalars().all())

    # ──────────────────────────────────────────────────────────────────
    # DUYET / TU CHOI
    # ──────────────────────────────────────────────────────────────────
    async def duyet(
        self,
        xpv_id: UUID,
        payload: XinPhepVangDuyet,
        user: TokenPayload,
    ) -> XinPhepVang:
        user_id = UUID(user.sub)

        # Lấy đơn + cuộc họp
        result = await self.db.execute(
            select(XinPhepVang).where(XinPhepVang.id == xpv_id)
        )
        xpv = result.scalar_one_or_none()
        if xpv is None:
            raise HTTPException(
                status_code=404,
                detail={"success": False, "error": {"code": "LEAVE_NOT_FOUND",
                        "message": "Không tìm thấy đơn"}},
            )
        if xpv.trang_thai != "CHO_DUYET":
            raise HTTPException(
                status_code=409,
                detail={"success": False, "error": {"code": "ALREADY_DECIDED",
                        "message": "Đơn đã được xử lý"}},
            )

        ch_res = await self.db.execute(
            select(CuocHop).where(CuocHop.id == xpv.cuoc_hop_id)
        )
        ch = ch_res.scalar_one()
        if ch.chu_toa_id != user_id and not (
            user.is_admin or user.vai_tro in ("SUPER_ADMIN", "ADMIN")
        ):
            raise HTTPException(
                status_code=403,
                detail={"success": False, "error": {"code": "NO_PERMISSION",
                        "message": "Chỉ chủ tọa được duyệt đơn"}},
            )

        xpv.trang_thai = payload.quyet_dinh
        xpv.nguoi_duyet_id = user_id
        xpv.thoi_gian_duyet = datetime.now(timezone.utc)
        xpv.ly_do_tu_choi = (
            payload.ly_do_tu_choi if payload.quyet_dinh == "TU_CHOI" else None
        )
        xpv.updated_at = datetime.now(timezone.utc)

        # Notify CBCC nộp đơn
        sub_loai = "XIN_PHEP_DA_DUYET" if payload.quyet_dinh == "DA_DUYET" else "XIN_PHEP_TU_CHOI"
        await gui_thong_bao(
            self.db,
            nguoi_nhan_id=xpv.cong_chuc_id,
            tieu_de=f"Đơn xin vắng họp đã được {('duyệt' if payload.quyet_dinh == 'DA_DUYET' else 'từ chối')}",
            noi_dung=payload.ly_do_tu_choi or "Đơn đã được duyệt.",
            sub_loai=sub_loai,
            link_url=f"/hop-khong-giay/chi-tiet/{ch.id}",
            doi_tuong_id=xpv.id,
        )

        verb = "APPROVE_LEAVE" if payload.quyet_dinh == "DA_DUYET" else "REJECT_LEAVE"
        await ghi_audit(
            self.db,
            hanh_dong=verb,
            nguoi_thuc_hien_id=user_id,
            doi_tuong_loai="xin_phep_vang",
            doi_tuong_id=xpv.id,
            chi_tiet={
                "cuoc_hop_id": str(ch.id),
                "ly_do_tu_choi": payload.ly_do_tu_choi,
            },
        )
        await self.db.flush()
        return xpv

    # ──────────────────────────────────────────────────────────────────
    # AUTO-APPROVE LOGIC (gọi từ scheduler hoặc test trực tiếp)
    # ──────────────────────────────────────────────────────────────────
    async def auto_approve_overdue(self) -> int:
        """Auto duyệt các đơn CHO_DUYET quá AUTO_APPROVE_AFTER_HOURS.
        Trả về số đơn được auto duyệt.
        """
        threshold = datetime.now(timezone.utc) - timedelta(
            hours=AUTO_APPROVE_AFTER_HOURS
        )
        result = await self.db.execute(
            select(XinPhepVang).where(
                XinPhepVang.trang_thai == "CHO_DUYET",
                XinPhepVang.created_at < threshold,
            )
        )
        overdue = list(result.scalars().all())

        for xpv in overdue:
            xpv.trang_thai = "TU_DONG_DUYET"
            xpv.auto_approved = True
            xpv.thoi_gian_duyet = datetime.now(timezone.utc)
            xpv.updated_at = datetime.now(timezone.utc)

            await gui_thong_bao(
                self.db,
                nguoi_nhan_id=xpv.cong_chuc_id,
                tieu_de="Đơn xin vắng họp đã được tự động duyệt",
                noi_dung=f"Đơn quá {AUTO_APPROVE_AFTER_HOURS}h chưa duyệt — hệ thống tự đồng ý.",
                sub_loai="XIN_PHEP_TU_DONG_DUYET",
                link_url=f"/hop-khong-giay/chi-tiet/{xpv.cuoc_hop_id}",
                doi_tuong_id=xpv.id,
            )

            await ghi_audit(
                self.db,
                hanh_dong="AUTO_APPROVE_LEAVE",
                nguoi_thuc_hien_id=xpv.cong_chuc_id,  # ai cũng được — system
                doi_tuong_loai="xin_phep_vang",
                doi_tuong_id=xpv.id,
                chi_tiet={"timeout_hours": AUTO_APPROVE_AFTER_HOURS},
            )

        await self.db.flush()
        return len(overdue)
