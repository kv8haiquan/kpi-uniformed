# Hỏi – Đáp bổ sung đợt 2 phục vụ rà quét ATTT (CV 153/CNTT)

> Trả lời 6 yêu cầu bổ sung hồ sơ của đoàn kiểm tra. Lập ngày 06/10/2026, số liệu xác minh trực tiếp trên máy chủ production và mã nguồn đang chạy (nhánh `prod`, commit `9534f17`) tại thời điểm lập.
> Đợt 1: `10_HOI_DAP_BO_SUNG.md` (05/08/2026). Mục 7 dưới đây **đính chính** các điểm của hồ sơ đợt 1 đã thay đổi hoặc chưa chính xác.

---

## 1. Tài liệu phân tích yêu cầu người sử dụng

**Tài liệu:** `11_phan_tich_yeu_cau_nguoi_dung.md`

- Dự án **không lập tài liệu yêu cầu người dùng (URD) theo mẫu ngay từ đầu**: hệ thống được phát triển theo hình thức làm dần từng phần, mỗi đợt dựa trên văn bản chỉ đạo và góp ý nghiệp vụ. Tài liệu này được **lập hồi cố** từ các nguồn có thật: văn bản chỉ đạo (CV 21169/CHQ-TCCB ngày 28/8/2026), tờ trình nền tảng Digital Learning, góp ý của Văn phòng và các phòng, lịch sử phát triển trên Git. Phần mở đầu tài liệu nói rõ phương pháp lập.
- Nội dung chính:
  - Nhóm người dùng và số lượng thật: 544 tài khoản đang hoạt động, gồm CC 383, HĐ 111 106, PDV 37, TDV 13, PCCT 3, CCT 1, quản trị 1.
  - Yêu cầu chức năng theo phân hệ: mỗi yêu cầu có mã, mức ưu tiên, trạng thái đáp ứng, trang giao diện và endpoint thật.
  - Yêu cầu phi chức năng: ATTT, hiệu năng, sẵn sàng, pháp lý.
  - Ma trận truy vết từ yêu cầu tới phân hệ và tài liệu.
  - Danh sách yêu cầu chưa đáp ứng.
- **Cần TCCB bổ sung:** bản đã ký của tờ trình chủ trương (bản trong kho mã nguồn là dự thảo, chưa có số và ngày). Đây cũng là mục 1 của CV 153.

## 2. Quy trình giám sát vận hành hệ thống

**Tài liệu:** `12_quy_trinh_giam_sat_van_hanh.md`

- Căn cứ: Quy chế ATTT mạng kèm QĐ 1804/QĐ-TCHQ và Quy trình quản lý vận hành an toàn hệ thống thông tin kèm QĐ 330/QĐ-HQKV8.
- Đối tượng giám sát:
  - Hạ tầng: CPU, RAM, swap, đĩa.
  - 10 tiến trình ứng dụng chạy bằng PM2, cùng nginx và PostgreSQL.
  - Điểm kiểm tra sức khỏe (health check) của 8 backend.
  - Chứng chỉ SSL, sao lưu, nhật ký an ninh đăng nhập.
  - Các kỳ thi ĐGNL và tiến trình gửi tin Zalo OA.
- Tài liệu có ma trận "chỉ số – lệnh kiểm tra – tần suất – ngưỡng – người chịu trách nhiệm – hành động", checklist ngày/tuần/tháng, quy trình phân cấp và leo thang sự cố, cùng mẫu sổ nhật ký vận hành.
- Hiện trạng đo ngày 06/10/2026:

| Hạng mục | Kết quả |
|---|---|
| Health check | 8/8 backend trả 200, frontend trả 200 |
| Đĩa | Dùng 71% |
| RAM | Dùng ~65% |
| CSDL | 218 MB |
| Sao lưu | Bản gần nhất 14:00 cùng ngày, đã đẩy off-site lúc 14:30 |
| SSL | Hết hạn 21/11/2026, bộ tự gia hạn đang chạy |

