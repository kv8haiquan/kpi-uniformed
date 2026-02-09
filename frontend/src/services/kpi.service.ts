/**
 * src/services/kpi.service.ts
 * ===========================
 * Service xử lý các API calls liên quan đến Kê khai KPI và Phê duyệt.
 *
 * PHIÊN BẢN: 2.7.0 (31/01/2026)
 * 
 * CHANGELOG v2.7.0:
 * - ADD: getSpChuanList() - Lấy danh sách Sản phẩm chuẩn (SP1-SP4)
 * - ADD: Interface ISpChuan cho SP chuẩn
 * 
 * CHANGELOG v2.6.0:
 * - ADD: getKeKhaiByMonthWithPagination() - Lấy kê khai với pagination info
 * - ADD: getAllKeKhaiByMonth() - Lấy TẤT CẢ kê khai (loop qua các trang)
 * - FIX: Sửa submitKpi() sử dụng getAllKeKhaiByMonth thay vì getKeKhaiByMonth
 *
 * THAM CHIẾU BACKEND:
 * - ke_khai.py: Endpoints cho kê khai công việc
 * - phe_duyet.py: Endpoints cho phê duyệt
 * - danh_muc.py: Endpoints cho danh mục công việc, cấp độ
 * - sp_cong_viec_chuan.py: Endpoints cho SP chuẩn (v2.7.0)
 *
 * API ENDPOINTS (khớp 100% với Backend):
 *
 * KÊ KHAI CÔNG VIỆC (prefix: /ke-khai):
 *   - GET    /ke-khai/nguoi-phe-duyet        -> DS người phê duyệt (tự lấy từ token)
 *   - GET    /ke-khai                        -> DS kê khai (query: thang, nam, trang_thai, page, page_size)
 *   - GET    /ke-khai/{id}                   -> Chi tiết kê khai
 *   - POST   /ke-khai                        -> Tạo kê khai mới
 *   - PUT    /ke-khai/{id}                   -> Cập nhật kê khai
 *   - DELETE /ke-khai/{id}                   -> Xóa kê khai
 *   - POST   /ke-khai/{id}/gui-duyet         -> Gửi phê duyệt (payload: nguoi_phe_duyet_id)
 *   - GET    /ke-khai/thong-ke/thang         -> Thống kê kê khai theo tháng
 *
 * PHÊ DUYỆT (prefix: /phe-duyet):
 *   - GET    /phe-duyet/pending              -> DS kê khai chờ phê duyệt
 *   - POST   /phe-duyet/xu-ly                -> Phê duyệt/Từ chối hàng loạt
 *   - POST   /phe-duyet/{ke_khai_id}         -> Phê duyệt/Từ chối đơn lẻ
 *   - GET    /phe-duyet/thong-ke             -> Thống kê chờ duyệt
 *
 * DANH MỤC (prefix: /danh-muc):
 *   - GET /danh-muc/danh-muc-sp              -> DS công việc
 *   - GET /danh-muc/cap-do-phuc-tap          -> DS cấp độ phức tạp C1-C5
 *   - GET /danh-muc/nhom-cong-viec           -> DS nhóm công việc (distinct)
 *
 * SẢN PHẨM CHUẨN (v2.7.0):
 *   - GET /sp-cong-viec-chuan                -> DS SP chuẩn (SP1-SP4)
 */

import apiClient, { IApiError } from '@/lib/axios';
import {
  IKeKhaiCongViec,
  IKeKhaiBrief,
  IKeKhaiCreateRequest,
  IKeKhaiUpdateRequest,
  IKeKhaiFilterParams,
  IKeKhaiMonthSummary,
  IDanhMucCongViec,
  ICapDo,
  KpiStatus,
} from '@/types/kpi';
import { IDataResponse, IPaginatedResponse, IListResponse } from '@/types/api';

// =============================================================================
// CONSTANTS - v2.6.0
// =============================================================================

/**
 * Page size tối đa cho phép bởi Backend (ke_khai.py)
 * Dùng để load nhiều bản kê khai hơn trong 1 request
 */
const MAX_PAGE_SIZE = 100;

// =============================================================================
// INTERFACES CHO KÊ KHAI
// =============================================================================

/**
 * Response từ endpoint /ke-khai/nguoi-phe-duyet
 * Backend trả về theo cấp bậc của user:
 * - CC -> DS Phó ĐV cùng đơn vị
 * - PDV -> Trưởng ĐV cùng đơn vị
 * - TDV/PCCT -> Chi cục trưởng
 */
