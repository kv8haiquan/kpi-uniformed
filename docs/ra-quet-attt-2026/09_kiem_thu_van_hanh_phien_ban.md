# Mục 9 — Hồ sơ kiểm thử, nghiệm thu, hướng dẫn quản trị/vận hành/sử dụng, cập nhật phiên bản và xử lý sự cố

> Phục vụ công văn 153/CNTT ngày 08/7/2026. Lập ngày 30/07/2026.

## 1. Hồ sơ kiểm thử

### 1.1. Khung kiểm thử

| Tầng | Framework | Cấu hình |
|---|---|---|
| Backend (8 service Python) | pytest + pytest-asyncio, đo độ phủ pytest-cov | `backend/pytest.ini` |
| Frontend (Next.js) | Vitest + Testing Library + jsdom | `frontend/` (thiết lập Phase 4.1) |
| Quy tắc an toàn khi test | Mọi test ghi DB **bắt buộc** chạy trên database test `kpi_haiquan_test` (clone từ production, override qua biến `DB_NAME`) — tuyệt đối không test ghi trên production | Quy định tại `CLAUDE.md` |

### 1.2. Thống kê bộ kiểm thử tự động (kiểm đếm 30/07/2026)

**Backend: 73 file test / ~749 test case.** Phân bố:

| Module | Số file test | Số test case (ước) | Nội dung chính |
|---|---|---|---|
| Tests lõi KPI (`backend/tests/`) | 13 | ~90 | Unit test công thức `kpi_calculator_v2`, `kpi_lanh_dao_v2`, HDLD; integration kê khai V2, PL3 Excel, lịch sử điều chuyển; **regression** bảo đảm công thức V1 không đổi (baseline) |
| LMS | 13 | ~179 | Khóa học, bài kiểm tra, ĐGNL, kỳ thi, chứng chỉ |
| Họp Không Giấy (HKG) | 24 | ~153 | Cuộc họp, tài liệu, WebSocket trình chiếu, phân quyền |
| Legal | 8 | ~108 | Văn bản, tìm kiếm, phân quyền biên tập |
| Portal | 7 | ~68 | Tin bài, chuyên mục |
| Common | 7 | ~64 | Thông báo, tập tin, health check |
| Forum | 8 | ~57 | Chủ đề, bình luận, tìm kiếm |
| Chỉ tiêu | 4 | ~30 | Giao chỉ tiêu, đăng ký tháng, duyệt |

**Frontend: 5 file test / ~15 test case** (smoke test, hook đồng bộ trình chiếu, responsive, tab leader).

### 1.3. Kiểm thử thủ công và nghiệm thu người dùng (UAT)

- Checklist UAT và checklist triển khai theo giai đoạn: `docs/HKG/Phase_4_1_UAT_Checklist.md`, `Phase_4_1_Deploy_Checklist.md` (mô-đun HKG).
- **Đối chiếu số liệu thực tế** thay vai trò nghiệm thu định kỳ với module KPI: bộ 22 báo cáo tại `docs/Fix-Bao-Cao/` — đối chiếu xếp loại tháng 01, 04, 05/2026, kiểm chứng biểu quyết 3 nguồn, xác minh 0 sai lệch sau mỗi đợt hiệu chỉnh công thức.
- Kiểm thử bảo mật nội bộ: bandit + pip-audit + npm audit (kết quả tại `BAO_CAO_RA_QUET_NOI_BO.md`).

## 2. Tài liệu hướng dẫn quản trị, vận hành, sử dụng

### 2.1. Đã có

| Nhóm | Tài liệu |
|---|---|
| Quản trị nghiệp vụ | `docs/HUONG_DAN_ADMIN_PL3.md` — quản lý danh mục PL3, phiên bản công thức KPI, cấp độ, sản phẩm chuẩn |
| Vận hành hệ thống | `docs/HKG/PM2_DEPLOY.md` (triển khai PM2), `backend/MIGRATION_GUIDE.md` + `MIGRATION_GUIDE_20260227.md` (nâng cấp CSDL), `backend/README.md`, `frontend/README.md` (cài đặt/chạy) |
| Quy tắc nghiệp vụ | `docs/BUSINESS_RULES_v3_0_PL3.md` (quy tắc PL3 V2), `docs/lms/LMS_BUSINESS_RULES.md`, tương tự cho Forum/Legal/Portal/Chỉ tiêu |
| Đặc tả kỹ thuật | Bộ `*_API_SPECS.md` + `*_DATABASE_DESIGN.md` cho từng module (LMS, HKG, Forum, Legal, Portal, Chỉ tiêu); `docs/shared/SHARED_AUTH_SPECS.md`, `SHARED_DB_REFERENCE.md`, `SHARED_CODING_STANDARDS.md`; `docs/API_CONTRACT_BETWEEN_MODULES.md` |
| Vận hành sao lưu | Script + cron backup (mô tả tại tài liệu Mục 6) |

