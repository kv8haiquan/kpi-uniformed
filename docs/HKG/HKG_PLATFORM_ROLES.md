# HKG_PLATFORM_ROLES.md — Phân quyền Platform Roles

**Phiên bản:** 1.0 (MVP) · **Ngày:** 30/04/2026

> File này định nghĩa CHI TIẾT các platform_role mới cần seed cho HKG, kèm bảng ánh xạ nghiệp vụ HKG.pdf v5.0 → cơ chế phân quyền 2 lớp của nền tảng.
>
> **Nguyên tắc tuyệt đối:** KHÔNG sửa `public.cong_chuc`, KHÔNG thêm cột flag. Mọi vai trò mới đều thông qua `platform_role` + `cong_chuc_platform_role`.

---

## 1. CƠ CHẾ PHÂN QUYỀN 2 LỚP

```
Lớp 1: vai_tro KPI (đã có sẵn — KHÔNG sửa)
─────────────────────────────────────────
SUPER_ADMIN > CHI_CUC_TRUONG > PHO_CHI_CUC_TRUONG >
TRUONG_DON_VI > PHO_DON_VI > CONG_CHUC > TCCB

→ 1 CBCC có CHÍNH XÁC 1 vai_tro
→ Lưu trong: public.cong_chuc.vai_tro_id
→ Cờ tự động: is_lanh_dao = TRUE nếu vai_tro IN (CCT, PCCT, TDV, PDV)


Lớp 2: platform_roles (gán thêm cho từng module)
─────────────────────────────────────────
HKG-specific: CHU_TOA_HOP, THU_KY_HOP, CHANH_VP,
              TRUONG_CNTT, DANG_VIEN, BI_THU_CHI_BO, PHO_BI_THU

→ 1 CBCC có 0 → nhiều platform_roles
→ Lưu trong: public.cong_chuc_platform_role
→ Có thể có pham_vi (JSONB): áp dụng đơn vị nào / chi bộ nào
```

---

## 2. ÁNH XẠ HKG.pdf §4.4 → CƠ CHẾ HIỆN TẠI

HKG.pdf v5.0 đề xuất thêm 7 cột flag vào `public.cong_chuc`. Đây là cách map đúng theo nguyên tắc nền tảng:

| HKG.pdf đề xuất (SAI) | Cách đúng theo nền tảng |
|---|---|
| `is_lanh_dao_cc` | Dẫn xuất từ `vai_tro IN ('CHI_CUC_TRUONG', 'PHO_CHI_CUC_TRUONG')` |
| `is_lanh_dao_dv` | Đã có sẵn `cong_chuc.is_lanh_dao` (flag boolean trong KPI) |
| `is_admin` | Dẫn xuất từ `vai_tro = 'SUPER_ADMIN'` |
| `is_chanh_vp` | **Platform role mới**: `CHANH_VP` |
| `is_truong_cntt` | **Platform role mới**: `TRUONG_CNTT` |
| `is_thu_ky_dv` | **Platform role mới**: `THU_KY_HOP` |
| `is_dang_vien` | **Platform role mới**: `DANG_VIEN` |

→ **KHÔNG cần sửa public.cong_chuc**. Mọi nhu cầu phân quyền đều xử lý được.

---

## 3. ĐỊNH NGHĨA 7 PLATFORM ROLES MỚI

### 3.1. Bảng tổng quan

> **Lưu ý:** chỉ **6 role static** được seed vào `public.platform_role`. `CHU_TOA_HOP` là **dynamic** — không seed, suy ra từ `meeting.cuoc_hop.chu_toa_id`. Xem §3.2 để hiểu lý do.

