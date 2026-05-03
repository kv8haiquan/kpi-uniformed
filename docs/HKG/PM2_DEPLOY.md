# PM2_DEPLOY.md — Deploy `meeting-backend` vào PM2

**Phiên bản:** 1.0 · **Ngày:** 2026-05-01

> File hướng dẫn user deploy HKG service (port 8006, internal-only) qua PM2.
> CLI **đã tạo** file `ecosystem.config.js` ở root repo. **CLI KHÔNG tự chạy `pm2 ...`** — đó là việc của user.

---

## 0. Bối cảnh

Trước G4-deploy, 7 service hiện có (KPI/LMS/Forum/Legal/Portal/Common backend + KPI frontend) được start qua CLI thủ công rồi `pm2 save`. **KHÔNG có file ecosystem.**

CLI tạo `ecosystem.config.js` chứa **đầy đủ 8 entry** (7 cũ y nguyên cấu hình thật + 1 mới `meeting-backend`). Diff verify đã pass — 7 entry cũ khớp 100% với `pm2 jlist`.

---

## 1. Pre-flight (kiểm tra trước khi deploy)

```bash
# Verify file ecosystem
ls -la /root/kpi-haiquan/ecosystem.config.js

# Verify cấu hình ecosystem khớp với 7 service đang chạy (đã verify CLI — chạy lại nếu muốn)
node -e "console.log(require('/root/kpi-haiquan/ecosystem.config.js').apps.map(a => a.name))"
# → 8 names; 7 cũ khớp với `pm2 list`, +1 'meeting-backend'

# Verify port 8006 chưa bị chiếm
ss -tln | grep ':8006 ' || echo '(8006 free — OK)'

# Verify code meeting_service ready
ls /root/kpi-haiquan/backend/meeting_service/main.py

# Verify migrations đã apply (G0+G1)
cd /root/kpi-haiquan/backend && source venv/bin/activate && alembic current
# → mt_011_seed_roles_20260430 (head)
```

---

## 2. Step-by-step deploy

### Step 1: Start MỘT mình `meeting-backend` (KHÔNG đụng 7 service cũ)

```bash
cd /root/kpi-haiquan
pm2 start ecosystem.config.js --only meeting-backend
```

Output mong đợi:

```
[PM2][WARN] Applications meeting-backend not running, starting...
[PM2] App [meeting-backend] launched (1 instances)
```

### Step 2: Verify status

```bash
pm2 status
# → Phải có 8 process online: 7 cũ + meeting-backend
```

```bash
pm2 logs meeting-backend --lines 50 --nostream
# Phải thấy:
#   Starting HQKV8 HKG service on port 8006 (internal-only)...
#   APScheduler started — 4 jobs registered
#   INFO: Uvicorn running on http://127.0.0.1:8006
```

```bash
curl -s http://127.0.0.1:8006/health | python3 -m json.tool
# Mong đợi:
# {
#   "status": "ok",
#   "service": "meeting",
#   "version": "0.1.0-G3b",
#   "scheduler": {"running": true, "jobs": [...4 jobs...]},
#   "modules": {...6 modules ready...}
# }
```

### Step 3: Verify internal-only (không expose ra ngoài)

```bash
HOST_IP=$(hostname -I | awk '{print $1}')
echo "Host IP: $HOST_IP"
curl -m 3 http://${HOST_IP}:8006/health
# Mong đợi: connection refused / timeout — vì meeting bind 127.0.0.1
```

### Step 4: Persist để auto-restart sau reboot

```bash
pm2 save
# → Saving current process list...
# → Successfully saved in /root/.pm2/dump.pm2
```

### Step 5: Verify 7 service cũ KHÔNG bị restart

```bash
pm2 status
# Cột "↺" của 7 service cũ phải GIỮ NGUYÊN số restart đếm trước Step 1.
# Nếu tăng → đã restart (sai bước, kiểm tra lại Step 1 dùng đúng --only).
```

---

## 3. Re-deploy / update code

Sau khi sửa code `meeting_service/`:

```bash
cd /root/kpi-haiquan
pm2 restart meeting-backend
# Hoặc reload (graceful):
pm2 reload meeting-backend
pm2 save
```

**KHÔNG dùng** `pm2 reload ecosystem.config.js` (không có `--only`) trên production — sẽ restart cả 7 service cũ.

---

## 4. Rollback nếu fail

### Trường hợp A: meeting-backend báo lỗi khởi động

```bash
# Xem log chi tiết
pm2 logs meeting-backend --lines 100 --nostream

# Common errors:
# 1. ImportError → check venv: cd backend && source venv/bin/activate && python -c "from meeting_service.main import app"
# 2. DB connection refused → check PostgreSQL có chạy không (port 5432)
# 3. Port 8006 EADDRINUSE → ss -tlnp | grep 8006 → kill process chiếm port
# 4. ModuleNotFoundError 'apscheduler' → pip install apscheduler trong venv
```

