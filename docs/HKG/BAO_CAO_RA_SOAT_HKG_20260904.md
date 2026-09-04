# Rà soát module Họp Không Giấy — 04/09/2026

Phạm vi: lỗi cũ còn tồn, tính năng nợ từ các đợt trước, tiến độ thực tế.

**Cách làm:** mọi con số trong báo cáo này được **đo trực tiếp** trên production
(`localhost:5432`, chỉ câu `SELECT`), trên log PM2, và bằng cách gọi thật API qua
một tiến trình tạm trỏ vào DB test. Chỗ nào chỉ là **tài liệu khai** thì ghi rõ.
Không chạy bất kỳ câu ghi nào lên production.

---

## 1. Kết luận ngắn

Module **đang chạy thật và ổn định**, nhưng trọng tâm sử dụng đã dịch hẳn khỏi
thứ mà tài liệu vẫn coi là cốt lõi.

| Câu hỏi | Trả lời |
|---|---|
| Có lỗi nào đang thực sự xảy ra trên production? | **Có 1**, lặp 4 lần/ngày, tác động thực tế gần bằng 0 nhưng gốc rễ đáng sửa (mục 3.1) |
| Có lỗi nào che mắt được không? | **Có** — 15 test đang đỏ, và **14 trong số đó thuộc đúng tính năng được dùng nhiều nhất hôm nay** (mục 3.2) |
| Tiến độ tới đâu? | Quy mô code **gấp 3 lần** tài liệu ghi; nhưng **6 tính năng đã xây xong chưa ai dùng lần nào** (mục 2.2) |
| Tài liệu tin được không? | **Không.** Mọi con số tổng quan đều sai, `README` của service sai toàn bộ (mục 5) |
| Sao lưu có lỗ hổng không? | **Không** — đã kiểm tận file, lành mạnh (mục 6.1) |

Điều đáng chú ý nhất: tài liệu xếp **"CKS thật" là nợ đỏ ưu tiên cao nhất** vì
"biên bản ký mock không có giá trị pháp lý". Nhưng đo trên production:
**cả 11 biên bản đều đang ở trạng thái `DANG_SOAN`, chưa một biên bản nào được
trình ký.** Luồng ký số chưa từng được dùng, nên món nợ này **không chặn ai cả**
— khác hẳn mức ưu tiên tài liệu gán cho nó.

---

## 2. Tiến độ thực tế

### 2.1 Quy mô code (đo trực tiếp)

| Hạng mục | Đo được 04/09/2026 | Tài liệu khai | Chênh |
|---|---|---|---|
| REST endpoint | **127** | 7 (`README`) / 39 (`MVP_REPORT`) / 55 (rà quét ATTT) | gấp 2,3–18 lần |
| Bảng schema `meeting` | **23** | 10 (`MVP_REPORT`) / 13 (rà quét ATTT) | +10 |
| Migration `meeting_*` | **25** | 11 (`mt_001`→`mt_011`) | +14 |
| Test backend | **478** | 146 / 153 / 107 / 72 (bốn con số khác nhau) | +325 |
| Trang giao diện | **12** (HKG) + **10** (Lịch công tác) | 7 | +15 |

Cách đo lại: mục 8.

### 2.2 Mức dùng thật trên production — phần quan trọng nhất

| Bảng | Số dòng | Lần dùng cuối | Nhận xét |
|---|---:|---|---|
| `cuoc_hop` nguồn `LICH_CONG_TAC` | **526** | 03/09/2026 | **Trọng tâm thật của module** |
| `tai_lieu` | **890** | 04/09/2026 | Dùng rất mạnh (1,6 GB / 1.739 file) |
| `truc_ban` | **681** | — | Dùng mạnh |
| `lanh_dao_lien_quan` | 503 | — | Đi kèm Lịch công tác |
| `thanh_phan` | 253 | — | |
| `danh_gia_cuoc_hop` | 109 | — | |
| `diem_danh` | **49** | 04/09/2026 | Chỉ 6 cuộc họp từng điểm danh |
| `ghi_chu` | 18 | **17/06/2026** | ⚠️ **chết 2,5 tháng** |
| `cuoc_hop` nguồn `HKG` | **12** | 04/09/2026 | ⚠️ Họp không giấy "thuần" rất ít |
| `bien_ban` | 11 | 04/09/2026 | **100% còn ở `DANG_SOAN`** |
| `nhom_thanh_phan` | 1 | — | ⚠️ Gần như không dùng |
| `ket_luan` | **0** | — | ⛔ **chưa dùng lần nào** |
| `xin_phep_vang` | **0** | — | ⛔ **chưa dùng lần nào** |
| `y_kien` | **0** | — | ⛔ **chưa dùng lần nào** |
| `tien_do` | **0** | — | ⛔ **chưa dùng lần nào** |
| `mau_bieu` | **0** | — | ⛔ **chưa dùng lần nào** |
| `ghi_chu_chia_se` | **0** | — | ⛔ **chưa dùng lần nào** |

