/**
 * scripts/docx_generator/generate.js
 * ====================================
 * Node.js script tạo DOCX cho hệ thống KPI.
 * 
 * Usage: node generate.js <report_type> <data_json_path> <output_path>
 *   report_type: "ca-nhan" | "don-vi" | "tong-hop"
 * 
 * Version: 1.1.0 (11/02/2026) - Thêm Mẫu 04 cho tổng hợp toàn Chi cục
 * Version: 1.0.0 (02/02/2026)
 */

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, HeadingLevel,
  BorderStyle, WidthType, ShadingType, VerticalAlign,
  PageNumber, PageBreak,
} = require("docx");

// =============================================================================
// CONSTANTS
// =============================================================================

const FONT = "Times New Roman";
const FONT_SIZE_NORMAL = 22;   // 11pt
const FONT_SIZE_SMALL = 20;    // 10pt  
const FONT_SIZE_TITLE = 28;    // 14pt
const FONT_SIZE_HEADER = 24;   // 12pt

// A4 page dimensions (DXA)
const PAGE_WIDTH = 11906;
const PAGE_HEIGHT = 16838;
const MARGIN_TOP = 1134;    // ~2cm
const MARGIN_BOTTOM = 1134;
const MARGIN_LEFT = 1701;   // ~3cm
const MARGIN_RIGHT = 1134;  // ~2cm
const CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT; // 9071

// Table border
const BORDER = { style: BorderStyle.SINGLE, size: 1, color: "000000" };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };
const NO_BORDER = { style: BorderStyle.NONE, size: 0 };
const NO_BORDERS = { top: NO_BORDER, bottom: NO_BORDER, left: NO_BORDER, right: NO_BORDER };

// Cell padding
const CELL_MARGINS = { top: 40, bottom: 40, left: 80, right: 80 };

// Xếp loại mapping
const XEP_LOAI_MAP = {
  A: "Hoàn thành xuất sắc nhiệm vụ",
  B: "Hoàn thành tốt nhiệm vụ",
  C: "Hoàn thành nhiệm vụ",
  D: "Không hoàn thành nhiệm vụ",
  E: "Không đánh giá",
};

// =============================================================================
// HELPERS
// =============================================================================
// Helper: số La Mã
function toRoman(num) {
  const map = { 1: "I", 2: "II", 3: "III", 4: "IV", 5: "V" };
  return map[num] || String(num);
}

function txt(text, opts = {}) {
  return new TextRun({ text: String(text), font: FONT, size: opts.size || FONT_SIZE_NORMAL, ...opts });
}

function para(children, opts = {}) {
  if (typeof children === "string") children = [txt(children)];
  return new Paragraph({ children, spacing: { after: 60, line: 276 }, ...opts });
}

function emptyPara() {
  return para([txt("")]);
}

function titlePara(text) {
  return para([txt(text, { bold: true, size: FONT_SIZE_TITLE })], { alignment: AlignmentType.CENTER, spacing: { after: 120 } });
}

function headerPara(text) {
  return para([txt(text, { bold: true, size: FONT_SIZE_HEADER })], { spacing: { before: 120, after: 80 } });
}

function cell(children, opts = {}) {
  if (typeof children === "string") children = [para([txt(children, { size: opts.fontSize || FONT_SIZE_NORMAL })])];
  if (!Array.isArray(children)) children = [children];
  
  return new TableCell({
    borders: opts.noBorder ? NO_BORDERS : BORDERS,
    margins: CELL_MARGINS,
    verticalAlign: opts.vAlign || VerticalAlign.CENTER,
    width: opts.width ? { size: opts.width, type: WidthType.DXA } : undefined,
    shading: opts.shading ? { fill: opts.shading, type: ShadingType.CLEAR } : undefined,
    columnSpan: opts.colSpan || undefined,
    rowSpan: opts.rowSpan || undefined,
    children,
  });
}

