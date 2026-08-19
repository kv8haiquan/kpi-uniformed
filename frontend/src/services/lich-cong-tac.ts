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
  IBaoCaoTaiLieu,
  IDanhMucLoai,
  IDanhMucTinhTrang,
  IDongNhatKy,
  ILichCongTacGhi,
  ILichLanhDao,
  ILichThang,
  ISuKienChiTiet,
  ISuKienLich,
  IQuyenLich,
  IThongKeLich,
  ITomTatLich,
  LoaiLich,
  TinhTrangTaiLieu,
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

  // ── quản lý lịch (G4.3) ────────────────────────────────────────────

  /** Quyền của người đang đăng nhập — để biết có hiện nút Sửa/Xoá không. */
  quyenCuaToi: () => unwrap<IQuyenLich>(api.get('/quyen/cua-toi')),

  tao: (du_lieu: ILichCongTacGhi) =>
    unwrap<ISuKienChiTiet>(api.post('/', du_lieu)),

  capNhat: (id: string, thay_doi: ILichCongTacGhi) =>
    unwrap<ISuKienChiTiet>(api.patch(`/${id}`, thay_doi)),

  /** Huỷ giữ lại bản ghi kèm lý do — khác hẳn xoá. */
  huy: (id: string, ly_do_huy: string) =>
    unwrap<ISuKienChiTiet>(api.post(`/${id}/huy`, { ly_do_huy })),

  xoa: (id: string) => api.delete(`/${id}`),

  nhatKy: (id: string) => unwrap<IDongNhatKy[]>(api.get(`/${id}/nhat-ky`)),

  xuatExcel: async (params?: ILichParams) => {
    const resp = await api.get('/xuat-excel', {
      params,
      responseType: 'blob',
      timeout: 60000,
    });
    const url = URL.createObjectURL(resp.data as Blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = layTenFile(resp.headers['content-disposition'],
                            'lich-cong-tac.xlsx');
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};

// ─── Thống kê tài liệu họp (G4.6) ───────────────────────────────────────
// Báo cáo nằm ở prefix riêng `/thong-ke-tai-lieu`, không phải dưới
// `/lich-cong-tac`, nên cần một instance axios khác baseURL.

const apiTaiLieu: AxiosInstance = axios.create({
  baseURL: `${API_URL}/thong-ke-tai-lieu`,
  timeout: 60000, // xuất Excel 2000 dòng chậm hơn API thường
  headers: { 'Content-Type': 'application/json' },
});

apiTaiLieu.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export interface IThongKeTaiLieuParams {
  'tu-ngay'?: string;
  'den-ngay'?: string;
  'tu-khoa'?: string;
  'lanh-dao-id'?: string;
  'trang-thai-lich'?: string;
  'tinh-trang'?: TinhTrangTaiLieu;
  'tinh-lich-huy'?: boolean;
  'gioi-han'?: number;
}

export const thongKeTaiLieuApi = {
  baoCao: (params?: IThongKeTaiLieuParams) =>
    unwrap<IBaoCaoTaiLieu>(apiTaiLieu.get('/', { params })),

  danhMucTinhTrang: () =>
    unwrap<IDanhMucTinhTrang[]>(apiTaiLieu.get('/tinh-trang')),

  /**
   * Tải file Excel về máy.
   *
   * Backend trả thẳng bytes chứ không bọc JSON, nên phải xin `blob` và tự tạo
   * link tải — không dùng được `unwrap`.
   */
  xuatExcel: async (params?: IThongKeTaiLieuParams) => {
    const resp = await apiTaiLieu.get('/xuat-excel', {
      params,
      responseType: 'blob',
    });
    const url = URL.createObjectURL(resp.data as Blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = layTenFile(resp.headers['content-disposition'],
                            'thong-ke-tai-lieu-hop.xlsx');
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};

/** Lấy tên file từ `Content-Disposition`, có tên dự phòng khi thiếu. */
function layTenFile(cd: unknown, duPhong = 'bao-cao.xlsx'): string {
  if (typeof cd === 'string') {
    const m = /filename="?([^";]+)"?/.exec(cd);
    if (m) return m[1];
  }
  return duPhong;
}

export default lichCongTacApi;
