#!/usr/bin/env python3
"""
Script gui thong bao cho CBCC duoc giao khoa hoc nhung chua bat dau.

Chay: python3 backend/scripts/07_notify_unstarted_courses.py
"""

import asyncio
import logging
import os
from collections import defaultdict

import asyncpg
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Config — doc tu env hoac dung default
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "kpi_haiquan")
DB_USER = os.getenv("DB_USER", "kpi_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "KpiHaiQuan2026!")

COMMON_INTERNAL_URL = os.getenv("COMMON_INTERNAL_URL", "http://localhost:8005/internal/v1")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "kv08-internal-secret-key")

QUERY = """
SELECT
    dk.cong_chuc_id,
    dk.khoa_hoc_id,
    dk.loai_dang_ky,
    dk.han_hoan_thanh,
    dk.trang_thai,
    kh.ten_khoa_hoc
FROM lms.dang_ky_khoa_hoc dk
JOIN lms.khoa_hoc kh ON dk.khoa_hoc_id = kh.id
JOIN public.cong_chuc cc ON dk.cong_chuc_id = cc.id
WHERE dk.trang_thai IN ('CHUA_BAT_DAU', 'CHO_PHE_DUYET')
  AND dk.loai_dang_ky IN ('BAT_BUOC', 'GIAO_VIEC')
  AND cc.is_active = true
  AND kh.is_active = true
ORDER BY kh.ten_khoa_hoc, dk.created_at
"""


async def main():
    logger.info("Ket noi DB %s:%s/%s ...", DB_HOST, DB_PORT, DB_NAME)
    conn = await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
    )

    rows = await conn.fetch(QUERY)
    await conn.close()
    logger.info("Tim thay %d dang ky chua bat dau", len(rows))

    if not rows:
        logger.info("Khong co ai can gui thong bao. Thoat.")
        return

    # Nhom theo khoa hoc
    by_course: dict[str, dict] = defaultdict(lambda: {"ten": "", "han": None, "users": []})
    for r in rows:
        kid = str(r["khoa_hoc_id"])
        by_course[kid]["ten"] = r["ten_khoa_hoc"]
        if r["han_hoan_thanh"] and (by_course[kid]["han"] is None):
            by_course[kid]["han"] = r["han_hoan_thanh"]
        by_course[kid]["users"].append(str(r["cong_chuc_id"]))

    logger.info("Gui thong bao cho %d khoa hoc ...", len(by_course))

    total_sent = 0
    async with httpx.AsyncClient(timeout=15.0) as client:
        for course_id, data in by_course.items():
            han_text = f" (hạn: {data['han'].strftime('%d/%m/%Y')})" if data["han"] else ""
            payload = {
                "nguoi_nhan_ids": data["users"],
                "tieu_de": f"Nhắc nhở: Khóa học \"{data['ten']}\" chưa bắt đầu",
                "noi_dung": (
                    f"Bạn được giao tham gia khóa học \"{data['ten']}\"{han_text}. "
                    "Vui lòng truy cập và bắt đầu học sớm."
                ),
                "loai": "LMS",
                "muc_do": "QUAN_TRONG",
                "link_url": f"/dao-tao/khoa-hoc/{course_id}",
                "doi_tuong_type": "KHOA_HOC",
                "doi_tuong_id": course_id,
            }

            try:
                resp = await client.post(
                    f"{COMMON_INTERNAL_URL}/thong-bao/bulk",
                    json=payload,
                    headers={"X-Internal-Key": INTERNAL_API_KEY},
                )
                if resp.status_code == 201:
                    count = resp.json().get("data", {}).get("created_count", len(data["users"]))
                    logger.info("  [OK] %s — %d thong bao", data["ten"], count)
                    total_sent += count
                else:
                    logger.warning("  [FAIL] %s — %s %s", data["ten"], resp.status_code, resp.text[:200])
            except Exception as e:
                logger.error("  [ERROR] %s — %s", data["ten"], e)

    logger.info("Hoan tat. Da gui %d thong bao cho %d khoa hoc.", total_sent, len(by_course))


if __name__ == "__main__":
    asyncio.run(main())
