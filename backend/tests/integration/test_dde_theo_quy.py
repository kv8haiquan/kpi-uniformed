"""
tests/integration/test_dde_theo_quy.py
======================================
Tests cho việc chuyển kê khai d/đ/e của LÃNH ĐẠO từ THÁNG sang QUÝ
(Mẫu 02B kèm Công văn 21169/CHQ-TCCB, áp dụng từ quý III/2026).

Chạy trên kpi_haiquan_test — TUYỆT ĐỐI KHÔNG chạy trên kpi_haiquan (prod):
    DB_NAME=kpi_haiquan_test pytest tests/integration/test_dde_theo_quy.py -v

Phạm vi:
1. Hàm thuần — mốc kỳ, tháng neo, nhãn kỳ.
2. KHÔNG HỒI TỐ kỳ cũ — quý I/II/2026 vẫn đọc đúng bản ghi từng tháng và điểm
   quý của lãnh đạo không đổi (đo trên dữ liệu thật, chỉ đọc).
3. Quý III/2026 — điểm của cả 54 lãnh đạo trước và sau thay đổi phải giống hệt
   (phép đo ngày 28/09: 2 bản T7 lệch so với T9 nhưng không ai đổi điểm).
4. Neo đúng chỗ — kê ở tháng nào trong quý cũng ghi vào bản ghi tháng cuối quý,
   ba tháng đọc ra cùng giá trị.
5. Bỏ MIN ba tháng — d/đ/e quý = giá trị trên phiếu quý.
6. Chốt chặn — duyệt/trả lại trên bản ghi không phải tháng neo bị từ chối.
"""

from __future__ import annotations

from uuid import UUID

import pytest
from fastapi import HTTPException
from sqlalchemy import select, text

from app.api.v1.endpoints.danh_gia_lanh_dao import (
    _chan_neu_khong_phai_thang_neo_dde,
    create_or_update_dde,
)
from app.api.v1.endpoints.xep_loai_quy_helpers import _lay_dde_thang, tinh_diem_quy
from app.core import ky_tieu_chi as K
from app.core.kpi_lanh_dao_v2 import _get_dde as _lay_dde_v2
from app.db.session import AsyncSessionLocal
from app.models.leader_kpi import DanhGiaDDE
from app.models.user_org import CongChuc
from app.schemas.leader_kpi import DanhGiaDDECreate

NAM_TEST = 2026
QUY_TEST = 3
THANG_NEO_TEST = 9


# =============================================================================
# 1. Hàm thuần — mốc kỳ và tháng neo
# =============================================================================

def test_moc_ky_dde_dung_theo_cong_van():
    """Q2/2026 trở về trước kê theo tháng; Q3/2026 trở đi kê theo quý."""
    assert K.DDE_THEO_QUY_TU == (2026, 3)

    for thang in (1, 4, 5, 6):
        assert K.dde_theo_quy(thang, 2026) is False
        assert K.thang_neo_dde(thang, 2026) == thang
        assert K.la_thang_neo_dde(thang, 2026) is True
        assert K.cac_thang_ap_dung_dde(thang, 2026) == [thang]
        assert K.nhan_ky_dde(thang, 2026) == f"Tháng {thang}/2026"
    assert K.dde_theo_quy(12, 2025) is False

    for thang in (7, 8, 9):
        assert K.dde_theo_quy(thang, 2026) is True
        assert K.thang_neo_dde(thang, 2026) == 9
        assert K.cac_thang_ap_dung_dde(thang, 2026) == [7, 8, 9]
        assert K.nhan_ky_dde(thang, 2026) == "Quý 3/2026"
    assert K.la_thang_neo_dde(7, 2026) is False
    assert K.la_thang_neo_dde(9, 2026) is True
    assert K.thang_neo_dde(10, 2026) == 12
    assert K.thang_neo_dde(1, 2027) == 3


def test_thong_tin_ky_dde():
    ky = K.thong_tin_ky_dde(7, 2026)
    assert ky["ky"] == "QUY"
    assert ky["quy"] == 3
    assert ky["thang_neo"] == 9
    assert ky["cac_thang_ap_dung"] == [7, 8, 9]

    ky_cu = K.thong_tin_ky_dde(5, 2026)
    assert ky_cu["ky"] == "THANG"
    assert ky_cu["thang_neo"] == 5
    assert ky_cu["cac_thang_ap_dung"] == [5]


# =============================================================================
# 2. KHÔNG HỒI TỐ — kỳ cũ đọc đúng bản ghi tháng đó (dữ liệu thật, chỉ đọc)
# =============================================================================

