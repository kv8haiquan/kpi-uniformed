/**
 * src/services/admin.service.ts
 * =============================
 * Service gọi API cho Admin Module.
 * 
 * Version: 1.0.1 (30/01/2026)
 */

import apiClient, { isApiError, IApiError } from '@/lib/axios';
import {
  IUserResponse,
  IUserCreateRequest,
  IUserUpdateRequest,
  IUserStatusRequest,
  IUserTransferRequest,
  ILichSuDieuChuyenResponse,
  ILichSuDieuChuyenUpdateRequest,
  LoaiLichSuDieuChuyen,
  ISpChuanResponse,
  ISpChuanCreateRequest,
  ISpChuanUpdateRequest,
  ICapDoResponse,
  ICapDoCreateRequest,
  ICapDoUpdateRequest,
  IDanhMucCvResponse,
  IDanhMucCvCreateRequest,
  IDanhMucCvUpdateRequest,
  IAdminStats,
  IDonViOption,
  IVaiTroOption,
  IPaginatedResponse,
} from '@/types/admin';

// =============================================================================
// BASE URL (không cần /api/v1 vì đã có trong apiClient.baseURL)
// =============================================================================

const ADMIN_URL = '/admin';

// =============================================================================
// HELPER - Handle API Error
// =============================================================================

function handleError(error: unknown): never {
  if (isApiError(error)) {
    throw error;
  }
  throw {
    code: 'UNKNOWN_ERROR',
    message: 'Có lỗi xảy ra. Vui lòng thử lại.',
  } as IApiError;
}

// =============================================================================
// THỐNG KÊ
// =============================================================================

