# Kế hoạch nâng cấp phần mềm KPI theo Công văn 21169

> **Căn cứ:**
> - Công văn số **21169/CHQ-TCCB** ngày 28/8/2026 của Cục Hải quan — đánh giá, xếp loại theo quý, năm (bản scan 25 trang: `docs/KPI-new/Cong van/VB_21169.pdf`)
> - Công văn triển khai của Chi cục HQKV VIII (đã ký, Chi cục trưởng Phạm Quốc Hưng): `docs/KPI-new/Cong van/Chi cục/CV trien khai DGXL_HQKV8 (ký).docx`
> - Mẫu số 02A (công chức) / 02B (lãnh đạo) — phiếu đánh giá, xếp loại **theo quý**
>
> Ngày lập: 18/09/2026 · **Bản 2** (viết lại sau khi có văn bản gốc) · Trạng thái: chờ duyệt phạm vi đợt P0

---

## 0. Việc gấp nhất

CV Chi cục, mục II.4:

> *"Từ quý III/2026, kỳ đánh giá, xếp loại trên Phần mềm được thiết lập theo quý. Giao Phòng Tổ chức cán bộ chủ trì, phối hợp với Phòng Công nghệ thông tin nâng cấp, hoàn thiện Phần mềm đánh giá KPI nội bộ… (**hoàn thành trước kỳ đánh giá quý III/2026**)."*

CV Chi cục, mục II.3 Bước 3:

> *"**Chậm nhất trong ngày 23 của tháng cuối Quý**, các đơn vị hoàn thiện, gửi hồ sơ đánh giá, xếp loại về Chi cục (qua Phòng Tổ chức cán bộ)."*

→ Hạn hồ sơ Quý III/2026 là **23/9/2026**. Hôm nay 18/9. Còn **5 ngày**, trong đó công chức và hai cấp lãnh đạo còn phải chấm và duyệt.

Quyết định của người dùng (18/09): **làm gấp phần tối thiểu trước 23/9**, phần còn lại sang quý IV.

---

## 1. Công văn yêu cầu gì (đối chiếu với phần mềm)

| # | Yêu cầu của công văn | Phần mềm hiện nay | Khoảng cách | Đợt |
|---|---|---|---|---|
| 1 | Kỳ đánh giá, xếp loại là **quý** (áp dụng từ Q3/2026) | Xếp loại theo tháng là chính; luồng quý đã có nhưng lấy dữ liệu bình quân từ tháng | Chuyển kỳ sang quý, ẩn kỳ tháng | **P0** |
| 2 | Tiêu chí chung 30 điểm chấm **một lần cho quý** (Mẫu 02A/02B mục I) | Chấm theo từng tháng, điểm quý = trung bình 3 tháng | Phiếu tiêu chí theo quý, duyệt 2 cấp | **P0** |
| 3 | Phiếu 02A/02B quý: tự chấm → tự nhận xét → tự đề xuất → lãnh đạo nhận xét/đề xuất → cấp thẩm quyền quyết định | Đã có (`phieu_danh_gia_quy`, in 02A/02B) | Mục I của phiếu phải lấy điểm tiêu chí **của quý** | **P0** |
| 4 | Công thức: CC = 30 + (a+b+c)/3×70; LĐ = 30 + (a+b+c+d+đ+e)/6×70; mốc 90/70/50 | Đúng như vậy | Không đổi | — |
| 5 | Hồ sơ nộp chậm nhất ngày **23** tháng cuối quý (CCT gửi Cục ngày 25) | Không có mốc hạn theo quý | Nhắc hạn, cảnh báo đơn vị chưa nộp | P1 |
| 6 | Xếp loại **không chỉ theo điểm KPI**: nhiệm vụ trọng tâm chậm/chưa xong, chỉ tiêu không đạt, báo cáo chậm ≥ 2 lần, kỷ luật… có thể hạ loại dù KPI 88 điểm | Xếp loại tự động theo điểm; lãnh đạo chỉ điều chỉnh thủ công kèm lý do | Ghi nhận cờ định tính | P1 *(người dùng chọn chưa làm đợt này)* |
| 7 | Trần xếp loại: người đứng đầu **không cao hơn** đơn vị; cấp phó không cao hơn người đứng đầu khi đơn vị có việc chậm muộn | Không kiểm tra | Cảnh báo/ràng buộc | P1 |
| 8 | Tỷ lệ Hoàn thành xuất sắc ≤ 20% (đặc biệt ≤ 25%) | Có cảnh báo "A > 20% số B" | Đối chiếu lại đúng định nghĩa của công văn | P1 |
| 9 | CC-NLĐ công tác **≤ 01 tháng** trong quý thì **chưa đánh giá** quý đó, kết quả chuyển sang quý sau | Loại tháng khỏi bình quân nhưng vẫn xếp loại | Trạng thái "chưa đánh giá" (dùng mức E) | P1 |
| 10 | Xếp loại **năm** tổng hợp từ 4 quý (≥ 2 quý HTXS và không quý nào KHT → HTXS; ≤ 2 quý HTNV hoặc ≤ 1 quý KHT → HTT; ≥ 2 quý KHT → KHT) | Chưa có | Màn hình + báo cáo xếp loại năm | P2 (tháng 12) |
| 11 | Chỉ 4 mức xếp loại | Có thêm mức E (không xếp loại) | **Giữ E** làm cờ "chưa đánh giá", không in ra phiếu chính thức | P1 |

