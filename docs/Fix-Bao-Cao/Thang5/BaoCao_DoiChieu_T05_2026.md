# Báo cáo đối chiếu kết quả theo dõi, đánh giá THÁNG 5/2026
## Chi cục Hải quan khu vực VIII

**Ngày lập:** 15/07/2026
**Phạm vi:** đối chiếu **đầy đủ 548/548 dòng** (khác tháng 01/2026 — kỳ đó phụ lục là bản scan nên chỉ spot-check được).

### Nguồn dữ liệu

| Ký hiệu | Tệp | Bản ghi | Mô tả |
|---|---|---|---|
| `HT` | `Mau04_DanhSach_XepLoai_ChiCuc_05_2026.docx` | **546** | Xuất từ hệ thống KPI |
| `PL` | `Pl_Tháng_5_2026.pdf` | **548** | Bảng tổng hợp kèm Thông báo 3083/TB-HQKV8 ngày 29/6/2026. **Có lớp text → bóc tách được 100%** |
| `TB` | `Thông_báo_điểm_theo_dõi_đánh_giá_T5_2026__ký_.pdf` | – | Thông báo 3083/TB-HQKV8, bảng tổng hợp theo đơn vị |

**Kiểm chứng chất lượng bóc tách:** dữ liệu parse từ `PL` khớp **tuyệt đối** với `TB`: 548 người · A 104 · B 436 · C 5 · D 0 · Không đánh giá 3 · tỷ lệ A/(A+B) = 19,26%. Con số phía `PL` trong báo cáo này là đáng tin cậy, không phải ước lượng.

**Bộ tiêu chí mới:** áp dụng theo **CV 1829/HQKV8-TCCB ngày 01/5/2026** và **CV 1909/HQKV8-TCCB ngày 07/5/2026**. Công thức: `Điểm theo dõi đánh giá = Điểm tiêu chí chung (trần 20) + Điểm KPI (trần 70)`.

**Ánh xạ mức:** `A` = Hoàn thành xuất sắc · `B` = Hoàn thành tốt · `C` = Hoàn thành nhiệm vụ · `D` = Không hoàn thành

**Ngưỡng suy ra từ dữ liệu:** A ≥ 90 · B: 70–89,99 · C: 60–69,99 · D < 60. Cả `PL` và `HT` đều áp cùng ngưỡng này (đã kiểm chứng: PL mức A min = 90,0; HT mức A min = 90,0). **Khác tháng 01/2026**, kỳ này A **không có trần tỷ lệ** — chỉ cần ≥ 90 là A.

---

## 1. TÓM TẮT

| Chỉ tiêu | HT | PL / TB (chuẩn) | Lệch |
|---|---|---|---|
| Tổng số | 546 | **548** | −2 |
| A – Hoàn thành xuất sắc | **115** | **104** | **+11** |
| B – Hoàn thành tốt | 411 | 436 | −25 |
| C – Hoàn thành nhiệm vụ | **11** | 5 | +6 |
| D – Không hoàn thành | **7** | **0** | **+7** |
| Không đánh giá | 0 (không hỗ trợ) | 3 | −3 |
| Tỷ lệ A/(A+B) | **21,82%** | **19,26%** | +2,56 đ% |

Trong 542 cặp đối chiếu được cả điểm và mức:

- **476 người khớp hoàn toàn (87,8%)**
- **65 người lệch điểm** · **32 người lệch mức**

> **Điểm khác biệt lớn nhất so với tháng 01:** kỳ này **lỗi không chỉ nằm ở hệ thống**. Phụ lục do các đơn vị lập có **13 dòng sai số học** (mục 4), trong đó 11 dòng ở HQCK Hoành Mô làm 11 người bị hạ từ A xuống B. Cần xử lý cả hai phía.

---

## 2. PHÂN LOẠI NGUYÊN NHÂN LỆCH (66 ca)

