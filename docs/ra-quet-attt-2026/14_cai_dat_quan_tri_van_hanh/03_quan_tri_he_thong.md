# 03 — Quản trị hệ thống

> Phục vụ công văn 153/CNTT ngày 08/7/2026 — Mục 14.3.
> Lập ngày 06/10/2026.

## 1. Quản trị tài khoản người dùng và phân quyền

### 1.1. Nguồn tài khoản

Tài khoản người dùng lưu trong bảng `public.cong_chuc` (558 tài khoản hiện tại), đồng bộ theo danh sách công chức của Phòng TCCB.

| Trường | Ý nghĩa | Lưu ý |
|--------|---------|-------|
| `id` | UUID (khóa chính) | Duy nhất, không đổi |
| `ma_cc` | Mã công chức (username) | VD: `20ZZ-xxxx`, duy nhất |
| `ho_ten` | Họ tên | Có thể trùng → phân biệt bằng `ma_cc` |
| `email` | Email | Có thể null |
| `so_dien_thoai` | Số điện thoại | Có thể null, dùng cho Zalo OA |
| `don_vi_id` | Đơn vị hiện tại | FK → `public.don_vi(id)` |
| `vai_tro_id` | Vai trò chính | FK → `public.vai_tro(id)` |
| `is_lanh_dao` | Là lãnh đạo hay không | Boolean |
| `is_active` | Tài khoản còn hoạt động | Boolean, `false` = khóa |
| `is_deleted` | Đã xóa mềm | Boolean, KHÔNG xóa vật lý |
| `password_hash` | Mật khẩu (bcrypt) | Hash bcrypt, KHÔNG lưu plaintext |

### 1.2. Vai trò (RBAC 2 lớp)

#### Lớp 1 — Vai trò chính (bảng `public.vai_tro`, 9 vai trò)

| Mã | Vai trò | Quyền chính |
|---|---|---|
| `CCT` | Chi cục trưởng | Duyệt cuối, xếp loại toàn Chi cục, điều chỉnh kết quả |
| `PCCT` | Phó Chi cục trưởng | Duyệt/đánh giá khối phụ trách |
| `TDV` | Trưởng đơn vị | Duyệt kê khai, đánh giá công chức trong đơn vị |
| `PDV` | Phó đơn vị | Duyệt kê khai trong phạm vi phân công |
| `QLDV` | Quản lý đơn vị | Quản lý nghiệp vụ đơn vị |
| `CC` | Công chức | Kê khai công việc, xem kết quả của mình |
| `HD_111` | Hợp đồng 111 | Kê khai (phạm vi hạn chế) |
| `TCCB` | Cán bộ Tổ chức | Tổng hợp, đối soát, báo cáo toàn Chi cục |
| `ADMIN` | Quản trị hệ thống | Quản lý tài khoản, danh mục, cấu hình |

#### Lớp 2 — Vai trò nền tảng (bảng `public.platform_role`, 15 vai trò)

Bảng liên kết: `public.cong_chuc_platform_role` (nhiều-nhiều).

Một số vai trò quan trọng:

| Mã | Module | Mục đích |
|---|---|---|
| `GIANG_VIEN` | LMS | Giảng viên kiêm nhiệm, tạo khóa học |
| `QT_DAO_TAO` | LMS | Quản trị đào tạo, tạo kỳ thi ĐGNL |
| `THU_KY_HOP` | HKG | Tạo cuộc họp, quản lý tài liệu |
| `CHANH_VP` | HKG | Toàn quyền HKG |
| `QT_NOI_DUNG` | Portal | Quản trị nội dung Portal |
| `QT_ATTT` | ALL | Quản trị an toàn thông tin |
| `QT_CHI_TIEU` | Chỉ tiêu | Quản trị chỉ tiêu đơn vị |

**Nguyên tắc:** Kiểm tra quyền tại **backend** (dependency `get_current_user` + kiểm tra vai trò/đơn vị), frontend chỉ ẩn/hiện UI.

