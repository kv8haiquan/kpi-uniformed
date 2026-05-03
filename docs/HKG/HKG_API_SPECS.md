# HKG_API_SPECS.md — API Specifications

**Phiên bản:** 1.0 (MVP) · **Ngày:** 30/04/2026
**Backend:** FastAPI port **8006** · **Base path:** `/api/v1/hop-khong-giay/`

---

## 1. NGUYÊN TẮC API

```
✅ TUÂN THỦ:
- REST (GET/POST/PUT/PATCH/DELETE)
- JWT Bearer token bắt buộc cho mọi endpoint (trừ /health)
- Response chuẩn: { "data": ..., "meta": {...} }
- Pagination: ?page=1&limit=20 (default 20, max 100)
- Error: HTTP status + { "error": { "code": "...", "message": "..." } }
- Soft delete: DELETE chỉ set is_deleted=TRUE, không xoá hẳn
- Audit log: mọi mutation phải ghi vào common.audit_log

⛔ TRÁNH:
- KHÔNG expose UUID nội bộ qua URL nếu nhạy cảm — dùng JWT để auth
- KHÔNG trả về password hash, secret keys
- KHÔNG hard-code role check — dùng dependency permission
```

---

## 2. CẤU TRÚC URL

```
http://localhost:8006
└── /api/v1/hop-khong-giay/
    ├── /health                          GET   (no auth)
    ├── /cuoc-hop/                       Module 1
    ├── /thong-bao/                      Module 2
    ├── /tai-lieu/                       Module 3
    ├── /diem-danh/                      Module 4
    ├── /xin-phep-vang/                  Module 5
    ├── /y-kien/                         (Module 7 cơ bản)
    ├── /bien-ban/                       Module 9
    ├── /ket-luan/                       Module 10
    └── /thong-ke/                       Dashboard 1 cấp
```

---

## 3. AUTHENTICATION

### 3.1. JWT Bearer

```
Authorization: Bearer <jwt_token>
```

JWT payload (đã có chuẩn, HKG chỉ đọc):
```json
{
  "sub": "{cong_chuc_id}",
  "ho_ten": "Nguyễn Văn A",
  "vai_tro": "TRUONG_DON_VI",
  "don_vi_id": "{uuid}",
  "is_lanh_dao": true,
  "platform_roles": ["THU_KY_HOP", "DANG_VIEN"],
  "exp": 1234567890
}
```

> **Lưu ý triển khai (verify P0 — 2026-04-30):** field `platform_roles[]` **đã có sẵn** trong JWT của codebase hiện tại. Code injection nằm tại `backend/app/api/v1/endpoints/auth.py` — block "MO RONG PLATFORM (3 fields moi)" — query `public.platform_role` JOIN `public.cong_chuc_platform_role` rồi đính `[ma_role for r in roles]` vào claims.
>
> → KHÔNG còn là blocker cho G2. Chỉ cần verify trong G0:
> 1. Login user có gán `THU_KY_HOP` → JWT decode ra `platform_roles: ["THU_KY_HOP"]` đúng.
> 2. HKG service decode JWT bằng cùng `SECRET_KEY` → đọc được `platform_roles[]`.

### 3.2. Permission helper (dùng nội bộ)

```python
# backend/meeting_service/dependencies.py

def require_role(role: str):
    """vai_tro KPI"""
    ...

def require_platform_role(role: str):
    """platform_role HKG"""
    ...

def require_can_view_meeting(cuoc_hop_id):
    """Logic: được mời / là chủ tọa / là lãnh đạo đv / role đặc biệt"""
    ...

def require_can_edit_meeting(cuoc_hop_id):
    """Chỉ chu_toa, thu_ky, hoặc admin"""
    ...
```

---

## 4. MODULE 1 — QUẢN LÝ CUỘC HỌP

