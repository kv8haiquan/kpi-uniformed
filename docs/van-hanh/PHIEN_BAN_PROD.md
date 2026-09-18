# Mốc phiên bản production

Ghi lại commit đang phục vụ người dùng, để luôn có điểm quay lui xác định.
Cập nhật mỗi lần triển khai.

## Hiện tại

| | |
|---|---|
| **Commit** | `41058a3` |
| **Ngắn** | `41058a3` |
| **Nhánh nguồn** | `feature/kpi-tieu-chi-theo-quy` (fast-forward thẳng từ `c825d1d`) |
| **Ngày ghi mốc** | 18/09/2026 21:27 |
| **Alembic** | `kpi_tc_theo_quy_20260918` — **CÓ migration** (thêm cột `danh_gia_thang.la_phieu_tc_quy`) |

Nội dung: **KPI — chấm tiêu chí chung theo QUÝ từ quý III/2026 (Công văn 21169).**

Công văn số 21169/CHQ-TCCB ngày 28/8/2026 của Cục Hải quan và công văn triển khai
của Chi cục (đã ký): *"Từ quý III/2026, kỳ đánh giá, xếp loại trên Phần mềm được
thiết lập theo quý"*, giao hoàn thành **trước kỳ đánh giá quý III**. Hồ sơ quý nộp
chậm nhất **ngày 23 tháng cuối quý** — với quý III là 23/9/2026, năm ngày sau khi
phát hành bản này. Công văn cũng **thay thế 6 công văn cũ** của Chi cục, trong đó
có CV 1909 hướng dẫn đánh giá hằng tháng ⇒ kỳ đánh giá THÁNG hết hiệu lực.

**Cách làm — phiếu tiêu chí của quý NEO ở tháng cuối quý.** Không tạo bảng mới:
việc chấm và duyệt chỉ diễn ra trên MỘT bản ghi `danh_gia_thang` — bản ghi tháng
cuối quý (T3/T6/T9/T12), đánh dấu bằng cột mới `la_phieu_tc_quy`. Hai tháng còn
lại đọc xuyên sang bản ghi neo qua `app/core/ky_tieu_chi.py`. Lý do chọn hướng
này: toàn bộ luồng duyệt 2 cấp (tự chấm · duyệt · từ chối · trả lại · duyệt hàng
loạt · lịch sử · khoá CCT · xử lý đơn mồ côi khi chuyển đơn vị) khoảng 1.300 dòng
backend và màn hình duyệt 1.568 dòng được tái dùng NGUYÊN VẸN; dựng bảng riêng
nghĩa là viết lại tất cả, không khả thi trong năm ngày.

**Nguyên tắc an toàn: chỉ đổi nơi ĐỌC, không ghi đè dữ liệu cũ.** KHÔNG đồng bộ
ngược điểm quý vào bản ghi T7/T8 — việc đó sẽ đè 517 + 322 đơn đã duyệt trên
production và không hoàn tác được. Đổi lại, tám điểm đọc phải rà đủ:
`xep_loai_quy_helpers._lay_tc_chung_thang` (cửa vào của TOÀN BỘ điểm quý),
`bao_cao_xep_loai` (2 chỗ), `xep_loai_moi` (2 chỗ), `in_bang_ke` (phiếu tháng +
phiếu quý), `doi_soat_danh_gia` (bỏ qua thì báo nhầm cả 544 người "chưa chấm"),
`phieu_danh_gia_thang`/`_quy`, `export_bao_cao`.

Phiếu quý 02A/02B nay lấy thẳng chi tiết của phiếu quý, bỏ bước gộp trung bình
ba tháng. Kỳ tháng bị chặn LẬP MỚI (báo cáo xếp loại tháng + phiếu đánh giá
tháng) và ẩn khỏi giao diện; bản ghi cũ vẫn xem và in bình thường.

Kiểm chứng trước khi phát hành, trên `kpi_haiquan_test` nhân bản từ prod:
**116 passed** (11 test mới đều PASS), trong đó phép thử **không hồi tố** đối
chiếu 160 bản ghi thật của T1/T4/T5/T6 2026 — điểm trước và sau giống hệt — và
phép thử luồng thật: CC gửi duyệt → lọc bằng tháng 7 vẫn ra phiếu quý → Phó
duyệt cấp 1 → Trưởng duyệt cấp 2 → cả ba tháng đọc ra cùng con điểm. Hai test đỏ
còn lại (`test_bao_cao_da_phe_duyet_bao_400`, `test_cct_no_assignment_empty_scope`)
đã đỏ SẴN trên code gốc, đã đối chứng bằng cách stash thay đổi và chạy lại.
Sau triển khai: 8/8 dịch vụ health 200, `kpihaiquan.vn` 200, migration đã áp,
dữ liệu cũ nguyên vẹn (T7 còn đủ 517 đơn có điểm, 34.680 dòng chi tiết tiêu chí).

