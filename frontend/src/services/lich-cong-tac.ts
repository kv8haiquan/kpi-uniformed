/**
 * src/services/lich-cong-tac.ts
 * =============================
 * Service module Lịch công tác — dùng chung backend HKG (port 8006), prefix
 * `/api/v1/hop-khong-giay/lich-cong-tac`.
 *
 * Đi chung backend vì lịch công tác và cuộc họp nằm trên cùng một bảng —
 * xem docs/lich-cong-tac/KE_HOACH_TRIEN_KHAI.md §0.
 */

import axios, { type AxiosInstance } from 'axios';

import type {
  IDanhMucLoai,
  ILichLanhDao,
  ILichThang,
  ISuKienChiTiet,
  ISuKienLich,
  IThongKeLich,
  ITomTatLich,
  LoaiLich,
  TrangThaiLich,
} from '@/types/lich-cong-tac';

const API_URL =
  process.env.NEXT_PUBLIC_HKG_API_URL || '/api/v1/hop-khong-giay';

const TOKEN_KEY = 'kpi_access_token';

const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/lich-cong-tac`,
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
  pagination?: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
  };
}

async function unwrap<T>(p: Promise<{ data: ApiResponse<T> }>): Promise<T> {
  return (await p).data.data;
}

export interface ILichParams {
  'tu-ngay'?: string;
  'den-ngay'?: string;
  'loai-lich'?: LoaiLich;
  'trang-thai'?: TrangThaiLich;
  'lanh-dao-id'?: string;
  'tim-kiem'?: string;
  nguon?: string;
  trang?: number;
  'so-dong'?: number;
}

export const lichCongTacApi = {
  /** Danh sách có phân trang — trả nguyên response để lấy được `pagination`. */
  danhSach: (params?: ILichParams) =>
    api.get<ApiResponse<ISuKienLich[]>>('/', { params }),

  /** Lịch tháng, backend đã gom sẵn theo ngày. */
  theoThang: (
    nam: number,
    thang: number,
    params?: { 'loai-lich'?: LoaiLich; 'lanh-dao-id'?: string },
  ) => unwrap<ILichThang>(api.get(`/thang/${nam}/${thang}`, { params })),

  chiTiet: (id: string) => unwrap<ISuKienChiTiet>(api.get(`/${id}`)),

  /** Mặc định 3 ngày — giữ đúng cấu hình của lichkv8. */
  tomTat: (params?: {
    'tu-ngay'?: string;
    'so-ngay'?: number;
    'chi-da-dang'?: boolean;
    'kem-truc-ban'?: boolean;
  }) => unwrap<ITomTatLich>(api.get('/tom-tat', { params })),

  lichLanhDao: (
    lanhDaoId: string,
    params?: { 'tu-ngay'?: string; 'so-ngay'?: number },
  ) => unwrap<ILichLanhDao>(api.get(`/lanh-dao/${lanhDaoId}`, { params })),

  thongKe: () => unwrap<IThongKeLich>(api.get('/thong-ke')),

  danhMuc: () => unwrap<IDanhMucLoai[]>(api.get('/danh-muc')),
};

export default lichCongTacApi;
