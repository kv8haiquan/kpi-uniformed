# API SPECS — MODULE LEGAL (PHỔ BIẾN PHÁP LUẬT)
## Base URL: `/api/legal/v1` | Backend Port: 8003

> **Phiên bản:** 1.0 | **Ngày:** 19/02/2026

---

## I. TỔNG QUAN

| Thông tin | Giá trị |
|-----------|---------|
| **Base URL** | `/api/legal/v1` |
| **Auth** | Bearer JWT |
| **Pagination** | `?page=1&page_size=20` |

---

## II. LOẠI VĂN BẢN (`/loai-van-ban`)

### 2.1. Danh sách loại VB
```
GET /api/legal/v1/loai-van-ban
Auth: Tất cả CBCC
```

Response:
```json
{
  "data": [
    {"id": "uuid", "ma": "LUAT", "ten": "Luật"},
    {"id": "uuid", "ma": "NGHI_DINH", "ten": "Nghị định"},
    {"id": "uuid", "ma": "THONG_TU", "ten": "Thông tư"}
  ]
}
```

### 2.2. CRUD loại VB
```
POST/PUT/DELETE /api/legal/v1/loai-van-ban
Auth: ADMIN
```

---

## III. VĂN BẢN (`/van-ban`)

### 3.1. Danh sách văn bản (cho CBCC)
```
GET /api/legal/v1/van-ban
Query: ?loai_van_ban_id=uuid&trang_thai_hieu_luc=CON_HIEU_LUC
       &muc_do=KHAN&bat_buoc_doc=true&chuyen_de=thuế XNK
       &search=từ_khóa&sap_xep=moi_nhat|quan_trong
       &page=1&page_size=20
Auth: Tất cả CBCC
Note: Chỉ trả về VB có trang_thai_duyet=DA_XUAT_BAN
```

Response:
```json
{
  "data": [
    {
      "id": "uuid",
      "so_hieu": "335/2025/NĐ-CP",
      "trich_yeu": "Quy định xử phạt vi phạm hành chính trong lĩnh vực hải quan",
      "loai_van_ban": {"id": "uuid", "ma": "NGHI_DINH", "ten": "Nghị định"},
      "co_quan_ban_hanh": "Chính phủ",
      "ngay_ban_hanh": "2025-10-01",
      "ngay_hieu_luc": "2025-12-01",
      "trang_thai_hieu_luc": "CON_HIEU_LUC",
      "muc_do": "QUAN_TRONG",
      "bat_buoc_doc": true,
      "han_xac_nhan": "2026-03-30",
      "da_doc": false,
      "da_xac_nhan": false,
      "co_diem_moi": true,
      "tags": ["xử phạt", "hành chính"],
      "ngay_xuat_ban": "2026-03-10"
    }
  ]
}
```

### 3.2. VB chưa đọc / cần xác nhận
```
GET /api/legal/v1/van-ban/chua-doc
Query: ?page=1&page_size=20
Auth: Tất cả CBCC
Note: Trả về VB có bat_buoc_doc=TRUE mà CBCC chưa đọc/xác nhận
```

### 3.3. Chi tiết văn bản
```
GET /api/legal/v1/van-ban/{id}
Auth: Tất cả CBCC
Side effect: Tạo/cập nhật xac_nhan_doc (da_doc=TRUE, ghi ngay_doc)
```

Response:
```json
{
  "data": {
    "id": "uuid",
    "so_hieu": "335/2025/NĐ-CP",
    "trich_yeu": "...",
    "loai_van_ban": {...},
    "co_quan_ban_hanh": "Chính phủ",
    "ngay_ban_hanh": "2025-10-01",
    "ngay_hieu_luc": "2025-12-01",
    "trang_thai_hieu_luc": "CON_HIEU_LUC",
    "tom_tat": "...",
    "noi_dung_html": "<html>Nội dung đầy đủ...</html>",
    "file_goc_url": "https://kv08.vn/files/legal/335-2025-ND-CP.pdf",
    "diem_moi": "1. Bổ sung hành vi...\n2. Tăng mức phạt...",
    "viec_can_lam": "1. Cập nhật quy trình KTSTQ\n2. Phổ biến cho CBCC",
    "muc_do": "QUAN_TRONG",
    "bat_buoc_doc": true,
    "han_xac_nhan": "2026-03-30",
    "chuyen_de": ["xử phạt", "hành chính"],
    "van_ban_lien_ket": [
      {"id": "uuid", "so_hieu": "123/2020/NĐ-CP", "loai_lien_ket": "THAY_THE", "trich_yeu": "..."}
    ],
    "xac_nhan": {
      "da_doc": true,
      "ngay_doc": "2026-03-15T08:00:00",
      "da_xac_nhan": false
    },
    "quiz": [
      {"id": "uuid", "tieu_de": "Kiểm tra NĐ 335", "so_cau_hoi": 10}
    ]
  }
}
```

