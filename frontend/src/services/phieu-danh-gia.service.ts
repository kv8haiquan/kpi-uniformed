/**
 * services/phieu-danh-gia.service.ts
 * ====================================
 * API client cho Phiếu theo dõi, đánh giá công chức theo QUÝ.
 */

import apiClient from '@/lib/axios';
import type {
  ChoPheDuyetResponse,
  KiemTraDuDieuKienResponse,
  PheDuyetPhieuRequest,
  PhieuDanhGiaQuy,
  TraLaiPhieuRequest,
  TrangThaiPhieuDanhGia,
  TuChoiPhieuRequest,
  UpsertPhieuQuyRequest,
} from '@/types/phieu-danh-gia';

const BASE = '/phieu-danh-gia-quy';
const BANG_KE_BASE = '/in-bang-ke';

class PhieuDanhGiaService {
  /** CC: tạo mới hoặc cập nhật phiếu nháp. */
  async upsertNhap(payload: UpsertPhieuQuyRequest): Promise<PhieuDanhGiaQuy> {
    const { data } = await apiClient.post<{ success: boolean; data: PhieuDanhGiaQuy }>(
      `${BASE}/`,
      payload,
    );
    if (!data.success) throw new Error('Lưu phiếu thất bại');
    return data.data;
  }

  /** CC: xem phiếu của mình (trả null nếu chưa có). */
  async getCuaToi(quy: number, nam: number): Promise<PhieuDanhGiaQuy | null> {
    const { data } = await apiClient.get<{ success: boolean; data: PhieuDanhGiaQuy | null }>(
      `${BASE}/cua-toi`,
      { params: { quy, nam } },
    );
    if (!data.success) throw new Error('Không lấy được phiếu');
    return data.data;
  }

  /** CC: gửi duyệt. */
  async guiDuyet(phieuId: string): Promise<PhieuDanhGiaQuy> {
    const { data } = await apiClient.post<{ success: boolean; data: PhieuDanhGiaQuy }>(
      `${BASE}/${phieuId}/gui-duyet`,
    );
    if (!data.success) throw new Error('Gửi duyệt thất bại');
    return data.data;
  }

  /** TDV/CCT: danh sách phiếu theo trạng thái (mặc định CHO_PHE_DUYET). */
  async getChoDuyet(params?: {
    quy?: number;
    nam?: number;
    trang_thai?: TrangThaiPhieuDanhGia;
    page?: number;
    page_size?: number;
  }): Promise<ChoPheDuyetResponse> {
    const { data } = await apiClient.get<{ success: boolean; data: ChoPheDuyetResponse }>(
      `${BASE}/cho-duyet`,
      { params },
    );
    if (!data.success) throw new Error('Không lấy được danh sách');
    return data.data;
  }

  /** TDV/CCT: chấp nhận phiếu + nhập ý kiến. */
  async pheDuyet(phieuId: string, payload: PheDuyetPhieuRequest): Promise<PhieuDanhGiaQuy> {
    const { data } = await apiClient.post<{ success: boolean; data: PhieuDanhGiaQuy }>(
      `${BASE}/${phieuId}/phe-duyet`,
      payload,
    );
    if (!data.success) throw new Error('Phê duyệt thất bại');
    return data.data;
  }

  /** TDV/CCT: từ chối phiếu + lý do. */
  async tuChoi(phieuId: string, payload: TuChoiPhieuRequest): Promise<PhieuDanhGiaQuy> {
    const { data } = await apiClient.post<{ success: boolean; data: PhieuDanhGiaQuy }>(
      `${BASE}/${phieuId}/tu-choi`,
      payload,
    );
    if (!data.success) throw new Error('Từ chối thất bại');
    return data.data;
  }

  /** TDV/CCT: trả lại phiếu đã duyệt (phê duyệt nhầm). */
  async traLai(phieuId: string, payload: TraLaiPhieuRequest): Promise<PhieuDanhGiaQuy> {
    const { data } = await apiClient.post<{ success: boolean; data: PhieuDanhGiaQuy }>(
      `${BASE}/${phieuId}/tra-lai`,
      payload,
    );
    if (!data.success) throw new Error('Trả lại phiếu thất bại');
    return data.data;
  }

  /** CC: kiểm tra điều kiện trước khi gửi phiếu quý (CV + TC đã duyệt hay chưa). */
  async kiemTraDuDieuKien(quy: number, nam: number): Promise<KiemTraDuDieuKienResponse> {
    const { data } = await apiClient.get<{ success: boolean; data: KiemTraDuDieuKienResponse }>(
      `${BASE}/kiem-tra-du-dieu-kien`,
      { params: { quy, nam } },
    );
    if (!data.success) throw new Error('Không kiểm tra được điều kiện');
    return data.data;
  }

  /** TDV/CCT: tải phiếu đánh giá quý (PL-01) của 1 CC cụ thể. */
  async downloadPhieuCuaCC(congChucId: string, quy: number, nam: number): Promise<Blob> {
    const res = await apiClient.get<Blob>(
      `${BANG_KE_BASE}/phieu-danh-gia-quy/${quy}/${nam}/cua-cc/${congChucId}`,
      { responseType: 'blob' },
    );
    return res.data;
  }

  /** TDV/CCT: tải bảng kê công việc quý (PL-02) của 1 CC cụ thể. */
  async downloadBangKeCuaCC(congChucId: string, quy: number, nam: number): Promise<Blob> {
    const res = await apiClient.get<Blob>(
      `${BANG_KE_BASE}/bang-ke-cong-viec-quy/${quy}/${nam}/cua-cc/${congChucId}`,
      { responseType: 'blob' },
    );
    return res.data;
  }
}

export const phieuDanhGiaService = new PhieuDanhGiaService();
