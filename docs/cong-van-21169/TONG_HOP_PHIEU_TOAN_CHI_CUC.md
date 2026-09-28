# Xem phiếu Mẫu 02 của toàn Chi cục

> Ngày lập: 29/09/2026 · Nhánh `feature/kpi-phieu-tong-hop`, dựng trên prod `fe71cea`
>
> Câu hỏi của người dùng: *"mẫu 02 của công chức/lãnh đạo có cách nào để xem được kê
> khai của toàn chi cục không?"* — Câu trả lời lúc rà: **không có cách nào**, kể cả
> Chi cục trưởng.

---

## 1. Hiện trạng trước khi sửa (đo trên production 28/09/2026)

Quyền xem phiếu nằm ở hai nơi dùng chung một ma trận: `phieu_danh_gia_quy._co_quyen_duyet`
và `in_bang_ke._load_cc_cho_in_boi_tdv`. Cả hai đều bám theo phạm vi **DUYỆT**, nên ai
không duyệt phiếu của người khác thì không xem được phiếu của người đó.

| Vai trò | Xem được phiếu của | Số phiếu quý III thực tế xem được |
|---|---|---|
| Trưởng đơn vị | CC + Phó ĐV **cùng đơn vị** | phần của đơn vị mình |
| Chi cục trưởng | **chỉ** TDV + PCCT | **7 / 450** |
| Phó Chi cục trưởng | — (403) | 0 |
| TCCB | — (không có nhánh nào) | 0 |
| Cờ `can_view_all_units` | — (chỉ ăn ở *báo cáo xếp loại*) | 0 |

Quý III/2026 có 450 phiếu: 417 của công chức, 22 của Phó ĐV, 7 của Trưởng ĐV. Tức
**439/450 phiếu chỉ mỗi Trưởng đơn vị của người đó nhìn thấy**, trong khi TCCB là nơi
phải tổng hợp hồ sơ nộp trước ngày 23 tháng cuối quý.

Báo cáo xếp loại quý đã cho CCT/PCCT/TCCB xem **điểm + xếp loại** toàn Chi cục, nhưng
không có phần chữ của Mẫu 02: ưu điểm, hạn chế khuyết điểm, cá nhân tự đề xuất, ý kiến
lãnh đạo, đề xuất và quyết định xếp loại.

---

## 2. Quyết định 29/09/2026

| Vấn đề | Quyết định |
|---|---|
| Ai được xem toàn Chi cục | **CCT, PCCT, TCCB** và cờ `can_view_all_units` |
| Quyền đó gồm gì | **CHỈ ĐỌC** — xem và tải bản in, không duyệt, không sửa |
| Trưởng đơn vị xem đơn vị khác | **KHÔNG** — phiếu chứa nhận xét cá nhân và phần hạn chế, khuyết điểm |
| Tải hàng loạt (ZIP 543 tệp .docx) | **Chưa làm** — nặng, và dev lẫn prod dùng chung một máy |

---

## 3. Đã làm

### 3.1 Nới quyền

- `app/core/quyen_xem_phieu.py` (mới) — một chỗ duy nhất trả lời "ai xem được toàn Chi cục".
- `in_bang_ke._load_cc_cho_in_boi_tdv` gọi hàm đó: người xem toàn Chi cục tải được phiếu
  và bảng kê của **mọi** công chức. Hai endpoint phiếu THÁNG dùng chung hàm này nên cũng
  được mở theo.
- Quyền **duyệt** không đụng tới: `_co_quyen_duyet` giữ nguyên, có test khoá lại.

### 3.2 Trang tổng hợp

- `GET /phieu-danh-gia-quy/toan-chi-cuc` — lọc theo đơn vị / trạng thái / xếp loại / tìm
  theo tên hoặc mã, phân trang, kèm `tong_hop` đếm trên **toàn bộ** kết quả lọc.
- `GET /phieu-danh-gia-quy/toan-chi-cuc/export` — Excel một sheet phẳng, 17 cột, trọn bộ
  kết quả lọc (không phân trang).
- Trang `/phieu-tong-hop` — bảng toàn Chi cục, thẻ đếm theo trạng thái, modal xem thẳng
  nội dung Mẫu 02 mà không phải tải .docx, nút tải phiếu và bảng kê từng người.
- Mục "Tổng hợp phiếu 02" trên sidebar, cùng nhóm quyền với Đối soát đánh giá.

> **Người CHƯA soạn phiếu vẫn có một dòng** (trạng thái "Chưa gửi", `id = null`). Đây là
> nhóm TCCB cần thấy nhất khi đi đòi hồ sơ, nên không được lọc mất.

---

## 4. Kiểm chứng

- `tests/integration/test_phieu_tong_hop.py` — **12/12 PASS**, toàn bộ chỉ đọc.
- Toàn bộ backend: **154 PASS / 2 FAIL** — hai test đỏ sẵn từ trước
  (`test_cct_no_assignment_empty_scope`, `test_bao_cao_da_phe_duyet_bao_400`).
- Đo trên bản sao dữ liệu prod: bảng tổng hợp **542 dòng trong 0,19s**; Excel **109 KB
  trong 0,33s**. `npx tsc --noEmit` sạch, build Next.js PASS.

Một lỗi thật phát hiện khi viết test: lọc "ai không có phiếu" theo **mã vai trò**
(`TCCB`, `SUPER_ADMIN`) để lọt tài khoản quản trị vào bảng, vì tài khoản đó mang mã
`ADMIN` mà cấp bậc mới là `SUPER_ADMIN`. Đã đổi sang lọc theo **cấp bậc**.

> `doi_soat_danh_gia.py` đang lọc đúng theo cách cũ (`KHONG_DANH_GIA = {"TCCB",
> "SUPER_ADMIN"}` so với `ma_vai_tro`) nên nhiều khả năng tài khoản admin cũng lọt vào
> bảng đối soát. Chưa sửa vì ngoài phạm vi đợt này — cần xác nhận trước.

---

## 5. Còn nợ

- Tải hàng loạt .docx theo ZIP (cách 3 người dùng gác lại).
- Đối soát theo **QUÝ** — trang đối soát hiện chỉ có theo tháng, trong khi từ Q3/2026 kỳ
  đánh giá đã chuyển sang quý.
