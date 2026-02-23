/**
 * src/services/legal.ts
 * =====================
 * Service cho module Pháp luật (Legal).
 *
 * ⚠️  QUAN TRỌNG — KHÔNG dùng api từ @/lib/axios.
 *     Instance đó có baseURL = '/api/v1' (của KPI), sẽ ghép thành
 *     /api/v1/api/legal/v1/... → sai.
 *
 * ✅  Dùng legalApi riêng với baseURL = '' (trống).
 *     Nginx proxy: /api/legal/ → Legal backend (port 8003).
 *     Token lấy từ localStorage (SSO chung với KPI).
 *
 * @see docs/legal/LEGAL_API_SPECS.md
 * @see nginx/default.conf  location /api/legal/
 */

import axios, {
  type AxiosInstance,
  type AxiosError,
  type InternalAxiosRequestConfig,
  type AxiosResponse,
} from 'axios';

// Import helper token từ @/lib/axios (KHÔNG import instance apiClient)
import { getStoredToken, removeStoredToken } from '@/lib/axios';
import type { IApiErrorWrapper } from '@/types/api';
import type {
  IVanBanCreate,
  IVanBanQueryParams,
  ICapNhatTrangThaiBody,
  IXacNhanDocBody,
  ITrackingDocBody,
  IQuizVanBanCreate,
  ILamQuizBody,
} from '@/types/legal';

// =============================================================================
// AXIOS INSTANCE RIÊNG CHO LEGAL
// =============================================================================

/**
 * Base path theo SHARED_CODING_STANDARDS §5.1.
 * Nginx: location /api/legal/ → proxy_pass http://127.0.0.1:8003/
 * Dùng absolute path — KHÔNG phụ thuộc baseURL của instance KPI.
 */
const BASE = '/api/legal/v1';

/**
 * Axios instance riêng cho Legal.
 * baseURL = '' → URL cuối = path tuyệt đối (/api/legal/v1/...).
 * Tránh bị ghép prefix /api/v1 của KPI.
 */
const legalApi: AxiosInstance = axios.create({
  baseURL: '', // ← KHÔNG có baseURL — dùng absolute path
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// =============================================================================
// REQUEST INTERCEPTOR — Gắn JWT token (SSO chung với KPI)
// =============================================================================

legalApi.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Lấy token từ localStorage (key chung với KPI: 'kpi_access_token')
    const token = getStoredToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Log request trong development
    if (process.env.NODE_ENV === 'development') {
      console.log(`🚀 [Legal API] ${config.method?.toUpperCase()} ${config.url}`);
    }

    return config;
  },
  (error: AxiosError) => {
    console.error('❌ [Legal API Request Error]', error.message);
    return Promise.reject(error);
  },
);

// =============================================================================
// RESPONSE INTERCEPTOR — Xử lý lỗi chuẩn (copy từ @/lib/axios)
// =============================================================================