| # | Nhóm nguyên nhân | Số ca | Phía sai | Mức độ |
|---|---|---|---|---|
| 1 | HT lấy **điểm tiêu chí chung = 20 (trần)** thay vì điểm thực → thổi điểm lên | **18** | Hệ thống | **Nghiêm trọng** |
| 2 | HT **mất phần điểm tiêu chí chung**, chỉ còn KPI → tụt ~20 điểm | **13** | Hệ thống | **Nghiêm trọng** |
| 3 | HT = **0** (mất toàn bộ) — nhóm Lãnh đạo Chi cục | **4** | Hệ thống | **Nghiêm trọng** |
| 4 | HT **mất phần KPI**, chỉ còn tiêu chí chung | **1** | Hệ thống | Cao |
| 5 | Lệch nhỏ < 0,6 (làm tròn / nhập lệch) | **24** | Cả hai | Thấp |
| 6 | Khác (chưa quy được về quy luật) | **6** | Cần điều tra | Trung bình |

Cộng thêm: **13 dòng sai số học trong chính Phụ lục** (mục 4) và **4 ca lệch quân số** (mục 5).

### 2.1 ⚠ Nhóm 1 — Hệ thống áp trần điểm tiêu chí chung = 20 (18 người)

Đây là lỗi **mới, chưa từng thấy ở tháng 01**. Hệ thống lấy `chung = 20` (giá trị trần) thay vì điểm thực do đơn vị chấm, làm điểm bị **nâng lên** và nhiều người **được A oan**.

Kiểm chứng công thức: với cả 18 ca, `Điểm HT = 20 + Điểm KPI (PL)` — khớp tuyệt đối.

Tập trung ở: **HQCK cảng Hòn Gai 15** · Phòng CNTT 2 · HQCK cảng Vạn Gia 1.

| Mã CC | Họ và tên | Đơn vị | Chức vụ | PL: chung + KPI = tổng | PL mức | HT điểm | HT mức |
|---|---|---|---|---|---|---|---|
| 20ZZ-0473 | Lê Thị Thanh Vân | HQCK cảng Hòn Gai | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A |
| 20ZZ-0458 | Lê Nguyên Hoàn | HQCK cảng Hòn Gai | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A |
| 20ZZ-0159 | Lưu Thị Loan | HQCK cảng Hòn Gai | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A |
| 20ZZ-0554 | Trần Tùng Dương | HQCK cảng Hòn Gai | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A |
| 20ZZ-0365 | Đăng Tích Khoa | HQCK cảng Hòn Gai | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A |
| 20ZZ-0107 | Nguyễn Anh Tuấn 1981 | HQCK cảng Hòn Gai | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A |
| 20ZZ-0208 | Nguyễn Thị Thanh Hương | HQCK cảng Hòn Gai | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A |
| 20ZZ-0064 | Đàm Quang Cường | HQCK cảng Hòn Gai | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A |
| 20ZZ-0444 | Trần Văn Hiếu | HQCK cảng Hòn Gai | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A |
| 20ZZ-0522 | Trịnh Đăng Dung | HQCK cảng Hòn Gai | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A |
| 20ZZ-0239 | Lê Thanh Dương | HQCK cảng Hòn Gai | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A |
| 20ZZ-0305 | Trần Cao Sơn | HQCK cảng Hòn Gai | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A |
| 20ZZ-0190 | Nguyễn Duy Khánh | HQCK cảng Hòn Gai | Công chức | 19 + 70 = 89.0 | B | 90.0 | A |
| 20ZZ-0475 | Nguyễn Thế Thành | HQCK cảng Hòn Gai | Công chức | 19 + 70 = 89.0 | B | 90.0 | A |
| 20ZZ-0213 | Đỗ Vân Trung | HQCK cảng Hòn Gai | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A |
| 20ZZ-0071 | Vũ Văn Nam | HQCK cảng Vạn Gia | Công chức | 15 + 70 = 85.0 | B | 90.0 | A |
| 20ZZ-0205 | Trương Anh Tuấn | Phòng CNTT | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A |
| 20ZZ-0112 | Bùi Thị Huyền | Phòng CNTT | Công chức | 19.5 + 70 = 89.5 | B | 90.0 | A |

