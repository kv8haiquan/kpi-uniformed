import apiClient from '@/lib/axios';
import { IDoiSoatData } from '@/types/doi-soat';

const BASE_URL = '/doi-soat-danh-gia';

class DoiSoatService {
  /** Lấy dữ liệu đối soát hoàn thành đánh giá tháng (toàn Chi cục hoặc 1 đơn vị). */
  async getDoiSoat(
    thang: number,
    nam: number,
    donViId?: string,
  ): Promise<IDoiSoatData | null> {
    try {
      const params: Record<string, string> = {};
      if (donViId) params.don_vi_id = donViId;
      const res = await apiClient.get(`${BASE_URL}/thang/${thang}/nam/${nam}`, { params });
      return res.data?.success ? (res.data.data as IDoiSoatData) : null;
    } catch (error) {
      console.error('[DoiSoat] Error:', error);
      throw error;
    }
  }

  /** Tải Excel danh sách đối soát. */
  async exportDoiSoat(thang: number, nam: number, donViId?: string): Promise<void> {
    const params: Record<string, string> = {};
    if (donViId) params.don_vi_id = donViId;
    const res = await apiClient.get(`${BASE_URL}/thang/${thang}/nam/${nam}/export`, {
      params,
      responseType: 'blob',
    });
    const blob = new Blob([res.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `DoiSoat_T${String(thang).padStart(2, '0')}_${nam}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
}

export const doiSoatService = new DoiSoatService();
