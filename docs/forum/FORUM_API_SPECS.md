# API SPECS — MODULE FORUM (DIỄN ĐÀN NGHIỆP VỤ)
## Base URL: `/api/v1/forum` | Backend Port: 8002

> **Phiên bản:** 1.0 | **Ngày:** 19/02/2026

---

## I. TỔNG QUAN

| Thông tin | Giá trị |
|-----------|---------|
| **Base URL** | `/api/v1/forum` |
| **Auth** | Bearer JWT |
| **Pagination** | `?page=1&page_size=20` |

---

## II. CHUYÊN MỤC (`/chuyen-muc`)

### 2.1. Danh sách chuyên mục
```
GET /api/v1/forum/chuyen-muc
Query: ?is_active=true
Auth: Tất cả CBCC
```

Response:
```json
{
  "data": [
    {
      "id": "uuid",
      "ten_chuyen_muc": "Thủ tục hải quan",
      "mo_ta": "...",
      "icon": "📋",
      "so_chu_de": 45,
      "so_tra_loi": 320,
      "chu_de_moi_nhat": {"id": "uuid", "tieu_de": "...", "created_at": "..."},
      "children": []
    }
  ]
}
```

### 2.2. Tạo / Sửa / Xóa chuyên mục
```
POST /api/v1/forum/chuyen-muc
PUT /api/v1/forum/chuyen-muc/{id}
DELETE /api/v1/forum/chuyen-muc/{id}
Auth: DIEU_PHOI_FORUM, ADMIN
```

---

## III. CHỦ ĐỀ (`/chu-de`)

### 3.1. Danh sách chủ đề
```
GET /api/v1/forum/chu-de
Query: ?chuyen_muc_id=uuid&trang_thai=MO&tags=thuế XNK&search=từ_khóa
       &sap_xep=moi_nhat|nhieu_upvote|nhieu_tra_loi&page=1&page_size=20
Auth: Tất cả CBCC
```

Response:
```json
{
  "data": [
    {
      "id": "uuid",
      "tieu_de": "Cách tính thuế XNK cho hàng gia công?",
      "noi_dung_tom_tat": "Tôi đang gặp vấn đề với...",
      "tags": ["thuế XNK", "gia công"],
      "tac_gia": {"id": "uuid", "ho_ten": "Nguyễn Văn A", "don_vi": "Đội thủ tục 1"},
      "trang_thai": "MO",
      "is_ghim": false,
      "so_luot_xem": 120,
      "so_tra_loi": 5,
      "so_upvote": 12,
      "co_dap_an_chuan": true,
      "created_at": "2026-03-15T08:30:00"
    }
  ]
}
```

### 3.2. Chi tiết chủ đề
```
GET /api/v1/forum/chu-de/{id}
Auth: Tất cả CBCC
Side effect: +1 so_luot_xem
```

Response:
```json
{
  "data": {
    "id": "uuid",
    "tieu_de": "...",
    "noi_dung": "<html>Nội dung đầy đủ</html>",
    "tags": [...],
    "tac_gia": {...},
    "trang_thai": "MO",
    "is_ghim": false,
    "is_khoa": false,
    "so_luot_xem": 121,
    "so_tra_loi": 5,
    "so_upvote": 12,
    "van_ban_lien_quan": [
      {"id": "uuid", "so_hieu": "335/2025/NĐ-CP", "trich_yeu": "..."}
    ],
    "sop_lien_quan": [
      {"id": "uuid", "tieu_de": "SOP khai báo hàng gia công"}
    ],
    "da_upvote": true,
    "da_theo_doi": false,
    "tra_loi_chuan": {"id": "uuid"},
    "created_at": "...",
    "tra_loi": [
      {
        "id": "uuid",
        "noi_dung": "<html>...</html>",
        "tac_gia": {...},
        "is_dap_an_chuan": true,
        "so_upvote": 8,
        "da_upvote": false,
        "can_cu_phap_ly": [...],
        "children": [
          {"id": "uuid", "noi_dung": "...", "tac_gia": {...}}
        ],
        "created_at": "..."
      }
    ]
  }
}
```

