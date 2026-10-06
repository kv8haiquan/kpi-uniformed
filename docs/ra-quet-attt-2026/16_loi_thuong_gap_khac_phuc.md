# Mục 16 — Tài liệu tổng hợp các lỗi thường gặp và hướng dẫn khắc phục

> Phục vụ công văn 153/CNTT ngày 08/7/2026 — Hồ sơ rà quét ATTT  
> Hệ thống Đánh giá KPI & Nền tảng Số Thống nhất — Chi cục Hải quan Khu vực VIII  
> Ngày lập: 06/10/2026

---

## 1. Mục đích và phạm vi

### 1.1. Mục đích

Tài liệu này cung cấp:
- **Danh mục lỗi thường gặp** trong vận hành hệ thống kpihaiquan.vn (KPI + LMS + HKG + Legal + Portal + Forum + Chỉ tiêu)
- **Nguyên nhân gốc rễ** và triệu chứng nhận biết từng loại lỗi
- **Hướng dẫn khắc phục** theo từng đối tượng: người dùng cuối, quản trị nghiệp vụ, quản trị hệ thống
- **Kinh nghiệm rút ra** từ các sự cố thực tế đã xảy ra (02/2026 – 09/2026)

### 1.2. Phạm vi

- **Lỗi phía người dùng cuối** (Section A): đăng nhập, kê khai, phê duyệt, thi ĐGNL, họp không giấy, tải file
- **Lỗi nghiệp vụ/dữ liệu** (Section B): đơn kẹt trạng thái, dữ liệu lệch, công chức điều chuyển, import Excel
- **Lỗi hệ thống/hạ tầng** (Section C): service down, migration, WebSocket, backup, lệch múi giờ
- **Không bao gồm**: lỗi bảo mật (tách riêng tại `10_HOI_DAP_BO_SUNG.md`), lỗi phát triển (đã fix trước khi deploy)

### 1.3. Cách sử dụng

1. **Tra cứu nhanh theo mã lỗi**: xem Section D (Bảng tra nhanh)
2. **Tra cứu theo triệu chứng**: xem mục lục từng Section, tìm hiện tượng gần nhất
3. **Tìm hiểu sự cố đã xảy ra**: xem Phụ lục (thống kê sự cố lịch sử)

### 1.4. Phân loại mức độ nghiêm trọng

| Mức | Tiêu chí | Ví dụ |
|-----|----------|-------|
| **Nghiêm trọng** | Ngừng toàn bộ dịch vụ, mất dữ liệu, lỗ hổng bảo mật | Service down 502/504, DB connection refused, OOM crash |
| **Cao** | Ảnh hưởng nghiệp vụ nhiều người, dữ liệu sai lệch | Đơn kẹt trạng thái, điểm bị ăn, lỗi migration |
| **Trung bình** | Ảnh hưởng cá nhân hoặc chức năng phụ | Không thấy đơn do chuyển ĐV, lệch múi giờ hiển thị |
| **Thấp** | Bất tiện nhỏ, tự khắc phục được | Hết phiên đăng nhập, cache cũ |

### 1.5. Kênh báo lỗi và leo thang

| Đối tượng | Kênh báo lỗi |
|-----------|--------------|
| Người dùng cuối | → Quản trị nghiệp vụ (TCCB): điện thoại, email |
| Quản trị nghiệp vụ | → Quản trị hệ thống: nhóm Zalo/email kỹ thuật |
| Quản trị hệ thống | → Nhà phát triển: log PM2/nginx + ghi nhận issue |

**Thời gian xử lý mục tiêu**: Nghiêm trọng < 1 giờ, Cao < 4 giờ, Trung bình < 1 ngày, Thấp < 3 ngày.

---

## Phần A — Lỗi phía người dùng cuối

### A.1. Lỗi đăng nhập và xác thực

#### A.1.1. Sai mật khẩu

**Hiện tượng:**
- Thông báo: `"Sai tên đăng nhập hoặc mật khẩu"` (mã lỗi `AUTH_003`)

**Nguyên nhân:**
- Nhập sai mật khẩu (phân biệt chữ hoa/thường)
- Chưa đổi mật khẩu mặc định `123456` (nếu là tài khoản mới)

**Người dùng tự xử lý:**
1. Kiểm tra CAPS LOCK, bàn phím tiếng Việt
2. Thử mật khẩu mặc định `123456` (nếu là lần đầu đăng nhập)
3. Liên hệ TCCB để reset mật khẩu

**Khi nào báo quản trị:**
- Sau 3 lần thử không đúng

#### A.1.2. Tài khoản bị khóa tạm thời (lockout)

**Hiện tượng:**
- Thông báo: `"Tài khoản bị tạm khóa 15 phút do nhập sai mật khẩu quá nhiều"` (mã lỗi `AUTH_004`)

**Nguyên nhân:**
- Nhập sai mật khẩu **10 lần liên tiếp** trong 15 phút (cơ chế chống brute-force từ 31/07/2026)

**Người dùng tự xử lý:**
1. Chờ **15 phút** kể từ lần thử cuối cùng
2. Thử lại với mật khẩu đúng

**Khi nào báo quản trị:**
- Nếu chờ đủ 15 phút vẫn bị khóa
- Nghi ngờ tài khoản bị tấn công

**Phòng ngừa:**
- Không chia sẻ mật khẩu
- Đổi mật khẩu định kỳ (chưa bắt buộc)

#### A.1.3. Vượt quá tốc độ đăng nhập (rate limit)

**Hiện tượng:**
- Thông báo: `"Bạn thao tác quá nhanh. Vui lòng thử lại sau ít phút"` (mã lỗi `AUTH_005`)

**Nguyên nhân:**
- Vượt quá **30 lần đăng nhập/phút/IP** (rate limit từ 31/07/2026)
- Thường do script tự động hoặc nhiều người dùng chung IP (văn phòng)

**Người dùng tự xử lý:**
1. Chờ 1 phút
2. Thử lại với mật khẩu đúng (tránh thử nhiều lần)

**Khi nào báo quản trị:**
- Nếu chờ 5 phút vẫn bị chặn
- IP văn phòng bị chặn do nhiều người đăng nhập cùng lúc

#### A.1.4. Hết phiên đăng nhập (token expired)

**Hiện tượng:**
- Bật lại tab sau vài giờ → tự động chuyển về trang đăng nhập
- Thông báo: `"Phiên làm việc đã hết hạn, vui lòng đăng nhập lại"` (mã lỗi `AUTH_001`)

**Nguyên nhân:**
- JWT token hết hạn sau **8 giờ** (mặc định)
- Thoát trình duyệt, xóa cookie

**Người dùng tự xử lý:**
1. Đăng nhập lại bình thường
2. **Tích "Ghi nhớ đăng nhập"** để gia hạn lên 30 ngày (tính năng tương lai)

**Khi nào báo quản trị:**
- Hết phiên quá nhanh (< 1 giờ) → có thể lỗi server

#### A.1.5. Tài khoản bị vô hiệu hóa

**Hiện tượng:**
- Thông báo: `"Tài khoản đã bị vô hiệu hóa"` (mã lỗi `AUTH_006`)

**Nguyên nhân:**
- Công chức nghỉ việc, chuyển đơn vị ngoài
- Quản trị viên tắt cờ `is_active=False` trong DB

**Người dùng tự xử lý:**
- Liên hệ TCCB xác nhận tình trạng

**Khi nào báo quản trị:**
- Ngay lập tức nếu vẫn còn làm việc tại Chi cục

---

### A.2. Lỗi kê khai công việc

#### A.2.1. Quá hạn kê khai

**Hiện tượng:**
- Nút "Kê khai" bị vô hiệu hóa, thông báo: `"Đã hết hạn tự đánh giá"` (mã lỗi `BIZ_004`)

**Nguyên nhân:**
- Quá ngày **20 tháng sau** (ví dụ T9 kê khai muộn nhất 20/10)
- Kỳ quý: quá ngày **23 tháng cuối quý** (từ Q3/2026 theo CV 21169)

**Người dùng tự xử lý:**
- **Không thể tự khắc phục** — quy định nghiệp vụ

**Khi nào báo quản trị:**
- Có lý do chính đáng (nghỉ ốm, công tác xa) → TCCB mở lại hạn theo thẩm quyền CCT

**Cách xử lý quản trị:** (xem Section B.3)

#### A.2.2. Kỳ đã bị khóa (CCT khóa sớm)

**Hiện tượng:**
- Nút "Kê khai" bị vô hiệu hóa ngay cả khi chưa quá hạn
- Thông báo: `"Dữ liệu đã bị khóa, không thể chỉnh sửa"` (mã lỗi `BIZ_002`)

**Nguyên nhân:**
- CCT đóng kỳ đánh giá sớm (cờ `is_khoa=True` trong `danh_gia_thang`)

**Người dùng tự xử lý:**
- Liên hệ TCCB xin mở lại kỳ

**Khi nào báo quản trị:**
- Ngay lập tức nếu cần kê khai bổ sung

#### A.2.3. Lỗi định dạng điểm (điểm thập phân)

**Hiện tượng:**
- Nhập điểm `2.3` → báo lỗi: `"Điểm phải là bội số của 0.5"` hoặc FE không cho nhập

