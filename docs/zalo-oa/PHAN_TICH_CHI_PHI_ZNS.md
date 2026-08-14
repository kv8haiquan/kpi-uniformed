# Phân tích chi phí kênh Zalo ZNS — Họp Không Giấy

**Ngày lập:** 14/08/2026 · **Nguồn số liệu:** `common.thong_bao` (dữ liệu thật, 05/2026–07/2026) · **Đơn giá:** `template/info/v2` của Zalo

> Tài liệu này để lãnh đạo quyết định **mức độ bật kênh Zalo**, không phải để mô tả kỹ thuật. Mọi con số đều đếm từ dữ liệu thật đang có trong hệ thống, không ước lượng.

---

## 1. Kết luận trước

| Câu hỏi | Trả lời |
|---|---|
| Một cuộc họp tốn bao nhiêu? | **Trung bình 79.000đ**, cuộc lớn nhất đã ghi nhận **204.800đ** |
| Chi phí lớn nhất nằm ở đâu? | **Tin nhắc họp — chiếm 51,9%**, hơn một nửa |
| Cắt được bao nhiêu mà không mất tác dụng? | **~36%** nếu giữ đúng 1 mốc nhắc |
| Rủi ro lớn nhất hiện nay? | **Hệ thống chưa có trần chi tiêu** (xem mục 6) |

**Khuyến nghị:** giữ **một mốc nhắc trước 1 giờ**, bỏ mốc 24 giờ và 30 phút. Tiết kiệm ~36% chi phí, và thực tế người nhận cũng không cần bị nhắc ba lần cho cùng một cuộc họp.

---

## 2. Đơn giá

Cả 4 mẫu tin đều **cùng giá**, không có mẫu nào rẻ hơn:

| Loại tin | Mã mẫu | Gửi theo SĐT | Gửi theo Zalo ID |
|---|---|---:|---:|
| Giấy mời họp | 623165 | 800đ | 560đ |
| Nhắc họp | 623236 | 800đ | 560đ |
| Thay đổi lịch họp | 623180 | 800đ | 560đ |
| Hủy họp | 623182 | 800đ | 560đ |

Hiện hệ thống gửi **theo số điện thoại — 800đ/tin**. Cột "Zalo ID" là mức giá rẻ hơn 30%, nhưng đòi hỏi điều kiện chưa có (xem mục 5.3).

> ⚠️ **Đính chính:** các trao đổi trước đây có nêu con số ~300đ cho tin nhắc/thay đổi/hủy. Con số đó **sai**. Đã kiểm lại trực tiếp trên API Zalo: cả 4 mẫu đều 800đ.

---

## 3. Chi phí thật đã phát sinh

Toàn bộ hoạt động HKG từ 05/2026 đến 07/2026:

| Loại tin | Số tin | Tỷ trọng | Thành tiền |
|---|---:|---:|---:|
| Giấy mời họp | 245 | 35,3% | 196.000đ |
| Nhắc trước 24 giờ | 134 | 19,3% | 107.200đ |
| Nhắc trước 1 giờ | 113 | 16,3% | 90.400đ |
| Nhắc trước 30 phút | 113 | 16,3% | 90.400đ |
| Thay đổi lịch họp | 50 | 7,2% | 40.000đ |
| Hủy họp | 39 | 5,6% | 31.200đ |
| **Tổng** | **694** | **100%** | **555.200đ** |

**Ba mốc nhắc gộp lại = 360 tin = 288.000đ = 51,9% tổng chi phí.** Đây là khoản lớn nhất, và cũng là khoản dễ cắt nhất.

### Theo tháng

| Tháng | Số cuộc họp | Số tin | Chi phí |
|---|---:|---:|---:|
| 05/2026 | 6 | 581 | 464.800đ |
| 07/2026 | 1 | 113 | 90.400đ |

Chênh lệch giữa hai tháng **không phải do dùng nhiều hay ít**, mà do **số cuộc họp**. Đây là điểm quan trọng nhất của toàn bộ tài liệu này.

