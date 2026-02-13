"""
app/api/v1/endpoints/export_bao_cao.py
======================================
API Endpoints xuất báo cáo DOCX/PDF cho hệ thống KPI.

Endpoints:
1. GET /export/ca-nhan/thang/{thang}/nam/{nam}          - Xuất Mẫu 01 + 02 (cá nhân)
2. GET /export/don-vi/thang/{thang}/nam/{nam}            - Xuất Mẫu 03 (đơn vị)
3. GET /export/tong-hop/thang/{thang}/nam/{nam}          - Xuất Mẫu 04 toàn Chi cục (CCT/PCCT)
4. GET /export/don-vi-tong-hop/thang/{thang}/nam/{nam}   - Xuất Mẫu 03 tất cả đơn vị
5. GET /export/mau05-doi-moi/thang/{thang}/nam/{nam}     - Xuất Mẫu 05 CC có thành tích đổi mới

Output: DOCX hoặc PDF (query param ?format=docx|pdf)

Phiên bản: 1.1.0 (11/02/2026) - Thêm Mẫu 04 cho tổng hợp toàn Chi cục
Phiên bản: 1.0.0 (02/02/2026)
"""

import io
import logging
import subprocess
import tempfile
import traceback
import calendar
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Optional, List
from uuid import UUID

logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import DatabaseDep, ActiveUserDep
from app.models.user_org import CongChuc, DonVi, VaiTro, CapBacVaiTro
from app.models.kpi_submission import KeKhaiCongViec, TrangThaiKeKhai
from app.models.kpi_assessment import DanhGiaThang, TieuChiChung, TieuChiChungDanhGia
from app.models.bao_cao_xep_loai import (
    BaoCaoXepLoai, ChiTietXepLoai, TrangThaiBaoCao
)
from app.schemas.common import error_response


router = APIRouter()


# =============================================================================
# HELPER: CONVERT DOCX -> PDF VIA LIBREOFFICE
# =============================================================================

