# KPI LIÊN KẾT NỀN TẢNG
## Hướng dẫn tích hợp KPI với Nền tảng Số mới — HQKV8

> **Phiên bản:** 1.0 | **Ngày:** 18/02/2026
> **Dành cho:** Project KPI (Bảo trì & UAT) — Dev A
> **Mục đích:** Giúp người bảo trì KPI hiểu những thay đổi từ nền tảng mới mà KHÔNG cần biết chi tiết module mới

---

## I. TÓM TẮT: CHUYỆN GÌ ĐANG XẢY RA?

Hệ thống KPI (v1.0) đang được **mở rộng** thành Nền tảng Số gồm 5 module:
KPI + E-Learning + Diễn đàn + Pháp luật + Portal

**Ảnh hưởng đến KPI production:**
```
✅ Database KPI:        GIỮ NGUYÊN 100%
✅ API KPI:             GIỮ NGUYÊN 100%
✅ Business logic KPI:  GIỮ NGUYÊN 100%
✅ Frontend KPI pages:  GIỮ NGUYÊN 100%
⚠️ JWT payload:         THÊM 1 field mới (platform_roles)
⚠️ Schema public:       THÊM 2 bảng mới (platform_role, cong_chuc_platform_role)
⚠️ Frontend layout:     Sidebar được MỞ RỘNG thêm menu
⚠️ Dashboard:           THÊM widget từ module mới bên cạnh widget KPI
```

**Kết luận:** Code KPI hiện tại KHÔNG cần sửa. Nhưng cần BIẾT về những thay đổi xung quanh.

---

## II. THAY ĐỔI TRONG DATABASE

### 2.1. Bảng MỚI trong schema public (KHÔNG ảnh hưởng KPI)

```sql
-- Bảng 1: Vai trò bổ sung cho nền tảng mới
CREATE TABLE public.platform_role (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ma_role VARCHAR(50) NOT NULL UNIQUE,
    ten_role VARCHAR(100) NOT NULL,
    mo_ta TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng 2: Gán vai trò bổ sung cho CBCC
CREATE TABLE public.cong_chuc_platform_role (
    cong_chuc_id UUID NOT NULL REFERENCES public.cong_chuc(id),
    platform_role_id UUID NOT NULL REFERENCES public.platform_role(id),
    pham_vi JSONB,
    assigned_by UUID REFERENCES public.cong_chuc(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cong_chuc_id, platform_role_id)
);
```

**Tại sao không ảnh hưởng KPI?**
- Không FK nào từ bảng KPI trỏ đến 2 bảng này
- Code KPI không query 2 bảng này
- Bảng `cong_chuc` KHÔNG BỊ SỬA — chỉ có bảng mới FK tới nó

### 2.2. Schema MỚI (nằm ngoài KPI hoàn toàn)

```
kpi_haiquan database:
├── Schema public   ← KPI sống ở đây (GIỮ NGUYÊN)
├── Schema lms      ← Module Đào tạo (MỚI, không liên quan)
├── Schema forum    ← Module Diễn đàn (MỚI, không liên quan)
├── Schema legal    ← Module Pháp luật (MỚI, không liên quan)
├── Schema portal   ← Module Portal (MỚI, không liên quan)
└── Schema common   ← Dùng chung (MỚI, KPI chỉ ĐỌC 1 bảng)
```

Khi query bảng KPI, PostgreSQL vẫn hoạt động bình thường vì search_path mặc định là `public`.

### 2.3. Bảng KPI sẽ ĐỌC (không ghi)

```sql
-- common.kpi_integration_log: Dữ liệu từ module mới
-- KPI Dashboard sẽ ĐỌC bảng này để hiển thị thông tin bổ sung

SELECT * FROM common.kpi_integration_log
WHERE cong_chuc_id = :id AND thang = :thang AND nam = :nam;
```

Bảng này do module LMS/Forum/Legal ghi vào. KPI chỉ đọc để hiển thị trên dashboard.

---

## III. THAY ĐỔI TRONG JWT

### 3.1. JWT payload hiện tại (GIỮ NGUYÊN)

```json
{
  "sub": "uuid-cong-chuc",
  "ma_cc": "20ZZ-0224",
  "vai_tro": "CONG_CHUC",
  "don_vi_id": "uuid-don-vi",
  "is_lanh_dao": false,
  "exp": 1234567890
}
```

