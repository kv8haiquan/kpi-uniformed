# Hỏi – Đáp bổ sung phục vụ rà quét ATTT (CV 153/CNTT)

> Trả lời trực tiếp các câu hỏi của đoàn kiểm tra. Lập ngày 05/08/2026, số liệu xác minh trực tiếp trên máy chủ production tại thời điểm lập.
> Đã bao gồm kết quả **đợt vá bảo mật 31/07/2026** (chi tiết: `BAO_CAO_RA_QUET_NOI_BO.md` mục 0).

---

## 1. Kiến trúc & kỹ thuật

### 1.1. Sơ đồ kiến trúc

Chi tiết đầy đủ (kèm sơ đồ mermaid): **`05_kien_truc_he_thong.md`**. Tóm tắt:

```
Internet ──HTTPS 443──► nginx 1.24 (SSL Let's Encrypt, reverse proxy)
                          ├── /                    → Frontend Next.js (port 3000)
                          ├── /api                 → KPI Backend      (port 8000)
                          ├── /api/v1/lms/         → LMS              (port 8001)
                          ├── /api/forum/v1/       → Forum            (port 8002)
                          ├── /api/legal/v1/       → Legal            (port 8003)
                          ├── /api/portal/v1/      → Portal           (port 8004)
                          ├── /api/common/         → Common           (port 8005)
                          ├── /api/v1/hop-khong-giay/ + /ws/… → HKG   (port 8006)
                          └── /api/v1/chi-tieu/    → Chỉ tiêu         (port 8007)
                                      │
                                      ▼
                          PostgreSQL 15.16 (localhost:5432, 1 database `kpi_haiquan`, 8 schema)
```

### 1.2. IP, port, domain

