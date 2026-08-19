/**
 * src/services/doi-soat.ts
 * ========================
 * Đối soát tài liệu di trú — G4.9. Màn hình dùng MỘT LẦN trong đợt chuyển đổi
 * từ lichkv8, xong thì ẩn khỏi menu.
 */

import axios, { type AxiosInstance } from 'axios';

import type {
  IDanhSachDoiSoat,
  IGoiYDoiSoat,
  IThuMucDoiSoat,
  QuyetDinhDoiSoat,
} from '@/types/lich-cong-tac';

const API_URL =
  process.env.NEXT_PUBLIC_HKG_API_URL || '/api/v1/hop-khong-giay';

const TOKEN_KEY = 'kpi_access_token';

const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/doi-soat`,
  timeout: 60000,
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

async function unwrap<T>(
  p: Promise<{ data: { success: boolean; data: T } }>,
): Promise<T> {
  return (await p).data.data;
}

export const doiSoatApi = {
  quyen: () => unwrap<{ duoc_xem: boolean }>(api.get('/quyen')),

  danhSach: (params?: { nhom?: string; 'da-quyet-dinh'?: boolean }) =>
    unwrap<IDanhSachDoiSoat>(api.get('/', { params })),

  ungVien: (id: string, soNgay?: number) =>
    unwrap<IGoiYDoiSoat>(
      api.get(`/${id}/ung-vien`, { params: { 'so-ngay': soNgay } })),

  quyetDinh: (
    id: string,
    quyet_dinh: QuyetDinhDoiSoat,
    cuoc_hop_id?: string | null,
    ghi_chu?: string | null,
  ) =>
    unwrap<IThuMucDoiSoat>(
      api.post(`/${id}/quyet-dinh`, { quyet_dinh, cuoc_hop_id, ghi_chu })),

  boQuyetDinh: (id: string) =>
    unwrap<IThuMucDoiSoat>(api.delete(`/${id}/quyet-dinh`)),

  /** Bản Excel này chính là biên bản đối chiếu nộp khi nghiệm thu. */
  xuatBienBan: async () => {
    const resp = await api.get('/xuat-excel', { responseType: 'blob' });
    const cd = resp.headers['content-disposition'];
    const m = typeof cd === 'string' ? /filename="?([^";]+)"?/.exec(cd) : null;
    const url = URL.createObjectURL(resp.data as Blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = m ? m[1] : 'bien-ban-doi-chieu.xlsx';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};

export default doiSoatApi;