### 1.3. Tạo tài khoản mới

#### Cách 1: Import từ Excel (hàng loạt)

```bash
cd /opt/kpi-prod/backend
source venv/bin/activate

# Chuẩn bị file Excel theo mẫu:
# - Sheet "Công chức": ma_cc, ho_ten, email, so_dien_thoai, ma_don_vi, ma_vai_tro, is_lanh_dao
# - Đặt tại backend/data/cong_chuc.xlsx

python scripts/seed_users.py

# Kiểm tra
python scripts/verify_import.py
```

Mật khẩu mặc định: `123456` (bcrypt hash).

#### Cách 2: SQL thủ công (phương án khẩn cấp)

⚠️ **CHỈ sử dụng khi giao diện không khả dụng**. Database tại `localhost:5432` CHÍNH LÀ PRODUCTION đang phục vụ người dùng thật. **BẮT BUỘC:**
- Thử trên DB test `kpi_haiquan_test` trước
- Bọc trong transaction `BEGIN...COMMIT`
- Kiểm tra số dòng ảnh hưởng trước khi COMMIT
- Không đặt mật khẩu `123456` — đây là khoảng trống bảo mật (chưa có tính năng must_change_password)

```sql
BEGIN;

-- Lấy UUID đơn vị và vai trò
SELECT id, ten_don_vi FROM don_vi WHERE ma_don_vi = 'DV01';
SELECT id, ma_vai_tro FROM vai_tro WHERE ma_vai_tro = 'CC';

-- Sinh hash bcrypt cho mật khẩu
-- (chạy bằng Python TRƯỚC KHI vào psql)
-- from passlib.context import CryptContext
-- pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
-- print(pwd_context.hash("<mật-khẩu-an-toàn>"))

-- Tạo tài khoản
INSERT INTO cong_chuc (
    id, ma_cc, ho_ten, email, so_dien_thoai,
    don_vi_id, vai_tro_id, is_lanh_dao, is_active,
    username, password_hash
) VALUES (
    gen_random_uuid(),
    '20ZZ-xxxx',
    'Họ Tên (ví dụ)',
    'email@example.com',
    '<so-dien-thoai>',
    '<uuid-don-vi>',
    '<uuid-vai-tro>',
    false,
    true,
    '20zz-xxxx',
    '<bcrypt-hash-vừa-sinh>'
);

-- Kiểm tra số dòng
SELECT COUNT(*) FROM cong_chuc WHERE ma_cc = '20ZZ-xxxx';
-- Phải ra: 1

-- Nếu đúng, COMMIT; nếu sai, ROLLBACK
COMMIT;
-- ROLLBACK;
```

### 1.4. Gán vai trò nền tảng (platform role)

#### Cách 1: Qua giao diện Admin (khuyến nghị)

Giao diện: **chưa có màn hình quản trị chung cho vai trò nền tảng** (kiểm tra `/opt/kpi-prod/frontend/src/app/(main)/admin` ngày 06/10/2026). Ngoại lệ duy nhất: vai trò theo dõi chỉ tiêu được gán qua chức năng "người theo dõi" của module Chỉ tiêu (`chi_tieu_service/services/nguoi_theo_doi_service.py`). Các vai trò còn lại hiện gán bằng SQL theo quy trình khẩn cấp dưới đây — đây là **khoảng trống quản trị đã ghi nhận** (đề xuất bổ sung màn hình gán vai trò có ghi nhật ký).

#### Cách 2: SQL thủ công (phương án khẩn cấp)

⚠️ **CHỈ sử dụng khi giao diện không khả dụng**. Xem cảnh báo mục 1.3.

