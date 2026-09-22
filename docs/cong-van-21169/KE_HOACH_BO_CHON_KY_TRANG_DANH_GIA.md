# Kế hoạch: bộ chọn kỳ (tháng 1–7, Quý III, Quý IV) ở trang Đánh giá và trang Tiêu chí chung

> Tiếp theo `0086dd6` (live 22/09/2026). Ngày lập: 22/09/2026 · **DỰ THẢO, chờ duyệt**
>
> Yêu cầu: *"điều chỉnh hiển thị trang /danh-gia — cho phép chọn từ tháng 1 đến tháng 7,
> Quý III và Quý IV. Default là quý III hiện tại."* · Bổ sung 22/09: *"sửa cả phần
> dropdown chọn tháng bên trang tiêu chí chung"*.

---

## 1. Hiện trạng

### 1.1 Có HAI trang đánh giá, và `/danh-gia` không phải trang đa số người dùng thấy

| Trang | Ai thấy | Số người |
|---|---|---|
| `/danh-gia-v2` | Công chức thường (V2_PL3) và lãnh đạo thật từ tháng 4/2026 | **381 + 53** |
| `/danh-gia` | Chỉ **HĐLĐ 111** (và ai bị ghim V1) — các trường hợp khác bị `router.replace` đá sang v2 ngay khi mở | **106** |

Menu bên trái, mục "Đánh giá", trỏ tới `/danh-gia-v2`. Trang `/danh-gia` giữ lại cho
nhóm HĐLĐ 111 dùng công thức V1 (`effective_kpi_version = "V1"` cho lãnh đạo và HĐ 111
— `auth.py:347`).

→ **Cần chốt sửa trang nào** (mục 5, câu hỏi 1). Đề xuất: sửa **cả hai**, dùng chung một
bộ chọn kỳ, vì phần lớn công sức nằm ở logic kỳ chứ không ở từng trang.

### 1.2 Bộ chọn hiện tại

Cả hai trang đều là: `<select>` Tháng 1–12 + `<select>` Năm, mặc định tháng hiện tại.
Không có khái niệm quý.

### 1.3 Dữ liệu và API sẵn có

- **Kê khai công việc vẫn theo tháng** — điểm KPI 70 của từng tháng vẫn có nghĩa và vẫn
  xem được cho mọi tháng, kể cả T8, T9.
- **Điểm quý đã có API**: `GET /xep-loai-quy/chi-tiet/{cong_chuc_id}?quy=&nam=` trả
  `cac_thang`, `tieu_chi_quy`, `diem_kpi_quy`, `diem_tc_quy`, `diem_tong_quy`,
  `xep_loai_quy`. Công chức thường gọi được cho **chính mình** (phân quyền sẵn trong
  endpoint). Frontend đã có `xepLoaiQuyService.getChiTietQuy`.

→ Chế độ xem theo quý **không cần thêm endpoint nào**.

### 1.4 Một điểm cần lưu ý về tháng 7

Từ đợt `41058a3` (18/09), backend quy mọi truy vấn tiêu chí chung về **tháng neo** của
quý. Nghĩa là hôm nay, chọn "Tháng 7" thì phần Tiêu chí chung hiện **điểm của Quý 3**,
không phải 517 đơn đã chấm hồi tháng 7 — dữ liệu cũ vẫn nằm trong CSDL nhưng không còn
đường API nào đọc ra. Phần điểm KPI 70 thì vẫn đúng là của tháng 7.

→ Cần chốt ý nghĩa của "Tháng 7" trong bộ chọn (mục 5, câu hỏi 3).

---

## 2. Bộ chọn kỳ đề xuất

Một `<select>` "Kỳ đánh giá" duy nhất thay cho ô Tháng, dựng từ `lib/ky-tieu-chi.ts`
(đã có sẵn từ đợt 18/09, đang dùng ở trang tự chấm, đối soát, điều chỉnh điểm TC):

```
Năm 2026:  Tháng 1 · Tháng 2 · … · Tháng 7 · Quý III · Quý IV
Năm 2025:  Tháng 1 … Tháng 12          (toàn bộ theo tháng)
Năm 2027:  Quý I · Quý II · Quý III · Quý IV   (toàn bộ theo quý)
```

Quy tắc dựng danh sách, đặt bằng **hai mốc** trong `lib/ky-tieu-chi.ts` thay vì cắm cứng:

- `TC_THEO_QUY_TU = (2026, 3)` — đã có: từ đây trở đi kỳ là **quý**.
- `THANG_XEM_LAI_DEN = (2026, 7)` — **mới**: vẫn hiện mục **Tháng** cho mọi tháng đến mốc
  này, kể cả tháng đã nằm trong một quý. Mốc 7 vì tháng 7 là tháng cuối cùng thực sự được
  chấm tiêu chí theo tháng (517 đơn đã duyệt); tháng 8 chỉ chấm dở rồi dừng.

