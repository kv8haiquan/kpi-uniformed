# Kế hoạch: chuyển trang Đối soát sang kỳ QUÝ

> Ngày lập: 29/09/2026 · **DỰ THẢO, chờ duyệt** · Tiếp theo `60b8932` (live 29/09)
>
> Trang `/doi-soat` (`doi_soat_danh_gia.py`) là công cụ TCCB tự phục vụ: mỗi kỳ ai
> CHƯA hoàn tất kê khai / duyệt. Từ Q3/2026 kỳ đánh giá đã sang QUÝ nhưng trang này
> vẫn chỉ có **theo THÁNG**.

---

## 1. Năm phát hiện khi đo trên production (29/09/2026, chỉ đọc)

### 1.1 Trang gắn nhãn THÁNG nhưng đã trả số liệu QUÝ

Phần tiêu chí chung trong đối soát đã được vá để đọc theo **tháng neo** (`thang_neo`),
nên mở đối soát tháng 7, tháng 8 hay tháng 9 đều đang trả về **tình trạng của phiếu
quý III**. TCCB mở tháng 7 thấy "16 người chờ duyệt tiêu chí chung" và tưởng đó là số
của tháng 7 — thực ra là số của cả quý.

| Kỳ mở | Tổng ca | chưa kê khai CV | HĐ111 chờ duyệt | TC chưa kê khai | TC chờ duyệt | điểm 0 |
|---|---|---|---|---|---|---|
| Tháng 7/2026 | 188 | 4 | 4 | 19 | 16 | 145 |
| Tháng 8/2026 | 224 | 9 | 5 | 15 | 16 | 174 |
| Tháng 9/2026 | 127 | 8 | 12 | 16 | 16 | 72 |

Cột "TC chờ duyệt" bằng nhau ở cả ba tháng chính là dấu hiệu đó.

### 1.2 Nhóm "điểm 0" đang **báo động giả 66/72 ca**

Nhóm này đọc `bao_cao_xep_loai` **THÁNG**. Từ Q3/2026 kỳ tháng hết hiệu lực, báo cáo
tháng chỉ còn là **bản nháp tự dựng** (13 bản tháng 9, tất cả `NHAP`) và không ai tính
lại, nên số liệu đóng băng ở thời điểm dựng.

Đo tháng 9: báo cáo tháng ghi "tiêu chí chung = 0" cho **99 người**, nhưng **66 người
trong số đó thực tế đã được duyệt tiêu chí chung quý III với điểm > 0**. Tức phần lớn
nhóm "điểm 0" hiện nay là rác:

| Lý do trong nhóm "điểm 0" tháng 9 | Số ca |
|---|---|
| tiêu chí chung = 0 | 44 |
| KPI = 0 + tiêu chí chung = 0 | 22 |
| KPI = 0 (đã kê khai nhưng SP chưa đạt/chưa duyệt) | 6 |

### 1.3 Thiếu hẳn ba thứ mà kỳ quý mới có

Đối soát hiện chỉ kiểm: kê khai công việc, VB714 của HĐ 111, tiêu chí chung, điểm 0.
Ba việc quyết định hồ sơ quý thì **không kiểm gì cả**:

| Việc | Số liệu quý III (đo 29/09) |
|---|---|
| **Phiếu Mẫu 02** chưa gửi hoặc kẹt duyệt | 8 nháp · 6 bị từ chối · **294 chờ duyệt** · 146 đã duyệt · **92 người chưa soạn** |
| **d/đ/e của lãnh đạo** (Mẫu 02B) | chỉ 20/55 lãnh đạo có phiếu quý III — **35 người chưa kê**; trong 20 bản thì 8 còn chờ duyệt |
| **Báo cáo xếp loại QUÝ** theo đơn vị | **13/13 đơn vị còn ở trạng thái NHAP**, chưa đơn vị nào gửi duyệt |

Hạn nộp hồ sơ là ngày 23 tháng cuối quý. Đây đúng là ba thứ TCCB phải đi đòi.

### 1.4 Tài khoản quản trị lọt vào bảng ở **cả ba tháng**

