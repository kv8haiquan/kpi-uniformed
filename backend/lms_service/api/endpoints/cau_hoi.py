"""
lms_service/api/endpoints/cau_hoi.py
====================================
API endpoints cho CRUD ngan hang cau hoi + import hang loat.

Endpoints:
  GET    /cau-hoi                Danh sach cau hoi
  POST   /cau-hoi                Tao cau hoi
  GET    /cau-hoi/import/mau     Download file mau import (xlsx)
  POST   /cau-hoi/import         Import hang loat tu file Excel/CSV
  GET    /cau-hoi/{id}           Chi tiet cau hoi
  PUT    /cau-hoi/{id}           Cap nhat cau hoi
  DELETE /cau-hoi/{id}           Xoa cau hoi (soft)

LƯU Ý QUAN TRỌNG: Route /cau-hoi/import và /cau-hoi/import/mau PHẢI đứng
TRƯỚC route /cau-hoi/{id}, nếu không FastAPI sẽ parse "import" như một {id}.
"""

import io
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.dependencies import get_db, require_platform_role
from lms_service.schemas.cau_hoi import CauHoiCreate, CauHoiResponse, CauHoiUpdate
from lms_service.services.cau_hoi_service import CauHoiService
from lms_service.services.import_cau_hoi_service import ImportCauHoiService
from shared.auth import TokenPayload

router = APIRouter(prefix="/cau-hoi", tags=["Câu hỏi"])


# =============================================================================
# GET /cau-hoi — Danh sach cau hoi
# =============================================================================

@router.get("")
async def danh_sach_cau_hoi(
    khoa_hoc_id: Optional[UUID] = Query(None),
    chuyen_de_id: Optional[UUID] = Query(None),
    bai_kiem_tra_id: Optional[UUID] = Query(None),
    loai: Optional[str] = Query(None),
    do_kho: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Ngân hàng câu hỏi. Auth: GIANG_VIEN, QT_DAO_TAO."""
    service = CauHoiService(db)
    result = await service.danh_sach(khoa_hoc_id, chuyen_de_id, bai_kiem_tra_id, loai, do_kho, page, page_size)
    return {
        "success": True,
        "data": [CauHoiResponse(**item).model_dump(mode="json") for item in result["items"]],
        "pagination": result["pagination"],
    }


# =============================================================================
# POST /cau-hoi — Tao cau hoi moi
# =============================================================================

@router.post("", status_code=201)
async def tao_cau_hoi(
    data: CauHoiCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Tạo câu hỏi mới."""
    service = CauHoiService(db)
    ch = await service.tao_moi(data, user)
    return {
        "success": True,
        "data": CauHoiResponse.model_validate(ch).model_dump(mode="json"),
        "message": "Tạo câu hỏi thành công",
    }


# =============================================================================
# GET /cau-hoi/import/mau — Download file mau import
# QUAN TRONG: phai dat TRUOC route /{id}
# =============================================================================

@router.get("/import/mau")
async def download_mau_import(
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """
    Download file Excel mẫu để import câu hỏi hàng loạt.

    File có header + 3 dòng mẫu minh hoạ cách điền.
    """
    service = ImportCauHoiService()
    xlsx_bytes = service.generate_template_xlsx()

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.document",
        headers={"Content-Disposition": "attachment; filename=mau_import_cau_hoi.xlsx"},
    )


# =============================================================================
# POST /cau-hoi/import — Import hang loat tu file Excel/CSV
# QUAN TRONG: phai dat TRUOC route /{id}
# =============================================================================

@router.post("/import", status_code=201)
async def import_cau_hoi(
    file: UploadFile = File(..., description="File .xlsx hoặc .csv chứa danh sách câu hỏi"),
    khoa_hoc_id: Optional[str] = Query(
        default=None,
        description="UUID khóa học — gắn toàn bộ câu hỏi vào khóa học này (tuỳ chọn)",
    ),
    bai_kiem_tra_id: Optional[str] = Query(
        default=None,
        description="UUID bài kiểm tra — gắn toàn bộ câu hỏi vào BKT này (tuỳ chọn, tự lấy khoa_hoc_id từ BKT)",
    ),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """
    Import câu hỏi hàng loạt từ file Excel (.xlsx) hoặc CSV (.csv).

    POST /api/v1/lms/cau-hoi/import?bai_kiem_tra_id=<uuid>
    POST /api/v1/lms/cau-hoi/import?khoa_hoc_id=<uuid>
    Content-Type: multipart/form-data

    Format cột:
      noi_dung | loai | dap_an_a | dap_an_b | dap_an_c | dap_an_d | dap_an_dung | do_kho | diem | giai_thich

    Giá trị loai: TRAC_NGHIEM_1 | TRAC_NGHIEM_NHIEU | DUNG_SAI | TU_LUAN
    Giá trị dap_an_dung:
      - TRAC_NGHIEM_1: A | B | C | D
      - TRAC_NGHIEM_NHIEU: A,C | A,B,D
      - DUNG_SAI: A (Đúng) | B (Sai)
      - TU_LUAN: text gợi ý đáp án

    Response: { thanh_cong, that_bai, tong, loi_chi_tiet }
    """
    service = ImportCauHoiService()
    result = await service.import_from_file(
        file=file,
        khoa_hoc_id=khoa_hoc_id,
        bai_kiem_tra_id=bai_kiem_tra_id,
        db=db,
        user_id=user.sub,
    )

    return {
        "success": True,
        "data": result,
        "message": f"Import hoàn tất: {result['thanh_cong']}/{result['tong']} câu thành công",
    }


# =============================================================================
# GET /cau-hoi/{id} — Chi tiet
# =============================================================================

@router.get("/{id}")
async def chi_tiet_cau_hoi(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Chi tiết câu hỏi (kèm đáp án)."""
    service = CauHoiService(db)
    ch = await service.chi_tiet(id)
    return {"success": True, "data": CauHoiResponse.model_validate(ch).model_dump(mode="json")}


# =============================================================================
# PUT /cau-hoi/{id} — Cap nhat
# =============================================================================

@router.put("/{id}")
async def cap_nhat_cau_hoi(
    id: UUID,
    data: CauHoiUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Cập nhật câu hỏi."""
    service = CauHoiService(db)
    ch = await service.cap_nhat(id, data, user)
    return {
        "success": True,
        "data": CauHoiResponse.model_validate(ch).model_dump(mode="json"),
        "message": "Cập nhật câu hỏi thành công",
    }


# =============================================================================
# DELETE /cau-hoi/{id} — Xoa (soft)
# =============================================================================

@router.delete("/{id}")
async def xoa_cau_hoi(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Xóa câu hỏi (soft delete)."""
    service = CauHoiService(db)
    await service.xoa(id, user)
    return {"success": True, "data": None, "message": "Xóa câu hỏi thành công"}
