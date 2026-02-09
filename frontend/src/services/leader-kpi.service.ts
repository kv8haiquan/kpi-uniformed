/**
 * src/services/leader-kpi.service.ts
 * ===================================
 * Service gọi API cho Kê khai công việc Lãnh đạo.
 * 
 * Lưu ý: Các endpoint này cần Backend implement.
 * File này tạo sẵn structure để Frontend hoạt động.
 * 
 * Version: 2.5.7 (27/01/2026)
 */

import apiClient from '@/lib/axios';
import {
  IKeKhaiLanhDaoForm,
  IKeKhaiLanhDaoCreateRequest,
  IKeKhaiLanhDaoUpdateRequest,
  IKeKhaiLanhDaoResponse,
  IDanhGiaDDEForm,
  IDanhGiaDDERequest,
  IDanhGiaDDEResponse,
  IThongKeKeKhaiLanhDao,
  INguoiPheDuyetLanhDao,
  TrangThaiKeKhaiLD,
} from '@/types/leader-kpi';

// =============================================================================
// API ENDPOINTS (Backend cần implement)
// =============================================================================

const ENDPOINTS = {
  // Kê khai công việc Lãnh đạo
  KE_KHAI_LD: '/ke-khai-lanh-dao',
  KE_KHAI_LD_DETAIL: (id: string) => `/ke-khai-lanh-dao/${id}`,
  KE_KHAI_LD_GUI_DUYET: (id: string) => `/ke-khai-lanh-dao/${id}/gui-duyet`,
  KE_KHAI_LD_THONG_KE: '/ke-khai-lanh-dao/thong-ke/thang',
  
  // Đánh giá d, đ, e
  DANH_GIA_DDE: '/danh-gia-lanh-dao/dde',
  DANH_GIA_DDE_THANG: (thang: number, nam: number) => 
    `/danh-gia-lanh-dao/dde/thang/${thang}/nam/${nam}`,
  
  // Người phê duyệt
  NGUOI_PHE_DUYET_LD: '/ke-khai-lanh-dao/nguoi-phe-duyet',
};

// =============================================================================
// SERVICE CLASS
// =============================================================================

class LeaderKPIService {
  // ===========================================================================
  // KÊ KHAI CÔNG VIỆC LÃNH ĐẠO
  // ===========================================================================

  /**
   * Lấy danh sách kê khai công việc của Lãnh đạo.
   */
  async getKeKhaiList(
    thang: number,
    nam: number,
    trangThai?: TrangThaiKeKhaiLD
  ): Promise<IKeKhaiLanhDaoResponse[]> {
    try {
      const params: Record<string, any> = { thang, nam };
      if (trangThai) params.trang_thai = trangThai;

      const response = await apiClient.get(ENDPOINTS.KE_KHAI_LD, { params });
      
      if (response.data.success) {
        return response.data.data || [];
      }
      return [];
    } catch (error) {
      console.error('[LeaderKPI] Error getting ke khai list:', error);
      // Return empty array - Backend chưa implement
      return [];
    }
  }

  /**
   * Tạo kê khai công việc mới cho Lãnh đạo.
   */
  async createKeKhai(
    data: IKeKhaiLanhDaoCreateRequest
  ): Promise<IKeKhaiLanhDaoResponse | null> {
    try {
      const response = await apiClient.post(ENDPOINTS.KE_KHAI_LD, data);
      
      if (response.data.success) {
        return response.data.data;
      }
      throw new Error(response.data.error?.message || 'Lỗi tạo kê khai');
    } catch (error: any) {
      console.error('[LeaderKPI] Error creating ke khai:', error);
      throw error;
    }
  }

  /**
   * Cập nhật kê khai công việc.
   */
  async updateKeKhai(
    id: string,
    data: Partial<IKeKhaiLanhDaoForm>
  ): Promise<IKeKhaiLanhDaoResponse | null> {
    try {
      const response = await apiClient.put(ENDPOINTS.KE_KHAI_LD_DETAIL(id), data);
      
      if (response.data.success) {
        return response.data.data;
      }
      throw new Error(response.data.error?.message || 'Lỗi cập nhật kê khai');
    } catch (error: any) {
      console.error('[LeaderKPI] Error updating ke khai:', error);
      throw error;
    }
  }

  /**
   * Xóa kê khai công việc.
   */
  async deleteKeKhai(id: string): Promise<boolean> {
    try {
      const response = await apiClient.delete(ENDPOINTS.KE_KHAI_LD_DETAIL(id));
      return response.data.success === true;
    } catch (error) {
      console.error('[LeaderKPI] Error deleting ke khai:', error);
      return false;
    }
  }

