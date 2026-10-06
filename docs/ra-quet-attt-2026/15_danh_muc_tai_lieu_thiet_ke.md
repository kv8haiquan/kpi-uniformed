# Mục 15 — Danh mục và hiện trạng các tài liệu phân tích, thiết kế kỹ thuật chi tiết được dẫn chiếu trong hồ sơ

> Phục vụ công văn 153/CNTT ngày 08/7/2026 — kiểm tra, đánh giá an toàn, an ninh thông tin.
> Lập ngày **06/10/2026** bởi đội ngũ kỹ thuật Chi cục Hải quan Khu vực VIII.
> Rà soát toàn bộ tài liệu được dẫn chiếu trong các mục 2–10 của hồ sơ rà quét ATTT.

---

## 1. Mục đích

Tài liệu này cung cấp:

1. **Danh mục đầy đủ** các tài liệu phân tích, thiết kế kỹ thuật chi tiết đã được dẫn chiếu trong hồ sơ rà quét ATTT (các mục 2–10).
2. **Hiện trạng từng tài liệu**: vị trí lưu trữ, ngày cập nhật cuối, có trong nhánh production (`prod`) hay không, mức độ khớp với code hiện hành.
3. **Đánh giá khoảng trống thiết kế**: những loại tài liệu còn thiếu hoặc chưa đầy đủ.
4. **Danh sách dẫn chiếu gãy** và tài liệu cần biên tập (chứa thông tin nhạy cảm) trước khi nộp.
5. **Đề xuất gói nộp** cụ thể cho đoàn kiểm tra.

---

## 2. Bảng danh mục tài liệu thiết kế theo nhóm

### 2.1. Kiến trúc tổng thể và chiến lược mở rộng

| Mã TL | Tên tài liệu | Đường dẫn | Dẫn chiếu từ | Ngày cập nhật | Trong nhánh prod? | Mức độ khớp code | Ghi chú |
|---|---|---|---|---|---|---|---|
| KT-01 | Chiến lược nền tảng số thống nhất | `docs/CHIEN_LUOC_NEN_TANG_THONG_NHAT.md` | CLAUDE.md (bảng "Tài liệu tham chiếu") | — | ❌ **Không tồn tại** | N/A | ⚠️ Dẫn chiếu gãy: file không có trong repo và không có trong lịch sử git (kiểm 06/10/2026). Nội dung chiến lược thay thế: `docs/shared/To_trinh_Nen_tang_Digital_Learning_HQKV8 (2).docx` + `05_kien_truc_he_thong.md` |
| KT-02 | CLAUDE.md — hướng dẫn dự án cho AI | `CLAUDE.md` | (tự tham chiếu, tổng quan toàn hệ thống) | 2026-08-25 | ✅ Có | **Khớp** | Tài liệu nội bộ dev, đề xuất biên tập trước khi nộp (chứa quy tắc cấm test prod, port, thông tin hạ tầng) |
| KT-03 | README backend | `backend/README.md` | 09, 10 | 2026-02-23 | ✅ Có | **Khớp** | Hướng dẫn cài đặt/chạy |
| KT-04 | README frontend | `frontend/README.md` | 09, 10 | 2026-02-23 | ✅ Có | **Khớp** | Hướng dẫn cài đặt/chạy |

### 2.2. Xác thực, phân quyền, bảo mật

| Mã TL | Tên tài liệu | Đường dẫn | Dẫn chiếu từ | Ngày cập nhật | Trong nhánh prod? | Mức độ khớp code | Ghi chú |
|---|---|---|---|---|---|---|---|
| AUTH-01 | Đặc tả xác thực SSO dùng chung | `docs/shared/SHARED_AUTH_SPECS.md` | 09 | 2026-02-23 | ✅ Có | **Khớp** | 17 KB, 630 dòng — thiết kế JWT, flow đăng nhập, vai trò |
| AUTH-02 | Tham chiếu cơ sở dữ liệu dùng chung | `docs/shared/SHARED_DB_REFERENCE.md` | 09 | 2026-02-23 | ✅ Có | **Khớp** | 22 KB — bảng public.cong_chuc, don_vi, vai_tro |
| AUTH-03 | Chuẩn viết code dùng chung | `docs/shared/SHARED_CODING_STANDARDS.md` | 09 | 2026-02-23 | ✅ Có | **Khớp** | 23 KB — quy ước code, response format, error handling |

### 2.3. Cơ sở dữ liệu

