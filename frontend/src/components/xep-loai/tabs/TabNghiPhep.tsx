/**
 * src/components/xep-loai/tabs/TabNghiPhep.tsx
 * =============================================
 * Tab "Duyệt nghỉ phép" - Phê duyệt đơn nghỉ phép 1 CẤP.
 * 
 * ✅ VERIFIED API ENDPOINTS (31/01/2026):
 * ┌────────┬─────────────────────────────────────────┬─────────────────────────────┐
 * │ Method │ Endpoint                                │ Mô tả                       │
 * ├────────┼─────────────────────────────────────────┼─────────────────────────────┤
 * │ GET    │ /nghi-phep/cho-phe-duyet                │ DS chờ phê duyệt            │
 * │ GET    │ /nghi-phep/lich-su                      │ Lịch sử đã duyệt/từ chối    │
 * │ POST   │ /nghi-phep/{nghi_phep_id}/phe-duyet     │ Phê duyệt                   │
 * │ POST   │ /nghi-phep/{nghi_phep_id}/tu-choi       │ Từ chối                     │
 * └────────┴─────────────────────────────────────────┴─────────────────────────────┘
 * 
 * Version: 4.0.0 - ĐƠN GIẢN HÓA 1 CẤP (31/01/2026)
 * - Bỏ hoàn toàn logic cấp 1, cấp 2
 * - Đội trưởng duyệt là XONG
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { format, parseISO } from 'date-fns';
import apiClient from '@/lib/axios';
import { ITabProps } from '@/types/xep-loai';
import {
  LoadingSpinner,
  EmptyState,
  ErrorMessage,
} from '../shared';

// =============================================================================
// TYPES
// =============================================================================

interface INghiPhepItem {
  id: string;
  cong_chuc_id?: string;
  cong_chuc?: {
    id: string;
    ma_cc: string;
    ho_ten: string;
    chuc_vu?: string;
    don_vi_ten?: string;
  };
  loai_nghi: string;
  loai_nghi_ten?: string;
  tu_ngay?: string;
  den_ngay?: string;
  ngay_bat_dau?: string;
  ngay_ket_thuc?: string;
  so_ngay: number;
  ly_do?: string;
  trang_thai: string;
  trang_thai_ten?: string;
  nguoi_phe_duyet_id?: string;
  nguoi_phe_duyet?: {
    id: string;
    ho_ten: string;
  };
  thang_ap_dung?: number;
  nam_ap_dung?: number;
}

// Helper để lấy ngày bắt đầu (support cả 2 format)
const getNgayBatDau = (item: INghiPhepItem): string | undefined => {
  return item.tu_ngay || item.ngay_bat_dau;
};

const getNgayKetThuc = (item: INghiPhepItem): string | undefined => {
  return item.den_ngay || item.ngay_ket_thuc;
};

type StatusFilter = 'all' | 'pending' | 'approved' | 'rejected';

const LOAI_NGHI_LABELS: Record<string, string> = {
  PHEP_NAM: 'Phép năm',
  NGHI_OM: 'Nghỉ ốm',
  NGHI_LE: 'Nghỉ lễ',
  NGHI_TET: 'Nghỉ Tết',
  NGHI_TUAN: 'Nghỉ tuần',
  VIEC_RIENG: 'Việc riêng',
  KHONG_LUONG: 'Không lương',
  THAI_SAN: 'Thai sản',
  NGHI_BU: 'Nghỉ bù',
  KHAC: 'Khác',
};

// =============================================================================
// API FUNCTIONS
// =============================================================================

/**
 * Helper function để parse response từ nhiều format khác nhau
 */
function parseResponseData<T>(responseData: any): T[] {
  if (!responseData) return [];
  
  // Format 1: Direct array
  if (Array.isArray(responseData)) {
    return responseData;
  }
  
  // Format 2: { success: true, data: { items: [...] } }
  if (responseData?.data?.items && Array.isArray(responseData.data.items)) {
    return responseData.data.items;
  }
  
  // Format 3: { data: [...] }
  if (responseData?.data && Array.isArray(responseData.data)) {
    return responseData.data;
  }
  
  // Format 4: { items: [...] }
  if (responseData?.items && Array.isArray(responseData.items)) {
    return responseData.items;
  }
  
  console.warn('[parseResponseData] Could not find array in response:', Object.keys(responseData));
  return [];
}

