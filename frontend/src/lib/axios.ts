/**
 * src/lib/axios.ts
 * ================
 * Setup Axios instance với interceptors chuẩn Enterprise.
 *
 * Chức năng:
 * - Request Interceptor: Tự động gắn token vào header Authorization
 * - Response Interceptor: Unwrap data và xử lý lỗi 401 (Auto logout)
 */

import axios, {
  AxiosInstance,
  AxiosError,
  InternalAxiosRequestConfig,
  AxiosResponse,
} from 'axios';

import { IApiErrorWrapper } from '@/types/api';

// =============================================================================
// CONSTANTS
// =============================================================================

/** Base URL của Backend API */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

/** Key lưu token trong localStorage */
const TOKEN_STORAGE_KEY = 'kpi_access_token';

/** Các endpoint không cần authentication */
const PUBLIC_ENDPOINTS = ['/auth/login'];

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Lấy token từ localStorage.
 * @returns Token string hoặc null nếu không có
 */
export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

/**
 * Lưu token vào localStorage.
 * @param token - JWT access token
 */
export function setStoredToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

/**
 * Xóa token khỏi localStorage.
 */
export function removeStoredToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

// =============================================================================
// AXIOS INSTANCE
// =============================================================================

/**
 * Tạo Axios instance với config mặc định.
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 giây timeout
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// =============================================================================
// REQUEST INTERCEPTOR
// =============================================================================

/**
 * Interceptor xử lý request trước khi gửi đi.
 * - Tự động gắn token vào header Authorization
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Bỏ qua các endpoint public
    const isPublicEndpoint = PUBLIC_ENDPOINTS.some(
      (endpoint) => config.url?.includes(endpoint)
    );

    if (!isPublicEndpoint) {
      const token = getStoredToken();
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }

    // Log request trong development
    if (process.env.NODE_ENV === 'development') {
      console.log(`🚀 [API Request] ${config.method?.toUpperCase()} ${config.url}`);
    }

    return config;
  },
  (error: AxiosError) => {
    // Log lỗi request
    console.error('❌ [API Request Error]', error.message);
    return Promise.reject(error);
  }
);

// =============================================================================
// RESPONSE INTERCEPTOR
// =============================================================================

/**
 * Interceptor xử lý response trả về.
 * - Unwrap data từ response.data
 * - Xử lý lỗi 401 (Auto logout)
 * - Chuẩn hóa error messages
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log response trong development
    if (process.env.NODE_ENV === 'development') {
      console.log(`✅ [API Response] ${response.config.url}`, response.status);
    }

    // Trả về data trực tiếp (unwrap)
    // Backend trả về { success: true, data: {...} }
    // Sau interceptor, client nhận được {...} trực tiếp
    return response;
  },
  async (error: AxiosError<IApiErrorWrapper>) => {
    const originalRequest = error.config;

    // Log lỗi trong development
    if (process.env.NODE_ENV === 'development') {
      console.error(`❌ [API Error] ${originalRequest?.url}`, error.response?.status);
    }

    // Xử lý lỗi 401 - Unauthorized (Token hết hạn hoặc không hợp lệ)
    if (error.response?.status === 401) {
      // Nếu lỗi 401 từ endpoint login → trả error từ backend (AUTH_003)
      // KHÔNG redirect, KHÔNG xóa token
      const isLoginRequest = originalRequest?.url?.includes('/auth/login');
      if (isLoginRequest) {
        // FastAPI HTTPException trả response dạng: { detail: { success, error: { code, message } } }
        // hoặc dạng chuẩn: { success, error: { code, message } }
        const responseData = error.response.data as any;
        const errorData = responseData?.detail?.error || responseData?.error;
        return Promise.reject({
          code: errorData?.code || 'AUTH_003',
          message: errorData?.message || 'Sai tên đăng nhập hoặc mật khẩu.',
          originalError: error,
        });
      }

      // Các request khác: xóa token và redirect về login
      removeStoredToken();

      // Redirect về trang login nếu không phải đang ở trang login
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        // Lưu URL hiện tại để redirect sau khi login
        const currentPath = window.location.pathname + window.location.search;
        if (currentPath !== '/login') {
          sessionStorage.setItem('redirect_after_login', currentPath);
        }

        // Dispatch event để Auth Store biết cần logout
        window.dispatchEvent(new CustomEvent('auth:unauthorized'));

        // Redirect về login
        window.location.href = '/login';
      }

      // Trả về error chuẩn
      return Promise.reject({
        code: 'AUTH_001',
        message: 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.',
        originalError: error,
      });
    }

    // Xử lý lỗi 403 - Forbidden (Không có quyền hoặc tài khoản bị khóa)
    if (error.response?.status === 403) {
      // FastAPI HTTPException trả response dạng: { detail: { success, error: { code, message } } }
      const responseData = error.response.data as any;
      const errorData = responseData?.detail?.error || responseData?.error;
      return Promise.reject({
        code: errorData?.code || 'AUTH_002',
        message: errorData?.message || 'Bạn không có quyền thực hiện thao tác này.',
        originalError: error,
      });
    }

    // Xử lý lỗi 404 - Not Found
    if (error.response?.status === 404) {
      return Promise.reject({
        code: 'BIZ_001',
        message: 'Không tìm thấy dữ liệu yêu cầu.',
        originalError: error,
      });
    }

    // Xử lý lỗi 422 - Validation Error
    if (error.response?.status === 422) {
      const errorData = error.response.data?.error;
      return Promise.reject({
        code: errorData?.code || 'VAL_001',
        message: errorData?.message || 'Dữ liệu đầu vào không hợp lệ.',
        details: errorData?.details,
        originalError: error,
      });
    }

    // Xử lý lỗi 500+ - Server Error
    if (error.response && error.response.status >= 500) {
      return Promise.reject({
        code: 'SYS_001',
        message: 'Lỗi hệ thống. Vui lòng thử lại sau.',
        originalError: error,
      });
    }

    // Xử lý lỗi network (không có response)
    if (!error.response) {
      return Promise.reject({
        code: 'NETWORK_ERROR',
        message: 'Không thể kết nối đến máy chủ. Vui lòng kiểm tra kết nối mạng.',
        originalError: error,
      });
    }

    // Trả về lỗi mặc định
    const errorData = error.response.data?.error;
    return Promise.reject({
      code: errorData?.code || 'UNKNOWN_ERROR',
      message: errorData?.message || 'Đã có lỗi xảy ra. Vui lòng thử lại.',
      originalError: error,
    });
  }
);

// =============================================================================
// EXPORTS
// =============================================================================

export default apiClient;

/**
 * Type cho API Error (sau khi xử lý qua interceptor).
 */
export interface IApiError {
  code: string;
  message: string;
  details?: Array<{ field: string; message: string }>;
  originalError?: AxiosError;
}

/**
 * Type guard để kiểm tra error có phải IApiError không.
 */
export function isApiError(error: unknown): error is IApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    'message' in error
  );
}