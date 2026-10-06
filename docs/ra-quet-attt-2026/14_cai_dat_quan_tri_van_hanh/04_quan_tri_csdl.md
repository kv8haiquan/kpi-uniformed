# 04 — Quản trị cơ sở dữ liệu

> Phục vụ công văn 153/CNTT ngày 08/7/2026 — Mục 14.4.
> Lập ngày 06/10/2026.

## 1. Cấu trúc database và schema

### 1.1. Thông tin cơ bản

| Hạng mục | Giá trị |
|----------|---------|
| DBMS | PostgreSQL 15.16 |
| Database | `kpi_haiquan` |
| Kích thước | ~170 MB |
| Số schema | 8 (public, lms, forum, legal, portal, common, meeting, chi_tieu) |
| Số bảng | 96 bảng |
| Truy cập | localhost:5432, KHÔNG mở ra Internet |
| Encoding | UTF8 |
| Timezone | Asia/Ho_Chi_Minh |

### 1.2. Phân bố schema

| Schema | Owner | Module | Số bảng | Bảng quan trọng |
|--------|-------|--------|---------|-----------------|
| `public` | **kpi_user** / postgres | KPI + Platform | 37 | `cong_chuc` (558), `ke_khai_cong_viec` (44.552), `danh_gia_thang` (2.614), `tieu_chi_chung_danh_gia` (26.020) |
| `lms` | postgres | Đào tạo | 20 | `khoa_hoc`, `cau_hoi_dgnl`, `ky_thi`, `thi_sinh`, `ket_qua_bai_kiem_tra` |
| `forum` | kpi_user | Diễn đàn | 5 | `chu_de`, `binh_luan` |
| `legal` | postgres | Pháp luật | 6 | `van_ban`, `linh_vuc` |
| `portal` | postgres | Portal/CMS | 5 | `bai_viet`, `chuyen_muc` |
| `common` | kpi_user | Dùng chung | 5 | `thong_bao`, `tap_tin` |
| `meeting` | kpi_user | Họp Không Giấy | 13 | `cuoc_hop`, `tai_lieu`, `y_kien` |
| `chi_tieu` | kpi_user | Chỉ tiêu đơn vị | 5 | `danh_muc_chi_tieu`, `giao_nam`, `dang_ky_thang` |

**Nguyên tắc:** Module mới **CHỈ ĐỌC** (`SELECT`) bảng `public.cong_chuc`, `public.don_vi`, `public.vai_tro`. Mọi bảng nghiệp vụ mới nằm trong schema riêng, FK trực tiếp về `public.cong_chuc(id)`.

### 1.3. ⚠️ Vấn đề owner bảng trong schema public

**Hiện trạng:** 17/37 bảng trong schema `public` thuộc owner `postgres` thay vì `kpi_user`. Ví dụ:

```
public.alembic_version         → postgres
public.audit_log               → postgres
public.bao_cao_xep_loai        → postgres
public.cong_chuc_platform_role → postgres
public.vai_tro                 → postgres
...
```

**Hậu quả:** Khi chạy Alembic migration bằng user `kpi_user`, gặp lỗi:

```
sqlalchemy.exc.InsufficientPrivilege: (psycopg2.errors.InsufficientPrivilege)
must be owner of table <tên-bảng>
```

**Nguyên nhân:** Các bảng này được tạo bởi migration chạy bằng superuser `postgres` trong quá khứ.

**Giải pháp:** Chuyển owner về `kpi_user` trước khi chạy migration:

```sql
-- Chuyển owner từng bảng
ALTER TABLE public.alembic_version OWNER TO kpi_user;
ALTER TABLE public.audit_log OWNER TO kpi_user;
ALTER TABLE public.bao_cao_xep_loai OWNER TO kpi_user;
ALTER TABLE public.cong_chuc_platform_role OWNER TO kpi_user;
ALTER TABLE public.vai_tro OWNER TO kpi_user;
-- ... (tất cả bảng thuộc postgres)

-- Hoặc script tự động (chạy bằng superuser)
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' AND tableowner = 'postgres'
    LOOP
        EXECUTE 'ALTER TABLE public.' || quote_ident(r.tablename) || ' OWNER TO kpi_user';
    END LOOP;
END $$;
```