function headerCell(text, opts = {}) {
  return cell(
    [para([txt(text, { bold: true, size: opts.fontSize || FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER })],
    { shading: "D9E2F3", ...opts }
  );
}

function numCell(value, opts = {}) {
  const formatted = typeof value === "number" ? (Number.isInteger(value) ? value.toString() : value.toFixed(1)) : String(value || "");
  return cell(
    [para([txt(formatted, { size: opts.fontSize || FONT_SIZE_NORMAL })], { alignment: AlignmentType.CENTER })],
    opts
  );
}

function formatNum(v) {
  if (v === null || v === undefined) return "0";
  return Number.isInteger(v) ? v.toString() : Number(v).toFixed(1);
}

// =============================================================================
// MẪU 01: PHIẾU THEO DÕI, ĐÁNH GIÁ CÔNG CHỨC
// =============================================================================

function buildMau01(data) {
  const children = [];
  
  // Header: cơ quan
  children.push(
    new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      columnWidths: [4535, 4536],
      rows: [
        new TableRow({ children: [
          cell([
            para([txt("CHI CỤC HẢI QUAN KHU VỰC VIII", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
            para([txt(data.don_vi, { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
          ], { noBorder: true, width: 4535 }),
          cell([
            para([txt("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
            para([txt("Độc lập - Tự do - Hạnh phúc", { bold: true, size: FONT_SIZE_SMALL, underline: {} })], { alignment: AlignmentType.CENTER }),
          ], { noBorder: true, width: 4536 }),
        ]}),
      ],
    })
  );
  
  children.push(emptyPara());
  children.push(titlePara("PHIẾU THEO DÕI, ĐÁNH GIÁ CÔNG CHỨC"));
  children.push(para([txt(`(Kỳ theo dõi, đánh giá: Tháng ${data.thang}/${data.nam})`, { italics: true })], { alignment: AlignmentType.CENTER }));
  children.push(emptyPara());
  
  // Thông tin cá nhân
  children.push(para([txt("Họ và tên: ", { bold: true }), txt(data.ho_ten)]));
  children.push(para([txt("Chức vụ, chức danh: ", { bold: true }), txt(data.chuc_vu)]));
  children.push(para([txt("Đơn vị công tác: ", { bold: true }), txt(data.don_vi)]));
  children.push(emptyPara());
  
  // I. Tiêu chí chung
  children.push(headerPara("I. KẾT QUẢ THEO DÕI, ĐÁNH GIÁ THEO TIÊU CHÍ CHUNG"));
  
  // Bảng tiêu chí
  const tcCols = [600, 4200, 1000, 1200, 1200]; // sum ~ 8200
  const tcHeaderRow = new TableRow({ children: [
    headerCell("TT", { width: tcCols[0] }),
    headerCell("Tiêu chí chấm điểm", { width: tcCols[1] }),
    headerCell("Điểm tối đa", { width: tcCols[2] }),
    headerCell("Điểm tự chấm", { width: tcCols[3] }),
    headerCell("Điểm LĐ chấm", { width: tcCols[4] }),
  ]});
  
  const tcRows = [tcHeaderRow];
  let totalMax = 0, totalTu = 0, totalLD = 0;
  
  (data.tieu_chi_items || []).forEach((item, idx) => {
    totalMax += item.diem_toi_da || 0;
    totalTu += item.diem_tu_cham || 0;
    totalLD += item.diem_lanh_dao || 0;
    
    tcRows.push(new TableRow({ children: [
      numCell(idx + 1, { width: tcCols[0] }),
      cell(item.ten || "", { width: tcCols[1] }),
      numCell(item.diem_toi_da, { width: tcCols[2] }),
      numCell(item.diem_tu_cham, { width: tcCols[3] }),
      numCell(item.diem_lanh_dao, { width: tcCols[4] }),
    ]}));
  });
  
  // Dòng tổng
  tcRows.push(new TableRow({ children: [
    cell([para([txt("Tổng cộng", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER })], { colSpan: 2, width: tcCols[0] + tcCols[1] }),
    numCell(totalMax, { width: tcCols[2] }),
    numCell(totalTu, { width: tcCols[3] }),
    numCell(totalLD, { width: tcCols[4] }),
  ]}));
  
  children.push(new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: tcCols,
    rows: tcRows,
  }));
  
  children.push(emptyPara());
  
  // II. KPI
  children.push(headerPara("II. KẾT QUẢ THEO DÕI, ĐÁNH GIÁ THEO KPI"));
  children.push(para([txt(`Điểm KPI (×70): ${formatNum(data.diem_kpi)} / 70 điểm`)]));
  children.push(emptyPara());
  
  // III. Tổng hợp
  children.push(headerPara("III. TỔNG HỢP KẾT QUẢ THEO DÕI, ĐÁNH GIÁ CÔNG CHỨC"));
  children.push(para([txt("1. Điểm tiêu chí chung: "), txt(`${formatNum(data.diem_tieu_chi_chung)} / 30 điểm`, { bold: true })]));
  children.push(para([txt("2. Điểm KPI (×70): "), txt(`${formatNum(data.diem_kpi)} / 70 điểm`, { bold: true })]));
  children.push(para([txt("3. Tổng điểm: "), txt(`${formatNum(data.diem_tong)} / 100 điểm`, { bold: true })]));
  children.push(para([txt("4. Xếp loại: "), txt(`${data.xep_loai} - ${XEP_LOAI_MAP[data.xep_loai] || ""}`, { bold: true })]));
  children.push(emptyPara());
  children.push(para([txt("5. Ưu điểm: "), txt("..........................................................")]));
  children.push(para([txt("6. Hạn chế, khuyết điểm: "), txt("............................................")]));
  children.push(para([txt("7. Ý kiến nhận xét của cấp có thẩm quyền: "), txt("......................")]));
  children.push(emptyPara());
  children.push(emptyPara());
  
  // Chữ ký
  children.push(new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: [4535, 4536],
    rows: [
      new TableRow({ children: [
        cell([
          para([txt("NGƯỜI ĐƯỢC ĐÁNH GIÁ", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
          para([txt("(Ký, ghi rõ họ tên)", { italics: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
          emptyPara(), emptyPara(), emptyPara(),
          para([txt(data.ho_ten, { bold: true })], { alignment: AlignmentType.CENTER }),
        ], { noBorder: true, width: 4535 }),
        cell([
          para([txt("CẤP CÓ THẨM QUYỀN", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
          para([txt("(Ký tên, đóng dấu)", { italics: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
          emptyPara(), emptyPara(), emptyPara(),
          para([txt(".............................")], { alignment: AlignmentType.CENTER }),
        ], { noBorder: true, width: 4536 }),
      ]}),
    ],
  }));
  
  return children;
}


// =============================================================================
// MẪU 02: BẢNG KÊ CÔNG VIỆC CÁ NHÂN
// =============================================================================

function buildMau02(data) {
  const children = [];
  
  // Header
  children.push(
    new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      columnWidths: [4535, 4536],
      rows: [
        new TableRow({ children: [
          cell([
            para([txt("CHI CỤC HẢI QUAN KHU VỰC VIII", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
            para([txt(data.don_vi, { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
          ], { noBorder: true, width: 4535 }),
          cell([
            para([txt("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
            para([txt("Độc lập - Tự do - Hạnh phúc", { bold: true, size: FONT_SIZE_SMALL, underline: {} })], { alignment: AlignmentType.CENTER }),
          ], { noBorder: true, width: 4536 }),
        ]}),
      ],
    })
  );
  
  children.push(emptyPara());
  children.push(titlePara("BẢNG KÊ CÔNG VIỆC CÁ NHÂN"));
  children.push(para([txt(`Tháng ${data.thang} năm ${data.nam}`, { italics: true })], { alignment: AlignmentType.CENTER }));
  children.push(emptyPara());
  
  // Thông tin
  children.push(para([txt("Họ và tên: ", { bold: true }), txt(data.ho_ten)]));
  children.push(para([txt("Chức vụ: ", { bold: true }), txt(data.chuc_vu), txt("     Đơn vị: ", { bold: true }), txt(data.don_vi)]));
  children.push(para([
    txt("Số ngày làm việc: ", { bold: true }), txt(formatNum(data.so_ngay_lam_viec)),
    txt("     Số ngày nghỉ: ", { bold: true }), txt(formatNum(data.so_ngay_nghi)),
    txt("     SP được giao: ", { bold: true }), txt(formatNum(data.target_sp)),
  ]));
  children.push(emptyPara());
  
  // Bảng kê công việc
  // 10 cột: STT, Tên CV, Mức, SL, SP quy đổi, SP CL, SP TĐ, Lỗi CL, Lỗi TĐ, Ghi chú
  const cols = [500, 2500, 600, 600, 800, 800, 800, 700, 700, 700]; // ~8700
  
  const headerRow = new TableRow({ children: [
    headerCell("STT", { width: cols[0], fontSize: 18 }),
    headerCell("Tên công việc", { width: cols[1], fontSize: 18 }),
    headerCell("Mức", { width: cols[2], fontSize: 18 }),
    headerCell("SL", { width: cols[3], fontSize: 18 }),
    headerCell("SP QĐ", { width: cols[4], fontSize: 18 }),
    headerCell("SP CL", { width: cols[5], fontSize: 18 }),
    headerCell("SP TĐ", { width: cols[6], fontSize: 18 }),
    headerCell("Lỗi CL", { width: cols[7], fontSize: 18 }),
    headerCell("Lỗi TĐ", { width: cols[8], fontSize: 18 }),
    headerCell("Ghi chú", { width: cols[9], fontSize: 18 }),
  ]});
  
  const rows = [headerRow];
  
  (data.cong_viec_items || []).forEach((item, idx) => {
    rows.push(new TableRow({ children: [
      numCell(idx + 1, { width: cols[0], fontSize: FONT_SIZE_SMALL }),
      cell(item.ten_cong_viec || "", { width: cols[1], fontSize: FONT_SIZE_SMALL }),
      numCell(item.cap_do, { width: cols[2], fontSize: FONT_SIZE_SMALL }),
      numCell(item.so_luong, { width: cols[3], fontSize: FONT_SIZE_SMALL }),
      numCell(item.sp_quy_doi, { width: cols[4], fontSize: FONT_SIZE_SMALL }),
      numCell(item.sp_chat_luong, { width: cols[5], fontSize: FONT_SIZE_SMALL }),
      numCell(item.sp_tien_do, { width: cols[6], fontSize: FONT_SIZE_SMALL }),
      numCell(item.so_loi_chat_luong, { width: cols[7], fontSize: FONT_SIZE_SMALL }),
      numCell(item.so_loi_tien_do, { width: cols[8], fontSize: FONT_SIZE_SMALL }),
      cell("", { width: cols[9], fontSize: FONT_SIZE_SMALL }),
    ]}));
  });
  
  // Dòng tổng
  rows.push(new TableRow({ children: [
    cell([para([txt("TỔNG CỘNG", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER })], { colSpan: 4, width: cols[0]+cols[1]+cols[2]+cols[3] }),
    numCell(data.tong_sp_quy_doi, { width: cols[4], fontSize: FONT_SIZE_SMALL }),
    numCell(data.tong_sp_chat_luong, { width: cols[5], fontSize: FONT_SIZE_SMALL }),
    numCell(data.tong_sp_tien_do, { width: cols[6], fontSize: FONT_SIZE_SMALL }),
    cell("", { width: cols[7], fontSize: FONT_SIZE_SMALL }),
    cell("", { width: cols[8], fontSize: FONT_SIZE_SMALL }),
    cell("", { width: cols[9], fontSize: FONT_SIZE_SMALL }),
  ]}));
  
  children.push(new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: cols,
    rows,
  }));
  
  children.push(emptyPara());
  
  // Tổng hợp điểm
  children.push(headerPara("TỔNG HỢP"));
  children.push(para([txt("Điểm tiêu chí chung: "), txt(`${formatNum(data.diem_tieu_chi_chung)} / 30 điểm`, { bold: true })]));
  children.push(para([txt("Điểm KPI (×70): "), txt(`${formatNum(data.diem_kpi)} / 70 điểm`, { bold: true })]));
  children.push(para([txt("Tổng điểm: "), txt(`${formatNum(data.diem_tong)} / 100 điểm`, { bold: true })]));
  children.push(para([txt("Xếp loại: "), txt(`${data.xep_loai} - ${XEP_LOAI_MAP[data.xep_loai] || ""}`, { bold: true })]));
  children.push(emptyPara());
  children.push(emptyPara());
  
  // Chữ ký
  children.push(new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: [4535, 4536],
    rows: [
      new TableRow({ children: [
        cell([
          para([txt("NGƯỜI KÊ KHAI", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
          para([txt("(Ký, ghi rõ họ tên)", { italics: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
          emptyPara(), emptyPara(), emptyPara(),
          para([txt(data.ho_ten, { bold: true })], { alignment: AlignmentType.CENTER }),
        ], { noBorder: true, width: 4535 }),
        cell([
          para([txt("TRƯỞNG ĐƠN VỊ", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
          para([txt("(Ký tên, đóng dấu)", { italics: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
          emptyPara(), emptyPara(), emptyPara(),
          para([txt(".............................")], { alignment: AlignmentType.CENTER }),
        ], { noBorder: true, width: 4536 }),
      ]}),
    ],
  }));
  
  return children;
}


// =============================================================================
// MẪU 03: BẢNG TỔNG HỢP KẾT QUẢ XẾP LOẠI
// =============================================================================

function buildMau03(data) {
  const children = [];
  
  // Header
  children.push(
    new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      columnWidths: [4535, 4536],
      rows: [
        new TableRow({ children: [
          cell([
            para([txt("CHI CỤC HẢI QUAN KHU VỰC VIII", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
          ], { noBorder: true, width: 4535 }),
          cell([
            para([txt("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
            para([txt("Độc lập - Tự do - Hạnh phúc", { bold: true, size: FONT_SIZE_SMALL, underline: {} })], { alignment: AlignmentType.CENTER }),
          ], { noBorder: true, width: 4536 }),
        ]}),
      ],
    })
  );
  
  children.push(emptyPara());
  // Title cố định theo Mẫu mới (BaoCao_DonVi_03_2026.docx — 05/05/2026):
  // "BẢNG TỔNG HỢP KẾT QUẢ ĐÁNH GIÁ CÔNG CHỨC-NGƯỜI LAO ĐỘNG".
  children.push(titlePara("BẢNG TỔNG HỢP KẾT QUẢ ĐÁNH GIÁ CÔNG CHỨC-NGƯỜI LAO ĐỘNG"));
  // Nếu data.quy được truyền → header "Quý X năm Y", ngược lại "Tháng X năm Y"
  const periodText = data.quy
    ? `Quý ${data.quy} năm ${data.nam}`
    : `Tháng ${data.thang} năm ${data.nam}`;
  children.push(para([txt(periodText)], { alignment: AlignmentType.CENTER }));
  if (!data.is_toan_chi_cuc && data.don_vi_name) {
    children.push(para([txt(`Đơn vị: ${data.don_vi_name}`, { italics: true })], { alignment: AlignmentType.CENTER }));
  }
  children.push(emptyPara());

  // 11 cột: STT, Họ tên, Đơn vị, Chức vụ, Điểm TC, Điểm KPI, Tổng điểm,
  // ĐG Hệ thống, ĐG ĐT duyệt, ĐG CCT duyệt, Ghi chú
  const cols = [450, 1600, 1200, 1000, 700, 700, 700, 700, 700, 700, 621];

  const headerRow = new TableRow({ children: [
    headerCell("STT", { width: cols[0], fontSize: 16 }),
    headerCell("Họ và tên", { width: cols[1], fontSize: 16 }),
    headerCell("Đơn vị", { width: cols[2], fontSize: 16 }),
    headerCell("Chức vụ", { width: cols[3], fontSize: 16 }),
    headerCell("Điểm TC", { width: cols[4], fontSize: 16 }),
    headerCell("Điểm KPI", { width: cols[5], fontSize: 16 }),
    headerCell("Tổng điểm", { width: cols[6], fontSize: 16 }),
    headerCell("ĐG Hệ thống", { width: cols[7], fontSize: 16 }),
    headerCell("ĐG ĐT duyệt", { width: cols[8], fontSize: 16 }),
    headerCell("ĐG CCT duyệt", { width: cols[9], fontSize: 16 }),
    headerCell("Ghi chú", { width: cols[10], fontSize: 16 }),
  ]});
  
  const rows = [headerRow];
  
  (data.rows || []).forEach((item) => {
    rows.push(new TableRow({ children: [
      numCell(item.stt, { width: cols[0], fontSize: 18 }),
      cell(item.ho_ten, { width: cols[1], fontSize: 18 }),
      cell(item.don_vi, { width: cols[2], fontSize: 18 }),
      cell(item.chuc_vu || "", { width: cols[3], fontSize: 18 }),
      numCell(item.diem_tcc, { width: cols[4], fontSize: 18 }),
      numCell(item.diem_kpi, { width: cols[5], fontSize: 18 }),
      numCell(item.diem_tong, { width: cols[6], fontSize: 18 }),
      numCell(item.xep_loai_he_thong, { width: cols[7], fontSize: 18 }),
      numCell(item.xep_loai_de_xuat || "", { width: cols[8], fontSize: 18 }),
      numCell(item.xep_loai_quyet_dinh || "", { width: cols[9], fontSize: 18 }),
      cell(item.ghi_chu || "", { width: cols[10], fontSize: 18 }),
    ]}));
  });
  
  children.push(new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: cols,
    rows,
  }));
  
  children.push(emptyPara());
  
  // Thống kê — theo Mẫu mới (BaoCao_DonVi_03_2026.docx — 05/05/2026):
  // "Mức" cho A/B/C, "Loại" cho D, KHÔNG hiển thị E.
  const tk = data.thong_ke || {};
  children.push(para([
    txt("Tổng số: ", { bold: true }), txt(`${tk.tong || 0} công chức`),
    txt("  |  Mức A: ", { bold: true }), txt(`${tk.A || 0}`),
    txt("  |  Mức B: ", { bold: true }), txt(`${tk.B || 0}`),
    txt("  |  Mức C: ", { bold: true }), txt(`${tk.C || 0}`),
    txt("  |  Loại D: ", { bold: true }), txt(`${tk.D || 0}`),
  ]));
  children.push(emptyPara());
  children.push(emptyPara());
  
  // Chữ ký
  children.push(new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: [4535, 4536],
    rows: [
      new TableRow({ children: [
        cell([
          para([txt("NGƯỜI LẬP BIỂU", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
          para([txt("(Ký, ghi rõ họ tên)", { italics: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
        ], { noBorder: true, width: 4535 }),
        cell([
          para([txt("CHI CỤC TRƯỞNG", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
          para([txt("(Ký tên, đóng dấu)", { italics: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
        ], { noBorder: true, width: 4536 }),
      ]}),
    ],
  }));
  
  return children;
}


// =============================================================================
// MẪU 04: DANH SÁCH PHÊ DUYỆT KẾT QUẢ XẾP LOẠI CHẤT LƯỢNG CÔNG CHỨC
// =============================================================================

function buildMau04(data) {
  const children = [];
  
  // Header đơn giản - chỉ có tên cơ quan và quốc hiệu
  children.push(
    new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      columnWidths: [4535, 4536],
      rows: [
        new TableRow({ children: [
          cell([
            para([txt("CHI CỤC HẢI QUAN KHU VỰC VIII", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
          ], { noBorder: true, width: 4535 }),
          cell([
            para([txt("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
            para([txt("Độc lập - Tự do - Hạnh phúc", { bold: true, size: FONT_SIZE_SMALL, underline: {} })], { alignment: AlignmentType.CENTER }),
          ], { noBorder: true, width: 4536 }),
        ]}),
      ],
    })
  );
  
  children.push(emptyPara());
  
  // Title
  children.push(titlePara(data.title || "DANH SÁCH PHÊ DUYỆT KẾT QUẢ XẾP LOẠI CHẤT LƯỢNG CÔNG CHỨC"));
  children.push(para([txt(data.subtitle || `Tháng ${data.thang} năm ${data.nam}`)], { alignment: AlignmentType.CENTER }));
  children.push(emptyPara());
  
  // Bảng chính: STT, Mã CC, Họ tên, Năm sinh, Chức vụ, Đơn vị, Điểm, Xếp loại, Ghi chú
  const cols = [400, 900, 1500, 700, 1000, 1400, 900, 1200, 1071];
  
  const headerRow = new TableRow({ children: [
    headerCell("TT", { width: cols[0], fontSize: 16 }),
    headerCell("Mã công chức", { width: cols[1], fontSize: 16 }),
    headerCell("Họ và tên", { width: cols[2], fontSize: 16 }),
    headerCell("Năm sinh", { width: cols[3], fontSize: 16 }),
    headerCell("Chức vụ", { width: cols[4], fontSize: 16 }),
    headerCell("Đơn vị", { width: cols[5], fontSize: 16 }),
    headerCell("Điểm theo dõi, đánh giá tháng", { width: cols[6], fontSize: 16 }),
    headerCell("Mức xếp loại chất lượng tháng", { width: cols[7], fontSize: 16 }),
    headerCell("Ghi chú", { width: cols[8], fontSize: 16 }),
  ]});
  
  const rows = [headerRow];
  
  (data.rows || []).forEach((item) => {
    // Map xếp loại sang tên đầy đủ
    const xepLoaiText = XEP_LOAI_MAP[item.xep_loai] || item.xep_loai || "";
    
    rows.push(new TableRow({ children: [
      numCell(item.stt, { width: cols[0], fontSize: 18 }),
      cell(item.ma_cc || "", { width: cols[1], fontSize: 18 }),
      cell(item.ho_ten || "", { width: cols[2], fontSize: 18 }),
      numCell(item.nam_sinh || "", { width: cols[3], fontSize: 18 }),
      cell(item.chuc_vu || "", { width: cols[4], fontSize: 18 }),
      cell(item.don_vi || "", { width: cols[5], fontSize: 18 }),
      numCell(item.diem_tong || 0, { width: cols[6], fontSize: 18 }),
      cell(xepLoaiText, { width: cols[7], fontSize: 18 }),
      cell(item.ghi_chu || "", { width: cols[8], fontSize: 18 }),
    ]}));
  });
  
  children.push(new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: cols,
    rows,
  }));
  
  children.push(emptyPara());
  children.push(emptyPara());
  
  // Bảng thống kê và vinh danh (2 cột song song)
  const tkCols = [1200, 800, 800];  // Mức xếp loại | Số lượng | Tỷ lệ %
  const vdCols = [400, 1500, 1400, 800];  // STT | Họ tên | Đơn vị | Điểm
  
  // Tạo bảng thống kê
  const tkRows = [
    new TableRow({ children: [
      headerCell("Mức xếp loại", { width: tkCols[0], fontSize: 18 }),
      headerCell("Số lượng", { width: tkCols[1], fontSize: 18 }),
      headerCell("Tỷ lệ %", { width: tkCols[2], fontSize: 18 }),
    ]}),
  ];
  
  (data.thong_ke || []).forEach((tk) => {
    tkRows.push(new TableRow({ children: [
      cell(tk.muc || "", { width: tkCols[0], fontSize: 18 }),
      numCell(tk.so_luong || 0, { width: tkCols[1], fontSize: 18 }),
      numCell(tk.ty_le ? `${tk.ty_le}%` : "0%", { width: tkCols[2], fontSize: 18 }),
    ]}));
  });
  
  // Tạo bảng vinh danh
  const vdRows = [
    new TableRow({ children: [
      headerCell("STT", { width: vdCols[0], fontSize: 18 }),
      headerCell("Họ và tên", { width: vdCols[1], fontSize: 18 }),
      headerCell("Đơn vị", { width: vdCols[2], fontSize: 18 }),
      headerCell("Điểm", { width: vdCols[3], fontSize: 18 }),
    ]}),
  ];
  
  (data.vinh_danh || []).forEach((vd) => {
    vdRows.push(new TableRow({ children: [
      numCell(vd.stt || "", { width: vdCols[0], fontSize: 18 }),
      cell(vd.ho_ten || "", { width: vdCols[1], fontSize: 18 }),
      cell(vd.don_vi || "", { width: vdCols[2], fontSize: 18 }),
      numCell(vd.diem || 0, { width: vdCols[3], fontSize: 18 }),
    ]}));
  });
  
  // Bảng tổng hợp (2 bảng con)
  children.push(new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: [3200, 400, 5471],
    rows: [
      new TableRow({ children: [
        // Cột trái: Bảng thống kê
        cell([
          para([txt("TỔNG HỢP", { bold: true })], { alignment: AlignmentType.CENTER, spacing: { after: 80 } }),
          new Table({
            width: { size: 100, type: WidthType.PERCENTAGE },
            columnWidths: tkCols,
            rows: tkRows,
          }),
        ], { noBorder: true, width: 3200, vAlign: VerticalAlign.TOP }),
        // Cột giữa: khoảng trống
        cell([para([txt("")])], { noBorder: true, width: 400 }),
        // Cột phải: Bảng vinh danh
        cell([
          para([txt("VINH DANH CÁC CÔNG CHỨC XUẤT SẮC NHẤT", { bold: true })], { alignment: AlignmentType.CENTER, spacing: { after: 80 } }),
          new Table({
            width: { size: 100, type: WidthType.PERCENTAGE },
            columnWidths: vdCols,
            rows: vdRows,
          }),
        ], { noBorder: true, width: 5471, vAlign: VerticalAlign.TOP }),
      ]}),
    ],
  }));
  
  children.push(emptyPara());
  children.push(emptyPara());
  
  // Chữ ký
  children.push(new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: [4535, 4536],
    rows: [
      new TableRow({ children: [
        cell([
          para([txt("NGƯỜI LẬP BIỂU", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
          para([txt("(Ký, ghi rõ họ tên)", { italics: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
        ], { noBorder: true, width: 4535 }),
        cell([
          para([txt("CHI CỤC TRƯỞNG", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
          para([txt("(Ký tên, đóng dấu)", { italics: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
        ], { noBorder: true, width: 4536 }),
      ]}),
    ],
  }));
  
  return children;
}

// =============================================================================
// MẪU 05: BÁO CÁO CÔNG CHỨC CÓ THÀNH TÍCH ĐỔI MỚI SÁNG TẠO
// =============================================================================

function buildMau05(data) {
  const allChildren = [];
  
  (data.cong_chucs || []).forEach((cc, index) => {
    // Page break trước mỗi CC (trừ người đầu tiên)
    if (index > 0) {
      allChildren.push(new Paragraph({ children: [new PageBreak()] }));
    }
    
    // Header
    allChildren.push(
      new Table({
        width: { size: 100, type: WidthType.PERCENTAGE },
        columnWidths: [4535, 4536],
        rows: [
          new TableRow({ children: [
            cell([
              para([txt("CHI CỤC HẢI QUAN KHU VỰC VIII", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
            ], { noBorder: true, width: 4535 }),
            cell([
              para([txt("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
              para([txt("Độc lập - Tự do - Hạnh phúc", { bold: true, size: FONT_SIZE_SMALL, underline: {} })], { alignment: AlignmentType.CENTER }),
            ], { noBorder: true, width: 4536 }),
          ]}),
        ],
      })
    );
    
    allChildren.push(emptyPara());
    allChildren.push(titlePara(data.title || "PHIẾU THEO DÕI TIÊU CHÍ CHUNG - CÔNG CHỨC CÓ THÀNH TÍCH ĐỔI MỚI"));
    allChildren.push(para([txt(`Tháng ${data.thang} năm ${data.nam}`)], { alignment: AlignmentType.CENTER }));
    allChildren.push(emptyPara());
    
    // Thông tin CC
    allChildren.push(para([txt("Họ và tên: ", { bold: true }), txt(cc.ho_ten)]));
    allChildren.push(para([txt("Mã công chức: ", { bold: true }), txt(cc.ma_cc)]));
    allChildren.push(para([txt("Đơn vị: ", { bold: true }), txt(cc.don_vi)]));
    if (cc.chuc_vu) {
      allChildren.push(para([txt("Chức vụ: ", { bold: true }), txt(cc.chuc_vu)]));
    }
    allChildren.push(emptyPara());
    
    // Bảng tiêu chí chung
    const cols = [400, 3500, 700, 800, 800, 2871];
    
    const headerRow = new TableRow({ children: [
      headerCell("TT", { width: cols[0], fontSize: 18 }),
      headerCell("Tiêu chí chấm điểm", { width: cols[1], fontSize: 18 }),
      headerCell("Điểm tối đa", { width: cols[2], fontSize: 18 }),
      headerCell("CC tự chấm", { width: cols[3], fontSize: 18 }),
      headerCell("LĐ duyệt", { width: cols[4], fontSize: 18 }),
      headerCell("Ghi chú / Minh chứng", { width: cols[5], fontSize: 18 }),
    ]});
    
    const rows = [headerRow];
    let currentNhom = 0;
    const nhomNames = {
      1: "Phẩm chất chính trị, đạo đức",
      2: "Năng lực chuyên môn, nghiệp vụ", 
      3: "Năng lực đổi mới, sáng tạo",
    };
    
    (cc.tieu_chi || []).forEach((tc) => {
      // Header nhóm
      if (tc.nhom !== currentNhom) {
        currentNhom = tc.nhom;
        rows.push(new TableRow({ children: [
          cell([para([txt(toRoman(tc.nhom), { bold: true, size: 18 })])], { width: cols[0], shading: "E8E8E8" }),
          cell([para([txt(nhomNames[tc.nhom] || "", { bold: true, size: 18 })])], { width: cols[1] + cols[2] + cols[3] + cols[4] + cols[5], shading: "E8E8E8", colSpan: 5 }),
        ]}));
      }
      
      // Dòng tiêu chí
      const diemCcText = tc.is_achieved_cc ? `✓ (${tc.diem_cc})` : `✗ (0)`;
      const diemLdText = tc.is_achieved_ld === null ? "-" : (tc.is_achieved_ld ? `✓ (${tc.diem_ld})` : `✗ (0)`);
      
      // Highlight nhóm III có ghi chú
      const isNhom3WithNote = tc.nhom === 3 && tc.ghi_chu;
      
      rows.push(new TableRow({ children: [
        numCell(tc.ma, { width: cols[0], fontSize: 18 }),
        cell(tc.ten, { width: cols[1], fontSize: 18 }),
        numCell(tc.diem_toi_da, { width: cols[2], fontSize: 18 }),
        numCell(diemCcText, { width: cols[3], fontSize: 18 }),
        numCell(diemLdText, { width: cols[4], fontSize: 18 }),
        cell(tc.ghi_chu || "", { width: cols[5], fontSize: 16, shading: isNhom3WithNote ? "FFFDE7" : undefined }),
      ]}));
    });
    
    // Dòng tổng cộng
    rows.push(new TableRow({ children: [
      cell([para([txt("", { bold: true })])], { width: cols[0] }),
      cell([para([txt("Tổng cộng", { bold: true, size: 18 })])], { width: cols[1] }),
      numCell("30", { width: cols[2], fontSize: 18 }),
      numCell(cc.tong_diem_cc, { width: cols[3], fontSize: 18 }),
      numCell(cc.tong_diem_ld || "-", { width: cols[4], fontSize: 18 }),
      cell("", { width: cols[5] }),
    ]}));
    
    allChildren.push(new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      columnWidths: cols,
      rows,
    }));
    
    allChildren.push(emptyPara());
    allChildren.push(para([
      txt("Tổng điểm tiêu chí chung: ", { bold: true }), 
      txt(`${cc.tong_diem_ld || cc.tong_diem_cc}/30`),
      txt("   |   Điểm nhóm III: ", { bold: true }),
      txt(`${cc.diem_nhom3_ld || cc.diem_nhom3_cc}/10`),
    ]));
    
    allChildren.push(emptyPara());
    allChildren.push(emptyPara());
    
    // Chữ ký
    allChildren.push(new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      columnWidths: [4535, 4536],
      rows: [
        new TableRow({ children: [
          cell([
            para([txt("CÔNG CHỨC TỰ ĐÁNH GIÁ", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
            para([txt("(Ký, ghi rõ họ tên)", { italics: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
            emptyPara(), emptyPara(), emptyPara(),
            para([txt(cc.ho_ten, { bold: true })], { alignment: AlignmentType.CENTER }),
          ], { noBorder: true, width: 4535 }),
          cell([
            para([txt("TRƯỞNG ĐƠN VỊ", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
            para([txt("(Ký tên, đóng dấu)", { italics: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
          ], { noBorder: true, width: 4536 }),
        ]}),
      ],
    }));
  });
  
  return allChildren;
}

// =============================================================================
// MẪU 03 TỔNG HỢP: GHÉP NHIỀU ĐƠN VỊ (MỖI ĐƠN VỊ 1 TRANG)
// =============================================================================

function buildMau03TongHop(data) {
  // data.don_vi_list là mảng các mau03_data của từng đơn vị
  const allChildren = [];
  
  (data.don_vi_list || []).forEach((donViData, index) => {
    // Thêm page break trước mỗi đơn vị (trừ đơn vị đầu tiên)
    if (index > 0) {
      allChildren.push(new Paragraph({ children: [new PageBreak()] }));
    }
    
    // Build nội dung Mẫu 03 cho đơn vị này
    const donViChildren = buildMau03(donViData);
    allChildren.push(...donViChildren);
  });
  
  return allChildren;
}

// =============================================================================
// MAIN: GENERATE DOCUMENT
// =============================================================================

async function main() {
  const [,, reportType, dataPath, outputPath] = process.argv;
  
  if (!reportType || !dataPath || !outputPath) {
    console.error("Usage: node generate.js <report_type> <data_json_path> <output_path>");
    process.exit(1);
  }
  
  const rawData = JSON.parse(fs.readFileSync(dataPath, "utf-8"));
  
  let sections = [];
  
  if (reportType === "ca-nhan") {
    // Mẫu 01 + Mẫu 02 trong 1 file, tách page
    const mau01Children = buildMau01(rawData.mau01);
    const mau02Children = buildMau02(rawData.mau02);
    
    sections = [
      {
        properties: {
          page: {
            size: { width: PAGE_WIDTH, height: PAGE_HEIGHT },
            margin: { top: MARGIN_TOP, bottom: MARGIN_BOTTOM, left: MARGIN_LEFT, right: MARGIN_RIGHT },
          },
        },
        children: mau01Children,
      },
      {
        properties: {
          page: {
            size: { width: PAGE_WIDTH, height: PAGE_HEIGHT },
            margin: { top: MARGIN_TOP, bottom: MARGIN_BOTTOM, left: MARGIN_LEFT, right: MARGIN_RIGHT },
          },
        },
        children: mau02Children,
      },
    ];
  } else if (reportType === "don-vi") {
    // Mẫu 03 - landscape cho bảng rộng
    const mau03Children = buildMau03(rawData);
    
    sections = [{
      properties: {
        page: {
          size: { width: PAGE_HEIGHT, height: PAGE_WIDTH, orientation: "landscape" },
          margin: { top: MARGIN_LEFT, bottom: MARGIN_RIGHT, left: MARGIN_TOP, right: MARGIN_BOTTOM },
        },
      },
      children: mau03Children,
    }];

    
  } else if (reportType === "don-vi-tong-hop") {
    // Mẫu 03 tổng hợp - ghép tất cả đơn vị
    const mau03TongHopChildren = buildMau03TongHop(rawData);
    
    sections = [{
      properties: {
        page: {
          size: { width: PAGE_HEIGHT, height: PAGE_WIDTH, orientation: "landscape" },
          margin: { top: MARGIN_LEFT, bottom: MARGIN_RIGHT, left: MARGIN_TOP, right: MARGIN_BOTTOM },
        },
      },
      children: mau03TongHopChildren,
    }];
  } else if (reportType === "mau05-doi-moi") {
    // Mẫu 05 - portrait, mỗi CC 1 trang
    const mau05Children = buildMau05(rawData);
    
    sections = [{
      properties: {
        page: {
          size: { width: PAGE_WIDTH, height: PAGE_HEIGHT },
          margin: { top: MARGIN_TOP, bottom: MARGIN_BOTTOM, left: MARGIN_LEFT, right: MARGIN_RIGHT },
        },
      },
      children: mau05Children,
    }];
  } else if (reportType === "tong-hop") {
    // Mẫu 04 - landscape cho danh sách toàn Chi cục
    const mau04Children = buildMau04(rawData);
    
    sections = [{
      properties: {
        page: {
          size: { width: PAGE_HEIGHT, height: PAGE_WIDTH, orientation: "landscape" },
          margin: { top: MARGIN_LEFT, bottom: MARGIN_RIGHT, left: MARGIN_TOP, right: MARGIN_BOTTOM },
        },
      },
      children: mau04Children,
    }];
  } else {
    console.error(`Unknown report type: ${reportType}`);
    process.exit(1);
  }
  
  const doc = new Document({
    styles: {
      default: {
        document: { run: { font: FONT, size: FONT_SIZE_NORMAL } },
      },
    },
    sections,
  });
  
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);
  console.log(`Generated: ${outputPath} (${buffer.length} bytes)`);
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});