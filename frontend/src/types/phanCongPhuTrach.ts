/**
 * src/types/phanCongPhuTrach.ts
 * =============================
 * TypeScript types cho phân công CCT/PCCT phụ trách đơn vị.
 */

export interface ICongChucBrief {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu?: string | null;
}

export interface IDonViBrief {
  id: string;
  ma_don_vi: string;
  ten_don_vi: string;
}

export interface IPhanCongPhuTrach {
  id: string;
  lanh_dao_id: string;
  don_vi_id: string;
  hieu_luc_tu: string; // YYYY-MM-DD
  hieu_luc_den: string | null;
  ghi_chu: string | null;
  is_deleted: boolean;
  lanh_dao?: ICongChucBrief | null;
  don_vi?: IDonViBrief | null;
}

export interface IPhanCongCreateRequest {
  lanh_dao_id: string;
  don_vi_id: string;
  hieu_luc_tu: string;
  hieu_luc_den?: string | null;
  ghi_chu?: string | null;
}

export interface IPhanCongUpdateRequest {
  hieu_luc_den?: string | null;
  ghi_chu?: string | null;
}

export interface IPhanCongKetThucRequest {
  hieu_luc_den: string;
}

export interface ILanhDaoKhaDung {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string | null;
  ma_vai_tro: string;
  cap_bac: string;
}

export interface IDonViKhaDung {
  id: string;
  ma_don_vi: string;
  ten_don_vi: string;
  loai_don_vi: string;
}

// Phase 3+ (05/05/2026): PCCT/CCT tự cập nhật phân công
export interface IMyActiveAssignment {
  phan_cong_id: string;
  don_vi_id: string;
  ma_don_vi: string;
  ten_don_vi: string;
  hieu_luc_tu: string;
}

export interface IDonViWithCurrent {
  id: string;
  ma_don_vi: string;
  ten_don_vi: string;
  loai_don_vi: string;
  current_lanh_dao_id: string | null;
  current_lanh_dao_ma_cc: string | null;
  current_lanh_dao_ho_ten: string | null;
  is_mine: boolean;
}

export interface IPhanCongConflict {
  don_vi_id: string;
  ma_don_vi: string;
  ten_don_vi: string;
  lanh_dao_ma_cc: string | null;
  lanh_dao_ho_ten: string | null;
}
