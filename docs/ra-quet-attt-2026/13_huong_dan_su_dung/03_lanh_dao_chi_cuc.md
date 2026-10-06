# HƯỚNG DẪN SỬ DỤNG — DÀNH CHO LÃNH ĐẠO CHI CỤC

**Đối tượng:** Chi cục trưởng (CCT), Phó Chi cục trưởng (PCCT) — 4 người  
**Phiên bản:** Tháng 10/2026

---

## MỤC LỤC

1. [Tổng quan vai trò và quyền hạn](#1-tổng-quan-vai-trò-và-quyền-hạn)
2. [Duyệt kê khai và đánh giá](#2-duyệt-kê-khai-và-đánh-giá)
3. [Xếp loại A/B/C/D (CCT)](#3-xếp-loại-abcd-cct)
4. [Khóa/mở khóa kỳ đánh giá (CCT)](#4-khóamở-khóa-kỳ-đánh-giá-cct)
5. [Sửa điểm tiêu chí chung](#5-sửa-điểm-tiêu-chí-chung)
6. [Tổng hợp phiếu Mẫu 02 toàn Chi cục](#6-tổng-hợp-phiếu-mẫu-02-toàn-chi-cục)
7. [Phiếu tổng hợp và báo cáo](#7-phiếu-tổng-hợp-và-báo-cáo)
8. [Điều chỉnh kết quả công việc (CCT)](#8-điều-chỉnh-kết-quả-công-việc-cct)
9. [Lỗi thường gặp](#9-lỗi-thường-gặp)

---

## 1. Tổng quan vai trò và quyền hạn

### 1.1. Vai trò của CCT/PCCT

| Vai trò | Phạm vi quản lý | Quyền hạn |
|---------|-----------------|-----------|
| **Phó Chi cục trưởng (PCCT)** | Khối đơn vị được phân công phụ trách | Duyệt kê khai, tiêu chí chung cấp 2; Xem báo cáo toàn Chi cục; Sửa điểm tiêu chí chung |
| **Chi cục trưởng (CCT)** | Toàn Chi cục (15 đơn vị, 558 công chức) | Toàn quyền: Duyệt, xếp loại, điều chỉnh điểm, khóa/mở khóa kỳ, điều chỉnh KQCV |

### 1.2. Đường dẫn chính

Dashboard → Thanh bên trái → **Phê duyệt** (`/xep-loai`, trang với nhiều tab)

Dashboard → Thanh bên trái → **Xếp loại** (`/xep-loai`) (CCT thấy đầy đủ, PCCT thấy một phần)

*(ảnh minh họa bổ sung khi in)*

---

## 2. Duyệt kê khai và đánh giá

### 2.1. Phạm vi duyệt

- **PCCT:** Duyệt cấp 2 kê khai, tiêu chí chung của **khối đơn vị mình phụ trách**.
- **CCT:** Duyệt cấp 2 của **toàn Chi cục** (nếu cần).

### 2.2. Đường dẫn

Dashboard → **Phê duyệt** (`/xep-loai`) → Tab **Công việc** (`?tab=cong-viec`) / **Tiêu chí chung** (`?tab=tieu-chi`)

### 2.3. Các bước

**Giống như TDV** (xem mục tương ứng trong `02_lanh_dao_don_vi.md`), nhưng:

- CCT/PCCT **xem được toàn bộ đơn vị** trong phạm vi phụ trách
- Có bộ lọc **Đơn vị** để thu hẹp danh sách
- Có thể **duyệt hàng loạt** nhiều đơn vị cùng lúc

**Lưu ý:**

- **CCT/PCCT không duyệt thường xuyên** — chỉ duyệt khi TDV chưa duyệt hoặc có vấn đề.
- Trách nhiệm chính thuộc về **TDV**.

---

## 3. Xếp loại A/B/C/D (CCT)

### 3.1. Mục đích

**Chỉ CCT** có quyền quyết định xếp loại chính thức A/B/C/D cho toàn bộ công chức.

### 3.2. Đường dẫn

Dashboard → **Xếp loại** (`/xep-loai?tab=quy`)

### 3.3. Các bước

**Bước 1: Chọn quý, năm**

- Chọn **Quý** và **Năm** từ danh sách thả xuống

**Bước 2: Xem bảng tổng hợp toàn Chi cục**

Bảng hiển thị:
- Tên công chức, mã công chức
- Đơn vị
- Điểm KPI (70 điểm)
- Điểm tiêu chí chung (30 điểm)
- **Tổng điểm** (100 điểm)
- Xếp loại tự động (A/B/C/D tính theo ngưỡng điểm)
- Xếp loại đề xuất (công chức tự đề xuất)
- Xếp loại quyết định (CCT quyết)

**Bước 3: Kiểm soát tỷ lệ loại A**

Hệ thống hiển thị cảnh báo nếu **vi phạm tỷ lệ**:

- **Quy tắc:** Số công chức loại A ≤ 20% số công chức loại B
- Ví dụ: Có 50 người loại B → tối đa 10 người loại A

**Bước 4: Xếp loại từng công chức**

1. Bấm vào dòng công chức
2. Xem chi tiết:
   - Kết quả KPI (a, b, c)
   - Điểm tiêu chí chung (31 tiêu chí)
   - Phiếu đánh giá (nhận xét của TDV)
3. Chọn **Xếp loại quyết định** từ dropdown:
   - A — Hoàn thành xuất sắc nhiệm vụ
   - B — Hoàn thành tốt nhiệm vụ
   - C — Hoàn thành nhiệm vụ
   - D — Không hoàn thành nhiệm vụ
4. Bấm **"Lưu"**

**Bước 5: Hoàn tất xếp loại**

- Sau khi xếp loại xong toàn bộ, bấm **"Lưu"** hoặc nút hoàn tất tương ứng
- Hệ thống lưu kết quả xếp loại
- Xếp loại được ghi nhận và có thể khóa kỳ để chặn chỉnh sửa (xem mục 4)

### 3.4. Ngưỡng xếp loại

| Xếp loại | Ngưỡng tổng điểm | Ý nghĩa |
|----------|------------------|---------|
| **A** | ≥ 90 điểm | Hoàn thành xuất sắc nhiệm vụ |
| **B** | 70 – dưới 90 điểm | Hoàn thành tốt nhiệm vụ |
| **C** | 50 – dưới 70 điểm | Hoàn thành nhiệm vụ |
| **D** | < 50 điểm | Không hoàn thành nhiệm vụ |

**Lưu ý:**

- CCT có quyền **xếp khác với ngưỡng hệ thống** (ví dụ: 92 điểm nhưng xếp B) — nhưng phải có căn cứ.
- **Xếp loại D:** Cần xem xét kỹ, có thể cần họp Hội đồng đánh giá.

### 3.5. Lưu ý nghiệp vụ

- **Hạn chốt:** Trước ngày **23** tháng cuối quý (hạn nộp hồ sơ về TCCB), sau đó TCCB tổng hợp nộp lên Cục.
- **Tỷ lệ loại A:** Không vượt 20% loại B (theo quy định).
- **Công chức chưa đủ thời gian:** Làm việc quá ngắn trong quý → không xếp loại (xếp loại E — Không đánh giá).

---

## 4. Khóa/mở khóa kỳ đánh giá (CCT)

### 4.1. Mục đích

Sau khi hoàn tất xếp loại, CCT có thể khóa kỳ đánh giá để ngăn chặn thay đổi dữ liệu.

**Lưu ý:** Chức năng khóa/mở khóa kỳ **chưa có giao diện nút riêng** trên trang xếp loại. Hệ thống tự động khóa dữ liệu theo cơ chế backend khi đủ điều kiện.

### 4.2. Cơ chế khóa tự động

- Kê khai công việc: Tự động khóa khi đã duyệt (không sửa/xóa được)
- Tiêu chí chung: Khóa sau khi duyệt xong
- Phiếu đánh giá: Khóa khi hoàn tất quy trình

### 4.3. Mở khóa (nếu cần điều chỉnh)

Nếu cần điều chỉnh dữ liệu đã khóa:
- Liên hệ quản trị hệ thống (admin) hoặc CNTT
- Hoặc sử dụng chức năng **Sửa điểm tiêu chí chung** (mục 5) — CCT được phép sửa ngay cả khi đã chốt

**Lưu ý:**

- Mọi điều chỉnh quan trọng đều **ghi nhật ký**: ai, khi nào, điều chỉnh gì.
- Không tồn tại nút "Khóa kỳ" / "Mở khóa" trên giao diện người dùng hiện tại.

---

## 5. Sửa điểm tiêu chí chung

### 5.1. Mục đích

CCT có quyền **điều chỉnh điểm tiêu chí chung** của từng công chức — áp dụng khi:

- Phát hiện sai sót trong quá trình duyệt
- Cần điều chỉnh dựa trên thông tin bổ sung

### 5.2. Ai dùng

- **CCT:** Điều chỉnh **mọi đơn vị**, **bất kể trạng thái** (kể cả báo cáo đã chốt)
- **PCCT:** Điều chỉnh khối phụ trách (nếu chưa chốt)
- **TDV:** Điều chỉnh đơn vị mình (nếu chưa chốt)

### 5.3. Đường dẫn

**Cách 1 — Từ trang Xếp loại:**

1. Dashboard → **Xếp loại**
2. Chọn quý, năm
3. Bấm vào dòng công chức cần điều chỉnh
4. Bấm nút **"Sửa điểm TC chung"** (ở góc phải chi tiết)

**Cách 2 — Từ trang riêng (CCT/PCCT):**

1. Dashboard → Thanh bên trái → **Điều chỉnh điểm TC** (`/dieu-chinh-tieu-chi`)
2. Chọn quý, năm, đơn vị
3. Bảng hiển thị danh sách công chức
4. Bấm **"Sửa điểm"** hoặc **"Điều chỉnh"** ở dòng công chức cần điều chỉnh

### 5.4. Các bước sửa điểm

**Bước 1: Mở modal sửa điểm**

Modal (cửa sổ pop-up) hiển thị:
- Tên công chức
- Danh sách 31 tiêu chí
- Mỗi tiêu chí có:
  - Điểm tự chấm
  - Điểm duyệt (nếu có)
  - Ô nhập để điều chỉnh điểm (input number)

**Bước 2: Nhập điểm điều chỉnh**

- Mỗi tiêu chí có **ô nhập điểm** (input number)
- Nhập điểm mới theo **bội số 0.5**: 0; 0,5; 1,0; 1,5; ... đến tối đa điểm tiêu chí
- **Nếu không điều chỉnh:** Để trống (giữ nguyên điểm duyệt)

**Bước 3: Lưu**

- Bấm **"Lưu"**
- Hệ thống tự tính lại:
  - Tổng điểm tiêu chí chung (30 điểm)
  - Tổng điểm (KPI + Tiêu chí chung)
  - Xếp loại tự động (theo ngưỡng mới)
  - Cập nhật dữ liệu trong báo cáo (nếu báo cáo đã hoàn tất)

**Bước 4: Xác nhận thay đổi**

- Nếu báo cáo **đã chốt**, hệ thống hiển thị cảnh báo:
  > "Báo cáo đã được duyệt. Điều chỉnh điểm sẽ tính lại xếp loại. Bạn có chắc chắn?"
- Bấm **"Xác nhận"**

### 5.5. Lưu ý nghiệp vụ

- **CCT sửa được bất kể trạng thái** — kể cả báo cáo đã chốt.
- **PCCT/TDV chỉ sửa được khi chưa chốt.**
- Mọi điều chỉnh **đều ghi nhật ký**: Ai, khi nào, tiêu chí nào, từ bao nhiêu sang bao nhiêu.
- **Lưu ý:** Hiện **chưa có trường nhập lý do điều chỉnh** — đang nằm trong khuyến nghị cải tiến.

---

## 6. Tổng hợp phiếu Mẫu 02 toàn Chi cục

### 6.1. Mục đích

CCT, PCCT, TCCB xem danh sách **toàn bộ phiếu đánh giá quý** (Mẫu 02A/02B) của toàn Chi cục — để:

- Tổng hợp hồ sơ nộp lên Cục (hạn 23 tháng cuối quý)
- Kiểm tra ai chưa lập phiếu, ai chưa duyệt

**Lưu ý quan trọng:** Trang này **CHỈ ĐỌC** — không duyệt, không sửa phiếu. Muốn lập/sửa phiếu, vào trang xếp loại (tab Quý) hoặc đánh giá.

### 6.2. Ai dùng

- **CCT, PCCT, TCCB:** Xem toàn Chi cục
- **TDV:** **KHÔNG** xem được đơn vị khác (chỉ xem đơn vị mình)

### 6.3. Đường dẫn

Dashboard → Thanh bên trái → **Tổng hợp phiếu 02** (`/phieu-tong-hop`)

### 6.4. Các bước

**Bước 1: Chọn quý, năm**

**Bước 2: Lọc (nếu cần)**

- **Đơn vị:** Chọn đơn vị cụ thể (hoặc "Tất cả")
- **Trạng thái:** Nháp / Chờ duyệt / Đã duyệt / Bị từ chối
- **Xếp loại:** A / B / C / D
- **Tìm kiếm:** Nhập tên hoặc mã công chức

**Bước 3: Xem danh sách**

Bảng hiển thị (542 dòng, thời gian tải ~0.19s):
- Tên công chức, mã công chức
- Đơn vị
- **Trạng thái phiếu** (Nháp / Chờ duyệt / Đã duyệt / Bị từ chối)
- **Xếp loại quyết định** (A/B/C/D)
- Tổng điểm
- Ngày lập phiếu
- Cột **Hành động** (chỉ đọc)

**Bước 4: Xem chi tiết phiếu**

- Bấm vào dòng công chức
- Phiếu hiển thị (Mẫu 02A hoặc 02B)
- **Chỉ xem, không sửa**

**Bước 5: Tải hàng loạt (nếu cần)**

- Bấm nút **"Xuất Excel"** (góc trên bên phải)
- File Excel 17 cột, kích thước ~109 KB, thời gian tải ~0.33s

**Bước 6: Tải từng phiếu (nếu cần)**

- Bấm biểu tượng **tải xuống** ở cột Hành động
- Chọn **"Tải phiếu Mẫu 02"** hoặc **"Tải bảng kê công việc"**

### 6.5. Lưu ý nghiệp vụ

- Người chưa lập phiếu vẫn hiển thị trong danh sách — để TCCB biết ai còn thiếu.
- TDV **không** xem được đơn vị khác — phiếu chứa nhận xét cá nhân, hạn chế/khuyết điểm.
- Quyền chỉ xem — không duyệt, không sửa từ trang này.

---

## 7. Phiếu tổng hợp và báo cáo

### 7.1. Phiếu tổng hợp

**Mục đích:** Lập phiếu tổng hợp kết quả xếp loại toàn Chi cục (Mẫu 04).

**Đường dẫn:** Dashboard → **Xếp loại** → các tab báo cáo tương ứng

**Các bước:**

1. Chọn quý, năm
2. Xem báo cáo tổng hợp xếp loại (trang hiển thị sẵn):
   - Số lượng từng xếp loại (A/B/C/D)
   - Tỷ lệ %
   - Danh sách theo đơn vị
3. Xuất file báo cáo nếu cần (chọn định dạng phù hợp)

### 7.2. Báo cáo thống kê

**Đường dẫn:** Dashboard → **Xếp loại** → các tab báo cáo

**Các loại báo cáo:**

- **Báo cáo xếp loại theo quý:** Tổng hợp A/B/C/D toàn Chi cục
- **Báo cáo theo đơn vị:** So sánh các đơn vị
- **Báo cáo theo lĩnh vực:** Phân tích theo 16 lĩnh vực công việc
- **Báo cáo xu hướng:** So sánh các quý trong năm

**Lưu ý:**

- Báo cáo **chỉ hiển thị dữ liệu đã chốt** (báo cáo đã duyệt).
- Xuất file **Excel** để phân tích thêm.

---

## 8. Điều chỉnh kết quả công việc (CCT)

### 8.1. Mục đích

CCT có quyền **điều chỉnh kết quả công việc** (KQCV) của công chức — áp dụng khi:

- Phát hiện sai sót trong kê khai đã duyệt
- Cần điều chỉnh số lỗi chất lượng/tiến độ

**Lưu ý:** Chức năng này **rất nhạy cảm** — chỉ dùng khi thật sự cần thiết.

### 8.2. Đường dẫn

Dashboard → **Điều chỉnh KQCV** (`/dieu-chinh-kqcv`) (menu riêng cho lãnh đạo)

### 8.3. Các bước

1. Chọn quý, năm, đơn vị
2. Chọn công chức cần điều chỉnh
3. Xem danh sách kê khai đã duyệt
4. Bấm **"Điều chỉnh"** ở dòng kê khai cần sửa
5. Nhập:
   - Số lượng mới
   - Số lỗi chất lượng (nếu có)
   - Số lỗi tiến độ (nếu có)
   - **Lý do điều chỉnh** (bắt buộc)
6. Bấm **"Lưu"**
7. Hệ thống **tính lại điểm KPI** (a, b, c)

**Lưu ý:**

- Mọi điều chỉnh **ghi nhật ký** đầy đủ: Ai, khi nào, điều chỉnh gì, lý do.
- **Chỉ CCT** có quyền điều chỉnh KQCV.

---

## 9. Lỗi thường gặp

| Hiện tượng | Nguyên nhân | Cách xử lý |
|------------|-------------|------------|
| Không xếp loại được (nút mờ) | Báo cáo chưa đủ điều kiện (thiếu dữ liệu, vi phạm tỷ lệ) | Kiểm tra cảnh báo trên màn hình |
| Vi phạm tỷ lệ loại A | Số A > 20% số B | Giảm số người xếp A hoặc tăng số người xếp B |
| Không khóa được kỳ | Còn đơn vị chưa hoàn tất | Kiểm tra trang Đối soát |
| Sửa điểm tiêu chí không ảnh hưởng xếp loại | Chưa bấm "Lưu" hoặc hệ thống chưa tính lại | Kiểm tra lại, F5 tải lại trang |
| Trang Tổng hợp phiếu trống | Chưa có công chức nào lập phiếu | Đúng thiết kế — chờ TDV lập phiếu |
| Không tải được Excel Tổng hợp phiếu | Lỗi server hoặc file quá lớn | Thử lại, hoặc xuất theo đơn vị |

---

*Tài liệu biên soạn tháng 10/2026. Phục vụ công văn 153/CNTT.*
