# Mục 3 — Danh mục sản phẩm/công việc, tiêu chí đánh giá, công thức tính điểm, hệ số quy đổi, quy tắc xếp loại

> Phục vụ công văn 153/CNTT ngày 08/7/2026. Lập ngày 30/07/2026.
> Số liệu trích trực tiếp từ database production và mã nguồn (kèm vị trí file để đoàn kiểm tra đối chiếu).

## 1. Danh mục sản phẩm/công việc

### 1.1. Danh mục công việc chuẩn (`danh_muc_sp_cong_viec`) — 2.812 đầu việc đang áp dụng

Xây dựng theo **Phụ lục III** (danh mục vị trí việc làm/công việc ngành Hải quan), phân theo **16 lĩnh vực**:

| Lĩnh vực | Số đầu việc |
|---|---|
| I — Quản lý điều hành, hành chính, văn phòng | 287 |
| II — Hợp tác quốc tế | 42 |
| III — Công tác Đảng | 122 |
| IV — Tổ chức, cán bộ | 225 |
| V — Kiểm tra, PCTN và giải quyết KNTC | 115 |
| VI — Tài vụ - Quản trị | 429 |
| VII — CNTT và Thống kê hải quan | 533 |
| VIII — Đổi mới và chiến lược hải quan | 56 |
| IX — Pháp chế | 228 |
| X — Giám sát quản lý | 181 |
| XI — Thuế XNK | 188 |
| XII — Điều tra chống buôn lậu | 67 |
| XIII — Kiểm tra sau thông quan | 102 |
| XIV — Quản lý rủi ro | 113 |
| XV — Kiểm định | 124 |
| (Chưa gắn lĩnh vực — danh mục bổ sung) | 52 |

Mỗi đầu việc gắn: nhiệm vụ, công việc chi tiết, sản phẩm đầu ra, **nhóm phức tạp PL3 (1–5)**, khung điểm tối đa, điểm chấm, **hệ số quy đổi**.

### 1.2. Nhóm công việc PL3 (`nhom_cong_viec_pl3`) — 5 nhóm phức tạp

| Nhóm | Tên | Điểm tối đa | Số đầu việc đang gắn |
|---|---|---|---|
| 1 | Đơn giản | 100 | 570 |
| 2 | Thông thường | 200 | 1.312 |
| 3 | Nâng cao | 300 | 639 |
| 4 | Phức tạp | 400 | 263 |
| 5 | Đặc thù | 500 | 28 |

### 1.3. Sản phẩm chuẩn (`sp_cong_viec_chuan`) và cấp độ phức tạp (`cap_do_phuc_tap`) — dùng cho công thức V1 (trước 04/2026)

| Mã | Sản phẩm chuẩn | Thời gian chuẩn | Hệ số quy đổi về SP1 |
|---|---|---|---|
| SP1 | Tờ khai HQ kiểm tra chi tiết hồ sơ (SP gốc) | 5 phút | 1 |
| SP2 | Văn bản hành chính | 60 phút | 12 |
| SP3 | Giờ trực làm việc | 60 phút | 12 |
| SP4 | Giờ tuần tra kiểm soát | 60 phút | 12 |

| Cấp độ | Tên | Hệ số nhân SP1 | Hệ số nhân SP2-4 |
|---|---|---|---|
| C1 | Dễ - Đơn giản | 1 | 1 |
| C2 | Trung bình - Thông thường | 4 | 2 |
| C3 | Khó - Nâng cao | 12 | 4 |
| C4 | Rất khó - Phức tạp | 24 | 8 |
| C5 | Theo thực tế | Lãnh đạo quyết định theo thực tế | — |

## 2. Hệ số quy đổi (công thức V2_PL3 — áp dụng từ tháng 04/2026)

- Đơn vị điểm cơ sở: **1 SP1 = 25 điểm** (`task_catalog.py`).
- Hệ số quy đổi mỗi đầu việc: `he_so_quy_doi = diem_cham / 25` (lưu sẵn trong `danh_muc_sp_cong_viec.he_so_quy_doi`).
- Số sản phẩm gốc quy đổi mỗi dòng kê khai: `so_sp_goc_quy_doi = so_luong × he_so_quy_doi` (`app/core/kpi_calculator_v2.py:34-58`).
- Công thức V1 cũ (trước 04/2026, còn dùng cho dữ liệu lịch sử): mẫu số = `số ngày làm việc × 96 SP/ngày` (`xep_loai_quy_helpers.py:77`).

