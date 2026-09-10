"""
app/api/v1/endpoints/admin_dieu_chuyen_hang_loat.py
===================================================
Điều chuyển nhân sự HÀNG LOẠT theo quyết định, bằng file Excel.

Ba bước, cố ý tách rời:
    GET  /admin/dieu-chuyen-hang-loat/mau-excel   tải mẫu 4 sheet
    POST /admin/dieu-chuyen-hang-loat/xem-truoc   đọc file, đối chiếu, KHÔNG ghi
    POST /admin/dieu-chuyen-hang-loat/ghi         ghi cả đợt trong MỘT transaction

VÌ SAO PHẢI QUA XEM TRƯỚC
-------------------------
Một file 142 dòng ghi thẳng mà sai thì hậu quả gấp 142 lần một lần nhập lẻ sai,
và khó phát hiện hơn nhiều vì không ai ngồi nhìn từng người. Bảng xem trước dội
lại HỌ TÊN + ĐƠN VỊ HIỆN TẠI của từng mã CC — đây là chỗ duy nhất phát hiện được
việc gõ nhầm một chữ số trong mã CC làm trỏ sang người khác.

Endpoint `ghi` tự đọc và đối chiếu lại từ đầu, không tin gì từ phía client.
Còn dòng lỗi thì từ chối cả đợt — thà bắt sửa file còn hơn ghi một nửa rồi để
người dùng tự đoán nửa nào đã vào.

Xem thêm: `app/core/dieu_chuyen_excel.py` (sinh mẫu + đọc file),
`app/core/dieu_chuyen.py` (hệ quả dữ liệu, dùng chung với điều chuyển lẻ).
"""

from __future__ import annotations

import io
from datetime import date

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.api.deps import AdminUserDep, DatabaseDep
from app.core.dieu_chuyen import don_dep_du_lieu_khi_chuyen_don_vi
from app.core.dieu_chuyen_excel import (
    DongNhap,
    KetQuaDoc,
    TrangThaiDong,
    doc_sheet_nhap_lieu,
    doi_chieu_voi_db,
    sinh_file_mau,
)
from app.models.admin import LichSuDieuChuyen
from app.models.user_org import CongChuc, DonVi
from app.schemas.common import error_response, success_response

router = APIRouter()

# Cùng hằng số với admin.py — tài khoản quản trị gốc không được đụng tới.
PROTECTED_ADMIN_MA_CC = "ADMIN-001"

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB — mẫu 4 sheet chỉ cỡ 40KB
MA_DON_VI_AN = {"DEPT-ADMIN"}          # đơn vị kỹ thuật, không phải nơi công tác


# =============================================================================
# Helpers
# =============================================================================

async def _tra_cuu(db) -> tuple[dict, dict, dict, list, list]:
    """Nạp sẵn bảng tra công chức + đơn vị (một lượt, tránh N+1)."""
    don_vi_rows = (await db.execute(
        select(DonVi).where(DonVi.is_deleted == False)  # noqa: E712
        .order_by(DonVi.ma_don_vi)
    )).scalars().all()
    don_vi_dung = [d for d in don_vi_rows if d.ma_don_vi not in MA_DON_VI_AN]

    cc_rows = (await db.execute(
        select(CongChuc).where(CongChuc.is_deleted == False)  # noqa: E712
        .order_by(CongChuc.ma_cc)
    )).scalars().all()

    cong_chuc_theo_ma = {c.ma_cc: c for c in cc_rows}
    don_vi_theo_ma = {d.ma_don_vi.upper(): d for d in don_vi_dung}
    ma_don_vi_theo_id = {d.id: d.ma_don_vi for d in don_vi_rows}

    return cong_chuc_theo_ma, don_vi_theo_ma, ma_don_vi_theo_id, cc_rows, don_vi_dung


