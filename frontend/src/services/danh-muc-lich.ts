/**
 * src/services/danh-muc-lich.ts
 * =============================
 * Quản trị danh mục dùng chung của Lịch công tác — G4.11.
 *
 * Thay sheet `SETUP` của lichkv8, đáp yêu cầu chuyển đổi mục II.15 và bảng
 * nghiệm thu XI.9. Backend HKG (cổng 8006), prefix
 * `/api/v1/hop-khong-giay/danh-muc`.
 */

import axios, { type AxiosInstance } from 'axios';

import type {
  IMucDanhMuc,
  INhomDanhMuc,
  NhomDanhMuc,
} from '@/types/lich-cong-tac';

const API_URL =
  process.env.NEXT_PUBLIC_HKG_API_URL || '/api/v1/hop-khong-giay';

const TOKEN_KEY = 'kpi_access_token';

const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/danh-muc`,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

interface ApiResponse<T> {
  success: boolean;
  data: T;
}

async function unwrap<T>(p: Promise<{ data: ApiResponse<T> }>): Promise<T> {
  return (await p).data.data;
}

export interface IDanhSachThamSo {
  nhom?: NhomDanhMuc;
  /** Lấy cả mục đã tắt — chỉ có tác dụng với quản trị. */
  gomCaTat?: boolean;
  /** Kèm số bản ghi đang dùng từng mục. Tốn thêm một truy vấn mỗi mục. */
  demSuDung?: boolean;
}

export const danhMucLichApi = {
  /** Các nhóm quản trị được, kèm cờ `duoc_sua` theo vai trò người gọi. */
  nhom: () => unwrap<INhomDanhMuc>(api.get('/nhom')),

  danhSach: (t: IDanhSachThamSo = {}) =>
    unwrap<IMucDanhMuc[]>(
      api.get('/', {
        params: {
          nhom: t.nhom,
          'gom-ca-tat': t.gomCaTat || undefined,
          'dem-su-dung': t.demSuDung || undefined,
        },
      }),
    ),

  them: (goi: {
    nhom: NhomDanhMuc;
    ma: string;
    nhan: string;
    thu_tu?: number;
    mo_ta?: string | null;
  }) => unwrap<IMucDanhMuc>(api.post('/', goi)),

  /**
   * Sửa nhãn, thứ tự, bật/tắt hoặc mô tả.
   *
   * Cố tình KHÔNG nhận `ma`: mã là khoá mà dữ liệu đã ghi tham chiếu tới,
   * đổi là làm mồ côi hàng loạt bản ghi. Máy chủ cũng chối nếu vẫn gửi lên.
   */
  sua: (
    id: string,
    thay_doi: {
      nhan?: string;
      thu_tu?: number;
      is_active?: boolean;
      mo_ta?: string | null;
    },
  ) => unwrap<IMucDanhMuc>(api.patch(`/${id}`, thay_doi)),

  sapXep: (thu_tu: { id: string; thu_tu: number }[]) =>
    unwrap<{ so_muc_doi: number }>(api.put('/sap-xep', { thu_tu })),

  /** Chỉ xoá được khi chưa bản ghi nào dùng tới; đang dùng thì tắt. */
  xoa: (id: string) =>
    unwrap<{ id: string; da_xoa: boolean }>(api.delete(`/${id}`)),
};
