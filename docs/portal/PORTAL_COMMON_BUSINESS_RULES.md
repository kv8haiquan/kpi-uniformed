# BUSINESS RULES — MODULE PORTAL & COMMON

> **Phiên bản:** 1.0 | **Ngày:** 19/02/2026

---

## I. QUY TẮC TIN TỨC / BÀI VIẾT

### 1.1. Workflow duyệt đăng

```
NHAP ──(Biên tập gửi)──► KIEM_TRA
KIEM_TRA ──(QT nội dung OK)──► DUYET
KIEM_TRA ──(QT nội dung từ chối)──► NHAP
DUYET ──(Lãnh đạo duyệt)──► XUAT_BAN
DUYET ──(Lãnh đạo từ chối)──► NHAP
XUAT_BAN ──(thu hồi)──► THU_HOI
THU_HOI ──(sửa & gửi lại)──► NHAP
```

### 1.2. Quy tắc ghim

```
- Tối đa 3 bài ghim trên trang chủ
- Bài ghim hiển thị ĐẦU TIÊN, nổi bật
- Chỉ QT_NOI_DUNG, ADMIN được ghim/bỏ ghim
```

### 1.3. Chuyên mục tin tức mặc định

| Chuyên mục | Nội dung |
|-----------|---------|
| Tin chỉ đạo | Chỉ đạo từ lãnh đạo Chi cục, Tổng cục |
| Thông báo | Thông báo nội bộ, lịch họp, sự kiện |
| Tin hoạt động | Hoạt động nghiệp vụ, kết quả công tác |
| Cập nhật pháp luật | Tự động/thủ công link sang module Legal |

---

## II. QUY TẮC THƯ VIỆN TÀI LIỆU (ECM)

### 2.1. Phân quyền thư mục

| Quyền | Ai xem được |
|-------|------------|
| TAT_CA | Tất cả 549 CBCC |
| LANH_DAO | Chỉ CBCC có is_lanh_dao=TRUE |
| DON_VI | Chỉ CBCC thuộc don_vi_ids chỉ định |
| CA_NHAN | Chỉ người tạo + ADMIN |

```
Quy tắc kế thừa:
- Tài liệu kế thừa quyền từ thư mục cha
- Có thể override (tài liệu có quyền riêng)
- Thư mục con kế thừa quyền thư mục cha
```

### 2.2. Versioning tài liệu

```
Khi upload phiên bản mới:
- Tạo record mới: phien_ban = phien_ban_cũ + 1
- phien_ban_truoc_id = ID phiên bản cũ
- Phiên bản cũ vẫn giữ nguyên (không xóa)
- Mặc định hiển thị phiên bản mới nhất
- Có thể xem/download phiên bản cũ qua "Lịch sử"
```

### 2.3. Giới hạn file

| Loại | Định dạng | Kích thước tối đa |
|------|----------|------------------|
| Tài liệu | PDF, DOCX, XLSX, PPTX | 50 MB |
| Hình ảnh | JPG, PNG, GIF | 10 MB |
| Video | MP4 (chỉ qua LMS) | 500 MB |
| Nén | ZIP, RAR | 100 MB |
| Khác | — | Từ chối |

---

## III. QUY TẮC HỆ THỐNG THÔNG BÁO

### 3.1. Nguồn notification

```
Thông báo được TẠO BỞI các module khác qua Internal API.
Module Portal/Common chỉ LƯU TRỮ và HIỂN THỊ.

Nguồn → Event → Notification:
LMS    → Giao bài, hoàn thành, hết hạn, BKT chấm
Forum  → Trả lời mới, upvote, đáp án chuẩn
Legal  → VB mới, nhắc hạn, quá hạn
Portal → Tin tức mới, thông báo nội bộ
System → Bảo trì, cập nhật hệ thống
```

### 3.2. Mức độ & Hiển thị

| Mức độ | Badge | Hành vi |
|--------|-------|---------|
| KHAN | 🔴 Đỏ | Nổi bật đầu danh sách, có thể gửi email |
| QUAN_TRONG | 🟡 Vàng | Nổi bật |
| BINH_THUONG | ⚪ Xám | Bình thường |

### 3.3. Quy tắc hiển thị