Đọc bảng này ra ba điều:

1. **Module đã trở thành hệ Lịch công tác + Kho tài liệu**, không phải hệ họp
   không giấy. 526 sự kiện Lịch công tác so với 12 cuộc họp HKG — tỉ lệ 44:1.
   Vòng nghiệp vụ mà spec gốc coi là cốt lõi (mời họp → tài liệu → điểm danh →
   ý kiến → biên bản → **kết luận** → **theo dõi tiến độ**) bị **đứt ở khúc
   giữa**: có tài liệu, có điểm danh lẻ tẻ, còn kết luận và tiến độ thì bằng 0.
2. **Sáu tính năng đã xây xong nhưng chưa ai dùng lần nào.** Đây không phải nợ
   "chưa làm" mà là nợ **"làm rồi không ai cần"** — tốn công bảo trì mà không
   sinh giá trị. Tài liệu không có mục nào ghi nhận loại nợ này.
3. **Hai trong bốn job scheduler đang chạy cho bảng trống.**
   `mark_tre_han_ket_luan` và `nhac_han_ket_luan` phục vụ `ket_luan` (0 dòng);
   `auto_approve_xin_phep_vang` phục vụ `xin_phep_vang` (0 dòng) — chạy 10
   phút/lần suốt 4 tháng cho một bảng rỗng. Chỉ `nhac_hop_3_tang` làm việc thật.

### 2.3 Trình chiếu đồng bộ (Phase 4.1): tài liệu nói CHƯA deploy — thực tế ĐANG CHẠY

Tài liệu `BaoCao_TongKet_Phase4_1_PageSync.md` ghi *"✅ Code hoàn thành, **chưa
deploy production** (chờ UAT mini)"*, và cả hai checklist UAT/Deploy **không tick
ô nào**. `PHIEN_BAN_PROD.md` cũng không có dòng nào ghi mốc deploy Phase 4.1.

Nhưng log production **hôm nay** cho thấy hàng chục kết nối thật:

```
WebSocket /ws/hop-khong-giay/cuoc-hop/09aa6fa2-.../presentation?token=... [accepted]
```

và bảng `meeting.trang_thai_trinh_chieu` có 6 dòng. Nginx cũng đã mở
`/ws/hop-khong-giay/` ra ngoài.

→ **Tính năng đã lên production và đang được dùng, nhưng chưa qua UAT, chưa có
sign-off, chưa ghi vào sổ phiên bản.** Đây là rủi ro quản lý cấu hình: không ai
biết chắc bản nào đang chạy.

---

## 3. Lỗi cũ còn tồn

### 3.1 Lỗi ĐANG xảy ra trên production: mất kết nối DB trong job nền

**Bằng chứng.** `common.audit_log` không ghi việc này, nhưng log PM2 có:

```
Job "auto_approve_xin_phep_vang_job (trigger: interval[0:10:00],
     next run at: 2026-09-03 06:59:50 +07)" raised an exception
asyncpg.exceptions._base.InterfaceError: connection is closed
```

**Tần suất và phân bố** (đếm trên log PM2):

| Ngày | Số lần |
|---|---:|
| 27/08 · 30/08 · 03/09 · 04/09 | **4 lần mỗi ngày** |

| Job bị lỗi | Số lần |
|---|---:|
| `nhac_hop_3_tang_job` | **3** |
| `auto_approve_xin_phep_vang_job` | 1 |