Hệ quả: 2026 ra Tháng 1…7 + Quý III + Quý IV; 2025 ra 12 tháng; 2027 ra 4 quý.

**Mặc định**: quý hiện hành theo đồng hồ hệ thống — hôm nay là 22/09 nên ra **Quý III/2026**;
sang tháng 10 sẽ tự ra Quý IV. Nếu năm đang chọn chưa tới kỳ quý thì mặc định là tháng
hiện tại (giữ hành vi cũ cho 2025).

---

## 3. Trang hiển thị gì khi chọn QUÝ

| Khối | Chế độ Tháng (như hiện nay) | Chế độ Quý (mới) |
|---|---|---|
| Thẻ **Tiêu chí chung** | Điểm 30 của kỳ | Điểm 30 của quý (`diem_tc_quy`) |
| Thẻ **Điểm KPI** | a/b/c (hoặc a–e) của tháng × 70 | Lũy kế cả quý (`diem_kpi_quy`) |
| Thẻ **Điểm tổng + xếp loại** | Tổng tháng | Tổng quý + `xep_loai_quy` |
| Bảng **chi tiết kê khai** | Danh sách bản kê khai trong tháng | Xem câu hỏi 4 |
| Bảng **ba tháng trong quý** | — | Bảng mới: mỗi tháng một dòng (điểm TC, KPI, tổng, nguồn "đã duyệt"/"tạm tính") từ `cac_thang` |
| Tab **Tạm tính / Chính thức** | Giữ nguyên | Giữ nguyên; điểm quý gọi với `tam_tinh` tương ứng |

---

## 4. Việc phải làm

### 4.1 Dùng chung

| # | Việc | Tệp |
|---|---|---|
| 1 | Thêm `danhSachKyTrongNam` biến thể cho trang đánh giá (giữ Tháng 7 nếu chốt phương án A), và `kyMacDinh(nam)` trả kỳ mặc định | `lib/ky-tieu-chi.ts` |
| 2 | Component `BoChonKyDanhGia` dùng chung cho cả hai trang: một select Kỳ + một select Năm, phát ra `{ loai: 'THANG' \| 'QUY', thang?, quy?, nam }` | **mới** `components/danh-gia/BoChonKyDanhGia.tsx` |
| 3 | Hook `useDiemQuyCuaToi(quy, nam, tamTinh)` gọi `xepLoaiQuyService.getChiTietQuy` cho chính mình | **mới** `hooks/useDiemQuyCuaToi.ts` |

### 4.2 `/danh-gia-v2` (434 người dùng)

| # | Việc |
|---|---|
| 4 | Thay ô chọn Tháng bằng `BoChonKyDanhGia`; giữ nguyên ô Năm |
| 5 | Chế độ Quý: ba thẻ điểm lấy từ `useDiemQuyCuaToi`; thêm bảng ba tháng; tiêu đề ghi "Quý 3/2026" |
| 6 | Chế độ Tháng: giữ nguyên 100% hành vi hiện tại |

### 4.3 `/danh-gia` (106 HĐLĐ 111) — nếu chốt làm cả hai

| # | Việc |
|---|---|
| 7 | Như mục 4–6. Lưu ý trang này có logic V1 riêng cho HĐLĐ 111 (VB714) — chỉ thay bộ chọn và thêm khối quý, không đụng công thức |
| 8 | Điều kiện `router.replace('/danh-gia-v2')` đang so sánh `selectedThang >= 4` — phải quy đổi khi kỳ là quý, nếu không lãnh đạo chọn Quý IV sẽ bị đá sang v2 sai lúc |

### 4.3b Trang Tiêu chí chung `/danh-gia/tu-cham-diem` (bổ sung 22/09)

Trang này đã dùng `danhSachKyTrongNam` từ đợt 18/09 nên đang hiện **Tháng 1–6 + Quý III +
Quý IV** — thiếu Tháng 7. Chuyển sang danh sách dùng chung là có ngay.

| # | Việc |
|---|---|
| 7b | Dùng danh sách kỳ mới (có Tháng 7) |
| 7c | **Chốt an toàn — đây là trang GHI, không phải trang xem.** Với tháng nằm trong một kỳ quý (T7 và về sau), form phải ở chế độ **chỉ đọc**: hiện lại đúng điểm đã chấm hồi tháng đó, khoá toàn bộ ô nhập, ẩn nút Lưu nháp và Gửi phê duyệt, kèm banner "Số liệu lịch sử — tiêu chí chung nay chấm theo quý, chọn Quý III để chấm" |

Vì sao bắt buộc phải khoá: backend quy mọi thao tác GHI về phiếu quý. Nếu để form mở ở
Tháng 7, công chức sẽ thấy điểm tháng 7 cũ, sửa vài ô rồi bấm lưu — và thứ bị ghi đè là
**phiếu Quý III đang có hiệu lực**. Đây là kiểu lỗi âm thầm, người dùng không thể tự phát
hiện.

