# Câu hỏi ĐGNL hằng ngày qua chatbot Zalo

Mỗi ngày phát 1 câu hỏi trắc nghiệm lấy từ ngân hàng đề ĐGNL, người dùng bấm
nút chọn đáp án, bot trả lời đúng/sai kèm giải thích.

Trạng thái: **backend xong, chưa deploy prod** (nhánh `feature/lms-dgnl-cau-hoi-hang-ngay`).

---

## 1. Hai endpoint

Cả hai đều là `GET`, xác thực bằng header `X-Bot-Key`.

| Endpoint | Trả về |
|---|---|
| `GET /api/v1/lms/dgnl/cong-khai/cau-hoi-hang-ngay` | Đề + các phương án. **Không có đáp án đúng.** |
| `GET /api/v1/lms/dgnl/cong-khai/dap-an` | Đáp án đúng + giải thích + chấm đúng/sai |

### Tham số

**`/cau-hoi-hang-ngay`**

| Tham số | Bắt buộc | Ý nghĩa |
|---|---|---|
| `ngay` | không | `YYYY-MM-DD`. Mặc định hôm nay theo giờ VN. |
| `dinh_dang` | không | `zalo` → trả object `message` của Zalo. Bỏ trống → `{success, data}`. |

**`/dap-an`**

| Tham số | Bắt buộc | Ý nghĩa |
|---|---|---|
| `cau_hoi_id` | **có** | Lấy từ `cau_hoi_id` của câu hỏi (hoặc từ payload nút). |
| `chon` | không | `A`/`B`/`C`/`D`. Có thì mới chấm đúng/sai; chữ thường cũng được. |
| `dinh_dang` | không | `zalo` |

Tra theo `cau_hoi_id` chứ **không** theo ngày: người dùng có thể bấm trả lời
lúc nửa đêm hoặc sáng hôm sau, tra theo ngày sẽ ra nhầm câu.

---

## 2. Nối vào khối động (Dynamic block) của chatbot

Trong `oa.zalo.me` → **Tương tác → Menu, chatbot**, tại hộp thoại **Edit Request**:

```
Request Type : GET
Request URL  : https://kpihaiquan.vn/api/v1/lms/dgnl/cong-khai/cau-hoi-hang-ngay?dinh_dang=zalo
Headers      : X-Bot-Key  =  <giá trị ZALO_BOT_API_KEY trong backend/.env>
```

Bấm **Test the Request** để đối chứng. Endpoint trả về đúng hình dạng object
`message` của Zalo:

```json
{
  "text": "📚 CÂU HỎI ĐGNL NGÀY 27/08/2026\nLĩnh vực: 1. Luật HQ\n\n… \n\nA. …\nB. …\n\n👇 Chọn đáp án bên dưới",
  "attachment": {
    "type": "template",
    "payload": {
      "buttons": [
        {"title": "A. …", "type": "oa.query.hide",
         "payload": {"content": "DGNL|<cau_hoi_id>|A"}}
      ]
    }
  }
}
```

Khi người dùng bấm nút, Zalo gửi chuỗi `payload.content` về. Tách theo dấu `|`
lấy `cau_hoi_id` và phương án đã chọn, rồi gọi:

```
https://kpihaiquan.vn/api/v1/lms/dgnl/cong-khai/dap-an?cau_hoi_id=<id>&chon=<A|B|C|D>&dinh_dang=zalo
```

Kết quả trả về cũng là object `message`, gửi thẳng cho người dùng:

```json
{"text": "❌ Chưa đúng. Bạn chọn A, đáp án đúng là D.\n…\n\n📖 Giải thích: …"}
```

### ⚠️ Chưa đối chứng

Hình dạng `attachment` ở trên dựng theo tài liệu tin tư vấn dạng button của
Zalo, **chưa chạy thật qua khối động**. Endpoint mẫu Zalo gợi ý
(`chatbot.zalo.me/json-api?option=V_OPENAPI`) chỉ trả `{"text": "..."}` nên
phần `text` là chắc, phần nút là suy luận. Nếu **Test the Request** báo sai
định dạng thì chỉ sửa hai hàm `zalo_cau_hoi()` / `zalo_dap_an()` trong
`lms_service/services/cau_hoi_hang_ngay_service.py`, không đụng phần còn lại.

---

## 3. Quy tắc chọn câu

- **Kho câu**: 1.207 câu `is_active`, loại `TRAC_NGHIEM_1` hoặc `DUNG_SAI`,
  thuộc 9 lĩnh vực khai trong `DGNL_DAILY_MA_LINH_VUC`.
  Loại `TU_LUAN` và `TRAC_NGHIEM_NHIEU` bị loại vì không chấm được bằng một nút bấm.
- **Chốt một lần mỗi ngày**: lần gọi đầu bốc ngẫu nhiên rồi ghi vào
  `lms.cau_hoi_hang_ngay`; các lần sau trả đúng câu đó. Khoá chính là cột
  `ngay` nên hai tiến trình gọi cùng lúc không thể tạo hai câu khác nhau.
- **Không lặp lại**: chỉ bốc câu chưa từng phát. Hết mới vòng lại câu cũ nhất —
  với 1.207 câu thì hơn 3 năm mới chạm.
- **9 lĩnh vực khai tường minh**, không cắt tiền tố số của mã: cột `thu_tu`
  của mọi lĩnh vực trong DB đều bằng 0, và các mã `10.`/`11.`/`13.`/`14.` cũng
  bắt đầu bằng chữ số.

## 4. Bảo mật

- `ZALO_BOT_API_KEY` **để trống = tắt hẳn** (mọi lời gọi 401). Không có chế độ mở.
- Khoá **riêng**, không dùng lại `INTERNAL_API_KEY` — khoá bot nằm trong cấu
  hình phía Zalo nên phải tách phạm vi thiệt hại.
- `/dap-an` **chỉ trả đáp án cho câu đã từng phát**. Câu chưa phát → 404. Nhờ
  vậy dù lộ khoá thì cũng chỉ xem được những câu đã gửi ra ngoài, không moi
  được cả ngân hàng đề thi.
- Endpoint câu hỏi không chứa `dap_an_dung` lẫn `giai_thich` (có test chặn).

## 5. Triển khai

```bash
# 1. Sinh khoá rồi đặt vào backend/.env của cây prod
openssl rand -hex 32

# 2. Migration (chạy TỪ cây prod)
cd /opt/kpi-prod/backend && source venv/bin/activate && alembic upgrade head

# 3. Nạp lại service
pm2 restart lms-backend
```

Migration `lms_cau_hoi_hang_ngay_20260827` **chỉ thêm mới** bảng
`lms.cau_hoi_hang_ngay`, không sửa bảng nào đang chạy.

## 6. Kiểm thử

```bash
cd backend && source venv/bin/activate
DB_NAME=kpi_haiquan_test pytest lms_service/tests/test_dgnl_cong_khai.py -v
```

16 test: xác thực (3), chốt câu theo ngày (5), định dạng Zalo (2), đáp án (6).

⚠️ Service tự gọi `commit()` nên test **ghi thật** vào DB đang trỏ tới —
bắt buộc `DB_NAME=kpi_haiquan_test`.

## 7. Còn nợ

- Đối chứng định dạng `attachment` bằng **Test the Request** (mục 2).
- Xác nhận khối động đặt được trong quy tắc hẹn giờ hằng ngày.
- Nếu khối động truyền được `user_id`: thêm bảng ghi nhận ai trả lời gì để
  làm thống kê/xếp hạng theo đơn vị.