**Quay lui không cần migration ngược:** đặt `TC_THEO_QUY_TU = (9999, 1)` trong
`app/core/ky_tieu_chi.py` rồi phát hành lại — toàn hệ thống trở về chấm theo
tháng ngay, dữ liệu phiếu quý nằm im, cột mới vô hại.

**Lưu ý vận hành:** lúc phát hành đã có **87 công chức tự chấm cho tháng 9/2026**
theo luồng cũ. Vì T9 chính là tháng neo của quý III, các đơn đó trở thành phiếu
Quý 3 luôn, không phải nhập lại — nhưng họ điền khi đang nghĩ là "tháng 9", nên
cần nhắc rà lại cho đúng phạm vi cả quý.

Phần còn lại của công văn (cờ định tính hạ loại, trần "lãnh đạo không cao hơn đơn
vị", tỷ lệ HTXS, quy tắc công tác ≤ 1 tháng/quý, nhắc hạn ngày 23, xếp loại NĂM
từ 4 quý) chưa làm trong đợt này — xem
`docs/cong-van-21169/KE_HOACH_TIEU_CHI_CHUNG_THEO_QUY.md` mục 9.

### Mốc trước — `4aaa43e`

Nội dung: **KPI — điều chuyển nhân sự hàng loạt theo quyết định, bằng file Excel.**

Một quyết định điều động là MỘT sự kiện: một ngày hiệu lực, một danh sách người.
Nhưng giao diện bắt nhập như N sự kiện rời rạc — mở modal từng người. Hậu quả đo
được trên chính dữ liệu đợt điều động 2026: đợt 04/02 **bỏ quên trọn 62 người**,
đợt 03/7 nhập được 1/3, đợt 15/5 ngày hiệu lực rải ra 6 ngày vì nhập nhiều buổi,
và 4 người nhập nhầm đơn vị phải chuyển đi/chuyển lại sinh 8 bản ghi rác.

Đợt `dba30f9` (04/09) đã chặn được NGÀY sai — bỏ điền sẵn ngày hôm nay, bắt buộc
nhập, cảnh báo lệch quá 15 ngày. Nhưng không chặn được BỎ SÓT NGƯỜI, vì vẫn phải
nhập lẻ từng người. Đây là nửa còn lại.

Ba endpoint, cố ý tách rời — `/api/v1/admin/dieu-chuyen-hang-loat/`:
`mau-excel` (GET, sinh mẫu) · `xem-truoc` (POST, đọc + đối chiếu, KHÔNG ghi) ·
`ghi` (POST, cả đợt trong MỘT transaction). Trang `/admin/dieu-chuyen-hang-loat`.

**Mẫu 4 sheet, sheet nhập liệu để TRỐNG:**
`Nhap lieu` (Mã CC · Đơn vị đến dropdown · Ngày hiệu lực · Số QĐ tuỳ chọn) ·
`Huong dan` (cách điền + ví dụ) · `Danh sach cong chuc` (543 người còn hoạt động,
để copy mã CC sang) · `Ma don vi` (15 đơn vị).

Ví dụ đặt ở sheet hướng dẫn chứ KHÔNG trên sheet nhập — để trên sheet nhập thì sẽ
có lần quên xoá rồi nhập nhầm người mẫu vào thật.

**Khoá là Mã CC, không phải họ tên.** File theo dõi của TCCB chỉ có họ tên, và
khớp theo tên đã hỏng ở đợt 2026: 5 người không khớp vì DB gắn hậu tố năm sinh
("Nguyễn Viết Cường 1971"), 8/142 dòng trùng tên gốc, một ca phải tra bốn nguồn
mới tách được. Mã CC gõ sai thì hoặc không tìm thấy (báo lỗi to), hoặc trỏ sang
người khác — mà bảng xem trước dội lại HỌ TÊN + ĐƠN VỊ HIỆN TẠI nên nhìn là thấy.
Khác hẳn khớp theo tên: sai mà im lặng.

