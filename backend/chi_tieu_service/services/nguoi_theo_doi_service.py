"""
chi_tieu_service/services/nguoi_theo_doi_service.py
===================================================
Quan ly gan platform_role THEO_DOI_CHI_TIEU / QT_CHI_TIEU cho cong chuc.
Ghi vao public.cong_chuc_platform_role (bang platform — duoc phep ghi).
Doc public.cong_chuc / public.don_vi (READONLY).
"""

import json
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _err(code: str, msg: str, http=status.HTTP_400_BAD_REQUEST):
    return HTTPException(status_code=http, detail={"success": False, "error": {"code": code, "message": msg}})


class NguoiTheoDoiService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _role_id(self, ma_role: str) -> str:
        rid = (await self.db.execute(
            text("SELECT id FROM public.platform_role WHERE ma_role = :ma"), {"ma": ma_role}
        )).scalar_one_or_none()
        if not rid:
            raise _err("CT_ERR_ROLE", f"Khong tim thay platform_role '{ma_role}'", status.HTTP_404_NOT_FOUND)
        return str(rid)

    async def danh_sach(self, ma_role: str) -> list[dict]:
        """Liet ke cong chuc dang giu role + pham_vi.don_vi_ids."""
        rows = (await self.db.execute(text("""
            SELECT cpr.cong_chuc_id, cpr.pham_vi, cpr.is_active,
                   cc.ma_cc, cc.ho_ten, cc.chuc_vu, dv.ten_don_vi AS don_vi_cong_chuc
            FROM public.cong_chuc_platform_role cpr
            JOIN public.platform_role pr ON pr.id = cpr.platform_role_id
            JOIN public.cong_chuc cc ON cc.id = cpr.cong_chuc_id
            LEFT JOIN public.don_vi dv ON dv.id = cc.don_vi_id
            WHERE pr.ma_role = :ma AND cpr.is_active = TRUE
            ORDER BY cc.ho_ten
        """), {"ma": ma_role})).mappings().all()

        out = []
        for r in rows:
            pv = r["pham_vi"] or {}
            don_vi_ids = [str(x) for x in (pv.get("don_vi_ids", []) or [])] if isinstance(pv, dict) else []
            out.append({
                "cong_chuc_id": str(r["cong_chuc_id"]),
                "ma_cc": r["ma_cc"], "ho_ten": r["ho_ten"], "chuc_vu": r["chuc_vu"],
                "don_vi_cong_chuc": r["don_vi_cong_chuc"],
                "role": ma_role, "don_vi_ids": don_vi_ids, "is_active": r["is_active"],
            })
        return out

    async def _check_cong_chuc(self, cong_chuc_id: UUID) -> None:
        ok = (await self.db.execute(
            text("SELECT 1 FROM public.cong_chuc WHERE id = :id AND is_deleted = FALSE"),
            {"id": str(cong_chuc_id)},
        )).scalar_one_or_none()
        if not ok:
            raise _err("CT_ERR_CC", "Cong chuc khong ton tai", status.HTTP_404_NOT_FOUND)

    async def gan(self, cong_chuc_id: UUID, don_vi_ids: list[UUID], ma_role: str, assigned_by: UUID) -> dict:
        """Upsert role cho cong chuc. Neu da co row (cong_chuc, role) -> cap nhat pham_vi + bat is_active."""
        await self._check_cong_chuc(cong_chuc_id)
        role_id = await self._role_id(ma_role)
        pham_vi = json.dumps({"don_vi_ids": [str(d) for d in don_vi_ids]})

        existing = (await self.db.execute(text("""
            SELECT id FROM public.cong_chuc_platform_role
            WHERE cong_chuc_id = :cc AND platform_role_id = :role
        """), {"cc": str(cong_chuc_id), "role": role_id})).scalar_one_or_none()

        if existing:
            await self.db.execute(text("""
                UPDATE public.cong_chuc_platform_role
                SET pham_vi = CAST(:pv AS jsonb), is_active = TRUE,
                    assigned_by = :by, assigned_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """), {"pv": pham_vi, "by": str(assigned_by), "id": str(existing)})
        else:
            await self.db.execute(text("""
                INSERT INTO public.cong_chuc_platform_role
                    (id, cong_chuc_id, platform_role_id, pham_vi, assigned_by, assigned_at, is_active)
                VALUES (gen_random_uuid(), :cc, :role, CAST(:pv AS jsonb), :by, CURRENT_TIMESTAMP, TRUE)
            """), {"cc": str(cong_chuc_id), "role": role_id, "pv": pham_vi, "by": str(assigned_by)})

        await self.db.commit()
        return {"cong_chuc_id": str(cong_chuc_id), "role": ma_role, "don_vi_ids": [str(d) for d in don_vi_ids]}

    async def go(self, cong_chuc_id: UUID, ma_role: str) -> None:
        """Go role (is_active=FALSE) cho cong chuc."""
        role_id = await self._role_id(ma_role)
        res = await self.db.execute(text("""
            UPDATE public.cong_chuc_platform_role
            SET is_active = FALSE
            WHERE cong_chuc_id = :cc AND platform_role_id = :role AND is_active = TRUE
        """), {"cc": str(cong_chuc_id), "role": role_id})
        if (res.rowcount or 0) == 0:
            raise _err("CT_ERR_404", "Cong chuc chua duoc gan role nay", status.HTTP_404_NOT_FOUND)
        await self.db.commit()

    async def tim_cong_chuc(self, search: Optional[str], don_vi_id: Optional[UUID], limit: int = 30) -> list[dict]:
        """Tim cong chuc (READONLY public.cong_chuc) cho picker."""
        conds = ["cc.is_active = TRUE", "cc.is_deleted = FALSE"]
        params: dict = {"lim": limit}
        if search:
            conds.append("(cc.ho_ten ILIKE :q OR cc.ma_cc ILIKE :q)")
            params["q"] = f"%{search}%"
        if don_vi_id:
            conds.append("cc.don_vi_id = :dv")
            params["dv"] = str(don_vi_id)
        where = " AND ".join(conds)
        rows = (await self.db.execute(text(f"""
            SELECT cc.id, cc.ma_cc, cc.ho_ten, cc.chuc_vu, cc.don_vi_id, dv.ten_don_vi
            FROM public.cong_chuc cc
            LEFT JOIN public.don_vi dv ON dv.id = cc.don_vi_id
            WHERE {where}
            ORDER BY cc.ho_ten
            LIMIT :lim
        """), params)).mappings().all()
        return [
            {"id": str(r["id"]), "ma_cc": r["ma_cc"], "ho_ten": r["ho_ten"],
             "chuc_vu": r["chuc_vu"], "don_vi_id": str(r["don_vi_id"]) if r["don_vi_id"] else None,
             "ten_don_vi": r["ten_don_vi"]}
            for r in rows
        ]