**Kiểm tra:**

```sql
SELECT tablename, tableowner 
FROM pg_tables 
WHERE schemaname = 'public' AND tableowner = 'postgres';
-- Phải trả về 0 rows
```


---

## 2. Tài khoản và quyền

### 2.1. User PostgreSQL

| User | Vai trò | Quyền | Dùng cho |
|------|---------|-------|----------|
| `postgres` | Superuser | Toàn quyền | Cài đặt extension, ALTER OWNER, backup/restore |
| `kpi_user` | Ứng dụng | CRUD trên schema riêng + SELECT bảng public | Ứng dụng backend (8 services) |

**KHÔNG dùng superuser `postgres` cho ứng dụng.** Chỉ dùng `kpi_user`.

### 2.2. Tạo user mới (nếu cần)

```sql
-- Tạo user
CREATE USER new_user WITH PASSWORD '<mật-khẩu>';

-- Cấp quyền kết nối database
GRANT CONNECT ON DATABASE kpi_haiquan TO new_user;

-- Cấp quyền trên schema
GRANT USAGE ON SCHEMA public TO new_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO new_user;

-- Cấp quyền insert/update/delete trên schema riêng (nếu cần)
GRANT ALL ON SCHEMA lms TO new_user;
GRANT ALL ON ALL TABLES IN SCHEMA lms TO new_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA lms TO new_user;
```

### 2.3. Đổi mật khẩu user

```sql
ALTER USER kpi_user WITH PASSWORD '<mật-khẩu-mới>';
```

Sau khi đổi, phải cập nhật file `.env` và restart backend.

### 2.4. Kiểm tra quyền

```sql
-- Xem danh sách user
\du

-- Xem quyền trên database
\l+ kpi_haiquan

-- Xem quyền trên schema
\dn+ public

-- Xem quyền trên bảng cụ thể
\dp public.cong_chuc
```

---

## 3. Migration (Alembic)

### 3.1. Cấu trúc migration

- File cấu hình: `backend/alembic.ini`
- Thư mục migrations: `backend/alembic/versions/`
- Chuỗi revision: **tuyến tính qua mọi module** (kpi, lms, zalo, meeting, chi_tieu...)

**Quan trọng:** `down_revision` phải là head thật (revision cuối cùng), không phải revision cuối của module mình.

### 3.2. Kiểm tra trạng thái migration

```bash
cd /opt/kpi-prod/backend
source venv/bin/activate

# Xem revision hiện tại
alembic current

# Xem lịch sử migration
alembic history

# Xem các revision chưa apply
alembic heads
```

### 3.3. Chạy migration

⚠️ **BẮT BUỘC chạy từ `/opt/kpi-prod/backend`**, không phải từ cây dev.

```bash
cd /opt/kpi-prod/backend
source venv/bin/activate

# Upgrade lên revision mới nhất
alembic upgrade head

# Upgrade lên revision cụ thể
alembic upgrade <revision-id>

# Upgrade 1 bước
alembic upgrade +1
```

**Lưu ý:** Migration tự chạy khi khởi động KPI backend (`app/main.py`), NHƯNG các service khác (lms, meeting, chi_tieu...) KHÔNG tự chạy — phải chạy thủ công.

### 3.4. Tạo migration mới

```bash
cd /root/kpi-haiquan/backend
source venv/bin/activate

# Sau khi thay đổi models
alembic revision --autogenerate -m "mô tả ngắn gọn"

# Kiểm tra file migration vừa tạo
ls -lt alembic/versions/ | head -5
vim alembic/versions/<revision-id>_<mô-tả>.py
```

**Kiểm tra kỹ trước khi apply:**
- `upgrade()` và `downgrade()` đầy đủ
- Cột mới có `nullable=True` hoặc `server_default` (nếu bảng đã có dữ liệu)
- Không xóa cột đang dùng mà chưa remove khỏi code
- Index/FK được tạo đúng

### 3.5. Rollback migration (downgrade)

⚠️ **CHỈ khi migration XÓA hoặc ĐỔI TÊN cột.** Migration thêm cột/bảng thì code cũ vẫn chạy (cột thừa không sao).

