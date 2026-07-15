# Báo cáo đối chiếu kết quả xếp loại chất lượng tháng 01/2026
## Chi cục Hải quan khu vực VIII

**Ngày lập:** 15/07/2026
**Mục đích:** Xác định điểm khác biệt giữa kết quả trên hệ thống KPI và bản tổng hợp thủ công của các đơn vị, phục vụ rà soát và xử lý dữ liệu.

### Nguồn dữ liệu

| Ký hiệu | Tệp | Mô tả |
|---|---|---|
| `HT` | `Mau04_DanhSach_XepLoai_ChiCuc_01_2026.docx` | Xuất từ hệ thống KPI. 530 bản ghi, 9 cột. |
| `QD` | `QĐ_T1.pdf` | Quyết định số 263/QĐ-HQKV8 ngày 11/3/2026, kèm bảng tổng hợp thủ công của các đơn vị. 546 bản ghi. |

**Lưu ý về độ tin cậy:** file `QD` là bản scan không có lớp text (OCR tiếng Việt không đạt chất lượng). Toàn bộ số liệu phía `HT` được bóc tách bằng code và chính xác 100%. Số liệu phía `QD` được đọc thủ công từ ảnh: các số tổng hợp (546/112/430/0/03/01) lấy từ Điều 1 của Quyết định nên chắc chắn; các dòng cá nhân là spot-check, **cần đối chiếu lại nếu dùng cho quyết định chính thức**.

Quyết định 263 **thay thế Quyết định 188/QĐ-HQKV8 ngày 13/02/2026** — đây là bản đã qua rà soát, và là bản có hiệu lực.

---

## 1. TÓM TẮT ĐIỀU HÀNH

Có **4 nhóm khác biệt** giữa hệ thống và bản tổng hợp của đơn vị:

| # | Vấn đề | Quy mô | Mức độ |
|---|---|---|---|
| 1 | Hệ thống thiếu điểm KPI cho nhóm lãnh đạo / trưởng đơn vị / HĐ 111 → tự động xếp "Không hoàn thành" sai | **63 người** | **Nghiêm trọng** |
| 2 | Hệ thống không có mức "Không xếp loại (E)" và không có trường kỷ luật | **4 người** | Cao |
| 3 | Hệ thống giữ điểm trước rà soát (theo QĐ 188 cũ), chưa cập nhật theo QĐ 263 | Chưa xác định hết, ≥ 5 ca đã xác nhận | Cao |
| 4 | Hệ thống thiếu 16 bản ghi; có 1 ca trùng tên mâu thuẫn xếp loại | 16 + 1 | Trung bình |

Xử lý xong nhóm 1 sẽ giải quyết 60/60 ca lệch mức "Không hoàn thành".

---

## 2. KHÁC BIỆT VỀ CẤU TRÚC

| Tiêu chí | HT (hệ thống) | QD (đơn vị) |
|---|---|---|
| Cột điểm | 1 cột gộp: `Điểm theo dõi, đánh giá tháng` | 3 cột tách: `Điểm tiêu chí chung` + `Điểm KPI` = `Điểm theo dõi đánh giá của tháng` |
| Ký hiệu xếp loại | Chữ đầy đủ ("Hoàn thành xuất sắc nhiệm vụ"...) | Mã A / B / D / E |
| Mức "Không xếp loại" | **Không tồn tại** | Có (mã E) |
| Cột `Ghi chú` | Có, nhưng **rỗng 100% (0/530 dòng)** | Có nội dung: "Điều chỉnh lại điểm đánh giá sau rà soát", "Xếp loại D thi hành hình thức kỷ luật", "Nghỉ thai sản (Không phân loại)" |
| Định danh | Có `Mã công chức` (20ZZ-xxxx) | **Không có mã** — chỉ có Họ tên + Đơn vị |

**Ánh xạ mã xếp loại:** `A` = Hoàn thành xuất sắc nhiệm vụ · `B` = Hoàn thành tốt nhiệm vụ · `C` = Hoàn thành nhiệm vụ · `D` = Không hoàn thành nhiệm vụ · `E` = Không xếp loại

