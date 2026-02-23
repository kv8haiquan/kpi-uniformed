# API SPECS — MODULE PORTAL & COMMON
## Base URL: `/api/v1/portal` + `/api/v1/common`

> **Phiên bản:** 1.0 | **Ngày:** 19/02/2026

---

## I. PORTAL — TRANG CHỦ / CMS / ECM

### 1. CHUYÊN MỤC TIN TỨC (`/portal/chuyen-muc`)

```
GET /api/v1/portal/chuyen-muc                     — Danh sách (Auth: tất cả)
POST /api/v1/portal/chuyen-muc                     — Tạo (Auth: BIEN_TAP, ADMIN)
PUT /api/v1/portal/chuyen-muc/{id}                 — Sửa
DELETE /api/v1/portal/chuyen-muc/{id}               — Xóa
```

### 2. BÀI VIẾT / TIN TỨC (`/portal/bai-viet`)

#### 2.1. Danh sách (công khai)
```
GET /api/v1/portal/bai-viet
Query: ?chuyen_muc_id=uuid&trang_thai=XUAT_BAN&search=từ_khóa&page=1&page_size=20
Auth: Tất cả CBCC
Note: Chỉ XUAT_BAN. Bài ghim hiện đầu.
```

Response:
```json
{
  "data": [
    {
      "id": "uuid",
      "tieu_de": "Chi cục HQ KV8 triển khai hệ thống KPI",
      "tom_tat": "Ngày 28/01/2026...",
      "anh_dai_dien": "url",
      "chuyen_muc": {"id": "uuid", "ten": "Tin hoạt động"},
      "nguoi_soan": {"ho_ten": "..."},
      "ngay_xuat_ban": "2026-03-15",
      "so_luot_xem": 250,
      "is_ghim": false
    }
  ]
}
```

#### 2.2. Chi tiết
```
GET /api/v1/portal/bai-viet/{id}
Auth: Tất cả CBCC
Side effect: +1 so_luot_xem
```

#### 2.3. Tạo bài viết
```
POST /api/v1/portal/bai-viet
Auth: BIEN_TAP, QT_NOI_DUNG, ADMIN
```

Body:
```json
{
  "chuyen_muc_id": "uuid",
  "tieu_de": "Tiêu đề bài viết",
  "tom_tat": "Tóm tắt ngắn...",
  "noi_dung": "<html>Nội dung đầy đủ</html>",
  "anh_dai_dien": "url (upload qua Common file API)"
}
```

#### 2.4. Workflow duyệt
```
PATCH /api/v1/portal/bai-viet/{id}/trang-thai
Auth: BIEN_TAP (gửi duyệt), QT_NOI_DUNG (kiểm tra), Lãnh đạo (duyệt), ADMIN
```

Workflow: `NHAP → KIEM_TRA → DUYET → XUAT_BAN → THU_HOI`

#### 2.5. Ghim / Bỏ ghim
```
PATCH /api/v1/portal/bai-viet/{id}/ghim
Auth: QT_NOI_DUNG, ADMIN
Body: {"is_ghim": true}
```

#### 2.6. Sửa / Xóa
```
PUT /api/v1/portal/bai-viet/{id}
DELETE /api/v1/portal/bai-viet/{id}
Auth: BIEN_TAP (NHAP), QT_NOI_DUNG, ADMIN
```

### 3. THƯ VIỆN TÀI LIỆU ECM (`/portal/tai-lieu`)

#### 3.1. Danh sách thư mục
```
GET /api/v1/portal/thu-muc
Query: ?parent_id=uuid (NULL = root)
Auth: Tất cả CBCC (lọc theo phân quyền)
```

#### 3.2. CRUD thư mục
```
POST /api/v1/portal/thu-muc                        — Auth: QT_NOI_DUNG, ADMIN
PUT /api/v1/portal/thu-muc/{id}
DELETE /api/v1/portal/thu-muc/{id}                  — Chỉ xóa thư mục rỗng
```

#### 3.3. Danh sách tài liệu trong thư mục
```
GET /api/v1/portal/tai-lieu
Query: ?thu_muc_id=uuid&file_type=PDF&search=từ_khóa&tags=biểu mẫu&page=1
Auth: Tất cả CBCC (lọc theo phân quyền thư mục)
```

Response:
```json
{
  "data": [
    {
      "id": "uuid",
      "ten_tai_lieu": "Mẫu tờ khai XNK",
      "mo_ta": "...",
      "thu_muc": {"id": "uuid", "ten": "Biểu mẫu"},
      "file_name": "mau-to-khai-xnk-v3.pdf",
      "file_size_bytes": 524288,
      "file_type": "PDF",
      "phien_ban": 3,
      "nguoi_tai_len": {"ho_ten": "..."},
      "created_at": "2026-03-10",
      "tags": ["biểu mẫu", "XNK"]
    }
  ]
}
```

