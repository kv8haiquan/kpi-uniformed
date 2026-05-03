# HKG_SPEC_ADAPTED.md — Module Họp Không Giấy

**Phiên bản:** 1.0 (Adapted) · **Ngày:** 30/04/2026
**Đơn vị:** Phòng CNTT — Chi cục HQKV8

> Tài liệu này **chốt lại** scope và kiến trúc của HKG sau khi điều chỉnh theo Nền tảng Số HQKV8. **Đây là tài liệu authoritative** — khi có xung đột giữa HKG.pdf v5.0 và file này, **lấy file này làm chuẩn**.

---

## 1. NGUYÊN TẮC TUYỆT ĐỐI

### 1.1. HKG là MODULE TÍCH HỢP, không phải app độc lập

| Hạng mục | Quyết định |
|---|---|
| Database | Schema `meeting` trong DB **`kpi_haiquan`** (chung với KPI, LMS) |
| Backend | FastAPI service mới, port **8006**, folder `backend/meeting_service/` |
| Frontend | **Tích hợp thẳng vào portal nền tảng** — chung Next.js app, route `/hop-khong-giay` |
| Domain | **KHÔNG dùng subdomain riêng** — dùng chung domain của portal (vd: `kv08.vn/hop-khong-giay`) |
| SSO | Dùng chung JWT + `SECRET_KEY` của nền tảng |
| Sidebar | Bổ sung entry "Họp Không Giấy" vào sidebar chung của portal |
| Notification | Dùng chung bell icon + bảng `common.thong_bao` (loại `MEETING`) |
| Audit log | Dùng chung **`common.audit_log`**, `module = 'MEETING'` |

### 1.2. Bốn ràng buộc kiến trúc KHÔNG ĐƯỢC vi phạm

```
1. ⛔ KHÔNG sửa schema bảng public.* (cong_chuc, don_vi, vai_tro, ...)
   → CHỈ được INSERT vào public.platform_role + public.cong_chuc_platform_role.
2. ⛔ KHÔNG tạo FK từ schema meeting sang schema khác,
   TRỪ public.cong_chuc(id), public.don_vi(id), public.platform_role(id)
3. ⛔ KHÔNG tạo bảng user/auth riêng — dùng chung public.cong_chuc
4. ⛔ KHÔNG tạo audit_log riêng cho HKG. Dùng common.audit_log.
   Nếu common.audit_log CHƯA tồn tại (verify P0 — 2026-04-30 confirmed CHƯA):
   tạo migration platform-level (trong common_service) TRƯỚC khi vào G1.
   Đây là trách nhiệm nền tảng, KHÔNG phải scope HKG.
   Schema gợi ý xem Phụ lục A của HKG_DATABASE_DESIGN.md.
```

### 1.3. Pattern phải tuân theo (đã thành công với LMS)

```
✅ ĐƯỢC PHÉP:
- Tạo schema meeting trong DB kpi_haiquan
- Thêm bảng MỚI vào schema public: chỉ platform_role + cong_chuc_platform_role
- Cross-schema FK đến public.cong_chuc, public.don_vi
- Reuse JWT/auth dependency từ shared module
- Reuse upload-to-MinIO util từ KPI/LMS
```

---

## 2. PHẠM VI MVP (4-6 TUẦN)

### 2.1. CÓ trong MVP — 7 module cốt lõi

| # | Module | Phạm vi MVP |
|---|---|---|
| 1 | Quản lý cuộc họp | Tạo/sửa/hủy cuộc họp, lịch tháng/tuần/ngày, lọc theo đơn vị |
| 2 | Thông báo & giấy mời | Email + thông báo in-app (KHÔNG SMS, KHÔNG Zalo) |
| 3 | Tài liệu họp | Upload PDF/Word/PPT/Excel lên MinIO, xem PDF.js, phân quyền 2 cấp (Công khai/Hạn chế — KHÔNG có cấp Mật) |
| 4 | Điểm danh | QR code + bấm tay (KHÔNG tự động qua Jitsi) |
| 5 | Xin phép vắng | CBCC gửi đơn → Chủ tọa duyệt → auto-approve sau timeout |
| 9 | Biên bản | Editor TipTap, auto-fill thành phần/điểm danh/ý kiến, xuất DOCX/PDF với **Mock CKS** (watermark + QR, chưa nhúng PAdES thật) |
| 10 | Kết luận & nhắc hạn | Giao việc, hạn hoàn thành, tiến độ %, nhắc 3 ngày trước hạn, dashboard 1 cấp |