**Gốc rễ — đã xác định.** `shared/database.py`:

```python
def create_db_engine(database_url: str, echo: bool = False):
    return create_async_engine(database_url, echo=echo, future=True)
```

Không có `pool_pre_ping=True`. Kết nối trong pool chết qua đêm khi nhàn rỗi, sáng
hôm sau job đầu tiên vớ phải kết nối đã đóng. Đúng khớp với thời điểm lỗi:
**~06:50–07:00 sáng**.

Đáng nói: trong KPI backend `app/db/session.py:38` dòng này **có sẵn nhưng bị
comment**, nằm trong khối `# Production settings:` chưa bao giờ được bật — tức
đây là việc bỏ dở, không phải quyết định có chủ ý.

**Phạm vi ảnh hưởng:** `create_db_engine` được dùng bởi **meeting, forum, portal,
legal, common** và cả `zalo_worker`. Sửa một dòng ở `shared/database.py` là khỏi
cho cả năm service.

**Tác động thực tế: gần bằng 0.** Job nhắc họp chạy **mỗi phút**, mốc nhắc có
biên độ `WINDOW_TOLERANCE = 5 phút`, và có cơ chế chống gửi trùng
(`_query_sent_pairs`). Mỗi mốc nhắc vì thế có ~10 lần thử. 3 lỗi trên 1.440 lần
chạy mỗi ngày (0,2%) gần như chắc chắn được lần chạy kế tiếp bù lại.

**Vì vậy xếp ưu tiên: Trung bình** — không phải sự cố, nhưng là mảnh giòn nằm
đúng đường đi của tin nhắc họp có tính phí, và giá sửa chỉ là một dòng.

### 3.2 15 test đang đỏ — không phải lỗi sản phẩm, nhưng mất trắng vùng phủ

Chạy `meeting_service/tests/`: **463 pass / 15 fail**. Đã đối chứng trên cây
sạch (chưa có thay đổi nào của đợt điểm danh): **cùng đúng 15 lỗi đó** → tồn tại
từ trước, không phải hồi quy.

**Nhóm A — 14 lỗi, cùng một gốc rễ: test mục ngày cắm cứng.**

`test_presentation_ws.py` và `test_presentation_rest.py` tạo cuộc họp với
`ngay_hop=date(2026, 5, 15)`. Sau đó Phase 4.1 thêm chốt chặn "cuộc họp đã kết
thúc thì không cấp WS token mới". Hôm nay ngày đó đã lùi 3,5 tháng nên mọi test
ăn:

```
410 MEETING_EXPIRED — "Cuộc họp đã kết thúc — không thể cấp WS token mới."
```

**Đây là chỗ đáng lo nhất của toàn bộ báo cáo.** Ghép với mục 2.3:
tính năng trình chiếu **đang được dùng thật hôm nay**, chưa qua UAT, chưa ghi sổ
phiên bản, **và toàn bộ 14 test bảo vệ nó đều đã mục** — sửa gì vào vùng đó cũng
không có lưới an toàn. Giá sửa rất thấp: đổi ngày cắm cứng thành ngày tương đối
(`date.today()`), giống cách `test_diem_danh.py` đang làm.

**Nhóm B — 1 lỗi: test đếm cả dữ liệu thật.**

`test_loai_tai_lieu.py:147` kỳ vọng `dang_su_dung == 1` nhưng nhận **17**, vì DB
test được clone từ production nên có 17 tài liệu thật đang dùng loại đó. Test
thiếu cách ly, không phải lỗi sản phẩm.

### 3.3 Lỗi/hạn chế đã biết theo tài liệu, kèm đối chứng thực tế

