/**
 * src/services/assessment.service.ts
 * ====================================
 * Service xử lý các API calls cho Module Đánh giá KPI.
 *
 * Tham chiếu: API_SPECS.md - Chapter 8 (Đánh giá tháng)
 * Version: 2.5 - Graceful 404 Handling
 *
 * ENDPOINTS:
 * - GET  /danh-gia/thang/{thang}/nam/{nam}     -> Lấy đánh giá tháng của bản thân
 * - POST /danh-gia/tu-danh-gia                  -> Tự đánh giá TC chung
 * - PUT  /danh-gia/{id}/tieu-chi-chung          -> Cập nhật TC chung (khi chưa duyệt)
 * - GET  /danh-gia/don-vi/{id}/thang/{t}/nam/{n} -> DS đánh giá đơn vị (LĐ)
 *
 * ⚠️ QUAN TRỌNG - Graceful 404 Handling:
 * Khi API trả về 404 (chưa có bản ghi đánh giá), service sẽ:
 * 1. KHÔNG throw error
 * 2. Trả về object mặc định với flag `is_new_record = true`
 * 3. Tự động tính KPI Target dựa trên ngày nghỉ (nếu có)
 */

import apiClient, { IApiError, isApiError } from '@/lib/axios';
import { leaveService } from './leave.service';
import {
  IDanhGiaThangResponse,
  ITuDanhGiaRequest,
  ITieuChiChungResponse,
  TrangThaiDanhGia,
  MucXepLoai,
  TIEU_CHI_CHUNG,
} from '@/types/assessment';

// =============================================================================
// RESPONSE INTERFACES (Khớp với Backend success_response)
// =============================================================================

interface IBackendResponse<T> {
  success: boolean;
  data: T;
  message: string;
}

// =============================================================================
// HELPER: Tính số ngày trong tháng
// =============================================================================

function getDaysInMonth(thang: number, nam: number): number {
  return new Date(nam, thang, 0).getDate();
}

// =============================================================================
// HELPER: Tạo object đánh giá mặc định (khi chưa có bản ghi)
// =============================================================================

/**
 * Tạo object đánh giá mặc định cho tháng mới.
 * Được gọi khi API trả về 404 (chưa có bản ghi).
 *
 * @param thang - Tháng
 * @param nam - Năm
 * @param soNgayNghi - Số ngày nghỉ đã duyệt (từ API nghỉ phép)
 * @returns Object đánh giá mặc định với is_new_record = true
 */
function createDefaultDanhGia(
  thang: number,
  nam: number,
  soNgayNghi: number = 0
): IDanhGiaThangResponse {
  const soNgayTrongThang = getDaysInMonth(thang, nam);
  const soNgayLamViec = Math.max(0, soNgayTrongThang - soNgayNghi);
  
  // Công thức: SP được giao = Ngày làm việc × 8 giờ × 12 SP/giờ
  const soSpDuocGiao = soNgayLamViec * 8 * 12;

  // Tạo danh sách tiêu chí chung mặc định (chưa chấm điểm)
  const tieuChiChungDefault: ITieuChiChungResponse[] = [];
  TIEU_CHI_CHUNG.forEach((nhom) => {
    nhom.tieuChi.forEach((tc) => {
      tieuChiChungDefault.push({
        ma_tieu_chi: tc.ma,
        ten_tieu_chi: tc.ten,
        diem_toi_da: tc.diemToiDa,
        diem_tu_cham: null,      // Chưa chấm
        diem_phe_duyet: null,    // Chưa duyệt
        ghi_chu: null,
        da_phe_duyet: false,
      });
    });
  });

  return {
    // ✅ Flag quan trọng: Đánh dấu đây là bản ghi MỚI (chưa tồn tại trong DB)
    id: '',  // Empty = chưa có ID
    is_new_record: true,
    
    cong_chuc: {
      id: '',
      ma_cc: '',
      ho_ten: '',
      is_lanh_dao: false,
    },
    
    thang,
    nam,
    
    // Thông tin ngày làm việc (đã tính)
    so_ngay_trong_thang: soNgayTrongThang,
    so_ngay_nghi_phep: soNgayNghi,
    so_ngay_lam_viec: soNgayLamViec,
    
    // SP được giao (Target)
    so_sp_goc_duoc_giao: soSpDuocGiao,
    
    // Kết quả kê khai (chưa có)
    tong_sp_hoan_thanh: 0,
    tong_sp_chat_luong: 0,
    tong_sp_tien_do: 0,
    
    // Điểm số (chưa có)
    diem_tieu_chi_chung: 0,
    diem_kpi: 0,
    diem_kpi_quy_doi: 0,
    diem_chi_tiet: {
      a_so_luong: 0,
      b_chat_luong: 0,
      c_tien_do: 0,
    },
    diem_tong: 0,
    
    // Xếp loại (chưa có)
    muc_xep_loai_tu_dong: null,
    muc_xep_loai_de_xuat: null,
    muc_xep_loai_chinh_thuc: null,
    
    // Trạng thái = CHỜ TỰ ĐÁNH GIÁ
    trang_thai: TrangThaiDanhGia.CHO_TU_DANH_GIA,
    
    // Tiêu chí chung (chưa chấm)
    tieu_chi_chung: tieuChiChungDefault,
    
    // Không phải lãnh đạo (sẽ được cập nhật từ user)
    is_lanh_dao: false,
    
    // Timestamps
    created_at: '',
    updated_at: null,
  };
}

