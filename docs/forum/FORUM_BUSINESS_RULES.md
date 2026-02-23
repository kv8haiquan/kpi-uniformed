# BUSINESS RULES — MODULE FORUM (DIỄN ĐÀN NGHIỆP VỤ)

> **Phiên bản:** 1.0 | **Ngày:** 19/02/2026

---

## I. QUY TẮC CHUYÊN MỤC

### 1.1. Phân cấp

```
Chuyên mục cha (VD: "Thủ tục hải quan")
  └── Chuyên mục con (VD: "Hàng XNK thương mại")
  └── Chuyên mục con (VD: "Quá cảnh, tạm nhập")

Tối đa 2 cấp (cha → con). Không cho phép tạo cấp 3.
```

### 1.2. Cấu hình chuyên mục

| Cấu hình | Ý nghĩa | Mặc định |
|-----------|---------|---------|
| `chi_doc` | TRUE → Chỉ CHUYEN_GIA, DIEU_PHOI, ADMIN đăng bài | FALSE |
| `yeu_cau_duyet` | TRUE → Bài mới cần DIEU_PHOI duyệt trước khi hiện | FALSE |

### 1.3. Chuyên mục mặc định (seed data)

8 chuyên mục: Thủ tục HQ, KTSTQ, Thuế & Chính sách, Kiểm soát, CNTT, Pháp luật, Tình huống thực tế, Góp ý & Đề xuất.

---

## II. QUY TẮC CHỦ ĐỀ

### 2.1. Trạng thái chủ đề

```
CHO_DUYET ──(Điều phối duyệt)──► MO
CHO_DUYET ──(Điều phối từ chối)──► AN
MO ──(Có đáp án chuẩn + Điều phối đóng)──► DONG
MO ──(Điều phối ghim)──► GHIM (vẫn MO, is_ghim=TRUE)
MO ──(Vi phạm)──► AN
DONG ──(Mở lại)──► MO
```

### 2.2. Quy tắc đăng bài

```
- Tiêu đề: 10-500 ký tự, bắt buộc
- Nội dung: tối thiểu 30 ký tự, hỗ trợ Markdown/HTML
- Tags: 0-5 tags, mỗi tag 2-50 ký tự
- Chuyên mục: bắt buộc chọn
- Văn bản liên quan: tùy chọn (link sang module Legal)
- Hình ảnh: cho phép upload inline (lưu qua Common file_storage)
```

### 2.3. Quy tắc sửa/xóa

```
Tác giả:
- Sửa: Trong 24 giờ đầu tiên (sau 24h phải nhờ Điều phối)
- Xóa: Chỉ khi CHƯA CÓ trả lời nào
- Sửa ghi nhận lịch sử: updated_at cập nhật, hiển thị "(đã chỉnh sửa)"

Điều phối viên / Admin:
- Sửa: Bất kỳ lúc nào
- Xóa: Bất kỳ lúc nào (soft delete)
```

### 2.4. Ghim & Sắp xếp

```
- Bài ghim (is_ghim=TRUE) luôn hiển thị ĐẦU danh sách
- Tối đa 3 bài ghim mỗi chuyên mục
- Thứ tự mặc định: Ghim trước → Mới nhất → Nhiều upvote
```

---

## III. QUY TẮC TRẢ LỜI

### 3.1. Reply lồng nhau (threaded)

```
Trả lời cấp 1: parent_id = NULL (trả lời trực tiếp chủ đề)
Trả lời cấp 2: parent_id = UUID cấp 1 (reply vào câu trả lời)

Tối đa 2 cấp. Reply vào cấp 2 → gán parent_id = cấp 1 (flatten).
```

### 3.2. Đáp án chuẩn

```
Ai chọn:
- Tác giả chủ đề (người đặt câu hỏi)
- Chuyên gia (CHUYEN_GIA)
- Điều phối viên (DIEU_PHOI_FORUM)

Quy tắc:
- Chỉ 1 đáp án chuẩn mỗi chủ đề
- Đáp án chuẩn hiển thị ĐẦU TIÊN (trước các trả lời khác)
- Có badge "✅ Đáp án chuẩn" nổi bật
- Khi chọn đáp án: cập nhật chu_de.tra_loi_chuan_id + tra_loi.is_dap_an_chuan
```

### 3.3. Trích dẫn căn cứ pháp lý

```
CBCC có thể đính kèm căn cứ pháp lý trong câu trả lời:

can_cu_phap_ly = [
  {"loai": "VAN_BAN", "id": "uuid", "trich_dan": "Điều 5 khoản 2 NĐ 335..."},
  {"loai": "SOP", "id": "uuid", "trich_dan": "Bước 3: Kiểm tra C/O..."}
]

Hiển thị: Khối trích dẫn có link sang VB/SOP tương ứng.
Khi click → chuyển sang module Legal (VB) hoặc Knowledge Base (SOP).
Frontend gọi Internal API để lấy thông tin VB (số hiệu, trích yếu).
```

---

## IV. QUY TẮC BIỂU QUYẾT (VOTE)

### 4.1. Upvote / Downvote