| Hạn chế | Tài liệu xếp | Đối chứng thực tế 04/09 | Ưu tiên nên đặt lại |
|---|---|---|---|
| Ký số mock không có giá trị pháp lý | 🔴 **Cao** | **11/11 biên bản còn `DANG_SOAN`, 0 biên bản trình ký** — luồng ký chưa từng chạy | ⬇️ **Thấp** đến khi có người thật cần ký |
| Ghi đè biên bản khi nhiều người soạn | 🟡 Trung | 11 biên bản / 4 tháng — xác suất hai người soạn cùng lúc rất thấp | ⬇️ Thấp |
| LibreOffice ngốn ~200MB/lần chuyển đổi, chưa có hàng đợi | 🔴 Rủi ro OOM | Máy đã có swap 8GB + chốt chặn từ sự cố OOM 25/08; nhưng dev và prod **cùng một máy** | ↔️ Giữ Trung |
| `_preview_cache` phình không dọn | P0 | ✅ **Đã có cron** Chủ nhật 03:00; hiện chỉ 12 file | ✅ Xong |
| Rate limit upload | P0 | ✅ Đã có (slowapi 10 lần/5 phút) | ✅ Xong |
| Backup tự động | P0 | ✅ Đã có, đã kiểm tận file (mục 6.1) | ✅ Xong |
| Đặt `HKG_UPLOAD_DIR` trong `.env` production | P0 | ⚠️ **Vẫn chưa đặt** (mục 6.2) | ↔️ Thấp nhưng nên dọn |
| Không có metrics/observability | ⚠️ | Vẫn chỉ có log PM2. Chính vì thế lỗi mục 3.1 lặp 4 lần/ngày suốt hơn tuần mà không ai biết | ⬆️ **Trung** |
| Danh sách họp giới hạn 50 cuộc | không xếp | **Gốc rễ ở giao diện, không phải máy chủ**: `hop-khong-giay/page.tsx:95` gọi cứng `{page: 1, limit: 50}`, trong khi endpoint đã có `page`+`limit` (mặc định 20, tối đa 100). 538 cuộc trong DB → người dùng thấy tối đa 50 | ⬆️ **Trung** (sửa chỉ ở giao diện) |

---

## 4. Tính năng còn nợ

Tài liệu liệt kê **hơn 35 hạng mục**. Dưới đây gom lại và **xếp lại ưu tiên theo
mức dùng thật**, vì thứ tự trong tài liệu được viết tháng 5/2026 khi chưa có dữ
liệu vận hành.

### 4.1 Nên làm — có người thật đang thiếu

| Việc | Nguồn | Lý do đặt lên đầu |
|---|---|---|
| Thêm phân trang cho danh sách họp | `HUONG_DAN` §24 | 538 cuộc trong DB, thấy được 50. **Máy chủ đã hỗ trợ sẵn** — chỉ cần bỏ `limit: 50` cắm cứng ở `page.tsx:95` và thêm nút chuyển trang |
| Liên kết menu tới trang Thống kê và Xin phép vắng | `HUONG_DAN` §25 | Trang đã có nhưng **phải gõ tay địa chỉ mới vào được** |
| Wire dữ liệu thật cho trang `/hop-khong-giay/thong-ke` | `MVP_REPORT` quick win #2 | Đang là bảng số giả |
| Ô chọn bật/tắt gửi Zalo cho từng cuộc họp | `HUONG_DAN` §25 | Mỗi tin 800đ; đang chờ lãnh đạo quyết |
| Trình chiếu đồng bộ cho Word/Excel/PowerPoint | `HUONG_DAN` §25 | Nay chỉ PDF, mà trình chiếu **đang được dùng thật** |

### 4.2 Nên hoãn — tài liệu xếp cao nhưng thực tế chưa ai cần

| Việc | Tài liệu xếp | Vì sao hoãn được |
|---|---|---|
| CKS thật (HSM/USB token), ~3 tuần, Phase 6 | 🔴 Cao / P1.1 | 0 biên bản trình ký |
| Biểu mẫu gửi đơn xin vắng trên giao diện | không xếp | 0 đơn; và từ 04/09 thư ký đã chấm được "Vắng có phép" kèm lý do ngay ở bảng điểm danh |
| Dashboard 3 cấp, template biên bản Đảng/Chuyên môn (Phase 8) | Phase 8 | Kết luận và ý kiến đều 0 dòng — chưa có gì để dựng bảng |
| SMS Brand Name (12–15 triệu/năm) | P1.3 / Phase 7 | Zalo đã chạy và rẻ hơn |
| Realtime collab soạn biên bản (Yjs) | P1.4 | 11 biên bản / 4 tháng |
| MinIO | P2.6 | 1,6 GB, ngưỡng tài liệu tự đặt là 50–100 GB |