@pytest.mark.asyncio
async def test_ky_cu_doc_dung_ban_ghi_thang_do():
    """
    Với mọi kỳ trước Q3/2026, `_lay_dde_thang` và `_lay_dde` (engine tháng V2)
    phải trả về ĐÚNG d/đ/e của chính tháng đó.
    """
    async with AsyncSessionLocal() as db:
        da_kiem_tra = 0
        for thang in (1, 2, 3, 4, 5, 6):
            rows = (await db.execute(text("""
                SELECT cong_chuc_id,
                       COALESCE(d_phe_duyet, d_ket_qua_don_vi),
                       COALESCE(dd_phe_duyet, dd_to_chuc_trien_khai),
                       COALESCE(e_phe_duyet, e_doan_ket_noi_bo)
                FROM danh_gia_dde
                WHERE thang = :t AND nam = 2026 AND trang_thai = 'DA_PHE_DUYET'
                ORDER BY cong_chuc_id
            """), {"t": thang})).all()

            for cc_id, d_goc, dd_goc, e_goc in rows:
                dde = await _lay_dde_thang(db, cc_id, thang, 2026)
                assert dde is not None, f"CC {cc_id} tháng {thang}: resolver mất bản ghi"
                assert dde["d"] == float(d_goc) / 100
                assert dde["dd"] == float(dd_goc) / 100
                assert dde["e"] == float(e_goc) / 100

                d_v2, dd_v2, e_v2 = await _lay_dde_v2(db, cc_id, thang, 2026)
                assert (d_v2, dd_v2, e_v2) == (
                    float(d_goc) / 100, float(dd_goc) / 100, float(e_goc) / 100
                )
                da_kiem_tra += 1

        assert da_kiem_tra >= 20, f"Mẫu đối chiếu quá nhỏ ({da_kiem_tra} bản)"


@pytest.mark.asyncio
async def test_diem_quy_ky_cu_van_lay_min_ba_thang():
    """
    Kỳ trước mốc giữ nguyên quy ước MIN ba tháng: dựng lại MIN bằng SQL rồi
    đối chiếu với d/đ/e mà `tinh_diem_quy` trả ra.
    """
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(text("""
            SELECT cong_chuc_id,
                   MIN(COALESCE(d_phe_duyet, d_ket_qua_don_vi))       AS d_min,
                   MIN(COALESCE(dd_phe_duyet, dd_to_chuc_trien_khai)) AS dd_min,
                   MIN(COALESCE(e_phe_duyet, e_doan_ket_noi_bo))      AS e_min,
                   count(*)                                          AS so_thang
            FROM danh_gia_dde
            WHERE nam = 2026 AND thang IN (4, 5, 6) AND trang_thai = 'DA_PHE_DUYET'
            GROUP BY cong_chuc_id
            HAVING count(*) = 3
            LIMIT 10
        """))).all()
        if not rows:
            pytest.skip("DB test không có LĐ nào đủ 3 tháng d/đ/e quý II/2026")

        for cc_id, d_min, dd_min, e_min, _ in rows:
            kq = await tinh_diem_quy(db, cc_id, 2, 2026, tam_tinh=False)
            if kq is None:
                continue
            ct = kq  # metrics nằm ở cấp gốc của kết quả
            assert ct["d_ket_qua"] == float(d_min) / 100, f"CC {cc_id}: d quý II lệch"
            assert ct["e_doan_ket"] == float(e_min) / 100, f"CC {cc_id}: e quý II lệch"
            # đ có thể được nâng bởi miếng vá "kê khai lại đ cấp quý" → chỉ ≥ MIN
            assert ct["dd_to_chuc"] >= float(dd_min) / 100


# =============================================================================
# 3. Quý III/2026 — hồi tố KHÔNG làm ai đổi điểm
# =============================================================================

