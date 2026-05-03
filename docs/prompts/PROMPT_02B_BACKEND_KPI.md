# PROMPT 02B — BACKEND KPI LOGIC (KÊ KHAI + PHÊ DUYỆT + XẾP LOẠI)

> **Phase:** B — Backend services và endpoints cho V2_PL3.
> **Phụ thuộc:** Phase A đã DONE (migration, model, seed PL3 đã xong).
> **Output mong đợi:** API kê khai V2, phê duyệt V2, tính KPI V2 hoạt động — tất cả V1 cũ KHÔNG bị thay đổi hành vi.

---

## Bối cảnh

Phase A đã dựng xong nền tảng DB. Phase B bây giờ implement logic backend cho V2_PL3.

**Nguyên tắc kiến trúc:**
- Code V1 cũ KHÔNG sửa nội dung. Chỉ THÊM nhánh `if version == 'V2_PL3'` ở đầu các function tính toán.
- Helper V2 đặt ở file riêng có hậu tố `_v2` (ví dụ: `kpi_calculator_v2.py`).
- Endpoint mới: route riêng `/api/ke-khai-v2/...` để dễ phân biệt và rollback.
- `Decimal` xuyên suốt mọi tính toán.

---

## Tài liệu tham chiếu

1. `IMPACT_ANALYSIS_KPI_V2_PL3.md` — đặc biệt §3 (Backend) và §6.1 (rủi ro).
2. `BUSINESS_RULES_FINAL.md` — công thức gốc.
3. `API_SPECS_v1_8_0.md` — đặc tả API hiện tại.
4. `README_BO_PROMPT_02.md` — 19 quyết định locked.

---

## 19 LOCKED DECISIONS — phase này dùng

Quyết định liên quan: **1, 2, 3, 4, 5, 10, 12, 13, 14, 17, 19, 20**.

**Tóm tắt quan trọng:**
- **(1)** Mẫu số V2 = `SUM(so_sp_goc_quy_doi)` của các bản kê khai **đã phê duyệt** trong tháng.
- **(2)** Hệ số V2 lấy thẳng từ `danh_muc_sp_cong_viec.he_so_quy_doi`.
- **(3)** Công thức trừ điểm tuyến tính GIỮ NGUYÊN.
- **(4)** KPI lãnh đạo (a, b, c, d, đ, e) GIỮ NGUYÊN.
- **(5)** Mẫu số = 0 → KPI = 0 → tự xếp D.
- **(12)** 1 tháng = 1 version, không cho mix.
- **(13)** Snapshot `he_so_quy_doi` immutable.
- **(14)** KHÔNG cho lãnh đạo override hệ số.

---

## NHIỆM VỤ

### Task B.1 — Tạo helper tính KPI V2

**File mới:** `backend/app/services/kpi_calculator_v2.py`

**Hàm chính:**

