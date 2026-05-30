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
        # Chi cap CCT/PCCT moi duoc xem ket qua DGNL (yeu cau nghiep vu).
        # TDV/PDV (is_lanh_dao=True) bi chan boi day du don vi nho ko nen thay
        # bai lam cua thi sinh don vi khac.
        return user.vai_tro in ("CCT", "PCCT")

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
                # Override raw lich_su_thi voi summary projection (an chi_tiet_tra_loi)
                "lich_su_thi": self._project_lich_su_summary(ts.lich_su_thi),
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
            # Dang thi — tra lai de cu kem bai lam nhap (resume autosave)
            cau_hoi_list = await self._lay_de_thi_hien_tai(ts)
            return {
                "thi_sinh_id": ts.id,
                "thoi_gian_con_lai_giay": self._tinh_thoi_gian_con(ts, kt),
                "tong_so_cau": ts.tong_so_cau or len(ts.de_thi_ids or []),
                "cau_hoi": cau_hoi_list,
                "dang_tiep_tuc": True,
                "chi_tiet_nhap": ts.chi_tiet_nhap or [],
                "so_lan_vi_pham": ts.so_lan_vi_pham or 0,
            }

        if ts.trang_thai == "DA_NOP":
            # Check con luot thi lai khong
            if ts.lan_thi_hien_tai >= (kt.so_lan_thi_toi_da or 1):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "error": {"code": "DGNL_029", "message": f"Đã hết lượt thi (tối đa {kt.so_lan_thi_toi_da} lần)"}},
                )
            # Snapshot lan vua nop vao lich_su (upsert idempotent theo lan).
            # 30/05/2026: mo rong shape -> luu day du chi_tiet_tra_loi, de_thi_ids,
            # diem_theo_linh_vuc... de QT_DAO_TAO drill-down lai bai lam lan cu.
            self._upsert_lan_thi(ts, self._snapshot_lan_thi(ts))

        if ts.trang_thai == "VANG":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "DGNL_030", "message": "Bạn đã bị đánh dấu vắng, không thể thi"}},
            )

        # Random de thi
        de_thi_ids = await self._tao_de_thi(kt, ts)

        # Cap nhat thi sinh — reset toan bo state cua lan thi truoc (Bug A fix
        # 27/05/2026): khong reset cac field diem cu -> kep DANG_THI van hien
        # diem cu, gay nham lan cho QT_DAO_TAO.
        ts.de_thi_ids = [str(cid) for cid in de_thi_ids]
        ts.chi_tiet_tra_loi = []
        ts.chi_tiet_nhap = None
        ts.so_lan_vi_pham = 0
        ts.trang_thai = "DANG_THI"
        ts.lan_thi_hien_tai = (ts.lan_thi_hien_tai or 0) + 1
        ts.thoi_gian_bat_dau = datetime.utcnow()
        ts.thoi_gian_nop = None
        ts.thoi_gian_lam_giay = None
        ts.tong_so_cau = len(de_thi_ids)
        ts.diem_tong = None
        ts.xep_loai = None
        ts.so_cau_dung = None
        ts.so_cau_sai = None
        ts.diem_theo_linh_vuc = {}
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
            "dang_tiep_tuc": False,
            "chi_tiet_nhap": [],
            "so_lan_vi_pham": 0,
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
        # Bug B fix (27/05/2026): nop bai idempotent. Neu da DA_NOP, tra lai ket
        # qua da co thay vi loi 400 — tranh truong hop user retry sau khi network
        # timeout o lan submit dau (commit DB thanh cong, response mat).
        if ts.trang_thai == "DA_NOP":
            return await self._build_ket_qua(ts, kt)
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
                "dap_an_dung": self._normalize_dap_an_dung(ch.dap_an),
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

        # Cap nhat 27/05/2026: luon ghi diem lan hien tai (latest-score). De biet
        # diem cao nhat -> tra cuu trong lich_su_thi. Ly do: tranh nham lan giua
        # DANG_THI va "diem cu" lan truoc.
        ts.diem_tong = diem_tong
        ts.xep_loai = xep_loai
        ts.so_cau_dung = tong_dung
        ts.so_cau_sai = tong_sai
        ts.tong_so_cau = tong_cau
        ts.diem_theo_linh_vuc = diem_theo_lv

        ts.chi_tiet_tra_loi = chi_tiet
        ts.chi_tiet_nhap = None  # clear autosave draft sau khi nop
        ts.trang_thai = "DA_NOP"
        ts.thoi_gian_nop = now
        ts.thoi_gian_lam_giay = thoi_gian_lam
        ts.updated_at = now

        # Snapshot lan vua nop vao lich_su_thi (upsert theo lan).
        # Ly do: voi ky thi 1 lan (so_lan_thi_toi_da=1), bat_dau_thi khong duoc
        # goi lai -> neu chi snapshot tai bat_dau_thi thi lich_su_thi mai mai
        # rong va trang thong-ke khong drill-down duoc lan duy nhat.
        self._upsert_lan_thi(ts, self._snapshot_lan_thi(ts))

        await self.db.commit()
        await self.db.refresh(ts)

        return await self._build_ket_qua(ts, kt)

    # ================================================================
    # LUU NHAP — AUTO-SAVE 30s/lan
    # ================================================================

    async def luu_nhap(
        self,
        ky_thi_id: uuid.UUID,
        cau_tra_loi: list,
        so_lan_vi_pham: int,
        user: TokenPayload,
    ) -> dict:
        """Luu bai lam nhap (auto-save moi 30s).

        Khac nop_bai: KHONG cham diem, KHONG doi trang_thai. Chi luu chi_tiet_nhap
        + so_lan_vi_pham de FE restore khi mat ket noi / dong tab / treo may.
        """
        cc_id = uuid.UUID(user.sub)
        stmt = select(ThiSinh).where(
            ThiSinh.ky_thi_id == ky_thi_id,
            ThiSinh.cong_chuc_id == cc_id,
        )
        result = await self.db.execute(stmt)
        ts = result.scalar_one_or_none()

        if not ts:
            raise HTTPException(
                status_code=404,
                detail={"success": False, "error": {"code": "DGNL_028", "message": "Bạn không có trong kỳ thi này"}},
            )
        if ts.trang_thai != "DANG_THI":
            # Da nop hoac chua bat dau -> bo qua autosave (idempotent, khong raise
            # de FE khong spam loi voi user).
            return {"saved": False, "trang_thai": ts.trang_thai}

        # Chuan hoa payload
        nhap_data = [
            {"cau_hoi_id": str(tl.cau_hoi_id), "tra_loi": tl.tra_loi}
            for tl in cau_tra_loi
        ]
        ts.chi_tiet_nhap = nhap_data
        ts.so_lan_vi_pham = so_lan_vi_pham
        ts.updated_at = datetime.utcnow()
        await self.db.commit()
        return {"saved": True, "so_cau_da_luu": len(nhap_data)}

    @staticmethod
    def _project_lich_su_summary(lich_su: Optional[list]) -> Optional[list[dict]]:
        """Project raw lich_su_thi (co chi_tiet_tra_loi) -> summary array.

        Dung cho ket_qua endpoints + danh_sach_thi_sinh — han che payload va
        an chi tiet cau tra loi (FE lay rieng qua /ket-qua/{lan}).
        """
        if not lich_su:
            return None
        return [
            {
                "lan": e.get("lan", 0),
                "diem": e.get("diem", 0) or 0,
                "xep_loai": e.get("xep_loai"),
                "so_cau_dung": e.get("so_cau_dung"),
                "so_cau_sai": e.get("so_cau_sai"),
                "tong_so_cau": e.get("tong_so_cau"),
                "thoi_gian_bat_dau": e.get("thoi_gian_bat_dau"),
                "thoi_gian_nop": e.get("thoi_gian_nop"),
                "thoi_gian_lam_giay": e.get("thoi_gian_lam_giay"),
                "has_chi_tiet": bool(e.get("chi_tiet_tra_loi")),
            }
            for e in lich_su if e
        ]

    @staticmethod
    def _snapshot_lan_thi(ts: ThiSinh) -> dict:
        """Build snapshot 1 entry lich_su_thi tu state hien tai cua thi sinh.

        Luu day du chi_tiet_tra_loi + de_thi_ids + diem_theo_linh_vuc de
        QT_DAO_TAO co the drill-down lai bai lam cua lan thi cu.
        """
        return {
            "lan": ts.lan_thi_hien_tai or 0,
            "diem": float(ts.diem_tong) if ts.diem_tong is not None else 0,
            "xep_loai": ts.xep_loai,
            "so_cau_dung": ts.so_cau_dung,
            "so_cau_sai": ts.so_cau_sai,
            "tong_so_cau": ts.tong_so_cau,
            "thoi_gian_bat_dau": ts.thoi_gian_bat_dau.isoformat() if ts.thoi_gian_bat_dau else None,
            "thoi_gian_nop": ts.thoi_gian_nop.isoformat() if ts.thoi_gian_nop else None,
            "thoi_gian_lam_giay": ts.thoi_gian_lam_giay,
            "diem_theo_linh_vuc": dict(ts.diem_theo_linh_vuc) if ts.diem_theo_linh_vuc else {},
            "de_thi_ids": list(ts.de_thi_ids or []),
            "chi_tiet_tra_loi": list(ts.chi_tiet_tra_loi or []),
        }

    @staticmethod
    def _upsert_lan_thi(ts: ThiSinh, snapshot: dict) -> None:
        """Upsert snapshot vao ts.lich_su_thi (theo lan). Idempotent.

        - Neu da co entry voi cung `lan` -> replace.
        - Neu chua co -> append.
        Reassign list moi de SQLAlchemy detect change tren JSONB.
        """
        lich_su = list(ts.lich_su_thi or [])
        lan = snapshot.get("lan")
        idx = next((i for i, e in enumerate(lich_su) if (e or {}).get("lan") == lan), None)
        if idx is not None:
            lich_su[idx] = snapshot
        else:
            lich_su.append(snapshot)
        ts.lich_su_thi = lich_su

    @staticmethod
    def _normalize_dap_an_dung(da):
        """Chuan hoa dap_an_dung: tu full dict ch.dap_an → scalar/list/None.

        Backend lich su luu nguyen ch.dap_an ({lua_chon, dap_an_dung, ...} hoac {goi_y})
        vao chi_tiet_tra_loi. Frontend khi do gap dict se hien '[object Object]'.
        Helper nay extract gia tri thuc su can hien thi.
        """
        if isinstance(da, dict):
            if "dap_an_dung" in da:
                return da["dap_an_dung"]
            if "goi_y" in da:
                return da["goi_y"]
            return None
        return da

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

    async def ket_qua_lan_thi(
        self,
        ky_thi_id: uuid.UUID,
        cong_chuc_id: uuid.UUID,
        lan: int,
        user: TokenPayload,
    ) -> KetQuaResponse:
        """Xem ket qua 1 lan thi cu the (QT/LD).

        - lan == lan_thi_hien_tai -> tra ve state hien tai (giong ket_qua_cbcc).
        - lan < lan_thi_hien_tai -> tim entry trong lich_su_thi.
        - Entry cu khong co chi_tiet_tra_loi (data truoc 30/05/2026) -> tra ve
          response nhung chi_tiet=None, FE hien "Chi tiet khong kha dung".
        """
        kt = await self._get_ky_thi(ky_thi_id)

        stmt = select(ThiSinh).where(ThiSinh.ky_thi_id == ky_thi_id, ThiSinh.cong_chuc_id == cong_chuc_id)
        result = await self.db.execute(stmt)
        ts = result.scalar_one_or_none()
        if not ts:
            raise HTTPException(status_code=404, detail={"success": False, "error": {"code": "DGNL_023", "message": "Thí sinh không tồn tại trong kỳ thi này"}})

        # Lan hien tai -> dung _build_ket_qua nhu cu
        if lan == (ts.lan_thi_hien_tai or 0):
            return await self._build_ket_qua(ts, kt)

        # Tim trong lich su
        entry = next(
            (e for e in (ts.lich_su_thi or []) if (e or {}).get("lan") == lan),
            None,
        )
        if not entry:
            raise HTTPException(
                status_code=404,
                detail={"success": False, "error": {"code": "DGNL_035", "message": f"Không tìm thấy lần thi {lan}"}},
            )

        return await self._build_ket_qua_lan(ts, kt, entry)

    async def _build_ket_qua(self, ts: ThiSinh, kt: KyThi) -> KetQuaResponse:
        """Build response ket qua tu state hien tai cua thi sinh (lan moi nhat)."""
        cc_info = await self._lay_thi_sinh_info(ts)
        diem_lv_list = await self._build_diem_lv_list(ts.diem_theo_linh_vuc)
        chi_tiet = await self._enrich_chi_tiet(ts.chi_tiet_tra_loi) if kt.hien_dap_an else None

        return KetQuaResponse(
            ky_thi={"id": str(kt.id), "ten_ky_thi": kt.ten_ky_thi, "diem_dat": float(kt.diem_dat) if kt.diem_dat else 50},
            thi_sinh=cc_info,
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
            lich_su_thi=self._project_lich_su_summary(ts.lich_su_thi),
        )

    async def _build_ket_qua_lan(
        self, ts: ThiSinh, kt: KyThi, entry: dict
    ) -> KetQuaResponse:
        """Build response ket qua tu 1 entry lich_su_thi (lan cu)."""
        cc_info = await self._lay_thi_sinh_info(ts)
        diem_lv_list = await self._build_diem_lv_list(entry.get("diem_theo_linh_vuc"))
        chi_tiet = None
        if kt.hien_dap_an and entry.get("chi_tiet_tra_loi"):
            chi_tiet = await self._enrich_chi_tiet(entry.get("chi_tiet_tra_loi"))

        return KetQuaResponse(
            ky_thi={"id": str(kt.id), "ten_ky_thi": kt.ten_ky_thi, "diem_dat": float(kt.diem_dat) if kt.diem_dat else 50},
            thi_sinh=cc_info,
            ket_qua={
                "diem_tong": float(entry.get("diem") or 0),
                "xep_loai": entry.get("xep_loai"),
                "so_cau_dung": entry.get("so_cau_dung") or 0,
                "so_cau_sai": entry.get("so_cau_sai") or 0,
                "tong_so_cau": entry.get("tong_so_cau") or 0,
                "thoi_gian_lam_giay": entry.get("thoi_gian_lam_giay") or 0,
                "lan_thi": entry.get("lan") or 0,
            },
            diem_theo_linh_vuc=diem_lv_list,
            chi_tiet=chi_tiet,
            lich_su_thi=self._project_lich_su_summary(ts.lich_su_thi),
        )

    async def _lay_thi_sinh_info(self, ts: ThiSinh) -> dict:
        """Lay ho_ten/ma_cc/don_vi/vi_tri cua thi sinh."""
        cc = CongChucRef.__table__
        dv = DonViRef.__table__
        stmt = (
            select(cc.c.ho_ten, cc.c.ma_cc, dv.c.ten_don_vi)
            .outerjoin(dv, cc.c.don_vi_id == dv.c.id)
            .where(cc.c.id == ts.cong_chuc_id)
        )
        r = await self.db.execute(stmt)
        cc_row = r.first()

        vt_r = await self.db.execute(
            select(ViTriViecLam.ten_vi_tri).where(ViTriViecLam.id == ts.vi_tri_id)
        )
        vt_ten = vt_r.scalar() or ""

        return {
            "ho_ten": cc_row.ho_ten if cc_row else None,
            "ma_cc": cc_row.ma_cc if cc_row else None,
            "don_vi": cc_row.ten_don_vi if cc_row else None,
            "vi_tri_thi": vt_ten,
        }

    async def _build_diem_lv_list(self, diem_theo_lv: Optional[dict]) -> list[DiemLinhVuc]:
        """Build list DiemLinhVuc tu dict {ma_lv: {dung, tong, phan_tram}}."""
        out: list[DiemLinhVuc] = []
        if not diem_theo_lv:
            return out
        for ma, stats in diem_theo_lv.items():
            lv_r = await self.db.execute(
                select(LinhVuc.ten_linh_vuc).where(LinhVuc.ma_linh_vuc == ma)
            )
            lv_ten = lv_r.scalar() or ma
            out.append(DiemLinhVuc(
                linh_vuc=lv_ten,
                so_cau_dung=(stats or {}).get("dung", 0),
                tong_cau=(stats or {}).get("tong", 0),
                phan_tram=(stats or {}).get("phan_tram", 0),
            ))
        return out

    async def _enrich_chi_tiet(self, chi_tiet_raw: Optional[list]) -> Optional[list]:
        """Enrich chi_tiet_tra_loi them noi_dung/loai/giai_thich tu CauHoiDgnl.

        Dung cho ca lan hien tai (ts.chi_tiet_tra_loi) va lan cu (entry["chi_tiet_tra_loi"]).
        """
        if not chi_tiet_raw:
            return None
        try:
            ch_ids = [uuid.UUID(item["cau_hoi_id"]) for item in chi_tiet_raw if item.get("cau_hoi_id")]
        except (ValueError, TypeError):
            ch_ids = []
        ch_map: dict[uuid.UUID, CauHoiDgnl] = {}
        if ch_ids:
            ch_r = await self.db.execute(select(CauHoiDgnl).where(CauHoiDgnl.id.in_(ch_ids)))
            ch_map = {ch.id: ch for ch in ch_r.scalars().all()}

        out: list = []
        for item in chi_tiet_raw:
            enriched = dict(item)
            try:
                cid = uuid.UUID(item["cau_hoi_id"]) if item.get("cau_hoi_id") else None
            except (ValueError, TypeError):
                cid = None
            ch = ch_map.get(cid) if cid else None
            if ch:
                enriched["noi_dung"] = ch.noi_dung
                enriched["loai"] = ch.loai
                enriched["giai_thich"] = ch.giai_thich
                enriched["diem_toi_da"] = float(ch.diem) if ch.diem else 1.0
                enriched["diem_dat"] = enriched["diem_toi_da"] if item.get("dung") else 0.0
            # Chuan hoa data cu — unwrap dict ch.dap_an de FE khong hien "[object Object]"
            enriched["dap_an_dung"] = self._normalize_dap_an_dung(enriched.get("dap_an_dung"))
            out.append(enriched)
        return out

    # ================================================================
    # EXPORT EXCEL
    # ================================================================

    async def export_excel(self, ky_thi_id: uuid.UUID, user: TokenPayload) -> bytes:
        """Export ket qua ky thi ra Excel: sheet Tong quan (thong ke) + sheet Danh sach thi sinh.

        Lay TAT CA thi sinh (khong gioi han so luong). Lanh dao chi export don vi minh.
        """
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter
        import io

        kt = await self._get_ky_thi(ky_thi_id)

        # Lay danh sach thi sinh (toan bo). Lanh dao chi xem don vi minh.
        cc = CongChucRef.__table__.alias("cc")
        dv = DonViRef.__table__.alias("dv")

        base_where = [ThiSinh.ky_thi_id == ky_thi_id]
        if self._is_lanh_dao(user) and not self._is_manager(user):
            don_vi_id = getattr(user, "don_vi_id", None)
            if don_vi_id:
                base_where.append(
                    ThiSinh.cong_chuc_id.in_(
                        select(cc.c.id).where(cc.c.don_vi_id == uuid.UUID(don_vi_id))
                    )
                )

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
            .where(*base_where)
            .order_by(cc.c.ho_ten.asc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        # Lay danh sach linh vuc de lam header
        lv_stmt = select(LinhVuc).where(LinhVuc.is_active == True).order_by(LinhVuc.thu_tu)
        lv_result = await self.db.execute(lv_stmt)
        all_lv = lv_result.scalars().all()
        lv_ma_to_ten = {lv.ma_linh_vuc: lv.ten_linh_vuc for lv in all_lv}

        # Styles dung chung
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font_white = Font(bold=True, size=11, color="FFFFFF")
        center = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style="thin"), right=Side(style="thin"),
            top=Side(style="thin"), bottom=Side(style="thin"),
        )
        dat_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        kdat_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

        def auto_width(ws, n_cols: int, from_row: int = 1) -> None:
            """Tinh do rong cot — duyet theo index, bo qua merged cell de tranh
            AttributeError tren MergedCell.column_letter."""
            for col_idx in range(1, n_cols + 1):
                col_letter = get_column_letter(col_idx)
                max_length = 0
                for row_idx in range(from_row, ws.max_row + 1):
                    val = ws.cell(row=row_idx, column=col_idx).value
                    if val is not None:
                        max_length = max(max_length, len(str(val)))
                ws.column_dimensions[col_letter].width = min(max_length + 3, 30)

        wb = Workbook()

        # ============================================================
        # SHEET 1: TONG QUAN (thong ke)
        # ============================================================
        ws_tq = wb.active
        ws_tq.title = "Tổng quan"

        all_ts = [r[0] for r in rows]
        tong = len(all_ts)
        da_thi = sum(1 for t in all_ts if t.trang_thai == "DA_NOP")
        chua_thi = sum(1 for t in all_ts if t.trang_thai == "CHUA_THI")
        dang_thi = sum(1 for t in all_ts if t.trang_thai == "DANG_THI")
        vang = sum(1 for t in all_ts if t.trang_thai == "VANG")
        dat = sum(1 for t in all_ts if t.xep_loai == "DAT")
        khong_dat = sum(1 for t in all_ts if t.xep_loai == "KHONG_DAT")
        diem_list = [float(t.diem_tong) for t in all_ts if t.diem_tong is not None]
        diem_tb = round(sum(diem_list) / len(diem_list), 1) if diem_list else 0
        diem_cao = round(max(diem_list), 1) if diem_list else 0
        diem_thap = round(min(diem_list), 1) if diem_list else 0
        ti_le_dat = round(dat / da_thi * 100, 1) if da_thi > 0 else 0

        ws_tq.merge_cells("A1:C1")
        ws_tq["A1"] = f"THỐNG KÊ KỲ THI: {kt.ten_ky_thi}"
        ws_tq["A1"].font = Font(bold=True, size=14)
        ws_tq["A1"].alignment = center
        ws_tq.merge_cells("A2:C2")
        ws_tq["A2"] = f"Mã kỳ thi: {kt.ma_ky_thi} | Điểm đạt: {kt.diem_dat}%"
        ws_tq["A2"].font = Font(size=11)

        tq_rows = [
            ("Tổng thí sinh", tong),
            ("Đã thi", da_thi),
            ("Chưa thi", chua_thi),
            ("Đang thi", dang_thi),
            ("Vắng", vang),
            ("Đạt", dat),
            ("Không đạt", khong_dat),
            ("Tỷ lệ đạt (%)", ti_le_dat),
            ("Điểm trung bình", diem_tb),
            ("Điểm cao nhất", diem_cao),
            ("Điểm thấp nhất", diem_thap),
        ]
        r = 4
        for label, val in tq_rows:
            ws_tq.cell(row=r, column=1, value=label).font = Font(bold=True)
            c = ws_tq.cell(row=r, column=2, value=val)
            c.alignment = center
            ws_tq.cell(row=r, column=1).border = thin_border
            c.border = thin_border
            r += 1

        # Theo vi tri
        vt_groups: dict[str, list] = {}
        for ts, _ho, _ma, _dv, vt_ten in rows:
            vt_groups.setdefault(vt_ten or "Không xác định", []).append(ts)
        if vt_groups:
            r += 1
            ws_tq.cell(row=r, column=1, value="THEO VỊ TRÍ").font = Font(bold=True, size=12)
            r += 1
            for col_idx, h in enumerate(["Vị trí", "Tổng", "Đạt", "Không đạt", "Điểm TB"], 1):
                cell = ws_tq.cell(row=r, column=col_idx, value=h)
                cell.font = header_font_white
                cell.fill = header_fill
                cell.alignment = center
                cell.border = thin_border
            r += 1
            for vt_ten, vt_ts in vt_groups.items():
                vt_dat = sum(1 for t in vt_ts if t.xep_loai == "DAT")
                vt_kdat = sum(1 for t in vt_ts if t.xep_loai == "KHONG_DAT")
                vt_diem = [float(t.diem_tong) for t in vt_ts if t.diem_tong is not None]
                vals = [
                    vt_ten, len(vt_ts), vt_dat, vt_kdat,
                    round(sum(vt_diem) / len(vt_diem), 1) if vt_diem else 0,
                ]
                for col_idx, v in enumerate(vals, 1):
                    cell = ws_tq.cell(row=r, column=col_idx, value=v)
                    cell.border = thin_border
                    if col_idx > 1:
                        cell.alignment = center
                r += 1

        # Theo don vi
        dv_groups: dict[str, list] = {}
        for ts, _ho, _ma, dv_ten, _vt in rows:
            dv_groups.setdefault(dv_ten or "Không xác định", []).append(ts)
        if dv_groups:
            r += 1
            ws_tq.cell(row=r, column=1, value="THEO ĐƠN VỊ").font = Font(bold=True, size=12)
            r += 1
            for col_idx, h in enumerate(["Đơn vị", "Tổng", "Đạt", "Tỷ lệ đạt (%)", "Điểm TB"], 1):
                cell = ws_tq.cell(row=r, column=col_idx, value=h)
                cell.font = header_font_white
                cell.fill = header_fill
                cell.alignment = center
                cell.border = thin_border
            r += 1
            for dv_ten, dv_ts in dv_groups.items():
                dv_dat = sum(1 for t in dv_ts if t.xep_loai == "DAT")
                dv_diem = [float(t.diem_tong) for t in dv_ts if t.diem_tong is not None]
                vals = [
                    dv_ten, len(dv_ts), dv_dat,
                    round(dv_dat / len(dv_ts) * 100, 1) if dv_ts else 0,
                    round(sum(dv_diem) / len(dv_diem), 1) if dv_diem else 0,
                ]
                for col_idx, v in enumerate(vals, 1):
                    cell = ws_tq.cell(row=r, column=col_idx, value=v)
                    cell.border = thin_border
                    if col_idx > 1:
                        cell.alignment = center
                r += 1

        auto_width(ws_tq, 5, from_row=4)

        # ============================================================
        # SHEET 2: DANH SACH THI SINH
        # ============================================================
        ws = wb.create_sheet("Danh sách thí sinh")

        base_headers = ["STT", "Mã CC", "Họ tên", "Đơn vị", "Vị trí thi",
                        "Trạng thái", "Điểm (%)", "Xếp loại", "Số câu đúng",
                        "Tổng câu", "Thời gian (phút)", "Lần thi"]
        lv_headers = [lv_ma_to_ten.get(ma, ma) for ma in lv_ma_to_ten.keys()]
        headers = base_headers + lv_headers
        n_cols = len(headers)

        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_cols)
        ws.cell(row=1, column=1, value=f"KẾT QUẢ KỲ THI: {kt.ten_ky_thi}")
        ws.cell(row=1, column=1).font = Font(bold=True, size=14)
        ws.cell(row=1, column=1).alignment = center

        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=n_cols)
        ws.cell(row=2, column=1, value=f"Mã kỳ thi: {kt.ma_ky_thi} | Điểm đạt: {kt.diem_dat}%")
        ws.cell(row=2, column=1).font = Font(size=11)

        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_idx, value=h)
            cell.font = header_font_white
            cell.fill = header_fill
            cell.alignment = center
            cell.border = thin_border

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

            xep_loai_cell = ws.cell(row=row_idx, column=8)
            if ts.xep_loai == "DAT":
                xep_loai_cell.fill = dat_fill
            elif ts.xep_loai == "KHONG_DAT":
                xep_loai_cell.fill = kdat_fill

        auto_width(ws, n_cols, from_row=4)

        # ============================================================
        # SHEET 3: LICH SU LUOT THI — 1 row / (thi sinh × lan thi)
        # Bat AutoFilter de QT_DAO_TAO/LD filter theo cot "Lan" hoac "Xep loai"
        # ============================================================
        ws_ls = wb.create_sheet("Lịch sử lượt thi")

        ls_headers = [
            "STT", "Mã CC", "Họ tên", "Đơn vị", "Vị trí thi",
            "Lần", "Điểm (%)", "Xếp loại", "Số câu đúng", "Tổng câu",
            "Thời gian (phút)", "Thời gian nộp",
        ]
        ls_n_cols = len(ls_headers)

        ws_ls.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ls_n_cols)
        ws_ls.cell(row=1, column=1, value=f"LỊCH SỬ LƯỢT THI: {kt.ten_ky_thi}")
        ws_ls.cell(row=1, column=1).font = Font(bold=True, size=14)
        ws_ls.cell(row=1, column=1).alignment = center

        ws_ls.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ls_n_cols)
        ws_ls.cell(
            row=2, column=1,
            value=f"Mã kỳ thi: {kt.ma_ky_thi} | Điểm đạt: {kt.diem_dat}% | "
                  f"Số lần tối đa: {kt.so_lan_thi_toi_da or 1} | "
                  f"Mẹo: Dùng AutoFilter ▼ trên cột \"Lần\" để xem 1 lượt cụ thể"
        )
        ws_ls.cell(row=2, column=1).font = Font(size=10, italic=True, color="666666")

        for col_idx, h in enumerate(ls_headers, 1):
            cell = ws_ls.cell(row=4, column=col_idx, value=h)
            cell.font = header_font_white
            cell.fill = header_fill
            cell.alignment = center
            cell.border = thin_border

        # Build rows: 1 row / (thi_sinh × lan)
        ls_row_idx = 5
        stt = 0
        for ts, ho_ten, ma_cc, dv_ten, vt_ten in rows:
            lich_su = ts.lich_su_thi or []
            lan_hien_tai = ts.lan_thi_hien_tai or 0
            cu_co_lan_ht = any((e or {}).get("lan") == lan_hien_tai for e in lich_su)

            # Cac lan tu lich_su_thi (sap xep theo lan tang dan)
            entries = sorted(
                [e for e in lich_su if e and e.get("lan") is not None],
                key=lambda e: e.get("lan", 0),
            )

            # Backward-compat: data cu chua snapshot lan hien tai vao lich_su_thi.
            # Bo sung tu ts.* truc tiep.
            if ts.trang_thai == "DA_NOP" and lan_hien_tai > 0 and not cu_co_lan_ht:
                entries.append({
                    "lan": lan_hien_tai,
                    "diem": float(ts.diem_tong) if ts.diem_tong is not None else 0,
                    "xep_loai": ts.xep_loai,
                    "so_cau_dung": ts.so_cau_dung,
                    "tong_so_cau": ts.tong_so_cau,
                    "thoi_gian_lam_giay": ts.thoi_gian_lam_giay,
                    "thoi_gian_nop": ts.thoi_gian_nop.isoformat() if ts.thoi_gian_nop else None,
                })

            for e in entries:
                stt += 1
                tg_phut = round(e["thoi_gian_lam_giay"] / 60, 1) if e.get("thoi_gian_lam_giay") else ""
                tg_nop_str = ""
                if e.get("thoi_gian_nop"):
                    try:
                        tg_nop_str = datetime.fromisoformat(
                            str(e["thoi_gian_nop"]).replace("Z", "")
                        ).strftime("%d/%m/%Y %H:%M")
                    except (ValueError, TypeError):
                        tg_nop_str = str(e["thoi_gian_nop"])

                row_data = [
                    stt, ma_cc, ho_ten, dv_ten, vt_ten,
                    e.get("lan"),
                    float(e["diem"]) if e.get("diem") is not None else "",
                    e.get("xep_loai") or "",
                    e.get("so_cau_dung") or "",
                    e.get("tong_so_cau") or "",
                    tg_phut,
                    tg_nop_str,
                ]
                for col_idx, val in enumerate(row_data, 1):
                    cell = ws_ls.cell(row=ls_row_idx, column=col_idx, value=val)
                    cell.border = thin_border
                    cell.alignment = center

                xl_cell = ws_ls.cell(row=ls_row_idx, column=8)
                if e.get("xep_loai") == "DAT":
                    xl_cell.fill = dat_fill
                elif e.get("xep_loai") == "KHONG_DAT":
                    xl_cell.fill = kdat_fill

                ls_row_idx += 1

        # Khong co data -> hien thong bao
        if stt == 0:
            ws_ls.merge_cells(start_row=5, start_column=1, end_row=5, end_column=ls_n_cols)
            ws_ls.cell(row=5, column=1, value="Chưa có lượt thi nào được nộp.").alignment = center
            ws_ls.cell(row=5, column=1).font = Font(italic=True, color="888888")
        else:
            # AutoFilter tu row header (4) den row cuoi cung
            ws_ls.auto_filter.ref = f"A4:{get_column_letter(ls_n_cols)}{ls_row_idx - 1}"
            # Freeze header de scroll giu tieu de
            ws_ls.freeze_panes = "A5"

        auto_width(ws_ls, ls_n_cols, from_row=4)

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()
