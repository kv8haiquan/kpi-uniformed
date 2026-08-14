"""
Test trần chi tiêu kênh Zalo (common_service/services/zalo/tran_chi.py).

Chạy trên DB TEST:
    DB_NAME=kpi_haiquan_test PYTHONPATH=$PWD pytest \
        common_service/tests/test_zalo_tran_chi.py -v

Chia hai phần:
  - TestSoHoc: thuần tính toán, không đụng DB, chạy ở đâu cũng được
  - phần còn lại: tích hợp thật với common.zalo_outbox

Các test tích hợp đặt trần THEO NỀN sẵn có trong DB (`tin_ngay` hiện tại + N)
chứ không đặt số tuyệt đối — DB test là bản sao của production nên có thể đã
có sẵn tin đã gửi, đặt số cứng sẽ đỏ/xanh tùy ngày chạy.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from common_service.config import settings
from common_service.models.zalo import (
    BQ_QUA_HAN,
    OB_BO_QUA,
    OB_CHO_GUI,
    OB_DA_GUI,
    ZaloOutbox,
)
from common_service.services.zalo.outbox import chay_mot_vong, gui_hang_doi
from common_service.services.zalo.tran_chi import (
    LOAI_CANH_BAO,
    MUC_CHAN,
    MUC_SAP_CHAM,
    TinhHinhChi,
    _tran_tin,
    canh_bao_neu_can,
    dinh_dang_tien,
    het_han_tin_cho,
    tinh_hinh_chi,
)

from .conftest import _REAL_CC_IDS

CC_A = uuid.UUID(_REAL_CC_IDS[0])
DON_GIA = 800


# ---------------------------------------------------------------------------
# Phần 1 — số học thuần, không cần DB
# ---------------------------------------------------------------------------


class TestSoHoc:
    def _th(self, tin_ngay=0, tin_thang=0, tran_ngay=-1, tran_thang=-1):
        return TinhHinhChi(
            tin_ngay=tin_ngay,
            tin_thang=tin_thang,
            don_gia=DON_GIA,
            tran_ngay_tin=tran_ngay,
            tran_thang_tin=tran_thang,
        )

    def test_khong_dat_tran_thi_khong_gioi_han(self):
        """Mặc định phải là KHÔNG chặn — merge code không được âm thầm cắt tin."""
        th = self._th(tin_ngay=99999, tin_thang=99999)
        assert th.con_lai is None
        assert th.cham_tran is False

    def test_tran_bang_khong_la_chan_het_chu_khong_phai_vo_han(self):
        """Quy ước sống còn: ai gõ 0 để khóa chi tiêu phải được khóa thật.
        Nếu 0 mang nghĩa 'không giới hạn' thì thao tác khóa lại mở toang."""
        th = self._th(tin_ngay=0, tran_ngay=0)
        assert th.con_lai == 0
        assert th.cham_tran is True
        assert th.phan_tram_ngay == 100  # không được chia cho 0

    def test_tran_chat_hon_la_tran_co_hieu_luc(self):
        """Còn 5 tin theo ngày, 100 theo tháng → hiệu lực là 5."""
        th = self._th(tin_ngay=95, tin_thang=900, tran_ngay=100, tran_thang=1000)
        assert th.con_lai_ngay == 5
        assert th.con_lai_thang == 100
        assert th.con_lai == 5

    def test_tran_thang_cung_chan_duoc_du_ngay_con_room(self):
        """Ngược chiều: hết hạn mức tháng thì trần ngày rộng cũng vô nghĩa."""
        th = self._th(tin_ngay=1, tin_thang=1000, tran_ngay=500, tran_thang=1000)
        assert th.con_lai == 0
        assert th.cham_tran is True

    def test_vuot_tran_khong_tra_ve_so_am(self):
        """Vượt trần (do đổi cấu hình giữa chừng) vẫn phải là 0, không âm —
        nếu âm thì `min(gioi_han, con_lai)` sẽ thành limit âm ở câu SQL."""
        th = self._th(tin_ngay=150, tran_ngay=100)
        assert th.con_lai == 0
        assert th.cham_tran is True

    def test_quy_doi_tien_sang_so_tin(self):
        assert _tran_tin(800_000, 800) == 1000
        assert _tran_tin(0, 800) == 0  # chặn hoàn toàn
        assert _tran_tin(-1, 800) == -1  # không giới hạn
        # Đơn giá gõ sai không được phép làm cả cơ quan mất giấy mời họp
        assert _tran_tin(800_000, 0) == -1

    def test_quy_doi_lam_tron_xuong(self):
        """999đ trần với giá 800đ/tin = 1 tin, không phải 1,25 tin."""
        assert _tran_tin(999, 800) == 1

    def test_khong_dat_tran_ngay_thi_phan_tram_la_none(self):
        th = self._th(tin_ngay=500)
        assert th.phan_tram_ngay is None
        assert th.phan_tram_cao_nhat == 0

    def test_phan_tram_lay_theo_tran_lap_day_nhat(self):
        th = self._th(tin_ngay=90, tin_thang=100, tran_ngay=100, tran_thang=1000)
        assert th.phan_tram_ngay == 90
        assert th.phan_tram_thang == 10
        assert th.phan_tram_cao_nhat == 90

    def test_dinh_dang_tien_kieu_viet_nam(self):
        assert dinh_dang_tien(1_234_000) == "1.234.000đ"
        assert dinh_dang_tien(800) == "800đ"
        assert dinh_dang_tien(0) == "0đ"

    def test_tom_tat_neu_ro_khong_dat_tran(self):
        assert "không trần" in self._th(tin_ngay=5).tom_tat()


# ---------------------------------------------------------------------------
# Phần 2 — tích hợp
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def cau_hinh_zalo(monkeypatch):
    """Dry-run + mở khung giờ cả ngày (xem test_zalo_outbox.py để biết vì sao)."""
    monkeypatch.setattr(settings, "zalo_dry_run", True, raising=False)
    monkeypatch.setattr(settings, "zalo_loai_bat", "MEETING", raising=False)
    monkeypatch.setattr(settings, "zalo_khong_gui_truoc_gio", 0, raising=False)
    monkeypatch.setattr(settings, "zalo_khong_gui_sau_gio", 24, raising=False)
    monkeypatch.setattr(settings, "zalo_don_gia_tin", DON_GIA, raising=False)
    monkeypatch.setattr(settings, "zalo_tran_ngay_dong", -1, raising=False)
    monkeypatch.setattr(settings, "zalo_tran_thang_dong", -1, raising=False)
    monkeypatch.setattr(settings, "zalo_han_gui_gio", 12, raising=False)
    monkeypatch.setattr(settings, "zalo_nguong_canh_bao_pc", 80, raising=False)


@pytest_asyncio.fixture
async def hang_doi_sach(db_session: AsyncSession):
    """Bỏ qua test nếu hàng đợi đang có tin lạ.

    `gui_hang_doi()` lấy theo `gui_sau` trên TOÀN bảng, không lọc theo test.
    Nếu DB test còn tin tồn thì nó sẽ chiếm mất suất gửi và test đếm sai. Thà
    bỏ qua có thông báo còn hơn đỏ vì lý do không liên quan.
    """
    r = await db_session.execute(
        text("SELECT count(*) FROM common.zalo_outbox WHERE trang_thai = :t"),
        {"t": OB_CHO_GUI},
    )
    if (r.scalar() or 0) > 0:
        pytest.skip("common.zalo_outbox đang có tin CHO_GUI tồn — bỏ qua để khỏi đếm nhầm")


async def _tao_thong_bao(db: AsyncSession, doi_tuong_type: str = "GIAY_MOI_HOP") -> uuid.UUID:
    """Outbox có FK sang thong_bao nên phải có bản ghi thật để tựa vào."""
    tb_id = uuid.uuid4()
    await db.execute(
        text(
            """
            INSERT INTO common.thong_bao
                (id, nguoi_nhan_id, tieu_de, loai, doi_tuong_type, muc_do)
            VALUES (:id, :nn, 'Test trần chi', 'MEETING', :dtt, 'BINH_THUONG')
            """
        ),
        {"id": str(tb_id), "nn": str(CC_A), "dtt": doi_tuong_type},
    )
    return tb_id


async def _tao_outbox(
    db: AsyncSession,
    trang_thai: str = OB_CHO_GUI,
    tuoi_gio: int = 0,
    da_gui: bool = False,
) -> uuid.UUID:
    """Một bản ghi outbox. `tuoi_gio` lùi created_at để thử logic quá hạn."""
    tb_id = await _tao_thong_bao(db)
    ob_id = uuid.uuid4()
    await db.execute(
        text(
            """
            INSERT INTO common.zalo_outbox
                (id, thong_bao_id, cong_chuc_id, so_dien_thoai, template_id,
                 template_data, trang_thai, gui_sau, ngay_gui, created_at)
            VALUES
                (:id, :tb, :cc, '84900000001', 'TPL_TEST',
                 '{"ho_ten":"Test"}'::jsonb, :tt,
                 now() - make_interval(hours => :tuoi),
                 CASE WHEN :da_gui THEN now() ELSE NULL END,
                 now() - make_interval(hours => :tuoi))
            """
        ),
        {
            "id": str(ob_id),
            "tb": str(tb_id),
            "cc": str(CC_A),
            "tt": trang_thai,
            "tuoi": tuoi_gio,
            "da_gui": da_gui,
        },
    )
    return ob_id


async def _trang_thai(db: AsyncSession, ob_id: uuid.UUID) -> ZaloOutbox:
    return (
        await db.execute(select(ZaloOutbox).where(ZaloOutbox.id == ob_id))
    ).scalar_one()


async def _dat_tran_con_lai(db: AsyncSession, monkeypatch, con_lai: int) -> None:
    """Đặt trần NGÀY sao cho còn đúng `con_lai` tin, tính từ nền hiện có."""
    nen = await tinh_hinh_chi(db)
    monkeypatch.setattr(
        settings, "zalo_tran_ngay_dong", (nen.tin_ngay + con_lai) * DON_GIA, raising=False
    )


# --- chặn -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cham_tran_thi_khong_gui_tin_nao(
    db_session: AsyncSession, hang_doi_sach, monkeypatch
):
    ob_id = await _tao_outbox(db_session)
    await _dat_tran_con_lai(db_session, monkeypatch, 0)

    kq = await gui_hang_doi(db_session)

    assert kq["gui"] == 0, "chạm trần mà vẫn gọi API gửi"
    assert kq["chan_boi_tran"] >= 1
    assert (await _trang_thai(db_session, ob_id)).trang_thai == OB_CHO_GUI


@pytest.mark.asyncio
async def test_tin_bi_tran_chan_van_nam_cho_chu_khong_bi_bo(
    db_session: AsyncSession, hang_doi_sach, monkeypatch
):
    """Chặn ≠ hủy. Nâng trần lên là tin phải gửi được ngay, không phải tạo lại."""
    ob_id = await _tao_outbox(db_session)
    await _dat_tran_con_lai(db_session, monkeypatch, 0)
    await gui_hang_doi(db_session)
    assert (await _trang_thai(db_session, ob_id)).trang_thai == OB_CHO_GUI

    await _dat_tran_con_lai(db_session, monkeypatch, 10)
    kq = await gui_hang_doi(db_session)

    assert kq["thanh_cong"] == 1
    assert (await _trang_thai(db_session, ob_id)).trang_thai == OB_DA_GUI


@pytest.mark.asyncio
async def test_gui_toi_sat_tran_roi_dung(
    db_session: AsyncSession, hang_doi_sach, monkeypatch
):
    """5 tin chờ, còn 2 suất → gửi đúng 2, ba tin còn lại ở nguyên hàng đợi."""
    ids = [await _tao_outbox(db_session) for _ in range(5)]
    await _dat_tran_con_lai(db_session, monkeypatch, 2)

    kq = await gui_hang_doi(db_session)

    assert kq["gui"] == 2, f"phải gửi đúng 2 tin, thực tế {kq['gui']}"
    trang_thai = [(await _trang_thai(db_session, i)).trang_thai for i in ids]
    assert trang_thai.count(OB_DA_GUI) == 2
    assert trang_thai.count(OB_CHO_GUI) == 3


@pytest.mark.asyncio
async def test_khong_dat_tran_thi_gui_binh_thuong(
    db_session: AsyncSession, hang_doi_sach
):
    """Cấu hình mặc định (trần = 0) không được làm thay đổi hành vi cũ."""
    ids = [await _tao_outbox(db_session) for _ in range(3)]
    kq = await gui_hang_doi(db_session)

    assert kq["gui"] == 3
    assert kq["chan_boi_tran"] == 0
    for i in ids:
        assert (await _trang_thai(db_session, i)).trang_thai == OB_DA_GUI


@pytest.mark.asyncio
async def test_tran_thang_chan_duoc_du_khong_dat_tran_ngay(
    db_session: AsyncSession, hang_doi_sach, monkeypatch
):
    ob_id = await _tao_outbox(db_session)
    nen = await tinh_hinh_chi(db_session)
    monkeypatch.setattr(
        settings, "zalo_tran_thang_dong", nen.tin_thang * DON_GIA, raising=False
    )

    kq = await gui_hang_doi(db_session)

    assert kq["gui"] == 0
    assert (await _trang_thai(db_session, ob_id)).trang_thai == OB_CHO_GUI


# --- đo chi tiêu ------------------------------------------------------------


@pytest.mark.asyncio
async def test_chi_dem_tin_da_gui_thanh_cong(db_session: AsyncSession):
    """Tin thất bại / bỏ qua không tính tiền nên không được vào số đã chi."""
    nen = await tinh_hinh_chi(db_session)

    await _tao_outbox(db_session, trang_thai=OB_DA_GUI, da_gui=True)
    await _tao_outbox(db_session, trang_thai="THAT_BAI")
    await _tao_outbox(db_session, trang_thai=OB_BO_QUA)
    await _tao_outbox(db_session, trang_thai=OB_CHO_GUI)

    sau = await tinh_hinh_chi(db_session)
    assert sau.tin_ngay == nen.tin_ngay + 1
    assert sau.tin_thang == nen.tin_thang + 1


@pytest.mark.asyncio
async def test_tien_quy_doi_dung_don_gia(db_session: AsyncSession):
    nen = await tinh_hinh_chi(db_session)
    await _tao_outbox(db_session, trang_thai=OB_DA_GUI, da_gui=True)
    sau = await tinh_hinh_chi(db_session)
    assert sau.dong_ngay - nen.dong_ngay == DON_GIA


# --- quá hạn ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_tin_cho_qua_han_bi_bo(db_session: AsyncSession, monkeypatch):
    """Không có bước này thì trần chỉ hoãn tiền, và dồn thành đợt tin lỗi thời."""
    cu = await _tao_outbox(db_session, tuoi_gio=13)
    moi = await _tao_outbox(db_session, tuoi_gio=1)

    so = await het_han_tin_cho(db_session)

    assert so >= 1
    ob_cu = await _trang_thai(db_session, cu)
    assert ob_cu.trang_thai == OB_BO_QUA
    assert ob_cu.ly_do_bo_qua == BQ_QUA_HAN
    assert (await _trang_thai(db_session, moi)).trang_thai == OB_CHO_GUI


@pytest.mark.asyncio
async def test_han_gui_bang_khong_thi_khong_bo_tin_nao(
    db_session: AsyncSession, monkeypatch
):
    """Cửa thoát hiểm: đặt 0 để tắt hẳn việc bỏ tin quá hạn."""
    monkeypatch.setattr(settings, "zalo_han_gui_gio", 0, raising=False)
    ob_id = await _tao_outbox(db_session, tuoi_gio=100)

    assert await het_han_tin_cho(db_session) == 0
    assert (await _trang_thai(db_session, ob_id)).trang_thai == OB_CHO_GUI


@pytest.mark.asyncio
async def test_don_qua_han_chay_truoc_khi_gui(
    db_session: AsyncSession, hang_doi_sach, monkeypatch
):
    """Trong một vòng đầy đủ, tin lỗi thời không được chiếm suất của tin mới."""
    cu = await _tao_outbox(db_session, tuoi_gio=20)
    moi = await _tao_outbox(db_session, tuoi_gio=0)
    await _dat_tran_con_lai(db_session, monkeypatch, 1)

    kq = await chay_mot_vong(db_session)

    assert kq["het_han"] >= 1
    assert (await _trang_thai(db_session, cu)).trang_thai == OB_BO_QUA
    assert (await _trang_thai(db_session, moi)).trang_thai == OB_DA_GUI


# --- cảnh báo ---------------------------------------------------------------


async def _dem_canh_bao(db: AsyncSession, muc: str) -> int:
    r = await db.execute(
        text(
            "SELECT count(*) FROM common.thong_bao "
            "WHERE loai = :loai AND doi_tuong_type = :muc"
        ),
        {"loai": LOAI_CANH_BAO, "muc": muc},
    )
    return int(r.scalar() or 0)


@pytest.mark.asyncio
async def test_cham_tran_thi_bao_cho_quan_tri(
    db_session: AsyncSession, hang_doi_sach, monkeypatch
):
    await _tao_outbox(db_session)
    await _dat_tran_con_lai(db_session, monkeypatch, 0)

    await gui_hang_doi(db_session)

    assert await _dem_canh_bao(db_session, MUC_CHAN) >= 1


@pytest.mark.asyncio
async def test_moi_muc_chi_bao_mot_lan_trong_ngay(
    db_session: AsyncSession, hang_doi_sach, monkeypatch
):
    """Worker chạy 60 giây/nhịp — không khóa lại thì quản trị nhận 1.440 tin
    giống nhau mỗi ngày và sẽ tắt thông báo, tức là mất luôn cảnh báo thật."""
    await _tao_outbox(db_session)
    await _dat_tran_con_lai(db_session, monkeypatch, 0)

    await gui_hang_doi(db_session)
    sau_lan_1 = await _dem_canh_bao(db_session, MUC_CHAN)
    for _ in range(3):
        await gui_hang_doi(db_session)

    assert await _dem_canh_bao(db_session, MUC_CHAN) == sau_lan_1


@pytest.mark.asyncio
async def test_canh_bao_som_khi_vuot_nguong(db_session: AsyncSession):
    """90% hạn mức → báo trước, chưa chặn."""
    th = TinhHinhChi(
        tin_ngay=90, tin_thang=0, don_gia=DON_GIA, tran_ngay_tin=100, tran_thang_tin=-1
    )
    assert th.cham_tran is False

    muc = await canh_bao_neu_can(db_session, th, so_cho_gui=5)

    assert muc == MUC_SAP_CHAM
    assert await _dem_canh_bao(db_session, MUC_SAP_CHAM) >= 1


@pytest.mark.asyncio
async def test_duoi_nguong_thi_khong_lam_phien(db_session: AsyncSession):
    th = TinhHinhChi(
        tin_ngay=10, tin_thang=0, don_gia=DON_GIA, tran_ngay_tin=100, tran_thang_tin=-1
    )
    assert await canh_bao_neu_can(db_session, th, so_cho_gui=0) is None


@pytest.mark.asyncio
async def test_khong_dat_tran_thi_khong_canh_bao(db_session: AsyncSession):
    th = TinhHinhChi(
        tin_ngay=99999, tin_thang=99999, don_gia=DON_GIA,
        tran_ngay_tin=-1, tran_thang_tin=-1,
    )
    assert await canh_bao_neu_can(db_session, th, so_cho_gui=0) is None


@pytest.mark.asyncio
async def test_canh_bao_khong_bao_gio_thanh_tin_zalo(
    db_session: AsyncSession, monkeypatch
):
    """Chốt chặn chống vòng lặp tự nuôi: cảnh báo hết tiền mà lại gửi bằng
    chính kênh tính phí thì càng hết tiền càng tiêu. `loai` của cảnh báo phải
    nằm ngoài phạm vi worker quét, và nếu ai cấu hình nhầm thì bỏ cảnh báo."""
    assert LOAI_CANH_BAO not in settings.zalo_danh_sach_loai

    monkeypatch.setattr(
        settings, "zalo_loai_bat", f"MEETING,{LOAI_CANH_BAO}", raising=False
    )
    th = TinhHinhChi(
        tin_ngay=100, tin_thang=0, don_gia=DON_GIA, tran_ngay_tin=100, tran_thang_tin=-1
    )
    truoc = await _dem_canh_bao(db_session, MUC_CHAN)

    assert await canh_bao_neu_can(db_session, th, so_cho_gui=1) is None
    assert await _dem_canh_bao(db_session, MUC_CHAN) == truoc
