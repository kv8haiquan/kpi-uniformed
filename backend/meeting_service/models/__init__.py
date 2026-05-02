"""Models cho schema meeting (10 bảng MVP + 1 bảng Phase 4.1) + base."""

from meeting_service.models.base import Base
from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.models.thanh_phan import ThanhPhan
from meeting_service.models.tai_lieu import TaiLieu
from meeting_service.models.diem_danh import DiemDanh
from meeting_service.models.xin_phep_vang import XinPhepVang
from meeting_service.models.y_kien import YKien
from meeting_service.models.bien_ban import BienBan
from meeting_service.models.ket_luan import KetLuan
from meeting_service.models.tien_do import TienDo
from meeting_service.models.mau_bieu import MauBieu
from meeting_service.models.trang_thai_trinh_chieu import TrangThaiTrinhChieu

__all__ = [
    "Base",
    "CuocHop",
    "ThanhPhan",
    "TaiLieu",
    "DiemDanh",
    "XinPhepVang",
    "YKien",
    "BienBan",
    "KetLuan",
    "TienDo",
    "MauBieu",
    "TrangThaiTrinhChieu",
]