@pytest.mark.asyncio
async def test_hoi_to_quy_3_khong_ai_doi_diem():
    """
    So MIN ba tháng (cách cũ) với giá trị phiếu quý (cách mới) cho TOÀN BỘ lãnh
    đạo có d/đ/e trong quý III. Theo phép đo 28/09 phải không ai lệch; ai lệch
    thì test in ra để dừng lại xem xét.
    """
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(text("""
            SELECT cong_chuc_id,
                   MIN(COALESCE(d_phe_duyet, d_ket_qua_don_vi))       AS d_min,
                   MIN(COALESCE(dd_phe_duyet, dd_to_chuc_trien_khai)) AS dd_min,
                   MIN(COALESCE(e_phe_duyet, e_doan_ket_noi_bo))      AS e_min
            FROM danh_gia_dde
            WHERE nam = 2026 AND thang IN (7, 8, 9) AND trang_thai = 'DA_PHE_DUYET'
            GROUP BY cong_chuc_id
        """))).all()
        if not rows:
            pytest.skip("DB test không có d/đ/e quý III/2026 đã duyệt")

        lech = []
        for cc_id, d_min, dd_min, e_min in rows:
            dde_quy = await _lay_dde_thang(db, cc_id, 7, NAM_TEST)  # đọc xuyên → T9
            d_moi = dde_quy["d"] if dde_quy else 1.0
            dd_moi = dde_quy["dd"] if dde_quy else 1.0
            e_moi = dde_quy["e"] if dde_quy else 1.0
            cu = (float(d_min) / 100, float(dd_min) / 100, float(e_min) / 100)
            if (d_moi, dd_moi, e_moi) != cu:
                lech.append((str(cc_id), cu, (d_moi, dd_moi, e_moi)))

        assert not lech, (
            "Hồi tố quý III làm đổi d/đ/e của các lãnh đạo sau "
            f"(cũ → mới): {lech}"
        )


# =============================================================================
# Helpers cho các test ghi dữ liệu
# =============================================================================

async def _pick_ld_sach(db) -> CongChuc:
    """Lãnh đạo CHƯA có bản ghi d/đ/e nào trong quý III/2026."""
    row = (await db.execute(text("""
        SELECT cc.id FROM cong_chuc cc
        JOIN vai_tro vt ON cc.vai_tro_id = vt.id
        WHERE cc.is_lanh_dao = true AND cc.is_active = true AND cc.is_deleted = false
          AND vt.cap_bac IN ('TRUONG_DON_VI', 'PHO_DON_VI')
          AND NOT EXISTS (
              SELECT 1 FROM danh_gia_dde dd
              WHERE dd.cong_chuc_id = cc.id AND dd.nam = :n AND dd.thang IN (7, 8, 9)
          )
        LIMIT 1
    """), {"n": NAM_TEST})).first()
    assert row, "Không tìm thấy lãnh đạo chưa có d/đ/e quý III/2026 trong DB test"
    return (await db.execute(
        select(CongChuc).where(CongChuc.id == row[0])
    )).scalar_one()


async def _cleanup_dde_quy(db, cong_chuc_id: UUID) -> None:
    await db.execute(text("""
        DELETE FROM danh_gia_dde
        WHERE cong_chuc_id = :cc AND nam = :n AND thang IN (7, 8, 9)
    """), {"cc": str(cong_chuc_id), "n": NAM_TEST})
    await db.commit()


def _payload(thang: int, d: bool = True, dd: bool = True, e: bool = True) -> DanhGiaDDECreate:
    return DanhGiaDDECreate(
        thang=thang, nam=NAM_TEST,
        d_ket_qua_don_vi=d, dd_to_chuc_trien_khai=dd, e_doan_ket_noi_bo=e,
        d_ghi_chu=None if d else "test",
        dd_ghi_chu=None if dd else "test",
        e_ghi_chu=None if e else "test",
    )


# =============================================================================
# 4. Neo đúng chỗ + ba tháng đọc ra cùng giá trị
# =============================================================================

@pytest.mark.asyncio
async def test_ke_thang_bat_ky_trong_quy_ghi_vao_thang_neo():
    """Kê ở tháng 7 → bản ghi nằm ở tháng 9, cờ la_phieu_dde_quy bật."""
    async with AsyncSessionLocal() as db:
        ld = await _pick_ld_sach(db)
        await _cleanup_dde_quy(db, ld.id)
        try:
            await create_or_update_dde(db, ld, _payload(thang=7, d=False))
            await db.commit()

            rows = (await db.execute(
                select(DanhGiaDDE)
                .where(DanhGiaDDE.cong_chuc_id == ld.id)
                .where(DanhGiaDDE.nam == NAM_TEST)
                .where(DanhGiaDDE.thang.in_([7, 8, 9]))
            )).scalars().all()

            assert len(rows) == 1, f"Phải chỉ có MỘT phiếu cho cả quý, đang có {len(rows)}"
            assert rows[0].thang == THANG_NEO_TEST
            assert rows[0].la_phieu_dde_quy is True
            assert rows[0].d_ket_qua_don_vi == 50
        finally:
            await _cleanup_dde_quy(db, ld.id)


