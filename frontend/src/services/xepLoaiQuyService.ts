/**
 * services/xepLoaiQuyService.ts
 * ==============================
 * Service cho API Xếp loại quý (Quarterly Assessment)
 *
 * Version: 3.7.0 (2026-04-16)
 */

import apiClient from '@/lib/axios';
import type {
  TongHopQuyResponse,
  ChiTietQuyResponse,
  XepLoaiQuyQueryParams,
  TinhLaiQuyRequest,
  BaoCaoXepLoaiQuy,
  ChoPheQuyetQueryParams,
} from '@/types/xep-loai-quy';

const BASE_URL = '/xep-loai-quy';
const BAO_CAO_URL = '/bao-cao-xep-loai-quy';

class XepLoaiQuyService {
  /**
   * Lấy danh sách tổng hợp xếp loại quý
   */
  async getTongHopQuy(params: XepLoaiQuyQueryParams): Promise<TongHopQuyResponse> {
    const { data } = await apiClient.get<{ success: boolean; data: TongHopQuyResponse }>(
      `${BASE_URL}/tong-hop`,
      { params }
    );

    if (!data.success) {
      throw new Error('Failed to fetch quarterly assessment');
    }

    return data.data;
  }

  /**
   * Lấy chi tiết đánh giá quý của 1 công chức
   */
  async getChiTietQuy(
    congChucId: string,
    quy: number,
    nam: number
  ): Promise<ChiTietQuyResponse> {
    const { data } = await apiClient.get<{ success: boolean; data: ChiTietQuyResponse }>(
      `${BASE_URL}/chi-tiet/${congChucId}`,
      { params: { quy, nam } }
    );

    if (!data.success) {
      throw new Error('Failed to fetch quarterly details');
    }

    return data.data;
  }

  /**
   * Tính lại điểm quý và lưu vào DB (admin)
   */
  async tinhLaiQuy(request: TinhLaiQuyRequest): Promise<any> {
    const { data } = await apiClient.post<{ success: boolean; data: any }>(
      `${BASE_URL}/tinh-lai`,
      request
    );

    if (!data.success) {
      throw new Error('Failed to recalculate quarterly assessment');
    }

    return data.data;
  }

  // ============================================================================
  // BÁO CÁO XẾP LOẠI QUÝ (WORKFLOW)
  // ============================================================================

  /**
   * TDV tạo hoặc lấy báo cáo xếp loại quý của đơn vị
   */
  async getBaoCaoQuy(quy: number, nam: number): Promise<BaoCaoXepLoaiQuy> {
    const { data } = await apiClient.get<{ success: boolean; data: BaoCaoXepLoaiQuy }>(
      `${BAO_CAO_URL}/don-vi/quy/${quy}/nam/${nam}`
    );

    if (!data.success) {
      throw new Error('Failed to fetch quarterly report');
    }

    return data.data;
  }

  /**
   * TDV điều chỉnh xếp loại đề xuất cho 1 công chức trong báo cáo quý
   */
  async deXuatXepLoai(
    chiTietId: string,
    payload: {
      xep_loai_de_xuat: string;
      ly_do_dieu_chinh?: string;
    }
  ): Promise<void> {
    const { data } = await apiClient.put<{ success: boolean }>(
      `${BAO_CAO_URL}/chi-tiet/${chiTietId}/de-xuat`,
      payload
    );

    if (!data.success) {
      throw new Error('Failed to update classification proposal');
    }
  }

  /**
   * TDV gửi báo cáo quý lên CCT để phê duyệt
   */
  async guiDuyet(baoCaoId: string): Promise<void> {
    const { data } = await apiClient.post<{ success: boolean }>(
      `${BAO_CAO_URL}/${baoCaoId}/gui-duyet`
    );

    if (!data.success) {
      throw new Error('Failed to submit report for approval');
    }
  }

  /**
   * CCT xem danh sách báo cáo quý chờ phê duyệt
   */
  async getChoPheduyet(params?: ChoPheQuyetQueryParams): Promise<{
    data: BaoCaoXepLoaiQuy[];
    pagination: {
      page: number;
      page_size: number;
      total_items: number;
      total_pages: number;
    };
  }> {
    const { data } = await apiClient.get<{
      success: boolean;
      data: BaoCaoXepLoaiQuy[];
      pagination: any;
    }>(`${BAO_CAO_URL}/cho-phe-duyet`, { params });

    if (!data.success) {
      throw new Error('Failed to fetch pending quarterly reports');
    }

    return {
      data: data.data,
      pagination: data.pagination,
    };
  }

  /**
   * CCT phê duyệt hoặc từ chối báo cáo quý
   */
  async pheDuyet(
    baoCaoId: string,
    payload: {
      hanh_dong: 'phe_duyet' | 'tu_choi';
      y_kien?: string;
      chi_tiet_tu_choi?: string[];
    }
  ): Promise<void> {
    // Map frontend format → backend format (action: APPROVE/REJECT)
    const backendPayload = {
      action: payload.hanh_dong === 'phe_duyet' ? 'APPROVE' : 'REJECT',
      y_kien: payload.y_kien,
      chi_tiet_tu_choi: payload.chi_tiet_tu_choi,
    };
    const { data } = await apiClient.post<{ success: boolean }>(
      `${BAO_CAO_URL}/${baoCaoId}/phe-duyet`,
      backendPayload
    );

    if (!data.success) {
      throw new Error('Failed to approve/reject quarterly report');
    }
  }
}

export const xepLoaiQuyService = new XepLoaiQuyService();
