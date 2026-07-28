/**
 * src/services/bao-cao-xep-loai.service.ts
 * =========================================
 * Service gọi API cho Module Báo cáo Xếp loại Chất lượng Công chức.
 * 
 * Version: 1.0.0 (28/01/2026)
 */

import apiClient from '@/lib/axios';
import {
  IBaoCaoXepLoai,
  IBaoCaoXepLoaiSummary,
  IChiTietXepLoai,
  IDeXuatXepLoaiRequest,
  IQuyetDinhXepLoaiRequest,
  IPheDuyetBaoCaoRequest,
  IGuiDuyetResponse,
  IPheDuyetResponse,
  IThongKeXepLoai,
  ITieuChiChungBrief,
} from '@/types/bao-cao-xep-loai';

// =============================================================================
// CONSTANTS
// =============================================================================

const BASE_URL = '/bao-cao-xep-loai';

// =============================================================================
// SERVICE CLASS
// =============================================================================

class BaoCaoXepLoaiService {
  // ===========================================================================
  // ĐỘI TRƯỞNG APIs
  // ===========================================================================

  /**
   * Lấy/Tạo báo cáo xếp loại của đơn vị theo tháng/năm.
   * Nếu chưa có báo cáo → Backend tự động tạo mới với dữ liệu từ hệ thống.
   * 
   * API: GET /bao-cao-xep-loai/don-vi/thang/{thang}/nam/{nam}
   * Quyền: Đội trưởng (TRUONG_DON_VI)
   */
  async getBaoCaoDonVi(thang: number, nam: number): Promise<IBaoCaoXepLoai | null> {
    try {
      const response = await apiClient.get(`${BASE_URL}/don-vi/thang/${thang}/nam/${nam}`);
      if (response.data.success) {
        return response.data.data;
      }
      return null;
    } catch (error: any) {
      console.error('[BaoCaoXepLoai] Error getting bao cao don vi:', error);
      throw error;
    }
  }

  /**
   * Điều chỉnh xếp loại đề xuất cho 1 công chức.
   * 
   * API: PUT /bao-cao-xep-loai/chi-tiet/{id}/de-xuat
   * Quyền: Đội trưởng (TRUONG_DON_VI)
   * 
   * @param chiTietId ID chi tiết xếp loại
   * @param data Dữ liệu đề xuất
   */
  async deXuatXepLoai(
    chiTietId: string,
    data: IDeXuatXepLoaiRequest
  ): Promise<IChiTietXepLoai | null> {
    try {
      const response = await apiClient.put(`${BASE_URL}/chi-tiet/${chiTietId}/de-xuat`, data);
      if (response.data.success) {
        return response.data.data;
      }
      throw new Error(response.data.error?.message || 'Lỗi cập nhật đề xuất');
    } catch (error: any) {
      console.error('[BaoCaoXepLoai] Error de xuat xep loai:', error);
      throw error;
    }
  }

  /**
   * Gửi báo cáo lên CCT phê duyệt.
   * 
   * API: POST /bao-cao-xep-loai/{id}/gui-duyet
   * Quyền: Đội trưởng (TRUONG_DON_VI)
   * 
   * @param baoCaoId ID báo cáo
   */
  async guiDuyet(baoCaoId: string): Promise<IGuiDuyetResponse> {
    try {
      const response = await apiClient.post(`${BASE_URL}/${baoCaoId}/gui-duyet`);
      if (response.data.success) {
        return {
          ...response.data.data,
          warnings: response.data.warnings || [],
        };
      }
      throw new Error(response.data.error?.message || 'Lỗi gửi duyệt');
    } catch (error: any) {
      console.error('[BaoCaoXepLoai] Error gui duyet:', error);
      throw error;
    }
  }

  // ===========================================================================
  // CHI CỤC TRƯỞNG APIs
  // ===========================================================================

  /**
   * Lấy danh sách báo cáo chờ phê duyệt.
   * 
   * API: GET /bao-cao-xep-loai/cho-phe-duyet
   * Quyền: CCT (CHI_CUC_TRUONG)
   */
  async getChoPeDuyet(thang?: number, nam?: number): Promise<IBaoCaoXepLoaiSummary[]> {
    try {
      const params: Record<string, any> = {};
      if (thang) params.thang = thang;
      if (nam) params.nam = nam;

      const response = await apiClient.get(`${BASE_URL}/cho-phe-duyet`, { params });
      if (response.data.success) {
        return response.data.data || [];
      }
      return [];
    } catch (error: any) {
      console.error('[BaoCaoXepLoai] Error getting cho phe duyet:', error);
      return [];
    }
  }

  /**
   * Lấy chi tiết 1 báo cáo.
   * 
   * API: GET /bao-cao-xep-loai/{id}
   * Quyền: CCT, Đội trưởng (báo cáo đơn vị mình)
   */
  async getBaoCaoChiTiet(baoCaoId: string): Promise<IBaoCaoXepLoai | null> {
    try {
      const response = await apiClient.get(`${BASE_URL}/${baoCaoId}`);
      if (response.data.success) {
        return response.data.data;
      }
      return null;
    } catch (error: any) {
      console.error('[BaoCaoXepLoai] Error getting bao cao chi tiet:', error);
      throw error;
    }
  }

  /**
   * CCT điều chỉnh xếp loại quyết định cho 1 công chức.
   * 
   * API: PUT /bao-cao-xep-loai/chi-tiet/{id}/quyet-dinh
   * Quyền: CCT (CHI_CUC_TRUONG)
   */
  async quyetDinhXepLoai(
    chiTietId: string,
    data: IQuyetDinhXepLoaiRequest
  ): Promise<IChiTietXepLoai | null> {
    try {
      const response = await apiClient.put(`${BASE_URL}/chi-tiet/${chiTietId}/quyet-dinh`, data);
      if (response.data.success) {
        return response.data.data;
      }
      throw new Error(response.data.error?.message || 'Lỗi cập nhật quyết định');
    } catch (error: any) {
      console.error('[BaoCaoXepLoai] Error quyet dinh xep loai:', error);
      throw error;
    }
  }