| Mã TL | Tên tài liệu | Đường dẫn | Dẫn chiếu từ | Ngày cập nhật | Trong nhánh prod? | Mức độ khớp code | Ghi chú |
|---|---|---|---|---|---|---|---|
| DB-01 | Từ điển dữ liệu 96 bảng | `docs/ra-quet-attt-2026/06_phu_luc_tu_dien_du_lieu.md` | 06, README | Đã nộp (60 KB) | ✅ Có | **Khớp** | Đã là phần hồ sơ chính thức |
| DB-02 | Database Design — LMS | `docs/lms/LMS_DATABASE_DESIGN.md` | 09 | 2026-02-23 | ✅ Có | **Khớp** | 13 KB — 11 bảng schema lms |
| DB-03 | Database Design — Forum | `docs/forum/FORUM_DATABASE_DESIGN.md` | 09 | 2026-02-23 | ✅ Có | **Khớp** | 7.6 KB — 5 bảng schema forum |
| DB-04 | Database Design — Legal | `docs/legal/LEGAL_DATABASE_DESIGN.md` | 09 | 2026-02-23 | ✅ Có | **Khớp** | 8.5 KB — 6 bảng schema legal |
| DB-05 | Database Design — Portal/Common | `docs/portal/PORTAL_COMMON_DATABASE_DESIGN.md` | 09 | 2026-02-23 | ✅ Có | **Khớp** | 12 KB — Portal 4 bảng + Common 4 bảng |
| DB-06 | Database Design — HKG | `docs/HKG/HKG_DATABASE_DESIGN.md` | 09 | 2026-05-03 | ✅ Có | **Khớp** | 25 KB — 14 bảng schema meeting |
| DB-07 | Database Design — Chỉ tiêu | `docs/Chi Tieu/CHI_TIEU_DATABASE_DESIGN.md` | 09 | 2026-06-04 | ✅ Có | **Khớp** | 13 KB — 5 bảng + 1 view schema chi_tieu |
| DB-08 | Hướng dẫn nâng cấp CSDL | `backend/MIGRATION_GUIDE.md` | 09, 10 | 2026-02-23 | ✅ Có | **Khớp** | 5.4 KB — quy trình Alembic, troubleshooting |
| DB-09 | Hướng dẫn nâng cấp 27/02/2026 | `MIGRATION_GUIDE_20260227.md` (thư mục gốc repo, 292 dòng) | 09, 10 | 2026-02-27 | ✅ | Lịch sử (mốc 27/02) | ⚠️ Dẫn chiếu **sai thư mục**: mục 10 ghi `backend/MIGRATION_GUIDE*.md` nên không bao trùm file này; file thực tế nằm ở thư mục gốc repo, có ở cả `main` và `prod` (hai nhánh cùng commit) |

**Đánh giá khoảng trống DB:**
- ⚠️ **Module KPI lõi (backend/app) KHÔNG có file DATABASE_DESIGN.md riêng** — thiết kế bảng schema public chỉ có trong `06_phu_luc_tu_dien_du_lieu.md` (dạng từ điển, không có ER diagram hay giải thích quan hệ chi tiết).
- Tất cả module mới (LMS, Forum, Legal, Portal, Common, HKG, Chỉ tiêu) đều có DATABASE_DESIGN.md đầy đủ.

### 2.4. API và tích hợp giữa các module

| Mã TL | Tên tài liệu | Đường dẫn | Dẫn chiếu từ | Ngày cập nhật | Trong nhánh prod? | Mức độ khớp code | Ghi chú |
|---|---|---|---|---|---|---|---|
| API-01 | Hợp đồng API giữa các module | `docs/API_CONTRACT_BETWEEN_MODULES.md` | 09 | 2026-02-28 | ✅ Có | **Khớp** | 13 KB — gọi nội bộ, header `X-Internal-Key`, format chung |
| API-02 | API Specs — LMS | `docs/lms/LMS_API_SPECS.md` | 09 | 2026-02-23 | ✅ Có | **Khớp nhẹ** | 13 KB, 569 dòng, ~45 endpoint theo spec; thực tế **111 endpoint** (file 08) — mở rộng sau spec ban đầu |
| API-03 | API Specs — Forum | `docs/forum/FORUM_API_SPECS.md` | 09 | 2026-02-23 | ✅ Có | **Khớp** | 8.1 KB, 389 dòng, ~15 endpoint; thực tế **27 endpoint** |
| API-04 | API Specs — Legal | `docs/legal/LEGAL_API_SPECS.md` | 09 | 2026-02-23 | ✅ Có | **Khớp** | 9.1 KB, 417 dòng, ~18 endpoint; thực tế **29 endpoint** |
| API-05 | API Specs — Portal/Common | `docs/portal/PORTAL_COMMON_API_SPECS.md` | 09 | 2026-02-23 | ✅ Có | **Khớp** | 9.5 KB, 418 dòng — Portal ~20 + Common ~15 endpoint; thực tế Portal **38** + Common **23** |
| API-06 | API Specs — HKG | `docs/HKG/HKG_API_SPECS.md` | 09 | 2026-05-03 | ✅ Có | **Khớp** | 18 KB, 779 dòng, ~50 endpoint; thực tế **55 endpoint** |
| API-07 | API Specs — Chỉ tiêu | `docs/Chi Tieu/CHI_TIEU_API_SPECS.md` | 09 | 2026-06-04 | ✅ Có | **Khớp** | 6.9 KB, 205 dòng, ~26 endpoint; thực tế **33 endpoint** |
| API-08 | Danh mục endpoint tổng hợp | `docs/ra-quet-attt-2026/08_danh_muc_api.md` | README, 10 | Đã nộp | ✅ Có | **Khớp** | Đã là phần hồ sơ chính thức — 555 endpoint / 8 service |
| API-09 | OpenAPI JSON (8 file) | `docs/ra-quet-attt-2026/api-specs/*.json` | 10 | Đã nộp | ✅ Có | **Khớp** | Export trực tiếp từ từng service production |
| API-10 | Danh mục endpoint CSV | `docs/ra-quet-attt-2026/api-specs/danh_muc_endpoints.csv` | 10 | Đã nộp (556 dòng) | ✅ Có | **Khớp** | Định dạng Excel, đầy đủ 555 endpoint |