Các mục P1/P2 nằm ngoài đợt này theo quyết định của người dùng, nhưng vẫn ghi lại để không rơi.

---

## 2. Bốn quyết định của người dùng (18/09/2026)

| Vấn đề | Quyết định |
|---|---|
| Điểm tiêu chí chung của từng tháng trong quý | **3 tháng dùng chung một điểm quý** |
| Dữ liệu tiêu chí chung T7 + T8/2026 đã chấm | **Chấm mới hoàn toàn cho Quý 3**; dữ liệu cũ giữ nguyên trong CSDL để tra cứu |
| Luồng duyệt | **Giữ 2 cấp**: CC tự chấm → Phó ĐV duyệt cấp 1 → Trưởng ĐV duyệt cấp 2 |
| Thời hạn chấm | **Mở suốt quý**, chỉ khóa khi CCT chốt báo cáo (`is_khoa`) |
| Kỳ tháng | **Ẩn hẳn khỏi giao diện** từ Q3/2026 (dữ liệu cũ vẫn tra cứu được) |
| Quy tắc định tính (mục 6, 7, 8, 9 bảng trên) | **Chưa làm đợt này** |
| Mức E | **Giữ**, dùng cho trường hợp không đánh giá |

---

## 3. Hiện trạng (đo thật trên CSDL production, 18/09/2026)

### 3.1 Dữ liệu tiêu chí chung năm 2026 (`danh_gia_thang`)

| Tháng | Số đơn | Có điểm TC | TC đã duyệt | Đã khóa |
|---|---|---|---|---|
| 1 | 544 | 530 | 530 | 80 |
| 4 | 541 | 539 | 539 | 78 |
| 5 | 541 | 540 | 540 | 43 |
| 6 | 537 | 533 | 533 | 4 |
| **7** | **533** | **517** | **517** | **2** |
| **8** | **458** | **322** | **322** | **0** |
| **9** | **86** | **0** | **0** | **0** |

### 3.2 Luồng quý đã có sẵn (thuận lợi lớn)

- `xep_loai_quy_helpers.tinh_diem_quy` — tính a/b/c/d/đ/e lũy kế theo quý cho CC thường, lãnh đạo, HĐLĐ 111
- `bao_cao_xep_loai_quy.py` — báo cáo xếp loại quý của đơn vị: đề xuất → CCT duyệt (đã có bản ghi Q1, Q2, Q3/2026)
- `phieu_danh_gia_quy.py` — phiếu cá nhân quý, workflow 1 cấp, đúng mục 4/5/6 của Mẫu 02A/02B
- `in_bang_ke.export_phieu_danh_gia_quy` — in phiếu 02A/02B + bảng kê
- Bảng `danh_gia_quy` đã tạo sẵn nhưng chưa dùng (0 dòng)

Chỗ **duy nhất** còn lấy dữ liệu theo tháng để dựng điểm quý là điểm tiêu chí chung 30 điểm.

---

## 4. Kiến trúc cho P0 — phiếu tiêu chí của quý neo ở tháng cuối quý

Không tạo bảng mới. Từ Q3/2026, việc chấm và duyệt tiêu chí chung chỉ diễn ra trên **một** bản ghi `danh_gia_thang` — bản ghi **tháng cuối quý** (T9, T12, T3, T6) — đánh dấu bằng cột mới `la_phieu_tc_quy`. Hai tháng còn lại đọc xuyên sang bản ghi đó.

