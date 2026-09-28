# Kế hoạch: chuyển kê khai d/đ/e của lãnh đạo từ THÁNG sang QUÝ

> Tiếp theo `08cf400` (live 28/09/2026). Ngày lập: 28/09/2026 · **DỰ THẢO, chờ duyệt**
>
> Yêu cầu: *"chỉnh sửa kê khai d đ e của lãnh đạo sang theo quý thay vì theo tháng"*.

---

## 1. Vì sao cần đổi

**Mẫu 02B (phiếu đánh giá lãnh đạo theo QUÝ)** ban hành kèm Công văn 21169 chỉ có
**một** ô cho mỗi chỉ số:

> *d. Điểm tỷ lệ % về kết quả hoạt động của lĩnh vực, bộ phận, đơn vị được giao lãnh đạo,
> quản lý, phụ trách (d): ……(%)* · *đ. Khả năng tổ chức triển khai thực hiện nhiệm vụ* ·
> *e. Năng lực tập hợp, đoàn kết công chức thuộc phạm vi quản lý*

Phần mềm hiện bắt lãnh đạo kê khai **ba lần mỗi quý** (mỗi tháng một bản), rồi khi
tính điểm quý lấy **MIN của ba tháng**. Hai hệ quả:

- Lãnh đạo làm ba lần việc mà biểu mẫu chỉ hỏi một lần.
- Cách lấy MIN là quy ước nội bộ, không có trong công văn: một tháng bị 50% kéo cả
  quý xuống 50% dù hai tháng còn lại đạt 100%.

Đã có một miếng vá cho chuyện này: lãnh đạo được **kê khai lại riêng chỉ số đ ở cấp
quý** trên phiếu quý (`PhieuDanhGiaQuy.dd_quy_ke_khai`, chỉ được nâng ≥ MIN). Miếng
vá này sẽ thừa khi d/đ/e chuyển hẳn sang quý.

---

## 2. Hiện trạng

### 2.1 Dữ liệu (đo trên production 28/09/2026)

| Nhóm | Số người |
|---|---|
| Phó đơn vị | 37 |
| Trưởng đơn vị | 13 |
| Phó Chi cục trưởng | 3 |
| Chi cục trưởng | 1 |
| **Tổng lãnh đạo** | **54** |
| Đã có bản d/đ/e nào đó trong quý III | 37 |

Bản ghi `danh_gia_dde` quý III: T7 31 bản (21 đã duyệt) · T8 22 bản (14 đã duyệt) ·
T9 19 bản (12 đã duyệt). Nghĩa là **mỗi quý phát sinh khoảng 70–90 bản** cho việc
mà biểu mẫu chỉ hỏi 54 lần.

### 2.2 Luồng hiện tại

```
Lãnh đạo tự kê (3 mức 100%/50% cho d, đ, e)   → NHAP
   ↓ gửi duyệt, chọn người duyệt
Cấp trên duyệt (ĐT duyệt Phó ĐT · CCT duyệt ĐT) → DA_PHE_DUYET
```

Bảng `danh_gia_dde`: khoá theo `(cong_chuc_id, thang, nam)`; có cột tự chấm
(`d_ket_qua_don_vi`…) và cột người duyệt chốt (`d_phe_duyet`…), `d_final` ưu tiên cột
duyệt.

### 2.3 Nơi d/đ/e được đọc

| Tệp | Dùng để |
|---|---|
| `core/kpi_lanh_dao_v2.py` | Điểm KPI **tháng** của lãnh đạo (V2) |
| `xep_loai_moi.py` | Điểm KPI tháng (nhánh V1) |
| `xep_loai_quy_helpers.py` `_lay_dde_thang` | Điểm **quý** — hiện lấy MIN 3 tháng |
| `bao_cao_xep_loai.py`, `export_bao_cao.py` | Báo cáo, xuất Excel |
| FE `LeaderAssessmentDDE.tsx` | Màn lãnh đạo tự kê (trong trang Kê khai) |
| FE `TabDanhGiaLD.tsx` | Màn cấp trên duyệt |
| FE `/danh-gia`, `TabBaoCao` | Hiển thị |