**Còn một dòng lỗi thì từ chối cả đợt.** Ghi một nửa rồi báo "59/62 thành công" là
đẩy việc dò tìm 3 dòng còn lại sang người dùng. Endpoint `ghi` đọc và đối chiếu
LẠI TỪ ĐẦU, không tin kết quả xem trước phía client.

Mỗi dòng một ngày hiệu lực riêng → một file xử lý được nhiều đợt cùng lúc, đúng
như file 2026 chứa cả 4 đợt.

Kèm một refactor: hệ quả dữ liệu khi đổi đơn vị (khoá đánh giá tháng cũ, xoá mềm
kê khai nháp, gỡ khỏi báo cáo chưa duyệt) tách từ `admin.transfer_user` ra
`app/core/dieu_chuyen.py`, dùng CHUNG cho cả hai luồng. Để mỗi bên một bản thì chỉ
cần sửa một bên là kê khai/xếp loại của người vừa chuyển bị xử lý khác nhau tuỳ
admin bấm nút nào.

Kiểm chứng trước khi phát hành: **13/13 test mới PASS** trên `kpi_haiquan_test`
(gồm ca then chốt — một dòng lỗi thì dòng hợp lệ cũng KHÔNG được ghi); chạy thử
đầu-cuối sinh mẫu → điền → xem trước → ghi → tải lại cùng file ra "bỏ qua 3, ghi 0"
(idempotent); regression 52 pass / 1 fail (`test_bao_cao_da_phe_duyet_bao_400` đỏ
SẴN từ trước, đã đối chứng trên code gốc); `tsc --noEmit` + `eslint` + `npm run build`
sạch. Sau triển khai: 8/8 dịch vụ health 200, ba endpoint mới trả 401 (có route,
đòi đăng nhập — đúng), `kpihaiquan.vn` 200.

> Ghi chú quy trình: mục "Hiện tại" trước đây ghi `13647f8`, nhưng prod thực tế đã
> đi tiếp tới `2bd8508` (lọc danh sách thí sinh ĐGNL) mà không ai cập nhật sổ —
> đúng loại lệch mà ghi chú 25/08 bên dưới đã cảnh báo. Nay `2bd8508` đã có hàng
> riêng trong bảng lịch sử.

### Mốc trước — `13647f8`

Nội dung: **ĐGNL — công cụ reset lượt thi cho quản trị đào tạo, có nhật ký.**

Khi có người đăng nhập nhầm tài khoản rồi làm bài ĐGNL, cách duy nhất để trả lượt
thi cho chủ tài khoản là sửa tay bằng SQL trên database đang phục vụ người dùng:
không ai kiểm soát phạm vi, không lưu vết ai sửa và vì sao, bản ghi cũ mất hẳn nếu
người sửa quên chụp lại. Đã xảy ra hai lần trong mười ngày — `20ZZ-0431` ngày
31/08 và `20ZZ-0005` ngày 10/09 (xem `docs/fix-reset-luot-thi/NHAT_KY_RESET.md`).
Gốc rễ không phải một lần sửa nhầm, mà là thiếu hẳn đường đi hợp lệ cho một
nghiệp vụ có thật.

Nay quản trị đào tạo bấm nút **Reset** ngay trên trang thống kê kỳ thi, hai mức:
`XOA_SACH` (về `CHUA_THI`, trả lại đủ lượt, kết quả người làm nhầm biến mất khỏi
báo cáo) và `MO_KHOA_LUOT` (giữ kết quả, chỉ gỡ cờ `da_xac_nhan`). Lý do là bắt
buộc; bảng `lms.lich_su_reset_thi` ghi ai reset · cho ai · vì sao · điểm và trạng
thái trước đó, kèm ảnh chụp NGUYÊN TRẠNG bản ghi `thi_sinh` và các lần vi phạm
trong `du_lieu_truoc` — xoá rồi vẫn dựng lại được. FK dùng `ON DELETE SET NULL`
chứ không CASCADE: nhật ký phải sống lâu hơn đối tượng nó ghi lại.

Cả hai mức đều xoá dòng `lms.phien_thi`; không xoá thì thiết bị của người làm
nhầm còn giữ token và nộp tiếp được vào bản ghi vừa reset. Các trường hợp mở khoá
vô nghĩa bị chặn bằng mã lỗi riêng thay vì im lặng không làm gì: chưa nộp bài
(`DGNL_051`), chưa hề bị khoá (`DGNL_052`), đã dùng hết lượt (`DGNL_053` — nói
thẳng là phải dùng Xoá sạch). Hai endpoint mới, chỉ admin:
`POST /api/v1/lms/ky-thi/{id}/thi-sinh/{cc_id}/reset` và
`GET /api/v1/lms/ky-thi/{id}/lich-su-reset`.

