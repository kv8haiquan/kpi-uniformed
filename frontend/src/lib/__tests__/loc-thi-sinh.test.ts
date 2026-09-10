/**
 * src/lib/__tests__/loc-thi-sinh.test.ts
 * ======================================
 * Test bộ lọc thí sinh kỳ thi ĐGNL.
 */

import { describe, it, expect } from 'vitest';
import {
  BO_LOC_RONG,
  boDau,
  coDangLoc,
  danhSachDonVi,
  danhSachViTri,
  locThiSinh,
  moTaLoc,
  slug,
  type BoLocThiSinh,
} from '../loc-thi-sinh';
import type { IThiSinh } from '@/types/lms';

/** Dựng 1 thí sinh với các trường cần cho phép lọc, phần còn lại để mặc định. */
function ts(p: Partial<IThiSinh> & { id: string }): IThiSinh {
  return {
    ky_thi_id: 'ky-thi-1',
    cong_chuc_id: `cc-${p.id}`,
    vi_tri_id: 'vt-1',
    trang_thai: 'CHUA_THI',
    lan_thi_hien_tai: 0,
    diem_tong: null,
    xep_loai: null,
    so_cau_dung: null,
    so_cau_sai: null,
    tong_so_cau: null,
    so_lan_vi_pham: 0,
    diem_theo_linh_vuc: null,
    thoi_gian_bat_dau: null,
    thoi_gian_nop: null,
    thoi_gian_lam_giay: null,
    ho_ten: 'Người Không Tên',
    ma_cc: '20ZZ-9999',
    don_vi_ten: 'Đội Nghiệp vụ 1',
    vi_tri_ten: 'Công chức',
    lich_su_thi: [],
    ...p,
  } as IThiSinh;
}

/** Kỳ thi tối đa 2 lượt — giống ĐGNL-THANG 8 - TA. */
const SO_LAN_TOI_DA = 2;

const CHUNG = ts({
  id: 'chung',
  ma_cc: '20ZZ-0005',
  ho_ten: 'Võ Hồng Chung',
  don_vi_ten: 'Phòng Tổ chức cán bộ',
  vi_tri_ten: 'Chuyên viên',
  // Vừa được reset: về CHUA_THI, lượt 0, không còn điểm
  trang_thai: 'CHUA_THI',
  lan_thi_hien_tai: 0,
});

const DAT_HET_LUOT = ts({
  id: 'dat',
  ma_cc: '20ZZ-0100',
  ho_ten: 'Trần Đức Lợi',
  trang_thai: 'DA_NOP',
  lan_thi_hien_tai: 2,
  diem_tong: 88,
  xep_loai: 'DAT',
});

const TRUOT_CON_LUOT = ts({
  id: 'truot',
  ma_cc: '20ZZ-0200',
  ho_ten: 'Lê Thị Hoa',
  don_vi_ten: 'Phòng Tổ chức cán bộ',
  trang_thai: 'DA_NOP',
  lan_thi_hien_tai: 1,
  diem_tong: 40,
  xep_loai: 'KHONG_DAT',
  so_lan_vi_pham: 3,
});

const DANG_THI = ts({
  id: 'dangthi',
  ma_cc: '20ZZ-0300',
  ho_ten: 'Phạm Văn Đông',
  vi_tri_ten: 'Kiểm tra viên',
  trang_thai: 'DANG_THI',
  lan_thi_hien_tai: 1,
});

const DS = [CHUNG, DAT_HET_LUOT, TRUOT_CON_LUOT, DANG_THI];

/** Bộ lọc rỗng + vài trường ghi đè. */
function loc(patch: Partial<BoLocThiSinh> = {}): BoLocThiSinh {
  return { ...BO_LOC_RONG, ...patch };
}

const ids = (ds: IThiSinh[]) => ds.map((x) => x.id).sort();

describe('boDau', () => {
  it('bỏ dấu thanh và đ/Đ, đưa về chữ thường', () => {
    expect(boDau('Võ Hồng Chung')).toBe('vo hong chung');
    expect(boDau('Trần Đức Lợi')).toBe('tran duc loi');
    expect(boDau('20ZZ-0005')).toBe('20zz-0005');
  });
});

