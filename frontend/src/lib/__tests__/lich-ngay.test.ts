/**
 * Kiểm thử phép tính ngày của Lịch công tác.
 *
 * Trọng tâm là hai chỗ dễ sai: mốc đầu tuần theo lịch Việt Nam (thứ Hai) và
 * việc trải sự kiện nhiều ngày ra từng ngày trong khoảng đang xem.
 */

import { describe, expect, it } from 'vitest';

import {
  dauTuan,
  gioNgan,
  nhanThu,
  ngayVN,
  nhomTheoNgay,
  themNgay,
  thuTrongTuan,
  tuanCua,
} from '../lich-ngay';

describe('mốc tuần theo lịch Việt Nam', () => {
  it('thứ Hai là ngày đầu tuần, Chủ nhật là ngày cuối', () => {
    // 24/08/2026 là thứ Hai, 30/08/2026 là Chủ nhật.
    expect(thuTrongTuan('2026-08-24')).toBe(0);
    expect(thuTrongTuan('2026-08-30')).toBe(6);
    expect(nhanThu('2026-08-24')).toBe('Thứ Hai');
    expect(nhanThu('2026-08-30')).toBe('Chủ nhật');
  });

  it('Chủ nhật vẫn thuộc tuần bắt đầu từ thứ Hai trước đó', () => {
    expect(dauTuan('2026-08-30')).toBe('2026-08-24');
    expect(dauTuan('2026-08-24')).toBe('2026-08-24');
  });

  it('tuanCua trả đủ 7 ngày liên tiếp', () => {
    expect(tuanCua('2026-08-27')).toEqual([
      '2026-08-24',
      '2026-08-25',
      '2026-08-26',
      '2026-08-27',
      '2026-08-28',
      '2026-08-29',
      '2026-08-30',
    ]);
  });

  it('cộng ngày vượt qua mốc tháng và năm', () => {
    expect(themNgay('2026-08-31', 1)).toBe('2026-09-01');
    expect(themNgay('2026-01-01', -1)).toBe('2025-12-31');
    expect(themNgay('2028-02-28', 1)).toBe('2028-02-29'); // năm nhuận
  });
});

describe('nhomTheoNgay', () => {
  const sk = (
    id: string,
    ngay: string,
    ket_thuc?: string,
    gio?: string,
  ) => ({
    id,
    ngay_hop: ngay,
    ngay_hien_thi: ngay,
    ngay_ket_thuc: ket_thuc ?? null,
    gio_bat_dau: gio ?? '08:00:00',
  });

  it('sự kiện một ngày rơi đúng vào ngày của nó', () => {
    const kq = nhomTheoNgay([sk('a', '2026-08-25')], '2026-08-24', '2026-08-30');
    expect(Object.keys(kq)).toEqual(['2026-08-25']);
    expect(kq['2026-08-25'][0].id).toBe('a');
  });

  it('sự kiện nhiều ngày lặp ở mọi ngày nó kéo dài', () => {
    const kq = nhomTheoNgay(
      [sk('a', '2026-08-25', '2026-08-27')],
      '2026-08-24',
      '2026-08-30',
    );
    expect(Object.keys(kq).sort()).toEqual([
      '2026-08-25',
      '2026-08-26',
      '2026-08-27',
    ]);
  });

  it('cắt sự kiện dài về đúng khoảng đang xem', () => {
    const kq = nhomTheoNgay(
      [sk('a', '2026-08-20', '2026-09-05')],
      '2026-08-24',
      '2026-08-26',
    );
    expect(Object.keys(kq).sort()).toEqual([
      '2026-08-24',
      '2026-08-25',
      '2026-08-26',
    ]);
  });

  it('ngày kết thúc trước ngày bắt đầu vẫn hiện một ngày, không mất tích', () => {
    const kq = nhomTheoNgay(
      [sk('a', '2026-08-25', '2026-08-20')],
      '2026-08-24',
      '2026-08-30',
    );
    expect(Object.keys(kq)).toEqual(['2026-08-25']);
  });

  it('trong ngày xếp theo giờ, sự kiện không ghi giờ xuống cuối', () => {
    const kq = nhomTheoNgay(
      [
        sk('chieu', '2026-08-25', undefined, '14:00:00'),
        { ...sk('khong-gio', '2026-08-25'), gio_bat_dau: null },
        sk('sang', '2026-08-25', undefined, '08:30:00'),
      ],
      '2026-08-25',
      '2026-08-25',
    );
    expect(kq['2026-08-25'].map((x) => x.id)).toEqual([
      'sang',
      'chieu',
      'khong-gio',
    ]);
  });

  it('ưu tiên ngay_hien_thi, lùi về ngay_hop khi thiếu', () => {
    const kq = nhomTheoNgay(
      [
        {
          id: 'a',
          ngay_hop: '2026-08-25',
          ngay_hien_thi: null,
          ngay_ket_thuc: null,
          gio_bat_dau: '08:00:00',
        },
      ],
      '2026-08-24',
      '2026-08-30',
    );
    expect(Object.keys(kq)).toEqual(['2026-08-25']);
  });
});

describe('định dạng hiển thị', () => {
  it('ngày kiểu Việt Nam và giờ rút gọn', () => {
    expect(ngayVN('2026-08-05')).toBe('05/08/2026');
    expect(gioNgan('08:30:00')).toBe('08:30');
    expect(gioNgan(null)).toBe('');
  });
});
