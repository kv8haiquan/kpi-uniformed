# API CONTRACT BETWEEN MODULES
## Giao kèo API liên module — Nền tảng Số HQKV8

> **Phiên bản:** 1.0 | **Ngày:** 18/02/2026
> **Quản lý bởi:** Tech Lead (HUB project)
> **Quy tắc:** Mọi thay đổi API liên module PHẢI qua HUB duyệt trước khi triển khai

---

## I. NGUYÊN TẮC CHUNG

### 1. Giao tiếp giữa module

```
Các module KHÔNG gọi trực tiếp DB của nhau.
Mọi trao đổi dữ liệu cross-module đi qua Internal API.

LMS ──API──► Common (ghi notification, ghi kpi_integration_log)
Forum ──API──► Common (ghi notification, ghi kpi_integration_log)
Forum ──API──► Legal (lấy thông tin văn bản để trích dẫn)
Legal ──API──► Common (ghi notification, ghi kpi_integration_log)
Portal ──API──► LMS + Forum + Legal (đọc dữ liệu cho dashboard)
Portal ──API──► Common (quản lý notification, file, search)
```

### 2. Internal API vs External API

| Loại | Base URL | Ai gọi | Mục đích |
|------|----------|--------|----------|
| **External** | `/api/v1/{module}/...` | Frontend → Backend | CBCC sử dụng qua UI |
| **Internal** | `/internal/v1/{module}/...` | Backend → Backend | Module gọi module |

Internal API:
- KHÔNG expose qua Nginx ra ngoài
- Chỉ chấp nhận request từ localhost hoặc IP nội bộ
- Xác thực bằng `X-Internal-Key` header (shared secret giữa services)
- Response format giống External API

### 3. Response format chuẩn

```json
// Thành công
{
  "success": true,
  "data": { ... },
  "message": "Thao tác thành công",
  "pagination": {               // Chỉ với list
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5
  }
}

// Lỗi
{
  "success": false,
  "error": {
    "code": "MODULE_ERR_001",
    "message": "Mô tả lỗi tiếng Việt"
  }
}
```

### 4. Error code convention

```
KPI_ERR_xxx    — Lỗi từ module KPI
LMS_ERR_xxx    — Lỗi từ module LMS
FORUM_ERR_xxx  — Lỗi từ module Forum
LEGAL_ERR_xxx  — Lỗi từ module Legal
PORTAL_ERR_xxx — Lỗi từ module Portal
CMN_ERR_xxx    — Lỗi từ Common services
AUTH_ERR_xxx   — Lỗi xác thực
```

---

## II. CONTRACT: COMMON SERVICES (Port chung hoặc Common API)

Tất cả module đều cần gọi Common để ghi notification, upload file, ghi KPI log.

### 2.1. Ghi thông báo

```
POST /internal/v1/common/thong-bao
```

Request:
```json
{
  "nguoi_nhan_id": "uuid",
  "tieu_de": "Bạn được giao khóa học mới",
  "noi_dung": "Khóa học 'Luật Hải quan 2024' cần hoàn thành trước 30/03",
  "loai": "LMS",
  "muc_do": "QUAN_TRONG",
  "link_url": "/dao-tao/khoa-hoc/uuid-khoa-hoc",
  "doi_tuong_type": "KHOA_HOC",
  "doi_tuong_id": "uuid-khoa-hoc"
}
```

Response: `{"success": true, "data": {"id": "uuid-thong-bao"}}`

**Gửi thông báo hàng loạt:**

```
POST /internal/v1/common/thong-bao/batch
```

Request:
```json
{
  "nguoi_nhan_ids": ["uuid-1", "uuid-2", "uuid-3"],
  "tieu_de": "Văn bản khẩn cần đọc",
  "noi_dung": "Nghị định 335/2025/NĐ-CP cần đọc trong 24h",
  "loai": "LEGAL",
  "muc_do": "KHAN",
  "link_url": "/phap-luat/van-ban/uuid-vb",
  "doi_tuong_type": "VAN_BAN",
  "doi_tuong_id": "uuid-vb"
}
```

### 2.2. Ghi KPI Integration Log

```
POST /internal/v1/common/kpi-log
```