> Riêng **Vũ Văn Nam** (Vạn Gia): PL chấm chung 15 → 85 điểm (B), hệ thống cho 90 (A) — lệch **+5 điểm và nhảy 1 mức**.
> **HQCK cảng Hòn Gai** vì lỗi này mà có **29 người A trên hệ thống, trong khi TB chỉ 14** — hơn gấp đôi.

### 2.2 ⚠ Nhóm 2 — Hệ thống mất điểm tiêu chí chung (13 người)

Ngược chiều nhóm 1: `Điểm HT = Điểm KPI` đúng, nhưng **mất hẳn phần tiêu chí chung (~19,5–22,5)**. Hậu quả: điểm rơi xuống dưới 70 → bị đẩy từ **B xuống C**.

Đây là **lỗi kéo dài từ tháng 01** (kỳ đó là Tống Thị Thái Hà). Nay lan rộng, tập trung ở **Phòng Tổ chức cán bộ (6/13)**.

| Mã CC | Họ và tên | Đơn vị | Chức vụ | PL: chung + KPI = tổng | PL mức | HT điểm | HT mức |
|---|---|---|---|---|---|---|---|
| 20ZZ-0073 | Phùng Thị Nguyên Hạnh | HQCK cảng Cẩm Phả | Đội trưởng | 20 + 69.93 = 69.93 | B | 69.93 | C |
| 20ZZ-0082 | Vũ Đức Dũng | HQCK cảng Vạn Gia | Đội trưởng | 20 + 70 = 90.0 | A | 69.99 | C |
| 20ZZ-0187 | Nguyễn Đình Hiến | HQCK quốc tế Móng Cái | Quyền Đội trưởng | 20 + 69.99 = 89.99 | B | 69.99 | C |
| 20ZZ-0431 | Vũ Quý Hưng | Phòng CNTT | Trưởng phòng | 22 + 70 = 92.0 | A | 70.0 | B |
| 20ZZ-0061 | Đinh Việt Dũng | Phòng Nghiệp vụ Hải quan | Trưởng phòng | 19.5 + 69.99 = 89.5 | B | 69.99 | C |
| 20ZZ-0452 | Nguyễn Huy Đông | Phòng QLRR | Trưởng phòng | 19.5 + 70 = 89.5 | B | 70.0 | B |
| 20ZZ-0005 | Võ Hồng Chung | Phòng Tổ chức cán bộ | Trưởng phòng | 19.5 + 70 = 89.5 | B | 70.0 | B |
| 20ZZ-0035 | Nguyễn Thị Thuý Nga 1978 | Phòng Tổ chức cán bộ | Phó trưởng phòng | 22.5 + 70 = 92.5 | A | 70.0 | B |
| 20ZZ-0322 | Phùng Thế Phương | Phòng Tổ chức cán bộ | Công chức | 19.5 + 70 = 89.5 | B | 70.0 | B |
| 20ZZ-0483 | Nguyễn Đức Tuệ 1985 | Phòng Tổ chức cán bộ | Công chức | 19.5 + 70 = 89.5 | B | 70.0 | B |
| 20ZZ-0194 | Ngô Minh Hoàn | Phòng Tổ chức cán bộ | Công chức | 19.5 + 70 = 89.5 | B | 70.0 | B |
| 20ZZ-0403 | Trần Khánh Hoàng | Phòng Tổ chức cán bộ | Công chức | 19.5 + 70 = 89.5 | B | 70.0 | B |
| 20ZZ-0185 | Ngô Xuân Hiệp | Đội Phúc tập và KTSTQ | Đội trưởng | 20 + 69.98 = 89.98 | B | 69.98 | C |

### 2.3 ⚠ Nhóm 3 — Lãnh đạo Chi cục: điểm 0 (4 người)

**Lỗi tồn tại từ tháng 01 đến nay, chưa được xử lý.** Toàn bộ Lãnh đạo Chi cục có điểm 0 trên hệ thống → xếp Không hoàn thành. Tháng 01 ít nhất còn giữ được phần tiêu chí chung; **tháng 5 mất sạch, còn tệ hơn**.

