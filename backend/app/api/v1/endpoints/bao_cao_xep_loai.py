"""
app/api/v1/endpoints/bao_cao_xep_loai.py
========================================
API Endpoints cho Báo cáo Xếp loại Chất lượng Công chức.

Endpoints:
1. GET  /don-vi/thang/{thang}/nam/{nam}  - Lấy/Tạo báo cáo đơn vị (Đội trưởng)
2. PUT  /chi-tiet/{id}/de-xuat           - Điều chỉnh xếp loại đề xuất (Đội trưởng)
3. POST /{id}/gui-duyet                  - Gửi báo cáo lên CCT (Đội trưởng)
4. GET  /cho-phe-duyet                   - DS báo cáo chờ phê duyệt (CCT)
5. GET  /{id}                            - Chi tiết báo cáo (CCT)
6. PUT  /chi-tiet/{id}/quyet-dinh        - Điều chỉnh xếp loại quyết định (CCT)
7. POST /{id}/phe-duyet                  - Phê duyệt/Từ chối (CCT)
8. GET  /thong-ke/thang/{thang}/nam/{nam} - Thống kê toàn Chi cục

Tham chiếu: Điều 17 - Quy chế đánh giá KPI Chi cục Hải quan KV8

Phiên bản: 1.3 (09/02/2026) - FIX: xep_loai_de_xuat tự động cập nhật khi điểm thay đổi
Phiên bản: 1.2 (31/01/2026) - FIX MissingGreenlet error khi truy cập lazy-loaded relationships
Phiên bản: 1.1 (30/01/2026) - Thêm so_ngay_lam_viec, so_ngay_nghi vào response
"""

from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from typing import Optional, List, Tuple, NamedTuple
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import DatabaseDep, ActiveUserDep, is_qldv
from app.models.user_org import CongChuc, DonVi, LoaiDonVi, VaiTro, CapBacVaiTro
from app.models.kpi_assessment import DanhGiaThang
from app.models.kpi_submission import KeKhaiCongViec
from app.models.leave import DangKyNghi
from app.models.leader_kpi import KeKhaiLanhDao, DanhGiaDDE, TrangThaiKeKhaiLD, TrangThaiDDE
from app.models.bao_cao_xep_loai import (
    BaoCaoXepLoai, ChiTietXepLoai, TrangThaiBaoCao, tinh_xep_loai
)
from app.schemas.common import success_response, error_response
from app.schemas.bao_cao_xep_loai import (
    DeXuatXepLoaiRequest, QuyetDinhXepLoaiRequest,
    PheDuyetBaoCaoRequest, get_trang_thai_ten
)

from pydantic import BaseModel, Field


class TraLaiBaoCaoRequest(BaseModel):
    """Yêu cầu trả lại báo cáo xếp loại đã phê duyệt."""
    ly_do: str = Field(..., min_length=1, max_length=500, description="Lý do trả lại (bắt buộc)")


router = APIRouter()


# =============================================================================
# HELPER FUNCTIONS - KIỂM TRA QUYỀN
# =============================================================================

def check_is_truong_don_vi(user: CongChuc) -> bool:
    """Kiểm tra user có phải là Trưởng đơn vị không."""
    if not user.vai_tro:
        return False
    return user.vai_tro.cap_bac == CapBacVaiTro.TRUONG_DON_VI


def check_is_chi_cuc_truong(user: CongChuc) -> bool:
    """Kiểm tra user có phải là Chi cục trưởng không."""
    if not user.vai_tro:
        return False
    return user.vai_tro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG


def check_is_lanh_dao_chi_cuc(user: CongChuc) -> bool:
    """Kiểm tra user có phải là Lãnh đạo Chi cục (CCT hoặc PCCT) hoặc có quyền xem toàn chi cục không."""
    # v1.1.0: User có flag can_view_all_units cũng được xem (read-only)
    if getattr(user, 'can_view_all_units', False):
        return True
    if not user.vai_tro:
        return False
    return user.vai_tro.cap_bac in [
        CapBacVaiTro.CHI_CUC_TRUONG,
        CapBacVaiTro.PHO_CHI_CUC_TRUONG
    ]

def check_is_pho_don_vi(user: CongChuc) -> bool:
    """Kiểm tra user có phải là Phó Đơn vị (Phó Đội trưởng) không."""
    if not user.vai_tro:
        return False
    return user.vai_tro.cap_bac == CapBacVaiTro.PHO_DON_VI


def check_is_lanh_dao_don_vi(user: CongChuc) -> bool:
    """
    Kiểm tra user có phải là Lãnh đạo đơn vị (ĐT hoặc Phó ĐT hoặc QLDV) không.
    v3.6: Thêm QLDV (read-only)
    """
    if not user.vai_tro:
        return False
    return user.vai_tro.cap_bac in [
        CapBacVaiTro.TRUONG_DON_VI,
        CapBacVaiTro.PHO_DON_VI,
        CapBacVaiTro.QUAN_LY_DON_VI,  # QLDV
    ]


def check_can_view_bao_cao(user: CongChuc) -> bool:
    """
    Kiểm tra user có quyền XEM báo cáo không.
    Quyền xem: QLDV, Phó ĐT, ĐT, Phó CCT, CCT, hoặc user có flag can_view_all_units
    v3.6: Thêm QLDV (read-only với don_vi scope)
    """
    # v1.1.0: User có flag can_view_all_units luôn được xem
    if getattr(user, 'can_view_all_units', False):
        return True
    if not user.vai_tro:
        return False
    return user.vai_tro.cap_bac in [
        CapBacVaiTro.QUAN_LY_DON_VI,  # QLDV - CHỈ XEM (v3.6)
        CapBacVaiTro.PHO_DON_VI,      # Phó Đội trưởng - CHỈ XEM
        CapBacVaiTro.TRUONG_DON_VI,   # Đội trưởng - XEM + SỬA
        CapBacVaiTro.PHO_CHI_CUC_TRUONG,  # Phó CCT - CHỈ XEM
        CapBacVaiTro.CHI_CUC_TRUONG,  # CCT - XEM + DUYỆT
    ]


def check_can_edit_bao_cao(user: CongChuc) -> bool:
    """
    Kiểm tra user có quyền CHỈNH SỬA báo cáo không.

    Quyền sửa: ĐT (lập báo cáo), CCT (phê duyệt)
    v3.6: QLDV KHÔNG có quyền sửa (chỉ xem)
    """
    if not user.vai_tro:
        return False
    return user.vai_tro.cap_bac in [
        CapBacVaiTro.TRUONG_DON_VI,   # Đội trưởng - lập báo cáo
        CapBacVaiTro.CHI_CUC_TRUONG,  # CCT - phê duyệt
        # KHÔNG bao gồm QLDV
    ]

def check_can_approve_bao_cao(user: CongChuc) -> bool:
    """
    Kiểm tra user có quyền PHÊ DUYỆT báo cáo không.
    Quyền duyệt: Chỉ CCT
    v3.6: QLDV KHÔNG có quyền phê duyệt (chỉ xem)
    """
    if not user.vai_tro:
        return False
    return user.vai_tro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG
    # KHÔNG bao gồm QLDV


# =============================================================================
# HELPER FUNCTIONS - TÍNH ĐIỂM (v1.1 - Thêm so_ngay_lam_viec, so_ngay_nghi)
# =============================================================================

class KetQuaTinhDiem(NamedTuple):
    """Kết quả tính điểm công chức - v1.1 thêm ngày làm việc/nghỉ."""
    diem_tieu_chi_chung: Decimal
    diem_kpi: Decimal
    diem_tong: Decimal
    xep_loai: str
    so_ngay_lam_viec: Decimal
    so_ngay_nghi: Decimal


def _truncate_2dp(value: Optional[Decimal]) -> Optional[Decimal]:
    # Cắt bỏ về 2 thập phân (ROUND_DOWN). Match formatScore() ở FE và tránh
    # 89.997 bị Numeric(5,2) round-half-up thành 90.00 → /xep-loai hiện 90.0
    # còn /danh-gia (live) hiện 89.9.
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)


