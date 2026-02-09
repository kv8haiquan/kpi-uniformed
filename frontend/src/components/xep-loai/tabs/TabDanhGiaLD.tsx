/**
 * src/components/xep-loai/tabs/TabDanhGiaLD.tsx
 * ==============================================
 * Tab "Đánh giá LĐ (d,đ,e)" - Phê duyệt đánh giá năng lực lãnh đạo.
 * 
 * ✅ VERIFIED API ENDPOINTS (31/01/2026):
 * ┌────────┬──────────────────────────────────────────────────────────┬──────────────────────────┐
 * │ Method │ Endpoint                                                 │ Mô tả                    │
 * ├────────┼──────────────────────────────────────────────────────────┼──────────────────────────┤
 * │ GET    │ /danh-gia-lanh-dao/dde/nguoi-phe-duyet                   │ Lấy người phê duyệt      │
 * │ GET    │ /danh-gia-lanh-dao/dde/cho-phe-duyet                     │ DS chờ phê duyệt         │
 * │ GET    │ /danh-gia-lanh-dao/dde/lich-su                           │ DS đã phê duyệt          │
 * │ GET    │ /danh-gia-lanh-dao/dde/thang/{thang}/nam/{nam}           │ Lấy đánh giá d,đ,e       │
 * │ POST   │ /danh-gia-lanh-dao/dde                                   │ Tạo/cập nhật d,đ,e       │
 * │ POST   │ /danh-gia-lanh-dao/dde/thang/{thang}/nam/{nam}/gui-duyet │ Gửi duyệt                │
 * │ POST   │ /danh-gia-lanh-dao/dde/{dde_id}/phe-duyet                │ Phê duyệt                │
 * └────────┴──────────────────────────────────────────────────────────┴──────────────────────────┘
 * 
 * Version: 3.4.0 - THÊM LỊCH SỬ PHÊ DUYỆT (31/01/2026)
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import apiClient from '@/lib/axios';
import { ITabProps } from '@/types/xep-loai';
import {
  LoadingSpinner,
  EmptyState,
  ErrorMessage,
  StatusBadge,
} from '../shared';

// =============================================================================
// TYPES
// =============================================================================

interface IDDEItem {
  id: string;
  cong_chuc_id: string;
  cong_chuc?: {
    id: string;
    ma_cc: string;
    ho_ten: string;
    chuc_vu?: string;
  };
  thang: number;
  nam: number;
  d_ket_qua_don_vi: number;
  d_ghi_chu?: string;
  dd_to_chuc_trien_khai: number;
  dd_ghi_chu?: string;
  e_doan_ket_noi_bo: number;
  e_ghi_chu?: string;
  trang_thai: string;
  nguoi_phe_duyet_id?: string;
  nguoi_phe_duyet?: { ho_ten: string } | null;
  ngay_phe_duyet?: string;
  y_kien_phe_duyet?: string;
}

// =============================================================================
// API FUNCTIONS - VERIFIED ENDPOINTS
// =============================================================================

const ddeApi = {
  /**
   * GET /danh-gia-lanh-dao/dde/cho-phe-duyet
   */
  async getChoPheDuyet(params?: { thang?: number; nam?: number }): Promise<IDDEItem[]> {
    const response = await apiClient.get('/danh-gia-lanh-dao/dde/cho-phe-duyet', { params });
    if (Array.isArray(response.data)) return response.data;
    if (response.data?.data && Array.isArray(response.data.data)) return response.data.data;
    return [];
  },

  /**
   * GET /danh-gia-lanh-dao/dde/lich-su
   * Lấy lịch sử đánh giá đã phê duyệt
   */
  async getLichSu(params?: { thang?: number; nam?: number; page?: number; page_size?: number }): Promise<IDDEItem[]> {
    try {
      const response = await apiClient.get('/danh-gia-lanh-dao/dde/lich-su', { 
        params: { ...params, page_size: 100 } 
      });
      if (Array.isArray(response.data)) return response.data;
      if (response.data?.data && Array.isArray(response.data.data)) return response.data.data;
      return [];
    } catch (err) {
      console.warn('[TabDanhGiaLD] /dde/lich-su error:', err);
      return [];
    }
  },

  /**
   * POST /danh-gia-lanh-dao/dde/{dde_id}/phe-duyet
   */
  async pheDuyet(ddeId: string, payload: {
    action: 'APPROVE' | 'REJECT';
    d_phe_duyet?: number;
    dd_phe_duyet?: number;
    e_phe_duyet?: number;
    y_kien?: string;
  }): Promise<void> {
    await apiClient.post(`/danh-gia-lanh-dao/dde/${ddeId}/phe-duyet`, payload);
  },
};

