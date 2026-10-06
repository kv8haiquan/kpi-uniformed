# HƯỚNG DẪN SỬ DỤNG HỆ THỐNG THEO DÕI, ĐÁNH GIÁ KPI

**Địa chỉ:** https://kpihaiquan.vn  
**Đơn vị:** Chi cục Hải quan Khu vực VIII  
**Phiên bản tài liệu:** Tháng 10/2026 — phục vụ công văn 153/CNTT

---

## MỤC LỤC

### 1. Giới thiệu chung

Hệ thống số hóa toàn trình việc kê khai công việc, thẩm định, phê duyệt, chấm điểm KPI, đánh giá tiêu chí chung và xếp loại chất lượng công chức theo tháng/quý. Từ **Quý III/2026**, theo Công văn 21169/CHQ-TCCB (28/8/2026), toàn bộ kỳ đánh giá, xếp loại chuyển sang **QUÝ** — kỳ tháng hết hiệu lực. Công chức vẫn kê khai công việc theo tháng, nhưng việc chấm tiêu chí chung và xếp loại thực hiện theo quý.

### 2. Tài liệu hướng dẫn theo vai trò

| STT | Tên file | Đối tượng | Số lượng |
|-----|----------|-----------|----------|
| 1 | [01_cong_chuc.md](./01_cong_chuc.md) | Công chức (CC, HD_111) | 489 người |
| 2 | [02_lanh_dao_don_vi.md](./02_lanh_dao_don_vi.md) | Trưởng đơn vị (TDV), Phó đơn vị (PDV) | 50 người |
| 3 | [03_lanh_dao_chi_cuc.md](./03_lanh_dao_chi_cuc.md) | Chi cục trưởng (CCT), Phó Chi cục trưởng (PCCT) | 4 người |
| 4 | [04_tccb.md](./04_tccb.md) | Cán bộ Tổ chức Cán bộ (TCCB) | Quyền cấp qua vai trò `TCCB` (hiện 0 tài khoản) hoặc cờ `can_view_all_units` (hiện 1 tài khoản) — số liệu 06/10/2026 |

### 3. Ma trận quyền hạn theo vai trò

