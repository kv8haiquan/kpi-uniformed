"""
app/api/v1/endpoints/in_bang_ke.py
===================================
API Endpoints in bảng kê cá nhân (phiếu đánh giá + bảng kê công việc).

Endpoints:
1. GET /api/v1/in-bang-ke/phieu-danh-gia/{thang}/{nam} - In phiếu đánh giá tháng (PL-01A hoặc PL-01B)
2. GET /api/v1/in-bang-ke/bang-ke-cong-viec/{thang}/{nam} - In bảng kê công việc tháng (PL-02)
3. GET /api/v1/in-bang-ke/phieu-danh-gia-quy/{quy}/{nam} - In phiếu đánh giá quý (PL-01A hoặc PL-01B)
4. GET /api/v1/in-bang-ke/bang-ke-cong-viec-quy/{quy}/{nam} - In bảng kê công việc quý (PL-02)

Output: DOCX file download

Version: 1.1.0 (16/04/2026)
"""

import io
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from app.api.deps import DatabaseDep, ActiveUserDep
from app.models.user_org import CongChuc
from app.models.kpi_submission import KeKhaiCongViec, TrangThaiKeKhai
from app.models.kpi_assessment import DanhGiaThang, TieuChiChungDanhGia, LanhDaoChiSo
from app.models.leader_kpi import KeKhaiLanhDao, TrangThaiKeKhaiLD, TrangThaiHoanThanh
from app.models.task_catalog import DanhMucSpCongViec

logger = logging.getLogger(__name__)

router = APIRouter()

TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent.parent / "templates"


# =============================================================================
# HELPER: SET FONT TIMES NEW ROMAN
# =============================================================================

def set_times_new_roman(run):
    """
    Set font Times New Roman cho run (bao gồm tiếng Việt có dấu).
    Phải set cả eastAsia để áp dụng cho tiếng Việt.
    """
    run.font.name = 'Times New Roman'
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:ascii'), 'Times New Roman')
    rFonts.set(qn('w:hAnsi'), 'Times New Roman')
    rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    rFonts.set(qn('w:cs'), 'Times New Roman')


def set_cell_font_times_new_roman(cell):
    """
    Set font Times New Roman cho tất cả runs trong 1 cell.
    """
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            set_times_new_roman(run)


def replace_in_runs(paragraph, old_text: str, new_text: str) -> bool:
    """
    Replace text trong runs của paragraph, giữ nguyên cấu trúc runs khác.
    Tránh bug: khi template có nhiều runs (equation, subscript/superscript),
    việc replace toàn bộ paragraph.text sẽ làm mất format.

    Strategy:
    - old_text có thể bị tách ra nhiều runs (VD: "……….(%)" = run[6]="………." + run[7-9]="(%)")
    - Trước tiên tìm run chứa phần chính (dấu chấm placeholder)
    - Replace phần đó thành giá trị mới
    - Nếu old_text có phần tail (VD: "(%)", ".)"), tìm và clear các run chứa tail

    Returns:
        True nếu đã replace, False nếu không tìm thấy old_text
    """
    replaced = False

    # Case 1: old_text hoàn toàn trong 1 run (easy case)
    for run in paragraph.runs:
        if old_text in run.text:
            run.text = run.text.replace(old_text, new_text)
            set_times_new_roman(run)
            return True

    # Case 2: old_text bị tách ra nhiều runs (complex case)
    # VD: "……….(%)" → run[6]="): ………." + run[7-9]="(%)"
    # Strategy: tìm run chứa dấu chấm (……….hoặc …………), replace thành new_text, clear run chứa "(%)hoặc ."

    # Xác định placeholder core (dấu chấm) và tail ((...) hoặc.)
    # Các placeholder trong template:
    # - "……….(%)" → core="……….", tail="(%)"
    # - "…………………………." → core="…………………………..", tail=""

    # Tách old_text thành core và tail
    if "(%)" in old_text:
        core = old_text.replace("(%)", "")
        tail = "(%)"
    elif old_text.endswith("."):
        core = old_text
        tail = ""
    else:
        core = old_text
        tail = ""

    # Tìm run chứa core hoặc một phần của core
    for i, run in enumerate(paragraph.runs):
        if core in run.text:
            # Replace core thành new_text
            run.text = run.text.replace(core, new_text)
            set_times_new_roman(run)
            replaced = True

            # Nếu có tail, tìm và clear các run chứa tail
            if tail:
                for j in range(i+1, len(paragraph.runs)):
                    next_run = paragraph.runs[j]
                    if tail in next_run.text:
                        next_run.text = next_run.text.replace(tail, "")
                        break
                    # Nếu tail bị tách thành nhiều run (VD: "(", "%", ")"), clear từng phần
                    elif any(char in next_run.text for char in tail):
                        next_run.text = ""

            return True

        # Nếu run chứa dấu chấm (placeholder bị tách ra nhiều runs)
        # VD: "…………………………….." → run[2]="…………" + run[3]="……………….."
        # Strategy: tìm run đầu tiên chứa dấu "…" → replace thành new_text, clear các run tiếp theo chứa "…"
        elif "…" in run.text:
            # Replace dấu chấm thành new_text
            run.text = run.text.replace("…", "").replace(".", "") + new_text
            set_times_new_roman(run)
            replaced = True

            # Clear các run tiếp theo chứa dấu "…" hoặc "."
            for j in range(i+1, len(paragraph.runs)):
                next_run = paragraph.runs[j]
                if "…" in next_run.text or (next_run.text and next_run.text.strip() == "."):
                    next_run.text = ""

            # Nếu có tail (VD: "(%)", clear luôn)
            if tail:
                for j in range(i+1, len(paragraph.runs)):
                    next_run = paragraph.runs[j]
                    if any(char in next_run.text for char in tail):
                        next_run.text = ""

            return True

    return replaced


# =============================================================================
# HELPER: REPLACE PLACEHOLDER IN DOCX
# =============================================================================

def replace_placeholder_in_docx(doc: Document, placeholder: str, value: str):
    """
    Replace {{placeholder}} trong tất cả paragraphs của document.
    Áp dụng font Times New Roman cho text mới.
    """
    for para in doc.paragraphs:
        if placeholder in para.text:
            # Merge all runs để tránh bị split text
            full_text = para.text
            for run in para.runs:
                run.text = ""
            if para.runs:
                para.runs[0].text = full_text.replace(placeholder, value)
                set_times_new_roman(para.runs[0])
            else:
                para.text = full_text.replace(placeholder, value)

    # Replace trong tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    if placeholder in para.text:
                        full_text = para.text
                        for run in para.runs:
                            run.text = ""
                        if para.runs:
                            para.runs[0].text = full_text.replace(placeholder, value)
                            set_times_new_roman(para.runs[0])
                        else:
                            para.text = full_text.replace(placeholder, value)


# =============================================================================
# ENDPOINT 1: IN PHIẾU ĐÁNH GIÁ (PL-01A hoặc PL-01B)
# =============================================================================

