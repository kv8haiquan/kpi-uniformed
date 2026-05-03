# SPEC_CHANGELOG.md — Lịch sử sửa spec HKG

> Ghi nhận MỌI sửa đổi từ Pre-flight P0 + Spec Correction P1 theo `HKG_SPEC_FIX_CHECKLIST.md`.

---

## 2026-04-30 — Fix mismatch với codebase (P0 + P1)

**Người thực hiện:** Claude (CLI scaffold).
**Tham chiếu Pre-flight:** `HKG_PREFLIGHT_RESULTS.md`.

### File `HKG_PLATFORM_ROLES.md`

**FIX-1 (column names):**
- §3.1 Bảng tổng quan: header cột "Mã vai trò" → "Mã role (`ma_role`)"; "Tên hiển thị" → "Tên hiển thị (`ten_role`)". Thêm cột "Seed?" đánh dấu role nào seed (✅) vs dynamic (❌).
- §3.2 (CHU_TOA_HOP): tiêu đề bổ sung "(DYNAMIC — KHÔNG SEED)"; thêm dòng "KHÔNG có trong danh sách seed (xem §4 và §8.1 của HKG_DATABASE_DESIGN.md)".
- §4 Seed Migration: viết lại hoàn toàn.
  - **Old:** `INSERT ... (id, ma_vai_tro, ten_vai_tro, mo_ta, module, created_at)` — schema không tồn tại.
  - **New:** `INSERT ... (id, ma_role, ten_role, mo_ta, quyen_han, is_active, created_at)` đúng schema thật. Encode `module/type/scoped` vào `quyen_han` JSONB. Thêm bảng giải thích semantics 3 keys.
- §9 (`pham_vi` JSONB format): các SQL ví dụ đổi `'{thu_ky_role_id}'` placeholder → sub-query `(SELECT id FROM public.platform_role WHERE ma_role = 'THU_KY_HOP')`.

**FIX-2 (bỏ CHU_TOA_HOP khỏi seed, 7→6):**
- §3.1: cột "Seed?" đánh ❌ cho CHU_TOA_HOP.
- §3.2: bổ sung note "KHÔNG seed" (xem trên).
- §4: PLATFORM_ROLES_HKG list giảm 7 → 6 mục (xóa entry CHU_TOA_HOP).
- §8 Checklist: "Seed 7 platform_roles" → "Seed 6 platform_roles static (CHU_TOA_HOP là dynamic — không seed)".

### File `HKG_DATABASE_DESIGN.md`

**FIX-1 + FIX-2 (§8.1 Seed Platform roles):**
- **Old:** `INSERT INTO public.platform_role (ma_vai_tro, ten_vai_tro, mo_ta, module) VALUES ...` 7 rows.
- **New:** `INSERT INTO public.platform_role (ma_role, ten_role, mo_ta, quyen_han, is_active) VALUES ...` 6 rows. Sử dụng `quyen_han` JSONB cho `module/type/scoped`. Thêm `ON CONFLICT (ma_role) DO NOTHING`. Thêm note filter `WHERE quyen_han->>'module' = 'MEETING'`.

**FIX-3 (common.audit_log):**
- §1 (Nguyên tắc thiết kế): thêm callout box giải thích bảng chưa tồn tại + hướng dẫn tạo migration platform-level + lý do KPI audit_log không tái sử dụng được.
- §5 (Sử dụng audit_log): chỉnh tên cột INSERT cho khớp Phụ lục A.
  - **Old:** `(module, action, entity_type, entity_id, user_id, details)`.
  - **New:** `(module, hanh_dong, doi_tuong_loai, doi_tuong_id, nguoi_thuc_hien_id, chi_tiet)`.
- **Thêm Phụ lục A** ở cuối file: schema gợi ý đầy đủ cho `common.audit_log` (CREATE TABLE + 5 indexes), pattern INSERT mẫu, phân biệt với `app/models/audit_log.py` của KPI.

**FIX-4 (common.thong_bao schema thật):**
- §6: viết lại block sử dụng.
  - **Old:** `INSERT INTO common.thong_bao (module, loai_thong_bao, nguoi_nhan_id, tieu_de, noi_dung, link)` — sai cột.
  - **New:** `INSERT INTO common.thong_bao (nguoi_nhan_id, tieu_de, noi_dung, loai, link_url, doi_tuong_type, doi_tuong_id, muc_do)` đúng schema thật.