---

## 3. Cách làm đề xuất — neo vào THÁNG CUỐI QUÝ

Giống hệt cách đã làm cho tiêu chí chung ngày 18/09 và đang chạy ổn: **không tạo bảng
mới**. Từ mốc áp dụng, bản d/đ/e của quý nằm ở bản ghi `danh_gia_dde` của **tháng cuối
quý** (T12, T3, T6, T9), đánh dấu bằng cột mới `la_phieu_dde_quy`. Hai tháng còn lại
đọc xuyên sang qua một lớp resolver.

**Vì sao không tạo bảng riêng:** toàn bộ luồng tự kê → gửi duyệt → phê duyệt → trả lại
(39 chỗ trong `danh_gia_lanh_dao.py`), màn tự kê và màn duyệt của cấp trên được tái dùng
nguyên vẹn. Bảng mới nghĩa là viết lại tất cả cho đúng 54 người dùng.

**Dùng lại được ngay** hai thứ đã có sẵn từ đợt tiêu chí chung: hàm `thang_neo()` trong
`app/core/ky_tieu_chi.py` và bộ chọn kỳ ở frontend (`danhSachKyXemLai`, `kyMacDinh`).

---

## 4. Việc phải làm

### 4.1 Backend

| # | Việc | Tệp |
|---|---|---|
| 1 | Mốc `DDE_THEO_QUY_TU` + hàm `dde_theo_quy(thang, nam)` dùng chung với `thang_neo()` sẵn có | `core/ky_tieu_chi.py` |
| 2 | Cột `la_phieu_dde_quy BOOLEAN DEFAULT false` + migration (chỉ thêm cột) | `models/leader_kpi.py` |
| 3 | Tự kê / gửi duyệt / phê duyệt / trả lại: quy tháng gửi lên về tháng neo; chặn thao tác trên bản ghi không phải tháng neo | `danh_gia_lanh_dao.py` |
| 4 | `_lay_dde_thang` đọc xuyên sang bản ghi neo | `xep_loai_quy_helpers.py` |
| 5 | **Bỏ MIN 3 tháng**: từ mốc áp dụng, d/đ/e quý = giá trị trên phiếu quý. Kỳ cũ giữ nguyên MIN | `xep_loai_quy_helpers.py` |
| 6 | Điểm KPI **tháng** của lãnh đạo đọc d/đ/e từ bản ghi neo (xem mục 5, câu hỏi 2) | `kpi_lanh_dao_v2.py`, `xep_loai_moi.py` |
| 7 | Báo cáo + xuất Excel đọc qua resolver | `bao_cao_xep_loai.py`, `export_bao_cao.py` |

### 4.2 Frontend

| # | Việc | Tệp |
|---|---|---|
| 8 | Màn tự kê đổi nhãn sang kỳ quý, gửi tháng neo; banner "d/đ/e nay kê một lần cho cả quý" | `components/ke-khai/LeaderAssessmentDDE.tsx` |
| 9 | Màn duyệt của cấp trên: cột "Kỳ", lọc theo quý | `components/xep-loai/tabs/TabDanhGiaLD.tsx` |
| 10 | Chỗ hiển thị d/đ/e ghi rõ nguồn "(Quý N/NNNN)" | `/danh-gia`, `/danh-gia-v2`, `TabBaoCao` |

### 4.3 Kiểm thử

| # | Việc |
|---|---|
| 11 | Kỳ trước mốc (quý I, II/2026): điểm quý của 54 lãnh đạo trước và sau thay đổi phải giống hệt |
| 11b | Quý III: đối chiếu điểm của cả 54 lãnh đạo trước và sau — theo phép đo mục 5b phải KHÔNG ai đổi điểm; ai lệch thì dừng lại xem xét |
| 12 | Kỳ mới: kê ở tháng nào trong quý cũng ghi vào bản ghi tháng neo; ba tháng đọc ra cùng giá trị |
| 13 | d/đ/e quý = giá trị phiếu quý, KHÔNG còn là MIN ba tháng |
| 14 | Luồng duyệt: Phó ĐT gửi → ĐT duyệt; chặn thao tác trên bản ghi không phải tháng neo |