  /**
   * CCT phê duyệt hoặc từ chối báo cáo.
   * 
   * API: POST /bao-cao-xep-loai/{id}/phe-duyet
   * Quyền: CCT (CHI_CUC_TRUONG)
   */
  async pheDuyet(
    baoCaoId: string,
    data: IPheDuyetBaoCaoRequest
  ): Promise<IPheDuyetResponse> {
    try {
      const response = await apiClient.post(`${BASE_URL}/${baoCaoId}/phe-duyet`, data);
      if (response.data.success) {
        return response.data.data;
      }
      throw new Error(response.data.error?.message || 'Lỗi phê duyệt');
    } catch (error: any) {
      console.error('[BaoCaoXepLoai] Error phe duyet:', error);
      throw error;
    }
  }

  // ===========================================================================
  // THỐNG KÊ APIs
  // ===========================================================================

  /**
   * Lấy thống kê xếp loại toàn Chi cục.
   * 
   * API: GET /bao-cao-xep-loai/thong-ke/thang/{thang}/nam/{nam}
   * Quyền: CCT, Phó CCT
   */
  async getThongKe(thang: number, nam: number): Promise<IThongKeXepLoai | null> {
    try {
      const response = await apiClient.get(`${BASE_URL}/thong-ke/thang/${thang}/nam/${nam}`);
      if (response.data.success) {
        return response.data.data;
      }
      return null;
    } catch (error: any) {
      console.error('[BaoCaoXepLoai] Error getting thong ke:', error);
      return null;
    }
  }

  // ===========================================================================
  // ĐIỂM TIÊU CHÍ CHUNG — Điều chỉnh "Đánh giá tháng" (CCT/LĐ)
  // ===========================================================================

  /**
   * Lấy danh sách báo cáo xếp loại toàn Chi cục theo tháng/năm.
   *
   * API: GET /bao-cao-xep-loai/danh-sach/thang/{thang}/nam/{nam}?trang_thai=
   * Quyền: CCT/PCCT/can_view_all_units
   */
  async getDanhSach(thang: number, nam: number, trangThai?: string): Promise<IBaoCaoXepLoai[]> {
    try {
      const params: Record<string, string> = {};
      if (trangThai) params.trang_thai = trangThai;
      const response = await apiClient.get(`${BASE_URL}/danh-sach/thang/${thang}/nam/${nam}`, { params });
      const d = response.data;
      if (Array.isArray(d)) return d;
      if (d?.data?.danh_sach && Array.isArray(d.data.danh_sach)) return d.data.danh_sach;
      if (d?.data && Array.isArray(d.data)) return d.data;
      if (d?.danh_sach && Array.isArray(d.danh_sach)) return d.danh_sach;
      return [];
    } catch (error) {
      console.error('[BaoCaoXepLoai] Error getting danh sach:', error);
      return [];
    }
  }

  /**
   * Lấy chi tiết tiêu chí chung của 1 công chức trong tháng (để sửa điểm).
   *
   * API: GET /danh-gia/tieu-chi/cong-chuc/{congChucId}/thang/{thang}/nam/{nam}
   * Quyền: CCT/PCCT xem mọi CC; LĐ đơn vị xem CC cùng đơn vị.
   */
  async getTieuChiChung(
    congChucId: string,
    thang: number,
    nam: number
  ): Promise<ITieuChiChungBrief | null> {
    try {
      const response = await apiClient.get(
        `/danh-gia/tieu-chi/cong-chuc/${congChucId}/thang/${thang}/nam/${nam}`
      );
      return response.data?.data || null;
    } catch {
      return null;
    }
  }

  /**
   * Điều chỉnh điểm "Đánh giá tháng" (override) theo từng tiêu chí.
   * diem_danh_gia_thang = null → gỡ điều chỉnh dòng đó (về điểm Trưởng duyệt).
   *
   * API: POST /danh-gia/{danhGiaThangId}/dieu-chinh-danh-gia-thang
   * Quyền: CCT/PCCT (mọi ĐV), TDV/PDV (cùng ĐV). Chỉ khi báo cáo chưa chốt.
   */
  async dieuChinhDanhGiaThang(
    danhGiaThangId: string,
    tieuChi: { ma_tieu_chi: string; diem_danh_gia_thang: number | null }[]
  ): Promise<void> {
    await apiClient.post(`/danh-gia/${danhGiaThangId}/dieu-chinh-danh-gia-thang`, { tieu_chi: tieuChi });
  }

  // ===========================================================================
  // HELPER METHODS
  // ===========================================================================

  /**
   * Kiểm tra tỷ lệ loại A có vượt 20% loại B không.
   */
  checkTyLeA(soLoaiA: number, soLoaiB: number): boolean {
    if (soLoaiB === 0) return soLoaiA > 0;
    return soLoaiA > 0.2 * soLoaiB;
  }

  /**
   * Tính phần trăm tỷ lệ A/B.
   */
  tinhTyLeA(soLoaiA: number, soLoaiB: number): number {
    if (soLoaiB === 0) return soLoaiA > 0 ? 100 : 0;
    return (soLoaiA / soLoaiB) * 100;
  }
}

// =============================================================================
// EXPORT SINGLETON
// =============================================================================

export const baoCaoXepLoaiService = new BaoCaoXepLoaiService();
export default baoCaoXepLoaiService;