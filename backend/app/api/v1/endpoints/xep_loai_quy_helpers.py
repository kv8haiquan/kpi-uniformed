"""
app/api/v1/endpoints/xep_loai_quy_helpers.py
=============================================
Helper functions cho tính điểm và xếp loại quý.

PHIÊN BẢN: 3.9.0 (15/04/2026)

LOGIC REFACTOR — Hybrid approach với fallback real-time:
- Ưu tiên 1: chi_tiet_xep_loai với trang_thai = DA_PHE_DUYET
- Ưu tiên 2: chi_tiet_xep_loai với trang_thai = CHO_PHE_DUYET
- Ưu tiên 3 (MỚI): Tính real-time từ ke_khai_cong_viec / ke_khai_lanh_dao
- Tiêu chí chung: GIỮ NGUYÊN logic cũ (deduplicate Option Y)

CÔNG THỨC QUÝ (v3.9.0):
- CÔNG CHỨC THƯỜNG: diem_kpi_quy = (t1 + t2 + t3) / 3 (LUÔN chia 3, thiếu tính 0)
- LÃNH ĐẠO (MỚI):
  + a/b/c quý = TB 3 tháng (tỷ lệ số lượng / tiến độ / chất lượng công việc)
  + d/đ/e quý = MIN 3 tháng (kết quả ĐV / tổ chức TK / đoàn kết), NULL = 100%
  + diem_kpi_quy = (a + b + c + d_quy + dd_quy + e_quy) / 6 × 70

Các hàm chính:
- tinh_diem_quy(db, cc_id, quy, nam) -> dict
- lay_tieu_chi_quy(db, cc_id, thang_list, nam) -> dict (trung bình 3 tháng)
- xep_loai_kpi(diem_tong) -> str (reuse từ xep_loai_moi.py)
- kiem_tra_chuyen_don_vi(db, cc_id, thang_list, nam) -> bool (KHÔNG ĐỔI)
"""

import logging
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kpi_assessment import (
    DanhGiaThang,
    TieuChiChungDanhGia,
    TieuChiChung,
)
from app.models.lich_su_dieu_chinh import LichSuDieuChinh, LoaiDoiTuongDieuChinh
from app.models.user_org import CongChuc

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