async def tinh_diem_cong_chuc(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int
) -> KetQuaTinhDiem:
    """
    Tính điểm cho công chức KHÔNG phải lãnh đạo.
    
    FIX v1.1 (28/01/2026): 
    - Tính điểm KPI trực tiếp từ ke_khai_cong_viec thay vì đọc từ danh_gia_thang
    - Nguyên nhân bug: diem_kpi không được ghi vào danh_gia_thang
    
    v1.1 (30/01/2026):
    - Trả về thêm so_ngay_lam_viec, so_ngay_nghi
    
    Công thức: 
    - a = SP_hoàn_thành / SP_được_giao (tỷ lệ số lượng)
    - b = SP_đạt_chất_lượng / SP_hoàn_thành (tỷ lệ chất lượng)  
    - c = SP_đúng_tiến_độ / SP_hoàn_thành (tỷ lệ tiến độ)
    - diem_kpi_ratio = (a + b + c) / 3 (0-1)
    - diem_kpi = diem_kpi_ratio × 70 (0-70)
    - diem_tong = diem_tieu_chi_chung + diem_kpi (0-100)
    
    Returns:
        KetQuaTinhDiem(diem_tcc, diem_kpi, diem_tong, xep_loai, so_ngay_lv, so_ngay_nghi)
    """
    # Import trong hàm để tránh circular import
    from app.models.kpi_submission import KeKhaiCongViec, TrangThaiKeKhai
    from app.api.v1.endpoints.nghi_phep import tinh_tong_ngay_nghi_thang
    
    # =========================================================================
    # 1. Lấy điểm tiêu chí chung (30 điểm) từ danh_gia_thang
    # =========================================================================
    dg_stmt = select(DanhGiaThang).where(
        DanhGiaThang.cong_chuc_id == cong_chuc_id,
        DanhGiaThang.thang == thang,
        DanhGiaThang.nam == nam,
        DanhGiaThang.is_deleted == False,
    )
    dg_result = await db.execute(dg_stmt)
    danh_gia = dg_result.scalar_one_or_none()
    
    diem_tcc = Decimal("0")
    if danh_gia and danh_gia.diem_tieu_chi_chung:
        diem_tcc = Decimal(str(danh_gia.diem_tieu_chi_chung))
    
    # =========================================================================
    # 2. Tính số ngày làm việc + nghỉ (luôn dùng để hiển thị/báo cáo)
    # =========================================================================
    nghi_phep_data = await tinh_tong_ngay_nghi_thang(db, cong_chuc_id, thang, nam)
    so_ngay_lam_viec = Decimal(str(nghi_phep_data.get("so_ngay_lam_viec", 0)))
    so_ngay_nghi = Decimal(str(nghi_phep_data.get("tong_ngay_nghi", 0)))

    # =========================================================================
    # 3. Lấy tổng SP từ kê khai ĐÃ PHÊ DUYỆT
    # =========================================================================
    kk_stmt = select(
        func.coalesce(func.sum(KeKhaiCongViec.so_sp_goc_quy_doi), Decimal("0")).label("tong_sp_quy_doi"),
        func.coalesce(func.sum(KeKhaiCongViec.so_sp_chat_luong), Decimal("0")).label("tong_sp_chat_luong"),
        func.coalesce(func.sum(KeKhaiCongViec.so_sp_tien_do), Decimal("0")).label("tong_sp_tien_do"),
    ).where(
        KeKhaiCongViec.cong_chuc_id == cong_chuc_id,
        KeKhaiCongViec.thang == thang,
        KeKhaiCongViec.nam == nam,
        KeKhaiCongViec.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET,
        KeKhaiCongViec.is_deleted == False,
    )
    kk_result = await db.execute(kk_stmt)
    kk_row = kk_result.one()

    tong_sp_hoan_thanh = Decimal(str(kk_row.tong_sp_quy_doi or 0))
    tong_sp_chat_luong = Decimal(str(kk_row.tong_sp_chat_luong or 0))
    tong_sp_tien_do = Decimal(str(kk_row.tong_sp_tien_do or 0))

    # =========================================================================
    # PL3 V2 (28/04/2026): Mẫu số = tổng SP kê khai đã duyệt
    # =========================================================================
    # FIX 05/05/2026: check V2 dựa vào sự tồn tại KK V2_PL3 thực tế của CC
    # (nguồn sự thật từ ke_khai_cong_viec). Trước đây check qua
    # danh_gia.version_tinh_diem hoặc resolve_kpi_version (đọc danh_gia_thang
    # ở step 1) — nhưng field này không được cập nhật khi platform default
    # đổi sang V2_PL3 → CC V2 bị fallback V1 (target = ngày × 96) → điểm
    # xếp loại lệch so với trang /danh-gia.
    from app.core.kpi_version import VERSION_V2
    v2_check_stmt = select(func.count(KeKhaiCongViec.id)).where(
        KeKhaiCongViec.cong_chuc_id == cong_chuc_id,
        KeKhaiCongViec.thang == thang,
        KeKhaiCongViec.nam == nam,
        KeKhaiCongViec.version_kekhai == "V2_PL3",
        KeKhaiCongViec.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET,
        KeKhaiCongViec.is_deleted == False,
    )
    v2_count = (await db.execute(v2_check_stmt)).scalar() or 0
    is_v2 = v2_count > 0

    if is_v2:
        # V2: dispatch sang helper thống nhất với /danh-gia-v2
        # (lọc version_kekhai='V2_PL3', mẫu số = SUM(so_sp_goc_quy_doi)).
        from app.api.v1.endpoints.xep_loai_moi import tinh_diem_kpi_70_v2
        v2_data = await tinh_diem_kpi_70_v2(db, cong_chuc_id, thang, nam, tam_tinh=False)
        diem_kpi_v2 = Decimal(str(v2_data["diem_70"]))
        diem_tong_v2 = (diem_tcc or Decimal("0")) + diem_kpi_v2
        xep_loai_v2 = tinh_xep_loai(diem_tong_v2)
        # Cache tong_sp_ke_khai vào danh_gia (để báo cáo tham chiếu)
        if danh_gia is not None:
            danh_gia.tong_sp_ke_khai = Decimal(str(v2_data["tong_sp_ke_khai"]))
            # Cập nhật version_tinh_diem cho nhất quán
            if getattr(danh_gia, "version_tinh_diem", None) != VERSION_V2:
                danh_gia.version_tinh_diem = VERSION_V2
        return KetQuaTinhDiem(
            diem_tieu_chi_chung=diem_tcc,
            diem_kpi=diem_kpi_v2,
            diem_tong=diem_tong_v2,
            xep_loai=xep_loai_v2.value,
            so_ngay_lam_viec=so_ngay_lam_viec,
            so_ngay_nghi=so_ngay_nghi,
        )

    # V1: target_sp = số ngày làm việc × 96 SP/ngày
    target_sp = so_ngay_lam_viec * Decimal("96")
    
    # =========================================================================
    # 4. Tính các chỉ số a, b, c
    # =========================================================================
    # a = Tỷ lệ số lượng = SP_hoàn_thành / SP_được_giao
    if target_sp > 0:
        a_so_luong = tong_sp_hoan_thanh / target_sp
    else:
        a_so_luong = Decimal("0")
    
    # b = Tỷ lệ chất lượng = SP_đạt_CL / SP_hoàn_thành
    # c = Tỷ lệ tiến độ = SP_đúng_TĐ / SP_hoàn_thành
    if target_sp > 0:
        b_chat_luong = tong_sp_chat_luong / target_sp  # Chia cho TARGET
        c_tien_do = tong_sp_tien_do / target_sp        # Chia cho TARGET
    else:
        b_chat_luong = Decimal("0")
        c_tien_do = Decimal("0")
    
    # Cap giá trị tại 1.0 (100%) - không vượt quá 100%
    a_so_luong = min(a_so_luong, Decimal("1.0"))
    b_chat_luong = min(b_chat_luong, Decimal("1.0"))
    c_tien_do = min(c_tien_do, Decimal("1.0"))
    
    # =========================================================================
    # 5. Tính điểm KPI (70 điểm)
    # =========================================================================
    # KPI ratio = (a + b + c) / 3 (giá trị 0-1)
    kpi_ratio = (a_so_luong + b_chat_luong + c_tien_do) / Decimal("3")
    
    # Điểm KPI quy đổi = KPI ratio × 70 (giá trị 0-70)
    diem_kpi = kpi_ratio * Decimal("70")
    
    # =========================================================================
    # 6. Tính điểm tổng và xếp loại
    # =========================================================================
    diem_tong = (diem_tcc or Decimal("0")) + (diem_kpi or Decimal("0"))
    xep_loai = tinh_xep_loai(diem_tong)
    
    return KetQuaTinhDiem(
        diem_tieu_chi_chung=diem_tcc,
        diem_kpi=diem_kpi,
        diem_tong=diem_tong,
        xep_loai=xep_loai.value,
        so_ngay_lam_viec=so_ngay_lam_viec,
        so_ngay_nghi=so_ngay_nghi,
    )


