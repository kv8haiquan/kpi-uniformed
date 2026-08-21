"""Quản trị danh mục dùng chung của Lịch công tác (G4.11).

Thay sheet `SETUP` của lichkv8 — đáp yêu cầu chuyển đổi mục II.15.

Luật gói gọn trong ba câu:
  1. Ai cũng ĐỌC được danh mục (mọi màn hình lịch đều cần để đổ ô chọn).
  2. Chỉ quản trị lịch mới SỬA được.
  3. Mục `he_thong` sửa được nhãn và thứ tự, không đổi mã / xoá / tắt — vì mã
     của chúng bị mã nguồn rẽ nhánh theo (xem migration meeting_024).
"""

from __future__ import annotations

import re
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import Select, func, select, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models.danh_muc import (
    COT_SU_DUNG,
    NHOM_HOP_LE,
    NHOM_LOAI_TAI_LIEU,
    NHOM_PHONG_HOP,
    DanhMuc,
)
from meeting_service.services.lich_cong_tac_service import (
    LoiNghiepVu,
    la_quan_tri_lich,
)
from shared.auth import TokenPayload


# Mã dùng làm khoá tham chiếu nên giữ dạng máy đọc được: chữ HOA, số, gạch
# dưới. Cho phép gõ thường rồi tự nâng lên hoa, nhưng không nhận dấu tiếng
# Việt hay khoảng trắng — đó là việc của `nhan`.
MAU_MA = re.compile(r"^[A-Z0-9_]{2,50}$")


def _chuan_ma(ma: str) -> str:
    return (ma or "").strip().upper().replace(" ", "_").replace("-", "_")