```
Mỗi CBCC chỉ được 1 vote (UP hoặc DOWN) cho mỗi đối tượng.

Áp dụng cho: Chủ đề (CHU_DE) + Trả lời (TRA_LOI)

Toggle logic:
- Chưa vote → Click UP → UP (+1)
- Đã UP → Click UP → Hủy vote (0)
- Đã UP → Click DOWN → Đổi thành DOWN (-1)
- Đã DOWN → Click DOWN → Hủy vote (0)
- Đã DOWN → Click UP → Đổi thành UP (+1)

Không được vote bài của chính mình.
```

### 4.2. Hiển thị điểm

```
so_upvote = COUNT(UP) - COUNT(DOWN)
Hiển thị: Nếu >= 0 → số xanh, Nếu < 0 → số đỏ
```

---

## V. QUY TẮC THEO DÕI

```
- CBCC theo dõi chủ đề → nhận notification khi có trả lời mới
- Tự động theo dõi: khi TẠO chủ đề hoặc TRẢ LỜI
- Có thể bỏ theo dõi bất kỳ lúc nào
- Notification gửi qua Common API (không gửi cho người vừa trả lời)
```

---

## VI. QUY TẮC TÌM KIẾM

```
Full-text search trên: tieu_de + noi_dung (PostgreSQL tsvector)
Bộ lọc: chuyên mục, tags, trạng thái, khoảng thời gian, tác giả
Sắp xếp: Độ liên quan (score) | Mới nhất | Nhiều upvote

Tìm kiếm tag: prefix match (gõ "thu" → "thuế XNK", "thủ tục")
Gợi ý: Khi đang gõ tiêu đề → hiện danh sách chủ đề trùng (tránh trùng câu hỏi)
```

---

## VII. QUY TẮC CHUYỂN ĐỔI SOP/FAQ

### 7.1. Khi nào chuyển

```
Điều phối / Chuyên gia nhận thấy:
- Chủ đề có chất lượng cao
- Đáp án chuẩn đầy đủ, có căn cứ pháp lý
- Nội dung áp dụng được cho nhiều tình huống

→ Chọn "Chuyển thành SOP/FAQ"
→ Biên tập nội dung cho chuẩn
→ Lưu vào common.knowledge_base
→ Link chéo: knowledge_base ↔ chu_de
```

### 7.2. Sau khi chuyển

```
- Chủ đề gốc gắn badge "📚 Đã thành SOP"
- SOP mới link ngược về chủ đề gốc
- SOP/FAQ hiển thị trong Unified Search
```

---

## VIII. QUY TẮC BÁO CÁO

### 8.1. Metrics cá nhân (tháng)

| Chỉ số | Cách tính |
|--------|-----------|
| Chủ đề đã đăng | COUNT(chu_de WHERE tac_gia_id=X) |
| Trả lời đã đăng | COUNT(tra_loi WHERE tac_gia_id=X) |
| Upvote nhận được | SUM(bieu_quyet.UP WHERE doi_tuong thuộc bài của X) |
| Bài được ghim | COUNT(chu_de WHERE tac_gia_id=X AND is_ghim=TRUE) |
| Đáp án chuẩn | COUNT(tra_loi WHERE tac_gia_id=X AND is_dap_an_chuan=TRUE) |
| SOP đóng góp | COUNT(knowledge_base WHERE chu_so_huu_id=X) |

### 8.2. KPI Integration Log (cuối tháng)

```json
{
  "module": "FORUM",
  "metrics": {
    "bai_dang": 5,
    "tra_loi": 12,
    "upvote_nhan_duoc": 30,
    "bai_ghim": 2,
    "dap_an_chuan": 1,
    "sop_dong_gop": 0
  }
}
```

---

## IX. QUY TẮC NỘI QUY DIỄN ĐÀN

```
KHÔNG ĐƯỢC ĐĂNG:
- Nội dung không liên quan nghiệp vụ hải quan
- Thông tin mật, nội bộ mức ĐỘ MẬT trở lên
- Ngôn từ thiếu tôn trọng
- Quảng cáo, spam

VI PHẠM:
- Lần 1: Điều phối ẩn bài + cảnh cáo
- Lần 2: Khóa quyền đăng bài 7 ngày
- Lần 3: Báo quản trị xử lý

(Logic khóa quyền: thêm field banned_until vào cong_chuc_platform_role nếu cần)
```

---

## X. PHÂN QUYỀN CHI TIẾT

### Điều phối viên (DIEU_PHOI_FORUM)

```
Quyền:
- Duyệt/từ chối chủ đề chờ duyệt
- Ghim/bỏ ghim chủ đề (tối đa 3/chuyên mục)
- Khóa/mở chủ đề
- Ẩn bài vi phạm
- Chọn đáp án chuẩn
- Sửa/xóa bài bất kỳ
- Quản lý chuyên mục
- Xem báo cáo tất cả đơn vị
```

### Chuyên gia (CHUYEN_GIA)

```
Quyền:
- Tất cả quyền CBCC +
- Chọn đáp án chuẩn
- Chuyển bài → SOP/FAQ
- Badge "Chuyên gia" bên cạnh tên
```