async def tinh_diem_lanh_dao(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
    *,
    is_hd_111: bool = False,
) -> KetQuaTinhDiem:
    """
    Tính điểm cho công chức kê khai theo form Lãnh đạo.

    v1.1 (30/01/2026): Trả về thêm so_ngay_lam_viec, so_ngay_nghi
    Phase 3 (29/04/2026): thêm flag is_hd_111 — HĐ 111 dùng cùng nguồn
    ke_khai_lanh_dao nhưng KHÔNG có d/đ/e, KPI = (a + b + c) / 3.

    Phase 3 KPI LĐ V2 (05/05/2026): từ tháng 5/2026 trở đi, LĐ thật KÊ KHAI
    THEO FORM V2 (kpi_submission). Tính điểm:
    - HĐ 111: vẫn đọc ke_khai_lanh_dao như cũ.
    - LĐ thật + tháng < 5/2026: vẫn đọc ke_khai_lanh_dao như cũ.
    - LĐ thật + tháng ≥ 5/2026: gọi calc_kpi_lanh_dao_v2 — scope mở rộng
      sang SP cấp dưới (xem app.core.kpi_lanh_dao_v2).

    Công thức:
    - LĐ thật: KPI = (a + b + c + d + đ + e) / 6 × 70
    - HĐ 111:  KPI = (a + b + c) / 3 × 70

    Returns:
        KetQuaTinhDiem(diem_tcc, diem_kpi, diem_tong, xep_loai, so_ngay_lv, so_ngay_nghi)
    """
    from app.api.v1.endpoints.nghi_phep import tinh_tong_ngay_nghi_thang
    from app.core.kpi_lanh_dao_v2 import (
        calc_kpi_lanh_dao_v2,
        is_kpi_lanh_dao_v2_active,
    )

    # Lấy điểm tiêu chí chung từ danh_gia_thang
    dg_stmt = select(DanhGiaThang).where(
        DanhGiaThang.cong_chuc_id == cong_chuc_id,
        DanhGiaThang.thang == thang,
        DanhGiaThang.nam == nam,
        DanhGiaThang.is_deleted == False,
    )
    dg_result = await db.execute(dg_stmt)
    danh_gia = dg_result.scalar_one_or_none()
    diem_tcc = danh_gia.diem_tieu_chi_chung if danh_gia else Decimal("0")

    # =====================================================================
    # NHÁNH MỚI (Phase 3 — 05/05/2026): LĐ thật + tháng ≥ 5/2026 → gọi V2
    # HĐ 111 vẫn đi theo nhánh cũ bên dưới.
    # =====================================================================
    if not is_hd_111 and is_kpi_lanh_dao_v2_active(thang, nam):
        try:
            v2_result = await calc_kpi_lanh_dao_v2(db, cong_chuc_id, thang, nam)
        except ValueError:
            # Không phải LĐ → fallback (an toàn)
            v2_result = None

        if v2_result is not None:
            kpi_ratio_v2 = Decimal(str(v2_result["kpi_tong"]))
            diem_kpi_v2 = kpi_ratio_v2 * Decimal("70")
            diem_tong_v2 = (diem_tcc or Decimal("0")) + diem_kpi_v2

            nghi_phep_data = await tinh_tong_ngay_nghi_thang(db, cong_chuc_id, thang, nam)
            so_ngay_lam_viec_v2 = Decimal(str(nghi_phep_data.get("so_ngay_lam_viec", 0)))
            so_ngay_nghi_v2 = Decimal(str(nghi_phep_data.get("tong_ngay_nghi", 0)))

            return KetQuaTinhDiem(
                diem_tieu_chi_chung=diem_tcc,
                diem_kpi=diem_kpi_v2,
                diem_tong=diem_tong_v2,
                xep_loai=tinh_xep_loai(diem_tong_v2).value,
                so_ngay_lam_viec=so_ngay_lam_viec_v2,
                so_ngay_nghi=so_ngay_nghi_v2,
            )
    
    # =====================================================================
    # NHÁNH HĐLĐ 111 VB714 (01/06/2026): từ T5/2026 đọc điểm từ hdld_danh_gia
    # (Bộ tiêu chí VB714, 3 tiêu chí × cột cấp quản lý). Nếu chưa có bản DA_DUYET
    # → rơi xuống nhánh cũ (ke_khai_lanh_dao) để không vỡ tháng chuyển tiếp.
    # =====================================================================
    if is_hd_111:
        from app.core.hdld_vb714 import (
            is_hdld_vb714_active, get_hdld_danh_gia_da_duyet, kpi_70_tu_tb, tb_3_tieu_chi,
        )
        if is_hdld_vb714_active(thang, nam):
            dg_vb714 = await get_hdld_danh_gia_da_duyet(db, cong_chuc_id, thang, nam)
            if dg_vb714 is not None:
                diem_kpi_vb714 = dg_vb714.diem_kpi_70
                if diem_kpi_vb714 is None:
                    diem_kpi_vb714 = kpi_70_tu_tb(
                        tb_3_tieu_chi([ct.diem_ql for ct in dg_vb714.chi_tiets])
                    )
                diem_kpi_vb714 = diem_kpi_vb714 or Decimal("0")
                diem_tong_vb714 = (diem_tcc or Decimal("0")) + diem_kpi_vb714
                nghi_vb714 = await tinh_tong_ngay_nghi_thang(db, cong_chuc_id, thang, nam)
                return KetQuaTinhDiem(
                    diem_tieu_chi_chung=diem_tcc,
                    diem_kpi=diem_kpi_vb714,
                    diem_tong=diem_tong_vb714,
                    xep_loai=tinh_xep_loai(diem_tong_vb714).value,
                    so_ngay_lam_viec=Decimal(str(nghi_vb714.get("so_ngay_lam_viec", 0))),
                    so_ngay_nghi=Decimal(str(nghi_vb714.get("tong_ngay_nghi", 0))),
                )

    # =========================================================================
    # Tính số ngày làm việc và nghỉ (v1.1)
    # =========================================================================
    nghi_phep_data = await tinh_tong_ngay_nghi_thang(db, cong_chuc_id, thang, nam)
    so_ngay_lam_viec = Decimal(str(nghi_phep_data.get("so_ngay_lam_viec", 0)))
    so_ngay_nghi = Decimal(str(nghi_phep_data.get("tong_ngay_nghi", 0)))

    # Tính a, b, c từ ke_khai_lanh_dao (đã phê duyệt)
    kk_stmt = select(KeKhaiLanhDao).where(
        KeKhaiLanhDao.cong_chuc_id == cong_chuc_id,
        KeKhaiLanhDao.thang == thang,
        KeKhaiLanhDao.nam == nam,
        KeKhaiLanhDao.trang_thai == TrangThaiKeKhaiLD.DA_PHE_DUYET.value,
        KeKhaiLanhDao.is_deleted == False,
    )
    kk_result = await db.execute(kk_stmt)
    ke_khais = kk_result.scalars().all()
    
    if not ke_khais:
        a, b, c = Decimal("0"), Decimal("0"), Decimal("0")
    else:
        tong_sp = len(ke_khais)
        # Đếm số công việc hoàn thành (trang_thai_hoan_thanh = DA_HOAN_THANH)
        tong_hoan_thanh = sum(1 for kk in ke_khais if kk.trang_thai_hoan_thanh == 'DA_HOAN_THANH')
        
        # =====================================================================
        # FIX v2.6.1 - Công thức đúng theo Quy chế KPI:
        # a - Hoàn thành: Số việc hoàn thành / Tổng việc được giao
        # b - Tiến độ: Σ(điểm_tiến_độ_i) / tổng_cv
        #     Mỗi CV: điểm = max(0, 1 - số_lỗi × 0.25)
        # c - Chất lượng: Σ(điểm_chất_lượng_i) / tổng_cv
        #     Mỗi CV: điểm = max(0, 1 - số_lỗi × 0.25)
        #
        # Ví dụ: 6 CV, 1 CV bị 1 lỗi CL
        # c = (5×1 + 1×0.75) / 6 = 5.75/6 = 0.9583 (95.8%)
        # =====================================================================
        
        # a = Số việc hoàn thành / Tổng việc
        a = Decimal(tong_hoan_thanh) / Decimal(tong_sp) if tong_sp > 0 else Decimal("0")
        
        # b = Tổng điểm tiến độ / Tổng CV
        # Mỗi CV: điểm_tiến_độ = max(0, 1 - số_lỗi_tiến_độ × 0.25)
        tong_diem_tien_do = sum(
            max(Decimal("0"), Decimal("1") - Decimal(kk.so_loi_tien_do or 0) * Decimal("0.25"))
            for kk in ke_khais
        )
        b = tong_diem_tien_do / Decimal(tong_sp) if tong_sp > 0 else Decimal("0")
        
        # c = Tổng điểm chất lượng / Tổng CV
        # Mỗi CV: điểm_chất_lượng = max(0, 1 - số_lỗi_chất_lượng × 0.25)
        tong_diem_chat_luong = sum(
            max(Decimal("0"), Decimal("1") - Decimal(kk.so_loi_chat_luong or 0) * Decimal("0.25"))
            for kk in ke_khais
        )
        c = tong_diem_chat_luong / Decimal(tong_sp) if tong_sp > 0 else Decimal("0")
    
    # Lấy d, đ, e — chỉ cho LĐ thật, HĐ 111 không có d/đ/e (Phase 3 — 29/04/2026).
    if is_hd_111:
        # HĐ 111: KPI = (a + b + c) / 3 — bỏ qua d/đ/e
        kpi_ratio = (a + b + c) / Decimal("3")
    else:
        # Lãnh đạo: lấy d/đ/e từ danh_gia_dde (đã phê duyệt)
        dde_stmt = select(DanhGiaDDE).where(
            DanhGiaDDE.cong_chuc_id == cong_chuc_id,
            DanhGiaDDE.thang == thang,
            DanhGiaDDE.nam == nam,
            DanhGiaDDE.trang_thai == TrangThaiDDE.DA_PHE_DUYET.value,
        )
        dde_result = await db.execute(dde_stmt)
        dde = dde_result.scalar_one_or_none()

        if dde:
            # ⚠️ BUGFIX: Sử dụng đúng tên field và property helper
            # Giá trị DDE là 50 hoặc 100 → chia 100 để thành tỷ lệ 0.5 hoặc 1.0
            d = Decimal(str(dde.d_final)) / Decimal("100")
            dd = Decimal(str(dde.dd_final)) / Decimal("100")
            e = Decimal(str(dde.e_final)) / Decimal("100")
        else:
            # Chưa có đánh giá DDE → default 100% (tỷ lệ 1.0)
            d, dd, e = Decimal("1.0"), Decimal("1.0"), Decimal("1.0")

        # KPI = (a + b + c + d + đ + e) / 6
        kpi_ratio = (a + b + c + d + dd + e) / Decimal("6")

    diem_kpi = kpi_ratio * Decimal("70")
    diem_tong = (diem_tcc or Decimal("0")) + (diem_kpi or Decimal("0"))
    xep_loai = tinh_xep_loai(diem_tong)
    
    return KetQuaTinhDiem(
        diem_tieu_chi_chung=diem_tcc,
        diem_kpi=diem_kpi,
        diem_tong=diem_tong,
        xep_loai=xep_loai.value,
        so_ngay_lam_viec=so_ngay_lam_viec,
        so_ngay_nghi=so_ngay_nghi,
    )


