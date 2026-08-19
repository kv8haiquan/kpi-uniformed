"""
truc_ban_service.py
====================
Lịch trực ban cuối tuần — G4.7.

Hình dạng nghiệp vụ: mỗi ngày cuối tuần, MỖI trụ sở cử người trực. Bảng ma
trận là cách Văn phòng vẫn đọc — hàng là ngày, cột là trụ sở, ô là người trực.

Khoá theo **trụ sở**, không phải đơn vị. Một đơn vị có thể giữ nhiều trụ sở,
và trụ sở Chi cục thì không thuộc đơn vị nào — lấy đơn vị làm khoá là mất
đúng cái cột đó.

Phân quyền THAY chứ không port. `isDutyAdmin_()` của lichkv8 (Mã.gs dòng 4591)
dò chuỗi trên họ tên + chức vụ + đơn vị gộp lại: ai có đơn vị chứa "Văn phòng"
hoặc chức vụ chứa "lãnh đạo" đều thành quản trị toàn Chi cục. Ở đây dùng quyền
chức năng thật, dựa trên vai_tro và don_vi_id khoá ngoại.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models.lich_cong_tac import TrucBan, TrucBanTruSo, TruSo
from meeting_service.services.audit_log_service import ghi_audit
from meeting_service.services.lich_cong_tac_service import (
    THU_VN,
    LoiNghiepVu,
    la_quan_tri_lich,
)
from shared.auth import TokenPayload

# Phải khớp CHECK `ck_truc_ban_loai` trong CSDL. Lệch một giá trị là người
# dùng chọn xong nhận lỗi 500 thay vì thông báo tử tế — schema không được tự
# nghĩ ra danh mục riêng.
LOAI_TRUC_VALUES = ["CUOI_TUAN", "NGAY_THUONG", "LE_TET"]

NHAN_LOAI_TRUC = {
    "CUOI_TUAN": "Cuối tuần",
    "NGAY_THUONG": "Ngày thường",
    "LE_TET": "Lễ, Tết",
}
CA_TRUC_VALUES = ["CA_NGAY", "SANG", "CHIEU", "DEM"]
TRANG_THAI_VALUES = ["NHAP", "DA_NOP"]


# ── thứ tự chức vụ ────────────────────────────────────────────────────
# Yêu cầu: CCT → PCCT → Trưởng/Chánh → Phó → Công chức. So khớp trên chuỗi
# chức vụ vì đó là dữ liệu duy nhất có (`truc_ban.chuc_vu` là văn bản tự do,
# nhập tay từ hệ cũ) — nhưng chỉ dùng để SẮP XẾP, không dùng để phân quyền.
#
# Thứ tự trong danh sách là thứ tự XÉT, không phải thứ hạng — luật hẹp phải
# đứng trước luật rộng, nếu không "Phó Chi cục trưởng" khớp luôn vào luật của
# "Chi cục trưởng" và hai người xếp ngang nhau.
#
# So khớp theo TỪ (`\b`) chứ không theo chuỗi con: "Chánh Văn phòng" bỏ dấu
# thành "chanh van phong", mà "phong" chứa "pho" — dò chuỗi con sẽ xếp Chánh
# Văn phòng xuống hàng cấp phó.
_BAC_CHUC_VU = [
    (r"\bpho chi cuc truong\b", 1),
    (r"\bchi cuc truong\b", 0),
    (r"\bpho\b", 3),
    (r"\b(truong|chanh)\b", 2),
]


def _bo_dau(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d")


def bac_chuc_vu(chuc_vu: Optional[str]) -> int:
    """Số càng nhỏ càng đứng trên. Không khớp gì thì xuống cuối."""
    s = _bo_dau(chuc_vu or "")
    for mau, bac in _BAC_CHUC_VU:
        if re.search(mau, s):
            return bac
    return 9


def chuan_hoa_sdt(v: object) -> Optional[str]:
    """Đưa số điện thoại về dạng chuẩn `0xxxxxxxxx`.

    Dữ liệu di trú từ lichkv8 hỏng theo hai kiểu, cùng một nguyên nhân là
    Excel coi số điện thoại như SỐ chứ không phải chuỗi:

      - `9.13264340E8`  → Excel đổi sang số thực, mất số 0 đứng đầu
      - `0916,382,222`  → Excel chèn dấu phân cách hàng nghìn

    Hàm này cũng chạy khi thêm/nhập mới, để một chỗ sửa là mọi đường vào đều
    sạch — nếu không thì nhập Excel lần sau lại đẻ ra đúng bộ dữ liệu hỏng này.
    """
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None

    # Dạng khoa học: 9.13264340E8 → 913264340
    if re.fullmatch(r"[0-9]+\.?[0-9]*[Ee][+]?[0-9]+", s):
        try:
            s = str(int(float(s)))
        except (ValueError, OverflowError):
            return s

    so = re.sub(r"[^0-9+]", "", s)

    # +84 / 84 đứng đầu là mã quốc gia — đưa về dạng nội địa.
    if so.startswith("+84"):
        so = "0" + so[3:]
    elif so.startswith("84") and len(so) == 11:
        so = "0" + so[2:]

    # 9 chữ số là đã rụng số 0 đứng đầu.
    if len(so) == 9 and not so.startswith("0"):
        so = "0" + so

    return so or None


class TrucBanService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── quyền ─────────────────────────────────────────────────────────

    async def _tru_so_sua_duoc(self, user: TokenPayload) -> Optional[set[UUID]]:
        """Tập trụ sở user được sửa. `None` nghĩa là sửa được tất cả.

        Người thường sửa trụ sở thuộc đơn vị mình. Trụ sở Chi cục không thuộc
        đơn vị nào nên chỉ quản trị lịch mới đụng được — đúng thực tế, lịch
        trực trụ sở Chi cục do Văn phòng xếp.
        """
        if la_quan_tri_lich(user):
            return None
        if not user.don_vi_id:
            return set()
        try:
            dv = UUID(user.don_vi_id)
        except (ValueError, TypeError):
            return set()
        rows = (await self.db.execute(
            select(TruSo.id).where(TruSo.don_vi_id == dv))).scalars().all()
        return set(rows)

    async def _kiem_tra_sua(self, tru_so_id: UUID, user: TokenPayload) -> None:
        duoc = await self._tru_so_sua_duoc(user)
        if duoc is None or tru_so_id in duoc:
            return
        raise LoiNghiepVu(
            "KHONG_DU_QUYEN",
            "Chỉ sửa được lịch trực của trụ sở thuộc đơn vị mình", 403)

    # ── danh mục ──────────────────────────────────────────────────────

    async def danh_muc_tru_so(self) -> list[dict]:
        rows = (await self.db.execute(
            select(TruSo).where(TruSo.is_active.is_(True))
            .order_by(TruSo.thu_tu))).scalars().all()
        return [{"id": r.id, "ma_tru_so": r.ma_tru_so,
                 "ten_tru_so": r.ten_tru_so, "don_vi_id": r.don_vi_id,
                 "thu_tu": r.thu_tu} for r in rows]

    async def nguoi_goi_y(self, tru_so_id: UUID, *,
                          tu_khoa: Optional[str] = None,
                          gioi_han: int = 200) -> list[dict]:
        """Công chức có thể phân trực ở trụ sở này, kèm số điện thoại gợi ý.

        Số điện thoại KHÔNG lấy từ `public.cong_chuc`: bảng đó chỉ có 6/544
        người khai số. Nguồn thật là chính lịch trực cũ — lichkv8 ghi số theo
        từng lượt trực, nên lấy lượt gần nhất của người đó.

        Trụ sở Chi cục không gắn với đơn vị nào (`don_vi_id` rỗng) nên trả toàn
        Chi cục; lịch trực trụ sở Chi cục do Văn phòng xếp, người trực có thể
        thuộc bất kỳ phòng nào.
        """
        ts = await self.db.get(TruSo, tru_so_id)
        if ts is None:
            raise LoiNghiepVu("KHONG_TIM_THAY", "Không tìm thấy trụ sở", 404)

        dieu_kien = "cc.is_active"
        tham_so: dict = {"gioi_han": gioi_han}
        if ts.don_vi_id:
            dieu_kien += " AND cc.don_vi_id = :dv"
            tham_so["dv"] = ts.don_vi_id
        if tu_khoa:
            dieu_kien += " AND (cc.ho_ten ILIKE :tk OR cc.ma_cc ILIKE :tk)"
            tham_so["tk"] = f"%{tu_khoa.strip()}%"

        rows = (await self.db.execute(sa_text(f"""
            SELECT cc.id, cc.ma_cc, cc.ho_ten, cc.chuc_vu, cc.is_lanh_dao,
                   (SELECT tb.so_dien_thoai
                      FROM meeting.truc_ban tb
                     WHERE tb.cong_chuc_id = cc.id
                       AND tb.so_dien_thoai IS NOT NULL
                     ORDER BY tb.ngay_truc DESC
                     LIMIT 1) AS sdt_goi_y
              FROM public.cong_chuc cc
             WHERE {dieu_kien}
             ORDER BY cc.is_lanh_dao DESC, cc.ho_ten
             LIMIT :gioi_han
        """), tham_so)).all()

        # Chuẩn hoá cả khi ĐỌC, không chỉ khi ghi: dữ liệu di trú có thể còn
        # sót bản ghi hỏng ở môi trường chưa vá, và số hiện sai trên màn hình
        # thì người dùng chép nhầm vào báo cáo.
        ds = [{"cong_chuc_id": i, "ma_cc": ma, "ho_ten": ht, "chuc_vu": cv,
               "is_lanh_dao": ld, "so_dien_thoai": chuan_hoa_sdt(sdt)}
              for i, ma, ht, cv, ld, sdt in rows]
        # Chức vụ quyết định thứ tự hiển thị trong ô nên xếp sẵn theo bậc,
        # người dùng chọn từ trên xuống là ra đúng thứ tự.
        ds.sort(key=lambda x: (bac_chuc_vu(x["chuc_vu"]), x["ho_ten"]))
        return ds

    # ── ma trận ───────────────────────────────────────────────────────

    async def ma_tran(self, tu_ngay: date, den_ngay: date, *,
                      user: TokenPayload,
                      don_vi_id: Optional[UUID] = None,
                      chi_cuoi_tuan: bool = True) -> dict:
        """Hàng = ngày, cột = trụ sở, ô = danh sách người trực.

        Ngày cuối tuần luôn có hàng kể cả khi chưa ai trực — ô trống chính là
        thông tin, đó là chỗ Văn phòng phải đi hỏi.

        `chi_cuoi_tuan=True` (mặc định) bỏ các ngày trong tuần, vì Chi cục chỉ
        phân trực Thứ Bảy và Chủ Nhật. NHƯNG ngày thường CÓ người trực thì vẫn
        giữ lại — trực ngày lễ rơi vào giữa tuần, lọc cứng theo thứ là giấu mất
        đúng những ca đặc biệt đó.
        """
        if den_ngay < tu_ngay:
            raise LoiNghiepVu("KHOANG_NGAY_SAI",
                              "den_ngay không được trước tu_ngay")
        if (den_ngay - tu_ngay).days > 120:
            raise LoiNghiepVu("KHOANG_NGAY_QUA_DAI",
                              "Khoảng ngày tối đa 120 ngày")

        cot = await self.danh_muc_tru_so()
        if don_vi_id:
            cot = [c for c in cot if c["don_vi_id"] == don_vi_id]
        cot_ids = {c["id"] for c in cot}

        rows = (await self.db.execute(
            select(TrucBan).where(and_(
                TrucBan.ngay_truc.between(tu_ngay, den_ngay),
                TrucBan.is_deleted.is_(False),
            )).order_by(TrucBan.ngay_truc))).scalars().all()

        # Trạng thái nộp theo (ngày, trụ sở).
        nop: dict[tuple[date, UUID], dict] = {}
        for r in (await self.db.execute(
            select(TrucBanTruSo).where(
                TrucBanTruSo.ngay_truc.between(tu_ngay, den_ngay))
        )).scalars().all():
            nop[(r.ngay_truc, r.tru_so_id)] = {
                "trang_thai": r.trang_thai, "is_locked": r.is_locked}

        o: dict[tuple[date, UUID], list[dict]] = {}
        for r in rows:
            if r.tru_so_id not in cot_ids:
                continue
            o.setdefault((r.ngay_truc, r.tru_so_id), []).append({
                "id": r.id,
                "ho_ten": r.ho_ten,
                "chuc_vu": r.chuc_vu,
                "so_dien_thoai": chuan_hoa_sdt(r.so_dien_thoai),
                "cong_chuc_id": r.cong_chuc_id,
                "ca_truc": r.ca_truc,
                "loai_truc": r.loai_truc,
                "ghi_chu": r.ghi_chu,
                "trang_thai": r.trang_thai,
            })
        for ds in o.values():
            ds.sort(key=lambda x: (bac_chuc_vu(x["chuc_vu"]), x["ho_ten"]))

        sua_duoc = await self._tru_so_sua_duoc(user)

        hang = []
        n = tu_ngay
        while n <= den_ngay:
            cuoi_tuan = n.weekday() >= 5
            if chi_cuoi_tuan and not cuoi_tuan:
                co_nguoi = any((n, c["id"]) in o for c in cot)
                if not co_nguoi:
                    n += timedelta(days=1)
                    continue
            hang.append({
                "ngay": n,
                "thu": THU_VN[n.weekday()],
                "cuoi_tuan": cuoi_tuan,
                "o": [{
                    "tru_so_id": c["id"],
                    "nguoi": o.get((n, c["id"]), []),
                    "trang_thai": nop.get((n, c["id"]), {}).get(
                        "trang_thai", "NHAP"),
                    "is_locked": nop.get((n, c["id"]), {}).get(
                        "is_locked", False),
                    "sua_duoc": sua_duoc is None or c["id"] in sua_duoc,
                } for c in cot],
            })
            n += timedelta(days=1)

        return {
            "tu_ngay": tu_ngay,
            "den_ngay": den_ngay,
            "tru_so": cot,
            "hang": hang,
            "la_quan_tri": sua_duoc is None,
        }

    # ── danh sách chi tiết ────────────────────────────────────────────

    async def danh_sach(self, tu_ngay: date, den_ngay: date, *,
                        tru_so_id: Optional[UUID] = None) -> list[dict]:
        dk = [TrucBan.ngay_truc.between(tu_ngay, den_ngay),
              TrucBan.is_deleted.is_(False)]
        if tru_so_id:
            dk.append(TrucBan.tru_so_id == tru_so_id)

        q = (select(TrucBan, TruSo.ten_tru_so, TruSo.thu_tu)
             .join(TruSo, TruSo.id == TrucBan.tru_so_id)
             .where(and_(*dk))
             .order_by(TrucBan.ngay_truc, TruSo.thu_tu))
        rows = (await self.db.execute(q)).all()

        ket_qua = [{
            "id": r.id, "ngay_truc": r.ngay_truc, "thu": THU_VN[r.ngay_truc.weekday()],
            "tru_so_id": r.tru_so_id, "ten_tru_so": ten,
            "ho_ten": r.ho_ten, "chuc_vu": r.chuc_vu,
            "so_dien_thoai": r.so_dien_thoai, "ca_truc": r.ca_truc,
            "loai_truc": r.loai_truc, "ghi_chu": r.ghi_chu,
            "trang_thai": r.trang_thai,
        } for r, ten, _ in rows]
        ket_qua.sort(key=lambda x: (x["ngay_truc"], x["ten_tru_so"],
                                    bac_chuc_vu(x["chuc_vu"]), x["ho_ten"]))
        return ket_qua

    # ── ghi ───────────────────────────────────────────────────────────

    async def them(self, du_lieu: dict, *, user: TokenPayload) -> dict:
        await self._kiem_tra_sua(du_lieu["tru_so_id"], user)
        if "so_dien_thoai" in du_lieu:
            du_lieu["so_dien_thoai"] = chuan_hoa_sdt(du_lieu["so_dien_thoai"])
        await self._chan_khi_da_khoa(du_lieu["ngay_truc"],
                                     du_lieu["tru_so_id"])

        r = TrucBan(created_by=UUID(user.sub), updated_by=UUID(user.sub),
                    **du_lieu)
        self.db.add(r)
        await self.db.flush()
        await ghi_audit(
            self.db, hanh_dong="THEM_TRUC_BAN", nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="TRUC_BAN", doi_tuong_id=r.id,
            chi_tiet={"ngay": r.ngay_truc.isoformat(), "ho_ten": r.ho_ten})
        await self.db.commit()
        return await self._mot(r.id)

    async def sua(self, truc_ban_id: UUID, thay_doi: dict, *,
                  user: TokenPayload) -> dict:
        r = await self._lay(truc_ban_id)
        await self._kiem_tra_sua(r.tru_so_id, user)
        await self._chan_khi_da_khoa(r.ngay_truc, r.tru_so_id)

        if "so_dien_thoai" in thay_doi:
            thay_doi["so_dien_thoai"] = chuan_hoa_sdt(thay_doi["so_dien_thoai"])
        for k, v in thay_doi.items():
            setattr(r, k, v)
        r.updated_by = UUID(user.sub)

        await ghi_audit(
            self.db, hanh_dong="SUA_TRUC_BAN", nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="TRUC_BAN", doi_tuong_id=r.id,
            chi_tiet={"ngay": r.ngay_truc.isoformat(),
                      "truong": list(thay_doi)})
        await self.db.commit()
        return await self._mot(r.id)

    async def xoa(self, truc_ban_id: UUID, *, user: TokenPayload) -> None:
        r = await self._lay(truc_ban_id)
        await self._kiem_tra_sua(r.tru_so_id, user)
        await self._chan_khi_da_khoa(r.ngay_truc, r.tru_so_id)

        r.is_deleted = True
        r.updated_by = UUID(user.sub)
        await ghi_audit(
            self.db, hanh_dong="XOA_TRUC_BAN", nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="TRUC_BAN", doi_tuong_id=r.id,
            chi_tiet={"ngay": r.ngay_truc.isoformat(), "ho_ten": r.ho_ten})
        await self.db.commit()

    async def nop(self, ngay_truc: date, tru_so_id: UUID, *,
                  user: TokenPayload) -> dict:
        """Nộp chính thức một ô: NHAP → DA_NOP, và khoá lại.

        Sau khi nộp, đơn vị không tự sửa được nữa — muốn sửa phải nhờ quản trị
        mở khoá. Đó là điểm khác biệt với hệ cũ, nơi ai sửa lúc nào cũng được
        nên Văn phòng không biết bản nào là bản chốt.
        """
        await self._kiem_tra_sua(tru_so_id, user)

        co_nguoi = await self.db.scalar(
            select(func.count()).select_from(TrucBan).where(
                TrucBan.ngay_truc == ngay_truc,
                TrucBan.tru_so_id == tru_so_id,
                TrucBan.is_deleted.is_(False)))
        if not co_nguoi:
            raise LoiNghiepVu("CHUA_CO_NGUOI_TRUC",
                              "Chưa phân công ai trực nên chưa nộp được")

        r = await self.db.scalar(select(TrucBanTruSo).where(
            TrucBanTruSo.ngay_truc == ngay_truc,
            TrucBanTruSo.tru_so_id == tru_so_id))
        if r is None:
            r = TrucBanTruSo(ngay_truc=ngay_truc, tru_so_id=tru_so_id)
            self.db.add(r)

        r.trang_thai = "DA_NOP"
        r.is_locked = True
        r.nguoi_nop_id = UUID(user.sub)
        r.thoi_diem_nop = datetime.now()
        r.updated_by = UUID(user.sub)

        await self.db.execute(
            TrucBan.__table__.update()
            .where(TrucBan.ngay_truc == ngay_truc,
                   TrucBan.tru_so_id == tru_so_id,
                   TrucBan.is_deleted.is_(False))
            .values(trang_thai="DA_NOP"))

        await ghi_audit(
            self.db, hanh_dong="NOP_TRUC_BAN", nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="TRUC_BAN_TRU_SO", doi_tuong_id=r.id,
            chi_tiet={"ngay": ngay_truc.isoformat(),
                      "tru_so_id": str(tru_so_id)})
        await self.db.commit()
        return {"ngay_truc": ngay_truc, "tru_so_id": tru_so_id,
                "trang_thai": "DA_NOP", "is_locked": True}

    async def mo_khoa(self, ngay_truc: date, tru_so_id: UUID, *,
                      user: TokenPayload) -> dict:
        """Mở khoá để sửa lại — chỉ quản trị lịch."""
        if not la_quan_tri_lich(user):
            raise LoiNghiepVu("KHONG_DU_QUYEN",
                              "Chỉ người quản trị lịch mới mở khoá được", 403)

        r = await self.db.scalar(select(TrucBanTruSo).where(
            TrucBanTruSo.ngay_truc == ngay_truc,
            TrucBanTruSo.tru_so_id == tru_so_id))
        if r is None or not r.is_locked:
            raise LoiNghiepVu("CHUA_KHOA", "Ô này chưa bị khoá")

        r.is_locked = False
        r.trang_thai = "NHAP"
        r.updated_by = UUID(user.sub)
        await self.db.execute(
            TrucBan.__table__.update()
            .where(TrucBan.ngay_truc == ngay_truc,
                   TrucBan.tru_so_id == tru_so_id,
                   TrucBan.is_deleted.is_(False))
            .values(trang_thai="NHAP"))

        await ghi_audit(
            self.db, hanh_dong="MO_KHOA_TRUC_BAN",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="TRUC_BAN_TRU_SO", doi_tuong_id=r.id,
            chi_tiet={"ngay": ngay_truc.isoformat(),
                      "tru_so_id": str(tru_so_id)})
        await self.db.commit()
        return {"ngay_truc": ngay_truc, "tru_so_id": tru_so_id,
                "trang_thai": "NHAP", "is_locked": False}

    # ── bản text để copy ──────────────────────────────────────────────

    async def van_ban(self, tu_ngay: date, den_ngay: date) -> str:
        """Bản text gọn để dán sang Zalo — cùng mục đích với tóm tắt lịch."""
        ds = await self.danh_sach(tu_ngay, den_ngay)
        theo_ngay: dict[date, dict[str, list[str]]] = {}
        for d in ds:
            nguoi = " · ".join(filter(None, [
                d["ho_ten"], d["chuc_vu"], d["so_dien_thoai"]]))
            theo_ngay.setdefault(d["ngay_truc"], {}).setdefault(
                d["ten_tru_so"], []).append(nguoi)

        dong: list[str] = []
        for ngay in sorted(theo_ngay):
            dong.append(f"{THU_VN[ngay.weekday()]}, {ngay:%d/%m/%Y}")
            for tru_so, ds_nguoi in theo_ngay[ngay].items():
                dong.append(f"  {tru_so}: {'; '.join(ds_nguoi)}")
            dong.append("")
        return "\n".join(dong).strip()

    # ── phụ trợ ───────────────────────────────────────────────────────

    async def _lay(self, truc_ban_id: UUID) -> TrucBan:
        r = await self.db.get(TrucBan, truc_ban_id)
        if not r or r.is_deleted:
            raise LoiNghiepVu("KHONG_TIM_THAY",
                              "Không tìm thấy bản ghi trực ban", 404)
        return r

    async def _chan_khi_da_khoa(self, ngay_truc: date,
                                tru_so_id: UUID) -> None:
        khoa = await self.db.scalar(select(TrucBanTruSo.is_locked).where(
            TrucBanTruSo.ngay_truc == ngay_truc,
            TrucBanTruSo.tru_so_id == tru_so_id))
        if khoa:
            raise LoiNghiepVu(
                "DA_KHOA",
                "Ô này đã nộp và bị khoá — đề nghị Văn phòng mở khoá trước "
                "khi sửa", 409)

    async def _mot(self, truc_ban_id: UUID) -> dict:
        r = await self.db.get(TrucBan, truc_ban_id)
        ten = await self.db.scalar(
            select(TruSo.ten_tru_so).where(TruSo.id == r.tru_so_id))
        return {"id": r.id, "ngay_truc": r.ngay_truc,
                "thu": THU_VN[r.ngay_truc.weekday()],
                "tru_so_id": r.tru_so_id, "ten_tru_so": ten,
                "ho_ten": r.ho_ten, "chuc_vu": r.chuc_vu,
                "so_dien_thoai": r.so_dien_thoai, "ca_truc": r.ca_truc,
                "loai_truc": r.loai_truc, "ghi_chu": r.ghi_chu,
                "trang_thai": r.trang_thai}


def tuan_chua(moc: date, lech: int = 0) -> tuple[date, date]:
    """Đầu và cuối tuần chứa `moc`, dịch `lech` tuần. Tuần bắt đầu từ Thứ Hai."""
    dau = moc - timedelta(days=moc.weekday()) + timedelta(weeks=lech)
    return dau, dau + timedelta(days=6)
