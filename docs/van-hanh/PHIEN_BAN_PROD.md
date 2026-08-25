# Mốc phiên bản production

Ghi lại commit đang phục vụ người dùng, để luôn có điểm quay lui xác định.
Cập nhật mỗi lần triển khai.

## Hiện tại

| | |
|---|---|
| **Commit** | `2137a32` |
| **Ngắn** | `2137a32` |
| **Nhánh nguồn** | `prod` (fast-forward từ `feature/van-hanh-chan-build-khi-thi`) |
| **Ngày ghi mốc** | 25/08/2026 11:23 |
| **Alembic** | `mt_025_loai_tai_lieu_20260822` (không đổi — đợt này không có migration) |

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

### Mốc trước — `cc254be`

**Quy trình khôi phục file từ ảnh uploads**, kèm cảnh báo `/opt/kpi/scripts` nằm
ngoài `trien_khai.sh`. Trước đó là `e005660` (sửa mặc định uploads sai trong sao
lưu) và `b6f805c` (lịch sử phiên bản cho uploads bằng ảnh hardlink).

### Mốc trước nữa — `8653f0e`

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

> Ghi chú 25/08/2026: mục "Hiện tại" từng ghi `e005660` trong khi cây prod thực
> tế đã ở `cc254be` — sổ tụt sau thực tế 2 commit. Đã đối chiếu lại bằng
> `git -C /opt/kpi-prod rev-parse HEAD` và bổ sung các mốc còn thiếu. Kiểm tra
> nhanh bất cứ lúc nào: `git -C /opt/kpi-prod rev-parse --short HEAD`.
| 25/08/2026 | `902e711` | Công cụ: `trien_khai.sh` tự gắn nhánh `prod` — chỉ script + tài liệu, không chạm code dịch vụ, không restart |
| 25/08/2026 | `e005660` | Backup: lịch sử phiên bản uploads (ảnh hardlink, giữ 60 bản) + sửa mặc định đường dẫn uploads đã chết. Cần cài tay vào `/opt/kpi/scripts/` — xem `scripts/INSTALL_CRON.md` |

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
