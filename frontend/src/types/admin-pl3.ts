/**
 * src/types/admin-pl3.ts
 * ======================
 * Types cho Admin PL3 (Phase E — 29/04/2026).
 */

import { IDanhMucPL3 } from './kpi-v2';

export type KpiVersion = 'V1' | 'V2_PL3';

// =============================================================================
// CRUD danh mục PL3
// =============================================================================

export interface IDanhMucPL3CreateRequest {
  ma_danh_muc: string;          // unique, format PL3-{lv}-{stt}
  ten_cong_viec: string;
  linh_vuc: string;             // I-XV
  nhom_pl3: number;             // 1-5
  diem_cham: number;            // > 0, ≤ khung của nhóm
  nhiem_vu?: string;
  cong_viec_chi_tiet?: string;
  san_pham_dau_ra?: string;
  mo_ta?: string;
  is_active?: boolean;
}

export interface IDanhMucPL3UpdateRequest {
  ten_cong_viec?: string;
  linh_vuc?: string;
  nhom_pl3?: number;
  diem_cham?: number;
  nhiem_vu?: string;
  cong_viec_chi_tiet?: string;
  san_pham_dau_ra?: string;
  mo_ta?: string;
  is_active?: boolean;
}

// IDanhMucPL3 from kpi-v2.ts có đầy đủ fields response

// =============================================================================
// Import Excel
// =============================================================================

export interface IExcelImportError {
  row: number;
  ma_danh_muc: string | null;
  error: string;
}

export interface IExcelImportSummary {
  total_rows_in_file: number;
  valid: number;
  invalid: number;
  will_insert: number;
  will_update: number;
  skipped: number;
  actually_inserted?: number;
  actually_updated?: number;
}

export interface IExcelImportPreviewRow {
  ma_danh_muc: string;
  ten_cong_viec: string;
  linh_vuc: string;
  nhom_pl3: number;
  diem_cham: number;
  he_so_quy_doi: number;
  action: 'insert' | 'update';
}

export interface IExcelImportResponse {
  summary: IExcelImportSummary;
  errors: IExcelImportError[];
  preview: IExcelImportPreviewRow[];
  is_dry_run: boolean;
  file_hash?: string;
}

// =============================================================================
// Pin version
// =============================================================================

export interface IKpiVersionPinRequest {
  kpi_version_pinned: KpiVersion | null;
}

export interface IPinCcResponse {
  id: string;
  ma_cc: string;
  kpi_version_pinned: KpiVersion | null;
}

export interface IPinDonViResponse {
  don_vi_id: string;
  ten_don_vi: string;
  total_cc: number;
  updated: number;
  kpi_version_pinned: KpiVersion | null;
}

// =============================================================================
// Filter list admin
// =============================================================================

export interface IAdminListPL3Params {
  linh_vuc?: string;
  nhom_pl3?: number;
  search?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

// Re-export IDanhMucPL3 cho convenience
export type { IDanhMucPL3 };
