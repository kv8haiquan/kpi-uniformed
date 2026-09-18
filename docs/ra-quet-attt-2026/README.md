# Hồ sơ phục vụ công văn 153/CNTT — Kiểm tra, đánh giá an toàn, an ninh thông tin

> Phần mềm theo dõi, đánh giá KPI & Digital Learning — Chi cục Hải quan Khu vực VIII.
> Lập ngày 30/07/2026. Đầu mối tiếp nhận phía CNTT: Đ/c Đỗ Quang Huy (Phó Trưởng phòng), Đ/c Vi Trung Hiếu.

## Trạng thái 10 mục theo công văn

| Mục | Nội dung yêu cầu | Tài liệu | Trạng thái |
|---|---|---|---|
| 1 | Hồ sơ chủ trương, phê duyệt triển khai | *(hồ sơ hành chính — Phòng TCCB tập hợp)* | ⏳ Chờ TCCB |
| 2 | Mô tả chức năng, quy trình nghiệp vụ | `02_mo_ta_chuc_nang_quy_trinh.md` | ✅ Xong |
| 3 | Danh mục SP/CV, tiêu chí, công thức điểm, quy tắc xếp loại | `03_tieu_chi_cong_thuc_xep_loai.md` | ✅ Xong |
| 4 | Mã nguồn, thư viện, framework, phiên bản | `04_danh_muc_ma_nguon_thu_vien.md` | ✅ Xong |
| 5 | Kiến trúc, máy chủ, tên miền, IP, cổng | `05_kien_truc_he_thong.md` | ✅ Xong |
| 6 | CSDL, sao lưu/phục hồi, dữ liệu cá nhân | `06_co_so_du_lieu_sao_luu.md` + phụ lục `06_phu_luc_tu_dien_du_lieu.md` (96 bảng) | ✅ Xong |
| 7 | Tài khoản, phân quyền, xác thực, nhật ký, giám sát | `07_tai_khoan_phan_quyen_nhat_ky.md` | ✅ Xong |
| 8 | Danh mục API, kết nối, tích hợp | `08_danh_muc_api.md` (555 endpoints / 8 service) | ✅ Xong |
| 9 | Hồ sơ kiểm thử, nghiệm thu, HDSD, cập nhật phiên bản | `09_kiem_thu_van_hanh_phien_ban.md` | ✅ Xong |
| 10 | Đầu mối kỹ thuật | Ghi tại công văn phúc đáp | ⏳ Chờ TCCB |

## Tài liệu bổ sung

- `10_HOI_DAP_BO_SUNG.md` — trả lời trực tiếp bộ câu hỏi của đoàn kiểm tra (kiến trúc, backup, PII, mật khẩu, audit, API, kiểm thử) — lập 05/08/2026, đã gồm hiện trạng sau đợt vá 31/07.
- `api-specs/` — 8 file OpenAPI JSON (export từ từng service) + `danh_muc_endpoints.csv` (555 endpoints, mở bằng Excel).

## Tài liệu nội bộ (không bàn giao nguyên trạng)

- `BAO_CAO_RA_QUET_NOI_BO.md` — kết quả tự rà quét (bandit, pip-audit, npm audit, rà cấu hình) + kế hoạch khắc phục. Dùng để vá trước khi đoàn kiểm tra rà quét; sau khi vá xong sẽ cập nhật và có thể trích nộp phần "đã khắc phục".

## Nguyên tắc khi bàn giao mã nguồn (mục 4)

1. Chốt bản tag (ví dụ `audit-2026-07`) từ nhánh production, `git archive` **loại trừ** `.env`, backup/dump, `venv/`, `node_modules/`, dữ liệu uploads.
2. Quét secrets lần cuối trên gói bàn giao trước khi gửi.
3. SECRET_KEY, mật khẩu DB không nằm trong gói — cung cấp riêng qua kênh bảo mật nếu được yêu cầu.