```bash
cd /opt/kpi-prod/backend
source venv/bin/activate

# Downgrade về revision cụ thể
alembic downgrade <revision-id>

# Downgrade 1 bước
alembic downgrade -1
```

**PHẢI test trên DB test trước.** Downgrade trên prod mà không sao lưu = mất dữ liệu.

### 3.6. Xử lý lỗi migration

#### Lỗi: "Target database is not up to date"

```bash
alembic stamp head
```

#### Lỗi: "Can't locate revision"

Nguyên nhân: `alembic_version` chứa revision id không có trong `alembic/versions/`.

Giải pháp:

```sql
-- Xem revision hiện tại
SELECT * FROM alembic_version;

-- Sửa về revision gần nhất (biết chắc là đúng)
UPDATE alembic_version SET version_num = '<revision-id>';
```

Hoặc drop và chạy lại:

```sql
DROP TABLE alembic_version;
-- Rồi: alembic stamp <revision-id>
```

#### Lỗi: "ENUM type already exists"

```sql
DROP TYPE <tên-enum-type> CASCADE;
-- Rồi chạy lại migration
```

---

## 4. Backup và Restore

### 4.1. Phương án backup tự động

Xem chi tiết: `02_cau_hinh.md` mục 4.

**Tóm tắt:**
- 02:00 + 14:00 hằng ngày — `pg_dump` + rsync uploads
- Lưu tại `/var/backup/kpi_haiquan/daily/` (30 ngày) và `monthly/` (400 ngày)
- Bản off-site: đẩy lên GitHub private (đã mã hóa AES256), giữ 14 bản

### 4.2. Backup thủ công (trước migration quan trọng)

```bash
# Tạo tên file rõ ràng
OUT=/var/backup/kpi_haiquan/daily/db_premig_<mô-tả>_$(date +%Y%m%d_%H%M%S).sql.gz

# Dump bằng superuser postgres
sudo -u postgres pg_dump kpi_haiquan | gzip > "$OUT"

# Kiểm tra toàn vẹn file nén
gzip -t "$OUT" && echo "OK" || echo "FAILED"

# Kiểm tra kích thước
ls -lh "$OUT"
```

### 4.3. Restore database

#### Bước 1: Chọn bản backup

```bash
# Liệt kê bản backup gần nhất
ls -lht /var/backup/kpi_haiquan/daily/ | head -10
```

#### Bước 2: Restore vào DB tạm để kiểm tra

```bash
# Tạo DB tạm
sudo -u postgres psql -c "DROP DATABASE IF EXISTS kpi_haiquan_restore;"
sudo -u postgres psql -c "CREATE DATABASE kpi_haiquan_restore OWNER kpi_user;"

# Restore
gunzip -c /var/backup/kpi_haiquan/daily/db_<file>.sql.gz | sudo -u postgres psql -d kpi_haiquan_restore

# Kiểm tra dữ liệu
sudo -u postgres psql -d kpi_haiquan_restore -c "SELECT COUNT(*) FROM cong_chuc;"
sudo -u postgres psql -d kpi_haiquan_restore -c "SELECT MAX(created_at) FROM ke_khai_cong_viec;"
```

#### Bước 3: Swap database (nếu đã kiểm tra OK)

```bash
# Dừng tất cả backend
pm2 stop all

# Rename database
sudo -u postgres psql <<EOF
ALTER DATABASE kpi_haiquan RENAME TO kpi_haiquan_old;
ALTER DATABASE kpi_haiquan_restore RENAME TO kpi_haiquan;
EOF

# Khởi động lại
pm2 restart all

# Kiểm tra
curl http://localhost:8000/health
```

#### Bước 4: Cleanup (sau khi chạy ổn định)

```bash
# Xóa DB cũ (sau vài ngày chạy ổn)
sudo -u postgres psql -c "DROP DATABASE kpi_haiquan_old;"
```

### 4.4. Restore uploads (file đính kèm)

```bash
# Restore từ bản rsync
rsync -av --delete /var/backup/kpi_haiquan/uploads/ /var/data/kpi/uploads/

# Hoặc restore từ snapshot cụ thể (nếu cần)
rsync -av /var/backup/kpi_haiquan/uploads_snapshots/<timestamp>/ /var/data/kpi/uploads/
```

