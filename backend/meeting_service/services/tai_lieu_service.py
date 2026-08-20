"""
tai_lieu_service.py
====================
Business logic Module 3 — Tài liệu họp.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.models.tai_lieu import TaiLieu
from meeting_service.schemas.tai_lieu import TaiLieuMetadataUpdate
from meeting_service.services.audit_log_service import ghi_audit
from meeting_service.services.storage_service import StorageService
from shared.auth import TokenPayload


FOLDER_TAI_LIEU = "tai-lieu"


class TaiLieuService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = StorageService()

    # ──────────────────────────────────────────────────────────────────
    # UPLOAD
    # ──────────────────────────────────────────────────────────────────
    async def upload(
        self,
        cuoc_hop: CuocHop,
        file: UploadFile,
        user: TokenPayload,
        *,
        ten_tai_lieu: Optional[str] = None,
        mo_ta: Optional[str] = None,
        phan_quyen: str = "CONG_KHAI",
        cho_phep_tai: bool = True,
        cho_phep_in: bool = True,
    ) -> TaiLieu:
        # Save file → filesystem
        meta = await self.storage.save_upload(
            file, folder=FOLDER_TAI_LIEU, cuoc_hop_id=cuoc_hop.id
        )

        tl = TaiLieu(
            cuoc_hop_id=cuoc_hop.id,
            ten_tai_lieu=ten_tai_lieu or meta["original_filename"],
            mo_ta=mo_ta,
            minio_bucket=meta["minio_bucket"],
            minio_key=meta["minio_key"],
            file_size=meta["file_size"],
            mime_type=meta["mime_type"],
            extension=meta["extension"],
            phan_quyen=phan_quyen,
            cho_phep_tai=cho_phep_tai,
            cho_phep_in=cho_phep_in,
            created_by=UUID(user.sub),
        )
        self.db.add(tl)
        await self.db.flush()

        await ghi_audit(
            self.db,
            hanh_dong="UPLOAD_DOC",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="tai_lieu",
            doi_tuong_id=tl.id,
            chi_tiet={
                "cuoc_hop_id": str(cuoc_hop.id),
                "ten_tai_lieu": tl.ten_tai_lieu,
                "file_size": tl.file_size,
                "phan_quyen": phan_quyen,
            },
        )
        await self.db.flush()
        return tl

    # ──────────────────────────────────────────────────────────────────
    # LIST
    # ──────────────────────────────────────────────────────────────────
    async def list_for_cuoc_hop(self, cuoc_hop_id: UUID) -> list[TaiLieu]:
        result = await self.db.execute(
            select(TaiLieu)
            .where(TaiLieu.cuoc_hop_id == cuoc_hop_id, TaiLieu.is_deleted.is_(False))
            .order_by(TaiLieu.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, tai_lieu_id: UUID) -> TaiLieu:
        result = await self.db.execute(
            select(TaiLieu).where(
                TaiLieu.id == tai_lieu_id, TaiLieu.is_deleted.is_(False)
            )
        )
        tl = result.scalar_one_or_none()
        if tl is None:
            raise HTTPException(
                status_code=404,
                detail={"success": False, "error": {"code": "DOC_NOT_FOUND",
                        "message": "Không tìm thấy tài liệu"}},
            )
        return tl

    # ──────────────────────────────────────────────────────────────────
    # AUDIT VIEW / DOWNLOAD (gọi sau khi serve file thành công)
    # ──────────────────────────────────────────────────────────────────
    async def audit_view(self, tl: TaiLieu, user_id: UUID) -> None:
        await ghi_audit(
            self.db,
            hanh_dong="VIEW_DOC",
            nguoi_thuc_hien_id=user_id,
            doi_tuong_loai="tai_lieu",
            doi_tuong_id=tl.id,
            chi_tiet={"cuoc_hop_id": str(tl.cuoc_hop_id)},
        )
        await self.db.flush()

    async def audit_download(self, tl: TaiLieu, user_id: UUID) -> None:
        await ghi_audit(
            self.db,
            hanh_dong="DOWNLOAD_DOC",
            nguoi_thuc_hien_id=user_id,
            doi_tuong_loai="tai_lieu",
            doi_tuong_id=tl.id,
            chi_tiet={"cuoc_hop_id": str(tl.cuoc_hop_id)},
        )
        await self.db.flush()

    # ──────────────────────────────────────────────────────────────────
    # UPDATE METADATA
    # ──────────────────────────────────────────────────────────────────
    async def update_metadata(
        self, tl: TaiLieu, data: TaiLieuMetadataUpdate, user: TokenPayload
    ) -> TaiLieu:
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return tl
        # Đổi mức phân quyền là thay đổi ai đọc được tài liệu, nên nhật ký
        # phải giữ cả giá trị CŨ — chỉ ghi giá trị mới thì sau này không dựng
        # lại được ai đã hạ mức một tài liệu và từ mức nào.
        muc_cu = tl.phan_quyen if "phan_quyen" in changes else None

        for k, v in changes.items():
            setattr(tl, k, v)
        tl.updated_at = datetime.now(timezone.utc)

        await ghi_audit(
            self.db,
            hanh_dong="UPDATE_DOC",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="tai_lieu",
            doi_tuong_id=tl.id,
            chi_tiet={"new_value": changes,
                      **({"phan_quyen_cu": muc_cu} if muc_cu else {})},
        )
        await self.db.flush()
        return tl

    # ──────────────────────────────────────────────────────────────────
    # SOFT DELETE
    # ──────────────────────────────────────────────────────────────────
    async def soft_delete(self, tl: TaiLieu, user: TokenPayload) -> None:
        tl.is_deleted = True
        tl.updated_at = datetime.now(timezone.utc)
        # KHÔNG xóa file vật lý ở MVP — để audit/restore được. Phase sau
        # có thể thêm cron-job xóa file của row is_deleted >30 ngày.
        # Xóa cache PDF preview (nếu có) để giải phóng disk
        from meeting_service.services.preview_service import invalidate_cache
        invalidate_cache(str(tl.id))
        await ghi_audit(
            self.db,
            hanh_dong="DELETE_DOC",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="tai_lieu",
            doi_tuong_id=tl.id,
            chi_tiet={"cuoc_hop_id": str(tl.cuoc_hop_id), "soft_delete": True},
        )
        await self.db.flush()
