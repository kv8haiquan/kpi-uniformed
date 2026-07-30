# Báo cáo rà quét an toàn thông tin NỘI BỘ (tự thực hiện trước khi bàn giao)

> Ngày rà quét: 30/07/2026. Công cụ: `bandit` 1.8.x (quét mã nguồn Python), `pip-audit` (lỗ hổng thư viện Python theo CSDL PyPI/OSV), `npm audit` (lỗ hổng thư viện Node.js), rà soát cấu hình thủ công.
> **Tài liệu lưu hành nội bộ** — dùng để chủ động khắc phục trước khi đoàn kiểm tra rà quét chính thức.

## 1. Tóm tắt kết quả

| Hạng mục | Kết quả |
|---|---|
| Lỗ hổng thư viện Python (pip-audit) | 2 thư viện production cần nâng cấp: `python-jose`, `python-multipart` |
| Lỗ hổng thư viện Node.js (npm audit) | 16 cảnh báo (13 high) — đa số ở gói build/dev; cần nâng `next`, `axios`; `xlsx` chưa có bản vá |
| Quét mã nguồn (bandit) | 43 cảnh báo — đã rà thủ công: **không phát hiện SQL injection thực tế** (các cảnh báo B608 đều là parameterized query, f-string chỉ ghép mệnh đề WHERE nội bộ) |
| Secrets trong mã nguồn | KHÔNG phát hiện SECRET_KEY/mật khẩu DB hardcode; `.env` không bị track git |
| Cấu hình | 2 điểm cần cải thiện: chưa chống brute-force login, chưa bắt buộc đổi mật khẩu mặc định |

## 2. Lỗ hổng thư viện Python (production) — CẦN VÁ

| Thư viện | Đang dùng | Lỗ hổng | Mức | Khắc phục |
|---|---|---|---|---|
| python-jose | 3.3.0 | PYSEC-2024-232 (algorithm confusion với khóa OpenSSH), PYSEC-2024-233 (DoS khi decode JWT chế tác), PYSEC-2025-185 | Cao (liên quan trực tiếp xác thực JWT) | Nâng `python-jose[cryptography]>=3.4.0` (cân nhắc chuyển `PyJWT`) |
| python-multipart | 0.0.20 | 6 lỗ hổng PYSEC-2026-* (DoS khi parse multipart/upload) | Trung bình | Nâng `python-multipart>=0.0.31` |
| pytest | 8.3.4 | PYSEC-2026-1845 | Thấp (chỉ môi trường dev/test) | Nâng khi thuận tiện |

## 3. Lỗ hổng thư viện Node.js

`npm audit`: 16 cảnh báo (1 low, 2 moderate, 13 high). Phân loại:

- **Gói runtime cần nâng:** `next` (16.1.4 → bản vá mới hơn), `axios`, `form-data`, `follow-redirects`, `undici`, `sharp`.
- **Gói build/dev (không chạy production):** `vite`, `postcss`, `@babel/core`, `js-yaml`, `minimatch`, `picomatch`, `brace-expansion`, `flatted`, `ajv` — rủi ro thực tế thấp, nâng khi build lại.
- **`xlsx` 0.18.5 — CHƯA có bản vá** (prototype pollution/ReDoS). Giảm thiểu: chức năng xuất Excel chỉ dùng cho người dùng đã xác thực, dữ liệu đầu vào do hệ thống sinh; theo dõi bản vá hoặc chuyển sang `exceljs`.

Khắc phục: `npm audit fix` (đa số có fix tự động), kiểm tra regression rồi build lại.

## 4. Kết quả quét mã nguồn (bandit) — 43 cảnh báo, đã rà thủ công

