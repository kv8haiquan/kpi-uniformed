# PHÂN TÍCH & GÓP Ý — MODULE HKG (HỌP KHÔNG GIẤY)

**Người phân tích:** Claude (AI hỗ trợ phát triển)
**Ngày:** 30/04/2026
**Tài liệu nguồn:** `/docs/HKG/HKG.pdf`, `KeHoach_Phase4_HKG.docx`, `So sanh diem moi.docx`, `VP phối hợp xây dựng Module.1.docx`
**Đối chiếu:** `CLAUDE.md`, `docs/CHIEN_LUOC_NEN_TANG_THONG_NHAT.md`, codebase hiện tại

---

## 1. Tóm tắt module HKG

| Hạng mục | Nội dung |
|---|---|
| **Tên module** | Hệ thống Họp Không Giấy (HKG — Meeting Paperless System) |
| **Quy mô** | 549 CBCC · 14 đơn vị (Phòng/Đội/HQ Cửa khẩu — không có Tổ) |
| **Khối họp** | Đảng + Chuyên môn + Hành chính + Ban/Nhóm |
| **Hình thức** | Trực tiếp · Họp video trực tuyến · Lấy ý kiến từ xa · Hybrid |
| **Phạm vi chức năng** | 10 module nghiệp vụ + 2 dạng CKS, **17 bảng DB** |
| **Lộ trình** | Phase 1-3: 6 tuần · Phase 4: thêm 4 tuần (page-sync, annotation, PWA, SMS, Zalo) |
| **Stack đề xuất** | FastAPI 0.115 + Next.js 16 + PostgreSQL 15 + Redis + MinIO + Jitsi + WebSocket |
| **Kiến trúc trong spec** | Web app **riêng biệt**, domain `hkg.hqkv8.vn`, schema `meeting`, **không nhúng vào kpi.kv08.vn** |
| **Chi phí phần mềm** | 0đ (open-source). Phát sinh: SMS Brand Name 12-15tr/năm + CKS dịch vụ |

Stack đề xuất **trùng khớp gần như 100%** với codebase hiện tại của Nền tảng Số HQKV8.

---

## 2. Các điểm mạnh của hồ sơ HKG v5.0

1. **Hồ sơ rất chi tiết:** DB schema, luồng nghiệp vụ, phân quyền, lộ trình tuần, tiêu chí nghiệm thu — tất cả đều có sẵn ở mức implementation-ready.
2. **Nguyên tắc MVP rõ ràng:** Phase 1 cốt lõi → Phase 2 nâng cao → Phase 3 hoàn thiện. Phù hợp với 1 dev + AI hỗ trợ.
3. **Stack 100% open-source:** chi phí bản quyền 0đ. Đã chọn Rancher Desktop thay Docker Desktop để né phí >250 user.
4. **Ma trận đáp ứng VP:** đã định lượng 72% (sau Phase 1-3) → 92% (sau Phase 4) với phân tích rủi ro cụ thể.
5. **Phân quyền rõ ràng:** quy tắc "cấp nào xem cấp đó" + đặc cách (Lãnh đạo CC, Chánh VP, Trưởng phòng CNTT) — bám sát thực tế nghiệp vụ.
6. **Họp Đảng dùng chung luồng:** chỉ khác template tiêu đề + chức danh ký. Quyết định kiến trúc đúng đắn, tránh duplicate logic.
7. **CKS hai tầng:** CKS Cá nhân + CKS Công vụ với luồng PAdES, QR xác thực, hash SHA-256. Đáp ứng quy định pháp lý Việt Nam.

---

## 3. Vấn đề & xung đột với codebase hiện tại

### 3.1. Mâu thuẫn kiến trúc (QUAN TRỌNG NHẤT)

Spec HKG nói:

> "Web app RIÊNG BIỆT với domain/subdomain riêng (hkg.hqkv8.vn), cơ sở dữ liệu schema riêng, **không nhúng vào kpi.kv08.vn**"

Nhưng `CLAUDE.md` của project quy định **ngược lại**:

> "Tất cả module MỚI dùng PostgreSQL schema riêng trong **CÙNG database** `kpi_haiquan` ... Cross-schema JOIN hoạt động bình thường, 1 connection pool, FK trực tiếp đến `public.cong_chuc(id)`"

**Cần chốt trước khi code:** theo spec HKG (DB tách rời) hay theo pattern Nền tảng Số (cùng DB, schema `meeting`)?

**Khuyến nghị:** **Theo pattern hiện có** — đặt schema `meeting` (hoặc `hkg`) trong database `kpi_haiquan`, backend port `8004`, frontend dùng chung `frontend/` với route `/hop-khong-giay`.

**Lý do:**
- Tận dụng được SSO (`SECRET_KEY` chung).
- Đã có sẵn 3 bảng platform: `platform_role`, `cong_chuc_platform_role`, `platform_config`.
- Cross-schema JOIN với `public.cong_chuc`, `public.don_vi`, `public.vai_tro` hoạt động ngay.
- Không phải duplicate user table 549 records.
- Bám đúng các bullet "✅ CHỈ THÊM bảng mới vào schema riêng" trong CLAUDE.md.
- Đã có pattern thành công: LMS module đã production với 11 bảng schema `lms.*`.

---

### 3.2. HKG.pdf §4.4 đề xuất sửa `public.cong_chuc` — VI PHẠM RULE TUYỆT ĐỐI

`CLAUDE.md` ghi rõ:

> "⛔ KHÔNG BAO GIỜ sửa/xóa bảng trong schema public (cong_chuc, vai_tro, don_vi, ...)"

Nhưng spec HKG đề xuất thêm 7 cột flag vào `public.cong_chuc`:
`is_lanh_dao_cc`, `is_chanh_vp`, `is_truong_cntt`, `is_lanh_dao_dv`, `is_thu_ky_dv`, `is_dang_vien`, `is_admin`.

**Cách đúng theo pattern hiện có — map sang infrastructure đã sẵn sàng:**

| Spec HKG đề xuất | Cách đúng (không sửa public.cong_chuc) |
|---|---|
| `is_lanh_dao_cc` | Dẫn xuất từ `vai_tro.ma_vai_tro IN ('CCT','PCCT')` |
| `is_lanh_dao_dv` | Dẫn xuất từ `vai_tro.ma_vai_tro IN ('TDV','PDV')` hoặc cột `cong_chuc.is_lanh_dao` đã có |
| `is_admin` | Dẫn xuất từ `vai_tro.ma_vai_tro = 'SUPER_ADMIN'` |
| `is_chanh_vp` | **Platform role mới:** `CHANH_VP` qua `cong_chuc_platform_role` |
| `is_truong_cntt` | **Platform role mới:** `TRUONG_CNTT` |
| `is_thu_ky_dv` | **Platform role mới:** `THU_KY_HOP` |
| `is_dang_vien` | **Platform role mới:** `DANG_VIEN` |
| (cần thêm) | **Platform role mới:** `BI_THU_CHI_BO`, `PHO_BI_THU` |

**Kết quả:**
- Không động chạm `public.cong_chuc`.
- Đúng quy tắc tuyệt đối.
- Vẫn đáp ứng đủ phân quyền nghiệp vụ HKG.
- Tận dụng cơ chế `cong_chuc_platform_role.pham_vi` (JSONB) để lưu phạm vi áp dụng (đơn vị nào, chi bộ nào).

---

### 3.3. Cấu trúc đơn vị — không có cấp "Bộ phận"

`public.don_vi` hiện có enum `LOAI_DON_VI = PHONG | DOI | HAI_QUAN_CUA_KHAU`, **không có cấp "Bộ phận"**.

Spec HKG đề cập "cấp tổ chức: Chi cục → Phòng/Đội/HQ Cửa khẩu → **Bộ phận**".

