/**
 * src/services/export.service.ts
 * ===============================
 * Service gọi API xuất báo cáo DOCX/PDF.
 * 
 * Endpoints:
 * - GET /export/ca-nhan/thang/{thang}/nam/{nam}     → Mẫu 01 + 02
 * - GET /export/don-vi/thang/{thang}/nam/{nam}       → Mẫu 03 đơn vị
 * - GET /export/tong-hop/thang/{thang}/nam/{nam}     → Mẫu 04 toàn Chi cục
 * 
 * Version: 1.1.0 (11/02/2026) - Mẫu 04 cho tổng hợp toàn Chi cục
 * Version: 1.0.0 (02/02/2026)
 */

import apiClient from '@/lib/axios';

// =============================================================================
// TYPES
// =============================================================================

export type ExportFormat = 'docx' | 'pdf';

export interface IExportOptions {
  thang: number;
  nam: number;
  format?: ExportFormat;
}

export interface IExportCaNhanOptions extends IExportOptions {
  congChucId?: string;  // LĐ xuất cho CC khác
}

export interface IExportDonViOptions extends IExportOptions {
  donViId?: string;  // CCT/PCCT chọn đơn vị
}

// =============================================================================
// HELPER: DOWNLOAD FILE TỪ RESPONSE
// =============================================================================

async function downloadBlob(response: any, fallbackFilename: string): Promise<void> {
  // apiClient trả về response.data là blob (vì responseType: 'blob')
  const blob = new Blob([response.data], { 
    type: response.headers['content-type'] || 'application/octet-stream' 
  });
  
  // Lấy filename từ Content-Disposition header
  let filename = fallbackFilename;
  const contentDisposition = response.headers['content-disposition'];
  if (contentDisposition) {
    const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
    if (match && match[1]) {
      filename = match[1].replace(/['"]/g, '');
    }
  }
  
  // Tạo link download
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  
  // Cleanup
  setTimeout(() => {
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }, 100);
}

// =============================================================================
// SERVICE CLASS
// =============================================================================

class ExportService {
  private readonly BASE_URL = '/export';

  /**
   * Xuất báo cáo cá nhân (Mẫu 01 + 02).
   * CC xuất cho mình, LĐ có thể xuất cho CC trong đơn vị.
   */
  async exportCaNhan(options: IExportCaNhanOptions): Promise<void> {
    const { thang, nam, format = 'docx', congChucId } = options;
    
    const params: Record<string, any> = { format };
    if (congChucId) params.cong_chuc_id = congChucId;
    
    try {
      const response = await apiClient.get(
        `${this.BASE_URL}/ca-nhan/thang/${thang}/nam/${nam}`,
        { params, responseType: 'blob' }
      );
      
      const fallback = `BaoCao_CaNhan_${thang.toString().padStart(2, '0')}_${nam}.${format}`;
      await downloadBlob(response, fallback);
    } catch (error: any) {
      console.error('[Export] Error exporting ca nhan:', error);
      throw error;
    }
  }

  /**
   * Xuất báo cáo đơn vị (Mẫu 03).
   * ĐT/Phó ĐT: đơn vị mình. CCT/PCCT: chọn đơn vị.
   */
  async exportDonVi(options: IExportDonViOptions): Promise<void> {
    const { thang, nam, format = 'docx', donViId } = options;
    
    const params: Record<string, any> = { format };
    if (donViId) params.don_vi_id = donViId;
    
    try {
      const response = await apiClient.get(
        `${this.BASE_URL}/don-vi/thang/${thang}/nam/${nam}`,
        { params, responseType: 'blob' }
      );
      
      const fallback = `BaoCao_DonVi_${thang.toString().padStart(2, '0')}_${nam}.${format}`;
      await downloadBlob(response, fallback);
    } catch (error: any) {
      console.error('[Export] Error exporting don vi:', error);
      throw error;
    }
  }

  /**
   * Xuất báo cáo tổng hợp toàn Chi cục (Mẫu 04).
   * Danh sách phê duyệt kết quả xếp loại chất lượng công chức.
   * Quyền: Chỉ CCT và PCCT.
   */
  async exportTongHop(options: IExportOptions): Promise<void> {
    const { thang, nam, format = 'docx' } = options;
    
    try {
      const response = await apiClient.get(
        `${this.BASE_URL}/tong-hop/thang/${thang}/nam/${nam}`,
        { params: { format }, responseType: 'blob' }
      );
      
      const fallback = `Mau04_DanhSach_XepLoai_${thang.toString().padStart(2, '0')}_${nam}.${format}`;
      await downloadBlob(response, fallback);
    } catch (error: any) {
      console.error('[Export] Error exporting tong hop:', error);
      throw error;
    }
  }

  /**
   * Xuất báo cáo Mẫu 03 tổng hợp tất cả đơn vị (mỗi đơn vị 1 trang).
   * Quyền: Chỉ CCT và PCCT.
   */
  async exportDonViTongHop(options: IExportOptions): Promise<void> {
    const { thang, nam, format = 'docx' } = options;
    
    try {
      const response = await apiClient.get(
        `${this.BASE_URL}/don-vi-tong-hop/thang/${thang}/nam/${nam}`,
        { params: { format }, responseType: 'blob' }
      );
      
      const fallback = `Mau03_TatCaDonVi_${thang.toString().padStart(2, '0')}_${nam}.${format}`;
      await downloadBlob(response, fallback);
    } catch (error: any) {
      console.error('[Export] Error exporting don vi tong hop:', error);
      throw error;
    }
  }
}

// =============================================================================
// EXPORT SINGLETON
// =============================================================================

export const exportService = new ExportService();
export default exportService;