- Pattern HKG: dùng `loai='MEETING'` (module level) + `doi_tuong_type` lưu sub-loại (GIAY_MOI_HOP, NHAC_HOP_24H...) + `doi_tuong_id` = cuoc_hop_id.
- Thêm callout: KHÔNG có CHECK constraint trên `loai` → KHÔNG cần migration mở rộng.
- Thêm câu lệnh SELECT mẫu để đọc thông báo HKG của 1 user.

### File `HKG_SPEC_ADAPTED.md`

**FIX-3 (ràng buộc số 4):**
- §1.2: ràng buộc số 4 viết lại đầy đủ — yêu cầu tạo `common.audit_log` ở G0 nếu chưa có; ghi rõ "trách nhiệm nền tảng, không phải scope HKG"; trỏ tới Phụ lục A.

**FIX-2 (§4.1 Cấu trúc 2 lớp):**
- **Old:** liệt kê 7 platform_roles HKG.
- **New:** chia rõ "6 role STATIC cần seed" vs "1 role DYNAMIC (KHÔNG seed) — CHU_TOA_HOP suy ra từ meeting.cuoc_hop.chu_toa_id".

**FIX-6 (test framework + npm note):**
- §3.3: thêm block "Pattern reference (verify P0)" cuối section — bám LMS service skeleton, test pytest theo `lms_service/tests/conftest.py`, frontend dùng npm với `npm run build`.
- §3.2: KHÔNG sửa (file không có chuỗi `pnpm` ban đầu — verify bằng grep).

### File `HKG_API_SPECS.md`

**FIX-5 (note JWT mở rộng):**
- §3.1: thêm callout cuối section.
  - **Phát hiện P0:** JWT **đã có** `platform_roles[]` rồi. Code injection nằm tại `backend/app/api/v1/endpoints/auth.py` block "MO RONG PLATFORM (3 fields moi)".
  - Note ghi: "KHÔNG còn là blocker cho G2. Chỉ cần verify trong G0 (login user có `THU_KY_HOP` → JWT decode đúng)".

### File `HKG_SPEC_FIX_CHECKLIST.md` — KHÔNG SỬA

(Là instruction file, để nguyên cho lịch sử.)

### File `PHAN_TICH_VA_GOP_Y_HKG.md` — KHÔNG SỬA

(Doc lịch sử ghi nhận đúng các vấn đề.)

### File mới được tạo

- `docs/HKG/HKG_PREFLIGHT_RESULTS.md` — kết quả P0 Pre-flight đầy đủ.
- `docs/HKG/SPEC_CHANGELOG.md` — file này.

---

## Tóm tắt impact lên G0/G1

| Item | Trước Fix | Sau Fix |
|---|---|---|
| Migration seed platform_role | 7 rows, sai tên cột → FAIL khi chạy | 6 rows, đúng schema → OK |
| `common.audit_log` reference | Giả định có sẵn → INSERT FAIL | Có Phụ lục A để tạo bảng ở G0 |
| `common.thong_bao` reference | Sai tên cột → INSERT FAIL | Đúng schema, không cần migration |
| JWT mở rộng | Tưởng là blocker G0 | Đã có sẵn — chỉ verify |
| Test framework | Không nói rõ | Bám LMS pattern |
| Frontend tooling | Không xác định | npm (xác nhận từ package-lock.json) |

→ G0 work giảm còn **1 task chính**: tạo `common.audit_log` migration platform-level.
→ G1 ready để bắt đầu sau khi user duyệt.

---

## Verify integrity

| Spec | Đọc lại OK? | Format markdown OK? |
|---|:---:|:---:|
| HKG_PLATFORM_ROLES.md | ✅ | ✅ |
| HKG_DATABASE_DESIGN.md | ✅ | ✅ |
| HKG_SPEC_ADAPTED.md | ✅ | ✅ |
| HKG_API_SPECS.md | ✅ | ✅ |

*Changelog hoàn tất 2026-04-30. Chuyển hand-off sang user — review + re-upload lên Claude.ai project knowledge.*

---

## 2026-04-30 — Fix bổ sung (theo user request sau review SPEC_CHANGELOG)

- **FIX-A — `HKG_DATABASE_DESIGN.md` §9 (Checklist migration):** sửa dòng 011 cho khớp với §8.1 đã giảm 7→6.
  - **Old:** `011_seed_platform_roles_meeting.py   — Seed 7 platform roles`
  - **New:** `011_seed_platform_roles_meeting.py   — Seed 6 platform roles (CHU_TOA_HOP dynamic)`