**Hai phương án:**
- **(a) Bỏ qua cấp Bộ phận trong MVP** — đa số cuộc họp diễn ra ở cấp Phòng/Đội. Phục vụ 90% use case.
- **(b) Tạo bảng `meeting.bo_phan`** riêng cho HKG, FK đến `public.don_vi` — không động đến `public.don_vi`.

**Khuyến nghị:** **(a) cho MVP** — đơn giản hoá, ship nhanh. Mở rộng sang (b) khi có yêu cầu thực tế từ các đơn vị.

---

### 3.4. Phân quyền "Khối Đảng" — cần dữ liệu mới (nằm trong schema riêng)

Spec yêu cầu "Họp Đảng dùng chung luồng, chỉ khác template tiêu đề và chức danh ký". Cần các trường mới (đều trong schema `meeting`, không động public):

- `meeting.cuoc_hop.khoi` ∈ `{DANG, CHUYEN_MON, HANH_CHINH, BAN_NHOM}`.
- Platform roles bổ sung: `BI_THU_CHI_BO`, `PHO_BI_THU`, `DANG_VIEN`, `THU_KY_CHI_BO` để render placeholder `{{chu_tri}}` / `{{thu_ky}}` đúng theo khối họp.
- `meeting.cuoc_hop.chi_bo_id` (NULLABLE) — chỉ điền khi `khoi = DANG`. Có thể tham chiếu một bảng `meeting.chi_bo` riêng hoặc dùng JSONB ghi tên chi bộ.

---

### 3.5. Phase 1 quá tham vọng cho 1 người × 6 tuần

Spec yêu cầu Phase 1 phải có:
- 17 bảng DB
- 10 module nghiệp vụ
- Jitsi Meet self-host + JWT SSO
- WebSocket realtime cho biểu quyết, điểm danh, ý kiến
- Mock CKS với luồng đầy đủ
- Template đôi (Đảng + Chuyên môn) với placeholder thay thế
- Dashboard 3 cấp
- Import/Export Excel + Word + PDF

**Đánh giá:** **Không khả thi nếu muốn giữ chất lượng** với 1 dev + 21 giờ/tuần × 6 tuần = ~126 giờ.

**Đề xuất MVP cắt giảm (4 tuần ≈ 84 giờ):**

✅ **Giữ lại:**
- Module 1 (Quản lý cuộc họp)
- Module 2 (Thông báo/Giấy mời — chỉ email + in-app, bỏ SMS)
- Module 3 (Tài liệu — upload MinIO + xem PDF.js, không phân lớp Mật)
- Module 4 (Điểm danh QR + bấm tay — bỏ tự động Jitsi)
- Module 5 (Xin phép vắng + auto-approve)
- Module 9 (Biên bản editor cơ bản, **không CKS**)
- Module 10 (Kết luận + nhắc hạn cơ bản, dashboard 1 cấp)

❌ **Cắt khỏi MVP, đưa sang Phase tiếp:**
- Module 6 (Jitsi video) — phức tạp hạ tầng
- Module 7 (Lấy ý kiến từ xa nâng cao)
- Module 8 (Biểu quyết WebSocket + Kín có CKS)
- CKS thật (giữ Mock cho UAT)
- Annotation realtime (Phase 4)
- Page-sync (Phase 4)
- PWA Offline (Phase 4)
- Template đôi Đảng/Chuyên môn (chỉ làm 1 template chung trước)
- Dashboard 3 cấp (làm sau khi có dữ liệu thực)

---

### 3.6. Đánh giá độ phức tạp các tính năng Phase 4

