/**
 * src/services/kpiLanhDaoV2.service.ts
 * ====================================
 * API service cho KPI lãnh đạo công thức mới.
 */

import apiClient from '@/lib/axios';
import { ICongViecLanhDaoV2, IKpiLanhDaoV2, IKpiLanhDaoV2FeatureFlag } from '@/types/kpiLanhDaoV2';

interface IBackendResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

const BASE = '/kpi-lanh-dao-v2';

export const kpiLanhDaoV2Service = {
  async getFeatureFlag(): Promise<IKpiLanhDaoV2FeatureFlag> {
    const r = await apiClient.get<IBackendResponse<IKpiLanhDaoV2FeatureFlag>>(`${BASE}/feature-flag`);
    return r.data.data;
  },

  async getMyKpi(thang: number, nam: number, tamTinh = false): Promise<IKpiLanhDaoV2> {
    const r = await apiClient.get<IBackendResponse<IKpiLanhDaoV2>>(`${BASE}/me`, {
      params: { thang, nam, tam_tinh: tamTinh },
    });
    return r.data.data;
  },

  async getKpiOf(
    congChucId: string,
    thang: number,
    nam: number,
    tamTinh = false,
  ): Promise<IKpiLanhDaoV2> {
    const r = await apiClient.get<IBackendResponse<IKpiLanhDaoV2>>(`${BASE}/${congChucId}`, {
      params: { thang, nam, tam_tinh: tamTinh },
    });
    return r.data.data;
  },

  // Yêu cầu 1 (06/05/2026): list CV trong scope KPI LĐ
  async getMyCongViec(
    thang: number,
    nam: number,
    tamTinh = false,
    loai: 'all' | 'tu_lam' | 'cap_duoi' = 'all',
  ): Promise<ICongViecLanhDaoV2[]> {
    const r = await apiClient.get<IBackendResponse<ICongViecLanhDaoV2[]>>(
      `${BASE}/me/cong-viec`,
      { params: { thang, nam, tam_tinh: tamTinh, loai } },
    );
    return r.data.data;
  },
};
