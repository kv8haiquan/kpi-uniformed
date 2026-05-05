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
  tong_sp_ke_khai: number;
  tong_sp_hoan_thanh: number;
  sp_chat_luong: number;
  sp_tien_do: number;
  so_kekhai_records: number;

  a: number;  // hoàn thành
  b: number;  // tỷ lệ tiến độ
  c: number;  // tỷ lệ chất lượng
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
