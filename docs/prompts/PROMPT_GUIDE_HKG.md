# PROMPT v1.2: Scaffold Module HKG MVP — Nền tảng Số HQKV8

> **Cách dùng:** Đặt file này + `HKG_SPEC_FIX_CHECKLIST.md` + `HKG_PREFLIGHT_RESULTS.md` (template trống) + 5 file `HKG_*.md` ở `docs/HKG/` của repo. Trong Claude Code CLI:
> `claude "Đọc HKG_CLAUDE_CODE_PROMPT.md, làm Pre-flight, sửa spec theo checklist, sinh changelog, dừng chờ user duyệt."`
>
> **Workflow tổng quan:**
> ```
> P0. Pre-flight (đọc codebase) → điền PREFLIGHT_RESULTS
> P1. Spec Correction (sửa spec gốc theo SPEC_FIX_CHECKLIST) → sinh SPEC_CHANGELOG
>     ──── DỪNG, user review + re-upload spec lên project knowledge ────
> G0. Platform-level prerequisites (audit_log, thong_bao MEETING, JWT)
> G1. DB foundation HKG (schema meeting + 10 bảng + 6 platform_role)
> G2. Backend skeleton + Module 1
> G3. Module 3, 4, 5, 9, 10
> G4. Frontend skeleton
> ```
>
> **Đổi so v1.1:** Bỏ ERRATA layer. CLI sửa thẳng spec gốc → single source of truth.

---

## 1. TÀI LIỆU AUTHORITATIVE — đọc theo thứ tự

| # | File | Vai trò |
|---|---|---|
| 1 | `CLAUDE.md` (root repo) | Quy tắc nền tảng tổng thể |
| 2 | `docs/HKG/HKG_SPEC_FIX_CHECKLIST.md` | **Danh sách sửa CLI phải apply vào spec gốc trước G0** |
| 3 | `docs/HKG/HKG_SPEC_ADAPTED.md` | Scope + kiến trúc HKG đã chốt |
| 4 | `docs/HKG/HKG_DATABASE_DESIGN.md` | Chi tiết 10 bảng schema `meeting` |
| 5 | `docs/HKG/HKG_API_SPECS.md` | Endpoints `/api/v1/hop-khong-giay/*` |
| 6 | `docs/HKG/HKG_PLATFORM_ROLES.md` | Logic phân quyền 2 lớp |
| 7 | `backend/lms_service/` (toàn folder) | **Tham chiếu pattern đã production** — bám sát |

---

## 2. BỐN RÀNG BUỘC KIẾN TRÚC — VI PHẠM = STOP

```
1. ⛔ KHÔNG sửa schema public.* (cong_chuc, don_vi, vai_tro)
   → CHỈ được INSERT vào public.platform_role + public.cong_chuc_platform_role.
2. ⛔ FK cross-schema CHỈ tới public.cong_chuc(id), public.don_vi(id), public.platform_role(id).
3. ⛔ KHÔNG tạo bảng auth/user riêng — dùng public.cong_chuc qua JWT.
4. ⛔ KHÔNG tạo audit_log riêng cho HKG. Dùng common.audit_log.
   Nếu chưa tồn tại: tạo migration platform-level (common_service) trước G1.
```

Phát hiện yêu cầu/quyết định bất kỳ động vào 4 điểm trên → **DỪNG, báo cáo, chờ user duyệt**.

---

## 3. PHASE P0 — PRE-FLIGHT CHECKS

CLI điền kết quả vào `docs/HKG/HKG_PREFLIGHT_RESULTS.md`. **Không qua P1 nếu P0 chưa hoàn tất.**

### 3.1. Môi trường

```
[ ] Folder backend/meeting_service/ chưa tồn tại
[ ] Schema "meeting" chưa tồn tại trong DB kpi_haiquan
[ ] Route frontend/src/app/(main)/hop-khong-giay/ chưa tồn tại
[ ] Port 8004 chưa bị chiếm trong docker-compose / .env
```