@router.get("/phieu-danh-gia/{thang}/{nam}")
async def export_phieu_danh_gia(
    thang: int,
    nam: int,
    db: DatabaseDep,
    current_user: ActiveUserDep,
):
    """
    Xuất phiếu đánh giá cá nhân (PL-01A hoặc PL-01B) cho tháng/năm chỉ định.

    Auto-detect is_lanh_dao của user hiện tại:
    - is_lanh_dao = False → dùng template PL-01A (CC không lãnh đạo)
    - is_lanh_dao = True → dùng template PL-01B (Lãnh đạo)

    Args:
        thang: Tháng (1-12)
        nam: Năm (>= 2020)
        db: Database session
        current_user: User hiện tại (từ JWT)

    Returns:
        StreamingResponse: File DOCX download
    """
    # Validation
    if not (1 <= thang <= 12):
        raise HTTPException(status_code=400, detail="Tháng không hợp lệ (1-12)")
    if nam < 2020 or nam > 2100:
        raise HTTPException(status_code=400, detail="Năm không hợp lệ")

    # Load user với relationships
    stmt = (
        select(CongChuc)
        .options(
            selectinload(CongChuc.don_vi),
            selectinload(CongChuc.vai_tro),
        )
        .where(CongChuc.id == current_user.id)
    )
    result = await db.execute(stmt)
    cc = result.scalar_one_or_none()
    if not cc:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin công chức")

    # Lấy dữ liệu đánh giá tháng
    stmt_dg = (
        select(DanhGiaThang)
        .where(
            and_(
                DanhGiaThang.cong_chuc_id == cc.id,
                DanhGiaThang.thang == thang,
                DanhGiaThang.nam == nam,
            )
        )
    )
    result_dg = await db.execute(stmt_dg)
    danh_gia = result_dg.scalar_one_or_none()

    # Lấy tiêu chí chung (phải JOIN qua DanhGiaThang vì TieuChiChungDanhGia không có cong_chuc_id)
    tieu_chi_list = []
    diem_tieu_chi = 0
    if danh_gia:
        stmt_tc = (
            select(TieuChiChungDanhGia)
            .where(TieuChiChungDanhGia.danh_gia_thang_id == danh_gia.id)
            .options(selectinload(TieuChiChungDanhGia.tieu_chi))
        )
        result_tc = await db.execute(stmt_tc)
        tieu_chi_list = result_tc.scalars().all()

        # Tính điểm tiêu chí chung (dùng is_achieved_ld nếu có, không thì is_achieved_cc)
        diem_tieu_chi = sum([
            float(tc.diem_phe_duyet or tc.diem_tu_cham or 0)
            for tc in tieu_chi_list
        ])

    # Chọn template
    is_lanh_dao = cc.is_lanh_dao or False
    template_name = "PL-Mẫu số 01B-LĐ.docx" if is_lanh_dao else "PL-Mẫu số 01A-CC.docx"
    template_path = TEMPLATES_DIR / template_name

    if not template_path.exists():
        raise HTTPException(status_code=500, detail=f"Template {template_name} không tồn tại")

    # Load template
    doc = Document(template_path)

    # Replace placeholders
    ky_danh_gia = f"Tháng {thang}/{nam}"
    ho_ten = cc.ho_ten or "N/A"
    chuc_vu = cc.chuc_vu or "Công chức"
    don_vi = cc.don_vi.ten_don_vi if cc.don_vi else "N/A"
    diem_tieu_chi_str = f"{diem_tieu_chi:.2f}"

    # Tính điểm tổng (nếu có danh_gia)
    diem_tong_str = "Chưa có dữ liệu"
    if danh_gia and danh_gia.diem_tong is not None:
        diem_tong_str = f"{float(danh_gia.diem_tong):.2f}"

    replace_placeholder_in_docx(doc, "{{ky_danh_gia}}", ky_danh_gia)
    replace_placeholder_in_docx(doc, "{{ho_ten}}", ho_ten)
    replace_placeholder_in_docx(doc, "{{chuc_vu}}", chuc_vu)
    replace_placeholder_in_docx(doc, "{{don_vi}}", don_vi)
    replace_placeholder_in_docx(doc, "{{diem_tieu_chi}}", diem_tieu_chi_str)
    replace_placeholder_in_docx(doc, "{{diem_tong}}", diem_tong_str)

    # === Tính điểm nhiệm vụ REUSE logic từ xep_loai_moi.py ===
    # Import hàm tính điểm KPI 70 (production logic)
    from app.api.v1.endpoints.xep_loai_moi import tinh_diem_kpi_70, tinh_diem_kpi_70_lanh_dao

    # Gọi hàm tính điểm (tam_tinh=False vì cần kết quả chính thức)
    diem_a = None
    diem_b = None
    diem_c = None
    diem_d = None
    diem_dd = None
    diem_e = None
    diem_kpi_nhiem_vu = None

    try:
        if is_lanh_dao:
            # Lãnh đạo: dùng công thức 6 chỉ số (a,b,c,d,đ,e)
            kpi_data = await tinh_diem_kpi_70_lanh_dao(db, cc.id, thang, nam, tam_tinh=False)
            # Cap tỷ lệ % ở 100% (phục vụ hiển thị trong phiếu đánh giá)
            diem_a = min(kpi_data.get("a_so_luong", 0) * 100, 100.0)  # a: tỷ lệ hoàn thành
            diem_b = min(kpi_data.get("b_tien_do", 0) * 100, 100.0)   # b: tỷ lệ tiến độ
            diem_c = min(kpi_data.get("c_chat_luong", 0) * 100, 100.0)  # c: tỷ lệ chất lượng
            diem_d = min(kpi_data.get("d_ket_qua", 0) * 100, 100.0)   # d: kết quả đơn vị
            diem_dd = min(kpi_data.get("dd_to_chuc", 0) * 100, 100.0)  # đ: tổ chức triển khai
            diem_e = min(kpi_data.get("e_doan_ket", 0) * 100, 100.0)   # e: đoàn kết nội bộ
            diem_kpi_nhiem_vu = kpi_data.get("diem_70", 0)  # Điểm KPI /70
        else:
            # Công chức: dùng công thức 3 chỉ số (a,b,c)
            kpi_data = await tinh_diem_kpi_70(db, cc.id, thang, nam, tam_tinh=False)
            # Cap tỷ lệ % ở 100% (fix bug a > 100% khi CC làm vượt chỉ tiêu)
            diem_a = min(kpi_data.get("a_so_luong", 0) * 100, 100.0)
            diem_b = min(kpi_data.get("c_tien_do", 0) * 100, 100.0)   # Chú ý: key là "c_tien_do" (theo code)
            diem_c = min(kpi_data.get("b_chat_luong", 0) * 100, 100.0)  # Chú ý: key là "b_chat_luong"
            diem_kpi_nhiem_vu = kpi_data.get("diem_70", 0)
    except Exception as e:
        logger.warning(f"Lỗi tính điểm KPI cho {cc.ma_cc} tháng {thang}/{nam}: {e}")
        # Giữ giá trị None để hiển thị "N/A" trong template

    # Replace vào paragraph (dùng search text)
    # Phải replace toàn bộ text của para rồi gán lại vào run đầu tiên để preserve formatting
    for para in doc.paragraphs:
        full_text = para.text
        replaced = False

        # Điểm a (số lượng)
        # Pattern: "………..(%)" (3× U+2026 + ".." + "(%)")
        if "Điểm tỷ lệ % đánh giá về số lượng (a):" in full_text:
            if diem_a is not None:
                full_text = full_text.replace("………..(%)", f"{diem_a:.2f}%")
            else:
                full_text = full_text.replace("………..(%)", "N/A")
            replaced = True

        # Điểm b (tiến độ)
        elif "Điểm tỷ lệ % đánh giá về tiến độ (b):" in full_text:
            if diem_b is not None:
                full_text = full_text.replace("………..(%)", f"{diem_b:.2f}%")
            else:
                full_text = full_text.replace("………..(%)", "N/A")
            replaced = True

        # Điểm c (chất lượng)
        elif "Điểm tỷ lệ % đánh giá về chất lượng (c):" in full_text:
            if diem_c is not None:
                full_text = full_text.replace("………..(%)", f"{diem_c:.2f}%")
            else:
                full_text = full_text.replace("………..(%)", "N/A")
            replaced = True

        # Điểm d (kết quả đơn vị)
        elif "Điểm tỷ lệ % đánh giá về kết quả hoạt động của bộ phận/đơn vị (d):" in full_text:
            if diem_d is not None:
                full_text = full_text.replace("………..(%)", f"{diem_d:.2f}%")
            else:
                full_text = full_text.replace("………..(%)", "N/A")
            replaced = True

        # Điểm đ (tổ chức triển khai) — pattern khác: "……(%)"
        elif "Điểm tỷ lệ % đánh giá về khả năng tổ chức triển khai thực hiện nhiệm vụ (đ):" in full_text:
            if diem_dd is not None:
                full_text = full_text.replace("……(%)", f"{diem_dd:.2f}%")
            else:
                full_text = full_text.replace("……(%)", "N/A")
            replaced = True

        # Điểm e (đoàn kết) — text khác, chứa "năng lực tập hợp"
        elif "Điểm tỷ lệ % đánh giá về năng lực tập hợp, đoàn kết công chức" in full_text:
            if diem_e is not None:
                full_text = full_text.replace("………..(%)", f"{diem_e:.2f}%")
            else:
                full_text = full_text.replace("………..(%)", "N/A")
            replaced = True

        # Điểm d (tổng kết quả thực hiện nhiệm vụ - PL-01A cho CC thường)
        # d = (a + b + c) / 3 × 100 (%), cap ở 100%
        # Placeholder: "d. Điểm tỷ lệ % kết quả thực hiện nhiệm vụ (d = ): ……….(%)"
        # FIX BUG: Dùng replace_in_runs() để giữ nguyên equation trong template
        # KHÔNG set replaced=True vì replace_in_runs() đã xử lý xong, không cần clear all runs
        elif "Điểm tỷ lệ % kết quả thực hiện nhiệm vụ (d = )" in full_text:
            diem_d_01a = None
            if not is_lanh_dao and None not in [diem_a, diem_b, diem_c]:
                # CC thường (PL-01A): d = (a + b + c) / 3
                diem_d_01a = min((diem_a + diem_b + diem_c) / 3, 100.0)

            if diem_d_01a is not None:
                replace_in_runs(para, "……….(%)", f"{diem_d_01a:.2f}%")
            else:
                replace_in_runs(para, "……….(%)", "N/A")

        # Điểm g (tổng kết quả thực hiện nhiệm vụ - PL-01B cho lãnh đạo)
        # g = (a + b + c + d + đ + e) / 6 × 100 (%)
        # Hoặc tương đương: g = diem_kpi_nhiem_vu / 70 × 100
        # FIX BUG: Dùng replace_in_runs() để giữ nguyên equation trong template
        # KHÔNG set replaced=True vì replace_in_runs() đã xử lý xong, không cần clear all runs
        elif "Điểm tỷ lệ % kết quả thực hiện nhiệm vụ (g = " in full_text:
            diem_g = None
            if is_lanh_dao and None not in [diem_a, diem_b, diem_c, diem_d, diem_dd, diem_e]:
                # Lãnh đạo: g = (a + b + c + d + đ + e) / 6 (đã scale 0-100, nên lấy trung bình)
                diem_g = min((diem_a + diem_b + diem_c + diem_d + diem_dd + diem_e) / 6, 100.0)
            elif not is_lanh_dao and None not in [diem_a, diem_b, diem_c]:
                # CC thường: g = (a + b + c) / 3 (fallback nếu template dùng g thay vì d)
                diem_g = min((diem_a + diem_b + diem_c) / 3, 100.0)

            if diem_g is not None:
                replace_in_runs(para, "……….(%)", f"{diem_g:.2f}%")
            else:
                replace_in_runs(para, "……….(%)", "N/A")

        # Điểm KPI nhiệm vụ (70 điểm max)
        # FIX BUG: Dùng replace_in_runs() để giữ nguyên equation trong template
        # KHÔNG set replaced=True vì replace_in_runs() đã xử lý xong, không cần clear all runs
        elif "Điểm tiêu chí kết quả thực hiện nhiệm vụ (= )" in full_text:
            if diem_kpi_nhiem_vu is not None:
                replace_in_runs(para, "………………………….", f"{diem_kpi_nhiem_vu:.2f}")
            else:
                replace_in_runs(para, "………………………….", "Chưa có dữ liệu")

        # Tổng điểm theo dõi, đánh giá (3=1+2)
        # 1 = điểm tiêu chí chung (/30)
        # 2 = điểm kết quả thực hiện nhiệm vụ (/70)
        # 3 = 1 + 2 = tổng /100
        # Placeholder là ": \t" (tab character)
        elif "3. Tổng điểm theo dõi, đánh giá (3=1+2):" in full_text:
            if diem_kpi_nhiem_vu is not None and diem_tieu_chi is not None:
                tong_diem = diem_tieu_chi + diem_kpi_nhiem_vu
                # Replace ": \t" → ": {số}"
                full_text = full_text.replace(": \t", f": {tong_diem:.2f}")
            else:
                full_text = full_text.replace(": \t", ": Chưa có dữ liệu")
            replaced = True

        # Nếu có replace, gán lại text và set font
        if replaced:
            # Clear all runs
            for run in para.runs:
                run.text = ""
            # Gán text mới vào run đầu tiên (hoặc tạo mới nếu không có)
            if para.runs:
                para.runs[0].text = full_text
                set_times_new_roman(para.runs[0])
            else:
                new_run = para.add_run(full_text)
                set_times_new_roman(new_run)

    # Điền điểm vào bảng tiêu chí (Table 1 - bảng thứ 2)
    if len(doc.tables) >= 2:
        table_tc = doc.tables[1]
        # Map tieu_chi_list theo ma_tieu_chi (1.1, 1.2, 2.1, ...)
        tc_map = {tc.tieu_chi.ma_tieu_chi: tc for tc in tieu_chi_list if tc.tieu_chi}

        # Duyệt rows (bỏ qua header 2 dòng đầu)
        # Row 0,1: header, Row 2: I (nhóm 1), Row 3: 1.1, Row 4: 1.2, Row 5: II (nhóm 2), ...
        # Logic map: đọc cột TT, match với danh sách 10 tiêu chí:
        # Nhóm I: 1.1, 1.2 (2 tiêu chí)
        # Nhóm II: 2.1, 2.2, 2.3, 2.4 (4 tiêu chí)
        # Nhóm III: 3.1, 3.2, 3.3, 3.4 (4 tiêu chí)
        ma_tieu_chi_list = [
            ("1", "1.1"),
            ("2", "1.2"),
            ("1", "2.1"),
            ("2", "2.2"),
            ("3", "2.3"),
            ("4", "2.4"),
            ("1", "3.1"),
            ("2", "3.2"),
            ("3", "3.3"),
            ("4", "3.4"),
        ]

        # Track thứ tự tiêu chí và tổng nhóm
        tc_idx = 0
        tong_nhom_1 = Decimal(0)
        tong_nhom_2 = Decimal(0)
        tong_nhom_3 = Decimal(0)

        for row_idx, row in enumerate(table_tc.rows[2:], start=0):
            if len(row.cells) >= 4:
                cell_tt = row.cells[0].text.strip()

                # Điền tổng nhóm vào row header (I, II, III)
                # Row 2 (idx=0): I → tổng nhóm 1
                # Row 5 (idx=3): II → tổng nhóm 2
                # Row 10 (idx=8): III → tổng nhóm 3
                if cell_tt == "I":
                    # Tính tổng nhóm 1 sau khi đã duyệt 2 tiêu chí (1.1, 1.2)
                    # Nhưng hiện tại chưa duyệt → sẽ cập nhật sau
                    pass
                elif cell_tt == "II":
                    # Cập nhật tổng nhóm 1 vào row I
                    table_tc.rows[2].cells[3].text = f"{float(tong_nhom_1):.2f}"
                    for para in table_tc.rows[2].cells[3].paragraphs:
                        for run in para.runs:
                            set_times_new_roman(run)
                elif cell_tt == "III":
                    # Cập nhật tổng nhóm 2 vào row II
                    table_tc.rows[5].cells[3].text = f"{float(tong_nhom_2):.2f}"
                    for para in table_tc.rows[5].cells[3].paragraphs:
                        for run in para.runs:
                            set_times_new_roman(run)
                elif cell_tt == "Tổng cộng":
                    # Cập nhật tổng nhóm 3 vào row III
                    table_tc.rows[10].cells[3].text = f"{float(tong_nhom_3):.2f}"
                    for para in table_tc.rows[10].cells[3].paragraphs:
                        for run in para.runs:
                            set_times_new_roman(run)

                    # Cập nhật tổng /30 vào row Tổng cộng
                    tong_30 = tong_nhom_1 + tong_nhom_2 + tong_nhom_3
                    row.cells[3].text = f"{float(tong_30):.2f}"
                    for para in row.cells[3].paragraphs:
                        for run in para.runs:
                            set_times_new_roman(run)
                    continue

                # Match theo TT number để điền điểm tiêu chí con
                if tc_idx < len(ma_tieu_chi_list):
                    expected_tt, ma_tc = ma_tieu_chi_list[tc_idx]
                    # Kiểm tra cell_tt có match không (cột TT chứa "1", "2", "3", ...)
                    if cell_tt == expected_tt:
                        # Tìm điểm trong tc_map
                        diem = Decimal(0)
                        if ma_tc in tc_map:
                            tc_data = tc_map[ma_tc]
                            # Dùng điểm phê duyệt (LD) nếu có, không thì tự chấm
                            diem = tc_data.diem_phe_duyet or tc_data.diem_tu_cham or Decimal(0)
                            row.cells[3].text = f"{float(diem):.2f}"
                        else:
                            # Tiêu chí chưa có dữ liệu
                            row.cells[3].text = ""

                        # Set font Times New Roman
                        for para in row.cells[3].paragraphs:
                            for run in para.runs:
                                set_times_new_roman(run)

                        # Cộng vào tổng nhóm tương ứng
                        if ma_tc in ["1.1", "1.2"]:
                            tong_nhom_1 += diem
                        elif ma_tc in ["2.1", "2.2", "2.3", "2.4"]:
                            tong_nhom_2 += diem
                        elif ma_tc in ["3.1", "3.2", "3.3", "3.4"]:
                            tong_nhom_3 += diem

                        tc_idx += 1

    # Lưu vào buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    # Tên file
    ma_cc_safe = cc.ma_cc.replace("/", "-") if cc.ma_cc else "user"
    filename = f"PhieuDanhGia_{ma_cc_safe}_T{thang}_{nam}.docx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# =============================================================================
