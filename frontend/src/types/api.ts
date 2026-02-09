/**
 * src/types/api.ts
 * ================
 * TypeScript interfaces cho API responses.
 * Tham chiếu từ: app/schemas/common.py
 */

// =============================================================================
// GENERIC RESPONSE TYPES
// =============================================================================

/**
 * Chi tiết lỗi cho từng field (validation errors).
 */
export interface IErrorDetail {
  field: string;       // Tên field bị lỗi
  message: string;     // Mô tả lỗi
  type?: string;       // Loại lỗi (optional)
}

/**
 * Schema cho response lỗi từ API.
 */
export interface IErrorResponse {
  code: string;        // Mã lỗi: AUTH_001, VAL_001, etc.
  message: string;     // Mô tả lỗi
  details?: IErrorDetail[]; // Chi tiết lỗi (cho validation errors)
}

/**
 * Response wrapper khi API trả về lỗi.
 */
export interface IApiErrorWrapper {
  success: false;
  error: IErrorResponse;
}

/**
 * Generic response wrapper cho API thành công.
 * Tương ứng với DataResponse[T] trong Python.
 */
export interface IDataResponse<T> {
  success: true;
  data: T;
  message?: string;
}

/**
 * Response wrapper có thể thành công hoặc thất bại.
 * Dùng cho Axios interceptor.
 */
export type IApiResponse<T> = IDataResponse<T> | IApiErrorWrapper;

// =============================================================================
// PAGINATION TYPES
// =============================================================================

/**
 * Thông tin phân trang.
 * Tương ứng với Pagination trong Python.
 */
export interface IPagination {
  page: number;        // Trang hiện tại (bắt đầu từ 1)
  page_size: number;   // Số item mỗi trang
  total_items: number; // Tổng số item
  total_pages: number; // Tổng số trang
}

/**
 * Generic response wrapper cho danh sách có phân trang.
 * Tương ứng với PaginatedResponse[T] trong Python.
 */
export interface IPaginatedResponse<T> {
  success: true;
  data: T[];
  pagination: IPagination;
  message?: string;
}

/**
 * Generic response wrapper cho danh sách không phân trang.
 * Tương ứng với DataListResponse[T] trong Python.
 */
export interface IListResponse<T> {
  success: true;
  data: T[];
  message?: string;
}

// =============================================================================
// QUERY PARAMS TYPES
// =============================================================================

/**
 * Query params phân trang.
 */
export interface IPaginationParams {
  page?: number;       // Default: 1
  page_size?: number;  // Default: 20, max: 100
}

/**
 * Query params sắp xếp.
 */
export interface ISortParams {
  sort_by?: string;    // Field để sắp xếp
  order?: 'asc' | 'desc'; // Thứ tự sắp xếp
}

// =============================================================================
// HTTP STATUS CODES (Reference)
// =============================================================================

/**
 * Mã lỗi chuẩn từ Backend.
 */
export const API_ERROR_CODES = {
  // Auth errors (AUTH_XXX)
  AUTH_001: 'Token hết hạn hoặc không hợp lệ',
  AUTH_002: 'Không có quyền truy cập',
  AUTH_003: 'Sai tên đăng nhập hoặc mật khẩu',
  AUTH_004: 'Tài khoản đã bị khóa',
  
  // Validation errors (VAL_XXX)
  VAL_001: 'Dữ liệu đầu vào không hợp lệ',
  VAL_002: 'Thiếu field bắt buộc',
  
  // Business errors (BIZ_XXX)
  BIZ_001: 'Không tìm thấy dữ liệu',
  BIZ_002: 'Trạng thái không cho phép thao tác này',
  
  // Server errors (SYS_XXX)
  SYS_001: 'Lỗi hệ thống, vui lòng thử lại sau',
} as const;

export type ApiErrorCode = keyof typeof API_ERROR_CODES;
