/**
 * types/phieu-danh-gia.ts
 * ========================
 * Types cho Phiếu theo dõi, đánh giá công chức theo QUÝ (Mẫu 01A/01B).
 */

export type TrangThaiPhieuDanhGia =
  | 'NHAP'
  | 'CHO_PHE_DUYET'
  | 'DA_PHE_DUYET'
  | 'BI_TU_CHOI';

export interface NguoiKy {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string | null;
}

export interface PhieuDanhGiaQuy {
  id: string;
  cong_chuc_id: string;
  cong_chuc: NguoiKy | null;

  quy: number;
  nam: number;

  uu_diem: string | null;
  han_che: string | null;
  y_kien_lanh_dao: string | null;

  trang_thai: TrangThaiPhieuDanhGia;
  ngay_gui_duyet: string | null;

  nguoi_phe_duyet_id: string | null;
  nguoi_phe_duyet: NguoiKy | null;
  ngay_phe_duyet: string | null;
  ly_do_tu_choi: string | null;

  created_at: string;
  updated_at: string;
}

export interface UpsertPhieuQuyRequest {
  quy: number;
  nam: number;
  uu_diem?: string | null;
  han_che?: string | null;
}

export interface PheDuyetPhieuRequest {
  y_kien_lanh_dao?: string | null;
}

export interface TuChoiPhieuRequest {
  ly_do_tu_choi: string;
}

export interface PhieuChoPheDuyetItem {
  id: string;
  cong_chuc_id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string | null;
  don_vi_ten: string | null;
  quy: number;
  nam: number;
  trang_thai: TrangThaiPhieuDanhGia;
  ngay_gui_duyet: string | null;
  uu_diem: string | null;
  han_che: string | null;
}

export interface ChoPheDuyetResponse {
  items: PhieuChoPheDuyetItem[];
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
  };
}