## 3. Tiêu chí đánh giá

### 3.1. Bộ tiêu chí chung hằng tháng (`tieu_chi_chung`) — 3 nhóm, 10 tiêu chí chấm điểm, tổng 30 điểm

| Mã | Tiêu chí | Điểm tối đa |
|---|---|---|
| **Nhóm 1 — Phẩm chất, kỷ luật (10 điểm)** | | |
| 1.1 | Phẩm chất chính trị, đạo đức, văn hóa thực thi công vụ *(8 nội dung thành phần 1.1a1–1.1a8)* | 5,0 |
| 1.2 | Ý thức kỷ luật, kỷ cương trong thực thi công vụ *(4 nội dung thành phần 1.2b1–1.2b4)* | 5,0 |
| **Nhóm 2 — Năng lực, trách nhiệm (10 điểm)** | | |
| 2.1 | Năng lực chuyên môn, nghiệp vụ theo vị trí việc làm | 2,5 |
| 2.2 | Khả năng đáp ứng yêu cầu thực thi nhiệm vụ được giao | 2,5 |
| 2.3 | Tinh thần trách nhiệm trong thực thi công vụ | 2,5 |
| 2.4 | Thái độ phục vụ Nhân dân, doanh nghiệp và khả năng phối hợp | 2,5 |
| **Nhóm 3 — Sáng tạo, đột phá (10 điểm)** | | |
| 3.1 | Có sản phẩm, giải pháp đột phá, sáng tạo | 2,5 |
| 3.2 | Sẵn sàng tham gia nhiệm vụ chính trị đặc biệt quan trọng | 2,5 |
| 3.3 | Tinh thần chịu trách nhiệm trước kết quả công việc | 2,5 |
| 3.4 | Chủ động quyết định trong phạm vi thẩm quyền | 2,5 |

- Cách chấm: công chức **tự chấm theo bội số 0,5**; lãnh đạo phê duyệt/điều chỉnh 2 cấp; CCT có quyền điều chỉnh cuối (lưu lịch sử).
- Nhóm 1–2 mặc định "đạt", nhóm 3 mặc định "không đạt" (phải có minh chứng mới được điểm).

### 3.2. Bộ tiêu chí Hội đồng đánh giá lãnh đạo (`hdld_tieu_chi`, `danh_gia_dde`)

6 nhóm chức danh (I–VI), mỗi nhóm 3 tiêu chí × 100 điểm: **Chất lượng công việc — Tuân thủ quy định, quy trình — Hiệu quả công việc**. Kết quả tạo thành 3 thành phần d, đ, e trong công thức KPI lãnh đạo (điểm/100; thiếu đánh giá thì mặc định 1,0).

## 4. Công thức tính điểm KPI

### 4.1. Công chức (V2_PL3, từ 04/2026) — `app/core/kpi_calculator_v2.py`

```
Trừ lỗi (mỗi dòng kê khai):
  sp_đạt = hệ_số × (số_lượng − 0,25 × min(số_lần_lỗi, số_lượng × 4))
  → mỗi lỗi trừ 25% của 1 đơn vị sản phẩm, tối đa 4 lỗi/đơn vị (trừ hết 100%), kết quả không âm

Ba tỷ lệ thành phần (trên tổng kê khai ĐÃ PHÊ DUYỆT trong tháng):
  a = Σ SP hoàn thành / Σ SP kê khai      (tỷ lệ số lượng)
  b = Σ SP đạt chất lượng / Σ SP kê khai  (tỷ lệ chất lượng)
  c = Σ SP đạt tiến độ / Σ SP kê khai     (tỷ lệ tiến độ)

Điểm KPI tháng = (a + b + c) / 3 × 70
Tổng điểm tháng = Điểm KPI (tối đa 70) + Điểm tiêu chí chung (tối đa 30) = 100
Trường hợp không có kê khai được duyệt (mẫu số = 0): KPI = 0 → xếp loại D
```

### 4.2. Lãnh đạo (V2, từ 04/2026) — `app/core/kpi_lanh_dao_v2.py`

Phạm vi sản phẩm tính gộp theo cấp:

| Cấp | Phạm vi cộng sản phẩm |
|---|---|
| PDV | SP tự kê + SP của công chức do PDV trực tiếp duyệt |
| TDV | Toàn bộ SP của đơn vị (CC + PDV + tự kê) |
| PCCT | Gộp SP các đơn vị mình phụ trách |
| CCT | Gộp SP các khối PCCT phụ trách + đơn vị trực tiếp phụ trách |