# ENDPOINT 2: IN BẢNG KÊ CÔNG VIỆC (PL-02)
# =============================================================================

@router.get("/bang-ke-cong-viec/{thang}/{nam}")
async def export_bang_ke_cong_viec(
    thang: int,
    nam: int,
    db: DatabaseDep,
    current_user: ActiveUserDep,
):
    """
    Xuất bảng kê công việc cá nhân (PL-02) cho tháng/năm chỉ định.

    Bao gồm:
    - Thống kê tổng hợp (tổng CV, đã hoàn thành, chưa hoàn thành, ...)
    - Chi tiết từng công việc trong bảng

    Args:
        thang: Tháng (1-12)
        nam: Năm (>= 2020)
        db: Database session
        current_user: User hiện tại

    Returns:
        StreamingResponse: File DOCX download
    """
    # Validation
    if not (1 <= thang <= 12):
        raise HTTPException(status_code=400, detail="Tháng không hợp lệ (1-12)")
    if nam < 2020 or nam > 2100:
        raise HTTPException(status_code=400, detail="Năm không hợp lệ")

    # Load user
    stmt_user = (
        select(CongChuc)
        .options(selectinload(CongChuc.don_vi))
        .where(CongChuc.id == current_user.id)
    )
    result_user = await db.execute(stmt_user)
    cc = result_user.scalar_one_or_none()
    if not cc:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin công chức")

    is_lanh_dao = cc.is_lanh_dao or False

    # Lấy danh sách công việc đã kê khai trong tháng
    # Nếu là lãnh đạo → query KeKhaiLanhDao, nếu không → KeKhaiCongViec
    cong_viec_list = []
    cong_viec_lanh_dao_list = []

    if is_lanh_dao:
        # Query KeKhaiLanhDao
        stmt_kkld = (
            select(KeKhaiLanhDao)
            .where(
                and_(
                    KeKhaiLanhDao.cong_chuc_id == cc.id,
                    KeKhaiLanhDao.thang == thang,
                    KeKhaiLanhDao.nam == nam,
                    KeKhaiLanhDao.is_deleted == False,
                )
            )
            .order_by(KeKhaiLanhDao.ngay_thuc_hien.desc())
        )
        result_kkld = await db.execute(stmt_kkld)
        cong_viec_lanh_dao_list = result_kkld.scalars().all()
    else:
        # Query KeKhaiCongViec
        stmt_kk = (
            select(KeKhaiCongViec)
            .options(
                selectinload(KeKhaiCongViec.danh_muc_sp).selectinload(DanhMucSpCongViec.sp_chuan),
                selectinload(KeKhaiCongViec.cap_do)
            )
            .where(
                and_(
                    KeKhaiCongViec.cong_chuc_id == cc.id,
                    KeKhaiCongViec.thang == thang,
                    KeKhaiCongViec.nam == nam,
                )
            )
            .order_by(KeKhaiCongViec.ngay_thuc_hien.desc())
        )
        result_kk = await db.execute(stmt_kk)
        cong_viec_list = result_kk.scalars().all()

    # Tính thống kê
    if is_lanh_dao:
        # KeKhaiLanhDao: có trang_thai_hoan_thanh (DA_HOAN_THANH/CHUA_HOAN_THANH)
        tong_cv = len(cong_viec_lanh_dao_list)
        da_ht = sum(1 for cv in cong_viec_lanh_dao_list
                    if cv.trang_thai_hoan_thanh == TrangThaiHoanThanh.DA_HOAN_THANH)
        chua_ht = tong_cv - da_ht

        # Tính đúng hạn/trễ hạn cho lãnh đạo dựa vào so_loi_tien_do
        # Đạt tiến độ = đã hoàn thành VÀ không có lỗi tiến độ
        dung_han = sum(
            1 for cv in cong_viec_lanh_dao_list
            if cv.trang_thai_hoan_thanh == TrangThaiHoanThanh.DA_HOAN_THANH
            and cv.so_loi_tien_do == 0
        )
        # Chậm tiến độ = đã hoàn thành NHƯNG có lỗi tiến độ
        tre_han = sum(
            1 for cv in cong_viec_lanh_dao_list
            if cv.trang_thai_hoan_thanh == TrangThaiHoanThanh.DA_HOAN_THANH
            and cv.so_loi_tien_do > 0
        )

        ty_le_dung_han = round((dung_han / da_ht * 100) if da_ht > 0 else 0, 2)
        ty_le_tre_han = round((tre_han / da_ht * 100) if da_ht > 0 else 0, 2)
    else:
        # KeKhaiCongViec: không có trang_thai_hoan_thanh - chỉ có trang_thai
        tong_cv = len(cong_viec_list)
        # Coi DA_PHE_DUYET là đã hoàn thành
        da_ht = sum(1 for cv in cong_viec_list if cv.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET)
        chua_ht = tong_cv - da_ht

        # Logic mới (fix bug PL-02): Dùng so_loi_tien_do (giống xep_loai_moi.py::tinh_diem_kpi_70)
        # Đạt tiến độ = đã hoàn thành VÀ không có lỗi tiến độ
        dung_han = sum(
            1 for cv in cong_viec_list
            if cv.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET
            and cv.so_loi_tien_do == 0
        )
        # Chậm tiến độ = đã hoàn thành NHƯNG có lỗi tiến độ
        tre_han = sum(
            1 for cv in cong_viec_list
            if cv.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET
            and cv.so_loi_tien_do > 0
        )

        ty_le_dung_han = round((dung_han / da_ht * 100) if da_ht > 0 else 0, 2)
        ty_le_tre_han = round((tre_han / da_ht * 100) if da_ht > 0 else 0, 2)

    # Load template
    template_path = TEMPLATES_DIR / "PL-Mẫu số 02-Bang ke.docx"
    if not template_path.exists():
        raise HTTPException(status_code=500, detail="Template PL-02 không tồn tại")

    doc = Document(template_path)

    # Replace placeholders
    ky_danh_gia = f"Tháng {thang}/{nam}"
    replace_placeholder_in_docx(doc, "{{ky_danh_gia}}", ky_danh_gia)
    replace_placeholder_in_docx(doc, "{{tong_cv}}", str(tong_cv))
    replace_placeholder_in_docx(doc, "{{chua_ht}}", str(chua_ht))
    replace_placeholder_in_docx(doc, "{{da_ht}}", str(da_ht))
    replace_placeholder_in_docx(doc, "{{dung_han}}", str(dung_han))
    replace_placeholder_in_docx(doc, "{{ty_le_dung_han}}", f"{ty_le_dung_han}")
    replace_placeholder_in_docx(doc, "{{tre_han}}", str(tre_han))
    replace_placeholder_in_docx(doc, "{{ty_le_tre_han}}", f"{ty_le_tre_han}")

    # Điền bảng công việc (Table 1 - bảng thứ 2)
    if len(doc.tables) >= 2:
        table_cv = doc.tables[1]

        # Xóa các row mẫu (giữ header 3 dòng đầu)
        # Rows từ index 3 trở đi là data rows mẫu
        rows_to_delete = []
        for idx in range(3, len(table_cv.rows)):
            rows_to_delete.append(idx)

        # Delete từ cuối lên đầu
        for idx in reversed(rows_to_delete):
            table_cv._element.remove(table_cv.rows[idx]._element)

        # Thêm row mới cho từng công việc
        # Chọn danh sách dựa vào is_lanh_dao
        data_source = cong_viec_lanh_dao_list if is_lanh_dao else cong_viec_list

        for idx, cv in enumerate(data_source, start=1):
            # Add new row (copy format từ row template cuối cùng)
            new_row = table_cv.add_row()

            # Điền dữ liệu vào các cột
            # (1) STT
            new_row.cells[0].text = str(idx)
            set_cell_font_times_new_roman(new_row.cells[0])

            if is_lanh_dao:
                # ===== MAPPING CHO LÃNH ĐẠO (KeKhaiLanhDao) =====
                # (2) Nhiệm vụ được giao (tên công việc)
                new_row.cells[1].text = cv.ten_cong_viec or "N/A"
                set_cell_font_times_new_roman(new_row.cells[1])

                # (3) Số, ngày văn bản giao (không có trong KeKhaiLanhDao - bỏ trống)
                new_row.cells[2].text = ""
                set_cell_font_times_new_roman(new_row.cells[2])

                # (4) Công việc chi tiết (mô tả)
                new_row.cells[3].text = cv.mo_ta or ""
                set_cell_font_times_new_roman(new_row.cells[3])

                # (5) Ngày phải hoàn thành (dùng ngay_thuc_hien - giống cột 6)
                ngay_ht_str = cv.ngay_thuc_hien.strftime("%d/%m/%Y") if cv.ngay_thuc_hien else ""
                new_row.cells[4].text = ngay_ht_str
                set_cell_font_times_new_roman(new_row.cells[4])

                # (6) Ngày hoàn thành thực tế (dùng ngay_thuc_hien)
                new_row.cells[5].text = ngay_ht_str
                set_cell_font_times_new_roman(new_row.cells[5])

                # (7) Chưa hoàn thành
                chua_hoan_thanh = cv.trang_thai_hoan_thanh == TrangThaiHoanThanh.CHUA_HOAN_THANH
                new_row.cells[6].text = "X" if chua_hoan_thanh else ""
                set_cell_font_times_new_roman(new_row.cells[6])

                # (8) Đạt tiến độ (đã hoàn thành và không có lỗi tiến độ)
                dat_tien_do = (
                    cv.trang_thai_hoan_thanh == TrangThaiHoanThanh.DA_HOAN_THANH
                    and cv.so_loi_tien_do == 0
                )
                new_row.cells[7].text = "X" if dat_tien_do else ""
                set_cell_font_times_new_roman(new_row.cells[7])

                # (9) Chậm tiến độ (đã hoàn thành nhưng có lỗi tiến độ)
                cham_tien_do = (
                    cv.trang_thai_hoan_thanh == TrangThaiHoanThanh.DA_HOAN_THANH
                    and cv.so_loi_tien_do > 0
                )
                new_row.cells[8].text = "X" if cham_tien_do else ""
                set_cell_font_times_new_roman(new_row.cells[8])

                # (10) Ghi chú (gộp lỗi CL + TĐ + số lỗi)
                ghi_chu = ""
                if cv.so_loi_chat_luong > 0:
                    ghi_chu += f"Lỗi CL ({cv.so_loi_chat_luong}): {cv.ghi_chu_loi_chat_luong or 'Không có mô tả'}. "
                if cv.so_loi_tien_do > 0:
                    ghi_chu += f"Lỗi TĐ ({cv.so_loi_tien_do}): {cv.ghi_chu_loi_tien_do or 'Không có mô tả'}."
                if cv.y_kien_lanh_dao:
                    ghi_chu += f" Ý kiến LĐ: {cv.y_kien_lanh_dao}."
                new_row.cells[9].text = ghi_chu.strip()
                set_cell_font_times_new_roman(new_row.cells[9])

            else:
                # ===== MAPPING CHO CÔNG CHỨC THƯỜNG (KeKhaiCongViec) =====
                # (2) Nhiệm vụ được giao (tên công việc + cấp độ)
                ten_sp = ""
                if cv.danh_muc_sp:
                    ten_sp = cv.danh_muc_sp.ten_cong_viec
                    if cv.cap_do:
                        ten_sp += f" ({cv.cap_do.ten_cap_do})"
                new_row.cells[1].text = ten_sp or "N/A"
                set_cell_font_times_new_roman(new_row.cells[1])

                # (3) Số, ngày văn bản giao (không có trong model - bỏ trống)
                new_row.cells[2].text = ""
                set_cell_font_times_new_roman(new_row.cells[2])

                # (4) Công việc chi tiết - FORMAT MỚI: {tên CV} (tổng {SL} {đơn vị}, mức độ {cấp độ})
                chi_tiet_cv = ""
                if cv.danh_muc_sp:
                    chi_tiet_cv = cv.danh_muc_sp.ten_cong_viec

                    # Build suffix: (tổng X đơn vị, mức độ Y)
                    parts = []

                    # Phần số lượng + đơn vị
                    if cv.so_luong and cv.danh_muc_sp.sp_chuan:
                        # Xác định đơn vị tính dựa vào loại SP
                        ma_sp = cv.danh_muc_sp.sp_chuan.ma_sp
                        don_vi = "TK" if ma_sp == "SP1" else "VB" if ma_sp == "SP2" else "Giờ"
                        parts.append(f"tổng {cv.so_luong} {don_vi}")

                    # Phần cấp độ
                    if cv.cap_do:
                        parts.append(f"mức độ {cv.cap_do.ma_cap_do}")

                    # Ghép lại
                    if parts:
                        chi_tiet_cv += f" ({', '.join(parts)})"

                new_row.cells[3].text = chi_tiet_cv or ""
                set_cell_font_times_new_roman(new_row.cells[3])

                # (5) + (6) Ngày hoàn thành: Dùng ngay_thuc_hien (CC không điền ngay_hoan_thanh)
                # Production data: 152/154 records có ngay_hoan_thanh=NULL, nhưng 100% có ngay_thuc_hien
                ngay_ht_str = cv.ngay_thuc_hien.strftime("%d/%m/%Y") if cv.ngay_thuc_hien else ""
                new_row.cells[4].text = ngay_ht_str
                set_cell_font_times_new_roman(new_row.cells[4])

                # (6) Ngày hoàn thành thực tế (dùng ngay_thuc_hien)
                new_row.cells[5].text = ngay_ht_str
                set_cell_font_times_new_roman(new_row.cells[5])

                # (7) Chưa hoàn thành
                chua_hoan_thanh = cv.trang_thai != TrangThaiKeKhai.DA_PHE_DUYET
                new_row.cells[6].text = "X" if chua_hoan_thanh else ""
                set_cell_font_times_new_roman(new_row.cells[6])

                # (8) Đạt tiến độ: Dùng logic từ xep_loai_moi.py::tinh_diem_kpi_70
                # Đã hoàn thành VÀ không có lỗi tiến độ (so_loi_tien_do=0)
                dat_tien_do = (
                    cv.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET
                    and cv.so_loi_tien_do == 0
                )
                new_row.cells[7].text = "X" if dat_tien_do else ""
                set_cell_font_times_new_roman(new_row.cells[7])

                # (9) Chậm tiến độ: Đã hoàn thành NHƯNG có lỗi tiến độ (so_loi_tien_do>0)
                cham_tien_do = (
                    cv.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET
                    and cv.so_loi_tien_do > 0
                )
                new_row.cells[8].text = "X" if cham_tien_do else ""
                set_cell_font_times_new_roman(new_row.cells[8])

                # (10) Ghi chú (gộp lỗi CL + TĐ)
                ghi_chu = ""
                if cv.ghi_chu_loi_chat_luong:
                    ghi_chu += f"Lỗi CL: {cv.ghi_chu_loi_chat_luong}. "
                if cv.ghi_chu_loi_tien_do:
                    ghi_chu += f"Lỗi TĐ: {cv.ghi_chu_loi_tien_do}."
                new_row.cells[9].text = ghi_chu.strip()
                set_cell_font_times_new_roman(new_row.cells[9])

    # Lưu vào buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    # Tên file
    ma_cc_safe = cc.ma_cc.replace("/", "-") if cc.ma_cc else "user"
    filename = f"BangKeCongViec_{ma_cc_safe}_T{thang}_{nam}.docx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# =============================================================================