| Mã role (`ma_role`) | Tên hiển thị (`ten_role`) | Phạm vi | Ai có quyền gán | Số lượng dự kiến | Seed? |
|---|---|---|---|---|:---:|
| `CHU_TOA_HOP` | Chủ tọa cuộc họp | Theo từng cuộc họp | Tự động (dynamic) | Theo nhu cầu | ❌ |
| `THU_KY_HOP` | Thư ký cuộc họp | Đơn vị cụ thể | Admin / Chánh VP | ~14-28 người (1-2/đơn vị) | ✅ |
| `CHANH_VP` | Chánh Văn phòng | Toàn Chi cục | SUPER_ADMIN | 1 người | ✅ |
| `TRUONG_CNTT` | Trưởng phòng CNTT | Toàn Chi cục | SUPER_ADMIN | 1 người | ✅ |
| `DANG_VIEN` | Đảng viên | Theo Chi bộ | Admin / Bí thư | Tùy thực tế | ✅ |
| `BI_THU_CHI_BO` | Bí thư Chi bộ | 1 Chi bộ | SUPER_ADMIN | 14 người (1/chi bộ) | ✅ |
| `PHO_BI_THU` | Phó Bí thư Chi bộ | 1 Chi bộ | SUPER_ADMIN | 14 người | ✅ |

### 3.2. Chi tiết quyền của từng role

#### CHU_TOA_HOP (DYNAMIC — KHÔNG SEED)
```
- Tự động được gán khi 1 CBCC được set là chu_toa_id của 1 cuộc họp
- KHÔNG phải role gán cố định — tính theo từng cuộc họp
- KHÔNG có trong danh sách seed (xem §4 và §8.1 của HKG_DATABASE_DESIGN.md)
- Quyền:
  ✓ Sửa/hủy cuộc họp đó
  ✓ Duyệt đơn xin vắng của cuộc họp đó
  ✓ Mở/đóng phiên biểu quyết (Phase sau)
  ✓ Ký biên bản
  ✓ Tạo kết luận / nhiệm vụ
- KHÔNG lưu trong cong_chuc_platform_role
- Implementation: check meeting.cuoc_hop.chu_toa_id = current_user_id
```

#### THU_KY_HOP
```
- Role gán cố định cho CBCC làm thư ký 1 hoặc nhiều đơn vị
- Quyền:
  ✓ Tạo cuộc họp cho đơn vị mình (cùng với chủ tọa)
  ✓ Upload tài liệu họp
  ✓ Bấm điểm danh tay
  ✓ Ghi biên bản, soạn → trình ký
  ✓ Cập nhật kết luận đơn vị mình
  ✓ Xem thống kê đơn vị mình
- KHÔNG được:
  ✗ Xem cuộc họp / thống kê đơn vị KHÁC
  ✗ Ký biên bản (chỉ chủ tọa ký)
- Phạm vi: pham_vi JSONB = {"don_vi_ids": ["uuid1", "uuid2"]}
- Auto khi tạo họp: nếu CBCC set là thu_ky_id → kiểm tra phải có role THU_KY_HOP
```

#### CHANH_VP
```
- Role đặc biệt, gán cố định
- Quyền:
  ✓ Xem TOÀN BỘ cuộc họp Chi cục (mọi đơn vị)
  ✓ Xem TOÀN BỘ thống kê
  ✓ Xem TOÀN BỘ biên bản
  ✓ Tạo cuộc họp cấp Chi cục
  ✓ Điều phối lịch họp toàn CC
- KHÔNG có quyền:
  ✗ Sửa/xóa cuộc họp của đơn vị khác (chỉ XEM)
  ✗ Quản trị hệ thống (cấu hình, user management)
- Phạm vi: TOAN_CHI_CUC (mặc định)
```

#### TRUONG_CNTT
```
- Role đặc biệt, gán cho 1 người (Trưởng phòng CNTT)
- Quyền:
  ✓ Xem TOÀN BỘ giống CHANH_VP
  ✓ + Quyền QUẢN TRỊ KỸ THUẬT:
    - Quản lý template biên bản (upload, version)
    - Cấu hình hệ thống HKG
    - Import/Export dữ liệu
    - Xem audit log đầy đủ
  ✓ Chủ trì module HKG về mặt kỹ thuật
- Phạm vi: TOAN_CHI_CUC + ADMIN_HKG
```

