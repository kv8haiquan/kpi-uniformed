/**
 * scripts/docx_generator/generate.js
 * ====================================
 * Node.js script tạo DOCX cho hệ thống KPI.
 * 
 * Usage: node generate.js <report_type> <data_json_path> <output_path>
 *   report_type: "ca-nhan" | "don-vi" | "tong-hop"
 * 
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
            para([txt("CỤC HẢI QUAN", { bold: true, size: FONT_SIZE_SMALL })], { alignment: AlignmentType.CENTER }),
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
  children.push(titlePara(data.title));
  children.push(para([txt(`Tháng ${data.thang} năm ${data.nam}`)], { alignment: AlignmentType.CENTER }));
  if (!data.is_toan_chi_cuc && data.don_vi_name) {
    children.push(para([txt(`Đơn vị: ${data.don_vi_name}`, { italics: true })], { alignment: AlignmentType.CENTER }));
  }
  children.push(emptyPara());
  
  // 10 cột: STT, Họ tên, Đơn vị, Chức vụ, Điểm TC, Điểm KPI, Điểm tổng, XL Hệ thống, XL ĐT duyệt, XL CCT duyệt, Ghi chú
  const cols = [450, 1600, 1200, 1000, 700, 700, 700, 700, 700, 700, 621];
  
  const headerRow = new TableRow({ children: [
    headerCell("STT", { width: cols[0], fontSize: 16 }),
    headerCell("Họ và tên", { width: cols[1], fontSize: 16 }),
    headerCell("Đơn vị", { width: cols[2], fontSize: 16 }),
    headerCell("Chức vụ", { width: cols[3], fontSize: 16 }),
    headerCell("Điểm TC", { width: cols[4], fontSize: 16 }),
    headerCell("Điểm KPI", { width: cols[5], fontSize: 16 }),
    headerCell("Tổng điểm", { width: cols[6], fontSize: 16 }),
    headerCell("XL Hệ thống", { width: cols[7], fontSize: 16 }),
    headerCell("XL ĐT duyệt", { width: cols[8], fontSize: 16 }),
    headerCell("XL CCT duyệt", { width: cols[9], fontSize: 16 }),
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
  
  // Thống kê
  const tk = data.thong_ke || {};
  children.push(para([
    txt("Tổng số: ", { bold: true }), txt(`${tk.tong || 0} công chức`),
    txt("  |  Loại A: ", { bold: true }), txt(`${tk.A || 0}`),
    txt("  |  Loại B: ", { bold: true }), txt(`${tk.B || 0}`),
    txt("  |  Loại C: ", { bold: true }), txt(`${tk.C || 0}`),
    txt("  |  Loại D: ", { bold: true }), txt(`${tk.D || 0}`),
    txt("  |  Loại E: ", { bold: true }), txt(`${tk.E || 0}`),
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
  } else if (reportType === "don-vi" || reportType === "tong-hop") {
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