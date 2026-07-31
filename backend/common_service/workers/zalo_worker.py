"""
common_service/workers/zalo_worker.py
======================================
Tiến trình nền gửi thông báo Zalo.

CHẠY RIÊNG, KHÔNG nằm trong tiến trình API — cố ý như vậy để:
  - Zalo treo/chậm không làm chậm API của common_service
  - Tắt kênh Zalo = dừng 1 tiến trình, không phải restart service đang phục vụ
  - Log tách bạch, dễ soi khi có người báo không nhận được tin

Chạy tay để thử:
    cd backend && source venv/bin/activate
    PYTHONPATH=/root/kpi-haiquan/backend python -m common_service.workers.zalo_worker

Chạy 1 vòng rồi thoát (dùng khi kiểm thử):
    ... python -m common_service.workers.zalo_worker --mot-vong

Đăng ký PM2 (chỉ làm SAU khi đã bật ZALO_ENABLED và nạp token):
    pm2 start "python -m common_service.workers.zalo_worker" \
        --name zalo-worker --cwd /root/kpi-haiquan/backend \
        --interpreter /root/kpi-haiquan/backend/venv/bin/python
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.database import create_db_engine, create_session_factory  # noqa: E402

from common_service.config import settings  # noqa: E402
from common_service.services.zalo.outbox import chay_mot_vong  # noqa: E402


def _cau_hinh_log() -> logging.Logger:
    """uvicorn không cấu hình root logger; worker chạy độc lập nên tự gắn."""
    goc = logging.getLogger("zalo")
    if not goc.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        )
        goc.addHandler(h)
        goc.setLevel(logging.INFO)
        goc.propagate = False
    return logging.getLogger("zalo.worker")


logger = _cau_hinh_log()


async def _vong_lap(mot_vong: bool = False) -> None:
    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    logger.info(
        "Worker Zalo khởi động | enabled=%s dry_run=%s loai=%s nhịp=%ds",
        settings.zalo_enabled,
        settings.zalo_dry_run,
        settings.zalo_danh_sach_loai,
        settings.zalo_chu_ky_giay,
    )
    if settings.zalo_dry_run:
        logger.warning(
            "ĐANG Ở CHẾ ĐỘ DRY-RUN — chỉ ghi log, KHÔNG gửi tin thật. "
            "Đặt ZALO_DRY_RUN=false trong .env khi muốn gửi thật."
        )

    try:
        while True:
            try:
                async with session_factory() as db:
                    ket_qua = await chay_mot_vong(db)
                    if ket_qua["xep_hang"]["quet"] or ket_qua["gui"]["gui"]:
                        logger.info("Vòng chạy xong: %s", ket_qua)
            except Exception:  # pragma: no cover — vòng lặp phải sống sót
                logger.exception("Lỗi trong vòng chạy, sẽ thử lại ở nhịp sau")

            if mot_vong:
                break
            await asyncio.sleep(settings.zalo_chu_ky_giay)
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Worker gửi thông báo Zalo")
    parser.add_argument(
        "--mot-vong",
        action="store_true",
        help="Chạy đúng 1 vòng rồi thoát (dùng khi kiểm thử)",
    )
    parser.add_argument(
        "--bo-qua-cong-tac",
        action="store_true",
        help="Chạy kể cả khi ZALO_ENABLED=false (chỉ dùng để thử tay)",
    )
    args = parser.parse_args()

    if not settings.zalo_enabled and not args.bo_qua_cong_tac:
        logger.warning(
            "ZALO_ENABLED=false → worker không chạy. "
            "Bật trong .env, hoặc thêm --bo-qua-cong-tac để thử tay."
        )
        return 0

    try:
        asyncio.run(_vong_lap(mot_vong=args.mot_vong))
    except KeyboardInterrupt:
        logger.info("Nhận Ctrl+C, dừng worker")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