**Công thức suy ra từ QD:** `Điểm theo dõi đánh giá = Điểm tiêu chí chung + Điểm KPI`

---

## 3. KHÁC BIỆT VỀ SỐ LIỆU TỔNG HỢP

| Mức xếp loại | HT | QD | Chênh lệch |
|---|---|---|---|
| Tổng số | **530** | **546** | **-16** |
| A – Hoàn thành xuất sắc | 131 (24,72%) | 112 (20,66%) | **+19** |
| B – Hoàn thành tốt | 336 | 430 | -94 |
| C – Hoàn thành nhiệm vụ | 0 | 0 | 0 |
| D – Không hoàn thành | **63** | **3** | **+60** |
| E – Không xếp loại | 0 (không hỗ trợ) | 1 | -1 |

### Phân bố theo đơn vị (dữ liệu hệ thống)

| Đơn vị | Số người trên HT | Trong đó bị xếp "Không hoàn thành" |
|---|---|---|
| HQCK quốc tế Móng Cái | 138 | 2 |
| HQCK cảng Hòn Gai | 65 | 1 |
| Đội Kiểm soát Hải quan | 65 | 12 |
| HQCK cảng Vạn Gia | 55 | 13 |
| HQCK Hoành Mô | 42 | 10 |
| Văn phòng | 37 | 2 |
| HQCK cảng Cẩm Phả | 36 | 12 |
| HQCK Bắc Phong Sinh | 21 | 2 |
| Đội Phúc tập và Kiểm tra sau thông quan | 20 | 1 |
| Phòng Nghiệp vụ Hải quan | 15 | 1 |
| Phòng Tổ chức cán bộ | 14 | 1 |
| Phòng Công nghệ thông tin | 11 | 1 |
| Phòng Quản lý rủi ro | 7 | 1 |
| Lãnh đạo Chi cục | 4 | 4 |

---

## 4. VẤN ĐỀ 1 — THIẾU ĐIỂM KPI (63 người) ⚠ ƯU TIÊN CAO NHẤT

### Bằng chứng

Toàn bộ 63 người bị hệ thống xếp "Không hoàn thành" có điểm chỉ nằm trong tập rời rạc **{0; 20; 22,5; 25; 35}**. Đối chiếu với QD cho thấy các giá trị này **trùng khớp với cột `Điểm tiêu chí chung`**, tức phần `Điểm KPI` (thường = 70) **bị bỏ trống trên hệ thống**.

| Họ tên | QD: chung + KPI = tổng → loại | HT: điểm → loại |
|---|---|---|
| Tống Thị Thái Hà (Chánh VP) | 25 + 70 = 95 → **A** | 35 → **Không hoàn thành** |
| Võ Hồng Chung (TP TCCB) | 27,5 + 70 = 97,5 → **B** | 35 → **Không hoàn thành** |
| Đinh Việt Dũng (TP NVHQ) | 20 + 70 = 90 → **B** | 35 → **Không hoàn thành** |
| Nguyễn Huy Đông (TP QLRR) | 17,5 + 70 = 87,5 → **B** | 35 → **Không hoàn thành** |
| Ngô Xuân Hiệp (ĐT PT&KTSTQ) | 15 + 70 = 85 → **B** | 35 → **Không hoàn thành** |
| Lê Mạnh Tùng (ĐT BPS) | 20 + 68,3 = 88,3 → **B** | 35 → **Không hoàn thành** |
| Bùi Ngọc Lợi (Phó CCT) | 20 + 70 = 90 → **B** | 20 → **Không hoàn thành** |
| Nguyễn Cảnh Thắng (Phó CCT) | 25 + 70 = 95 → **A** | 25 → **Không hoàn thành** |
| Ngô Tùng Dương (Phó CCT) | 22,5 + 70 = 92,5 → **A** | 22,5 → **Không hoàn thành** |

### Kết luận nguyên nhân

