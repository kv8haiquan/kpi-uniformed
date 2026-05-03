/**
 * src/lib/jwt-claims.ts
 * =====================
 * Decode JWT payload (KHÔNG verify signature — chỉ đọc claims).
 * Dùng cho UI guards như sidebar visibility, không thay thế server-side check.
 */

export interface IJwtClaims {
  sub?: string;
  ma_cc?: string;
  ho_ten?: string;
  vai_tro?: string;
  role?: string;
  is_lanh_dao?: boolean;
  is_admin?: boolean;
  don_vi_id?: string;
  platform_roles?: string[];
  exp?: number;
}

/** Base64url decode (browser-safe). */
function base64urlDecode(str: string): string {
  const padding = '='.repeat((4 - (str.length % 4)) % 4);
  const base64 = (str + padding).replace(/-/g, '+').replace(/_/g, '/');
  if (typeof window !== 'undefined' && typeof atob === 'function') {
    return atob(base64);
  }
  return Buffer.from(base64, 'base64').toString('utf-8');
}

/** Đọc claims từ JWT (không verify). Trả {} nếu lỗi. */
export function decodeJwtClaims(token: string | null | undefined): IJwtClaims {
  if (!token) return {};
  const parts = token.split('.');
  if (parts.length !== 3) return {};
  try {
    return JSON.parse(base64urlDecode(parts[1])) as IJwtClaims;
  } catch {
    return {};
  }
}

/** Tiện ích: lấy platform_roles từ token trong localStorage. */
export function getPlatformRolesFromToken(): string[] {
  if (typeof window === 'undefined') return [];
  const token = localStorage.getItem('kpi_access_token');
  return decodeJwtClaims(token).platform_roles || [];
}

/**
 * Check 1 user có quyền truy cập module HKG không.
 *
 * G4-fix-5 (01/05/2026): mở public cho 549 user — phase MVP UAT mở rộng.
 * Mọi user authenticated thấy entry + truy cập được route.
 *
 * Backend permission vẫn enforce:
 * - List `/cuoc-hop/` filter visibility — CBCC thường chỉ thấy họp được mời
 * - Chi tiết họp không được mời → 403 NO_PERMISSION
 * - Edit/delete cần chu_toa | thu_ky | admin role
 *
 * Args giữ lại signature cho future re-gate khi cần (chỉ cần đổi return body).
 */
export function userCanAccessHkg(_opts: {
  vai_tro?: string;
  is_admin?: boolean;
  platform_roles?: string[];
}): boolean {
  return true;
}