### 3.4. Tạo văn bản (nhập mới)
```
POST /api/legal/v1/van-ban
Auth: BIEN_TAP, QT_NOI_DUNG, ADMIN
Content-Type: multipart/form-data (nếu upload file)
```

Body:
```json
{
  "so_hieu": "335/2025/NĐ-CP",
  "trich_yeu": "Quy định xử phạt...",
  "loai_van_ban_id": "uuid",
  "co_quan_ban_hanh": "Chính phủ",
  "ngay_ban_hanh": "2025-10-01",
  "ngay_hieu_luc": "2025-12-01",
  "trang_thai_hieu_luc": "CON_HIEU_LUC",
  "tom_tat": "...",
  "noi_dung_html": "<html>...</html>",
  "diem_moi": "1. Bổ sung hành vi...",
  "viec_can_lam": "1. Cập nhật quy trình...",
  "muc_do": "QUAN_TRONG",
  "bat_buoc_doc": true,
  "han_xac_nhan": "2026-03-30",
  "doi_tuong_ap_dung": ["TAT_CA"],
  "chuyen_de": ["xử phạt", "hành chính"],
  "van_ban_lien_ket": [
    {"van_ban_lien_quan_id": "uuid", "loai_lien_ket": "THAY_THE"}
  ]
}
```

### 3.5. Sửa văn bản
```
PUT /api/legal/v1/van-ban/{id}
Auth: BIEN_TAP (trạng thái NHAP/CHO_DUYET), QT_NOI_DUNG, ADMIN
```

### 3.6. Workflow duyệt
```
PATCH /api/legal/v1/van-ban/{id}/trang-thai
Auth: BIEN_TAP (gửi duyệt), QT_NOI_DUNG (duyệt/từ chối), Lãnh đạo (duyệt), ADMIN
```

Body:
```json
{"trang_thai_duyet": "DA_XUAT_BAN", "ghi_chu": "Đã kiểm tra"}
```

Workflow: `NHAP → CHO_DUYET → DA_DUYET → DA_XUAT_BAN`

Side effect khi DA_XUAT_BAN:
- Nếu `bat_buoc_doc=TRUE`: Tạo xac_nhan_doc cho tất cả CBCC (hoặc theo doi_tuong_ap_dung)
- Gửi notification batch qua Common API

### 3.7. Xóa văn bản
```
DELETE /api/legal/v1/van-ban/{id}
Auth: QT_NOI_DUNG, ADMIN
Điều kiện: Chỉ trạng thái NHAP
```

### 3.8. Download file gốc
```
GET /api/legal/v1/van-ban/{id}/download
Auth: Tất cả CBCC
Response: application/pdf
```

---

## IV. XÁC NHẬN ĐỌC (`/xac-nhan`)

### 4.1. Xác nhận đã đọc và hiểu
```
POST /api/legal/v1/van-ban/{id}/xac-nhan
Auth: Tất cả CBCC
```

Body:
```json
{
  "da_xac_nhan": true,
  "ghi_chu": "Đã đọc và hiểu nội dung"
}
```

Logic: Cập nhật da_xac_nhan=TRUE, ngay_xac_nhan=NOW()

### 4.2. Tracking thời gian đọc
```
PATCH /api/legal/v1/van-ban/{id}/tracking
Auth: Tất cả CBCC (tự động gọi từ Frontend)
```

Body:
```json
{"thoi_gian_doc_giay": 300}
```

Logic: Cập nhật thoi_gian_doc_giay (cộng dồn).

### 4.3. Báo cáo xác nhận đọc (cho lãnh đạo)
```
GET /api/legal/v1/van-ban/{id}/bao-cao-doc
Query: ?don_vi_id=uuid
Auth: QT_NOI_DUNG, Lãnh đạo (đơn vị mình), ADMIN
```

Response:
```json
{
  "data": {
    "van_ban": {"so_hieu": "335/2025/NĐ-CP", "han_xac_nhan": "2026-03-30"},
    "tong_doi_tuong": 549,
    "da_doc": 420,
    "da_xac_nhan": 380,
    "chua_doc": 129,
    "qua_han": 15,
    "chi_tiet": [
      {"cong_chuc": {"ho_ten": "...", "don_vi": "..."}, "da_doc": true, "da_xac_nhan": true, "ngay_doc": "..."},
      {"cong_chuc": {"ho_ten": "...", "don_vi": "..."}, "da_doc": false, "da_xac_nhan": false, "ngay_doc": null}
    ]
  }
}
```