Kiểm chứng trước khi phát hành: **265/265 test LMS PASS** trên `kpi_haiquan_test`
(13 test riêng cho luồng này — hai mức reset, bốn nhánh từ chối, nhật ký ghi đủ,
lọc theo thí sinh, chặn CCT và công chức thường), migration lên → xuống → lên sạch
trên DB test, `tsc --noEmit` sạch. Migration chỉ THÊM một bảng mới, không sửa bảng
nào sẵn có.

> Ghi chú quy trình: `6c7270d` cắt từ `c53d843` (28/08), trong khi prod đã đi
> thêm 9 commit. Triển khai thẳng SHA gốc sẽ **lùi prod về 28/08** — mất bài tập
> PDF/Word, bảng điểm danh HKG và hai fix ngày hiệu lực điều chuyển. Đã rebase
> lên `prod` thành `13647f8` rồi mới phát hành. Rebase không xung đột: hai file
> trùng (`frontend/src/services/lms.ts`, `types/lms.ts`) đổi ở hunk khác nhau.
>
> Hai commit `c358641` (xem bài nộp Word khi chấm) và `914125d` (thiết kế lại
> chứng chỉ) trên nhánh `upload-pdf-dao-tao` **chưa** lên prod, đợt này không kéo theo.

### Mốc trước — `d15b850`

Nội dung: **LMS — bài tập thực hành nhận file PDF và Word, không chỉ video.**

Bài kiểm tra loại `THUC_HANH` trước đây được thiết kế riêng cho video: mặc định
`dinh_dang_cho_phep = "mp4,mov,webm"`, toàn bộ nhãn giao diện ghi "nộp video",
và màn chấm bài luôn dựng thẻ `<video>`. Cột `dinh_dang_cho_phep` vốn đã cho
phép gõ `pdf` từ `add_lms_bkt_thuc_hanh_20260422`, nhưng làm vậy thì giảng viên
mở bài nộp ra chỉ thấy khung đen — nên trên thực tế tính năng chưa dùng được.

Nay giảng viên chọn định dạng bằng nút bấm (📕 PDF · 📘 Word · 📄 PDF+Word ·
🎬 Video · 📎 Tất cả). Màn nộp bài và màn chấm bài hiển thị theo đúng loại file:
iframe cho PDF, trình phát cho video, ảnh cho ảnh, nút tải về cho tài liệu
Office. Học viên xem trước được bản PDF trước khi bấm nộp.

Endpoint mới `POST /bai-kiem-tra/{id}/nop-bai-thuc-hanh`; `/nop-video` giữ
nguyên làm bí danh (ẩn khỏi OpenAPI) để client đã phát hành không vỡ.

Kèm một lớp chống đổi đuôi file: đối chiếu chữ ký (magic bytes) ở đầu file
TRƯỚC khi ghi xuống đĩa, phủ pdf/doc/docx/xls/xlsx/ppt/pptx. Hai chỗ dễ chặn
nhầm đã xử lý — docx/xlsx/pptx thực chất là ZIP nên đối chiếu tiền tố `PK`;
`.doc` chấp nhận CẢ chữ ký OLE2 lẫn `{\rtf` vì Word vẫn lưu RTF dưới đuôi
`.doc`, chỉ nhận OLE2 sẽ loại oan bài nộp thật.

Kiểm chứng trước khi phát hành: 21/21 test `lms_service/tests/test_bai_kiem_tra.py`
PASS trên `kpi_haiquan_test` (11 test mới cho luồng nộp file), 11 test vitest cho
`lib/bai-nop-file.ts`, `tsc --noEmit` sạch. Không đụng dữ liệu production.

> Ghi chú quy trình: nhánh `upload-pdf-dao-tao` cắt từ nhánh làm việc dở
> `feature/kpi-mo-lai-tieu-chi-chung` nên mang theo 2 commit không liên quan —
> `85cbedf` (thêm `scripts/mo_lai_tieu_chi_chung.py`, script chạy tay, đã đối
> chứng không nơi nào import nên trơ lúc chạy) và `a828e89` (chỉ tài liệu). Đã
> báo và người dùng chọn phát hành cả 4 commit cùng lượt, nên truyền một SHA
> `d15b850` là đủ.
>
> Còn nợ: xem `.docx` ngay trong màn chấm bài. Trình duyệt không đọc được
> `.docx` (bản chất là ZIP chứa XML) nên hiện chỉ có nút tải về. Hướng đã chốt
> là dùng `docx-preview` dựng ở TRÌNH DUYỆT người chấm, KHÔNG chuyển sang PDF
> bằng LibreOffice ở máy chủ: `FileService.convert_to_pdf` gọi `subprocess.run`
> đồng bộ, chẹn event loop tới 60s mỗi file — không an toàn khi nhiều học viên
> nộp cùng lúc. File `.doc` nhị phân cũ thì không thư viện JS nào đọc được, giữ
> nguyên nút tải về.