#### DANG_VIEN
```
- Role gán cho CBCC là Đảng viên
- Quyền:
  ✓ Tham dự họp Đảng (khoi=DANG)
  ✓ Xem tài liệu họp Đảng được mời
  ✓ Biểu quyết trong họp Đảng (Phase sau)
- KHÔNG ảnh hưởng quyền họp Chuyên môn
- Phạm vi: pham_vi JSONB = {"chi_bo": "ten_chi_bo"} hoặc don_vi_id
- Khi tạo cuộc họp khoi=DANG: chỉ Đảng viên mới được thêm vào thanh_phan
```

#### BI_THU_CHI_BO
```
- Role gán cho 1 người/chi bộ
- Quyền:
  ✓ Tự động là CHU_TOA_HOP cho mọi họp Chi bộ mình
  ✓ Tạo họp Chi bộ
  ✓ Khi xuất biên bản Chi bộ: placeholder {{chu_tri}} = "Bí thư"
- Phạm vi: pham_vi JSONB = {"chi_bo_id": "uuid"} (Phase 8 mới có chi_bo_id)
- MVP: chỉ cần khoi=DANG, chưa cần chi_bo_id cụ thể
```

#### PHO_BI_THU
```
- Role gán cho 1 người/chi bộ
- Quyền:
  ✓ Hỗ trợ Bí thư
  ✓ Có thể là Chủ tọa khi Bí thư vắng
  ✓ Khi xuất biên bản: placeholder {{chu_tri}} = "Phó Bí thư"
- Phạm vi: tương tự BI_THU_CHI_BO
```

---

## 4. SEED MIGRATION

> **Schema thật `public.platform_role`:** `id, ma_role, ten_role, mo_ta, quyen_han(JSONB), is_active, created_at`. **Không có** cột `module` riêng — encode `{"module": "MEETING"}` vào JSONB `quyen_han`. Filter HKG roles bằng `WHERE quyen_han->>'module' = 'MEETING'`.

```python
# Alembic: meeting_seed_platform_roles_YYYYMMDD.py
# Seed 6 platform_role static cho HKG. CHU_TOA_HOP là dynamic — KHÔNG seed.

PLATFORM_ROLES_HKG = [
    {
        "ma_role": "THU_KY_HOP",
        "ten_role": "Thư ký cuộc họp",
        "mo_ta": "Ghi biên bản, hỗ trợ điều hành",
        "quyen_han": {"module": "MEETING", "type": "static", "scoped": True},
    },
    {
        "ma_role": "CHANH_VP",
        "ten_role": "Chánh Văn phòng",
        "mo_ta": "Xem toàn bộ cuộc họp Chi cục, điều phối lịch",
        "quyen_han": {"module": "MEETING", "type": "static"},
    },
    {
        "ma_role": "TRUONG_CNTT",
        "ten_role": "Trưởng phòng CNTT",
        "mo_ta": "Quản trị kỹ thuật HKG + xem toàn bộ",
        "quyen_han": {"module": "MEETING", "type": "static"},
    },
    {
        "ma_role": "DANG_VIEN",
        "ten_role": "Đảng viên",
        "mo_ta": "Tham dự họp Đảng",
        "quyen_han": {"module": "MEETING", "type": "static"},
    },
    {
        "ma_role": "BI_THU_CHI_BO",
        "ten_role": "Bí thư Chi bộ",
        "mo_ta": "Chủ trì họp Chi bộ",
        "quyen_han": {"module": "MEETING", "type": "static", "scoped": True},
    },
    {
        "ma_role": "PHO_BI_THU",
        "ten_role": "Phó Bí thư Chi bộ",
        "mo_ta": "Hỗ trợ Bí thư",
        "quyen_han": {"module": "MEETING", "type": "static", "scoped": True},
    },
]

def upgrade():
    import json
    for role in PLATFORM_ROLES_HKG:
        op.execute(f"""
            INSERT INTO public.platform_role
                (id, ma_role, ten_role, mo_ta, quyen_han, is_active, created_at)
            VALUES
                (gen_random_uuid(),
                 '{role['ma_role']}',
                 '{role['ten_role']}',
                 '{role['mo_ta']}',
                 '{json.dumps(role['quyen_han'])}'::jsonb,
                 TRUE,
                 NOW())
            ON CONFLICT (ma_role) DO NOTHING
        """)
```

