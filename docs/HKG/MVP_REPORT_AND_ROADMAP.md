# BÁO CÁO MVP & ROADMAP — Module Họp Không Giấy (HKG)

**Phiên bản:** 1.0 · **Ngày:** 2026-05-02 · **Trạng thái:** MVP đã release production cho 549 user

---

## 1. Tóm tắt tình trạng

Module **Họp Không Giấy (HKG)** — quản lý cuộc họp số hóa toàn trình cho Chi cục Hải quan Khu vực VIII — đã hoàn tất giai đoạn MVP và vận hành thực tế trên `kpihaiquan.vn` từ 01/05/2026. Tất cả 6 module nghiệp vụ chính đã hoạt động đầu-cuối, đã qua 8 vòng fix bug từ phản hồi UAT, và mở quyền truy cập cho toàn bộ 549 cán bộ công chức.

**Đánh giá tổng quan:** ✅ MVP đạt mục tiêu chức năng, đủ điều kiện vận hành nội bộ. Các điểm cần đầu tư trước khi mở rộng quy mô (multi-region, mobile, CKS thật) được liệt kê trong §6 Roadmap.

---

## 2. Phạm vi đã ship

### 2.1 Module nghiệp vụ (6/6)

| # | Module | Mô tả | Trạng thái |
|---|---|---|---|
| 1 | **Cuộc họp** | CRUD cuộc họp (3 khối: chuyên môn / tổng hợp / lãnh đạo), đa hình thức (trực tiếp/online/hybrid), 6 trạng thái lifecycle | ✅ |
| 2 | **Thành phần & Mời họp** | Quản lý thành phần tham dự, sửa thành phần (PUT replace với diff), tích hợp bộ chọn CBCC theo đơn vị | ✅ |
| 3 | **Tài liệu** | Upload/list/xem/tải, phân quyền CÔNG_KHAI/HẠN_CHẾ, soft-delete, short-lived JWT token cho file gateway, **preview Office docs qua LibreOffice** | ✅ |
| 4 | **Điểm danh** | QR code động (TTL 1h), tự điểm danh trong window (-30 / +60 phút), 4 trạng thái (CHƯA_MỞ / CÓ_MẶT / ĐẾN_MUỘN / ĐÃ_ĐÓNG) | ✅ |
| 5 | **Ý kiến phát biểu** | Submit ý kiến, đính kèm file, threading | ✅ |
| 6 | **Biên bản & Kết luận** | Soạn biên bản TipTap rich-text, ký số mock (SHA-256 + QR + watermark ReportLab), export DOCX/PDF, kết luận → tiến độ thực hiện | ✅ |

### 2.2 Hạ tầng & Tooling

| Hạng mục | Chi tiết |
|---|---|
| Backend service | `meeting_service` chạy port **8006**, internal-only (bind `127.0.0.1`) |
| Frontend | `/hop-khong-giay/*` integrate Next.js 16 main app |
| Database | Schema **`meeting`** trong DB `kpi_haiquan`, FK đọc `public.cong_chuc/don_vi/vai_tro` |
| Migrations | 11 alembic revisions (`mt_001` → `mt_011_seed_roles`) — tất cả applied production |
| Auth | JWT shared SECRET_KEY với KPI backend (no extra login) |
| Storage | Filesystem `uploads/meeting/`, alias env `HKG_UPLOAD_DIR` cho production isolation |
| Background jobs | APScheduler in-process — 4 jobs (nhắc họp, đóng điểm danh, tạo nhắc tiến độ, cleanup token) |
| Reverse proxy | Nginx `/api/v1/hop-khong-giay/` → `localhost:8006` |
| Process manager | PM2 entry `meeting-backend` trong `ecosystem.config.js` |
| Test coverage | **146 tests** trên 11 file pytest (cuoc_hop 26, tai_lieu 15, bien_ban 17, ...), tx-rollback + production guard |

