/**
 * src/types/forum.ts
 * ==================
 * TypeScript interfaces cho module Dien dan (Forum).
 * Map tu backend forum_service/schemas/*.py
 */

// =============================================================================
// COMMON
// =============================================================================

export interface IUserBrief {
  id: string;
  ma_cc: string | null;
  ho_ten: string;
  chuc_vu: string | null;
  don_vi_ten: string | null;
}

export interface ICanCuPhapLy {
  loai: 'VAN_BAN' | 'SOP';
  id: string;
  trich_dan: string;
}

// =============================================================================
// CHUYEN MUC
// =============================================================================

export interface IChuDeMoiNhat {
  id: string;
  tieu_de: string;
  created_at: string;
}

export interface IChuyenMuc {
  id: string;
  ten_chuyen_muc: string;
  mo_ta: string | null;
  icon: string | null;
  thu_tu: number | null;
  parent_id: string | null;
  chi_doc: boolean;
  yeu_cau_duyet: boolean;
  is_active: boolean;
  created_at: string;
  so_chu_de: number;
  so_tra_loi: number;
  chu_de_moi_nhat: IChuDeMoiNhat | null;
  children: IChuyenMuc[];
}

export interface IChuyenMucCreate {
  ten_chuyen_muc: string;
  mo_ta?: string;
  icon?: string;
  thu_tu?: number;
  parent_id?: string;
  chi_doc?: boolean;
  yeu_cau_duyet?: boolean;
}

export interface IChuyenMucUpdate {
  ten_chuyen_muc?: string;
  mo_ta?: string;
  icon?: string;
  thu_tu?: number;
  chi_doc?: boolean;
  yeu_cau_duyet?: boolean;
  is_active?: boolean;
}

// =============================================================================
// CHU DE
// =============================================================================

export type TrangThaiChuDe = 'CHO_DUYET' | 'MO' | 'DONG' | 'AN';

export interface IChuDeListItem {
  id: string;
  tieu_de: string;
  noi_dung_tom_tat: string;
  tags: string[];
  tac_gia: IUserBrief | null;
  trang_thai: TrangThaiChuDe;
  is_ghim: boolean;
  is_khoa: boolean;
  so_luot_xem: number;
  so_tra_loi: number;
  so_upvote: number;
  co_dap_an_chuan: boolean;
  created_at: string;
  updated_at: string;
}

export interface ITraLoiInChuDe {
  id: string;
  noi_dung: string;
  tac_gia: IUserBrief | null;
  is_dap_an_chuan: boolean;
  is_an: boolean;
  so_upvote: number;
  da_upvote: boolean | null;
  can_cu_phap_ly: ICanCuPhapLy[] | null;
  created_at: string;
  updated_at: string;
  children: ITraLoiInChuDe[];
}

export interface IChuDeDetail {
  id: string;
  chuyen_muc_id: string;
  tieu_de: string;
  noi_dung: string;
  tags: string[];
  tac_gia: IUserBrief | null;
  trang_thai: TrangThaiChuDe;
  is_ghim: boolean;
  is_khoa: boolean;
  so_luot_xem: number;
  so_tra_loi: number;
  so_upvote: number;
  tra_loi_chuan_id: string | null;
  van_ban_lien_quan: unknown[] | null;
  sop_lien_quan: unknown[] | null;
  nguoi_duyet_id: string | null;
  ngay_duyet: string | null;
  created_at: string;
  updated_at: string;
  da_upvote: boolean | null;
  da_theo_doi: boolean | null;
  co_dap_an_chuan: boolean;
  tra_loi: ITraLoiInChuDe[];
}

export interface IChuDeCreate {
  chuyen_muc_id: string;
  tieu_de: string;
  noi_dung: string;
  tags?: string[];
  van_ban_lien_quan?: string[];
  sop_lien_quan?: string[];
}

export interface IChuDeUpdate {
  tieu_de?: string;
  noi_dung?: string;
  tags?: string[];
  van_ban_lien_quan?: string[];
  sop_lien_quan?: string[];
}

export type HanhDongType = 'GHIM' | 'BO_GHIM' | 'KHOA' | 'MO_KHOA' | 'DUYET' | 'AN';

export interface IHanhDongChuDe {
  hanh_dong: HanhDongType;
  ly_do?: string;
}

export interface IChonDapAnChuan {
  tra_loi_id: string;
}

// =============================================================================
// TRA LOI
// =============================================================================

export interface ITraLoiCreate {
  noi_dung: string;
  parent_id?: string;
  can_cu_phap_ly?: ICanCuPhapLy[];
}

export interface ITraLoiUpdate {
  noi_dung?: string;
  can_cu_phap_ly?: ICanCuPhapLy[];
}

export interface ITraLoiResponse {
  id: string;
  chu_de_id: string;
  parent_id: string | null;
  noi_dung: string;
  tac_gia: IUserBrief | null;
  is_dap_an_chuan: boolean;
  is_an: boolean;
  so_upvote: number;
  can_cu_phap_ly: ICanCuPhapLy[] | null;
  created_at: string;
  updated_at: string;
}

// =============================================================================
// BIEU QUYET (VOTE)
// =============================================================================

export type DoiTuongType = 'CHU_DE' | 'TRA_LOI';
export type LoaiVote = 'UP' | 'DOWN';

export interface IBieuQuyetCreate {
  doi_tuong_type: DoiTuongType;
  doi_tuong_id: string;
  loai: LoaiVote;
}

export interface IBieuQuyetResponse {
  hanh_dong: 'CREATED' | 'TOGGLED_OFF' | 'CHANGED';
  loai: LoaiVote | null;
  so_upvote_moi: number;
}

// =============================================================================
// DASHBOARD / BAO CAO
// =============================================================================

export interface IDashboardSummary {
  chu_de_moi_tuan: number;
  tra_loi_chua_doc: number;
  upvote_tuan: number;
  chu_de_cua_toi_chua_tra_loi: number;
}

export interface IBaoCaoCaNhan {
  thang: number;
  nam: number;
  chu_de_da_dang: number;
  tra_loi_da_dang: number;
  upvote_nhan_duoc: number;
  bai_ghim: number;
  dap_an_chuan: number;
}

export interface IBaoCaoDonVi {
  don_vi_id: string;
  don_vi_ten: string | null;
  thang: number;
  nam: number;
  tong_chu_de: number;
  tong_tra_loi: number;
  tong_upvote: number;
  so_nguoi_tham_gia: number;
}

export interface ITopContributor {
  user: IUserBrief;
  chu_de: number;
  tra_loi: number;
  upvote: number;
  dap_an_chuan: number;
  diem: number;
}

// =============================================================================
// QUERY PARAMS
// =============================================================================

export interface IChuDeQueryParams {
  chuyen_muc_id?: string;
  trang_thai?: TrangThaiChuDe;
  tags?: string;
  search?: string;
  sap_xep?: 'moi_nhat' | 'nhieu_upvote' | 'nhieu_tra_loi';
  page?: number;
  page_size?: number;
}

// =============================================================================
// TRANG THAI LABELS
// =============================================================================

export const TRANG_THAI_LABEL: Record<TrangThaiChuDe, string> = {
  CHO_DUYET: 'Cho duyet',
  MO: 'Dang mo',
  DONG: 'Da dong',
  AN: 'Da an',
};

export const TRANG_THAI_COLOR: Record<TrangThaiChuDe, string> = {
  CHO_DUYET: 'bg-yellow-100 text-yellow-700',
  MO: 'bg-green-100 text-green-700',
  DONG: 'bg-gray-100 text-gray-600',
  AN: 'bg-red-100 text-red-700',
};
