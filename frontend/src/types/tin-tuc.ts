/**
 * src/types/tin-tuc.ts
 * =====================
 * TypeScript interfaces cho module Tin tức CMS (Portal).
 */

// =============================================================================
// CHUYÊN MỤC
// =============================================================================

export interface IChuyenMuc {
  id: string;
  ten: string;
  slug: string;
  loai: string;
  mo_ta?: string | null;
  is_active?: boolean;
  thu_tu?: number;
  so_bai_viet?: number;
}

export interface IChuyenMucCreate {
  ten: string;
  loai: string;
  mo_ta?: string;
}

export interface IChuyenMucUpdate {
  ten?: string;
  loai?: string;
  mo_ta?: string;
  is_active?: boolean;
}

// =============================================================================
// USER BRIEF
// =============================================================================

export interface IUserBriefTT {
  id: string;
  ma_cc: string;
  ho_ten: string;
}

// =============================================================================
// BÀI VIẾT
// =============================================================================

/** Item trong danh sách bài viết */
export interface IBaiVietListItem {
  id: string;
  tieu_de: string;
  tom_tat?: string | null;
  anh_dai_dien?: string | null;
  chuyen_muc: IChuyenMuc;
  nguoi_soan: IUserBriefTT;
  trang_thai: string;
  ngay_xuat_ban?: string | null;
  so_luot_xem: number;
  is_ghim: boolean;
  created_at: string;
}

/** Chi tiết bài viết (bao gồm nội dung đầy đủ) */
export interface IBaiVietDetail extends IBaiVietListItem {
  noi_dung?: string | null;
  nguoi_kiem_tra?: IUserBriefTT | null;
  nguoi_duyet?: IUserBriefTT | null;
  updated_at?: string | null;
}

/** Form tạo bài viết */
export interface IBaiVietCreate {
  tieu_de: string;
  tom_tat?: string;
  noi_dung?: string;
  anh_dai_dien?: string;
  chuyen_muc_id: string;
}

/** Form sửa bài viết */
export interface IBaiVietUpdate {
  tieu_de?: string;
  tom_tat?: string;
  noi_dung?: string;
  anh_dai_dien?: string;
  chuyen_muc_id?: string;
}

/** Request đổi trạng thái workflow */
export interface IDoiTrangThaiRequest {
  trang_thai_moi: string;
  ghi_chu?: string;
}

/** Params query cho danh sách bài viết */
export interface IBaiVietParams {
  page?: number;
  page_size?: number;
  chuyen_muc_id?: string;
  search?: string;
  trang_thai?: string;
}

/** Pagination metadata */
export interface IPagination {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

/** Response danh sách bài viết có phân trang */
export interface IBaiVietListResponse {
  items: IBaiVietListItem[];
  pagination: IPagination;
}

// =============================================================================
// TRẠNG THÁI + HÀNH ĐỘNG WORKFLOW
// =============================================================================

/** Nhãn hiển thị trạng thái */
export const TRANG_THAI_LABEL: Record<string, string> = {
  NHAP: 'Nháp',
  KIEM_TRA: 'Kiểm tra',
  DUYET: 'Duyệt',
  XUAT_BAN: 'Xuất bản',
  THU_HOI: 'Thu hồi',
};

/** Màu badge trạng thái */
export const TRANG_THAI_COLOR: Record<string, string> = {
  NHAP: 'bg-gray-100 text-gray-600',
  KIEM_TRA: 'bg-yellow-100 text-yellow-700',
  DUYET: 'bg-blue-100 text-blue-700',
  XUAT_BAN: 'bg-green-100 text-green-700',
  THU_HOI: 'bg-red-100 text-red-700',
};