### 4.1. Tạo cuộc họp
```
POST /cuoc-hop/

Body:
{
  "tieu_de": "Giao ban tuần Phòng CNTT",
  "mo_ta": "...",
  "khoi": "CHUYEN_MON",
  "hinh_thuc": "TRUC_TIEP",
  "ngay_hop": "2026-05-15",
  "gio_bat_dau": "08:30",
  "gio_ket_thuc": "10:00",
  "dia_diem": "Phòng họp số 1",
  "don_vi_to_chuc_id": "{uuid}",
  "chu_toa_id": "{uuid}",
  "thu_ky_id": "{uuid}",
  "thanh_phan": [
    {"cong_chuc_id": "{uuid}", "loai_tham_du": "BAT_BUOC"},
    {"cong_chuc_id": "{uuid}", "loai_tham_du": "THAM_KHAO"}
  ]
}

Response: 201
{
  "data": {
    "id": "{uuid}",
    "tieu_de": "...",
    ...
  }
}

Permission: require_role(SUPER_ADMIN | CHI_CUC_TRUONG | PHO_CHI_CUC_TRUONG | TRUONG_DON_VI | PHO_DON_VI)
       OR  require_platform_role(CHU_TOA_HOP | CHANH_VP | TRUONG_CNTT)

Side effects:
- Insert meeting.cuoc_hop
- Insert N records meeting.thanh_phan
- Audit log: CREATE_MEETING
```

### 4.2. Lấy danh sách cuộc họp
```
GET /cuoc-hop/?page=1&limit=20
              &ngay_tu=2026-05-01&ngay_den=2026-05-31
              &don_vi_id={uuid}
              &khoi=CHUYEN_MON
              &trang_thai=DA_THONG_BAO

Response: 200
{
  "data": [
    {
      "id": "{uuid}",
      "tieu_de": "...",
      "ngay_hop": "2026-05-15",
      "gio_bat_dau": "08:30",
      "trang_thai": "DA_THONG_BAO",
      "chu_toa": {"id": "...", "ho_ten": "..."},
      "don_vi_to_chuc": {"id": "...", "ten_don_vi": "..."},
      "so_thanh_phan": 12
    }
  ],
  "meta": {"total": 45, "page": 1, "limit": 20}
}

Permission: dùng require_can_view_meeting để filter.
- CBCC thường → chỉ thấy cuộc họp được mời
- LĐ ĐV → cuộc họp đơn vị mình
- CHANH_VP / TRUONG_CNTT / CCT / PCCT → toàn bộ
```

### 4.3. Chi tiết cuộc họp
```
GET /cuoc-hop/{id}

Response: 200
{
  "data": {
    "id": "...",
    "tieu_de": "...",
    "thanh_phan": [...],
    "tai_lieu": [...],
    "diem_danh_summary": { "co_mat": 8, "vang_phep": 2, "vang_khong_phep": 0 },
    "co_bien_ban": true,
    ...
  }
}

Permission: require_can_view_meeting
```

### 4.4. Cập nhật cuộc họp
```
PATCH /cuoc-hop/{id}

Body: (chỉ những field cần đổi)
{
  "ngay_hop": "2026-05-16",
  "dia_diem": "Phòng họp số 2"
}

Response: 200

Permission: require_can_edit_meeting
Side effects:
- Update meeting.cuoc_hop
- Insert thông báo THAY_DOI_HOP cho tất cả thành phần
- Audit log: UPDATE_MEETING
```

### 4.5. Hủy cuộc họp
```
POST /cuoc-hop/{id}/huy

Body:
{
  "ly_do": "Lãnh đạo đột xuất bận"
}

Response: 200

Side effects:
- Update trang_thai = HUY
- Insert thông báo HUY_HOP cho tất cả thành phần
- Audit log: CANCEL_MEETING
```

### 4.6. Gửi giấy mời
```
POST /cuoc-hop/{id}/gui-giay-moi

Response: 200
{
  "data": {"so_giay_moi_da_gui": 12}
}

Side effects:
- Update trang_thai = DA_THONG_BAO
- Insert thông báo GIAY_MOI_HOP cho tất cả thành phần
- Schedule Celery task: nhắc 24h, 1h, 30p trước họp
- Audit log: SEND_INVITATION
```