| Tính năng | Độ phức tạp thực sự | Ghi chú |
|---|---|---|
| Đồng bộ trình chiếu (page-sync) | **Trung bình** | WebSocket + Redis pub/sub đủ. Reconnect logic là phần khó. Spec ước 1 tuần — hợp lý. |
| Annotation realtime | **Cao** | PDF.js annotation editor là per-user; đồng bộ nhiều client cần custom layer (toạ độ %, conflict resolution). Spec ước 0.5 tuần — **quá tight**, nên 1.5-2 tuần. |
| PWA Offline | **Cao** | Mâu thuẫn với watermark/tài liệu Mật. Cần policy rõ: tài liệu nào được cache offline, retention bao lâu, sync conflict điểm danh. |
| CKS Production (PAdES + USB Token + CACC API) | **Cao** | Cần phần cứng + chứng thư hợp lệ + UAT thật với CA. **Không nên đặt trong cùng phase với phát triển mới.** Tách thành phase riêng sau khi hệ thống ổn định. |
| SMS Brand Name | **Quy trình — chậm** | Đăng ký 5-10 ngày làm việc, phí 12-15tr/năm. **Phải khởi động sớm Phase 1** vì là blocker. Có thể fallback bằng email + thông báo in-app trong khi chờ. |

---

### 3.7. Thiếu sót hoặc chưa làm rõ trong spec

- **Concurrency 549 user trên WebSocket:** chưa có capacity plan. 1 cuộc họp toàn Chi cục có thể có >100 client cùng lúc nhận page-sync, annotation, biểu quyết. Phase 1 nên test load với ≥50 client đồng thời.
- **MinIO bucket sizing:** 17 bảng + tài liệu họp + record video Jitsi → tăng nhanh. Cần policy lifecycle (giữ video 6 tháng? Tự xoá tài liệu họp >3 năm?).
- **Backup chéo schema:** spec nói backup "PostgreSQL + MinIO daily" nhưng chưa rõ chiến lược restore selective khi chỉ schema `meeting` lỗi mà không ảnh hưởng KPI/LMS.
- **Audit log:** KPI có model `audit_log` trong `app/models/audit_log.py` — HKG nên dùng chung hay tạo riêng `meeting.audit_log`? **Khuyến nghị:** dùng chung schema `common.audit_log` (đã có trong CLAUDE.md) để tra cứu cross-module.
- **JWT mở rộng:** trạng thái hiện tại "JWT mở rộng (thêm platform_roles) — Chưa implement". HKG phụ thuộc vào trường này để check `THU_KY_HOP`, `CHANH_VP`, ... → **Phải implement JWT mở rộng trước khi build HKG**.

---

## 4. Đề xuất triển khai

### 4.1. Tuần 0 — Chuẩn bị (3-5 ngày)

1. Tạo file `docs/HKG/SPEC_ADAPTED.md` chốt:
   - Schema `meeting`, port 8004, route `/hop-khong-giay`.
   - Danh sách platform roles cần seed: `CHANH_VP`, `TRUONG_CNTT`, `THU_KY_HOP`, `DANG_VIEN`, `BI_THU_CHI_BO`, `PHO_BI_THU`.
   - Bảng ánh xạ HKG.pdf §4.4 → vai_tro + platform_role hiện có.
2. Implement **JWT mở rộng** thêm `platform_roles[]` (từ `cong_chuc_platform_role`).
3. Quyết định subdomain: `hkg.kv08.vn` (subdomain KPI) vs `hkg.hqkv8.vn` (theo spec).
4. Bắt đầu thủ tục đăng ký SMS Brand Name (blocker dài hạn).

### 4.2. Tuần 1-2 — DB + API skeleton

- Migration tạo schema `meeting` + 8-10 bảng cốt lõi:
  - `cuoc_hop`, `thanh_phan`, `tai_lieu`, `diem_danh`, `xin_phep_vang`, `y_kien`, `bien_ban`, `ket_luan`, `tien_do`, `mau_bieu`.
- Seed platform roles HKG.
- CRUD endpoints `/api/v1/hop-khong-giay/*`.
- Reuse JWT/Auth của KPI thông qua shared module.
- Swagger UI test xong các API cốt lõi.

### 4.3. Tuần 3-4 — Frontend MVP

- Scaffold `frontend/src/app/(main)/hop-khong-giay/`:
  - `lich-hop/` — calendar view tháng/tuần/ngày.
  - `tao-hop/` — form tạo cuộc họp.
  - `chi-tiet/[id]/` — view chi tiết + PDF viewer + danh sách thành phần.
  - `diem-danh/[id]/` — QR điểm danh + danh sách bấm tay.
  - `xin-phep-vang/` — gửi đơn + duyệt.