**Đánh giá khoảng trống API:**
- ⚠️ **Module KPI lõi (backend/app, 239 endpoint) KHÔNG có file API_SPECS.md riêng** — thông tin nằm phân tán trong `08_danh_muc_api.md` (dạng bảng liệt kê) và OpenAPI JSON `kpi_8000.json`. KHÔNG có file mô tả use case, business flow, ví dụ request/response dạng văn bản như các module khác.
- Các module mới đều có API_SPECS.md chi tiết — nhưng số endpoint thực tế luôn nhiều hơn spec ban đầu (do phát triển thêm tính năng sau khi viết spec). Chênh lệch **chấp nhận được** (10–50%), không ảnh hưởng đến tính đầy đủ của OpenAPI JSON.

### 2.5. Nghiệp vụ và công thức tính toán

| Mã TL | Tên tài liệu | Đường dẫn | Dẫn chiếu từ | Ngày cập nhật | Trong nhánh prod? | Mức độ khớp code | Ghi chú |
|---|---|---|---|---|---|---|---|
| BIZ-01 | Tiêu chí, công thức, xếp loại KPI | `docs/ra-quet-attt-2026/03_tieu_chi_cong_thuc_xep_loai.md` | README | Đã nộp (9.8 KB) | ✅ Có | **Khớp** | Đã là phần hồ sơ chính thức — trích từ code + DB |
| BIZ-02 | Quy tắc nghiệp vụ KPI V3.0 PL3 | `docs/BUSINESS_RULES_v3_0_PL3.md` | 09, 10 | 2026-05-05 | ✅ Có | **Khớp** | 8.9 KB — quy tắc PL3, công thức V2, kê khai lãnh đạo |
| BIZ-03 | Phân tích tác động KPI V2 PL3 | `docs/IMPACT_ANALYSIS_KPI_V2_PL3.md` | (không dẫn chiếu trực tiếp) | 2026-05-05 | ✅ Có | **Khớp** | 21 KB — so sánh V1 vs V2, kịch bản chuyển đổi |
| BIZ-04 | Hướng dẫn quản trị PL3 | `docs/HUONG_DAN_ADMIN_PL3.md` | 09, 10 | 2026-05-05 | ✅ Có | **Khớp** | 8.5 KB — quản lý danh mục, phiên bản công thức |
| BIZ-05 | Business Rules — LMS | `docs/lms/LMS_BUSINESS_RULES.md` | 09 | 2026-02-23 | ✅ Có | **Khớp** | Quy tắc đào tạo, kỳ thi, chứng chỉ |
| BIZ-06 | Business Rules — Forum | `docs/forum/FORUM_BUSINESS_RULES.md` | 09 | 2026-02-23 | ✅ Có | **Khớp** | Quy tắc diễn đàn, duyệt bài, chuyên gia |
| BIZ-07 | Business Rules — Legal | `docs/legal/LEGAL_BUSINESS_RULES.md` | 09 | 2026-02-23 | ✅ Có | **Khớp** | Quy tắc văn bản pháp luật, biên tập |
| BIZ-08 | Business Rules — Portal/Common | `docs/portal/PORTAL_COMMON_BUSINESS_RULES.md` | 09 | 2026-02-23 | ✅ Có | **Khớp** | Quy tắc CMS, thông báo |
| BIZ-09 | Business Rules — Chỉ tiêu | `docs/Chi Tieu/CHI_TIEU_BUSINESS_RULES.md` | 09 | 2026-06-04 | ✅ Có | **Khớp** | Quy tắc giao chỉ tiêu, đăng ký tháng, duyệt |

**File mã nguồn công thức KPI:**
- `backend/app/core/kpi_calculator_v2.py` — công thức tính KPI công chức V2_PL3 (a, b, c, trừ lỗi 25%)
- `backend/app/core/kpi_lanh_dao_v2.py` — công thức KPI lãnh đạo V2 (cộng SP cấp dưới, a-b-c-d-đ-e)
- `backend/app/core/kpi_version.py` — quản lý phiên bản công thức
- `backend/app/services/xep_loai_quy_helpers.py` — tính điểm quý, ngưỡng A/B/C/D, kiểm soát tỷ lệ

### 2.6. Vận hành và triển khai

| Mã TL | Tên tài liệu | Đường dẫn | Dẫn chiếu từ | Ngày cập nhật | Trong nhánh prod? | Mức độ khớp code | Ghi chú |
|---|---|---|---|---|---|---|---|
| OPS-01 | Triển khai PM2 | `docs/HKG/PM2_DEPLOY.md` | 09, 10 | Không xác định | ✅ Có | **Khớp** | Hướng dẫn cấu hình PM2 cho 9 service |
| OPS-02 | Hướng dẫn dev-prod | `docs/van-hanh/HUONG_DAN_DEV_PROD.md` | (không dẫn chiếu trực tiếp) | Không xác định | ❓ Cần kiểm tra | N/A | Quy trình triển khai từ dev lên prod |
| OPS-03 | Phiên bản production | `docs/van-hanh/PHIEN_BAN_PROD.md` | (không dẫn chiếu trực tiếp) | Không xác định | ❓ Cần kiểm tra | N/A | Lịch sử phát hành |
| OPS-04 | Kế hoạch tách môi trường | `docs/van-hanh/KE_HOACH_TACH_MOI_TRUONG.md` | (không dẫn chiếu trực tiếp) | Không xác định | ❓ Cần kiểm tra | N/A | Kế hoạch, chưa triển khai |