const nghiPhepApi = {
  /**
   * GET /nghi-phep/cho-phe-duyet
   */
  async getChoPheDuyet(): Promise<INghiPhepItem[]> {
    console.log('[TabNghiPhep] Calling GET /nghi-phep/cho-phe-duyet');
    const response = await apiClient.get('/nghi-phep/cho-phe-duyet');
    console.log('[TabNghiPhep] Raw Response:', response.data);
    const data = parseResponseData<INghiPhepItem>(response.data);
    console.log('[TabNghiPhep] Parsed pending data:', data.length, 'items');
    return data;
  },

  /**
   * GET /nghi-phep/lich-su
   */
  async getLichSu(params?: { trang_thai?: 'DA_PHE_DUYET' | 'TU_CHOI' }): Promise<INghiPhepItem[]> {
    console.log('[TabNghiPhep] Calling GET /nghi-phep/lich-su with params:', params);
    try {
      const response = await apiClient.get('/nghi-phep/lich-su', { params });
      const data = parseResponseData<INghiPhepItem>(response.data);
      console.log('[TabNghiPhep] Parsed lich-su data:', data.length, 'items');
      return data;
    } catch (error) {
      console.warn('[TabNghiPhep] /nghi-phep/lich-su error:', error);
      return [];
    }
  },

  /**
   * POST /nghi-phep/{nghi_phep_id}/phe-duyet
   */
  async pheDuyet(nghiPhepId: string, payload?: { ghi_chu?: string }): Promise<void> {
    await apiClient.post(`/nghi-phep/${nghiPhepId}/phe-duyet`, payload || {});
  },

  /**
   * POST /nghi-phep/{nghi_phep_id}/tu-choi
   */
  async tuChoi(nghiPhepId: string, payload: { ly_do_tu_choi: string }): Promise<void> {
    await apiClient.post(`/nghi-phep/${nghiPhepId}/tu-choi`, payload);
  },

  /**
   * POST /nghi-phep/{nghi_phep_id}/tra-lai
   */
  async traLai(nghiPhepId: string, lyDo: string): Promise<void> {
    await apiClient.post(`/nghi-phep/${nghiPhepId}/tra-lai`, { ly_do: lyDo });
  },
};

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

const getBadgeColor = (loai: string): string => {
  if (['PHEP_NAM'].includes(loai)) return 'bg-blue-100 text-blue-700';
  if (['NGHI_OM'].includes(loai)) return 'bg-red-100 text-red-700';
  if (['NGHI_LE', 'NGHI_TET'].includes(loai)) return 'bg-amber-100 text-amber-700';
  if (['NGHI_TUAN'].includes(loai)) return 'bg-green-100 text-green-700';
  return 'bg-gray-100 text-gray-700';
};

const getStatusBadge = (trangThai: string) => {
  if (trangThai === 'DA_PHE_DUYET') {
    return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-green-100 text-green-700">Đã duyệt</span>;
  }
  if (trangThai === 'TU_CHOI') {
    return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-red-100 text-red-700">Từ chối</span>;
  }
  if (trangThai === 'CHO_PHE_DUYET') {
    return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-amber-100 text-amber-700">Chờ duyệt</span>;
  }
  return null;
};

