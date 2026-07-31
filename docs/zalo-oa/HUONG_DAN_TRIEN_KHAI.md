# Kênh thông báo Zalo OA — Hướng dẫn triển khai

**Trạng thái:** Code xong, CHƯA bật, CHƯA áp migration lên production.
**Nhánh:** `feature/hkg-zalo-oa`
**Phạm vi giai đoạn 1:** chỉ module HKG (Họp Không Giấy).

---

## 1. Vì sao làm

Đo trên dữ liệu thật của `common.thong_bao` (8.867 bản ghi, ngày 31/07/2026):

| Loại | Số lượng | Tỷ lệ đọc | Trung vị thời gian tới lúc đọc |
|---|---|---|---|
| LMS | 5.040 | 55,3% | 56,9 giờ |
| KPI | 3.133 | 28,9% | 160 giờ |
| MEETING | 694 | 44,2% | **58,2 giờ** |

133 công chức chưa từng đọc một thông báo nào.

Trung vị 58 giờ nghĩa là lời nhắc họp tới tay người nhận **sau khi cuộc họp đã
tan**. Logic nhắc họp không sai — scheduler HKG đã nhắc đúng ở 3 mốc 24h/1h/30
phút — vấn đề là thông báo in-app chỉ hiện khi người ta đăng nhập, mà phần lớn
công chức chỉ đăng nhập vài lần mỗi tháng.

Zalo không thêm tính năng nhắc họp nào cả. Nó chỉ là **đường ống giao hàng mới**
cho những thông báo vốn đã được sinh ra đúng lúc.

---

## 2. Quyết định thiết kế (và lý do)

### 2.1. Đặt ở `common_service`, không đặt trong `meeting_service`

Bảng `common.thong_bao` đang phục vụ cả KPI (3.133), LMS (5.040) và MEETING
(694). Nếu viết Zalo trong `meeting_service` thì sớm muộn phải copy sang 2
module còn lại. Đặt ở `common_service` thì bật thêm module chỉ là đổi biến
`ZALO_LOAI_BAT`.

### 2.2. Worker QUÉT BẢNG, không gắn hook lúc ghi thông báo

Đây là quyết định quan trọng nhất, và lý do rất cụ thể.

`common.thong_bao` hiện có **hai đường ghi khác nhau**:

| Module | Cách ghi |
|---|---|
| KPI | HTTP → `POST /internal/v1/thong-bao` (`app/core/thong_bao_helper.py:48`) |
| LMS | HTTP → `POST /internal/v1/thong-bao` (`lms_service/services/thong_bao_helper.py:47`) |
| **HKG** | **INSERT raw SQL thẳng vào bảng** (`meeting_service/services/notification_service.py:35`) |

Nếu gắn hook gửi Zalo vào `thong_bao_service.tao_thong_bao()` — chỗ trông tự
nhiên nhất — thì **KPI và LMS có Zalo còn HKG thì không**, đúng module cần
trước. Và nó sẽ hỏng **im lặng**, vì INSERT vẫn thành công bình thường.

Quét bảng bắt được mọi đường ghi, kể cả module thứ tư sau này lại ghi bằng
cách thứ ba. Test `test_zalo_outbox.py::test_bat_duoc_thong_bao_hkg_ghi_bang_raw_sql`
canh giữ đúng điều này.

Hệ quả tốt: **không phải sửa một dòng nào** trong HKG, KPI hay LMS.

### 2.3. Không đụng vào bảng `common.thong_bao`

Không thêm cột nào. Quan hệ là một chiều: `zalo_outbox.thong_bao_id` → FK
sang `thong_bao`. Nhờ vậy bật/tắt Zalo không có rủi ro nào với đường ghi
thông báo hiện có của 3 module.

### 2.4. ZNS (gửi theo số điện thoại), không dùng OA message API

| | OA message API | **ZNS** |
|---|---|---|
| Gửi đến | `user_id` | **số điện thoại** |
| Cần follow OA trước? | **Có** | Không |
| Nội dung | Tự do (trong 7 ngày) | Chỉ template đã duyệt |