export interface INguoiPheDuyet {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string;
  don_vi_ten?: string;
  cap_bac?: string;
}

/**
 * Payload cho endpoint POST /ke-khai/{id}/gui-duyet
 */
export interface IGuiDuyetPayload {
  nguoi_phe_duyet_id: string;
}

/**
 * Response từ endpoint POST /ke-khai/{id}/gui-duyet
 */
export interface IGuiDuyetResponse {
  ke_khai_id: string;
  nguoi_phe_duyet_id: string;
  trang_thai_moi: string;
}

/**
 * Pagination params cho API calls - v2.6.0
 */
export interface IPaginationParams {
  page?: number;
  page_size?: number;
}

/**
 * Response với pagination info - v2.6.0
 */
export interface IPaginatedKeKhaiResponse {
  data: IKeKhaiBrief[];
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
  };
}

// =============================================================================
// INTERFACES CHO PHÊ DUYỆT (Leader View)
// Tham chiếu: phe_duyet.py
// =============================================================================

/**
 * Thông tin công chức trong pending list
 */
export interface ICongChucPendingInfo {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string;
  don_vi_id: string;
  don_vi_ten: string | null;
}

/**
 * Response từ GET /phe-duyet/pending
 * Bao gồm thông tin tự đánh giá của CC để Lãnh đạo xem xét
 */
export interface IKeKhaiPending {
  id: string;
  cong_chuc: ICongChucPendingInfo | null;
  thang: number;
  nam: number;
  ngay_thuc_hien: string | null;
  danh_muc_sp_id: string;
  danh_muc_ten: string | null;
  cap_do_ma: string | null;
  so_luong: number;
  he_so_thuc_te: number | null;
  mo_ta_cong_viec: string | null;
  is_doi_moi_sang_tao: boolean;
  ngay_deadline: string | null;
  ngay_hoan_thanh: string | null;
  // Tự đánh giá của CC (để LĐ tham khảo)
  tu_danh_gia_chat_luong: number;
  tu_danh_gia_tien_do: number;
  ghi_chu_tu_danh_gia: string | null;
  // Kết quả
  so_sp_goc_quy_doi: number | null;
  trang_thai: string;
  created_at: string;
}

/**
 * Filter params cho pending list
 */
export interface IPendingFilterParams {
  don_vi_id?: string;
  thang?: number;
  nam?: number;
  page?: number;
  page_size?: number;
}

/**
 * Enum action phê duyệt
 */
export enum PheDuyetAction {
  APPROVE = 'APPROVE',
  REJECT = 'REJECT',
}

/**
 * Payload cho POST /phe-duyet/xu-ly (xử lý hàng loạt)
 * Tham chiếu: PheDuyetBulkRequest trong phe_duyet.py
 */
export interface IPheDuyetBulkRequest {
  ke_khai_ids: string[];
  action: PheDuyetAction;
  so_loi_chat_luong?: number;
  so_loi_tien_do?: number;
  noi_dung_trao_doi?: string;
}

/**
 * Payload cho POST /phe-duyet/{id} (xử lý đơn lẻ)
 * Tham chiếu: PheDuyetRequest trong phe_duyet.py
 */
export interface IPheDuyetRequest {
  action: PheDuyetAction;
  so_loi_chat_luong?: number;
  so_loi_tien_do?: number;
  noi_dung_trao_doi?: string;
}

/**
 * Response từ POST /phe-duyet/xu-ly
 */
export interface IPheDuyetResponse {
  success: boolean;
  message: string;
  processed_count: number;
  ke_khai_ids: string[];
  trang_thai_moi: string;
  warnings?: string[];
}

/**
 * Response từ GET /phe-duyet/thong-ke
 */
export interface IPendingStats {
  tong_cho_duyet: number;
  tong_sp_quy_doi: number;
}

// =============================================================================
// INTERFACES CHO SẢN PHẨM CHUẨN - v2.7.0
// =============================================================================

/**
 * Sản phẩm chuẩn (SP1-SP4)
 * Endpoint: GET /sp-cong-viec-chuan
 */
export interface ISpChuan {
  id: string;
  ma_sp: string;        // SP1, SP2, SP3, SP4
  ten_sp: string;       // Tên đầy đủ
  mo_ta?: string;       // Mô tả
  thoi_gian_phut: number;
  he_so_quy_doi_sp1: number;
  is_sp_goc: boolean;
  is_active: boolean;
}

// =============================================================================
// KPI SERVICE
// =============================================================================