/** Số ngày trong tháng */
const soNgayTrongThang = (thang: number, nam: number): number => {
  return new Date(nam, thang, 0).getDate();
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function TabNghiPhep({ thang, nam, canApprove, onPendingCountChange }: ITabProps) {
  const [data, setData] = useState<INghiPhepItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [congChucFilter, setCongChucFilter] = useState<string>('all');
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Counts state
  const [counts, setCounts] = useState({ pending: 0, approved: 0, rejected: 0, total: 0 });
  
  // Modal state
  const [selectedItem, setSelectedItem] = useState<INghiPhepItem | null>(null);
  const [modalAction, setModalAction] = useState<'approve' | 'reject' | null>(null);
  const [lyDo, setLyDo] = useState('');
  const [ghiChu, setGhiChu] = useState('');

  // Filter theo tháng/năm dựa trên thang_ap_dung hoặc tu_ngay
  const filterTheoThangNam = useCallback((items: INghiPhepItem[]): INghiPhepItem[] => {
    return items.filter(item => {
      // Ưu tiên thang_ap_dung/nam_ap_dung
      if (item.thang_ap_dung && item.nam_ap_dung) {
        return item.thang_ap_dung === thang && item.nam_ap_dung === nam;
      }
      // Fallback: lấy tháng/năm từ tu_ngay
      const ngayBD = getNgayBatDau(item);
      if (ngayBD) {
        const d = parseISO(ngayBD);
        return (d.getMonth() + 1) === thang && d.getFullYear() === nam;
      }
      return false;
    });
  }, [thang, nam]);

  // Load counts
  const loadCounts = useCallback(async () => {
    try {
      const [pendingRes, lichSuRes] = await Promise.all([
        nghiPhepApi.getChoPheDuyet(),
        nghiPhepApi.getLichSu(),
      ]);

      // Filter theo tháng/năm
      const pendingFiltered = filterTheoThangNam(pendingRes);
      const lichSuFiltered = filterTheoThangNam(lichSuRes);

      const pendingCount = pendingFiltered.length;
      const approvedCount = lichSuFiltered.filter(d => d.trang_thai === 'DA_PHE_DUYET').length;
      const rejectedCount = lichSuFiltered.filter(d => d.trang_thai === 'TU_CHOI').length;

      setCounts({
        pending: pendingCount,
        approved: approvedCount,
        rejected: rejectedCount,
        total: pendingCount + approvedCount + rejectedCount,
      });

      if (onPendingCountChange) {
        onPendingCountChange(pendingCount);
      }
    } catch (err) {
      console.error('[TabNghiPhep] Error loading counts:', err);
    }
  }, [onPendingCountChange, filterTheoThangNam]);

  // Load data theo statusFilter
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      let items: INghiPhepItem[] = [];

      if (statusFilter === 'pending') {
        items = await nghiPhepApi.getChoPheDuyet();
      } else if (statusFilter === 'approved') {
        items = await nghiPhepApi.getLichSu({ trang_thai: 'DA_PHE_DUYET' });
      } else if (statusFilter === 'rejected') {
        items = await nghiPhepApi.getLichSu({ trang_thai: 'TU_CHOI' });
      } else {
        // Tất cả: gộp pending + lich-su
        const [pending, lichSu] = await Promise.all([
          nghiPhepApi.getChoPheDuyet(),
          nghiPhepApi.getLichSu(),
        ]);
        items = [...pending, ...lichSu];
      }

      // Filter theo tháng/năm đang chọn
      setData(filterTheoThangNam(items));
    } catch (err) {
      const error = err as Error;
      setError(error.message || 'Có lỗi xảy ra khi tải dữ liệu');
      setData([]);
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter, filterTheoThangNam]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    loadCounts();
  }, [loadCounts]);

  // Clear selected items when filter changes
  useEffect(() => {
    setSelectedIds(new Set());
  }, [statusFilter, congChucFilter]);

  const refreshAll = useCallback(async () => {
    await Promise.all([loadData(), loadCounts()]);
  }, [loadData, loadCounts]);

  // Handlers
  const handleSelect = (id: string, selected: boolean) => {
    const newSelected = new Set(selectedIds);
    selected ? newSelected.add(id) : newSelected.delete(id);
    setSelectedIds(newSelected);
  };

  const handleApprove = (id: string) => {
    const item = data.find(d => d.id === id);
    if (item) {
      setSelectedItem(item);
      setModalAction('approve');
      setGhiChu('');
    }
  };

  const handleReject = (id: string) => {
    const item = data.find(d => d.id === id);
    if (item) {
      setSelectedItem(item);
      setModalAction('reject');
      setLyDo('');
    }
  };

  // ===== TRẢ LẠI ĐÃ DUYỆT =====
  const [traLaiItem, setTraLaiItem] = useState<INghiPhepItem | null>(null);
  const [traLaiLyDo, setTraLaiLyDo] = useState('');
  const [isTraLai, setIsTraLai] = useState(false);

  const handleTraLai = (item: INghiPhepItem) => {
    setTraLaiItem(item);
    setTraLaiLyDo('');
  };

  const handleSubmitTraLai = async () => {
    if (!traLaiItem || !traLaiLyDo.trim()) return;
    setIsTraLai(true);
    try {
      await nghiPhepApi.traLai(traLaiItem.id, traLaiLyDo);
      await refreshAll();
      setTraLaiItem(null);
      setTraLaiLyDo('');
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra khi trả lại');
    } finally {
      setIsTraLai(false);
    }
  };

  const handleModalSubmit = async () => {
    if (!selectedItem) return;
    if (modalAction === 'reject' && !lyDo.trim()) {
      alert('Vui lòng nhập lý do từ chối');
      return;
    }

    setIsProcessing(true);
    try {
      if (modalAction === 'approve') {
        await nghiPhepApi.pheDuyet(selectedItem.id, { ghi_chu: ghiChu || undefined });
      } else {
        await nghiPhepApi.tuChoi(selectedItem.id, { ly_do_tu_choi: lyDo });
      }
      await refreshAll();
      setSelectedItem(null);
      setModalAction(null);
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleBulkApprove = async () => {
    if (selectedIds.size === 0) return;
    if (!window.confirm(`Phê duyệt ${selectedIds.size} đơn nghỉ đã chọn?`)) return;

    setIsProcessing(true);
    try {
      const ids = Array.from(selectedIds);
      for (const id of ids) {
        await nghiPhepApi.pheDuyet(id);
      }
      await refreshAll();
      setSelectedIds(new Set());
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra');
    } finally {
      setIsProcessing(false);
    }
  };

  // ✅ Danh sách công chức unique để filter
  const uniqueCongChuc = React.useMemo(() => {
    const map = new Map<string, { id: string; ho_ten: string; ma_cc: string }>();
    data.forEach(item => {
      const id = item.cong_chuc_id || item.cong_chuc?.id || item.cong_chuc?.ho_ten || '';
      if (id && !map.has(id)) {
        map.set(id, {
          id,
          ho_ten: item.cong_chuc?.ho_ten || '',
          ma_cc: item.cong_chuc?.ma_cc || '',
        });
      }
    });
    return Array.from(map.values()).sort((a, b) => a.ho_ten.localeCompare(b.ho_ten, 'vi'));
  }, [data]);

  // Apply congChucFilter
  const filteredData = React.useMemo(() => {
    if (congChucFilter === 'all') return data;
    return data.filter(item => {
      const itemCCId = item.cong_chuc_id || item.cong_chuc?.id || item.cong_chuc?.ho_ten || '';
      return itemCCId === congChucFilter;
    });
  }, [data, congChucFilter]);

  // ✅ Counts theo filteredData (theo CC đã chọn)
  const filteredCounts = React.useMemo(() => {
    const pending = filteredData.filter(d => d.trang_thai === 'CHO_PHE_DUYET').length;
    const approved = filteredData.filter(d => d.trang_thai === 'DA_PHE_DUYET').length;
    const rejected = filteredData.filter(d => d.trang_thai === 'TU_CHOI').length;
    return { pending, approved, rejected, total: filteredData.length };
  }, [filteredData]);

  // ✅ pendingItems từ filteredData (theo CC đã chọn)
  const pendingItems = filteredData.filter(d => d.trang_thai === 'CHO_PHE_DUYET');

  const handleSelectAll = () => {
    setSelectedIds(selectedIds.size === pendingItems.length ? new Set() : new Set(pendingItems.map(d => d.id)));
  };

  // Render
  if (isLoading) {
    return <div className="flex items-center justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={loadData} />;
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white rounded-lg p-4 border border-gray-200">
        <div className="flex items-center gap-4">
          {/* Status Filter - counts theo CC đã chọn */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Trạng thái:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Tất cả ({filteredCounts.total})</option>
              <option value="pending">Chờ duyệt ({filteredCounts.pending})</option>
              <option value="approved">Đã duyệt ({filteredCounts.approved})</option>
              <option value="rejected">Từ chối ({filteredCounts.rejected})</option>
            </select>
          </div>

          {/* Công chức Filter - luôn hiển thị */}
          {uniqueCongChuc.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Công chức:</span>
              <select
                value={congChucFilter}
                onChange={(e) => setCongChucFilter(e.target.value)}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 max-w-[220px]"
              >
                <option value="all">Tất cả ({uniqueCongChuc.length})</option>
                {uniqueCongChuc.map(cc => (
                  <option key={cc.id} value={cc.id}>
                    {cc.ho_ten} {cc.ma_cc ? `(${cc.ma_cc})` : ''}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {canApprove && pendingItems.length > 0 && statusFilter !== 'approved' && statusFilter !== 'rejected' && (
          <div className="flex items-center gap-3">
            <button
              onClick={handleSelectAll}
              className="px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {selectedIds.size === pendingItems.length ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
            </button>
            {selectedIds.size > 0 && (
              <button
                onClick={handleBulkApprove}
                disabled={isProcessing}
                className="px-4 py-1.5 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors disabled:opacity-50"
              >
                {isProcessing ? 'Đang xử lý...' : `Duyệt ${selectedIds.size} đã chọn`}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Table */}
      {filteredData.length === 0 ? (
        <EmptyState
          title="Không có đơn nghỉ"
          description={statusFilter === 'pending' ? 'Không có đơn nghỉ phép nào chờ phê duyệt' : congChucFilter !== 'all' ? 'Không có dữ liệu cho công chức đã chọn' : 'Không có dữ liệu'}
        />
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {canApprove && (
                    <th className="w-10 px-3 py-3 text-center">
                      <input
                        type="checkbox"
                        checked={selectedIds.size > 0 && selectedIds.size === pendingItems.length}
                        onChange={handleSelectAll}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        title="Chọn tất cả chờ duyệt"
                      />
                    </th>
                  )}
                  <th className="px-3 py-3 text-left font-medium text-gray-700">Công chức</th>
                  <th className="px-3 py-3 text-center font-medium text-gray-700 whitespace-nowrap">Thời gian</th>
                  <th className="px-3 py-3 text-center font-medium text-gray-700 w-20">Số ngày</th>
                  <th className="px-3 py-3 text-left font-medium text-gray-700 min-w-[150px]">Lý do</th>
                  <th className="px-3 py-3 text-center font-medium text-gray-700">Loại nghỉ</th>
                  <th className="px-3 py-3 text-center font-medium text-gray-700">Trạng thái</th>
                  {canApprove && (
                    <th className="px-3 py-3 text-center font-medium text-gray-700">Thao tác</th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredData.map((item) => {
                  const isPending = item.trang_thai === 'CHO_PHE_DUYET';
                  const isApproved = item.trang_thai === 'DA_PHE_DUYET';
                  return (
                    <tr key={item.id} className={`hover:bg-gray-50 transition-colors ${selectedIds.has(item.id) ? 'bg-blue-50' : ''}`}>
                      {canApprove && (
                        <td className="w-10 px-3 py-3 text-center">
                          {isPending && (
                            <input
                              type="checkbox"
                              checked={selectedIds.has(item.id)}
                              onChange={(e) => handleSelect(item.id, e.target.checked)}
                              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                            />
                          )}
                        </td>
                      )}
                      {/* Công chức */}
                      <td className="px-3 py-3">
                        <div>
                          <p className="font-medium text-gray-900 text-sm">{item.cong_chuc?.ho_ten || 'N/A'}</p>
                          <p className="text-xs text-gray-500">{item.cong_chuc?.ma_cc}</p>
                          {item.cong_chuc?.don_vi_ten && (
                            <p className="text-xs text-gray-400">{item.cong_chuc.don_vi_ten}</p>
                          )}
                        </div>
                      </td>
                      {/* Thời gian */}
                      <td className="px-3 py-3 text-center text-sm text-gray-600 whitespace-nowrap">
                        {getNgayBatDau(item) ? format(parseISO(getNgayBatDau(item)!), 'dd/MM/yyyy') : 'N/A'}
                        {getNgayKetThuc(item) && getNgayKetThuc(item) !== getNgayBatDau(item) && (
                          <>
                            <br />
                            <span className="text-gray-400">→</span> {format(parseISO(getNgayKetThuc(item)!), 'dd/MM/yyyy')}
                          </>
                        )}
                      </td>
                      {/* Số ngày */}
                      <td className="px-3 py-3 text-center">
                        <span className="font-semibold text-blue-600">{item.so_ngay}</span>
                      </td>
                      {/* Lý do */}
                      <td className="px-3 py-3">
                        {item.ly_do ? (
                          <p className="text-xs text-gray-700 whitespace-pre-wrap break-words max-w-[250px]">{item.ly_do}</p>
                        ) : (
                          <span className="text-gray-300 text-xs">—</span>
                        )}
                      </td>
                      {/* Loại nghỉ */}
                      <td className="px-3 py-3 text-center">
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full whitespace-nowrap ${getBadgeColor(item.loai_nghi)}`}>
                          {LOAI_NGHI_LABELS[item.loai_nghi] || item.loai_nghi}
                        </span>
                      </td>
                      {/* Trạng thái */}
                      <td className="px-3 py-3 text-center">
                        {getStatusBadge(item.trang_thai)}
                      </td>
                      {/* Thao tác */}
                      {canApprove && (
                        <td className="px-3 py-3">
                          <div className="flex items-center justify-center gap-1.5">
                            {isPending && (
                              <>
                                <button
                                  onClick={() => handleApprove(item.id)}
                                  className="px-2.5 py-1 text-xs font-medium text-white bg-green-600 hover:bg-green-700 rounded transition-colors"
                                >
                                  Duyệt
                                </button>
                                <button
                                  onClick={() => handleReject(item.id)}
                                  className="px-2.5 py-1 text-xs font-medium text-white bg-red-600 hover:bg-red-700 rounded transition-colors"
                                >
                                  Từ chối
                                </button>
                              </>
                            )}
                            {isApproved && (
                              <button
                                onClick={() => handleTraLai(item)}
                                className="px-2 py-1 text-xs font-medium text-orange-700 bg-orange-50 hover:bg-orange-100 border border-orange-200 rounded transition-colors whitespace-nowrap"
                              >
                                ↩ Trả lại
                              </button>
                            )}
                          </div>
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Tổng kết khi chọn công chức cụ thể */}
          {congChucFilter !== 'all' && filteredData.length > 0 && (() => {
            const soNgayThang = soNgayTrongThang(thang, nam);
            const approvedItems = filteredData.filter(d => d.trang_thai === 'DA_PHE_DUYET');
            const pendingItems2 = filteredData.filter(d => d.trang_thai === 'CHO_PHE_DUYET');
            const ngayNghiThucTe = approvedItems.reduce((sum, d) => sum + d.so_ngay, 0);
            const ngayNghiTamTinh = pendingItems2.reduce((sum, d) => sum + d.so_ngay, 0);
            const ngayLamViecThucTe = soNgayThang - ngayNghiThucTe;
            const ngayLamViecTamTinh = soNgayThang - ngayNghiThucTe - ngayNghiTamTinh;
            const ccInfo = filteredData[0]?.cong_chuc;
            return (
              <div className="border-t-2 border-gray-200 bg-gray-50 px-4 py-3">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="text-sm text-gray-700">
                    <span className="font-medium">{ccInfo?.ho_ten}</span>
                    <span className="text-gray-400 mx-1">•</span>
                    <span className="text-gray-500">T{thang}/{nam} ({soNgayThang} ngày)</span>
                    <span className="text-gray-400 mx-1">•</span>
                    <span className="text-gray-500">{filteredData.length} đơn nghỉ</span>
                  </div>
                  <div className="flex items-center gap-4">
                    {/* Thực tế (đã duyệt) */}
                    <div className="text-center px-3 py-1 bg-white rounded-lg border border-gray-200">
                      <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Thực tế</p>
                      <div className="flex items-center gap-3 mt-0.5">
                        <div>
                          <p className="text-xs text-gray-500">Nghỉ</p>
                          <p className="text-base font-bold text-red-600">{ngayNghiThucTe}</p>
                        </div>
                        <div className="text-gray-300">|</div>
                        <div>
                          <p className="text-xs text-gray-500">Làm việc</p>
                          <p className="text-base font-bold text-green-600">{ngayLamViecThucTe}</p>
                        </div>
                      </div>
                    </div>
                    {/* Tạm tính (bao gồm chờ duyệt) */}
                    {ngayNghiTamTinh > 0 && (
                      <div className="text-center px-3 py-1 bg-amber-50 rounded-lg border border-amber-200">
                        <p className="text-[10px] text-amber-600 font-medium uppercase tracking-wide">Tạm tính</p>
                        <div className="flex items-center gap-3 mt-0.5">
                          <div>
                            <p className="text-xs text-gray-500">Nghỉ</p>
                            <p className="text-base font-bold text-red-600">{ngayNghiThucTe + ngayNghiTamTinh}</p>
                          </div>
                          <div className="text-gray-300">|</div>
                          <div>
                            <p className="text-xs text-gray-500">Làm việc</p>
                            <p className={`text-base font-bold ${ngayLamViecTamTinh >= 0 ? 'text-amber-600' : 'text-red-600'}`}>{ngayLamViecTamTinh}</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })()}
        </div>
      )}

      {/* Modal */}
      {selectedItem && modalAction && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {modalAction === 'approve' ? 'Phê duyệt đơn nghỉ' : 'Từ chối đơn nghỉ'}
            </h3>
            
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <p className="font-medium text-gray-900">{selectedItem.cong_chuc?.ho_ten}</p>
              <p className="text-sm text-gray-600 mt-1">{selectedItem.cong_chuc?.ma_cc}</p>
              <p className="text-sm text-gray-500 mt-1">
                {LOAI_NGHI_LABELS[selectedItem.loai_nghi]} • {selectedItem.so_ngay} ngày
              </p>
              <p className="text-sm text-gray-500">
                {getNgayBatDau(selectedItem) ? format(parseISO(getNgayBatDau(selectedItem)!), 'dd/MM/yyyy') : 'N/A'}
                {getNgayKetThuc(selectedItem) && getNgayKetThuc(selectedItem) !== getNgayBatDau(selectedItem) && (
                  <> - {format(parseISO(getNgayKetThuc(selectedItem)!), 'dd/MM/yyyy')}</>
                )}
              </p>
            </div>

            {modalAction === 'approve' ? (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Ghi chú (không bắt buộc)</label>
                <textarea
                  value={ghiChu}
                  onChange={(e) => setGhiChu(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Nhập ghi chú..."
                />
              </div>
            ) : (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Lý do từ chối <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={lyDo}
                  onChange={(e) => setLyDo(e.target.value)}
                  rows={3}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Nhập lý do từ chối..."
                />
              </div>
            )}

            <div className="flex justify-end gap-3">
              <button
                onClick={() => { setSelectedItem(null); setModalAction(null); }}
                disabled={isProcessing}
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
              >
                Hủy
              </button>
              <button
                onClick={handleModalSubmit}
                disabled={isProcessing}
                className={`px-4 py-2 text-white rounded-lg transition-colors disabled:opacity-50 ${modalAction === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}`}
              >
                {isProcessing ? 'Đang xử lý...' : modalAction === 'approve' ? 'Phê duyệt' : 'Từ chối'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Trả lại nghỉ phép đã duyệt */}
      {traLaiItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-orange-700">↩ Trả lại đơn nghỉ đã duyệt</h3>
              <button onClick={() => setTraLaiItem(null)} className="p-1 text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg text-sm text-orange-800">
                ⚠️ Đơn nghỉ phép của <strong>{traLaiItem.cong_chuc?.ho_ten || 'N/A'}</strong> ({traLaiItem.so_ngay} ngày) sẽ được chuyển về trạng thái <strong>Chờ phê duyệt</strong>.
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Lý do trả lại <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={traLaiLyDo}
                  onChange={(e) => setTraLaiLyDo(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 text-sm"
                  rows={3}
                  maxLength={500}
                  placeholder="Nhập lý do trả lại..."
                  required
                />
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
              <button onClick={() => setTraLaiItem(null)} className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">Hủy</button>
              <button
                onClick={handleSubmitTraLai}
                disabled={isTraLai || !traLaiLyDo.trim()}
                className="px-4 py-2 text-white bg-orange-600 hover:bg-orange-700 rounded-lg transition-colors disabled:opacity-50"
              >
                {isTraLai ? 'Đang xử lý...' : 'Xác nhận trả lại'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}