Zalo **không có API tra số điện thoại → `user_id`** (chặn có chủ đích vì
riêng tư). `user_id` chỉ sinh ra khi người dùng chủ động follow OA hoặc ủy
quyền qua Zalo Login. Bắt 544 công chức cùng follow là rủi ro triển khai lớn
nhất, nên giai đoạn 1 đi bằng ZNS.

Giai đoạn 2 có thể bổ sung `zalo_user_id` (cột đã có sẵn trong `zalo_lien_ket`)
cho ai có follow, để gửi tin miễn phí và linh hoạt hơn.

### 2.5. Chính sách "chuông cửa" — không gửi nội dung

Tin Zalo chỉ báo **có việc** và **khi nào**. Không có tiêu đề cuộc họp, địa
điểm, thành phần hay tài liệu. Muốn xem chi tiết thì mở phần mềm.

Ba lợi ích cùng lúc:
1. Dữ liệu họp nội bộ không đi qua máy chủ bên thứ ba (VNG).
2. Số điện thoại có thể đã đổi chủ — người lạ nhận được tin cũng không đọc
   được gì.
3. Template ít tham số thì dễ được Zalo duyệt hơn.

Test `test_zalo_templates.py::TestChinhSachChuongCua` canh giữ quyết định này:
nếu ai đó thêm tiêu đề vào tham số template, test sẽ đỏ.

---

## 3. Những gì đã có trong nhánh

```
backend/alembic/versions/zalo_oa_20260731.py      migration 3 bảng
backend/common_service/models/zalo.py             models + hằng số trạng thái
backend/common_service/services/zalo/
    phone.py        chuẩn hóa SĐT VN → 84xxxxxxxxx (thuần túy, 50 test)
    templates.py    ánh xạ 6 loại thông báo → 4 template ZNS
    token_store.py  giữ OAuth token (refresh_token XOAY VÒNG)
    client.py       gọi ZNS, có dry-run, phân loại lỗi
    outbox.py       quét → xếp hàng → gửi → retry backoff
backend/common_service/workers/zalo_worker.py     tiến trình nền
backend/scripts/zalo_import_sdt.py                import SĐT (mặc định chạy khô)
backend/scripts/zalo_nap_token.py                 nạp refresh_token lần đầu
backend/common_service/tests/test_zalo_*.py       81 test
```

**Kiểm chứng đã chạy:** 81/81 test Zalo PASS. Bộ test cũ của `common_service`
có 9 fail — đã đối chứng bằng `git stash` phần thay đổi của tôi, **fail y hệt**
→ có sẵn từ trước (test phụ thuộc dữ liệu clone prod), không phải do đợt này.

---

## 4. Ba lớp an toàn

Code này merge vào nhánh chính cũng **không thể vô tình nhắn cho ai**:

1. `ZALO_ENABLED=false` (mặc định) → worker không chạy vòng lặp nào.
2. `ZALO_DRY_RUN=true` (mặc định) → có chạy, có xếp hàng, nhưng **chỉ ghi log**,
   không gọi API Zalo.
3. `ZALO_TPL_*` để trống → đánh dấu `BO_QUA/KHONG_CO_TEMPLATE` thay vì gửi lỗi.

Thêm khung giờ yên tĩnh mặc định 6h–22h giờ VN, chặn ở tầng dữ liệu chứ không
tin vào lịch chạy của scheduler.

> **Vì sao chặn ở tầng dữ liệu:** scheduler của HKG đang chạy timezone **UTC**
> (`CronTrigger(hour=8)` = 15:00 giờ VN). Hiện lệch giờ chỉ làm badge hiện sớm/
> muộn, không ai để ý. Khi có Zalo, mọi sai lệch giờ sẽ thành tin nhắn rung
> điện thoại lãnh đạo lúc nửa đêm. Nên rà lại phần giờ của scheduler HKG
> **trước** khi bật kênh đẩy.