#### 3.4. Upload tài liệu
```
POST /api/v1/portal/tai-lieu
Content-Type: multipart/form-data
Auth: QT_NOI_DUNG, ADMIN (hoặc CBCC nếu thư mục cho phép)
```

Fields:
```
file: <binary>
ten_tai_lieu: "Mẫu tờ khai XNK"
mo_ta: "Phiên bản mới nhất"
thu_muc_id: "uuid"
tags: ["biểu mẫu", "XNK"]
```

#### 3.5. Upload phiên bản mới
```
POST /api/v1/portal/tai-lieu/{id}/phien-ban-moi
Content-Type: multipart/form-data
Auth: Người upload gốc, QT_NOI_DUNG, ADMIN
```

Logic: Tạo record mới, phien_ban +1, phien_ban_truoc_id = id cũ.

#### 3.6. Download
```
GET /api/v1/portal/tai-lieu/{id}/download
Auth: CBCC (theo phân quyền thư mục)
```

#### 3.7. Xem lịch sử phiên bản
```
GET /api/v1/portal/tai-lieu/{id}/lich-su
Auth: Tất cả CBCC
```

#### 3.8. Xóa tài liệu
```
DELETE /api/v1/portal/tai-lieu/{id}
Auth: QT_NOI_DUNG, ADMIN
```

---

## II. COMMON — THÔNG BÁO / FILE / SEARCH / KPI LOG

### 4. THÔNG BÁO (`/common/thong-bao`)

#### 4.1. Danh sách thông báo
```
GET /api/v1/common/thong-bao
Query: ?da_doc=false&loai=LMS&muc_do=KHAN&page=1&page_size=20
Auth: Tất cả CBCC (chỉ thông báo CỦA MÌNH)
```

Response:
```json
{
  "data": [
    {
      "id": "uuid",
      "tieu_de": "Văn bản khẩn cần đọc",
      "noi_dung": "NĐ 335/2025/NĐ-CP cần đọc trong 24h",
      "loai": "LEGAL",
      "muc_do": "KHAN",
      "link_url": "/phap-luat/van-ban/uuid",
      "da_doc": false,
      "created_at": "2026-03-15T08:00:00"
    }
  ]
}
```

#### 4.2. Đếm chưa đọc
```
GET /api/v1/common/thong-bao/count?da_doc=false
Auth: Tất cả CBCC
```

Response: `{"data": {"count": 7, "khan": 1, "quan_trong": 2, "binh_thuong": 4}}`

#### 4.3. Đánh dấu đã đọc
```
PATCH /api/v1/common/thong-bao/{id}/doc
Auth: CBCC (của mình)
```

#### 4.4. Đánh dấu tất cả đã đọc
```
PATCH /api/v1/common/thong-bao/doc-tat-ca
Auth: CBCC (của mình)
```

### 5. UNIFIED SEARCH (`/common/search`)

#### 5.1. Tìm kiếm hợp nhất
```
GET /api/v1/common/search
Query: ?q=thuế+XNK&modules=lms,forum,legal,portal&page=1&page_size=20
Auth: Tất cả CBCC
```

Response:
```json
{
  "data": {
    "results": [
      {
        "module": "LEGAL",
        "type": "VAN_BAN",
        "id": "uuid",
        "title": "NĐ 335/2025/NĐ-CP — Quy định xử phạt...",
        "snippet": "...thuế XNK hàng hóa xuất nhập khẩu...",
        "link": "/phap-luat/van-ban/uuid",
        "score": 0.95
      },
      {
        "module": "FORUM",
        "type": "CHU_DE",
        "id": "uuid",
        "title": "Cách tính thuế XNK cho hàng gia công?",
        "snippet": "...câu hỏi về thuế XNK áp dụng cho...",
        "link": "/dien-dan/chu-de/uuid",
        "score": 0.88
      }
    ],
    "total_by_module": {
      "LEGAL": 5,
      "FORUM": 12,
      "LMS": 3,
      "PORTAL": 1
    }
  }
}
```

Logic: Query tsvector trên các bảng có search_vector, gom kết quả, sắp theo score.

### 6. FILE STORAGE (`/common/file`)

#### 6.1. Upload file (Internal + External)
```
POST /api/v1/common/file/upload
Content-Type: multipart/form-data
Auth: Tất cả CBCC
```

Fields: `file, module, doi_tuong_type, doi_tuong_id`