async def cap_nhat_chi_tiet_tu_du_lieu(
    db: AsyncSession, 
    bao_cao: BaoCaoXepLoai,
    current_user: CongChuc
) -> None:
    """
    Tự động tính và cập nhật chi tiết xếp loại từ dữ liệu đã duyệt.
    
    v1.2 (31/01/2026): FIX MissingGreenlet - load chi_tiets trước khi truy cập
    v1.1 (30/01/2026): Cập nhật thêm so_ngay_lam_viec, so_ngay_nghi
    
    Chỉ chạy khi báo cáo ở trạng thái NHAP (chưa gửi duyệt).
    """
    don_vi_id = bao_cao.don_vi_id
    thang = bao_cao.thang
    nam = bao_cao.nam
    
    # Lấy danh sách CC HIỆN TẠI thuộc đơn vị (loại trừ ADMIN và QLDV)
    # FIX (02/03/2026): Dùng CongChuc.don_vi_id trực tiếp thay vì INNER JOIN DanhGiaThang
    # → CC chưa kê khai/đánh giá vẫn xuất hiện trong báo cáo với điểm 0
    _excluded_roles = [CapBacVaiTro.SUPER_ADMIN, CapBacVaiTro.QUAN_LY_DON_VI]

    # FIX Issue #2 (27/02/2026): Sort theo chức vụ thay vì tên
    # Thứ tự: TDV → QLDV → PDV → CC → TCCB
    SORT_ORDER_CAP_BAC = {
        "CHI_CUC_TRUONG": 1,
        "PHO_CHI_CUC_TRUONG": 2,
        "TRUONG_DON_VI": 3,
        "QUAN_LY_DON_VI": 4,
        "PHO_DON_VI": 5,
        "CONG_CHUC": 6,
        "TCCB": 7,
    }

    stmt_cc = (
        select(CongChuc)
        .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id, isouter=True)
        .options(selectinload(CongChuc.vai_tro))
        .where(
            CongChuc.don_vi_id == don_vi_id,
            CongChuc.is_deleted == False,
            CongChuc.is_active == True,
            or_(
                CongChuc.vai_tro_id == None,
                ~VaiTro.cap_bac.in_(_excluded_roles),
            ),
        )
    )
    result_cc = await db.execute(stmt_cc)
    cong_chucs = list(result_cc.scalars().all())

    # Sort Python-side: chức vụ → họ tên
    cong_chucs.sort(key=lambda cc: (
        SORT_ORDER_CAP_BAC.get(cc.vai_tro.cap_bac.value if cc.vai_tro else "CONG_CHUC", 99),
        cc.ho_ten or ""
    ))
    
    # =========================================================================
    # v1.2 FIX: Load chi_tiets relationship để tránh MissingGreenlet error
    # =========================================================================
    # Lấy chi_tiets từ database thay vì truy cập lazy-loaded attribute
    stmt_chi_tiets = select(ChiTietXepLoai).where(
        ChiTietXepLoai.bao_cao_id == bao_cao.id
    )
    result_chi_tiets = await db.execute(stmt_chi_tiets)
    existing_chi_tiets = result_chi_tiets.scalars().all()
    
    # Map chi tiết hiện có
    existing_map = {ct.cong_chuc_id: ct for ct in existing_chi_tiets}

    # FIX v1.5 (28/02/2026): XÓA chi tiết của CC KHÔNG CÒN trong đơn vị
    # (CC đã chuyển đi sau tháng báo cáo)
    valid_cc_ids = {cc.id for cc in cong_chucs}
    chi_tiet_to_delete = [ct for ct in existing_chi_tiets if ct.cong_chuc_id not in valid_cc_ids]

    if chi_tiet_to_delete:
        for ct in chi_tiet_to_delete:
            await db.delete(ct)

    stats = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}

    for cc in cong_chucs:
        # Xác định loại CC (lãnh đạo hay thường)
        is_lanh_dao = cc.vai_tro and cc.vai_tro.cap_bac in [
            CapBacVaiTro.TRUONG_DON_VI,
            CapBacVaiTro.PHO_DON_VI
        ]
        # Phase 3 (29/04/2026): HĐ 111 dùng form LĐ → công thức 3 chỉ số.
        is_hd_111 = cc.is_hd_111

        # Tính điểm - v1.1: nhận thêm so_ngay_lam_viec, so_ngay_nghi
        if is_lanh_dao:
            ket_qua = await tinh_diem_lanh_dao(db, cc.id, thang, nam)
        elif is_hd_111:
            ket_qua = await tinh_diem_lanh_dao(db, cc.id, thang, nam, is_hd_111=True)
        else:
            ket_qua = await tinh_diem_cong_chuc(db, cc.id, thang, nam)

        # Cập nhật hoặc tạo chi tiết
        if cc.id in existing_map:
            ct = existing_map[cc.id]
            ct.is_lanh_dao = is_lanh_dao  # v1.4: đảm bảo is_lanh_dao luôn đúng
            ct.diem_tieu_chi_chung = _truncate_2dp(ket_qua.diem_tieu_chi_chung)
            ct.diem_kpi = _truncate_2dp(ket_qua.diem_kpi)
            ct.diem_tong = _truncate_2dp(ket_qua.diem_tong)
            # Lưu xep_loai_he_thong cũ để so sánh
            old_xep_loai_he_thong = ct.xep_loai_he_thong
            ct.xep_loai_he_thong = ket_qua.xep_loai
            ct.so_ngay_lam_viec = ket_qua.so_ngay_lam_viec  # v1.1
            ct.so_ngay_nghi = ket_qua.so_ngay_nghi          # v1.1
            # FIX v1.2: Cập nhật xep_loai_de_xuat nếu:
            # - Chưa có giá trị, HOẶC
            # - Đội trưởng chưa chủ động điều chỉnh (de_xuat == he_thong cũ)
            # Điều này đảm bảo khi điểm thay đổi, xếp loại đề xuất cũng cập nhật theo
            if not ct.xep_loai_de_xuat or ct.xep_loai_de_xuat == old_xep_loai_he_thong:
                ct.xep_loai_de_xuat = ket_qua.xep_loai
        else:
            ct = ChiTietXepLoai(
                bao_cao_id=bao_cao.id,
                cong_chuc_id=cc.id,
                is_lanh_dao=is_lanh_dao,  # v1.4
                diem_tieu_chi_chung=_truncate_2dp(ket_qua.diem_tieu_chi_chung),
                diem_kpi=_truncate_2dp(ket_qua.diem_kpi),
                diem_tong=_truncate_2dp(ket_qua.diem_tong),
                xep_loai_he_thong=ket_qua.xep_loai,
                xep_loai_de_xuat=ket_qua.xep_loai,
                so_ngay_lam_viec=ket_qua.so_ngay_lam_viec,  # v1.1
                so_ngay_nghi=ket_qua.so_ngay_nghi,          # v1.1
            )
            db.add(ct)
        
        # Đếm thống kê
        final_xep_loai = ct.xep_loai_de_xuat or ket_qua.xep_loai
        if final_xep_loai in stats:
            stats[final_xep_loai] += 1
    
    # Cập nhật thống kê báo cáo
    bao_cao.tong_cong_chuc = len(cong_chucs)
    bao_cao.so_loai_a = stats["A"]
    bao_cao.so_loai_b = stats["B"]
    bao_cao.so_loai_c = stats["C"]
    bao_cao.so_loai_d = stats["D"]
    bao_cao.so_loai_e = stats["E"]
    
    # Kiểm tra cảnh báo tỷ lệ A
    if stats["B"] > 0 and stats["A"] > stats["B"] * 0.2:
        bao_cao.canh_bao_ty_le_a = True
    else:
        bao_cao.canh_bao_ty_le_a = False
    
    await db.flush()


# =============================================================================
# HELPER FUNCTIONS - TẠO BÁO CÁO
# =============================================================================

async def tao_bao_cao_xep_loai(
    db: AsyncSession,
    don_vi_id: UUID,
    thang: int,
    nam: int,
    nguoi_lap_id: UUID
    
) -> BaoCaoXepLoai:
    """
    Tạo báo cáo xếp loại mới cho đơn vị.

    v1.3 (02/03/2026): Dùng CongChuc.don_vi_id thay vì INNER JOIN DanhGiaThang
        → CC chưa kê khai vẫn xuất hiện với điểm 0
    v1.2 (27/02/2026): Dùng don_vi_id_snapshot từ DanhGiaThang
    v1.1 (30/01/2026): Lưu so_ngay_lam_viec, so_ngay_nghi vào chi tiết

    Logic:
    1. Lấy TẤT CẢ CC active thuộc đơn vị hiện tại
    2. Với mỗi CC, tính điểm (0 nếu chưa kê khai)
    3. Tạo bản ghi bao_cao_xep_loai và chi_tiet_xep_loai
    """
    # Lấy danh sách CC HIỆN TẠI thuộc đơn vị (loại trừ ADMIN và QLDV)
    # FIX (02/03/2026): Dùng CongChuc.don_vi_id trực tiếp thay vì INNER JOIN DanhGiaThang
    # → CC chưa kê khai/đánh giá vẫn xuất hiện trong báo cáo với điểm 0
    _excluded = [CapBacVaiTro.SUPER_ADMIN, CapBacVaiTro.QUAN_LY_DON_VI]

    # FIX Issue #2 (27/02/2026): Sort theo chức vụ thay vì tên
    SORT_ORDER_CAP_BAC = {
        "CHI_CUC_TRUONG": 1,
        "PHO_CHI_CUC_TRUONG": 2,
        "TRUONG_DON_VI": 3,
        "QUAN_LY_DON_VI": 4,
        "PHO_DON_VI": 5,
        "CONG_CHUC": 6,
        "TCCB": 7,
    }

    cc_stmt = (
        select(CongChuc)
        .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id, isouter=True)
        .options(selectinload(CongChuc.vai_tro))
        .where(
            CongChuc.don_vi_id == don_vi_id,
            CongChuc.is_active == True,
            CongChuc.is_deleted == False,
            or_(
                CongChuc.vai_tro_id == None,
                ~VaiTro.cap_bac.in_(_excluded),
            ),
        )
    )
    cc_result = await db.execute(cc_stmt)
    cong_chucs = list(cc_result.scalars().all())

    # Sort Python-side: chức vụ → họ tên
    cong_chucs.sort(key=lambda cc: (
        SORT_ORDER_CAP_BAC.get(cc.vai_tro.cap_bac.value if cc.vai_tro else "CONG_CHUC", 99),
        cc.ho_ten or ""
    ))

    # Tạo báo cáo
    bao_cao = BaoCaoXepLoai(
        don_vi_id=don_vi_id,
        thang=thang,
        nam=nam,
        nguoi_lap_id=nguoi_lap_id,
        trang_thai=TrangThaiBaoCao.NHAP.value,
        tong_cong_chuc=len(cong_chucs),
    )
    db.add(bao_cao)
    await db.flush()
    
    # Tạo chi tiết cho từng CC
    stats = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}

    for cc in cong_chucs:
        # Xác định loại CC (lãnh đạo hay thường) - nhất quán với cap_nhat_chi_tiet
        is_lanh_dao = cc.vai_tro and cc.vai_tro.cap_bac in [
            CapBacVaiTro.TRUONG_DON_VI,
            CapBacVaiTro.PHO_DON_VI
        ]
        # Phase 3 (29/04/2026): HĐ 111 dùng form LĐ → công thức 3 chỉ số.
        is_hd_111 = cc.is_hd_111

        if is_lanh_dao:
            ket_qua = await tinh_diem_lanh_dao(db, cc.id, thang, nam)
        elif is_hd_111:
            ket_qua = await tinh_diem_lanh_dao(db, cc.id, thang, nam, is_hd_111=True)
        else:
            ket_qua = await tinh_diem_cong_chuc(db, cc.id, thang, nam)

        chi_tiet = ChiTietXepLoai(
            bao_cao_id=bao_cao.id,
            cong_chuc_id=cc.id,
            is_lanh_dao=is_lanh_dao,
            diem_tieu_chi_chung=_truncate_2dp(ket_qua.diem_tieu_chi_chung),
            diem_kpi=_truncate_2dp(ket_qua.diem_kpi),
            diem_tong=_truncate_2dp(ket_qua.diem_tong),
            xep_loai_he_thong=ket_qua.xep_loai,
            xep_loai_de_xuat=ket_qua.xep_loai,
            so_ngay_lam_viec=ket_qua.so_ngay_lam_viec,  # v1.1
            so_ngay_nghi=ket_qua.so_ngay_nghi,          # v1.1
        )
        db.add(chi_tiet)
        
        if ket_qua.xep_loai in stats:
            stats[ket_qua.xep_loai] += 1
    
    # Cập nhật thống kê
    bao_cao.so_loai_a = stats["A"]
    bao_cao.so_loai_b = stats["B"]
    bao_cao.so_loai_c = stats["C"]
    bao_cao.so_loai_d = stats["D"]
    bao_cao.so_loai_e = stats["E"]
    
    # Kiểm tra tỷ lệ A
    if stats["B"] > 0 and stats["A"] > 0.2 * stats["B"]:
        bao_cao.canh_bao_ty_le_a = True
    elif stats["B"] == 0 and stats["A"] > 0:
        bao_cao.canh_bao_ty_le_a = True
    
    await db.flush()
    return bao_cao