| Thông tin | Giá trị |
|---|---|
| Domain | `kpihaiquan.vn` (SSL Let's Encrypt, tự gia hạn) |
| IP public | `79.108.216.189` |
| Port mở ra Internet | **chỉ 80/443** (nginx); 80 redirect 443 |
| Port nội bộ (chỉ localhost) | 3000 (FE), 8000–8007 (8 backend), 5432 (PostgreSQL) |

### 1.3. Môi trường vận hành

- **VM (máy chủ ảo) — KHÔNG dùng Docker/Kubernetes.** Toàn bộ service chạy native, quản lý tiến trình bằng **PM2 6.0.14** (9 process: 8 backend Python/uvicorn + 1 frontend Next.js), tự khởi động lại khi lỗi/reboot.
- PostgreSQL 15.16 cài native (systemd), chỉ nghe localhost.

### 1.4. Thông tin máy chủ production

| Thông số | Giá trị |
|---|---|
| OS | Ubuntu 24.04.4 LTS (kernel 6.8) |
| CPU / RAM / Disk | 4 vCPU / 8 GB / 100 GB (đang dùng ~37%) |
| Runtime | Python 3.12.3, Node.js 20.20.0, nginx 1.24.0 |
| Máy chủ backup riêng | **Không có** — backup lưu tại chỗ + đẩy off-site lên GitHub private (mã hóa). Xem mục 2.1. |

---

## 2. Cơ sở dữ liệu

### 2.1. Phương án sao lưu / phục hồi

**Ngoài GitHub còn có backup cục bộ trên máy chủ** — tổng cộng 3 lớp, chạy tự động bằng cron (`/etc/cron.d/hkg-backups`), 2 lần/ngày (02:00 và 14:00):

| Lớp | Nội dung | Vị trí | Retention |
|---|---|---|---|
| 1. Backup cục bộ | `pg_dump` toàn bộ DB (nén gz) + rsync thư mục uploads | `/var/backup/kpi_haiquan/{daily,monthly,uploads}` | daily 30 ngày, monthly 400 ngày |
| 2. Off-site DB | Bản dump **mã hóa** đẩy lên GitHub repository private | GitHub (02:30/14:30) | theo lịch sử repo |
| 3. Off-site mã nguồn | Snapshot working tree → branch `auto-backup` | GitHub (02:45/14:45) | theo lịch sử repo |

- **RPO ≈ 12 giờ** (2 bản/ngày). Đã xác minh backup đang chạy đều (bản gần nhất trong ngày lập tài liệu).
- **Quy trình phục hồi** (chi tiết `06_co_so_du_lieu_sao_luu.md`): tạo DB tạm → restore bản dump → kiểm tra số liệu → đổi tên/trỏ ứng dụng. Việc restore vào DB tạm được thực hiện thường xuyên trong vận hành (tạo DB test `kpi_haiquan_test` từ dump prod trước mỗi đợt kiểm thử) — đóng vai trò diễn tập phục hồi định kỳ.
- Hạn chế ghi nhận: backup cục bộ nằm cùng VM với production (rủi ro hỏng đĩa mất cả 2 lớp đầu) — lớp GitHub off-site là phương án chống thảm họa; khuyến nghị bổ sung 1 đích lưu trữ ngoài nữa (NAS/máy chủ cơ quan) khi có hạ tầng.

### 2.2. Phân loại dữ liệu

| Nhóm | Bảng/dữ liệu tiêu biểu | Phân loại |
|---|---|---|
| **Dữ liệu cá nhân (PII)** theo NĐ 13/2023/NĐ-CP | `public.cong_chuc`: họ tên, ngày sinh, giới tính, email, số điện thoại, mã công chức, chức vụ, đơn vị | Dữ liệu cá nhân cơ bản — chỉ người trong hệ thống (đã đăng nhập, đúng phân quyền) xem được |
| **Nội bộ — nhạy cảm nghiệp vụ** | Kê khai công việc, điểm KPI, đánh giá, xếp loại A/B/C/D, phiếu đánh giá, kết quả thi ĐGNL, biên bản họp (HKG), chỉ tiêu đơn vị | Nội bộ; phân quyền theo vai trò + đơn vị (công chức chỉ xem của mình; lãnh đạo theo phạm vi quản lý; TCCB/CCT toàn chi cục) |
| **Nội bộ — dùng chung** | Tin tức portal, văn bản pháp luật, tài liệu đào tạo, diễn đàn | Nội bộ; mọi tài khoản đăng nhập xem được |
| **Công khai** | **Không có** — toàn bộ chức năng đều sau đăng nhập; không có trang nào phục vụ người dùng vãng lai | — |

### 2.3. Biện pháp bảo vệ

| Biện pháp | Hiện trạng |
|---|---|
| Mật khẩu người dùng | **Đã mã hóa một chiều bằng bcrypt** (passlib, salt tự sinh từng mật khẩu) — không lưu và không thể khôi phục mật khẩu gốc |
| Chính sách độ phức tạp mật khẩu | **CHƯA đạt mức 8 ký tự + hoa/thường/số/ký tự đặc biệt.** Hiện tại chỉ yêu cầu tối thiểu 6 ký tự khi đổi mật khẩu; mật khẩu khởi tạo mặc định `123456` và chưa bắt buộc đổi ở lần đăng nhập đầu. **Đã có kế hoạch khắc phục** (cờ `must_change_password` + nâng chuẩn mật khẩu ≥8 ký tự đủ 4 nhóm — dự kiến đợt cập nhật tiếp theo) |
| Chống dò mật khẩu | Đã có từ 31/07/2026: khóa tài khoản tạm 15 phút sau 10 lần sai liên tiếp + rate limit 30 lần/phút/IP tại endpoint login |
| Mã hóa đường truyền | HTTPS toàn bộ (TLS, Let's Encrypt); DB không mở ra ngoài (localhost) |
| Mã hóa dữ liệu lưu trữ (at-rest) | DB không mã hóa at-rest (thông lệ với hệ nội bộ đặt sau firewall); **bản backup đẩy off-site có mã hóa** |
| Kiểm soát truy cập | RBAC 2 lớp (vai trò nghiệp vụ + platform role), kiểm tra tại backend từng endpoint; JWT ký HS256, SECRET_KEY qua biến môi trường (không hardcode — đã rà và gỡ toàn bộ credential khỏi mã nguồn 31/07/2026) |
| Truy cập máy chủ | SSH; DB/backend không truy cập được từ ngoài |

---

## 3. Xác thực & giám sát

### 3.1. Cơ chế xác thực chi tiết

**Login flow** (một điểm đăng nhập duy nhất cho cả 8 module — SSO):

1. Người dùng nhập username (mã công chức) + mật khẩu tại FE → `POST /api/v1/auth/login` (KPI backend 8000).
2. Backend kiểm tra: tài khoản đang bị khóa tạm? (brute-force) → tìm user (không phân biệt hoa/thường) → so bcrypt hash → kiểm tra `is_active`.
3. Thành công: phát hành **JWT** ký **HS256**, hiệu lực **480 phút (8 giờ)**, claims: `sub` (user id), `ma_cc`, `ho_ten`, `role`, `don_vi_id`, `is_lanh_dao`, `is_admin`, `platform_roles`, `exp`; cập nhật `last_login`; reset bộ đếm sai mật khẩu.
4. FE lưu token, gắn `Authorization: Bearer` cho mọi request. **Không có server-side session** (stateless) — mỗi service tự verify chữ ký JWT bằng cùng SECRET_KEY, không gọi lại KPI backend.
5. Logout = client hủy token. Token không có cơ chế thu hồi trước hạn (chấp nhận được với hệ nội bộ hạn 8h; đã ghi nhận cân nhắc refresh-token ngắn hạn ở phiên bản sau).

### 3.2. Nhật ký hệ thống

| Loại log | Vị trí | Nội dung |
|---|---|---|
| Access log web | `/var/log/nginx/access.log` (logrotate nén giữ nhiều kỳ) | IP client, thời điểm, method + URL, status code, User-Agent — **toàn bộ request đi qua hệ thống** |
| Application log (9 service) | `/root/.pm2/logs/*-out.log`, `*-error.log` (pm2-logrotate) | Log ứng dụng, lỗi runtime, traceback |
| Log an ninh đăng nhập | logger `app.security` (ghi vào PM2 log của kpi-backend) | Từng lần **đăng nhập sai** (tài khoản, lần thứ mấy, IP) và sự kiện **khóa tạm tài khoản** |
| Log sao lưu | `/var/log/backup_kpi.log`, `backup_github.log`, `backup_source.log` | Kết quả từng lần backup |

### 3.3. Cơ chế audit (ai – làm gì – khi nào)

Hiện trạng trung thực, gồm cả điểm mạnh và khoảng trống:

**Đã có:**
- **Đăng nhập**: thời điểm đăng nhập thành công gần nhất lưu ở `cong_chuc.last_login`; từng lần đăng nhập **sai** + sự kiện khóa tài khoản ghi log an ninh (kèm IP) từ 31/07/2026; mọi lần gọi endpoint login đều có dòng tương ứng trong nginx access log (IP + thời điểm + status 200/401/429).
- **Nghiệp vụ**: các bảng chính tự lưu vết trong dữ liệu — ai phê duyệt/từ chối (id người duyệt + thời điểm, 2 cấp), lịch sử điều chỉnh điểm (JSONB `lich_su`), lịch sử điều chuyển đơn vị, lịch sử thi ĐGNL từng lần (`lich_su_thi`, `phien_thi`, bảng vi phạm), HKG ghi log định danh khi từ chối truy cập họp (403).
- Bảng `public.audit_log` (table_name, record_id, action, old/new JSONB, user_id, ip_address) đã có cấu trúc sẵn.

**Khoảng trống (ghi nhận để hoàn thiện):**
- Trigger tự động ghi `audit_log` cho các bảng nghiệp vụ **chưa kích hoạt** trên production (bảng hiện chỉ có bản ghi thử nghiệm) — vết thay đổi đang nằm phân tán trong từng bảng nghiệp vụ thay vì tập trung.
- Đăng nhập **thành công** từng lần chưa ghi thành bản ghi DB riêng (chỉ có `last_login` gần nhất + access log nginx).
- **Kế hoạch**: bổ sung bảng nhật ký đăng nhập (thời điểm, tài khoản, IP, kết quả đúng/sai) + kích hoạt trigger audit cho nhóm bảng trọng yếu — gộp vào đợt cập nhật `must_change_password`.

---

## 4. API & tích hợp

### 4.1. Danh mục API

- **555 endpoints / 8 service** — danh mục dạng bảng: `08_danh_muc_api.md`.
- **OpenAPI spec đầy đủ (JSON)**: thư mục **`api-specs/`** — 8 file (`kpi_8000.json`, `svc_8001.json` … `svc_8007.json`), export trực tiếp từ từng service.
- **Định dạng CSV**: `api-specs/danh_muc_endpoints.csv` (555 dòng: Service, Method, Path, Mô tả) — mở được bằng Excel.
- Lưu ý: từ 31/07/2026 `/docs`, `/openapi.json` đã **tắt trên production** (bật lại được bằng `DEBUG=true` khi cần kiểm tra).

### 4.2. 8 service và kết nối ra bên ngoài

| Service | Port | Chức năng |
|---|---|---|
| KPI | 8000 | Kê khai, phê duyệt, đánh giá, xếp loại + **đăng nhập SSO** |
| LMS | 8001 | Đào tạo, thi ĐGNL |
| Forum | 8002 | Diễn đàn nội bộ |
| Legal | 8003 | Văn bản pháp luật |
| Portal | 8004 | Tin tức/CMS nội bộ |
| Common | 8005 | Thông báo, file storage, API nội bộ dùng chung |
| HKG | 8006 | Họp không giấy (kèm WebSocket trình chiếu) |
| Chỉ tiêu | 8007 | Chỉ tiêu đơn vị |

**Kết nối:**
- Giữa các service (nội bộ máy): gọi HTTP localhost, xác thực bằng header `X-Internal-Key` (key ngẫu nhiên trong `.env`, đã rotate 31/07/2026); ví dụ các module gửi thông báo qua Common service.
- **Ra Internet (outbound) chỉ có duy nhất**: đẩy backup mã hóa + snapshot mã nguồn lên GitHub private (cron). **Không tích hợp/gọi bất kỳ hệ thống bên ngoài nào khác** (không thanh toán, không SMS/OTP, không API bên thứ ba trong luồng nghiệp vụ).
- Vào từ Internet (inbound): duy nhất nginx 443.

---

## 5. Kiểm thử & bảo trì

### 5.1. Hồ sơ test case, kết quả kiểm thử

- Chi tiết: **`09_kiem_thu_van_hanh_phien_ban.md`** — 73 file test backend (~749 test case, phân theo 8 module) + 5 file test frontend; khung pytest + vitest; quy tắc mọi test ghi DB chạy trên database test clone từ production.
- Kết quả đợt chạy gần nhất (31/07/2026, sau đợt vá bảo mật): **~706 PASS**; 41 fail được đối chứng là lỗi có sẵn của test phụ thuộc dữ liệu (chạy trên cả mã nguồn + thư viện cũ cho kết quả y hệt), không phải lỗi hệ thống — đã ghi nhận kế hoạch làm mới bộ test này.
- Kiểm thử thủ công/nghiệm thu: checklist UAT (HKG Phase 4.1) + 22 báo cáo đối chiếu số liệu thực tế tại `docs/Fix-Bao-Cao/` (đối chiếu xếp loại từng tháng với dữ liệu gốc, xác minh 0 sai lệch).
- Kiểm thử bảo mật nội bộ: bandit + pip-audit + npm audit — kết quả và hiện trạng sau vá tại `BAO_CAO_RA_QUET_NOI_BO.md`.

### 5.2. Tài liệu HDSD, vận hành, xử lý sự cố

- **Quản trị nghiệp vụ**: `docs/HUONG_DAN_ADMIN_PL3.md`.
- **Vận hành**: `docs/HKG/PM2_DEPLOY.md` (triển khai PM2), `backend/MIGRATION_GUIDE*.md` (nâng cấp CSDL), README backend/frontend.
- **Quy trình cập nhật phiên bản**: Git (nhánh `feature/*` → kiểm thử trên DB test → commit chuẩn `feat|fix(module)` → deploy → `pm2 restart` từng service, downtime ≈ 0); toàn bộ mốc phiên bản tại `09_kiem_thu_van_hanh_phien_ban.md` mục 3.
- **Xử lý sự cố** (troubleshooting): quy trình 6 bước tại `09_…` mục 4 (ghi nhận → chẩn đoán trên DB test → sửa trên nhánh + pytest → deploy → kiểm chứng đối soát → báo cáo lưu `docs/Fix-Bao-Cao/`); sự cố hạ tầng khôi phục theo quy trình backup/restore (RPO 12h).
- **HDSD người dùng cuối theo vai trò** (công chức / lãnh đạo / TCCB / học viên): **đang biên soạn**, hoàn thành cùng đợt bàn giao hồ sơ.

---

## 6. Hồ sơ gốc (chủ trương triển khai)

- Đây là hồ sơ hành chính do **Phòng TCCB** tập hợp (mục 1 và mục 10 của công văn 153/CNTT) — không thuộc phạm vi hồ sơ kỹ thuật tự sinh được từ hệ thống.
- Căn cứ pháp lý của đợt kiểm tra đã dẫn tại công văn: QĐ 1804/QĐ-TCHQ (31/7/2024) và QĐ 330/QĐ-HQKV8 (10/7/2025).
- **Cần bổ sung từ TCCB**: quyết định/công văn phê duyệt chủ trương xây dựng – triển khai phần mềm KPI & Digital Learning (nếu có), hoặc văn bản giao nhiệm vụ tương đương; kèm danh sách đầu mối kỹ thuật (mục 10) để ghi vào công văn phúc đáp.
