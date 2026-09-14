# Đề xuất của Chánh Văn phòng: mở mục lấy ý kiến dự thảo trong Họp Không Giấy

*Nghiên cứu ngày 14/09/2026. Số liệu đo trực tiếp trên production (chỉ câu `SELECT`),
không lấy lại từ tài liệu.*

> Nguyên văn đề xuất: *"chỗ họp không giấy mình có mở mục lấy ý kiến tham gia các
> dự thảo được không"*

---

## 1. Trả lời ngắn

**Được, và nên làm.** Nhưng có ba điều cần biết trước khi quyết:

| Điều cần biết | Nội dung |
|---|---|
| **Nhu cầu có thật, đo được** | 44 cuộc họp bàn dự thảo trong 7 tháng (đều đặn ~7/tháng), 59 tài liệu kèm theo. Khâu tổng hợp **đang làm tay bằng Word** — trong kho có file *"Tổng hợp ý kiến của các cơ quan.signed.pdf"* |
| **Đây là đề xuất MỚI, không phải việc đã hứa mà quên** | Công văn yêu cầu gốc của Văn phòng (do chính Chánh Văn phòng ký, phúc đáp CV 94/CNTT) **không có dòng nào** về lấy ý kiến văn bản dự thảo |
| **Bảng `y_kien` sẵn có KHÔNG dùng lại được** | Nó buộc `cuoc_hop_id NOT NULL` — chỉ chứa được ý kiến gắn với một cuộc họp cụ thể |

Việc này **không nằm trong bất kỳ kế hoạch nào** đang treo, nên làm hay không là quyết
định mới hoàn toàn, không ảnh hưởng cam kết cũ.

---

## 2. Nhu cầu là có thật — bằng chứng trên dữ liệu

### 2.1 Quy mô

| Chỉ số | Số đo 14/09/2026 |
|---|---:|
| Cuộc họp có "dự thảo / góp ý / ý kiến" trong tiêu đề | **44** |
| Tài liệu kèm các cuộc họp đó | **59** |
| Tài liệu tên có chữ "dự thảo" | **36** |
| Tài liệu tên có "góp ý" hoặc "ý kiến" | **13** |

Phân bố đều, không phải đột biến một lần:

| Tháng | 03 | 04 | 05 | 06 | 07 | 08 | 09 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Số cuộc họp bàn dự thảo | 7 | 4 | 1 | 9 | 7 | 14 | 2 |
| Tài liệu kèm | 0 | 0 | 0 | 23 | 18 | 15 | 3 |

### 2.2 Chính tên file đã lộ nguyên quy trình đang chạy tay

Một bộ hồ sơ thật trong kho, xếp theo số thứ tự người dùng tự đánh:

```
01_05.3_VB GỬI XIN Ý KIẾN GÓP Ý DT NGHỊ QUYẾT.docx
02_05.3_DỰ THẢO TỜ TRÌNH.docx
03_05.3_DỰ THẢO NGHỊ QUYẾT.docx
04_05.3_BẢN SO SÁNH, THUYẾT MINH DỰ THẢO.docx
```

và ở hồ sơ khác:

```
20250514. Tổng hợp ý kiến của các cơ quan.signed.pdf
01. UBND BC 195 bc kết quả lấy ý kiến nhân dân ve De an TP QN.pdf
DANH SÁCH CÁC NỘI DUNG XIN Ý KIẾN THÀNH VIÊN UBND TỈNH TẠI PHIÊN HỌP…
```

**Đọc ra ba việc phần mềm có thể gánh:**

1. **Phát dự thảo kèm hạn** — hiện là đính file vào cuộc họp, ai để ý thì đọc.
2. **Đòi ý kiến từng đơn vị** — hiện không có cách biết đơn vị nào chưa gửi, phải gọi
   điện/nhắn hỏi từng nơi.
3. **Tổng hợp** — hiện gõ tay thành một file Word *"Tổng hợp ý kiến"* rồi tải lên.
   Đây là khâu tốn công nhất và dễ sót nhất.

### 2.3 Một lưu ý về bản chất dòng công việc

Toàn bộ 44 cuộc họp trên đều thuộc nguồn **Lịch công tác** (sự kiện của Tỉnh/Cục dội
xuống), không phải họp do Chi cục tự tổ chức. Nghĩa là vai trò của Chi cục ở đây phần
lớn là **bên ĐƯỢC HỎI**: nhận dự thảo từ cấp trên → hỏi ý kiến các đơn vị trong Chi cục
→ gộp thành một văn bản tham gia ý kiến gửi ngược lên.