async def cap_nhat_thong_ke_bao_cao(db: AsyncSession, bao_cao: BaoCaoXepLoai) -> dict:
    """
    Cập nhật thống kê báo cáo từ danh sách chi tiết.
    
    v1.2 (31/01/2026): FIX MissingGreenlet - load chi_tiets trước khi truy cập
    """
    stats = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    
    # =========================================================================
    # v1.2 FIX: Load chi_tiets từ database để tránh MissingGreenlet
    # =========================================================================
    stmt_chi_tiets = select(ChiTietXepLoai).where(
        ChiTietXepLoai.bao_cao_id == bao_cao.id
    )
    result_chi_tiets = await db.execute(stmt_chi_tiets)
    chi_tiets = result_chi_tiets.scalars().all()
    
    for ct in chi_tiets:
        xep_loai = ct.xep_loai_quyet_dinh or ct.xep_loai_de_xuat or ct.xep_loai_he_thong
        if xep_loai in stats:
            stats[xep_loai] += 1
    
    bao_cao.tong_cong_chuc = len(chi_tiets)
    bao_cao.so_loai_a = stats["A"]
    bao_cao.so_loai_b = stats["B"]
    bao_cao.so_loai_c = stats["C"]
    bao_cao.so_loai_d = stats["D"]
    bao_cao.so_loai_e = stats["E"]
    
    # Kiểm tra tỷ lệ A
    if stats["B"] > 0:
        bao_cao.canh_bao_ty_le_a = stats["A"] > 0.2 * stats["B"]
    else:
        bao_cao.canh_bao_ty_le_a = stats["A"] > 0
    
    return stats


# =============================================================================
# HELPER FUNCTIONS - BUILD RESPONSE (v1.1 - Thêm so_ngay_lam_viec, so_ngay_nghi)
# =============================================================================

def build_chi_tiet_response(ct: ChiTietXepLoai) -> dict:
    """
    Build response dict từ ChiTietXepLoai.
    
    v1.1 (30/01/2026): Thêm so_ngay_lam_viec, so_ngay_nghi
    """
    response = {
        "id": ct.id,
        "cong_chuc_id": ct.cong_chuc_id,
        "cong_chuc": None,
        "is_lanh_dao": ct.is_lanh_dao,
        # Phase 3 (29/04/2026): HĐ 111 — kê khai form LĐ, không có d/đ/e.
        # Suy ra từ vai_tro của CC (joined load) thay vì lưu cột riêng.
        "is_hd_111": ct.cong_chuc.is_hd_111 if ct.cong_chuc else False,
        # v1.1: Thêm số ngày làm việc và nghỉ
        "so_ngay_lam_viec": float(ct.so_ngay_lam_viec) if ct.so_ngay_lam_viec is not None else None,
        "so_ngay_nghi": float(ct.so_ngay_nghi) if ct.so_ngay_nghi is not None else None,
        # Điểm
        "diem_tieu_chi_chung": float(ct.diem_tieu_chi_chung) if ct.diem_tieu_chi_chung else 0,
        "diem_kpi": float(ct.diem_kpi) if ct.diem_kpi else 0,
        "diem_tong": float(ct.diem_tong) if ct.diem_tong else 0,
        # Xếp loại
        "xep_loai_he_thong": ct.xep_loai_he_thong,
        "xep_loai_de_xuat": ct.xep_loai_de_xuat,
        "ly_do_dieu_chinh_dt": ct.ly_do_dieu_chinh_dt,
        "xep_loai_quyet_dinh": ct.xep_loai_quyet_dinh,
        "ly_do_dieu_chinh_cct": ct.ly_do_dieu_chinh_cct,
        "bi_tu_choi": ct.bi_tu_choi,
        "ly_do_tu_choi": ct.ly_do_tu_choi,
        "ghi_chu": ct.ghi_chu,
    }
    
    if ct.cong_chuc:
        response["cong_chuc"] = {
            "id": ct.cong_chuc.id,
            "ma_cc": ct.cong_chuc.ma_cc,
            "ho_ten": ct.cong_chuc.ho_ten,
            "chuc_vu": ct.cong_chuc.chuc_vu,
        }
    
    return response


def build_bao_cao_response(bc: BaoCaoXepLoai, include_chi_tiet: bool = True) -> dict:
    """Build response dict từ BaoCaoXepLoai."""
    response = {
        "id": bc.id,
        "don_vi_id": bc.don_vi_id,
        "don_vi": None,
        "thang": bc.thang,
        "nam": bc.nam,
        "nguoi_lap_id": bc.nguoi_lap_id,
        "nguoi_lap": None,
        "ngay_lap": bc.ngay_lap,
        "ngay_gui_duyet": bc.ngay_gui_duyet,
        "trang_thai": bc.trang_thai,
        "trang_thai_ten": get_trang_thai_ten(bc.trang_thai),
        "nguoi_phe_duyet_id": bc.nguoi_phe_duyet_id,
        "nguoi_phe_duyet": None,
        "ngay_phe_duyet": bc.ngay_phe_duyet,
        "y_kien_phe_duyet": bc.y_kien_phe_duyet,
        "tong_cong_chuc": bc.tong_cong_chuc,
        "so_loai_a": bc.so_loai_a,
        "so_loai_b": bc.so_loai_b,
        "so_loai_c": bc.so_loai_c,
        "so_loai_d": bc.so_loai_d,
        "so_loai_e": bc.so_loai_e,
        "canh_bao_ty_le_a": bc.canh_bao_ty_le_a,
        "chi_tiet": [],
        "created_at": bc.created_at,
        "updated_at": bc.updated_at,
    }
    
    if bc.don_vi:
        response["don_vi"] = {
            "id": bc.don_vi.id,
            "ma_don_vi": bc.don_vi.ma_don_vi,
            "ten_don_vi": bc.don_vi.ten_don_vi,
        }
    
    if bc.nguoi_lap:
        response["nguoi_lap"] = {
            "id": bc.nguoi_lap.id,
            "ma_cc": bc.nguoi_lap.ma_cc,
            "ho_ten": bc.nguoi_lap.ho_ten,
            "chuc_vu": bc.nguoi_lap.chuc_vu,
        }
    
    if bc.nguoi_phe_duyet:
        response["nguoi_phe_duyet"] = {
            "id": bc.nguoi_phe_duyet.id,
            "ma_cc": bc.nguoi_phe_duyet.ma_cc,
            "ho_ten": bc.nguoi_phe_duyet.ho_ten,
            "chuc_vu": bc.nguoi_phe_duyet.chuc_vu,
        }
    
    if include_chi_tiet and bc.chi_tiets:
        response["chi_tiet"] = [build_chi_tiet_response(ct) for ct in bc.chi_tiets]
    
    return response


async def get_bao_cao_full(db: AsyncSession, bao_cao_id: UUID) -> Optional[BaoCaoXepLoai]:
    """Lấy báo cáo kèm đầy đủ relationships."""
    stmt = (
        select(BaoCaoXepLoai)
        .options(
            selectinload(BaoCaoXepLoai.don_vi),
            selectinload(BaoCaoXepLoai.nguoi_lap),
            selectinload(BaoCaoXepLoai.nguoi_phe_duyet),
            selectinload(BaoCaoXepLoai.chi_tiets).selectinload(ChiTietXepLoai.cong_chuc),
        )
        .where(BaoCaoXepLoai.id == bao_cao_id, BaoCaoXepLoai.is_deleted == False)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def enrich_chi_tiet_with_cv_c3(
    db: AsyncSession,
    response_data: dict,
    thang: int,
    nam: int,
) -> None:
    """
    Bổ sung so_cv_c3_plus (số công việc C3+) cho từng chi_tiet trong response.
    
    Batch-query tất cả kê khai ĐÃ DUYỆT trong tháng, group by cong_chuc_id,
    đếm những kê khai có cap_do.ma_cap_do IN ('C3', 'C4', 'C5').
    
    v1.4 (10/02/2026): Thêm để hỗ trợ lãnh đạo đề xuất xếp loại.
    """
    from app.models.kpi_submission import KeKhaiCongViec, TrangThaiKeKhai
    from app.models.task_catalog import CapDoPhucTap
    
    chi_tiet_list = response_data.get("chi_tiet", [])
    if not chi_tiet_list:
        return
    
    # Lấy tất cả cong_chuc_id từ chi_tiet
    cc_ids = [ct["cong_chuc_id"] for ct in chi_tiet_list if ct.get("cong_chuc_id")]
    if not cc_ids:
        return
    
    # Batch query: đếm kê khai C3+ cho tất cả CC trong 1 query
    stmt = (
        select(
            KeKhaiCongViec.cong_chuc_id,
            func.count(KeKhaiCongViec.id).label("so_cv_c3_plus"),
        )
        .join(CapDoPhucTap, KeKhaiCongViec.cap_do_id == CapDoPhucTap.id)
        .where(
            KeKhaiCongViec.cong_chuc_id.in_(cc_ids),
            KeKhaiCongViec.thang == thang,
            KeKhaiCongViec.nam == nam,
            KeKhaiCongViec.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET,
            KeKhaiCongViec.is_deleted == False,
            CapDoPhucTap.ma_cap_do.in_(["C3", "C4", "C5"]),
        )
        .group_by(KeKhaiCongViec.cong_chuc_id)
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    # Build map: cong_chuc_id → count
    c3_map = {str(row.cong_chuc_id): row.so_cv_c3_plus for row in rows}
    
    # Inject vào từng chi_tiet
    for ct in chi_tiet_list:
        cc_id = str(ct.get("cong_chuc_id", ""))
        ct["so_cv_c3_plus"] = c3_map.get(cc_id, 0)


# =============================================================================
# 1. GET /don-vi/thang/{thang}/nam/{nam} - Lấy/Tạo báo cáo đơn vị
# =============================================================================

@router.get("/don-vi/thang/{thang}/nam/{nam}")
async def get_bao_cao_don_vi(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int,
    nam: int,
) -> dict:
    """
    Lấy báo cáo xếp loại của đơn vị - TỰ ĐỘNG TÍNH từ dữ liệu đã duyệt.
    
    Logic:
    1. Nếu chưa có record BaoCaoXepLoai → tự động tạo mới (trạng thái NHAP)
    2. Luôn tính lại điểm từ dữ liệu đã duyệt (công việc, tiêu chí, nghỉ phép, d,đ,e)
    3. Cập nhật ChiTietXepLoai với điểm mới nhất
    
    Quyền XEM: Phó ĐT, ĐT, Phó CCT, CCT (báo cáo đơn vị mình)
    Quyền SỬA: Chỉ ĐT (điều chỉnh đề xuất, gửi duyệt)
    """
    # Kiểm tra quyền XEM
    if not check_can_view_bao_cao(current_user):
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_003", message="Bạn không có quyền xem báo cáo xếp loại"
        ))
    
    # Xác định quyền
    can_edit = check_can_edit_bao_cao(current_user)
    can_approve = check_can_approve_bao_cao(current_user)
    
    # Validate params
    if thang < 1 or thang > 12:
        raise HTTPException(status_code=400, detail=error_response(
            code="VAL_001", message="Tháng phải từ 1-12"
        ))
    if nam < 2025:
        raise HTTPException(status_code=400, detail=error_response(
            code="VAL_002", message="Năm phải >= 2025"
        ))
    
    don_vi_id = current_user.don_vi_id
    
    # =========================================================================
    # BƯỚC 1: Tìm hoặc tạo BaoCaoXepLoai
    # =========================================================================
    existing_stmt = (
        select(BaoCaoXepLoai)
        .options(
            selectinload(BaoCaoXepLoai.don_vi),
            selectinload(BaoCaoXepLoai.nguoi_lap),
            selectinload(BaoCaoXepLoai.nguoi_phe_duyet),
            selectinload(BaoCaoXepLoai.chi_tiets).selectinload(ChiTietXepLoai.cong_chuc),
        )
        .where(
            BaoCaoXepLoai.don_vi_id == don_vi_id,
            BaoCaoXepLoai.thang == thang,
            BaoCaoXepLoai.nam == nam,
            BaoCaoXepLoai.is_deleted == False,
        )
    )
    existing_result = await db.execute(existing_stmt)
    bao_cao = existing_result.scalar_one_or_none()
    
    is_new = False
    if not bao_cao:
        # Tự động tạo mới với trạng thái NHAP
        bao_cao = BaoCaoXepLoai(
            don_vi_id=don_vi_id,
            thang=thang,
            nam=nam,
            trang_thai=TrangThaiBaoCao.NHAP.value,
            nguoi_lap_id=current_user.id,
            ngay_lap=datetime.utcnow(),
        )
        db.add(bao_cao)
        await db.flush()
        is_new = True
    
    # =========================================================================
    # BƯỚC 2: Nếu báo cáo chưa bị khóa (NHAP) → tính lại điểm từ dữ liệu mới nhất
    # =========================================================================
    if bao_cao.trang_thai in [TrangThaiBaoCao.NHAP.value, 'CHO_PHE_DUYET', 'TRA_LAI', 'TU_CHOI']:
        await cap_nhat_chi_tiet_tu_du_lieu(db, bao_cao, current_user)
    
    # =========================================================================
    # BƯỚC 3: Load lại và trả response
    # =========================================================================
    await db.refresh(bao_cao)
    
    # Load relationships
    reload_stmt = (
        select(BaoCaoXepLoai)
        .options(
            selectinload(BaoCaoXepLoai.don_vi),
            selectinload(BaoCaoXepLoai.nguoi_lap),
            selectinload(BaoCaoXepLoai.nguoi_phe_duyet),
            selectinload(BaoCaoXepLoai.chi_tiets).selectinload(ChiTietXepLoai.cong_chuc),
        )
        .where(BaoCaoXepLoai.id == bao_cao.id)
    )
    reload_result = await db.execute(reload_stmt)
    bao_cao = reload_result.scalar_one()
    
    response_data = build_bao_cao_response(bao_cao)
    response_data["can_edit"] = can_edit
    response_data["can_approve"] = can_approve
    response_data["is_auto_calculated"] = True
    
    # v1.4: Bổ sung số CV C3+ cho từng CC
    await enrich_chi_tiet_with_cv_c3(db, response_data, thang, nam)
    
    return success_response(
        data=response_data,
        message=f"{'Tạo mới' if is_new else 'Lấy'} báo cáo tháng {thang}/{nam} thành công"
    )


