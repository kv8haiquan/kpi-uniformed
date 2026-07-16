# Kiểm chứng lần 5 — Bản xuất T4/2026 (`__5_`)
## Chi cục Hải quan khu vực VIII

**Ngày lập:** 15/07/2026

---

## 1. KẾT LUẬN

🟢 **T4 đã sửa xong 4 ca đơn vị cuối cùng. Cả hai tháng nay đều 0 ca sai đơn vị.**

Toàn bộ vấn đề đơn vị — thứ đã kéo từ 80 ca sai xuống 0 — **coi như đóng lại**.

Còn lại: **11 ca ở T4** và **6 ca ở T5** là lỗi phần mềm thật sự, chia thành 4 nhóm rõ rệt.

---

## 2. FILE `__5_`: ĐÚNG 4 THAY ĐỔI, ĐỀU LÀ ĐƠN VỊ

| | `__4_` | **`__5_`** |
|---|---|---|
| Thời điểm xuất | 16/07 17:58 | **16/07 18:06** |
| md5 `document.xml` | `97b15b6062…` | **`cf2b9bbaac…`** ✅ đổi |
| Số dòng | 545 | 545 |

| Loại thay đổi | Số lượng |
|---|---|
| Đổi **Đơn vị** | **4** |
| Đổi Điểm / Mức / Chức vụ / Họ tên | **0** |
| Thêm / bớt bản ghi | **0** |

| Mã CC | Họ tên | Cũ | Mới | PL4 |
|---|---|---|---|---|
| 20ZZ-0138 | Hoàng Văn Thoại | Phòng Quản lý rủi ro | **HQCK quốc tế Móng Cái** | ✅ |
| 20ZZ-0207 | Nguyễn Thanh Quang 1970 | Đội Kiểm soát Hải quan | **HQCK quốc tế Móng Cái** | ✅ |
| 20ZZ-0513 | Nguyễn Tiến Vinh | Đội Phúc tập và KTSTQ | **HQCK quốc tế Móng Cái** | ✅ |
| 20ZZ-0560 | Phạm Thị Thu Thuỷ | Văn phòng | **HQCK quốc tế Móng Cái** | ✅ |

Đúng 4 ca tôi nêu ở báo cáo trước. Cột VOTE đã được áp cho cả T4.

---

## 3. TRẠNG THÁI HAI THÁNG

| Chỉ tiêu | T4 | T5 |
|---|---|---|
| Quân số | 545 / 548 | **548 / 548** ✅ |
| **Sai đơn vị** | **0** ✅ | **0** ✅ |
| Lệch mức | 41 | 12 |
| — DS TCC đã nhận diện (chờ nghiệp vụ) | **30** (73%) | **6** (50%) |
| — **Lỗi phần mềm thật sự** | **11** | **6** |
| Trưởng đơn vị điểm cứng 35 | 0 ✅ | 0 ✅ |
| Người ≥90 chỉ xếp B | 0 ✅ | 0 ✅ |
| Trạng thái "Không đánh giá" | không có ❌ | không có ❌ |

> T4 vẫn thiếu 5 người (4 Lãnh đạo Chi cục + Đỗ Xuân Hiền) và thừa 2 bản ghi rác (Dương Việt Cường, Vũ Minh Đức) — **chưa động tới**.

---

## 4. 11 CA LỖI PHẦN MỀM CÒN LẠI Ở T4