export const adminService = {
  /**
   * Lấy thống kê tổng quan Admin
   */
  async getStats(): Promise<IAdminStats> {
    try {
      // Backend có endpoint /admin/stats (không phải /admin/overview)
      const response = await apiClient.get(`${ADMIN_URL}/stats`);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  // ===========================================================================
  // USER MANAGEMENT
  // ===========================================================================

  /**
   * Lấy danh sách users với phân trang và filter
   */
  async getUsers(params: {
    page?: number;
    page_size?: number;
    search?: string;
    don_vi_id?: string;
    vai_tro_id?: string;
    is_active?: boolean;
    is_lanh_dao?: boolean;
  } = {}): Promise<IPaginatedResponse<IUserResponse>> {
    try {
      const response = await apiClient.get(`${ADMIN_URL}/users`, { params });
      return response.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Lấy chi tiết một user
   */
  async getUserById(userId: string): Promise<IUserResponse> {
    try {
      const response = await apiClient.get(`${ADMIN_URL}/users/${userId}`);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Tạo mới user
   */
  async createUser(data: IUserCreateRequest): Promise<IUserResponse> {
    try {
      const response = await apiClient.post(`${ADMIN_URL}/users`, data);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Cập nhật thông tin user
   */
  async updateUser(userId: string, data: IUserUpdateRequest): Promise<IUserResponse> {
    try {
      const response = await apiClient.put(`${ADMIN_URL}/users/${userId}`, data);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Cập nhật trạng thái user (kích hoạt/vô hiệu hóa)
   */
  async updateUserStatus(userId: string, data: IUserStatusRequest): Promise<IUserResponse> {
    try {
      const response = await apiClient.put(`${ADMIN_URL}/users/${userId}/status`, data);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Reset password về mặc định (123456)
   */
  async resetUserPassword(userId: string): Promise<{ user_id: string; ma_cc: string; new_password: string }> {
    try {
      const response = await apiClient.put(`${ADMIN_URL}/users/${userId}/reset-password`);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Điều chuyển nhân sự
   */
  async transferUser(userId: string, data: IUserTransferRequest): Promise<IUserResponse> {
    try {
      // Kiểm tra phải có ít nhất 1 thay đổi
      if (!data.don_vi_id_moi && !data.vai_tro_id_moi) {
        throw { code: 'VALIDATION_ERROR', message: 'Vui lòng chọn đơn vị mới hoặc vai trò mới' };
      }
      
      // Backend expect: don_vi_id_moi, vai_tro_id_moi, ly_do, chuc_vu_moi, is_lanh_dao, ngay_hieu_luc
      const apiData: Record<string, unknown> = {
        ly_do: data.ly_do || 'Điều chuyển nhân sự',
      };
      
      if (data.don_vi_id_moi) {
        apiData.don_vi_id_moi = data.don_vi_id_moi;
      }
      if (data.vai_tro_id_moi) {
        apiData.vai_tro_id_moi = data.vai_tro_id_moi;
      }
      if (data.chuc_vu_moi) {
        apiData.chuc_vu_moi = data.chuc_vu_moi;
      }
      if (data.is_lanh_dao !== undefined) {
        apiData.is_lanh_dao = data.is_lanh_dao;
      }
      if (data.ngay_hieu_luc) {
        apiData.ngay_hieu_luc = data.ngay_hieu_luc;
      }

      console.log('Transfer API data:', apiData);
      
      const response = await apiClient.put(`${ADMIN_URL}/users/${userId}/transfer`, apiData);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Lấy lịch sử điều chuyển của user
   */
  async getTransferHistory(userId: string): Promise<ILichSuDieuChuyenResponse[]> {
    try {
      const response = await apiClient.get(`${ADMIN_URL}/users/${userId}/transfer-history`);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Lấy N hoạt động điều chuyển/trạng thái gần đây toàn cơ quan (widget dashboard).
   */
  async getRecentLichSu(limit: number = 10): Promise<ILichSuDieuChuyenResponse[]> {
    try {
      const response = await apiClient.get(`${ADMIN_URL}/lich-su-dieu-chuyen`, {
        params: { page: 1, page_size: limit },
      });
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Danh sách lịch sử điều chuyển/trạng thái toàn cơ quan (phân trang + lọc) —
   * gồm cả CC đã vô hiệu hóa. Dùng cho trang xem đầy đủ.
   */
  async getLichSuDieuChuyen(params: {
    page?: number;
    page_size?: number;
    loai?: LoaiLichSuDieuChuyen;
    search?: string;
  } = {}): Promise<IPaginatedResponse<ILichSuDieuChuyenResponse>> {
    try {
      const response = await apiClient.get(`${ADMIN_URL}/lich-su-dieu-chuyen`, { params });
      return response.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Điều chỉnh một bản ghi lịch sử điều chuyển/trạng thái (sửa sai sót).
   * Nếu dong_bo_hien_tai=true và là bản ghi mới nhất → đồng bộ lại hồ sơ CC.
   */
  async updateTransferHistory(
    userId: string,
    historyId: string,
    data: ILichSuDieuChuyenUpdateRequest
  ): Promise<ILichSuDieuChuyenResponse> {
    try {
      const response = await apiClient.put(
        `${ADMIN_URL}/users/${userId}/transfer-history/${historyId}`,
        data
      );
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Xóa một bản ghi lịch sử điều chuyển/trạng thái nhập sai.
   * dongBo=true và là bản ghi mới nhất → hoàn tác trạng thái hồ sơ CC về giá trị cũ.
   */
  async deleteTransferHistory(
    userId: string,
    historyId: string,
    dongBo: boolean = false
  ): Promise<void> {
    try {
      await apiClient.delete(
        `${ADMIN_URL}/users/${userId}/transfer-history/${historyId}`,
        { params: { dong_bo_hien_tai: dongBo } }
      );
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Xóa hoàn toàn user (hard delete)
   * Điều kiện: User phải đang bị vô hiệu hóa và không có kê khai công việc
   */
  async deleteUser(userId: string): Promise<{ user_id: string; ma_cc: string; ho_ten: string }> {
    try {
      const response = await apiClient.delete(`${ADMIN_URL}/users/${userId}`);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  // ===========================================================================
  // SP CHUẨN MANAGEMENT
  // ===========================================================================

  /**
   * Lấy danh sách SP Chuẩn
   */
  async getSpChuanList(includeInactive: boolean = false): Promise<ISpChuanResponse[]> {
    try {
      const response = await apiClient.get(`${ADMIN_URL}/sp-chuan`, {
        params: { include_inactive: includeInactive }
      });
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Lấy chi tiết SP Chuẩn
   */
  async getSpChuanById(spId: string): Promise<ISpChuanResponse> {
    try {
      const response = await apiClient.get(`${ADMIN_URL}/sp-chuan/${spId}`);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Tạo mới SP Chuẩn
   */
  async createSpChuan(data: ISpChuanCreateRequest): Promise<ISpChuanResponse> {
    try {
      const response = await apiClient.post(`${ADMIN_URL}/sp-chuan`, data);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Cập nhật SP Chuẩn
   */
  async updateSpChuan(spId: string, data: ISpChuanUpdateRequest): Promise<ISpChuanResponse> {
    try {
      const response = await apiClient.put(`${ADMIN_URL}/sp-chuan/${spId}`, data);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Vô hiệu hóa SP Chuẩn
   */
  async deactivateSpChuan(spId: string): Promise<{ id: string; ma_sp: string; is_active: boolean }> {
    try {
      const response = await apiClient.delete(`${ADMIN_URL}/sp-chuan/${spId}`);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  // ===========================================================================
  // CẤP ĐỘ MANAGEMENT
  // ===========================================================================

  /**
   * Lấy danh sách Cấp độ
   */
  async getCapDoList(includeInactive: boolean = false): Promise<ICapDoResponse[]> {
    try {
      const response = await apiClient.get(`${ADMIN_URL}/cap-do`, {
        params: { include_inactive: includeInactive }
      });
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Lấy chi tiết Cấp độ
   */
  async getCapDoById(capDoId: string): Promise<ICapDoResponse> {
    try {
      const response = await apiClient.get(`${ADMIN_URL}/cap-do/${capDoId}`);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Tạo mới Cấp độ
   */
  async createCapDo(data: ICapDoCreateRequest): Promise<ICapDoResponse> {
    try {
      const response = await apiClient.post(`${ADMIN_URL}/cap-do`, data);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Cập nhật Cấp độ
   */
  async updateCapDo(capDoId: string, data: ICapDoUpdateRequest): Promise<ICapDoResponse> {
    try {
      const response = await apiClient.put(`${ADMIN_URL}/cap-do/${capDoId}`, data);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Vô hiệu hóa Cấp độ
   */
  async deactivateCapDo(capDoId: string): Promise<{ id: string; ma_cap_do: string; is_active: boolean }> {
    try {
      const response = await apiClient.delete(`${ADMIN_URL}/cap-do/${capDoId}`);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  // ===========================================================================
  // DANH MỤC CÔNG VIỆC MANAGEMENT
  // ===========================================================================

  /**
   * Lấy danh sách Danh mục CV với phân trang
   */
  async getDanhMucCvList(params: {
    page?: number;
    page_size?: number;
    search?: string;
    sp_chuan_id?: string;
    don_vi_id?: string;
    include_inactive?: boolean;
  } = {}): Promise<IPaginatedResponse<IDanhMucCvResponse>> {
    try {
      const response = await apiClient.get(`${ADMIN_URL}/danh-muc-cv`, { params });
      return response.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Lấy chi tiết Danh mục CV
   */
  async getDanhMucCvById(dmId: string): Promise<IDanhMucCvResponse> {
    try {
      const response = await apiClient.get(`${ADMIN_URL}/danh-muc-cv/${dmId}`);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Tạo mới Danh mục CV
   */
  async createDanhMucCv(data: IDanhMucCvCreateRequest): Promise<IDanhMucCvResponse> {
    try {
      const response = await apiClient.post(`${ADMIN_URL}/danh-muc-cv`, data);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Cập nhật Danh mục CV
   */
  async updateDanhMucCv(dmId: string, data: IDanhMucCvUpdateRequest): Promise<IDanhMucCvResponse> {
    try {
      const response = await apiClient.put(`${ADMIN_URL}/danh-muc-cv/${dmId}`, data);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Vô hiệu hóa Danh mục CV
   */
  async deactivateDanhMucCv(dmId: string): Promise<{ id: string; ma_danh_muc: string; is_active: boolean }> {
    try {
      const response = await apiClient.delete(`${ADMIN_URL}/danh-muc-cv/${dmId}`);
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  // ===========================================================================
  // HELPERS - Lấy danh sách đơn vị & vai trò
  // ===========================================================================

  /**
   * Lấy danh sách đơn vị
   */
  async getDonViList(): Promise<IDonViOption[]> {
    try {
      const response = await apiClient.get('/don-vi');
      return response.data.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Lấy danh sách vai trò từ API endpoint GET /admin/vai-tro
   */
  async getVaiTroList(): Promise<IVaiTroOption[]> {
    try {
      const response = await apiClient.get(`${ADMIN_URL}/vai-tro`);
      const data = response.data.data || [];

      // Map API response sang IVaiTroOption
      const vaiTroList: IVaiTroOption[] = data.map((vt: any) => ({
        id: vt.id,
        ma_vai_tro: vt.ma_vai_tro,
        ten_vai_tro: vt.ten_vai_tro,
        is_lanh_dao: vt.is_lanh_dao,
      }));

      // Sắp xếp theo thứ tự: CC, QLDV, PDV, TDV, PCCT, CCT, ADMIN
      const order = ['CC', 'QLDV', 'PDV', 'TDV', 'PCCT', 'CCT', 'ADMIN', 'TCCB'];
      return vaiTroList.sort((a, b) => {
        const aIdx = order.indexOf(a.ma_vai_tro);
        const bIdx = order.indexOf(b.ma_vai_tro);
        return (aIdx === -1 ? 99 : aIdx) - (bIdx === -1 ? 99 : bIdx);
      });
    } catch (error) {
      console.error('Error loading vai tro:', error);
      return [];
    }
  },
};

// Re-export isApiError for convenience
export { isApiError };
export type { IApiError };

export default adminService;