describe('locThiSinh — không lọc', () => {
  it('bộ lọc rỗng trả nguyên danh sách', () => {
    expect(locThiSinh(DS, BO_LOC_RONG, SO_LAN_TOI_DA)).toHaveLength(DS.length);
    expect(coDangLoc(BO_LOC_RONG)).toBe(false);
  });
});

describe('locThiSinh — trạng thái', () => {
  it('CHUA_THI bắt cả người vừa được reset', () => {
    const kq = locThiSinh(DS, loc({ trangThai: 'CHUA_THI' }), SO_LAN_TOI_DA);
    expect(ids(kq)).toEqual(['chung']);
    expect(kq[0].lan_thi_hien_tai).toBe(0);
    expect(kq[0].diem_tong).toBeNull();
  });

  it('DA_NOP chỉ lấy người đã nộp', () => {
    expect(ids(locThiSinh(DS, loc({ trangThai: 'DA_NOP' }), SO_LAN_TOI_DA))).toEqual(['dat', 'truot']);
  });

  it('DANG_THI tách riêng khỏi CHUA_THI', () => {
    expect(ids(locThiSinh(DS, loc({ trangThai: 'DANG_THI' }), SO_LAN_TOI_DA))).toEqual(['dangthi']);
  });
});

describe('locThiSinh — tìm theo mã CC / họ tên', () => {
  it('gõ không dấu vẫn ra đúng người', () => {
    expect(ids(locThiSinh(DS, loc({ tuKhoa: 'chung' }), SO_LAN_TOI_DA))).toEqual(['chung']);
    expect(ids(locThiSinh(DS, loc({ tuKhoa: 'duc loi' }), SO_LAN_TOI_DA))).toEqual(['dat']);
  });

  it('gõ mã công chức, không phân biệt hoa thường', () => {
    expect(ids(locThiSinh(DS, loc({ tuKhoa: '20zz-0005' }), SO_LAN_TOI_DA))).toEqual(['chung']);
    expect(ids(locThiSinh(DS, loc({ tuKhoa: '0300' }), SO_LAN_TOI_DA))).toEqual(['dangthi']);
  });

  it('khoảng trắng thừa không ảnh hưởng, không khớp thì trả rỗng', () => {
    expect(locThiSinh(DS, loc({ tuKhoa: '   ' }), SO_LAN_TOI_DA)).toHaveLength(DS.length);
    expect(locThiSinh(DS, loc({ tuKhoa: 'khong-co-ai' }), SO_LAN_TOI_DA)).toHaveLength(0);
  });
});

describe('locThiSinh — đơn vị và vị trí', () => {
  it('lọc theo đơn vị', () => {
    expect(ids(locThiSinh(DS, loc({ donVi: 'Phòng Tổ chức cán bộ' }), SO_LAN_TOI_DA))).toEqual(['chung', 'truot']);
  });

  it('lọc theo vị trí việc làm', () => {
    expect(ids(locThiSinh(DS, loc({ viTri: 'Kiểm tra viên' }), SO_LAN_TOI_DA))).toEqual(['dangthi']);
  });

  it('danh sách đơn vị / vị trí là unique và đã sắp xếp', () => {
    expect(danhSachDonVi(DS)).toEqual(['Đội Nghiệp vụ 1', 'Phòng Tổ chức cán bộ']);
    expect(danhSachViTri(DS)).toEqual(['Chuyên viên', 'Công chức', 'Kiểm tra viên']);
  });

  it('bỏ qua đơn vị rỗng/null khi dựng dropdown', () => {
    const co = danhSachDonVi([...DS, ts({ id: 'trong', don_vi_ten: null }), ts({ id: 'trong2', don_vi_ten: '  ' })]);
    expect(co).toEqual(['Đội Nghiệp vụ 1', 'Phòng Tổ chức cán bộ']);
  });
});