### Trường hợp B: cần xóa hoàn toàn entry

```bash
pm2 delete meeting-backend
pm2 save
# Khôi phục git nếu cần:
cd /root/kpi-haiquan
git restore ecosystem.config.js
```

### Trường hợp C: lỡ reload toàn bộ ecosystem (7 cũ bị restart)

Không cần làm gì — autorestart=true sẽ self-heal. Chỉ verify lại:

```bash
pm2 status
# Tất cả phải online sau ~5 giây
```

---

## 5. Debug nếu service không healthy

### Service status `errored` hoặc `stopped`

```bash
# 1. Check log
pm2 logs meeting-backend --err --lines 100 --nostream

# 2. Stop + try manual run để xem stderr trực tiếp
pm2 stop meeting-backend
cd /root/kpi-haiquan/backend
source venv/bin/activate
HKG_DISABLE_SCHEDULER=true python -m uvicorn meeting_service.main:app --host 127.0.0.1 --port 8006
# Ctrl+C khi xác định nguyên nhân, sau đó:
pm2 start meeting-backend
```

### Service online nhưng /health fail

```bash
# Kiểm tra DB connection
cd /root/kpi-haiquan/backend && source venv/bin/activate
python -c "
import asyncio
from meeting_service.dependencies import session_factory
async def t():
    async with session_factory() as s:
        from sqlalchemy import text
        r = await s.execute(text('SELECT 1'))
        print('DB OK:', r.scalar())
asyncio.run(t())
"
```

---

## 5A. Storage isolation (G4-fix-8 — 02/05/2026)

> **Bug đã fix:** test fixture cũ `rmtree("uploads/meeting")` từng xóa nhầm file
> production. Đã chuyển sang sandbox tmpdir cho test + alias env `HKG_UPLOAD_DIR`
> cho production.

### Recommendation cho production

Dùng **absolute path** ngoài repo để tránh git/redeploy nuốt mất file. Sửa hoặc thêm vào `backend/.env`:

```bash
# .env — backend/
HKG_UPLOAD_DIR=/var/data/hkg/uploads/meeting
```

Setup:
```bash
# Tạo dir + chmod
sudo mkdir -p /var/data/hkg/uploads/meeting
sudo chown -R root:root /var/data/hkg          # hoặc user chạy meeting-backend
sudo chmod 755 /var/data/hkg

# Migrate file hiện tại (nếu cần)
mv /root/kpi-haiquan/backend/uploads/meeting/* /var/data/hkg/uploads/meeting/

# Restart
pm2 restart meeting-backend
pm2 logs meeting-backend --lines 20 --nostream | grep -i "upload\|hkg"
```

Verify:
```bash
# Upload 1 file qua FE → check disk
ls -la /var/data/hkg/uploads/meeting/tai-lieu/
```

### Default fallback

Nếu KHÔNG set `HKG_UPLOAD_DIR`, default là `uploads/meeting` (relative, theo cwd PM2 = `backend/`). Hoạt động được nhưng risk:
- Redeploy bằng `git clean -fdx` xóa folder
- Test fixture cũ (đã fix nhưng nếu ai paste lại) có thể xóa nhầm

→ **Production STRONGLY recommended:** set `HKG_UPLOAD_DIR=/var/data/hkg/uploads/meeting` trong `.env`.

---

## 6. Khi nào mở public (sau UAT pass)

Sau UAT (xem G4 báo cáo §8 UAT checklist), để mở `:8006` ra Nginx public:

1. Sửa `ecosystem.config.js` → đổi `--host 127.0.0.1` thành `--host 0.0.0.0` cho `meeting-backend`.
2. `pm2 reload ecosystem.config.js --only meeting-backend`.
3. Cấu hình Nginx reverse proxy `https://hkg.kv08.vn` → `http://127.0.0.1:8006`.
4. Sửa `frontend/src/components/common/Sidebar.tsx` — bỏ điều kiện `hkgVisible` để mở cho 549 user (xem G4 báo cáo).

---

## 7. Quick Reference

| Lệnh | Tác dụng |
|---|---|
| `pm2 start ecosystem.config.js --only meeting-backend` | Lần đầu start |
| `pm2 restart meeting-backend` | Restart sau update code |
| `pm2 reload meeting-backend` | Graceful restart (giữ connections) |
| `pm2 logs meeting-backend --lines 50` | Tail log |
| `pm2 logs meeting-backend --err` | Chỉ error log |
| `pm2 stop meeting-backend` | Tạm dừng |
| `pm2 delete meeting-backend` | Xóa entry hoàn toàn |
| `pm2 save` | Persist sau mọi thay đổi |
| `pm2 monit` | Real-time CPU/Mem dashboard |

---

*Hết tài liệu. Sau khi deploy thành công, reply lại CLI kết quả các Step 1-5 để xác nhận.*
