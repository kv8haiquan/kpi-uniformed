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
 * Tham chiếu: nghi_phep.py (Backend v2.5)
 * API Version: v2.6 - Hỗ trợ phê duyệt 2 cấp
 *
 * THAY ĐỔI v2.6:
 * - getPendingLeaves() trả về đơn cho cả cap1 và cap2
 * - approve() tự động xử lý đúng cấp phê duyệt
 * - reject() hỗ trợ từ chối ở cả 2 cấp
 * - Thêm getStatsByApprovalLevel() thống kê theo cấp
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
 *
 * ⚠️ LƯU Ý QUAN TRỌNG (v3.0 FIX):
 * Backend GET /nghi-phep/nguoi-phe-duyet trả:
 *   { success: true, data: [ { id, ho_ten, chuc_vu, ... } ] }
 * → data là ARRAY TRỰC TIẾP, không wrap trong object { nguoi_phe_duyet: [] }
 *
 * Trước đây service expect sai format { nguoi_phe_duyet: [], auto_approve: false }
 * nên luôn parse ra mảng rỗng → hiện "Hệ thống tự gán" thay vì tên Đội trưởng.
 */
// (Interface INguoiPheDuyetResponse removed - không cần vì data là array)

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
  // v2.6: Thêm thống kê theo cấp
  thong_ke?: {
    cho_cap1: number;
    cho_cap2: number;
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
   * ⚠️ FIX v3.0: Backend trả data là ARRAY trực tiếp:
   *   { success: true, data: [ { id, ho_ten, chuc_vu } ] }
   * - CC/PDV → Trả về Trưởng ĐV cùng đơn vị (Đội trưởng)
   * - PCCT/TDV → Trả về CCT
   * - CCT → Trả về [] (tự phê duyệt)
   *
   * @returns Object chứa danh sách người phê duyệt
   */
  async getNguoiPheDuyet(): Promise<{
    nguoiPheDuyet: INguoiPheDuyetNghi[];
    autoApprove: boolean;
    quyTrinh: 'TU_PHE_DUYET' | '1_CAP' | '2_CAP';
  }> {
    try {
      const response = await apiClient.get<IBackendResponse<INguoiPheDuyetNghi[] | Record<string, unknown>>>(
        '/nghi-phep/nguoi-phe-duyet'
      );
      
      const responseData = response.data;
      
      if (responseData.success && responseData.data) {
        // ⚠️ FIX v3.0: Backend trả data là ARRAY trực tiếp
        // Trước đây expect { nguoi_phe_duyet: [], auto_approve: false }
        // Thực tế backend trả [ { id, ho_ten, chuc_vu, don_vi_ten } ]
        let nguoiPheDuyet: INguoiPheDuyetNghi[] = [];
        
        if (Array.isArray(responseData.data)) {
          // ✅ Backend v3.0: data là array trực tiếp
          nguoiPheDuyet = responseData.data as INguoiPheDuyetNghi[];
        } else if (
          typeof responseData.data === 'object' &&
          'nguoi_phe_duyet' in responseData.data
        ) {
          // Fallback: format cũ { nguoi_phe_duyet: [...] }
          const legacy = responseData.data as { nguoi_phe_duyet?: INguoiPheDuyetNghi[]; auto_approve?: boolean; quy_trinh?: string };
          nguoiPheDuyet = legacy.nguoi_phe_duyet || [];
          
          return {
            nguoiPheDuyet,
            autoApprove: legacy.auto_approve || false,
            quyTrinh: (legacy.quy_trinh as 'TU_PHE_DUYET' | '1_CAP' | '2_CAP') || '1_CAP',
          };
        }
        
        // Xác định auto_approve: CCT trả mảng rỗng + message chứa "tự phê duyệt"
        const msg = responseData.message || '';
        const autoApprove = nguoiPheDuyet.length === 0 && msg.toLowerCase().includes('tự phê duyệt');
        
        return {
          nguoiPheDuyet,
          autoApprove,
          quyTrinh: autoApprove ? 'TU_PHE_DUYET' : '1_CAP',
        };
      }
      
      return { nguoiPheDuyet: [], autoApprove: false, quyTrinh: '1_CAP' };
    } catch (error) {
      console.warn('getNguoiPheDuyet error:', error);
      return { nguoiPheDuyet: [], autoApprove: false, quyTrinh: '1_CAP' };
    }
  }

  /**
   * Lấy danh sách đơn đang chờ user phê duyệt.
   * Dành cho Lãnh đạo.
   *
   * v2.6: Trả về cả đơn chờ cap1 và cap2 (backend tự filter theo user).
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
    thongKe: { cho_cap1: number; cho_cap2: number };
  }> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

      const url = queryParams.toString()
        ? `/nghi-phep/cho-phe-duyet?${queryParams.toString()}`
        : '/nghi-phep/cho-phe-duyet';

      const response = await apiClient.get<IBackendResponse<IPaginatedData<INghiPhepResponse>>>(url);
      
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
          thongKe: responseData.data.thong_ke || { cho_cap1: 0, cho_cap2: 0 },
        };
      }
      
      return {
        data: [],
        pagination: { total_items: 0, total_pages: 0, page: 1, page_size: 20 },
        thongKe: { cho_cap1: 0, cho_cap2: 0 },
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
   * @param nam - Năm cần thống kê
   * @returns Thống kê cá nhân
   */
  async getThongKeCaNhan(nam?: number): Promise<IThongKeNghiPhepCaNhan> {
    try {
      const year = nam || new Date().getFullYear();
      
      // ✅ FIX: Backend GET /nghi-phep/thong-ke trả về format:
      // { nam, tong_ngay_nghi, tong_so_don, chi_tiet_loai: [{loai_nghi, tong_ngay, so_don}] }
      // KHÔNG phải { chi_tiet: { nghi_tuan, phep_nam, ... } }
      const response = await apiClient.get<IBackendResponse<{
        nam: number;
        tong_ngay_nghi: number;
        tong_so_don: number;
        chi_tiet_loai: Array<{
          loai_nghi: string;
          loai_nghi_ten: string;
          tong_ngay: number;
          so_don: number;
        }>;
      }>>(
        `/nghi-phep/thong-ke?nam=${year}`
      );
      
      const responseData = response.data;
      
      if (responseData.success && responseData.data) {
        const data = responseData.data;
        const chiTietLoai = data.chi_tiet_loai || [];
        
        // Helper: lấy tong_ngay theo loai_nghi
        const getNgay = (loai: string): number => {
          const found = chiTietLoai.find(c => c.loai_nghi === loai);
          return found?.tong_ngay || 0;
        };
        
        const nghiTuan = getNgay('NGHI_TUAN');
        const nghiTet = getNgay('NGHI_TET');
        const phepNam = getNgay('PHEP_NAM');
        const nghiOm = getNgay('NGHI_OM');
        const nghiLe = getNgay('NGHI_LE');
        const viecRieng = getNgay('VIEC_RIENG');
        const khongLuong = getNgay('KHONG_LUONG');
        const nghiBu = getNgay('NGHI_BU');
        const thaiSan = getNgay('THAI_SAN');
        const khac = getNgay('KHAC');
        
        return {
          nam: data.nam,
          tong_ngay_nghi: data.tong_ngay_nghi || 0,
          nghi_tuan: nghiTuan,
          nghi_tet: nghiTet,
          phep_nam_da_dung: phepNam,
          phep_nam_con_lai: 12 - phepNam, // Mặc định 12 ngày/năm
          nghi_om: nghiOm,
          nghi_le: nghiLe,
          nghi_khac: viecRieng + khongLuong + nghiBu + khac + thaiSan,
          cho_phe_duyet: 0, // Backend thong-ke chỉ đếm DA_PHE_DUYET, tính từ leaveList
          cho_cap2: 0,
        };
      }
      
      // Default nếu không có data
      return {
        nam: year,
        tong_ngay_nghi: 0,
        nghi_tuan: 0,
        nghi_tet: 0,
        phep_nam_da_dung: 0,
        phep_nam_con_lai: 12,
        nghi_om: 0,
        nghi_le: 0,
        nghi_khac: 0,
        cho_phe_duyet: 0,
        cho_cap2: 0,
      };
    } catch (error) {
      console.warn('getThongKeCaNhan error:', error);
      return {
        nam: nam || new Date().getFullYear(),
        tong_ngay_nghi: 0,
        nghi_tuan: 0,
        nghi_tet: 0,
        phep_nam_da_dung: 0,
        phep_nam_con_lai: 12,
        nghi_om: 0,
        nghi_le: 0,
        nghi_khac: 0,
        cho_phe_duyet: 0,
        cho_cap2: 0,
      };
    }
  }

  /**
   * Lấy tổng số ngày nghỉ đã duyệt trong tháng.
   *
   * @param thang - Tháng
   * @param nam - Năm
   * @returns Tổng ngày nghỉ
   */
  async getTongNgayNghiThang(thang: number, nam: number): Promise<number> {
    try {
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
   * @param filters - Filter và pagination params
   * @returns Danh sách đơn nghỉ
   */
  async getMyLeaves(filters?: INghiPhepFilterParams): Promise<{
    data: INghiPhepResponse[];
  }> {
    try {
      const queryParams = new URLSearchParams();

      if (filters?.loai_nghi) queryParams.append('loai_nghi', filters.loai_nghi);
      if (filters?.trang_thai) queryParams.append('trang_thai', filters.trang_thai);
      if (filters?.tu_ngay) queryParams.append('tu_ngay', filters.tu_ngay);
      if (filters?.den_ngay) queryParams.append('den_ngay', filters.den_ngay);
      if (filters?.thang) queryParams.append('thang', filters.thang.toString());
      if (filters?.nam) queryParams.append('nam', filters.nam.toString());

      const url = queryParams.toString()
        ? `/nghi-phep?${queryParams.toString()}`
        : '/nghi-phep';

      // ✅ FIX: Backend GET /nghi-phep trả về success_response(data=[...])
      // data là mảng trực tiếp, KHÔNG phải { items: [...], pagination: {...} }
      const response = await apiClient.get<IBackendResponse<INghiPhepResponse[]>>(url);
      
      const responseData = response.data;
      
      if (responseData.success && responseData.data) {
        // responseData.data là mảng INghiPhepResponse[] trực tiếp
        const items = Array.isArray(responseData.data) ? responseData.data : [];
        return { data: items };
      }
      
      return { data: [] };
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
   * v2.6: Backend tự động gán người phê duyệt theo quy trình 2 cấp.
   *
   * @param data - Dữ liệu bulk
   * @returns Kết quả tạo bulk
   */
  async createBulk(data: INghiPhepBulkCreateRequest): Promise<IBulkCreateResponse> {
    try {
      // ✅ FIX v3.1: Backend POST /nghi-phep/bulk giờ trả đúng NghiPhepBulkResponse:
      // { success: true, data: { tong_don_tao, danh_sach_id, ngay_da_ton_tai, nguoi_phe_duyet_id, message } }
      // Fallback: nếu backend cũ vẫn trả { so_don_da_tao } thì vẫn parse được
      const response = await apiClient.post<IBackendResponse<{
        tong_don_tao?: number;
        so_don_da_tao?: number;
        danh_sach_id?: string[];
        ngay_da_ton_tai?: string[];
        nguoi_phe_duyet_id?: string | null;
        message?: string;
      }>>(
        '/nghi-phep/bulk',
        data
      );
      
      if (response.data.success && response.data.data) {
        const d = response.data.data;
        return {
          // Ưu tiên tong_don_tao (schema mới), fallback so_don_da_tao (schema cũ)
          tong_don_tao: d.tong_don_tao ?? d.so_don_da_tao ?? 0,
          danh_sach_id: d.danh_sach_id ?? [],
          ngay_da_ton_tai: d.ngay_da_ton_tai ?? [],
        };
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
   * v2.6: Backend tự động xử lý đúng cấp:
   * - Nếu đơn đang CHO_PHE_DUYET → duyệt cấp 1
   * - Nếu đơn đang CHO_CAP2 → duyệt cấp 2
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
   * v2.6: Từ chối ở cấp nào thì đơn quay về TU_CHOI.
   *
   * ⚠️ LƯU Ý: Backend mong đợi field "ly_do_tu_choi" (không phải "ly_do")
   *
   * @param id - ID đơn nghỉ
   * @param data - Lý do từ chối (bắt buộc)
   * @returns Đơn nghỉ sau từ chối
   */
  async reject(id: string, data: ITuChoiNghiRequest): Promise<INghiPhepResponse> {
    try {
      const response = await apiClient.post<IBackendResponse<INghiPhepResponse>>(
        `/nghi-phep/${id}/tu-choi`,
        { ly_do_tu_choi: data.ly_do }
      );
      
      if (response.data.success && response.data.data) {
        return response.data.data;
      }
      
      throw new Error(response.data.message || 'Không thể từ chối đơn nghỉ');
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * v2.6: Phê duyệt hàng loạt.
   *
   * @param ids - Danh sách ID đơn nghỉ
   * @param ghiChu - Ghi chú (optional)
   * @returns Kết quả phê duyệt
   */
  async approveBulk(ids: string[], ghiChu?: string): Promise<{
    tong_phe_duyet: number;
    danh_sach_id: string[];
  }> {
    try {
      const response = await apiClient.post<IBackendResponse<{
        tong_phe_duyet: number;
        danh_sach_id: string[];
      }>>('/nghi-phep/phe-duyet-bulk', {
        don_nghi_ids: ids,
        ghi_chu: ghiChu,
      });
      
      if (response.data.success && response.data.data) {
        return response.data.data;
      }
      
      throw new Error(response.data.message || 'Không thể phê duyệt hàng loạt');
    } catch (error) {
      throw error as IApiError;
    }
  }

   /**
   * v2.6.2: Lấy chi tiết ngày nghỉ tháng bao gồm so_ngay_lam_viec.
   * 
   * Gọi API /nghi-phep/tong-ngay-nghi (backend tinh_tong_ngay_nghi_thang)
   * trả về object đầy đủ thay vì chỉ tổng ngày nghỉ.
   * 
   * Dùng cho trang danh-gia/page.tsx để hiện số ngày làm việc chính xác
   * khớp với cách backend tính trong bao_cao_xep_loai.py (KetQuaTinhDiem).
   *
   * @param thang - Tháng
   * @param nam - Năm
   * @returns Object chứa tong_ngay_nghi, so_ngay_trong_thang, so_ngay_lam_viec
   */
   async getTongNgayNghiThangChiTiet(thang: number, nam: number): Promise<{
    tong_ngay_nghi: number;
    so_ngay_trong_thang: number;
    so_ngay_lam_viec: number;
    // v3.1: Tạm tính (CHO_PHE_DUYET + DA_PHE_DUYET)
    tam_tinh_ngay_nghi: number;
    tam_tinh_ngay_lam_viec: number;
    tam_tinh_sp_duoc_giao: number;
    cho_duyet_ngay_nghi: number;
  }> {
    try {
      const response = await apiClient.get<IBackendResponse<{
        tong_ngay_nghi: number;
        so_ngay_trong_thang: number;
        so_ngay_lam_viec: number;
        sp_duoc_giao: number;
        chi_tiet: Record<string, number>;
        // v3.1 fields
        tam_tinh_ngay_nghi?: number;
        tam_tinh_ngay_lam_viec?: number;
        tam_tinh_sp_duoc_giao?: number;
        cho_duyet_ngay_nghi?: number;
      }>>(
        `/nghi-phep/tong-ngay-nghi?thang=${thang}&nam=${nam}`
      );
      
      if (response.data.success && response.data.data) {
        const data = response.data.data;
        const tongNghi = data.tong_ngay_nghi || 0;
        const soNgayThang = data.so_ngay_trong_thang || 0;
        const soNgayLV = data.so_ngay_lam_viec || 0;
        
        // v3.1: Tạm tính - fallback về chính thức nếu backend chưa trả
        const tamTinhNghi = data.tam_tinh_ngay_nghi ?? tongNghi;
        const tamTinhLV = data.tam_tinh_ngay_lam_viec ?? soNgayLV;
        const tamTinhSP = data.tam_tinh_sp_duoc_giao ?? (tamTinhLV * 96);
        const choDuyetNghi = data.cho_duyet_ngay_nghi ?? 0;
        
        return {
          tong_ngay_nghi: tongNghi,
          so_ngay_trong_thang: soNgayThang,
          so_ngay_lam_viec: soNgayLV,
          tam_tinh_ngay_nghi: tamTinhNghi,
          tam_tinh_ngay_lam_viec: tamTinhLV,
          tam_tinh_sp_duoc_giao: tamTinhSP,
          cho_duyet_ngay_nghi: choDuyetNghi,
        };
      }
      
      // Fallback: tính từ số ngày trong tháng
      const soNgay = new Date(nam, thang, 0).getDate();
      return {
        tong_ngay_nghi: 0,
        so_ngay_trong_thang: soNgay,
        so_ngay_lam_viec: soNgay,
        tam_tinh_ngay_nghi: 0,
        tam_tinh_ngay_lam_viec: soNgay,
        tam_tinh_sp_duoc_giao: soNgay * 96,
        cho_duyet_ngay_nghi: 0,
      };
    } catch (error) {
      console.warn('getTongNgayNghiThangChiTiet error:', error);
      const soNgay = new Date(nam, thang, 0).getDate();
      return {
        tong_ngay_nghi: 0,
        so_ngay_trong_thang: soNgay,
        so_ngay_lam_viec: soNgay,
        tam_tinh_ngay_nghi: 0,
        tam_tinh_ngay_lam_viec: soNgay,
        tam_tinh_sp_duoc_giao: soNgay * 96,
        cho_duyet_ngay_nghi: 0,
      };
    }
  }

}



// =============================================================================
// SINGLETON INSTANCE
// =============================================================================

export const leaveService = new LeaveService();
export default leaveService;