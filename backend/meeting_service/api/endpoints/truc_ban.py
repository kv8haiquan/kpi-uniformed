"""
api/endpoints/truc_ban.py
==========================
Lịch trực ban — G4.7 (ma trận, nhập tay, nộp) và G4.8 (nhập từ Excel).

Nhập Excel đi hai bước: đọc file → **xem trước** → mới ghi. Hệ cũ ghi thẳng,
sai một dòng là hỏng cả bảng và không biết hỏng ở đâu.
"""

from datetime import date as date_type
from io import BytesIO
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)

from meeting_service.dependencies import CurrentUserDep, DatabaseDep
from meeting_service.schemas.truc_ban import (
    DongNhapExcel,
    KetQuaXemTruoc,
    TrucBanCreate,
    TrucBanNop,
    TrucBanUpdate,
    YeuCauGhiNhap,
)
from meeting_service.services.lich_cong_tac_service import LoiNghiepVu
from meeting_service.services.truc_ban_service import (
    TrucBanService,
    bac_chuc_vu,
    tuan_chua,
)

router = APIRouter(prefix="/truc-ban", tags=["Trực ban"])

# File mẫu mang sang từ lichkv8, giữ nguyên để đơn vị dùng lại bản đang quen.
#
# Đặt TRONG gói backend chứ không trỏ sang docs/: thư mục docs không nằm trong
# git nên bản triển khai sẽ không có file, và endpoint tải mẫu sẽ 404 trên
# production dù chạy tốt trên máy phát triển.
MAU_IMPORT = (Path(__file__).resolve().parents[2]
              / "static" / "Mau_import_lich_truc_ban.xlsx")


def _loi(e: LoiNghiepVu) -> HTTPException:
    return HTTPException(
        e.http,
        detail={"success": False,
                "error": {"code": e.ma, "message": e.thong_diep}})


def _khoang(tu_ngay: Optional[date_type], den_ngay: Optional[date_type],
            tuan: Optional[str]) -> tuple[date_type, date_type]:
    """Ưu tiên khoảng ngày tự chọn; không có thì lấy theo tuần."""
    if tu_ngay and den_ngay:
        return tu_ngay, den_ngay
    lech = {"truoc": -1, "nay": 0, "sau": 1}.get(tuan or "nay", 0)
    return tuan_chua(date_type.today(), lech)


# ── xem ───────────────────────────────────────────────────────────────

@router.get("/tru-so", summary="Danh mục trụ sở trực ban")
async def danh_muc_tru_so(db: DatabaseDep, user: CurrentUserDep):
    return {"success": True,
            "data": await TrucBanService(db).danh_muc_tru_so()}


@router.get("/ma-tran", summary="Bảng ma trận trực ban")
async def ma_tran(
    db: DatabaseDep,
    user: CurrentUserDep,
    tu_ngay: Optional[date_type] = Query(None, alias="tu-ngay"),
    den_ngay: Optional[date_type] = Query(None, alias="den-ngay"),
    tuan: Optional[str] = Query(None, description="truoc | nay | sau"),
    don_vi_id: Optional[UUID] = Query(None, alias="don-vi-id"),
):
    bd, kt = _khoang(tu_ngay, den_ngay, tuan)
    try:
        kq = await TrucBanService(db).ma_tran(bd, kt, user=user,
                                              don_vi_id=don_vi_id)
    except LoiNghiepVu as e:
        raise _loi(e) from e
    return {"success": True, "data": kq}


@router.get("/danh-sach", summary="Dữ liệu chi tiết dạng bảng phẳng")
async def danh_sach(
    db: DatabaseDep,
    user: CurrentUserDep,
    tu_ngay: Optional[date_type] = Query(None, alias="tu-ngay"),
    den_ngay: Optional[date_type] = Query(None, alias="den-ngay"),
    tuan: Optional[str] = Query(None),
    tru_so_id: Optional[UUID] = Query(None, alias="tru-so-id"),
):
    bd, kt = _khoang(tu_ngay, den_ngay, tuan)
    return {"success": True,
            "data": await TrucBanService(db).danh_sach(bd, kt,
                                                       tru_so_id=tru_so_id)}


