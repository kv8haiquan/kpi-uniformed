"""
danh_gia_service.py
====================
Chấm sao công tác chuẩn bị cuộc họp — G5.3, thay `MEETING_RATING` của lichkv8.

Ai được chấm: lãnh đạo Chi cục (Chi cục trưởng, Phó Chi cục trưởng) và quản
trị hệ thống. Đây là quyền THAY chứ không port: `canRateMeetingPrep_` (Mã.gs
dòng 2937) ghép họ tên + chức vụ + tên đăng nhập thành một chuỗi rồi dò
"lanh dao chi cuc" — ai có chức vụ ghi kiểu khác là mất quyền, mà ai tên
trùng cụm đó lại được. Ở đây dùng `vai_tro` khoá ngoại.

Chánh Văn phòng KHÔNG nằm trong nhóm được chấm dù là quản trị lịch: điểm này
chấm chính công tác chuẩn bị của Văn phòng, tự chấm mình thì con số vô nghĩa.

Ai được XEM: tất cả. Giữ đúng hành vi cũ (`publicPrepRating` hiện cho mọi
người ở chế độ chỉ đọc) — điểm chuẩn bị là lời nhắc cho đơn vị chuẩn bị chứ
không phải hồ sơ kín.

Mỗi người một điểm cho một cuộc họp; chấm lại là ghi đè, ràng buộc bằng
`uq_danh_gia_cuoc_hop_nguoi` chứ không phải bằng câu lệnh.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models.base import CongChucRef as CongChuc
from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.models.lich_cong_tac import DanhGiaCuocHop
from meeting_service.services.audit_log_service import ghi_audit
from meeting_service.services.lich_cong_tac_service import LoiNghiepVu
from shared.auth import TokenPayload

DIEM_MIN, DIEM_MAX = 1, 5

# Khớp CHECK `ck_danh_gia_diem` (diem BETWEEN 1 AND 5). Lệch là 500 thay vì
# một thông báo tử tế.
DIEM_HOP_LE = range(DIEM_MIN, DIEM_MAX + 1)

# Mã vai trò cùng nghĩa "lãnh đạo Chi cục" — CSDL dùng mã ngắn, một vài chỗ
# trong hệ cũ dùng mã dài, nhận cả hai cho khỏi mất quyền vì lệch chính tả.
VAI_TRO_LANH_DAO_CHI_CUC = {
    "CCT", "CHI_CUC_TRUONG", "PCCT", "PHO_CHI_CUC_TRUONG",
}
VAI_TRO_QUAN_TRI = {"ADMIN", "SUPER_ADMIN"}


def duoc_cham_diem(user: TokenPayload) -> bool:
    return bool(
        user.is_admin
        or user.vai_tro in VAI_TRO_QUAN_TRI
        or user.vai_tro in VAI_TRO_LANH_DAO_CHI_CUC
    )


class DanhGiaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _lay_cuoc_hop(self, cuoc_hop_id: UUID) -> CuocHop:
        ch = await self.db.get(CuocHop, cuoc_hop_id)
        if ch is None or ch.is_deleted:
            raise LoiNghiepVu("MEETING_NOT_FOUND",
                              "Không tìm thấy cuộc họp", 404)
        return ch

    # ── xem ───────────────────────────────────────────────────────────

    async def cua_cuoc_hop(self, cuoc_hop_id: UUID,
                           user: TokenPayload) -> dict:
        await self._lay_cuoc_hop(cuoc_hop_id)
        toi = UUID(user.sub)

        rows = (await self.db.execute(
            select(DanhGiaCuocHop, CongChuc.ho_ten, CongChuc.chuc_vu)
            .join(CongChuc, CongChuc.id == DanhGiaCuocHop.cong_chuc_id)
            .where(DanhGiaCuocHop.cuoc_hop_id == cuoc_hop_id)
            .order_by(DanhGiaCuocHop.updated_at.desc()))).all()

        danh_sach = [
            {"id": d.id, "cong_chuc_id": d.cong_chuc_id, "ho_ten": ho_ten,
             "chuc_vu": chuc_vu, "diem": d.diem, "ghi_chu": d.ghi_chu,
             "la_cua_toi": d.cong_chuc_id == toi,
             "created_at": d.created_at, "updated_at": d.updated_at}
            for d, ho_ten, chuc_vu in rows]

        cua_toi = next((x for x in danh_sach if x["la_cua_toi"]), None)
        diem = [x["diem"] for x in danh_sach]
        return {
            "cuoc_hop_id": cuoc_hop_id,
            "duoc_cham": duoc_cham_diem(user),
            "diem_cua_toi": cua_toi["diem"] if cua_toi else None,
            "ghi_chu_cua_toi": cua_toi["ghi_chu"] if cua_toi else None,
            "so_luot": len(diem),
            "diem_tb": round(sum(diem) / len(diem), 2) if diem else None,
            "danh_sach": danh_sach,
        }

    # ── chấm ──────────────────────────────────────────────────────────

    async def cham(
        self, cuoc_hop_id: UUID, diem: int, ghi_chu: Optional[str],
        user: TokenPayload,
    ) -> dict:
        if not duoc_cham_diem(user):
            raise LoiNghiepVu(
                "RATE_FORBIDDEN",
                "Chỉ lãnh đạo Chi cục và quản trị hệ thống được chấm điểm "
                "công tác chuẩn bị", 403)
        if diem not in DIEM_HOP_LE:
            raise LoiNghiepVu("RATE_BAD_SCORE",
                              f"Điểm phải từ {DIEM_MIN} đến {DIEM_MAX} sao")

        ch = await self._lay_cuoc_hop(cuoc_hop_id)
        toi = UUID(user.sub)

        dg = await self.db.scalar(
            select(DanhGiaCuocHop).where(
                DanhGiaCuocHop.cuoc_hop_id == cuoc_hop_id,
                DanhGiaCuocHop.cong_chuc_id == toi))
        diem_cu = dg.diem if dg else None

        if dg is None:
            dg = DanhGiaCuocHop(cuoc_hop_id=cuoc_hop_id, cong_chuc_id=toi,
                                diem=diem, ghi_chu=ghi_chu)
            self.db.add(dg)
        else:
            dg.diem = diem
            dg.ghi_chu = ghi_chu
            dg.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

        await ghi_audit(
            self.db, hanh_dong="CHAM_DIEM_CHUAN_BI",
            nguoi_thuc_hien_id=toi,
            doi_tuong_loai="cuoc_hop", doi_tuong_id=cuoc_hop_id,
            chi_tiet={"ma_lich": ch.ma_lich, "diem": diem,
                      "diem_cu": diem_cu, "co_ghi_chu": bool(ghi_chu)})
        return await self.cua_cuoc_hop(cuoc_hop_id, user)

    async def bo_cham(self, cuoc_hop_id: UUID, user: TokenPayload) -> dict:
        """Rút lại điểm của chính mình. Không ai xoá được điểm người khác."""
        dg = await self.db.scalar(
            select(DanhGiaCuocHop).where(
                DanhGiaCuocHop.cuoc_hop_id == cuoc_hop_id,
                DanhGiaCuocHop.cong_chuc_id == UUID(user.sub)))
        if dg is None:
            raise LoiNghiepVu("RATE_NOT_FOUND",
                              "Bạn chưa chấm điểm cuộc họp này", 404)
        diem_cu = dg.diem
        await self.db.delete(dg)
        await self.db.flush()
        await ghi_audit(
            self.db, hanh_dong="BO_CHAM_DIEM_CHUAN_BI",
            nguoi_thuc_hien_id=UUID(user.sub),
            doi_tuong_loai="cuoc_hop", doi_tuong_id=cuoc_hop_id,
            chi_tiet={"diem_cu": diem_cu})
        return await self.cua_cuoc_hop(cuoc_hop_id, user)

    # ── tổng hợp ──────────────────────────────────────────────────────

    async def tong_hop(self, tu_ngay=None, den_ngay=None,
                       gioi_han: int = 200) -> dict:
        """Các cuộc họp đã có điểm, kèm điểm trung bình theo đơn vị chuẩn bị.

        Đây là lý do tồn tại của tính năng: 102 lượt chấm mang từ hệ cũ sang
        chỉ có ý nghĩa khi đọc được thành "đơn vị nào chuẩn bị đều tay".
        """
        dk = []
        if tu_ngay:
            dk.append(CuocHop.ngay_hien_thi >= tu_ngay)
        if den_ngay:
            dk.append(CuocHop.ngay_hien_thi <= den_ngay)

        q = (select(CuocHop.id, CuocHop.ma_lich, CuocHop.tieu_de,
                    CuocHop.ngay_hien_thi, CuocHop.don_vi_chuan_bi,
                    func.avg(DanhGiaCuocHop.diem).label("diem_tb"),
                    func.count().label("so_luot"))
             .join(DanhGiaCuocHop, DanhGiaCuocHop.cuoc_hop_id == CuocHop.id)
             .where(CuocHop.is_deleted.is_(False), *dk)
             .group_by(CuocHop.id, CuocHop.ma_lich, CuocHop.tieu_de,
                       CuocHop.ngay_hien_thi, CuocHop.don_vi_chuan_bi)
             .order_by(CuocHop.ngay_hien_thi.desc().nullslast())
             .limit(gioi_han))
        dong = [
            {"cuoc_hop_id": i, "ma_lich": ml, "tieu_de": td, "ngay": ng,
             "don_vi_chuan_bi": dv, "diem_tb": round(float(tb), 2),
             "so_luot": n}
            for i, ml, td, ng, dv, tb, n in (await self.db.execute(q)).all()]

        theo_don_vi: dict[str, dict] = {}
        for d in dong:
            k = d["don_vi_chuan_bi"] or "(Không ghi đơn vị chuẩn bị)"
            o = theo_don_vi.setdefault(k, {"don_vi": k, "so_cuoc_hop": 0,
                                           "_tong": 0.0})
            o["so_cuoc_hop"] += 1
            o["_tong"] += d["diem_tb"]
        bang = sorted(
            ({"don_vi": o["don_vi"], "so_cuoc_hop": o["so_cuoc_hop"],
              "diem_tb": round(o["_tong"] / o["so_cuoc_hop"], 2)}
             for o in theo_don_vi.values()),
            key=lambda x: (-x["so_cuoc_hop"], x["don_vi"]))

        tong_luot = sum(d["so_luot"] for d in dong)
        return {
            "so_cuoc_hop": len(dong),
            "so_luot": tong_luot,
            "diem_tb": (round(sum(d["diem_tb"] * d["so_luot"] for d in dong)
                              / tong_luot, 2) if tong_luot else None),
            "theo_don_vi": bang,
            "cuoc_hop": dong,
        }
