/**
 * src/services/truc-ban.ts
 * ========================
 * Lịch trực ban — dùng chung backend HKG (port 8006), prefix
 * `/api/v1/hop-khong-giay/truc-ban`.
 *
 * Tách khỏi `lich-cong-tac.ts` vì đây là nghiệp vụ riêng: dữ liệu do các đơn
 * vị tự nhập rồi nộp, không phải lịch do Văn phòng xếp.
 */

import axios, { type AxiosInstance } from 'axios';

import type {
  IDongNhapExcel,
  INguoiGoiYTruc,
  IKetQuaXemTruoc,
  IMaTranTruc,
  INguoiTruc,
  ITrucBanGhi,
  ITruSo,
} from '@/types/lich-cong-tac';

const API_URL =
  process.env.NEXT_PUBLIC_HKG_API_URL || '/api/v1/hop-khong-giay';

const TOKEN_KEY = 'kpi_access_token';

const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/truc-ban`,
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
}

async function unwrap<T>(p: Promise<{ data: ApiResponse<T> }>): Promise<T> {
  return (await p).data.data;
}

export type Tuan = 'truoc' | 'nay' | 'sau';

export interface ITrucBanParams {
  'tu-ngay'?: string;
  'den-ngay'?: string;
  tuan?: Tuan;
  'don-vi-id'?: string;
  'tru-so-id'?: string;
  /** Mặc định true — bỏ ngày trong tuần trống khỏi bảng. */
  'chi-cuoi-tuan'?: boolean;
}

/** Tải một Blob về máy, dùng chung cho xuất Excel và tải file mẫu. */
async function taiVe(duong_dan: string, ten_du_phong: string,
                     params?: ITrucBanParams) {
  const resp = await api.get(duong_dan, { params, responseType: 'blob' });
  const cd = resp.headers['content-disposition'];
  const m = typeof cd === 'string' ? /filename="?([^";]+)"?/.exec(cd) : null;
  const url = URL.createObjectURL(resp.data as Blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = m ? m[1] : ten_du_phong;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export const trucBanApi = {
  truSo: () => unwrap<ITruSo[]>(api.get('/tru-so')),

  /** Công chức thuộc đơn vị giữ trụ sở này — để chọn thay vì gõ tay. */
  nguoiGoiY: (truSoId: string, tuKhoa?: string) =>
    unwrap<INguoiGoiYTruc[]>(
      api.get(`/nguoi-goi-y/${truSoId}`, { params: { 'tu-khoa': tuKhoa } })),

  maTran: (params?: ITrucBanParams) =>
    unwrap<IMaTranTruc>(api.get('/ma-tran', { params })),

  danhSach: (params?: ITrucBanParams) =>
    unwrap<Record<string, unknown>[]>(api.get('/danh-sach', { params })),

  vanBan: (params?: ITrucBanParams) =>
    unwrap<{ van_ban: string }>(api.get('/van-ban', { params })),

  them: (du_lieu: ITrucBanGhi) =>
    unwrap<INguoiTruc>(api.post('/', du_lieu)),

  sua: (id: string, thay_doi: ITrucBanGhi) =>
    unwrap<INguoiTruc>(api.patch(`/${id}`, thay_doi)),

  xoa: (id: string) => api.delete(`/${id}`),

  /** Nộp chính thức một ô — sau đó ô bị khoá. */
  nop: (ngay_truc: string, tru_so_id: string) =>
    unwrap<{ is_locked: boolean }>(api.post('/nop', { ngay_truc, tru_so_id })),

  moKhoa: (ngay_truc: string, tru_so_id: string) =>
    unwrap<{ is_locked: boolean }>(
      api.post('/mo-khoa', { ngay_truc, tru_so_id })),

  xuatExcel: (params?: ITrucBanParams) =>
    taiVe('/xuat-excel', 'truc-ban.xlsx', params),

  taiFileMau: () => taiVe('/mau-import', 'Mau_import_lich_truc_ban.xlsx'),

  /** Bước 1: đọc file và kiểm tra. KHÔNG ghi gì vào cơ sở dữ liệu. */
  xemTruoc: (file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    return unwrap<IKetQuaXemTruoc>(
      api.post('/nhap/xem-truoc', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }),
    );
  },

  /** Bước 2: ghi những dòng đã xem trước. */
  ghiNhap: (dong: IDongNhapExcel[], ghi_de: boolean) =>
    unwrap<{ da_ghi: number; so_o: number }>(
      api.post('/nhap/ghi', { dong, ghi_de })),
};

export default trucBanApi;