@router.get("/van-ban", summary="Bản text để sao chép sang Zalo")
async def van_ban(
    db: DatabaseDep,
    user: CurrentUserDep,
    tu_ngay: Optional[date_type] = Query(None, alias="tu-ngay"),
    den_ngay: Optional[date_type] = Query(None, alias="den-ngay"),
    tuan: Optional[str] = Query(None),
):
    bd, kt = _khoang(tu_ngay, den_ngay, tuan)
    return {"success": True,
            "data": {"van_ban": await TrucBanService(db).van_ban(bd, kt)}}


# ── ghi ───────────────────────────────────────────────────────────────

@router.post("/", status_code=status.HTTP_201_CREATED,
             summary="Thêm một người trực")
async def them(du_lieu: TrucBanCreate, db: DatabaseDep, user: CurrentUserDep):
    try:
        item = await TrucBanService(db).them(
            du_lieu.model_dump(exclude_unset=True), user=user)
    except LoiNghiepVu as e:
        raise _loi(e) from e
    return {"success": True, "data": item, "message": "Đã thêm người trực"}


@router.patch("/{truc_ban_id}", summary="Sửa một người trực")
async def sua(truc_ban_id: UUID, thay_doi: TrucBanUpdate,
              db: DatabaseDep, user: CurrentUserDep):
    try:
        item = await TrucBanService(db).sua(
            truc_ban_id, thay_doi.model_dump(exclude_unset=True), user=user)
    except LoiNghiepVu as e:
        raise _loi(e) from e
    return {"success": True, "data": item, "message": "Đã lưu"}


@router.delete("/{truc_ban_id}", summary="Xoá một người trực")
async def xoa(truc_ban_id: UUID, db: DatabaseDep, user: CurrentUserDep):
    try:
        await TrucBanService(db).xoa(truc_ban_id, user=user)
    except LoiNghiepVu as e:
        raise _loi(e) from e
    return {"success": True, "data": None, "message": "Đã xoá"}


@router.post("/nop", summary="Nộp chính thức một ô (khoá lại)")
async def nop(du_lieu: TrucBanNop, db: DatabaseDep, user: CurrentUserDep):
    try:
        kq = await TrucBanService(db).nop(du_lieu.ngay_truc,
                                          du_lieu.tru_so_id, user=user)
    except LoiNghiepVu as e:
        raise _loi(e) from e
    return {"success": True, "data": kq, "message": "Đã nộp lịch trực"}


@router.post("/mo-khoa", summary="Mở khoá ô đã nộp (chỉ quản trị lịch)")
async def mo_khoa(du_lieu: TrucBanNop, db: DatabaseDep, user: CurrentUserDep):
    try:
        kq = await TrucBanService(db).mo_khoa(du_lieu.ngay_truc,
                                              du_lieu.tru_so_id, user=user)
    except LoiNghiepVu as e:
        raise _loi(e) from e
    return {"success": True, "data": kq, "message": "Đã mở khoá"}


# ── xuất Excel ────────────────────────────────────────────────────────

