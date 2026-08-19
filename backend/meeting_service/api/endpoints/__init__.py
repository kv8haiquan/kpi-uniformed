"""API endpoints HKG. G2 chỉ có Module 1 (cuoc_hop). G3 sẽ thêm các module khác."""

from meeting_service.api.endpoints.cuoc_hop import router as cuoc_hop_router
from meeting_service.api.endpoints.lich_cong_tac import router as lich_cong_tac_router
from meeting_service.api.endpoints.thong_ke_tai_lieu import router as thong_ke_tai_lieu_router
from meeting_service.api.endpoints.truc_ban import router as truc_ban_router
from meeting_service.api.endpoints.doi_soat import router as doi_soat_router
from meeting_service.api.endpoints.nhom_thanh_phan import (
    router as nhom_thanh_phan_router,
    router_cuoc_hop as nhom_thanh_phan_cuoc_hop_router,
)

__all__ = [
    "cuoc_hop_router",
    "lich_cong_tac_router",
    "thong_ke_tai_lieu_router",
    "truc_ban_router",
    "doi_soat_router",
    "nhom_thanh_phan_router",
    "nhom_thanh_phan_cuoc_hop_router",
]
