# Biên bản đối chiếu di trú lichkv8

## Đối chiếu số lượng bản ghi

| Nhóm dữ liệu | Nguồn | Đích | Chênh | Ghi chú |
|---|---:|---:|---:|---|
| Cuộc họp | 489 | 489 | ✅ |  |
| Trực ban (còn hiệu lực) | 333 | 333 | ✅ |  |
| Trạng thái nộp trực ban | 200 | 198 | ✅ -2 | nguồn có 2 cặp (ngày, trụ sở) bị lặp — 20/06 CHICUC và 11/07 MONGCAI; ràng buộc UNIQUE gộp lại còn một |
| Ghi chú | 7 | 6 | ✅ -1 | 1 ghi chú của tài khoản 'superadmin' — không phải công chức thật |
| Chia sẻ ghi chú | 0 | 0 | ✅ |  |

## Kiểm tra chất lượng

| Chỉ tiêu | Giá trị |
|---|---:|
| Lãnh đạo liên quan (bản ghi) | 475 |
| Cuộc họp có lãnh đạo liên quan | 447 |
| Đánh giá cuộc họp | 102 |
| Cuộc họp khớp được chủ trì | 362 |
| Cuộc họp giữ nguyên văn chủ trì | 370 |
| Sự kiện nhiều ngày | 13 |
| Mã lịch bị trùng (phải = 0) | 0 |
| Cuộc họp thiếu ngày hiển thị (phải = 0) | 0 |
| Trực ban thiếu số điện thoại | 0 |
| Cuộc họp HKG (không được đụng tới) | 9 |

## Kho tài liệu

| Chỉ tiêu | Giá trị |
|---|---:|
| Tài liệu di trú từ Drive | 813 |
| Tài liệu sẵn có của HKG (không đụng) | 40 |
| Cuộc họp có tài liệu | 197 |
| Tổng dung lượng đã gắn (MB) | 785.0 |
| Thư mục chờ đối soát (nhóm D) | 15 |
| Thư mục chờ đối soát (nhóm E) | 19 |
| File chờ đối soát | 412 |
| Tài liệu trùng khoá lưu trữ (phải = 0) | 0 |

File kho tài liệu họp tải về: **1225** · đã gắn cuộc họp: **813** · chờ đối soát: **412** · tổng đã xử lý: **1225**

## Đối chiếu thứ trong tuần

Ngày sau di trú khớp cột `THU` của bản gốc: **489 khớp, 0 lệch**.

> Cột serial `NGAY_BAT_DAU` của lichkv8 lệch sớm 1 ngày ở 212/489 dòng. Di trú lấy `NGAY_HIEN_THI` làm chuẩn vì cột `THU` xác nhận đó mới là ngày đúng.

**Kết luận:** ✅ Toàn bộ khớp.
