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

## 3d. Cấu hình khối "Nhập liệu" — hai bẫy

Kịch bản gọn nhất chỉ cần **1 quy tắc**: hẹn giờ 08:00 → khối động lấy câu hỏi
→ khối **Nhập liệu** chờ trả lời → khối động thứ hai gọi `/dap-an`.

⛔ **"Lưu vào Chatbot" phải là trường TỰ TẠO**, ví dụ `dap_an_dgnl`. Tuyệt đối
không chọn trường có sẵn của Zalo (Họ Tên, SĐT, Email): câu trả lời sẽ ghi đè
lên dữ liệu thật, ai trả lời "A" thì họ tên trong danh bạ OA thành "A". Không
khôi phục được.

⏰ **Thời gian chờ mặc định 5 phút là quá ngắn.** Tin gửi 08:00, nhiều người
trưa chiều mới mở Zalo. Đặt 999 phút (~16 tiếng) là vừa nhịp một ngày một câu.

URL khối động thứ hai — không truyền `cau_hoi_id`, API tự lấy câu phát gần nhất:

```
…/dgnl/cong-khai/dap-an?chon={{tên_trường_tự_tạo}}&dinh_dang=zalo
```

## 3e. Bấm nút gửi về cái gì — đối chứng thật 27/08/2026

Zalo **không** gửi về chuỗi `A`. Nó gửi nguyên object payload đã chuyển thành
chuỗi:

```
{"content":"A"}
```

Xem được trong hộp thư OA (tin `oa.query.hide` ẩn với người dùng nhưng quản
trị viên vẫn thấy). Người gõ tay thì gửi về `A` trơn.

⚠️ Đây từng là một **lỗi im lặng**: bỏ hết dấu của `{"content":"A"}` còn
`contentA`, lấy ký tự đầu ra `C` → **mọi lần bấm nút đều bị chấm thành C**, mà
kết quả trả về vẫn trông hợp lý nên rất khó phát hiện. `_chuan_hoa_chon()` nay
bóc `content` bằng `json.loads`, hỏng thì vớt bằng regex, vẫn không được thì
trả `None` (thà không chấm còn hơn chấm nhầm).

Hệ quả cho kịch bản chatbot: biến của khối Nhập liệu sẽ chứa cả chuỗi
`{"content":"A"}`. **Không sao** — cứ truyền nguyên vào `chon=`, API tự bóc.

## 3f. Zalo gửi gì tới khối Dynamic — soi thật 27/08/2026

Bật `DGNL_SOI_YEU_CAU=true` (chỉ dev) rồi đọc `/tmp/kpi-dev-logs/lms.log`:

```
[SOI dap-an] GET  ip=49.213.78.2 query={'chon':'B'} than=<rỗng>
[SOI dap-an] POST ip=49.213.78.2 query={'chon':'A'} than=<rỗng> content-length: 0
headers: host, x-real-ip, x-forwarded-for, x-forwarded-proto, connection,
         content-type: application/json, user-agent: ZPChatbot, x-bot-key
```

**Zalo KHÔNG gửi kèm định danh người dùng.** Không `user_id`, không mã hội
thoại — cả GET lẫn POST, POST thì thân rỗng hẳn.

Hệ quả: **không chặn spam theo từng người được** qua đường chatbot. Chặn theo
IP cũng vô nghĩa vì mọi lời gọi đều từ dải IP của Zalo (`49.213.78.x`), cắt là
cắt của tất cả. Muốn chặn theo người thì phải tự gửi bằng `user_id` + webhook
(xem mục 7).

Được một thứ: `user-agent: ZPChatbot` dùng để xác minh nguồn gọi — giả mạo
được nên chỉ là lớp phụ, không thay khoá.

Lưu ý về chi phí: `tran_chi.py` chặn ở `gui_hang_doi()` của worker ZNS nên
**không** nhìn thấy tin do chatbot Zalo gửi. Theo xác nhận của quản trị OA
(27/08/2026), hạn mức **Zalo Cloud Account nay gộp chung với ZBS**, nên phần
chi của luồng chatbot đã nằm trong hạn mức đó — không cần dựng thêm trần.

Ước lượng rủi ro spam: tin tư vấn miễn phí 8 tin đầu trong 48h, sau đó 55đ/tin
— phải trên 7 lần trả lời trong 48h mới bắt đầu mất tiền. 10 người nghịch 50
lần ≈ 24.000đ. Chấp nhận được, và không chặn theo từng người được (xem trên).

**Vì sao gặp nhiều giới hạn đến vậy:** OA của Chi cục là **OA cơ quan nhà
nước**. Ba bức tường gặp phải khi dựng kịch bản — không tạo được trường tuỳ
biến, tối đa 4 quy tắc, không có bước điều kiện — đều là giới hạn tính năng của
loại OA này, không phải cấu hình sai.

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

40 test: xác thực (3), chốt câu theo ngày (5), định dạng Zalo (8), đáp án (24).

⚠️ Service tự gọi `commit()` nên test **ghi thật** vào DB đang trỏ tới —
bắt buộc `DB_NAME=kpi_haiquan_test`.