### Mốc trước — `dba30f9`

Nội dung: **hai việc trong một lần phát hành.**

**1. HKG — bảng điểm danh chi tiết từng thành phần.** Tab Điểm danh trước chỉ có
6 ô số tổng hợp: ban tổ chức biết BAO NHIÊU người có mặt mà không biết là AI.
Nay 6 ô đó thành nút lọc cho một bảng liệt kê từng người — họ tên, mã công chức,
đơn vị, chức vụ, loại tham dự, trạng thái, giờ, hình thức, người chấm, lý do
vắng. Người **chưa** điểm danh vẫn có tên trong bảng. Chủ tọa/thư ký chấm tay
ngay trên từng dòng (endpoint `bam-tay` có từ đầu nhưng chưa có giao diện — nợ
ghi trong `HUONG_DAN_SU_DUNG_HKG.md` §18/§25, nay gỡ được). Thêm nút xuất Excel
làm bảng điểm danh lưu hồ sơ, có ghi nhật ký `EXPORT_DIEM_DANH`.

Hai endpoint mới, đều chỉ-đọc và chỉ ban tổ chức gọi được:
`GET /cuoc-hop/{id}/diem-danh/chi-tiet` và `.../diem-danh/xuat-excel`.

Kèm ba bản vá phát hiện khi làm: chấm tay không còn xoá mất ghi chú cũ khi gửi
payload không có `ghi_chu`; nhật ký `CHECKIN_MANUAL` ghi rõ từng người (trước
chỉ ghi tổng số, mà bảng `diem_danh` không có `updated_at` nên mất dấu vĩnh
viễn); hằng `HINH_THUC_VALUES` bổ sung `TU_DIEM_DANH` — giá trị chiếm 100% dữ
liệu thật nhưng trước đó khai thiếu cả ở máy chủ lẫn giao diện.

**2. KPI — sửa ngày hiệu lực điều chuyển** (`699cbc1` + `0cd7daa`): `ngay_hieu_luc`
trả về đúng ngày quyết định thay vì ngày nhập liệu, mốc chốt về cuối tháng M, và
bắt buộc nhập ngày hiệu lực khi điều chuyển thay vì điền sẵn ngày hôm nay.

> Ghi chú quy trình: nhánh HKG được tạo TỪ `feature/kpi-sua-ngay-dieu-chuyen`
> nên chứa sẵn 2 commit KPI. Đã báo và người dùng chọn phát hành cả hai cùng
> lượt, nên truyền một SHA `dba30f9` là đủ. Đã đối chứng
> `git log dba30f9..origin/prod` RỖNG trước khi chạy `trien_khai.sh`.
>
> Nhánh `feature/lms-reset-luot-thi` (1 commit, **có migration**) cố ý để lại
> cho đợt sau.
>
> Sửa luôn một lỗi của chính sổ này: mục "Hiện tại" trước đây ghi commit
> `81bb5b5` nhưng phần Nội dung lại tả tính năng Lịch công tác tuần/ngày của
> `97264ae` — hai phần lệch nhau, đúng loại lỗi mà ghi chú 25/08 bên dưới đã
> cảnh báo. Nội dung của `81bb5b5` nay nằm đúng ở hàng của nó trong bảng lịch sử.

### Mốc trước nữa — `2137a32`

Nội dung: **Chặn build/triển khai khi đang có người thi**. Sinh ra từ sự cố cùng
ngày 10:04–10:17: `npm run build` chạy trần đúng lúc 13 thí sinh đang ở phút thứ
30 của bài ĐGNL 45 phút, RAM 7,8GB cạn sạch trên máy **không có swap**, cả máy
đóng băng 12 phút — SSH không vào được, nginx gần như câm, OOM-killer bắn chết
next-server. Thêm `kiem_tra_ky_thi.sh` (chốt chặn) và `build_frontend.sh` (dùng
thay `npm run build`, nhốt build trong cgroup có trần RAM **và** trần swap).
`trien_khai.sh` gọi chốt trước cả `git checkout`.