---

## 3. Quyết định kiến trúc đáng chú ý

| Quyết định | Lý do | Đánh đổi |
|---|---|---|
| **Multi-schema 1 DB** thay vì DB riêng | Cross-schema JOIN tới `public.cong_chuc` không cần API, 1 connection pool | Khó tách service về sau nếu cần (chấp nhận, vì tránh microservice trap khi <10 service) |
| **Filesystem storage** thay vì MinIO | Dependency-lite, đủ dùng cho <100GB, không cần ops object storage | Phải migrate khi >100GB hoặc multi-node (xem §6.P2) |
| **APScheduler in-process** thay vì Celery+Redis | Không cần broker, deploy đơn giản | Job mất khi service restart trong khoảnh khắc; đủ cho jobs idempotent |
| **JWT shared key** thay vì OAuth2 between services | Mỗi service tự verify, không call kpi-backend mỗi request | Tất cả service phải biết SECRET_KEY (đã đặt rule không hardcode) |
| **Mock CKS (SHA-256 + ReportLab QR)** | Phase 1 không có HSM/USB token | **Không có giá trị pháp lý** — phải replace bằng CKS thật trước khi dùng cho biên bản chính thức (xem §6.P1) |
| **LibreOffice convert Office → PDF** cho preview | Browser native chỉ render PDF/ảnh; viewer Office Online cần URL public không phù hợp file sau JWT | Tốn ~700MB binary + 2-3GB cache disk; conversion 2-5s/file lần đầu |
| **Iframe wrapper page** cho preview | Bypass Chrome setting "Download PDFs" — top-level navigation tới PDF có thể trigger download, iframe luôn render | +1 route FE; UX tốt hơn |
| **Mở quyền cho 549 user ở MVP** thay vì rollout dần | Nhu cầu vận hành tức thì, không có gate-keeping logic phức tạp | Không có A/B safe rollout; rủi ro được mitigate bằng rollback đơn giản (sửa `userCanAccessHkg` trả `false`) |

---

## 4. Bug & lesson learned trong giai đoạn UAT (G4-fix 1→8)

| # | Vấn đề | Cách fix | Bài học |
|---|---|---|---|
| 1 | TipTap chưa cài → biên bản hỏng | `npm install @tiptap/react @tiptap/starter-kit @tiptap/pm` | Verify dependencies thực ship trước khi mark module done |
| 2 | Search CBCC không filter theo đơn vị | Tạo endpoint `/cong-chuc/search` riêng với param `don_vi_id` | Reuse KPI endpoint không phải lúc nào cũng đủ — module mới có thể cần API riêng |
| 3 | Port conflict với portal_service (8004) | Chuyển HKG sang **8006** (8005 cũng đã bị common chiếm) | Cập nhật bảng port mapping CLAUDE.md ngay khi thêm service |
| 4 | CBCC thường thấy tính năng admin (disabled buttons) | Refactor `MeetingContext.canEdit` để **HIDE** thay vì disable | UX bảo mật: không hiển thị action user không có quyền, kể cả disabled |
| 5 | Timezone bug điểm danh — UTC vs local | Dùng `datetime.now()` naive local thay vì UTC | Service nội bộ 1 timezone (Asia/HCM) thì naive local đơn giản hơn UTC + tz-conversion |
| 6 | **🔴 CRITICAL — Test fixture xóa nhầm file production** (`shutil.rmtree("uploads/meeting")`) | (a) restore file từ /docs/HKG/, (b) sandbox `_TEST_UPLOAD_DIR = tempfile.mkdtemp()` set trước khi import service, (c) thêm env alias `HKG_UPLOAD_DIR` cho production tách path | **KHÔNG BAO GIỜ** test chạm path production. Mọi cleanup phải nằm trong tmpdir. Đã update CLAUDE.md rule. |
| 7 | PDF "view" tự auto-download | Backend thêm `content_disposition_type="inline"`, FE thêm wrapper page render qua iframe | Chrome "Download PDFs" setting áp dụng cho top-level nav, không áp dụng iframe |
| 8 | File Word/Excel không preview | Cài LibreOffice + service `preview_service.py` convert Office → PDF với cache | Browser native không render Office; LibreOffice headless là giải pháp internal-friendly nhất |

