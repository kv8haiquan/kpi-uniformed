# BUSINESS RULES — MODULE LEGAL (PHỔ BIẾN PHÁP LUẬT)

> **Phiên bản:** 1.0 | **Ngày:** 19/02/2026

---

## I. QUY TẮC VĂN BẢN

### 1.1. Phân loại văn bản

| Mã | Loại | Ví dụ |
|-----|------|-------|
| LUAT | Luật | Luật Hải quan 2014 |
| NGHI_DINH | Nghị định | NĐ 335/2025/NĐ-CP |
| THONG_TU | Thông tư | TT 38/2015/TT-BTC |
| QUYET_DINH | Quyết định | QĐ của Tổng cục HQ |
| CONG_VAN | Công văn | CV hướng dẫn |
| CHI_THI | Chỉ thị | Chỉ thị Tổng cục |
| HUONG_DAN | Hướng dẫn | Hướng dẫn nội bộ |
| NOI_BO | VB nội bộ | Quy chế, quy trình nội bộ |

### 1.2. Workflow duyệt đăng

```
NHAP ──(Biên tập gửi duyệt)──► CHO_DUYET
CHO_DUYET ──(QT nội dung duyệt)──► DA_DUYET
CHO_DUYET ──(QT nội dung từ chối)──► NHAP (kèm lý do)
DA_DUYET ──(Lãnh đạo/QT xuất bản)──► DA_XUAT_BAN
DA_XUAT_BAN ──(thu hồi)──► NHAP

Điều kiện xuất bản:
- Có đầy đủ: số hiệu, trích yếu, loại VB, ngày ban hành
- Có ít nhất 1: nội dung HTML hoặc file gốc
- Đã được duyệt (DA_DUYET)
```

### 1.3. Quản lý hiệu lực

```
CON_HIEU_LUC  → Đang có hiệu lực pháp luật
HET_HIEU_LUC  → Đã hết hiệu lực (ngay_het_hieu_luc <= TODAY)
BI_THAY_THE   → Bị VB mới thay thế (van_ban_thay_the_id != NULL)
DANG_SUA_DOI  → Đang trong quá trình sửa đổi, bổ sung

Tự động cập nhật:
- Cron job hàng ngày: Nếu ngay_het_hieu_luc <= TODAY → HET_HIEU_LUC
- Khi tạo VB mới có loai_lien_ket=THAY_THE → VB cũ tự động BI_THAY_THE

Hiển thị:
- CON_HIEU_LUC: Badge xanh
- HET_HIEU_LUC: Badge xám + gạch ngang
- BI_THAY_THE: Badge vàng + link VB thay thế
```

### 1.4. Liên kết văn bản

| Loại | Ý nghĩa | Ví dụ |
|------|---------|-------|
| THAY_THE | VB A thay thế VB B | NĐ mới thay NĐ cũ |
| BO_SUNG | VB A bổ sung VB B | TT hướng dẫn thêm NĐ |
| HUONG_DAN | VB A hướng dẫn VB B | CV hướng dẫn TT |
| LIEN_QUAN | Liên quan chung | NĐ cùng lĩnh vực |

```
Liên kết 2 chiều:
- VB A → THAY_THE → VB B
- VB B tự động hiển thị "Bị thay thế bởi VB A"
```

### 1.5. Versioning

```
- Mỗi lần sửa nội dung VB đã XUAT_BAN → phien_ban + 1
- Giữ lịch sử (có thể xem phiên bản cũ)
- VB chưa XUAT_BAN → sửa thoải mái, không tăng version
```

---

## II. QUY TẮC "ĐIỂM MỚI QUY ĐỊNH"

### 2.1. Cấu trúc điểm mới

```
Khi nhập VB, Biên tập viên soạn:

diem_moi: (Nội dung điểm mới so với VB cũ)
  "1. Bổ sung hành vi vi phạm mới tại Điều 15
   2. Tăng mức phạt từ 10tr lên 50tr cho hành vi X
   3. Thay đổi thẩm quyền xử phạt tại Điều 20"

viec_can_lam: (Việc CBCC cần làm sau khi đọc)
  "1. Cập nhật checklist KTSTQ theo Điều 15 mới
   2. Thông báo cho doanh nghiệp về mức phạt mới
   3. Rà soát hồ sơ đang xử lý theo quy định cũ"
```

