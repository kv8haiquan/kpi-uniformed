"""
Test Sổ tay số — /api/common/v1/so-tay

Test thuần túy — KHÔNG đụng DB (endpoint không dùng DatabaseDep), thư mục sổ
tay trỏ vào tmp_path nên chạy ở đâu cũng được.
Chạy: PYTHONPATH=$PWD pytest common_service/tests/test_so_tay.py -v
"""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from common_service.config import settings
from common_service.dependencies import get_current_user
from common_service.main import app
from shared.auth import TokenPayload

URL = "/api/common/v1/so-tay"


@pytest.fixture
def thu_muc(tmp_path, monkeypatch):
    """Thư mục sổ tay tạm, có sẵn Sổ tra cứu lỗi; Sổ tay KTNB chưa chép lên."""
    (tmp_path / "So_tra_cuu_loi.html").write_text(
        '<!DOCTYPE html><title>Sổ tra cứu</title><script type="application/json">'
        '{"version": "V1.0", "updated": "08/10/2026", "items": []}</script>',
        encoding="utf-8",
    )
    # Tệp nằm ngoài danh mục — không được đọc ra bằng bất kỳ mã nào
    (tmp_path.parent / "bi-mat.html").write_text("bi mat", encoding="utf-8")
    monkeypatch.setattr(settings, "so_tay_dir", str(tmp_path))
    return tmp_path


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def dang_nhap():
    """Công chức thường (không vai trò nền tảng) — sổ tay mở cho mọi công chức."""
    user = TokenPayload(
        sub="00327c43-c9a3-44d7-8306-7084e75cb2b5",
        exp=int((datetime.now(timezone.utc) + timedelta(hours=8)).timestamp()),
        type="access",
        ma_cc="TEST-00",
        vai_tro="CC",
        don_vi_id="a0000000-0000-0000-0000-000000000001",
        is_lanh_dao=False,
        platform_roles=[],
    )

    async def _override():
        return user

    app.dependency_overrides[get_current_user] = _override


class TestChuaDangNhap:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("duong_dan", ["", "/tra-cuu-loi"])
    async def test_khong_token_401(self, client, thu_muc, duong_dan):
        r = await client.get(URL + duong_dan)
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_token_sai_401(self, client, thu_muc):
        r = await client.get(URL + "/tra-cuu-loi", headers={"Authorization": "Bearer xyz"})
        assert r.status_code == 401


class TestDanhSach:
    @pytest.mark.asyncio
    async def test_doc_phien_ban_va_trang_thai(self, client, thu_muc, dang_nhap):
        r = await client.get(URL)
        assert r.status_code == 200
        ds = {x["ma"]: x for x in r.json()["data"]}
        assert set(ds) == {"kiem-tra-noi-bo", "tra-cuu-loi"}

        loi = ds["tra-cuu-loi"]
        assert loi["co_san"] is True
        assert loi["phien_ban"] == "V1.0"
        assert loi["ngay_cap_nhat"] == "08/10/2026"
        assert loi["dung_luong"] > 0

        # Chưa chép tệp lên → vẫn liệt kê, nhưng báo chưa có
        assert ds["kiem-tra-noi-bo"]["co_san"] is False

    @pytest.mark.asyncio
    async def test_khong_co_phien_ban_thi_lay_ngay_tep(self, client, thu_muc, dang_nhap):
        (thu_muc / "So-tay-kiem-tra-noi-bo.html").write_text("<html></html>", encoding="utf-8")
        r = await client.get(URL)
        ktnb = {x["ma"]: x for x in r.json()["data"]}["kiem-tra-noi-bo"]
        assert ktnb["co_san"] is True
        assert ktnb["phien_ban"] is None
        assert ktnb["ngay_cap_nhat"] == datetime.now().strftime("%d/%m/%Y")


class TestNoiDung:
    @pytest.mark.asyncio
    async def test_tra_html_inline_khong_cache(self, client, thu_muc, dang_nhap):
        r = await client.get(URL + "/tra-cuu-loi")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/html")
        assert r.headers["content-disposition"] == "inline"
        assert "no-store" in r.headers["cache-control"]
        assert '"version": "V1.0"' in r.text

    @pytest.mark.asyncio
    async def test_chua_chep_tep_404(self, client, thu_muc, dang_nhap):
        r = await client.get(URL + "/kiem-tra-noi-bo")
        assert r.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "ma", ["khong-ton-tai", "So_tra_cuu_loi.html", "..%2Fbi-mat.html", "..%2F..%2Fetc%2Fpasswd"]
    )
    async def test_ma_ngoai_danh_muc_404(self, client, thu_muc, dang_nhap, ma):
        r = await client.get(f"{URL}/{ma}")
        assert r.status_code == 404
        assert "bi mat" not in r.text
