/**
 * src/services/common.ts
 * =======================
 * Service cho module Common (Thong bao, Tim kiem, Knowledge Base).
 * Dung axios instance rieng tro den Common backend (port 8005).
 * Token lay chung tu localStorage (SSO voi KPI).
 */

import axios, { AxiosInstance } from 'axios';
import type {
  IThongBaoParams,
  ISearchParams,
  IKBParams,
} from '@/types/common';

// =============================================================================
// AXIOS INSTANCE
// =============================================================================

const COMMON_API_URL =
  process.env.NEXT_PUBLIC_COMMON_API_URL || 'http://localhost:8005/api/common/v1';
const TOKEN_KEY = 'kpi_access_token';

const commonAxios: AxiosInstance = axios.create({
  baseURL: COMMON_API_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Interceptor: gan JWT token tu localStorage (chung voi KPI)
commonAxios.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// =============================================================================
// THONG BAO
// =============================================================================

export const thongBaoApi = {
  /** Danh sach thong bao — GET /thong-bao */
  danhSach: (params?: IThongBaoParams) =>
    commonAxios.get('/thong-bao', { params }),

  /** Dem thong bao chua doc — GET /thong-bao/count */
  demChuaDoc: () =>
    commonAxios.get('/thong-bao/count'),

  /** Danh dau da doc 1 thong bao — PATCH /thong-bao/{id}/read */
  danhDauDaDoc: (id: string) =>
    commonAxios.patch(`/thong-bao/${id}/read`),

  /** Danh dau tat ca da doc — PATCH /thong-bao/read-all */
  danhDauTatCaDaDoc: () =>
    commonAxios.patch('/thong-bao/read-all'),
};

// =============================================================================
// TIM KIEM
// =============================================================================

export const searchApi = {
  /** Tim kiem hop nhat — GET /search */
  timKiem: (params: ISearchParams) =>
    commonAxios.get('/search', { params }),

  /** Goi y tu khoa — GET /search/suggest */
  goiY: (q: string) =>
    commonAxios.get('/search/suggest', { params: { q } }),
};

// =============================================================================
// KNOWLEDGE BASE
// =============================================================================

export const knowledgeBaseApi = {
  /** Danh sach KB — GET /knowledge-base */
  danhSach: (params?: IKBParams) =>
    commonAxios.get('/knowledge-base', { params }),

  /** Chi tiet KB — GET /knowledge-base/{id} */
  chiTiet: (id: string) =>
    commonAxios.get(`/knowledge-base/${id}`),

  /** Tao moi KB — POST /knowledge-base */
  taoMoi: (data: {
    loai: string;
    tieu_de: string;
    noi_dung: string;
    chuyen_de?: string[];
    tags?: string[];
    van_ban_lien_quan?: string[];
    chu_de_forum_lien_quan?: string[];
  }) =>
    commonAxios.post('/knowledge-base', data),

  /** Cap nhat KB — PUT /knowledge-base/{id} */
  capNhat: (id: string, data: {
    tieu_de?: string;
    noi_dung?: string;
    chuyen_de?: string[];
    tags?: string[];
    van_ban_lien_quan?: string[];
    chu_de_forum_lien_quan?: string[];
  }) =>
    commonAxios.put(`/knowledge-base/${id}`, data),

  /** Doi trang thai — PATCH /knowledge-base/{id}/trang-thai */
  doiTrangThai: (id: string, trang_thai_moi: string) =>
    commonAxios.patch(`/knowledge-base/${id}/trang-thai`, { trang_thai_moi }),

  /** Xoa KB — DELETE /knowledge-base/{id} */
  xoa: (id: string) =>
    commonAxios.delete(`/knowledge-base/${id}`),
};

// =============================================================================
// DEFAULT EXPORT
// =============================================================================

const commonService = {
  thongBaoApi,
  searchApi,
  knowledgeBaseApi,
};

export default commonService;