### 4.5. Giải mã bản backup off-site (từ GitHub)

```bash
# Clone repo backup (private)
git clone git@github.com:<org>/kpi-backup.git /tmp/kpi-backup
cd /tmp/kpi-backup

# Giải mã bằng GPG
gpg -d daily/db_<file>.sql.gz.gpg > /tmp/db_<file>.sql.gz

# Kiểm tra
gzip -t /tmp/db_<file>.sql.gz

# Restore như bước 4.3
```

**Lưu ý:** Cần passphrase GPG để giải mã (lưu an toàn, KHÔNG commit vào git).

---

## 5. Tạo database test (kpi_haiquan_test)

Database test dùng cho môi trường Development và chạy pytest.

### 5.1. Tạo DB test từ dump production

```bash
# Dump production (CHỈ ĐỌC, an toàn)
sudo -u postgres pg_dump kpi_haiquan > /tmp/kpi_haiquan_prod_$(date +%Y%m%d).sql

# Tạo DB test
sudo -u postgres psql -c "DROP DATABASE IF EXISTS kpi_haiquan_test;"
sudo -u postgres psql -c "CREATE DATABASE kpi_haiquan_test OWNER kpi_user;"

# Restore vào DB test
sudo -u postgres psql -d kpi_haiquan_test < /tmp/kpi_haiquan_prod_<ngày>.sql

# Kiểm tra
sudo -u postgres psql -d kpi_haiquan_test -c "\dt public.*" | wc -l
```

### 5.2. Làm mới DB test (khi prod có dữ liệu mới)

```bash
cd /root/kpi-haiquan/backend
./scripts/dev.sh lam-moi-db
```

Script này tự:
1. Dump `kpi_haiquan` bằng `pg_dump`
2. Drop và recreate `kpi_haiquan_test`
3. Restore dump vào DB test

**An toàn:** Chỉ ĐỌC prod, KHÔNG ghi.

### 5.3. Chạy test trên DB test

```bash
cd /root/kpi-haiquan/backend

# Tự động trỏ vào DB test
./scripts/dev.sh test lms_service/tests/ -v

# Hoặc export thủ công
DB_NAME=kpi_haiquan_test pytest meeting_service/tests/ -v
```

**TUYỆT ĐỐI KHÔNG** chạy test có ghi DB mà `DB_NAME=kpi_haiquan` (prod).

---

## 6. Bảo trì database

### 6.1. VACUUM và ANALYZE

```bash
# VACUUM toàn bộ database (thu hồi không gian)
sudo -u postgres psql -d kpi_haiquan -c "VACUUM ANALYZE;"

# VACUUM bảng cụ thể
sudo -u postgres psql -d kpi_haiquan -c "VACUUM ANALYZE public.ke_khai_cong_viec;"

# VACUUM FULL (khóa bảng, cần downtime)
# CHỈ dùng khi bảng phình to bất thường
sudo -u postgres psql -d kpi_haiquan -c "VACUUM FULL public.<tên-bảng>;"
```

**Lưu ý:** PostgreSQL có autovacuum chạy tự động, ít khi cần VACUUM thủ công.

### 6.2. Kiểm tra kích thước database

```sql
-- Kích thước database
SELECT pg_size_pretty(pg_database_size('kpi_haiquan'));

-- Kích thước từng schema
SELECT 
    schemaname,
    pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename))::bigint) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
GROUP BY schemaname
ORDER BY SUM(pg_total_relation_size(schemaname||'.'||tablename)) DESC;

-- Top 10 bảng lớn nhất
SELECT 
    schemaname || '.' || tablename AS table_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

### 6.3. Kiểm tra kết nối

```sql
-- Số kết nối hiện tại
SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'kpi_haiquan';

-- Chi tiết kết nối
SELECT pid, usename, application_name, client_addr, state, query_start, state_change
FROM pg_stat_activity
WHERE datname = 'kpi_haiquan'
ORDER BY query_start DESC;

-- Giết kết nối cụ thể (nếu cần)
SELECT pg_terminate_backend(<pid>);
```

### 6.4. Reindex (khi index bị phình)

```sql
-- Reindex bảng cụ thể
REINDEX TABLE public.ke_khai_cong_viec;