Điều này quan trọng vì nó quyết định thiết kế: thứ cần đếm là **đơn vị đã gửi / chưa
gửi**, không phải số lượt bình luận.

---

## 3. Phải chọn đúng một trong hai nghiệp vụ

Hai thứ hay bị gọi chung là "ý kiến" nhưng khác hẳn nhau:

| | **A. Ý kiến về một cuộc họp** | **B. Đợt lấy ý kiến một văn bản** |
|---|---|---|
| Gắn với | Một cuộc họp cụ thể | Một văn bản dự thảo, **không cần cuộc họp** |
| Ai nói | Người dự họp | Đơn vị / người được hỏi |
| Thời điểm | Trước · trong · sau họp | Từ lúc phát đến **hạn** |
| Cần theo dõi | Không | **Có** — đơn vị nào chưa gửi |
| Đầu ra | Đưa vào biên bản họp | **Bảng tổng hợp ý kiến** gửi cấp trên |
| Bảng có sẵn | `meeting.y_kien` ✅ | **chưa có** ❌ |

Chánh Văn phòng đang nói về **B**. Đây cũng chính là thứ tốn công nhất hiện nay.

### Vì sao `y_kien` không gánh được B

```sql
cuoc_hop_id UUID NOT NULL REFERENCES meeting.cuoc_hop(id) ON DELETE CASCADE
loai VARCHAR(20) CHECK (loai IN ('TRUOC_HOP','TRONG_HOP','SAU_HOP'))
```

Buộc phải có cuộc họp, và không có chỗ cho hạn phản hồi, đơn vị được hỏi, hay trạng
thái tiếp thu. Muốn dùng lại phải đổi schema — mà đổi xong thì nó không còn là bảng cũ.

**Điểm đáng chú ý:** thiết kế gốc của dự án **đã tính đúng chuyện này**. Bản spec 17
bảng ban đầu có riêng hai bảng `lay_y_kien_tu_xa` *(tiêu đề, mô tả, hạn phản hồi, trạng
thái — **không có** `hop_id`)* và `phan_hoi_tu_xa`. Khi cắt gọn còn 10 bảng cho bản đầu,
hai bảng này bị bỏ, chỉ giữ `y_kien`. Tức là hướng làm đã có sẵn từ đầu, chỉ là chưa làm.

---

## 4. Hiện trạng: khung đã dựng bao nhiêu phần

### 4.1 Trong Họp Không Giấy

| Thành phần | Trạng thái |
|---|---|
| Bảng `meeting.y_kien` | ✅ có bảng + model |
| Kết xuất mục "Ý kiến" vào biên bản Word | ✅ **code đã viết sẵn** nhưng chưa bao giờ chạy được |
| Schema / endpoint / giao diện cho ý kiến | ❌ **không có gì** |
| Dữ liệu | **0 dòng** — không có đường ghi nào nên bảng không thể có dữ liệu |

Nói cách khác: đây là **khung dựng sẵn rồi bỏ đó**, không phải tính năng hỏng.

> ⚠️ Hai tài liệu đang ghi sai, cần biết để khỏi nhầm khi họp bàn:
> - `MVP_REPORT_AND_ROADMAP.md` ghi *"Ý kiến phát biểu — Submit ý kiến, đính kèm file,
>   threading ✅"* — **không đúng**, không có endpoint nào.
> - Báo cáo rà soát 04/09 của tôi ghi *"gỡ tab ý kiến"* — **cũng không đúng**, tab đó
>   chưa từng tồn tại. Đã đính chính trong file đó.

### 4.2 Những thứ đã có ở module khác, dùng lại được

Đây là phần khiến việc này rẻ hơn tưởng:

| Đã có sẵn | Ở đâu | Mức dùng thật |
|---|---|---|
| Kho tài liệu + phân quyền + xem/tải/in | `meeting.tai_lieu` | **918 file, 1,6 GB** |
| Tài liệu **không cần gắn cuộc họp** | `tai_lieu.cuoc_hop_id` cho phép NULL | khung có, chưa dùng (0 file) |
| Văn bản + **hạn xác nhận** + **đối tượng áp dụng** + phiên bản + quy trình duyệt/xuất bản | `legal.van_ban` | đang chạy |
| Theo dõi **ai đã đọc / chưa đọc** + báo cáo | `legal.xac_nhan_doc` | **616 lượt**, một văn bản có 65 người xác nhận rải suốt 7 tháng |
| Thảo luận có trả lời + trích dẫn **theo điều khoản** (`can_cu_phap_ly`) | `forum.chu_de` / `forum.tra_loi` | 2 chủ đề, 14 trả lời (gần như chưa dùng) |
| Chuyên mục **"Góp ý & Đề xuất"** đã tạo sẵn | `forum.chuyen_muc` | chưa dùng |
| Gắn chủ đề thảo luận với văn bản | `forum.chu_de.van_ban_lien_quan` | khung có |
| Nhắc việc qua Zalo | worker `zalo-worker` | đang chạy thật |
| Danh mục loại tài liệu **sửa được từ giao diện** | `meeting.danh_muc` | 7 loại, thêm "Dự thảo" không cần code |
| Xuất Excel/Word | 4 chỗ trong `meeting_service` | đang chạy |