@router.get("/xuat-excel", summary="Xuất bảng trực ban ra Excel")
async def xuat_excel(
    db: DatabaseDep,
    user: CurrentUserDep,
    tu_ngay: Optional[date_type] = Query(None, alias="tu-ngay"),
    den_ngay: Optional[date_type] = Query(None, alias="den-ngay"),
    tuan: Optional[str] = Query(None),
):
    bd, kt = _khoang(tu_ngay, den_ngay, tuan)
    svc = TrucBanService(db)
    try:
        mt = await svc.ma_tran(bd, kt, user=user)
    except LoiNghiepVu as e:
        raise _loi(e) from e

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Truc ban"

    cot = ["Ngày", "Thứ"] + [t["ten_tru_so"] for t in mt["tru_so"]]

    ws.append([f"LỊCH TRỰC BAN ({bd:%d/%m/%Y} – {kt:%d/%m/%Y})"])
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(cot))
    ws["A1"].font = Font(bold=True, size=13)
    ws["A1"].alignment = Alignment(horizontal="center")
    ws.append([])
    ws.append(cot)

    dong_tieu_de = ws.max_row
    vien = Border(*[Side(style="thin")] * 4)
    for c in range(1, len(cot) + 1):
        o = ws.cell(row=dong_tieu_de, column=c)
        o.font = Font(bold=True)
        o.fill = PatternFill("solid", fgColor="D9E1F2")
        o.alignment = Alignment(horizontal="center", vertical="center",
                                wrap_text=True)
        o.border = vien

    mau_cuoi_tuan = PatternFill("solid", fgColor="FFF7E6")

    for h in mt["hang"]:
        hang = [h["ngay"].strftime("%d/%m/%Y"), h["thu"]]
        for o in h["o"]:
            hang.append("\n".join(
                " · ".join(filter(None, [n["ho_ten"], n["chuc_vu"],
                                         n["so_dien_thoai"]]))
                for n in o["nguoi"]))
        ws.append(hang)
        for c in range(1, len(cot) + 1):
            cell = ws.cell(row=ws.max_row, column=c)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = vien
            if h["cuoi_tuan"]:
                cell.fill = mau_cuoi_tuan

    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 10
    for i in range(len(mt["tru_so"])):
        ws.column_dimensions[get_column_letter(3 + i)].width = 30
    ws.freeze_panes = ws.cell(row=dong_tieu_de + 1, column=3)

    buf = BytesIO()
    wb.save(buf)
    ten_file = f"truc-ban-{bd:%Y%m%d}-{kt:%Y%m%d}.xlsx"
    return Response(
        content=buf.getvalue(),
        media_type=("application/vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet"),
        headers={"Content-Disposition": f'attachment; filename="{ten_file}"'},
    )


# ── nhập từ Excel (G4.8) ──────────────────────────────────────────────

# Tên cột chấp nhận được. Hệ cũ nhận nhiều biến thể vì mỗi đơn vị sửa file mẫu
# một kiểu; giữ đúng độ rộng đó, thêm chuẩn hoá bỏ dấu để khỏi liệt kê vô tận.
_COT = {
    "ngay_truc": ["ngay truc", "ngay", "ngay tr"],
    "ma_tru_so": ["unit code", "ma tru so", "ma don vi", "unitcode"],
    "ho_ten": ["ho ten", "ho va ten", "nguoi truc"],
    "chuc_vu": ["chuc vu", "chuc danh"],
    "so_dien_thoai": ["so dien thoai", "dien thoai", "sdt", "phone"],
    "ghi_chu": ["ghi chu", "note", "ghichu"],
    "ca_truc": ["ca truc", "ca"],
    "loai_truc": ["loai truc", "loai"],
}


def _chuan_ten_cot(s: object) -> str:
    import re
    import unicodedata
    t = unicodedata.normalize("NFD", str(s or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def _doc_ngay(v: object) -> Optional[date_type]:
    """Nhận cả ô ngày thật của Excel lẫn chuỗi dd/mm/yyyy."""
    from datetime import datetime
    if v is None or str(v).strip() == "":
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date_type):
        return v
    s = str(v).strip()
    for khuon in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, khuon).date()
        except ValueError:
            continue
    return None


@router.get("/mau-import", summary="Tải file Excel mẫu")
async def mau_import(user: CurrentUserDep):
    if not MAU_IMPORT.exists():
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {
                "code": "THIEU_FILE_MAU",
                "message": "Chưa có file mẫu trên máy chủ"}})
    return Response(
        content=MAU_IMPORT.read_bytes(),
        media_type=("application/vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet"),
        headers={"Content-Disposition":
                 'attachment; filename="Mau_import_lich_truc_ban.xlsx"'},
    )