**Field semantics trong `quyen_han` JSONB:**

| Key | Giá trị | Ý nghĩa |
|---|---|---|
| `module` | `"MEETING"` | Module sở hữu role |
| `type` | `"static"` | Static = lưu cố định trong `cong_chuc_platform_role`. `dynamic` = suy ra runtime (như `CHU_TOA_HOP`) |
| `scoped` | `true` / vắng | `true` = role có scope đơn vị (đọc thêm từ `cong_chuc_platform_role.pham_vi`); vắng = áp dụng toàn Chi cục |

---

## 5. BẢNG MA TRẬN PHÂN QUYỀN HKG

| Hành động | CBCC | Thư ký HOP | Chủ tọa | LĐ ĐV | Chánh VP | TP CNTT | CCT/PCCT | Admin |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Cuộc họp** |
| Xem cuộc họp được mời | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Xem cuộc họp đơn vị mình | — | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| Xem TOÀN BỘ cuộc họp Chi cục | — | — | — | — | ✅ | ✅ | ✅ | ✅ |
| Tạo cuộc họp đơn vị mình | — | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tạo cuộc họp cấp Chi cục | — | — | — | — | ✅ | ✅ | ✅ | ✅ |
| Sửa/hủy cuộc họp | — | — | ✅ | — | — | — | — | ✅ |
| **Tài liệu** |
| Xem tài liệu được phân quyền | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Upload tài liệu | — | ✅ | ✅ | — | — | — | — | ✅ |
| Phân quyền/ẩn tài liệu | — | ✅ | ✅ | — | — | — | — | ✅ |
| **Điểm danh** |
| Điểm danh QR (cá nhân) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Bấm điểm danh tay | — | ✅ | ✅ | — | — | — | — | ✅ |
| **Xin phép vắng** |
| Gửi đơn xin vắng | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Duyệt đơn xin vắng | — | — | ✅ | — | — | — | — | ✅ |
| **Biên bản** |
| Soạn biên bản | — | ✅ | — | — | — | — | — | ✅ |
| Trình ký biên bản | — | ✅ | — | — | — | — | — | ✅ |
| Ký biên bản | — | — | ✅ | — | — | — | — | — |
| Xuất DOCX/PDF | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Kết luận / Nhiệm vụ** |
| Tạo kết luận | — | — | ✅ | — | — | — | — | ✅ |
| Cập nhật tiến độ (cá nhân) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Xem kết luận đơn vị mình | — | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| Xem kết luận TOÀN CC | — | — | — | — | ✅ | ✅ | ✅ | ✅ |
| **Thống kê** |
| Thống kê cá nhân | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Thống kê đơn vị mình | — | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| Thống kê TOÀN CC | — | — | — | — | ✅ | ✅ | ✅ | ✅ |
| **Quản trị** |
| Quản lý template | — | — | — | — | — | ✅ | — | ✅ |
| Cấu hình hệ thống | — | — | — | — | — | ✅ | — | ✅ |
| Quản lý user/role | — | — | — | — | — | — | — | ✅ |
| Xem audit log | — | — | — | — | — | ✅ | — | ✅ |

> **Quan trọng:** Thư ký HOP cấp đơn vị **KHÔNG xem được dữ liệu đơn vị khác**. Đây là yêu cầu nghiệp vụ rõ ràng từ HKG.pdf v5.0 §2.1.

---

## 6. IMPLEMENTATION PATTERN — PERMISSION CHECK

### 6.1. Helper functions

