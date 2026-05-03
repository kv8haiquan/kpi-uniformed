/**
 * src/services/kpi-v2.service.ts
 * ==============================
 * Service cho kê khai V2_PL3 (28/04/2026).
 *
 * Mapping endpoint backend:
 *   GET    /api/v1/danh-muc/linh-vuc                → getLinhVuc
 *   GET    /api/v1/danh-muc/sp-cong-viec/pl3        → searchDanhMucPL3
 *   POST   /api/v1/ke-khai-v2                       → createKeKhai
 *   PUT    /api/v1/ke-khai-v2/{id}                  → updateKeKhai
 *   DELETE /api/v1/ke-khai-v2/{id}                  → deleteKeKhai
 *   GET    /api/v1/ke-khai-v2/me                    → getMyKeKhai
 *   POST   /api/v1/ke-khai-v2/nhieu-ngay            → createMultiDay
 *   GET    /api/v1/ke-khai-v2/thong-ke/thang        → getThongKeThang
 */

import apiClient from '@/lib/axios';
import { IDataResponse, IPaginatedResponse } from '@/types/api';
import {
  IDanhMucPL3,
  IFavoriteItem,
  IKeKhaiV2CreateRequest,
  IKeKhaiV2MultiDayRequest,
  IKeKhaiV2MultiDayResponse,
  IKeKhaiV2Response,
  IKeKhaiV2UpdateRequest,
  ILinhVuc,
  IListMyKeKhaiV2Params,
  IRecentItem,
  ISearchPL3Params,
  IThongKeKeKhaiThangV2,
} from '@/types/kpi-v2';

// =============================================================================
// MASTER DATA
// =============================================================================

async function getLinhVuc(): Promise<ILinhVuc[]> {
  const res = await apiClient.get<IDataResponse<ILinhVuc[]>>('/danh-muc/linh-vuc');
  return res.data.data;
}

async function searchDanhMucPL3(
  params: ISearchPL3Params = {}
): Promise<IPaginatedResponse<IDanhMucPL3>> {
  const search = new URLSearchParams();
  if (params.linh_vuc) search.append('linh_vuc', params.linh_vuc);
  if (params.nhom_pl3 !== undefined) search.append('nhom_pl3', String(params.nhom_pl3));
  if (params.search) search.append('search', params.search);
  if (params.page) search.append('page', String(params.page));
  if (params.size) search.append('size', String(params.size));

  const res = await apiClient.get<IPaginatedResponse<IDanhMucPL3>>(
    `/danh-muc/sp-cong-viec/pl3?${search.toString()}`
  );
  return res.data;
}

// =============================================================================
// KÊ KHAI V2
// =============================================================================

async function createKeKhai(data: IKeKhaiV2CreateRequest): Promise<IKeKhaiV2Response> {
  const res = await apiClient.post<IDataResponse<IKeKhaiV2Response>>('/ke-khai-v2', data);
  return res.data.data;
}

async function updateKeKhai(
  id: string,
  data: IKeKhaiV2UpdateRequest
): Promise<IKeKhaiV2Response> {
  const res = await apiClient.put<IDataResponse<IKeKhaiV2Response>>(`/ke-khai-v2/${id}`, data);
  return res.data.data;
}

async function deleteKeKhai(id: string): Promise<void> {
  await apiClient.delete(`/ke-khai-v2/${id}`);
}

async function getKeKhaiDetail(id: string): Promise<IKeKhaiV2Response> {
  const res = await apiClient.get<IDataResponse<IKeKhaiV2Response>>(`/ke-khai-v2/${id}`);
  return res.data.data;
}

async function getMyKeKhai(
  params: IListMyKeKhaiV2Params = {}
): Promise<IPaginatedResponse<IKeKhaiV2Response>> {
  const search = new URLSearchParams();
  if (params.thang) search.append('thang', String(params.thang));
  if (params.nam) search.append('nam', String(params.nam));
  if (params.trang_thai) search.append('trang_thai', params.trang_thai);
  if (params.page) search.append('page', String(params.page));
  if (params.page_size) search.append('page_size', String(params.page_size));

  const res = await apiClient.get<IPaginatedResponse<IKeKhaiV2Response>>(
    `/ke-khai-v2/me?${search.toString()}`
  );
  return res.data;
}

/**
 * Lấy TẤT CẢ kê khai V2 trong tháng — loop qua các trang để lấy đầy đủ
 * (BE giới hạn page_size ≤ 100). Tránh việc CC kê >100 bản bị mất.
 */
async function getAllKeKhaiByMonth(
  thang: number,
  nam: number
): Promise<IKeKhaiV2Response[]> {
  const all: IKeKhaiV2Response[] = [];
  let page = 1;
  // Safety cap 50 trang × 100 = 5000 bản — đủ dùng.
  while (page <= 50) {
    const res = await getMyKeKhai({ thang, nam, page, page_size: 100 });
    all.push(...res.data);
    const totalPages = res.pagination?.total_pages ?? 1;
    if (page >= totalPages) break;
    page++;
  }
  return all;
}

async function createMultiDay(
  data: IKeKhaiV2MultiDayRequest
): Promise<IKeKhaiV2MultiDayResponse> {
  const res = await apiClient.post<IDataResponse<IKeKhaiV2MultiDayResponse>>(
    '/ke-khai-v2/nhieu-ngay',
    data
  );
  return res.data.data;
}

async function getThongKeThang(thang: number, nam: number): Promise<IThongKeKeKhaiThangV2> {
  const res = await apiClient.get<IDataResponse<IThongKeKeKhaiThangV2>>(
    `/ke-khai-v2/thong-ke/thang?thang=${thang}&nam=${nam}`
  );
  return res.data.data;
}

// =============================================================================
// FAVORITES + RECENT (30/04/2026)
// =============================================================================

async function getFavorites(): Promise<IFavoriteItem[]> {
  const res = await apiClient.get<IDataResponse<IFavoriteItem[]>>(
    '/ke-khai-v2/favorites'
  );
  return res.data.data;
}

async function addFavorite(danhMucSpId: string): Promise<IFavoriteItem> {
  const res = await apiClient.post<IDataResponse<IFavoriteItem>>(
    '/ke-khai-v2/favorites',
    { danh_muc_sp_id: danhMucSpId }
  );
  return res.data.data;
}

async function removeFavorite(danhMucSpId: string): Promise<void> {
  await apiClient.delete(`/ke-khai-v2/favorites/${danhMucSpId}`);
}

async function getRecent(thang: number, nam: number): Promise<IRecentItem[]> {
  const res = await apiClient.get<IDataResponse<IRecentItem[]>>(
    `/ke-khai-v2/recent?thang=${thang}&nam=${nam}`
  );
  return res.data.data;
}

// =============================================================================
// EXPORT
// =============================================================================

export const kpiV2Service = {
  getLinhVuc,
  searchDanhMucPL3,
  createKeKhai,
  updateKeKhai,
  deleteKeKhai,
  getKeKhaiDetail,
  getMyKeKhai,
  getAllKeKhaiByMonth,
  createMultiDay,
  getThongKeThang,
  getFavorites,
  addFavorite,
  removeFavorite,
  getRecent,
};
