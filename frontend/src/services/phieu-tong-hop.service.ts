/**
 * src/services/phieu-tong-hop.service.ts
 * =======================================
 * Tổng hợp phiếu đánh giá quý (Mẫu 02A/02B) toàn Chi cục — CHỈ ĐỌC.
 *
 * Quyền ở backend: CCT / PCCT / TCCB / cờ `can_view_all_units`.
 */

import apiClient from '@/lib/axios';
import { IPhieuTongHopData, IPhieuTongHopFilter } from '@/types/phieu-tong-hop';

const BASE = '/phieu-danh-gia-quy/toan-chi-cuc';

function buildParams(f: IPhieuTongHopFilter): Record<string, string | number> {
  const p: Record<string, string | number> = { quy: f.quy, nam: f.nam };
  if (f.don_vi_id) p.don_vi_id = f.don_vi_id;
  if (f.trang_thai) p.trang_thai = f.trang_thai;
  if (f.xep_loai) p.xep_loai = f.xep_loai;
  if (f.tim?.trim()) p.tim = f.tim.trim();
  if (f.page) p.page = f.page;
  if (f.page_size) p.page_size = f.page_size;
  return p;
}

export const phieuTongHopService = {
  /** Danh sách phiếu toàn Chi cục kèm số đếm theo trạng thái / xếp loại. */
  async getTongHop(filter: IPhieuTongHopFilter): Promise<IPhieuTongHopData> {
    const res = await apiClient.get(BASE, { params: buildParams(filter) });
    if (!res.data?.success) throw new Error('Không tải được tổng hợp phiếu');
    return res.data.data as IPhieuTongHopData;
  },

  /** Xuất Excel trọn bộ kết quả lọc (KHÔNG phân trang). */
  async exportExcel(filter: IPhieuTongHopFilter): Promise<void> {
    const res = await apiClient.get(`${BASE}/export`, {
      params: buildParams({ ...filter, page: undefined, page_size: undefined }),
      responseType: 'blob',
    });
    const blob = new Blob([res.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `TongHopPhieu_Q${filter.quy}_${filter.nam}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};

export default phieuTongHopService;