---

## 5. Còn thiếu gì để chạy thật

### 5.1. Xác nhận với VNG (đường găng — làm trước tiên)

OA của Chi cục là loại **cơ quan nhà nước đã xác thực**. Cần hỏi VNG hai câu:

1. OA này có được bật **ZNS** không?
2. Mức phí / ưu đãi cho cơ quan nhà nước ra sao?

Nếu ZNS không bật được thì toàn bộ kế hoạch phải quay về hướng OA-follow, và
đó là dự án khác hẳn về công sức triển khai.

> Chính sách, hạn mức và giá ZNS của VNG thay đổi thường xuyên. Đừng lập kế
> hoạch dựa vào tài liệu cũ — hỏi trực tiếp.

### 5.2. Bốn template ZNS cần xin duyệt

Đếm từ dữ liệu thật của HKG:

| `doi_tuong_type` | Số lượng | Template |
|---|---|---|
| GIAY_MOI_HOP | 245 | Giấy mời họp |
| NHAC_HOP_24H / 1H / 30P | 360 | **Gộp 1 template**, mốc là tham số |
| THAY_DOI_HOP | 50 | Thay đổi lịch họp |
| HUY_HOP | 39 | Hủy họp |

Tham số tối đa: `ho_ten`, `thoi_gian`, `moc`. Không có gì khác.

Khối lượng thực tế ~100 tin/tháng (694 tin trong 7 tháng).

### 5.3. Danh sách số điện thoại

Hiện **chỉ 6/544** công chức có số trong DB. `public.cong_chuc.so_dien_thoai`
là cột số điện thoại duy nhất trong toàn hệ thống — danh sách đầy đủ đang
nằm ngoài phần mềm.

Cần file Excel/CSV có 2 cột `ma_cc` + `so_dien_thoai`.

**Lưu ý pháp lý:** số điện thoại là dữ liệu cá nhân theo Nghị định
13/2023/NĐ-CP. Nên có văn bản thông báo nội bộ cho công chức biết trước khi
dùng để gửi thông báo. Hệ thống đã có sẵn cờ `da_dong_y` để ai yêu cầu ngừng
nhận thì tắt riêng người đó.

---

## 6. Quy trình bật (theo thứ tự, không đảo)

```bash
cd /root/kpi-haiquan/backend && source venv/bin/activate

# --- Bước 1: đối chiếu số điện thoại, CHẠY KHÔ, chưa ghi gì ---
PYTHONPATH=$PWD python scripts/zalo_import_sdt.py danh_sach.xlsx \
    --xuat-loi loi_can_ra_soat.csv
# Xem báo cáo: độ phủ bao nhiêu %, bao nhiêu số sai, bao nhiêu số trùng.
# Gửi loi_can_ra_soat.csv cho các đơn vị rà lại.

# --- Bước 2: ghi thật (chỉ ghi vào common.zalo_lien_ket) ---
PYTHONPATH=$PWD python scripts/zalo_import_sdt.py danh_sach.xlsx --ghi

# --- Bước 3: áp migration (LƯU Ý: đây là production) ---
alembic upgrade head

# --- Bước 4: điền credential vào backend/.env ---
#   ZALO_APP_ID / ZALO_OA_ID / ZALO_OA_SECRET
#   ZALO_TPL_* (4 template ID Zalo cấp sau khi duyệt)

# --- Bước 5: nạp refresh_token lần đầu ---
PYTHONPATH=$PWD python scripts/zalo_nap_token.py --hoi

# --- Bước 6: chạy thử KHÔ, xem log, chưa gửi tin nào ---
ZALO_ENABLED=true PYTHONPATH=$PWD \
    python -m common_service.workers.zalo_worker --mot-vong
# Kiểm tra: SELECT trang_thai, ly_do_bo_qua, COUNT(*)
#           FROM common.zalo_outbox GROUP BY 1,2;

# --- Bước 7: bật thật (SAU khi bước 6 sạch) ---
# .env: ZALO_ENABLED=true, ZALO_DRY_RUN=false
pm2 start "python -m common_service.workers.zalo_worker" \
    --name zalo-worker --cwd /root/kpi-haiquan/backend \
    --interpreter /root/kpi-haiquan/backend/venv/bin/python
pm2 save
```