### 3.2. Codebase reconnaissance — đọc file THẬT, KHÔNG đoán

```
[ ] Đọc backend/alembic/versions/add_platform_tables_*.py
    → Xác nhận tên cột public.platform_role thật
    → Khớp với SPEC_FIX_CHECKLIST FIX-1 không?
[ ] Đọc backend/common_service/models/thong_bao.py (path verify)
    → Tên cột phân biệt module + người nhận?
    → CHECK constraint giới hạn loại?
    → Có loại MEETING chưa?
[ ] Tìm common.audit_log: SELECT to_regclass('common.audit_log')
    → NULL = chưa có → cần migration platform-level ở G0
[ ] Đọc 1 endpoint LMS bất kỳ
    → Xác định path shared module + tên function verify_jwt/get_current_user
[ ] Đọc 1 service upload của LMS
    → Path file để G2/G3 reuse pattern MinIO
[ ] Đọc backend/alembic/env.py
    → include_schemas=True? target_metadata gộp các schema?
[ ] Đọc package.json + lock file frontend
    → Xác nhận npm hay pnpm
```

### 3.3. JWT mở rộng — blocker G2

```
[ ] Đọc backend/app/core/security.py (path verify)
    → JWT có chứa platform_roles[] chưa?
    → Nếu CHƯA: liệt kê file cần sửa, ước lượng effort
```

### 3.4. Platform roles HKG đã có chưa

```
[ ] SELECT ma_role FROM public.platform_role WHERE quyen_han->>'module' = 'MEETING'
    → Cần seed: THU_KY_HOP, CHANH_VP, TRUONG_CNTT, DANG_VIEN, BI_THU_CHI_BO, PHO_BI_THU
    → CHU_TOA_HOP KHÔNG seed (dynamic theo cuoc_hop.chu_toa_id)
```

### 3.5. Test pattern reference

```
[ ] Liệt kê 3 file điển hình từ backend/lms_service/tests/
```

**Pre-flight hoàn tất → chuyển P1.**

---

## 4. PHASE P1 — SPEC CORRECTION (sửa spec gốc)

> **Đây là phase CLI sửa các file `.md` trong `docs/HKG/`. KHÔNG sinh code Python/TS ở phase này.**

### 4.1. Quy tắc

- Đọc `HKG_SPEC_FIX_CHECKLIST.md` đầy đủ.
- Với mỗi FIX (1 → 7), verify lại trong codebase thật. Nếu codebase khác checklist → DỪNG, hỏi user.
- Apply sửa vào spec gốc bằng tool edit (không tự viết lại file).
- KHÔNG sửa `PHAN_TICH_VA_GOP_Y_HKG.md` (doc lịch sử).
- Mỗi sửa ghi vào `docs/HKG/SPEC_CHANGELOG.md` với format old → new.

### 4.2. Output P1

Sau khi sửa xong:

1. Files modified: `HKG_PLATFORM_ROLES.md`, `HKG_DATABASE_DESIGN.md`, `HKG_SPEC_ADAPTED.md`, `HKG_API_SPECS.md` (file nào không cần sửa thì bỏ qua).
2. File mới: `docs/HKG/SPEC_CHANGELOG.md`.
3. Hiển thị cho user message dạng:
   ```
   ✅ P0 Pre-flight: OK (xem HKG_PREFLIGHT_RESULTS.md)
   ✅ P1 Spec correction: đã sửa N file, M thay đổi (xem SPEC_CHANGELOG.md)

   📋 Action cần user thực hiện:
   1. Review SPEC_CHANGELOG.md
   2. Tải về 4 file spec đã sửa: HKG_PLATFORM_ROLES.md, HKG_DATABASE_DESIGN.md,
      HKG_SPEC_ADAPTED.md, HKG_API_SPECS.md
   3. Re-upload lên Claude.ai project knowledge (thay file cũ)
   4. Reply "Approve G0" để tôi tiếp tục platform prerequisites
   ```

