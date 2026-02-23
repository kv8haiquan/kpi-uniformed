# API SPECS — MODULE LMS (ĐÀO TẠO TRỰC TUYẾN)
## Base URL: `/api/v1/lms` | Backend Port: 8001

> **Phiên bản:** 1.0 | **Ngày:** 19/02/2026

---

## I. TỔNG QUAN

| Thông tin | Giá trị |
|-----------|---------|
| **Base URL** | `/api/v1/lms` |
| **Auth** | Bearer JWT (xem SHARED_AUTH_SPECS) |
| **Response format** | `{"success": bool, "data": {...}, "message": "..."}` |
| **Pagination** | `?page=1&page_size=20` → `"pagination": {"page", "page_size", "total", "total_pages"}` |

### Quy ước chung
- Tất cả endpoint cần JWT trừ khi ghi chú PUBLIC
- ID luôn là UUID
- Ngày giờ format ISO 8601: `2026-03-15T08:30:00`
- Lỗi: `{"success": false, "error": {"code": "LMS_ERR_xxx", "message": "..."}}`

---

## II. CHUYÊN ĐỀ (`/chuyen-de`)

### 2.1. Danh sách chuyên đề
```
GET /api/v1/lms/chuyen-de
Query: ?is_active=true
Auth: Tất cả CBCC
```

Response:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "ma_chuyen_de": "CD001",
      "ten_chuyen_de": "Nghiệp vụ hải quan",
      "mo_ta": "...",
      "anh_dai_dien": "url",
      "so_khoa_hoc": 5,
      "thu_tu": 1
    }
  ]
}
```

### 2.2. Chi tiết chuyên đề
```
GET /api/v1/lms/chuyen-de/{id}
Auth: Tất cả CBCC
```

### 2.3. Tạo chuyên đề
```
POST /api/v1/lms/chuyen-de
Auth: QT_DAO_TAO, ADMIN
```

Body:
```json
{
  "ma_chuyen_de": "CD001",
  "ten_chuyen_de": "Nghiệp vụ hải quan",
  "mo_ta": "Các khóa học về thủ tục hải quan",
  "thu_tu": 1
}
```

### 2.4. Cập nhật chuyên đề
```
PUT /api/v1/lms/chuyen-de/{id}
Auth: QT_DAO_TAO, ADMIN
```

### 2.5. Xóa chuyên đề (soft delete)
```
DELETE /api/v1/lms/chuyen-de/{id}
Auth: QT_DAO_TAO, ADMIN
```

---

## III. KHÓA HỌC (`/khoa-hoc`)

### 3.1. Danh sách khóa học (cho học viên)
```
GET /api/v1/lms/khoa-hoc
Query: ?chuyen_de_id=uuid&loai=BAT_BUOC&trang_thai=DA_XUAT_BAN&search=từ_khóa&page=1&page_size=20
Auth: Tất cả CBCC
Note: Chỉ trả về khóa có trang_thai=DA_XUAT_BAN
```

Response:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "ma_khoa_hoc": "KH001",
      "ten_khoa_hoc": "Luật Hải quan 2024",
      "mo_ta": "...",
      "chuyen_de": {"id": "uuid", "ten_chuyen_de": "..."},
      "loai": "BAT_BUOC",
      "thoi_luong_phut": 120,
      "so_bai_hoc": 10,
      "diem_dat_yeu_cau": 70.0,
      "ngay_bat_dau": "2026-03-01",
      "ngay_ket_thuc": "2026-06-30",
      "giang_vien": {"id": "uuid", "ho_ten": "Nguyễn Văn A"},
      "anh_dai_dien": "url",
      "da_dang_ky": true,
      "tien_do": 45.5
    }
  ],
  "pagination": {"page": 1, "page_size": 20, "total": 35, "total_pages": 2}
}
```

### 3.2. Danh sách khóa học (cho giảng viên / QT đào tạo)
```
GET /api/v1/lms/khoa-hoc/quan-ly
Query: ?trang_thai=NHAP&giang_vien_id=uuid&page=1&page_size=20
Auth: GIANG_VIEN (chỉ khóa của mình), QT_DAO_TAO, ADMIN (tất cả)
Note: Trả về TẤT CẢ trạng thái
```

### 3.3. Chi tiết khóa học
```
GET /api/v1/lms/khoa-hoc/{id}
Auth: Tất cả CBCC
```

