/**
 * src/services/lms.ts
 * ===================
 * Service cho module Đào tạo (LMS).
 * Dùng axios instance riêng trỏ đến LMS backend.
 * Token lấy chung từ localStorage (SSO với KPI).
 */

import axios, { AxiosInstance } from 'axios';
import type { IChuyenDeCreate, IChuyenDeUpdate, IBaiHocCreate, ICauHoiCreate, IBaiKiemTraCreate } from '@/types/lms';

// =============================================================================
// AXIOS INSTANCE cho LMS
// =============================================================================

const LMS_API_URL = process.env.NEXT_PUBLIC_LMS_API_URL || '/api/v1/lms';
const TOKEN_KEY = 'kpi_access_token';

const lmsApi: AxiosInstance = axios.create({
  baseURL: LMS_API_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Interceptor: gắn JWT token từ localStorage (chung với KPI)
lmsApi.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// =============================================================================
// CHUYÊN ĐỀ
// =============================================================================

export const chuyenDeApi = {
  /** Lấy danh sách chuyên đề — GET /chuyen-de */
  danhSach: (params?: { is_active?: boolean }) =>
    lmsApi.get('/chuyen-de', { params }),
  /** Chi tiết chuyên đề — GET /chuyen-de/{id} */
  chiTiet: (id: string) =>
    lmsApi.get(`/chuyen-de/${id}`),
  /** Tạo chuyên đề mới — POST /chuyen-de (QT_DAO_TAO, ADMIN) */
  taoMoi: (data: IChuyenDeCreate) =>
    lmsApi.post('/chuyen-de', data),
  /** Cập nhật chuyên đề — PUT /chuyen-de/{id} (QT_DAO_TAO, ADMIN) */
  capNhat: (id: string, data: IChuyenDeUpdate) =>
    lmsApi.put(`/chuyen-de/${id}`, data),
  /** Xóa chuyên đề (soft delete) — DELETE /chuyen-de/{id} (QT_DAO_TAO, ADMIN) */
  xoa: (id: string) =>
    lmsApi.delete(`/chuyen-de/${id}`),
};

// =============================================================================
// KHÓA HỌC
// =============================================================================

export const khoaHocApi = {
  danhSach: (params?: any) =>
    lmsApi.get('/khoa-hoc', { params }),
  quanLy: (params?: any) =>
    lmsApi.get('/khoa-hoc/quan-ly', { params }),
  chiTiet: (id: string) =>
    lmsApi.get(`/khoa-hoc/${id}`),
  taoMoi: (data: any) =>
    lmsApi.post('/khoa-hoc', data),
  capNhat: (id: string, data: any) =>
    lmsApi.put(`/khoa-hoc/${id}`, data),
  chuyenTrangThai: (id: string, data: { trang_thai: string; ghi_chu?: string }) =>
    lmsApi.patch(`/khoa-hoc/${id}/trang-thai`, data),
  xoa: (id: string) =>
    lmsApi.delete(`/khoa-hoc/${id}`),
};

// =============================================================================
// BÀI HỌC
// =============================================================================

export const baiHocApi = {
  /** Danh sách bài học theo khóa — GET /khoa-hoc/{id}/bai-hoc */
  danhSach: (khoaHocId: string) =>
    lmsApi.get(`/khoa-hoc/${khoaHocId}/bai-hoc`),
  /** Chi tiết bài học — GET /bai-hoc/{id} */
  chiTiet: (id: string) =>
    lmsApi.get(`/bai-hoc/${id}`),
  /** Tạo bài học — POST /khoa-hoc/{id}/bai-hoc (GIANG_VIEN, QT_DAO_TAO, ADMIN) */
  taoMoi: (khoaHocId: string, data: IBaiHocCreate) =>
    lmsApi.post(`/khoa-hoc/${khoaHocId}/bai-hoc`, data),
  /** Cập nhật bài học — PUT /bai-hoc/{id} (GIANG_VIEN, QT_DAO_TAO, ADMIN) */
  capNhat: (id: string, data: Partial<IBaiHocCreate>) =>
    lmsApi.put(`/bai-hoc/${id}`, data),
  /** Cập nhật tiến độ học viên — PATCH /bai-hoc/{id}/tien-do */
  capNhatTienDo: (id: string, data: { thoi_gian_xem_giay: number; hoan_thanh: boolean }) =>
    lmsApi.patch(`/bai-hoc/${id}/tien-do`, data),
  /** Sắp xếp thứ tự bài học — PATCH /khoa-hoc/{id}/bai-hoc/sap-xep */
  sapXep: (khoaHocId: string, data: { thu_tu: { bai_hoc_id: string; thu_tu: number }[] }) =>
    lmsApi.patch(`/khoa-hoc/${khoaHocId}/bai-hoc/sap-xep`, data),
  /** Xóa bài học — DELETE /bai-hoc/{id} (GIANG_VIEN, QT_DAO_TAO, ADMIN) */
  xoa: (id: string) =>
    lmsApi.delete(`/bai-hoc/${id}`),
};

// =============================================================================
// ĐĂNG KÝ
// =============================================================================

export const dangKyApi = {
  dangKy: (khoaHocId: string) =>
    lmsApi.post(`/khoa-hoc/${khoaHocId}/dang-ky`),
  giaoBai: (khoaHocId: string, data: any) =>
    lmsApi.post(`/khoa-hoc/${khoaHocId}/giao-bai`, data),
  cuaToi: (params?: any) =>
    lmsApi.get('/dang-ky/cua-toi', { params }),
  hocVien: (khoaHocId: string, params?: any) =>
    lmsApi.get(`/khoa-hoc/${khoaHocId}/hoc-vien`, { params }),
  huy: (khoaHocId: string) =>
    lmsApi.delete(`/khoa-hoc/${khoaHocId}/dang-ky`),
};

// =============================================================================
// CÂU HỎI (Ngân hàng câu hỏi)
// =============================================================================

export const cauHoiApi = {
  /** Danh sách câu hỏi — GET /cau-hoi (GIANG_VIEN, QT_DAO_TAO, ADMIN) */
  danhSach: (params?: {
    khoa_hoc_id?: string;
    bai_kiem_tra_id?: string;
    loai?: string;
    do_kho?: string;
    page?: number;
    page_size?: number;
  }) => lmsApi.get('/cau-hoi', { params }),
  /** Tạo câu hỏi — POST /cau-hoi */
  taoMoi: (data: ICauHoiCreate) =>
    lmsApi.post('/cau-hoi', data),
  /** Cập nhật câu hỏi — PUT /cau-hoi/{id} */
  capNhat: (id: string, data: Partial<ICauHoiCreate>) =>
    lmsApi.put(`/cau-hoi/${id}`, data),
  /** Xóa câu hỏi — DELETE /cau-hoi/{id} */
  xoa: (id: string) =>
    lmsApi.delete(`/cau-hoi/${id}`),
  /**
   * Import câu hỏi hàng loạt — POST /cau-hoi/import
   * @param file    File .xlsx hoặc .csv
   * @param params  { khoa_hoc_id?, bai_kiem_tra_id? } — tuỳ chọn
   */
  importFile: (file: File, params?: { khoa_hoc_id?: string; bai_kiem_tra_id?: string }) => {
    const fd = new FormData();
    fd.append('file', file);
    const qs = new URLSearchParams();
    if (params?.khoa_hoc_id) qs.set('khoa_hoc_id', params.khoa_hoc_id);
    if (params?.bai_kiem_tra_id) qs.set('bai_kiem_tra_id', params.bai_kiem_tra_id);
    const qsStr = qs.toString() ? `?${qs}` : '';
    return lmsApi.post(`/cau-hoi/import${qsStr}`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  /**
   * Download file Excel mẫu import — GET /cau-hoi/import/mau
   */
  downloadMauImport: () =>
    lmsApi.get('/cau-hoi/import/mau', { responseType: 'blob' }),
};

// =============================================================================
// BÀI KIỂM TRA
// =============================================================================

export const baiKiemTraApi = {
  /** Danh sách BKT theo khóa — GET /khoa-hoc/{id}/bai-kiem-tra */
  danhSach: (khoaHocId: string) =>
    lmsApi.get(`/khoa-hoc/${khoaHocId}/bai-kiem-tra`),
  chiTiet: (id: string) =>
    lmsApi.get(`/bai-kiem-tra/${id}`),
  /** Tạo bài kiểm tra — POST /khoa-hoc/{id}/bai-kiem-tra */
  taoMoi: (khoaHocId: string, data: IBaiKiemTraCreate) =>
    lmsApi.post(`/khoa-hoc/${khoaHocId}/bai-kiem-tra`, data),
  /** Cập nhật bài kiểm tra — PUT /bai-kiem-tra/{id} */
  capNhat: (id: string, data: Partial<IBaiKiemTraCreate>) =>
    lmsApi.put(`/bai-kiem-tra/${id}`, data),
  /** Xóa bài kiểm tra — DELETE /bai-kiem-tra/{id} */
  xoa: (id: string) =>
    lmsApi.delete(`/bai-kiem-tra/${id}`),
  batDau: (id: string) =>
    lmsApi.post(`/bai-kiem-tra/${id}/bat-dau`),
  nopBai: (id: string, data: any) =>
    lmsApi.post(`/bai-kiem-tra/${id}/nop-bai`, data),
  ketQua: (id: string) =>
    lmsApi.get(`/ket-qua/${id}`),
  /** Lịch sử làm bài của user cho 1 BKT — GET /bai-kiem-tra/{id}/ket-qua */
  lichSuThi: (id: string) =>
    lmsApi.get(`/bai-kiem-tra/${id}/ket-qua`),
  /** Danh sách câu hỏi của BKT (kèm đáp án, cho giảng viên) — GET /bai-kiem-tra/{id}/cau-hoi */
  danhSachCauHoi: (id: string) =>
    lmsApi.get(`/bai-kiem-tra/${id}/cau-hoi`),
};

// =============================================================================
// CHỨNG CHỈ & KHẢO SÁT
// =============================================================================

export const chungChiApi = {
  cuaToi: (params?: any) =>
    lmsApi.get('/chung-chi/cua-toi', { params }),
  xacMinh: (ma: string) =>
    lmsApi.get(`/chung-chi/xac-minh/${ma}`),
  tai: (id: string) =>
    lmsApi.get(`/chung-chi/${id}/tai`),
};

export const khaoSatApi = {
  /** Gửi khảo sát sau khi hoàn thành khóa — POST /khoa-hoc/{id}/khao-sat */
  guiKhaoSat: (khoaHocId: string, data: any) =>
    lmsApi.post(`/khoa-hoc/${khoaHocId}/khao-sat`, data),
  thongKe: (khoaHocId: string) =>
    lmsApi.get(`/khoa-hoc/${khoaHocId}/khao-sat/thong-ke`),
};

// =============================================================================
// BÁO CÁO & DASHBOARD
// =============================================================================

export const baoCaoApi = {
  caNhan: () =>
    lmsApi.get('/bao-cao/ca-nhan'),
  donVi: (donViId: string, params?: { thang?: number; nam?: number }) =>
    lmsApi.get(`/bao-cao/don-vi/${donViId}`, { params }),
  khoaHoc: (khoaHocId: string) =>
    lmsApi.get(`/bao-cao/khoa-hoc/${khoaHocId}`),
  dashboard: () =>
    lmsApi.get('/dashboard/summary'),
};

// =============================================================================
// UPLOAD FILE
// =============================================================================

export const uploadApi = {
  /**
   * Upload 1 file lên server — POST /upload/file
   * @param file        File object từ input
   * @param folder      Sub-folder: bai-hoc | anh-bia | tai-lieu | general
   * @param onProgress  Callback nhận % tiến trình (0–100)
   * Returns: { file_name, file_url, file_size, content_type }
   */
  uploadFile: (
    file: File,
    folder: string = 'bai-hoc',
    onProgress?: (pct: number) => void,
  ) => {
    const fd = new FormData();
    fd.append('file', file);
    return lmsApi.post(`/upload/file?folder=${encodeURIComponent(folder)}`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded * 100) / e.total));
        }
      },
    });
  },

  /**
   * Upload nhiều file — POST /upload/files
   */
  uploadFiles: (
    files: File[],
    folder: string = 'bai-hoc',
    onProgress?: (pct: number) => void,
  ) => {
    const fd = new FormData();
    files.forEach((f) => fd.append('files', f));
    return lmsApi.post(`/upload/files?folder=${encodeURIComponent(folder)}`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded * 100) / e.total));
        }
      },
    });
  },
};

// =============================================================================
// CBCC & ĐƠN VỊ (helper lookup)
// =============================================================================

export const cbccApi = {
  /**
   * Tìm kiếm CBCC theo tên hoặc mã số — GET /cbcc/search
   * Auth: GIANG_VIEN, QT_DAO_TAO, ADMIN, Lãnh đạo
   */
  searchCBCC: (params: { q: string; don_vi_id?: string; page_size?: number }) =>
    lmsApi.get('/cbcc/search', { params }),

  /**
   * Danh sách tất cả đơn vị — GET /don-vi
   * Auth: Tất cả CBCC
   */
  getDonVi: () =>
    lmsApi.get('/don-vi'),
};

export default lmsApi;