Quy mô cần phục vụ rất nhỏ: **15 đơn vị, 544 người, 55 lãnh đạo**. Một đợt lấy ý kiến
điển hình chỉ gửi tới ~14 đơn vị.

---

## 5. Ba cách làm

### Cách 1 — Bật mục "Ý kiến" trong cuộc họp *(nhỏ, nhưng KHÔNG giải quyết việc chính)*

Viết nốt phần còn thiếu cho `y_kien`: schema, service, endpoint, một tab trong trang chi
tiết cuộc họp.

- **Được**: người dự họp gửi ý kiến trước/trong/sau họp; ý kiến **tự chảy vào biên bản**
  (đoạn code đó đã viết sẵn, chỉ đang nằm im).
- **Không được**: không có hạn, không biết đơn vị nào chưa gửi, không xuất được bảng
  tổng hợp. **Khâu tốn công nhất vẫn phải làm tay.**
- **Công sức**: nhỏ (~2–3 ngày). Không migration.

### Cách 2 — Làm "Đợt lấy ý kiến" trong Họp Không Giấy ⭐ *(khuyến nghị)*

Một mục mới, độc lập với cuộc họp, đúng như thiết kế gốc `lay_y_kien_tu_xa` đã tính.

Một đợt gồm: tiêu đề · văn bản dự thảo đính kèm · đơn vị/người được hỏi · **hạn** ·
trạng thái (đang lấy ý kiến / đã đóng / đã tổng hợp).

Màn hình cần có:
- **Người phát** (Văn phòng): tạo đợt, chọn đơn vị, đặt hạn, xem **bảng theo dõi ai đã
  gửi / chưa gửi**, bấm nhắc, **xuất bảng tổng hợp ý kiến ra Word/Excel**.
- **Đơn vị được hỏi**: thấy dự thảo, gõ ý kiến (kèm file nếu cần), gửi trước hạn.

Dùng lại: kho tài liệu, danh bạ đơn vị, nhắc Zalo, khuôn xuất Excel/Word, nhật ký.
Thêm mới: 2 bảng (`dot_lay_y_kien`, `y_kien_tham_gia`), ~8 endpoint, 2–3 trang.

- **Công sức**: vừa (~1,5–2 tuần), có 1 migration.
- **Giải quyết trọn** cả ba việc ở mục 2.2.

### Cách 3 — Mở chuyên mục "Góp ý dự thảo" trên Diễn đàn *(gần như miễn phí, để thử)*

Chuyên mục **"Góp ý & Đề xuất"** đã có sẵn. Đăng dự thảo thành một chủ đề, mọi người trả
lời bên dưới; phần trả lời còn có sẵn chỗ trích dẫn **theo từng điều khoản**.

- **Công sức**: gần bằng không — chỉ là thao tác cấu hình + hướng dẫn.
- **Không được**: không hạn, không biết đơn vị nào chưa gửi, không xuất tổng hợp, và
  Diễn đàn hiện gần như chưa ai dùng (2 chủ đề). Đặt một quy trình hành chính chính thức
  lên một chỗ chưa có thói quen dùng thì rủi ro chết yểu cao.
- **Hợp để**: thử nghiệm 1–2 dự thảo xem anh em có góp ý thật không, trước khi bỏ 2 tuần
  làm Cách 2.

---

## 6. Khuyến nghị

**Làm Cách 2**, vì nó là thứ duy nhất gánh được khâu tổng hợp — chỗ đang tốn công nhất.

Nếu muốn chắc tay trước khi đầu tư, chạy **Cách 3 trong 2–3 tuần** với một dự thảo thật:
nếu các đơn vị chịu góp ý trên hệ thống thì làm Cách 2; nếu vẫn quen gửi công văn giấy
thì phần mềm có làm cũng để không — giống 6 tính năng đang 0 người dùng trong chính
module này.