class KpiService {
  // ===========================================================================
  // NGƯỜI PHÊ DUYỆT - Endpoint: GET /ke-khai/nguoi-phe-duyet
  // Tham chiếu: ke_khai.py line 278-430
  // ===========================================================================

  /**
   * Lấy danh sách người phê duyệt phù hợp với cấp bậc của user hiện tại.
   * 
   * Backend tự động lấy thông tin user từ Token để xác định:
   * - Đơn vị của user
   * - Cấp bậc của user (CC, PDV, TDV, PCCT, CCT)
   * 
   * Logic nghiệp vụ (từ ke_khai.py):
   * - CC -> Trả về DS Phó ĐV cùng đơn vị
   * - PDV -> Trả về Trưởng ĐV cùng đơn vị
   * - TDV/PCCT -> Trả về Chi cục trưởng
   * - CCT -> Trả về [] (tự phê duyệt)
   *
   * Endpoint: GET /ke-khai/nguoi-phe-duyet
   * 
   * @returns Danh sách người phê duyệt phù hợp
   */
  async getNguoiPheDuyet(): Promise<INguoiPheDuyet[]> {
    try {
      const response = await apiClient.get<IDataResponse<INguoiPheDuyet[]>>(
        '/ke-khai/nguoi-phe-duyet'
      );

      return response.data.data;
    } catch (error) {
      // Nếu endpoint lỗi, trả về mảng rỗng để UI không crash
      console.warn('getNguoiPheDuyet error:', error);
      return [];
    }
  }

  // ===========================================================================
  // KÊ KHAI CÔNG VIỆC - Endpoint prefix: /ke-khai
  // Tham chiếu: ke_khai.py
  // ===========================================================================

