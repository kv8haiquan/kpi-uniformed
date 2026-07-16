# Kiểm chứng cơ chế bình chọn Đơn vị (Roster_Vote) — T4 & T5/2026
## Chi cục Hải quan khu vực VIII

**Ngày lập:** 15/07/2026
**Nguồn:** `Roster_Vote_T04.csv` (540 dòng) · `Roster_Vote_T05.csv` (540 dòng) · đối chiếu với `PL4`/`PL5` (548 dòng, đã kiểm chứng khớp Thông báo)

---

## 1. KẾT LUẬN

🟢 **Cột `Đơn vị (VOTE)` chính xác 100%** ở cả hai tháng — không sai một ca nào. Cơ chế bình chọn đã giải được đúng bài toán "đơn vị theo kỳ" mà tôi nêu ở báo cáo trước.

🔴 **Nhưng bản xuất docx KHÔNG dùng cột VOTE.** Nó vẫn lấy từ `hồ sơ`/`heuristic`. Toàn bộ **6 ca sai đơn vị còn lại** (4 ở T4 + 2 ở T5) đều đã được VOTE giải đúng — chỉ là kết quả VOTE chưa được đưa vào luồng xuất.

→ **Việc cần làm gọn nhất trong toàn bộ dự án này: chuyển nguồn trường `Đơn vị` khi xuất sang cột VOTE. Xong là hết sạch lỗi đơn vị.**

---

## 2. ĐỘ CHÍNH XÁC TỪNG NGUỒN (so với PL — chuẩn)

Ghép được **539/540** người ở T4 và **536/540** ở T5 (phần chênh là biến thể chính tả tên, xem mục 6).

| Nguồn | T4 đúng | T4 sai | T4 trống | T4 % | T5 đúng | T5 sai | T5 trống | T5 % |
|---|---|---|---|---|---|---|---|---|
| **Đơn vị (VOTE)** | 539 | 0 | 0 | 100.0% | 536 | 0 | 0 | 100.0% |
| ĐV hồ sơ | 462 | 77 | 0 | 85.7% | 534 | 2 | 0 | 99.6% |
| ĐV heuristic(đang xuất) | 535 | 4 | 0 | 99.3% | 536 | 0 | 0 | 100.0% |
| ĐV người-duyệt | 525 | 0 | 14 | 100.0% | 522 | 2 | 12 | 99.6% |
| ĐV kê-khai | 397 | 0 | 142 | 100.0% | 394 | 2 | 140 | 99.5% |

**Đọc bảng:**
- **VOTE: 100% / 100%** — hoàn hảo, và **phủ 100%** (không dòng nào trống).
- **`ĐV hồ sơ`: 85,7% ở T4** — đây đúng là thủ phạm tôi đã chỉ ra: trường này lưu **đơn vị hiện tại**, không có tính lịch sử, nên càng lùi về quá khứ càng sai (T5 gần hiện tại nên 99,6%, T4 xa hơn nên tụt xuống 85,7%).
- **`ĐV heuristic(đang xuất)`: 99,3% / 100%** — tốt nhưng vẫn sót 4 ca ở T4.
- **`ĐV người-duyệt` và `ĐV kê-khai`: 100%** nhưng **độ phủ thấp** (trống 14 và 142 dòng). Chính xác tuyệt đối khi có dữ liệu — đây là lý do VOTE đạt 100%: hai nguồn này bẻ được thế bí ở đúng những ca `hồ sơ` sai.

---

## 3. 🔴 6 CA SAI ĐƠN VỊ CÒN LẠI — VOTE ĐÃ ĐÚNG, DOCX CHƯA LẤY