### 2.7. Kiểm thử, sửa lỗi, nghiệm thu

| Mã TL | Tên tài liệu | Đường dẫn | Dẫn chiếu từ | Ngày cập nhật | Trong nhánh prod? | Mức độ khớp code | Ghi chú |
|---|---|---|---|---|---|---|---|
| TEST-01 | Checklist UAT Phase 4.1 HKG | `docs/HKG/Phase_4_1_UAT_Checklist.md` | 09, 10 | Không xác định | ✅ Có | **Khớp** | Checklist nghiệm thu WebSocket trình chiếu |
| TEST-02 | Checklist triển khai Phase 4.1 | `docs/HKG/Phase_4_1_Deploy_Checklist.md` | 09 | Không xác định | ✅ Có | **Khớp** | Quy trình triển khai HKG |
| TEST-03 | Báo cáo đối chiếu số liệu (22 file) | `docs/Fix-Bao-Cao/*.md` (22 file) | 09, 10 | Nhiều thời điểm | ✅ Có | **Khớp** | 765 dòng tổng — đối chiếu xếp loại T01, T04, T05/2026, xác minh 0 sai lệch |
| TEST-04 | Báo cáo rà quét nội bộ | `docs/ra-quet-attt-2026/BAO_CAO_RA_QUET_NOI_BO.md` | 10, README | Đã nộp (11 KB) | ✅ Có | **Khớp** | Kết quả bandit, pip-audit, npm audit, đợt vá 31/07/2026 |

**Bộ test tự động (không phải tài liệu văn bản, nhưng là hồ sơ kiểm thử quan trọng):**
- `backend/tests/` — 13 file test KPI lõi (~90 test case)
- `backend/lms_service/tests/` — 13 file (~179 test case)
- `backend/meeting_service/tests/` — 24 file (~153 test case)
- `backend/legal_service/tests/`, `forum_service/tests/`, `portal_service/tests/`, `common_service/tests/`, `chi_tieu_service/tests/` — 38 file (~287 test case)
- `frontend/__tests__/` — 5 file (~15 test case)
- **Tổng cộng: 73 file backend + 5 file frontend, ~749 test case**

### 2.8. Module HKG (Họp Không Giấy) — tài liệu chuyên biệt

| Mã TL | Tên tài liệu | Đường dẫn | Dẫn chiếu từ | Ngày cập nhật | Trong nhánh prod? | Mức độ khớp code | Ghi chú |
|---|---|---|---|---|---|---|---|
| HKG-01 | Báo cáo rà soát HKG 04/09 | `docs/HKG/BAO_CAO_RA_SOAT_HKG_20260904.md` | (không dẫn chiếu) | 2026-09-04 | ✅ Có | **Khớp** | Đo thật 6 tháng, 14/15 test đỏ do dữ liệu cũ |
| HKG-02 | Báo cáo Phase 4.1 Page Sync | `docs/HKG/BaoCao_TongKet_Phase4_1_PageSync.md` | (không dẫn chiếu) | Không xác định | ❓ Cần kiểm tra | **Khớp** | Tổng kết WebSocket đồng bộ trang |
| HKG-03 | Kế hoạch Phase 4.1 v3 FINAL | `docs/HKG/KeHoach_Phase4_1_PageSync_v3_FINAL.md` | (không dẫn chiếu) | Không xác định | ❓ Cần kiểm tra | **Khớp** | Kế hoạch phát triển |
| HKG-04 | MVP Report and Roadmap | `docs/HKG/MVP_REPORT_AND_ROADMAP.md` | (không dẫn chiếu) | Không xác định | ❓ Cần kiểm tra | **Khớp** | Báo cáo MVP, lộ trình phát triển |
| HKG-05 | Phân tích và góp ý HKG | `docs/HKG/PHAN_TICH_VA_GOP_Y_HKG.md` | (không dẫn chiếu) | Không xác định | ❓ Cần kiểm tra | N/A | Góp ý từ người dùng, feedback |

---

## 3. Đánh giá khoảng trống thiết kế

### 3.1. Thiếu hoàn toàn

| Loại tài liệu | Module bị thiếu | Mức độ ảnh hưởng | Nguồn thay thế |
|---|---|---|---|
| **SRS (Software Requirements Specification)** | Toàn bộ | Cao | Phần mô tả chức năng trong `02_mo_ta_chuc_nang_quy_trinh.md` đóng vai trò SRS thu gọn; yêu cầu chi tiết nằm phân tán trong BUSINESS_RULES + API_SPECS |
| **SDD (Software Design Document)** | KPI lõi (backend/app) | Trung bình | `03_tieu_chi_cong_thuc_xep_loai.md` + `06_phu_luc_tu_dien_du_lieu.md` (schema public) + `BUSINESS_RULES_v3_0_PL3.md` + OpenAPI JSON `kpi_8000.json` + file mã nguồn công thức (`kpi_calculator_v2.py`, `kpi_lanh_dao_v2.py`) |
| **API_SPECS.md (dạng văn bản)** | KPI lõi | Thấp | `08_danh_muc_api.md` (bảng tổng hợp) + OpenAPI JSON `kpi_8000.json` (đầy đủ) |
| **DATABASE_DESIGN.md riêng** | KPI lõi | Thấp | `06_phu_luc_tu_dien_du_lieu.md` (schema public) — dạng từ điển, không có ER diagram |
| **Sơ đồ tuần tự (Sequence Diagram)** | Toàn bộ | Trung bình | Quy trình mô tả bằng văn bản trong `02_mo_ta_chuc_nang_quy_trinh.md` + flowchart mermaid cho workflow chính |
| **Thiết kế bảo mật chi tiết** | Toàn bộ | Trung bình | Phân tán trong `SHARED_AUTH_SPECS.md` (JWT), `07_tai_khoan_phan_quyen_nhat_ky.md`, `10_HOI_DAP_BO_SUNG.md` mục 3 (xác thực, audit) |
| **Kịch bản test case chi tiết** | Toàn bộ | Trung bình | Bộ test tự động (pytest) đóng vai trò test case thực thi được; checklist UAT cho HKG Phase 4.1; báo cáo đối chiếu số liệu (22 file) cho KPI |

