/**
 * src/services/leave.service.ts
 * ==============================
 * Service xử lý các API calls cho Module Quản lý Nghỉ phép.
 *
 * ⚠️ LƯU Ý QUAN TRỌNG - Response Format từ Backend:
 * Backend sử dụng wrapper success_response() với cấu trúc:
 * {
 *   "success": true,
 *   "data": { ... },    // Data thực sự nằm ở đây
 *   "message": "..."
 * }
 *
 * Các API list trả về:
 * {
 *   "success": true,
 *   "data": {
 *     "items": [...],      // Danh sách items
 *     "pagination": {...}  // Thông tin phân trang
 *   }
 * }
 *
 * API nguoi-phe-duyet trả về:
 * {
 *   "success": true,
 *   "data": {
 *     "nguoi_phe_duyet": [...],  // Danh sách người phê duyệt
 *     "auto_approve": boolean    // CCT tự phê duyệt?
 *   }
 * }
 *
 * Tham chiếu: nghi_phep.py (Backend)
 * API Version: v2.4 - Fixed response parsing
 */

import apiClient, { IApiError } from '@/lib/axios';
import {
  INghiPhepResponse,
  INguoiPheDuyetNghi,
  IThongKeNghiPhepCaNhan,
  IBulkCreateResponse,
  INghiPhepCreateRequest,
  INghiPhepBulkCreateRequest,
  INghiPhepUpdateRequest,
  IPheDuyetNghiRequest,
  ITuChoiNghiRequest,
  INghiPhepFilterParams,
} from '@/types/leave';

// =============================================================================
// RESPONSE INTERFACES (Khớp với Backend success_response)
// =============================================================================

/**
 * Base response wrapper từ Backend.
 */
interface IBackendResponse<T> {
  success: boolean;
  data: T;
  message: string;
}

/**
 * Response cho API nguoi-phe-duyet.
 */
interface INguoiPheDuyetResponse {
  nguoi_phe_duyet: INguoiPheDuyetNghi[];
  auto_approve: boolean;
  message?: string;
}

/**
 * Response cho các API có pagination (items + pagination).
 */
interface IPaginatedData<T> {
  items: T[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

// =============================================================================
// LEAVE SERVICE CLASS
// =============================================================================

class LeaveService {
  // ===========================================================================
  // TRA CỨU & HỖ TRỢ
  // ===========================================================================

  /**
   * Lấy danh sách người có thể phê duyệt cho user hiện tại.
   * Backend tự xác định dựa trên cấp bậc.
   *
   * ⚠️ Backend Response Format:
   * {
   *   "success": true,
   *   "data": {
   *     "nguoi_phe_duyet": [...],  // Mảng người phê duyệt
   *     "auto_approve": false       // true nếu là CCT (tự phê duyệt)
   *   },
   *   "message": "..."
   * }
   *
   * @returns Object chứa danh sách người phê duyệt và flag auto_approve
   */
  async getNguoiPheDuyet(): Promise<{ nguoiPheDuyet: INguoiPheDuyetNghi[]; autoApprove: boolean }> {
    try {
      const response = await apiClient.get<IBackendResponse<INguoiPheDuyetResponse>>(
        '/nghi-phep/nguoi-phe-duyet'
      );
      
      // ✅ Parse đúng cấu trúc: response.data.data.nguoi_phe_duyet
      const responseData = response.data;
      
      if (responseData.success && responseData.data) {
        return {
          nguoiPheDuyet: responseData.data.nguoi_phe_duyet || [],
          autoApprove: responseData.data.auto_approve || false,
        };
      }
      
      return { nguoiPheDuyet: [], autoApprove: false };
    } catch (error) {
      console.warn('getNguoiPheDuyet error:', error);
      return { nguoiPheDuyet: [], autoApprove: false };
    }
  }

  /**
   * Lấy danh sách đơn đang chờ user phê duyệt.
   * Dành cho Lãnh đạo.
   *
   * ⚠️ Backend Response Format:
   * {
   *   "success": true,
   *   "data": {
   *     "items": [...],       // Mảng đơn nghỉ
   *     "pagination": {...}   // Thông tin phân trang
   *   }
   * }
   *
   * @param params - Pagination params
   * @returns Danh sách đơn chờ duyệt
   */
  async getPendingLeaves(params?: {
    page?: number;
    page_size?: number;
  }): Promise<{
    data: INghiPhepResponse[];
    pagination: { total_items: number; total_pages: number; page: number; page_size: number };
  }> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

      const url = queryParams.toString()
        ? `/nghi-phep/cho-phe-duyet?${queryParams.toString()}`
        : '/nghi-phep/cho-phe-duyet';

      const response = await apiClient.get<IBackendResponse<IPaginatedData<INghiPhepResponse>>>(url);
      
      // ✅ Parse đúng: response.data.data.items và response.data.data.pagination
      const responseData = response.data;
      
      if (responseData.success && responseData.data) {
        return {
          data: responseData.data.items || [],
          pagination: {
            total_items: responseData.data.pagination?.total || 0,
            total_pages: responseData.data.pagination?.total_pages || 0,
            page: responseData.data.pagination?.page || 1,
            page_size: responseData.data.pagination?.page_size || 20,
          },
        };
      }
      
      return {
        data: [],
        pagination: { total_items: 0, total_pages: 0, page: 1, page_size: 20 },
      };
    } catch (error) {
      throw error as IApiError;
    }
  }