### 2.2. Kế hoạch bổ sung (đang biên soạn)

Hướng dẫn sử dụng theo vai trò người dùng cuối: (1) Công chức — kê khai, tự chấm tiêu chí chung; (2) Lãnh đạo — phê duyệt, đánh giá, xếp loại; (3) TCCB — báo cáo, đối soát; (4) Học viên/Giảng viên LMS. Dự kiến hoàn thành cùng đợt bàn giao hồ sơ.

## 3. Hồ sơ cập nhật phiên bản

### 3.1. Quản lý phiên bản

- Toàn bộ mã nguồn quản lý bằng **Git**: **181 commit** từ 09/02/2026 (~6 tháng phát triển), commit theo chuẩn `feat|fix|chore|refactor|docs(module): mô tả` — 89 feat (49%), 48 fix (27%), còn lại chore/refactor/docs.
- Nhánh: tính năng phát triển trên `feature/[module]-[tính năng]`, hợp vào nhánh chính sau kiểm thử; snapshot mã nguồn tự động 2 lần/ngày lên branch `auto-backup` (off-site).

### 3.2. Các mốc phiên bản chính

| Thời gian | Phiên bản / mốc | Nội dung |
|---|---|---|
| 02/2026 | Khởi tạo | KPI V1 (công thức SP chuẩn 96 SP/ngày), cấu trúc hệ thống |
| 02–03/2026 | KPI V1 + LMS core | Kê khai, phê duyệt, đánh giá tháng; khóa học, đăng ký học |
| 04/2026 | **KPI V2_PL3** | Chuyển công thức theo danh mục PL3 (2.812 đầu việc, hệ số điểm/25); công thức KPI lãnh đạo V2 (cộng SP cấp dưới); có regression test bảo toàn V1 |
| 04–05/2026 | v3.6–v3.7 | Điểm tiêu chí chung thập phân (bội 0,5); phiếu đánh giá tháng; xử lý công chức điều chuyển đơn vị; HKG Phase 4 (trình chiếu WebSocket) |
| 06/2026 | Chỉ tiêu đơn vị | Module chỉ tiêu (giao năm, đăng ký tháng, 26 endpoints) |
| 07/2026 | v3.8 + hardening | Đối soát đánh giá tháng (TCCB); CCT sửa điểm tiêu chí chung; chống gian lận thi ĐGNL (single-session, fullscreen, best-score); in phiếu quý 02A/02B; fix mở khóa chuyển đơn vị |

## 4. Hồ sơ khắc phục lỗi, xử lý sự cố

### 4.1. Cách ghi nhận hiện hành

- **48 commit `fix(...)`** trong git log — mỗi lỗi ghi rõ module, hiện tượng, cách sửa.
- **Báo cáo tổng kết sửa lỗi lớn** (9 file): chống gian lận thi, trang thi, phê duyệt đăng ký học, tích hợp thông báo, fix tổng hợp 27/02/2026...
- **Báo cáo đối chiếu dữ liệu định kỳ** (`docs/Fix-Bao-Cao/`, 22 file): đối chiếu kết quả xếp loại từng tháng với dữ liệu gốc, phát hiện – sửa – kiểm chứng lại (ví dụ đối chiếu T01, T04, T05/2026).

### 4.2. Quy trình xử lý sự cố đang áp dụng

1. Ghi nhận (người dùng phản ánh / báo cáo đối chiếu / log hệ thống PM2, nginx, `audit_log`).
2. Chẩn đoán trên môi trường dev + database test `kpi_haiquan_test` (không thao tác trực tiếp production).
3. Sửa lỗi trên nhánh `feature/*`, chạy pytest module liên quan; nếu ảnh hưởng dữ liệu cũ thì viết kịch bản backfill kèm kiểm chứng.
4. Triển khai: commit `fix(...)` → deploy → `pm2 restart` service liên quan (downtime ≈ 0 do các service độc lập).
5. Kiểm chứng sau triển khai bằng truy vấn đối soát; sự cố lớn lập báo cáo tổng kết lưu `docs/Fix-Bao-Cao/`.
6. Sự cố hạ tầng: khôi phục theo quy trình backup/restore (tài liệu Mục 6, RPO 12 giờ).

### 4.3. Đề xuất chuẩn hóa (ghi nhận để hoàn thiện)

- Lập file `LICH_SU_PHIEN_BAN.md` (changelog) tổng hợp từ git log theo mẫu chuẩn.
- Mẫu biên bản sự cố chuẩn (template incident report) cho các sự cố mức nghiêm trọng.
- Chạy và đính kèm báo cáo độ phủ kiểm thử (`pytest --cov`) trên database test vào hồ sơ nghiệm thu.
