/**
 * src/lib/ky-tieu-chi.ts
 * ======================
 * Kỳ chấm TIÊU CHÍ CHUNG (30 điểm): theo THÁNG (cũ) hay theo QUÝ (mới).
 *
 * Căn cứ: Công văn 21169/CHQ-TCCB ngày 28/8/2026 — "Từ quý III/2026, kỳ đánh giá,
 * xếp loại trên Phần mềm được thiết lập theo quý".
 *
 * PHẢI giữ đồng bộ với backend `app/core/ky_tieu_chi.py` (cùng mốc, cùng quy tắc
 * tháng neo). Backend luôn tự quy tháng gửi lên về tháng neo, nên phía FE chỉ cần
 * đúng để HIỂN THỊ và dựng bộ chọn kỳ.
 */

/** (năm, quý) — mọi kỳ TỪ mốc này trở đi chấm tiêu chí chung theo QUÝ. */
export const TC_THEO_QUY_TU = { nam: 2026, quy: 3 };

export function quyCuaThang(thang: number): number {
  return Math.floor((thang - 1) / 3) + 1;
}

export function cacThangTrongQuy(quy: number): number[] {
  const dau = (quy - 1) * 3 + 1;
  return [dau, dau + 1, dau + 2];
}

export function thangCuoiQuy(quy: number): number {
  return quy * 3;
}

/** Kỳ này chấm tiêu chí chung theo quý chưa? */
export function tcTheoQuy(thang: number, nam: number): boolean {
  const quy = quyCuaThang(thang);
  return nam > TC_THEO_QUY_TU.nam || (nam === TC_THEO_QUY_TU.nam && quy >= TC_THEO_QUY_TU.quy);
}

/** Tháng chứa phiếu tiêu chí của kỳ (kỳ quý → tháng cuối quý). */
export function thangNeo(thang: number, nam: number): number {
  return tcTheoQuy(thang, nam) ? thangCuoiQuy(quyCuaThang(thang)) : thang;
}

/** Các tháng dùng chung điểm tiêu chí của kỳ. */
export function cacThangApDung(thang: number, nam: number): number[] {
  return tcTheoQuy(thang, nam) ? cacThangTrongQuy(quyCuaThang(thang)) : [thang];
}

/** Nhãn hiển thị: 'Quý 3/2026' hoặc 'Tháng 5/2026'. */
export function nhanKy(thang: number, nam: number): string {
  return tcTheoQuy(thang, nam) ? `Quý ${quyCuaThang(thang)}/${nam}` : `Tháng ${thang}/${nam}`;
}

/** Nhãn ngắn cho bộ chọn: 'Quý 3' hoặc 'Tháng 5'. */
export function nhanKyNgan(thang: number, nam: number): string {
  return tcTheoQuy(thang, nam) ? `Quý ${quyCuaThang(thang)}` : `Tháng ${thang}`;
}

/**
 * Kỳ đã bắt đầu chưa. Kỳ quý neo ở tháng cuối quý nên tháng neo có thể ở tương
 * lai trong khi quý đã bắt đầu (chấm Quý IV từ tháng 10, phiếu neo ở T12).
 */
export function kyDaBatDau(thang: number, nam: number, homNay: Date = new Date()): boolean {
  const namNay = homNay.getFullYear();
  const thangNay = homNay.getMonth() + 1;
  if (tcTheoQuy(thang, nam)) {
    const quy = quyCuaThang(thang);
    return nam < namNay || (nam === namNay && quy <= quyCuaThang(thangNay));
  }
  return nam < namNay || (nam === namNay && thang <= thangNay);
}

/** Kỳ đánh giá, xếp loại THÁNG còn hiệu lực với tháng/năm này không. */
export function kyThangConHieuLuc(thang: number, nam: number): boolean {
  return !tcTheoQuy(thang, nam);
}

export interface TuyChonKy {
  /** Giá trị gửi lên backend — luôn là một số tháng (kỳ quý → tháng neo). */
  thang: number;
  nhan: string;
  laQuy: boolean;
}

/**
 * Danh sách kỳ chọn được trong một năm: tháng cho kỳ cũ, quý cho kỳ mới.
 * Ví dụ 2026 → Tháng 1..6 + Quý 3 + Quý 4; 2027 → Quý 1..4.
 */