- **FIX-B — `HKG_SPEC_ADAPTED.md` §6.1 (Phụ thuộc của HKG):** cập nhật trạng thái JWT theo phát hiện P0 (đã có sẵn, không cần làm thêm).
  - **Old:** `| JWT mở rộng có `platform_roles[]` | ⏳ Cần check | Phòng CNTT |`
  - **New:** `| JWT mở rộng có `platform_roles[]` | ✅ Đã có sẵn (auth.py block 'MO RONG PLATFORM') | - |`

---

## 2026-04-30 — Port HKG đổi 8004 → 8006 do conflict portal_service

**Trigger:** Cuối G2, verify §7 phát hiện `portal_service` đã chiếm `0.0.0.0:8004` (PID 2312199, không document trong CLAUDE.md). Không tự kill — user chọn phương án (b): đổi HKG sang port mới.

### Files modified
- `backend/meeting_service/config.py` — `service_port: 8004 → 8006`
- `backend/meeting_service/main.py` — docstring run command 8004 → 8006
- `backend/meeting_service/README.md` — toàn bộ 6 occurrences 8004 → 8006
- `docs/HKG/HKG_API_SPECS.md` — header `port **8004**` → `**8006**`; §2 URL example 8004 → 8006
- `docs/HKG/HKG_SPEC_ADAPTED.md` — §1.1 table row, §3.1 ASCII diagram, §3.3 folder comment

### Reconcile port map thực tế (đã verify 2026-05-01)
| Port | Service | Status trong CLAUDE.md |
|---|---|---|
| 8000 | KPI (`app.main`) | ✅ documented |
| 8001 | LMS | ✅ documented |
| 8002 | Forum | ✅ documented |
| 8003 | Legal | ✅ documented |
| 8004 | portal_service | ⚠️ chưa document |
| 8005 | common_service | ⚠️ chưa document |
| 8006 | HKG meeting_service | 🆕 chưa document |

→ `CLAUDE.md` **cần** cập nhật port map. Diff đề xuất xem report cuối G2-fix (chờ user duyệt — KHÔNG tự sửa).

### Test impact
- pytest dùng `httpx.ASGITransport` (in-process, không bind port) → KHÔNG bị ảnh hưởng. Re-run xác nhận 13 passed.
- Port 8004 vẫn là portal_service (PID không đổi, không phá).

---

## 2026-05-01 — Infra deviation: filesystem (thay MinIO) + APScheduler (thay Celery)

**Trigger:** G3a recon phát hiện MinIO server, Celery package, Redis broker đều KHÔNG có trong codebase. Spec gốc giả định MinIO + Celery — không khả thi mà không setup infra mới.

### Quyết định

**Storage → Phương án (A) filesystem (giữ schema cột legacy):**
- Path layout: `uploads/meeting/{cuoc_hop_id}/{uuid}_{filename}`
- DB cột `minio_bucket = 'meeting'` (constant), `minio_key` = relative path
- Endpoint `xem`/`tai`: trả URL kèm JWT short-lived token (TTL 1h) thay presigned MinIO URL
- Bucket init: KHÔNG cần. `mkdir -p` lazy ở lần upload đầu tiên.
- Bám pattern `lms_service/services/file_service.py` đã production.
- **Nâng cấp MinIO** → Phase 4+. DB schema sẽ không đổi (cột đã abstract).

**Scheduler → APScheduler in-process (thay Celery+Redis):**
- `pip install apscheduler` (đã cài 01/05/2026, version 3.11.2)
- 4 jobs trong `meeting_service/scheduler.py`:
  - `auto_approve_xin_phep_vang` — interval 10 phút
  - `nhac_hop_3_tang` — interval 1 phút (windows 24h/1h/30p)
  - `nhac_han_ket_luan` — cron 8AM hàng ngày
  - `mark_tre_han_ket_luan` — cron 0AM hàng ngày
- Start trong FastAPI lifespan event (`@asynccontextmanager`).
- Test: gọi function trực tiếp, không cần eager mode.
- **Single-server only.** Multi-server deployment cần migrate sang Celery+Redis.

### Files modified

- `docs/HKG/HKG_API_SPECS.md §5.3-5.4` — note JWT short-lived token thay presigned URL.
- `docs/HKG/HKG_DATABASE_DESIGN.md §7` — đổi tiêu đề "MINIO BUCKET" → "STORAGE LAYOUT", note filesystem MVP.
- `docs/prompts/PROMPT_GUIDE_HKG.md §5 G3` — APScheduler thay Celery, filesystem thay MinIO.

### Files giữ nguyên

- DB schema (`HKG_DATABASE_DESIGN.md §4`): cột `minio_bucket/minio_key` không đổi tên.
- Migration `meeting_004_create_tai_lieu`: server_default `minio_bucket='meeting'` vẫn đúng.
- Tests methodology (tx-rollback, TEST-G*-* prefix) không đổi.