legalApi.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log response trong development
    if (process.env.NODE_ENV === 'development') {
      console.log(`✅ [Legal API] ${response.config.url}`, response.status);
    }
    return response;
  },
  async (error: AxiosError<IApiErrorWrapper>) => {
    const originalRequest = error.config;

    if (process.env.NODE_ENV === 'development') {
      console.error(
        `❌ [Legal API Error] ${originalRequest?.url}`,
        error.response?.status,
      );
    }

    // 401 — Token hết hạn hoặc không hợp lệ → xóa token, redirect về login
    if (error.response?.status === 401) {
      removeStoredToken();

      if (
        typeof window !== 'undefined' &&
        !window.location.pathname.includes('/login')
      ) {
        const currentPath = window.location.pathname + window.location.search;
        if (currentPath !== '/login') {
          sessionStorage.setItem('redirect_after_login', currentPath);
        }
        // Thông báo cho AuthProvider biết cần logout
        window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        window.location.href = '/login';
      }

      return Promise.reject({
        code: 'AUTH_001',
        message: 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.',
        originalError: error,
      });
    }

    // 403 — Không có quyền truy cập
    if (error.response?.status === 403) {
      const responseData = error.response.data as unknown as Record<string, unknown>;
      const errorData =
        (responseData?.detail as Record<string, unknown>)?.error ||
        responseData?.error;
      const errObj = errorData as Record<string, unknown> | undefined;
      return Promise.reject({
        code: errObj?.code || 'AUTH_002',
        message: errObj?.message || 'Bạn không có quyền thực hiện thao tác này.',
        originalError: error,
      });
    }

    // 404 — Không tìm thấy tài nguyên
    if (error.response?.status === 404) {
      return Promise.reject({
        code: 'BIZ_001',
        message: 'Không tìm thấy dữ liệu yêu cầu.',
        originalError: error,
      });
    }

    // 422 — Validation Error (dữ liệu đầu vào không hợp lệ)
    if (error.response?.status === 422) {
      const errorData = error.response.data?.error;
      return Promise.reject({
        code: errorData?.code || 'VAL_001',
        message: errorData?.message || 'Dữ liệu đầu vào không hợp lệ.',
        details: errorData?.details,
        originalError: error,
      });
    }

    // 500+ — Lỗi phía server
    if (error.response && error.response.status >= 500) {
      return Promise.reject({
        code: 'SYS_001',
        message: 'Lỗi hệ thống. Vui lòng thử lại sau.',
        originalError: error,
      });
    }

    // Network error — không nhận được response (mạng bị đứt, backend down)
    if (!error.response) {
      return Promise.reject({
        code: 'NETWORK_ERROR',
        message: 'Không thể kết nối đến máy chủ. Vui lòng kiểm tra kết nối mạng.',
        originalError: error,
      });
    }

    // Lỗi không xác định
    const errorData = error.response.data?.error;
    return Promise.reject({
      code: errorData?.code || 'UNKNOWN_ERROR',
      message: errorData?.message || 'Đã có lỗi xảy ra. Vui lòng thử lại.',
      originalError: error,
    });
  },
);

// =============================================================================
// LEGAL SERVICE
// =============================================================================