---

## 5. Quyết định của người dùng (28/09/2026)

| Vấn đề | Quyết định |
|---|---|
| Mốc áp dụng | **Từ Quý III/2026 — hồi tố** quý đang dở |
| d/đ/e của từng tháng | **Ba tháng dùng chung giá trị quý** (như tiêu chí chung) |
| Miếng vá "kê khai lại đ cấp quý" | **Giữ** làm đường điều chỉnh bổ sung |
| Dữ liệu d/đ/e theo tháng đã có | **Giữ nguyên** để tra cứu, không xoá không sửa |

---

## 5b. Đo tác động của việc hồi tố Quý III — gần như bằng KHÔNG

Tháng neo của quý III là **tháng 9**, mà tháng 9 đã có sẵn 19 bản d/đ/e (12 đã duyệt).
Nghĩa là các bản tháng 9 hiện có **trở thành phiếu quý III luôn**, không ai phải nhập
lại. Đo trên production ngày 28/09:

| Phép đo | Kết quả |
|---|---|
| Lãnh đạo có d/đ/e trong quý III | 37 / 54 |
| Bản tháng 7 + tháng 8 đã duyệt | 35 |
| Trong đó **lệch** so với bản tháng 9 của cùng người | **2** |
| Lãnh đạo có bản T7/T8 nhưng **không có bản tháng 9** | 15 |
| Lãnh đạo có chỉ số 50% trong quý III | **4** |

Hai bản lệch duy nhất, và cả hai đều **không làm đổi điểm quý**:

| Mã CC | Tháng | d/đ/e tháng | d/đ/e tháng 9 (phiếu quý) |
|---|---|---|---|
| 20ZZ-0433 Nguyễn Mạnh Toàn | 7 | 100 · 100 · 100 | **50** · 100 · 100 |
| 20ZZ-0229 Lê Thanh Long | 7 | 100 · 100 · 100 | 100 · **50** · 100 |

Điểm quý hiện tính bằng **MIN ba tháng** nên hai người này vốn đã nhận 50% ở chỉ số
tương ứng; sau khi đổi sang "lấy thẳng phiếu quý" họ vẫn 50%. **Không ai đổi điểm.**

Với 15 người chưa có bản tháng 9: hiện MIN ba tháng của họ đều là 100% (không ai có
chỉ số 50), nên sau khi đổi, d/đ/e quý đọc ở tháng 9 chưa có → vẫn mặc định 100%.
Cũng **không ai đổi điểm** — nhưng nhóm này nên được nhắc kê phiếu quý III cho đủ hồ sơ.

> Kết luận: hồi tố quý III an toàn. Rủi ro thực tế nằm ở chỗ khác — 2 bản đang ở
> trạng thái CHỜ DUYỆT có chỉ số 50% (20ZZ-0185 tháng 9, 20ZZ-0231 tháng 7). Bản tháng
> 9 của 20ZZ-0185 khi được duyệt sẽ thành d = 50% cho cả quý III; bản tháng 7 của
> 20ZZ-0231 sẽ **không còn được tính** vì tháng 7 không phải tháng neo. Cần báo người
> duyệt biết trước.

---

## 6. Ước lượng

| Phần | Thời gian |
|---|---|
| Backend: mốc + cột + luồng tự kê/duyệt theo tháng neo | 0,75 ngày |
| Backend: resolver cho 5 điểm đọc + bỏ MIN ba tháng | 0,5 ngày |
| Frontend: màn tự kê, màn duyệt, nhãn kỳ | 0,5 ngày |
| Kiểm thử + phát hành | 0,25 ngày |
| **Tổng** | **~2 ngày** |

Migration chỉ thêm một cột mặc định `false`, không đụng dữ liệu. Quay lui bằng cách
đặt mốc `DDE_THEO_QUY_TU` ra xa — như cách `TC_THEO_QUY_TU` đang làm.