### 4.7. Xác nhận tham dự (CBCC tự xác nhận)
```
POST /cuoc-hop/{id}/xac-nhan

Body:
{
  "xac_nhan": "THAM_DU",        // hoặc KHONG_THAM_DU, UY_QUYEN
  "nguoi_uy_quyen_id": "...",   // nếu UY_QUYEN
  "ghi_chu": "..."
}

Response: 200
```

---

## 5. MODULE 3 — TÀI LIỆU HỌP

### 5.1. Upload tài liệu
```
POST /tai-lieu/upload
Content-Type: multipart/form-data

Form fields:
- cuoc_hop_id: UUID
- file: binary
- ten_tai_lieu: string (optional, default = filename)
- mo_ta: string (optional)
- phan_quyen: CONG_KHAI | HAN_CHE
- cho_phep_tai: bool
- cho_phep_in: bool

Response: 201
{
  "data": {
    "id": "...",
    "ten_tai_lieu": "...",
    "minio_key": "tai-lieu/{cuoc_hop_id}/{filename}",
    "file_size": 123456,
    "mime_type": "application/pdf"
  }
}

Permission: require_can_edit_meeting
Side effects:
- Upload to MinIO bucket `meeting`
- Insert meeting.tai_lieu
- Audit log: UPLOAD_DOC
```

### 5.2. Danh sách tài liệu của cuộc họp
```
GET /cuoc-hop/{cuoc_hop_id}/tai-lieu

Response: 200
{
  "data": [
    {
      "id": "...",
      "ten_tai_lieu": "...",
      "extension": "pdf",
      "file_size": 123456,
      "phan_quyen": "CONG_KHAI",
      "cho_phep_tai": true,
      "cho_phep_in": false,
      "url_xem": "/api/v1/hop-khong-giay/tai-lieu/{id}/xem"  // signed URL
    }
  ]
}
```

### 5.3. Xem tài liệu (short-lived URL)
```
GET /tai-lieu/{id}/xem

Response: 302 Redirect tới URL kèm JWT short-lived token (TTL 1h)

Side effects:
- Audit log: VIEW_DOC
```

> **MVP storage note (verify P0 — 2026-05-01):** dùng filesystem (`uploads/meeting/...`)
> theo pattern LMS, **KHÔNG presigned MinIO URL**. URL trả về dạng:
> `/api/v1/hop-khong-giay/tai-lieu/{id}/xem-noi-dung?t=<jwt_short_lived>`.
> Token verify trong endpoint serve file. Khi nâng cấp MinIO (Phase 4+) thay
> bằng presigned URL thật — DB schema giữ nguyên.

### 5.4. Tải tài liệu
```
GET /tai-lieu/{id}/tai

Response: 302 Redirect tới URL kèm JWT short-lived token + flag download=1

Permission: kiểm tra cho_phep_tai = TRUE
Side effects:
- Audit log: DOWNLOAD_DOC
- Error 403 nếu cho_phep_tai = FALSE
```

### 5.5. Xóa tài liệu (soft delete)
```
DELETE /tai-lieu/{id}

Response: 200
```

---

## 6. MODULE 4 — ĐIỂM DANH

### 6.1. Tạo QR điểm danh
```
GET /cuoc-hop/{id}/qr-diem-danh

Response: 200
{
  "data": {
    "qr_code_base64": "data:image/png;base64,...",
    "qr_url": "/hop-khong-giay/diem-danh-qr?token={short_token}",
    "expires_at": "2026-05-15T10:00:00Z"  // hết giờ họp
  }
}

Logic: tạo short-lived token (JWT 30s TTL), encode vào QR.
```

### 6.2. Điểm danh QR (CBCC quét)
```
POST /diem-danh/qr

Body:
{
  "token": "{token_từ_QR}"
}

Response: 200
{
  "data": {
    "trang_thai": "CO_MAT",  // hoặc DEN_MUON nếu quá 5 phút sau gio_bat_dau
    "gio_diem_danh": "2026-05-15T08:32:00Z"
  }
}

Permission: CBCC phải có trong meeting.thanh_phan
Side effects:
- Insert meeting.diem_danh
- Audit log: CHECKIN_QR
```