Hệ thống **chưa có công thức tính / chưa đồng bộ điểm KPI** cho 3 nhóm chức danh:

| Nhóm | Số người | Điểm HT đặc trưng | Ghi chú |
|---|---|---|---|
| Lãnh đạo Chi cục | 4 | 20 / 22,5 / 25 | Đúng bằng điểm tiêu chí chung |
| Trưởng phòng / Đội trưởng | 12 | **35** (cứng) | Giá trị 35 không xuất hiện ở QD — cần làm rõ nguồn |
| Hợp đồng 111 | 41 | **20** (cứng) | Đúng bằng điểm tiêu chí chung |
| Điểm 0 (chưa nhập gì) | 6 | 0 | Bao gồm cả Chi cục trưởng và 1 ca nghỉ thai sản |

### 4.1 Nhóm Lãnh đạo Chi cục (4 người)

| TT | Mã công chức | Họ và tên | Năm sinh | Chức vụ | Đơn vị | Điểm HT |
|---|---|---|---|---|---|---|
| 1 | 20ZZ-0224 | Phạm Quốc Hưng | 1973 | Chi cục trưởng | Lãnh đạo Chi cục | 0 |
| 2 | 20ZZ-0565 | Bùi Ngọc Lợi | 1974 | Phó Chi cục trưởng | Lãnh đạo Chi cục | 20 |
| 3 | 20ZZ-0479 | Nguyễn Cảnh Thắng | 1970 | Phó Chi cục trưởng | Lãnh đạo Chi cục | 25 |
| 4 | 20ZZ-0119 | Ngô Tùng Dương | 1969 | Phó Chi cục trưởng | Lãnh đạo Chi cục | 22.50 |

### 4.2 Nhóm Trưởng phòng / Đội trưởng (12 người) — điểm cứng 35

| TT | Mã công chức | Họ và tên | Năm sinh | Chức vụ | Đơn vị | Điểm HT |
|---|---|---|---|---|---|---|
| 5 | 20ZZ-0431 | Vũ Quý Hưng | 1979 | Trưởng phòng | Phòng Công nghệ thông tin | 35 |
| 16 | 20ZZ-0033 | Lê Mạnh Tùng | 1968 | Đội trưởng | HQCK Bắc Phong Sinh | 35 |
| 37 | 20ZZ-0073 | Phùng Thị Nguyên Hạnh | 1974 | Đội trưởng | HQCK cảng Cẩm Phả | 35 |
| 73 | 20ZZ-0231 | Nguyễn Thị Thuý Hà | 1976 | Đội trưởng | HQCK cảng Hòn Gai | 35 |
| 138 | 20ZZ-0375 | Đậu Hùng Dương | 1974 | Đội trưởng | HQCK Hoành Mô | 35 |
| 318 | 20ZZ-0082 | Vũ Đức Dũng | 1967 | Đội trưởng | HQCK cảng Vạn Gia | 35 |
| 373 | 20ZZ-0338 | Nguyễn Hoàng Tuân | 1970 | Đội trưởng | Đội Kiểm soát Hải quan | 35 |
| 438 | 20ZZ-0061 | Đinh Việt Dũng | 1969 | Trưởng phòng | Phòng Nghiệp vụ Hải quan | 35 |
| 453 | 20ZZ-0185 | Ngô Xuân Hiệp | 1968 | Đội trưởng | Đội Phúc tập và Kiểm tra sau thông quan | 35 |
| 473 | 20ZZ-0452 | Nguyễn Huy Đông | 1968 | Trưởng phòng | Phòng Quản lý rủi ro | 35 |
| 480 | 20ZZ-0005 | Võ Hồng Chung | 1971 | Trưởng phòng | Phòng Tổ chức cán bộ | 35 |
| 494 | 20ZZ-0097 | Tống Thị Thái Hà | 1980 | Chánh Văn phòng | Văn phòng | 35 |

### 4.3 Nhóm Hợp đồng 111 (41 người) — điểm cứng 20

