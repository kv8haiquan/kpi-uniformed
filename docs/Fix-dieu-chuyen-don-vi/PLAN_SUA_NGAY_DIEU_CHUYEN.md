# Plan sửa dữ liệu "ngày điều chuyển" (lich_su_dieu_chuyen)

Nguồn đối chiếu: `docs/Fix-dieu-chuyen-don-vi/BANG THEO DOI DIEU DONG 2026.xls`, sheet
`Lam QD 2026` (142 dòng). Đối chiếu thực hiện ngày 25/08/2026 trên DB prod
`kpi_haiquan` bằng **truy vấn CHỈ ĐỌC**.

---

## 1. Kết quả đối chiếu — cái gì đang sai

### Tin tốt: trạng thái hiện tại gần như đúng

**142/142 người đã khớp được với `cong_chuc`**, và cả 142 đều có
`cong_chuc.don_vi_id` đúng bằng "Đơn vị đến" của quyết định. Nghĩa là đơn vị
*hiện tại* không cần sửa nữa — chỉ **lịch sử** sai.

Tổng kết 142 dòng: **73 cần sửa ngày**, **62 cần thêm mới**, **3 đã đúng sẵn**,
**4 là bộ khứ hồi cần gộp**.

### Sai #1 — `ngay_hieu_luc` là ngày NHẬP LIỆU, không phải ngày hiệu lực QĐ (73 dòng)

Bảng phân bố trong DB cho thấy `ngay_hieu_luc = created_at::date` ở gần như mọi
dòng — người nhập bấm "điều chuyển" ngày nào thì hệ thống lấy ngày đó.

| Đợt QĐ (Excel) | Số người | Ngày đang lưu trong DB |
|---|---|---|
| 15/5/2026 | 70 | 20/5, 21/5, 26/5, **01/6 → 06/6** |
| 03/6/2026 | 2 | 13/7, 14/7 |
| 03/7/2026 | 3 | 03/7 ✅ đúng sẵn cả 3 |