```sql
BEGIN;

-- Lấy UUID công chức
SELECT id, ma_cc, ho_ten FROM cong_chuc WHERE ma_cc = '20ZZ-xxxx';

-- Lấy ID vai trò nền tảng
SELECT id, ma_role, ten_role FROM platform_role WHERE ma_role = 'GIANG_VIEN';

-- Gán vai trò (kiểm tra chưa tồn tại)
INSERT INTO cong_chuc_platform_role (cong_chuc_id, platform_role_id, is_active)
VALUES ('<uuid-cong-chuc>', '<id-platform-role>', true)
ON CONFLICT (cong_chuc_id, platform_role_id) DO NOTHING;

-- Kiểm tra
SELECT COUNT(*) FROM cong_chuc_platform_role 
WHERE cong_chuc_id = '<uuid-cong-chuc>' AND platform_role_id = '<id-platform-role>';
-- Phải ra: 1

COMMIT;
-- ROLLBACK;
```

**Lưu ý:** Người dùng phải **đăng nhập lại** để JWT mới chứa `platform_roles` (trường này có trong token từ 23/02/2026 — commit 321244e, xem `backend/app/api/v1/endpoints/auth.py` dòng 252-262).

### 1.5. Reset mật khẩu

#### Cách 1: Qua giao diện Admin (khuyến nghị)

Giao diện: **Admin → Quản lý người dùng** → chọn công chức → nút **Reset mật khẩu**.

Endpoint: `PUT /api/v1/admin/users/{user_id}/reset-password`

Yêu cầu vai trò: `ADMIN` hoặc `TCCB`.

Mật khẩu sau khi reset: `123456` (người dùng nên đổi ngay).

#### Cách 2: SQL thủ công (phương án khẩn cấp)

⚠️ **CHỈ sử dụng khi giao diện không khả dụng**. Xem cảnh báo mục 1.3.

```python
# Sinh hash mới (chạy TRƯỚC KHI vào psql)
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
new_hash = pwd_context.hash("<mật-khẩu-an-toàn>")
print(new_hash)
```

```sql
BEGIN;

-- Kiểm tra tài khoản tồn tại và không phải ADMIN-001
SELECT ma_cc, ho_ten, is_active FROM cong_chuc WHERE ma_cc = '20ZZ-xxxx';
-- KHÔNG reset password cho 'ADMIN-001'

-- Cập nhật mật khẩu
UPDATE cong_chuc
SET password_hash = '<bcrypt-hash-vừa-sinh>'
WHERE ma_cc = '20ZZ-xxxx';

-- Kiểm tra số dòng ảnh hưởng
-- Phải ra: 1 row affected

COMMIT;
-- ROLLBACK;
```

### 1.6. Khóa tài khoản

#### Cách 1: Qua giao diện Admin (khuyến nghị)

Giao diện: **Admin → Quản lý người dùng** → chọn công chức → toggle **Trạng thái hoạt động**.

#### Cách 2: SQL thủ công (phương án khẩn cấp)

⚠️ **CHỈ sử dụng khi giao diện không khả dụng**. Xem cảnh báo mục 1.3.

```sql
BEGIN;

-- Khóa (vô hiệu hóa)
UPDATE cong_chuc SET is_active = false WHERE ma_cc = '20ZZ-xxxx';
-- Kiểm tra: 1 row affected

-- Mở khóa
UPDATE cong_chuc SET is_active = true WHERE ma_cc = '20ZZ-xxxx';
-- Kiểm tra: 1 row affected

COMMIT;
-- ROLLBACK;
```

**Không xóa vật lý** (không `DELETE`) vì cần giữ lịch sử đánh giá, kê khai. Chức năng xóa hoàn toàn nằm trong giao diện Admin với nhiều bước kiểm tra (xem endpoint `DELETE /api/v1/users/{user_id}` trong `admin.py` dòng 676-837).

### 1.7. Vô hiệu hóa có ngày hiệu lực

Từ tính năng mở rộng, bảng `lich_su_dieu_chuyen` có cột `loai`:

- `DIEU_CHUYEN` — điều chuyển đơn vị (endpoint PUT `/api/v1/admin/users/{user_id}/transfer`)
- `VO_HIEU_HOA` — vô hiệu hóa (nghỉ việc, chuyển công tác)
- `KICH_HOAT` — kích hoạt lại

#### Cách 1: Qua giao diện Admin (khuyến nghị)

