# Hướng dẫn tạo `dev.kpihaiquan.vn`

> Mục đích: vào môi trường phát triển bằng trình duyệt mà không phải mở đường
> hầm SSH mỗi lần. Đọc kèm `HUONG_DAN_DEV_PROD.md`.
>
> **✅ ĐÃ DỰNG XONG 19/08/2026** — https://dev.kpihaiquan.vn
> Tài khoản `hqkv8`, mật khẩu lưu tại `/root/.dev-htpasswd-note` (chmod 600).
> Chứng chỉ hết hạn 17/11/2026, certbot tự gia hạn.
> Phần dưới giữ lại làm tài liệu tham chiếu và để dựng lại khi cần.

---

## 0. Cân nhắc trước khi làm

Cách hiện tại — **đường hầm SSH** — không cần cấu hình gì và không mở cổng nào
ra Internet:

```bash
ssh -L 3001:127.0.0.1:3001 -L 9000:127.0.0.1:9000 -L 9006:127.0.0.1:9006 root@79.108.216.189
# rồi vào http://localhost:3001
```

Làm subdomain tiện hơn, nhưng đổi lại **môi trường dev có mặt trên Internet**.
Mà dev thì chứa bản sao dữ liệu thật của 549 công chức, chạy code chưa kiểm thử,
và không được vá bảo mật cùng nhịp với prod.

Nên nếu làm, **lớp bảo vệ là bắt buộc, không phải tuỳ chọn** — mục 2 dưới đây.

Hiện trạng:

| | |
|---|---|
| IP máy chủ | `79.108.216.189` |
| DNS quản lý bởi | **Viettel IDC** (`ns.viettelidc.com.vn`) |
| Đã trỏ về IP này | `kpihaiquan.vn`, `www.kpihaiquan.vn` |
| Chứng chỉ hiện có | `kpihaiquan.vn` + `www` — hết hạn 22/09/2026 |

---

## 1. Tạo bản ghi DNS (anh làm trên trang Viettel IDC)

Đăng nhập trang quản trị tên miền của Viettel IDC, vào phần quản lý DNS của
`kpihaiquan.vn`, thêm một bản ghi:

| Trường | Giá trị |
|---|---|
| Loại (Type) | **A** |
| Tên (Name / Host) | **dev** |
| Giá trị (Value / Points to) | **79.108.216.189** |
| TTL | 3600 (hoặc để mặc định) |

> Ô "Name" chỉ điền `dev`, không điền `dev.kpihaiquan.vn` — hệ thống tự ghép
> phần tên miền. Điền đủ sẽ thành `dev.kpihaiquan.vn.kpihaiquan.vn`.

Lưu lại rồi **chờ DNS lan truyền**. Thường 5–30 phút, có thể tới vài giờ.

### Kiểm tra đã xong chưa

Chạy trên máy chủ:

```bash
dig +short dev.kpihaiquan.vn A
```

Ra `79.108.216.189` là được. Chưa ra gì thì chờ thêm — **đừng sang bước 3**,
vì certbot cần DNS trỏ đúng mới cấp được chứng chỉ.

---

## 2. Đặt mật khẩu bảo vệ (làm trước khi bật nginx)

```bash
apt-get install -y apache2-utils          # nếu chưa có lệnh htpasswd
htpasswd -c /etc/nginx/.htpasswd-dev <tên-đăng-nhập>
# nhập mật khẩu 2 lần

chmod 640 /etc/nginx/.htpasswd-dev
chown root:www-data /etc/nginx/.htpasswd-dev
```

Thêm người dùng khác về sau thì **bỏ `-c`** (có `-c` là tạo file mới, xoá hết
người cũ):

```bash
htpasswd /etc/nginx/.htpasswd-dev <tên-khác>
```

Chọn mật khẩu khác mật khẩu hệ thống KPI. Đây là lớp chắn duy nhất giữa
Internet và bản sao dữ liệu thật.

### Chặt hơn nữa: giới hạn theo địa chỉ IP

Nếu cơ quan có IP tĩnh, thêm vào đầu khối `server` trong cấu hình nginx:

```nginx
allow 203.0.113.0/24;   # thay bằng dải IP của cơ quan
deny all;
```

Dùng kèm mật khẩu thì phải qua cả hai lớp.

---

## 3. Bật cấu hình nginx

```bash
# Snippet dùng chung cho các location
mkdir -p /etc/nginx/snippets
cat > /etc/nginx/snippets/dev-proxy.conf <<'EOF'
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
EOF

# Cấu hình dev — bản mẫu đã chuẩn bị sẵn trong repo
cp /root/kpi-haiquan/docs/van-hanh/nginx-dev.conf.mau \
   /etc/nginx/sites-available/kpi-dev
ln -s /etc/nginx/sites-available/kpi-dev /etc/nginx/sites-enabled/kpi-dev

nginx -t          # PHẢI thấy "syntax is ok" và "test is successful"
```

⚠️ `nginx -t` báo lỗi thì **dừng lại, sửa xong mới reload**. Reload với cấu hình
sai sẽ làm ngã cả `kpihaiquan.vn`.

Ở bước này khối dev chưa có chứng chỉ nên chưa reload được — sang bước 4,
certbot sẽ tự điền rồi reload.

---

## 4. Cấp chứng chỉ HTTPS

```bash
certbot --nginx -d dev.kpihaiquan.vn
```

Certbot sẽ tự thêm hai dòng `ssl_certificate` vào khối `server` và reload nginx.

> Cấp **chứng chỉ riêng** cho subdomain, không gộp vào chứng chỉ hiện có của
> `kpihaiquan.vn`. Gộp thì mỗi lần gia hạn phải xác thực cả ba tên miền — dev
> trục trặc là kéo theo cả prod không gia hạn được.

Kiểm tra tự động gia hạn:

```bash
certbot renew --dry-run
```

---

## 5. Kiểm tra

```bash
# Phải hỏi mật khẩu → 401
curl -s -o /dev/null -w "%{http_code}\n" https://dev.kpihaiquan.vn/

# Có mật khẩu → 200
curl -s -o /dev/null -w "%{http_code}\n" -u <tên>:<mật-khẩu> https://dev.kpihaiquan.vn/

# Đúng môi trường dev chứ không phải prod
curl -s -I -u <tên>:<mật-khẩu> https://dev.kpihaiquan.vn/ | grep -i x-moi-truong
# → X-Moi-Truong: DEV
```

**Phép thử quyết định** — hai môi trường phải cho số liệu khác nhau:

```bash
# dev: 498 cuộc họp (9 HKG + 489 di trú từ lichkv8)
# prod: 9 cuộc họp
```

Nếu `dev.kpihaiquan.vn` cho ra 9 cuộc họp thì **cấu hình đang trỏ nhầm sang
cổng prod** — dừng ngay và rà lại số cổng trong `/etc/nginx/sites-available/kpi-dev`.

---

## 6. Lưu ý khi dùng

**Dịch vụ dev không tự chạy.** Khác prod do PM2 quản lý, dev phải bật tay:

```bash
cd /root/kpi-haiquan/backend && ./scripts/dev.sh chay
```

Chưa bật mà vào `dev.kpihaiquan.vn` sẽ thấy lỗi 502 Bad Gateway. Đó là bình
thường, không phải hỏng.

**Dev có thể vỡ bất cứ lúc nào** — đó là mục đích của nó. Đừng đưa đường dẫn
này cho người dùng cuối.

**Sau mỗi lần `./scripts/dev.sh lam-moi-db`**, dữ liệu dev trở thành bản sao
prod tại thời điểm đó. Thao tác trên dev sau đó không ảnh hưởng prod, nhưng dữ
liệu cá nhân của công chức thì vẫn là thật — đối xử cẩn thận như với prod.

---

## 7. Ba cái bẫy đã gặp (19/08/2026)

Cả ba đều cho ra CÙNG một triệu chứng: vào `dev.kpihaiquan.vn` thì đứng ở màn
hình **"Đang tải hệ thống"**. Đã sửa, ghi lại để lần sau nhận ra ngay.

### 7.1. `frontend/.env` trỏ tuyệt đối vào prod

```
NEXT_PUBLIC_API_URL=https://kpihaiquan.vn/api/v1
```

