/**
 * types/xep-loai-quy.ts
 * =====================
 * TypeScript types cho Xếp loại quý (Quarterly Assessment)
 *
 * Version: 3.6.0 (2026-04-14)
 */

// Reuse types from existing modules
export interface ICongChucBrief {
  id: string;
  ma_cc: string;
  ho_ten: string;
  email?: string;
  so_dien_thoai?: string;
  chuc_vu?: string;
  is_lanh_dao: boolean;
}

export interface IDonVi {
  id: string;
  ma_don_vi: string;
  ten_don_vi: string;
  loai_don_vi: string;
}

// ============================================================================
// ENUMS
// ============================================================================

export type MucXepLoaiQuy = 'A' | 'B' | 'C' | 'D';

// ============================================================================
// DANH GIA THANG TRONG QUY
// ============================================================================

export interface DanhGiaThangTrongQuy {
  thang: number;
  diem_kpi: number | null;
  diem_tc: number | null;
  diem_tong: number | null;
  xep_loai_thang: string | null;
  co_du_lieu: boolean;
  nguon: string | null; // "DA_PHE_DUYET" | "CHO_PHE_DUYET" | "real_time" | null
}

// ============================================================================
// TIEU CHI QUY
// ============================================================================

export interface TieuChiQuyItem {
  tieu_chi_id: string;
  ma_tieu_chi: string;
  ten_tieu_chi: string;
  nhom: number;
  diem_toi_da: number;
  is_vi_pham: boolean;
  is_dat: boolean;
  cac_thang_vi_pham: number[];
  cac_thang_dat: number[];
}

// ============================================================================
// RESPONSES
// ============================================================================

export interface TongHopQuyItem {
  stt: number;
  cong_chuc_id: string;
  ma_cc: string;
  ho_ten: string;
  don_vi_ten: string;
  is_lanh_dao: boolean;
  diem_kpi_quy: number | null;
  diem_tc_quy: number | null;
  diem_tong_quy: number | null;
  xep_loai_quy: MucXepLoaiQuy | null;
  co_chuyen_don_vi: boolean;
  ghi_chu: string | null;
}

export interface ThongKeQuyResponse {
  tong_so_cc: number;
  so_luong_A: number;
  so_luong_B: number;
  so_luong_C: number;
  so_luong_D: number;
  so_luong_chua_tinh: number;
  ty_le_A: number;
  ty_le_B: number;
  ty_le_C: number;
  ty_le_D: number;
}

export interface TongHopQuyResponse {
  data: TongHopQuyItem[];
  thong_ke: ThongKeQuyResponse;
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
  };
}

export interface ChiTietQuyResponse {
  cong_chuc_id: string;
  cong_chuc: ICongChucBrief | null;
  don_vi: IDonVi | null;
  quy: number;
  nam: number;
  cac_thang: DanhGiaThangTrongQuy[];
  tieu_chi_quy: TieuChiQuyItem[];
  diem_kpi_quy: number | null;
  diem_tc_quy: number | null;
  diem_tong_quy: number | null;
  xep_loai_quy: MucXepLoaiQuy | null;
  co_chuyen_don_vi: boolean;
  ghi_chu: string | null;
}

// ============================================================================
// REQUESTS
// ============================================================================

export interface TinhLaiQuyRequest {
  quy: number;
  nam: number;
  don_vi_id?: string;
  cong_chuc_id?: string;
}

// ============================================================================
// QUERY PARAMS
// ============================================================================

export interface XepLoaiQuyQueryParams {
  quy: number;
  nam: number;
  don_vi_id?: string;
  page?: number;
  page_size?: number;
}

export interface ChoPheQuyetQueryParams {
  quy?: number;
  nam?: number;
  page?: number;
  page_size?: number;
}

// ============================================================================
// BÁO CÁO XẾP LOẠI QUÝ (WORKFLOW)
// ============================================================================

export type TrangThaiBaoCaoQuy = 'NHAP' | 'CHO_PHE_DUYET' | 'DA_PHE_DUYET' | 'TU_CHOI';

export interface BriefInfo {
  id: string;
  ma_cc?: string;
  ma_don_vi?: string;
  ho_ten?: string;
  ten_don_vi?: string;
  chuc_vu?: string;
}

export interface ChiTietXepLoaiQuy {
  id: string;
  cong_chuc_id: string;
  cong_chuc: BriefInfo | null;
  is_lanh_dao: boolean;
  diem_tieu_chi_chung: number;
  diem_kpi: number;
  diem_tong: number;
  xep_loai_he_thong: MucXepLoaiQuy | null;
  xep_loai_de_xuat: MucXepLoaiQuy | null;
  xep_loai_quyet_dinh: MucXepLoaiQuy | null;
  ly_do_dieu_chinh_dt: string | null;
  ly_do_dieu_chinh_cct: string | null;
  bi_tu_choi: boolean;
  ly_do_tu_choi: string | null;
  ghi_chu: string | null;
}

export interface BaoCaoXepLoaiQuy {
  id: string;
  don_vi_id: string;
  don_vi: BriefInfo | null;
  quy: number;
  nam: number;
  trang_thai: TrangThaiBaoCaoQuy;
  nguoi_lap_id: string;
  nguoi_lap: BriefInfo | null;
  ngay_lap: string | null;
  ngay_gui_duyet: string | null;
  nguoi_phe_duyet_id: string | null;
  nguoi_phe_duyet: BriefInfo | null;
  ngay_phe_duyet: string | null;
  y_kien_phe_duyet: string | null;
  tong_cong_chuc: number;
  so_loai_a: number;
  so_loai_b: number;
  so_loai_c: number;
  so_loai_d: number;
  so_loai_e: number;
  canh_bao_ty_le_a: boolean;
  chi_tiets: ChiTietXepLoaiQuy[];
  canh_bao?: string;
  last_recalculated_at?: string | null;
}
