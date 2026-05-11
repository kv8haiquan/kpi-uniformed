/**
 * src/services/tieu-chi-chung.service.ts
 * =======================================
 * Service cho Module Tiêu chí chung - ĐỒNG BỘ VỚI BACKEND v2.6.0
 * 
 * ⚠️ ĐÃ FIX v2.6.0:
 * - Hỗ trợ phê duyệt 2 cấp (cap1/cap2)
 * - getChoPheyet() trả về đơn cho cả cap1 và cap2
 * - pheDuyet() tự động xử lý đúng cấp phê duyệt
 *
 * Version: 2.6.0 (29/01/2026)
 */

import apiClient from '@/lib/axios';
import {
  ITieuChiChungMaster,
  IDanhMucTieuChiResponse,
  IKetQuaTieuChiChungResponse,
  ITuDanhGiaRequest,
  ITieuChiChungInput,
  TrangThaiTieuChiChung,
  TrangThaiPheDuyetCap,
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
  cap_phe_duyet?: 1 | 2;  // v2.6: Phê duyệt cấp nào
}

export interface INguoiPheDuyetResult {
  nguoiPheDuyet: INguoiPheDuyet[];
  autoApprove: boolean;
  ghiChu: string | null;
  quyTrinh: 'TU_PHE_DUYET' | '1_CAP' | '2_CAP';  // v2.6
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
  trang_thai: TrangThaiTieuChiChung;
  ngay_gui: string;
  // v2.6: Thông tin 2 cấp
  cap_cho_duyet?: 1 | 2;  // Đơn đang chờ cấp nào duyệt
  nguoi_phe_duyet_cap1_id?: string | null;
  nguoi_phe_duyet_cap1_ten?: string | null;
  trang_thai_cap1?: TrangThaiPheDuyetCap | null;
  ngay_phe_duyet_cap1?: string | null;
}

// =============================================================================
// SERVICE
// =============================================================================

