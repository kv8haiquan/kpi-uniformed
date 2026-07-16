# Kiểm chứng bản xuất T4/2026 lần 3 (`__3_`)
## Chi cục Hải quan khu vực VIII

**Ngày lập:** 15/07/2026
**Bổ sung cho:** `BaoCao_DoiChieu_T04_2026_BAN2.md`

---

## 1. LẦN NÀY DỮ LIỆU ĐÃ THẬT SỰ ĐỔI

| | `__1_` / `__2_` | **`__3_`** |
|---|---|---|
| Thời điểm xuất | 15/07 17:19 · 16/07 11:05 | **16/07 13:52** |
| md5 `word/document.xml` | `8da6145260…` (cả hai giống nhau) | **`97b15b6062…`** ✅ đổi |
| Số dòng | 544 | **545** |

## 2. NỘI DUNG THAY ĐỔI: **CHỈ SỬA ĐƠN VỊ**

| Loại thay đổi | Số lượng |
|---|---|
| Bản ghi được thêm | **1** (Vũ Văn Lưu) |
| Bản ghi bị bớt | 0 |
| Bản ghi đổi **Đơn vị** | **73** |
| Bản ghi đổi **Điểm** | **0** |
| Bản ghi đổi **Mức** | **0** |
| Bản ghi đổi Chức vụ / Họ tên / Năm sinh | **0** |

→ Đợt sửa này **chỉ chạm vào trường Đơn vị**. Toàn bộ điểm và mức xếp loại giữ nguyên.

---

## 3. ✅ SỬA ĐƠN VỊ: RẤT THÀNH CÔNG

| | `__2_` | **`__3_`** |
|---|---|---|
| Đơn vị **đúng** so với PL4 | 462 | **536** |
| Đơn vị **sai** | **80** | **4** |

**70/73 ca đổi đơn vị là khớp đúng PL4** (2 ca khớp cả PL4 lẫn PL5, 1 ca không khớp nguồn nào). Sai đơn vị giảm **95%**.

### 🔍 4 ca còn sai đều cùng một kiểu — và chỉ ra một lỗi thiết kế

| Mã CC | Họ và tên | Chức vụ | PL4 (tháng 4) | HT4-v3 |
|---|---|---|---|---|
| 20ZZ-0138 | Hoàng Văn Thoại | Công chức | HQCK quốc tế Móng Cái | Phòng QLRR |
| 20ZZ-0513 | Nguyễn Tiến Vinh | Công chức | HQCK quốc tế Móng Cái | Đội Phúc tập và KTSTQ |
| 20ZZ-0207 | Nguyễn Thanh Quang 1970 | Công chức | HQCK quốc tế Móng Cái | Đội Kiểm soát Hải quan |
| 20ZZ-0560 | Phạm Thị Thu Thuỷ | Công chức | HQCK quốc tế Móng Cái | Văn phòng |

**Cả 4 người đều: PL4 (tháng 4) ghi ở Móng Cái, PL5 (tháng 5) ghi ở đơn vị mới, và hệ thống dùng đơn vị của tháng 5.**

→ **Trường `Đơn vị` trên hệ thống không có tính lịch sử.** Nó lưu đơn vị **hiện tại** của người đó, chứ không phải đơn vị tại thời điểm của kỳ đánh giá. Vì vậy khi xuất lại một tháng cũ, những ai đã chuyển đơn vị sẽ hiện đơn vị mới — làm sai thống kê theo đơn vị của tháng đó.

Kiểm chứng: HT4-v3 có **5 ca khớp PL5 nhưng lệch PL4**, và **0 ca ngược lại**. Quân số Móng Cái: PL4 = 134 · PL5 = 137 · HT4-v3 = **132**.

> **Đây không phải lỗi nhập liệu mà là lỗi mô hình dữ liệu.** Cần lưu đơn vị theo từng kỳ đánh giá (snapshot), nếu không thì mọi báo cáo tháng cũ xuất lại đều sẽ sai dần theo thời gian.

---

## 4. 🔴 ĐIỂM SỐ: KHÔNG SỬA GÌ — 40 CA LỆCH MỨC VẪN NGUYÊN

| Chỉ tiêu | `__2_` | **`__3_`** | PL4/TB4 (chuẩn) |
|---|---|---|---|
| Tổng số | 544 | **545** | 548 |
| A | 211 | **211** | 223 |
| B | 297 | **297** | 320 |
| C | 3 | **3** | 2 |
| **D** | 33 | **34** | **1** |
| **Lệch mức** | 40 | **40** | – |

### Nguyên nhân lệch điểm thực chất (đã loại chênh làm tròn)

| Nhóm | Số ca | Ghi chú |
|---|---|---|
| **HĐ 111 mất điểm KPI** | **29** | Vạn Gia 10 · Hòn Gai 9 · Cẩm Phả 8 · Móng Cái 1 · Văn phòng 1 |
| Khác (HĐ 111 sai điểm kiểu khác) | 22 | |
| Áp trần chung = 20 | 4 | |
| Mất điểm tiêu chí chung | 2 | |