```python
# backend/meeting_service/dependencies.py

from fastapi import Depends, HTTPException

async def can_view_meeting(
    cuoc_hop_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> bool:
    """Check user có xem được cuộc họp này không"""
    cuoc_hop = db.query(CuocHop).filter_by(id=cuoc_hop_id).first()
    if not cuoc_hop:
        raise HTTPException(404, "Không tìm thấy cuộc họp")

    user_id = current_user["sub"]
    user_don_vi = current_user["don_vi_id"]
    vai_tro = current_user["vai_tro"]
    platform_roles = current_user.get("platform_roles", [])
    is_lanh_dao = current_user.get("is_lanh_dao", False)

    # 1. Admin / CCT / PCCT / CHANH_VP / TRUONG_CNTT → toàn quyền
    if vai_tro in ["SUPER_ADMIN", "CHI_CUC_TRUONG", "PHO_CHI_CUC_TRUONG"]:
        return True
    if "CHANH_VP" in platform_roles or "TRUONG_CNTT" in platform_roles:
        return True

    # 2. Lãnh đạo đơn vị → cuộc họp đơn vị mình
    if is_lanh_dao and cuoc_hop.don_vi_to_chuc_id == user_don_vi:
        return True

    # 3. Thư ký → cuộc họp đơn vị mình
    if "THU_KY_HOP" in platform_roles:
        # check pham_vi
        thu_ky_don_vi_ids = get_thu_ky_pham_vi(user_id, db)
        if cuoc_hop.don_vi_to_chuc_id in thu_ky_don_vi_ids:
            return True

    # 4. Chủ tọa
    if cuoc_hop.chu_toa_id == user_id:
        return True

    # 5. Thư ký được chỉ định cho cuộc họp này
    if cuoc_hop.thu_ky_id == user_id:
        return True

    # 6. Được mời tham dự
    is_invited = db.query(ThanhPhan).filter_by(
        cuoc_hop_id=cuoc_hop_id,
        cong_chuc_id=user_id
    ).first()
    if is_invited:
        return True

    raise HTTPException(403, "Bạn không có quyền xem cuộc họp này")


async def can_edit_meeting(cuoc_hop_id, current_user, db):
    """Chỉ chu_toa, thu_ky của cuộc họp, hoặc admin/TP CNTT"""
    cuoc_hop = db.query(CuocHop).filter_by(id=cuoc_hop_id).first()
    if not cuoc_hop:
        raise HTTPException(404)

    user_id = current_user["sub"]
    if cuoc_hop.chu_toa_id == user_id:
        return True
    if cuoc_hop.thu_ky_id == user_id:
        return True
    if current_user["vai_tro"] == "SUPER_ADMIN":
        return True
    if "TRUONG_CNTT" in current_user.get("platform_roles", []):
        return True

    raise HTTPException(403, "Bạn không có quyền sửa cuộc họp này")
```

### 6.2. Sử dụng trong endpoint

```python
# api/endpoints/cuoc_hop.py

@router.get("/{cuoc_hop_id}")
async def get_cuoc_hop(
    cuoc_hop_id: UUID,
    _: bool = Depends(can_view_meeting),  # ← raises 403 if not allowed
    db: Session = Depends(get_db),
):
    return ...

@router.patch("/{cuoc_hop_id}")
async def update_cuoc_hop(
    cuoc_hop_id: UUID,
    payload: CuocHopUpdateSchema,
    _: bool = Depends(can_edit_meeting),
    db: Session = Depends(get_db),
):
    ...
```

---

## 7. FILTERING LIST CUỘC HỌP THEO PHÂN QUYỀN