export const tieuChiChungService = {
  /**
   * ⭐ Lấy Master Data - 10 tiêu chí lớn (chia theo nhóm).
   * 
   * GET /api/v1/danh-gia/tieu-chi-chung
   */
  async getMasterData(): Promise<ITieuChiChungMaster[]> {
    try {
      console.log('=== [getMasterData] Starting ===');
      const response = await apiClient.get(`${API_PREFIX}/tieu-chi-chung`);
      
      // Unwrap từ success_response wrapper
      let data = response.data;
      if (data && typeof data === 'object' && 'data' in data) {
        data = data.data;
      }
      
      // Extract từ { nhom_1, nhom_2, nhom_3 } và merge thành 1 array
      if (data && typeof data === 'object') {
        const danhMuc = data as IDanhMucTieuChiResponse;
        const merged: ITieuChiChungMaster[] = [
          ...(danhMuc.nhom_1 || []),
          ...(danhMuc.nhom_2 || []),
          ...(danhMuc.nhom_3 || []),
        ];
        
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
   * v2.6: Response bao gồm thông tin phê duyệt 2 cấp.
   */
  async getKetQuaThang(
    thang: number,
    nam: number
  ): Promise<IKetQuaTieuChiChungResponse> {
    console.log('=== [getKetQuaThang] Starting ===', { thang, nam });
    const response = await apiClient.get(
      `${API_PREFIX}/tieu-chi/thang/${thang}/nam/${nam}`
    );
    
    // Unwrap từ success_response wrapper
    let data = response.data;
    if (data && typeof data === 'object' && 'data' in data) {
      data = data.data;
    }
    
    return data as IKetQuaTieuChiChungResponse;
  },

  /**
   * Lấy danh sách người phê duyệt phù hợp.
   * 
   * GET /api/v1/danh-gia/nguoi-phe-duyet
   * 
   * v2.6: Response bao gồm quy_trinh để biết quy trình phê duyệt.
   */
  async getNguoiPheDuyet(): Promise<INguoiPheDuyetResult> {
    try {
      console.log('=== [getNguoiPheDuyet] Starting ===');
      const response = await apiClient.get(`${API_PREFIX}/nguoi-phe-duyet`);
      
      // Unwrap từ success_response wrapper
      let data = response.data;
      if (data && typeof data === 'object' && 'data' in data) {
        data = data.data;
      }
      
      // Extract từ { danh_sach, ghi_chu, quy_trinh }
      const danhSach = data?.danh_sach;
      const ghiChu = data?.ghi_chu;
      const quyTrinh = data?.quy_trinh || '1_CAP';
      
      const nguoiPheDuyet: INguoiPheDuyet[] = Array.isArray(danhSach)
        ? danhSach.map((item: INguoiPheDuyet) => ({
            id: item.id,
            ma_cc: item.ma_cc,
            ho_ten: item.ho_ten,
            chuc_vu: item.chuc_vu,
            cap_phe_duyet: item.cap_phe_duyet,
          }))
        : [];
      
      // Check auto-approve (Chi cục trưởng tự phê duyệt)
      const autoApprove = quyTrinh === 'TU_PHE_DUYET' || ghiChu?.includes('tự phê duyệt') || false;
      
      return {
        nguoiPheDuyet,
        autoApprove,
        ghiChu: ghiChu || null,
        quyTrinh,
      };
    } catch (error: unknown) {
      console.error('[getNguoiPheDuyet] ERROR:', error);
      return { nguoiPheDuyet: [], autoApprove: false, ghiChu: null, quyTrinh: '1_CAP' };
    }
  },

  /**
   * ⭐ Lưu nháp tự đánh giá (gui_phe_duyet = false).
   * 
   * POST /api/v1/danh-gia/tu-danh-gia
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
   * 
   * v2.6: Backend tự động gán người phê duyệt theo quy trình 2 cấp.
   */
  async luuVaGuiPheDuyet(data: {
    thang: number;
    nam: number;
    tieu_chi: ITieuChiChungInput[];
    nguoi_phe_duyet_id?: string;
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

  /**
   * Lấy danh sách đơn chờ phê duyệt.
   * 
   * GET /api/v1/danh-gia/tieu-chi/cho-phe-duyet
   * 
   * v2.6: Trả về cả đơn chờ cap1 và cap2 (backend tự filter theo user).
   */
  async getChoPheyet(
    page: number = 1,
    pageSize: number = 20
  ): Promise<{
    items: IChoPheyet[];
    total: number;
    thongKe: { cho_cap1: number; cho_cap2: number };
  }> {
    try {
      const response = await apiClient.get(
        `${API_PREFIX}/tieu-chi/cho-phe-duyet`,
        { params: { page, page_size: pageSize } }
      );
      
      let data = response.data;
      if (data && 'data' in data) data = data.data;
      
      const items = Array.isArray(data?.danh_sach) ? data.danh_sach : [];
      const total = data?.tong_so || items.length;
      const thongKe = data?.thong_ke || { cho_cap1: 0, cho_cap2: 0 };
      
      return { items, total, thongKe };
    } catch (error: unknown) {
      console.error('[getChoPheyet] ERROR:', error);
      return { items: [], total: 0, thongKe: { cho_cap1: 0, cho_cap2: 0 } };
    }
  },

  /**
   * Lấy chi tiết một đơn để phê duyệt.
   * 
   * GET /api/v1/danh-gia/tieu-chi/{id}/chi-tiet
   */
  async getChiTietPheDuyet(danhGiaThangId: string): Promise<IKetQuaTieuChiChungResponse> {
    const response = await apiClient.get(
      `${API_PREFIX}/tieu-chi/${danhGiaThangId}/chi-tiet`
    );
    
    let data = response.data;
    if (data && 'data' in data) data = data.data;
    return data as IKetQuaTieuChiChungResponse;
  },

  /**
   * Phê duyệt tiêu chí chung.
   * 
   * POST /api/v1/danh-gia/{id}/phe-duyet-tieu-chi
   * 
   * v2.6: Backend tự động xử lý đúng cấp (cap1 hoặc cap2).
   */
  async pheDuyet(
    danhGiaThangId: string,
    dieuChinh?: Array<{
      ma_tieu_chi: string;
      /** v3.6 (08/05/2026): điểm LĐ chấm (bội 0.5, 0 → diem_toi_da). Ưu tiên field này. */
      diem_phe_duyet?: number;
      /** Legacy — backend tự suy từ diem_phe_duyet nếu không gửi. */
      is_achieved_ld?: boolean;
      ly_do_dieu_chinh?: string;
    }>,
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

  /**
   * Từ chối tiêu chí chung.
   * 
   * POST /api/v1/danh-gia/{id}/tu-choi-tieu-chi
   * 
   * v2.6: Từ chối ở cấp nào thì đơn quay về TU_CHOI.
   */
  async tuChoi(
    danhGiaThangId: string,
    lyDo: string
  ): Promise<unknown> {
    const payload = {
      ly_do_tu_choi: lyDo,
    };

    const response = await apiClient.post(
      `${API_PREFIX}/${danhGiaThangId}/tu-choi-tieu-chi`,
      payload
    );
    
    let data = response.data;
    if (data && 'data' in data) data = data.data;
    return data;
  },

  /**
   * Phê duyệt hàng loạt.
   * 
   * POST /api/v1/danh-gia/phe-duyet-tieu-chi-bulk
   * 
   * v2.6: Backend xử lý đúng cấp cho từng đơn.
   */
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
  // ⚠️ FIX v2.6.1: Đã XÓA 3 hàm cũ gây lỗi 422:
  // - getPendingApprovals() → dùng getChoPheyet() thay thế
  // - approve() → URL sai + payload sai → dùng pheDuyet()
  // - reject() → URL sai + payload sai → dùng tuChoi()
};

export default tieuChiChungService;