```
Quý 3/2026
┌──────────┬──────────┬───────────────────────────────┐
│  T7      │  T8      │  T9  ← PHIẾU TC CỦA QUÝ 3     │
│  (đọc)   │  (đọc)   │  la_phieu_tc_quy = true       │
│    └─────┴──────────┤  CC tự chấm 1 lần             │
│  resolver đọc sang  │  Phó ĐV duyệt cấp 1           │
│  bản ghi neo ──────►│  Trưởng ĐV duyệt cấp 2        │
└─────────────────────┴───────────────────────────────┘
```

**Vì sao không tạo bảng mới:** toàn bộ luồng 2 cấp — tự chấm, duyệt, từ chối, trả lại, duyệt hàng loạt, lịch sử điều chỉnh, khóa CCT, quyền duyệt cho công chức chuyển đơn vị (v3.7/v3.8) — khoảng 1.300 dòng backend và màn hình duyệt 1.568 dòng được tái dùng nguyên vẹn. Bảng mới đồng nghĩa viết lại tất cả, không khả thi trong 5 ngày.

**Nguyên tắc an toàn:** chỉ đổi nơi **đọc**, không ghi đè dữ liệu cũ. Không đồng bộ ngược điểm quý vào bản ghi T7/T8 — việc đó sẽ đè 517 + 322 đơn đã duyệt trên production và không hoàn tác được.

**Mốc bật:** một hằng số duy nhất `TC_THEO_QUY_TU = (2026, 3)` trong module mới `app/core/ky_tieu_chi.py`. Kỳ trước mốc không có nhánh code nào chạm tới.

---

## 5. Phạm vi đợt P0 (phải xong trước 20/9 để kịp hạn 23/9)

### 5.1 Backend

| # | Việc | Tệp |
|---|---|---|
| 1 | Module kỳ: `quy_cua_thang`, `thang_neo`, `tc_theo_quy`, `nhan_ky`, hằng số mốc | **mới** `app/core/ky_tieu_chi.py` |
| 2 | Cột `la_phieu_tc_quy BOOLEAN DEFAULT false` + migration (chỉ thêm cột, vài giây) | `models/kpi_assessment.py`, `alembic/versions/` |
| 3 | Tự chấm ghi vào bản ghi tháng neo; nới thời hạn cho tháng neo của quý hiện tại; chốt chặn thao tác trên bản ghi không phải neo | `danh_gia.py` (`tu_danh_gia_tieu_chi`, `kiem_tra_thoi_han_tu_danh_gia`, `get_tu_danh_gia_tieu_chi`, `get_tieu_chi_cong_chuc`, `get_danh_sach_cho_phe_duyet`) |
| 4 | Điểm quý lấy qua resolver (**chỗ quan trọng nhất** — cửa vào của mọi tính điểm quý) | `xep_loai_quy_helpers.py:411 _lay_tc_chung_thang` |
| 5 | In phiếu quý 02A/02B lấy thẳng chi tiết phiếu quý, bỏ bước gộp 3 tháng | `in_bang_ke.py:1678` |
| 6 | Cảnh báo "tiêu chí đang tạm tính" join qua bản ghi neo | `phieu_danh_gia_quy.py:786` |
| 7 | Trang đối soát của TCCB đọc trạng thái theo quý (nếu bỏ qua sẽ báo nhầm cả 544 người "chưa chấm") | `doi_soat_danh_gia.py:215, 333` |
| 8 | Chặn tạo mới báo cáo xếp loại **tháng** và phiếu **tháng** cho kỳ ≥ 7/2026 (đọc dữ liệu cũ vẫn cho phép) | `bao_cao_xep_loai.py`, `phieu_danh_gia_thang.py` |

### 5.2 Frontend

| # | Việc | Tệp |
|---|---|---|
| 9 | Trang tự chấm: kỳ ≥ Q3/2026 đổi bộ chọn Tháng → **Quý**; tiêu đề "Tiêu chí chung — Quý 3/2026"; dòng nhắc "Điểm này áp dụng cho tháng 7, 8, 9" | `danh-gia/tu-cham-diem/page.tsx` |
| 10 | Màn hình duyệt: lọc theo quý, cột "Kỳ", badge phân biệt phiếu quý với phiếu tháng cũ | `components/xep-loai/tabs/TabTieuChi.tsx` |
| 11 | Ẩn kỳ tháng: bỏ tab "Báo cáo" (xếp loại tháng) khỏi `/xep-loai`; `/in-bang-ke` mặc định Quý và ẩn nút chuyển sang Tháng; `/doi-soat` chọn theo quý | `xep-loai/page.tsx`, `in-bang-ke/page.tsx`, `doi-soat/page.tsx`, `Sidebar.tsx` |
| 12 | Chỗ hiện điểm tiêu chí ghi rõ nguồn "(theo Quý 3/2026)" | `dashboard`, `danh-gia`, `danh-gia-v2` |
| 13 | Kiểu dữ liệu: thêm `ky`, `quy`, `thang_neo`, `cac_thang_ap_dung` | `types/tieu-chi-chung.ts`, `services/tieu-chi-chung.service.ts` |

