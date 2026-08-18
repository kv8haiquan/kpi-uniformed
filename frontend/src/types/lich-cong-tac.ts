/**
 * src/types/lich-cong-tac.ts
 * ==========================
 * Kiểu dữ liệu cho module Lịch công tác (di trú từ lichkv8).
 *
 * Sự kiện trên lịch dùng chung bảng cuộc họp với Họp Không Giấy, phân biệt
 * bằng `nguon`. Sự kiện `nguon='HKG'` mở được sang màn hình chi tiết cuộc họp
 * — cờ `co_the_mo_hkg` do backend tính sẵn.
 */

export type LoaiLich =
  | 'HOP'
  | 'TRUC_BAN'
  | 'HOI_NGHI'
  | 'LAM_VIEC'
  | 'CONG_TAC'
  | 'LICH_KHAC';

export type NguonSuKien = 'HKG' | 'LICH_CONG_TAC';

export type TrangThaiLich =
  | 'LEN_KE_HOACH'
  | 'DA_THONG_BAO'
  | 'DANG_DIEN_RA'
  | 'HOAN_THANH'
  | 'HUY';

/** Nhãn tiếng Việt — giữ đúng cách gọi của lichkv8 để người dùng không phải học lại. */
export const NHAN_LOAI_LICH: Record<LoaiLich, string> = {
  HOP: 'Họp',
  TRUC_BAN: 'Trực ban',
  HOI_NGHI: 'Hội nghị',
  LAM_VIEC: 'Làm việc',
  CONG_TAC: 'Đi công tác',
  LICH_KHAC: 'Lịch khác',
};

export const NHAN_TRANG_THAI: Record<TrangThaiLich, string> = {
  LEN_KE_HOACH: 'Nháp',
  DA_THONG_BAO: 'Đã đăng',
  DANG_DIEN_RA: 'Đang diễn ra',
  HOAN_THANH: 'Hoàn thành',
  HUY: 'Đã hủy',
};

export interface INguoiTomTat {
  id: string;
  ho_ten: string;
  chuc_vu?: string | null;
}

export interface ISuKienLich {
  id: string;
  nguon: NguonSuKien;
  ma_lich?: string | null;
  tieu_de: string;
  loai_lich?: LoaiLich | null;
  loai_lich_nhan?: string | null;

  ngay_hien_thi?: string | null;
  ngay_hop: string;
  ngay_ket_thuc?: string | null;
  gio_bat_dau: string;
  gio_ket_thuc?: string | null;

  dia_diem?: string | null;
  trang_thai: TrangThaiLich;

  /** Khớp được công chức thì có chu_toa; không thì đọc chu_tri_text. */
  chu_toa?: INguoiTomTat | null;
  chu_tri_text?: string | null;

  don_vi_chuan_bi?: string | null;
  so_van_ban?: string | null;
  lanh_dao_lien_quan: INguoiTomTat[];
  so_tai_lieu: number;

  /** Bấm vào mở được sang chi tiết cuộc họp trong Họp Không Giấy. */
  co_the_mo_hkg: boolean;
}

export interface ISuKienChiTiet extends ISuKienLich {
  mo_ta?: string | null;
  thanh_phan_text?: string | null;
  ly_do_huy?: string | null;
}

export interface ILichThang {
  nam: number;
  thang: number;
  tong: number;
  /** Khóa là ngày dạng YYYY-MM-DD; sự kiện nhiều ngày lặp ở mọi ngày nó kéo dài. */
  theo_ngay: Record<string, ISuKienLich[]>;
}

export interface ITomTatNgay {
  ngay: string;
  thu: string;
  su_kien: ISuKienLich[];
  truc_ban: string[];
}

export interface ITomTatLich {
  tu_ngay: string;
  den_ngay: string;
  theo_ngay: ITomTatNgay[];
  /** Bản text sẵn để dán sang Zalo hoặc email. */
  van_ban_thuan: string;
}

export interface ILichLanhDaoNgay {
  ngay: string;
  su_kien: ISuKienLich[];
}

export interface ILichLanhDao {
  lanh_dao: INguoiTomTat;
  tong_su_kien: number;
  theo_ngay: ILichLanhDaoNgay[];
}

export interface IThongKeLich {
  hom_nay: number;
  ngay_mai: number;
  trong_tuan: number;
  trong_thang: number;
  trong_nam: number;
  theo_loai_thang_nay: Record<string, number>;
}

export interface IDanhMucLoai {
  ma: LoaiLich;
  ten: string;
}