| Mã CC | Họ và tên | Đơn vị | Chức vụ | PL: chung + KPI = tổng | PL mức | HT điểm | HT mức |
|---|---|---|---|---|---|---|---|
| 20ZZ-0224 | Phạm Quốc Hưng | Lãnh đạo Chi cục | Chi cục trưởng | 25 + 70 = 95.0 | A | 0.0 | D |
| 20ZZ-0565 | Bùi Ngọc Lợi | Lãnh đạo Chi cục | Phó Chi cục trưởng | 23 + 70 = 93.0 | A | 0.0 | D |
| 20ZZ-0119 | Ngô Tùng Dương | Lãnh đạo Chi cục | Phó Chi cục trưởng | 20 + 69.9 = 89.9 | B | 0.0 | D |
| 20ZZ-0479 | Nguyễn Cảnh Thắng | Lãnh đạo Chi cục | Phó Chi cục trưởng | 20 + 70 = 90.0 | A | 0.0 | D |

### 2.4 Nhóm 4 — Mất điểm KPI (1 người)

| Mã CC | Họ và tên | Đơn vị | Chức vụ | PL: chung + KPI = tổng | PL mức | HT điểm | HT mức |
|---|---|---|---|---|---|---|---|
| 20ZZ-0042 | Đoàn Hồng Chinh | Phòng Tổ chức cán bộ | Công chức | 19.5 + 70 = 89.5 | B | 19.5 | D |

### 2.5 Nhóm 6 — Chưa quy được quy luật (6 người) — cần điều tra

| Mã CC | Họ và tên | Đơn vị | Chức vụ | PL: chung + KPI = tổng | PL mức | HT điểm | HT mức |
|---|---|---|---|---|---|---|---|
| 20ZZ-0378 | Chu Minh Phong | HQCK Hoành Mô | Công chức | 15 + 70 = 85.0 | B | 89.5 | B |
| 20ZZ-0293 | Lương Ngọc Thành | HQCK Hoành Mô | Công chức | 20 + 70 = 90.0 | A | 91.0 | A |
| 20ZZ-0388 | Đỗ Thế Anh | HQCK Hoành Mô | Công chức | 20 + 70 = 90.0 | A | 91.0 | A |
| 20ZZ-0231 | Nguyễn Thị Thúy Hà | HQCK cảng Hòn Gai | Đội trưởng | 20 + 64.1 = 84.1 | B | 69.99 | C |
| 20ZZ-0508 | Nguyễn Xuân Giáp | HQCK cảng Hòn Gai | Công chức | 19 + 69.9 = 88.9 | B | 89.99 | B |
| 20ZZ-0615 | Lê Trung Hiếu | HQCK cảng Hòn Gai | Hợp đồng 111 | 19 + 67.6 = 86.6 | B | 87.67 | B |

> **Nguyễn Thị Thúy Hà** (Đội trưởng Hòn Gai) là ca nặng nhất nhóm này: PL 20 + 64,1 = 84,1 (B), HT 69,99 (C). Điểm HT không bằng chung, không bằng KPI, cũng không bằng tổng — **sai lệch không giải thích được**.
> **Chu Minh Phong**: PL 15 + 70 = 85 (B), HT 89,5. Hệ thống dùng chung ≈ 19,5 thay vì 15.
> **Lương Ngọc Thành, Đỗ Thế Anh**: HT 91,0 nhưng trần công thức là 20 + 70 = **90**. Hệ thống cho điểm **vượt trần** — cần kiểm tra ngay.

---

## 3. MA TRẬN CHUYỂN MỨC PL → HT

| PL → HT | Số người | Đánh giá |
|---|---|---|
| A → A | 97 | ✅ |
| B → B | 408 | ✅ |
| C → C | 5 | ✅ |
| **B → A** | **18** | ❌ Hệ thống nâng mức (lỗi trần 20) |
| **B → C** | **5** | ❌ Hệ thống hạ mức (mất tiêu chí chung) |
| **A → B** | **3** | ❌ |
| **A → D** | **3** | ❌ Lãnh đạo Chi cục |
| **B → D** | **2** | ❌ |
| **A → C** | **1** | ❌ Vũ Đức Dũng |

