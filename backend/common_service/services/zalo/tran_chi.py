"""
common_service/services/zalo/tran_chi.py
=========================================
Trần chi tiêu cho kênh Zalo — chốt chặn cuối cùng trước khi tiền ra khỏi ví.

VÌ SAO CẦN
==========
Hạn mức kỹ thuật Zalo cấp cho OA là 20.000 tin/ngày. Với đơn giá 800đ/tin,
một lỗi lập trình hay một cuộc họp lỡ tay mời cả cơ quan có thể tiêu
16.000.000đ trong một ngày mà không có gì chặn lại. Phần mềm tiêu tiền công
thì không được phép không có trần.

CHẶN Ở ĐÂU — khâu GỬI, không phải khâu XẾP HÀNG
================================================
`xep_hang()` vẫn chạy đầy đủ kể cả khi đã chạm trần. Cố ý như vậy:
  - giữ dấu vết "thông báo này đã được nhìn thấy", trả lời được về sau
  - khi lãnh đạo nâng trần thì tin còn nằm sẵn đó, gửi tiếp được ngay
Chặn ở `gui_hang_doi()` mới đúng chỗ tiền thực sự ra khỏi ví.

TIN BỊ CHẶN KHÔNG BỊ XÓA, NHƯNG CÓ HẠN SỬ DỤNG
===============================================
Tin bị trần chặn giữ nguyên trạng thái CHO_GUI. Nếu để vậy vô thời hạn thì
sang ngày/tháng mới cả đống nhắc họp cũ sẽ ùa ra cùng lúc — nhắc về cuộc họp
đã diễn ra ba tuần trước là quấy rối chứ không phải phục vụ. Vì vậy tin quá
`zalo_han_gui_gio` giờ bị đánh dấu BO_QUA/QUA_HAN.

⚠️ CẢNH BÁO GỬI BẰNG THÔNG BÁO TRONG PHẦN MỀM, KHÔNG GỬI BẰNG ZALO.
   Gửi cảnh báo "hết tiền" bằng chính kênh đang tiêu tiền là vòng lặp tự nuôi:
   cảnh báo sinh thông báo → worker nhặt lên → lại tốn tin. Cảnh báo dùng
   `loai = 'HE_THONG'`, nằm ngoài `zalo_loai_bat`, và có thêm một lớp chặn
   phòng khi ai đó cấu hình nhầm (xem `_duoc_phep_canh_bao`).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from common_service.config import settings
from common_service.models.zalo import BQ_QUA_HAN, OB_BO_QUA, OB_CHO_GUI, OB_DA_GUI

logger = logging.getLogger("zalo.tran_chi")

# Vai trò nhận cảnh báo chi tiêu. Tách ra hằng số để đổi được mà không phải
# lục trong câu SQL (mã vai trò thật trong public.vai_tro là 'ADMIN').
VAI_TRO_NHAN_CANH_BAO = "ADMIN"

# `loai` của thông báo cảnh báo — CỐ Ý khác mọi giá trị trong zalo_loai_bat
LOAI_CANH_BAO = "HE_THONG"

# Đánh dấu vào doi_tuong_type để (a) chống gửi trùng trong ngày, (b) lọc ra
# xem lại về sau. Không cần thêm cột nào vào bảng.
MUC_CHAN = "ZALO_CHAM_TRAN"
MUC_SAP_CHAM = "ZALO_SAP_CHAM_TRAN"


def dinh_dang_tien(so: int) -> str:
    """1234000 → '1.234.000đ' (dấu chấm phân nhóm kiểu Việt Nam)."""
    return f"{so:,}đ".replace(",", ".")


def khong_gioi_han(tran: int) -> bool:
    """Quy ước chung: âm = không giới hạn, 0 = chặn hoàn toàn, >0 = trần thật."""
    return tran < 0


def mo_ta_tran(tran_dong: int) -> str:
    """Diễn giải giá trị cấu hình cho log và báo cáo."""
    if khong_gioi_han(tran_dong):
        return "KHÔNG ĐẶT"
    if tran_dong == 0:
        return "0đ — CHẶN HOÀN TOÀN"
    return dinh_dang_tien(tran_dong)


def _phan_tram(da_dung: int, tran: int) -> Optional[int]:
    """None nếu không đặt trần. Trần 0 luôn coi là đã đầy 100%."""
    if khong_gioi_han(tran):
        return None
    if tran == 0:
        return 100
    return int(100 * da_dung / tran)


# ---------------------------------------------------------------------------
# Đo đã chi bao nhiêu
# ---------------------------------------------------------------------------

# Chỉ đếm tin ĐÃ GỬI THÀNH CÔNG — tin thất bại Zalo không tính tiền, tin thử
# lại rồi mới thành công chỉ tính một lần (mỗi bản ghi outbox là một tin).
#
# ⚠️ MÚI GIỜ: `ngay_gui` là TIMESTAMPTZ. "Hôm nay" phải là hôm nay theo giờ
# Việt Nam, không phải theo UTC — nếu so bằng UTC thì từ 0h đến 7h sáng mỗi
# ngày sẽ tính nhầm sang mốc hôm trước, và trần ngày trượt 7 tiếng.
_SQL_DA_CHI = text(
    """
    SELECT
        count(*) FILTER (
            WHERE ngay_gui AT TIME ZONE 'Asia/Ho_Chi_Minh'
                  >= date_trunc('day', now() AT TIME ZONE 'Asia/Ho_Chi_Minh')
        ) AS tin_ngay,
        count(*) FILTER (
            WHERE ngay_gui AT TIME ZONE 'Asia/Ho_Chi_Minh'
                  >= date_trunc('month', now() AT TIME ZONE 'Asia/Ho_Chi_Minh')
        ) AS tin_thang
    FROM common.zalo_outbox
    WHERE trang_thai = :da_gui
      AND ngay_gui IS NOT NULL
    """
)


@dataclass(frozen=True)
class TinhHinhChi:
    """Ảnh chụp chi tiêu tại một thời điểm.

    Trần tính bằng SỐ TIN: âm = không giới hạn, 0 = chặn hoàn toàn.
    """

    tin_ngay: int
    tin_thang: int
    don_gia: int
    tran_ngay_tin: int
    tran_thang_tin: int

    @property
    def dong_ngay(self) -> int:
        return self.tin_ngay * self.don_gia

    @property
    def dong_thang(self) -> int:
        return self.tin_thang * self.don_gia

    @property
    def con_lai_ngay(self) -> Optional[int]:
        """Số tin còn được gửi hôm nay. None = không đặt trần ngày."""
        if self.tran_ngay_tin < 0:
            return None
        return max(0, self.tran_ngay_tin - self.tin_ngay)

    @property
    def con_lai_thang(self) -> Optional[int]:
        if self.tran_thang_tin < 0:
            return None
        return max(0, self.tran_thang_tin - self.tin_thang)

    @property
    def con_lai(self) -> Optional[int]:
        """Trần nào chặt hơn thì trần đó có hiệu lực. None = không trần nào."""
        cac_tran = [x for x in (self.con_lai_ngay, self.con_lai_thang) if x is not None]
        return min(cac_tran) if cac_tran else None

    @property
    def cham_tran(self) -> bool:
        return self.con_lai == 0

    @property
    def phan_tram_ngay(self) -> Optional[int]:
        return _phan_tram(self.tin_ngay, self.tran_ngay_tin)

    @property
    def phan_tram_thang(self) -> Optional[int]:
        return _phan_tram(self.tin_thang, self.tran_thang_tin)

    @property
    def phan_tram_cao_nhat(self) -> int:
        """Mức lấp đầy của trần chặt nhất — dùng để quyết định có cảnh báo."""
        cac = [x for x in (self.phan_tram_ngay, self.phan_tram_thang) if x is not None]
        return max(cac) if cac else 0

    def tom_tat(self) -> str:
        """Một dòng cho log và cho nội dung cảnh báo."""

        def _ve(nhan: str, tin: int, tran: int, pc: Optional[int]) -> str:
            if khong_gioi_han(tran):
                return f"{nhan} {tin} tin ({dinh_dang_tien(tin * self.don_gia)}, không trần)"
            return (
                f"{nhan} {tin}/{tran} tin — "
                f"{dinh_dang_tien(tin * self.don_gia)}/"
                f"{dinh_dang_tien(tran * self.don_gia)} ({pc}%)"
            )

        return " | ".join(
            [
                _ve("Hôm nay:", self.tin_ngay, self.tran_ngay_tin, self.phan_tram_ngay),
                _ve(
                    "Tháng này:",
                    self.tin_thang,
                    self.tran_thang_tin,
                    self.phan_tram_thang,
                ),
            ]
        )


def _tran_tin(tran_dong: int, don_gia: int) -> int:
    """Quy đổi trần từ đồng sang số tin, giữ nguyên quy ước dấu.

    Cấu hình bằng ĐỒNG chứ không bằng số tin vì lãnh đạo duyệt ngân sách bằng
    tiền. Quy đổi ở đây, một chỗ duy nhất.

    Đơn giá ≤ 0 là cấu hình hỏng → trả về "không giới hạn" thay vì "chặn hết":
    một biến môi trường gõ sai không được phép làm cả cơ quan ngừng nhận giấy
    mời họp.
    """
    if don_gia <= 0:
        return -1
    if tran_dong < 0:
        return -1
    return tran_dong // don_gia


async def tinh_hinh_chi(db: AsyncSession) -> TinhHinhChi:
    """Đọc chi tiêu hiện tại từ outbox và ghép với trần đang cấu hình."""
    r = (await db.execute(_SQL_DA_CHI, {"da_gui": OB_DA_GUI})).mappings().one()
    don_gia = settings.zalo_don_gia_tin
    return TinhHinhChi(
        tin_ngay=r["tin_ngay"] or 0,
        tin_thang=r["tin_thang"] or 0,
        don_gia=don_gia,
        tran_ngay_tin=_tran_tin(settings.zalo_tran_ngay_dong, don_gia),
        tran_thang_tin=_tran_tin(settings.zalo_tran_thang_dong, don_gia),
    )


# ---------------------------------------------------------------------------
# Hết hạn tin nằm chờ quá lâu
# ---------------------------------------------------------------------------

_SQL_HET_HAN = text(
    """
    UPDATE common.zalo_outbox
       SET trang_thai   = :bo_qua,
           ly_do_bo_qua = :qua_han,
           updated_at   = now()
     WHERE trang_thai = :cho_gui
       AND created_at < now() - make_interval(hours => :han_gio)
    """
)


async def het_han_tin_cho(db: AsyncSession) -> int:
    """Đánh dấu bỏ qua các tin nằm chờ quá `zalo_han_gui_gio` giờ.

    Không phải dọn rác cho đẹp — đây là điều kiện để trần chi tiêu dùng được.
    Không có nó thì trần chỉ hoãn tiền chứ không tiết kiệm, và còn dồn thành
    một đợt tin lỗi thời bắn ra lúc trần được nới.

    Ngưỡng mặc định 12 giờ nằm ngoài mọi độ trễ bình thường: giờ yên tĩnh
    hoãn tối đa 8 tiếng (22h → 6h), backoff thử lại tối đa 1 tiếng.
    """
    han_gio = settings.zalo_han_gui_gio
    if han_gio <= 0:
        return 0
    kq = await db.execute(
        _SQL_HET_HAN,
        {
            "bo_qua": OB_BO_QUA,
            "qua_han": BQ_QUA_HAN,
            "cho_gui": OB_CHO_GUI,
            "han_gio": han_gio,
        },
    )
    so = kq.rowcount or 0
    if so:
        logger.warning(
            "Bỏ qua %d tin nằm chờ quá %d giờ (quá hạn — nội dung đã lỗi thời)",
            so,
            han_gio,
        )
    return so


async def dem_cho_gui(db: AsyncSession) -> int:
    """Số tin đang xếp hàng chờ — đưa vào cảnh báo để biết mức độ dồn ứ."""
    r = await db.execute(
        text(
            "SELECT count(*) FROM common.zalo_outbox WHERE trang_thai = :cho_gui"
        ),
        {"cho_gui": OB_CHO_GUI},
    )
    return int(r.scalar() or 0)


# ---------------------------------------------------------------------------
# Cảnh báo quản trị
# ---------------------------------------------------------------------------


def _duoc_phep_canh_bao() -> bool:
    """Chặn vòng lặp tự nuôi: không cảnh báo nếu loai cảnh báo lại bật Zalo.

    Kịch bản hỏng: ai đó đặt ZALO_LOAI_BAT="MEETING,HE_THONG". Khi ấy mỗi
    cảnh báo hết tiền lại đẻ ra tin Zalo tính phí — càng hết tiền càng tiêu.
    """
    if LOAI_CANH_BAO in settings.zalo_danh_sach_loai:
        logger.error(
            "ZALO_LOAI_BAT đang chứa '%s' — bỏ cảnh báo để tránh vòng lặp tự "
            "gửi. Hãy bỏ giá trị này khỏi cấu hình.",
            LOAI_CANH_BAO,
        )
        return False
    return True


_SQL_DA_CANH_BAO_HOM_NAY = text(
    """
    SELECT 1
      FROM common.thong_bao
     WHERE loai = :loai
       AND doi_tuong_type = :muc
       AND created_at >= date_trunc('day', CURRENT_TIMESTAMP)
     LIMIT 1
    """
)

# created_at của common.thong_bao là TIMESTAMP *naive* lưu giờ VN (xem đầu
# outbox.py) nên so trực tiếp với CURRENT_TIMESTAMP, KHÔNG đổi múi giờ.

_SQL_CHEN_CANH_BAO = text(
    """
    INSERT INTO common.thong_bao
        (nguoi_nhan_id, tieu_de, noi_dung, loai, link_url,
         doi_tuong_type, muc_do)
    SELECT cc.id, :tieu_de, :noi_dung, :loai, NULL, :muc, 'QUAN_TRONG'
      FROM public.cong_chuc cc
      JOIN public.vai_tro vt ON vt.id = cc.vai_tro_id
     WHERE vt.ma_vai_tro = :vai_tro
       AND cc.is_active = true
    """
)


async def canh_bao_neu_can(
    db: AsyncSession, th: TinhHinhChi, so_cho_gui: int
) -> Optional[str]:
    """Gửi thông báo cho quản trị khi sắp chạm hoặc đã chạm trần.

    Trả về mức đã cảnh báo, hoặc None nếu không cần / đã cảnh báo hôm nay rồi.
    Mỗi mức chỉ báo MỘT lần trong ngày — worker chạy 60 giây một nhịp, không
    khóa lại thì quản trị nhận 1.440 thông báo giống nhau mỗi ngày.
    """
    if th.con_lai is None or not _duoc_phep_canh_bao():
        return None

    if th.cham_tran:
        muc = MUC_CHAN
        tieu_de = "Zalo: đã chạm trần chi tiêu — tạm ngừng gửi tin"
        noi_dung = (
            f"Kênh Zalo đã ngừng gửi vì chạm trần chi tiêu.\n"
            f"{th.tom_tat()}\n"
            f"Đang có {so_cho_gui} tin xếp hàng chờ. Tin chờ quá "
            f"{settings.zalo_han_gui_gio} giờ sẽ bị bỏ do nội dung lỗi thời.\n"
            f"Nâng trần bằng ZALO_TRAN_NGAY_DONG / ZALO_TRAN_THANG_DONG trong "
            f"backend/.env rồi khởi động lại zalo-worker."
        )
    elif th.phan_tram_cao_nhat >= settings.zalo_nguong_canh_bao_pc:
        muc = MUC_SAP_CHAM
        tieu_de = (
            f"Zalo: đã dùng {th.phan_tram_cao_nhat}% hạn mức chi tiêu"
        )
        noi_dung = (
            f"Kênh Zalo sắp chạm trần chi tiêu.\n"
            f"{th.tom_tat()}\n"
            f"Khi chạm trần, tin sẽ ngừng gửi cho tới khi sang kỳ mới hoặc "
            f"trần được nâng."
        )
    else:
        return None

    da_bao = await db.execute(
        _SQL_DA_CANH_BAO_HOM_NAY, {"loai": LOAI_CANH_BAO, "muc": muc}
    )
    if da_bao.first() is not None:
        return None

    kq = await db.execute(
        _SQL_CHEN_CANH_BAO,
        {
            "tieu_de": tieu_de[:300],
            "noi_dung": noi_dung,
            "loai": LOAI_CANH_BAO,
            "muc": muc,
            "vai_tro": VAI_TRO_NHAN_CANH_BAO,
        },
    )
    logger.error("%s | %s | báo cho %d quản trị", tieu_de, th.tom_tat(), kq.rowcount or 0)
    return muc