Kèm theo, đã áp thẳng lên máy và **không nằm trong git**: swapfile 8GB +
`/etc/fstab`, và `/etc/sysctl.d/99-kpi-oom.conf` (`vm.swappiness=10`,
`vm.min_free_kbytes=131072`, `vm.watermark_scale_factor=100`).

### Mốc cũ hơn — `cc254be`

**Quy trình khôi phục file từ ảnh uploads**, kèm cảnh báo `/opt/kpi/scripts` nằm
ngoài `trien_khai.sh`. Trước đó là `e005660` (sửa mặc định uploads sai trong sao
lưu) và `b6f805c` (lịch sử phiên bản cho uploads bằng ảnh hardlink).

### Mốc cũ nhất — `8653f0e`

**ĐGNL — thư viện mẫu cấu trúc đề**. Tab "Mẫu cấu trúc đề" cho sửa
mẫu trực tiếp trên lưới (trước chỉ tạo được bằng cách lưu từ kỳ thi, không sửa
được), nhân bản, chặn trùng tên. Sửa cấu trúc đề của kỳ thi nay nạp sẵn dữ liệu
cũ vào form — trước đó sửa một lĩnh vực là xóa mất các lĩnh vực còn lại. Áp
dụng mẫu gộp về một transaction thay vì N request tuần tự. Nới khóa trạng thái:
cho sửa ở NHÁP/CHỜ DUYỆT, khi ĐANG MỞ chỉ chặn vị trí đã có thí sinh làm bài.
Hiện tồn kho ngân hàng câu hỏi ngay cạnh ô nhập số câu.

## Lịch sử triển khai

