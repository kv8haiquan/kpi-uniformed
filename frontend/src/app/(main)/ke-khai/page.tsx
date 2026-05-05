/**
 * src/app/(main)/ke-khai/page.tsx
 * ================================
 * Trang Kê khai KPI - Hỗ trợ cả CC thường và Lãnh đạo.
 *
 * PHIÊN BẢN: 2.7.4 (02/02/2026)
 * 
 * CHANGELOG v2.7.4:
 * - Thêm cột "Lỗi" hiển thị số lỗi CL/TĐ (tự đánh giá + lãnh đạo chốt)
 * - Hiển thị mô tả lỗi (ghi_chu_tu_dg_*, ghi_chu_loi_*) khi hover/expand
 * - Thêm row expandable để xem chi tiết lỗi
 * 
 * CHANGELOG v2.6.0:
 * - FIX: Sử dụng getAllKeKhaiByMonth() để load TẤT CẢ bản kê khai
 * - FIX: Sửa logic gửi duyệt - đếm bản nháp từ keKhaiList đã load đầy đủ
 * - FIX: Hiển thị số lượng chính xác trên button và modal
 * 
 * Logic hiển thị:
 * - CC thường: Form kê khai như cũ (chọn danh mục SP, cấp độ...)
 * - Lãnh đạo: 2 Tabs: "Kê khai công việc" + "Đánh giá d, đ, e"
 *
 * Features:
 * - Xem danh sách kê khai theo tháng/năm (TẤT CẢ - không giới hạn 20 bản)
 * - Thêm mới, Sửa, Xóa kê khai (khi trạng thái NHÁP hoặc TỪ CHỐI)
 * - Gửi kê khai đi phê duyệt (TẤT CẢ bản nháp)
 * - Hiển thị tổng hợp và trạng thái chung
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';

import { useAuthStore, useIsLanhDao, useIsQLDV, useIsHd111 } from '@/stores/useAuthStore';
import LeaderKeKhaiView from '@/components/ke-khai/LeaderKeKhaiView';
import { kpiService } from '@/services/kpi.service';
import { isApiError } from '@/lib/axios';
import {
  IKeKhaiBrief,
  IKeKhaiCongViec,
  IKeKhaiMonthSummary,
  KpiStatus,
  getStatusLabel,
  getStatusBadgeClass,
  canEditKeKhai,
} from '@/types/kpi';
import KpiTargetModal from '@/components/kpi/KpiTargetModal';
import KpiMultiDayModal from '@/components/kpi/KpiMultiDayModal';

// =============================================================================
// COMPONENT
// =============================================================================

export default function KeKhaiPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const isLanhDao = useIsLanhDao();
  const isQldv = useIsQLDV();
  const isHd111 = useIsHd111();

  // State cho filter tháng/năm - DÙNG CHUNG CHO CẢ 2 VIEW
  const currentDate = new Date();
  const [selectedThang, setSelectedThang] = useState(currentDate.getMonth() + 1);
  const [selectedNam, setSelectedNam] = useState(currentDate.getFullYear());

  // ==========================================================================
  // TẤT CẢ HOOKS PHẢI KHAI BÁO Ở ĐÂY - TRƯỚC BẤT KỲ ĐIỀU KIỆN RETURN NÀO
  // ==========================================================================

  // State cho data (CC thường)
  const [keKhaiList, setKeKhaiList] = useState<IKeKhaiBrief[]>([]);
  const [summary, setSummary] = useState<IKeKhaiMonthSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // State cho Modal thêm/sửa kê khai
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingKeKhai, setEditingKeKhai] = useState<IKeKhaiCongViec | null>(null);

  // State cho confirm dialog
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: string; name: string } | null>(null);
  const [submitConfirm, setSubmitConfirm] = useState(false);

  // State cho actions
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // State cho filter theo trạng thái - v2.6.1
  // null = Tất cả, 'NHAP' = Nháp, 'CHO_PHE_DUYET' = Chờ duyệt, 'DA_PHE_DUYET' = Đã duyệt
  const [filterTrangThai, setFilterTrangThai] = useState<string | null>(null);

  // v2.7.4: State cho expandable row - xem chi tiết lỗi
  const [expandedRowId, setExpandedRowId] = useState<string | null>(null);

  // v2.8.0: State cho Modal kê khai nhiều ngày
  const [isMultiDayModalOpen, setIsMultiDayModalOpen] = useState(false);

  // ==========================================================================
  // QLDV REDIRECT — QLDV không có quyền tạo kê khai
  // ==========================================================================
  useEffect(() => {
    if (isQldv) {
      router.replace('/dashboard');
    }
  }, [isQldv, router]);

  // ==========================================================================
  // PHASE 3 (05/05/2026) — LĐ thật + tháng ≥ 4/2026 dùng form V2
  // (HĐ 111 vẫn ở form cũ; LĐ tháng < 4/2026 vẫn ở form cũ)
  // ==========================================================================
  useEffect(() => {
    const isV2Active = selectedNam > 2026 || (selectedNam === 2026 && selectedThang >= 4);
    if (isLanhDao && !isHd111 && isV2Active) {
      router.replace('/ke-khai-v2');
    }
  }, [isLanhDao, isHd111, selectedThang, selectedNam, router]);

  // ==========================================================================
  // V2 READ-ONLY MODE (02/05/2026) — CC V2 chỉ xem dữ liệu V1 cũ để đối chiếu.
  // Lãnh đạo + HĐ 111 dùng LeaderKeKhaiView (V1 hợp lệ) nên không bị ảnh hưởng.
  // ==========================================================================
  const isV1ReadOnly =
    user?.effective_kpi_version === 'V2_PL3' && !isLanhDao && !isHd111;

  // ==========================================================================
  // LOAD DATA - FIX v2.6.0: SỬ DỤNG getAllKeKhaiByMonth()
  // ==========================================================================

  /**
   * Load TẤT CẢ bản kê khai trong tháng.
   * 
   * FIX v2.6.0: Sử dụng getAllKeKhaiByMonth() từ kpiService
   * để tự động loop qua tất cả các trang và merge kết quả.
   */
  const loadData = useCallback(async () => {
    // Chỉ load data cho CC thường (LĐ + HĐ 111 dùng LeaderKeKhaiView riêng)
    if (isLanhDao || isHd111) return;

    setIsLoading(true);
    setError(null);

    try {
      // Load song song: summary và danh sách kê khai
      const [summaryData, allKeKhai] = await Promise.all([
        kpiService.getMonthSummary(selectedThang, selectedNam),
        // FIX: Sử dụng getAllKeKhaiByMonth() để lấy TẤT CẢ bản kê khai
        kpiService.getAllKeKhaiByMonth(selectedThang, selectedNam),
      ]);

      setSummary(summaryData);
      setKeKhaiList(allKeKhai);
    } catch (err) {
      if (isApiError(err)) {
        setError(err.message);
      } else {
        setError('Không thể tải dữ liệu. Vui lòng thử lại.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [selectedThang, selectedNam, isLanhDao, isHd111]);

  // Load data khi tháng/năm thay đổi
  useEffect(() => {
    loadData();
  }, [loadData]);

  // ==========================================================================
  // HANDLERS CHO CC THƯỜNG
  // ==========================================================================

  // Mở modal thêm mới
  const handleOpenCreate = () => {
    setEditingKeKhai(null);
    setIsModalOpen(true);
  };

  // Mở modal sửa
  const handleOpenEdit = async (id: string) => {
    try {
      const detail = await kpiService.getKeKhaiById(id);
      setEditingKeKhai(detail);
      setIsModalOpen(true);
    } catch (err) {
      if (isApiError(err)) {
        alert(err.message);
      }
    }
  };

  // Xử lý xóa
  const handleDelete = async () => {
    if (!deleteConfirm) return;

    setIsDeleting(true);
    try {
      await kpiService.deleteKeKhai(deleteConfirm.id);
      setDeleteConfirm(null);
      loadData(); // Reload data
    } catch (err) {
      if (isApiError(err)) {
        alert(err.message);
      }
    } finally {
      setIsDeleting(false);
    }
  };

  // v2.7.3: Mở modal xác nhận gửi duyệt (đơn giản - không cần chọn người phê duyệt)
  const handleOpenSubmitModal = async () => {
    // Người phê duyệt đã được chọn khi tạo từng kê khai
    setSubmitConfirm(true);
  };

  // ==========================================================================
  // XỬ LÝ GỬI DUYỆT - FIX v2.6.0: GỬI TẤT CẢ BẢN NHÁP
  // ==========================================================================

  /**
   * v2.7.3: Xử lý gửi duyệt TẤT CẢ bản kê khai NHÁP
   * 
   * Lấy nguoi_phe_duyet_id từ mỗi bản kê khai (đã chọn khi tạo)
   * Không cần chọn lại ở modal gửi duyệt
   */
  const handleSubmitKpi = async () => {
    setIsSubmitting(true);
    try {
      // Lọc ra TẤT CẢ các kê khai có trạng thái NHÁP (NHAP)
      const draftList = keKhaiList.filter((item) => item.trang_thai === KpiStatus.DRAFT);

      if (draftList.length === 0) {
        alert('Không có bản kê khai nào ở trạng thái Nháp để gửi duyệt.');
        setSubmitConfirm(false);
        return;
      }

      // v2.7.3: Kiểm tra tất cả draft đều có người phê duyệt
      const draftsWithoutApprover = draftList.filter(
        (item) => !item.nguoi_phe_duyet_id
      );
      if (draftsWithoutApprover.length > 0) {
        alert(
          `Có ${draftsWithoutApprover.length} bản kê khai chưa chọn người phê duyệt.\n` +
          `Vui lòng sửa từng bản và chọn người phê duyệt trước khi gửi duyệt.`
        );
        setSubmitConfirm(false);
        setIsSubmitting(false);
        return;
      }

      // Gửi từng bản với người phê duyệt đã chọn sẵn trong kê khai
      let submittedCount = 0;
      let failedCount = 0;

      for (const draft of draftList) {
        try {
          await kpiService.submitKeKhaiSingle(draft.id, draft.nguoi_phe_duyet_id!);
          submittedCount++;
        } catch (error) {
          console.error(`Failed to submit ke_khai ${draft.id}:`, error);
          failedCount++;
        }
      }

      setSubmitConfirm(false);

      // Hiển thị kết quả chi tiết
      if (failedCount > 0) {
        alert(
          `Kết quả gửi duyệt:\n` +
          `✅ Thành công: ${submittedCount} bản\n` +
          `❌ Thất bại: ${failedCount} bản\n\n` +
          `Vui lòng kiểm tra lại các bản gửi thất bại.`
        );
      } else {
        alert(`✅ Đã gửi thành công ${submittedCount} bản kê khai đi phê duyệt!`);
      }

      loadData(); // Reload data để cập nhật trạng thái
    } catch (err) {
      if (isApiError(err)) {
        alert(`Lỗi gửi duyệt: ${err.message}`);
      } else {
        alert('Có lỗi xảy ra khi gửi duyệt. Vui lòng thử lại.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // ==========================================================================
  // COMPUTED VALUES - FIX v2.6.0
  // ==========================================================================

  // Đếm số bản nháp thực tế từ keKhaiList (đã load đầy đủ)
  const actualDraftCount = keKhaiList.filter((item) => item.trang_thai === KpiStatus.DRAFT).length;

  // Kiểm tra có thể gửi duyệt không - dựa trên số bản nháp thực tế
  const canSubmit = actualDraftCount > 0;

  // Filter danh sách theo trạng thái đã chọn - v2.6.1
  const filteredKeKhaiList = filterTrangThai
    ? keKhaiList.filter((item) => item.trang_thai === filterTrangThai)
    : keKhaiList;

  // Tạo options cho select tháng
  const thangOptions = Array.from({ length: 12 }, (_, i) => i + 1);

  // Tạo options cho select năm (từ 2025 đến năm hiện tại + 1)
  const namOptions = Array.from(
    { length: currentDate.getFullYear() - 2025 + 2 },
    (_, i) => 2025 + i
  );

  // ==========================================================================
  // RENDER LÃNH ĐẠO VIEW (+ HĐ 111 — Phase 3, 29/04/2026)
  // ==========================================================================
  if (isLanhDao || isHd111) {
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
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                </button>
                <div>
                  <h1 className="text-lg font-semibold text-gray-900">
                    Kê khai công việc
                    <span className={`ml-2 px-2 py-0.5 text-xs rounded-full ${
                      isHd111
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-purple-100 text-purple-700'
                    }`}>
                      {isHd111 ? 'Hợp đồng 111' : 'Lãnh đạo'}
                    </span>
                  </h1>
                  <p className="text-xs text-gray-500">{user?.ho_ten} - {user?.chuc_vu || user?.vai_tro?.ten_vai_tro}</p>
                </div>
              </div>

              {/* Filter tháng/năm */}
              <div className="flex items-center gap-3">
                <select
                  value={selectedThang}
                  onChange={(e) => setSelectedThang(Number(e.target.value))}
                  className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500"
                >
                  {Array.from({ length: 12 }, (_, i) => i + 1).map((t) => (
                    <option key={t} value={t}>Tháng {t}</option>
                  ))}
                </select>
                <select
                  value={selectedNam}
                  onChange={(e) => setSelectedNam(Number(e.target.value))}
                  className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500"
                >
                  {[2025, 2026, 2027].map((n) => (
                    <option key={n} value={n}>Năm {n}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </header>

        {/* Main - Leader View */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <LeaderKeKhaiView thang={selectedThang} nam={selectedNam} isHd111={isHd111} />
        </main>
      </div>
    );
  }

  // ==========================================================================
  // RENDER CC THƯỜNG VIEW
  // ==========================================================================

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
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </button>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">Kê khai công việc</h1>
                <p className="text-xs text-gray-500">{user?.ho_ten}</p>
              </div>
            </div>

            {/* User info */}
            <div className="text-right text-sm text-gray-600">
              {user?.don_vi?.ten_don_vi}
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* PL3 V2 (02/05/2026): CC V2 chỉ xem V1 cũ — read-only banner */}
        {isV1ReadOnly && (
          <div className="mb-4 rounded-md border border-amber-300 bg-amber-50 px-4 py-3 flex items-start justify-between gap-3">
            <div className="text-sm text-amber-900">
              <strong>Trang xem tham khảo (V1) — chỉ đọc.</strong>{' '}
              Hệ thống đã chuyển sang phiên bản V2_PL3. Trang này giữ lại để bạn
              đối chiếu kê khai cũ. Vui lòng kê khai mới tại{' '}
              <a href="/ke-khai-v2" className="font-semibold underline hover:text-amber-700">
                /ke-khai-v2
              </a>
              .
            </div>
            <button
              onClick={() => router.push('/ke-khai-v2')}
              className="px-3 py-1.5 text-xs font-medium text-white bg-amber-600 rounded hover:bg-amber-700 whitespace-nowrap"
            >
              Sang V2
            </button>
          </div>
        )}

        {/* Filter & Actions */}
        <div className="card mb-6">
          <div className="card-body">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              {/* Filter tháng/năm */}
              <div className="flex items-center gap-3">
                <label className="text-sm font-medium text-gray-700 whitespace-nowrap">Kỳ kê khai:</label>
                <select
                  value={selectedThang}
                  onChange={(e) => setSelectedThang(Number(e.target.value))}
                  className="input w-32"
                >
                  {thangOptions.map((t) => (
                    <option key={t} value={t}>
                      Tháng {t}
                    </option>
                  ))}
                </select>
                <select
                  value={selectedNam}
                  onChange={(e) => setSelectedNam(Number(e.target.value))}
                  className="input w-32"
                >
                  {namOptions.map((n) => (
                    <option key={n} value={n}>
                      Năm {n}
                    </option>
                  ))}
                </select>

                {/* Trạng thái chung */}
                {summary && summary.trang_thai_chung && (
                  <span className={`ml-2 ${getStatusBadgeClass(summary.trang_thai_chung)}`}>
                    {getStatusLabel(summary.trang_thai_chung)}
                  </span>
                )}
              </div>

              {/* Actions — ẩn toàn bộ khi V1 read-only */}
              {!isV1ReadOnly && (
                <div className="flex items-center gap-3">
                  <button
                    onClick={handleOpenCreate}
                    className="btn-primary"
                    disabled={summary?.trang_thai_chung === KpiStatus.APPROVED}
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Thêm công việc
                  </button>

                  <button
                    onClick={() => setIsMultiDayModalOpen(true)}
                    className="btn-outline"
                    disabled={summary?.trang_thai_chung === KpiStatus.APPROVED}
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    Kê khai nhiều ngày
                  </button>

                  {/* FIX v2.6.0: Hiển thị số bản nháp thực tế */}
                  {canSubmit && (
                    <button
                      onClick={handleOpenSubmitModal}
                      className="btn-success"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Gửi duyệt ({actualDraftCount})
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Summary Cards - Clickable Filter v2.6.1 */}
        {summary && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            {/* Tổng kê khai */}
            <div 
              className={`card cursor-pointer transition-all hover:shadow-md ${
                filterTrangThai === null ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:bg-gray-50'
              }`}
              onClick={() => setFilterTrangThai(null)}
            >
              <div className="card-body text-center">
                <p className={`text-2xl font-bold ${filterTrangThai === null ? 'text-blue-700' : 'text-blue-600'}`}>
                  {summary.tong_ke_khai}
                </p>
                <p className="text-sm text-gray-500">Tổng kê khai</p>
              </div>
            </div>

            {/* Bản nháp */}
            <div 
              className={`card cursor-pointer transition-all hover:shadow-md ${
                filterTrangThai === KpiStatus.DRAFT ? 'ring-2 ring-gray-500 bg-gray-100' : 'hover:bg-gray-50'
              }`}
              onClick={() => setFilterTrangThai(filterTrangThai === KpiStatus.DRAFT ? null : KpiStatus.DRAFT)}
            >
              <div className="card-body text-center">
                <p className={`text-2xl font-bold ${filterTrangThai === KpiStatus.DRAFT ? 'text-gray-700' : 'text-gray-600'}`}>
                  {summary.tong_nhap}
                </p>
                <p className="text-sm text-gray-500">Bản nháp</p>
              </div>
            </div>

            {/* Chờ duyệt */}
            <div 
              className={`card cursor-pointer transition-all hover:shadow-md ${
                filterTrangThai === KpiStatus.PENDING ? 'ring-2 ring-yellow-500 bg-yellow-50' : 'hover:bg-gray-50'
              }`}
              onClick={() => setFilterTrangThai(filterTrangThai === KpiStatus.PENDING ? null : KpiStatus.PENDING)}
            >
              <div className="card-body text-center">
                <p className={`text-2xl font-bold ${filterTrangThai === KpiStatus.PENDING ? 'text-yellow-700' : 'text-yellow-600'}`}>
                  {summary.tong_cho_duyet}
                </p>
                <p className="text-sm text-gray-500">Chờ duyệt</p>
              </div>
            </div>

            {/* Đã duyệt */}
            <div 
              className={`card cursor-pointer transition-all hover:shadow-md ${
                filterTrangThai === KpiStatus.APPROVED ? 'ring-2 ring-green-500 bg-green-50' : 'hover:bg-gray-50'
              }`}
              onClick={() => setFilterTrangThai(filterTrangThai === KpiStatus.APPROVED ? null : KpiStatus.APPROVED)}
            >
              <div className="card-body text-center">
                <p className={`text-2xl font-bold ${filterTrangThai === KpiStatus.APPROVED ? 'text-green-700' : 'text-green-600'}`}>
                  {summary.tong_da_duyet}
                </p>
                <p className="text-sm text-gray-500">Đã duyệt</p>
              </div>
            </div>
          </div>
        )}

        {/* Table */}
        <div className="card">
          <div className="card-header flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h2 className="text-base font-medium text-gray-900">
                Danh sách kê khai tháng {selectedThang}/{selectedNam}
              </h2>
              {/* Hiển thị filter đang chọn */}
              {filterTrangThai && (
                <span className={`text-xs px-2 py-1 rounded-full ${
                  filterTrangThai === KpiStatus.DRAFT ? 'bg-gray-100 text-gray-700' :
                  filterTrangThai === KpiStatus.PENDING ? 'bg-yellow-100 text-yellow-700' :
                  filterTrangThai === KpiStatus.APPROVED ? 'bg-green-100 text-green-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {filterTrangThai === KpiStatus.DRAFT ? 'Bản nháp' :
                   filterTrangThai === KpiStatus.PENDING ? 'Chờ duyệt' :
                   filterTrangThai === KpiStatus.APPROVED ? 'Đã duyệt' : filterTrangThai}
                  <button 
                    onClick={() => setFilterTrangThai(null)}
                    className="ml-1 hover:text-red-500"
                    title="Xóa bộ lọc"
                  >
                    ✕
                  </button>
                </span>
              )}
            </div>
            {/* Hiển thị số lượng đang hiển thị */}
            {!isLoading && keKhaiList.length > 0 && (
              <span className="text-sm text-gray-500">
                Hiển thị: {filteredKeKhaiList.length} / {keKhaiList.length} bản
              </span>
            )}
          </div>

          {isLoading ? (
            <div className="card-body flex flex-col items-center justify-center py-12">
              <svg className="animate-spin h-8 w-8 text-blue-600 mb-2" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <p className="text-sm text-gray-500">Đang tải dữ liệu...</p>
            </div>
          ) : error ? (
            <div className="card-body">
              <div className="bg-red-50 border border-red-200 rounded-md p-4 text-center">
                <p className="text-red-600">{error}</p>
                <button
                  onClick={loadData}
                  className="mt-2 text-sm text-red-700 underline"
                >
                  Thử lại
                </button>
              </div>
            </div>
          ) : filteredKeKhaiList.length === 0 ? (
            <div className="card-body text-center py-12">
              <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              {filterTrangThai ? (
                <>
                  <p className="text-gray-500">Không có kê khai nào với trạng thái này</p>
                  <button
                    onClick={() => setFilterTrangThai(null)}
                    className="mt-4 text-blue-600 hover:text-blue-800 text-sm underline"
                  >
                    Xem tất cả kê khai
                  </button>
                </>
              ) : (
                <>
                  <p className="text-gray-500">Chưa có kê khai nào trong tháng này</p>
                  {!isV1ReadOnly && (
                    <button
                      onClick={handleOpenCreate}
                      className="mt-4 btn-primary"
                    >
                      Thêm kê khai đầu tiên
                    </button>
                  )}
                </>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th className="w-12">STT</th>
                    <th className="w-24">Ngày</th>
                    <th>Nội dung công việc</th>
                    <th className="min-w-[200px]">Mô tả</th>
                    <th className="w-24">Cấp độ</th>
                    <th className="w-24 text-center">Số lượng</th>
                    <th className="w-32 text-center">SP quy đổi</th>
                    {/* v2.7.4: Cột lỗi CL/TĐ */}
                    <th className="w-28 text-center">Lỗi CL/TĐ</th>
                    <th className="w-32">LĐ Phê duyệt</th>
                    <th className="w-28 text-center">Trạng thái</th>
                    <th className="w-32 text-center">Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredKeKhaiList.map((item, index) => {
                    // v2.7.4: Cast item để truy cập các field mới
                    const itemFull = item as IKeKhaiBrief & {
                      danh_muc_sp?: { ten_cong_viec?: string; ma_danh_muc?: string; mo_ta?: string };
                      cap_do?: { ma_cap_do?: string };
                      nguoi_phe_duyet?: { id?: string; ho_ten?: string; chuc_vu?: string };
                      mo_ta_cong_viec?: string;
                      // Tự đánh giá
                      tu_danh_gia_chat_luong?: number;
                      tu_danh_gia_tien_do?: number;
                      ghi_chu_tu_dg_chat_luong?: string;
                      ghi_chu_tu_dg_tien_do?: string;
                      ghi_chu_tu_danh_gia?: string;
                      // Lãnh đạo chốt
                      so_loi_chat_luong?: number;
                      so_loi_tien_do?: number;
                      ghi_chu_loi_chat_luong?: string;
                      ghi_chu_loi_tien_do?: string;
                      y_kien_lanh_dao?: string;
                    };

                    const tuDgCl = itemFull.tu_danh_gia_chat_luong || 0;
                    const tuDgTd = itemFull.tu_danh_gia_tien_do || 0;
                    const loiCl = itemFull.so_loi_chat_luong || 0;
                    const loiTd = itemFull.so_loi_tien_do || 0;
                    const hasAnyError = tuDgCl > 0 || tuDgTd > 0 || loiCl > 0 || loiTd > 0;
                    const hasErrorDesc = !!(
                      itemFull.ghi_chu_tu_dg_chat_luong ||
                      itemFull.ghi_chu_tu_dg_tien_do ||
                      itemFull.ghi_chu_loi_chat_luong ||
                      itemFull.ghi_chu_loi_tien_do ||
                      itemFull.ghi_chu_tu_danh_gia ||
                      itemFull.y_kien_lanh_dao
                    );
                    const isExpanded = expandedRowId === item.id;

                    return (
                      <>
                        <tr key={item.id} className={isExpanded ? 'bg-gray-50' : ''}>
                          <td className="text-center text-gray-500">{index + 1}</td>
                          <td className="text-center text-sm text-gray-600 whitespace-nowrap">
                            {item.ngay_thuc_hien
                              ? new Date(item.ngay_thuc_hien).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })
                              : '-'}
                          </td>
                          <td>
                            <div>
                              <p className="font-medium text-gray-900">
                                {itemFull.danh_muc_sp?.ten_cong_viec || item.danh_muc_ten || '-'}
                              </p>
                              <p className="text-xs text-gray-500">
                                {itemFull.danh_muc_sp?.ma_danh_muc || item.danh_muc_ma || ''}
                              </p>
                            </div>
                          </td>
                          {/* v2.7.0: Cột mô tả công việc - wrap text */}
                          <td className="max-w-[300px]">
                            <p className="text-sm text-gray-600 whitespace-pre-wrap break-words">
                              {itemFull.danh_muc_sp?.mo_ta || itemFull.mo_ta_cong_viec || '-'}
                            </p>
                          </td>
                          <td>
                            <span className="badge-blue">
                              {itemFull.cap_do?.ma_cap_do || item.cap_do_ma || '-'}
                            </span>
                          </td>
                          <td className="text-center font-medium">{item.so_luong}</td>
                          <td className="text-center">
                            {item.so_sp_goc_quy_doi !== null ? (
                              <span className="font-medium text-green-600">
                                {item.so_sp_goc_quy_doi.toFixed(2)}
                              </span>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                          {/* v2.7.4: Cột lỗi CL/TĐ */}
                          <td className="text-center">
                            {hasAnyError ? (
                              <button
                                onClick={() => setExpandedRowId(isExpanded ? null : item.id)}
                                className="inline-flex flex-col items-center gap-0.5 group cursor-pointer"
                                title="Nhấn để xem chi tiết lỗi"
                              >
                                {/* Hiển thị số lỗi tự đánh giá */}
                                {(tuDgCl > 0 || tuDgTd > 0) && (
                                  <span className="text-xs px-1.5 py-0.5 rounded bg-orange-100 text-orange-700 group-hover:bg-orange-200">
                                    TD: {tuDgCl}/{tuDgTd}
                                  </span>
                                )}
                                {/* Hiển thị số lỗi lãnh đạo chốt */}
                                {(loiCl > 0 || loiTd > 0) && (
                                  <span className="text-xs px-1.5 py-0.5 rounded bg-red-100 text-red-700 group-hover:bg-red-200">
                                    LĐ: {loiCl}/{loiTd}
                                  </span>
                                )}
                                {/* Icon expand */}
                                {hasErrorDesc && (
                                  <svg className={`w-3.5 h-3.5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                  </svg>
                                )}
                              </button>
                            ) : (
                              <span className="text-gray-300 text-xs">—</span>
                            )}
                          </td>
                          <td>
                            {itemFull.nguoi_phe_duyet?.ho_ten ? (
                              <span className="text-sm text-gray-700">{itemFull.nguoi_phe_duyet.ho_ten}</span>
                            ) : (
                              <span className="text-gray-300 text-xs">—</span>
                            )}
                          </td>
                          <td className="text-center">
                            <span className={getStatusBadgeClass(item.trang_thai)}>
                              {getStatusLabel(item.trang_thai)}
                            </span>
                          </td>
                          <td>
                            <div className="flex items-center justify-center gap-2">
                              {!isV1ReadOnly && canEditKeKhai(item.trang_thai) && (
                                <>
                                  <button
                                    onClick={() => handleOpenEdit(item.id)}
                                    className="text-blue-600 hover:text-blue-800"
                                    title="Sửa"
                                  >
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                    </svg>
                                  </button>
                                  <button
                                    onClick={() => setDeleteConfirm({ id: item.id, name: item.danh_muc_ten })}
                                    className="text-red-600 hover:text-red-800"
                                    title="Xóa"
                                  >
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                    </svg>
                                  </button>
                                </>
                              )}
                              {!isV1ReadOnly && !canEditKeKhai(item.trang_thai) && (
                                <span className="text-gray-400 text-xs">Không thể sửa</span>
                              )}
                              {isV1ReadOnly && (
                                <span className="text-gray-400 text-xs">Chỉ xem</span>
                              )}
                            </div>
                          </td>
                        </tr>

                        {/* v2.7.4: Expandable row - chi tiết mô tả lỗi */}
                        {isExpanded && hasAnyError && (
                          <tr key={`${item.id}-detail`} className="bg-gray-50">
                            <td colSpan={11} className="px-6 py-3">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                {/* Tự đánh giá */}
                                {(tuDgCl > 0 || tuDgTd > 0) && (
                                  <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                                    <h4 className="font-medium text-orange-800 mb-2 flex items-center gap-1.5">
                                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                      </svg>
                                      Tự đánh giá
                                    </h4>
                                    <div className="space-y-1.5">
                                      {tuDgCl > 0 && (
                                        <div>
                                          <span className="text-orange-700 font-medium">Lỗi chất lượng: {tuDgCl}</span>
                                          {itemFull.ghi_chu_tu_dg_chat_luong && (
                                            <p className="text-orange-600 mt-0.5 pl-3 border-l-2 border-orange-300 whitespace-pre-wrap">
                                              {itemFull.ghi_chu_tu_dg_chat_luong}
                                            </p>
                                          )}
                                        </div>
                                      )}
                                      {tuDgTd > 0 && (
                                        <div>
                                          <span className="text-orange-700 font-medium">Lỗi tiến độ: {tuDgTd}</span>
                                          {itemFull.ghi_chu_tu_dg_tien_do && (
                                            <p className="text-orange-600 mt-0.5 pl-3 border-l-2 border-orange-300 whitespace-pre-wrap">
                                              {itemFull.ghi_chu_tu_dg_tien_do}
                                            </p>
                                          )}
                                        </div>
                                      )}
                                      {itemFull.ghi_chu_tu_danh_gia && (
                                        <div className="mt-1 pt-1 border-t border-orange-200">
                                          <span className="text-orange-600 text-xs">Ghi chú chung:</span>
                                          <p className="text-orange-600 whitespace-pre-wrap">{itemFull.ghi_chu_tu_danh_gia}</p>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                )}

                                {/* Lãnh đạo chốt */}
                                {(loiCl > 0 || loiTd > 0) && (
                                  <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                                    <h4 className="font-medium text-red-800 mb-2 flex items-center gap-1.5">
                                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                      </svg>
                                      Lãnh đạo chốt
                                    </h4>
                                    <div className="space-y-1.5">
                                      {loiCl > 0 && (
                                        <div>
                                          <span className="text-red-700 font-medium">Lỗi chất lượng: {loiCl}</span>
                                          {itemFull.ghi_chu_loi_chat_luong && (
                                            <p className="text-red-600 mt-0.5 pl-3 border-l-2 border-red-300 whitespace-pre-wrap">
                                              {itemFull.ghi_chu_loi_chat_luong}
                                            </p>
                                          )}
                                        </div>
                                      )}
                                      {loiTd > 0 && (
                                        <div>
                                          <span className="text-red-700 font-medium">Lỗi tiến độ: {loiTd}</span>
                                          {itemFull.ghi_chu_loi_tien_do && (
                                            <p className="text-red-600 mt-0.5 pl-3 border-l-2 border-red-300 whitespace-pre-wrap">
                                              {itemFull.ghi_chu_loi_tien_do}
                                            </p>
                                          )}
                                        </div>
                                      )}
                                      {itemFull.y_kien_lanh_dao && (
                                        <div className="mt-1 pt-1 border-t border-red-200">
                                          <span className="text-red-600 text-xs">Ý kiến lãnh đạo:</span>
                                          <p className="text-red-600 whitespace-pre-wrap">{itemFull.y_kien_lanh_dao}</p>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* Modal thêm/sửa */}
      <KpiTargetModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingKeKhai(null);
        }}
        onSuccess={loadData}
        editData={editingKeKhai}
        thang={selectedThang}
        nam={selectedNam}
      />

      {/* Modal kê khai nhiều ngày */}
      <KpiMultiDayModal
        isOpen={isMultiDayModalOpen}
        onClose={() => setIsMultiDayModalOpen(false)}
        onSuccess={loadData}
        thang={selectedThang}
        nam={selectedNam}
      />

      {/* Confirm Delete Dialog */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="fixed inset-0 bg-black/50" onClick={() => setDeleteConfirm(null)} />
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="relative bg-white rounded-lg shadow-xl max-w-sm w-full p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Xác nhận xóa</h3>
              <p className="text-gray-600 mb-4">
                Bạn có chắc muốn xóa kê khai <strong>&quot;{deleteConfirm.name}&quot;</strong>?
              </p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setDeleteConfirm(null)}
                  className="btn-outline"
                  disabled={isDeleting}
                >
                  Hủy
                </button>
                <button
                  onClick={handleDelete}
                  className="btn-danger"
                  disabled={isDeleting}
                >
                  {isDeleting ? 'Đang xóa...' : 'Xóa'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* v2.7.3: Confirm Submit Dialog đơn giản - không cần chọn người phê duyệt */}
      {submitConfirm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="fixed inset-0 bg-black/50" onClick={() => setSubmitConfirm(false)} />
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Xác nhận gửi duyệt</h3>
              
              <p className="text-gray-600 mb-4">
                Bạn có chắc muốn gửi <strong>{actualDraftCount} bản kê khai</strong> đi phê duyệt?
              </p>

              <p className="text-sm text-yellow-600 mb-4">
                ⚠️ Sau khi gửi, bạn sẽ không thể sửa/xóa các bản kê khai này.
              </p>

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setSubmitConfirm(false)}
                  className="btn-outline"
                  disabled={isSubmitting}
                >
                  Hủy
                </button>
                <button
                  onClick={handleSubmitKpi}
                  className="btn-success"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Đang gửi...' : 'Gửi duyệt'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}