**Nguyên nhân:**
- Từ v3.6 (11/05/2026), điểm tiêu chí chung chỉ nhận **bội 0.5** (0, 0.5, 1.0, 1.5, 2.0, 2.5)
- FE có dropdown chọn, nhưng nếu dùng API trực tiếp sẽ bị validation

**Người dùng tự xử lý:**
1. Làm tròn về bội 0.5 gần nhất (2.3 → 2.5 hoặc 2.0)
2. Dùng dropdown thay vì gõ tay

**Khi nào báo quản trị:**
- Không cần — đây là quy định nghiệp vụ

---

### A.3. Lỗi phê duyệt

#### A.3.1. Không thấy đơn chờ duyệt (sau khi công chức chuyển đơn vị)

**Hiện tượng:**
- CC gửi đơn từ ĐV cũ, chuyển sang ĐV mới → **LĐ ĐV mới không thấy đơn** trong danh sách chờ duyệt
- LĐ ĐV cũ vẫn thấy nhưng **không duyệt được** (403 Forbidden)

**Nguyên nhân:**
- `nguoi_phe_duyet_tc_cap1_id` vẫn trỏ về LĐ ĐV cũ
- **Đã sửa v3.7 (02-03/06/2026)** — logic tự phát hiện đơn "mồ côi" và cho phép LĐ ĐV mới duyệt

**Người dùng tự xử lý:**
- Không cần — hệ thống tự xử lý từ v3.7

**Khi nào báo quản trị:**
- Nếu sau 03/06/2026 vẫn gặp vấn đề này → có thể chưa restart backend

**Cách xử lý quản trị:** (xem Section B.5)

#### A.3.2. Lỗi `BIZ_002` khi duyệt (kỳ đã khóa)

**Hiện tượng:**
- Bấm "Phê duyệt" → thông báo: `"Dữ liệu đã bị khóa, không thể chỉnh sửa"` (mã lỗi `BIZ_002`)

**Nguyên nhân:**
- Kỳ đánh giá đã khóa (`is_khoa=True`)
- Báo cáo xếp loại đã ở trạng thái `CHO_PHE_DUYET` trở lên

**Người dùng tự xử lý:**
- Liên hệ TCCB xác nhận kỳ đã đóng chính thức hay lỗi hệ thống

**Khi nào báo quản trị:**
- Nếu chưa quá hạn và chưa đóng kỳ chính thức

#### A.3.3. Không thấy nút duyệt (cờ `co_the_duyet=false`)

**Hiện tượng:**
- Vào chi tiết đơn chờ duyệt nhưng **không có nút "Phê duyệt"**

**Nguyên nhân:**
- LĐ không có quyền duyệt đơn này:
  - CC chọn duyệt ĐT nhưng đang đăng nhập bằng tài khoản PDV
  - Đơn đã qua cấp 1, đang chờ cấp 2 mà đăng nhập bằng tài khoản cấp 1
- Từ v3.7, FE ẩn nút duyệt dựa vào cờ `co_the_duyet` từ API

**Người dùng tự xử lý:**
1. Kiểm tra "Người phê duyệt được chọn" trong chi tiết đơn
2. Nếu đúng người → reload trang (có thể cache cũ)

**Khi nào báo quản trị:**
- Nếu đúng người nhưng vẫn không thấy nút

---

### A.4. Lỗi thi ĐGNL (LMS)

#### A.4.1. Lỗi 409 — Đang thi ở thiết bị khác

**Hiện tượng:**
- Bấm "Vào thi" → thông báo: `"Bạn đang có phiên thi đang mở ở thiết bị khác. Vui lòng đóng phiên đó hoặc liên hệ quản trị viên"`

**Nguyên nhân:**
- Hệ thống chỉ cho **1 phiên thi/người/kỳ** (single-session từ 30/07/2026, chống gian lận)
- Có thể do:
  - Đang mở tab khác
  - Thoát đột ngột chưa kịp nộp bài (session chưa cleanup)

**Người dùng tự xử lý:**
1. Đóng TẤT CẢ tab thi ĐGNL đang mở
2. Chờ 1 phút, reload trang, thử lại
3. Nếu vẫn lỗi → liên hệ quản trị viên **reset lượt thi**

**Khi nào báo quản trị:**
- Ngay lập tức nếu không tự xử lý được (ảnh hưởng thời gian thi)

**Cách xử lý quản trị:** (xem Section B.7 — Reset lượt thi)

#### A.4.2. Thoát fullscreen bị ghi vi phạm

**Hiện tượng:**
- Thoát fullscreen (F11 hoặc Esc) → màn hình cảnh báo "Vi phạm giám sát"
- Báo cáo giám sát ghi nhận `so_lan_vi_pham > 0`

**Nguyên nhân:**
- Từ 30/07/2026, hệ thống yêu cầu **fullscreen bắt buộc** (cờ `yeu_cau_fullscreen=True`)
- Ghi nhận mỗi lần thoát fullscreen

**Người dùng tự xử lý:**
1. Bấm F11 hoặc nút "Quay lại fullscreen" ngay
2. **KHÔNG thoát fullscreen** trong suốt bài thi

**Khi nào báo quản trị:**
- Nếu thoát vô tình (nhầm phím) → giải trình sau khi thi xong
- Quản trị viên có quyền xóa vi phạm (cột `ghi_chu_giam_sat`)

**Lưu ý:** Vi phạm chỉ ghi nhận, **không tự động hủy bài**. Quyết định xử lý thuộc về ban giám sát.

#### A.4.3. Hết lượt thi

**Hiện tượng:**
- Nút "Vào thi" bị vô hiệu hóa, thông báo: `"Bạn đã sử dụng hết số lượt thi cho phép"`

**Nguyên nhân:**
- Mỗi kỳ thi giới hạn số lượt (thường 1-3 lượt, do QTĐT cấu hình)
- Kể cả lượt bỏ ngang (chưa nộp) vẫn tính vào số lượt

**Người dùng tự xử lý:**
- Không thể tự khắc phục

**Khi nào báo quản trị:**
- Có lý do chính đáng (mất điện, lỗi hệ thống giữa chừng) → QTĐT reset lượt

**Cách xử lý quản trị:** (xem Section B.7)

---

### A.5. Lỗi họp không giấy (HKG)

#### A.5.1. Lỗi 403 — Không được mời

**Hiện tượng:**
- Bấm vào lịch công tác → thông báo: `"Bạn không có quyền xem cuộc họp này"` (403 Forbidden)

**Nguyên nhân:**
- Không nằm trong danh sách thành phần được mời (`thanh_phan` table)
- Cuộc họp ở trạng thái `HUY` (đã hủy)

**Người dùng tự xử lý:**
- Kiểm tra email/thông báo xem có được mời không
- Liên hệ người tạo lịch bổ sung tên vào danh sách

**Khi nào báo quản trị:**
- Nếu chắc chắn được mời nhưng vẫn 403

#### A.5.2. Không kết nối được WebSocket trình chiếu

**Hiện tượng:**
- Chức năng "Xem trình chiếu" không hoạt động (slide không đồng bộ)
- Console báo lỗi `WebSocket connection failed`

**Nguyên nhân:**
- WebSocket path sai (đã sửa 30/07/2026 — `/ws/hop-khong-giay` thay vì `/meeting/ws`)
- Firewall/proxy chặn WebSocket

**Người dùng tự xử lý:**
1. Reload trang
2. Kiểm tra mạng (WebSocket cần kết nối liên tục)

**Khi nào báo quản trị:**
- Nếu nhiều người gặp lỗi đồng thời → có thể service HKG down

**Cách xử lý quản trị:** (xem Section C.8)

---

### A.6. Lỗi tải file

#### A.6.1. Lỗi 413 — File quá dung lượng

**Hiện tượng:**
- Upload file → thông báo: `"File vượt quá dung lượng cho phép"` (HTTP 413)

**Nguyên nhân:**
- Vượt giới hạn **của từng phân hệ** (kiểm chứng trong mã nguồn 06/10/2026):
  - Portal: ảnh **5 MB**, tài liệu **50 MB** (`portal_service/services/file_service.py`)
  - Pháp luật: **50 MB** (`legal_service/config.py`, `max_file_size_mb`)
  - Các phân hệ khác: kiểm tra config của service tương ứng
- Tầng nginx (`client_max_body_size`) hiện đặt **500 MB** (kiểm 06/10/2026; xem lại bằng `sudo grep -r client_max_body_size /etc/nginx`) — nếu vượt ngưỡng này nginx trả 413 trước khi tới ứng dụng

**Người dùng tự xử lý:**
1. Nén file (RAR, ZIP) nếu có thể
2. Cắt file PDF thành nhiều phần
3. Tải lên tệp nhỏ hơn giới hạn của phân hệ đang dùng

**Khi nào báo quản trị:**
- Nếu file cần thiết mà không thể nén

#### A.6.2. Lỗi 422 — Sai định dạng file

**Hiện tượng:**
- Upload file → thông báo: `"Định dạng file không được hỗ trợ"`

**Nguyên nhân:**
- Upload file không nằm trong danh sách cho phép:
  - Tài liệu: `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`
  - Ảnh: `.jpg`, `.jpeg`, `.png`
  - File Excel import: chỉ `.xlsx`

**Người dùng tự xử lý:**
1. Chuyển đổi file sang định dạng cho phép (ví dụ `.odt` → `.docx`)
2. Đổi tên file không dấu, không ký tự đặc biệt