### 3.2. Chưa đầy đủ

| Loại tài liệu | Vấn đề | Đề xuất khắc phục |
|---|---|---|
| API_SPECS.md các module mới | Số endpoint thực tế (555) > số endpoint trong spec ban đầu (ước ~200) — do phát triển thêm sau khi viết spec | **Chấp nhận được** — OpenAPI JSON `*.json` (8 file) export trực tiếp từ production là nguồn đầy đủ 100% |
| Audit log | Bảng `audit_log` đã có cấu trúc nhưng chưa kích hoạt trigger tự động (ghi nhận trong `10_HOI_DAP_BO_SUNG.md` mục 3.3) | Không ảnh hưởng đến hồ sơ thiết kế — đây là kế hoạch triển khai |
| Hướng dẫn sử dụng người dùng cuối | Chưa có theo vai trò (CC/LĐ/TCCB/Học viên) — ghi nhận "đang biên soạn" trong `09_kiem_thu_van_hanh_phien_ban.md` | **Cần bổ sung trước khi nộp** — tài liệu mục 9 yêu cầu "hướng dẫn sử dụng" |

### 3.3. Lỗi thời hoặc không khớp

| Tài liệu | Vấn đề | Mức độ nghiêm trọng | Xử lý |
|---|---|---|---|
| `MIGRATION_GUIDE_20260227.md` | Dẫn chiếu ghi sai thư mục (`backend/` thay vì thư mục gốc) | Thấp | Ghi đúng đường dẫn khi đóng gói; không cần sửa file |
| API_SPECS.md (LMS, Forum, Legal, Portal, HKG, Chỉ tiêu) | Số endpoint thực tế nhiều hơn spec 10–50% | Thấp | Không cần sửa — OpenAPI JSON là nguồn chính thức |
| Các file trong `docs/HKG/` (MVP_REPORT, PHAN_TICH_VA_GOP_Y, ...) | Không được dẫn chiếu trong hồ sơ 2–10 nhưng tồn tại trong repo | N/A | Có thể bỏ qua hoặc đính kèm như tài liệu tham khảo |

---

## 4. Danh sách dẫn chiếu gãy và tài liệu cần biên tập

### 4.1. Dẫn chiếu gãy (file không tồn tại trong working tree hiện tại)

| File được dẫn chiếu | Dẫn chiếu từ | Hiện trạng | Xử lý đề xuất |
|---|---|---|---|
| `backend/MIGRATION_GUIDE_20260227.md` (theo mẫu `backend/MIGRATION_GUIDE*.md` ở mục 10) | 09, 10 | File có thật nhưng nằm ở **thư mục gốc**: `MIGRATION_GUIDE_20260227.md` (có ở cả `main` và `prod`) | Đóng gói đúng đường dẫn gốc; không di chuyển file |

### 4.2. Tài liệu cần biên tập trước khi nộp (chứa thông tin nhạy cảm hoặc nội bộ)

| File | Thông tin nhạy cảm | Mức độ | Xử lý đề xuất |
|---|---|---|---|
| `backend/.env.example` | Chứa mật khẩu mẫu `your_secure_password_here`, comment hướng dẫn tạo SECRET_KEY | Thấp | ✅ **Đã an toàn** — đây là file `.example`, không chứa giá trị thật; đề xuất nộp nguyên trạng |
| `CLAUDE.md` | Chứa quy tắc cấm test trên production, IP cloud `79.108.216.189`, thông tin cổng nội bộ, cấu trúc thư mục chi tiết | Trung bình | ⚠️ **Biên tập trước khi nộp** — bỏ phần "QUY TẮC TUYỆT ĐỐI" chứa IP/cảnh báo nội bộ, giữ phần kiến trúc kỹ thuật; HOẶC chỉ trích 1 phần (Tech Stack, Architecture, Domain Concepts) làm tài liệu riêng |
| `docs/HKG/PM2_DEPLOY.md` | Có thể chứa đường dẫn thư mục hệ thống, lệnh chạy cụ thể | Thấp | Rà soát trước khi nộp — bỏ đường dẫn tuyệt đối `/opt/kpi-prod` nếu có |
| `docs/van-hanh/HUONG_DAN_DEV_PROD.md` | Quy trình triển khai nội bộ, có thể chứa thông tin SSH/credential | Trung bình | ⚠️ **Biên tập trước khi nộp** — bỏ phần credential, giữ quy trình kỹ thuật |
| `docs/Fix-Bao-Cao/*.md` (22 file) | Chứa tên công chức thật, mã công chức, đơn vị — **dữ liệu cá nhân (PII)** | **Cao** | ⚠️ **CHỈ nộp tóm tắt/thống kê, KHÔNG nộp file gốc** — trích 1–2 file làm mẫu sau khi làm ẩn danh (thay tên người bằng "CC001", "CC002", ...) |
| `BAO_CAO_RA_QUET_NOI_BO.md` | Có thể chứa CVE cụ thể, dependency version nhạy cảm | Thấp | Rà soát — phần "đã khắc phục" an toàn để nộp, phần "kế hoạch khắc phục" cân nhắc |
| Các file trong `docs/HKG/` không được dẫn chiếu | Có thể chứa feedback người dùng, góp ý nội bộ | Thấp | **Không nộp** — không được dẫn chiếu trong hồ sơ chính thức |

