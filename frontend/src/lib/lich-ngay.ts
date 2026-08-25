/**
 * src/lib/lich-ngay.ts
 * ====================
 * Phép tính ngày dùng chung cho các chế độ xem của Lịch công tác (tháng, tuần,
 * ngày).
 *
 * Mọi ngày ở đây là chuỗi `YYYY-MM-DD` chứ không phải `Date`. Lý do: backend
 * trả về đúng dạng đó, và so sánh chuỗi `YYYY-MM-DD` cho ra thứ tự thời gian
 * chuẩn — không phải dựng `Date` nên không dính lệch múi giờ khi trình duyệt
 * của người dùng đặt lệch UTC+7.
 *
 * Khi buộc phải cộng/trừ ngày thì tính bằng mốc UTC, vì cộng ngày trên giờ địa
 * phương sẽ nhảy sai vào ngày đổi giờ mùa ở một số máy đặt sai vùng.
 */

/** Đổi `Date` (giờ địa phương) sang khoá ngày `YYYY-MM-DD`. */
export function khoaNgay(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
    d.getDate(),
  ).padStart(2, '0')}`;
}

/** Khoá ngày của hôm nay theo giờ máy người dùng. */
export function homNayKhoa(): string {
  return khoaNgay(new Date());
}

/** Cộng (hoặc trừ, khi `so` âm) số ngày vào một khoá ngày. */
export function themNgay(khoa: string, so: number): string {
  const d = new Date(`${khoa}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + so);
  return d.toISOString().slice(0, 10);
}

/** 0 = thứ Hai … 6 = Chủ nhật — lịch Việt Nam, khác mặc định của `Date`. */
export function thuTrongTuan(khoa: string): number {
  return (new Date(`${khoa}T00:00:00Z`).getUTCDay() + 6) % 7;
}

/** Thứ Hai của tuần chứa `khoa`. */
export function dauTuan(khoa: string): string {
  return themNgay(khoa, -thuTrongTuan(khoa));
}

/** Bảy khoá ngày của tuần chứa `khoa`, từ thứ Hai tới Chủ nhật. */
export function tuanCua(khoa: string): string[] {
  const bd = dauTuan(khoa);
  return Array.from({ length: 7 }, (_, i) => themNgay(bd, i));
}

const TEN_THU = [
  'Thứ Hai',
  'Thứ Ba',
  'Thứ Tư',
  'Thứ Năm',
  'Thứ Sáu',
  'Thứ Bảy',
  'Chủ nhật',
];

const TEN_THU_NGAN = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];

export function nhanThu(khoa: string): string {
  return TEN_THU[thuTrongTuan(khoa)];
}

export function nhanThuNgan(khoa: string): string {
  return TEN_THU_NGAN[thuTrongTuan(khoa)];
}

/** `2026-08-25` → `25/08/2026`. */
export function ngayVN(khoa: string): string {
  const [n, t, ng] = khoa.split('-');
  return `${ng}/${t}/${n}`;
}

/** `2026-08-25` → `25/08`. */
export function ngayThangVN(khoa: string): string {
  const [, t, ng] = khoa.split('-');
  return `${ng}/${t}`;
}

/** `08:30:00` → `08:30`; rỗng/null → chuỗi rỗng. */
export function gioNgan(gio?: string | null): string {
  return gio ? gio.slice(0, 5) : '';
}

/**
 * Hình dạng tối thiểu để gom theo ngày — cố ý KHÔNG dùng `ISuKienLich` để hàm
 * này còn test được mà không phải dựng cả một sự kiện đầy đủ.
 */
export interface ISuKienCoNgay {
  ngay_hop: string;
  ngay_hien_thi?: string | null;
  ngay_ket_thuc?: string | null;
  gio_bat_dau?: string | null;
}

/**
 * Gom sự kiện theo từng ngày trong khoảng `[tu, den]`, giống hệt cách endpoint
 * lịch tháng gom phía máy chủ: sự kiện nhiều ngày xuất hiện ở MỌI ngày nó kéo
 * dài, và bị cắt về đúng khoảng đang xem.
 *
 * Trong mỗi ngày, sự kiện xếp theo giờ bắt đầu; sự kiện không ghi giờ xuống
 * cuối vì không biết nó chen vào đâu.
 */
export function nhomTheoNgay<T extends ISuKienCoNgay>(
  ds: T[],
  tu: string,
  den: string,
): Record<string, T[]> {
  const kq: Record<string, T[]> = {};
  for (const sk of ds) {
    const bd = sk.ngay_hien_thi || sk.ngay_hop;
    if (!bd) continue;
    // Dữ liệu di trú từ lichkv8 có vài bản ghi ngày kết thúc trước ngày bắt
    // đầu — coi như sự kiện một ngày, đừng để vòng lặp chạy lùi thành rỗng.
    const kt = sk.ngay_ket_thuc && sk.ngay_ket_thuc > bd ? sk.ngay_ket_thuc : bd;
    let n = bd > tu ? bd : tu;
    const cuoi = kt < den ? kt : den;
    while (n <= cuoi) {
      (kq[n] ??= []).push(sk);
      n = themNgay(n, 1);
    }
  }
  for (const n of Object.keys(kq)) {
    kq[n].sort((a, b) =>
      (a.gio_bat_dau || '99:99').localeCompare(b.gio_bat_dau || '99:99'),
    );
  }
  return kq;
}
