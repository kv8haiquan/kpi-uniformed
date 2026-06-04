/**
 * src/services/chi-tieu.ts
 * ========================
 * Service cho module Chỉ tiêu đơn vị.
 * Axios instance riêng trỏ backend port 8007 (qua nginx /api/v1/chi-tieu).
 * Token chung từ localStorage (SSO với KPI).
 */

import axios, { AxiosInstance } from 'axios';
import type {
  IChiTieuCreate, IGiaoNamCreate, ILinhVucCreate, LoaiChoDuyet,
} from '@/types/chi-tieu';

const CHI_TIEU_API_URL = process.env.NEXT_PUBLIC_CHI_TIEU_API_URL || '/api/v1/chi-tieu';
const TOKEN_KEY = 'kpi_access_token';

const chiTieuApi: AxiosInstance = axios.create({
  baseURL: CHI_TIEU_API_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

chiTieuApi.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// =============================================================================
// LĨNH VỰC
// =============================================================================
export const linhVucApi = {
  danhSach: () => chiTieuApi.get('/linh-vuc', { params: { page_size: 200 } }),
  taoMoi: (data: ILinhVucCreate) => chiTieuApi.post('/linh-vuc', data),
  capNhat: (id: string, data: Partial<ILinhVucCreate>) => chiTieuApi.put(`/linh-vuc/${id}`, data),
  xoa: (id: string) => chiTieuApi.delete(`/linh-vuc/${id}`),
};

// =============================================================================
// DANH MỤC CHỈ TIÊU
// =============================================================================
export const danhMucApi = {
  danhSach: (params?: { linh_vuc_id?: string; is_active?: boolean }) =>
    chiTieuApi.get('/danh-muc', { params: { page_size: 200, ...params } }),
  taoMoi: (data: IChiTieuCreate) => chiTieuApi.post('/danh-muc', data),
  capNhat: (id: string, data: Partial<IChiTieuCreate>) => chiTieuApi.put(`/danh-muc/${id}`, data),
  xoa: (id: string) => chiTieuApi.delete(`/danh-muc/${id}`),
};

// =============================================================================
// GIAO NĂM
// =============================================================================
export const giaoNamApi = {
  danhSach: (params: { nam: number; don_vi_id?: string }) =>
    chiTieuApi.get('/giao-nam', { params: { page_size: 500, ...params } }),
  taoMoi: (data: IGiaoNamCreate) => chiTieuApi.post('/giao-nam', data),
  capNhat: (id: string, data: Partial<IGiaoNamCreate>) => chiTieuApi.put(`/giao-nam/${id}`, data),
  xoa: (id: string) => chiTieuApi.delete(`/giao-nam/${id}`),
};

// =============================================================================
// ĐĂNG KÝ & KẾT QUẢ (người theo dõi)
// =============================================================================
export const dangKyApi = {
  canDangKy: (params: { don_vi_id: string; thang: number; nam: number }) =>
    chiTieuApi.get('/dang-ky', { params }),
  taoMoi: (data: { don_vi_id: string; chi_tieu_id: string; thang: number; nam: number; khong_dang_ky?: boolean; gia_tri_dang_ky?: number | null }) =>
    chiTieuApi.post('/dang-ky', data),
  capNhat: (id: string, data: { khong_dang_ky?: boolean; gia_tri_dang_ky?: number | null }) =>
    chiTieuApi.put(`/dang-ky/${id}`, data),
  guiDuyet: (id: string) => chiTieuApi.post(`/dang-ky/${id}/gui-duyet`),
  yeuCauSua: (id: string, data: { gia_tri_dang_ky_moi: number; ly_do?: string }) =>
    chiTieuApi.post(`/dang-ky/${id}/yeu-cau-sua`, data),
  nhapKetQua: (id: string, data: { gia_tri_ket_qua: number; danh_gia_ghi_chu?: string }) =>
    chiTieuApi.post(`/dang-ky/${id}/nhap-ket-qua`, data),
  guiKetQua: (id: string) => chiTieuApi.post(`/dang-ky/${id}/gui-ket-qua`),
  moKhoa: (id: string) => chiTieuApi.post(`/dang-ky/${id}/mo-khoa`),
  lichSu: (id: string) => chiTieuApi.get(`/dang-ky/${id}/lich-su`),
};

// =============================================================================
// DUYỆT (Trưởng đơn vị)
// =============================================================================
export const duyetApi = {
  choXuLy: (params: { loai: LoaiChoDuyet; don_vi_id?: string }) =>
    chiTieuApi.get('/duyet/cho-xu-ly', { params }),
  duyet: (id: string) => chiTieuApi.post(`/duyet/${id}/duyet`),
  tuChoi: (id: string, ly_do_tu_choi: string) =>
    chiTieuApi.post(`/duyet/${id}/tu-choi`, { ly_do_tu_choi }),
};

// =============================================================================
// BÁO CÁO
// =============================================================================
export const baoCaoApi = {
  raSoat: (params: { thang: number; nam: number; linh_vuc_id?: string; don_vi_id?: string }) =>
    chiTieuApi.get('/bao-cao/ra-soat', { params }),
  luyKe: (params: { nam: number; don_vi_id?: string; thang?: number }) =>
    chiTieuApi.get('/bao-cao/luy-ke', { params }),
};

export default chiTieuApi;
