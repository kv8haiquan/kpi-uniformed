# Chuẩn bị tài khoản Zalo OA — Tài liệu nghiên cứu

**Ngày soạn:** 31/07/2026
**Bối cảnh:** Chi cục đã có Zalo OA (loại cơ quan nhà nước, đã xác thực), nhưng
người triển khai kỹ thuật **không phải là người quản lý OA**.
**Liên quan:** `docs/zalo-oa/HUONG_DAN_TRIEN_KHAI.md` (phần kỹ thuật đã code xong)

> ⚠️ **Về độ tin cậy của tài liệu này**
>
> Phần *hệ thống của ta cần gì* (mục 4) là chắc chắn — lấy trực tiếp từ code đã
> viết, có thể kiểm chứng bằng `grep settings.zalo_` trong `backend/common_service/`.
>
> Phần *quy trình và tên gọi trên Zalo* (mục 2, 3, 6) có thể đã đổi: Zalo thay
> đổi giao diện, tên vai trò, chính sách ZNS và luồng OAuth khá thường xuyên.
> Hãy coi đây là bản đồ để định hướng, còn số liệu và thao tác cụ thể thì đối
> chiếu với giao diện thực tế và tài liệu chính thức tại `developers.zalo.me`.
> Chỗ nào tôi không chắc, tôi ghi rõ là không chắc.

---

## 1. Vấn đề cần giải quyết

Hệ thống cần gửi 4 loại thông báo họp qua Zalo tới công chức: giấy mời họp,
nhắc họp, thay đổi lịch, hủy họp. Khối lượng thực tế khoảng **100 tin/tháng**.

Phần mềm đã viết xong và test đủ. Thứ duy nhất còn thiếu là **quyền truy cập
và mấy giá trị cấu hình từ tài khoản Zalo OA** — mà những thứ đó chỉ người
quản lý OA lấy được.

---

## 2. Ba khái niệm rất dễ lẫn

Đây là chỗ gây nhầm nhiều nhất, cần phân biệt rõ trước khi đi xin việc gì:

| | **Official Account (OA)** | **Ứng dụng (App)** | **ZNS** |
|---|---|---|---|
| Là gì | Trang chính thức của cơ quan trên Zalo | Danh tính kỹ thuật để gọi API | Dịch vụ gửi tin theo số điện thoại |
| Quản ở đâu | `oa.zalo.me` | `developers.zalo.me` | Đăng ký/duyệt riêng |
| Chi cục đã có? | ✅ Có, đã xác thực | ❓ **Chưa rõ — cần kiểm tra** | ❓ **Chưa rõ — cần hỏi VNG** |

**Điểm quan trọng nhất:** có OA **không** có nghĩa là có App ID. OA và Ứng dụng
là hai thực thể riêng, phải **liên kết** với nhau. Rất nhiều người tưởng chỉ cần
OA là gọi API được.

Quan hệ giữa ba thứ:

```
   Ứng dụng (App)  ──liên kết──▶  OA của Chi cục
        │                              │
        │ cho ta App ID + Secret       │ cho ta quyền gửi tin
        │                              │
        └────────► gọi API ZNS ◄───────┘
                        │
                   phải được bật
                   + template duyệt trước
```

---

## 3. Vai trò trên OA — ai làm được gì

> Tên vai trò dưới đây theo cách gọi phổ biến; giao diện thực tế có thể khác.
> Việc cần kiểm tra là **ai có quyền cao nhất**, không phải tên gọi chính xác.

| Vai trò | Làm được | Làm được việc ta cần? |
|---|---|---|
| Quản trị viên / Admin | Toàn quyền, gồm liên kết ứng dụng và uỷ quyền API | ✅ Có |
| Điều hành / Biên tập | Đăng bài, trả lời tin nhắn | ❌ Không |
| Chăm sóc khách hàng | Chỉ chat | ❌ Không |

**Việc bắt buộc cần quyền Admin:**
1. Liên kết ứng dụng với OA
2. Thực hiện uỷ quyền OAuth (bước sinh ra `refresh_token`)
3. Đăng ký ZNS và gửi template đi duyệt