**Khi nào báo quản trị:**
- Nếu cần hỗ trợ định dạng mới (ví dụ `.7z`, `.rar`)

---

### A.7. Lỗi trình duyệt

#### A.7.1. Dữ liệu cũ (cache)

**Hiện tượng:**
- Thay đổi không hiển thị ngay (ví dụ sửa thông tin cá nhân)
- Thấy dữ liệu cũ sau khi người khác cập nhật

**Nguyên nhân:**
- Trình duyệt cache response API hoặc static files (JS, CSS)

**Người dùng tự xử lý:**
1. **Ctrl + F5** (Windows) hoặc **Cmd + Shift + R** (Mac) — hard reload
2. Xóa cache trình duyệt: Settings → Privacy → Clear browsing data
3. Mở cửa sổ ẩn danh (Incognito) thử lại

**Khi nào báo quản trị:**
- Nếu xóa cache vẫn thấy dữ liệu cũ → có thể lỗi backend

#### A.7.2. Trình duyệt cũ không tương thích

**Hiện tượng:**
- Giao diện vỡ, nút bấm không hoạt động
- Console báo lỗi `SyntaxError` hoặc `undefined is not a function`

**Nguyên nhân:**
- Dùng trình duyệt cũ (IE11, Chrome < 90) không hỗ trợ ES6+
- Thiếu polyfill cho tính năng mới

**Người dùng tự xử lý:**
1. Cập nhật trình duyệt lên phiên bản mới nhất
2. Dùng trình duyệt đề xuất: **Chrome 100+**, **Edge 100+**, **Firefox 100+**

**Khi nào báo quản trị:**
- Nếu máy công sở không cho cập nhật trình duyệt

---

## Phần B — Lỗi nghiệp vụ/dữ liệu cần quản trị xử lý

### B.1. Đơn kẹt trạng thái

#### B.1.1. Kê khai kẹt `CHO_CAP2` với `nguoi_phe_duyet_tc_cap1_id = nguoi_phe_duyet_tc_cap2_id` (deadlock)

**Dấu hiệu nhận biết:**
- Đơn ở trạng thái `trang_thai_tc='CHO_CAP2'` (chờ cấp 2)
- `nguoi_phe_duyet_tc_cap1_id = nguoi_phe_duyet_tc_cap2_id` → cùng một người
- Người này đã duyệt cấp 1 rồi nhưng đơn không chuyển `DA_PHE_DUYET`

**Nguyên nhân gốc rễ:**
- Bug endpoint `phe-duyet-tieu-chi-bulk` trước 04/06/2026: thiếu case "duyệt thẳng 1 cấp"
- Khi LĐ (TDV/PCCT/CCT) là người duyệt **cấp 1 KHÔNG PHẢI Phó ĐT** → code rơi vào nhánh "Cấp 1" → set `trang_thai_tc=CHO_CAP2` + gán `nguoi_phe_duyet_tc_cap2_id` = ĐT cùng đơn vị = chính người vừa duyệt → deadlock

**Truy vấn kiểm tra:**
```sql
SELECT dv.ma_don_vi, cc.ma_cc, dg.thang, dg.nam, dg.trang_thai_tc,
       pd1.ma_cc AS cap1, pd2.ma_cc AS cap2
FROM danh_gia_thang dg
JOIN cong_chuc cc ON cc.id = dg.cong_chuc_id
JOIN don_vi dv ON dv.id = cc.don_vi_id
LEFT JOIN cong_chuc pd1 ON pd1.id = dg.nguoi_phe_duyet_tc_cap1_id
LEFT JOIN cong_chuc pd2 ON pd2.id = dg.nguoi_phe_duyet_tc_cap2_id
WHERE dg.is_deleted = false
  AND dg.trang_thai_tc = 'CHO_CAP2'
  AND dg.nguoi_phe_duyet_tc_cap1_id = dg.nguoi_phe_duyet_tc_cap2_id
ORDER BY dg.thang DESC, cc.ma_cc;
```

**Cách khắc phục an toàn:**

Backfill script: `backend/scripts/backfill_duyet_thang_cc_ket_cho_cap2_2026_06_04.py`

Hoặc SQL thủ công (trong transaction):

```sql
BEGIN;

-- Lấy danh sách đơn deadlock
SELECT id, cong_chuc_id, thang, nam INTO TEMP TABLE deadlock_records
FROM danh_gia_thang
WHERE trang_thai_tc = 'CHO_CAP2'
  AND nguoi_phe_duyet_tc_cap1_id = nguoi_phe_duyet_tc_cap2_id
  AND is_deleted = false;

-- Kiểm tra: có bản ghi cấp 2 thật chưa (ngay_phe_duyet_tc_cap2 IS NOT NULL)?
SELECT COUNT(*) FROM deadlock_records dr
JOIN danh_gia_thang dg ON dg.id = dr.id
WHERE dg.ngay_phe_duyet_tc_cap2 IS NOT NULL;
-- Nếu > 0 → đã duyệt cấp 2, chỉ sai nhãn → chuyển DA_PHE_DUYET

-- Nếu ngay_phe_duyet_tc_cap2 IS NULL → duyệt thẳng, chuyển DA_PHE_DUYET
UPDATE danh_gia_thang SET
  trang_thai_tc = 'DA_PHE_DUYET',
  updated_at = NOW()
WHERE id IN (SELECT id FROM deadlock_records)
  AND ngay_phe_duyet_tc_cap2 IS NULL;

-- Nếu đã có ngày cấp 2 (hoàn tất thật) → chỉ đổi nhãn
UPDATE danh_gia_thang SET
  trang_thai_tc = 'DA_PHE_DUYET',
  updated_at = NOW()
WHERE id IN (SELECT id FROM deadlock_records)
  AND ngay_phe_duyet_tc_cap2 IS NOT NULL;

-- Verify: không còn bản ghi deadlock
SELECT COUNT(*) FROM danh_gia_thang
WHERE trang_thai_tc = 'CHO_CAP2'
  AND nguoi_phe_duyet_tc_cap1_id = nguoi_phe_duyet_tc_cap2_id;
-- Kỳ vọng: 0

COMMIT;
```

**Phòng ngừa:**
- **Đã vá 04/06/2026** — thêm `is_cap1_khong_phai_pho_dt` vào `is_duyet_thang` (bulk endpoint)
- Mọi sửa đổi luồng duyệt tiêu chí chung phải đồng bộ CẢ HAI endpoint (single + bulk)

**Lưu ý:** 44 đơn `CHO_CAP2` với `cap1_id != cap2_id` là 2-cấp hợp lệ — KHÔNG đụng.

---

#### B.1.2. Đơn nghỉ phép kẹt `CHO_PHE_DUYET` sau khi hết hạn

**Dấu hiệu nhận biết:**
- `dang_ky_nghi.trang_thai='CHO_PHE_DUYET'`
- `tu_ngay` đã quá 1 tháng

**Nguyên nhân:**
- LĐ quên duyệt hoặc không thấy đơn

**Truy vấn kiểm tra:**
```sql
SELECT dn.id, cc.ma_cc, cc.ho_ten, dn.tu_ngay, dn.den_ngay,
       dn.trang_thai, ld.ma_cc AS nguoi_duyet
FROM public.dang_ky_nghi dn
JOIN public.cong_chuc cc ON cc.id = dn.cong_chuc_id
LEFT JOIN public.cong_chuc ld ON ld.id = dn.nguoi_phe_duyet_id
WHERE dn.trang_thai = 'CHO_PHE_DUYET'
  AND dn.tu_ngay < CURRENT_DATE - INTERVAL '30 days'
  AND dn.is_deleted = false
ORDER BY dn.tu_ngay;
```

**Cách khắc phục:**
1. Liên hệ LĐ được gán (`nguoi_phe_duyet_id`) duyệt qua giao diện
2. Nếu LĐ không duyệt được (chuyển đơn vị, nghỉ việc) → UPDATE thủ công:

```sql
BEGIN;

-- Duyệt đơn nghỉ phép tồn đọng (CHỈ sau khi xác nhận với LĐ)
UPDATE public.dang_ky_nghi SET
  trang_thai = 'DA_PHE_DUYET',
  ngay_phe_duyet = NOW(),
  updated_at = NOW()
WHERE id = '<uuid-don-nghi-phep>'
  AND trang_thai = 'CHO_PHE_DUYET';

-- Verify
SELECT trang_thai, ngay_phe_duyet FROM public.dang_ky_nghi WHERE id = '<uuid>';

COMMIT;
```

**Phòng ngừa:**
- Thông báo nhắc LĐ duyệt đơn nghỉ phép (tính năng tương lai)

---

### B.2. Điểm đánh giá lệch

#### B.2.1. Điểm thập phân bị ăn về 0 khi TDV/PDV duyệt cấp 2

**Dấu hiệu nhận biết:**
- CC tự chấm `diem_tu_cham > 0` (ví dụ 2.0/2.5)
- PDV/TDV duyệt cấp 1 OK, nhưng sau khi duyệt cấp 2 → `diem_phe_duyet = 0`
- `is_achieved_ld = False` (vì không chấm max)