Request:
```json
{
  "cong_chuc_id": "uuid",
  "thang": 3,
  "nam": 2026,
  "module": "LMS",
  "metrics": {
    "khoa_hoc_hoan_thanh": 3,
    "diem_trung_binh": 85.5,
    "chung_chi_dat": 2,
    "tong_thoi_gian_hoc_phut": 480
  }
}
```

Logic: UPSERT — nếu đã có record (cong_chuc_id + thang + nam + module), cập nhật metrics.

### 2.3. Upload file

```
POST /internal/v1/common/file/upload
Content-Type: multipart/form-data
```

Fields:
```
file: <binary>
module: "LMS"
doi_tuong_type: "BAI_HOC"
doi_tuong_id: "uuid-bai-hoc"
nguoi_tai_len_id: "uuid-cong-chuc"
```

Response:
```json
{
  "success": true,
  "data": {
    "id": "uuid-file",
    "file_url": "https://kv08.vn/files/lms/videos/uuid.mp4",
    "file_path": "lms/videos/uuid.mp4",
    "file_size_bytes": 52428800,
    "mime_type": "video/mp4"
  }
}
```

### 2.4. Đọc thông báo chưa đọc (cho Frontend)

```
GET /api/v1/common/thong-bao?da_doc=false&page=1&page_size=20
Header: Authorization: Bearer <jwt>
```

### 2.5. Đánh dấu đã đọc

```
PATCH /api/v1/common/thong-bao/{id}/doc
Header: Authorization: Bearer <jwt>
```

---

## III. CONTRACT: LMS → CÁC MODULE KHÁC

### 3.1. LMS → Common: Khi CBCC hoàn thành khóa học

**Trigger:** `dang_ky_khoa_hoc.trang_thai` chuyển sang `HOAN_THANH`

**Actions:**
1. Ghi notification cho CBCC: "Chúc mừng! Bạn đã hoàn thành khóa học X"
2. Ghi notification cho lãnh đạo đơn vị: "CBCC Y đã hoàn thành khóa học X"
3. Cập nhật `kpi_integration_log` với metrics mới

### 3.2. LMS → Common: Khi giao khóa bắt buộc

**Trigger:** QT đào tạo tạo `dang_ky_khoa_hoc` với `loai_dang_ky = 'BAT_BUOC'`

**Actions:**
1. Ghi notification cho CBCC: "Bạn được giao khóa học bắt buộc X, hạn DD/MM"
2. Nếu muc_do = KHAN → gửi email (nếu có)

### 3.3. LMS → Common: Nhắc hạn

**Trigger:** Cron job hàng ngày kiểm tra `dang_ky_khoa_hoc.han_hoan_thanh`

**Actions:**
1. Còn 3 ngày → notification "Sắp hết hạn khóa học X"
2. Quá hạn → notification "Đã quá hạn khóa học X" + cập nhật trạng thái

---

## IV. CONTRACT: FORUM → CÁC MODULE KHÁC

### 4.1. Forum → Legal: Lấy thông tin VB để trích dẫn

```
GET /internal/v1/legal/van-ban/{id}/summary
```

Response:
```json
{
  "success": true,
  "data": {
    "id": "uuid-vb",
    "so_hieu": "335/2025/NĐ-CP",
    "trich_yeu": "Quy định xử phạt vi phạm hành chính...",
    "trang_thai_hieu_luc": "CON_HIEU_LUC",
    "link": "/phap-luat/van-ban/uuid-vb"
  }
}
```

**Dùng khi:** CBCC trích dẫn căn cứ pháp lý trong câu trả lời diễn đàn.

### 4.2. Forum → Legal: Tìm kiếm VB liên quan

```
GET /internal/v1/legal/van-ban/search?q=thuế+XNK&limit=5
```

Response: danh sách VB khớp, dùng cho autocomplete khi CBCC nhập trích dẫn.

### 4.3. Forum → Common: Khi có trả lời mới / upvote

**Trigger:** Tạo `tra_loi` mới hoặc `bieu_quyet` mới

**Actions:**
1. Notification cho tác giả chủ đề: "Có trả lời mới cho chủ đề X"
2. Notification cho tất cả người theo dõi (`forum.theo_doi`)
3. Cập nhật `kpi_integration_log` cuối tháng (cron job)

### 4.4. Forum → Common/Knowledge Base: Chuyển bài → SOP

