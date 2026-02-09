/**
 * src/stores/useAuthStore.ts
 * ==========================
 * Zustand store quản lý trạng thái Authentication.
 *
 * State:
 * - user: Thông tin user đang đăng nhập
 * - token: JWT access token
 * - isAuthenticated: Trạng thái đăng nhập
 * - isLoading: Đang loading (validate token)
 *
 * Actions:
 * - loginSuccess: Cập nhật state sau khi login thành công
 * - logout: Xóa state và redirect về login
 * - setUser: Cập nhật thông tin user
 * - setLoading: Cập nhật trạng thái loading
 * - initializeAuth: Khởi tạo auth state từ localStorage
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

import { IUser, IAuthStore } from '@/types/auth';
import { authService } from '@/services/auth.service';
import { getStoredToken, removeStoredToken } from '@/lib/axios';

// =============================================================================
// ZUSTAND STORE
// =============================================================================

/**
 * Auth Store với Zustand.
 * Sử dụng persist middleware để lưu user info vào localStorage.
 */
export const useAuthStore = create<IAuthStore>()(
  persist(
    (set, get) => ({
      // =========================================================================
      // STATE
      // =========================================================================
      
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: true, // Mặc định true để check token khi khởi tạo

      // =========================================================================
      // ACTIONS
      // =========================================================================

      /**
       * Cập nhật state sau khi login thành công.
       *
       * @param user - Thông tin user từ GET /auth/me
       * @param token - JWT access token
       */
      loginSuccess: (user: IUser, token: string) => {
        set({
          user,
          token,
          isAuthenticated: true,
          isLoading: false,
        });

        // Log trong development
        if (process.env.NODE_ENV === 'development') {
          console.log('🔐 [Auth] Login success:', user.ma_cc, user.ho_ten);
        }
      },

      /**
       * Đăng xuất và xóa state.
       * Sẽ redirect về trang login.
       */
      logout: () => {
        // Xóa token từ service
        authService.logout();

        // Reset state
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        });

        // Log trong development
        if (process.env.NODE_ENV === 'development') {
          console.log('🔓 [Auth] Logged out');
        }

        // Redirect về login (nếu đang ở client)
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      },

      /**
       * Cập nhật thông tin user (dùng khi refresh user info).
       *
       * @param user - Thông tin user mới
       */
      setUser: (user: IUser) => {
        set({ user });
      },

      /**
       * Cập nhật trạng thái loading.
       *
       * @param loading - Đang loading hay không
       */
      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },
    }),
    {
  name: 'kpi-auth-storage',
  storage: createJSONStorage(() => localStorage),
  
  // Chỉ persist các field này
  partialize: (state: IAuthStore) => ({    // ✅ Đổi tên + thêm type
    user: state.user,
    token: state.token,
    isAuthenticated: state.isAuthenticated,
  }),
  }
  )
);

// =============================================================================
// HELPER HOOKS
// =============================================================================

/**
 * Hook lấy thông tin user hiện tại.
 */
export const useCurrentUser = () => useAuthStore((state) => state.user);

/**
 * Hook kiểm tra đã đăng nhập chưa.
 */
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);

/**
 * Hook kiểm tra user có phải lãnh đạo không.
 */
export const useIsLanhDao = () => {
  const user = useAuthStore((state) => state.user);
  return user?.is_lanh_dao ?? false;
};

/**
 * Hook kiểm tra user có phải admin không.
 */
export const useIsAdmin = () => {
  const user = useAuthStore((state) => state.user);
  return user?.is_system_admin ?? false;
};

/**
 * Hook lấy tên đơn vị của user.
 */
export const useUserDonVi = () => {
  const user = useAuthStore((state) => state.user);
  return user?.don_vi?.ten_don_vi ?? null;
};

// =============================================================================
// INITIALIZATION FUNCTION
// =============================================================================

/**
 * Khởi tạo auth state từ localStorage.
 * Gọi trong _app.tsx hoặc layout.tsx khi app mount.
 *
 * Quy trình:
 * 1. Kiểm tra có token trong localStorage không
 * 2. Nếu có, gọi GET /auth/me để validate và lấy user info
 * 3. Nếu thành công, cập nhật store
 * 4. Nếu thất bại (token hết hạn), logout
 */
export async function initializeAuth(): Promise<boolean> {
  const { setLoading, loginSuccess, logout } = useAuthStore.getState();
  
  setLoading(true);

  try {
    // Kiểm tra token trong localStorage
    const token = getStoredToken();
    
    if (!token) {
      // Không có token, set loading = false và return
      setLoading(false);
      return false;
    }

    // Có token, validate bằng cách gọi GET /auth/me
    const user = await authService.getMe();
    
    // Token hợp lệ, cập nhật store
    loginSuccess(user, token);
    return true;
    
  } catch (error) {
    // Token không hợp lệ hoặc hết hạn
    console.warn('🔐 [Auth] Token validation failed, logging out...');
    removeStoredToken();
    
    // Reset state nhưng không redirect (để app tự xử lý)
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });
    
    return false;
  }
}

// =============================================================================
// EVENT LISTENER (cho unauthorized event từ axios)
// =============================================================================

if (typeof window !== 'undefined') {
  // Lắng nghe event unauthorized từ axios interceptor
  window.addEventListener('auth:unauthorized', () => {
    const { logout } = useAuthStore.getState();
    
    // Reset state (không redirect vì axios đã redirect)
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });
  });
}

export default useAuthStore;