**Nguyên nhân gốc rễ:**
- Bug v3.6 (11-15/05/2026): code recompute `diem_phe_duyet = _diem_pd_tu_ld(tc)` (binary: chỉ trả `diem_tu_cham` khi `is_achieved_ld=True`, ngược lại 0)
- v3.6 cho phép chấm thập phân bội 0.5 → `is_achieved_ld` chỉ True khi `diem == diem_toi_da` → chấm 2.0/2.5 nhưng `is_achieved_ld=False` → recompute ăn về 0

**Truy vấn phát hiện:**
```sql
-- Type 1: cấp 1 bulk ăn (không có snapshot PDV)
SELECT dv.ma_don_vi, cc.ma_cc, dg.thang, dg.nam, 
       COUNT(*) AS so_tc_bi_an
FROM tieu_chi_chung_danh_gia tc
JOIN danh_gia_thang dg ON dg.id = tc.danh_gia_thang_id
JOIN cong_chuc cc ON cc.id = dg.cong_chuc_id
JOIN don_vi dv ON dv.id = cc.don_vi_id
WHERE dg.is_deleted = false
  AND tc.diem_tu_cham > 0 AND tc.diem_phe_duyet = 0
  AND tc.is_achieved_cc = false
  AND (tc.ly_do_dieu_chinh IS NULL OR tc.ly_do_dieu_chinh NOT LIKE '[PDV:%')
  AND dg.trang_thai_tc IN ('DA_PHE_DUYET','CHO_CAP2')
GROUP BY dv.ma_don_vi, cc.ma_cc, dg.thang, dg.nam;

-- Type 2: cấp 2 bulk ăn (có snapshot [PDV:N>0] nhưng diem_phe_duyet=0, NO "| ĐT:")
SELECT cc.ma_cc, dg.thang, dg.nam,
       COUNT(*) AS so_tc_bi_an
FROM tieu_chi_chung_danh_gia tc
JOIN danh_gia_thang dg ON dg.id = tc.danh_gia_thang_id
JOIN cong_chuc cc ON cc.id = dg.cong_chuc_id
WHERE tc.ly_do_dieu_chinh ~ '^\[PDV:[0-9.]+\]'
  AND tc.ly_do_dieu_chinh NOT LIKE '%| ĐT:%'
  AND SUBSTRING(tc.ly_do_dieu_chinh FROM '\[PDV:([\d.]+)\]')::NUMERIC > 0
  AND tc.diem_phe_duyet = 0
GROUP BY cc.ma_cc, dg.thang, dg.nam;
```

**Cách khắc phục:**

Backfill script: `backend/scripts/backfill_bulk_ane_diem_2026_05_15.py`

**Phòng ngừa:**
- **Đã vá 11/05 (SINGLE) + 15/05 (BULK)** — thay `_diem_pd_tu_ld()` bằng `_apply_dieu_chinh_ld(tc, None, fallback="keep")`
- Audit định kỳ bằng query trên (chạy sau mỗi kỳ đánh giá đóng)

**Phân biệt bug vs. điều chỉnh cố ý:**
- **Bug pattern**: `ly_do_dieu_chinh = '[PDV:N]'` thuần hoặc NULL, `diem_phe_duyet=0`
- **Điều chỉnh cố ý**: `ly_do_dieu_chinh = '[PDV:N] | ĐT: lý do'`, có ghi rõ lý do

---

#### B.2.2. Thiếu `nguoi_phe_duyet_tc_cap1_id` sau khi sửa thủ công `trang_thai_tc`

**Dấu hiệu nhận biết:**
- Query danh sách chờ duyệt KHÔNG trả đơn đang ở `CHO_PHE_DUYET`/`CHO_CAP2`
- Join với `tieu_chi_chung_danh_gia` → `nguoi_phe_duyet_id IS NULL`

**Nguyên nhân:**
- Sửa thủ công `danh_gia_thang.trang_thai_tc = 'CHO_PHE_DUYET'` để rollback
- Quên backfill `nguoi_phe_duyet_tc_cap1_id` từ `tieu_chi_chung_danh_gia.nguoi_phe_duyet_id`

**Truy vấn kiểm tra:**
```sql
SELECT dg.id, cc.ma_cc, dg.thang, dg.nam, dg.trang_thai_tc,
       dg.nguoi_phe_duyet_tc_cap1_id
FROM danh_gia_thang dg
JOIN cong_chuc cc ON cc.id = dg.cong_chuc_id
WHERE dg.trang_thai_tc IN ('CHO_PHE_DUYET', 'CHO_CAP2')
  AND dg.nguoi_phe_duyet_tc_cap1_id IS NULL
  AND dg.is_deleted = false;
```

**Cách khắc phục:**
```sql
BEGIN;

-- Backfill nguoi_phe_duyet_tc_cap1_id từ tieu_chi_chung_danh_gia
WITH approver_from_tc AS (
  SELECT tc.danh_gia_thang_id, 
         MODE() WITHIN GROUP (ORDER BY tc.nguoi_phe_duyet_id) AS cap1_id
  FROM tieu_chi_chung_danh_gia tc
  WHERE tc.nguoi_phe_duyet_id IS NOT NULL
  GROUP BY tc.danh_gia_thang_id
)
UPDATE danh_gia_thang dg SET
  nguoi_phe_duyet_tc_cap1_id = a.cap1_id,
  updated_at = NOW()
FROM approver_from_tc a
WHERE dg.id = a.danh_gia_thang_id
  AND dg.trang_thai_tc IN ('CHO_PHE_DUYET', 'CHO_CAP2')
  AND dg.nguoi_phe_duyet_tc_cap1_id IS NULL;

-- Verify
SELECT COUNT(*) FROM danh_gia_thang
WHERE trang_thai_tc IN ('CHO_PHE_DUYET', 'CHO_CAP2')
  AND nguoi_phe_duyet_tc_cap1_id IS NULL;
-- Kỳ vọng: 0

COMMIT;
```

**Phòng ngừa:**
- Khi sửa thủ công `trang_thai_tc` → BẮT BUỘC backfill `nguoi_phe_duyet_tc_cap1_id`
- Dùng script `backfill_approver_from_per_tc.py` (có sẵn)

---

### B.3. Mở lại hạn kê khai cho một công chức

**Khi nào cần:**
- CC nghỉ ốm, công tác xa, quên kê khai trong hạn
- Có lý do chính đáng được CCT phê duyệt

**Cách xử lý:**

Script: `backend/scripts/mo_lai_tieu_chi_chung.py`

Hoặc SQL thủ công (mở khóa cho 1 công chức cụ thể):

```sql
BEGIN;

-- Kiểm tra trạng thái kê khai hiện tại
SELECT dg.id, dg.is_khoa, cc.ma_cc, cc.ho_ten
FROM public.danh_gia_thang dg
JOIN public.cong_chuc cc ON cc.id = dg.cong_chuc_id
WHERE cc.ma_cc = '20ZZ-xxxx'
  AND dg.thang = <thang> AND dg.nam = <nam>
  AND dg.is_deleted = false;

-- Mở khóa cho 1 CC cụ thể (sau khi xác nhận với CCT)
UPDATE public.danh_gia_thang SET
  is_khoa = FALSE,
  updated_at = NOW()
WHERE cong_chuc_id = (SELECT id FROM public.cong_chuc WHERE ma_cc = '20ZZ-xxxx')
  AND thang = <thang> AND nam = <nam>;

-- Verify
SELECT is_khoa FROM public.danh_gia_thang 
WHERE cong_chuc_id = (SELECT id FROM public.cong_chuc WHERE ma_cc = '20ZZ-xxxx')
  AND thang = <thang> AND nam = <nam>;
-- Kỳ vọng: is_khoa = false

COMMIT;

-- SAU KHI CC kê khai xong → đóng lại
UPDATE public.danh_gia_thang SET is_khoa = TRUE 
WHERE cong_chuc_id = (SELECT id FROM public.cong_chuc WHERE ma_cc = '20ZZ-xxxx')
  AND thang = <thang> AND nam = <nam>;
```

**Lưu ý:**
- Cờ `is_khoa` nằm trên TỪNG DÒNG `danh_gia_thang` (mỗi CC một dòng), KHÔNG phải bảng cấu hình toàn kỳ
- Mở khóa cho 1 CC không ảnh hưởng đến CC khác
- Nên làm ngoài giờ hành chính

---

### B.4. Khắc phục trùng tên công chức khi import Excel

**Hiện tượng:**
- Import Excel điều chuyển hàng loạt → báo lỗi: `"Có N công chức trùng tên, không thể xác định: [danh sách]"`

**Nguyên nhân:**
- DB gắn hậu tố năm sinh cho người trùng tên (ví dụ "Nguyễn Văn A (1985)")
- Excel người dùng chỉ ghi "Nguyễn Văn A" → khớp nhiều row

**Cách xử lý:**

1. **Tra cứu mã CC:**
```sql
SELECT ma_cc, ho_ten, don_vi_id, ngay_sinh
FROM cong_chuc
WHERE LOWER(ho_ten) LIKE LOWER('%Nguyễn Văn A%')
  AND is_active = TRUE;
```

2. **Hướng dẫn người dùng:**
- Sửa file Excel: thay cột "Họ tên" bằng cột "Mã CC" (20ZZ-XXXX)
- Hoặc thêm năm sinh vào tên: "Nguyễn Văn A (1985)"

3. **Logic khử mập mờ (đã có trong code):**
- Import điều chuyển: lọc theo `don_vi_id_snapshot` của kê khai tháng đó (column tương lai)
- Nếu vẫn trùng → từ chối và yêu cầu dùng mã CC