### 4.3. **DỪNG SAU P1.** KHÔNG tự đi tiếp G0.

---

## 5. PHẠM VI MVP

### CÓ trong scaffold

| Module | Nội dung |
|---|---|
| 1. Quản lý cuộc họp | CRUD, lịch tháng/tuần/ngày, lọc đơn vị, gửi giấy mời, xác nhận tham dự, hủy |
| 2. Thông báo | Email + in-app — ghi `common.thong_bao` (tên cột verify từ Pre-flight) |
| 3. Tài liệu | Upload MinIO, xem PDF.js, phân quyền 2 cấp (CONG_KHAI/HAN_CHE) |
| 4. Điểm danh | QR + bấm tay |
| 5. Xin phép vắng | Đơn → duyệt → auto-approve sau timeout (Celery) |
| 9. Biên bản | TipTap editor, auto-fill, xuất DOCX/PDF, **Mock CKS** = SHA-256 + QR + watermark |
| 10. Kết luận | Giao việc, tiến độ %, nhắc 3 ngày trước hạn (Celery), dashboard 1 cấp |

### KHÔNG làm

Jitsi · page-sync · annotation realtime · PWA Offline · CKS Production thật · SMS · Zalo OA · template đôi Đảng/Chuyên môn · dashboard 3 cấp · Import/Export đầy đủ · cấp "Bộ phận".

---

## 6. PHASE G0 — Platform-level prerequisites

> Chỉ vào G0 sau khi user "Approve G0". Pre-flight chỉ ra item nào thiếu thì làm item đó, bỏ qua nếu đã có.

- [ ] Migration `common.audit_log` (nếu Pre-flight 3.2 báo NULL) — đặt trong common_service, schema theo Phụ lục A của `HKG_DATABASE_DESIGN.md`
- [ ] Migration mở rộng `common.thong_bao` thêm loại `MEETING` (nếu Pre-flight 3.2 báo có CHECK constraint thiếu) — common_service
- [ ] Mở rộng JWT claim `platform_roles[]` — sửa file đã verify ở Pre-flight 3.3
- [ ] Test verify: login user có gán platform_role → JWT decode ra `platform_roles: [...]` đúng
- [ ] Báo cáo G0 theo template §9 → chờ user "Approve G1"

---

## 7. PHASE G1-G4 — HKG implementation

### G1 — DB foundation HKG

- [ ] Migration `00X_create_meeting_schema.py`: `CREATE SCHEMA meeting` + 10 bảng
- [ ] Seed 6 platform_role HKG (đã sửa SQL trong spec ở P1)
- [ ] Smoke verify: 10 bảng, 6 role, migration head clean

### G2 — Backend skeleton + Module 1

- [ ] `backend/meeting_service/` đúng cấu trúc, bám pattern `backend/lms_service/`
- [ ] `main.py` port 8004, `/health` 200
- [ ] SQLAlchemy models 10 bảng (Module 1 đầy đủ)
- [ ] Reuse JWT/auth dependency từ shared module (path đã verify)
- [ ] Reuse MinIO util từ pattern LMS
- [ ] Implement đầy đủ Module 1 endpoints theo `HKG_API_SPECS.md §4`
- [ ] Mọi mutation → `common.audit_log` (`module='MEETING'`)
- [ ] Mọi notification → `common.thong_bao` (tên cột thật từ Pre-flight)
- [ ] Swagger UI tại `:8004/docs` đầy đủ description tiếng Việt
- [ ] Test pytest bám pattern `backend/lms_service/tests/`

### G3 — Module 3, 4, 5, 9, 10 backend

Theo thứ tự, mỗi module testable:
1. Module 3 — upload **filesystem** (uploads/meeting/...), JWT short-lived URL, phân quyền tải/in
2. Module 4 — QR sinh + verify, bấm tay
3. Module 5 — xin phép + **APScheduler** auto-approve (KHÔNG dùng Celery)
4. Module 9 — biên bản TipTap, Mock CKS, xuất DOCX (`python-docx`) + PDF (`weasyprint`)
5. Module 10 — kết luận, tiến độ, **APScheduler** nhắc 3 ngày, thống kê 1 cấp

