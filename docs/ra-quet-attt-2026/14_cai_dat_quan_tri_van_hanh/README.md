# Bộ tài liệu hướng dẫn cài đặt, cấu hình, quản trị và vận hành hệ thống

> Phục vụ công văn 153/CNTT ngày 08/7/2026 — Mục 14.
> Lập ngày 06/10/2026.

## Mục đích

Hướng dẫn chi tiết từng bước cài đặt, cấu hình, quản trị và vận hành hệ thống **KPI & Nền tảng Số Thống nhất** của Chi cục Hải quan Khu vực VIII (kpihaiquan.vn, IP 79.108.216.189).

## Đối tượng đọc

- **Quản trị viên hệ thống** — cài đặt lần đầu, cấu hình, bảo trì máy chủ
- **Người vận hành** — triển khai phiên bản mới, backup/restore, xử lý sự cố
- **Người phát triển** — hiểu môi trường production để tránh lỗi khi triển khai

## Danh mục tài liệu

| File | Nội dung | Đối tượng |
|------|----------|-----------|
| [01_cai_dat_moi_truong.md](01_cai_dat_moi_truong.md) | Yêu cầu phần cứng, cài đặt hệ điều hành, cài gói phụ thuộc, tạo database, seed dữ liệu, build lần đầu, kịch bản cài đặt lại toàn bộ (DR) | Quản trị viên |
| [02_cau_hinh.md](02_cau_hinh.md) | Biến môi trường (.env), nginx, PM2, cron, logrotate, tường lửa, múi giờ | Quản trị viên, Vận hành |
| [03_quan_tri_he_thong.md](03_quan_tri_he_thong.md) | Quản trị tài khoản người dùng & phân quyền, quản lý PM2, phát hành phiên bản (trien_khai.sh), quay lui | Vận hành, Quản trị viên |
| [04_quan_tri_csdl.md](04_quan_tri_csdl.md) | Cấu trúc schema/owner, tài khoản DB, migration, backup/restore, tạo DB test, bảo trì, quy tắc an toàn | Vận hành, Quản trị viên |
| [05_van_hanh_hang_ngay.md](05_van_hanh_hang_ngay.md) | Khởi động/dừng/restart, kiểm tra trạng thái, xem log, bảo trì có kế hoạch, xử lý sự cố OOM/kỳ thi | Vận hành |

## Tài liệu liên quan

Bộ tài liệu này **BỔ SUNG** cho các tài liệu khác đã có:

- `docs/ra-quet-attt-2026/05_kien_truc_he_thong.md` — Kiến trúc tổng thể
- `docs/ra-quet-attt-2026/06_co_so_du_lieu_sao_luu.md` — Cấu trúc CSDL, phương án backup
- `docs/ra-quet-attt-2026/07_tai_khoan_phan_quyen_nhat_ky.md` — Phân quyền, nhật ký
- `docs/ra-quet-attt-2026/12_quy_trinh_giam_sat_van_hanh.md` — Quy trình giám sát (đang soạn)
- `docs/ra-quet-attt-2026/16_loi_thuong_gap_khac_phuc.md` — Lỗi thường gặp (đang soạn)
- `docs/van-hanh/HUONG_DAN_DEV_PROD.md` — Môi trường Dev và Production
- `docs/van-hanh/PHIEN_BAN_PROD.md` — Lịch sử phát hành production
- `backend/README.md`, `frontend/README.md` — Tài liệu kỹ thuật từng module
- `CLAUDE.md` — Hướng dẫn phát triển và quy trình Git

## Lưu ý quan trọng

⚠️ **Database tại `localhost:5432` CHÍNH LÀ PRODUCTION** đang phục vụ 558 người dùng. Tài liệu này chỉ GHI NHẬN cấu hình, KHÔNG hướng dẫn thực hiện thao tác ghi dữ liệu trên production mà không có sự xác nhận của người chủ dự án.

⚠️ **Mật khẩu và khóa bí mật** trong tài liệu đều ghi `<cung cấp qua kênh bảo mật>` — KHÔNG bao giờ commit giá trị thật vào Git.

## Lịch sử cập nhật

| Ngày | Phiên bản | Nội dung thay đổi |
|------|-----------|-------------------|
| 06/10/2026 | 1.0 | Phiên bản đầu tiên — ghi nhận trạng thái production tại commit 9534f17 |