Response bổ sung:
```json
{
  "data": {
    "...": "...",
    "bai_hoc": [
      {"id": "uuid", "thu_tu": 1, "tieu_de": "Bài 1: Tổng quan", "loai_noi_dung": "VIDEO", "thoi_luong_phut": 15, "tien_do": "DA_HOAN_THANH"},
      {"id": "uuid", "thu_tu": 2, "tieu_de": "Bài 2: Thủ tục XNK", "loai_noi_dung": "PDF", "thoi_luong_phut": 20, "tien_do": "DANG_XEM"}
    ],
    "bai_kiem_tra": [
      {"id": "uuid", "tieu_de": "Bài kiểm tra cuối khóa", "so_cau_hoi": 20, "thoi_gian_lam_bai_phut": 30}
    ],
    "dang_ky": {
      "trang_thai": "DANG_HOC",
      "phan_tram_hoan_thanh": 45.5,
      "loai_dang_ky": "BAT_BUOC",
      "han_hoan_thanh": "2026-06-30"
    }
  }
}
```

### 3.4. Tạo khóa học
```
POST /api/v1/lms/khoa-hoc
Auth: GIANG_VIEN, QT_DAO_TAO, ADMIN
```

Body:
```json
{
  "ma_khoa_hoc": "KH001",
  "ten_khoa_hoc": "Luật Hải quan 2024",
  "mo_ta": "Khóa học về Luật Hải quan...",
  "chuyen_de_id": "uuid",
  "loai": "BAT_BUOC",
  "thoi_luong_phut": 120,
  "diem_dat_yeu_cau": 70.0,
  "ngay_bat_dau": "2026-03-01",
  "ngay_ket_thuc": "2026-06-30",
  "dieu_kien_tien_quyet": []
}
```

### 3.5. Cập nhật khóa học
```
PUT /api/v1/lms/khoa-hoc/{id}
Auth: GIANG_VIEN (khóa của mình, trạng thái NHAP), QT_DAO_TAO, ADMIN
```

### 3.6. Chuyển trạng thái khóa học (workflow)
```
PATCH /api/v1/lms/khoa-hoc/{id}/trang-thai
Auth: GIANG_VIEN (NHAP→CHO_DUYET), QT_DAO_TAO (duyệt/từ chối), ADMIN
```

Body:
```json
{
  "trang_thai": "DA_XUAT_BAN",
  "ghi_chu": "Đã kiểm tra nội dung"
}
```

Workflow: `NHAP → CHO_DUYET → DA_XUAT_BAN → TAM_DUNG/DA_DONG`

### 3.7. Xóa khóa học
```
DELETE /api/v1/lms/khoa-hoc/{id}
Auth: QT_DAO_TAO, ADMIN
Điều kiện: Chỉ xóa khóa trạng thái NHAP, hoặc chưa có ai đăng ký
```

---

## IV. BÀI HỌC (`/khoa-hoc/{khoa_hoc_id}/bai-hoc`)

### 4.1. Danh sách bài học
```
GET /api/v1/lms/khoa-hoc/{khoa_hoc_id}/bai-hoc
Auth: Tất cả CBCC (đã đăng ký khóa)
```

### 4.2. Chi tiết bài học (xem nội dung)
```
GET /api/v1/lms/bai-hoc/{id}
Auth: CBCC đã đăng ký khóa chứa bài này
Side effect: Cập nhật tien_do_bai_hoc (CHUA_XEM → DANG_XEM)
```

Response:
```json
{
  "data": {
    "id": "uuid",
    "tieu_de": "Bài 1: Tổng quan",
    "loai_noi_dung": "VIDEO",
    "noi_dung": "<html>...</html>",
    "file_url": "https://kv08.vn/files/lms/videos/uuid.mp4",
    "thoi_luong_phut": 15,
    "tien_do": {
      "trang_thai": "DANG_XEM",
      "thoi_gian_xem_giay": 320
    }
  }
}
```

### 4.3. Tạo bài học
```
POST /api/v1/lms/khoa-hoc/{khoa_hoc_id}/bai-hoc
Auth: GIANG_VIEN (khóa của mình), QT_DAO_TAO, ADMIN
Content-Type: multipart/form-data (nếu upload file)
```

### 4.4. Cập nhật bài học
```
PUT /api/v1/lms/bai-hoc/{id}
Auth: GIANG_VIEN (khóa của mình), QT_DAO_TAO, ADMIN
```

### 4.5. Cập nhật tiến độ bài học
```
PATCH /api/v1/lms/bai-hoc/{id}/tien-do
Auth: CBCC đã đăng ký
```

Body:
```json
{
  "thoi_gian_xem_giay": 600,
  "hoan_thanh": true
}
```

Logic: Nếu `hoan_thanh=true` → set trạng thái DA_HOAN_THANH, cập nhật % khóa học.

### 4.6. Sắp xếp lại bài học
```
PATCH /api/v1/lms/khoa-hoc/{khoa_hoc_id}/bai-hoc/sap-xep
Auth: GIANG_VIEN, QT_DAO_TAO, ADMIN
```

