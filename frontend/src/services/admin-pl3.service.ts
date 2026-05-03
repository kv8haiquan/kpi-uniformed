/**
 * services/admin-pl3.service.ts
 * =============================
 * Service admin cho danh mục PL3 + import + pin version (Phase E).
 *
 * Mapping endpoint backend (Phase C):
 *   GET    /admin/danh-muc-pl3                       → list
 *   GET    /admin/danh-muc-pl3/{id}                  → detail
 *   POST   /admin/danh-muc-pl3                       → create
 *   PUT    /admin/danh-muc-pl3/{id}                  → update
 *   DELETE /admin/danh-muc-pl3/{id}                  → soft delete
 *
 *   GET    /admin/danh-muc-v1                        → list V1
 *   PUT    /admin/danh-muc-v1/{id}/deactivate        → deactivate V1
 *
 *   POST   /admin/danh-muc-pl3/import/dry-run        → dry-run upload
 *   POST   /admin/danh-muc-pl3/import/commit         → commit upload
 *
 *   PUT    /admin/cong-chuc/{id}/kpi-version         → pin CC
 *   PUT    /admin/don-vi/{id}/kpi-version            → bulk pin đơn vị
 */

import apiClient from '@/lib/axios';
import { IDataResponse, IPaginatedResponse } from '@/types/api';
import {
  IAdminListPL3Params,
  IDanhMucPL3,
  IDanhMucPL3CreateRequest,
  IDanhMucPL3UpdateRequest,
  IExcelImportResponse,
  IKpiVersionPinRequest,
  IPinCcResponse,
  IPinDonViResponse,
  KpiVersion,
} from '@/types/admin-pl3';

// =============================================================================
// CRUD PL3
// =============================================================================

async function listPL3(
  params: IAdminListPL3Params = {}
): Promise<IPaginatedResponse<IDanhMucPL3>> {
  const sp = new URLSearchParams();
  if (params.linh_vuc) sp.append('linh_vuc', params.linh_vuc);
  if (params.nhom_pl3 !== undefined) sp.append('nhom_pl3', String(params.nhom_pl3));
  if (params.search) sp.append('search', params.search);
  if (params.is_active !== undefined) sp.append('is_active', String(params.is_active));
  if (params.page) sp.append('page', String(params.page));
  if (params.page_size) sp.append('page_size', String(params.page_size));
  const res = await apiClient.get<IPaginatedResponse<IDanhMucPL3>>(
    `/admin/danh-muc-pl3?${sp.toString()}`
  );
  return res.data;
}

async function detailPL3(id: string): Promise<IDanhMucPL3> {
  const res = await apiClient.get<IDataResponse<IDanhMucPL3>>(`/admin/danh-muc-pl3/${id}`);
  return res.data.data;
}

async function createPL3(data: IDanhMucPL3CreateRequest): Promise<IDanhMucPL3> {
  const res = await apiClient.post<IDataResponse<IDanhMucPL3>>('/admin/danh-muc-pl3', data);
  return res.data.data;
}

async function updatePL3(id: string, data: IDanhMucPL3UpdateRequest): Promise<IDanhMucPL3> {
  const res = await apiClient.put<IDataResponse<IDanhMucPL3>>(`/admin/danh-muc-pl3/${id}`, data);
  return res.data.data;
}

async function deactivatePL3(id: string): Promise<void> {
  await apiClient.delete(`/admin/danh-muc-pl3/${id}`);
}

// =============================================================================
// V1 read-only
// =============================================================================

async function listV1(
  params: { is_active?: boolean; page?: number; page_size?: number } = {}
): Promise<IPaginatedResponse<IDanhMucPL3>> {
  const sp = new URLSearchParams();
  if (params.is_active !== undefined) sp.append('is_active', String(params.is_active));
  if (params.page) sp.append('page', String(params.page));
  if (params.page_size) sp.append('page_size', String(params.page_size));
  const res = await apiClient.get<IPaginatedResponse<IDanhMucPL3>>(
    `/admin/danh-muc-v1?${sp.toString()}`
  );
  return res.data;
}

async function deactivateV1(id: string): Promise<void> {
  await apiClient.put(`/admin/danh-muc-v1/${id}/deactivate`);
}

// =============================================================================
// Import Excel
// =============================================================================

async function importDryRun(file: File): Promise<IExcelImportResponse> {
  const fd = new FormData();
  fd.append('file', file);
  const res = await apiClient.post<IDataResponse<IExcelImportResponse>>(
    '/admin/danh-muc-pl3/import/dry-run',
    fd,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return res.data.data;
}

async function importCommit(file: File): Promise<IExcelImportResponse> {
  const fd = new FormData();
  fd.append('file', file);
  const res = await apiClient.post<IDataResponse<IExcelImportResponse>>(
    '/admin/danh-muc-pl3/import/commit',
    fd,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return res.data.data;
}

// =============================================================================
// Pin version
// =============================================================================

async function setCongChucVersion(
  ccId: string,
  version: KpiVersion | null
): Promise<IPinCcResponse> {
  const body: IKpiVersionPinRequest = { kpi_version_pinned: version };
  const res = await apiClient.put<IDataResponse<IPinCcResponse>>(
    `/admin/cong-chuc/${ccId}/kpi-version`,
    body
  );
  return res.data.data;
}

async function setDonViVersion(
  dvId: string,
  version: KpiVersion | null
): Promise<IPinDonViResponse> {
  const body: IKpiVersionPinRequest = { kpi_version_pinned: version };
  const res = await apiClient.put<IDataResponse<IPinDonViResponse>>(
    `/admin/don-vi/${dvId}/kpi-version`,
    body
  );
  return res.data.data;
}

// =============================================================================
// EXPORT
// =============================================================================

export const adminPL3Service = {
  listPL3,
  detailPL3,
  createPL3,
  updatePL3,
  deactivatePL3,
  listV1,
  deactivateV1,
  importDryRun,
  importCommit,
  setCongChucVersion,
  setDonViVersion,
};
