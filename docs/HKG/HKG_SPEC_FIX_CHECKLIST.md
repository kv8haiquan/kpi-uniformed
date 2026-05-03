# HKG_SPEC_FIX_CHECKLIST.md — Danh sách sửa spec gốc

**Phiên bản:** 1.0 · **Ngày:** 30/04/2026

> File này liệt kê các sửa CLI **phải apply trực tiếp** vào 5 file spec gốc (`HKG_SPEC_ADAPTED.md`, `HKG_DATABASE_DESIGN.md`, `HKG_API_SPECS.md`, `HKG_PLATFORM_ROLES.md`, và optional `PHAN_TICH_VA_GOP_Y_HKG.md`).
>
> **Quy tắc TUYỆT ĐỐI:**
> - Chỉ sửa khi đã verify mismatch trong codebase thật (không sửa theo niềm tin).
> - Mỗi sửa phải ghi vào `SPEC_CHANGELOG.md` với old → new diff.
> - KHÔNG sửa `PHAN_TICH_VA_GOP_Y_HKG.md` (đây là doc lịch sử ghi nhận đúng các vấn đề — để nguyên).
> - Sau khi sửa xong: DỪNG, không tự đi tiếp G0/G1.

---

## FIX-1. `public.platform_role` — tên cột

### Verify trước khi sửa

CLI mở `backend/alembic/versions/add_platform_tables_*.py`, xác nhận schema thật:

```
ma_role     ← KHÔNG phải ma_vai_tro
ten_role    ← KHÔNG phải ten_vai_tro
quyen_han   JSONB ← KHÔNG có cột module riêng
is_active   BOOLEAN
```

Nếu codebase thật KHÁC checklist này → DỪNG, hỏi user. KHÔNG tự suy diễn.

### File cần sửa

#### A. `HKG_PLATFORM_ROLES.md`

- **§3.2 và mọi vị trí khác** dùng `ma_vai_tro` / `ten_vai_tro` → đổi sang `ma_role` / `ten_role`.
- **§4 (Chi tiết quyền)** không cần đổi (chỉ mô tả nghiệp vụ).
- **§9 (`pham_vi` JSONB format)** không cần đổi (đang dùng cột `pham_vi` của bảng `cong_chuc_platform_role` — verify cột này trong codebase trước).

#### B. `HKG_DATABASE_DESIGN.md`

- **§8.1 (Seed Platform roles SQL)** — viết lại đoạn INSERT:

  ```sql
  -- Trước (SAI):
  INSERT INTO public.platform_role (ma_vai_tro, ten_vai_tro, mo_ta, module) VALUES (...);

  -- Sau (ĐÚNG):
  INSERT INTO public.platform_role (ma_role, ten_role, mo_ta, quyen_han, is_active) VALUES
  ('THU_KY_HOP',     'Thư ký cuộc họp',     'Ghi biên bản, hỗ trợ điều hành',  '{"module":"MEETING","type":"static","scoped":true}'::jsonb,  TRUE),
  ('CHANH_VP',       'Chánh Văn phòng',     'Xem toàn bộ cuộc họp Chi cục',    '{"module":"MEETING","type":"static"}'::jsonb,                TRUE),
  ('TRUONG_CNTT',    'Trưởng phòng CNTT',   'Quản trị + xem toàn bộ',          '{"module":"MEETING","type":"static"}'::jsonb,                TRUE),
  ('DANG_VIEN',      'Đảng viên',           'Tham dự họp Đảng',                '{"module":"MEETING","type":"static"}'::jsonb,                TRUE),
  ('BI_THU_CHI_BO',  'Bí thư Chi bộ',       'Chủ trì họp Chi bộ',              '{"module":"MEETING","type":"static","scoped":true}'::jsonb,  TRUE),
  ('PHO_BI_THU',     'Phó Bí thư Chi bộ',   'Hỗ trợ họp Chi bộ',               '{"module":"MEETING","type":"static","scoped":true}'::jsonb,  TRUE);
  ```

- **Thêm note:** "Filter HKG roles bằng `WHERE quyen_han->>'module' = 'MEETING'`."

---

## FIX-2. Bỏ `CHU_TOA_HOP` khỏi danh sách seed (7 → 6)

### Lý do

