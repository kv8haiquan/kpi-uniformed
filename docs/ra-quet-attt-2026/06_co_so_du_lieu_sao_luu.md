# Mục 6 — Cơ sở dữ liệu, sao lưu/phục hồi, dữ liệu cá nhân và biện pháp bảo vệ

> Phục vụ công văn 153/CNTT ngày 08/7/2026. Lập ngày 30/07/2026.
> Từ điển dữ liệu chi tiết (96 bảng, đầy đủ cột/kiểu/khóa): xem **Phụ lục** `06_phu_luc_tu_dien_du_lieu.md`.

## 1. Tổng quan cơ sở dữ liệu

| Hạng mục | Giá trị |
|---|---|
| Hệ quản trị | PostgreSQL 15.16 |
| Tên database | `kpi_haiquan` |
| Kích thước | ~170 MB |
| Số bảng | 96 bảng / 8 schema |
| Truy cập | Chỉ nội bộ máy chủ (localhost:5432), không mở ra Internet |
| Tài khoản ứng dụng | `kpi_user` (không dùng superuser cho ứng dụng) |

### Phân bố schema (multi-schema trong 1 database)

| Schema | Module | Số bảng | Bảng tiêu biểu |
|---|---|---|---|
| `public` | KPI (production) + platform | 37 | `cong_chuc` (558), `ke_khai_cong_viec` (44.552), `danh_gia_thang` (2.614), `tieu_chi_chung_danh_gia` (26.020), `dang_ky_nghi` (16.448) |
| `lms` | Đào tạo | 20 | `khoa_hoc`, `cau_hoi_dgnl`, `ky_thi`, `thi_sinh`, `ket_qua_bai_kiem_tra` |
| `forum` | Diễn đàn | 5 | `chu_de`, `binh_luan` |
| `legal` | Pháp luật | 6 | `van_ban`, `linh_vuc` |
| `portal` | Portal/CMS | 5 | `bai_viet`, `chuyen_muc` |
| `common` | Dùng chung | 5 | `thong_bao`, `tap_tin` |
| `meeting` | Họp Không Giấy | 13 | `cuoc_hop`, `tai_lieu`, `y_kien` |
| `chi_tieu` | Chỉ tiêu đơn vị | 5 | `danh_muc_chi_tieu`, `giao_nam`, `dang_ky_thang` |

Nguyên tắc: module mới **chỉ đọc** (`SELECT`) các bảng dùng chung `public.cong_chuc`, `public.don_vi`, `public.vai_tro`; mọi bảng nghiệp vụ mới nằm trong schema riêng, FK trực tiếp về `public.cong_chuc(id)`.

## 2. Phương án sao lưu

Sao lưu tự động qua cron hệ thống (`/etc/cron.d/hkg-backups`):

| Thời điểm | Việc | Script |
|---|---|---|
| 02:00 và 14:00 hằng ngày | Full `pg_dump` DB + rsync thư mục uploads (file đính kèm) | `/opt/kpi/scripts/backup_daily.sh` |
| 02:30 và 14:30 hằng ngày | Đẩy bản backup **đã mã hóa** lên private GitHub (off-site) | `/opt/kpi/scripts/backup_to_github.sh` |
| 02:45 và 14:45 hằng ngày | Snapshot mã nguồn → branch `auto-backup` | `/opt/kpi/scripts/backup_source.sh` |

- Định dạng backup DB: `db_*.sql.gz` (pg_dump + gzip, có kiểm tra toàn vẹn gzip sau khi dump).
- **Retention:** bản ngày giữ 30 ngày; bản tháng giữ 400 ngày (~12 tháng); tự động xóa bản quá hạn.
- Log sao lưu: `/var/log/backup_kpi.log`, `/var/log/backup_github.log`, `/var/log/backup_source.log`.

## 3. Phương án phục hồi

1. Chọn bản backup gần nhất (`db_YYYYMMDD_HHMMSS.sql.gz`).
2. Restore vào **database tạm** để kiểm tra toàn vẹn trước (`createdb kpi_haiquan_restore` → `gunzip -c ... | psql -d kpi_haiquan_restore`).
3. Sau khi xác nhận dữ liệu đúng: dừng các backend (PM2), swap database (rename), khởi động lại dịch vụ.
4. RPO tối đa: 12 giờ (2 bản/ngày). RTO thực tế: < 30 phút (DB ~170 MB).
5. Quy trình đã được diễn tập khi nâng cấp schema (bản `premig` được dump thủ công trước mỗi migration lớn).

## 4. Phân loại dữ liệu và dữ liệu cá nhân

### Dữ liệu cá nhân được xử lý (theo Nghị định 13/2023/NĐ-CP)

| Trường | Bảng | Phân loại |
|---|---|---|
| Họ tên (`ho_ten`) | `public.cong_chuc` | Dữ liệu cá nhân cơ bản |
| Mã công chức (`ma_cc`) | `public.cong_chuc` | Định danh nội ngành |
| Email (`email`) | `public.cong_chuc` | Dữ liệu cá nhân cơ bản |
| Số điện thoại (`so_dien_thoai`) | `public.cong_chuc` | Dữ liệu cá nhân cơ bản |
| Đơn vị, chức vụ, vai trò | `public.cong_chuc` | Thông tin công vụ |
| Kết quả đánh giá, xếp loại A/B/C/D | `danh_gia_thang`, `chi_tiet_xep_loai`, `phieu_danh_gia_*` | Dữ liệu nội bộ nhạy cảm (ảnh hưởng thi đua, thu nhập) |
| Nghỉ phép | `dang_ky_nghi` | Dữ liệu nội bộ |
| Kết quả thi/khảo sát | `lms.ket_qua_bai_kiem_tra`, `lms.thi_sinh` | Dữ liệu nội bộ |

**Không lưu:** CCCD/hộ chiếu, dữ liệu sinh trắc, tài khoản ngân hàng, dữ liệu sức khỏe. Mật khẩu **không lưu dạng rõ** — chỉ lưu hash bcrypt.

### Phạm vi dữ liệu

- Toàn bộ dữ liệu là **dữ liệu nội bộ** của Chi cục (558 tài khoản công chức, 15 đơn vị).
- Không có dữ liệu công dân/doanh nghiệp bên ngoài.

## 5. Biện pháp bảo vệ dữ liệu

| Biện pháp | Hiện trạng |
|---|---|
| Mã hóa kênh truyền | HTTPS/TLS toàn bộ (Let's Encrypt), cổng 80 redirect 443 |
| Mật khẩu | Hash bcrypt (passlib), không lưu plaintext |
| DB không public | PostgreSQL chỉ nghe localhost, không mở cổng ra Internet |
| Phân quyền ứng dụng | RBAC 2 lớp (vai trò + đơn vị) — chi tiết tại tài liệu Mục 7 |
| Backup off-site mã hóa | Bản backup đẩy GitHub private **đã mã hóa** trước khi đẩy |
| Chống SQL injection | ORM SQLAlchemy + parameterized query toàn bộ |
| Validate dữ liệu vào | Pydantic schema trên mọi endpoint |
| Nhật ký | Bảng `audit_log`, `lich_su_*` + log ứng dụng (loguru/PM2) |