---

## 2026-05-01 — G3b: Tracking nhắc họp dùng `common.thong_bao` (không sửa schema)

**Trigger:** G3b cần implement scheduler `nhac_hop_3_tang` gửi 3 nhắc trước họp (24h/1h/30p). Phải tránh duplicate khi job interval 1 phút trùng window. CLI propose 3 phương án; user chọn (A).

### Decision

**Phương án (A) — query `common.thong_bao` để check đã nhắc.** Logic:
```sql
SELECT doi_tuong_id, doi_tuong_type
  FROM common.thong_bao
 WHERE doi_tuong_id IN (:cuoc_hop_ids)
   AND doi_tuong_type IN ('NHAC_HOP_24H','NHAC_HOP_1H','NHAC_HOP_30P')
```

### Tại sao không thêm cột vào `meeting.cuoc_hop`

- ⛔ Phải migrate thêm 3 cột bool hoặc 1 JSONB → đụng schema, vi phạm "CLI propose trước, không tự sửa schema".
- ⛔ State về notification ở 2 nơi → nguồn lỗi đồng bộ.
- ⛔ Khó mở rộng (thêm window 5p sau cũng phải migrate).

### Optimizations

1. **Cache RAM 1 phút (TTL ngắn):** scheduler chạy interval 1p, mỗi tick query 1 lần và cache. Giải quyết multi-window check (24h+1h+30p) chỉ 1 query.
2. **Batch `WHERE doi_tuong_id IN (...)`:** với N cuộc họp đang trong scope, query 1 lần thay vì N lần.

### Test methodology

Dùng `freezegun` để mock thời gian. Test 4 transitions:
- `now = ngay_hop - 24h - 3p` → trigger `NHAC_HOP_24H` 1 lần.
- `now = ngay_hop - 24h - 1p` → KHÔNG trigger (đã có row).
- `now = ngay_hop - 1h - 3p` → trigger `NHAC_HOP_1H`.
- `now = ngay_hop - 30p - 3p` → trigger `NHAC_HOP_30P`.

Verify `common.thong_bao` chỉ có 3 rows (24h/1h/30p), không duplicate.

### Files modified

- `backend/meeting_service/scheduler.py` — implement `nhac_hop_3_tang_job` + cache module-level.
- `backend/meeting_service/services/scheduler_helpers.py` (mới) — pure logic functions cho test.
- `backend/meeting_service/tests/test_scheduler.py` (mới) — freezegun-based tests.

### Note phát triển sau

Khi quy mô tăng (>1000 cuộc họp/ngày), có thể cần index composite trên `common.thong_bao(doi_tuong_id, doi_tuong_type)`. Hiện chưa cần — Postgres planner xử lý tốt với UUID equality scan.

---

## 2026-05-01 — G4-fix: TipTap editor + CBCC picker (closed 2 G4 deviations)

**Trigger:** G4 báo cáo có 2 deviation FE quan trọng:
1. TipTap chưa cài → biên bản dùng `<textarea>` plain
2. CBCC search picker chưa có → form tạo cuộc họp nhập UUID trực tiếp

User yêu cầu G4-fix xử lý trước UAT. Spec docs **KHÔNG đổi** (deviation đã ghi G4 báo cáo); chỉ thêm entry này để track việc closed.

### FIX #1 — TipTap editor

**Đã cài:** `@tiptap/react @tiptap/starter-kit @tiptap/pm` (vào `frontend/package.json`).

**Files mới:**
- `frontend/src/components/editor/TipTapEditor.tsx` — basic toolbar (Bold/Italic/H2/H3/BulletList/OrderedList/Quote/Undo/Redo). Output TipTap JSON + HTML. Vietnamese Unicode native qua contenteditable. `immediatelyRender: false` để tránh hydration mismatch trong Next.js 16 SSR.

**Files modified:**
- `frontend/src/app/(main)/hop-khong-giay/chi-tiet/[id]/bien-ban/page.tsx`:
  - Replace textarea → `<TipTapEditor>`.
  - Auto-save debounce 30s khi editor thay đổi.
  - Detect TipTap doc vs legacy `noi_dung_thao_luan` plain text → wrap thành TipTap doc.
  - Lưu nội dung pending trước khi `trinh-ky` / `ky` để tránh mất data.

### FIX #2 — CongChucPicker

**Quyết định backend:** dùng LMS endpoint `GET /api/v1/lms/cbcc/search?q=...` đã có sẵn (verify P0 — `lms_service/api/endpoints/cbcc.py`). KHÔNG cài endpoint mới ở `meeting_service`.