Response:
```json
{
  "data": {
    "id": "uuid",
    "file_url": "https://kv08.vn/files/lms/videos/uuid.mp4",
    "file_name": "bai-giang-1.mp4",
    "file_size_bytes": 52428800,
    "mime_type": "video/mp4"
  }
}
```

#### 6.2. Lấy URL file
```
GET /api/v1/common/file/{id}
Auth: Tất cả CBCC
```

#### 6.3. Xóa file
```
DELETE /api/v1/common/file/{id}
Auth: Người upload, ADMIN
```

### 7. KNOWLEDGE BASE (`/common/knowledge-base`)

#### 7.1. Danh sách SOP/FAQ
```
GET /api/v1/common/knowledge-base
Query: ?loai=SOP&chuyen_de=thủ tục&tags=XNK&search=từ_khóa&page=1
Auth: Tất cả CBCC
```

#### 7.2. Chi tiết SOP/FAQ
```
GET /api/v1/common/knowledge-base/{id}
Auth: Tất cả CBCC
```

#### 7.3. Tạo / Sửa / Xóa
```
POST /api/v1/common/knowledge-base
PUT /api/v1/common/knowledge-base/{id}
DELETE /api/v1/common/knowledge-base/{id}
Auth: CHUYEN_GIA, DIEU_PHOI_FORUM, QT_NOI_DUNG, ADMIN
```

### 8. KPI INTEGRATION LOG (`/common/kpi-log`)

#### 8.1. Đọc dữ liệu tích hợp (cho KPI Dashboard)
```
GET /api/v1/common/kpi-log/{cong_chuc_id}
Query: ?thang=3&nam=2026
Auth: CBCC (của mình), Lãnh đạo (đơn vị mình), ADMIN
```

#### 8.2. Đọc dữ liệu theo đơn vị
```
GET /api/v1/common/kpi-log/don-vi/{don_vi_id}
Query: ?thang=3&nam=2026
Auth: Lãnh đạo (đơn vị mình), QT_DAO_TAO, QT_NOI_DUNG, ADMIN
```

#### 8.3. Internal: Ghi log (chỉ module khác gọi)
```
POST /internal/v1/common/kpi-log
Auth: X-Internal-Key
```

---

## III. DASHBOARD TỔNG HỢP

### 9. Dashboard CBCC
```
GET /api/v1/portal/dashboard
Auth: Tất cả CBCC
```

Response: Gom từ nhiều API:
```json
{
  "data": {
    "kpi": {"diem_thang_nay": 85, "xep_loai": "A"},
    "lms": {"khoa_dang_hoc": 2, "khoa_sap_het_han": 1},
    "forum": {"chu_de_moi": 5, "tra_loi_chua_doc": 3},
    "legal": {"vb_chua_doc": 2, "vb_khan": 1},
    "thong_bao_chua_doc": 7,
    "tin_tuc_moi": [
      {"id": "uuid", "tieu_de": "...", "ngay": "..."}
    ]
  }
}
```

### 10. Dashboard lãnh đạo
```
GET /api/v1/portal/dashboard/lanh-dao
Query: ?don_vi_id=uuid&thang=3&nam=2026
Auth: Lãnh đạo (is_lanh_dao=TRUE), ADMIN
```

Response:
```json
{
  "data": {
    "don_vi": {"ten": "Đội thủ tục 1", "tong_cbcc": 35},
    "kpi": {"diem_tb": 82.3, "phan_loai": {"A": 5, "B": 20, "C": 8, "D": 2}},
    "lms": {"ty_le_hoan_thanh": 78.5, "cbcc_qua_han": 2},
    "legal": {"ty_le_da_doc": 85.7, "cbcc_chua_doc": 5},
    "forum": {"tong_bai_dang": 45, "top_contributors": [...]},
    "tong_hop_kpi_log": [...]
  }
}
```

---

## IV. ERROR CODES

| Code | HTTP | Mô tả |
|------|------|-------|
| PORTAL_ERR_001 | 404 | Bài viết không tồn tại |
| PORTAL_ERR_002 | 400 | Workflow trạng thái không hợp lệ |
| PORTAL_ERR_003 | 403 | Không có quyền truy cập thư mục |
| PORTAL_ERR_004 | 400 | Không thể xóa thư mục có tài liệu |
| CMN_ERR_001 | 400 | File quá lớn (>100MB) |
| CMN_ERR_002 | 400 | Định dạng file không được hỗ trợ |
| CMN_ERR_003 | 404 | Thông báo không tồn tại |
| CMN_ERR_004 | 400 | Module không hợp lệ |