async def _doc_va_doi_chieu(db, file: UploadFile) -> KetQuaDoc:
    """Dùng chung cho `xem-truoc` và `ghi` — đảm bảo hai bước đánh giá y hệt nhau."""
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="INVALID_FILE_TYPE",
                message="Chỉ nhận file .xlsx — hãy tải mẫu và điền vào đó",
            ),
        )

    noi_dung = await file.read()
    if len(noi_dung) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=error_response(
                code="FILE_TOO_LARGE",
                message=f"File quá lớn ({len(noi_dung) // 1024} KB), tối đa 5 MB",
            ),
        )

    cac_dong, loi_chung = doc_sheet_nhap_lieu(noi_dung)
    if loi_chung:
        kq = KetQuaDoc(dong=cac_dong, loi_chung=loi_chung)
        return kq

    cong_chuc_theo_ma, don_vi_theo_ma, ma_don_vi_theo_id, _, _ = await _tra_cuu(db)
    kq = doi_chieu_voi_db(
        cac_dong=cac_dong,
        cong_chuc_theo_ma=cong_chuc_theo_ma,
        don_vi_theo_ma=don_vi_theo_ma,
        ma_don_vi_theo_id=ma_don_vi_theo_id,
        ma_cc_cam={PROTECTED_ADMIN_MA_CC},
    )
    if not kq.dong:
        kq.loi_chung.append("Sheet 'Nhap lieu' không có dòng nào được điền")
    return kq


def _serialize(d: DongNhap) -> dict:
    return {
        "dong_excel": d.dong_excel,
        "ma_cc": d.ma_cc,
        "ho_ten": d.ho_ten,
        "don_vi_hien_tai": d.don_vi_hien_tai,
        "don_vi_den": d.don_vi_den_ma or d.don_vi_den_nhap,
        "ngay_hieu_luc": d.ngay_hieu_luc.isoformat() if d.ngay_hieu_luc else None,
        "so_qd": d.so_qd,
        "trang_thai": d.trang_thai,
        "loi": d.loi,
        "canh_bao": d.canh_bao,
    }


def _tom_tat(kq: KetQuaDoc) -> dict:
    ngay = sorted({
        d.ngay_hieu_luc for d in kq.dong
        if d.ngay_hieu_luc and d.trang_thai == TrangThaiDong.GHI_MOI
    })
    return {
        "tong_dong": len(kq.dong),
        "se_ghi": kq.so_ghi_moi,
        "bo_qua": kq.so_bo_qua,
        "loi": kq.so_loi,
        "ghi_duoc": kq.ghi_duoc,
        "cac_dot": [n.isoformat() for n in ngay],
        "loi_chung": kq.loi_chung,
    }


# =============================================================================
# 1. TẢI MẪU
# =============================================================================

@router.get(
    "/dieu-chuyen-hang-loat/mau-excel",
    summary="Tải file mẫu điều chuyển hàng loạt",
)
async def tai_mau_excel(db: DatabaseDep, admin: AdminUserDep) -> StreamingResponse:
    """
    Sinh mẫu 4 sheet. Sheet `Nhap lieu` để TRỐNG; danh sách công chức nằm ở
    sheet tra cứu riêng để người điền copy mã sang — không ai phải gõ mã CC.

    Danh sách chỉ gồm người CÒN HOẠT ĐỘNG, để không ai vô tình điều chuyển
    người đã nghỉ.
    """
    _, _, ma_don_vi_theo_id, cc_rows, don_vi_dung = await _tra_cuu(db)

    cong_chuc = [
        (c.ma_cc, c.ho_ten, ma_don_vi_theo_id.get(c.don_vi_id) or "")
        for c in cc_rows
        if c.is_active and c.ma_cc != PROTECTED_ADMIN_MA_CC
    ]
    don_vi = [(d.ma_don_vi, d.ten_don_vi) for d in don_vi_dung]

    noi_dung = sinh_file_mau(cong_chuc=cong_chuc, don_vi=don_vi)
    ten_file = f"mau_dieu_chuyen_hang_loat_{date.today():%Y%m%d}.xlsx"

    return StreamingResponse(
        io.BytesIO(noi_dung),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{ten_file}"'},
    )


# =============================================================================
# 2. XEM TRƯỚC
# =============================================================================

