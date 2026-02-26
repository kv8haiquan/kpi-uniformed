# QLDV Implementation - Key Code Examples

## Pattern 1: Import Statement
All three files need the same import:

```python
from app.api.deps import DatabaseDep, ActiveUserDep, is_qldv
```

---

## Pattern 2: READ Endpoints - Allow QLDV with Đơn vị Scope

### Example from danh_gia.py - GET cho-phe-duyet

```python
async def get_danh_sach_cho_phe_duyet(
    db: DatabaseDep, current_user: ActiveUserDep,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    thang: Optional[int] = Query(default=None, ge=1, le=12),
    nam: Optional[int] = Query(default=None, ge=2025),
) -> dict:
    """
    Lấy danh sách tiêu chí chung chờ phê duyệt.
    v2.6: Hỗ trợ 2 cấp - hiển thị đơn chờ cấp 1 và cấp 2
    v3.6: Thêm QLDV - chỉ xem, không duyệt
    """
    is_qldv_user = is_qldv(current_user)

    # Cho phép: lãnh đạo HOẶC QLDV
    if not current_user.is_lanh_dao and not is_qldv_user:
        raise HTTPException(status_code=403, detail=error_response(code="PERM_002", message="Chỉ lãnh đạo hoặc QLDV"))

    # v3.6: QLDV chỉ xem đơn vị của mình (tất cả trạng thái chờ duyệt)
    if is_qldv_user:
        # QLDV: Xem tất cả đơn chờ duyệt trong đơn vị
        stmt = select(DanhGiaThang).options(
            selectinload(DanhGiaThang.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(TieuChiChungDanhGia.tieu_chi),
        ).join(CongChuc).where(
            DanhGiaThang.is_deleted == False,
            CongChuc.don_vi_id == current_user.don_vi_id,
            or_(
                DanhGiaThang.trang_thai_tc == TrangThaiTieuChi.CHO_PHE_DUYET,
                DanhGiaThang.trang_thai_tc == TrangThaiTieuChi.CHO_CAP2,
                DanhGiaThang.trang_thai_tc == None
            )
        ).distinct().order_by(DanhGiaThang.created_at.desc())
    else:
        # Lãnh đạo: theo logic cũ (assigned approver)
        stmt = select(DanhGiaThang).options(
            # ... original logic
        )
    
    # Rest of function continues...
```

### Example from nghi_phep.py - GET cho-phe-duyet

```python
async def get_cho_phe_duyet(
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Lấy danh sách đơn nghỉ phép chờ tôi phê duyệt.
    v3.0: Chỉ 1 cấp - ai được assign làm nguoi_phe_duyet thì duyệt
    v3.6: QLDV xem đơn chờ duyệt trong đơn vị (read-only)
    """
    is_qldv_user = is_qldv(current_user)

    # Query đơn chờ duyệt
    if is_qldv_user:
        # QLDV: Xem tất cả đơn chờ duyệt trong đơn vị
        stmt = (
            select(DangKyNghi)
            .options(
                selectinload(DangKyNghi.cong_chuc).selectinload(CongChuc.don_vi),
                selectinload(DangKyNghi.cong_chuc).selectinload(CongChuc.vai_tro),
                selectinload(DangKyNghi.nguoi_phe_duyet),
            )
            .join(CongChuc)
            .where(DangKyNghi.is_deleted == False)
            .where(DangKyNghi.trang_thai == TrangThaiNghi.CHO_PHE_DUYET)
            .where(CongChuc.don_vi_id == current_user.don_vi_id)
            .order_by(DangKyNghi.created_at.desc())
        )
    else:
        # Lãnh đạo: Chỉ đơn được assign
        stmt = (
            select(DangKyNghi)
            .options(
                # ... same options
            )
            .where(DangKyNghi.is_deleted == False)
            .where(DangKyNghi.trang_thai == TrangThaiNghi.CHO_PHE_DUYET)
            .where(DangKyNghi.nguoi_phe_duyet_id == current_user.id)
            .order_by(DangKyNghi.created_at.desc())
        )
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    data = [build_nghi_phep_response(item) for item in items]
    
    return success_response(data={"items": data})
```

---

## Pattern 3: WRITE Endpoints - Block QLDV with 403

### Example from danh_gia.py - POST phe-duyet

```python
@router.post("/{danh_gia_thang_id}/phe-duyet-tieu-chi")
async def phe_duyet_tieu_chi_chung(
    db: DatabaseDep, current_user: ActiveUserDep,
    danh_gia_thang_id: UUID, payload: PheDuyetTieuChiRequest
) -> dict:
    """
    LĐ phê duyệt tiêu chí chung của CC.
    v2.6: Phê duyệt 2 cấp - Phó ĐT (cấp 1) → ĐT (cấp 2)
    v3.6: Block QLDV - chỉ xem, KHÔNG duyệt
    """
    # Block QLDV
    if is_qldv(current_user):
        raise HTTPException(
            status_code=403,
            detail=error_response(code="PERM_002", message="QLDV không có quyền phê duyệt đánh giá")
        )

    # Rest of approval logic continues...
    stmt = select(DanhGiaThang).options(
        # ... continue with normal logic
    )
```