---

## V. QUIZ VĂN BẢN (`/quiz`)

### 5.1. Danh sách quiz của VB
```
GET /api/legal/v1/van-ban/{van_ban_id}/quiz
Auth: Tất cả CBCC
```

### 5.2. Tạo quiz
```
POST /api/legal/v1/van-ban/{van_ban_id}/quiz
Auth: BIEN_TAP, QT_NOI_DUNG, ADMIN
```

Body:
```json
{
  "tieu_de": "Kiểm tra NĐ 335/2025",
  "thoi_gian_phut": 15,
  "diem_dat": 70.0,
  "cau_hoi": [
    {
      "noi_dung": "NĐ 335 có hiệu lực từ ngày nào?",
      "dap_an": ["01/01/2025", "01/03/2025", "01/06/2025", "01/12/2025"],
      "correct": 3,
      "giai_thich": "Theo Điều 45..."
    }
  ]
}
```

### 5.3. Làm quiz
```
POST /api/legal/v1/quiz/{id}/lam-bai
Auth: Tất cả CBCC
```

Body:
```json
{
  "tra_loi": [
    {"cau": 0, "dap_an": 3},
    {"cau": 1, "dap_an": 1}
  ]
}
```

Response:
```json
{
  "data": {
    "diem": 90.0,
    "so_cau_dung": 9,
    "dat_yeu_cau": true,
    "chi_tiet": [
      {"cau": 0, "tra_loi": 3, "dung": true, "giai_thich": "..."}
    ]
  }
}
```

### 5.4. Xem kết quả quiz
```
GET /api/legal/v1/quiz/{id}/ket-qua
Auth: CBCC (của mình), BIEN_TAP, QT_NOI_DUNG, ADMIN
```

---

## VI. BÁO CÁO & DASHBOARD

### 6.1. Dashboard summary
```
GET /api/legal/v1/dashboard/summary
Auth: Tất cả CBCC
```

Response:
```json
{
  "data": {
    "vb_moi_tuan": 3,
    "vb_chua_doc": 2,
    "vb_khan": 1,
    "vb_sap_het_han": 1,
    "quiz_chua_lam": 2
  }
}
```

### 6.2. Báo cáo cá nhân
```
GET /api/legal/v1/bao-cao/ca-nhan
Query: ?thang=3&nam=2026
Auth: Tất cả CBCC
```

### 6.3. Báo cáo đơn vị
```
GET /api/legal/v1/bao-cao/don-vi/{don_vi_id}
Query: ?thang=3&nam=2026
Auth: QT_NOI_DUNG, Lãnh đạo (đơn vị mình), ADMIN
```

Response:
```json
{
  "data": {
    "don_vi": {"ten_don_vi": "Đội thủ tục 1"},
    "tong_cbcc": 35,
    "thong_ke": {
      "vb_bat_buoc_trong_thang": 5,
      "ty_le_da_doc": 85.7,
      "ty_le_xac_nhan": 78.3,
      "ty_le_qua_han": 5.2,
      "quiz_diem_tb": 82.0
    },
    "cbcc_chua_doc": [
      {"ho_ten": "...", "vb_chua_doc": 2, "vb_qua_han": 1}
    ]
  }
}
```

---

## VII. INTERNAL API (cho module khác gọi)

### 7.1. Lấy thông tin VB (cho Forum trích dẫn)
```
GET /internal/v1/legal/van-ban/{id}/summary
Auth: X-Internal-Key
```

### 7.2. Tìm kiếm VB (cho Forum autocomplete)
```
GET /internal/v1/legal/van-ban/search?q=thuế+XNK&limit=5
Auth: X-Internal-Key
```

---

## VIII. ERROR CODES

| Code | HTTP | Mô tả |
|------|------|-------|
| LEGAL_ERR_001 | 404 | Văn bản không tồn tại |
| LEGAL_ERR_002 | 400 | Số hiệu VB đã tồn tại |
| LEGAL_ERR_003 | 400 | Workflow trạng thái không hợp lệ |
| LEGAL_ERR_004 | 403 | Không có quyền duyệt |
| LEGAL_ERR_005 | 400 | Đã xác nhận đọc rồi |
| LEGAL_ERR_006 | 404 | Quiz không tồn tại |
| LEGAL_ERR_007 | 400 | VB chưa xuất bản |
| LEGAL_ERR_008 | 403 | Không có quyền thao tác |
