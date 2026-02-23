"""
lms_service/api/endpoints/bai_kiem_tra.py
=========================================
API endpoints cho BKT CRUD + luong thi.

Endpoints:
  GET    /khoa-hoc/{id}/bai-kiem-tra       Danh sach BKT cua khoa
  GET    /bai-kiem-tra/{id}                Chi tiet BKT
  POST   /khoa-hoc/{id}/bai-kiem-tra       Tao BKT moi
  PUT    /bai-kiem-tra/{id}                Cap nhat BKT
  DELETE /bai-kiem-tra/{id}                Xoa BKT
  POST   /bai-kiem-tra/{id}/bat-dau        Bat dau lam bai
  POST   /bai-kiem-tra/{id}/nop-bai        Nop bai
  GET    /ket-qua/{id}                     Xem ket qua chi tiet
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.dependencies import get_db, get_current_user, require_platform_role
from lms_service.schemas.bai_kiem_tra import (
    BaiKiemTraCreate,
    BaiKiemTraResponse,
    BaiKiemTraUpdate,
    BatDauResponse,
    KetQuaResponse,
    LichSuThiResponse,
    NopBaiRequest,
)
from lms_service.schemas.cau_hoi import CauHoiForExam, CauHoiResponse
from lms_service.services.bai_kiem_tra_service import BaiKiemTraService
from shared.auth import TokenPayload

router = APIRouter(tags=["Bài kiểm tra"])


@router.get("/khoa-hoc/{khoa_hoc_id}/bai-kiem-tra")
async def danh_sach_bkt(
    khoa_hoc_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Danh sách bài kiểm tra của khóa học. Kem thong ke ca nhan (so_lan_da_lam, diem_cao_nhat, da_dat)."""
    from uuid import UUID as _UUID
    service = BaiKiemTraService(db)
    result = await service.danh_sach(khoa_hoc_id, page, page_size, user_id=_UUID(user.sub))
    return {
        "success": True,
        "data": [BaiKiemTraResponse(**item).model_dump(mode="json") for item in result["items"]],
        "pagination": result["pagination"],
    }


@router.get("/bai-kiem-tra/{id}/cau-hoi")
async def danh_sach_cau_hoi_bkt(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Danh sách câu hỏi của bài kiểm tra (kèm đáp án — chỉ dành cho giảng viên quản trị)."""
    service = BaiKiemTraService(db)
    items = await service.danh_sach_cau_hoi(id)
    return {"success": True, "data": items}


@router.get("/bai-kiem-tra/{id}/ket-qua")
async def lich_su_thi_bkt(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Lịch sử làm bài kiểm tra của user hiện tại (tóm tắt + từng lần)."""
    service = BaiKiemTraService(db)
    result = await service.lich_su_thi(id, user)
    return {"success": True, "data": LichSuThiResponse(**result).model_dump(mode="json")}


@router.get("/bai-kiem-tra/{id}")
async def chi_tiet_bkt(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Chi tiết bài kiểm tra."""
    service = BaiKiemTraService(db)
    bkt = await service.chi_tiet(id)
    return {"success": True, "data": BaiKiemTraResponse.model_validate(bkt).model_dump(mode="json")}


@router.post("/khoa-hoc/{khoa_hoc_id}/bai-kiem-tra", status_code=201)
async def tao_bkt(
    khoa_hoc_id: UUID,
    data: BaiKiemTraCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Tạo bài kiểm tra + gắn câu hỏi."""
    # Override khoa_hoc_id tu path
    data.khoa_hoc_id = khoa_hoc_id
    service = BaiKiemTraService(db)
    bkt = await service.tao_moi(data, user)
    return {"success": True, "data": BaiKiemTraResponse.model_validate(bkt).model_dump(mode="json"), "message": "Tạo bài kiểm tra thành công"}


@router.put("/bai-kiem-tra/{id}")
async def cap_nhat_bkt(
    id: UUID,
    data: BaiKiemTraUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Cập nhật bài kiểm tra."""
    service = BaiKiemTraService(db)
    bkt = await service.cap_nhat(id, data, user)
    return {"success": True, "data": BaiKiemTraResponse.model_validate(bkt).model_dump(mode="json"), "message": "Cập nhật bài kiểm tra thành công"}


@router.delete("/bai-kiem-tra/{id}")
async def xoa_bkt(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Xóa bài kiểm tra."""
    service = BaiKiemTraService(db)
    await service.xoa(id, user)
    return {"success": True, "data": None, "message": "Xóa bài kiểm tra thành công"}


@router.post("/bai-kiem-tra/{id}/bat-dau")
async def bat_dau_thi(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Bắt đầu làm bài kiểm tra. Trả câu hỏi (không đáp án)."""
    service = BaiKiemTraService(db)
    result = await service.bat_dau_thi(id, user)
    return {
        "success": True,
        "data": BatDauResponse(
            ket_qua_id=result["ket_qua_id"],
            lan_thu=result["lan_thu"],
            thoi_gian_phut=result["thoi_gian_phut"],
            so_cau=result["so_cau"],
            cau_hoi=[CauHoiForExam(**ch) for ch in result["cau_hoi"]],
        ).model_dump(mode="json"),
    }


@router.post("/bai-kiem-tra/{id}/nop-bai")
async def nop_bai(
    id: UUID,
    data: NopBaiRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Nộp bài kiểm tra. Chấm điểm tự động."""
    service = BaiKiemTraService(db)
    result = await service.nop_bai(data.ket_qua_id, data.tra_loi, user)
    return {
        "success": True,
        "data": KetQuaResponse(**result).model_dump(mode="json"),
        "message": f"Nộp bài thành công. Điểm: {result['diem']}/{result.get('so_cau_dung', 0) + result.get('so_cau_sai', 0)} câu đúng",
    }


@router.get("/ket-qua/{id}")
async def ket_qua_chi_tiet(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Xem kết quả chi tiết bài thi."""
    service = BaiKiemTraService(db)
    result = await service.ket_qua_chi_tiet(id, user)
    return {"success": True, "data": KetQuaResponse(**result).model_dump(mode="json")}