### 3.2. JWT payload mới (THÊM field)

```json
{
  "sub": "uuid-cong-chuc",
  "ma_cc": "20ZZ-0224",
  "vai_tro": "CONG_CHUC",
  "don_vi_id": "uuid-don-vi",
  "is_lanh_dao": false,
  "platform_roles": ["GIANG_VIEN"],   // ← CHỈ THÊM FIELD NÀY
  "exp": 1234567890
}
```

**Ảnh hưởng KPI?**
- Code KPI đọc `payload["vai_tro"]` → vẫn hoạt động bình thường
- Field `platform_roles` là field mới, code KPI không đọc nó → không lỗi
- `jwt.decode()` vẫn trả về dict đầy đủ, field mới chỉ bị bỏ qua

### 3.3. Thay đổi cần làm trong KPI backend

**Khi endpoint `/api/v1/auth/login` được cập nhật:**

```python
# TRƯỚC (hiện tại):
payload = {
    "sub": str(user.id),
    "ma_cc": user.ma_cc,
    "vai_tro": user.vai_tro.ma_vai_tro,
    "don_vi_id": str(user.don_vi_id),
    "is_lanh_dao": user.is_lanh_dao,
}

# SAU (thêm platform_roles):
platform_roles = get_platform_roles(user.id)  # Query bảng mới
payload = {
    "sub": str(user.id),
    "ma_cc": user.ma_cc,
    "vai_tro": user.vai_tro.ma_vai_tro,
    "don_vi_id": str(user.don_vi_id),
    "is_lanh_dao": user.is_lanh_dao,
    "platform_roles": platform_roles,  # ← THÊM
}
```

> ⚠️ Việc sửa endpoint login sẽ do **Tech Lead (HUB)** thực hiện, KHÔNG phải Dev KPI. Dev KPI chỉ cần biết để không ngạc nhiên khi JWT thay đổi.

---

## IV. THAY ĐỔI TRONG FRONTEND

### 4.1. Sidebar mở rộng

```
TRƯỚC (hiện tại):           SAU (mở rộng):
┌─────────────────┐         ┌─────────────────┐
│ Dashboard       │         │ 🏠 Tổng quan    │ ← Dashboard mới
│ Kê khai         │         │ ◎ KPI & Thi đua │ ← Nhóm menu KPI
│ Phê duyệt      │         │   Kê khai       │
│ Đánh giá        │         │   Phê duyệt     │
│ Xếp loại       │         │   Đánh giá      │
│ Nghỉ phép      │         │   Xếp loại      │
│ Báo cáo        │         │   Nghỉ phép     │
│ Admin           │         │   Báo cáo       │
└─────────────────┘         │ 📚 Đào tạo      │ ← MỚI
                            │ 💬 Diễn đàn      │ ← MỚI
                            │ 📜 Pháp luật     │ ← MỚI
                            │ 📁 Tài liệu     │ ← MỚI
                            │ 🔔 Thông báo     │ ← MỚI
                            │ ⚙️ Quản trị      │ ← Mở rộng
                            └─────────────────┘
```

**Ảnh hưởng:** File sidebar layout sẽ được sửa. Các page KPI (`/ke-khai`, `/phe-duyet`, v.v.) KHÔNG thay đổi.

### 4.2. Dashboard page

Trang `/dashboard` hiện tại sẽ được **nâng cấp** (không phải thay thế):
- Widget KPI hiện tại → GIỮ NGUYÊN
- Thêm widget LMS, Forum, Legal bên cạnh
- Thêm widget thông báo

**Nếu Dev KPI đang sửa dashboard:** Phối hợp với Dev Portal (Project 5) để tránh conflict.

---

## V. NHỮNG GÌ DEV KPI CẦN LÀM / KHÔNG CẦN LÀM

### ✅ CẦN LÀM (như bình thường)

1. Fix bug KPI production
2. Hoàn thiện `/bao-cao` (báo cáo tổng hợp)
3. Hoàn thiện `/admin/*` (quản lý user, đơn vị, danh mục)
4. Export Excel/PDF
5. UAT với người dùng thực

### ⚠️ CẦN LƯU Ý