### 4.3 Nợ chưa từng được ghi nhận: tính năng xây rồi không ai dùng

Tài liệu không có mục nào cho loại này. Cần **quyết định dứt khoát** cho từng
tính năng dưới đây — hoặc tổ chức lại nghiệp vụ để người dùng thực sự dùng, hoặc
gỡ khỏi giao diện để bớt gánh bảo trì:

| Tính năng | Dấu vết dùng | Đề nghị |
|---|---|---|
| Kết luận + theo dõi tiến độ | 0 dòng, nhưng **2 job scheduler** phục vụ | Hỏi Văn phòng: có định dùng không? Nếu không, tắt 2 job |
| Ý kiến (`y_kien`) | 0 dòng | Gỡ tab hoặc bỏ |
| Xin phép vắng | 0 dòng, 1 job scheduler | Bảng điểm danh mới đã thay được phần lõi |
| Mẫu biểu (`mau_bieu`) | 0 dòng | Bỏ |
| Ghi chú cuộc họp | 18 dòng, **chết từ 17/06** | Tìm hiểu vì sao bị bỏ |
| Nhóm thành phần dùng chung | **1 nhóm** trên 549 người | Có thể do khó tìm thấy — kiểm tra lối vào |

### 4.4 Việc quy trình còn treo (không phải code)

- **UAT Phase 4.1: 0/24 ô tick**, Deploy checklist 0 ô tick, không có sign-off —
  trong khi tính năng đã chạy production (mục 2.3).
- **Cần văn bản Văn phòng đồng ý cắt phạm vi Phase 4**: plan gốc 10 hạng mục để
  nâng mức đáp ứng 72% → 92%, thực tế chỉ làm 1/10 (trình chiếu). Chưa có xác
  nhận, tức **cam kết "92% cuối tháng 5/2026" đang bị treo**.
- **Cắt chuyển lichkv8 (G6.1b→G6.8): 8/8 mục còn trống**, trong đó có hai việc
  bảo mật nghiêm trọng: *505 mật khẩu dạng rõ trong Google Sheets* và *kho tài
  liệu Drive đang công khai với bất kỳ ai có link*. Hệ cũ **vẫn chạy song song**.

---

## 5. Tài liệu sai lệch với thực tế

Không một con số tổng quan nào trong tài liệu còn đúng.

| Tài liệu | Khai | Thực tế | Việc cần làm |
|---|---|---|---|
| `backend/meeting_service/README.md` | "G2 — Module 1 only", "7 endpoints", "**KHÔNG expose** ra Nginx public", "Module 3,4,5,9,10 → G3", "`minio_service.py` SKELETON" | 127 endpoint; Nginx có location block thật (`sites-enabled/kpi-haiquan` dòng 77 + 90) và `curl https://kpihaiquan.vn/api/v1/hop-khong-giay/cuoc-hop/` từ Internet trả **401** — tức đã mở ra công khai, chỉ chặn bằng xác thực; mọi module đã chạy | **Viết lại toàn bộ** — sai từ dòng đầu |
| `MVP_REPORT_AND_ROADMAP.md` | 39 endpoint · 10 bảng · 11 migration · 146 test · 4 job *"nhắc họp, đóng điểm danh, tạo nhắc tiến độ, cleanup token"* | 127 · 23 · 25 · 478 · 4 job **thật là** `nhac_hop_3_tang`, `auto_approve_xin_phep_vang`, `nhac_han_ket_luan`, `mark_tre_han_ket_luan` | Cập nhật; **3/4 tên job đang ghi sai**, và **không tồn tại** job "đóng điểm danh" (việc đóng được tính tại chỗ theo cửa sổ giờ) |
| `BaoCao_TongKet_Phase4_1_PageSync.md` | "chưa deploy production" | Đang chạy và có người dùng hôm nay | Ghi mốc deploy vào `PHIEN_BAN_PROD.md` |
| `PHIEN_BAN_PROD.md` mục "Hiện tại" | commit `81bb5b5` nhưng phần "Nội dung" lại tả Lịch công tác tuần/ngày (`97264ae`) | Hai phần lệch nhau | Viết lại phần Nội dung cho khớp commit — đúng loại lỗi mà chính file này cảnh báo |
| `HUONG_DAN_SU_DUNG_HKG.md` §25 | "Lịch họp dạng lịch tháng" chưa có | Lịch tuần + ngày đã deploy 25/08 (`97264ae`) | Gỡ khỏi danh sách nợ |
| `HUONG_DAN_SU_DUNG_HKG.md` dòng 5 | "Module đang ở giai đoạn **UAT**" | Đang phục vụ thật, 526 sự kiện | Sửa cách gọi trạng thái |
| `PHAN_TICH_VA_GOP_Y_HKG.md` | "port 8004" | 8006 | Sửa |
| `CLAUDE.md` | "JWT mở rộng (platform_roles) — Chưa implement" | Đã implement (preflight đã xác nhận từ lâu) | Tick lại |