> **Infra deviation từ spec gốc (quyết định 01/05/2026):**
> - **Storage:** filesystem `uploads/meeting/` thay MinIO (LMS pattern, đã production).
> - **Scheduler:** APScheduler in-process (start trong FastAPI lifespan) thay Celery+Redis.
>   Single-server deployment OK; multi-server cần migrate sang Celery+Redis.
> - DB schema cột `minio_bucket/minio_key` GIỮ NGUYÊN — chỉ nội dung là local path.

### G4 — Frontend skeleton

- [ ] `frontend/src/app/(main)/hop-khong-giay/` đúng cấu trúc
- [ ] Reuse layout, auth context, API client, shadcn/ui, TipTap
- [ ] Sidebar entry "Họp Không Giấy"
- [ ] Pages: lịch họp, tạo/sửa, chi tiết (tab tài liệu/điểm danh/biên bản/kết luận), xin phép vắng, thống kê
- [ ] Permission guard `<RequireRole>` reuse từ portal
- [ ] `npm run build` pass (hoặc `pnpm` nếu Pre-flight xác định)

---

## 8. QUY ƯỚC BẮT BUỘC

- PK: `UUID DEFAULT gen_random_uuid()`
- Soft delete: `is_deleted BOOLEAN DEFAULT FALSE`
- Audit cols: `created_at`, `updated_at`, `created_by UUID REFERENCES public.cong_chuc(id)`
- Enum: `VARCHAR + CHECK constraint`
- Bucket MinIO: `meeting`, layout xem `HKG_DATABASE_DESIGN.md §7`
- API base: `/api/v1/hop-khong-giay/`
- VN snake_case theo pattern KPI/LMS
- Test framework: pytest, bám `backend/lms_service/tests/`

---

## 9. BÁO CÁO CUỐI MỖI GIAI ĐOẠN (template)

```markdown
## Giai đoạn {P0|P1|G0|G1|G2|G3|G4} — DONE

### Files thay đổi
- created: <relative path>
- modified: <relative path>

### DB (nếu có)
- Migration: <id> (head)
- Bảng tạo: <số>
- Platform roles seed: <số>

### Endpoints expose (nếu có)
- METHOD /api/v1/hop-khong-giay/<path>

### Quyết định kỹ thuật (nếu lệch spec)
- ...

### Test
- pytest: X passed, Y failed
- npm run build: ok / fail

### Câu hỏi/blocker cho user
- ...

### Action cần user
- ...
```

---

## 10. KHI UNSURE

- KHÔNG đoán bừa → đặt câu hỏi cho user
- Phát hiện cần sửa `public.cong_chuc/don_vi/vai_tro` → đề xuất platform_role mới
- Conflict spec ↔ codebase → ưu tiên codebase, ghi vào SPEC_CHANGELOG nếu cần sửa spec
- Library version: bám stack hiện có, không tự bump
- Không log JWT/password/secret ra console hay audit log

---

## 11. DEFINITION OF DONE (toàn bộ scaffold)

```
□ 4 ràng buộc kiến trúc: KHÔNG vi phạm điểm nào
□ Spec gốc đã sync với codebase (P1 done, user re-upload xong)
□ common.audit_log tồn tại; HKG có log row module='MEETING' sau mỗi mutation
□ JWT chứa platform_roles[] đúng — verify bằng login user có gán THU_KY_HOP
□ Migration head chạy clean trên DB rỗng và DB có sẵn KPI+LMS
□ Backend port 8004 lên được, /health 200, /docs đầy đủ
□ Frontend build pass, route /hop-khong-giay reachable sau login
□ Tạo được 1 cuộc họp test → giấy mời → 1 user nhận thông báo in-app
□ Test pytest pass, không log lộ token
□ README.md ngắn ở backend/meeting_service/
```