```
POST /internal/v1/common/knowledge-base
```

Request:
```json
{
  "loai": "SOP",
  "tieu_de": "Quy trình khai báo hàng tạm nhập tái xuất",
  "noi_dung": "<html>...</html>",
  "chu_so_huu_id": "uuid-chuyen-gia",
  "chu_de_forum_lien_quan": ["uuid-chu-de-goc"],
  "van_ban_lien_quan": ["uuid-vb-1", "uuid-vb-2"]
}
```

---

## V. CONTRACT: LEGAL → CÁC MODULE KHÁC

### 5.1. Legal → Common: Khi xuất bản VB mới

**Trigger:** `van_ban.trang_thai_duyet` chuyển sang `DA_XUAT_BAN`

**Actions:**
1. Nếu `bat_buoc_doc = TRUE`:
   - Tạo `xac_nhan_doc` cho TẤT CẢ CBCC (hoặc theo `doi_tuong_ap_dung`)
   - Ghi notification batch: "Văn bản mới cần đọc: [số hiệu]"
   - Nếu `muc_do = 'KHAN'` → muc_do notification = KHAN
2. Nếu `bat_buoc_doc = FALSE`:
   - Ghi notification thông thường

### 5.2. Legal → Common: Nhắc hạn xác nhận đọc

**Trigger:** Cron job hàng ngày kiểm tra `van_ban.han_xac_nhan`

**Actions:**
1. Còn 1 ngày → notification "Sắp hết hạn xác nhận VB [số hiệu]"
2. Quá hạn → notification "Quá hạn xác nhận VB [số hiệu]"
3. Báo cáo danh sách chưa đọc cho lãnh đạo đơn vị

### 5.3. Legal → Common: Cập nhật KPI log cuối tháng

**Trigger:** Cron job cuối tháng

**Logic:**
```python
for each cong_chuc:
    metrics = {
        "vb_da_doc": count(xac_nhan_doc WHERE da_doc=TRUE AND thang=X),
        "vb_chua_doc": count(xac_nhan_doc WHERE da_doc=FALSE AND thang=X),
        "vb_qua_han": count(xac_nhan_doc WHERE qua_han=TRUE AND thang=X),
        "quiz_hoan_thanh": count(ket_qua_quiz WHERE thang=X),
        "quiz_diem_tb": avg(ket_qua_quiz.diem WHERE thang=X)
    }
    POST /internal/v1/common/kpi-log
```

---

## VI. CONTRACT: PORTAL → TẤT CẢ MODULE (Dashboard Aggregation)

### 6.1. Dashboard tổng hợp — lấy dữ liệu từ mỗi module

Portal Frontend gọi từng API riêng (không qua Internal):

```
// Widget KPI
GET /api/v1/kpi/dashboard/summary
→ {"diem_thang_nay": 85, "xep_loai": "A", "ke_khai_cho_duyet": 3}

// Widget LMS
GET /api/v1/lms/dashboard/summary
→ {"khoa_dang_hoc": 2, "khoa_sap_het_han": 1, "chung_chi_moi": 1}

// Widget Forum
GET /api/v1/forum/dashboard/summary
→ {"chu_de_moi_tuan": 5, "tra_loi_chua_doc": 3, "upvote_tuan": 12}

// Widget Legal
GET /api/v1/legal/dashboard/summary
→ {"vb_moi_tuan": 3, "vb_chua_doc": 2, "vb_khan": 1}

// Widget Notification
GET /api/v1/common/thong-bao/count?da_doc=false
→ {"count": 7}
```

Mỗi module **BẮT BUỘC** phải implement endpoint `/dashboard/summary` trả về dữ liệu widget.

### 6.2. Dashboard lãnh đạo — thống kê đơn vị

```
// Thống kê KPI đơn vị
GET /api/v1/kpi/bao-cao/don-vi/{don_vi_id}?thang=3&nam=2026

// Thống kê đào tạo đơn vị
GET /api/v1/lms/bao-cao/don-vi/{don_vi_id}?thang=3&nam=2026

// Thống kê pháp luật đơn vị
GET /api/v1/legal/bao-cao/don-vi/{don_vi_id}?thang=3&nam=2026

// Tổng hợp từ KPI Integration Log
GET /api/v1/common/kpi-log/don-vi/{don_vi_id}?thang=3&nam=2026
```

