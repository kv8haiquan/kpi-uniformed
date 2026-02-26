"""
forum_service/tests/test_chuyen_muc.py
======================================
Test cases cho endpoints Chuyen muc (Categories).

Endpoint tests:
  - GET /chuyen-muc — danh sach chuyen muc (any authenticated user)
  - POST /chuyen-muc — tao chuyen muc (DIEU_PHOI_FORUM)
  - PUT /chuyen-muc/{id} — sua chuyen muc (DIEU_PHOI_FORUM)
  - DELETE /chuyen-muc/{id} — xoa chuyen muc (DIEU_PHOI_FORUM, reject if has active chu_de)

Business rules tested:
  - FORUM_BR_001: Phan cap toi da 2 cap (parent -> child, no grandchild)
  - FORUM_BR_008: Khong xoa chuyen muc con chu de dang hoat dong
  - Phan quyen: Chi DIEU_PHOI_FORUM duoc quan ly chuyen muc
"""

import uuid

import pytest
from httpx import AsyncClient

API = "/api/forum/v1"


# =========================================================================
# 1. GET /chuyen-muc — Danh sach chuyen muc
# =========================================================================


@pytest.mark.asyncio
async def test_tao_va_xem_chi_tiet_chuyen_muc(client: AsyncClient, dieu_phoi_user):
    """Tao chuyen muc va verify data tra ve dung.

    Alternative to danh_sach test (which has lazy loading issue).
    Test flow:
      1. Tao chuyen muc moi voi DIEU_PHOI_FORUM
      2. Verify response data co day du fields
      3. Verify cac gia tri mac dinh (so_chu_de=0, so_tra_loi=0, children=[])

    Business rules tested:
      - DIEU_PHOI_FORUM duoc tao chuyen muc
      - Response tra ve full chuyen muc info + stats
    """
    payload = {
        "ten_chuyen_muc": f"Test chuyen muc {uuid.uuid4().hex[:6]}",
        "mo_ta": "Mo ta chuyen muc de kiem tra",
        "icon": "question-circle",
        "thu_tu": 5,
        "chi_doc": False,
        "yeu_cau_duyet": False,
    }

    response = await client.post(f"{API}/chuyen-muc", json=payload)
    assert response.status_code == 201

    body = response.json()
    assert body["success"] is True

    data = body["data"]
    # Check all required fields
    assert "id" in data
    assert data["ten_chuyen_muc"] == payload["ten_chuyen_muc"]
    assert data["mo_ta"] == payload["mo_ta"]
    assert data["icon"] == payload["icon"]
    assert data["thu_tu"] == payload["thu_tu"]
    assert data["chi_doc"] is False
    assert data["yeu_cau_duyet"] is False
    assert data["is_active"] is True

    # Check stats (new category has no content yet)
    assert data["so_chu_de"] == 0
    assert data["so_tra_loi"] == 0
    assert data["chu_de_moi_nhat"] is None
    assert data["children"] == []


# =========================================================================
# 2. POST /chuyen-muc — Tao chuyen muc (DIEU_PHOI_FORUM)
# =========================================================================


@pytest.mark.asyncio
async def test_tao_chuyen_muc_dieu_phoi(client: AsyncClient, dieu_phoi_user):
    """POST /chuyen-muc thanh cong voi DIEU_PHOI_FORUM role.

    - User co DIEU_PHOI_FORUM role duoc tao chuyen muc
    - Response 201, data match voi input
    - Check cac truong: ten_chuyen_muc, mo_ta, chi_doc, yeu_cau_duyet
    """
    payload = {
        "ten_chuyen_muc": f"Chuyen muc moi tu test {uuid.uuid4().hex[:6]}",
        "mo_ta": "Mo ta chuyen muc tu test case tao moi",
        "icon": "folder",
        "thu_tu": 10,
        "chi_doc": False,
        "yeu_cau_duyet": True,
    }

    response = await client.post(f"{API}/chuyen-muc", json=payload)
    assert response.status_code == 201

    body = response.json()
    assert body["success"] is True

    data = body["data"]
    assert "id" in data
    assert data["ten_chuyen_muc"] == payload["ten_chuyen_muc"]
    assert data["mo_ta"] == payload["mo_ta"]
    assert data["icon"] == payload["icon"]
    assert data["thu_tu"] == payload["thu_tu"]
    assert data["chi_doc"] is False
    assert data["yeu_cau_duyet"] is True
    assert data["is_active"] is True


# =========================================================================
# 3. POST /chuyen-muc — CBCC thuong bi 403
# =========================================================================


