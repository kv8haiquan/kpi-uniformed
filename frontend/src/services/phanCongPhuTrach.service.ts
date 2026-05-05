/**
 * src/services/phanCongPhuTrach.service.ts
 * ========================================
 * Service xử lý API cho phân công CCT/PCCT phụ trách đơn vị.
 *
 * Backend trả response chuẩn: { success, data, message? }
 */

import apiClient from '@/lib/axios';
import {
  IDonViKhaDung,
  ILanhDaoKhaDung,
  IPhanCongCreateRequest,
  IPhanCongKetThucRequest,
  IPhanCongPhuTrach,
  IPhanCongUpdateRequest,
} from '@/types/phanCongPhuTrach';

interface IBackendResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

const BASE = '/phan-cong-phu-trach';

export const phanCongPhuTrachService = {
  async list(params?: {
    lanh_dao_id?: string;
    don_vi_id?: string;
    ngay?: string;
    include_deleted?: boolean;
  }): Promise<IPhanCongPhuTrach[]> {
    const r = await apiClient.get<IBackendResponse<IPhanCongPhuTrach[]>>(BASE, { params });
    return r.data.data;
  },

  async getById(id: string): Promise<IPhanCongPhuTrach> {
    const r = await apiClient.get<IBackendResponse<IPhanCongPhuTrach>>(`${BASE}/${id}`);
    return r.data.data;
  },

  async create(payload: IPhanCongCreateRequest): Promise<IPhanCongPhuTrach> {
    const r = await apiClient.post<IBackendResponse<IPhanCongPhuTrach>>(BASE, payload);
    return r.data.data;
  },

  async update(id: string, payload: IPhanCongUpdateRequest): Promise<IPhanCongPhuTrach> {
    const r = await apiClient.put<IBackendResponse<IPhanCongPhuTrach>>(`${BASE}/${id}`, payload);
    return r.data.data;
  },

  async ketThuc(id: string, payload: IPhanCongKetThucRequest): Promise<IPhanCongPhuTrach> {
    const r = await apiClient.post<IBackendResponse<IPhanCongPhuTrach>>(
      `${BASE}/${id}/ket-thuc`,
      payload,
    );
    return r.data.data;
  },

  async remove(id: string): Promise<void> {
    await apiClient.delete(`${BASE}/${id}`);
  },

  async getLanhDaoKhaDung(): Promise<ILanhDaoKhaDung[]> {
    const r = await apiClient.get<IBackendResponse<ILanhDaoKhaDung[]>>(
      `${BASE}/_meta/lanh-dao-kha-dung`,
    );
    return r.data.data;
  },

  async getDonViKhaDung(): Promise<IDonViKhaDung[]> {
    const r = await apiClient.get<IBackendResponse<IDonViKhaDung[]>>(
      `${BASE}/_meta/don-vi-kha-dung`,
    );
    return r.data.data;
  },
};