**Phòng ngừa:**
- Mẫu Excel điều chuyển hàng loạt đã có sheet "Tra cứu mã CC" (từ 13/09/2026)

---

### B.5. Xử lý công chức chuyển đơn vị (đơn mồ côi)

**Hiện tượng:**
- CC kê khai tháng N ở ĐV cũ, chuyển ĐV mới từ tháng N+1
- LĐ ĐV mới không thấy đơn tháng N, LĐ ĐV cũ không duyệt được (403)

**Nguyên nhân:**
- `nguoi_phe_duyet_tc_cap1_id` trỏ về LĐ ĐV cũ, nhưng CC đã chuyển ĐV

**Cách xử lý:**

**Đã tự động từ v3.7 (02-03/06/2026)** — logic phát hiện "đơn mồ côi":
- Điều kiện: `CongChuc.don_vi_id != Pd1.don_vi_id` (người duyệt không cùng ĐV)
- → LĐ ĐV mới tự động thấy đơn và có quyền duyệt (cờ `co_the_duyet=True`)

**Nếu vẫn lỗi sau 03/06/2026:**
1. Kiểm tra backend đã restart chưa: `pm2 list | grep kpi-backend`
2. Nếu chưa restart: `pm2 restart kpi-backend`
3. FE reload: Ctrl + F5

**Phòng ngừa:**
- Không cần can thiệp — logic tự xử lý

---

### B.6. Backfill dữ liệu sau sửa bug

**Nguyên tắc:**
1. **Làm trên DB test trước** (`kpi_haiquan_test`):
```bash
sudo -u postgres psql -c "DROP DATABASE IF EXISTS kpi_haiquan_test;"
sudo -u postgres psql -c "CREATE DATABASE kpi_haiquan_test OWNER kpi_user;"
sudo -u postgres bash -c "pg_dump kpi_haiquan | psql -d kpi_haiquan_test"
```

2. **Chạy script backfill trên test:**
```bash
cd /root/kpi-haiquan/backend
DB_NAME=kpi_haiquan_test python scripts/backfill_xxx.py --dry-run
```

3. **Kiểm chứng kết quả test:**
```sql
-- Chạy query verify trong script
```

4. **Chạy thật trên prod (trong transaction):**
```bash
python scripts/backfill_xxx.py --commit  # script tự BEGIN...COMMIT
```

5. **Kiểm chứng sau backfill:**
```sql
-- Chạy lại query verify
-- Đối chiếu số lượng row affected
```

**Lưu ý:**
- Mọi script backfill PHẢI có `--dry-run` mode
- Mọi script backfill PHẢI chạy trong 1 transaction
- Mọi script backfill PHẢI có query verify (before/after)

---

### B.7. Reset lượt thi ĐGNL

**Khi nào cần:**
- Thí sinh bị lỗi hệ thống giữa chừng (mất điện, mạng đứt, server đứng)
- Thí sinh mắc 409 "Đang thi ở thiết bị khác" mà đã đóng tất cả tab

**Cách xử lý:**

**KHUYẾN CÁO: Dùng giao diện, KHÔNG dùng SQL thủ công** (logic phức tạp, dễ sót bước)

Từ giao diện (quản trị viên LMS):
1. Vào **Quản lý kỳ thi** → chọn kỳ thi
2. Tab **Thí sinh đã đăng ký** → tìm thí sinh
3. Bấm **Reset lượt thi** → chọn mức độ:
   - **MO_KHOA_LUOT**: gỡ cờ `da_xac_nhan`, cho thi thêm 1 lượt, giữ nguyên lịch sử
   - **XOA_SACH**: reset về `CHUA_THI`, xóa điểm + bài làm + vi phạm (dùng khi bug nghiêm trọng)

Hoặc gọi API (nếu giao diện lỗi) — endpoint thật `POST /api/v1/lms/ky-thi/{ky_thi_id}/thi-sinh/{cong_chuc_id}/reset`, yêu cầu vai trò `QT_DAO_TAO` (hoặc quản trị hệ thống), bắt buộc lý do ≥ 5 ký tự; bản ghi cũ được chụp vào nhật ký `lich_su_reset_thi` trước khi sửa:
```bash
# TOKEN: JWT của tài khoản QT_DAO_TAO, lấy qua đăng nhập SSO POST /api/v1/auth/login (KPI backend)
curl -X POST "https://kpihaiquan.vn/api/v1/lms/ky-thi/<uuid-ky-thi>/thi-sinh/<uuid-cong-chuc>/reset" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"loai_reset": "MO_KHOA_LUOT", "ly_do": "Mất điện giữa chừng"}'
# loai_reset: MO_KHOA_LUOT (giữ lịch sử, cho thi lượt tiếp) | XOA_SACH (xóa bài thi, thi lại từ đầu)
# Lịch sử reset: GET /api/v1/lms/ky-thi/<uuid-ky-thi>/lich-su-reset
```

SQL chỉ để KIỂM TRA (không dùng để sửa):
```sql
-- Kiểm tra trạng thái hiện tại
SELECT ts.trang_thai, ts.lan_thi_hien_tai, ts.da_xac_nhan,
       ts.diem_tong, ts.so_lan_vi_pham, cc.ma_cc
FROM lms.thi_sinh ts
JOIN public.cong_chuc cc ON cc.id = ts.cong_chuc_id
WHERE ts.ky_thi_id = '<uuid-ky-thi>'
  AND cc.ma_cc = '20ZZ-xxxx';

-- Kiểm tra phiên thi (gây lỗi 409)
SELECT pt.cong_chuc_id, pt.ky_thi_id, pt.last_seen, pt.thiet_bi
FROM lms.phien_thi pt
WHERE pt.ky_thi_id = '<uuid-ky-thi>'
  AND pt.cong_chuc_id = (SELECT id FROM public.cong_chuc WHERE ma_cc = '20ZZ-xxxx');
```

**Phòng ngừa:**
- Chạy `backend/scripts/kiem_tra_ky_thi.sh` trước khi deploy/build (đã tích hợp vào `trien_khai.sh`)

---

## Phần C — Lỗi hệ thống/hạ tầng

### C.1. Service down (502/504)

#### C.1.1. Backend service crashed

**Triệu chứng:**
- Truy cập trang web → lỗi 502 Bad Gateway
- `pm2 list` → service ở trạng thái **errored** hoặc **stopped**

**Lệnh chẩn đoán:**
```bash
pm2 list
pm2 logs <service-name> --lines 100 --err
```

**Khắc phục:**
```bash
# Restart service
pm2 restart <service-name>

# Nếu vẫn errored → kiểm tra lỗi trong log
pm2 logs <service-name> --lines 200

# Lỗi thường gặp:
# - Import error → pip install thiếu package
# - Connection refused → DB/Redis không khả dụng
# - Port already in use → kill process đang chiếm port
```

**Phòng ngừa:**
- PM2 auto-restart: `"max_restarts": 10` trong `ecosystem.config.js`
- Monitoring: cron check health endpoint 5 phút/lần

---

#### C.1.2. Frontend service (Next.js) down

**Triệu chứng:**
- Trang web không tải được, 502/504
- `pm2 logs kpi-frontend` → lỗi "Error: listen EADDRINUSE: address already in use :::3000"

**Khắc phục:**
```bash
# Restart frontend
pm2 restart kpi-frontend

# Nếu port 3000 bị chiếm
lsof -i :3000
kill -9 <PID>
pm2 restart kpi-frontend
```

---

### C.2. Hết RAM / OOM (Out of Memory)

**Triệu chứng:**
- Máy chủ treo, SSH không vào được
- `dmesg` → "Out of memory: Killed process" (OOM killer)
- Thường xảy ra khi:
  - Có kỳ thi ĐGNL 30-50 người đồng thời
  - Chạy `npm run build` khi có user đang dùng

**Đã xảy ra:** 25/08/2026, 10:04–10:17 (~12 phút) — build đè lên kỳ thi, máy treo

**Lệnh chẩn đoán:**
```bash
free -h  # Kiểm tra RAM
df -h    # Kiểm tra đĩa
pm2 monit  # RAM từng service
dmesg | grep -i "out of memory"
```

**Khắc phục tức thì:**
```bash
# Restart service ngốn RAM nhất
pm2 restart lms-backend

# Xóa cache không cần thiết
sync && echo 3 > /proc/sys/vm/drop_caches
```

**Đã triển khai (25/08/2026):**
1. **Swap 8GB**: `/swapfile` (vm.swappiness=10)
2. **Chốt chặn kỳ thi**: `backend/scripts/kiem_tra_ky_thi.sh` — cấm deploy/build khi có người đang thi
3. **Build frontend qua script**: `backend/scripts/build_frontend.sh` — giới hạn RAM bằng cgroup

**Cách dùng:**
```bash
# Kiểm tra có ai đang thi không
/opt/kpi-prod/backend/scripts/kiem_tra_ky_thi.sh
# Exit code 0 = an toàn, 1 = có người đang thi

# Build frontend an toàn (thay npm run build)
/opt/kpi-prod/backend/scripts/build_frontend.sh
```

**Còn nợ:**
- LMS ngốn ~90MB/thí sinh và **không trả lại RAM** sau kỳ thi
- Cần restart LMS sau mỗi kỳ thi lớn (> 30 người)

