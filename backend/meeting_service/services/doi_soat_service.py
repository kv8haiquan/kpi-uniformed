"""
doi_soat_service.py
====================
Màn hình đối soát tài liệu di trú — G4.9. **Dùng một lần** rồi ẩn khỏi menu.

Bối cảnh: 1.225 file trên Drive, 813 file tự gắn được vào cuộc họp nhờ khớp
thư mục. Còn 412 file trong 34 thư mục mà máy không đoán ra thuộc cuộc họp nào.

Vì sao không tự động nốt được: ngày nào cũng có 2–8 cuộc họp — riêng "Chỉ đạo
trực ban" lặp gần như hằng ngày — nên KHÔNG thư mục nào có ứng viên duy nhất.
Xếp hạng theo từ khoá chỉ làm rõ được 9/29 trường hợp; số còn lại tên viết tắt
quá ("TL HN chỉ số", "260519-CCT lv KTSTQ"). Vì vậy màn hình này đưa ra DANH
SÁCH để người chọn, không phải nút xác nhận một chạm.

Mọi quyết định ghi kèm người và thời điểm — xuất Excel ra là biên bản đối chiếu
nộp khi nghiệm thu.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.models.lich_cong_tac import DiTruDoiSoat
from meeting_service.services.audit_log_service import ghi_audit
from meeting_service.services.lich_cong_tac_service import LoiNghiepVu
from shared.auth import TokenPayload

QUYET_DINH_VALUES = ["GAN_CUOC_HOP", "TAO_CUOC_HOP_LICH_SU", "KHO_LUU_TRU",
                     "KHONG_DI_TRU"]

NHAN_QUYET_DINH = {
    "GAN_CUOC_HOP": "Gắn vào cuộc họp đã có",
    "TAO_CUOC_HOP_LICH_SU": "Tạo cuộc họp lịch sử từ thư mục",
    "KHO_LUU_TRU": "Đưa vào kho lưu trữ, không gắn",
    "KHONG_DI_TRU": "Không di trú",
}

# Chỉ Chánh Văn phòng và Quản trị viên thấy màn hình này — quyết định ở đây
# ảnh hưởng tới toàn bộ kho tài liệu họp.
MA_CC_CHANH_VP = "20ZZ-0097"

# Từ vô nghĩa khi so khớp: xuất hiện ở hầu hết tên thư mục nên không phân biệt
# được gì, mà lại đẩy điểm lên đều cho mọi ứng viên.
TU_BO_QUA = {
    "tl", "tai", "lieu", "tailieu", "hop", "gm", "giay", "moi", "ban",
    "cua", "va", "ve", "cac", "kv8", "hqkv8", "chi", "cuc", "so", "nam",
    "thang", "ngay", "phong", "doi", "to",
}


def _chuan(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def tach_tu(s: str) -> set[str]:
    """Tách thành tập từ có nghĩa để so khớp.

    Bỏ token thuần số: hầu hết là ngày tháng dạng `260425` hoặc số giấy mời,
    đã có cột riêng nên đưa vào đây chỉ gây khớp giả.
    """
    return {t for t in _chuan(s).split()
            if len(t) > 1 and t not in TU_BO_QUA and not t.isdigit()}


class DoiSoatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def duoc_xem(user: TokenPayload) -> bool:
        return bool(user.is_admin
                    or user.vai_tro in ("ADMIN", "SUPER_ADMIN")
                    or user.ma_cc == MA_CC_CHANH_VP)

    def _chan_neu_khong_duoc_xem(self, user: TokenPayload) -> None:
        if not self.duoc_xem(user):
            raise LoiNghiepVu(
                "KHONG_DU_QUYEN",
                "Màn hình đối soát chỉ dành cho Chánh Văn phòng và Quản trị "
                "viên", 403)

    # ── danh sách cụm ─────────────────────────────────────────────────

    async def danh_sach(self, *, user: TokenPayload,
                        nhom: Optional[str] = None,
                        da_quyet_dinh: Optional[bool] = None) -> dict:
        self._chan_neu_khong_duoc_xem(user)

        dk = []
        if nhom:
            dk.append(DiTruDoiSoat.nhom == nhom)
        if da_quyet_dinh is True:
            dk.append(DiTruDoiSoat.quyet_dinh.isnot(None))
        elif da_quyet_dinh is False:
            dk.append(DiTruDoiSoat.quyet_dinh.is_(None))

        cau = select(DiTruDoiSoat)
        if dk:
            cau = cau.where(and_(*dk))
        rows = (await self.db.execute(
            cau.order_by(DiTruDoiSoat.nhom, DiTruDoiSoat.ngay_suy_ra)
        )).scalars().all()

        # Tên người quyết định, nạp theo lô.
        ten_nguoi: dict[UUID, str] = {}
        ids = {r.nguoi_quyet_dinh_id for r in rows if r.nguoi_quyet_dinh_id}
        if ids:
            q = await self.db.execute(sa_text(
                "SELECT id, ho_ten FROM public.cong_chuc WHERE id = ANY(:ids)"),
                {"ids": list(ids)})
            ten_nguoi = {i: h for i, h in q.all()}

        dong = [{
            "id": r.id,
            "nhom": r.nhom,
            "duong_dan_thu_muc": r.duong_dan_thu_muc,
            "ten_thu_muc": r.duong_dan_thu_muc.rsplit("/", 1)[-1],
            "drive_folder_id": r.drive_folder_id,
            "so_file": r.so_file,
            "ngay_suy_ra": r.ngay_suy_ra,
            "so_gm_suy_ra": r.so_gm_suy_ra,
            "danh_sach_file": r.danh_sach_file or [],
            "quyet_dinh": r.quyet_dinh,
            "quyet_dinh_nhan": NHAN_QUYET_DINH.get(r.quyet_dinh or ""),
            "cuoc_hop_id": r.cuoc_hop_id,
            "nguoi_quyet_dinh": ten_nguoi.get(r.nguoi_quyet_dinh_id or UUID(int=0)),
            "thoi_diem_quyet_dinh": r.thoi_diem_quyet_dinh,
            "ghi_chu": r.ghi_chu,
        } for r in rows]

        return {
            "dong": dong,
            "tong_hop": {
                "tong_thu_muc": len(dong),
                "tong_file": sum(d["so_file"] for d in dong),
                "da_quyet_dinh": sum(1 for d in dong if d["quyet_dinh"]),
                "con_lai": sum(1 for d in dong if not d["quyet_dinh"]),
            },
        }

    # ── gợi ý ứng viên ────────────────────────────────────────────────

    async def ung_vien(self, doi_soat_id: UUID, *, user: TokenPayload,
                       so_ngay: int = 3, gioi_han: int = 15) -> dict:
        """Cuộc họp có thể là chủ của thư mục này, xếp theo độ trùng từ khoá.

        Cửa sổ ngày mặc định ±3 ngày quanh ngày suy ra từ tên thư mục. Không
        suy ra được ngày thì mở rộng ra toàn bộ, chỉ xếp theo từ khoá.
        """
        self._chan_neu_khong_duoc_xem(user)
        r = await self._lay(doi_soat_id)

        dk = [CuocHop.is_deleted.is_(False)]
        if r.ngay_suy_ra:
            dk.append(CuocHop.ngay_hien_thi.between(
                r.ngay_suy_ra - timedelta(days=so_ngay),
                r.ngay_suy_ra + timedelta(days=so_ngay)))

        hop = (await self.db.execute(
            select(CuocHop).where(and_(*dk))
            .order_by(CuocHop.ngay_hien_thi))).scalars().all()

        tu_thu_muc = tach_tu(r.duong_dan_thu_muc.rsplit("/", 1)[-1])
        # Tên file cũng là manh mối — nhiều thư mục tên viết tắt nhưng file bên
        # trong ghi rõ nội dung.
        tu_file: set[str] = set()
        for f in (r.danh_sach_file or []):
            tu_file |= tach_tu(f.get("ten", ""))

        ket_qua = []
        for h in hop:
            tu_hop = tach_tu(h.tieu_de)
            chung_tm = tu_thu_muc & tu_hop
            chung_file = (tu_file & tu_hop) - chung_tm

            # Từ trùng ở tên thư mục đáng tin hơn ở tên file: thư mục do người
            # tạo cuộc họp đặt, còn tên file thì ai nộp cũng đặt một kiểu.
            diem = len(chung_tm) * 3 + len(chung_file)
            if r.ngay_suy_ra and h.ngay_hien_thi == r.ngay_suy_ra:
                diem += 2
            if r.so_gm_suy_ra and r.so_gm_suy_ra == (h.so_van_ban or ""):
                diem += 10   # số giấy mời trùng gần như chắc chắn đúng

            if diem <= 0:
                continue
            ket_qua.append({
                "cuoc_hop_id": h.id,
                "ma_lich": h.ma_lich,
                "tieu_de": h.tieu_de,
                "ngay": h.ngay_hien_thi,
                "gio_bat_dau": h.gio_bat_dau,
                "so_van_ban": h.so_van_ban,
                "don_vi_chuan_bi": h.don_vi_chuan_bi,
                "diem": diem,
                "tu_trung": sorted(chung_tm | chung_file),
            })

        ket_qua.sort(key=lambda x: (-x["diem"], x["ngay"] or date.min))
        return {
            "thu_muc": r.duong_dan_thu_muc,
            "ngay_suy_ra": r.ngay_suy_ra,
            "so_ung_vien": len(ket_qua),
            # Không có ứng viên nào nổi trội hẳn thì nói thẳng, đừng để người
            # dùng tưởng ứng viên đầu bảng là đáp án.
            "co_ung_vien_noi_troi": bool(
                len(ket_qua) >= 2
                and ket_qua[0]["diem"] >= ket_qua[1]["diem"] * 2),
            "ung_vien": ket_qua[:gioi_han],
        }

    # ── ghi quyết định ────────────────────────────────────────────────

    async def quyet_dinh(self, doi_soat_id: UUID, *, user: TokenPayload,
                         quyet_dinh: str,
                         cuoc_hop_id: Optional[UUID] = None,
                         ghi_chu: Optional[str] = None) -> dict:
        self._chan_neu_khong_duoc_xem(user)

        if quyet_dinh not in QUYET_DINH_VALUES:
            raise LoiNghiepVu("QUYET_DINH_KHONG_HOP_LE",
                              f"quyet_dinh phải thuộc {QUYET_DINH_VALUES}")

        r = await self._lay(doi_soat_id)

        if quyet_dinh == "GAN_CUOC_HOP":
            if not cuoc_hop_id:
                raise LoiNghiepVu("THIEU_CUOC_HOP",
                                  "Chọn 'gắn vào cuộc họp' thì phải chỉ ra "
                                  "cuộc họp nào")
            ch = await self.db.get(CuocHop, cuoc_hop_id)
            if not ch or ch.is_deleted:
                raise LoiNghiepVu("KHONG_TIM_THAY_CUOC_HOP",
                                  "Không tìm thấy cuộc họp đã chọn", 404)
            r.cuoc_hop_id = cuoc_hop_id

        elif quyet_dinh == "TAO_CUOC_HOP_LICH_SU":
            r.cuoc_hop_id = await self._tao_cuoc_hop_lich_su(r, user)

        else:
            r.cuoc_hop_id = None

        r.quyet_dinh = quyet_dinh
        r.nguoi_quyet_dinh_id = UUID(user.sub)
        r.thoi_diem_quyet_dinh = datetime.now()
        r.ghi_chu = ghi_chu

        await ghi_audit(
            self.db, hanh_dong="DOI_SOAT_QUYET_DINH",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="DI_TRU_DOI_SOAT", doi_tuong_id=r.id,
            chi_tiet={"thu_muc": r.duong_dan_thu_muc,
                      "quyet_dinh": quyet_dinh,
                      "cuoc_hop_id": str(r.cuoc_hop_id) if r.cuoc_hop_id else None,
                      "so_file": r.so_file})
        await self.db.commit()
        return await self._mot(r.id)

    async def huy_quyet_dinh(self, doi_soat_id: UUID, *,
                             user: TokenPayload) -> dict:
        """Bỏ quyết định để chọn lại.

        KHÔNG xoá cuộc họp lịch sử đã tạo — có thể đã có người gắn tài liệu
        khác vào đó. Xoá cuộc họp là việc riêng, làm ở màn hình lịch.
        """
        self._chan_neu_khong_duoc_xem(user)
        r = await self._lay(doi_soat_id)
        if not r.quyet_dinh:
            raise LoiNghiepVu("CHUA_QUYET_DINH", "Thư mục này chưa có quyết định")

        cu = r.quyet_dinh
        r.quyet_dinh = None
        r.nguoi_quyet_dinh_id = None
        r.thoi_diem_quyet_dinh = None

        await ghi_audit(
            self.db, hanh_dong="DOI_SOAT_HUY_QUYET_DINH",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="DI_TRU_DOI_SOAT", doi_tuong_id=r.id,
            chi_tiet={"thu_muc": r.duong_dan_thu_muc, "quyet_dinh_cu": cu})
        await self.db.commit()
        return await self._mot(r.id)

    # ── phụ trợ ───────────────────────────────────────────────────────

    async def _tao_cuoc_hop_lich_su(self, r: DiTruDoiSoat,
                                    user: TokenPayload) -> UUID:
        """Dựng một cuộc họp từ chính tên thư mục.

        Dùng cho tài liệu có trước khi hệ thống chạy (Drive có file từ
        24/01/2026, còn bảng MEETING chỉ bắt đầu 09/03/2026) — không có cuộc
        họp nào để gắn vào vì lúc đó chưa ai nhập lịch.
        """
        from meeting_service.services.lich_cong_tac_service import (
            LichCongTacService,
        )

        if not r.ngay_suy_ra:
            raise LoiNghiepVu(
                "KHONG_SUY_RA_NGAY",
                "Tên thư mục không cho biết ngày nên không dựng được cuộc "
                "họp — chọn cách khác hoặc tạo lịch thủ công rồi gắn vào")

        svc = LichCongTacService(self.db)
        ten = r.duong_dan_thu_muc.rsplit("/", 1)[-1]
        ch = CuocHop(
            nguon="LICH_CONG_TAC",
            ma_lich=await svc._sinh_ma_lich(),          # noqa: SLF001
            tieu_de=ten[:500],
            loai_lich="HOP",
            ngay_hop=r.ngay_suy_ra,
            ngay_hien_thi=r.ngay_suy_ra,
            gio_bat_dau=datetime.min.time().replace(hour=8),
            trang_thai="HOAN_THANH",
            so_van_ban=r.so_gm_suy_ra,
            mo_ta=("Cuộc họp dựng lại từ thư mục tài liệu trên Drive khi đối "
                   f"soát di trú: {r.duong_dan_thu_muc}"),
            created_by=UUID(user.sub),
            updated_by=UUID(user.sub),
        )
        self.db.add(ch)
        await self.db.flush()
        return ch.id

    async def _lay(self, doi_soat_id: UUID) -> DiTruDoiSoat:
        r = await self.db.get(DiTruDoiSoat, doi_soat_id)
        if not r:
            raise LoiNghiepVu("KHONG_TIM_THAY",
                              "Không tìm thấy thư mục đối soát", 404)
        return r

    async def _mot(self, doi_soat_id: UUID) -> dict[str, Any]:
        r = await self._lay(doi_soat_id)
        return {
            "id": r.id,
            "nhom": r.nhom,
            "duong_dan_thu_muc": r.duong_dan_thu_muc,
            "so_file": r.so_file,
            "quyet_dinh": r.quyet_dinh,
            "quyet_dinh_nhan": NHAN_QUYET_DINH.get(r.quyet_dinh or ""),
            "cuoc_hop_id": r.cuoc_hop_id,
            "thoi_diem_quyet_dinh": r.thoi_diem_quyet_dinh,
            "ghi_chu": r.ghi_chu,
        }