1. **Nếu sửa file sidebar/layout** → Kiểm tra với Tech Lead vì file này sẽ được mở rộng
2. **Nếu sửa endpoint `/auth/login`** → Báo Tech Lead vì endpoint này ảnh hưởng tất cả module
3. **Nếu sửa bảng `cong_chuc`** → DỪNG LẠI, hỏi Tech Lead (bảng này là SSO cho toàn nền tảng)
4. **Nếu thêm bảng vào schema public** → Hỏi Tech Lead trước

### ❌ KHÔNG CẦN LÀM

1. Không cần biết chi tiết module LMS/Forum/Legal
2. Không cần đọc/sửa schema lms, forum, legal, portal, common
3. Không cần cài Redis, MinIO
4. Không cần config Nginx (Tech Lead làm)
5. Không cần lo về `kpi_integration_log` (module mới tự ghi)

---

## VI. GIAI ĐOẠN TÍCH HỢP (Phase 5 — Tháng 8-9)

Khi nền tảng mới sẵn sàng, Dev KPI sẽ cần phối hợp:

### 6.1. Thêm widget tham khảo trên Dashboard KPI

Hiển thị dữ liệu từ `common.kpi_integration_log` bên cạnh điểm KPI:

```
┌─ Dashboard CBCC ──────────────────────────────────┐
│                                                    │
│  📊 ĐIỂM KPI THÁNG 3/2026                         │
│  ┌─────────────────────────────────┐               │
│  │ Tiêu chí chung: 27/30          │               │
│  │ KPI: 65/70                      │               │
│  │ TỔNG: 92/100 → Xếp loại: A     │               │
│  └─────────────────────────────────┘               │
│                                                    │
│  📋 THÔNG TIN THAM KHẢO (từ nền tảng)             │
│  ┌─────────────────────────────────┐               │
│  │ 📚 Đào tạo: 3 khóa hoàn thành  │  ← Từ LMS    │
│  │ 💬 Diễn đàn: 5 bài, 12 trả lời │  ← Từ Forum  │
│  │ 📜 Pháp luật: 8/10 VB đã đọc   │  ← Từ Legal  │
│  └─────────────────────────────────┘               │
│                                                    │
│  ⚠️ Dữ liệu tham khảo này KHÔNG ảnh hưởng điểm   │
│     KPI. Lãnh đạo có thể tham chiếu khi phê       │
│     duyệt đánh giá.                               │
└────────────────────────────────────────────────────┘
```

### 6.2. API cần gọi

```
GET /api/v1/common/kpi-log/{cong_chuc_id}?thang=3&nam=2026

Response:
{
  "data": [
    {"module": "LMS", "metrics": {"khoa_hoc_hoan_thanh": 3, ...}},
    {"module": "FORUM", "metrics": {"bai_dang": 5, "tra_loi": 12, ...}},
    {"module": "LEGAL", "metrics": {"vb_da_doc": 8, "vb_chua_doc": 2, ...}}
  ]
}
```

### 6.3. Dashboard lãnh đạo bổ sung

Khi phê duyệt KPI, lãnh đạo sẽ thấy thêm tab "Hoạt động nền tảng" cho từng CBCC:

```
Phê duyệt KPI tháng 3/2026 — Nguyễn Văn A
┌─────────┬──────────────┬───────────────────┐
│ Tab KPI │ Tab Nền tảng │                   │
└─────────┴──────────────┘                   │
│                                             │
│  📚 Đào tạo:                                │
│  • Khóa học hoàn thành: 3                   │
│  • Điểm trung bình: 85.5                   │
│  • Chứng chỉ: 2                            │
│                                             │
│  💬 Diễn đàn:                                │
│  • Bài đăng: 5 (2 được ghim)               │
│  • Trả lời: 12 (1 đáp án chuẩn)            │
│  • Upvote nhận được: 30                     │
│                                             │
│  📜 Pháp luật:                               │
│  • VB đã đọc: 8/10                         │
│  • Quiz pháp luật TB: 90.0                  │
│  • VB quá hạn: 0                            │
└─────────────────────────────────────────────┘
```

> ⚠️ Phần này sẽ được implement ở Phase 5. Dev KPI không cần làm ngay.

---

## VII. LIÊN HỆ KHI CẦN

```
Thay đổi liên quan nền tảng → Liên hệ Tech Lead (HUB project)
Thay đổi sidebar/layout     → Phối hợp Dev Portal (Project 5)
Thay đổi bảng cong_chuc     → DỪNG LẠI → Hỏi Tech Lead
```
