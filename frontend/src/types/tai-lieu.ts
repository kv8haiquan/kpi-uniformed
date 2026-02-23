/**
 * src/types/tai-lieu.ts
 * ======================
 * TypeScript interfaces cho module Thư viện tài liệu ECM (Portal).
 */

// =============================================================================
// THƯ MỤC
// =============================================================================

export interface IThuMucItem {
  id: string;
  ten: string;
  parent_id?: string | null;
  thu_tu: number;
  quyen_truy_cap: string;
}

/** Thư mục dạng tree (có con) */
export interface IThuMucTree extends IThuMucItem {
  children: IThuMucTree[];
}

/** Thư mục tóm tắt (dùng trong tai_lieu) */
export interface IThuMucBrief {
  id: string;
  ten: string;
}

export interface IThuMucCreate {
  ten: string;
  parent_id?: string;
  thu_tu?: number;
  quyen_truy_cap?: string;
  don_vi_ids?: string[];
}

export interface IThuMucUpdate {
  ten?: string;
  thu_tu?: number;
  quyen_truy_cap?: string;
  don_vi_ids?: string[];
}

// =============================================================================
// USER BRIEF
// =============================================================================

export interface IUserBriefTL {
  id: string;
  ma_cc: string;
  ho_ten: string;
}

// =============================================================================
// TÀI LIỆU
// =============================================================================

/** Item trong danh sách tài liệu */
export interface ITaiLieuItem {
  id: string;
  ten_tai_lieu: string;
  mo_ta?: string | null;
  thu_muc: IThuMucBrief;
  file_name: string;
  file_url: string;
  file_size_bytes: number;
  file_type: string;
  phien_ban: number;
  nguoi_tai_len: IUserBriefTL;
  created_at: string;
  tags: string[];
}

/** Item trong lịch sử phiên bản */
export interface ITaiLieuVersionItem {
  id: string;
  phien_ban: number;
  file_name: string;
  file_url: string;
  file_size_bytes: number;
  nguoi_tai_len: IUserBriefTL;
  created_at: string;
}

/** Form tạo tài liệu mới */
export interface ITaiLieuCreate {
  thu_muc_id: string;
  ten_tai_lieu: string;
  mo_ta?: string;
  file_name: string;
  file_url: string;
  file_size_bytes: number;
  file_type: string;
  tags?: string[];
}

/** Form cập nhật tài liệu */
export interface ITaiLieuUpdate {
  ten_tai_lieu?: string;
  mo_ta?: string;
  tags?: string[];
}

/** Upload phiên bản mới */
export interface IUploadPhienBanMoiRequest {
  file_name: string;
  file_url: string;
  file_size_bytes: number;
  file_type: string;
  mo_ta?: string;
}

/** Params query cho danh sách tài liệu */
export interface ITaiLieuParams {
  thu_muc_id?: string;
  file_type?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

/** Response danh sách có phân trang */
export interface ITaiLieuListResponse {
  items: ITaiLieuItem[];
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
  };
}

// =============================================================================
// HELPERS
// =============================================================================

/** Icon theo loại file */
export function getFileIcon(fileType: string): string {
  if (fileType.includes('pdf')) return '📄';
  if (fileType.includes('word') || fileType.includes('docx') || fileType.includes('doc')) return '📝';
  if (fileType.includes('excel') || fileType.includes('xlsx') || fileType.includes('xls')) return '📊';
  if (fileType.includes('powerpoint') || fileType.includes('pptx') || fileType.includes('ppt')) return '📋';
  if (fileType.includes('image') || fileType.includes('png') || fileType.includes('jpg')) return '🖼️';
  if (fileType.includes('zip') || fileType.includes('rar')) return '🗜️';
  return '📎';
}

/** Định dạng kích thước file */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
