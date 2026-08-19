"""
thong_ke_tai_lieu_service.py
=============================
Báo cáo "Thống kê tài liệu họp" — theo dõi đơn vị được giao chuẩn bị đã nộp
tài liệu hay chưa.

Đây là công cụ thay cho việc Văn phòng phải rà từng lịch hoặc hỏi từng đơn vị,
nên phải tính đúng — báo sai là đơn vị bị nhắc oan.

Quy tắc phân loại giấy mời nằm ở `quy_tac_giay_moi.py`, port nguyên văn từ
lichkv8. Không tính lại ở đây.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models.base import CongChucRef
from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.models.lich_cong_tac import LanhDaoLienQuan
from meeting_service.models.tai_lieu import TaiLieu
from meeting_service.services.quy_tac_giay_moi import la_giay_moi_thuan

# Tình trạng tài liệu của một cuộc họp — đúng 5 mức của lichkv8.
TAT_CA = "TAT_CA"
CO_GIAO_CHUAN_BI = "CO_GIAO_CHUAN_BI"
DA_GAN_TAI_LIEU = "DA_GAN_TAI_LIEU"
THIEU_TAI_LIEU = "THIEU_TAI_LIEU"
CHUA_GIAO_CHUAN_BI = "CHUA_GIAO_CHUAN_BI"

TINH_TRANG_VALUES = [TAT_CA, CO_GIAO_CHUAN_BI, DA_GAN_TAI_LIEU,
                     THIEU_TAI_LIEU, CHUA_GIAO_CHUAN_BI]

NHAN_TINH_TRANG = {
    TAT_CA: "Tất cả",
    CO_GIAO_CHUAN_BI: "Có giao chuẩn bị",
    DA_GAN_TAI_LIEU: "Đã gắn tài liệu",
    THIEU_TAI_LIEU: "Thiếu tài liệu",
    CHUA_GIAO_CHUAN_BI: "Chưa giao chuẩn bị",
}


class ThongKeTaiLieuService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bao_cao(
        self,
        *,
        tu_ngay: Optional[date] = None,
        den_ngay: Optional[date] = None,
        tu_khoa: Optional[str] = None,
        lanh_dao_id: Optional[UUID] = None,
        trang_thai_lich: Optional[str] = None,
        tinh_trang: str = TAT_CA,
        tinh_lich_huy: bool = False,
        gioi_han: int = 500,
    ) -> dict[str, Any]:
        dk = [CuocHop.is_deleted.is_(False)]

        # Lịch trực ban không có nghĩa vụ chuẩn bị tài liệu — loại khỏi báo cáo,
        # đúng như ghi chú trong mã gốc: "loại trừ lịch trực ban".
        dk.append(or_(CuocHop.loai_lich.is_(None),
                      CuocHop.loai_lich != "TRUC_BAN"))

        if tu_ngay:
            dk.append(CuocHop.ngay_hien_thi >= tu_ngay)
        if den_ngay:
            dk.append(CuocHop.ngay_hien_thi <= den_ngay)
        if trang_thai_lich:
            dk.append(CuocHop.trang_thai == trang_thai_lich)
        if not tinh_lich_huy:
            dk.append(CuocHop.trang_thai != "HUY")
        if tu_khoa:
            t = f"%{tu_khoa.strip()}%"
            dk.append(or_(
                CuocHop.tieu_de.ilike(t),
                CuocHop.ma_lich.ilike(t),
                CuocHop.don_vi_chuan_bi.ilike(t),
                CuocHop.so_van_ban.ilike(t),
            ))
        if lanh_dao_id:
            dk.append(or_(
                CuocHop.chu_toa_id == lanh_dao_id,
                CuocHop.id.in_(
                    select(LanhDaoLienQuan.cuoc_hop_id)
                    .where(LanhDaoLienQuan.cong_chuc_id == lanh_dao_id)),
            ))

        rows = (await self.db.execute(
            select(CuocHop).where(and_(*dk))
            .order_by(CuocHop.ngay_hien_thi.desc(), CuocHop.gio_bat_dau.desc())
            .limit(gioi_han)
        )).scalars().all()

        if not rows:
            return {"dong": [], "tong_hop": self._tong_hop_rong()}

        ids = [r.id for r in rows]

        # Tên tài liệu theo lô — quy tắc giấy mời chạy trên tên file nên không
        # đẩy xuống SQL được.
        tai_lieu: dict[UUID, list[str]] = {}
        q = (select(TaiLieu.cuoc_hop_id, TaiLieu.ten_tai_lieu)
             .where(TaiLieu.cuoc_hop_id.in_(ids), TaiLieu.is_deleted.is_(False)))
        for ch_id, ten in (await self.db.execute(q)).all():
            tai_lieu.setdefault(ch_id, []).append(ten or "")

        ld: dict[UUID, list[str]] = {}
        q = (select(LanhDaoLienQuan.cuoc_hop_id, CongChucRef.ho_ten)
             .join(CongChucRef, CongChucRef.id == LanhDaoLienQuan.cong_chuc_id)
             .where(LanhDaoLienQuan.cuoc_hop_id.in_(ids))
             .order_by(LanhDaoLienQuan.thu_tu))
        for ch_id, ho_ten in (await self.db.execute(q)).all():
            ld.setdefault(ch_id, []).append(ho_ten)

        dong: list[dict] = []
        for r in rows:
            ten_files = tai_lieu.get(r.id, [])
            so_chuan_bi = sum(1 for t in ten_files if not la_giay_moi_thuan(t))
            so_giay_moi = len(ten_files) - so_chuan_bi
            co_giao = bool((r.don_vi_chuan_bi or "").strip())

            if not co_giao:
                tt = CHUA_GIAO_CHUAN_BI
            elif so_chuan_bi > 0:
                tt = DA_GAN_TAI_LIEU
            else:
                tt = THIEU_TAI_LIEU

            dong.append({
                "id": r.id,
                "ma_lich": r.ma_lich,
                "ngay": r.ngay_hien_thi,
                "gio_bat_dau": r.gio_bat_dau,
                "tieu_de": r.tieu_de,
                "loai_lich": r.loai_lich,
                "trang_thai": r.trang_thai,
                "lanh_dao": ld.get(r.id, []),
                "chu_tri": (r.chu_tri_text or ""),
                "don_vi_chuan_bi": r.don_vi_chuan_bi,
                "so_van_ban": r.so_van_ban,
                "so_tai_lieu": len(ten_files),
                "so_tai_lieu_chuan_bi": so_chuan_bi,
                "so_giay_moi": so_giay_moi,
                "tinh_trang": tt,
                "tinh_trang_nhan": NHAN_TINH_TRANG[tt],
            })

        tong_hop = {
            "tong": len(dong),
            CO_GIAO_CHUAN_BI: sum(1 for d in dong
                                  if d["tinh_trang"] != CHUA_GIAO_CHUAN_BI),
            DA_GAN_TAI_LIEU: sum(1 for d in dong
                                 if d["tinh_trang"] == DA_GAN_TAI_LIEU),
            THIEU_TAI_LIEU: sum(1 for d in dong
                                if d["tinh_trang"] == THIEU_TAI_LIEU),
            CHUA_GIAO_CHUAN_BI: sum(1 for d in dong
                                    if d["tinh_trang"] == CHUA_GIAO_CHUAN_BI),
        }

        # Lọc theo tình trạng làm SAU khi tính, vì tình trạng phụ thuộc tên file
        # chứ không phải cột nào trong CSDL.
        if tinh_trang == CO_GIAO_CHUAN_BI:
            dong = [d for d in dong if d["tinh_trang"] != CHUA_GIAO_CHUAN_BI]
        elif tinh_trang in (DA_GAN_TAI_LIEU, THIEU_TAI_LIEU,
                            CHUA_GIAO_CHUAN_BI):
            dong = [d for d in dong if d["tinh_trang"] == tinh_trang]

        return {"dong": dong, "tong_hop": tong_hop}

    @staticmethod
    def _tong_hop_rong() -> dict[str, int]:
        return {"tong": 0, CO_GIAO_CHUAN_BI: 0, DA_GAN_TAI_LIEU: 0,
                THIEU_TAI_LIEU: 0, CHUA_GIAO_CHUAN_BI: 0}
