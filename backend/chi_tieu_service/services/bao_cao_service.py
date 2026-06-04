"""
chi_tieu_service/services/bao_cao_service.py
============================================
Bao cao: ra soat theo thang (tai lap bieu Excel) + luy ke nam.
Luy ke CAT theo thang dang xem (dung view v_luy_ke_thang voi thang = N).
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _num(v):
    return str(v) if isinstance(v, Decimal) else v


class BaoCaoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def luy_ke(self, nam: int, don_vi_id: Optional[UUID], thang: Optional[int] = None) -> list[dict]:
        """
        Luy ke nam tu view. Neu truyen thang -> cat den thang do (lay dong thang lon nhat <= thang).
        Mac dinh: lay dong thang lon nhat da chot trong nam.
        """
        sql = """
            SELECT DISTINCT ON (don_vi_id, chi_tieu_id, loai_muc)
                   don_vi_id, chi_tieu_id, nam, loai_muc, gia_tri_giao,
                   thang, luy_ke_den_thang, dat_phan_tram_den_thang
            FROM chi_tieu.v_luy_ke_thang
            WHERE nam = :nam
              {don_vi_filter}
              {thang_filter}
            ORDER BY don_vi_id, chi_tieu_id, loai_muc, thang DESC
        """.format(
            don_vi_filter="AND don_vi_id = :don_vi_id" if don_vi_id else "",
            thang_filter="AND thang <= :thang" if thang else "",
        )
        params: dict = {"nam": nam}
        if don_vi_id:
            params["don_vi_id"] = str(don_vi_id)
        if thang:
            params["thang"] = thang
        rows = (await self.db.execute(text(sql), params)).mappings().all()
        return [
            {
                "don_vi_id": str(r["don_vi_id"]),
                "chi_tieu_id": str(r["chi_tieu_id"]),
                "nam": r["nam"],
                "loai_muc": r["loai_muc"],
                "gia_tri_giao": _num(r["gia_tri_giao"]),
                "den_thang": r["thang"],
                "luy_ke": _num(r["luy_ke_den_thang"]),
                "dat_phan_tram_nam": _num(r["dat_phan_tram_den_thang"]),
            }
            for r in rows
        ]

    async def ra_soat(
        self, thang: int, nam: int,
        linh_vuc_id: Optional[UUID] = None, don_vi_id: Optional[UUID] = None,
    ) -> list[dict]:
        """
        Cau truc long: linh_vuc[] -> chi_tieu[] -> dong_don_vi[].
        Moi dong don vi: dang ky, ket qua, danh gia, gia tri giao (theo muc), luy ke nam, dat%.
        """
        # 1. Linh vuc (active)
        lv_sql = "SELECT id, ma_linh_vuc, ten_linh_vuc, van_ban_ke_hoach, thu_tu FROM chi_tieu.linh_vuc WHERE is_active = TRUE"
        lv_params: dict = {}
        if linh_vuc_id:
            lv_sql += " AND id = :lv_id"
            lv_params["lv_id"] = str(linh_vuc_id)
        lv_sql += " ORDER BY thu_tu, ten_linh_vuc"
        linh_vucs = (await self.db.execute(text(lv_sql), lv_params)).mappings().all()
        lv_ids = [str(r["id"]) for r in linh_vucs]
        if not lv_ids:
            return []

        # 2. Danh muc chi tieu thuoc cac linh vuc nay
        dm = (await self.db.execute(text("""
            SELECT id, linh_vuc_id, ma_chi_tieu, ten_chi_tieu, don_vi_tinh, kieu_du_lieu, co_phan_dau, thu_tu
            FROM chi_tieu.danh_muc_chi_tieu
            WHERE is_active = TRUE AND linh_vuc_id = ANY(:lv_ids)
            ORDER BY thu_tu, ten_chi_tieu
        """), {"lv_ids": lv_ids})).mappings().all()

        # 3. Dang ky thang (thang/nam) + ten don vi
        dk_sql = """
            SELECT d.chi_tieu_id, d.don_vi_id, dv.ten_don_vi, dv.ma_don_vi,
                   d.khong_dang_ky, d.gia_tri_dang_ky, d.gia_tri_ket_qua,
                   d.danh_gia_tu_dong, d.danh_gia_ghi_chu, d.trang_thai
            FROM chi_tieu.dang_ky_thang d
            JOIN public.don_vi dv ON dv.id = d.don_vi_id
            WHERE d.thang = :thang AND d.nam = :nam AND d.is_deleted = FALSE
        """
        dk_params: dict = {"thang": thang, "nam": nam}
        if don_vi_id:
            dk_sql += " AND d.don_vi_id = :don_vi_id"
            dk_params["don_vi_id"] = str(don_vi_id)
        dks = (await self.db.execute(text(dk_sql), dk_params)).mappings().all()

        # 4. Luy ke den thang (cat theo thang dang xem)
        luy_ke_rows = await self.luy_ke(nam=nam, don_vi_id=don_vi_id, thang=thang)
        luy_ke_map: dict = {}
        for lk in luy_ke_rows:
            luy_ke_map.setdefault((lk["chi_tieu_id"], lk["don_vi_id"]), {})[lk["loai_muc"]] = lk

        # Index dang ky theo (chi_tieu, don_vi)
        dk_map: dict = {}
        for r in dks:
            dk_map.setdefault(str(r["chi_tieu_id"]), []).append(r)

        # Assemble
        result = []
        for lv in linh_vucs:
            ct_list = []
            for ct in [c for c in dm if str(c["linh_vuc_id"]) == str(lv["id"])]:
                dong_don_vi = []
                for r in dk_map.get(str(ct["id"]), []):
                    lk = luy_ke_map.get((str(ct["id"]), str(r["don_vi_id"])), {})
                    dong_don_vi.append({
                        "don_vi_id": str(r["don_vi_id"]),
                        "ten_don_vi": r["ten_don_vi"],
                        "ma_don_vi": r["ma_don_vi"],
                        "khong_dang_ky": r["khong_dang_ky"],
                        "gia_tri_dang_ky": _num(r["gia_tri_dang_ky"]),
                        "gia_tri_ket_qua": _num(r["gia_tri_ket_qua"]),
                        "danh_gia": r["danh_gia_ghi_chu"] or r["danh_gia_tu_dong"],
                        "trang_thai": r["trang_thai"],
                        "luy_ke_nam": {muc: {"gia_tri_giao": v["gia_tri_giao"],
                                             "luy_ke": v["luy_ke"],
                                             "dat_phan_tram": v["dat_phan_tram_nam"]}
                                       for muc, v in lk.items()},
                    })
                ct_list.append({
                    "chi_tieu_id": str(ct["id"]),
                    "ma_chi_tieu": ct["ma_chi_tieu"],
                    "ten_chi_tieu": ct["ten_chi_tieu"],
                    "don_vi_tinh": ct["don_vi_tinh"],
                    "kieu_du_lieu": ct["kieu_du_lieu"],
                    "co_phan_dau": ct["co_phan_dau"],
                    "dong_don_vi": dong_don_vi,
                })
            result.append({
                "linh_vuc_id": str(lv["id"]),
                "ma_linh_vuc": lv["ma_linh_vuc"],
                "ten_linh_vuc": lv["ten_linh_vuc"],
                "van_ban_ke_hoach": lv["van_ban_ke_hoach"],
                "chi_tieu": ct_list,
            })
        return result
