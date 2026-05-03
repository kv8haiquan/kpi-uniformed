"""
meeting_service/scheduler.py
=============================
APScheduler in-process — thay Celery+Redis cho MVP single-server.

Jobs:
- auto_approve_xin_phep_vang  interval 10 phút   (Module 5)
- nhac_hop_3_tang             interval 1 phút    (Module 1+2)
- nhac_han_ket_luan           cron 8AM hàng ngày (Module 10)
- mark_tre_han_ket_luan       cron 0AM hàng ngày (Module 10)

Logic chi tiết tách ra `services/scheduler_helpers.py` để test trực tiếp với
freezegun (không cần đợi APScheduler tick).

Lý do chọn APScheduler thay Celery:
1. Codebase chưa có Celery/Redis broker — tránh setup infra mới
2. Single-server deployment OK cho MVP HKG (~200 users active concurrent)
3. APScheduler chạy in-process trong FastAPI lifespan → 0 cấu hình thêm
4. Multi-server: migrate sang Celery+Redis ở phase scale-out
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from meeting_service.dependencies import session_factory
from meeting_service.services.scheduler_helpers import (
    mark_tre_han_logic,
    nhac_han_ket_luan_logic,
    nhac_hop_3_tang_logic,
)
from meeting_service.services.xin_phep_vang_service import XinPhepVangService


logger = logging.getLogger(__name__)


_scheduler: AsyncIOScheduler | None = None


# ──────────────────────────────────────────────────────────────────────
# JOB WRAPPERS — open session + commit + log
# ──────────────────────────────────────────────────────────────────────

async def auto_approve_xin_phep_vang_job() -> int:
    async with session_factory() as session:
        service = XinPhepVangService(session)
        count = await service.auto_approve_overdue()
        await session.commit()
        if count:
            logger.info("auto_approve_xin_phep_vang: %d đơn auto-duyệt", count)
        return count


async def nhac_hop_3_tang_job() -> int:
    async with session_factory() as session:
        count = await nhac_hop_3_tang_logic(session)
        await session.commit()
        if count:
            logger.info("nhac_hop_3_tang: %d notif đã gửi", count)
        return count


async def nhac_han_ket_luan_job() -> int:
    async with session_factory() as session:
        count = await nhac_han_ket_luan_logic(session)
        await session.commit()
        if count:
            logger.info("nhac_han_ket_luan: %d notif đã gửi", count)
        return count


async def mark_tre_han_ket_luan_job() -> int:
    async with session_factory() as session:
        count = await mark_tre_han_logic(session)
        await session.commit()
        if count:
            logger.info("mark_tre_han_ket_luan: %d kết luận chuyển TRE_HAN", count)
        return count


# ──────────────────────────────────────────────────────────────────────
# LIFECYCLE
# ──────────────────────────────────────────────────────────────────────

def start_scheduler() -> AsyncIOScheduler:
    """Khởi động scheduler. Gọi từ FastAPI lifespan startup."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    sched = AsyncIOScheduler(timezone="UTC")

    sched.add_job(
        auto_approve_xin_phep_vang_job,
        trigger=IntervalTrigger(minutes=10),
        id="auto_approve_xin_phep_vang",
        replace_existing=True,
        max_instances=1,
    )
    sched.add_job(
        nhac_hop_3_tang_job,
        trigger=IntervalTrigger(minutes=1),
        id="nhac_hop_3_tang",
        replace_existing=True,
        max_instances=1,
    )
    sched.add_job(
        nhac_han_ket_luan_job,
        trigger=CronTrigger(hour=8, minute=0),  # 8:00 UTC
        id="nhac_han_ket_luan",
        replace_existing=True,
        max_instances=1,
    )
    sched.add_job(
        mark_tre_han_ket_luan_job,
        trigger=CronTrigger(hour=0, minute=0),  # 0:00 UTC
        id="mark_tre_han_ket_luan",
        replace_existing=True,
        max_instances=1,
    )

    sched.start()
    _scheduler = sched
    logger.info("APScheduler started — %d jobs registered", len(sched.get_jobs()))
    return sched


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("APScheduler stopped")


def get_scheduler() -> AsyncIOScheduler | None:
    return _scheduler
