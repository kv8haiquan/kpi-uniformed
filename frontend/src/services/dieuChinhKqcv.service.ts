/**
 * src/services/dieuChinhKqcv.service.ts
 * =====================================
 * API service cho điều chỉnh KQCV (Yêu cầu 2 — 06/05/2026).
 */

import apiClient from '@/lib/axios';
import {
  IDieuChinhCreateRequest,
  IDieuChinhKqcv,
} from '@/types/dieuChinhKqcv';

interface IBackendResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

const BASE = '/dieu-chinh-kqcv';

export const dieuChinhKqcvService = {
  async create(payload: IDieuChinhCreateRequest): Promise<IDieuChinhKqcv> {
    const r = await apiClient.post<IBackendResponse<IDieuChinhKqcv>>(BASE, payload);
    return r.data.data;
  },

  async guiDuyet(id: string): Promise<IDieuChinhKqcv> {
    const r = await apiClient.post<IBackendResponse<IDieuChinhKqcv>>(`${BASE}/${id}/gui-duyet`);
    return r.data.data;
  },

  async pheDuyet(id: string, yKien?: string): Promise<IDieuChinhKqcv> {
    const r = await apiClient.post<IBackendResponse<IDieuChinhKqcv>>(`${BASE}/${id}/phe-duyet`, {
      y_kien: yKien ?? null,
    });
    return r.data.data;
  },

  async tuChoi(id: string, yKien: string): Promise<IDieuChinhKqcv> {
    const r = await apiClient.post<IBackendResponse<IDieuChinhKqcv>>(`${BASE}/${id}/tu-choi`, {
      y_kien: yKien,
    });
    return r.data.data;
  },

  async remove(id: string): Promise<void> {
    await apiClient.delete(`${BASE}/${id}`);
  },

  async listMe(trangThai?: string): Promise<IDieuChinhKqcv[]> {
    const r = await apiClient.get<IBackendResponse<IDieuChinhKqcv[]>>(`${BASE}/me`, {
      params: trangThai ? { trang_thai: trangThai } : undefined,
    });
    return r.data.data;
  },

  async listChoToiDuyet(): Promise<IDieuChinhKqcv[]> {
    const r = await apiClient.get<IBackendResponse<IDieuChinhKqcv[]>>(`${BASE}/cho-toi-duyet`);
    return r.data.data;
  },

  async listLichSuCV(keKhaiId: string): Promise<IDieuChinhKqcv[]> {
    const r = await apiClient.get<IBackendResponse<IDieuChinhKqcv[]>>(`${BASE}/lich-su-cv/${keKhaiId}`);
    return r.data.data;
  },
};