@pytest.mark.asyncio
async def test_ba_thang_doc_ra_cung_mot_phieu():
    """Kê một lần ở tháng 8 → tháng 7, 8, 9 đọc ra cùng giá trị."""
    async with AsyncSessionLocal() as db:
        ld = await _pick_ld_sach(db)
        await _cleanup_dde_quy(db, ld.id)
        try:
            await create_or_update_dde(db, ld, _payload(thang=8, dd=False))
            await db.execute(text("""
                UPDATE danh_gia_dde SET trang_thai = 'DA_PHE_DUYET'
                WHERE cong_chuc_id = :cc AND nam = :n AND thang = 9
            """), {"cc": str(ld.id), "n": NAM_TEST})
            await db.commit()

            for thang in (7, 8, 9):
                dde = await _lay_dde_thang(db, ld.id, thang, NAM_TEST)
                assert dde is not None, f"Tháng {thang} không đọc được phiếu quý"
                assert (dde["d"], dde["dd"], dde["e"]) == (1.0, 0.5, 1.0)

                # Engine điểm THÁNG của lãnh đạo cũng phải đọc cùng phiếu
                assert await _lay_dde_v2(db, ld.id, thang, NAM_TEST) == (1.0, 0.5, 1.0)
        finally:
            await _cleanup_dde_quy(db, ld.id)


# =============================================================================
# 5. Bỏ MIN ba tháng — d/đ/e quý lấy thẳng phiếu quý
# =============================================================================

@pytest.mark.asyncio
async def test_diem_quy_lay_thang_phieu_quy_khong_con_min():
    """
    Dựng bản tháng 7 có d = 50% (số liệu cũ) và phiếu quý (tháng 9) d = 100%.
    Cách cũ (MIN) sẽ ra 50%; cách mới phải ra 100% theo phiếu quý.
    """
    async with AsyncSessionLocal() as db:
        ld = await _pick_ld_sach(db)
        await _cleanup_dde_quy(db, ld.id)
        try:
            await db.execute(text("""
                INSERT INTO danh_gia_dde
                    (id, cong_chuc_id, thang, nam,
                     d_ket_qua_don_vi, dd_to_chuc_trien_khai, e_doan_ket_noi_bo,
                     trang_thai, la_phieu_dde_quy)
                VALUES
                    (gen_random_uuid(), :cc, 7, :n, 50, 50, 50, 'DA_PHE_DUYET', false),
                    (gen_random_uuid(), :cc, 9, :n, 100, 100, 100, 'DA_PHE_DUYET', true)
            """), {"cc": str(ld.id), "n": NAM_TEST})
            await db.commit()

            for thang in (7, 8, 9):
                dde = await _lay_dde_thang(db, ld.id, thang, NAM_TEST)
                assert (dde["d"], dde["dd"], dde["e"]) == (1.0, 1.0, 1.0), (
                    f"Tháng {thang} vẫn đọc bản cũ thay vì phiếu quý"
                )

            kq = await tinh_diem_quy(db, ld.id, QUY_TEST, NAM_TEST, tam_tinh=True)
            assert kq is not None
            ct = kq  # metrics nằm ở cấp gốc của kết quả
            assert ct["d_ket_qua"] == 1.0, "d quý vẫn bị kéo xuống bởi MIN ba tháng"
            assert ct["e_doan_ket"] == 1.0, "e quý vẫn bị kéo xuống bởi MIN ba tháng"
            assert ct["dd_to_chuc"] == 1.0, "đ quý vẫn bị kéo xuống bởi MIN ba tháng"
        finally:
            await _cleanup_dde_quy(db, ld.id)


# =============================================================================
# 6. Chốt chặn — không thao tác trên bản ghi không phải tháng neo
# =============================================================================

def test_chan_thao_tac_tren_ban_ghi_khong_phai_thang_neo():
    """Bản tháng 7/2026 (kỳ quý) bị chặn; bản tháng 9 và bản kỳ cũ thì không."""
    ban_thang_7 = DanhGiaDDE(thang=7, nam=NAM_TEST)
    with pytest.raises(HTTPException) as exc:
        _chan_neu_khong_phai_thang_neo_dde(ban_thang_7)
    assert exc.value.status_code == 400
    assert exc.value.detail["error"]["code"] == "BIZ_008"

    # Tháng neo của kỳ quý — cho qua
    _chan_neu_khong_phai_thang_neo_dde(DanhGiaDDE(thang=9, nam=NAM_TEST))
    # Kỳ cũ (trước mốc) — mọi tháng đều cho qua
    _chan_neu_khong_phai_thang_neo_dde(DanhGiaDDE(thang=5, nam=NAM_TEST))
    _chan_neu_khong_phai_thang_neo_dde(DanhGiaDDE(thang=11, nam=2025))