### 2.2. Hiển thị

```
┌─ VĂN BẢN: NĐ 335/2025/NĐ-CP ────────────────┐
│                                                  │
│  📌 ĐIỂM MỚI:                                   │
│  1. Bổ sung hành vi vi phạm mới tại Điều 15     │
│  2. Tăng mức phạt từ 10tr lên 50tr...           │
│                                                  │
│  ✅ VIỆC CẦN LÀM:                                │
│  1. Cập nhật checklist KTSTQ...                  │
│  2. Thông báo cho doanh nghiệp...               │
│                                                  │
│  📄 [Xem nội dung đầy đủ] [Download PDF gốc]    │
│  ✅ [Xác nhận đã đọc và hiểu]                    │
└──────────────────────────────────────────────────┘
```

---

## III. QUY TẮC XÁC NHẬN ĐỌC

### 3.1. VB bắt buộc đọc

```
Khi bat_buoc_doc=TRUE và VB được XUAT_BAN:
→ Hệ thống tạo xac_nhan_doc cho mỗi CBCC trong doi_tuong_ap_dung
→ CBCC phải: (1) Mở đọc VB, (2) Click "Xác nhận đã đọc và hiểu"

doi_tuong_ap_dung:
- ["TAT_CA"] → Tạo cho tất cả 549 CBCC (is_active=TRUE)
- ["Đội thủ tục 1", "Đội KTSTQ"] → Chỉ CBCC thuộc các đơn vị này
```

### 3.2. Tracking thời gian đọc

```
Frontend gọi API tracking mỗi 30 giây khi CBCC đang đọc VB.
thoi_gian_doc_giay tăng dần (cộng dồn qua nhiều lần mở).

Mục đích: Phát hiện CBCC "xác nhận cho có" (mở VB <30 giây rồi xác nhận).
Báo cáo hiển thị thời gian đọc trung bình.
```

### 3.3. Hạn xác nhận

```
han_xac_nhan: Ngày cuối cùng CBCC phải xác nhận

Timeline:
- Ngày xuất bản: Gửi notification
- Còn 3 ngày: Nhắc nhở (QUAN_TRONG)
- Còn 1 ngày: Nhắc nhở (KHAN)
- Quá hạn: Thông báo lãnh đạo + đánh dấu qua_han

Quá hạn: Vẫn cho phép xác nhận (nhưng ghi nhận trễ hạn).
```

### 3.4. Quy tắc mức độ

| Mức độ | Hạn đọc khuyến nghị | Notification | Hiển thị |
|--------|---------------------|-------------|---------|
| KHAN | 24 giờ | KHAN + email | Badge đỏ, đầu danh sách |
| QUAN_TRONG | 3 ngày | QUAN_TRONG | Badge vàng |
| BINH_THUONG | 7 ngày (hoặc theo han_xac_nhan) | BINH_THUONG | Bình thường |

---

## IV. QUY TẮC QUIZ PHÁP LUẬT

### 4.1. Cấu trúc quiz

```
- Mỗi VB có thể có 0 hoặc nhiều quiz
- Quiz lưu câu hỏi trực tiếp trong JSONB (không dùng ngân hàng riêng)
- Loại câu hỏi: Trắc nghiệm chọn 1 (giống LMS nhưng đơn giản hơn)
- Số câu: 5-20 câu mỗi quiz
```

### 4.2. Chấm điểm

```
diem = (so_cau_dung / tong_so_cau) × 100
dat_yeu_cau = diem >= diem_dat (mặc định 70.0)
```

### 4.3. Số lần làm

```
- Không giới hạn số lần (khuyến khích làm lại để nhớ)
- Lấy kết quả TỐT NHẤT để tính vào KPI Integration Log
```

---

## V. QUY TẮC TÌM KIẾM