  /**
   * Gửi kê khai để phê duyệt.
   * 
   * Backend yêu cầu: { nguoi_phe_duyet_id: UUID }
   */
  async guiDuyet(id: string, nguoiPheDuyetId: string): Promise<boolean> {
    try {
      const response = await apiClient.post(ENDPOINTS.KE_KHAI_LD_GUI_DUYET(id), {
        nguoi_phe_duyet_id: nguoiPheDuyetId
      });
      return response.data.success === true;
    } catch (error) {
      console.error('[LeaderKPI] Error submitting ke khai:', error);
      throw error; // Throw để UI hiển thị lỗi cụ thể
    }
  }

  /**
   * Gửi nhiều kê khai để phê duyệt.
   */
  async guiDuyetNhieu(ids: string[], nguoiPheDuyetId: string): Promise<{ success: string[]; failed: string[] }> {
    const success: string[] = [];
    const failed: string[] = [];

    for (const id of ids) {
      try {
        const response = await apiClient.post(ENDPOINTS.KE_KHAI_LD_GUI_DUYET(id), {
          nguoi_phe_duyet_id: nguoiPheDuyetId
        });
        if (response.data.success) {
          success.push(id);
        } else {
          failed.push(id);
        }
      } catch {
        failed.push(id);
      }
    }

    return { success, failed };
  }

  // ===========================================================================
  // PHÊ DUYỆT KÊ KHAI LÃNH ĐẠO (Dành cho Lãnh đạo cấp trên)
  // ===========================================================================

  /**
   * Lấy danh sách kê khai công việc Lãnh đạo chờ phê duyệt.
   * 
   * API: GET /ke-khai-lanh-dao/cho-phe-duyet
   */
  async getKeKhaiLDChoPeDuyet(thang?: number, nam?: number): Promise<IKeKhaiLDPending[]> {
    try {
      const params: Record<string, any> = {};
      if (thang) params.thang = thang;
      if (nam) params.nam = nam;

      const response = await apiClient.get(`${ENDPOINTS.KE_KHAI_LD}/cho-phe-duyet`, { params });
      
      if (response.data.success) {
        return response.data.data || [];
      }
      return [];
    } catch (error) {
      console.error('[LeaderKPI] Error getting ke khai LD cho phe duyet:', error);
      return [];
    }
  }

  /**
   * Phê duyệt hoặc từ chối kê khai công việc Lãnh đạo.
   * 
   * API: POST /ke-khai-lanh-dao/{id}/phe-duyet
   */
  async pheDuyetKeKhaiLD(
    keKhaiId: string,
    action: 'APPROVE' | 'REJECT',
    soLoiChatLuong?: number,
    soLoiTienDo?: number,
    yKien?: string
  ): Promise<IKeKhaiLanhDaoResponse | null> {
    try {
      const payload: Record<string, any> = {
        action,
        y_kien: yKien || null,
      };

      if (action === 'APPROVE') {
        payload.so_loi_chat_luong = soLoiChatLuong || 0;
        payload.so_loi_tien_do = soLoiTienDo || 0;
      }

      const response = await apiClient.post(`${ENDPOINTS.KE_KHAI_LD}/${keKhaiId}/phe-duyet`, payload);
      
      if (response.data.success) {
        return response.data.data;
      }
      throw new Error(response.data.error?.message || 'Lỗi phê duyệt');
    } catch (error: any) {
      console.error('[LeaderKPI] Error processing ke khai LD phe duyet:', error);
      throw error;
    }
  }

  /**
   * Lấy thống kê kê khai theo tháng.
   */
  async getThongKe(thang: number, nam: number): Promise<IThongKeKeKhaiLanhDao | null> {
    try {
      const response = await apiClient.get(ENDPOINTS.KE_KHAI_LD_THONG_KE, {
        params: { thang, nam },
      });
      
      if (response.data.success) {
        return response.data.data;
      }
      return null;
    } catch (error) {
      console.error('[LeaderKPI] Error getting thong ke:', error);
      // Return default values - Backend chưa implement
      return {
        thang,
        nam,
        tong_cong_viec: 0,
        tong_hoan_thanh: 0,
        tong_chua_hoan_thanh: 0,
        tong_da_duyet: 0,
        tong_cho_duyet: 0,
        tong_tu_choi: 0,
        tong_nhap: 0,
        tong_dat_chat_luong: 0,
        tong_dung_tien_do: 0,
        // v2.7.3: Thêm đủ fields mới
        tong_loi_chat_luong: 0,
        tong_loi_tien_do: 0,
        tong_diem_chat_luong: 0,
        tong_diem_tien_do: 0,
        tam_tinh_tong_cong_viec: 0,
        tam_tinh_hoan_thanh: 0,
        tam_tinh_chua_hoan_thanh: 0,
        tam_tinh_dat_chat_luong: 0,
        tam_tinh_dung_tien_do: 0,
        tam_tinh_loi_chat_luong: 0,
        tam_tinh_loi_tien_do: 0,
        tam_tinh_diem_chat_luong: 0,
        tam_tinh_diem_tien_do: 0,
      };
    }
  }

