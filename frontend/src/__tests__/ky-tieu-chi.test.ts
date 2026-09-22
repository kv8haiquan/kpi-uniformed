/**
 * src/__tests__/ky-tieu-chi.test.ts
 * =================================
 * Logic kỳ dùng chung cho bộ chọn ở trang Đánh giá và trang Tiêu chí chung
 * (Công văn 21169 + quyết định người dùng 22/09/2026).
 */

import { describe, expect, it } from 'vitest';

import {
  THANG_XEM_LAI_DEN,
  conXemLaiTheoThang,
  danhSachKyXemLai,
  kyMacDinh,
  laThangLichSu,
  nhanKy,
  quyCuaThang,
  tcTheoQuy,
  thangCuoiQuy,
  thangNeo,
} from '@/lib/ky-tieu-chi';

describe('danh sách kỳ trong bộ chọn', () => {
  it('2026 ra Tháng 1–7 rồi Quý III, Quý IV', () => {
    const ds = danhSachKyXemLai(2026);
    expect(ds.map((k) => k.nhan)).toEqual([
      'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6', 'Tháng 7',
      'Quý 3', 'Quý 4',
    ]);
    // Quý III mang giá trị tháng neo (9) — khác hẳn Tháng 7
    expect(ds.find((k) => k.nhan === 'Quý 3')?.thang).toBe(9);
    expect(ds.find((k) => k.nhan === 'Tháng 7')?.thang).toBe(7);
  });

  it('2025 toàn tháng, 2027 toàn quý', () => {
    expect(danhSachKyXemLai(2025)).toHaveLength(12);
    expect(danhSachKyXemLai(2025).every((k) => !k.laQuy)).toBe(true);

    const ds2027 = danhSachKyXemLai(2027);
    expect(ds2027.map((k) => k.nhan)).toEqual(['Quý 1', 'Quý 2', 'Quý 3', 'Quý 4']);
  });

  it('mỗi mục có một giá trị riêng — không hai mục trùng số tháng', () => {
    // Bất biến quan trọng: các trang lưu lựa chọn bằng MỘT số tháng, nên hai mục
    // trùng số sẽ khiến chọn "Tháng X" lại nhảy sang "Quý Y". Chỉ đúng khi mốc
    // THANG_XEM_LAI_DEN không rơi vào tháng cuối quý (3, 6, 9, 12).
    expect([3, 6, 9, 12]).not.toContain(THANG_XEM_LAI_DEN.thang);
    for (const nam of [2025, 2026, 2027]) {
      const values = danhSachKyXemLai(nam).map((k) => k.thang);
      expect(new Set(values).size).toBe(values.length);
    }
  });
});

describe('kỳ mặc định khi mở trang', () => {
  it('trong quý III/2026 thì mặc định là Quý 3', () => {
    const muc = kyMacDinh(2026, new Date(2026, 8, 22)); // 22/09/2026
    expect(muc.laQuy).toBe(true);
    expect(muc.thang).toBe(9);
    expect(nhanKy(muc.thang, 2026)).toBe('Quý 3/2026');
  });

  it('sang tháng 10 thì tự nhảy sang Quý 4', () => {
    expect(kyMacDinh(2026, new Date(2026, 9, 5)).thang).toBe(12);
  });

  it('năm cũ (2025) vẫn mặc định theo tháng', () => {
    const muc = kyMacDinh(2025, new Date(2026, 8, 22));
    expect(muc.laQuy).toBe(false);
    expect(muc.thang).toBe(12);
  });

  it('kỳ mặc định luôn nằm trong danh sách chọn được', () => {
    for (const nam of [2025, 2026, 2027]) {
      const ds = danhSachKyXemLai(nam);
      const muc = kyMacDinh(nam, new Date(2026, 8, 22));
      expect(ds.some((k) => k.thang === muc.thang && k.laQuy === muc.laQuy)).toBe(true);
    }
  });
});

describe('tháng lịch sử — màn hình phải khoá form', () => {
  it('tháng 7/2026 là số liệu lịch sử', () => {
    expect(laThangLichSu(7, 2026)).toBe(true);
    expect(tcTheoQuy(7, 2026)).toBe(true);
    expect(conXemLaiTheoThang(7, 2026)).toBe(true);
  });

  it('tháng 1–6/2026 là kỳ tháng thật, không phải lịch sử', () => {
    for (const thang of [1, 2, 3, 4, 5, 6]) {
      expect(laThangLichSu(thang, 2026)).toBe(false);
    }
  });

  it('giá trị của một quý (tháng neo) không bị coi là tháng lịch sử', () => {
    expect(laThangLichSu(9, 2026)).toBe(false);  // "Quý 3"
    expect(laThangLichSu(12, 2026)).toBe(false); // "Quý 4"
  });

  it('tháng neo và quý khớp nhau', () => {
    expect(thangNeo(7, 2026)).toBe(9);
    expect(thangCuoiQuy(quyCuaThang(7))).toBe(9);
  });
});