**Tổng 32 người bị xếp sai mức trên hệ thống.**

---

## 4. ⚠ LỖI TRONG CHÍNH PHỤ LỤC CỦA CÁC ĐƠN VỊ (13 dòng)

Đây là phát hiện **mới và quan trọng**: `chung + KPI ≠ tổng` ngay trong Phụ lục.

| STT PL | Họ và tên | Đơn vị | Tính đúng | PL ghi | PL mức | Δ |
|---|---|---|---|---|---|---|
| 457 | Phùng Thị Nguyên Hạnh | HQCK cảng Cẩm Phả | 20 + 69.93 = 89.93 | 69.93 | B | +20.00 |
| 325 | Bùi Vinh Quang | HQCK Hoành Mô | 20 + 70 = 90.00 | 89.5 | B | +0.50 |
| 330 | Lý Trần Hùng | HQCK Hoành Mô | 20 + 70 = 90.00 | 89.5 | B | +0.50 |
| 335 | Trần Ngọc Diệp | HQCK Hoành Mô | 20 + 70 = 90.00 | 89.5 | B | +0.50 |
| 336 | Vũ Thị Linh Chi | HQCK Hoành Mô | 20 + 70 = 90.00 | 89.5 | B | +0.50 |
| 340 | Lưu Thị Sen | HQCK Hoành Mô | 20 + 70 = 90.00 | 89.5 | B | +0.50 |
| 358 | Trần Thị Tình | HQCK Hoành Mô | 20 + 70 = 90.00 | 89.5 | B | +0.50 |
| 359 | Vũ Duy Nam | HQCK Hoành Mô | 20 + 70 = 90.00 | 89.5 | B | +0.50 |
| 360 | Nguyễn Viết Cường 1971 | HQCK Hoành Mô | 20 + 70 = 90.00 | 89.5 | B | +0.50 |
| 361 | Nguyễn Viết Cường 1988 | HQCK Hoành Mô | 20 + 70 = 90.00 | 89.5 | B | +0.50 |
| 363 | Trần Văn Tuyên | HQCK Hoành Mô | 20 + 70 = 90.00 | 89.5 | B | +0.50 |
| 60 | Đinh Việt Dũng | Phòng Nghiệp vụ Hải quan | 19.5 + 69.99 = 89.49 | 89.5 | B | -0.01 |
| 344 | Trần Quang Hưng | HQCK Hoành Mô | 20 + 70 = 90.00 | 89.99 | B | +0.01 |

### 4.1 HQCK Hoành Mô — 11 người bị hạ mức oan

11 dòng có `20 + 70 = 90` (đúng ra là **mức A**) nhưng phụ lục ghi tổng **89,5** và xếp **B**. Sai lệch **đồng loạt −0,5**, cùng một đơn vị, cùng một kiểu → **không phải lỗi ngẫu nhiên**, mà là lỗi công thức/thao tác của đơn vị hoặc chủ ý hạ điểm.

Nếu tính đúng, HQCK Hoành Mô phải có **18 người A thay vì 7**, và tổng toàn Chi cục là **115 A** — trùng khớp với con số hệ thống đưa ra.

> Ba người trong nhóm này (Bùi Vinh Quang, Lý Trần Hùng, Trần Ngọc Diệp, Vũ Thị Linh Chi, Lưu Thị Sen, Trần Thị Tình, Vũ Duy Nam, Nguyễn Viết Cường 1971/1988, Trần Văn Tuyên, Trần Quang Hưng) **đang bị thiệt quyền lợi**. Đây là vấn đề cần xử lý gấp nhất về mặt nhân sự.

### 4.2 Phùng Thị Nguyên Hạnh (Đội trưởng, Cẩm Phả)