Body:
```json
{
  "thu_tu": [
    {"bai_hoc_id": "uuid-1", "thu_tu": 1},
    {"bai_hoc_id": "uuid-2", "thu_tu": 2}
  ]
}
```

---

## V. ĐĂNG KÝ KHÓA HỌC (`/dang-ky`)

### 5.1. CBCC tự đăng ký
```
POST /api/v1/lms/khoa-hoc/{khoa_hoc_id}/dang-ky
Auth: Tất cả CBCC
```

Response: `{"data": {"id": "uuid", "trang_thai": "CHUA_BAT_DAU"}}`

### 5.2. Giao khóa bắt buộc (batch)
```
POST /api/v1/lms/khoa-hoc/{khoa_hoc_id}/giao-bai
Auth: QT_DAO_TAO, Lãnh đạo (is_lanh_dao=TRUE), ADMIN
```

Body:
```json
{
  "cong_chuc_ids": ["uuid-1", "uuid-2"],
  "loai_dang_ky": "BAT_BUOC",
  "han_hoan_thanh": "2026-06-30"
}
```

Hoặc giao theo đơn vị:
```json
{
  "don_vi_ids": ["uuid-dv-1"],
  "loai_dang_ky": "BAT_BUOC",
  "han_hoan_thanh": "2026-06-30"
}
```

Side effect: Gửi notification → Common API.

### 5.3. Danh sách khóa đã đăng ký (của CBCC hiện tại)
```
GET /api/v1/lms/dang-ky/cua-toi
Query: ?trang_thai=DANG_HOC&page=1
Auth: Tất cả CBCC
```

### 5.4. Danh sách học viên của khóa (cho giảng viên)
```
GET /api/v1/lms/khoa-hoc/{khoa_hoc_id}/hoc-vien
Query: ?trang_thai=DANG_HOC&don_vi_id=uuid
Auth: GIANG_VIEN (khóa mình), QT_DAO_TAO, ADMIN
```

### 5.5. Hủy đăng ký
```
DELETE /api/v1/lms/khoa-hoc/{khoa_hoc_id}/dang-ky
Auth: CBCC (chỉ khóa TU_NGUYEN + CHUA_BAT_DAU)
```

---

## VI. CÂU HỎI & BÀI KIỂM TRA

### 6.1. Ngân hàng câu hỏi
```
GET /api/v1/lms/cau-hoi
Query: ?khoa_hoc_id=uuid&loai=TRAC_NGHIEM_1&do_kho=KHO&page=1
Auth: GIANG_VIEN, QT_DAO_TAO, ADMIN

POST /api/v1/lms/cau-hoi
Auth: GIANG_VIEN, QT_DAO_TAO, ADMIN

PUT /api/v1/lms/cau-hoi/{id}
DELETE /api/v1/lms/cau-hoi/{id}
```

### 6.2. Bài kiểm tra
```
GET /api/v1/lms/khoa-hoc/{khoa_hoc_id}/bai-kiem-tra
POST /api/v1/lms/khoa-hoc/{khoa_hoc_id}/bai-kiem-tra
PUT /api/v1/lms/bai-kiem-tra/{id}
DELETE /api/v1/lms/bai-kiem-tra/{id}
Auth: GIANG_VIEN, QT_DAO_TAO, ADMIN
```

### 6.3. Bắt đầu làm bài kiểm tra
```
POST /api/v1/lms/bai-kiem-tra/{id}/bat-dau
Auth: CBCC đã đăng ký khóa
Điều kiện: Chưa vượt so_lan_lam_toi_da, trong thời gian ngay_mo-ngay_dong
```

Response:
```json
{
  "data": {
    "lan_thu": 2,
    "cau_hoi": [
      {"id": "uuid", "thu_tu": 1, "noi_dung": "...", "loai": "TRAC_NGHIEM_1", "dap_an": {"options": ["A", "B", "C", "D"]}},
      "..."
    ],
    "thoi_gian_lam_bai_phut": 30,
    "thoi_gian_bat_dau": "2026-03-15T08:30:00"
  }
}
```

Note: Đáp án đúng KHÔNG trả về. Nếu `tron_de=true` → random thứ tự.

### 6.4. Nộp bài kiểm tra
```
POST /api/v1/lms/bai-kiem-tra/{id}/nop-bai
Auth: CBCC đang làm bài
```

Body:
```json
{
  "tra_loi": [
    {"cau_hoi_id": "uuid", "dap_an": [1]},
    {"cau_hoi_id": "uuid", "dap_an": [0, 2]},
    {"cau_hoi_id": "uuid", "dap_an": true}
  ]
}
```

