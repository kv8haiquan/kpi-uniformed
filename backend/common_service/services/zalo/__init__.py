"""
common_service/services/zalo
=============================
Hạ tầng gửi thông báo qua Zalo OA cho toàn nền tảng.

Giai đoạn 1 (07/2026): chỉ bật cho HKG (`ZALO_LOAI_BAT=MEETING`).
Bật thêm KPI/LMS về sau chỉ cần đổi biến môi trường, không sửa code.

Module con:
    phone        — chuẩn hóa số điện thoại VN về dạng 84xxxxxxxxx (thuần túy)
    templates    — ánh xạ loại thông báo → template ZNS + tham số
    token_store  — giữ OAuth token của OA (refresh_token XOAY VÒNG)
    client       — gọi API ZNS, có chế độ dry-run
    outbox       — quét thông báo, xếp hàng, gửi, retry có backoff
"""

from common_service.services.zalo.outbox import (  # noqa: F401
    chay_mot_vong,
    gui_hang_doi,
    xep_hang,
)
from common_service.services.zalo.phone import chuan_hoa  # noqa: F401
