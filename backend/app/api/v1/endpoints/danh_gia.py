"""
app/api/v1/endpoints/danh_gia.py
================================
API Endpoints cho Module Đánh giá Tiêu chí chung.

THAY ĐỔI CHÍNH v3.5.0:
1. THÊM endpoint POST /{id}/tu-choi-tieu-chi (trước đó THIẾU → gây lỗi)
2. FIX: Phê duyệt cấp 1 phải set trang_thai_tc = CHO_CAP2 (thay vì giữ CHO_PHE_DUYET)
3. FIX: Query chờ phê duyệt nhận dạng CHO_CAP2 cho cấp 2
4. FIX: Lịch sử hỗ trợ filter TU_CHOI
5. FIX: Response cho-phe-duyet thêm cap_phe_duyet_hien_tai, ly_do_tu_choi_tc
6. FIX: Tự đánh giá block CHO_CAP2 (không cho CC sửa khi đang chờ cấp 2)

THAY ĐỔI v2.6.0 (giữ nguyên):
1. Phê duyệt tiêu chí 2 cấp: Phó ĐT (cấp 1) → ĐT (cấp 2)
2. Thêm cột trang_thai_tc, diem_tc_cap1, diem_tc_cap2
3. Response có thêm thông tin cấp 2

Phiên bản: 3.5.0 (02/02/2026)
"""

import calendar
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, aliased

from app.api.deps import DatabaseDep, ActiveUserDep, is_qldv
from app.core.kpi_version import resolve_kpi_version
from app.core.thong_bao_helper import gui_thong_bao
from app.models.kpi_assessment import (
    DanhGiaThang,
    TieuChiChung,
    TieuChiChungDanhGia,
    TrangThaiTieuChi,
    TrangThaiDanhGia,
)
from app.models.user_org import CongChuc, VaiTro, CapBacVaiTro
from app.models.bao_cao_xep_loai import BaoCaoXepLoai, TrangThaiBaoCao
from app.schemas.common import success_response, error_response
from app.schemas.assessment import (
    TrangThaiTieuChiEnum,
    TrangThaiDanhGiaThangEnum,
    TuDanhGiaTieuChiRequest,
    PheDuyetTieuChiRequest,
    PheDuyetTieuChiBulkRequest,
    DieuChinhDanhGiaThangRequest,  # Lãnh đạo chỉnh điểm Đánh giá tháng ở giai đoạn báo cáo
    TuChoiTieuChiRequest,  # v3.5
    TieuChiItemResponse,
    TieuChiChungTongHop,
    TuDanhGiaResponse,
    DanhGiaThangTieuChiResponse,
    DanhSachChoPheDuyetItem,
    DanhSachChoPheDuyetResponse,
    ChiTietPheDuyetResponse,
    PheDuyetTieuChiResponse,
    PheDuyetBulkResponse,
    TieuChiChungMasterResponse,
    DanhMucTieuChiResponse,
    NguoiPheDuyetOption,
    DanhSachNguoiPheDuyetResponse,
    TIEU_CHI_DIEM_TOI_DA,
    TIEU_CHI_GIA_TRI_MAC_DINH,
    tinh_diem_binary,
    build_virtual_tieu_chi_response,
    build_virtual_tong_hop,
)


router = APIRouter()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _diem_pd_tu_ld(tc) -> Decimal:
    """
    Tính điểm phê duyệt từ phán quyết LĐ (boolean).

    v3.6 (08/05/2026): CC có thể tự chấm điểm thập phân (bội số 0.5). Khi LĐ
    tick "Đạt" → giữ nguyên điểm CC tự chấm thay vì ép full điểm tối đa. Khi
    "Không đạt" → 0.
    """
    if tc.is_achieved_ld:
        return tc.diem_tu_cham if tc.diem_tu_cham is not None else Decimal("0")
    return Decimal("0")


# v3.6 (12/05/2026): Snapshot điểm Phó ĐT chấm per-TC qua prefix [PDV:N]
# trong tc.ly_do_dieu_chinh — tránh phải migration thêm cột.
_PDV_SNAPSHOT_REGEX = re.compile(r"^\[PDV:([\d.]+)\]\s*")


def _strip_pdv_snapshot(text: Optional[str]) -> str:
    """Bỏ prefix [PDV:N] khỏi ly_do_dieu_chinh để lấy lý do gốc."""
    if not text:
        return ""
    return _PDV_SNAPSHOT_REGEX.sub("", text).strip()


def _parse_pdv_diem(text: Optional[str]) -> Optional[float]:
    """Parse điểm PDV chấm từ prefix [PDV:N]. None nếu không có snapshot."""
    if not text:
        return None
    m = _PDV_SNAPSHOT_REGEX.match(text)
    if not m:
        return None
    try:
        return float(m.group(1))
    except (ValueError, TypeError):
        return None


def _save_pdv_snapshot(tc, pdv_diem: float) -> None:
    """Ghi snapshot [PDV:N] vào tc.ly_do_dieu_chinh (preserve lý do hiện có)."""
    cur = _strip_pdv_snapshot(tc.ly_do_dieu_chinh)
    # Format điểm: nguyên thì không hiển thị .0, lẻ giữ 1 chữ số
    diem_str = f"{pdv_diem:g}"
    prefix = f"[PDV:{diem_str}]"
    tc.ly_do_dieu_chinh = f"{prefix} {cur}".strip() if cur else prefix


def _apply_dieu_chinh_ld(tc, dc, *, fallback: str = "cc") -> None:
    """
    Áp dụng điều chỉnh LĐ lên 1 record TieuChiChungDanhGia.

    v3.6 (08/05/2026): hỗ trợ 2 mode payload trong `dc`:
    - `diem_phe_duyet` (số thập phân): LĐ chấm trực tiếp 0 → diem_toi_da.
       Backend suy `is_achieved_ld = (diem >= diem_toi_da)`.
    - `is_achieved_ld` (boolean, legacy): tick "Đạt" → giữ diem_tu_cham,
       "Không đạt" → 0. Dùng helper `_diem_pd_tu_ld`.

    Khi `dc is None`, hành vi phụ thuộc `fallback`:
    - "cc"  : đồng ý với CC → is_achieved_ld = is_achieved_cc, diem = diem_tu_cham
    - "keep": ĐT đồng ý quyết định Phó ĐT → GIỮ NGUYÊN diem_phe_duyet & is_achieved_ld
              đã có. v3.6 BUG FIX (12/05/2026): KHÔNG recompute từ is_achieved_ld
              vì điểm có thể thập phân (CC chấm 2.0 < max 2.5 → is_achieved_ld=False
              nhưng diem_phe_duyet=2.0 vẫn hợp lệ). Recompute sẽ mất điểm.
    """
    if dc is None:
        if fallback == "keep":
            # Giữ nguyên diem_phe_duyet đã có. Chỉ fallback về diem_tu_cham
            # khi chưa có gì (edge case: TDV duyệt thẳng mà PDV chưa duyệt).
            if tc.diem_phe_duyet is None:
                tc.diem_phe_duyet = (
                    tc.diem_tu_cham if tc.diem_tu_cham is not None else Decimal("0")
                )
                if tc.is_achieved_ld is None:
                    tc.is_achieved_ld = tc.is_achieved_cc
        else:
            tc.is_achieved_ld = tc.is_achieved_cc
            tc.diem_phe_duyet = (
                tc.diem_tu_cham if tc.diem_tu_cham is not None else Decimal("0")
            )
        return

    if dc.diem_phe_duyet is not None:
        diem_max = Decimal(str(tc.tieu_chi.diem_toi_da)) if tc.tieu_chi else None
        diem = Decimal(str(dc.diem_phe_duyet))
        tc.diem_phe_duyet = diem
        tc.is_achieved_ld = (diem_max is not None and diem >= diem_max)
    else:
        tc.is_achieved_ld = bool(dc.is_achieved_ld)
        tc.diem_phe_duyet = _diem_pd_tu_ld(tc)

    if dc.ly_do_dieu_chinh:
        tc.ly_do_dieu_chinh = dc.ly_do_dieu_chinh

# =============================================================================
# NỚI HẠN (2026-04-21): Cho phép tự đánh giá + phê duyệt tiêu chí chung cho mọi
# tháng từ 2026-01 trở đi để CC bổ sung các tháng còn thiếu.
# Xem thêm: CONFIRM với người dùng ngày 2026-04-21.
# Gia hạn 2026-06-02: 2026-05-31 → 2026-07-31 (xử lý tồn đọng CC chuyển đơn vị).
# Cập nhật 2026-07-04: mở VÔ THỜI HẠN (bỏ mốc hết hạn theo ngày) — user xác nhận.
#   • Thời gian: mọi tháng ≥ 2026-01 luôn mở, KHÔNG còn auto-khóa theo ngày.
#   • Vẫn TÔN TRỌNG khóa CCT (is_khoa): tháng đã duyệt báo cáo xếp loại vẫn khóa.
#   • Muốn bật lại auto-khóa theo ngày: gán HAN_MO_RONG_TAM_THOI_DEN = date(...).
# =============================================================================
HAN_MO_RONG_TAM_THOI_DEN = None  # None = vô thời hạn; gán date(...) để bật lại hạn
MO_RONG_TU_THANG_NAM = (2026, 1)  # (năm, tháng) — tuple để so sánh


def _trong_han_mo_rong_tam_thoi(thang: int, nam: int) -> bool:
    """True nếu tháng/năm ≥ 2026-01 và (nếu có mốc) vẫn trong hạn."""
    if HAN_MO_RONG_TAM_THOI_DEN is not None and date.today() > HAN_MO_RONG_TAM_THOI_DEN:
        return False
    return (nam, thang) >= MO_RONG_TU_THANG_NAM


def kiem_tra_thoi_han_tu_danh_gia(thang: int, nam: int) -> bool:
    """Kiểm tra có trong thời hạn tự đánh giá không.

    Quy tắc: Trước ngày 10 tháng sau (BUSINESS_RULES §1.2)
    - Tháng hiện tại: luôn cho phép
    - Tháng trước: cho phép nếu ngày ≤ 10
    """
    # Nới tạm thời đến HAN_MO_RONG_TAM_THOI_DEN — cho phép mọi tháng ≥ 2026-01
    # Vẫn chặn tháng tương lai
    today = date.today()
    if _trong_han_mo_rong_tam_thoi(thang, nam) and (nam, thang) <= (today.year, today.month):
        return True

    if thang == today.month and nam == today.year:
        return True
    prev_month = 12 if today.month == 1 else today.month - 1
    prev_year = today.year - 1 if today.month == 1 else today.year
    if thang == prev_month and nam == prev_year and today.day <= 30:
        return True
    return False


def _dang_bi_khoa(danh_gia: "DanhGiaThang") -> bool:
    """TÔN TRỌNG khóa CCT: tháng đã duyệt báo cáo xếp loại (is_khoa) thì khóa.

    Từ 2026-07-04 KHÔNG còn bypass is_khoa theo window nữa — mở vô thời hạn chỉ
    áp cho giới hạn THỜI GIAN (xem `kiem_tra_thoi_han_tu_danh_gia`), còn khóa CCT
    vẫn được tôn trọng để bảo toàn dữ liệu đã chốt.
    """
    return bool(danh_gia.is_khoa)


def _co_the_duyet_tc(dg: "DanhGiaThang", current_user) -> bool:
    """True nếu current_user được phép phê duyệt tiêu chí chung của đơn `dg` lúc này.

    Bao gồm:
    - Người được gán duyệt cấp 1 (chưa duyệt cấp 1), hoặc cấp 2 (đã qua cấp 1, chưa cấp 2).
    - v3.7 (02/06/2026): LĐ (Phó ĐT/ĐT) của ĐƠN VỊ HIỆN TẠI của CC — xử lý CC chuyển
      đơn vị khi người được gán duyệt vẫn là LĐ đơn vị cũ. Action thực tế vẫn được
      guard ở endpoint phê duyệt (theo cấp bậc + same_don_vi).
    FE dùng cờ `co_the_duyet` này để hiện nút Duyệt/Từ chối.
    """
    if dg.trang_thai_tc not in (
        TrangThaiTieuChi.CHO_PHE_DUYET, TrangThaiTieuChi.CHO_CAP2, None
    ):
        return False
    if dg.ngay_phe_duyet_tc_cap2:
        return False
    uid = current_user.id
    # 1) Người được gán duyệt (luồng chuẩn) — giữ nguyên hành vi cũ
    if dg.nguoi_phe_duyet_tc_cap1_id == uid and not dg.ngay_phe_duyet_tc_cap1:
        return True
    if (dg.nguoi_phe_duyet_tc_cap2_id == uid and dg.ngay_phe_duyet_tc_cap1
            and not dg.ngay_phe_duyet_tc_cap2):
        return True

    # 2) v3.7: LĐ ĐV HIỆN TẠI của CC — CHỈ cho đơn MỒ CÔI do chuyển ĐV.
    # Điều kiện chặt để tránh "nhảy" sai người duyệt:
    #   - Người kê khai là CC thường (is_lanh_dao=False). LĐ (TDV/PCCT) gửi lên CCT
    #     ở đơn vị khác là HỢP LỆ, KHÔNG được reroute về Phó ĐT.
    #   - Người được gán duyệt ở cấp đang chờ KHÔNG còn thuộc ĐV hiện tại của CC
    #     (đã chuyển đi) hoặc chưa được gán.
    cc = dg.cong_chuc
    if not cc or cc.is_lanh_dao or cc.don_vi_id != current_user.don_vi_id:
        return False
    cap = current_user.vai_tro.cap_bac if current_user.vai_tro else None
    cc_dv = cc.don_vi_id
    if not dg.ngay_phe_duyet_tc_cap1:
        # Đang chờ cấp 1 (hoặc duyệt thẳng): xét người được gán cấp 1
        pd1 = dg.nguoi_phe_duyet_tc_cap1
        cap1_orphan = pd1 is None or pd1.don_vi_id != cc_dv
        if cap1_orphan and cap in (CapBacVaiTro.PHO_DON_VI, CapBacVaiTro.TRUONG_DON_VI):
            return True
    elif not dg.ngay_phe_duyet_tc_cap2:
        # Đã qua cấp 1, chờ cấp 2: xét người được gán cấp 2
        pd2 = dg.nguoi_phe_duyet_tc_cap2
        cap2_orphan = pd2 is None or pd2.don_vi_id != cc_dv
        if cap2_orphan and cap == CapBacVaiTro.TRUONG_DON_VI:
            return True
    return False


async def get_or_create_danh_gia_thang(
    db: AsyncSession, cong_chuc_id: UUID, thang: int, nam: int
) -> tuple[DanhGiaThang, bool]:
    """Lấy hoặc tạo mới DanhGiaThang cho CC."""
    stmt = select(DanhGiaThang).where(
        DanhGiaThang.cong_chuc_id == cong_chuc_id,
        DanhGiaThang.thang == thang,
        DanhGiaThang.nam == nam,
        DanhGiaThang.is_deleted == False
    )
    result = await db.execute(stmt)
    danh_gia = result.scalar_one_or_none()

    if danh_gia:
        return danh_gia, False

    # Get cong_chuc's current don_vi_id for snapshot
    cc_stmt = select(CongChuc).where(CongChuc.id == cong_chuc_id)
    cc_result = await db.execute(cc_stmt)
    cong_chuc = cc_result.scalar_one_or_none()
    if not cong_chuc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="USER_NOT_FOUND", message="Công chức không tồn tại")
        )

    so_ngay = calendar.monthrange(nam, thang)[1]

    # PL3 V2 (28/04/2026): xác định version theo kê khai đầu / pin / default
    version_tinh_diem = await resolve_kpi_version(db, cong_chuc_id, thang, nam)

    danh_gia = DanhGiaThang(
        cong_chuc_id=cong_chuc_id,
        don_vi_id_snapshot=cong_chuc.don_vi_id,
        thang=thang,
        nam=nam,
        so_ngay_lam_viec=so_ngay,
        trang_thai=TrangThaiDanhGia.DANG_DANH_GIA,
        version_tinh_diem=version_tinh_diem,
    )
    db.add(danh_gia)
    await db.flush()
    await db.refresh(danh_gia)
    return danh_gia, True


