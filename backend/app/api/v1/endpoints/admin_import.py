"""
app/api/v1/endpoints/admin_import.py
=====================================
Admin Excel import danh mục PL3 (Phase C — 28/04/2026).

Routes:
- POST /admin/danh-muc-pl3/import/dry-run  Upload, parse, validate; KHÔNG insert
- POST /admin/danh-muc-pl3/import/commit   Upload, parse, validate, insert (atomic)

Strategy: ON CONFLICT (ma_danh_muc) DO UPDATE — idempotent.
Giới hạn: file ≤ 10MB, 5000 rows.

LOCKED 13 — snapshot kê khai cũ KHÔNG bị ảnh hưởng khi admin import lại
(snapshot lưu ngay lúc tạo kê khai, immutable).
"""

import hashlib
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from sqlalchemy import text

from app.api.deps import AdminUserDep, DatabaseDep
from app.core.pl3_excel_parser import ParsedRow, ParseResult, parse_pl3_excel
from app.models.audit_log import AuditAction, AuditLog
from app.schemas.common import error_response, success_response


router = APIRouter()


# 10MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_ROWS = 5000


# =============================================================================
# Helpers
# =============================================================================

async def _read_and_validate_upload(file: UploadFile) -> bytes:
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="INVALID_FILE_TYPE", message="Chỉ chấp nhận file .xlsx"),
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=error_response(
                code="FILE_TOO_LARGE",
                message=f"File quá lớn: {len(content)} bytes > {MAX_FILE_SIZE_BYTES} bytes (10MB)",
            ),
        )
    return content


def _summarize(result: ParseResult, existing_ma_set: set[str]) -> dict:
    will_insert = sum(1 for r in result.rows if r.ma_danh_muc not in existing_ma_set)
    will_update = len(result.rows) - will_insert
    return {
        "total_rows_in_file": result.total_excel_rows,
        "valid": len(result.rows),
        "invalid": len(result.errors),
        "will_insert": will_insert,
        "will_update": will_update,
        "skipped": result.skipped_no_data + result.skipped_pre_section,
    }


def _serialize_errors(result: ParseResult, limit: int = 50) -> list[dict]:
    return [
        {"row": e.row, "ma_danh_muc": e.ma_danh_muc, "error": e.error}
        for e in result.errors[:limit]
    ]


def _serialize_preview(rows: list[ParsedRow], existing_ma_set: set[str], limit: int = 10) -> list[dict]:
    out = []
    for r in rows[:limit]:
        action = "update" if r.ma_danh_muc in existing_ma_set else "insert"
        out.append({
            "ma_danh_muc": r.ma_danh_muc,
            "ten_cong_viec": r.ten_cong_viec,
            "linh_vuc": r.linh_vuc,
            "nhom_pl3": r.nhom_pl3,
            "diem_cham": r.diem_cham,
            "he_so_quy_doi": float(r.he_so_quy_doi),
            "action": action,
        })
    return out


async def _existing_ma_set(db) -> set[str]:
    rows = (await db.execute(
        text(
            "SELECT ma_danh_muc FROM danh_muc_sp_cong_viec "
            "WHERE nguon_du_lieu='PL3' AND is_deleted=false"
        )
    )).scalars().all()
    return set(rows)


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/danh-muc-pl3/import/dry-run",
    summary="Dry-run import Excel PL3 (KHÔNG insert)",
)
async def import_pl3_dry_run(
    db: DatabaseDep,
    current_user: AdminUserDep,
    file: UploadFile = File(..., description="File .xlsx"),
) -> dict:
    content = await _read_and_validate_upload(file)
    file_hash = hashlib.sha256(content).hexdigest()

    try:
        result = parse_pl3_excel(content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="PARSE_FAILED", message=str(e)),
        )

    if len(result.rows) > MAX_ROWS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="TOO_MANY_ROWS",
                message=f"Có {len(result.rows)} rows hợp lệ > giới hạn {MAX_ROWS}",
            ),
        )

    existing = await _existing_ma_set(db)
    summary = _summarize(result, existing)

    return success_response(data={
        "summary": summary,
        "errors": _serialize_errors(result),
        "preview": _serialize_preview(result.rows, existing),
        "is_dry_run": True,
        "file_hash": file_hash,
    })