// =============================================================================
// ASSESSMENT SERVICE CLASS
// =============================================================================

class AssessmentService {
  /**
   * Lấy đánh giá KPI tháng của bản thân.
   *
   * ⚠️ GRACEFUL 404 HANDLING:
   * - Nếu API trả về 404 (chưa có bản ghi), service sẽ:
   *   1. Gọi API lấy tổng ngày nghỉ tháng
   *   2. Tạo object mặc định với `is_new_record = true`
   *   3. Tính KPI Target dựa trên ngày nghỉ
   * - KHÔNG throw error, KHÔNG trả về null
   *
   * @param thang - Tháng (1-12)
   * @param nam - Năm
   * @returns Đánh giá tháng (hoặc object mặc định nếu chưa có)
   */
  async getDanhGiaThang(thang: number, nam: number): Promise<IDanhGiaThangResponse> {
    try {
      // ✅ FIX v2.5.6: Đúng endpoint Backend là /tieu-chi/thang/{t}/nam/{n}
      const response = await apiClient.get<IBackendResponse<IDanhGiaThangResponse>>(
        `/danh-gia/tieu-chi/thang/${thang}/nam/${nam}`
      );

      if (response.data.success && response.data.data) {
        const data = response.data.data;
        
        // Ensure all required fields have defaults + mark as existing record
        return {
          ...data,
          is_new_record: false, // ✅ Đây là bản ghi đã tồn tại
          so_ngay_lam_viec: data.so_ngay_lam_viec || 0,
          so_ngay_nghi_phep: data.so_ngay_nghi_phep || 0,
          so_ngay_trong_thang: data.so_ngay_trong_thang || getDaysInMonth(thang, nam),
          so_sp_goc_duoc_giao: data.so_sp_goc_duoc_giao || 0,
          tong_sp_hoan_thanh: data.tong_sp_hoan_thanh || 0,
          tong_sp_chat_luong: data.tong_sp_chat_luong || 0,
          tong_sp_tien_do: data.tong_sp_tien_do || 0,
          diem_tieu_chi_chung: data.diem_tieu_chi_chung || 0,
          diem_kpi: data.diem_kpi || 0,
          diem_kpi_quy_doi: data.diem_kpi_quy_doi || 0,
          diem_tong: data.diem_tong || 0,
          diem_chi_tiet: data.diem_chi_tiet || {
            a_so_luong: 0,
            b_chat_luong: 0,
            c_tien_do: 0,
          },
          tieu_chi_chung: data.tieu_chi_chung || [],
          trang_thai: data.trang_thai || TrangThaiDanhGia.CHUA_DANH_GIA,
          is_lanh_dao: data.is_lanh_dao || false,
        };
      }

      // API trả về success nhưng không có data => Tạo mặc định
      return await this.createDefaultWithLeaveData(thang, nam);
      
    } catch (error: any) {
      // ✅ GRACEFUL 404 HANDLING
      // Kiểm tra nhiều cách để detect 404
      const is404 = 
        error?.response?.status === 404 ||
        error?.status === 404 ||
        error?.message?.includes('404') ||
        error?.message?.includes('NOT_FOUND') ||
        error?.message?.includes('Không tìm thấy');

      if (is404) {
        console.info(`[AssessmentService] Tháng ${thang}/${nam} chưa có bản ghi đánh giá. Tạo mặc định.`);
        return await this.createDefaultWithLeaveData(thang, nam);
      }

      // Lỗi khác => throw
      throw error as IApiError;
    }
  }

  /**
   * Tạo object mặc định và lấy dữ liệu ngày nghỉ từ API.
   * @private
   */
  private async createDefaultWithLeaveData(thang: number, nam: number): Promise<IDanhGiaThangResponse> {
    let soNgayNghi = 0;
    
    try {
      // Gọi API lấy tổng ngày nghỉ đã duyệt trong tháng
      soNgayNghi = await leaveService.getTongNgayNghiThang(thang, nam);
    } catch (leaveError) {
      // Nếu không lấy được ngày nghỉ, dùng 0
      console.warn('[AssessmentService] Không lấy được ngày nghỉ, dùng mặc định 0:', leaveError);
    }

    return createDefaultDanhGia(thang, nam, soNgayNghi);
  }