## 7. Còn nợ

- ✅ ~~Đối chứng định dạng `attachment`~~ — đã chạy thật 27/08, tin hiện đúng
  kèm 4 nút trên Zalo điện thoại.
- Dựng kịch bản 2 (từ khoá `A`/`B`/`C`/`D`) — xem mục 3c. Bấm nút hiện chưa có
  phản hồi vì chưa có quy tắc nào bắt.
- Xác nhận khối động đặt được trong quy tắc hẹn giờ hằng ngày.
- Thử **Phản hồi nhanh** A/B/C/D của Zalo trong khối Nhập liệu — có thể hiện
  được trên Zalo máy tính, chỗ mà nút trong `attachment` không hiện.
- ❌ ~~Nếu khối động truyền được `user_id`~~ — đã soi, Zalo không gửi (mục 3f).
  Muốn thống kê theo người thì phải tự gửi bằng OA Message API.

**Về việc "gửi bằng UID đã thử và thất bại" (mục 5.3 của PHAN_TICH_CHI_PHI_ZNS.md):**
lần đó thử trên `business.openapi.zalo.me/message/template` — tức **ZBS/ZNS**,
gửi tin mẫu theo số điện thoại, mục đích là hưởng giá 560đ thay vì 800đ. Endpoint
đó đòi số điện thoại nên trả `-108` (số điện thoại không hợp lệ) khi đưa UID vào.

Đó là **một sản phẩm khác** với OA Message API
(`openapi.zalo.me/v3.0/oa/message/cs` — tin tư vấn), vốn định địa chỉ bằng
`user_id` chứ không bằng số điện thoại. Thất bại của ZNS-theo-UID **không**
chứng minh `message/cs` bị chặn. Nhưng cũng chưa có gì chứng minh nó chạy: quyền
*gửi tin tư vấn* chưa từng được xin cho ứng dụng này. Muốn biết chắc thì phải
nộp duyệt quyền rồi thử — không suy ra được từ dữ liệu hiện có.


## 8. Lọc người nhận bằng nhãn — đã làm 28/08/2026

OA có **758 người theo dõi**, chỉ ~327 là công chức. Hơn 400 người còn lại là
người dân. Quy tắc hẹn giờ của chatbot lọc được người nhận **theo nhãn**, nên
phải gắn nhãn cho đúng nhóm công chức.

### Đã làm

| Bước | Lệnh | Kết quả |
|---|---|---|
| Quét UID | `python scripts/zalo_tra_uid.py --tat-ca --ghi` | 327/543 có `zalo_user_id` (60,2%) |
| Gắn nhãn | `python scripts/zalo_gan_nhan_cong_chuc.py --ghi` | 327 người, 0 lỗi |

Đối chứng lại từ phía Zalo (`getfollowers` theo `tag_name`):

```
CC_HQKV08_1  119      HQQN  70   ← nhãn cũ của Hải quan Quảng Ninh, KHÔNG đụng
CC_HQKV08_2  111
CC_HQKV08_3   97
  cộng      327
```

**Quy tắc 08:00 phải nhắm cả ba nhãn `CC_HQKV08_*`.**

### Vì sao ba nhãn chứ không một

Zalo giới hạn **200 người/nhãn**; vượt quá thì hệ thống **tự gỡ nhãn của người
được gắn lâu nhất, không báo gì** — người bị gỡ lặng lẽ không nhận tin nữa.
Script chia theo `int(user_id) % số_nhãn` nên mỗi người luôn rơi vào cùng một
nhãn qua mọi lần chạy; chia theo thứ tự danh sách thì thêm một người ở đầu là
dồn toàn bộ phía sau sang nhãn khác.

Ngưỡng đặt 150/nhãn (không phải 200) để còn chỗ cho người follow thêm giữa hai
lần chạy.

### Chạy lại định kỳ

Công chức mới follow OA sẽ **không có nhãn** và lặng lẽ không nhận được câu
hỏi. Script chạy lại được nhiều lần (gắn lại nhãn cũ là thao tác vô hại):

```bash
0 6 * * 1  cd /opt/kpi-prod/backend && venv/bin/python \
           scripts/zalo_gan_nhan_cong_chuc.py --ghi >> /var/log/zalo-nhan.log 2>&1
```

### ⚠️ Độ phủ thật chỉ 60%

```
543 công chức
327 đã follow OA   ← chỉ nhóm này nhận được tin
172 chưa follow    ← không nhận gì, gắn nhãn cũng vô ích
 44 số hỏng        ← đơn vị cần rà lại danh bạ
```

Gắn nhãn **không** cải thiện con số này. Muốn phủ hết phải có đợt phổ biến để
172 người kia quan tâm OA — việc hành chính, không phải việc kỹ thuật. Nếu lãnh
đạo kỳ vọng "cả cơ quan cùng ôn tập" thì con số thật hiện là 6/10 người.

### Còn nợ

Công chức nghỉ hưu / chuyển công tác vẫn giữ nhãn cũ. Muốn gỡ thì bổ sung nhánh
gọi `rmfollowerfromtag` cho người có `is_active = false`.