// =============================================================================
// SUB COMPONENTS
// =============================================================================

function DDEIndicator({ label, value, ghiChu }: { label: string; value: number; ghiChu?: string }) {
  const isGood = value === 100;
  return (
    <div className={`p-3 rounded-lg ${isGood ? 'bg-green-50' : 'bg-amber-50'}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className={`text-lg font-bold ${isGood ? 'text-green-600' : 'text-amber-600'}`}>{value}%</span>
      </div>
      {ghiChu && <p className="text-xs text-gray-500 mt-1">{ghiChu}</p>}
    </div>
  );
}

interface DDECardProps {
  item: IDDEItem;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  canApprove: boolean;
}

function DDECard({ item, onApprove, onReject, canApprove }: DDECardProps) {
  const isPending = item.trang_thai === 'CHO_PHE_DUYET';
  const tongDiem = Math.round((item.d_ket_qua_don_vi + item.dd_to_chuc_trien_khai + item.e_doan_ket_noi_bo) / 3);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:border-gray-300 transition-all">
      <div className="flex items-start justify-between gap-2 mb-3">
        <div>
          <h4 className="font-medium text-gray-900">{item.cong_chuc?.ho_ten || 'N/A'}</h4>
          <p className="text-xs text-gray-500">{item.cong_chuc?.ma_cc} • {item.cong_chuc?.chuc_vu}</p>
        </div>
        <div className="text-right">
          <StatusBadge status={isPending ? 'pending' : 'approved'} label={isPending ? 'Chờ duyệt' : 'Đã duyệt'} />
          <p className="text-xs text-gray-500 mt-1">Tháng {item.thang}/{item.nam}</p>
        </div>
      </div>

      <div className="space-y-2 mb-3">
        <DDEIndicator label="d) Kết quả đơn vị" value={item.d_ket_qua_don_vi} ghiChu={item.d_ghi_chu} />
        <DDEIndicator label="đ) Tổ chức triển khai" value={item.dd_to_chuc_trien_khai} ghiChu={item.dd_ghi_chu} />
        <DDEIndicator label="e) Đoàn kết nội bộ" value={item.e_doan_ket_noi_bo} ghiChu={item.e_ghi_chu} />
      </div>

      <div className="flex items-center justify-between p-2 bg-gray-50 rounded-lg mb-3">
        <span className="text-sm font-medium text-gray-700">Điểm TB:</span>
        <span className={`text-lg font-bold ${tongDiem >= 80 ? 'text-green-600' : 'text-amber-600'}`}>{tongDiem}%</span>
      </div>

      {canApprove && isPending && (
        <div className="flex gap-2 pt-3 border-t border-gray-100">
          <button onClick={() => onApprove(item.id)} className="flex-1 px-3 py-1.5 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors">Duyệt</button>
          <button onClick={() => onReject(item.id)} className="flex-1 px-3 py-1.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors">Từ chối</button>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function TabDanhGiaLD({ thang, nam, canApprove, onPendingCountChange }: ITabProps) {
  const [pendingData, setPendingData] = useState<IDDEItem[]>([]);
  const [historyData, setHistoryData] = useState<IDDEItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [viewMode, setViewMode] = useState<'pending' | 'history' | 'all'>('all');
  const [congChucFilter, setCongChucFilter] = useState<string>('all');
  
  // Modal state
  const [selectedItem, setSelectedItem] = useState<IDDEItem | null>(null);
  const [modalAction, setModalAction] = useState<'approve' | 'reject' | null>(null);
  const [yKien, setYKien] = useState('');
  const [dPheDuyet, setDPheDuyet] = useState(100);
  const [ddPheDuyet, setDDPheDuyet] = useState(100);
  const [ePheDuyet, setEPheDuyet] = useState(100);

  // Load data
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const [pending, history] = await Promise.all([
        ddeApi.getChoPheDuyet({ thang, nam }),
        ddeApi.getLichSu({ thang, nam }),
      ]);
      
      setPendingData(pending);
      setHistoryData(history);
    } catch (err) {
      const error = err as Error;
      setError(error.message || 'Có lỗi xảy ra khi tải dữ liệu');
      setPendingData([]);
      setHistoryData([]);
    } finally {
      setIsLoading(false);
    }
  }, [thang, nam]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Update pending count khi data thay đổi
  useEffect(() => {
    onPendingCountChange?.(pendingData.length);
  }, [pendingData, onPendingCountChange]);

  // Computed data based on viewMode
  const displayData = viewMode === 'pending' 
    ? pendingData 
    : viewMode === 'history' 
      ? historyData 
      : [...pendingData, ...historyData];

  // ✅ Danh sách công chức unique để filter
  const uniqueCongChuc = React.useMemo(() => {
    const allItems = [...pendingData, ...historyData];
    const map = new Map<string, { id: string; ho_ten: string; ma_cc: string }>();
    allItems.forEach(item => {
      const id = item.cong_chuc_id || item.cong_chuc?.id || '';
      if (id && !map.has(id)) {
        map.set(id, {
          id,
          ho_ten: item.cong_chuc?.ho_ten || '',
          ma_cc: item.cong_chuc?.ma_cc || '',
        });
      }
    });
    return Array.from(map.values()).sort((a, b) => a.ho_ten.localeCompare(b.ho_ten, 'vi'));
  }, [pendingData, historyData]);

  // Apply congChucFilter
  const filteredDisplayData = React.useMemo(() => {
    if (congChucFilter === 'all') return displayData;
    return displayData.filter(item => {
      const itemCCId = item.cong_chuc_id || item.cong_chuc?.id || '';
      return itemCCId === congChucFilter;
    });
  }, [displayData, congChucFilter]);

  // Handlers
  const handleApprove = (id: string) => {
    const item = filteredDisplayData.find(d => d.id === id);
    if (item) {
      setSelectedItem(item);
      setModalAction('approve');
      setYKien('');
      setDPheDuyet(item.d_ket_qua_don_vi);
      setDDPheDuyet(item.dd_to_chuc_trien_khai);
      setEPheDuyet(item.e_doan_ket_noi_bo);
    }
  };

  const handleReject = (id: string) => {
    const item = filteredDisplayData.find(d => d.id === id);
    if (item) {
      setSelectedItem(item);
      setModalAction('reject');
      setYKien('');
    }
  };

  const handleModalSubmit = async () => {
    if (!selectedItem) return;
    if (modalAction === 'reject' && !yKien.trim()) {
      alert('Vui lòng nhập lý do từ chối');
      return;
    }

    setIsProcessing(true);
    try {
      await ddeApi.pheDuyet(selectedItem.id, {
        action: modalAction === 'approve' ? 'APPROVE' : 'REJECT',
        d_phe_duyet: modalAction === 'approve' ? dPheDuyet : undefined,
        dd_phe_duyet: modalAction === 'approve' ? ddPheDuyet : undefined,
        e_phe_duyet: modalAction === 'approve' ? ePheDuyet : undefined,
        y_kien: yKien || undefined,
      });
      await loadData();
      setSelectedItem(null);
      setModalAction(null);
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra');
    } finally {
      setIsProcessing(false);
    }
  };

  // Render
  if (isLoading) {
    return <div className="flex items-center justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={loadData} />;
  }

  const pendingCount = pendingData.length;
  const historyCount = historyData.length;

  return (
    <div className="space-y-4">
      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-1">Về chỉ tiêu d, đ, e</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• <strong>d) Kết quả đơn vị:</strong> Đơn vị hoàn thành nhiệm vụ (100%) hoặc không (50%)</li>
          <li>• <strong>đ) Tổ chức triển khai:</strong> Tốt (100%) hoặc chưa tốt (50%)</li>
          <li>• <strong>e) Đoàn kết nội bộ:</strong> Tốt (100%) hoặc có vấn đề (50%)</li>
        </ul>
      </div>

      {/* Filter & Stats */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Hiển thị:</span>
            <select
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value as 'pending' | 'history' | 'all')}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Tất cả ({pendingCount + historyCount})</option>
              <option value="pending">Chờ duyệt ({pendingCount})</option>
              <option value="history">Đã duyệt ({historyCount})</option>
            </select>
          </div>

          {/* ✅ Công chức Filter */}
          {uniqueCongChuc.length > 1 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Lãnh đạo:</span>
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
        
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span>Chờ duyệt: <strong className="text-amber-600">{pendingCount}</strong></span>
          <span>Đã duyệt: <strong className="text-green-600">{historyCount}</strong></span>
        </div>
      </div>

      {/* List */}
      {filteredDisplayData.length === 0 ? (
        <EmptyState 
          title={viewMode === 'pending' ? "Không có đánh giá chờ duyệt" : viewMode === 'history' ? "Chưa có lịch sử phê duyệt" : "Không có đánh giá d,đ,e"} 
          description={congChucFilter !== 'all' ? "Không có dữ liệu cho lãnh đạo đã chọn" : viewMode === 'pending' ? "Không có đánh giá năng lực lãnh đạo nào chờ phê duyệt" : "Chưa có đánh giá nào được phê duyệt trong tháng này"} 
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredDisplayData.map((item) => (
            <DDECard key={item.id} item={item} onApprove={handleApprove} onReject={handleReject} canApprove={canApprove} />
          ))}
        </div>
      )}

      {/* Modal */}
      {selectedItem && modalAction && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {modalAction === 'approve' ? 'Phê duyệt đánh giá d,đ,e' : 'Từ chối đánh giá d,đ,e'}
            </h3>

            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <p className="font-medium text-gray-900">{selectedItem.cong_chuc?.ho_ten}</p>
              <p className="text-sm text-gray-600 mt-1">{selectedItem.cong_chuc?.ma_cc} • {selectedItem.cong_chuc?.chuc_vu}</p>
              <p className="text-sm text-gray-500 mt-1">Tháng {selectedItem.thang}/{selectedItem.nam}</p>
            </div>

            {modalAction === 'approve' && (
              <div className="mb-4 space-y-3">
                <p className="text-sm font-medium text-gray-700">Điều chỉnh giá trị (nếu cần):</p>
                {[
                  { label: 'd) Kết quả đơn vị:', value: dPheDuyet, setValue: setDPheDuyet, opt1: '100% (Đạt)', opt2: '50% (Không đạt)' },
                  { label: 'đ) Tổ chức triển khai:', value: ddPheDuyet, setValue: setDDPheDuyet, opt1: '100% (Tốt)', opt2: '50% (Chưa tốt)' },
                  { label: 'e) Đoàn kết nội bộ:', value: ePheDuyet, setValue: setEPheDuyet, opt1: '100% (Tốt)', opt2: '50% (Có vấn đề)' },
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between gap-4">
                    <label className="text-sm text-gray-600">{item.label}</label>
                    <select
                      value={item.value}
                      onChange={(e) => item.setValue(parseInt(e.target.value))}
                      className="px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value={100}>{item.opt1}</option>
                      <option value={50}>{item.opt2}</option>
                    </select>
                  </div>
                ))}
              </div>
            )}

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {modalAction === 'approve' ? 'Ý kiến (không bắt buộc)' : <>Lý do từ chối <span className="text-red-500">*</span></>}
              </label>
              <textarea
                value={yKien}
                onChange={(e) => setYKien(e.target.value)}
                rows={modalAction === 'approve' ? 2 : 3}
                required={modalAction === 'reject'}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder={modalAction === 'approve' ? 'Nhập ý kiến...' : 'Nhập lý do từ chối...'}
              />
            </div>

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