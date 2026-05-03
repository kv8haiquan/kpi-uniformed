# Hướng dẫn Admin — Quản lý KPI V2_PL3

> **Đối tượng:** Admin hệ thống (vai trò ADMIN), TCCB
> **Áp dụng:** Phiên bản KPI V2_PL3 (từ tháng 5/2026 trở đi)

---

## 1. Truy cập

1. Login với tài khoản admin (`ADMIN-001` hoặc tài khoản cấp cho bạn).
2. URL: `https://<host>/admin` — hiện dashboard admin.
3. Menu PL3 V2:
   - `/admin/danh-muc-pl3` — quản lý danh mục công việc PL3
   - `/admin/kpi-version` — pin phiên bản KPI cho CC/đơn vị
   - `/admin/cap-do` (V1 deprecated) — quản lý cấp độ C1-C5 cũ
   - `/admin/sp-chuan` (V1 deprecated) — quản lý SP1-SP4 cũ
   - `/admin/danh-muc-cv` (V1 deprecated) — quản lý danh mục V1 cũ

---

## 2. Quản lý danh mục PL3

### 2.1 Xem danh sách
- Vào `/admin/danh-muc-pl3` — bảng list 50 mục/trang.
- Filter: lĩnh vực (15 La Mã), nhóm (1-5), keyword search.
- Mỗi row hiển thị: Mã, Tên CV, Lĩnh vực, Nhóm, Điểm chấm, Hệ số, Active/Inactive.

### 2.2 Thêm mục mới (manual)
1. Click nút **"+ Thêm mục"**.
2. Nhập:
   - **Mã danh mục**: format `PL3-{lĩnh vực}-{stt}`, ví dụ `PL3-I-CUSTOM-001`. Tối đa 30 ký tự, unique.
   - **Tên công việc**: 3-500 ký tự.
   - **Lĩnh vực**: chọn 1 trong 15.
   - **Nhóm**: 1-5.
   - **Điểm chấm**: số nguyên 1-500, ≤ khung của nhóm.
3. **Tự tính**:
   - `Khung điểm tối đa` = 100/200/300/400/500 (theo nhóm).
   - `Hệ số quy đổi` = `Điểm chấm / 25`.
4. Validate realtime: nếu điểm chấm vượt khung → báo lỗi đỏ.
5. Click **"Lưu"** → mục mới xuất hiện trong list.

### 2.3 Sửa mục
1. Click icon ✏️ ở row cần sửa.
2. Modal hiển thị data hiện tại — sửa các field cần.
3. **Lưu ý:** Không sửa được `Mã danh mục` (đã khoá để giữ FK).
4. Click "Lưu" → audit log ghi nhận thay đổi.

### 2.4 Vô hiệu hóa mục (soft delete)
1. Click icon 🚫 ở row cần vô hiệu hóa.
2. Confirm popup → mục chuyển sang `is_active=FALSE`.
3. Mục sẽ không còn hiện cho CC chọn khi kê khai mới.
4. **Lưu ý:** Bản kê khai cũ vẫn dùng snapshot — KHÔNG bị ảnh hưởng (LOCKED 13).

---

## 3. Import Excel danh mục PL3

Khi Bộ Nội vụ ban hành sửa đổi PL3, admin có thể import file Excel mới mà không cần dev migration.

### 3.1 Chuẩn bị file
- File `.xlsx` (≤ 10MB).
- Sheet tên `PL3`.
- Cột bắt buộc:
  - A: Stt
  - B: Nhiệm vụ (optional)
  - C: Công việc chi tiết (bắt buộc)
  - D: Sản phẩm đầu ra (bắt buộc)
  - E: Phân nhóm ("Nhóm 1"..."Nhóm 5")
  - F: Khung điểm tối đa (100/200/300/400/500)
  - K: Điểm chấm
  - L: Hệ số quy đổi (= K/25)
- Section header định dạng: `I. Tên lĩnh vực`, `II. Tên`, ... (15 lĩnh vực).

### 3.2 Thực hiện import (3 bước)
1. Vào `/admin/danh-muc-pl3` → click **"Import Excel"**.
2. **Bước 1 — Upload**: chọn file → click "Tiếp →".
3. **Bước 2 — Preview**: hệ thống dry-run, hiển thị:
   - Tổng dòng / hợp lệ / lỗi / sẽ insert / sẽ update.
   - Danh sách lỗi (nếu có) — VD: `Row 145: he_so_quy_doi không khớp diem_cham/25`.
   - Preview 10 dòng đầu.
   - Nếu **có lỗi** → button "Commit" disabled. Sửa file Excel rồi upload lại.
   - Nếu **không lỗi** → click "Commit ✓".
4. **Bước 3 — Result**: hiển thị số đã insert / update / lỗi.

### 3.3 Strategy
- **Idempotent**: import lại cùng file → row đã có sẽ UPDATE thay vì INSERT trùng.
- **Atomic**: nếu commit fail giữa chừng → rollback toàn bộ.
- **Audit log**: mỗi lần import ghi 1 audit record với file hash + summary.
- **KHÔNG xóa** mục cũ không có trong file mới (admin tự deactivate nếu cần).

---

## 4. Pin phiên bản KPI

### 4.1 Khái niệm
- Hệ thống chạy song song V1 (cũ) và V2_PL3 (mới).
- Mỗi CC có 1 trong 3 trạng thái:
  - `kpi_version_pinned = NULL` → dùng default hệ thống (hiện tại = V2_PL3).
  - `kpi_version_pinned = 'V1'` → ép dùng V1.
  - `kpi_version_pinned = 'V2_PL3'` → ép dùng V2.