| Kỳ | Mã CC | Họ và tên | **docx đang xuất** | **VOTE (đúng)** | hồ sơ | heuristic | người-duyệt | kê-khai |
|---|---|---|---|---|---|---|---|---|
| T04 | 20ZZ-0138 | Hoàng Văn Thoại | Phòng Quản lý rủi ro | HQCK quốc tế Móng Cái | Phòng Quản lý rủi ro | Phòng Quản lý rủi ro | HQCK quốc tế Móng Cái | HQCK quốc tế Móng Cái |
| T04 | 20ZZ-0207 | Nguyễn Thanh Quang 1970 | Đội Kiểm soát Hải quan | HQCK quốc tế Móng Cái | Đội Kiểm soát Hải quan | Đội Kiểm soát Hải quan | HQCK quốc tế Móng Cái | HQCK quốc tế Móng Cái |
| T04 | 20ZZ-0513 | Nguyễn Tiến Vinh | Đội Phúc tập và Kiểm tra sau thông quan | HQCK quốc tế Móng Cái | Đội Phúc tập và Kiểm tra sau thông quan | Đội Phúc tập và Kiểm tra sau thông quan | HQCK quốc tế Móng Cái | HQCK quốc tế Móng Cái |
| T04 | 20ZZ-0560 | Phạm Thị Thu Thuỷ | Văn phòng | HQCK quốc tế Móng Cái | Văn phòng | Văn phòng | HQCK quốc tế Móng Cái | HQCK quốc tế Móng Cái |
| T05 | 20ZZ-0018 | Bùi Quang Tiến | HQCK cảng Hòn Gai | HQCK quốc tế Móng Cái | HQCK cảng Hòn Gai | HQCK quốc tế Móng Cái | HQCK quốc tế Móng Cái | (trống) |
| T05 | 20ZZ-0019 | Bùi Anh Luận | HQCK cảng Vạn Gia | Văn phòng | HQCK cảng Vạn Gia | Văn phòng | Văn phòng | (trống) |

**Bốn ca T4** đều cùng một kiểu: `hồ sơ` và `heuristic` giữ đơn vị **hiện tại** (tháng 5), trong khi `người-duyệt` và `kê-khai` giữ đúng đơn vị **tháng 4** (Móng Cái). VOTE chọn đúng. docx lấy nhầm.

**Hai ca T5** (Bùi Quang Tiến, Bùi Anh Luận) là 2 ca tôi đã nêu ở `BaoCao_KiemChung_T05_v3_va_T04.md`. Ở đây thấy rõ: `heuristic` và `người-duyệt` đều **đúng**, chỉ `hồ sơ` sai — nhưng **docx lại đang lấy theo `hồ sơ`** cho 2 người này.

> ⚠ Lưu ý kỹ thuật: ở T4 docx bám theo `heuristic` (540/540), nhưng ở T5 có **2 dòng docx bám theo `hồ sơ` thay vì `heuristic`**. Tức luồng xuất hiện tại **không nhất quán** — không phải luôn dùng một nguồn. Đây là dấu hiệu logic chọn đơn vị khi xuất còn tùy biến, cần thay bằng một quy tắc duy nhất: **lấy VOTE**.

---

## 4. ROSTER THIẾU 8 NGƯỜI MỖI THÁNG

Roster có 540 dòng, PL có 548. Sau khi trừ các biến thể chính tả, **thiếu đúng 8 người mỗi kỳ**.

### T4 — thiếu 8

| STT PL4 | Họ và tên | Đơn vị | Chức vụ | PL điểm | PL mức / ghi chú |
|---|---|---|---|---|---|
| 1 | Phạm Quốc Hưng | Lãnh đạo Chi cục | Chi cục trưởng | 89.7 | B |
| 2 | Bùi Ngọc Lợi | Lãnh đạo Chi cục | Phó Chi cục trưởng | 92.5 | A |
| 3 | Ngô Tùng Dương | Lãnh đạo Chi cục | Phó Chi cục trưởng | 89.9 | B |
| 4 | Nguyễn Cảnh Thắng | Lãnh đạo Chi cục | Phó Chi cục trưởng | 90 | A |
| 188 | Đỗ Xuân Hiền | HQCK quốc tế Móng Cái | Đội trưởng | 90 | A |
| 304 | Hứa Hà Lê | HQCK quốc tế Móng Cái | Công chức | – | Nghỉ thai sản |
| 378 | Nguyễn Thị Thúy Hà | HQCK cảng Hòn Gai | Đội trưởng | 84.2 | B |
| 391 | Trần Thị Khánh Linh | HQCK cảng Hòn Gai | Công chức | – | Nghỉ thai sản |

### T5 — thiếu 8