  // ===========================================================================
  // ĐÁNH GIÁ d, đ, e
  // ===========================================================================

  /**
   * Lấy đánh giá d, đ, e theo tháng.
   */
  async getDanhGiaDDE(thang: number, nam: number): Promise<IDanhGiaDDEResponse | null> {
    try {
      const response = await apiClient.get(ENDPOINTS.DANH_GIA_DDE_THANG(thang, nam));
      
      if (response.data.success) {
        return response.data.data;
      }
      return null;
    } catch (error) {
      console.error('[LeaderKPI] Error getting DDE:', error);
      // Return null - chưa có đánh giá
      return null;
    }
  }

  /**
   * Lưu đánh giá d, đ, e.
   */
  async saveDanhGiaDDE(data: IDanhGiaDDERequest): Promise<IDanhGiaDDEResponse | null> {
    try {
      const response = await apiClient.post(ENDPOINTS.DANH_GIA_DDE, data);
      
      if (response.data.success) {
        return response.data.data;
      }
      throw new Error(response.data.error?.message || 'Lỗi lưu đánh giá');
    } catch (error: any) {
      console.error('[LeaderKPI] Error saving DDE:', error);
      throw error;
    }
  }

  /**
   * Gửi đánh giá d, đ, e để phê duyệt.
   * 
   * BACKEND YÊU CẦU:
   * POST /danh-gia-lanh-dao/dde/thang/{t}/nam/{n}/gui-duyet
   * Body: { nguoi_phe_duyet_id: "uuid" }
   */
  async guiDuyetDDE(thang: number, nam: number, nguoiPheDuyetId: string): Promise<boolean> {
    try {
      const response = await apiClient.post(
        `${ENDPOINTS.DANH_GIA_DDE_THANG(thang, nam)}/gui-duyet`,
        { nguoi_phe_duyet_id: nguoiPheDuyetId }
      );
      return response.data.success === true;
    } catch (error) {
      console.error('[LeaderKPI] Error submitting DDE:', error);
      return false;
    }
  }

  // ===========================================================================
  // NGƯỜI PHÊ DUYỆT
  // ===========================================================================

  /**
   * Lấy danh sách người phê duyệt cho Lãnh đạo.
   * 
   * Quy tắc:
   * - Phó ĐV → Trưởng ĐV cùng đơn vị
   * - Trưởng ĐV → CCT
   * - Phó CCT → CCT
   * - CCT → Tự phê duyệt
   * 
   * BACKEND RESPONSE FORMAT:
   * {
   *   "success": true,
   *   "data": {
   *     "danh_sach": [...],
   *     "ghi_chu": "..."
   *   }
   * }
   */
  async getNguoiPheDuyet(): Promise<INguoiPheDuyetLanhDao[]> {
    try {
      const response = await apiClient.get(ENDPOINTS.NGUOI_PHE_DUYET_LD);
      
      if (response.data.success && response.data.data) {
        // Backend trả về { danh_sach: [...], ghi_chu: "..." }
        // Cần lấy danh_sach, không phải data trực tiếp
        const data = response.data.data;
        return data.danh_sach || [];
      }
      return [];
    } catch (error) {
      console.error('[LeaderKPI] Error getting nguoi phe duyet:', error);
      return [];
    }
  }

  /**
   * Lấy danh sách người phê duyệt cho đánh giá d, đ, e.
   */
  async getNguoiPheDuyetDDE(): Promise<INguoiPheDuyetLanhDao[]> {
    try {
      const response = await apiClient.get('/danh-gia-lanh-dao/dde/nguoi-phe-duyet');
      
      if (response.data.success && response.data.data) {
        const data = response.data.data;
        return data.danh_sach || [];
      }
      return [];
    } catch (error) {
      console.error('[LeaderKPI] Error getting nguoi phe duyet DDE:', error);
      return [];
    }
  }

  // ===========================================================================
  // PHÊ DUYỆT D, Đ, E (Dành cho Lãnh đạo cấp trên)
  // ===========================================================================