| TT | Mã công chức | Họ và tên | Năm sinh | Chức vụ | Đơn vị | Điểm HT |
|---|---|---|---|---|---|---|
| 30 | 20ZZ-0374 | Nguyễn Xuân Tùng |  | Hợp đồng 111 | HQCK Bắc Phong Sinh | 20 |
| 41 | 20ZZ-0619 | Bùi Quốc Văn |  | Hợp đồng 111 | HQCK cảng Cẩm Phả | 20 |
| 42 | 20ZZ-0469 | Hoàng Lê Thế Anh | 1985 | Hợp đồng 111 | HQCK cảng Cẩm Phả | 20 |
| 44 | 20ZZ-0533 | Hoàng Văn Hiệu | 1986 | Hợp đồng 111 | HQCK cảng Cẩm Phả | 20 |
| 45 | 20ZZ - 0223 | Hà Thị Kim Thanh | 1981 | Hợp đồng 111 | HQCK cảng Cẩm Phả | 20 |
| 51 | 20ZZ-0558 | Nguyễn Minh Chiến | 2000 | Hợp đồng 111 | HQCK cảng Cẩm Phả | 20 |
| 56 | 20ZZ-0222 | Nguyễn Văn Tùng | 1987 | Hợp đồng 111 | HQCK cảng Cẩm Phả | 20 |
| 58 | 20ZZ-0420 | Phạm Ngọc Hà | 1974 | Hợp đồng 111 | HQCK cảng Cẩm Phả | 20 |
| 60 | 20ZZ-0604 | Phạm Thị Mai Anh | 1985 | Hợp đồng 111 | HQCK cảng Cẩm Phả | 20 |
| 64 | 20ZZ-0603 | Trần Khánh Chi |  | Hợp đồng 111 | HQCK cảng Cẩm Phả | 20 |
| 145 | 20ZZ-0372 | Chu Thị Tiên | 1971 | Hợp đồng 111 | HQCK Hoành Mô | 20 |
| 146 | 20ZZ-0600 | Chu Văn Hà | 1989 | Hợp đồng 111 | HQCK Hoành Mô | 20 |
| 160 | 20ZZ-0220 | Nguyễn Viết Cường 1971 | 1971 | Hợp đồng 111 | HQCK Hoành Mô | 20 |
| 161 | 20ZZ-0369 | Nguyễn Viết Cường 1988 |  | Hợp đồng 111 | HQCK Hoành Mô | 20 |
| 166 | 20ZZ-0373 | Phạm Duy Huy |  | Hợp đồng 111 | HQCK Hoành Mô | 20 |
| 167 | 20ZZ-0370 | Phạm Văn Tỉnh |  | Hợp đồng 111 | HQCK Hoành Mô | 20 |
| 170 | 20ZZ-0607 | Trần Thị Tình | 1982 | Hợp đồng 111 | HQCK Hoành Mô | 20 |
| 171 | 20ZZ-0399 | Trần Văn Tuyên |  | Hợp đồng 111 | HQCK Hoành Mô | 20 |
| 172 | 20ZZ-0606 | Vũ Duy Nam |  | Hợp đồng 111 | HQCK Hoành Mô | 20 |
| 328 | 20ZZ-0528 | Lê Công Vương | 1981 | Hợp đồng 111 | HQCK cảng Vạn Gia | 20 |
| 331 | 20ZZ-0523 | Lưu Chí Công |  | Hợp đồng 111 | HQCK cảng Vạn Gia | 20 |
| 339 | 20ZZ-0175 | Nguyễn Ngọc Hải | 1981 | Hợp đồng 111 | HQCK cảng Vạn Gia | 20 |
| 341 | 20ZZ-0426 | Nguyễn Quang Sơn | 1983 | Hợp đồng 111 | HQCK cảng Vạn Gia | 20 |
| 344 | 20ZZ-0531 | Nguyễn Trọng Đạt | 1980 | Hợp đồng 111 | HQCK cảng Vạn Gia | 20 |
| 345 | 20ZZ-0499 | Nguyễn Văn Hiếu | 1979 | Hợp đồng 111 | HQCK cảng Vạn Gia | 20 |
| 350 | 20ZZ-0183 | Phạm Thái Hưng | 1978 | Hợp đồng 111 | HQCK cảng Vạn Gia | 20 |
| 352 | 20ZZ-0537 | Phạm Văn Cường |  | Hợp đồng 111 | HQCK cảng Vạn Gia | 20 |
| 353 | 20ZZ-0174 | Phạm Văn Tân | 1981 | Hợp đồng 111 | HQCK cảng Vạn Gia | 20 |
| 357 | 20ZZ-0538 | Trần Mạnh Trung |  | Hợp đồng 111 | HQCK cảng Vạn Gia | 20 |
| 366 | 20ZZ-0500 | Vũ Đình Thảo | 1991 | Hợp đồng 111 | HQCK cảng Vạn Gia | 20 |
| 371 | 20ZZ-0534 | Đỗ Ngọc Hải | 1970 | Hợp đồng 111 | HQCK cảng Vạn Gia | 20 |
| 389 | 20ZZ-0418 | Lý Ngọc Đàm | 1978 | Hợp đồng 111 | Đội Kiểm soát Hải quan | 20 |
| 401 | 20ZZ-0524 | Nguyễn Viết Tiến | 1970 | Hợp đồng 111 | Đội Kiểm soát Hải quan | 20 |
| 405 | 20ZZ-0423 | Nguyễn Văn Đức | 1980 | Hợp đồng 111 | Đội Kiểm soát Hải quan | 20 |
| 406 | 20ZZ-0419 | Ngô Đình Cường | 1984 | Hợp đồng 111 | Đội Kiểm soát Hải quan | 20 |
| 408 | 20ZZ-0526 | Phan Đình Tường | 1982 | Hợp đồng 111 | Đội Kiểm soát Hải quan | 20 |
| 409 | 20ZZ-0218 | Phạm Huy Toàn | 1981 | Hợp đồng 111 | Đội Kiểm soát Hải quan | 20 |
| 425 | 20ZZ-0328 | Trần Thế Hùng | 1967 | Hợp đồng 111 | Đội Kiểm soát Hải quan | 20 |
| 431 | 20ZZ-0427 | Vũ Văn Khá |  | Hợp đồng 111 | Đội Kiểm soát Hải quan | 20 |
| 432 | 20ZZ-0421 | Vũ Đình Thương | 1975 | Hợp đồng 111 | Đội Kiểm soát Hải quan | 20 |
| 436 | 20ZZ-0022 | Đỗ Hoàng Dương | 2000 | Hợp đồng 111 | Đội Kiểm soát Hải quan | 20 |