Phụ lục ghi `20 + 69,93 = **69,93**` — sót mất số 8, đúng ra là **89,93**. Mức vẫn ghi B (đúng), nên chỉ là lỗi hiển thị cột tổng. Nhưng hệ thống cũng cho 69,93 và xếp **C** → nếu ai lấy cột tổng của phụ lục làm chuẩn sẽ xếp sai.

---

## 5. CHÊNH LỆCH QUÂN SỐ: 546 vs 548

| Trường hợp | Nguồn | Chi tiết | Xử lý |
|---|---|---|---|
| **Vũ Văn Lưu** (VP, HĐ 111) | Chỉ có ở PL (STT 43) | Không đánh giá — đã chấm dứt HĐLĐ theo QĐ 614/QĐ-HQKV8 ngày 26/05/2026 | Hệ thống **không có là hợp lý**, nhưng PL vẫn liệt kê |
| **Bùi Anh Luận** (VP, HĐ 111) | Chỉ có ở PL (STT 27) | 19 + 70 = 89 → B | ❌ **Thiếu trên hệ thống** |
| **Bùi Quang Tiến** (Móng Cái, HĐ 111) | Chỉ có ở PL (STT 304) | 20 + 69,99 = 89,99 → B | ❌ **Thiếu trên hệ thống** |
| **Vương Trọng Dũng** (20ZZ-0120, Móng Cái, Công chức) | Chỉ có ở HT | Điểm 0 → Không hoàn thành | ❌ **Thừa trên hệ thống** — không có trong PL |

Cân đối: 546 + 3 − 1 = 548 ✓

---

## 6. ĐỐI CHIẾU THEO ĐƠN VỊ

| Đơn vị | Quân số | TB: A | TB: B | TB: C | TB: KĐG | HT: A | HT: B | HT: C | HT: D | Lệch A |
|---|---|---|---|---|---|---|---|---|---|---|
| Lãnh đạo Chi cục | 4 | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 4 | -3 ⚠ |
| Văn phòng | 41 | 8 | 32 | 0 | 1 | 8 | 31 | 0 | 0 | +0 ⚠ |
| Phòng Tổ chức cán bộ | 14 | 2 | 12 | 0 | 0 | 0 | 13 | 0 | 1 | -2 ⚠ |
| Phòng Nghiệp vụ Hải quan | 18 | 3 | 15 | 0 | 0 | 3 | 14 | 1 | 0 | +0 ⚠ |
| Phòng QLRR | 8 | 1 | 7 | 0 | 0 | 1 | 7 | 0 | 0 | +0 |
| Phòng CNTT | 11 | 2 | 9 | 0 | 0 | 3 | 8 | 0 | 0 | +1 ⚠ |
| Đội Phúc tập và KTSTQ | 22 | 4 | 18 | 0 | 0 | 4 | 17 | 1 | 0 | +0 ⚠ |
| Đội Kiểm soát Hải quan | 65 | 14 | 51 | 0 | 0 | 14 | 51 | 0 | 0 | +0 |
| HQCK quốc tế Móng Cái | 138 | 25 | 112 | 0 | 1 | 25 | 109 | 1 | 1 | +0 ⚠ |
| HQCK Hoành Mô | 42 | 7 | 30 | 5 | 0 | 7 | 30 | 5 | 0 | +0 |
| HQCK Bắc Phong Sinh | 21 | 4 | 17 | 0 | 0 | 4 | 17 | 0 | 0 | +0 |
| HQCK cảng Hòn Gai | 72 | 14 | 57 | 0 | 1 | 29 | 41 | 1 | 1 | +15 ⚠ |
| HQCK cảng Cẩm Phả | 37 | 7 | 30 | 0 | 0 | 7 | 29 | 1 | 0 | +0 ⚠ |
| HQCK cảng Vạn Gia | 55 | 10 | 45 | 0 | 0 | 10 | 44 | 1 | 0 | +0 ⚠ |

