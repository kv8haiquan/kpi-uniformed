# HƯỚNG DẪN SỬ DỤNG — DÀNH CHO TCCB

**Đối tượng:** Cán bộ Tổ chức Cán bộ (TCCB) — 3-5 người  
**Phiên bản:** Tháng 10/2026

---

## MỤC LỤC

1. [Tổng quan vai trò và quyền hạn](#1-tổng-quan-vai-trò-và-quyền-hạn)
2. [Đối soát đánh giá](#2-đối-soát-đánh-giá)
3. [Điều chuyển đơn vị (từng người)](#3-điều-chuyển-đơn-vị-từng-người)
4. [Điều chuyển hàng loạt bằng Excel](#4-điều-chuyển-hàng-loạt-bằng-excel)
5. [In bảng kê và xuất báo cáo](#5-in-bảng-kê-và-xuất-báo-cáo)
6. [Tổng hợp phiếu Mẫu 02 toàn Chi cục](#6-tổng-hợp-phiếu-mẫu-02-toàn-chi-cục)
7. [Quản lý tài khoản](#7-quản-lý-tài-khoản)
8. [Lỗi thường gặp](#8-lỗi-thường-gặp)

---

## 1. Tổng quan vai trò và quyền hạn

### 1.1. Vai trò của TCCB

TCCB là **vai trò platform** (không phải vai trò nghiệp vụ như TDV/CCT), có quyền:

- **Xem toàn bộ dữ liệu** của toàn Chi cục (như CCT)
- **Đối soát đánh giá:** Kiểm tra ai/đơn vị nào chưa hoàn tất quy trình
- **Điều chuyển đơn vị:** Cập nhật khi có quyết định điều động nhân sự
- **Quản lý tài khoản:** Kích hoạt/vô hiệu, reset mật khẩu
- **In bảng kê, xuất báo cáo:** Tổng hợp hồ sơ nộp lên Cục
- **Tổng hợp phiếu Mẫu 02:** Xem phiếu đánh giá toàn Chi cục (cùng quyền với CCT/PCCT)

**Lưu ý quan trọng:** TCCB **KHÔNG có quyền duyệt** kê khai, tiêu chí chung, xếp loại. TCCB chỉ **xem, đối soát, tổng hợp, hỗ trợ kỹ thuật**. TCCB không phải vai trò nghiệp vụ (như TDV/CCT) mà là **vai trò hệ thống** được gán qua cờ `ma_vai_tro='TCCB'` trong bảng `public.vai_tro`.

### 1.2. Đường dẫn chính

Sau khi đăng nhập, thanh bên trái hiển thị các menu:

- **Đối soát đánh giá** → `/doi-soat` (mục KPI)
- **Tổng hợp phiếu 02** → `/phieu-tong-hop` (mục KPI)
- **Quản trị → Quản lý tài khoản** (mục Quản trị, chia sẻ với Admin)
- **Quản trị → Điều chuyển đơn vị** (mục Quản trị)
- **Quản trị → Điều chuyển hàng loạt** (mục Quản trị)

*(ảnh minh họa bổ sung khi in)*

---

## 2. Đối soát đánh giá

### 2.1. Mục đích

Kiểm tra danh sách công chức **chưa hoàn tất** kê khai/duyệt — để nhắc đơn vị xử lý trước khi chốt (hạn 23 tháng cuối quý).

**Lưu ý từ Q3/2026:** Dù kỳ đánh giá đã chuyển sang quý, trang **Đối soát** hiện vẫn theo **THÁNG**. Cần kiểm tra **3 tháng** của quý để đối soát đầy đủ.

### 2.2. Ai dùng

Các vai trò sau thấy menu "Đối soát đánh giá":
- TCCB (`ma_vai_tro='TCCB'`)
- CCT, PCCT (`ma_vai_tro='CCT'` hoặc `'PCCT'`)
- Tài khoản có cờ `is_system_admin=TRUE` (Admin)
- Tài khoản có cờ `can_view_all_units=TRUE` (hiếm, chủ yếu dùng cho Admin)

### 2.3. Đường dẫn

Dashboard → Thanh bên trái (mục KPI) → **Đối soát đánh giá** (`/doi-soat`)

### 2.4. Các bước

**Bước 1: Chọn tháng, năm**

- **Lưu ý:** Từ Q3/2026, chọn **tháng cuối quý** (T3, T6, T9, T12) để đối soát kỳ đó
- Ví dụ: Đối soát Quý III/2026 → chọn **Tháng 9/2026**

**Bước 2: Bấm nút "Tải lại" (hoặc icon làm mới)**

Hệ thống tải dữ liệu, thời gian ~1-2 giây. Nếu chưa chọn tháng/năm thì nút này sẽ bị vô hiệu hóa.

**Bước 3: Xem tổng hợp**

Phần đầu hiển thị 6 nhóm (tên nhóm lấy từ `doi_soat_danh_gia.py`, mức ưu tiên Cao/Trung bình/Thấp):

| Nhóm | Ý nghĩa | Mức độ |
|------|---------|--------|
| **Công chức chưa kê khai công việc** | CC chưa gửi duyệt kê khai công việc | 🔴 Cao |
| **HĐ 111 chưa kê khai VB714** | Hợp đồng 111 chưa kê khai | 🟡 Trung bình |
| **HĐ 111 — VB714 chờ duyệt** | Hợp đồng 111 đã kê khai, chờ duyệt | 🟡 Trung bình |
| **Chưa kê khai tiêu chí chung** | CC chưa tự chấm tiêu chí chung | 🔴 Cao |
| **Tiêu chí chung — chờ duyệt** | Đã tự chấm, chờ lãnh đạo duyệt | 🟡 Trung bình |
| **Điểm 0 chưa rõ nguyên nhân (lưới an toàn)** | Có điểm = 0 nhưng không thuộc nhóm nào ở trên | ⚪ Thấp (cần kiểm tra) |

**Bước 4: Xem chi tiết từng nhóm**

- Bấm vào nhóm (ví dụ: "Công chức chưa kê khai công việc")
- Bảng hiển thị danh sách công chức:
  - Mã công chức, họ tên
  - Đơn vị
  - **Chi tiết** (mô tả cụ thể vấn đề)

**Bước 5: Xuất Excel**

- Bấm nút **"Xuất Excel"** (góc trên bên phải)
- File Excel chứa:
  - Sheet 1: Tổng hợp 6 nhóm (số lượng)
  - Sheet 2: Danh sách chi tiết từng người (phẳng, dễ filter)

**Bước 6: Nhắc đơn vị xử lý**

- Gửi danh sách cho **Trưởng đơn vị** liên quan
- Theo dõi đến khi **tổng số ca = 0** (hoàn tất)

### 2.5. Lưu ý nghiệp vụ

- **Mỗi công chức chỉ vào ĐÚNG 1 nhóm** (không trùng lặp).
- **Nhóm ưu tiên cao hơn** (chưa kê khai) sẽ "che" nhóm thấp hơn (chờ duyệt).
- Nhóm **"Điểm 0 chưa rõ nguyên nhân"** là nhóm **dự phòng** — chứa ca ngoại lệ cần kiểm tra thủ công.
- Trang đối soát hiện **theo tháng** (tiêu đề "Đối soát hoàn thành đánh giá tháng", chưa có chế độ theo quý) — cần kiểm tra 3 tháng riêng lẻ.

---

## 3. Điều chuyển đơn vị (từng người)

### 3.1. Mục đích

Cập nhật đơn vị công tác của công chức khi có **Quyết định điều động**.

### 3.2. Ai dùng

Chỉ TCCB hoặc Admin (`is_system_admin=TRUE`). Endpoint backend yêu cầu quyền Admin.

### 3.3. Đường dẫn

**Không có menu riêng.** Tính năng này nằm trong trang **Quản trị → Quản lý tài khoản** → cột "Thao tác" của từng công chức có biểu tượng **🔄 Điều chuyển**.

### 3.4. Các bước

**Bước 1: Tìm công chức**

- Nhập **mã công chức** hoặc **họ tên** vào ô tìm kiếm
- Hoặc lọc theo **Đơn vị hiện tại**

**Bước 2: Bấm "Điều chuyển"**

- Bấm nút **"Điều chuyển"** ở dòng công chức cần chuyển

**Bước 3: Nhập thông tin**

Modal (cửa sổ pop-up) hiển thị:
- **Đơn vị đến:** Chọn từ dropdown (15 đơn vị)
- **Ngày hiệu lực:** Ngày bắt đầu công tác tại đơn vị mới (quan trọng)
- **Số Quyết định:** Số QĐ điều động (không bắt buộc, nhưng nên điền)

**Bước 4: Xác nhận**

- Bấm **"Xác nhận"**
- Hệ thống tự:
  - Cập nhật `cong_chuc.don_vi_id`
  - Ghi lịch sử vào `lich_su_dieu_chuyen`
  - Khóa đánh giá tháng cũ (nếu đang mở) của đơn vị cũ
  - **Xóa mềm kê khai nháp** (trạng thái NHAP) của đơn vị cũ
  - Gỡ khỏi báo cáo chưa duyệt của đơn vị cũ
  - (Nguồn: `app/core/dieu_chuyen.py`, dùng chung cho điều chuyển từng người và hàng loạt)

**Bước 5: Kiểm tra**

- Vào trang **Lịch sử điều chuyển** (tab bên cạnh) để xem lịch sử
- Đảm bảo **ngày hiệu lực** chính xác

### 3.5. Hệ quả của việc điều chuyển

| Dữ liệu | Hệ quả |
|---------|--------|
| Kê khai công việc (tháng cũ) | Nháp → Xóa mềm; Đã gửi/Đã duyệt → Giữ nguyên, lãnh đạo đơn vị cũ duyệt |
| Kê khai công việc (tháng mới) | Kê khai tại đơn vị mới, lãnh đạo đơn vị mới duyệt |
| **Tiêu chí chung (quý)** | **Theo đơn vị tại thời điểm kê khai tiêu chí** (thường là tháng cuối quý) |
| **Báo cáo xếp loại** | **Tính theo đơn vị tại tháng cuối quý** |
| **Duyệt kê khai** | Dựa vào ngày hiệu lực: trước ngày chuyển → LĐ cũ duyệt; sau ngày chuyển → LĐ mới duyệt |

**Lưu ý:**

- **Ngày hiệu lực** rất quan trọng — sai ngày sẽ dẫn đến sai người duyệt.
- **Không điều chuyển nếu chưa có QĐ chính thức.**

---

## 4. Điều chuyển hàng loạt bằng Excel

### 4.1. Mục đích

Điều chuyển **nhiều người cùng lúc** theo một Quyết định điều động — tiết kiệm thời gian, giảm sai sót.

**Bài học 2026:** Các đợt điều động 04/02, 15/5, 03/7/2026 bỏ quên trọn 62 người khi nhập tay từng người một. Import Excel giúp **không bỏ sót**.

### 4.2. Ai dùng

Chỉ Admin (`is_system_admin=TRUE`). Endpoint backend yêu cầu quyền Admin. TCCB không có quyền truy cập trang này (code frontend kiểm tra `user.is_system_admin`).

### 4.3. Đường dẫn

Dashboard → **Quản trị** → **Điều chuyển hàng loạt** (`/admin/dieu-chuyen-hang-loat`)

**Lưu ý:** Nếu TCCB cố truy cập URL này, sẽ bị chuyển hướng về `/dashboard`.

### 4.4. Các bước

**Bước 1 — Tải file mẫu**

1. Bấm nút **"⬇ Tải file mẫu"**
2. File mẫu có **4 sheet:**

| Sheet | Nội dung | Ghi chú |
|-------|----------|---------|
| **Nhap lieu** | Sheet điền dữ liệu — **ĐỂ TRỐNG** (không có dữ liệu mẫu) | 4 cột: Mã CC, Đơn vị đến, Ngày hiệu lực, Số QĐ |
| **Huong dan** | Hướng dẫn + Ví dụ | Đọc trước khi điền |
| **Danh sach cong chuc** (hoặc **2. Tra cứu Mã CC**) | ~543 công chức còn hoạt động (lọc bỏ người đã nghỉ + ADMIN-001) | Copy mã CC từ đây |
| **Ma don vi** (hoặc **3. Tra cứu Mã ĐV**) | 15 đơn vị + mã đơn vị | Để tra cứu |

**Bước 2: Điền dữ liệu vào sheet "Nhap lieu"**

**Cột A — Mã công chức (bắt buộc):**
- Copy **Mã CC** từ sheet "Danh sach cong chuc"
- **Không gõ tay** (dễ sai) — phải copy từ sheet tra cứu
- Ví dụ: `20ZZ-xxxx`

**Cột B — Đơn vị đến (bắt buộc):**
- Chọn từ **dropdown** (15 đơn vị)
- Hoặc gõ **chính xác tên đơn vị** như trong sheet "Ma don vi"
- Ví dụ: `Đội Nghiệp vụ 1`

**Cột C — Ngày hiệu lực (bắt buộc):**
- Định dạng: **DD/MM/YYYY** (ví dụ: `01/04/2026`)
- Một dòng một ngày → một file có thể chứa **nhiều đợt** (nếu ngày khác nhau)

**Cột D — Số Quyết định (không bắt buộc):**
- Số QĐ điều động (ví dụ: `123/QĐ-CCT`)
- Nên điền để lưu trữ

**Lưu ý quan trọng:**

- **Khoá là Mã CC, KHÔNG phải họ tên** — khớp tên đã hỏng ở đợt 2026.
- **Xóa dòng tiêu đề (hàng 1)** nếu sao chép từ sheet khác — nếu không hệ thống sẽ báo lỗi "Không tìm thấy công chức".

**Bước 3: Lưu file**

- Lưu file Excel (định dạng `.xlsx`)
- Đặt tên rõ ràng: `Dieu_chuyen_QD123_01042026.xlsx`

**Bước 4: Upload file**

1. Quay lại trang **Điều chuyển hàng loạt**
2. Bấm **"Chọn file"** hoặc kéo thả file vào khung
3. Bấm **"Xem trước"**

**Bước 5: Xem trước**

Hệ thống hiển thị bảng xem trước:
- Mã CC
- **Họ tên** (hệ thống tự lấy từ DB — để kiểm tra mã CC có đúng không)
- **Đơn vị hiện tại** (để so sánh với đơn vị đến)
- Đơn vị đến
- Ngày hiệu lực
- Số QĐ
- **Trạng thái** (Hợp lệ / Lỗi)

**Nếu có lỗi:**
- Dòng lỗi hiển thị **màu đỏ**, cột "Trạng thái" ghi rõ lý do:
  - "Không tìm thấy công chức với mã ..."
  - "Đơn vị đến không hợp lệ"
  - "Ngày hiệu lực không đúng định dạng"
  - "Công chức đã ở đơn vị này rồi"
- **Một dòng lỗi → từ chối cả đợt** (không ghi một nửa)
- Sửa file Excel, upload lại

**Nếu hợp lệ:**
- Tất cả dòng màu xanh, "Trạng thái: Hợp lệ"
- Kiểm tra kỹ **Họ tên, Đơn vị hiện tại** có đúng không

**Bước 6: Xác nhận ghi**

1. Ở "Bước 3 — Đối chiếu rồi xác nhận", bấm nút **"Xác nhận điều chuyển N người"** (N = số dòng "Sẽ ghi"; nút bị khóa nếu còn dòng lỗi)
2. Hệ thống xử lý (nút hiện "Đang ghi...")
3. Kiểm tra kết quả tại **Lịch sử điều chuyển** (`/admin/lich-su-dieu-chuyen`)

**Bước 7: Kiểm tra**

- Vào trang **Lịch sử điều chuyển** để xem lịch sử
- Hoặc vào trang **Danh sách công chức** để kiểm tra đơn vị mới

### 4.5. Lưu ý nghiệp vụ

- **Một dòng một ngày hiệu lực:** Một file có thể chứa nhiều đợt (nếu ngày khác nhau).
- **Một dòng lỗi → từ chối cả đợt:** Không ghi một nửa.
- **Idempotent:** Upload cùng một file nhiều lần → chỉ ghi một lần (hệ thống kiểm tra trùng lặp).
- **Sheet tra cứu lọc bỏ người đã nghỉ** + `ADMIN-001` (tài khoản quản trị).

### 4.6. Lỗi thường gặp khi import

| Lỗi | Nguyên nhân | Cách sửa |
|-----|-------------|----------|
| "Không tìm thấy công chức với mã ..." | Gõ sai mã CC, hoặc người đã nghỉ việc | Copy mã CC từ sheet "Danh sach cong chuc" |
| "Đơn vị đến không hợp lệ" | Gõ sai tên đơn vị, hoặc chọn sai dropdown | Copy tên đơn vị từ sheet "Ma don vi" |
| "Ngày hiệu lực không đúng định dạng" | Ngày không đúng DD/MM/YYYY, hoặc ô định dạng Text | Đổi định dạng ô thành Date |
| "Công chức đã ở đơn vị này rồi" | Điều chuyển về đúng đơn vị hiện tại | Xóa dòng này khỏi file |
| "File không đúng định dạng" | File không phải .xlsx, hoặc thiếu sheet "Nhap lieu" | Kiểm tra file, tải lại mẫu |

---

## 5. In bảng kê và xuất báo cáo

### 5.1. In bảng kê (Mẫu 05)

**Mục đích:** In bảng kê kết quả xếp loại quý (Mẫu 05) — dùng khi nộp hồ sơ lên Cục.

**Đường dẫn:** không có menu "Báo cáo" riêng. Báo cáo nằm ở:

| Nơi xem | Nội dung | Xuất file |
|---------|----------|-----------|
| **Xếp loại** (`/xep-loai`, các tab báo cáo / quý) | Báo cáo xếp loại theo đơn vị, theo quý | Excel (`/api/v1/export/...`), Word/Excel qua in bảng kê |
| **Tổng hợp phiếu 02** (`/phieu-tong-hop`) | Phiếu Mẫu 02 toàn Chi cục, chỉ đọc | "Tải phiếu Mẫu 02", "Tải bảng kê công việc" |
| **Đối soát đánh giá** (`/doi-soat`) | Danh sách chưa hoàn tất | "Xuất Excel" |

**Lưu ý:** báo cáo theo lĩnh vực, báo cáo xu hướng giữa các quý **chưa có** trên hệ thống — cần thì xuất Excel rồi tổng hợp ngoài.

---

## 6. Tổng hợp phiếu Mẫu 02 toàn Chi cục

**Đường dẫn:** Dashboard → Thanh bên trái (mục KPI) → **Tổng hợp phiếu 02** (`/phieu-tong-hop`)

**Quyền:** TCCB, CCT, PCCT, Admin (`is_system_admin`), hoặc tài khoản có cờ `can_view_all_units=TRUE` (cùng nhóm quyền với Đối soát đánh giá).

**Chức năng:** Xem danh sách toàn bộ phiếu đánh giá quý (Mẫu 02A/02B) của toàn Chi cục — để tổng hợp hồ sơ nộp lên Cục (hạn 23 tháng cuối quý).

**Chi tiết:** Xem mục tương ứng trong `03_lanh_dao_chi_cuc.md`, mục 6 (chức năng giống hệt).

**Lưu ý quan trọng:** 
- Trang này **CHỈ ĐỌC** — không duyệt, không sửa phiếu.
- **Trưởng đơn vị (TDV) KHÔNG xem được** trang này (dù TDV xem được Đối soát đánh giá). Lý do: phiếu chứa nhận xét cá nhân và phần hạn chế, khuyết điểm nên không mở chéo giữa các đơn vị (xem comment line 140-144 trong Sidebar.tsx production).

---

## 7. Quản lý tài khoản

**Đường dẫn:** Dashboard → **Quản trị** → **Quản lý tài khoản** (`/admin/nguoi-dung`)

**Quyền:** Admin (`is_system_admin=TRUE`) hoặc TCCB. Backend endpoint yêu cầu quyền Admin (`AdminUserDep`).

### 7.1. Kích hoạt/vô hiệu tài khoản

**Mục đích:** Kích hoạt tài khoản mới hoặc vô hiệu tài khoản công chức nghỉ việc, chuyển công tác.

**Các bước:**

1. Tìm công chức (ô tìm kiếm theo mã CC hoặc họ tên)
2. Xem cột **Trạng thái:** Đang hoạt động / Đã vô hiệu hóa
3. Bấm nút **"Vô hiệu hóa"** (màu đỏ) hoặc **"Kích hoạt"** (màu xanh) ở cột Thao tác
4. Hệ thống hỏi xác nhận → Bấm **"Xác nhận"**

**Lưu ý:**

- **Vô hiệu tài khoản:** Người đó không đăng nhập được nữa, nhưng dữ liệu đánh giá **giữ nguyên** (không xóa). Cờ `is_active` trong bảng `public.cong_chuc` chuyển thành `FALSE`.
- **Kích hoạt lại:** Người đó có thể đăng nhập trở lại (nếu quay lại công tác). Cờ `is_active` chuyển thành `TRUE`.

### 7.2. Reset mật khẩu

**Mục đích:** Reset mật khẩu khi công chức quên mật khẩu hoặc bị khóa tài khoản do nhập sai nhiều lần (10 lần sai → khóa 15 phút).

**Các bước:**

1. Tìm công chức
2. Bấm biểu tượng **🔑** (hoặc nút "Reset mật khẩu") ở cột Thao tác
3. Hệ thống hỏi xác nhận → Bấm **"Xác nhận"**
4. Mật khẩu được đặt lại về **`123456`** (mặc định hệ thống, xem `DEFAULT_PASSWORD` trong `backend/app/api/v1/endpoints/admin.py` line 81)
5. Thông báo cho công chức **đổi mật khẩu ngay** sau khi đăng nhập (độ dài tối thiểu **6 ký tự**)

**Lưu ý:**

- Mọi lần reset mật khẩu đều **ghi nhật ký** (ai reset, khi nào, cho ai) — backend ghi vào log hoặc audit trail (nếu có).
- **Không reset mật khẩu khi không cần thiết** — vi phạm bảo mật. Chỉ reset khi công chức yêu cầu và xác thực đúng danh tính.
- Reset mật khẩu **KHÔNG tự động mở khóa** tài khoản bị vô hiệu hóa (`is_active=FALSE`). Phải kích hoạt lại riêng.

### 7.3. Thêm tài khoản mới

**Các bước:**

1. Vào trang **Quản lý tài khoản**
2. Bấm nút **"Tạo mới"** → mở hộp thoại **"➕ Tạo người dùng mới"**
3. Nhập:
   - **Mã công chức** (bắt buộc): Tối đa 20 ký tự, duy nhất, ví dụ `20ZZ-9999`
   - **Họ tên** (bắt buộc): Tối đa 100 ký tự
   - **Đơn vị** (bắt buộc): Chọn từ dropdown
   - **Vai trò** (bắt buộc): Chọn từ dropdown (SUPER_ADMIN, CCT, PCCT, TDV, PDV, CC, TCCB)
   - **Chức vụ**: Ví dụ "Công chức", "Đội trưởng" (không bắt buộc)
   - **Email**: Tối đa 100 ký tự (không bắt buộc)
   - **Số điện thoại**: Tối đa 20 ký tự — **cần chính xác để nhận tin Zalo** (không bắt buộc nhưng nên điền)
   - **Lãnh đạo**: Tích checkbox nếu là lãnh đạo
   - **Mật khẩu** (bắt buộc): Tối thiểu 6 ký tự — người dùng sẽ đổi sau lần đầu đăng nhập
4. Bấm **"Tạo"**
5. Hệ thống tạo tài khoản và báo thành công

**Lưu ý:**

- **Mã công chức phải duy nhất** — không trùng với ai (database constraint `UNIQUE` trên cột `ma_cc`).
- Thông báo cho công chức **đổi mật khẩu ngay** sau khi đăng nhập (độ dài tối thiểu **6 ký tự**).
- **Mật khẩu admin nhập** khi tạo tài khoản sẽ bị hash bằng bcrypt trước khi lưu vào DB (xem `hash_password()` trong `backend/app/core/security.py`).

---

## 8. Lỗi thường gặp

| Hiện tượng | Nguyên nhân | Cách xử lý |
|------------|-------------|------------|
| Đối soát không tải được dữ liệu | Lỗi server hoặc timeout, hoặc chưa chọn tháng/năm | Chọn tháng/năm trước, bấm "Tải lại"; nếu vẫn lỗi thì liên hệ CNTT |
| Import Excel: "Không tìm thấy công chức" | Gõ sai mã CC, hoặc người đã nghỉ việc, hoặc copy từ nguồn khác không phải sheet tra cứu | **Chỉ** copy mã CC từ sheet "Danh sach cong chuc" trong file mẫu (sheet đó đã lọc sẵn người còn hoạt động) |
| Điều chuyển thất bại: "Công chức đã ở đơn vị này" | Điều chuyển về đúng đơn vị hiện tại (không có gì thay đổi) | Kiểm tra lại đơn vị đích, hoặc xóa dòng này khỏi file import |
| Reset mật khẩu nhưng công chức vẫn không đăng nhập được | Tài khoản bị vô hiệu (`is_active=FALSE`), hoặc bị khóa tạm 15 phút do nhập sai 10 lần | Kiểm tra trạng thái tài khoản, kích hoạt lại nếu cần; nếu bị khóa tạm thì phải đợi hết 15 phút |
| Tổng hợp phiếu: Không xem được phiếu của TDV | Chỉ CCT/PCCT/TCCB/Admin xem được — TDV không xem chéo đơn vị (phiếu có nhận xét cá nhân, khuyết điểm) | Đúng thiết kế (xem comment line 140-144 trong `Sidebar.tsx` production) |
| Xuất Excel bị lỗi (file rỗng hoặc bị hỏng) | Dữ liệu quá lớn, timeout backend | Xuất theo đơn vị riêng lẻ thay vì "Tất cả", hoặc giảm phạm vi thời gian |
| TCCB không truy cập được trang "Điều chuyển hàng loạt" | Trang này chỉ dành cho Admin (`is_system_admin=TRUE`), frontend kiểm tra và chuyển hướng về Dashboard | Đúng thiết kế; TCCB chỉ dùng được "Điều chuyển từng người" (qua modal trong trang Quản lý tài khoản) |

---

*Tài liệu biên soạn tháng 10/2026. Phục vụ công văn 153/CNTT.*
