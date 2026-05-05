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

  tong_cv: number;
  tong_hoan_thanh: number;
  tong_cv_cc: number;
  tong_cv_ld: number;

  a: number;
  b: number;
  c: number;
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