export function danhSachKyTrongNam(nam: number): TuyChonKy[] {
  const ds: TuyChonKy[] = [];
  const quyDaThem = new Set<number>();
  for (let thang = 1; thang <= 12; thang++) {
    if (!tcTheoQuy(thang, nam)) {
      ds.push({ thang, nhan: `Tháng ${thang}`, laQuy: false });
      continue;
    }
    const quy = quyCuaThang(thang);
    if (quyDaThem.has(quy)) continue;
    quyDaThem.add(quy);
    ds.push({ thang: thangCuoiQuy(quy), nhan: `Quý ${quy}`, laQuy: true });
  }
  return ds;
}

// =============================================================================
// XEM LẠI KỲ THÁNG (22/09/2026)
// -----------------------------------------------------------------------------
// Trang Đánh giá và trang Tiêu chí chung vẫn cần chọn được các THÁNG đã đánh giá
// xong theo kỳ tháng, kể cả tháng đã nằm trong một quý. Mốc dưới là tháng cuối
// cùng thực sự chấm xong theo tháng: tháng 7/2026 có 517 đơn tiêu chí đã duyệt,
// tháng 8 chỉ chấm dở (322/458) rồi dừng khi chuyển sang kỳ quý.
// =============================================================================

/** Tháng cuối cùng còn hiện thành một mục "Tháng" trong bộ chọn kỳ. */
export const THANG_XEM_LAI_DEN = { nam: 2026, thang: 7 };

/** Tháng này còn được chọn riêng để XEM LẠI số liệu đã chấm theo tháng không? */
export function conXemLaiTheoThang(thang: number, nam: number): boolean {
  return (
    nam < THANG_XEM_LAI_DEN.nam ||
    (nam === THANG_XEM_LAI_DEN.nam && thang <= THANG_XEM_LAI_DEN.thang)
  );
}

/**
 * Tháng đang chọn là SỐ LIỆU LỊCH SỬ: đã thuộc một kỳ quý nhưng vẫn cho xem lại
 * theo tháng. Màn hình phải để chế độ chỉ đọc — mọi thao tác GHI đều bị backend
 * quy về phiếu quý, nếu để form mở thì người dùng tưởng sửa tháng 7 mà thực ra
 * đang ghi đè phiếu Quý III.
 */
export function laThangLichSu(thang: number, nam: number): boolean {
  return tcTheoQuy(thang, nam) && conXemLaiTheoThang(thang, nam);
}

/**
 * Danh sách kỳ cho trang ĐÁNH GIÁ và trang TIÊU CHÍ CHUNG: các tháng còn xem lại
 * được, rồi tới các quý. Năm 2026 ra: Tháng 1…7 · Quý III · Quý IV.
 */
export function danhSachKyXemLai(nam: number): TuyChonKy[] {
  const ds: TuyChonKy[] = [];
  const quyDaThem = new Set<number>();
  for (let thang = 1; thang <= 12; thang++) {
    if (conXemLaiTheoThang(thang, nam)) {
      ds.push({ thang, nhan: `Tháng ${thang}`, laQuy: false });
    }
    if (!tcTheoQuy(thang, nam)) continue;
    const quy = quyCuaThang(thang);
    if (quyDaThem.has(quy)) continue;
    quyDaThem.add(quy);
    ds.push({ thang: thangCuoiQuy(quy), nhan: `Quý ${quy}`, laQuy: true });
  }
  return ds;
}

/**
 * Kỳ mặc định khi mở trang: quý hiện hành nếu năm đó đã chuyển sang kỳ quý,
 * ngược lại là tháng hiện tại (giữ hành vi cũ cho các năm trước).
 */
export function kyMacDinh(nam: number, homNay: Date = new Date()): TuyChonKy {
  const ds = danhSachKyXemLai(nam);
  const thangNay = homNay.getMonth() + 1;
  const thangMoc = nam === homNay.getFullYear() ? thangNay : 12;

  if (tcTheoQuy(thangMoc, nam)) {
    const quy = quyCuaThang(thangMoc);
    const muc = ds.find((k) => k.laQuy && k.thang === thangCuoiQuy(quy));
    if (muc) return muc;
  }
  const mucThang = ds.find((k) => !k.laQuy && k.thang === thangMoc);
  return mucThang ?? ds[ds.length - 1];
}
