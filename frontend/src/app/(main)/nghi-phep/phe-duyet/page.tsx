/**
 * src/app/(main)/nghi-phep/phe-duyet/page.tsx
 * =============================================
 * Trang Phê duyệt Nghỉ phép - Leader View.
 *
 * Features v2.6:
 * - Hiển thị đơn chờ duyệt cấp 1 và cấp 2
 * - Badge phân biệt cấp phê duyệt
 * - Progress bar hiển thị tiến trình 2 cấp
 * - Phê duyệt nhanh / Xem chi tiết
 *
 * Quyền: Chỉ Lãnh đạo (is_lanh_dao === true)
 *
 * Version: 2.6 (29/01/2026) - Hỗ trợ phê duyệt 2 cấp
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { format, parseISO } from 'date-fns';

import { useAuthStore } from '@/stores/useAuthStore';
import { leaveService } from '@/services/leave.service';
import { isApiError } from '@/lib/axios';
import {
  INghiPhepResponse,
  TrangThaiNghi,
  getLoaiNghiLabel,
  getLoaiNghiBadgeClass,
  getTrangThaiNghiLabel,
  getTrangThaiNghiBadgeClass,
  getApprovalProgress,
} from '@/types/leave';

// =============================================================================
// SUB COMPONENTS
// =============================================================================

/**
 * Badge hiển thị cấp phê duyệt.
 */
function CapPheDuyetBadge({ trangThai }: { trangThai: TrangThaiNghi }) {
  if (trangThai === TrangThaiNghi.CHO_PHE_DUYET) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
        Cấp 1
      </span>
    );
  }
  if (trangThai === TrangThaiNghi.CHO_CAP2) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
        Cấp 2
      </span>
    );
  }
  return null;
}

/**
 * Progress bar hiển thị tiến trình phê duyệt.
 */
function ApprovalProgressBar({ nghiPhep }: { nghiPhep: INghiPhepResponse }) {
  const progress = getApprovalProgress(nghiPhep);
  const quyTrinh = nghiPhep.quy_trinh;

  if (quyTrinh === 'TU_PHE_DUYET' || quyTrinh === '1_CAP') {
    return null; // Không hiển thị cho quy trình 1 cấp
  }

  return (
    <div className="mt-2">
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <span className={progress >= 0 ? 'text-green-600 font-medium' : ''}>
          Gửi
        </span>
        <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-amber-400 to-green-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className={progress >= 50 ? 'text-amber-600 font-medium' : ''}>
          Cấp 1
        </span>
        <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-amber-400 to-green-500 transition-all duration-300"
            style={{ width: progress >= 50 ? `${(progress - 50) * 2}%` : '0%' }}
          />
        </div>
        <span className={progress >= 100 ? 'text-green-600 font-medium' : ''}>
          Cấp 2
        </span>
      </div>
    </div>
  );
}

// =============================================================================
// COMPONENT
// =============================================================================

export default function PheDuyetNghiPhepPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();

  // Data state
  const [pendingList, setPendingList] = useState<INghiPhepResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Thống kê theo cấp
  const [thongKe, setThongKe] = useState({ cho_cap1: 0, cho_cap2: 0 });

  // Pagination state
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [totalItems, setTotalItems] = useState(0);

  // Filter state
  const [filterCap, setFilterCap] = useState<'all' | 'cap1' | 'cap2'>('all');

  // Modal Phê duyệt
  const [approveModal, setApproveModal] = useState<INghiPhepResponse | null>(null);
  const [approveGhiChu, setApproveGhiChu] = useState('');

  // Modal Từ chối
  const [rejectModal, setRejectModal] = useState<INghiPhepResponse | null>(null);
  const [rejectLyDo, setRejectLyDo] = useState('');

  // Action state
  const [isProcessing, setIsProcessing] = useState(false);

  // ===========================================================================
  // AUTH CHECK
  // ===========================================================================
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    if (user && !user.is_lanh_dao) {
      alert('⚠️ Bạn không có quyền truy cập trang này.\nChỉ Lãnh đạo mới được phép phê duyệt.');
      router.push('/nghi-phep');
    }
  }, [user, isAuthenticated, router]);

  // ===========================================================================
  // LOAD DATA
  // ===========================================================================
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await leaveService.getPendingLeaves({
        page,
        page_size: 20,
      });

      setPendingList(result.data);
      setTotalPages(result.pagination.total_pages);
      setTotalItems(result.pagination.total_items);
      setThongKe(result.thongKe);
    } catch (err) {
      if (isApiError(err)) {
        setError(err.message);
      } else {
        setError('Có lỗi xảy ra khi tải dữ liệu');
      }
    } finally {
      setIsLoading(false);
    }
  }, [page]);

  useEffect(() => {
    if (user?.is_lanh_dao) {
      loadData();
    }
  }, [loadData, user?.is_lanh_dao]);

  // ===========================================================================
  // FILTER
  // ===========================================================================
  const filteredList = pendingList.filter((item) => {
    if (filterCap === 'cap1') return item.trang_thai === TrangThaiNghi.CHO_PHE_DUYET;
    if (filterCap === 'cap2') return item.trang_thai === TrangThaiNghi.CHO_CAP2;
    return true;
  });

  // ===========================================================================
  // APPROVE HANDLER
  // ===========================================================================
  const handleApprove = async () => {
    if (!approveModal) return;

    setIsProcessing(true);
    try {
      await leaveService.approve(approveModal.id, {
        ghi_chu: approveGhiChu || undefined,
      });

      const capText = approveModal.trang_thai === TrangThaiNghi.CHO_CAP2 ? 'cấp 2' : 'cấp 1';
      alert(`✅ Đã phê duyệt ${capText} thành công!`);
      setApproveModal(null);
      setApproveGhiChu('');
      loadData();
    } catch (err) {
      if (isApiError(err)) {
        alert(`❌ Lỗi: ${err.message}`);
      } else {
        alert('❌ Có lỗi xảy ra khi phê duyệt');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  // ===========================================================================
  // REJECT HANDLER
  // ===========================================================================
  const handleReject = async () => {
    if (!rejectModal) return;

    if (!rejectLyDo.trim()) {
      alert('⚠️ Vui lòng nhập lý do từ chối.');
      return;
    }

    setIsProcessing(true);
    try {
      await leaveService.reject(rejectModal.id, {
        ly_do: rejectLyDo.trim(),
      });

      alert('✅ Đã từ chối đơn nghỉ!');
      setRejectModal(null);
      setRejectLyDo('');
      loadData();
    } catch (err) {
      if (isApiError(err)) {
        alert(`❌ Lỗi: ${err.message}`);
      } else {
        alert('❌ Có lỗi xảy ra khi từ chối');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  // ===========================================================================
  // RENDER
  // ===========================================================================

  // Guard: Chỉ Lãnh đạo mới render
  if (!user?.is_lanh_dao) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <button
                onClick={() => router.push('/nghi-phep')}
                className="text-gray-500 hover:text-gray-700"
                title="Quay lại"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </button>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">Phê duyệt Nghỉ phép</h1>
                <p className="text-xs text-gray-500">Các đơn nghỉ chờ bạn phê duyệt</p>
              </div>
            </div>

            {/* Stats Badges */}
            <div className="flex items-center gap-3">
              <div 
                className={`px-4 py-2 rounded-lg flex items-center gap-2 cursor-pointer transition-all ${
                  filterCap === 'all' ? 'bg-gray-200 ring-2 ring-gray-400' : 'bg-gray-100 hover:bg-gray-200'
                }`}
                onClick={() => setFilterCap('all')}
              >
                <span className="text-sm font-medium text-gray-700">Tất cả</span>
                <span className="px-2 py-0.5 bg-white rounded-full text-sm font-bold text-gray-900">
                  {totalItems}
                </span>
              </div>
              <div 
                className={`px-4 py-2 rounded-lg flex items-center gap-2 cursor-pointer transition-all ${
                  filterCap === 'cap1' ? 'bg-amber-200 ring-2 ring-amber-400' : 'bg-amber-100 hover:bg-amber-200'
                }`}
                onClick={() => setFilterCap('cap1')}
              >
                <span className="text-sm font-medium text-amber-700">Cấp 1</span>
                <span className="px-2 py-0.5 bg-white rounded-full text-sm font-bold text-amber-900">
                  {thongKe.cho_cap1}
                </span>
              </div>
              <div 
                className={`px-4 py-2 rounded-lg flex items-center gap-2 cursor-pointer transition-all ${
                  filterCap === 'cap2' ? 'bg-indigo-200 ring-2 ring-indigo-400' : 'bg-indigo-100 hover:bg-indigo-200'
                }`}
                onClick={() => setFilterCap('cap2')}
              >
                <span className="text-sm font-medium text-indigo-700">Cấp 2</span>
                <span className="px-2 py-0.5 bg-white rounded-full text-sm font-bold text-indigo-900">
                  {thongKe.cho_cap2}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Error */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="flex justify-center items-center py-20">
            <svg className="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && filteredList.length === 0 && (
          <div className="text-center py-20 bg-white rounded-lg shadow-sm">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="mt-2 text-lg font-medium text-gray-900">Không có đơn chờ duyệt</h3>
            <p className="mt-1 text-sm text-gray-500">
              {filterCap === 'cap1' && 'Không có đơn nào chờ duyệt cấp 1.'}
              {filterCap === 'cap2' && 'Không có đơn nào chờ duyệt cấp 2.'}
              {filterCap === 'all' && 'Hiện tại chưa có đơn nghỉ nào cần phê duyệt.'}
            </p>
          </div>
        )}

        {/* List */}
        {!isLoading && filteredList.length > 0 && (
          <div className="space-y-4">
            {filteredList.map((item) => (
              <div
                key={item.id}
                className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
              >
                <div className="p-5">
                  <div className="flex items-start justify-between">
                    {/* Left: Info */}
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-base font-semibold text-gray-900">
                          {item.cong_chuc?.ho_ten || 'N/A'}
                        </h3>
                        <CapPheDuyetBadge trangThai={item.trang_thai} />
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLoaiNghiBadgeClass(item.loai_nghi)}`}>
                          {getLoaiNghiLabel(item.loai_nghi)}
                        </span>
                      </div>

                      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                        <div className="flex items-center gap-1">
                          <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          <span>
                            {format(parseISO(item.tu_ngay), 'dd/MM/yyyy')}
                            {item.tu_ngay !== item.den_ngay && (
                              <> - {format(parseISO(item.den_ngay), 'dd/MM/yyyy')}</>
                            )}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span className="font-medium text-blue-600">{item.so_ngay} ngày</span>
                        </div>
                        {item.ly_do && (
                          <div className="flex items-center gap-1">
                            <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                            </svg>
                            <span className="text-gray-500">{item.ly_do}</span>
                          </div>
                        )}
                      </div>

                      {/* Progress bar cho quy trình 2 cấp */}
                      <ApprovalProgressBar nghiPhep={item} />

                      {/* Thông tin phê duyệt cấp 1 (nếu đang chờ cấp 2) */}
                      {item.trang_thai === TrangThaiNghi.CHO_CAP2 && item.nguoi_phe_duyet_cap1 && (
                        <div className="mt-3 px-3 py-2 bg-amber-50 rounded-lg text-sm">
                          <span className="text-amber-700">
                            ✓ Đã duyệt cấp 1 bởi <strong>{item.nguoi_phe_duyet_cap1.ho_ten}</strong>
                            {item.ngay_phe_duyet_cap1 && (
                              <> vào {format(parseISO(item.ngay_phe_duyet_cap1), 'HH:mm dd/MM/yyyy')}</>
                            )}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Right: Actions */}
                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => setApproveModal(item)}
                        className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 flex items-center gap-1"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Duyệt
                      </button>
                      <button
                        onClick={() => setRejectModal(item)}
                        className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 flex items-center gap-1"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                        Từ chối
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-6 flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Trang {page} / {totalPages} ({totalItems} đơn)
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50"
              >
                Trước
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50"
              >
                Sau
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Modal Phê duyệt */}
      {approveModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="fixed inset-0 bg-black/50" onClick={() => setApproveModal(null)} />
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
              {/* Header */}
              <div className="px-6 py-4 border-b border-gray-200 bg-green-50">
                <h3 className="text-lg font-semibold text-green-800 flex items-center gap-2">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Phê duyệt đơn nghỉ
                  {approveModal.trang_thai === TrangThaiNghi.CHO_CAP2 && (
                    <span className="ml-2 px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded text-sm">Cấp 2</span>
                  )}
                </h3>
              </div>

              {/* Body */}
              <div className="p-6">
                {/* Info Card */}
                <div className="bg-gray-50 rounded-lg p-4 mb-4">
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Người đăng ký:</span>
                      <span className="font-medium text-gray-900">{approveModal.cong_chuc?.ho_ten}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Loại nghỉ:</span>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getLoaiNghiBadgeClass(approveModal.loai_nghi)}`}>
                        {getLoaiNghiLabel(approveModal.loai_nghi)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Thời gian:</span>
                      <span className="text-gray-900">
                        {format(parseISO(approveModal.tu_ngay), 'dd/MM/yyyy')}
                        {approveModal.tu_ngay !== approveModal.den_ngay && (
                          <> - {format(parseISO(approveModal.den_ngay), 'dd/MM/yyyy')}</>
                        )}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Số ngày:</span>
                      <span className="font-bold text-blue-600">{approveModal.so_ngay} ngày</span>
                    </div>
                    {approveModal.ly_do && (
                      <div className="pt-2 border-t border-gray-200">
                        <span className="text-gray-500">Lý do:</span>
                        <p className="text-gray-900 mt-1">{approveModal.ly_do}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Thông tin cấp 1 đã duyệt */}
                {approveModal.trang_thai === TrangThaiNghi.CHO_CAP2 && approveModal.nguoi_phe_duyet_cap1 && (
                  <div className="mb-4 p-3 bg-amber-50 rounded-lg">
                    <p className="text-sm text-amber-700">
                      ✓ Cấp 1 đã duyệt bởi: <strong>{approveModal.nguoi_phe_duyet_cap1.ho_ten}</strong>
                    </p>
                  </div>
                )}

                {/* Ghi chú */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ghi chú <span className="text-gray-400">(không bắt buộc)</span>
                  </label>
                  <textarea
                    value={approveGhiChu}
                    onChange={(e) => setApproveGhiChu(e.target.value)}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    placeholder="Nhập ghi chú nếu có..."
                  />
                </div>
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3 bg-gray-50">
                <button
                  onClick={() => setApproveModal(null)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100"
                  disabled={isProcessing}
                >
                  Hủy
                </button>
                <button
                  onClick={handleApprove}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                  disabled={isProcessing}
                >
                  {isProcessing ? (
                    <>
                      <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Đang xử lý...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Phê duyệt
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Từ chối */}
      {rejectModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="fixed inset-0 bg-black/50" onClick={() => setRejectModal(null)} />
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
              {/* Header */}
              <div className="px-6 py-4 border-b border-gray-200 bg-red-50">
                <h3 className="text-lg font-semibold text-red-800 flex items-center gap-2">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Từ chối đơn nghỉ
                </h3>
              </div>

              {/* Body */}
              <div className="p-6">
                {/* Info Card */}
                <div className="bg-gray-50 rounded-lg p-4 mb-4">
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Người đăng ký:</span>
                      <span className="font-medium text-gray-900">{rejectModal.cong_chuc?.ho_ten}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Loại nghỉ:</span>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getLoaiNghiBadgeClass(rejectModal.loai_nghi)}`}>
                        {getLoaiNghiLabel(rejectModal.loai_nghi)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Thời gian:</span>
                      <span className="text-gray-900">
                        {format(parseISO(rejectModal.tu_ngay), 'dd/MM/yyyy')}
                        {rejectModal.tu_ngay !== rejectModal.den_ngay && (
                          <> - {format(parseISO(rejectModal.den_ngay), 'dd/MM/yyyy')}</>
                        )}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Số ngày:</span>
                      <span className="font-bold text-blue-600">{rejectModal.so_ngay} ngày</span>
                    </div>
                  </div>
                </div>

                {/* Lý do từ chối */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Lý do từ chối <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={rejectLyDo}
                    onChange={(e) => setRejectLyDo(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    placeholder="Nhập lý do từ chối đơn nghỉ..."
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Lý do sẽ được hiển thị cho người đăng ký biết.
                  </p>
                </div>
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3 bg-gray-50">
                <button
                  onClick={() => setRejectModal(null)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100"
                  disabled={isProcessing}
                >
                  Hủy
                </button>
                <button
                  onClick={handleReject}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
                  disabled={isProcessing || !rejectLyDo.trim()}
                >
                  {isProcessing ? (
                    <>
                      <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Đang xử lý...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                      Từ chối
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}