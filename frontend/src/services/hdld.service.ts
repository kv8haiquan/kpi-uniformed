/**
 * src/services/hdld.service.ts
 * ============================
 * Service gọi API đánh giá HĐLĐ 111 theo Bộ tiêu chí VB714.
 */

import apiClient from '@/lib/axios';
import {
  IHdldTieuChiResponse,
  IHdldDanhGia,
  INguoiDuyetOption,
  IHdldTuDanhGiaRequest,
  IHdldNopRequest,
  IHdldDuyetRequest,
  IHdldTraLaiRequest,
} from '@/types/hdld';

const BASE = '/hdld';

const ENDPOINTS = {
  TIEU_CHI: `${BASE}/tieu-chi`,
  NGUOI_DUYET: `${BASE}/nguoi-duyet`,
  DANH_GIA: `${BASE}/danh-gia`,
  LICH_SU: `${BASE}/danh-gia/lich-su`,
  CHO_DUYET: `${BASE}/cho-duyet`,
  TU_DANH_GIA: (id: string) => `${BASE}/danh-gia/${id}/tu-danh-gia`,
  NOP: (id: string) => `${BASE}/danh-gia/${id}/nop`,
  DUYET: (id: string) => `${BASE}/danh-gia/${id}/duyet`,
  TRA_LAI: (id: string) => `${BASE}/danh-gia/${id}/tra-lai`,
};

class HdldService {
  /** Lấy 3 tiêu chí của 1 nhóm nghề. */
  async getTieuChi(nhom: string): Promise<IHdldTieuChiResponse | null> {
    const res = await apiClient.get(ENDPOINTS.TIEU_CHI, { params: { nhom } });
    return res.data.success ? res.data.data : null;
  }

  /** Danh sách người duyệt (TDV/PDV cùng đơn vị) cho HĐLĐ tự chọn. */
  async getNguoiDuyet(): Promise<INguoiDuyetOption[]> {
    const res = await apiClient.get(ENDPOINTS.NGUOI_DUYET);
    return res.data.success ? res.data.data || [] : [];
  }

  /** Lấy (hoặc khởi tạo nháp) bản đánh giá của tháng. */
  async getDanhGia(thang: number, nam: number): Promise<IHdldDanhGia | null> {
    const res = await apiClient.get(ENDPOINTS.DANH_GIA, { params: { thang, nam } });
    return res.data.success ? res.data.data : null;
  }

  /** HĐLĐ lưu tự đánh giá (nhóm nghề + 3 điểm + ghi chú). */
  async luuTuDanhGia(id: string, data: IHdldTuDanhGiaRequest): Promise<IHdldDanhGia | null> {
    const res = await apiClient.put(ENDPOINTS.TU_DANH_GIA(id), data);
    if (res.data.success) return res.data.data;
    throw new Error(res.data.error?.message || 'Lỗi lưu tự đánh giá');
  }

  /** HĐLĐ nộp (chọn người duyệt). */
  async nop(id: string, data: IHdldNopRequest): Promise<IHdldDanhGia | null> {
    const res = await apiClient.post(ENDPOINTS.NOP(id), data);
    if (res.data.success) return res.data.data;
    throw new Error(res.data.error?.message || 'Lỗi nộp đánh giá');
  }

  /** Cấp quản lý: danh sách chờ duyệt. */
  async getChoDuyet(thang?: number, nam?: number): Promise<IHdldDanhGia[]> {
    const params: Record<string, number> = {};
    if (thang) params.thang = thang;
    if (nam) params.nam = nam;
    const res = await apiClient.get(ENDPOINTS.CHO_DUYET, { params });
    return res.data.success ? res.data.data || [] : [];
  }

  /** Cấp quản lý duyệt (nhập cột cấp quản lý). */
  async duyet(id: string, data: IHdldDuyetRequest): Promise<IHdldDanhGia | null> {
    const res = await apiClient.post(ENDPOINTS.DUYET(id), data);
    if (res.data.success) return res.data.data;
    throw new Error(res.data.error?.message || 'Lỗi duyệt');
  }

  /** Cấp quản lý trả lại. */
  async traLai(id: string, data: IHdldTraLaiRequest): Promise<IHdldDanhGia | null> {
    const res = await apiClient.post(ENDPOINTS.TRA_LAI(id), data);
    if (res.data.success) return res.data.data;
    throw new Error(res.data.error?.message || 'Lỗi trả lại');
  }

  /** HĐLĐ xem lịch sử đánh giá. */
  async getLichSu(nam?: number): Promise<IHdldDanhGia[]> {
    const params: Record<string, number> = {};
    if (nam) params.nam = nam;
    const res = await apiClient.get(ENDPOINTS.LICH_SU, { params });
    return res.data.success ? res.data.data || [] : [];
  }
}

const hdldService = new HdldService();
export default hdldService;
