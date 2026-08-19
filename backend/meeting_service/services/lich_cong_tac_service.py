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

from datetime import date, time, timedelta
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import Select, and_, delete, func, or_, select
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models.base import CongChucRef as CongChuc
from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.models.lich_cong_tac import LanhDaoLienQuan, TrucBan, TruSo
from meeting_service.models.tai_lieu import TaiLieu
from meeting_service.schemas.lich_cong_tac import NHAN_LOAI_LICH
from meeting_service.services.audit_log_service import ghi_audit
from shared.auth import TokenPayload

THU_VN = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu",
          "Thứ Bảy", "Chủ Nhật"]

# Nguồn của dòng do module Lịch công tác quản lý. Dòng `HKG` đi qua nghiệp vụ
# Họp Không Giấy nên KHÔNG được sửa bằng các hàm dưới đây.
NGUON_LICH = "LICH_CONG_TAC"

TRANG_THAI_VALUES = ["LEN_KE_HOACH", "DA_THONG_BAO", "HOAN_THANH", "HUY"]

# Các trường được phép sửa qua màn hình lịch, kèm nhãn để ghi nhật ký cho
# người đọc hiểu được (thay bảng MEETING_LOG của lichkv8).
NHAN_TRUONG = {
    "tieu_de": "Nội dung",
    "loai_lich": "Loại lịch",
    "ngay_hop": "Ngày bắt đầu",
    "ngay_ket_thuc": "Ngày kết thúc",
    "ngay_hien_thi": "Ngày hiển thị",
    "gio_bat_dau": "Giờ bắt đầu",
    "gio_ket_thuc": "Giờ kết thúc",
    "dia_diem": "Địa điểm",
    "mo_ta": "Ghi chú",
    "trang_thai": "Trạng thái",
    "chu_toa_id": "Chủ trì (công chức)",
    "chu_tri_text": "Chủ trì (ghi tay)",
    "thanh_phan_text": "Thành phần",
    "don_vi_chuan_bi": "Đơn vị chuẩn bị",
    "so_van_ban": "Số văn bản",
}


# ── quyền sửa lịch ────────────────────────────────────────────────────
# lichkv8 không có phân quyền thật: ai mở được bảng tính là sửa được, và 217
# người đã từng tạo lịch. Ở đây tách làm hai mức thay vì bê nguyên:
#
#   - Người quản trị lịch: sửa được MỌI sự kiện.
#   - Người dùng thường: tạo mới được, và chỉ sửa được sự kiện mình tạo.
#
# Không dò chuỗi trên tên đơn vị hay chức vụ như hàm `isDutyAdmin_()` của hệ
# cũ — ai có đơn vị chứa "Văn phòng" đều thành quản trị toàn Chi cục.
VAI_TRO_QUAN_TRI_LICH = {"ADMIN", "SUPER_ADMIN", "CCT", "CHI_CUC_TRUONG",
                         "PCCT", "PHO_CHI_CUC_TRUONG"}
PLATFORM_QUAN_TRI_LICH = {"CHANH_VP", "QT_NOI_DUNG"}


def la_quan_tri_lich(user: TokenPayload) -> bool:
    return bool(
        user.is_admin
        or user.vai_tro in VAI_TRO_QUAN_TRI_LICH
        or set(user.platform_roles or []) & PLATFORM_QUAN_TRI_LICH
    )


