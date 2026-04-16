"""
app/api/v1/endpoints/xep_loai_quy.py
=====================================
API Endpoints cho Xếp loại quý (Quarterly Assessment).

PHIÊN BẢN: 3.6.0 (14/04/2026)

Endpoints:
- GET /tong-hop: Danh sách tổng hợp xếp loại quý
- GET /chi-tiet/{cong_chuc_id}: Chi tiết 3 tháng + tiêu chí
- POST /tinh-lai: Tính lại và lưu vào DB (admin)

Quyền:
- CC: Chỉ xem của mình
- TDV/PDV: Xem đơn vị mình
- CCT/PCCT: Xem tất cả
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DatabaseDep, ActiveUserDep
from app.models.kpi_assessment import DanhGiaQuy, DanhGiaThang
from app.models.user_org import CongChuc, VaiTro, CapBacVaiTro, DonVi
from app.schemas.quarterly import (
    TongHopQuyResponse,
    TongHopQuyItem,
    ThongKeQuyResponse,
    ChiTietQuyResponse,
    DanhGiaThangTrongQuy,
    DiemTCThangItem,
    TinhLaiQuyRequest,
    DanhGiaQuyResponse,
)
from app.schemas.master_data import CongChucBriefResponse, DonViResponse
from app.schemas.common import success_response, error_response
from app.api.v1.endpoints.xep_loai_quy_helpers import tinh_diem_quy, QUY_TO_THANG


router = APIRouter()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def kiem_tra_quyen_xem_quy(
    current_user: CongChuc,
    don_vi_id: Optional[UUID],
) -> bool:
    """Kiểm tra quyền xem xếp loại quý."""
    vai_tro = current_user.vai_tro

    if vai_tro.cap_bac in [CapBacVaiTro.SUPER_ADMIN, CapBacVaiTro.CHI_CUC_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG]:
        return True  # Xem tất cả

    if vai_tro.cap_bac in [CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI]:
        # TDV/PDV chỉ xem đơn vị mình
        if don_vi_id is None or don_vi_id == current_user.don_vi_id:
            return True

    return False


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get("/tong-hop", response_model=dict)
async def get_tong_hop_quy(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    quy: int = Query(..., ge=1, le=4, description="Quý (1-4)"),
    nam: int = Query(..., ge=2025, description="Năm"),
    don_vi_id: Optional[UUID] = Query(None, description="Lọc theo đơn vị (NULL = tất cả)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """
    Lấy danh sách tổng hợp xếp loại quý.

    Quyền:
    - CC: Chỉ xem của mình
    - TDV/PDV: Xem đơn vị mình
    - CCT/PCCT: Xem tất cả

    Returns:
    - data: List[TongHopQuyItem]
    - thong_ke: ThongKeQuyResponse
    - pagination: dict
    """
    vai_tro = current_user.vai_tro

    # Build query
    stmt = select(CongChuc).where(CongChuc.is_active == True)

    # Phân quyền
    if vai_tro.cap_bac == CapBacVaiTro.CONG_CHUC:
        # CC chỉ xem của mình
        stmt = stmt.where(CongChuc.id == current_user.id)
    elif vai_tro.cap_bac in [CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI]:
        # TDV/PDV xem đơn vị mình (hoặc filter)
        if don_vi_id:
            if don_vi_id != current_user.don_vi_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bạn không có quyền xem đơn vị khác"
                )
            stmt = stmt.where(CongChuc.don_vi_id == don_vi_id)
        else:
            stmt = stmt.where(CongChuc.don_vi_id == current_user.don_vi_id)
    else:
        # CCT/PCCT/SUPER_ADMIN xem tất cả (có filter)
        if don_vi_id:
            stmt = stmt.where(CongChuc.don_vi_id == don_vi_id)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = await db.scalar(count_stmt)

    # Pagination
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    cong_chucs = result.scalars().all()

    # Tính điểm quý cho từng CC
    data = []
    thong_ke = ThongKeQuyResponse()

    for idx, cc in enumerate(cong_chucs, start=(page - 1) * page_size + 1):
        # Tính điểm quý real-time
        ket_qua = await tinh_diem_quy(db, cc.id, quy, nam)

        item = TongHopQuyItem(
            stt=idx,
            cong_chuc_id=cc.id,
            ma_cc=cc.ma_cc,
            ho_ten=cc.ho_ten,
            don_vi_ten=cc.don_vi.ten_don_vi if cc.don_vi else "",
            is_lanh_dao=cc.is_lanh_dao,
            diem_kpi_quy=float(ket_qua["diem_kpi_quy"]) if ket_qua["diem_kpi_quy"] else None,
            diem_tc_quy=float(ket_qua["diem_tc_quy"]) if ket_qua["diem_tc_quy"] else None,
            diem_tong_quy=float(ket_qua["diem_tong_quy"]) if ket_qua["diem_tong_quy"] else None,
            xep_loai_quy=ket_qua["xep_loai_quy"],
            co_chuyen_don_vi=ket_qua["co_chuyen_don_vi"],
            ghi_chu=ket_qua["ghi_chu"],
        )
        data.append(item)

        # Thống kê
        thong_ke.tong_so_cc += 1
        if ket_qua["xep_loai_quy"] == "A":
            thong_ke.so_luong_A += 1
        elif ket_qua["xep_loai_quy"] == "B":
            thong_ke.so_luong_B += 1
        elif ket_qua["xep_loai_quy"] == "C":
            thong_ke.so_luong_C += 1
        elif ket_qua["xep_loai_quy"] == "D":
            thong_ke.so_luong_D += 1
        else:
            thong_ke.so_luong_chua_tinh += 1

    # Tính tỷ lệ %
    if thong_ke.tong_so_cc > 0:
        thong_ke.ty_le_A = round(thong_ke.so_luong_A / thong_ke.tong_so_cc * 100, 2)
        thong_ke.ty_le_B = round(thong_ke.so_luong_B / thong_ke.tong_so_cc * 100, 2)
        thong_ke.ty_le_C = round(thong_ke.so_luong_C / thong_ke.tong_so_cc * 100, 2)
        thong_ke.ty_le_D = round(thong_ke.so_luong_D / thong_ke.tong_so_cc * 100, 2)

    return success_response(
        data={
            "data": [item.model_dump() for item in data],
            "thong_ke": thong_ke.model_dump(),
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_count,
                "total_pages": (total_count + page_size - 1) // page_size,
            },
        }
    )


@router.get("/chi-tiet/{cong_chuc_id}", response_model=dict)
async def get_chi_tiet_quy(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    cong_chuc_id: UUID,
    quy: int = Query(..., ge=1, le=4, description="Quý (1-4)"),
    nam: int = Query(..., ge=2025, description="Năm"),
) -> dict:
    """
    Lấy chi tiết đánh giá quý của 1 công chức.

    Returns:
    - cac_thang: List[DanhGiaThangTrongQuy]
    - tieu_chi_quy: List[TieuChiQuyItem]
    - diem_kpi_quy, diem_tc_quy, diem_tong_quy, xep_loai_quy
    """
    # Kiểm tra quyền
    vai_tro = current_user.vai_tro

    # Lấy thông tin CC
    stmt_cc = select(CongChuc).where(CongChuc.id == cong_chuc_id)
    result_cc = await db.execute(stmt_cc)
    cc = result_cc.scalar_one_or_none()

    if not cc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy công chức"
        )

    # Phân quyền
    if vai_tro.cap_bac == CapBacVaiTro.CONG_CHUC:
        if cc.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn chỉ được xem của mình"
            )
    elif vai_tro.cap_bac in [CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI]:
        if cc.don_vi_id != current_user.don_vi_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền xem công chức đơn vị khác"
            )

    # Tính điểm quý
    ket_qua = await tinh_diem_quy(db, cong_chuc_id, quy, nam)

    # Build response
    cac_thang = [DanhGiaThangTrongQuy(**t) for t in ket_qua["cac_thang"]]

    # Tiêu chí quý (trung bình 3 tháng)
    tc_result = ket_qua["tieu_chi_quy"]
    tieu_chi_quy = [
        DiemTCThangItem(**item)
        for item in tc_result.get("chi_tiet_thang", [])
    ]

    response = ChiTietQuyResponse(
        cong_chuc_id=cc.id,
        cong_chuc=CongChucBriefResponse(
            id=cc.id,
            ma_cc=cc.ma_cc,
            ho_ten=cc.ho_ten,
            email=cc.email,
            so_dien_thoai=cc.so_dien_thoai,
            chuc_vu=cc.chuc_vu,
            is_lanh_dao=cc.is_lanh_dao,
        ),
        don_vi=DonViResponse(
            id=cc.don_vi.id,
            ma_don_vi=cc.don_vi.ma_don_vi,
            ten_don_vi=cc.don_vi.ten_don_vi,
            loai_don_vi=cc.don_vi.loai_don_vi.value,
        ) if cc.don_vi else None,
        quy=quy,
        nam=nam,
        cac_thang=cac_thang,
        tieu_chi_quy=tieu_chi_quy,
        diem_kpi_quy=float(ket_qua["diem_kpi_quy"]) if ket_qua["diem_kpi_quy"] else None,
        diem_tc_quy=float(ket_qua["diem_tc_quy"]) if ket_qua["diem_tc_quy"] else None,
        diem_tong_quy=float(ket_qua["diem_tong_quy"]) if ket_qua["diem_tong_quy"] else None,
        xep_loai_quy=ket_qua["xep_loai_quy"],
        co_chuyen_don_vi=ket_qua["co_chuyen_don_vi"],
        ghi_chu=ket_qua["ghi_chu"],
    )

    return success_response(data=response.model_dump())


@router.post("/tinh-lai", response_model=dict)
async def tinh_lai_quy(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    request: TinhLaiQuyRequest,
) -> dict:
    """
    Tính lại điểm quý và lưu vào bảng danh_gia_quy.

    Quyền: Chỉ SUPER_ADMIN, CCT

    Use case:
    - Admin muốn cache kết quả vào DB thay vì tính real-time
    - Hoặc để export báo cáo nhanh hơn
    """
    vai_tro = current_user.vai_tro

    if vai_tro.cap_bac not in [CapBacVaiTro.SUPER_ADMIN, CapBacVaiTro.CHI_CUC_TRUONG]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ CCT/SUPER_ADMIN mới được tính lại"
        )

    # Build query CC
    stmt = select(CongChuc).where(CongChuc.is_active == True)

    if request.don_vi_id:
        stmt = stmt.where(CongChuc.don_vi_id == request.don_vi_id)

    if request.cong_chuc_id:
        stmt = stmt.where(CongChuc.id == request.cong_chuc_id)

    result = await db.execute(stmt)
    cong_chucs = result.scalars().all()

    count_updated = 0

    for cc in cong_chucs:
        # Tính điểm quý
        ket_qua = await tinh_diem_quy(db, cc.id, request.quy, request.nam)

        # Upsert vào DB
        stmt_check = (
            select(DanhGiaQuy)
            .where(DanhGiaQuy.cong_chuc_id == cc.id)
            .where(DanhGiaQuy.quy == request.quy)
            .where(DanhGiaQuy.nam == request.nam)
        )
        result_check = await db.execute(stmt_check)
        existing = result_check.scalar_one_or_none()

        if existing:
            # Update
            existing.don_vi_id_snapshot = cc.don_vi_id
            existing.diem_kpi_quy = ket_qua["diem_kpi_quy"]
            existing.diem_tc_quy = ket_qua["diem_tc_quy"]
            existing.diem_tong_quy = ket_qua["diem_tong_quy"]
            existing.xep_loai_quy = ket_qua["xep_loai_quy"]
            existing.co_chuyen_don_vi = ket_qua["co_chuyen_don_vi"]
            existing.ghi_chu = ket_qua["ghi_chu"]
            existing.updated_at = datetime.utcnow()
        else:
            # Insert
            new_record = DanhGiaQuy(
                cong_chuc_id=cc.id,
                don_vi_id_snapshot=cc.don_vi_id,
                quy=request.quy,
                nam=request.nam,
                diem_kpi_quy=ket_qua["diem_kpi_quy"],
                diem_tc_quy=ket_qua["diem_tc_quy"],
                diem_tong_quy=ket_qua["diem_tong_quy"],
                xep_loai_quy=ket_qua["xep_loai_quy"],
                co_chuyen_don_vi=ket_qua["co_chuyen_don_vi"],
                ghi_chu=ket_qua["ghi_chu"],
            )
            db.add(new_record)

        count_updated += 1

    await db.commit()

    return success_response(
        data={
            "so_luong_tinh_lai": count_updated,
            "quy": request.quy,
            "nam": request.nam,
        },
        message=f"Đã tính lại điểm quý cho {count_updated} công chức"
    )