async def tinh_tong_diem_tieu_chi_chung(
    tieu_chi_list: List[TieuChiChungDanhGia], use_ld: bool = False
) -> TieuChiChungTongHop:
    """Tính tổng điểm tiêu chí chung theo nhóm."""
    nhom_1, nhom_2, nhom_3 = Decimal("0"), Decimal("0"), Decimal("0")
    
    for tc_dg in tieu_chi_list:
        tc = tc_dg.tieu_chi
        # Ưu tiên điểm "Đánh giá tháng" (LĐ chỉnh ở báo cáo xếp loại) nếu có,
        # rồi mới đến điểm phê duyệt, cuối cùng là điểm CC tự chấm.
        if use_ld and tc_dg.diem_danh_gia_thang is not None:
            diem = tc_dg.diem_danh_gia_thang
        elif use_ld and tc_dg.diem_phe_duyet is not None:
            diem = tc_dg.diem_phe_duyet
        else:
            diem = tc_dg.diem_tu_cham
        if tc.nhom_tieu_chi == 1:
            nhom_1 += diem
        elif tc.nhom_tieu_chi == 2:
            nhom_2 += diem
        elif tc.nhom_tieu_chi == 3:
            nhom_3 += diem
    
    return TieuChiChungTongHop(
        nhom_1_diem=float(nhom_1), nhom_2_diem=float(nhom_2),
        nhom_3_diem=float(nhom_3), tong_diem=float(nhom_1 + nhom_2 + nhom_3)
    )


def build_tieu_chi_response(tc_dg: TieuChiChungDanhGia, dgt_id: Optional[UUID] = None) -> TieuChiItemResponse:
    """Build TieuChiItemResponse từ model."""
    tc = tc_dg.tieu_chi
    is_achieved = tc_dg.is_achieved_ld if tc_dg.is_achieved_ld is not None else tc_dg.is_achieved_cc
    diem = float(tc_dg.diem_phe_duyet) if tc_dg.diem_phe_duyet is not None else float(tc_dg.diem_tu_cham)

    # v3.6 (12/05/2026): parse snapshot điểm PDV từ prefix [PDV:N] trong ly_do_dieu_chinh.
    diem_pdv = _parse_pdv_diem(tc_dg.ly_do_dieu_chinh)
    ly_do_clean = _strip_pdv_snapshot(tc_dg.ly_do_dieu_chinh) or None

    return TieuChiItemResponse(
        id=tc_dg.id,
        danh_gia_thang_id=dgt_id or tc_dg.danh_gia_thang_id,
        tieu_chi_id=tc_dg.tieu_chi_id,
        ma_tieu_chi=tc.ma_tieu_chi,
        ten_tieu_chi=tc.ten_tieu_chi,
        nhom_tieu_chi=tc.nhom_tieu_chi,
        diem_toi_da=float(tc.diem_toi_da),
        gia_tri_mac_dinh=tc.gia_tri_mac_dinh,
        is_achieved_cc=tc_dg.is_achieved_cc,
        is_achieved_ld=tc_dg.is_achieved_ld,
        is_achieved=is_achieved,
        diem_tu_cham=float(tc_dg.diem_tu_cham),
        diem_phe_duyet=float(tc_dg.diem_phe_duyet) if tc_dg.diem_phe_duyet is not None else None,
        diem_pdv=diem_pdv,
        diem=diem,
        diem_danh_gia_thang=float(tc_dg.diem_danh_gia_thang) if tc_dg.diem_danh_gia_thang is not None else None,
        trang_thai=TrangThaiTieuChiEnum(tc_dg.trang_thai.value),
        ghi_chu_cc=tc_dg.ghi_chu_cc,
        ghi_chu_ld=tc_dg.ghi_chu_ld,
        ly_do_dieu_chinh=ly_do_clean,
        ngay_gui=tc_dg.ngay_gui,
        ngay_phe_duyet=tc_dg.ngay_phe_duyet,
    )


def build_danh_gia_thang_response(danh_gia: DanhGiaThang) -> dict:
    """
    Build response cho DanhGiaThang với thông tin phê duyệt tiêu chí 2 cấp.
    v2.6: Thêm thông tin phê duyệt tiêu chí cấp 1 và cấp 2
    """
    # Thông tin người phê duyệt tiêu chí cấp 1
    nguoi_phe_duyet_tc_cap1_data = None
    if hasattr(danh_gia, 'nguoi_phe_duyet_tc_cap1') and danh_gia.nguoi_phe_duyet_tc_cap1:
        npd1 = danh_gia.nguoi_phe_duyet_tc_cap1
        nguoi_phe_duyet_tc_cap1_data = {
            "id": npd1.id,
            "ma_cc": npd1.ma_cc,
            "ho_ten": npd1.ho_ten,
            "chuc_vu": npd1.chuc_vu,
            # v3.6 (12/05/2026): FE cần cap_bac để phân biệt 2-cấp vs duyệt thẳng
            "cap_bac": npd1.vai_tro.cap_bac.value if npd1.vai_tro and npd1.vai_tro.cap_bac else None,
            "ma_vai_tro": npd1.vai_tro.ma_vai_tro if npd1.vai_tro else None,
        }
    
    # Thông tin người phê duyệt tiêu chí cấp 2
    nguoi_phe_duyet_tc_cap2_data = None
    if hasattr(danh_gia, 'nguoi_phe_duyet_tc_cap2') and danh_gia.nguoi_phe_duyet_tc_cap2:
        npd2 = danh_gia.nguoi_phe_duyet_tc_cap2
        nguoi_phe_duyet_tc_cap2_data = {
            "id": npd2.id,
            "ma_cc": npd2.ma_cc,
            "ho_ten": npd2.ho_ten,
            "chuc_vu": npd2.chuc_vu,
            # v3.6 (12/05/2026): cap_bac cho consistency với cap1
            "cap_bac": npd2.vai_tro.cap_bac.value if npd2.vai_tro and npd2.vai_tro.cap_bac else None,
            "ma_vai_tro": npd2.vai_tro.ma_vai_tro if npd2.vai_tro else None,
        }
    
    return {
        "danh_gia_thang_id": danh_gia.id,
        "cong_chuc_id": danh_gia.cong_chuc_id,
        "thang": danh_gia.thang,
        "nam": danh_gia.nam,
        "is_khoa": danh_gia.is_khoa,
        
        # Phê duyệt tiêu chí 2 cấp
        "trang_thai_tc": danh_gia.trang_thai_tc.value if danh_gia.trang_thai_tc else None,
        "nguoi_phe_duyet_tc_cap1_id": danh_gia.nguoi_phe_duyet_tc_cap1_id,
        "nguoi_phe_duyet_tc_cap1": nguoi_phe_duyet_tc_cap1_data,
        "ngay_phe_duyet_tc_cap1": danh_gia.ngay_phe_duyet_tc_cap1.isoformat() if danh_gia.ngay_phe_duyet_tc_cap1 else None,
        "diem_tc_cap1": float(danh_gia.diem_tc_cap1) if danh_gia.diem_tc_cap1 is not None else None,
        
        "nguoi_phe_duyet_tc_cap2_id": danh_gia.nguoi_phe_duyet_tc_cap2_id,
        "nguoi_phe_duyet_tc_cap2": nguoi_phe_duyet_tc_cap2_data,
        "ngay_phe_duyet_tc_cap2": danh_gia.ngay_phe_duyet_tc_cap2.isoformat() if danh_gia.ngay_phe_duyet_tc_cap2 else None,
        "diem_tc_cap2": float(danh_gia.diem_tc_cap2) if danh_gia.diem_tc_cap2 is not None else None,
        
        # Điểm tiêu chí chung final
        "diem_tieu_chi_chung": float(danh_gia.diem_tieu_chi_chung) if danh_gia.diem_tieu_chi_chung is not None else None,
        
        # v3.5: Thông tin từ chối
        "ly_do_tu_choi_tc": danh_gia.ly_do_tu_choi_tc if hasattr(danh_gia, 'ly_do_tu_choi_tc') else None,
        "nguoi_tu_choi_tc_id": danh_gia.nguoi_tu_choi_tc_id if hasattr(danh_gia, 'nguoi_tu_choi_tc_id') else None,
        "ngay_tu_choi_tc": danh_gia.ngay_tu_choi_tc.isoformat() if hasattr(danh_gia, 'ngay_tu_choi_tc') and danh_gia.ngay_tu_choi_tc else None,
        
        # v3.5: Cấp phê duyệt hiện tại
        "cap_phe_duyet_hien_tai": "cap2" if danh_gia.trang_thai_tc == TrangThaiTieuChi.CHO_CAP2 else ("cap1" if danh_gia.trang_thai_tc in [TrangThaiTieuChi.CHO_PHE_DUYET, None] else None),
    }


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get("/tieu-chi-chung")
async def get_danh_muc_tieu_chi_chung(db: DatabaseDep, current_user: ActiveUserDep) -> dict:
    """Lấy danh mục tiêu chí chung (master data)."""
    stmt = select(TieuChiChung).where(
        TieuChiChung.is_active == True,
        TieuChiChung.ma_tieu_chi_con.is_(None)
    ).order_by(TieuChiChung.thu_tu)
    
    result = await db.execute(stmt)
    tc_list = result.scalars().all()
    
    nhom_1, nhom_2, nhom_3 = [], [], []
    for tc in tc_list:
        tc_resp = TieuChiChungMasterResponse(
            id=tc.id, ma_tieu_chi=tc.ma_tieu_chi, ma_tieu_chi_con=tc.ma_tieu_chi_con,
            nhom_tieu_chi=tc.nhom_tieu_chi, ten_tieu_chi=tc.ten_tieu_chi,
            mo_ta=tc.mo_ta, diem_toi_da=float(tc.diem_toi_da),
            gia_tri_mac_dinh=tc.gia_tri_mac_dinh,
            loai_logic=tc.loai_logic.value if hasattr(tc.loai_logic, 'value') else tc.loai_logic,
            parent_ma_tieu_chi=tc.parent_ma_tieu_chi, thu_tu=tc.thu_tu,
        )
        if tc.nhom_tieu_chi == 1: nhom_1.append(tc_resp)
        elif tc.nhom_tieu_chi == 2: nhom_2.append(tc_resp)
        elif tc.nhom_tieu_chi == 3: nhom_3.append(tc_resp)
    
    return success_response(
        data=DanhMucTieuChiResponse(nhom_1=nhom_1, nhom_2=nhom_2, nhom_3=nhom_3),
        message="Lấy danh mục tiêu chí chung thành công"
    )


@router.get("/nguoi-phe-duyet")
async def get_nguoi_phe_duyet(db: DatabaseDep, current_user: ActiveUserDep) -> dict:
    """Lấy danh sách người phê duyệt phù hợp."""
    approvers, ghi_chu = [], None
    vai_tro = current_user.vai_tro
    
    if not vai_tro:
        return success_response(
            data=DanhSachNguoiPheDuyetResponse(danh_sach=[], ghi_chu="Không có vai trò"),
            message="Không có người phê duyệt"
        )
    
    cap_bac = vai_tro.cap_bac
    
    if cap_bac == CapBacVaiTro.CHI_CUC_TRUONG:
        approvers.append(NguoiPheDuyetOption(
            id=current_user.id, ma_cc=current_user.ma_cc,
            ho_ten=current_user.ho_ten, chuc_vu=current_user.chuc_vu
        ))
        ghi_chu = "Chi cục trưởng tự phê duyệt"
    elif cap_bac in [CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.TRUONG_DON_VI]:
        stmt = select(CongChuc).join(VaiTro).where(
            CongChuc.is_active == True, VaiTro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG
        )
        result = await db.execute(stmt)
        for cct in result.scalars().all():
            approvers.append(NguoiPheDuyetOption(
                id=cct.id, ma_cc=cct.ma_cc, ho_ten=cct.ho_ten, chuc_vu=cct.chuc_vu
            ))
        ghi_chu = "Người phê duyệt: Chi cục trưởng"
    elif cap_bac == CapBacVaiTro.PHO_DON_VI:
        # v2.6: Phó ĐT gửi cho ĐT duyệt (1 cấp)
        stmt = select(CongChuc).join(VaiTro).where(
            CongChuc.is_active == True, CongChuc.don_vi_id == current_user.don_vi_id,
            VaiTro.cap_bac == CapBacVaiTro.TRUONG_DON_VI
        )
        result = await db.execute(stmt)
        for tdv in result.scalars().all():
            approvers.append(NguoiPheDuyetOption(
                id=tdv.id, ma_cc=tdv.ma_cc, ho_ten=tdv.ho_ten, chuc_vu=tdv.chuc_vu
            ))
        ghi_chu = "Người phê duyệt: Đội trưởng"
    else:
        # v3.6: CC thường thấy CẢ Phó ĐT (cấp 1) VÀ Đội trưởng (gửi thẳng)
        # Phó ĐT
        stmt_pho = select(CongChuc).join(VaiTro).where(
            CongChuc.is_active == True, CongChuc.don_vi_id == current_user.don_vi_id,
            VaiTro.cap_bac == CapBacVaiTro.PHO_DON_VI
        )
        result = await db.execute(stmt_pho)
        for pdv in result.scalars().all():
            approvers.append(NguoiPheDuyetOption(
                id=pdv.id, ma_cc=pdv.ma_cc,
                ho_ten=f"{pdv.ho_ten} (Phó ĐT - cấp 1)", chuc_vu=pdv.chuc_vu
            ))
        
        # Đội trưởng (gửi thẳng)
        stmt_dt = select(CongChuc).join(VaiTro).where(
            CongChuc.is_active == True, CongChuc.don_vi_id == current_user.don_vi_id,
            VaiTro.cap_bac == CapBacVaiTro.TRUONG_DON_VI
        )
        result = await db.execute(stmt_dt)
        for tdv in result.scalars().all():
            approvers.append(NguoiPheDuyetOption(
                id=tdv.id, ma_cc=tdv.ma_cc,
                ho_ten=f"{tdv.ho_ten} (Đội trưởng - duyệt thẳng)", chuc_vu=tdv.chuc_vu
            ))
        
        ghi_chu = "Chọn Phó ĐT (qua 2 cấp) hoặc Đội trưởng (duyệt thẳng)"
    
    return success_response(
        data=DanhSachNguoiPheDuyetResponse(danh_sach=approvers, ghi_chu=ghi_chu),
        message="Lấy danh sách người phê duyệt thành công"
    )