- Sidebar entry mới "Họp Không Giấy".
- Permission guard theo platform role.

### 4.4. Tuần 5-6 — Biên bản + UAT

- Module 9 (Biên bản): editor TipTap (đã có trong codebase), auto-fill thành phần/điểm danh/ý kiến, xuất DOCX/PDF (mock CKS — chỉ watermark + QR, chưa nhúng PAdES thật).
- Module 8 cơ bản: biểu quyết công khai (không kín, không CKS) qua WebSocket.
- UAT 10-20 CBCC với 2-3 cuộc họp thử thực tế.
- Deploy staging trên Ubuntu Server.

### 4.5. Phase nâng cao (sau khi MVP ổn)

Mỗi phase 2-3 tuần, **không gộp**:

| Phase | Nội dung | Thời gian |
|---|---|---|
| Phase 2 | Jitsi Meet + JWT SSO + auto-attendance | 2 tuần |
| Phase 3 | Page-sync (đồng bộ trình chiếu) | 1.5 tuần |
| Phase 4 | Annotation realtime | 2 tuần |
| Phase 5 | PWA Offline (chỉ tài liệu Công khai) | 2 tuần |
| Phase 6 | CKS Sandbox → CKS Production | 3 tuần |
| Phase 7 | SMS Brand Name + Zalo OA | 1.5 tuần |
| Phase 8 | Template đôi Đảng/Chuyên môn + Dashboard 3 cấp | 2 tuần |
| Phase 9 | Import/Export Excel + Word đầy đủ | 1.5 tuần |

**Tổng:** ~16 tuần sau MVP. Realistic hơn nhiều so với "10 tuần làm tất cả" của spec gốc.

---

## 5. Câu hỏi cần chốt trước khi code

1. **Triển khai chung DB hay tách riêng?**
   - Khuyến nghị: schema `meeting` trong `kpi_haiquan`.
   - **Cần quyết định.**

2. **Khoanh vùng MVP:** đồng ý cắt Jitsi / page-sync / annotation / PWA / CKS-thật ra khỏi Phase 1 không?

3. **Quyết định "Bộ phận":** bỏ qua trong MVP hay làm bảng `meeting.bo_phan` riêng?

4. **Subdomain:** dùng `hkg.kv08.vn` (subdomain của KPI hiện có) hay `hkg.hqkv8.vn` (như spec)? Ảnh hưởng cấu hình Nginx.

5. **SMS Brand Name (Phase 4):** có sẵn budget/quy trình duyệt không? Nếu chưa, nên bỏ ra khỏi MVP và dùng email + thông báo in-app trước.

6. **Audit log:** dùng chung `common.audit_log` hay tạo riêng `meeting.audit_log`?

7. **Tài khoản UAT:** có dùng tài khoản KPI thật (549 CBCC) hay tạo môi trường staging riêng với data mock?

---

## 6. Kết luận

Hồ sơ HKG v5.0 **chất lượng tốt, đầy đủ về nghiệp vụ**, nhưng cần **2 điều chỉnh kiến trúc bắt buộc** để tích hợp với Nền tảng Số HQKV8:

1. **Đặt vào schema `meeting` trong DB chung `kpi_haiquan`**, không tách database riêng.
2. **Không sửa `public.cong_chuc`** — dùng `cong_chuc_platform_role` cho các flag mới.

Đồng thời cần **cắt giảm phạm vi MVP** xuống còn 6-7 module cốt lõi trong 4 tuần, đẩy 4-5 tính năng phức tạp (Jitsi, page-sync, annotation, PWA, CKS thật, SMS) sang các phase sau.

Khi anh chốt được 7 câu hỏi ở mục 5, tôi sẽ tạo plan implementation chi tiết và bắt đầu scaffold.

---

*Tài liệu phân tích — phục vụ thảo luận nội bộ Phòng CNTT.*