---

## 4. Chi phí tính theo cuộc họp, không theo tháng

Chỉ **7 cuộc họp** sinh ra toàn bộ 694 tin. Chi tiết từng cuộc:

| Ngày | Mời | Nhắc 24h | Nhắc 1h | Nhắc 30p | Đổi lịch | Hủy | Tổng tin | Chi phí |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 03/05/2026 | 109 | 24 | 29 | 29 | 36 | 29 | 256 | **204.800đ** |
| 08/05/2026 | 44 | 44 | 44 | 44 | 0 | 0 | 176 | 140.800đ |
| 29/07/2026 | 35 | 26 | 26 | 26 | 0 | 0 | 113 | 90.400đ |
| 03/05/2026 | 28 | 14 | 14 | 14 | 14 | 0 | 84 | 67.200đ |
| 26/05/2026 | 26 | 26 | 0 | 0 | 0 | 0 | 52 | 41.600đ |
| 03/05/2026 | 0 | 0 | 0 | 0 | 0 | 7 | 7 | 5.600đ |
| 01/05/2026 | 3 | 0 | 0 | 0 | 0 | 3 | 6 | 4.800đ |

**Chi phí một cuộc họp:** trung bình **79.300đ** · trung vị **67.200đ** · cao nhất **204.800đ**

**Quy mô mời:** trung bình 40,8 người/cuộc · trung vị 31,5 · cao nhất **109 người**

### Cách tính nhanh cho một cuộc họp sắp tới

```
Chi phí ≈ Số người được mời × 2,83 × 800đ  ≈  Số người × 2.270đ
```

Hệ số 2,83 là số tin trung bình mỗi người nhận cho một cuộc họp (1 giấy mời + các mốc nhắc + tin đổi/hủy nếu có).

| Quy mô cuộc họp | Chi phí ước tính |
|---|---:|
| 10 người | ~23.000đ |
| 30 người | ~68.000đ |
| 50 người | ~113.000đ |
| 100 người | ~226.000đ |

### Hai khoản phát sinh dễ bị bỏ quên

Cuộc họp ngày **03/05** cho thấy rõ: 109 giấy mời, rồi **36 tin đổi lịch**, rồi **29 tin hủy họp**. Tức là:

- **Mỗi lần đổi lịch = thêm 1 tin/người = thêm tiền.** Cuộc đó tốn thêm 28.800đ chỉ vì đổi lịch.
- **Hủy họp cũng tốn tiền** — 23.200đ để báo hủy.

Họp bị đổi lịch hoặc hủy nhiều lần sẽ đội chi phí lên nhanh. Đây là lý do nên chốt lịch trước khi phát giấy mời.

---

## 5. Các phương án cắt giảm

### 5.1 Bốn kịch bản mốc nhắc

Áp lên đúng dữ liệu 694 tin đã phát sinh:

| Kịch bản | Mốc nhắc giữ lại | Số tin | Chi phí | Tiết kiệm |
|---|---|---:|---:|---:|
| **A — Hiện trạng** | 24h + 1h + 30 phút | 694 | 555.200đ | — |
| **B** | 24h + 1h | 581 | 464.800đ | **−16,3%** |
| **C — Khuyến nghị** | Chỉ 1h | 447 | 357.600đ | **−35,6%** |
| **D** | Không nhắc | 334 | 267.200đ | **−51,9%** |

### 5.2 Dự toán theo nhịp họp

HKG hiện mới ở giai đoạn thí điểm (7 cuộc trong 3 tháng). Nếu triển khai đều:

| Nhịp họp | A (hiện trạng) | B | C (khuyến nghị) | D |
|---|---:|---:|---:|---:|
| 2 cuộc/tháng | 158.600đ | 132.800đ | **102.200đ** | 76.300đ |
| 4 cuộc/tháng | 317.300đ | 265.600đ | **204.300đ** | 152.700đ |
| 8 cuộc/tháng | 634.500đ | 531.200đ | **408.600đ** | 305.400đ |
| **Cả năm** (4 cuộc/tháng) | **3.807.000đ** | 3.187.000đ | **2.452.000đ** | 1.832.000đ |