@router.get("/tieu-chi/thang/{thang}/nam/{nam}")
async def get_tu_danh_gia_tieu_chi(
    db: DatabaseDep, current_user: ActiveUserDep, thang: int, nam: int
) -> dict:
    """
    Xem tự đánh giá tiêu chí chung của bản thân.
    
    VIRTUAL RECORD: Trả về dữ liệu ảo nếu chưa có bản ghi (thay vì 404).
    """
    if thang < 1 or thang > 12:
        raise HTTPException(status_code=400, detail=error_response(code="VAL_003", message="Tháng phải từ 1-12"))
    
    so_ngay_thang = calendar.monthrange(nam, thang)[1]
    so_ngay_nghi = 0  # TODO: Tích hợp module nghỉ phép
    so_ngay_lv = so_ngay_thang - so_ngay_nghi
    target_kpi = so_ngay_lv * 96
    
    # Query đánh giá tháng
    stmt = select(DanhGiaThang).options(
        selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(TieuChiChungDanhGia.tieu_chi),
        selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(TieuChiChungDanhGia.nguoi_phe_duyet),
        selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap1).selectinload(CongChuc.vai_tro),
        selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap2).selectinload(CongChuc.vai_tro),
    ).where(
        DanhGiaThang.cong_chuc_id == current_user.id,
        DanhGiaThang.thang == thang, DanhGiaThang.nam == nam,
        DanhGiaThang.is_deleted == False
    )
    result = await db.execute(stmt)
    danh_gia = result.scalar_one_or_none()
    
    # =========================================================================
    # VIRTUAL RECORD - Chưa có dữ liệu
    # =========================================================================
    if not danh_gia or not danh_gia.tieu_chi_chungs:
        tieu_chi = [build_virtual_tieu_chi_response(m) for m in ["1.1", "1.2", "2.1", "2.2", "2.3", "2.4", "3.1", "3.2", "3.3", "3.4"]]
        return success_response(
            data=DanhGiaThangTieuChiResponse(
                danh_gia_thang_id=danh_gia.id if danh_gia else None,
                cong_chuc_id=current_user.id, thang=thang, nam=nam,
                is_new_record=True,
                so_ngay_trong_thang=so_ngay_thang, so_ngay_nghi_phep=so_ngay_nghi,
                so_ngay_lam_viec=so_ngay_lv, target_kpi=float(target_kpi),
                trang_thai=TrangThaiTieuChiEnum.CHUA_DANH_GIA,
                trang_thai_danh_gia_thang=TrangThaiDanhGiaThangEnum.CHUA_DANH_GIA,
                tong_hop=build_virtual_tong_hop(),
                tieu_chi=tieu_chi,
            ),
            message="Chưa có dữ liệu. Hiển thị giá trị mặc định."
        )
    
    # =========================================================================
    # EXISTING RECORD
    # =========================================================================
    tc_responses = [build_tieu_chi_response(tc, danh_gia.id) for tc in danh_gia.tieu_chi_chungs]
    any_approved = any(tc.trang_thai == TrangThaiTieuChi.DA_PHE_DUYET for tc in danh_gia.tieu_chi_chungs)
    tong_hop = await tinh_tong_diem_tieu_chi_chung(danh_gia.tieu_chi_chungs, use_ld=any_approved)
    
    first_tc = danh_gia.tieu_chi_chungs[0] if danh_gia.tieu_chi_chungs else None
    trang_thai_tc = TrangThaiTieuChiEnum(first_tc.trang_thai.value) if first_tc else TrangThaiTieuChiEnum.NHAP
    
    # v2.6: Thêm thông tin phê duyệt 2 cấp
    response_data = DanhGiaThangTieuChiResponse(
        danh_gia_thang_id=danh_gia.id, cong_chuc_id=current_user.id,
        thang=thang, nam=nam, is_new_record=False,
        so_ngay_trong_thang=so_ngay_thang,
        so_ngay_nghi_phep=danh_gia.so_ngay_nghi_phep or 0,
        so_ngay_lam_viec=danh_gia.so_ngay_lam_viec or so_ngay_lv,
        target_kpi=float((danh_gia.so_ngay_lam_viec or so_ngay_lv) * 96),
        trang_thai=trang_thai_tc,
        trang_thai_danh_gia_thang=TrangThaiDanhGiaThangEnum(danh_gia.trang_thai.value),
        tong_hop=tong_hop, tieu_chi=tc_responses,
        nguoi_phe_duyet_id=first_tc.nguoi_phe_duyet_id if first_tc else None,
        nguoi_phe_duyet_ten=first_tc.nguoi_phe_duyet.ho_ten if first_tc and first_tc.nguoi_phe_duyet else None,
        ngay_gui=first_tc.ngay_gui if first_tc else None,
        ngay_phe_duyet=first_tc.ngay_phe_duyet if first_tc else None,
    )
    
    # Thêm thông tin phê duyệt 2 cấp vào response
    extra_data = build_danh_gia_thang_response(danh_gia)
    
    return success_response(
        data={
            **response_data.model_dump(),
            **extra_data,
        },
        message="Lấy dữ liệu tự đánh giá thành công"
    )


@router.post("/tu-danh-gia")
async def tu_danh_gia_tieu_chi(
    db: DatabaseDep, current_user: ActiveUserDep, payload: TuDanhGiaTieuChiRequest
) -> dict:
    """
    CC tự đánh giá tiêu chí chung.
    
    v2.5.0: Nhận `is_achieved_cc` và `ghi_chu_cc` thay vì `is_achieved`, `ghi_chu`.
    v2.6.0: Gán nguoi_phe_duyet_tc_cap1_id khi gửi phê duyệt
    """
    if not kiem_tra_thoi_han_tu_danh_gia(payload.thang, payload.nam):
        raise HTTPException(status_code=400, detail=error_response(code="BIZ_004", message="Đã hết hạn tự đánh giá"))
    
    danh_gia, is_new = await get_or_create_danh_gia_thang(db, current_user.id, payload.thang, payload.nam)
    
    # v2.6: Kiểm tra khóa dữ liệu (bypass trong window nới tạm thời)
    if _dang_bi_khoa(danh_gia):
        raise HTTPException(status_code=400, detail=error_response(code="BIZ_002", message="Dữ liệu đã bị khóa, không thể chỉnh sửa"))
    
    # Kiểm tra trạng thái
    if not is_new:
        stmt = select(TieuChiChungDanhGia).where(TieuChiChungDanhGia.danh_gia_thang_id == danh_gia.id)
        result = await db.execute(stmt)
        existing = result.scalars().first()
        # v3.5: Chặn CHO_PHE_DUYET, CHO_CAP2, DA_PHE_DUYET. Cho phép NHAP (bao gồm đơn bị từ chối đã reset)
        blocked_states = [TrangThaiTieuChi.CHO_PHE_DUYET, TrangThaiTieuChi.CHO_CAP2, TrangThaiTieuChi.DA_PHE_DUYET]
        if existing and existing.trang_thai in blocked_states:
            raise HTTPException(status_code=400, detail=error_response(code="BIZ_001", message=f"Không thể sửa khi {existing.trang_thai.value}"))
    
    # Lấy master data
    stmt = select(TieuChiChung).where(TieuChiChung.is_active == True, TieuChiChung.ma_tieu_chi_con.is_(None))
    result = await db.execute(stmt)
    master_map = {tc.ma_tieu_chi: tc for tc in result.scalars().all()}
    
    # Xác định người phê duyệt
    nguoi_pd = None
    if payload.gui_phe_duyet and payload.nguoi_phe_duyet_id:
        stmt = select(CongChuc).where(CongChuc.id == payload.nguoi_phe_duyet_id)
        result = await db.execute(stmt)
        nguoi_pd = result.scalar_one_or_none()
    
    # Xóa bản cũ
    if not is_new:
        stmt = select(TieuChiChungDanhGia).where(TieuChiChungDanhGia.danh_gia_thang_id == danh_gia.id)
        result = await db.execute(stmt)
        for old in result.scalars().all():
            await db.delete(old)
        await db.flush()
    
    # Tạo mới
    now = datetime.now()
    created = []
    
    for tc_input in payload.tieu_chi:
        master = master_map.get(tc_input.ma_tieu_chi)
        if not master:
            raise HTTPException(status_code=400, detail=error_response(code="VAL_001", message=f"Mã không hợp lệ: {tc_input.ma_tieu_chi}"))

        # v3.6: ưu tiên diem_tu_cham (CC nhập số trực tiếp).
        # Fallback về is_achieved_cc (legacy) khi diem_tu_cham không được gửi.
        if tc_input.diem_tu_cham is not None:
            diem = float(tc_input.diem_tu_cham)
            diem_max = float(master.diem_toi_da or 0)
            is_achieved = diem >= diem_max - 1e-9
        else:
            is_achieved = bool(tc_input.is_achieved_cc)
            diem = tinh_diem_binary(tc_input.ma_tieu_chi, is_achieved)

        tc_dg = TieuChiChungDanhGia(
            danh_gia_thang_id=danh_gia.id,
            tieu_chi_id=master.id,
            is_achieved_cc=is_achieved,
            is_achieved_ld=None,
            diem_tu_cham=Decimal(str(diem)),
            trang_thai=TrangThaiTieuChi.CHO_PHE_DUYET if payload.gui_phe_duyet else TrangThaiTieuChi.NHAP,
            nguoi_phe_duyet_id=nguoi_pd.id if nguoi_pd else None,
            ngay_gui=now if payload.gui_phe_duyet else None,
            ghi_chu_cc=tc_input.ghi_chu_cc,
        )
        db.add(tc_dg)
        created.append(tc_dg)
    
    # v2.6/v3.6: Cập nhật nguoi_phe_duyet_tc_cap1_id trên DanhGiaThang
    # Nếu CC chọn Đội trưởng → gán cap1 = ĐT (ĐT sẽ duyệt thẳng qua TH đặc biệt)
    if payload.gui_phe_duyet and nguoi_pd:
        # Kiểm tra người được chọn là Phó ĐT hay Đội trưởng
        nguoi_pd_vai_tro = None
        if nguoi_pd.vai_tro:
            nguoi_pd_vai_tro = nguoi_pd.vai_tro.cap_bac
        else:
            # Load vai_tro nếu chưa có
            stmt_vt = select(VaiTro).where(VaiTro.cong_chuc_id == nguoi_pd.id)
            result_vt = await db.execute(stmt_vt)
            vt = result_vt.scalar_one_or_none()
            if vt:
                nguoi_pd_vai_tro = vt.cap_bac

        danh_gia.nguoi_phe_duyet_tc_cap1_id = nguoi_pd.id
        danh_gia.trang_thai_tc = TrangThaiTieuChi.CHO_PHE_DUYET

        # Reset toàn bộ state cũ để tránh pollution khi resubmit (ví dụ tháng
        # trước từng là CC thường + Phó ĐT đã duyệt cap1 → cap2_id bị prefill =
        # ĐT; nếu giờ ĐT tự đánh giá và chọn CCT, data cũ sẽ khiến badge FE
        # hiển thị "Chờ cấp 2" thay vì "Chờ duyệt thẳng").
        danh_gia.nguoi_phe_duyet_tc_cap2_id = None
        danh_gia.ngay_phe_duyet_tc_cap1 = None
        danh_gia.ngay_phe_duyet_tc_cap2 = None
        danh_gia.diem_tc_cap1 = None
        danh_gia.diem_tc_cap2 = None
        danh_gia.diem_tieu_chi_chung = None
        danh_gia.ly_do_tu_choi_tc = None
        danh_gia.nguoi_tu_choi_tc_id = None
        danh_gia.ngay_tu_choi_tc = None
    
    await db.flush()
    for tc in created:
        await db.refresh(tc, ["tieu_chi"])
    
    tong_hop = await tinh_tong_diem_tieu_chi_chung(created, use_ld=False)
    tc_responses = [build_tieu_chi_response(tc, danh_gia.id) for tc in created]
    
    return success_response(
        data=TuDanhGiaResponse(
            success=True,
            message="Đã gửi phê duyệt" if payload.gui_phe_duyet else "Lưu nháp thành công",
            danh_gia_thang_id=danh_gia.id, cong_chuc_id=current_user.id,
            thang=payload.thang, nam=payload.nam, is_new_record=is_new,
            trang_thai=TrangThaiTieuChiEnum.CHO_PHE_DUYET if payload.gui_phe_duyet else TrangThaiTieuChiEnum.NHAP,
            tong_hop=tong_hop, tieu_chi=tc_responses,
            ngay_gui=now if payload.gui_phe_duyet else None,
            nguoi_phe_duyet_id=nguoi_pd.id if nguoi_pd else None,
        ),
        message="Tự đánh giá tiêu chí chung thành công"
    )


