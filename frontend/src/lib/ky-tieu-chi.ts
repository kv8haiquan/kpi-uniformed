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
