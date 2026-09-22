"""
tests/integration/test_moc_ke_khai_quy4.py
==========================================
Mốc chuyển kỳ của KÊ KHAI CÔNG VIỆC: từ 16/9/2026, kê khai thuộc quý IV
(quyết định 22/09/2026 — hồ sơ quý III phải nộp ngày 23/9 nên công việc làm sau
mốc chốt không kịp vào hồ sơ quý đó).

Chạy trên kpi_haiquan_test — KHÔNG chạy trên kpi_haiquan (prod):
    DB_NAME=kpi_haiquan_test pytest tests/integration/test_moc_ke_khai_quy4.py -v

Phạm vi CỐ Ý HẸP, các test dưới khoá lại đúng phạm vi đó:
  • Chỉ phần điểm tính từ kê khai (a/b/c) đi theo mốc ngày.
  • Điểm THÁNG 9 vẫn trọn 1–30/9.
  • Không đụng quý khác, không đụng HĐLĐ 111 (điểm từ VB714 theo tháng).
"""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import text

from app.api.v1.endpoints.xep_loai_moi import tinh_diem_kpi_70
from app.core.ky_tieu_chi import cac_thang_ke_khai_cua_quy, co_moc_chuyen_ky
from app.db.session import AsyncSessionLocal

MOC = date(2026, 9, 16)


# =============================================================================
# 1. Danh sách tháng đóng góp kê khai cho mỗi quý
# =============================================================================

def test_quy_3_cat_den_15_9_quy_4_nhan_phan_con_lai():
    q3 = cac_thang_ke_khai_cua_quy(3, 2026)
    assert q3 == [(7, None, None), (8, None, None), (9, None, date(2026, 9, 15))]

    q4 = cac_thang_ke_khai_cua_quy(4, 2026)
    assert q4 == [
        (9, MOC, None),
        (10, None, None),
        (11, None, None),
        (12, None, None),
    ]


def test_cac_quy_khac_khong_bi_dung_toi():
    """Mốc chỉ áp một lần cho Q3→Q4/2026."""
    for quy, nam in [(1, 2026), (2, 2026), (1, 2027), (3, 2027), (4, 2027), (3, 2025)]:
        ds = cac_thang_ke_khai_cua_quy(quy, nam)
        assert all(tu is None and den is None for _, tu, den in ds), (quy, nam)
        assert len(ds) == 3
        assert co_moc_chuyen_ky(quy, nam) is False

    assert co_moc_chuyen_ky(3, 2026) is True
    assert co_moc_chuyen_ky(4, 2026) is True


# =============================================================================
# 2. Tách theo ngày KHÔNG làm rơi bản kê khai nào
# =============================================================================

@pytest.mark.asyncio
async def test_hai_nua_thang_9_cong_lai_bang_tron_thang():
    """SP đến 15/9 + SP từ 16/9 = SP trọn tháng 9, với mọi công chức có dữ liệu."""
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(text("""
            SELECT DISTINCT k.cong_chuc_id
            FROM ke_khai_cong_viec k
            WHERE k.nam = 2026 AND k.thang = 9 AND k.is_deleted = false
              AND k.trang_thai = 'DA_PHE_DUYET'
            LIMIT 15
        """))).all()
        if not rows:
            pytest.skip("DB test không có kê khai tháng 9/2026 đã duyệt")

        for (cc_id,) in rows:
            tron = await tinh_diem_kpi_70(db, cc_id, 9, 2026)
            nua_dau = await tinh_diem_kpi_70(db, cc_id, 9, 2026, den_ngay=date(2026, 9, 15))
            nua_sau = await tinh_diem_kpi_70(db, cc_id, 9, 2026, tu_ngay=MOC)
            tong = float(nua_dau["sp_duoc_giao"]) + float(nua_sau["sp_duoc_giao"])
            assert abs(tong - float(tron["sp_duoc_giao"])) < 0.01, (
                f"CC {cc_id}: tách hai nửa làm rơi SP "
                f"({nua_dau['sp_duoc_giao']} + {nua_sau['sp_duoc_giao']} "
                f"≠ {tron['sp_duoc_giao']})"
            )