| Ngày | Commit | Ghi chú |
|---|---|---|
| 18/08/2026 | `19bea09` | Mốc đầu tiên khi tách môi trường |
| 19/08/2026 | `be0670b` | Lịch công tác G4 + migration `meeting_016`→`022` + di trú dữ liệu |
| 25/08/2026 | `8653f0e` | ĐGNL: thư viện mẫu cấu trúc đề, sửa cấu trúc trực tiếp, áp mẫu nguyên tử — không migration |
| 25/08/2026 | `40de07e` | LMS: sửa `POST /cau-hoi` trả 500 khi thêm câu vào bài kiểm tra đã có — không migration |
| 25/08/2026 | `cc254be` | Sao lưu: lịch sử phiên bản uploads bằng ảnh hardlink + quy trình khôi phục — không migration |
| 25/08/2026 | `2137a32` | Vận hành: chặn build/triển khai khi đang có người thi (sau sự cố OOM 10:04–10:17) — không migration |
| 25/08/2026 | `902e711` | Công cụ: `trien_khai.sh` tự gắn nhánh `prod` — chỉ script + tài liệu, không chạm code dịch vụ, không restart |
| 25/08/2026 | `e005660` | Backup: lịch sử phiên bản uploads (ảnh hardlink, giữ 60 bản) + sửa mặc định đường dẫn uploads đã chết. Cần cài tay vào `/opt/kpi/scripts/` — xem `scripts/INSTALL_CRON.md` |
| 25/08/2026 | `97264ae` | Lịch công tác: xem theo tuần và theo ngày, một ngày hiện chi tiết đầy đủ mọi cuộc họp — thuần frontend, không migration |
| 28/08/2026 | `81bb5b5` | ĐGNL: câu hỏi ôn tập hằng ngày qua chatbot Zalo — 2 endpoint công khai `/api/v1/lms/dgnl/cong-khai/*` (khoá `ZALO_BOT_API_KEY`), migration `lms_cau_hoi_hang_ngay_20260827` thêm bảng mới. Kèm script gắn nhãn công chức trên OA và báo cáo người chưa quan tâm OA |
| 28/08/2026 | `c53d843` | Ghi mốc prod `81bb5b5` vào sổ — chỉ tài liệu, không chạm code |
| 04/09/2026 | `dba30f9` | HKG: bảng điểm danh chi tiết từng thành phần + chấm tay + xuất Excel (2 endpoint chỉ-đọc mới, audit `EXPORT_DIEM_DANH`); kèm KPI: sửa ngày hiệu lực điều chuyển (`699cbc1`+`0cd7daa`) — **không migration** |
| 05/09/2026 | *(không phát hành code)* | **Di trú DỮ LIỆU** `lich_su_dieu_chuyen` theo QĐ điều động 2026: xóa 8 · sửa 77 · thêm 62 (`scripts/fix_ngay_dieu_chuyen_2026.py`). Kèm mở lại tiêu chí chung T7 cho `20ZZ-0529` (`scripts/mo_lai_tieu_chi_chung.py`). Chi tiết ở mục dưới |
| 08/09/2026 | `d15b850` | LMS: bài tập thực hành nhận file PDF/Word (endpoint `nop-bai-thuc-hanh`, `/nop-video` thành bí danh; đối chiếu chữ ký file chống đổi đuôi; giao diện chọn định dạng + xem theo loại file). Kèm `85cbedf` (script `mo_lai_tieu_chi_chung.py`, trơ lúc chạy) và `a828e89` (tài liệu) — **không migration** |
| 10/09/2026 | *(không phát hành code)* | **Sửa DỮ LIỆU**: reset lượt thi ĐGNL cho `20ZZ-0005` kỳ ĐGNL-THANG 8 - TA bằng SQL (xoá 2 lượt 6đ + 74đ, về `CHUA_THI`; xoá 3 vi phạm + 1 phiên thi). Snapshot và nhật ký ở `docs/fix-reset-luot-thi/` |
| 10/09/2026 | `13647f8` | ĐGNL: công cụ reset lượt thi cho quản trị đào tạo — 2 endpoint chỉ-admin, nút Reset + Nhật ký trên trang thống kê kỳ thi, migration `lms_reset_luot_thi_20260831` thêm bảng `lms.lich_su_reset_thi`. Rebase `6c7270d` lên `prod` trước khi phát hành (SHA gốc đã tụt sau prod 9 commit) |
| 10/09/2026 | `2bd8508` | ĐGNL: bộ lọc danh sách thí sinh trên trang thống kê kỳ thi — thuần frontend, không migration. **Phát hành nhưng khi đó chưa ghi sổ** |
| 13/09/2026 | `4aaa43e` | KPI: điều chuyển nhân sự hàng loạt theo QĐ bằng Excel — 3 endpoint (`mau-excel`/`xem-truoc`/`ghi`), mẫu 4 sheet, trang `/admin/dieu-chuyen-hang-loat`; tách `app/core/dieu_chuyen.py` dùng chung với điều chuyển lẻ — **không migration** |
| 18/09/2026 | `41058a3` | KPI: chấm tiêu chí chung theo QUÝ từ Q3/2026 theo CV 21169 — phiếu quý neo ở tháng cuối quý (`la_phieu_tc_quy`), 8 điểm đọc chuyển sang tháng neo, chặn lập mới báo cáo/phiếu THÁNG, ẩn kỳ tháng khỏi giao diện. **Migration `kpi_tc_theo_quy_20260918`** (chỉ thêm cột, không đụng dữ liệu) |

> Ghi chú 25/08/2026: mục "Hiện tại" từng ghi `e005660` trong khi cây prod thực
> tế đã ở `cc254be` — sổ tụt sau thực tế 2 commit. Đã đối chiếu lại bằng
> `git -C /opt/kpi-prod rev-parse HEAD` và bổ sung các mốc còn thiếu. Kiểm tra
> nhanh bất cứ lúc nào: `git -C /opt/kpi-prod rev-parse --short HEAD`.
>
> Chú thích này trước nằm CHEN GIỮA bảng, cắt bảng làm đôi nên hai dòng
> `902e711` và `e005660` hiện ra thành văn bản thường, không phải hàng bảng.
> Đã chuyển xuống dưới bảng.

## Di trú dữ liệu 05/09/2026 — ngày hiệu lực điều chuyển

Không phát hành code (code đã ra cùng `dba30f9` ngày 04/09). Đây là **sửa nội
dung dữ liệu**, chạy tay có user duyệt từng bước — cố tình KHÔNG đóng thành
Alembic migration để không ai bị nó tự chạy lúc khởi động app mà không xem trước.

**Sao lưu trước khi ghi:** `/var/backup/truoc_ap_prod_20260905_0021.sql` (12 MB,
gồm `lich_su_dieu_chuyen`, `cong_chuc`, `danh_gia_thang`, `tieu_chi_chung_danh_gia`).

**Bước 1 — `scripts/fix_ngay_dieu_chuyen_2026.py --apply`**