---

## 5. Đánh giá Production-Readiness

### ✅ Đã ổn

- **Functional coverage**: 6 module chạy đầu-cuối, 146 tests pass
- **Auth & permission**: JWT shared, RBAC theo role + platform_role + chu_toa/thu_ky của cuộc họp
- **Audit trail**: Mọi action ghi vào `common.audit_log` (VIEW_DOC, DOWNLOAD_DOC, DELETE_DOC, ...)
- **Backup-friendly**: File production tách path (`HKG_UPLOAD_DIR`), DB chung backup KPI
- **Process supervision**: PM2 auto-restart, ecosystem.config.js đầy đủ 8 service
- **Reverse proxy**: Nginx route OK, HTTPS qua Let's Encrypt sẵn có

### ⚠️ Cần monitor / cải thiện

| Hạng mục | Rủi ro | Khuyến nghị |
|---|---|---|
| **LibreOffice memory** | Mỗi convert spawn ~200MB; 10 user cùng xem 10 file mới = 2GB RAM peak | Monitor RAM, throttle concurrent conversion (semaphore N=3) nếu cần |
| **Cache disk growth** | `_preview_cache/` không có cleanup, năm đầu ~2-3GB | Cron weekly xóa cache file `mtime < now - 30days` |
| **Single-server deployment** | 1 VM xử lý tất cả; downtime kéo dài nếu host fail | Sao lưu DB hàng ngày + có sẵn snapshot VM (đã có) |
| **No rate limit** | User có thể spam upload 100MB/file | Thêm middleware giới hạn 10 upload/phút/user |
| **No metrics/observability** | Chỉ có pm2 logs; không có trace performance | Thêm Prometheus + Grafana hoặc tối thiểu structured log + log rotation |
| **APScheduler jobs single-process** | Nếu service restart đúng giờ chạy job, có thể bỏ lỡ | Job design idempotent; thêm `coalesce=True misfire_grace_time=300` (đã có) |

### ❌ Còn nợ — KHÔNG block MVP nhưng phải xử lý sớm

| Hạng mục | Mức độ |
|---|---|
| **CKS thật** (HSM/USB token) thay cho mock SHA-256 | 🔴 Cao — biên bản hiện tại không có giá trị pháp lý |
| **Mobile/PWA** | 🟡 Trung — UAT cho thấy 30%+ user dùng điện thoại điểm danh QR |
| **Realtime collab** soạn biên bản nhiều người | 🟡 Trung — hiện đang dùng "ai mở sau ghi đè" |
| **Email/SMS nhắc họp** | 🟢 Thấp — đã có in-app notification, tốt hơn nếu thêm |
| **Tìm kiếm full-text** trong tài liệu/biên bản | 🟢 Thấp — pg_tsvector đã có sẵn, chưa wire |
| **Migration MinIO** khi >100GB | 🟢 Thấp — chưa cấp bách (hiện đang ~1MB) |

---

## 6. Roadmap đề xuất

### P0 — Hardening (tuần 1-2 sau MVP)

Mục tiêu: tránh sự cố production.

1. **Backup tự động hàng ngày**:
   - DB dump → `/var/backup/kpi_haiquan_$(date).sql.gz`
   - rsync `/var/data/hkg/uploads/` sang storage thứ 2
   - Retention 30 ngày + monthly snapshot 1 năm