Nói cách khác: **không có quyền Admin thì không làm được gì trong 3 việc trên.**

---

## 4. Những giá trị hệ thống cần (phần chắc chắn)

### 4.1. Bắt buộc để hệ thống chạy — 3 giá trị

| Giá trị | Đưa vào đâu | Ghi chú |
|---|---|---|
| **App ID** | `backend/.env` → `ZALO_APP_ID` | Dãy số, lấy ở trang ứng dụng |
| **App Secret Key** | `backend/.env` → `ZALO_OA_SECRET` | Khoá bí mật của ứng dụng |
| **refresh_token** | **Database**, không phải .env | Nạp bằng `scripts/zalo_nap_token.py` |

**Vì sao `refresh_token` không để trong file cấu hình:** Zalo cấp
`refresh_token` **mới** sau mỗi lần làm mới và vô hiệu hoá cái cũ. Nếu để trong
`.env` thì sau lần làm mới đầu tiên, giá trị trong file đã chết — lần khởi động
lại kế tiếp hệ thống sẽ không lấy được token nào dùng được. Vì vậy nó nằm ở
bảng `common.zalo_token` để ghi đè được.

Hệ quả cần biết: **`refresh_token` chỉ dùng được đúng một lần.** Nếu ai đó chạy
lại luồng uỷ quyền sau khi hệ thống đã làm mới token, giá trị cũ hết hiệu lực
và phải xin lại từ đầu.

### 4.2. Cần để gửi được tin thật — 4 template ID

Zalo cấp một ID cho mỗi template ZNS sau khi duyệt:

```
ZALO_TPL_MOI_HOP=        # Giấy mời họp
ZALO_TPL_NHAC_HOP=       # Nhắc họp — dùng CHUNG cho cả 3 mốc 24h/1h/30 phút
ZALO_TPL_THAY_DOI_HOP=   # Thay đổi lịch họp
ZALO_TPL_HUY_HOP=        # Hủy họp
```

Để trống vẫn chạy bình thường — hệ thống đánh dấu `BO_QUA/KHONG_CO_TEMPLATE`
chứ không báo lỗi. Nhờ vậy **bật dần từng template được**, Zalo duyệt xong cái
nào thì điền cái đó.

### 4.3. Không cần

**`ZALO_OA_ID` không cần thiết.** Đã kiểm tra lại code: biến này không được
dùng trong bất kỳ lời gọi API nào (`access_token` đã định danh OA). Vẫn giữ
trong cấu hình để ghi lại hệ thống đang gắn với OA nào, phục vụ đối soát và hồ
sơ ATTT, nhưng **để trống thì chạy bình thường**.

---

## 5. Hai phương án khi không phải người quản lý OA

### Phương án A — Xin cấp quyền Quản trị viên trên OA

| | |
|---|---|
| **Ưu điểm** | Tự chủ hoàn toàn; về sau token hỏng, cần thêm template, đổi cấu hình đều tự xử lý được trong vài phút |
| **Nhược điểm** | Phải qua thủ tục hành chính; người đang quản có thể e ngại chia quyền trên trang chính thức của cơ quan |
| **Nên chọn khi** | Việc này là lâu dài (đúng với trường hợp này — kênh thông báo dùng liên tục) |

### Phương án B — Nhờ người quản lý OA thực hiện, mình chỉ nhận kết quả

| | |
|---|---|
| **Ưu điểm** | Không cần thủ tục chia quyền |
| **Nhược điểm** | Mỗi lần cần thao tác lại phải nhờ; token hỏng vào cuối tuần thì kênh thông báo chết cho tới khi liên lạc được |
| **Nên chọn khi** | Chỉ làm thử nghiệm ngắn hạn |

### Khuyến nghị

Đi **phương án A**, và nói rõ lý do kỹ thuật khi xin quyền:

> `refresh_token` của Zalo có thể mất hiệu lực (hết hạn nếu lâu không dùng, hoặc
> bị vô hiệu khi có người chạy lại luồng uỷ quyền). Khi đó **bắt buộc phải uỷ
> quyền lại bằng tay** với quyền Admin. Nếu người có quyền không phải người vận
> hành hệ thống, mỗi sự cố như vậy sẽ làm kênh thông báo họp chết cho tới khi
> liên lạc được — trong khi thông báo họp là loại tin nhạy cảm về thời gian.

Nếu không xin được quyền, phương án B vẫn chạy được, chỉ cần **thoả thuận trước
một đầu mối và cách liên lạc khi có sự cố**.

Có một phương án trung gian đáng cân nhắc: cấp quyền Admin cho **một tài khoản
Zalo dùng riêng cho việc kỹ thuật** (không phải Zalo cá nhân của ai), do bộ phận
CNTT giữ. Cách này tránh được cả chuyện chia quyền cá nhân lẫn chuyện phụ thuộc
một người.

---

## 6. Phiếu yêu cầu — gửi cho người quản lý OA

> Cắt phần dưới đây gửi cho người đang quản lý OA. Đã viết sẵn để họ không cần
> hiểu kỹ thuật.

---

**ĐỀ NGHỊ CUNG CẤP THÔNG TIN KỸ THUẬT ZALO OA**

Kính gửi anh/chị đang quản lý Zalo OA của Chi cục,

Chúng tôi đang triển khai gửi thông báo họp (giấy mời, nhắc họp, thay đổi, hủy)
qua Zalo cho công chức, thay cho việc chỉ hiện thông báo trong phần mềm. Lý do:
đo trên dữ liệu thực tế, thông báo trong phần mềm trung bình phải **58 giờ** mới
được đọc — tức là cuộc họp đã tan.

Đề nghị anh/chị hỗ trợ các nội dung sau:

**A. Kiểm tra hiện trạng** (chỉ cần trả lời có/không)

- [ ] OA của Chi cục đã có **Ứng dụng (App)** nào được liên kết chưa? Nếu có, tên là gì?
- [ ] OA đã đăng ký dịch vụ **ZNS** (Zalo Notification Service) chưa?
- [ ] Hiện có bao nhiêu người có quyền **Quản trị viên** trên OA?

**B. Thông tin cần cung cấp** (nếu đã có Ứng dụng)

- [ ] **App ID**: ........................
- [ ] **App Secret Key**: ........................ *(vui lòng gửi qua kênh riêng, không gửi qua email/chat nhóm)*

**C. Nếu chưa có Ứng dụng** — đề nghị tạo mới tại `developers.zalo.me`, liên
kết với OA của Chi cục, và khai báo Callback URL:

```
https://kpihaiquan.vn/zalo-callback
```

**D. Đề nghị về quyền**

- [ ] Cấp quyền **Quản trị viên** trên OA cho tài khoản: ........................
      *(hoặc cho một tài khoản Zalo dùng riêng cho kỹ thuật do CNTT giữ)*
- [ ] Nếu không cấp quyền được: đề nghị cử một đầu mối để phối hợp thực hiện
      bước uỷ quyền API, và cho biết cách liên lạc khi có sự cố ngoài giờ.

**E. Về ZNS** — đề nghị liên hệ VNG/Zalo hỏi rõ:

- [ ] OA cơ quan nhà nước của Chi cục có được bật **ZNS** không?
- [ ] Mức phí hoặc chính sách ưu đãi cho cơ quan nhà nước?
- [ ] Có cần thêm thủ tục xác minh tổ chức, hay liên kết phương thức thanh toán?

Khối lượng dự kiến khoảng **100 tin/tháng**.

**F. Cam kết về nội dung tin nhắn**

Tin nhắn Zalo **chỉ** chứa: họ tên người nhận, thời gian họp, và lời nhắc mở
phần mềm. **Không** chứa tiêu đề cuộc họp, địa điểm, thành phần dự, hay bất kỳ
nội dung tài liệu nào. Đây là quyết định có chủ đích để nội dung họp nội bộ
không đi qua hệ thống của bên thứ ba.

---

## 7. Bốn nội dung template đề xuất