### 2.2. CẮT khỏi MVP — đẩy sang phase sau

| Tính năng | Lý do cắt | Đẩy sang |
|---|---|---|
| Module 6: Jitsi video | Phức tạp hạ tầng, không phải nghiệp vụ cốt lõi | Phase 2 |
| Module 7: Lấy ý kiến từ xa | Nâng cao | Phase 2 |
| Module 8: Biểu quyết WebSocket realtime + biểu quyết kín | Phức tạp realtime + crypto | Phase 3 |
| Page-sync (đồng bộ trình chiếu) | Tính năng nâng cao | Phase 4 (đã có kế hoạch) |
| Annotation realtime | Tính năng nâng cao | Phase 4 |
| PWA Offline | Phức tạp + xung đột với tài liệu Mật | Phase 5 |
| CKS Production thật (PAdES + USB Token + CACC API) | Phụ thuộc phần cứng + chứng thư + UAT với CA | Phase 6 |
| SMS Brand Name | Có ngân sách nhưng cắt khỏi MVP | Phase 7 |
| Template đôi Đảng/Chuyên môn | Làm 1 template chung trước | Phase 8 |
| Dashboard 3 cấp | Sau khi có dữ liệu thực | Phase 8 |
| Import/Export Excel + Word đầy đủ | Sau MVP | Phase 9 |

### 2.3. Cấu trúc đơn vị

- **MVP**: chỉ làm tới cấp **Phòng / Đội / HQ Cửa khẩu** (14 đơn vị có sẵn trong `public.don_vi`)
- **KHÔNG làm cấp "Bộ phận"** trong MVP. Khi có yêu cầu thực tế → tạo bảng `meeting.bo_phan` riêng (không động `public.don_vi`)

### 2.4. Khối họp

- **MVP**: tất cả khối họp (Đảng + Chuyên môn + Hành chính + Ban/Nhóm) **dùng chung 1 template biên bản**
- Template Đảng riêng → đẩy sang Phase 8
- Cột `meeting.cuoc_hop.khoi` vẫn được tạo từ đầu (giá trị `DANG | CHUYEN_MON | HANH_CHINH | BAN_NHOM`) để chuẩn bị cho phase sau

---

## 3. KIẾN TRÚC TÍCH HỢP CHI TIẾT

### 3.1. Sơ đồ tích hợp

```
                      ┌──────────────────────────────┐
                      │   Portal Next.js (port 3000) │
                      │   Domain: kv08.vn (chung)    │
                      ├──────────────────────────────┤
                      │ Sidebar:                     │
                      │  - KPI                       │
                      │  - Đào tạo (LMS)             │
                      │  - Diễn đàn                  │
                      │  - Pháp luật                 │
                      │  - 🆕 Họp Không Giấy         │
                      │  - Thông báo                 │
                      └──────┬───────────────────────┘
                             │ JWT (1 lần đăng nhập)
              ┌──────────────┼──────────────────────┐
              ▼              ▼                      ▼
     ┌────────────┐  ┌────────────┐         ┌─────────────┐
     │  KPI API   │  │  LMS API   │   ...   │  HKG API    │
     │  port 8000 │  │  port 8001 │         │  port 8006  │
     └─────┬──────┘  └─────┬──────┘         └──────┬──────┘
           │               │                       │
           └───────────────┼───────────────────────┘
                           ▼
                ┌──────────────────────┐
                │  PostgreSQL          │
                │  DB: kpi_haiquan     │
                ├──────────────────────┤
                │ Schema: public       │ ← cong_chuc, don_vi, vai_tro,
                │                      │   platform_role, cong_chuc_platform_role
                │ Schema: common       │ ← thong_bao, audit_log
                │ Schema: kpi          │
                │ Schema: lms          │
                │ Schema: meeting      │ ← 🆕 HKG (10 bảng MVP)
                └──────────────────────┘
```

### 3.2. Frontend tích hợp portal

**Routes mới được thêm vào Next.js app chung:**