  /**
   * Tự đánh giá tiêu chí chung (30 điểm).
   *
   * Payload:
   * {
   *   "thang": 1, "nam": 2026,
   *   "tieu_chi": [
   *     { "ma_tieu_chi": "1.1", "diem_tu_cham": 5.0 },
   *     { "ma_tieu_chi": "3.1", "diem_tu_cham": 2.5, "ghi_chu": "Sáng kiến..." }
   *   ]
   * }
   *
   * @param data - Request tự đánh giá
   * @returns Đánh giá tháng sau khi cập nhật
   */
  async tuDanhGia(data: ITuDanhGiaRequest): Promise<IDanhGiaThangResponse> {
    try {
      const response = await apiClient.post<IBackendResponse<IDanhGiaThangResponse>>(
        '/danh-gia/tu-danh-gia',
        data
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.message || 'Không thể lưu tự đánh giá');
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Cập nhật tiêu chí chung (khi chưa được phê duyệt).
   *
   * @param danhGiaId - ID đánh giá tháng
   * @param tieuChi - Danh sách tiêu chí cần cập nhật
   * @returns Đánh giá tháng sau khi cập nhật
   */
  async capNhatTieuChiChung(
    danhGiaId: string,
    tieuChi: Array<{ ma_tieu_chi: string; diem_tu_cham: number; ghi_chu?: string }>
  ): Promise<IDanhGiaThangResponse> {
    try {
      const response = await apiClient.put<IBackendResponse<IDanhGiaThangResponse>>(
        `/danh-gia/${danhGiaId}/tieu-chi-chung`,
        { tieu_chi: tieuChi }
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.message || 'Không thể cập nhật tiêu chí chung');
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Lấy chi tiết một đánh giá theo ID.
   *
   * @param id - ID đánh giá
   * @returns Chi tiết đánh giá
   */
  async getDanhGiaById(id: string): Promise<IDanhGiaThangResponse> {
    try {
      const response = await apiClient.get<IBackendResponse<IDanhGiaThangResponse>>(
        `/danh-gia/${id}`
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error('Không tìm thấy đánh giá');
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Lấy danh sách đánh giá đơn vị theo tháng (dành cho Lãnh đạo).
   *
   * @param donViId - ID đơn vị
   * @param thang - Tháng
   * @param nam - Năm
   * @returns Danh sách đánh giá
   */
  async getDanhGiaDonVi(
    donViId: string,
    thang: number,
    nam: number
  ): Promise<IDanhGiaThangResponse[]> {
    try {
      const response = await apiClient.get<IBackendResponse<{ items: IDanhGiaThangResponse[] }>>(
        `/danh-gia/don-vi/${donViId}/thang/${thang}/nam/${nam}`
      );

      if (response.data.success && response.data.data) {
        return response.data.data.items || [];
      }

      return [];
    } catch (error) {
      throw error as IApiError;
    }
  }

  /**
   * Lấy tổng hợp đánh giá Chi cục theo tháng (CCT, Phó CCT, TCCB).
   *
   * @param thang - Tháng
   * @param nam - Năm
   * @returns Tổng hợp đánh giá
   */
  async getTongHopChiCuc(
    thang: number,
    nam: number
  ): Promise<{
    thong_ke: {
      tong_cc: number;
      da_danh_gia: number;
      chua_danh_gia: number;
      muc_a: number;
      muc_b: number;
      muc_c: number;
      muc_d: number;
      muc_e: number;
    };
    danh_sach: IDanhGiaThangResponse[];
  }> {
    try {
      const response = await apiClient.get<IBackendResponse<{
        thong_ke: any;
        items: IDanhGiaThangResponse[];
      }>>(
        `/danh-gia/tong-hop/thang/${thang}/nam/${nam}`
      );

      if (response.data.success && response.data.data) {
        return {
          thong_ke: response.data.data.thong_ke || {
            tong_cc: 0, da_danh_gia: 0, chua_danh_gia: 0,
            muc_a: 0, muc_b: 0, muc_c: 0, muc_d: 0, muc_e: 0,
          },
          danh_sach: response.data.data.items || [],
        };
      }

      return {
        thong_ke: {
          tong_cc: 0, da_danh_gia: 0, chua_danh_gia: 0,
          muc_a: 0, muc_b: 0, muc_c: 0, muc_d: 0, muc_e: 0,
        },
        danh_sach: [],
      };
    } catch (error) {
      throw error as IApiError;
    }
  }
}

// =============================================================================
// SINGLETON INSTANCE
// =============================================================================

export const assessmentService = new AssessmentService();
export default assessmentService;