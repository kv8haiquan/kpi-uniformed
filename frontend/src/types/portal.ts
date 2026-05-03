/**
 * src/types/portal.ts
 * ===================
 * TypeScript interfaces cho module Portal/Tài liệu.
 */

// =============================================================================
// PORTAL TYPES
// =============================================================================

// =============================================================================
// BÀI VIẾT (CMS)
// =============================================================================

export interface IBaiViet {
  id: string;
  tieu_de: string;
  tom_tat?: string | null;
  noi_dung: string | null;
  anh_dai_dien?: string | null;
  trang_thai: string;
  is_ghim: boolean;
  so_luot_xem: number;
  ngay_xuat_ban?: string | null;
  created_at: string;
  updated_at?: string | null;
}

// =============================================================================
// TÀI LIỆU (ECM)
// =============================================================================

export interface ITaiLieu {
  id: string;
  ten_tai_lieu: string;
  mo_ta: string | null;
  duong_dan: string;
  loai_file: string;
  phien_ban: number;
  created_at: string;
}

// =============================================================================
// DASHBOARD PORTAL
// =============================================================================

export interface ITinGhimBrief {
  id: string;
  tieu_de: string;
  tom_tat?: string | null;
  anh_dai_dien?: string | null;
  ngay_xuat_ban?: string | null;
  so_luot_xem: number;
}

export interface IPortalDashboardSummary {
  bai_viet_moi: number;
  tai_lieu_moi: number;
  tin_ghim: ITinGhimBrief[];
  tin_moi_nhat: ITinGhimBrief[];
}

// =============================================================================
// DASHBOARD CÁC MODULE KHÁC (placeholder — sẽ đầy đủ khi module sẵn sàng)
// =============================================================================

export interface IKPIDashboardSummary {
  diem_thang_nay?: number;
  xep_loai?: string;
  trang_thai_ke_khai?: string;
}

export interface ILMSDashboardSummary {
  khoa_dang_hoc?: number;
  khoa_hoan_thanh?: number;
  chung_chi?: number;
  /** Số đăng ký chờ phê duyệt (dành cho GV chủ khóa / QT_DAO_TAO). */
  cho_phe_duyet?: number;
}

export interface IHKGDashboardSummary {
  so_cuoc_hop_thang_nay?: number;
  so_cuoc_hop_tham_du?: number;
  ty_le_tham_du?: number;
  nhiem_vu_dang_lam?: number;
  nhiem_vu_qua_han?: number;
}

export interface IForumDashboardSummary {
  chu_de_moi?: number;
  tra_loi_moi?: number;
}

export interface ILegalDashboardSummary {
  vb_chua_doc?: number;
  vb_moi?: number;
}

export interface IThongBaoCount {
  count: number;
  khan: number;
  quan_trong: number;
  binh_thuong: number;
}
