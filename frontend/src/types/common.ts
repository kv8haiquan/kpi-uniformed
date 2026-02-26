/**
 * src/types/common.ts
 * ====================
 * TypeScript interfaces cho module Common (Thong bao, Tim kiem, Knowledge Base).
 * Map tu backend common_service/schemas/*.py
 */

// =============================================================================
// THONG BAO (Notification)
// =============================================================================

export type LoaiThongBao = 'KPI' | 'LMS' | 'FORUM' | 'LEGAL' | 'PORTAL' | 'HE_THONG';
export type MucDoThongBao = 'KHAN' | 'QUAN_TRONG' | 'BINH_THUONG';

export interface IThongBao {
  id: string;
  tieu_de: string;
  noi_dung?: string | null;
  loai: LoaiThongBao;
  muc_do: MucDoThongBao;
  link_url?: string | null;
  doi_tuong_type?: string | null;
  doi_tuong_id?: string | null;
  da_doc: boolean;
  ngay_doc?: string | null;
  created_at: string;
}

export interface IThongBaoListItem {
  id: string;
  tieu_de: string;
  loai: LoaiThongBao;
  muc_do: MucDoThongBao;
  link_url?: string | null;
  doi_tuong_type?: string | null;
  doi_tuong_id?: string | null;
  da_doc: boolean;
  created_at: string;
}

export interface IThongBaoCount {
  count: number;
  khan: number;
  quan_trong: number;
  binh_thuong: number;
}

export interface IThongBaoParams {
  loai?: LoaiThongBao;
  da_doc?: boolean;
  page?: number;
  page_size?: number;
}

// =============================================================================
// TIM KIEM (Unified Search)
// =============================================================================

export type SearchModule = 'LEGAL' | 'FORUM' | 'LMS' | 'PORTAL' | 'COMMON';

export interface ISearchResultItem {
  module: SearchModule;
  type: string;
  id: string;
  title: string;
  snippet: string;
  link: string;
  score: number;
}

export interface ISearchResponse {
  results: ISearchResultItem[];
  total_by_module: Record<string, number>;
  total: number;
  page: number;
  page_size: number;
}

export interface ISearchSuggestion {
  suggestions: string[];
}

export interface ISearchParams {
  q: string;
  modules?: string;
  page?: number;
  page_size?: number;
}

// =============================================================================
// KNOWLEDGE BASE (SOP/FAQ)
// =============================================================================

export type LoaiKB = 'SOP' | 'FAQ';
export type TrangThaiKB = 'NHAP' | 'CHO_DUYET' | 'DA_XUAT_BAN' | 'CAN_CAP_NHAT';

export interface IUserBrief {
  id: string;
  ma_cc: string;
  ho_ten: string;
}

export interface IKnowledgeBase {
  id: string;
  loai: LoaiKB;
  tieu_de: string;
  noi_dung: string;
  chuyen_de: string[];
  tags: string[];
  chu_so_huu?: IUserBrief | null;
  trang_thai: TrangThaiKB;
  van_ban_lien_quan?: string[] | null;
  chu_de_forum_lien_quan?: string[] | null;
  phien_ban: number;
  ngay_cap_nhat_cuoi?: string | null;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
}

export interface IKBListItem {
  id: string;
  loai: LoaiKB;
  tieu_de: string;
  chuyen_de: string[];
  tags: string[];
  trang_thai: TrangThaiKB;
  phien_ban: number;
  chu_so_huu?: IUserBrief | null;
  created_at: string;
  updated_at: string;
}

export interface IKBParams {
  loai?: LoaiKB;
  trang_thai?: TrangThaiKB;
  tags?: string;
  chuyen_de?: string;
  q?: string;
  page?: number;
  page_size?: number;
}

// =============================================================================
// CONSTANTS
// =============================================================================

export const LOAI_THONG_BAO_LABELS: Record<LoaiThongBao, string> = {
  KPI: 'KPI',
  LMS: 'Dao tao',
  FORUM: 'Dien dan',
  LEGAL: 'Phap luat',
  PORTAL: 'Tin tuc',
  HE_THONG: 'He thong',
};

export const MUC_DO_CONFIG: Record<MucDoThongBao, { label: string; cls: string }> = {
  KHAN: { label: 'Khan cap', cls: 'bg-red-100 text-red-700' },
  QUAN_TRONG: { label: 'Quan trong', cls: 'bg-orange-100 text-orange-700' },
  BINH_THUONG: { label: 'Binh thuong', cls: 'bg-gray-100 text-gray-600' },
};

export const TRANG_THAI_KB_CONFIG: Record<TrangThaiKB, { label: string; cls: string }> = {
  NHAP: { label: 'Nhap', cls: 'bg-gray-100 text-gray-600' },
  CHO_DUYET: { label: 'Cho duyet', cls: 'bg-yellow-100 text-yellow-700' },
  DA_XUAT_BAN: { label: 'Da xuat ban', cls: 'bg-green-100 text-green-700' },
  CAN_CAP_NHAT: { label: 'Can cap nhat', cls: 'bg-orange-100 text-orange-700' },
};

export const SEARCH_MODULE_LABELS: Record<SearchModule, string> = {
  LEGAL: 'Phap luat',
  FORUM: 'Dien dan',
  LMS: 'Dao tao',
  PORTAL: 'Tin tuc',
  COMMON: 'Kho tri thuc',
};