```
frontend/src/app/(main)/
├── kpi/                  ← đã có
├── dao-tao/              ← đã có (LMS)
├── dien-dan/             ← đã có (Forum)
├── phap-luat/            ← đã có (Legal)
└── hop-khong-giay/       ← 🆕 HKG MVP
    ├── page.tsx                    # Lịch họp tháng/tuần/ngày
    ├── tao-hop/page.tsx            # Form tạo cuộc họp
    ├── chi-tiet/[id]/
    │   ├── page.tsx                # Tổng quan cuộc họp
    │   ├── tai-lieu/page.tsx       # Quản lý tài liệu
    │   ├── diem-danh/page.tsx      # Điểm danh QR + bấm tay
    │   ├── bien-ban/page.tsx       # Editor biên bản
    │   └── ket-luan/page.tsx       # Giao việc + tiến độ
    ├── xin-phep-vang/page.tsx      # Đơn xin vắng
    └── thong-ke/page.tsx           # Thống kê cá nhân/đơn vị
```

**Reuse từ portal:**
- Layout chung (sidebar, header, breadcrumb)
- Auth context (JWT, current user)
- Notification component (bell icon)
- Toast/Alert component
- Form components (shadcn/ui đã sẵn)
- API client với JWT auto-attach

### 3.3. Backend service

```
backend/meeting_service/         ← 🆕 port 8006
├── main.py                      # FastAPI app entry
├── config.py                    # Đọc DB_URL, MINIO, REDIS từ .env chung
├── dependencies.py              # Reuse JWT decode từ shared
├── models/
│   ├── __init__.py
│   ├── cuoc_hop.py
│   ├── thanh_phan.py
│   ├── tai_lieu.py
│   ├── diem_danh.py
│   ├── xin_phep_vang.py
│   ├── y_kien.py
│   ├── bien_ban.py
│   ├── ket_luan.py
│   └── tien_do.py
├── schemas/
│   ├── cuoc_hop.py
│   └── ...
├── api/
│   ├── endpoints/                # External — frontend gọi
│   │   ├── cuoc_hop.py
│   │   ├── tai_lieu.py
│   │   └── ...
│   └── internal/                 # Internal — module khác gọi
│       └── meeting_summary.py    # vd: KPI cần biết CBCC tham dự bao nhiêu họp
└── services/
    ├── audit_log_service.py     # Wrapper ghi vào common.audit_log
    ├── notification_service.py  # Wrapper ghi vào common.thong_bao
    └── minio_service.py         # Reuse pattern từ KPI/LMS
```

**Pattern reference (verify P0):**
- Backend service skeleton: bám `backend/lms_service/` (đã production).
- Test framework: pytest, fixtures `backend/lms_service/tests/conftest.py`.
- Frontend package manager: **npm** (verify từ `frontend/package-lock.json`). Build command: `npm run build`.

### 3.4. Kết nối Portal — đầu mục cụ thể

| Connector | Cách thực hiện |
|---|---|
| **SSO** | Reuse `verify_jwt` dependency từ shared. JWT phải chứa `platform_roles[]` |
| **Sidebar entry** | Sửa file layout chung của portal, thêm 1 menu item |
| **Notification bell** | Backend HKG ghi vào `common.thong_bao` với `module='MEETING'` — bell icon portal tự đọc |
| **User avatar dropdown** | Không sửa — dùng nguyên |
| **Dashboard portal** | Optional: thêm widget "Họp sắp diễn ra" gọi internal API HKG |
| **Permission guard** | Component `<RequireRole role="THU_KY_HOP">` reuse từ portal |

---

## 4. PHÂN QUYỀN

### 4.1. Cấu trúc 2 lớp (theo INTEGRATION_RULES.md)

```
Lớp 1: vai_tro KPI (đã có sẵn)
  SUPER_ADMIN > CHI_CUC_TRUONG > PHO_CHI_CUC_TRUONG >
  TRUONG_DON_VI > PHO_DON_VI > CONG_CHUC > TCCB

Lớp 2: platform_roles HKG
  - 6 role STATIC cần seed:
    THU_KY_HOP, CHANH_VP, TRUONG_CNTT,
    DANG_VIEN, BI_THU_CHI_BO, PHO_BI_THU
  - 1 role DYNAMIC (KHÔNG seed):
    CHU_TOA_HOP — suy ra từ meeting.cuoc_hop.chu_toa_id mỗi cuộc họp
```

Chi tiết các platform_role + ánh xạ → xem **HKG_PLATFORM_ROLES.md**.

### 4.2. Quy tắc phân quyền HKG

