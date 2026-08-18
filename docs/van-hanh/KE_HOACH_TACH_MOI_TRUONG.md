# Kế hoạch tách môi trường phát triển khỏi production

> **Ngày lập:** 18/08/2026
> **Nguyên nhân:** sự cố 19:10–19:16 ngày 18/08 — toàn bộ module Họp Không Giấy ngừng hoạt động
> **Trạng thái:** chờ chủ dự án duyệt

---

## 1. Chuyện gì đã xảy ra

Đang phát triển tính năng Lịch công tác, có sửa `backend/meeting_service/models/cuoc_hop.py`
để thêm cột mới. Migration **cố ý chưa chạy trên prod**. Nhưng `meeting-backend` tự khởi động
lại lúc 19:10 và nạp luôn code mới, trong khi cơ sở dữ liệu prod chưa có cột đó:

```
sqlalchemy.exc.ProgrammingError: column cuoc_hop.nguon does not exist
```

Hậu quả rộng hơn tính năng đang làm, vì model dùng chung:

| Thành phần | Ảnh hưởng |
|---|---|
| `/lich-cong-tac/*` | 500 — endpoint mới |
| **`/cuoc-hop/` danh sách họp HKG** | **500 — nghiệp vụ đang chạy thật** |
| **Scheduler nhắc họp** | **Vỡ mỗi chu kỳ** |

Khắc phục bằng cách khôi phục `backend/meeting_service/` về commit trước rồi khởi động lại.
Không ghi gì vào cơ sở dữ liệu prod.

---

## 2. Vì sao sẽ lặp lại nếu không tách

Đây **không phải lỗi thao tác đơn lẻ** mà là đặc điểm của cách triển khai hiện tại.

### 2.1. Toàn bộ 10 dịch vụ chạy từ chính cây làm việc

```
kpi-backend       /root/kpi-haiquan/backend     ← KPI production, 549 người dùng
lms-backend       /root/kpi-haiquan/backend
forum-backend     /root/kpi-haiquan/backend
legal-backend     /root/kpi-haiquan/backend
portal-backend    /root/kpi-haiquan/backend
common-backend    /root/kpi-haiquan/backend
meeting-backend   /root/kpi-haiquan/backend
chi-tieu-backend  /root/kpi-haiquan/backend
zalo-worker       /root/kpi-haiquan/backend
kpi-frontend      /root/kpi-haiquan/frontend
```

Sửa một file bất kỳ trong `backend/` là đã thay đổi code của **cả 9 dịch vụ backend**.

### 2.2. Không tránh được bằng cách cẩn thận

Các dịch vụ chạy **không có `--reload`**, nên code mới chỉ vào khi khởi động lại. Điều nguy hiểm
là **khởi động lại phần lớn không do người chủ động**: PM2 tự restart khi tiến trình chết. Số lần
restart tích luỹ cho thấy việc này xảy ra thường xuyên:

```
kpi-backend      409 lần
kpi-frontend     246 lần
lms-backend      227 lần
meeting-backend  143 lần
```

Nghĩa là: chỉ cần code trong cây làm việc đang dở dang, **lần restart tự động kế tiếp sẽ đưa nó
lên production** — không ai bấm nút, không ai biết trước.

### 2.3. Prod đang chạy nhánh feature, không phải nhánh phát hành

```
nhánh hiện tại : feature/lich-cong-tac
main           : đi sau HEAD 174 commit
```

`main` đã không còn là đích triển khai từ lâu. Thứ đang phục vụ người dùng là **cây làm việc của
người phát triển**, ở bất kỳ nhánh nào đang mở.

### 2.4. Có code chưa commit đang phục vụ người dùng

**11 file backend đã sửa nhưng chưa commit** đang được prod chạy, phần lớn thuộc module KPI:

```
backend/app/api/v1/endpoints/admin.py, bao_cao_xep_loai.py, danh_gia.py,
    in_bang_ke.py, phieu_danh_gia_quy.py, xep_loai_quy_helpers.py
backend/app/models/admin.py, phieu_danh_gia.py
backend/app/schemas/admin.py, bao_cao_xep_loai.py, phieu_danh_gia.py
```

Điểm nhẹ nhõm: `backup_source.sh` có chụp cả thay đổi chưa commit lên nhánh `auto-backup`, nên
không mất. Nhưng **không ai biết chính xác prod đang chạy phiên bản nào** — không tra được, không
quay lui được về một mốc xác định.

---

## 3. Phương án: tách hai cây thư mục

Ý tưởng đơn giản: **prod đọc một thư mục riêng, phát triển ghi ở thư mục khác.** Chuyển từ cây này
sang cây kia là một thao tác có chủ ý, không xảy ra tự động.

```
/opt/kpi-prod/          ← PM2 chạy từ đây, chỉ ở nhánh phát hành
/root/kpi-haiquan/      ← nơi phát triển, sửa thoải mái, không ảnh hưởng ai
```

Dùng **`git worktree`** thay vì clone riêng: hai cây dùng chung kho `.git` (49 MB) nên không tốn
thêm dung lượng cho lịch sử, và `git log` ở cả hai bên đều thấy nhau.

### Dung lượng phát sinh

| Thành phần | Dung lượng | Ghi chú |
|---|---:|---|
| Mã nguồn (worktree) | ~1,4 GB | không kể venv, node_modules, uploads |
| `venv` riêng cho prod | 361 MB | phải riêng — nâng thư viện không được ảnh hưởng prod |
| `node_modules` + `.next` riêng | ~1 GB | |
| **Tổng** | **~2,8 GB** | đĩa còn trống 56 GB |