Địa chỉ **tuyệt đối** — mở dev.kpihaiquan.vn thì trình duyệt gọi API của
**production**. Tức giao diện đang làm dở thao tác trên dữ liệu thật của 549
công chức.

Thực tế chưa xảy ra, vì `CORS_ORIGINS` của prod không có
`https://dev.kpihaiquan.vn` nên trình duyệt chặn phản hồi — và `AuthProvider`
không thoát khỏi trạng thái đang tải. **Lỗi giao diện đó vô tình là chốt an
toàn.** Đừng thêm dev vào `CORS_ORIGINS` của prod để "sửa" — như vậy là mở
đúng cái cửa mà nó đang chặn.

**Cách sửa:** `frontend/.env.local` (bị gitignore, Next.js ưu tiên hơn `.env`)
đặt lại tất cả biến `NEXT_PUBLIC_*_API_URL` thành đường dẫn **tương đối**
(`/api/v1`, …). Trình duyệt gọi cùng tên miền đang mở, nginx định tuyến sang
cổng dev. Chạy được cả qua đường hầm SSH.

### 7.2. `next.config.ts` viết cứng cổng 800x

Các quy tắc `rewrites` trỏ thẳng `http://localhost:8001…8007` — cổng
**production**. Qua nginx thì không sao vì nginx bắt các tiền tố `/api/...`
trước; nhưng `/uploads/lms/`, `/uploads/legal/`, `/uploads/portal/` không có
trong cấu hình nginx dev nên rơi vào Next.js và bị đẩy sang prod. Vào thẳng
`localhost:3001` qua đường hầm SSH thì **mọi** lệnh gọi đều sang prod.

**Cách sửa:** số cổng lấy từ biến `BACKEND_PORT_PREFIX` (mặc định `80` = prod).
`frontend/.env.local` đặt `BACKEND_PORT_PREFIX=90`.

### 7.3. Next.js 16 chặn Origin lạ ở chế độ dev

```
⚠ Blocked cross-origin request to Next.js dev resource /_next/webpack-hmr
  from "dev.kpihaiquan.vn".
```

Trang HTML về được (200) nhưng các gói mã JS bị chặn → React không khởi động →
đứng ở màn hình đang tải. **Log của frontend là chỗ nhìn ra ngay:**

```bash
grep "Blocked cross-origin" /tmp/kpi-dev-logs/frontend.log
```

**Cách sửa:** `allowedDevOrigins: ['dev.kpihaiquan.vn']` trong `next.config.ts`.
Chỉ có tác dụng ở chế độ dev; prod chạy `next start` nên không đọc mục này.

### 7.4. Sai mật khẩu trong `/etc/nginx/.htpasswd-dev`

Băm trong file không khớp mật khẩu đã ghi chú → nginx trả 401 cho mọi thứ, kể
cả khi nhập đúng theo ghi chú. Kiểm tra:

```bash
htpasswd -vb /etc/nginx/.htpasswd-dev hqkv8 '<mật-khẩu>'
# "Password for user hqkv8 correct." là đạt
```

Đặt lại (**bỏ `-c`**, có `-c` là xoá hết người dùng cũ):

```bash
htpasswd -bB /etc/nginx/.htpasswd-dev hqkv8 '<mật-khẩu>'
chmod 640 /etc/nginx/.htpasswd-dev && chown root:www-data /etc/nginx/.htpasswd-dev
```

### 7.5. Đăng nhập xong bị hỏi mật khẩu liên tục

Triệu chứng khác hẳn ba mục trên: vào được, đăng nhập được, nhưng hộp
**"Sign in to dev.kpihaiquan.vn"** cứ bật lại. Nguyên nhân là **xung đột tiêu
đề `Authorization`**:

HTTP chỉ có **một** tiêu đề `Authorization`. Sau khi đăng nhập, ứng dụng gắn
`Authorization: Bearer <JWT>` vào mọi lệnh gọi API — đè mất
`Authorization: Basic` mà trình duyệt vẫn tự gửi. nginx không thấy mật khẩu
nữa nên trả 401 kèm `WWW-Authenticate: Basic`, và trình duyệt bật lại hộp đăng
nhập. **Mỗi lệnh gọi API là một lần hỏi.**

