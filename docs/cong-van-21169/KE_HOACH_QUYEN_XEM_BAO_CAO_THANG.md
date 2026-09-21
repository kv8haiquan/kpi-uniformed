# Kế hoạch: báo cáo xếp loại THÁNG chuyển sang chế độ CHỈ XEM

> Tiếp theo đợt P0 (`41058a3`, live 18/09/2026). Ngày lập: 21/09/2026 · **DỰ THẢO, chờ duyệt**
>
> Yêu cầu của người dùng: *"hiển thị quyền xem chứ không chỉnh sửa đối với đánh giá xếp loại tháng"*.

---

## 1. Hiện trạng sau đợt 18/09 — và một lỗ hổng

Đợt P0 xử lý kỳ tháng theo hướng **ẩn**: bỏ tab "Duyệt đánh giá tháng" khỏi `/xep-loai`
khi kỳ đang chọn từ Q3/2026 trở đi, và chặn **lập mới** báo cáo/phiếu tháng ở backend.

Hai vấn đề:

**(a) Mất đường tra cứu.** Báo cáo tháng đã có vẫn nằm trong CSDL nhưng không còn cửa
nào mở ra xem:

| Tháng 2026 | Số báo cáo | Số dòng chi tiết | Trạng thái |
|---|---|---|---|
| 7 | 13 | 540 | 10 NHAP · 3 CHO_PHE_DUYET |
| 8 | 12 | 466 | 11 NHAP · 1 CHO_PHE_DUYET |
| 9 | 8 | 404 | 8 NHAP |

**(b) Lỗ hổng: năm endpoint GHI vẫn mở.** Việc ẩn chỉ nằm ở giao diện. Backend chưa
chặn thao tác ghi trên báo cáo tháng của kỳ đã chuyển sang quý:

| Endpoint | Việc | Ai gọi được |
|---|---|---|
| `PUT /chi-tiet/{id}/de-xuat` | Trưởng ĐV đổi xếp loại đề xuất | Trưởng ĐV |
| `POST /{id}/gui-duyet` | Gửi báo cáo tháng lên CCT | Trưởng ĐV |
| `PUT /chi-tiet/{id}/quyet-dinh` | CCT quyết định xếp loại | CCT |
| `POST /{id}/phe-duyet` | CCT duyệt báo cáo tháng | CCT |
| `POST /{id}/tra-lai` | CCT trả lại báo cáo | CCT |

Ai còn giữ link cũ `/xep-loai?tab=bao-cao`, hoặc gọi thẳng API, vẫn sửa và **phê duyệt
được báo cáo tháng 7, 8, 9/2026** — trái với công văn (kỳ tháng hết hiệu lực) và nguy
hiểm hơn: `phe_duyet_bao_cao` sẽ đặt `is_khoa = true` cho các bản ghi đánh giá của
tháng đó, khoá luôn phiếu tiêu chí quý nếu rơi vào tháng neo (T9).

→ Chuyển sang **chỉ xem** vừa trả lại đường tra cứu, vừa bịt lỗ hổng này.

---

## 2. Nguyên tắc

- Chế độ chỉ-xem **chặn ở backend**, không chỉ ẩn nút. Giao diện chỉ phản ánh điều đó.
- Áp cho kỳ **từ Q3/2026** (đúng mốc `TC_THEO_QUY_TU` đã có). Kỳ đến hết Q2/2026 giữ
  nguyên toàn bộ quyền sửa để các đơn vị hoàn tất hồ sơ còn dở.
- Không xoá, không sửa một dòng dữ liệu nào đang có.

---

## 3. Thay đổi backend — `app/api/v1/endpoints/bao_cao_xep_loai.py`

| # | Việc |
|---|---|
| 1 | Helper `_chan_neu_ky_thang_chi_doc(thang, nam)` — dùng lại `ky_thang_con_hieu_luc` trong `app/core/ky_tieu_chi.py`, ném 400 kèm câu hướng dẫn sang báo cáo quý |
| 2 | Gắn chốt chặn vào 5 endpoint ghi ở bảng trên. Hai endpoint nhận `chi_tiet_id` phải join lên `bao_cao_xep_loai` để lấy tháng/năm trước khi chặn |
| 3 | `get_bao_cao_don_vi`: với kỳ chỉ-đọc trả `can_edit = false`, `can_approve = false`, thêm cờ `chi_doc: true` và `ly_do_chi_doc` để giao diện hiện banner |
| 4 | **Gỡ chốt chặn lập mới** đã thêm ngày 18/9 ở `get_bao_cao_don_vi` — theo quyết định mục 6, mở báo cáo tháng nào cũng dựng được bản nháp để xem |

Không đụng: công thức tính điểm, `cho-phe-duyet`, `danh-sach`, `thong-ke`, xuất Excel —
đều là đường đọc.

---

## 4. Thay đổi frontend

| # | Việc | Tệp |
|---|---|---|
| 5 | Bỏ đoạn lọc ẩn tab `bao-cao`; thay bằng truyền cờ chỉ-đọc xuống tab | `app/(main)/xep-loai/page.tsx` |
| 6 | Nhãn tab đổi "Duyệt đánh giá tháng" → "Đánh giá tháng (chỉ xem)" khi kỳ chỉ-đọc | `types/xep-loai.ts` |
| 7 | `TabBaoCao`: ép `canEdit=false`, `canApprove=false`; ẩn nút Gửi phê duyệt, Đề xuất, Phê duyệt/Từ chối, Trả lại, và **nút "Sửa điểm tiêu chí chung"** (nút này hiện bỏ qua `canEdit` — bật cho CCT/TDV/admin ở mọi trạng thái); giữ nguyên nút Xuất Excel; thêm banner giải thích | `components/xep-loai/tabs/TabBaoCao.tsx` |
| 8 | `/xep-loai/phe-duyet` đang chuyển hướng tới `?tab=bao-cao` — kiểm tra lại sau khi tab hiện trở lại | `app/(main)/xep-loai/phe-duyet/page.tsx` |

