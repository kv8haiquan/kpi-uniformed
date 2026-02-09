/**
 * src/services/tieu-chi-chung.service.ts
 * =======================================
 * Service cho Module Tiêu chí chung - ĐỒNG BỘ VỚI BACKEND v2.5.0
 * 
 * ⚠️ ĐÃ FIX v2.5.4:
 * - getMasterData(): Extract từ { nhom_1, nhom_2, nhom_3 } và merge thành 1 array
 * - getNguoiPheDuyet(): Extract từ data.danh_sach
 * - POST dùng ma_tieu_chi, KHÔNG phải tieu_chi_id
 *
 * Version: 2.5.4 (27/01/2026)
 */

import apiClient from '@/lib/axios';
import {
  ITieuChiChungMaster,
  IDanhMucTieuChiResponse,
  IKetQuaTieuChiChungResponse,
  ITuDanhGiaRequest,
  ITieuChiChungInput,
} from '@/types/tieu-chi-chung';

const API_PREFIX = '/danh-gia';

// =============================================================================
// INTERFACES
// =============================================================================

export interface INguoiPheDuyet {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu?: string;
}

export interface INguoiPheDuyetResult {
  nguoiPheDuyet: INguoiPheDuyet[];
  autoApprove: boolean;
  ghiChu: string | null;
}

export interface IChoPheyet {
  danh_gia_thang_id: string;
  cong_chuc_id: string;
  ma_cc: string;
  ho_ten: string;
  don_vi_ten?: string;
  thang: number;
  nam: number;
  diem_tu_cham: number;
  trang_thai: string;
  ngay_gui: string;
}

// =============================================================================
// SERVICE
// =============================================================================