```python
from decimal import Decimal
from typing import Optional

def calculate_so_sp_goc_quy_doi_v2(
    so_luong: int,
    he_so_quy_doi: Decimal,
) -> Decimal:
    """
    V2: lấy thẳng he_so_quy_doi từ danh mục PL3.
    Không nhân với cap_do nữa.
    """
    return Decimal(str(so_luong)) * he_so_quy_doi


def calculate_sp_dat_v2(
    so_luong: int,
    he_so_quy_doi: Decimal,
    so_lan_loi: int,
) -> Decimal:
    """
    Công thức trừ điểm tuyến tính, GIỮ NGUYÊN từ V1.
    sp_dat = he_so × (so_luong - 0.25 × min(so_lan_loi, so_luong × 4))
    """
    so_luong_d = Decimal(str(so_luong))
    so_lan_loi_d = Decimal(str(so_lan_loi))
    max_loi = so_luong_d * Decimal("4")
    factor = so_luong_d - Decimal("0.25") * min(so_lan_loi_d, max_loi)
    result = he_so_quy_doi * factor
    return max(result, Decimal("0"))


def calculate_kpi_score_v2(
    tong_sp_hoan_thanh_quy_doi: Decimal,
    tong_sp_dat_cl_quy_doi: Decimal,
    tong_sp_dat_td_quy_doi: Decimal,
    tong_sp_ke_khai: Decimal,  # <-- mẫu số V2
) -> dict:
    """
    Trả về dict {a, b, c, kpi}.
    Nếu mẫu số = 0 → tất cả = 0 (LOCKED DECISION 5).
    """
    if tong_sp_ke_khai == 0:
        return {
            "a": Decimal("0"),
            "b": Decimal("0"),
            "c": Decimal("0"),
            "kpi": Decimal("0"),
            "ly_do": "MAU_SO_BANG_0",
        }
    
    a = tong_sp_hoan_thanh_quy_doi / tong_sp_ke_khai
    b = tong_sp_dat_cl_quy_doi / tong_sp_ke_khai
    c = tong_sp_dat_td_quy_doi / tong_sp_ke_khai
    kpi = (a + b + c) / Decimal("3")
    
    return {
        "a": a,
        "b": b,
        "c": c,
        "kpi": kpi,
        "ly_do": None,
    }
```

**Unit test bắt buộc:** `tests/services/test_kpi_calculator_v2.py` với các case:
- `so_luong=5, he_so=8, loi=0` → sp_dat = 40
- `so_luong=5, he_so=6.4, loi=3` → sp_dat = 27.2 (test thập phân)
- `so_luong=5, he_so=8, loi=20` → loi bị cap ở 5×4=20, sp_dat = 0
- `so_luong=1, he_so=20, loi=3` → loi cap ở 4, sp_dat = 5
- Mẫu số = 0 → return KPI = 0 với `ly_do='MAU_SO_BANG_0'`.

---

### Task B.2 — Endpoint kê khai V2

**File mới:** `backend/app/api/v1/endpoints/ke_khai_v2.py`

**Routes:**
- `POST /api/ke-khai-v2` — tạo bản kê khai mới
- `PUT /api/ke-khai-v2/{id}` — sửa bản kê khai đang ở trạng thái NHAP
- `DELETE /api/ke-khai-v2/{id}` — xoá bản kê khai (chỉ NHAP)
- `GET /api/ke-khai-v2/me` — lấy danh sách kê khai của bản thân theo tháng/năm
- `POST /api/ke-khai-v2/multi-day` — kê khai nhiều ngày (giữ tương đương V1)
- `GET /api/ke-khai-v2/thong-ke/thang` — thống kê tổng SP tháng (cho banner)

**Request body schema (POST):**

```python
class KeKhaiV2CreateRequest(BaseModel):
    danh_muc_sp_id: UUID  # phải là mục có nguon_du_lieu='PL3'
    so_luong: int = Field(..., gt=0)  # LOCKED DECISION 17: > 0 nguyên
    thang: int = Field(..., ge=1, le=12)
    nam: int = Field(..., ge=2025)
    ngay_thuc_hien: Optional[date] = None
    mo_ta_cong_viec: Optional[str] = None
    is_doi_moi_sang_tao: bool = False
    ngay_deadline: Optional[date] = None
    ngay_hoan_thanh: Optional[date] = None
    nguoi_phe_duyet_id: UUID
    
    # KHÔNG có cap_do_id, KHÔNG có he_so_thuc_te (override)
    # → LOCKED DECISION 14
```

**Validation logic:**

1. **Verify danh mục:** `danh_muc.nguon_du_lieu == 'PL3'`. Nếu là `'V1'` → reject với code `INVALID_CATALOG_VERSION`.
2. **1 tháng = 1 version (LOCKED 12):**
   - Query: `SELECT version_kekhai FROM ke_khai_cong_viec WHERE cong_chuc_id=? AND thang=? AND nam=? LIMIT 1`
   - Nếu kết quả là `'V1'` → reject với code `MIXED_VERSION_NOT_ALLOWED`, message "Tháng này đã có kê khai V1, không thể thêm kê khai V2".
