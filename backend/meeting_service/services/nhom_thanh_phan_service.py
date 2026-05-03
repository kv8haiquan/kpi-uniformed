"""
nhom_thanh_phan_service.py
============================
Business logic cho nhóm thành phần dùng chung.

CRUD nhóm + chi tiết. Helper merge_into_cuoc_hop() để gộp 1+ nhóm vào
1 cuộc họp với 2 quy tắc:
- Skip thành viên trùng (đã tồn tại trong meeting.thanh_phan) — KHÔNG ghi đè.
- Auto-fill cuoc_hop.chu_toa_id (nếu NULL) từ vai_tro=CHU_TRI;
  auto-fill thu_ky_id từ vai_tro=THU_KY.

Permission: KHÔNG check ownership — mọi công chức đều CRUD được mọi nhóm.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.models.nhom_thanh_phan import (
    NhomThanhPhan,
    NhomThanhPhanChiTiet,
)
from meeting_service.models.thanh_phan import ThanhPhan
from meeting_service.schemas.nhom_thanh_phan import (
    ChiTietBatchResponse,
    ChiTietCreate,
    ChiTietUpdate,
    NhomCreate,
    NhomUpdate,
    ThemTuNhomResponse,
)
from meeting_service.services.audit_log_service import ghi_audit
from shared.auth import TokenPayload


def _err(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"code": code, "message": message}},
    )


class NhomThanhPhanService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ──────────────────────────────────────────────────────────────────
    # CRUD nhóm
    # ──────────────────────────────────────────────────────────────────
    async def tao_moi(self, data: NhomCreate, user: TokenPayload) -> NhomThanhPhan:
        # Validate trùng cong_chuc_id trong cùng request
        seen: set[UUID] = set()
        for tp in data.chi_tiet:
            if tp.cong_chuc_id in seen:
                raise _err(400, "DUPLICATE_MEMBER",
                           f"Công chức {tp.cong_chuc_id} bị lặp trong danh sách")
            seen.add(tp.cong_chuc_id)

        nhom = NhomThanhPhan(
            ten_nhom=data.ten_nhom.strip(),
            mo_ta=data.mo_ta,
            loai_nhom=data.loai_nhom,
            nguoi_tao_id=UUID(user.sub),
        )
        self.db.add(nhom)
        await self.db.flush()

        for tp in data.chi_tiet:
            self.db.add(NhomThanhPhanChiTiet(
                nhom_id=nhom.id,
                cong_chuc_id=tp.cong_chuc_id,
                vai_tro=tp.vai_tro,
                loai_tham_du=tp.loai_tham_du,
            ))

        await ghi_audit(
            self.db,
            hanh_dong="CREATE_NHOM_THANH_PHAN",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="nhom_thanh_phan",
            doi_tuong_id=nhom.id,
            chi_tiet={"ten_nhom": data.ten_nhom, "so_thanh_vien": len(data.chi_tiet)},
        )
        await self.db.flush()
        return nhom

    async def danh_sach(
        self,
        *,
        page: int = 1,
        limit: int = 20,
        q: Optional[str] = None,
        loai_nhom: Optional[str] = None,
    ) -> dict:
        """List nhóm + so_thanh_vien + nguoi_tao_ho_ten qua 1 query SQL raw."""
        where = ["1=1"]
        params: dict = {"limit": limit, "offset": (page - 1) * limit}

        if q:
            where.append("n.ten_nhom ILIKE :pattern")
            params["pattern"] = f"%{q.strip()}%"
        if loai_nhom:
            where.append("n.loai_nhom = :loai_nhom")
            params["loai_nhom"] = loai_nhom

        where_sql = " AND ".join(where)

        sql = sa_text(f"""
            SELECT
                n.id::text                                  AS id,
                n.ten_nhom                                  AS ten_nhom,
                n.mo_ta                                     AS mo_ta,
                n.loai_nhom                                 AS loai_nhom,
                n.nguoi_tao_id::text                        AS nguoi_tao_id,
                n.created_at                                AS created_at,
                n.updated_at                                AS updated_at,
                cc.ho_ten                                   AS nguoi_tao_ho_ten,
                COALESCE(cnt.so_thanh_vien, 0)              AS so_thanh_vien
              FROM meeting.nhom_thanh_phan n
              LEFT JOIN public.cong_chuc cc ON cc.id = n.nguoi_tao_id
              LEFT JOIN (
                  SELECT nhom_id, COUNT(*) AS so_thanh_vien
                    FROM meeting.nhom_thanh_phan_chi_tiet
                   GROUP BY nhom_id
              ) cnt ON cnt.nhom_id = n.id
             WHERE {where_sql}
             ORDER BY n.updated_at DESC
             LIMIT :limit OFFSET :offset
        """)

        count_sql = sa_text(f"""
            SELECT COUNT(*) FROM meeting.nhom_thanh_phan n WHERE {where_sql}
        """)

        result = await self.db.execute(sql, params)
        rows = result.fetchall()

        total_result = await self.db.execute(count_sql, params)
        total = total_result.scalar() or 0

        items = [
            {
                "id": UUID(row.id),
                "ten_nhom": row.ten_nhom,
                "mo_ta": row.mo_ta,
                "loai_nhom": row.loai_nhom,
                "nguoi_tao_id": UUID(row.nguoi_tao_id),
                "nguoi_tao_ho_ten": row.nguoi_tao_ho_ten,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "so_thanh_vien": int(row.so_thanh_vien),
            }
            for row in rows
        ]
        return {
            "items": items,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
            },
        }

    async def chi_tiet(self, nhom_id: UUID) -> dict:
        """Lấy nhóm + danh sách chi tiết kèm thông tin CBCC."""
        nhom = await self.db.get(NhomThanhPhan, nhom_id)
        if nhom is None:
            raise _err(404, "NHOM_NOT_FOUND", "Không tìm thấy nhóm thành phần")

        members_result = await self.db.execute(sa_text("""
            SELECT
                ct.id::text             AS id,
                ct.nhom_id::text        AS nhom_id,
                ct.cong_chuc_id::text   AS cong_chuc_id,
                ct.vai_tro              AS vai_tro,
                ct.loai_tham_du         AS loai_tham_du,
                ct.created_at           AS created_at,
                cc.ho_ten               AS ho_ten,
                cc.ma_cc                AS ma_cc,
                cc.don_vi_id::text      AS don_vi_id,
                dv.ten_don_vi           AS ten_don_vi,
                cc.chuc_vu              AS chuc_vu
              FROM meeting.nhom_thanh_phan_chi_tiet ct
              LEFT JOIN public.cong_chuc cc ON cc.id = ct.cong_chuc_id
              LEFT JOIN public.don_vi    dv ON dv.id = cc.don_vi_id
             WHERE ct.nhom_id = :nhom_id
             ORDER BY
                CASE ct.vai_tro
                    WHEN 'CHU_TRI' THEN 1
                    WHEN 'THU_KY' THEN 2
                    ELSE 3
                END,
                cc.ho_ten
        """), {"nhom_id": str(nhom_id)})

        chi_tiet = [
            {
                "id": UUID(r.id),
                "nhom_id": UUID(r.nhom_id),
                "cong_chuc_id": UUID(r.cong_chuc_id),
                "vai_tro": r.vai_tro,
                "loai_tham_du": r.loai_tham_du,
                "created_at": r.created_at,
                "ho_ten": r.ho_ten,
                "ma_cc": r.ma_cc,
                "don_vi_id": UUID(r.don_vi_id) if r.don_vi_id else None,
                "ten_don_vi": r.ten_don_vi,
                "chuc_vu": r.chuc_vu,
            }
            for r in members_result.fetchall()
        ]

        return {
            "id": nhom.id,
            "ten_nhom": nhom.ten_nhom,
            "mo_ta": nhom.mo_ta,
            "loai_nhom": nhom.loai_nhom,
            "nguoi_tao_id": nhom.nguoi_tao_id,
            "created_at": nhom.created_at,
            "updated_at": nhom.updated_at,
            "chi_tiet": chi_tiet,
        }

    async def cap_nhat(
        self, nhom_id: UUID, data: NhomUpdate, user: TokenPayload
    ) -> NhomThanhPhan:
        nhom = await self.db.get(NhomThanhPhan, nhom_id)
        if nhom is None:
            raise _err(404, "NHOM_NOT_FOUND", "Không tìm thấy nhóm thành phần")

        if data.ten_nhom is not None:
            nhom.ten_nhom = data.ten_nhom.strip()
        if data.mo_ta is not None:
            nhom.mo_ta = data.mo_ta
        if data.loai_nhom is not None:
            nhom.loai_nhom = data.loai_nhom or None  # empty string → NULL
        nhom.updated_at = datetime.now(timezone.utc)

        await ghi_audit(
            self.db,
            hanh_dong="UPDATE_NHOM_THANH_PHAN",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="nhom_thanh_phan",
            doi_tuong_id=nhom.id,
            chi_tiet={"ten_nhom": nhom.ten_nhom},
        )
        await self.db.flush()
        return nhom

    async def xoa(self, nhom_id: UUID, user: TokenPayload) -> None:
        nhom = await self.db.get(NhomThanhPhan, nhom_id)
        if nhom is None:
            raise _err(404, "NHOM_NOT_FOUND", "Không tìm thấy nhóm thành phần")

        ten = nhom.ten_nhom
        await self.db.delete(nhom)  # cascade chi_tiet qua FK ON DELETE CASCADE

        await ghi_audit(
            self.db,
            hanh_dong="DELETE_NHOM_THANH_PHAN",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="nhom_thanh_phan",
            doi_tuong_id=nhom_id,
            chi_tiet={"ten_nhom": ten},
        )
        await self.db.flush()

    # ──────────────────────────────────────────────────────────────────
    # CRUD chi tiết (thành viên trong nhóm)
    # ──────────────────────────────────────────────────────────────────
    async def them_thanh_vien(
        self, nhom_id: UUID, data: ChiTietCreate, user: TokenPayload
    ) -> NhomThanhPhanChiTiet:
        nhom = await self.db.get(NhomThanhPhan, nhom_id)
        if nhom is None:
            raise _err(404, "NHOM_NOT_FOUND", "Không tìm thấy nhóm thành phần")

        # Check trùng
        existing = await self.db.execute(
            select(NhomThanhPhanChiTiet.id).where(
                NhomThanhPhanChiTiet.nhom_id == nhom_id,
                NhomThanhPhanChiTiet.cong_chuc_id == data.cong_chuc_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise _err(409, "MEMBER_EXISTS",
                       "Thành viên này đã tồn tại trong nhóm")

        ct = NhomThanhPhanChiTiet(
            nhom_id=nhom_id,
            cong_chuc_id=data.cong_chuc_id,
            vai_tro=data.vai_tro,
            loai_tham_du=data.loai_tham_du,
        )
        self.db.add(ct)
        nhom.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return ct

    async def them_thanh_vien_batch(
        self,
        nhom_id: UUID,
        items: list[ChiTietCreate],
        user: TokenPayload,
    ) -> ChiTietBatchResponse:
        """Thêm nhiều thành viên 1 lần. Skip CC đã có sẵn (không raise 409).

        Trùng cong_chuc_id giữa các item trong cùng request → cũng skip.
        """
        nhom = await self.db.get(NhomThanhPhan, nhom_id)
        if nhom is None:
            raise _err(404, "NHOM_NOT_FOUND", "Không tìm thấy nhóm thành phần")

        # Members hiện có
        existing_result = await self.db.execute(
            select(NhomThanhPhanChiTiet.cong_chuc_id).where(
                NhomThanhPhanChiTiet.nhom_id == nhom_id
            )
        )
        existing_ids: set[UUID] = {row[0] for row in existing_result.fetchall()}

        seen_in_request: set[UUID] = set()
        so_them = 0
        so_bo_qua = 0

        for item in items:
            cc_id = item.cong_chuc_id
            if cc_id in existing_ids or cc_id in seen_in_request:
                so_bo_qua += 1
                continue
            self.db.add(NhomThanhPhanChiTiet(
                nhom_id=nhom_id,
                cong_chuc_id=cc_id,
                vai_tro=item.vai_tro,
                loai_tham_du=item.loai_tham_du,
            ))
            seen_in_request.add(cc_id)
            so_them += 1

        nhom.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

        # Tổng thành viên hiện tại
        tong_result = await self.db.execute(
            select(func.count(NhomThanhPhanChiTiet.id)).where(
                NhomThanhPhanChiTiet.nhom_id == nhom_id
            )
        )
        tong = tong_result.scalar() or 0

        await ghi_audit(
            self.db,
            hanh_dong="ADD_THANH_VIEN_BATCH",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="nhom_thanh_phan",
            doi_tuong_id=nhom_id,
            chi_tiet={"so_them": so_them, "so_bo_qua_trung": so_bo_qua},
        )
        await self.db.flush()

        return ChiTietBatchResponse(
            so_them=so_them,
            so_bo_qua_trung=so_bo_qua,
            tong_thanh_vien=tong,
        )

    async def cap_nhat_thanh_vien(
        self,
        nhom_id: UUID,
        cong_chuc_id: UUID,
        data: ChiTietUpdate,
        user: TokenPayload,
    ) -> NhomThanhPhanChiTiet:
        result = await self.db.execute(
            select(NhomThanhPhanChiTiet).where(
                NhomThanhPhanChiTiet.nhom_id == nhom_id,
                NhomThanhPhanChiTiet.cong_chuc_id == cong_chuc_id,
            )
        )
        ct = result.scalar_one_or_none()
        if ct is None:
            raise _err(404, "MEMBER_NOT_FOUND",
                       "Không tìm thấy thành viên trong nhóm")

        if data.vai_tro is not None:
            ct.vai_tro = data.vai_tro
        if data.loai_tham_du is not None:
            ct.loai_tham_du = data.loai_tham_du

        # Cập nhật updated_at của nhóm
        nhom = await self.db.get(NhomThanhPhan, nhom_id)
        if nhom:
            nhom.updated_at = datetime.now(timezone.utc)

        await self.db.flush()
        return ct

    async def xoa_thanh_vien(
        self, nhom_id: UUID, cong_chuc_id: UUID, user: TokenPayload
    ) -> None:
        result = await self.db.execute(
            select(NhomThanhPhanChiTiet).where(
                NhomThanhPhanChiTiet.nhom_id == nhom_id,
                NhomThanhPhanChiTiet.cong_chuc_id == cong_chuc_id,
            )
        )
        ct = result.scalar_one_or_none()
        if ct is None:
            raise _err(404, "MEMBER_NOT_FOUND",
                       "Không tìm thấy thành viên trong nhóm")

        await self.db.delete(ct)

        nhom = await self.db.get(NhomThanhPhan, nhom_id)
        if nhom:
            nhom.updated_at = datetime.now(timezone.utc)

        await self.db.flush()

    # ──────────────────────────────────────────────────────────────────
    # MERGE — gộp nhóm vào cuộc họp
    # ──────────────────────────────────────────────────────────────────
    async def merge_into_cuoc_hop(
        self,
        cuoc_hop: CuocHop,
        nhom_ids: list[UUID],
        user: TokenPayload,
    ) -> ThemTuNhomResponse:
        """Gộp 1+ nhóm vào cuộc họp.

        - Skip member đã có (không ghi đè loai_tham_du cũ).
        - Auto-fill chu_toa_id nếu cuoc_hop chưa có chu_toa_id (NULL).
          [Trên thực tế chu_toa_id NOT NULL nên field này chỉ check khi extension tương lai;
          giữ logic an toàn — chỉ điền nếu hiện đang None.]
        - Auto-fill thu_ky_id nếu hiện đang NULL.
        - Lấy member đầu tiên thoả vai_tro tương ứng (theo thứ tự nhom_ids đầu vào).
        """
        if not nhom_ids:
            raise _err(400, "MISSING_NHOM_IDS", "Phải truyền ít nhất 1 nhom_id")

        # Load tất cả chi tiết của các nhóm — giữ thứ tự theo nhom_ids đầu vào
        result = await self.db.execute(
            select(NhomThanhPhanChiTiet).where(
                NhomThanhPhanChiTiet.nhom_id.in_(nhom_ids)
            )
        )
        all_chi_tiet = result.scalars().all()

        # Validate: nhom_ids phải hợp lệ
        found_nhom_ids = {ct.nhom_id for ct in all_chi_tiet}
        # Cho phép nhóm rỗng (không có thành viên) — chỉ validate sự tồn tại của nhóm
        nhom_check = await self.db.execute(
            select(NhomThanhPhan.id).where(NhomThanhPhan.id.in_(nhom_ids))
        )
        existing_nhom_ids = {row[0] for row in nhom_check.fetchall()}
        missing = set(nhom_ids) - existing_nhom_ids
        if missing:
            raise _err(404, "NHOM_NOT_FOUND",
                       f"Không tìm thấy nhóm: {', '.join(str(x) for x in missing)}")

        # Sort theo thứ tự nhom_ids đầu vào (để auto-fill ưu tiên nhóm đầu)
        order_map = {nid: i for i, nid in enumerate(nhom_ids)}
        all_chi_tiet_sorted = sorted(all_chi_tiet, key=lambda ct: order_map.get(ct.nhom_id, 999))

        # Members hiện có trong cuộc họp
        existing_result = await self.db.execute(
            select(ThanhPhan.cong_chuc_id).where(ThanhPhan.cuoc_hop_id == cuoc_hop.id)
        )
        existing_member_ids: set[UUID] = {row[0] for row in existing_result.fetchall()}

        so_them = 0
        so_bo_qua = 0
        candidate_chu_tri: Optional[UUID] = None
        candidate_thu_ky: Optional[UUID] = None
        seen_in_request: set[UUID] = set()  # tránh trùng giữa các nhóm trong 1 request

        for ct in all_chi_tiet_sorted:
            cc_id = ct.cong_chuc_id

            # Track candidate cho auto-fill (lấy người đầu tiên gặp được)
            if ct.vai_tro == "CHU_TRI" and candidate_chu_tri is None:
                candidate_chu_tri = cc_id
            if ct.vai_tro == "THU_KY" and candidate_thu_ky is None:
                candidate_thu_ky = cc_id

            # Skip nếu đã có (rule B-a)
            if cc_id in existing_member_ids or cc_id in seen_in_request:
                so_bo_qua += 1
                continue

            self.db.add(ThanhPhan(
                cuoc_hop_id=cuoc_hop.id,
                cong_chuc_id=cc_id,
                loai_tham_du=ct.loai_tham_du,
            ))
            seen_in_request.add(cc_id)
            so_them += 1

        # Auto-fill chu_toa_id / thu_ky_id (rule A-b)
        chu_toa_filled = False
        thu_ky_filled = False
        if cuoc_hop.chu_toa_id is None and candidate_chu_tri is not None:
            cuoc_hop.chu_toa_id = candidate_chu_tri
            chu_toa_filled = True
        if cuoc_hop.thu_ky_id is None and candidate_thu_ky is not None:
            cuoc_hop.thu_ky_id = candidate_thu_ky
            thu_ky_filled = True

        cuoc_hop.updated_at = datetime.now(timezone.utc)

        # Flush để các INSERT vào meeting.thanh_phan được visible khi COUNT
        await self.db.flush()

        # Tổng thành phần sau khi merge
        tong_result = await self.db.execute(
            select(func.count(ThanhPhan.id)).where(ThanhPhan.cuoc_hop_id == cuoc_hop.id)
        )
        tong = tong_result.scalar() or 0

        await ghi_audit(
            self.db,
            hanh_dong="ADD_THANH_PHAN_FROM_NHOM",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="cuoc_hop",
            doi_tuong_id=cuoc_hop.id,
            chi_tiet={
                "nhom_ids": [str(x) for x in nhom_ids],
                "so_them": so_them,
                "so_bo_qua_trung": so_bo_qua,
                "chu_toa_auto_filled": chu_toa_filled,
                "thu_ky_auto_filled": thu_ky_filled,
            },
        )
        await self.db.flush()

        return ThemTuNhomResponse(
            so_them=so_them,
            so_bo_qua_trung=so_bo_qua,
            tong_thanh_phan=tong,
            chu_toa_auto_filled=chu_toa_filled,
            thu_ky_auto_filled=thu_ky_filled,
        )
