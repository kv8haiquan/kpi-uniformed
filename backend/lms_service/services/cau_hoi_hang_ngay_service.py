"""
lms_service/services/cau_hoi_hang_ngay_service.py
=================================================
Business logic cau hoi DGNL phat hang ngay cho chatbot Zalo.

Hai viec chinh:
  1. Chot cau hoi cua ngay (boc ngau nhien 1 lan roi ghi lai, khong boc lai)
  2. Tra dap an cua mot cau DA PHAT (khong cho tra cau chua phat)

Gioi han cua Zalo duoc ma hoa thanh hang so o duoi — vuot la tin bi tu choi.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.config import settings
from lms_service.core.timezone import now_vn
from lms_service.models.cau_hoi_dgnl import CauHoiDgnl
from lms_service.models.cau_hoi_hang_ngay import CauHoiHangNgay
from lms_service.models.linh_vuc import LinhVuc

# ---------------------------------------------------------------------------
# Gioi han cua Zalo OA (nguon: tai lieu tin tu van dang button)
#   - text cua tin nhan: toi da 2.000 ky tu
#   - title cua nut:     toi da   100 ky tu
#   - payload cua nut:   toi da 1.000 ky tu
# ---------------------------------------------------------------------------
ZALO_MAX_TEXT = 2000
ZALO_MAX_BUTTON_TITLE = 100

# Chi phat cac loai bot cham duoc bang nut bam 1 lua chon.
# TU_LUAN va TRAC_NGHIEM_NHIEU khong hop voi luong bam 1 nut.
LOAI_PHAT_DUOC = ("TRAC_NGHIEM_1", "DUNG_SAI")

# Tien to payload nut — webhook loc theo tien to nay de biet la cua tinh nang
# nay, khong dinh vao cac kich ban chatbot khac.
TIEN_TO_PAYLOAD = "DGNL"


class CauHoiHangNgayService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================================================================
    # CHOT CAU HOI CUA NGAY
    # ==================================================================

    async def lay_cau_hoi(self, ngay: Optional[date] = None) -> dict:
        """Tra ve cau hoi cua `ngay` (mac dinh hom nay theo gio VN).

        Lan goi dau trong ngay se boc va CHOT lai; cac lan sau tra dung cau do.
        """
        ngay = ngay or now_vn().date()

        da_chot = await self._doc_ban_ghi(ngay)
        if da_chot is None:
            await self._chot_cau_cho_ngay(ngay)
            da_chot = await self._doc_ban_ghi(ngay)

        if da_chot is None:
            # Chi xay ra khi ngan hang rong hoan toan
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {
                        "code": "DGNL_001",
                        "message": "Chưa có câu hỏi nào khả dụng trong 9 lĩnh vực",
                    },
                },
            )
        return da_chot

    async def _doc_ban_ghi(self, ngay: date) -> Optional[dict]:
        """Doc cau hoi da chot cho ngay, kem ten linh vuc. None neu chua chot."""
        stmt = (
            select(CauHoiHangNgay.ngay, CauHoiDgnl, LinhVuc)
            .join(CauHoiDgnl, CauHoiHangNgay.cau_hoi_id == CauHoiDgnl.id)
            .join(LinhVuc, CauHoiDgnl.linh_vuc_id == LinhVuc.id)
            .where(CauHoiHangNgay.ngay == ngay)
        )
        row = (await self.db.execute(stmt)).first()
        if row is None:
            return None
        return self._dung_ket_qua(row[0], row[1], row[2])

    async def _chot_cau_cho_ngay(self, ngay: date) -> None:
        """Boc 1 cau chua tung phat roi ghi vao bang.

        ON CONFLICT DO NOTHING: hai tien trinh goi cung luc thi chi mot ban ghi
        song sot, ca hai deu doc lai duoc dung cau do.
        """
        cau_hoi_id = await self._boc_cau_chua_phat()
        if cau_hoi_id is None:
            cau_hoi_id = await self._boc_cau_cu_nhat()
        if cau_hoi_id is None:
            return

        await self.db.execute(
            pg_insert(CauHoiHangNgay.__table__)
            .values(ngay=ngay, cau_hoi_id=cau_hoi_id)
            .on_conflict_do_nothing(index_elements=["ngay"])
        )
        await self.db.commit()

    def _pool_where(self) -> list:
        """Dieu kien loc kho cau hoi duoc phep phat."""
        return [
            CauHoiDgnl.is_active == True,  # noqa: E712
            CauHoiDgnl.loai.in_(LOAI_PHAT_DUOC),
            LinhVuc.ma_linh_vuc.in_(settings.dgnl_daily_linh_vuc_list),
        ]

    async def _boc_cau_chua_phat(self) -> Optional[uuid.UUID]:
        """Boc ngau nhien 1 cau CHUA TUNG phat ngay nao."""
        da_phat = select(CauHoiHangNgay.cau_hoi_id)
        stmt = (
            select(CauHoiDgnl.id)
            .join(LinhVuc, CauHoiDgnl.linh_vuc_id == LinhVuc.id)
            .where(*self._pool_where(), CauHoiDgnl.id.notin_(da_phat))
            .order_by(func.random())
            .limit(1)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def _boc_cau_cu_nhat(self) -> Optional[uuid.UUID]:
        """Het cau moi thi vong lai cau da phat LAU NHAT.

        Voi 1.207 cau trong 9 linh vuc thi phai hon 3 nam moi cham nhanh nay.
        """
        lan_cuoi = (
            select(
                CauHoiHangNgay.cau_hoi_id.label("cid"),
                func.max(CauHoiHangNgay.ngay).label("lan_cuoi"),
            )
            .group_by(CauHoiHangNgay.cau_hoi_id)
            .subquery()
        )
        stmt = (
            select(CauHoiDgnl.id)
            .join(LinhVuc, CauHoiDgnl.linh_vuc_id == LinhVuc.id)
            .outerjoin(lan_cuoi, lan_cuoi.c.cid == CauHoiDgnl.id)
            .where(*self._pool_where())
            .order_by(lan_cuoi.c.lan_cuoi.asc().nullsfirst(), func.random())
            .limit(1)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    # ==================================================================
    # DAP AN
    # ==================================================================

    @staticmethod
    def _chuan_hoa_chon(chon: Optional[str]) -> Optional[str]:
        """Lay ra dung mot ky tu phuong an tu thu nguoi dung go.

        Nguoi dung Zalo may tinh khong thay nut nen phai go tay: "a", "A.",
        "(B)", "c " ... deu phai hieu duoc. Bo het ky tu khong phai chu/so roi
        lay ky tu dau.
        """
        if not chon:
            return None
        # Neu kich ban chuyen nguyen payload nut "DGNL|<id>|A" thi lay doan
        # cuoi. Khong co nhanh nay thi ky tu dau se ra "D" — cham sai het.
        if "|" in chon:
            chon = chon.rsplit("|", 1)[-1]
        sach = "".join(c for c in chon if c.isalnum()).upper()
        return sach[0] if sach else None

    async def lay_dap_an(
        self,
        cau_hoi_id: Optional[uuid.UUID] = None,
        chon: Optional[str] = None,
    ) -> dict:
        """Tra dap an dung cua mot cau ĐÃ PHAT.

        `cau_hoi_id` de trong -> lay cau PHAT GAN NHAT. Duong nay danh cho
        nguoi go tay "A"/"B" tren Zalo may tinh: kich ban chatbot chi bat duoc
        chu cai, khong co cach nao biet cau_hoi_id.
        Dung "phat gan nhat" chu khong phai "hom nay" de khong hong khi nguoi
        ta tra loi luc qua nua dem, hoac khi hom nay chua ai goi lay cau hoi.

        Chan chinh o day: cau chua tung phat thi tra 404. Nho vay du lo khoa
        bot thi nguoi cam khoa cung chi xem duoc nhung cau da gui ra ngoai,
        khong moc duoc ca ngan hang de thi.
        """
        stmt = (
            select(CauHoiHangNgay.ngay, CauHoiDgnl)
            .join(CauHoiDgnl, CauHoiHangNgay.cau_hoi_id == CauHoiDgnl.id)
            .order_by(CauHoiHangNgay.ngay.desc())
            .limit(1)
        )
        if cau_hoi_id is not None:
            stmt = stmt.where(CauHoiHangNgay.cau_hoi_id == cau_hoi_id)
        row = (await self.db.execute(stmt)).first()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {
                        "code": "DGNL_002",
                        "message": "Câu hỏi không tồn tại hoặc chưa từng được phát",
                    },
                },
            )

        ngay, ch = row[0], row[1]
        dap_an = ch.dap_an or {}
        dung_key = str(dap_an.get("dap_an_dung") or "")
        lua_chon = dap_an.get("lua_chon") or []
        dung_noi_dung = next(
            (lc.get("noi_dung", "") for lc in lua_chon if lc.get("key") == dung_key),
            "",
        )

        da_chon = self._chuan_hoa_chon(chon)
        la_dung = (da_chon == dung_key) if da_chon else None

        return {
            "ngay": ngay,
            "cau_hoi_id": ch.id,
            "dap_an_dung": dung_key,
            "dap_an_dung_noi_dung": dung_noi_dung,
            "giai_thich": ch.giai_thich,
            "da_chon": da_chon,
            "dung": la_dung,
            "text_zalo": self._text_dap_an(
                dung_key, dung_noi_dung, ch.giai_thich, da_chon, la_dung
            ),
        }

    # ==================================================================
    # DUNG KET QUA + DINH DANG
    # ==================================================================

    def _dung_ket_qua(self, ngay: date, ch: CauHoiDgnl, lv: LinhVuc) -> dict:
        dap_an = ch.dap_an or {}
        lua_chon = [
            {"key": str(lc.get("key", "")), "noi_dung": str(lc.get("noi_dung", ""))}
            for lc in (dap_an.get("lua_chon") or [])
        ]
        return {
            "ngay": ngay,
            "cau_hoi_id": ch.id,
            "linh_vuc_ma": lv.ma_linh_vuc,
            "linh_vuc_ten": lv.ten_linh_vuc,
            "loai": ch.loai,
            "do_kho": ch.do_kho,
            "noi_dung": ch.noi_dung,
            "lua_chon": lua_chon,
            "text_zalo": self._text_cau_hoi(ngay, lv, ch.noi_dung, lua_chon),
        }

    @staticmethod
    def _cat(s: str, gioi_han: int) -> str:
        """Cat chuoi cho vua gioi han cua Zalo, co dau … de biet la da cat."""
        s = s or ""
        return s if len(s) <= gioi_han else s[: gioi_han - 1].rstrip() + "…"

    def _text_cau_hoi(
        self, ngay: date, lv: LinhVuc, noi_dung: str, lua_chon: list[dict]
    ) -> str:
        dong = [
            f"📚 CÂU HỎI ĐGNL NGÀY {ngay.strftime('%d/%m/%Y')}",
            f"Lĩnh vực: {lv.ten_linh_vuc}",
            "",
            noi_dung,
            "",
        ]
        dong += [f"{lc['key']}. {lc['noi_dung']}" for lc in lua_chon]
        # Zalo may tinh KHONG hien nut bam (han che cua Zalo, khong sua duoc
        # tu phia minh) — nen luon chi them duong go tay, chay o moi nen tang.
        dong += ["", "👇 Bấm nút bên dưới, hoặc nhắn A/B/C/D nếu bạn dùng Zalo máy tính"]
        return self._cat("\n".join(dong), ZALO_MAX_TEXT)

    def _text_dap_an(
        self,
        dung_key: str,
        dung_noi_dung: str,
        giai_thich: Optional[str],
        da_chon: Optional[str],
        la_dung: Optional[bool],
    ) -> str:
        dong: list[str] = []
        if la_dung is True:
            dong.append(f"✅ Chính xác! Đáp án đúng là {dung_key}.")
        elif la_dung is False:
            dong.append(f"❌ Chưa đúng. Bạn chọn {da_chon}, đáp án đúng là {dung_key}.")
        else:
            dong.append(f"💡 Đáp án đúng: {dung_key}.")

        if dung_noi_dung:
            dong.append(dung_noi_dung)
        if giai_thich:
            dong += ["", f"📖 Giải thích: {giai_thich}"]
        return self._cat("\n".join(dong), ZALO_MAX_TEXT)

    # ==================================================================
    # DINH DANG ZALO — object `message` de khoi dong chatbot dung thang
    # ==================================================================
    #
    # Endpoint mau cua Zalo (https://chatbot.zalo.me/json-api?option=V_OPENAPI)
    # tra ve {"text": "..."} — dung hinh dang object `message` cua OA. Phan
    # `attachment` duoi day dung theo dinh dang tin tu van dang button.
    #
    # ⚠️ CHUA DOI CHUNG bang khoi dong that. Neu "Test the Request" bao sai
    # dinh dang thi CHI sua hai ham nay, khong dung den phan con lai.

    def zalo_cau_hoi(self, kq: dict) -> dict:
        """Doi ket qua cau hoi -> object message Zalo kem nut chon dap an."""
        nut = []
        for lc in kq["lua_chon"]:
            nut.append(
                {
                    # Chi dat chu cai: noi dung phuong an da nam o than tin roi,
                    # lap lai lan hai lam khung chat dai gap doi.
                    "title": self._cat(lc["key"], ZALO_MAX_BUTTON_TITLE),
                    "type": "oa.query.hide",
                    # Payload CHI la chu cai, co y. Zalo may tinh khong hien nut
                    # nen phai co duong go tay, ma quy tac chatbot bat theo tu
                    # khoa: de payload la "DGNL|<id>|A" thi cu bam nut se KHONG
                    # khop tu khoa "A", thanh ra phai dung hai quy tac rieng cho
                    # hai duong. De tro lai chu cai thi mot quy tac lo ca hai.
                    #
                    # Danh doi: mat `cau_hoi_id` nen nguoi tra loi sau nua dem bi
                    # cham theo cau moi. Chap nhan duoc — duong go tay von da vay.
                    # Neu sau nay tu viet webhook (khong con phu thuoc quy tac
                    # chatbot) thi doi lai thanh f"{TIEN_TO_PAYLOAD}|{id}|{key}";
                    # `_chuan_hoa_chon` doc duoc ca hai dang.
                    "payload": {"content": lc["key"]},
                }
            )
        return {
            "text": kq["text_zalo"],
            "attachment": {"type": "template", "payload": {"buttons": nut}},
        }

    def zalo_dap_an(self, kq: dict) -> dict:
        """Doi ket qua dap an -> object message Zalo (chi text, khong nut)."""
        return {"text": kq["text_zalo"]}