describe('locThiSinh — còn lượt / hết lượt', () => {
  it('hết lượt = đã dùng đủ số lượt tối đa của kỳ', () => {
    expect(ids(locThiSinh(DS, loc({ luot: 'het' }), SO_LAN_TOI_DA))).toEqual(['dat']);
  });

  it('còn lượt là phần bù của hết lượt', () => {
    expect(ids(locThiSinh(DS, loc({ luot: 'con' }), SO_LAN_TOI_DA))).toEqual(['chung', 'dangthi', 'truot']);
  });

  it('chưa biết cấu hình kỳ (0 lượt) thì không ai bị coi là hết lượt', () => {
    expect(locThiSinh(DS, loc({ luot: 'het' }), 0)).toHaveLength(0);
    expect(locThiSinh(DS, loc({ luot: 'con' }), 0)).toHaveLength(DS.length);
  });
});

describe('locThiSinh — xếp loại và vi phạm', () => {
  it('KHONG_DAT không dính người chưa thi', () => {
    const kq = locThiSinh(DS, loc({ xepLoai: 'KHONG_DAT' }), SO_LAN_TOI_DA);
    expect(ids(kq)).toEqual(['truot']);
    expect(kq.every((x) => x.trang_thai === 'DA_NOP')).toBe(true);
  });

  it('DAT chỉ lấy người đạt', () => {
    expect(ids(locThiSinh(DS, loc({ xepLoai: 'DAT' }), SO_LAN_TOI_DA))).toEqual(['dat']);
  });

  it('chỉ người có vi phạm', () => {
    expect(ids(locThiSinh(DS, loc({ chiViPham: true }), SO_LAN_TOI_DA))).toEqual(['truot']);
  });
});

describe('locThiSinh — kết hợp nhiều điều kiện', () => {
  it('chưa thi + đơn vị giao nhau đúng', () => {
    expect(ids(locThiSinh(DS, loc({ trangThai: 'CHUA_THI', donVi: 'Phòng Tổ chức cán bộ' }), SO_LAN_TOI_DA)))
      .toEqual(['chung']);
  });

  it('điều kiện chỏi nhau thì trả rỗng', () => {
    expect(locThiSinh(DS, loc({ trangThai: 'CHUA_THI', xepLoai: 'DAT' }), SO_LAN_TOI_DA)).toHaveLength(0);
    expect(locThiSinh(DS, loc({ trangThai: 'CHUA_THI', donVi: 'Đội Nghiệp vụ 1' }), SO_LAN_TOI_DA)).toHaveLength(0);
  });
});

describe('coDangLoc', () => {
  it('nhận ra từng loại điều kiện', () => {
    expect(coDangLoc(loc({ tuKhoa: 'a' }))).toBe(true);
    expect(coDangLoc(loc({ tuKhoa: '   ' }))).toBe(false);
    expect(coDangLoc(loc({ trangThai: 'CHUA_THI' }))).toBe(true);
    expect(coDangLoc(loc({ donVi: 'X' }))).toBe(true);
    expect(coDangLoc(loc({ viTri: 'X' }))).toBe(true);
    expect(coDangLoc(loc({ luot: 'het' }))).toBe(true);
    expect(coDangLoc(loc({ xepLoai: 'DAT' }))).toBe(true);
    expect(coDangLoc(loc({ chiViPham: true }))).toBe(true);
  });
});

describe('moTaLoc / slug — hậu tố tên file Excel', () => {
  it('không lọc gì -> tat-ca', () => {
    expect(moTaLoc(BO_LOC_RONG)).toBe('tat-ca');
  });

  it('ghép các điều kiện đang bật', () => {
    expect(moTaLoc(loc({ trangThai: 'CHUA_THI' }))).toBe('chua-thi');
    expect(moTaLoc(loc({ trangThai: 'CHUA_THI', donVi: 'Phòng Tổ chức cán bộ' })))
      .toBe('chua-thi_phong-to-chuc-can-bo');
    expect(moTaLoc(loc({ xepLoai: 'KHONG_DAT', chiViPham: true }))).toBe('khong-dat_co-vi-pham');
    expect(moTaLoc(loc({ luot: 'het' }))).toBe('het-luot');
  });

  it('slug bỏ dấu, thay ký tự lạ, cắt ngắn', () => {
    expect(slug('ĐGNL-THANG 8 - TA')).toBe('dgnl-thang-8-ta');
    expect(slug('  ')).toBe('');
    expect(slug('a'.repeat(60))).toHaveLength(40);
  });
});
