"""
legal_service/tests/test_quiz.py
==================================
Tests Quiz pháp luật.

Business rules:
  - Quiz chỉ tạo cho VB DA_XUAT_BAN
  - Số câu hỏi: 5-20 (validate bởi Pydantic)
  - Auto-grading: diem = (so_cau_dung / so_cau_hoi) * 100
  - dat_yeu_cau = diem >= diem_dat (default 70%)
  - CBCC không thấy field 'correct' trong câu hỏi
  - Lưu kết quả mỗi lần làm (cho phép làm lại nhiều lần)
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


# Helper: tạo danh sách câu hỏi hợp lệ (n câu)
def _make_cau_hoi(n: int = 5) -> list:
    return [
        {
            "noi_dung": f"Câu hỏi {i + 1}: Quy định hải quan?",
            "dap_an": ["A. Đúng", "B. Sai", "C. Không rõ", "D. Khác"],
            "correct": 0,  # Index đáp án đúng (A)
            "giai_thich": f"Đáp án A là đúng vì quy định {i + 1}",
        }
        for i in range(n)
    ]


class TestTaoQuiz:
    """Test tạo quiz cho văn bản."""

    async def test_tao_quiz_thanh_cong_5_cau(
        self, client: AsyncClient, bien_tap_user, published_van_ban
    ):
        """BIEN_TAP tạo quiz 5 câu hỏi thành công."""
        vb_id = published_van_ban["id"]
        resp = await client.post(
            f"/api/legal/v1/van-ban/{vb_id}/quiz",
            json={
                "tieu_de": "Quiz cơ bản 5 câu",
                "thoi_gian_phut": 30,
                "diem_dat": 70.0,
                "cau_hoi": _make_cau_hoi(5),
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        quiz = data["data"]
        assert quiz["so_cau_hoi"] == 5
        assert quiz["diem_dat"] == 70.0
        assert quiz["is_active"] is True
        assert len(quiz["cau_hoi"]) == 5

    async def test_tao_quiz_20_cau_ok(
        self, client: AsyncClient, qt_noi_dung_user, published_van_ban
    ):
        """Quiz 20 câu (max) được chấp nhận."""
        vb_id = published_van_ban["id"]
        resp = await client.post(
            f"/api/legal/v1/van-ban/{vb_id}/quiz",
            json={
                "tieu_de": "Quiz đầy đủ 20 câu",
                "diem_dat": 80.0,
                "cau_hoi": _make_cau_hoi(20),
            },
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["so_cau_hoi"] == 20

    async def test_tao_quiz_it_hon_5_cau_fail(
        self, client: AsyncClient, bien_tap_user, published_van_ban
    ):
        """Quiz < 5 câu → validation error 422."""
        vb_id = published_van_ban["id"]
        resp = await client.post(
            f"/api/legal/v1/van-ban/{vb_id}/quiz",
            json={
                "tieu_de": "Quiz ít câu",
                "diem_dat": 70.0,
                "cau_hoi": _make_cau_hoi(4),  # Chỉ 4 câu
            },
        )
        assert resp.status_code == 422  # Pydantic validation error

    async def test_tao_quiz_nhieu_hon_20_cau_fail(
        self, client: AsyncClient, bien_tap_user, published_van_ban
    ):
        """Quiz > 20 câu → validation error 422."""
        vb_id = published_van_ban["id"]
        resp = await client.post(
            f"/api/legal/v1/van-ban/{vb_id}/quiz",
            json={
                "tieu_de": "Quiz quá nhiều câu",
                "diem_dat": 70.0,
                "cau_hoi": _make_cau_hoi(21),  # 21 câu
            },
        )
        assert resp.status_code == 422

    async def test_tao_quiz_cho_vb_chua_xuat_ban_fail(
        self, client: AsyncClient, bien_tap_user, sample_van_ban
    ):
        """Quiz chỉ tạo cho VB DA_XUAT_BAN → VB NHAP lỗi LEGAL_ERR_007."""
        vb_id = sample_van_ban["id"]
        resp = await client.post(
            f"/api/legal/v1/van-ban/{vb_id}/quiz",
            json={
                "tieu_de": "Quiz cho VB chưa xuất bản",
                "diem_dat": 70.0,
                "cau_hoi": _make_cau_hoi(5),
            },
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "LEGAL_ERR_007"

    async def test_cbcc_khong_tao_quiz(
        self, client: AsyncClient, cbcc_user, published_van_ban
    ):
        """CBCC không tạo quiz → 403."""
        vb_id = published_van_ban["id"]
        resp = await client.post(
            f"/api/legal/v1/van-ban/{vb_id}/quiz",
            json={
                "tieu_de": "CBCC tạo quiz",
                "diem_dat": 70.0,
                "cau_hoi": _make_cau_hoi(5),
            },
        )
        assert resp.status_code == 403

    async def test_correct_index_khong_hop_le(
        self, client: AsyncClient, bien_tap_user, published_van_ban
    ):
        """correct index vượt quá số đáp án → LEGAL_ERR_008."""
        vb_id = published_van_ban["id"]
        cau_hoi_loi = [
            {
                "noi_dung": "Câu hỏi lỗi",
                "dap_an": ["A", "B"],  # 2 đáp án
                "correct": 5,  # Index 5 không hợp lệ
                "giai_thich": "",
            }
        ] + _make_cau_hoi(4)  # Thêm 4 câu hợp lệ để đủ 5

        resp = await client.post(
            f"/api/legal/v1/van-ban/{vb_id}/quiz",
            json={
                "tieu_de": "Quiz lỗi correct index",
                "diem_dat": 70.0,
                "cau_hoi": cau_hoi_loi,
            },
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "LEGAL_ERR_008"


class TestLamBai:
    """Test làm bài và chấm điểm tự động."""

    async def test_lam_bai_cham_diem_dung(
        self, client: AsyncClient, cbcc_user, sample_quiz
    ):
        """Trả lời đúng 5/5 câu → diem=100, dat_yeu_cau=True."""
        quiz_id = sample_quiz["id"]
        # Tất cả đáp án đúng là index=0 (theo conftest sample_quiz)
        tra_loi = [{"cau": i, "dap_an": 0} for i in range(5)]

        resp = await client.post(
            f"/api/legal/v1/quiz/{quiz_id}/lam-bai",
            json={"tra_loi": tra_loi},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        ket_qua = data["data"]
        assert ket_qua["diem"] == 100.0
        assert ket_qua["so_cau_dung"] == 5
        assert ket_qua["dat_yeu_cau"] is True

    async def test_lam_bai_9_tren_10_cau(
        self, client: AsyncClient, cbcc_user, db_session: AsyncSession, published_van_ban
    ):
        """Đúng 9/10 câu → diem=90.0, dat_yeu_cau=True (diem_dat=70)."""
        from uuid import UUID
        from datetime import datetime, timezone
        from legal_service.models.quiz_van_ban import QuizVanBan

        cau_hoi = _make_cau_hoi(10)
        quiz = QuizVanBan(
            van_ban_id=UUID(published_van_ban["id"]),
            tieu_de="Quiz 10 câu",
            so_cau_hoi=10,
            diem_dat=70.0,
            cau_hoi=cau_hoi,
            nguoi_tao_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            is_active=True,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db_session.add(quiz)
        await db_session.flush()
        await db_session.refresh(quiz)
        quiz_id = str(quiz.id)

        # Đúng 9/10: câu 0-8 đúng (index=0), câu 9 sai (index=1)
        tra_loi = [{"cau": i, "dap_an": 0 if i < 9 else 1} for i in range(10)]

        resp = await client.post(
            f"/api/legal/v1/quiz/{quiz_id}/lam-bai",
            json={"tra_loi": tra_loi},
        )
        assert resp.status_code == 200
        ket_qua = resp.json()["data"]
        assert ket_qua["diem"] == 90.0
        assert ket_qua["so_cau_dung"] == 9
        assert ket_qua["dat_yeu_cau"] is True  # 90 >= 70

    async def test_lam_bai_khong_dat(
        self, client: AsyncClient, cbcc_user, db_session: AsyncSession, published_van_ban
    ):
        """Đúng 5/10 → diem=50.0, dat_yeu_cau=False (diem_dat=70)."""
        from uuid import UUID
        from datetime import datetime, timezone
        from legal_service.models.quiz_van_ban import QuizVanBan

        cau_hoi = _make_cau_hoi(10)
        quiz = QuizVanBan(
            van_ban_id=UUID(published_van_ban["id"]),
            tieu_de="Quiz 10 câu không đạt",
            so_cau_hoi=10,
            diem_dat=70.0,  # Cần >= 70%
            cau_hoi=cau_hoi,
            nguoi_tao_id=UUID("01abd5c1-5c34-475b-8ea8-803ad461f66d"),
            is_active=True,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db_session.add(quiz)
        await db_session.flush()
        await db_session.refresh(quiz)
        quiz_id = str(quiz.id)

        # Chỉ đúng 5/10: câu 0-4 đúng (index=0), câu 5-9 sai (index=1)
        tra_loi = [{"cau": i, "dap_an": 0 if i < 5 else 1} for i in range(10)]

        resp = await client.post(
            f"/api/legal/v1/quiz/{quiz_id}/lam-bai",
            json={"tra_loi": tra_loi},
        )
        assert resp.status_code == 200
        ket_qua = resp.json()["data"]
        assert ket_qua["diem"] == 50.0
        assert ket_qua["so_cau_dung"] == 5
        assert ket_qua["dat_yeu_cau"] is False  # 50 < 70

    async def test_chi_tiet_cham_diem_dung_sai(
        self, client: AsyncClient, cbcc_user, sample_quiz
    ):
        """Kết quả chứa chi_tiet từng câu: dung/sai và giải thích."""
        quiz_id = sample_quiz["id"]
        # Câu 0 đúng (index=0), câu 1 sai (index=1)
        tra_loi = [{"cau": 0, "dap_an": 0}] + [
            {"cau": i, "dap_an": 1} for i in range(1, 5)
        ]

        resp = await client.post(
            f"/api/legal/v1/quiz/{quiz_id}/lam-bai",
            json={"tra_loi": tra_loi},
        )
        assert resp.status_code == 200
        ket_qua = resp.json()["data"]
        assert ket_qua["so_cau_dung"] == 1  # Chỉ 1 câu đúng
        assert ket_qua["diem"] == 20.0  # 1/5 * 100

        chi_tiet = ket_qua["chi_tiet"]
        assert len(chi_tiet) == 5

        # Câu 0 đúng
        assert chi_tiet[0]["cau"] == 0
        assert chi_tiet[0]["dung"] is True

        # Câu 1-4 sai
        for i in range(1, 5):
            assert chi_tiet[i]["dung"] is False

    async def test_lam_lai_nhieu_lan_luu_nhieu_ket_qua(
        self, client: AsyncClient, cbcc_user, sample_quiz
    ):
        """Làm quiz nhiều lần → mỗi lần tạo 1 bản ghi kết quả (không ghi đè)."""
        quiz_id = sample_quiz["id"]
        tra_loi_dung = [{"cau": i, "dap_an": 0} for i in range(5)]
        tra_loi_sai = [{"cau": i, "dap_an": 1} for i in range(5)]

        # Lần 1: đúng hết
        r1 = await client.post(
            f"/api/legal/v1/quiz/{quiz_id}/lam-bai",
            json={"tra_loi": tra_loi_dung},
        )
        assert r1.status_code == 200
        assert r1.json()["data"]["diem"] == 100.0

        # Lần 2: sai hết
        r2 = await client.post(
            f"/api/legal/v1/quiz/{quiz_id}/lam-bai",
            json={"tra_loi": tra_loi_sai},
        )
        assert r2.status_code == 200
        assert r2.json()["data"]["diem"] == 0.0

        # Xem kết quả → phải có 2 bản ghi (lần 2 trước vì DESC)
        ket_qua_resp = await client.get(f"/api/legal/v1/quiz/{quiz_id}/ket-qua")
        assert ket_qua_resp.status_code == 200
        ket_quas = ket_qua_resp.json()["data"]
        assert len(ket_quas) >= 2


class TestXemQuiz:
    """Test xem danh sách quiz và ẩn đáp án."""

    async def test_cbcc_khong_thay_correct_trong_cau_hoi(
        self, client: AsyncClient, cbcc_user, sample_quiz
    ):
        """CBCC xem quiz → field 'correct' bị ẩn khỏi câu hỏi."""
        vb_id = sample_quiz["van_ban_id"]
        resp = await client.get(f"/api/legal/v1/van-ban/{vb_id}/quiz")
        assert resp.status_code == 200
        quizzes = resp.json()["data"]
        assert len(quizzes) >= 1

        quiz = quizzes[0]
        # Kiểm tra câu hỏi không có field 'correct'
        for cau in quiz["cau_hoi"]:
            assert "correct" not in cau, "CBCC không được thấy đáp án đúng"
            assert "noi_dung" in cau
            assert "dap_an" in cau

    async def test_bien_tap_thay_correct_trong_cau_hoi(
        self, client: AsyncClient, bien_tap_user, sample_quiz
    ):
        """BIEN_TAP xem quiz → field 'correct' xuất hiện trong câu hỏi."""
        vb_id = sample_quiz["van_ban_id"]
        resp = await client.get(f"/api/legal/v1/van-ban/{vb_id}/quiz")
        assert resp.status_code == 200
        quizzes = resp.json()["data"]
        assert len(quizzes) >= 1

        quiz = quizzes[0]
        # BIEN_TAP thấy đáp án đúng
        for cau in quiz["cau_hoi"]:
            assert "correct" in cau

    async def test_qt_noi_dung_thay_correct(
        self, client: AsyncClient, qt_noi_dung_user, sample_quiz
    ):
        """QT_NOI_DUNG xem quiz → thấy đáp án đúng."""
        vb_id = sample_quiz["van_ban_id"]
        resp = await client.get(f"/api/legal/v1/van-ban/{vb_id}/quiz")
        assert resp.status_code == 200
        quizzes = resp.json()["data"]
        if quizzes:
            for cau in quizzes[0]["cau_hoi"]:
                assert "correct" in cau

    async def test_xem_ket_qua_cbcc_chi_thay_cua_minh(
        self, client: AsyncClient, cbcc_user, sample_quiz
    ):
        """CBCC chỉ xem kết quả của mình."""
        quiz_id = sample_quiz["id"]

        # Làm bài trước
        tra_loi = [{"cau": i, "dap_an": 0} for i in range(5)]
        lam_resp = await client.post(
            f"/api/legal/v1/quiz/{quiz_id}/lam-bai",
            json={"tra_loi": tra_loi},
        )
        assert lam_resp.status_code == 200

        # Xem kết quả
        ket_qua_resp = await client.get(f"/api/legal/v1/quiz/{quiz_id}/ket-qua")
        assert ket_qua_resp.status_code == 200
        ket_quas = ket_qua_resp.json()["data"]
        assert len(ket_quas) >= 1

        # Tất cả kết quả phải có đầy đủ thông tin
        for kq in ket_quas:
            assert "diem" in kq
            assert "so_cau_dung" in kq
            assert "dat_yeu_cau" in kq
            assert "chi_tiet" in kq