### 4.2 Pin theo đơn vị (bulk)
1. Vào `/admin/kpi-version`.
2. Section "Pin theo đơn vị":
   - Chọn đơn vị (vd: HQCK Móng Cái).
   - Chọn phiên bản (V1 / V2_PL3 / Default).
3. Click "Áp dụng cho tất cả CC" → toàn bộ CC trong đơn vị được pin theo lựa chọn.
4. Banner xanh xác nhận: `Đã set X/Y CC...`.

### 4.3 Pin theo cá nhân
1. Section "Pin theo cá nhân".
2. Search theo mã CC hoặc họ tên (cộng filter đơn vị nếu cần).
3. Bảng hiển thị CC + version pinned hiện tại.
4. Đổi dropdown ở cột "Hành động" → tự lưu ngay (Default / V1 / V2_PL3).

### 4.4 Use case UAT
- Pin 1-2 đơn vị thử V2_PL3 trong tháng kiểm thử.
- Các đơn vị khác giữ V1 (hoặc default).
- Đối chiếu KPI giữa 2 nhóm để verify công thức V2 chính xác.

### 4.5 Cutover toàn cụ (sau UAT)
Cutover bằng SQL (không có UI):
```sql
-- Đổi default toàn hệ thống V1 → V2_PL3
UPDATE public.platform_config
SET value = '"V2_PL3"'::jsonb,
    updated_at = NOW()
WHERE key = 'kpi_version_default';
```

Rollback (V2 → V1):
```sql
UPDATE public.platform_config
SET value = '"V1"'::jsonb,
    updated_at = NOW()
WHERE key = 'kpi_version_default';
```

Liên hệ devops khi cần chạy.

---

## 5. Xử lý lỗi thường gặp

### 5.1 `MIXED_VERSION_NOT_ALLOWED`
**Triệu chứng:** CC thử kê khai V2 nhưng tháng đó đã có bản V1.
**Nguyên nhân:** LOCKED 12 — 1 tháng = 1 version, không cho mix.
**Cách xử lý:**
- Yêu cầu CC chọn tháng khác.
- Hoặc TCCB xóa toàn bộ kê khai V1 trong tháng đó (nếu admin đồng ý) rồi CC mới tạo V2.

### 5.2 `INVALID_CATALOG_VERSION`
**Triệu chứng:** Modal V2 báo "Mục đã chọn không hợp lệ".
**Nguyên nhân:** Mục có `nguon_du_lieu='V1'` (mục cũ) nhưng dùng cho V2.
**Cách xử lý:** Refresh trang, chọn lại từ search PL3.

### 5.3 `V2_NO_OVERRIDE`
**Triệu chứng:** Lãnh đạo phê duyệt bị reject "không cho phép đổi cấp độ".
**Nguyên nhân:** LOCKED 14 — V2 không cho override hệ số. LĐ vô tình gửi `cap_do_ma`.
**Cách xử lý:** LĐ chỉ gửi action APPROVE/REJECT + số lỗi, không gửi `cap_do_ma`.

### 5.4 Mẫu số = 0 → KPI = 0
**Triệu chứng:** CC nhìn KPI tháng = 0, mức D.
**Nguyên nhân (LOCKED 5):** CC chưa kê khai bản nào hoặc tất cả bị từ chối.
**Cách xử lý:**
- Nếu CC nghỉ thai sản → admin set xếp loại tay sang **mức E** (không xếp loại).
- Nếu CC làm việc bình thường mà chưa kê → nhắc CC kê khai sớm.

### 5.5 Import Excel báo lỗi `he_so_quy_doi không khớp diem_cham/25`
**Triệu chứng:** Dry-run liệt kê 1 số row có sai số.
**Nguyên nhân:** Excel gốc có cell `he_so_quy_doi` lệch tolerance 0.05 so với `diem_cham/25`.
**Cách xử lý:** Sửa cell L trong file Excel (= cell K / 25), upload lại.

### 5.6 Import Excel báo `15 section headers not found`
**Triệu chứng:** Dry-run fail ngay với "Kỳ vọng 15 sections".
**Nguyên nhân:** File Excel không có đủ 15 section header dạng `I. ...`, `II. ...`, ..., `XV. ...` ở cột A.
**Cách xử lý:** Verify từng section có format đúng, không bị xóa nhầm.

---

## 6. Roles & permissions

| Role | Quyền |
|---|---|
| ADMIN | Toàn quyền: CRUD danh mục, import Excel, pin version |
| TCCB | (tùy cấu hình) — thường có quyền pin version, xem dashboard |
| CCT/PCCT | Xem báo cáo, không CRUD danh mục |
| CC | Chỉ kê khai (V1 hoặc V2 theo pin) |

---

## 7. Liên hệ

- Bug / lỗi system: dev team.
- Câu hỏi nghiệp vụ: TCCB.
- Cutover prod / SQL config: devops.

---

## Phụ lục: Định nghĩa 15 lĩnh vực PL3

| Mã | Tên |
|---|---|
| I | Công tác quản lý điều hành, hành chính, văn phòng |
| II | Hợp tác quốc tế |
| III | Công tác Đảng |
| IV | Tổ chức, cán bộ |
| V | Kiểm tra, PCTN, KNTC |
| VI | Tài vụ - Quản trị |
| VII | CNTT và thống kê hải quan |
| VIII | Đổi mới và chiến lược |
| IX | Pháp chế |
| X | Giám sát quản lý |
| XI | Thuế XNK |
| XII | Điều tra chống buôn lậu |
| XIII | Kiểm tra sau thông quan |
| XIV | Quản lý rủi ro |
| XV | Kiểm định |