```
- Badge số trên icon 🔔: Đếm tổng chưa đọc
- Dropdown notification: 5 mới nhất + link "Xem tất cả"
- Trang /thong-bao: Danh sách đầy đủ, lọc theo loại/mức độ
- Auto-refresh: Polling mỗi 60 giây (hoặc WebSocket nếu có)
- Giữ lại 90 ngày, notification cũ hơn tự xóa (cron job)
```

### 3.4. Gom nhóm notification

```
Nếu cùng 1 event gửi cho CBCC nhiều lần trong 1 giờ → gom:
  "Có 5 trả lời mới cho chủ đề X" (thay vì 5 notification riêng)
```

---

## IV. QUY TẮC TÌM KIẾM HỢP NHẤT

### 4.1. Nguồn dữ liệu search

| Module | Bảng | Trường search |
|--------|------|--------------|
| LMS | lms.khoa_hoc | ten_khoa_hoc + mo_ta |
| Forum | forum.chu_de | tieu_de + noi_dung |
| Legal | legal.van_ban | so_hieu + trich_yeu + tom_tat + diem_moi |
| Portal | portal.bai_viet | tieu_de + noi_dung |
| Common | common.knowledge_base | tieu_de + noi_dung |

### 4.2. Ranking

```
1. Tính score bằng ts_rank (PostgreSQL)
2. Boost factor theo module (cấu hình):
   - LEGAL: ×1.2 (ưu tiên VB pháp luật)
   - Forum (có đáp án chuẩn): ×1.1
   - Bài ghim: ×1.1
3. Sắp xếp: score × boost, giảm dần
4. Phân trang: 20 kết quả/trang
```

### 4.3. Gợi ý tìm kiếm

```
- Khi gõ >= 2 ký tự → hiện gợi ý (debounce 300ms)
- Gợi ý từ: tags phổ biến + tiêu đề gần đây + số hiệu VB
- Lịch sử tìm kiếm cá nhân (lưu localStorage, không lưu server)
```

---

## V. QUY TẮC KNOWLEDGE BASE (SOP/FAQ)

### 5.1. SOP — Quy trình thao tác chuẩn

```
Nguồn tạo:
1. Chuyên gia soạn trực tiếp
2. Chuyển từ bài diễn đàn chất lượng cao (Forum → SOP)

Cấu trúc SOP:
- Tiêu đề
- Phạm vi áp dụng
- Các bước thực hiện (step-by-step)
- Căn cứ pháp lý (link VB)
- Lưu ý / Ngoại lệ
- Liên hệ khi cần hỗ trợ

Trạng thái: NHAP → CHO_DUYET → DA_XUAT_BAN → CAN_CAP_NHAT
Khi VB pháp luật liên quan thay đổi → tự động chuyển CAN_CAP_NHAT
```

### 5.2. FAQ — Câu hỏi thường gặp

```
Cấu trúc FAQ:
- Câu hỏi (tiêu đề)
- Trả lời (nội dung)
- Căn cứ pháp lý
- Link bài diễn đàn gốc (nếu chuyển từ Forum)
```

### 5.3. Liên kết chéo

```
SOP/FAQ ↔ VB pháp luật (legal.van_ban)
SOP/FAQ ↔ Chủ đề diễn đàn (forum.chu_de)
SOP/FAQ ↔ Khóa học (lms.khoa_hoc) — có thể tham chiếu

Khi VB bị thay thế:
→ Tất cả SOP/FAQ liên kết VB đó → chuyển CAN_CAP_NHAT
→ Notification cho chủ sở hữu SOP
```

---

## VI. QUY TẮC DASHBOARD TỔNG HỢP

### 6.1. Dashboard CBCC

```
Layout (top → bottom):
┌─────────────────────────────────────────┐
│ ⚡ THÔNG BÁO KHẨN (nếu có)             │
├──────────────┬──────────────────────────┤
│ 📊 KPI      │ 📚 Đào tạo              │
│ Điểm tháng  │ Khóa đang học: 2         │
│ Xếp loại: A │ Sắp hết hạn: 1          │
├──────────────┼──────────────────────────┤
│ 📜 Pháp luật│ 💬 Diễn đàn             │
│ VB chưa đọc │ Chủ đề mới: 5           │
│ VB khẩn: 1  │ Trả lời chờ: 3          │
├──────────────┴──────────────────────────┤
│ 📰 TIN TỨC MỚI NHẤT                   │
│ • Tin 1...                              │
│ • Tin 2...                              │
└─────────────────────────────────────────┘
```

