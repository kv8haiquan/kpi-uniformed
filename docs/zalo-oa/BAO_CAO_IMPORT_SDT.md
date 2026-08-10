# Báo cáo đối chiếu số điện thoại — kênh Zalo OA

**Nguồn:** `DANH SACH SO DIEN THOAI CONG CHUC 2026.xlsx`  
**Đối chiếu với:** `public.cong_chuc` (544 công chức đang hoạt động)  
**Chế độ:** đối chiếu, chưa ghi database

> Khớp theo **họ và tên** vì file nguồn không có cột mã công chức.
> Đã kiểm tra: không có tên trùng ở cả hai phía nên cách khớp này an toàn.

---

## 1. Tổng quan

| Chỉ số | Số lượng |
|---|---:|
| Công chức đang hoạt động trong hệ thống | 544 |
| Dòng đọc được từ file | 548 |
| **Khớp được người + số hợp lệ** | **541** |
| Số điện thoại không dùng được | 0 |
| Có trong file nhưng không tìm thấy trong hệ thống | 7 |
| **Công chức CHƯA có số điện thoại** | **3** |

**Độ phủ: 541/544 = 99.4%**

> ✅ Độ phủ rất tốt, đủ điều kiện triển khai.

---

## 2. Công chức CHƯA có số điện thoại (3 người)

Những người này sẽ **không nhận được** thông báo họp qua Zalo.

| # | Mã CC | Họ và tên | Chức vụ | Đơn vị |
|---:|---|---|---|---|
| 1 | 20ZZ-0331 | Nguyễn Thị Thu Hường | Hợp đồng 111 | HQCK quốc tế Móng Cái |
| 2 | 20ZZ-0631 | Nguyễn Văn Hùng |  | Phòng Nghiệp vụ Hải quan |
| 3 | ADMIN-001 | Quản trị viên | Quản trị viên hệ thống | Phòng Quản trị Hệ thống |

**Gom theo đơn vị:**

| Đơn vị | Số người thiếu |
|---|---:|
| HQCK quốc tế Móng Cái | 1 |
| Phòng Nghiệp vụ Hải quan | 1 |
| Phòng Quản trị Hệ thống | 1 |

---

## 3. Dòng trong file không dùng được (7 dòng)

| Họ và tên (trong file) | Số trong file | Lý do |
|---|---|---|
| Vũ Văn Lưu | `0973348***` | Không tìm thấy trong hệ thống (có thể đã nghỉ/chuyển đơn vị) |
| Lê Thị Minh | `0913251***` | Không tìm thấy trong hệ thống (có thể đã nghỉ/chuyển đơn vị) |
| Lê Thuý Hà | `0912336***` | Không tìm thấy trong hệ thống (có thể đã nghỉ/chuyển đơn vị) |
| Nguyễn Thu Hường | `0977226***` | Khớp khi bỏ dấu nhưng ngày sinh không xác nhận được |
| Lê Thanh Xuân | `0912092***` | Không tìm thấy trong hệ thống (có thể đã nghỉ/chuyển đơn vị) |
| Nguyễn Anh Tuấn(84) | `0989668***` | Năm sinh mâu thuẫn: file ghi 1984, hệ thống ghi 1972 (20ZZ-0090 Nguyễn Anh Tuấn 1972) — không dám khớp |
| Nguyễn Nghĩa Hoằng | `0916665***` | Không tìm thấy trong hệ thống (có thể đã nghỉ/chuyển đơn vị) |

---

## 4. Số điện thoại trùng giữa nhiều người (2 số)

Thường là nhập nhầm — cần đơn vị xác nhận lại.

| Số | Những người cùng khai |
|---|---|
| 0934 216 *** | 20ZZ-0032 Vũ Tuấn Hải, 20ZZ-0336 Vũ Hồng Hải |
| 0936 451 *** | 20ZZ-0555 Vũ Thanh Hồng, 20ZZ-0538 Trần Mạnh Trung |

---

## 5. Lệch ngày sinh (5 trường hợp)

Tên khớp nhưng ngày sinh khác — **có thể là trùng tên khác người**.
Cần kiểm tra tay trước khi tin kết quả khớp.

| Mã CC | Họ và tên | Ngày sinh trong hệ thống | Ngày sinh trong file |
|---|---|---|---|
| 20ZZ-0010 | Ngô Thị Cẩm Linh | 1983-10-10 | 1983-10-16 |
| 20ZZ-0599 | Lê Duy Bình | 1988-09-27 | 1988-03-26 |
| 20ZZ-0328 | Trần Thế Hùng | 1967-04-21 | 1968-04-21 |
| 20ZZ-0434 | Ngô Thị Mỳ | 1971-04-14 | 1974-04-14 |
| 20ZZ-0385 | Lê Văn Phương | 1972-07-20 | 1970-07-21 |