3. **Snapshot fields:**
   ```python
   he_so_quy_doi_snapshot = danh_muc.he_so_quy_doi
   nhom_pl3_snapshot = danh_muc.nhom_pl3
   linh_vuc_snapshot = danh_muc.linh_vuc
   ```
4. **Tính `so_sp_goc_quy_doi`:**
   ```python
   so_sp_goc_quy_doi = calculate_so_sp_goc_quy_doi_v2(so_luong, he_so_quy_doi_snapshot)
   ```
5. **Insert** với `version_kekhai='V2_PL3'`, `cap_do_id=NULL`.
6. **Audit log:** ghi action `KE_KHAI_V2_CREATE`.

**Endpoint thống kê tháng (cho banner UI):**

```python
GET /api/ke-khai-v2/thong-ke/thang?thang=4&nam=2026
Response:
{
    "thang": 4,
    "nam": 2026,
    "version_kekhai": "V2_PL3",
    "tong_sp_da_duyet": 240.0,      # mẫu số chính thức
    "tong_sp_cho_duyet": 45.6,
    "tong_sp_du_kien": 285.6,        # tổng cộng (kể cả chờ duyệt)
    "so_kekhai_da_duyet": 12,
    "so_kekhai_cho_duyet": 3,
}
```

---

### Task B.3 — Endpoint phê duyệt V2

**File:** Mở rộng `backend/app/api/v1/endpoints/phe_duyet.py` (giữ V1 logic, thêm nhánh V2).

**Logic:**

1. Endpoint `POST /api/phe-duyet/{id}/duyet` — kiểm tra `version_kekhai`:
   - V1 → chạy logic cũ (giữ nguyên).
   - V2_PL3 → chạy hàm helper mới `apply_danh_muc_change_v2()`.
2. Helper `apply_danh_muc_change_v2()`:
   ```python
   def apply_danh_muc_change_v2(
       ke_khai: KeKhaiCongViec,
       so_loi_chat_luong: int,
       so_loi_tien_do: int,
   ) -> dict:
       """
       Tính lại sp_dat_chat_luong và sp_dat_tien_do dựa trên snapshot.
       KHÔNG đụng đến danh_muc hiện tại (snapshot final - LOCKED 13).
       """
       he_so = ke_khai.he_so_quy_doi_snapshot
       sp_dat_cl = calculate_sp_dat_v2(ke_khai.so_luong, he_so, so_loi_chat_luong)
       sp_dat_td = calculate_sp_dat_v2(ke_khai.so_luong, he_so, so_loi_tien_do)
       return {
           "sp_dat_chat_luong": sp_dat_cl,
           "sp_dat_tien_do": sp_dat_td,
       }
   ```
3. Bulk approve cũng phân nhánh tương tự.

**KHÔNG cho phép override `he_so_quy_doi`** ở bất kỳ endpoint phê duyệt nào (LOCKED 14). Reject nếu request body có field `he_so_thuc_te`.

---

### Task B.4 — Service tính điểm KPI tháng (xếp loại)

**File:** Mở rộng `backend/app/api/v1/endpoints/xep_loai_moi.py`.

**Hàm `tinh_diem_kpi_70()` hiện tại (V1):** Giữ nguyên logic. **THÊM** wrapper trên cùng:

```python
def tinh_diem_kpi_70(cong_chuc_id, thang, nam, db) -> dict:
    danh_gia = db.query(DanhGiaThang).filter(...).first()
    
    if danh_gia and danh_gia.version_tinh_diem == 'V2_PL3':
        return tinh_diem_kpi_70_v2(cong_chuc_id, thang, nam, db)
    
    # ... logic V1 cũ giữ nguyên
```

**Hàm mới `tinh_diem_kpi_70_v2()`:**

