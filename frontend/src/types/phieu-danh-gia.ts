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

/** Mã mức xếp loại (mẫu 02A/02B theo quý — Nghị định 335/2025/NĐ-CP). */
export type MucXepLoai = 'HTXSNV' | 'HTTNV' | 'HTNV' | 'KHTNV';

/** Nhãn hiển thị mức xếp loại. */
export const NHAN_XEP_LOAI: Record<MucXepLoai, string> = {
  HTXSNV: 'Hoàn thành xuất sắc nhiệm vụ',
  HTTNV: 'Hoàn thành tốt nhiệm vụ',
  HTNV: 'Hoàn thành nhiệm vụ',
  KHTNV: 'Không hoàn thành nhiệm vụ',
};

export interface PhieuDanhGiaQuy {
  id: string;
  cong_chuc_id: string;
  cong_chuc: NguoiKy | null;

  quy: number;
  nam: number;

  uu_diem: string | null;
  han_che: string | null;
  y_kien_lanh_dao: string | null;

  // Xếp loại (mẫu 02A/02B theo quý)
  tu_de_xuat_xep_loai: MucXepLoai | null;
  de_xuat_xep_loai: MucXepLoai | null;
  quyet_dinh_xep_loai: MucXepLoai | null;
  y_kien_cap_tham_quyen: string | null;

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
  /** Mục 5: CC tự đề xuất mức xếp loại. */
  tu_de_xuat_xep_loai?: MucXepLoai | null;
}

export interface PheDuyetPhieuRequest {
  /** Mục 6 (tháng) / Mục III.1 (quý): ý kiến nhận xét. */
  y_kien_lanh_dao?: string | null;
  /** Mục III.2 (quý): người trực tiếp sử dụng đề xuất mức xếp loại. */
  de_xuat_xep_loai?: MucXepLoai | null;
  /** Mục IV.1 (quý): quyết định mức xếp loại của cấp có thẩm quyền. */
  quyet_dinh_xep_loai?: MucXepLoai | null;
  /** Mục IV.2 (quý): ý kiến của cấp có thẩm quyền. */
  y_kien_cap_tham_quyen?: string | null;
}

export interface TuChoiPhieuRequest {
  ly_do_tu_choi: string;
}

export interface TraLaiPhieuRequest {
  ly_do?: string | null;
}

export interface PhieuChoPheDuyetItem {
  /** null khi CC chưa soạn phiếu (backend sinh virtual row NHAP). */
  id: string | null;
  cong_chuc_id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string | null;
  don_vi_ten: string | null;
  quy: number;
  nam: number;
  trang_thai: TrangThaiPhieuDanhGia;
  ngay_gui_duyet: string | null;
  ngay_phe_duyet: string | null;
  uu_diem: string | null;
  han_che: string | null;
  y_kien_lanh_dao: string | null;
  tu_de_xuat_xep_loai: MucXepLoai | null;
  de_xuat_xep_loai: MucXepLoai | null;
  quyet_dinh_xep_loai: MucXepLoai | null;
  y_kien_cap_tham_quyen: string | null;
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

export interface ChiTietThangThieu {
  thang: number;
  cv_chua_duyet: number;
  tc_chua_duyet: number;
}

export interface KiemTraDuDieuKienResponse {
  quy: number;
  nam: number;
  co_van_de: boolean;
  so_cv_chua_duyet: number;
  so_tc_chua_duyet: number;
  chi_tiet_thang: ChiTietThangThieu[];
}

// ============================================================================
// Phiếu THÁNG (08/05/2026)
// ============================================================================

export interface PhieuDanhGiaThang {
  id: string;
  cong_chuc_id: string;
  cong_chuc: NguoiKy | null;

  thang: number;
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

export interface UpsertPhieuThangRequest {
  thang: number;
  nam: number;
  uu_diem?: string | null;
  han_che?: string | null;
}

export interface PhieuThangChoPheDuyetItem {
  id: string | null;
  cong_chuc_id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string | null;
  don_vi_ten: string | null;
  thang: number;
  nam: number;
  trang_thai: TrangThaiPhieuDanhGia;
  ngay_gui_duyet: string | null;
  ngay_phe_duyet: string | null;
  uu_diem: string | null;
  han_che: string | null;
  y_kien_lanh_dao: string | null;
}

export interface ChoPheDuyetThangResponse {
  items: PhieuThangChoPheDuyetItem[];
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
  };
}

export interface KiemTraDuDieuKienThangResponse {
  thang: number;
  nam: number;
  co_van_de: boolean;
  so_cv_chua_duyet: number;
  so_tc_chua_duyet: number;
}