**Khuyến nghị bật dần:** giai đoạn đầu đặt `ZALO_LOAI_BAT=MEETING` và chỉ
import số của một đơn vị (ví dụ Văn phòng) để chạy thử một tuần, rồi mới mở
rộng toàn Chi cục.

---

## 7. Ghi chú cho hồ sơ ATTT (liên quan CV 153/CNTT)

Mấy điểm cần đưa vào hồ sơ rà quét:

1. **Đây là phụ thuộc bên thứ ba ĐẦU TIÊN của hệ thống.** Trước đợt này backend
   không gọi ra bất kỳ domain ngoài nào — mọi lời gọi `httpx` đều là nội bộ
   giữa các service qua localhost. Từ nay có một điểm phụ thuộc ra ngoài
   (`openapi.zalo.me`, `business.openapi.zalo.me`) mà ta không kiểm soát được
   tình trạng hoạt động.

2. **Egress hiện đang mở hoàn toàn** (`ufw` inactive, `iptables OUTPUT` policy
   ACCEPT). Nên whitelist domain Zalo thay vì để mở hết.

3. **Không mở webhook.** Giai đoạn 1 chỉ gọi ra, không nhận vào — cố ý như vậy
   để không thêm bề mặt tấn công công khai. Nếu sau này cần webhook nhận trạng
   thái gửi, **bắt buộc** xác thực chữ ký `X-ZEvent-Signature` trước khi xử lý
   payload, cộng rate limit.

4. **Secret mới**: `ZALO_OA_SECRET` nằm trong `backend/.env`. File này hiện
   đang là mode **644 (world-readable)** — nên siết về **600** trước khi thêm
   secret mới vào.

5. **Số điện thoại trong log đã được che** (`0913***358`) — xem
   `phone.che_giau()`. Không ghi nguyên số vào file log.

6. **Token không nằm trong `.env`** mà ở DB, vì `refresh_token` xoay vòng.

---

## 8. Vận hành: trả lời "vì sao anh A không nhận được tin"

Hệ thống ghi lại **cả trường hợp không gửi**, kèm lý do, nên không phải suy đoán:

```sql
SELECT ob.trang_thai, ob.ly_do_bo_qua, ob.ma_loi, ob.mo_ta_loi,
       ob.so_lan_thu, ob.ngay_gui, cc.ma_cc, cc.ho_ten
FROM common.zalo_outbox ob
JOIN public.cong_chuc cc ON cc.id = ob.cong_chuc_id
WHERE cc.ma_cc = '20ZZ-0097'
ORDER BY ob.created_at DESC
LIMIT 20;
```

Ý nghĩa các lý do bỏ qua:

| `ly_do_bo_qua` | Nghĩa | Xử lý |
|---|---|---|
| `KHONG_CO_SDT` | Chưa import số cho người này | Bổ sung vào danh sách |
| `DA_TU_CHOI` | Đã tắt nhận, hoặc số bị đánh dấu lỗi | Kiểm tra `zalo_lien_ket.trang_thai` |
| `KHONG_CO_TEMPLATE` | Template chưa được cấu hình | Điền `ZALO_TPL_*` vào `.env` |

Danh sách số cần đơn vị rà lại (Zalo báo số sai/không tồn tại):

```sql
SELECT cc.ma_cc, cc.ho_ten, dv.ten_don_vi, lk.so_dien_thoai
FROM common.zalo_lien_ket lk
JOIN public.cong_chuc cc ON cc.id = lk.cong_chuc_id
LEFT JOIN public.don_vi dv ON dv.id = cc.don_vi_id
WHERE lk.trang_thai = 'SO_LOI';
```