`doi_soat_danh_gia.py:185` lọc theo **mã vai trò** (`{"TCCB", "SUPER_ADMIN"}`), nhưng
tài khoản quản trị mang mã `ADMIN` còn *cấp bậc* mới là `SUPER_ADMIN`. Kết quả:
`ADMIN-001` xuất hiện ở T7, T8, T9 với chi tiết "Chưa có bản tiêu chí chung (lãnh đạo)".
Đúng lỗi đã gặp ở đợt `60b8932` — sửa bằng cách lọc theo **cấp bậc**.

### 1.5 Kê khai công việc quý III bị cắt ở 15/9

Mốc `MOC_CHUYEN_KY_KE_KHAI` (live `08cf400`): kê khai từ 16/9/2026 thuộc quý IV. Đối
soát theo quý phải dùng `cac_thang_ke_khai_cua_quy(quy, nam)` chứ không phải ba tháng
trơn, nếu không quý III sẽ tính nhầm cả phần đã chuyển sang quý IV.

---

## 2. Cách làm đề xuất

### 2.1 Bộ chọn kỳ dùng chung

Thay ô chọn tháng bằng **bộ chọn kỳ đã có sẵn** (`danhSachKyXemLai`, `kyMacDinh` trong
`lib/ky-tieu-chi.ts`) — giống trang Đánh giá và Tiêu chí chung: năm 2026 ra *Tháng 1…7 ·
Quý III · Quý IV*, mặc định quý hiện hành. Chọn tháng cũ vẫn chạy đúng logic tháng như
hôm nay (số liệu lịch sử), chọn quý thì chạy logic quý.

Backend giữ endpoint tháng hiện có, **thêm** `GET /doi-soat-danh-gia/quy/{quy}/nam/{nam}`
và `.../export` song song. Không đụng đường cũ → không có rủi ro hồi quy cho kỳ tháng.

### 2.2 Các nhóm khi kỳ là QUÝ

| Nhóm | Nguồn | Ghi chú |
|---|---|---|
| `cc_chua_ke_khai_cv` | `ke_khai_cong_viec` theo `cac_thang_ke_khai_cua_quy` | ghi rõ **thiếu tháng nào** ("thiếu T7, T9") vì kê khai vẫn theo tháng |
| `hd111_chua_ke_khai` · `hd111_cho_duyet` | `hdld_danh_gia` từng tháng của quý | nêu rõ tháng nào còn kẹt |
| `tcc_chua_ke_khai` · `tcc_cho_duyet` | `danh_gia_thang` tại **tháng neo** | một phiếu cho cả quý — giữ nguyên cách đọc hiện tại |
| **`dde_chua_ke_khai`** (mới) | `danh_gia_dde` tại tháng neo, chỉ lãnh đạo | 35 người đang thiếu |
| **`dde_cho_duyet`** (mới) | như trên, trạng thái `CHO_PHE_DUYET` | 8 bản |
| **`phieu02_chua_gui`** (mới) | `phieu_danh_gia_quy` — chưa soạn / `NHAP` / `BI_TU_CHOI` | 92 + 8 + 6 |
| **`phieu02_cho_duyet`** (mới) | `phieu_danh_gia_quy` = `CHO_PHE_DUYET`, kèm **người cần duyệt** | 294 bản |
| `diem_bat_thuong` | đổi sang `bao_cao_xep_loai_quy` | bỏ nguồn báo cáo tháng — chính chỗ đẻ ra 66 báo động giả |

Giữ nguyên cơ chế **ưu tiên**: một người chỉ nằm ở đúng một nhóm, các vấn đề còn lại
gộp vào cột chi tiết. Thứ tự ưu tiên đề xuất: chưa kê khai (CV → VB714 → TC → d/đ/e →
phiếu 02) trước, rồi tới các nhóm chờ duyệt, cuối cùng là lưới an toàn "điểm 0".

### 2.3 Khối "Báo cáo xếp loại quý theo đơn vị"

Báo cáo là việc ở **mức đơn vị**, không phải mức người, nên không trộn vào danh sách.
Đề xuất một khối gọn ở đầu trang: 15 đơn vị × trạng thái báo cáo quý (NHAP / chờ duyệt /
đã duyệt), để TCCB thấy ngay đơn vị nào chưa gửi. Hiện là **13/13 chưa gửi**.

---

## 3. Việc phải làm

### 3.1 Backend