  // ===========================================================================
  // THỐNG KÊ
  // ===========================================================================

  /**
   * Lấy thống kê nghỉ phép cá nhân theo năm.
   *
   * ⚠️ Backend Response Format:
   * {
   *   "success": true,
   *   "data": {
   *     "cong_chuc_id": "...",
   *     "nam": 2026,
   *     "tong_ngay_nghi": 5.0,
   *     "chi_tiet": {
   *       "nghi_tuan": 4.0,
   *       "phep_nam": 1.0,
   *       "phep_nam_con_lai": 11.0,
   *       ...
   *     },
   *     "theo_thang": [...]
   *   }
   * }
   *
   * @param nam - Năm cần thống kê
   * @returns Thống kê cá nhân
   */
  async getThongKeCaNhan(nam?: number): Promise<IThongKeNghiPhepCaNhan> {
    try {
      const year = nam || new Date().getFullYear();
      const response = await apiClient.get<IBackendResponse<{
        cong_chuc_id: string;
        nam: number;
        tong_ngay_nghi: number;
        chi_tiet: {
          nghi_tuan: number;
          phep_nam: number;
          phep_nam_con_lai: number;
          nghi_le: number;
          nghi_om: number;
          thai_san: number;
          viec_rieng: number;
          khong_luong: number;
          nghi_bu: number;
          khac: number;
        };
        theo_thang: Array<{
          thang: number;
          nam: number;
          nghi_tuan: number;
          nghi_khac: number;
          tong: number;
        }>;
      }>>(
        `/nghi-phep/thong-ke?nam=${year}`
      );
      
      // ✅ Parse đúng cấu trúc từ Backend
      const responseData = response.data;
      
      if (responseData.success && responseData.data) {
        const data = responseData.data;
        const chiTiet = data.chi_tiet || {};
        
        return {
          nam: data.nam,
          tong_ngay_nghi: data.tong_ngay_nghi || 0,
          nghi_tuan: chiTiet.nghi_tuan || 0,
          phep_nam_da_dung: chiTiet.phep_nam || 0,
          phep_nam_con_lai: chiTiet.phep_nam_con_lai || 12,
          nghi_om: chiTiet.nghi_om || 0,
          nghi_le: chiTiet.nghi_le || 0,
          nghi_khac: (chiTiet.viec_rieng || 0) + (chiTiet.khong_luong || 0) + 
                     (chiTiet.nghi_bu || 0) + (chiTiet.khac || 0) + (chiTiet.thai_san || 0),
          cho_phe_duyet: 0, // Sẽ tính từ API khác nếu cần
        };
      }
      
      // Default nếu không có data
      return {
        nam: year,
        tong_ngay_nghi: 0,
        nghi_tuan: 0,
        phep_nam_da_dung: 0,
        phep_nam_con_lai: 12,
        nghi_om: 0,
        nghi_le: 0,
        nghi_khac: 0,
        cho_phe_duyet: 0,
      };
    } catch (error) {
      console.warn('getThongKeCaNhan error:', error);
      return {
        nam: nam || new Date().getFullYear(),
        tong_ngay_nghi: 0,
        nghi_tuan: 0,
        phep_nam_da_dung: 0,
        phep_nam_con_lai: 12,
        nghi_om: 0,
        nghi_le: 0,
        nghi_khac: 0,
        cho_phe_duyet: 0,
      };
    }
  }