@router.get("/tieu-chi/cho-phe-duyet")
async def get_danh_sach_cho_phe_duyet(
    db: DatabaseDep, current_user: ActiveUserDep,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    thang: Optional[int] = Query(default=None, ge=1, le=12),
    nam: Optional[int] = Query(default=None, ge=2025),
) -> dict:
    """
    Lấy danh sách tiêu chí chung chờ phê duyệt.
    v2.6: Hỗ trợ 2 cấp - hiển thị đơn chờ cấp 1 và cấp 2
    v3.6: Thêm QLDV - chỉ xem, không duyệt
    """
    is_qldv_user = is_qldv(current_user)

    # Cho phép: lãnh đạo HOẶC QLDV
    if not current_user.is_lanh_dao and not is_qldv_user:
        raise HTTPException(status_code=403, detail=error_response(code="PERM_002", message="Chỉ lãnh đạo hoặc QLDV"))

    # v2.6: Lọc cả cấp 1 và cấp 2
    # v3.6: QLDV chỉ xem đơn vị của mình (tất cả trạng thái chờ duyệt)
    if is_qldv_user:
        # QLDV: Xem tất cả đơn chờ duyệt trong đơn vị
        stmt = select(DanhGiaThang).options(
            selectinload(DanhGiaThang.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(TieuChiChungDanhGia.tieu_chi),
            selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap1).selectinload(CongChuc.vai_tro),
        ).join(CongChuc).where(
            DanhGiaThang.is_deleted == False,
            CongChuc.don_vi_id == current_user.don_vi_id,
            or_(
                DanhGiaThang.trang_thai_tc == TrangThaiTieuChi.CHO_PHE_DUYET,
                DanhGiaThang.trang_thai_tc == TrangThaiTieuChi.CHO_CAP2,
                DanhGiaThang.trang_thai_tc == None
            )
        ).distinct().order_by(DanhGiaThang.created_at.desc())
    else:
        # Lãnh đạo: theo logic cũ
        # v3.7 (02/06/2026): bổ sung visibility cho LĐ ĐV HIỆN TẠI của CC — NHƯNG CHỈ
        # với đơn MỒ CÔI do chuyển đơn vị, để không "nhảy" sai người duyệt.
        # Mồ côi = (a) người kê khai là CC thường (is_lanh_dao=False — LĐ gửi lên CCT ở
        # ĐV khác là hợp lệ, KHÔNG reroute) VÀ (b) người được gán duyệt ở cấp đang chờ
        # KHÔNG còn thuộc ĐV hiện tại của CC (đã chuyển đi) hoặc chưa được gán.
        cap_bac_cur = current_user.vai_tro.cap_bac if current_user.vai_tro else None
        Pd1 = aliased(CongChuc)  # người được gán duyệt cấp 1
        Pd2 = aliased(CongChuc)  # người được gán duyệt cấp 2
        cap1_orphan = or_(Pd1.id == None, Pd1.don_vi_id != CongChuc.don_vi_id)
        cap2_orphan = or_(Pd2.id == None, Pd2.don_vi_id != CongChuc.don_vi_id)

        don_vi_clauses = []
        if cap_bac_cur == CapBacVaiTro.TRUONG_DON_VI:
            # ĐT: nhận đơn mồ côi của CC trong ĐV — chờ cấp 1 (duyệt thẳng) hoặc chờ cấp 2.
            # CHỈ đơn ĐÃ GỬI (CHO_PHE_DUYET/CHO_CAP2) — loại bỏ NHAP (nháp chưa gửi).
            don_vi_clauses.append(and_(
                CongChuc.don_vi_id == current_user.don_vi_id,
                CongChuc.is_lanh_dao == False,
                DanhGiaThang.trang_thai_tc.in_([
                    TrangThaiTieuChi.CHO_PHE_DUYET, TrangThaiTieuChi.CHO_CAP2
                ]),
                DanhGiaThang.ngay_phe_duyet_tc_cap2 == None,
                or_(
                    and_(DanhGiaThang.ngay_phe_duyet_tc_cap1 == None, cap1_orphan),
                    and_(DanhGiaThang.ngay_phe_duyet_tc_cap1 != None, cap2_orphan),
                ),
            ))
        elif cap_bac_cur == CapBacVaiTro.PHO_DON_VI:
            # Phó ĐT: nhận đơn mồ côi của CC trong ĐV đang chờ cấp 1 (đã gửi, chưa duyệt).
            don_vi_clauses.append(and_(
                CongChuc.don_vi_id == current_user.don_vi_id,
                CongChuc.is_lanh_dao == False,
                DanhGiaThang.trang_thai_tc == TrangThaiTieuChi.CHO_PHE_DUYET,
                DanhGiaThang.ngay_phe_duyet_tc_cap1 == None,
                cap1_orphan,
            ))

        stmt = select(DanhGiaThang).options(
            selectinload(DanhGiaThang.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(TieuChiChungDanhGia.tieu_chi),
            selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap1).selectinload(CongChuc.vai_tro),
            selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap2).selectinload(CongChuc.vai_tro),
        ).join(
            CongChuc, DanhGiaThang.cong_chuc_id == CongChuc.id
        ).outerjoin(
            Pd1, DanhGiaThang.nguoi_phe_duyet_tc_cap1_id == Pd1.id
        ).outerjoin(
            Pd2, DanhGiaThang.nguoi_phe_duyet_tc_cap2_id == Pd2.id
        ).where(
            DanhGiaThang.is_deleted == False,
            or_(
                # Cấp 1: Phó ĐT chờ duyệt
                and_(
                    DanhGiaThang.nguoi_phe_duyet_tc_cap1_id == current_user.id,
                    or_(
                        DanhGiaThang.trang_thai_tc == TrangThaiTieuChi.CHO_PHE_DUYET,
                        DanhGiaThang.trang_thai_tc == None
                    ),
                    DanhGiaThang.ngay_phe_duyet_tc_cap1 == None
                ),
                # Cấp 2: ĐT chờ duyệt (sau khi cấp 1 đã duyệt)
                and_(
                    DanhGiaThang.nguoi_phe_duyet_tc_cap2_id == current_user.id,
                    or_(
                        DanhGiaThang.trang_thai_tc == TrangThaiTieuChi.CHO_CAP2,  # v3.5
                        and_(  # fallback: cũng lọc theo ngay_phe_duyet
                            DanhGiaThang.ngay_phe_duyet_tc_cap1 != None,
                        ),
                    ),
                    DanhGiaThang.ngay_phe_duyet_tc_cap2 == None
                ),
                # v3.7: đơn MỒ CÔI của CC thường đang thuộc đơn vị mình (xử lý chuyển đơn vị)
                *don_vi_clauses,
            )
        ).distinct().order_by(DanhGiaThang.created_at.desc())
    
    # ✅ FIX: Filter theo tháng/năm nếu có
    if thang:
        stmt = stmt.where(DanhGiaThang.thang == thang)
    if nam:
        stmt = stmt.where(DanhGiaThang.nam == nam)
    
    # Fallback: Cũng lọc theo cách cũ (TieuChiChungDanhGia.nguoi_phe_duyet_id)
    # QLDV không cần fallback vì đã lấy theo đơn vị
    if is_qldv_user:
        stmt_fallback = select(DanhGiaThang).where(DanhGiaThang.id == None)  # Empty query
    else:
        stmt_fallback = select(DanhGiaThang).options(
            selectinload(DanhGiaThang.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(TieuChiChungDanhGia.tieu_chi),
            selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap1).selectinload(CongChuc.vai_tro),
        ).join(TieuChiChungDanhGia).where(
            TieuChiChungDanhGia.trang_thai == TrangThaiTieuChi.CHO_PHE_DUYET,
            TieuChiChungDanhGia.nguoi_phe_duyet_id == current_user.id,
            DanhGiaThang.is_deleted == False
        ).distinct().order_by(DanhGiaThang.created_at.desc())
    
    # ✅ FIX: Filter fallback theo tháng/năm
    if thang:
        stmt_fallback = stmt_fallback.where(DanhGiaThang.thang == thang)
    if nam:
        stmt_fallback = stmt_fallback.where(DanhGiaThang.nam == nam)
    
    # Chạy cả 2 query và merge
    result1 = (await db.execute(stmt)).scalars().unique().all()
    result2 = (await db.execute(stmt_fallback)).scalars().unique().all()
    
    # Merge và dedupe
    seen_ids = set()
    danh_gias = []
    for dg in list(result1) + list(result2):
        if dg.id not in seen_ids:
            seen_ids.add(dg.id)
            danh_gias.append(dg)
    
    total = len(danh_gias)
    
    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    danh_gias_page = danh_gias[start:end]
    
    items = []
    for dg in danh_gias_page:
        tc_list = [tc for tc in dg.tieu_chi_chungs if tc.trang_thai == TrangThaiTieuChi.CHO_PHE_DUYET]
        if not tc_list:
            # v2.6: Có thể đơn đã duyệt cấp 1, chờ cấp 2
            tc_list = dg.tieu_chi_chungs
        
        items.append(DanhSachChoPheDuyetItem(
            danh_gia_thang_id=dg.id, cong_chuc_id=dg.cong_chuc.id,
            ma_cc=dg.cong_chuc.ma_cc, ho_ten=dg.cong_chuc.ho_ten,
            don_vi_ten=dg.cong_chuc.don_vi.ten_don_vi if dg.cong_chuc.don_vi else None,
            thang=dg.thang, nam=dg.nam,
            diem_tu_cham=sum(float(tc.diem_tu_cham) for tc in tc_list),
            trang_thai=TrangThaiTieuChiEnum.CHO_PHE_DUYET,
            ngay_gui=tc_list[0].ngay_gui if tc_list and tc_list[0].ngay_gui else datetime.now(),
            nguoi_phe_duyet_tc_cap1_id=dg.nguoi_phe_duyet_tc_cap1_id,
            ngay_phe_duyet_tc_cap1=dg.ngay_phe_duyet_tc_cap1,
            # v3.6 (12/05/2026): FE dùng cap_bac này để phân biệt 2-cấp vs duyệt thẳng
            nguoi_phe_duyet_tc_cap1_cap_bac=(
                dg.nguoi_phe_duyet_tc_cap1.vai_tro.cap_bac.value
                if dg.nguoi_phe_duyet_tc_cap1
                and dg.nguoi_phe_duyet_tc_cap1.vai_tro
                and dg.nguoi_phe_duyet_tc_cap1.vai_tro.cap_bac
                else None
            ),
            nguoi_phe_duyet_tc_cap2_id=dg.nguoi_phe_duyet_tc_cap2_id,
            ngay_phe_duyet_tc_cap2=dg.ngay_phe_duyet_tc_cap2,
            trang_thai_tieu_chi=dg.trang_thai_tc.value if dg.trang_thai_tc else None,
            # v3.5: Thêm fields mới - ✅ FIX: is not None thay vì truthiness
            diem_tc_cap1=float(dg.diem_tc_cap1) if dg.diem_tc_cap1 is not None else None,
            diem_tc_cap2=float(dg.diem_tc_cap2) if dg.diem_tc_cap2 is not None else None,
            diem_tieu_chi_chung=float(dg.diem_tieu_chi_chung) if dg.diem_tieu_chi_chung is not None else None,
            ly_do_tu_choi_tc=dg.ly_do_tu_choi_tc,
            cap_phe_duyet_hien_tai="cap2" if dg.trang_thai_tc == TrangThaiTieuChi.CHO_CAP2 else "cap1",
            # v3.7 (02/06/2026): cờ cho FE — gồm cả LĐ ĐV hiện tại (xử lý chuyển ĐV)
            co_the_duyet=_co_the_duyet_tc(dg, current_user),
        ))
    
    return success_response(
        data=DanhSachChoPheDuyetResponse(
            tong_so=total, danh_sach=items, page=page,
            page_size=page_size, total_pages=(total + page_size - 1) // page_size
        ),
        message="Lấy danh sách chờ phê duyệt thành công"
    )

@router.get(
    "/tieu-chi/lich-su",
    summary="Lấy lịch sử phê duyệt tiêu chí chung",
)
async def get_lich_su_tieu_chi(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    trang_thai: Optional[str] = Query(default=None),
    thang: Optional[int] = Query(default=None, ge=1, le=12),
    nam: Optional[int] = Query(default=None, ge=2025),
) -> dict:
    cap_bac = current_user.vai_tro.cap_bac if current_user.vai_tro else None
    
    stmt = (
        select(DanhGiaThang)
        .options(
            selectinload(DanhGiaThang.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(TieuChiChungDanhGia.tieu_chi),
        )
        .where(DanhGiaThang.is_deleted == False)
    )
    
    # Filter trạng thái
    # Filter trạng thái - v3.5: Thêm TU_CHOI
    if trang_thai == "DA_PHE_DUYET":
        stmt = stmt.where(DanhGiaThang.trang_thai_tc == TrangThaiTieuChi.DA_PHE_DUYET)
    elif trang_thai == "TU_CHOI":
        # v3.5: Lọc đơn đã bị từ chối (có ly_do_tu_choi_tc)
        stmt = stmt.where(DanhGiaThang.ly_do_tu_choi_tc != None)
    else:
        # Lấy tất cả đã phê duyệt
        stmt = stmt.where(DanhGiaThang.trang_thai_tc == TrangThaiTieuChi.DA_PHE_DUYET)
        
    # Phân quyền
    is_cct = cap_bac == CapBacVaiTro.CHI_CUC_TRUONG
    is_qldv_user = is_qldv(current_user)

    if not is_cct:
        if is_qldv_user:
            # QLDV xem lịch sử của đơn vị - dùng snapshot để lấy đúng đơn vị lúc đánh giá
            stmt = stmt.where(DanhGiaThang.don_vi_id_snapshot == current_user.don_vi_id)
        else:
            # Lãnh đạo khác xem đơn mình đã duyệt
            stmt = stmt.where(
                or_(
                    DanhGiaThang.nguoi_phe_duyet_tc_cap1_id == current_user.id,
                    DanhGiaThang.nguoi_phe_duyet_tc_cap2_id == current_user.id,
                )
            )
    
    if thang:
        stmt = stmt.where(DanhGiaThang.thang == thang)
    if nam:
        stmt = stmt.where(DanhGiaThang.nam == nam)
    
    # Count & Pagination
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    stmt = stmt.order_by(DanhGiaThang.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(stmt)
    danh_gia_list = result.scalars().all()
    
    data = []
    for dg in danh_gia_list:
        item = build_danh_gia_thang_response(dg)
        item["cong_chuc"] = {
            "id": dg.cong_chuc.id,
            "ma_cc": dg.cong_chuc.ma_cc,
            "ho_ten": dg.cong_chuc.ho_ten,
            "don_vi_ten": dg.cong_chuc.don_vi.ten_don_vi if dg.cong_chuc.don_vi else None,
        } if dg.cong_chuc else None
        # v3.5: Thêm thông tin từ chối
        item["ly_do_tu_choi_tc"] = dg.ly_do_tu_choi_tc
        item["ngay_tu_choi_tc"] = dg.ngay_tu_choi_tc.isoformat() if getattr(dg, 'ngay_tu_choi_tc', None) else None
        # v3.6 (12/05/2026): trả về điểm CC tự chấm gốc để FE không fallback nhầm sang
        # diem_tieu_chi_chung (vốn là điểm sau LĐ chỉnh) khi hiển thị cột "CC tự chấm".
        item["diem_tu_cham"] = float(sum((tc.diem_tu_cham or 0) for tc in dg.tieu_chi_chungs))
        data.append(item)
    
    return success_response(
        data={
            "items": data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": (total + page_size - 1) // page_size,
            }
        },
        message=f"Lịch sử {total} đánh giá tiêu chí"
    )

@router.get("/tieu-chi/{danh_gia_thang_id}/chi-tiet")
async def get_chi_tiet_phe_duyet(
    db: DatabaseDep, current_user: ActiveUserDep, danh_gia_thang_id: UUID
) -> dict:
    """Xem chi tiết để phê duyệt."""
    stmt = select(DanhGiaThang).options(
        selectinload(DanhGiaThang.cong_chuc).selectinload(CongChuc.don_vi),
        selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(TieuChiChungDanhGia.tieu_chi),
        selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap1).selectinload(CongChuc.vai_tro),
        selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap2).selectinload(CongChuc.vai_tro),
    ).where(DanhGiaThang.id == danh_gia_thang_id, DanhGiaThang.is_deleted == False)
    
    danh_gia = (await db.execute(stmt)).scalar_one_or_none()
    if not danh_gia:
        raise HTTPException(status_code=404, detail=error_response(code="NOT_FOUND", message="Không tìm thấy"))
    
    # Kiểm tra quyền
    is_approver_cap1 = danh_gia.nguoi_phe_duyet_tc_cap1_id == current_user.id
    is_approver_cap2 = danh_gia.nguoi_phe_duyet_tc_cap2_id == current_user.id
    is_approver_legacy = any(tc.nguoi_phe_duyet_id == current_user.id for tc in danh_gia.tieu_chi_chungs)
    is_cct = current_user.vai_tro and current_user.vai_tro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG
    # v3.7 (02/06/2026): LĐ ĐV hiện tại của CC được xem khi đơn MỒ CÔI do chuyển đơn vị
    # (dùng chung điều kiện với danh sách chờ duyệt — tránh "nhảy" sai người duyệt).
    is_leader_orphan = _co_the_duyet_tc(danh_gia, current_user)

    if not (is_approver_cap1 or is_approver_cap2 or is_approver_legacy or is_cct or is_leader_orphan):
        raise HTTPException(status_code=403, detail=error_response(code="PERM_002", message="Không có quyền"))
    
    tc_list = [build_tieu_chi_response(tc, danh_gia.id) for tc in danh_gia.tieu_chi_chungs]
    tong_hop = await tinh_tong_diem_tieu_chi_chung(danh_gia.tieu_chi_chungs, use_ld=False)
    first_tc = danh_gia.tieu_chi_chungs[0] if danh_gia.tieu_chi_chungs else None
    
    # v2.6: Thêm thông tin phê duyệt 2 cấp
    extra_data = build_danh_gia_thang_response(danh_gia)
    
    return success_response(
        data={
            **ChiTietPheDuyetResponse(
                danh_gia_thang_id=danh_gia.id,
                cong_chuc={
                    "id": danh_gia.cong_chuc.id, "ma_cc": danh_gia.cong_chuc.ma_cc,
                    "ho_ten": danh_gia.cong_chuc.ho_ten, "chuc_vu": danh_gia.cong_chuc.chuc_vu,
                    "don_vi_ten": danh_gia.cong_chuc.don_vi.ten_don_vi if danh_gia.cong_chuc.don_vi else None,
                },
                thang=danh_gia.thang, nam=danh_gia.nam,
                tong_hop_cc=tong_hop, tieu_chi=tc_list,
                ngay_gui=first_tc.ngay_gui if first_tc else datetime.now(),
                trang_thai=TrangThaiTieuChiEnum(first_tc.trang_thai.value) if first_tc else TrangThaiTieuChiEnum.NHAP,
            ).model_dump(),
            **extra_data,
        },
        message="Lấy chi tiết thành công"
    )