### 3.3. Tạo chủ đề
```
POST /api/v1/forum/chu-de
Auth: Tất cả CBCC (trừ chuyên mục chi_doc=TRUE → chỉ expert/admin)
```

Body:
```json
{
  "chuyen_muc_id": "uuid",
  "tieu_de": "Cách tính thuế XNK cho hàng gia công?",
  "noi_dung": "<html>Tôi đang gặp vấn đề...</html>",
  "tags": ["thuế XNK", "gia công"],
  "van_ban_lien_quan": ["uuid-vb-1"],
  "sop_lien_quan": []
}
```

Logic: Nếu `chuyen_muc.yeu_cau_duyet=TRUE` → trang_thai = CHO_DUYET, ngược lại → MO.

### 3.4. Sửa chủ đề
```
PUT /api/v1/forum/chu-de/{id}
Auth: Tác giả (trong 24h đầu), DIEU_PHOI_FORUM, ADMIN
```

### 3.5. Xóa chủ đề (soft delete)
```
DELETE /api/v1/forum/chu-de/{id}
Auth: Tác giả (nếu chưa có trả lời), DIEU_PHOI_FORUM, ADMIN
```

### 3.6. Ghim / Khóa / Duyệt chủ đề
```
PATCH /api/v1/forum/chu-de/{id}/hanh-dong
Auth: DIEU_PHOI_FORUM, ADMIN
```

Body:
```json
{"hanh_dong": "GHIM"}
{"hanh_dong": "BO_GHIM"}
{"hanh_dong": "KHOA", "ly_do": "Đã có đáp án chuẩn"}
{"hanh_dong": "MO_KHOA"}
{"hanh_dong": "AN", "ly_do": "Vi phạm nội quy"}
{"hanh_dong": "DUYET"}
```

### 3.7. Chọn đáp án chuẩn
```
PATCH /api/v1/forum/chu-de/{id}/dap-an-chuan
Auth: Tác giả chủ đề, DIEU_PHOI_FORUM, CHUYEN_GIA, ADMIN
```

Body:
```json
{"tra_loi_id": "uuid"}
```

---

## IV. TRẢ LỜI (`/tra-loi`)

### 4.1. Tạo trả lời
```
POST /api/v1/forum/chu-de/{chu_de_id}/tra-loi
Auth: Tất cả CBCC
Điều kiện: Chủ đề không bị khóa (is_khoa=FALSE)
```

Body:
```json
{
  "noi_dung": "<html>Theo tôi biết thì...</html>",
  "parent_id": null,
  "can_cu_phap_ly": [
    {"loai": "VAN_BAN", "id": "uuid-vb", "trich_dan": "Điều 5 khoản 2..."},
    {"loai": "SOP", "id": "uuid-sop", "trich_dan": "Bước 3 quy trình..."}
  ]
}
```

Side effect: Gửi notification cho tác giả chủ đề + người theo dõi.

### 4.2. Sửa trả lời
```
PUT /api/v1/forum/tra-loi/{id}
Auth: Tác giả (trong 24h), DIEU_PHOI_FORUM, ADMIN
```

### 4.3. Xóa trả lời
```
DELETE /api/v1/forum/tra-loi/{id}
Auth: Tác giả, DIEU_PHOI_FORUM, ADMIN
```

### 4.4. Ẩn trả lời
```
PATCH /api/v1/forum/tra-loi/{id}/an
Auth: DIEU_PHOI_FORUM, ADMIN
```

---

## V. BIỂU QUYẾT (`/bieu-quyet`)

### 5.1. Upvote / Downvote
```
POST /api/v1/forum/bieu-quyet
Auth: Tất cả CBCC
```

Body:
```json
{
  "doi_tuong_type": "CHU_DE",
  "doi_tuong_id": "uuid",
  "loai": "UP"
}
```