2. **Monitoring cơ bản**: cài `pm2-logrotate`, check disk space daily, alert email khi pm2 process restart >3 lần/giờ
3. **Cron cleanup cache**: xóa `_preview_cache/*.pdf` cũ >30 ngày
4. **Rate limit upload**: 10 file / 5 phút / user
5. **Cập nhật `HKG_UPLOAD_DIR=/var/data/hkg/uploads/meeting`** trong production `.env` (đã có hướng dẫn ở `PM2_DEPLOY.md` §5A)

### P1 — Pháp lý + UX cải thiện (tuần 3-6)

1. **🔴 CKS thật cho biên bản**:
   - Nghiên cứu integration với `pyHanko` + USB token (Vinaphone CA / VNPT CA)
   - Workflow: chu_toa cắm USB → ký digest PDF biên bản → embed signature theo PAdES
   - Mock cũ vẫn giữ làm fallback "preview" cho draft, **production phải block** ký mock
2. **PWA cho mobile**:
   - Add manifest.json + service worker
   - Tối ưu UX điểm danh QR (camera fullscreen)
   - Offline view tài liệu đã cache
3. **Email/SMS nhắc họp** (có Microsoft Graph hoặc SMTP nội bộ):
   - 24h trước, 1h trước, khi đến giờ
   - Template tiếng Việt, link 1-click vào meeting page
4. **Realtime soạn biên bản** (hoặc auto-save + warning):
   - Quick win: thêm `updated_at` check, FE warn nếu version đã đổi
   - Long-term: Yjs/Hocuspocus cho true collaborative editing

### P2 — Tính năng mở rộng (tháng 2-3 sau MVP)

1. **Tích hợp lịch Outlook/Calendar** — đẩy cuộc họp ra Outlook của participants
2. **Video conference link** — auto-generate Jitsi/Zoom URL khi tạo họp online
3. **Search full-text** trong biên bản + tài liệu (pg_tsvector + GIN index, sẵn có khả năng pg)
4. **Voting/biểu quyết** trong cuộc họp — module 7 (chưa có spec)
5. **Phân tích thống kê**: dashboard số họp/tháng/khối, tỷ lệ điểm danh, thời gian trung bình, top user phát biểu
6. **Migration MinIO** khi tổng `uploads/` > 50GB
7. **Cluster Postgres + Redis cache** khi concurrent user > 100

### P3 — Tương lai (Q3-Q4 2026)

1. **AI features**:
   - Tự động transcribe ghi âm cuộc họp → biên bản nháp (Whisper)
   - Tóm tắt biên bản dài (Claude/GPT)
   - Trích xuất task → sync vào module Tiến độ
2. **App mobile native** (React Native) nếu PWA không đủ
3. **Federation với HQKV khác** — chia sẻ template, mời chéo đại diện
4. **E-signing flow đầy đủ**: nhiều người ký (chu_toa + thu_ky), thứ tự ký, gửi ký từ xa

---

## 7. Quick wins — có thể làm trong 1-2 ngày

Nếu cần show progress nhanh:

1. ✏️ **Thêm export biên bản ra Word có chèn ký số mock** (đã có ReportLab cho PDF, tận dụng `python-docx`)
2. 📊 **Trang thống kê** trên `/hop-khong-giay/thong-ke` (đã có route, cần wire data)
3. 🔔 **Badge số cuộc họp sắp tới** trên Sidebar
4. 📥 **Bulk download tất cả tài liệu cuộc họp** thành ZIP
5. 🎨 **Improve UX**: print biên bản trực tiếp từ trang chi tiết (CSS print stylesheet)
6. 🌐 **Dark mode toggle** (toàn platform, không chỉ HKG)

---

## 8. Rủi ro & Mitigation

