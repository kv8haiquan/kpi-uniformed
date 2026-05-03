"""
api/endpoints/cong_chuc.py
===========================
Helper search/list CBCC cho HKG — KHÔNG ghi audit log (read-only, type-ahead).

Endpoint: GET /api/v1/hop-khong-giay/cong-chuc/search
Params:
  - q          (Optional): từ khoá search ho_ten/ma_cc/email (ILIKE)
  - don_vi_id  (Optional): filter theo đơn vị
  - limit      (Default 20, max 200): cap số kết quả

Yêu cầu: ÍT NHẤT 1 trong q hoặc don_vi_id (tránh full-table dump).

Permission: mọi CBCC đã đăng nhập đều được phép search (G4-fix-7 — 2026-05-03).
Trước đây giới hạn cho lãnh đạo/admin/THU_KY_HOP; mở rộng để công chức thường
có thể tự tạo cuộc họp / pick thành phần. Endpoint chỉ trả thông tin cơ bản
đã có trong UI khác (sidebar, danh bạ), không có audit log do query rate cao.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text as sa_text

from meeting_service.dependencies import CurrentUserDep, DatabaseDep


router = APIRouter(prefix="/cong-chuc", tags=["CBCC search"])


# ──────────────────────────────────────────────────────────────────────
# ENDPOINT
# ──────────────────────────────────────────────────────────────────────

@router.get("/search", summary="Tìm/list CBCC theo q hoặc don_vi_id")
async def search_cong_chuc(
    db: DatabaseDep,
    _: CurrentUserDep,
    q: Optional[str] = Query(None, max_length=200,
                             description="Từ khoá: tên, mã CC, hoặc email (optional)"),
    don_vi_id: Optional[UUID] = Query(None,
                                       description="Filter theo đơn vị (optional)"),
    limit: int = Query(20, ge=1, le=200,
                       description="Số kết quả tối đa. Bump 200 cho list theo đơn vị."),
):
    """
    Search/list CBCC active. KHÔNG audit log (query rate cao).
    Yêu cầu ÍT NHẤT 1 trong q hoặc don_vi_id (tránh full-table dump).
    """
    q_clean = q.strip() if q else None

    if not q_clean and not don_vi_id:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": {"code": "MISSING_FILTER",
                    "message": "Phải truyền ít nhất 1 trong q hoặc don_vi_id"}},
        )

    # Build WHERE động — parameterized, SQL injection safe
    where_clauses = ["cc.is_active = TRUE", "cc.is_deleted = FALSE"]
    params: dict = {"limit": limit}

    if q_clean:
        where_clauses.append(
            "(cc.ho_ten ILIKE :pattern OR cc.ma_cc ILIKE :pattern"
            " OR cc.email ILIKE :pattern)"
        )
        params["pattern"] = f"%{q_clean}%"

    if don_vi_id:
        where_clauses.append("cc.don_vi_id = :don_vi_id")
        params["don_vi_id"] = str(don_vi_id)

    sql = f"""
        SELECT
            cc.id::text         AS id,
            cc.ho_ten           AS ho_ten,
            cc.ma_cc            AS ma_cc,
            cc.email            AS email,
            cc.chuc_vu          AS chuc_vu,
            cc.don_vi_id::text  AS don_vi_id,
            dv.ten_don_vi       AS ten_don_vi,
            vt.ma_vai_tro       AS ma_vai_tro,
            cc.is_lanh_dao      AS is_lanh_dao
          FROM public.cong_chuc cc
          LEFT JOIN public.don_vi  dv ON dv.id = cc.don_vi_id
          LEFT JOIN public.vai_tro vt ON vt.id = cc.vai_tro_id
         WHERE {' AND '.join(where_clauses)}
         ORDER BY cc.is_lanh_dao DESC, cc.ho_ten
         LIMIT :limit
    """

    result = await db.execute(sa_text(sql), params)
    items = [
        {
            "id": row.id,
            "ho_ten": row.ho_ten,
            "ma_cc": row.ma_cc,
            "email": row.email,
            "chuc_vu": row.chuc_vu,
            "don_vi_id": row.don_vi_id,
            "ten_don_vi": row.ten_don_vi,
            "ma_vai_tro": row.ma_vai_tro,
            "is_lanh_dao": row.is_lanh_dao,
        }
        for row in result.fetchall()
    ]
    return {"success": True, "data": items}


@router.get("/{cong_chuc_id}", summary="Lấy thông tin 1 CBCC theo id")
async def get_cong_chuc_by_id(
    cong_chuc_id: UUID,
    db: DatabaseDep,
    _: CurrentUserDep,
):
    """Hydrate 1 CBCC để FE hiển thị tên + mã thay vì UUID (form sửa cuộc họp,
    sửa biên bản, ...). Trả về cùng shape với /search.
    """
    sql = """
        SELECT
            cc.id::text         AS id,
            cc.ho_ten           AS ho_ten,
            cc.ma_cc            AS ma_cc,
            cc.email            AS email,
            cc.chuc_vu          AS chuc_vu,
            cc.don_vi_id::text  AS don_vi_id,
            dv.ten_don_vi       AS ten_don_vi,
            vt.ma_vai_tro       AS ma_vai_tro,
            cc.is_lanh_dao      AS is_lanh_dao
          FROM public.cong_chuc cc
          LEFT JOIN public.don_vi  dv ON dv.id = cc.don_vi_id
          LEFT JOIN public.vai_tro vt ON vt.id = cc.vai_tro_id
         WHERE cc.id = :id
         LIMIT 1
    """
    result = await db.execute(sa_text(sql), {"id": str(cong_chuc_id)})
    row = result.fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": {"code": "CONG_CHUC_NOT_FOUND",
                    "message": "Không tìm thấy CBCC"}},
        )
    return {
        "success": True,
        "data": {
            "id": row.id,
            "ho_ten": row.ho_ten,
            "ma_cc": row.ma_cc,
            "email": row.email,
            "chuc_vu": row.chuc_vu,
            "don_vi_id": row.don_vi_id,
            "ten_don_vi": row.ten_don_vi,
            "ma_vai_tro": row.ma_vai_tro,
            "is_lanh_dao": row.is_lanh_dao,
        },
    }
