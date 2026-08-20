/**
 * src/services/danh-gia-chuan-bi.ts
 * =================================
 * Chấm sao công tác chuẩn bị cuộc họp — G5.3. Backend HKG (port 8006),
 * prefix `/api/v1/hop-khong-giay/danh-gia-chuan-bi`.
 */

import axios, { type AxiosInstance } from 'axios';

import type {
  IDanhGiaChuanBi,
  ITongHopChuanBi,
} from '@/types/lich-cong-tac';

const API_URL =
  process.env.NEXT_PUBLIC_HKG_API_URL || '/api/v1/hop-khong-giay';

const TOKEN_KEY = 'kpi_access_token';

const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/danh-gia-chuan-bi`,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

interface ApiResponse<T> {
  success: boolean;
  data: T;
}

async function unwrap<T>(p: Promise<{ data: ApiResponse<T> }>): Promise<T> {
  return (await p).data.data;
}

export const danhGiaChuanBiApi = {
  quyen: () =>
    unwrap<{ duoc_cham: boolean }>(api.get('/quyen')).then((d) => d.duoc_cham),

  cuaCuocHop: (cuocHopId: string) =>
    unwrap<IDanhGiaChuanBi>(api.get(`/${cuocHopId}`)),

  cham: (cuocHopId: string, diem: number, ghi_chu?: string | null) =>
    unwrap<IDanhGiaChuanBi>(api.put(`/${cuocHopId}`, { diem, ghi_chu })),

  boCham: (cuocHopId: string) =>
    unwrap<IDanhGiaChuanBi>(api.delete(`/${cuocHopId}`)),

  tongHop: (params?: { 'tu-ngay'?: string; 'den-ngay'?: string }) =>
    unwrap<ITongHopChuanBi>(api.get('/tong-hop', { params })),
};

export default danhGiaChuanBiApi;
