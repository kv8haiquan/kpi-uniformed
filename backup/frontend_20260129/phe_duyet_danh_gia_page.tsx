/**
 * src/app/(main)/danh-gia/phe-duyet/page.tsx
 * ==========================================
 * Trang Danh sách Phê duyệt Tiêu chí chung - Dành cho Lãnh đạo.
 *
 * Features:
 * - Danh sách đơn CHO_PHE_DUYET
 * - Checkbox chọn nhiều + Phê duyệt hàng loạt
 * - Phê duyệt nhanh từng đơn
 * - Xem chi tiết để điều chỉnh
 *
 * Version: 2.5.4 (27/01/2026)
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/useAuthStore';
import { tieuChiChungService, IChoPheyet } from '@/services/tieu-chi-chung.service';
import { isApiError } from '@/lib/axios';

// =============================================================================
// INTERFACES
// =============================================================================

interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading?: boolean;
}

// =============================================================================
// SUB COMPONENTS
// =============================================================================

function ConfirmModal({ isOpen, title, message, onConfirm, onCancel, isLoading }: ConfirmModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex-shrink-0 w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">
            <svg className="w-6 h-6 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        <p className="text-gray-600 mb-6">{message}</p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            Hủy
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            {isLoading && (
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            )}
            Xác nhận phê duyệt
          </button>
        </div>
      </div>
    </div>
  );
}

function SuccessModal({ isOpen, message, onClose }: { isOpen: boolean; message: string; onClose: () => void }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4 text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Thành công!</h3>
        <p className="text-gray-600 mb-4">{message}</p>
        <button
          onClick={onClose}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Đóng
        </button>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function PheDuyetListPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();

  const [items, setItems] = useState<IChoPheyet[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Selection
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  
  // Modals
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmAction, setConfirmAction] = useState<'single' | 'bulk'>('single');
  const [singleApproveId, setSingleApproveId] = useState<string | null>(null);
  const [isApproving, setIsApproving] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  // Check auth & role
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    // TODO: Check if user is lanh_dao
  }, [isAuthenticated, router]);

  // Load data
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('[PheDuyetList] Loading data...');
      const result = await tieuChiChungService.getChoPheyet(page, pageSize);
      console.log('[PheDuyetList] Result:', result);
      setItems(result.items);
      setTotal(result.total);
    } catch (err) {
      console.error('[PheDuyetList] Error:', err);
      setError(isApiError(err) ? err.message : 'Có lỗi xảy ra khi tải dữ liệu');
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Selection handlers
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(new Set(items.map((item: IChoPheyet) => item.danh_gia_thang_id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  const handleSelectItem = (id: string, checked: boolean) => {
    const newSelected = new Set(selectedIds);
    if (checked) {
      newSelected.add(id);
    } else {
      newSelected.delete(id);
    }
    setSelectedIds(newSelected);
  };

  const isAllSelected = items.length > 0 && selectedIds.size === items.length;

  // Check if item can be auto-approved (all criteria match default)
  const canAutoApprove = (item: IChoPheyet): boolean => {
    // For now, always allow - detailed check done in chi tiết
    return true;
  };

  // Phê duyệt nhanh single
  const handleQuickApproveSingle = (id: string) => {
    setSingleApproveId(id);
    setConfirmAction('single');
    setShowConfirmModal(true);
  };

  // Phê duyệt hàng loạt
  const handleBulkApprove = () => {
    if (selectedIds.size === 0) {
      alert('Vui lòng chọn ít nhất 1 đơn!');
      return;
    }
    setConfirmAction('bulk');
    setShowConfirmModal(true);
  };

  // Execute approval
  const executeApproval = async () => {
    setIsApproving(true);
    
    try {
      if (confirmAction === 'single' && singleApproveId) {
        // Phê duyệt đơn lẻ - không điều chỉnh
        await tieuChiChungService.pheDuyet(singleApproveId, [], 'Phê duyệt nhanh');
        setSuccessMessage('Đã phê duyệt thành công!');
      } else if (confirmAction === 'bulk') {
        // Phê duyệt hàng loạt
        const ids = Array.from(selectedIds);
        const result = await tieuChiChungService.pheDuyetHangLoat(ids, 'Phê duyệt nhanh hàng loạt');
        setSuccessMessage(`Đã phê duyệt ${result.tong_phe_duyet} đơn thành công!`);
        setSelectedIds(new Set());
      }
      
      setShowConfirmModal(false);
      setShowSuccessModal(true);
      loadData(); // Reload data
    } catch (err) {
      console.error('[PheDuyetList] Approval error:', err);
      alert(isApiError(err) ? 'Lỗi: ' + err.message : 'Có lỗi xảy ra');
    } finally {
      setIsApproving(false);
      setSingleApproveId(null);
    }
  };

  // Navigate to detail
  const handleViewDetail = (id: string) => {
    router.push(`/danh-gia/phe-duyet/${id}`);
  };

  // Format date
  const formatDate = (dateStr: string | null | undefined): string => {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toLocaleDateString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return '—';
    }
  };

  // Get score badge class
  const getScoreBadgeClass = (score: number): string => {
    if (score >= 25) return 'bg-green-100 text-green-700';
    if (score >= 20) return 'bg-yellow-100 text-yellow-700';
    return 'bg-red-100 text-red-700';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Đang tải danh sách...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-6 px-4">
      {/* Header với nút Quay lại */}
      <div className="mb-6">
        <button
          onClick={() => router.push('/dashboard')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4 group"
        >
          <svg className="w-5 h-5 group-hover:-translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>Quay lại Dashboard</span>
        </button>
        
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Phê duyệt Tiêu chí chung</h1>
            <p className="text-gray-600">Danh sách đơn chờ phê duyệt từ công chức</p>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
          <div className="text-sm text-gray-500">Tổng đơn chờ duyệt</div>
          <div className="text-2xl font-bold text-blue-600">{total}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-amber-500">
          <div className="text-sm text-gray-500">Đã chọn</div>
          <div className="text-2xl font-bold text-amber-600">{selectedIds.size}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
          <div className="text-sm text-gray-500">Trang hiện tại</div>
          <div className="text-2xl font-bold text-green-600">{page} / {Math.ceil(total / pageSize) || 1}</div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-red-800">{error}</span>
            <button onClick={loadData} className="ml-auto text-red-600 hover:text-red-800 underline text-sm">
              Thử lại
            </button>
          </div>
        </div>
      )}

      {/* Toolbar */}
      {items.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isAllSelected}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded"
                />
                <span className="text-sm text-gray-700">Chọn tất cả trang này</span>
              </label>
              
              {selectedIds.size > 0 && (
                <span className="text-sm text-gray-500">
                  Đã chọn <strong>{selectedIds.size}</strong> đơn
                </span>
              )}
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={loadData}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Làm mới
              </button>

              <button
                onClick={handleBulkApprove}
                disabled={selectedIds.size === 0}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Phê duyệt nhanh ({selectedIds.size})
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {items.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">Không có đơn chờ duyệt</h3>
            <p className="text-gray-500">Hiện tại chưa có công chức nào gửi đơn tự đánh giá.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left">
                    <input
                      type="checkbox"
                      checked={isAllSelected}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded"
                    />
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Công chức
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Đơn vị
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Kỳ đánh giá
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Điểm tự chấm
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ngày gửi
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Thao tác
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {items.map((item: IChoPheyet) => {
                  const isSelected = selectedIds.has(item.danh_gia_thang_id);
                  const canQuickApprove = canAutoApprove(item);
                  
                  return (
                    <tr
                      key={item.danh_gia_thang_id}
                      className={`hover:bg-gray-50 ${isSelected ? 'bg-blue-50' : ''}`}
                    >
                      <td className="px-4 py-4">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={(e) => handleSelectItem(item.danh_gia_thang_id, e.target.checked)}
                          className="w-4 h-4 text-blue-600 rounded"
                        />
                      </td>
                      <td className="px-4 py-4">
                        <div className="font-medium text-gray-900">{item.ho_ten}</div>
                        <div className="text-sm text-gray-500">{item.ma_cc}</div>
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-600">
                        {item.don_vi_ten || '—'}
                      </td>
                      <td className="px-4 py-4 text-center">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          T{item.thang}/{item.nam}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-center">
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-bold ${getScoreBadgeClass(item.diem_tu_cham)}`}>
                          {item.diem_tu_cham.toFixed(1)}/30
                        </span>
                      </td>
                      <td className="px-4 py-4 text-center text-sm text-gray-500">
                        {formatDate(item.ngay_gui)}
                      </td>
                      <td className="px-4 py-4 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => handleQuickApproveSingle(item.danh_gia_thang_id)}
                            disabled={!canQuickApprove}
                            className="px-3 py-1.5 bg-green-600 text-white text-xs rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                            title="Phê duyệt nhanh (đồng ý 100%)"
                          >
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            Duyệt nhanh
                          </button>
                          <button
                            onClick={() => handleViewDetail(item.danh_gia_thang_id)}
                            className="px-3 py-1.5 border border-gray-300 text-gray-700 text-xs rounded-md hover:bg-gray-50 flex items-center gap-1"
                            title="Xem chi tiết để điều chỉnh"
                          >
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                            Chi tiết
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {total > pageSize && (
          <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Hiển thị {(page - 1) * pageSize + 1} - {Math.min(page * pageSize, total)} / {total} đơn
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50"
              >
                Trước
              </button>
              <span className="px-3 py-1 text-sm">
                Trang {page} / {Math.ceil(total / pageSize)}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(Math.ceil(total / pageSize), p + 1))}
                disabled={page >= Math.ceil(total / pageSize)}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50"
              >
                Sau
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Confirm Modal */}
      <ConfirmModal
        isOpen={showConfirmModal}
        title={confirmAction === 'bulk' ? 'Phê duyệt hàng loạt' : 'Phê duyệt nhanh'}
        message={
          confirmAction === 'bulk'
            ? `Bạn có chắc chắn muốn phê duyệt ${selectedIds.size} đơn đã chọn? Hệ thống sẽ chấp nhận toàn bộ kết quả tự chấm của công chức.`
            : 'Bạn có chắc chắn muốn phê duyệt đơn này? Hệ thống sẽ chấp nhận toàn bộ kết quả tự chấm của công chức.'
        }
        onConfirm={executeApproval}
        onCancel={() => {
          setShowConfirmModal(false);
          setSingleApproveId(null);
        }}
        isLoading={isApproving}
      />

      {/* Success Modal */}
      <SuccessModal
        isOpen={showSuccessModal}
        message={successMessage}
        onClose={() => setShowSuccessModal(false)}
      />
    </div>
  );
}