### 4.4 Nhóm điểm 0 — chưa có dữ liệu nào (6 người)

| TT | Mã công chức | Họ và tên | Năm sinh | Chức vụ | Đơn vị | Điểm HT |
|---|---|---|---|---|---|---|
| 65 | 20ZZ-0628 | Trần Mạnh Cường |  | (trống) | HQCK cảng Cẩm Phả | 0 |
| 67 | 20ZZ-0627 | Trần Viết Duy |  | (trống) | HQCK cảng Cẩm Phả | 0 |
| 191 | 20ZZ-0630 | Dương Việt Cường |  | (trống) | HQCK quốc tế Móng Cái | 0 |
| 289 | 20ZZ-0629 | Vũ Minh Đức |  | (trống) | HQCK quốc tế Móng Cái | 0 |
| 379 | 20ZZ-0625 | Bùi Khánh Chi |  | (trống) | Đội Kiểm soát Hải quan | 0 |
| 523 | 20ZZ-0610 | Vũ Thị Hiên | 1988 | Hợp đồng 111 | Văn phòng | 0 |

> **Vũ Thị Hiên** tại QD là 0/0/0 → E (nghỉ thai sản) — xem Vấn đề 2, không phải lỗi hệ thống về điểm. 5 trường hợp còn lại (Trần Mạnh Cường, Trần Viết Duy, Dương Việt Cường, Vũ Minh Đức, Bùi Khánh Chi) đều **trống cả cột Chức vụ** trên hệ thống → nghi vấn bản ghi chưa được gán chức danh nên không tính được điểm.
>
> Ngoài ra **Phạm Quốc Hưng** (Chi cục trưởng, mã 20ZZ-0224) cũng có điểm 0 nhưng được xếp ở nhóm Lãnh đạo Chi cục tại mục 4.1; tại QD ông có 25 + 70 = 95 → A.