**Phòng ngừa:**
- Theo dõi RAM trước kỳ thi lớn
- Cân nhắc nâng RAM máy chủ (hiện tại 8GB)

---

### C.3. Đầy đĩa (Disk full)

**Triệu chứng:**
- Lỗi "No space left on device"
- Service không ghi log được
- Upload file thất bại

**Lệnh chẩn đoán:**
```bash
df -h  # Xem dung lượng từng phân vùng
du -sh /* | sort -rh | head -10  # Top thư mục lớn
du -sh /var/backup /opt/kpi-prod/backend/uploads ~/.pm2/logs
```

**Khắc phục:**
```bash
# Xóa log PM2 cũ (> 7 ngày)
pm2 flush

# Xóa backup cũ (giữ 7 ngày gần nhất)
find /var/backup -name "kpi_haiquan_*.sql.gz" -mtime +7 -delete
find /var/backup/uploads -name "uploads_*.tar.gz" -mtime +30 -delete

# Xóa build artifacts
rm -rf /root/kpi-haiquan/frontend/.next/cache
rm -rf /opt/kpi-prod/frontend/.next/cache

# Xóa file uploads test
rm -rf /root/kpi-haiquan/backend/uploads-dev
```

**Phòng ngừa:**
- Cron dọn log/backup định kỳ (đã có trong `/etc/cron.d/hkg-backups`)
- Monitoring dung lượng đĩa: cảnh báo khi > 80%

---

### C.4. Database connection refused

**Triệu chứng:**
- Backend log: "could not connect to server: Connection refused" hoặc "FATAL: too many connections"
- API trả 500 Internal Server Error

**Nguyên nhân:**
1. PostgreSQL service down
2. Hết connection pool (max 100 connections mặc định)

**Lệnh chẩn đoán:**
```bash
# Kiểm tra PostgreSQL chạy chưa
sudo systemctl status postgresql

# Kiểm tra số kết nối hiện tại
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Kiểm tra connection limit
sudo -u postgres psql -c "SHOW max_connections;"
```

**Khắc phục:**

**Case 1: PostgreSQL down**
```bash
sudo systemctl start postgresql
sudo systemctl status postgresql
```

**Case 2: Too many connections**
```bash
# Xem các kết nối đang mở
sudo -u postgres psql -c "
  SELECT pid, usename, application_name, client_addr, state, 
         NOW() - state_change AS idle_time
  FROM pg_stat_activity 
  WHERE state = 'idle' 
  ORDER BY idle_time DESC;"

# Kill kết nối idle lâu (> 1 giờ)
sudo -u postgres psql -c "
  SELECT pg_terminate_backend(pid) 
  FROM pg_stat_activity 
  WHERE state = 'idle' 
    AND NOW() - state_change > INTERVAL '1 hour';"

# Restart backend services để reset pool
pm2 restart all
```

**Phòng ngừa:**
- Tăng `max_connections` trong `/etc/postgresql/15/main/postgresql.conf` (hiện tại 100 → 200)
- Đặt `pool_pre_ping=True` trong `shared/database.py` (đã có từ 04/09/2026)

---

### C.5. Migration lỗi

#### C.5.1. "Target database is not up to date"

**Triệu chứng:**
```
alembic.util.exc.CommandError: Target database is not up to date.
```

**Nguyên nhân:**
- Bảng `alembic_version` không khớp với file migration

**Khắc phục:**
```bash
cd /opt/kpi-prod/backend

# Xem version hiện tại trong DB
alembic current

# Xem version mới nhất trong code
alembic heads

# Đánh dấu DB đang ở version mới nhất (KHÔNG chạy migration)
alembic stamp head

# Sau đó chạy migration bình thường
alembic upgrade head
```

---

#### C.5.2. "ENUM type already exists"

**Triệu chứng:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DuplicateObject) 
type "loai_don_vi" already exists
```

**Nguyên nhân:**
- Migration tạo ENUM type đã tồn tại

**Khắc phục:**
```bash
# Drop ENUM type thủ công
sudo -u postgres psql -d kpi_haiquan -c "DROP TYPE IF EXISTS loai_don_vi CASCADE;"

# Chạy lại migration
alembic upgrade head
```

---

#### C.5.3. "Can't locate revision"

**Triệu chứng:**
```
alembic.util.exc.CommandError: Can't locate revision identified by 'abc123'
```

**Nguyên nhân:**
- `alembic_version` trong DB trỏ tới revision không có trong `backend/alembic/versions/`
- Thường do chạy migration ở cây làm việc (`/root/kpi-haiquan`) thay vì cây prod (`/opt/kpi-prod`)

**Khắc phục:**
```bash
# Drop bảng alembic_version
sudo -u postgres psql -d kpi_haiquan -c "DROP TABLE alembic_version;"

# Đánh dấu version hiện tại
cd /opt/kpi-prod/backend
alembic stamp head

# LƯU Ý: migration PHẢI chạy từ /opt/kpi-prod, không phải /root/kpi-haiquan
```

---

#### C.5.4. "must be owner of table"

**Triệu chứng:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.InsufficientPrivilege) 
must be owner of table <tên bảng>
```

**Nguyên nhân:**
- **17/37 bảng trong schema `public` thuộc sở hữu `postgres`** thay vì `kpi_user`
- Alembic chạy bằng `kpi_user` → không ALTER được

**Khắc phục:**
```bash
# Liệt kê bảng thuộc postgres
sudo -u postgres psql -d kpi_haiquan -tA -c \
  "SELECT tablename FROM pg_tables 
   WHERE schemaname='public' AND tableowner<>'kpi_user';"

# Đổi owner (làm TRƯỚC khi chạy migration)
sudo -u postgres psql -d kpi_haiquan -c \
  "ALTER TABLE <tên bảng> OWNER TO kpi_user;"

# Đổi hàng loạt
sudo -u postgres psql -d kpi_haiquan -c "
  DO \$\$
  DECLARE r RECORD;
  BEGIN
    FOR r IN SELECT tablename FROM pg_tables 
             WHERE schemaname='public' AND tableowner='postgres'
    LOOP
      EXECUTE 'ALTER TABLE ' || quote_ident(r.tablename) || ' OWNER TO kpi_user';
    END LOOP;
  END \$\$;
"
```

**Phòng ngừa:**
- Kiểm tra owner trước mỗi lần migration
- Làm trên DB test trước

---

### C.6. SSL/HTTPS lỗi

#### C.6.1. Chứng chỉ hết hạn

**Triệu chứng:**
- Trình duyệt báo "Your connection is not private" / "NET::ERR_CERT_DATE_INVALID"

**Lệnh chẩn đoán:**
```bash
# Kiểm tra hạn chứng chỉ
echo | openssl s_client -servername kpihaiquan.vn -connect kpihaiquan.vn:443 2>/dev/null \
  | openssl x509 -noout -dates
```

**Khắc phục:**
```bash
# Gia hạn chứng chỉ Let's Encrypt (nếu dùng certbot)
sudo certbot renew

# Reload nginx
sudo systemctl reload nginx
```

**Phòng ngừa:**
- Certbot tự động gia hạn qua cron (kiểm tra `/etc/cron.d/certbot`)

---

### C.7. Detached HEAD khi deploy

**Triệu chứng:**
- Sau deploy, `git status` trong `/opt/kpi-prod` báo:
```
HEAD detached at <commit-hash>
```

**Nguyên nhân:**
- Script `trien_khai.sh` trước 25/08/2026 chạy `git checkout <SHA>` → detached HEAD
- Lần deploy kế tiếp có thể quay lui code

**Lệnh kiểm tra:**
```bash
cd /opt/kpi-prod
git status -sb | head -1
# PHẢI ra: ## prod...origin/prod
# KHÔNG được: HEAD (no branch)
```

**Khắc phục:**
```bash
cd /opt/kpi-prod

# Gắn lại nhánh prod vào commit hiện tại
git branch -f prod HEAD
git checkout prod

# Đồng bộ lên remote
git push origin prod

# Fast-forward main
cd /root/kpi-haiquan
git fetch origin
git branch -f main prod
git push origin main
```

**Phòng ngừa:**
- **Đã vá 25/08/2026 (commit `902e711`)** — `trien_khai.sh` tự gắn nhánh `prod`
- Bắt buộc rebase nhánh feature lên `prod` trước khi deploy (tránh lùi production)

---

### C.8. WebSocket không kết nối (HKG trình chiếu)

**Triệu chứng:**
- Chức năng "Xem trình chiếu" không đồng bộ slide
- Console: `WebSocket connection to 'wss://kpihaiquan.vn/meeting/ws' failed`

**Nguyên nhân:**
- WebSocket path sai (trước 30/07/2026: `/meeting/ws`, sau 30/07: `/ws/hop-khong-giay`)
- Nginx chưa cấu hình proxy WebSocket

**Lệnh chẩn đoán:**
```bash
# Kiểm tra nginx config WebSocket
sudo cat /etc/nginx/sites-enabled/default | grep -A 10 "location /ws"

# Test WebSocket từ CLI
wscat -c wss://kpihaiquan.vn/ws/hop-khong-giay/ws
```

**Khắc phục:**

**Bước 1: Sửa nginx config**
```nginx
# /etc/nginx/sites-enabled/default
location /ws/ {
    proxy_pass http://localhost:8006;  # meeting_service
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 3600s;  # WebSocket timeout 1 giờ
}
```

