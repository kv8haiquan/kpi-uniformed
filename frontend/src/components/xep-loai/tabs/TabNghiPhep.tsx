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
};

// =============================================================================
// SUB COMPONENTS
// =============================================================================

interface NghiPhepCardProps {
  item: INghiPhepItem;
  isSelected: boolean;
  onSelect: (id: string, selected: boolean) => void;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  canApprove: boolean;
}

function NghiPhepCard({ item, isSelected, onSelect, onApprove, onReject, canApprove }: NghiPhepCardProps) {
  const isPending = item.trang_thai === 'CHO_PHE_DUYET';
  const isApproved = item.trang_thai === 'DA_PHE_DUYET';
  const isRejected = item.trang_thai === 'TU_CHOI';

  const getBadgeColor = (loai: string): string => {
    if (['PHEP_NAM'].includes(loai)) return 'bg-blue-100 text-blue-700';
    if (['NGHI_OM'].includes(loai)) return 'bg-red-100 text-red-700';
    if (['NGHI_LE', 'NGHI_TET'].includes(loai)) return 'bg-amber-100 text-amber-700';
    if (['NGHI_TUAN'].includes(loai)) return 'bg-green-100 text-green-700';
    return 'bg-gray-100 text-gray-700';
  };

  const getStatusBadge = () => {
    if (isApproved) {
      return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-green-100 text-green-700">Đã duyệt</span>;
    }
    if (isRejected) {
      return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-red-100 text-red-700">Từ chối</span>;
    }
    if (isPending) {
      return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-amber-100 text-amber-700">Chờ duyệt</span>;
    }
    return null;
  };

  return (
    <div className={`bg-white rounded-lg border p-4 transition-all ${isSelected ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200 hover:border-gray-300'}`}>
      <div className="flex items-start gap-3">
        {canApprove && isPending && (
          <input
            type="checkbox"
            checked={isSelected}
            onChange={(e) => onSelect(item.id, e.target.checked)}
            className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <div>
              <h4 className="font-medium text-gray-900">{item.cong_chuc?.ho_ten || 'N/A'}</h4>
              <p className="text-xs text-gray-500">{item.cong_chuc?.ma_cc}</p>
              {item.cong_chuc?.don_vi_ten && (
                <p className="text-xs text-gray-400">{item.cong_chuc.don_vi_ten}</p>
              )}
            </div>
            <div className="flex flex-col items-end gap-1">
              <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${getBadgeColor(item.loai_nghi)}`}>
                {LOAI_NGHI_LABELS[item.loai_nghi] || item.loai_nghi}
              </span>
              {getStatusBadge()}
            </div>
          </div>

          <div className="space-y-1 text-sm">
            <p className="text-gray-700">
              <span className="font-medium">Thời gian:</span>{' '}
              {getNgayBatDau(item) ? format(parseISO(getNgayBatDau(item)!), 'dd/MM/yyyy') : 'N/A'}
              {getNgayKetThuc(item) && getNgayKetThuc(item) !== getNgayBatDau(item) && (
                <> - {format(parseISO(getNgayKetThuc(item)!), 'dd/MM/yyyy')}</>
              )}
            </p>
            <p className="text-gray-600">Số ngày: <strong>{item.so_ngay}</strong></p>
            {item.ly_do && <p className="text-gray-600 text-xs">Lý do: {item.ly_do}</p>}
          </div>

          {/* Action buttons - chỉ hiện khi pending */}
          {canApprove && isPending && (
            <div className="flex gap-2 mt-3 pt-3 border-t border-gray-100">
              <button 
                onClick={() => onApprove(item.id)} 
                className="flex-1 px-3 py-1.5 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
              >
                Duyệt
              </button>
              <button 
                onClick={() => onReject(item.id)} 
                className="flex-1 px-3 py-1.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
              >
                Từ chối
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function TabNghiPhep({ canApprove, onPendingCountChange }: ITabProps) {
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

  // Load counts
  const loadCounts = useCallback(async () => {
    try {
      const [pendingRes, lichSuRes] = await Promise.all([
        nghiPhepApi.getChoPheDuyet(),
        nghiPhepApi.getLichSu(),
      ]);
      
      const pendingCount = pendingRes.length;
      const approvedCount = lichSuRes.filter(d => d.trang_thai === 'DA_PHE_DUYET').length;
      const rejectedCount = lichSuRes.filter(d => d.trang_thai === 'TU_CHOI').length;
      
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
  }, [onPendingCountChange]);

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
      
      setData(items);
    } catch (err) {
      const error = err as Error;
      setError(error.message || 'Có lỗi xảy ra khi tải dữ liệu');
      setData([]);
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    loadCounts();
  }, [loadCounts]);

  const refreshAll = useCallback(async () => {
    await Promise.all([loadData(), loadCounts()]);
  }, [loadData, loadCounts]);

  // Handlers
  const handleSelect = (id: string, selected: boolean) => {
    const newSelected = new Set(selectedIds);
    selected ? newSelected.add(id) : newSelected.delete(id);
    setSelectedIds(newSelected);
  };

  const handleSelectAll = () => {
    const pendingItems = data.filter(d => d.trang_thai === 'CHO_PHE_DUYET');
    setSelectedIds(selectedIds.size === pendingItems.length ? new Set() : new Set(pendingItems.map(d => d.id)));
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

  const pendingItems = data.filter(d => d.trang_thai === 'CHO_PHE_DUYET');

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
          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Trạng thái:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Tất cả ({counts.total})</option>
              <option value="pending">Chờ duyệt ({counts.pending})</option>
              <option value="approved">Đã duyệt ({counts.approved})</option>
              <option value="rejected">Từ chối ({counts.rejected})</option>
            </select>
          </div>

          {/* ✅ Công chức Filter */}
          {uniqueCongChuc.length > 1 && (
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
        
        {canApprove && counts.pending > 0 && statusFilter !== 'approved' && statusFilter !== 'rejected' && (
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

      {/* List */}
      {filteredData.length === 0 ? (
        <EmptyState 
          title="Không có đơn nghỉ" 
          description={statusFilter === 'pending' ? 'Không có đơn nghỉ phép nào chờ phê duyệt' : congChucFilter !== 'all' ? 'Không có dữ liệu cho công chức đã chọn' : 'Không có dữ liệu'} 
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredData.map((item) => (
            <NghiPhepCard
              key={item.id}
              item={item}
              isSelected={selectedIds.has(item.id)}
              onSelect={handleSelect}
              onApprove={handleApprove}
              onReject={handleReject}
              canApprove={canApprove}
            />
          ))}
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
    </div>
  );
}