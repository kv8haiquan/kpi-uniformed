'use client';

/**
 * app/(main)/ke-khai-v2/page.tsx
 * ==============================
 * Trang Kê khai KPI V2_PL3 (28/04/2026).
 *
 * Khác V1 (`/ke-khai`):
 * - Modal mới với search 2.812 mục PL3.
 * - Banner Tổng SP đã kê (mẫu số V2).
 * - Bảng hiển thị thêm cột Lĩnh vực + Nhóm + Hệ số.
 *
 * Logic version (sidebar đã redirect đúng nhưng vẫn check ở đây để chống truy cập tay):
 * - User effective_kpi_version === 'V1' → redirect /ke-khai.
 * - Ngược lại → render trang.
 */

import { Fragment, useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Plus,
  CalendarDays,
  Trash2,
  Pencil,
  RefreshCw,
  AlertTriangle,
  Send,
  ChevronDown,
  Lock,
  X,
  FileText,
} from 'lucide-react';

import { useAuthStore } from '@/stores/useAuthStore';
import { kpiV2Service } from '@/services/kpi-v2.service';
import { kpiService } from '@/services/kpi.service';
import { IKeKhaiV2Response, IThongKeKeKhaiThangV2 } from '@/types/kpi-v2';
import { isApiError } from '@/lib/axios';

import { KpiTargetModalV2 } from '@/components/kpi-v2/KpiTargetModalV2';
import { KpiMultiDayModalV2 } from '@/components/kpi-v2/KpiMultiDayModalV2';
import LeaderAssessmentDDE from '@/components/ke-khai/LeaderAssessmentDDE';

const TRANG_THAI_LABEL: Record<string, string> = {
  NHAP: 'Nháp',
  CHO_PHE_DUYET: 'Chờ duyệt',
  DA_PHE_DUYET: 'Đã duyệt',
  TU_CHOI: 'Bị từ chối',
  HUY: 'Đã hủy',
};

const TRANG_THAI_BADGE: Record<string, string> = {
  NHAP: 'bg-gray-100 text-gray-700',
  CHO_PHE_DUYET: 'bg-yellow-100 text-yellow-800',
  DA_PHE_DUYET: 'bg-green-100 text-green-800',
  TU_CHOI: 'bg-red-100 text-red-800',
  HUY: 'bg-gray-200 text-gray-500',
};