@pytest.mark.asyncio
async def test_ban_thieu_ngay_thuc_hien_o_lai_quy_cu():
    """
    Bản kê khai bỏ trống ngày thực hiện phải nằm ở quý GỐC, không được biến mất.
    Tháng 9/2026 có 16 bản như vậy trên dữ liệu thật.
    """
    async with AsyncSessionLocal() as db:
        row = (await db.execute(text("""
            SELECT k.cong_chuc_id, count(*) AS so_ban
            FROM ke_khai_cong_viec k
            WHERE k.nam = 2026 AND k.thang = 9 AND k.is_deleted = false
              AND k.ngay_thuc_hien IS NULL AND k.trang_thai = 'DA_PHE_DUYET'
            GROUP BY 1 LIMIT 1
        """))).first()
        if not row:
            pytest.skip("DB test không có bản thiếu ngày thực hiện ở tháng 9/2026")

        cc_id = row[0]
        nua_dau = await tinh_diem_kpi_70(db, cc_id, 9, 2026, den_ngay=date(2026, 9, 15))
        nua_sau = await tinh_diem_kpi_70(db, cc_id, 9, 2026, tu_ngay=MOC)
        tron = await tinh_diem_kpi_70(db, cc_id, 9, 2026)
        assert float(nua_dau["sp_duoc_giao"]) > 0, "Bản thiếu ngày phải ở quý III"
        assert abs(
            float(nua_dau["sp_duoc_giao"]) + float(nua_sau["sp_duoc_giao"])
            - float(tron["sp_duoc_giao"])
        ) < 0.01


# =============================================================================
# 3. Điểm THÁNG không đổi
# =============================================================================

@pytest.mark.asyncio
async def test_diem_thang_9_van_tron_thang():
    """Không truyền cửa sổ ngày → kết quả y như trước khi có mốc."""
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(text("""
            SELECT DISTINCT k.cong_chuc_id FROM ke_khai_cong_viec k
            WHERE k.nam = 2026 AND k.thang = 9 AND k.is_deleted = false
              AND k.ngay_thuc_hien >= '2026-09-16'
            LIMIT 5
        """))).all()
        if not rows:
            pytest.skip("DB test không có kê khai từ 16/9")

        for (cc_id,) in rows:
            tron = await tinh_diem_kpi_70(db, cc_id, 9, 2026, tam_tinh=True)
            nua_sau = await tinh_diem_kpi_70(db, cc_id, 9, 2026, tam_tinh=True, tu_ngay=MOC)
            # Trọn tháng phải ≥ nửa sau (vì gồm cả nửa đầu)
            assert float(tron["sp_duoc_giao"]) >= float(nua_sau["sp_duoc_giao"])


# =============================================================================
# 4. Điểm quý: tháng 9 xuất hiện ở cả hai quý, mỗi bên một nửa
# =============================================================================

@pytest.mark.asyncio
async def test_thang_9_gop_vao_ca_hai_quy():
    from app.api.v1.endpoints.xep_loai_quy_helpers import tinh_diem_quy

    async with AsyncSessionLocal() as db:
        row = (await db.execute(text("""
            SELECT k.cong_chuc_id FROM ke_khai_cong_viec k
            JOIN cong_chuc cc ON cc.id = k.cong_chuc_id
            JOIN vai_tro vt ON vt.id = cc.vai_tro_id AND vt.ma_vai_tro = 'CC'
            WHERE k.nam = 2026 AND k.thang = 9 AND k.is_deleted = false
              AND k.ngay_thuc_hien >= '2026-09-16'
            GROUP BY 1 ORDER BY count(*) DESC LIMIT 1
        """))).first()
        if not row:
            pytest.skip("DB test không có công chức nào kê khai từ 16/9")

        cc_id = row[0]
        q3 = await tinh_diem_quy(db, cc_id, 3, 2026, tam_tinh=True)
        q4 = await tinh_diem_quy(db, cc_id, 4, 2026, tam_tinh=True)

        assert [t["thang"] for t in q3["cac_thang"]] == [7, 8, 9]
        assert 9 in [t["thang"] for t in q4["cac_thang"]], (
            "Quý IV phải nhận phần tháng 9 từ 16/9"
        )
        # Tiêu chí chung quý IV vẫn chia theo 3 tháng 10/11/12, không phải 4
        assert q4["so_thang_thuc_te"] <= 3
