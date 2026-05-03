# HKG_PREFLIGHT_RESULTS.md — Kết quả Pre-flight P0

**Phiên bản:** 1.0 · **Ngày:** 2026-04-30 · **Người chạy:** Claude (CLI scaffold)

> File này ghi lại kết quả P0 Pre-flight checks theo `PROMPT_GUIDE_HKG.md v1.2 §3`. Dùng làm input cho P1 (Spec Correction).

---

## 3.1. Môi trường — TẤT CẢ OK

| Check | Kết quả | Ghi chú |
|---|---|---|
| `backend/meeting_service/` chưa tồn tại | ✅ PASS | Chưa có folder |
| Schema `meeting` chưa tồn tại trong DB | ✅ PASS | Chưa migrate (chưa có file alembic `meeting.*`) |
| Route `frontend/src/app/(main)/hop-khong-giay/` chưa tồn tại | ✅ PASS | Chưa scaffold |
| Port 8004 chưa bị chiếm trong docker-compose / .env | ✅ PASS | KPI=8000, LMS=8001, Forum=8002, Legal=8003 — 8004 free |

---

## 3.2. Codebase reconnaissance

### 3.2.A. `public.platform_role` — schema thật

File: `backend/alembic/versions/add_platform_tables_20260220.py`

```
Cột thật:                         Spec hiện ghi:
─────────────────────────         ─────────────────────────
id              UUID PK            ✅ trùng
ma_role         VARCHAR(50) UNIQ   ❌ spec ghi "ma_vai_tro"  → CẦN SỬA (FIX-1)
ten_role        VARCHAR(100)       ❌ spec ghi "ten_vai_tro" → CẦN SỬA (FIX-1)
mo_ta           TEXT               ✅ trùng
quyen_han       JSONB              ❌ spec không dùng → CẦN MAP module vào đây (FIX-1)
is_active       BOOLEAN DEFAULT t  ❌ spec không dùng → CẦN BỔ SUNG (FIX-1)
created_at      TIMESTAMP          ✅ trùng
```

**Không có cột `module` riêng**, không có cột `is_dynamic` riêng. → Encode vào `quyen_han` JSONB.

### 3.2.B. `public.cong_chuc_platform_role` — schema thật

```
id                      UUID PK
cong_chuc_id            UUID FK → public.cong_chuc(id)
platform_role_id        UUID FK → public.platform_role(id)
pham_vi                 JSONB            ✅ tên cột đúng như spec
assigned_by             UUID FK → public.cong_chuc(id)
assigned_at             TIMESTAMP
is_active               BOOLEAN DEFAULT t
UNIQUE (cong_chuc_id, platform_role_id)
```

→ Spec dùng `pham_vi` đúng tên cột.

### 3.2.C. `common.thong_bao` — schema thật

File: `backend/common_service/models/thong_bao.py` + `backend/alembic/versions/create_common_schema_20260224.py`

```
Cột thật:                                Spec hiện ghi:
─────────────────────────────            ─────────────────────────
id                  UUID PK
nguoi_nhan_id       UUID FK              ✅ trùng (spec đoán đúng)
tieu_de             VARCHAR(300)         ✅
noi_dung            TEXT                 ✅
loai                VARCHAR(50)          ❌ spec ghi "module" + "loai_thong_bao" → SỬA thành "loai"
link_url            TEXT                 ❌ spec ghi "link" → SỬA thành "link_url"
doi_tuong_type      VARCHAR(50)          (spec chưa dùng — có thể dùng cho sub-loại MEETING)
doi_tuong_id        UUID                 (spec chưa dùng)
da_doc              BOOLEAN DEFAULT f
ngay_doc            TIMESTAMP
muc_do              VARCHAR(20) DEFAULT 'BINH_THUONG'
created_at          TIMESTAMP
```

**Quan trọng:**
- **KHÔNG có cột `module`** — chỉ có `loai`.
- **KHÔNG có CHECK constraint** trên `loai`. Comment liệt kê: `KPI, LMS, FORUM, LEGAL, PORTAL, HE_THONG` → là gợi ý, không enforced.
- → Có thể dùng `loai='MEETING'` ngay, **KHÔNG cần migration mở rộng** (FIX-4 nhẹ hơn dự kiến).
- Sub-loại notification (GIAY_MOI_HOP, NHAC_HOP_24H...) nên đặt vào `doi_tuong_type` hoặc `tieu_de`.

### 3.2.D. `common.audit_log` — KHÔNG TỒN TẠI ❌

```
SELECT to_regclass('common.audit_log');  -- NULL
```

- File `backend/common_service/models/` không có `audit_log.py`.
- Migration `create_common_schema_20260224.py` chỉ tạo: `thong_bao`, `file_storage`, `knowledge_base`, `kpi_integration_log`.

KPI có audit_log riêng tại `backend/app/models/audit_log.py`:
- Schema: `public` (default)
- Cột: `id, table_name, record_id, action(INSERT/UPDATE/DELETE), old_value, new_value, user_id, ip_address, user_agent, created_at`
- **Design khác hoàn toàn** — chỉ track DML thay đổi, không có cột `module/hanh_dong` cho audit nghiệp vụ HKG.
- → KHÔNG tái sử dụng được cho HKG.

**Kết luận FIX-3:** PHẢI tạo `common.audit_log` mới ở G0 (platform-level prerequisite).

### 3.2.E. Shared module path (JWT, deps)

