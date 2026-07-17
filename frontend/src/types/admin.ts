/**
 * src/types/admin.ts
 * ==================
 * Type definitions cho Admin Module.
 * 
 * Version: 1.0.0 (30/01/2026)
 */

// =============================================================================
// USER TYPES
// =============================================================================

export interface IUserResponse {
  id: string;
  ma_cc: string;
  ho_ten: string;
  email: string | null;
  so_dien_thoai: string | null;
  ngay_sinh: string | null;
  gioi_tinh: 'NAM' | 'NU' | null;
  chuc_vu: string | null;
  is_lanh_dao: boolean;
  is_active: boolean;
  ngay_vao_nganh: string | null;
  ngay_vao_chi_cuc: string | null;
  last_login: string | null;
  created_at: string;
  // Đơn vị
  don_vi_id: string | null;
  don_vi_ma: string | null;
  don_vi_ten: string | null;
  // Vai trò
  vai_tro_id: string | null;
  vai_tro_ma: string | null;
  vai_tro_ten: string | null;
}

export interface IUserCreateRequest {
  ma_cc: string;
  ho_ten: string;
  don_vi_id: string;
  vai_tro_id: string;
  email?: string | null;
  so_dien_thoai?: string | null;
  ngay_sinh?: string | null;
  gioi_tinh?: 'NAM' | 'NU' | null;
  chuc_vu?: string | null;
  ngay_vao_nganh?: string | null;
  ngay_vao_chi_cuc?: string | null;
  is_lanh_dao?: boolean;
}

export interface IUserUpdateRequest {
  ho_ten?: string;
  email?: string | null;
  so_dien_thoai?: string | null;
  ngay_sinh?: string | null;
  gioi_tinh?: 'NAM' | 'NU' | null;
  chuc_vu?: string | null;
  ngay_vao_nganh?: string | null;
  ngay_vao_chi_cuc?: string | null;
}

export interface IUserStatusRequest {
  is_active: boolean;
  ly_do?: string;
  ngay_hieu_luc?: string;
}

export interface IUserTransferRequest {
  don_vi_id_moi?: string;
  vai_tro_id_moi?: string;
  chuc_vu_moi?: string;
  is_lanh_dao?: boolean;
  ly_do?: string;
  ngay_hieu_luc?: string;
}

// =============================================================================
// TRANSFER HISTORY
// =============================================================================

export type LoaiLichSuDieuChuyen = 'DIEU_CHUYEN' | 'VO_HIEU_HOA' | 'KICH_HOAT';

export interface ILichSuDieuChuyenResponse {
  id: string;
  cong_chuc_id: string;
  cong_chuc_ho_ten?: string | null;
  cong_chuc_ma_cc?: string | null;
  loai: LoaiLichSuDieuChuyen;
  don_vi_cu_id: string | null;
  don_vi_cu_ten: string | null;
  don_vi_moi_id: string | null;
  don_vi_moi_ten: string | null;
  vai_tro_cu_id: string | null;
  vai_tro_cu_ten: string | null;
  vai_tro_moi_id: string | null;
  vai_tro_moi_ten: string | null;
  chuc_vu_cu: string | null;
  chuc_vu_moi: string | null;
  ly_do: string | null;
  ngay_hieu_luc: string | null;
  nguoi_thuc_hien_id: string | null;
  nguoi_thuc_hien_ten: string | null;
  created_at: string;
}

export interface ILichSuDieuChuyenUpdateRequest {
  loai?: LoaiLichSuDieuChuyen;
  don_vi_cu_id?: string | null;
  don_vi_moi_id?: string | null;
  vai_tro_cu_id?: string | null;
  vai_tro_moi_id?: string | null;
  chuc_vu_cu?: string | null;
  chuc_vu_moi?: string | null;
  ngay_hieu_luc?: string | null;
  ly_do?: string | null;
  dong_bo_hien_tai?: boolean;
}

// =============================================================================
// SP CHUẨN TYPES
// =============================================================================

export interface ISpChuanResponse {
  id: string;
  ma_sp: string;
  ten_sp: string;
  mo_ta: string | null;
  thoi_gian_phut: number | null;
  he_so_quy_doi_sp1: string | number;
  is_sp_goc: boolean;
  is_active: boolean;
  created_at: string;
}

export interface ISpChuanCreateRequest {
  ma_sp: string;
  ten_sp: string;
  mo_ta?: string | null;
  thoi_gian_phut?: number | null;
  he_so_quy_doi_sp1: number;
}

export interface ISpChuanUpdateRequest {
  ten_sp?: string;
  mo_ta?: string | null;
  thoi_gian_phut?: number | null;
  he_so_quy_doi_sp1?: number;
}

// =============================================================================
// CẤP ĐỘ TYPES
// =============================================================================

export interface ICapDoResponse {
  id: string;
  ma_cap_do: string;
  ten_cap_do: string;
  mo_ta: string | null;
  he_so_sp1: string | number;
  he_so_sp2: string | number;
  is_theo_thuc_te: boolean;
  thu_tu: number;
  is_active: boolean;
  created_at: string;
}

export interface ICapDoCreateRequest {
  ma_cap_do: string;
  ten_cap_do: string;
  mo_ta?: string | null;
  he_so_sp1: number;
  he_so_sp2: number;
  is_theo_thuc_te?: boolean;
  thu_tu: number;
}

export interface ICapDoUpdateRequest {
  ten_cap_do?: string;
  mo_ta?: string | null;
  he_so_sp1?: number;
  he_so_sp2?: number;
  is_theo_thuc_te?: boolean;
  thu_tu?: number;
}

// =============================================================================
// DANH MỤC CÔNG VIỆC TYPES
// =============================================================================

export interface IDanhMucCvResponse {
  id: string;
  ma_danh_muc: string;
  ten_cong_viec: string;
  mo_ta: string | null;
  nhom_cong_viec: string | null;
  is_active: boolean;
  sp_chuan_id: string;
  sp_chuan_ma: string | null;
  sp_chuan_ten: string | null;
  he_so_quy_doi: string | number | null;
  don_vi_ap_dung_id: string | null;
  don_vi_ap_dung_ten: string | null;
  created_at: string;
}

export interface IDanhMucCvCreateRequest {
  ma_danh_muc: string;
  ten_cong_viec: string;
  mo_ta?: string | null;
  sp_chuan_id: string;
  don_vi_ap_dung_id?: string | null;
  nhom_cong_viec?: string | null;
}

export interface IDanhMucCvUpdateRequest {
  ten_cong_viec?: string;
  mo_ta?: string | null;
  sp_chuan_id?: string;
  don_vi_ap_dung_id?: string | null;
  nhom_cong_viec?: string | null;
}

// =============================================================================
// ADMIN STATS
// =============================================================================

export interface IAdminStats {
  tong_user: number;
  user_active: number;
  user_inactive: number;
  tong_don_vi: number;
  tong_sp_chuan: number;
  tong_cap_do: number;
  tong_danh_muc_cv: number;
}

// =============================================================================
// ĐƠN VỊ & VAI TRÒ (Reference)
// =============================================================================

export interface IDonViOption {
  id: string;
  ma_don_vi: string;
  ten_don_vi: string;
}

export interface IVaiTroOption {
  id: string;
  ma_vai_tro: string;
  ten_vai_tro: string;
  is_lanh_dao: boolean;
}

// =============================================================================
// PAGINATION
// =============================================================================

export interface IPagination {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface IPaginatedResponse<T> {
  success: boolean;
  data: T[];
  pagination: IPagination;
  message?: string;
}
