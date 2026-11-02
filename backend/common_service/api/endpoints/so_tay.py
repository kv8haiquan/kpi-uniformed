"""
common_service/api/endpoints/so_tay.py
=======================================
Sổ tay số — phục vụ các tệp HTML một-tệp do phòng nghiệp vụ biên soạn
(Sổ tay kiểm tra nội bộ, Sổ tra cứu lỗi hải quan).
Prefix: /api/common/v1/so-tay
Auth: JWT Bearer token — mọi công chức đã đăng nhập

Endpoints:
  GET /so-tay        — Danh sách sổ tay (tên, phiên bản, ngày cập nhật, dung lượng)
  GET /so-tay/{ma}   — Nội dung HTML của một sổ

Vì sao không để nginx phục vụ tĩnh: nội dung chỉ dùng nội bộ, mà JWT nằm ở
localStorage (không có cookie) nên nginx không soát được đăng nhập. Frontend
gọi endpoint này bằng axios kèm Bearer rồi hiển thị trong iframe blob.

Thay bản mới: chép đè tệp vào settings.so_tay_dir — không build, không restart.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from common_service.config import settings
from common_service.dependencies import CurrentUserDep
from common_service.schemas.base import SuccessResponse

router = APIRouter(prefix="/so-tay", tags=["Sổ tay số"])

# Danh mục CỐ ĐỊNH: mã → tên tệp. Không ghép đường dẫn từ dữ liệu người gửi
# lên → không có đường nào đọc tệp ngoài danh mục (chống path traversal).
DANH_MUC: dict[str, dict[str, str]] = {
    "kiem-tra-noi-bo": {
        "ten_tep": "So-tay-kiem-tra-noi-bo.html",
        "tieu_de": "Sổ tay kiểm tra nội bộ",
        "mo_ta": "Trình tự, thủ tục tiến hành một cuộc kiểm tra nội bộ theo "
        "Quyết định số 459/QĐ-CHQ — kèm 19 biểu mẫu chính thức.",
    },
    "tra-cuu-loi": {
        "ten_tep": "So_tra_cuu_loi.html",
        "tieu_de": "Sổ tra cứu lỗi hải quan",
        "mo_ta": "Các lỗi thường gặp tổng hợp từ kết luận của đoàn thanh tra, "
        "kiểm tra cấp trên và kiểm tra nội bộ Chi cục.",
    },
}

# Sổ tra cứu lỗi nhúng dữ liệu dạng {"version": "V1.0", "updated": "08/10/2026", ...}
_RE_PHIEN_BAN = re.compile(rb'"version"\s*:\s*"([^"]{1,30})"')
_RE_NGAY = re.compile(rb'"updated"\s*:\s*"([^"]{1,30})"')
# Khối dữ liệu nằm ở nửa đầu tệp; đọc giới hạn để không nạp cả tệp 9 MB
_DOC_TOI_DA = 512 * 1024


class SoTayItem(BaseModel):
    ma: str
    tieu_de: str
    mo_ta: str
    co_san: bool
    dung_luong: Optional[int] = None
    phien_ban: Optional[str] = None
    ngay_cap_nhat: Optional[str] = None


def _duong_dan(ma: str) -> Optional[Path]:
    muc = DANH_MUC.get(ma)
    if muc is None:
        return None
    return Path(settings.so_tay_dir) / muc["ten_tep"]


def _thong_tin(ma: str) -> SoTayItem:
    muc = DANH_MUC[ma]
    tep = _duong_dan(ma)
    item = SoTayItem(ma=ma, tieu_de=muc["tieu_de"], mo_ta=muc["mo_ta"], co_san=False)
    if tep is None or not tep.is_file():
        return item

    item.co_san = True
    st = tep.stat()
    item.dung_luong = st.st_size
    with tep.open("rb") as f:
        dau = f.read(_DOC_TOI_DA)
    m_pb, m_ngay = _RE_PHIEN_BAN.search(dau), _RE_NGAY.search(dau)
    item.phien_ban = m_pb.group(1).decode("utf-8", "replace") if m_pb else None
    # Ưu tiên ngày tác giả ghi trong tệp; không có thì lấy ngày chép tệp lên
    item.ngay_cap_nhat = (
        m_ngay.group(1).decode("utf-8", "replace")
        if m_ngay
        else datetime.fromtimestamp(st.st_mtime).strftime("%d/%m/%Y")
    )
    return item


@router.get("", response_model=SuccessResponse[list[SoTayItem]])
async def danh_sach(user: CurrentUserDep):
    """Danh sách sổ tay số."""
    return SuccessResponse(data=[_thong_tin(ma) for ma in DANH_MUC])


@router.get("/{ma}", response_class=FileResponse)
async def noi_dung(ma: str, user: CurrentUserDep):
    """Trả nội dung HTML của một sổ để frontend hiển thị trong iframe.

    `no-store` để trình duyệt không giữ bản sao trong cache đĩa; `inline` để
    không bật hộp thoại tải về. Việc chặn tải nguyên tệp do frontend lo.
    """
    tep = _duong_dan(ma)
    if tep is None or not tep.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {"code": "NOT_FOUND", "message": "Không tìm thấy sổ tay"},
            },
        )
    return FileResponse(
        tep,
        media_type="text/html; charset=utf-8",
        headers={
            "Content-Disposition": "inline",
            "Cache-Control": "no-store, private",
            "X-Content-Type-Options": "nosniff",
        },
    )
