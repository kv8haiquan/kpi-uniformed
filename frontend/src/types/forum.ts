/**
 * src/types/forum.ts
 * ==================
 * TypeScript interfaces cho module Diễn đàn (Forum).
 */

// =============================================================================
// FORUM TYPES
// =============================================================================

export interface IChuDe {
  id: string;
  tieu_de: string;
  noi_dung: string | null;
  cong_chuc_id: string;
  trang_thai: string;
  created_at: string;
}

export interface ICauHoi {
  id: string;
  chu_de_id: string;
  tieu_de: string;
  noi_dung: string;
  cong_chuc_id: string;
  created_at: string;
}

export interface ITraLoi {
  id: string;
  cau_hoi_id: string;
  noi_dung: string;
  cong_chuc_id: string;
  created_at: string;
}
