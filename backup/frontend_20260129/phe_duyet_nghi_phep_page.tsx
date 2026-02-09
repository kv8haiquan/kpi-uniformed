/**
 * src/app/(main)/nghi-phep/phe-duyet/page.tsx
 * =============================================
 * Trang Phê duyệt Nghỉ phép - Leader View.
 *
 * Features:
 * - Danh sách đơn nghỉ chờ phê duyệt (CHO_PHE_DUYET)
 * - Nút Duyệt (xanh) / Từ chối (đỏ) cho mỗi đơn
 * - Modal nhập ghi chú (duyệt) / lý do (từ chối)
 *
 * Quyền: Chỉ Lãnh đạo (is_lanh_dao === true)
 *
 * Tham chiếu: PHASE5A_HANDOVER.md
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
  getLoaiNghiLabel,
  getLoaiNghiBadgeClass,
} from '@/types/leave';

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

  // Pagination state
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [totalItems, setTotalItems] = useState(0);

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
  // APPROVE HANDLER
  // ===========================================================================
  const handleApprove = async () => {
    if (!approveModal) return;

    setIsProcessing(true);
    try {
      await leaveService.approve(approveModal.id, {
        ghi_chu: approveGhiChu || undefined,
      });

      alert('✅ Đã phê duyệt đơn nghỉ thành công!');
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

            {/* Stats Badge */}
            <div className="flex items-center gap-3">
              <div className="bg-yellow-100 text-yellow-800 px-4 py-2 rounded-lg flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-bold">{totalItems}</span>
                <span className="text-sm">đơn chờ duyệt</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Loading */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <svg className="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>
        ) : pendingList.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
            <div className="w-20 h-20 mx-auto bg-green-100 rounded-full flex items-center justify-center mb-4">
              <svg className="w-10 h-10 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">Không có đơn chờ duyệt</h3>
            <p className="text-gray-500">Tất cả đơn nghỉ đã được xử lý.</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>Người đăng ký</th>
                    <th>Loại nghỉ</th>
                    <th>Thời gian</th>
                    <th className="text-center">Số ngày</th>
                    <th>Lý do</th>
                    <th>Ngày đăng ký</th>
                    <th className="text-center">Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingList.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td>
                        <div className="font-medium text-gray-900">{item.cong_chuc.ho_ten}</div>
                        <div className="text-sm text-gray-500">
                          {item.cong_chuc.ma_cc}
                          {item.cong_chuc.don_vi_ten && ` • ${item.cong_chuc.don_vi_ten}`}
                        </div>
                      </td>
                      <td>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLoaiNghiBadgeClass(item.loai_nghi)}`}>
                          {getLoaiNghiLabel(item.loai_nghi)}
                        </span>
                      </td>
                      <td>
                        <div className="text-sm">
                          {format(parseISO(item.tu_ngay), 'dd/MM/yyyy')}
                          {item.tu_ngay !== item.den_ngay && (
                            <>
                              <br />
                              <span className="text-gray-400">→</span> {format(parseISO(item.den_ngay), 'dd/MM/yyyy')}
                            </>
                          )}
                        </div>
                      </td>
                      <td className="text-center">
                        <span className="inline-flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-700 rounded-full font-bold">
                          {item.so_ngay}
                        </span>
                      </td>
                      <td>
                        <div className="max-w-[200px] truncate text-sm text-gray-600" title={item.ly_do || ''}>
                          {item.ly_do || <span className="text-gray-400 italic">Không có lý do</span>}
                        </div>
                      </td>
                      <td className="text-sm text-gray-500">
                        {format(parseISO(item.created_at), 'dd/MM/yyyy')}
                        <br />
                        <span className="text-xs text-gray-400">
                          {format(parseISO(item.created_at), 'HH:mm')}
                        </span>
                      </td>
                      <td>
                        <div className="flex items-center justify-center gap-2">
                          {/* Nút Duyệt */}
                          <button
                            onClick={() => {
                              setApproveModal(item);
                              setApproveGhiChu('');
                            }}
                            className="inline-flex items-center px-3 py-1.5 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors shadow-sm"
                            title="Phê duyệt"
                          >
                            <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            Duyệt
                          </button>

                          {/* Nút Từ chối */}
                          <button
                            onClick={() => {
                              setRejectModal(item);
                              setRejectLyDo('');
                            }}
                            className="inline-flex items-center px-3 py-1.5 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors shadow-sm"
                            title="Từ chối"
                          >
                            <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                            Từ chối
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between bg-gray-50">
                <div className="text-sm text-gray-600">
                  Trang <strong>{page}</strong> / <strong>{totalPages}</strong> ({totalItems} đơn)
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="btn-outline text-sm"
                  >
                    ← Trước
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="btn-outline text-sm"
                  >
                    Sau →
                  </button>
                </div>
              </div>
            )}
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
                </h3>
              </div>

              {/* Body */}
              <div className="p-6">
                {/* Info Card */}
                <div className="bg-gray-50 rounded-lg p-4 mb-4">
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Người đăng ký:</span>
                      <span className="font-medium text-gray-900">{approveModal.cong_chuc.ho_ten}</span>
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

                {/* Ghi chú */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ghi chú <span className="text-gray-400">(không bắt buộc)</span>
                  </label>
                  <textarea
                    value={approveGhiChu}
                    onChange={(e) => setApproveGhiChu(e.target.value)}
                    rows={2}
                    className="input"
                    placeholder="Nhập ghi chú nếu có..."
                  />
                </div>
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3 bg-gray-50">
                <button
                  onClick={() => setApproveModal(null)}
                  className="btn-outline"
                  disabled={isProcessing}
                >
                  Hủy
                </button>
                <button
                  onClick={handleApprove}
                  className="btn-success"
                  disabled={isProcessing}
                >
                  {isProcessing ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Đang xử lý...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
                      <span className="font-medium text-gray-900">{rejectModal.cong_chuc.ho_ten}</span>
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
                    className="input"
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
                  className="btn-outline"
                  disabled={isProcessing}
                >
                  Hủy
                </button>
                <button
                  onClick={handleReject}
                  className="btn-danger"
                  disabled={isProcessing || !rejectLyDo.trim()}
                >
                  {isProcessing ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Đang xử lý...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
