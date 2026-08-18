"""
api/endpoints/lich_cong_tac.py
===============================
Lịch công tác — di trú từ lichkv8.

Đọc trên cùng bảng `meeting.cuoc_hop` với Họp Không Giấy nên cuộc họp HKG tự
hiện lên lịch, không cần đồng bộ. Sự kiện nguồn HKG có cờ `co_the_mo_hkg` để
giao diện điều hướng thẳng sang màn hình chi tiết cuộc họp (tiêu chí 8.3).
"""

from datetime import date as date_type
from datetime import timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from meeting_service.dependencies import CurrentUserDep, DatabaseDep
from meeting_service.schemas.lich_cong_tac import (
    LOAI_LICH_VALUES,
    NHAN_LOAI_LICH,
)
from meeting_service.services.lich_cong_tac_service import LichCongTacService

router = APIRouter(prefix="/lich-cong-tac", tags=["Lịch công tác"])


@router.get("/", summary="Danh sách sự kiện trên lịch")
async def danh_sach(
    db: DatabaseDep,
    user: CurrentUserDep,
    tu_ngay: Optional[date_type] = Query(None, alias="tu-ngay"),
    den_ngay: Optional[date_type] = Query(None, alias="den-ngay"),
    loai_lich: Optional[str] = Query(None, alias="loai-lich"),
    trang_thai: Optional[str] = Query(None, alias="trang-thai"),
    lanh_dao_id: Optional[UUID] = Query(None, alias="lanh-dao-id"),
    tim_kiem: Optional[str] = Query(None, alias="tim-kiem"),
    nguon: Optional[str] = Query(None),
    trang: int = Query(1, ge=1),
    so_dong: int = Query(50, ge=1, le=500, alias="so-dong"),
):
    """Phân trang phía máy chủ.

    Hệ cũ tải toàn bộ mảng cuộc họp vào bộ nhớ trình duyệt và có ngưỡng cảnh
    báo hiệu năng 3000ms — không lặp lại cách đó.
    """
    if loai_lich and loai_lich not in LOAI_LICH_VALUES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {
                "code": "LOAI_LICH_KHONG_HOP_LE",
                "message": f"loai_lich phải thuộc {LOAI_LICH_VALUES}"}})

    svc = LichCongTacService(db)
    items, tong = await svc.danh_sach(
        trang=trang, so_dong=so_dong,
        tu_ngay=tu_ngay, den_ngay=den_ngay, loai_lich=loai_lich,
        trang_thai=trang_thai, lanh_dao_id=lanh_dao_id, tim_kiem=tim_kiem,
        nguon=nguon,
    )
    return {
        "success": True,
        "data": items,
        "pagination": {
            "page": trang,
            "page_size": so_dong,
            "total_items": tong,
            "total_pages": (tong + so_dong - 1) // so_dong,
        },
    }


@router.get("/thang/{nam}/{thang}", summary="Lịch theo tháng")
async def theo_thang(
    nam: int,
    thang: int,
    db: DatabaseDep,
    user: CurrentUserDep,
    loai_lich: Optional[str] = Query(None, alias="loai-lich"),
    lanh_dao_id: Optional[UUID] = Query(None, alias="lanh-dao-id"),
):
    if not 1 <= thang <= 12:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {
                "code": "THANG_KHONG_HOP_LE", "message": "Tháng phải từ 1 đến 12"}})

    dau = date_type(nam, thang, 1)
    cuoi = (date_type(nam + (thang == 12), (thang % 12) + 1, 1)
            - timedelta(days=1))

    svc = LichCongTacService(db)
    items, tong = await svc.danh_sach(
        trang=1, so_dong=500, tu_ngay=dau, den_ngay=cuoi,
        loai_lich=loai_lich, lanh_dao_id=lanh_dao_id)

    # Gom theo ngày để giao diện lịch tháng render thẳng. Sự kiện nhiều ngày
    # xuất hiện ở mọi ngày nó kéo dài.
    theo_ngay: dict[str, list] = {}
    for it in items:
        bd = it["ngay_hien_thi"] or it["ngay_hop"]
        kt = it["ngay_ket_thuc"] or bd
        n = max(bd, dau)
        while n <= min(kt, cuoi):
            theo_ngay.setdefault(n.isoformat(), []).append(it)
            n += timedelta(days=1)

    return {"success": True,
            "data": {"nam": nam, "thang": thang, "tong": tong,
                     "theo_ngay": theo_ngay}}


@router.get("/tom-tat", summary="Tóm tắt lịch để gửi nhanh")
async def tom_tat(
    db: DatabaseDep,
    user: CurrentUserDep,
    tu_ngay: Optional[date_type] = Query(None, alias="tu-ngay"),
    so_ngay: int = Query(3, ge=1, le=31, alias="so-ngay"),
    chi_da_dang: bool = Query(True, alias="chi-da-dang"),
    kem_truc_ban: bool = Query(True, alias="kem-truc-ban"),
):
    """Mặc định 3 ngày — giữ đúng cấu hình của lichkv8."""
    bd = tu_ngay or date_type.today()
    svc = LichCongTacService(db)
    return {"success": True,
            "data": await svc.tom_tat(bd, bd + timedelta(days=so_ngay - 1),
                                      chi_da_dang=chi_da_dang,
                                      kem_truc_ban=kem_truc_ban)}


@router.get("/lanh-dao/{lanh_dao_id}", summary="Chương trình công tác của một lãnh đạo")
async def lich_lanh_dao(
    lanh_dao_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
    tu_ngay: Optional[date_type] = Query(None, alias="tu-ngay"),
    so_ngay: int = Query(7, ge=1, le=90, alias="so-ngay"),
):
    bd = tu_ngay or date_type.today()
    svc = LichCongTacService(db)
    return {"success": True,
            "data": await svc.lich_lanh_dao(lanh_dao_id, bd,
                                            bd + timedelta(days=so_ngay - 1))}


@router.get("/thong-ke", summary="Chỉ số tổng quan")
async def thong_ke(db: DatabaseDep, user: CurrentUserDep):
    svc = LichCongTacService(db)
    return {"success": True, "data": await svc.thong_ke()}


@router.get("/danh-muc", summary="Danh mục loại lịch")
async def danh_muc(user: CurrentUserDep):
    return {"success": True,
            "data": [{"ma": k, "ten": v} for k, v in NHAN_LOAI_LICH.items()]}


@router.get("/{cuoc_hop_id}", summary="Chi tiết một sự kiện")
async def chi_tiet(cuoc_hop_id: UUID, db: DatabaseDep, user: CurrentUserDep):
    svc = LichCongTacService(db)
    item = await svc.chi_tiet(cuoc_hop_id)
    if not item:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {
                "code": "KHONG_TIM_THAY",
                "message": "Không tìm thấy sự kiện trên lịch"}})
    return {"success": True, "data": item}
