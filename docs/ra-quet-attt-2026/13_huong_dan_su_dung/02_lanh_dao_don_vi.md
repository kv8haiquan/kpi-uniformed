# HƯỚNG DẪN SỬ DỤNG — DÀNH CHO LÃNH ĐẠO ĐƠN VỊ

**Đối tượng:** Trưởng đơn vị (TDV), Phó đơn vị (PDV) — 50 người  
**Phiên bản:** Tháng 10/2026

---

## MỤC LỤC

1. [Tổng quan vai trò và quyền hạn](#1-tổng-quan-vai-trò-và-quyền-hạn)
2. [Phê duyệt kê khai công việc](#2-phê-duyệt-kê-khai-công-việc)
3. [Duyệt tiêu chí chung theo quý](#3-duyệt-tiêu-chí-chung-theo-quý)
4. [Đánh giá và phiếu nhận xét](#4-đánh-giá-và-phiếu-nhận-xét)
5. [Phân công phụ trách](#5-phân-công-phụ-trách)
6. [Chỉ tiêu đơn vị (TDV)](#6-chỉ-tiêu-đơn-vị-tdv)
7. [Kê khai công việc của lãnh đạo](#7-kê-khai-công-việc-của-lãnh-đạo)
8. [Lỗi thường gặp](#8-lỗi-thường-gặp)

---

## 1. Tổng quan vai trò và quyền hạn

### 1.1. Vai trò của TDV/PDV

| Vai trò | Phạm vi quản lý | Quyền duyệt |
|---------|-----------------|-------------|
| **Phó đơn vị (PDV)** | Công chức do PDV trực tiếp phụ trách (theo phân công) | Duyệt cấp 1 kê khai, tiêu chí chung |
| **Trưởng đơn vị (TDV)** | Toàn bộ công chức trong đơn vị | Duyệt cấp 1 và cấp 2 kê khai, tiêu chí chung; Duyệt phiếu đánh giá |

### 1.2. Quy trình 2 cấp duyệt

```
Công chức kê khai → PDV/TDV duyệt cấp 1 → TDV duyệt cấp 2 → Hoàn tất
```

**Lưu ý:**
- **Duyệt thẳng (1 cấp):** Nếu TDV duyệt trực tiếp → hệ thống tự ghi cả cấp 1 và cấp 2.
- **PDV không duyệt cấp 2:** Chỉ TDV (hoặc lãnh đạo cao hơn: PCCT, CCT) mới duyệt cấp 2.

### 1.3. Đường dẫn chính

Dashboard → Thanh bên trái → **Phê duyệt** (thực tế là trang `/xep-loai` với nhiều tab)

*(ảnh minh họa bổ sung khi in)*

---

## 2. Phê duyệt kê khai công việc

### 2.1. Mục đích

Thẩm định, phê duyệt kê khai công việc của công chức trong đơn vị. Chỉ những kê khai **Đã duyệt** mới được tính điểm KPI.

### 2.2. Ai dùng

PDV, TDV (theo phạm vi phân công).

### 2.3. Đường dẫn

Dashboard → **Phê duyệt** (`/xep-loai?tab=cong-viec`) → Tab **Công việc**

### 2.4. Các bước duyệt từng bản

**Bước 1: Chọn tháng, năm cần duyệt**

- Ở góc trên, chọn **Tháng** và **Năm** từ danh sách thả xuống

**Bước 2: Xem danh sách chờ duyệt**

Tab **Công việc** hiển thị:
- Số lượng chờ duyệt (badge màu vàng bên cạnh tên tab)
- Bảng danh sách công chức và kê khai chờ duyệt

Mỗi dòng hiển thị:
- Tên công chức, mã công chức
- Tên công việc
- Số lượng
- Ngày thực hiện
- Minh chứng
- Trạng thái

**Bước 3: Xem chi tiết kê khai**

- Bấm vào dòng kê khai để mở chi tiết
- Kiểm tra:
  - Tên công việc có đúng không
  - Số lượng có hợp lý không
  - Minh chứng có rõ ràng không

**Bước 4: Phê duyệt hoặc Từ chối**

**Nếu đồng ý:**
1. Bấm nút **"Phê duyệt"** (màu xanh)
2. Hệ thống hỏi xác nhận → Bấm **"Xác nhận"**
3. Trạng thái chuyển sang:
   - **Chờ duyệt cấp 2** (nếu bạn là PDV hoặc TDV duyệt cấp 1)
   - **Đã duyệt** (nếu bạn là TDV duyệt thẳng hoặc duyệt cấp 2)

**Nếu không đồng ý:**
1. Bấm nút **"Từ chối"** (màu đỏ)
2. **Bắt buộc nhập lý do từ chối** (rõ ràng, cụ thể)
3. Bấm **"Xác nhận"**
4. Kê khai trả về trạng thái **Từ chối**, công chức sẽ nhận thông báo và phải sửa lại

**Lưu ý:**
- **Lý do từ chối phải rõ ràng:** "Số lượng không khớp với minh chứng", "Công việc này không thuộc phạm vi của bạn", v.v.
- **Không từ chối chung chung:** "Không đúng", "Sai" → công chức không biết sửa chỗ nào.

### 2.5. Duyệt hàng loạt (bulk)

**Mục đích:** Duyệt nhiều bản kê khai cùng lúc, tiết kiệm thời gian.

**Các bước:**

1. Tick vào **ô checkbox** đầu mỗi dòng kê khai muốn duyệt
2. Hoặc tick **ô checkbox ở tiêu đề bảng** để chọn tất cả
3. Bấm nút **"Duyệt hàng loạt"** (xuất hiện khi có ít nhất 1 bản được chọn)
4. Hệ thống hỏi xác nhận: "Duyệt ... bản kê khai?"
5. Bấm **"Xác nhận"**

**Lưu ý:**
- Chỉ duyệt hàng loạt khi **chắc chắn tất cả đều đúng**.
- Nếu có nghi ngờ, duyệt **từng bản** để kiểm tra kỹ.

### 2.6. Xử lý trường hợp công chức điều chuyển đơn vị giữa kỳ

Nếu công chức **chuyển đơn vị** trong tháng, hệ thống tự xử lý:
- Kê khai **trước ngày chuyển:** Lãnh đạo đơn vị **cũ** duyệt
- Kê khai **sau ngày chuyển:** Lãnh đạo đơn vị **mới** duyệt

**Lưu ý:** Hệ thống **tự phân quyền** dựa trên ngày hiệu lực điều chuyển — không cần thao tác thủ công.

### 2.7. Lưu ý nghiệp vụ

- **Hạn duyệt:** Trước ngày **23** tháng cuối quý (hạn nộp hồ sơ về TCCB). Lưu ý: kê khai vẫn theo **tháng**, dù kỳ đánh giá là quý.
- **Kiểm tra kỹ minh chứng:** Đảm bảo công việc thực sự đã hoàn thành.
- **Lỗi chất lượng/tiến độ:** Nếu phát hiện lỗi, có thể **ghi chú lỗi** (hệ thống tự trừ 25% điểm/lỗi).

---

## 3. Duyệt tiêu chí chung theo quý

### 3.1. Mục đích

Duyệt tiêu chí chung (31 tiêu chí, 30 điểm) mà công chức đã tự chấm. Từ **Quý III/2026**, tiêu chí chung chấm **MỘT LẦN** cho cả quý.

### 3.2. Ai dùng

PDV, TDV (theo phạm vi phân công).

### 3.3. Đường dẫn

Dashboard → **Phê duyệt** (`/xep-loai?tab=tieu-chi`) → Tab **Tiêu chí chung**

### 3.4. Các bước duyệt

**Bước 1: Chọn quý, năm**

- Chọn **Quý** (Q1, Q2, Q3, Q4) và **Năm** từ danh sách thả xuống

**Bước 2: Xem danh sách chờ duyệt**

Bảng hiển thị:
- Tên công chức
- Trạng thái (Chờ duyệt cấp 1 / Chờ duyệt cấp 2)
- Tổng điểm tự chấm (tối đa 30)
- Cột **Hành động**

**Bước 3: Xem chi tiết tiêu chí**

- Bấm vào dòng công chức
- Hệ thống hiển thị 31 tiêu chí, mỗi tiêu chí có:
  - Điểm tự chấm của công chức
  - Ô điều chỉnh (nếu cần)

**Bước 4: Điều chỉnh điểm (nếu cần)**

- Mỗi tiêu chí có ô nhập điểm (input number) để điều chỉnh
- Nhập điểm mới theo **bội số 0.5**: 0; 0,5; 1,0; 1,5; ... đến tối đa điểm tiêu chí
- **Nếu đồng ý với điểm tự chấm:** Không cần nhập gì (để trống → giữ nguyên điểm tự chấm)
- **Nếu không đồng ý:** Nhập điểm mới

**Bước 5: Phê duyệt hoặc Trả lại**

**Nếu đồng ý:**
1. Bấm nút **"Phê duyệt"**
2. Trạng thái chuyển sang:
   - **Chờ duyệt cấp 2** (nếu bạn duyệt cấp 1)
   - **Đã duyệt** (nếu bạn duyệt cấp 2)

**Nếu không đồng ý:**
1. Bấm nút **"Trả lại"**
2. Nhập **lý do trả lại**
3. Công chức nhận thông báo, phải chấm lại

### 3.5. Duyệt hàng loạt tiêu chí

- Tick chọn nhiều công chức
- Bấm **"Duyệt hàng loạt"**

**Lưu ý:** Duyệt hàng loạt **giữ nguyên điểm tự chấm** — không điều chỉnh. Chỉ dùng khi đồng ý với điểm tự chấm của tất cả công chức được chọn.

### 3.6. Lưu ý nghiệp vụ

- **Nhóm 1, 2** (Phẩm chất, Năng lực): Mặc định Đạt — chỉ giảm điểm nếu có khuyết điểm.
- **Nhóm 3** (Sáng tạo): Kiểm tra **minh chứng cụ thể** trước khi duyệt.
- **Điểm thập phân:** Chấm theo bội số **0.5** — chỉ chấm 0; 0,5; 1,0; 1,5; 2,0;... không chấm 1,2 hoặc 1,7.
- **Từ Q3/2026 (CV 21169):** Tiêu chí chung chấm MỘT LẦN cho cả quý, không chấm 3 tháng riêng. Kê khai công việc vẫn theo tháng.

---

## 4. Đánh giá và phiếu nhận xét

### 4.1. Phiếu nhận xét, đánh giá quý

**Mục đích:** Lập phiếu đánh giá quý (Mẫu 02A/02B) cho công chức/lãnh đạo trong đơn vị.

**Đường dẫn:** Dashboard → **Phê duyệt** → Tab **Quý** (hoặc từ trang **Đánh giá**)

**Các bước:**

**Bước 1: Chọn quý, năm**

**Bước 2: Xem/lập phiếu**

- Chọn công chức từ bảng
- Phiếu sẽ hiển thị hoặc cho phép điền nếu chưa có

**Bước 3: Điền phiếu đánh giá**

Phiếu gồm 5 phần:

| Phần | Nội dung | Ai điền |
|------|----------|---------|
| **I — Kết quả công việc** | Điểm KPI (a, b, c), tổng điểm KPI | Hệ thống tự tính |
| **II — Tiêu chí chung** | 31 tiêu chí, tổng 30 điểm | Hệ thống tự tính từ đánh giá đã duyệt |
| **III — Tự đề xuất** | Công chức tự đề xuất xếp loại A/B/C/D | Công chức tự điền |
| **IV — Nhận xét** | Nhận xét của lãnh đạo đơn vị | **TDV điền** |
| **V — Quyết định** | Quyết định xếp loại chính thức | CCT quyết định |

**Bước 4: TDV điền phần "Nhận xét"**

- Nhập nhận xét về:
  - Ưu điểm, kết quả nổi bật
  - Hạn chế, khuyết điểm (nếu có)
  - Đề xuất xếp loại của TDV
- Bấm **"Lưu"**

**Bước 5: Lưu và gửi (nếu cần)**

- Sau khi điền xong, bấm **"Lưu"**
- Phiếu được lưu, CCT sẽ xem khi xếp loại

### 4.2. In phiếu và bảng kê

**Các bước:**

1. Chọn quý, năm
2. Chọn **Đơn vị** (TDV chỉ xem đơn vị mình)
3. Chọn định dạng xuất (hệ thống hỗ trợ xuất file)
4. File tải về máy

**Loại bản in:**

- **Mẫu 02A:** Phiếu đánh giá xếp loại công chức
- **Mẫu 02B:** Phiếu đánh giá xếp loại lãnh đạo
- **Bảng kê:** Danh sách toàn bộ công chức trong đơn vị (dùng khi nộp hồ sơ)

### 4.3. Lưu ý nghiệp vụ

- **Nhận xét phải khách quan, cụ thể:** Không nên chung chung "hoàn thành tốt nhiệm vụ".
- **Hạn chế, khuyết điểm:** Nêu rõ (nếu có) để công chức biết và khắc phục.
- **Hạn nộp hồ sơ:** Ngày **23** tháng cuối quý.

---

## 5. Phân công phụ trách

### 5.1. Mục đích

TDV phân công PDV phụ trách từng công chức trong đơn vị. Hệ thống dựa vào phân công này để xác định **ai duyệt cấp 1**.

### 5.2. Đường dẫn

Dashboard → Thanh bên trái → **Phân công phụ trách** (`/phan-cong-phu-trach`) (chỉ CCT và admin thấy menu này)

### 5.3. Các bước

1. Bảng hiển thị danh sách công chức trong đơn vị
2. Mỗi dòng có cột **"Người phụ trách"** (dropdown)
3. Chọn **PDV** phụ trách công chức đó
4. Bấm **"Lưu"**

**Lưu ý:**

- Nếu **không phân công PDV:** TDV tự duyệt cấp 1 và cấp 2.
- Nếu **có phân công:** PDV duyệt cấp 1, TDV duyệt cấp 2.

---

## 6. Chỉ tiêu đơn vị (TDV)

### 6.1. Mục đích

Xem, duyệt chỉ tiêu được giao cho đơn vị (theo năm, theo tháng).

### 6.2. Đường dẫn

Dashboard → Nền tảng số → **Chỉ tiêu đơn vị** (`/chi-tieu`)

### 6.3. Các bước

1. Chọn **Năm**
2. Bảng hiển thị danh sách chỉ tiêu:
   - Tên chỉ tiêu
   - Lĩnh vực
   - Số lượng được giao
   - Kết quả đã đạt
   - Trạng thái
3. Bấm vào dòng chỉ tiêu để xem chi tiết
4. Cập nhật kết quả (nếu cần)
5. TDV xem và theo dõi kết quả chỉ tiêu

**Lưu ý:**

- Chỉ tiêu đơn vị **khác với KPI cá nhân** — theo dõi riêng.
- Module mới (từ 04/06/2026), đang ở giai đoạn thử nghiệm.

---

## 7. Kê khai công việc của lãnh đạo

### 7.1. Điểm khác với công chức thường

Lãnh đạo (PDV, TDV, PCCT, CCT) kê khai theo **bộ chỉ số lãnh đạo riêng** (không phải danh mục 2.812 đầu việc).

**Công thức KPI lãnh đạo (từ 04/2026):**

```
KPI lãnh đạo = (a + b + c + d + đ + e) / 6 × 70
```

Trong đó:
- **a, b, c:** Tính từ kê khai công việc (giống công chức)
- **d, đ, e:** Điểm Hội đồng đánh giá lãnh đạo (HDLD) — 3 tiêu chí chất lượng, tuân thủ, hiệu quả

**Phạm vi cộng sản phẩm:**

| Cấp | Phạm vi |
|-----|---------|
| PDV | SP tự kê + SP của công chức do PDV trực tiếp duyệt |
| TDV | Toàn bộ SP của đơn vị (CC + PDV + tự kê) |
| PCCT | Gộp SP các đơn vị mình phụ trách |
| CCT | Gộp SP các khối PCCT phụ trách + đơn vị trực tiếp phụ trách |

### 7.2. Đường dẫn kê khai

Dashboard → **Kê khai công việc** (`/ke-khai-v2`) (trang tự động chọn form lãnh đạo)

**Lưu ý:** Lãnh đạo **vẫn kê khai theo tháng**, nhưng đánh giá tiêu chí chung và xếp loại theo quý.

---

## 8. Lỗi thường gặp

| Hiện tượng | Nguyên nhân | Cách xử lý |
|------------|-------------|------------|
| Không thấy công chức trong danh sách duyệt | Công chức chưa gửi duyệt, hoặc không thuộc phạm vi phụ trách | Kiểm tra phân công phụ trách, hoặc liên hệ TCCB |
| Không duyệt được cấp 2 (PDV) | PDV chỉ duyệt cấp 1, không duyệt cấp 2 | Đúng thiết kế — TDV sẽ duyệt cấp 2 |
| Duyệt hàng loạt nhưng vẫn còn bản chờ | Có bản lỗi (thiếu minh chứng, trùng lặp) bị bỏ qua | Kiểm tra thông báo lỗi, duyệt từng bản còn lại |
| Không sửa được điểm tiêu chí chung sau khi duyệt | TDV chỉ sửa được khi **chưa chốt** báo cáo | Liên hệ CCT nếu cần điều chỉnh báo cáo đã chốt |
| Công chức điều chuyển đơn vị → không duyệt được | Kê khai thuộc thời điểm trước/sau chuyển → người duyệt khác | Kiểm tra ngày hiệu lực điều chuyển |

---

*Tài liệu biên soạn tháng 10/2026. Phục vụ công văn 153/CNTT.*