### 5.3 Ngoài phần mềm (Phòng TCCB làm song song)

- Thông báo các đơn vị: **tiêu chí chung quý III chấm lại trên phần mềm**, điểm đã chấm tháng 7 và tháng 8 không dùng nữa.

### 5.4 Không làm trong P0

Công thức điểm, ngưỡng xếp loại, danh mục 10 tiêu chí chung, quy tắc định tính (mục 6–9 bảng phần 1), xếp loại năm, mốc nhắc hạn 23. Các điểm đọc còn lại của kỳ tháng (`bao_cao_xep_loai.py:225/395`, `in_bang_ke.py:591`, `phieu_danh_gia_thang.py:670`, `xep_loai_moi.py`) chuyển sang resolver ở P1 — kỳ tháng đã bị ẩn nên không ảnh hưởng người dùng.

---

## 6. Lịch P0 (rất căng, phải bắt đầu ngay)

| Ngày | Việc |
|---|---|
| **18/9 (chiều)** | Duyệt phạm vi P0. Tạo nhánh `feature/kpi-tieu-chi-theo-quy`. Backend mục 1–4 |
| **19/9** | Backend mục 5–8; Frontend mục 9–10; test trên `kpi_haiquan_test` (clone từ prod) |
| **19/9 (tối)** | Frontend mục 11–13; chạy đủ test hồi quy; đối chiếu điểm các kỳ cũ trước/sau |
| **20/9 (sáng)** | Phát hành theo SHA qua `trien_khai.sh`; TCCB thông báo toàn Chi cục |
| **20–22/9** | Công chức tự chấm tiêu chí chung quý III; lãnh đạo duyệt 2 cấp |
| **23/9** | Đơn vị gửi hồ sơ về TCCB; in phiếu 02A/02B từ phần mềm |

**Rủi ro lịch:** 544 công chức chấm + hai cấp duyệt trong 3 ngày. Nếu đến 21/9 tỷ lệ chấm thấp, phương án dự phòng là các đơn vị điền phiếu 02A/02B bằng Word cho quý III và phần mềm chỉ dùng từ quý IV.

**Quay lui:** đặt `TC_THEO_QUY_TU = (9999, 1)` rồi phát hành lại — hệ thống trở về chấm theo tháng ngay, dữ liệu phiếu quý nằm im. Không cần migration ngược.

---

## 7. Kiểm thử

Chạy **bắt buộc** trên `kpi_haiquan_test`, không bao giờ trên `kpi_haiquan`:

```bash
sudo -u postgres psql -c "DROP DATABASE IF EXISTS kpi_haiquan_test;"
sudo -u postgres psql -c "CREATE DATABASE kpi_haiquan_test OWNER kpi_user;"
sudo -u postgres bash -c "pg_dump kpi_haiquan | psql -d kpi_haiquan_test"
cd backend && source venv/bin/activate
DB_NAME=kpi_haiquan_test pytest tests/ -v
```

Tệp mới `backend/tests/integration/test_tieu_chi_theo_quy.py`:

1. **Không hồi tố** — điểm và xếp loại T1, T4, T5, T6/2026 trước và sau thay đổi phải giống hệt nhau. Phép thử quan trọng nhất.
2. Gọi tự đánh giá với tháng 7 → ghi vào bản ghi tháng 9, cờ `la_phieu_tc_quy` bật.
3. Sau khi duyệt cấp 2 → resolver trả cùng con điểm cho T7, T8, T9; `tinh_diem_quy(quy=3)` ra đúng số đó.
4. In phiếu 02A/02B quý III hiện đúng bảng 10 tiêu chí của phiếu quý (không phải bình quân 3 tháng).
5. Gọi API duyệt trên bản ghi T7 → trả lỗi 400.
6. Đối soát TCCB: T7/T8 không bị báo "chưa chấm" khi phiếu quý đã duyệt.
7. Công chức chuyển đơn vị giữa quý: lãnh đạo đơn vị mới duyệt được.
8. Tạo mới báo cáo xếp loại tháng cho T7/2026 → bị chặn; đọc báo cáo tháng cũ vẫn được.

