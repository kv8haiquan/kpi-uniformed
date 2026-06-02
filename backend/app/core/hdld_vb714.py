"""
app/core/hdld_vb714.py
======================
Helper cho Bộ tiêu chí đánh giá HĐLĐ 111 theo QĐ 714/QĐ-CHQ (08/5/2026).

- Mốc áp dụng: từ tháng 5/2026. Tháng ≤ 4/2026 HĐLĐ vẫn dùng form lãnh đạo cũ
  (ke_khai_lanh_dao, công thức (a+b+c)/3×70).
- Công thức VB714: điểm chính thức = TB 3 tiêu chí (cột cấp quản lý), thang 0-100.
  KPI-70 = TB / 100 × 70. Cộng tiêu chí chung 30 như công chức → xếp loại A/B/C/D.
"""

from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hdld import HdldDanhGia, TrangThaiHdldDanhGia


# Mốc áp dụng VB714 — (năm, tháng)
# 01/06/2026: đổi về T1/2026 — HĐLĐ kê khai lại toàn bộ T1–T6 theo VB714
# (đã xóa sạch dữ liệu kê khai cũ form lãnh đạo của HĐLĐ).
HDLD_VB714_FROM_NAM = 2026
HDLD_VB714_FROM_THANG = 1


def is_hdld_vb714_active(thang: int, nam: int) -> bool:
    """True nếu (thang, nam) >= mốc áp dụng VB714 (T5/2026)."""
    return (nam, thang) >= (HDLD_VB714_FROM_NAM, HDLD_VB714_FROM_THANG)


def tb_3_tieu_chi(diem_list: List[Optional[Decimal]]) -> Optional[Decimal]:
    """TB cộng 3 tiêu chí (0-100). Trả None nếu thiếu bất kỳ điểm nào."""
    vals = [d for d in diem_list if d is not None]
    if len(vals) != 3:
        return None
    tong = sum(Decimal(str(v)) for v in vals)
    return (tong / Decimal(3)).quantize(Decimal("0.01"))


def kpi_70_tu_tb(diem_tb: Optional[Decimal]) -> Optional[Decimal]:
    """Quy TB (0-100) về điểm KPI-70."""
    if diem_tb is None:
        return None
    return (Decimal(str(diem_tb)) / Decimal(100) * Decimal(70)).quantize(Decimal("0.01"))


async def get_hdld_in_data(
    db: AsyncSession, cong_chuc_id: UUID, thang: int, nam: int
) -> Optional[dict]:
    """Dữ liệu phục vụ IN bảng kê / phiếu đánh giá HĐLĐ theo VB714.

    Lấy bản đánh giá đã duyệt (DA_DUYET) + tên 3 tiêu chí theo nhóm nghề.
    Trả None nếu chưa có bản duyệt (caller fallback / báo "chưa có dữ liệu").

    Cấu trúc trả về:
        {
          "nhom_nghe": "I", "ten_nhom": "...",
          "tieu_chi": [  # đúng 3 dòng, sort theo so_tt
            {"so_tt": 1, "ten": "...", "diem_tu": 90.0, "ghi_chu_tu": "...",
             "diem_ql": 95.0, "ghi_chu_ql": "..."},
            ...
          ],
          "diem_tc_tb_tu": 90.0, "diem_tc_tb_ql": 93.33, "diem_kpi_70": 65.33,
        }
    """
    from app.models.hdld import HdldTieuChi  # tránh import vòng ở module top

    dg = await get_hdld_danh_gia_da_duyet(db, cong_chuc_id, thang, nam)
    if dg is None:
        return None

    # Tên tiêu chí theo nhóm nghề (nếu đã chọn)
    ten_map: dict[int, str] = {}
    ten_nhom = None
    if dg.nhom_nghe:
        rows = (await db.execute(
            select(HdldTieuChi).where(
                HdldTieuChi.nhom == dg.nhom_nghe, HdldTieuChi.is_active == True
            )
        )).scalars().all()
        for tc in rows:
            ten_map[tc.so_tt] = tc.ten_tieu_chi
            ten_nhom = tc.ten_nhom

    tieu_chi = []
    for ct in sorted(dg.chi_tiets, key=lambda x: x.so_tt):
        tieu_chi.append({
            "so_tt": ct.so_tt,
            "ten": ten_map.get(ct.so_tt, f"Tiêu chí {ct.so_tt}"),
            "diem_tu": float(ct.diem_tu) if ct.diem_tu is not None else None,
            "ghi_chu_tu": ct.ghi_chu_tu or "",
            "diem_ql": float(ct.diem_ql) if ct.diem_ql is not None else None,
            "ghi_chu_ql": ct.ghi_chu_ql or "",
        })

    return {
        "nhom_nghe": dg.nhom_nghe,
        "ten_nhom": ten_nhom,
        "tieu_chi": tieu_chi,
        "diem_tc_tb_tu": float(dg.diem_tc_tb_tu) if dg.diem_tc_tb_tu is not None else None,
        "diem_tc_tb_ql": float(dg.diem_tc_tb_ql) if dg.diem_tc_tb_ql is not None else None,
        "diem_kpi_70": float(dg.diem_kpi_70) if dg.diem_kpi_70 is not None else None,
    }


