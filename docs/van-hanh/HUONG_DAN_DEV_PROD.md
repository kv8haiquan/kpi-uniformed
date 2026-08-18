# Hướng dẫn môi trường Dev và Production

> Áp dụng từ 18/08/2026, sau khi tách môi trường.
> Đọc kèm: `KE_HOACH_TACH_MOI_TRUONG.md` (vì sao tách) · `PHIEN_BAN_PROD.md` (prod đang chạy gì)

---

## 1. Mô hình: hai cây thư mục

```
/opt/kpi-prod/          PRODUCTION — người dùng thật vào đây
   nhánh git : prod
   cổng      : 8000–8007 (backend) · 3000 (frontend)
   CSDL      : kpi_haiquan
   kho file  : /var/data/kpi/uploads (qua symlink)
   nạp code  : CHỈ khi chạy trien_khai.sh

/root/kpi-haiquan/      PHÁT TRIỂN — nơi viết code
   nhánh git : feature/... bất kỳ
   cổng      : 9000–9007 (backend) · 3001 (frontend)
   CSDL      : kpi_haiquan_test
   kho file  : uploads-dev/
   nạp code  : tự động, uvicorn --reload
```

**Điểm cốt lõi:** sửa file trong cây phát triển **không** ảnh hưởng production.
Hai môi trường chạy đồng thời được, không tranh cổng, không đụng dữ liệu nhau.

Trước 18/08/2026 thì cả hai là **một** — PM2 phục vụ trực tiếp cây đang code.
Ngày 18/08 việc này làm ngừng toàn bộ module Họp Không Giấy trong 6 phút.

---

## 2. Làm việc hằng ngày

### 2.1. Khởi động môi trường phát triển

```bash
cd /root/kpi-haiquan/backend

./scripts/dev.sh chay               # kpi + meeting + frontend (mặc định)
./scripts/dev.sh chay lms forum     # chỉ những dịch vụ cần
./scripts/dev.sh trang-thai         # xem cả dev lẫn prod
./scripts/dev.sh dung               # dừng dev; prod không đụng tới
```

### Truy cập dev từ máy cá nhân

Dev chỉ lắng nghe `127.0.0.1` — **không mở ra Internet**, và nên giữ vậy: máy chủ
có IP công cộng, tường lửa đang tắt, còn dev thì chứa bản sao dữ liệu thật và
giao diện đang làm dở.

Dùng đường hầm SSH:

```bash
ssh -L 3001:127.0.0.1:3001 -L 9000:127.0.0.1:9000 -L 9006:127.0.0.1:9006 root@<máy-chủ>
```

Giữ cửa sổ đó mở, rồi vào **http://localhost:3001** trên trình duyệt.
Không phải 3000 — đó là production.

Muốn tiện hơn thì làm `dev.kpihaiquan.vn` riêng có chứng chỉ và mật khẩu bảo vệ,
nhưng cần thêm bản ghi DNS.

Sửa file `.py` là uvicorn tự nạp lại, không phải khởi động tay.
Log ở `/tmp/kpi-dev-logs/<tên>.log`.

### 2.2. Bảng cổng

| Dịch vụ | Prod | Dev |
|---|---:|---:|
| KPI backend | 8000 | 9000 |
| LMS | 8001 | 9001 |
| Forum | 8002 | 9002 |
| Legal | 8003 | 9003 |
| Portal | 8004 | 9004 |
| Common | 8005 | 9005 |
| Meeting (HKG) | 8006 | 9006 |
| Chỉ tiêu | 8007 | 9007 |
| Frontend | 3000 | **3001** |

### 2.3. Cơ sở dữ liệu

Dev dùng `kpi_haiquan_test` — bản sao của prod. Làm mới khi cần dữ liệu thật:

```bash
./scripts/dev.sh lam-moi-db
```

Lệnh này `pg_dump` **chỉ đọc** prod rồi nạp sang DB test. An toàn với prod,
nhưng **xoá sạch** DB test hiện tại.

### 2.4. Chạy test

```bash
./scripts/dev.sh test meeting_service/tests/ -v
./scripts/dev.sh test meeting_service/tests/test_lich_cong_tac_api.py -q
./scripts/dev.sh test -k "truc_ban"
```

Script tự đặt `DB_NAME=kpi_haiquan_test` nên không có đường ghi nhầm vào prod.

---

## 3. Hai chốt an toàn