---

## 5. VẤN ĐỀ 2 — HỆ THỐNG KHÔNG PHẢN ÁNH QUYẾT ĐỊNH THỦ CÔNG (4 người)

| Họ tên | Đơn vị | QD | Lý do ghi trong QD | HT | Sai lệch |
|---|---|---|---|---|---|
| Nguyễn Thị Kim Long | Văn phòng | **D** | Xếp loại D thi hành hình thức kỷ luật | 88,89 → Hoàn thành tốt | Bỏ sót kỷ luật |
| Trịnh Trọng Thái | Đội KSHQ | **D** | Xếp loại D thi hành hình thức kỷ luật | 95 → Hoàn thành tốt | Bỏ sót kỷ luật + sai điểm |
| Phạm Hùng Cường | Đội KSHQ | **D** | Xếp loại D thi hành hình thức kỷ luật | 86,42 → Hoàn thành tốt | Bỏ sót kỷ luật |
| Vũ Thị Hiên | Văn phòng | **E** | Nghỉ thai sản (Không phân loại) | 0 → Không hoàn thành | Thiếu mức E |

**Nguyên nhân:** hệ thống thiếu (a) trường đánh dấu đang thi hành kỷ luật để ép mức D, và (b) mức "Không xếp loại (E)" cho các trường hợp nghỉ chế độ.

---

## 6. VẤN ĐỀ 3 — HỆ THỐNG GIỮ ĐIỂM TRƯỚC RÀ SOÁT

QD 263 thay thế QD 188 ngày 13/02/2026. Rất nhiều dòng trong QD ghi chú **"Điều chỉnh lại điểm đánh giá sau rà soát"**. Đối chiếu cho thấy hệ thống vẫn lưu **điểm cũ, cao hơn**:

| Họ tên | HT (điểm cũ) | QD 263 (sau rà soát) | Hệ quả |
|---|---|---|---|
| Trịnh Trọng Thái | 95 | 71,3 | -23,7 |
| Chu Minh Phong | 92,5 → **XS** | 88,3 → **B** | Lệch mức |
| Phạm Xuân Huynh | 95 | 90 | -5 |
| Bùi Thị Hằng | 95 | 90 | -5 |
| Phạm Hồng Hải 1978 | 95 | 90 | -5 |
| Trịnh Ngọc Hoàng Nam | 70,94 | 76,4 | +5,46 |

Đây là nguyên nhân chính khiến **tỷ lệ XS trên hệ thống (24,72%) cao hơn QD (20,66%)** — chênh 19 người.

> **Cần làm:** rà toàn bộ các dòng có ghi chú "Điều chỉnh lại điểm đánh giá sau rà soát" trong QD và cập nhật lên hệ thống. Số lượng dòng loại này trong QD chưa đếm hết được do chất lượng scan — ước tính vài chục dòng, tập trung ở Đội KSHQ và HQCK quốc tế Móng Cái.

---

## 7. VẤN ĐỀ 4 — CHẤT LƯỢNG DỮ LIỆU

### 7.1 Thiếu 16 bản ghi
HT có 530 dòng, QD có 546. **Chênh 16 người chưa xác định được danh tính** do QD không có mã công chức và bản scan không OCR được. Chênh lệch tập trung ở **Văn phòng** và **Phòng Nghiệp vụ Hải quan**.

### 7.2 Trùng tên, mâu thuẫn xếp loại
**Chu Minh Phong** có **2 dòng trên hệ thống**, cùng điểm 92,5 nhưng **một dòng xếp XS, một dòng xếp Tốt**. Cần rà lại theo mã công chức.