@router.post("/{danh_gia_thang_id}/phe-duyet-tieu-chi")
async def phe_duyet_tieu_chi_chung(
    db: DatabaseDep, current_user: ActiveUserDep,
    danh_gia_thang_id: UUID, payload: PheDuyetTieuChiRequest
) -> dict:
    """
    LĐ phê duyệt tiêu chí chung của CC.
    v2.6: Phê duyệt 2 cấp - Phó ĐT (cấp 1) → ĐT (cấp 2)
    v3.6: Block QLDV - chỉ xem, KHÔNG duyệt
    """
    # Block QLDV
    if is_qldv(current_user):
        raise HTTPException(
            status_code=403,
            detail=error_response(code="PERM_002", message="QLDV không có quyền phê duyệt đánh giá")
        )

    stmt = select(DanhGiaThang).options(
        selectinload(DanhGiaThang.cong_chuc).selectinload(CongChuc.don_vi),
        selectinload(DanhGiaThang.cong_chuc).selectinload(CongChuc.vai_tro),
        selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(TieuChiChungDanhGia.tieu_chi),
        selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap1).selectinload(CongChuc.vai_tro),
        selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap2).selectinload(CongChuc.vai_tro),
    ).where(DanhGiaThang.id == danh_gia_thang_id, DanhGiaThang.is_deleted == False)
    
    danh_gia = (await db.execute(stmt)).scalar_one_or_none()
    if not danh_gia:
        raise HTTPException(status_code=404, detail=error_response(code="NOT_FOUND", message="Không tìm thấy"))
    
    # Kiểm tra khóa dữ liệu (bypass trong window nới tạm thời)
    if _dang_bi_khoa(danh_gia):
        raise HTTPException(status_code=400, detail=error_response(code="BIZ_002", message="Dữ liệu đã bị khóa"))
    
    # Lấy cấp bậc người đăng ký và current_user
    cap_bac_nguoi_dk = None
    if danh_gia.cong_chuc and danh_gia.cong_chuc.vai_tro:
        cap_bac_nguoi_dk = danh_gia.cong_chuc.vai_tro.cap_bac
    
    cap_bac_current = None
    if current_user.vai_tro:
        cap_bac_current = current_user.vai_tro.cap_bac
    
    now = datetime.now()
    
    # Map điều chỉnh
    dieu_chinh_map = {dc.ma_tieu_chi: dc for dc in (payload.dieu_chinh or [])}
    
    # ==========================================================================
    # TRƯỜNG HỢP 1: CCT tự phê duyệt
    # ==========================================================================
    if (danh_gia.cong_chuc_id == current_user.id and 
        cap_bac_current == CapBacVaiTro.CHI_CUC_TRUONG):
        
        for tc in danh_gia.tieu_chi_chungs:
            ma_tc = tc.tieu_chi.ma_tieu_chi
            _apply_dieu_chinh_ld(tc, dieu_chinh_map.get(ma_tc))
            tc.trang_thai = TrangThaiTieuChi.DA_PHE_DUYET
            tc.ngay_phe_duyet = now
            tc.ghi_chu_ld = payload.ghi_chu
        
        tong_hop = await tinh_tong_diem_tieu_chi_chung(danh_gia.tieu_chi_chungs, use_ld=True)
        danh_gia.diem_tieu_chi_chung = Decimal(str(tong_hop.tong_diem))
        danh_gia.trang_thai_tc = TrangThaiTieuChi.DA_PHE_DUYET
        await db.flush()
        
        return success_response(
            data=PheDuyetTieuChiResponse(
                success=True, message="CCT đã tự phê duyệt tiêu chí",
                danh_gia_thang_id=danh_gia.id, diem_tieu_chi_chung=float(danh_gia.diem_tieu_chi_chung),
                so_dieu_chinh=len(dieu_chinh_map), ngay_phe_duyet=now,
            ),
            message="CCT tự phê duyệt tiêu chí thành công"
        )
    
    # ==========================================================================
    # TRƯỜNG HỢP 2: ĐT/Phó CCT → CCT duyệt (1 cấp)
    # ==========================================================================
    if cap_bac_nguoi_dk in [CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_CHI_CUC_TRUONG]:
        if cap_bac_current != CapBacVaiTro.CHI_CUC_TRUONG:
            raise HTTPException(status_code=403, detail=error_response(code="PERM_002", message="Chỉ CCT mới được duyệt"))
        
        for tc in danh_gia.tieu_chi_chungs:
            ma_tc = tc.tieu_chi.ma_tieu_chi
            _apply_dieu_chinh_ld(tc, dieu_chinh_map.get(ma_tc))
            tc.trang_thai = TrangThaiTieuChi.DA_PHE_DUYET
            tc.ngay_phe_duyet = now
            tc.ghi_chu_ld = payload.ghi_chu
        
        tong_hop = await tinh_tong_diem_tieu_chi_chung(danh_gia.tieu_chi_chungs, use_ld=True)
        danh_gia.diem_tieu_chi_chung = Decimal(str(tong_hop.tong_diem))
        danh_gia.trang_thai_tc = TrangThaiTieuChi.DA_PHE_DUYET
        danh_gia.nguoi_phe_duyet_tc_cap2_id = current_user.id
        danh_gia.ngay_phe_duyet_tc_cap2 = now
        danh_gia.diem_tc_cap2 = danh_gia.diem_tieu_chi_chung
        await db.flush()
        
        return success_response(
            data=PheDuyetTieuChiResponse(
                success=True, message="CCT đã phê duyệt tiêu chí của ĐT/Phó CCT",
                danh_gia_thang_id=danh_gia.id, diem_tieu_chi_chung=float(danh_gia.diem_tieu_chi_chung),
                so_dieu_chinh=len(dieu_chinh_map), ngay_phe_duyet=now,
            ),
            message="Phê duyệt tiêu chí thành công"
        )
    
    # ==========================================================================
    # TRƯỜNG HỢP 3: Phó ĐT → ĐT duyệt (1 cấp)
    # ==========================================================================
    if cap_bac_nguoi_dk == CapBacVaiTro.PHO_DON_VI:
        if cap_bac_current != CapBacVaiTro.TRUONG_DON_VI:
            raise HTTPException(status_code=403, detail=error_response(code="PERM_002", message="Chỉ ĐT mới được duyệt"))
        
        for tc in danh_gia.tieu_chi_chungs:
            ma_tc = tc.tieu_chi.ma_tieu_chi
            _apply_dieu_chinh_ld(tc, dieu_chinh_map.get(ma_tc))
            tc.trang_thai = TrangThaiTieuChi.DA_PHE_DUYET
            tc.ngay_phe_duyet = now
            tc.ghi_chu_ld = payload.ghi_chu
        
        tong_hop = await tinh_tong_diem_tieu_chi_chung(danh_gia.tieu_chi_chungs, use_ld=True)
        danh_gia.diem_tieu_chi_chung = Decimal(str(tong_hop.tong_diem))
        danh_gia.trang_thai_tc = TrangThaiTieuChi.DA_PHE_DUYET
        danh_gia.nguoi_phe_duyet_tc_cap2_id = current_user.id
        danh_gia.ngay_phe_duyet_tc_cap2 = now
        danh_gia.diem_tc_cap2 = danh_gia.diem_tieu_chi_chung
        await db.flush()
        
        return success_response(
            data=PheDuyetTieuChiResponse(
                success=True, message="ĐT đã phê duyệt tiêu chí của Phó ĐT",
                danh_gia_thang_id=danh_gia.id, diem_tieu_chi_chung=float(danh_gia.diem_tieu_chi_chung),
                so_dieu_chinh=len(dieu_chinh_map), ngay_phe_duyet=now,
            ),
            message="Phê duyệt tiêu chí thành công"
        )
    
    # ==========================================================================
    # TRƯỜNG HỢP 4: CC thường → Phó ĐT (cấp 1) → ĐT (cấp 2)
    # ==========================================================================
    
    # --- CẤP 1: Phó ĐT phê duyệt ---
    is_cc_thuong = cap_bac_nguoi_dk in [CapBacVaiTro.CONG_CHUC, None] or cap_bac_nguoi_dk not in [
        CapBacVaiTro.CHI_CUC_TRUONG, 
        CapBacVaiTro.PHO_CHI_CUC_TRUONG,
        CapBacVaiTro.TRUONG_DON_VI,
        CapBacVaiTro.PHO_DON_VI
    ]
    is_pho_dt = cap_bac_current == CapBacVaiTro.PHO_DON_VI
    is_dt = cap_bac_current == CapBacVaiTro.TRUONG_DON_VI
    
    # Kiểm tra cùng đơn vị
    same_don_vi = False
    if danh_gia.cong_chuc and danh_gia.cong_chuc.don_vi_id:
        same_don_vi = current_user.don_vi_id == danh_gia.cong_chuc.don_vi_id
    
    # --- CẤP 1: Phó ĐT phê duyệt CC thường ---
    if is_cc_thuong and is_pho_dt and same_don_vi and not danh_gia.ngay_phe_duyet_tc_cap1:
        # Phó ĐT duyệt cấp 1
        so_dieu_chinh = 0
        for tc in danh_gia.tieu_chi_chungs:
            ma_tc = tc.tieu_chi.ma_tieu_chi
            dc = dieu_chinh_map.get(ma_tc)
            _apply_dieu_chinh_ld(tc, dc)
            if dc is not None:
                so_dieu_chinh += 1
            tc.ghi_chu_ld = payload.ghi_chu
            # v3.6 (12/05/2026): snapshot điểm PDV chấm per-TC qua prefix
            # [PDV:N] trong ly_do_dieu_chinh — tránh migration thêm cột.
            pdv_diem = float(tc.diem_phe_duyet) if tc.diem_phe_duyet is not None else 0.0
            _save_pdv_snapshot(tc, pdv_diem)
        
        tong_hop = await tinh_tong_diem_tieu_chi_chung(danh_gia.tieu_chi_chungs, use_ld=True)
        
        # ⭐ LƯU NGƯỜI PHÊ DUYỆT CẤP 1
        danh_gia.nguoi_phe_duyet_tc_cap1_id = current_user.id
        danh_gia.ngay_phe_duyet_tc_cap1 = now
        danh_gia.diem_tc_cap1 = Decimal(str(tong_hop.tong_diem))
        danh_gia.trang_thai_tc = TrangThaiTieuChi.CHO_CAP2  # v3.5: Phân biệt cấp 1 đã duyệt
        
        # Tìm ĐT của đơn vị để gán cấp 2
        don_vi_id = danh_gia.cong_chuc.don_vi_id if danh_gia.cong_chuc else None
        if don_vi_id:
            stmt_dt = (
                select(CongChuc)
                .join(VaiTro)
                .where(CongChuc.don_vi_id == don_vi_id)
                .where(VaiTro.cap_bac == CapBacVaiTro.TRUONG_DON_VI)
                .where(CongChuc.is_active == True)
                .limit(1)
            )
            result_dt = await db.execute(stmt_dt)
            doi_truong = result_dt.scalar_one_or_none()
            
            if doi_truong:
                danh_gia.nguoi_phe_duyet_tc_cap2_id = doi_truong.id
        
        await db.flush()
        
        return success_response(
            data=PheDuyetTieuChiResponse(
                success=True, 
                message=f"Phó ĐT đã phê duyệt cấp 1 ({so_dieu_chinh} điều chỉnh). Chờ ĐT duyệt cấp 2.",
                danh_gia_thang_id=danh_gia.id, 
                diem_tieu_chi_chung=float(tong_hop.tong_diem),
                so_dieu_chinh=so_dieu_chinh, 
                ngay_phe_duyet=now,
            ),
            message="Phê duyệt cấp 1 thành công. Chờ Đội trưởng phê duyệt cấp 2."
        )
    
    # --- CẤP 2: ĐT phê duyệt (sau khi Phó ĐT đã duyệt cấp 1) ---
    if is_cc_thuong and is_dt and same_don_vi and danh_gia.ngay_phe_duyet_tc_cap1 and not danh_gia.ngay_phe_duyet_tc_cap2:
        # ĐT duyệt cấp 2 (có thể điều chỉnh thêm)
        so_dieu_chinh = 0
        for tc in danh_gia.tieu_chi_chungs:
            ma_tc = tc.tieu_chi.ma_tieu_chi
            dc = dieu_chinh_map.get(ma_tc)
            if dc is None:
                # ĐT đồng ý quyết định Phó ĐT → giữ is_achieved_ld, recompute điểm
                _apply_dieu_chinh_ld(tc, None, fallback="keep")
            else:
                # ĐT điều chỉnh — nối lý do với phần Phó ĐT đã có (prefix "ĐT:")
                if dc.ly_do_dieu_chinh:
                    tc.ly_do_dieu_chinh = (tc.ly_do_dieu_chinh or "") + f" | ĐT: {dc.ly_do_dieu_chinh}"
                    dc_no_ly_do = dc.model_copy(update={"ly_do_dieu_chinh": None})
                    _apply_dieu_chinh_ld(tc, dc_no_ly_do, fallback="keep")
                else:
                    _apply_dieu_chinh_ld(tc, dc, fallback="keep")
                so_dieu_chinh += 1
            tc.trang_thai = TrangThaiTieuChi.DA_PHE_DUYET
            tc.ngay_phe_duyet = now
        
        tong_hop = await tinh_tong_diem_tieu_chi_chung(danh_gia.tieu_chi_chungs, use_ld=True)
        
        danh_gia.diem_tieu_chi_chung = Decimal(str(tong_hop.tong_diem))
        danh_gia.trang_thai_tc = TrangThaiTieuChi.DA_PHE_DUYET
        # ⭐ LƯU NGƯỜI PHÊ DUYỆT CẤP 2
        danh_gia.nguoi_phe_duyet_tc_cap2_id = current_user.id
        danh_gia.ngay_phe_duyet_tc_cap2 = now
        danh_gia.diem_tc_cap2 = danh_gia.diem_tieu_chi_chung
        
        await db.flush()
        
        return success_response(
            data=PheDuyetTieuChiResponse(
                success=True, 
                message=f"ĐT đã phê duyệt cấp 2 ({so_dieu_chinh} điều chỉnh). Hoàn tất.",
                danh_gia_thang_id=danh_gia.id, 
                diem_tieu_chi_chung=float(danh_gia.diem_tieu_chi_chung),
                so_dieu_chinh=so_dieu_chinh, 
                ngay_phe_duyet=now,
            ),
            message="Phê duyệt tiêu chí hoàn tất"
        )
    
    # --- ĐẶC BIỆT: ĐT duyệt trực tiếp CC thường (bỏ qua cấp 1) ---
    if is_cc_thuong and is_dt and same_don_vi and not danh_gia.ngay_phe_duyet_tc_cap2:
        # ĐT có thể duyệt trực tiếp không cần qua Phó ĐT
        so_dieu_chinh = 0
        for tc in danh_gia.tieu_chi_chungs:
            ma_tc = tc.tieu_chi.ma_tieu_chi
            dc = dieu_chinh_map.get(ma_tc)
            _apply_dieu_chinh_ld(tc, dc)
            if dc is not None:
                so_dieu_chinh += 1
            tc.trang_thai = TrangThaiTieuChi.DA_PHE_DUYET
            tc.ngay_phe_duyet = now
            tc.ghi_chu_ld = payload.ghi_chu
        
        tong_hop = await tinh_tong_diem_tieu_chi_chung(danh_gia.tieu_chi_chungs, use_ld=True)
        
        danh_gia.diem_tieu_chi_chung = Decimal(str(tong_hop.tong_diem))
        danh_gia.trang_thai_tc = TrangThaiTieuChi.DA_PHE_DUYET
        # ⭐ LƯU NGƯỜI PHÊ DUYỆT (ĐT duyệt trực tiếp = cả cấp 1 và cấp 2)
        if not danh_gia.nguoi_phe_duyet_tc_cap1_id:
            danh_gia.nguoi_phe_duyet_tc_cap1_id = current_user.id
            danh_gia.ngay_phe_duyet_tc_cap1 = now
            danh_gia.diem_tc_cap1 = Decimal(str(tong_hop.tong_diem))
        danh_gia.nguoi_phe_duyet_tc_cap2_id = current_user.id
        danh_gia.ngay_phe_duyet_tc_cap2 = now
        danh_gia.diem_tc_cap2 = danh_gia.diem_tieu_chi_chung
        
        await db.flush()
        
        return success_response(
            data=PheDuyetTieuChiResponse(
                success=True, 
                message=f"ĐT đã phê duyệt trực tiếp ({so_dieu_chinh} điều chỉnh). Hoàn tất.",
                danh_gia_thang_id=danh_gia.id, 
                diem_tieu_chi_chung=float(danh_gia.diem_tieu_chi_chung),
                so_dieu_chinh=so_dieu_chinh, 
                ngay_phe_duyet=now,
            ),
            message="Phê duyệt tiêu chí hoàn tất"
        )
    
    # ==========================================================================
    # FALLBACK: Logic cũ (TieuChiChungDanhGia.nguoi_phe_duyet_id)
    # ==========================================================================
    tc_cho_duyet = [tc for tc in danh_gia.tieu_chi_chungs if tc.trang_thai == TrangThaiTieuChi.CHO_PHE_DUYET]
    if not tc_cho_duyet:
        raise HTTPException(status_code=400, detail=error_response(code="BIZ_001", message="Không có tiêu chí chờ duyệt"))
    
    is_approver = any(tc.nguoi_phe_duyet_id == current_user.id for tc in tc_cho_duyet)
    is_cct = current_user.vai_tro and current_user.vai_tro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG
    if not is_approver and not is_cct:
        raise HTTPException(status_code=403, detail=error_response(code="PERM_002", message="Không có quyền"))
    
    so_dieu_chinh = 0
    for tc in danh_gia.tieu_chi_chungs:
        ma_tc = tc.tieu_chi.ma_tieu_chi
        dc = dieu_chinh_map.get(ma_tc)
        _apply_dieu_chinh_ld(tc, dc)
        if dc is not None:
            so_dieu_chinh += 1
        tc.trang_thai = TrangThaiTieuChi.DA_PHE_DUYET
        tc.ngay_phe_duyet = now
        tc.ghi_chu_ld = payload.ghi_chu
    
    tong_hop = await tinh_tong_diem_tieu_chi_chung(danh_gia.tieu_chi_chungs, use_ld=True)
    danh_gia.diem_tieu_chi_chung = Decimal(str(tong_hop.tong_diem))
    danh_gia.trang_thai_tc = TrangThaiTieuChi.DA_PHE_DUYET
    await db.flush()
    
    return success_response(
        data=PheDuyetTieuChiResponse(
            success=True, message=f"Phê duyệt thành công ({so_dieu_chinh} điều chỉnh)",
            danh_gia_thang_id=danh_gia.id, diem_tieu_chi_chung=float(danh_gia.diem_tieu_chi_chung),
            so_dieu_chinh=so_dieu_chinh, ngay_phe_duyet=now,
        ),
        message="Phê duyệt tiêu chí chung thành công"
    )


