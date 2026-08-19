# Hướng dẫn tạo `dev.kpihaiquan.vn`

> Mục đích: vào môi trường phát triển bằng trình duyệt mà không phải mở đường
> hầm SSH mỗi lần. Đọc kèm `HUONG_DAN_DEV_PROD.md`.

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

## 7. Gỡ bỏ nếu không dùng nữa

```bash
rm /etc/nginx/sites-enabled/kpi-dev
nginx -t && systemctl reload nginx
certbot delete --cert-name dev.kpihaiquan.vn
```

Rồi xoá bản ghi A trên trang Viettel IDC.