# =============================================================================
# 2. PUT /chi-tiet/{id}/de-xuat - Đội trưởng điều chỉnh xếp loại
# =============================================================================

@router.put("/chi-tiet/{chi_tiet_id}/de-xuat")
async def de_xuat_xep_loai(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    chi_tiet_id: UUID,
    payload: DeXuatXepLoaiRequest,
) -> dict:
    """
    Đội trưởng điều chỉnh xếp loại đề xuất cho 1 CC.
    
    Validation:
    - Nếu xep_loai_de_xuat != xep_loai_he_thong → ly_do_dieu_chinh BẮT BUỘC
    - Báo cáo phải ở trạng thái NHAP hoặc TU_CHOI
    """
    # Lấy chi tiết kèm báo cáo
    stmt = (
        select(ChiTietXepLoai)
        .options(
            selectinload(ChiTietXepLoai.bao_cao),
            selectinload(ChiTietXepLoai.cong_chuc),
        )
        .where(ChiTietXepLoai.id == chi_tiet_id)
    )
    result = await db.execute(stmt)
    chi_tiet = result.scalar_one_or_none()
    
    if not chi_tiet:
        raise HTTPException(status_code=404, detail=error_response(
            code="NOT_FOUND", message="Không tìm thấy chi tiết xếp loại"
        ))
    
    # Kiểm tra quyền: phải là Đội trưởng của đơn vị này
    is_tdv = check_is_truong_don_vi(current_user)
    is_cct = check_is_chi_cuc_truong(current_user)
    
    if not (is_tdv or is_cct):
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_003", message="Chỉ Trưởng đơn vị hoặc CCT mới có quyền điều chỉnh"
        ))
    
    if chi_tiet.bao_cao.don_vi_id != current_user.don_vi_id:
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_004", message="Bạn không có quyền điều chỉnh báo cáo của đơn vị khác"
        ))
    
    # Kiểm tra trạng thái báo cáo
    if chi_tiet.bao_cao.trang_thai not in [TrangThaiBaoCao.NHAP.value, TrangThaiBaoCao.TU_CHOI.value]:
        raise HTTPException(status_code=400, detail=error_response(
            code="BIZ_001", message=f"Không thể điều chỉnh ở trạng thái {chi_tiet.bao_cao.trang_thai}"
        ))
    
    # Validation: Nếu khác hệ thống → bắt buộc lý do
    if payload.xep_loai_de_xuat.value != chi_tiet.xep_loai_he_thong:
        if not payload.ly_do_dieu_chinh or len(payload.ly_do_dieu_chinh.strip()) == 0:
            raise HTTPException(status_code=400, detail=error_response(
                code="VAL_003", message="Phải nhập lý do khi điều chỉnh xếp loại khác hệ thống"
            ))
    
    # Cập nhật
    chi_tiet.xep_loai_de_xuat = payload.xep_loai_de_xuat.value
    chi_tiet.ly_do_dieu_chinh_dt = payload.ly_do_dieu_chinh
    chi_tiet.ghi_chu = payload.ghi_chu
    chi_tiet.bi_tu_choi = False  # Reset nếu đã sửa
    chi_tiet.ly_do_tu_choi = None
    
    await db.flush()
    await db.refresh(chi_tiet)
    
    return success_response(
        data=build_chi_tiet_response(chi_tiet),
        message="Cập nhật xếp loại đề xuất thành công"
    )


# =============================================================================
# 3. POST /{id}/gui-duyet - Gửi báo cáo lên CCT
# =============================================================================

@router.post("/{bao_cao_id}/gui-duyet")
async def gui_duyet_bao_cao(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    bao_cao_id: UUID,
) -> dict:
    """
    Đội trưởng gửi báo cáo lên CCT phê duyệt.
    
    Logic:
    - Với mỗi chi tiết: nếu xep_loai_de_xuat = null → gán = xep_loai_he_thong
    - Cập nhật trạng thái = CHO_PHE_DUYET
    """
    if not check_is_truong_don_vi(current_user):
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_003", message="Chỉ Trưởng đơn vị mới có quyền gửi phê duyệt"
        ))
    
    bao_cao = await get_bao_cao_full(db, bao_cao_id)
    
    if not bao_cao:
        raise HTTPException(status_code=404, detail=error_response(
            code="NOT_FOUND", message="Không tìm thấy báo cáo"
        ))
    
    if bao_cao.don_vi_id != current_user.don_vi_id:
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_004", message="Bạn không có quyền gửi báo cáo của đơn vị khác"
        ))
    
    if bao_cao.trang_thai not in [TrangThaiBaoCao.NHAP.value, TrangThaiBaoCao.TU_CHOI.value]:
        raise HTTPException(status_code=400, detail=error_response(
            code="BIZ_001", message=f"Không thể gửi duyệt ở trạng thái {bao_cao.trang_thai}"
        ))
    
    # Gán xep_loai_de_xuat = xep_loai_he_thong nếu chưa có
    for ct in bao_cao.chi_tiets:
        if not ct.xep_loai_de_xuat:
            ct.xep_loai_de_xuat = ct.xep_loai_he_thong
    
    # Cập nhật thống kê
    await cap_nhat_thong_ke_bao_cao(db, bao_cao)
    
    # Cập nhật trạng thái
    bao_cao.trang_thai = TrangThaiBaoCao.CHO_PHE_DUYET.value
    bao_cao.ngay_gui_duyet = datetime.utcnow()
    
    await db.flush()
    
    return success_response(
        data={
            "id": bao_cao.id,
            "trang_thai": bao_cao.trang_thai,
            "ngay_gui_duyet": bao_cao.ngay_gui_duyet,
        },
        message="Gửi báo cáo phê duyệt thành công"
    )


# =============================================================================
# 4. GET /cho-phe-duyet - DS báo cáo chờ phê duyệt (CCT)
# =============================================================================