export default function KeKhaiV2Page() {
  const router = useRouter();
  const { user } = useAuthStore();

  const now = new Date();
  const [thang, setThang] = useState(now.getMonth() + 1);
  const [nam, setNam] = useState(now.getFullYear());

  const [list, setList] = useState<IKeKhaiV2Response[]>([]);
  const [thongKe, setThongKe] = useState<IThongKeKeKhaiThangV2 | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [openSingle, setOpenSingle] = useState(false);
  const [openMulti, setOpenMulti] = useState(false);
  const [editing, setEditing] = useState<IKeKhaiV2Response | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  // Phase 1: expand row chi tiết lỗi + batch gửi duyệt
  const [expandedRowId, setExpandedRowId] = useState<string | null>(null);
  const [submitConfirm, setSubmitConfirm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  // 06/05/2026: checkbox chọn từng CV để gửi duyệt
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Phase 2: filter trạng thái (null = tất cả)
  const [filterTrangThai, setFilterTrangThai] = useState<string | null>(null);

  // Redirect nếu user không thuộc đối tượng V2:
  // - HĐ 111: luôn dùng form cũ (/ke-khai)
  // - LĐ thật: chỉ dùng V2 từ tháng 4/2026 trở đi (Phase 3, 05/05/2026)
  // - CC pinned V1: dùng /ke-khai
  useEffect(() => {
    if (!user) return;
    const isLanhDao = user.is_lanh_dao;
    const isHd111 = user.is_hd_111;
    const isV2ActiveForLeader = nam > 2026 || (nam === 2026 && thang >= 4);

    if (isHd111) {
      router.replace('/ke-khai');
      return;
    }
    if (isLanhDao && !isV2ActiveForLeader) {
      router.replace('/ke-khai');
      return;
    }
    if (!isLanhDao && user.effective_kpi_version === 'V1') {
      router.replace('/ke-khai');
    }
  }, [user, router, thang, nam]);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Phase 2: dùng getAllKeKhaiByMonth để loop hết các trang (CC kê >100 bản không bị mất)
      const [thongKeRes, allList] = await Promise.all([
        kpiV2Service.getThongKeThang(thang, nam),
        kpiV2Service.getAllKeKhaiByMonth(thang, nam),
      ]);
      setThongKe(thongKeRes);
      setList(allList);
    } catch (err: unknown) {
      console.error(err);
      if (isApiError(err)) setError(err.message);
      else setError('Lỗi tải dữ liệu');
    } finally {
      setLoading(false);
    }
  }, [thang, nam]);

  useEffect(() => {
    reload();
  }, [reload]);

  const handleDelete = async (id: string) => {
    if (!confirm('Xoá bản kê khai này?')) return;
    setDeleting(id);
    try {
      await kpiV2Service.deleteKeKhai(id);
      await reload();
    } catch (err: unknown) {
      if (isApiError(err)) alert(err.message);
      else alert('Lỗi xóa');
    } finally {
      setDeleting(null);
    }
  };

  const yearOptions = useMemo(() => {
    const arr: number[] = [];
    for (let y = now.getFullYear() + 1; y >= 2025; y--) arr.push(y);
    return arr;
  }, [now]);

  // Bản nháp gửi được = NHAP có nguoi_phe_duyet_id (TU_CHOI cũng nháp lại nhưng spec V1 chỉ gửi NHAP)
  const draftList = useMemo(
    () => list.filter((kk) => kk.trang_thai === 'NHAP'),
    [list]
  );
  const actualDraftCount = draftList.length;

  // CV nháp đã được tick (lọc theo selectedIds + hợp lệ)
  const selectedDrafts = useMemo(
    () => draftList.filter((kk) => selectedIds.has(kk.id)),
    [draftList, selectedIds]
  );

  // Auto-clean: bỏ khỏi selectedIds những bản đã không còn NHAP (đã gửi/duyệt/xóa)
  useEffect(() => {
    const validIds = new Set(draftList.map((kk) => kk.id));
    setSelectedIds((prev) => {
      const next = new Set<string>();
      for (const id of prev) if (validIds.has(id)) next.add(id);
      return next.size === prev.size ? prev : next;
    });
  }, [draftList]);

  const allDraftsSelected = draftList.length > 0 && selectedIds.size === draftList.length;
  const someDraftsSelected = selectedIds.size > 0 && !allDraftsSelected;

  const toggleSelectAll = () => {
    setSelectedIds(allDraftsSelected ? new Set() : new Set(draftList.map((kk) => kk.id)));
  };
  const toggleSelectOne = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Phase 2: counters cho 4 cards
  const counts = useMemo(() => {
    let nhap = 0;
    let cho = 0;
    let da = 0;
    list.forEach((kk) => {
      if (kk.trang_thai === 'NHAP') nhap++;
      else if (kk.trang_thai === 'CHO_PHE_DUYET') cho++;
      else if (kk.trang_thai === 'DA_PHE_DUYET') da++;
    });
    return { tong: list.length, nhap, cho, da };
  }, [list]);

  // Phase 2: list sau khi áp filter
  const filteredList = useMemo(
    () =>
      filterTrangThai
        ? list.filter((kk) => kk.trang_thai === filterTrangThai)
        : list,
    [list, filterTrangThai]
  );

  // Phase 2: tháng đã chốt → suy ra từ is_khoa của bất kỳ bản nào
  const isLocked = useMemo(() => list.some((kk) => kk.is_khoa), [list]);

  const handleBatchSubmit = async () => {
    // 06/05/2026: chỉ submit các CV nháp đã được TICK
    const toSubmit = selectedDrafts;
    if (toSubmit.length === 0) {
      alert('Vui lòng tick chọn ít nhất 1 bản nháp để gửi duyệt.');
      setSubmitConfirm(false);
      return;
    }
    const noApprover = toSubmit.filter((d) => !d.nguoi_phe_duyet_id);
    if (noApprover.length > 0) {
      alert(
        `Có ${noApprover.length} bản nháp chưa chọn người phê duyệt.\n` +
          `Vui lòng sửa từng bản và chọn người phê duyệt trước khi gửi.`
      );
      setSubmitConfirm(false);
      return;
    }

    setSubmitting(true);
    let ok = 0;
    let fail = 0;
    for (const d of toSubmit) {
      try {
        await kpiService.submitKeKhaiSingle(d.id, d.nguoi_phe_duyet_id!);
        ok++;
      } catch (err) {
        console.error(`Submit ${d.id} failed`, err);
        fail++;
      }
    }
    setSubmitting(false);
    setSubmitConfirm(false);
    // Reset selection sau khi submit xong
    setSelectedIds(new Set());

    if (fail > 0) {
      alert(
        `Kết quả gửi duyệt:\n` +
          `✅ Thành công: ${ok} bản\n` +
          `❌ Thất bại: ${fail} bản\n\n` +
          `Vui lòng kiểm tra lại các bản gửi thất bại.`
      );
    } else {
      alert(`✅ Đã gửi thành công ${ok} bản kê khai đi phê duyệt!`);
    }
    await reload();
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Kê khai công việc — V2_PL3
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Phiên bản mới với 2.812 mục PL3 + 5 nhóm
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={thang}
            onChange={(e) => setThang(Number(e.target.value))}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            {Array.from({ length: 12 }).map((_, i) => (
              <option key={i + 1} value={i + 1}>
                Tháng {i + 1}
              </option>
            ))}
          </select>
          <select
            value={nam}
            onChange={(e) => setNam(Number(e.target.value))}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            {yearOptions.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
          <button
            onClick={reload}
            className="p-2 rounded-md border border-gray-300 hover:bg-gray-50"
            title="Tải lại"
          >
            <RefreshCw className="h-4 w-4 text-gray-600" />
          </button>
          <button
            onClick={() => router.push('/ke-khai')}
            className="px-3 py-2 rounded-md border border-gray-300 hover:bg-gray-50 text-sm text-gray-700 inline-flex items-center gap-1.5"
            title="Xem dữ liệu kê khai V1 cũ (chỉ đọc)"
          >
            <FileText className="h-4 w-4" />
            Xem V1 cũ
          </button>
        </div>
      </div>

      {/* Banner Tổng điểm */}
      {thongKe && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 px-5 py-4">
          <div className="flex items-start gap-3">
            <div className="flex-1">
              <p className="text-sm text-blue-900 font-medium">
                Tổng điểm đã kê khai tháng {String(thang).padStart(2, '0')}/{nam}
              </p>
              <div className="mt-2 grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Đã duyệt:</span>{' '}
                  <strong className="text-green-700 text-base">
                    {thongKe.tong_sp_da_duyet.toFixed(6).replace(/\.?0+$/, '')} điểm
                  </strong>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Mẫu số chính thức tính KPI
                  </p>
                </div>
                <div>
                  <span className="text-gray-600">Chờ duyệt:</span>{' '}
                  <strong className="text-yellow-700 text-base">
                    {thongKe.tong_sp_cho_duyet.toFixed(6).replace(/\.?0+$/, '')} điểm
                  </strong>
                </div>
                <div>
                  <span className="text-gray-600">Dự kiến:</span>{' '}
                  <strong className="text-blue-700 text-base">
                    {thongKe.tong_sp_du_kien.toFixed(6).replace(/\.?0+$/, '')} điểm
                  </strong>
                </div>
              </div>
            </div>
          </div>
          {thongKe.tong_sp_da_duyet === 0 && thongKe.tong_sp_du_kien > 0 && (
            <div className="mt-3 flex items-center gap-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 px-3 py-1.5 rounded">
              <AlertTriangle className="h-4 w-4" />
              Bạn chưa có bản kê khai nào được duyệt. Mẫu số V2 = 0 sẽ làm KPI = 0
              (tự xếp mức D).
            </div>
          )}
        </div>
      )}

      {/* Phase 2: 4 Summary cards clickable filter */}
      {!loading && list.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <button
            type="button"
            onClick={() => setFilterTrangThai(null)}
            className={`rounded-lg border p-4 text-left transition-all ${
              filterTrangThai === null
                ? 'ring-2 ring-blue-500 bg-blue-50 border-blue-200'
                : 'bg-white border-gray-200 hover:bg-gray-50'
            }`}
          >
            <p
              className={`text-2xl font-bold ${
                filterTrangThai === null ? 'text-blue-700' : 'text-blue-600'
              }`}
            >
              {counts.tong}
            </p>
            <p className="text-xs text-gray-500">Tổng kê khai</p>
          </button>
          <button
            type="button"
            onClick={() =>
              setFilterTrangThai(filterTrangThai === 'NHAP' ? null : 'NHAP')
            }
            className={`rounded-lg border p-4 text-left transition-all ${
              filterTrangThai === 'NHAP'
                ? 'ring-2 ring-gray-500 bg-gray-100 border-gray-300'
                : 'bg-white border-gray-200 hover:bg-gray-50'
            }`}
          >
            <p
              className={`text-2xl font-bold ${
                filterTrangThai === 'NHAP' ? 'text-gray-800' : 'text-gray-600'
              }`}
            >
              {counts.nhap}
            </p>
            <p className="text-xs text-gray-500">Bản nháp</p>
          </button>
          <button
            type="button"
            onClick={() =>
              setFilterTrangThai(
                filterTrangThai === 'CHO_PHE_DUYET' ? null : 'CHO_PHE_DUYET'
              )
            }
            className={`rounded-lg border p-4 text-left transition-all ${
              filterTrangThai === 'CHO_PHE_DUYET'
                ? 'ring-2 ring-yellow-500 bg-yellow-50 border-yellow-200'
                : 'bg-white border-gray-200 hover:bg-gray-50'
            }`}
          >
            <p
              className={`text-2xl font-bold ${
                filterTrangThai === 'CHO_PHE_DUYET'
                  ? 'text-yellow-700'
                  : 'text-yellow-600'
              }`}
            >
              {counts.cho}
            </p>
            <p className="text-xs text-gray-500">Chờ duyệt</p>
          </button>
          <button
            type="button"
            onClick={() =>
              setFilterTrangThai(
                filterTrangThai === 'DA_PHE_DUYET' ? null : 'DA_PHE_DUYET'
              )
            }
            className={`rounded-lg border p-4 text-left transition-all ${
              filterTrangThai === 'DA_PHE_DUYET'
                ? 'ring-2 ring-green-500 bg-green-50 border-green-200'
                : 'bg-white border-gray-200 hover:bg-gray-50'
            }`}
          >
            <p
              className={`text-2xl font-bold ${
                filterTrangThai === 'DA_PHE_DUYET'
                  ? 'text-green-700'
                  : 'text-green-600'
              }`}
            >
              {counts.da}
            </p>
            <p className="text-xs text-gray-500">Đã duyệt</p>
          </button>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={() => {
            setEditing(null);
            setOpenSingle(true);
          }}
          disabled={isLocked}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          title={isLocked ? 'Tháng đã chốt — không thể thêm' : undefined}
        >
          <Plus className="h-4 w-4" /> Thêm kê khai
        </button>
        <button
          onClick={() => setOpenMulti(true)}
          disabled={isLocked}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-300 rounded-md hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed"
          title={isLocked ? 'Tháng đã chốt — không thể thêm' : undefined}
        >
          <CalendarDays className="h-4 w-4" /> Kê khai nhiều ngày
        </button>
        {actualDraftCount > 0 && !isLocked && (
          <button
            onClick={() => setSubmitConfirm(true)}
            disabled={selectedDrafts.length === 0}
            title={
              selectedDrafts.length === 0
                ? 'Tick chọn các bản nháp trong bảng để gửi duyệt'
                : `Gửi duyệt ${selectedDrafts.length} bản đã chọn`
            }
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-4 w-4" />
            Gửi duyệt {selectedDrafts.length > 0
              ? `${selectedDrafts.length} đã chọn`
              : `(0 / ${actualDraftCount} nháp)`}
          </button>
        )}
        {isLocked && (
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-gray-700 bg-gray-100 border border-gray-300">
            <Lock className="h-3.5 w-3.5" />
            Tháng đã chốt
          </span>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {/* Phase 2: header bar — filter chip + counter */}
        {!loading && list.length > 0 && (
          <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-medium text-gray-700">
                Danh sách kê khai tháng {String(thang).padStart(2, '0')}/{nam}
              </h2>
              {filterTrangThai && (
                <span
                  className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full ${
                    TRANG_THAI_BADGE[filterTrangThai] ?? 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {TRANG_THAI_LABEL[filterTrangThai] ?? filterTrangThai}
                  <button
                    type="button"
                    onClick={() => setFilterTrangThai(null)}
                    className="hover:text-red-500"
                    title="Xóa bộ lọc"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              )}
            </div>
            <span className="text-xs text-gray-500">
              Hiển thị: <strong>{filteredList.length}</strong> / {list.length} bản
            </span>
          </div>
        )}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {/* Checkbox cột chọn — chỉ hiển thị khi có nháp + chưa khóa */}
                <th className="px-3 py-3 w-10 text-center">
                  {actualDraftCount > 0 && !isLocked ? (
                    <input
                      type="checkbox"
                      checked={allDraftsSelected}
                      ref={(el) => {
                        if (el) el.indeterminate = someDraftsSelected;
                      }}
                      onChange={toggleSelectAll}
                      title="Chọn / bỏ chọn tất cả nháp"
                      className="w-4 h-4 cursor-pointer"
                    />
                  ) : null}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Mã
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                  Ngày
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Công việc
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Mô tả
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Lĩnh vực
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nhóm
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Hệ số
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  SL
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Điểm quy đổi
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Lỗi CL/TĐ
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  LĐ Phê duyệt
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trạng thái
                </th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {loading && (
                <tr>
                  <td colSpan={14} className="px-4 py-8 text-center text-sm text-gray-500">
                    Đang tải…
                  </td>
                </tr>
              )}
              {!loading && list.length === 0 && (
                <tr>
                  <td colSpan={14} className="px-4 py-12 text-center">
                    <FileText className="h-12 w-12 mx-auto text-gray-300 mb-3" />
                    <p className="text-sm text-gray-500 mb-3">
                      Chưa có kê khai V2 nào trong tháng này.
                    </p>
                    <button
                      onClick={() => {
                        setEditing(null);
                        setOpenSingle(true);
                      }}
                      disabled={isLocked}
                      className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Plus className="h-4 w-4" /> Thêm kê khai đầu tiên
                    </button>
                  </td>
                </tr>
              )}
              {!loading && list.length > 0 && filteredList.length === 0 && (
                <tr>
                  <td colSpan={14} className="px-4 py-12 text-center">
                    <p className="text-sm text-gray-500 mb-3">
                      Không có kê khai nào với trạng thái này.
                    </p>
                    <button
                      onClick={() => setFilterTrangThai(null)}
                      className="text-sm text-blue-600 hover:text-blue-800 underline"
                    >
                      Xem tất cả kê khai
                    </button>
                  </td>
                </tr>
              )}
              {filteredList.map((kk) => {
                const editable =
                  kk.trang_thai === 'NHAP' || kk.trang_thai === 'TU_CHOI';
                const dm = kk.danh_muc_sp;
                const tuDgCl = kk.tu_danh_gia_chat_luong || 0;
                const tuDgTd = kk.tu_danh_gia_tien_do || 0;
                const loiCl = kk.so_loi_chat_luong || 0;
                const loiTd = kk.so_loi_tien_do || 0;
                const hasAnyError = tuDgCl > 0 || tuDgTd > 0 || loiCl > 0 || loiTd > 0;
                const hasErrorDetail = !!(
                  kk.ghi_chu_tu_dg_chat_luong ||
                  kk.ghi_chu_tu_dg_tien_do ||
                  kk.ghi_chu_loi_chat_luong ||
                  kk.ghi_chu_loi_tien_do ||
                  kk.ghi_chu_tu_danh_gia ||
                  kk.y_kien_lanh_dao
                );
                const isExpanded = expandedRowId === kk.id;
                const isDraft = kk.trang_thai === 'NHAP';
                const isSelected = selectedIds.has(kk.id);
                return (
                  <Fragment key={kk.id}>
                    <tr
                      className={
                        isSelected
                          ? 'bg-blue-50'
                          : isExpanded
                            ? 'bg-gray-50'
                            : 'hover:bg-gray-50'
                      }
                    >
                      <td className="px-3 py-3 text-center">
                        {isDraft && !isLocked ? (
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleSelectOne(kk.id)}
                            className="w-4 h-4 cursor-pointer"
                          />
                        ) : null}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-600 font-mono">
                        {dm?.ma_danh_muc ?? '—'}
                      </td>
                      {/* Cột Ngày thực hiện */}
                      <td className="px-4 py-3 text-center text-xs text-gray-600 whitespace-nowrap">
                        {kk.ngay_thuc_hien
                          ? new Date(kk.ngay_thuc_hien).toLocaleDateString('vi-VN', {
                              day: '2-digit',
                              month: '2-digit',
                            })
                          : '—'}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <p className="text-gray-900 line-clamp-2">
                          {dm?.ten_cong_viec ?? '—'}
                        </p>
                        {dm?.san_pham_dau_ra && (
                          <p className="text-xs text-gray-500 mt-0.5">
                            Đầu ra: {dm.san_pham_dau_ra}
                          </p>
                        )}
                      </td>
                      {/* Cột Mô tả công việc (CC nhập) */}
                      <td className="px-4 py-3 text-sm max-w-[250px]">
                        {kk.mo_ta_cong_viec ? (
                          <p className="text-gray-600 whitespace-pre-wrap break-words line-clamp-3">
                            {kk.mo_ta_cong_viec}
                          </p>
                        ) : (
                          <span className="text-gray-300 text-xs">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center text-sm font-medium text-gray-700">
                        {kk.linh_vuc_snapshot ?? '—'}
                      </td>
                      <td className="px-4 py-3 text-center text-sm text-gray-700">
                        {kk.nhom_pl3_snapshot ?? '—'}
                      </td>
                      <td className="px-4 py-3 text-right text-sm font-mono text-blue-700">
                        {kk.he_so_quy_doi_snapshot?.toFixed(6).replace(/\.?0+$/, '') ?? '—'}
                      </td>
                      <td className="px-4 py-3 text-right text-sm">{kk.so_luong}</td>
                      <td className="px-4 py-3 text-right text-sm font-mono">
                        {kk.so_sp_goc_quy_doi?.toFixed(6).replace(/\.?0+$/, '') ?? '—'}
                      </td>
                      {/* Cột Lỗi CL/TĐ */}
                      <td className="px-4 py-3 text-center">
                        {hasAnyError ? (
                          <button
                            type="button"
                            onClick={() =>
                              setExpandedRowId(isExpanded ? null : kk.id)
                            }
                            className="inline-flex flex-col items-center gap-0.5 group"
                            title="Click để xem chi tiết lỗi"
                          >
                            {(tuDgCl > 0 || tuDgTd > 0) && (
                              <span className="text-xs px-1.5 py-0.5 rounded bg-orange-100 text-orange-700 group-hover:bg-orange-200">
                                TD: {tuDgCl}/{tuDgTd}
                              </span>
                            )}
                            {(loiCl > 0 || loiTd > 0) && (
                              <span className="text-xs px-1.5 py-0.5 rounded bg-red-100 text-red-700 group-hover:bg-red-200">
                                LĐ: {loiCl}/{loiTd}
                              </span>
                            )}
                            {hasErrorDetail && (
                              <ChevronDown
                                className={`h-3.5 w-3.5 text-gray-400 transition-transform ${
                                  isExpanded ? 'rotate-180' : ''
                                }`}
                              />
                            )}
                          </button>
                        ) : (
                          <span className="text-gray-300 text-xs">—</span>
                        )}
                      </td>
                      {/* Cột LĐ Phê duyệt */}
                      <td className="px-4 py-3 text-sm text-gray-700 whitespace-nowrap">
                        {kk.nguoi_phe_duyet?.ho_ten ? (
                          <span title={kk.nguoi_phe_duyet.chuc_vu ?? ''}>
                            {kk.nguoi_phe_duyet.ho_ten}
                          </span>
                        ) : (
                          <span className="text-gray-300 text-xs">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                            TRANG_THAI_BADGE[kk.trang_thai] ?? 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {TRANG_THAI_LABEL[kk.trang_thai] ?? kk.trang_thai}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        {editable && (
                          <div className="flex items-center justify-end gap-1">
                            <button
                              onClick={() => {
                                setEditing(kk);
                                setOpenSingle(true);
                              }}
                              className="p-1 rounded text-blue-600 hover:bg-blue-50"
                              title="Sửa"
                            >
                              <Pencil className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(kk.id)}
                              disabled={deleting === kk.id}
                              className="p-1 rounded text-red-500 hover:bg-red-50 disabled:opacity-40"
                              title="Xóa"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                    {/* Expandable detail row — chi tiết mô tả lỗi */}
                    {isExpanded && hasAnyError && (
                      <tr className="bg-gray-50">
                        <td colSpan={14} className="px-6 py-3">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                            {(tuDgCl > 0 || tuDgTd > 0 || kk.ghi_chu_tu_danh_gia) && (
                              <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                                <h4 className="font-medium text-orange-800 mb-2">
                                  Tự đánh giá
                                </h4>
                                <div className="space-y-1.5">
                                  {tuDgCl > 0 && (
                                    <div>
                                      <span className="text-orange-700 font-medium">
                                        Lỗi chất lượng: {tuDgCl}
                                      </span>
                                      {kk.ghi_chu_tu_dg_chat_luong && (
                                        <p className="text-orange-600 mt-0.5 pl-3 border-l-2 border-orange-300 whitespace-pre-wrap">
                                          {kk.ghi_chu_tu_dg_chat_luong}
                                        </p>
                                      )}
                                    </div>
                                  )}
                                  {tuDgTd > 0 && (
                                    <div>
                                      <span className="text-orange-700 font-medium">
                                        Lỗi tiến độ: {tuDgTd}
                                      </span>
                                      {kk.ghi_chu_tu_dg_tien_do && (
                                        <p className="text-orange-600 mt-0.5 pl-3 border-l-2 border-orange-300 whitespace-pre-wrap">
                                          {kk.ghi_chu_tu_dg_tien_do}
                                        </p>
                                      )}
                                    </div>
                                  )}
                                  {kk.ghi_chu_tu_danh_gia && (
                                    <div className="mt-1 pt-1 border-t border-orange-200">
                                      <span className="text-orange-600 text-xs">
                                        Ghi chú chung:
                                      </span>
                                      <p className="text-orange-600 whitespace-pre-wrap">
                                        {kk.ghi_chu_tu_danh_gia}
                                      </p>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                            {(loiCl > 0 || loiTd > 0 || kk.y_kien_lanh_dao) && (
                              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                                <h4 className="font-medium text-red-800 mb-2">
                                  Lãnh đạo chốt
                                </h4>
                                <div className="space-y-1.5">
                                  {loiCl > 0 && (
                                    <div>
                                      <span className="text-red-700 font-medium">
                                        Lỗi chất lượng: {loiCl}
                                      </span>
                                      {kk.ghi_chu_loi_chat_luong && (
                                        <p className="text-red-600 mt-0.5 pl-3 border-l-2 border-red-300 whitespace-pre-wrap">
                                          {kk.ghi_chu_loi_chat_luong}
                                        </p>
                                      )}
                                    </div>
                                  )}
                                  {loiTd > 0 && (
                                    <div>
                                      <span className="text-red-700 font-medium">
                                        Lỗi tiến độ: {loiTd}
                                      </span>
                                      {kk.ghi_chu_loi_tien_do && (
                                        <p className="text-red-600 mt-0.5 pl-3 border-l-2 border-red-300 whitespace-pre-wrap">
                                          {kk.ghi_chu_loi_tien_do}
                                        </p>
                                      )}
                                    </div>
                                  )}
                                  {kk.y_kien_lanh_dao && (
                                    <div className="mt-1 pt-1 border-t border-red-200">
                                      <span className="text-red-600 text-xs">
                                        Ý kiến lãnh đạo:
                                      </span>
                                      <p className="text-red-600 whitespace-pre-wrap">
                                        {kk.y_kien_lanh_dao}
                                      </p>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section đánh giá d/đ/e — chỉ LĐ thật + tháng ≥ 4/2026 (HĐ 111 không có DDE) */}
      {user?.is_lanh_dao && !user?.is_hd_111 &&
        (nam > 2026 || (nam === 2026 && thang >= 4)) && (
          <div className="mt-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 bg-gradient-to-r from-purple-600 to-indigo-600">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <span>👔</span>
                  Đánh giá năng lực lãnh đạo (d, đ, e)
                </h2>
                <p className="text-xs text-purple-100 mt-1">
                  Tự đánh giá 3 chỉ số: Kết quả đơn vị · Tổ chức triển khai · Đoàn kết nội bộ
                </p>
              </div>
              <div className="p-5">
                <LeaderAssessmentDDE thang={thang} nam={nam} />
              </div>
            </div>
          </div>
        )}

      {/* Modals */}
      <KpiTargetModalV2
        open={openSingle}
        onClose={() => {
          setOpenSingle(false);
          setEditing(null);
        }}
        onSuccess={reload}
        thang={thang}
        nam={nam}
        editing={editing}
      />
      <KpiMultiDayModalV2
        open={openMulti}
        onClose={() => setOpenMulti(false)}
        onSuccess={reload}
        thang={thang}
        nam={nam}
      />

      {/* Confirm dialog batch submit */}
      {submitConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => !submitting && setSubmitConfirm(false)}
          />
          <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Xác nhận gửi duyệt
            </h3>
            <p className="text-gray-600 mb-3">
              Bạn có chắc muốn gửi <strong>{selectedDrafts.length} bản kê khai đã chọn</strong>{' '}
              đi phê duyệt?
              {selectedDrafts.length < actualDraftCount && (
                <span className="block text-xs text-gray-500 mt-1">
                  ({actualDraftCount - selectedDrafts.length} bản nháp khác sẽ giữ nguyên)
                </span>
              )}
            </p>
            <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded p-2 mb-4">
              ⚠️ Sau khi gửi, bạn sẽ không thể sửa/xóa các bản này (trừ khi bị từ chối).
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setSubmitConfirm(false)}
                disabled={submitting}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-60"
              >
                Hủy
              </button>
              <button
                onClick={handleBatchSubmit}
                disabled={submitting}
                className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-60"
              >
                {submitting ? 'Đang gửi…' : 'Gửi duyệt'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