| Mã CC | Họ và tên | Đơn vị | Chức vụ | PL: chung + KPI = tổng | PL | HT | HT mức | Δ | Nhận định |
|---|---|---|---|---|---|---|---|---|---|
| 20ZZ-0398 | Trần Công Mạnh | HQCK Bắc Phong Sinh | Hợp đồng 111 | 20 + 70 = 90.0 | A | 83.0 | B | -7.00 | **KPI 63 thay vì 70** |
| 20ZZ-0397 | Nguyễn Thị Thúy | HQCK Bắc Phong Sinh | Hợp đồng 111 | 20 + 70 = 90.0 | A | 83.0 | B | -7.00 | **KPI 63 thay vì 70** |
| 20ZZ-0375 | Đậu Hùng Dương | HQCK Hoành Mô | Đội trưởng | 20 + 70 = 90.0 | A | 89.99 | B | -0.01 | Chênh nhỏ quanh ngưỡng 90 |
| 20ZZ-0186 | Phạm Văn Hanh | HQCK cảng Hòn Gai | Phó Đội trưởng | 20 + 70 = 90.0 | A | 89.98 | B | -0.02 | Chênh nhỏ quanh ngưỡng 90 |
| 20ZZ-0087 | Đàm Quang Lượng | HQCK cảng Hòn Gai | Công chức | 20 + 70 = 90.0 | A | 89.5 | B | -0.50 | Chênh nhỏ quanh ngưỡng 90 |
| 20ZZ-0097 | Tống Thị Thái Hà | Văn phòng | Chánh Văn phòng | 20 + 70 = 90.0 | A | 89.99 | B | -0.01 | Chênh nhỏ quanh ngưỡng 90 |
| 20ZZ-0602 | Nguyễn Anh Dũng | Văn phòng | Hợp đồng 111 | 20 + 70 = 90.0 | A | 83.0 | B | -7.00 | **KPI 63 thay vì 70** |
| 20ZZ-0506 | Kiều Văn Ninh | Đội Kiểm soát Hải quan | Phó Đội trưởng | 19.5 + 70 = 89.5 | B | 90.0 | A | +0.50 | **Áp trần chung = 20** |
| 20ZZ-0620 | Phan Văn Vinh | Đội Kiểm soát Hải quan | Phó Đội trưởng | 19.5 + 70 = 89.5 | B | 90.0 | A | +0.50 | **Áp trần chung = 20** |
| 20ZZ-0156 | Bùi Hồng Ngọc | Đội Kiểm soát Hải quan | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A | +0.50 | **Áp trần chung = 20** |
| 20ZZ-0252 | Phạm Xuân Huynh | Đội Kiểm soát Hải quan | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A | +0.50 | **Áp trần chung = 20** |

## 5. 6 CA LỖI PHẦN MỀM CÒN LẠI Ở T5

| Mã CC | Họ và tên | Đơn vị | Chức vụ | PL: chung + KPI = tổng | PL | HT | HT mức | Δ | Nhận định |
|---|---|---|---|---|---|---|---|---|---|
| 20ZZ-0365 | Đăng Tích Khoa | HQCK cảng Hòn Gai | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A | +0.50 | **Áp trần chung = 20** |
| 20ZZ-0071 | Vũ Văn Nam | HQCK cảng Vạn Gia | Công chức | 15 + 70 = 85.0 | B | 90.0 | A | +5.00 | **Áp trần chung = 20** |
| 20ZZ-0205 | Trương Anh Tuấn | Phòng CNTT | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A | +0.50 | **Áp trần chung = 20** |
| 20ZZ-0112 | Bùi Thị Huyền | Phòng CNTT | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A | +0.50 | **Áp trần chung = 20** |
| 20ZZ-0211 | Dương Thanh Hà | Phòng Tổ chức cán bộ | Công chức | 20 + 70 = 90.0 | A | 89.5 | B | -0.50 | Chênh nhỏ quanh ngưỡng 90 |
| 20ZZ-0042 | Đoàn Hồng Chinh | Phòng Tổ chức cán bộ | Công chức | 19.5 + 70 = 89.5 | B | 19.5 | D | -70.00 | **Mất trọn KPI** |

---

## 6. BỐN NHÓM LỖI CÒN LẠI (17 ca)

### 6.1 🔴 Áp trần tiêu chí chung = 20 — **8 ca** (T4: 4 · T5: 4)

Hệ thống lấy `chung = 20` thay vì điểm thực do đơn vị chấm → điểm bị **nâng**, được **A oan**.

| Kỳ | Người | PL | HT |
|---|---|---|---|
| T4 | Kiều Văn Ninh, Phan Văn Vinh, Bùi Hồng Ngọc, Phạm Xuân Huynh (đều Đội KSHQ) | 19,5 + 70 = 89,5 → B | 90,0 → **A** |
| T5 | Đăng Tích Khoa, Trương Anh Tuấn, Bùi Thị Huyền | 19,5 + 70 = 89,5 → B | 90,0 → **A** |
| T5 | **Vũ Văn Nam** | **15** + 70 = 85 → B | 90,0 → **A** |

Kiểm chứng công thức: cả 8 ca đều đúng `HT = 20 + KPI`. **Vũ Văn Nam nặng nhất — lệch +5,00 điểm.**

