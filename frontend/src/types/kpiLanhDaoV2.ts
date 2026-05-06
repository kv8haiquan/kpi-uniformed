/**
 * src/types/kpiLanhDaoV2.ts
 * ========================
 * Types cho KPI lãnh đạo công thức mới (từ tháng 4/2026).
 */

export interface IKpiLanhDaoV2 {
  cong_chuc_id: string;
  thang: number;
  nam: number;
  cap_bac: 'PDV' | 'TDV' | 'PCCT' | 'CCT';

  // Phase 3 fix (05/05/2026): SP quy đổi (so_sp_goc_quy_doi) thay vì đếm CV
  // ===== Scope tổng (dùng tính KPI chính thức) =====
  tong_sp_ke_khai: number;
  tong_sp_hoan_thanh: number;
  sp_chat_luong: number;
  sp_tien_do: number;
  so_kekhai_records: number;

  a: number;  // hoàn thành
  b: number;  // tỷ lệ tiến độ
  c: number;  // tỷ lệ chất lượng

  // ===== Scope LĐ tự kê (chỉ thông tin tham khảo) =====
  tong_sp_ke_khai_self: number;
  sp_chat_luong_self: number;
  sp_tien_do_self: number;
  so_kekhai_records_self: number;

  a_self: number;
  b_self: number;
  c_self: number;

  // ===== d, đ, e =====
  d: number;
  dd: number;
  e: number;

  kpi_tong: number;
  has_phan_cong: boolean | null;
  is_v2_active: boolean;
}

export interface IKpiLanhDaoV2FeatureFlag {
  tu_thang: number;
  tu_nam: number;
  mo_ta: string;
}

// Yêu cầu 1 (06/05/2026): list chi tiết CV trong scope KPI LĐ
export interface ICongViecLanhDaoV2 {
  ke_khai_id: string;
  loai: 'TU_LAM' | 'CAP_DUOI';
  cong_chuc_id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string | null;
  danh_muc_sp_id: string | null;
  ma_danh_muc: string | null;
  ten_cong_viec: string | null;
  linh_vuc: string | null;
  nhom_pl3: number | null;
  ngay_thuc_hien: string | null;
  so_luong: number;
  so_sp_goc_quy_doi: number;
  sp_chat_luong: number;
  sp_tien_do: number;
  so_loi_chat_luong: number;
  so_loi_tien_do: number;
  tu_danh_gia_chat_luong: number;
  tu_danh_gia_tien_do: number;
  trang_thai: string;
}