| | |
|---|---|
| Xóa | 8 bản ghi (4 người × 2 dòng — vết "nhập → hoàn tác → nhập lại") |
| Sửa | 77 bản ghi: `ngay_hieu_luc` về ngày QĐ, `ly_do` → `"Đợt điều động <ngày>"` (chỉ khi đang rỗng/mặc định) |
| Thêm | 62 bản ghi đợt 04/02/2026 |
| Tổng | `lich_su_dieu_chuyen` 111 → **165** (151 DIEU_CHUYEN + 14 trạng thái) |

Đối chứng sau khi ghi: phân bố `2026-02-04 = 62 · 2026-05-15 = 75 · 2026-06-03 = 2
· 2026-07-03 = 3`; 0 công chức lệch giữa đơn vị hiện tại và đơn vị đến của QĐ mới
nhất. Còn đúng 1 bộ trùng cùng chiều — `20ZZ-0187` Nguyễn Đình Hiến, 2 dòng
HQCK-MC→HQCK-MC (đổi chức vụ trong cùng đơn vị, không nằm trong QĐ) — **cố ý
không đụng**.

**Bước 2 — `scripts/mo_lai_tieu_chi_chung.py --ma-cc 20ZZ-0529 --thang 7 --nam 2026 --apply`**

QĐ 03/7/2026 chuyển người này HQCK-MC → KSHQ nhưng chỉ được nhập 25/08, khi T7
đã `DA_PHE_DUYET` bởi PĐT đơn vị cũ. Đã trả T7 về `NHAP`, bỏ khóa, xóa dấu vết
phê duyệt của đơn vị cũ, dời `don_vi_id_snapshot` sang KSHQ; 10 dòng tiêu chí về
`NHAP` và giữ 20.00 điểm tự chấm. Các tháng 1, 4, 5, 6, 8 **không bị đụng**.

**Đối chứng cuối, bằng chính biểu thức `_don_vi_tai_thang_expr` của báo cáo**
(`scripts/doi_chung_don_vi_tai_thang.py`), so với ảnh chụp hiện trạng 31/08 trên
558 công chức × T1–T8/2026 — đổi **đúng 2 ca dự kiến, không có ca thứ ba**:

| Tháng | Mã CC | Trước | Sau | Vì sao đúng |
|---|---|---|---|---|
| T1 | `20ZZ-0303` | HQCK-MC | PTSTQ | QĐ 04/02 mới chuyển PTSTQ→MC; kê khai T1 cũng ghi PTSTQ |
| T7 | `20ZZ-0529` | HQCK-MC | KSHQ | QĐ 03/7 đã chuyển sang KSHQ |

**Còn phải làm tay trên giao diện** (không làm bằng SQL):
1. `20ZZ-0529` tự đánh giá tiêu chí chung T7 → gửi phê duyệt
2. Lãnh đạo KSHQ duyệt cấp 1 rồi cấp 2
3. Cả HQCK-MC và KSHQ bấm "cập nhật chi tiết từ dữ liệu" cho báo cáo xếp loại T7
   — hiện còn một dòng `chi_tiet_xep_loai` T7 xếp người này vào báo cáo HQCK-MC
   (trạng thái `NHAP`, tạo 28/08)

**Còn nợ:** `ly_do` của 139 bản ghi mới/vừa sửa đang là `"Đợt điều động <ngày>"`
— chưa có số quyết định. TCCB bổ sung sau qua `/admin/lich-su-dieu-chuyen`.

## Quy ước giữ nhánh khớp code đang chạy

Cây production là git worktree tại `/opt/kpi-prod`, **bám nhánh `prod`** — không
để ở trạng thái `detached HEAD`. Triển khai đúng cách:

```bash
cd /opt/kpi-prod
git fetch origin
git merge --ff-only <commit>      # hoặc: git branch -f prod <commit> && git checkout prod
git push origin prod
```

Sau đó đồng bộ `main` theo `prod` (chỉ fast-forward, không tạo commit trên `main`):

```bash
cd /root/kpi-haiquan && git branch -f main prod && git push origin main
```

Ngày 25/08/2026 đã xảy ra lệch: cây prod chạy `40de07e` ở `detached HEAD` trong
khi nhánh `prod` còn ở `73c994f`. Hậu quả nếu không phát hiện: lần
`git checkout prod` kế tiếp sẽ âm thầm quay lui, mất bản vá đang phục vụ người
dùng. Kiểm tra nhanh bất cứ lúc nào:

```bash
cd /opt/kpi-prod && git status -sb | head -1   # phải là "## prod...origin/prod", không có "HEAD (no branch)"
```