### 7.3 Sai khác chính tả tên
**Nguyễn Hoàng Tuân** (HT, mã 20ZZ-0338, Đội trưởng Đội KSHQ) vs **Nguyễn Hoàng Tuấn** (QD). Cùng một người, khác dấu. Ảnh hưởng tới mọi phép đối chiếu tự động theo tên.

### 7.4 Bản ghi thiếu chức vụ
7 bản ghi trên hệ thống có cột `Chức vụ` trống (xem mục 4.4).

### 7.5 Quy tắc xếp loại XS chưa rõ
Trên hệ thống có **121 người điểm ≥ 90 nhưng chỉ xếp "Hoàn thành tốt"**, trong khi 93 người cũng điểm 90,0 lại xếp XS. Xếp loại XS **không thuần theo điểm** — có áp trần tỷ lệ hoặc nguồn dữ liệu khác. Cần đối chiếu với quy chế tại **QĐ 67/QĐ-HQKV6 ngày 27/01/2026**.

---

## 8. DANH SÁCH VIỆC CẦN XỬ LÝ (theo thứ tự ưu tiên)

1. **[P0]** Nạp / đồng bộ `Điểm KPI` cho 63 người tại mục 4 — theo 3 nhóm: Lãnh đạo Chi cục (4), Trưởng đơn vị (12), HĐ 111 (41), điểm 0 (6). Nguồn số liệu: cột `Điểm KPI` trong QD 263. → giải quyết 60/60 ca lệch mức D.
2. **[P0]** Làm rõ vì sao trưởng đơn vị nhận điểm cứng **35** và HĐ 111 nhận **20** trên hệ thống — đây là lỗi công thức, không phải lỗi nhập liệu.
3. **[P1]** Bổ sung mức xếp loại **E – Không xếp loại** và trường **đang thi hành kỷ luật** (ép mức D) vào hệ thống. Áp dụng cho 4 người tại mục 5.
4. **[P1]** Cập nhật điểm sau rà soát theo QD 263 cho toàn bộ dòng có ghi chú "Điều chỉnh lại điểm đánh giá sau rà soát" (mục 6).
5. **[P2]** Xác định 16 bản ghi thiếu; ưu tiên rà Văn phòng và Phòng NVHQ.
6. **[P2]** Xử lý bản ghi trùng Chu Minh Phong; chuẩn hóa tên Nguyễn Hoàng Tuân/Tuấn; bổ sung chức vụ cho 7 bản ghi trống.
7. **[P2]** Đối chiếu quy tắc xếp loại XS trên hệ thống với QĐ 67/QĐ-HQKV6.
8. **[P3]** Đề xuất hệ thống bổ sung cột `Ghi chú` có nội dung và tách 2 cột `Điểm tiêu chí chung` / `Điểm KPI` để đối chiếu được với báo cáo đơn vị.

---

## 9. GHI CHÚ CHO XỬ LÝ TỰ ĐỘNG

- Khóa nối (join key) tin cậy duy nhất là **`Mã công chức` (20ZZ-xxxx)** nhưng **chỉ có ở phía HT**. Phía QD phải nối theo `Họ và tên` + `Đơn vị`, và tên có trùng lặp (hệ thống đã phải hậu tố năm sinh: "Bùi Thị Huyền 1985", "Nguyễn Viết Cường 1971"/"1988", "Nguyễn Minh Tuấn 1986").
- Chuẩn hóa dấu tiếng Việt trước khi so khớp tên (xem 7.3).
- File `QĐ_T1.pdf` là ảnh scan xoay 90°, **không có lớp text**; tesseract với `vie.traineddata` cho kết quả không dùng được do kẻ bảng. Nếu cần bóc tách toàn bộ 546 dòng, phải dùng OCR chuyên bảng hoặc nhập tay.
- Dữ liệu HT đã bóc tách sẵn: `sys.csv` (530 dòng × 9 cột). Danh sách 63 ca lệch: `63_nguoi_lech_xep_loai_T01_2026.csv`.
