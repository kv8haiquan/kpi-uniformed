/**
 * src/services/hkg.ts
 * ===================
 * Service cho module HKG (Họp Không Giấy) — backend port 8006.
 * Token chia sẻ với KPI/LMS qua localStorage `kpi_access_token`.
 *
 * 35 endpoints theo §2 HKG_API_SPECS.md.
 */

import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios';

import { layTenFile } from '@/services/lich-cong-tac';
import type {
  IBienBan,
  ICuocHop,
  ICuocHopCreate,
  ICuocHopListItem,
  ICuocHopUpdate,
  IDashboardCaNhan,
  IDashboardDonVi,
  IDiemDanh,
  IDiemDanhChiTiet,
  IDiemDanhSummary,
  IMyStatus,
  IKetLuan,
  IKetLuanCreate,
  IMucPhanQuyen,
  INhom,
  INhomChiTiet,
  INhomChiTietInput,
  INhomChiTietUpdate,
  INhomCreate,
  INhomListItem,
  INhomUpdate,
  IQRTokenResponse,
  ITaiLieuKhoItem,
  NguonKhoTaiLieu,
  PhanQuyenTaiLieu,
  ITaiLieu,
  ITaiLieuListItem,
  IThemTuNhomResponse,
  ITienDoCreate,
  IXinPhepVang,
  IXinPhepVangCreate,
  IXuatBienBan,
  TrangThaiKetLuan,
} from '@/types/hkg';

// ════════════════════════════════════════════════════════════
// AXIOS INSTANCE
// ════════════════════════════════════════════════════════════

const HKG_API_URL =
  process.env.NEXT_PUBLIC_HKG_API_URL || '/api/v1/hop-khong-giay';

const TOKEN_KEY = 'kpi_access_token';