→ **73 dòng** cần `UPDATE ngay_hieu_luc` (72 + `20ZZ-0261` tra thêm ở Sai #3).

### Sai #2 — thiếu hẳn bản ghi lịch sử (62 dòng)

Toàn bộ **đợt 04/02/2026 (62 người)** không có bản ghi nào trong
`lich_su_dieu_chuyen`; đơn vị được đặt thẳng vào `cong_chuc.don_vi_id` (seed hoặc
sửa tay). Đợt 03/7 đã được xử lý xong (xem Sai #4) → còn **62 dòng cần `INSERT`**.

Hệ quả: mọi phép suy "đơn vị tại tháng" cho **tháng 1/2026** coi như họ đã ở đơn
vị mới từ đầu năm — sai.

### Sai #3 — 5 người ban đầu không khớp tên → ĐÃ TRA RA ĐỦ 5

Nguyên nhân: **DB gắn hậu tố năm sinh cho người trùng tên** ("Nguyễn Viết Cường
1971"), Excel ghi tên trần → so khớp chuỗi chính xác trượt. Cách tra: bỏ dấu, cắt
hậu tố `\d{2,4}` ở cuối, rồi khử mập mờ bằng **`ke_khai_cong_viec.don_vi_id_snapshot`
theo tháng** (đơn vị nơi người đó thực kê khai).

| STT | Tên trong Excel | Đi → Đến | **`ma_cc` xác định** | Bằng chứng |
|---|---|---|---|---|
| 7 | Nguyễn Viết Cường | HQCK-CP → HQCK-HM | **20ZZ-0220** (1971) | KK T1 = HQCK-CP ✅ đúng đơn vị đi; nay ở HM. Người kia (`20ZZ-0369`, 1988) đã ở HM từ T1–T2 → không phải |
| 24 | Nguyễn Đức Tuệ | HQCK-HG → TCCB | **20ZZ-0483** (1985) | KK T1,T2 = HQCK-HG → T4 = TCCB. Người kia (`20ZZ-0139`, 1971) ở HQCK-MC suốt T1–T8 |
| 29 | Phạm Thị Lan Hương | HQCK-BPS → HQCK-MC | **20ZZ-0298** (1987) | KK T1 = HQCK-BPS → T4 = HQCK-MC. Người kia (`20ZZ-0446`, 1989) ở QLRR suốt |
| 110 | Nguyễn Mạnh Cường | KSHQ → HQCK-MC | **20ZZ-0261** (1970) | Ứng viên duy nhất. KK T4 = KSHQ, **T5 có CẢ KSHQ lẫn HQCK-MC**, T6–T7 = HQCK-MC |
| 141 | Nguyễn Văn Hoàn | HQCK-MC → KSHQ | **20ZZ-0176** (1995) | Ứng viên duy nhất; lúc tra còn ở HQCK-MC vì đợt 03/7 chưa nhập — **đã điều chuyển xong 25/08**, xem Sai #4 |

> Ca STT 110 còn là **bằng chứng độc lập xác nhận mốc 15/5/2026**: kê khai tháng 5
> của người này rơi vào cả hai đơn vị — đúng dấu vết của người chuyển giữa tháng.
> Nếu ngày hiệu lực thật là 01/6 như DB đang lưu thì T5 phải thuần KSHQ.

Cả 5 đều `is_active = true`, `is_deleted = false`, chức vụ "Hợp đồng 111".

#### Ca STT 7 — đã chốt bằng 4 nguồn độc lập, không còn mập mờ

Hai người trùng tên nay **cùng ở HQCK-HM**, nên phải tra bằng dấu vết tháng 1:

| Nguồn | `20ZZ-0220` (1971) | `20ZZ-0369` (1988) |
|---|---|---|
| Snapshot đơn vị của kê khai T1 | **HQCK-CP** | HQCK-HM |
| Người duyệt kê khai T1 | Nguyễn Thị Minh, PĐT **HQCK-CP** | Đoàn Thế Thăng, PĐT HQCK-HM |
| Người duyệt TCC T1 → T7 | T1 = **CP** → T4–T7 = **HM** (đổi rõ ràng) | HM suốt T1–T7, không đổi |
| Nội dung công việc T1 | Tuần tra Quang Hanh, Vũng Đục, Mông Dương, Vân Đồn, Cảng 10/10 (**địa bàn Cẩm Phả**); "Trực phương tiện ô tô BKS 14A-014.08" → **lái xe**, khớp cột ngạch "Lái xe" của Excel | 1 dòng duy nhất, nội dung "25 ngày" |

→ **`20ZZ-0220` là người ở STT 7.** `20ZZ-0369` ở HQCK-HM từ đầu, không hề chuyển.
Vẫn nên báo TCCB một câu cho có người chịu trách nhiệm, nhưng dữ liệu đã đủ chắc.

#### Snapshot tháng 1 có đáng tin không? — Có

Kê khai T1/2026 được nhập **02–13/02/2026**, tức *sau* mốc hiệu lực 04/02, nên
thoạt nhìn snapshot có thể đã nhiễm đơn vị mới. Kiểm tra thực tế trên 62 người
đợt 04/02:

| Snapshot T1 bằng… | Số người |
|---|---|
| **Đơn vị ĐI** | **53** |
| Đơn vị ĐẾN | **0** |
| Đơn vị khác | 0 |
| Không kê khai T1 | 9 |

53/53 khớp đơn vị đi, không một ca ngược → `cong_chuc.don_vi_id` chỉ được đổi
**sau khi kê khai T1 đã xong** (sau 13/02). Snapshot T1 dùng làm bằng chứng
"đơn vị tại tháng 1" được, không cần dè dặt.

Hệ quả tích cực: **báo cáo T1 hiện tại về cơ bản đã đúng** — nguồn kê-khai và
nguồn người-duyệt đều trỏ đơn vị đi và thắng phiếu, dù heuristic trỏ sai. Việc
INSERT 62 dòng là để **lịch sử đúng sự thật**, không phải để cứu báo cáo. Rủi ro
của bước này vì thế thấp hơn đánh giá ban đầu.

### ~~Sai #4 — 2 người lệch đơn vị hiện tại~~ → ✅ ĐÃ XỬ LÝ 25/08/2026

Đợt 03/7 (3 thuyền viên MC → KSHQ) trước đó chỉ nhập được 1/3. User đã tự điều
chuyển nốt 2 người còn lại lúc 16:35 ngày 25/08, **ghi đúng `ngay_hieu_luc = 2026-07-03`**:

| `ma_cc` | Họ tên | Đơn vị | `ngay_hieu_luc` |
|---|---|---|---|
| `20ZZ-0527` | Phạm Bình Dương | KSHQ ✅ | 2026-07-03 (nhập 03/08) |
| `20ZZ-0529` | Nguyễn Đức Quang | KSHQ ✅ | 2026-07-03 (nhập 25/08) |
| `20ZZ-0176` | Nguyễn Văn Hoàn 1995 | KSHQ ✅ | 2026-07-03 (nhập 25/08) |

Còn tồn: **T7/2026 của `20ZZ-0529` đã được HQCK-MC phê duyệt** (`DA_PHE_DUYET`)
trước khi chuyển. Cần quyết xem có chấm lại theo KSHQ hay giữ nguyên.

### Sai #5 — 4 bộ bản ghi "khứ hồi" do nhập sai rồi sửa

```
20ZZ-0210 Lê Hùng        01/6 VG→MC | 02/6 MC→VG | 02/6 VG→MC
20ZZ-0126 Lê Thanh Hải   01/6 PTSTQ→MC | 01/6 MC→PTSTQ | 02/6 PTSTQ→MC
20ZZ-0417 Lê Vũ Hải      01/6 CP→MC | 02/6 MC→CP | 02/6 CP→MC
20ZZ-0108 Ngô Văn Chung  29/5 BPS→HM | 02/6 HM→BPS | 02/6 BPS→HM
```

Mỗi bộ chỉ tương ứng **một** dòng trong QĐ. Phải gộp về 1 dòng (giữ dòng cuối,
xóa cặp khứ hồi) — nếu để nguyên sẽ sinh sai lệch báo cáo (đã kiểm chứng, xem §3).

### Sai #6 (ngoài phạm vi Excel) — 12 dòng `VO_HIEU_HOA` còn `ngay_hieu_luc = NULL`

Đây **không phải lỗi mới**: 12 dòng này (`ly_do = "Vô hiệu hóa (backfill trước khi
có tính năng)"`) do đợt backfill 17/07/2026 cố ý để NULL, để `_active_tai_thang_expr`
bỏ qua và báo cáo không đổi cho tới khi admin điền ngày thật. Việc còn nợ là
**TCCB điền ngày nghỉ hưu/nghỉ việc thực tế** qua nút "Sửa ngày" ở
`/admin/lich-su-dieu-chuyen`.

Tiện đợt này thì làm luôn, nhưng **không gộp vào script** — ngày nghỉ của từng
người phải do TCCB nhập, không suy ra được từ dữ liệu.

---

## 2. Sai kèm theo trong CODE — `mốc chốt` đang bù trừ cho dữ liệu bẩn

`backend/app/api/v1/endpoints/bao_cao_xep_loai.py:557` `_don_vi_tai_thang_expr`,
nhánh heuristic (nguồn 3/3) cuộn ngược điều chuyển khi:

```python
mocchot = ngày cuối tháng M+1          # ← nới thêm TRỌN một tháng
LichSuDieuChuyen.ngay_hieu_luc > mocchot
```

Cái "nới thêm một tháng" đó chính là để bù cho việc `ngay_hieu_luc` bị ghi trễ
~2–3 tuần so với QĐ. **Khi dữ liệu đã đúng thì mốc phải là cuối tháng M**, nếu
không heuristic sẽ hiểu ngược. Vì vậy sửa dữ liệu và sửa mốc **phải đi cùng nhau**
trong một lần phát hành.

### ⚠️ Phát hiện khi viết test: heuristic một mình KHÔNG đổi được kết quả

Nhánh phá hòa của phép bầu phiếu là `COALESCE(v_kk, v_ap, v_he)`, mà
`v_ap = COALESCE(đơn vị người duyệt, đơn vị hồ sơ)` → **không bao giờ NULL**.
Nên `v_he` **không bao giờ được chạm tới** ở nhánh phá hòa.

Hệ quả: heuristic chỉ có tiếng nói khi **đồng ý với phiếu kê-khai** (hoặc trùng
phiếu người-duyệt). Công chức không kê khai trong tháng thì đơn vị-tại-tháng
luôn bằng đơn vị hồ sơ hiện tại, bất kể lịch sử điều chuyển ghi gì.

Điều này giải thích tại sao đợt sửa chỉ đổi 1 ca trên 558 người × 8 tháng, và
cũng có nghĩa: **giá trị chính của việc làm sạch lịch sử là tính đúng đắn của
hồ sơ nhân sự**, không phải cứu báo cáo. Hành vi này đã được chốt bằng test
`test_heuristic_mot_minh_khong_doi_duoc_ket_qua` để lần sau ai đọc hàm không
kỳ vọng sai.

---

## 3. Đã mô phỏng tác động (chưa ghi gì vào DB)

Chạy lại đúng biểu thức bầu-cử-3-nguồn của báo cáo trên 558 công chức, tháng
1→7/2026, so sánh **hiện trạng** với **sau khi sửa (73 UPDATE + 62 INSERT + đổi mốc
về cuối tháng M)**:

| Tháng | Heuristic đổi | **Kết quả báo cáo đổi** |
|---|---|---|
| 1 | 63 | **1** |
| 2 | 0 | 0 |
| 3 | 0 | 0 |
| 4 | 4 | 0 |
| 5 | 4 | **1** |
| 6 | 1 | 0 |
| 7 | 0 | 0 |

Cơ chế bầu-cử-3-nguồn hấp thụ gần hết. Hai ca đổi:

- **T1 — `20ZZ-0303` Vũ Thanh Hảo**: `HQCK-MC → PTSTQ`. Đây là **sửa đúng**: QĐ
  04/02 mới chuyển PTSTQ→MC, kê khai T1 cũng ghi PTSTQ.
- **T5 — `20ZZ-0126` Lê Thanh Hải**: `HQCK-MC → PTSTQ`, **sai**. Nguyên nhân là bộ
  khứ hồi ở Sai #5 chưa được dọn. Dọn xong thì ca này tự hết → **phải làm Sai #5
  trước hoặc cùng lúc**.

Nói cách khác: làm đủ 6 mục thì báo cáo T2–T7 **không đổi một dòng nào**, T1 sửa
đúng 1 ca. An toàn cho các tháng đã chốt/đã xuất phụ lục.

> Nếu chỉ sửa dữ liệu mà **không** đổi mốc chốt: T4 sẽ sai thêm 2 người
> (`20ZZ-0508` Nguyễn Xuân Giáp, `20ZZ-0304` Vũ Thị Hậu) — đã mô phỏng riêng.
> Đây là lý do không tách hai việc.

---

## 4. Kế hoạch thực hiện

Nhánh: `feature/kpi-sua-ngay-dieu-chuyen` (tạo từ `prod` @ `c53d843`)

### Tình trạng — cập nhật 31/08/2026

| Bước | Trạng thái |
|---|---|
| 0. Chốt đầu vào | ✅ xong (4 quyết định + 2 câu còn treo, không chặn) |
| 1. Sao lưu | ✅ `/var/backup/truoc_sua_ngay_dieu_chuyen_20260831_1819.sql` (232 KB) |
| 2. Viết script | ✅ `backend/scripts/fix_ngay_dieu_chuyen_2026.py` |
| 3. Chạy thử DB test | ✅ `kpi_haiquan_test`: xóa 8 · sửa 77 · thêm 62 · 0 cảnh báo; chạy lần 2 ra 0 thao tác (idempotent) |
| 4. Sửa code + đối chứng | ✅ mốc chốt → cuối tháng M; đối chứng T1–T8 = **1 ca đổi**; 5/5 test PASS |
| 5. Chặn tái diễn (FE/BE) | ✅ xong — bỏ prefill, bắt buộc nhập ngày, cảnh báo lệch >15 ngày, vá lỗi UTC; build sạch |
| 6. Áp prod | ⬜ **chưa làm** — cần user ngồi cạnh |

Con số thực tế của script (khác dự toán ban đầu vì 4 người khứ hồi sau khi gộp
thì dòng giữ lại cũng phải sửa ngày → 73 + 4 = 77):

```
xóa 8 · sửa 77 · thêm 62 · đã đúng sẵn 3 · cảnh báo 0     (tổng 142 dòng QĐ)
```

### Bước 0 — Chốt đầu vào (cần TCCB trả lời, chặn bước 3)

1. ~~`ma_cc` của 5 người ở Sai #3~~ — **đã tra ra đủ 5, cả 5 đều chắc chắn**
   (xem bảng Sai #3). Ca STT 7 đã chốt bằng 3 nguồn độc lập → `20ZZ-0220`.
   Chỉ cần báo TCCB xác nhận cho đúng thủ tục, **không còn chặn bước 3**.
2. Số/ngày quyết định thật của từng đợt để ghi vào `ly_do`
   (hiện đang là chuỗi rỗng nghĩa "Điều chuyển nhân sự"). Đề xuất:
   `"Theo QĐ số …/QĐ-HQKV8 ngày 04/02/2026"`.
3. Xác nhận `20ZZ-0529` Nguyễn Đức Quang và `20ZZ-0176` Nguyễn Văn Hoàn 1995 đã
   thực chuyển sang KSHQ chưa (Sai #4) — cả đợt 03/7 gần như chưa vào hệ thống.
4. Đợt 15/5: ngày hiệu lực là **15/5/2026** hay ngày ký QĐ khác? Cột Excel ghi
   `15/5/2026`, và dấu vết kê khai của `20ZZ-0261` (T5 rơi vào cả 2 đơn vị) ủng hộ
   mốc giữa tháng. Cần đúng vì nó quyết định T5 thuộc đơn vị nào.

### Bước 1 — Sao lưu

```bash
sudo -u postgres pg_dump -t lich_su_dieu_chuyen -t cong_chuc kpi_haiquan \
  > /var/backup/truoc_sua_ngay_dieu_chuyen_$(date +%Y%m%d_%H%M).sql
```

### Bước 2 — Viết script di trú (không sửa tay trên prod)

`backend/scripts/fix_ngay_dieu_chuyen_2026.py`, đọc thẳng file `.xls`, có:

- `--dry-run` (mặc định): chỉ in bảng "sẽ UPDATE / sẽ INSERT / sẽ XÓA".
- `--apply`: chạy trong **một** transaction, `COMMIT` cuối cùng.
- Khớp người theo `ma_cc` **đã chốt ở bước 0**, không khớp theo họ tên khi chạy thật.
  (Hàm khớp tên chỉ dùng để dựng bảng đối chiếu, và phải: bỏ dấu → cắt hậu tố năm
  sinh `\d{2,4}` → nếu còn >1 ứng viên thì khử bằng `ke_khai_cong_viec.don_vi_id_snapshot`
  của tháng TRƯỚC ngày hiệu lực, so với "Đơn vị đi". Xem Sai #3.)
- Ghi `nguoi_thuc_hien_id = NULL`, `ly_do` = số QĐ, `loai = 'DIEU_CHUYEN'`.
- Chống chạy lại: bỏ qua nếu đã tồn tại dòng cùng `(cong_chuc_id, don_vi_cu_id,
  don_vi_moi_id, ngay_hieu_luc)`.

Thứ tự thao tác trong script:

1. XÓA 4 cặp khứ hồi (Sai #5) — giữ dòng cuối mỗi bộ.
2. UPDATE 73 dòng `ngay_hieu_luc` (Sai #1), gồm cả 4 dòng vừa gộp ở bước 1.
3. INSERT 62 dòng đợt 04/02 (Sai #2 + 3 người tra thêm ở Sai #3).
12 dòng `VO_HIEU_HOA` NULL (Sai #6) **để ngoài script** — TCCB tự điền trên giao diện.

### Bước 3 — Chạy thử trên DB test, KHÔNG chạy prod trước

```bash
sudo -u postgres psql -c "DROP DATABASE IF EXISTS kpi_haiquan_test;"
sudo -u postgres psql -c "CREATE DATABASE kpi_haiquan_test OWNER kpi_user;"
sudo -u postgres bash -c "pg_dump kpi_haiquan | psql -d kpi_haiquan_test"

cd backend && source venv/bin/activate
DB_NAME=kpi_haiquan_test python scripts/fix_ngay_dieu_chuyen_2026.py --apply
```

### Bước 4 — Sửa code, chạy đối chứng trên DB test

- `bao_cao_xep_loai.py`: `mocchot` → **ngày cuối tháng M** (bỏ `+1`), cập nhật
  docstring nêu rõ lý do đổi (dữ liệu ngày đã được làm sạch 25/08/2026).
- `_active_tai_thang_expr`: giữ nguyên (12 dòng NULL là cố ý — xem Sai #6).
- Đối chứng: `backend/scripts/doi_chung_don_vi_tai_thang.py` chạy **chính biểu thức
  trong code** trên 2 database rồi so từng công chức từng tháng — không viết lại SQL
  bằng tay nên không lệch khỏi thứ thật sự chạy.

  Cách so "code cũ + dữ liệu cũ" với "code mới + dữ liệu mới":

  ```bash
  git stash push backend/app/api/v1/endpoints/bao_cao_xep_loai.py
  python scripts/doi_chung_don_vi_tai_thang.py --db-a kpi_haiquan --db-b kpi_haiquan --xuat /tmp/truoc.json
  git stash pop
  python scripts/doi_chung_don_vi_tai_thang.py --db-a kpi_haiquan_test --db-b kpi_haiquan_test --xuat /tmp/sau.json
  # rồi so trường "a" của hai file
  ```

  **Kết quả thực tế (31/08/2026): T1 đổi 1 ca (`20ZZ-0303` HQCK-MC → PTSTQ),
  T2–T8 đổi 0 ca.** Đúng bằng dự đoán ở §3.
- Test: `backend/tests/integration/test_moc_chot_don_vi_tai_thang.py` — 5 test,
  đã kiểm chứng **có tác dụng thật**: đưa mốc cũ trở lại thì 2 test đỏ ngay.

  ```bash
  DB_NAME=kpi_haiquan_test pytest tests/integration/test_moc_chot_don_vi_tai_thang.py -v
  ```

- Regression toàn bộ `tests/integration/` + `tests/regression/`: **39 pass, 1 fail**.
  Ca đỏ là `test_dieu_chinh_danh_gia_thang.py::test_bao_cao_da_phe_duyet_bao_400`
  — **đỏ sẵn từ trước**, đã kiểm chứng bằng cách chạy lại trên code gốc. Không
  thuộc đợt này, nhưng nên vá riêng.

### Bước 5 — Chặn tái diễn (quan trọng hơn cả việc vá)

**Cái ĐÃ CÓ** (từ đợt 17/07/2026, nhánh `feature/kpi-lich-su-dieu-chuyen`):

- Ô "Ngày hiệu lực" trong modal điều chuyển — `UserModals.tsx:611-619`
- Ô "Lý do điều chuyển", placeholder đã gợi ý số QĐ — `UserModals.tsx:622-630`
- Sửa lịch sử ngay trong modal + trang `/admin/lich-su-dieu-chuyen`

Nhờ vậy user nhập đúng `03/7` cho 2 người ngày 25/08. **Trường ngày không thiếu —
vấn đề nằm ở giá trị mặc định.**

**Cái CÒN THIẾU — đúng chỗ sinh ra 92/95 bản ghi sai:**

| # | Vị trí | Hiện tại | Hệ quả |
|---|---|---|---|
| 1 | `frontend/src/components/admin/UserModals.tsx:443` | `ngay_hieu_luc: new Date().toISOString().split('T')[0]` | **Điền sẵn hôm nay.** Bấm Lưu mà không để ý là ra ngày nhập liệu |
| 2 | `backend/app/api/v1/endpoints/admin.py:1004` | `ngay_hieu_luc=payload.ngay_hieu_luc or date.today()` | Kể cả FE gửi rỗng, BE vẫn **âm thầm** điền hôm nay — không có cách nào để trống |
| 3 | cùng dòng 443 | `toISOString()` trả ngày theo **UTC** | Từ 00:00–07:00 giờ VN, ô ngày điền sẵn **hôm qua** |

**ĐÃ LÀM 31/08/2026** (bỏ yêu cầu bắt buộc số QĐ theo quyết định của user):

- ✅ `UserModals.tsx` — bỏ prefill, ô ngày để trống + `required` + dấu `*`;
  thêm nút **"Hôm nay"** để người nhập bấm chủ động thay vì được điền sẵn;
  chú thích dưới ô: *"Lấy đúng ngày ghi trong quyết định, không phải ngày nhập liệu."*
- ✅ Chặn ở `handleSubmit`: thiếu ngày → báo và không gửi.
- ✅ Hàm `ngayHomNay()` dùng **giờ địa phương**, thay `toISOString()` (vốn trả giờ
  UTC → từ 00:00–07:00 giờ VN điền sẵn ngày HÔM QUA).
- ✅ Cảnh báo vàng khi ngày hiệu lực lệch quá **15 ngày** so với ngày nhập, cả hai
  chiều: về trước = "bạn đang nhập muộn", về sau = "kiểm tra gõ nhầm tháng/năm".
  Bấm Lưu khi đang có cảnh báo thì phải xác nhận thêm một lần — nhắc, không chặn.
- ✅ `admin.py` — giữ `or date.today()` làm lưới an toàn cho client cũ, kèm ghi chú
  nêu rõ đây KHÔNG phải hành vi mong muốn và chính nó đã gây ra đợt sửa này.
- Ô "Lý do" giữ nguyên **không bắt buộc**.

Kiểm chứng: `tsc --noEmit` sạch, `npm run build` compiled successfully.
`eslint` còn 1 lỗi `react-hooks/set-state-in-effect` ở `useEffect(reloadHistory)`
— **đỏ sẵn từ trước**, đã đối chứng bằng cách lint lại trên bản gốc.

Modal đổi trạng thái (vô hiệu hóa/kích hoạt) ở `admin/users/page.tsx` vốn đã để
trống ngày sẵn (`useState('')`) → không cần sửa.

**Còn treo:** màn "Điều chuyển hàng loạt theo QĐ" (1 ngày hiệu lực + dán danh
sách `ma_cc, đơn vị đến`). Đợt nào cũng vài chục người; nhập lẻ là lý do đợt
04/02 bị bỏ quên trọn vẹn 62 người và đợt 03/7 chỉ nhập được 1/3.

### Bước 6 — Áp prod

```bash
# 1. deploy code theo SHA (KHÔNG truyền tên nhánh)
/opt/kpi-prod/backend/scripts/trien_khai.sh <sha>
# 2. chạy script với --apply trên prod, trong cùng phiên, có user ngồi cạnh
# 3. chạy lại truy vấn đối chứng §7
```

---

## 5. Việc cần user quyết trước khi tôi code

Chốt ngày 25/08/2026:

| # | Câu hỏi | Quyết định |
|---|---|---|
| 1 | STT 7 = `20ZZ-0220`? | ✅ Đã chốt bằng 4 nguồn độc lập; báo TCCB cho đúng thủ tục, không chặn |
| 2 | Số/ngày QĐ từng đợt? | ⏸ **Chưa có, để sau.** Script ghi tạm `ly_do = "Đợt điều động <ngày>"`; bổ sung số QĐ sau qua trang `/admin/lich-su-dieu-chuyen` |
| 3 | `20ZZ-0529`, `20ZZ-0176` đã chuyển chưa? | ✅ **User đã tự điều chuyển xong 25/08**, ngày hiệu lực đúng 03/7 |
| 4 | Đổi mốc chốt về cuối tháng M? | ✅ **Đồng ý** |
| 5 | Bắt buộc nhập số QĐ? | ❌ **Không.** Ô "Lý do" giữ nguyên không bắt buộc |
| 6 | Màn điều chuyển hàng loạt? | ⏳ **Còn treo** — xem bước 5 |

Còn tồn cần quyết: **T7/2026 của `20ZZ-0529`** đã được HQCK-MC duyệt xong trước
khi chuyển sang KSHQ — chấm lại theo KSHQ hay giữ nguyên?

---

## 6. Rủi ro

| Rủi ro | Mức | Cách chặn |
|---|---|---|
| Báo cáo tháng đã xuất phụ lục bị đổi | Thấp | Đã mô phỏng: T2–T7 không đổi dòng nào |
| Khớp sai người do trùng họ tên | Trung bình | 8/142 dòng có >1 người cùng tên gốc — đã rà hết từng ca bằng kê khai theo tháng; `--apply` chỉ nhận `ma_cc` cứng, không khớp theo tên |
| Script chạy 2 lần sinh trùng | Thấp | Khoá chống trùng theo `(cc, đi, đến, ngày)` |
| Ghi nhầm prod | Trung bình | `--dry-run` mặc định; chạy DB test trước; 1 transaction; có `pg_dump` |

---

## 7. Truy vấn đối chứng sau khi áp

```sql
-- (a) Phân bố ngày hiệu lực phải gom về đúng 4 mốc QĐ + vài ca lẻ
SELECT ngay_hieu_luc, count(*) FROM lich_su_dieu_chuyen
WHERE loai='DIEU_CHUYEN' GROUP BY 1 ORDER BY 1;
-- kỳ vọng: 2026-02-04 = 62, 2026-05-15 = 75, 2026-06-03 = 2, 2026-07-03 = 3 (đã đúng sẵn)

-- (b) Không còn ai có >1 bản ghi cùng chiều đi/đến
SELECT cong_chuc_id, don_vi_cu_id, don_vi_moi_id, count(*)
FROM lich_su_dieu_chuyen WHERE loai='DIEU_CHUYEN'
GROUP BY 1,2,3 HAVING count(*)>1;   -- kỳ vọng 0 dòng

-- (c) Đơn vị hiện tại khớp "Đơn vị đến" của QĐ mới nhất — 0 dòng lệch
```

Ngoài ra chạy lại `/api/v1/bao-cao-xep-loai` cho T4 và T5/2026, đối chiếu với
phụ lục đã xuất — phải **khớp 100%** như trước khi sửa.