# =============================================================================
# v3.5: TỪ CHỐI TIÊU CHÍ CHUNG
# =============================================================================

@router.post("/{danh_gia_thang_id}/tu-choi-tieu-chi")
async def tu_choi_tieu_chi_chung(
    db: DatabaseDep, current_user: ActiveUserDep,
    danh_gia_thang_id: UUID, payload: TuChoiTieuChiRequest
) -> dict:
    """
    Từ chối tiêu chí chung - Trả đơn về cho CC kê khai lại.

    v3.5.0: Endpoint mới - trước đó backend thiếu → gây lỗi "Chờ ĐT phê duyệt".
    v3.6: Block QLDV - chỉ xem, KHÔNG từ chối

    Logic:
    - Phó ĐT/ĐT/CCT từ chối → reset toàn bộ tiêu chí về NHAP
    - CC thấy trạng thái NHAP → sửa → gửi lại
    - Lưu lý do từ chối để CC biết cần sửa gì
    """
    # Block QLDV
    if is_qldv(current_user):
        raise HTTPException(
            status_code=403,
            detail=error_response(code="PERM_002", message="QLDV không có quyền phê duyệt đánh giá")
        )

    stmt = select(DanhGiaThang).options(
        selectinload(DanhGiaThang.cong_chuc).selectinload(CongChuc.don_vi),
        selectinload(DanhGiaThang.cong_chuc).selectinload(CongChuc.vai_tro),
        selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(TieuChiChungDanhGia.tieu_chi),
    ).where(DanhGiaThang.id == danh_gia_thang_id, DanhGiaThang.is_deleted == False)
    
    danh_gia = (await db.execute(stmt)).scalar_one_or_none()
    if not danh_gia:
        raise HTTPException(
            status_code=404,
            detail=error_response(code="NOT_FOUND", message="Không tìm thấy đánh giá")
        )
    
    # Kiểm tra khóa dữ liệu (bypass trong window nới tạm thời)
    if _dang_bi_khoa(danh_gia):
        raise HTTPException(
            status_code=400,
            detail=error_response(code="BIZ_002", message="Dữ liệu đã bị khóa, không thể từ chối")
        )
    
    # Kiểm tra trạng thái: chỉ từ chối khi đang chờ phê duyệt
    allowed_states = [TrangThaiTieuChi.CHO_PHE_DUYET, TrangThaiTieuChi.CHO_CAP2]
    if danh_gia.trang_thai_tc not in allowed_states:
        raise HTTPException(
            status_code=400,
            detail=error_response(
                code="BIZ_001",
                message=f"Không thể từ chối ở trạng thái "
                        f"'{danh_gia.trang_thai_tc.value if danh_gia.trang_thai_tc else 'N/A'}'. "
                        f"Chỉ từ chối được khi đang CHO_PHE_DUYET hoặc CHO_CAP2."
            )
        )
    
    # Kiểm tra quyền từ chối
    cap_bac_current = None
    if current_user.vai_tro:
        cap_bac_current = current_user.vai_tro.cap_bac
    
    same_don_vi = False
    if danh_gia.cong_chuc and danh_gia.cong_chuc.don_vi_id:
        same_don_vi = current_user.don_vi_id == danh_gia.cong_chuc.don_vi_id
    
    can_reject = (
        # Người được gán phê duyệt cấp 1
        (danh_gia.nguoi_phe_duyet_tc_cap1_id and 
         danh_gia.nguoi_phe_duyet_tc_cap1_id == current_user.id) or
        # Người được gán phê duyệt cấp 2
        (danh_gia.nguoi_phe_duyet_tc_cap2_id and 
         danh_gia.nguoi_phe_duyet_tc_cap2_id == current_user.id) or
        # Fallback: legacy nguoi_phe_duyet_id trên tiêu chí
        any(tc.nguoi_phe_duyet_id == current_user.id for tc in danh_gia.tieu_chi_chungs) or
        # CCT luôn có quyền
        cap_bac_current == CapBacVaiTro.CHI_CUC_TRUONG or
        # Phó ĐT/ĐT cùng đơn vị
        (cap_bac_current == CapBacVaiTro.PHO_DON_VI and same_don_vi) or
        (cap_bac_current == CapBacVaiTro.TRUONG_DON_VI and same_don_vi)
    )
    
    if not can_reject:
        raise HTTPException(
            status_code=403,
            detail=error_response(code="PERM_002", message="Bạn không có quyền từ chối đơn này")
        )
    
    now = datetime.now()
    
    # =========================================================================
    # RESET TOÀN BỘ VỀ NHẬP
    # =========================================================================
    
    # Reset từng tiêu chí
    for tc in danh_gia.tieu_chi_chungs:
        tc.trang_thai = TrangThaiTieuChi.NHAP
        tc.is_achieved_ld = None          # Xóa kết quả LĐ duyệt
        tc.diem_phe_duyet = None          # Xóa điểm phê duyệt
        tc.ly_do_dieu_chinh = None        # Xóa lý do điều chỉnh
        tc.ngay_phe_duyet = None
        tc.ghi_chu_ld = None
    
    # Reset trạng thái đánh giá tháng
    danh_gia.trang_thai_tc = TrangThaiTieuChi.NHAP
    
    # Reset phê duyệt cấp 1
    danh_gia.nguoi_phe_duyet_tc_cap1_id = None
    danh_gia.ngay_phe_duyet_tc_cap1 = None
    danh_gia.diem_tc_cap1 = None
    
    # Reset phê duyệt cấp 2
    danh_gia.nguoi_phe_duyet_tc_cap2_id = None
    danh_gia.ngay_phe_duyet_tc_cap2 = None
    danh_gia.diem_tc_cap2 = None
    
    # Reset điểm tổng
    danh_gia.diem_tieu_chi_chung = None
    
    # Lưu thông tin từ chối
    danh_gia.ly_do_tu_choi_tc = payload.ly_do_tu_choi
    danh_gia.nguoi_tu_choi_tc_id = current_user.id
    danh_gia.ngay_tu_choi_tc = now
    
    await db.flush()

    # Label người từ chối
    cap_labels = {
        CapBacVaiTro.PHO_DON_VI: "Phó ĐT",
        CapBacVaiTro.TRUONG_DON_VI: "Đội trưởng",
        CapBacVaiTro.CHI_CUC_TRUONG: "Chi cục trưởng",
    }
    cap_label = cap_labels.get(cap_bac_current, "Lãnh đạo")
    ho_ten_cc = danh_gia.cong_chuc.ho_ten if danh_gia.cong_chuc else "N/A"

    if danh_gia.cong_chuc_id:
        await gui_thong_bao(
            nguoi_nhan_id=danh_gia.cong_chuc_id,
            tieu_de="Tiêu chí chung bị từ chối",
            noi_dung=f"Lý do: {payload.ly_do_tu_choi}",
            link_url="/danh-gia/tu-cham-diem",
            doi_tuong_type="DANH_GIA_THANG",
            doi_tuong_id=danh_gia.id,
        )

    return success_response(
        data={
            "danh_gia_thang_id": str(danh_gia.id),
            "trang_thai_moi": "NHAP",
            "ly_do_tu_choi": payload.ly_do_tu_choi,
            "nguoi_tu_choi": current_user.ho_ten,
            "cap_bac": cap_label,
            "ngay_tu_choi": now.isoformat(),
        },
        message=f"{cap_label} đã từ chối tiêu chí của {ho_ten_cc}. "
                f"Đơn đã trả về để CC kê khai lại."
    )


# =============================================================================
# v3.6: TRẢ LẠI TIÊU CHÍ ĐÃ DUYỆT
# =============================================================================

from pydantic import BaseModel as _BaseModel, Field as _Field


class TraLaiTieuChiRequest(_BaseModel):
    """Schema request trả lại tiêu chí đã duyệt."""
    ly_do: str = _Field(..., min_length=1, max_length=500, description="Lý do trả lại")


@router.post("/{danh_gia_thang_id}/tra-lai-tieu-chi")
async def tra_lai_tieu_chi_da_duyet(
    db: DatabaseDep, current_user: ActiveUserDep,
    danh_gia_thang_id: UUID, payload: TraLaiTieuChiRequest
) -> dict:
    """
    Trả lại tiêu chí chung đã phê duyệt - v3.6.
    
    Dùng khi lãnh đạo phê duyệt nhầm, cần hoàn tác.
    Tiêu chí sẽ quay về trạng thái NHAP để CC chỉnh sửa và gửi lại.
    
    Quyền:
    - Người đã phê duyệt cấp 1 (nguoi_phe_duyet_tc_cap1)
    - Người đã phê duyệt cấp 2 (nguoi_phe_duyet_tc_cap2)
    - Chi cục trưởng (CCT)
    
    Reset logic:
    - Reset trang_thai_tc → NHAP
    - Reset phê duyệt cấp 1 + cấp 2
    - Reset điểm tiêu chí chung + từng tiêu chí con
    - Lưu lý do trả lại vào ly_do_tu_choi_tc với prefix [TRẢ LẠI]
    """
    stmt = select(DanhGiaThang).options(
        selectinload(DanhGiaThang.cong_chuc).selectinload(CongChuc.don_vi),
        selectinload(DanhGiaThang.cong_chuc).selectinload(CongChuc.vai_tro),
        selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(TieuChiChungDanhGia.tieu_chi),
        selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap1).selectinload(CongChuc.vai_tro),
        selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap2).selectinload(CongChuc.vai_tro),
    ).where(DanhGiaThang.id == danh_gia_thang_id, DanhGiaThang.is_deleted == False)
    
    danh_gia = (await db.execute(stmt)).scalar_one_or_none()
    if not danh_gia:
        raise HTTPException(
            status_code=404,
            detail=error_response(code="NOT_FOUND", message="Không tìm thấy đánh giá")
        )
    
    # Kiểm tra khóa dữ liệu (bypass trong window nới tạm thời)
    if _dang_bi_khoa(danh_gia):
        raise HTTPException(
            status_code=400,
            detail=error_response(code="BIZ_002", message="Dữ liệu đã bị khóa, không thể trả lại")
        )
    
    # Kiểm tra trạng thái - chỉ trả lại khi DA_PHE_DUYET
    if danh_gia.trang_thai_tc != TrangThaiTieuChi.DA_PHE_DUYET:
        raise HTTPException(
            status_code=400,
            detail=error_response(
                code="BIZ_001",
                message=f"Chỉ có thể trả lại tiêu chí đã phê duyệt. "
                        f"Trạng thái hiện tại: {danh_gia.trang_thai_tc.value if danh_gia.trang_thai_tc else 'N/A'}"
            )
        )
    
    # Kiểm tra quyền trả lại
    cap_bac_current = None
    if current_user.vai_tro:
        cap_bac_current = current_user.vai_tro.cap_bac
    
    can_tra_lai = False
    
    # Người đã phê duyệt cấp 1
    if (danh_gia.nguoi_phe_duyet_tc_cap1_id and 
        danh_gia.nguoi_phe_duyet_tc_cap1_id == current_user.id):
        can_tra_lai = True
    
    # Người đã phê duyệt cấp 2
    if (danh_gia.nguoi_phe_duyet_tc_cap2_id and 
        danh_gia.nguoi_phe_duyet_tc_cap2_id == current_user.id):
        can_tra_lai = True
    
    # CCT luôn có quyền
    if cap_bac_current == CapBacVaiTro.CHI_CUC_TRUONG:
        can_tra_lai = True
    
    if not can_tra_lai:
        raise HTTPException(
            status_code=403,
            detail=error_response(code="PERM_002", message="Bạn không có quyền trả lại đơn này")
        )
    
    now = datetime.now()
    
    # =========================================================================
    # RESET TOÀN BỘ VỀ NHẬP (giống tu-choi nhưng từ DA_PHE_DUYET)
    # =========================================================================
    
    # Reset từng tiêu chí con
    for tc in danh_gia.tieu_chi_chungs:
        tc.trang_thai = TrangThaiTieuChi.NHAP
        tc.is_achieved_ld = None
        tc.diem_phe_duyet = None
        tc.ly_do_dieu_chinh = None
        tc.ngay_phe_duyet = None
        tc.ghi_chu_ld = None
    
    # Reset trạng thái tổng
    danh_gia.trang_thai_tc = TrangThaiTieuChi.NHAP
    
    # Reset phê duyệt cấp 1
    danh_gia.nguoi_phe_duyet_tc_cap1_id = None
    danh_gia.ngay_phe_duyet_tc_cap1 = None
    danh_gia.diem_tc_cap1 = None
    
    # Reset phê duyệt cấp 2
    danh_gia.nguoi_phe_duyet_tc_cap2_id = None
    danh_gia.ngay_phe_duyet_tc_cap2 = None
    danh_gia.diem_tc_cap2 = None
    
    # Reset điểm tổng
    danh_gia.diem_tieu_chi_chung = None
    
    # Lưu thông tin trả lại (dùng chung fields từ chối, thêm prefix)
    danh_gia.ly_do_tu_choi_tc = f"[TRẢ LẠI] {payload.ly_do}"
    danh_gia.nguoi_tu_choi_tc_id = current_user.id
    danh_gia.ngay_tu_choi_tc = now
    
    await db.flush()
    
    # Label người trả lại
    cap_labels = {
        CapBacVaiTro.PHO_DON_VI: "Phó ĐT",
        CapBacVaiTro.TRUONG_DON_VI: "Đội trưởng",
        CapBacVaiTro.CHI_CUC_TRUONG: "Chi cục trưởng",
        CapBacVaiTro.PHO_CHI_CUC_TRUONG: "Phó Chi cục trưởng",
    }
    cap_label = cap_labels.get(cap_bac_current, "Lãnh đạo")
    ho_ten_cc = danh_gia.cong_chuc.ho_ten if danh_gia.cong_chuc else "N/A"

    if danh_gia.cong_chuc_id:
        await gui_thong_bao(
            nguoi_nhan_id=danh_gia.cong_chuc_id,
            tieu_de="Tiêu chí chung bị trả lại",
            noi_dung=f"Lý do: {payload.ly_do}",
            link_url="/danh-gia/tu-cham-diem",
            doi_tuong_type="DANH_GIA_THANG",
            doi_tuong_id=danh_gia.id,
        )

    return success_response(
        data={
            "danh_gia_thang_id": str(danh_gia.id),
            "trang_thai_moi": "NHAP",
            "ly_do_tra_lai": payload.ly_do,
            "nguoi_tra_lai": current_user.ho_ten,
            "cap_bac": cap_label,
            "ngay_tra_lai": now.isoformat(),
        },
        message=f"{cap_label} đã trả lại tiêu chí của {ho_ten_cc}. "
                f"Đơn đã chuyển về trạng thái Nháp để CC kê khai lại."
    )