- **Khoảng trống:**
  - **Chưa có cảnh báo tự động**: giám sát hiện làm thủ công theo checklist.
  - Bản sao lưu cục bộ nằm cùng ổ đĩa với dữ liệu gốc.
  - Thư mục tệp tải lên (uploads) chưa có bản off-site.
  - Môi trường phát triển (dev) và production chạy chung một máy chủ.

  Lộ trình khắc phục nêu tại mục 8 của tài liệu.

## 3. Hướng dẫn sử dụng theo từng nhóm người dùng

**Thư mục:** `13_huong_dan_su_dung/` (9 file):

| File | Nhóm người dùng |
|---|---|
| `README.md` | Mục lục + ma trận vai trò × chức năng |
| `01_cong_chuc.md` | Công chức, HĐ 111 |
| `02_lanh_dao_don_vi.md` | Trưởng / Phó đơn vị |
| `03_lanh_dao_chi_cuc.md` | Chi cục trưởng / Phó Chi cục trưởng |
| `04_tccb.md` | Tổ chức cán bộ |
| `05_quan_tri_he_thong.md` | Quản trị hệ thống |
| `06_hoc_vien_giang_vien_lms.md` | Học viên, giảng viên, quản trị đào tạo, kỳ thi ĐGNL |
| `07_hop_khong_giay_lich_cong_tac.md` | Họp không giấy, lịch công tác |
| `08_dien_dan_phap_luat_tin_tuc.md` | Diễn đàn, pháp luật, tin tức/tài liệu, chỉ tiêu đơn vị |

- Chỉ mô tả các tính năng **đang chạy trên production**. Tên menu, nút, tab và đường dẫn được đối chiếu với mã nguồn giao diện bản production ngày 06/10/2026.
- Phần đăng nhập ghi đúng hiện trạng bảo mật: khóa tạm 15 phút sau 10 lần sai liên tiếp, phiên đăng nhập 8 giờ, khuyến cáo đổi mật khẩu mặc định.
- Chưa có ảnh chụp màn hình. Sẽ bổ sung khi in bản giấy.

## 4. Bộ tài liệu cài đặt, cấu hình, quản trị và vận hành hệ thống/CSDL

**Thư mục:** `14_cai_dat_quan_tri_van_hanh/`:

| File | Nội dung |
|---|---|
| `01_cai_dat_moi_truong.md` | Yêu cầu phần cứng/OS, cài gói, tạo CSDL/schema, migration, build, **kịch bản dựng lại toàn bộ trên máy mới (DR)** |
| `02_cau_hinh.md` | Biến môi trường (chỉ tên biến, không có giá trị bí mật), nginx, PM2, cron, logrotate, tường lửa, múi giờ |
| `03_quan_tri_he_thong.md` | Tài khoản và phân quyền, phát hành phiên bản theo SHA, quay lui phiên bản |
| `04_quan_tri_csdl.md` | Schema/owner, tài khoản CSDL, migration, sao lưu – phục hồi, CSDL kiểm thử, bảo trì, quy tắc ghi dữ liệu an toàn trên production |
| `05_van_hanh_hang_ngay.md` | Khởi động/dừng, xem log, bảo trì định kỳ, vận hành trong kỳ thi |

- Mọi thao tác quản trị đều ưu tiên làm qua giao diện. SQL ghi trực tiếp chỉ là phương án khẩn cấp, bắt buộc chạy trong `BEGIN … kiểm tra … COMMIT` và thử trước trên CSDL kiểm thử.
- Bổ sung so với hồ sơ đợt 1: tài liệu cũ `docs/van-hanh/HUONG_DAN_DEV_PROD.md` còn ghi `trien_khai.sh main` (**sai**, script phải nhận SHA commit). Tài liệu mới đã ghi đúng.

## 5. Tài liệu phân tích, thiết kế kỹ thuật chi tiết được dẫn chiếu trong hồ sơ

**Tài liệu:** `15_danh_muc_tai_lieu_thiet_ke.md` — danh mục khoảng 65 tài liệu, mỗi tài liệu ghi: đường dẫn, hồ sơ nào dẫn chiếu tới, ngày cập nhật, có trong nhánh production hay không, mức khớp với mã nguồn.