| Item | Path verify | Note |
|---|---|---|
| Login endpoint | `backend/app/api/v1/endpoints/auth.py` | KPI backend (port 8000) |
| JWT create | `backend/app/core/security.py` → `create_access_token()` | Đã có `additional_claims` mở rộng |
| LMS auth dep | `backend/lms_service/dependencies.py` | Verify pattern |

### 3.2.F. MinIO upload pattern reference

- `backend/lms_service/services/` có nhiều service file — bám pattern này cho HKG.
- Bucket KPI/LMS hiện đang dùng — HKG sẽ tạo bucket riêng `meeting`.

### 3.2.G. Alembic env

```python
# backend/alembic/env.py
target_metadata = Base.metadata
include_schemas=True  # ✅ đã enable cho multi-schema
```

→ Migration HKG schema `meeting` chạy được không cần config thêm.

### 3.2.H. Frontend package manager

```
frontend/package-lock.json    ✅ tồn tại
frontend/pnpm-lock.yaml       ❌ không có
frontend/yarn.lock            ❌ không có
```

→ Frontend dùng **npm**, không phải pnpm. CẦN SỬA `pnpm build` → `npm run build` trong `HKG_SPEC_ADAPTED.md` (FIX-6).

---

## 3.3. JWT mở rộng — KHÔNG CÒN LÀ BLOCKER ✅

**Phát hiện quan trọng:** JWT **ĐÃ CÓ** `platform_roles[]` rồi.

File: `backend/app/api/v1/endpoints/auth.py` (block "MO RONG PLATFORM (3 fields moi)"):

```python
# v1.1.0 - flag xem toàn chi cục
additional_claims["can_view_all_units"] = ...

# vai_tro alias cho "role"
additional_claims["vai_tro"] = user.vai_tro.ma_vai_tro

# is_lanh_dao
additional_claims["is_lanh_dao"] = ...

# platform_roles: query tu bang cong_chuc_platform_role
pr_result = await db.execute(sa_text(
    "SELECT pr.ma_role FROM public.platform_role pr "
    "JOIN public.cong_chuc_platform_role ccpr ON pr.id = ccpr.platform_role_id "
    "WHERE ccpr.cong_chuc_id = :uid AND ccpr.is_active = true AND pr.is_active = true"
), {"uid": str(user.id)})
additional_claims["platform_roles"] = [r[0] for r in pr_result.fetchall()]
```

**Implications:**
- G0 task "Mở rộng JWT" → **REMOVE** (đã xong).
- HKG_API_SPECS.md §3.1 note nên đổi từ "blocker" → "verify đã hoạt động đúng".
- CLAUDE.md ở dòng `[ ] JWT mở rộng (thêm platform_roles) — Chưa implement` cần update thành `[x] Đã implement`.

---

## 3.4. Platform roles HKG đã có chưa

```sql
SELECT ma_role FROM public.platform_role
WHERE quyen_han->>'module' = 'MEETING';
-- Kết quả: 0 rows
```

→ Cần seed 6 platform_role HKG (bỏ CHU_TOA_HOP dynamic):
- `THU_KY_HOP`
- `CHANH_VP`
- `TRUONG_CNTT`
- `DANG_VIEN`
- `BI_THU_CHI_BO`
- `PHO_BI_THU`

**Roles hiện đã seed (LMS/Forum/Legal):**
`GIANG_VIEN, QT_DAO_TAO, BIEN_TAP, DIEU_PHOI_FORUM, CHUYEN_GIA, QT_NOI_DUNG, QT_ATTT`.

---

## 3.5. Test pattern reference

```
backend/lms_service/tests/
├── conftest.py
├── test_khoa_hoc.py
├── test_dang_ky.py
├── test_bai_kiem_tra.py
├── test_chung_chi.py
├── test_chuyen_de.py
├── test_dgnl.py
└── test_bao_cao.py
```

→ Bám pattern này khi viết test HKG.

---

## TỔNG KẾT P0

| FIX | Trạng thái sau verify | Ghi chú |
|---|---|---|
| FIX-1 (column names) | ✅ CẦN APPLY | `ma_role/ten_role` thay cho `ma_vai_tro/ten_vai_tro`, dùng `quyen_han` JSONB |
| FIX-2 (bỏ CHU_TOA_HOP) | ✅ CẦN APPLY | Giảm 7 → 6 |
| FIX-3 (common.audit_log) | ✅ CẦN APPLY | Bảng chưa tồn tại — tạo G0 + thêm phụ lục SQL |
| FIX-4 (common.thong_bao) | ✅ CẦN APPLY (NHẸ) | Sửa `module/loai_thong_bao/link` → `loai/link_url`. **Không cần migration** vì không có CHECK |
| FIX-5 (JWT note) | ⚠️ ĐÃ CÓ — đổi nội dung note | Đổi từ "blocker" → "verify hoạt động đúng" |
| FIX-6 (pnpm→npm) | ✅ CẦN APPLY | Frontend đang dùng npm |
| FIX-7 (changelog) | ✅ TẠO MỚI | SPEC_CHANGELOG.md |

**G0 task list cập nhật (sau Pre-flight):**

- [x] Mở rộng JWT — ĐÃ CÓ, chỉ verify
- [ ] Tạo `common.audit_log` (migration platform-level common_service)
- [ ] (Optional) Document loại MEETING vào comment `common.thong_bao` migration

---

*P0 Pre-flight hoàn tất 2026-04-30. Chuyển P1 — sửa spec theo HKG_SPEC_FIX_CHECKLIST.md.*
