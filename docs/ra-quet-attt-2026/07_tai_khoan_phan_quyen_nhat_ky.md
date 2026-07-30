# Mục 7 — Tài khoản, phân quyền, xác thực, nhật ký hệ thống và cơ chế giám sát

> Phục vụ công văn 153/CNTT ngày 08/7/2026. Lập ngày 30/07/2026.

## 1. Tài khoản người dùng

| Hạng mục | Giá trị |
|---|---|
| Nguồn tài khoản | Bảng `public.cong_chuc` — 558 tài khoản (đồng bộ theo danh sách công chức của Phòng TCCB) |
| Tên đăng nhập | Mã công chức (ví dụ `20ZZ-0224`) |
| Mật khẩu | Hash **bcrypt** (passlib), không lưu dạng rõ |
| Mật khẩu khởi tạo/reset | `123456` — người dùng tự đổi qua chức năng đổi mật khẩu (`POST /api/v1/auth/change-password`); hiện **chưa** có cơ chế bắt buộc đổi ở lần đăng nhập đầu (đã ghi nhận tại báo cáo rà quét nội bộ, mục khuyến nghị) |
| Khóa tài khoản | Cờ `is_active`, `is_deleted` — công chức chuyển công tác/nghỉ việc bị vô hiệu hóa, không xóa vật lý (giữ lịch sử đánh giá) |
| Tài khoản quản trị | Vai trò `ADMIN` (quản trị hệ thống) — số lượng hạn chế; các vai trò platform bổ sung cấp theo nhiệm vụ |

## 2. Cơ chế xác thực

- **JWT (HS256)** cấp tại `POST /api/v1/auth/login` (KPI backend). Payload: `sub` (UUID công chức), `ma_cc`, `vai_tro`, `don_vi_id`, `is_lanh_dao`, `exp`.
- Hạn token: **480 phút (8 giờ)** — hết hạn phải đăng nhập lại; không dùng session server-side.
- Các service khác (LMS, Forum, HKG, ...) tự verify chữ ký JWT bằng SECRET_KEY dùng chung (module `backend/shared/`) — kiến trúc SSO stateless.
- SECRET_KEY lưu trong `backend/.env` (không commit git, không hardcode trong mã nguồn).
- Frontend lưu token trong Zustand store; mọi request kèm header `Authorization: Bearer <token>` (interceptor axios).
- WebSocket HKG dùng token riêng ngắn hạn (`ws_presentation`, TTL tối đa 6 giờ).

## 3. Phân quyền (RBAC 2 lớp)

### Lớp 1 — Vai trò chính (`public.vai_tro`, 9 vai trò)

| Mã | Vai trò | Quyền chính |
|---|---|---|
| CCT | Chi cục trưởng | Duyệt cuối, xếp loại toàn Chi cục, điều chỉnh kết quả |
| PCCT | Phó Chi cục trưởng | Duyệt/đánh giá khối phụ trách |
| TDV | Trưởng đơn vị | Duyệt kê khai, đánh giá công chức trong đơn vị |
| PDV | Phó đơn vị | Duyệt kê khai trong phạm vi phân công |
| QLDV | Quản lý đơn vị | Quản lý nghiệp vụ đơn vị |
| CC | Công chức | Kê khai công việc, xem kết quả của mình |
| HD_111 | Hợp đồng 111 | Kê khai (phạm vi hạn chế) |
| TCCB | Cán bộ Tổ chức | Tổng hợp, đối soát, báo cáo toàn Chi cục |
| ADMIN | Quản trị hệ thống | Quản lý tài khoản, danh mục, cấu hình |

### Lớp 2 — Vai trò nền tảng (`public.platform_role`, 15 vai trò, gán qua `cong_chuc_platform_role`)