---

## 5. Kiểm thử

Tệp `backend/tests/integration/test_bao_cao_thang_chi_doc.py`, chạy trên `kpi_haiquan_test`:

1. Kỳ ≥ Q3/2026: cả 5 endpoint ghi đều trả **400**, dữ liệu không đổi một dòng.
2. Kỳ ≥ Q3/2026: `GET /don-vi/thang/…` vẫn **200**, `can_edit=false`, `can_approve=false`.
3. **Không hồi tố**: kỳ ≤ Q2/2026 vẫn đề xuất, gửi duyệt, phê duyệt bình thường.
4. `phe_duyet_bao_cao` bị chặn ⇒ không có bản ghi `danh_gia_thang` nào bị đặt
   `is_khoa` ngoài ý muốn ở tháng neo.
5. Sửa điểm tiêu chí từ màn báo cáo quý ghi đúng vào phiếu quý (bản ghi tháng neo),
   giữ nguyên `diem_phe_duyet` của Trưởng duyệt để đối chiếu.

Kèm chạy lại toàn bộ bộ test hiện có.

---

## 6. Quyết định của người dùng (21/09/2026)

| Vấn đề | Quyết định |
|---|---|
| Tháng chưa có báo cáo | **Tự tạo bản nháp để xem** — giữ cơ chế cũ, gỡ chốt chặn "không lập mới" đã thêm ngày 18/9 |
| Báo cáo nháp có tự tính lại điểm khi mở | **Có** — số liệu luôn khớp điểm quý mới |
| Sửa điểm tiêu chí chung của quý | **Thêm nút vào màn báo cáo QUÝ** (tab Đánh giá Quý) — nơi đúng nghĩa nhất; gỡ nút khỏi màn báo cáo tháng |
| Phiếu cá nhân tháng (01A/01B) | **Giữ ẩn** như hiện nay |

### Phát hiện kèm theo

Nút "Sửa điểm tiêu chí chung" trên màn báo cáo **tháng** hiện **đã ghi thẳng vào phiếu
quý**: từ 18/9 backend quy mọi truy vấn tiêu chí về tháng neo, nên modal nhận
`danh_gia_thang_id` của bản ghi T9 dù mở từ tháng 7. Dữ liệu không sai, nhưng tiêu đề
modal vẫn ghi "Tháng 7/2026" — đánh lừa người dùng. Trang `/dieu-chinh-tieu-chi` cũng
đang ghi nhãn "tháng" y như vậy. Cả hai nhãn phải sửa.

---

## 6b. Việc bổ sung theo quyết định: nút sửa điểm tiêu chí ở màn báo cáo QUÝ

| # | Việc | Tệp |
|---|---|---|
| 9 | Thêm cột thao tác "Sửa điểm TC" trong bảng chi tiết báo cáo quý, mở `SuaDiemTieuChiModal` với `thang = quý × 3` (tháng neo) để modal lấy đúng phiếu quý | `components/xep-loai/tabs/TabQuy.tsx` |
| 10 | Quyền hiện nút: CCT, PCCT, Trưởng đơn vị, admin — giống trang Điều chỉnh điểm TC. Backend đã chặn Trưởng đơn vị đụng công chức đơn vị khác (PERM_002), không nới thêm | `TabQuy.tsx` |
| 11 | Modal đổi tiêu đề từ "Tháng N/NNNN" sang nhãn kỳ ("Quý 3/2026") khi kỳ chấm theo quý | `components/xep-loai/modals/SuaDiemTieuChiModal.tsx` |
| 12 | Trang `/dieu-chinh-tieu-chi`: bộ chọn và tiêu đề đổi sang kỳ quý cho khớp thực tế | `app/(main)/dieu-chinh-tieu-chi/page.tsx` |
| 13 | Gỡ nút "Sửa điểm TC" khỏi màn báo cáo tháng (nằm trong hạng mục 7 — chế độ chỉ xem) | `TabBaoCao.tsx` |

Sau khi làm xong, điểm tiêu chí chung của quý sửa được ở đúng ba nơi, đều mang nhãn quý:
lúc duyệt (tab Duyệt tiêu chí) · màn báo cáo quý (mới) · trang Điều chỉnh điểm TC.

---

## 7. Ước lượng

| Phần | Thời gian |
|---|---|
| Backend (chốt chặn 5 endpoint ghi + cờ chỉ-đọc + gỡ chặn lập mới) | 0,5 ngày |
| Frontend: hiện lại tab tháng ở chế độ chỉ xem + banner | 0,5 ngày |
| Frontend: nút sửa điểm tiêu chí ở màn báo cáo quý + sửa nhãn hai nơi | 0,5 ngày |
| Kiểm thử + phát hành | 0,25 ngày |
| **Tổng** | **~1,75 ngày** |

Quay lui: chế độ chỉ-đọc dùng chung mốc `TC_THEO_QUY_TU`; đặt lại `(9999, 1)` là mọi
thứ trở về như cũ, không có migration nào để gỡ.