@router.get("/cho-phe-duyet")
async def get_bao_cao_cho_phe_duyet(
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Lấy danh sách báo cáo chờ phê duyệt (CCT).
    
    ⚠️ KHÔNG có params thang/nam - lấy tất cả báo cáo CHO_PHE_DUYET
    """
    has_view_all = getattr(current_user, 'can_view_all_units', False)
    if not check_is_chi_cuc_truong(current_user) and not has_view_all:
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_003", message="Chỉ Chi cục trưởng mới có quyền xem danh sách chờ phê duyệt"
        ))
    
    stmt = (
        select(BaoCaoXepLoai)
        .options(
            selectinload(BaoCaoXepLoai.don_vi),
            selectinload(BaoCaoXepLoai.nguoi_lap),
        )
        .where(
            BaoCaoXepLoai.trang_thai == TrangThaiBaoCao.CHO_PHE_DUYET.value,
            BaoCaoXepLoai.is_deleted == False,
        )
        .order_by(BaoCaoXepLoai.ngay_gui_duyet.desc())
    )
    result = await db.execute(stmt)
    bao_caos = result.scalars().all()
    
    return success_response(
        data=[build_bao_cao_response(bc, include_chi_tiet=False) for bc in bao_caos],
        message=f"Có {len(bao_caos)} báo cáo chờ phê duyệt"
    )



# =============================================================================
# 4b. GET /danh-sach/thang/{thang}/nam/{nam} - DS báo cáo toàn Chi cục (CCT)
# =============================================================================

@router.get("/danh-sach/thang/{thang}/nam/{nam}")
async def get_danh_sach_bao_cao(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int,
    nam: int,
    trang_thai: Optional[str] = Query(None, description="Filter: CHO_PHE_DUYET, DA_PHE_DUYET, TU_CHOI"),
) -> dict:
    """
    Danh sách báo cáo xếp loại toàn Chi cục theo tháng/năm.
    
    Quyền: CCT
    Query params:
    - trang_thai: filter theo trạng thái (không truyền = tất cả trừ NHAP)
    """
    has_view_all = getattr(current_user, 'can_view_all_units', False)
    if not check_is_chi_cuc_truong(current_user) and not has_view_all:
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_003", message="Chỉ Chi cục trưởng mới có quyền xem danh sách báo cáo"
        ))
    
    conditions = [
        BaoCaoXepLoai.thang == thang,
        BaoCaoXepLoai.nam == nam,
        BaoCaoXepLoai.is_deleted == False,
    ]
    
    if trang_thai:
        conditions.append(BaoCaoXepLoai.trang_thai == trang_thai)
    else:
        # v1.1.0: CCT và user có can_view_all_units xem được cả NHAP
        has_view_all = getattr(current_user, 'can_view_all_units', False)
        if check_is_chi_cuc_truong(current_user) or has_view_all:
            # Xem tất cả trạng thái (bao gồm NHAP)
            pass  # Không filter trạng thái
        else:
            # Mặc định: tất cả trừ NHAP (chỉ hiện báo cáo đã gửi)
            conditions.append(
                BaoCaoXepLoai.trang_thai.in_([
                    TrangThaiBaoCao.CHO_PHE_DUYET.value,
                    TrangThaiBaoCao.DA_PHE_DUYET.value,
                    TrangThaiBaoCao.TU_CHOI.value,
                ])
            )
    
    stmt = (
        select(BaoCaoXepLoai)
        .options(
            selectinload(BaoCaoXepLoai.don_vi),
            selectinload(BaoCaoXepLoai.nguoi_lap),
        )
        .where(*conditions)
        .order_by(BaoCaoXepLoai.ngay_gui_duyet.desc().nulls_last())
    )
    result = await db.execute(stmt)
    bao_caos = result.scalars().all()
    
    # Đếm theo trạng thái (lấy tất cả báo cáo tháng này để đếm chính xác)
    count_stmt = (
        select(BaoCaoXepLoai.trang_thai, func.count())
        .where(
            BaoCaoXepLoai.thang == thang,
            BaoCaoXepLoai.nam == nam,
            BaoCaoXepLoai.is_deleted == False,
            BaoCaoXepLoai.trang_thai.in_([
                TrangThaiBaoCao.CHO_PHE_DUYET.value,
                TrangThaiBaoCao.DA_PHE_DUYET.value,
                TrangThaiBaoCao.TU_CHOI.value,
            ])
        )
        .group_by(BaoCaoXepLoai.trang_thai)
    )
    count_result = await db.execute(count_stmt)
    counts = {"CHO_PHE_DUYET": 0, "DA_PHE_DUYET": 0, "TU_CHOI": 0}
    for row in count_result:
        counts[row[0]] = row[1]
    
    return success_response(
        data={
            "danh_sach": [build_bao_cao_response(bc, include_chi_tiet=False) for bc in bao_caos],
            "tong_so": len(bao_caos),
            "thong_ke_trang_thai": counts,
        },
        message=f"Có {len(bao_caos)} báo cáo tháng {thang}/{nam}"
    )

# =============================================================================
# 5. GET /{id} - Chi tiết báo cáo
# =============================================================================

@router.get("/{bao_cao_id}")
async def get_bao_cao_chi_tiet(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    bao_cao_id: UUID,
) -> dict:
    """
    Lấy chi tiết báo cáo theo ID.
    
    v1.1: 
    - Phó ĐT, ĐT xem báo cáo đơn vị mình
    - Phó CCT, CCT xem tất cả báo cáo
    """
    if not check_can_view_bao_cao(current_user):
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_003", message="Bạn không có quyền xem báo cáo"
        ))
    
    bao_cao = await get_bao_cao_full(db, bao_cao_id)
    
    if not bao_cao:
        raise HTTPException(status_code=404, detail=error_response(
            code="NOT_FOUND", message="Không tìm thấy báo cáo"
        ))
    
    # Kiểm tra quyền: Lãnh đạo Chi cục xem tất cả, Lãnh đạo đơn vị chỉ xem đơn vị mình
    is_lanh_dao_cc = check_is_lanh_dao_chi_cuc(current_user)
    has_view_all = getattr(current_user, 'can_view_all_units', False)
    if not is_lanh_dao_cc and not has_view_all and bao_cao.don_vi_id != current_user.don_vi_id:
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_004", message="Bạn không có quyền xem báo cáo của đơn vị khác"
        ))
    
    response_data = build_bao_cao_response(bao_cao)
    response_data["can_edit"] = check_can_edit_bao_cao(current_user)
    response_data["can_approve"] = check_can_approve_bao_cao(current_user)
    
    # v1.4: Bổ sung số CV C3+ cho từng CC
    await enrich_chi_tiet_with_cv_c3(db, response_data, bao_cao.thang, bao_cao.nam)
    
    return success_response(
        data=response_data,
        message="Lấy chi tiết báo cáo thành công"
    )


# =============================================================================
# 6. PUT /chi-tiet/{id}/quyet-dinh - CCT điều chỉnh xếp loại quyết định
# =============================================================================

@router.put("/chi-tiet/{chi_tiet_id}/quyet-dinh")
async def quyet_dinh_xep_loai(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    chi_tiet_id: UUID,
    payload: QuyetDinhXepLoaiRequest,
) -> dict:
    """
    CCT điều chỉnh xếp loại quyết định cho 1 CC.
    
    Validation:
    - Nếu xep_loai_quyet_dinh != xep_loai_de_xuat → ly_do_dieu_chinh BẮT BUỘC
    - Báo cáo phải ở trạng thái CHO_PHE_DUYET
    """
    if not check_is_chi_cuc_truong(current_user):
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_003", message="Chỉ Chi cục trưởng mới có quyền quyết định xếp loại"
        ))
    
    # Lấy chi tiết
    stmt = (
        select(ChiTietXepLoai)
        .options(
            selectinload(ChiTietXepLoai.bao_cao),
            selectinload(ChiTietXepLoai.cong_chuc),
        )
        .where(ChiTietXepLoai.id == chi_tiet_id)
    )
    result = await db.execute(stmt)
    chi_tiet = result.scalar_one_or_none()
    
    if not chi_tiet:
        raise HTTPException(status_code=404, detail=error_response(
            code="NOT_FOUND", message="Không tìm thấy chi tiết xếp loại"
        ))
    
    # Kiểm tra trạng thái báo cáo
    if chi_tiet.bao_cao.trang_thai != TrangThaiBaoCao.CHO_PHE_DUYET.value:
        raise HTTPException(status_code=400, detail=error_response(
            code="BIZ_001", message=f"Chỉ điều chỉnh được khi báo cáo ở trạng thái CHO_PHE_DUYET"
        ))
    
    # Validation: Nếu khác đề xuất → bắt buộc lý do
    xep_loai_de_xuat = chi_tiet.xep_loai_de_xuat or chi_tiet.xep_loai_he_thong
    if payload.xep_loai_quyet_dinh.value != xep_loai_de_xuat:
        if not payload.ly_do_dieu_chinh or len(payload.ly_do_dieu_chinh.strip()) == 0:
            raise HTTPException(status_code=400, detail=error_response(
                code="VAL_003", message="Phải nhập lý do khi điều chỉnh xếp loại khác đề xuất"
            ))
    
    # Cập nhật
    chi_tiet.xep_loai_quyet_dinh = payload.xep_loai_quyet_dinh.value
    chi_tiet.ly_do_dieu_chinh_cct = payload.ly_do_dieu_chinh
    
    await db.flush()
    await db.refresh(chi_tiet)
    
    return success_response(
        data=build_chi_tiet_response(chi_tiet),
        message="Cập nhật xếp loại quyết định thành công"
    )


# =============================================================================
# HELPER: Mở khóa dữ liệu kê khai/đánh giá/nghỉ phép khi từ chối hoặc trả lại
# =============================================================================

async def _mo_khoa_du_lieu_don_vi(db: AsyncSession, thang: int, nam: int, don_vi_id: UUID) -> dict:
    """
    Mở khóa is_khoa cho DanhGiaThang, KeKhaiCongViec, DangKyNghi
    của đơn vị trong tháng/năm cụ thể.

    Được gọi khi CCT từ chối hoặc trả lại báo cáo xếp loại.
    """
    # Mở khóa DanhGiaThang
    stmt_dg = select(DanhGiaThang).where(
        DanhGiaThang.thang == thang,
        DanhGiaThang.nam == nam,
        DanhGiaThang.don_vi_id_snapshot == don_vi_id,
        DanhGiaThang.is_deleted == False,
        DanhGiaThang.is_khoa == True,
    )
    result_dg = await db.execute(stmt_dg)
    count_dg = 0
    for dg in result_dg.scalars().all():
        dg.is_khoa = False
        count_dg += 1

    # Mở khóa KeKhaiCongViec
    stmt_kk = select(KeKhaiCongViec).where(
        KeKhaiCongViec.thang == thang,
        KeKhaiCongViec.nam == nam,
        KeKhaiCongViec.don_vi_id_snapshot == don_vi_id,
        KeKhaiCongViec.is_deleted == False,
        KeKhaiCongViec.is_khoa == True,
    )
    result_kk = await db.execute(stmt_kk)
    count_kk = 0
    for kk in result_kk.scalars().all():
        kk.is_khoa = False
        count_kk += 1

    # Mở khóa DangKyNghi
    stmt_np = (
        select(DangKyNghi)
        .join(CongChuc, DangKyNghi.cong_chuc_id == CongChuc.id)
        .where(
            DangKyNghi.thang_ap_dung == thang,
            DangKyNghi.nam_ap_dung == nam,
            CongChuc.don_vi_id == don_vi_id,
            DangKyNghi.is_deleted == False,
            DangKyNghi.is_khoa == True,
        )
    )
    result_np = await db.execute(stmt_np)
    count_np = 0
    for np in result_np.scalars().all():
        np.is_khoa = False
        count_np += 1

    return {
        "so_danh_gia_mo_khoa": count_dg,
        "so_ke_khai_mo_khoa": count_kk,
        "so_nghi_phep_mo_khoa": count_np,
    }


# =============================================================================
# 7. POST /{id}/phe-duyet - CCT phê duyệt/từ chối
# =============================================================================

@router.post("/{bao_cao_id}/phe-duyet")
async def phe_duyet_bao_cao(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    bao_cao_id: UUID,
    payload: PheDuyetBaoCaoRequest,
) -> dict:
    """
    CCT phê duyệt hoặc từ chối báo cáo.
    
    Logic APPROVE:
    - Với mỗi chi tiết: nếu xep_loai_quyet_dinh = null → gán = xep_loai_de_xuat
    - Cập nhật trạng thái = DA_PHE_DUYET (khóa)
    
    Logic REJECT:
    - Cập nhật trạng thái = TU_CHOI
    - Với mỗi chi_tiet_tu_choi: cập nhật bi_tu_choi = true
    """
    if not check_is_chi_cuc_truong(current_user):
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_003", message="Chỉ Chi cục trưởng mới có quyền phê duyệt"
        ))
    
    bao_cao = await get_bao_cao_full(db, bao_cao_id)
    
    if not bao_cao:
        raise HTTPException(status_code=404, detail=error_response(
            code="NOT_FOUND", message="Không tìm thấy báo cáo"
        ))
    
    if bao_cao.trang_thai != TrangThaiBaoCao.CHO_PHE_DUYET.value:
        raise HTTPException(status_code=400, detail=error_response(
            code="BIZ_001", message=f"Chỉ phê duyệt được khi báo cáo ở trạng thái CHO_PHE_DUYET"
        ))
    
    now = datetime.utcnow()
    so_cc_bi_tu_choi = 0
    
    if payload.action == "APPROVE":
        # Gán xep_loai_quyet_dinh = xep_loai_de_xuat nếu chưa có
        for ct in bao_cao.chi_tiets:
            if not ct.xep_loai_quyet_dinh:
                ct.xep_loai_quyet_dinh = ct.xep_loai_de_xuat or ct.xep_loai_he_thong
        
        # Cập nhật thống kê
        await cap_nhat_thong_ke_bao_cao(db, bao_cao)
        
        # Cập nhật trạng thái
        bao_cao.trang_thai = TrangThaiBaoCao.DA_PHE_DUYET.value
        bao_cao.nguoi_phe_duyet_id = current_user.id
        bao_cao.ngay_phe_duyet = now
        bao_cao.y_kien_phe_duyet = payload.y_kien
        
        message = "Phê duyệt báo cáo thành công"
        
    else:  # REJECT
        # Cập nhật trạng thái
        bao_cao.trang_thai = TrangThaiBaoCao.TU_CHOI.value
        bao_cao.y_kien_phe_duyet = payload.y_kien

        # Đánh dấu các CC bị từ chối
        if payload.chi_tiet_tu_choi:
            chi_tiet_ids = {item.chi_tiet_id: item.ly_do for item in payload.chi_tiet_tu_choi}
            for ct in bao_cao.chi_tiets:
                if ct.id in chi_tiet_ids:
                    ct.bi_tu_choi = True
                    ct.ly_do_tu_choi = chi_tiet_ids[ct.id]
                    so_cc_bi_tu_choi += 1

        # FIX: Mở khóa dữ liệu khi từ chối để CC có thể chỉnh sửa lại
        unlock_result = await _mo_khoa_du_lieu_don_vi(
            db, bao_cao.thang, bao_cao.nam, bao_cao.don_vi_id
        )

        message = f"Đã từ chối báo cáo. {so_cc_bi_tu_choi} CC cần điều chỉnh."
    
    await db.flush()
    
    return success_response(
        data={
            "id": bao_cao.id,
            "trang_thai": bao_cao.trang_thai,
            "ngay_phe_duyet": bao_cao.ngay_phe_duyet,
            "so_cc_bi_tu_choi": so_cc_bi_tu_choi,
        },
        message=message
    )


# =============================================================================
# 7b. POST /{id}/tra-lai - CCT trả lại báo cáo đã phê duyệt (MỚI v3.0.0)
# =============================================================================

@router.post("/{bao_cao_id}/tra-lai")
async def tra_lai_bao_cao(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    bao_cao_id: UUID,
    payload: TraLaiBaoCaoRequest,
) -> dict:
    """
    CCT trả lại báo cáo xếp loại đã phê duyệt.
    Chuyển DA_PHE_DUYET → CHO_PHE_DUYET để Đội trưởng điều chỉnh lại.
    """
    if not check_is_chi_cuc_truong(current_user):
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_003", message="Chỉ Chi cục trưởng mới có quyền trả lại báo cáo"
        ))
    
    bao_cao = await get_bao_cao_full(db, bao_cao_id)
    
    if not bao_cao:
        raise HTTPException(status_code=404, detail=error_response(
            code="NOT_FOUND", message="Không tìm thấy báo cáo"
        ))
    
    if bao_cao.trang_thai != TrangThaiBaoCao.DA_PHE_DUYET.value:
        raise HTTPException(status_code=400, detail=error_response(
            code="INVALID_STATE", message="Chỉ trả lại được khi báo cáo ở trạng thái DA_PHE_DUYET"
        ))
    
    # Trả lại về CHO_PHE_DUYET (ĐT xem lại và sửa)
    bao_cao.trang_thai = TrangThaiBaoCao.CHO_PHE_DUYET.value
    bao_cao.y_kien_phe_duyet = f"[TRẢ LẠI] {payload.ly_do}"
    bao_cao.ngay_phe_duyet = None
    
    # Reset xep_loai_quyet_dinh của tất cả chi tiết
    for ct in bao_cao.chi_tiets:
        ct.xep_loai_quyet_dinh = None
        ct.ly_do_dieu_chinh_cct = None

    # FIX: Mở khóa dữ liệu khi trả lại để ĐT/CC có thể chỉnh sửa
    unlock_result = await _mo_khoa_du_lieu_don_vi(
        db, bao_cao.thang, bao_cao.nam, bao_cao.don_vi_id
    )

    await db.flush()

    return success_response(
        data={
            "id": str(bao_cao.id),
            "trang_thai_moi": "CHO_PHE_DUYET",
            "ly_do": payload.ly_do,
            **unlock_result,
        },
        message="Đã trả lại báo cáo. Đội trưởng có thể điều chỉnh lại."
    )


# =============================================================================
# 8. GET /thong-ke/thang/{thang}/nam/{nam} - Thống kê toàn Chi cục
# =============================================================================

@router.get("/thong-ke/thang/{thang}/nam/{nam}")
async def get_thong_ke_chi_cuc(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int,
    nam: int,
) -> dict:
    """
    Thống kê xếp loại toàn Chi cục theo tháng.

    FIX (02/03/2026): Hiển thị TẤT CẢ đơn vị có CC active, kể cả khi
    chưa có báo cáo cho tháng đó. CC chưa kê khai tính điểm 0 → xếp loại D.

    Quyền: CCT, Phó CCT
    """
    if not check_is_lanh_dao_chi_cuc(current_user):
        raise HTTPException(status_code=403, detail=error_response(
            code="PERM_003", message="Chỉ Lãnh đạo Chi cục mới có quyền xem thống kê"
        ))

    _excluded_roles = [CapBacVaiTro.SUPER_ADMIN, CapBacVaiTro.QUAN_LY_DON_VI]

    # 1. Lấy TẤT CẢ đơn vị có CC active (loại đơn vị 0 người)
    stmt_dv = (
        select(
            DonVi,
            func.count(CongChuc.id).label("cc_count"),
        )
        .join(CongChuc, CongChuc.don_vi_id == DonVi.id)
        .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id, isouter=True)
        .where(
            DonVi.is_deleted == False,
            CongChuc.is_active == True,
            CongChuc.is_deleted == False,
            or_(
                CongChuc.vai_tro_id == None,
                ~VaiTro.cap_bac.in_(_excluded_roles),
            ),
        )
        .group_by(DonVi.id)
        .having(func.count(CongChuc.id) > 0)
        .order_by(DonVi.ten_don_vi)
    )
    result_dv = await db.execute(stmt_dv)
    don_vi_rows = result_dv.all()

    # 2. Lấy báo cáo tháng này (nếu có)
    stmt_bc = (
        select(BaoCaoXepLoai)
        .where(
            BaoCaoXepLoai.thang == thang,
            BaoCaoXepLoai.nam == nam,
            BaoCaoXepLoai.is_deleted == False,
        )
    )
    result_bc = await db.execute(stmt_bc)
    bc_map = {bc.don_vi_id: bc for bc in result_bc.scalars().all()}

    # 3. Tổng hợp
    # FIX (02/03/2026): Luôn dùng cc_count (live) làm tổng CC thay vì
    # bc.tong_cong_chuc (snapshot cũ có thể sai do code cũ hoặc CC chuyển đơn vị).
    # A/B/C/D: dùng từ báo cáo nếu có, phần dư = D (CC chưa được xếp loại).
    tong = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    tong_cc = 0
    theo_don_vi = []

    for dv, cc_count in don_vi_rows:
        bc = bc_map.get(dv.id)

        # Luôn dùng cc_count (số CC active hiện tại) làm tổng
        dv_tong = cc_count

        if bc:
            # Có báo cáo → dùng A/B/C/D/E từ báo cáo
            dv_a = bc.so_loai_a or 0
            dv_b = bc.so_loai_b or 0
            dv_c = bc.so_loai_c or 0
            dv_d = bc.so_loai_d or 0
            dv_e = bc.so_loai_e or 0
            dv_trang_thai = bc.trang_thai

            # Nếu tổng xếp loại < cc_count (báo cáo cũ thiếu CC)
            # → CC thiếu tính là D (chưa kê khai = điểm 0)
            tong_xl = dv_a + dv_b + dv_c + dv_d + dv_e
            if tong_xl < cc_count:
                dv_d += (cc_count - tong_xl)
        else:
            # Chưa có báo cáo → tất cả CC = điểm 0 → xếp loại D
            dv_a = 0
            dv_b = 0
            dv_c = 0
            dv_d = cc_count
            dv_e = 0
            dv_trang_thai = None

        tong["A"] += dv_a
        tong["B"] += dv_b
        tong["C"] += dv_c
        tong["D"] += dv_d
        tong["E"] += dv_e
        tong_cc += dv_tong

        theo_don_vi.append({
            "don_vi": {
                "id": dv.id,
                "ma_don_vi": dv.ma_don_vi,
                "ten_don_vi": dv.ten_don_vi,
            },
            "tong": dv_tong,
            "A": dv_a,
            "B": dv_b,
            "C": dv_c,
            "D": dv_d,
            "E": dv_e,
            "trang_thai": dv_trang_thai,
        })

    return success_response(
        data={
            "thang": thang,
            "nam": nam,
            "tong_cong_chuc": tong_cc,
            "theo_xep_loai": tong,
            "theo_don_vi": theo_don_vi,
        },
        message=f"Thống kê tháng {thang}/{nam}"
    )