def convert_docx_to_pdf(docx_bytes: bytes) -> bytes:
    """
    Convert DOCX bytes sang PDF bytes sử dụng LibreOffice headless.
    
    Raises:
        HTTPException nếu LibreOffice không khả dụng hoặc convert lỗi.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        docx_path = Path(tmpdir) / "report.docx"
        docx_path.write_bytes(docx_bytes)
        
        try:
            result = subprocess.run(
                [
                    "libreoffice", "--headless", "--convert-to", "pdf",
                    "--outdir", tmpdir, str(docx_path)
                ],
                capture_output=True, text=True, timeout=60
            )
        except FileNotFoundError:
            raise HTTPException(
                status_code=500,
                detail=error_response(
                    code="SYS_010",
                    message="LibreOffice chưa được cài đặt trên server. Vui lòng xuất DOCX."
                )
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=500,
                detail=error_response(
                    code="SYS_011",
                    message="Chuyển đổi PDF quá thời gian cho phép."
                )
            )
        
        pdf_path = Path(tmpdir) / "report.pdf"
        if not pdf_path.exists():
            raise HTTPException(
                status_code=500,
                detail=error_response(
                    code="SYS_012",
                    message="Không thể tạo file PDF. Vui lòng xuất DOCX."
                )
            )
        
        return pdf_path.read_bytes()


# =============================================================================
# HELPER: STREAMING RESPONSE
# =============================================================================

def make_file_response(
    file_bytes: bytes,
    filename: str,
    fmt: str = "docx"
) -> StreamingResponse:
    """Tạo StreamingResponse cho file download."""
    if fmt == "pdf":
        media_type = "application/pdf"
        filename = filename.replace(".docx", ".pdf")
    else:
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        }
    )


# =============================================================================
# HELPER: KIỂM TRA QUYỀN
# =============================================================================

def _get_cap_bac(user: CongChuc) -> Optional[str]:
    """Lấy cấp bậc vai trò."""
    if not user.vai_tro:
        return None
    return user.vai_tro.cap_bac


def _is_lanh_dao_chi_cuc(user: CongChuc) -> bool:
    """CCT hoặc PCCT hoặc user có flag can_view_all_units."""
    # v1.1.0: User có flag can_view_all_units
    if getattr(user, 'can_view_all_units', False):
        return True
    cap_bac = _get_cap_bac(user)
    return cap_bac in [CapBacVaiTro.CHI_CUC_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG]


def _is_lanh_dao_don_vi(user: CongChuc) -> bool:
    """ĐT hoặc Phó ĐT."""
    cap_bac = _get_cap_bac(user)
    return cap_bac in [CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI]


# =============================================================================
# HELPER: LẤY DỮ LIỆU
# =============================================================================

async def _get_danh_gia_thang(
    db: AsyncSession, cong_chuc_id: UUID, thang: int, nam: int
) -> Optional[DanhGiaThang]:
    """Lấy đánh giá tháng (tiêu chí chung) của 1 CC."""
    stmt = (
        select(DanhGiaThang)
        .options(
            selectinload(DanhGiaThang.tieu_chi_chungs)
            .selectinload(TieuChiChungDanhGia.tieu_chi)
        )
        .where(
            DanhGiaThang.cong_chuc_id == cong_chuc_id,
            DanhGiaThang.thang == thang,
            DanhGiaThang.nam == nam,
            DanhGiaThang.is_deleted == False,
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _get_ke_khai_list(
    db: AsyncSession, cong_chuc_id: UUID, thang: int, nam: int
) -> list:
    """Lấy danh sách kê khai đã duyệt của 1 CC."""
    stmt = (
        select(KeKhaiCongViec)
        .options(
            selectinload(KeKhaiCongViec.danh_muc_sp),
            selectinload(KeKhaiCongViec.cap_do),
        )
        .where(
            KeKhaiCongViec.cong_chuc_id == cong_chuc_id,
            KeKhaiCongViec.thang == thang,
            KeKhaiCongViec.nam == nam,
            KeKhaiCongViec.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET,
            KeKhaiCongViec.is_deleted == False,
        )
        .order_by(KeKhaiCongViec.created_at)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _get_tieu_chi_chung_list(db: AsyncSession) -> list:
    """Lấy danh sách tiêu chí chung (master data)."""
    stmt = (
        select(TieuChiChung)
        .where(TieuChiChung.is_active == True)
        .order_by(TieuChiChung.thu_tu)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _get_bao_cao_don_vi(
    db: AsyncSession, don_vi_id: UUID, thang: int, nam: int
) -> Optional[BaoCaoXepLoai]:
    """Lấy báo cáo xếp loại đơn vị kèm chi tiết."""
    stmt = (
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
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _get_all_bao_cao(
    db: AsyncSession, thang: int, nam: int
) -> list:
    """Lấy tất cả báo cáo xếp loại toàn Chi cục."""
    stmt = (
        select(BaoCaoXepLoai)
        .options(
            selectinload(BaoCaoXepLoai.don_vi),
            selectinload(BaoCaoXepLoai.nguoi_lap),
            selectinload(BaoCaoXepLoai.chi_tiets).selectinload(ChiTietXepLoai.cong_chuc),
        )
        .where(
            BaoCaoXepLoai.thang == thang,
            BaoCaoXepLoai.nam == nam,
            BaoCaoXepLoai.is_deleted == False,
        )
        .order_by(BaoCaoXepLoai.don_vi_id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


# =============================================================================
# HELPER: BUILD DATA DICTS CHO DOCX GENERATOR
# =============================================================================

def _build_mau01_data(
    user: CongChuc,
    thang: int, nam: int,
    danh_gia: Optional[DanhGiaThang],
    chi_tiet_xep_loai: Optional[ChiTietXepLoai],
) -> dict:
    """Build data dict cho Mẫu 01 - Phiếu theo dõi đánh giá."""
    # Tiêu chí chung chi tiết
    tieu_chi_items = []
    if danh_gia and hasattr(danh_gia, 'tieu_chi_chungs') and danh_gia.tieu_chi_chungs:
        for tc_dg in danh_gia.tieu_chi_chungs:
            tc = tc_dg.tieu_chi  # TieuChiChung master record
            tieu_chi_items.append({
                "ten": tc.ten_tieu_chi if tc else "",
                "diem_toi_da": float(tc.diem_toi_da) if tc else 0,
                "diem_tu_cham": float(tc_dg.diem_tu_cham) if tc_dg.diem_tu_cham else 0,
                "diem_lanh_dao": float(tc_dg.diem_phe_duyet) if tc_dg.diem_phe_duyet else 0,
            })
    
    diem_tcc = float(chi_tiet_xep_loai.diem_tieu_chi_chung) if chi_tiet_xep_loai else 0
    diem_kpi = float(chi_tiet_xep_loai.diem_kpi) if chi_tiet_xep_loai else 0
    diem_tong = float(chi_tiet_xep_loai.diem_tong) if chi_tiet_xep_loai else 0
    
    return {
        "ho_ten": user.ho_ten,
        "chuc_vu": user.chuc_vu or "",
        "don_vi": user.don_vi.ten_don_vi if user.don_vi else "",
        "thang": thang,
        "nam": nam,
        "tieu_chi_items": tieu_chi_items,
        "diem_tieu_chi_chung": diem_tcc,
        "diem_kpi": diem_kpi,
        "diem_tong": diem_tong,
        "xep_loai": chi_tiet_xep_loai.xep_loai_cuoi_cung if chi_tiet_xep_loai else "E",
    }


def _build_mau02_data(
    user: CongChuc,
    thang: int, nam: int,
    ke_khais: list,
    chi_tiet_xep_loai: Optional[ChiTietXepLoai],
) -> dict:
    """Build data dict cho Mẫu 02 - Bảng kê công việc cá nhân."""
    cong_viec_items = []
    tong_sp_quy_doi = Decimal("0")
    tong_sp_cl = Decimal("0")
    tong_sp_td = Decimal("0")
    
    for kk in ke_khais:
        sp_qd = kk.so_sp_goc_quy_doi or Decimal("0")
        sp_cl = kk.so_sp_chat_luong or Decimal("0")
        sp_td = kk.so_sp_tien_do or Decimal("0")
        
        tong_sp_quy_doi += sp_qd
        tong_sp_cl += sp_cl
        tong_sp_td += sp_td
        
        cong_viec_items.append({
            "ten_cong_viec": kk.danh_muc_sp.ten_cong_viec if kk.danh_muc_sp else "",
            "cap_do": kk.cap_do.ma_cap_do if kk.cap_do else "",
            "so_luong": kk.so_luong,
            "sp_quy_doi": float(sp_qd),
            "tu_dg_tien_do": kk.tu_danh_gia_tien_do or 0,
            "tu_dg_chat_luong": kk.tu_danh_gia_chat_luong or 0,
            "so_loi_tien_do": kk.so_loi_tien_do or 0,
            "so_loi_chat_luong": kk.so_loi_chat_luong or 0,
            "sp_chat_luong": float(sp_cl),
            "sp_tien_do": float(sp_td),
        })
    
    so_ngay_lv = float(chi_tiet_xep_loai.so_ngay_lam_viec or 0) if chi_tiet_xep_loai else 0
    so_ngay_nghi = float(chi_tiet_xep_loai.so_ngay_nghi or 0) if chi_tiet_xep_loai else 0
    diem_tcc = float(chi_tiet_xep_loai.diem_tieu_chi_chung) if chi_tiet_xep_loai else 0
    diem_kpi = float(chi_tiet_xep_loai.diem_kpi) if chi_tiet_xep_loai else 0
    diem_tong = float(chi_tiet_xep_loai.diem_tong) if chi_tiet_xep_loai else 0
    
    return {
        "ho_ten": user.ho_ten,
        "chuc_vu": user.chuc_vu or "",
        "don_vi": user.don_vi.ten_don_vi if user.don_vi else "",
        "thang": thang,
        "nam": nam,
        "so_ngay_lam_viec": so_ngay_lv,
        "so_ngay_nghi": so_ngay_nghi,
        "cong_viec_items": cong_viec_items,
        "tong_sp_quy_doi": float(tong_sp_quy_doi),
        "tong_sp_chat_luong": float(tong_sp_cl),
        "tong_sp_tien_do": float(tong_sp_td),
        "target_sp": so_ngay_lv * 96,
        "diem_tieu_chi_chung": diem_tcc,
        "diem_kpi": diem_kpi,
        "diem_tong": diem_tong,
        "xep_loai": chi_tiet_xep_loai.xep_loai_cuoi_cung if chi_tiet_xep_loai else "E",
    }


def _build_mau03_data(
    bao_caos: list,
    thang: int, nam: int,
    don_vi_name: str = "",
    is_toan_chi_cuc: bool = False,
) -> dict:
    """Build data dict cho Mẫu 03 - Bảng tổng hợp xếp loại."""
    rows = []
    stt = 0
    
    for bc in bao_caos:
        don_vi_ten = bc.don_vi.ten_don_vi if bc.don_vi else ""
        
        if bc.chi_tiets:
            for ct in bc.chi_tiets:
                stt += 1
                xep_loai_cuoi = ct.xep_loai_quyet_dinh or ct.xep_loai_de_xuat or ct.xep_loai_he_thong
                
                rows.append({
                    "stt": stt,
                    "ho_ten": ct.cong_chuc.ho_ten if ct.cong_chuc else "",
                    "don_vi": don_vi_ten,
                    "chuc_vu": ct.cong_chuc.chuc_vu if ct.cong_chuc else "",
                    "so_ngay_lv": float(ct.so_ngay_lam_viec or 0),
                    "so_ngay_nghi": float(ct.so_ngay_nghi or 0),
                    "diem_tcc": float(ct.diem_tieu_chi_chung or 0),
                    "diem_kpi": float(ct.diem_kpi or 0),
                    "diem_tong": float(ct.diem_tong or 0),
                    "xep_loai_he_thong": ct.xep_loai_he_thong or "",
                    "xep_loai_de_xuat": ct.xep_loai_de_xuat or "",
                    "xep_loai_quyet_dinh": ct.xep_loai_quyet_dinh or "",
                    "xep_loai_cuoi": xep_loai_cuoi,
                    "ghi_chu": ct.ghi_chu or "",
                })
    
    title = "BẢNG TỔNG HỢP KẾT QUẢ XẾP LOẠI CHẤT LƯỢNG CÔNG CHỨC"
    if is_toan_chi_cuc:
        subtitle = f"Toàn Chi cục - Tháng {thang}/{nam}"
    else:
        subtitle = f"{don_vi_name} - Tháng {thang}/{nam}"
    
    # Thống kê
    tong = len(rows)
    so_a = sum(1 for r in rows if r["xep_loai_cuoi"] == "A")
    so_b = sum(1 for r in rows if r["xep_loai_cuoi"] == "B")
    so_c = sum(1 for r in rows if r["xep_loai_cuoi"] == "C")
    so_d = sum(1 for r in rows if r["xep_loai_cuoi"] == "D")
    so_e = sum(1 for r in rows if r["xep_loai_cuoi"] == "E")
    
    return {
        "title": title,
        "subtitle": subtitle,
        "thang": thang,
        "nam": nam,
        "don_vi_name": don_vi_name,
        "is_toan_chi_cuc": is_toan_chi_cuc,
        "rows": rows,
        "thong_ke": {
            "tong": tong,
            "A": so_a, "B": so_b, "C": so_c, "D": so_d, "E": so_e,
        },
    }


def _build_mau04_data(
    bao_caos: list,
    thang: int, nam: int,
) -> dict:
    """
    Build data dict cho Mẫu 04 - DANH SÁCH PHÊ DUYỆT KẾT QUẢ XẾP LOẠI CHẤT LƯỢNG CÔNG CHỨC.
    
    Mẫu 04 bao gồm:
    - Bảng danh sách toàn bộ công chức với: STT, Mã CC, Họ tên, Năm sinh, Chức vụ, Đơn vị, Điểm, Xếp loại, Ghi chú
    - Bảng tổng hợp: Mức xếp loại | Số lượng | Tỷ lệ %
    - Bảng vinh danh: Top 5 công chức có điểm cao nhất (loại A)
    """
    rows = []
    stt = 0
    
    for bc in bao_caos:
        don_vi_ten = bc.don_vi.ten_don_vi if bc.don_vi else ""
        
        if bc.chi_tiets:
            for ct in bc.chi_tiets:
                # Filter: bỏ qua user đã bị vô hiệu hóa hoặc đã xóa
                if not ct.cong_chuc:
                    continue
                if hasattr(ct.cong_chuc, 'is_active') and ct.cong_chuc.is_active == False:
                    continue
                if hasattr(ct.cong_chuc, 'deleted_at') and ct.cong_chuc.deleted_at is not None:
                    continue
                    
                stt += 1
                xep_loai_cuoi = ct.xep_loai_quyet_dinh or ct.xep_loai_de_xuat or ct.xep_loai_he_thong
                
                # Lấy năm sinh từ ngày sinh
                nam_sinh = ""
                if ct.cong_chuc and ct.cong_chuc.ngay_sinh:
                    nam_sinh = ct.cong_chuc.ngay_sinh.year if hasattr(ct.cong_chuc.ngay_sinh, 'year') else str(ct.cong_chuc.ngay_sinh)[:4]
                
                rows.append({
                    "stt": stt,
                    "ma_cc": ct.cong_chuc.ma_cc if ct.cong_chuc else "",
                    "ho_ten": ct.cong_chuc.ho_ten if ct.cong_chuc else "",
                    "nam_sinh": nam_sinh,
                    "chuc_vu": ct.cong_chuc.chuc_vu if ct.cong_chuc else "",
                    "don_vi": don_vi_ten,
                    "diem_tong": float(ct.diem_tong or 0),
                    "xep_loai": xep_loai_cuoi,
                    "ghi_chu": ct.ghi_chu or "",
                })
    
    # Thống kê
    tong = len(rows)
    so_a = sum(1 for r in rows if r["xep_loai"] == "A")
    so_b = sum(1 for r in rows if r["xep_loai"] == "B")
    so_c = sum(1 for r in rows if r["xep_loai"] == "C")
    so_d = sum(1 for r in rows if r["xep_loai"] == "D")
    so_e = sum(1 for r in rows if r["xep_loai"] == "E")
    
    # Tính tỷ lệ phần trăm
    def calc_pct(count):
        return round(count * 100 / tong, 1) if tong > 0 else 0
    
    thong_ke = [
        {"muc": "A", "so_luong": so_a, "ty_le": calc_pct(so_a)},
        {"muc": "B", "so_luong": so_b, "ty_le": calc_pct(so_b)},
        {"muc": "C", "so_luong": so_c, "ty_le": calc_pct(so_c)},
        {"muc": "D", "so_luong": so_d, "ty_le": calc_pct(so_d)},
        {"muc": "E", "so_luong": so_e, "ty_le": calc_pct(so_e)},
    ]
    
    # Top công chức xuất sắc (loại A, sắp theo điểm giảm dần)
    top_xuat_sac = sorted(
        [r for r in rows if r["xep_loai"] == "A"],
        key=lambda x: x["diem_tong"],
        reverse=True
    )[:5]  # Top 5
    
    vinh_danh = []
    for i, r in enumerate(top_xuat_sac, 1):
        vinh_danh.append({
            "stt": i,
            "ho_ten": r["ho_ten"],
            "don_vi": r["don_vi"],
            "diem": r["diem_tong"],
        })
    
    return {
        "title": "DANH SÁCH PHÊ DUYỆT KẾT QUẢ XẾP LOẠI CHẤT LƯỢNG CÔNG CHỨC",
        "subtitle": f"Tháng {thang} năm {nam}",
        "thang": thang,
        "nam": nam,
        "rows": rows,
        "thong_ke": thong_ke,
        "vinh_danh": vinh_danh,
        "tong_cong_chuc": tong,
    }

async def _build_mau05_data(
    db: AsyncSession,
    thang: int, 
    nam: int,
) -> dict:
    """
    Build data cho Mẫu 05 - Báo cáo CC có thành tích đổi mới sáng tạo.
    Chỉ lấy CC có tích ít nhất 1 tiêu chí nhóm III (nhom_tieu_chi = 3).
    """
    # 1. Lấy tất cả tiêu chí chung (master data)
    stmt_tc = select(TieuChiChung).where(TieuChiChung.is_active == True).order_by(TieuChiChung.ma_tieu_chi)
    result_tc = await db.execute(stmt_tc)
    all_tieu_chi = result_tc.scalars().all()
    
    # 2. Lấy tất cả đánh giá tháng
    stmt = (
        select(DanhGiaThang)
        .options(
            selectinload(DanhGiaThang.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(DanhGiaThang.tieu_chi_chungs),
        )
        .where(
            DanhGiaThang.thang == thang,
            DanhGiaThang.nam == nam,
        )
    )
    result = await db.execute(stmt)
    danh_gias = result.scalars().all()
    
    cong_chuc_list = []
    
    for dg in danh_gias:
        # Filter: bỏ user inactive/deleted
        if not dg.cong_chuc:
            continue
        if hasattr(dg.cong_chuc, 'is_active') and dg.cong_chuc.is_active == False:
            continue
        if hasattr(dg.cong_chuc, 'deleted_at') and dg.cong_chuc.deleted_at is not None:
            continue
        
        # Kiểm tra có tích nhóm III không
        has_nhom3 = False
        tieu_chi_data = []
        tong_diem_cc = 0
        tong_diem_ld = 0
        diem_nhom3_cc = 0
        diem_nhom3_ld = 0
        
        # Map tiêu chí đánh giá theo tieu_chi_id
        tc_danh_gia_map = {str(tcdg.tieu_chi_id): tcdg for tcdg in (dg.tieu_chi_chungs or [])}
        
        for tc in all_tieu_chi:
            tcdg = tc_danh_gia_map.get(str(tc.id))
            
            is_achieved_cc = tcdg.is_achieved_cc if tcdg else False
            is_achieved_ld = tcdg.is_achieved_ld if tcdg else None
            diem_cc = float(tcdg.diem_tu_cham) if tcdg and tcdg.diem_tu_cham else 0
            diem_ld = float(tcdg.diem_phe_duyet) if tcdg and tcdg.diem_phe_duyet is not None else None
            ghi_chu = tcdg.ghi_chu_cc if tcdg else ""
            
            # Tính điểm
            tong_diem_cc += diem_cc
            if diem_ld is not None:
                tong_diem_ld += diem_ld
            
            # Kiểm tra nhóm III
            if tc.nhom_tieu_chi == 3:
                diem_nhom3_cc += diem_cc
                if diem_ld is not None:
                    diem_nhom3_ld += diem_ld
                final_achieved = is_achieved_ld if is_achieved_ld is not None else is_achieved_cc
                if final_achieved:
                    has_nhom3 = True
            
            tieu_chi_data.append({
                "ma": tc.ma_tieu_chi,
                "ten": tc.ten_tieu_chi,
                "nhom": tc.nhom_tieu_chi,
                "diem_toi_da": float(tc.diem_toi_da),
                "is_achieved_cc": is_achieved_cc,
                "is_achieved_ld": is_achieved_ld,
                "diem_cc": diem_cc,
                "diem_ld": diem_ld,
                "ghi_chu": ghi_chu or "",
            })
        
        # Chỉ lấy CC có tích nhóm III
        if has_nhom3:
            cong_chuc_list.append({
                "ho_ten": dg.cong_chuc.ho_ten,
                "ma_cc": dg.cong_chuc.ma_cc,
                "don_vi": dg.cong_chuc.don_vi.ten_don_vi if dg.cong_chuc.don_vi else "",
                "chuc_vu": dg.cong_chuc.chuc_vu or "",
                "tieu_chi": tieu_chi_data,
                "tong_diem_cc": tong_diem_cc,
                "tong_diem_ld": tong_diem_ld,
                "diem_nhom3_cc": diem_nhom3_cc,
                "diem_nhom3_ld": diem_nhom3_ld,
            })
    
    # Sắp xếp theo điểm nhóm III giảm dần
    cong_chuc_list.sort(key=lambda x: x["diem_nhom3_ld"] or x["diem_nhom3_cc"], reverse=True)
    
    return {
        "title": "PHIẾU THEO DÕI TIÊU CHÍ CHUNG - CÔNG CHỨC CÓ THÀNH TÍCH ĐỔI MỚI",
        "thang": thang,
        "nam": nam,
        "cong_chucs": cong_chuc_list,
        "tong_so_cc": len(cong_chuc_list),
    }

# =============================================================================
# HELPER: TÌM CHI TIẾT XẾP LOẠI CỦA 1 CC
# =============================================================================

async def _find_chi_tiet_xep_loai(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
) -> Optional[ChiTietXepLoai]:
    """Tìm chi tiết xếp loại của 1 CC trong tháng."""
    stmt = (
        select(ChiTietXepLoai)
        .join(BaoCaoXepLoai)
        .where(
            ChiTietXepLoai.cong_chuc_id == cong_chuc_id,
            BaoCaoXepLoai.thang == thang,
            BaoCaoXepLoai.nam == nam,
            BaoCaoXepLoai.is_deleted == False,
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# =============================================================================
# 1. EXPORT CÁ NHÂN (Mẫu 01 + 02)
# =============================================================================

@router.get("/ca-nhan/thang/{thang}/nam/{nam}")
async def export_ca_nhan(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int,
    nam: int,
    format: str = Query("docx", regex="^(docx|pdf)$"),
    cong_chuc_id: Optional[UUID] = Query(None, description="ID CC cần xuất (LĐ xuất cho nhân viên)"),
):
    """
    Xuất báo cáo cá nhân: Mẫu 01 + Mẫu 02 trong 1 file DOCX.
    
    - CC thường: Xuất cho chính mình
    - Lãnh đạo (ĐT/PCCT/CCT): Có thể xuất cho CC thuộc đơn vị (truyền cong_chuc_id)
    
    Query params:
    - format: docx | pdf (default: docx)
    - cong_chuc_id: UUID (optional, LĐ xuất cho CC khác)
    """
    # Validate
    if thang < 1 or thang > 12:
        raise HTTPException(400, detail=error_response("VAL_001", "Tháng phải từ 1-12"))
    if nam < 2025:
        raise HTTPException(400, detail=error_response("VAL_002", "Năm phải >= 2025"))
    
    # Xác định CC cần xuất
    target_user = current_user
    if cong_chuc_id and cong_chuc_id != current_user.id:
        # Kiểm tra quyền: phải là LĐ đơn vị hoặc LĐ chi cục
        if not (_is_lanh_dao_don_vi(current_user) or _is_lanh_dao_chi_cuc(current_user)):
            raise HTTPException(403, detail=error_response(
                "PERM_003", "Bạn không có quyền xuất báo cáo cho người khác"
            ))
        
        # Load target user
        stmt = (
            select(CongChuc)
            .options(selectinload(CongChuc.don_vi), selectinload(CongChuc.vai_tro))
            .where(CongChuc.id == cong_chuc_id, CongChuc.is_deleted == False)
        )
        result = await db.execute(stmt)
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise HTTPException(404, detail=error_response("BIZ_001", "Không tìm thấy công chức"))
        
        # ĐT/Phó ĐT chỉ được xuất cho CC cùng đơn vị
        if _is_lanh_dao_don_vi(current_user) and target_user.don_vi_id != current_user.don_vi_id:
            raise HTTPException(403, detail=error_response(
                "PERM_004", "Bạn chỉ được xuất báo cáo cho CC trong đơn vị mình"
            ))
    else:
        # Load đầy đủ relationships cho current_user
        stmt = (
            select(CongChuc)
            .options(selectinload(CongChuc.don_vi), selectinload(CongChuc.vai_tro))
            .where(CongChuc.id == current_user.id)
        )
        result = await db.execute(stmt)
        target_user = result.scalar_one_or_none() or current_user
    
    # Lấy dữ liệu
    danh_gia = await _get_danh_gia_thang(db, target_user.id, thang, nam)
    ke_khais = await _get_ke_khai_list(db, target_user.id, thang, nam)
    chi_tiet_xl = await _find_chi_tiet_xep_loai(db, target_user.id, thang, nam)
    
    # Build data
    mau01_data = _build_mau01_data(target_user, thang, nam, danh_gia, chi_tiet_xl)
    mau02_data = _build_mau02_data(target_user, thang, nam, ke_khais, chi_tiet_xl)
    
    # Generate DOCX via Node.js script
    import json
    combined_data = {
        "mau01": mau01_data,
        "mau02": mau02_data,
    }
    
    # Gọi Node.js generator
    docx_bytes = await _generate_docx("ca-nhan", combined_data)
    
    # Convert nếu cần PDF
    if format == "pdf":
        docx_bytes = convert_docx_to_pdf(docx_bytes)
    
    filename = f"BaoCao_CaNhan_{target_user.ma_cc}_{thang:02d}_{nam}.{format}"
    return make_file_response(docx_bytes, filename, format)


# =============================================================================
# 2. EXPORT ĐƠN VỊ (Mẫu 03)
# =============================================================================

@router.get("/don-vi/thang/{thang}/nam/{nam}")
async def export_don_vi(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int,
    nam: int,
    format: str = Query("docx", regex="^(docx|pdf)$"),
    don_vi_id: Optional[UUID] = Query(None, description="ID đơn vị (CCT/PCCT chọn đơn vị)"),
):
    """
    Xuất Mẫu 03 - Bảng tổng hợp xếp loại đơn vị.
    
    - ĐT/Phó ĐT: Chỉ xuất đơn vị mình
    - PCCT/CCT: Chọn đơn vị bất kỳ
    """
    if thang < 1 or thang > 12:
        raise HTTPException(400, detail=error_response("VAL_001", "Tháng phải từ 1-12"))
    if nam < 2025:
        raise HTTPException(400, detail=error_response("VAL_002", "Năm phải >= 2025"))
    
    # Xác định đơn vị
    target_don_vi_id = don_vi_id or current_user.don_vi_id
    
    cap_bac = _get_cap_bac(current_user)
    has_view_all = getattr(current_user, 'can_view_all_units', False)
    if not has_view_all and cap_bac not in [
        CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI,
        CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG,
    ]:
        raise HTTPException(403, detail=error_response(
            "PERM_003", "Bạn không có quyền xuất báo cáo đơn vị"
        ))

    # ĐT/Phó ĐT: chỉ được xuất đơn vị mình (trừ user có flag can_view_all_units)
    if not has_view_all and _is_lanh_dao_don_vi(current_user) and target_don_vi_id != current_user.don_vi_id:
        raise HTTPException(403, detail=error_response(
            "PERM_004", "Bạn chỉ được xuất báo cáo đơn vị mình"
        ))
    
    # Lấy báo cáo
    bao_cao = await _get_bao_cao_don_vi(db, target_don_vi_id, thang, nam)
    if not bao_cao:
        raise HTTPException(404, detail=error_response(
            "BIZ_002", f"Chưa có báo cáo xếp loại tháng {thang}/{nam} cho đơn vị này"
        ))
    
    try:
        don_vi_name = bao_cao.don_vi.ten_don_vi if bao_cao.don_vi else ""
        mau03_data = _build_mau03_data([bao_cao], thang, nam, don_vi_name, is_toan_chi_cuc=False)
        
        # Generate DOCX
        docx_bytes = await _generate_docx("don-vi", mau03_data)
        
        if format == "pdf":
            docx_bytes = convert_docx_to_pdf(docx_bytes)
        
        filename = f"BaoCao_DonVi_{thang:02d}_{nam}.{format}"
        return make_file_response(docx_bytes, filename, format)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EXPORT] export_don_vi error: {traceback.format_exc()}")
        raise HTTPException(500, detail=error_response(
            "SYS_099", f"Lỗi xuất báo cáo: {str(e)[:200]}"
        ))


# =============================================================================
# 3. EXPORT TOÀN CHI CỤC (Mẫu 03 tổng hợp)
# =============================================================================

@router.get("/tong-hop/thang/{thang}/nam/{nam}")
async def export_tong_hop(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int,
    nam: int,
    format: str = Query("docx", regex="^(docx|pdf)$"),
):
    """
    Xuất Mẫu 04 - Danh sách phê duyệt kết quả xếp loại chất lượng công chức toàn Chi cục.
    
    Quyền: Chỉ CCT và PCCT.
    """
    if thang < 1 or thang > 12:
        raise HTTPException(400, detail=error_response("VAL_001", "Tháng phải từ 1-12"))
    if nam < 2025:
        raise HTTPException(400, detail=error_response("VAL_002", "Năm phải >= 2025"))
    
    if not _is_lanh_dao_chi_cuc(current_user):
        raise HTTPException(403, detail=error_response(
            "PERM_003", "Chỉ CCT và Phó CCT mới được xuất báo cáo tổng hợp toàn Chi cục"
        ))
    
    bao_caos = await _get_all_bao_cao(db, thang, nam)
    if not bao_caos:
        raise HTTPException(404, detail=error_response(
            "BIZ_003", f"Chưa có báo cáo xếp loại tháng {thang}/{nam}"
        ))
    
    # Sử dụng Mẫu 04 thay vì Mẫu 03
    mau04_data = _build_mau04_data(bao_caos, thang, nam)
    
    docx_bytes = await _generate_docx("tong-hop", mau04_data)
    
    if format == "pdf":
        docx_bytes = convert_docx_to_pdf(docx_bytes)
    
    filename = f"Mau04_DanhSach_XepLoai_ChiCuc_{thang:02d}_{nam}.{format}"
    return make_file_response(docx_bytes, filename, format)


@router.get("/don-vi-tong-hop/thang/{thang}/nam/{nam}")
async def export_don_vi_tong_hop(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int,
    nam: int,
    format: str = Query("docx", regex="^(docx|pdf)$"),
):
    """
    Xuất Mẫu 03 tổng hợp TẤT CẢ đơn vị (mỗi đơn vị 1 trang).
    
    Quyền: Chỉ CCT và PCCT.
    """
    if thang < 1 or thang > 12:
        raise HTTPException(400, detail=error_response("VAL_001", "Tháng phải từ 1-12"))
    if nam < 2025:
        raise HTTPException(400, detail=error_response("VAL_002", "Năm phải >= 2025"))
    
    if not _is_lanh_dao_chi_cuc(current_user):
        raise HTTPException(403, detail=error_response(
            "PERM_003", "Chỉ CCT và Phó CCT mới được xuất báo cáo tổng hợp"
        ))
    
    bao_caos = await _get_all_bao_cao(db, thang, nam)
    if not bao_caos:
        raise HTTPException(404, detail=error_response(
            "BIZ_003", f"Chưa có báo cáo xếp loại tháng {thang}/{nam}"
        ))
    
    # Build data cho từng đơn vị
    don_vi_list = []
    for bc in bao_caos:
        don_vi_data = _build_mau03_data(
            [bc], thang, nam,
            don_vi_name=bc.don_vi.ten_don_vi if bc.don_vi else "",
            is_toan_chi_cuc=False,
        )
        don_vi_list.append(don_vi_data)
    
    combined_data = {
        "don_vi_list": don_vi_list,
        "thang": thang,
        "nam": nam,
    }
    
    docx_bytes = await _generate_docx("don-vi-tong-hop", combined_data)
    
    if format == "pdf":
        docx_bytes = convert_docx_to_pdf(docx_bytes)
    
    filename = f"Mau03_TatCaDonVi_{thang:02d}_{nam}.{format}"
    return make_file_response(docx_bytes, filename, format)

@router.get("/mau05-doi-moi/thang/{thang}/nam/{nam}")
async def export_mau05_doi_moi(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int,
    nam: int,
    format: str = Query("docx", regex="^(docx|pdf)$"),
):
    """
    Xuất Mẫu 05 - Báo cáo công chức có thành tích đổi mới sáng tạo.
    Chỉ lấy CC có tích ít nhất 1 tiêu chí nhóm III.
    
    Quyền: Chỉ CCT và PCCT.
    """
    if thang < 1 or thang > 12:
        raise HTTPException(400, detail=error_response("VAL_001", "Tháng phải từ 1-12"))
    if nam < 2025:
        raise HTTPException(400, detail=error_response("VAL_002", "Năm phải >= 2025"))
    
    if not _is_lanh_dao_chi_cuc(current_user):
        raise HTTPException(403, detail=error_response(
            "PERM_003", "Chỉ CCT và Phó CCT mới được xuất báo cáo này"
        ))
    
    mau05_data = await _build_mau05_data(db, thang, nam)
    
    if not mau05_data["cong_chucs"]:
        raise HTTPException(404, detail=error_response(
            "BIZ_004", f"Không có công chức nào có tích tiêu chí nhóm III trong tháng {thang}/{nam}"
        ))
    
    docx_bytes = await _generate_docx("mau05-doi-moi", mau05_data)
    
    if format == "pdf":
        docx_bytes = convert_docx_to_pdf(docx_bytes)
    
    filename = f"Mau05_DoiMoiSangTao_{thang:02d}_{nam}.{format}"
    return make_file_response(docx_bytes, filename, format)

# =============================================================================
# HELPER: GỌI NODE.JS SCRIPT TẠO DOCX
# =============================================================================

async def _generate_docx(report_type: str, data: dict) -> bytes:
    """
    Gọi Node.js script để generate DOCX file.
    
    Args:
        report_type: "ca-nhan" | "don-vi" | "tong-hop"
        data: Dict dữ liệu cho template
    
    Returns:
        bytes: Nội dung file DOCX
    """
    import json
    
    # Đường dẫn tới script generator
    script_dir = Path(__file__).parent.parent.parent.parent / "scripts" / "docx_generator"
    script_path = script_dir / "generate.js"
    
    logger.error(f"[EXPORT] _generate_docx: script_path={script_path}, exists={script_path.exists()}, resolved={script_path.resolve()}")
    
    if not script_path.exists():
        raise HTTPException(500, detail=error_response(
            "SYS_020", f"Script tạo DOCX chưa được cài đặt trên server. Path: {script_path}"
        ))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Ghi data JSON
        data_path = Path(tmpdir) / "data.json"
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str)
        
        output_path = Path(tmpdir) / "output.docx"
        
        try:
            cmd = ["node", str(script_path), report_type, str(data_path), str(output_path)]
            logger.error(f"[EXPORT] Running: {' '.join(cmd)}")
            logger.error(f"[EXPORT] CWD: {script_dir}")
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=30,
                cwd=str(script_dir),
            )
            logger.error(f"[EXPORT] returncode={result.returncode}, stdout={result.stdout[:200]}, stderr={result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            raise HTTPException(500, detail=error_response(
                "SYS_021", "Tạo DOCX quá thời gian cho phép"
            ))
        
        # Node.js có thể exit với code != 0 (ví dụ SIGABRT) nhưng vẫn tạo file OK
        # Ưu tiên kiểm tra file output tồn tại
        if output_path.exists() and output_path.stat().st_size > 0:
            logger.error(f"[EXPORT] DOCX created OK: {output_path.stat().st_size} bytes (returncode={result.returncode})")
            return output_path.read_bytes()
        
        # Nếu file không tồn tại VÀ returncode != 0 → lỗi thật
        if result.returncode != 0:
            raise HTTPException(500, detail=error_response(
                "SYS_022",
                f"Lỗi tạo DOCX: {result.stderr[:200] if result.stderr else 'Unknown error'}"
            ))
        
        if not output_path.exists():
            raise HTTPException(500, detail=error_response(
                "SYS_023", "File DOCX không được tạo thành công"
            ))
        
        return output_path.read_bytes()