/**
 * src/services/dieu-chuyen-hang-loat.service.ts
 * =============================================
 * Điều chuyển nhân sự hàng loạt theo quyết định, bằng file Excel.
 *
 * Ba bước cố ý tách rời: tải mẫu → xem trước → ghi. Bước xem trước KHÔNG ghi gì
 * và là chỗ duy nhất phát hiện được việc gõ nhầm mã CC (bảng dội lại họ tên).
 */

import apiClient from '@/lib/axios';
import type { IDataResponse } from '@/types/api';

const BASE_URL = '/admin/dieu-chuyen-hang-loat';

/** Trạng thái một dòng sau khi đối chiếu với dữ liệu. */
export type TrangThaiDongDieuChuyen = 'GHI_MOI' | 'BO_QUA' | 'LOI';

export interface IDongDieuChuyen {
  dong_excel: number;
  ma_cc: string;
  ho_ten: string | null;
  don_vi_hien_tai: string | null;
  don_vi_den: string;
  ngay_hieu_luc: string | null;
  so_qd: string | null;
  trang_thai: TrangThaiDongDieuChuyen;
  loi: string[];
  canh_bao: string[];
}

export interface ITomTatDieuChuyen {
  tong_dong: number;
  se_ghi: number;
  bo_qua: number;
  loi: number;
  ghi_duoc: boolean;
  cac_dot: string[];
  loi_chung: string[];
}

export interface IXemTruocDieuChuyen {
  tom_tat: ITomTatDieuChuyen;
  cac_dong: IDongDieuChuyen[];
}

export interface IKetQuaGhiDieuChuyen {
  so_da_ghi: number;
  bo_qua: number;
  danh_sach: Array<{
    ma_cc: string;
    ho_ten: string;
    don_vi_den: string;
    ngay_hieu_luc: string;
  }>;
}

class DieuChuyenHangLoatService {
  /** Tải file mẫu 4 sheet (sheet nhập liệu để trống, kèm sheet tra cứu mã CC). */
  async taiMauExcel(): Promise<void> {
    const res = await apiClient.get(`${BASE_URL}/mau-excel`, { responseType: 'blob' });
    const blob = new Blob([res.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const homNay = new Date();
    const ngay = `${homNay.getFullYear()}${String(homNay.getMonth() + 1).padStart(2, '0')}${String(homNay.getDate()).padStart(2, '0')}`;
    link.download = `mau_dieu_chuyen_hang_loat_${ngay}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  /** Đọc file và đối chiếu — KHÔNG ghi gì vào dữ liệu. */
  async xemTruoc(file: File): Promise<IXemTruocDieuChuyen> {
    const fd = new FormData();
    fd.append('file', file);
    const res = await apiClient.post<IDataResponse<IXemTruocDieuChuyen>>(
      `${BASE_URL}/xem-truoc`,
      fd,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return res.data.data;
  }

  /**
   * Ghi cả đợt trong một transaction.
   * Máy chủ đọc và đối chiếu LẠI TỪ ĐẦU, không tin kết quả xem trước.
   */
  async ghi(file: File): Promise<IKetQuaGhiDieuChuyen> {
    const fd = new FormData();
    fd.append('file', file);
    const res = await apiClient.post<IDataResponse<IKetQuaGhiDieuChuyen>>(
      `${BASE_URL}/ghi`,
      fd,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return res.data.data;
  }
}

export const dieuChuyenHangLoatService = new DieuChuyenHangLoatService();