Chọn kịch bản C ở nhịp 4 cuộc/tháng **tiết kiệm khoảng 1.355.000đ/năm**.

### 5.3 Giảm 30% bằng cách gửi theo Zalo ID — **hiện chưa dùng được**

Zalo niêm yết hai mức giá cho cùng một mẫu tin: **800đ gửi theo số điện thoại**, **560đ gửi theo Zalo ID**. Ở nhịp 4 cuộc/tháng kịch bản C, mức chênh này trị giá khoảng **735.000đ/năm**.

Đã kiểm hai bước, kết quả trái ngược nhau:

**Bước 1 — Tra Zalo ID từ số điện thoại: LÀM ĐƯỢC.** Đã dựng công cụ `scripts/zalo_tra_uid.py` và thử trên 20 số thật:

| Kết quả | Số người | Tỷ lệ |
|---|---:|---:|
| Đã follow OA — lấy được Zalo ID | 13 | **65,0%** |
| Chưa follow OA | 7 | 35,0% |
| Số điện thoại hỏng | 0 | 0% |

Việc tra dùng chính số điện thoại làm khóa nên kết quả **chính xác tuyệt đối**, không phải đoán theo tên hay ảnh đại diện.

**Bước 2 — Gửi tin theo Zalo ID: KHÔNG LÀM ĐƯỢC.** Đã thử toàn bộ các đường gọi khả dĩ; API gửi tin của Official Account này **bắt buộc phải có số điện thoại**, đưa Zalo ID vào thì bị từ chối (`error -108`). Không có endpoint thay thế nào mở cho OA này.

**Kết luận:** mức giá 560đ có niêm yết nhưng **đường gửi chưa được mở** cho Official Account của Chi cục. Đây là việc phải hỏi VNG, không phải việc lập trình.

> ⚠️ **Vì vậy KHÔNG nên quét Zalo ID của cả 543 công chức lúc này.** Việc quét gửi số điện thoại thật của cán bộ sang máy chủ VNG, mà hiện chưa đổi lấy được lợi ích nào. Chỉ nên làm sau khi VNG xác nhận mở đường gửi theo Zalo ID.

> **Đính chính hai điều tôi đã nói sai trong quá trình khảo sát:**
> 1. Tôi từng khẳng định Zalo *không* cho tra Zalo ID từ số điện thoại. **Sai** — API `oa/getprofile` nhận tham số `phone` và trả về đầy đủ hồ sơ nếu người đó đã follow OA.
> 2. Tôi từng đánh giá khoản tiết kiệm này "quá nhỏ, không đáng làm", dựa trên ước lượng ~100 tin/tháng. Ước lượng đó sai; với số liệu thật khoản này đáng kể hơn nhiều.

### 5.4 Xếp hạng các phương án

| Phương án | Tiết kiệm | Công sức | Rủi ro | Nên làm |
|---|---:|---|---|---|
| Bỏ mốc nhắc 30 phút và 24 giờ | −35,6% | Sửa 1 chỗ trong mã nguồn | Không | ✅ **Ngay** |
| Chốt lịch trước khi phát giấy mời | Tùy | Quy trình, không cần sửa mã | Không | ✅ **Ngay** |
| Không gửi Zalo cho người đã xác nhận dự họp | ~10–15% | Cần nối với HKG | Thấp | 🟡 Cân nhắc |
| Chỉ gửi Zalo cho họp gắn cờ quan trọng | Tùy | Cần thêm trường dữ liệu | Thấp | 🟡 Cân nhắc |
| Gửi theo Zalo ID | −30% (×65% người dùng ⇒ ~−19,5%) | Tra ID đã làm được; **đường gửi chưa mở** | — | ⏸️ Chờ VNG trả lời |

---

## 6. Rủi ro cần xử lý: chưa có trần chi tiêu

Đây là điểm tôi muốn lãnh đạo lưu ý nhất.