| Phạm vi xem | Đối tượng | Cơ sở |
|---|---|---|
| Cá nhân | CBCC thường (chỉ xem cuộc họp được mời) | Default |
| Đơn vị mình | Lãnh đạo đơn vị (`is_lanh_dao=TRUE` của KPI) | Auto |
| Đơn vị mình | Thư ký Phòng/Đội (`THU_KY_HOP`) | Platform role |
| Toàn Chi cục | Chi cục trưởng / Phó CCT | `vai_tro IN (CCT, PCCT)` |
| Toàn Chi cục | Chánh VP | Platform role `CHANH_VP` |
| Toàn Chi cục | Trưởng phòng CNTT | Platform role `TRUONG_CNTT` |
| Toàn quyền | Admin hệ thống | `vai_tro = SUPER_ADMIN` |

**Quan trọng:** Thư ký Phòng/Đội **CHỈ xem dữ liệu đơn vị mình** — không xem thống kê đơn vị khác. (Đây là yêu cầu nghiệp vụ rõ ràng từ HKG.pdf v5.0).

---

## 5. STAGING & UAT

### 5.1. Môi trường

- **Staging**: máy chủ riêng / namespace riêng, KHÔNG dùng DB production
- **Tài khoản UAT**: tạo 20-30 tài khoản mock với email `*.uat@kv08.vn`
- **Sau UAT**: chạy script xoá toàn bộ data có flag `is_uat=TRUE` hoặc email pattern UAT trước khi go-live

### 5.2. Tiêu chí nghiệm thu MVP

| # | Tiêu chí | Cách đo |
|---|---|---|
| 1 | CBCC đăng nhập từ portal → vào `/hop-khong-giay` không cần đăng nhập lại | Test 5 user |
| 2 | Tạo 1 cuộc họp, gửi giấy mời, 5 CBCC nhận thông báo | Manual test |
| 3 | Upload tài liệu PDF, đại biểu xem được trên trình duyệt | Test 3 file |
| 4 | Điểm danh QR: CBCC quét → ghi nhận trong DB | Test 5 lần |
| 5 | Thư ký ghi biên bản → xuất DOCX có watermark + QR | Test 3 biên bản |
| 6 | Phân quyền: Thư ký Phòng A KHÔNG xem được họp Phòng B | Test |
| 7 | Audit log ghi đầy đủ vào `common.audit_log` với `module='MEETING'` | Query DB |
| 8 | Xoá hết mock data sau UAT | Verify DB |

---

## 6. RÀNG BUỘC LIÊN PHASE

### 6.1. Phụ thuộc của HKG (cần sẵn sàng TRƯỚC khi build HKG)

| Phụ thuộc | Trạng thái | Ai làm |
|---|---|---|
| JWT mở rộng có `platform_roles[]` | ✅ Đã có sẵn (auth.py block 'MO RONG PLATFORM') | - |
| Bảng `public.platform_role` + `public.cong_chuc_platform_role` | ⏳ Cần check (đã có hay chưa) | Phòng CNTT |
| Bảng `common.audit_log` + `common.thong_bao` | ⏳ Cần check | Phòng CNTT |
| MinIO bucket `meeting` | ⏳ Cần tạo | Phòng CNTT |

**Nếu các phụ thuộc trên chưa có** → phải làm xong **Tuần 0** trước khi vào Tuần 1 của HKG.

### 6.2. Cam kết không phá vỡ KPI/LMS

Trước mỗi lần deploy HKG:
- ✅ Smoke test KPI: đăng nhập, tạo đánh giá KPI, xem báo cáo
- ✅ Smoke test LMS: đăng nhập, vào khóa học, làm bài
- ✅ Smoke test Portal: sidebar đầy đủ, notification, search

---

## 7. CÂU HỎI ĐÃ CHỐT

| # | Câu hỏi | Quyết định |
|---|---|---|
| 1 | DB chung hay tách | ✅ Schema `meeting` trong `kpi_haiquan` |
| 2 | Cắt khỏi MVP | ✅ Cắt Jitsi/page-sync/annotation/PWA/CKS thật/SMS |
| 3 | Cấp Bộ phận | ✅ Bỏ qua MVP, mở rộng sau |
| 4 | Subdomain | ✅ KHÔNG subdomain, tích hợp vào portal chung |
| 5 | SMS Brand Name | ✅ Có ngân sách nhưng cắt khỏi MVP |
| 6 | Audit log | ✅ Dùng chung `common.audit_log` |
| 7 | UAT | ✅ Staging riêng, xoá sạch mock sau test |

---

*Tài liệu này là input bắt buộc cho mọi prompt phát triển HKG. Khi có thay đổi kiến trúc, cập nhật file này TRƯỚC, rồi mới prompt code.*