Gửi Zalo duyệt. Tham số hệ thống hỗ trợ **chỉ có** `ho_ten`, `thoi_gian`, `moc`
— soạn nội dung không được dùng biến nào khác.

**Template 1 — Giấy mời họp**
```
Kính gửi {{ho_ten}},
Bạn có lịch họp vào {{thoi_gian}}.
Vui lòng truy cập phần mềm để xem giấy mời và tài liệu họp.
```

**Template 2 — Nhắc họp** *(dùng chung cho cả 3 mốc)*
```
Kính gửi {{ho_ten}},
Nhắc lịch họp {{moc}}: cuộc họp bắt đầu {{thoi_gian}}.
Vui lòng truy cập phần mềm để xem chi tiết.
```
> `{{moc}}` nhận một trong ba giá trị: "trước 24 giờ", "trước 1 giờ",
> "trước 30 phút". Gộp 3 mốc vào 1 template để chỉ phải xin duyệt 4 thay vì 6.

**Template 3 — Thay đổi lịch họp**
```
Kính gửi {{ho_ten}},
Lịch họp của bạn đã được thay đổi. Thời gian mới: {{thoi_gian}}.
Vui lòng truy cập phần mềm để xem chi tiết.
```

**Template 4 — Hủy họp**
```
Kính gửi {{ho_ten}},
Cuộc họp dự kiến {{thoi_gian}} đã được hủy.
Vui lòng truy cập phần mềm để xem thông báo.
```

Nếu Zalo yêu cầu sửa câu chữ để được duyệt thì cứ sửa thoải mái — hệ thống
không phụ thuộc vào câu chữ, chỉ phụ thuộc **tên các tham số**. Giữ đúng
`ho_ten`, `thoi_gian`, `moc` là được.

---

## 8. Luồng lấy `refresh_token` — phần tôi không chắc

Đại ý gồm ba bước:

1. Mở URL uỷ quyền trên trình duyệt, **đăng nhập bằng tài khoản có quyền Admin OA**
2. Zalo chuyển về Callback URL kèm một tham số `code` (dùng được rất ngắn)
3. Đổi `code` đó lấy cặp `access_token` + `refresh_token`

**Chỗ tôi không chắc:** luồng OAuth của Zalo đã đổi vài lần, phiên bản gần đây
dùng thêm PKCE (`code_challenge` / `code_verifier`). Tôi không muốn viết sẵn
script theo mô tả cũ rồi bạn mắc ở bước cuối mà không rõ vì sao.

**Cách xử lý:** sau khi có App ID và Secret, gửi tôi ảnh chụp hoặc link trang
tài liệu OAuth mà Zalo Developers đang hiển thị cho ứng dụng của bạn. Tôi sẽ
viết script đổi `code` → token đúng theo phiên bản đang áp dụng. Việc này chỉ
chạy một lần duy nhất nên chưa viết trước.

---

## 9. Lưu ý bảo mật

**Về việc gửi Secret Key:** đây là khoá cho phép nhân danh OA của Chi cục gửi
tin. Không gửi qua email hay chat nhóm. Ai có nó đều gửi được tin nhắn mang
danh Chi cục.

**Về nơi lưu:** `App Secret` vào `backend/.env`; file này đã nằm trong
`.gitignore` nên không lên git. `refresh_token` vào database.

**Cần làm trước:** `backend/.env` hiện đang là quyền **644 (mọi người trên
server đọc được)**. Nên siết về **600** trước khi thêm secret mới. Đây là một
lệnh, không cần khởi động lại service nào.

**Về số điện thoại:** là dữ liệu cá nhân theo **Nghị định 13/2023/NĐ-CP**. Nên
có văn bản thông báo nội bộ cho công chức biết trước khi dùng để gửi thông báo.
Hệ thống đã có sẵn cờ `da_dong_y` để tắt riêng cho ai yêu cầu ngừng nhận.