> Đây là **lỗi nghiêm trọng nhất còn lại**: nó cho A cho người không đủ điều kiện. Ở T4 tập trung toàn bộ tại **Đội Kiểm soát Hải quan**.

### 6.2 🟡 Chênh nhỏ quanh ngưỡng 90 — **5 ca** (T4: 4 · T5: 1)

| Kỳ | Người | PL | HT | Δ |
|---|---|---|---|---|
| T4 | Tống Thị Thái Hà (Chánh VP) | 90,0 → A | 89,99 → B | −0,01 |
| T4 | Đậu Hùng Dương (ĐT Hoành Mô) | 90,0 → A | 89,99 → B | −0,01 |
| T4 | Phạm Văn Hanh (Phó ĐT Hòn Gai) | 90,0 → A | 89,98 → B | −0,02 |
| T4 | Đàm Quang Lượng | 90,0 → A | 89,5 → B | −0,50 |
| T5 | Dương Thanh Hà | 90,0 → A | 89,5 → B | −0,50 |

Sai lệch chỉ 0,01–0,5 điểm nhưng **rơi đúng hai bên ngưỡng 90 nên đổi mức**. Ba ca đầu lệch đúng 0,01–0,02 — hệ thống có KPI 69,98–69,99 trong khi PL ghi 70.

> Cần chốt: điểm lấy mấy chữ số thập phân, làm tròn hay cắt cụt. Với hàng trăm người nằm ở 89,9x, quy tắc này **quyết định trực tiếp ai được A**.

### 6.3 🟡 KPI = 63 thay vì 70 — **3 ca HĐ 111 ở T4**

| Mã CC | Họ tên | Đơn vị | PL | HT | Δ |
|---|---|---|---|---|---|
| 20ZZ-0602 | Nguyễn Anh Dũng | Văn phòng | 20 + 70 = 90 → A | 83,0 → B | −7,00 |
| 20ZZ-0398 | Trần Công Mạnh | HQCK Bắc Phong Sinh | 20 + 70 = 90 → A | 83,0 → B | −7,00 |
| 20ZZ-0397 | Nguyễn Thị Thúy | HQCK Bắc Phong Sinh | 20 + 70 = 90 → A | 83,0 → B | −7,00 |

Cả 3 lệch **đúng −7,00** — hệ thống dùng KPI = 63 thay vì 70. Đều là Hợp đồng 111 nhưng **không có trong DS TCC** → VB714 của họ đã duyệt, nhưng KPI ra sai giá trị. Khác hẳn nhóm "mất trọn 70 điểm".

### 6.4 🔴 Đoàn Hồng Chinh (T5) — lỗ hổng của bộ lọc DS TCC

| | Giá trị |
|---|---|
| PL5 | 19,5 + **70** = 89,5 → **B** |
| HT5 | **19,50** → **D** |
| Trong DS TCC? | **KHÔNG** — vì ông là **Công chức**, không phải HĐ 111 |

Nhắc lại từ báo cáo trước: loại vấn đề `KPI HĐ111 (VB714)` có 29/29 dòng đều là Hợp đồng 111 → **bộ lọc quét theo chức danh, không theo triệu chứng**. Đây là **ca duy nhất bị xếp D oan mà không ai theo dõi**.

---

## 7. VIỆC CẦN LÀM

### Phần mềm

| # | Việc | Ưu tiên | Quy mô |
|---|---|---|---|
| 1 | **Sửa lỗi áp trần tiêu chí chung = 20** | **P0** | 8 ca — cho A oan |
| 2 | **Sửa bộ lọc DS TCC: quét theo triệu chứng (KPI thiếu), không theo chức danh** | **P0** | bỏ sót Đoàn Hồng Chinh |
| 3 | 3 ca HĐ 111 T4 có KPI = 63 thay vì 70 | P1 | 3 ca |
| 4 | Chốt quy tắc làm tròn quanh ngưỡng 90 | P1 | 5 ca đổi mức |
| 5 | **T4: khôi phục 4 bản ghi Lãnh đạo Chi cục + Đỗ Xuân Hiền** | P1 | 5 người thiếu |
| 6 | Bổ sung trạng thái **"Không đánh giá"** (E) | P1 | 5 ca chờ |
| 7 | Xóa/nạp điểm 2 bản ghi rác T4 (Dương Việt Cường, Vũ Minh Đức) | P2 | |
| 8 | Sửa mã `"20ZZ - 0223"`; bổ sung chức vụ các bản ghi trống | P2 | |