const hkgApi: AxiosInstance = axios.create({
  baseURL: HKG_API_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

hkgApi.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ════════════════════════════════════════════════════════════
// RESPONSE WRAPPER
// ════════════════════════════════════════════════════════════
// BE trả: {success: true, data: ..., pagination?}
// Service unwrap data tự động

interface ApiResponse<T> {
  success: boolean;
  data: T;
  pagination?: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}

async function unwrap<T>(promise: Promise<{ data: ApiResponse<T> }>): Promise<T> {
  const resp = await promise;
  return resp.data.data;
}

// ════════════════════════════════════════════════════════════
// MODULE 1 — CUỘC HỌP (7 endpoints)
// ════════════════════════════════════════════════════════════

export interface ICuocHopListParams {
  page?: number;
  limit?: number;
  ngay_tu?: string;
  ngay_den?: string;
  don_vi_id?: string;
  khoi?: string;
  trang_thai?: string;
}

export const cuocHopApi = {
  taoMoi: (data: ICuocHopCreate) => unwrap<ICuocHop>(hkgApi.post('/cuoc-hop/', data)),

  danhSach: (params?: ICuocHopListParams) =>
    hkgApi.get<ApiResponse<ICuocHopListItem[]>>('/cuoc-hop/', { params }),

  chiTiet: (id: string) => unwrap<ICuocHop>(hkgApi.get(`/cuoc-hop/${id}`)),

  capNhat: (id: string, data: ICuocHopUpdate) =>
    unwrap<ICuocHop>(hkgApi.patch(`/cuoc-hop/${id}`, data)),

  huy: (id: string, ly_do: string) =>
    unwrap<ICuocHop>(hkgApi.post(`/cuoc-hop/${id}/huy`, { ly_do })),

  /** Phase 4.1 — Bắt đầu cuộc họp: DA_THONG_BAO → DANG_DIEN_RA. */
  batDau: (id: string) =>
    unwrap<ICuocHop>(hkgApi.post(`/cuoc-hop/${id}/bat-dau`)),

  /** Phase 4.1 — Kết thúc cuộc họp: DANG_DIEN_RA → HOAN_THANH. */
  ketThuc: (id: string) =>
    unwrap<ICuocHop>(hkgApi.post(`/cuoc-hop/${id}/ket-thuc`)),

  guiGiayMoi: (id: string) =>
    unwrap<{ so_giay_moi_da_gui: number }>(hkgApi.post(`/cuoc-hop/${id}/gui-giay-moi`)),

  xacNhanThamDu: (
    id: string,
    payload: { xac_nhan: string; nguoi_uy_quyen_id?: string; ghi_chu?: string },
  ) => unwrap(hkgApi.post(`/cuoc-hop/${id}/xac-nhan`, payload)),

  // G4-fix-6.1: list + sửa thành phần
  // G4-fix-7: BE đã JOIN ho_ten/ma_cc/đơn vị để FE không cần fetch riêng.
  listThanhPhan: (id: string) =>
    unwrap<
      Array<{
        id: string;
        cong_chuc_id: string;
        loai_tham_du: string;
        xac_nhan?: string;
        ho_ten?: string | null;
        ma_cc?: string | null;
        don_vi_id?: string | null;
        ten_don_vi?: string | null;
        chuc_vu?: string | null;
      }>
    >(hkgApi.get(`/cuoc-hop/${id}/thanh-phan`)),

  suaThanhPhan: (
    id: string,
    thanh_phan: Array<{ cong_chuc_id: string; loai_tham_du: string }>,
  ) =>
    unwrap<{ so_them: number; so_bo: number; tong_thanh_phan: number }>(
      hkgApi.put(`/cuoc-hop/${id}/thanh-phan`, { thanh_phan }),
    ),
};

// ════════════════════════════════════════════════════════════
// MODULE 3 — TÀI LIỆU (5 + 2 gateway = 7 endpoints)
// ════════════════════════════════════════════════════════════

export interface ITaiLieuUploadInput {
  cuoc_hop_id: string;
  file: File;
  ten_tai_lieu?: string;
  mo_ta?: string;
  /** MÃ trong danh mục LOAI_TAI_LIEU (không phải nhãn — xem meeting_025). */
  loai_tai_lieu?: string;
  phan_quyen?: PhanQuyenTaiLieu;
  cho_phep_tai?: boolean;
  cho_phep_in?: boolean;
}

export const taiLieuApi = {
  upload: (input: ITaiLieuUploadInput) => {
    const fd = new FormData();
    fd.append('cuoc_hop_id', input.cuoc_hop_id);
    fd.append('file', input.file);
    if (input.ten_tai_lieu) fd.append('ten_tai_lieu', input.ten_tai_lieu);
    if (input.mo_ta) fd.append('mo_ta', input.mo_ta);
    if (input.loai_tai_lieu) fd.append('loai_tai_lieu', input.loai_tai_lieu);
    fd.append('phan_quyen', input.phan_quyen || 'CONG_KHAI');
    fd.append('cho_phep_tai', String(input.cho_phep_tai ?? true));
    fd.append('cho_phep_in', String(input.cho_phep_in ?? true));

    return unwrap<ITaiLieu>(
      hkgApi.post('/tai-lieu/upload', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }),
    );
  },

  listByCuocHop: (cuoc_hop_id: string) =>
    unwrap<ITaiLieuListItem[]>(hkgApi.get(`/cuoc-hop/${cuoc_hop_id}/tai-lieu`)),

  /** Danh mục mức phân quyền, kèm cờ `dat_duoc` theo vai trò người gọi. */
  mucPhanQuyen: () =>
    unwrap<IMucPhanQuyen[]>(hkgApi.get('/tai-lieu/muc-phan-quyen')),

  /**
   * Duyệt CẢ KHO tài liệu họp — cho mục "HKG + Lịch công tác" trong Thư viện
   * tài liệu. Trả kèm cuộc họp mà mỗi file thuộc về; máy chủ đã lọc theo
   * quyền xem cuộc họp và mức hạn chế G5.4 trước khi phát token.
   */
  kho: (t: {
    nguon?: NguonKhoTaiLieu;
    timKiem?: string;
    tuNgay?: string;
    denNgay?: string;
    trang?: number;
    soDong?: number;
  } = {}) =>
    hkgApi.get<{
      success: boolean;
      data: ITaiLieuKhoItem[];
      pagination: { trang: number; so_dong: number; con_nua: boolean };
    }>('/tai-lieu/kho', {
      params: {
        nguon: t.nguon,
        'tim-kiem': t.timKiem || undefined,
        'tu-ngay': t.tuNgay || undefined,
        'den-ngay': t.denNgay || undefined,
        trang: t.trang ?? 1,
        'so-dong': t.soDong ?? 24,
      },
    }),

  /** Số tài liệu mỗi nguồn — để cây thư mục hiện số bên cạnh tên. */
  khoThongKe: () =>
    unwrap<{ HKG: number; LICH_CONG_TAC: number; tong: number }>(
      hkgApi.get('/tai-lieu/kho/thong-ke'),
    ),

  /** Nâng/hạ mức hạn chế hoặc sửa siêu dữ liệu của một tài liệu (G5.4). */
  suaMetadata: (
    id: string,
    thay_doi: {
      ten_tai_lieu?: string;
      mo_ta?: string | null;
      phan_quyen?: PhanQuyenTaiLieu;
      cho_phep_tai?: boolean;
      cho_phep_in?: boolean;
    },
  ) => unwrap<ITaiLieu>(hkgApi.patch(`/tai-lieu/${id}`, thay_doi)),

  xemUrl: (id: string) =>
    unwrap<{ url: string; expires_in_seconds: number }>(
      hkgApi.get(`/tai-lieu/${id}/xem`),
    ),

  taiUrl: (id: string) =>
    unwrap<{ url: string; expires_in_seconds: number }>(
      hkgApi.get(`/tai-lieu/${id}/tai`),
    ),

  xoa: (id: string) =>
    unwrap<{ id: string; is_deleted: boolean }>(hkgApi.delete(`/tai-lieu/${id}`)),

  // 2 gateway endpoints — caller dùng URL trả về từ xemUrl/taiUrl
};

// ════════════════════════════════════════════════════════════
// MODULE 4 — ĐIỂM DANH (4 endpoints)
// ════════════════════════════════════════════════════════════

export const diemDanhApi = {
  qrToken: (cuoc_hop_id: string) =>
    unwrap<IQRTokenResponse>(hkgApi.post(`/diem-danh/qr-token/${cuoc_hop_id}`)),

  quet: (token: string) => unwrap<IDiemDanh>(hkgApi.post('/diem-danh/quet', { token })),

  bamTay: (
    cuoc_hop_id: string,
    diem_danh: Array<{
      cong_chuc_id: string;
      trang_thai: string;
      ghi_chu?: string;
    }>,
  ) =>
    unwrap<{ so_diem_danh: number; chi_tiet: IDiemDanh[] }>(
      hkgApi.post('/diem-danh/bam-tay', { cuoc_hop_id, diem_danh }),
    ),

  summary: (cuoc_hop_id: string) =>
    unwrap<IDiemDanhSummary>(hkgApi.get(`/cuoc-hop/${cuoc_hop_id}/diem-danh`)),

  // G4-fix-6.2: CBCC tự điểm danh từ máy tính (không cần QR)
  tuDiemDanh: (cuoc_hop_id: string) =>
    unwrap<IDiemDanh>(hkgApi.post(`/cuoc-hop/${cuoc_hop_id}/tu-diem-danh`)),

  // Kiểu lấy từ types/hkg.ts — trước đây khai cục bộ ở đây và THIẾU 3 field
  // window_status/open_at/close_at mà máy chủ vẫn trả, nên trang điểm danh
  // phải ép kiểu `as IMyStatus`.
  myStatus: (cuoc_hop_id: string) =>
    unwrap<IMyStatus>(hkgApi.get(`/cuoc-hop/${cuoc_hop_id}/diem-danh-cua-toi`)),

  /** Bảng điểm danh từng thành phần — chỉ ban tổ chức gọi được (403 nếu không). */
  chiTiet: (cuoc_hop_id: string) =>
    unwrap<IDiemDanhChiTiet>(
      hkgApi.get(`/cuoc-hop/${cuoc_hop_id}/diem-danh/chi-tiet`),
    ),

  /**
   * Tải bảng điểm danh dạng Excel.
   *
   * Máy chủ trả thẳng bytes chứ không bọc JSON nên không dùng được `unwrap`.
   * Cùng khuôn với lichCongTacApi.xuatExcel.
   */
  xuatExcel: async (cuoc_hop_id: string) => {
    const resp = await hkgApi.get(
      `/cuoc-hop/${cuoc_hop_id}/diem-danh/xuat-excel`,
      { responseType: 'blob', timeout: 60000 },
    );
    const url = URL.createObjectURL(resp.data as Blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = layTenFile(
      resp.headers['content-disposition'],
      'diem-danh.xlsx',
    );
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};

// ════════════════════════════════════════════════════════════
// MODULE 5 — XIN PHÉP VẮNG (3 endpoints)
// ════════════════════════════════════════════════════════════

export const xinPhepApi = {
  guiDon: (data: IXinPhepVangCreate) =>
    unwrap<IXinPhepVang>(hkgApi.post('/xin-phep-vang/', data)),

  choDuyet: () =>
    unwrap<IXinPhepVang[]>(hkgApi.get('/xin-phep-vang/cho-duyet')),

  duyet: (id: string, quyet_dinh: 'DA_DUYET' | 'TU_CHOI', ly_do_tu_choi?: string) =>
    unwrap<IXinPhepVang>(
      hkgApi.post(`/xin-phep-vang/${id}/duyet`, { quyet_dinh, ly_do_tu_choi }),
    ),
};

// ════════════════════════════════════════════════════════════
// MODULE 9 — BIÊN BẢN (6 endpoints + 1 file gateway)
// ════════════════════════════════════════════════════════════

export const bienBanApi = {
  get: (cuoc_hop_id: string) =>
    unwrap<IBienBan>(hkgApi.get(`/cuoc-hop/${cuoc_hop_id}/bien-ban`)),

  put: (
    cuoc_hop_id: string,
    noi_dung_json: Record<string, unknown>,
    noi_dung_html?: string | null,
  ) =>
    unwrap<IBienBan>(
      hkgApi.put(`/cuoc-hop/${cuoc_hop_id}/bien-ban`, {
        noi_dung_json,
        noi_dung_html,
      }),
    ),

  trinhKy: (bien_ban_id: string) =>
    unwrap<IBienBan>(hkgApi.post(`/bien-ban/${bien_ban_id}/trinh-ky`)),

  ky: (bien_ban_id: string) =>
    unwrap<IBienBan>(hkgApi.post(`/bien-ban/${bien_ban_id}/ky`)),

  xuat: (bien_ban_id: string, dinh_dang: 'docx' | 'pdf') =>
    unwrap<IXuatBienBan>(
      hkgApi.post(`/bien-ban/${bien_ban_id}/xuat`, undefined, {
        params: { 'dinh-dang': dinh_dang },
      } as AxiosRequestConfig),
    ),

  fileUrl: (bien_ban_id: string, dinh_dang: 'docx' | 'pdf') =>
    `${HKG_API_URL}/bien-ban/${bien_ban_id}/file?dinh-dang=${dinh_dang}`,
};

// ════════════════════════════════════════════════════════════
// MODULE 10 — KẾT LUẬN + DASHBOARD (8 endpoints)
// ════════════════════════════════════════════════════════════

export const ketLuanApi = {
  tao: (cuoc_hop_id: string, data: IKetLuanCreate) =>
    unwrap<IKetLuan>(hkgApi.post(`/cuoc-hop/${cuoc_hop_id}/ket-luan`, data)),

  listByCuocHop: (cuoc_hop_id: string) =>
    unwrap<IKetLuan[]>(hkgApi.get(`/cuoc-hop/${cuoc_hop_id}/ket-luan`)),

  capNhat: (kl_id: string, data: Partial<IKetLuanCreate & { trang_thai: TrangThaiKetLuan }>) =>
    unwrap<IKetLuan>(hkgApi.patch(`/ket-luan/${kl_id}`, data)),

  capNhatTienDo: (kl_id: string, data: ITienDoCreate) =>
    unwrap(hkgApi.post(`/ket-luan/${kl_id}/tien-do`, data)),

  cuaToi: (trang_thai?: TrangThaiKetLuan) =>
    unwrap<IKetLuan[]>(hkgApi.get('/ket-luan/cua-toi', { params: { trang_thai } })),

  cuaDonVi: (don_vi_id: string) =>
    unwrap<IKetLuan[]>(hkgApi.get(`/ket-luan/cua-don-vi/${don_vi_id}`)),
};

export const thongKeApi = {
  caNhan: () => unwrap<IDashboardCaNhan>(hkgApi.get('/thong-ke/ca-nhan')),
  donVi: (don_vi_id: string) =>
    unwrap<IDashboardDonVi>(hkgApi.get(`/thong-ke/don-vi/${don_vi_id}`)),
};

// ════════════════════════════════════════════════════════════
// CBCC SEARCH (G4-fix-2 — endpoint riêng HKG)
// ════════════════════════════════════════════════════════════

export interface ICongChucSearchItem {
  id: string;
  ho_ten: string;
  ma_cc: string;
  email: string | null;
  chuc_vu: string | null;
  don_vi_id: string | null;
  ten_don_vi: string | null;
  ma_vai_tro: string | null;
  is_lanh_dao: boolean;
}

export interface ICongChucSearchParams {
  q?: string;
  don_vi_id?: string;
  limit?: number;
}

export const congChucApi = {
  /** Search/list CBCC. Cần ít nhất 1 trong q hoặc don_vi_id. */
  search: (params: ICongChucSearchParams) =>
    unwrap<ICongChucSearchItem[]>(
      hkgApi.get('/cong-chuc/search', {
        params: {
          q: params.q || undefined,
          don_vi_id: params.don_vi_id || undefined,
          limit: params.limit || 20,
        },
      }),
    ),

  /** Hydrate 1 CBCC (cho form sửa hiển thị tên+mã thay vì UUID). */
  getById: (id: string) =>
    unwrap<ICongChucSearchItem>(hkgApi.get(`/cong-chuc/${id}`)),
};

// ════════════════════════════════════════════════════════════
// NHÓM THÀNH PHẦN (CRUD + merge vào cuộc họp)
// ════════════════════════════════════════════════════════════

export interface INhomListParams {
  page?: number;
  limit?: number;
  q?: string;
  loai_nhom?: string;
}

export const nhomThanhPhanApi = {
  danhSach: (params?: INhomListParams) =>
    hkgApi.get<ApiResponse<INhomListItem[]>>('/nhom-thanh-phan/', { params }),

  taoMoi: (data: INhomCreate) =>
    unwrap<INhom>(hkgApi.post('/nhom-thanh-phan/', data)),

  chiTiet: (id: string) => unwrap<INhom>(hkgApi.get(`/nhom-thanh-phan/${id}`)),

  capNhat: (id: string, data: INhomUpdate) =>
    unwrap<INhom>(hkgApi.patch(`/nhom-thanh-phan/${id}`, data)),

  xoa: (id: string) =>
    unwrap<{ id: string; deleted: boolean }>(hkgApi.delete(`/nhom-thanh-phan/${id}`)),

  themThanhVien: (nhom_id: string, data: INhomChiTietInput) =>
    unwrap<INhomChiTiet>(hkgApi.post(`/nhom-thanh-phan/${nhom_id}/thanh-vien`, data)),

  /** Bulk add — skip CBCC đã có (không 409). Trả {so_them, so_bo_qua_trung, tong_thanh_vien}. */
  themThanhVienBatch: (nhom_id: string, chi_tiet: INhomChiTietInput[]) =>
    unwrap<{ so_them: number; so_bo_qua_trung: number; tong_thanh_vien: number }>(
      hkgApi.post(`/nhom-thanh-phan/${nhom_id}/thanh-vien/batch`, { chi_tiet }),
    ),

  suaThanhVien: (nhom_id: string, cong_chuc_id: string, data: INhomChiTietUpdate) =>
    unwrap<INhomChiTiet>(
      hkgApi.put(`/nhom-thanh-phan/${nhom_id}/thanh-vien/${cong_chuc_id}`, data),
    ),

  xoaThanhVien: (nhom_id: string, cong_chuc_id: string) =>
    unwrap<{ deleted: boolean }>(
      hkgApi.delete(`/nhom-thanh-phan/${nhom_id}/thanh-vien/${cong_chuc_id}`),
    ),

  /** Gộp 1+ nhóm vào cuộc họp đã tồn tại — backend skip duplicate, auto-fill thu_ky_id. */
  themTuNhomVaoCuocHop: (cuoc_hop_id: string, nhom_ids: string[]) =>
    unwrap<IThemTuNhomResponse>(
      hkgApi.post(`/cuoc-hop/${cuoc_hop_id}/thanh-phan/them-tu-nhom`, { nhom_ids }),
    ),
};

// ════════════════════════════════════════════════════════════
// MODULE 9 — PRESENTATION (Phase 4.1)
// ════════════════════════════════════════════════════════════

import type { IPresentationStateResponse } from '@/types/hkg-presentation';

export const presentationApi = {
  /**
   * GET /cuoc-hop/{id}/presentation/state
   * Trả state hiện tại + WS token (TTL ≤ 6h, scope=meeting:{id}).
   * Endpoint UPSERT row meeting.trang_thai_trinh_chieu lazy.
   */
  getState: (cuoc_hop_id: string) =>
    unwrap<IPresentationStateResponse>(
      hkgApi.get(`/cuoc-hop/${cuoc_hop_id}/presentation/state`),
    ),
};

/**
 * Build URL WebSocket cho presentation channel.
 *
 * BE mount router WS tại prefix RIÊNG `/ws/hop-khong-giay` (xem
 * `meeting_service/main.py`), KHÔNG nằm dưới `/api/v1/hop-khong-giay`.
 * Path đầy đủ: `/ws/hop-khong-giay/cuoc-hop/{id}/presentation`.
 *
 * Fix 30/07/2026: trước đây build sai thành
 * `/api/v1/hop-khong-giay/ws/cuoc-hop/{id}/presentation` → uvicorn trả 404,
 * FE reconnect mỗi 1–2s và đồng bộ trang trình chiếu không hoạt động.
 *
 * Token đi qua query string vì FastAPI WebSocket không hỗ trợ
 * Authorization header reliable cross-browser.
 */
const HKG_WS_PREFIX = '/ws/hop-khong-giay';

export function buildPresentationWsUrl(
  cuoc_hop_id: string,
  ws_token: string,
): string {
  if (typeof window === 'undefined') return '';
  // Origin của HKG service: nếu NEXT_PUBLIC_HKG_API_URL là absolute (dev trỏ
  // thẳng cổng 8006) thì lấy origin của nó, ngược lại dùng origin hiện tại
  // (production đi qua nginx).
  const origin = HKG_API_URL.startsWith('http')
    ? new URL(HKG_API_URL).origin
    : window.location.origin;
  // http://host → ws://host, https://host → wss://host
  const wsOrigin = origin.replace(/^http/, 'ws');
  return `${wsOrigin}${HKG_WS_PREFIX}/cuoc-hop/${cuoc_hop_id}/presentation?token=${encodeURIComponent(ws_token)}`;
}

// ════════════════════════════════════════════════════════════
// HEALTH (cho debug)
// ════════════════════════════════════════════════════════════

export const hkgHealthApi = {
  health: () => axios.get('/health', { baseURL: HKG_API_URL.replace('/api/v1/hop-khong-giay', '') }),
};