### 6.3. Điểm danh bấm tay (Thư ký)
```
POST /diem-danh/bam-tay

Body:
{
  "cuoc_hop_id": "...",
  "diem_danh": [
    {"cong_chuc_id": "...", "trang_thai": "CO_MAT"},
    {"cong_chuc_id": "...", "trang_thai": "VANG_KHONG_PHEP"}
  ]
}

Response: 200

Permission: chu_toa hoặc thu_ky của cuộc họp
```

### 6.4. Tổng hợp điểm danh
```
GET /cuoc-hop/{id}/diem-danh

Response: 200
{
  "data": {
    "tong_so": 12,
    "co_mat": 9,
    "den_muon": 1,
    "vang_co_phep": 2,
    "vang_khong_phep": 0,
    "chi_tiet": [...]
  }
}
```

---

## 7. MODULE 5 — XIN PHÉP VẮNG

### 7.1. Gửi đơn xin vắng
```
POST /xin-phep-vang/

Body:
{
  "cuoc_hop_id": "...",
  "ly_do": "...",
  "nguoi_du_thay_id": "...",  // optional
  "file_dinh_kem": "..."       // optional, minio_key sau khi upload riêng
}

Response: 201
```

### 7.2. Duyệt đơn (Chủ tọa)
```
POST /xin-phep-vang/{id}/duyet

Body:
{
  "quyet_dinh": "DA_DUYET",  // hoặc TU_CHOI
  "ly_do_tu_choi": "..."     // nếu TU_CHOI
}

Permission: chu_toa của cuộc họp
```

### 7.3. Auto-approve (Celery task)
```
Internal — chạy tự động:
- Sau 4h Chủ tọa không duyệt → chuyển cho Thư ký
- Đến giờ họp Thư ký vẫn không duyệt → auto_approved = TRUE
```

---

## 8. MODULE 9 — BIÊN BẢN

### 8.1. Tạo / cập nhật biên bản (Thư ký)
```
PUT /cuoc-hop/{id}/bien-ban

Body:
{
  "noi_dung_json": {...},  // TipTap JSON
  "noi_dung_html": "<p>...</p>"
}

Response: 200
{
  "data": {
    "id": "...",
    "trang_thai": "DANG_SOAN"
  }
}

Permission: thu_ky_id = current user
```

### 8.2. Trình ký
```
POST /bien-ban/{id}/trinh-ky

Response: 200
- Update trang_thai = TRINH_KY
- Insert thông báo BIEN_BAN_TRINH_KY cho chu_toa
```

### 8.3. Ký biên bản (Mock CKS — MVP)
```
POST /bien-ban/{id}/ky

Body:
{
  "nguoi_ky_id": "..."  // tự động lấy từ JWT
}

Response: 200
{
  "data": {
    "trang_thai": "DA_KY",
    "qr_xac_thuc": "https://kv08.vn/verify/{hash}",
    "hash_noi_dung": "abc123...",
    "is_mock_signed": true
  }
}

Permission: nguoi_ky_id = chu_toa của cuộc họp
Logic MVP:
- Tính SHA-256 của noi_dung_json
- Sinh QR code link verify
- Set is_mock_signed = TRUE
- Phase 6 sẽ thay bằng ký PAdES thật
```

### 8.4. Xuất biên bản DOCX/PDF
```
POST /bien-ban/{id}/xuat?dinh-dang=docx
POST /bien-ban/{id}/xuat?dinh-dang=pdf

Response: 200
{
  "data": {
    "minio_key": "bien-ban/{cuoc_hop_id}/bien_ban.docx",
    "url_tai": "/api/v1/hop-khong-giay/bien-ban/{id}/tai?dinh-dang=docx"
  }
}

Logic:
- Lấy template mặc định từ meeting.mau_bieu (la_mac_dinh=TRUE, ap_dung_cho='TAT_CA')
- Render placeholder: {{ten_cuoc_hop}}, {{ngay_hop}}, {{chu_tri}}, {{thu_ky}},
  {{danh_sach_tham_du}}, {{ket_luan}}, ...
- python-docx → DOCX, weasyprint → PDF
- Watermark + QR cho PDF
- Upload MinIO, lưu key vào file_pdf_minio_key / file_docx_minio_key
```