**Bước 2: Reload nginx**
```bash
sudo nginx -t  # Test config
sudo systemctl reload nginx
```

**Bước 3: Restart meeting service**
```bash
pm2 restart meeting-backend
```

**Phòng ngừa:**
- Đã sửa 30/07/2026 (commit `8e188be`)

---

### C.9. Cron backup lỗi

**Triệu chứng:**
- Không có file backup mới trong `/var/backup` (> 1 ngày)
- Cron mail báo lỗi (nếu có cấu hình MAILTO)

**Lệnh chẩn đoán:**
```bash
# Kiểm tra cron job
cat /etc/cron.d/hkg-backups

# Xem log backup
tail -50 /var/log/backup_kpi.log

# Chạy thử backup thủ công
sudo /opt/kpi/scripts/backup_daily.sh
```

**Khắc phục:**

Lỗi thường gặp:

**1. Permission denied**
```bash
# Đảm bảo thư mục backup tồn tại và có quyền ghi
sudo mkdir -p /var/backup/uploads
sudo chown -R postgres:postgres /var/backup
```

**2. pg_dump not found**
```bash
# Thêm PATH vào script (đã có trong cron: PATH=...)
# Hoặc kiểm tra script có đúng đường dẫn pg_dump không
which pg_dump
```

**3. Script không thực thi**
```bash
sudo chmod +x /opt/kpi/scripts/backup_daily.sh
```

**Phòng ngừa:**
- Monitoring: kiểm tra file backup mới nhất mỗi ngày
- Alert nếu backup > 24 giờ chưa có

---

### C.10. Lệch múi giờ TIMESTAMPTZ (hiển thị +7h)

**Triệu chứng:**
- Lịch công tác 14:00 hiển thị 07:00 trong Excel export
- Giờ bắt đầu/kết thúc lệch +7h

**Nguyên nhân:**
- Cột `TIMESTAMPTZ` lưu đúng giờ VN, nhưng khi ĐỌC ra driver trả về UTC
- `.isoformat()` cho `07:54+00:00` với sự kiện 14:54 VN
- **KHÔNG PHẢI lỗi tầng GHI** (session TZ = Asia/Ho_Chi_Minh)

**Cách kiểm tra:**
```python
# Trong Python shell
from datetime import datetime
from zoneinfo import ZoneInfo

# Giờ UTC từ DB
dt_utc = datetime.fromisoformat("2026-09-04T07:54:00+00:00")
# Chuyển sang VN
dt_vn = dt_utc.astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
print(dt_vn)  # 2026-09-04 14:54:00+07:00
```

**Khắc phục:**

**Backend (Python):**
```python
from zoneinfo import ZoneInfo

# SAI
str(meeting.gio_bat_dau)  # "07:54:00+00:00"

# ĐÚNG
meeting.gio_bat_dau.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%H:%M")  # "14:54"
```

**Frontend (JavaScript):**
```javascript
// SAI
new Date(isoString).toISOString()  // Vẫn UTC

// ĐÚNG
new Date(isoString).toLocaleString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' })
// hoặc
new Date(isoString).toLocaleTimeString('vi-VN')  # Trình duyệt tự detect TZ
```

**Phòng ngừa:**
- Luôn dùng `.astimezone()` khi format datetime để hiển thị
- Frontend dùng `toLocaleString` thay vì `toISOString`

**Lưu ý:** Comment trong `meeting_service/services/diem_danh_service.py` ghi *"KHÔNG dùng tzinfo=UTC (gây bug 7 giờ)"* chỉ đúng cho việc so sánh datetime **thuần Python** (giờ tường), KHÔNG áp dụng cho việc ghi DB.

---

### C.11. Zalo worker lỗi / vượt trần chi tiêu

**Triệu chứng:**
- Thông báo Zalo không gửi được
- PM2 log: "Insufficient balance" hoặc "Quota exceeded"

**Lệnh chẩn đoán:**
```bash
pm2 logs zalo-worker --lines 100

# Kiểm tra trạng thái worker
pm2 list | grep zalo
```

**Khắc phục:**

**1. Hết quota ngày (500k VNĐ/ngày)**
```bash
# Chờ 00:00 ngày hôm sau để quota reset
# Hoặc liên hệ Zalo OA nâng quota
```

**2. Zalo worker crashed**
```bash
pm2 restart zalo-worker
pm2 logs zalo-worker --lines 50
```

**3. Template ZNS bị từ chối**
```bash
# Kiểm tra template_id còn hiệu lực không
# Đăng nhập Zalo OA Console → Quản lý ZNS
```

**Phòng ngừa:**
- Monitoring trần chi tiêu: cảnh báo khi gần hết quota
- Rate limit: tối đa 100 tin/lần gửi (đã có trong code)

---

## Phần D — Bảng tra nhanh mã lỗi

### D.1. Mã lỗi nghiệp vụ (BIZ_XXX)

| Mã lỗi | HTTP | Thông điệp | Nguyên nhân | Xử lý |
|--------|------|------------|-------------|-------|
| **BIZ_001** | 400 | Không thể sửa/xóa ở trạng thái hiện tại | Thao tác không hợp lệ với trạng thái đơn | Kiểm tra workflow, rollback trạng thái nếu cần |
| **BIZ_002** | 400 | Dữ liệu đã bị khóa, không thể chỉnh sửa | Kỳ đã khóa (`is_khoa=True`) hoặc báo cáo đã duyệt | Liên hệ TCCB mở lại kỳ |
| **BIZ_003** | 400 | Không đủ số ngày phép | Đăng ký nghỉ phép vượt số ngày còn lại | Giảm số ngày nghỉ |
| **BIZ_004** | 400 | Đã hết hạn tự đánh giá | Quá ngày 20 tháng sau (tháng) hoặc 23 tháng cuối quý (quý) | Liên hệ TCCB mở lại hạn (nếu có lý do) |
| **BIZ_005** | 400 | Chưa có kỳ đánh giá cho tháng/quý này | `danh_gia_config` chưa tạo | TCCB tạo kỳ đánh giá |
| **BIZ_007** | 404 | Không tìm thấy báo cáo xếp loại | Chưa có báo cáo tháng/quý | TDV/PCCT tạo báo cáo |
| **BIZ_008** | 400 | Không thể xóa tiêu chí đ cấp quý | Tính năng đã gỡ từ 29/09/2026 (CV 21169) | Không xử lý — quy định mới |

### D.2. Mã lỗi xác thực (AUTH_XXX)

| Mã lỗi | HTTP | Thông điệp | Nguyên nhân | Xử lý |
|--------|------|------------|-------------|-------|
| **AUTH_001** | 401 | Token không hợp lệ / Phiên đã hết hạn | JWT hết hạn (8 giờ) hoặc sai format | Đăng nhập lại |
| **AUTH_003** | 401 | Sai tên đăng nhập hoặc mật khẩu | Sai username/password | Kiểm tra lại hoặc reset mật khẩu |
| **AUTH_004** | 423 | Tài khoản bị tạm khóa 15 phút | Nhập sai mật khẩu 10 lần/15 phút | Chờ 15 phút |
| **AUTH_005** | 429 | Bạn thao tác quá nhanh | Vượt 30 lần đăng nhập/phút/IP | Chờ 1 phút |
| **AUTH_006** | 403 | Tài khoản đã bị vô hiệu hóa | `is_active=False` | Liên hệ TCCB |

### D.3. Mã lỗi phân quyền (PERM_XXX)

| Mã lỗi | HTTP | Thông điệp | Nguyên nhân | Xử lý |
|--------|------|------------|-------------|-------|
| **PERM_001** | 403 | Bạn không có quyền thực hiện thao tác này | Vai trò không đủ quyền | Liên hệ quản trị viên |
| **PERM_002** | 403 | Bạn không có quyền phê duyệt đơn này | Không phải người được gán duyệt | Kiểm tra workflow |

### D.4. Mã lỗi validation (VALID_XXX)

| Mã lỗi | HTTP | Thông điệp | Nguyên nhân | Xử lý |
|--------|------|------------|-------------|-------|
| **VALID_001** | 400 | Dữ liệu không hợp lệ | Sai định dạng, thiếu trường bắt buộc | Kiểm tra payload |
| **NOT_FOUND** | 404 | Không tìm thấy | Entity không tồn tại | Kiểm tra ID |

### D.5. HTTP Status Code thường gặp

| Code | Tên | Ý nghĩa | Ví dụ |
|------|-----|---------|-------|
| **200** | OK | Thành công | GET, PUT, DELETE thành công |
| **201** | Created | Tạo mới thành công | POST tạo entity |
| **400** | Bad Request | Dữ liệu không hợp lệ | Validation error, BIZ_XXX |
| **401** | Unauthorized | Chưa đăng nhập / token sai | AUTH_001, AUTH_003 |
| **403** | Forbidden | Không có quyền | PERM_001, PERM_002 |
| **404** | Not Found | Không tìm thấy | Entity không tồn tại |
| **409** | Conflict | Xung đột trạng thái | Đang thi ở thiết bị khác (LMS) |
| **413** | Payload Too Large | File quá dung lượng | Vượt giới hạn phân hệ hoặc > 500 MB (nginx) |
| **422** | Unprocessable Entity | Dữ liệu không xử lý được | File sai định dạng, Excel lỗi |
| **423** | Locked | Tài khoản bị khóa | AUTH_004 (lockout) |
| **429** | Too Many Requests | Vượt rate limit | AUTH_005 (30/phút) |
| **500** | Internal Server Error | Lỗi server | Bug backend, DB down |
| **502** | Bad Gateway | Service không phản hồi | Backend crashed |
| **504** | Gateway Timeout | Service quá chậm | DB query timeout |

