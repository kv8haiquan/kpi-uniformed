"""
common_service/services/zalo/client.py
=======================================
Client gửi tin ZNS (Zalo Notification Service).

Vì sao dùng ZNS chứ không dùng OA message API:
    ZNS gửi theo SỐ ĐIỆN THOẠI, không đòi người nhận phải follow OA trước.
    OA message API gửi theo `user_id`, mà `user_id` chỉ có khi người dùng chủ
    động follow/nhắn tin cho OA — Zalo KHÔNG có API tra số điện thoại ra
    user_id. Với 544 công chức thì phương án bắt mọi người tự follow là rủi ro
    triển khai lớn nhất, nên giai đoạn 1 đi bằng ZNS.

Chế độ DRY-RUN: khi settings.zalo_dry_run=True (mặc định), client KHÔNG gọi
mạng, chỉ ghi log và trả kết quả thành công giả lập. Nhờ vậy chạy thử được
toàn bộ đường đi của dữ liệu mà không tốn tin nhắn và không cần credential.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from common_service.config import settings
from common_service.services.zalo.phone import che_giau
from common_service.services.zalo.token_store import LoiTokenZalo, lay_access_token

logger = logging.getLogger("zalo.client")


@dataclass(frozen=True)
class KetQuaGui:
    """Kết quả gửi 1 tin."""

    thanh_cong: bool
    message_id: Optional[str] = None
    ma_loi: Optional[str] = None
    mo_ta_loi: Optional[str] = None
    thu_lai_duoc: bool = False


# ---------------------------------------------------------------------------
# Phân loại mã lỗi Zalo → có nên thử lại không
#
# ⚠️ Bảng mã lỗi của Zalo thay đổi theo thời gian. Danh sách dưới đây là các
# nhóm phổ biến; mã lạ sẽ được coi là THỬ LẠI ĐƯỢC (an toàn hơn: tin bị chậm
# còn hơn mất hẳn) nhưng vẫn bị chặn bởi số lần thử tối đa.
# Khi có tài liệu chính thức từ VNG thì cập nhật lại ở đây.
# ---------------------------------------------------------------------------

# Lỗi vĩnh viễn — thử lại vô ích, đánh THAT_BAI luôn
_LOI_VINH_VIEN = {
    -108,  # số điện thoại không hợp lệ
    -118,  # người dùng không tồn tại trên Zalo
    -119,  # người dùng đã chặn nhận tin từ OA
    -132,  # template không hợp lệ
    -133,  # tham số template không khớp
}

# Lỗi token — refresh rồi thử lại
_LOI_TOKEN = {-124, -216, -217}


def _phan_loai(ma_loi: Any) -> bool:
    """True nếu nên thử lại."""
    try:
        ma = int(ma_loi)
    except (TypeError, ValueError):
        return True
    if ma in _LOI_VINH_VIEN:
        return False
    return True


async def gui_zns(
    db: AsyncSession,
    so_dien_thoai: str,
    template_id: str,
    template_data: dict[str, Any],
    tracking_id: Optional[str] = None,
) -> KetQuaGui:
    """Gửi 1 tin ZNS. Không raise — mọi lỗi trả về trong KetQuaGui."""

    # --- Chế độ chạy khô: không gọi mạng ---
    if settings.zalo_dry_run:
        logger.info(
            "[DRY-RUN] Sẽ gửi ZNS tới %s | template=%s | data=%s",
            che_giau(so_dien_thoai),
            template_id,
            template_data,
        )
        return KetQuaGui(thanh_cong=True, message_id=f"dryrun-{tracking_id or 'x'}")

    try:
        access_token = await lay_access_token(db)
    except LoiTokenZalo as e:
        # Hết token là lỗi hệ thống, không phải lỗi của tin này → thử lại sau
        logger.error("Không lấy được access_token: %s", e)
        return KetQuaGui(
            thanh_cong=False, ma_loi="TOKEN", mo_ta_loi=str(e), thu_lai_duoc=True
        )

    payload: dict[str, Any] = {
        "phone": so_dien_thoai,
        "template_id": template_id,
        "template_data": template_data,
    }
    if tracking_id:
        payload["tracking_id"] = tracking_id

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                settings.zalo_zns_url,
                headers={
                    "access_token": access_token,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except httpx.HTTPError as e:
        logger.warning("Lỗi mạng khi gửi ZNS tới %s: %s", che_giau(so_dien_thoai), e)
        return KetQuaGui(
            thanh_cong=False, ma_loi="MANG", mo_ta_loi=str(e), thu_lai_duoc=True
        )

    try:
        du_lieu = resp.json()
    except ValueError:
        return KetQuaGui(
            thanh_cong=False,
            ma_loi=f"HTTP_{resp.status_code}",
            mo_ta_loi=(resp.text or "")[:500],
            thu_lai_duoc=True,
        )

    ma_loi = du_lieu.get("error")
    if ma_loi in (0, "0", None):
        data = du_lieu.get("data") or {}
        return KetQuaGui(
            thanh_cong=True, message_id=str(data.get("msg_id") or "") or None
        )

    mo_ta = str(du_lieu.get("message") or "")[:500]
    thu_lai = _phan_loai(ma_loi)
    logger.warning(
        "ZNS lỗi %s tới %s: %s (thử lại=%s)",
        ma_loi,
        che_giau(so_dien_thoai),
        mo_ta,
        thu_lai,
    )
    return KetQuaGui(
        thanh_cong=False,
        ma_loi=str(ma_loi),
        mo_ta_loi=mo_ta,
        thu_lai_duoc=thu_lai,
    )


def loi_lam_hong_so(ma_loi: Optional[str]) -> bool:
    """True nếu mã lỗi cho thấy SỐ ĐIỆN THOẠI hỏng (không phải lỗi tạm thời).

    Dùng để đánh dấu zalo_lien_ket.trang_thai = SO_LOI, tránh gửi lại mãi vào
    một số sai và tạo ra danh sách cần đơn vị rà lại.
    """
    try:
        return int(ma_loi) in {-108, -118}
    except (TypeError, ValueError):
        return False