Cách nhìn ra trong 5 giây:

```bash
curl -s -I -H "Authorization: Bearer bat-ky" \
     https://dev.kpihaiquan.vn/api/v1/auth/me | grep -i www-authenticate
# Còn dòng `WWW-Authenticate: Basic` → đúng bệnh này.
```

Kèm theo là các file font 401: Next.js tải font ở chế độ `crossorigin`, mà chế
độ đó **không** đính mật khẩu đã lưu.

**Cách sửa** (đã áp dụng, xem `nginx-dev.conf.mau`): request đã mang Bearer thì
bỏ qua basic-auth — JWT của ứng dụng kiểm nó rồi, đúng như trên prod. Dùng
`map` đặt ngoài khối `server`:

```nginx
map $http_authorization $vung_bao_ve_dev {
    default        "Moi truong phat trien — chi noi bo";
    "~*^Bearer\s"  off;
}
# trong server: auth_basic $vung_bao_ve_dev;
```

Thêm `auth_basic off` cho `/_next/` và `/__nextjs_font/`.

> ⚠️ **Đánh đổi cần biết.** Sau thay đổi này, API của dev có thể gọi từ Internet
> nếu gửi kèm Bearer bất kỳ. Token sai vẫn bị ứng dụng từ chối — tức API dev
> được bảo vệ đúng bằng lớp mà prod đang dùng — nhưng lớp mật khẩu không còn
> che API nữa. Cổng vào (`/`, `/login`) thì vẫn phải có mật khẩu.
>
> Muốn giữ nguyên độ chặt cũ thì thêm **giới hạn theo IP** ở mục 2. Khi đó phải
> qua cả hai lớp và đánh đổi trên không còn ý nghĩa.

### Quy trình rà khi lại đứng ở "Đang tải hệ thống"

```bash
# 1. Dịch vụ dev có chạy không (dev KHÔNG tự khởi động, khác prod do PM2 quản)
cd /root/kpi-haiquan/backend && ./scripts/dev.sh trang-thai

# 2. Mật khẩu nginx
curl -s -o /dev/null -w "%{http_code}\n" -u hqkv8:<mk> https://dev.kpihaiquan.vn/   # 200

# 3. Next.js có chặn Origin không
grep "Blocked cross-origin" /tmp/kpi-dev-logs/frontend.log                          # rỗng

# 4. Trang có nhúng địa chỉ prod không
curl -s -u hqkv8:<mk> https://dev.kpihaiquan.vn/login | grep -c 'https://kpihaiquan.vn/api'   # 0

# 5. Lệnh gọi API có vào backend DEV không — xem log dev tăng dòng
tail -f /tmp/kpi-dev-logs/kpi.log

# 6. Hỏi mật khẩu liên tục sau khi đăng nhập → xung đột Bearer/Basic (mục 7.5)
curl -s -I -H "Authorization: Bearer bat-ky" \
     https://dev.kpihaiquan.vn/api/v1/auth/me | grep -i www-authenticate   # rỗng
```

Mẹo đọc log nginx: `/var/log/nginx/access.log` gộp cả prod lẫn dev, phân biệt
bằng cột `Referer`. Kích thước phần thân giúp đoán ai trả lời:

| Số byte | Ai trả |
|---|---|
| 188 | nginx — hộp mật khẩu basic-auth |
| 30 | backend — `{"detail":"Not authenticated"}`, thiếu/sai JWT |
| ~100 | backend — lỗi nghiệp vụ có mã |

**Sau khi sửa `.env.local` hay `next.config.ts` phải khởi động lại frontend
dev** — Next.js chỉ đọc các file này lúc khởi động. Dòng `- Environments:
.env.local, .env` trong log xác nhận đã nạp đúng.

---

## 8. Gỡ bỏ nếu không dùng nữa

```bash
rm /etc/nginx/sites-enabled/kpi-dev
nginx -t && systemctl reload nginx
certbot delete --cert-name dev.kpihaiquan.vn
```

Rồi xoá bản ghi A trên trang Viettel IDC.