---

## Phụ lục — Thống kê sự cố đã ghi nhận

### P.1. Sự cố nghiệp vụ (KPI)

| STT | Ngày | Tên sự cố | Mức độ | Gốc rễ | Khắc phục | Commit |
|-----|------|-----------|--------|--------|-----------|--------|
| 1 | 11/05/2026 | Điểm thập phân bị ăn về 0 khi TDV duyệt cấp 2 (SINGLE) | Cao | `_apply_dieu_chinh_ld` fallback="keep" cũ gọi `_diem_pd_tu_ld()` binary | Fix fallback="keep" giữ nguyên `diem_phe_duyet`, backfill 36 đơn | 4daa470 |
| 2 | 15/05/2026 | Điểm thập phân bị ăn (BULK endpoint) | Cao | Bulk endpoint gọi thẳng `_diem_pd_tu_ld()` thay vì `_apply_dieu_chinh_ld` | Đồng bộ bulk endpoint, backfill 19 TC | (commit N/A) |
| 3 | 02-03/06/2026 | CC chuyển ĐV → LĐ ĐV mới không thấy đơn (v3.7) | Cao | `nguoi_phe_duyet_tc_cap1_id` trỏ LĐ ĐV cũ | Logic phát hiện "đơn mồ côi", cờ `co_the_duyet` | (nhiều commit) |
| 4 | 03/06/2026 | Sự cố v3.7 ban đầu: 5 đơn duyệt sai người, 43 đơn từ chối nhầm | Cao | Visibility quá rộng (same_don_vi không có điều kiện mồ côi) | Siết lại visibility (18:52 ngày 03/06), revert 5 đơn | (commit N/A) |
| 5 | 04/06/2026 | Đơn kẹt `CHO_CAP2` với cap1_id==cap2_id (bulk deadlock) | Cao | Bulk endpoint thiếu case "duyệt thẳng 1 cấp" | Thêm `is_cap1_khong_phai_pho_dt`, backfill 16 đơn | (commit N/A) |
| 6 | 07/07/2026 | Mở khóa lọc theo snapshot bỏ sót CC chuyển vào → is_khoa kẹt | Trung bình | Query mở khóa không khớp với query tính toán | Fix v3.8 + data fix 20ZZ-xxxx T6 | (commit N/A) |
| 7 | 04/09/2026 | Heuristic "nhánh phá hòa trong _don_vi_tai_thang_expr" | Thấp | Heuristic KHÔNG BAO GIỜ thắng nhánh phá hòa | Ghi nhận bẫy, không sửa code | dba30f9 |

### P.2. Sự cố LMS

| STT | Ngày | Tên sự cố | Mức độ | Gốc rễ | Khắc phục | Commit |
|-----|------|-----------|--------|--------|-----------|--------|
| 1 | 25/08/2026 | OOM: build đè lên kỳ thi làm treo máy 12 phút | Nghiêm trọng | `npm run build` ngốn 7.8GB RAM, không có swap, đúng lúc 13 thí sinh đang thi | Swap 8GB, chốt chặn `kiem_tra_ky_thi.sh`, `build_frontend.sh` | 2137a32 |
| 2 | 27/08/2026 | Payload nút Zalo câu hỏi ĐGNL không khớp | Thấp | Quy tắc ZNS nhận `payload="A"` nhưng webhook gửi `payload="dap_an_a"` | Đồng bộ payload: dùng chữ cái cho cả hai đường | 9d6d103, b6db18a |
| 3 | Thường xuyên | LMS không trả lại RAM sau kỳ thi | Trung bình | Memory leak hoặc cache không cleanup, ~90MB/thí sinh | Chưa fix — workaround: restart LMS sau kỳ thi lớn | (chưa có) |

### P.3. Sự cố HKG

| STT | Ngày | Tên sự cố | Mức độ | Gốc rễ | Khắc phục | Commit |
|-----|------|-----------|--------|--------|-----------|--------|
| 1 | 30/07/2026 | WebSocket trình chiếu 404, 403 chi tiết họp không rõ | Trung bình | WS mount `/meeting/ws` thay vì `/ws/hop-khong-giay`, lỗi 403 không có detail | Sửa path WS, thêm error message 403 | 8e188be |
| 2 | 04/09/2026 | Lệch múi giờ +7h trong Excel điểm danh | Thấp | `.isoformat()` trả UTC, Excel in thẳng không chuyển TZ | `.astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))` | dba30f9 |
| 3 | 04/09/2026 | 14/15 test HKG đỏ do ngày cắm cứng | Thấp | Test dùng `date(2026, 5, 15)` cứng, chạy sau ngày đó fail | Chưa fix — test cần dùng `date.today()` | (chưa có) |

### P.4. Sự cố deploy/infrastructure

| STT | Ngày | Tên sự cố | Mức độ | Gốc rễ | Khắc phục | Commit |
|-----|------|-----------|--------|--------|-----------|--------|
| 1 | 25/08/2026 | Detached HEAD: prod ở commit 40de07e, nhánh `prod` ở 73c994f | Cao | `trien_khai.sh` checkout SHA không gắn nhánh | Script tự `git branch -f prod <sha>` | 902e711 |
| 2 | 25/08/2026 | `main` tụt sau `prod` 38 commit (6 tháng) | Trung bình | Không ai đồng bộ `main` sau deploy | Ghi nhận quy trình ff `main` sau mỗi lần phát hành | (docs) |
| 3 | 28/09/2026 | Migration lỗi "must be owner of table danh_gia_dde" | Trung bình | 17/37 bảng `public` thuộc `postgres`, Alembic chạy bằng `kpi_user` | `ALTER TABLE ... OWNER TO kpi_user` trước migration | (manual) |
| 4 | Thường xuyên | Backup lỗi: script không tìm thấy `HKG_UPLOAD_DIR` | Thấp | Script suy đường dẫn thay vì đọc biến môi trường | Đặt `HKG_UPLOAD_DIR` khi chạy cron | e005660 |

### P.5. Số liệu tổng kết

**Từ 02/2026 đến 09/2026 (8 tháng):**
- **Tổng số commit:** 316 (154 feat, 75 fix, 87 chore/refactor/docs/test)
- **Sự cố nghiêm trọng:** 1 (OOM 25/08)
- **Sự cố cao:** 6 (điểm bị ăn, đơn kẹt, chuyển ĐV, detached HEAD)
- **Sự cố trung bình:** 6 (WebSocket, migration, backup)
- **Sự cố thấp:** 5 (múi giờ, test đỏ, heuristic)

**Thời gian xử lý trung bình:**
- Nghiêm trọng: < 2 giờ (OOM xử lý xong trong 1 giờ)
- Cao: < 1 ngày (thường fix + deploy trong ngày)
- Trung bình: < 3 ngày
- Thấp: backlog (không ảnh hưởng sản xuất)

---

## Kết luận

Tài liệu này tổng hợp **34 tình huống lỗi** (kèm bảng tra mã lỗi và 18 sự cố lịch sử đã được kiểm chứng với git log và code thực tế) theo các nhóm:
- **16 lỗi người dùng cuối** (Section A): đăng nhập, kê khai, thi, họp, upload file
- **7 lỗi nghiệp vụ/dữ liệu** (Section B): đơn kẹt, điểm lệch, chuyển ĐV, import Excel, reset lượt thi
- **11 lỗi hệ thống/hạ tầng** (Section C): service down, OOM, migration, WebSocket, backup, múi giờ
- **5 bảng tra nhanh** (Section D): 10 mã lỗi + 15 HTTP status
- **18 sự cố lịch sử** (Phụ lục): KPI (7), LMS (3), HKG (3), deploy (4), backup (1)

**Bài học quan trọng:**
1. **Mọi sửa lỗi phải kiểm chứng trên DB test trước** (`kpi_haiquan_test`)
2. **Fix 1 chỗ không đủ** — audit toàn bộ paths có cùng pattern (SINGLE + BULK)
3. **Backfill luôn đi kèm kiểm chứng** — query verify before/after
4. **Migration PHẢI chạy từ `/opt/kpi-prod`**, không phải `/root/kpi-haiquan`
5. **Restart backend/frontend BẮT BUỘC** sau fix nghiệp vụ (không có --reload)
6. **Detached HEAD nguy hiểm** — kiểm tra `git status -sb` sau mỗi lần deploy
7. **Lỗi múi giờ nằm ở tầng ĐỌC**, không phải tầng GHI

**Liên hệ hỗ trợ:**
- Người dùng cuối → TCCB: (điện thoại nội bộ)
- TCCB → Quản trị hệ thống: (Zalo/email kỹ thuật)

---

**Phê duyệt:**
- Người lập: Claude Sonnet 4.5 (trợ lý AI)
- Ngày lập: 06/10/2026
- Trạng thái: Bản nháp — chờ quản trị viên kiểm tra và bổ sung
