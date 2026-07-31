"""
common_service/services/zalo/outbox.py
=======================================
Lõi nghiệp vụ của kênh Zalo — chia làm 2 bước tách bạch:

    xep_hang()     : quét common.thong_bao → tạo bản ghi common.zalo_outbox
    gui_hang_doi() : lấy bản ghi tới hạn trong outbox → gọi ZNS → cập nhật

Tách 2 bước để lỗi ở khâu gửi không làm mất việc đã xếp hàng, và để soi được
"tin này đã vào hàng đợi chưa" tách khỏi "gửi được chưa".

VÌ SAO QUÉT BẢNG THAY VÌ GẮN HOOK LÚC GHI THÔNG BÁO
====================================================
`common.thong_bao` hiện có HAI đường ghi khác nhau:
  - KPI + LMS: gọi HTTP tới Internal API của common_service
  - HKG      : INSERT raw SQL thẳng vào bảng
               (meeting_service/services/notification_service.py:35)
Nếu gắn hook vào tầng service của common_service thì KPI/LMS có Zalo còn HKG
thì KHÔNG — mà HKG mới là module cần trước. Quét bảng bắt được mọi đường ghi,
kể cả module thứ tư sau này lại ghi bằng cách thứ ba.

⚠️ BẪY MÚI GIỜ: `common.thong_bao.created_at` là TIMESTAMP *naive* lưu giờ VN
(Postgres timezone = Asia/Ho_Chi_Minh), trong khi các bảng zalo_* dùng
TIMESTAMPTZ. Mọi so sánh với created_at đều làm bằng SQL CURRENT_TIMESTAMP —
tuyệt đối không so với datetime.utcnow() phía Python (lệch 7 giờ).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from common_service.config import settings
from common_service.models.zalo import (
    BQ_DA_TU_CHOI,
    BQ_KHONG_CO_SDT,
    BQ_KHONG_CO_TEMPLATE,
    LK_HOAT_DONG,
    LK_SO_LOI,
    LK_TU_CHOI_NHAN,
    OB_BO_QUA,
    OB_CHO_GUI,
    OB_DA_GUI,
    OB_THAT_BAI,
    ZaloLienKet,
    ZaloOutbox,
)
from common_service.services.zalo.client import gui_zns, loi_lam_hong_so
from common_service.services.zalo.phone import che_giau
from common_service.services.zalo.templates import ThongTinGui, lay_mau

logger = logging.getLogger("zalo.outbox")

TZ_VN = ZoneInfo("Asia/Ho_Chi_Minh")


# ---------------------------------------------------------------------------
# Bước 1 — xếp hàng
# ---------------------------------------------------------------------------

# LƯU Ý: có LEFT JOIN sang meeting.cuoc_hop để lấy ngày/giờ họp cho tham số
# template. Đây là join chỉ-đọc cross-schema (được phép theo CLAUDE.md).
_SQL_QUET = text(
    """
    SELECT tb.id            AS thong_bao_id,
           tb.nguoi_nhan_id,
           tb.doi_tuong_type,
           tb.link_url,
           cc.ho_ten,
           lk.so_dien_thoai,
           lk.da_dong_y,
           lk.trang_thai    AS lk_trang_thai,
           ch.ngay_hop,
           ch.gio_bat_dau
    FROM common.thong_bao tb
    JOIN public.cong_chuc cc          ON cc.id = tb.nguoi_nhan_id
    LEFT JOIN common.zalo_lien_ket lk ON lk.cong_chuc_id = tb.nguoi_nhan_id
    LEFT JOIN meeting.cuoc_hop ch     ON ch.id = tb.doi_tuong_id
    LEFT JOIN common.zalo_outbox ob   ON ob.thong_bao_id = tb.id
    WHERE tb.loai = ANY(:danh_sach_loai)
      AND tb.created_at >= CURRENT_TIMESTAMP - make_interval(mins => :cua_so_phut)
      AND ob.id IS NULL
      AND cc.is_active = true
    ORDER BY tb.created_at
    LIMIT :gioi_han
    """
)


async def xep_hang(db: AsyncSession, gioi_han: int = 500) -> dict[str, int]:
    """Quét thông báo mới và tạo bản ghi outbox tương ứng.

    Bản ghi được tạo ở một trong hai trạng thái:
      CHO_GUI — đủ điều kiện gửi
      BO_QUA  — thiếu số điện thoại / người dùng từ chối / chưa có template
    Ghi cả trường hợp BO_QUA để sau này trả lời được câu "vì sao anh A không
    nhận được tin" mà không phải suy đoán.
    """
    kq = await db.execute(
        _SQL_QUET,
        {
            "danh_sach_loai": settings.zalo_danh_sach_loai,
            "cua_so_phut": settings.zalo_cua_so_quet_phut,
            "gioi_han": gioi_han,
        },
    )
    dong = kq.mappings().all()

    thong_ke = {"quet": len(dong), "cho_gui": 0, "bo_qua": 0}

    for r in dong:
        mau = lay_mau(r["doi_tuong_type"])
        template_id = getattr(settings, mau.khoa_config, "") if mau else ""

        ly_do: Optional[str] = None
        if mau is None or not template_id:
            ly_do = BQ_KHONG_CO_TEMPLATE
        elif not r["so_dien_thoai"]:
            ly_do = BQ_KHONG_CO_SDT
        elif r["da_dong_y"] is False or r["lk_trang_thai"] in (
            LK_TU_CHOI_NHAN,
            LK_SO_LOI,
        ):
            ly_do = BQ_DA_TU_CHOI

        if ly_do:
            db.add(
                ZaloOutbox(
                    thong_bao_id=r["thong_bao_id"],
                    cong_chuc_id=r["nguoi_nhan_id"],
                    so_dien_thoai=r["so_dien_thoai"],
                    template_id=template_id or None,
                    trang_thai=OB_BO_QUA,
                    ly_do_bo_qua=ly_do,
                )
            )
            thong_ke["bo_qua"] += 1
            continue

        tham_so = mau.dung_tham_so(  # type: ignore[union-attr]
            ThongTinGui(
                doi_tuong_type=r["doi_tuong_type"],
                ho_ten=r["ho_ten"] or "",
                ngay_hop=r["ngay_hop"],
                gio_bat_dau=r["gio_bat_dau"],
                link_url=r["link_url"],
            )
        )
        db.add(
            ZaloOutbox(
                thong_bao_id=r["thong_bao_id"],
                cong_chuc_id=r["nguoi_nhan_id"],
                so_dien_thoai=r["so_dien_thoai"],
                template_id=template_id,
                template_data=tham_so,
                trang_thai=OB_CHO_GUI,
                gui_sau=_moc_gui_hop_le(datetime.now(timezone.utc)),
            )
        )
        thong_ke["cho_gui"] += 1

    await db.commit()
    if thong_ke["quet"]:
        logger.info(
            "Xếp hàng: quét %(quet)d, chờ gửi %(cho_gui)d, bỏ qua %(bo_qua)d",
            thong_ke,
        )
    return thong_ke


# ---------------------------------------------------------------------------
# Khung giờ được phép gửi
# ---------------------------------------------------------------------------


def _moc_gui_hop_le(moc: datetime) -> datetime:
    """Đẩy mốc gửi ra khỏi khung giờ yên tĩnh (mặc định 22h–6h giờ VN).

    Tin Zalo làm rung điện thoại — nhắc họp lúc 2 giờ sáng vì lệch múi giờ
    hay vì job chạy sai là sự cố có thật ở các hệ thống tương tự, nên chặn
    ngay từ tầng dữ liệu chứ không tin vào lịch chạy của scheduler.
    """
    vn = moc.astimezone(TZ_VN)
    sang = settings.zalo_khong_gui_truoc_gio
    toi = settings.zalo_khong_gui_sau_gio

    if vn.hour >= toi:
        # Sau giờ tối → dời sang đầu giờ cho phép sáng hôm sau
        moc_moi = (vn + timedelta(days=1)).replace(
            hour=sang, minute=0, second=0, microsecond=0
        )
    elif vn.hour < sang:
        moc_moi = vn.replace(hour=sang, minute=0, second=0, microsecond=0)
    else:
        return moc

    return moc_moi.astimezone(timezone.utc)


def _backoff(so_lan_thu: int) -> datetime:
    """Giãn cách thử lại: 1, 5, 15, 60 phút."""
    bang = [1, 5, 15, 60]
    phut = bang[min(so_lan_thu, len(bang) - 1)]
    return _moc_gui_hop_le(datetime.now(timezone.utc) + timedelta(minutes=phut))


# ---------------------------------------------------------------------------
# Bước 2 — gửi
# ---------------------------------------------------------------------------


async def gui_hang_doi(db: AsyncSession, gioi_han: Optional[int] = None) -> dict[str, int]:
    """Lấy các bản ghi CHO_GUI đã tới hạn và gửi đi."""
    gioi_han = gioi_han or settings.zalo_moi_lan_gui

    kq = await db.execute(
        select(ZaloOutbox)
        .where(
            ZaloOutbox.trang_thai == OB_CHO_GUI,
            ZaloOutbox.gui_sau <= datetime.now(timezone.utc),
        )
        .order_by(ZaloOutbox.gui_sau)
        .limit(gioi_han)
        .with_for_update(skip_locked=True)  # an toàn nếu lỡ chạy 2 worker
    )
    viec = list(kq.scalars().all())

    thong_ke = {"gui": 0, "thanh_cong": 0, "that_bai": 0, "thu_lai": 0}

    for ob in viec:
        thong_ke["gui"] += 1
        ket_qua = await gui_zns(
            db=db,
            so_dien_thoai=ob.so_dien_thoai or "",
            template_id=ob.template_id or "",
            template_data=ob.template_data or {},
            tracking_id=str(ob.id),
        )
        now = datetime.now(timezone.utc)
        ob.so_lan_thu += 1
        ob.updated_at = now

        if ket_qua.thanh_cong:
            ob.trang_thai = OB_DA_GUI
            ob.ngay_gui = now
            ob.zns_message_id = ket_qua.message_id
            ob.ma_loi = None
            ob.mo_ta_loi = None
            thong_ke["thanh_cong"] += 1
            await _danh_dau_lien_ket(db, ob.cong_chuc_id, LK_HOAT_DONG)
            continue

        ob.ma_loi = ket_qua.ma_loi
        ob.mo_ta_loi = ket_qua.mo_ta_loi

        het_luot = ob.so_lan_thu >= settings.zalo_so_lan_thu_toi_da
        if ket_qua.thu_lai_duoc and not het_luot:
            ob.trang_thai = OB_CHO_GUI
            ob.gui_sau = _backoff(ob.so_lan_thu)
            thong_ke["thu_lai"] += 1
        else:
            ob.trang_thai = OB_THAT_BAI
            thong_ke["that_bai"] += 1
            if loi_lam_hong_so(ket_qua.ma_loi):
                # Số hỏng → đánh dấu để đơn vị rà lại, ngừng gửi vào số này
                await _danh_dau_lien_ket(db, ob.cong_chuc_id, LK_SO_LOI)
                logger.warning(
                    "Số %s của công chức %s có vẻ sai (mã %s) — đã đánh dấu SO_LOI",
                    che_giau(ob.so_dien_thoai),
                    ob.cong_chuc_id,
                    ket_qua.ma_loi,
                )

    await db.commit()
    if thong_ke["gui"]:
        logger.info(
            "Gửi: %(gui)d tin — thành công %(thanh_cong)d, thử lại %(thu_lai)d, "
            "thất bại %(that_bai)d",
            thong_ke,
        )
    return thong_ke


async def _danh_dau_lien_ket(db: AsyncSession, cong_chuc_id, trang_thai: str) -> None:
    """Cập nhật trạng thái liên kết (không commit — để hàm gọi commit chung)."""
    kq = await db.execute(
        select(ZaloLienKet).where(ZaloLienKet.cong_chuc_id == cong_chuc_id)
    )
    lk = kq.scalar_one_or_none()
    if lk is not None and lk.trang_thai != trang_thai:
        lk.trang_thai = trang_thai
        lk.updated_at = datetime.now(timezone.utc)


async def chay_mot_vong(db: AsyncSession) -> dict[str, Any]:
    """Một nhịp đầy đủ: xếp hàng rồi gửi. Dùng cho worker và cho test."""
    kq_xep = await xep_hang(db)
    kq_gui = await gui_hang_doi(db)
    return {"xep_hang": kq_xep, "gui": kq_gui}
