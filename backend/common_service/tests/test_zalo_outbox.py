"""
Test tích hợp hàng đợi Zalo (common.zalo_outbox).

Chạy trên DB TEST:
    DB_NAME=kpi_haiquan_test PYTHONPATH=$PWD pytest \
        common_service/tests/test_zalo_outbox.py -v

Điểm quan trọng nhất được kiểm chứng ở đây: thông báo do HKG ghi bằng
RAW SQL (không qua Internal API của common_service) vẫn phải được worker
nhặt lên. Đó là lý do chọn kiến trúc quét bảng thay vì gắn hook lúc ghi.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from common_service.config import settings
from common_service.models.zalo import (
    BQ_DA_TU_CHOI,
    BQ_KHONG_CO_SDT,
    BQ_KHONG_CO_TEMPLATE,
    BQ_THIEU_MA_HOP,
    LK_CHUA_XAC_MINH,
    LK_TU_CHOI_NHAN,
    OB_BO_QUA,
    OB_CHO_GUI,
    OB_DA_GUI,
    ZaloLienKet,
    ZaloOutbox,
)
from common_service.services.zalo.outbox import gui_hang_doi, xep_hang

from .conftest import _REAL_CC_IDS

CC_A = uuid.UUID(_REAL_CC_IDS[0])
CC_B = uuid.UUID(_REAL_CC_IDS[1])


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def cau_hinh_zalo(monkeypatch):
    """Bật template + dry-run cho mọi test trong file này.

    Mở khung giờ gửi ra cả ngày (0h–24h) để test KHÔNG phụ thuộc giờ chạy
    thực tế: nếu để mặc định 6h–22h thì chạy test lúc đêm sẽ bị logic giờ
    yên tĩnh dời lịch và test đỏ oan. Bản thân logic giờ yên tĩnh được kiểm
    riêng bằng mốc thời gian cố định ở test_zalo_templates.py::TestKhungGioGui.
    """
    monkeypatch.setattr(settings, "zalo_loai_bat", "MEETING", raising=False)
    monkeypatch.setattr(settings, "zalo_dry_run", True, raising=False)
    monkeypatch.setattr(settings, "zalo_tpl_moi_hop", "TPL_MOI_TEST", raising=False)
    monkeypatch.setattr(settings, "zalo_tpl_nhac_hop", "TPL_NHAC_TEST", raising=False)
    monkeypatch.setattr(settings, "zalo_tpl_huy_hop", "TPL_HUY_TEST", raising=False)
    monkeypatch.setattr(settings, "zalo_cua_so_quet_phut", 120, raising=False)
    monkeypatch.setattr(settings, "zalo_khong_gui_truoc_gio", 0, raising=False)
    monkeypatch.setattr(settings, "zalo_khong_gui_sau_gio", 24, raising=False)


async def _tao_thong_bao_kieu_hkg(
    db: AsyncSession,
    nguoi_nhan_id: uuid.UUID,
    doi_tuong_type: str = "GIAY_MOI_HOP",
    loai: str = "MEETING",
    tre_phut: int = 0,
    co_doi_tuong_id: bool = True,
) -> uuid.UUID:
    """Ghi thông báo BẰNG RAW SQL — bắt chước đúng cách HKG đang làm.

    Xem meeting_service/services/notification_service.py:35 — HKG không gọi
    Internal API mà INSERT thẳng. Test phải đi đúng đường đó.
    """
    tb_id = uuid.uuid4()
    await db.execute(
        text(
            """
            INSERT INTO common.thong_bao
                (id, nguoi_nhan_id, tieu_de, noi_dung, loai,
                 link_url, doi_tuong_type, doi_tuong_id, muc_do, created_at)
            VALUES
                (:id, :nn, :td, :nd, :loai,
                 :link, :dtt, :dti, 'BINH_THUONG',
                 CURRENT_TIMESTAMP - make_interval(mins => :tre))
            """
        ),
        {
            "id": tb_id,
            "nn": nguoi_nhan_id,
            "td": "Giấy mời họp giao ban",
            "nd": "Nội dung mật không được lộ ra Zalo",
            "loai": loai,
            "link": f"/hop-khong-giay/chi-tiet/{uuid.uuid4()}",
            "dtt": doi_tuong_type,
            "dti": uuid.uuid4() if co_doi_tuong_id else None,
            "tre": tre_phut,
        },
    )
    await db.flush()
    return tb_id


async def _tao_lien_ket(
    db: AsyncSession,
    cong_chuc_id: uuid.UUID,
    so: str = "84913048358",
    da_dong_y: bool = True,
    trang_thai: str = LK_CHUA_XAC_MINH,
) -> None:
    db.add(
        ZaloLienKet(
            cong_chuc_id=cong_chuc_id,
            so_dien_thoai=so,
            so_goc=so,
            da_dong_y=da_dong_y,
            trang_thai=trang_thai,
            nguon="IMPORT_EXCEL",
        )
    )
    await db.flush()


async def _outbox_cua(db: AsyncSession, tb_id: uuid.UUID):
    kq = await db.execute(select(ZaloOutbox).where(ZaloOutbox.thong_bao_id == tb_id))
    return kq.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Xếp hàng
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestXepHang:
    async def test_bat_duoc_thong_bao_hkg_ghi_bang_raw_sql(self, db_session):
        """Kiểm chứng lựa chọn kiến trúc: quét bảng bắt được cả đường raw SQL."""
        await _tao_lien_ket(db_session, CC_A)
        tb_id = await _tao_thong_bao_kieu_hkg(db_session, CC_A)

        await xep_hang(db_session)

        ob = await _outbox_cua(db_session, tb_id)
        assert ob is not None, "Không nhặt được thông báo HKG ghi bằng raw SQL"
        assert ob.trang_thai == OB_CHO_GUI
        assert ob.template_id == "TPL_MOI_TEST"
        assert ob.so_dien_thoai == "84913048358"

    async def test_khong_lo_noi_dung_cuoc_hop_ra_template(self, db_session):
        """Chính sách chuông cửa: tham số template không chứa tiêu đề/nội dung."""
        await _tao_lien_ket(db_session, CC_A)
        tb_id = await _tao_thong_bao_kieu_hkg(db_session, CC_A)

        await xep_hang(db_session)

        ob = await _outbox_cua(db_session, tb_id)
        chuoi = str(ob.template_data)
        assert "mật" not in chuoi
        assert "giao ban" not in chuoi.lower()
        assert set(ob.template_data.keys()) <= {"ho_ten", "thoi_gian", "moc"}

    async def test_khong_co_so_thi_bo_qua_co_ly_do(self, db_session):
        """Không có liên kết → vẫn ghi outbox để trả lời được 'vì sao không nhận'."""
        tb_id = await _tao_thong_bao_kieu_hkg(db_session, CC_B)

        await xep_hang(db_session)

        ob = await _outbox_cua(db_session, tb_id)
        assert ob is not None
        assert ob.trang_thai == OB_BO_QUA
        assert ob.ly_do_bo_qua == BQ_KHONG_CO_SDT

    async def test_nguoi_tu_choi_nhan_thi_bo_qua(self, db_session):
        """Cờ opt-out theo Nghị định 13/2023 phải được tôn trọng."""
        await _tao_lien_ket(db_session, CC_A, da_dong_y=False)
        tb_id = await _tao_thong_bao_kieu_hkg(db_session, CC_A)

        await xep_hang(db_session)

        ob = await _outbox_cua(db_session, tb_id)
        assert ob.trang_thai == OB_BO_QUA
        assert ob.ly_do_bo_qua == BQ_DA_TU_CHOI

    async def test_trang_thai_tu_choi_cung_bi_chan(self, db_session):
        await _tao_lien_ket(db_session, CC_A, trang_thai=LK_TU_CHOI_NHAN)
        tb_id = await _tao_thong_bao_kieu_hkg(db_session, CC_A)

        await xep_hang(db_session)

        ob = await _outbox_cua(db_session, tb_id)
        assert ob.trang_thai == OB_BO_QUA
        assert ob.ly_do_bo_qua == BQ_DA_TU_CHOI

    async def test_chua_cau_hinh_template_thi_bo_qua(self, db_session, monkeypatch):
        monkeypatch.setattr(settings, "zalo_tpl_moi_hop", "", raising=False)
        await _tao_lien_ket(db_session, CC_A)
        tb_id = await _tao_thong_bao_kieu_hkg(db_session, CC_A)

        await xep_hang(db_session)

        ob = await _outbox_cua(db_session, tb_id)
        assert ob.trang_thai == OB_BO_QUA
        assert ob.ly_do_bo_qua == BQ_KHONG_CO_TEMPLATE

    async def test_chi_gui_loai_da_bat(self, db_session, monkeypatch):
        """Giai đoạn 1 chỉ bật MEETING — thông báo KPI phải bị bỏ qua hoàn toàn."""
        await _tao_lien_ket(db_session, CC_A)
        tb_kpi = await _tao_thong_bao_kieu_hkg(
            db_session, CC_A, doi_tuong_type="GIAY_MOI_HOP", loai="KPI"
        )

        await xep_hang(db_session)

        assert await _outbox_cua(db_session, tb_kpi) is None

    async def test_bo_qua_thong_bao_qua_cu(self, db_session):
        """Bật tính năng lần đầu không được bắn lại 8.867 thông báo cũ."""
        await _tao_lien_ket(db_session, CC_A)
        tb_cu = await _tao_thong_bao_kieu_hkg(db_session, CC_A, tre_phut=500)

        await xep_hang(db_session)

        assert await _outbox_cua(db_session, tb_cu) is None

    async def test_chay_hai_lan_khong_tao_trung(self, db_session):
        """Chống gửi trùng — worker chạy chồng vẫn chỉ 1 bản ghi."""
        await _tao_lien_ket(db_session, CC_A)
        tb_id = await _tao_thong_bao_kieu_hkg(db_session, CC_A)

        await xep_hang(db_session)
        await xep_hang(db_session)

        kq = await db_session.execute(
            select(ZaloOutbox).where(ZaloOutbox.thong_bao_id == tb_id)
        )
        assert len(kq.scalars().all()) == 1

    async def test_ba_moc_nhac_deu_co_tham_so_moc(self, db_session):
        await _tao_lien_ket(db_session, CC_A)
        ids = {}
        for loai in ("NHAC_HOP_24H", "NHAC_HOP_1H", "NHAC_HOP_30P"):
            ids[loai] = await _tao_thong_bao_kieu_hkg(
                db_session, CC_A, doi_tuong_type=loai
            )

        await xep_hang(db_session)

        moc = set()
        for loai, tb_id in ids.items():
            ob = await _outbox_cua(db_session, tb_id)
            assert ob.template_id == "TPL_NHAC_TEST"
            moc.add(ob.template_data["moc"])
        assert len(moc) == 3, "Ba mốc nhắc phải khác nhau ở tham số moc"

    async def test_moi_hop_khong_kem_ma_hop_con_huy_hop_thi_co(self, db_session):
        """Template 620450 không khai ma_hop, 622520 thì có — thừa hay thiếu
        tham số đều bị Zalo từ chối cả tin nên phải đúng từng loại."""
        await _tao_lien_ket(db_session, CC_A)
        tb_moi = await _tao_thong_bao_kieu_hkg(
            db_session, CC_A, doi_tuong_type="GIAY_MOI_HOP"
        )
        tb_huy = await _tao_thong_bao_kieu_hkg(
            db_session, CC_A, doi_tuong_type="HUY_HOP"
        )

        await xep_hang(db_session)

        assert "ma_hop" not in (await _outbox_cua(db_session, tb_moi)).template_data
        ob_huy = await _outbox_cua(db_session, tb_huy)
        assert uuid.UUID(ob_huy.template_data["ma_hop"]), "ma_hop phải là UUID cuộc họp"

    async def test_thieu_doi_tuong_id_thi_bo_qua_thay_vi_gui_hong(self, db_session):
        """HUY_HOP không có doi_tuong_id → gửi đi chắc chắn bị từ chối.
        Chặn từ đầu để khỏi tốn 4 lần thử lại."""
        await _tao_lien_ket(db_session, CC_A)
        tb_id = await _tao_thong_bao_kieu_hkg(
            db_session, CC_A, doi_tuong_type="HUY_HOP", co_doi_tuong_id=False
        )

        await xep_hang(db_session)

        ob = await _outbox_cua(db_session, tb_id)
        assert ob.trang_thai == OB_BO_QUA
        assert ob.ly_do_bo_qua == BQ_THIEU_MA_HOP

    async def test_moi_hop_thieu_doi_tuong_id_van_gui_binh_thuong(self, db_session):
        """620450 không cần ma_hop nên thiếu doi_tuong_id không sao."""
        await _tao_lien_ket(db_session, CC_A)
        tb_id = await _tao_thong_bao_kieu_hkg(
            db_session, CC_A, doi_tuong_type="GIAY_MOI_HOP", co_doi_tuong_id=False
        )

        await xep_hang(db_session)

        assert (await _outbox_cua(db_session, tb_id)).trang_thai == OB_CHO_GUI


# ---------------------------------------------------------------------------
# Gửi
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestGuiHangDoi:
    async def test_dry_run_danh_dau_da_gui_ma_khong_goi_mang(self, db_session):
        await _tao_lien_ket(db_session, CC_A)
        tb_id = await _tao_thong_bao_kieu_hkg(db_session, CC_A)
        await xep_hang(db_session)

        thong_ke = await gui_hang_doi(db_session)

        assert thong_ke["thanh_cong"] == 1
        ob = await _outbox_cua(db_session, tb_id)
        assert ob.trang_thai == OB_DA_GUI
        assert ob.ngay_gui is not None
        assert ob.zns_message_id.startswith("dryrun-")

    async def test_khong_gui_lai_tin_da_gui(self, db_session):
        await _tao_lien_ket(db_session, CC_A)
        await _tao_thong_bao_kieu_hkg(db_session, CC_A)
        await xep_hang(db_session)

        lan_dau = await gui_hang_doi(db_session)
        assert lan_dau["gui"] == 1, "Lần đầu phải gửi thật thì test mới có nghĩa"

        lan_hai = await gui_hang_doi(db_session)
        assert lan_hai["gui"] == 0

    async def test_khong_dung_toi_ban_ghi_bo_qua(self, db_session):
        """Bản ghi BO_QUA không được đưa vào luồng gửi."""
        tb_id = await _tao_thong_bao_kieu_hkg(db_session, CC_B)
        await xep_hang(db_session)

        thong_ke = await gui_hang_doi(db_session)

        assert thong_ke["gui"] == 0
        ob = await _outbox_cua(db_session, tb_id)
        assert ob.trang_thai == OB_BO_QUA

    async def test_chua_toi_han_thi_chua_gui(self, db_session):
        """gui_sau ở tương lai (backoff / giờ yên tĩnh) thì bỏ qua vòng này."""
        await _tao_lien_ket(db_session, CC_A)
        tb_id = await _tao_thong_bao_kieu_hkg(db_session, CC_A)
        await xep_hang(db_session)

        ob = await _outbox_cua(db_session, tb_id)
        ob.gui_sau = datetime.now(timezone.utc) + timedelta(hours=2)
        await db_session.flush()

        thong_ke = await gui_hang_doi(db_session)
        assert thong_ke["gui"] == 0
