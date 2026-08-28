"""
lms_service/api/endpoints/dgnl_cong_khai.py
===========================================
API cong khai cau hoi DGNL hang ngay — cho chatbot Zalo goi tu ben ngoai.

2 endpoint:
  GET /dgnl/cong-khai/cau-hoi-hang-ngay   Cau hoi cua ngay (KHONG kem dap an)
  GET /dgnl/cong-khai/dap-an              Dap an cua mot cau da phat

XAC THUC: header `X-Bot-Key` phai khop settings.zalo_bot_api_key.
  - KHONG dung chung INTERNAL_API_KEY (khoa do mo cua cho cac endpoint noi bo
    khac; khoa bot se nam trong cau hinh ben ngoai nen phai tach rieng).
  - Chua dat khoa trong .env = TAT han tinh nang (fail closed).

HAI DINH DANG TRA VE, chon bang tham so `dinh_dang`:
  - mac dinh  -> {"success": true, "data": {...}}  chuan cua du an
  - `zalo`    -> object `message` tran cua Zalo, dan thang vao khoi dong
                 (Dynamic block) cua chatbot, khong phai bien doi gi them
"""

import logging
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.config import settings
from lms_service.dependencies import get_db
from lms_service.schemas.cau_hoi_hang_ngay import (
    CauHoiHangNgayResponse,
    DapAnResponse,
)
from lms_service.services.cau_hoi_hang_ngay_service import CauHoiHangNgayService

router = APIRouter(prefix="/dgnl/cong-khai", tags=["ĐGNL - Công khai (chatbot)"])

# Bam vao logger cua uvicorn: no da co handler san, logger tu dat ten thi
# khong co handler nao nen log roi vao hu khong.
logger = logging.getLogger("uvicorn.error")


async def soi_yeu_cau(req: Request, ten: str) -> None:
    """Ghi lai TOAN BO header + query cua mot lan goi, de xem Zalo gui gi.

    Muc dich: tim xem Zalo co tu dinh kem danh tinh nguoi dung (user_id) vao
    loi goi cua khoi Dynamic khong. Co thi moi chan spam theo tung nguoi duoc.

    Chi bat khi `dgnl_soi_yeu_cau=True` (dat trong .env cua DEV). KHONG bat
    tren prod: log day du header cua moi lan goi la vua on vua thua.
    Khoa bot LUON bi che, ke ca khi bat.
    """
    if not settings.dgnl_soi_yeu_cau:
        return
    header = {
        k: ("***" if k.lower() in ("x-bot-key", "authorization") else v)
        for k, v in req.headers.items()
    }
    try:
        than = (await req.body())[:2000].decode("utf-8", "replace")
    except Exception:  # noqa: BLE001 — soi log thi khong duoc lam hong request
        than = "<khong doc duoc>"
    logger.info(
        "[SOI %s] %s ip=%s query=%s than=%s headers=%s",
        ten,
        req.method,
        req.client.host if req.client else "?",
        dict(req.query_params),
        than or "<rong>",
        header,
    )


def xac_thuc_bot(x_bot_key: Optional[str] = Header(None)) -> None:
    """Kiem tra khoa bot. Khoa rong = tinh nang chua bat -> tu choi."""
    if not settings.zalo_bot_api_key or x_bot_key != settings.zalo_bot_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_003",
                    "message": "Khoa bot khong hop le",
                },
            },
        )


@router.api_route("/cau-hoi-hang-ngay", methods=["GET", "POST"])
async def cau_hoi_hang_ngay(
    request: Request,
    ngay: Optional[date] = Query(
        None, description="Mac dinh la hom nay theo gio Viet Nam"
    ),
    dinh_dang: Optional[str] = Query(
        None, description="`zalo` de tra object message cua Zalo"
    ),
    kieu_nut: str = Query(
        "object",
        description=(
            "Hinh dang payload cua nut (chi co tac dung khi dinh_dang=zalo). "
            "`object` = {\"content\": \"A\"} (mac dinh, da doi chung hien "
            "duoc nut). `chuoi` = \"A\" — bam nut va go tay cho ra CUNG mot "
            "gia tri, buoc dieu kien trong kich ban chi con mot dang de khop."
        ),
    ),
    loai_nut: str = Query(
        "hide",
        description=(
            "`hide` = oa.query.hide (mac dinh, tin gui ve OA nhung an voi "
            "nguoi dung). `show` = oa.query.show — tin hien nhu chinh nguoi "
            "dung vua nhan; dung khi bo may tu khoa khong nhin thay tin an."
        ),
    ),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(xac_thuc_bot),
):
    """Cau hoi DGNL cua ngay — de va cac phuong an, KHONG kem dap an dung.

    Goi bao nhieu lan trong cung mot ngay cung ra dung mot cau (da chot o bang
    lms.cau_hoi_hang_ngay), nen bot thu lai hay nhieu nguoi cung nhan deu khop.
    """
    await soi_yeu_cau(request, "cau-hoi")
    service = CauHoiHangNgayService(db)
    kq = await service.lay_cau_hoi(ngay)

    if (dinh_dang or "").lower() == "zalo":
        return service.zalo_cau_hoi(kq, kieu_nut=kieu_nut, loai_nut=loai_nut)

    return {
        "success": True,
        "data": CauHoiHangNgayResponse(**kq).model_dump(mode="json"),
    }


@router.api_route("/dap-an", methods=["GET", "POST"])
async def dap_an(
    request: Request,
    cau_hoi_id: Optional[UUID] = Query(
        None,
        description="Lay tu payload cua nut. De trong = cau phat gan nhat.",
    ),
    chon: Optional[str] = Query(
        None, description="Phuong an nguoi dung chon (A/B/C/D) — de cham dung/sai"
    ),
    dinh_dang: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(xac_thuc_bot),
):
    """Dap an dung + giai thich cua mot cau DA PHAT.

    Hai duong goi:
      - CO `cau_hoi_id` (nguoi dung BAM NUT): tra dung cau ho da nhan. Khong
        tra theo ngay vi ho co the bam luc dem hoac sang hom sau.
      - KHONG co `cau_hoi_id` (nguoi dung GO TAY "A"/"B" tren Zalo may tinh,
        noi khong hien nut): lay cau phat gan nhat.
    """
    await soi_yeu_cau(request, "dap-an")
    service = CauHoiHangNgayService(db)
    kq = await service.lay_dap_an(cau_hoi_id, chon)

    if (dinh_dang or "").lower() == "zalo":
        return service.zalo_dap_an(kq)

    return {
        "success": True,
        "data": DapAnResponse(**kq).model_dump(mode="json"),
    }