Ngoài ra tài liệu **tự mâu thuẫn nhau** ở 20 điểm, nặng nhất là cách đánh số
phase cho cùng một hạng mục trình chiếu: gọi song song là *Phase 2*, *Phase 3*,
*Phase 4* và *Phase 4.1* tuỳ file.

---

## 6. Rủi ro vận hành — đã kiểm, kết quả

### 6.1 Sao lưu: lành mạnh (đã kiểm tận file)

Ban đầu tôi nghi có lỗ hổng vì cron khai `HKG_UPLOAD_DIR=/var/data/kpi/uploads`
trong khi tiến trình prod ghi vào `/opt/kpi-prod/backend/uploads/meeting`. **Nghi
ngờ này sai**: đường thứ hai là **symlink** trỏ về đường thứ nhất.

Đối chứng số file:

| Nơi | Số file | Dung lượng |
|---|---:|---|
| Nguồn `/var/data/kpi/uploads/meeting` | 1.739 | 1,6 G |
| Gương backup | 1.727 | 1,6 G |

12 file lệch **đều nằm trong `_preview_cache/`** — bản xem trước sinh lại được,
bị loại trừ có chủ ý. Ảnh chụp có đủ tới `20260904_1400`. Đĩa còn 33 GB / 99 GB
(dùng 66%).

### 6.2 Còn lại

| Việc | Trạng thái |
|---|---|
| `HKG_UPLOAD_DIR` chưa đặt trong `.env` prod | Đang chạy nhờ đường **tương đối** theo thư mục làm việc của tiến trình. Hoạt động đúng, nhưng sẽ ghi sai chỗ nếu ai đó khởi động service từ thư mục khác |
| Một máy chủ duy nhất, dev và prod cùng máy | Đã gây sự cố OOM 25/08 |
| Không có cảnh báo | Lỗi mục 3.1 lặp 4 lần/ngày hơn một tuần, không ai biết |
| `uploads/lms` 5,4 GB chưa sao lưu | P4 trong kế hoạch tách môi trường, còn trống |
| Off-site cho tài liệu | Chưa có — cần làm **trước** khi thu hồi chia sẻ Drive (G6.7) |

---

## 7. Đề nghị thứ tự xử lý

**Làm ngay, rẻ, chặn rủi ro thật**

1. Thêm `pool_pre_ping=True` vào `shared/database.py` — một dòng, hết lỗi mục
   3.1 cho cả năm service. Cân nhắc bật luôn khối `# Production settings` đang
   bị comment ở `app/db/session.py`.
2. Sửa ngày cắm cứng trong `test_presentation_ws.py` / `test_presentation_rest.py`
   thành ngày tương đối — phục hồi 14 test bảo vệ tính năng đang được dùng nhiều
   nhất. Cách ly lại `test_loai_tai_lieu.py:147`.
3. Ghi mốc deploy trình chiếu vào `PHIEN_BAN_PROD.md` và sửa phần "Nội dung" của
   mục "Hiện tại" cho khớp commit.
4. Viết lại `backend/meeting_service/README.md`.

**Cần lãnh đạo/Văn phòng quyết, không phải việc kỹ thuật**

5. Sáu tính năng 0 người dùng (mục 4.3): dùng hay gỡ?
6. Văn bản đồng ý cắt phạm vi Phase 4 — cam kết 92% đang treo.
7. Cắt chuyển lichkv8, đặc biệt **505 mật khẩu dạng rõ** và **kho tài liệu Drive
   công khai**.