# ENDPOINT 3: IN PHIẾU ĐÁNH GIÁ QUÝ (PL-01A hoặc PL-01B)
# =============================================================================

@router.get("/phieu-danh-gia-quy/{quy}/{nam}")
async def export_phieu_danh_gia_quy(
    quy: int,
    nam: int,
    db: DatabaseDep,
    current_user: ActiveUserDep,
):
    """
    Xuất phiếu đánh giá cá nhân QUÝ (PL-01A hoặc PL-01B).

    Tương tự endpoint tháng, nhưng:
    - Dùng `tinh_diem_quy()` từ xep_loai_quy_helpers
    - Kỳ đánh giá: "Quý {quy}/{nam}"
    - Điểm a,b,c: trung bình 3 tháng (CC) hoặc a-e theo logic LD (từ tinh_diem_quy)
    - Điểm tiêu chí chung: không điền chi tiết từng ô (deduplicate), chỉ điền tổng

    Args:
        quy: Quý (1-4)
        nam: Năm (>= 2020)
        db: Database session
        current_user: User hiện tại

    Returns:
        StreamingResponse: File DOCX download
    """
    # Import helper
    from app.api.v1.endpoints.xep_loai_quy_helpers import tinh_diem_quy, QUY_TO_THANG
    from app.api.v1.endpoints.xep_loai_moi import tinh_diem_kpi_70, tinh_diem_kpi_70_lanh_dao

    # Validation
    if not (1 <= quy <= 4):
        raise HTTPException(status_code=400, detail="Quý không hợp lệ (1-4)")
    if nam < 2020 or nam > 2100:
        raise HTTPException(status_code=400, detail="Năm không hợp lệ")

    # Load user
    stmt = (
        select(CongChuc)
        .options(
            selectinload(CongChuc.don_vi),
            selectinload(CongChuc.vai_tro),
        )
        .where(CongChuc.id == current_user.id)
    )
    result = await db.execute(stmt)
    cc = result.scalar_one_or_none()
    if not cc:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin công chức")

    is_lanh_dao = cc.is_lanh_dao or False

    # Tính điểm quý
    ket_qua = await tinh_diem_quy(db, cc.id, quy, nam)

    # Lấy 3 tháng trong quý
    thang_list = QUY_TO_THANG.get(quy, [])

    # Điểm tiêu chí chung
    diem_tieu_chi = ket_qua.get("diem_tc_quy", 0)
    diem_kpi_nhiem_vu = ket_qua.get("diem_kpi_quy", 0)
    diem_tong = ket_qua.get("diem_tong_quy", 0)

    # === Tính điểm a,b,c,d,đ,e cho quý (trung bình 3 tháng) ===
    # CC thường: diem_a, diem_b, diem_c (tỷ lệ 0-100%)
    # Lãnh đạo: diem_a, b, c, d, đ, e (tỷ lệ 0-100%)
    diem_a = None
    diem_b = None
    diem_c = None
    diem_d = None
    diem_dd = None
    diem_e = None

    try:
        if is_lanh_dao:
            # Lãnh đạo: tính từng tháng, rồi lấy trung bình
            a_values, b_values, c_values = [], [], []
            d_values, dd_values, e_values = [], [], []

            for thang in thang_list:
                kpi_data = await tinh_diem_kpi_70_lanh_dao(db, cc.id, thang, nam, tam_tinh=False)
                a_values.append(kpi_data.get("a_so_luong", 0) * 100)  # Scale 0-1 → 0-100%
                b_values.append(kpi_data.get("b_tien_do", 0) * 100)
                c_values.append(kpi_data.get("c_chat_luong", 0) * 100)
                d_values.append(kpi_data.get("d_ket_qua", 0) * 100)
                dd_values.append(kpi_data.get("dd_to_chuc", 0) * 100)
                e_values.append(kpi_data.get("e_doan_ket", 0) * 100)

            # Trung bình
            diem_a = sum(a_values) / 3 if len(a_values) == 3 else 0
            diem_b = sum(b_values) / 3 if len(b_values) == 3 else 0
            diem_c = sum(c_values) / 3 if len(c_values) == 3 else 0
            diem_d = sum(d_values) / 3 if len(d_values) == 3 else 0
            diem_dd = sum(dd_values) / 3 if len(dd_values) == 3 else 0
            diem_e = sum(e_values) / 3 if len(e_values) == 3 else 0

            # Cap ở 100%
            diem_a = min(diem_a, 100.0)
            diem_b = min(diem_b, 100.0)
            diem_c = min(diem_c, 100.0)
            diem_d = min(diem_d, 100.0)
            diem_dd = min(diem_dd, 100.0)
            diem_e = min(diem_e, 100.0)
        else:
            # CC thường: tính từng tháng, lấy TB a, b (c_tien_do), c (b_chat_luong)
            a_values, b_values, c_values = [], [], []

            for thang in thang_list:
                kpi_data = await tinh_diem_kpi_70(db, cc.id, thang, nam, tam_tinh=False)
                a_values.append(kpi_data.get("a_so_luong", 0) * 100)  # Scale 0-1 → 0-100%
                c_values.append(kpi_data.get("c_tien_do", 0) * 100)  # Key là c_tien_do
                b_values.append(kpi_data.get("b_chat_luong", 0) * 100)  # Key là b_chat_luong

            diem_a = sum(a_values) / 3 if len(a_values) == 3 else 0
            diem_b = sum(c_values) / 3 if len(c_values) == 3 else 0  # Tỷ lệ tiến độ
            diem_c = sum(b_values) / 3 if len(b_values) == 3 else 0  # Tỷ lệ chất lượng

            # Cap ở 100%
            diem_a = min(diem_a, 100.0)
            diem_b = min(diem_b, 100.0)
            diem_c = min(diem_c, 100.0)
    except Exception as e:
        logger.warning(f"Lỗi tính điểm KPI quý cho {cc.ma_cc} quý {quy}/{nam}: {e}")

    # Chọn template
    template_name = "PL-Mẫu số 01B-LĐ.docx" if is_lanh_dao else "PL-Mẫu số 01A-CC.docx"
    template_path = TEMPLATES_DIR / template_name

    if not template_path.exists():
        raise HTTPException(status_code=500, detail=f"Template {template_name} không tồn tại")

    # Load template
    doc = Document(template_path)

    # Replace placeholders
    ky_danh_gia = f"Quý {quy}/{nam}"
    ho_ten = cc.ho_ten or "N/A"
    chuc_vu = cc.chuc_vu or "Công chức"
    don_vi = cc.don_vi.ten_don_vi if cc.don_vi else "N/A"
    diem_tieu_chi_str = f"{diem_tieu_chi:.2f}"
    diem_tong_str = f"{diem_tong:.2f}" if diem_tong else "Chưa có dữ liệu"

    replace_placeholder_in_docx(doc, "{{ky_danh_gia}}", ky_danh_gia)
    replace_placeholder_in_docx(doc, "{{ho_ten}}", ho_ten)
    replace_placeholder_in_docx(doc, "{{chuc_vu}}", chuc_vu)
    replace_placeholder_in_docx(doc, "{{don_vi}}", don_vi)
    replace_placeholder_in_docx(doc, "{{diem_tieu_chi}}", diem_tieu_chi_str)
    replace_placeholder_in_docx(doc, "{{diem_tong}}", diem_tong_str)

    # === Replace điểm a,b,c,d,đ,e vào paragraphs ===
    for para in doc.paragraphs:
        full_text = para.text
        replaced = False

        # Điểm a (số lượng)
        if "Điểm tỷ lệ % đánh giá về số lượng (a):" in full_text:
            if diem_a is not None:
                full_text = full_text.replace("………..(%)", f"{diem_a:.2f}%")
            else:
                full_text = full_text.replace("………..(%)", "N/A")
            replaced = True

        # Điểm b (tiến độ)
        elif "Điểm tỷ lệ % đánh giá về tiến độ (b):" in full_text:
            if diem_b is not None:
                full_text = full_text.replace("………..(%)", f"{diem_b:.2f}%")
            else:
                full_text = full_text.replace("………..(%)", "N/A")
            replaced = True

        # Điểm c (chất lượng)
        elif "Điểm tỷ lệ % đánh giá về chất lượng (c):" in full_text:
            if diem_c is not None:
                full_text = full_text.replace("………..(%)", f"{diem_c:.2f}%")
            else:
                full_text = full_text.replace("………..(%)", "N/A")
            replaced = True

        # Điểm d (kết quả đơn vị)
        elif "Điểm tỷ lệ % đánh giá về kết quả hoạt động của bộ phận/đơn vị (d):" in full_text:
            if diem_d is not None:
                full_text = full_text.replace("………..(%)", f"{diem_d:.2f}%")
            else:
                full_text = full_text.replace("………..(%)", "N/A")
            replaced = True

        # Điểm đ (tổ chức triển khai)
        elif "Điểm tỷ lệ % đánh giá về khả năng tổ chức triển khai thực hiện nhiệm vụ (đ):" in full_text:
            if diem_dd is not None:
                full_text = full_text.replace("……(%)", f"{diem_dd:.2f}%")
            else:
                full_text = full_text.replace("……(%)", "N/A")
            replaced = True

        # Điểm e (đoàn kết)
        elif "Điểm tỷ lệ % đánh giá về năng lực tập hợp, đoàn kết công chức" in full_text:
            if diem_e is not None:
                full_text = full_text.replace("………..(%)", f"{diem_e:.2f}%")
            else:
                full_text = full_text.replace("………..(%)", "N/A")
            replaced = True

        # Điểm d (tổng kết quả - PL-01A cho CC thường)
        elif "Điểm tỷ lệ % kết quả thực hiện nhiệm vụ (d = )" in full_text:
            diem_d_01a = None
            if not is_lanh_dao and None not in [diem_a, diem_b, diem_c]:
                diem_d_01a = min((diem_a + diem_b + diem_c) / 3, 100.0)

            if diem_d_01a is not None:
                replace_in_runs(para, "……….(%)", f"{diem_d_01a:.2f}%")
            else:
                replace_in_runs(para, "……….(%)", "N/A")

        # Điểm g (tổng kết quả - PL-01B cho lãnh đạo)
        elif "Điểm tỷ lệ % kết quả thực hiện nhiệm vụ (g = " in full_text:
            diem_g = None
            if is_lanh_dao and None not in [diem_a, diem_b, diem_c, diem_d, diem_dd, diem_e]:
                diem_g = min((diem_a + diem_b + diem_c + diem_d + diem_dd + diem_e) / 6, 100.0)
            elif not is_lanh_dao and None not in [diem_a, diem_b, diem_c]:
                diem_g = min((diem_a + diem_b + diem_c) / 3, 100.0)

            if diem_g is not None:
                replace_in_runs(para, "……….(%)", f"{diem_g:.2f}%")
            else:
                replace_in_runs(para, "……….(%)", "N/A")

        # Điểm KPI nhiệm vụ (70 điểm max)
        elif "Điểm tiêu chí kết quả thực hiện nhiệm vụ (= )" in full_text:
            if diem_kpi_nhiem_vu is not None:
                replace_in_runs(para, "………………………….", f"{diem_kpi_nhiem_vu:.2f}")
            else:
                replace_in_runs(para, "………………………….", "Chưa có dữ liệu")

        # Tổng điểm (3=1+2)
        elif "3. Tổng điểm theo dõi, đánh giá (3=1+2):" in full_text:
            if diem_kpi_nhiem_vu is not None and diem_tieu_chi is not None:
                tong_diem_text = diem_tieu_chi + diem_kpi_nhiem_vu
                full_text = full_text.replace(": \t", f": {tong_diem_text:.2f}")
            else:
                full_text = full_text.replace(": \t", ": Chưa có dữ liệu")
            replaced = True

        # Gán lại text nếu có replace
        if replaced:
            for run in para.runs:
                run.text = ""
            if para.runs:
                para.runs[0].text = full_text
                set_times_new_roman(para.runs[0])
            else:
                new_run = para.add_run(full_text)
                set_times_new_roman(new_run)

    # KHÔNG điền chi tiết từng ô tiêu chí chung (quý dùng deduplicate)
    # Chỉ điền tổng điểm tiêu chí chung đã được replace ở trên

    # Lưu vào buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    # Tên file
    ma_cc_safe = cc.ma_cc.replace("/", "-") if cc.ma_cc else "user"
    filename = f"PhieuDanhGia_{ma_cc_safe}_Q{quy}_{nam}.docx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# =============================================================================
