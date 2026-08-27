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
| `cau_hoi_id` | không | Lấy từ payload nút. **Để trống = câu phát gần nhất.** |
| `chon` | không | `A`/`B`/`C`/`D`. Có thì mới chấm đúng/sai. |
| `dinh_dang` | không | `zalo` |

Hai đường gọi:

- **Người bấm nút** → có `cau_hoi_id`, trả đúng câu họ đã nhận. Không tra theo
  ngày vì họ có thể bấm lúc nửa đêm hoặc sáng hôm sau.
- **Người gõ tay `A`/`B`** → không có `cau_hoi_id`, lấy **câu phát gần nhất**.
  Kịch bản chatbot chỉ bắt được chữ cái, không có cách nào biết id.

`chon` được chuẩn hoá rộng tay: `a`, `A.`, `(a)`, `A)`, ` a ` đều hiểu là `A`.

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
        {"title": "A", "type": "oa.query.hide",
         "payload": {"content": "A"}}
      ]
    }
  }
}
```

Khi người dùng bấm nút, Zalo gửi `payload.content` về — **chỉ là chữ cái**
`A`/`B`/`C`/`D`, cố ý để trùng với thứ người dùng Zalo máy tính gõ tay. Nhờ vậy
**một** quy tắc từ khoá lo được cả hai đường, không phải tách chuỗi. Gọi:

```
https://kpihaiquan.vn/api/v1/lms/dgnl/cong-khai/dap-an?chon=<A|B|C|D>&dinh_dang=zalo
```

Kết quả trả về cũng là object `message`, gửi thẳng cho người dùng:

```json
{"text": "❌ Chưa đúng. Bạn chọn A, đáp án đúng là D.\n…\n\n📖 Giải thích: …"}
```

### ✅ Đã đối chứng 27/08/2026

Chạy thật qua khối động: Zalo hiểu JSON này là một tin nhắn thật, hiện đúng nội
dung câu hỏi kèm 4 nút A/B/C/D trên **Zalo điện thoại**. Định dạng ở trên là
đúng, không phải sửa.

Hai lưu ý rút ra từ lần chạy đầu:

- **Không để dòng header trống** trong hộp thoại Edit Request. Zalo vẫn gửi
  chúng đi, tạo dòng header rỗng, và nginx trả **400 Bad Request** trước khi
  request chạm tới ứng dụng. Bấm nút thùng rác đỏ xoá hết dòng trống.
- **Zalo máy tính không hiện nút** — xem mục 3b.

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

## 3b. Zalo máy tính không hiện nút

Quan sát thực tế 27/08/2026: tin nhắn kèm nút hiện đúng trên **Zalo điện
thoại**, nhưng **Zalo máy tính không hiện nút**. Đây là hạn chế phía Zalo,
không sửa được từ phía mình.

Cách vá: thân tin luôn có dòng *"Bấm nút bên dưới, hoặc nhắn A/B/C/D nếu bạn
dùng Zalo máy tính"*, và `/dap-an` chấp nhận gọi **không kèm `cau_hoi_id`**.
Chatbot chỉ cần một quy tắc bắt từ khoá `A`/`B`/`C`/`D` rồi gọi:

```
…/dgnl/cong-khai/dap-an?chon=<chữ người dùng gõ>&dinh_dang=zalo
```

Nhãn nút cũng đã rút gọn còn `A`/`B`/`C`/`D` — nội dung phương án đã nằm ở
thân tin, để cả câu trên nút làm khung chat dài gấp đôi.

## 3c. Cần dựng mấy quy tắc trên Zalo OA

Tối thiểu **2 kịch bản**:

| # | Kịch bản | Quy tắc kích hoạt | Khối động gọi |
|---|---|---|---|
| 1 | Câu hỏi | Hẹn giờ, lặp hằng ngày 08:00 | `/cau-hoi-hang-ngay?dinh_dang=zalo` |
| 2 | Đáp án | Từ khoá `A`, `B`, `C`, `D` | `/dap-an?chon=…&dinh_dang=zalo` |

Kịch bản 2 phục vụ **cả** người bấm nút lẫn người gõ tay, vì payload nút đã là
chữ cái.

Nếu quy tắc từ khoá **truyền được** chữ đã khớp vào URL → đúng 2 kịch bản.
Nếu **không truyền được** → tách thành 4 quy tắc, mỗi chữ cái một quy tắc trỏ
tới một URL cố định (`…&chon=A`, `…&chon=B`, …). Xấu hơn nhưng chắc chắn chạy
và không cần xử lý biến.

Thêm một quy tắc **tạm** với từ khoá `CAUHOI` chạy kịch bản 1 để test — sửa và
xem kết quả trong 10 giây thay vì chờ sang hôm sau. Xoá sau khi xong.

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

25 test: xác thực (3), chốt câu theo ngày (5), định dạng Zalo (3), đáp án (14).

⚠️ Service tự gọi `commit()` nên test **ghi thật** vào DB đang trỏ tới —
bắt buộc `DB_NAME=kpi_haiquan_test`.

## 7. Còn nợ

- ✅ ~~Đối chứng định dạng `attachment`~~ — đã chạy thật 27/08, tin hiện đúng
  kèm 4 nút trên Zalo điện thoại.
- Dựng kịch bản 2 (từ khoá `A`/`B`/`C`/`D`) — xem mục 3c. Bấm nút hiện chưa có
  phản hồi vì chưa có quy tắc nào bắt.
- Xác nhận khối động đặt được trong quy tắc hẹn giờ hằng ngày.
- Nếu khối động truyền được `user_id`: thêm bảng ghi nhận ai trả lời gì để
  làm thống kê/xếp hạng theo đơn vị.
