# Project Status v2.0 — PL3 V2

> **Cập nhật:** 2026-04-29
> **Phiên bản:** 2.0 PL3 V2

---

## 1. Phase hoàn thành

| Phase | Tên | Status | Ngày | Files chính |
|---|---|---|---|---|
| A | Database & Migration | ✅ DONE | 2026-04-28 | 9 migrations + 5 models updated + seed 2.812 PL3 |
| B | Backend KPI Logic | ✅ DONE | 2026-04-28 | `kpi_calculator_v2`, `kpi_version`, `ke_khai_v2`, dispatcher |
| C | Backend Admin + Tests | ✅ DONE | 2026-04-28 | `admin_pl3`, `admin_import`, 46/46 tests pass |
| D | Frontend KPI Flow | ✅ DONE | 2026-04-28 | Service V2, modals, trang `/ke-khai-v2`, sidebar redirect |
| E | Frontend Admin + Docs | ✅ DONE | 2026-04-29 | Trang admin PL3 + import + pin version + docs |

---

## 2. Migration applied

```
add_lms_bkt_thuc_hanh_20260422 (V1 head)
   ↓
pl3_v2_001_dm_20260428          # extend danh_muc 14 cột PL3
pl3_v2_002_kk_ver_20260428      # ke_khai_cong_viec version + snapshot
pl3_v2_003_dg_ver_20260428      # danh_gia_thang version + tong_sp_ke_khai
pl3_v2_004_nhom_20260428        # nhom_cong_viec_pl3 + seed 5 nhóm
pl3_v2_005_cc_pin_20260428      # cong_chuc.kpi_version_pinned
pl3_v2_006_seed_def_20260428    # platform_config('kpi_version_default')='V2_PL3'
pl3_v2_007_add_e_20260428       # MucXepLoai enum thêm 'E' (nghỉ thai sản)
pl3_v2_008_drop_cham_20260428   # drop 4 cột chấm chi tiết
pl3_v2_009_ma_30_20260428       # ma_danh_muc VARCHAR(20)→(30) (hỗ trợ -r{row} suffix)
```

---

## 3. Test status

| Suite | Total | Passed |
|---|---|---|
| Unit (kpi_calculator_v2) | 23 | 23 |
| Integration kekhai V2 flow | 4 | 4 |
| Integration V2 schema | 11 | 11 |
| Integration Excel parser | 7 | 7 |
| Regression V1 baseline | 1 | 1 (10 cases) |
| **TỔNG backend** | **46** | **46 ✓** |

Frontend: build production OK 47/47 routes (manual smoke test pass).

---

## 4. Routes mới (V2)

### Backend
- `GET /api/v1/danh-muc/linh-vuc` — 15 lĩnh vực
- `GET /api/v1/danh-muc/sp-cong-viec/pl3?linh_vuc=&nhom_pl3=&search=` — search 2.812 mục
- `POST /api/v1/ke-khai-v2` — tạo kê khai
- `GET /api/v1/ke-khai-v2/me` — list của bản thân
- `GET /api/v1/ke-khai-v2/thong-ke/thang` — banner Tổng SP
- `POST /api/v1/ke-khai-v2/nhieu-ngay` — multi-day
- `PUT /api/v1/ke-khai-v2/{id}`, `DELETE`, `GET /{id}` — CRUD
- `GET/POST/PUT/DELETE /api/v1/admin/danh-muc-pl3` — admin CRUD
- `GET /api/v1/admin/danh-muc-v1` + `PUT /{id}/deactivate` — V1 read + deactivate
- `POST /api/v1/admin/danh-muc-pl3/import/dry-run` + `/commit` — import Excel
- `PUT /api/v1/admin/cong-chuc/{id}/kpi-version` — pin CC
- `PUT /api/v1/admin/don-vi/{id}/kpi-version` — bulk pin đơn vị
- `/api/v1/auth/me` mở rộng `kpi_version_pinned` + `effective_kpi_version`

### Frontend
- `/ke-khai-v2` — trang kê khai V2 cho CC
- `/admin/danh-muc-pl3` — quản lý 2.812 mục PL3 + import Excel
- `/admin/kpi-version` — pin V1/V2 cho CC + đơn vị

---

## 5. Database state hiện tại

```
public.danh_muc_sp_cong_viec:
  - V1 (nguon_du_lieu='V1'):  55 mục (46 gốc + 9 admin thêm)
  - PL3 (nguon_du_lieu='PL3'): 2.812 mục (15 lĩnh vực × 5 nhóm)

public.cong_chuc.kpi_version_pinned:
  - 551/551 NULL → fallback platform_config('V2_PL3')

public.platform_config('kpi_version_default') = 'V2_PL3'

public.muc_xep_loai_enum: ['A','B','C','D','E']

ke_khai_cong_viec.version_kekhai:
  - 12.646 V1 (data lịch sử)
  - 0 V2_PL3 (chưa có user kê khai trên test)

danh_gia_thang.version_tinh_diem:
  - 783 V1 (data lịch sử)
```

---

## 6. UAT plan

### 6.1 Trên test env hiện tại
1. Admin login với `ADMIN-001` / `123456` → vào `/admin/danh-muc-pl3` → verify 2.812 mục.
2. Pin 1-2 đơn vị (vd Văn phòng, HQCK Móng Cái) sang `V2_PL3` qua `/admin/kpi-version`.
3. CC trong đơn vị thử login → thấy menu "Kê khai (V2)" → tạo kê khai → submit.
4. Lãnh đạo phê duyệt.
5. CC vào `/danh-gia` xem KPI tháng (ban đầu V2 dispatcher tính đúng từ snapshot).
6. Admin vào `/admin/kpi-version` chọn unpin → CC quay về V1 (effective qua platform_config default).

### 6.2 Trên prod (sau UAT)
- Cutover toàn cụ: SQL `UPDATE platform_config SET value='"V2_PL3"' WHERE key='kpi_version_default'`.
- Rollback: đổi `'V1'` lại.

---

## 7. Known limitations

| Phần | Trạng thái | Lý do |
|---|---|---|
| `don_vi_linh_vuc_mac_dinh` | DEFER | Cần input nghiệp vụ map 15 đơn vị → lĩnh vực |
| Báo cáo quý cross-version | DEFER | Cần policy nghiệp vụ |
| UI default hệ thống | SKIP | Cutover qua SQL đủ |
| Frontend tests automated | SKIP | Chưa có infra Vitest/Playwright |
| Label "ngày × 96" replacement | PARTIAL | Chỉ thêm banner V2 cảnh báo, không sửa toàn bộ label trong xếp loại |

---

## 8. Reference docs

- `docs/IMPACT_ANALYSIS_KPI_V2_PL3.md` — phân tích tác động ban đầu
- `docs/BUSINESS_RULES_v3_0_PL3.md` — rules + 19 LOCKED decisions
- `docs/HUONG_DAN_ADMIN_PL3.md` — hướng dẫn admin
- `docs/prompts/README_BO_PROMPT_02.md` — bộ 5 prompts gốc
- `docs/prompts/PROMPT_02A...02E.md` — chi tiết từng phase
