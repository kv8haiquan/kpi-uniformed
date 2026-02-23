# BUSINESS RULES — MODULE LMS (ĐÀO TẠO TRỰC TUYẾN)

> **Phiên bản:** 1.0 | **Ngày:** 19/02/2026

---

## I. QUY TẮC KHÓA HỌC

### 1.1. Phân loại khóa học

| Loại | Mã | Ai tạo đăng ký | Hủy được? | Bắt buộc hoàn thành? |
|------|-----|----------------|-----------|---------------------|
| Tự học | TU_HOC | CBCC tự đăng ký | ✅ Có (nếu chưa bắt đầu) | Không |
| Bắt buộc | BAT_BUOC | QT đào tạo giao | ❌ Không | ✅ Có (theo hạn) |
| Giao việc | GIAO_VIEC | Lãnh đạo giao | ❌ Không | ✅ Có (theo hạn) |
| Trực tuyến | TRUC_TUYEN | QT đào tạo giao | ❌ Không | Theo cấu hình |
| Kết hợp | KET_HOP | QT đào tạo giao | ❌ Không | Theo cấu hình |

### 1.2. Workflow trạng thái khóa học

```
NHAP ──(Giảng viên gửi duyệt)──► CHO_DUYET
CHO_DUYET ──(QT đào tạo duyệt)──► DA_XUAT_BAN
CHO_DUYET ──(QT đào tạo từ chối)──► NHAP (kèm lý do)
DA_XUAT_BAN ──(tạm dừng)──► TAM_DUNG
TAM_DUNG ──(mở lại)──► DA_XUAT_BAN
DA_XUAT_BAN ──(kết thúc)──► DA_DONG

Điều kiện xuất bản:
- Phải có ít nhất 1 bài học
- Phải có ít nhất 1 bài kiểm tra (nếu loai != TU_HOC)
- Thông tin đầy đủ (tên, mô tả, thời gian)
```

### 1.3. Điều kiện tiên quyết

- Khóa A yêu cầu tiên quyết khóa B → CBCC phải `HOAN_THANH` khóa B trước khi đăng ký A
- Kiểm tra tại thời điểm đăng ký (không kiểm tra lại sau đó)
- Lưu trong `dieu_kien_tien_quyet JSONB` dạng mảng UUID

---

## II. QUY TẮC ĐĂNG KÝ & TIẾN ĐỘ

### 2.1. Trạng thái đăng ký

```
CHUA_BAT_DAU ──(xem bài đầu tiên)──► DANG_HOC
DANG_HOC ──(hoàn thành TẤT CẢ bài + BKT đạt)──► HOAN_THANH
DANG_HOC ──(BKT không đạt hết lần)──► KHONG_DAT
DANG_HOC ──(quá hạn, chưa xong)──► QUA_HAN
```

### 2.2. Tính phần trăm hoàn thành

```
phan_tram = (số bài_hoc DA_HOAN_THANH / tổng số bài_hoc) × 100

Nếu khóa có bài kiểm tra:
  phan_tram = (bài_hoc hoàn thành × 80% + BKT đạt × 20%) / tổng

Ví dụ: 10 bài học, 1 BKT
  - Hoàn thành 8/10 bài = 8/10 × 80 = 64%
  - BKT chưa làm = 0 × 20 = 0%
  - Tổng = 64%
```

### 2.3. Điều kiện hoàn thành khóa

```
1. Tất cả bài học có trạng thái DA_HOAN_THANH
2. Bài kiểm tra (nếu có) đạt điểm >= diem_dat_yeu_cau
3. Nếu khóa BAT_BUOC: phải hoàn thành trước han_hoan_thanh

Khi HOAN_THANH:
→ Tự động cấp chứng chỉ
→ Gửi notification cho CBCC + Lãnh đạo đơn vị
→ Ghi KPI integration log
```

### 2.4. Giao bài bắt buộc (batch)