-- Reindex toàn schema
REINDEX SCHEMA public;

-- Reindex toàn database (cần downtime)
REINDEX DATABASE kpi_haiquan;
```

---

## 7. Quy tắc an toàn khi ghi dữ liệu production

⚠️ **Database tại `localhost:5432` CHÍNH LÀ PRODUCTION** đang phục vụ 558 người dùng.

### 7.1. Nguyên tắc bắt buộc

1. **LUÔN dùng transaction** `BEGIN...COMMIT`
2. **Kiểm tra trong transaction** trước khi `COMMIT`
3. **Backup trước** khi thao tác quan trọng
4. **Test trên DB test** trước khi chạy prod
5. **KHÔNG chạy write query** mà không có user xác nhận

### 7.2. Quy trình thao tác an toàn

```sql
-- Bước 1: Backup (nếu thao tác quan trọng)
\! sudo -u postgres pg_dump kpi_haiquan | gzip > /tmp/backup_before_<việc>_$(date +%Y%m%d_%H%M%S).sql.gz

-- Bước 2: BEGIN transaction
BEGIN;

-- Bước 3: Thực hiện thao tác
UPDATE cong_chuc SET is_active = false WHERE ma_cc = '20ZZ-xxxx';

-- Bước 4: Kiểm tra trong transaction
SELECT ma_cc, ho_ten, is_active FROM cong_chuc WHERE ma_cc = '20ZZ-xxxx';
SELECT COUNT(*) FROM cong_chuc WHERE is_active = false;  -- Đảm bảo chỉ đúng 1 row bị ảnh hưởng

-- Bước 5a: Nếu OK → COMMIT
COMMIT;

-- Bước 5b: Nếu SAI → ROLLBACK
ROLLBACK;
```

### 7.3. Cleanup dữ liệu test (nếu lỡ tạo trên prod)

⚠️ **Sự cố 27/05/2026:** Lỡ tạo ~700 rows test trên prod, phải cleanup thủ công.

Quy trình cleanup bắt buộc:

```sql
BEGIN;

-- 1. Liệt kê toàn bộ row test (có pattern nhận diện)
SELECT id, ma_cc, ho_ten, created_at 
FROM cong_chuc 
WHERE ma_cc LIKE 'TEST_%' OR ho_ten LIKE '%TEST%'
ORDER BY created_at DESC;

-- 2. Báo user và xin confirm phạm vi xóa

-- 3. Xóa trong transaction
DELETE FROM cong_chuc WHERE ma_cc LIKE 'TEST_%';

-- 4. Verify count = 0 (không ảnh hưởng dữ liệu thật)
SELECT COUNT(*) FROM cong_chuc WHERE ma_cc LIKE 'TEST_%';  -- Phải ra 0

-- 5. Sanity check dữ liệu thật KHÔNG bị đụng
SELECT COUNT(*) FROM cong_chuc WHERE is_active = true;  -- Phải ra 558 (hoặc số đúng)

-- 6. Nếu OK → COMMIT
COMMIT;
```

### 7.4. Cấm tuyệt đối

❌ Không chạy E2E test / smoke test trên server cloud prod `79.108.216.189`
❌ Không chạy write query trực tiếp mà không có `BEGIN...COMMIT`
❌ Không chạy `DELETE` / `UPDATE` / `TRUNCATE` mà không có `WHERE` cụ thể
❌ Không chạy migration mới trên prod mà chưa test trên DB test
❌ Không `DROP TABLE` / `DROP SCHEMA` / `DROP DATABASE` mà không backup trước

---

## 8. Tham khảo

- `docs/ra-quet-attt-2026/06_co_so_du_lieu_sao_luu.md` — Cấu trúc CSDL tổng thể
- `backend/alembic/README` — Hướng dẫn Alembic
- `backend/MIGRATION_GUIDE*.md` — Hướng dẫn migration từng module
- Memory `project_db_backup_automation.md` — Chi tiết backup
- Memory `feedback_db_production.md` — Cảnh báo DB production
- Memory `feedback_smoke_test_cleanup.md` — Quy tắc cleanup test data
- Memory `reference_bang_public_thuoc_postgres.md` — Vấn đề owner bảng