```
KPI lãnh đạo = (a + b + c + d + đ + e) / 6 × 70
  a, b, c: như công chức, tính trên phạm vi gộp ở trên
  d, đ, e: điểm Hội đồng đánh giá (danh_gia_dde, /100; thiếu → 1,0; chỉ lấy bản đã phê duyệt)
Điều chỉnh KQCV (dieu_chinh_kqcv) chỉ ảnh hưởng KPI lãnh đạo, tính lại theo cùng quy tắc trừ 25%/lỗi
```

### 4.3. Điểm quý — `xep_loai_quy_helpers.py`

```
Tiêu chí chung quý = trung bình cộng các THÁNG THỰC TẾ làm việc
a, b, c quý (CC)  = lũy kế Σ tử / Σ mẫu của 3 tháng
a, b, c quý (LĐ)  = trung bình có trọng số; d, đ, e quý = MIN của 3 tháng
KPI quý (CC) = (a+b+c)/3 × 70;  KPI quý (LĐ) = (a+b+c+d+đ+e)/6 × 70
Tổng điểm quý = Tiêu chí chung quý + KPI quý
Loại trừ: tháng nghỉ thai sản trọn tháng; tháng trước ngày vào Chi cục. Không có tháng thực tế → không xếp loại
```

## 5. Quy tắc xếp loại và kiểm soát tỷ lệ

### 5.1. Ngưỡng xếp loại (tháng và quý) — `bao_cao_xep_loai.py:68-97`

| Loại | Ngưỡng tổng điểm | Ý nghĩa |
|---|---|---|
| **A** | ≥ 90 | Hoàn thành xuất sắc nhiệm vụ |
| **B** | 70 – dưới 90 | Hoàn thành tốt nhiệm vụ |
| **C** | 50 – dưới 70 | Hoàn thành nhiệm vụ |
| **D** | < 50 | Không hoàn thành nhiệm vụ |

### 5.2. Kiểm soát tỷ lệ loại A — `bao_cao_xep_loai.py:343-359`

- **Số công chức loại A ≤ 20% số công chức loại B** (trong phạm vi báo cáo xếp loại).
- Có loại A mà không có loại B → vi phạm.
- Hệ thống tự cảnh báo vi phạm tỷ lệ trên bảng xếp loại; Chi cục trưởng quyết định điều chỉnh trước khi chốt.

### 5.3. Xếp loại đánh giá năng lực/chứng chỉ LMS — `lms_service/schemas/chung_chi.py`

| Xếp loại | Ngưỡng điểm |
|---|---|
| Xuất sắc | ≥ 90 |
| Giỏi | ≥ 80 |
| Khá | ≥ 65 |
| Đạt | ≥ 50 |
| Không đạt | < 50 |

- Điểm bài kiểm tra/kỳ thi: chấm tự động, lấy **điểm cao nhất (best-score)** giữa các lượt làm hợp lệ; ngưỡng đạt từng bài do giảng viên cấu hình.
- Chứng chỉ cấp tự động khi hoàn thành khóa học/kỳ thi (mã số tự tăng dạng `CC000001`).

## 6. Bảng tham số/cấu hình nghiệp vụ đang áp dụng (tra cứu nhanh)

| Tham số | Giá trị | Nguồn |
|---|---|---|
| Điểm cơ sở 1 SP1 | 25 điểm | `task_catalog.py` |
| SP chuẩn/ngày (công thức V1) | 96 SP | `xep_loai_quy_helpers.py:77` |
| Mức trừ mỗi lỗi CL/TĐ | 25% / lỗi, tối đa 4 lỗi/đơn vị | `kpi_calculator_v2.py:26-31` |
| Trọng số KPI / Tiêu chí chung | 70 / 30 | `assessment.py` |
| Ngưỡng A/B/C/D | 90 / 70 / 50 | `bao_cao_xep_loai.py` |
| Trần loại A | ≤ 20% số loại B | `bao_cao_xep_loai.py:347` |
| Công thức lãnh đạo V2 áp dụng từ | Tháng 04/2026 | `kpi_lanh_dao_v2.py:53-54` |
| Bước điểm tự chấm tiêu chí chung | Bội số 0,5 | v3.6 (05/2026) |
| Hạn token đăng nhập | 480 phút | `config.py:72` |