export const legalService = {
  // ---------------------------------------------------------------------------
  // LOẠI VĂN BẢN
  // ---------------------------------------------------------------------------

  /**
   * Lấy danh sách loại văn bản.
   * Auth: Tất cả CBCC.
   * Response: { data: ILoaiVanBan[] }
   */
  getLoaiVanBan: () =>
    legalApi.get(`${BASE}/loai-van-ban`),

  /**
   * Lấy danh sách đơn vị kèm số CBCC (để chọn đối tượng áp dụng).
   * Auth: Tất cả CBCC.
   * Response: { data: IDonVi[] }
   */
  getDonVi: () =>
    legalApi.get(`${BASE}/don-vi`),

  /**
   * Tìm kiếm công chức theo tên hoặc mã (dùng cho autocomplete chọn đối tượng áp dụng).
   * Auth: BIEN_TAP, QT_NOI_DUNG, ADMIN.
   * Response: { data: ICongChuc[], pagination: IPagination }
   */
  getCongChuc: (params?: {
    search?: string;
    don_vi_id?: string;
    page?: number;
    page_size?: number;
  }) =>
    legalApi.get(`${BASE}/cong-chuc`, { params }),

  /**
   * Tạo loại văn bản mới.
   * Auth: ADMIN.
   */
  createLoaiVanBan: (data: { ma: string; ten: string; thu_tu?: number }) =>
    legalApi.post(`${BASE}/loai-van-ban`, data),

  /**
   * Cập nhật loại văn bản.
   * Auth: ADMIN.
   */
  updateLoaiVanBan: (
    id: string,
    data: { ma?: string; ten?: string; thu_tu?: number },
  ) => legalApi.put(`${BASE}/loai-van-ban/${id}`, data),

  /**
   * Xóa loại văn bản.
   * Auth: ADMIN.
   */
  deleteLoaiVanBan: (id: string) =>
    legalApi.delete(`${BASE}/loai-van-ban/${id}`),

  // ---------------------------------------------------------------------------
  // VĂN BẢN
  // ---------------------------------------------------------------------------

  /**
   * Lấy danh sách văn bản đã xuất bản.
   * Chỉ trả về VB có trang_thai_duyet = DA_XUAT_BAN.
   * Auth: Tất cả CBCC.
   *
   * @param params - Bộ lọc và phân trang
   */
  getVanBan: (params?: IVanBanQueryParams) =>
    legalApi.get(`${BASE}/van-ban`, { params }),

  /**
   * Lấy danh sách VB chưa đọc / cần xác nhận.
   * Trả về VB có bat_buoc_doc=TRUE mà CBCC chưa đọc/xác nhận.
   * Auth: Tất cả CBCC.
   *
   * @param params - Phân trang
   */
  getVanBanChuaDoc: (params?: { page?: number; page_size?: number }) =>
    legalApi.get(`${BASE}/van-ban/chua-doc`, { params }),

  /**
   * Lấy danh sách VB cho trang quản lý (tất cả trạng thái duyệt).
   * Auth: BIEN_TAP, QT_NOI_DUNG, ADMIN.
   *
   * @param params - Bộ lọc theo trang_thai_duyet, phân trang, tìm kiếm
   */
  getVanBanQuanLy: (params?: {
    trang_thai_duyet?: string;
    page?: number;
    page_size?: number;
    search?: string;
  }) =>
    legalApi.get(`${BASE}/van-ban/quan-ly`, { params }),

  /**
   * Lấy chi tiết 1 văn bản.
   * Side effect: Tạo/cập nhật xac_nhan_doc (da_doc=TRUE, ghi ngay_doc).
   * Auth: Tất cả CBCC.
   *
   * @param id - UUID văn bản
   */
  getVanBanById: (id: string) =>
    legalApi.get(`${BASE}/van-ban/${id}`),

  /**
   * Tạo văn bản mới (trạng thái NHAP).
   * Auth: BIEN_TAP, QT_NOI_DUNG, ADMIN.
   * Content-Type: multipart/form-data (nếu upload file) hoặc application/json.
   *
   * @param data - Thông tin văn bản
   */
  createVanBan: (data: IVanBanCreate) =>
    legalApi.post(`${BASE}/van-ban`, data),

  /**
   * Cập nhật văn bản (chỉ khi trạng thái NHAP hoặc CHO_DUYET).
   * Auth: BIEN_TAP (trạng thái NHAP/CHO_DUYET), QT_NOI_DUNG, ADMIN.
   *
   * @param id   - UUID văn bản
   * @param data - Dữ liệu cập nhật (partial)
   */
  updateVanBan: (id: string, data: Partial<IVanBanCreate>) =>
    legalApi.put(`${BASE}/van-ban/${id}`, data),

  /**
   * Cập nhật trạng thái duyệt văn bản.
   * Workflow: NHAP → CHO_DUYET → DA_DUYET → DA_XUAT_BAN.
   * Side effect khi DA_XUAT_BAN: Tạo xac_nhan_doc cho tất cả CBCC trong doi_tuong_ap_dung.
   * Auth: BIEN_TAP (gửi duyệt), QT_NOI_DUNG (duyệt/từ chối), Lãnh đạo (duyệt), ADMIN.
   *
   * @param id   - UUID văn bản
   * @param data - Trạng thái mới và ghi chú
   */
  updateTrangThai: (id: string, data: ICapNhatTrangThaiBody) =>
    legalApi.patch(`${BASE}/van-ban/${id}/trang-thai`, data),

  /**
   * Xóa văn bản (chỉ khi trạng thái NHAP).
   * Auth: QT_NOI_DUNG, ADMIN.
   *
   * @param id - UUID văn bản
   */
  deleteVanBan: (id: string) =>
    legalApi.delete(`${BASE}/van-ban/${id}`),

  /**
   * Upload file PDF/DOCX cho văn bản.
   * Auth: BIEN_TAP (VB của mình), QT_NOI_DUNG, ADMIN.
   * Content-Type: multipart/form-data (tự động từ FormData).
   *
   * @param vanBanId - UUID văn bản
   * @param file     - File PDF/DOCX cần upload
   */
  uploadFile: (vanBanId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return legalApi.post(`${BASE}/van-ban/${vanBanId}/upload-file`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  /**
   * Download file PDF gốc của văn bản.
   * Auth: Tất cả CBCC.
   * Response: application/pdf (blob).
   *
   * @param id - UUID văn bản
   */
  downloadVanBan: (id: string) =>
    legalApi.get(`${BASE}/van-ban/${id}/download`, { responseType: 'blob' }),

  // ---------------------------------------------------------------------------
  // XÁC NHẬN ĐỌC
  // ---------------------------------------------------------------------------

  /**
   * Xác nhận đã đọc và hiểu văn bản.
   * Cập nhật da_xac_nhan=TRUE, ngay_xac_nhan=NOW().
   * Auth: Tất cả CBCC.
   *
   * @param id   - UUID văn bản
   * @param data - { da_xac_nhan: true, ghi_chu?: string }
   */
  xacNhanDoc: (id: string, data: IXacNhanDocBody) =>
    legalApi.post(`${BASE}/van-ban/${id}/xac-nhan`, data),

  /**
   * Tracking thời gian đọc tích lũy (gọi tự động từ Frontend).
   * Cộng dồn thoi_gian_doc_giay vào tổng thời gian đọc.
   * Auth: Tất cả CBCC.
   *
   * @param id   - UUID văn bản
   * @param data - { thoi_gian_doc_giay: number }
   */
  trackingDoc: (id: string, data: ITrackingDocBody) =>
    legalApi.patch(`${BASE}/van-ban/${id}/tracking`, data),

  /**
   * Lấy báo cáo xác nhận đọc của văn bản (cho lãnh đạo).
   * Auth: QT_NOI_DUNG, Lãnh đạo (đơn vị mình), ADMIN.
   *
   * @param id     - UUID văn bản
   * @param params - { don_vi_id?: string } — lọc theo đơn vị
   */
  getBaoCaoDoc: (id: string, params?: { don_vi_id?: string }) =>
    legalApi.get(`${BASE}/van-ban/${id}/bao-cao-doc`, { params }),

  // ---------------------------------------------------------------------------
  // QUIZ VĂN BẢN
  // ---------------------------------------------------------------------------

  /**
   * Lấy danh sách quiz của văn bản.
   * Auth: Tất cả CBCC.
   *
   * @param vbId - UUID văn bản
   */
  getQuiz: (vbId: string) =>
    legalApi.get(`${BASE}/van-ban/${vbId}/quiz`),

  /**
   * Tạo quiz kiểm tra hiểu biết cho văn bản.
   * Auth: BIEN_TAP, QT_NOI_DUNG, ADMIN.
   *
   * @param vbId - UUID văn bản
   * @param data - Thông tin quiz và câu hỏi
   */
  createQuiz: (vbId: string, data: IQuizVanBanCreate) =>
    legalApi.post(`${BASE}/van-ban/${vbId}/quiz`, data),

  /**
   * Nộp bài làm quiz.
   * Auth: Tất cả CBCC.
   * Response: IKetQuaQuiz — kết quả với điểm số và chi tiết từng câu.
   *
   * @param quizId - UUID quiz
   * @param data   - Danh sách câu trả lời
   */
  lamQuiz: (quizId: string, data: ILamQuizBody) =>
    legalApi.post(`${BASE}/quiz/${quizId}/lam-bai`, data),

  /**
   * Xem kết quả quiz đã làm.
   * Auth: CBCC (của mình), BIEN_TAP, QT_NOI_DUNG, ADMIN.
   *
   * @param quizId - UUID quiz
   */
  getKetQua: (quizId: string) =>
    legalApi.get(`${BASE}/quiz/${quizId}/ket-qua`),

  // ---------------------------------------------------------------------------
  // DASHBOARD & BÁO CÁO
  // ---------------------------------------------------------------------------

  /**
   * Lấy tóm tắt dashboard cá nhân.
   * Auth: Tất cả CBCC.
   * Response: IDashboardSummary
   */
  getDashboard: () =>
    legalApi.get(`${BASE}/dashboard/summary`),

  /**
   * Báo cáo tiến độ đọc VB cá nhân.
   * Auth: Tất cả CBCC.
   *
   * @param params - { thang?: number, nam?: number }
   */
  getBaoCaoCaNhan: (params?: { thang?: number; nam?: number }) =>
    legalApi.get(`${BASE}/bao-cao/ca-nhan`, { params }),

  /**
   * Báo cáo tổng hợp đơn vị cho lãnh đạo.
   * Auth: QT_NOI_DUNG, Lãnh đạo (đơn vị mình), ADMIN.
   *
   * @param donViId - UUID đơn vị
   * @param params  - { thang?: number, nam?: number }
   */
  getBaoCaoDonVi: (donViId: string, params?: { thang?: number; nam?: number }) =>
    legalApi.get(`${BASE}/bao-cao/don-vi/${donViId}`, { params }),
};

export default legalService;
