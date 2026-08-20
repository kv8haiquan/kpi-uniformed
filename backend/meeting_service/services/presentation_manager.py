"""PresentationManager — orchestration layer cho Phase 4.1 page-sync.

Threat model:
- Mọi inbound event check chu_toa trước khi broadcast — silent reject
  (KHÔNG send error event) cho non-host events để giảm noise + tránh
  leak thông tin về phân quyền.
- Debounce 150ms cho page_change/zoom_change theo (channel, user, type)
  — nhiều event gần nhau chỉ broadcast event cuối → giảm tải mạng + UX
  mượt hơn cho client.
- Validate cuoc_hop.trang_thai='DANG_DIEN_RA' trước presentation_start
  (DA_THONG_BAO chỉ cho phép pre-load tài liệu, KHÔNG bắt đầu trình chiếu).
- Audit log 3 events business-value (PRESENTATION_START/END, DOCUMENT_OPEN);
  page_change/zoom_change KHÔNG audit để tránh flood DB (D11 plan v3.1).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.models.tai_lieu import TaiLieu
from meeting_service.models.trang_thai_trinh_chieu import TrangThaiTrinhChieu
from meeting_service.services.audit_log_service import ghi_audit
from meeting_service.services.phan_quyen_tai_lieu import (
    CONG_KHAI,
    chuan_hoa as chuan_hoa_phan_quyen,
)
from meeting_service.services.broadcast_backend import BroadcastBackend, WebSocketLike


logger = logging.getLogger("hkg.presentation")

DEBOUNCE_SECONDS = 0.15  # 150ms (D13 plan v3.1)


def channel_for(cuoc_hop_id: UUID) -> str:
    return f"meeting:{cuoc_hop_id}"


class PresentationManager:
    """High-level service: validate + DB UPSERT + debounce + broadcast routing."""

    def __init__(self, backend: BroadcastBackend):
        self.backend = backend
        # Key: (channel, user_id, event_type) → asyncio.Task chờ debounce
        self._debounce_tasks: dict[tuple[str, UUID, str], asyncio.Task] = {}

    # ──────────────────────────────────────────────────────────────────
    # Entry point
    # ──────────────────────────────────────────────────────────────────
    async def handle_inbound_event(
        self,
        db: AsyncSession,
        cuoc_hop_id: UUID,
        user_id: UUID,
        event: dict,
        ws: WebSocketLike,
    ) -> None:
        """Process 1 inbound event từ chu_toa.

        Silent reject (không send error event) nếu:
        - Cuoc hop không tồn tại / đã xóa
        - User KHÔNG phải chu_toa của cuộc họp
        Trả error event nếu:
        - Sai event type
        - Tài liệu không hợp lệ (document_open / page_change cho doc khác meeting)
        """
        event_type = event.get("type")
        if not event_type:
            return

        ch = await self._load_meeting(db, cuoc_hop_id)
        if ch is None:
            return  # silent — meeting bị xóa giữa chừng

        if ch.chu_toa_id != user_id:
            return  # silent reject non-host

        channel = channel_for(cuoc_hop_id)

        if event_type == "presentation_start":
            await self._handle_presentation_start(db, ch, event, channel, user_id)
        elif event_type == "presentation_end":
            await self._handle_presentation_end(db, ch, channel, user_id)
        elif event_type == "document_open":
            await self._handle_document_open(db, ch, event, channel, user_id, ws)
        elif event_type == "page_change":
            await self._handle_page_change(db, ch, event, channel, user_id)
        elif event_type == "zoom_change":
            await self._handle_zoom_change(db, ch, event, channel, user_id)
        else:
            await ws.send_json({
                "type": "error",
                "code": "UNKNOWN_EVENT",
                "message": f"Event type không hợp lệ: {event_type}",
            })

    async def close_channel(self, cuoc_hop_id: UUID, reason: str = "completed") -> None:
        """Hook khi cuộc họp kết thúc/hủy — broadcast meeting_ended + close all."""
        await self.backend.close_channel(
            channel_for(cuoc_hop_id),
            {"type": "meeting_ended", "reason": reason},
        )

    # ──────────────────────────────────────────────────────────────────
    # Lifecycle handlers
    # ──────────────────────────────────────────────────────────────────
    async def _handle_presentation_start(
        self,
        db: AsyncSession,
        ch: CuocHop,
        event: dict,
        channel: str,
        user_id: UUID,
    ) -> None:
        # Yêu cầu cuoc_hop ở DANG_DIEN_RA — DA_THONG_BAO chỉ pre-load.
        if ch.trang_thai != "DANG_DIEN_RA":
            return  # silent — host chưa bấm "Bắt đầu cuộc họp"

        tai_lieu_id = self._uuid_from(event.get("tai_lieu_id"))
        if tai_lieu_id is None:
            return
        # Validate tài liệu thuộc cuộc họp + chưa xóa
        if not await self._validate_tai_lieu(db, ch.id, tai_lieu_id):
            return

        page = max(1, int(event.get("page") or 1))
        now = datetime.now(timezone.utc)

        await db.execute(sa_text("""
            INSERT INTO meeting.trang_thai_trinh_chieu
                (cuoc_hop_id, tai_lieu_hien_tai_id, trang_hien_tai,
                 is_active, bat_dau_luc, ket_thuc_luc,
                 cap_nhat_luc, cap_nhat_boi_id)
            VALUES (:ch, :tl, :page, TRUE, :now, NULL, :now, :uid)
            ON CONFLICT (cuoc_hop_id) DO UPDATE
                SET tai_lieu_hien_tai_id = EXCLUDED.tai_lieu_hien_tai_id,
                    trang_hien_tai = EXCLUDED.trang_hien_tai,
                    is_active = TRUE,
                    bat_dau_luc = EXCLUDED.bat_dau_luc,
                    ket_thuc_luc = NULL,
                    cap_nhat_luc = EXCLUDED.cap_nhat_luc,
                    cap_nhat_boi_id = EXCLUDED.cap_nhat_boi_id
        """), {"ch": str(ch.id), "tl": str(tai_lieu_id), "page": page,
               "now": now, "uid": str(user_id)})
        await ghi_audit(
            db,
            hanh_dong="PRESENTATION_START",
            nguoi_thuc_hien_id=user_id,
            doi_tuong_loai="cuoc_hop",
            doi_tuong_id=ch.id,
            chi_tiet={"tai_lieu_id": str(tai_lieu_id), "page": page},
        )
        await db.flush()

        await self.backend.broadcast(channel, {
            "type": "presentation_started",
            "tai_lieu_id": str(tai_lieu_id),
            "page": page,
            "bat_dau_luc": now.isoformat(),
        })

    async def _handle_presentation_end(
        self,
        db: AsyncSession,
        ch: CuocHop,
        channel: str,
        user_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc)
        result = await db.execute(sa_text("""
            UPDATE meeting.trang_thai_trinh_chieu
               SET is_active = FALSE,
                   ket_thuc_luc = :now,
                   cap_nhat_luc = :now,
                   cap_nhat_boi_id = :uid
             WHERE cuoc_hop_id = :ch AND is_active = TRUE
            RETURNING id
        """), {"ch": str(ch.id), "now": now, "uid": str(user_id)})
        if result.scalar_one_or_none() is None:
            return  # KHÔNG có phiên active — no-op

        await ghi_audit(
            db,
            hanh_dong="PRESENTATION_END",
            nguoi_thuc_hien_id=user_id,
            doi_tuong_loai="cuoc_hop",
            doi_tuong_id=ch.id,
        )
        await db.flush()

        await self.backend.broadcast(channel, {
            "type": "presentation_ended",
            "ket_thuc_luc": now.isoformat(),
        })

    async def _handle_document_open(
        self,
        db: AsyncSession,
        ch: CuocHop,
        event: dict,
        channel: str,
        user_id: UUID,
        ws: WebSocketLike,
    ) -> None:
        tai_lieu_id = self._uuid_from(event.get("tai_lieu_id"))
        if tai_lieu_id is None:
            return
        loi = await self._kiem_tai_lieu(db, ch.id, tai_lieu_id)
        if loi is not None:
            await ws.send_json({
                "type": "error", "code": loi[0], "message": loi[1],
            })
            return

        page = max(1, int(event.get("page") or 1))
        now = datetime.now(timezone.utc)

        await db.execute(sa_text("""
            UPDATE meeting.trang_thai_trinh_chieu
               SET tai_lieu_hien_tai_id = :tl,
                   trang_hien_tai = :page,
                   cap_nhat_luc = :now,
                   cap_nhat_boi_id = :uid
             WHERE cuoc_hop_id = :ch
        """), {"ch": str(ch.id), "tl": str(tai_lieu_id), "page": page,
               "now": now, "uid": str(user_id)})

        await ghi_audit(
            db,
            hanh_dong="DOCUMENT_OPEN",
            nguoi_thuc_hien_id=user_id,
            doi_tuong_loai="cuoc_hop",
            doi_tuong_id=ch.id,
            chi_tiet={"tai_lieu_id": str(tai_lieu_id), "page": page},
        )
        await db.flush()

        await self.backend.broadcast(channel, {
            "type": "document_changed",
            "tai_lieu_id": str(tai_lieu_id),
            "page": page,
        })

    # ──────────────────────────────────────────────────────────────────
    # Debounced: page_change / zoom_change (KHÔNG audit, KHÔNG flood DB)
    # ──────────────────────────────────────────────────────────────────
    async def _handle_page_change(
        self,
        db: AsyncSession,
        ch: CuocHop,
        event: dict,
        channel: str,
        user_id: UUID,
    ) -> None:
        page = int(event.get("page") or 0)
        if page <= 0:
            return
        await self._schedule_debounced(
            channel,
            user_id,
            "page_change",
            self._apply_page_change,
            (db, ch.id, user_id, page, channel),
        )

    async def _handle_zoom_change(
        self,
        db: AsyncSession,
        ch: CuocHop,
        event: dict,
        channel: str,
        user_id: UUID,
    ) -> None:
        zoom_raw = event.get("zoom")
        if zoom_raw is None:
            return
        try:
            zoom = Decimal(str(zoom_raw)).quantize(Decimal("0.01"))
        except Exception:
            return
        if zoom < Decimal("0.5") or zoom > Decimal("4.0"):
            return
        await self._schedule_debounced(
            channel,
            user_id,
            "zoom_change",
            self._apply_zoom_change,
            (db, ch.id, user_id, zoom, channel),
        )

    async def _apply_page_change(
        self,
        db: AsyncSession,
        ch_id: UUID,
        user_id: UUID,
        page: int,
        channel: str,
    ) -> None:
        await db.execute(sa_text("""
            UPDATE meeting.trang_thai_trinh_chieu
               SET trang_hien_tai = :page,
                   cap_nhat_luc = NOW(),
                   cap_nhat_boi_id = :uid
             WHERE cuoc_hop_id = :ch
        """), {"ch": str(ch_id), "page": page, "uid": str(user_id)})
        await db.flush()
        await self.backend.broadcast(channel, {"type": "page_changed", "page": page})

    async def _apply_zoom_change(
        self,
        db: AsyncSession,
        ch_id: UUID,
        user_id: UUID,
        zoom: Decimal,
        channel: str,
    ) -> None:
        await db.execute(sa_text("""
            UPDATE meeting.trang_thai_trinh_chieu
               SET zoom_level = :zoom,
                   cap_nhat_luc = NOW(),
                   cap_nhat_boi_id = :uid
             WHERE cuoc_hop_id = :ch
        """), {"ch": str(ch_id), "zoom": str(zoom), "uid": str(user_id)})
        await db.flush()
        await self.backend.broadcast(channel, {"type": "zoom_changed", "zoom": str(zoom)})

    # ──────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────
    async def _schedule_debounced(
        self,
        channel: str,
        user_id: UUID,
        event_type: str,
        action: Any,
        args: tuple,
    ) -> None:
        """Cancel pending task cùng key, schedule task mới sau DEBOUNCE_SECONDS."""
        key = (channel, user_id, event_type)
        prior = self._debounce_tasks.get(key)
        if prior and not prior.done():
            prior.cancel()

        async def _runner():
            try:
                await asyncio.sleep(DEBOUNCE_SECONDS)
                await action(*args)
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                logger.warning("debounced %s failed: %s", event_type, exc)
            finally:
                # Self-cleanup nếu key vẫn trỏ vào task của mình
                if self._debounce_tasks.get(key) is asyncio.current_task():
                    self._debounce_tasks.pop(key, None)

        self._debounce_tasks[key] = asyncio.create_task(_runner())

    @staticmethod
    def _uuid_from(value: Any) -> Optional[UUID]:
        if value is None:
            return None
        if isinstance(value, UUID):
            return value
        try:
            return UUID(str(value))
        except (ValueError, TypeError):
            return None

    async def _load_meeting(
        self, db: AsyncSession, cuoc_hop_id: UUID
    ) -> Optional[CuocHop]:
        res = await db.execute(
            select(CuocHop).where(
                CuocHop.id == cuoc_hop_id,
                CuocHop.is_deleted.is_(False),
            )
        )
        return res.scalar_one_or_none()

    async def _kiem_tai_lieu(
        self, db: AsyncSession, cuoc_hop_id: UUID, tai_lieu_id: UUID
    ) -> Optional[tuple[str, str]]:
        """Trả None nếu trình chiếu được, ngược lại (mã lỗi, thông điệp).

        Tài liệu hạn chế (G5.4) KHÔNG trình chiếu được, dù chủ toạ có quyền
        xem nó: trình chiếu là đẩy nội dung ra cả phòng họp, trong đó có người
        không đủ mức. Chặn ngay tại thao tác của chủ toạ để họ biết mà chọn
        cách khác, thay vì để cả phòng nhận 403 khi tải nội dung.
        """
        res = await db.execute(
            select(TaiLieu.phan_quyen).where(
                TaiLieu.id == tai_lieu_id,
                TaiLieu.cuoc_hop_id == cuoc_hop_id,
                TaiLieu.is_deleted.is_(False),
            )
        )
        muc = res.scalar_one_or_none()
        if muc is None:
            return ("DOCUMENT_DELETED",
                    "Tài liệu không tồn tại hoặc không thuộc cuộc họp này")
        if chuan_hoa_phan_quyen(muc) != CONG_KHAI:
            return ("DOCUMENT_RESTRICTED",
                    "Tài liệu đang ở mức hạn chế người xem nên không trình "
                    "chiếu được — hạ mức về công khai nội bộ nếu cần chiếu "
                    "cho cả phòng họp")
        return None

    async def _validate_tai_lieu(
        self, db: AsyncSession, cuoc_hop_id: UUID, tai_lieu_id: UUID
    ) -> bool:
        return await self._kiem_tai_lieu(db, cuoc_hop_id, tai_lieu_id) is None