# ENDPOINT 4: IN BẢNG KÊ CÔNG VIỆC QUÝ (PL-02)
# =============================================================================

@router.get("/bang-ke-cong-viec-quy/{quy}/{nam}")
async def export_bang_ke_cong_viec_quy(
    quy: int,
    nam: int,
    db: DatabaseDep,
    current_user: ActiveUserDep,
):
    """
    Xuất bảng kê công việc cá nhân QUÝ (PL-02).

    Gộp công việc cả 3 tháng trong quý vào 1 bảng.

    Args:
        quy: Quý (1-4)
        nam: Năm (>= 2020)
        db: Database session
        current_user: User hiện tại

    Returns:
        StreamingResponse: File DOCX download
    """
    # Import helper
    from app.api.v1.endpoints.xep_loai_quy_helpers import QUY_TO_THANG

    # Validation
    if not (1 <= quy <= 4):
        raise HTTPException(status_code=400, detail="Quý không hợp lệ (1-4)")
    if nam < 2020 or nam > 2100:
        raise HTTPException(status_code=400, detail="Năm không hợp lệ")

    # Load user
    stmt_user = (
        select(CongChuc)
        .options(selectinload(CongChuc.don_vi))
        .where(CongChuc.id == current_user.id)
    )
    result_user = await db.execute(stmt_user)
    cc = result_user.scalar_one_or_none()
    if not cc:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin công chức")

    is_lanh_dao = cc.is_lanh_dao or False

    # Lấy 3 tháng trong quý
    thang_list = QUY_TO_THANG.get(quy, [])

    # Lấy danh sách công việc trong 3 tháng của quý
    cong_viec_list = []
    cong_viec_lanh_dao_list = []

    if is_lanh_dao:
        # Query KeKhaiLanhDao cho 3 tháng
        stmt_kkld = (
            select(KeKhaiLanhDao)
            .where(
                and_(
                    KeKhaiLanhDao.cong_chuc_id == cc.id,
                    KeKhaiLanhDao.thang.in_(thang_list),
                    KeKhaiLanhDao.nam == nam,
                    KeKhaiLanhDao.is_deleted == False,
                )
            )
            .order_by(KeKhaiLanhDao.thang, KeKhaiLanhDao.ngay_thuc_hien.desc())
        )
        result_kkld = await db.execute(stmt_kkld)
        cong_viec_lanh_dao_list = result_kkld.scalars().all()
    else:
        # Query KeKhaiCongViec cho 3 tháng
        stmt_kk = (
            select(KeKhaiCongViec)
            .options(
                selectinload(KeKhaiCongViec.danh_muc_sp).selectinload(DanhMucSpCongViec.sp_chuan),
                selectinload(KeKhaiCongViec.cap_do)
            )
            .where(
                and_(
                    KeKhaiCongViec.cong_chuc_id == cc.id,
                    KeKhaiCongViec.thang.in_(thang_list),
                    KeKhaiCongViec.nam == nam,
                )
            )
            .order_by(KeKhaiCongViec.thang, KeKhaiCongViec.ngay_thuc_hien.desc())
        )
        result_kk = await db.execute(stmt_kk)
        cong_viec_list = result_kk.scalars().all()

    # Tính thống kê (cộng gộp 3 tháng)
    if is_lanh_dao:
        tong_cv = len(cong_viec_lanh_dao_list)
        da_ht = sum(1 for cv in cong_viec_lanh_dao_list
                    if cv.trang_thai_hoan_thanh == TrangThaiHoanThanh.DA_HOAN_THANH)
        chua_ht = tong_cv - da_ht

        dung_han = sum(
            1 for cv in cong_viec_lanh_dao_list
            if cv.trang_thai_hoan_thanh == TrangThaiHoanThanh.DA_HOAN_THANH
            and cv.so_loi_tien_do == 0
        )
        tre_han = sum(
            1 for cv in cong_viec_lanh_dao_list
            if cv.trang_thai_hoan_thanh == TrangThaiHoanThanh.DA_HOAN_THANH
            and cv.so_loi_tien_do > 0
        )

        ty_le_dung_han = round((dung_han / da_ht * 100) if da_ht > 0 else 0, 2)
        ty_le_tre_han = round((tre_han / da_ht * 100) if da_ht > 0 else 0, 2)
    else:
        tong_cv = len(cong_viec_list)
        da_ht = sum(1 for cv in cong_viec_list if cv.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET)
        chua_ht = tong_cv - da_ht

        dung_han = sum(
            1 for cv in cong_viec_list
            if cv.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET
            and cv.so_loi_tien_do == 0
        )
        tre_han = sum(
            1 for cv in cong_viec_list
            if cv.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET
            and cv.so_loi_tien_do > 0
        )

        ty_le_dung_han = round((dung_han / da_ht * 100) if da_ht > 0 else 0, 2)
        ty_le_tre_han = round((tre_han / da_ht * 100) if da_ht > 0 else 0, 2)

    # Load template
    template_path = TEMPLATES_DIR / "PL-Mẫu số 02-Bang ke.docx"
    if not template_path.exists():
        raise HTTPException(status_code=500, detail="Template PL-02 không tồn tại")

    doc = Document(template_path)

    # Replace placeholders
    ky_danh_gia = f"Quý {quy}/{nam}"
    replace_placeholder_in_docx(doc, "{{ky_danh_gia}}", ky_danh_gia)
    replace_placeholder_in_docx(doc, "{{tong_cv}}", str(tong_cv))
    replace_placeholder_in_docx(doc, "{{chua_ht}}", str(chua_ht))
    replace_placeholder_in_docx(doc, "{{da_ht}}", str(da_ht))
    replace_placeholder_in_docx(doc, "{{dung_han}}", str(dung_han))
    replace_placeholder_in_docx(doc, "{{ty_le_dung_han}}", f"{ty_le_dung_han}")
    replace_placeholder_in_docx(doc, "{{tre_han}}", str(tre_han))
    replace_placeholder_in_docx(doc, "{{ty_le_tre_han}}", f"{ty_le_tre_han}")

    # Điền bảng công việc (Table 1 - bảng thứ 2)
    if len(doc.tables) >= 2:
        table_cv = doc.tables[1]

        # Xóa các row mẫu (giữ header 3 dòng đầu)
        rows_to_delete = []
        for idx in range(3, len(table_cv.rows)):
            rows_to_delete.append(idx)

        for idx in reversed(rows_to_delete):
            table_cv._element.remove(table_cv.rows[idx]._element)

        # Thêm row mới cho từng công việc
        data_source = cong_viec_lanh_dao_list if is_lanh_dao else cong_viec_list

        for idx, cv in enumerate(data_source, start=1):
            new_row = table_cv.add_row()

            # (1) STT
            new_row.cells[0].text = str(idx)
            set_cell_font_times_new_roman(new_row.cells[0])

            if is_lanh_dao:
                # ===== MAPPING CHO LÃNH ĐẠO =====
                new_row.cells[1].text = cv.ten_cong_viec or "N/A"
                set_cell_font_times_new_roman(new_row.cells[1])

                new_row.cells[2].text = ""
                set_cell_font_times_new_roman(new_row.cells[2])

                new_row.cells[3].text = cv.mo_ta or ""
                set_cell_font_times_new_roman(new_row.cells[3])

                ngay_ht_str = cv.ngay_thuc_hien.strftime("%d/%m/%Y") if cv.ngay_thuc_hien else ""
                new_row.cells[4].text = ngay_ht_str
                set_cell_font_times_new_roman(new_row.cells[4])

                new_row.cells[5].text = ngay_ht_str
                set_cell_font_times_new_roman(new_row.cells[5])

                chua_hoan_thanh = cv.trang_thai_hoan_thanh == TrangThaiHoanThanh.CHUA_HOAN_THANH
                new_row.cells[6].text = "X" if chua_hoan_thanh else ""
                set_cell_font_times_new_roman(new_row.cells[6])

                dat_tien_do = (
                    cv.trang_thai_hoan_thanh == TrangThaiHoanThanh.DA_HOAN_THANH
                    and cv.so_loi_tien_do == 0
                )
                new_row.cells[7].text = "X" if dat_tien_do else ""
                set_cell_font_times_new_roman(new_row.cells[7])

                cham_tien_do = (
                    cv.trang_thai_hoan_thanh == TrangThaiHoanThanh.DA_HOAN_THANH
                    and cv.so_loi_tien_do > 0
                )
                new_row.cells[8].text = "X" if cham_tien_do else ""
                set_cell_font_times_new_roman(new_row.cells[8])

                ghi_chu = ""
                if cv.so_loi_chat_luong > 0:
                    ghi_chu += f"Lỗi CL ({cv.so_loi_chat_luong}): {cv.ghi_chu_loi_chat_luong or 'Không có mô tả'}. "
                if cv.so_loi_tien_do > 0:
                    ghi_chu += f"Lỗi TĐ ({cv.so_loi_tien_do}): {cv.ghi_chu_loi_tien_do or 'Không có mô tả'}."
                if cv.y_kien_lanh_dao:
                    ghi_chu += f" Ý kiến LĐ: {cv.y_kien_lanh_dao}."
                new_row.cells[9].text = ghi_chu.strip()
                set_cell_font_times_new_roman(new_row.cells[9])

            else:
                # ===== MAPPING CHO CÔNG CHỨC THƯỜNG =====
                ten_sp = ""
                if cv.danh_muc_sp:
                    ten_sp = cv.danh_muc_sp.ten_cong_viec
                    if cv.cap_do:
                        ten_sp += f" ({cv.cap_do.ten_cap_do})"
                new_row.cells[1].text = ten_sp or "N/A"
                set_cell_font_times_new_roman(new_row.cells[1])

                new_row.cells[2].text = ""
                set_cell_font_times_new_roman(new_row.cells[2])

                chi_tiet_cv = ""
                if cv.danh_muc_sp:
                    chi_tiet_cv = cv.danh_muc_sp.ten_cong_viec

                    parts = []
                    if cv.so_luong and cv.danh_muc_sp.sp_chuan:
                        ma_sp = cv.danh_muc_sp.sp_chuan.ma_sp
                        don_vi = "TK" if ma_sp == "SP1" else "VB" if ma_sp == "SP2" else "Giờ"
                        parts.append(f"tổng {cv.so_luong} {don_vi}")

                    if cv.cap_do:
                        parts.append(f"mức độ {cv.cap_do.ma_cap_do}")

                    if parts:
                        chi_tiet_cv += f" ({', '.join(parts)})"

                new_row.cells[3].text = chi_tiet_cv or ""
                set_cell_font_times_new_roman(new_row.cells[3])

                ngay_ht_str = cv.ngay_thuc_hien.strftime("%d/%m/%Y") if cv.ngay_thuc_hien else ""
                new_row.cells[4].text = ngay_ht_str
                set_cell_font_times_new_roman(new_row.cells[4])

                new_row.cells[5].text = ngay_ht_str
                set_cell_font_times_new_roman(new_row.cells[5])

                chua_hoan_thanh = cv.trang_thai != TrangThaiKeKhai.DA_PHE_DUYET
                new_row.cells[6].text = "X" if chua_hoan_thanh else ""
                set_cell_font_times_new_roman(new_row.cells[6])

                dat_tien_do = (
                    cv.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET
                    and cv.so_loi_tien_do == 0
                )
                new_row.cells[7].text = "X" if dat_tien_do else ""
                set_cell_font_times_new_roman(new_row.cells[7])

                cham_tien_do = (
                    cv.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET
                    and cv.so_loi_tien_do > 0
                )
                new_row.cells[8].text = "X" if cham_tien_do else ""
                set_cell_font_times_new_roman(new_row.cells[8])

                ghi_chu = ""
                if cv.ghi_chu_loi_chat_luong:
                    ghi_chu += f"Lỗi CL: {cv.ghi_chu_loi_chat_luong}. "
                if cv.ghi_chu_loi_tien_do:
                    ghi_chu += f"Lỗi TĐ: {cv.ghi_chu_loi_tien_do}."
                new_row.cells[9].text = ghi_chu.strip()
                set_cell_font_times_new_roman(new_row.cells[9])

    # Lưu vào buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    # Tên file
    ma_cc_safe = cc.ma_cc.replace("/", "-") if cc.ma_cc else "user"
    filename = f"BangKeCongViec_{ma_cc_safe}_Q{quy}_{nam}.docx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