@router.post(
    "/dieu-chuyen-hang-loat/xem-truoc",
    summary="Đọc file và đối chiếu, KHÔNG ghi gì",
)
async def xem_truoc(
    db: DatabaseDep,
    admin: AdminUserDep,
    file: UploadFile = File(..., description="File .xlsx theo mẫu"),
) -> dict:
    kq = await _doc_va_doi_chieu(db, file)
    return success_response(
        data={
            "tom_tat": _tom_tat(kq),
            "cac_dong": [_serialize(d) for d in kq.dong],
        },
        message=(
            f"Đọc được {len(kq.dong)} dòng — {kq.so_ghi_moi} sẽ ghi, "
            f"{kq.so_bo_qua} bỏ qua, {kq.so_loi} lỗi"
        ),
    )


# =============================================================================
# 3. GHI
# =============================================================================

@router.post(
    "/dieu-chuyen-hang-loat/ghi",
    summary="Ghi cả đợt điều chuyển trong một transaction",
)
async def ghi_hang_loat(
    db: DatabaseDep,
    admin: AdminUserDep,
    file: UploadFile = File(..., description="File .xlsx theo mẫu"),
) -> dict:
    """
    Đọc và đối chiếu LẠI TỪ ĐẦU, không tin kết quả xem trước phía client.

    Còn bất kỳ dòng lỗi nào thì từ chối cả đợt: ghi một nửa rồi báo "62 dòng,
    59 thành công" là đẩy việc dò tìm ba dòng còn lại sang người dùng.
    """
    kq = await _doc_va_doi_chieu(db, file)

    if not kq.ghi_duoc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="ADMIN_020",
                message=(
                    f"Không ghi được: còn {kq.so_loi} dòng lỗi. Sửa file rồi tải lại."
                    if kq.so_loi
                    else "; ".join(kq.loi_chung) or "Không có dòng nào để ghi."
                ),
                # Chỉ trả các dòng HỎNG để giao diện chỉ thẳng chỗ cần sửa
                details=[
                    _serialize(d) for d in kq.dong
                    if d.trang_thai == TrangThaiDong.LOI
                ],
            ),
        )

    da_ghi: list[dict] = []
    try:
        for d in kq.dong:
            if d.trang_thai != TrangThaiDong.GHI_MOI:
                continue

            cc = (await db.execute(
                select(CongChuc).where(CongChuc.id == d.cong_chuc_id)
            )).scalar_one()

            don_vi_cu_id = cc.don_vi_id

            # Hệ quả dữ liệu — dùng CHUNG với điều chuyển lẻ
            await don_dep_du_lieu_khi_chuyen_don_vi(db, cc.id)

            cc.don_vi_id = d.don_vi_den_id

            db.add(LichSuDieuChuyen(
                loai="DIEU_CHUYEN",
                cong_chuc_id=cc.id,
                don_vi_cu_id=don_vi_cu_id,
                don_vi_moi_id=d.don_vi_den_id,
                # Quyết định điều động không nói gì về vai trò/chức vụ → không
                # khẳng định bừa, giữ nguyên hai đầu.
                vai_tro_cu_id=cc.vai_tro_id,
                vai_tro_moi_id=cc.vai_tro_id,
                chuc_vu_cu=cc.chuc_vu,
                chuc_vu_moi=cc.chuc_vu,
                ly_do=(
                    f"Theo QĐ số {d.so_qd}" if d.so_qd
                    else f"Đợt điều động {d.ngay_hieu_luc:%d/%m/%Y}"
                ),
                ngay_hieu_luc=d.ngay_hieu_luc,
                nguoi_thuc_hien_id=admin.id,
            ))

            da_ghi.append({
                "ma_cc": cc.ma_cc,
                "ho_ten": cc.ho_ten,
                "don_vi_den": d.don_vi_den_ma,
                "ngay_hieu_luc": d.ngay_hieu_luc.isoformat(),
            })

        await db.flush()
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code="DB_ERROR",
                message=f"Lỗi khi ghi, đã hoàn tác toàn bộ đợt: {e}",
            ),
        )

    return success_response(
        data={"so_da_ghi": len(da_ghi), "danh_sach": da_ghi, "bo_qua": kq.so_bo_qua},
        message=f"Đã điều chuyển {len(da_ghi)} công chức",
    )