  /**
   * Lấy danh sách đánh giá d, đ, e chờ phê duyệt.
   * 
   * BACKEND RESPONSE:
   * {
   *   "success": true,
   *   "data": [
   *     {
   *       "id": "uuid",
   *       "cong_chuc_id": "uuid",
   *       "cong_chuc": { "id", "ma_cc", "ho_ten", "chuc_vu" },
   *       "thang": 1, "nam": 2026,
   *       "d_ket_qua_don_vi": 100,
   *       "dd_to_chuc_trien_khai": 100,
   *       "e_doan_ket_noi_bo": 50,
   *       "trang_thai": "CHO_PHE_DUYET",
   *       ...
   *     }
   *   ]
   * }
   */
  async getDDEChoPeDuyet(thang?: number, nam?: number): Promise<IDanhGiaDDEPending[]> {
    try {
      const params: Record<string, any> = {};
      if (thang) params.thang = thang;
      if (nam) params.nam = nam;

      const response = await apiClient.get('/danh-gia-lanh-dao/dde/cho-phe-duyet', { params });
      
      if (response.data.success) {
        return response.data.data || [];
      }
      return [];
    } catch (error) {
      console.error('[LeaderKPI] Error getting DDE cho phe duyet:', error);
      return [];
    }
  }

  /**
   * Phê duyệt hoặc từ chối đánh giá d, đ, e.
   * 
   * @param ddeId - ID đánh giá d, đ, e
   * @param action - "APPROVE" hoặc "REJECT"
   * @param yKien - Ý kiến phê duyệt/từ chối
   * @param adjustments - Điều chỉnh giá trị (chỉ khi APPROVE)
   */
  async pheDuyetDDE(
    ddeId: string,
    action: 'APPROVE' | 'REJECT',
    yKien?: string,
    adjustments?: {
      d_phe_duyet?: number;
      dd_phe_duyet?: number;
      e_phe_duyet?: number;
    }
  ): Promise<IDanhGiaDDEResponse | null> {
    try {
      const payload: Record<string, any> = {
        action,
        y_kien: yKien || null,
      };

      // Nếu APPROVE và có điều chỉnh
      if (action === 'APPROVE' && adjustments) {
        if (adjustments.d_phe_duyet !== undefined) payload.d_phe_duyet = adjustments.d_phe_duyet;
        if (adjustments.dd_phe_duyet !== undefined) payload.dd_phe_duyet = adjustments.dd_phe_duyet;
        if (adjustments.e_phe_duyet !== undefined) payload.e_phe_duyet = adjustments.e_phe_duyet;
      }

      const response = await apiClient.post(`/danh-gia-lanh-dao/dde/${ddeId}/phe-duyet`, payload);
      
      if (response.data.success) {
        return response.data.data;
      }
      throw new Error(response.data.error?.message || 'Lỗi phê duyệt');
    } catch (error: any) {
      console.error('[LeaderKPI] Error processing DDE phe duyet:', error);
      throw error;
    }
  }
}

// =============================================================================
// INTERFACE CHO PHÊ DUYỆT D, Đ, E
// =============================================================================

export interface IDanhGiaDDEPending {
  id: string;
  cong_chuc_id: string;
  cong_chuc?: {
    id: string;
    ma_cc: string;
    ho_ten: string;
    chuc_vu?: string;
  };
  thang: number;
  nam: number;
  d_ket_qua_don_vi: number;
  d_ghi_chu?: string | null;
  dd_to_chuc_trien_khai: number;
  dd_ghi_chu?: string | null;
  e_doan_ket_noi_bo: number;
  e_ghi_chu?: string | null;
  trang_thai: string;
  nguoi_phe_duyet_id?: string | null;
  created_at?: string;
  updated_at?: string;
}

// Interface cho Kê khai Lãnh đạo chờ phê duyệt
export interface IKeKhaiLDPending {
  id: string;
  cong_chuc_id: string;
  cong_chuc?: {
    id: string;
    ma_cc: string;
    ho_ten: string;
    chuc_vu?: string;
  };
  thang: number;
  nam: number;
  ten_cong_viec: string;
  mo_ta?: string | null;
  ngay_thuc_hien: string;
  trang_thai_hoan_thanh: string;
  so_luong: number;
  trang_thai: string;
  nguoi_phe_duyet_id?: string | null;
  nguoi_phe_duyet?: {
    id: string;
    ma_cc: string;
    ho_ten: string;
    chuc_vu?: string;
  } | null;
  so_loi_chat_luong?: number;
  so_loi_tien_do?: number;
  y_kien_lanh_dao?: string | null;
  created_at?: string;
  updated_at?: string;
}

// =============================================================================
// EXPORT SINGLETON
// =============================================================================

export const leaderKPIService = new LeaderKPIService();
export default leaderKPIService;