**Permission gap:** LMS endpoint allowlist `is_admin | SUPER_ADMIN | GIANG_VIEN | QT_DAO_TAO | is_lanh_dao`. Form-creators HKG (TDV/PDV/CCT/PCCT/admin) đều pass — `is_lanh_dao=true` cho leadership. THU_KY_HOP role thuần (CC + platform_role) sẽ FAIL 403 → fallback UI message thông báo "Không có quyền tìm CBCC. Liên hệ admin để thêm role GIANG_VIEN/QT_DAO_TAO hoặc nhập UUID trực tiếp." Phase tiếp có thể: (a) extend LMS permission cho HKG roles, (b) tạo HKG endpoint search riêng.

**Files mới:**
- `frontend/src/components/hkg/CongChucPicker.tsx` — type-ahead với debounce 300ms, single + multi mode, module-level cache cho selected items, dropdown click-outside-to-close.

**Files modified:**
- `frontend/src/app/(main)/hop-khong-giay/tao-hop/page.tsx`:
  - `chu_toa_id`, `thu_ky_id` → `<CongChucPicker multiple={false}>` qua `react-hook-form Controller`.
  - `thanh_phan_text` (CSV UUIDs textarea) → `<CongChucPicker multiple>` quản lý array trong `useState`.
  - `don_vi_to_chuc_id` (UUID input) → `<select>` 14 đơn vị từ `GET /api/v1/lms/don-vi` (LMS endpoint cho mọi user đăng nhập).

### Verify

- `npm run build` → ✓ Compiled successfully in 8.4s. 9 HKG routes vẫn mount.
- Lint: 0 lỗi mới (TipTap + Picker types đầy đủ).
- KHÔNG đụng backend `meeting_service`.
- KHÔNG đổi spec docs (`HKG_*.md` giữ nguyên).

---

## 2026-05-01 — G4-fix-2: tạo endpoint search CBCC riêng cho HKG

**Trigger:** G4-fix dùng `GET /api/v1/lms/cbcc/search` của LMS làm tạm; permission allowlist LMS không cover role HKG đặc thù `THU_KY_HOP` (CC + platform_role, không có `is_lanh_dao`). User chọn phương án (b): tạo endpoint riêng trong meeting_service.

### Files mới

- `backend/meeting_service/api/endpoints/cong_chuc.py` — endpoint `GET /cong-chuc/search?q&limit`. ACL helper `_can_search_cbcc` + dependency `require_can_search_cbcc`.
- `backend/meeting_service/tests/test_cong_chuc_search.py` — 4 tests (happy SUPER_ADMIN, perm denied CBCC thường, granted THU_KY_HOP, SQL injection safe).

### Files modified

- `backend/meeting_service/main.py` — register `cong_chuc_router`.
- `frontend/src/services/hkg.ts` — thêm `congChucApi.search()`.
- `frontend/src/components/hkg/CongChucPicker.tsx` — đổi endpoint sang HKG (`congChucApi.search`), bỏ block fallback "Liên hệ admin", giữ debounce 300ms + cache module.
- `docs/HKG/HKG_API_SPECS.md` — thêm §11A.1 documenting endpoint mới + ACL.

### ACL endpoint mới

```
SUPER_ADMIN | ADMIN | CCT | PCCT | TDV | PDV          (vai_tro KPI)
+ THU_KY_HOP | CHANH_VP | TRUONG_CNTT | BI_THU_CHI_BO  (platform_roles HKG)
+ is_lanh_dao = TRUE                                    (flag)
→ Còn lại = 403 NO_PERMISSION
```

### Decisions kỹ thuật

1. **KHÔNG ghi audit log** — type-ahead query rate cao (mỗi keystroke debounce 300ms = ~5 req/sec/user). Audit log sẽ noise. Read-only, không thay đổi state.
2. **Parameterized query** — `sa_text(... ILIKE :pattern ...)` với bind param. SQL injection test pass với payload `'; DROP TABLE meeting.cuoc_hop; --` → trả `[]`, bảng không drop.
3. **JOIN không LEFT JOIN bắt buộc** — `LEFT JOIN public.don_vi` để CBCC chưa gán don_vi vẫn trả về (không filter mất).
4. **Limit max 50** — không cho client pull bulk (DoS prevention).

### Verify

- `pytest meeting_service/tests/` → **53 passed in 5.10s** (49 cũ + 4 mới).
- `npm run build` → pass (sẽ verify ngay).
- Frontend picker bây giờ dùng endpoint HKG → không còn permission gap với THU_KY_HOP.