`CHU_TOA_HOP` là dynamic role, suy ra từ `meeting.cuoc_hop.chu_toa_id` mỗi cuộc họp. Permission check trực tiếp `cuoc_hop.chu_toa_id = current_user_id`, không qua bảng `platform_role`. Seed là thừa và mâu thuẫn với chính §3.2 của `HKG_PLATFORM_ROLES.md`.

### File cần sửa

#### A. `HKG_PLATFORM_ROLES.md`

- **§3.1 (Bảng tổng quan):** xóa hàng `CHU_TOA_HOP` HOẶC đổi cột "Phạm vi" thành "Tính dynamic theo cuoc_hop.chu_toa_id, không lưu trong cong_chuc_platform_role".
- **§3.2 (CHU_TOA_HOP):** giữ nguyên section (vì giải thích dynamic role) nhưng thêm note: "**KHÔNG có trong danh sách seed** (xem §8.1 của `HKG_DATABASE_DESIGN.md`)".
- **§8 (Checklist cấu hình sau migration):** đổi "Seed 7 platform_roles" → "Seed 6 platform_roles".

#### B. `HKG_DATABASE_DESIGN.md`

- **§8.1:** SQL seed chỉ còn 6 INSERT (đã viết ở FIX-1).

#### C. `HKG_SPEC_ADAPTED.md`

- **§4.1:** "platform_roles HKG (cần seed mới)" — chỉnh danh sách bỏ `CHU_TOA_HOP`, ghi rõ "6 platform_role static; `CHU_TOA_HOP` là dynamic, không seed".

---

## FIX-3. `common.audit_log` — tạo migration platform-level TRƯỚC HKG

### Verify trước khi sửa

```sql
SELECT to_regclass('common.audit_log');
-- Nếu NULL → bảng chưa tồn tại
```

Cũng kiểm tra: `app/models/audit_log.py` của KPI nằm ở schema nào (public/kpi/common)?

### File cần sửa

#### A. `HKG_SPEC_ADAPTED.md`

- **§1.1 và §1.2 (4 ràng buộc tuyệt đối):** ràng buộc số 4 hiệu đính:

  ```
  4. ⛔ KHÔNG tạo audit_log riêng cho HKG. Dùng common.audit_log.
     Nếu common.audit_log CHƯA tồn tại: tạo migration platform-level
     (trong common_service) TRƯỚC khi vào G1 — đây là trách nhiệm nền tảng,
     không phải scope HKG.
  ```

#### B. `HKG_DATABASE_DESIGN.md`

- **§1 (Nguyên tắc thiết kế):** giữ nguyên dòng "KHÔNG tạo bảng audit_log riêng — dùng common.audit_log", thêm: "*Lưu ý: nếu common.audit_log chưa tồn tại trong codebase, tạo migration platform-level trong common_service trước. Schema gợi ý ở phụ lục cuối file.*"
- **Thêm phụ lục mới ở cuối file** — tiêu đề "Phụ lục A: Schema gợi ý cho common.audit_log (nếu chưa có)" với SQL:

  ```sql
  CREATE TABLE common.audit_log (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      module VARCHAR(20) NOT NULL,
      hanh_dong VARCHAR(50) NOT NULL,
      doi_tuong_loai VARCHAR(50),
      doi_tuong_id UUID,
      nguoi_thuc_hien_id UUID NOT NULL REFERENCES public.cong_chuc(id),
      ip_address INET,
      user_agent TEXT,
      chi_tiet JSONB,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );

  CREATE INDEX idx_audit_log_module ON common.audit_log(module);
  CREATE INDEX idx_audit_log_doi_tuong ON common.audit_log(doi_tuong_loai, doi_tuong_id);
  CREATE INDEX idx_audit_log_nguoi ON common.audit_log(nguoi_thuc_hien_id);
  CREATE INDEX idx_audit_log_thoi_gian ON common.audit_log(created_at DESC);
  ```

---

## FIX-4. `common.thong_bao` — verify schema thật trước khi sửa spec

### Verify trước khi sửa

CLI mở `backend/common_service/models/thong_bao.py` (hoặc path tương đương), ghi nhận:

- Tên cột phân biệt module: `module` / `loai_he_thong` / khác?
- Tên cột người nhận: `nguoi_nhan_id` / `cong_chuc_nhan_id` / khác?
- CHECK constraint hoặc enum giới hạn loại?
- Đã có loại `MEETING` chưa?

### File cần sửa (sau khi đã verify)

#### A. `HKG_DATABASE_DESIGN.md` §6 (`SỬ DỤNG common.thong_bao`)

- Sửa câu lệnh INSERT mẫu cho khớp tên cột thật.
- Thêm note: nếu `common.thong_bao` có CHECK constraint chưa cho `MEETING` → cần migration mở rộng trong `common_service` trước G2.

#### B. `HKG_API_SPECS.md` các đoạn "Side effects: Insert thông báo ..."

- Không cần sửa wording (vẫn nói "Insert thông báo XXX"), nhưng comment trong code thực tế phải dùng tên cột verify.

---

## FIX-5. `HKG_API_SPECS.md` §3.1 — JWT mở rộng `platform_roles[]`

Spec hiện đã ghi đúng — không sửa text. Nhưng thêm vào CUỐI §3.1:

> **Lưu ý triển khai:** field `platform_roles[]` chưa có sẵn trong JWT của codebase hiện tại. Phải mở rộng trong G0 trước khi vào G2. Files cần sửa: `backend/app/core/security.py`, `backend/app/api/v1/endpoints/auth.py` (verify path chính xác từ codebase). Logic: query `cong_chuc_platform_role` của user → nhét `[ma_role for r in roles]` vào claim.

---

## FIX-6. `HKG_SPEC_ADAPTED.md` — đính chính tooling

#### A. §3.2 / mọi nơi nhắc package manager

- `pnpm build` → `npm run build` (nếu codebase thực dùng npm).
- CLI verify trong `frontend/package.json` + có file `package-lock.json` (npm) hay `pnpm-lock.yaml` (pnpm).

#### B. Thêm 1 bullet vào §3.3 (Backend service)

> Test framework + pattern: bám `backend/lms_service/tests/` (pytest, fixtures `conftest.py`).

---

## FIX-7. CLI sinh `SPEC_CHANGELOG.md`

Sau khi sửa xong, CLI tạo file `docs/HKG/SPEC_CHANGELOG.md` ghi lại MỌI thay đổi:

```markdown
# SPEC_CHANGELOG.md

## 2026-04-30 — Fix mismatch với codebase

### HKG_PLATFORM_ROLES.md
- §3.1: removed CHU_TOA_HOP from seed list (dynamic role)
- §3.2: ma_vai_tro → ma_role (5 occurrences)
- §8: "Seed 7 platform_roles" → "Seed 6 platform_roles"

### HKG_DATABASE_DESIGN.md
- §8.1: rewrote INSERT to use ma_role/ten_role/quyen_han(JSONB), 6 rows instead of 7
- §1: added note about common.audit_log creation if missing
- Added: Phụ lục A — schema gợi ý common.audit_log

### HKG_SPEC_ADAPTED.md
- §1.2: ràng buộc số 4 hiệu đính
- §3.2: pnpm → npm
- §4.1: 7 → 6 platform_roles, ghi rõ CHU_TOA_HOP dynamic

### HKG_API_SPECS.md
- §3.1: thêm note về JWT mở rộng

### Files KHÔNG sửa
- PHAN_TICH_VA_GOP_Y_HKG.md (doc lịch sử)
```

---

## Quy trình áp dụng

1. CLI đọc file này + Pre-flight kết quả
2. Với mỗi FIX (1→7), verify lại trong codebase
3. Apply sửa vào spec gốc bằng `str_replace` hoặc tương đương
4. Ghi `SPEC_CHANGELOG.md`
5. Điền `HKG_PREFLIGHT_RESULTS.md`
6. **DỪNG**, hiển thị summary cho user:
   ```
   Đã sửa N spec files. Vui lòng:
   1. Review SPEC_CHANGELOG.md
   2. Re-upload các file sau lên Claude.ai project knowledge:
      - HKG_PLATFORM_ROLES.md
      - HKG_DATABASE_DESIGN.md
      - HKG_SPEC_ADAPTED.md
      - HKG_API_SPECS.md
   3. Reply "Approve G0" để tôi bắt đầu platform prerequisites.
   ```