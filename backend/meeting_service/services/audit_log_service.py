"""
audit_log_service.py
=====================
Wrapper INSERT trực tiếp vào common.audit_log với module='MEETING'.

Schema thật (xem Phụ lục A của HKG_DATABASE_DESIGN.md):
  module, hanh_dong, doi_tuong_loai, doi_tuong_id,
  nguoi_thuc_hien_id, ip_address, user_agent, chi_tiet (JSONB)
"""

import json
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


MODULE = "MEETING"


async def ghi_audit(
    db: AsyncSession,
    *,
    hanh_dong: str,
    nguoi_thuc_hien_id: UUID,
    doi_tuong_loai: Optional[str] = None,
    doi_tuong_id: Optional[UUID] = None,
    chi_tiet: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Ghi 1 audit log row. Caller chịu trách nhiệm flush/commit của session."""
    await db.execute(
        sa_text("""
            INSERT INTO common.audit_log
                (module, hanh_dong, doi_tuong_loai, doi_tuong_id,
                 nguoi_thuc_hien_id, ip_address, user_agent, chi_tiet)
            VALUES
                (:module, :hanh_dong, :doi_tuong_loai, :doi_tuong_id,
                 :nguoi_thuc_hien_id, :ip_address, :user_agent,
                 CAST(:chi_tiet AS JSONB))
        """),
        {
            "module": MODULE,
            "hanh_dong": hanh_dong,
            "doi_tuong_loai": doi_tuong_loai,
            "doi_tuong_id": str(doi_tuong_id) if doi_tuong_id else None,
            "nguoi_thuc_hien_id": str(nguoi_thuc_hien_id),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "chi_tiet": json.dumps(chi_tiet) if chi_tiet else None,
        },
    )