### 6.3. Unified Search

```
GET /api/v1/common/search?q=thuế+XNK&modules=lms,forum,legal,portal&page=1
```

Response:
```json
{
  "success": true,
  "data": {
    "results": [
      {"module": "LEGAL", "type": "VAN_BAN", "id": "uuid", "title": "...", "snippet": "...", "score": 0.95},
      {"module": "FORUM", "type": "CHU_DE", "id": "uuid", "title": "...", "snippet": "...", "score": 0.88},
      {"module": "LMS", "type": "KHOA_HOC", "id": "uuid", "title": "...", "snippet": "...", "score": 0.75}
    ],
    "total_by_module": {"LEGAL": 5, "FORUM": 12, "LMS": 3, "PORTAL": 1}
  }
}
```

Logic: Common service query tsvector trên các bảng có search_vector.

---

## VII. CONTRACT: KPI → COMMON (Đọc dữ liệu tích hợp)

KPI module **chỉ đọc** từ `kpi_integration_log`, KHÔNG ghi.

```
// Dashboard KPI đọc dữ liệu bổ sung
GET /internal/v1/common/kpi-log/{cong_chuc_id}?thang=3&nam=2026
```

Response:
```json
{
  "success": true,
  "data": [
    {"module": "LMS", "metrics": {"khoa_hoc_hoan_thanh": 3, ...}, "diem_quy_doi": 8.5},
    {"module": "FORUM", "metrics": {"bai_dang": 5, ...}, "diem_quy_doi": 5.0},
    {"module": "LEGAL", "metrics": {"vb_da_doc": 8, ...}, "diem_quy_doi": 9.0}
  ]
}
```

> ⚠️ Dữ liệu này hiển thị THAM KHẢO bên cạnh điểm KPI. KHÔNG tự động thay đổi điểm.

---

## VIII. BẢNG TÓM TẮT TẤT CẢ ENDPOINT INTERNAL

| Endpoint | Method | Caller | Provider | Mục đích |
|----------|--------|--------|----------|----------|
| `/internal/v1/common/thong-bao` | POST | LMS/Forum/Legal | Common | Ghi notification |
| `/internal/v1/common/thong-bao/batch` | POST | Legal | Common | Notification hàng loạt |
| `/internal/v1/common/kpi-log` | POST | LMS/Forum/Legal | Common | Ghi KPI integration |
| `/internal/v1/common/file/upload` | POST | LMS/Forum/Legal | Common | Upload file |
| `/internal/v1/common/knowledge-base` | POST | Forum | Common | Tạo SOP/FAQ |
| `/internal/v1/common/kpi-log/{cc_id}` | GET | KPI | Common | Đọc dữ liệu tích hợp |
| `/internal/v1/legal/van-ban/{id}/summary` | GET | Forum | Legal | Lấy info VB trích dẫn |
| `/internal/v1/legal/van-ban/search` | GET | Forum | Legal | Tìm VB autocomplete |

---

## IX. BẢNG TÓM TẮT ENDPOINT DASHBOARD (BẮT BUỘC MỖI MODULE)

| Endpoint | Module | Frontend dùng cho |
|----------|--------|-------------------|
| `GET /api/v1/kpi/dashboard/summary` | KPI | Widget KPI |
| `GET /api/v1/lms/dashboard/summary` | LMS | Widget Đào tạo |
| `GET /api/v1/forum/dashboard/summary` | Forum | Widget Diễn đàn |
| `GET /api/v1/legal/dashboard/summary` | Legal | Widget Pháp luật |
| `GET /api/v1/common/thong-bao/count` | Common | Badge notification |
| `GET /api/v1/common/search` | Common | Unified search |

---

## X. QUY TẮC THAY ĐỔI CONTRACT

```
1. Developer muốn thêm/sửa Internal API
       ↓
2. Mô tả: endpoint, request, response, trigger
       ↓
3. Gửi cho Tech Lead (HUB project) review
       ↓
4. Tech Lead cập nhật file này
       ↓
5. Thông báo các project liên quan cập nhật tài liệu
       ↓
6. Cả 2 bên (caller + provider) implement
       ↓
7. Test tích hợp trên develop branch
```

> **KHÔNG ĐƯỢC tự thêm Internal API mà không qua HUB.**