| # | Việc | Tệp |
|---|---|---|
| 1 | Lọc diện đánh giá theo **cấp bậc** thay vì mã vai trò (bỏ `ADMIN-001` khỏi bảng) — áp cho **cả** đường tháng lẫn đường quý | `doi_soat_danh_gia.py` |
| 2 | Tách phần thu thập thành hàm dùng chung; thêm `_thu_thap_doi_soat_quy(db, quy, nam, don_vi_id)` | `doi_soat_danh_gia.py` |
| 3 | Bốn nhóm mới: `dde_chua_ke_khai`, `dde_cho_duyet`, `phieu02_chua_gui`, `phieu02_cho_duyet` + `NHOM_META` tương ứng | `doi_soat_danh_gia.py` |
| 4 | `diem_bat_thuong` của kỳ quý đọc `bao_cao_xep_loai_quy` | `doi_soat_danh_gia.py` |
| 5 | Kê khai công việc quý dùng `cac_thang_ke_khai_cua_quy` (tôn trọng mốc 16/9) | `doi_soat_danh_gia.py` |
| 6 | Khối tổng hợp báo cáo quý theo đơn vị | `doi_soat_danh_gia.py` |
| 7 | `GET /quy/{quy}/nam/{nam}` + `/export` (Excel cùng dạng sheet phẳng) | `doi_soat_danh_gia.py` |

### 3.2 Frontend

| # | Việc | Tệp |
|---|---|---|
| 8 | Bộ chọn kỳ dùng chung (Tháng 1–7 · Quý III · Quý IV), mặc định quý hiện hành | `app/(main)/doi-soat/page.tsx` |
| 9 | Gọi endpoint quý khi kỳ là quý; nhãn tiêu đề và tên tệp Excel theo kỳ | `page.tsx`, `services/doi-soat.service.ts` |
| 10 | Khối "Báo cáo xếp loại quý theo đơn vị" | `page.tsx` |
| 11 | Nhóm mới hiển thị kèm người cần duyệt (như `tcc_cho_duyet` đang làm) | `page.tsx` |

### 3.3 Kiểm thử

| # | Việc |
|---|---|
| 12 | Kỳ THÁNG cũ (T1–T6/2026) cho kết quả **y hệt trước khi sửa**, trừ việc mất dòng `ADMIN-001` |
| 13 | Kỳ quý: mỗi người chỉ nằm ở đúng một nhóm; tổng các nhóm = tổng số ca |
| 14 | `dde_*` chỉ chứa lãnh đạo; `phieu02_*` không chứa CCT (CCT không có phiếu) |
| 15 | Kê khai quý III không đếm phần từ 16/9; quý IV có đếm |
| 16 | `diem_bat_thuong` quý đọc báo cáo quý — đối chiếu không còn 66 ca báo động giả |
| 17 | Quyền: CC thường và Trưởng đơn vị bị 403 ở cả hai đường |

---

## 4. Cần anh/chị quyết

| # | Câu hỏi | Đề xuất của tôi |
|---|---|---|
| A | Giữ luôn cả kỳ THÁNG (xem lại T1–T7) hay bỏ hẳn, chỉ còn quý? | **Giữ cả hai** — nhất quán với trang Đánh giá, và tháng 1–7 vẫn là hồ sơ thật |
| B | Có thêm khối "báo cáo xếp loại quý theo đơn vị" không? | **Có** — 13/13 đơn vị chưa gửi, đây là việc đọng lớn nhất hiện nay |
| C | Nhóm "điểm 0" của kỳ quý đọc báo cáo quý, mà 13 báo cáo quý III đều còn NHAP. Chấp nhận số liệu nháp? | **Chấp nhận**, nhưng ghi rõ trên giao diện "nguồn: báo cáo quý bản nháp" |
| D | `phieu02_cho_duyet` đang có 294 ca — có nên gộp theo **người duyệt** thay vì liệt kê 294 dòng? | **Gộp theo người duyệt** ở phần tổng hợp, vẫn giữ danh sách chi tiết bên dưới |

---

## 5. Ước lượng

| Phần | Thời gian |
|---|---|
| Backend: tách hàm, 4 nhóm mới, đổi nguồn điểm 0, endpoint quý + Excel | 1 ngày |
| Frontend: bộ chọn kỳ, khối báo cáo đơn vị, nhóm mới | 0,5 ngày |
| Kiểm thử + phát hành | 0,5 ngày |
| **Tổng** | **~2 ngày** |

Không có migration. Toàn bộ thay đổi là **đọc** — trang đối soát không ghi gì vào
dữ liệu KPI.