**Cách 1 chỉ nên làm kèm**, không nên làm thay: nó rẻ và làm sống đoạn kết xuất biên bản
đang nằm im, nhưng không chạm được vào việc Chánh Văn phòng đang cần.

---

## 7. Rủi ro cần nói trước

| Rủi ro | Mức | Ghi chú |
|---|---|---|
| **Phân mảnh chỗ bình luận** | 🔴 Cao | Hệ thống **đã có 3 cơ chế ghi ý kiến**: `y_kien` (chưa dùng), `forum.tra_loi`, `ghi_chu` + chia sẻ (chết từ 17/06) — và **2 kho tài liệu** (`meeting.tai_lieu`, `legal.van_ban`). Thêm cái thứ tư mà không chốt "chỗ nào dùng để làm gì" sẽ khiến người dùng không biết vào đâu. **Nên chốt việc này trước khi viết dòng code đầu tiên.** |
| **Làm xong không ai dùng** | 🟡 Vừa | Tiền lệ ngay trong module: kết luận, ý kiến, xin phép vắng, tiến độ, mẫu biểu, ghi chú chia sẻ — 6 tính năng 0 người dùng. Giảm rủi ro bằng cách chạy thử Cách 3 trước. |
| **Nhầm vai** | 🟡 Vừa | Chi cục chủ yếu là bên ĐƯỢC HỎI. Nếu thiết kế theo hướng "ta phát dự thảo cho thiên hạ góp ý" sẽ lệch nhu cầu. Cần hỏi lại Chánh Văn phòng: chủ yếu là **hỏi ý kiến nội bộ để trả lời cấp trên**, hay **phát dự thảo quy chế nội bộ của Chi cục**? Hai cái cho ra hai màn hình khác nhau. |
| Tốn tiền Zalo nếu nhắc nhiều | 🟢 Thấp | 800đ/tin. Gửi 15 đơn vị × 2 lần nhắc ≈ 24.000đ/đợt. Không đáng kể. |

---

## 8. Câu cần hỏi lại Chánh Văn phòng

Trước khi làm, ba câu này quyết định thiết kế:

1. **Chủ yếu là dự thảo của cấp trên gửi xuống hỏi ý kiến Chi cục, hay dự thảo quy chế
   nội bộ của Chi cục?** (quyết định ai là người phát, ai là người góp)
2. **Đơn vị góp ý theo tư cách đơn vị (một ý kiến chính thức cho cả đơn vị), hay từng
   công chức góp riêng?** (quyết định bảng theo dõi đếm theo đơn vị hay theo người)
3. **Có cần khâu "tiếp thu / giải trình" từng ý kiến không** — tức ghi rõ ý kiến nào được
   tiếp thu, ý kiến nào không và vì sao? (nếu có thì thêm khoảng 3–4 ngày)

---

## 9. Cách kiểm chứng lại các số trong tài liệu này

```bash
cd /root/kpi-haiquan/backend && set -a && . .env && set +a

# Nhu cầu: cuộc họp + tài liệu về dự thảo
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT to_char(ngay_hop,'YYYY-MM') thang, count(*) FROM meeting.cuoc_hop
 WHERE NOT is_deleted AND (tieu_de ILIKE '%dự thảo%' OR tieu_de ILIKE '%góp ý%'
                            OR tieu_de ILIKE '%ý kiến%') GROUP BY 1 ORDER BY 1;"

# Tên tài liệu dự thảo thật
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT left(ten_tai_lieu,70) FROM meeting.tai_lieu
 WHERE NOT is_deleted AND ten_tai_lieu ILIKE '%ý kiến%';"

# y_kien rỗng và không có đường ghi
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT count(*) FROM meeting.y_kien;"
grep -rn "y_kien\|YKien" meeting_service/api/ meeting_service/schemas/   # → không kết quả

# Những thứ dùng lại được
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT count(*) FROM legal.xac_nhan_doc;"          # 616
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT ten_chuyen_muc FROM forum.chuyen_muc ORDER BY thu_tu;"   # có 'Góp ý & Đề xuất'
```

---

*Liên quan: `docs/HKG/BAO_CAO_RA_SOAT_HKG_20260904.md` (rà soát toàn module),
`docs/HKG/HKG.txt` §Module 7 (spec gốc), `docs/HKG/VP phối hợp xây dựng Module.1.txt`
(công văn yêu cầu gốc của Văn phòng).*