```
Ai được giao:
- QT_DAO_TAO: Giao cho bất kỳ CBCC nào
- Lãnh đạo (TRUONG_DON_VI, PHO_DON_VI): Chỉ giao cho CBCC trong đơn vị mình
- ADMIN: Giao cho bất kỳ ai

Giao theo đơn vị:
- Chọn don_vi_id → hệ thống lấy TẤT CẢ cong_chuc có don_vi_id = X AND is_active = TRUE
- Bỏ qua CBCC đã đăng ký khóa này rồi (không tạo trùng)
```

---

## III. QUY TẮC BÀI KIỂM TRA

### 3.1. Cấu hình đề thi

| Cấu hình | Giá trị | Mặc định |
|-----------|---------|---------|
| Số câu hỏi | 5-100 | 20 |
| Thời gian làm | NULL (không giới hạn) hoặc 10-180 phút | 30 phút |
| Số lần làm tối đa | 1-10 | 3 |
| Điểm đạt | 0-100 | 70.0 |
| Trộn đề | true/false | true |
| Trộn đáp án | true/false | true |

### 3.2. Tạo đề thi

```
Trường hợp 1: Chọn tay
- Giảng viên chọn cau_hoi_ids từ ngân hàng → lưu vào bai_kiem_tra_cau_hoi

Trường hợp 2: Random từ ngân hàng
- Giảng viên cấu hình: 10 câu DE + 7 câu TRUNG_BINH + 3 câu KHO
- Hệ thống random mỗi lần CBCC bắt đầu làm bài
```

### 3.3. Chấm điểm tự động

```
Loại TRAC_NGHIEM_1, TRAC_NGHIEM_NHIEU, DUNG_SAI, GHEP_DOI:
  → So sánh tra_loi với dap_an.correct
  → Đúng = cau_hoi.diem, Sai = 0
  → Tổng điểm = (SUM diem_dat / SUM diem_toi_da) × 100

Loại TU_LUAN:
  → Không chấm tự động
  → Trạng thái: CHO_CHAM
  → Giảng viên chấm tay + nhập điểm + nhận xét
```

### 3.4. Thời gian làm bài

```
- Khi bắt đầu: ghi thoi_gian_bat_dau = NOW()
- Khi nộp: kiểm tra NOW() - thoi_gian_bat_dau <= thoi_gian_lam_bai_phut
- Nếu quá giờ: tự động nộp bài với câu trả lời đã có
- Frontend đếm ngược + cảnh báo khi còn 5 phút
```

### 3.5. Số lần làm lại

```
- Lấy kết quả tốt nhất (điểm cao nhất) trong các lần
- Nếu đã đạt ở lần trước → vẫn cho làm lại (để cải thiện điểm)
- Nếu hết số lần mà chưa đạt → KHONG_DAT
```

---

## IV. QUY TẮC CHỨNG CHỈ

### 4.1. Tự động cấp khi

```
Điều kiện cấp:
1. dang_ky_khoa_hoc.trang_thai = 'HOAN_THANH'
2. Bài kiểm tra (nếu có) đã đạt
3. Chưa có chứng chỉ cho CBCC + khóa này

Mã chứng chỉ: CC-[MÃ_KHÓA]-[NĂM]-[SỐ_THỨ_TỰ]
  Ví dụ: CC-KH001-2026-00142
```

### 4.2. Nội dung chứng chỉ PDF

```
- Tên đơn vị: Chi cục Hải quan Khu vực VIII
- Tiêu đề: CHỨNG NHẬN HOÀN THÀNH KHÓA HỌC
- Tên CBCC, Đơn vị
- Tên khóa học, Chuyên đề
- Điểm đạt
- Ngày cấp
- Mã chứng chỉ (để xác minh)
- Chữ ký điện tử (nếu có)
```

---

## V. QUY TẮC BÁO CÁO

### 5.1. Chỉ số cá nhân