> **Phụ lục khớp Thông báo 100% ở mọi đơn vị.** Sai lệch nằm hoàn toàn ở phía hệ thống.
> Ba đơn vị lệch nặng nhất: **HQCK cảng Hòn Gai** (A: 29 vs 14 — lỗi trần 20), **Phòng Tổ chức cán bộ** (A: 0 vs 2 — mất tiêu chí chung), **Lãnh đạo Chi cục** (toàn bộ 4 người thành D).

---

## 7. HỆ THỐNG KHÔNG HỖ TRỢ TRẠNG THÁI "KHÔNG ĐÁNH GIÁ" (3 người)

| Họ tên | Đơn vị | Lý do trong PL | HT |
|---|---|---|---|
| Vũ Văn Lưu | Văn phòng | Chấm dứt HĐLĐ theo QĐ 614/QĐ-HQKV8 ngày 26/05/2026 | Không có bản ghi |
| Hứa Hà Lê | HQCK quốc tế Móng Cái | Nghỉ thai sản | Cần kiểm tra |
| Trần Thị Khánh Linh | HQCK cảng Hòn Gai | Nghỉ thai sản | Cần kiểm tra |

Ngoài ra **Nguyễn Anh Tuấn 1984** (Vạn Gia) có ghi chú *"Chuyển Chi cục Hải quan khu vực VII từ ngày 25/5/2026"* nhưng **vẫn được đánh giá** (17,50 + 69,98 = 87,48 → B).

→ Vấn đề tồn tại từ tháng 01 (khi đó là mức "E – Không xếp loại" cho Vũ Thị Hiên). **Chưa được khắc phục.**

---

## 8. SO SÁNH DIỄN BIẾN THÁNG 01 → THÁNG 5

| Vấn đề | T01/2026 | T5/2026 | Xu hướng |
|---|---|---|---|
| Lãnh đạo Chi cục thiếu điểm | 4 người (giữ được điểm chung) | 4 người (**điểm 0, mất sạch**) | 🔴 Xấu đi |
| Trưởng đơn vị điểm cứng 35 | 9 người | **Không còn** | 🟢 Đã sửa |
| HĐ 111 thiếu KPI | 41 người | **Không còn** | 🟢 Đã sửa |
| Mất điểm tiêu chí chung | 1 người (Tống Thị Thái Hà) | **13 người** | 🔴 Lan rộng |
| Áp trần tiêu chí chung = 20 | Không thấy | **18 người** | 🔴 Lỗi mới |
| Mã công chức trùng | 14 → 1 | **0** | 🟢 Đã sửa |
| Thiếu mức "Không đánh giá" | Có | **Vẫn còn** | ⚪ Chưa sửa |
| Cột Ghi chú rỗng 100% | Có | **Vẫn còn** | ⚪ Chưa sửa |
| Tỷ lệ khớp hoàn toàn | Không đo được (scan) | **87,8%** | – |

---

## 9. VIỆC CẦN XỬ LÝ

### Phía hệ thống

1. **[P0]** Sửa lỗi **áp trần tiêu chí chung = 20** (18 người, mục 2.1). Đây là lỗi nâng điểm → 18 người đang được A/B cao hơn thực tế. Tập trung ở HQCK cảng Hòn Gai.
2. **[P0]** Sửa lỗi **mất điểm tiêu chí chung** (13 người, mục 2.2). Tập trung ở Phòng Tổ chức cán bộ.
3. **[P0]** Sửa lỗi **Lãnh đạo Chi cục = 0 điểm** (4 người). Tồn tại từ T01, đã 5 tháng chưa xử lý, và đang xấu đi.
4. **[P0]** Kiểm tra **điểm vượt trần**: Lương Ngọc Thành và Đỗ Thế Anh có 91,0 trong khi trần là 90.
5. **[P1]** Điều tra 6 ca nhóm "khác" (mục 2.5), nặng nhất là Nguyễn Thị Thúy Hà (84,1 → 69,99).
6. **[P1]** Bổ sung trạng thái **"Không đánh giá"** (nghỉ thai sản, chấm dứt HĐLĐ, chuyển đơn vị).
7. **[P1]** Rà quân số: bổ sung **Bùi Anh Luận**, **Bùi Quang Tiến**; xác minh **Vương Trọng Dũng** (thừa, điểm 0).
8. **[P2]** Cho phép nhập **Ghi chú** và tách 2 cột `Điểm tiêu chí chung` / `Điểm KPI` để đối chiếu được với phụ lục đơn vị.