### Những thứ KHÔNG nhân đôi

| Tài nguyên | Cách xử lý | Lý do |
|---|---|---|
| `backend/uploads/` (5,4 GB) | symlink sang thư mục dùng chung | File thật của người dùng, chỉ có một bản |
| `backend/.env` | file riêng của prod, không theo git | Chứa bí mật; bản dev trỏ DB test |
| Cơ sở dữ liệu | giữ nguyên `kpi_haiquan` / `kpi_haiquan_test` | Đã tách sẵn từ trước |

---

## 4. Các bước thực hiện

### Giai đoạn P0 — Chặn rủi ro ngay *(30 phút)*

Làm trước, độc lập với phần còn lại. Mục tiêu: **từ giờ tới lúc tách xong, không có lần restart
tự động nào đưa code dở lên prod.**

- [ ] **P0.1** — Commit hoặc stash 11 file backend chưa commit, để cây làm việc sạch
      → chủ dự án xác nhận số file này thuộc việc nào trước khi commit
- [ ] **P0.2** — Ghi lại commit đang phục vụ prod vào `docs/van-hanh/PHIEN_BAN_PROD.md`
      để có mốc quay lui xác định

### Giai đoạn P1 — Dựng cây prod *(1–2 giờ)*

- [ ] **P1.1** — Tạo nhánh phát hành từ trạng thái prod đang chạy:
      `git branch prod <commit-đang-chạy>`
- [ ] **P1.2** — `git worktree add /opt/kpi-prod prod`
- [ ] **P1.3** — Dựng `venv` riêng trong `/opt/kpi-prod/backend`, cài theo `requirements.txt`
- [ ] **P1.4** — Chép `.env` sang, giữ nguyên cấu hình prod
- [ ] **P1.5** — Symlink `uploads`: `ln -s /root/kpi-haiquan/backend/uploads /opt/kpi-prod/backend/uploads`
      *(hoặc chuyển hẳn uploads ra `/var/data/kpi/uploads` rồi symlink từ cả hai cây — sạch hơn)*
- [ ] **P1.6** — `npm ci && npm run build` cho frontend trong cây prod
- [ ] **P1.7** — Chạy thử từng dịch vụ ở cổng tạm, đối chiếu `/health`

### Giai đoạn P2 — Chuyển PM2 *(30 phút, có gián đoạn ngắn)*

- [ ] **P2.1** — Chọn khung giờ ít người dùng, báo trước
- [ ] **P2.2** — Sửa `ecosystem.config.js` (hoặc lệnh PM2) trỏ `cwd` sang `/opt/kpi-prod`
- [ ] **P2.3** — `pm2 reload` từng dịch vụ, kiểm `/health` sau mỗi cái
- [ ] **P2.4** — `pm2 save` để cấu hình sống qua khởi động lại máy
- [ ] **P2.5** — Theo dõi log 30 phút

### Giai đoạn P3 — Quy trình triển khai *(1 giờ)*

- [ ] **P3.1** — Viết `scripts/trien_khai.sh`:
      `git -C /opt/kpi-prod fetch && checkout <tag> && cài thư viện nếu đổi && alembic upgrade head && pm2 reload`
- [ ] **P3.2** — Bắt buộc: **migration chạy TRƯỚC khi nạp code mới**, không được ngược lại —
      chính thứ tự này là nguyên nhân sự cố 18/08
- [ ] **P3.3** — Ghi quy trình vào `CLAUDE.md` để mọi người và mọi phiên làm việc đều theo

### Giai đoạn P4 — Dọn phần còn lại *(tuỳ chọn)*

- [ ] **P4.1** — `uploads/lms` 5,4 GB chưa được sao lưu — mở rộng `backup_daily.sh` rsync cả
      thư mục `uploads/` thay vì chỉ `uploads/meeting`
- [ ] **P4.2** — Off-site cho file tài liệu, làm **trước** khi thu hồi chia sẻ Drive (G6.7)

---

## 5. Sau khi tách xong thì dự án Lịch công tác đi tiếp thế nào

Thứ tự bắt buộc, đúng cái mà sự cố 18/08 cho thấy không được làm ngược:

1. Chạy migration `meeting_016` → `021` trên prod — thêm cột nullable và bảng mới,
   đã kiểm cả `upgrade` lẫn `downgrade` trên bản clone tươi từ prod
2. Kiểm `/health` và danh sách cuộc họp HKG vẫn bình thường
3. Mới nạp code Lịch công tác vào cây prod và `pm2 reload`
4. Di trú dữ liệu 489 sự kiện + 1.225 file lên prod
5. Bà Hà rà 34 cụm trên màn hình đối soát

Từ bước 3 trở đi mới có tính năng cho người dùng thấy.

---

## 6. Rủi ro của chính việc tách

| Rủi ro | Cách giảm |
|---|---|
| Gián đoạn khi chuyển PM2 | `reload` từng dịch vụ, chọn giờ vắng, kiểm `/health` sau mỗi cái |
| Sai đường dẫn `uploads` → mất file | Dùng symlink, **không** chép; kiểm đếm file trước và sau |
| `.env` chép nhầm sang bản dev | Đối chiếu `DB_NAME` ngay sau khi chép |
| `venv` prod thiếu thư viện | Cài theo `requirements.txt`, chạy thử ở cổng tạm trước khi chuyển |
| Quên `pm2 save` → khởi động máy về cấu hình cũ | Đưa vào danh sách kiểm P2.4 |