@router.post("/nhap/xem-truoc", summary="Đọc file Excel và xem trước")
async def xem_truoc(db: DatabaseDep, user: CurrentUserDep,
                    file: UploadFile = File(...)):
    """Đọc và kiểm tra, KHÔNG ghi gì.

    Trả về từng dòng kèm lỗi của riêng dòng đó. Một dòng hỏng không làm hỏng
    cả file — người dùng thấy rõ dòng nào sai vì sao rồi tự quyết định.
    """
    if not (file.filename or "").lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {
                "code": "SAI_DINH_DANG",
                "message": "Chỉ nhận file .xlsx"}})

    noi_dung = await file.read()
    if len(noi_dung) > 10 * 1024 * 1024:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {
                "code": "FILE_QUA_LON", "message": "File tối đa 10MB"}})

    from openpyxl import load_workbook

    try:
        wb = load_workbook(BytesIO(noi_dung), data_only=True, read_only=True)
    except Exception as e:  # openpyxl ném nhiều loại lỗi khác nhau
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {
                "code": "KHONG_DOC_DUOC",
                "message": f"Không đọc được file Excel: {e}"}}) from e

    ws = (wb["IMPORT_LICH_TRUC"] if "IMPORT_LICH_TRUC" in wb.sheetnames
          else wb.worksheets[0])

    hang = list(ws.iter_rows(values_only=True))
    if not hang:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {
                "code": "FILE_RONG", "message": "File không có dữ liệu"}})

    tieu_de = [_chuan_ten_cot(x) for x in hang[0]]
    vi_tri: dict[str, int] = {}
    for khoa, bien_the in _COT.items():
        for i, t in enumerate(tieu_de):
            if t in bien_the:
                vi_tri[khoa] = i
                break

    thieu = [k for k in ("ngay_truc", "ma_tru_so", "ho_ten")
             if k not in vi_tri]
    if thieu:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {
                "code": "THIEU_COT",
                "message": f"File thiếu cột bắt buộc: {', '.join(thieu)}"}})

    tru_so = {t["ma_tru_so"].upper(): t
              for t in await TrucBanService(db).danh_muc_tru_so()}

    ket_qua: list[DongNhapExcel] = []
    for so_dong, r in enumerate(hang[1:], start=2):
        def o(khoa: str) -> object:
            i = vi_tri.get(khoa)
            return r[i] if i is not None and i < len(r) else None

        if all(x is None or str(x).strip() == ""
               for x in (o("ngay_truc"), o("ma_tru_so"), o("ho_ten"))):
            continue  # dòng trống ở cuối file

        loi: list[str] = []
        ngay = _doc_ngay(o("ngay_truc"))
        if ngay is None:
            loi.append("Ngày trực không đọc được (cần dd/mm/yyyy)")

        ma = str(o("ma_tru_so") or "").strip().upper()
        ts = tru_so.get(ma)
        if ts is None:
            loi.append(f"Mã trụ sở '{ma}' không có trong danh mục")

        ho_ten = str(o("ho_ten") or "").strip()
        if not ho_ten:
            loi.append("Thiếu họ tên")

        sdt = o("so_dien_thoai")
        # Excel hay đổi số điện thoại thành số thực rồi mất số 0 đứng đầu.
        sdt_txt = ("" if sdt is None else
                   str(int(sdt)) if isinstance(sdt, float) and sdt.is_integer()
                   else str(sdt)).strip()

        ket_qua.append(DongNhapExcel(
            dong=so_dong,
            ngay_truc=ngay,
            ma_tru_so=ma or None,
            tru_so_id=ts["id"] if ts else None,
            ten_tru_so=ts["ten_tru_so"] if ts else None,
            ho_ten=ho_ten or None,
            chuc_vu=(str(o("chuc_vu")).strip() if o("chuc_vu") else None),
            so_dien_thoai=sdt_txt or None,
            ca_truc=str(o("ca_truc") or "CA_NGAY").strip().upper(),
            loai_truc=str(o("loai_truc") or "CUOI_TUAN").strip().upper(),
            ghi_chu=(str(o("ghi_chu")).strip() if o("ghi_chu") else None),
            hop_le=not loi,
            loi=loi,
        ))

    return {"success": True, "data": KetQuaXemTruoc(
        tong_dong=len(ket_qua),
        so_hop_le=sum(1 for d in ket_qua if d.hop_le),
        so_loi=sum(1 for d in ket_qua if not d.hop_le),
        dong=ket_qua,
    )}


