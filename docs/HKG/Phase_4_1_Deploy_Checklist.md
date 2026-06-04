# Phase 4.1 — Deploy Checklist (Page-Sync HKG)

**Phạm vi**: Deploy commits FE_P0..P5 + BE_P0..P6 từ branch `feature/kpi-lanh-dao-phan-cong` lên production.

**Yêu cầu**: UAT đã pass (≥22/24 case), backup hôm nay đã verify, có cửa sổ bảo trì 30 phút.

---

## 1. Pre-deploy (làm trước maintenance window)

- [ ] **Branch hợp nhất**: PR mở từ `feature/kpi-lanh-dao-phan-cong` → `main`, đã review + approve
- [ ] **Backup verify**: chạy `bash /root/kpi-haiquan/scripts/backup_daily.sh` thủ công 1 lần → verify file `.dump` nằm tại đích + checksum OK
- [ ] **DB snapshot bổ sung**: `pg_dump -Fc kpi_haiquan > /var/backups/kpi_pre_phase41_$(date +%Y%m%d_%H%M).dump` (nếu cần rollback nhanh)
- [ ] **Notify users**: thông báo cuộc họp đang diễn ra (nếu có) → tránh deploy khi đang họp live
- [ ] **Tag release**: `git tag phase-4.1-page-sync-v1.0` trên commit cuối cùng của FE_P5

---

## 2. Deploy backend (meeting_service port 8006)

```bash
# 1. Pull code mới
cd /root/kpi-haiquan
git fetch origin
git checkout main
git pull --ff-only

# 2. Migration (auto-run khi service start, nhưng explicit cho an tâm)
cd backend
source venv/bin/activate
alembic upgrade head 2>&1 | tail -20
# Verify: revision = mt_013_ttc_20260502
alembic current

# 3. Reload meeting_service
pm2 restart meeting_service
pm2 logs meeting_service --lines 50 --nostream | grep -iE "(error|started|listening)"
# Phải thấy "Uvicorn running on ... 8006" + KHÔNG có ERROR

# 4. Smoke test REST endpoint
curl -s http://localhost:8006/health
# Expect: {"status":"ok"}

# 5. Smoke test JWT-protected endpoint (cần token tự lấy)
TOKEN="<JWT của 1 user test>"
CUOC_HOP_ID="<uuid của 1 cuộc họp DA_THONG_BAO>"
curl -s "http://localhost:8006/api/v1/hop-khong-giay/cuoc-hop/$CUOC_HOP_ID/presentation/state" \
  -H "Authorization: Bearer $TOKEN" | jq
# Expect: {success:true, data:{ws_token:"...", ...}}
```

- [ ] Migration applied
- [ ] meeting_service restart sạch
- [ ] /health 200 OK
- [ ] /presentation/state cấp ws_token

---

## 3. Deploy frontend (next.js port 3000)

```bash
cd /root/kpi-haiquan/frontend

# 1. Install deps mới (pdfjs-dist, vitest devDeps)
npm ci

# 2. Build prod
npm run build 2>&1 | tail -10
# Phải thấy "✓ Compiled successfully"

# 3. Reload Next.js
pm2 restart frontend
pm2 logs frontend --lines 30 --nostream | grep -iE "(error|ready|listening)"

# 4. Smoke test browser:
#    - Mở https://kpihaiquan.vn/hop-khong-giay/chi-tiet/<id>/tai-lieu
#    - DevTools Console: KHÔNG có lỗi pdfjs / WebSocket
#    - Network: /pdf.worker.min.mjs trả 200 (1.4MB)
```

- [ ] Build PASS
- [ ] Frontend restart sạch
- [ ] PDF worker file load 200
- [ ] Tab Tài liệu render đúng trên cuộc họp test

---

## 4. Smoke test sau deploy (5 phút)

| # | Action | Expected | Pass/Fail |
|---|--------|----------|-----------|
| 1 | Host bấm "Bắt đầu họp" trên 1 cuộc họp test | trạng thái → DANG_DIEN_RA | ☐ |
| 2 | Host bấm "Trình chiếu" file PDF | viewer render trang 1, badge "Đang đồng bộ" | ☐ |
| 3 | Đại biểu trên thiết bị khác mở cuộc họp | Thấy đúng trang host trong ≤2s | ☐ |
| 4 | Host lật trang | đại biểu lật theo ≤500ms | ☐ |
| 5 | Host bấm "Kết thúc trình chiếu" | viewer ẩn, list doc trở lại | ☐ |
| 6 | Đóng test bằng cách host bấm "Kết thúc họp" | trạng thái → HOAN_THANH | ☐ |
| 7 | `pm2 logs meeting_service` | KHÔNG có ERROR/Exception trong 5 phút deploy | ☐ |
| 8 | `psql -c "SELECT count(*) FROM meeting.audit_log WHERE created_at > NOW() - INTERVAL '10 minutes'"` | có ≥3 row tương ứng action P1..P6 | ☐ |

---

## 5. Rollback procedures (nếu fail)

### 5.1. Rollback frontend (nhanh — không cần restore DB)

```bash
cd /root/kpi-haiquan
git checkout <commit-before-FE_P0>
cd frontend && npm ci && npm run build && pm2 restart frontend
```

### 5.2. Rollback backend + DB (nếu migration gây hỏng)

```bash
# CẨN THẬN: chỉ làm khi đã xác định Phase 4.1 là root cause
cd /root/kpi-haiquan
git checkout <commit-before-BE_P0>

# Downgrade migration
cd backend && source venv/bin/activate
alembic downgrade -1  # → revert mt_013_ttc_20260502
alembic current  # phải show mt_012_extend_dd_20260501

# Restore từ snapshot (nếu downgrade không đủ)
# pg_restore -d kpi_haiquan -c /var/backups/kpi_pre_phase41_*.dump

pm2 restart meeting_service
```

- Backup snapshot path: `/var/backups/kpi_pre_phase41_<timestamp>.dump`
- Phone hỗ trợ DBA: ____________________

---

## 6. Post-deploy (sau 1 giờ)

- [ ] Monitor `/var/log/pm2/meeting_service-error.log` không có spike
- [ ] Audit log: số bản ghi action `PRESENTATION_*` ổn định (không spam)
- [ ] DB connection count: <50% pool
- [ ] User feedback: không có report "không xem được trình chiếu"

---

## Sign-off

- Deployer: ____________________
- Ngày/giờ deploy: ____________________
- Tag release: `phase-4.1-page-sync-v1.0`
- PR link: ____________________
- UAT report: ____________________