class LoiNghiepVu(Exception):
    """Lỗi nghiệp vụ có mã, để tầng endpoint dịch thẳng sang HTTP."""

    def __init__(self, ma: str, thong_diep: str, http: int = 400):
        super().__init__(thong_diep)
        self.ma = ma
        self.thong_diep = thong_diep
        self.http = http


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
                        moi_truoc: bool = False,
                        **loc: Any) -> tuple[list[dict], int]:
        """`moi_truoc=True` xếp ngày gần nhất lên đầu.

        Xem theo tháng thì phải tăng dần vì đó là thứ tự của tờ lịch. Nhưng ở
        chế độ danh sách, tăng dần nghĩa là mở ra thấy tháng 3 — dữ liệu cũ
        nhất — trong khi việc cần xem là những ngày quanh hôm nay.
        """
        cau = self._cau_truy_van(**loc)

        tong = await self.db.scalar(
            select(func.count()).select_from(cau.subquery()))

        thu_tu = ((CuocHop.ngay_hien_thi.desc(), CuocHop.gio_bat_dau.desc())
                  if moi_truoc
                  else (CuocHop.ngay_hien_thi.asc(), CuocHop.gio_bat_dau.asc()))
        cau = (cau.order_by(*thu_tu)
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
            # Giao diện cần biết ai tạo để quyết định có hiện nút Sửa/Xoá —
            # người thường chỉ sửa được lịch mình tạo.
            "created_by": r.created_by,
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

    # ══ QUẢN LÝ LỊCH (G4.3) ═══════════════════════════════════════════

    async def _sinh_ma_lich(self) -> str:
        """Sinh mã tiếp theo dạng `LH0490`.

        Khoá tư vấn ở mức giao dịch: hai người bấm Lưu cùng lúc mà không khoá
        thì cùng đọc ra một số lớn nhất và sinh ra hai mã trùng nhau. Khoá tự
        nhả khi giao dịch kết thúc, không cần dọn.
        """
        await self.db.execute(
            sa_text("SELECT pg_advisory_xact_lock(hashtext('meeting.ma_lich'))"))

        # Chỉ lấy mã đúng khuôn LH + 4 chữ số; mã lạ do nhập tay không được
        # phép đẩy bộ đếm nhảy vọt.
        lon_nhat = await self.db.scalar(sa_text("""
            SELECT max(substring(ma_lich from 3)::int)
              FROM meeting.cuoc_hop
             WHERE ma_lich ~ '^LH[0-9]{4,}$'
        """))
        return f"LH{int(lon_nhat or 0) + 1:04d}"

    async def _dat_lanh_dao(self, cuoc_hop_id: UUID,
                            ids: list[UUID]) -> None:
        """Ghi đè danh sách lãnh đạo liên quan, giữ thứ tự người dùng chọn."""
        await self.db.execute(
            delete(LanhDaoLienQuan).where(
                LanhDaoLienQuan.cuoc_hop_id == cuoc_hop_id))
        for thu_tu, cc_id in enumerate(ids):
            self.db.add(LanhDaoLienQuan(
                cuoc_hop_id=cuoc_hop_id, cong_chuc_id=cc_id, thu_tu=thu_tu))

    async def _lay_de_sua(self, cuoc_hop_id: UUID) -> CuocHop:
        """Lấy một dòng lịch để sửa, chặn mọi thao tác lên dòng HKG.

        Cuộc họp HKG có quy trình riêng (thành phần, điểm danh, biên bản, thông
        báo Zalo). Sửa nó qua màn hình lịch sẽ bỏ qua toàn bộ những thứ đó, nên
        chặn thẳng thay vì cố xử lý cho khéo.
        """
        r = await self.db.get(CuocHop, cuoc_hop_id)
        if not r or r.is_deleted:
            raise LoiNghiepVu("KHONG_TIM_THAY",
                              "Không tìm thấy sự kiện trên lịch", 404)
        if r.nguon != NGUON_LICH:
            raise LoiNghiepVu(
                "THUOC_HOP_KHONG_GIAY",
                "Đây là cuộc họp của Họp Không Giấy — sửa trong màn hình cuộc "
                "họp, không sửa ở lịch công tác", 409)
        return r

    async def _lay_de_sua_theo_quyen(self, cuoc_hop_id: UUID,
                                     user: TokenPayload) -> CuocHop:
        """Như `_lay_de_sua`, thêm kiểm tra quyền: quản trị lịch hoặc người tạo.

        Toàn bộ 489 sự kiện di trú có `created_by` là người tạo trong hệ cũ,
        nên quy tắc "người tạo sửa được" áp dụng đúng ngay từ dữ liệu cũ.
        """
        r = await self._lay_de_sua(cuoc_hop_id)
        if la_quan_tri_lich(user) or r.created_by == UUID(user.sub):
            return r
        raise LoiNghiepVu(
            "KHONG_DU_QUYEN",
            "Chỉ người tạo lịch hoặc người quản trị lịch mới sửa được", 403)

    async def tao(self, du_lieu: dict, *, nguoi_id: UUID) -> dict:
        """Tạo một sự kiện lịch mới."""
        ids_lanh_dao = du_lieu.pop("lanh_dao_lien_quan_ids", []) or []

        r = CuocHop(
            nguon=NGUON_LICH,
            ma_lich=await self._sinh_ma_lich(),
            created_by=nguoi_id,
            updated_by=nguoi_id,
            trang_thai=du_lieu.pop("trang_thai", None) or "LEN_KE_HOACH",
            **du_lieu,
        )
        # Bỏ trống thì lấy ngày bắt đầu — trigger cũng làm vậy, đặt sẵn ở đây
        # để giá trị trả về ngay sau khi tạo đã đúng.
        if r.ngay_hien_thi is None:
            r.ngay_hien_thi = r.ngay_hop

        self.db.add(r)
        await self.db.flush()

        if ids_lanh_dao:
            await self._dat_lanh_dao(r.id, ids_lanh_dao)

        await ghi_audit(
            self.db, hanh_dong="TAO_LICH", nguoi_thuc_hien_id=nguoi_id,
            doi_tuong_loai="LICH_CONG_TAC", doi_tuong_id=r.id,
            chi_tiet={"ma_lich": r.ma_lich, "tieu_de": r.tieu_de,
                      "ngay": r.ngay_hien_thi.isoformat()})
        await self.db.commit()
        return await self.chi_tiet(r.id)  # type: ignore[return-value]

    async def cap_nhat(self, cuoc_hop_id: UUID, thay_doi: dict, *,
                       user: TokenPayload) -> dict:
        """Sửa sự kiện, ghi nhật ký từng trường đã đổi."""
        nguoi_id = UUID(user.sub)
        r = await self._lay_de_sua_theo_quyen(cuoc_hop_id, user)

        ids_lanh_dao = thay_doi.pop("lanh_dao_lien_quan_ids", None)

        if (tt := thay_doi.get("trang_thai")) and tt not in TRANG_THAI_VALUES:
            raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE",
                              f"trang_thai phải thuộc {TRANG_THAI_VALUES}")

        nhat_ky: list[dict] = []
        for truong, moi in thay_doi.items():
            cu = getattr(r, truong, None)
            if cu == moi:
                continue
            setattr(r, truong, moi)
            nhat_ky.append({
                "truong": truong,
                "nhan": NHAN_TRUONG.get(truong, truong),
                "cu": _doc_duoc(cu),
                "moi": _doc_duoc(moi),
            })

        # Đổi ngày bắt đầu mà không đụng ngày hiển thị thì hai cột lệch nhau,
        # và lịch xếp theo ngày hiển thị nên sự kiện sẽ nằm sai chỗ.
        if "ngay_hop" in thay_doi and "ngay_hien_thi" not in thay_doi:
            if r.ngay_hien_thi != r.ngay_hop:
                nhat_ky.append({
                    "truong": "ngay_hien_thi",
                    "nhan": NHAN_TRUONG["ngay_hien_thi"],
                    "cu": _doc_duoc(r.ngay_hien_thi),
                    "moi": _doc_duoc(r.ngay_hop),
                })
                r.ngay_hien_thi = r.ngay_hop

        if ids_lanh_dao is not None:
            await self._dat_lanh_dao(r.id, ids_lanh_dao)
            nhat_ky.append({"truong": "lanh_dao_lien_quan",
                            "nhan": "Lãnh đạo liên quan",
                            "cu": "", "moi": f"{len(ids_lanh_dao)} người"})

        if not nhat_ky:
            return await self.chi_tiet(r.id)  # type: ignore[return-value]

        r.updated_by = nguoi_id
        await ghi_audit(
            self.db, hanh_dong="SUA_LICH", nguoi_thuc_hien_id=nguoi_id,
            doi_tuong_loai="LICH_CONG_TAC", doi_tuong_id=r.id,
            chi_tiet={"ma_lich": r.ma_lich, "thay_doi": nhat_ky})
        await self.db.commit()
        return await self.chi_tiet(r.id)  # type: ignore[return-value]

    async def huy(self, cuoc_hop_id: UUID, ly_do: str, *,
                  user: TokenPayload) -> dict:
        """Huỷ lịch — đổi trạng thái, KHÔNG xoá.

        Lịch đã huỷ vẫn phải tra được: người ta cần biết cuộc họp từng có và vì
        sao không diễn ra.
        """
        nguoi_id = UUID(user.sub)
        r = await self._lay_de_sua_theo_quyen(cuoc_hop_id, user)
        if r.trang_thai == "HUY":
            raise LoiNghiepVu("DA_HUY", "Lịch này đã ở trạng thái huỷ")

        r.trang_thai = "HUY"
        r.ly_do_huy = ly_do
        r.updated_by = nguoi_id

        await ghi_audit(
            self.db, hanh_dong="HUY_LICH", nguoi_thuc_hien_id=nguoi_id,
            doi_tuong_loai="LICH_CONG_TAC", doi_tuong_id=r.id,
            chi_tiet={"ma_lich": r.ma_lich, "ly_do": ly_do})
        await self.db.commit()
        return await self.chi_tiet(r.id)  # type: ignore[return-value]

    async def xoa(self, cuoc_hop_id: UUID, *, user: TokenPayload) -> None:
        """Xoá mềm. Tài liệu đính kèm giữ nguyên để còn truy vết được."""
        nguoi_id = UUID(user.sub)
        r = await self._lay_de_sua_theo_quyen(cuoc_hop_id, user)
        r.is_deleted = True
        r.updated_by = nguoi_id

        await ghi_audit(
            self.db, hanh_dong="XOA_LICH", nguoi_thuc_hien_id=nguoi_id,
            doi_tuong_loai="LICH_CONG_TAC", doi_tuong_id=r.id,
            chi_tiet={"ma_lich": r.ma_lich, "tieu_de": r.tieu_de})
        await self.db.commit()

    async def nhat_ky(self, cuoc_hop_id: UUID, gioi_han: int = 100) -> list[dict]:
        """Lịch sử thay đổi của một sự kiện, đọc từ `common.audit_log`."""
        rows = (await self.db.execute(sa_text("""
            SELECT a.hanh_dong, a.chi_tiet, a.created_at, cc.ho_ten
              FROM common.audit_log a
              LEFT JOIN public.cong_chuc cc ON cc.id = a.nguoi_thuc_hien_id
             WHERE a.module = 'MEETING'
               AND a.doi_tuong_loai = 'LICH_CONG_TAC'
               AND a.doi_tuong_id = :id
             ORDER BY a.created_at DESC
             LIMIT :n
        """), {"id": str(cuoc_hop_id), "n": gioi_han})).all()
        return [{"hanh_dong": h, "chi_tiet": ct, "thoi_diem": t,
                 "nguoi_thuc_hien": ho_ten}
                for h, ct, t, ho_ten in rows]

    # ── dashboard ─────────────────────────────────────────────────────
    async def thong_ke(self, hom_nay: Optional[date] = None) -> dict:
        hn = hom_nay or date.today()
        dau_tuan = hn - timedelta(days=hn.weekday())

        async def dem(tu: date, den: date) -> int:
            cau = self._cau_truy_van(tu_ngay=tu, den_ngay=den)
            return int(await self.db.scalar(
                select(func.count()).select_from(cau.subquery())) or 0)

        # Trọn tháng, không cắt ở hôm nay: lịch là để nhìn việc SẮP tới, đếm
        # đến hôm nay thì đầu tháng nào con số cũng gần bằng 0.
        cuoi_thang = (date(hn.year + (hn.month == 12), (hn.month % 12) + 1, 1)
                      - timedelta(days=1))

        cau_loai = (select(CuocHop.loai_lich, func.count())
                    .where(CuocHop.is_deleted.is_(False),
                           CuocHop.ngay_hien_thi.between(
                               hn.replace(day=1), cuoi_thang))
                    .group_by(CuocHop.loai_lich))
        theo_loai = {k or "?": v
                     for k, v in (await self.db.execute(cau_loai)).all()}

        # Số sự kiện theo từng lãnh đạo trong tháng — dựa trên bảng lãnh đạo
        # liên quan (khớp 100% khi di trú) HỢP với vai trò chủ toạ, vì lichkv8
        # ghi lãnh đạo theo cả hai cách.
        cau_ld = sa_text("""
            SELECT cc.id, cc.ho_ten, cc.chuc_vu, count(*) AS so_su_kien
              FROM meeting.cuoc_hop ch
              JOIN LATERAL (
                    SELECT ldlq.cong_chuc_id
                      FROM meeting.lanh_dao_lien_quan ldlq
                     WHERE ldlq.cuoc_hop_id = ch.id
                    UNION
                    SELECT ch.chu_toa_id WHERE ch.chu_toa_id IS NOT NULL
                   ) AS ld(cong_chuc_id) ON TRUE
              JOIN public.cong_chuc cc ON cc.id = ld.cong_chuc_id
             WHERE ch.is_deleted = false
               AND ch.ngay_hien_thi BETWEEN :dau AND :cuoi
             GROUP BY cc.id, cc.ho_ten, cc.chuc_vu
             ORDER BY so_su_kien DESC, cc.ho_ten
             LIMIT 20
        """)
        theo_lanh_dao = [
            {"cong_chuc_id": i, "ho_ten": h, "chuc_vu": cv, "so_su_kien": n}
            for i, h, cv, n in (await self.db.execute(
                cau_ld, {"dau": hn.replace(day=1), "cuoi": cuoi_thang})).all()
        ]

        return {
            "hom_nay": await dem(hn, hn),
            "ngay_mai": await dem(hn + timedelta(days=1), hn + timedelta(days=1)),
            "trong_tuan": await dem(dau_tuan, dau_tuan + timedelta(days=6)),
            "trong_thang": await dem(hn.replace(day=1), cuoi_thang),
            "trong_nam": await dem(hn.replace(month=1, day=1),
                                   hn.replace(month=12, day=31)),
            "theo_loai_thang_nay": theo_loai,
            "theo_lanh_dao_thang_nay": theo_lanh_dao,
            # Giao diện cần biết mốc để bấm thẻ là nhảy sang lịch đúng khoảng.
            "moc": {
                "hom_nay": hn,
                "ngay_mai": hn + timedelta(days=1),
                "dau_tuan": dau_tuan,
                "cuoi_tuan": dau_tuan + timedelta(days=6),
                "dau_thang": hn.replace(day=1),
                "cuoi_thang": cuoi_thang,
                "dau_nam": hn.replace(month=1, day=1),
                "cuoi_nam": hn.replace(month=12, day=31),
            },
        }


def _doc_duoc(v: Any) -> str:
    """Đổi giá trị sang chuỗi để ghi vào nhật ký.

    JSONB không nhận date/time/UUID, mà nhật ký là để người đọc chứ không phải
    máy đọc lại, nên quy hết về chuỗi ngay tại đây.
    """
    if v is None:
        return ""
    if isinstance(v, date):
        return v.strftime("%d/%m/%Y")
    if isinstance(v, time):
        return v.strftime("%H:%M")
    return str(v)