```python
def tinh_diem_kpi_70_v2(cong_chuc_id, thang, nam, db) -> dict:
    """
    V2: mẫu số = SUM(so_sp_goc_quy_doi) của các bản đã duyệt.
    """
    # 1. Lấy tất cả kê khai V2 đã duyệt
    kekhai_list = db.query(KeKhaiCongViec).filter(
        KeKhaiCongViec.cong_chuc_id == cong_chuc_id,
        KeKhaiCongViec.thang == thang,
        KeKhaiCongViec.nam == nam,
        KeKhaiCongViec.version_kekhai == 'V2_PL3',
        KeKhaiCongViec.trang_thai == 'DA_PHE_DUYET',
        KeKhaiCongViec.is_deleted == False,
    ).all()
    
    # 2. Mẫu số = tổng SP kê khai
    tong_sp_ke_khai = sum(kk.so_sp_goc_quy_doi for kk in kekhai_list)
    
    # 3. Tử số
    tong_hoan_thanh = sum(kk.so_sp_goc_quy_doi for kk in kekhai_list 
                          if kk.trang_thai_hoan_thanh in ('DUNG_HAN', 'SOM_HAN'))
    tong_dat_cl = sum(kk.sp_dat_chat_luong for kk in kekhai_list)
    tong_dat_td = sum(kk.sp_dat_tien_do for kk in kekhai_list)
    
    # 4. Tính KPI
    result = calculate_kpi_score_v2(tong_hoan_thanh, tong_dat_cl, tong_dat_td, tong_sp_ke_khai)
    
    # 5. Cache vào danh_gia_thang
    danh_gia.tong_sp_ke_khai = tong_sp_ke_khai
    danh_gia.diem_so_luong = result['a']
    danh_gia.diem_chat_luong = result['b']
    danh_gia.diem_tien_do = result['c']
    danh_gia.diem_kpi = result['kpi']
    
    # 6. LOCKED DECISION 5: mẫu số = 0 → tự xếp D
    if result['ly_do'] == 'MAU_SO_BANG_0':
        danh_gia.muc_xep_loai_tu_dong = 'D'
        # log warning
    
    return result
```

**KPI lãnh đạo (`tinh_diem_kpi_70_lanh_dao`)**: KHÔNG sửa (LOCKED 4).

---

### Task B.5 — Cập nhật danh_gia_thang khi tạo

**File:** `backend/app/services/danh_gia_service.py` (hoặc tương đương).

Khi tạo bản ghi `danh_gia_thang` cho một (CC, tháng, năm):
- Đọc kê khai đầu tiên của (CC, tháng, năm) → lấy `version_kekhai`.
- Set `danh_gia_thang.version_tinh_diem = version_kekhai`.
- Nếu chưa có kê khai nào → set theo `cong_chuc.kpi_version_pinned` hoặc default `'V1'`.

---

### Task B.6 — Endpoint helper cho frontend

**File:** Mở rộng `backend/app/api/v1/endpoints/danh_muc.py`.

**Routes mới:**

```
GET /api/danh-muc/linh-vuc
→ Trả về 15 lĩnh vực:
[
  {"ma": "I", "ten": "CÔNG TÁC QUẢN LÝ ĐIỀU HÀNH..."},
  {"ma": "II", "ten": "LĨNH VỰC HỢP TÁC QUỐC TẾ"},
  ...
]

GET /api/danh-muc/sp-cong-viec/pl3?linh_vuc=&nhom=&search=&page=&size=
→ Trả về danh sách mục PL3, có pagination, full-text search.
→ Filter:
  - linh_vuc: 'I'..'XV'
  - nhom: 1..5
  - search: full-text trên ten_cong_viec + cong_viec_chi_tiet
→ Default size=50, max size=100.

GET /api/danh-muc/sp-cong-viec/{id}
→ Detail 1 mục.

GET /api/don-vi/{id}/linh-vuc-mac-dinh
→ Trả về danh sách lĩnh vực mặc định của đơn vị (LOCKED 15: filter mềm).
→ Implementation: bảng config `don_vi_linh_vuc_mac_dinh` (don_vi_id, linh_vuc, thu_tu).
→ Nếu chưa có config → trả về tất cả 15 lĩnh vực.
```

