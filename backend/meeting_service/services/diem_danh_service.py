"""
diem_danh_service.py
=====================
Business logic Module 4 — Điểm danh.

QR token: JWT short-lived TTL=1h, sub=cuoc_hop_id, purpose='qr_diem_danh'.
Khi CBCC quét QR → POST /quet với token → backend verify + insert diem_danh.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.models.diem_danh import DiemDanh
from meeting_service.models.thanh_phan import ThanhPhan
from meeting_service.schemas.diem_danh import BamTayBulk, BamTayItem
from meeting_service.services.audit_log_service import ghi_audit
from meeting_service.services.short_lived_token import (
    PURPOSE_QR_DIEM_DANH,
    issue_token,
    verify_token,
)
from shared.auth import TokenPayload


# ──────────────────────────────────────────────────────────────────────
# CHECKIN WINDOW POLICY (G4-fix-7)
# ──────────────────────────────────────────────────────────────────────
# Window mở: gio_bat_dau − OPEN_BEFORE → gio_ket_thuc + CLOSE_AFTER
# (nếu thiếu gio_ket_thuc → fallback gio_bat_dau + DEFAULT_DURATION)
#
# Threshold "đến muộn" — sau giờ bắt đầu N phút thì ghi DEN_MUON.
# Trước window → 409 NOT_YET_OPEN. Sau window → 409 CHECKIN_CLOSED.

LATE_THRESHOLD_MINUTES = 5
CHECKIN_OPEN_BEFORE_MINUTES = 30
CHECKIN_CLOSE_AFTER_MINUTES = 60
DEFAULT_DURATION_MINUTES = 240  # 4h fallback nếu không có gio_ket_thuc


class DiemDanhService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ──────────────────────────────────────────────────────────────────
    # QR TOKEN (Chủ tọa/Thư ký bấm sinh — CBCC quét)
    # ──────────────────────────────────────────────────────────────────
    def issue_qr_token(self, cuoc_hop_id: UUID, ttl_seconds: int = 3600) -> dict:
        token = issue_token(
            purpose=PURPOSE_QR_DIEM_DANH,
            subject=str(cuoc_hop_id),
            ttl_seconds=ttl_seconds,
        )
        return {
            "token": token,
            "qr_url": f"/hop-khong-giay/diem-danh-qr?token={token}",
            "expires_in_seconds": ttl_seconds,
        }

    # ──────────────────────────────────────────────────────────────────
    # QR SUBMIT
    # ──────────────────────────────────────────────────────────────────
    async def submit_qr(self, token: str, user: TokenPayload) -> DiemDanh:
        payload = verify_token(token, expected_purpose=PURPOSE_QR_DIEM_DANH)
        try:
            cuoc_hop_id = UUID(payload["sub"])
        except (KeyError, ValueError):
            raise HTTPException(
                status_code=401,
                detail={"success": False, "error": {"code": "TOKEN_INVALID",
                        "message": "Token không hợp lệ"}},
            )

        ch = await self._get_cuoc_hop(cuoc_hop_id)

        # G4-fix-5: chặn quét QR cho cuộc họp đã hủy
        if ch.trang_thai == "HUY":
            raise HTTPException(
                status_code=409,
                detail={"success": False, "error": {"code": "MEETING_CANCELLED",
                        "message": "Cuộc họp đã hủy — không thể điểm danh"}},
            )

        # CBCC phải có trong thành phần (check TRƯỚC window — outsider không
        # leak info về thời gian)
        user_id = UUID(user.sub)
        result = await self.db.execute(
            select(ThanhPhan.id).where(
                ThanhPhan.cuoc_hop_id == cuoc_hop_id,
                ThanhPhan.cong_chuc_id == user_id,
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=403,
                detail={"success": False, "error": {"code": "NOT_INVITED",
                        "message": "Bạn không có trong danh sách mời"}},
            )

        # Idempotent
        result = await self.db.execute(
            select(DiemDanh).where(
                DiemDanh.cuoc_hop_id == cuoc_hop_id,
                DiemDanh.cong_chuc_id == user_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail={"success": False, "error": {"code": "ALREADY_CHECKED_IN",
                        "message": "Bạn đã điểm danh cuộc họp này"}},
            )

        # G4-fix-7: window check sau khi pass invited + idempotent
        self._check_checkin_window(ch)

        now = datetime.now()  # naive local
        trang_thai = self._compute_trang_thai(ch, now)

        dd = DiemDanh(
            cuoc_hop_id=cuoc_hop_id,
            cong_chuc_id=user_id,
            hinh_thuc="QR",
            trang_thai=trang_thai,
            gio_diem_danh=now,
        )
        self.db.add(dd)
        await self.db.flush()

        await ghi_audit(
            self.db,
            hanh_dong="CHECKIN_QR",
            nguoi_thuc_hien_id=user_id,
            doi_tuong_loai="diem_danh",
            doi_tuong_id=dd.id,
            chi_tiet={
                "cuoc_hop_id": str(cuoc_hop_id),
                "trang_thai": trang_thai,
            },
        )
        await self.db.flush()
        return dd

    # ──────────────────────────────────────────────────────────────────
    # BẤM TAY
    # ──────────────────────────────────────────────────────────────────
    async def bam_tay(
        self, payload: BamTayBulk, user: TokenPayload
    ) -> list[DiemDanh]:
        ch = await self._get_cuoc_hop(payload.cuoc_hop_id)
        nguoi_diem_danh_id = UUID(user.sub)

        results: list[DiemDanh] = []
        # Nhật ký từng người, để audit truy được "ai đổi trạng thái của ai".
        # meeting.diem_danh KHÔNG có updated_at và nguoi_diem_danh_id bị ghi đè
        # mỗi lần sửa, nên không ghi ở đây là mất dấu vĩnh viễn.
        thay_doi: list[dict] = []
        for item in payload.diem_danh:
            # Verify thành phần
            res = await self.db.execute(
                select(ThanhPhan.id).where(
                    ThanhPhan.cuoc_hop_id == ch.id,
                    ThanhPhan.cong_chuc_id == item.cong_chuc_id,
                )
            )
            if res.scalar_one_or_none() is None:
                # Skip CBCC ngoài thành phần (không raise — cho phép thư ký
                # bỏ qua người không hợp lệ trong batch)
                continue

            # Check duplicate
            res = await self.db.execute(
                select(DiemDanh).where(
                    DiemDanh.cuoc_hop_id == ch.id,
                    DiemDanh.cong_chuc_id == item.cong_chuc_id,
                )
            )
            existing = res.scalar_one_or_none()
            if existing is not None:
                # Update existing (cho phép thay đổi trạng thái)
                thay_doi.append({
                    "cong_chuc_id": str(item.cong_chuc_id),
                    "tu": existing.trang_thai,
                    "den": item.trang_thai,
                })
                existing.trang_thai = item.trang_thai
                # ghi_chu=None nghĩa là GIỮ NGUYÊN, "" nghĩa là XOÁ TRẮNG.
                # Trước đây gán thẳng nên payload không kèm ghi_chu sẽ xoá mất
                # lý do vắng mà thư ký đã nhập ở lần chấm trước.
                if item.ghi_chu is not None:
                    existing.ghi_chu = item.ghi_chu
                existing.nguoi_diem_danh_id = nguoi_diem_danh_id
                results.append(existing)
                continue

            # Mốc tuyệt đối (aware UTC). Cột gio_diem_danh là TIMESTAMPTZ nên
            # dạng này đúng kể cả khi TimeZone của session DB đổi sang UTC —
            # bền hơn datetime.now() naive mà submit_qr/tu_diem_danh đang dùng.
            now = datetime.now(timezone.utc)
            dd = DiemDanh(
                cuoc_hop_id=ch.id,
                cong_chuc_id=item.cong_chuc_id,
                hinh_thuc="BAM_TAY",
                trang_thai=item.trang_thai,
                gio_diem_danh=now,
                ghi_chu=item.ghi_chu,
                nguoi_diem_danh_id=nguoi_diem_danh_id,
            )
            self.db.add(dd)
            results.append(dd)
            thay_doi.append({
                "cong_chuc_id": str(item.cong_chuc_id),
                "tu": None,
                "den": item.trang_thai,
            })

        await self.db.flush()

        await ghi_audit(
            self.db,
            hanh_dong="CHECKIN_MANUAL",
            nguoi_thuc_hien_id=nguoi_diem_danh_id,
            doi_tuong_loai="cuoc_hop",
            doi_tuong_id=ch.id,
            chi_tiet={
                "cuoc_hop_id": str(ch.id),
                "so_diem_danh": len(results),
                "thay_doi": thay_doi,
            },
        )
        await self.db.flush()
        return results

    # ──────────────────────────────────────────────────────────────────
    # SELF CHECKIN — CBCC tự điểm danh từ máy tính (G4-fix-6.2)
    # ──────────────────────────────────────────────────────────────────
    async def tu_diem_danh(
        self, cuoc_hop_id: UUID, user: TokenPayload
    ) -> DiemDanh:
        """CBCC tự click "Tôi có mặt" trong app — không cần quét QR."""
        ch = await self._get_cuoc_hop(cuoc_hop_id)

        if ch.trang_thai == "HUY":
            raise HTTPException(
                status_code=409,
                detail={"success": False, "error": {"code": "MEETING_CANCELLED",
                        "message": "Cuộc họp đã hủy — không thể điểm danh"}},
            )

        user_id = UUID(user.sub)

        # CBCC phải có trong thành phần (TRƯỚC window check)
        result = await self.db.execute(
            select(ThanhPhan.id).where(
                ThanhPhan.cuoc_hop_id == cuoc_hop_id,
                ThanhPhan.cong_chuc_id == user_id,
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=403,
                detail={"success": False, "error": {"code": "NOT_INVITED",
                        "message": "Bạn không có trong danh sách mời"}},
            )

        # Idempotent
        result = await self.db.execute(
            select(DiemDanh).where(
                DiemDanh.cuoc_hop_id == cuoc_hop_id,
                DiemDanh.cong_chuc_id == user_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail={"success": False, "error": {"code": "ALREADY_CHECKED_IN",
                        "message": "Bạn đã điểm danh cuộc họp này"}},
            )

        # G4-fix-7: window check sau khi pass invited + idempotent
        self._check_checkin_window(ch)

        now = datetime.now()  # naive local
        trang_thai = self._compute_trang_thai(ch, now)

        dd = DiemDanh(
            cuoc_hop_id=cuoc_hop_id,
            cong_chuc_id=user_id,
            hinh_thuc="TU_DIEM_DANH",
            trang_thai=trang_thai,
            gio_diem_danh=now,
        )
        self.db.add(dd)
        await self.db.flush()

        await ghi_audit(
            self.db,
            hanh_dong="CHECKIN_SELF",
            nguoi_thuc_hien_id=user_id,
            doi_tuong_loai="diem_danh",
            doi_tuong_id=dd.id,
            chi_tiet={"cuoc_hop_id": str(cuoc_hop_id), "trang_thai": trang_thai},
        )
        await self.db.flush()
        return dd

    # ──────────────────────────────────────────────────────────────────
    # MY CHECKIN STATUS (cho FE biết button "Tôi có mặt" hiện hay không)
    # ──────────────────────────────────────────────────────────────────
    async def my_status(self, cuoc_hop_id: UUID, user: TokenPayload) -> dict:
        """Trả về trạng thái điểm danh của user hiện tại + flag is_invited
        + window info để FE pre-compute "Chưa đến giờ"."""
        user_id = UUID(user.sub)

        ch = await self._get_cuoc_hop(cuoc_hop_id)

        # Invited?
        invited_res = await self.db.execute(
            select(ThanhPhan.id).where(
                ThanhPhan.cuoc_hop_id == cuoc_hop_id,
                ThanhPhan.cong_chuc_id == user_id,
            )
        )
        is_invited = invited_res.scalar_one_or_none() is not None

        # Đã điểm danh?
        dd_res = await self.db.execute(
            select(DiemDanh).where(
                DiemDanh.cuoc_hop_id == cuoc_hop_id,
                DiemDanh.cong_chuc_id == user_id,
            )
        )
        dd = dd_res.scalar_one_or_none()

        # Window info (G4-fix-7)
        open_at, close_at = self._checkin_window(ch)
        now_local = datetime.now()
        if now_local < open_at:
            window_status = "NOT_YET_OPEN"
        elif now_local > close_at:
            window_status = "CLOSED"
        else:
            window_status = "OPEN"

        return {
            "is_invited": is_invited,
            "da_diem_danh": dd is not None,
            "trang_thai": dd.trang_thai if dd else None,
            "hinh_thuc": dd.hinh_thuc if dd else None,
            "gio_diem_danh": dd.gio_diem_danh.isoformat() if dd and dd.gio_diem_danh else None,
            # Window info
            "window_status": window_status,
            "open_at": open_at.isoformat(),
            "close_at": close_at.isoformat(),
        }

    # ──────────────────────────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────────────────────────
    async def summary(self, cuoc_hop_id: UUID) -> dict:
        # Tổng thành phần
        res_tp = await self.db.execute(
            select(ThanhPhan).where(ThanhPhan.cuoc_hop_id == cuoc_hop_id)
        )
        thanh_phan = list(res_tp.scalars().all())

        # Điểm danh
        res_dd = await self.db.execute(
            select(DiemDanh).where(DiemDanh.cuoc_hop_id == cuoc_hop_id)
        )
        diem_danh = list(res_dd.scalars().all())

        co_mat = sum(1 for d in diem_danh if d.trang_thai == "CO_MAT")
        den_muon = sum(1 for d in diem_danh if d.trang_thai == "DEN_MUON")
        vang_co_phep = sum(1 for d in diem_danh if d.trang_thai == "VANG_CO_PHEP")
        vang_khong_phep = sum(
            1 for d in diem_danh if d.trang_thai == "VANG_KHONG_PHEP"
        )

        diem_danh_cc_ids = {d.cong_chuc_id for d in diem_danh}
        chua = sum(
            1 for tp in thanh_phan if tp.cong_chuc_id not in diem_danh_cc_ids
        )

        return {
            "tong_so": len(thanh_phan),
            "co_mat": co_mat,
            "den_muon": den_muon,
            "vang_co_phep": vang_co_phep,
            "vang_khong_phep": vang_khong_phep,
            "chua_diem_danh": chua,
            "chi_tiet": diem_danh,
        }

    # ──────────────────────────────────────────────────────────────────
    # CHI TIẾT TỪNG THÀNH PHẦN (bảng điểm danh cho ban tổ chức)
    # ──────────────────────────────────────────────────────────────────
    # Câu SQL đi TỪ meeting.thanh_phan chứ không từ meeting.diem_danh, nhờ vậy
    # người chưa điểm danh vẫn có một dòng với trang_thai = NULL. Hai LEFT JOIN
    # sang diem_danh và xin_phep_vang KHÔNG nhân bản dòng vì cả hai bảng đều có
    # UNIQUE (cuoc_hop_id, cong_chuc_id).
    _SQL_CHI_TIET = sa_text("""
        SELECT tp.cong_chuc_id, cc.ho_ten, cc.ma_cc, cc.chuc_vu,
               cc.don_vi_id, dv.ten_don_vi,
               tp.loai_tham_du, tp.xac_nhan,
               dd.trang_thai AS dd_trang_thai, dd.hinh_thuc AS dd_hinh_thuc,
               dd.gio_diem_danh, dd.ghi_chu AS dd_ghi_chu,
               dd.nguoi_diem_danh_id, ndd.ho_ten AS nguoi_diem_danh_ho_ten,
               xpv.trang_thai AS xp_trang_thai, xpv.ly_do AS xp_ly_do,
               xpv.auto_approved AS xp_auto_approved,
               dt.ho_ten AS nguoi_du_thay_ho_ten
          FROM meeting.thanh_phan tp
          LEFT JOIN public.cong_chuc      cc  ON cc.id  = tp.cong_chuc_id
          LEFT JOIN public.don_vi         dv  ON dv.id  = cc.don_vi_id
          LEFT JOIN meeting.diem_danh     dd  ON dd.cuoc_hop_id  = tp.cuoc_hop_id
                                             AND dd.cong_chuc_id = tp.cong_chuc_id
          LEFT JOIN public.cong_chuc      ndd ON ndd.id = dd.nguoi_diem_danh_id
          LEFT JOIN meeting.xin_phep_vang xpv ON xpv.cuoc_hop_id  = tp.cuoc_hop_id
                                             AND xpv.cong_chuc_id = tp.cong_chuc_id
          LEFT JOIN public.cong_chuc      dt  ON dt.id  = xpv.nguoi_du_thay_id
         WHERE tp.cuoc_hop_id = :ch_id
         ORDER BY dv.ten_don_vi NULLS LAST, cc.ho_ten
    """)

    @staticmethod
    def _co_the_bam_tay(ch: CuocHop, user: TokenPayload) -> bool:
        """Phản chiếu ĐÚNG luật của POST /diem-danh/bam-tay.

        Để giao diện không hiện ô chọn trạng thái cho người chắc chắn sẽ ăn
        403 — CCT/PCCT xem được bảng nhưng theo ma trận quyền thì KHÔNG được
        bấm tay.
        """
        if ch.trang_thai == "HUY":
            return False
        user_id = UUID(user.sub)
        return bool(
            user.is_admin
            or user.vai_tro in ("SUPER_ADMIN", "ADMIN")
            or ch.chu_toa_id == user_id
            or ch.thu_ky_id == user_id
            or "TRUONG_CNTT" in (user.platform_roles or [])
        )

    async def chi_tiet(self, ch: CuocHop, user: TokenPayload) -> dict:
        """Bảng điểm danh từng người + tổng hợp + cờ quyền bấm tay."""
        res = await self.db.execute(self._SQL_CHI_TIET, {"ch_id": str(ch.id)})

        danh_sach: list[dict] = []
        for row in res.fetchall():
            # Lý do vắng: ưu tiên đơn xin phép, không có thì lấy ghi chú thư ký
            # nhập khi chấm tay. Bắt buộc có nhánh sau vì thực tế chưa ai dùng
            # luồng đơn xin phép — nếu chỉ đọc từ đơn thì cột này luôn rỗng.
            if row.xp_ly_do:
                ly_do_vang, nguon_ly_do = row.xp_ly_do, "DON_XIN_PHEP"
            elif row.dd_ghi_chu:
                ly_do_vang, nguon_ly_do = row.dd_ghi_chu, "GHI_CHU_DIEM_DANH"
            else:
                ly_do_vang, nguon_ly_do = None, None

            danh_sach.append({
                "cong_chuc_id": str(row.cong_chuc_id),
                "ho_ten": row.ho_ten,
                "ma_cc": row.ma_cc,
                "chuc_vu": row.chuc_vu,
                "don_vi_id": str(row.don_vi_id) if row.don_vi_id else None,
                "ten_don_vi": row.ten_don_vi,
                "loai_tham_du": row.loai_tham_du,
                "xac_nhan": row.xac_nhan,
                "trang_thai": row.dd_trang_thai,
                "hinh_thuc": row.dd_hinh_thuc,
                "gio_diem_danh": (
                    row.gio_diem_danh.isoformat() if row.gio_diem_danh else None
                ),
                "ghi_chu": row.dd_ghi_chu,
                "nguoi_diem_danh_id": (
                    str(row.nguoi_diem_danh_id) if row.nguoi_diem_danh_id else None
                ),
                "nguoi_diem_danh_ho_ten": row.nguoi_diem_danh_ho_ten,
                "ly_do_vang": ly_do_vang,
                "nguon_ly_do": nguon_ly_do,
                "xin_phep_trang_thai": row.xp_trang_thai,
                "xin_phep_auto_duyet": row.xp_auto_approved,
                "nguoi_du_thay_ho_ten": row.nguoi_du_thay_ho_ten,
            })

        # Đếm TỪ CHÍNH danh_sach — bảng và các ô số không bao giờ lệch nhau.
        def _dem(tt: str) -> int:
            return sum(1 for r in danh_sach if r["trang_thai"] == tt)

        return {
            "tong_hop": {
                "tong_so": len(danh_sach),
                "co_mat": _dem("CO_MAT"),
                "den_muon": _dem("DEN_MUON"),
                "vang_co_phep": _dem("VANG_CO_PHEP"),
                "vang_khong_phep": _dem("VANG_KHONG_PHEP"),
                "chua_diem_danh": sum(
                    1 for r in danh_sach if r["trang_thai"] is None
                ),
            },
            "co_the_bam_tay": self._co_the_bam_tay(ch, user),
            "danh_sach": danh_sach,
        }

    # ──────────────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────────────
    async def _get_cuoc_hop(self, cuoc_hop_id: UUID) -> CuocHop:
        result = await self.db.execute(
            select(CuocHop).where(
                CuocHop.id == cuoc_hop_id, CuocHop.is_deleted.is_(False)
            )
        )
        ch = result.scalar_one_or_none()
        if ch is None:
            raise HTTPException(
                status_code=404,
                detail={"success": False, "error": {"code": "MEETING_NOT_FOUND",
                        "message": "Không tìm thấy cuộc họp"}},
            )
        return ch

    # ──────────────────────────────────────────────────────────────────
    # TIME / WINDOW HELPERS (G4-fix-7)
    # ──────────────────────────────────────────────────────────────────
    # Server timezone = local (Vietnam UTC+7). DB lưu DATE + TIME naive
    # (không tz). So sánh giữa naive local datetime với naive local now.
    # KHÔNG dùng tzinfo=UTC (gây bug 7 giờ).

    @staticmethod
    def _gio_bat_dau_local(ch: CuocHop) -> datetime:
        """ngay_hop + gio_bat_dau → naive local datetime."""
        return datetime.combine(ch.ngay_hop, ch.gio_bat_dau)

    @classmethod
    def _gio_ket_thuc_local(cls, ch: CuocHop) -> datetime:
        """ngay_hop + gio_ket_thuc; nếu thiếu → fallback gio_bd + DEFAULT_DURATION."""
        if ch.gio_ket_thuc is not None:
            return datetime.combine(ch.ngay_hop, ch.gio_ket_thuc)
        return cls._gio_bat_dau_local(ch) + timedelta(minutes=DEFAULT_DURATION_MINUTES)

    @classmethod
    def _checkin_window(cls, ch: CuocHop) -> tuple[datetime, datetime]:
        """Trả về (open_at, close_at) naive local cho cuộc họp."""
        gio_bd = cls._gio_bat_dau_local(ch)
        gio_kt = cls._gio_ket_thuc_local(ch)
        open_at = gio_bd - timedelta(minutes=CHECKIN_OPEN_BEFORE_MINUTES)
        close_at = gio_kt + timedelta(minutes=CHECKIN_CLOSE_AFTER_MINUTES)
        return open_at, close_at

    @classmethod
    def _check_checkin_window(cls, ch: CuocHop, now: datetime | None = None) -> None:
        """Raise 409 nếu now ngoài window. None = datetime.now() local."""
        now_local = now or datetime.now()
        open_at, close_at = cls._checkin_window(ch)
        if now_local < open_at:
            raise HTTPException(
                status_code=409,
                detail={"success": False, "error": {
                    "code": "NOT_YET_OPEN",
                    "message": (
                        f"Chưa đến giờ điểm danh. Mở lúc "
                        f"{open_at.strftime('%H:%M %d/%m/%Y')}"
                    ),
                    "open_at": open_at.isoformat(),
                    "close_at": close_at.isoformat(),
                }},
            )
        if now_local > close_at:
            raise HTTPException(
                status_code=409,
                detail={"success": False, "error": {
                    "code": "CHECKIN_CLOSED",
                    "message": (
                        f"Đã đóng điểm danh "
                        f"({close_at.strftime('%H:%M %d/%m/%Y')})"
                    ),
                    "open_at": open_at.isoformat(),
                    "close_at": close_at.isoformat(),
                }},
            )

    @classmethod
    def _compute_trang_thai(cls, ch: CuocHop, now: datetime | None = None) -> str:
        """CO_MAT nếu trong threshold sau giờ bắt đầu, sau đó DEN_MUON.
        now = naive local (datetime.now()). Không dùng UTC để tránh lệch tz.
        """
        now_local = now or datetime.now()
        gio_bd = cls._gio_bat_dau_local(ch)
        diff_minutes = (now_local - gio_bd).total_seconds() / 60
        if diff_minutes <= LATE_THRESHOLD_MINUTES:
            return "CO_MAT"
        return "DEN_MUON"