GIANG_VIEN, QT_DAO_TAO (LMS); DIEU_PHOI_FORUM, CHUYEN_GIA (Forum); BIEN_TAP, QT_NOI_DUNG (Legal/Portal); THU_KY_HOP, CHANH_VP (HKG); QT_CHI_TIEU, THEO_DOI_CHI_TIEU (Chỉ tiêu); QT_ATTT, TRUONG_CNTT (quản trị); BI_THU_CHI_BO, PHO_BI_THU, DANG_VIEN (sinh hoạt Đảng).

### Nguyên tắc thực thi quyền

- Kiểm tra quyền tại **backend** trên từng endpoint (dependency `get_current_user` + kiểm tra vai trò/đơn vị) — frontend chỉ ẩn/hiện UI, không phải chốt chặn.
- Phạm vi dữ liệu ràng theo `don_vi_id`: lãnh đạo đơn vị chỉ thấy/duyệt công chức thuộc đơn vị mình; xử lý riêng trường hợp điều chuyển đơn vị (bảng `lich_su_dieu_chuyen`).
- Chức năng nhạy cảm (điều chỉnh điểm, mở khóa, reset mật khẩu, import dữ liệu) giới hạn cho CCT/TCCB/ADMIN.

## 4. Nhật ký hệ thống

### Nhật ký trong database

| Bảng | Nội dung ghi |
|---|---|
| `public.audit_log` | Thao tác thay đổi dữ liệu: bảng, bản ghi, hành động, giá trị cũ/mới (JSONB), user_id, **địa chỉ IP, user-agent**, thời điểm |
| `public.lich_su_dieu_chinh` | Lịch sử điều chỉnh kết quả đánh giá |
| `public.lich_su_dieu_chuyen` | Lịch sử điều chuyển đơn vị của công chức |
| `chi_tieu.lich_su_duyet` | Lịch sử duyệt chỉ tiêu |
| `lms.kpi_integration_log` | Log tích hợp LMS ↔ KPI |
| Các cột `created_at`, `updated_at`, `nguoi_*_id`, `trang_thai` trên mọi bảng nghiệp vụ | Truy vết ai kê khai / ai duyệt cấp 1, cấp 2 / thời điểm từng bước |

### Nhật ký nghiệp vụ kê khai – thẩm định – phê duyệt – điều chỉnh

Mỗi bước của quy trình đều lưu người thực hiện + thời điểm ngay trên bản ghi nghiệp vụ (`ke_khai_cong_viec`, `danh_gia_thang`, `tieu_chi_chung_danh_gia`, `phieu_danh_gia_*`): người kê khai, người duyệt cấp 1/cấp 2, người điều chỉnh, trạng thái từng bước — bảo đảm truy vết toàn trình.

### Nhật ký ứng dụng và hệ thống

| Nguồn | Vị trí |
|---|---|
| Log ứng dụng (loguru + uvicorn access log) | PM2 log: `~/.pm2/logs/*.log`, xoay vòng bằng pm2-logrotate |
| Log truy cập web (toàn bộ request) | nginx access log / error log (`/var/log/nginx/`) |
| Log xác thực máy chủ | `/var/log/auth.log` (SSH) |
| Log sao lưu | `/var/log/backup_kpi.log`, `backup_github.log`, `backup_source.log` |
| Log 403 truy cập họp (HKG) | Ghi định danh người bị từ chối truy cập cuộc họp |

## 5. Cơ chế giám sát hoạt động

- **PM2**: giám sát 9 process, tự khởi động lại khi crash, thống kê CPU/RAM.
- **Đối soát nghiệp vụ**: trang "Đối soát đánh giá tháng" cho TCCB tự kiểm tra đơn vị/cá nhân chưa hoàn tất quy trình; các query audit định kỳ đối chiếu điểm.
- **Giám sát thi trực tuyến (LMS)**: single-session (1 phiên thi/thí sinh), cờ fullscreen, polling giám sát live cho quản trị.
- **Rà quét nội bộ**: bandit + pip-audit + npm audit chạy nội bộ trước khi bàn giao mã nguồn (kết quả tại `BAO_CAO_RA_QUET_NOI_BO.md`).
