/**
 * src/types/auth.ts
 * =================
 * TypeScript interfaces cho Authentication & User.
 * Tham chiếu từ:
 * - app/api/v1/endpoints/auth.py (Login endpoint, /me response)
 * - app/schemas/master_data.py (User schemas)
 * - app/schemas/token.py (Token schema)
 */

// =============================================================================
// ENUMS
// =============================================================================

/**
 * Giới tính công chức.
 */
export type GioiTinh = 'NAM' | 'NU';

/**
 * Loại đơn vị.
 */
export type LoaiDonVi = 'PHONG' | 'DOI' | 'HAI_QUAN_CUA_KHAU';

/**
 * Cấp bậc vai trò.
 */
export type CapBac = 'CHI_CUC_TRUONG' | 'PHO_CHI_CUC_TRUONG' | 'TRUONG_DON_VI' | 'QUAN_LY_DON_VI' | 'PHO_DON_VI' | 'CONG_CHUC';

/**
 * Mã vai trò chuẩn.
 */
export type MaVaiTro = 'CCT' | 'PCCT' | 'TDV' | 'QLDV' | 'PDV' | 'CC' | 'HD_111';

// =============================================================================
// LOGIN TYPES
// =============================================================================

/**
 * Request đăng nhập.
 * Backend nhận qua OAuth2PasswordRequestForm.
 */
export interface ILoginRequest {
  username: string; // Mã công chức (VD: 20ZZ-0224) hoặc 'admin'
  password: string; // Mật khẩu (mặc định: 123456)
}

/**
 * Response khi đăng nhập thành công.
 * Tương ứng với Token schema.
 */
export interface ILoginResponse {
  access_token: string;
  token_type: 'bearer';
}

// =============================================================================
// USER TYPES
// =============================================================================

/**
 * Thông tin đơn vị của user (nested trong /me response).
 */
export interface IUserDonVi {
  id: string;           // UUID
  ma_don_vi: string;    // Mã đơn vị
  ten_don_vi: string;   // Tên đơn vị
  loai_don_vi: LoaiDonVi | null; // Loại đơn vị
}

/**
 * Thông tin vai trò của user (nested trong /me response).
 */
export interface IUserVaiTro {
  id: string;           // UUID
  ma_vai_tro: MaVaiTro; // Mã vai trò: CCT, PCCT, TDV, PDV, CC
  ten_vai_tro: string;  // Tên vai trò
  cap_bac: CapBac | null; // Cấp bậc
}

/**
 * Thông tin user đầy đủ từ endpoint GET /auth/me.
 * Dùng để lưu trong Auth Store.
 */
export interface IUser {
  // Thông tin cơ bản
  id: string;                 // UUID
  ma_cc: string;              // Mã công chức
  ho_ten: string;             // Họ tên
  email: string | null;       // Email
  so_dien_thoai: string | null; // Số điện thoại
  ngay_sinh: string | null;   // ISO date string
  gioi_tinh: GioiTinh | null; // Giới tính
  
  // Chức vụ & vai trò
  chuc_vu: string | null;     // Chức vụ hiển thị (VD: "Đội trưởng")
  is_lanh_dao: boolean;       // Có phải lãnh đạo không
  is_hd_111?: boolean;        // Phase 3 (29/04/2026): HĐ 111 — kê khai form LĐ, không có d/đ/e
  is_system_admin: boolean;   // Có phải System Admin không
  can_view_all_units: boolean; // v1.1.0: Quyền xem toàn chi cục (read-only)
  is_active: boolean;         // Tài khoản đang active
  
  // Nested objects
  don_vi: IUserDonVi | null;  // Thông tin đơn vị
  vai_tro: IUserVaiTro | null; // Thông tin vai trò

  // Timestamps
  last_login: string | null;  // ISO datetime string

  // PL3 V2 (28/04/2026)
  kpi_version_pinned?: 'V1' | 'V2_PL3' | null;  // CC pin riêng (NULL = dùng default)
  effective_kpi_version?: 'V1' | 'V2_PL3';      // resolved version để FE biết route

  // HĐLĐ 111 VB714 (01/06/2026): mốc áp dụng Bộ tiêu chí (FE route view theo tháng)
  hdld_vb714_from?: { nam: number; thang: number } | null;

  // HKG (01/05/2026): platform_roles từ JWT — fallback decode token nếu /me không trả
  platform_roles?: string[];
}

/**
 * Thông tin tóm tắt của user (dùng trong nested responses).
 * Tương ứng với CongChucBriefResponse.
 */
export interface IUserBrief {
  id: string;
  ma_cc: string;
  ho_ten: string;
}

// =============================================================================
// AUTH STORE TYPES
// =============================================================================

/**
 * State của Auth Store.
 */
export interface IAuthState {
  user: IUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

/**
 * Actions của Auth Store.
 */
export interface IAuthActions {
  loginSuccess: (user: IUser, token: string) => void;
  logout: () => void;
  setUser: (user: IUser) => void;
  setLoading: (loading: boolean) => void;
}

/**
 * Toàn bộ Auth Store (State + Actions).
 */
export type IAuthStore = IAuthState & IAuthActions;

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Kiểm tra user có phải lãnh đạo Chi cục không (CCT, PCCT).
 */
export function isLanhDaoChiCuc(user: IUser | null): boolean {
  if (!user?.vai_tro) return false;
  return ['CCT', 'PCCT'].includes(user.vai_tro.ma_vai_tro);
}

/**
 * Kiểm tra user có phải lãnh đạo đơn vị không (TDV, PDV).
 */
export function isLanhDaoDonVi(user: IUser | null): boolean {
  if (!user?.vai_tro) return false;
  return ['TDV', 'PDV'].includes(user.vai_tro.ma_vai_tro);
}

/**
 * Kiểm tra user có phải công chức thường không.
 */
export function isCongChuc(user: IUser | null): boolean {
  if (!user?.vai_tro) return false;
  return user.vai_tro.ma_vai_tro === 'CC';
}

/**
 * Kiểm tra user có phải Quản lý Đơn vị (QLDV) không.
 * QLDV: Read-only TDV + trả lại + export, KHÔNG có quyền phê duyệt.
 */
export function isQLDV(user: IUser | null): boolean {
  if (!user?.vai_tro) return false;
  return user.vai_tro.ma_vai_tro === 'QLDV';
}

/**
 * Lấy tên hiển thị của user.
 */
export function getUserDisplayName(user: IUser | null): string {
  if (!user) return 'Khách';
  return user.ho_ten || user.ma_cc;
}