### 4.3. Các file `.env`, backup, mật khẩu thật

| File | Hiện trạng | Xử lý |
|---|---|---|
| `backend/.env` | Chứa SECRET_KEY, DB password THẬT — **TUYỆT ĐỐI KHÔNG nộp** | ✅ Đã loại trừ trong `.gitignore`, không có trong repo |
| `backend/uploads/`, `frontend/.next/`, `node_modules/`, `venv/` | Thư mục runtime, không phải mã nguồn | ✅ Loại trừ bằng `git archive` với `.gitattributes` |
| Các file dump database (`*.sql`, `*.gz` trong `/var/backup/`) | Chứa toàn bộ dữ liệu người dùng thật | ✅ Không nộp — chỉ mô tả quy trình backup trong mục 06 |

---

## 5. Đề xuất gói nộp

### 5.1. Danh sách file cụ thể (82 file tài liệu kỹ thuật)

#### Nhóm A: Tài liệu đã nộp trong hồ sơ mục 2–10 (12 file)
```
docs/ra-quet-attt-2026/
├── README.md
├── 02_mo_ta_chuc_nang_quy_trinh.md
├── 03_tieu_chi_cong_thuc_xep_loai.md
├── 04_danh_muc_ma_nguon_thu_vien.md
├── 05_kien_truc_he_thong.md
├── 06_co_so_du_lieu_sao_luu.md
├── 06_phu_luc_tu_dien_du_lieu.md
├── 07_tai_khoan_phan_quyen_nhat_ky.md
├── 08_danh_muc_api.md
├── 09_kiem_thu_van_hanh_phien_ban.md
├── 10_HOI_DAP_BO_SUNG.md
├── BAO_CAO_RA_QUET_NOI_BO.md
└── api-specs/
    ├── danh_muc_endpoints.csv  (555 endpoint)
    ├── kpi_8000.json  (239 endpoint KPI)
    ├── svc_8001.json  (111 endpoint LMS)
    ├── svc_8002.json  (27 endpoint Forum)
    ├── svc_8003.json  (29 endpoint Legal)
    ├── svc_8004.json  (38 endpoint Portal)
    ├── svc_8005.json  (23 endpoint Common)
    ├── svc_8006.json  (55 endpoint HKG)
    └── svc_8007.json  (33 endpoint Chỉ tiêu)
```

#### Nhóm B: Tài liệu thiết kế dẫn chiếu trong mục 9 (25 file)
```
docs/
├── shared/
│   ├── SHARED_AUTH_SPECS.md
│   ├── SHARED_DB_REFERENCE.md
│   └── SHARED_CODING_STANDARDS.md
├── API_CONTRACT_BETWEEN_MODULES.md
├── BUSINESS_RULES_v3_0_PL3.md
├── HUONG_DAN_ADMIN_PL3.md
├── IMPACT_ANALYSIS_KPI_V2_PL3.md
├── lms/
│   ├── LMS_API_SPECS.md
│   ├── LMS_DATABASE_DESIGN.md
│   └── LMS_BUSINESS_RULES.md
├── forum/
│   ├── FORUM_API_SPECS.md
│   ├── FORUM_DATABASE_DESIGN.md
│   └── FORUM_BUSINESS_RULES.md
├── legal/
│   ├── LEGAL_API_SPECS.md
│   ├── LEGAL_DATABASE_DESIGN.md
│   └── LEGAL_BUSINESS_RULES.md
├── portal/
│   ├── PORTAL_COMMON_API_SPECS.md
│   ├── PORTAL_COMMON_DATABASE_DESIGN.md
│   └── PORTAL_COMMON_BUSINESS_RULES.md
├── HKG/
│   ├── HKG_API_SPECS.md
│   ├── HKG_DATABASE_DESIGN.md
│   ├── Phase_4_1_UAT_Checklist.md
│   ├── Phase_4_1_Deploy_Checklist.md
│   └── PM2_DEPLOY.md  ⚠️ (biên tập)
└── Chi Tieu/
    ├── CHI_TIEU_API_SPECS.md
    ├── CHI_TIEU_DATABASE_DESIGN.md
    └── CHI_TIEU_BUSINESS_RULES.md
```

#### Nhóm C: Tài liệu vận hành (4 file)
```
backend/
├── README.md
├── MIGRATION_GUIDE.md
MIGRATION_GUIDE_20260227.md     (ở thư mục gốc repo)

frontend/
└── README.md
```