| Rủi ro | Xác suất | Tác động | Mitigation |
|---|---|---|---|
| LibreOffice spike RAM khi 50+ user cùng xem Office docs | Trung | Cao (OOM) | Semaphore N=3 concurrent; queue request thừa |
| Mất file production do thao tác nhầm (như sự cố G4-fix-8) | Thấp (đã sandbox) | Cao | (1) `HKG_UPLOAD_DIR` ngoài repo, (2) backup daily, (3) rule "no rmtree path không có UUID/tmp prefix" |
| Mock CKS gây hiểu nhầm pháp lý | Trung | Cao | Thêm watermark **"BẢN NHÁP - KHÔNG CÓ GIÁ TRỊ PHÁP LÝ"** trên PDF mock; bullet rõ trong UI |
| 549 user UAT đồng loạt = service quá tải | Thấp | Trung | Đã test với load synthetic; giám sát metrics tuần đầu |
| Chu_toa/thu_ky quên giờ họp (không ai bấm bắt đầu) | Cao | Thấp | Email/SMS nhắc (P1) + auto-mark COMPLETED sau giờ kết thúc + 2h |
| Schema drift khi nhiều dev cùng sửa migrations | Trung | Cao | Quy tắc 1 migration/PR, review chéo, branch protection trên main |

---

## 9. Khuyến nghị cuối

**Triển khai P0 ngay (1-2 tuần tới)**: backup + monitoring + cleanup cache + rate limit. Đây là 4 việc rẻ nhưng tránh được 80% sự cố production thường gặp.

**Sau đó dồn lực vào P1.1 (CKS thật)** vì đây là blocker pháp lý — biên bản hiện tại tuy hoạt động kỹ thuật nhưng không có giá trị pháp lý chính thức. Nếu Chi cục bắt đầu dùng HKG thay biên bản giấy → cần CKS thật trước khi tháng đầu tiên kết thúc.

**P1.2 (PWA mobile)** nên làm song song vì impact lớn cho UX điểm danh — thấy rõ trong UAT.

Các P2/P3 ưu tiên theo demand thực tế, không cần roadmap cứng.

---

## 10. Phụ lục — Inventory MVP

### Backend endpoints (`backend/meeting_service/api/endpoints/`)
- `cuoc_hop.py` — 12 endpoints (CRUD + sửa thành phần + đổi trạng thái)
- `tai_lieu.py` — 7 endpoints (upload/list/view/download/delete/metadata + 2 file gateways)
- `diem_danh.py` — 6 endpoints (QR token, tự điểm danh, status, list, override, my_status)
- `xin_phep_vang.py` — 4 endpoints (request/approve/reject/list)
- `bien_ban.py` — 5 endpoints (CRUD + ký mock + export DOCX/PDF)
- `ket_luan.py` — 4 endpoints (CRUD + tiến độ thực hiện)
- `cong_chuc.py` — 1 endpoint (search CBCC theo đơn vị)

### Frontend pages (`frontend/src/app/(main)/hop-khong-giay/`)
- `page.tsx` — list cuộc họp + filter
- `tao-hop/` — wizard tạo cuộc họp
- `chi-tiet/[id]/` — 7 tabs: tổng quan / thành phần / tài liệu / điểm danh / ý kiến / biên bản / kết luận
- `diem-danh-qr/` — landing scan QR
- `xin-phep-vang/` — list + form xin phép
- `thong-ke/` — placeholder dashboard
- `xem-tai-lieu/` — preview wrapper iframe (mới — G4-fix-9)

### Database tables (schema `meeting`)
`cuoc_hop`, `thanh_phan`, `tai_lieu`, `diem_danh`, `xin_phep_vang`, `y_kien`, `bien_ban`, `ket_luan`, `tien_do`, `mau_bieu` (10 bảng)

### Tests
146 test cases trên 11 file (test_cuoc_hop, test_tai_lieu, test_bien_ban, test_diem_danh, test_checkin_window, test_cancelled_meeting, test_g4_fix_6, test_cong_chuc_search, test_xin_phep_vang, test_ket_luan, test_scheduler).

---

*Hết báo cáo. Liên hệ team backend qua `kv8haiquan@gmail.com` cho mọi câu hỏi triển khai.*
