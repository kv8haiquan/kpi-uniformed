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
  IHKGDashboardSummary,
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
    // Lấy báo cáo cá nhân + đếm yêu cầu chờ phê duyệt song song.
    // Đếm yêu cầu chỉ trả về số > 0 với GV chủ khóa / QT_DAO_TAO / lãnh đạo;
    // user thường sẽ nhận về 0 → backend đã xử lý phân quyền.
    const [resCaNhan, resChoDuyet] = await Promise.allSettled([
      axios.get('/api/v1/lms/bao-cao/ca-nhan', {
        headers: authHeaders(),
        timeout: TIMEOUT_MS,
      }),
      axios.get('/api/v1/lms/dang-ky/cho-phe-duyet', {
        params: { page: 1, page_size: 1 },
        headers: authHeaders(),
        timeout: TIMEOUT_MS,
      }),
    ]);

    const caNhanData =
      resCaNhan.status === 'fulfilled'
        ? resCaNhan.value.data?.data ?? resCaNhan.value.data
        : null;
    if (!caNhanData) return null;

    let choPheDuyet: number | undefined;
    if (resChoDuyet.status === 'fulfilled') {
      const pg = resChoDuyet.value.data?.pagination;
      choPheDuyet = pg?.total_items ?? 0;
    }

    return {
      khoa_dang_hoc: caNhanData.khoa_dang_hoc ?? caNhanData.tong_dang_hoc ?? undefined,
      khoa_hoan_thanh: caNhanData.khoa_hoan_thanh ?? caNhanData.tong_hoan_thanh ?? undefined,
      chung_chi: caNhanData.chung_chi ?? caNhanData.tong_chung_chi ?? undefined,
      cho_phe_duyet: choPheDuyet,
    };
  } catch {
    return null;
  }
}

// =============================================================================
// HKG (Họp Không Giấy) — port 8006 (qua nginx /api/v1/hop-khong-giay/*)
// =============================================================================

/**
 * Lấy tóm tắt cá nhân HKG (số cuộc họp tháng, nhiệm vụ đang làm/quá hạn).
 * Endpoint: GET /api/v1/hop-khong-giay/thong-ke/ca-nhan
 */
export async function fetchHKGSummary(): Promise<IHKGDashboardSummary | null> {
  try {
    const res = await axios.get('/api/v1/hop-khong-giay/thong-ke/ca-nhan', {
      headers: authHeaders(),
      timeout: TIMEOUT_MS,
    });
    const data = res.data?.data ?? res.data;
    if (!data) return null;
    return {
      so_cuoc_hop_thang_nay: data.so_cuoc_hop_thang_nay ?? undefined,
      so_cuoc_hop_tham_du: data.so_cuoc_hop_tham_du ?? undefined,
      ty_le_tham_du: data.ty_le_tham_du ?? undefined,
      nhiem_vu_dang_lam: data.nhiem_vu_dang_lam ?? undefined,
      nhiem_vu_qua_han: data.nhiem_vu_qua_han ?? undefined,
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
