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

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.config import settings
from lms_service.dependencies import get_db
from lms_service.schemas.cau_hoi_hang_ngay import (
    CauHoiHangNgayResponse,
    DapAnResponse,
)
from lms_service.services.cau_hoi_hang_ngay_service import CauHoiHangNgayService

router = APIRouter(prefix="/dgnl/cong-khai", tags=["ĐGNL - Công khai (chatbot)"])


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


@router.get("/cau-hoi-hang-ngay")
async def cau_hoi_hang_ngay(
    ngay: Optional[date] = Query(
        None, description="Mac dinh la hom nay theo gio Viet Nam"
    ),
    dinh_dang: Optional[str] = Query(
        None, description="`zalo` de tra object message cua Zalo"
    ),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(xac_thuc_bot),
):
    """Cau hoi DGNL cua ngay — de va cac phuong an, KHONG kem dap an dung.

    Goi bao nhieu lan trong cung mot ngay cung ra dung mot cau (da chot o bang
    lms.cau_hoi_hang_ngay), nen bot thu lai hay nhieu nguoi cung nhan deu khop.
    """
    service = CauHoiHangNgayService(db)
    kq = await service.lay_cau_hoi(ngay)

    if (dinh_dang or "").lower() == "zalo":
        return service.zalo_cau_hoi(kq)

    return {
        "success": True,
        "data": CauHoiHangNgayResponse(**kq).model_dump(mode="json"),
    }


@router.get("/dap-an")
async def dap_an(
    cau_hoi_id: UUID = Query(..., description="Lay tu `cau_hoi_id` cua cau hoi"),
    chon: Optional[str] = Query(
        None, description="Phuong an nguoi dung bam (A/B/C/D) — de cham dung/sai"
    ),
    dinh_dang: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(xac_thuc_bot),
):
    """Dap an dung + giai thich cua mot cau DA PHAT.

    Tra theo `cau_hoi_id` chu khong theo ngay: nguoi dung co the bam tra loi
    luc dem hoac sang hom sau, tra theo ngay se ra nham cau khac.
    """
    service = CauHoiHangNgayService(db)
    kq = await service.lay_dap_an(cau_hoi_id, chon)

    if (dinh_dang or "").lower() == "zalo":
        return service.zalo_dap_an(kq)

    return {
        "success": True,
        "data": DapAnResponse(**kq).model_dump(mode="json"),
    }