**Bảng config:** Tạo migration phụ trong `alembic/versions/pl3_v2_006_don_vi_linh_vuc_mac_dinh.py`:

```sql
CREATE TABLE don_vi_linh_vuc_mac_dinh (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    don_vi_id UUID NOT NULL REFERENCES don_vi(id) ON DELETE CASCADE,
    linh_vuc VARCHAR(10) NOT NULL,
    thu_tu SMALLINT NOT NULL DEFAULT 0,
    UNIQUE (don_vi_id, linh_vuc)
);
CREATE INDEX idx_dvlvm_don_vi ON don_vi_linh_vuc_mac_dinh (don_vi_id);
```

(Admin sẽ config bảng này ở Phase E.)

---

### Task B.7 — Cập nhật báo cáo

**File:** `backend/app/api/v1/endpoints/bao_cao_xep_loai.py`.

Tất cả query tính toán phân nhánh theo `version_tinh_diem`:
- V1: dùng `so_ngay_lam_viec * 96` (cũ).
- V2_PL3: dùng `tong_sp_ke_khai` (cache đã tính ở Task B.4).

**KHÔNG sửa** logic xuất Mẫu 01-04 docx/pdf (giữ format gốc), chỉ sửa số liệu nguồn.

**Báo cáo quý:** Trên test env, tạm thời báo cáo quý chỉ tính cho các tháng cùng version. Nếu trong 1 quý có cả V1 và V2 → log warning, vẫn xuất nhưng đánh dấu rõ trong file output.

---

## ACCEPTANCE CRITERIA

Phase B coi là DONE khi:

- [ ] File `kpi_calculator_v2.py` có đầy đủ 3 hàm với unit test pass.
- [ ] Route `POST /api/ke-khai-v2` tạo được bản kê khai V2 với snapshot đầy đủ.
- [ ] Reject kê khai V2 khi tháng đã có V1 (verify bằng test integration).
- [ ] Reject request body có `he_so_thuc_te` ở mọi endpoint V2.
- [ ] Phê duyệt V2 tính `sp_dat_chat_luong` và `sp_dat_tien_do` đúng (verify với case `so_luong=5, he_so=6.4, loi=3` → sp_dat = 27.2).
- [ ] `tinh_diem_kpi_70_v2` tính đúng KPI khi có nhiều bản kê khai (test với scenario có sẵn).
- [ ] Mẫu số = 0 → KPI = 0 → tự gán mức D, log audit.
- [ ] V1 endpoints/services hoạt động không thay đổi (chạy lại regression test V1 hiện có).
- [ ] Endpoint `GET /api/danh-muc/linh-vuc` trả về đúng 15 lĩnh vực.
- [ ] Endpoint `GET /api/danh-muc/sp-cong-viec/pl3` filter và search hoạt động đúng.

---

## STOP và báo cáo

Sau khi xong Task B.7, **DỪNG LẠI**. Báo cáo cho user:

```
## Phase B Report

### Files created
- backend/app/services/kpi_calculator_v2.py
- backend/app/api/v1/endpoints/ke_khai_v2.py
- ... (list)

### Files modified (added V2 branch)
- backend/app/api/v1/endpoints/phe_duyet.py
- backend/app/api/v1/endpoints/xep_loai_moi.py
- ... (list, kèm line ranges)

### Test results
- Unit tests: X passed, Y failed
- Integration tests V2 flow: X passed, Y failed
- Regression tests V1: X passed, Y failed

### Manual smoke test
[Chạy thử: tạo kê khai V2 → phê duyệt → tính KPI tháng → kết quả số]

### Issues encountered
[Liệt kê]

### Ready for Phase C?
[YES / NO + lý do]
```

KHÔNG động vào frontend. KHÔNG sửa code V1 ngoài việc thêm nhánh `if version == 'V2_PL3'`.
