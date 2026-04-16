/**
 * src/lib/dashboard-api.ts
 * =========================
 * Hàm fetch dữ liệu cho từng widget trên trang Tổng quan.
 *
 * Nguyên tắc:
 *  - Mỗi hàm: try/catch → trả null nếu API chưa có hoặc lỗi (fallback graceful)
 *  - Dùng Promise.allSettled() ở page để gọi song song
 *  - Timeout 5s mỗi request (không block UI lâu)
 */

import axios from 'axios';
import type {
  IPortalDashboardSummary,
  IKPIDashboardSummary,
  ILMSDashboardSummary,
  IForumDashboardSummary,
  ILegalDashboardSummary,
  IThongBaoCount,
} from '@/types/portal';

const TOKEN_KEY = 'kpi_access_token';
const TIMEOUT_MS = 5000;

/** Lấy JWT token từ localStorage (SSO chung). */
function authHeaders(): Record<string, string> {
  if (typeof window === 'undefined') return {};
  const token = localStorage.getItem(TOKEN_KEY);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// =============================================================================
// PORTAL — port 8004 (qua Next.js rewrite /api/portal/v1/*)
// =============================================================================

/**
 * Lấy dữ liệu dashboard Portal (tin ghim, tin mới, số liệu 7 ngày).
 * Endpoint: GET /api/portal/v1/dashboard/summary
 */
export async function fetchPortalSummary(): Promise<IPortalDashboardSummary | null> {
  try {
    const res = await axios.get('/api/portal/v1/dashboard/summary', {
      headers: authHeaders(),
      timeout: TIMEOUT_MS,
    });
    // Backend trả { success: true, data: {...} }
    return res.data?.data ?? null;
  } catch {
    return null;
  }
}

// =============================================================================
// KPI — port 8000 (qua axios instance chính baseURL = NEXT_PUBLIC_API_URL)
// =============================================================================

const KPI_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

/**
 * Lấy tóm tắt KPI cá nhân (điểm tháng này, xếp loại).
 * Endpoint: GET /tieu-chi-chung/ket-qua-thang?thang=&nam=
 * Trả null nếu chưa kê khai hoặc API không có dữ liệu.
 */
export async function fetchKPISummary(): Promise<IKPIDashboardSummary | null> {
  try {
    const now = new Date();
    const res = await axios.get(`${KPI_BASE}/tieu-chi-chung/ket-qua-thang`, {
      params: { thang: now.getMonth() + 1, nam: now.getFullYear() },
      headers: authHeaders(),
      timeout: TIMEOUT_MS,
    });
    const data = res.data?.data ?? res.data;
    if (!data) return null;
    return {
      diem_thang_nay: data.tong_diem ?? data.diem_tong ?? undefined,
      xep_loai: data.xep_loai ?? undefined,
      trang_thai_ke_khai: data.trang_thai ?? undefined,
    };
  } catch {
    return null;
  }
}

// =============================================================================
// LMS — port 8001 (qua Next.js rewrite /api/v1/lms/*)
// =============================================================================

/**
 * Lấy tóm tắt học tập cá nhân.
 * Endpoint: GET /api/v1/lms/bao-cao/ca-nhan
 */
export async function fetchLMSSummary(): Promise<ILMSDashboardSummary | null> {
  try {
    const res = await axios.get('/api/v1/lms/bao-cao/ca-nhan', {
      headers: authHeaders(),
      timeout: TIMEOUT_MS,
    });
    const data = res.data?.data ?? res.data;
    if (!data) return null;
    return {
      khoa_dang_hoc: data.khoa_dang_hoc ?? data.tong_dang_hoc ?? undefined,
      khoa_hoan_thanh: data.khoa_hoan_thanh ?? data.tong_hoan_thanh ?? undefined,
      chung_chi: data.chung_chi ?? data.tong_chung_chi ?? undefined,
    };
  } catch {
    return null;
  }
}

// =============================================================================
// FORUM — port 8002 (chưa implement, luôn trả null)
// =============================================================================

/**
 * Placeholder — Forum chưa có backend.
 * Khi Forum sẵn sàng: GET /api/forum/v1/dashboard/summary
 */
export async function fetchForumSummary(): Promise<IForumDashboardSummary | null> {
  try {
    const res = await axios.get('/api/forum/v1/dashboard/summary', {
      headers: authHeaders(),
      timeout: TIMEOUT_MS,
    });
    const data = res.data?.data ?? res.data;
    if (!data) return null;
    return {
      chu_de_moi: data.chu_de_moi ?? undefined,
      tra_loi_moi: data.tra_loi_moi ?? undefined,
    };
  } catch {
    return null;
  }
}

// =============================================================================
// LEGAL — port 8003 (qua Next.js rewrite /api/legal/v1/*)
// =============================================================================

/**
 * Lấy tóm tắt pháp luật (văn bản chưa đọc).
 * Endpoint: GET /api/legal/v1/xac-nhan-doc/summary hoặc tương đương
 */
export async function fetchLegalSummary(): Promise<ILegalDashboardSummary | null> {
  try {
    const res = await axios.get('/api/legal/v1/internal/summary', {
      headers: authHeaders(),
      timeout: TIMEOUT_MS,
    });
    const data = res.data?.data ?? res.data;
    if (!data) return null;
    return {
      vb_chua_doc: data.chua_doc ?? data.vb_chua_doc ?? undefined,
      vb_moi: data.vb_moi ?? data.tong_moi ?? undefined,
    };
  } catch {
    return null;
  }
}

// =============================================================================
// THÔNG BÁO — port 8005 (Common service, chưa implement)
// =============================================================================

/**
 * Placeholder — Common notification service chưa có.
 * Khi sẵn sàng: GET /api/common/v1/thong-bao/count?da_doc=false
 */
export async function fetchThongBaoCount(): Promise<IThongBaoCount | null> {
  try {
    const res = await axios.get('/api/common/v1/thong-bao/count', {
      params: { da_doc: false },
      headers: authHeaders(),
      timeout: TIMEOUT_MS,
    });
    const data = res.data?.data ?? res.data;
    if (!data) return null;
    return {
      count: data.count ?? 0,
      khan: data.khan ?? 0,
      quan_trong: data.quan_trong ?? 0,
      binh_thuong: data.binh_thuong ?? 0,
    };
  } catch {
    return null;
  }
}
