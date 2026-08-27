"""
lms_service/schemas/cau_hoi_hang_ngay.py
========================================
Pydantic schemas cho cau hoi DGNL phat hang ngay (chatbot Zalo).
"""

from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class LuaChon(BaseModel):
    """Mot phuong an tra loi."""
    key: str        # "A" | "B" | "C" | "D"
    noi_dung: str


class CauHoiHangNgayResponse(BaseModel):
    """Cau hoi cua ngay — KHONG kem dap an dung."""
    ngay: date
    cau_hoi_id: UUID
    linh_vuc_ma: str
    linh_vuc_ten: str
    loai: str
    do_kho: Optional[str] = None
    noi_dung: str
    lua_chon: list[LuaChon]
    # Chuoi da dung san de bot gui thang, khong phai ghep lai o phia Zalo
    text_zalo: str


class DapAnResponse(BaseModel):
    """Dap an dung cua mot cau da phat."""
    ngay: date
    cau_hoi_id: UUID
    dap_an_dung: str
    dap_an_dung_noi_dung: str
    giai_thich: Optional[str] = None
    # Chi co khi bot truyen `chon` — None nghia la chi hoi dap an, khong cham
    da_chon: Optional[str] = None
    dung: Optional[bool] = None
    text_zalo: str