- **Có sẵn và nộp được:**
  - Đặc tả API và thiết kế CSDL của từng module mới: LMS, HKG, Forum, Legal, Portal, Chỉ tiêu.
  - Bộ đặc tả dùng chung `SHARED_*`: xác thực, CSDL tham chiếu, chuẩn lập trình.
  - Hợp đồng API giữa các module.
  - Quy tắc nghiệp vụ PL3, phân tích tác động công thức KPI V2.
  - OpenAPI JSON của cả 8 service (`api-specs/`). Đây là nguồn chính thức, sinh tự động từ mã nguồn.
  - Từ điển dữ liệu (`06_phu_luc_tu_dien_du_lieu.md`).
- **Khoảng trống:**
  - **Module KPI lõi chưa có tài liệu thiết kế chi tiết (SDD) riêng.** Thông tin thiết kế đang nằm ở các mục 03 (công thức), 06 (từ điển dữ liệu), 08 (API), OpenAPI JSON và `BUSINESS_RULES_v3_0_PL3.md`.
  - Chưa có sơ đồ tuần tự (sequence diagram).
  - Chưa có tài liệu thiết kế bảo mật tập trung.
  - Đặc tả API của các module mới ít hơn số endpoint thực tế 10–50%. Số endpoint thực tế lấy theo OpenAPI JSON.
- **Không có dẫn chiếu gãy** trong bộ hồ sơ 02–10. Có một chỗ ghi sai thư mục: `MIGRATION_GUIDE_20260227.md` nằm ở thư mục gốc kho mã nguồn, không phải `backend/`.
- **Không nộp nguyên trạng** 22 báo cáo đối chiếu tại `docs/Fix-Bao-Cao/` vì chứa họ tên, mã công chức thật. Chỉ nộp bản tóm tắt hoặc bản đã ẩn danh.

## 6. Tổng hợp lỗi thường gặp và hướng dẫn khắc phục

**Tài liệu:** `16_loi_thuong_gap_khac_phuc.md`:

| Phần | Nội dung |
|---|---|
| A | Lỗi phía người dùng: đăng nhập, kê khai, phê duyệt, thi ĐGNL, họp, tải tệp, trình duyệt |
| B | Lỗi nghiệp vụ/dữ liệu cần quản trị xử lý: đơn kẹt trạng thái, điểm lệch, chuyển đơn vị, trùng tên khi nhập Excel, reset lượt thi |
| C | Lỗi hệ thống/hạ tầng: dịch vụ ngừng, hết bộ nhớ, đầy đĩa, lỗi migration, SSL, WebSocket, sao lưu, lệch múi giờ, Zalo |
| D | Bảng tra mã lỗi nghiệp vụ và mã HTTP (mã lỗi đối chiếu với mã nguồn) |
| Phụ lục | Thống kê sự cố đã xảy ra từ 02/2026 đến 09/2026: ngày, nguyên nhân gốc, cách khắc phục, commit |

- Thống kê theo nhật ký 7 ngày gần nhất (đến 06/10/2026): **không có lỗi nghiêm trọng nào đang diễn ra**, `nginx error.log` trống.

---

## 7. Đính chính và cập nhật so với hồ sơ đợt 1