```
Full-text search trên: so_hieu + trich_yeu + tom_tat + diem_moi
Bộ lọc: loai_van_ban, trang_thai_hieu_luc, muc_do, chuyen_de, khoảng ngày
Sắp xếp: Mới nhất | Quan trọng nhất | Sắp hết hạn xác nhận

Đặc biệt: Tìm theo số hiệu VB (exact match hoặc prefix)
  VD: "335" → tìm "335/2025/NĐ-CP"
```

---

## VI. QUY TẮC BÁO CÁO

### 6.1. Metrics cá nhân (tháng)

| Chỉ số | Cách tính |
|--------|-----------|
| VB đã đọc | COUNT(xac_nhan_doc WHERE da_doc=TRUE AND trong tháng) |
| VB chưa đọc | COUNT(xac_nhan_doc WHERE da_doc=FALSE AND bat_buoc_doc) |
| VB quá hạn | COUNT(xac_nhan_doc WHERE da_xac_nhan=FALSE AND han < TODAY) |
| Quiz hoàn thành | COUNT(ket_qua_quiz WHERE trong tháng) |
| Quiz điểm TB | AVG(ket_qua_quiz.diem) |
| Thời gian đọc TB | AVG(xac_nhan_doc.thoi_gian_doc_giay) |

### 6.2. Metrics đơn vị (cho lãnh đạo)

| Chỉ số | Cách tính |
|--------|-----------|
| Tỷ lệ đã đọc | CBCC đã đọc / Tổng CBCC cần đọc × 100% |
| Tỷ lệ xác nhận | CBCC xác nhận / Tổng CBCC cần đọc × 100% |
| Tỷ lệ quá hạn | CBCC quá hạn / Tổng CBCC cần đọc × 100% |
| CBCC chưa đọc | Danh sách tên + VB chưa đọc |

### 6.3. KPI Integration Log (cuối tháng)

```json
{
  "module": "LEGAL",
  "metrics": {
    "vb_da_doc": 8,
    "vb_chua_doc": 2,
    "vb_qua_han": 0,
    "quiz_hoan_thanh": 3,
    "quiz_diem_tb": 90.0,
    "thoi_gian_doc_tb_giay": 420
  }
}
```

---

## VII. QUY TẮC NOTIFICATION

| Event | Người nhận | Mức độ |
|-------|-----------|--------|
| VB mới xuất bản (bắt buộc, KHAN) | Theo doi_tuong_ap_dung | KHAN |
| VB mới xuất bản (bắt buộc, QUAN_TRONG) | Theo doi_tuong_ap_dung | QUAN_TRONG |
| VB mới xuất bản (không bắt buộc) | Tất cả CBCC | BINH_THUONG |
| Còn 3 ngày hạn xác nhận | CBCC chưa xác nhận | QUAN_TRONG |
| Còn 1 ngày hạn xác nhận | CBCC chưa xác nhận | KHAN |
| Quá hạn xác nhận | Lãnh đạo đơn vị | KHAN |
| VB bị thay thế | CBCC đã đọc VB cũ | BINH_THUONG |

---

## VIII. PHÂN QUYỀN CHI TIẾT

### Biên tập viên (BIEN_TAP)

```
Được:
- Nhập VB mới (trạng thái NHAP)
- Soạn trích yếu, điểm mới, việc cần làm
- Upload file gốc
- Gửi duyệt (NHAP → CHO_DUYET)
- Tạo quiz cho VB
- Sửa VB chưa xuất bản

Không được:
- Duyệt xuất bản
- Xem báo cáo xác nhận đọc đơn vị
```

### QT Nội dung (QT_NOI_DUNG)

```
Tất cả quyền Biên tập +
- Duyệt/từ chối VB (CHO_DUYET → DA_DUYET/NHAP)
- Xuất bản VB (DA_DUYET → DA_XUAT_BAN)
- Cấu hình: bat_buoc_doc, muc_do, han_xac_nhan, doi_tuong_ap_dung
- Xem báo cáo xác nhận đọc TẤT CẢ đơn vị
- Gửi notification nhắc nhở thủ công
```

### Lãnh đạo đơn vị

```
Được:
- Đọc VB, xác nhận như CBCC
- Xem báo cáo xác nhận đọc ĐƠN VỊ MÌNH
- Duyệt xuất bản (nếu workflow yêu cầu)
```