```python
def filter_cuoc_hop_visible(query, current_user, db):
    """
    Apply WHERE clauses dựa vào quyền:
    - Admin / CCT / PCCT / CHANH_VP / TP CNTT → no filter
    - LĐ ĐV → don_vi_to_chuc_id = user_don_vi
    - Thư ký → don_vi_to_chuc_id IN thu_ky_pham_vi
    - CBCC thường → JOIN thanh_phan WHERE cong_chuc_id = user_id
    """
    user_id = current_user["sub"]
    vai_tro = current_user["vai_tro"]
    platform_roles = current_user.get("platform_roles", [])

    # Toàn quyền
    if vai_tro in ["SUPER_ADMIN", "CHI_CUC_TRUONG", "PHO_CHI_CUC_TRUONG"]:
        return query
    if "CHANH_VP" in platform_roles or "TRUONG_CNTT" in platform_roles:
        return query

    # Build OR conditions
    conditions = []

    # Cuộc họp đơn vị mình (nếu là LĐ ĐV)
    if current_user.get("is_lanh_dao"):
        conditions.append(CuocHop.don_vi_to_chuc_id == current_user["don_vi_id"])

    # Cuộc họp đơn vị mình (nếu là Thư ký HOP)
    if "THU_KY_HOP" in platform_roles:
        thu_ky_don_vi_ids = get_thu_ky_pham_vi(user_id, db)
        if thu_ky_don_vi_ids:
            conditions.append(CuocHop.don_vi_to_chuc_id.in_(thu_ky_don_vi_ids))

    # Cuộc họp được mời / là chủ tọa / là thư ký cuộc họp đó
    invited_subq = db.query(ThanhPhan.cuoc_hop_id).filter(
        ThanhPhan.cong_chuc_id == user_id
    ).subquery()
    conditions.append(CuocHop.id.in_(invited_subq))
    conditions.append(CuocHop.chu_toa_id == user_id)
    conditions.append(CuocHop.thu_ky_id == user_id)

    return query.filter(or_(*conditions))
```

---

## 8. CHECKLIST CẤU HÌNH SAU MIGRATION

```
□ Seed 6 platform_roles static vào public.platform_role
  (CHU_TOA_HOP là dynamic — không seed)
□ Gán role CHANH_VP cho 1 CBCC (Chánh VP hiện tại)
□ Gán role TRUONG_CNTT cho 1 CBCC (Trưởng phòng CNTT)
□ Gán role THU_KY_HOP cho ~14 CBCC (1-2 người/đơn vị)
□ Gán role DANG_VIEN cho các CBCC là Đảng viên (theo danh sách HR)
□ Gán role BI_THU_CHI_BO + PHO_BI_THU cho 14 chi bộ
□ Test JWT: đăng nhập 1 user có role THU_KY_HOP → JWT phải chứa platform_roles
□ Test API: Thư ký Phòng A KHÔNG xem được cuộc họp Phòng B
```

---

## 9. PHẠM VI (`pham_vi`) JSONB FORMAT

Trường `pham_vi` trong `public.cong_chuc_platform_role` lưu thông tin chi tiết phạm vi áp dụng. Helper sub-query lấy role_id theo `ma_role`:

```sql
-- Ví dụ: Thư ký HOP cho 2 đơn vị
INSERT INTO public.cong_chuc_platform_role (cong_chuc_id, platform_role_id, pham_vi)
VALUES (
    '{user_id}',
    (SELECT id FROM public.platform_role WHERE ma_role = 'THU_KY_HOP'),
    '{"don_vi_ids": ["uuid_phong_a", "uuid_doi_b"]}'::jsonb
);

-- Bí thư Chi bộ Phòng CNTT
INSERT INTO public.cong_chuc_platform_role (cong_chuc_id, platform_role_id, pham_vi)
VALUES (
    '{user_id}',
    (SELECT id FROM public.platform_role WHERE ma_role = 'BI_THU_CHI_BO'),
    '{"ten_chi_bo": "Chi bộ Phòng CNTT", "don_vi_id": "uuid_phong_cntt"}'::jsonb
);

-- Đảng viên (không cần pham_vi cụ thể MVP)
INSERT INTO public.cong_chuc_platform_role (cong_chuc_id, platform_role_id, pham_vi)
VALUES (
    '{user_id}',
    (SELECT id FROM public.platform_role WHERE ma_role = 'DANG_VIEN'),
    '{}'::jsonb
);

-- Chánh VP / TP CNTT (toàn Chi cục, pham_vi rỗng)
INSERT INTO public.cong_chuc_platform_role (cong_chuc_id, platform_role_id, pham_vi)
VALUES (
    '{user_id}',
    (SELECT id FROM public.platform_role WHERE ma_role = 'CHANH_VP'),
    '{}'::jsonb
);
```

---

*File này dùng làm authoritative reference cho mọi logic phân quyền trong HKG. Khi cần thêm role mới, cập nhật file này TRƯỚC, rồi mới sinh migration + code.*
