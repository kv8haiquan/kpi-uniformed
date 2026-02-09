/**
 * src/components/xep-loai/tabs/TabBaoCao.tsx
 * ===========================================
 * Tab "Báo cáo xếp loại" - Báo cáo xếp loại cuối tháng.
 * 
 * Version: 3.5.0 - Thêm nút Export DOCX/PDF (02/02/2026)
 * 
 * DESIGN MỚI:
 * - Dạng bảng với các cột: STT, Họ tên/Mã CC, Đơn vị, Ngày LV, Ngày nghỉ, 
 *   Điểm TC, Điểm CV, Điểm KPI, XL Đề xuất, Thao tác
 * - Tự động tính từ dữ liệu đã duyệt
 * - Phó ĐT/ĐT/Phó CCT/CCT đều xem được
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import apiClient from '@/lib/axios';
import { ITabProps, CapBacVaiTro } from '@/types/xep-loai';
import {
  LoadingSpinner,
  EmptyState,
  ErrorMessage,
  StatusBadge,
} from '../shared';
import ExportButton, { ExportFormat } from '@/components/common/ExportButton';
import { exportService } from '@/services/export.service';

// =============================================================================
// TYPES
// =============================================================================

interface IChiTietXepLoai {
  id: string;
  cong_chuc_id?: string;
  cong_chuc?: {
    id: string;
    ma_cc: string;
    ho_ten: string;
    chuc_vu?: string;
  };
  don_vi?: {
    id: string;
    ten_don_vi: string;
  };
  // Điểm chi tiết
  diem_tieu_chi_chung?: number;
  diem_kpi?: number;
  diem_tong?: number;
  // Ngày công
  so_ngay_lam_viec?: number;
  so_ngay_nghi?: number;
  // Xếp loại
  xep_loai_he_thong?: string;
  xep_loai_tu_dong?: string; // backward compat
  xep_loai_de_xuat?: string;
  xep_loai_quyet_dinh?: string;
  ly_do_dieu_chinh_dt?: string;
  ly_do_de_xuat?: string; // backward compat
  ghi_chu?: string;
}

interface IBaoCaoXepLoai {
  id: string;
  don_vi_id?: string;
  don_vi?: {
    id: string;
    ma_don_vi?: string;
    ten_don_vi?: string;
  };
  thang: number;
  nam: number;
  trang_thai: string;
  tong_cong_chuc: number;
  so_loai_a: number;
  so_loai_b: number;
  so_loai_c: number;
  so_loai_d: number;
  so_loai_e?: number;
  chi_tiet?: IChiTietXepLoai[];
  can_edit?: boolean;
  can_approve?: boolean;
}

const TRANG_THAI_MAP: Record<string, { label: string; color: string }> = {
  NHAP: { label: 'Nháp', color: 'bg-gray-100 text-gray-700' },
  CHO_PHE_DUYET: { label: 'Chờ duyệt', color: 'bg-amber-100 text-amber-700' },
  DA_PHE_DUYET: { label: 'Đã duyệt', color: 'bg-green-100 text-green-700' },
  TU_CHOI: { label: 'Từ chối', color: 'bg-red-100 text-red-700' },
  TRA_LAI: { label: 'Trả lại', color: 'bg-red-100 text-red-700' },
};

const XEP_LOAI_COLORS: Record<string, string> = {
  A: 'bg-green-100 text-green-700 border-green-300',
  B: 'bg-blue-100 text-blue-700 border-blue-300',
  C: 'bg-amber-100 text-amber-700 border-amber-300',
  D: 'bg-orange-100 text-orange-700 border-orange-300',
  E: 'bg-red-100 text-red-700 border-red-300',
};

// =============================================================================
// API FUNCTIONS
// =============================================================================

const baoCaoApi = {
  async getBaoCaoDonVi(thang: number, nam: number): Promise<IBaoCaoXepLoai | null> {
    try {
      const response = await apiClient.get(`/bao-cao-xep-loai/don-vi/thang/${thang}/nam/${nam}`);
      return response.data?.data || response.data || null;
    } catch (err) {
      const error = err as { response?: { status: number } };
      if (error.response?.status === 404) return null;
      throw err;
    }
  },

  async deXuatXepLoai(chiTietId: string, payload: {
    xep_loai_de_xuat: string;
    ly_do_dieu_chinh?: string;
  }): Promise<void> {
    await apiClient.put(`/bao-cao-xep-loai/chi-tiet/${chiTietId}/de-xuat`, payload);
  },

  async guiDuyet(baoCaoId: string): Promise<void> {
    await apiClient.post(`/bao-cao-xep-loai/${baoCaoId}/gui-duyet`);
  },

  async getChoPheDuyet(): Promise<IBaoCaoXepLoai[]> {
    const response = await apiClient.get('/bao-cao-xep-loai/cho-phe-duyet');
    if (Array.isArray(response.data)) return response.data;
    if (response.data?.data && Array.isArray(response.data.data)) return response.data.data;
    return [];
  },

  async getDanhSach(thang: number, nam: number, trangThai?: string): Promise<{
    danh_sach: IBaoCaoXepLoai[];
    tong_so: number;
    thong_ke_trang_thai: Record<string, number>;
  }> {
    const params = new URLSearchParams();
    if (trangThai) params.set('trang_thai', trangThai);
    const qs = params.toString();
    const response = await apiClient.get(
      `/bao-cao-xep-loai/danh-sach/thang/${thang}/nam/${nam}${qs ? `?${qs}` : ''}`
    );
    const data = response.data?.data || response.data;
    return {
      danh_sach: data?.danh_sach || [],
      tong_so: data?.tong_so || 0,
      thong_ke_trang_thai: data?.thong_ke_trang_thai || {},
    };
  },

  async getChiTiet(baoCaoId: string): Promise<IBaoCaoXepLoai | null> {
    const response = await apiClient.get(`/bao-cao-xep-loai/${baoCaoId}`);
    return response.data?.data || response.data || null;
  },

  async pheDuyet(baoCaoId: string, payload: {
    action: 'APPROVE' | 'REJECT';
    y_kien?: string;
  }): Promise<void> {
    await apiClient.post(`/bao-cao-xep-loai/${baoCaoId}/phe-duyet`, payload);
  },

  async quyetDinhXepLoai(chiTietId: string, payload: {
    xep_loai_quyet_dinh: string;
    ly_do_dieu_chinh?: string;
  }): Promise<void> {
    await apiClient.put(`/bao-cao-xep-loai/chi-tiet/${chiTietId}/quyet-dinh`, payload);
  },
};

// =============================================================================
// HELPER COMPONENTS
// =============================================================================

function XepLoaiBadge({ xepLoai, size = 'sm' }: { xepLoai?: string; size?: 'sm' | 'md' }) {
  if (!xepLoai) return <span className="text-gray-400">-</span>;
  const sizeClass = size === 'md' ? 'px-3 py-1 text-sm' : 'px-2 py-0.5 text-xs';
  return (
    <span className={`${sizeClass} font-bold rounded border ${XEP_LOAI_COLORS[xepLoai] || 'bg-gray-100 text-gray-700 border-gray-300'}`}>
      {xepLoai}
    </span>
  );
}

function StatsSummary({ baoCao }: { baoCao: IBaoCaoXepLoai }) {
  // FIX v3.6.0: Tính thống kê từ chi_tiet thay vì so_loai_* từ backend
  // Backend có thể trả so_loai_* sai nếu xep_loai_de_xuat chưa được gán
  const computed = { A: 0, B: 0, C: 0, D: 0, E: 0 };
  if (baoCao.chi_tiet && baoCao.chi_tiet.length > 0) {
    for (const ct of baoCao.chi_tiet) {
      const xl = ct.xep_loai_de_xuat || ct.xep_loai_he_thong || ct.xep_loai_tu_dong || 'D';
      if (xl in computed) computed[xl as keyof typeof computed]++;
    }
  } else {
    // Fallback nếu không có chi_tiet (ví dụ danh sách tóm tắt)
    computed.A = baoCao.so_loai_a;
    computed.B = baoCao.so_loai_b;
    computed.C = baoCao.so_loai_c;
    computed.D = baoCao.so_loai_d;
    computed.E = baoCao.so_loai_e || 0;
  }
  const stats = [
    { label: 'A', value: computed.A, color: 'bg-green-500' },
    { label: 'B', value: computed.B, color: 'bg-blue-500' },
    { label: 'C', value: computed.C, color: 'bg-amber-500' },
    { label: 'D', value: computed.D, color: 'bg-orange-500' },
    { label: 'E', value: computed.E, color: 'bg-red-500' },
  ];
  const total = baoCao.tong_cong_chuc || stats.reduce((sum, s) => sum + s.value, 0);

  return (
    <div className="flex items-center gap-4">
      {stats.map((s) => (
        <div key={s.label} className="flex items-center gap-1.5">
          <div className={`w-3 h-3 rounded ${s.color}`} />
          <span className="text-sm font-medium text-gray-700">{s.label}:</span>
          <span className="text-sm font-bold text-gray-900">{s.value}</span>
        </div>
      ))}
      <div className="border-l border-gray-300 pl-4 ml-2">
        <span className="text-sm text-gray-500">Tổng:</span>
        <span className="text-sm font-bold text-gray-900 ml-1">{total}</span>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN TABLE VIEW (cho cả ĐT và CCT)
// =============================================================================

interface BaoCaoTableViewProps {
  baoCao: IBaoCaoXepLoai;
  canEdit: boolean;
  canApprove: boolean;
  onRefresh: () => void;
  isProcessing: boolean;
  setIsProcessing: (v: boolean) => void;
}

function BaoCaoTableView({ 
  baoCao, 
  canEdit, 
  canApprove, 
  onRefresh,
  isProcessing,
  setIsProcessing 
}: BaoCaoTableViewProps) {
  const [selectedChiTiet, setSelectedChiTiet] = useState<IChiTietXepLoai | null>(null);
  const [deXuatXepLoai, setDeXuatXepLoai] = useState('B');
  const [lyDoDeXuat, setLyDoDeXuat] = useState('');

  const trangThaiInfo = TRANG_THAI_MAP[baoCao.trang_thai] || TRANG_THAI_MAP.NHAP;
  const canGuiDuyet = canEdit && (baoCao.trang_thai === 'NHAP' || baoCao.trang_thai === 'TU_CHOI' || baoCao.trang_thai === 'TRA_LAI');

  const handleDeXuat = (ct: IChiTietXepLoai) => {
    setSelectedChiTiet(ct);
    setDeXuatXepLoai(ct.xep_loai_de_xuat || ct.xep_loai_he_thong || ct.xep_loai_tu_dong || 'B');
    setLyDoDeXuat(ct.ly_do_dieu_chinh_dt || ct.ly_do_de_xuat || '');
  };

  const handleDeXuatSubmit = async () => {
    if (!selectedChiTiet) return;
    setIsProcessing(true);
    try {
      await baoCaoApi.deXuatXepLoai(selectedChiTiet.id, {
        xep_loai_de_xuat: deXuatXepLoai,
        ly_do_dieu_chinh: lyDoDeXuat || undefined,
      });
      await onRefresh();
      setSelectedChiTiet(null);
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleGuiDuyet = async () => {
    if (!window.confirm('Gửi báo cáo lên Chi cục trưởng phê duyệt?')) return;
    setIsProcessing(true);
    try {
      await baoCaoApi.guiDuyet(baoCao.id);
      await onRefresh();
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header Card */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-semibold text-gray-900">
                Báo cáo tháng {baoCao.thang}/{baoCao.nam}
              </h3>
              <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${trangThaiInfo.color}`}>
                {trangThaiInfo.label}
              </span>
            </div>
            <p className="text-sm text-gray-500 mt-1">{baoCao.don_vi?.ten_don_vi}</p>
          </div>
          
          <StatsSummary baoCao={baoCao} />
          
          <div className="flex items-center gap-2">
            {/* Nút xuất báo cáo đơn vị */}
            <ExportButton
              label="Xuất báo cáo"
              size="sm"
              onExport={async (format: ExportFormat) => {
                await exportService.exportDonVi({
                  thang: baoCao.thang,
                  nam: baoCao.nam,
                  format,
                  donViId: baoCao.don_vi_id,
                });
              }}
            />

            {canGuiDuyet && (
            <button
              onClick={handleGuiDuyet}
              disabled={isProcessing}
              className="px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
              Gửi phê duyệt
            </button>
          )}
          </div>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="px-3 py-3 text-left font-semibold text-gray-700 w-12">STT</th>
                <th className="px-3 py-3 text-left font-semibold text-gray-700 min-w-[180px]">Họ tên / Mã CC</th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700 w-20">Ngày LV</th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700 w-20">Ngày nghỉ</th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700 w-24">
                  <div>Điểm TC</div>
                  <div className="text-xs font-normal text-gray-500">(30đ)</div>
                </th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700 w-24">
                  <div>Điểm CV</div>
                  <div className="text-xs font-normal text-gray-500">(70đ)</div>
                </th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700 w-24">
                  <div>Tổng KPI</div>
                  <div className="text-xs font-normal text-gray-500">(100đ)</div>
                </th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700 w-20">XL Tự động</th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700 w-20">XL Đề xuất</th>
                {canEdit && canGuiDuyet && (
                  <th className="px-3 py-3 text-center font-semibold text-gray-700 w-20">Thao tác</th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {baoCao.chi_tiet?.map((ct, index) => {
                const xepLoaiHeThong = ct.xep_loai_he_thong || ct.xep_loai_tu_dong;
                // FIX v3.6.0: XL Đề xuất mặc định = XL Tự động nếu chưa có
                const xepLoaiDeXuat = ct.xep_loai_de_xuat || xepLoaiHeThong;
                // Chỉ hiện "Đã điều chỉnh" khi ĐT thực sự đã sửa khác hệ thống
                const hasCustomDeXuat = ct.xep_loai_de_xuat != null && ct.xep_loai_de_xuat !== xepLoaiHeThong;
                
                return (
                  <tr key={ct.id} className="hover:bg-gray-50">
                    <td className="px-3 py-3 text-gray-500">{index + 1}</td>
                    <td className="px-3 py-3">
                      <div className="font-medium text-gray-900">{ct.cong_chuc?.ho_ten}</div>
                      <div className="text-xs text-gray-500">{ct.cong_chuc?.ma_cc}</div>
                      {ct.cong_chuc?.chuc_vu && (
                        <div className="text-xs text-blue-600">{ct.cong_chuc.chuc_vu}</div>
                      )}
                    </td>
                    <td className="px-3 py-3 text-center font-medium text-gray-900">
                      {ct.so_ngay_lam_viec?.toFixed(0) || '-'}
                    </td>
                    <td className="px-3 py-3 text-center">
                      {ct.so_ngay_nghi ? (
                        <span className="text-red-600 font-medium">{ct.so_ngay_nghi.toFixed(1)}</span>
                      ) : (
                        <span className="text-gray-400">0</span>
                      )}
                    </td>
                    <td className="px-3 py-3 text-center font-medium text-gray-900">
                      {ct.diem_tieu_chi_chung?.toFixed(1) || '-'}
                    </td>
                    <td className="px-3 py-3 text-center font-medium text-gray-900">
                      {ct.diem_kpi?.toFixed(1) || '-'}
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span className="font-bold text-lg text-gray-900">
                        {ct.diem_tong?.toFixed(1) || '-'}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-center">
                      <XepLoaiBadge xepLoai={xepLoaiHeThong} />
                    </td>
                    <td className="px-3 py-3 text-center">
                      {hasCustomDeXuat ? (
                        <div className="flex flex-col items-center gap-1">
                          <XepLoaiBadge xepLoai={xepLoaiDeXuat} />
                          <span className="text-[10px] text-amber-600">Đã điều chỉnh</span>
                        </div>
                      ) : (
                        <XepLoaiBadge xepLoai={xepLoaiDeXuat} />
                      )}
                    </td>
                    {canEdit && canGuiDuyet && (
                      <td className="px-3 py-3 text-center">
                        <button
                          onClick={() => handleDeXuat(ct)}
                          className="px-2.5 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded border border-blue-200 transition-colors"
                        >
                          Sửa
                        </button>
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        
        {(!baoCao.chi_tiet || baoCao.chi_tiet.length === 0) && (
          <div className="py-12 text-center text-gray-500">
            Không có dữ liệu chi tiết
          </div>
        )}
      </div>

      {/* Modal Đề xuất xếp loại */}
      {selectedChiTiet && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Điều chỉnh xếp loại đề xuất</h3>
            
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <p className="font-medium text-gray-900">{selectedChiTiet.cong_chuc?.ho_ten}</p>
              <p className="text-sm text-gray-600">{selectedChiTiet.cong_chuc?.ma_cc}</p>
              <div className="flex items-center gap-4 mt-2 text-sm">
                <span className="text-gray-500">
                  Điểm: <strong>{selectedChiTiet.diem_tong?.toFixed(1)}</strong>
                </span>
                <span className="text-gray-500">
                  Tự động: <XepLoaiBadge xepLoai={selectedChiTiet.xep_loai_he_thong || selectedChiTiet.xep_loai_tu_dong} />
                </span>
              </div>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Xếp loại đề xuất</label>
              <div className="grid grid-cols-4 gap-2">
                {['A', 'B', 'C', 'D'].map((xl) => (
                  <button
                    key={xl}
                    onClick={() => setDeXuatXepLoai(xl)}
                    className={`py-2 px-3 rounded-lg border-2 font-bold text-center transition-all ${
                      deXuatXepLoai === xl 
                        ? `${XEP_LOAI_COLORS[xl]} border-current` 
                        : 'bg-gray-50 text-gray-400 border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {xl}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Lý do điều chỉnh 
                {deXuatXepLoai !== (selectedChiTiet.xep_loai_he_thong || selectedChiTiet.xep_loai_tu_dong) && (
                  <span className="text-red-500 ml-1">*</span>
                )}
              </label>
              <textarea
                value={lyDoDeXuat}
                onChange={(e) => setLyDoDeXuat(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Nhập lý do nếu khác xếp loại tự động..."
              />
            </div>
            
            <div className="flex justify-end gap-3">
              <button 
                onClick={() => setSelectedChiTiet(null)} 
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium"
              >
                Hủy
              </button>
              <button 
                onClick={handleDeXuatSubmit} 
                disabled={isProcessing}
                className="px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-lg font-medium disabled:opacity-50"
              >
                {isProcessing ? 'Đang lưu...' : 'Lưu'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// ĐƠN VỊ VIEW (Phó ĐT, ĐT)
// =============================================================================

interface DonViViewProps {
  thang: number;
  nam: number;
  canApprove: boolean;
}

function DonViView({ thang, nam, canApprove }: DonViViewProps) {
  const [baoCao, setBaoCao] = useState<IBaoCaoXepLoai | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await baoCaoApi.getBaoCaoDonVi(thang, nam);
      setBaoCao(response);
    } catch (err) {
      const error = err as Error;
      setError(error.message || 'Có lỗi xảy ra');
    } finally {
      setIsLoading(false);
    }
  }, [thang, nam]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={loadData} />;
  }

  if (!baoCao) {
    return (
      <EmptyState 
        title="Chưa có dữ liệu" 
        description={`Chưa có dữ liệu xếp loại tháng ${thang}/${nam}`} 
      />
    );
  }

  // can_edit từ API hoặc dựa vào canApprove prop
  const canEdit = baoCao.can_edit ?? canApprove;

  return (
    <BaoCaoTableView
      baoCao={baoCao}
      canEdit={canEdit}
      canApprove={false}
      onRefresh={loadData}
      isProcessing={isProcessing}
      setIsProcessing={setIsProcessing}
    />
  );
}

// =============================================================================
// CCT VIEW
// =============================================================================

type TrangThaiFilter = '' | 'CHO_PHE_DUYET' | 'DA_PHE_DUYET' | 'TU_CHOI';

const TRANG_THAI_FILTER_OPTIONS: { value: TrangThaiFilter; label: string }[] = [
  { value: '', label: 'Tất cả' },
  { value: 'CHO_PHE_DUYET', label: 'Chờ duyệt' },
  { value: 'DA_PHE_DUYET', label: 'Đã duyệt' },
  { value: 'TU_CHOI', label: 'Từ chối' },
];

interface CCTViewProps {
  thang: number;
  nam: number;
  canApprove: boolean;
  onPendingCountChange?: (count: number) => void;
}

function CCTView({ thang, nam, canApprove, onPendingCountChange }: CCTViewProps) {
  const [baoCaoList, setBaoCaoList] = useState<IBaoCaoXepLoai[]>([]);
  const [selectedBaoCao, setSelectedBaoCao] = useState<IBaoCaoXepLoai | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const [filterTrangThai, setFilterTrangThai] = useState<TrangThaiFilter>('');
  const [counts, setCounts] = useState<Record<string, number>>({});

  const [pheDuyetAction, setPheDuyetAction] = useState<'approve' | 'reject' | null>(null);
  const [lyDoPheDuyet, setLyDoPheDuyet] = useState('');

  // State cho modal sửa XL quyết định (CCT)
  const [editingChiTiet, setEditingChiTiet] = useState<IChiTietXepLoai | null>(null);
  const [quyetDinhXepLoai, setQuyetDinhXepLoai] = useState('');
  const [lyDoQuyetDinh, setLyDoQuyetDinh] = useState('');

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await baoCaoApi.getDanhSach(thang, nam, filterTrangThai || undefined);
      setBaoCaoList(result.danh_sach);
      setCounts(result.thong_ke_trang_thai);
    } catch (err) {
      const error = err as Error;
      setError(error.message || 'Có lỗi xảy ra');
    } finally {
      setIsLoading(false);
    }
  }, [thang, nam, filterTrangThai]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Badge count trên tab = số báo cáo chờ duyệt
  useEffect(() => {
    onPendingCountChange?.(counts.CHO_PHE_DUYET || 0);
  }, [counts, onPendingCountChange]);

  const handleSelectBaoCao = async (baoCaoId: string) => {
    try {
      const detail = await baoCaoApi.getChiTiet(baoCaoId);
      setSelectedBaoCao(detail);
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra');
    }
  };

  const handlePheDuyetSubmit = async () => {
    if (!selectedBaoCao || !pheDuyetAction) return;
    if (pheDuyetAction === 'reject' && !lyDoPheDuyet.trim()) {
      alert('Vui lòng nhập lý do từ chối');
      return;
    }

    setIsProcessing(true);
    try {
      await baoCaoApi.pheDuyet(selectedBaoCao.id, {
        action: pheDuyetAction === 'approve' ? 'APPROVE' : 'REJECT',
        y_kien: lyDoPheDuyet || undefined,
      });
      await loadData();
      setSelectedBaoCao(null);
      setPheDuyetAction(null);
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra');
    } finally {
      setIsProcessing(false);
    }
  };

  // CCT mở modal sửa XL quyết định
  const handleEditQuyetDinh = (ct: IChiTietXepLoai) => {
    setEditingChiTiet(ct);
    // FIX v3.6.0: Ưu tiên quyết định > đề xuất > hệ thống
    const xlDeXuat = ct.xep_loai_de_xuat || ct.xep_loai_he_thong || ct.xep_loai_tu_dong;
    setQuyetDinhXepLoai(ct.xep_loai_quyet_dinh || xlDeXuat || 'B');
    setLyDoQuyetDinh('');
  };

  // CCT submit sửa XL quyết định
  const handleQuyetDinhSubmit = async () => {
    if (!editingChiTiet || !selectedBaoCao) return;
    
    // Validate: nếu khác đề xuất thì phải có lý do
    const xlDeXuat = editingChiTiet.xep_loai_de_xuat || editingChiTiet.xep_loai_he_thong || editingChiTiet.xep_loai_tu_dong;
    if (quyetDinhXepLoai !== xlDeXuat && !lyDoQuyetDinh.trim()) {
      alert('Vui lòng nhập lý do khi điều chỉnh khác đề xuất');
      return;
    }

    setIsProcessing(true);
    try {
      await baoCaoApi.quyetDinhXepLoai(editingChiTiet.id, {
        xep_loai_quyet_dinh: quyetDinhXepLoai,
        ly_do_dieu_chinh: lyDoQuyetDinh || undefined,
      });
      // Reload chi tiết báo cáo đang mở
      const updated = await baoCaoApi.getChiTiet(selectedBaoCao.id);
      setSelectedBaoCao(updated);
      setEditingChiTiet(null);
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra');
    } finally {
      setIsProcessing(false);
    }
  };

  // Tính tổng cho filter "Tất cả"
  const totalAll = Object.values(counts).reduce((sum, n) => sum + n, 0);

  // Badge trạng thái cho từng card
  const getTrangThaiBadge = (trangThai: string) => {
    const info = TRANG_THAI_MAP[trangThai];
    if (!info) return null;
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${info.color}`}>
        {info.label}
      </span>
    );
  };

  // Kiểm tra card có thể duyệt
  const canApproveItem = (bc: IBaoCaoXepLoai) => canApprove && bc.trang_thai === 'CHO_PHE_DUYET';

  return (
    <div className="space-y-4">
      {/* Filter trạng thái */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-gray-700 whitespace-nowrap">Trạng thái:</label>
          <select
            value={filterTrangThai}
            onChange={(e) => setFilterTrangThai(e.target.value as TrangThaiFilter)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-w-[180px]"
          >
            {TRANG_THAI_FILTER_OPTIONS.map((opt) => {
              const count = opt.value === ''
                ? totalAll
                : (counts[opt.value] || 0);
              return (
                <option key={opt.value} value={opt.value}>
                  {opt.label} ({count})
                </option>
              );
            })}
          </select>
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      )}

      {/* Error */}
      {!isLoading && error && (
        <ErrorMessage message={error} onRetry={loadData} />
      )}

      {/* Empty state */}
      {!isLoading && !error && baoCaoList.length === 0 && (
        <EmptyState 
          title={filterTrangThai ? `Không có báo cáo ${TRANG_THAI_MAP[filterTrangThai]?.label?.toLowerCase() || ''}` : 'Không có báo cáo'} 
          description={`Không có báo cáo xếp loại nào ${filterTrangThai ? TRANG_THAI_MAP[filterTrangThai]?.label?.toLowerCase() : ''} tháng ${thang}/${nam}`} 
        />
      )}

      {/* Danh sách báo cáo */}
      {!isLoading && !error && baoCaoList.length > 0 && (
        <>
          <div className="text-sm text-gray-500">
            Hiển thị {baoCaoList.length} báo cáo
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {baoCaoList.map((bc) => {
              const borderColor = bc.trang_thai === 'CHO_PHE_DUYET' 
                ? 'border-l-amber-400' 
                : bc.trang_thai === 'DA_PHE_DUYET' 
                  ? 'border-l-green-500' 
                  : bc.trang_thai === 'TU_CHOI' 
                    ? 'border-l-red-500' 
                    : 'border-l-gray-300';
              return (
              <div
                key={bc.id}
                className={`bg-white rounded-lg border border-gray-200 border-l-4 ${borderColor} p-4 hover:shadow-md cursor-pointer transition-all`}
                onClick={() => handleSelectBaoCao(bc.id)}
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="font-medium text-gray-900">{bc.don_vi?.ten_don_vi}</h4>
                    <p className="text-sm text-gray-500">Tháng {bc.thang}/{bc.nam}</p>
                  </div>
                  {getTrangThaiBadge(bc.trang_thai)}
                </div>
                <div className="flex flex-wrap gap-2 text-xs">
                  <span className="px-2 py-1 bg-green-100 text-green-700 rounded font-medium">A: {bc.so_loai_a}</span>
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded font-medium">B: {bc.so_loai_b}</span>
                  <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded font-medium">C: {bc.so_loai_c}</span>
                  <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded font-medium">D: {bc.so_loai_d}</span>
                </div>
                <p className="text-xs text-gray-400 mt-2">Tổng: {bc.tong_cong_chuc} công chức</p>
              </div>
              );
            })}
          </div>
        </>
      )}

      {/* Modal chi tiết báo cáo */}
      {selectedBaoCao && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-xl">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
              <div>
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-semibold text-gray-900">{selectedBaoCao.don_vi?.ten_don_vi}</h3>
                  {getTrangThaiBadge(selectedBaoCao.trang_thai)}
                </div>
                <p className="text-sm text-gray-500">Báo cáo xếp loại tháng {selectedBaoCao.thang}/{selectedBaoCao.nam}</p>
              </div>
              <div className="flex items-center gap-2">
                <ExportButton
                  label="Xuất"
                  size="sm"
                  onExport={async (format: ExportFormat) => {
                    await exportService.exportDonVi({
                      thang: selectedBaoCao.thang,
                      nam: selectedBaoCao.nam,
                      format,
                      donViId: selectedBaoCao.don_vi_id,
                    });
                  }}
                />
                <button 
                  onClick={() => setSelectedBaoCao(null)} 
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {/* Stats */}
              <div className="mb-6">
                <StatsSummary baoCao={selectedBaoCao} />
              </div>

              {/* Table */}
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      <th className="px-3 py-2.5 text-left font-semibold text-gray-700">STT</th>
                      <th className="px-3 py-2.5 text-left font-semibold text-gray-700">Họ tên / Mã CC</th>
                      <th className="px-3 py-2.5 text-center font-semibold text-gray-700">Điểm TC</th>
                      <th className="px-3 py-2.5 text-center font-semibold text-gray-700">Điểm CV</th>
                      <th className="px-3 py-2.5 text-center font-semibold text-gray-700">Tổng KPI</th>
                      <th className="px-3 py-2.5 text-center font-semibold text-gray-700">XL Tự động</th>
                      <th className="px-3 py-2.5 text-center font-semibold text-gray-700">XL Đề xuất</th>
                      <th className="px-3 py-2.5 text-center font-semibold text-gray-700">XL Quyết định</th>
                      {canApproveItem(selectedBaoCao) && (
                        <th className="px-3 py-2.5 text-center font-semibold text-gray-700">Thao tác</th>
                      )}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {selectedBaoCao.chi_tiet?.map((ct, index) => {
                      // FIX v3.6.0: XL Đề xuất mặc định = XL Tự động
                      const xlHeThong = ct.xep_loai_he_thong || ct.xep_loai_tu_dong;
                      const xlDeXuat = ct.xep_loai_de_xuat || xlHeThong;
                      const hasCustomQD = ct.xep_loai_quyet_dinh && ct.xep_loai_quyet_dinh !== xlDeXuat;
                      return (
                        <tr key={ct.id} className="hover:bg-gray-50">
                          <td className="px-3 py-2 text-gray-500">{index + 1}</td>
                          <td className="px-3 py-2">
                            <div className="font-medium text-gray-900">{ct.cong_chuc?.ho_ten}</div>
                            <div className="text-xs text-gray-500">{ct.cong_chuc?.ma_cc}</div>
                          </td>
                          <td className="px-3 py-2 text-center">{ct.diem_tieu_chi_chung?.toFixed(1) || '-'}</td>
                          <td className="px-3 py-2 text-center">{ct.diem_kpi?.toFixed(1) || '-'}</td>
                          <td className="px-3 py-2 text-center font-bold">{ct.diem_tong?.toFixed(1) || '-'}</td>
                          <td className="px-3 py-2 text-center">
                            <XepLoaiBadge xepLoai={ct.xep_loai_he_thong || ct.xep_loai_tu_dong} />
                          </td>
                          <td className="px-3 py-2 text-center">
                            <XepLoaiBadge xepLoai={xlDeXuat} />
                          </td>
                          <td className="px-3 py-2 text-center">
                            {hasCustomQD ? (
                              <div className="flex flex-col items-center gap-1">
                                <XepLoaiBadge xepLoai={ct.xep_loai_quyet_dinh} />
                                <span className="text-[10px] text-purple-600">Đã điều chỉnh</span>
                              </div>
                            ) : (
                              <XepLoaiBadge xepLoai={ct.xep_loai_quyet_dinh} />
                            )}
                          </td>
                          {canApproveItem(selectedBaoCao) && (
                            <td className="px-3 py-2 text-center">
                              <button
                                onClick={(e) => { e.stopPropagation(); handleEditQuyetDinh(ct); }}
                                className="px-2.5 py-1 text-xs text-purple-600 hover:bg-purple-50 rounded border border-purple-200 transition-colors"
                              >
                                Sửa
                              </button>
                            </td>
                          )}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Footer - chỉ hiện nút duyệt/từ chối nếu báo cáo đang CHO_PHE_DUYET */}
            {canApproveItem(selectedBaoCao) && (
              <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end gap-3">
                <button
                  onClick={() => { setPheDuyetAction('reject'); setLyDoPheDuyet(''); }}
                  disabled={isProcessing}
                  className="px-4 py-2 text-red-600 bg-white border border-red-200 hover:bg-red-50 rounded-lg font-medium transition-colors"
                >
                  Từ chối
                </button>
                <button
                  onClick={() => { setPheDuyetAction('approve'); setLyDoPheDuyet(''); }}
                  disabled={isProcessing}
                  className="px-4 py-2 text-white bg-green-600 hover:bg-green-700 rounded-lg font-medium transition-colors"
                >
                  Phê duyệt
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modal sửa XL Quyết định (CCT) */}
      {editingChiTiet && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60]">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Điều chỉnh xếp loại quyết định</h3>
            
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <p className="font-medium text-gray-900">{editingChiTiet.cong_chuc?.ho_ten}</p>
              <p className="text-sm text-gray-600">{editingChiTiet.cong_chuc?.ma_cc}</p>
              <div className="flex items-center gap-4 mt-2 text-sm">
                <span className="text-gray-500">
                  Điểm: <strong>{editingChiTiet.diem_tong?.toFixed(1)}</strong>
                </span>
                <span className="text-gray-500">
                  Đề xuất: <XepLoaiBadge xepLoai={editingChiTiet.xep_loai_de_xuat || editingChiTiet.xep_loai_he_thong || editingChiTiet.xep_loai_tu_dong} />
                </span>
              </div>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Xếp loại quyết định</label>
              <div className="grid grid-cols-4 gap-2">
                {['A', 'B', 'C', 'D'].map((xl) => (
                  <button
                    key={xl}
                    onClick={() => setQuyetDinhXepLoai(xl)}
                    className={`py-2 px-3 rounded-lg border-2 font-bold text-center transition-all ${
                      quyetDinhXepLoai === xl 
                        ? `${XEP_LOAI_COLORS[xl]} border-current` 
                        : 'bg-gray-50 text-gray-400 border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {xl}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Lý do điều chỉnh
                {quyetDinhXepLoai !== (editingChiTiet.xep_loai_de_xuat || editingChiTiet.xep_loai_he_thong || editingChiTiet.xep_loai_tu_dong) && (
                  <span className="text-red-500 ml-1">*</span>
                )}
              </label>
              <textarea
                value={lyDoQuyetDinh}
                onChange={(e) => setLyDoQuyetDinh(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                placeholder="Nhập lý do nếu khác đề xuất của Đội trưởng..."
              />
            </div>
            
            <div className="flex justify-end gap-3">
              <button 
                onClick={() => setEditingChiTiet(null)} 
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium"
              >
                Hủy
              </button>
              <button 
                onClick={handleQuyetDinhSubmit} 
                disabled={isProcessing}
                className="px-4 py-2 text-white bg-purple-600 hover:bg-purple-700 rounded-lg font-medium disabled:opacity-50"
              >
                {isProcessing ? 'Đang lưu...' : 'Lưu'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal xác nhận phê duyệt/từ chối */}
      {pheDuyetAction && selectedBaoCao && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60]">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {pheDuyetAction === 'approve' ? '✅ Xác nhận phê duyệt' : '❌ Xác nhận từ chối'}
            </h3>
            <p className="text-gray-600 mb-4">
              {pheDuyetAction === 'approve'
                ? `Phê duyệt báo cáo xếp loại của ${selectedBaoCao.don_vi?.ten_don_vi}?`
                : `Từ chối báo cáo xếp loại của ${selectedBaoCao.don_vi?.ten_don_vi}?`}
            </p>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ý kiến {pheDuyetAction === 'reject' && <span className="text-red-500">*</span>}
              </label>
              <textarea
                value={lyDoPheDuyet}
                onChange={(e) => setLyDoPheDuyet(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder={pheDuyetAction === 'reject' ? 'Nhập lý do từ chối...' : 'Nhập ý kiến (không bắt buộc)...'}
              />
            </div>
            
            <div className="flex justify-end gap-3">
              <button 
                onClick={() => setPheDuyetAction(null)} 
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium"
              >
                Hủy
              </button>
              <button
                onClick={handlePheDuyetSubmit}
                disabled={isProcessing}
                className={`px-4 py-2 text-white rounded-lg font-medium disabled:opacity-50 ${
                  pheDuyetAction === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
                }`}
              >
                {isProcessing ? 'Đang xử lý...' : 'Xác nhận'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function TabBaoCao({ thang, nam, canApprove, capBac, onPendingCountChange }: ITabProps) {
  const isCCT = capBac === CapBacVaiTro.CHI_CUC_TRUONG;

  // CCT xem danh sách chờ duyệt
  if (isCCT) {
    return <CCTView thang={thang} nam={nam} canApprove={canApprove} onPendingCountChange={onPendingCountChange} />;
  }
  
  // Phó ĐT, ĐT, Phó CCT xem báo cáo đơn vị
  return <DonViView thang={thang} nam={nam} canApprove={canApprove} />;
}