/**
 * src/services/auth.service.ts
 * ============================
 * Service xử lý các API calls liên quan đến Authentication.
 *
 * Endpoints:
 * - POST /auth/login: Đăng nhập
 * - GET /auth/me: Lấy thông tin user hiện tại
 */

import apiClient, { setStoredToken, removeStoredToken, IApiError } from '@/lib/axios';
import { ILoginRequest, ILoginResponse, IUser } from '@/types/auth';
import { IDataResponse } from '@/types/api';

// =============================================================================
// AUTH SERVICE
// =============================================================================

class AuthService {
  /**
   * Đăng nhập vào hệ thống.
   *
   * @param data - Thông tin đăng nhập (username, password)
   * @returns Token response nếu thành công
   * @throws IApiError nếu thất bại
   *
   * @example
   * ```ts
   * const result = await authService.login({
   *   username: '20ZZ-0224',
   *   password: '123456'
   * });
   * console.log(result.access_token);
   * ```
   */
  async login(data: ILoginRequest): Promise<ILoginResponse> {
    try {
      // Backend nhận request dưới dạng form-data (OAuth2PasswordRequestForm)
      const formData = new URLSearchParams();
      formData.append('username', data.username);
      formData.append('password', data.password);

      const response = await apiClient.post<ILoginResponse>('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      // Lưu token vào localStorage
      const tokenData = response.data;
      if (tokenData.access_token) {
        setStoredToken(tokenData.access_token);
      }

      return tokenData;
    } catch (error) {
      // Xử lý lỗi cụ thể cho login
      const apiError = error as IApiError;
      
      // Map mã lỗi sang message thân thiện
      if (apiError.code === 'AUTH_003') {
        throw {
          ...apiError,
          message: 'Sai tên đăng nhập hoặc mật khẩu. Vui lòng thử lại.',
        };
      }
      
      if (apiError.code === 'AUTH_004') {
        throw {
          ...apiError,
          message: 'Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên.',
        };
      }

      throw apiError;
    }
  }

  /**
   * Lấy thông tin user hiện tại từ token.
   *
   * @returns User info nếu token hợp lệ
   * @throws IApiError nếu token hết hạn hoặc không hợp lệ
   *
   * @example
   * ```ts
   * const user = await authService.getMe();
   * console.log(user.ho_ten);
   * ```
   */
  async getMe(): Promise<IUser> {
    try {
      const response = await apiClient.get<IDataResponse<IUser>>('/auth/me');
      
      // Response: { success: true, data: {...user} }
      return response.data.data;
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Đăng xuất khỏi hệ thống.
   * Xóa token khỏi localStorage.
   *
   * @example
   * ```ts
   * authService.logout();
   * // Redirect về trang login
   * ```
   */
  logout(): void {
    removeStoredToken();
    
    // Clear session storage
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('redirect_after_login');
    }
  }

  /**
   * Kiểm tra xem user đã đăng nhập chưa.
   * Dựa vào việc có token trong localStorage không.
   *
   * @returns true nếu có token
   *
   * @note Không validate token, chỉ check sự tồn tại.
   * Để validate, gọi getMe().
   */
  isLoggedIn(): boolean {
    if (typeof window === 'undefined') return false;
    const token = localStorage.getItem('kpi_access_token');
    return !!token;
  }

  /**
   * Lấy URL redirect sau khi login (nếu có).
   * Dùng khi user bị redirect về login do session expired.
   *
   * @returns URL để redirect hoặc '/tong-quan'
   */
  getRedirectUrl(): string {
    if (typeof window === 'undefined') return '/tong-quan';

    const redirectUrl = sessionStorage.getItem('redirect_after_login');
    if (redirectUrl) {
      sessionStorage.removeItem('redirect_after_login');
      return redirectUrl;
    }

    return '/tong-quan';
  }
}

// =============================================================================
// SINGLETON INSTANCE
// =============================================================================

/**
 * Singleton instance của AuthService.
 * Import và sử dụng trực tiếp.
 *
 * @example
 * ```ts
 * import { authService } from '@/services/auth.service';
 * await authService.login({ username, password });
 * ```
 */
export const authService = new AuthService();

export default authService;