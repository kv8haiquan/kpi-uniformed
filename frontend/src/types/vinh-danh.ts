/**
 * src/types/vinh-danh.ts
 * =======================
 * Types cho module Vinh danh (cong chuc tieu bieu thang).
 * Tuong ung backend portal_service/schemas/vinh_danh_thang.py
 */

export type TrangThaiVinhDanh = 'DRAFT' | 'PUBLISHED';

export interface ICongChucBrief {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu?: string | null;
}

export interface IVinhDanhThang {
  id: string;
  thang: number;
  nam: number;
  tieu_de: string;
  ly_do: string;
  anh_chan_dung?: string | null;
  /** Vị trí ảnh trong khung tròn (CSS object-position), vd "50% 30%" */
  anh_vi_tri?: string | null;
  loi_tuyen_duong?: string | null;
  trang_thai: TrangThaiVinhDanh;
  ngay_cong_bo?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  cong_chuc?: ICongChucBrief | null;
  nguoi_tao?: ICongChucBrief | null;
}

export interface IVinhDanhThangCreate {
  thang: number;
  nam: number;
  cong_chuc_id: string;
  tieu_de: string;
  ly_do: string;
  anh_chan_dung?: string | null;
  anh_vi_tri?: string | null;
  loi_tuyen_duong?: string | null;
}

export interface IVinhDanhThangUpdate {
  thang?: number;
  nam?: number;
  cong_chuc_id?: string;
  tieu_de?: string;
  ly_do?: string;
  anh_chan_dung?: string | null;
  anh_vi_tri?: string | null;
  loi_tuyen_duong?: string | null;
}

export interface IVinhDanhListParams {
  nam?: number;
  thang?: number;
  trang_thai?: TrangThaiVinhDanh;
  page?: number;
  page_size?: number;
}