  /**
   * Lấy danh sách kê khai theo tháng/năm.
   * Endpoint: GET /ke-khai?thang=X&nam=Y&trang_thai=...
   * 
   * ⚠️ LƯU Ý: Hàm này chỉ trả về data của 1 trang (mặc định 20 bản).
   * Nếu cần lấy TẤT CẢ bản kê khai, sử dụng getAllKeKhaiByMonth() hoặc 
   * getKeKhaiByMonthWithPagination() để tự xử lý pagination.
   *
   * @param thang - Tháng (1-12)
   * @param nam - Năm (>= 2025)
   * @param filters - Các filter bổ sung
   * @returns Danh sách kê khai (tối đa 1 trang)
   * @deprecated Sử dụng getAllKeKhaiByMonth() để lấy tất cả bản kê khai
   */
  async getKeKhaiByMonth(
    thang: number,
    nam: number,
    filters?: Partial<IKeKhaiFilterParams>
  ): Promise<IKeKhaiBrief[]> {
    try {
      const params = new URLSearchParams();
      params.append('thang', thang.toString());
      params.append('nam', nam.toString());

      if (filters?.trang_thai) {
        params.append('trang_thai', filters.trang_thai);
      }
      if (filters?.danh_muc_sp_id) {
        params.append('danh_muc_sp_id', filters.danh_muc_sp_id);
      }
      if (filters?.cap_do_id) {
        params.append('cap_do_id', filters.cap_do_id);
      }

      const response = await apiClient.get<IListResponse<IKeKhaiBrief>>(
        `/ke-khai?${params.toString()}`
      );

      return response.data.data;
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * [v2.6.0] Lấy danh sách kê khai theo tháng/năm VỚI PAGINATION INFO.
   * Endpoint: GET /ke-khai?thang=X&nam=Y&page=P&page_size=S
   * 
   * Khác với getKeKhaiByMonth():
   * - Trả về cả pagination object (total_items, total_pages)
   * - Cho phép truyền page và page_size
   * - Frontend có thể dùng để load tất cả các trang
   *
   * @param thang - Tháng (1-12)
   * @param nam - Năm (>= 2025)
   * @param pagination - Page và page_size (optional)
   * @param filters - Các filter bổ sung (optional)
   * @returns Data và pagination info
   */
  async getKeKhaiByMonthWithPagination(
    thang: number,
    nam: number,
    pagination?: IPaginationParams,
    filters?: Partial<IKeKhaiFilterParams>
  ): Promise<IPaginatedKeKhaiResponse> {
    try {
      const params = new URLSearchParams();
      params.append('thang', thang.toString());
      params.append('nam', nam.toString());

      // Pagination params
      if (pagination?.page) {
        params.append('page', pagination.page.toString());
      }
      if (pagination?.page_size) {
        params.append('page_size', pagination.page_size.toString());
      }

      // Filter params
      if (filters?.trang_thai) {
        params.append('trang_thai', filters.trang_thai);
      }
      if (filters?.danh_muc_sp_id) {
        params.append('danh_muc_sp_id', filters.danh_muc_sp_id);
      }
      if (filters?.cap_do_id) {
        params.append('cap_do_id', filters.cap_do_id);
      }

      // Backend trả về PaginatedResponse với structure:
      // { success: true, data: [...], pagination: { page, page_size, total_items, total_pages } }
      const response = await apiClient.get<IPaginatedResponse<IKeKhaiBrief>>(
        `/ke-khai?${params.toString()}`
      );

      return {
        data: response.data.data || [],
        pagination: response.data.pagination || {
          page: 1,
          page_size: 20,
          total_items: 0,
          total_pages: 0,
        },
      };
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * [v2.6.0] Lấy TẤT CẢ bản kê khai theo tháng/năm.
   * 
   * Hàm này tự động loop qua tất cả các trang để lấy đầy đủ data.
   * Sử dụng page_size = 100 (max) để giảm số request.
   * 
   * ✅ KHUYẾN NGHỊ: Sử dụng hàm này thay vì getKeKhaiByMonth() để đảm bảo
   * lấy được TẤT CẢ bản kê khai, không bị giới hạn 20 bản.
   *
   * @param thang - Tháng (1-12)
   * @param nam - Năm (>= 2025)
   * @param filters - Các filter bổ sung (optional)
   * @returns Tất cả bản kê khai trong tháng
   */
  async getAllKeKhaiByMonth(
    thang: number,
    nam: number,
    filters?: Partial<IKeKhaiFilterParams>
  ): Promise<IKeKhaiBrief[]> {
    const allKeKhai: IKeKhaiBrief[] = [];
    let currentPage = 1;
    let hasMorePages = true;

    try {
      while (hasMorePages) {
        const response = await this.getKeKhaiByMonthWithPagination(
          thang,
          nam,
          { page: currentPage, page_size: MAX_PAGE_SIZE },
          filters
        );

        // Thêm data vào list tổng
        allKeKhai.push(...response.data);

        // Kiểm tra còn trang nào không
        if (currentPage >= response.pagination.total_pages || response.data.length === 0) {
          hasMorePages = false;
        } else {
          currentPage++;
        }
      }

      return allKeKhai;
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Lấy thống kê kê khai theo tháng.
   * Endpoint: GET /ke-khai/thong-ke/thang?thang=X&nam=Y
   * Tham chiếu: ke_khai.py line 17
   *
   * @param thang - Tháng
   * @param nam - Năm
   * @returns Thông tin thống kê
   */
  async getMonthSummary(thang: number, nam: number): Promise<IKeKhaiMonthSummary> {
    try {
      const response = await apiClient.get<IDataResponse<IKeKhaiMonthSummary>>(
        `/ke-khai/thong-ke/thang?thang=${thang}&nam=${nam}`
      );

      return response.data.data;
    } catch (error) {
      // Nếu chưa có dữ liệu hoặc endpoint error, trả về default
      console.warn('getMonthSummary error:', error);
      const defaultSummary: IKeKhaiMonthSummary = {
        thang,
        nam,
        tong_ke_khai: 0,
        tong_nhap: 0,
        tong_cho_duyet: 0,
        tong_da_duyet: 0,
        tong_tu_choi: 0,
        tong_sp_quy_doi: 0,
        trang_thai_chung: KpiStatus.DRAFT,
      };
      return defaultSummary;
    }
  }

  /**
   * Lấy chi tiết 1 bản kê khai.
   * Endpoint: GET /ke-khai/{id}
   *
   * @param id - ID kê khai
   * @returns Chi tiết kê khai
   */
  async getKeKhaiById(id: string): Promise<IKeKhaiCongViec> {
    try {
      const response = await apiClient.get<IDataResponse<IKeKhaiCongViec>>(
        `/ke-khai/${id}`
      );

      return response.data.data;
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Tạo mới bản kê khai công việc.
   * Endpoint: POST /ke-khai
   *
   * Payload bao gồm các trường tự đánh giá:
   * - tu_danh_gia_chat_luong
   * - tu_danh_gia_tien_do
   * - ghi_chu_tu_danh_gia
   *
   * @param data - Dữ liệu kê khai
   * @returns Kê khai vừa tạo
   */
  async createKeKhai(data: IKeKhaiCreateRequest): Promise<IKeKhaiCongViec> {
    try {
      // Build payload đầy đủ
      const payload = {
        danh_muc_sp_id: data.danh_muc_sp_id,
        cap_do_id: data.cap_do_id,
        so_luong: data.so_luong,
        he_so_thuc_te: data.he_so_thuc_te ?? null,
        nguoi_phe_duyet_id: data.nguoi_phe_duyet_id ?? null,
        ngay_thuc_hien: data.ngay_thuc_hien ?? null,
        ngay_deadline: data.ngay_deadline ?? null,
        ngay_hoan_thanh: data.ngay_hoan_thanh ?? null,
        mo_ta_cong_viec: data.mo_ta_cong_viec ?? null,
        is_doi_moi_sang_tao: data.is_doi_moi_sang_tao ?? false,
        // Các trường tự đánh giá
        tu_danh_gia_chat_luong: data.tu_danh_gia_chat_luong ?? 0,
        tu_danh_gia_tien_do: data.tu_danh_gia_tien_do ?? 0,
        ghi_chu_tu_danh_gia: data.ghi_chu_tu_danh_gia ?? null,
      };

      const response = await apiClient.post<IDataResponse<IKeKhaiCongViec>>(
        '/ke-khai',
        payload
      );

      return response.data.data;
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Cập nhật bản kê khai công việc.
   * Endpoint: PUT /ke-khai/{id}
   *
   * Payload bao gồm các trường tự đánh giá:
   * - tu_danh_gia_chat_luong
   * - tu_danh_gia_tien_do
   * - ghi_chu_tu_danh_gia
   *
   * @param id - ID kê khai
   * @param data - Dữ liệu cập nhật
   * @returns Kê khai sau cập nhật
   */
  async updateKeKhai(id: string, data: IKeKhaiUpdateRequest): Promise<IKeKhaiCongViec> {
    try {
      // Build payload - chỉ gửi các trường có giá trị
      const payload: Record<string, unknown> = {};

      if (data.danh_muc_sp_id !== undefined) {
        payload.danh_muc_sp_id = data.danh_muc_sp_id;
      }
      if (data.cap_do_id !== undefined) {
        payload.cap_do_id = data.cap_do_id;
      }
      if (data.so_luong !== undefined) {
        payload.so_luong = data.so_luong;
      }
      if (data.he_so_thuc_te !== undefined) {
        payload.he_so_thuc_te = data.he_so_thuc_te;
      }
      if (data.nguoi_phe_duyet_id !== undefined) {
        payload.nguoi_phe_duyet_id = data.nguoi_phe_duyet_id;
      }
      if (data.ngay_thuc_hien !== undefined) {
        payload.ngay_thuc_hien = data.ngay_thuc_hien;
      }
      if (data.ngay_deadline !== undefined) {
        payload.ngay_deadline = data.ngay_deadline;
      }
      if (data.ngay_hoan_thanh !== undefined) {
        payload.ngay_hoan_thanh = data.ngay_hoan_thanh;
      }
      if (data.mo_ta_cong_viec !== undefined) {
        payload.mo_ta_cong_viec = data.mo_ta_cong_viec;
      }
      if (data.is_doi_moi_sang_tao !== undefined) {
        payload.is_doi_moi_sang_tao = data.is_doi_moi_sang_tao;
      }
      // Các trường tự đánh giá
      if (data.tu_danh_gia_chat_luong !== undefined) {
        payload.tu_danh_gia_chat_luong = data.tu_danh_gia_chat_luong;
      }
      if (data.tu_danh_gia_tien_do !== undefined) {
        payload.tu_danh_gia_tien_do = data.tu_danh_gia_tien_do;
      }
      if (data.ghi_chu_tu_danh_gia !== undefined) {
        payload.ghi_chu_tu_danh_gia = data.ghi_chu_tu_danh_gia;
      }

      const response = await apiClient.put<IDataResponse<IKeKhaiCongViec>>(
        `/ke-khai/${id}`,
        payload
      );

      return response.data.data;
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Xóa bản kê khai công việc.
   * Endpoint: DELETE /ke-khai/{id}
   *
   * Chỉ cho phép xóa khi trạng thái là NHÁP.
   *
   * @param id - ID kê khai
   */
  async deleteKeKhai(id: string): Promise<void> {
    try {
      await apiClient.delete(`/ke-khai/${id}`);
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Gửi một bản kê khai đi phê duyệt.
   * Endpoint: POST /ke-khai/{id}/gui-duyet
   * Tham chiếu: ke_khai.py line 1170-1291
   *
   * Chuyển trạng thái từ NHÁP -> CHỜ PHÊ DUYỆT.
   * 
   * YÊU CẦU: Phải truyền nguoi_phe_duyet_id trong payload.
   *
   * @param keKhaiId - ID kê khai cần gửi
   * @param nguoiPheDuyetId - ID người phê duyệt (bắt buộc)
   * @returns Response từ Backend
   */
  async submitKeKhaiSingle(
    keKhaiId: string,
    nguoiPheDuyetId: string
  ): Promise<IGuiDuyetResponse> {
    try {
      const payload: IGuiDuyetPayload = {
        nguoi_phe_duyet_id: nguoiPheDuyetId,
      };

      const response = await apiClient.post<IDataResponse<IGuiDuyetResponse>>(
        `/ke-khai/${keKhaiId}/gui-duyet`,
        payload
      );

      return response.data.data;
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Gửi nhiều bản kê khai đi phê duyệt.
   * Gọi endpoint POST /ke-khai/{id}/gui-duyet cho từng bản.
   *
   * @param keKhaiIds - Danh sách ID kê khai cần gửi
   * @param nguoiPheDuyetId - ID người phê duyệt (bắt buộc)
   * @returns Số lượng kê khai đã gửi thành công
   */
  async submitKpiMultiple(
    keKhaiIds: string[],
    nguoiPheDuyetId: string
  ): Promise<{ submitted_count: number; failed_count: number }> {
    let submittedCount = 0;
    let failedCount = 0;

    for (const id of keKhaiIds) {
      try {
        await this.submitKeKhaiSingle(id, nguoiPheDuyetId);
        submittedCount++;
      } catch (error) {
        console.error(`Failed to submit ke_khai ${id}:`, error);
        failedCount++;
        // Tiếp tục với các bản khác
      }
    }

    return { submitted_count: submittedCount, failed_count: failedCount };
  }

  /**
   * [v2.6.0 - UPDATED] Gửi tất cả bản kê khai NHÁP trong tháng đi phê duyệt.
   * 
   * ⚠️ FIX: Sử dụng getAllKeKhaiByMonth() để lấy TẤT CẢ bản kê khai,
   * không bị giới hạn 20 bản như trước.
   * 
   * Logic:
   * 1. Gọi getAllKeKhaiByMonth() để lấy TẤT CẢ kê khai trong tháng
   * 2. Lọc ra các bản có trạng thái NHÁP (NHAP)
   * 3. Duyệt qua từng bản nháp:
   *    - Kiểm tra bản nháp đã có nguoi_phe_duyet_id chưa
   *    - Nếu có, gọi submitKeKhaiSingle để gửi đi
   * 4. Trả về kết quả tổng hợp
   *
   * @param thang - Tháng (1-12)
   * @param nam - Năm (>= 2025)
   * @returns Kết quả: số bản đã gửi thành công và số bản thất bại
   */
  async submitKpi(
    thang: number,
    nam: number
  ): Promise<{ submitted_count: number; failed_count: number; skipped_count: number }> {
    let submittedCount = 0;
    let failedCount = 0;
    let skippedCount = 0;

    try {
      // FIX v2.6.0: Sử dụng getAllKeKhaiByMonth() thay vì getKeKhaiByMonth()
      // để lấy TẤT CẢ bản kê khai, không bị giới hạn 20 bản
      const keKhaiList = await this.getAllKeKhaiByMonth(thang, nam);

      // Bước 2: Lọc ra các bản có trạng thái NHÁP (NHAP hoặc DRAFT)
      const draftList = keKhaiList.filter(
        (item) => item.trang_thai === KpiStatus.DRAFT
      );

      if (draftList.length === 0) {
        console.warn('submitKpi: Không có bản kê khai nào ở trạng thái Nháp');
        return { submitted_count: 0, failed_count: 0, skipped_count: 0 };
      }

      // Bước 3: Duyệt qua từng bản nháp
      for (const item of draftList) {
        // Kiểm tra đã có người phê duyệt chưa
        if (!item.nguoi_phe_duyet_id) {
          console.warn(`submitKpi: Bản kê khai ${item.id} chưa có người phê duyệt, bỏ qua`);
          skippedCount++;
          continue;
        }

        try {
          // Gửi phê duyệt
          await this.submitKeKhaiSingle(item.id, item.nguoi_phe_duyet_id);
          submittedCount++;
        } catch (error) {
          console.error(`submitKpi: Lỗi khi gửi bản kê khai ${item.id}:`, error);
          failedCount++;
          // Tiếp tục với các bản khác
        }
      }

      return { submitted_count: submittedCount, failed_count: failedCount, skipped_count: skippedCount };
    } catch (error) {
      console.error('submitKpi: Lỗi khi lấy danh sách kê khai:', error);
      throw error as IApiError;
    }
  }

  // ===========================================================================
  // DANH MỤC CÔNG VIỆC - Endpoint prefix: /danh-muc
  // Tham chiếu: danh_muc.py
  // ===========================================================================

  /**
   * Lấy danh mục công việc.
   * Endpoint: GET /danh-muc/danh-muc-sp?is_active=true&nhom_cong_viec=...
   *
   * @param nhomCongViec - Filter theo nhóm công việc (optional)
   * @returns Danh sách công việc
   */
  async getDanhMucCongViec(nhomCongViec?: string): Promise<IDanhMucCongViec[]> {
    try {
      const params = new URLSearchParams();
      params.append('is_active', 'true');
      params.append('page_size', '100');

      if (nhomCongViec) {
        params.append('nhom_cong_viec', nhomCongViec);
      }

      const response = await apiClient.get<IPaginatedResponse<IDanhMucCongViec>>(
        `/danh-muc/danh-muc-sp?${params.toString()}`
      );

      return response.data.data;
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Lấy danh sách nhóm công việc (distinct).
   * Endpoint: GET /danh-muc/nhom-cong-viec
   *
   * @returns Danh sách tên nhóm
   */
  async getNhomCongViec(): Promise<string[]> {
    try {
      const response = await apiClient.get<IDataResponse<string[]>>(
        '/danh-muc/nhom-cong-viec'
      );

      return response.data.data;
    } catch (error) {
      throw error as IApiError;
    }
  }

  // ===========================================================================
  // CẤP ĐỘ PHỨC TẠP - Endpoint prefix: /danh-muc
  // Tham chiếu: danh_muc.py
  // ===========================================================================

  /**
   * Lấy danh sách cấp độ phức tạp (C1-C5).
   * Endpoint: GET /danh-muc/cap-do-phuc-tap?is_active=true
   *
   * @returns Danh sách cấp độ
   */
  async getCapDoPhucTap(): Promise<ICapDo[]> {
    try {
      const response = await apiClient.get<IDataResponse<ICapDo[]>>(
        '/danh-muc/cap-do-phuc-tap?is_active=true'
      );

      return response.data.data;
    } catch (error) {
      throw error as IApiError;
    }
  }

  // ===========================================================================
  // SẢN PHẨM CHUẨN - Endpoint: GET /sp-cong-viec-chuan
  // v2.7.0 - NEW
  // ===========================================================================

  /**
   * Lấy danh sách Sản phẩm chuẩn (SP1-SP4).
   * Endpoint: GET /sp-cong-viec-chuan
   *
   * Response:
   * [
   *   { id, ma_sp: "SP1", ten_sp: "Tờ khai HQ...", ... },
   *   { id, ma_sp: "SP2", ten_sp: "Văn bản hành chính...", ... },
   *   ...
   * ]
   *
   * @returns Danh sách SP chuẩn
   */
  async getSpChuanList(): Promise<ISpChuan[]> {
    try {
      const response = await apiClient.get('/sp-cong-viec-chuan');

      // Handle các format response khác nhau
      if (response.data?.data && Array.isArray(response.data.data)) {
        return response.data.data;
      }
      if (Array.isArray(response.data)) {
        return response.data;
      }

      console.warn('[kpiService] getSpChuanList: Unexpected response format');
      return [];
    } catch (error) {
      // Nếu API chưa có, trả về mảng rỗng để UI không crash
      console.warn('[kpiService] getSpChuanList error:', error);
      return [];
    }
  }

  // ===========================================================================
  // PHÊ DUYỆT - Endpoint prefix: /phe-duyet
  // Tham chiếu: phe_duyet.py
  // ===========================================================================

  /**
   * Lấy danh sách kê khai chờ phê duyệt.
   * Endpoint: GET /phe-duyet/pending
   *
   * Logic phân quyền (từ phe_duyet.py):
   * - Admin/CCT: Thấy tất cả
   * - Lãnh đạo thường: Chỉ thấy những bài mình được gán làm người phê duyệt
   *
   * @param params - Filter và pagination params
   * @returns Danh sách kê khai chờ duyệt (có pagination)
   */
  async getPendingList(
    params?: IPendingFilterParams
  ): Promise<{ data: IKeKhaiPending[]; pagination: { page: number; page_size: number; total_items: number; total_pages: number } }> {
    try {
      const queryParams = new URLSearchParams();

      if (params?.page) {
        queryParams.append('page', params.page.toString());
      }
      if (params?.page_size) {
        queryParams.append('page_size', params.page_size.toString());
      }
      if (params?.don_vi_id) {
        queryParams.append('don_vi_id', params.don_vi_id);
      }
      if (params?.thang) {
        queryParams.append('thang', params.thang.toString());
      }
      if (params?.nam) {
        queryParams.append('nam', params.nam.toString());
      }

      const url = queryParams.toString()
        ? `/phe-duyet/pending?${queryParams.toString()}`
        : '/phe-duyet/pending';

      const response = await apiClient.get<IPaginatedResponse<IKeKhaiPending>>(url);

      return {
        data: response.data.data,
        pagination: response.data.pagination,
      };
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Xử lý phê duyệt/từ chối hàng loạt.
   * Endpoint: POST /phe-duyet/xu-ly
   *
   * APPROVE: Cập nhật trạng thái → DA_PHE_DUYET, lưu số lỗi chốt
   * REJECT: Cập nhật trạng thái → TU_CHOI (CC có thể sửa và gửi lại)
   *
   * @param payload - Dữ liệu phê duyệt (ke_khai_ids, action, so_loi_*, noi_dung_trao_doi)
   * @returns Kết quả xử lý
   */
  async processPheDuyet(payload: IPheDuyetBulkRequest): Promise<IPheDuyetResponse> {
    try {
      const response = await apiClient.post<IDataResponse<IPheDuyetResponse>>(
        '/phe-duyet/xu-ly',
        payload
      );

      return response.data.data;
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Xử lý phê duyệt/từ chối đơn lẻ.
   * Endpoint: POST /phe-duyet/{ke_khai_id}
   *
   * @param keKhaiId - ID kê khai cần xử lý
   * @param payload - Dữ liệu phê duyệt
   * @returns Kết quả xử lý
   */
  async processPheDuyetSingle(
    keKhaiId: string,
    payload: IPheDuyetRequest
  ): Promise<{ ke_khai_id: string; action: string; trang_thai_moi: string }> {
    try {
      const response = await apiClient.post<
        IDataResponse<{ ke_khai_id: string; action: string; trang_thai_moi: string }>
      >(`/phe-duyet/${keKhaiId}`, payload);

      return response.data.data;
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Lấy thống kê kê khai chờ phê duyệt.
   * Endpoint: GET /phe-duyet/thong-ke
   *
   * @returns Thống kê (tổng chờ duyệt, tổng SP quy đổi)
   */
  async getPendingStats(): Promise<IPendingStats> {
    try {
      const response = await apiClient.get<IDataResponse<IPendingStats>>(
        '/phe-duyet/thong-ke'
      );

      return response.data.data;
    } catch (error) {
      // Nếu lỗi, trả về default
      console.warn('getPendingStats error:', error);
      return {
        tong_cho_duyet: 0,
        tong_sp_quy_doi: 0,
      };
    }
  }

  async getPendingApprovals(thang: number, nam: number) {
    const response = await apiClient.get('/phe-duyet/pending', {
      params: { thang, nam }
    });
    return {
      data: response.data.success ? response.data.data : []
    };
  }
  
  async processApproval(
    keKhaiId: string,
    action: 'APPROVE' | 'REJECT',
    soLoiChatLuong?: number,
    soLoiTienDo?: number,
    lyDo?: string
  ) {
    const response = await apiClient.post('/phe-duyet/xu-ly', {
      ke_khai_id: keKhaiId,
      action,
      so_loi_chat_luong: soLoiChatLuong,
      so_loi_tien_do: soLoiTienDo,
      y_kien: lyDo
    });
    return response.data;
  }
  
  async bulkApprove(keKhaiIds: string[]) {
    const response = await apiClient.post('/phe-duyet/xu-ly-bulk', {
      ke_khai_ids: keKhaiIds,
      action: 'APPROVE'
    });
    return response.data;
  }
}

// =============================================================================
// SINGLETON INSTANCE
// =============================================================================

/**
 * Singleton instance của KpiService.
 */
export const kpiService = new KpiService();

export default kpiService;