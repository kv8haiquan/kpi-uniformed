"""
lms_service/services/thi_sinh_service.py
========================================
Business logic: giao thi sinh, bat dau thi (random de), nop bai (cham diem),
xem ket qua, export Excel.
"""

import random
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.models.base import CongChucRef, DonViRef
from lms_service.models.ky_thi import KyThi
from lms_service.models.cau_truc_de import CauTrucDe
from lms_service.models.thi_sinh import ThiSinh
from lms_service.models.linh_vuc import LinhVuc
from lms_service.models.vi_tri_viec_lam import ViTriViecLam
from lms_service.models.cau_hoi import CauHoi
from lms_service.models.cau_hoi_dgnl import CauHoiDgnl
from lms_service.schemas.thi_sinh import (
    ThiSinhBatchCreate, ThiSinhResponse,
    NopBaiRequest, KetQuaResponse, DiemLinhVuc,
)
from lms_service.services.thong_bao_helper import gui_thong_bao_bulk
from shared.auth import TokenPayload


class ThiSinhService:
    """Service thi sinh DGNL."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _is_manager(self, user: TokenPayload) -> bool:
        return user.vai_tro == "SUPER_ADMIN" or "QT_DAO_TAO" in (user.platform_roles or [])

    def _is_lanh_dao(self, user: TokenPayload) -> bool:
        return user.vai_tro in ("CCT", "PCCT") or getattr(user, "is_lanh_dao", False)

    async def _get_ky_thi(self, ky_thi_id: uuid.UUID) -> KyThi:
        stmt = select(KyThi).where(KyThi.id == ky_thi_id, KyThi.is_active == True)
        result = await self.db.execute(stmt)
        kt = result.scalar_one_or_none()
        if not kt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": {"code": "DGNL_010", "message": "Kỳ thi không tồn tại"}},
            )
        return kt

    # ================================================================
    # GIAO THI SINH
    # ================================================================

    async def giao_thi_sinh(
        self, ky_thi_id: uuid.UUID, data: ThiSinhBatchCreate, user: TokenPayload
    ) -> dict:
        """Giao thi sinh theo danh sach hoac theo don vi."""
        kt = await self._get_ky_thi(ky_thi_id)
        if kt.trang_thai not in ("NHAP", "CHO_DUYET", "DANG_MO"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "DGNL_021", "message": "Không thể giao thí sinh khi kỳ thi đã đóng"}},
            )

        items_to_add = []

        if data.danh_sach:
            # Giao theo danh sach cu the
            for item in data.danh_sach:
                items_to_add.append((item.cong_chuc_id, item.vi_tri_id))
        elif data.don_vi_ids and data.vi_tri_id:
            # Giao theo don vi
            cc_table = CongChucRef.__table__
            stmt = select(cc_table.c.id).where(
                cc_table.c.don_vi_id.in_(data.don_vi_ids),
                cc_table.c.is_active == True,
            )
            result = await self.db.execute(stmt)
            cc_ids = result.scalars().all()
            for cc_id in cc_ids:
                items_to_add.append((cc_id, data.vi_tri_id))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "DGNL_022", "message": "Phải cung cấp danh_sach hoặc (don_vi_ids + vi_tri_id)"}},
            )

        thanh_cong = 0
        bo_qua = 0
        loi = []

        for cc_id, vt_id in items_to_add:
            # Check da ton tai
            existing = await self.db.execute(
                select(ThiSinh).where(
                    ThiSinh.ky_thi_id == ky_thi_id,
                    ThiSinh.cong_chuc_id == cc_id,
                )
            )
            if existing.scalar_one_or_none():
                bo_qua += 1
                continue

            # Validate vi tri ton tai
            vt_r = await self.db.execute(
                select(ViTriViecLam.id).where(ViTriViecLam.id == vt_id, ViTriViecLam.is_active == True)
            )
            if not vt_r.scalar_one_or_none():
                loi.append(f"Vị trí {vt_id} không tồn tại")
                continue

            ts = ThiSinh(
                ky_thi_id=ky_thi_id,
                cong_chuc_id=cc_id,
                vi_tri_id=vt_id,
                trang_thai="CHUA_THI",
            )
            self.db.add(ts)
            thanh_cong += 1

        await self.db.commit()

        # Gui thong bao cho cac thi sinh vua duoc giao
        if thanh_cong > 0:
            new_cc_ids = [cc_id for cc_id, _ in items_to_add
                          if any(cc_id == ts_cc for ts_cc, _ in items_to_add)]
            # Lay danh sach cc_id thuc su them thanh cong (loai bo_qua + loi)
            ts_result = await self.db.execute(
                select(ThiSinh.cong_chuc_id).where(ThiSinh.ky_thi_id == ky_thi_id)
            )
            all_cc_ids = ts_result.scalars().all()
            await gui_thong_bao_bulk(
                nguoi_nhan_ids=all_cc_ids[-thanh_cong:] if thanh_cong <= len(all_cc_ids) else all_cc_ids,
                tieu_de=f"Bạn được giao thi: {kt.ten_ky_thi}",
                noi_dung=f"Kỳ thi \"{kt.ten_ky_thi}\" ({kt.ma_ky_thi}). Vui lòng vào mục Đào tạo → Kỳ thi ĐGNL để xem chi tiết.",
                muc_do="QUAN_TRONG",
                link_url="/dao-tao/ky-thi",
                doi_tuong_type="KY_THI",
                doi_tuong_id=ky_thi_id,
            )

        return {
            "thanh_cong": thanh_cong,
            "bo_qua": bo_qua,
            "loi": loi,
            "tong": len(items_to_add),
        }

    async def danh_sach_thi_sinh(
        self, ky_thi_id: uuid.UUID, user: TokenPayload,
        trang_thai: Optional[str] = None,
        page: int = 1, page_size: int = 50,
    ) -> dict:
        """Danh sach thi sinh + ket qua."""
        await self._get_ky_thi(ky_thi_id)

        cc = CongChucRef.__table__.alias("cc")
        dv = DonViRef.__table__.alias("dv")

        base_where = [ThiSinh.ky_thi_id == ky_thi_id]
        if trang_thai:
            base_where.append(ThiSinh.trang_thai == trang_thai)

        # Lanh dao chi xem CBCC don vi minh
        if self._is_lanh_dao(user) and not self._is_manager(user):
            don_vi_id = getattr(user, "don_vi_id", None)
            if don_vi_id:
                base_where.append(
                    ThiSinh.cong_chuc_id.in_(
                        select(cc.c.id).where(cc.c.don_vi_id == uuid.UUID(don_vi_id))
                    )
                )

        count_stmt = select(func.count()).select_from(ThiSinh).where(*base_where)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(
                ThiSinh,
                cc.c.ho_ten,
                cc.c.ma_cc,
                dv.c.ten_don_vi.label("don_vi_ten"),
                ViTriViecLam.ten_vi_tri.label("vi_tri_ten"),
            )
            .outerjoin(cc, ThiSinh.cong_chuc_id == cc.c.id)
            .outerjoin(dv, cc.c.don_vi_id == dv.c.id)
            .outerjoin(ViTriViecLam, ThiSinh.vi_tri_id == ViTriViecLam.id)
            .where(*base_where)
            .order_by(cc.c.ho_ten.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        items = []
        for ts, ho_ten, ma_cc, dv_ten, vt_ten in rows:
            items.append({
                **{c.key: getattr(ts, c.key) for c in ts.__table__.columns},
                "ho_ten": ho_ten,
                "ma_cc": ma_cc,
                "don_vi_ten": dv_ten,
                "vi_tri_ten": vt_ten,
            })

        return {
            "items": items,
            "pagination": {
                "page": page, "page_size": page_size,
                "total_items": total,
                "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
            },
        }

    async def xoa_thi_sinh(
        self, ky_thi_id: uuid.UUID, cong_chuc_id: uuid.UUID, user: TokenPayload
    ) -> None:
        """Xoa thi sinh — chi khi CHUA_THI."""
        stmt = select(ThiSinh).where(
            ThiSinh.ky_thi_id == ky_thi_id,
            ThiSinh.cong_chuc_id == cong_chuc_id,
        )
        result = await self.db.execute(stmt)
        ts = result.scalar_one_or_none()
        if not ts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": {"code": "DGNL_023", "message": "Thí sinh không tồn tại trong kỳ thi này"}},
            )
        if ts.trang_thai != "CHUA_THI":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "DGNL_024", "message": "Chỉ được xóa thí sinh chưa thi"}},
            )

        await self.db.delete(ts)
        await self.db.commit()

    # ================================================================
    # BAT DAU THI — RANDOM DE
    # ================================================================

    async def bat_dau_thi(self, ky_thi_id: uuid.UUID, user: TokenPayload) -> dict:
        """Bat dau thi: random de thi cho thi sinh."""
        kt = await self._get_ky_thi(ky_thi_id)

        # Validate trang thai ky thi
        if kt.trang_thai != "DANG_MO":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "DGNL_025", "message": "Kỳ thi chưa mở hoặc đã đóng"}},
            )

        # Validate thoi gian
        now = datetime.utcnow()
        if now < kt.ngay_bat_dau:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "DGNL_026", "message": "Chưa đến thời gian thi"}},
            )
        if now > kt.ngay_ket_thuc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "DGNL_027", "message": "Đã hết thời gian thi"}},
            )

        # Lay thi sinh
        cc_id = uuid.UUID(user.sub)
        stmt = select(ThiSinh).where(
            ThiSinh.ky_thi_id == ky_thi_id,
            ThiSinh.cong_chuc_id == cc_id,
        )
        result = await self.db.execute(stmt)
        ts = result.scalar_one_or_none()
        if not ts:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"success": False, "error": {"code": "DGNL_028", "message": "Bạn không được giao thi kỳ thi này"}},
            )

        # Check thi lai
        if ts.trang_thai == "DANG_THI":
            # Dang thi — tra lai de cu
            cau_hoi_list = await self._lay_de_thi_hien_tai(ts)
            return {
                "thi_sinh_id": ts.id,
                "thoi_gian_con_lai_giay": self._tinh_thoi_gian_con(ts, kt),
                "tong_so_cau": ts.tong_so_cau or len(ts.de_thi_ids or []),
                "cau_hoi": cau_hoi_list,
            }

        if ts.trang_thai == "DA_NOP":
            # Check con luot thi lai khong
            if ts.lan_thi_hien_tai >= (kt.so_lan_thi_toi_da or 1):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "error": {"code": "DGNL_029", "message": f"Đã hết lượt thi (tối đa {kt.so_lan_thi_toi_da} lần)"}},
                )
            # Luu ket qua lan truoc vao lich_su
            lich_su = ts.lich_su_thi or []
            lich_su.append({
                "lan": ts.lan_thi_hien_tai,
                "diem": float(ts.diem_tong) if ts.diem_tong else 0,
                "xep_loai": ts.xep_loai,
                "thoi_gian_nop": ts.thoi_gian_nop.isoformat() if ts.thoi_gian_nop else None,
                "so_cau_dung": ts.so_cau_dung,
            })
            ts.lich_su_thi = lich_su

        if ts.trang_thai == "VANG":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "DGNL_030", "message": "Bạn đã bị đánh dấu vắng, không thể thi"}},
            )

        # Random de thi
        de_thi_ids = await self._tao_de_thi(kt, ts)

        # Cap nhat thi sinh
        ts.de_thi_ids = [str(cid) for cid in de_thi_ids]
        ts.chi_tiet_tra_loi = []
        ts.trang_thai = "DANG_THI"
        ts.lan_thi_hien_tai = (ts.lan_thi_hien_tai or 0) + 1
        ts.thoi_gian_bat_dau = datetime.utcnow()
        ts.thoi_gian_nop = None
        ts.tong_so_cau = len(de_thi_ids)
        ts.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(ts)

        # Lay cau hoi (khong co dap an)
        cau_hoi_list = await self._lay_de_thi_hien_tai(ts)

        return {
            "thi_sinh_id": ts.id,
            "thoi_gian_con_lai_giay": kt.thoi_gian_lam_bai_phut * 60,
            "tong_so_cau": len(de_thi_ids),
            "cau_hoi": cau_hoi_list,
        }

    async def _tao_de_thi(self, kt: KyThi, ts: ThiSinh) -> list[uuid.UUID]:
        """Random de thi theo cau truc de cua vi tri."""
        # Lay cau truc de cho vi tri cua thi sinh
        stmt = select(CauTrucDe).where(
            CauTrucDe.ky_thi_id == kt.id,
            CauTrucDe.vi_tri_id == ts.vi_tri_id,
        )
        result = await self.db.execute(stmt)
        cau_trucs = result.scalars().all()

        if not cau_trucs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "DGNL_031", "message": "Chưa cấu hình cấu trúc đề cho vị trí này"}},
            )

        de_thi: list[uuid.UUID] = []

        for ct in cau_trucs:
            for do_kho, so_cau in [
                ("DE", ct.so_cau_de or 0),
                ("TRUNG_BINH", ct.so_cau_trung_binh or 0),
                ("KHO", ct.so_cau_kho or 0),
            ]:
                if so_cau <= 0:
                    continue

                # Random tu ngan hang DGNL
                stmt = (
                    select(CauHoiDgnl.id)
                    .where(
                        CauHoiDgnl.linh_vuc_id == ct.linh_vuc_id,
                        CauHoiDgnl.do_kho == do_kho,
                        CauHoiDgnl.is_active == True,
                    )
                    .order_by(func.random())
                    .limit(so_cau)
                )
                r = await self.db.execute(stmt)
                ids = r.scalars().all()

                if len(ids) < so_cau:
                    # Lay ten linh vuc
                    lv_r = await self.db.execute(select(LinhVuc.ten_linh_vuc).where(LinhVuc.id == ct.linh_vuc_id))
                    lv_ten = lv_r.scalar() or str(ct.linh_vuc_id)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "success": False,
                            "error": {
                                "code": "DGNL_032",
                                "message": f"Không đủ câu hỏi {do_kho} cho lĩnh vực {lv_ten} "
                                           f"(cần {so_cau}, có {len(ids)})",
                            },
                        },
                    )
                de_thi.extend(ids)

        # Xao tron toan bo
        if kt.tron_cau_hoi:
            random.shuffle(de_thi)

        return de_thi

    async def _lay_de_thi_hien_tai(self, ts: ThiSinh) -> list[dict]:
        """Lay danh sach cau hoi cua de thi (KHONG co dap an dung)."""
        if not ts.de_thi_ids:
            return []

        cau_hoi_ids = [uuid.UUID(cid) for cid in ts.de_thi_ids]
        stmt = select(CauHoiDgnl).where(CauHoiDgnl.id.in_(cau_hoi_ids))
        result = await self.db.execute(stmt)
        ch_map = {ch.id: ch for ch in result.scalars().all()}

        # Lay ten linh vuc
        lv_ids = set(ch.linh_vuc_id for ch in ch_map.values() if ch.linh_vuc_id)
        lv_map = {}
        if lv_ids:
            lv_r = await self.db.execute(select(LinhVuc).where(LinhVuc.id.in_(lv_ids)))
            lv_map = {lv.id: lv.ten_linh_vuc for lv in lv_r.scalars().all()}

        cau_hoi_list = []
        for i, cid in enumerate(cau_hoi_ids):
            ch = ch_map.get(cid)
            if not ch:
                continue

            # Xay dung lua chon (khong co dap an dung)
            lua_chon = None
            if ch.dap_an and ch.loai in ("TRAC_NGHIEM_1", "TRAC_NGHIEM_NHIEU", "DUNG_SAI"):
                dap_an = ch.dap_an
                if isinstance(dap_an, dict) and "lua_chon" in dap_an:
                    lua_chon = dap_an["lua_chon"]
                elif isinstance(dap_an, list):
                    lua_chon = [{"key": d.get("key", ""), "noi_dung": d.get("noi_dung", "")} for d in dap_an if isinstance(d, dict)]

            cau_hoi_list.append({
                "id": str(ch.id),
                "thu_tu": i + 1,
                "noi_dung": ch.noi_dung,
                "loai": ch.loai,
                "diem": float(ch.diem) if ch.diem else 1.0,
                "lua_chon": lua_chon,
                "linh_vuc": lv_map.get(ch.linh_vuc_id),
            })

        return cau_hoi_list

    def _tinh_thoi_gian_con(self, ts: ThiSinh, kt: KyThi) -> int:
        """Tinh so giay con lai."""
        if not ts.thoi_gian_bat_dau:
            return kt.thoi_gian_lam_bai_phut * 60
        now = datetime.utcnow()
        bd = ts.thoi_gian_bat_dau
        elapsed = (now - bd).total_seconds()
        remaining = (kt.thoi_gian_lam_bai_phut * 60) - elapsed
        return max(0, int(remaining))

    # ================================================================
    # NOP BAI — CHAM DIEM
    # ================================================================

    async def nop_bai(
        self, ky_thi_id: uuid.UUID, data: NopBaiRequest, user: TokenPayload
    ) -> KetQuaResponse:
        """Nop bai va cham diem tu dong."""
        kt = await self._get_ky_thi(ky_thi_id)
        cc_id = uuid.UUID(user.sub)

        stmt = select(ThiSinh).where(
            ThiSinh.ky_thi_id == ky_thi_id,
            ThiSinh.cong_chuc_id == cc_id,
        )
        result = await self.db.execute(stmt)
        ts = result.scalar_one_or_none()

        if not ts:
            raise HTTPException(status_code=404, detail={"success": False, "error": {"code": "DGNL_028", "message": "Bạn không có trong kỳ thi này"}})
        if ts.trang_thai != "DANG_THI":
            raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "DGNL_033", "message": "Bạn chưa bắt đầu thi hoặc đã nộp bài"}})

        # Cham diem
        cau_hoi_ids = [uuid.UUID(cid) for cid in (ts.de_thi_ids or [])]
        ch_stmt = select(CauHoiDgnl).where(CauHoiDgnl.id.in_(cau_hoi_ids))
        ch_result = await self.db.execute(ch_stmt)
        ch_map = {ch.id: ch for ch in ch_result.scalars().all()}

        # Map tra loi
        tra_loi_map = {tl.cau_hoi_id: tl.tra_loi for tl in data.cau_tra_loi}

        chi_tiet = []
        tong_dung = 0
        tong_sai = 0
        diem_lv: dict[uuid.UUID, dict] = {}  # linh_vuc_id -> {dung, tong}

        for cid in cau_hoi_ids:
            ch = ch_map.get(cid)
            if not ch:
                continue

            tra_loi = tra_loi_map.get(cid)
            dung = self._cham_1_cau(ch, tra_loi)

            if dung:
                tong_dung += 1
            else:
                tong_sai += 1

            # Diem theo linh vuc
            lv_id = ch.linh_vuc_id
            if lv_id:
                if lv_id not in diem_lv:
                    diem_lv[lv_id] = {"dung": 0, "tong": 0}
                diem_lv[lv_id]["tong"] += 1
                if dung:
                    diem_lv[lv_id]["dung"] += 1

            chi_tiet.append({
                "cau_hoi_id": str(cid),
                "tra_loi": tra_loi,
                "dap_an_dung": ch.dap_an,
                "dung": dung,
            })

        tong_cau = len(cau_hoi_ids)
        diem_tong = round(Decimal(tong_dung) / Decimal(tong_cau) * 100, 2) if tong_cau > 0 else Decimal("0")
        xep_loai = "DAT" if diem_tong >= (kt.diem_dat or Decimal("50")) else "KHONG_DAT"

        # Tinh diem theo linh vuc
        diem_theo_lv = {}
        lv_ids = list(diem_lv.keys())
        if lv_ids:
            lv_r = await self.db.execute(select(LinhVuc).where(LinhVuc.id.in_(lv_ids)))
            lv_name_map = {lv.id: lv.ma_linh_vuc for lv in lv_r.scalars().all()}
            for lv_id, stats in diem_lv.items():
                ma = lv_name_map.get(lv_id, str(lv_id))
                phan_tram = round(stats["dung"] / stats["tong"] * 100, 1) if stats["tong"] > 0 else 0
                diem_theo_lv[ma] = {"dung": stats["dung"], "tong": stats["tong"], "phan_tram": phan_tram}

        # Thoi gian lam bai
        now = datetime.utcnow()
        thoi_gian_lam = 0
        if ts.thoi_gian_bat_dau:
            bd = ts.thoi_gian_bat_dau
            thoi_gian_lam = int((now - bd).total_seconds())

        # Logic thi lai: chi cap nhat ket qua neu diem cao hon
        diem_cu = ts.diem_tong
        is_better = diem_cu is None or diem_tong > diem_cu

        if is_better:
            ts.diem_tong = diem_tong
            ts.xep_loai = xep_loai
            ts.so_cau_dung = tong_dung
            ts.so_cau_sai = tong_sai
            ts.tong_so_cau = tong_cau
            ts.diem_theo_linh_vuc = diem_theo_lv

        ts.chi_tiet_tra_loi = chi_tiet
        ts.trang_thai = "DA_NOP"
        ts.thoi_gian_nop = now
        ts.thoi_gian_lam_giay = thoi_gian_lam
        ts.updated_at = now

        await self.db.commit()
        await self.db.refresh(ts)

        return await self._build_ket_qua(ts, kt)

    def _cham_1_cau(self, ch: CauHoiDgnl, tra_loi: Optional[dict]) -> bool:
        """Cham 1 cau hoi. Tra ve True/False."""
        if tra_loi is None:
            return False

        dap_an = ch.dap_an
        if not dap_an:
            return False

        loai = ch.loai

        if loai == "TRAC_NGHIEM_1":
            # tra_loi: {"dap_an": "A"}, dap_an: {"dap_an_dung": "A", ...} hoac {"lua_chon": [...], "dap_an_dung": "A"}
            correct = dap_an.get("dap_an_dung", "")
            answer = tra_loi.get("dap_an", "")
            return str(answer).strip().upper() == str(correct).strip().upper()

        elif loai == "TRAC_NGHIEM_NHIEU":
            # tra_loi: {"dap_an": ["A", "C"]}, dap_an: {"dap_an_dung": ["A", "C"]}
            correct = set(str(x).upper() for x in (dap_an.get("dap_an_dung") or []))
            answer = set(str(x).upper() for x in (tra_loi.get("dap_an") or []))
            return correct == answer

        elif loai == "DUNG_SAI":
            correct = str(dap_an.get("dap_an_dung", "")).upper()
            answer = str(tra_loi.get("dap_an", "")).upper()
            return correct == answer

        elif loai == "GHEP_DOI":
            correct = dap_an.get("dap_an_dung", {})
            answer = tra_loi.get("dap_an", {})
            return correct == answer

        # TU_LUAN: khong cham tu dong
        return False

    # ================================================================
    # KET QUA
    # ================================================================

    async def ket_qua_ca_nhan(self, ky_thi_id: uuid.UUID, user: TokenPayload) -> KetQuaResponse:
        """Xem ket qua ca nhan."""
        kt = await self._get_ky_thi(ky_thi_id)
        cc_id = uuid.UUID(user.sub)

        stmt = select(ThiSinh).where(ThiSinh.ky_thi_id == ky_thi_id, ThiSinh.cong_chuc_id == cc_id)
        result = await self.db.execute(stmt)
        ts = result.scalar_one_or_none()
        if not ts:
            raise HTTPException(status_code=404, detail={"success": False, "error": {"code": "DGNL_028", "message": "Bạn không có trong kỳ thi này"}})
        if ts.trang_thai not in ("DA_NOP",):
            raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "DGNL_034", "message": "Bạn chưa nộp bài"}})

        return await self._build_ket_qua(ts, kt)

    async def ket_qua_cbcc(
        self, ky_thi_id: uuid.UUID, cong_chuc_id: uuid.UUID, user: TokenPayload
    ) -> KetQuaResponse:
        """Xem ket qua 1 CBCC cu the (QT/LD)."""
        kt = await self._get_ky_thi(ky_thi_id)

        stmt = select(ThiSinh).where(ThiSinh.ky_thi_id == ky_thi_id, ThiSinh.cong_chuc_id == cong_chuc_id)
        result = await self.db.execute(stmt)
        ts = result.scalar_one_or_none()
        if not ts:
            raise HTTPException(status_code=404, detail={"success": False, "error": {"code": "DGNL_023", "message": "Thí sinh không tồn tại trong kỳ thi này"}})

        return await self._build_ket_qua(ts, kt)

    async def _build_ket_qua(self, ts: ThiSinh, kt: KyThi) -> KetQuaResponse:
        """Build response ket qua."""
        # Lay thong tin thi sinh
        cc = CongChucRef.__table__
        dv = DonViRef.__table__
        stmt = (
            select(cc.c.ho_ten, cc.c.ma_cc, dv.c.ten_don_vi)
            .outerjoin(dv, cc.c.don_vi_id == dv.c.id)
            .where(cc.c.id == ts.cong_chuc_id)
        )
        r = await self.db.execute(stmt)
        cc_row = r.first()

        vt_r = await self.db.execute(select(ViTriViecLam.ten_vi_tri).where(ViTriViecLam.id == ts.vi_tri_id))
        vt_ten = vt_r.scalar() or ""

        # Diem theo linh vuc
        diem_lv_list = []
        if ts.diem_theo_linh_vuc:
            # Lay ten linh vuc tu ma
            for ma, stats in ts.diem_theo_linh_vuc.items():
                lv_r = await self.db.execute(
                    select(LinhVuc.ten_linh_vuc).where(LinhVuc.ma_linh_vuc == ma)
                )
                lv_ten = lv_r.scalar() or ma
                diem_lv_list.append(DiemLinhVuc(
                    linh_vuc=lv_ten,
                    so_cau_dung=stats.get("dung", 0),
                    tong_cau=stats.get("tong", 0),
                    phan_tram=stats.get("phan_tram", 0),
                ))

        # Chi tiet (chi hien neu cho phep)
        chi_tiet = None
        if kt.hien_dap_an and ts.chi_tiet_tra_loi:
            chi_tiet = ts.chi_tiet_tra_loi

        return KetQuaResponse(
            ky_thi={"id": str(kt.id), "ten_ky_thi": kt.ten_ky_thi, "diem_dat": float(kt.diem_dat) if kt.diem_dat else 50},
            thi_sinh={
                "ho_ten": cc_row.ho_ten if cc_row else None,
                "ma_cc": cc_row.ma_cc if cc_row else None,
                "don_vi": cc_row.ten_don_vi if cc_row else None,
                "vi_tri_thi": vt_ten,
            },
            ket_qua={
                "diem_tong": float(ts.diem_tong) if ts.diem_tong else 0,
                "xep_loai": ts.xep_loai,
                "so_cau_dung": ts.so_cau_dung or 0,
                "so_cau_sai": ts.so_cau_sai or 0,
                "tong_so_cau": ts.tong_so_cau or 0,
                "thoi_gian_lam_giay": ts.thoi_gian_lam_giay or 0,
                "lan_thi": ts.lan_thi_hien_tai or 0,
            },
            diem_theo_linh_vuc=diem_lv_list,
            chi_tiet=chi_tiet,
            lich_su_thi=ts.lich_su_thi if ts.lich_su_thi else None,
        )

    # ================================================================
    # EXPORT EXCEL
    # ================================================================

    async def export_excel(self, ky_thi_id: uuid.UUID, user: TokenPayload) -> bytes:
        """Export ket qua ky thi ra Excel."""
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        import io

        kt = await self._get_ky_thi(ky_thi_id)

        # Lay danh sach thi sinh
        cc = CongChucRef.__table__.alias("cc")
        dv = DonViRef.__table__.alias("dv")
        stmt = (
            select(
                ThiSinh,
                cc.c.ho_ten, cc.c.ma_cc,
                dv.c.ten_don_vi.label("don_vi_ten"),
                ViTriViecLam.ten_vi_tri.label("vi_tri_ten"),
            )
            .outerjoin(cc, ThiSinh.cong_chuc_id == cc.c.id)
            .outerjoin(dv, cc.c.don_vi_id == dv.c.id)
            .outerjoin(ViTriViecLam, ThiSinh.vi_tri_id == ViTriViecLam.id)
            .where(ThiSinh.ky_thi_id == ky_thi_id)
            .order_by(cc.c.ho_ten.asc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        # Lay danh sach linh vuc de lam header
        lv_stmt = select(LinhVuc).where(LinhVuc.is_active == True).order_by(LinhVuc.thu_tu)
        lv_result = await self.db.execute(lv_stmt)
        all_lv = lv_result.scalars().all()
        lv_ma_to_ten = {lv.ma_linh_vuc: lv.ten_linh_vuc for lv in all_lv}

        wb = Workbook()
        ws = wb.active
        ws.title = "Kết quả kỳ thi"

        # Header styles
        header_font = Font(bold=True, size=11)
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font_white = Font(bold=True, size=11, color="FFFFFF")
        center = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style="thin"), right=Side(style="thin"),
            top=Side(style="thin"), bottom=Side(style="thin"),
        )

        # Title
        ws.merge_cells("A1:H1")
        ws["A1"] = f"KẾT QUẢ KỲ THI: {kt.ten_ky_thi}"
        ws["A1"].font = Font(bold=True, size=14)
        ws["A1"].alignment = center

        ws.merge_cells("A2:H2")
        ws["A2"] = f"Mã kỳ thi: {kt.ma_ky_thi} | Điểm đạt: {kt.diem_dat}%"
        ws["A2"].font = Font(size=11)

        # Headers
        base_headers = ["STT", "Mã CC", "Họ tên", "Đơn vị", "Vị trí thi",
                        "Trạng thái", "Điểm (%)", "Xếp loại", "Số câu đúng",
                        "Tổng câu", "Thời gian (phút)", "Lần thi"]
        lv_headers = [lv_ma_to_ten.get(ma, ma) for ma in lv_ma_to_ten.keys()]
        headers = base_headers + lv_headers

        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_idx, value=h)
            cell.font = header_font_white
            cell.fill = header_fill
            cell.alignment = center
            cell.border = thin_border

        # Data
        dat_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        kdat_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

        for i, (ts, ho_ten, ma_cc, dv_ten, vt_ten) in enumerate(rows, 1):
            row_idx = i + 4
            thoi_gian_phut = round(ts.thoi_gian_lam_giay / 60, 1) if ts.thoi_gian_lam_giay else ""

            base_data = [
                i, ma_cc, ho_ten, dv_ten, vt_ten,
                ts.trang_thai, float(ts.diem_tong) if ts.diem_tong else "",
                ts.xep_loai or "", ts.so_cau_dung or "",
                ts.tong_so_cau or "", thoi_gian_phut,
                ts.lan_thi_hien_tai or 0,
            ]

            # Diem theo linh vuc
            lv_data = []
            for ma in lv_ma_to_ten.keys():
                if ts.diem_theo_linh_vuc and ma in ts.diem_theo_linh_vuc:
                    stats = ts.diem_theo_linh_vuc[ma]
                    lv_data.append(f"{stats.get('dung', 0)}/{stats.get('tong', 0)}")
                else:
                    lv_data.append("")

            all_data = base_data + lv_data

            for col_idx, val in enumerate(all_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.border = thin_border
                cell.alignment = center

            # Highlight xep loai
            xep_loai_cell = ws.cell(row=row_idx, column=8)
            if ts.xep_loai == "DAT":
                xep_loai_cell.fill = dat_fill
            elif ts.xep_loai == "KHONG_DAT":
                xep_loai_cell.fill = kdat_fill

        # Auto width
        for col in ws.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = min(max_length + 3, 30)

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()