### 4.4 Kiểm thử

| # | Việc |
|---|---|
| 9 | Test thuần cho `danhSachKyTrongNam` + `kyMacDinh`: 2025 ra 12 tháng; 2026 ra 7 tháng + 2 quý; 2027 ra 4 quý; mặc định 2026 = Quý III |
| 10 | Chạy lại `DB_NAME=kpi_haiquan_test pytest tests/` + `build_frontend.sh` |
| 10b | Trang tự chấm ở Tháng 7: form khoá, không có nút lưu — kiểm bằng tay trên môi trường dev trước khi phát hành |

**Backend**: chỉ thêm cờ đọc lịch sử ở mục 5b; API điểm quý đã có sẵn, không cần thêm.

---

## 5. Quyết định của người dùng (22/09/2026)

| Vấn đề | Quyết định |
|---|---|
| Sửa trang nào | **Cả hai** — `/danh-gia` và `/danh-gia-v2`, dùng chung một bộ chọn kỳ |
| Danh sách kỳ của 2026 | **Tháng 1 … Tháng 7 + Quý III + Quý IV** (chấp nhận T7 nằm trong cả hai) |
| Chọn "Tháng 7" thì Tiêu chí chung hiện gì | **Điểm đã chấm hồi tháng 7** — dữ liệu lịch sử, không phải điểm Quý 3 |
| Chế độ Quý | **Chỉ bảng tổng hợp ba tháng**, không gộp danh sách bản kê khai |

---

## 5b. Việc phát sinh từ quyết định 3: đường đọc tiêu chí THEO ĐÚNG THÁNG

Từ 18/09, backend quy **mọi** truy vấn tiêu chí chung về tháng neo của quý. Muốn xem lại
điểm đã chấm hồi tháng 7 thì phải có đường đọc bỏ qua bước quy đổi đó.

| # | Việc | Tệp |
|---|---|---|
| 11 | Thêm tham số `theo_dung_thang` (mặc định `false`) cho **hai endpoint ĐỌC**: `GET /danh-gia/tieu-chi/thang/{thang}/nam/{nam}` và `GET /danh-gia/tieu-chi/cong-chuc/{id}/thang/{t}/nam/{n}`. Bật cờ → đọc đúng bản ghi tháng đó, không quy về tháng neo | `api/v1/endpoints/danh_gia.py` |
| 12 | Response khi bật cờ phải ghi rõ `ky = "THANG_LICH_SU"` để giao diện hiện nhãn "Tiêu chí đã chấm theo tháng 7 (số liệu lịch sử)" — tránh người dùng tưởng đây là điểm đang có hiệu lực | `danh_gia.py` |
| 13 | **Chỉ áp cho đường ĐỌC.** Tự chấm, gửi duyệt, phê duyệt, điều chỉnh vẫn ghi vào phiếu quý như hiện nay — không mở đường sửa ngược vào dữ liệu tháng cũ | — |
| 14 | Frontend: khi kỳ đang chọn là Tháng và tháng đó thuộc phạm vi công văn (T7 trở đi), gọi API kèm `theo_dung_thang=true` và hiện nhãn lịch sử | cả hai trang |

Phạm vi ảnh hưởng nhỏ: tháng 1–6 có tháng neo trùng chính nó nên cờ không đổi gì; thực
chất chỉ tháng 7 (và T8, T9 nếu về sau ai đó mở rộng danh sách) đi qua nhánh mới.

Kiểm thử bổ sung:
- Bật cờ ở tháng 7 → trả đúng 517 đơn dữ liệu cũ, tổng điểm khớp `danh_gia_thang` của T7.
- Không bật cờ → vẫn trả phiếu Quý 3 như hiện nay (không phá hành vi đã phát hành).
- Đường GHI không nhận cờ: tự chấm với tháng 7 vẫn ghi vào bản ghi tháng 9.

---

## 6. Ước lượng

| Phần | Thời gian |
|---|---|
| Backend: cờ `theo_dung_thang` cho hai endpoint đọc + test | 0,5 ngày |
| Bộ chọn kỳ dùng chung + hook điểm quý | 0,5 ngày |
| `/danh-gia-v2`: chế độ quý + bảng ba tháng | 0,5 ngày |
| `/danh-gia`: như trên, cho HĐLĐ 111 | 0,25 ngày |
| Trang Tiêu chí chung: danh sách kỳ mới + chế độ chỉ đọc cho tháng lịch sử | 0,25 ngày |
| Kiểm thử + phát hành | 0,25 ngày |
| **Tổng** | **~2,25 ngày** |

Không migration, không đụng một dòng dữ liệu nào. Backend chỉ thêm một tham số đọc có
giá trị mặc định giữ nguyên hành vi cũ. Quay lui = phát hành lại mốc trước.