**Việc thường, theo mức dùng thật**

8. Phân trang danh sách họp (đang chặn ở 50/538) — máy chủ đã sẵn, chỉ sửa giao diện.
9. Liên kết menu cho Thống kê + Xin phép vắng.
10. Dữ liệu thật cho trang Thống kê.
11. Cảnh báo cơ bản: PM2 restart, đĩa, job nền lỗi.

**Hoãn:** CKS thật, SMS Brand Name, MinIO, realtime collab, dashboard 3 cấp —
xem mục 4.2.

---

## 8. Cách kiểm chứng lại

```bash
# Quy mô code
cd /root/kpi-haiquan/backend && source venv/bin/activate
DB_NAME=kpi_haiquan_test ALLOW_PROD_TEST=true pytest meeting_service/tests/ --collect-only -q | tail -2
ls alembic/versions/ | grep -c '^meeting_'
find "../frontend/src/app/(main)/hop-khong-giay" -name page.tsx | wc -l

# Mức dùng thật (CHỈ SELECT trên production)
set -a && . .env && set +a
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
  -c "SELECT nguon, count(*) FROM meeting.cuoc_hop WHERE NOT is_deleted GROUP BY 1;" \
  -c "SELECT trang_thai, count(*) FROM meeting.bien_ban GROUP BY 1;"

# Lỗi job nền
grep -l "connection is closed" /root/.pm2/logs/meeting-backend-error__*.log
grep -h "in .*_job" /root/.pm2/logs/meeting-backend-error__*.log | sed 's/.*in //' | sort | uniq -c

# Job scheduler đang chạy thật
curl -s http://127.0.0.1:8006/health | python3 -m json.tool

# Trình chiếu có đang được dùng?
grep -c "presentation?token=" /root/.pm2/logs/meeting-backend-error.log

# Nginx có mở HKG ra ngoài không? (README nói KHÔNG — thực tế trả 401, tức đã mở
# kèm xác thực). Chỉ GET, không ghi gì.
grep -n "location.*hop-khong-giay" /etc/nginx/sites-enabled/kpi-haiquan
curl -s -o /dev/null -w '%{http_code}\n' https://kpihaiquan.vn/api/v1/hop-khong-giay/cuoc-hop/

# Sao lưu
find /var/data/kpi/uploads/meeting -type f | wc -l
find /var/backup/kpi_haiquan/uploads/meeting -type f | wc -l
```

---

## 9. Ghi chú về đợt việc 04/09/2026

Nhánh `feature/hkg-diem-danh-chi-tiet` (commit `fec9275` + `dba30f9`) đã thêm
bảng điểm danh chi tiết, chấm tay và xuất Excel; gỡ được mục *"Màn hình thư ký
bấm điểm danh tay"* khỏi §25.

**✅ ĐÃ PHÁT HÀNH 04/09/2026 22:45 — prod đang ở `dba30f9`.**

Nhánh này được tạo từ `feature/kpi-sua-ngay-dieu-chuyen` nên chứa sẵn 2 commit
KPI (`699cbc1`, `0cd7daa`) sửa `backend/app/`. Đã báo trước và người dùng chọn
phát hành cả hai cùng lượt, nên chỉ cần một SHA. 8/8 dịch vụ trả 200 sau khi
nạp; hai route mới trả 401 từ Internet (có route, đòi xác thực); `prod` và
`main` cùng ở `dba30f9`; cây `/opt/kpi-prod` gắn đúng nhánh `prod`, không để
lại detached HEAD. Không có migration nên điểm quay lui gọn:
`trien_khai.sh c53d843`.

Còn **1 nhánh chờ phát hành**: `feature/lms-reset-luot-thi` (1 commit, **có
migration** `lms_reset_luot_thi_20260831`) — cố ý để lại cho đợt sau.

Ghi chú đính chính: bản đầu của báo cáo này viết *"prod và main đang khớp nhau
tại `81bb5b5`"*. Không chính xác — `81bb5b5` là mốc **code** được ghi trong sổ,
còn hai nhánh khi đó thực tế ở `c53d843` (commit ghi sổ, đứng sau `81bb5b5`).