**Toàn bộ 29 ca mất KPI đều là Hợp đồng 111** — không sót một Công chức nào. Đây là lỗi khu trú rất rõ theo loại hợp đồng.

### ⚠ Vũ Văn Lưu — được thêm vào nhưng thêm sai

| | Giá trị |
|---|---|
| PL4 | 14,5 + **70** = **84,5** → **B** |
| HT4-v3 | **14,5** → **D** |

Người này vừa được bổ sung ở bản `__3_`, nhưng **mất trọn 70 điểm KPI** — rơi đúng vào lỗi HĐ 111. Việc bổ sung làm số D tăng từ 33 lên **34**.

### Nhóm D trên HT4-v3 (34 người) phân rã

| Thành phần | Số người | Đúng/Sai |
|---|---|---|
| HĐ 111 mất điểm KPI (điểm 14,5–20) | **29** | ❌ Sai |
| Nghỉ thai sản bị xếp D (Hứa Hà Lê, Trần Thị Khánh Linh — 0 điểm) | **2** | ❌ Sai |
| Bản ghi rác 0 điểm (Dương Việt Cường, Vũ Minh Đức) | **2** | ❌ Sai |
| Nguyễn Minh Đức (49,16) | **1** | ✅ Đúng |

**Chỉ 1/34 ca mức D là đúng.**

---

## 5. CÁC VẤN ĐỀ CHƯA ĐỘNG TỚI

| Vấn đề | Trạng thái |
|---|---|
| **Lãnh đạo Chi cục — không có bản ghi nào** (Phạm Quốc Hưng, Bùi Ngọc Lợi, Ngô Tùng Dương, Nguyễn Cảnh Thắng) | ❌ vẫn thiếu |
| **Đỗ Xuân Hiền** (Đội trưởng Móng Cái, PL4: 90 → A, ghi chú *chuyển công tác từ 28/4/2026*) | ❌ vẫn thiếu |
| **Dương Việt Cường, Vũ Minh Đức** — 0 điểm, trống chức vụ | ❌ bản ghi rác vẫn còn |
| **Hứa Hà Lê, Trần Thị Khánh Linh** — nghỉ thai sản, 0 điểm → D | ❌ vẫn sai (thiếu trạng thái "Không đánh giá") |
| **29 HĐ 111 mất điểm KPI** | ❌ chưa sửa |
| **8 bản ghi trống Chức vụ** | ❌ vẫn 8 |
| **Mã `"20ZZ - 0223"`** (Hà Thị Kim Thanh) | ❌ vẫn sai |

Cân đối quân số: 545 + 5 (4 lãnh đạo + Đỗ Xuân Hiền) − 2 (rác) = 548 ✓

---

## 6. VIỆC CẦN LÀM TIẾP

1. **[P0]** **29 ca HĐ 111 mất điểm KPI ở T4.** Lỗi này T5 không có → so cấu hình/công thức giữa hai kỳ để tìm khác biệt. Nhớ Vũ Văn Lưu vừa thêm cũng rơi vào lỗi này.
2. **[P0]** **Khôi phục 4 bản ghi Lãnh đạo Chi cục cho T4** (T5 đã có, T4 vẫn trắng).
3. **[P0]** **Trường `Đơn vị` cần lưu theo kỳ (snapshot), không lấy đơn vị hiện tại.** Đây là lỗi mô hình dữ liệu — hiện đã làm sai 4 người ở T4 và sẽ sai nhiều thêm mỗi khi có người chuyển đơn vị.
4. **[P1]** Bổ sung trạng thái **"Không đánh giá"** — sẽ xử lý gọn 2 ca thai sản (T4) và Vũ Văn Lưu (T5).
5. **[P1]** Bổ sung **Đỗ Xuân Hiền**; xóa/nạp điểm cho Dương Việt Cường và Vũ Minh Đức.
6. **[P2]** 4 ca áp trần chung = 20; 2 ca mất chung; 8 bản ghi trống chức vụ; mã `"20ZZ - 0223"`.

---

## 7. GHI CHÚ CHO XỬ LÝ TỰ ĐỘNG

- **Trường `Đơn vị` không đáng tin để ghép giữa các kỳ** — hệ thống lưu đơn vị hiện tại, không phải đơn vị tại thời điểm đánh giá (mục 3).
- Dung sai so khớp điểm HT↔PL4: **±0,10** (PL4 cắt cụt 1 chữ số thập phân).
- **Bẫy tên khi ghép HT4↔PL4:** `Nguyễn Thị Thuý Hà` (HT) ↔ `Nguyễn Thị Thúy Hà` (PL4); `Đặng Tích Khoa` (HT) ↔ `Đăng Tích Khoa` (PL4). Chuẩn hóa dấu là bắt buộc — **nhưng không được bỏ dấu hoàn toàn**, vì `Vũ Thị Hiên` (Văn phòng) và `Vũ Thị Hiền` (Móng Cái) là hai người khác nhau.
- Dữ liệu: `T4_HeThong_v3_545dong.csv`, `T4_DoiChieu_ChiTiet_v3.csv`.