| Chức năng | CC | PDV | TDV | PCCT | CCT | TCCB | Ghi chú |
|-----------|:--:|:---:|:---:|:----:|:---:|:----:|---------|
| **Kê khai công việc** ||||||| |
| Kê khai công việc theo tháng | ✅ | ✅ | ✅ | ✅ | ✅ | | Lãnh đạo kê khai riêng theo bộ chỉ số lãnh đạo |
| Lưu nháp / Gửi duyệt | ✅ | ✅ | ✅ | ✅ | ✅ | | |
| **Phê duyệt** ||||||| |
| Duyệt kê khai cấp 1 | | ✅ | ✅ | | | | PDV: phạm vi phân công; TDV: toàn đơn vị |
| Duyệt kê khai cấp 2 | | | ✅ | ✅ | ✅ | | TDV hoặc LĐ trực tiếp cao hơn |
| Duyệt hàng loạt (bulk) | | ✅ | ✅ | ✅ | ✅ | | |
| **Đánh giá theo quý (từ Q3/2026)** ||||||| |
| Tự chấm tiêu chí chung (31 tiêu chí) | ✅ | ✅ | ✅ | ✅ | ✅ | | Điểm thập phân bội 0.5 |
| Duyệt tiêu chí chung cấp 1 | | ✅ | ✅ | | | | |
| Duyệt tiêu chí chung cấp 2 | | | ✅ | ✅ | ✅ | | |
| Sửa điểm tiêu chí chung | | | ✅ | ✅ | ✅ | | TDV: chỉ trong đơn vị; CCT: toàn Chi cục |
| Phiếu nhận xét, đánh giá quý | ✅ | ✅ | ✅ | ✅ | ✅ | | Tự đề xuất → Nhận xét → Quyết định |
| **Xếp loại** ||||||| |
| Xếp loại A/B/C/D quý | | | | | ✅ | | Chỉ CCT |
| Điều chỉnh kết quả công việc | | | | | ✅ | | Có lưu lịch sử |
| Khóa/mở khóa kỳ đánh giá | | | | | ✅ | | |
| **Báo cáo & Quản trị** ||||||| |
| Xem phiếu đánh giá của mình | ✅ | ✅ | ✅ | ✅ | ✅ | | |
| Xem phiếu đánh giá đơn vị | | | ✅ | | | | TDV chỉ xem đơn vị mình |
| Tổng hợp phiếu toàn Chi cục | | | | ✅ | ✅ | ✅ | Chỉ đọc, không duyệt; TDV KHÔNG xem được (phiếu có nhận xét cá nhân) |
| Đối soát đánh giá | | | | ✅ | ✅ | ✅ | Kiểm tra ai chưa hoàn tất; TDV **không** có menu và bị backend từ chối (`_check_quyen_doi_soat`) |
| In bảng kê, xuất Excel | | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Điều chuyển đơn vị (từng người) | | | | | | ✅ | Endpoint yêu cầu quyền Admin |
| Điều chuyển hàng loạt (Excel) | | | | | | | **Chỉ Admin**, TCCB không truy cập được |
| Quản lý tài khoản | | | | | | ✅ | Reset mật khẩu, kích hoạt/vô hiệu — endpoint yêu cầu Admin |
| **Nghỉ phép** ||||||| |
| Đăng ký nghỉ phép | ✅ | ✅ | ✅ | ✅ | ✅ | | |
| Duyệt nghỉ phép | | ✅ | ✅ | ✅ | ✅ | | Theo phân cấp quản lý |
| **Lịch công tác (HKG)** ||||||| Hiển thị cho user có platform role HKG hoặc lãnh đạo/admin |
| Xem lịch công tác | ✅ | ✅ | ✅ | ✅ | ✅ | | Tất cả 549 user |
| Đăng lịch công tác | ✅ | ✅ | ✅ | ✅ | ✅ | | Mở cho toàn bộ 544 công chức (comment line 58-59 Sidebar.tsx) |
| Tổ chức cuộc họp | ✅ | ✅ | ✅ | ✅ | ✅ | | Chủ tọa/thư ký có toàn quyền sửa/xóa cuộc họp đó |
| **Nền tảng số khác** ||||||| |
| Đào tạo trực tuyến (LMS) | ✅ | ✅ | ✅ | ✅ | ✅ | | Đăng ký khóa học, làm bài kiểm tra |
| Kỳ thi đánh giá năng lực (ĐGNL) | ✅ | ✅ | ✅ | ✅ | ✅ | | |

---

## 4. Thông tin hỗ trợ

**Khi gặp sự cố**, vui lòng cung cấp đầy đủ 4 thông tin sau:

1. **Mã công chức** của bạn (ví dụ: 20ZZ-xxxx)
2. **Chức năng** đang sử dụng (ví dụ: Kê khai công việc, Duyệt tiêu chí chung)
3. **Thao tác** cụ thể đang làm khi gặp lỗi
4. **Ảnh chụp màn hình** đầy đủ, bao gồm cả thông báo lỗi

**Liên hệ:** Đội Công nghệ thông tin — Chi cục Hải quan Khu vực VIII

---

## 5. Lưu ý quan trọng

- **Từ Quý III/2026:** Kỳ đánh giá, xếp loại chuyển sang **QUÝ**. Công chức vẫn kê khai công việc theo tháng, nhưng chấm tiêu chí chung và xếp loại thực hiện theo quý.
- **Hạn nộp hồ sơ:** Ngày **23** tháng cuối quý, đơn vị nộp hồ sơ về TCCB.
- **Mật khẩu:** Tên đăng nhập là **mã công chức**, mật khẩu khởi tạo là `123456` — đổi ngay sau lần đăng nhập đầu tiên.
- **Bảo mật:** Hệ thống khóa tài khoản **15 phút** sau **10 lần** đăng nhập sai liên tiếp. Phiên đăng nhập có hiệu lực **8 giờ** (480 phút).
- **Tiêu chí chung:** Chấm điểm theo **bội số 0.5** (0; 0.5; 1.0; ...; tối đa điểm tiêu chí). Không còn dùng tick box Đạt/Không đạt.

---

*Tài liệu biên soạn tháng 10/2026 theo phiên bản phần mềm đang chạy. Phục vụ công văn 153/CNTT.*
