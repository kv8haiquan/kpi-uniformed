"""
lms_service/models/__init__.py
==============================
Import tat ca LMS models (11 goc + 5 DGNL).
"""

from lms_service.models.base import Base
from lms_service.models.chuyen_de import ChuyenDe
from lms_service.models.khoa_hoc import KhoaHoc
from lms_service.models.bai_hoc import BaiHoc
from lms_service.models.cau_hoi import CauHoi
from lms_service.models.bai_kiem_tra import BaiKiemTra
from lms_service.models.bai_kiem_tra_cau_hoi import BaiKiemTraCauHoi
from lms_service.models.dang_ky_khoa_hoc import DangKyKhoaHoc
from lms_service.models.tien_do_bai_hoc import TienDoBaiHoc
from lms_service.models.ket_qua_bai_kiem_tra import KetQuaBaiKiemTra
from lms_service.models.chung_chi import ChungChi
from lms_service.models.khao_sat import KhaoSat
# DGNL models
from lms_service.models.linh_vuc import LinhVuc
from lms_service.models.vi_tri_viec_lam import ViTriViecLam
from lms_service.models.ky_thi import KyThi
from lms_service.models.cau_truc_de import CauTrucDe
from lms_service.models.thi_sinh import ThiSinh
from lms_service.models.cau_hoi_dgnl import CauHoiDgnl

__all__ = [
    "Base",
    "ChuyenDe",
    "KhoaHoc",
    "BaiHoc",
    "CauHoi",
    "BaiKiemTra",
    "BaiKiemTraCauHoi",
    "DangKyKhoaHoc",
    "TienDoBaiHoc",
    "KetQuaBaiKiemTra",
    "ChungChi",
    "KhaoSat",
    # DGNL
    "LinhVuc",
    "ViTriViecLam",
    "KyThi",
    "CauTrucDe",
    "ThiSinh",
    "CauHoiDgnl",
]