QUY_TO_THANG = {
    1: [1, 2, 3],
    2: [4, 5, 6],
    3: [7, 8, 9],
    4: [10, 11, 12],
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def xep_loai_kpi(diem_tong: float) -> str:
    """
    Xếp loại KPI theo điểm tổng.
    Reuse logic từ xep_loai_moi.py.
    """
    if diem_tong >= 90:
        return "A"
    elif diem_tong >= 70:
        return "B"
    elif diem_tong >= 50:
        return "C"
    else:
        return "D"


async def kiem_tra_chuyen_don_vi(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang_list: List[int],
    nam: int
) -> bool:
    """
    Kiểm tra CC có chuyển đơn vị giữa quý không.

    Trả về TRUE nếu có bản ghi chuyển đơn vị trong khoảng 3 tháng của quý.
    """
    # Lấy tất cả bản ghi danh_gia_thang của 3 tháng
    stmt = (
        select(DanhGiaThang.don_vi_id_snapshot)
        .where(DanhGiaThang.cong_chuc_id == cong_chuc_id)
        .where(DanhGiaThang.thang.in_(thang_list))
        .where(DanhGiaThang.nam == nam)
        .where(DanhGiaThang.is_deleted == False)
    )
    result = await db.execute(stmt)
    don_vi_ids = [row[0] for row in result.fetchall() if row[0]]

    # Nếu có nhiều hơn 1 đơn vị → chuyển đơn vị giữa quý
    return len(set(don_vi_ids)) > 1


async def lay_tieu_chi_quy(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang_list: List[int],
    nam: int
) -> dict:
    """
    Lấy tiêu chí chung quý (trung bình 3 tháng).

    Logic:
    - Lấy điểm tiêu chí chung của từng tháng trong quý
    - Tính trung bình: diem_tc_quy = (diem_tc_t1 + diem_tc_t2 + diem_tc_t3) / 3
    - Luôn chia 3, tháng thiếu tính 0

    Returns:
    {
        "diem_tc_quy": Decimal,
        "chi_tiet_thang": List[dict],  # Điểm TC từng tháng
    }
    """
    from app.models.kpi_assessment import DanhGiaThang

    # Lấy điểm tiêu chí chung của từng tháng
    chi_tiet_thang = []
    tong_diem_tc = Decimal("0")

    for thang in thang_list:
        # Query DanhGiaThang để lấy diem_tieu_chi_chung
        stmt = (
            select(DanhGiaThang.diem_tieu_chi_chung)
            .where(DanhGiaThang.cong_chuc_id == cong_chuc_id)
            .where(DanhGiaThang.thang == thang)
            .where(DanhGiaThang.nam == nam)
            .where(DanhGiaThang.is_deleted == False)
        )
        result = await db.execute(stmt)
        diem_tc_thang = result.scalar() or Decimal("0")

        tong_diem_tc += diem_tc_thang
        chi_tiet_thang.append({
            "thang": thang,
            "diem_tc": float(diem_tc_thang),
        })

    # Trung bình luôn chia 3
    diem_tc_quy = tong_diem_tc / Decimal("3")
    diem_tc_quy = max(Decimal("0"), min(Decimal("30"), diem_tc_quy))

    return {
        "diem_tc_quy": diem_tc_quy,
        "chi_tiet_thang": chi_tiet_thang,
    }


async def tinh_diem_quy(
    db: AsyncSession,
    cong_chuc_id: UUID,
    quy: int,
    nam: int
) -> dict:
    """
    Tính điểm quý cho 1 công chức.

    HYBRID APPROACH (v3.9.0 - 15/04/2026):
    - Ưu tiên 1: chi_tiet_xep_loai với trang_thai = DA_PHE_DUYET
    - Ưu tiên 2: chi_tiet_xep_loai với trang_thai = CHO_PHE_DUYET
    - Ưu tiên 3: Fallback real-time từ ke_khai_cong_viec / ke_khai_lanh_dao
    - Tiêu chí chung: GIỮ NGUYÊN logic cũ (deduplicate)

    CÔNG THỨC QUÝ:
    - CÔNG CHỨC THƯỜNG: diem_kpi_quy = (diem_kpi_t1 + t2 + t3) / 3 (LUÔN chia 3, thiếu tính 0)
    - LÃNH ĐẠO (MỚI):
      + a/b/c quý = TB 3 tháng (a: số lượng, b: tiến độ, c: chất lượng)
      + d/đ/e quý = MIN 3 tháng (d: kết quả ĐV, đ: tổ chức TK, e: đoàn kết)
      + NULL → 1.0 (100%) khi tính MIN
      + diem_kpi_quy = (a + b + c + d_quy + dd_quy + e_quy) / 6 × 70

    Returns:
    {
        "diem_kpi_quy": float,  # Scale 0-70
        "diem_tc_quy": float,   # Scale 0-30
        "diem_tong_quy": float,
        "xep_loai_quy": str | None,
        "co_chuyen_don_vi": bool,
        "so_thang_co_du_lieu": int,  # 0-3
        "ghi_chu": str | None,
        "cac_thang": List[dict],  # Chi tiết 3 tháng (mỗi tháng có field "nguon")
        "tieu_chi_quy": dict,     # Kết quả từ lay_tieu_chi_quy()
    }
    """
    from app.models.bao_cao_xep_loai import BaoCaoXepLoai, ChiTietXepLoai

    thang_list = QUY_TO_THANG.get(quy, [])
    if not thang_list:
        return {
            "diem_kpi_quy": None,
            "diem_tc_quy": None,
            "diem_tong_quy": None,
            "xep_loai_quy": None,
            "co_chuyen_don_vi": False,
            "so_thang_co_du_lieu": 0,
            "ghi_chu": "Quý không hợp lệ",
            "cac_thang": [],
            "tieu_chi_quy": {},
        }

    # === Bước 1: Check chuyển đơn vị ===
    co_chuyen_don_vi = await kiem_tra_chuyen_don_vi(db, cong_chuc_id, thang_list, nam)
    if co_chuyen_don_vi:
        return {
            "diem_kpi_quy": None,
            "diem_tc_quy": None,
            "diem_tong_quy": None,
            "xep_loai_quy": None,
            "co_chuyen_don_vi": True,
            "so_thang_co_du_lieu": 0,
            "ghi_chu": "Không tính do chuyển đơn vị giữa quý",
            "cac_thang": [],
            "tieu_chi_quy": {},
        }

    # === Bước 2: Lấy điểm KPI từng tháng từ chi_tiet_xep_loai ===
    # Chấp nhận cả CHO_PHE_DUYET (đã gửi) và DA_PHE_DUYET (đã duyệt)
    # Ưu tiên DA_PHE_DUYET nếu cùng 1 tháng có cả 2 (hiếm khi xảy ra)
    stmt = (
        select(
            BaoCaoXepLoai.thang,
            BaoCaoXepLoai.trang_thai,
            ChiTietXepLoai.diem_kpi,
            ChiTietXepLoai.diem_tieu_chi_chung,
            ChiTietXepLoai.diem_tong,
            ChiTietXepLoai.xep_loai_he_thong,
        )
        .join(ChiTietXepLoai, ChiTietXepLoai.bao_cao_id == BaoCaoXepLoai.id)
        .where(ChiTietXepLoai.cong_chuc_id == cong_chuc_id)
        .where(BaoCaoXepLoai.thang.in_(thang_list))
        .where(BaoCaoXepLoai.nam == nam)
        .where(BaoCaoXepLoai.trang_thai.in_(["DA_PHE_DUYET", "CHO_PHE_DUYET"]))
        .where(BaoCaoXepLoai.is_deleted == False)
    )
    result = await db.execute(stmt)
    rows = result.all()

    # Map thang -> diem, ưu tiên DA_PHE_DUYET nếu cùng tháng có nhiều bản
    thang_to_diem: dict[int, any] = {}
    for row in rows:
        existing = thang_to_diem.get(row.thang)
        if existing is None:
            thang_to_diem[row.thang] = row
        elif existing.trang_thai != "DA_PHE_DUYET" and row.trang_thai == "DA_PHE_DUYET":
            thang_to_diem[row.thang] = row

    # === Bước 2.5: Lấy is_lanh_dao của CC (dùng cho fallback) ===
    cc_query = select(CongChuc.is_lanh_dao).where(CongChuc.id == cong_chuc_id)
    is_lanh_dao = (await db.execute(cc_query)).scalar()
    if is_lanh_dao is None:
        is_lanh_dao = False

    # Debug removed (v3.9.0)

    # === Bước 3: Build danh sách 3 tháng (với fallback real-time) ===
    cac_thang = []
    tong_diem_kpi = Decimal("0")
    so_thang_co_du_lieu = 0

    # Lưu d/đ/e của từng tháng (cho lãnh đạo) để tính MIN
    d_values = []
    dd_values = []
    e_values = []

    for thang in thang_list:
        if thang in thang_to_diem:
            # Có báo cáo
            row = thang_to_diem[thang]
            diem_kpi_thang = row.diem_kpi or Decimal("0")  # Scale 0-70 (đã nhân)
            tong_diem_kpi += diem_kpi_thang
            so_thang_co_du_lieu += 1
            cac_thang.append({
                "thang": thang,
                "diem_kpi": float(diem_kpi_thang),
                "diem_tc": float(row.diem_tieu_chi_chung or 0),
                "diem_tong": float(row.diem_tong or 0),
                "xep_loai_thang": row.xep_loai_he_thong,
                "co_du_lieu": True,
                "nguon": row.trang_thai,  # "DA_PHE_DUYET" hoặc "CHO_PHE_DUYET"
            })
            # TODO: Nếu lãnh đạo, lấy d/đ/e từ báo cáo (hiện chưa lưu trong chi_tiet_xep_loai)
            # Tạm thời giả định NULL → sẽ fallback real-time để lấy d/đ/e
            d_values.append(None)
            dd_values.append(None)
            e_values.append(None)
        else:
            # FALLBACK: Tính real-time
            try:
                # Import helper INSIDE để tránh circular import
                from app.api.v1.endpoints.xep_loai_moi import tinh_diem_kpi_70, tinh_diem_kpi_70_lanh_dao

                if is_lanh_dao:
                    kpi_data = await tinh_diem_kpi_70_lanh_dao(db, cong_chuc_id, thang, nam, tam_tinh=False)
                    # Lưu d/đ/e của tháng này
                    d_val = kpi_data.get("d_ket_qua", 1.0)  # Scale 0-1, NULL → 1.0
                    dd_val = kpi_data.get("dd_to_chuc", 1.0)
                    e_val = kpi_data.get("e_doan_ket", 1.0)

                    # Debug removed (v3.9.0)

                    d_values.append(d_val)
                    dd_values.append(dd_val)
                    e_values.append(e_val)
                else:
                    kpi_data = await tinh_diem_kpi_70(db, cong_chuc_id, thang, nam, tam_tinh=False)
                    d_values.append(None)  # CC thường không có d/đ/e
                    dd_values.append(None)
                    e_values.append(None)

                diem_kpi_rt = Decimal(str(kpi_data.get("diem_70", 0)))
            except Exception as e:
                logger.warning(
                    f"Fallback real-time failed for CC {cong_chuc_id} thang {thang}/{nam}: {e}"
                )
                diem_kpi_rt = Decimal("0")
                # Không có data → coi như NULL
                d_values.append(None)
                dd_values.append(None)
                e_values.append(None)

            # Lấy điểm TC từ danh_gia_thang (nếu có)
            dg_stmt = select(DanhGiaThang.diem_tieu_chi_chung).where(
                DanhGiaThang.cong_chuc_id == cong_chuc_id,
                DanhGiaThang.thang == thang,
                DanhGiaThang.nam == nam,
                DanhGiaThang.is_deleted == False,
            )
            diem_tc_rt = (await db.execute(dg_stmt)).scalar() or Decimal("0")

            tong_diem_kpi += diem_kpi_rt
            if diem_kpi_rt > 0:
                so_thang_co_du_lieu += 1  # count nếu có điểm thực

            cac_thang.append({
                "thang": thang,
                "diem_kpi": float(diem_kpi_rt),
                "diem_tc": float(diem_tc_rt),
                "diem_tong": float(diem_kpi_rt + diem_tc_rt),
                "xep_loai_thang": None,
                "co_du_lieu": diem_kpi_rt > 0,
                "nguon": "real_time",
            })

    # === Bước 3.5: Nếu là lãnh đạo, lấy d/đ/e từ bảng DanhGiaDDE cho các tháng thiếu ===
    if is_lanh_dao:
        from app.models.leader_kpi import DanhGiaDDE, TrangThaiDDE
        for i, thang in enumerate(thang_list):
            # Nếu đã có giá trị từ real-time, skip
            if d_values[i] is not None:
                continue

            # Query DanhGiaDDE cho tháng này
            stmt_dde = (
                select(DanhGiaDDE)
                .where(DanhGiaDDE.cong_chuc_id == cong_chuc_id)
                .where(DanhGiaDDE.thang == thang)
                .where(DanhGiaDDE.nam == nam)
                .where(DanhGiaDDE.trang_thai == TrangThaiDDE.DA_PHE_DUYET.value)
            )
            result_dde = await db.execute(stmt_dde)
            dde = result_dde.scalar_one_or_none()

            if dde:
                # Có data → lưu vào list (scale 0-1)
                d_values[i] = float(dde.d_final) / 100.0
                dd_values[i] = float(dde.dd_final) / 100.0
                e_values[i] = float(dde.e_final) / 100.0
            else:
                # Không có data → giữ nguyên NULL
                pass

    # === Bước 4: Tính điểm KPI quý ===
    # CÔNG THỨC MỚI cho LÃNH ĐẠO: d_quy/dd_quy/e_quy = MIN 3 tháng, NULL = 100% (1.0)
    # CC thường: giữ nguyên logic cũ (TB 3 tháng)

    if is_lanh_dao and any(v is not None for v in d_values):
        # Tính d/đ/e quý = MIN 3 tháng, NULL → 1.0
        d_quy = min([v if v is not None else 1.0 for v in d_values])
        dd_quy = min([v if v is not None else 1.0 for v in dd_values])
        e_quy = min([v if v is not None else 1.0 for v in e_values])

        logger.info(
            f"[LANH_DAO QUY] CC={cong_chuc_id}, Q{quy}/{nam}: "
            f"d={d_values} → d_quy={d_quy:.2f}, "
            f"dd={dd_values} → dd_quy={dd_quy:.2f}, "
            f"e={e_values} → e_quy={e_quy:.2f}"
        )

        # Tính lại diem_kpi_quy cho lãnh đạo
        # Lấy (a+b+c) trung bình 3 tháng, rồi cộng (d_quy + dd_quy + e_quy)
        # Công thức: diem_kpi = (a + b + c + d + đ + e) / 6 × 70
        # Nhưng d/đ/e quý dùng MIN, a/b/c quý dùng TB

        # Tính lại từng tháng để lấy a/b/c
        a_values, b_values, c_values = [], [], []
        for i, thang in enumerate(thang_list):
            try:
                from app.api.v1.endpoints.xep_loai_moi import tinh_diem_kpi_70_lanh_dao
                kpi_data = await tinh_diem_kpi_70_lanh_dao(db, cong_chuc_id, thang, nam, tam_tinh=False)
                a_values.append(kpi_data.get("a_so_luong", 0))
                b_values.append(kpi_data.get("b_tien_do", 0))
                c_values.append(kpi_data.get("c_chat_luong", 0))
            except Exception as e:
                logger.warning(f"Failed to get a/b/c for CC {cong_chuc_id} thang {thang}/{nam}: {e}")
                a_values.append(0)
                b_values.append(0)
                c_values.append(0)

        # a/b/c quý = trung bình 3 tháng
        a_quy = sum(a_values) / 3 if len(a_values) == 3 else 0
        b_quy = sum(b_values) / 3 if len(b_values) == 3 else 0
        c_quy = sum(c_values) / 3 if len(c_values) == 3 else 0

        # Điểm KPI quý cho lãnh đạo = (a_quy + b_quy + c_quy + d_quy + dd_quy + e_quy) / 6 × 70
        diem_kpi_quy = Decimal(str((a_quy + b_quy + c_quy + d_quy + dd_quy + e_quy) / 6 * 70))

        logger.info(
            f"[LANH_DAO QUY FINAL] CC={cong_chuc_id}, Q{quy}/{nam}: "
            f"a_quy={a_quy:.3f}, b_quy={b_quy:.3f}, c_quy={c_quy:.3f}, "
            f"d_quy={d_quy:.3f}, dd_quy={dd_quy:.3f}, e_quy={e_quy:.3f}, "
            f"diem_kpi_quy={(a_quy + b_quy + c_quy + d_quy + dd_quy + e_quy) / 6 * 70:.2f}"
        )
    else:
        # CC thường: giữ nguyên logic cũ (TB 3 tháng)
        diem_kpi_quy = tong_diem_kpi / Decimal("3")

    # === Bước 5: Tính điểm TC quý (GIỮ NGUYÊN logic cũ — deduplicate) ===
    tieu_chi_quy = await lay_tieu_chi_quy(db, cong_chuc_id, thang_list, nam)
    diem_tc_quy = tieu_chi_quy["diem_tc_quy"]

    # === Bước 6: Điểm tổng + xếp loại ===
    diem_tong_quy = diem_kpi_quy + diem_tc_quy
    xep_loai_quy = xep_loai_kpi(float(diem_tong_quy))  # A/B/C/D

    # Ghi chú nếu thiếu data
    ghi_chu = None
    if so_thang_co_du_lieu == 0:
        ghi_chu = "Chưa có báo cáo hoặc kê khai tháng nào trong quý"
    elif so_thang_co_du_lieu < 3:
        thang_thieu = [t for t in thang_list if not any(ct["co_du_lieu"] and ct["thang"] == t for ct in cac_thang)]
        if thang_thieu:
            ghi_chu = f"Thiếu dữ liệu tháng: {', '.join(map(str, thang_thieu))}"

    return {
        "diem_kpi_quy": float(diem_kpi_quy),
        "diem_tc_quy": float(diem_tc_quy),
        "diem_tong_quy": float(diem_tong_quy),
        "xep_loai_quy": xep_loai_quy,
        "co_chuyen_don_vi": False,
        "so_thang_co_du_lieu": so_thang_co_du_lieu,
        "ghi_chu": ghi_chu,
        "cac_thang": cac_thang,
        "tieu_chi_quy": tieu_chi_quy,
    }
