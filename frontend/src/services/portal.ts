/**
 * src/services/portal.ts
 * ======================
 * Service cho module Portal (Tin tức CMS + Thư viện tài liệu).
 * Dùng axios instance riêng trỏ đến Portal backend (port 8004).
 * Token lấy chung từ localStorage (SSO với KPI).
 */

import axios, { AxiosInstance } from 'axios';
import type {
  IBaiVietParams,
  IBaiVietCreate,
  IBaiVietUpdate,
  IDoiTrangThaiRequest,
  IChuyenMucCreate,
  IChuyenMucUpdate,
} from '@/types/tin-tuc';
import type {
  ITaiLieuParams,
  ITaiLieuCreate,
  ITaiLieuUpdate,
  IThuMucCreate,
  IThuMucUpdate,
  IUploadPhienBanMoiRequest,
} from '@/types/tai-lieu';

// =============================================================================
// AXIOS INSTANCE
// =============================================================================

const PORTAL_API_URL =
  process.env.NEXT_PUBLIC_PORTAL_API_URL || 'http://localhost:8004/api/v1';
const TOKEN_KEY = 'kpi_access_token';

const portalAxios: AxiosInstance = axios.create({
  baseURL: PORTAL_API_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Interceptor: gắn JWT token từ localStorage (chung với KPI)
portalAxios.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// =============================================================================
// CHUYÊN MỤC
// =============================================================================

export const chuyenMucApi = {
  /** Lấy danh sách chuyên mục — GET /chuyen-muc */
  danhSach: () =>
    portalAxios.get('/chuyen-muc'),
  /** Tạo chuyên mục — POST /chuyen-muc (QT_NOI_DUNG, ADMIN) */
  taoMoi: (data: IChuyenMucCreate) =>
    portalAxios.post('/chuyen-muc', data),
  /** Cập nhật chuyên mục — PUT /chuyen-muc/{id} */
  capNhat: (id: string, data: IChuyenMucUpdate) =>
    portalAxios.put(`/chuyen-muc/${id}`, data),
  /** Xóa chuyên mục — DELETE /chuyen-muc/{id} */
  xoa: (id: string) =>
    portalAxios.delete(`/chuyen-muc/${id}`),
};

// =============================================================================
// BÀI VIẾT
// =============================================================================

export const baiVietApi = {
  /** Danh sách bài viết công khai (XUAT_BAN) — GET /bai-viet */
  danhSach: (params?: IBaiVietParams) =>
    portalAxios.get('/bai-viet', { params }),
  /** Danh sách quản lý (tất cả trạng thái) — GET /bai-viet/quan-ly */
  quanLy: (params?: IBaiVietParams) =>
    portalAxios.get('/bai-viet/quan-ly', { params }),
  /** Chi tiết bài viết — GET /bai-viet/{id} */
  chiTiet: (id: string) =>
    portalAxios.get(`/bai-viet/${id}`),
  /** Tạo bài viết mới — POST /bai-viet (BIEN_TAP, QT_NOI_DUNG, ADMIN) */
  taoMoi: (data: IBaiVietCreate) =>
    portalAxios.post('/bai-viet', data),
  /** Cập nhật bài viết — PUT /bai-viet/{id} */
  capNhat: (id: string, data: IBaiVietUpdate) =>
    portalAxios.put(`/bai-viet/${id}`, data),
  /** Xóa bài viết — DELETE /bai-viet/{id} */
  xoa: (id: string) =>
    portalAxios.delete(`/bai-viet/${id}`),
  /** Đổi trạng thái workflow — PATCH /bai-viet/{id}/trang-thai */
  doiTrangThai: (id: string, data: IDoiTrangThaiRequest) =>
    portalAxios.patch(`/bai-viet/${id}/trang-thai`, data),
  /** Ghim / bỏ ghim bài viết — PATCH /bai-viet/{id}/ghim */
  doiGhim: (id: string, is_ghim: boolean) =>
    portalAxios.patch(`/bai-viet/${id}/ghim`, { is_ghim }),
};

// =============================================================================
// THƯ MỤC
// =============================================================================

export const thuMucApi = {
  /** Danh sách thư mục — GET /thu-muc */
  danhSach: () =>
    portalAxios.get('/thu-muc'),
  /** Cây thư mục — GET /thu-muc/tree */
  tree: () =>
    portalAxios.get('/thu-muc/tree'),
  /** Tạo thư mục — POST /thu-muc (QT_NOI_DUNG, ADMIN) */
  taoMoi: (data: IThuMucCreate) =>
    portalAxios.post('/thu-muc', data),
  /** Cập nhật thư mục — PUT /thu-muc/{id} */
  capNhat: (id: string, data: IThuMucUpdate) =>
    portalAxios.put(`/thu-muc/${id}`, data),
  /** Xóa thư mục — DELETE /thu-muc/{id} */
  xoa: (id: string) =>
    portalAxios.delete(`/thu-muc/${id}`),
};

// =============================================================================
// TÀI LIỆU
// =============================================================================

export const taiLieuApi = {
  /** Danh sách tài liệu (latest version only) — GET /tai-lieu */
  danhSach: (params?: ITaiLieuParams) =>
    portalAxios.get('/tai-lieu', { params }),
  /** Chi tiết tài liệu — GET /tai-lieu/{id} */
  chiTiet: (id: string) =>
    portalAxios.get(`/tai-lieu/${id}`),
  /** Tạo tài liệu mới — POST /tai-lieu */
  taoMoi: (data: ITaiLieuCreate) =>
    portalAxios.post('/tai-lieu', data),
  /** Cập nhật tài liệu — PUT /tai-lieu/{id} */
  capNhat: (id: string, data: ITaiLieuUpdate) =>
    portalAxios.put(`/tai-lieu/${id}`, data),
  /** Xóa tài liệu — DELETE /tai-lieu/{id} */
  xoa: (id: string) =>
    portalAxios.delete(`/tai-lieu/${id}`),
  /** Upload phiên bản mới — POST /tai-lieu/{id}/phien-ban-moi */
  taiPhienBanMoi: (id: string, data: IUploadPhienBanMoiRequest) =>
    portalAxios.post(`/tai-lieu/${id}/phien-ban-moi`, data),
  /** Lịch sử phiên bản — GET /tai-lieu/{id}/lich-su */
  lichSu: (id: string) =>
    portalAxios.get(`/tai-lieu/${id}/lich-su`),
  /** URL download (redirect) */
  downloadUrl: (id: string) =>
    `${PORTAL_API_URL}/tai-lieu/${id}/download`,
};

// =============================================================================
// DASHBOARD
// =============================================================================

export const portalDashboardApi = {
  /** Tóm tắt dashboard — GET /dashboard/summary */
  summary: () =>
    portalAxios.get('/dashboard/summary'),
  /** Dashboard lãnh đạo — GET /dashboard/lanh-dao */
  lanhDao: (thang?: number, nam?: number) =>
    portalAxios.get('/dashboard/lanh-dao', { params: { thang, nam } }),
};

// =============================================================================
// DEFAULT EXPORT (backward compat)
// =============================================================================

const portalService = {
  chuyenMucApi,
  baiVietApi,
  thuMucApi,
  taiLieuApi,
  portalDashboardApi,
};

export default portalService;