**Chốt 1 — script từ chối chạy trên DB prod.**
Nếu `DB_NAME` là `kpi_haiquan`, `dev.sh` dừng ngay:

```
⛔ DB_NAME đang là kpi_haiquan (PRODUCTION). Kiểm lại .env.dev
```

**Chốt 2 — tác vụ nền tắt sẵn ở dev.**
`.env.dev` đặt `HKG_DISABLE_SCHEDULER=true` và `ZALO_DRY_RUN=true`.

Nếu bật lên, môi trường dev sẽ **gửi nhắc họp và tin nhắn Zalo THẬT** tới công
chức, trùng với prod — người dùng nhận hai lần. Chỉ bật khi cố ý kiểm thử và
biết rõ hậu quả.

---

## 4. Đưa code từ dev lên production

### 4.1. Toàn cảnh

```
   viết code ở /root/kpi-haiquan
         │
         ├─ ./scripts/dev.sh chay      chạy thử ở cổng 9xxx
         ├─ ./scripts/dev.sh test      test trên DB test
         │
         ▼
   git commit  →  git push  →  merge vào nhánh main
         │
         ▼
   /opt/kpi-prod/backend/scripts/trien_khai.sh <commit|tag>
         │
         ├─ lấy code
         ├─ cài thư viện nếu requirements/package-lock đổi
         ├─ CHẠY MIGRATION          ← trước khi nạp code
         ├─ build frontend nếu đổi
         ├─ pm2 reload
         └─ kiểm /health từng dịch vụ, lỗi thì dừng và in lệnh quay lui
```

### 4.2. Các bước cụ thể

**Bước 1 — hoàn tất ở dev.**

```bash
cd /root/kpi-haiquan
./backend/scripts/dev.sh test <thư mục test liên quan>
git add <file cụ thể>          # tránh `git add -A`, xem mục 6
git commit
git push origin <nhánh>
```

**Bước 2 — gộp vào `main`.** Qua Pull Request trên GitHub, hoặc merge cục bộ.

**Bước 3 — triển khai.**

```bash
/opt/kpi-prod/backend/scripts/trien_khai.sh main
# hoặc chốt một mốc cụ thể:
/opt/kpi-prod/backend/scripts/trien_khai.sh v2026.08.20
```

**Bước 4 — cập nhật `docs/van-hanh/PHIEN_BAN_PROD.md`** với commit vừa lên.

### 4.3. Thứ tự migration — điều quan trọng nhất

```
✅ ĐÚNG:  chạy migration  →  rồi mới nạp code mới
❌ SAI :  nạp code mới    →  rồi mới chạy migration
```

Làm sai thì code mới tham chiếu cột chưa tồn tại trong CSDL, và **hỏng cả module**,
không riêng tính năng mới. Ngày 18/08/2026 chính là như vậy:

```
sqlalchemy.exc.ProgrammingError: column cuoc_hop.nguon does not exist
```

Model `CuocHop` thêm cột mới → **mọi** câu SELECT trên bảng đó vỡ → danh sách
cuộc họp và scheduler nhắc họp ngừng hoạt động, dù chúng chẳng liên quan gì
tới tính năng đang làm.

`trien_khai.sh` đã ép đúng thứ tự. Đừng chạy tay từng bước để "cho nhanh".

### 4.4. Quay lui

`trien_khai.sh` in sẵn lệnh quay lui ngay khi bắt đầu:

```
[19:30:12] Quay lui  : /opt/kpi-prod/backend/scripts/trien_khai.sh a1b2c3d
```

Chép lại lệnh đó trước khi làm gì tiếp. Nếu có dịch vụ không lên, script tự
dừng và nhắc lại lệnh này.

⚠️ **Quay lui code KHÔNG tự quay lui migration.** Migration thêm cột hay thêm
bảng thì code cũ vẫn chạy được (cột thừa không sao). Nhưng migration **xoá hoặc
đổi tên** cột thì phải `alembic downgrade` bằng tay. Cân nhắc điều này ngay từ
lúc viết migration: ưu tiên thêm mới, tránh xoá.

---

## 5. Bảo trì

### 5.1. Kiểm tra sức khoẻ

```bash
cd /root/kpi-haiquan/backend && ./scripts/dev.sh trang-thai
pm2 list
pm2 logs <tên dịch vụ> --lines 50
```

### 5.2. Sao lưu (tự động, không phải làm gì)

