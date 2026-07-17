// Types cho ĐỐI SOÁT HOÀN THÀNH ĐÁNH GIÁ THÁNG (TCCB tự phục vụ).

export interface IDoiSoatItem {
  cong_chuc_id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string | null;
  vai_tro: string | null;
  don_vi_id: string | null;
  don_vi_ten: string | null;
  chi_tiet: string;
  nguoi_xu_ly: string | null;
}

export type MucDo = 'cao' | 'trung_binh' | 'thap';

export interface IDoiSoatNhomMeta {
  key: string;
  ten: string;
  mo_ta: string;
  muc_do: MucDo;
  nguoi_xu_ly: string;
}

export interface IDoiSoatData {
  thang: number;
  nam: number;
  meta: IDoiSoatNhomMeta[];
  nhom: Record<string, IDoiSoatItem[]>;
  tong_hop: Record<string, number>;
  tong_so_ca: number;
}