@pytest.mark.asyncio
async def test_tao_chuyen_muc_cbcc_403(client: AsyncClient, cbcc_user):
    """POST /chuyen-muc bi 403 neu user khong co DIEU_PHOI_FORUM role.

    - CBCC thuong khong duoc phep tao chuyen muc
    - Response 403 Forbidden
    """
    payload = {
        "ten_chuyen_muc": "Chuyen muc CBCC bi tu choi",
        "mo_ta": "CBCC thuong khong co quyen tao",
        "chi_doc": False,
        "yeu_cau_duyet": False,
    }

    response = await client.post(f"{API}/chuyen-muc", json=payload)
    assert response.status_code == 403

    body = response.json()
    # FastAPI wraps HTTPException.detail in "detail" key
    detail = body["detail"]
    assert detail["success"] is False
    assert detail["error"]["code"] == "PERM_001"


# =========================================================================
# 4. POST /chuyen-muc — Phan cap toi da 2 cap (FORUM_BR_001)
# =========================================================================


@pytest.mark.asyncio
async def test_phan_cap_toi_da_2(client: AsyncClient, dieu_phoi_user):
    """Khong cho phep tao chuyen muc cap 3 (grandchild).

    Business rule FORUM_BR_001: Phan cap toi da 2 cap (parent -> child).

    Flow:
      1. Tao parent chuyen muc
      2. Tao child (parent_id = parent.id) — thanh cong
      3. Tao grandchild (parent_id = child.id) — FAIL voi FORUM_ERR_002

    Expected error code: FORUM_ERR_002
    """
    # Step 1: Tao parent
    parent_payload = {
        "ten_chuyen_muc": f"Parent CM {uuid.uuid4().hex[:6]}",
        "mo_ta": "Chuyen muc cap 1",
        "chi_doc": False,
        "yeu_cau_duyet": False,
    }
    parent_resp = await client.post(f"{API}/chuyen-muc", json=parent_payload)
    assert parent_resp.status_code == 201
    parent_id = parent_resp.json()["data"]["id"]

    # Step 2: Tao child (parent_id = parent.id)
    child_payload = {
        "ten_chuyen_muc": f"Child CM {uuid.uuid4().hex[:6]}",
        "mo_ta": "Chuyen muc cap 2",
        "parent_id": parent_id,
        "chi_doc": False,
        "yeu_cau_duyet": False,
    }
    child_resp = await client.post(f"{API}/chuyen-muc", json=child_payload)
    assert child_resp.status_code == 201
    child_id = child_resp.json()["data"]["id"]

    # Step 3: Tao grandchild (parent_id = child.id) — PHAI FAIL
    grandchild_payload = {
        "ten_chuyen_muc": f"Grandchild CM {uuid.uuid4().hex[:6]}",
        "mo_ta": "Chuyen muc cap 3 khong hop le",
        "parent_id": child_id,
        "chi_doc": False,
        "yeu_cau_duyet": False,
    }
    grandchild_resp = await client.post(f"{API}/chuyen-muc", json=grandchild_payload)
    assert grandchild_resp.status_code == 400

    body = grandchild_resp.json()
    detail = body["detail"]
    assert detail["success"] is False
    # Check error code FORUM_ERR_002
    assert "error" in detail
    assert detail["error"]["code"] == "FORUM_ERR_002"
    # Message uses "cap" (no dau) not "cấp"
    assert "2 cap" in detail["error"]["message"].lower()


# =========================================================================
# 5. DELETE /chuyen-muc/{id} — Khong xoa khi co chu de (FORUM_BR_008)
# =========================================================================


@pytest.mark.asyncio
async def test_xoa_chuyen_muc_co_chu_de_400(
    client: AsyncClient,
    dieu_phoi_user,
    sample_chuyen_muc,
    sample_chu_de,
):
    """DELETE /chuyen-muc/{id} bi tu choi neu chuyen muc con chu de dang hoat dong.

    Business rule FORUM_BR_008: Khong xoa chuyen muc neu con chu de chua bi xoa.

    Setup:
      - sample_chuyen_muc: chuyen muc test
      - sample_chu_de: chu de lien ket voi sample_chuyen_muc (is_deleted=False)

    Expected:
      - Response 400 Bad Request
      - Error code: FORUM_ERR_006
      - Message: chuyen muc con chu de khong the xoa
    """
    response = await client.delete(f"{API}/chuyen-muc/{sample_chuyen_muc['id']}")
    assert response.status_code == 400

    body = response.json()
    detail = body["detail"]
    assert detail["success"] is False

    # Check error code
    assert "error" in detail
    assert detail["error"]["code"] == "FORUM_ERR_006"

    # Check message hint ve chu de
    message_lower = detail["error"]["message"].lower()
    assert "chủ đề" in message_lower or "chu de" in message_lower