@router.post("/nhap/ghi", summary="Ghi các dòng đã xem trước")
async def ghi_nhap(du_lieu: YeuCauGhiNhap, db: DatabaseDep,
                   user: CurrentUserDep):
    from sqlalchemy import update as sa_update

    from meeting_service.models.lich_cong_tac import TrucBan

    svc = TrucBanService(db)
    hop_le = [d for d in du_lieu.dong if d.hop_le and d.tru_so_id and d.ngay_truc]
    if not hop_le:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {
                "code": "KHONG_CO_DONG_HOP_LE",
                "message": "Không có dòng nào hợp lệ để ghi"}})

    # Kiểm quyền và khoá TRƯỚC khi ghi dòng nào — ghi được nửa file rồi mới
    # báo lỗi là tình huống tệ nhất, không biết phần nào đã vào.
    o_can_ghi = {(d.ngay_truc, d.tru_so_id) for d in hop_le}
    try:
        for ngay, ts in sorted(o_can_ghi, key=lambda x: (x[0], str(x[1]))):
            await svc._kiem_tra_sua(ts, user)          # noqa: SLF001
            await svc._chan_khi_da_khoa(ngay, ts)      # noqa: SLF001
    except LoiNghiepVu as e:
        raise _loi(e) from e

    if du_lieu.ghi_de:
        for ngay, ts in o_can_ghi:
            await db.execute(
                sa_update(TrucBan)
                .where(TrucBan.ngay_truc == ngay, TrucBan.tru_so_id == ts,
                       TrucBan.is_deleted.is_(False))
                .values(is_deleted=True, updated_by=UUID(user.sub)))

    for d in hop_le:
        db.add(TrucBan(
            ngay_truc=d.ngay_truc, tru_so_id=d.tru_so_id,
            ho_ten=d.ho_ten or "", chuc_vu=d.chuc_vu,
            so_dien_thoai=d.so_dien_thoai,
            ca_truc=d.ca_truc or "CA_NGAY",
            loai_truc=d.loai_truc or "CUOI_TUAN",
            ghi_chu=d.ghi_chu, trang_thai="NHAP",
            created_by=UUID(user.sub), updated_by=UUID(user.sub)))

    from meeting_service.services.audit_log_service import ghi_audit
    await ghi_audit(
        db, hanh_dong="NHAP_EXCEL_TRUC_BAN", nguoi_thuc_hien_id=UUID(user.sub),
        doi_tuong_loai="TRUC_BAN",
        chi_tiet={"so_dong": len(hop_le), "ghi_de": du_lieu.ghi_de,
                  "so_o": len(o_can_ghi)})
    await db.commit()

    return {"success": True,
            "data": {"da_ghi": len(hop_le), "so_o": len(o_can_ghi)},
            "message": f"Đã ghi {len(hop_le)} dòng"}


@router.get("/thu-tu-chuc-vu", summary="Xem thứ tự sắp xếp theo chức vụ")
async def thu_tu_chuc_vu(user: CurrentUserDep,
                         chuc_vu: str = Query(..., alias="chuc-vu")):
    """Công cụ tra nhanh khi thấy thứ tự trong bảng có vẻ sai."""
    return {"success": True,
            "data": {"chuc_vu": chuc_vu, "bac": bac_chuc_vu(chuc_vu)}}
