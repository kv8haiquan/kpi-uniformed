/**
 * src/services/common.ts
 * =======================
 * Service cho module Common (Thông báo, Tìm kiếm, Knowledge Base).
 * Dùng axios instance qua Next.js rewrite → Common backend (port 8005).
 * Token lấy chung từ localStorage (SSO với KPI).
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
  process.env.NEXT_PUBLIC_COMMON_API_URL || '/api/common/v1';
const TOKEN_KEY = 'kpi_access_token';

const commonAxios: AxiosInstance = axios.create({
  baseURL: COMMON_API_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Interceptor: gắn JWT token từ localStorage (chung với KPI)
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
// THÔNG BÁO
// =============================================================================

export const thongBaoApi = {
  /** Danh sách thông báo — GET /thong-bao */
  danhSach: (params?: IThongBaoParams) =>
    commonAxios.get('/thong-bao', { params }),

  /** Đếm thông báo chưa đọc — GET /thong-bao/count */
  demChuaDoc: () =>
    commonAxios.get('/thong-bao/count'),

  /** Đánh dấu đã đọc 1 thông báo — PATCH /thong-bao/{id}/doc */
  danhDauDaDoc: (id: string) =>
    commonAxios.patch(`/thong-bao/${id}/doc`),

  /** Đánh dấu tất cả đã đọc — PATCH /thong-bao/doc-tat-ca */
  danhDauTatCaDaDoc: () =>
    commonAxios.patch('/thong-bao/doc-tat-ca'),
};

// =============================================================================
// TÌM KIẾM
// =============================================================================

export const searchApi = {
  /** Tìm kiếm hợp nhất — GET /search */
  timKiem: (params: ISearchParams) =>
    commonAxios.get('/search', { params }),

  /** Gợi ý từ khóa — GET /search/suggest */
  goiY: (q: string) =>
    commonAxios.get('/search/suggest', { params: { q } }),
};

// =============================================================================
// KNOWLEDGE BASE
// =============================================================================

export const knowledgeBaseApi = {
  /** Danh sách KB — GET /knowledge-base */
  danhSach: (params?: IKBParams) =>
    commonAxios.get('/knowledge-base', { params }),

  /** Chi tiết KB — GET /knowledge-base/{id} */
  chiTiet: (id: string) =>
    commonAxios.get(`/knowledge-base/${id}`),

  /** Tạo mới KB — POST /knowledge-base */
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

  /** Cập nhật KB — PUT /knowledge-base/{id} */
  capNhat: (id: string, data: {
    tieu_de?: string;
    noi_dung?: string;
    chuyen_de?: string[];
    tags?: string[];
    van_ban_lien_quan?: string[];
    chu_de_forum_lien_quan?: string[];
  }) =>
    commonAxios.put(`/knowledge-base/${id}`, data),

  /** Đổi trạng thái — PATCH /knowledge-base/{id}/trang-thai */
  doiTrangThai: (id: string, trang_thai_moi: string) =>
    commonAxios.patch(`/knowledge-base/${id}/trang-thai`, { trang_thai_moi }),

  /** Xóa KB — DELETE /knowledge-base/{id} */
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