**Về bề mặt tấn công:** giai đoạn 1 **cố ý không mở webhook** — hệ thống chỉ
gọi ra, không nhận vào, nên không thêm điểm truy cập công khai nào. Nếu sau này
cần webhook nhận trạng thái gửi thì bắt buộc xác thực chữ ký `X-ZEvent-Signature`
trước khi xử lý dữ liệu.

**Ghi cho hồ sơ ATTT (CV 153/CNTT):** đây là **phụ thuộc bên thứ ba đầu tiên**
của hệ thống. Trước đợt này, mọi lời gọi HTTP của backend đều là nội bộ qua
localhost. Nên whitelist domain Zalo ở tầng firewall thay vì để egress mở hoàn
toàn như hiện nay.

---

## 10. Việc cần làm, theo thứ tự

| # | Việc | Ai làm | Chặn cái gì |
|---|---|---|---|
| 1 | Hỏi VNG: OA có bật ZNS được không, phí thế nào | Người quản lý OA | **Chặn tất cả** |
| 2 | Xác định ai có quyền Admin OA | Bạn | Bước 3, 5 |
| 3 | Tạo/kiểm tra Ứng dụng, liên kết OA, khai Callback URL | Admin OA | Bước 5 |
| 4 | Lấy App ID + Secret | Admin OA | Bước 5 |
| 5 | Chạy uỷ quyền lấy `refresh_token` | Admin OA | Gửi tin |
| 6 | Gửi 4 template đi duyệt | Admin OA | Gửi tin |
| 7 | Gom danh sách số điện thoại công chức | TCCB / Văn phòng | Gửi tin |
| 8 | Siết quyền `backend/.env` về 600 | Kỹ thuật | — |

**Bước 1 là đường găng.** Nếu OA không bật được ZNS thì toàn bộ hướng đi phải
đổi sang phương án OA-follow (mỗi công chức tự bấm theo dõi OA), và đó là dự án
khác hẳn về công sức triển khai — nên hỏi việc này trước khi làm gì khác.

**Bước 7 chạy song song được**, không phụ thuộc bước nào. Hiện database chỉ có
**6/544** công chức có số điện thoại, nên đây có thể là việc mất nhiều thời gian
nhất. Script đối chiếu đã viết xong, chạy ở chế độ thử không ghi gì:

```bash
cd /root/kpi-haiquan/backend && source venv/bin/activate
PYTHONPATH=$PWD python scripts/zalo_import_sdt.py danh_sach.xlsx \
    --xuat-loi loi_can_ra_soat.csv
```

File đầu vào chỉ cần 2 cột: `ma_cc` và `so_dien_thoai`. Script tự chuẩn hoá mọi
kiểu viết (`0913...`, `+84913...`, số 11 chữ số cũ trước 2018), tự loại số máy
bàn, tự phát hiện số trùng giữa hai người, và báo độ phủ theo phần trăm.

---

## 11. Thuật ngữ

| Từ | Nghĩa |
|---|---|
| **OA** | Official Account — trang chính thức của tổ chức trên Zalo |
| **App / Ứng dụng** | Danh tính kỹ thuật để gọi API Zalo; phải liên kết với OA |
| **ZNS** | Zalo Notification Service — gửi tin theo **số điện thoại**, không cần người nhận theo dõi OA, nội dung phải theo template đã duyệt |
| **OA message API** | Gửi tin theo `user_id`, **bắt buộc** người nhận đã theo dõi OA |
| **`user_id`** | Mã người dùng riêng theo từng OA. **Không tra được từ số điện thoại** — Zalo chặn có chủ đích vì lý do riêng tư |
| **Template** | Mẫu tin cố định được Zalo duyệt trước; chỉ điền được vào các ô tham số |
| **`access_token`** | Vé gọi API, sống khoảng 1 giờ |
| **`refresh_token`** | Dùng để xin `access_token` mới; **đổi giá trị sau mỗi lần dùng** |
| **Callback URL** | Địa chỉ Zalo chuyển về sau khi uỷ quyền, kèm tham số `code` |
| **PKCE** | Cơ chế bảo vệ luồng uỷ quyền OAuth; phiên bản Zalo gần đây có dùng |