### Phía đơn vị

9. **[P0]** **HQCK Hoành Mô** — rà lại 11 dòng ghi `20 + 70 = 89,5` (mục 4.1). Nếu tính đúng, 11 người này phải là **mức A**, hiện đang bị hạ oan xuống B. Cần làm rõ là lỗi công thức hay chủ ý.
10. **[P1]** **HQCK cảng Cẩm Phả** — sửa cột tổng của Phùng Thị Nguyên Hạnh: 69,93 → **89,93**.
11. **[P1]** Rà lại 24 ca lệch nhỏ < 0,6 (mục 2, nhóm 5) — xác định do làm tròn hay nhập lệch.

---

## 10. GHI CHÚ CHO XỬ LÝ TỰ ĐỘNG

- **Khóa nối:** `Mã công chức` chỉ có ở phía HT; PL không có mã → phải nối theo `Họ và tên` + `Đơn vị` + năm sinh.
- **Bẫy so khớp tên (đã gặp thực tế ở T5):**
  - Khác dấu: `Nguyễn Thị Thuý Hà` (HT) ↔ `Nguyễn Thị Thúy Hà` (PL); `Vũ Thị Thuỷ` ↔ `Vũ Thị Thủy`
  - Sai chính tả: `Đặng Tích Khoa` (HT) ↔ `Đăng Tích Khoa` (PL); `Trần Văn Tuyển` ↔ `Trần Văn Tuyên`; `Vũ Thị Hiền` ↔ `Vũ Thị Hiên`
  - Thiếu chữ đệm: `Nguyễn Thị Thu Hường` (HT) ↔ `Nguyễn Thu Hường` (PL)
  - Khoảng trắng thừa: `Trần  Văn Giảng` (HT, 2 dấu cách)
  - **Hậu tố năm sinh KHÔNG được bỏ khi so khớp** — có các cặp thật sự khác người: `Nguyễn Thị Thanh Vân 1989/1990`, `Bùi Thị Huyền 1980/1985`, `Nguyễn Đức Tuệ 1971/1985`, `Nguyễn Minh Tuấn 1966/1986`, `Nguyễn Anh Tuấn 1972/1981/1984`, `Nguyễn Thị Thuý Nga 1973/1978`, `Trần Mạnh Hùng 1970/1974`, `Nguyễn Viết Cường 1971/1988`, `Nguyễn Thanh Quang 1970/1975`. Ngoài ra **hậu tố năm sinh giữa HT và PL không thống nhất** (VD: HT `Phạm Thị Lan Hương 1987` ↔ PL `Phạm Thị Lan Hương`) → phải đối chiếu thêm cột `Năm sinh` của HT.
- **Tên đơn vị viết khác nhau:** HT `Phòng Quản lý rủi ro` ↔ PL `Phòng QLRR`; HT `Phòng Công nghệ thông tin` ↔ PL `Phòng CNTT`; HT `Đội Phúc tập và Kiểm tra sau thông quan` ↔ PL `Đội Phúc tập và KTSTQ`.
- **Không so khớp điểm bằng `==`** — dùng dung sai ±0,006 (PL dùng 2 chữ số thập phân).
- **Không tin cột `Điểm theo dõi đánh giá` của PL** — 13 dòng sai số học. Luôn tính lại `chung + KPI`.
- `Pl_Tháng_5_2026.pdf` **có lớp text**, `pdftotext -layout` bóc tách được đầy đủ (khác `QĐ_T1.pdf` là scan).
- Dữ liệu đã bóc tách: `T5_HeThong_546dong.csv`, `T5_PhuLuc_548dong.csv`, `T5_DoiChieu_ChiTiet.csv` (bảng ghép đầy đủ có cột nguyên nhân).
