"""
ghi_chu_service.py
===================
Ghi chú cá nhân và chia sẻ — G5.2, thay `MEETING_NOTE` của lichkv8.

Ghi chú là dữ liệu RIÊNG của người tạo. Chỉ hai loại người đọc được:

* người tạo — toàn quyền sửa, xoá, đính kèm, chia sẻ;
* người được chia sẻ — chỉ đọc, và đánh dấu đã đọc.

Quản trị KHÔNG được đọc ghi chú người khác. Đây là khác biệt có chủ ý so với
mọi nghiệp vụ khác trong module: cuộc họp, tài liệu, lịch công tác đều là hồ
sơ công vụ nên quản trị xem được, còn đây là sổ tay cá nhân. Cho quản trị đọc
sẽ khiến không ai dám ghi thật, và tính năng chết ngay.

Đính kèm dùng chung bảng `meeting.tai_lieu` với tài liệu họp, phân biệt bằng
CHECK `ck_tai_lieu_chu_the` (đúng một trong `cuoc_hop_id` / `ghi_chu_id`).
File nằm ở `uploads/meeting/ghi-chu/{ghi_chu_id}/`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models.base import CongChucRef as CongChuc
from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.models.lich_cong_tac import GhiChu, GhiChuChiaSe
from meeting_service.models.tai_lieu import TaiLieu
from meeting_service.services.audit_log_service import ghi_audit
from meeting_service.services.lich_cong_tac_service import LoiNghiepVu
from meeting_service.services.notification_service import gui_thong_bao
from meeting_service.services.storage_service import StorageService
from shared.auth import TokenPayload

FOLDER_GHI_CHU = "ghi-chu"

# Trích yếu hiện trên thẻ danh sách — đủ để nhận ra ghi chú mà không phải mở.
DAI_TRICH_YEU = 220


def _trich_yeu(noi_dung: Optional[str]) -> Optional[str]:
    if not noi_dung:
        return None
    goi = " ".join(noi_dung.split())
    return goi if len(goi) <= DAI_TRICH_YEU else goi[:DAI_TRICH_YEU] + "…"


class GhiChuService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = StorageService()

    # ── lấy và kiểm quyền ─────────────────────────────────────────────

    async def _lay(self, ghi_chu_id: UUID) -> GhiChu:
        gc = await self.db.scalar(
            select(GhiChu).where(GhiChu.id == ghi_chu_id,
                                 GhiChu.is_deleted.is_(False)))
        if gc is None:
            raise LoiNghiepVu("NOTE_NOT_FOUND", "Không tìm thấy ghi chú", 404)
        return gc

    async def lay_de_sua(self, ghi_chu_id: UUID, user: TokenPayload) -> GhiChu:
        """Chỉ chủ ghi chú. Người được chia sẻ chỉ đọc.

        Đi qua `lay_de_xem` trước để giữ đúng hai mã lỗi: người ngoài nhận 404
        (không lộ ghi chú có tồn tại), người được chia sẻ nhận 403 (biết có
        ghi chú, chỉ là không được sửa).
        """
        gc, _ = await self.lay_de_xem(ghi_chu_id, user)
        if gc.cong_chuc_id != UUID(user.sub):
            raise LoiNghiepVu(
                "NOTE_FORBIDDEN",
                "Chỉ người tạo mới sửa được ghi chú này", 403)
        return gc

    async def lay_de_xem(
        self, ghi_chu_id: UUID, user: TokenPayload,
    ) -> tuple[GhiChu, Optional[GhiChuChiaSe]]:
        """Chủ ghi chú, hoặc người được chia sẻ (trả kèm bản ghi chia sẻ)."""
        gc = await self._lay(ghi_chu_id)
        toi = UUID(user.sub)
        if gc.cong_chuc_id == toi:
            return gc, None

        cs = await self.db.scalar(
            select(GhiChuChiaSe).where(
                GhiChuChiaSe.ghi_chu_id == gc.id,
                GhiChuChiaSe.nguoi_nhan_id == toi))
        if cs is None:
            # 404 chứ không 403: trả 403 là xác nhận ghi chú có tồn tại, người
            # ngoài không cần biết điều đó.
            raise LoiNghiepVu("NOTE_NOT_FOUND", "Không tìm thấy ghi chú", 404)
        return gc, cs

    # ── danh sách ─────────────────────────────────────────────────────

    async def danh_sach(
        self,
        user: TokenPayload,
        *,
        pham_vi: str = "TAT_CA",       # TAT_CA | CUA_TOI | DUOC_CHIA_SE
        cuoc_hop_id: Optional[UUID] = None,
        tu_khoa: Optional[str] = None,
        chi_chua_doc: bool = False,
        trang: int = 1,
        so_dong: int = 20,
    ) -> tuple[list[dict], int]:
        toi = UUID(user.sub)

        cua_toi = GhiChu.cong_chuc_id == toi
        duoc_chia_se = GhiChu.id.in_(
            select(GhiChuChiaSe.ghi_chu_id).where(
                GhiChuChiaSe.nguoi_nhan_id == toi))
        thay_duoc = {
            "CUA_TOI": cua_toi,
            "DUOC_CHIA_SE": duoc_chia_se,
        }.get(pham_vi, or_(cua_toi, duoc_chia_se))

        dieu_kien = [GhiChu.is_deleted.is_(False), thay_duoc]
        if cuoc_hop_id is not None:
            dieu_kien.append(GhiChu.cuoc_hop_id == cuoc_hop_id)
        if tu_khoa:
            mau = f"%{tu_khoa.strip()}%"
            dieu_kien.append(or_(GhiChu.tieu_de.ilike(mau),
                                 GhiChu.noi_dung.ilike(mau)))
        if chi_chua_doc:
            dieu_kien.append(GhiChu.id.in_(
                select(GhiChuChiaSe.ghi_chu_id).where(
                    GhiChuChiaSe.nguoi_nhan_id == toi,
                    GhiChuChiaSe.da_doc.is_(False))))

        tong = await self.db.scalar(
            select(func.count()).select_from(GhiChu).where(*dieu_kien)) or 0

        q = (select(GhiChu, CongChuc.ho_ten, CuocHop.tieu_de, CuocHop.ngay_hop,
                    CuocHop.ma_lich)
             .join(CongChuc, CongChuc.id == GhiChu.cong_chuc_id)
             .outerjoin(CuocHop, CuocHop.id == GhiChu.cuoc_hop_id)
             .where(*dieu_kien)
             .order_by(GhiChu.is_ghim.desc(), GhiChu.updated_at.desc())
             .limit(so_dong).offset((trang - 1) * so_dong))
        dong = (await self.db.execute(q)).all()
        ids = [g.id for g, *_ in dong]

        dem_tl = await self._dem_tai_lieu(ids)
        dem_cs = await self._dem_chia_se(ids)
        chia_se_toi = await self._chia_se_cho_toi(ids, toi)

        ds = [
            self._tom_tat(gc, ho_ten, ten_hop, ngay_hop, ma_hop, toi,
                          dem_tl.get(gc.id, 0), dem_cs.get(gc.id, 0),
                          chia_se_toi.get(gc.id))
            for gc, ho_ten, ten_hop, ngay_hop, ma_hop in dong
        ]
        return ds, tong

    def _tom_tat(self, gc, ho_ten, ten_hop, ngay_hop, ma_hop, toi,
                 so_tai_lieu, so_chia_se, cs) -> dict:
        return {
            "id": gc.id,
            "tieu_de": gc.tieu_de,
            "trich_yeu": _trich_yeu(gc.noi_dung),
            "is_ghim": gc.is_ghim,
            "cuoc_hop_id": gc.cuoc_hop_id,
            "ten_cuoc_hop": ten_hop,
            "ma_lich": ma_hop,
            "ngay_hop": ngay_hop,
            "la_cua_toi": gc.cong_chuc_id == toi,
            "nguoi_tao_id": gc.cong_chuc_id,
            "nguoi_tao": ho_ten,
            "so_tai_lieu": so_tai_lieu,
            "so_chia_se": so_chia_se,
            "da_doc": None if cs is None else cs["da_doc"],
            "nguoi_chia_se": None if cs is None else cs["nguoi_gui"],
            "loi_nhan": None if cs is None else cs["loi_nhan"],
            "created_at": gc.created_at,
            "updated_at": gc.updated_at,
        }

    async def _dem_tai_lieu(self, ids: list[UUID]) -> dict[UUID, int]:
        if not ids:
            return {}
        rows = (await self.db.execute(
            select(TaiLieu.ghi_chu_id, func.count())
            .where(TaiLieu.ghi_chu_id.in_(ids), TaiLieu.is_deleted.is_(False))
            .group_by(TaiLieu.ghi_chu_id))).all()
        return {i: n for i, n in rows}

    async def _dem_chia_se(self, ids: list[UUID]) -> dict[UUID, int]:
        if not ids:
            return {}
        rows = (await self.db.execute(
            select(GhiChuChiaSe.ghi_chu_id, func.count())
            .where(GhiChuChiaSe.ghi_chu_id.in_(ids))
            .group_by(GhiChuChiaSe.ghi_chu_id))).all()
        return {i: n for i, n in rows}

    async def _chia_se_cho_toi(
        self, ids: list[UUID], toi: UUID,
    ) -> dict[UUID, dict]:
        if not ids:
            return {}
        rows = (await self.db.execute(
            select(GhiChuChiaSe.ghi_chu_id, GhiChuChiaSe.da_doc,
                   GhiChuChiaSe.loi_nhan, CongChuc.ho_ten)
            .join(CongChuc, CongChuc.id == GhiChuChiaSe.nguoi_gui_id)
            .where(GhiChuChiaSe.ghi_chu_id.in_(ids),
                   GhiChuChiaSe.nguoi_nhan_id == toi))).all()
        return {r[0]: {"da_doc": r[1], "loi_nhan": r[2], "nguoi_gui": r[3]}
                for r in rows}

    async def dem_chua_doc(self, user: TokenPayload) -> int:
        return await self.db.scalar(
            select(func.count())
            .select_from(GhiChuChiaSe)
            .join(GhiChu, GhiChu.id == GhiChuChiaSe.ghi_chu_id)
            .where(GhiChuChiaSe.nguoi_nhan_id == UUID(user.sub),
                   GhiChuChiaSe.da_doc.is_(False),
                   GhiChu.is_deleted.is_(False))) or 0

    # ── chi tiết ──────────────────────────────────────────────────────

    async def chi_tiet(self, ghi_chu_id: UUID, user: TokenPayload) -> dict:
        gc, cs = await self.lay_de_xem(ghi_chu_id, user)
        toi = UUID(user.sub)
        la_chu = gc.cong_chuc_id == toi

        nguoi_tao = await self.db.scalar(
            select(CongChuc.ho_ten).where(CongChuc.id == gc.cong_chuc_id))

        hop = None
        if gc.cuoc_hop_id:
            r = (await self.db.execute(
                select(CuocHop.id, CuocHop.ma_lich, CuocHop.tieu_de,
                       CuocHop.ngay_hop)
                .where(CuocHop.id == gc.cuoc_hop_id))).first()
            if r:
                hop = {"id": r[0], "ma_lich": r[1], "tieu_de": r[2],
                       "ngay_hop": r[3]}

        # Danh sách người được chia sẻ chỉ chủ ghi chú thấy — người nhận không
        # cần biết ghi chú còn được gửi cho ai khác.
        chia_se: list[dict] = []
        if la_chu:
            rows = (await self.db.execute(
                select(GhiChuChiaSe, CongChuc.ho_ten, CongChuc.chuc_vu)
                .join(CongChuc, CongChuc.id == GhiChuChiaSe.nguoi_nhan_id)
                .where(GhiChuChiaSe.ghi_chu_id == gc.id)
                .order_by(GhiChuChiaSe.created_at))).all()
            chia_se = [
                {"id": c.id, "nguoi_nhan_id": c.nguoi_nhan_id,
                 "ho_ten": ho_ten, "chuc_vu": chuc_vu, "loi_nhan": c.loi_nhan,
                 "da_doc": c.da_doc, "thoi_diem_doc": c.thoi_diem_doc,
                 "created_at": c.created_at}
                for c, ho_ten, chuc_vu in rows]

        return {
            "id": gc.id,
            "tieu_de": gc.tieu_de,
            "noi_dung": gc.noi_dung,
            "is_ghim": gc.is_ghim,
            "la_cua_toi": la_chu,
            "nguoi_tao_id": gc.cong_chuc_id,
            "nguoi_tao": nguoi_tao,
            "cuoc_hop": hop,
            "tai_lieu": await self.danh_sach_tai_lieu(gc.id),
            "chia_se": chia_se,
            "da_doc": None if cs is None else cs.da_doc,
            "loi_nhan": None if cs is None else cs.loi_nhan,
            "created_at": gc.created_at,
            "updated_at": gc.updated_at,
        }

    # ── ghi ───────────────────────────────────────────────────────────

    async def _kiem_cuoc_hop(self, cuoc_hop_id: Optional[UUID]) -> None:
        if cuoc_hop_id is None:
            return
        co = await self.db.scalar(
            select(func.count()).select_from(CuocHop)
            .where(CuocHop.id == cuoc_hop_id, CuocHop.is_deleted.is_(False)))
        if not co:
            raise LoiNghiepVu("MEETING_NOT_FOUND",
                              "Không tìm thấy cuộc họp để gắn ghi chú", 404)

    async def tao(self, du_lieu: dict, user: TokenPayload) -> GhiChu:
        await self._kiem_cuoc_hop(du_lieu.get("cuoc_hop_id"))
        gc = GhiChu(
            cuoc_hop_id=du_lieu.get("cuoc_hop_id"),
            tieu_de=du_lieu["tieu_de"].strip(),
            noi_dung=du_lieu.get("noi_dung"),
            cong_chuc_id=UUID(user.sub),
            is_ghim=bool(du_lieu.get("is_ghim", False)),
        )
        self.db.add(gc)
        await self.db.flush()
        await ghi_audit(
            self.db, hanh_dong="TAO_GHI_CHU",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="ghi_chu", doi_tuong_id=gc.id,
            chi_tiet={"tieu_de": gc.tieu_de,
                      "cuoc_hop_id": str(gc.cuoc_hop_id) if gc.cuoc_hop_id
                      else None})
        return gc

    async def cap_nhat(
        self, ghi_chu_id: UUID, thay_doi: dict, user: TokenPayload,
    ) -> GhiChu:
        gc = await self.lay_de_sua(ghi_chu_id, user)
        if "cuoc_hop_id" in thay_doi:
            await self._kiem_cuoc_hop(thay_doi["cuoc_hop_id"])

        for cot in ("cuoc_hop_id", "tieu_de", "noi_dung", "is_ghim"):
            if cot in thay_doi:
                gia_tri = thay_doi[cot]
                if cot == "tieu_de":
                    gia_tri = (gia_tri or "").strip()
                    if not gia_tri:
                        raise LoiNghiepVu("NOTE_NO_TITLE",
                                          "Tiêu đề không được để trống")
                setattr(gc, cot, gia_tri)
        gc.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await ghi_audit(
            self.db, hanh_dong="SUA_GHI_CHU",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="ghi_chu", doi_tuong_id=gc.id,
            chi_tiet={"truong": sorted(thay_doi.keys())})
        return gc

    async def xoa(self, ghi_chu_id: UUID, user: TokenPayload) -> None:
        """Xoá mềm. File đính kèm xoá mềm theo, file vật lý giữ lại."""
        gc = await self.lay_de_sua(ghi_chu_id, user)
        gc.is_deleted = True
        gc.updated_at = datetime.now(timezone.utc)
        for tl in await self.danh_sach_tai_lieu(gc.id, tra_ve_model=True):
            tl.is_deleted = True
        await self.db.flush()
        await ghi_audit(
            self.db, hanh_dong="XOA_GHI_CHU",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="ghi_chu", doi_tuong_id=gc.id,
            chi_tiet={"tieu_de": gc.tieu_de})

    # ── chia sẻ ───────────────────────────────────────────────────────

    async def chia_se(
        self,
        ghi_chu_id: UUID,
        nguoi_nhan_ids: list[UUID],
        loi_nhan: Optional[str],
        user: TokenPayload,
    ) -> list[dict]:
        gc = await self.lay_de_sua(ghi_chu_id, user)
        toi = UUID(user.sub)

        # Bỏ trùng nhưng giữ thứ tự người dùng chọn, và bỏ chính mình.
        muon = list(dict.fromkeys(i for i in nguoi_nhan_ids if i != toi))
        if not muon:
            raise LoiNghiepVu("NOTE_NO_RECIPIENT",
                              "Chưa chọn người nhận hợp lệ")

        hop_le = set((await self.db.execute(
            select(CongChuc.id).where(CongChuc.id.in_(muon),
                                      CongChuc.is_active.is_(True))
        )).scalars().all())
        thieu = [i for i in muon if i not in hop_le]
        if thieu:
            raise LoiNghiepVu(
                "NOTE_BAD_RECIPIENT",
                f"{len(thieu)} người nhận không tồn tại hoặc đã nghỉ")

        da_co = set((await self.db.execute(
            select(GhiChuChiaSe.nguoi_nhan_id)
            .where(GhiChuChiaSe.ghi_chu_id == gc.id)
        )).scalars().all())

        them = [i for i in muon if i not in da_co]
        for nhan_id in them:
            self.db.add(GhiChuChiaSe(
                ghi_chu_id=gc.id, nguoi_gui_id=toi, nguoi_nhan_id=nhan_id,
                loi_nhan=loi_nhan))
            await gui_thong_bao(
                self.db,
                nguoi_nhan_id=nhan_id,
                tieu_de=f"Ghi chú được chia sẻ: {gc.tieu_de}",
                noi_dung=loi_nhan,
                sub_loai="GHI_CHU",
                link_url=f"/lich-cong-tac/ghi-chu?ghi_chu_id={gc.id}",
                doi_tuong_id=gc.id,
            )
        await self.db.flush()

        if them:
            await ghi_audit(
                self.db, hanh_dong="CHIA_SE_GHI_CHU",
                nguoi_thuc_hien_id=toi,
                doi_tuong_loai="ghi_chu", doi_tuong_id=gc.id,
                chi_tiet={"so_nguoi": len(them),
                          "nguoi_nhan": [str(i) for i in them]})

        return [{"nguoi_nhan_id": i, "moi": i in them} for i in muon]

    async def thu_hoi_chia_se(
        self, ghi_chu_id: UUID, chia_se_id: UUID, user: TokenPayload,
    ) -> None:
        gc = await self.lay_de_sua(ghi_chu_id, user)
        cs = await self.db.scalar(
            select(GhiChuChiaSe).where(GhiChuChiaSe.id == chia_se_id,
                                       GhiChuChiaSe.ghi_chu_id == gc.id))
        if cs is None:
            raise LoiNghiepVu("SHARE_NOT_FOUND",
                              "Không tìm thấy lượt chia sẻ", 404)
        nguoi_nhan_id = cs.nguoi_nhan_id
        await self.db.delete(cs)
        await self.db.flush()
        await ghi_audit(
            self.db, hanh_dong="THU_HOI_CHIA_SE_GHI_CHU",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="ghi_chu", doi_tuong_id=gc.id,
            chi_tiet={"nguoi_nhan": str(nguoi_nhan_id)})

    async def danh_dau_da_doc(self, ghi_chu_id: UUID, user: TokenPayload) -> bool:
        """Người nhận đánh dấu đã đọc. Chủ ghi chú gọi vào thì không có gì để làm."""
        _, cs = await self.lay_de_xem(ghi_chu_id, user)
        if cs is None or cs.da_doc:
            return False
        cs.da_doc = True
        cs.thoi_diem_doc = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    # ── đính kèm ──────────────────────────────────────────────────────

    async def danh_sach_tai_lieu(
        self, ghi_chu_id: UUID, *, tra_ve_model: bool = False,
    ):
        rows = list((await self.db.execute(
            select(TaiLieu)
            .where(TaiLieu.ghi_chu_id == ghi_chu_id,
                   TaiLieu.is_deleted.is_(False))
            .order_by(TaiLieu.created_at))).scalars().all())
        if tra_ve_model:
            return rows
        return [
            {"id": t.id, "ten_tai_lieu": t.ten_tai_lieu, "mo_ta": t.mo_ta,
             "file_size": t.file_size, "extension": t.extension,
             "mime_type": t.mime_type, "created_at": t.created_at}
            for t in rows]

    async def them_tai_lieu(
        self, ghi_chu_id: UUID, file: UploadFile, user: TokenPayload,
        *, mo_ta: Optional[str] = None,
    ) -> TaiLieu:
        gc = await self.lay_de_sua(ghi_chu_id, user)
        meta = await self.storage.save_upload(
            file, folder=FOLDER_GHI_CHU, thu_muc_con=str(gc.id))
        tl = TaiLieu(
            cuoc_hop_id=None,
            ghi_chu_id=gc.id,
            ten_tai_lieu=meta["original_filename"],
            mo_ta=mo_ta,
            minio_bucket=meta["minio_bucket"],
            minio_key=meta["minio_key"],
            file_size=meta["file_size"],
            mime_type=meta["mime_type"],
            extension=meta["extension"],
            created_by=UUID(user.sub),
        )
        self.db.add(tl)
        await self.db.flush()
        await ghi_audit(
            self.db, hanh_dong="THEM_TAI_LIEU_GHI_CHU",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="tai_lieu", doi_tuong_id=tl.id,
            chi_tiet={"ghi_chu_id": str(gc.id),
                      "ten_tai_lieu": tl.ten_tai_lieu,
                      "file_size": tl.file_size})
        return tl

    async def lay_tai_lieu(
        self, tai_lieu_id: UUID, user: TokenPayload,
    ) -> TaiLieu:
        """Đính kèm ghi chú — quyền đọc bám theo quyền đọc ghi chú chủ quản."""
        tl = await self.db.scalar(
            select(TaiLieu).where(TaiLieu.id == tai_lieu_id,
                                  TaiLieu.is_deleted.is_(False)))
        if tl is None or tl.ghi_chu_id is None:
            raise LoiNghiepVu("DOC_NOT_FOUND", "Không tìm thấy tài liệu", 404)
        await self.lay_de_xem(tl.ghi_chu_id, user)
        return tl

    async def xoa_tai_lieu(self, tai_lieu_id: UUID, user: TokenPayload) -> None:
        tl = await self.db.scalar(
            select(TaiLieu).where(TaiLieu.id == tai_lieu_id,
                                  TaiLieu.is_deleted.is_(False)))
        if tl is None or tl.ghi_chu_id is None:
            raise LoiNghiepVu("DOC_NOT_FOUND", "Không tìm thấy tài liệu", 404)
        await self.lay_de_sua(tl.ghi_chu_id, user)
        tl.is_deleted = True
        await self.db.flush()
        await ghi_audit(
            self.db, hanh_dong="XOA_TAI_LIEU_GHI_CHU",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="tai_lieu", doi_tuong_id=tl.id,
            chi_tiet={"ghi_chu_id": str(tl.ghi_chu_id),
                      "ten_tai_lieu": tl.ten_tai_lieu})

    # ── gợi ý người nhận ──────────────────────────────────────────────

    async def nguoi_nhan_goi_y(
        self, user: TokenPayload, tu_khoa: Optional[str] = None,
        gioi_han: int = 50,
    ) -> list[dict]:
        dieu_kien = [CongChuc.is_active.is_(True),
                     CongChuc.id != UUID(user.sub)]
        if tu_khoa:
            mau = f"%{tu_khoa.strip()}%"
            dieu_kien.append(or_(CongChuc.ho_ten.ilike(mau),
                                 CongChuc.ma_cc.ilike(mau)))
        rows = (await self.db.execute(
            select(CongChuc.id, CongChuc.ma_cc, CongChuc.ho_ten,
                   CongChuc.chuc_vu)
            .where(and_(*dieu_kien))
            .order_by(CongChuc.ho_ten)
            .limit(gioi_han))).all()
        return [{"id": i, "ma_cc": m, "ho_ten": h, "chuc_vu": cv}
                for i, m, h, cv in rows]
