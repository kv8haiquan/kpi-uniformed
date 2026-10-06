# HƯỚNG DẪN SỬ DỤNG MODULE QUẢN TRỊ HỆ THỐNG

**Dành cho:** SUPER_ADMIN (Trưởng phòng CNTT, Quản trị viên hệ thống)  
**Địa chỉ truy cập:** https://kpihaiquan.vn → menu **Quản trị**  
**Phiên bản tài liệu:** 06/10/2026

---

## MỤC LỤC

1. [Tổng quan](#1-tổng-quan)
2. [Đăng nhập và kiểm tra quyền](#2-đăng-nhập-và-kiểm-tra-quyền)
3. [Quản lý tài khoản người dùng](#3-quản-lý-tài-khoản-người-dùng)
4. [Quản lý danh mục PL3](#4-quản-lý-danh-mục-pl3)
5. [Cấu hình platform role](#5-cấu-hình-platform-role)
6. [Điều chuyển nhân sự hàng loạt](#6-điều-chuyển-nhân-sự-hàng-loạt)
7. [Lịch sử điều chuyển](#7-lịch-sử-điều-chuyển)
8. [Xử lý sự cố thường gặp](#8-xử-lý-sự-cố-thường-gặp)

---

## 1. Tổng quan

Module Quản trị hệ thống cung cấp các công cụ quản lý tập trung cho toàn bộ Nền tảng số:

- **Quản lý tài khoản** — kích hoạt/vô hiệu hóa, reset mật khẩu, thêm/sửa/xóa người dùng
- **Quản lý danh mục PL3** — CRUD danh mục công việc KPI V2_PL3, import Excel
- **Vai trò nền tảng (platform role)** — **chưa có màn hình**; gán bằng SQL theo quy trình khẩn cấp (mục 5)
- **Điều chuyển nhân sự** — điều chuyển hàng loạt bằng Excel, lịch sử điều chuyển
- **Danh mục phiên bản cũ** — Quản lý Cấp độ (`/admin/cap-do`), Danh mục CV (`/admin/danh-muc-cv`), SP Chuẩn (`/admin/sp-chuan`) — còn giữ cho dữ liệu trước PL3

> ⚠️ **Chỉ tài khoản có cờ `is_system_admin = TRUE` mới truy cập được module này.** Người dùng thường bấm vào menu Quản trị sẽ bị chuyển về Dashboard.

---

## 2. Đăng nhập và kiểm tra quyền

| | |
|---|---|
| Tên đăng nhập | Mã công chức, ví dụ `ADMIN-001` (không phân biệt hoa/thường) |
| Mật khẩu | Mật khẩu quản trị đã được cấp (mặc định `123456` nếu là tài khoản mới, **phải đổi ngay**) |
| Vị trí menu | Thanh bên trái → **Quản trị** (mục cuối cùng) |

**Kiểm tra quyền:** Sau khi đăng nhập, nếu:
- **Thấy menu "Quản trị"** → có quyền admin (`is_system_admin=TRUE`)
- **Không thấy menu "Quản trị"** hoặc bấm vào bị chuyển về Dashboard → chưa có quyền, liên hệ quản trị viên cấp cao hơn để được gán cờ `is_system_admin=TRUE` trong bảng `public.cong_chuc`.

### Dashboard quản trị

Trang **"🔧 Quản trị Hệ thống"** (`/admin`) gồm:

- Các ô thống kê: **Tổng người dùng**, **User không hoạt động**, **Đơn vị**, **Số cấp độ**.
- Khối **"⚡ Thao tác nhanh"**: Quản lý Người dùng, Điều chuyển nhân sự, Điều chuyển hàng loạt, Reset mật khẩu, Quản lý Cấp độ, Danh mục Công việc, Quản lý SP Chuẩn.
- Khối **"ℹ️ Thông tin hệ thống"**: người dùng hiện tại, vai trò, phiên bản.

---

## 3. Quản lý tài khoản người dùng

Vào **Quản trị → Quản lý tài khoản**.

### 3.1. Xem danh sách

Bảng hiển thị: Mã CC · Họ tên · Email · Đơn vị · Vai trò · Chức vụ · Trạng thái · Thao tác.

**Bộ lọc** ở trên cùng:

- **Đơn vị** — lọc theo đơn vị (15 đơn vị)
- **Vai trò** — lọc theo vai trò (SUPER_ADMIN, CCT, PCCT, TDV, PDV, CC, TCCB)
- **Trạng thái** — Tất cả / Đang hoạt động / Đã vô hiệu hóa
- **Tìm kiếm** — tìm theo mã CC hoặc họ tên

Danh sách tự động sắp xếp theo chức vụ: Chi cục trưởng → Phó Chi cục trưởng → Trưởng đơn vị → Phó đơn vị → Công chức → Hợp đồng 111.

### 3.2. Thêm người dùng mới

Tại trang **"👥 Quản lý Người dùng"** (`/admin/users`), bấm nút **"Tạo mới"** → hộp thoại **"➕ Tạo người dùng mới"**.

| Trường | Bắt buộc | Ghi chú |
|---|:---:|---|
| **Mã công chức** | ✅ | Tối đa 20 ký tự, duy nhất, ví dụ `20ZZ-xxxx` |
| **Họ tên** | ✅ | Tối đa 100 ký tự |
| **Email** | | Tối đa 100 ký tự |
| **Số điện thoại** | | Tối đa 20 ký tự — **cần chính xác để nhận tin Zalo** (tính năng nhắc lịch công tác qua Zalo OA) |
| **Đơn vị** | ✅ | Chọn từ danh sách 15 đơn vị |
| **Vai trò** | ✅ | Chọn từ danh sách: SUPER_ADMIN, CCT, PCCT, TDV, PDV, CC, TCCB |
| **Chức vụ** | | Ví dụ "Công chức", "Đội trưởng", "Chánh Văn phòng" |
| **Lãnh đạo** | | Tích checkbox nếu là lãnh đạo |
| **Mật khẩu** | ✅ | **Tối thiểu 6 ký tự** (kiểm tra ở `ChangePasswordRequest.new_password` trong `auth.py`, line `min_length=6`) — người dùng nên đổi sau lần đầu đăng nhập |

Bấm **"Tạo"** → hệ thống tạo tài khoản và báo thành công.

### 3.3. Sửa thông tin người dùng

Bấm biểu tượng **✏️** ở cột Thao tác. Modal hiển thị form tương tự form thêm mới.

**Không sửa được:** Mã CC (đã khóa để giữ FK).

Bấm **"Cập nhật"** → hệ thống lưu và ghi nhật ký thay đổi.

### 3.4. Vô hiệu hóa / Kích hoạt

Ở cột Trạng thái, bấm:

- **Nút đỏ "Vô hiệu hóa"** — khóa tài khoản, người dùng không đăng nhập được nữa
- **Nút xanh "Kích hoạt"** — mở khóa tài khoản

Hệ thống hỏi xác nhận trước khi thực hiện.

> **Lưu ý:** 
- Vô hiệu hóa tài khoản **không xóa dữ liệu** — kê khai KPI, nhiệm vụ HKG, tiến độ học LMS của người đó vẫn giữ nguyên.
- Tài khoản **`ADMIN-001`** là tài khoản admin gốc, được bảo vệ — **không được phép** vô hiệu hóa, xóa hoặc điều chuyển (xem `PROTECTED_ADMIN_MA_CC` trong `admin.py` line 78).

### 3.5. Reset mật khẩu

Bấm biểu tượng **🔑** (hoặc nút "Reset mật khẩu") ở cột Thao tác → hệ thống hỏi xác nhận → hệ thống đặt lại mật khẩu về **`123456`** (xem `DEFAULT_PASSWORD` trong `backend/app/api/v1/endpoints/admin.py` line 81).

Báo người dùng đăng nhập bằng mật khẩu mới và **đổi ngay** sau khi vào hệ thống. Mật khẩu mới phải có **tối thiểu 6 ký tự** (kiểm tra ở `ChangePasswordRequest.new_password`, `min_length=6`).

### 3.6. Điều chuyển cá nhân

Bấm biểu tượng **🔄** ở cột Thao tác.

| Trường | Bắt buộc | Ghi chú |
|---|:---:|---|
| **Đơn vị mới** | ✅ | Chọn từ danh sách |
| **Vai trò mới**, **Chức vụ mới** | | Mặc định "-- Giữ nguyên --" |
| **Ngày hiệu lực** | ✅ | Ngày theo quyết định — **ảnh hưởng đến báo cáo KPI tháng** (bắt buộc nhập, không tự lấy ngày hôm nay) |
| **Lý do điều chuyển** | | Ghi số QĐ vào đây nếu có (hộp thoại điều chuyển từng người không có ô Số QĐ riêng) |

Bấm **"Điều chuyển"** → hệ thống ghi nhật ký và cập nhật đơn vị hiện tại.

> ⚠️ **Quan trọng:** Ngày điều chuyển quyết định đơn vị nào tính KPI cho công chức trong tháng đó. Xem mục 7 để biết cách xử lý điều chuyển giữa tháng.

---

## 4. Quản lý danh mục PL3

Vào **Quản trị → Danh mục PL3**.

### 4.1. Xem danh sách

Bảng hiển thị: Mã danh mục · Tên công việc · Lĩnh vực · Nhóm · Điểm chấm · Hệ số · Trạng thái.

**Bộ lọc:**

- **Lĩnh vực** — I đến XV (15 lĩnh vực theo Phụ lục 3 Thông tư 07/2025)
- **Nhóm** — Nhóm 1 đến Nhóm 5
- **Tìm kiếm** — tìm theo mã hoặc tên công việc

Danh sách phân trang, mỗi trang 50 mục.

### 4.2. Thêm mục mới

Bấm nút **"Thêm mục"**.

| Trường | Bắt buộc | Ghi chú |
|---|:---:|---|
| **Mã danh mục** | ✅ | Format `PL3-{lĩnh vực}-{stt}`, ví dụ `PL3-I-CUSTOM-001`. Tối đa 30 ký tự, duy nhất. |
| **Tên công việc** | ✅ | 3-500 ký tự |
| **Lĩnh vực** | ✅ | Chọn 1 trong 15 |
| **Nhóm** | ✅ | 1-5 |
| **Điểm chấm** | ✅ | Số nguyên 1-500, không vượt khung của nhóm |

Hệ thống **tự tính:**

- `Khung điểm tối đa` = 100/200/300/400/500 (theo nhóm)
- `Hệ số quy đổi` = `Điểm chấm / 25`

Nếu điểm chấm vượt khung, hệ thống báo lỗi đỏ.

Bấm **"Lưu"** → mục mới xuất hiện trong danh sách.

### 4.3. Sửa mục

Bấm biểu tượng **✏️** ở cột Thao tác.

**Không sửa được:** Mã danh mục (đã khóa để giữ FK).

Bấm **"Lưu"** → hệ thống ghi nhật ký thay đổi.

### 4.4. Vô hiệu hóa mục

Bấm biểu tượng **🚫** ở cột Thao tác → hệ thống hỏi xác nhận.

Mục chuyển sang `is_active=FALSE`, không còn hiện cho công chức chọn khi kê khai mới.

> **Lưu ý:** Bản kê khai cũ vẫn dùng snapshot — **không bị ảnh hưởng**.

### 4.5. Import Excel danh mục PL3

Khi Bộ Nội vụ ban hành sửa đổi PL3, admin có thể import file Excel mới mà không cần dev migration.

#### Bước 1 — Chuẩn bị file

- File `.xlsx` (≤ 10MB)
- Sheet tên `PL3`
- Cột bắt buộc:
  - A: Stt
  - B: Nhiệm vụ (optional)
  - C: Công việc chi tiết (bắt buộc)
  - D: Sản phẩm đầu ra (bắt buộc)
  - E: Phân nhóm ("Nhóm 1"..."Nhóm 5")
  - F: Khung điểm tối đa (100/200/300/400/500)
  - K: Điểm chấm
  - L: Hệ số quy đổi (= K/25)
- Section header định dạng: `I. Tên lĩnh vực`, `II. Tên`, ... (15 lĩnh vực)

#### Bước 2 — Upload

Bấm nút **"Import Excel"** → chọn file → bấm **"Tiếp →"**.

#### Bước 3 — Preview

Hệ thống dry-run, hiển thị:

- Tổng dòng / hợp lệ / lỗi / sẽ insert / sẽ update
- Danh sách lỗi (nếu có) — VD: `Row 145: he_so_quy_doi không khớp diem_cham/25`
- Preview 10 dòng đầu

Nếu **có lỗi** → button "Commit" disabled. Sửa file Excel rồi upload lại.

Nếu **không lỗi** → bấm **"Commit ✓"**.

#### Bước 4 — Result

Hiển thị số đã insert / update / lỗi.

> **Strategy:** Import lại cùng file → row đã có sẽ UPDATE thay vì INSERT trùng. Atomic: nếu commit fail giữa chừng → rollback toàn bộ.

---

## 5. Cấu hình platform role

Vào **Quản trị → Platform Roles** (hoặc tìm trong quick actions). **Chức năng này chưa có giao diện** — hiện tại phải gán platform role qua SQL hoặc qua endpoint API (nếu có).

### 5.1. Khái niệm

Platform role là vai trò bổ sung cho các module mới (LMS, Forum, Legal, Portal, HKG, Chỉ tiêu), lưu trong bảng `public.platform_role` và gán cho công chức qua bảng `public.cong_chuc_platform_role`.

**Danh sách platform role thật sự tồn tại trong DB** (xác minh từ các migration production):

| ma_role | Tên | Module | Nguồn seed | Trạng thái |
|---------|-----|--------|------------|------------|
| GIANG_VIEN | Giảng viên kiêm nhiệm | LMS | add_platform_tables_20260220.py | ✅ Đã seed |
| QT_DAO_TAO | Quản trị đào tạo | LMS | add_platform_tables_20260220.py | ✅ Đã seed |
| BIEN_TAP | Biên tập viên | Legal, Portal | add_platform_tables_20260220.py | ✅ Đã seed |
| DIEU_PHOI_FORUM | Điều phối diễn đàn | Forum | add_platform_tables_20260220.py | ✅ Đã seed |
| CHUYEN_GIA | Chuyên gia nghiệp vụ | Forum | add_platform_tables_20260220.py | ✅ Đã seed |
| QT_NOI_DUNG | Quản trị nội dung | Portal | add_platform_tables_20260220.py | ✅ Đã seed |
| QT_ATTT | Quản trị ATTT | ALL | add_platform_tables_20260220.py | ✅ Đã seed |
| THU_KY_HOP | Thư ký cuộc họp | HKG | meeting_011_seed_platform_roles_20260430.py | ✅ Đã seed |
| CHANH_VP | Chánh Văn phòng | HKG | meeting_011_seed_platform_roles_20260430.py | ✅ Đã seed (7 người được gán 26/08) |
| TRUONG_CNTT | Trưởng phòng CNTT | HKG | meeting_011_seed_platform_roles_20260430.py | ✅ Đã seed |
| DANG_VIEN | Đảng viên | HKG (họp Đảng) | meeting_011_seed_platform_roles_20260430.py | ✅ Đã seed |
| BI_THU_CHI_BO | Bí thư Chi bộ | HKG (họp Đảng) | meeting_011_seed_platform_roles_20260430.py | ✅ Đã seed |
| PHO_BI_THU | Phó Bí thư Chi bộ | HKG (họp Đảng) | meeting_011_seed_platform_roles_20260430.py | ✅ Đã seed |
| QT_CHI_TIEU | Quản trị chỉ tiêu | Chỉ tiêu | create_chi_tieu_schema_20260604.py | ✅ Đã seed (chưa rõ số người được gán) |
| THEO_DOI_CHI_TIEU | Người theo dõi chỉ tiêu | Chỉ tiêu | create_chi_tieu_schema_20260604.py | ✅ Đã seed (chưa rõ số người được gán) |

**Lưu ý:** Trong bảng trên, **chưa rõ** có bao nhiêu người thật sự được gán mỗi role. Admin cần kiểm tra bảng `public.cong_chuc_platform_role` để biết ai có role gì.

### 5.2. Gán platform role (hiện chưa có giao diện)

**Tính năng này được mô tả trong HDSD nhưng chưa được triển khai đầy đủ ở frontend.** Hiện tại phải gán platform role bằng một trong hai cách:

**Cách 1 — SQL trực tiếp** (chỉ dùng trong trường hợp khẩn cấp, phải có quyền truy cập DB):

```sql
-- Tìm id của role
SELECT id, ma_role, ten_role FROM public.platform_role WHERE ma_role = 'CHANH_VP';

-- Tìm id của công chức
SELECT id, ma_cc, ho_ten FROM public.cong_chuc WHERE ma_cc = '20ZZ-xxxx';

-- Gán role
INSERT INTO public.cong_chuc_platform_role (cong_chuc_id, platform_role_id, is_active)
VALUES ('<uuid công chức>', '<uuid role>', TRUE)
ON CONFLICT (cong_chuc_id, platform_role_id) DO UPDATE SET is_active = TRUE;
```

**Không có endpoint API gán vai trò nền tảng** (kiểm tra backend production 06/10/2026). Thao tác gán/gỡ chỉ thực hiện được bằng SQL ở trên, do quản trị hệ thống làm trên DB production — bắt buộc bọc `BEGIN … COMMIT`, kiểm tra số dòng, thử trước trên `kpi_haiquan_test`. Đây là khoảng trống đã ghi nhận (đề xuất bổ sung màn hình gán vai trò có ghi nhật ký).

**Lưu ý:** Người dùng cần **đăng xuất và đăng nhập lại** để role mới có hiệu lực (JWT token cũ không chứa `platform_roles` mới).

### 5.3. Gỡ platform role (hiện chưa có giao diện)

Hiện chưa có giao diện. Phải gỡ bằng SQL:

```sql
DELETE FROM public.cong_chuc_platform_role
WHERE cong_chuc_id = '<uuid công chức>'
  AND platform_role_id = (SELECT id FROM public.platform_role WHERE ma_role = 'CHANH_VP');
```

Hoặc chỉ vô hiệu hóa (soft delete):

```sql
UPDATE public.cong_chuc_platform_role
SET is_active = FALSE
WHERE cong_chuc_id = '<uuid công chức>'
  AND platform_role_id = (SELECT id FROM public.platform_role WHERE ma_role = 'CHANH_VP');
```

---

## 6. Điều chuyển nhân sự hàng loạt

Vào **Quản trị → Điều chuyển hàng loạt**.

### 6.1. Tải mẫu Excel

Bấm nút **"⬇ Tải file mẫu"** → file gồm 4 sheet:

| Sheet | Nội dung |
|---|---|
| **Nhap lieu** | Sheet TRỐNG để admin điền — 4 cột: Mã CC, Đơn vị đến, Ngày hiệu lực, Số QĐ |
| **Danh sach cong chuc** | Danh sách đầy đủ mã CC + họ tên + đơn vị hiện tại |
| **Ma don vi** | Danh sách 15 đơn vị + mã đơn vị |
| **Huong dan** | Quy tắc điền file |

### 6.2. Điền file

Sheet **Nhap lieu** có 4 cột (`app/core/dieu_chuyen_excel.py`):

| Cột | Bắt buộc | Ví dụ |
|---|:---:|---|
| A: Mã CC | ✅ | `20ZZ-xxxx` |
| B: Đơn vị đến | ✅ | mã đơn vị, tra ở sheet `Ma don vi` |
| C: Ngày hiệu lực | ✅ | ngày theo quyết định |
| D: Số QĐ | | `1234/QĐ-HQKV8` |

**Lưu ý:**

- Khóa là **Mã CC**, không phải họ tên
- Mã đơn vị tra ở sheet `Ma don vi`
- Một dòng lỗi → từ chối cả đợt

### 6.3. Upload

Bấm nút **"Import Excel"** → chọn file → bấm **"Tiếp →"**.

Hệ thống dry-run, hiển thị:

- Tổng dòng / hợp lệ / lỗi
- Danh sách lỗi (nếu có)
- Preview 10 dòng đầu

Nếu có lỗi → button "Commit" disabled. Sửa file rồi upload lại.

Nếu không lỗi → bấm **"Commit ✓"**.

### 6.4. Kết quả

Hệ thống hiển thị số đã điều chuyển thành công / lỗi.

Mỗi lần import ghi 1 audit record với file hash + summary.

---

## 7. Lịch sử điều chuyển

Vào **Quản trị → Lịch sử điều chuyển**.

### 7.1. Xem lịch sử

Trang "🔄 Lịch sử điều chuyển & trạng thái" hiển thị các cột: Công chức · Loại · Nội dung · Ngày hiệu lực · Lý do · Người thực hiện · Thao tác ("Sửa ngày hiệu lực").

**Bộ lọc:**

- **Công chức** — tìm theo mã CC hoặc họ tên
- **Loại** — "-- Tất cả loại --" / Điều chuyển / Vô hiệu hóa / Kích hoạt

### 7.2. Loại sự kiện

| Loại | Ý nghĩa |
|---|---|
| **Điều chuyển** | Chuyển từ đơn vị A sang đơn vị B |
| **Vô hiệu hóa** | Ngưng hoạt động (nghỉ việc, nghỉ thai sản) |
| **Kích hoạt** | Kích hoạt lại sau khi vô hiệu hóa |

### 7.3. Xuất dữ liệu

Trang lịch sử điều chuyển **chưa có nút xuất Excel**. Danh sách người dùng xuất được tại `/admin/users`.

---

## 8. Xử lý sự cố thường gặp

| Hiện tượng | Nguyên nhân | Cách xử lý |
|---|---|---|
| Không thấy menu "Quản trị" | Chưa có cờ `is_system_admin=TRUE` trong bảng `cong_chuc` | Liên hệ quản trị viên cấp cao hơn để gán quyền |
| Import Excel báo "15 section headers not found" | File PL3 không có đủ 15 section header `I. ...`, `II. ...`, ..., `XV. ...` | Verify từng section có format đúng, không thiếu section |
| Import Excel báo `he_so_quy_doi không khớp diem_cham/25` | Cell `he_so_quy_doi` lệch tolerance 0.05 so với `diem_cham/25` | Sửa cell L = cell K / 25, upload lại |
| Điều chuyển hàng loạt báo lỗi "Mã CC không tồn tại" | Mã CC sai hoặc chưa có trong hệ thống, hoặc người đã nghỉ việc | Kiểm tra lại sheet "Danh sach cong chuc" trong file mẫu — chỉ copy mã CC từ đó |
| Platform role gán rồi nhưng không có quyền | Chưa đăng xuất và đăng nhập lại — JWT token cũ không chứa `platform_roles` mới | Yêu cầu người dùng logout (`/ho-so` → Đăng xuất) và login lại |
| Reset mật khẩu nhưng vẫn không đăng nhập được | Tài khoản bị vô hiệu hóa (`is_active=FALSE`) — reset mật khẩu không tự động kích hoạt tài khoản | Kiểm tra cột Trạng thái, bấm "Kích hoạt" riêng |
| Đăng nhập bị chặn "Tài khoản tạm khóa do nhập sai mật khẩu quá nhiều lần" | Đã nhập sai mật khẩu 10 lần liên tiếp → khóa tạm 15 phút (xem `MAX_FAILED_ATTEMPTS` và `LOCKOUT_SECONDS` trong `login_protection.py`) | Đợi 15 phút hoặc admin reset mật khẩu (reset KHÔNG xóa bộ đếm khóa tạm — người dùng vẫn phải đợi hết 15 phút) |

---

## Phụ lục A: Định nghĩa 15 lĩnh vực PL3

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

---

*Tài liệu biên soạn ngày 06/10/2026 theo phiên bản phần mềm đang chạy production.*