---

## 9. MODULE 10 — KẾT LUẬN & NHẮC HẠN

### 9.1. Tạo kết luận / nhiệm vụ
```
POST /cuoc-hop/{id}/ket-luan

Body:
{
  "noi_dung": "Báo cáo tiến độ dự án X trước 15/6",
  "nguoi_phu_trach_id": "...",
  "don_vi_phu_trach_id": "...",
  "han_hoan_thanh": "2026-06-15",
  "muc_uu_tien": "CAO"
}

Response: 201
Side effects:
- Insert meeting.ket_luan
- Thông báo KET_LUAN_GIAO cho nguoi_phu_trach_id
- Schedule Celery: nhắc 3 ngày trước han_hoan_thanh
```

### 9.2. Cập nhật tiến độ
```
POST /ket-luan/{id}/tien-do

Body:
{
  "phan_tram_sau": 60,
  "mo_ta": "Đã hoàn thành phân tích, đang viết báo cáo",
  "file_minh_chung": "..."  // optional
}

Response: 201
Side effects:
- Insert meeting.tien_do (snapshot phan_tram_truoc)
- Update meeting.ket_luan.tien_do_phan_tram
- Auto set trang_thai = HOAN_THANH nếu = 100
- Auto set trang_thai = DANG_LAM nếu > 0

Permission: nguoi_phu_trach_id = current user
```

### 9.3. Danh sách kết luận của tôi
```
GET /ket-luan/cua-toi?trang_thai=DANG_LAM

Response: 200
{
  "data": [...]
}
```

### 9.4. Danh sách kết luận đơn vị (LĐ ĐV / Chánh VP / TP CNTT)
```
GET /ket-luan/cua-don-vi/{don_vi_id}

Permission: is_lanh_dao_dv của đơn vị đó hoặc role mở rộng
```

---

## 10. THỐNG KÊ DASHBOARD

### 10.1. Dashboard cá nhân
```
GET /thong-ke/ca-nhan

Response: 200
{
  "data": {
    "so_cuoc_hop_thang_nay": 12,
    "so_cuoc_hop_tham_du": 11,
    "so_lan_vang": 1,
    "ty_le_tham_du": 91.7,
    "nhiem_vu_dang_lam": 3,
    "nhiem_vu_qua_han": 0
  }
}
```

### 10.2. Dashboard đơn vị (LĐ ĐV)
```
GET /thong-ke/don-vi/{don_vi_id}?tu=2026-05-01&den=2026-05-31

Response: 200
{
  "data": {
    "so_cuoc_hop": 23,
    "ty_le_tham_du_trung_binh": 87.5,
    "so_nhiem_vu_giao": 45,
    "so_nhiem_vu_hoan_thanh": 32,
    "so_nhiem_vu_qua_han": 3,
    "chi_tiet": [...]
  }
}

Permission: is_lanh_dao của đơn vị + Chánh VP + TP CNTT + CCT/PCCT
```

---

## 11. INTERNAL API (cho module khác gọi)

### 11.1. Số cuộc họp đã tham dự của 1 CBCC
```
GET /api/v1/hop-khong-giay/internal/cong-chuc/{id}/so-cuoc-hop

Auth: Internal API key (giữa các backend service)
Response:
{
  "data": {
    "thang_nay": 12,
    "thang_truoc": 15
  }
}

Use case: KPI module có thể tính điểm CBCC dựa vào tỷ lệ tham dự họp
```

