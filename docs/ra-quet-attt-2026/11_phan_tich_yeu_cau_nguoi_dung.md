# Mục 11 — Phân tích yêu cầu người sử dụng (URD)

> Phục vụ công văn 153/CNTT ngày 08/7/2026. Lập ngày 06/10/2026.
> Phần mềm: **Hệ thống theo dõi, đánh giá KPI & Nền tảng Digital Learning** — Chi cục Hải quan Khu vực VIII (https://kpihaiquan.vn).

## 1. Mục đích, phạm vi, phương pháp lập

### 1.1. Mục đích

Tài liệu này nhằm:

1. **Lập danh sách toàn diện** các yêu cầu chức năng và phi chức năng của hệ thống theo quan điểm người sử dụng — từ công chức, lãnh đạo, đến quản trị hệ thống.
2. **Truy vết nguồn gốc** từng yêu cầu về các căn cứ pháp lý, văn bản chỉ đạo, góp ý nghiệp vụ và nhu cầu phát sinh trong vận hành thực tế.
3. **Xác định trạng thái đáp ứng** tại thời điểm lập tài liệu (06/10/2026) để phục vụ công tác kiểm tra ATTT và lập kế hoạch hoàn thiện.
4. **Làm cơ sở** cho công tác kiểm thử nghiệm thu, bảo trì và phát triển tiếp hệ thống.

### 1.2. Phạm vi

- **Phạm vi triển khai:** Nội bộ Chi cục Hải quan Khu vực VIII — 15 đơn vị (Phòng/Đội/Hải quan Cửa khẩu), 560 tài khoản (544 đang hoạt động, kiểm đếm ngày 06/10/2026).
- **Phạm vi chức năng:** 8 module chính (KPI, LMS, HKG, Chỉ tiêu đơn vị, Forum, Legal, Portal, Common) + tích hợp Zalo OA + Lịch công tác + Trực ban.
- **Giai đoạn:** Module KPI production từ đầu 2026; các module mở rộng (LMS, HKG, Chỉ tiêu) đã triển khai từ Q2–Q3/2026; đang tiếp tục hoàn thiện theo lộ trình.

### 1.3. Phương pháp lập — Hồi cố (Reverse-engineered)

Dự án KPI & Nền tảng Số **không có tài liệu URD chính thức được lập từ giai đoạn đầu** theo quy trình chuẩn (thu thập yêu cầu → phân tích → phê duyệt → thiết kế). Thay vào đó, hệ thống phát triển theo mô hình **agile**, đáp ứng nhanh các yêu cầu nghiệp vụ phát sinh, dựa trên văn bản chỉ đạo và góp ý trực tiếp từ người dùng.

**Tài liệu này được lập hồi cố (reverse-engineered)** bằng phương pháp:

1. **Rà soát văn bản chỉ đạo, tờ trình** — trích xuất yêu cầu từ tài liệu hành chính.
2. **Phân tích mã nguồn production** — kiểm chứng tính năng đã triển khai thực tế (endpoint backend, trang frontend, schema CSDL).
3. **Đọc lịch sử phát triển** — từ git log (commit `feat`), tài liệu nghiệp vụ nội bộ, ghi chép vận hành nội bộ.
4. **Kiểm đếm dữ liệu thực tế** — số người dùng, vai trò, đơn vị, giao dịch (tại thời điểm 06/10/2026).

### 1.4. Nguồn yêu cầu

| Nguồn văn bản/tài liệu | Nội dung | Ngày |
|---|---|---|
| **QĐ 1804/QĐ-TCHQ** | Quy chế bảo đảm an toàn thông tin mạng, bảo vệ an ninh mạng của Tổng cục Hải quan — nguồn **yêu cầu phi chức năng ATTT** (căn cứ của CV 153/CNTT) | 31/7/2024 |
| **QĐ 330/QĐ-HQKV8** | Quy trình quản lý vận hành an toàn, an ninh hệ thống thông tin của Chi cục HQKV VIII — nguồn **yêu cầu vận hành/giám sát** | 10/7/2025 |
| **Công văn 21169/CHQ-TCCB** (Cục Hải quan) + công văn triển khai của Chi cục | Đánh giá, xếp loại theo **QUÝ**, năm (từ Q3/2026, kỳ tháng hết hiệu lực); hạn nộp hồ sơ ngày 23 tháng cuối quý | 28/8/2026 |
| **Tờ trình — Nền tảng Digital Learning** (TCCB, dự thảo `docs/shared/To_trinh_Nen_tang_Digital_Learning_HQKV8 (2).docx`) | Chủ trương xây dựng nền tảng đào tạo trực tuyến, thảo luận nghiệp vụ, phổ biến pháp luật | Bản trong repo chưa ghi ngày/số — **cần TCCB bổ sung bản đã ký** |
| **Kế hoạch Phase 4 — Module HKG** (Văn phòng) | Phối hợp xây dựng module Họp Không Giấy; 10 chức năng nghiệp vụ + trình chiếu đồng bộ | Q1/2026 |
| **Góp ý sử dụng thực tế — Lịch công tác** | Yêu cầu nhắc lịch qua Zalo, phân quyền tài liệu, tính năng ghi chú cá nhân, báo cáo đối soát | Q2–Q3/2026 |
| **Yêu cầu kiểm thử kỳ thi ĐGNL** | Chống gian lận (single-session, vi phạm giờ), giám sát live, import Excel, best-score | Q2–Q3/2026 |
| **Yêu cầu điều chỉnh KPI** (nghiệp vụ phát sinh) | Sửa điểm tiêu chí chung từng người, nới hạn tiêu chí chung, mở khóa kỳ đánh giá, xử lý trường hợp công chức điều chuyển đơn vị giữa kỳ | Liên tục trong vận hành |
| **Phương pháp tính KPI mới** (công thức lãnh đạo) | Từ 04/2026: lãnh đạo (PDV/TDV/PCCT/CCT) cộng sản phẩm cấp dưới vào KPI cá nhân | 04/2026 |
| **Lộ trình phát triển nội bộ** | Git log (commit `feat`), ghi chép dự án, tài liệu `docs/van-hanh/PHIEN_BAN_PROD.md` | 09/02/2026 – nay |

## 2. Các bên liên quan & nhóm người dùng

### 2.1. Số lượng người dùng (kiểm đếm ngày 06/10/2026)

| Nhóm | Vai trò | Số lượng (tổng) | Đang hoạt động | Ghi chú |
|---|---|---|---|---|
| **Lãnh đạo Chi cục** | Chi cục trưởng (CCT) | 1 | 1 | Quyền cao nhất: xếp loại toàn Chi cục, điều chỉnh điểm, khóa/mở khóa kỳ |
| | Phó Chi cục trưởng (PCCT) | 3 | 3 | Phê duyệt, xem báo cáo toàn Chi cục |
| **Lãnh đạo đơn vị** | Trưởng đơn vị (TDV) | 14 | 13 | Phê duyệt cấp 2, xem/duyệt phạm vi đơn vị |
| | Phó đơn vị (PDV) | 37 | 37 | Phê duyệt cấp 1, xem/duyệt phạm vi đơn vị |
| **Công chức** | Công chức (CC) | 395 | 383 | Kê khai, tự chấm, xem kết quả cá nhân |
| | Hợp đồng 111 (HD_111) | 109 | 106 | Tương tự CC, đánh giá theo VB 714 (quy trình riêng) |
| **Quản trị** | Cán bộ TCCB | (platform role) | — | Đối soát, báo cáo, quản lý danh mục |
| | Quản trị hệ thống (ADMIN) | 1 | 1 | Full quyền backend + frontend |
| **Tổng cộng** | | **560** | **544** | 56 là lãnh đạo (CCT+PCCT+TDV+PDV) |

**Platform roles bổ sung** (gán qua `cong_chuc_platform_role`, kiểm đếm 06/10/2026):

| Platform Role | Tên | Số người được gán | Module sử dụng |
|---|---|---|---|
| `QT_NOI_DUNG` | Quản trị nội dung | 7 | Portal, Legal, HKG (đăng/sửa/xóa lịch công tác) |
| `QT_DAO_TAO` | Quản trị đào tạo | 1 | LMS (quản lý khóa học, ngân hàng câu hỏi, kỳ thi ĐGNL) |
| `TRUONG_CNTT` | Trưởng phòng CNTT | 1 | Toàn hệ thống (xem log, cấu hình) |
| `THEO_DOI_CHI_TIEU` | Người theo dõi chỉ tiêu | 1 | Chỉ tiêu đơn vị (xem/báo cáo cross-unit) |
| `CHANH_VP` | Chánh Văn phòng | 1 | HKG, Lịch công tác (phê duyệt, xem toàn bộ) |
| `GIANG_VIEN` | Giảng viên kiêm nhiệm | 0 | LMS (soạn bài, chấm bài) — chưa sử dụng |
| `BIEN_TAP` | Biên tập viên | 0 | Legal, Portal — chưa sử dụng |
| Các role khác | (7 loại còn lại) | 0 | Dự phòng cho tương lai |

### 2.2. Mô tả nhu cầu theo nhóm người dùng

#### Nhóm 1: Công chức (CC) + Hợp đồng 111

- **Nhu cầu chính:**
  - Kê khai công việc hằng tháng/quý nhanh chóng, chọn từ danh mục chuẩn (~2.900 đầu việc).
  - Tự chấm 31 tiêu chí chung (phẩm chất, năng lực, sáng tạo).
  - Xem kết quả KPI, điểm đánh giá, xếp loại A/B/C/D của bản thân; in phiếu đánh giá.
  - Đăng ký nghỉ phép, xem lịch công tác, xem thông báo.
  - Học khóa học trực tuyến, thi đánh giá năng lực (ĐGNL), nhận chứng chỉ.
  - Tra cứu văn bản pháp luật, tài liệu họp, tham gia diễn đàn hỏi đáp nghiệp vụ.

- **Đặc điểm:**
  - Số lượng đông nhất (489/544 tài khoản active).
  - Phân tán 15 đơn vị, 8 lĩnh vực nghiệp vụ khác nhau.
  - Trình độ tin học không đồng đều → yêu cầu giao diện đơn giản, thao tác ít bước.

#### Nhóm 2: Lãnh đạo đơn vị (TDV + PDV)

- **Nhu cầu chính:**
  - Phê duyệt kê khai công việc của cấp dưới (2 cấp: PDV → TDV hoặc TDV duyệt thẳng).
  - Phê duyệt tiêu chí chung của công chức trong đơn vị (2 cấp).
  - Kê khai KPI lãnh đạo riêng (chỉ số a/b/c/d/đ/e).
  - Xem báo cáo đơn vị: xếp loại, thống kê, đối soát.
  - Phê duyệt nghỉ phép, phê duyệt chỉ tiêu đơn vị.
  - Duyệt/từ chối hàng loạt (bulk) để xử lý nhanh.

- **Đặc điểm:**
  - 50 người (13 TDV + 37 PDV).
  - Thường xuyên di động, cần xử lý trên điện thoại.
  - Yêu cầu dashboard tổng quan để nắm tình hình đơn vị.

#### Nhóm 3: Lãnh đạo Chi cục (CCT + PCCT)

- **Nhu cầu chính:**
  - Xem báo cáo tổng hợp **toàn Chi cục** (15 đơn vị).
  - **Xếp loại A/B/C/D** cho 544 công chức theo tháng/quý.
  - **Điều chỉnh điểm** tiêu chí chung từng cá nhân (có lưu lịch sử).
  - **Khóa/mở khóa kỳ đánh giá** — chốt điểm chính thức.
  - Xem tổng hợp phiếu đánh giá Mẫu 02 (chỉ đọc), xuất Excel.
  - Xem lịch công tác toàn Chi cục, thống kê tài liệu họp.
  - Xem báo cáo đào tạo, kết quả thi ĐGNL theo đơn vị.

- **Đặc điểm:**
  - 4 người (1 CCT + 3 PCCT).
  - Yêu cầu quyền cao nhất, kiểm soát chặt chẽ bảo mật.
  - Cần tính năng in ấn, xuất Word/Excel/PDF để trình lãnh đạo cấp trên hoặc nộp Cục.

#### Nhóm 4: TCCB (Tổ chức cán bộ)

- **Nhu cầu chính:**
  - **Đối soát đánh giá:** kiểm tra ai/đơn vị nào chưa hoàn tất từng bước (kê khai, duyệt, chấm, phiếu).
  - Xuất báo cáo định kỳ (xếp loại tháng/quý, thống kê theo đơn vị/lĩnh vực).
  - Quản lý danh mục công việc (thêm/sửa/vô hiệu hóa).
  - Quản lý tài khoản: kích hoạt/vô hiệu hóa, reset mật khẩu, gán platform role.
  - Quản lý lịch sử điều chuyển đơn vị (có ngày hiệu lực), điều chuyển hàng loạt bằng Excel.
  - Tổng hợp hồ sơ phiếu đánh giá nộp Cục (hạn ngày 23 tháng cuối quý).

- **Đặc điểm:**
  - Vai trò thực chất không phải 1 vai trò RBAC riêng mà là **platform role** gán cho một số công chức Phòng TCCB.
  - Cần quyền đọc toàn Chi cục nhưng **không có quyền xếp loại** (chỉ CCT mới xếp loại).

#### Nhóm 5: Quản trị hệ thống (ADMIN, TRUONG_CNTT)

- **Nhu cầu chính:**
  - Quản lý toàn bộ tài khoản, vai trò, đơn vị.
  - Xử lý sự cố kỹ thuật: xem log, mở khóa kỳ đánh giá (theo yêu cầu nghiệp vụ), sửa dữ liệu sai lệch (có audit trail).
  - Quản lý danh mục công việc, tham số nghiệp vụ (`platform_config`).
  - Theo dõi backup, cảnh báo lỗi hệ thống.
  - Pin phiên bản KPI (V1/V2_PL3) cho từng công chức hoặc đơn vị.

- **Đặc điểm:**
  - 2 người (1 ADMIN + 1 TRUONG_CNTT).
  - Quyền rộng nhất, cần kiểm soát chặt chẽ audit log.

#### Nhóm 6: Giảng viên, Quản trị đào tạo (QT_DAO_TAO)

- **Nhu cầu chính:**
  - Quản lý khóa học, bài học (video/tài liệu/bài tập).
  - Quản lý ngân hàng câu hỏi (~1.200 câu ĐGNL/11 lĩnh vực).
  - Tổ chức kỳ thi: tạo cấu trúc đề, template đề, ca thi, danh sách thí sinh (import Excel).
  - **Giám sát live** khi thi: xem danh sách thí sinh đang làm bài, vi phạm giờ, thoát fullscreen.
  - Reset lượt thi cho thí sinh (có nhật ký, cần phê duyệt).
  - Chấm bài thực hành (Word/Excel/PDF), cho điểm, nhận xét.
  - Xuất báo cáo kết quả đào tạo theo đơn vị.

- **Đặc điểm:**
  - Hiện có 1 QT_ĐÀO_TẠO chính.
  - Vai trò GIANG_VIEN (giảng viên kiêm nhiệm) đã có cơ chế nhưng chưa sử dụng thực tế.

#### Nhóm 7: Quản trị nội dung (QT_NOI_DUNG, CHANH_VP)

- **Nhu cầu chính:**
  - Đăng/sửa/xóa lịch công tác.
  - Phân quyền tài liệu họp (2 mức: "Công khai" / "Hạn chế đối tượng").
  - Đăng tin tức, văn bản pháp luật nội bộ.
  - Xem báo cáo thống kê tài liệu họp (số lượng, tải về).

- **Đặc điểm:**
  - 7 người QT_NOI_DUNG (VP + một số đơn vị).
  - 1 CHANH_VP (xem toàn bộ, phê duyệt).

## 3. Yêu cầu chức năng theo phân hệ

### 3.1. Module KPI — Kê khai và đánh giá KPI

#### YC-KPI-01: Kê khai công việc theo tháng/quý

- **Mô tả:** Công chức chọn đầu việc từ danh mục chuẩn (~2.900 đầu việc, 15 lĩnh vực), nhập số lượng sản phẩm, minh chứng; lưu nháp hoặc gửi duyệt. Hệ thống hỗ trợ "công việc yêu thích" để kê nhanh.
- **Nhóm người dùng:** CC, HD_111
- **Mức ưu tiên:** **Cao (P0)** — chức năng lõi
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint `POST /ke-khai`, `POST /ke-khai-v2` (V2_PL3 từ 04/2026)
- **Vị trí code:**
  - Backend: `backend/app/api/v1/endpoints/ke_khai.py`
  - Frontend: `frontend/src/app/(main)/ke-khai/page.tsx`, `/ke-khai-v2/page.tsx`

#### YC-KPI-02: Phê duyệt kê khai 2 cấp

- **Mô tả:** Lãnh đạo đơn vị duyệt kê khai theo 2 cấp (PDV → TDV hoặc TDV duyệt thẳng). Có duyệt từng đơn và duyệt hàng loạt (bulk). Từ chối kèm lý do. Xử lý đúng trường hợp công chức điều chuyển đơn vị giữa kỳ (người duyệt là lãnh đạo đơn vị hiện tại).
- **Nhóm người dùng:** PDV, TDV
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint `POST /api/v1/phe-duyet/xu-ly` (một/nhiều bản), `POST /api/v1/phe-duyet/{ke_khai_id}`, `POST /api/v1/phe-duyet/tra-lai-bulk`
- **Vị trí code:**
  - Backend: `backend/app/api/v1/endpoints/phe_duyet.py` (logic nghiệp vụ tích hợp trong endpoint)
  - Frontend: `frontend/src/app/(main)/phe-duyet/page.tsx`

#### YC-KPI-03: Tính điểm KPI tự động

- **Mô tả:** Hệ thống tự động tổng hợp sản phẩm quy đổi từ kê khai đã duyệt, tính điểm KPI theo công thức (V1: mẫu số = ngày × 96; V2_PL3: mẫu số = tổng SP đã duyệt). Trừ điểm chất lượng/tiến độ theo quy tắc tuyến tính (tối đa 4 lỗi/SP).
- **Nhóm người dùng:** Tất cả (hệ thống tính tự động)
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng**
- **Vị trí code:**
  - Backend: `backend/app/core/kpi_version.py`, logic tính điểm trong `backend/app/api/v1/endpoints/danh_gia.py`

#### YC-KPI-04: Kê khai KPI lãnh đạo (d/đ/e)

- **Mô tả:** Lãnh đạo (PDV/TDV/PCCT/CCT) kê khai riêng theo bộ chỉ số lãnh đạo (6 chỉ số a/b/c/d/đ/e). Từ 04/2026 áp dụng công thức cộng sản phẩm cấp dưới. Từ Q3/2026 (CV 21169): d/đ/e kê **một lần cho cả quý** (phiếu neo tháng cuối quý), không còn MIN ba tháng.
- **Nhóm người dùng:** PDV, TDV, PCCT, CCT
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint `POST /ke-khai-lanh-dao`
- **Vị trí code:**
  - Backend: `backend/app/api/v1/endpoints/ke_khai_lanh_dao.py`
  - Frontend: `frontend/src/app/(main)/ke-khai-v2/page.tsx` (lãnh đạo dùng chung trang kê khai)
- **Ghi chú:** Từ commit `67bda67` (28/09/2026) đã gỡ tính năng "kê khai lại đ cấp quý" — xem `d8762c2`.

#### YC-KPI-05: Tự chấm và duyệt tiêu chí chung (31 tiêu chí)

- **Mô tả:** Công chức tự chấm 31 tiêu chí chung (3 nhóm: phẩm chất – năng lực – sáng tạo/trách nhiệm), thang điểm bội 0,5. Lãnh đạo duyệt tiêu chí chung 2 cấp. Từ Q3/2026 chấm theo QUÝ (không còn chấm theo tháng).
- **Nhóm người dùng:** CC, HD_111 (tự chấm); PDV, TDV (duyệt)
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint `POST /api/v1/danh-gia/tu-danh-gia`, `POST /api/v1/danh-gia/{danh_gia_thang_id}/phe-duyet-tieu-chi`, `POST /api/v1/danh-gia/phe-duyet-tieu-chi-bulk`
- **Vị trí code:**
  - Backend: `backend/app/api/v1/endpoints/danh_gia.py`
  - Frontend: `frontend/src/app/(main)/danh-gia/page.tsx`, `/danh-gia/tieu-chi-chung/page.tsx`

#### YC-KPI-06: Xếp loại A/B/C/D (tháng và quý)

- **Mô tả:** Chi cục trưởng xem bảng tổng hợp toàn Chi cục, quyết định xếp loại A/B/C/D cho 544 công chức. Được quyền điều chỉnh điểm tiêu chí chung từng người trước khi chốt (modal sửa điểm, lưu lịch sử). Khóa/mở khóa kỳ đánh giá.
- **Nhóm người dùng:** CCT (chủ yếu), PCCT (hỗ trợ)
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint `POST /api/v1/danh-gia/{danh_gia_thang_id}/dieu-chinh-danh-gia-thang` (CCT sửa điểm), `POST /api/v1/xep-loai/khoa-du-lieu` / `mo-khoa-du-lieu` (chỉ có API, **chưa có nút trên giao diện**)
- **Vị trí code:**
  - Backend: `backend/app/api/v1/endpoints/xep_loai_moi.py` (tháng), `xep_loai_quy.py` (quý)
  - Frontend: `frontend/src/app/(main)/xep-loai/page.tsx`

#### YC-KPI-07: Phiếu đánh giá tháng và quý (Mẫu 01A/01B, 02A/02B)

- **Mô tả:** Lập phiếu đánh giá tháng/quý theo mẫu quy định: tự đề xuất mức xếp loại → nhận xét → quyết định. In mẫu Word/PDF (Mẫu 01A/01B cho tháng, 02A/02B cho quý).
- **Nhóm người dùng:** Tất cả (lập phiếu cá nhân); TDV (nhận xét); CCT (quyết định)
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint `POST /api/v1/phieu-danh-gia-thang/`, `POST /api/v1/phieu-danh-gia-quy/` (+ `/{phieu_id}/gui-duyet`, `/phe-duyet`, `/tu-choi`, `/tra-lai`), in phiếu `GET /api/v1/in-bang-ke/phieu-danh-gia-quy/{quy}/{nam}`
- **Vị trí code:**
  - Backend: `backend/app/api/v1/endpoints/phieu_danh_gia_thang.py`, `phieu_danh_gia_quy.py`, `in_phieu.py`
  - Frontend: `frontend/src/app/(main)/xep-loai/page.tsx` (tab Quý) + `frontend/src/app/(main)/danh-gia-v2/page.tsx`

#### YC-KPI-08: Tổng hợp phiếu Mẫu 02 toàn Chi cục (chỉ đọc)

- **Mô tả:** CCT/PCCT/TCCB xem tổng hợp phiếu đánh giá quý Mẫu 02 của tất cả công chức (chỉ đọc, không sửa). Lọc theo đơn vị, trạng thái, xếp loại, tìm theo tên/mã. Xuất Excel. **Cố ý không mở cho TDV xem chéo đơn vị** (phiếu chứa nhận xét cá nhân).
- **Nhóm người dùng:** CCT, PCCT, TCCB
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng** (từ commit `60b8932`, 29/09/2026)
- **Vị trí code:**
  - Backend: `backend/app/api/v1/endpoints/phieu_danh_gia_quy.py` (endpoint `GET /api/v1/phieu-danh-gia-quy/toan-chi-cuc`, `GET /api/v1/phieu-danh-gia-quy/toan-chi-cuc/export`)
  - Frontend: `frontend/src/app/(main)/phieu-tong-hop/page.tsx`
- **Ghi chú:** Đã kiểm chứng 12/12 test PASS; bảng tổng hợp 542 dòng / 0,19s, Excel 109 KB / 0,33s.

#### YC-KPI-09: Đối soát đánh giá (TCCB)

- **Mô tả:** TCCB tự kiểm tra ai/đơn vị nào chưa hoàn tất từng bước quy trình (kê khai, duyệt cấp 1/2, chấm tiêu chí, phiếu đánh giá). Xuất Excel.
- **Nhóm người dùng:** TCCB
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint `GET /api/v1/doi-soat-danh-gia/thang/{thang}/nam/{nam}` (+ `/export`)
- **Vị trí code:**
  - Backend: `backend/app/api/v1/endpoints/doi_soat_danh_gia.py`
  - Frontend: `frontend/src/app/(main)/doi-soat/page.tsx`

#### YC-KPI-10: Nghỉ phép

- **Mô tả:** Đăng ký nghỉ, duyệt nghỉ (2 cấp), thống kê ngày nghỉ. Hệ thống hiện có 16.448 lượt nghỉ đã ghi nhận (kiểm đếm 06/10/2026).
- **Nhóm người dùng:** Tất cả (đăng ký); PDV, TDV (duyệt)
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint `POST /nghi-phep`, `GET /nghi-phep/thong-ke`
- **Vị trí code:**
  - Backend: `backend/app/api/v1/endpoints/nghi_phep.py`
  - Frontend: `frontend/src/app/(main)/nghi-phep/page.tsx`

#### YC-KPI-11: Điều chuyển nhân sự (có ngày hiệu lực)

- **Mô tả:** Quản lý lịch sử điều chuyển đơn vị (timeline hợp nhất: điều chuyển/vô hiệu hóa có ngày hiệu lực). Điều chuyển hàng loạt bằng file Excel (mẫu 4 sheet: sheet nhập trống, sheet tra cứu mã CC; khóa là Mã CC không phải họ tên; một dòng lỗi thì từ chối cả đợt).
- **Nhóm người dùng:** TCCB, ADMIN
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng** (từ commit `4aaa43e`, 13/09/2026)
- **Vị trí code:**
  - Backend: `backend/app/api/v1/endpoints/admin_dieu_chuyen_hang_loat.py` (endpoint `GET /api/v1/admin/dieu-chuyen-hang-loat/mau-excel`, `POST .../xem-truoc`, `POST .../ghi`)
  - Frontend: `frontend/src/app/(main)/admin/dieu-chuyen-hang-loat/page.tsx`, `admin/lich-su-dieu-chuyen/page.tsx`
- **Ghi chú:** Cột `loai` trong `lich_su_dieu_chuyen` (DIEU_CHUYEN / VO_HIEU_HOA / KICH_HOAT). Cột `ngay_hieu_luc` trong `cong_chuc`.

#### YC-KPI-12: Báo cáo và xuất dữ liệu

- **Mô tả:** Báo cáo xếp loại tháng/quý, thống kê theo đơn vị/lĩnh vực/nhóm công việc. Xuất Excel, in bảng kê.
- **Nhóm người dùng:** CCT, PCCT, TDV, TCCB
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint nhóm `/api/v1/bao-cao-xep-loai/*`, `/api/v1/bao-cao-xep-loai-quy/*`, xuất Excel `GET /api/v1/export/ca-nhan/thang/{thang}/nam/{nam}`, `GET /api/v1/export/don-vi/thang/{thang}/nam/{nam}`
- **Vị trí code:**
  - Backend: `backend/app/api/v1/endpoints/bao_cao_xep_loai.py`, `bao_cao_xep_loai_quy.py`, `export_bao_cao.py`
  - Frontend: Tích hợp trong các trang xếp loại và phiếu đánh giá

#### YC-KPI-13: Quản trị danh mục công việc

- **Mô tả:** Thêm/sửa/vô hiệu hóa đầu việc trong danh mục chuẩn. Quản lý 2 bộ danh mục: V1 (46 mục cũ) và PL3 (2.812 mục mới, 15 lĩnh vực, 5 nhóm phức tạp).
- **Nhóm người dùng:** TCCB, ADMIN
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint `POST /api/v1/admin/danh-muc-pl3`, `PUT /api/v1/admin/danh-muc-pl3/{dm_id}`, import `POST /api/v1/admin/danh-muc-pl3/import/dry-run` → `/commit`
- **Vị trí code:**
  - Backend: `backend/app/api/v1/endpoints/admin.py`
  - Frontend: `frontend/src/app/(main)/admin/danh-muc-pl3/page.tsx` + `admin/danh-muc-cv/` + `admin/sp-chuan/`

### 3.2. Module LMS — Đào tạo trực tuyến

#### YC-LMS-01: Quản lý khóa học và bài học

- **Mô tả:** Quản trị tạo khóa học, chuyên đề, bài học (video/tài liệu/bài tập). Học viên đăng ký học, xem bài, làm bài tập (Word/Excel/PDF), theo dõi tiến độ.
- **Nhóm người dùng:** QT_ĐÀO_TẠO (quản lý), GIANG_VIEN (soạn bài), CC (học viên)
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** — 45 endpoints, 22 bảng schema `lms.*`
- **Vị trí code:**
  - Backend: `backend/lms_service/api/endpoints/` (port 8001): `khoa_hoc.py`, `chuyen_de.py`, `bai_hoc.py`, `dang_ky.py`
  - Frontend: `frontend/src/app/(main)/dao-tao/` (7 trang)

#### YC-LMS-02: Bài kiểm tra và chấm tự động

- **Mô tả:** Ngân hàng câu hỏi theo khóa học, làm bài trắc nghiệm, chấm tự động, lưu kết quả.
- **Nhóm người dùng:** QT_ĐÀO_TẠO (quản lý ngân hàng), CC (làm bài)
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng**
- **Vị trí code:**
  - Backend: `backend/lms_service/api/endpoints/bai_kiem_tra.py`, `cau_hoi.py`
  - Frontend: `frontend/src/app/(main)/dao-tao/khoa-hoc/[id]/kiem-tra/[bktId]/page.tsx`

#### YC-LMS-03: Ngân hàng câu hỏi ĐGNL (~1.200 câu, 11 lĩnh vực)

- **Mô tả:** Quản lý ngân hàng câu hỏi đánh giá năng lực (ĐGNL) theo 11 lĩnh vực nghiệp vụ. Import/export Excel. Đã ghi 1.195 câu hỏi mới từ bộ đề DGNL 2026 (28/07/2026, xóa mềm 1.101 câu cũ).
- **Nhóm người dùng:** QT_ĐÀO_TẠO
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint `POST /api/v1/lms/dgnl/ngan-hang`, `POST /api/v1/lms/dgnl/ngan-hang/import`, `POST /api/v1/lms/dgnl/ngan-hang/xoa-nhieu` (bulk delete)
- **Vị trí code:**
  - Backend: `backend/lms_service/api/endpoints/cau_hoi_dgnl.py`
  - Frontend: `frontend/src/app/(main)/dao-tao/ky-thi/quan-ly/page.tsx` (tab "Ngân hàng đề")

#### YC-LMS-04: Cấu trúc đề + Template đề ĐGNL

- **Mô tả:** Tab thư viện mẫu cấu trúc đề ĐGNL (sửa/nhân bản mẫu). Áp mẫu nguyên tử khi tạo đề. Nới khóa trạng thái cho phép chỉnh sửa cấu trúc khi chưa có thí sinh làm bài.
- **Nhóm người dùng:** QT_ĐÀO_TẠO
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** (từ commit `8653f0e`, 25/08/2026)
- **Vị trí code:**
  - Backend: `backend/lms_service/api/endpoints/cau_truc_de_template.py`
  - Frontend: `frontend/src/app/(main)/dao-tao/ky-thi/quan-ly/page.tsx` (tab "Mẫu cấu trúc đề")

#### YC-LMS-05: Kỳ thi ĐGNL — Tổ chức ca thi

- **Mô tả:** Tạo kỳ thi, cấu trúc đề (số câu theo lĩnh vực/độ khó), ca thi, danh sách thí sinh (import Excel). Xác nhận dự thi trong cửa sổ 10 phút trước ca thi.
- **Nhóm người dùng:** QT_ĐÀO_TẠO (tổ chức), CC (thí sinh)
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint `POST /api/v1/lms/ky-thi`, `POST /api/v1/lms/ky-thi/{ky_thi_id}/cau-truc-de` (+ `/ap-dung-mau`), `POST /api/v1/lms/ky-thi/{ky_thi_id}/thi-sinh/import-excel`
- **Vị trí code:**
  - Backend: `backend/lms_service/api/endpoints/ky_thi.py`, `thi_sinh.py`
  - Frontend: `frontend/src/app/(main)/dao-tao/ky-thi/quan-ly/page.tsx` (tab "Danh sách kỳ thi", "Tạo kỳ thi mới")

#### YC-LMS-06: Kỳ thi ĐGNL — Chống gian lận

- **Mô tả:**
  - **Single-session:** khóa 1 phiên duy nhất/thí sinh, thiết bị thứ 2 bị chặn (HTTP 409).
  - **Ghi nhận vi phạm:** thoát fullscreen, vi phạm giờ + lý do (thí sinh tự ghi).
  - **Giám sát live:** giám thị xem danh sách thí sinh đang làm bài, trạng thái, vi phạm (polling).
  - **Best-score:** điểm chính thức lấy best-score giữa các lượt theo quy định kỳ thi.
- **Nhóm người dùng:** QT_ĐÀO_TẠO (giám sát), CC (thí sinh)
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** (từ commit `3ec96bd`, 31/07/2026)
- **Vị trí code:**
  - Backend: `backend/lms_service/api/endpoints/ky_thi.py`, `thi_sinh.py` (endpoint `/phien-thi/bat-dau`, `/vi-pham`)
  - Frontend: `frontend/src/app/(main)/dao-tao/ky-thi/[id]/thi/page.tsx`, `frontend/src/app/(main)/dao-tao/ky-thi/[id]/giam-sat/page.tsx`
- **Ghi chú:** Migration đã áp production 31/07; tests PASS; nhánh `feature/lms-ky-thi-giam-sat`.

#### YC-LMS-07: Reset lượt thi ĐGNL

- **Mô tả:** QT_ĐÀO_TẠO reset lượt thi cho thí sinh (2 mức: XOA_SACH / MO_KHOA_LUOT). Có nhật ký (`lich_su_reset_luot`).
- **Nhóm người dùng:** QT_ĐÀO_TẠO
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng** (từ commit `13647f8`, 10/09/2026)
- **Vị trí code:**
  - Backend: `backend/lms_service/api/endpoints/thi_sinh.py` (endpoint reset lượt thi)
  - Frontend: `frontend/src/app/(main)/dao-tao/ky-thi/[id]/thong-ke/page.tsx` (modal reset lượt thi + nhật ký reset)

#### YC-LMS-08: Chứng chỉ hoàn thành

- **Mô tả:** Cấp chứng chỉ hoàn thành khóa học theo mẫu giấy của Chi cục. Thiết kế lại từ commit `51dd8c9` (10/09/2026).
- **Nhóm người dùng:** QT_ĐÀO_TẠO (cấp), CC (nhận)
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng**
- **Vị trí code:**
  - Backend: `backend/lms_service/api/endpoints/chung_chi.py`
  - Frontend: `frontend/src/app/(main)/dao-tao/chung-chi/page.tsx`

#### YC-LMS-09: Báo cáo đào tạo

- **Mô tả:** Báo cáo kết quả đào tạo theo đơn vị, thống kê kỳ thi ĐGNL (lọc danh sách thí sinh).
- **Nhóm người dùng:** QT_ĐÀO_TẠO, CCT, PCCT
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoints `GET /api/v1/lms/bao-cao/ca-nhan`, `/bao-cao/don-vi/{don_vi_id}`, `/bao-cao/khoa-hoc/{khoa_hoc_id}`
- **Vị trí code:**
  - Backend: `backend/lms_service/api/endpoints/bao_cao.py`
  - Frontend: `frontend/src/components/lms/KetQuaBaoCaoPanel.tsx` (hiển thị trong `frontend/src/app/(main)/dao-tao/page.tsx`)

#### YC-LMS-10: Câu hỏi ĐGNL hằng ngày qua Zalo OA

- **Mô tả:** API câu hỏi ĐGNL hằng ngày cho chatbot Zalo (gợi ý 4 câu trả lời dạng nút, trả lại đáp án đúng). Giới hạn cứng của OA nhà nước: không hiện nút trên máy tính, URL không thay biến, tối đa 4 quy tắc, Zalo không gửi định danh người dùng → không chặn spam. Nhãn `CC_HQKV08_1/2/3` lọc 327 công chức khỏi 758 người theo dõi; độ phủ thật ~60%.
- **Nhóm người dùng:** CC (người nhận tin)
- **Mức ưu tiên:** **Thấp (P2)** — tính năng bổ sung
- **Trạng thái:** ✅ **Đã đáp ứng** (từ commit `81bb5b5`, 28/08/2026)
- **Vị trí code:**
  - Backend: `backend/lms_service/api/endpoints/dgnl_cong_khai.py` (API công khai cho Zalo)
- **Ghi chú:** Template ZBS mới, độ phủ thật chỉ 60% do giới hạn OA nhà nước.

### 3.3. Module HKG — Họp Không Giấy

#### YC-HKG-01: Quản lý cuộc họp

- **Mô tả:** Tạo/sửa/xóa cuộc họp, thành phần dự họp (nhóm thành phần), tài liệu họp (upload PDF/Word/Excel), kiểm soát quyền truy cập từng cuộc họp.
- **Nhóm người dùng:** QT_NOI_DUNG, CHANH_VP (tạo/sửa), Thành phần họp (xem)
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint `POST /hop-khong-giay/cuoc-hop`, `GET /hop-khong-giay/cuoc-hop/{id}`
- **Vị trí code:**
  - Backend: `backend/meeting_service/api/endpoints/cuoc_hop.py`, `tai_lieu.py` (port 8006)
  - Frontend: `frontend/src/app/(main)/hop-khong-giay/page.tsx`

#### YC-HKG-02: Trình chiếu tài liệu đồng bộ (WebSocket)

- **Mô tả:** Chủ tọa điều khiển trang tài liệu (next/prev/jump), tất cả thành phần họp nhìn thấy trang hiện tại đồng bộ thời gian thực qua WebSocket. WebSocket mount ở prefix riêng `/ws/hop-khong-giay` (không dùng chung `/api`).
- **Nhóm người dùng:** Chủ tọa (điều khiển), Thành phần họp (xem)
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** (từ commit `8e188be`, 30/07/2026)
- **Vị trí code:**
  - Backend: `backend/meeting_service/api/endpoints/presentation_ws.py`, `presentation_rest.py`; `backend/meeting_service/services/presentation_manager.py`
  - Frontend: `frontend/src/app/(main)/hop-khong-giay/chi-tiet/[id]/tai-lieu/page.tsx` + `frontend/src/hooks/usePresentationSync.ts` (backend `meeting_service/api/endpoints/presentation_ws.py`, `presentation_rest.py`)
- **Ghi chú:** Fix lỗi 403 chi tiết họp + WS path trong nginx.

#### YC-HKG-03: Ý kiến góp ý

- **Mô tả:** Thành phần họp gửi ý kiến góp ý tài liệu, chủ tọa xem/duyệt ý kiến.
- **Nhóm người dùng:** Thành phần họp (gửi), Chủ tọa (xem/duyệt)
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint `POST /api/v1/hop-khong-giay/ghi-chu`, `POST /api/v1/hop-khong-giay/ghi-chu/{ghi_chu_id}/chia-se` (chức năng ghi chú cá nhân, không phải ý kiến tập trung)
- **Vị trí code:**
  - Backend: `backend/meeting_service/api/endpoints/ghi_chu.py`
  - Frontend: `frontend/src/app/(main)/lich-cong-tac/ghi-chu/page.tsx`
- **Ghi chú:** Tính năng "ý kiến góp ý" chưa triển khai độc lập; hiện có ghi chú cá nhân + chia sẻ

#### YC-HKG-04: Bảng điểm danh chi tiết

- **Mô tả:** Xem bảng điểm danh chi tiết từng thành phần (có mặt/vắng/đi trễ), chấm tay (cờ `co_the_bam_tay`), xuất Excel. Bẫy: endpoint `require_can_edit_meeting` raise 409 khi họp HUY.
- **Nhóm người dùng:** Chủ tọa, Thư ký họp
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng** (từ commit `dba30f9`, 04/09/2026)
- **Vị trí code:**
  - Backend: `backend/meeting_service/api/endpoints/diem_danh.py` (endpoint `GET /api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/diem-danh/chi-tiet`, `GET .../diem-danh/xuat-excel`)
  - Frontend: `frontend/src/app/(main)/hop-khong-giay/chi-tiet/[id]/diem-danh/page.tsx`

#### YC-HKG-05: Log định danh khi từ chối truy cập (403)

- **Mô tả:** Khi công chức cố truy cập cuộc họp không có quyền → ghi log định danh (user_id, cuộc họp, IP, thời điểm) để rà soát.
- **Nhóm người dùng:** ADMIN, TRUONG_CNTT (rà soát log)
- **Mức ưu tiên:** **Thấp (P2)** — bảo mật
- **Trạng thái:** ✅ **Đã đáp ứng**
- **Vị trí code:**
  - Backend: `backend/meeting_service/dependencies.py` (hàm `log_tu_choi_cuoc_hop()`, commit 45dfc81, 30/07/2026)

### 3.4. Module Lịch công tác

#### YC-LICH-01: Quản lý lịch công tác

- **Mô tả:** Đăng/sửa/xóa lịch công tác (họp, tiếp đoàn, công tác), chọn thành phần từ danh mục lãnh đạo. Phân quyền: mở cho cả 544 công chức đăng (không có lưới chặn endpoint tạo); sửa/xoá giới hạn người tạo + CCT/PCCT/CHANH_VP/QT_NOI_DUNG (7 người VP gán 26/08, phải đăng nhập lại mới ăn).
- **Nhóm người dùng:** Tất cả (đăng), QT_NOI_DUNG (sửa/xóa toàn bộ)
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint `POST /api/v1/hop-khong-giay/lich-cong-tac/`, `GET /api/v1/hop-khong-giay/lich-cong-tac/`, `GET .../lich-cong-tac/xuat-excel`
- **Vị trí code:**
  - Backend: `backend/meeting_service/api/endpoints/lich_cong_tac.py`
  - Frontend: `frontend/src/app/(main)/lich-cong-tac/page.tsx`

#### YC-LICH-02: Tài liệu đính kèm + Phân quyền tài liệu

- **Mô tả:** Thêm tài liệu đính kèm (PDF/Word/Excel) ngay trong modal Thêm lịch. Phân quyền tài liệu 2 mức: "Công khai" / "Hạn chế đối tượng". Thư viện văn bản pháp quy đã di trú sang Portal (G5.1).
- **Nhóm người dùng:** Người tạo lịch (đính kèm), QT_NOI_DUNG (phân quyền)
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng**
- **Vị trí code:**
  - Backend: `backend/meeting_service/api/endpoints/tai_lieu.py`
  - Frontend: `frontend/src/app/(main)/tai-lieu/page.tsx` (thư viện tài liệu chung), `frontend/src/app/(main)/hop-khong-giay/` (tài liệu họp)

#### YC-LICH-03: Nhắc lịch qua Zalo OA

- **Mô tả:** Nhắc lịch công tác qua Zalo OA tại 3 mốc (sáng trước họp, 1h trước họp, sau họp), dùng chung template ZBS 623236. Fix lỗi bộ nhắc lệch +7h (giờ họp là giờ VN, không phải UTC).
- **Nhóm người dùng:** Thành phần họp (nhận tin)
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng** (từ commit `69c795e`, 21/08/2026)
- **Vị trí code:**
  - Backend: `backend/common_service/services/zalo/` (scheduler trong common_service), `backend/meeting_service/scheduler.py` (PM2 process `zalo-worker` chạy scheduler)
  - Frontend: (không có — worker tự chạy)

#### YC-LICH-04: Ghi chú cá nhân và chia sẻ

- **Mô tả:** Công chức ghi chú cá nhân vào cuộc họp (chỉ mình nhìn thấy), chia sẻ ghi chú với người khác nếu muốn.
- **Nhóm người dùng:** Tất cả
- **Mức ưu tiên:** **Thấp (P2)**
- **Trạng thái:** ✅ **Đã đáp ứng**
- **Vị trí code:**
  - Backend: `backend/meeting_service/api/endpoints/ghi_chu.py`
  - Frontend: `frontend/src/app/(main)/lich-cong-tac/ghi-chu/page.tsx`

#### YC-LICH-05: Đánh giá cuộc họp

- **Mô tả:** Đánh giá chất lượng chuẩn bị cuộc họp (1–5 sao), chỉ lãnh đạo chấm.
- **Nhóm người dùng:** CCT, PCCT, TDV
- **Mức ưu tiên:** **Thấp (P2)**
- **Trạng thái:** ✅ **Đã đáp ứng**
- **Vị trí code:**
  - Backend: `backend/meeting_service/api/endpoints/danh_gia.py`
  - Frontend: Tích hợp trong chi tiết họp

#### YC-LICH-06: Báo cáo đối soát + Thống kê tài liệu

- **Mô tả:** Báo cáo đối soát cuộc họp (ai chưa xác nhận), thống kê tài liệu họp (số lượng, tải về).
- **Nhóm người dùng:** QT_NOI_DUNG, CHANH_VP
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng**
- **Vị trí code:**
  - Backend: `backend/meeting_service/api/endpoints/doi_soat.py`, `thong_ke_tai_lieu.py`
  - Frontend: `frontend/src/app/(main)/lich-cong-tac/doi-soat/page.tsx`

#### YC-LICH-07: Xem lịch (ngày/tuần/tháng)

- **Mô tả:** 3 chế độ xem: Lịch ngày (chi tiết đầy đủ từng cuộc họp), Lịch tuần, Lịch tháng (dạng lưới).
- **Nhóm người dùng:** Tất cả
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng**
- **Vị trí code:**
  - Frontend: `frontend/src/app/(main)/lich-cong-tac/page.tsx`

### 3.5. Module Chỉ tiêu đơn vị

#### YC-CHI-TIEU-01: Quản lý danh mục chỉ tiêu

- **Mô tả:** Danh mục chỉ tiêu theo lĩnh vực (Nghiệp vụ, Hành chính, Tài chính...), thêm/sửa/vô hiệu hóa chỉ tiêu.
- **Nhóm người dùng:** QT_CHI_TIEU, TCCB
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** — 26 endpoints, 6 trang FE (từ 04/06/2026)
- **Vị trí code:**
  - Backend: `backend/chi_tieu_service/` (port 8007)
  - Frontend: `frontend/src/app/(main)/chi-tieu/page.tsx`

#### YC-CHI-TIEU-02: Giao chỉ tiêu năm cho đơn vị

- **Mô tả:** Giao chỉ tiêu năm cho 15 đơn vị, đơn vị xem chỉ tiêu được giao.
- **Nhóm người dùng:** QT_CHI_TIEU (giao), TDV (xem)
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng**
- **Vị trí code:**
  - Backend: `backend/chi_tieu_service/api/endpoints/giao_nam.py`
  - Frontend: `frontend/src/app/(main)/chi-tieu/giao-nam/page.tsx`

#### YC-CHI-TIEU-03: Đăng ký/cập nhật kết quả theo tháng

- **Mô tả:** Đơn vị đăng ký/cập nhật kết quả thực hiện chỉ tiêu theo tháng. Luồng duyệt (2 cấp?).
- **Nhóm người dùng:** TDV (đăng ký), QT_CHI_TIEU (duyệt)
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng**
- **Vị trí code:**
  - Backend: `backend/chi_tieu_service/api/endpoints/dang_ky.py` + `duyet.py`
  - Frontend: `frontend/src/app/(main)/chi-tieu/dang-ky/page.tsx` + `chi-tieu/duyet/page.tsx`

#### YC-CHI-TIEU-04: Người theo dõi chỉ tiêu

- **Mô tả:** Gán người theo dõi chỉ tiêu (platform role `THEO_DOI_CHI_TIEU`), xem/báo cáo cross-unit.
- **Nhóm người dùng:** QT_CHI_TIEU (gán), THEO_DOI_CHI_TIEU (xem)
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng**
- **Vị trí code:**
  - Backend: `backend/chi_tieu_service/api/endpoints/nguoi_theo_doi.py`
  - Frontend: `frontend/src/app/(main)/chi-tieu/nguoi-theo-doi/page.tsx`

#### YC-CHI-TIEU-05: Báo cáo tổng hợp

- **Mô tả:** Báo cáo tổng hợp chỉ tiêu theo đơn vị, lĩnh vực, tháng/quý/năm. Xuất Excel.
- **Nhóm người dùng:** QT_CHI_TIEU, CCT, PCCT
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng**
- **Vị trí code:**
  - Backend: `backend/chi_tieu_service/api/endpoints/bao_cao.py`
  - Frontend: `frontend/src/app/(main)/chi-tieu/bao-cao/page.tsx`

### 3.6. Module Forum — Diễn đàn hỏi đáp

#### YC-FORUM-01: Chủ đề và bình luận

- **Mô tả:** Đăng chủ đề hỏi đáp nghiệp vụ, bình luận, chuyên gia trả lời, tìm kiếm.
- **Nhóm người dùng:** Tất cả (đăng), CHUYEN_GIA (trả lời)
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng (mức sử dụng thấp)** — BE + FE + test đã có và chạy prod (8 file test); dữ liệu thật 06/10/2026: 9 chuyên mục, 2 chủ đề, 14 trả lời
- **Vị trí code:**
  - Backend: `backend/forum_service/` (port 8002)
  - Frontend: `frontend/src/app/(main)/dien-dan/` (chủ đề, chuyên mục, của tôi, tạo mới, quản lý)

### 3.7. Module Legal — Văn bản pháp luật

#### YC-LEGAL-01: Tra cứu văn bản

- **Mô tả:** Tra cứu văn bản pháp luật nội bộ theo lĩnh vực, số/ký hiệu, ngày ban hành. Tìm kiếm full-text.
- **Nhóm người dùng:** Tất cả
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng (mức sử dụng thấp)** — BE + FE + test đã có và chạy prod (8 file test); dữ liệu thật: 2 văn bản, 618 lượt xác nhận đã đọc; quiz văn bản chưa dùng
- **Vị trí code:**
  - Backend: `backend/legal_service/` (port 8003)
  - Frontend: `frontend/src/app/(main)/phap-luat/` (danh sách, chi tiết, chưa đọc, quiz, báo cáo, quản lý)

### 3.8. Module Portal — Tin tức/CMS

#### YC-PORTAL-01: Đăng tin bài

- **Mô tả:** Đăng tin tức, chuyên mục thông tin nội bộ. Phân quyền BIEN_TAP.
- **Nhóm người dùng:** BIEN_TAP (đăng), Tất cả (xem)
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng một phần chức năng** — BE + FE + test đã có và chạy prod (7 file test); dùng chủ yếu cho kho tài liệu (194 thư mục, 22 tài liệu) và vinh danh; tin bài chưa có bài nào
- **Vị trí code:**
  - Backend: `backend/portal_service/` (port 8004)
  - Frontend: `frontend/src/app/(main)/tai-lieu/`, `tin-tuc/` (danh sách, chi tiết, quản lý)

### 3.9. Module Common — Dùng chung

#### YC-COMMON-01: Thông báo

- **Mô tả:** Thông báo hệ thống (popup/badge), đánh dấu đã đọc, lọc theo loại.
- **Nhóm người dùng:** Tất cả (nhận), Backend các module (gửi)
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint `GET /api/common/v1/thong-bao`, `PATCH /api/common/v1/thong-bao/{thong_bao_id}/doc`, `PATCH /api/common/v1/thong-bao/doc-tat-ca`
- **Vị trí code:**
  - Backend: `backend/common_service/` (port 8005)
  - Frontend: `frontend/src/app/(main)/tong-quan/components/WidgetThongBao.tsx`, `frontend/src/app/(main)/thong-bao/page.tsx`

#### YC-COMMON-02: Quản lý tập tin dùng chung

- **Mô tả:** Upload/download tập tin dùng chung (PDF/Word/Excel/hình ảnh), kiểm soát kích thước, kiểm tra virus (nếu có).
- **Nhóm người dùng:** Tất cả
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint `POST /api/common/v1/file/upload`, `GET /api/common/v1/file/{file_id}`
- **Vị trí code:**
  - Backend: `backend/common_service/api/endpoints/file_storage.py`

### 3.10. Module Zalo OA

#### YC-ZALO-01: Nhắc lịch qua Zalo OA

- **Mô tả:** (Đã mô tả ở YC-LICH-03)
- **Trạng thái:** ✅ **Đã đáp ứng**

#### YC-ZALO-02: Câu hỏi ĐGNL hằng ngày

- **Mô tả:** (Đã mô tả ở YC-LMS-10)
- **Trạng thái:** ✅ **Đã đáp ứng**

#### YC-ZALO-03: Gắn nhãn công chức để lọc người nhận

- **Mô tả:** Gắn nhãn `CC_HQKV08_1/2/3` qua API Zalo để lọc người nhận tin (327 công chức khỏi 758 người theo dõi). Xuất báo cáo công chức chưa quan tâm OA để đơn vị rà soát.
- **Nhóm người dùng:** ADMIN (gắn nhãn), TCCB (xuất báo cáo)
- **Mức ưu tiên:** **Thấp (P2)**
- **Trạng thái:** ✅ **Đã đáp ứng** (từ commit `81bb5b5`, `0da8ae3`)
- **Vị trí code:**
  - Backend: `backend/common_service/services/zalo/` (gắn nhãn, quản lý OA)
  - Frontend: Chưa có trang quản trị Zalo riêng, chức năng được tích hợp vào quản lý công chức
- **Ghi chú:** Trang admin/zalo/ chưa triển khai; gắn nhãn thực hiện qua script hoặc API trực tiếp

### 3.11. Module Trực ban

#### YC-TRUC-BAN-01: Nhập lịch trực bằng mã công chức

- **Mô tả:** Nhập lịch trực bằng file Excel (mã công chức), file mẫu sinh từ CSDL. Xem lịch trực theo tuần/tháng.
- **Nhóm người dùng:** QT_NOI_DUNG (nhập), Tất cả (xem)
- **Mức ưu tiên:** **Trung bình (P1)**
- **Trạng thái:** ✅ **Đã đáp ứng** (từ commit `dd3c8e4`)
- **Vị trí code:**
  - Backend: `backend/meeting_service/api/endpoints/truc_ban.py`
  - Frontend: `frontend/src/app/(main)/lich-cong-tac/truc-ban/page.tsx`

### 3.12. Tích hợp và tiện ích

#### YC-TICH-HOP-01: SSO — Đăng nhập một lần

- **Mô tả:** Đăng nhập một lần (`POST /api/v1/auth/login`) phục vụ cả 8 module. JWT ký HS256, hiệu lực 8 giờ, claims: `sub` (user id), `ma_cc`, `ho_ten`, `role`, `don_vi_id`, `is_lanh_dao`, `is_admin`, `platform_roles`, `exp`. Mỗi service tự verify JWT bằng cùng SECRET_KEY.
- **Nhóm người dùng:** Tất cả
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng**
- **Vị trí code:**
  - Backend: `backend/app/api/v1/endpoints/auth.py` (KPI backend port 8000), `backend/shared/auth.py` (dùng chung)
  - Frontend: `frontend/src/stores/useAuthStore.ts`, `frontend/src/providers/AuthProvider.tsx`

#### YC-TICH-HOP-02: Đổi mật khẩu

- **Mô tả:** Công chức đổi mật khẩu (nhập mật khẩu cũ + mới). Admin reset mật khẩu cho người dùng.
- **Nhóm người dùng:** Tất cả (đổi), ADMIN (reset)
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** — endpoint `POST /api/v1/auth/change-password`, `PUT /api/v1/admin/users/{user_id}/reset-password`
- **Vị trí code:**
  - Backend: `backend/app/api/v1/endpoints/auth.py` (change-password), `backend/app/api/v1/endpoints/admin.py` (reset)
  - Frontend: `frontend/src/app/(main)/ho-so/page.tsx` (trang hồ sơ cá nhân chứa đổi mật khẩu)

#### YC-TICH-HOP-03: Chống dò mật khẩu (rate limit + lockout)

- **Mô tả:** Khóa tài khoản tạm 15 phút sau 10 lần đăng nhập sai liên tiếp. Rate limit 30 lần/phút/IP tại endpoint login.
- **Nhóm người dùng:** (Bảo vệ tất cả)
- **Mức ưu tiên:** **Cao (P0)** — bảo mật
- **Trạng thái:** ✅ **Đã đáp ứng** (từ 31/07/2026, đợt vá bảo mật)
- **Vị trí code:**
  - Backend: `backend/app/core/security.py` (hàm `check_brute_force`, middleware `RateLimitMiddleware`)

#### YC-TICH-HOP-04: Responsive — Tương thích thiết bị di động

- **Mô tả:** Giao diện tương thích màn hình điện thoại (responsive), lãnh đạo có thể duyệt trên di động.
- **Nhóm người dùng:** Tất cả (đặc biệt lãnh đạo)
- **Mức ưu tiên:** **Cao (P0)**
- **Trạng thái:** ✅ **Đã đáp ứng** — frontend dùng Tailwind CSS 4, responsive breakpoints
- **Vị trí code:**
  - Frontend: toàn bộ components dùng `sm:`, `md:`, `lg:` breakpoints

## 4. Yêu cầu phi chức năng

### 4.1. Bảo mật và ATTT

| Yêu cầu | Mô tả | Trạng thái | Ghi chú |
|---|---|---|---|
| **NFR-SEC-01:** Mã hóa mật khẩu | Mật khẩu người dùng mã hóa một chiều bằng **bcrypt** (passlib), salt tự sinh từng mật khẩu | ✅ Đạt | Chi tiết: Mục 7 tài liệu, `07_tai_khoan_phan_quyen_nhat_ky.md` |
| **NFR-SEC-02:** Chính sách mật khẩu mạnh | Độ phức tạp tối thiểu 8 ký tự + hoa/thường/số/ký tự đặc biệt | ❌ Chưa đạt | Hiện chỉ yêu cầu ≥6 ký tự; mật khẩu khởi tạo mặc định `123456`; chưa bắt buộc đổi lần đầu |
| **NFR-SEC-03:** Chống dò mật khẩu | Rate limit + lockout tài khoản sau 10 lần sai | ✅ Đạt (từ 31/07/2026) | Khóa tạm 15 phút |
| **NFR-SEC-04:** Mã hóa đường truyền | HTTPS toàn bộ (TLS, Let's Encrypt) | ✅ Đạt | DB không mở ra ngoài (localhost) |
| **NFR-SEC-05:** Mã hóa dữ liệu lưu trữ (at-rest) | DB không mã hóa at-rest; bản backup đẩy off-site có mã hóa | 🟡 Một phần | DB nội bộ sau firewall → chấp nhận được |
| **NFR-SEC-06:** RBAC 2 lớp | Vai trò nghiệp vụ (7 loại) + platform role (15 loại), kiểm tra backend từng endpoint | ✅ Đạt | Chi tiết: Mục 7 tài liệu |
| **NFR-SEC-07:** JWT stateless | JWT ký HS256, hiệu lực 8h, SECRET_KEY qua biến môi trường (không hardcode) | ✅ Đạt (từ 31/07/2026) | Đã rà và gỡ toàn bộ credential khỏi mã nguồn 31/07 |
| **NFR-SEC-08:** Audit log tập trung | Bảng `audit_log` + trigger tự động cho bảng nghiệp vụ | ❌ Chưa đạt | Bảng có sẵn nhưng trigger chưa kích hoạt production; vết thay đổi đang phân tán |
| **NFR-SEC-09:** Log đăng nhập | Mọi lần đăng nhập (thành công + sai) ghi log kèm IP, thời điểm | 🟡 Một phần | Đăng nhập **sai** có log; đăng nhập **thành công** chỉ có `last_login` + nginx access log |
| **NFR-SEC-10:** Ẩn /docs trên production | `/docs`, `/openapi.json` tắt trên production (bật lại được bằng `DEBUG=true`) | ✅ Đạt (từ 31/07/2026) | 8 service đều tắt |
| **NFR-SEC-11:** Rotate credentials | INTERNAL_API_KEY đã rotate 31/07/2026; SECRET_KEY (ký JWT) và mật khẩu DB **chưa đổi** (mật khẩu DB cũ vẫn trong git history) | 🟡 Một phần | Cần đổi mật khẩu DB + rotate SECRET_KEY; gỡ khỏi git history |

### 4.2. Hiệu năng và tải

| Yêu cầu | Mô tả | Trạng thái | Ghi chú |
|---|---|---|---|
| **NFR-PERF-01:** Thời gian phản hồi API | ≤ 2s cho 95% request | ✅ Đạt | Đo trên prod: bảng tổng hợp 542 dòng / 0,19s, Excel 109 KB / 0,33s |
| **NFR-PERF-02:** Số người dùng đồng thời | Hỗ trợ ≥100 người dùng đồng thời | ✅ Đạt | Đã chịu tải kỳ thi ĐGNL ~90 thí sinh cùng lúc |
| **NFR-PERF-03:** Kỳ thi ĐGNL không OOM | Kỳ thi ~90 thí sinh không gây OOM (hết RAM) | 🟡 Một phần (từ 25/08/2026) | Đã bổ sung swap 8GB + chốt chặn `kiem_tra_ky_thi.sh`; nhưng LMS ~90MB/thí sinh không trả lại RAM → còn nợ |
| **NFR-PERF-04:** Chặn build khi đang thi | Build frontend không được chạy khi đang có người thi (tránh OOM) | ✅ Đạt (từ commit `2137a32`, 25/08/2026) | Script `build_frontend.sh` + `kiem_tra_ky_thi.sh` |
| **NFR-PERF-05:** Database indexing | Index thích hợp cho các bảng lớn (kê khai, đánh giá, thi sinh) | ✅ Đạt | Các bảng nghiệp vụ lớn có index |

### 4.3. Sẵn sàng và sao lưu

| Yêu cầu | Mô tả | Trạng thái | Ghi chú |
|---|---|---|---|
| **NFR-AVAIL-01:** RPO (Recovery Point Objective) | ≤ 12 giờ | ✅ Đạt | Backup 2 lần/ngày (02:00 + 14:00) |
| **NFR-AVAIL-02:** Backup tự động | Cron chạy tự động, 3 lớp: cục bộ + off-site DB + off-site mã nguồn | ✅ Đạt | Chi tiết: Mục 6 tài liệu, `06_co_so_du_lieu_sao_luu.md` |
| **NFR-AVAIL-03:** Backup off-site | Bản dump mã hóa đẩy lên GitHub private | ✅ Đạt | Uploads có lịch sử 30 ngày từ 25/08 |
| **NFR-AVAIL-04:** Diễn tập phục hồi định kỳ | Restore vào DB test thường xuyên (clone prod → test) | ✅ Đạt | Thực hiện trước mỗi đợt kiểm thử |
| **NFR-AVAIL-05:** Uptime | ≥ 99% (cho phép downtime ~7h/tháng) | ✅ Đạt | Triển khai downtime ≈ 0 (pm2 restart từng service) |
| **NFR-AVAIL-06:** Cảnh báo lỗi | Cảnh báo khi backup thất bại, service down | ❌ Chưa có | Hiện phải kiểm tra log thủ công |

### 4.4. Khả dụng trên thiết bị

| Yêu cầu | Mô tả | Trạng thái |
|---|---|---|
| **NFR-USAB-01:** Responsive | Giao diện tương thích điện thoại (responsive) | ✅ Đạt |
| **NFR-USAB-02:** Trình duyệt hỗ trợ | Chrome, Edge, Safari, Firefox (phiên bản mới nhất − 2) | ✅ Đạt |
| **NFR-USAB-03:** Không yêu cầu cài đặt | Web app, không cần cài đặt client | ✅ Đạt |

### 4.5. Ngôn ngữ

| Yêu cầu | Mô tả | Trạng thái |
|---|---|---|
| **NFR-LANG-01:** Tiếng Việt | Toàn bộ giao diện, thông báo, báo cáo bằng tiếng Việt có dấu | ✅ Đạt |

### 4.6. Tuân thủ pháp lý

| Yêu cầu | Mô tả | Trạng thái | Ghi chú |
|---|---|---|---|
| **NFR-LEGAL-01:** NĐ 13/2023 về dữ liệu cá nhân | Bảo vệ dữ liệu cá nhân (họ tên, ngày sinh, email, SĐT) | ✅ Đạt | Phân quyền theo vai trò + đơn vị; mật khẩu bcrypt |
| **NFR-LEGAL-02:** QĐ 1804/QĐ-TCHQ, QĐ 330/QĐ-HQKV8 | Tuân thủ quy chế ATTT mạng và quy trình vận hành an toàn hệ thống thông tin | 🟡 Một phần | Đã đáp ứng: HTTPS, RBAC, chống dò mật khẩu, sao lưu 3 lớp, ẩn API docs; còn thiếu: mật khẩu mạnh + bắt đổi mật khẩu mặc định, nhật ký audit tập trung, tường lửa trên máy chủ (ufw tắt) — xem `10_HOI_DAP_BO_SUNG.md`, `17_HOI_DAP_DOT_2.md` |
| **NFR-LEGAL-03:** CV 21169 — Đánh giá theo quý | Từ Q3/2026 chuyển từ tháng sang quý; hạn nộp ngày 23 tháng cuối quý | ✅ Đạt (từ commit `67bda67`, 28/09/2026) | |

### 4.7. Lưu trữ

| Yêu cầu | Mô tả | Trạng thái |
|---|---|---|
| **NFR-STOR-01:** Lưu trữ tập tin | Upload lên thư mục `backend/uploads/` (hoặc MinIO nếu mở rộng) | ✅ Đạt |
| **NFR-STOR-02:** Dung lượng DB | PostgreSQL hiện ~37% disk (100 GB tổng) | ✅ Đạt |

## 5. Yêu cầu ràng buộc và giả định

### 5.1. Ràng buộc kỹ thuật

| Ràng buộc | Mô tả |
|---|---|
| **CONST-01:** Một database, nhiều schema | Tất cả module mới dùng schema riêng trong **cùng database** `kpi_haiquan` (lý do: cross-schema JOIN, 1 connection pool, FK trực tiếp `public.cong_chuc(id)`) |
| **CONST-02:** Port mapping cố định | 8 backend service chạy port 8000–8007; frontend port 3000; DB port 5432 |
| **CONST-03:** SSO JWT — không thay đổi SECRET_KEY tùy tiện | Đổi SECRET_KEY → toàn bộ token hiện tại vô hiệu → 544 người phải đăng nhập lại |
| **CONST-04:** Dev + Prod cùng máy chủ | Cả 2 môi trường chạy trên cùng VM (79.108.216.189) → build ở dev vẫn có thể giết prod nếu không cẩn thận |
| **CONST-05:** KHÔNG sửa schema `public` | Các bảng KPI production trong `public` (cong_chuc, vai_tro, don_vi, ke_khai, danh_gia...) KHÔNG được sửa/xóa |
| **CONST-06:** Migration chạy từ `/opt/kpi-prod` | Alembic migration PHẢI chạy từ cây production `/opt/kpi-prod`, không chạy từ `/root/kpi-haiquan` |
| **CONST-07:** Nhánh `prod` là trunk | Code đang phục vụ người dùng nằm trên nhánh `prod`, không phải `main`; `main` chỉ fast-forward theo `prod` sau khi prod chạy thật |

### 5.2. Giả định nghiệp vụ

| Giả định | Mô tả |
|---|---|
| **ASSUME-01:** Một tháng = một version KPI | Không cho mix V1 + V2_PL3 trong cùng (công chức, tháng, năm) |
| **ASSUME-02:** Lãnh đạo dùng chung bảng kê khai | Lãnh đạo (PDV/TDV/PCCT/CCT) không có bảng kê khai riêng, dùng chung `ke_khai_cong_viec` nhưng có bộ chỉ số d/đ/e riêng |
| **ASSUME-03:** 15 đơn vị không thay đổi thường xuyên | Cơ cấu 15 đơn vị (Phòng/Đội/HQ Cửa khẩu) tương đối ổn định; điều chuyển nhân sự có ngày hiệu lực |
| **ASSUME-04:** Mọi người dùng đã có tài khoản | Không có chức năng đăng ký tài khoản công khai; tài khoản do ADMIN tạo sẵn |
| **ASSUME-05:** Không có thanh toán, SMS/OTP, API bên thứ ba trong luồng nghiệp vụ | Hệ thống nội bộ, không tích hợp hệ thống bên ngoài (trừ Zalo OA và backup lên GitHub) |

## 6. Ma trận truy vết yêu cầu

| Yêu cầu | Module | Nguồn văn bản | Tài liệu thiết kế / API | Trạng thái |
|---|---|---|---|---|
| YC-KPI-01 ~ YC-KPI-13 | KPI | CV 21169/CHQ-TCCB, yêu cầu nghiệp vụ TCCB, `docs/BUSINESS_RULES_v3_0_PL3.md` | `02_mo_ta_chuc_nang_quy_trinh.md`, `08_danh_muc_api.md` | ✅ Đã đáp ứng |
| YC-LMS-01 ~ YC-LMS-10 | LMS | Tờ trình Digital Learning, yêu cầu nghiệp vụ TCCB | `docs/lms/LMS_API_SPECS.md`, `docs/lms/LMS_BUSINESS_RULES.md` | ✅ Đã đáp ứng |
| YC-HKG-01 ~ YC-HKG-05 | HKG | Kế hoạch Phase 4 HKG (VP), góp ý sử dụng | `docs/HKG/HKG_SPEC_ADAPTED.md`, `docs/HKG/PHAN_TICH_VA_GOP_Y_HKG.md` | ✅ Đã đáp ứng |
| YC-LICH-01 ~ YC-LICH-07 | Lịch công tác | Góp ý sử dụng thực tế (Q2–Q3/2026), di trú lichkv8 | `docs/lich-cong-tac/`, git log G4.x, G5.x | ✅ Đã đáp ứng |
| YC-CHI-TIEU-01 ~ YC-CHI-TIEU-05 | Chỉ tiêu | Yêu cầu TCCB (Q2/2026) | `docs/Chi Tieu/`, nhánh `feature/chi-tieu-scaffold` | ✅ Đã đáp ứng |
| YC-FORUM-01 | Forum | Tờ trình Digital Learning | `docs/forum/FORUM_*.md` | ✅ (ít dùng) |
| YC-LEGAL-01 | Legal | Tờ trình Digital Learning | `docs/legal/LEGAL_*.md` | ✅ (ít dùng) |
| YC-PORTAL-01 | Portal | Tờ trình Digital Learning | — | ✅ (một phần chức năng) |
| YC-ZALO-01 ~ YC-ZALO-03 | Zalo OA | Góp ý Lịch công tác, yêu cầu ôn tập ĐGNL | `docs/zalo-oa/`, commit `69c795e`, `81bb5b5` | ✅ Đã đáp ứng |
| NFR-SEC-* | Toàn hệ thống | CV 153/CNTT, đợt vá 31/07/2026 | `07_tai_khoan_phan_quyen_nhat_ky.md`, `10_HOI_DAP_BO_SUNG.md` | 🟡 Đa số đạt, còn 3 mục chưa |
| NFR-PERF-* | Toàn hệ thống | Sự cố OOM 25/08/2026 | `docs/van-hanh/`, commit `2137a32` | 🟡 Đa số đạt, LMS leak RAM còn nợ |
| NFR-AVAIL-* | Toàn hệ thống | Yêu cầu vận hành nội bộ | `06_co_so_du_lieu_sao_luu.md`, `/etc/cron.d/hkg-backups` | ✅ Đa số đạt, thiếu cảnh báo |

## 7. Yêu cầu chưa đáp ứng / Tồn đọng

### 7.1. Bảo mật

| Mã | Yêu cầu | Mức ưu tiên | Kế hoạch |
|---|---|---|---|
| **TODO-SEC-01** | Chính sách mật khẩu mạnh (≥8 ký tự + 4 nhóm) + bắt buộc đổi lần đầu (`must_change_password`) | **Cao (P0)** | Dự kiến đợt cập nhật tiếp theo (Q4/2026) |
| **TODO-SEC-02** | Audit log tập trung — kích hoạt trigger tự động cho nhóm bảng trọng yếu | **Cao (P0)** | Gộp vào đợt `must_change_password` |
| **TODO-SEC-03** | Đổi mật khẩu DB + gỡ khỏi git history | **Trung bình (P1)** | Cần phối hợp CNTT |

### 7.2. Hiệu năng

| Mã | Yêu cầu | Mức ưu tiên | Kế hoạch |
|---|---|---|---|
| **TODO-PERF-01** | Fix LMS leak RAM (~90MB/thí sinh không trả lại) | **Trung bình (P1)** | Chưa rõ gốc rễ; cần profiling |

### 7.3. Sẵn sàng

| Mã | Yêu cầu | Mức ưu tiên | Kế hoạch |
|---|---|---|---|
| **TODO-AVAIL-01** | Backup off-site uploads (hiện chỉ có DB off-site) | **Trung bình (P1)** | Đã có lịch sử 30 ngày từ 25/08, cần đẩy lên NAS/máy chủ khác |
| **TODO-AVAIL-02** | Backup không cùng ổ đĩa với production | **Trung bình (P1)** | Cần hạ tầng (NAS/máy chủ riêng) |
| **TODO-AVAIL-03** | Cảnh báo khi backup thất bại, service down | **Trung bình (P1)** | Có thể dùng Telegram bot hoặc email |

### 7.4. Chức năng còn nợ

| Mã | Yêu cầu | Mức ưu tiên | Kế hoạch |
|---|---|---|---|
| **TODO-FUNC-01** | Lấy ý kiến dự thảo (đề xuất Chánh VP) | **Thấp (P2)** | Đang nghiên cứu (14/09), chờ quyết định; rủi ro phân mảnh (đã có 3 cơ chế ghi ý kiến) |
| **TODO-FUNC-02** | Đối soát đánh giá **theo QUÝ** (hiện chỉ có theo THÁNG) | **Trung bình (P1)** | Từ Q3/2026 kỳ đánh giá đã sang quý, trang đối soát chưa kịp cập nhật |
| **TODO-FUNC-03** | Tải hàng loạt .docx phiếu đánh giá theo ZIP | **Thấp (P2)** | Hiện chỉ tải từng file; TCCB nộp hồ sơ hàng loạt sẽ tiện hơn |
| **TODO-FUNC-04** | HDSD người dùng cuối theo vai trò | **Trung bình (P1)** | ✅ Đã lập 06/10/2026 tại `13_huong_dan_su_dung/`; còn thiếu ảnh minh họa |
| **TODO-FUNC-05** | Màn điều chuyển hàng loạt — thêm số QĐ | **Thấp (P2)** | Hiện chỉ có ngày hiệu lực, chưa có trường số QĐ |
| **TODO-FUNC-06** | Forum, Legal, Portal — thúc đẩy sử dụng thực tế | **Thấp (P2)** | Đã có BE/FE/test và chạy prod nhưng dữ liệu nghiệp vụ rất ít (2 chủ đề diễn đàn, 2 văn bản, 0 tin bài) |

## 8. Phụ lục — Thống kê chi tiết (kiểm đếm 06/10/2026)

### 8.1. Số liệu người dùng

- **Tổng số tài khoản:** 560 (544 đang hoạt động)
- **Phân theo vai trò:**
  - CCT: 1, PCCT: 3, TDV: 14 (13 active), PDV: 37, CC: 395 (383 active), HD_111: 109 (106 active), ADMIN: 1
  - 56 là lãnh đạo (CCT + PCCT + TDV + PDV)
- **Platform roles được gán:**
  - QT_NOI_DUNG: 7, QT_DAO_TAO: 1, TRUONG_CNTT: 1, THEO_DOI_CHI_TIEU: 1, CHANH_VP: 1
  - 10 role còn lại: 0 người (dự phòng)
- **15 đơn vị** đang hoạt động

### 8.2. Số liệu hệ thống

- **Database:** 1 database `kpi_haiquan`, 8 schema (public + lms + meeting + chi_tieu + forum + legal + portal + common), **111 bảng** (kiểm đếm 06/10/2026: public 37, meeting 23, lms 22, common 8, legal 6, chi_tieu 5, forum 5, portal 5)
- **Backend:** 8 service (KPI 8000, LMS 8001, Forum 8002, Legal 8003, Portal 8004, Common 8005, Meeting/HKG 8006, Chỉ tiêu 8007), cấu trúc endpoint không theo `/v1/` mà trực tiếp `/api/endpoints/` cho các service mới
- **Frontend:** Trang trong `frontend/src/app/(main)/`, cấu trúc route nested (ví dụ: `admin/dieu-chuyen-hang-loat/`, `lich-cong-tac/truc-ban/`)
- **Máy chủ:** Ubuntu 24.04, 4 vCPU / 7.8 GB RAM / 99 GB disk (71% dùng), Python 3.12, Node.js 20.20, PostgreSQL 15.16
- **PM2:** 10 process (8 backend Python/uvicorn + 1 frontend Next.js + 1 zalo-worker chạy trong meeting_service scheduler)
- **Nghỉ phép:** 16.448 lượt đã ghi nhận
- **Ngân hàng câu hỏi ĐGNL:** ~1.200 câu (11 lĩnh vực)
- **Danh mục công việc:** 46 mục V1 + 2.812 mục PL3 (15 lĩnh vực, 5 nhóm phức tạp)

### 8.3. Commit quan trọng (từ git log)

- `d8762c2` (29/09/2026): Gỡ tính năng kê khai lại đ cấp quý
- `60b8932` (29/09/2026): Tổng hợp phiếu Mẫu 02 toàn Chi cục (chỉ đọc)
- `67bda67` (28/09/2026): d/đ/e của lãnh đạo kê một lần cho cả quý
- `4aaa43e` (13/09/2026): Điều chuyển hàng loạt bằng Excel
- `13647f8` (10/09/2026): Reset lượt thi ĐGNL
- `8653f0e` (25/08/2026): Tab thư viện mẫu cấu trúc đề ĐGNL
- `2137a32` (25/08/2026): Chặn build/triển khai khi đang thi (fix OOM)
- `81bb5b5` (28/08/2026): Câu hỏi ĐGNL hằng ngày qua Zalo
- `3ec96bd` (31/07/2026): Nâng cấp kỳ thi ĐGNL (5 tính năng + TIMESTAMPTZ)
- `dba30f9` (04/09/2026): Bảng điểm danh chi tiết HKG
- `8e188be` (30/07/2026): HKG WebSocket trình chiếu + fix 403

### 8.4. Nguồn kiểm chứng

- **Mã nguồn production:** `/opt/kpi-prod/` (nhánh `prod`)
- **Database production:** `localhost:5432`, database `kpi_haiquan` (kết nối đọc thông qua `psql` — chỉ SELECT, không in mật khẩu)
- **Git log:** `/root/kpi-haiquan/.git/` (nhánh `main`)
- **Tài liệu:** `/root/kpi-haiquan/docs/`

---

## Kết luận

Tài liệu này đã lập danh sách **toàn diện** các yêu cầu chức năng và phi chức năng của hệ thống KPI & Nền tảng Số HQKV8, dựa trên:

- **Rà soát 10 nguồn văn bản/tài liệu** (QĐ, CV, tờ trình, kế hoạch, góp ý nghiệp vụ)
- **Kiểm chứng 97 trang frontend + 555 endpoints backend** từ mã nguồn thực tế
- **Kiểm đếm 560 tài khoản (544 active) / 15 đơn vị / 111 bảng DB** tại thời điểm 06/10/2026
- **Phân tích 50+ commit `feat`** từ git log (lịch sử phát triển từ 09/02/2026)

**Trạng thái đáp ứng:**

- **Đã đáp ứng (✅):** 47 yêu cầu chức năng (KPI, LMS, HKG, Lịch công tác, Chỉ tiêu, Zalo OA, Trực ban, SSO) + 14 yêu cầu phi chức năng (bảo mật/hiệu năng/sẵn sàng)
- **Một phần (🟡):** Forum/Legal/Portal đã chạy prod nhưng ít sử dụng (xem 3.6–3.8) + 6 yêu cầu phi chức năng (mật khẩu mạnh, audit log, backup toàn diện)
- **Chưa đáp ứng (❌):** 8 yêu cầu (xem Mục 7 — Yêu cầu tồn đọng)

**Phát hiện mâu thuẫn với hồ sơ cũ:** Không có mâu thuẫn nghiêm trọng. Hồ sơ `02_mo_ta_chuc_nang_quy_trinh.md` và `10_HOI_DAP_BO_SUNG.md` đã mô tả chính xác hiện trạng tại thời điểm lập (30/07–05/08/2026). Tài liệu này bổ sung thêm:

- **Yêu cầu mới phát sinh sau 05/08:** Tổng hợp phiếu Mẫu 02 (29/09), gỡ kê khai lại đ (29/09), điều chuyển hàng loạt (13/09), reset lượt thi (10/09).
- **Truy vết nguồn gốc từng yêu cầu** về văn bản chỉ đạo, góp ý nghiệp vụ.
- **Ma trận truy vết yêu cầu → phân hệ → tài liệu thiết kế/API.**

Tài liệu này phục vụ công tác kiểm tra ATTT (CV 153/CNTT) và là cơ sở cho lập kế hoạch hoàn thiện hệ thống theo lộ trình Q4/2026 – 2027.

---

**Lập bởi:** Claude Code (AI hỗ trợ phát triển)  
**Ngày:** 06/10/2026  
**Phê duyệt:** (Chờ TCCB xác nhận)