Logic:
- Nếu chưa vote → tạo mới
- Nếu đã vote cùng loại → xóa (toggle off)
- Nếu đã vote khác loại → đổi (DOWN→UP hoặc ngược lại)

### 5.2. Xóa vote
```
DELETE /api/v1/forum/bieu-quyet
Auth: CBCC (của mình)
Body: {"doi_tuong_type": "CHU_DE", "doi_tuong_id": "uuid"}
```

---

## VI. THEO DÕI (`/theo-doi`)

### 6.1. Theo dõi / Bỏ theo dõi chủ đề
```
POST /api/v1/forum/chu-de/{id}/theo-doi
DELETE /api/v1/forum/chu-de/{id}/theo-doi
Auth: Tất cả CBCC
```

### 6.2. Danh sách chủ đề đang theo dõi
```
GET /api/v1/forum/theo-doi/cua-toi
Query: ?page=1&page_size=20
Auth: Tất cả CBCC
```

---

## VII. TÌM KIẾM

### 7.1. Full-text search
```
GET /api/v1/forum/tim-kiem
Query: ?q=thuế+XNK&chuyen_muc_id=uuid&tags=gia công&page=1
Auth: Tất cả CBCC
```

Response: Danh sách chủ đề khớp, highlight snippet.

### 7.2. Gợi ý tag
```
GET /api/v1/forum/tags/goi-y
Query: ?q=thu
Auth: Tất cả CBCC
```

Response: `{"data": ["thuế XNK", "thủ tục", "thuê kho ngoại quan"]}`

---

## VIII. BÁO CÁO & DASHBOARD

### 8.1. Dashboard summary (cho widget)
```
GET /api/v1/forum/dashboard/summary
Auth: Tất cả CBCC
```

Response:
```json
{
  "data": {
    "chu_de_moi_tuan": 5,
    "tra_loi_chua_doc": 3,
    "upvote_tuan": 12,
    "chu_de_cua_toi_chua_tra_loi": 1
  }
}
```

### 8.2. Thống kê đóng góp cá nhân
```
GET /api/v1/forum/bao-cao/ca-nhan
Query: ?thang=3&nam=2026
Auth: Tất cả CBCC
```

### 8.3. Thống kê đóng góp đơn vị
```
GET /api/v1/forum/bao-cao/don-vi/{don_vi_id}
Query: ?thang=3&nam=2026
Auth: DIEU_PHOI_FORUM, Lãnh đạo (đơn vị mình), ADMIN
```

### 8.4. Top contributors
```
GET /api/v1/forum/bao-cao/top
Query: ?thang=3&nam=2026&limit=10
Auth: Tất cả CBCC
```

---

## IX. KNOWLEDGE BASE (gọi Common API)

### 9.1. Chuyển bài → SOP/FAQ
```
POST /api/v1/forum/chu-de/{id}/chuyen-sop
Auth: DIEU_PHOI_FORUM, CHUYEN_GIA, ADMIN
```

Body:
```json
{
  "loai": "SOP",
  "tieu_de": "Quy trình khai báo hàng gia công",
  "noi_dung_bien_tap": "<html>Nội dung đã biên tập...</html>"
}
```

Logic: Gọi Internal API → Common → tạo knowledge_base record.

---

## X. ERROR CODES

| Code | HTTP | Mô tả |
|------|------|-------|
| FORUM_ERR_001 | 404 | Chuyên mục không tồn tại |
| FORUM_ERR_002 | 404 | Chủ đề không tồn tại |
| FORUM_ERR_003 | 403 | Chủ đề bị khóa, không thể trả lời |
| FORUM_ERR_004 | 403 | Chuyên mục chỉ đọc |
| FORUM_ERR_005 | 403 | Hết thời gian sửa (>24h) |
| FORUM_ERR_006 | 409 | Đã vote rồi |
| FORUM_ERR_007 | 400 | Không thể xóa chủ đề đã có trả lời |
| FORUM_ERR_008 | 403 | Không có quyền thao tác |
| FORUM_ERR_009 | 400 | Chủ đề đang chờ duyệt |
