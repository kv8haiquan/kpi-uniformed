/**
 * src/lib/loc-thi-sinh.ts
 * =======================
 * Lọc danh sách thí sinh kỳ thi ĐGNL — logic thuần, không JSX, để test được.
 *
 * Trang thống kê kỳ thi tải sẵn TOÀN BỘ thí sinh (kyThiApi.danhSachThiSinhTatCa)
 * nên mọi phép lọc chạy ngay ở trình duyệt: không thêm request, không đụng backend.
 */

import type { IThiSinh } from '@/types/lms';

export type LocTrangThai = 'all' | 'CHUA_THI' | 'DANG_THI' | 'DA_NOP' | 'VANG';
export type LocLuot = 'all' | 'con' | 'het';
export type LocXepLoai = 'all' | 'DAT' | 'KHONG_DAT';

export interface BoLocThiSinh {
  /** Mã công chức hoặc họ tên — so khớp sau khi bỏ dấu. */
  tuKhoa: string;
  trangThai: LocTrangThai;
  /** Tên đơn vị đúng như hiển thị; '' = tất cả. */
  donVi: string;
  /** Tên vị trí việc làm; '' = tất cả. */
  viTri: string;
  luot: LocLuot;
  xepLoai: LocXepLoai;
  chiViPham: boolean;
}

export const BO_LOC_RONG: BoLocThiSinh = {
  tuKhoa: '',
  trangThai: 'all',
  donVi: '',
  viTri: '',
  luot: 'all',
  xepLoai: 'all',
  chiViPham: false,
};

/** Bỏ dấu để gõ "chung" cũng tìm ra "Chung", "Chúng". */
export function boDau(s: string): string {
  return s
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .toLowerCase();
}

/** Có đang lọc gì không — dùng để ẩn/hiện nút "Xoá lọc" và đổi tiêu đề bảng. */
export function coDangLoc(bl: BoLocThiSinh): boolean {
  return (
    bl.tuKhoa.trim() !== '' ||
    bl.trangThai !== 'all' ||
    bl.donVi !== '' ||
    bl.viTri !== '' ||
    bl.luot !== 'all' ||
    bl.xepLoai !== 'all' ||
    bl.chiViPham
  );
}

/**
 * Lọc danh sách thí sinh. Các điều kiện GIAO nhau (AND).
 *
 * Quy ước cần nhớ:
 * - "Chưa thi" = trang_thai CHUA_THI. Người vừa được RESET cũng rơi vào nhóm này —
 *   đúng nghĩa "chưa có kết quả", không tách riêng.
 * - "Hết lượt" = lan_thi_hien_tai >= soLanToiDa của kỳ. Đây là nhóm muốn thi lại thì
 *   phải reset, nên lọc ra được là đi thẳng tới nút Reset.
 * - Xếp loại chỉ xét người ĐÃ NỘP: ai chưa thi không lọt vào cả DAT lẫn KHONG_DAT.
 */
export function locThiSinh(
  ds: IThiSinh[],
  bl: BoLocThiSinh,
  soLanToiDa: number,
): IThiSinh[] {
  const tu = boDau(bl.tuKhoa.trim());

  return ds.filter((ts) => {
    if (tu !== '') {
      const dich = `${boDau(ts.ma_cc || '')} ${boDau(ts.ho_ten || '')}`;
      if (!dich.includes(tu)) return false;
    }

    if (bl.trangThai !== 'all' && ts.trang_thai !== bl.trangThai) return false;
    if (bl.donVi !== '' && (ts.don_vi_ten || '') !== bl.donVi) return false;
    if (bl.viTri !== '' && (ts.vi_tri_ten || '') !== bl.viTri) return false;

    if (bl.luot !== 'all') {
      // soLanToiDa <= 0 nghĩa là chưa biết cấu hình kỳ -> coi như không ai hết lượt,
      // thà hiện thừa còn hơn giấu mất người cần xử lý.
      const hetLuot = soLanToiDa > 0 && (ts.lan_thi_hien_tai || 0) >= soLanToiDa;
      if (bl.luot === 'het' && !hetLuot) return false;
      if (bl.luot === 'con' && hetLuot) return false;
    }

    if (bl.xepLoai !== 'all') {
      if (ts.trang_thai !== 'DA_NOP') return false;
      if (ts.xep_loai !== bl.xepLoai) return false;
    }

    if (bl.chiViPham && (ts.so_lan_vi_pham ?? 0) <= 0) return false;

    return true;
  });
}

/** Danh sách đơn vị có mặt trong kỳ — unique, sắp xếp tiếng Việt, để dựng dropdown. */
export function danhSachDonVi(ds: IThiSinh[]): string[] {
  return uniqueSapXep(ds.map((ts) => ts.don_vi_ten));
}

/** Danh sách vị trí việc làm có mặt trong kỳ. */
export function danhSachViTri(ds: IThiSinh[]): string[] {
  return uniqueSapXep(ds.map((ts) => ts.vi_tri_ten));
}

function uniqueSapXep(ten: (string | null | undefined)[]): string[] {
  const tap = new Set<string>();
  for (const t of ten) {
    if (t && t.trim() !== '') tap.add(t);
  }
  return Array.from(tap).sort((a, b) => a.localeCompare(b, 'vi'));
}

/**
 * Mô tả bộ lọc thành một mẩu chuỗi để gắn vào tên file Excel.
 * Ví dụ: 'chua-thi_doi-nghiep-vu-1'. Không lọc gì -> 'tat-ca'.
 */
export function moTaLoc(bl: BoLocThiSinh): string {
  const phan: string[] = [];

  const nhanTrangThai: Record<Exclude<LocTrangThai, 'all'>, string> = {
    CHUA_THI: 'chua-thi',
    DANG_THI: 'dang-thi',
    DA_NOP: 'da-nop',
    VANG: 'vang',
  };
  if (bl.trangThai !== 'all') phan.push(nhanTrangThai[bl.trangThai]);
  if (bl.xepLoai !== 'all') phan.push(bl.xepLoai === 'DAT' ? 'dat' : 'khong-dat');
  if (bl.luot !== 'all') phan.push(bl.luot === 'het' ? 'het-luot' : 'con-luot');
  if (bl.chiViPham) phan.push('co-vi-pham');
  if (bl.donVi !== '') phan.push(slug(bl.donVi));
  if (bl.viTri !== '') phan.push(slug(bl.viTri));
  if (bl.tuKhoa.trim() !== '') phan.push(slug(bl.tuKhoa));

  return phan.length > 0 ? phan.join('_') : 'tat-ca';
}

/** Chuỗi tiếng Việt -> mẩu an toàn cho tên file. */
export function slug(s: string): string {
  return boDau(s)
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 40);
}
