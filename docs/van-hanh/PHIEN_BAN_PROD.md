# Mốc phiên bản production

Ghi lại commit đang phục vụ người dùng, để luôn có điểm quay lui xác định.
Cập nhật mỗi lần triển khai.

## Hiện tại

| | |
|---|---|
| **Commit** | `dba30f9` |
| **Ngắn** | `dba30f9` |
| **Nhánh nguồn** | `feature/hkg-diem-danh-chi-tiet` (fast-forward, chứa cả `feature/kpi-sua-ngay-dieu-chuyen`) |
| **Ngày ghi mốc** | 04/09/2026 22:45 |
| **Alembic** | `lms_cau_hoi_hang_ngay_20260827` — **KHÔNG migration mới** |

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

### Mốc trước — `2137a32`

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

### Mốc trước nữa — `cc254be`

**Quy trình khôi phục file từ ảnh uploads**, kèm cảnh báo `/opt/kpi/scripts` nằm
ngoài `trien_khai.sh`. Trước đó là `e005660` (sửa mặc định uploads sai trong sao
lưu) và `b6f805c` (lịch sử phiên bản cho uploads bằng ảnh hardlink).

### Mốc cũ hơn — `8653f0e`

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

> Ghi chú 25/08/2026: mục "Hiện tại" từng ghi `e005660` trong khi cây prod thực
> tế đã ở `cc254be` — sổ tụt sau thực tế 2 commit. Đã đối chiếu lại bằng
> `git -C /opt/kpi-prod rev-parse HEAD` và bổ sung các mốc còn thiếu. Kiểm tra
> nhanh bất cứ lúc nào: `git -C /opt/kpi-prod rev-parse --short HEAD`.
>
> Chú thích này trước nằm CHEN GIỮA bảng, cắt bảng làm đôi nên hai dòng
> `902e711` và `e005660` hiện ra thành văn bản thường, không phải hàng bảng.
> Đã chuyển xuống dưới bảng.

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