  /**
   * Lấy tổng ngày nghỉ trong tháng.
   * Dùng cho tính KPI.
   *
   * ⚠️ FIX v2.5.6: Backend CHƯA có endpoint /tong-ngay-nghi
   * Tạm thời dùng API /thong-ke và filter theo tháng
   *
   * @param thang - Tháng
   * @param nam - Năm
   * @returns Tổng ngày nghỉ
   */
  async getTongNgayNghiThang(thang: number, nam: number): Promise<number> {
    try {
      // Gọi API thống kê năm và filter theo tháng
      const response = await apiClient.get<IBackendResponse<{
        theo_thang: Array<{ thang: number; tong: number }>;
      }>>(
        `/nghi-phep/thong-ke?nam=${nam}`
      );
      
      if (response.data.success && response.data.data?.theo_thang) {
        const thangData = response.data.data.theo_thang.find(t => t.thang === thang);
        return thangData?.tong || 0;
      }
      return 0;
    } catch (error) {
      console.warn('getTongNgayNghiThang error:', error);
      return 0;
    }
  }

  // ===========================================================================
  // CRUD ĐƠN NGHỈ PHÉP
  // ===========================================================================

  /**
   * Lấy danh sách đơn nghỉ của bản thân.
   *
   * ⚠️ Backend Response Format:
   * {
   *   "success": true,
   *   "data": {
   *     "items": [...],       // ← Mảng nằm trong "items"
   *     "pagination": {...}
   *   }
   * }
   *
   * @param filters - Filter và pagination params
   * @returns Danh sách đơn nghỉ
   */
  async getMyLeaves(filters?: INghiPhepFilterParams): Promise<{
    data: INghiPhepResponse[];
    pagination: { total_items: number; total_pages: number; page: number; page_size: number };
  }> {
    try {
      const queryParams = new URLSearchParams();

      if (filters?.loai_nghi) queryParams.append('loai_nghi', filters.loai_nghi);
      if (filters?.trang_thai) queryParams.append('trang_thai', filters.trang_thai);
      if (filters?.tu_ngay) queryParams.append('tu_ngay', filters.tu_ngay);
      if (filters?.den_ngay) queryParams.append('den_ngay', filters.den_ngay);
      if (filters?.thang) queryParams.append('thang', filters.thang.toString());
      if (filters?.nam) queryParams.append('nam', filters.nam.toString());
      if (filters?.page) queryParams.append('page', filters.page.toString());
      if (filters?.page_size) queryParams.append('page_size', filters.page_size.toString());

      const url = queryParams.toString()
        ? `/nghi-phep?${queryParams.toString()}`
        : '/nghi-phep';

      const response = await apiClient.get<IBackendResponse<IPaginatedData<INghiPhepResponse>>>(url);
      
      // ✅ Parse đúng: data.items thay vì data trực tiếp
      const responseData = response.data;
      
      if (responseData.success && responseData.data) {
        return {
          data: responseData.data.items || [],
          pagination: {
            total_items: responseData.data.pagination?.total || 0,
            total_pages: responseData.data.pagination?.total_pages || 0,
            page: responseData.data.pagination?.page || 1,
            page_size: responseData.data.pagination?.page_size || 20,
          },
        };
      }
      
      return {
        data: [],
        pagination: { total_items: 0, total_pages: 0, page: 1, page_size: 20 },
      };
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Lấy chi tiết 1 đơn nghỉ.
   *
   * @param id - ID đơn nghỉ
   * @returns Chi tiết đơn
   */
  async getById(id: string): Promise<INghiPhepResponse> {
    try {
      const response = await apiClient.get<IBackendResponse<INghiPhepResponse>>(
        `/nghi-phep/${id}`
      );
      
      if (response.data.success && response.data.data) {
        return response.data.data;
      }
      
      throw new Error('Không tìm thấy đơn nghỉ phép');
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Tạo đơn nghỉ đơn lẻ.
   * Dùng cho: Phép năm, Nghỉ ốm, Việc riêng...
   *
   * @param data - Dữ liệu đơn nghỉ
   * @returns Đơn nghỉ vừa tạo
   */
  async create(data: INghiPhepCreateRequest): Promise<INghiPhepResponse> {
    try {
      const response = await apiClient.post<IBackendResponse<INghiPhepResponse>>(
        '/nghi-phep',
        data
      );
      
      if (response.data.success && response.data.data) {
        return response.data.data;
      }
      
      throw new Error(response.data.message || 'Không thể tạo đơn nghỉ');
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Tạo đơn nghỉ hàng loạt (Bulk).
   * ⭐ Dùng cho nghỉ tuần (NGHI_TUAN) - chọn nhiều ngày rời rạc trên Calendar.
   *
   * Backend sẽ:
   * - Tách thành nhiều đơn riêng biệt (mỗi đơn 1 ngày)
   * - Kiểm tra trùng lặp (skip ngày đã có đơn)
   * - Gán người phê duyệt tự động theo hierarchy
   *
   * @param data - Dữ liệu bulk
   * @returns Kết quả tạo bulk
   */
  async createBulk(data: INghiPhepBulkCreateRequest): Promise<IBulkCreateResponse> {
    try {
      const response = await apiClient.post<IBackendResponse<IBulkCreateResponse>>(
        '/nghi-phep/bulk',
        data
      );
      
      if (response.data.success && response.data.data) {
        return response.data.data;
      }
      
      throw new Error(response.data.message || 'Không thể tạo đơn nghỉ hàng loạt');
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Cập nhật đơn nghỉ.
   * Chỉ được update khi trạng thái là CHO_PHE_DUYET hoặc TU_CHOI.
   *
   * @param id - ID đơn nghỉ
   * @param data - Dữ liệu cập nhật
   * @returns Đơn nghỉ sau cập nhật
   */
  async update(id: string, data: INghiPhepUpdateRequest): Promise<INghiPhepResponse> {
    try {
      const response = await apiClient.put<IBackendResponse<INghiPhepResponse>>(
        `/nghi-phep/${id}`,
        data
      );
      
      if (response.data.success && response.data.data) {
        return response.data.data;
      }
      
      throw new Error(response.data.message || 'Không thể cập nhật đơn nghỉ');
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Xóa đơn nghỉ.
   * Không được xóa đơn có trạng thái DA_PHE_DUYET.
   *
   * @param id - ID đơn nghỉ
   */
  async delete(id: string): Promise<void> {
    try {
      const response = await apiClient.delete<IBackendResponse<null>>(`/nghi-phep/${id}`);
      
      if (!response.data.success) {
        throw new Error(response.data.message || 'Không thể xóa đơn nghỉ');
      }
    } catch (error) {
      throw error as IApiError;
    }
  }

  // ===========================================================================
  // PHÊ DUYỆT
  // ===========================================================================

  /**
   * Phê duyệt đơn nghỉ.
   *
   * @param id - ID đơn nghỉ
   * @param data - Ghi chú phê duyệt (optional)
   * @returns Đơn nghỉ sau phê duyệt
   */
  async approve(id: string, data?: IPheDuyetNghiRequest): Promise<INghiPhepResponse> {
    try {
      const response = await apiClient.post<IBackendResponse<INghiPhepResponse>>(
        `/nghi-phep/${id}/phe-duyet`,
        data || {}
      );
      
      if (response.data.success && response.data.data) {
        return response.data.data;
      }
      
      throw new Error(response.data.message || 'Không thể phê duyệt đơn nghỉ');
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Từ chối đơn nghỉ.
   *
   * ⚠️ LƯU Ý: Backend mong đợi field "ly_do_tu_choi" (không phải "ly_do")
   *
   * @param id - ID đơn nghỉ
   * @param data - Lý do từ chối (bắt buộc)
   * @returns Đơn nghỉ sau từ chối
   */
  async reject(id: string, data: ITuChoiNghiRequest): Promise<INghiPhepResponse> {
    try {
      // ✅ Map đúng field name: ly_do → ly_do_tu_choi
      const response = await apiClient.post<IBackendResponse<INghiPhepResponse>>(
        `/nghi-phep/${id}/tu-choi`,
        { ly_do_tu_choi: data.ly_do }  // Backend expects "ly_do_tu_choi"
      );
      
      if (response.data.success && response.data.data) {
        return response.data.data;
      }
      
      throw new Error(response.data.message || 'Không thể từ chối đơn nghỉ');
    } catch (error) {
      throw error as IApiError;
    }
  }
}

// =============================================================================
// SINGLETON INSTANCE
// =============================================================================

export const leaveService = new LeaveService();
export default leaveService;