"""
app/api/v1/endpoints/hdld_danh_gia.py
=====================================
API Endpoints cho đánh giá HĐLĐ 111 theo Bộ tiêu chí VB714 (QĐ 714/QĐ-CHQ, 08/5/2026).

Áp dụng từ tháng 5/2026. Luồng 1 cấp:
    NHAP → (HĐLĐ nộp, chọn TDV/PDV) → CHO_DUYET → (cấp quản lý) → DA_DUYET / TRA_LAI

Quy tắc:
- HĐLĐ tự chọn nhóm nghề I..VI; tiêu chí < 100% bắt buộc ghi chú.
- Cấp quản lý chấm cột riêng; nếu sửa khác điểm tự chấm phải ghi lý do.
- Giữ cả 2 cột điểm (tự đánh giá + cấp quản lý). Điểm chính thức = cột cấp quản lý.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.api.deps import DatabaseDep, ActiveUserDep
from app.core.hdld_vb714 import is_hdld_vb714_active, tb_3_tieu_chi, kpi_70_tu_tb
from app.core.thong_bao_helper import gui_thong_bao
from app.models.hdld import (
    HdldTieuChi, HdldDanhGia, HdldDanhGiaChiTiet,
    TrangThaiHdldDanhGia, TEN_NHOM_HDLD,
)
from app.models.user_org import CongChuc, VaiTro, CapBacVaiTro
from app.schemas.common import success_response, error_response
from app.schemas.hdld import (
    HdldTieuChiResponse, HdldTuDanhGiaRequest, HdldNopRequest,
    HdldDuyetRequest, HdldTraLaiRequest, HdldDanhGiaResponse,
    HdldChiTietResponse, CongChucBrief, NguoiDuyetOption,
)

router = APIRouter()


# =============================================================================
# HELPERS
# =============================================================================

def _require_hd_111(user: CongChuc):
    if not user.is_hd_111:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ HĐLĐ 111 mới dùng được chức năng này",
        )


def _check_thang_vb714(thang: int, nam: int):
    if not is_hdld_vb714_active(thang, nam):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bộ tiêu chí VB714 chỉ áp dụng từ tháng 5/2026",
        )


async def _build_response(db: DatabaseDep, dg: HdldDanhGia) -> dict:
    """Dựng HdldDanhGiaResponse dict, kèm tên tiêu chí từ hdld_tieu_chi."""
    # Map mô tả tiêu chí theo nhóm nghề (nếu đã chọn)
    ten_map: dict[int, tuple] = {}
    if dg.nhom_nghe:
        stmt = select(HdldTieuChi).where(
            HdldTieuChi.nhom == dg.nhom_nghe, HdldTieuChi.is_active == True
        )
        for tc in (await db.execute(stmt)).scalars().all():
            ten_map[tc.so_tt] = (tc.ten_tieu_chi, tc.mo_ta_chi_tiet)

    chi_tiets = []
    for ct in sorted(dg.chi_tiets, key=lambda x: x.so_tt):
        ten, mo_ta = ten_map.get(ct.so_tt, (None, None))
        chi_tiets.append(HdldChiTietResponse(
            so_tt=ct.so_tt, diem_tu=ct.diem_tu, ghi_chu_tu=ct.ghi_chu_tu,
            diem_ql=ct.diem_ql, ghi_chu_ql=ct.ghi_chu_ql, ly_do_sua=ct.ly_do_sua,
            ten_tieu_chi=ten, mo_ta_chi_tiet=mo_ta,
        ))

    resp = HdldDanhGiaResponse(
        id=dg.id, cong_chuc_id=dg.cong_chuc_id, thang=dg.thang, nam=dg.nam,
        nhom_nghe=dg.nhom_nghe,
        ten_nhom=TEN_NHOM_HDLD.get(dg.nhom_nghe) if dg.nhom_nghe else None,
        trang_thai=dg.trang_thai, nguoi_duyet_id=dg.nguoi_duyet_id,
        nguoi_duyet=CongChucBrief.model_validate(dg.nguoi_duyet) if dg.nguoi_duyet else None,
        cong_chuc=CongChucBrief.model_validate(dg.cong_chuc) if dg.cong_chuc else None,
        diem_tc_tb_tu=dg.diem_tc_tb_tu, diem_tc_tb_ql=dg.diem_tc_tb_ql,
        diem_kpi_70=dg.diem_kpi_70, ghi_chu=dg.ghi_chu, ly_do_tra_lai=dg.ly_do_tra_lai,
        ngay_nop=dg.ngay_nop, ngay_duyet=dg.ngay_duyet, chi_tiets=chi_tiets,
    )
    return resp.model_dump()


async def _get_or_create_nhap(
    db: DatabaseDep, cong_chuc_id: UUID, thang: int, nam: int
) -> HdldDanhGia:
    """Lấy bản đánh giá của tháng, tạo nháp nếu chưa có."""
    stmt = select(HdldDanhGia).where(
        HdldDanhGia.cong_chuc_id == cong_chuc_id,
        HdldDanhGia.thang == thang, HdldDanhGia.nam == nam,
    ).options(
        selectinload(HdldDanhGia.chi_tiets),
        selectinload(HdldDanhGia.nguoi_duyet),
        selectinload(HdldDanhGia.cong_chuc),
    )
    dg = (await db.execute(stmt)).scalar_one_or_none()
    if dg is None:
        dg = HdldDanhGia(
            cong_chuc_id=cong_chuc_id, thang=thang, nam=nam,
            trang_thai=TrangThaiHdldDanhGia.NHAP.value,
        )
        db.add(dg)
        await db.flush()
        await db.refresh(dg, ["chi_tiets", "nguoi_duyet", "cong_chuc"])
    return dg


# =============================================================================
# ENDPOINTS — HĐLĐ tự kê khai
# =============================================================================

@router.get("/tieu-chi")
async def list_tieu_chi(db: DatabaseDep, current_user: ActiveUserDep, nhom: str = Query(...)):
    """Lấy 3 tiêu chí của 1 nhóm nghề (kèm mô tả VB714)."""
    if nhom not in TEN_NHOM_HDLD:
        return error_response("VALIDATION_ERROR", "Nhóm nghề không hợp lệ (I..VI)")
    stmt = select(HdldTieuChi).where(
        HdldTieuChi.nhom == nhom, HdldTieuChi.is_active == True
    ).order_by(HdldTieuChi.so_tt)
    rows = (await db.execute(stmt)).scalars().all()
    data = {
        "nhom": nhom,
        "ten_nhom": TEN_NHOM_HDLD[nhom],
        "tieu_chi": [HdldTieuChiResponse.model_validate(r).model_dump() for r in rows],
    }
    return success_response(data)


@router.get("/nguoi-duyet")
async def list_nguoi_duyet(db: DatabaseDep, current_user: ActiveUserDep):
    """Danh sách người duyệt cho HĐLĐ tự chọn: TDV/PDV cùng đơn vị."""
    _require_hd_111(current_user)
    stmt = select(CongChuc).join(VaiTro).where(
        CongChuc.is_active == True,
        CongChuc.don_vi_id == current_user.don_vi_id,
        VaiTro.cap_bac.in_([CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI]),
    )
    rows = (await db.execute(stmt)).scalars().all()
    data = [
        NguoiDuyetOption(
            id=cc.id, ma_cc=cc.ma_cc, ho_ten=cc.ho_ten, chuc_vu=cc.chuc_vu,
            cap_bac=cc.vai_tro.cap_bac.value if cc.vai_tro else None,
        ).model_dump()
        for cc in rows
    ]
    return success_response(data)


@router.get("/danh-gia")
async def get_danh_gia(
    db: DatabaseDep, current_user: ActiveUserDep,
    thang: int = Query(..., ge=1, le=12), nam: int = Query(..., ge=2020, le=2100),
):
    """HĐLĐ lấy (hoặc khởi tạo nháp) bản đánh giá của tháng."""
    _require_hd_111(current_user)
    _check_thang_vb714(thang, nam)
    dg = await _get_or_create_nhap(db, current_user.id, thang, nam)
    await db.commit()
    return success_response(await _build_response(db, dg))


@router.put("/danh-gia/{dg_id}/tu-danh-gia")
async def tu_danh_gia(
    dg_id: UUID, payload: HdldTuDanhGiaRequest,
    db: DatabaseDep, current_user: ActiveUserDep,
):
    """HĐLĐ lưu nháp: nhóm nghề + 3 điểm tự chấm + ghi chú (validate ở schema)."""
    _require_hd_111(current_user)
    dg = await db.get(HdldDanhGia, dg_id, options=[selectinload(HdldDanhGia.chi_tiets)])
    if dg is None or dg.cong_chuc_id != current_user.id:
        return error_response("NOT_FOUND", "Không tìm thấy bản đánh giá")
    if dg.trang_thai not in (TrangThaiHdldDanhGia.NHAP.value, TrangThaiHdldDanhGia.TRA_LAI.value):
        return error_response("INVALID_STATE", "Chỉ sửa được khi ở trạng thái Nháp hoặc Bị trả lại")

    dg.nhom_nghe = payload.nhom_nghe
    dg.ghi_chu = payload.ghi_chu
    if dg.trang_thai == TrangThaiHdldDanhGia.TRA_LAI.value:
        dg.trang_thai = TrangThaiHdldDanhGia.NHAP.value
        dg.ly_do_tra_lai = None

    # Upsert 3 chi tiết (giữ điểm cấp quản lý nếu đã có — không nên có ở trạng thái này)
    ct_map = {ct.so_tt: ct for ct in dg.chi_tiets}
    for item in payload.chi_tiets:
        ct = ct_map.get(item.so_tt)
        if ct is None:
            ct = HdldDanhGiaChiTiet(danh_gia_id=dg.id, so_tt=item.so_tt)
            db.add(ct)
        ct.diem_tu = item.diem_tu
        ct.ghi_chu_tu = item.ghi_chu_tu

    dg.diem_tc_tb_tu = tb_3_tieu_chi([item.diem_tu for item in payload.chi_tiets])
    await db.commit()
    await db.refresh(dg, ["chi_tiets", "nguoi_duyet", "cong_chuc"])
    return success_response(await _build_response(db, dg), "Đã lưu tự đánh giá")


@router.post("/danh-gia/{dg_id}/nop")
async def nop_danh_gia(
    dg_id: UUID, payload: HdldNopRequest,
    db: DatabaseDep, current_user: ActiveUserDep,
):
    """HĐLĐ nộp: chọn người duyệt (TDV/PDV cùng đơn vị) → CHO_DUYET."""
    _require_hd_111(current_user)
    dg = await db.get(HdldDanhGia, dg_id, options=[selectinload(HdldDanhGia.chi_tiets)])
    if dg is None or dg.cong_chuc_id != current_user.id:
        return error_response("NOT_FOUND", "Không tìm thấy bản đánh giá")
    if dg.trang_thai not in (TrangThaiHdldDanhGia.NHAP.value, TrangThaiHdldDanhGia.TRA_LAI.value):
        return error_response("INVALID_STATE", "Chỉ nộp được khi ở trạng thái Nháp hoặc Bị trả lại")
    if not dg.nhom_nghe or len(dg.chi_tiets) != 3 or any(ct.diem_tu is None for ct in dg.chi_tiets):
        return error_response("INCOMPLETE", "Phải tự đánh giá đủ 3 tiêu chí trước khi nộp")

    # Validate người duyệt thuộc TDV/PDV cùng đơn vị
    nguoi_duyet = await db.get(CongChuc, payload.nguoi_duyet_id,
                               options=[selectinload(CongChuc.vai_tro)])
    if (nguoi_duyet is None or not nguoi_duyet.is_active
            or nguoi_duyet.don_vi_id != current_user.don_vi_id
            or not nguoi_duyet.vai_tro
            or nguoi_duyet.vai_tro.cap_bac not in (CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI)):
        return error_response("INVALID_APPROVER", "Người duyệt phải là Trưởng/Phó đơn vị cùng đơn vị")

    dg.nguoi_duyet_id = payload.nguoi_duyet_id
    dg.trang_thai = TrangThaiHdldDanhGia.CHO_DUYET.value
    dg.ngay_nop = datetime.now()
    await db.commit()
    await db.refresh(dg, ["chi_tiets", "nguoi_duyet", "cong_chuc"])

    await gui_thong_bao(
        nguoi_nhan_id=payload.nguoi_duyet_id,
        tieu_de=f"HĐLĐ {current_user.ho_ten} nộp đánh giá tháng {dg.thang}/{dg.nam}",
        noi_dung="Có bản tự đánh giá HĐLĐ chờ bạn duyệt.",
        link_url="/hdld/cho-duyet",
        doi_tuong_type="HDLD_DANH_GIA", doi_tuong_id=dg.id,
    )
    return success_response(await _build_response(db, dg), "Đã nộp, chờ cấp quản lý duyệt")


# =============================================================================
# ENDPOINTS — Cấp quản lý duyệt
# =============================================================================

@router.get("/cho-duyet")
async def list_cho_duyet(
    db: DatabaseDep, current_user: ActiveUserDep,
    thang: Optional[int] = Query(None, ge=1, le=12), nam: Optional[int] = Query(None, ge=2020, le=2100),
):
    """Cấp quản lý xem danh sách HĐLĐ chờ mình duyệt."""
    conds = [
        HdldDanhGia.nguoi_duyet_id == current_user.id,
        HdldDanhGia.trang_thai == TrangThaiHdldDanhGia.CHO_DUYET.value,
    ]
    if thang is not None:
        conds.append(HdldDanhGia.thang == thang)
    if nam is not None:
        conds.append(HdldDanhGia.nam == nam)
    stmt = select(HdldDanhGia).where(and_(*conds)).options(
        selectinload(HdldDanhGia.chi_tiets),
        selectinload(HdldDanhGia.cong_chuc),
        selectinload(HdldDanhGia.nguoi_duyet),
    ).order_by(HdldDanhGia.ngay_nop.desc())
    rows = (await db.execute(stmt)).scalars().all()
    data = [await _build_response(db, dg) for dg in rows]
    return success_response(data)


@router.post("/danh-gia/{dg_id}/duyet")
async def duyet_danh_gia(
    dg_id: UUID, payload: HdldDuyetRequest,
    db: DatabaseDep, current_user: ActiveUserDep,
):
    """Cấp quản lý chấm cột 'Cấp quản lý đánh giá' → DA_DUYET, chốt điểm KPI-70.

    Nếu diem_ql khác diem_tu thì bắt buộc ly_do_sua (validate tại đây vì cần so điểm tự chấm).
    """
    dg = await db.get(HdldDanhGia, dg_id, options=[selectinload(HdldDanhGia.chi_tiets)])
    if dg is None:
        return error_response("NOT_FOUND", "Không tìm thấy bản đánh giá")
    if dg.nguoi_duyet_id != current_user.id:
        return error_response("FORBIDDEN", "Bạn không phải người được chọn duyệt bản này")
    if dg.trang_thai != TrangThaiHdldDanhGia.CHO_DUYET.value:
        return error_response("INVALID_STATE", "Chỉ duyệt được bản đang chờ duyệt")

    ct_map = {ct.so_tt: ct for ct in dg.chi_tiets}
    for item in payload.chi_tiets:
        ct = ct_map.get(item.so_tt)
        if ct is None:
            return error_response("INCOMPLETE", f"Thiếu tiêu chí {item.so_tt} trong bản tự đánh giá")
        # Bắt buộc lý do nếu cấp quản lý sửa khác điểm tự chấm
        if ct.diem_tu is not None and Decimal(str(item.diem_ql)) != Decimal(str(ct.diem_tu)):
            if not (item.ly_do_sua and item.ly_do_sua.strip()):
                return error_response(
                    "REQUIRE_REASON",
                    f"Tiêu chí {item.so_tt}: sửa khác điểm tự chấm phải ghi lý do",
                )
            ct.ly_do_sua = item.ly_do_sua
        ct.diem_ql = item.diem_ql
        ct.ghi_chu_ql = item.ghi_chu_ql

    diem_tb_ql = tb_3_tieu_chi([item.diem_ql for item in payload.chi_tiets])
    dg.diem_tc_tb_ql = diem_tb_ql
    dg.diem_kpi_70 = kpi_70_tu_tb(diem_tb_ql)
    dg.trang_thai = TrangThaiHdldDanhGia.DA_DUYET.value
    dg.ngay_duyet = datetime.now()
    if payload.ghi_chu is not None:
        dg.ghi_chu = payload.ghi_chu
    await db.commit()
    await db.refresh(dg, ["chi_tiets", "nguoi_duyet", "cong_chuc"])

    await gui_thong_bao(
        nguoi_nhan_id=dg.cong_chuc_id,
        tieu_de=f"Đánh giá HĐLĐ tháng {dg.thang}/{dg.nam} đã được duyệt",
        noi_dung=f"Điểm KPI: {dg.diem_kpi_70}/70.",
        link_url="/ke-khai",
        doi_tuong_type="HDLD_DANH_GIA", doi_tuong_id=dg.id,
    )
    return success_response(await _build_response(db, dg), "Đã duyệt")


@router.post("/danh-gia/{dg_id}/tra-lai")
async def tra_lai_danh_gia(
    dg_id: UUID, payload: HdldTraLaiRequest,
    db: DatabaseDep, current_user: ActiveUserDep,
):
    """Cấp quản lý trả lại bản đánh giá (duyệt nhầm / cần bổ sung) → TRA_LAI."""
    dg = await db.get(HdldDanhGia, dg_id, options=[selectinload(HdldDanhGia.chi_tiets)])
    if dg is None:
        return error_response("NOT_FOUND", "Không tìm thấy bản đánh giá")
    if dg.nguoi_duyet_id != current_user.id:
        return error_response("FORBIDDEN", "Bạn không phải người được chọn duyệt bản này")
    if dg.trang_thai not in (TrangThaiHdldDanhGia.CHO_DUYET.value, TrangThaiHdldDanhGia.DA_DUYET.value):
        return error_response("INVALID_STATE", "Chỉ trả lại bản đang chờ duyệt hoặc đã duyệt")

    dg.trang_thai = TrangThaiHdldDanhGia.TRA_LAI.value
    dg.ly_do_tra_lai = payload.ly_do
    # Reset kết quả duyệt (cho phép HĐLĐ sửa & nộp lại)
    dg.diem_tc_tb_ql = None
    dg.diem_kpi_70 = None
    dg.ngay_duyet = None
    await db.commit()
    await db.refresh(dg, ["chi_tiets", "nguoi_duyet", "cong_chuc"])

    await gui_thong_bao(
        nguoi_nhan_id=dg.cong_chuc_id,
        tieu_de=f"Đánh giá HĐLĐ tháng {dg.thang}/{dg.nam} bị trả lại",
        noi_dung=f"Lý do: {payload.ly_do}",
        link_url="/ke-khai",
        doi_tuong_type="HDLD_DANH_GIA", doi_tuong_id=dg.id,
    )
    return success_response(await _build_response(db, dg), "Đã trả lại")


@router.get("/danh-gia/lich-su")
async def lich_su(
    db: DatabaseDep, current_user: ActiveUserDep,
    nam: Optional[int] = Query(None, ge=2020, le=2100),
):
    """HĐLĐ xem lịch sử đánh giá của chính mình."""
    _require_hd_111(current_user)
    conds = [HdldDanhGia.cong_chuc_id == current_user.id]
    if nam is not None:
        conds.append(HdldDanhGia.nam == nam)
    stmt = select(HdldDanhGia).where(and_(*conds)).options(
        selectinload(HdldDanhGia.chi_tiets),
        selectinload(HdldDanhGia.nguoi_duyet),
        selectinload(HdldDanhGia.cong_chuc),
    ).order_by(HdldDanhGia.nam.desc(), HdldDanhGia.thang.desc())
    rows = (await db.execute(stmt)).scalars().all()
    data = [await _build_response(db, dg) for dg in rows]
    return success_response(data)