| Nhóm | Số lượng | Đánh giá sau khi rà thủ công |
|---|---|---|
| B608 — SQL qua f-string | 16 | **Cảnh báo giả**: đã kiểm tra từng vị trí (`export_bao_cao.py`, `chi_tieu`, `meeting`, `forum`) — tham số người dùng đều bind qua `:param`, f-string chỉ ghép mệnh đề WHERE cấu thành từ hằng nội bộ. Không có injection. |
| B105/B106 — "hardcoded password" | 8 | Phần lớn là cảnh báo giả (chuỗi `"bearer"`, `"access"`, `"ws_presentation"`). 2 vị trí là hằng `DEFAULT_PASSWORD = "123456"` (mật khẩu khởi tạo/reset) — đúng thiết kế nghiệp vụ nhưng xem khuyến nghị mục 5. |
| B110 — try/except pass | 6 | Chấp nhận được (bỏ qua lỗi phụ không tới hạn); nên bổ sung log. |
| B603/B607/B404 — subprocess | 9 | Script vận hành nội bộ (backup, seed), tham số cố định — chấp nhận được. |
| B104 — bind 0.0.0.0 | 1 | `app/main.py` dev-run block; production chạy sau nginx + firewall, cổng backend không mở ra ngoài — chấp nhận được. |
| B101 — assert | 3 | Trong code test — không ảnh hưởng. |

## 5. Rà soát cấu hình — các điểm CẦN CẢI THIỆN

| # | Phát hiện | Rủi ro | Khuyến nghị |
|---|---|---|---|
| 1 | Endpoint `POST /api/v1/auth/login` **chưa có rate limit / khóa tạm sau N lần sai** (slowapi mới áp dụng cho upload HKG) | Brute-force mật khẩu (đặc biệt khi tồn tại mật khẩu mặc định `123456`) | Thêm rate limit (ví dụ 5 lần/phút/IP) + khóa tạm tài khoản 15 phút sau 10 lần sai; ghi `audit_log` |
| 2 | **Chưa bắt buộc đổi mật khẩu** ở lần đăng nhập đầu / sau khi reset về `123456` | Tài khoản dùng lâu dài với mật khẩu mặc định | Thêm cờ `must_change_password`, chặn API nghiệp vụ đến khi đổi |
| 3 | JWT hạn 8 giờ, không có cơ chế thu hồi (stateless) | Token bị lộ dùng được tới hết hạn | Chấp nhận được với hệ nội bộ; cân nhắc refresh-token ngắn hạn ở phiên bản sau |
| 4 | `python-jose`/`python-multipart` phiên bản có lỗ hổng đã công bố | Xem mục 2 | Nâng cấp trong đợt vá này |
| 5 | Swagger `/docs` đã tắt production (KPI); cần rà cùng chính sách cho 7 service còn lại | Lộ cấu trúc API | Tắt `docs_url`/`openapi_url` production hoặc chặn qua nginx cho service phụ |

## 6. Các điểm ĐẠT qua rà soát

- Không có secret hardcode trong mã nguồn; `.env` nằm ngoài git; `.gitignore` chặn `.env*`, `*.dump`.
- Mật khẩu hash bcrypt; JWT HS256 với SECRET_KEY qua biến môi trường.
- Toàn bộ truy vấn DB qua ORM/parameterized — không phát hiện SQL injection.
- Validate đầu vào bằng Pydantic trên mọi endpoint; response chuẩn hóa.
- DB và các cổng backend không mở ra Internet; chỉ nginx 80/443 public; HTTPS toàn bộ.
- Backup 2 lần/ngày + off-site mã hóa + snapshot mã nguồn; retention rõ ràng; có log sao lưu.
- Kiểm tra phân quyền tại backend theo vai trò + đơn vị; chức năng nhạy cảm giới hạn CCT/TCCB/ADMIN.
- Có `audit_log` (IP, user-agent, old/new value) và lịch sử duyệt/điều chỉnh trên bảng nghiệp vụ.

## 7. Kế hoạch khắc phục đề xuất (trước khi đoàn kiểm tra rà quét)

1. **Đợt vá thư viện** (0,5 ngày + kiểm thử): nâng `python-jose`, `python-multipart`; `npm audit fix` + nâng `next`, `axios`; build + smoke test nội bộ trên DB test.
2. **Hardening đăng nhập** (1 ngày): rate limit login + khóa tạm + cờ bắt buộc đổi mật khẩu mặc định.
3. **Tắt OpenAPI/docs production** cho 7 service phụ (0,5 ngày).
4. Rà lại sau khi vá bằng đúng bộ công cụ trên, đính kèm kết quả vào hồ sơ bàn giao.