Giao diện: **Admin → Quản lý người dùng** → chọn công chức → nút **Điều chuyển** → chọn loại `Vô hiệu hóa` → nhập ngày hiệu lực.

#### Cách 2: SQL thủ công (phương án khẩn cấp)

⚠️ **CHỈ sử dụng khi giao diện không khả dụng**. Xem cảnh báo mục 1.3.

```sql
BEGIN;

-- Lấy UUID
SELECT id FROM cong_chuc WHERE ma_cc = '20ZZ-xxxx';
SELECT id FROM cong_chuc WHERE ma_cc = 'ADMIN-001';  -- người thực hiện

-- Vô hiệu hóa từ ngày cụ thể
INSERT INTO lich_su_dieu_chuyen (
    cong_chuc_id, loai, ngay_hieu_luc, ly_do, nguoi_thuc_hien_id,
    don_vi_cu_id, don_vi_moi_id
) VALUES (
    '<uuid-cong-chuc>',
    'VO_HIEU_HOA',
    '2026-10-15',
    'Chuyển công tác / Nghỉ việc',
    '<uuid-admin>',
    '<uuid-don-vi-hien-tai>',  -- giữ nguyên đơn vị
    '<uuid-don-vi-hien-tai>'
);

-- Kiểm tra số dòng
SELECT COUNT(*) FROM lich_su_dieu_chuyen WHERE cong_chuc_id = '<uuid-cong-chuc>' AND loai = 'VO_HIEU_HOA';

COMMIT;
-- ROLLBACK;
```

**Cơ chế:** Sau `ngay_hieu_luc`, công chức không thể đăng nhập (logic kiểm tra trong `app/api/deps.py` hàm `_active_tai_thang_expr`).

---

## 2. Quản trị danh mục

### 2.1. Danh mục quan trọng

| Bảng | Ý nghĩa | Ai chỉnh sửa |
|------|---------|--------------|
| `don_vi` | 15 đơn vị (Phòng/Đội/HQCK) | ADMIN, TCCB |
| `vai_tro` | 9 vai trò chính | ADMIN (hiếm khi đổi) |
| `platform_role` | 15 vai trò nền tảng | ADMIN |
| `danh_muc_sp_cong_viec` | Danh mục sản phẩm công việc | ADMIN, CCT |
| `tieu_chi_chung` | Tiêu chí chung (đánh giá tháng) | ADMIN, CCT |
| `lms.khoa_hoc` | Khóa học LMS | GIANG_VIEN, QT_DAO_TAO |
| `legal.linh_vuc` | Lĩnh vực pháp luật | QT_NOI_DUNG |

### 2.2. Sửa danh mục

**Khuyến nghị:** Qua giao diện Admin (nếu có) hoặc endpoint API tương ứng.

**Thủ công qua SQL:** Phương án khẩn cấp khi giao diện không khả dụng. **BẮT BUỘC:**
- Database `localhost:5432` là production — thử trên `kpi_haiquan_test` trước
- Bọc trong transaction `BEGIN...COMMIT`
- Kiểm tra ràng buộc FK trước khi xóa
- Kiểm tra số dòng ảnh hưởng trước khi COMMIT

Ví dụ sửa tên đơn vị:

```sql
BEGIN;

-- Kiểm tra trước khi sửa
SELECT id, ma_don_vi, ten_don_vi FROM don_vi WHERE ma_don_vi = 'DV01';

-- Cập nhật
UPDATE don_vi
SET ten_don_vi = 'Đội Nghiệp vụ 1 (tên mới)'
WHERE ma_don_vi = 'DV01';
-- Kiểm tra: 1 row affected

-- Kiểm tra không ảnh hưởng đến dữ liệu khác
SELECT COUNT(*) FROM cong_chuc WHERE don_vi_id = (SELECT id FROM don_vi WHERE ma_don_vi = 'DV01');
-- Số công chức thuộc đơn vị này (không đổi)

-- Nếu đúng, COMMIT; nếu sai, ROLLBACK
COMMIT;
-- ROLLBACK;
```