| Thành phần | Cơ chế | Off-site |
|---|---|---|
| CSDL | `backup_daily.sh` 02:00 và 14:00 | ✅ GitHub, mã hoá AES256, giữ 14 bản |
| Mã nguồn | `backup_source.sh` — chụp cả code chưa commit | ✅ nhánh `auto-backup` |
| `uploads/` toàn bộ 6,1 GB | rsync 2 lần/ngày | ❌ chỉ local |

Cấu hình ở `/etc/cron.d/hkg-backups`, script ở `/opt/kpi/scripts/`.

### 5.3. Việc còn nợ

- [x] ~~Chuyển `uploads/` ra khỏi cây phát triển~~ → `/var/data/kpi/uploads` *(18/08)*
- [x] ~~Mở rộng sao lưu cho cả `uploads/`~~ → đã phủ 6,1 GB gồm LMS *(18/08)*
- [ ] **Off-site cho file tài liệu** — hiện chỉ sao lưu cục bộ. Làm **trước**
      khi thu hồi chia sẻ Google Drive, vì sau đó bản trên nền tảng là bản duy nhất

---

## 6. Bẫy đã gặp thật

### 6.1. `git checkout <commit> -- <path>` đưa thay đổi vào index

Lệnh này **stage** luôn. Nên `git commit` kế tiếp cuốn theo cả những file đó,
dù chỉ `git add` file của tính năng đang làm.

Đã xảy ra ngày 18/08: commit "phiếu Quý 02A/02B" vô tình chứa 8 file
`meeting_service`, xoá mất phần backend Lịch công tác.

**Cách tránh:** trước khi commit, luôn xem

```bash
git diff --cached --name-only
```

và đối chiếu với đúng những file mình định đưa vào.

### 6.2. Cẩn thận với `git add -A`

Cây làm việc thường có thay đổi của nhiều việc khác nhau. `git add -A` gom tất.
Thêm file cụ thể, rồi kiểm bằng `git diff --cached --name-only`.

### 6.3. `requirements.txt` có thể thiếu gói

Gói cài tay vào venv thì vẫn chạy, nhưng dựng venv sạch từ `requirements.txt`
là chết. Ngày 18/08 phát hiện thiếu `APScheduler` và `qrcode` — không có chúng
thì `meeting_service` không khởi động nổi.

**Cách tránh:** cài gói mới thì thêm vào `requirements.txt` ngay, kèm ghi chú
dùng cho việc gì.

### 6.4. Test phụ thuộc giờ chạy

`test_presentation_rest.py` và `test_presentation_ws.py` đỏ khi chạy buổi tối:
token WebSocket hết hạn theo công thức `gio_bat_dau + 4h`, mà test tạo cuộc họp
giờ sáng. Đây là lỗi có sẵn của test, không phải code hỏng.

### 6.5. Alembic

- Chuỗi revision **tuyến tính qua mọi module** (kpi, lms, zalo, meeting…).
  `down_revision` phải là head thật, không phải migration cuối của module mình.
  Kiểm bằng: `ScriptDirectory.from_config(Config("alembic.ini")).get_heads()`
- Cột `alembic_version.version_num` là `varchar(32)`. Revision id dài hơn 32 ký
  tự làm migration vỡ **giữa chừng** — DDL đã chạy nhưng ghi version thất bại.

---

## 7. Tra cứu nhanh

| Việc | Lệnh |
|---|---|
| Chạy dev | `cd backend && ./scripts/dev.sh chay` |
| Dừng dev | `./scripts/dev.sh dung` |
| Xem trạng thái | `./scripts/dev.sh trang-thai` |
| Làm mới DB test | `./scripts/dev.sh lam-moi-db` |
| Chạy test | `./scripts/dev.sh test <đường dẫn>` |
| Triển khai lên prod | `/opt/kpi-prod/backend/scripts/trien_khai.sh main` |
| Prod đang chạy gì | `git -C /opt/kpi-prod log --oneline -1` |
| Log prod | `pm2 logs <tên> --lines 50` |
| Log dev | `tail -f /tmp/kpi-dev-logs/<tên>.log` |

**Ba điều tuyệt đối không làm**

1. Không sửa file trực tiếp trong `/opt/kpi-prod` — sẽ mất ở lần triển khai sau
2. Không chạy migration lên prod bằng tay ngoài `trien_khai.sh`
3. Không trỏ `DB_NAME=kpi_haiquan` khi chạy dev hay test