@router.post("/phe-duyet-tieu-chi-bulk")
async def phe_duyet_tieu_chi_bulk(
    db: DatabaseDep, current_user: ActiveUserDep, payload: PheDuyetTieuChiBulkRequest
) -> dict:
    """
    Phê duyệt hàng loạt (không điều chỉnh).
    v3.6: Block QLDV - chỉ xem, KHÔNG duyệt
    """
    # Block QLDV
    if is_qldv(current_user):
        raise HTTPException(
            status_code=403,
            detail=error_response(code="PERM_002", message="QLDV không có quyền phê duyệt đánh giá")
        )

    if not current_user.is_lanh_dao:
        raise HTTPException(status_code=403, detail=error_response(code="PERM_002", message="Chỉ lãnh đạo"))
    
    cap_bac_current = None
    if current_user.vai_tro:
        cap_bac_current = current_user.vai_tro.cap_bac
    
    processed_ids = []
    now = datetime.now()
    
    for dgt_id in payload.danh_gia_thang_ids:
        stmt = select(DanhGiaThang).options(
            selectinload(DanhGiaThang.cong_chuc).selectinload(CongChuc.vai_tro),
            selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(TieuChiChungDanhGia.tieu_chi)
        ).where(DanhGiaThang.id == dgt_id, DanhGiaThang.is_deleted == False)
        
        danh_gia = (await db.execute(stmt)).scalar_one_or_none()
        if not danh_gia:
            continue
        
        # Kiểm tra khóa (bypass trong window nới tạm thời)
        if _dang_bi_khoa(danh_gia):
            continue
        
        # Kiểm tra quyền
        is_approver_cap1 = danh_gia.nguoi_phe_duyet_tc_cap1_id == current_user.id
        is_approver_cap2 = danh_gia.nguoi_phe_duyet_tc_cap2_id == current_user.id
        is_approver_legacy = any(tc.nguoi_phe_duyet_id == current_user.id for tc in danh_gia.tieu_chi_chungs if tc.trang_thai == TrangThaiTieuChi.CHO_PHE_DUYET)
        is_cct = cap_bac_current == CapBacVaiTro.CHI_CUC_TRUONG
        
        if not (is_approver_cap1 or is_approver_cap2 or is_approver_legacy or is_cct):
            continue

        # Cấp bậc người được đánh giá — cần để phân biệt duyệt thẳng
        cap_bac_cc = None
        if danh_gia.cong_chuc and danh_gia.cong_chuc.vai_tro:
            cap_bac_cc = danh_gia.cong_chuc.vai_tro.cap_bac

        # --- DUYỆT THẲNG 1 CẤP ---
        # Bản chất luồng 2 cấp: CHỈ phát sinh khi người duyệt CẤP 1 là Phó ĐT
        # (PHO_DON_VI) — đó là chuỗi CC thường → Phó ĐT (cấp 1) → ĐT (cấp 2).
        # Mọi trường hợp còn lại, khi current_user chính là người được giao
        # duyệt cấp 1 (is_approver_cap1) NHƯNG KHÔNG phải Phó ĐT, đều là DUYỆT
        # THẲNG 1 cấp. Bao gồm:
        #   (a) CCT tự đánh giá → CCT tự duyệt
        #   (b) ĐT/PCCT → CCT duyệt
        #   (c) ĐT duyệt thẳng CC thường (CC chọn "Đội trưởng - duyệt thẳng")
        #   (d) Phó ĐT gửi → ĐT duyệt (1 cấp, giống TRƯỜNG HỢP 3 endpoint single)
        #
        # BUG FIX (04/06/2026): trước đây nhánh `is_duyet_thang` chỉ nhận ra
        # (a)+(b). Các case (c)/(d) rơi xuống nhánh "Cấp 1" → set CHO_CAP2 và
        # gán cap2_id = ĐT cùng đơn vị = CHÍNH người vừa duyệt → kẹt deadlock
        # (cap1_id == cap2_id). Endpoint single đã xử lý đúng; bulk nay đồng bộ.
        is_cct_tu_danh_gia = (
            cap_bac_cc == CapBacVaiTro.CHI_CUC_TRUONG
            and danh_gia.cong_chuc_id == current_user.id
        )
        # Người được giao duyệt cấp 1 mà KHÔNG phải Phó ĐT → luôn duyệt thẳng.
        is_cap1_khong_phai_pho_dt = (
            is_approver_cap1
            and cap_bac_current != CapBacVaiTro.PHO_DON_VI
        )
        is_duyet_thang = (
            (is_cct_tu_danh_gia or is_cap1_khong_phai_pho_dt)
            and is_approver_cap1
            and not danh_gia.ngay_phe_duyet_tc_cap1
        )
        if is_duyet_thang:
            # v3.6 (15/05/2026 BUG FIX): KHÔNG dùng _diem_pd_tu_ld (binary) trực
            # tiếp — sẽ ăn điểm thập phân CC tự chấm. Dùng _apply_dieu_chinh_ld
            # với fallback="cc" để đồng ý CC chấm, giữ nguyên diem_tu_cham.
            for tc in danh_gia.tieu_chi_chungs:
                _apply_dieu_chinh_ld(tc, None, fallback="cc")
                tc.trang_thai = TrangThaiTieuChi.DA_PHE_DUYET
                tc.ngay_phe_duyet = now
                tc.ghi_chu_ld = payload.ghi_chu

            tong_hop = await tinh_tong_diem_tieu_chi_chung(danh_gia.tieu_chi_chungs, use_ld=True)
            diem = Decimal(str(tong_hop.tong_diem))
            danh_gia.ngay_phe_duyet_tc_cap1 = now
            danh_gia.diem_tc_cap1 = diem
            danh_gia.nguoi_phe_duyet_tc_cap2_id = current_user.id
            danh_gia.ngay_phe_duyet_tc_cap2 = now
            danh_gia.diem_tc_cap2 = diem
            danh_gia.diem_tieu_chi_chung = diem
            danh_gia.trang_thai_tc = TrangThaiTieuChi.DA_PHE_DUYET

            processed_ids.append(dgt_id)
            continue

        # Xử lý theo cấp
        # Cấp 1
        if is_approver_cap1 and not danh_gia.ngay_phe_duyet_tc_cap1:
            # v3.6 (15/05/2026 BUG FIX): đồng ý CC chấm → giữ diem_tu_cham qua
            # _apply_dieu_chinh_ld(fallback="cc"). Lưu snapshot [PDV:N] giống
            # single endpoint để FE hiển thị 3 cột CC/PDV/TDV.
            for tc in danh_gia.tieu_chi_chungs:
                _apply_dieu_chinh_ld(tc, None, fallback="cc")
                tc.ghi_chu_ld = payload.ghi_chu
                pdv_diem = float(tc.diem_phe_duyet) if tc.diem_phe_duyet is not None else 0.0
                _save_pdv_snapshot(tc, pdv_diem)

            tong_hop = await tinh_tong_diem_tieu_chi_chung(danh_gia.tieu_chi_chungs, use_ld=True)
            danh_gia.ngay_phe_duyet_tc_cap1 = now
            danh_gia.diem_tc_cap1 = Decimal(str(tong_hop.tong_diem))
            danh_gia.trang_thai_tc = TrangThaiTieuChi.CHO_CAP2  # v3.5: Phân biệt cấp

            # Tìm ĐT
            don_vi_id = danh_gia.cong_chuc.don_vi_id if danh_gia.cong_chuc else None
            if don_vi_id:
                stmt_dt = select(CongChuc).join(VaiTro).where(
                    CongChuc.don_vi_id == don_vi_id,
                    VaiTro.cap_bac == CapBacVaiTro.TRUONG_DON_VI,
                    CongChuc.is_active == True
                ).limit(1)
                result_dt = await db.execute(stmt_dt)
                dt = result_dt.scalar_one_or_none()
                if dt:
                    danh_gia.nguoi_phe_duyet_tc_cap2_id = dt.id

            processed_ids.append(dgt_id)
            continue

        # Cấp 2
        if is_approver_cap2 and danh_gia.ngay_phe_duyet_tc_cap1 and not danh_gia.ngay_phe_duyet_tc_cap2:
            # v3.6 (15/05/2026 BUG FIX — ăn điểm thập phân): TDV đồng ý quyết
            # định PDV → GIỮ NGUYÊN diem_phe_duyet đã có từ cấp 1. Trước đây
            # recompute qua _diem_pd_tu_ld (binary) khiến TC mà CC chấm thập
            # phân < max (is_achieved_ld=False, diem=2.0/2.5) bị overwrite về 0.
            for tc in danh_gia.tieu_chi_chungs:
                _apply_dieu_chinh_ld(tc, None, fallback="keep")
                tc.trang_thai = TrangThaiTieuChi.DA_PHE_DUYET
                tc.ngay_phe_duyet = now

            tong_hop = await tinh_tong_diem_tieu_chi_chung(danh_gia.tieu_chi_chungs, use_ld=True)
            danh_gia.diem_tieu_chi_chung = Decimal(str(tong_hop.tong_diem))
            danh_gia.trang_thai_tc = TrangThaiTieuChi.DA_PHE_DUYET
            danh_gia.ngay_phe_duyet_tc_cap2 = now
            danh_gia.diem_tc_cap2 = danh_gia.diem_tieu_chi_chung

            processed_ids.append(dgt_id)
            continue

        # Fallback legacy
        tc_cho_duyet = [tc for tc in danh_gia.tieu_chi_chungs if tc.trang_thai == TrangThaiTieuChi.CHO_PHE_DUYET]
        if not tc_cho_duyet:
            continue

        # v3.6 (15/05/2026 BUG FIX): đồng ý CC chấm → giữ diem_tu_cham.
        for tc in danh_gia.tieu_chi_chungs:
            _apply_dieu_chinh_ld(tc, None, fallback="cc")
            tc.trang_thai = TrangThaiTieuChi.DA_PHE_DUYET
            tc.ngay_phe_duyet = now
            tc.ghi_chu_ld = payload.ghi_chu
        
        tong_hop = await tinh_tong_diem_tieu_chi_chung(danh_gia.tieu_chi_chungs, use_ld=True)
        danh_gia.diem_tieu_chi_chung = Decimal(str(tong_hop.tong_diem))
        danh_gia.trang_thai_tc = TrangThaiTieuChi.DA_PHE_DUYET
        processed_ids.append(dgt_id)
    
    await db.flush()
    
    return success_response(
        data=PheDuyetBulkResponse(
            success=True, message=f"Đã phê duyệt {len(processed_ids)} bản",
            tong_phe_duyet=len(processed_ids), danh_sach_id=processed_ids,
        ),
        message=f"Phê duyệt hàng loạt thành công ({len(processed_ids)} bản)"
    )


# =============================================================================
# XEM TIÊU CHÍ CHUNG CỦA CÔNG CHỨC (Lãnh đạo/Admin)
# =============================================================================

