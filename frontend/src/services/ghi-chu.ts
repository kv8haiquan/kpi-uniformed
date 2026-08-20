/**
 * src/services/ghi-chu.ts
 * =======================
 * Ghi chú cá nhân và chia sẻ — G5.2. Backend HKG (port 8006), prefix
 * `/api/v1/hop-khong-giay/ghi-chu`.
 *
 * File đính kèm dùng lại đường serve của tài liệu họp: backend trả sẵn URL
 * tuyệt đối trong `xemDinhKem` / `taiDinhKem` nên phía này không tự ghép.
 */

import axios, { type AxiosInstance } from 'axios';

import type {
  IDinhKemGhiChu,
  IGhiChuChiTiet,
  IGhiChuTomTat,
  INguoiNhanGhiChu,
  PhamViGhiChu,
} from '@/types/lich-cong-tac';

const API_URL =
  process.env.NEXT_PUBLIC_HKG_API_URL || '/api/v1/hop-khong-giay';

const TOKEN_KEY = 'kpi_access_token';

const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/ghi-chu`,
  timeout: 60000,
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

export interface IGhiChuParams {
  'pham-vi'?: PhamViGhiChu;
  'cuoc-hop-id'?: string;
  'tu-khoa'?: string;
  'chi-chua-doc'?: boolean;
  trang?: number;
  'so-dong'?: number;
}

export interface IGhiChuGhi {
  tieu_de?: string;
  noi_dung?: string | null;
  cuoc_hop_id?: string | null;
  is_ghim?: boolean;
}

export const ghiChuApi = {
  danhSach: (params?: IGhiChuParams) =>
    api.get<ApiResponse<IGhiChuTomTat[]>>('', { params }),

  chiTiet: (id: string) => unwrap<IGhiChuChiTiet>(api.get(`/${id}`)),

  soChuaDoc: () =>
    unwrap<{ so_chua_doc: number }>(api.get('/chua-doc')).then(
      (d) => d.so_chua_doc,
    ),

  nguoiNhan: (tuKhoa?: string) =>
    unwrap<INguoiNhanGhiChu[]>(
      api.get('/nguoi-nhan', { params: { 'tu-khoa': tuKhoa || undefined } }),
    ),

  tao: (du_lieu: IGhiChuGhi) =>
    unwrap<IGhiChuChiTiet>(api.post('', du_lieu)),

  capNhat: (id: string, thay_doi: IGhiChuGhi) =>
    unwrap<IGhiChuChiTiet>(api.patch(`/${id}`, thay_doi)),

  xoa: (id: string) => api.delete(`/${id}`),

  chiaSe: (id: string, nguoi_nhan_ids: string[], loi_nhan?: string) =>
    api.post(`/${id}/chia-se`, { nguoi_nhan_ids, loi_nhan: loi_nhan || null }),

  thuHoi: (id: string, chiaSeId: string) =>
    api.delete(`/${id}/chia-se/${chiaSeId}`),

  danhDauDaDoc: (id: string) => api.post(`/${id}/da-doc`),

  themDinhKem: (id: string, file: File, mo_ta?: string) => {
    const fd = new FormData();
    fd.append('file', file);
    if (mo_ta) fd.append('mo_ta', mo_ta);
    return unwrap<IDinhKemGhiChu>(
      api.post(`/${id}/tai-lieu`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }),
    );
  },

  xoaDinhKem: (taiLieuId: string) => api.delete(`/tai-lieu/${taiLieuId}`),

  /** URL xem trước — mở tab mới, hết hạn sau 1 giờ. */
  urlXem: (taiLieuId: string) =>
    unwrap<{ url: string }>(api.get(`/tai-lieu/${taiLieuId}/xem`)).then(
      (d) => d.url,
    ),

  urlTai: (taiLieuId: string) =>
    unwrap<{ url: string }>(api.get(`/tai-lieu/${taiLieuId}/tai`)).then(
      (d) => d.url,
    ),
};

export default ghiChuApi;