| STT PL5 | Họ và tên | Đơn vị | Chức vụ | PL điểm | PL mức / ghi chú |
|---|---|---|---|---|---|
| 1 | Phạm Quốc Hưng | Lãnh đạo Chi cục | Chi cục trưởng | 95 | A |
| 3 | Ngô Tùng Dương | Lãnh đạo Chi cục | Phó Chi cục trưởng | 89.9 | B |
| 4 | Nguyễn Cảnh Thắng | Lãnh đạo Chi cục | Phó Chi cục trưởng | 90 | A |
| 43 | Vũ Văn Lưu | Văn phòng | Hợp đồng 111 | – | Không đánh giá (chấm dứt HĐLĐ theo |
| 200 | Hứa Hà Lê | HQCK quốc tế Móng Cái | Công chức | – | Nghỉ thai sản |
| 398 | Trần Thị Khánh Linh | HQCK cảng Hòn Gai | Công chức | – | Nghỉ thai sản |
| 457 | Phùng Thị Nguyên Hạnh | HQCK cảng Cẩm Phả | Đội trưởng | 69.93 | B |
| 494 | Vũ Đức Dũng | HQCK cảng Vạn Gia | Đội trưởng | 90 | A |

**Nhận xét:**
- **Lãnh đạo Chi cục** vắng mặt ở cả hai kỳ (T4 thiếu cả 4; T5 thiếu 3 — **Bùi Ngọc Lợi có mặt**). Trùng khớp với lỗi lãnh đạo đã theo dai dẳng từ T01.
- **Hứa Hà Lê** và **Trần Thị Khánh Linh** (nghỉ thai sản) vắng ở cả hai kỳ — hệ quả của việc thiếu trạng thái "Không đánh giá".
- 🔍 **T5 thiếu thêm 2 Đội trưởng mà T4 lại có: Phùng Thị Nguyên Hạnh và Vũ Đức Dũng.** Cả hai đều nằm trong danh sách lệch mức của báo cáo T5 v3. Cần làm rõ vì sao họ bị loại khỏi Roster T5.
- **Nguyễn Thị Thúy Hà** (Đội trưởng Hòn Gai) vắng ở Roster T4 nhưng có ở T5.

---

## 5. PHẦN ĐIỂM: ROSTER SAO Y BẢN XUẤT — LỖI CŨ CÒN NGUYÊN

Đã kiểm chứng: **điểm trong Roster khớp 540/540 với bản xuất docx mới nhất** ở cả hai kỳ. Roster không sửa gì về điểm, chỉ bổ sung thông tin đơn vị.

Vì vậy các lỗi điểm vẫn nguyên:

| Kỳ | Cặp so được | Khớp (điểm + mức) | Lệch mức |
|---|---|---|---|
| T4 | 539 | 480 (89,1%) | **40** |
| T5 | 536 | 498 (92,9%) | **6** |

### T4 — 40 ca lệch mức, phân rã

| Nguyên nhân | Số ca |
|---|---|
| Mất trọn 70 điểm KPI (HĐ 111) | 19 |
| Khác | 13 |
| Chênh làm tròn quanh ngưỡng 90 | 8 |

Trong đó **30 ca là HĐ 111 mất trọn 70 điểm KPI** — điểm chỉ còn 14,5–20 → xếp D. Tập trung ở Hòn Gai, Cẩm Phả, Vạn Gia. Đây vẫn là lỗi nghiêm trọng nhất chưa xử lý.

### T5 — 6 ca lệch mức

| Mã CC | Họ và tên | Đơn vị | PL5 | Roster | Δ |
|---|---|---|---|---|---|
| 20ZZ-0211 | Dương Thanh Hà | Phòng Tổ chức cán bộ | 90 A | 89.50 B | -0.50 |
| 20ZZ-0042 | Đoàn Hồng Chinh | Phòng Tổ chức cán bộ | 89.5 B | 19.50 D | -70.00 |
| 20ZZ-0205 | Trương Anh Tuấn | Phòng CNTT | 89.5 B | 90.00 A | +0.50 |
| 20ZZ-0112 | Bùi Thị Huyền | Phòng CNTT | 89.5 B | 90.00 A | +0.50 |
| 20ZZ-0093 | Nguyễn Thị Hương | HQCK cảng Hòn Gai | 90 A | 70.00 B | -20.00 |
| 20ZZ-0071 | Vũ Văn Nam | HQCK cảng Vạn Gia | 85 B | 90.00 A | +5.00 |

> Ít hơn con số 12 ở báo cáo T5 v3, vì Roster đã thiếu sẵn 5 người trong nhóm lệch (3 lãnh đạo + Vũ Đức Dũng + Phùng Thị Nguyên Hạnh). **Không phải đã sửa được** — chỉ là họ không có trong Roster.

---

## 6. GHI CHÚ CHO XỬ LÝ TỰ ĐỘNG

- **Không bỏ dấu tiếng Việt khi so tên.** Tôi đã thử và tạo ra **2 lỗi giả**: `Trần Văn Tuyển` (Hòn Gai) bị lẫn với `Trần Văn Tuyên` (Hoành Mô), và `Vũ Thị Hiền` (Móng Cái) bị lẫn với `Vũ Thị Hiên` (Văn phòng). Đây là **4 người khác nhau**. Chuẩn hóa về NFC, giữ nguyên dấu.
- **Biến thể chính tả giữa Roster và PL** (đã xác minh là cùng người): `Đăng Tích Khoa` (PL) ↔ `Đặng Tích Khoa` (Roster) · `Nguyễn Thị Thúy Hà` ↔ `Nguyễn Thị Thuý Hà` · `Nguyễn Thu Hường` ↔ `Nguyễn Thị Thu Hường` · `Vũ Thị Thủy` ↔ `Vũ Thị Thuỷ`.
- **Mã `"20ZZ - 0223"`** (Hà Thị Kim Thanh) vẫn có dấu cách quanh gạch nối — trong chính file Roster. Phải `replace(' ','')` trước khi nối theo mã.
- **Tên đơn vị viết khác nhau giữa các nguồn:** Roster/PL dùng `Phòng QLRR`, `Phòng CNTT`, `Đội Phúc tập và KTSTQ`; docx dùng dạng đầy đủ `Phòng Quản lý rủi ro`, `Phòng Công nghệ thông tin`, `Đội Phúc tập và Kiểm tra sau thông quan`. Cần bảng ánh xạ.
- Dung sai so khớp điểm: **PL4 ±0,10** (cắt cụt 1 chữ số thập phân) · **PL5 ±0,006**.

---

## 7. VIỆC CẦN LÀM

| # | Việc | Ưu tiên | Ghi chú |
|---|---|---|---|
| 1 | **Chuyển trường `Đơn vị` khi xuất sang lấy từ cột VOTE** | **P0** | Giải quyết trọn 6/6 ca sai đơn vị. Việc dễ nhất, hiệu quả cao nhất |
| 2 | **29–30 ca HĐ 111 mất điểm KPI ở T4** | **P0** | Lỗi nặng nhất còn lại. T5 không có → so cấu hình 2 kỳ |
| 3 | **Lãnh đạo Chi cục**: T4 thiếu cả 4, T5 thiếu 3 (Bùi Ngọc Lợi có) | **P0** | Kéo dài từ T01. So bản ghi ông Lợi để tìm khác biệt |
| 4 | Làm rõ vì sao Roster T5 thiếu Phùng Thị Nguyên Hạnh và Vũ Đức Dũng | P1 | T4 có, T5 không |
| 5 | Bổ sung trạng thái **"Không đánh giá"** | P1 | Xử lý gọn Hứa Hà Lê, Trần Thị Khánh Linh, Vũ Văn Lưu |
| 6 | Nâng độ phủ `ĐV kê-khai` (đang trống 142/540 ≈ 26%) | P2 | VOTE đang tốt, nhưng phủ càng cao càng bền |
| 7 | Chuẩn hóa chính tả tên và mã `"20ZZ - 0223"` | P2 | |
| 8 | T5: 6 ca lệch mức (mục 5) | P2 | Đã nêu ở báo cáo T5 v3 |

---

## 8. TÓM TẮT DIỄN BIẾN

| Lỗi | T01 | T4 | T5 | Hiện tại |
|---|---|---|---|---|
| Trưởng đơn vị điểm cứng 35 | 9 | 0 | 0 | 🟢 Xong |
| Người ≥90 chỉ xếp B | 121 | 0 | 0 | 🟢 Xong |
| Cột Ghi chú rỗng | 100% | 12 dòng | 4 dòng | 🟢 Xong |
| Sai đơn vị | – | 80 → **4** | – → **2** | 🟡 **VOTE đã giải đúng, chờ đưa vào luồng xuất** |
| HĐ 111 mất KPI | 41 → 0 | **~30** | 0 | 🔴 Còn ở T4 |
| Lãnh đạo Chi cục | 4 (điểm 0) | **4 (mất bản ghi)** | 3 (mất điểm chung) | 🔴 Còn |
| Trạng thái "Không đánh giá" | Không có | Không có | Không có | 🔴 Chưa làm |