| Chỉ số | Cách tính |
|--------|-----------|
| Khóa đang học | COUNT(dang_ky WHERE trang_thai='DANG_HOC') |
| Khóa hoàn thành (tháng) | COUNT(dang_ky WHERE trang_thai='HOAN_THANH' AND ngay_hoan_thanh trong tháng) |
| Khóa quá hạn | COUNT(dang_ky WHERE trang_thai='QUA_HAN') |
| Điểm TB bài kiểm tra | AVG(ket_qua.diem WHERE dat_yeu_cau=TRUE) |
| Tổng thời gian học (phút) | SUM(tien_do_bai_hoc.thoi_gian_xem_giay) / 60 |
| Chứng chỉ đạt được | COUNT(chung_chi) |

### 5.2. Chỉ số đơn vị (cho lãnh đạo)

| Chỉ số | Cách tính |
|--------|-----------|
| Tỷ lệ hoàn thành | CBCC hoàn thành / Tổng CBCC đăng ký × 100% |
| Tỷ lệ quá hạn | CBCC quá hạn / Tổng CBCC bắt buộc × 100% |
| Điểm TB đơn vị | AVG(điểm BKT tất cả CBCC đơn vị) |
| CBCC chưa đăng ký | Tổng CBCC đơn vị - CBCC đã đăng ký ít nhất 1 khóa |

### 5.3. Dữ liệu ghi vào KPI Integration Log (cuối tháng)

```json
{
  "module": "LMS",
  "metrics": {
    "khoa_hoc_hoan_thanh": 3,
    "khoa_hoc_dang_hoc": 1,
    "diem_trung_binh": 85.5,
    "chung_chi_dat": 2,
    "tong_thoi_gian_hoc_phut": 480,
    "khoa_qua_han": 0
  }
}
```

---

## VI. QUY TẮC NOTIFICATION

| Event | Người nhận | Mức độ |
|-------|-----------|--------|
| Được giao khóa bắt buộc | CBCC | QUAN_TRONG |
| Còn 3 ngày hết hạn | CBCC | QUAN_TRONG |
| Quá hạn khóa bắt buộc | CBCC + Lãnh đạo ĐV | KHAN |
| Hoàn thành khóa | CBCC | BINH_THUONG |
| CBCC hoàn thành khóa | Lãnh đạo ĐV | BINH_THUONG |
| Khóa mới xuất bản | Tất cả CBCC (hoặc theo đối tượng) | BINH_THUONG |
| BKT được chấm tay (tự luận) | CBCC | BINH_THUONG |

---

## VII. QUY TẮC PHÂN QUYỀN CHI TIẾT

### 7.1. Giảng viên (GIANG_VIEN)

```
Được:
- Tạo, sửa, xóa khóa học CỦA MÌNH (trạng thái NHAP)
- Tạo câu hỏi, bài kiểm tra cho khóa CỦA MÌNH
- Xem danh sách học viên khóa CỦA MÌNH
- Chấm bài tự luận khóa CỦA MÌNH
- Xem kết quả khảo sát khóa CỦA MÌNH
- Gửi duyệt khóa (NHAP → CHO_DUYET)

Không được:
- Sửa/xóa khóa đã XUAT_BAN
- Giao bài bắt buộc
- Xem báo cáo đơn vị
- Quản lý chuyên đề
```

### 7.2. QT Đào tạo (QT_DAO_TAO)

```
Được TẤT CẢ quyền Giảng viên +
- Quản lý chuyên đề (CRUD)
- Duyệt/từ chối khóa học
- Giao bài bắt buộc cho BẤT KỲ CBCC
- Xem báo cáo TẤT CẢ đơn vị
- Xuất báo cáo Excel/PDF
```

### 7.3. Lãnh đạo đơn vị

```
Được:
- Học như CBCC bình thường
- Giao bài cho CBCC TRONG ĐƠN VỊ mình
- Xem báo cáo ĐƠN VỊ MÌNH
- Xem tiến độ CBCC trong đơn vị

Không được:
- Tạo/sửa khóa học (trừ khi cũng là GIANG_VIEN)
- Xem báo cáo đơn vị khác
```