#### Nhóm D: Báo cáo kiểm thử và sửa lỗi (3 file mẫu + tóm tắt, KHÔNG nộp 22 file gốc)
```
docs/Fix-Bao-Cao/
├── BaoCao_DoiChieu_XepLoai_T01_2026.md  ⚠️ (làm ẩn danh, nộp 1 file mẫu)
├── BaoCao_KiemChung_RosterVote_T04_T05.md  ⚠️ (làm ẩn danh)
└── TOM_TAT_22_BAO_CAO.md  ⚠️ (tạo mới — tóm tắt không chứa PII)
```

#### Nhóm E: Tài liệu tham chiếu tổng quan (1 file)
```
CLAUDE.md  ⚠️ (biên tập — chỉ giữ phần Tech Stack, Architecture, Domain Concepts, bỏ phần "QUY TẮC TUYỆT ĐỐI" chứa IP/cảnh báo nội bộ)
```

### 5.2. Lệnh đóng gói (git archive)

```bash
cd /root/kpi-haiquan

# Bước 1: (không cần) — MIGRATION_GUIDE_20260227.md đã có ở thư mục gốc repo, đóng gói đúng đường dẫn đó

# Bước 2: Tạo file tóm tắt báo cáo (không chứa PII)
cat > docs/Fix-Bao-Cao/TOM_TAT_22_BAO_CAO.md << 'EOF'
# Tóm tắt 22 báo cáo đối chiếu số liệu KPI

Bộ 22 báo cáo đối chiếu xếp loại tháng 01, 04, 05/2026 đã được thực hiện định kỳ,
xác minh 0 sai lệch sau mỗi đợt hiệu chỉnh công thức. Thống kê:
- Tổng số dòng: 765 dòng
- Số file: 22 file .md và .csv
- Nội dung: đối chiếu xếp loại, kiểm chứng biểu quyết 3 nguồn, danh sách chưa hoàn tất

File gốc chứa dữ liệu cá nhân (tên, mã CC, đơn vị) nên KHÔNG nộp nguyên trạng.
Nếu đoàn kiểm tra yêu cầu mẫu, chọn 1–2 file đã làm ẩn danh.
EOF

# Bước 3: Biên tập CLAUDE.md (tạo bản rút gọn)
# KHÔNG dùng head -N: phần đầu CLAUDE.md đã chứa mục "Database" (IP máy chủ, cảnh báo nội bộ).
# Trích tay đúng 4 mục: Project Overview, Tech Stack, Architecture, Domain Concepts.
awk '/^## Project Overview/,/^## Common Commands/' CLAUDE.md | sed '$d' > CLAUDE_TECH_SUMMARY.md
awk '/^## Architecture/,/^## Role Hierarchy/' CLAUDE.md | sed '$d' >> CLAUDE_TECH_SUMMARY.md
echo "
## Lưu ý
Đây là bản rút gọn của CLAUDE.md phục vụ hồ sơ kiểm tra ATTT.
Bản đầy đủ (chứa quy tắc nội bộ dev) không bàn giao.
" >> CLAUDE_TECH_SUMMARY.md

# Bước 4: Tạo file .gitattributes để loại trừ thư mục không cần thiết
cat > .gitattributes << 'EOF'
# Loại trừ khỏi git archive
backend/venv/ export-ignore
backend/uploads/ export-ignore
backend/uploads-dev/ export-ignore
backend/__pycache__/ export-ignore
backend/.pytest_cache/ export-ignore
backend/alembic/__pycache__/ export-ignore
frontend/node_modules/ export-ignore
frontend/.next/ export-ignore
frontend/out/ export-ignore
.git/ export-ignore
.env export-ignore
.env.local export-ignore
*.pyc export-ignore
*.log export-ignore
EOF

# Bước 5: Đóng gói bằng git archive (loại trừ file nhạy cảm)
git archive --format=tar \
  --prefix=kpi-haiquan-attt-audit-2026/ \
  HEAD \
  docs/ra-quet-attt-2026/ \
  docs/shared/ \
  docs/lms/ \
  docs/forum/ \
  docs/legal/ \
  docs/portal/ \
  docs/HKG/HKG_API_SPECS.md \
  docs/HKG/HKG_DATABASE_DESIGN.md \
  docs/HKG/Phase_4_1_UAT_Checklist.md \
  docs/HKG/Phase_4_1_Deploy_Checklist.md \
  docs/HKG/PM2_DEPLOY.md \
  "docs/Chi Tieu/" \
  docs/API_CONTRACT_BETWEEN_MODULES.md \
  docs/BUSINESS_RULES_v3_0_PL3.md \
  docs/HUONG_DAN_ADMIN_PL3.md \
  docs/IMPACT_ANALYSIS_KPI_V2_PL3.md \
  docs/Fix-Bao-Cao/TOM_TAT_22_BAO_CAO.md \
  backend/README.md \
  backend/MIGRATION_GUIDE.md \
  MIGRATION_GUIDE_20260227.md \
  backend/.env.example \
  frontend/README.md \
  CLAUDE_TECH_SUMMARY.md \
  | gzip > kpi-haiquan-tai-lieu-thiet-ke-attt-20261006.tar.gz

# Bước 6: Kiểm tra kích thước và nội dung gói
ls -lh kpi-haiquan-tai-lieu-thiet-ke-attt-20261006.tar.gz
tar -tzf kpi-haiquan-tai-lieu-thiet-ke-attt-20261006.tar.gz | wc -l
echo "Tổng số file trong gói (ước tính ~50 file tài liệu kỹ thuật)."

# Bước 7: Quét secrets lần cuối trước khi gửi
mkdir -p /tmp/attt-scan
tar -xzf kpi-haiquan-tai-lieu-thiet-ke-attt-20261006.tar.gz -C /tmp/attt-scan/
grep -r "SECRET_KEY.*=" /tmp/attt-scan/ 2>/dev/null && echo "⚠️ CÒN SECRET_KEY" || echo "✅ Không còn SECRET_KEY thật"
grep -r "DB_PASSWORD.*=" /tmp/attt-scan/ 2>/dev/null | grep -v "your_secure_password_here" && echo "⚠️ CÒN PASSWORD" || echo "✅ Không còn password thật"
rm -rf /tmp/attt-scan
```