class DanhMucService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── đọc ───────────────────────────────────────────────────────────
    def _cau(self, nhom: Optional[str], gom_ca_tat: bool) -> Select:
        q = select(DanhMuc)
        if nhom:
            q = q.where(DanhMuc.nhom == nhom)
        if not gom_ca_tat:
            q = q.where(DanhMuc.is_active.is_(True))
        return q.order_by(DanhMuc.nhom, DanhMuc.thu_tu, DanhMuc.nhan)

    async def danh_sach(
        self,
        *,
        nhom: Optional[str] = None,
        gom_ca_tat: bool = False,
    ) -> list[DanhMuc]:
        """Danh mục theo nhóm. Mặc định chỉ mục còn hiệu lực.

        `gom_ca_tat=True` chỉ dùng cho màn hình quản trị — các ô chọn ngoài
        nghiệp vụ không được thấy mục đã tắt, nếu không thì tắt cũng như không.
        """
        if nhom and nhom not in NHOM_HOP_LE:
            raise LoiNghiepVu(
                "DM_NHOM_KHONG_HOP_LE",
                f"Nhóm danh mục phải thuộc {list(NHOM_HOP_LE)}", 422)
        res = await self.db.execute(self._cau(nhom, gom_ca_tat))
        return list(res.scalars().all())

    async def ma_hop_le(self, nhom: str) -> set[str]:
        """Tập mã còn hiệu lực của một nhóm — để tầng ghi kiểm tra đầu vào."""
        res = await self.db.execute(
            select(DanhMuc.ma).where(
                DanhMuc.nhom == nhom, DanhMuc.is_active.is_(True))
        )
        return {r[0] for r in res.all()}

    async def nhan_theo_ma(self, nhom: str) -> dict[str, str]:
        """Từ điển mã → nhãn, kể cả mục đã tắt.

        Dữ liệu cũ vẫn mang mã của mục đã tắt; không tra được nhãn thì màn
        hình sẽ hiện mã trần cho người dùng đọc.
        """
        res = await self.db.execute(
            select(DanhMuc.ma, DanhMuc.nhan).where(DanhMuc.nhom == nhom)
        )
        return {ma: nhan for ma, nhan in res.all()}

    async def _lay(self, dm_id: UUID) -> DanhMuc:
        dm = await self.db.get(DanhMuc, dm_id)
        if dm is None:
            raise LoiNghiepVu("DM_KHONG_TON_TAI", "Không tìm thấy mục danh mục", 404)
        return dm

    # ── đếm nơi đang dùng ─────────────────────────────────────────────
    async def dem_su_dung(self, dm: DanhMuc) -> int:
        """Số bản ghi đang mang mã này.

        Quyết định được xoá hẳn hay chỉ được tắt. Nhóm chưa gắn vào cột nào
        trả 0 — nghĩa là xoá thoải mái.
        """
        cot = COT_SU_DUNG.get(dm.nhom)
        if cot:
            # Tên cột lấy từ hằng số trong mã, không phải đầu vào người dùng.
            res = await self.db.execute(sa_text(f"""
                SELECT count(*) FROM meeting.cuoc_hop
                 WHERE {cot} = :ma AND is_deleted = false
            """), {"ma": dm.ma})
            return int(res.scalar_one())

        if dm.nhom == NHOM_LOAI_TAI_LIEU:
            # Loại tài liệu lưu ở `tai_lieu.mo_ta` dưới dạng NHÃN (bảng chưa
            # có cột riêng — xem G4.11 trong kế hoạch), nên đối chiếu nhãn.
            res = await self.db.execute(sa_text("""
                SELECT count(*) FROM meeting.tai_lieu
                 WHERE mo_ta = :nhan AND is_deleted = false
            """), {"nhan": dm.nhan})
            return int(res.scalar_one())

        if dm.nhom == NHOM_PHONG_HOP:
            # Địa điểm cũng là chuỗi tự do — đối chiếu nhãn, không phân biệt
            # hoa thường vì Văn phòng gõ tay suốt 6 tháng qua.
            res = await self.db.execute(sa_text("""
                SELECT count(*) FROM meeting.cuoc_hop
                 WHERE lower(btrim(dia_diem)) = lower(btrim(:nhan))
                   AND is_deleted = false
            """), {"nhan": dm.nhan})
            return int(res.scalar_one())

        return 0

    # ── ghi ───────────────────────────────────────────────────────────
    def _kiem_quyen(self, user: TokenPayload) -> None:
        if not la_quan_tri_lich(user):
            raise LoiNghiepVu(
                "DM_KHONG_DU_QUYEN",
                "Chỉ quản trị Lịch công tác mới sửa được danh mục", 403)

    async def tao(
        self, nhom: str, ma: str, nhan: str, user: TokenPayload,
        *, thu_tu: Optional[int] = None, mo_ta: Optional[str] = None,
    ) -> DanhMuc:
        self._kiem_quyen(user)
        if nhom not in NHOM_HOP_LE:
            raise LoiNghiepVu(
                "DM_NHOM_KHONG_HOP_LE",
                f"Nhóm danh mục phải thuộc {list(NHOM_HOP_LE)}", 422)

        ma = _chuan_ma(ma)
        if not MAU_MA.match(ma):
            raise LoiNghiepVu(
                "DM_MA_KHONG_HOP_LE",
                "Mã chỉ gồm chữ không dấu, số và gạch dưới, dài 2–50 ký tự. "
                "Tên hiển thị có dấu thì nhập ở ô Tên.", 422)
        nhan = (nhan or "").strip()
        if not nhan:
            raise LoiNghiepVu("DM_THIEU_NHAN", "Chưa nhập tên hiển thị", 422)

        trung = await self.db.execute(
            select(DanhMuc).where(DanhMuc.nhom == nhom, DanhMuc.ma == ma))
        cu = trung.scalar_one_or_none()
        if cu is not None:
            # Mã trùng với một mục ĐÃ TẮT là chuyện thường: đơn vị tắt đi rồi
            # cần lại. Bật lại đúng mục cũ thay vì báo lỗi cụt — dữ liệu cũ
            # mang mã này lập tức hiện đúng nhãn trở lại.
            if not cu.is_active:
                cu.is_active = True
                cu.nhan = nhan
                if mo_ta is not None:
                    cu.mo_ta = mo_ta
                cu.updated_by = UUID(user.sub)
                cu.updated_at = func.now()
                await self.db.flush()
                return cu
            raise LoiNghiepVu(
                "DM_MA_TRUNG",
                f"Mã “{ma}” đã có trong nhóm này", 409)

        if thu_tu is None:
            res = await self.db.execute(
                select(func.coalesce(func.max(DanhMuc.thu_tu), 0))
                .where(DanhMuc.nhom == nhom))
            thu_tu = int(res.scalar_one()) + 1

        dm = DanhMuc(
            nhom=nhom, ma=ma, nhan=nhan, thu_tu=thu_tu, mo_ta=mo_ta,
            is_active=True, he_thong=False, created_by=UUID(user.sub),
        )
        self.db.add(dm)
        await self.db.flush()
        return dm

    async def cap_nhat(
        self, dm_id: UUID, thay_doi: dict, user: TokenPayload
    ) -> DanhMuc:
        self._kiem_quyen(user)
        dm = await self._lay(dm_id)

        if "ma" in thay_doi and _chuan_ma(thay_doi["ma"]) != dm.ma:
            # Mã là thứ dữ liệu đã ghi tham chiếu tới. Đổi mã là làm mồ côi
            # toàn bộ bản ghi cũ mà không báo ai — chặn cho cả mục thường,
            # không riêng mục hệ thống.
            raise LoiNghiepVu(
                "DM_KHONG_DOI_MA",
                "Không đổi được mã sau khi tạo — dữ liệu đã ghi đang tham "
                "chiếu tới mã này. Sửa Tên hiển thị, hoặc tắt mục cũ rồi "
                "thêm mục mới.", 422)

        if "nhan" in thay_doi:
            nhan = (thay_doi["nhan"] or "").strip()
            if not nhan:
                raise LoiNghiepVu("DM_THIEU_NHAN", "Chưa nhập tên hiển thị", 422)
            dm.nhan = nhan
        if "thu_tu" in thay_doi and thay_doi["thu_tu"] is not None:
            dm.thu_tu = int(thay_doi["thu_tu"])
        if "mo_ta" in thay_doi:
            dm.mo_ta = thay_doi["mo_ta"]

        if "is_active" in thay_doi and thay_doi["is_active"] is not None:
            bat = bool(thay_doi["is_active"])
            if not bat and dm.he_thong:
                raise LoiNghiepVu(
                    "DM_MUC_HE_THONG",
                    f"“{dm.nhan}” là mục hệ thống — phần mềm đang chạy theo "
                    "mã này nên không tắt được. Đổi tên hiển thị thì được.",
                    422)
            dm.is_active = bat

        dm.updated_by = UUID(user.sub)
        dm.updated_at = func.now()
        await self.db.flush()
        return dm

    async def xoa(self, dm_id: UUID, user: TokenPayload) -> dict:
        """Xoá hẳn nếu chưa ai dùng; đang dùng thì chỉ được tắt."""
        self._kiem_quyen(user)
        dm = await self._lay(dm_id)

        if dm.he_thong:
            raise LoiNghiepVu(
                "DM_MUC_HE_THONG",
                f"“{dm.nhan}” là mục hệ thống — phần mềm đang chạy theo mã "
                "này nên không xoá được.", 422)

        dang_dung = await self.dem_su_dung(dm)
        if dang_dung > 0:
            raise LoiNghiepVu(
                "DM_DANG_SU_DUNG",
                f"Còn {dang_dung} bản ghi đang dùng “{dm.nhan}”. Xoá đi là "
                "những bản ghi đó mất cách hiển thị. Hãy TẮT mục này thay vì "
                "xoá — dữ liệu cũ giữ nguyên, chỉ không chọn mới được nữa.",
                409)

        await self.db.delete(dm)
        await self.db.flush()
        return {"id": str(dm_id), "da_xoa": True}

    async def sap_xep(self, thu_tu_moi: Sequence[dict], user: TokenPayload) -> int:
        """Đặt lại thứ tự cả nhóm trong một lượt. Trả số mục đã đổi."""
        self._kiem_quyen(user)
        n = 0
        for muc in thu_tu_moi:
            dm = await self._lay(UUID(str(muc["id"])))
            moi = int(muc["thu_tu"])
            if dm.thu_tu != moi:
                dm.thu_tu = moi
                dm.updated_by = UUID(user.sub)
                dm.updated_at = func.now()
                n += 1
        await self.db.flush()
        return n
