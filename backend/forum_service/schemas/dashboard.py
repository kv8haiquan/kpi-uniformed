"""Pydantic schemas cho dashboard va bao cao."""
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from forum_service.schemas.chu_de import UserBrief


class DashboardSummary(BaseModel):
    """Summary cho widget trang chu."""
    chu_de_moi_tuan: int = 0
    tra_loi_chua_doc: int = 0  # placeholder
    upvote_tuan: int = 0
    chu_de_cua_toi_chua_tra_loi: int = 0


class BaoCaoCaNhan(BaseModel):
    """Thong ke dong gop ca nhan theo thang."""
    thang: int
    nam: int
    chu_de_da_dang: int = 0
    tra_loi_da_dang: int = 0
    upvote_nhan_duoc: int = 0
    bai_ghim: int = 0
    dap_an_chuan: int = 0


class BaoCaoDonVi(BaseModel):
    """Thong ke dong gop don vi."""
    don_vi_id: UUID
    don_vi_ten: Optional[str] = None
    thang: int
    nam: int
    tong_chu_de: int = 0
    tong_tra_loi: int = 0
    tong_upvote: int = 0
    so_nguoi_tham_gia: int = 0


class TopContributor(BaseModel):
    """Thong tin nguoi dong gop nhieu nhat."""
    user: UserBrief
    chu_de: int = 0
    tra_loi: int = 0
    upvote: int = 0
    dap_an_chuan: int = 0
    diem: int = 0  # tong hop
