# Báo cáo rà quét an toàn thông tin NỘI BỘ (tự thực hiện trước khi bàn giao)

> Ngày rà quét: 30/07/2026. Công cụ: `bandit` 1.8.x (quét mã nguồn Python), `pip-audit` (lỗ hổng thư viện Python theo CSDL PyPI/OSV), `npm audit` (lỗ hổng thư viện Node.js), rà soát cấu hình thủ công.
> **Tài liệu lưu hành nội bộ** — dùng để chủ động khắc phục trước khi đoàn kiểm tra rà quét chính thức.

## 0. KẾT QUẢ ĐỢT VÁ BẢO MẬT 31/07/2026 (nhánh `feature/security-patch-2026-07`)

| # | Hạng mục | Trạng thái |
|---|---|---|
| 1 | Nâng thư viện Python có lỗ hổng: `python-jose` 3.3.0→3.5.0, `python-multipart` 0.0.20→0.0.32, **`fastapi` 0.115.6→0.141.1 + `starlette` 0.41.3→1.3.1** (5 PYSEC DoS), `cryptography`, `urllib3`, `pillow`, `lxml`, `orjson`, `click`, `idna`, `mako`, `pyasn1`, `pygments`, `python-dotenv`, `ecdsa` | ✅ Đã vá |
| 2 | Thư viện Node.js: `next` 16.1.4→16.2.12, `axios`→1.19.0, **`xlsx` 0.18.5→0.20.3** (bản vá lấy từ CDN chính thức SheetJS vì npm registry dừng ở 0.18.5), override `postcss`≥8.5.18 + `sharp`≥0.35.0 — **runtime sạch 100% cảnh báo**; còn 9 cảnh báo thuộc chuỗi eslint (chỉ môi trường dev, bản vá đòi eslint 10 chưa được hệ sinh thái Next hỗ trợ — chấp nhận, chờ upstream) | ✅ Đã vá |
| 3 | Chống brute-force login: rate limit 30 lần/phút/IP (slowapi, key theo X-Real-IP sau nginx) + khóa tài khoản tạm 15 phút sau 10 lần sai liên tiếp; log sự kiện qua logger `app.security` | ✅ Đã thêm |
| 4 | Ẩn `/docs`, `/redoc`, `/openapi.json` production trên **cả 8 service** (trước đây KPI 8000 còn hở `/api/v1/openapi.json`; 7 service phụ hở ở localhost) — bật lại bằng `DEBUG=true` | ✅ Đã tắt |
| 5 | **Gỡ mật khẩu DB production + INTERNAL_API_KEY hardcode** làm default trong 8 file `config.py` + helpers (phát hiện mới trong đợt vá — nghiêm trọng vì mã nguồn sắp bàn giao); rotate INTERNAL_API_KEY sang giá trị ngẫu nhiên trong `.env`; verifier từ chối khi key chưa cấu hình | ✅ Đã gỡ |
| 6 | Bắt buộc đổi mật khẩu mặc định `123456` (cờ `must_change_password`) | ⏳ Đợt sau (quyết định 31/07) |
| 7 | Mật khẩu DB cũ vẫn nằm trong **git history** (dù đã gỡ khỏi code hiện tại; gói bàn giao dùng `git archive` nên không chứa history) — khuyến nghị **đổi mật khẩu DB** ở đợt bảo trì tới | ⏳ Khuyến nghị |

**Kiểm chứng sau vá (31/07/2026, DB test `kpi_haiquan_test` clone từ prod):**

- pip-audit sau nâng cấp: `python-jose`, `python-multipart`, `starlette`, `fastapi`, `urllib3`, `cryptography`, `pillow`... đều sạch. Còn lại duy nhất `ecdsa` PYSEC-2026-1325 (lỗ hổng timing Minerva — **chưa có bản vá upstream**, là dependency của python-jose; rủi ro thấp vì hệ thống chỉ dùng HS256, không dùng ECDSA) và các gói dev (pytest...).
- npm audit: **runtime 0 cảnh báo**; 9 cảnh báo high còn lại toàn bộ trong chuỗi eslint dev-only.
- Test hồi quy toàn backend: **~706 PASS / 41 FAIL** — đã đối chứng 41 fail này trên cả (code cũ + lib cũ): fail y hệt → **toàn bộ có sẵn từ trước** (test phụ thuộc dữ liệu, viết trên snapshot prod cũ), đợt vá gây **0 regression**. Khuyến nghị: làm mới bộ test data-dependent ở đợt bảo trì tới.
- Frontend `npm run build`: PASS (68/68 trang).
- Smoke in-process: login sai → 401 AUTH_003; sai 10 lần → khóa 429 AUTH_006 (Retry-After 15 phút); vượt 30 req/phút/IP → 429 AUTH_005; `/docs` + `/api/v1/openapi.json` → 404; `/health` → 200.

Chi tiết trước khi vá giữ nguyên bên dưới để đối chiếu.

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