---

## 3. Quản lý tiến trình PM2

### 3.1. Danh sách lệnh PM2

```bash
# Xem trạng thái
pm2 list
pm2 jlist                      # JSON format
pm2 prettylist                 # Format dễ đọc

# Xem log
pm2 logs                       # Tất cả
pm2 logs kpi-backend           # Một service
pm2 logs --lines 100           # 100 dòng cuối
pm2 logs --err                 # Chỉ stderr
pm2 flush                      # Xóa log cũ

# Restart/Reload
pm2 restart kpi-backend
pm2 reload kpi-backend         # Graceful restart (zero-downtime)
pm2 restart all
pm2 reload all --update-env    # Reload + nạp lại biến môi trường

# Stop/Start
pm2 stop kpi-backend
pm2 start kpi-backend

# Delete (xóa khỏi danh sách PM2)
pm2 delete kpi-backend
pm2 delete all

# Save/Restore
pm2 save                       # Lưu danh sách hiện tại
pm2 resurrect                  # Khôi phục danh sách đã lưu

# Thông tin chi tiết
pm2 describe kpi-backend
pm2 monit                      # Real-time CPU/RAM monitor
```

### 3.2. Thêm process mới

```bash
cd /opt/kpi-prod/backend

pm2 start venv/bin/uvicorn --name <tên-service> \
  --interpreter none \
  -- <module>.main:app --host 127.0.0.1 --port <port>

# Ví dụ:
pm2 start venv/bin/uvicorn --name new-backend \
  --interpreter none \
  -- new_service.main:app --host 127.0.0.1 --port 8008

pm2 save
```

### 3.3. Xóa process

```bash
pm2 delete <tên-service>
pm2 save
```

### 3.4. Kiểm tra lỗi

```bash
# Log lỗi
pm2 logs <tên-service> --err --lines 200

# Xem trạng thái chi tiết
pm2 describe <tên-service>

# Nếu service restart liên tục (status: errored)
pm2 logs <tên-service> --lines 50
# Thường là lỗi: port đã dùng, .env sai, DB không kết nối được
```

### 3.5. Update biến môi trường

```bash
# Sửa file .env
vim /opt/kpi-prod/backend/.env

# Reload với --update-env
pm2 reload kpi-backend --update-env

# Hoặc restart (mất kết nối tạm thời)
pm2 restart kpi-backend
```

---

## 4. Quy trình phát hành phiên bản (Deployment)

### 4.1. Tổng quan

Production chạy từ `/opt/kpi-prod` (git worktree nhánh `prod`). Phát hành bằng script `/opt/kpi-prod/backend/scripts/trien_khai.sh <SHA|tag>`.

**Thứ tự BẮT BUỘC:** lấy code → cài thư viện → **CHẠY MIGRATION** → build frontend → reload PM2.

### 4.2. Các bước chi tiết

#### Bước 1: Hoàn tất ở môi trường Dev

```bash
cd /root/kpi-haiquan

# Chạy test
./backend/scripts/dev.sh test <thư mục test>

# Commit code
git add <file cụ thể>    # KHÔNG dùng git add -A
git commit
git push origin <nhánh-feature>
```

#### Bước 2: Kiểm tra nhánh feature có up-to-date với prod không

```bash
cd /root/kpi-haiquan
git fetch origin

# Kiểm tra có commit nào giữa feature và prod không
git log --oneline <nhánh-feature>..origin/prod

# Nếu KHÔNG RỖNG → phải rebase trước khi triển khai
git rebase origin/prod
git push --force-with-lease origin <nhánh-feature>
```

**Lý do:** Nếu triển khai nhánh cũ hơn `prod`, sẽ **LÙI production** về trạng thái cũ, mất code đã phát hành.

#### Bước 3: Chạy script triển khai

