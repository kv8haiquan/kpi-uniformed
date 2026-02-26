/**
 * src/services/forum.ts
 * =====================
 * Service cho module Dien dan (Forum).
 * Base URL tro den Forum backend (port 8002).
 *
 * Dung forumApi rieng voi baseURL = '' (trong).
 * Next.js rewrite: /api/forum/v1/* -> http://localhost:8002/api/forum/v1/*
 * Token lay tu localStorage (SSO chung voi KPI).
 */

import axios, {
  type AxiosInstance,
  type AxiosError,
  type InternalAxiosRequestConfig,
  type AxiosResponse,
} from 'axios';

import { getStoredToken, removeStoredToken } from '@/lib/axios';
import type { IApiErrorWrapper } from '@/types/api';
import type {
  IChuyenMuc,
  IChuyenMucCreate,
  IChuyenMucUpdate,
  IChuDeListItem,
  IChuDeDetail,
  IChuDeCreate,
  IChuDeUpdate,
  IChuDeQueryParams,
  IHanhDongChuDe,
  IChonDapAnChuan,
  ITraLoiCreate,
  ITraLoiUpdate,
  ITraLoiResponse,
  IBieuQuyetCreate,
  IBieuQuyetResponse,
  IDashboardSummary,
  IBaoCaoCaNhan,
  IBaoCaoDonVi,
  ITopContributor,
} from '@/types/forum';

// =============================================================================
// AXIOS INSTANCE RIENG CHO FORUM
// =============================================================================

const BASE = '/api/forum/v1';

const forumApi: AxiosInstance = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Request interceptor — gan JWT
forumApi.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getStoredToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error),
);

// Response interceptor — xu ly 401
forumApi.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError<IApiErrorWrapper>) => {
    if (error.response?.status === 401) {
      removeStoredToken();
      if (
        typeof window !== 'undefined' &&
        !window.location.pathname.includes('/login')
      ) {
        window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  },
);

// =============================================================================
// HELPER — extract data tu response
// =============================================================================

function extractData<T>(response: AxiosResponse): T {
  return response.data?.data;
}

// =============================================================================
// CHUYEN MUC API
// =============================================================================

export const chuyenMucApi = {
  danhSach: (is_active?: boolean) =>
    forumApi.get<{ success: boolean; data: IChuyenMuc[] }>(
      `${BASE}/chuyen-muc`,
      { params: { is_active } },
    ).then(r => r.data.data),

  taoMoi: (data: IChuyenMucCreate) =>
    forumApi.post(`${BASE}/chuyen-muc`, data).then(r => r.data.data as IChuyenMuc),

  capNhat: (id: string, data: IChuyenMucUpdate) =>
    forumApi.put(`${BASE}/chuyen-muc/${id}`, data).then(r => r.data.data as IChuyenMuc),

  xoa: (id: string) =>
    forumApi.delete(`${BASE}/chuyen-muc/${id}`),
};

// =============================================================================
// CHU DE API
// =============================================================================

export const chuDeApi = {
  danhSach: (params?: IChuDeQueryParams) =>
    forumApi.get(`${BASE}/chu-de`, { params }).then(r => ({
      items: r.data.data as IChuDeListItem[],
      pagination: r.data.pagination,
    })),

  chiTiet: (id: string) =>
    forumApi.get(`${BASE}/chu-de/${id}`).then(r => r.data.data as IChuDeDetail),

  taoMoi: (data: IChuDeCreate) =>
    forumApi.post(`${BASE}/chu-de`, data).then(r => r.data.data as IChuDeDetail),

  capNhat: (id: string, data: IChuDeUpdate) =>
    forumApi.put(`${BASE}/chu-de/${id}`, data).then(r => r.data.data as IChuDeDetail),

  xoa: (id: string) =>
    forumApi.delete(`${BASE}/chu-de/${id}`),

  hanhDong: (id: string, data: IHanhDongChuDe) =>
    forumApi.patch(`${BASE}/chu-de/${id}/hanh-dong`, data).then(r => r.data),

  chonDapAnChuan: (chuDeId: string, data: IChonDapAnChuan) =>
    forumApi.patch(`${BASE}/chu-de/${chuDeId}/dap-an-chuan`, data).then(r => r.data),
};

// =============================================================================
// TRA LOI API
// =============================================================================

export const traLoiApi = {
  taoMoi: (chuDeId: string, data: ITraLoiCreate) =>
    forumApi.post(`${BASE}/chu-de/${chuDeId}/tra-loi`, data)
      .then(r => r.data.data as ITraLoiResponse),

  capNhat: (id: string, data: ITraLoiUpdate) =>
    forumApi.put(`${BASE}/tra-loi/${id}`, data)
      .then(r => r.data.data as ITraLoiResponse),

  xoa: (id: string) =>
    forumApi.delete(`${BASE}/tra-loi/${id}`),

  an: (id: string) =>
    forumApi.patch(`${BASE}/tra-loi/${id}/an`),
};

// =============================================================================
// BIEU QUYET (VOTE) API
// =============================================================================

export const bieuQuyetApi = {
  vote: (data: IBieuQuyetCreate) =>
    forumApi.post(`${BASE}/bieu-quyet`, data)
      .then(r => r.data.data as IBieuQuyetResponse),

  xoaVote: (data: { doi_tuong_type: string; doi_tuong_id: string }) =>
    forumApi.delete(`${BASE}/bieu-quyet`, { data }),
};

// =============================================================================
// THEO DOI API
// =============================================================================

export const theoDoiApi = {
  theoDoi: (chuDeId: string) =>
    forumApi.post(`${BASE}/chu-de/${chuDeId}/theo-doi`).then(r => r.data),

  boTheoDoi: (chuDeId: string) =>
    forumApi.delete(`${BASE}/chu-de/${chuDeId}/theo-doi`).then(r => r.data),

  cuaToi: (params?: { page?: number; page_size?: number }) =>
    forumApi.get(`${BASE}/theo-doi/cua-toi`, { params }).then(r => ({
      items: r.data.data as IChuDeListItem[],
      pagination: r.data.pagination,
    })),
};

// =============================================================================
// TIM KIEM API
// =============================================================================

export const timKiemApi = {
  timKiem: (params: { q: string; chuyen_muc_id?: string; tags?: string; page?: number; page_size?: number }) =>
    forumApi.get(`${BASE}/tim-kiem`, { params }).then(r => ({
      items: r.data.data as IChuDeListItem[],
      pagination: r.data.pagination,
    })),

  goiYTag: (q: string) =>
    forumApi.get<{ success: boolean; data: string[] }>(
      `${BASE}/tags/goi-y`,
      { params: { q } },
    ).then(r => r.data.data),
};

// =============================================================================
// DASHBOARD / BAO CAO API
// =============================================================================

export const dashboardApi = {
  summary: () =>
    forumApi.get(`${BASE}/dashboard/summary`)
      .then(r => r.data.data as IDashboardSummary),

  baoCaoCaNhan: (thang: number, nam: number) =>
    forumApi.get(`${BASE}/bao-cao/ca-nhan`, { params: { thang, nam } })
      .then(r => r.data.data as IBaoCaoCaNhan),

  baoCaoDonVi: (donViId: string, thang: number, nam: number) =>
    forumApi.get(`${BASE}/bao-cao/don-vi/${donViId}`, { params: { thang, nam } })
      .then(r => r.data.data as IBaoCaoDonVi),

  topContributors: (params?: { thang?: number; nam?: number; limit?: number }) =>
    forumApi.get(`${BASE}/bao-cao/top`, { params })
      .then(r => r.data.data as ITopContributor[]),
};