async def get_hdld_danh_gia_da_duyet(
    db: AsyncSession, cong_chuc_id: UUID, thang: int, nam: int
) -> Optional[HdldDanhGia]:
    """Lấy bản đánh giá HĐLĐ VB714 đã DA_DUYET của 1 người trong tháng (nếu có)."""
    stmt = select(HdldDanhGia).where(
        HdldDanhGia.cong_chuc_id == cong_chuc_id,
        HdldDanhGia.thang == thang,
        HdldDanhGia.nam == nam,
        HdldDanhGia.trang_thai == TrangThaiHdldDanhGia.DA_DUYET.value,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def tinh_diem_kpi_70_hdld_vb714(
    db: AsyncSession, cong_chuc_id: UUID, thang: int, nam: int, tam_tinh: bool = False
) -> Optional[dict]:
    """Tính điểm KPI-70 cho HĐLĐ theo VB714 từ bản đánh giá đã duyệt.

    Trả về dict đồng dạng với tinh_diem_kpi_70_hd_111 (xep_loai_moi.py) để
    nhánh gọi tái dùng được. Trả None nếu chưa có bản DA_DUYET (caller fallback).

    tam_tinh=True: cho phép lấy cả bản chưa duyệt (CHO_DUYET) để xem tạm tính.
    """
    dg = await get_hdld_danh_gia_da_duyet(db, cong_chuc_id, thang, nam)
    if dg is None and tam_tinh:
        stmt = select(HdldDanhGia).where(
            HdldDanhGia.cong_chuc_id == cong_chuc_id,
            HdldDanhGia.thang == thang,
            HdldDanhGia.nam == nam,
            HdldDanhGia.trang_thai.in_([
                TrangThaiHdldDanhGia.CHO_DUYET.value,
                TrangThaiHdldDanhGia.DA_DUYET.value,
            ]),
        )
        dg = (await db.execute(stmt)).scalar_one_or_none()

    if dg is None:
        return None

    diem_70 = dg.diem_kpi_70
    if diem_70 is None:
        # Fallback: tính lại từ chi tiết (cột cấp quản lý) nếu header chưa chốt
        diem_tb = tb_3_tieu_chi([ct.diem_ql for ct in dg.chi_tiets])
        diem_70 = kpi_70_tu_tb(diem_tb)

    diem_70_f = float(diem_70) if diem_70 is not None else 0.0

    # Map 3 tiêu chí VB714 (cột cấp quản lý, 0-100) về tỉ lệ 0-1 cho các slot a/b/c
    ct_by_sott = {ct.so_tt: ct for ct in dg.chi_tiets}
    def _ratio(sott: int) -> float:
        ct = ct_by_sott.get(sott)
        if ct is None or ct.diem_ql is None:
            return 0.0
        return min(1.0, float(ct.diem_ql) / 100.0)
    tc1, tc2, tc3 = _ratio(1), _ratio(2), _ratio(3)  # chất lượng / tuân thủ / hiệu quả
    diem_kpi = (tc1 + tc2 + tc3) / 3 if dg.chi_tiets else 0.0

    return {
        "is_lanh_dao": False,
        "is_hd_111": True,
        "is_vb714": True,
        "nhom_nghe": dg.nhom_nghe,
        "diem_tc_tb_ql": float(dg.diem_tc_tb_ql) if dg.diem_tc_tb_ql is not None else None,
        "diem_tc_tb_tu": float(dg.diem_tc_tb_tu) if dg.diem_tc_tb_tu is not None else None,
        # 3 tiêu chí VB714 → slot a/b/c (giữ tên key tương thích nhánh cũ)
        "tong_cong_viec": 0,
        "tong_hoan_thanh": 0,
        "tong_diem_chat_luong": 0.0,
        "tong_diem_tien_do": 0.0,
        "tong_loi_chat_luong": 0,
        "tong_loi_tien_do": 0,
        "a_so_luong": tc1,
        "b_tien_do": tc2,
        "c_chat_luong": tc3,
        "b_chat_luong": tc1,
        "c_tien_do": tc2,
        "diem_kpi": diem_kpi,
        "diem_70": min(70.0, diem_70_f),
        # Backward compatibility (HĐLĐ VB714 không dùng ngày công / SP)
        "so_ngay_trong_thang": 0,
        "so_ngay_nghi": 0,
        "so_ngay_lam_viec": 0,
        "sp_duoc_giao": 0,
        "tong_sp_hoan_thanh": 0,
        "sp_chat_luong": 0,
        "sp_tien_do": 0,
    }