```bash
# Lấy SHA của commit muốn triển khai
cd /root/kpi-haiquan
git log --oneline -1 <nhánh-feature>
# Hoặc: git rev-parse <nhánh-feature>

# Chạy trien_khai.sh với SHA (KHÔNG truyền tên nhánh)
/opt/kpi-prod/backend/scripts/trien_khai.sh <SHA>
```

Script sẽ:
1. Kiểm tra có ai đang thi ĐGNL không (chặn nếu có)
2. Ghi lệnh quay lui (để copy ngay nếu cần)
3. `git checkout <SHA>`
4. Cài thư viện nếu `requirements.txt` hoặc `package-lock.json` đổi
5. **Chạy migration** (`alembic upgrade head`)
6. Build frontend nếu thư mục `frontend/` đổi (qua `build_frontend.sh` có giới hạn RAM)
7. `pm2 reload` tất cả backend services + frontend
8. Kiểm tra `/health` từng service (8000-8007)
9. **Dời nhánh `prod` về commit vừa triển khai** và `git checkout prod` (thoát detached HEAD)

Nếu có service không lên, script **dừng ngay** và in lệnh quay lui.

#### Bước 4: Đẩy nhánh prod lên remote

Script KHÔNG tự push. Phải chạy tay:

```bash
cd /opt/kpi-prod
git push origin prod

# Fast-forward main theo prod (KHÔNG tạo commit mới)
cd /root/kpi-haiquan
git branch -f main prod
git push origin main
```

#### Bước 5: Cập nhật tài liệu

```bash
vim /root/kpi-haiquan/docs/van-hanh/PHIEN_BAN_PROD.md
# Ghi: ngày, commit SHA, nội dung thay đổi
git add docs/van-hanh/PHIEN_BAN_PROD.md
git commit -m "docs(van-hanh): ghi mốc prod <SHA> — <mô tả>"
git push origin main
```

### 4.3. Kiểm tra sau khi triển khai

```bash
# 1. Kiểm tra nhánh prod khớp commit
cd /opt/kpi-prod
git status -sb | head -1
# Phải ra: ## prod...origin/prod (SAU khi push)

# 2. Kiểm tra PM2
pm2 list
# Tất cả phải ở trạng thái "online"

# 3. Kiểm tra log
pm2 logs --lines 50

# 4. Thử đăng nhập qua trình duyệt
curl -I https://kpihaiquan.vn
```

### 4.4. Xử lý khi có lỗi

Nếu service không lên sau triển khai:

```bash
# Xem log lỗi
pm2 logs <tên-service> --err --lines 100

# Quay lui ngay
/opt/kpi-prod/backend/scripts/trien_khai.sh <SHA-trước-đó>
```

Lệnh quay lui đã được script in ra ở đầu. Ví dụ:

```
[19:30:12] Quay lui  : /opt/kpi-prod/backend/scripts/trien_khai.sh a1b2c3d
```

### 4.5. Lưu ý quan trọng

⚠️ **LUÔN truyền SHA, KHÔNG truyền tên nhánh** cho `trien_khai.sh`. Lý do: biết chính xác commit nào đang chạy, tránh deploy nhầm HEAD của nhánh đang phát triển.

⚠️ **Migration chạy TRƯỚC code mới.** Sự cố 18/08/2026: code mới tham chiếu cột chưa tồn tại → cả module HKG ngừng hoạt động. Script đã ép đúng thứ tự.

⚠️ **Không build khi có người thi.** Script kiểm tra `kiem_tra_ky_thi.sh` trước cả `git checkout`. Bypass (CHỈ khi cần gấp):

```bash
BO_QUA_KIEM_TRA_KY_THI=1 /opt/kpi-prod/backend/scripts/trien_khai.sh <SHA>
```

⚠️ **Quay lui code KHÔNG tự quay lui migration.** Migration thêm cột/bảng thì code cũ vẫn chạy (cột thừa không sao). Nhưng migration XÓA/ĐỔI TÊN cột thì phải `alembic downgrade` thủ công.

---

## 5. Quay lui phiên bản (Rollback)

### 5.1. Quay lui code