### Example from nghi_phep.py - POST phe-duyet

```python
@router.post("/{nghi_phep_id}/phe-duyet")
async def phe_duyet_nghi_phep(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    nghi_phep_id: UUID,
    payload: PheDuyetNghiPhepRequest,
) -> dict:
    """
    Phê duyệt đơn nghỉ phép - v3.0: CHỈ 1 CẤP.
    v3.6: Block QLDV - chỉ xem, KHÔNG duyệt
    """
    # Block QLDV
    if is_qldv(current_user):
        raise HTTPException(
            status_code=403,
            detail=error_response(code="PERM_002", message="QLDV không có quyền phê duyệt nghỉ phép")
        )

    # Rest of approval logic continues...
    stmt = (
        select(DangKyNghi)
        # ... continue with normal logic
    )
```

---

## Pattern 4: Helper Functions - Include QLDV for View, Exclude for Edit/Approve

### From bao_cao_xep_loai.py

```python
def check_is_lanh_dao_don_vi(user: CongChuc) -> bool:
    """
    Kiểm tra user có phải là Lãnh đạo đơn vị (ĐT hoặc Phó ĐT hoặc QLDV) không.
    v3.6: Thêm QLDV (read-only)
    """
    if not user.vai_tro:
        return False
    return user.vai_tro.cap_bac in [
        CapBacVaiTro.TRUONG_DON_VI,
        CapBacVaiTro.PHO_DON_VI,
        CapBacVaiTro.QUAN_LY_DON_VI,  # QLDV
    ]


def check_can_view_bao_cao(user: CongChuc) -> bool:
    """
    Kiểm tra user có quyền XEM báo cáo không.
    Quyền xem: QLDV, Phó ĐT, ĐT, Phó CCT, CCT, hoặc user có flag can_view_all_units
    v3.6: Thêm QLDV (read-only với don_vi scope)
    """
    if getattr(user, 'can_view_all_units', False):
        return True
    if not user.vai_tro:
        return False
    return user.vai_tro.cap_bac in [
        CapBacVaiTro.QUAN_LY_DON_VI,  # QLDV - CHỈ XEM (v3.6)
        CapBacVaiTro.PHO_DON_VI,      # Phó Đội trưởng - CHỈ XEM
        CapBacVaiTro.TRUONG_DON_VI,   # Đội trưởng - XEM + SỬA
        CapBacVaiTro.PHO_CHI_CUC_TRUONG,  # Phó CCT - CHỈ XEM
        CapBacVaiTro.CHI_CUC_TRUONG,  # CCT - XEM + DUYỆT
    ]


def check_can_edit_bao_cao(user: CongChuc) -> bool:
    """
    Kiểm tra user có quyền CHỈNH SỬA báo cáo không.

    Quyền sửa: ĐT (lập báo cáo), CCT (phê duyệt)
    v3.6: QLDV KHÔNG có quyền sửa (chỉ xem)
    """
    if not user.vai_tro:
        return False
    return user.vai_tro.cap_bac in [
        CapBacVaiTro.TRUONG_DON_VI,   # Đội trưởng - lập báo cáo
        CapBacVaiTro.CHI_CUC_TRUONG,  # CCT - phê duyệt
        # KHÔNG bao gồm QLDV
    ]


def check_can_approve_bao_cao(user: CongChuc) -> bool:
    """
    Kiểm tra user có quyền PHÊ DUYỆT báo cáo không.
    Quyền duyệt: Chỉ CCT
    v3.6: QLDV KHÔNG có quyền phê duyệt (chỉ xem)
    """
    if not user.vai_tro:
        return False
    return user.vai_tro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG
    # KHÔNG bao gồm QLDV
```

---

## Testing Examples

### Test QLDV View Access (Should PASS)

```python
# Test QLDV can view cho-phe-duyet list
response = client.get(
    "/api/v1/danh-gia/cho-phe-duyet",
    headers={"Authorization": f"Bearer {qldv_token}"}
)
assert response.status_code == 200
# Should return items only from QLDV's don_vi
```

### Test QLDV Approval Block (Should FAIL with 403)

```python
# Test QLDV cannot approve
response = client.post(
    f"/api/v1/danh-gia/{danh_gia_id}/phe-duyet-tieu-chi",
    json={"ghi_chu": "Test"},
    headers={"Authorization": f"Bearer {qldv_token}"}
)
assert response.status_code == 403
assert "QLDV không có quyền phê duyệt đánh giá" in response.json()["detail"]["error"]["message"]
```

---

## Error Messages (Standardized)

All approval endpoints blocked for QLDV return this format:

```python
HTTPException(
    status_code=403,
    detail=error_response(
        code="PERM_002", 
        message="QLDV không có quyền phê duyệt [module_name]"
    )
)
```

Where `[module_name]` is:
- "đánh giá" for danh_gia.py
- "nghỉ phép" for nghi_phep.py
- (bao_cao_xep_loai.py uses helper functions, no direct message)