Chạy lại bộ sẵn có: `tests/regression/test_v1_unchanged.py`, `tests/services/test_kpi_calculator_v2.py`, `test_kpi_lanh_dao_v2.py`, `test_hdld_vb714.py`.

---

## 8. Hệ quả vận hành

1. **Xếp loại tháng 7 và 8/2026 đổi số.** Điểm tiêu chí của hai tháng lấy theo phiếu Quý 3. Trong lúc quý chưa duyệt xong, hai tháng đó không có điểm tiêu chí. Do kỳ tháng bị ẩn nên người dùng gần như không thấy, nhưng dữ liệu bên dưới có thay đổi.
2. **Hai đơn tháng 7 đang khóa KHÔNG cản trở quý III** (tra cứu 18/09/2026): 20ZZ-0176 Nguyễn Văn Hoàn 1995 và 20ZZ-0527 Phạm Bình Dương, đều là Hợp đồng 111, điều chuyển HQCK quốc tế Móng Cái → Đội Kiểm soát Hải quan, ngày hiệu lực 03/7/2026. Khóa do `app/core/dieu_chuyen.py:49` tự đặt khi đổi đơn vị, **không phải** do chốt báo cáo (báo cáo T7 của Móng Cái vẫn NHAP). Cả hai **chưa từng có điểm tiêu chí tháng 7**, và bản ghi tháng 9 của họ không bị khóa → phiếu quý chấm bình thường. Toàn Chi cục không có bản ghi T8/T9 nào bị khóa. **Không cần mở khóa.**
3. **Dữ liệu tiêu chí T7/T8 cũ giữ nguyên** (517 + 322 đơn kèm chi tiết), tra cứu bằng SQL được.
4. **Công chức chuyển đơn vị giữa quý**: phiếu quý neo ở T9 nên người duyệt là lãnh đạo đơn vị mới; cơ chế đơn mồ côi v3.7/v3.8 vẫn chạy, phải test.
5. **Kê khai công việc vẫn theo tháng** — công văn vẫn yêu cầu lập kế hoạch, giao việc theo tuần/tháng; chỉ kỳ **đánh giá, xếp loại** chuyển sang quý.
6. **Phiếu in mẫu tháng 01A/01B** không còn dùng cho kỳ mới; mẫu chính thức của quý là 02A/02B.

---

## 9. Hạng mục P1 và P2 (ghi để không rơi)

**P1 — trong quý IV, xong trước 23/12/2026**

- Cờ định tính theo công văn trên phiếu/báo cáo quý: nhiệm vụ trọng tâm chậm hoặc chưa xong, chỉ tiêu không đạt, báo cáo chậm từ 2 lần, kỷ luật, tham nhũng/lãng phí — kèm cảnh báo hạ loại.
- Trần xếp loại: người đứng đầu không cao hơn đơn vị; cấp phó không cao hơn người đứng đầu khi đơn vị có việc chậm muộn; Phó Chi cục trưởng theo số Trưởng đơn vị phụ trách bị HTNV/KHTNV.
- Đối chiếu lại quy tắc tỷ lệ Hoàn thành xuất sắc (≤ 20%, đặc biệt ≤ 25%) với cách tính "A ≤ 20% B" đang dùng.
- Quy tắc công tác ≤ 01 tháng trong quý → chưa đánh giá, kết quả dồn sang quý sau (dùng mức E).
- Nhắc hạn ngày 23 tháng cuối quý; bảng theo dõi đơn vị chưa nộp.
- Chuyển nốt các điểm đọc kỳ tháng sang resolver.

**P2 — tháng 12/2026**

- Xếp loại **năm** tổng hợp từ 4 quý theo mục II.5 của CV Chi cục; báo cáo và phiếu năm.

---

## 10. Việc cần quyết ngay hôm nay

1. **Duyệt phạm vi P0** ở mục 5 để bắt đầu code chiều nay.
2. Ai phát thông báo cho 15 đơn vị về việc chấm lại tiêu chí chung quý III, và phát khi nào (đề xuất: ngay sau khi phát hành sáng 20/9)?

> Việc "hai đơn tháng 7 đã khóa" đã tra cứu xong ngày 18/09 và **không còn là điểm chặn** — xem mục 8.2.