@router.get("/tieu-chi/cong-chuc/{cong_chuc_id}/thang/{thang}/nam/{nam}")
async def get_tieu_chi_cong_chuc(
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Xem tiêu chí chung của một công chức cụ thể.
    
    **Mục đích:** Dùng trong modal "Chi tiết công chức" của Báo cáo xếp loại,
    cho phép Đội trưởng/CCT xem chi tiết tiêu chí chung của CC.
    
    **Quyền truy cập:**
    - Lãnh đạo đơn vị (TDV, PDV): Chỉ xem CC cùng đơn vị
    - Chi cục trưởng (CCT), Phó CCT: Xem tất cả CC
    - Admin: Xem tất cả CC
    
    **Response:** Giống GET /tieu-chi/thang/{thang}/nam/{nam} nhưng cho CC khác.
    Trả về danh sách tiêu chí (10 mục), tổng hợp nhóm (nhom_1, nhom_2, nhom_3),
    trạng thái phê duyệt.
    """
    if thang < 1 or thang > 12:
        raise HTTPException(status_code=400, detail=error_response(code="VAL_003", message="Tháng phải từ 1-12"))
    
    # =========================================================================
    # 1. Kiểm tra quyền
    # =========================================================================
    is_admin = getattr(current_user.vai_tro, 'is_system_admin', False) if current_user.vai_tro else False
    cap_bac = current_user.vai_tro.cap_bac if current_user.vai_tro else None
    
    is_cct_or_pcct = cap_bac in [CapBacVaiTro.CHI_CUC_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG]
    is_lanh_dao_don_vi = cap_bac in [CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI]
    
    if not (is_admin or is_cct_or_pcct or is_lanh_dao_don_vi):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                code="PERM_001",
                message="Chỉ Lãnh đạo hoặc Admin mới được xem tiêu chí của công chức khác"
            )
        )
    
    # =========================================================================
    # 2. Kiểm tra công chức tồn tại
    # =========================================================================
    cc_stmt = (
        select(CongChuc)
        .where(CongChuc.id == cong_chuc_id)
        .where(CongChuc.is_deleted == False)
    )
    cc_result = await db.execute(cc_stmt)
    cong_chuc = cc_result.scalar_one_or_none()
    
    if not cong_chuc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="Không tìm thấy công chức")
        )
    
    # =========================================================================
    # 3. Kiểm tra cùng đơn vị (nếu là lãnh đạo đơn vị)
    # =========================================================================
    if is_lanh_dao_don_vi and not is_admin and not is_cct_or_pcct:
        if cong_chuc.don_vi_id != current_user.don_vi_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_response(
                    code="PERM_002",
                    message="Lãnh đạo đơn vị chỉ được xem tiêu chí của CC cùng đơn vị"
                )
            )
    
    # =========================================================================
    # 4. Tính số ngày làm việc
    # =========================================================================
    so_ngay_thang = calendar.monthrange(nam, thang)[1]
    so_ngay_nghi = 0  # TODO: Tích hợp module nghỉ phép
    so_ngay_lv = so_ngay_thang - so_ngay_nghi
    target_kpi = so_ngay_lv * 96
    
    # =========================================================================
    # 5. Query đánh giá tháng
    # =========================================================================
    stmt = select(DanhGiaThang).options(
        selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(TieuChiChungDanhGia.tieu_chi),
        selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(TieuChiChungDanhGia.nguoi_phe_duyet),
        selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap1).selectinload(CongChuc.vai_tro),
        selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap2).selectinload(CongChuc.vai_tro),
    ).where(
        DanhGiaThang.cong_chuc_id == cong_chuc_id,
        DanhGiaThang.thang == thang, DanhGiaThang.nam == nam,
        DanhGiaThang.is_deleted == False
    )
    result = await db.execute(stmt)
    danh_gia = result.scalar_one_or_none()
    
    # =========================================================================
    # VIRTUAL RECORD - Chưa có dữ liệu
    # =========================================================================
    if not danh_gia or not danh_gia.tieu_chi_chungs:
        tieu_chi = [build_virtual_tieu_chi_response(m) for m in ["1.1", "1.2", "2.1", "2.2", "2.3", "2.4", "3.1", "3.2", "3.3", "3.4"]]
        return success_response(
            data=DanhGiaThangTieuChiResponse(
                danh_gia_thang_id=danh_gia.id if danh_gia else None,
                cong_chuc_id=cong_chuc_id, thang=thang, nam=nam,
                is_new_record=True,
                so_ngay_trong_thang=so_ngay_thang, so_ngay_nghi_phep=so_ngay_nghi,
                so_ngay_lam_viec=so_ngay_lv, target_kpi=float(target_kpi),
                trang_thai=TrangThaiTieuChiEnum.CHUA_DANH_GIA,
                trang_thai_danh_gia_thang=TrangThaiDanhGiaThangEnum.CHUA_DANH_GIA,
                tong_hop=build_virtual_tong_hop(),
                tieu_chi=tieu_chi,
            ),
            message="Chưa có dữ liệu tiêu chí. Hiển thị giá trị mặc định."
        )
    
    # =========================================================================
    # EXISTING RECORD
    # =========================================================================
    tc_responses = [build_tieu_chi_response(tc, danh_gia.id) for tc in danh_gia.tieu_chi_chungs]
    any_approved = any(tc.trang_thai == TrangThaiTieuChi.DA_PHE_DUYET for tc in danh_gia.tieu_chi_chungs)
    tong_hop = await tinh_tong_diem_tieu_chi_chung(danh_gia.tieu_chi_chungs, use_ld=any_approved)
    
    first_tc = danh_gia.tieu_chi_chungs[0] if danh_gia.tieu_chi_chungs else None
    trang_thai_tc = TrangThaiTieuChiEnum(first_tc.trang_thai.value) if first_tc else TrangThaiTieuChiEnum.NHAP
    
    # v2.6: Thêm thông tin phê duyệt 2 cấp
    response_data = DanhGiaThangTieuChiResponse(
        danh_gia_thang_id=danh_gia.id, cong_chuc_id=cong_chuc_id,
        thang=thang, nam=nam, is_new_record=False,
        so_ngay_trong_thang=so_ngay_thang,
        so_ngay_nghi_phep=danh_gia.so_ngay_nghi_phep or 0,
        so_ngay_lam_viec=danh_gia.so_ngay_lam_viec or so_ngay_lv,
        target_kpi=float((danh_gia.so_ngay_lam_viec or so_ngay_lv) * 96),
        trang_thai=trang_thai_tc,
        trang_thai_danh_gia_thang=TrangThaiDanhGiaThangEnum(danh_gia.trang_thai.value),
        tong_hop=tong_hop, tieu_chi=tc_responses,
        nguoi_phe_duyet_id=first_tc.nguoi_phe_duyet_id if first_tc else None,
        nguoi_phe_duyet_ten=first_tc.nguoi_phe_duyet.ho_ten if first_tc and first_tc.nguoi_phe_duyet else None,
        ngay_gui=first_tc.ngay_gui if first_tc else None,
        ngay_phe_duyet=first_tc.ngay_phe_duyet if first_tc else None,
    )
    
    return success_response(data=response_data, message="Lấy tiêu chí chung thành công")


async def _dong_bo_chi_tiet_bao_cao_chot(
    db, bc, cong_chuc, thang: int, nam: int
) -> Optional[str]:
    """
    CCT/admin sửa điểm tiêu chí chung trên báo cáo ĐÃ CHỐT → cập nhật snapshot
    chi_tiet_xep_loai của công chức đó (điểm TC chung, điểm KPI, điểm tổng, xếp loại)
    và tính lại thống kê A/B/C/D/E của báo cáo, để báo cáo chính thức phản ánh điểm mới.

    Theo lựa chọn "tính lại xếp loại cuối": ghi đè xếp loại đề xuất + quyết định theo
    điểm tổng mới. Trả về mã xếp loại mới (None nếu CC không có chi_tiet trong báo cáo).
    """
    from app.api.v1.endpoints.bao_cao_xep_loai import (
        tinh_diem_cong_chuc, tinh_diem_lanh_dao, _la_thai_san_tron_thang, _truncate_2dp,
    )
    from app.models.bao_cao_xep_loai import ChiTietXepLoai

    ct = (await db.execute(
        select(ChiTietXepLoai).where(
            ChiTietXepLoai.bao_cao_id == bc.id,
            ChiTietXepLoai.cong_chuc_id == cong_chuc.id,
        )
    )).scalar_one_or_none()
    if not ct:
        return None

    # Tính lại điểm đúng theo loại công chức (giống cap_nhat_chi_tiet_tu_du_lieu)
    if cong_chuc.is_lanh_dao:
        ket_qua = await tinh_diem_lanh_dao(db, cong_chuc.id, thang, nam)
    elif cong_chuc.is_hd_111:
        ket_qua = await tinh_diem_lanh_dao(db, cong_chuc.id, thang, nam, is_hd_111=True)
    else:
        ket_qua = await tinh_diem_cong_chuc(db, cong_chuc.id, thang, nam)

    # AUTO-E: nghỉ thai sản trọn tháng → 'E' (giống luồng refresh chuẩn)
    la_thai_san = await _la_thai_san_tron_thang(db, cong_chuc.id, thang, nam)
    xep_loai_ht = "E" if la_thai_san else ket_qua.xep_loai

    ct.diem_tieu_chi_chung = _truncate_2dp(ket_qua.diem_tieu_chi_chung)
    ct.diem_kpi = _truncate_2dp(ket_qua.diem_kpi)
    ct.diem_tong = _truncate_2dp(ket_qua.diem_tong)
    ct.xep_loai_he_thong = xep_loai_ht
    # "Tính lại xếp loại cuối": ghi đè đề xuất + quyết định theo điểm mới.
    ct.xep_loai_de_xuat = xep_loai_ht
    ct.xep_loai_quyet_dinh = xep_loai_ht

    # Tính lại thống kê A/B/C/D/E của báo cáo theo xếp loại cuối cùng.
    cts = (await db.execute(
        select(ChiTietXepLoai).where(ChiTietXepLoai.bao_cao_id == bc.id)
    )).scalars().all()
    dem = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    for c in cts:
        fx = c.xep_loai_quyet_dinh or c.xep_loai_de_xuat or c.xep_loai_he_thong
        if fx in dem:
            dem[fx] += 1
    bc.so_loai_a, bc.so_loai_b = dem["A"], dem["B"]
    bc.so_loai_c, bc.so_loai_d, bc.so_loai_e = dem["C"], dem["D"], dem["E"]

    return xep_loai_ht


@router.post("/{danh_gia_thang_id}/dieu-chinh-danh-gia-thang")
async def dieu_chinh_danh_gia_thang(
    danh_gia_thang_id: UUID,
    payload: DieuChinhDanhGiaThangRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Lãnh đạo chỉnh điểm 'Đánh giá tháng' của tiêu chí chung ở giai đoạn báo cáo xếp loại.

    - Lưu per-tiêu-chí vào tieu_chi_chung_danh_gia.diem_danh_gia_thang (NULL = về Trưởng duyệt).
    - Recompute danh_gia_thang.diem_tieu_chi_chung = SUM(COALESCE(diem_danh_gia_thang, diem_phe_duyet, diem_tu_cham)).
    - Điểm tổng + xếp loại trong báo cáo tự cập nhật khi báo cáo được tải lại (NHAP → cap_nhat_chi_tiet_tu_du_lieu).

    Quyền: TDV/PDV cùng đơn vị, hoặc CCT/PCCT/Admin.
    Chỉ cho phép khi báo cáo xếp loại tháng đó của đơn vị CHƯA chốt (NHAP/TU_CHOI hoặc chưa tạo).
    """
    # 1. Load đánh giá tháng + tiêu chí + công chức
    stmt = select(DanhGiaThang).options(
        selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(TieuChiChungDanhGia.tieu_chi),
    ).where(
        DanhGiaThang.id == danh_gia_thang_id,
        DanhGiaThang.is_deleted == False,
    )
    danh_gia = (await db.execute(stmt)).scalar_one_or_none()
    if not danh_gia:
        raise HTTPException(status_code=404, detail=error_response(
            code="NOT_FOUND", message="Không tìm thấy đánh giá tháng"
        ))

    cong_chuc = (await db.execute(
        select(CongChuc).where(CongChuc.id == danh_gia.cong_chuc_id)
    )).scalar_one_or_none()
    if not cong_chuc:
        raise HTTPException(status_code=404, detail=error_response(
            code="NOT_FOUND", message="Không tìm thấy công chức"
        ))

    # 2. Kiểm tra quyền (giống get_tieu_chi_cong_chuc)
    is_admin = getattr(current_user.vai_tro, 'is_system_admin', False) if current_user.vai_tro else False
    cap_bac = current_user.vai_tro.cap_bac if current_user.vai_tro else None
    is_cct_or_pcct = cap_bac in [CapBacVaiTro.CHI_CUC_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG]
    is_lanh_dao_don_vi = cap_bac in [CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI]

    if not (is_admin or is_cct_or_pcct or is_lanh_dao_don_vi):
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_001", message="Chỉ Lãnh đạo hoặc Admin mới được điều chỉnh điểm Đánh giá tháng"
        ))
    if is_lanh_dao_don_vi and not is_admin and not is_cct_or_pcct:
        if cong_chuc.don_vi_id != current_user.don_vi_id:
            raise HTTPException(status_code=403, detail=error_response(
                code="PERM_002", message="Lãnh đạo đơn vị chỉ được điều chỉnh CC cùng đơn vị"
            ))

    # 3. Guard theo trạng thái báo cáo xếp loại tháng đó của đơn vị.
    #    CCT (và admin) được sửa BẤT KỂ trạng thái — kể cả báo cáo ĐÃ DUYỆT — khi đó
    #    bước 6 sẽ tự đồng bộ snapshot + xếp loại + thống kê của báo cáo chính thức.
    #    PCCT/TDV/PDV vẫn chỉ được sửa khi báo cáo CHƯA chốt (NHAP/TU_CHOI).
    is_cct = cap_bac == CapBacVaiTro.CHI_CUC_TRUONG
    duoc_sua_da_chot = is_admin or is_cct
    bc = (await db.execute(
        select(BaoCaoXepLoai).where(
            BaoCaoXepLoai.don_vi_id == cong_chuc.don_vi_id,
            BaoCaoXepLoai.thang == danh_gia.thang,
            BaoCaoXepLoai.nam == danh_gia.nam,
            BaoCaoXepLoai.is_deleted == False,
        )
    )).scalar_one_or_none()
    bao_cao_da_chot = bool(
        bc and bc.trang_thai not in [TrangThaiBaoCao.NHAP.value, TrangThaiBaoCao.TU_CHOI.value]
    )
    if bao_cao_da_chot and not duoc_sua_da_chot:
        raise HTTPException(status_code=400, detail=error_response(
            code="BIZ_001", message=f"Không thể điều chỉnh khi báo cáo đang ở trạng thái {bc.trang_thai}"
        ))

    # 4. Áp điểm Đánh giá tháng per-tiêu-chí
    tc_map = {tc.tieu_chi.ma_tieu_chi: tc for tc in danh_gia.tieu_chi_chungs}
    for item in payload.tieu_chi:
        tc = tc_map.get(item.ma_tieu_chi)
        if not tc:
            raise HTTPException(status_code=400, detail=error_response(
                code="VAL_003", message=f"Tiêu chí {item.ma_tieu_chi} không có trong đánh giá tháng này"
            ))
        if item.diem_danh_gia_thang is None:
            tc.diem_danh_gia_thang = None
        else:
            tc.diem_danh_gia_thang = Decimal(str(item.diem_danh_gia_thang))

    # 5. Recompute tổng điểm tiêu chí chung (0-30)
    tong = Decimal("0")
    for tc in danh_gia.tieu_chi_chungs:
        if tc.diem_danh_gia_thang is not None:
            diem = tc.diem_danh_gia_thang
        elif tc.diem_phe_duyet is not None:
            diem = tc.diem_phe_duyet
        else:
            diem = tc.diem_tu_cham
        tong += diem
    if tong < 0:
        tong = Decimal("0")
    if tong > 30:
        tong = Decimal("30")
    danh_gia.diem_tieu_chi_chung = tong

    await db.flush()

    # 6. Báo cáo ĐÃ CHỐT (CCT/admin sửa) → đồng bộ snapshot chi_tiet + xếp loại + thống kê
    #    để báo cáo chính thức phản ánh điểm mới. Báo cáo chưa chốt tự refresh khi tải lại.
    xep_loai_moi = None
    if bc and bao_cao_da_chot:
        xep_loai_moi = await _dong_bo_chi_tiet_bao_cao_chot(
            db, bc, cong_chuc, danh_gia.thang, danh_gia.nam
        )
        await db.flush()

    return success_response(
        data={
            "danh_gia_thang_id": str(danh_gia.id),
            "diem_tieu_chi_chung": float(tong),
            "bao_cao_da_chot": bao_cao_da_chot,
            "xep_loai_moi": xep_loai_moi,
        },
        message="Cập nhật điểm Đánh giá tháng thành công"
    )


@router.get("/kpi/thang/{thang}/nam/{nam}")
async def get_kpi_summary(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int,
    nam: int,
) -> dict:
    """
    Lấy tổng hợp KPI tháng (cả 30đ + 70đ).
    """
    # 1. Lấy dữ liệu tiêu chí chung (30đ)
    tc_data = await get_tieu_chi_chung(db, current_user.id, thang, nam)
    
    # 2. Lấy dữ liệu kê khai đã duyệt (70đ)
    ke_khai_stats = await tinh_tong_sp_thang(db, current_user.id, thang, nam)
    
    # 3. Lấy ngày nghỉ
    nghi_phep = await tinh_tong_ngay_nghi_thang(db, current_user.id, thang, nam)
    
    # 4. Tính điểm KPI — PHÂN NHÁNH đúng theo loại CC (giống /xep-loai/tong-hop
    #    và bản in phiếu): lãnh đạo / HĐ111 VB714 / HĐ111 form lãnh đạo / CC thường.
    #    Trước đây hardcode công thức CC thường (ngày×96) → HĐ111 & lãnh đạo bị SAI.
    from app.api.v1.endpoints.xep_loai_moi import (
        tinh_diem_kpi_70,
        tinh_diem_kpi_70_lanh_dao,
        tinh_diem_kpi_70_hd_111,
        _has_ke_khai_lanh_dao,
    )
    from app.core.hdld_vb714 import is_hdld_vb714_active, tinh_diem_kpi_70_hdld_vb714

    so_ngay_lam_viec = nghi_phep["so_ngay_lam_viec"]
    target_sp = float(so_ngay_lam_viec) * 96
    tong_sp_hoan_thanh = ke_khai_stats["tong_sp_quy_doi"]
    tong_sp_chat_luong = ke_khai_stats["tong_sp_chat_luong"]
    tong_sp_tien_do = ke_khai_stats["tong_sp_tien_do"]

    cc = current_user
    _vb = None
    if cc.is_lanh_dao:
        kd = await tinh_diem_kpi_70_lanh_dao(db, cc.id, thang, nam, tam_tinh=False)
    elif cc.is_hd_111 and is_hdld_vb714_active(thang, nam) and (
        _vb := await tinh_diem_kpi_70_hdld_vb714(db, cc.id, thang, nam, tam_tinh=False)
    ) is not None:
        kd = _vb
    elif cc.is_hd_111 and await _has_ke_khai_lanh_dao(db, cc.id, thang, nam):
        kd = await tinh_diem_kpi_70_hd_111(db, cc.id, thang, nam, tam_tinh=False)
    else:
        kd = await tinh_diem_kpi_70(db, cc.id, thang, nam, tam_tinh=False)

    a_so_luong = kd.get("a_so_luong", 0)
    # Chuẩn hóa b=tiến độ, c=chất lượng (tinh_diem_kpi_70 CC dùng key legacy đảo)
    b_chat_luong = kd.get("b_tien_do", kd.get("b_chat_luong", 0))
    c_tien_do = kd.get("c_chat_luong", kd.get("c_tien_do", 0))
    diem_kpi = kd.get("diem_kpi", 0)
    diem_kpi_quy_doi = kd.get("diem_70", 0)
    
    return success_response(data={
        "thang": thang,
        "nam": nam,
        "is_new_record": tc_data is None,
        
        # Ngày làm việc
        "so_ngay_trong_thang": nghi_phep["so_ngay_trong_thang"],
        "so_ngay_nghi_phep": float(nghi_phep["tong_ngay_nghi"]),
        "so_ngay_lam_viec": float(so_ngay_lam_viec),
        
        # Target & Kết quả
        "so_sp_goc_duoc_giao": target_sp,
        "tong_sp_hoan_thanh": tong_sp_hoan_thanh,
        "tong_sp_chat_luong": tong_sp_chat_luong,
        "tong_sp_tien_do": tong_sp_tien_do,
        
        # Điểm chi tiết
        "diem_chi_tiet": {
            "a_so_luong": a_so_luong,
            "b_chat_luong": b_chat_luong,
            "c_tien_do": c_tien_do,
        },
        "diem_kpi": diem_kpi,
        "diem_kpi_quy_doi": diem_kpi_quy_doi,
        
        # Tiêu chí chung
        "diem_tieu_chi_chung": tc_data["tong_diem"] if tc_data else 0,
        
        # Tổng điểm
        "diem_tong": (tc_data["tong_diem"] if tc_data else 0) + diem_kpi_quy_doi,
    })


# =============================================================================
# HELPER FUNCTIONS (Private - used by other modules)
# =============================================================================

async def get_tieu_chi_chung(db: AsyncSession, cong_chuc_id: UUID, thang: int, nam: int) -> Optional[dict]:
    """Lấy dữ liệu tiêu chí chung cho KPI summary."""
    stmt = select(DanhGiaThang).options(
        selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(TieuChiChungDanhGia.tieu_chi)
    ).where(
        DanhGiaThang.cong_chuc_id == cong_chuc_id,
        DanhGiaThang.thang == thang,
        DanhGiaThang.nam == nam,
        DanhGiaThang.is_deleted == False
    )
    result = await db.execute(stmt)
    danh_gia = result.scalar_one_or_none()
    
    if not danh_gia or not danh_gia.tieu_chi_chungs:
        return None
    
    tong_hop = await tinh_tong_diem_tieu_chi_chung(danh_gia.tieu_chi_chungs, use_ld=True)
    return {"tong_diem": tong_hop.tong_diem}


async def tinh_tong_sp_thang(db: AsyncSession, cong_chuc_id: UUID, thang: int, nam: int) -> dict:
    """Placeholder - tính tổng SP đã duyệt trong tháng."""
    # TODO: Implement actual logic from ke_khai module
    return {
        "tong_sp_quy_doi": 0,
        "tong_sp_chat_luong": 0,
        "tong_sp_tien_do": 0,
    }


async def tinh_tong_ngay_nghi_thang(db: AsyncSession, cong_chuc_id: UUID, thang: int, nam: int) -> dict:
    """Placeholder - tính tổng ngày nghỉ trong tháng."""
    # TODO: Import from nghi_phep module
    so_ngay = calendar.monthrange(nam, thang)[1]
    return {
        "tong_ngay_nghi": Decimal("0"),
        "so_ngay_trong_thang": so_ngay,
        "so_ngay_lam_viec": Decimal(str(so_ngay)),
    }