| # | Hồ sơ đợt 1 ghi | Hiện trạng đúng (06/10/2026) |
|---|---|---|
| 1 | `10_…` mục 4.2: "Ra Internet chỉ có duy nhất GitHub" | Từ **tháng 08/2026** có thêm tiến trình `zalo-worker` gọi **API Zalo OA**: gửi tin nhắc lịch công tác 24 giờ, 1 giờ và 30 phút trước giờ họp, và câu hỏi ĐGNL hằng ngày. Trần chi tiêu 500.000 đ/ngày, 2.000.000 đ/tháng. Kết nối ra ngoài hiện gồm: GitHub (sao lưu) + Zalo OA. |
| 2 | `10_…` mục 1.2: cổng 3000, 8000–8007 "chỉ localhost" | **Chưa chính xác.** 6 backend (8000–8005) và frontend (3000) đang lắng nghe trên mọi giao diện mạng; chỉ 8006, 8007 và PostgreSQL 5432 bind `127.0.0.1`. Kiểm tra qua IP công khai cho thấy các cổng này **bị chặn** (tường lửa phía nhà cung cấp), chỉ 80/443 truy cập được. Tuy vậy tường lửa trên máy chủ (`ufw`) đang **tắt**, nên hiện chỉ còn một lớp bảo vệ. **Kế hoạch khắc phục:** chuyển các tiến trình về `127.0.0.1` và bật `ufw` chỉ mở 22/80/443 (`14_…/02_cau_hinh.md` mục 3.1 và 6). |
| 3 | Mục 06 và phụ lục từ điển dữ liệu: 96 bảng | Hiện có **111 bảng**: public 37, meeting 23, lms 22, common 8, legal 6, chi_tieu 5, forum 5, portal 5. 15 bảng tăng thêm: meeting +10 (Lịch công tác: trực ban, ghi chú và chia sẻ, đánh giá cuộc họp, danh mục, lãnh đạo liên quan, bảng phục vụ di trú dữ liệu…), common +3, lms +2. **Phụ lục từ điển dữ liệu 06 chưa mô tả 15 bảng này — sẽ sinh lại phụ lục trước khi bàn giao.** |
| 4 | Mục 09: 181 commit | Nhánh production hiện có **316 commit** (154 feat, 75 fix) tính từ 09/02/2026. |
| 5 | `10_…` mục 5.2: "HDSD theo vai trò đang biên soạn" | **Đã lập**: `13_huong_dan_su_dung/`. |
| 6 | (Chưa nêu) | **Bí mật ký JWT (SECRET_KEY) và mật khẩu CSDL chưa đổi định kỳ.** Đợt vá 31/07/2026 mới đổi `INTERNAL_API_KEY`. Mật khẩu CSDL cũ còn nằm trong lịch sử Git (gói bàn giao dùng `git archive` nên không mang theo lịch sử). Đã đưa vào kế hoạch khắc phục. |
| 7 | (Chưa nêu) | **Chưa có màn hình gán vai trò nền tảng** (giảng viên, quản trị đào tạo, biên tập…). Hiện gán bằng SQL do quản trị hệ thống thực hiện, trừ vai trò theo dõi chỉ tiêu đã có chức năng riêng trong module Chỉ tiêu. Đề xuất bổ sung màn hình gán vai trò có ghi nhật ký. |
| 8 | (Chưa nêu) | Vai trò `TCCB` hiện **chưa gán cho tài khoản nào**. Quyền xem toàn Chi cục của cán bộ TCCB đang cấp qua cờ `can_view_all_units` (1 tài khoản). |

## 8. Các việc còn tồn đọng (tổng hợp)

| Việc | Mức | Ghi chú |
|---|---|---|
| Bắt buộc đổi mật khẩu mặc định ở lần đăng nhập đầu + chuẩn mật khẩu ≥ 8 ký tự, đủ 4 nhóm ký tự | Cao | Đã nêu ở đợt 1, chưa triển khai |
| Bind `127.0.0.1` cho 7 tiến trình + bật `ufw` | Cao | Mục 7.2 |
| Đổi mật khẩu CSDL + SECRET_KEY | Trung bình | Đổi SECRET_KEY sẽ buộc mọi người đăng nhập lại |
| Sao lưu uploads ra ngoài máy chủ; tách bản sao lưu sang ổ đĩa/máy khác | Cao | `12_…` mục 8 |
| Cảnh báo tự động khi dịch vụ, sao lưu hoặc chứng chỉ lỗi | Trung bình | `12_…` mục 8 |
| Nhật ký audit tập trung + nhật ký đăng nhập thành công | Trung bình | Đã nêu ở đợt 1 |
| Màn hình gán vai trò nền tảng | Thấp | Mục 7.7 |
| Hồ sơ chủ trương (mục 1) và đầu mối kỹ thuật (mục 10) | — | Phòng TCCB |