Zalo cấp hạn mức **20.000 tin/ngày**. Với đơn giá 800đ, mức phơi nhiễm tối đa trong một ngày là:

```
20.000 tin × 800đ = 16.000.000đ/ngày
```

Hiện tại **trong hệ thống không có bất kỳ trần chi tiêu nào**. Các cơ chế bảo vệ đang có chỉ chặn được sự cố kỹ thuật, không chặn được chi phí:

| Cơ chế đang có | Chặn được gì | Không chặn được gì |
|---|---|---|
| Chỉ nhặt thông báo trong 2 giờ qua | Xả tồn đọng dữ liệu cũ | Cuộc họp mới quy mô lớn |
| Tối đa 50 tin mỗi vòng quét | Dồn tải tức thời | Tổng chi phí trong ngày |
| Chống gửi trùng ở mức cơ sở dữ liệu | Gửi lặp | Gửi đúng nhưng quá nhiều |
| Khung giờ 6h–22h | Nhắn lúc rạng sáng | Chi phí |

Tình huống thực tế có thể xảy ra: mời họp toàn đơn vị 543 người, bị đổi lịch hai lần → 543 × 5 tin × 800đ ≈ **2.170.000đ cho một cuộc họp**, không có gì cảnh báo trước.

**Đề xuất:** đặt trần chi tiêu theo ngày và theo tháng, vượt trần thì dừng gửi và báo quản trị. Đây là việc kỹ thuật nhỏ, làm được trong ngày. Cần lãnh đạo cho biết **mức trần mong muốn** — ví dụ 500.000đ/tháng.

---

## 7. Việc cần lãnh đạo quyết

1. **Giữ mấy mốc nhắc?** — Đề xuất: chỉ mốc trước 1 giờ (kịch bản C, tiết kiệm 35,6%)
2. **Trần chi tiêu tháng là bao nhiêu?** — Cần một con số để cài đặt
3. **Có gửi Zalo cho mọi cuộc họp không**, hay chỉ họp quan trọng?
4. **Hỏi VNG: Official Account của Chi cục có được mở gửi ZNS theo Zalo ID (560đ) không?** — nếu được, tiết kiệm thêm ~19,5%

---

## Phụ lục — Cách kiểm chứng lại các con số

**Đơn giá** — đọc thẳng từ Zalo, không phải con số ghi tay:

```bash
cd backend && source venv/bin/activate
python scripts/zalo_xem_template.py 623165 623236 623180 623182
```

**Thống kê chi phí** — lấy từ bảng `common.thong_bao`, lọc `doi_tuong_type` thuộc 6 loại thông báo của HKG, nhân đơn giá 800đ/tin. Đây là câu lệnh đã dùng để dựng mục 3 và 4 của tài liệu này:

```sql
SELECT to_char(created_at,'YYYY-MM') AS thang,
       doi_tuong_type AS loai,
       count(*) AS so_tin,
       count(*) * 800 AS chi_phi_dong
FROM common.thong_bao
WHERE doi_tuong_type IN ('GIAY_MOI_HOP','NHAC_HOP_24H','NHAC_HOP_1H',
                         'NHAC_HOP_30P','THAY_DOI_HOP','HUY_HOP')
GROUP BY 1, 2 ORDER BY 1 DESC, 3 DESC;
```

**Hạn mức còn lại trong ngày** — hiện **chưa có công cụ dòng lệnh**; đang phải gọi trực tiếp API `message/quota` của Zalo. Nếu lãnh đạo duyệt việc đặt trần chi tiêu ở mục 6 thì sẽ làm luôn công cụ theo dõi kèm theo.

**Lưu ý về đối soát:** số dư ví ZBS **không** giảm ngay sau khi gửi. Đồng hồ đo tin cậy là hạn mức còn lại trong ngày (`remainingQuota`) — đã kiểm chứng: gửi 1 tin thì hạn mức giảm đúng 1. Chi phí thực tế nên đối chiếu với **Nhật ký gửi** trong hệ thống ZBS của Zalo.