### 11.2. Cuộc họp sắp diễn ra của 1 CBCC (cho Portal Dashboard)
```
GET /api/v1/hop-khong-giay/internal/cong-chuc/{id}/sap-toi?limit=5
```

---

## 11A. HELPER ENDPOINTS (cho frontend HKG)

### 11A.1. Search CBCC

> **Bổ sung G4-fix-2 (01/05/2026)**: tách khỏi LMS endpoint `/api/v1/lms/cbcc/search` để mở permission cho role HKG đặc thù (THU_KY_HOP). Read-only — KHÔNG ghi audit log.

```
GET /api/v1/hop-khong-giay/cong-chuc/search
    ?q=<text>           # min 1, max 200 ký tự
    &limit=<int>        # default 20, max 50

Auth: Bearer JWT
ACL:
  - vai_tro KPI ∈ {SUPER_ADMIN, ADMIN, CCT, PCCT, TDV, PDV}
  - HOẶC platform_roles ∋ {THU_KY_HOP, CHANH_VP, TRUONG_CNTT, BI_THU_CHI_BO}
  - HOẶC is_lanh_dao = TRUE
  - Còn lại → 403 NO_PERMISSION

Logic:
  - SELECT từ public.cong_chuc WHERE is_active=TRUE AND is_deleted=FALSE
  - Filter: ho_ten ILIKE %q% OR ma_cc ILIKE %q% OR email ILIKE %q%
  - JOIN public.don_vi → ten_don_vi
  - JOIN public.vai_tro → ma_vai_tro
  - ORDER BY ho_ten, LIMIT :limit
  - Parameterized query — SQL injection safe

Response: 200
{
  "success": true,
  "data": [
    {
      "id": "uuid-string",
      "ho_ten": "Nguyễn Văn A",
      "ma_cc": "20ZZ-0224",
      "email": "a@example.com",
      "chuc_vu": "Đội trưởng",
      "ten_don_vi": "Đội Nghiệp vụ 1",
      "ma_vai_tro": "TDV"
    }
  ]
}

Use case: type-ahead picker trong form tạo cuộc họp (chu_toa, thu_ky, thành phần).
```

---

## 12. ERROR CODES

```
400 Bad Request            VALIDATION_ERROR
401 Unauthorized           NO_TOKEN | EXPIRED_TOKEN | INVALID_TOKEN
403 Forbidden              NO_PERMISSION | NOT_INVITED | NOT_CHU_TOA
404 Not Found              MEETING_NOT_FOUND | DOC_NOT_FOUND
409 Conflict               ALREADY_CHECKED_IN | ALREADY_INVITED
422 Unprocessable          MEETING_ALREADY_STARTED | DOC_TOO_LARGE
500 Internal               UNKNOWN_ERROR | DB_ERROR | MINIO_ERROR
```

Format response error:
```json
{
  "error": {
    "code": "NO_PERMISSION",
    "message": "Bạn không có quyền chỉnh sửa cuộc họp này",
    "details": {}
  }
}
```

---

## 13. RATE LIMITING (Phase sau, MVP chưa cần)

```
Endpoint                     | Limit
GET /cuoc-hop/               | 100/min/user
POST /tai-lieu/upload        | 20/hour/user
POST /diem-danh/qr           | 10/min/user
POST /bien-ban/{id}/xuat     | 30/hour/user
```

---

## 14. CHECKLIST KIỂM TRA TRƯỚC KHI MERGE CODE

```
□ Tất cả endpoint có require auth (trừ /health)
□ Permission check rõ ràng, không hard-code role
□ Mọi mutation ghi vào common.audit_log với module='MEETING'
□ Mọi notification ghi vào common.thong_bao với module='MEETING'
□ Soft delete thay vì DELETE thật
□ Validation Pydantic schema đầy đủ
□ Có test case cho happy path + 1 error path
□ Swagger UI hiển thị đầy đủ description
□ Không log JWT token / password ra console
```

---

*File này dùng làm spec authoritative khi sinh API endpoint. Mọi thay đổi phải cập nhật file này trước khi code.*