### 6.2. Dashboard lãnh đạo

```
Bổ sung so với CBCC:
- Thống kê đơn vị (tổng hợp từ kpi_integration_log)
- Danh sách CBCC chưa đọc VB bắt buộc
- Danh sách CBCC quá hạn khóa học
- Top contributors diễn đàn
- Biểu đồ xu hướng (recharts)
```

### 6.3. Data refresh

```
- Dashboard load: gọi song song các API /dashboard/summary
- Auto-refresh: mỗi 5 phút
- Notification badge: refresh mỗi 1 phút
- Dữ liệu KPI: cập nhật hàng tháng (theo chu kỳ KPI)
```

---

## VII. QUY TẮC FILE STORAGE (MinIO)

### 7.1. Cấu trúc bucket

```
Bucket: kv08-files
├── lms/
│   ├── videos/         ← Video bài giảng
│   ├── documents/      ← PDF, slide bài học
│   └── certificates/   ← Chứng chỉ PDF
├── forum/
│   └── attachments/    ← Ảnh, file đính kèm bài viết
├── legal/
│   └── documents/      ← File gốc văn bản (PDF, Word)
├── portal/
│   ├── images/         ← Ảnh tin tức
│   └── documents/      ← Tài liệu ECM
└── avatars/            ← Ảnh đại diện (tương lai)
```

### 7.2. Naming convention

```
File path: {module}/{loai}/{uuid}.{ext}
Ví dụ: lms/videos/a1b2c3d4-e5f6-7890.mp4

Không dùng tên file gốc (tránh trùng, ký tự đặc biệt).
Tên file gốc lưu trong common.file_storage.file_name.
```

### 7.3. Quy tắc xóa file

```
- Soft delete: Đánh dấu is_deleted=TRUE trong DB
- File vật lý trên MinIO: giữ lại 30 ngày (cron job dọn)
- File chứng chỉ: KHÔNG BAO GIỜ xóa vật lý
```

---

## VIII. QUY TẮC KPI INTEGRATION

### 8.1. Nguyên tắc vàng

```
⚠️ Dữ liệu từ module mới → KPI = CHỈ THAM KHẢO
→ KHÔNG TỰ ĐỘNG thay đổi điểm KPI
→ Hiển thị bên cạnh để lãnh đạo tham khảo khi phê duyệt
→ Trong tương lai, nếu Quy chế KPI sửa đổi → có thể tính vào
```

### 8.2. Thời điểm sync

| Module | Realtime | Cuối tháng (cron) |
|--------|----------|-------------------|
| LMS | Khi hoàn thành khóa | Tổng hợp metrics tháng |
| Forum | — | Đếm bài/trả lời/upvote tháng |
| Legal | Khi xác nhận đọc | Tổng hợp metrics tháng |

### 8.3. Cron job cuối tháng

```
Chạy ngày 1 hàng tháng, tính cho tháng trước:
1. Lặp qua tất cả cong_chuc (is_active=TRUE)
2. Với mỗi module (LMS, FORUM, LEGAL):
   - Query bảng module → tính metrics
   - UPSERT vào common.kpi_integration_log
3. Log kết quả
```

---

## IX. PHÂN QUYỀN CHI TIẾT

### Biên tập viên (BIEN_TAP)

```
Portal:
- Soạn bài viết (NHAP)
- Gửi duyệt bài viết

Legal (nếu cũng có role BIEN_TAP):
- Nhập văn bản, soạn trích yếu
```

### QT Nội dung (QT_NOI_DUNG)

```
Portal:
- Tất cả quyền Biên tập +
- Kiểm tra, duyệt bài viết
- Ghim/bỏ ghim
- Quản lý chuyên mục
- Quản lý thư mục ECM
- Upload/xóa tài liệu

Common:
- Quản lý SOP/FAQ
- Xem tất cả báo cáo
```

### QT ATTT (QT_ATTT)

```
- Xem audit log toàn nền tảng
- Quản lý phân quyền platform_role
- Cấu hình bảo mật (tương lai)
```