Response:
```json
{
  "data": {
    "diem": 85.0,
    "so_cau_dung": 17,
    "so_cau_sai": 3,
    "dat_yeu_cau": true,
    "chi_tiet": [
      {"cau_hoi_id": "uuid", "tra_loi": [1], "dung": true, "diem": 1.0, "giai_thich": "..."}
    ]
  }
}
```

Side effect: Nếu đạt → kiểm tra hoàn thành khóa → cấp chứng chỉ → ghi notification + KPI log.

### 6.5. Xem lịch sử kết quả
```
GET /api/v1/lms/bai-kiem-tra/{id}/ket-qua
Auth: CBCC (của mình), GIANG_VIEN, QT_DAO_TAO, ADMIN
```

---

## VII. CHỨNG CHỈ (`/chung-chi`)

### 7.1. Danh sách chứng chỉ của tôi
```
GET /api/v1/lms/chung-chi/cua-toi
Auth: Tất cả CBCC
```

### 7.2. Download chứng chỉ PDF
```
GET /api/v1/lms/chung-chi/{id}/download
Auth: CBCC (của mình), ADMIN
Response: application/pdf
```

### 7.3. Xác minh chứng chỉ
```
GET /api/v1/lms/chung-chi/xac-minh/{ma_chung_chi}
Auth: PUBLIC (ai cũng có thể xác minh bằng mã)
```

---

## VIII. BÁO CÁO (`/bao-cao`)

### 8.1. Báo cáo cá nhân
```
GET /api/v1/lms/bao-cao/ca-nhan
Query: ?thang=3&nam=2026
Auth: Tất cả CBCC
```

### 8.2. Báo cáo đơn vị
```
GET /api/v1/lms/bao-cao/don-vi/{don_vi_id}
Query: ?thang=3&nam=2026
Auth: QT_DAO_TAO, Lãnh đạo (chỉ đơn vị mình), ADMIN
```

Response:
```json
{
  "data": {
    "don_vi": {"id": "uuid", "ten_don_vi": "Đội thủ tục 1"},
    "tong_cbcc": 35,
    "thong_ke": {
      "dang_hoc": 15,
      "hoan_thanh_thang": 8,
      "qua_han": 2,
      "chua_dang_ky": 10
    },
    "chi_tiet_cbcc": [
      {"cong_chuc": {"id": "uuid", "ho_ten": "..."}, "khoa_dang_hoc": 2, "khoa_hoan_thanh": 3, "diem_tb": 85.5}
    ]
  }
}
```

### 8.3. Báo cáo khóa học
```
GET /api/v1/lms/bao-cao/khoa-hoc/{khoa_hoc_id}
Auth: GIANG_VIEN (khóa mình), QT_DAO_TAO, ADMIN
```

### 8.4. Dashboard summary (cho widget)
```
GET /api/v1/lms/dashboard/summary
Auth: Tất cả CBCC
```

Response:
```json
{
  "data": {
    "khoa_dang_hoc": 2,
    "khoa_sap_het_han": 1,
    "chung_chi_moi": 1,
    "thong_bao_chua_doc": 3
  }
}
```

---

## IX. KHẢO SÁT (`/khao-sat`)

### 9.1. Gửi khảo sát
```
POST /api/v1/lms/khoa-hoc/{khoa_hoc_id}/khao-sat
Auth: CBCC đã hoàn thành khóa
```

Body:
```json
{
  "noi_dung": {
    "rating": 4,
    "feedback": "Khóa học rất hữu ích",
    "questions": [
      {"q": "Nội dung phù hợp?", "score": 5},
      {"q": "Giảng viên tốt?", "score": 4}
    ]
  }
}
```

### 9.2. Xem kết quả khảo sát (giảng viên)
```
GET /api/v1/lms/khoa-hoc/{khoa_hoc_id}/khao-sat/thong-ke
Auth: GIANG_VIEN (khóa mình), QT_DAO_TAO, ADMIN
```

---

## X. ERROR CODES

| Code | HTTP | Mô tả |
|------|------|-------|
| LMS_ERR_001 | 404 | Khóa học không tồn tại |
| LMS_ERR_002 | 400 | Khóa học chưa xuất bản |
| LMS_ERR_003 | 409 | Đã đăng ký khóa này rồi |
| LMS_ERR_004 | 400 | Chưa hoàn thành khóa tiên quyết |
| LMS_ERR_005 | 400 | Đã hết số lần làm bài |
| LMS_ERR_006 | 400 | Ngoài thời gian làm bài |
| LMS_ERR_007 | 400 | Đã hết thời gian làm bài |
| LMS_ERR_008 | 403 | Không có quyền thao tác này |
| LMS_ERR_009 | 400 | Không thể xóa khóa đã có người đăng ký |
| LMS_ERR_010 | 400 | Workflow trạng thái không hợp lệ |
