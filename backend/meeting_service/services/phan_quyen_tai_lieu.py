"""
phan_quyen_tai_lieu.py
=======================
Phân quyền tài liệu họp hai mức hạn chế — G5.4.

Đây là XÂY MỚI THEO THIẾT KẾ, không phải giữ hành vi cũ. Cột `FILE_VISIBILITY`
của lichkv8 không có dòng nào mang giá trị `LEADER_*` trong 587 file (chỉ
`PUBLIC` = 374 và rỗng = 213), tức cơ chế này chưa từng vận hành thật. Vì thế
không có hành vi cũ nào phải bảo toàn — chỉ có một yêu cầu phải làm cho đúng.

Ba mức, có thứ bậc:

    CONG_KHAI        (0) ai xem được cuộc họp thì xem được tài liệu
    LANH_DAO_DON_VI  (1) thêm điều kiện: là lãnh đạo, phòng/đội trở lên
    LANH_DAO_CHI_CUC (2) chỉ Chi cục trưởng, Phó Chi cục trưởng, quản trị

Ánh xạ sang vai trò nền tảng dùng `vai_tro` và `is_lanh_dao` trong JWT, không
dò chuỗi trên chức vụ — chức vụ là văn bản tự do, mỗi đơn vị ghi một kiểu.

Hai ngoại lệ có chủ ý:

* **Người tải lên luôn xem lại được file của mình.** Thư ký nâng mức một tài
  liệu lên `LANH_DAO_CHI_CUC` rồi không mở lại được để kiểm tra là vô lý, và
  họ vốn đã có file trong tay.
* **Quyền hạn chế KHÔNG nới quyền xem cuộc họp.** Đây là bộ lọc chồng thêm
  lên `_can_view_cuoc_hop`, không thay thế: lãnh đạo đơn vị khác vẫn không vào
  được cuộc họp không liên quan, nên cũng không thấy tài liệu của nó.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from shared.auth import TokenPayload

CONG_KHAI = "CONG_KHAI"
LANH_DAO_DON_VI = "LANH_DAO_DON_VI"
LANH_DAO_CHI_CUC = "LANH_DAO_CHI_CUC"

# Phải khớp CHECK `ck_tai_lieu_phan_quyen` (migration meeting_023). Lệch một
# giá trị là người dùng chọn xong nhận lỗi 500 thay vì thông báo tử tế.
PHAN_QUYEN_VALUES = [CONG_KHAI, LANH_DAO_DON_VI, LANH_DAO_CHI_CUC]

BAC = {CONG_KHAI: 0, LANH_DAO_DON_VI: 1, LANH_DAO_CHI_CUC: 2}

NHAN = {
    CONG_KHAI: "Công khai nội bộ",
    LANH_DAO_DON_VI: "Lãnh đạo phòng/đội trở lên",
    LANH_DAO_CHI_CUC: "Lãnh đạo Chi cục",
}

MO_TA = {
    CONG_KHAI: "Ai xem được cuộc họp thì xem được tài liệu.",
    LANH_DAO_DON_VI: "Chỉ lãnh đạo phòng/đội trở lên, cộng lãnh đạo Chi cục "
                     "và quản trị.",
    LANH_DAO_CHI_CUC: "Chỉ Chi cục trưởng, Phó Chi cục trưởng và quản trị.",
}

VAI_TRO_LANH_DAO_CHI_CUC = {
    "CCT", "CHI_CUC_TRUONG", "PCCT", "PHO_CHI_CUC_TRUONG",
}
VAI_TRO_QUAN_TRI = {"ADMIN", "SUPER_ADMIN"}


def bac_nguoi_xem(user: TokenPayload) -> int:
    """Bậc cao nhất mà người này với tới. Xem `BAC` để đối chiếu."""
    if (user.is_admin
            or user.vai_tro in VAI_TRO_QUAN_TRI
            or user.vai_tro in VAI_TRO_LANH_DAO_CHI_CUC):
        return BAC[LANH_DAO_CHI_CUC]
    if user.is_lanh_dao:
        return BAC[LANH_DAO_DON_VI]
    return BAC[CONG_KHAI]


def chuan_hoa(muc: Optional[str]) -> str:
    """Giá trị lạ hoặc rỗng thì coi là công khai — đúng như CSDL mặc định."""
    return muc if muc in BAC else CONG_KHAI


def xem_duoc(
    muc: Optional[str], user: TokenPayload,
    *, nguoi_tai_len_id: Optional[UUID] = None,
) -> bool:
    """Người này có vượt được mức hạn chế của tài liệu không.

    KHÔNG bao gồm quyền xem cuộc họp — nơi gọi phải kiểm điều đó trước.
    """
    if nguoi_tai_len_id is not None and str(nguoi_tai_len_id) == user.sub:
        return True
    return bac_nguoi_xem(user) >= BAC[chuan_hoa(muc)]


def muc_dat_duoc(user: TokenPayload) -> list[str]:
    """Các mức người này được PHÉP ĐẶT cho một tài liệu.

    Không cho đặt mức cao hơn bậc của chính mình: đặt xong rồi tự mình không
    mở lại được là cách chắc chắn nhất để mất tài liệu.
    """
    tran = bac_nguoi_xem(user)
    return [m for m in PHAN_QUYEN_VALUES if BAC[m] <= tran]


def duoc_quan_ly_tai_lieu(cuoc_hop, user: TokenPayload) -> bool:
    """Ai được tải lên / sửa / xoá tài liệu của một cuộc họp hoặc sự kiện lịch.

    Cuộc họp Họp Không Giấy: chủ toạ, thư ký, quản trị, TRUONG_CNTT, THU_KY_HOP
    — giữ nguyên luật cũ.

    Sự kiện lịch công tác: quản trị lịch hoặc người tạo sự kiện. Luật của HKG
    không dùng được ở đây — sự kiện lịch thường không có thư ký, còn chủ toạ là
    lãnh đạo chủ trì chứ không phải người đi nộp tài liệu; người nộp là Văn
    phòng, tức người đã tạo dòng lịch đó. Dùng đúng luật đang áp cho nút Sửa
    lịch để hai thao tác không lệch nhau.
    """
    # Nhập tại chỗ: `lich_cong_tac_service` không phụ thuộc module này, nhập ở
    # đầu file sẽ tạo vòng nhập khi module kia dùng tới hằng số phân quyền.
    from meeting_service.services.lich_cong_tac_service import la_quan_tri_lich

    user_id = UUID(user.sub)
    if getattr(cuoc_hop, "nguon", "HKG") == "LICH_CONG_TAC":
        return bool(la_quan_tri_lich(user) or cuoc_hop.created_by == user_id)

    return bool(
        user.is_admin
        or user.vai_tro in ("SUPER_ADMIN", "ADMIN")
        or "TRUONG_CNTT" in (user.platform_roles or [])
        or cuoc_hop.chu_toa_id == user_id
        or cuoc_hop.thu_ky_id == user_id
        or "THU_KY_HOP" in (user.platform_roles or [])
    )


def loc_xem_duoc(tai_lieu: list, user: TokenPayload) -> list:
    """Bỏ khỏi danh sách những tài liệu người này không được xem."""
    return [
        t for t in tai_lieu
        if xem_duoc(t.phan_quyen, user, nguoi_tai_len_id=t.created_by)
    ]