export const tieuChiChungService = {
  /**
   * ⭐ Lấy Master Data - 10 tiêu chí lớn (chia theo nhóm).
   * 
   * GET /api/v1/danh-gia/tieu-chi-chung
   * 
   * Response format từ Backend:
   * {
   *   "success": true,
   *   "data": {
   *     "nhom_1": [...],
   *     "nhom_2": [...],
   *     "nhom_3": [...],
   *     "tong_diem_toi_da": 30.0
   *   },
   *   "message": "..."
   * }
   */
  async getMasterData(): Promise<ITieuChiChungMaster[]> {
    try {
      console.log('=== [getMasterData] Starting ===');
      const response = await apiClient.get(`${API_PREFIX}/tieu-chi-chung`);
      
      console.log('[getMasterData] Full response.data:', response.data);
      
      // Unwrap từ success_response wrapper
      let data = response.data;
      if (data && typeof data === 'object' && 'data' in data) {
        data = data.data;
        console.log('[getMasterData] Unwrapped data:', data);
      }
      
      // Extract từ { nhom_1, nhom_2, nhom_3 } và merge thành 1 array
      if (data && typeof data === 'object') {
        const danhMuc = data as IDanhMucTieuChiResponse;
        const merged: ITieuChiChungMaster[] = [
          ...(danhMuc.nhom_1 || []),
          ...(danhMuc.nhom_2 || []),
          ...(danhMuc.nhom_3 || []),
        ];
        
        console.log('[getMasterData] Merged array length:', merged.length);
        console.log('[getMasterData] First item:', merged[0]);
        
        if (merged.length > 0) {
          return merged;
        }
      }
      
      console.warn('[getMasterData] Could not extract data, returning empty array');
      return [];
    } catch (error: unknown) {
      console.error('[getMasterData] ERROR:', error);
      return [];
    }
  },

  /**
   * ⭐ Lấy kết quả đánh giá tháng - Virtual Record Support.
   * 
   * GET /api/v1/danh-gia/tieu-chi/thang/{thang}/nam/{nam}
   * 
   * Backend LUÔN trả về 200 OK với is_new_record flag.
   */
  async getKetQuaThang(
    thang: number,
    nam: number
  ): Promise<IKetQuaTieuChiChungResponse> {
    console.log('=== [getKetQuaThang] Starting ===', { thang, nam });
    const response = await apiClient.get(
      `${API_PREFIX}/tieu-chi/thang/${thang}/nam/${nam}`
    );
    
    console.log('[getKetQuaThang] response.data:', response.data);
    
    // Unwrap từ success_response wrapper
    let data = response.data;
    if (data && typeof data === 'object' && 'data' in data) {
      data = data.data;
      console.log('[getKetQuaThang] Unwrapped data:', data);
    }
    
    return data as IKetQuaTieuChiChungResponse;
  },

  /**
   * Lấy danh sách người phê duyệt phù hợp.
   * 
   * GET /api/v1/danh-gia/nguoi-phe-duyet
   * 
   * Response format từ Backend:
   * {
   *   "success": true,
   *   "data": {
   *     "danh_sach": [...],
   *     "ghi_chu": "..."
   *   },
   *   "message": "..."
   * }
   */
  async getNguoiPheDuyet(): Promise<INguoiPheDuyetResult> {
    try {
      console.log('=== [getNguoiPheDuyet] Starting ===');
      const response = await apiClient.get(`${API_PREFIX}/nguoi-phe-duyet`);
      
      console.log('[getNguoiPheDuyet] response.data:', response.data);
      
      // Unwrap từ success_response wrapper
      let data = response.data;
      if (data && typeof data === 'object' && 'data' in data) {
        data = data.data;
        console.log('[getNguoiPheDuyet] Unwrapped data:', data);
      }
      
      // Extract từ { danh_sach, ghi_chu }
      const danhSach = data?.danh_sach;
      const ghiChu = data?.ghi_chu;
      
      console.log('[getNguoiPheDuyet] danh_sach:', danhSach);
      console.log('[getNguoiPheDuyet] ghi_chu:', ghiChu);
      
      const nguoiPheDuyet: INguoiPheDuyet[] = Array.isArray(danhSach)
        ? danhSach.map((item: INguoiPheDuyet) => ({
            id: item.id,
            ma_cc: item.ma_cc,
            ho_ten: item.ho_ten,
            chuc_vu: item.chuc_vu,
          }))
        : [];
      
      // Check auto-approve (Chi cục trưởng tự phê duyệt)
      const autoApprove = ghiChu?.includes('tự phê duyệt') || false;
      
      return {
        nguoiPheDuyet,
        autoApprove,
        ghiChu: ghiChu || null,
      };
    } catch (error: unknown) {
      console.error('[getNguoiPheDuyet] ERROR:', error);
      return { nguoiPheDuyet: [], autoApprove: false, ghiChu: null };
    }
  },

  /**
   * ⭐ Lưu nháp tự đánh giá (gui_phe_duyet = false).
   * 
   * POST /api/v1/danh-gia/tu-danh-gia
   * 
   * ⚠️ QUAN TRỌNG: Backend dùng ma_tieu_chi, KHÔNG phải tieu_chi_id
   */
  async luuNhap(data: {
    thang: number;
    nam: number;
    tieu_chi: ITieuChiChungInput[];
  }): Promise<IKetQuaTieuChiChungResponse> {
    const payload: ITuDanhGiaRequest = {
      thang: data.thang,
      nam: data.nam,
      tieu_chi: data.tieu_chi,
      gui_phe_duyet: false,
    };

    console.log('[luuNhap] payload:', JSON.stringify(payload, null, 2));
    
    const response = await apiClient.post(`${API_PREFIX}/tu-danh-gia`, payload);
    
    // Unwrap
    let resData = response.data;
    if (resData && typeof resData === 'object' && 'data' in resData) {
      resData = resData.data;
    }
    return resData as IKetQuaTieuChiChungResponse;
  },

  /**
   * ⭐ Lưu và gửi phê duyệt (gui_phe_duyet = true).
   * 
   * POST /api/v1/danh-gia/tu-danh-gia
   */
  async luuVaGuiPheDuyet(data: {
    thang: number;
    nam: number;
    tieu_chi: ITieuChiChungInput[];
    nguoi_phe_duyet_id: string;
  }): Promise<IKetQuaTieuChiChungResponse> {
    const payload: ITuDanhGiaRequest = {
      thang: data.thang,
      nam: data.nam,
      tieu_chi: data.tieu_chi,
      gui_phe_duyet: true,
      nguoi_phe_duyet_id: data.nguoi_phe_duyet_id,
    };

    console.log('[luuVaGuiPheDuyet] payload:', JSON.stringify(payload, null, 2));
    
    const response = await apiClient.post(`${API_PREFIX}/tu-danh-gia`, payload);
    
    // Unwrap
    let resData = response.data;
    if (resData && typeof resData === 'object' && 'data' in resData) {
      resData = resData.data;
    }
    return resData as IKetQuaTieuChiChungResponse;
  },

  // ===========================================================================
  // ENDPOINTS DÀNH CHO LÃNH ĐẠO
  // ===========================================================================

  async getChoPheyet(
    page: number = 1,
    pageSize: number = 20
  ): Promise<{ items: IChoPheyet[]; total: number }> {
    try {
      const response = await apiClient.get(
        `${API_PREFIX}/tieu-chi/cho-phe-duyet`,
        { params: { page, page_size: pageSize } }
      );
      
      let data = response.data;
      if (data && 'data' in data) data = data.data;
      
      const items = Array.isArray(data?.danh_sach) ? data.danh_sach : [];
      const total = data?.tong_so || items.length;
      
      return { items, total };
    } catch (error: unknown) {
      console.error('[getChoPheyet] ERROR:', error);
      return { items: [], total: 0 };
    }
  },

  async getChiTietPheDuyet(danhGiaThangId: string): Promise<IKetQuaTieuChiChungResponse> {
    const response = await apiClient.get(
      `${API_PREFIX}/tieu-chi/${danhGiaThangId}/chi-tiet`
    );
    
    let data = response.data;
    if (data && 'data' in data) data = data.data;
    return data as IKetQuaTieuChiChungResponse;
  },

  async pheDuyet(
    danhGiaThangId: string,
    dieuChinh?: Array<{ ma_tieu_chi: string; is_achieved_ld: boolean; ly_do_dieu_chinh?: string }>,
    ghiChu?: string
  ): Promise<unknown> {
    const payload = {
      ghi_chu: ghiChu,
      dieu_chinh: dieuChinh || [],
    };

    const response = await apiClient.post(
      `${API_PREFIX}/${danhGiaThangId}/phe-duyet-tieu-chi`,
      payload
    );
    
    let data = response.data;
    if (data && 'data' in data) data = data.data;
    return data;
  },

  async pheDuyetHangLoat(
    danhGiaThangIds: string[],
    ghiChu?: string
  ): Promise<{ tong_phe_duyet: number; danh_sach_id: string[] }> {
    const payload = {
      danh_gia_thang_ids: danhGiaThangIds,
      ghi_chu: ghiChu,
    };

    const response = await apiClient.post(
      `${API_PREFIX}/phe-duyet-tieu-chi-bulk`,
      payload
    );
    
    let data = response.data;
    if (data && 'data' in data) data = data.data;
    return data as { tong_phe_duyet: number; danh_sach_id: string[] };
  },
};

export default tieuChiChungService;