### Nghiệp vụ — chiếm phần lớn số ca còn lại

| # | Việc | Số ca |
|---|---|---|
| 9 | **21 VB714 chờ ĐT duyệt** — Hòn Gai (7) · Vạn Gia (9) · Cẩm Phả (5) | 21 |
| 10 | 5 HĐ 111 chưa kê khai VB714 + 3 mới nháp chưa gửi | 8 |
| 11 | **6 người chưa kê khai TCC** — gồm **Chi cục trưởng và 2 Phó Chi cục trưởng** | 6 |
| 12 | 7 bản ghi 0 điểm chờ đơn vị xác nhận (thai sản → E / nghỉ / nhầm) | 7 |
| 13 | 3 TCC đã kê khai chờ duyệt 2 cấp | 3 |

> Nút thắt vẫn ở **ĐT Hòn Gai (Nguyễn Thị Thúy Hà)** và **ĐT Cẩm Phả (Phùng Thị Nguyên Hạnh)** — vừa phải duyệt cho cấp dưới, vừa là người chính họ chưa kê khai TCC.

---

## 8. TIẾN TRÌNH TOÀN DỰ ÁN

| Lỗi | T01 | T4 đầu | T5 đầu | **Hiện tại** |
|---|---|---|---|---|
| Trưởng đơn vị điểm cứng 35 | 9 | 0 | 0 | ✅ **Đóng** |
| Người ≥90 chỉ xếp B | 121 | 0 | 0 | ✅ **Đóng** |
| Mã công chức trùng | 14 | 0 | 0 | ✅ **Đóng** |
| Cột Ghi chú rỗng | 100% | có nội dung | có nội dung | ✅ **Đóng** |
| **Sai đơn vị** | – | **80** | **2** | ✅ **Đóng (0/0)** |
| HĐ 111 mất KPI | 41 | 29 | 0 | 🟡 Là **quy trình**, không phải lỗi PM |
| Lãnh đạo Chi cục | 4 (điểm 0) | **4 (mất bản ghi)** | 3 (chưa kê khai) | 🟡 T5 là quy trình · **T4 còn lỗi PM** |
| Áp trần chung = 20 | – | 4 | 4 | 🔴 **Còn 8 ca** |
| Trạng thái "Không đánh giá" | không có | không có | không có | 🔴 **Chưa làm** |

**Nhìn lại:** từ 63 ca "Không hoàn thành" sai ở T01 và 80 ca sai đơn vị ở T4, nay chỉ còn **17 ca lỗi phần mềm thật sự** trên tổng 1.096 bản ghi của hai tháng — tỷ lệ **1,6%**. Phần lớn số ca còn hiển thị sai là **chờ thao tác nghiệp vụ**, không phải lỗi hệ thống.

---

## 9. GHI CHÚ CHO XỬ LÝ TỰ ĐỘNG

- **Không bỏ dấu tiếng Việt khi so tên.** `Nguyễn Thị Thúy Hà`↔`Nguyễn Thị Thuý Hà`, `Đăng Tích Khoa`↔`Đặng Tích Khoa`, `Nguyễn Thu Hường`↔`Nguyễn Thị Thu Hường`, `Vũ Thị Thủy`↔`Vũ Thị Thuỷ` là **cùng người**. Nhưng `Vũ Thị Hiền`↔`Vũ Thị Hiên` và `Trần Văn Tuyển`↔`Trần Văn Tuyên` là **khác người**. Dùng bảng ánh xạ tường minh.
- Mã cần `replace(' ','')` trước khi nối — `"20ZZ - 0223"` vẫn còn.
- Dung sai điểm: **PL4 ±0,10** (cắt cụt 1 chữ số) · **PL5 ±0,006** (2 chữ số).
- Trần điểm tổng **không phải 90** — tiêu chí chung có thể tới 25.
- `Đơn vị` nay đã đúng ở cả hai kỳ → **có thể dùng làm điều kiện ghép phụ**, nhưng vẫn nên ưu tiên nối theo mã.