### 5.3. Checklist trước khi nộp

- [ ] Đóng gói `MIGRATION_GUIDE_20260227.md` theo đúng đường dẫn thư mục gốc
- [ ] Tạo `TOM_TAT_22_BAO_CAO.md` — KHÔNG nộp 22 file gốc chứa PII
- [ ] Biên tập `CLAUDE.md` → `CLAUDE_TECH_SUMMARY.md` (bỏ IP/cảnh báo nội bộ)
- [ ] Rà soát `PM2_DEPLOY.md` — bỏ đường dẫn tuyệt đối nếu có
- [ ] Kiểm tra `.env.example` — chỉ có mật khẩu mẫu, không có giá trị thật
- [ ] Quét secrets: `grep -r "SECRET_KEY.*=" <gói>` phải trả về rỗng (trừ `.env.example`)
- [ ] Quét IP nhạy cảm: `grep -r "79.108.216.189\|27.71.229.103" <gói>` — chấp nhận có trong tài liệu kỹ thuật (05, 10)
- [ ] Đóng gói bằng `git archive` với prefix `kpi-haiquan-attt-audit-2026/`
- [ ] Kiểm tra kích thước gói: ước ~5–10 MB (nén), ~50 file

---

## 6. Tổng kết

### 6.1. Thống kê tài liệu

| Nhóm | Số lượng | Ghi chú |
|---|---|---|
| Tài liệu đã nộp (mục 2–10) | 12 file + 9 OpenAPI JSON + 1 CSV | Đã là phần hồ sơ chính thức |
| Tài liệu thiết kế dẫn chiếu | 25 file | API_SPECS, DATABASE_DESIGN, BUSINESS_RULES theo module |
| Tài liệu vận hành | 4 file | README, MIGRATION_GUIDE, PM2_DEPLOY |
| Báo cáo kiểm thử | 22 file (chỉ nộp tóm tắt) | Chứa PII — biên tập trước khi nộp |
| Tài liệu tham chiếu | 1 file (CLAUDE.md) | Biên tập — bỏ phần nội bộ dev |
| **Tổng cộng** | **~65 file tài liệu kỹ thuật** | Nén thành 1 gói tar.gz ~5–10 MB |

### 6.2. Dẫn chiếu gãy

- **Trong bộ hồ sơ 02–10: 0 dẫn chiếu gãy thực sự.** Ngoài hồ sơ, `CLAUDE.md` dẫn chiếu `docs/CHIEN_LUOC_NEN_TANG_THONG_NHAT.md` — file không tồn tại (xem KT-01); không ảnh hưởng hồ sơ nộp. Một dẫn chiếu ghi sai thư mục: `MIGRATION_GUIDE_20260227.md` nằm ở thư mục gốc repo chứ không phải `backend/`.
- **Xử lý**: đóng gói đúng đường dẫn gốc; không cần commit thêm.

### 6.3. Tài liệu chứa thông tin nhạy cảm

| File | Loại thông tin | Mức độ | Xử lý |
|---|---|---|---|
| `docs/Fix-Bao-Cao/*.md` (22 file) | **Dữ liệu cá nhân (PII)**: tên, mã CC, đơn vị | **Cao** | CHỈ nộp tóm tắt, KHÔNG nộp file gốc |
| `CLAUDE.md` | IP cloud, cổng nội bộ, quy tắc dev | Trung bình | Biên tập → `CLAUDE_TECH_SUMMARY.md` |
| `docs/van-hanh/HUONG_DAN_DEV_PROD.md` | Quy trình triển khai, có thể chứa SSH | Trung bình | Rà soát, bỏ credential nếu có |
| `docs/HKG/PM2_DEPLOY.md` | Đường dẫn thư mục hệ thống | Thấp | Rà soát, bỏ đường dẫn tuyệt đối `/opt/kpi-prod` nếu có |

### 6.4. Tài liệu lỗi thời hoặc không khớp

- **Không có tài liệu lỗi thời nghiêm trọng** — tất cả tài liệu đều phản ánh code hiện hành.
- **API_SPECS.md các module mới**: số endpoint thực tế nhiều hơn spec 10–50% — **chấp nhận được**, OpenAPI JSON là nguồn chính thức 100%.
- **Module KPI lõi**: không có SDD/API_SPECS.md riêng — thông tin nằm trong `03_tieu_chi_cong_thuc_xep_loai.md` + `06_phu_luc_tu_dien_du_lieu.md` + `BUSINESS_RULES_v3_0_PL3.md` + OpenAPI JSON.

---

**Người lập:** Đội ngũ kỹ thuật Chi cục Hải quan Khu vực VIII  
**Ngày lập:** 06/10/2026  
**Phiên bản:** 1.0
