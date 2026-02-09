/**
 * src/app/(main)/nghi-phep/page.tsx
 * ==================================
 * Trang Quản lý Nghỉ phép - Employee View.
 *
 * Features:
 * - Cards thống kê nhanh (Tổng ngày nghỉ, Phép năm còn lại...)
 * - Bảng lịch sử nghỉ phép
 * - Modal đăng ký nghỉ với 2 chế độ:
 *   + Tab 1: Nghỉ thường (DatePicker Range)
 *   + Tab 2: Nghỉ tuần (Calendar multi-select)
 *
 * Tham chiếu: PHASE5A_HANDOVER.md
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  format,
  parseISO,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  isSameDay,
  addMonths,
  subMonths,
  getDay,
  isWeekend,
} from 'date-fns';
import { vi } from 'date-fns/locale';

import { useAuthStore } from '@/stores/useAuthStore';
import { leaveService } from '@/services/leave.service';
import { isApiError } from '@/lib/axios';
import {
  LoaiNghi,
  TrangThaiNghi,
  INghiPhepResponse,
  IThongKeNghiPhepCaNhan,
  INguoiPheDuyetNghi,
  getLoaiNghiLabel,
  getTrangThaiNghiLabel,
  getTrangThaiNghiBadgeClass,
  getLoaiNghiBadgeClass,
  canEditNghiPhep,
} from '@/types/leave';

// =============================================================================
// COMPONENT
// =============================================================================

export default function NghiPhepPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();

  // Data state
  const [leaveList, setLeaveList] = useState<INghiPhepResponse[]>([]);
  const [stats, setStats] = useState<IThongKeNghiPhepCaNhan | null>(null);
  const [nguoiPheDuyetList, setNguoiPheDuyetList] = useState<INguoiPheDuyetNghi[]>([]);
  const [autoApprove, setAutoApprove] = useState(false); // ✅ NEW: CCT tự phê duyệt
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [monthlyStats, setMonthlyStats] = useState({ tong: 0, choPheDuyet: 0, daPheDuyet: 0, tuChoi: 0 });

  // Filter theo trạng thái (click vào stats cards)
  // null = hiển thị tất cả, 'CHO_PHE_DUYET' | 'DA_PHE_DUYET' | 'TU_CHOI_HUY'
  const [activeStatusFilter, setActiveStatusFilter] = useState<string | null>(null);

  // Filter state
  const currentDate = new Date();
  const [selectedThang, setSelectedThang] = useState(currentDate.getMonth() + 1);
  const [selectedNam, setSelectedNam] = useState(currentDate.getFullYear());

  // Pagination không cần thiết - backend trả về toàn bộ danh sách theo tháng

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'normal' | 'bulk'>('normal');

  // Form - Nghỉ thường
  const [formLoaiNghi, setFormLoaiNghi] = useState<LoaiNghi>(LoaiNghi.PHEP_NAM);
  const [formTuNgay, setFormTuNgay] = useState('');
  const [formDenNgay, setFormDenNgay] = useState('');
  const [formSoNgay, setFormSoNgay] = useState(1);
  const [formLyDo, setFormLyDo] = useState('');
  const [formNguoiPheDuyet, setFormNguoiPheDuyet] = useState('');

  // Form - Nghỉ tuần (Bulk)
  const [bulkSelectedDates, setBulkSelectedDates] = useState<Date[]>([]);
  const [bulkCalendarMonth, setBulkCalendarMonth] = useState(new Date());
  const [bulkLyDo, setBulkLyDo] = useState('');
  const [bulkNguoiPheDuyet, setBulkNguoiPheDuyet] = useState('');

  // Action state
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Delete confirm state
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: string; info: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // ===========================================================================
  // AUTH CHECK
  // ===========================================================================
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  // ===========================================================================
  // LOAD DATA
  // ===========================================================================
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // ✅ Gọi getMyLeaves là bắt buộc, thống kê và người phê duyệt là optional
      const leavesResult = await leaveService.getMyLeaves({ thang: selectedThang, nam: selectedNam });
      
      // ✅ FIX: Backend trả về mảng trực tiếp, không có pagination
      const allLeaves = leavesResult.data;
      setLeaveList(allLeaves);
      
      // ✅ Tính thống kê từ leaveList theo tháng hiện tại
      const choPheDuyet = allLeaves.filter(l => l.trang_thai === TrangThaiNghi.CHO_PHE_DUYET).length;
      const daPheDuyet = allLeaves.filter(l => l.trang_thai === TrangThaiNghi.DA_PHE_DUYET).length;
      const tuChoi = allLeaves.filter(l => l.trang_thai === TrangThaiNghi.TU_CHOI || l.trang_thai === TrangThaiNghi.HUY).length;
      setMonthlyStats({ tong: allLeaves.length, choPheDuyet, daPheDuyet, tuChoi });
      
      // ✅ Load thống kê năm và người phê duyệt (không throw nếu fail)
      try {
        const statsResult = await leaveService.getThongKeCaNhan(selectedNam);
        if (statsResult) {
          statsResult.cho_phe_duyet = choPheDuyet;
        }
        setStats(statsResult);
      } catch {
        // Thống kê fail không ảnh hưởng tới danh sách
      }
      
      try {
        const nguoiPDResult = await leaveService.getNguoiPheDuyet();
        setNguoiPheDuyetList(nguoiPDResult.nguoiPheDuyet);
        setAutoApprove(nguoiPDResult.autoApprove);
        if (nguoiPDResult.nguoiPheDuyet.length === 1) {
          setFormNguoiPheDuyet(nguoiPDResult.nguoiPheDuyet[0].id);
          setBulkNguoiPheDuyet(nguoiPDResult.nguoiPheDuyet[0].id);
        }
      } catch {
        // Người phê duyệt fail không ảnh hưởng tới danh sách
      }
    } catch (err) {
      if (isApiError(err)) {
        setError(err.message);
      } else {
        setError('Có lỗi xảy ra khi tải dữ liệu');
      }
    } finally {
      setIsLoading(false);
    }
  }, [selectedThang, selectedNam]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Reset filter khi đổi tháng/năm
  useEffect(() => {
    setActiveStatusFilter(null);
  }, [selectedThang, selectedNam]);

  // Computed: danh sách sau khi filter theo status card
  const filteredLeaveList = activeStatusFilter === null
    ? leaveList
    : leaveList.filter((item) => {
        if (activeStatusFilter === 'CHO_PHE_DUYET') {
          return item.trang_thai === TrangThaiNghi.CHO_PHE_DUYET;
        }
        if (activeStatusFilter === 'DA_PHE_DUYET') {
          return item.trang_thai === TrangThaiNghi.DA_PHE_DUYET;
        }
        if (activeStatusFilter === 'TU_CHOI_HUY') {
          return item.trang_thai === TrangThaiNghi.TU_CHOI || item.trang_thai === TrangThaiNghi.HUY;
        }
        return true;
      });

  // ===========================================================================
  // MODAL HANDLERS
  // ===========================================================================
  const handleOpenModal = () => {
    setIsModalOpen(true);
    setActiveTab('normal');
    resetForm();
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    resetForm();
  };

  const resetForm = () => {
    setFormLoaiNghi(LoaiNghi.PHEP_NAM);
    setFormTuNgay('');
    setFormDenNgay('');
    setFormSoNgay(1);
    setFormLyDo('');
    setFormNguoiPheDuyet(nguoiPheDuyetList.length === 1 ? nguoiPheDuyetList[0].id : '');
    setBulkSelectedDates([]);
    setBulkLyDo('');
    setBulkNguoiPheDuyet(nguoiPheDuyetList.length === 1 ? nguoiPheDuyetList[0].id : '');
  };

  // ===========================================================================
  // SUBMIT - Nghỉ thường
  // ===========================================================================
  const handleSubmitNormal = async () => {
    if (!formTuNgay || !formDenNgay) {
      alert('Vui lòng chọn ngày bắt đầu và kết thúc.');
      return;
    }

    if (formSoNgay <= 0) {
      alert('Số ngày phải lớn hơn 0.');
      return;
    }

    setIsSubmitting(true);
    try {
      await leaveService.create({
        loai_nghi: formLoaiNghi,
        tu_ngay: formTuNgay,
        den_ngay: formDenNgay,
        so_ngay: formSoNgay,
        ly_do: formLyDo || undefined,
        nguoi_phe_duyet_id: formNguoiPheDuyet || undefined,
      });

      alert('✅ Đăng ký nghỉ phép thành công!');
      handleCloseModal();
      loadData();
    } catch (err: any) {
      // ⚠️ FIX v3.1: Xử lý lỗi trùng ngày LEAVE_005
      //
      // LƯU Ý QUAN TRỌNG: Có 2 nơi error code có thể nằm:
      // 1. err.code → Từ Axios interceptor (đã transform)
      // 2. err.originalError.response.data.detail.error.code → Raw từ FastAPI
      //    (FastAPI HTTPException wrap trong "detail" key)
      //
      // Interceptor hiện KHÔNG handle HTTP 400, nên rơi vào block default:
      //   error.response.data?.error?.code → undefined (vì data = { detail: { error: {...} } })
      //   → code = 'UNKNOWN_ERROR', message generic
      //
      // Giải pháp: Check tất cả các path có thể chứa error code
      
      const interceptorCode = err?.code || '';
      const interceptorMsg = err?.message || '';
      
      // Path 1: Interceptor đã parse (cho 400 block default)
      // Path 2: Raw response từ FastAPI (backup)
      const rawResponse = err?.originalError?.response?.data || err?.response?.data;
      const rawError = rawResponse?.detail?.error || rawResponse?.error;
      const rawCode = rawError?.code || '';
      const rawMsg = rawError?.message || '';
      
      const finalCode = interceptorCode || rawCode;
      const finalMsg = rawMsg || interceptorMsg; // Ưu tiên raw message (chi tiết hơn)
      
      if (finalCode === 'LEAVE_005') {
        // ✅ Trùng ngày → Hiện thông báo rõ ràng, thân thiện
        alert(`⚠️ Trùng ngày nghỉ!\n\n${finalMsg}\n\nVui lòng chọn ngày khác hoặc xóa đơn cũ trước.`);
      } else if (finalCode === 'VAL_001' || finalCode === 'VALID_001') {
        alert(`❌ Dữ liệu không hợp lệ: ${finalMsg}`);
      } else if (finalMsg) {
        alert(`❌ Lỗi: ${finalMsg}`);
      } else {
        alert('❌ Có lỗi xảy ra khi đăng ký nghỉ');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // ===========================================================================
  // SUBMIT - Nghỉ tuần (Bulk)
  // ===========================================================================
  const handleToggleBulkDate = (date: Date) => {
    const exists = bulkSelectedDates.some((d) => isSameDay(d, date));
    if (exists) {
      setBulkSelectedDates(bulkSelectedDates.filter((d) => !isSameDay(d, date)));
    } else {
      if (bulkSelectedDates.length >= 31) {
        alert('⚠️ Chỉ được chọn tối đa 31 ngày.');
        return;
      }
      setBulkSelectedDates([...bulkSelectedDates, date]);
    }
  };

  const handleSubmitBulk = async () => {
    if (bulkSelectedDates.length === 0) {
      alert('Vui lòng chọn ít nhất 1 ngày nghỉ tuần.');
      return;
    }

    setIsSubmitting(true);
    try {
      const danh_sach_ngay = bulkSelectedDates
        .sort((a, b) => a.getTime() - b.getTime())
        .map((d) => format(d, 'yyyy-MM-dd'));

      const result = await leaveService.createBulk({
        loai_nghi: LoaiNghi.NGHI_TUAN,
        danh_sach_ngay,
        ly_do: bulkLyDo || undefined,
        nguoi_phe_duyet_id: bulkNguoiPheDuyet || undefined,
      });

      let message = '';
      if (result.tong_don_tao > 0) {
        message = `✅ Đã đăng ký ${result.tong_don_tao} ngày nghỉ tuần thành công!`;
      }
      if (result.ngay_da_ton_tai.length > 0) {
        if (result.tong_don_tao === 0) {
          message = `⚠️ Tất cả ${result.ngay_da_ton_tai.length} ngày đã được đăng ký trước đó, không tạo đơn mới.`;
        } else {
          message += `\n\n⚠️ Các ngày đã tồn tại (bỏ qua): ${result.ngay_da_ton_tai.join(', ')}`;
        }
      }
      if (!message) {
        message = '✅ Đăng ký nghỉ tuần thành công!';
      }

      alert(message);
      handleCloseModal();
      loadData();
    } catch (err: any) {
      // ⚠️ FIX: Check cả interceptor path và raw FastAPI path
      const rawResponse = err?.originalError?.response?.data || err?.response?.data;
      const rawError = rawResponse?.detail?.error || rawResponse?.error;
      const errorCode = err?.code || rawError?.code || '';
      const errorMsg = rawError?.message || err?.message || '';
      
      if (errorCode === 'LEAVE_005') {
        alert(`⚠️ Trùng ngày nghỉ!\n\n${errorMsg}\n\nVui lòng chọn ngày khác hoặc xóa đơn cũ trước.`);
      } else if (errorMsg) {
        alert(`❌ Lỗi: ${errorMsg}`);
      } else {
        alert('❌ Có lỗi xảy ra khi đăng ký nghỉ tuần');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // ===========================================================================
  // DELETE HANDLER
  // ===========================================================================
  const handleDelete = async () => {
    if (!deleteConfirm) return;

    setIsDeleting(true);
    try {
      await leaveService.delete(deleteConfirm.id);
      alert('✅ Đã xóa đơn nghỉ thành công!');
      setDeleteConfirm(null);
      loadData();
    } catch (err) {
      if (isApiError(err)) {
        alert(`❌ Lỗi: ${err.message}`);
      }
    } finally {
      setIsDeleting(false);
    }
  };

  // ===========================================================================
  // CALENDAR HELPERS
  // ===========================================================================
  const calendarDays = eachDayOfInterval({
    start: startOfMonth(bulkCalendarMonth),
    end: endOfMonth(bulkCalendarMonth),
  });

  const firstDayOfMonth = getDay(startOfMonth(bulkCalendarMonth));
  const paddingDays = Array(firstDayOfMonth).fill(null);

  // ===========================================================================
  // RENDER
  // ===========================================================================
  const namOptions = Array.from({ length: 5 }, (_, i) => currentDate.getFullYear() - 2 + i);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <button
                onClick={() => router.push('/dashboard')}
                className="text-gray-500 hover:text-gray-700"
                title="Quay lại Dashboard"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </button>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">Quản lý Nghỉ phép</h1>
                <p className="text-xs text-gray-500">{user?.ho_ten}</p>
              </div>
            </div>

            <button onClick={handleOpenModal} className="btn-primary">
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Đăng ký nghỉ
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Filter Tháng + Năm */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">Kỳ kê khai:</label>
              <select
                value={selectedThang}
                onChange={(e) => {
                  setSelectedThang(parseInt(e.target.value));
                }}
                className="input w-32"
              >
                {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                  <option key={m} value={m}>Tháng {m}</option>
                ))}
              </select>
              <select
                value={selectedNam}
                onChange={(e) => {
                  setSelectedNam(parseInt(e.target.value));
                }}
                className="input w-32"
              >
                {namOptions.map((n) => (
                  <option key={n} value={n}>Năm {n}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Status Cards - click để filter */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <div
            onClick={() => setActiveStatusFilter(activeStatusFilter === null ? null : null)}
            className={`bg-white rounded-lg shadow-sm p-4 cursor-pointer transition-all hover:shadow-md ${
              activeStatusFilter === null
                ? 'border-2 border-blue-400 ring-2 ring-blue-100'
                : 'border border-gray-200 hover:border-blue-300'
            }`}
          >
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-600">{monthlyStats.tong}</p>
              <p className="text-xs text-gray-500 mt-1">Tổng kê khai</p>
            </div>
          </div>
          <div
            onClick={() => setActiveStatusFilter(activeStatusFilter === 'CHO_PHE_DUYET' ? null : 'CHO_PHE_DUYET')}
            className={`bg-white rounded-lg shadow-sm p-4 cursor-pointer transition-all hover:shadow-md ${
              activeStatusFilter === 'CHO_PHE_DUYET'
                ? 'border-2 border-yellow-400 ring-2 ring-yellow-100'
                : 'border border-gray-200 hover:border-yellow-300'
            }`}
          >
            <div className="text-center">
              <p className="text-3xl font-bold text-yellow-600">{monthlyStats.choPheDuyet}</p>
              <p className="text-xs text-gray-500 mt-1">Chờ duyệt</p>
            </div>
          </div>
          <div
            onClick={() => setActiveStatusFilter(activeStatusFilter === 'DA_PHE_DUYET' ? null : 'DA_PHE_DUYET')}
            className={`bg-white rounded-lg shadow-sm p-4 cursor-pointer transition-all hover:shadow-md ${
              activeStatusFilter === 'DA_PHE_DUYET'
                ? 'border-2 border-green-400 ring-2 ring-green-100'
                : 'border border-gray-200 hover:border-green-300'
            }`}
          >
            <div className="text-center">
              <p className="text-3xl font-bold text-green-600">{monthlyStats.daPheDuyet}</p>
              <p className="text-xs text-gray-500 mt-1">Đã duyệt</p>
            </div>
          </div>
          <div
            onClick={() => setActiveStatusFilter(activeStatusFilter === 'TU_CHOI_HUY' ? null : 'TU_CHOI_HUY')}
            className={`bg-white rounded-lg shadow-sm p-4 cursor-pointer transition-all hover:shadow-md ${
              activeStatusFilter === 'TU_CHOI_HUY'
                ? 'border-2 border-red-400 ring-2 ring-red-100'
                : 'border border-gray-200 hover:border-red-300'
            }`}
          >
            <div className="text-center">
              <p className="text-3xl font-bold text-red-600">{monthlyStats.tuChoi}</p>
              <p className="text-xs text-gray-500 mt-1">Từ chối / Hủy</p>
            </div>
          </div>
        </div>

        {/* Leave List Table */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <svg className="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>
        ) : filteredLeaveList.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p className="text-gray-600">
              {activeStatusFilter !== null && leaveList.length > 0
                ? `Không có đơn nghỉ nào ở trạng thái đang lọc`
                : `Chưa có đơn nghỉ nào trong tháng ${selectedThang}/${selectedNam}`
              }
            </p>
            {activeStatusFilter !== null && leaveList.length > 0 ? (
              <button onClick={() => setActiveStatusFilter(null)} className="mt-3 text-blue-600 hover:text-blue-800 font-medium">
                Bỏ lọc, xem tất cả →
              </button>
            ) : (
              <button onClick={handleOpenModal} className="mt-3 text-blue-600 hover:text-blue-800 font-medium">
                Đăng ký nghỉ ngay →
              </button>
            )}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            {/* Table Header */}
            <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-900">
                Danh sách kê khai tháng {selectedThang}/{selectedNam}
                {activeStatusFilter !== null && (
                  <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {activeStatusFilter === 'CHO_PHE_DUYET' && 'Chờ duyệt'}
                    {activeStatusFilter === 'DA_PHE_DUYET' && 'Đã duyệt'}
                    {activeStatusFilter === 'TU_CHOI_HUY' && 'Từ chối / Hủy'}
                    <button
                      onClick={() => setActiveStatusFilter(null)}
                      className="ml-1 text-blue-600 hover:text-blue-800"
                    >✕</button>
                  </span>
                )}
              </h3>
              <span className="text-sm text-gray-500">
                Hiển thị: {filteredLeaveList.length} / {leaveList.length} bản
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>Loại nghỉ</th>
                    <th>Thời gian</th>
                    <th className="text-center">Số ngày</th>
                    <th>Lý do</th>
                    <th>Trạng thái</th>
                    <th>Người duyệt</th>
                    <th className="text-center">Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLeaveList.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLoaiNghiBadgeClass(item.loai_nghi)}`}>
                          {getLoaiNghiLabel(item.loai_nghi)}
                        </span>
                      </td>
                      <td>
                        <div className="text-sm">
                          {format(parseISO(item.tu_ngay), 'dd/MM/yyyy')}
                          {item.tu_ngay !== item.den_ngay && (
                            <> - {format(parseISO(item.den_ngay), 'dd/MM/yyyy')}</>
                          )}
                        </div>
                      </td>
                      <td className="text-center font-medium">{item.so_ngay}</td>
                      <td>
                        <div className="max-w-[200px] truncate text-sm text-gray-600" title={item.ly_do || ''}>
                          {item.ly_do || '-'}
                        </div>
                      </td>
                      <td>
                        <span className={getTrangThaiNghiBadgeClass(item.trang_thai)}>
                          {getTrangThaiNghiLabel(item.trang_thai)}
                        </span>
                        {item.ly_do_tu_choi && (
                          <div className="text-xs text-red-500 mt-1 max-w-[150px] truncate" title={item.ly_do_tu_choi}>
                            Lý do: {item.ly_do_tu_choi}
                          </div>
                        )}
                      </td>
                      <td>
                        <div className="text-sm">{item.nguoi_phe_duyet?.ho_ten || '-'}</div>
                      </td>
                      <td className="text-center">
                        {canEditNghiPhep(item.trang_thai) && (
                          <button
                            onClick={() =>
                              setDeleteConfirm({
                                id: item.id,
                                info: `${getLoaiNghiLabel(item.loai_nghi)} - ${format(parseISO(item.tu_ngay), 'dd/MM/yyyy')}`,
                              })
                            }
                            className="text-red-600 hover:text-red-800"
                            title="Xóa đơn"
                          >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* Modal Đăng ký Nghỉ */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="fixed inset-0 bg-black/50" onClick={handleCloseModal} />
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              {/* Modal Header */}
              <div className="sticky top-0 bg-white px-6 py-4 border-b border-gray-200 z-10">
                <h3 className="text-lg font-semibold text-gray-900">📅 Đăng ký Nghỉ phép</h3>
                <button
                  onClick={handleCloseModal}
                  className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Tabs */}
              <div className="border-b border-gray-200">
                <div className="flex">
                  <button
                    onClick={() => setActiveTab('normal')}
                    className={`flex-1 px-6 py-3 text-sm font-medium text-center border-b-2 transition-colors ${
                      activeTab === 'normal'
                        ? 'border-blue-500 text-blue-600 bg-blue-50'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    📋 Nghỉ thường
                    <span className="block text-xs font-normal mt-0.5">Phép năm, ốm, việc riêng...</span>
                  </button>
                  <button
                    onClick={() => setActiveTab('bulk')}
                    className={`flex-1 px-6 py-3 text-sm font-medium text-center border-b-2 transition-colors ${
                      activeTab === 'bulk'
                        ? 'border-blue-500 text-blue-600 bg-blue-50'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    🗓️ Nghỉ tuần
                    <span className="block text-xs font-normal mt-0.5">Chọn nhiều ngày trên lịch</span>
                  </button>
                </div>
              </div>

              {/* Modal Body */}
              <div className="p-6">
                {activeTab === 'normal' ? (
                  /* ============ TAB: NGHỈ THƯỜNG ============ */
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Loại nghỉ <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={formLoaiNghi}
                        onChange={(e) => setFormLoaiNghi(e.target.value as LoaiNghi)}
                        className="input"
                      >
                        {Object.values(LoaiNghi)
                          .filter((l) => l !== LoaiNghi.NGHI_TUAN) // Nghỉ tuần dùng tab Bulk
                          .map((loai) => (
                            <option key={loai} value={loai}>
                              {getLoaiNghiLabel(loai)}
                            </option>
                          ))}
                      </select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Từ ngày <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="date"
                          value={formTuNgay}
                          onChange={(e) => {
                            setFormTuNgay(e.target.value);
                            if (!formDenNgay || e.target.value > formDenNgay) {
                              setFormDenNgay(e.target.value);
                            }
                          }}
                          className="input"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Đến ngày <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="date"
                          value={formDenNgay}
                          min={formTuNgay}
                          onChange={(e) => setFormDenNgay(e.target.value)}
                          className="input"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Số ngày <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="number"
                        min="0.5"
                        step="0.5"
                        value={formSoNgay}
                        onChange={(e) => setFormSoNgay(parseFloat(e.target.value) || 1)}
                        className="input w-32"
                      />
                      <p className="text-xs text-gray-500 mt-1">💡 Nhập 0.5 nếu nghỉ nửa ngày (buổi sáng/chiều)</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Lý do</label>
                      <textarea
                        value={formLyDo}
                        onChange={(e) => setFormLyDo(e.target.value)}
                        rows={2}
                        className="input"
                        placeholder="Nhập lý do nghỉ..."
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Người phê duyệt</label>
                      {autoApprove ? (
                        // ✅ CCT tự phê duyệt - Hiển thị thông báo
                        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                          <p className="text-sm text-green-700">
                            ✅ Bạn là Chi cục trưởng - Đơn sẽ được <strong>tự động phê duyệt</strong>.
                          </p>
                        </div>
                      ) : nguoiPheDuyetList.length === 1 ? (
                        // ✅ FIX v3.0: Chỉ có 1 người (Đội trưởng) → Hiện tên luôn
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                          <div className="flex items-center gap-2">
                            <svg className="w-5 h-5 text-blue-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                            <p className="text-sm text-blue-700">
                              👤 Người phê duyệt: <strong>{nguoiPheDuyetList[0].ho_ten}</strong>
                              {nguoiPheDuyetList[0].chuc_vu && (
                                <span className="text-blue-500"> ({nguoiPheDuyetList[0].chuc_vu})</span>
                              )}
                            </p>
                          </div>
                        </div>
                      ) : nguoiPheDuyetList.length > 1 ? (
                        // Nhiều người → dropdown chọn
                        <select
                          value={formNguoiPheDuyet}
                          onChange={(e) => setFormNguoiPheDuyet(e.target.value)}
                          className="input"
                        >
                          <option value="">-- Chọn người phê duyệt --</option>
                          {nguoiPheDuyetList.map((npd) => (
                            <option key={npd.id} value={npd.id}>
                              {npd.ho_ten} {npd.chuc_vu ? `(${npd.chuc_vu})` : ''}
                            </option>
                          ))}
                        </select>
                      ) : (
                        // Không có ai → fallback
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                          <p className="text-sm text-yellow-700">
                            ⚠️ Hệ thống sẽ tự động gán người phê duyệt phù hợp.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  /* ============ TAB: NGHỈ TUẦN (BULK) ============ */
                  <div className="space-y-4">
                    {/* Hướng dẫn */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="font-medium text-blue-800 mb-1">💡 Hướng dẫn đăng ký Nghỉ tuần</h4>
                      <p className="text-sm text-blue-700">
                        Click vào các ngày trên lịch để chọn nghỉ. Bạn có thể chọn nhiều ngày cùng lúc (tối đa 31 ngày).
                        Phù hợp cho công chức làm việc theo ca/kíp.
                      </p>
                    </div>

                    <div className="flex flex-col lg:flex-row gap-6">
                      {/* Calendar */}
                      <div className="flex-1">
                        {/* Calendar Navigation */}
                        <div className="flex items-center justify-between mb-4">
                          <button
                            onClick={() => setBulkCalendarMonth(subMonths(bulkCalendarMonth, 1))}
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                          >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                            </svg>
                          </button>
                          <span className="font-semibold text-gray-900">
                            {format(bulkCalendarMonth, 'MMMM yyyy', { locale: vi })}
                          </span>
                          <button
                            onClick={() => setBulkCalendarMonth(addMonths(bulkCalendarMonth, 1))}
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                          >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </button>
                        </div>

                        {/* Day Headers */}
                        <div className="grid grid-cols-7 gap-1 mb-2">
                          {['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'].map((day, idx) => (
                            <div
                              key={day}
                              className={`text-center text-xs font-medium py-2 ${
                                idx === 0 || idx === 6 ? 'text-red-500' : 'text-gray-500'
                              }`}
                            >
                              {day}
                            </div>
                          ))}
                        </div>

                        {/* Calendar Grid */}
                        <div className="grid grid-cols-7 gap-1">
                          {paddingDays.map((_, idx) => (
                            <div key={`pad-${idx}`} className="h-10" />
                          ))}

                          {calendarDays.map((day) => {
                            const isSelected = bulkSelectedDates.some((d) => isSameDay(d, day));
                            const isToday = isSameDay(day, new Date());
                            const isWeekendDay = isWeekend(day);

                            return (
                              <button
                                key={day.toISOString()}
                                onClick={() => handleToggleBulkDate(day)}
                                className={`h-10 rounded-lg text-sm font-medium transition-all ${
                                  isSelected
                                    ? 'bg-blue-600 text-white shadow-md'
                                    : isToday
                                    ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                                    : isWeekendDay
                                    ? 'text-red-500 hover:bg-red-50'
                                    : 'text-gray-700 hover:bg-gray-100'
                                }`}
                              >
                                {format(day, 'd')}
                              </button>
                            );
                          })}
                        </div>
                      </div>

                      {/* Selected Dates Panel */}
                      <div className="w-full lg:w-56">
                        <div className="bg-gray-50 rounded-lg p-4">
                          <h4 className="font-medium text-gray-900 mb-3">
                            Đã chọn ({bulkSelectedDates.length} ngày)
                          </h4>
                          <div className="max-h-48 overflow-y-auto space-y-1">
                            {bulkSelectedDates.length === 0 ? (
                              <p className="text-sm text-gray-400 italic">Chưa chọn ngày nào</p>
                            ) : (
                              bulkSelectedDates
                                .sort((a, b) => a.getTime() - b.getTime())
                                .map((date) => (
                                  <div
                                    key={date.toISOString()}
                                    className="flex items-center justify-between bg-white rounded-lg px-3 py-2 shadow-sm"
                                  >
                                    <span className="text-sm font-medium">
                                      {format(date, 'dd/MM/yyyy')}
                                    </span>
                                    <button
                                      onClick={() => handleToggleBulkDate(date)}
                                      className="text-red-500 hover:text-red-700 p-1"
                                    >
                                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                      </svg>
                                    </button>
                                  </div>
                                ))
                            )}
                          </div>

                          {bulkSelectedDates.length > 0 && (
                            <button
                              onClick={() => setBulkSelectedDates([])}
                              className="mt-3 text-sm text-red-600 hover:text-red-800 font-medium"
                            >
                              Xóa tất cả
                            </button>
                          )}
                        </div>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Lý do</label>
                      <input
                        type="text"
                        value={bulkLyDo}
                        onChange={(e) => setBulkLyDo(e.target.value)}
                        className="input"
                        placeholder="Ví dụ: Nghỉ tuần tháng 1/2026"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Người phê duyệt</label>
                      {autoApprove ? (
                        // ✅ CCT tự phê duyệt
                        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                          <p className="text-sm text-green-700">
                            ✅ Bạn là Chi cục trưởng - Đơn sẽ được <strong>tự động phê duyệt</strong>.
                          </p>
                        </div>
                      ) : nguoiPheDuyetList.length === 1 ? (
                        // ✅ FIX v3.0: Chỉ có 1 người (Đội trưởng) → Hiện tên luôn
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                          <div className="flex items-center gap-2">
                            <svg className="w-5 h-5 text-blue-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                            <p className="text-sm text-blue-700">
                              👤 Người phê duyệt: <strong>{nguoiPheDuyetList[0].ho_ten}</strong>
                              {nguoiPheDuyetList[0].chuc_vu && (
                                <span className="text-blue-500"> ({nguoiPheDuyetList[0].chuc_vu})</span>
                              )}
                            </p>
                          </div>
                        </div>
                      ) : nguoiPheDuyetList.length > 1 ? (
                        // Nhiều người → dropdown chọn
                        <select
                          value={bulkNguoiPheDuyet}
                          onChange={(e) => setBulkNguoiPheDuyet(e.target.value)}
                          className="input"
                        >
                          <option value="">-- Chọn người phê duyệt --</option>
                          {nguoiPheDuyetList.map((npd) => (
                            <option key={npd.id} value={npd.id}>
                              {npd.ho_ten} {npd.chuc_vu ? `(${npd.chuc_vu})` : ''}
                            </option>
                          ))}
                        </select>
                      ) : (
                        // Không có ai → fallback
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                          <p className="text-sm text-yellow-700">
                            ⚠️ Hệ thống sẽ tự động gán người phê duyệt phù hợp.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="sticky bottom-0 bg-white px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
                <button onClick={handleCloseModal} className="btn-outline" disabled={isSubmitting}>
                  Hủy
                </button>
                <button
                  onClick={activeTab === 'normal' ? handleSubmitNormal : handleSubmitBulk}
                  className="btn-primary"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Đang xử lý...
                    </>
                  ) : activeTab === 'normal' ? (
                    'Đăng ký nghỉ'
                  ) : (
                    `Đăng ký ${bulkSelectedDates.length} ngày nghỉ tuần`
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Confirm Delete Dialog */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="fixed inset-0 bg-black/50" onClick={() => setDeleteConfirm(null)} />
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="relative bg-white rounded-lg shadow-xl max-w-sm w-full p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">⚠️ Xác nhận xóa</h3>
              <p className="text-gray-600 mb-4">
                Bạn có chắc muốn xóa đơn nghỉ <strong className="text-gray-900">{deleteConfirm.info}</strong>?
              </p>
              <div className="flex justify-end gap-3">
                <button onClick={() => setDeleteConfirm(null)} className="btn-outline" disabled={isDeleting}>
                  Hủy
                </button>
                <button onClick={handleDelete} className="btn-danger" disabled={isDeleting}>
                  {isDeleting ? 'Đang xóa...' : 'Xóa'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}