"""
lich_cong_tac_service.py
=========================
Nghiệp vụ Lịch công tác — di trú từ lichkv8.

Đọc trên CÙNG bảng `meeting.cuoc_hop` với Họp Không Giấy, không tách bảng.
Nhờ vậy tiêu chí 8.3 ("cuộc họp phải tự hiện trên lịch, đổi giờ hoặc huỷ thì
lịch cập nhật theo") đạt được mà không cần một dòng mã đồng bộ nào.

Lịch xếp theo `ngay_hien_thi` chứ không phải `ngay_hop`: lichkv8 cho phép ngày
hiển thị khác ngày bắt đầu thật. Với dòng HKG, trigger
`fn_dong_bo_ngay_hien_thi` giữ hai cột luôn bằng nhau.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models.base import CongChucRef as CongChuc
from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.models.lich_cong_tac import LanhDaoLienQuan, TrucBan, TruSo
from meeting_service.models.tai_lieu import TaiLieu
from meeting_service.schemas.lich_cong_tac import NHAN_LOAI_LICH
from shared.auth import TokenPayload

THU_VN = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu",
          "Thứ Bảy", "Chủ Nhật"]


class LichCongTacService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── truy vấn nền ──────────────────────────────────────────────────
    def _cau_truy_van(
        self,
        tu_ngay: Optional[date] = None,
        den_ngay: Optional[date] = None,
        loai_lich: Optional[str] = None,
        trang_thai: Optional[str] = None,
        lanh_dao_id: Optional[UUID] = None,
        tim_kiem: Optional[str] = None,
        nguon: Optional[str] = None,
    ) -> Select:
        dk = [CuocHop.is_deleted.is_(False)]

        # Sự kiện nhiều ngày phải hiện ở mọi ngày trong khoảng, nên so sánh
        # theo cả ngay_ket_thuc chứ không chỉ ngay_hien_thi.
        if tu_ngay:
            dk.append(
                func.coalesce(CuocHop.ngay_ket_thuc, CuocHop.ngay_hien_thi)
                >= tu_ngay)
        if den_ngay:
            dk.append(CuocHop.ngay_hien_thi <= den_ngay)
        if loai_lich:
            dk.append(CuocHop.loai_lich == loai_lich)
        if trang_thai:
            dk.append(CuocHop.trang_thai == trang_thai)
        if nguon:
            dk.append(CuocHop.nguon == nguon)

        if lanh_dao_id:
            # Lãnh đạo liên quan HOẶC là chủ toạ — lichkv8 dùng cả hai cách.
            dk.append(or_(
                CuocHop.chu_toa_id == lanh_dao_id,
                CuocHop.id.in_(
                    select(LanhDaoLienQuan.cuoc_hop_id)
                    .where(LanhDaoLienQuan.cong_chuc_id == lanh_dao_id)),
            ))

        if tim_kiem:
            tu = f"%{tim_kiem.strip()}%"
            # Đúng 6 trường mà lichkv8 tìm: nội dung, ghi chú, địa điểm,
            # chủ trì, thành phần, lãnh đạo liên quan.
            dk.append(or_(
                CuocHop.tieu_de.ilike(tu),
                CuocHop.mo_ta.ilike(tu),
                CuocHop.dia_diem.ilike(tu),
                CuocHop.chu_tri_text.ilike(tu),
                CuocHop.thanh_phan_text.ilike(tu),
                CuocHop.ma_lich.ilike(tu),
                CuocHop.so_van_ban.ilike(tu),
            ))

        return select(CuocHop).where(and_(*dk))

    # ── danh sách có phân trang ───────────────────────────────────────
    async def danh_sach(self, *, trang: int = 1, so_dong: int = 50,
                        **loc: Any) -> tuple[list[dict], int]:
        cau = self._cau_truy_van(**loc)

        tong = await self.db.scalar(
            select(func.count()).select_from(cau.subquery()))

        cau = (cau.order_by(CuocHop.ngay_hien_thi.asc(),
                            CuocHop.gio_bat_dau.asc())
               .offset((trang - 1) * so_dong).limit(so_dong))
        rows = (await self.db.execute(cau)).scalars().all()
        return await self._lam_giau(rows), int(tong or 0)

    async def _lam_giau(self, rows: list[CuocHop]) -> list[dict]:
        """Bổ sung chủ toạ, lãnh đạo liên quan và số tài liệu.

        Nạp theo lô thay vì lazy-load từng dòng — màn hình lịch tháng có thể
        hiển thị vài trăm sự kiện, để lazy-load là N+1 truy vấn.
        """
        if not rows:
            return []
        ids = [r.id for r in rows]

        ld_theo_hop: dict[UUID, list[dict]] = {}
        q = (select(LanhDaoLienQuan.cuoc_hop_id, CongChuc.id,
                    CongChuc.ho_ten, CongChuc.chuc_vu)
             .join(CongChuc, CongChuc.id == LanhDaoLienQuan.cong_chuc_id)
             .where(LanhDaoLienQuan.cuoc_hop_id.in_(ids))
             .order_by(LanhDaoLienQuan.thu_tu))
        for ch_id, cc_id, ho_ten, chuc_vu in (await self.db.execute(q)).all():
            ld_theo_hop.setdefault(ch_id, []).append(
                {"id": cc_id, "ho_ten": ho_ten, "chuc_vu": chuc_vu})

        chu_toa_ids = {r.chu_toa_id for r in rows if r.chu_toa_id}
        chu_toa: dict[UUID, dict] = {}
        if chu_toa_ids:
            q = select(CongChuc.id, CongChuc.ho_ten, CongChuc.chuc_vu).where(
                CongChuc.id.in_(chu_toa_ids))
            for cc_id, ho_ten, chuc_vu in (await self.db.execute(q)).all():
                chu_toa[cc_id] = {"id": cc_id, "ho_ten": ho_ten,
                                  "chuc_vu": chuc_vu}

        q = (select(TaiLieu.cuoc_hop_id, func.count())
             .where(TaiLieu.cuoc_hop_id.in_(ids),
                    TaiLieu.is_deleted.is_(False))
             .group_by(TaiLieu.cuoc_hop_id))
        so_tl = {k: v for k, v in (await self.db.execute(q)).all()}

        return [{
            "id": r.id,
            "nguon": r.nguon,
            "ma_lich": r.ma_lich,
            "tieu_de": r.tieu_de,
            "loai_lich": r.loai_lich,
            "loai_lich_nhan": NHAN_LOAI_LICH.get(r.loai_lich or ""),
            "ngay_hien_thi": r.ngay_hien_thi,
            "ngay_hop": r.ngay_hop,
            "ngay_ket_thuc": r.ngay_ket_thuc,
            "gio_bat_dau": r.gio_bat_dau,
            "gio_ket_thuc": r.gio_ket_thuc,
            "dia_diem": r.dia_diem,
            "trang_thai": r.trang_thai,
            "chu_toa": chu_toa.get(r.chu_toa_id) if r.chu_toa_id else None,
            "chu_tri_text": r.chu_tri_text,
            "don_vi_chuan_bi": r.don_vi_chuan_bi,
            "so_van_ban": r.so_van_ban,
            "lanh_dao_lien_quan": ld_theo_hop.get(r.id, []),
            "so_tai_lieu": so_tl.get(r.id, 0),
            "co_the_mo_hkg": r.nguon == "HKG",
        } for r in rows]

    # ── chi tiết ──────────────────────────────────────────────────────
    async def chi_tiet(self, cuoc_hop_id: UUID) -> Optional[dict]:
        r = await self.db.get(CuocHop, cuoc_hop_id)
        if not r or r.is_deleted:
            return None
        (item,) = await self._lam_giau([r])
        item.update({
            "mo_ta": r.mo_ta,
            "thanh_phan_text": r.thanh_phan_text,
            "ly_do_huy": r.ly_do_huy,
        })
        return item

    # ── lịch theo lãnh đạo ────────────────────────────────────────────
    async def lich_lanh_dao(self, lanh_dao_id: UUID, tu_ngay: date,
                            den_ngay: date) -> dict:
        cau = (self._cau_truy_van(tu_ngay=tu_ngay, den_ngay=den_ngay,
                                  lanh_dao_id=lanh_dao_id)
               .order_by(CuocHop.ngay_hien_thi, CuocHop.gio_bat_dau))
        rows = (await self.db.execute(cau)).scalars().all()
        items = await self._lam_giau(rows)

        theo_ngay: dict[date, list] = {}
        for it in items:
            theo_ngay.setdefault(it["ngay_hien_thi"], []).append(it)

        cc = await self.db.get(CongChuc, lanh_dao_id)
        return {
            "lanh_dao": {"id": lanh_dao_id,
                         "ho_ten": cc.ho_ten if cc else "",
                         "chuc_vu": cc.chuc_vu if cc else None},
            "tong_su_kien": len(items),
            "theo_ngay": [{"ngay": k, "su_kien": v}
                          for k, v in sorted(theo_ngay.items())],
        }

    # ── tóm tắt lịch ──────────────────────────────────────────────────
    async def tom_tat(self, tu_ngay: date, den_ngay: date, *,
                      chi_da_dang: bool = True,
                      kem_truc_ban: bool = True) -> dict:
        """Bản tóm tắt để dán sang Zalo hoặc email.

        Sinh trực tiếp từ dữ liệu lịch, không lưu bản riêng — sửa lịch thì tóm
        tắt tự phản ánh, đúng yêu cầu mục VIII của đặc tả.
        """
        cau = self._cau_truy_van(
            tu_ngay=tu_ngay, den_ngay=den_ngay,
            trang_thai="DA_THONG_BAO" if chi_da_dang else None)
        rows = (await self.db.execute(
            cau.order_by(CuocHop.ngay_hien_thi, CuocHop.gio_bat_dau)
        )).scalars().all()
        items = await self._lam_giau(rows)

        truc: dict[date, list[str]] = {}
        if kem_truc_ban:
            q = (select(TrucBan.ngay_truc, TruSo.ten_tru_so, TrucBan.ho_ten,
                        TrucBan.chuc_vu, TrucBan.so_dien_thoai)
                 .join(TruSo, TruSo.id == TrucBan.tru_so_id)
                 .where(TrucBan.ngay_truc.between(tu_ngay, den_ngay),
                        TrucBan.is_deleted.is_(False))
                 .order_by(TruSo.thu_tu))
            for ngay, tru_so, ho_ten, chuc_vu, sdt in (
                    await self.db.execute(q)).all():
                truc.setdefault(ngay, []).append(
                    " · ".join(filter(None, [tru_so, ho_ten, chuc_vu, sdt])))

        theo_ngay: dict[date, list] = {}
        for it in items:
            theo_ngay.setdefault(it["ngay_hien_thi"], []).append(it)

        ngay_list = sorted(set(theo_ngay) | set(truc))
        ket_qua = [{
            "ngay": n,
            "thu": THU_VN[n.weekday()],
            "su_kien": theo_ngay.get(n, []),
            "truc_ban": truc.get(n, []),
        } for n in ngay_list]

        return {
            "tu_ngay": tu_ngay,
            "den_ngay": den_ngay,
            "theo_ngay": ket_qua,
            "van_ban_thuan": self._sinh_van_ban(ket_qua),
        }

    @staticmethod
    def _sinh_van_ban(theo_ngay: list[dict]) -> str:
        dong: list[str] = []
        for ng in theo_ngay:
            dong.append(f"{ng['thu']}, {ng['ngay'].strftime('%d/%m/%Y')}")
            for sk in ng["su_kien"]:
                gio = sk["gio_bat_dau"].strftime("%H:%M")
                phan = [f"  {gio}", sk["tieu_de"]]
                if sk.get("dia_diem"):
                    phan.append(f"({sk['dia_diem']})")
                chu_tri = (sk["chu_toa"]["ho_ten"] if sk.get("chu_toa")
                           else sk.get("chu_tri_text"))
                if chu_tri:
                    phan.append(f"— {chu_tri}")
                dong.append(" ".join(phan))
            for t in ng["truc_ban"]:
                dong.append(f"  Trực ban: {t}")
            dong.append("")
        return "\n".join(dong).strip()

    # ── dashboard ─────────────────────────────────────────────────────
    async def thong_ke(self, hom_nay: Optional[date] = None) -> dict:
        hn = hom_nay or date.today()
        dau_tuan = hn - timedelta(days=hn.weekday())

        async def dem(tu: date, den: date) -> int:
            cau = self._cau_truy_van(tu_ngay=tu, den_ngay=den)
            return int(await self.db.scalar(
                select(func.count()).select_from(cau.subquery())) or 0)

        cau_loai = (select(CuocHop.loai_lich, func.count())
                    .where(CuocHop.is_deleted.is_(False),
                           CuocHop.ngay_hien_thi.between(
                               hn.replace(day=1), hn))
                    .group_by(CuocHop.loai_lich))
        theo_loai = {k or "?": v
                     for k, v in (await self.db.execute(cau_loai)).all()}

        return {
            "hom_nay": await dem(hn, hn),
            "ngay_mai": await dem(hn + timedelta(days=1), hn + timedelta(days=1)),
            "trong_tuan": await dem(dau_tuan, dau_tuan + timedelta(days=6)),
            "trong_thang": await dem(hn.replace(day=1), hn),
            "trong_nam": await dem(hn.replace(month=1, day=1), hn),
            "theo_loai_thang_nay": theo_loai,
        }