```bash
# Lấy SHA của commit trước đó (từ PHIEN_BAN_PROD.md hoặc git log)
git -C /opt/kpi-prod log --oneline -10

# Quay lui
/opt/kpi-prod/backend/scripts/trien_khai.sh <SHA-cũ>
```

### 5.2. Quay lui migration (nếu cần)

⚠️ **Chỉ khi migration mới XÓA hoặc ĐỔI TÊN cột.**

```bash
cd /opt/kpi-prod/backend
source venv/bin/activate

# Xem lịch sử migration
alembic history

# Downgrade về revision cụ thể
alembic downgrade <revision-id>

# Hoặc downgrade 1 bước
alembic downgrade -1
```

**Lưu ý:** Migration `downgrade` PHẢI được test trước trên DB test. Không có sao lưu trước downgrade = mất dữ liệu.

### 5.3. Quay lui bằng restore database

Trường hợp khẩn cấp (migration hỏng dữ liệu):

```bash
# 1. Lấy bản backup gần nhất
ls -lht /var/backup/kpi_haiquan/daily/ | head -5

# 2. Dừng tất cả backend
pm2 stop all

# 3. Restore (xem chi tiết tại 04_quan_tri_csdl.md mục 4)
sudo -u postgres psql -c "DROP DATABASE kpi_haiquan;"
sudo -u postgres psql -c "CREATE DATABASE kpi_haiquan OWNER kpi_user;"
gunzip -c /var/backup/kpi_haiquan/daily/db_*.sql.gz | sudo -u postgres psql -d kpi_haiquan

# 4. Khởi động lại
pm2 restart all
```

---

## 6. Xóa nhánh feature sau khi đã lên prod

```bash
cd /root/kpi-haiquan

# Kiểm tra nhánh đã merge vào prod chưa
git fetch --prune
git branch --merged prod | grep -vE '^\*|^\s*(main|prod|auto-backup)$'

# Xóa nhánh local
git branch -d <tên-nhánh>

# Xóa nhánh remote
git push origin --delete <tên-nhánh>
```

Nhánh **chưa** vào prod mà muốn bỏ: gắn tag lưu trữ trước, nếu không commit sẽ mồ côi và bị GC dọn mất.

```bash
git tag -a attic/<tên>-<YYYYMMDD> <nhánh> -m "lý do bỏ"
git push origin attic/<tên>-<YYYYMMDD>
git branch -D <nhánh>
git push origin --delete <nhánh>
```

---

## 7. Kiểm tra sức khỏe hệ thống

### 7.1. Các lệnh kiểm tra nhanh

```bash
# Trạng thái PM2
pm2 list

# Disk space
df -h

# RAM usage
free -h

# Trạng thái PostgreSQL
systemctl status postgresql

# Trạng thái nginx
systemctl status nginx
nginx -t

# Trạng thái cron backup
tail -20 /var/log/backup_kpi.log
```

### 7.2. Kiểm tra endpoint health

```bash
# Backend
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
  echo -n "Port $port: "
  curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health
  echo
done

# Frontend
curl -I http://localhost:3000

# HTTPS public
curl -I https://kpihaiquan.vn
```

### 7.3. Kiểm tra log lỗi

```bash
# PM2 errors
pm2 logs --err --lines 100

# nginx errors
tail -50 /var/log/nginx/error.log

# PostgreSQL errors
sudo tail -50 /var/log/postgresql/postgresql-15-main.log
```

---

## 8. Tham khảo

- `docs/van-hanh/HUONG_DAN_DEV_PROD.md` — Quy trình Dev/Prod chi tiết
- `docs/van-hanh/PHIEN_BAN_PROD.md` — Lịch sử phát hành
- `/opt/kpi-prod/backend/scripts/trien_khai.sh` — Script triển khai
- Memory `project_deploy_prod_worktree.md` — Bài học detached HEAD
- `docs/ra-quet-attt-2026/07_tai_khoan_phan_quyen_nhat_ky.md` — Phân quyền chi tiết