@router.post(
    "/danh-muc-pl3/import/commit",
    summary="Commit import Excel PL3 (insert/update atomic)",
)
async def import_pl3_commit(
    db: DatabaseDep,
    current_user: AdminUserDep,
    request: Request,
    file: UploadFile = File(...),
) -> dict:
    content = await _read_and_validate_upload(file)
    file_hash = hashlib.sha256(content).hexdigest()

    try:
        result = parse_pl3_excel(content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="PARSE_FAILED", message=str(e)),
        )

    if len(result.rows) > MAX_ROWS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="TOO_MANY_ROWS",
                message=f"Có {len(result.rows)} rows hợp lệ > giới hạn {MAX_ROWS}",
            ),
        )

    if result.errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="VALIDATION_FAILED",
                message=f"File có {len(result.errors)} lỗi. Sửa Excel rồi commit lại.",
                details=_serialize_errors(result, limit=50),
            ),
        )

    existing = await _existing_ma_set(db)
    summary = _summarize(result, existing)

    # Atomic: SQLAlchemy session begin → upsert → commit
    upsert_sql = text("""
        INSERT INTO danh_muc_sp_cong_viec (
            ma_danh_muc, ten_cong_viec, mo_ta,
            nguon_du_lieu, linh_vuc, ten_linh_vuc,
            nhiem_vu, cong_viec_chi_tiet, san_pham_dau_ra,
            nhom_pl3, khung_diem_toi_da,
            diem_cham, he_so_quy_doi,
            is_active, sp_chuan_id, don_vi_ap_dung_id
        ) VALUES (
            :ma_danh_muc, :ten_cong_viec, :mo_ta,
            :nguon_du_lieu, :linh_vuc, :ten_linh_vuc,
            :nhiem_vu, :cong_viec_chi_tiet, :san_pham_dau_ra,
            :nhom_pl3, :khung_diem_toi_da,
            :diem_cham, :he_so_quy_doi,
            :is_active, NULL, NULL
        )
        ON CONFLICT (ma_danh_muc) DO UPDATE SET
            ten_cong_viec = EXCLUDED.ten_cong_viec,
            mo_ta = EXCLUDED.mo_ta,
            nguon_du_lieu = EXCLUDED.nguon_du_lieu,
            linh_vuc = EXCLUDED.linh_vuc,
            ten_linh_vuc = EXCLUDED.ten_linh_vuc,
            nhiem_vu = EXCLUDED.nhiem_vu,
            cong_viec_chi_tiet = EXCLUDED.cong_viec_chi_tiet,
            san_pham_dau_ra = EXCLUDED.san_pham_dau_ra,
            nhom_pl3 = EXCLUDED.nhom_pl3,
            khung_diem_toi_da = EXCLUDED.khung_diem_toi_da,
            diem_cham = EXCLUDED.diem_cham,
            he_so_quy_doi = EXCLUDED.he_so_quy_doi,
            is_active = EXCLUDED.is_active,
            updated_at = NOW()
        RETURNING (xmax = 0) AS inserted
    """)

    inserted_count = 0
    updated_count = 0

    for r in result.rows:
        ret = (await db.execute(upsert_sql, {
            "ma_danh_muc": r.ma_danh_muc,
            "ten_cong_viec": r.ten_cong_viec,
            "mo_ta": r.mo_ta,
            "nguon_du_lieu": r.nguon_du_lieu,
            "linh_vuc": r.linh_vuc,
            "ten_linh_vuc": r.ten_linh_vuc,
            "nhiem_vu": r.nhiem_vu,
            "cong_viec_chi_tiet": r.cong_viec_chi_tiet,
            "san_pham_dau_ra": r.san_pham_dau_ra,
            "nhom_pl3": r.nhom_pl3,
            "khung_diem_toi_da": r.khung_diem_toi_da,
            "diem_cham": r.diem_cham,
            "he_so_quy_doi": r.he_so_quy_doi,
            "is_active": r.is_active,
        })).first()
        if ret and ret[0]:
            inserted_count += 1
        else:
            updated_count += 1

    # Audit log: ghi 1 record summary cho cả batch
    audit = AuditLog.create_log(
        table_name="danh_muc_sp_cong_viec",
        record_id=current_user.id,  # placeholder — không có 1 record cụ thể
        action=AuditAction.INSERT if inserted_count > updated_count else AuditAction.UPDATE,
        user_id=current_user.id,
        old_value=None,
        new_value={
            "import_type": "EXCEL_PL3",
            "file_hash": file_hash,
            "filename": file.filename,
            "summary": summary,
            "inserted": inserted_count,
            "updated": updated_count,
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(audit)
    await db.commit()

    final_summary = dict(summary)
    final_summary["actually_inserted"] = inserted_count
    final_summary["actually_updated"] = updated_count

    return success_response(data={
        "summary": final_summary,
        "errors": [],
        "preview": _serialize_preview(result.rows, existing),
        "is_dry_run": False,
        "file_hash": file_hash,
    }, message=f"Import thành công: {inserted_count} mới, {updated_count} cập nhật")
