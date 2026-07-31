"""
lms_service/services/bai_kiem_tra_service.py
============================================
Business logic cho BKT CRUD + luong thi (bat dau, nop bai, cham diem).
"""

import math
import random
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.models.bai_kiem_tra import BaiKiemTra
from lms_service.models.bai_kiem_tra_cau_hoi import BaiKiemTraCauHoi
from lms_service.models.cau_hoi import CauHoi
from lms_service.models.ket_qua_bai_kiem_tra import KetQuaBaiKiemTra
from lms_service.models.khoa_hoc import KhoaHoc
from lms_service.models.dang_ky_khoa_hoc import DangKyKhoaHoc
from lms_service.models.base import CongChucRef, DonViRef
from lms_service.schemas.bai_kiem_tra import BaiKiemTraCreate, BaiKiemTraUpdate
from lms_service.services.file_service import FileService
from shared.auth import TokenPayload
from lms_service.core.timezone import now_vn


class BaiKiemTraService:
    """Service xu ly bai kiem tra va luong thi."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _is_manager(self, user: TokenPayload) -> bool:
        return user.vai_tro == "SUPER_ADMIN" or "QT_DAO_TAO" in (user.platform_roles or [])

    def _can_preview(self, user: TokenPayload) -> bool:
        """GV / QT_DAO_TAO / SUPER_ADMIN duoc phep xem thu (preview)."""
        return (
            self._is_manager(user)
            or "GIANG_VIEN" in (user.platform_roles or [])
        )

    async def _get_bkt(self, id: uuid.UUID) -> BaiKiemTra:
        result = await self.db.execute(select(BaiKiemTra).where(BaiKiemTra.id == id, BaiKiemTra.is_active == True))  # noqa: E712
        bkt = result.scalar_one_or_none()
        if bkt is None:
            raise HTTPException(status_code=404, detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy bài kiểm tra"}})
        return bkt

    # =========================================================================
    # 1. DANH SACH
    # =========================================================================
    async def danh_sach(
        self,
        khoa_hoc_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[uuid.UUID] = None,
    ) -> dict:
        base_where = [BaiKiemTra.khoa_hoc_id == khoa_hoc_id, BaiKiemTra.is_active == True]  # noqa: E712
        count_r = await self.db.execute(select(func.count(BaiKiemTra.id)).where(*base_where))
        total_items = count_r.scalar() or 0

        stmt = select(BaiKiemTra).where(*base_where).order_by(BaiKiemTra.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        # Lay thong ke ca nhan bang 1 query GROUP BY (tranh N+1)
        # Khong filter dat_yeu_cau.isnot(None) de THUC_HANH (chua cham) van duoc dem.
        stats_map: dict = {}
        if user_id and items:
            bkt_ids = [item.id for item in items]
            stats_r = await self.db.execute(
                select(
                    KetQuaBaiKiemTra.bai_kiem_tra_id,
                    func.count(KetQuaBaiKiemTra.id).label("so_lan_da_lam"),
                    func.max(KetQuaBaiKiemTra.diem).label("diem_cao_nhat"),
                    func.bool_or(KetQuaBaiKiemTra.dat_yeu_cau).label("da_dat"),
                )
                .where(
                    KetQuaBaiKiemTra.cong_chuc_id == user_id,
                    KetQuaBaiKiemTra.bai_kiem_tra_id.in_(bkt_ids),
                )
                .group_by(KetQuaBaiKiemTra.bai_kiem_tra_id)
            )
            for row in stats_r.all():
                stats_map[str(row.bai_kiem_tra_id)] = {
                    "so_lan_da_lam": row.so_lan_da_lam or 0,
                    "diem_cao_nhat": row.diem_cao_nhat,
                    "da_dat": bool(row.da_dat),
                }

        # Lay trang thai cham/bai nop moi nhat cua ca nhan (chi THUC_HANH)
        latest_map: dict = {}
        if user_id and items:
            bkt_ids = [item.id for item in items]
            latest_r = await self.db.execute(
                select(
                    KetQuaBaiKiemTra.bai_kiem_tra_id,
                    KetQuaBaiKiemTra.bai_nop_url,
                    KetQuaBaiKiemTra.trang_thai_cham,
                )
                .where(
                    KetQuaBaiKiemTra.cong_chuc_id == user_id,
                    KetQuaBaiKiemTra.bai_kiem_tra_id.in_(bkt_ids),
                )
                .order_by(
                    KetQuaBaiKiemTra.bai_kiem_tra_id,
                    KetQuaBaiKiemTra.lan_thu.desc(),
                )
            )
            for row in latest_r.all():
                key = str(row.bai_kiem_tra_id)
                if key not in latest_map:
                    latest_map[key] = {
                        "bai_nop_url": row.bai_nop_url,
                        "trang_thai_cham_moi_nhat": row.trang_thai_cham,
                    }

        # Chuyen ORM objects sang dict (de gan them stats ca nhan)
        item_dicts = []
        for item in items:
            stat = stats_map.get(str(item.id), {})
            latest = latest_map.get(str(item.id), {})
            item_dicts.append({
                "id": item.id,
                "khoa_hoc_id": item.khoa_hoc_id,
                "tieu_de": item.tieu_de,
                "mo_ta": item.mo_ta,
                "loai_bai_kiem_tra": item.loai_bai_kiem_tra,
                "yeu_cau_bai_lam": item.yeu_cau_bai_lam,
                "dung_luong_toi_da_mb": item.dung_luong_toi_da_mb,
                "dinh_dang_cho_phep": item.dinh_dang_cho_phep,
                "so_cau_hoi": item.so_cau_hoi,
                "thoi_gian_lam_bai_phut": item.thoi_gian_lam_bai_phut,
                "so_lan_lam_toi_da": item.so_lan_lam_toi_da,
                "diem_dat": item.diem_dat,
                "tron_de": item.tron_de,
                "tron_dap_an": item.tron_dap_an,
                "che_do_xem_ket_qua": item.che_do_xem_ket_qua,
                "hien_giai_thich": item.hien_giai_thich,
                "ngay_mo": item.ngay_mo if hasattr(item, "ngay_mo") else None,
                "ngay_dong": item.ngay_dong if hasattr(item, "ngay_dong") else None,
                "gio_mo": item.gio_mo if hasattr(item, "gio_mo") else None,
                "gio_dong": item.gio_dong if hasattr(item, "gio_dong") else None,
                "nguoi_tao_id": item.nguoi_tao_id,
                "is_active": item.is_active,
                "created_at": item.created_at,
                "so_lan_da_lam": stat.get("so_lan_da_lam"),
                "diem_cao_nhat": stat.get("diem_cao_nhat"),
                "da_dat": stat.get("da_dat"),
                "bai_nop_url": latest.get("bai_nop_url"),
                "trang_thai_cham_moi_nhat": latest.get("trang_thai_cham_moi_nhat"),
            })

        return {"items": item_dicts, "pagination": {"page": page, "page_size": page_size, "total_items": total_items, "total_pages": math.ceil(total_items / page_size) if total_items else 0}}

    # =========================================================================
    # 2. CHI TIET
    # =========================================================================
    async def chi_tiet(self, id: uuid.UUID) -> BaiKiemTra:
        return await self._get_bkt(id)

    # =========================================================================
    # 3. TAO MOI
    # =========================================================================
    async def tao_moi(self, data: BaiKiemTraCreate, user: TokenPayload) -> BaiKiemTra:
        # Verify khoa hoc
        kh_r = await self.db.execute(select(KhoaHoc).where(KhoaHoc.id == data.khoa_hoc_id))
        if kh_r.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy khóa học"}})

        la_thuc_hanh = data.loai_bai_kiem_tra == "THUC_HANH"
        cau_hoi_ids = data.cau_hoi_ids or []
        cau_hoi_moi = data.cau_hoi_moi or []

        # Trac nghiem: phai co it nhat 1 cau hoi.
        # Thuc hanh: bo qua cau hoi (BKT thuc hanh khong can ngan hang cau hoi).
        if not la_thuc_hanh:
            if not cau_hoi_ids and not cau_hoi_moi:
                raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Phải có ít nhất 1 câu hỏi"}})
            if cau_hoi_ids:
                ch_r = await self.db.execute(select(func.count(CauHoi.id)).where(CauHoi.id.in_(cau_hoi_ids), CauHoi.is_active == True))  # noqa: E712
                if (ch_r.scalar() or 0) != len(cau_hoi_ids):
                    raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Một số câu hỏi không tồn tại"}})

        if la_thuc_hanh:
            # Thuc hanh: yeu_cau_bai_lam bat buoc de hoc vien biet can lam gi
            if not (data.yeu_cau_bai_lam or "").strip():
                raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Yêu cầu bài làm là bắt buộc cho bài thực hành"}})
            tong_so_cau = 0
            # Thuc hanh: khong dung tron de / tron dap an / che do xem dap an
            tron_de = False
            tron_dap_an = False
        else:
            tong_so_cau = len(cau_hoi_ids) + len(cau_hoi_moi)
            tron_de = data.tron_de
            tron_dap_an = data.tron_dap_an

        bkt = BaiKiemTra(
            khoa_hoc_id=data.khoa_hoc_id,
            tieu_de=data.tieu_de,
            mo_ta=data.mo_ta,
            loai_bai_kiem_tra=data.loai_bai_kiem_tra,
            yeu_cau_bai_lam=data.yeu_cau_bai_lam,
            dung_luong_toi_da_mb=data.dung_luong_toi_da_mb or 500,
            dinh_dang_cho_phep=(data.dinh_dang_cho_phep or "mp4,mov,webm"),
            so_cau_hoi=tong_so_cau,
            thoi_gian_lam_bai_phut=data.thoi_gian_lam_bai_phut,
            so_lan_lam_toi_da=data.so_lan_lam_toi_da,
            diem_dat=data.diem_dat,
            tron_de=tron_de,
            tron_dap_an=tron_dap_an,
            che_do_xem_ket_qua=data.che_do_xem_ket_qua,
            hien_giai_thich=data.hien_giai_thich,
            gio_mo=data.gio_mo,
            gio_dong=data.gio_dong,
            nguoi_tao_id=uuid.UUID(user.sub),
        )
        self.db.add(bkt)
        await self.db.flush()  # lay bkt.id

        if la_thuc_hanh:
            # Thuc hanh — khong tao cau hoi / link
            await self.db.flush()
            await self.db.refresh(bkt)
            return bkt

        thu_tu = 1

        # Tao cau hoi moi (inline) va gan vao BKT
        user_uuid = uuid.UUID(user.sub)
        for ch_data in cau_hoi_moi:
            ch = CauHoi(
                khoa_hoc_id=data.khoa_hoc_id,
                bai_kiem_tra_id=bkt.id,
                noi_dung=ch_data.noi_dung,
                loai=ch_data.loai,
                do_kho=ch_data.do_kho,
                diem=ch_data.diem,
                dap_an=ch_data.dap_an,
                giai_thich=ch_data.giai_thich,
                nguoi_tao_id=user_uuid,
            )
            self.db.add(ch)
            await self.db.flush()
            link = BaiKiemTraCauHoi(bai_kiem_tra_id=bkt.id, cau_hoi_id=ch.id, thu_tu=thu_tu)
            self.db.add(link)
            thu_tu += 1

        # Tao lien ket cau hoi tu ngan hang
        for ch_id in cau_hoi_ids:
            link = BaiKiemTraCauHoi(bai_kiem_tra_id=bkt.id, cau_hoi_id=ch_id, thu_tu=thu_tu)
            self.db.add(link)
            thu_tu += 1

        await self.db.flush()
        await self.db.refresh(bkt)
        return bkt

    # =========================================================================
    # 4. CAP NHAT
    # =========================================================================
    async def cap_nhat(self, id: uuid.UUID, data: BaiKiemTraUpdate, user: TokenPayload) -> BaiKiemTra:
        bkt = await self._get_bkt(id)
        update_data = data.model_dump(exclude_unset=True)

        # Lay cac truong can rebuild lien ket
        cau_hoi_ids = update_data.pop("cau_hoi_ids", None)
        cau_hoi_moi = update_data.pop("cau_hoi_moi", None)

        for field, value in update_data.items():
            setattr(bkt, field, value)

        la_thuc_hanh = bkt.loai_bai_kiem_tra == "THUC_HANH"

        if la_thuc_hanh:
            # Thuc hanh: khong dung cau hoi -> luon clean links, ep so_cau_hoi = 0
            await self.db.execute(delete(BaiKiemTraCauHoi).where(BaiKiemTraCauHoi.bai_kiem_tra_id == id))
            bkt.so_cau_hoi = 0
            bkt.tron_de = False
            bkt.tron_dap_an = False
        elif cau_hoi_ids is not None or cau_hoi_moi is not None:
            # Trac nghiem + co thay doi cau hoi → xoa links cu, tao moi
            await self.db.execute(delete(BaiKiemTraCauHoi).where(BaiKiemTraCauHoi.bai_kiem_tra_id == id))

            thu_tu = 1
            user_uuid = uuid.UUID(user.sub)

            # Tao cau hoi moi inline
            for ch_data in (cau_hoi_moi or []):
                ch = CauHoi(
                    khoa_hoc_id=bkt.khoa_hoc_id,
                    bai_kiem_tra_id=id,
                    noi_dung=ch_data.noi_dung,
                    loai=ch_data.loai,
                    do_kho=ch_data.do_kho,
                    diem=ch_data.diem,
                    dap_an=ch_data.dap_an,
                    giai_thich=ch_data.giai_thich,
                    nguoi_tao_id=user_uuid,
                )
                self.db.add(ch)
                await self.db.flush()
                self.db.add(BaiKiemTraCauHoi(bai_kiem_tra_id=id, cau_hoi_id=ch.id, thu_tu=thu_tu))
                thu_tu += 1

            # Gan cau hoi tu ngan hang
            for ch_id in (cau_hoi_ids or []):
                self.db.add(BaiKiemTraCauHoi(bai_kiem_tra_id=id, cau_hoi_id=ch_id, thu_tu=thu_tu))
                thu_tu += 1

            bkt.so_cau_hoi = thu_tu - 1

        await self.db.flush()
        await self.db.refresh(bkt)
        return bkt

    # =========================================================================
    # 4b. DANH SACH CAU HOI CUA BKT (qua junction table)
    # =========================================================================
    async def danh_sach_cau_hoi(self, bai_kiem_tra_id: uuid.UUID) -> list[dict]:
        """Lay danh sach cau hoi cua BKT theo thu tu, ke ca dap an (cho GIANG_VIEN quan tri)."""
        bkt = await self._get_bkt(bai_kiem_tra_id)  # noqa: F841
        links_r = await self.db.execute(
            select(BaiKiemTraCauHoi, CauHoi)
            .join(CauHoi, BaiKiemTraCauHoi.cau_hoi_id == CauHoi.id)
            .where(BaiKiemTraCauHoi.bai_kiem_tra_id == bai_kiem_tra_id, CauHoi.is_active == True)  # noqa: E712
            .order_by(BaiKiemTraCauHoi.thu_tu.asc())
        )
        items = []
        for link, ch in links_r.all():
            items.append({
                "id": ch.id,
                "bai_kiem_tra_id": ch.bai_kiem_tra_id,
                "khoa_hoc_id": ch.khoa_hoc_id,
                "thu_tu": link.thu_tu,
                "noi_dung": ch.noi_dung,
                "loai": ch.loai,
                "do_kho": ch.do_kho,
                "diem": ch.diem,
                "dap_an": ch.dap_an,
                "giai_thich": ch.giai_thich,
                "is_active": ch.is_active,
                "created_at": ch.created_at,
            })
        return items

    # =========================================================================
    # 5. XOA
    # =========================================================================
    async def xoa(self, id: uuid.UUID, user: TokenPayload) -> None:
        bkt = await self._get_bkt(id)
        # Kiem tra chua co ai thi
        kq_count = await self.db.execute(select(func.count(KetQuaBaiKiemTra.id)).where(KetQuaBaiKiemTra.bai_kiem_tra_id == id))
        if (kq_count.scalar() or 0) > 0:
            raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_009", "message": "Không thể xóa bài kiểm tra đã có người thi"}})
        # Xoa links
        await self.db.execute(delete(BaiKiemTraCauHoi).where(BaiKiemTraCauHoi.bai_kiem_tra_id == id))
        bkt.is_active = False
        await self.db.flush()

    # =========================================================================
    # 6. BAT DAU THI
    # =========================================================================
    async def bat_dau_thi(
        self,
        bai_kiem_tra_id: uuid.UUID,
        user: TokenPayload,
        preview: bool = False,
    ) -> dict:
        """Bat dau lam bai kiem tra. Tra ve cau hoi (khong dap an).

        preview=True: danh cho GV/QT/ADMIN xem thu — KHONG tao ket_qua, KHONG ghi DB.
        """
        bkt = await self._get_bkt(bai_kiem_tra_id)
        user_uuid = uuid.UUID(user.sub)

        is_preview_mode = False
        if preview:
            if not self._can_preview(user):
                raise HTTPException(
                    status_code=403,
                    detail={"success": False, "error": {"code": "LMS_ERR_008", "message": "Bạn không có quyền xem thử"}},
                )
            is_preview_mode = True

        if not is_preview_mode:
            # Enforce ngay_mo/ngay_dong (Date check) va gio_mo/gio_dong (time check)
            now = now_vn()
            today = now.date()
            current_time = now.strftime("%H:%M")

            if bkt.ngay_mo and today < bkt.ngay_mo:
                raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_011", "message": f"Bài kiểm tra chưa mở. Ngày mở: {bkt.ngay_mo}"}})
            if bkt.ngay_dong and today > bkt.ngay_dong:
                raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_012", "message": "Bài kiểm tra đã đóng"}})
            if bkt.gio_mo and current_time < bkt.gio_mo:
                raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_013", "message": f"Chưa đến giờ thi. Khung giờ: {bkt.gio_mo} - {bkt.gio_dong}"}})
            if bkt.gio_dong and current_time > bkt.gio_dong:
                raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_014", "message": f"Đã hết giờ thi. Khung giờ: {bkt.gio_mo} - {bkt.gio_dong}"}})

            # Verify da dang ky khoa hoc
            dk_r = await self.db.execute(
                select(DangKyKhoaHoc).where(DangKyKhoaHoc.cong_chuc_id == user_uuid, DangKyKhoaHoc.khoa_hoc_id == bkt.khoa_hoc_id)
            )
            dk_obj = dk_r.scalar_one_or_none()
            if dk_obj is None:
                raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_003", "message": "Bạn chưa đăng ký khóa học này"}})
            if dk_obj.trang_thai in ("CHO_PHE_DUYET", "TU_CHOI", "BI_LOAI"):
                status_labels = {"CHO_PHE_DUYET": "chờ phê duyệt", "TU_CHOI": "bị từ chối", "BI_LOAI": "đã bị loại"}
                raise HTTPException(status_code=403, detail={"success": False, "error": {"code": "LMS_ERR_011", "message": f"Không thể thi. Đăng ký {status_labels.get(dk_obj.trang_thai, dk_obj.trang_thai)}."}})

            # Kiem tra so lan da thi
            done_count_r = await self.db.execute(
                select(func.count(KetQuaBaiKiemTra.id)).where(
                    KetQuaBaiKiemTra.cong_chuc_id == user_uuid,
                    KetQuaBaiKiemTra.bai_kiem_tra_id == bai_kiem_tra_id,
                    KetQuaBaiKiemTra.dat_yeu_cau.isnot(None),  # da cham xong
                )
            )
            done_count = done_count_r.scalar() or 0
            if bkt.so_lan_lam_toi_da and done_count >= bkt.so_lan_lam_toi_da:
                raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_005", "message": f"Đã hết lượt thi ({bkt.so_lan_lam_toi_da} lần)"}})

            # BKT thuc hanh: KHONG tao placeholder — chi tao record khi thuc su nop_video
            if bkt.loai_bai_kiem_tra == "THUC_HANH":
                kq = None
                existing = None
                lan_thu = done_count + 1
            else:
                # Trac nghiem: Check for existing in-progress attempt (resume logic)
                existing_r = await self.db.execute(
                    select(KetQuaBaiKiemTra).where(
                        KetQuaBaiKiemTra.cong_chuc_id == user_uuid,
                        KetQuaBaiKiemTra.bai_kiem_tra_id == bai_kiem_tra_id,
                        KetQuaBaiKiemTra.dat_yeu_cau.is_(None),
                    )
                )
                existing = existing_r.scalar_one_or_none()

                if existing:
                    kq = existing
                    lan_thu = kq.lan_thu
                else:
                    lan_thu = done_count + 1
                    kq = KetQuaBaiKiemTra(
                        cong_chuc_id=user_uuid,
                        bai_kiem_tra_id=bai_kiem_tra_id,
                        lan_thu=lan_thu,
                        ngay_lam=now_vn(),
                    )
                    self.db.add(kq)
                    await self.db.flush()
                    await self.db.refresh(kq)
        else:
            # Preview mode — KHONG tao record nao
            kq = None
            existing = None
            lan_thu = 0
            done_count = 0

        # =====================================================================
        # BKT THUC HANH — tra config upload, khong can list cau hoi
        # =====================================================================
        if bkt.loai_bai_kiem_tra == "THUC_HANH":
            # THUC_HANH khong tao placeholder → so_lan_con_lai = tong - da nop
            if bkt.so_lan_lam_toi_da and not is_preview_mode:
                so_lan_con_lai = bkt.so_lan_lam_toi_da - done_count
            else:
                so_lan_con_lai = None
            return {
                "ket_qua_id": kq.id if kq else None,
                "lan_thu": lan_thu,
                "thoi_gian_phut": bkt.thoi_gian_lam_bai_phut,
                "loai_bai_kiem_tra": "THUC_HANH",
                "yeu_cau_bai_lam": bkt.yeu_cau_bai_lam,
                "dung_luong_toi_da_mb": bkt.dung_luong_toi_da_mb,
                "dinh_dang_cho_phep": bkt.dinh_dang_cho_phep,
                "so_cau": 0,
                "cau_hoi": [],
                "so_lan_con_lai": so_lan_con_lai,
                "dang_tiep_tuc": False,
                "chi_tiet_nhap": None,
                "thoi_gian_da_lam_giay": 0,
                "so_lan_vi_pham": 0,
                "is_preview": is_preview_mode,
            }

        # Lay danh sach cau hoi
        links_r = await self.db.execute(
            select(BaiKiemTraCauHoi, CauHoi)
            .join(CauHoi, BaiKiemTraCauHoi.cau_hoi_id == CauHoi.id)
            .where(BaiKiemTraCauHoi.bai_kiem_tra_id == bai_kiem_tra_id)
            .order_by(BaiKiemTraCauHoi.thu_tu.asc())
        )
        links = links_r.all()

        cau_hoi_list = []
        for link, ch in links:
            # Lay lua_chon tu dap_an, LOAI BO dap_an_dung
            # Frontend luu: {"options": ["Opt A", "Opt B", ...], "correct": 0}
            lua_chon = None
            if isinstance(ch.dap_an, dict) and ch.loai in ("TRAC_NGHIEM_1", "TRAC_NGHIEM_NHIEU"):
                options = ch.dap_an.get("options") or ch.dap_an.get("lua_chon") or []
                if isinstance(options, list) and options:
                    lua_chon = [{"key": chr(65 + i), "noi_dung": str(opt)} for i, opt in enumerate(options)]

            cau_hoi_list.append({
                "id": ch.id,
                "thu_tu": link.thu_tu,
                "noi_dung": ch.noi_dung,
                "loai": ch.loai,
                "diem": ch.diem,
                "lua_chon": lua_chon,
            })

        # Xao tron cau hoi
        if bkt.tron_de:
            random.shuffle(cau_hoi_list)
            for i, item in enumerate(cau_hoi_list):
                item["thu_tu"] = i + 1

        # Xao tron dap an
        if bkt.tron_dap_an:
            for item in cau_hoi_list:
                if item["lua_chon"] and isinstance(item["lua_chon"], list):
                    random.shuffle(item["lua_chon"])

        # Tinh so_lan_con_lai
        so_lan_con_lai = (bkt.so_lan_lam_toi_da - lan_thu) if (bkt.so_lan_lam_toi_da and not is_preview_mode) else None

        # Neu resume, tra ve chi_tiet_nhap va thoi_gian_da_lam
        if existing and not is_preview_mode:
            thoi_gian_da_lam_giay = int((now_vn() - kq.ngay_lam).total_seconds()) if kq.ngay_lam else 0
            return {
                "ket_qua_id": kq.id,
                "lan_thu": lan_thu,
                "thoi_gian_phut": bkt.thoi_gian_lam_bai_phut,
                "loai_bai_kiem_tra": bkt.loai_bai_kiem_tra,
                "so_cau": len(cau_hoi_list),
                "cau_hoi": cau_hoi_list,
                "so_lan_con_lai": so_lan_con_lai,
                "dang_tiep_tuc": True,
                "chi_tiet_nhap": kq.chi_tiet_nhap,
                "thoi_gian_da_lam_giay": thoi_gian_da_lam_giay,
                "so_lan_vi_pham": kq.so_lan_vi_pham or 0,
                "is_preview": False,
            }
        else:
            return {
                "ket_qua_id": kq.id if kq else None,
                "lan_thu": lan_thu,
                "thoi_gian_phut": bkt.thoi_gian_lam_bai_phut,
                "loai_bai_kiem_tra": bkt.loai_bai_kiem_tra,
                "so_cau": len(cau_hoi_list),
                "cau_hoi": cau_hoi_list,
                "so_lan_con_lai": so_lan_con_lai,
                "dang_tiep_tuc": False,
                "chi_tiet_nhap": None,
                "thoi_gian_da_lam_giay": 0,
                "so_lan_vi_pham": 0,
                "is_preview": is_preview_mode,
            }

    # =========================================================================
    # 6b. LUU NHAP (AUTO-SAVE)
    # =========================================================================
    async def luu_nhap(self, ket_qua_id: uuid.UUID, tra_loi_nhap: list, so_lan_vi_pham: int, user: TokenPayload) -> dict:
        """Luu bai lam nhap (auto-save moi 30s)."""
        user_uuid = uuid.UUID(user.sub)
        kq_r = await self.db.execute(select(KetQuaBaiKiemTra).where(KetQuaBaiKiemTra.id == ket_qua_id))
        kq = kq_r.scalar_one_or_none()
        if kq is None:
            raise HTTPException(status_code=404, detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy kết quả thi"}})
        if kq.cong_chuc_id != user_uuid:
            raise HTTPException(status_code=403, detail={"success": False, "error": {"code": "LMS_ERR_008", "message": "Không có quyền"}})
        if kq.dat_yeu_cau is not None:
            raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_010", "message": "Bài đã nộp"}})

        # Convert list to serializable format
        nhap_data = [{"cau_hoi_id": str(tl.cau_hoi_id), "dap_an": tl.dap_an} for tl in tra_loi_nhap]
        kq.chi_tiet_nhap = nhap_data
        kq.so_lan_vi_pham = so_lan_vi_pham
        await self.db.flush()
        return {"success": True, "message": "Đã lưu bài làm nháp"}

    # =========================================================================
    # 7. NOP BAI — CHAM DIEM TU DONG
    # =========================================================================
    async def nop_bai(self, ket_qua_id: uuid.UUID, tra_loi_list: list, user: TokenPayload) -> dict:
        """Nop bai va cham diem tu dong (BKT trac nghiem)."""
        user_uuid = uuid.UUID(user.sub)

        # Lay ket qua
        kq_r = await self.db.execute(select(KetQuaBaiKiemTra).where(KetQuaBaiKiemTra.id == ket_qua_id))
        kq = kq_r.scalar_one_or_none()
        if kq is None:
            raise HTTPException(status_code=404, detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy kết quả thi"}})
        if kq.cong_chuc_id != user_uuid:
            raise HTTPException(status_code=403, detail={"success": False, "error": {"code": "LMS_ERR_008", "message": "Không có quyền nộp bài này"}})
        if kq.dat_yeu_cau is not None:
            raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_010", "message": "Bài thi này đã được nộp"}})

        bkt = await self._get_bkt(kq.bai_kiem_tra_id)

        # BKT thuc hanh khong dung endpoint nay
        if bkt.loai_bai_kiem_tra == "THUC_HANH":
            raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Bài kiểm tra thực hành phải dùng endpoint nộp video"}})

        # Tinh thoi gian lam
        thoi_gian_lam = int((now_vn() - kq.ngay_lam).total_seconds()) if kq.ngay_lam else 0

        # Map tra loi theo cau_hoi_id
        tra_loi_map = {str(tl.cau_hoi_id): tl.dap_an for tl in tra_loi_list}

        # Lay tat ca cau hoi cua BKT
        links_r = await self.db.execute(
            select(CauHoi)
            .join(BaiKiemTraCauHoi, CauHoi.id == BaiKiemTraCauHoi.cau_hoi_id)
            .where(BaiKiemTraCauHoi.bai_kiem_tra_id == bkt.id)
        )
        cau_hoi_list = links_r.scalars().all()

        # Cham diem tung cau
        chi_tiet = []
        tong_diem = Decimal("0")
        tong_diem_max = Decimal("0")
        so_dung = 0
        so_sai = 0

        for ch in cau_hoi_list:
            ch_diem_max = ch.diem or Decimal("1.0")
            tong_diem_max += ch_diem_max
            tra_loi_user = tra_loi_map.get(str(ch.id))
            dap_an = ch.dap_an or {}

            dung = False
            diem_dat = Decimal("0")

            if ch.loai == "TU_LUAN":
                # Tu luan: khong cham tu dong
                diem_dat = Decimal("0")
                dung = None  # chua cham
            elif ch.loai == "TRAC_NGHIEM_1":
                # Frontend luu {"options": [...], "correct": 0} (index)
                # User gui letter "A", "B", ... → chuyen sang index de so sanh
                correct_raw = dap_an.get("correct") if "correct" in dap_an else dap_an.get("dap_an_dung")
                if correct_raw is not None and tra_loi_user is not None:
                    if isinstance(correct_raw, int):
                        try:
                            user_idx = ord(str(tra_loi_user).upper()[0]) - ord("A")
                        except Exception:
                            user_idx = -1
                        if user_idx == correct_raw:
                            dung = True
                            diem_dat = ch_diem_max
                    else:
                        # Fallback: so sanh truc tiep (cu)
                        if str(tra_loi_user) == str(correct_raw):
                            dung = True
                            diem_dat = ch_diem_max
            elif ch.loai == "TRAC_NGHIEM_NHIEU":
                # Frontend luu {"options": [...], "correct": [0, 2]} (list of indices)
                # User gui list letters ["A", "C"] → chuyen sang indices
                correct_raw = dap_an.get("correct") if "correct" in dap_an else dap_an.get("dap_an_dung", [])
                if isinstance(correct_raw, list) and correct_raw and isinstance(correct_raw[0], int):
                    dap_an_set = set(correct_raw)
                    if isinstance(tra_loi_user, list):
                        try:
                            tra_loi_set = {ord(str(k).upper()[0]) - ord("A") for k in tra_loi_user if k}
                        except Exception:
                            tra_loi_set = set()
                    else:
                        tra_loi_set = set()
                else:
                    # Fallback: xu ly nhu strings
                    dap_an_set = set(correct_raw) if correct_raw else set()
                    tra_loi_set = set(tra_loi_user) if isinstance(tra_loi_user, list) else set()
                if dap_an_set and tra_loi_set == dap_an_set:
                    dung = True
                    diem_dat = ch_diem_max
                elif dap_an_set and tra_loi_set & dap_an_set:
                    # Diem tu phan: so dung / tong dung * diem
                    matched = len(tra_loi_set & dap_an_set)
                    diem_dat = ch_diem_max * Decimal(matched) / Decimal(len(dap_an_set))
            elif ch.loai == "DUNG_SAI":
                # Frontend luu {"correct": true/false}
                correct_raw = dap_an.get("correct") if "correct" in dap_an else dap_an.get("dap_an_dung")
                if tra_loi_user == correct_raw:
                    dung = True
                    diem_dat = ch_diem_max
            elif ch.loai == "GHEP_DOI":
                dap_an_dung = dap_an.get("dap_an_dung")
                if tra_loi_user == dap_an_dung:
                    dung = True
                    diem_dat = ch_diem_max

            tong_diem += diem_dat
            if dung is True:
                so_dung += 1
            elif dung is False:
                so_sai += 1

            # Build dap_an_dung hien thi (chuyen index → letter cho trac nghiem)
            _raw = dap_an.get("correct") if "correct" in dap_an else dap_an.get("dap_an_dung")
            if ch.loai == "TRAC_NGHIEM_1" and isinstance(_raw, int):
                dap_an_display = chr(65 + _raw)
            elif ch.loai == "TRAC_NGHIEM_NHIEU" and isinstance(_raw, list) and _raw and isinstance(_raw[0], int):
                dap_an_display = [chr(65 + x) for x in _raw]
            else:
                dap_an_display = _raw

            chi_tiet.append({
                "cau_hoi_id": str(ch.id),
                "noi_dung": ch.noi_dung,
                "loai": ch.loai,
                "tra_loi": tra_loi_user,
                "dap_an_dung": dap_an_display,
                "dung": dung,
                "diem_dat": float(diem_dat),
                "diem_toi_da": float(ch_diem_max),
                "giai_thich": ch.giai_thich,
            })

        # Tinh phan tram va dat yeu cau
        phan_tram = (tong_diem / tong_diem_max * 100) if tong_diem_max > 0 else Decimal("0")
        dat = phan_tram >= (bkt.diem_dat or Decimal("70"))

        # Cap nhat ket qua — LUU % (thang 100), KHONG luu diem tho.
        # Ly do: bkt.diem_dat la % (default 70 = 70%), nen kq.diem cung phai cung scale.
        # Cert (chung_chi.diem_dat) lay max(kq.diem) → can la % de hien thi/xep loai dung.
        kq.diem = phan_tram
        kq.so_cau_dung = so_dung
        kq.so_cau_sai = so_sai
        kq.thoi_gian_lam_giay = thoi_gian_lam
        kq.chi_tiet_tra_loi = chi_tiet
        kq.dat_yeu_cau = dat

        await self.db.flush()
        await self.db.refresh(kq)

        # Side effect: cap nhat dang_ky + tinh lai phan tram
        dk_r = await self.db.execute(
            select(DangKyKhoaHoc).where(
                DangKyKhoaHoc.cong_chuc_id == user_uuid,
                DangKyKhoaHoc.khoa_hoc_id == bkt.khoa_hoc_id,
            )
        )
        dk = dk_r.scalar_one_or_none()
        if dk:
            # Cap nhat diem cao nhat va so lan lam bai moi lan nop
            dk.so_lan_lam_bai = (dk.so_lan_lam_bai or 0) + 1
            if dat and (dk.diem_cao_nhat is None or tong_diem > dk.diem_cao_nhat):
                dk.diem_cao_nhat = tong_diem
            await self.db.flush()
            # Tinh lai phan tram hoan thanh (bao gom ca BKT)
            from lms_service.services.bai_hoc_service import BaiHocService
            bh_svc = BaiHocService(self.db)
            await bh_svc._tinh_lai_phan_tram(dk, bkt.khoa_hoc_id, user_uuid)

        # =====================================================================
        # Loc chi_tiet theo che_do_xem_ket_qua
        # =====================================================================
        che_do = bkt.che_do_xem_ket_qua
        la_lan_cuoi = (
            bkt.so_lan_lam_toi_da is not None
            and kq.lan_thu >= bkt.so_lan_lam_toi_da
        )

        thong_bao = None
        chi_tiet_response = None

        if che_do in ("KHONG_CHO_XEM", "CHI_XEM_DIEM"):
            # Khong tra chi tiet — chi biet diem tong / dat hay khong
            chi_tiet_response = None

        elif che_do == "CHI_XEM_CAU_SAI":
            # Tra chi tiet nhung KHONG co dap_an_dung va giai_thich
            chi_tiet_response = [
                {
                    "cau_hoi_id": ct["cau_hoi_id"],
                    "noi_dung": ct["noi_dung"],
                    "loai": ct["loai"],
                    "tra_loi": ct["tra_loi"],
                    "dung": ct["dung"],
                    "diem_dat": ct["diem_dat"],
                    "diem_toi_da": ct["diem_toi_da"],
                }
                for ct in chi_tiet
            ]

        elif che_do == "XEM_KHI_LAN_CUOI":
            if la_lan_cuoi:
                # Lan cuoi: tra day du nhu XEM_DIEM_VA_DAP_AN
                chi_tiet_response = [
                    {**ct, "giai_thich": ct["giai_thich"] if bkt.hien_giai_thich else None}
                    for ct in chi_tiet
                ]
            else:
                # Chua phai lan cuoi: chi tra diem, bao gio xem duoc
                con_lai = bkt.so_lan_lam_toi_da - kq.lan_thu
                thong_bao = (
                    f"Đáp án sẽ hiển thị sau lần làm cuối (còn {con_lai} lượt)"
                )

        else:
            # XEM_DIEM_VA_DAP_AN (mac dinh): tra day du
            chi_tiet_response = [
                {**ct, "giai_thich": ct["giai_thich"] if bkt.hien_giai_thich else None}
                for ct in chi_tiet
            ]

        result = {
            "id": kq.id,
            "lan_thu": kq.lan_thu,
            "diem": kq.diem,
            "so_cau_dung": kq.so_cau_dung,
            "so_cau_sai": kq.so_cau_sai,
            "thoi_gian_lam_giay": kq.thoi_gian_lam_giay,
            "dat_yeu_cau": kq.dat_yeu_cau,
            "ngay_lam": kq.ngay_lam,
            "che_do_xem": che_do,
            "chi_tiet": chi_tiet_response,
        }
        if thong_bao:
            result["thong_bao"] = thong_bao
        return result

    # =========================================================================
    # 8. KET QUA CHI TIET
    # =========================================================================
    async def ket_qua_chi_tiet(self, ket_qua_id: uuid.UUID, user: TokenPayload) -> dict:
        user_uuid = uuid.UUID(user.sub)
        kq_r = await self.db.execute(select(KetQuaBaiKiemTra).where(KetQuaBaiKiemTra.id == ket_qua_id))
        kq = kq_r.scalar_one_or_none()
        if kq is None:
            raise HTTPException(status_code=404, detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy kết quả thi"}})

        # Quyen: user cua minh hoac GIANG_VIEN/QT
        if kq.cong_chuc_id != user_uuid and not self._is_manager(user):
            if "GIANG_VIEN" not in (user.platform_roles or []):
                raise HTTPException(status_code=403, detail={"success": False, "error": {"code": "LMS_ERR_008", "message": "Không có quyền xem kết quả này"}})

        bkt = await self._get_bkt(kq.bai_kiem_tra_id)

        return {
            "id": kq.id,
            "lan_thu": kq.lan_thu,
            "diem": kq.diem,
            "so_cau_dung": kq.so_cau_dung,
            "so_cau_sai": kq.so_cau_sai,
            "thoi_gian_lam_giay": kq.thoi_gian_lam_giay,
            "dat_yeu_cau": kq.dat_yeu_cau,
            "ngay_lam": kq.ngay_lam,
            "chi_tiet": kq.chi_tiet_tra_loi,
            "loai_bai_kiem_tra": bkt.loai_bai_kiem_tra,
            "bai_nop_url": kq.bai_nop_url,
            "bai_nop_ten_file": kq.bai_nop_ten_file,
            "trang_thai_cham": kq.trang_thai_cham,
            "nhan_xet": kq.nhan_xet,
            "ngay_nop": kq.ngay_nop,
            "ngay_cham": kq.ngay_cham,
        }

    # =========================================================================
    # 9. LICH SU THI — danh sach cac lan lam bai cua user tren 1 BKT
    # =========================================================================
    async def lich_su_thi(self, bai_kiem_tra_id: uuid.UUID, user: TokenPayload) -> dict:
        """Lay lich su lam bai kiem tra cua user hien tai."""
        bkt = await self._get_bkt(bai_kiem_tra_id)
        user_uuid = uuid.UUID(user.sub)

        # Thuc hanh: hien thi ca lan dang CHO_CHAM (dat_yeu_cau chua co) de hoc vien biet
        la_thuc_hanh = bkt.loai_bai_kiem_tra == "THUC_HANH"
        if la_thuc_hanh:
            where_clauses = [
                KetQuaBaiKiemTra.cong_chuc_id == user_uuid,
                KetQuaBaiKiemTra.bai_kiem_tra_id == bai_kiem_tra_id,
            ]
        else:
            where_clauses = [
                KetQuaBaiKiemTra.cong_chuc_id == user_uuid,
                KetQuaBaiKiemTra.bai_kiem_tra_id == bai_kiem_tra_id,
                KetQuaBaiKiemTra.dat_yeu_cau.isnot(None),
            ]
        kq_r = await self.db.execute(
            select(KetQuaBaiKiemTra)
            .where(*where_clauses)
            .order_by(KetQuaBaiKiemTra.lan_thu.asc())
        )
        ket_qua_list = kq_r.scalars().all()

        so_lan_da_lam = len(ket_qua_list)
        diem_cao_nhat = max((kq.diem for kq in ket_qua_list if kq.diem is not None), default=None)
        da_dat = any(kq.dat_yeu_cau for kq in ket_qua_list)

        return {
            "bai_kiem_tra_id": bkt.id,
            "tieu_de": bkt.tieu_de,
            "loai_bai_kiem_tra": bkt.loai_bai_kiem_tra,
            "so_lan_lam_toi_da": bkt.so_lan_lam_toi_da,
            "diem_dat": bkt.diem_dat,
            "so_lan_da_lam": so_lan_da_lam,
            "diem_cao_nhat": diem_cao_nhat,
            "da_dat": da_dat,
            "lich_su": [
                {
                    "id": kq.id,
                    "lan_thu": kq.lan_thu,
                    "diem": kq.diem,
                    "so_cau_dung": kq.so_cau_dung,
                    "so_cau_sai": kq.so_cau_sai,
                    "thoi_gian_lam_giay": kq.thoi_gian_lam_giay,
                    "dat_yeu_cau": kq.dat_yeu_cau,
                    "ngay_lam": kq.ngay_lam,
                    "bai_nop_url": kq.bai_nop_url,
                    "bai_nop_ten_file": kq.bai_nop_ten_file,
                    "trang_thai_cham": kq.trang_thai_cham,
                    "nhan_xet": kq.nhan_xet,
                    "ngay_nop": kq.ngay_nop,
                    "ngay_cham": kq.ngay_cham,
                }
                for kq in ket_qua_list
            ],
        }

    # =========================================================================
    # 10. KET QUA TAT CA — danh sach tat ca ket qua thi cua 1 BKT (cho GIANG_VIEN/QT)
    # =========================================================================
    async def ket_qua_tat_ca(self, bai_kiem_tra_id: uuid.UUID, user: TokenPayload) -> list:
        """Lay tat ca ket qua thi cua 1 BKT (cho giang vien/QT)."""
        bkt = await self._get_bkt(bai_kiem_tra_id)

        # Auth check: only GIANG_VIEN, QT_DAO_TAO, SUPER_ADMIN
        if not self._is_manager(user) and "GIANG_VIEN" not in (user.platform_roles or []):
            raise HTTPException(
                status_code=403,
                detail={
                    "success": False,
                    "error": {"code": "LMS_ERR_008", "message": "Không có quyền"}
                }
            )

        cc = CongChucRef.__table__.alias("cc")
        dv = DonViRef.__table__.alias("dv")

        stmt = (
            select(
                KetQuaBaiKiemTra,
                cc.c.ho_ten.label("ho_ten"),
                cc.c.ma_cc.label("ma_cc"),
                dv.c.ten_don_vi.label("don_vi_ten"),
            )
            .join(cc, KetQuaBaiKiemTra.cong_chuc_id == cc.c.id)
            .outerjoin(dv, cc.c.don_vi_id == dv.c.id)
            .where(KetQuaBaiKiemTra.bai_kiem_tra_id == bai_kiem_tra_id)
            .order_by(KetQuaBaiKiemTra.ngay_lam.desc())
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        items = []
        for kq, ho_ten, ma_cc, don_vi_ten in rows:
            items.append({
                "id": kq.id,
                "cong_chuc_id": kq.cong_chuc_id,
                "ho_ten": ho_ten,
                "ma_cc": ma_cc,
                "don_vi_ten": don_vi_ten,
                "lan_thu": kq.lan_thu,
                "diem": kq.diem,
                "so_cau_dung": kq.so_cau_dung,
                "so_cau_sai": kq.so_cau_sai,
                "thoi_gian_lam_giay": kq.thoi_gian_lam_giay,
                "dat_yeu_cau": kq.dat_yeu_cau,
                "so_lan_vi_pham": kq.so_lan_vi_pham or 0,
                "ngay_lam": kq.ngay_lam,
                # THUC_HANH
                "bai_nop_url": kq.bai_nop_url,
                "bai_nop_ten_file": kq.bai_nop_ten_file,
                "bai_nop_size_bytes": kq.bai_nop_size_bytes,
                "bai_nop_content_type": kq.bai_nop_content_type,
                "trang_thai_cham": kq.trang_thai_cham,
                "nhan_xet": kq.nhan_xet,
                "ngay_nop": kq.ngay_nop,
                "ngay_cham": kq.ngay_cham,
            })

        return items

    # =========================================================================
    # 11. NOP VIDEO — BKT THUC HANH
    # =========================================================================
    async def nop_video(
        self,
        bai_kiem_tra_id: uuid.UUID,
        file: UploadFile,
        user: TokenPayload,
    ) -> dict:
        """Hoc vien nop video bai thuc hanh. Moi lan bam nop tao lan nop moi."""
        bkt = await self._get_bkt(bai_kiem_tra_id)
        user_uuid = uuid.UUID(user.sub)

        if bkt.loai_bai_kiem_tra != "THUC_HANH":
            raise HTTPException(
                status_code=400,
                detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Bài kiểm tra này không phải thực hành"}},
            )

        # Enforce ngay_mo/ngay_dong + gio_mo/gio_dong
        now = now_vn()
        today = now.date()
        current_time = now.strftime("%H:%M")
        if bkt.ngay_mo and today < bkt.ngay_mo:
            raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_011", "message": f"Bài kiểm tra chưa mở. Ngày mở: {bkt.ngay_mo}"}})
        if bkt.ngay_dong and today > bkt.ngay_dong:
            raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_012", "message": "Bài kiểm tra đã đóng"}})
        if bkt.gio_mo and current_time < bkt.gio_mo:
            raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_013", "message": f"Chưa đến giờ thi. Khung giờ: {bkt.gio_mo} - {bkt.gio_dong}"}})
        if bkt.gio_dong and current_time > bkt.gio_dong:
            raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_014", "message": f"Đã hết giờ thi. Khung giờ: {bkt.gio_mo} - {bkt.gio_dong}"}})

        # Check da dang ky + trang thai
        dk_r = await self.db.execute(
            select(DangKyKhoaHoc).where(
                DangKyKhoaHoc.cong_chuc_id == user_uuid,
                DangKyKhoaHoc.khoa_hoc_id == bkt.khoa_hoc_id,
            )
        )
        dk_obj = dk_r.scalar_one_or_none()
        if dk_obj is None:
            raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_003", "message": "Bạn chưa đăng ký khóa học này"}})
        if dk_obj.trang_thai in ("CHO_PHE_DUYET", "TU_CHOI", "BI_LOAI"):
            status_labels = {"CHO_PHE_DUYET": "chờ phê duyệt", "TU_CHOI": "bị từ chối", "BI_LOAI": "đã bị loại"}
            raise HTTPException(status_code=403, detail={"success": False, "error": {"code": "LMS_ERR_011", "message": f"Không thể nộp bài. Đăng ký {status_labels.get(dk_obj.trang_thai, dk_obj.trang_thai)}."}})

        # Dem so lan da nop (moi ban ghi ket qua = 1 lan)
        done_count_r = await self.db.execute(
            select(func.count(KetQuaBaiKiemTra.id)).where(
                KetQuaBaiKiemTra.cong_chuc_id == user_uuid,
                KetQuaBaiKiemTra.bai_kiem_tra_id == bai_kiem_tra_id,
            )
        )
        done_count = done_count_r.scalar() or 0
        if bkt.so_lan_lam_toi_da and done_count >= bkt.so_lan_lam_toi_da:
            raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "LMS_ERR_005", "message": f"Đã hết lượt nộp ({bkt.so_lan_lam_toi_da} lần)"}})

        # Validate extension (khop voi dinh_dang_cho_phep cua BKT)
        allowed_raw = (bkt.dinh_dang_cho_phep or "mp4,mov,webm").strip()
        allowed_exts = {
            e.strip().lstrip(".").lower()
            for e in allowed_raw.split(",")
            if e.strip()
        }
        filename = file.filename or ""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in allowed_exts:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": {
                        "code": "LMS_ERR_006",
                        "message": f"Định dạng '{ext}' không được chấp nhận. Cho phép: {', '.join(sorted(allowed_exts))}",
                    },
                },
            )

        # Luu file
        fs = FileService()
        result = await fs.save_file(file, sub_folder="bai-thuc-hanh")

        # Enforce giới hạn dung lượng theo BKT
        max_mb = bkt.dung_luong_toi_da_mb or 500
        if result["file_size"] > max_mb * 1024 * 1024:
            await fs.delete_file(result["file_url"])
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": {
                        "code": "LMS_ERR_007",
                        "message": f"File vượt quá {max_mb} MB theo cấu hình bài kiểm tra",
                    },
                },
            )

        # Tao lan nop moi
        lan_thu = done_count + 1
        now_dt = now_vn()
        kq = KetQuaBaiKiemTra(
            cong_chuc_id=user_uuid,
            bai_kiem_tra_id=bai_kiem_tra_id,
            lan_thu=lan_thu,
            ngay_lam=now_dt,
            ngay_nop=now_dt,
            bai_nop_url=result["file_url"],
            bai_nop_ten_file=result["file_name"],
            bai_nop_size_bytes=result["file_size"],
            bai_nop_content_type=result["content_type"],
            trang_thai_cham="CHO_CHAM",
        )
        self.db.add(kq)
        await self.db.flush()
        await self.db.refresh(kq)

        # Tang so_lan_lam_bai cua dang_ky
        if dk_obj:
            dk_obj.so_lan_lam_bai = (dk_obj.so_lan_lam_bai or 0) + 1

        await self.db.flush()
        return {
            "id": kq.id,
            "lan_thu": kq.lan_thu,
            "bai_nop_url": kq.bai_nop_url,
            "bai_nop_ten_file": kq.bai_nop_ten_file,
            "bai_nop_size_bytes": kq.bai_nop_size_bytes,
            "bai_nop_content_type": kq.bai_nop_content_type,
            "trang_thai_cham": kq.trang_thai_cham,
            "ngay_nop": kq.ngay_nop,
            "ngay_lam": kq.ngay_lam,
            "loai_bai_kiem_tra": "THUC_HANH",
        }

    # =========================================================================
    # 12. CHAM TAY — BKT THUC HANH (GV / QT)
    # =========================================================================
    async def cham_tay(
        self,
        ket_qua_id: uuid.UUID,
        diem: Decimal,
        nhan_xet: Optional[str],
        user: TokenPayload,
    ) -> dict:
        """Giang vien / QT cham diem bai thuc hanh."""
        # Only GV/QT/SUPER_ADMIN
        if not self._can_preview(user):
            raise HTTPException(
                status_code=403,
                detail={"success": False, "error": {"code": "LMS_ERR_008", "message": "Không có quyền chấm bài"}},
            )

        kq_r = await self.db.execute(select(KetQuaBaiKiemTra).where(KetQuaBaiKiemTra.id == ket_qua_id))
        kq = kq_r.scalar_one_or_none()
        if kq is None:
            raise HTTPException(status_code=404, detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Không tìm thấy kết quả thi"}})

        bkt = await self._get_bkt(kq.bai_kiem_tra_id)
        if bkt.loai_bai_kiem_tra != "THUC_HANH":
            raise HTTPException(
                status_code=400,
                detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Chỉ chấm tay cho bài thực hành"}},
            )
        if not kq.bai_nop_url:
            raise HTTPException(
                status_code=400,
                detail={"success": False, "error": {"code": "LMS_ERR_001", "message": "Học viên chưa nộp bài"}},
            )

        diem_decimal = Decimal(str(diem))
        kq.diem = diem_decimal
        kq.diem_cham_tay = diem_decimal
        kq.nhan_xet = nhan_xet
        kq.nguoi_cham_id = uuid.UUID(user.sub)
        kq.ngay_cham = now_vn()
        kq.trang_thai_cham = "DA_CHAM"
        kq.dat_yeu_cau = diem_decimal >= (bkt.diem_dat or Decimal("70"))

        await self.db.flush()
        await self.db.refresh(kq)

        # Cap nhat dang_ky + tinh lai phan tram hoan thanh (keu tu bai_hoc_service)
        dk_r = await self.db.execute(
            select(DangKyKhoaHoc).where(
                DangKyKhoaHoc.cong_chuc_id == kq.cong_chuc_id,
                DangKyKhoaHoc.khoa_hoc_id == bkt.khoa_hoc_id,
            )
        )
        dk = dk_r.scalar_one_or_none()
        if dk:
            if kq.dat_yeu_cau and (dk.diem_cao_nhat is None or diem_decimal > dk.diem_cao_nhat):
                dk.diem_cao_nhat = diem_decimal
            await self.db.flush()
            from lms_service.services.bai_hoc_service import BaiHocService
            bh_svc = BaiHocService(self.db)
            await bh_svc._tinh_lai_phan_tram(dk, bkt.khoa_hoc_id, kq.cong_chuc_id)

        return {
            "id": kq.id,
            "lan_thu": kq.lan_thu,
            "diem": kq.diem,
            "dat_yeu_cau": kq.dat_yeu_cau,
            "nhan_xet": kq.nhan_xet,
            "trang_thai_cham": kq.trang_thai_cham,
            "ngay_cham": kq.ngay_cham,
            "ngay_lam": kq.ngay_lam,
        }
