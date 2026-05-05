/**
 * src/app/(main)/phan-cong-phu-trach/page.tsx
 * ===========================================
 * Trang quản lý phân công CCT/PCCT phụ trách đơn vị.
 *
 * Chỉ CCT (vai_tro = CCT) hoặc Super Admin mới truy cập được.
 *
 * Phục vụ KPI lãnh đạo công thức mới (từ tháng 4/2026).
 *
 * Phiên bản: 1.0 (05/05/2026)
 */

'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/useAuthStore';
import { phanCongPhuTrachService } from '@/services/phanCongPhuTrach.service';
import {
  IDonViKhaDung,
  ILanhDaoKhaDung,
  IPhanCongPhuTrach,
} from '@/types/phanCongPhuTrach';

// =============================================================================
// HELPERS
// =============================================================================

const todayStr = () => new Date().toISOString().slice(0, 10);

function fmtDate(s: string | null | undefined): string {
  if (!s) return '—';
  const [y, m, d] = s.split('-');
  return `${d}/${m}/${y}`;
}

function getApiErrorMessage(err: unknown, fallback = 'Có lỗi xảy ra'): string {
  // axios error shape
  const e = err as { response?: { data?: { detail?: { error?: { message?: string } } | string } } };
  const detail = e?.response?.data?.detail;
  if (detail && typeof detail === 'object' && 'error' in detail && detail.error?.message) {
    return detail.error.message;
  }
  if (typeof detail === 'string') return detail;
  return fallback;
}

// =============================================================================
// MAIN PAGE
// =============================================================================

export default function PhanCongPhuTrachPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuthStore();

  const [authChecked, setAuthChecked] = useState(false);
  const [items, setItems] = useState<IPhanCongPhuTrach[]>([]);
  const [lanhDaoOptions, setLanhDaoOptions] = useState<ILanhDaoKhaDung[]>([]);
  const [donViOptions, setDonViOptions] = useState<IDonViKhaDung[]>([]);
  const [filterNgay, setFilterNgay] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Modal create
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({
    lanh_dao_id: '',
    don_vi_id: '',
    hieu_luc_tu: todayStr(),
    hieu_luc_den: '',
    ghi_chu: '',
  });
  const [submitting, setSubmitting] = useState(false);

  // Modal kết thúc
  const [endTarget, setEndTarget] = useState<IPhanCongPhuTrach | null>(null);
  const [endDate, setEndDate] = useState<string>(todayStr());

  // ---------------------------------------------------------------------------
  // AUTH GATE
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }
    const allowed = user?.is_system_admin || user?.vai_tro?.ma_vai_tro === 'CCT';
    if (!allowed) {
      router.replace('/dashboard');
      return;
    }
    setAuthChecked(true);
  }, [isAuthenticated, isLoading, user, router]);

  // ---------------------------------------------------------------------------
  // DATA LOAD
  // ---------------------------------------------------------------------------
  const loadList = async (ngay?: string) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await phanCongPhuTrachService.list(ngay ? { ngay } : undefined);
      setItems(data);
    } catch (err) {
      setErrorMsg(getApiErrorMessage(err, 'Không tải được danh sách'));
    } finally {
      setLoading(false);
    }
  };

  const loadMeta = async () => {
    try {
      const [lds, dvs] = await Promise.all([
        phanCongPhuTrachService.getLanhDaoKhaDung(),
        phanCongPhuTrachService.getDonViKhaDung(),
      ]);
      setLanhDaoOptions(lds);
      setDonViOptions(dvs);
    } catch (err) {
      setErrorMsg(getApiErrorMessage(err, 'Không tải được danh mục'));
    }
  };

  useEffect(() => {
    if (!authChecked) return;
    void loadList();
    void loadMeta();
  }, [authChecked]);

  // ---------------------------------------------------------------------------
  // ACTIONS
  // ---------------------------------------------------------------------------

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.lanh_dao_id || !createForm.don_vi_id || !createForm.hieu_luc_tu) {
      setErrorMsg('Vui lòng nhập đủ Lãnh đạo, Đơn vị, Ngày bắt đầu');
      return;
    }
    setSubmitting(true);
    setErrorMsg(null);
    try {
      await phanCongPhuTrachService.create({
        lanh_dao_id: createForm.lanh_dao_id,
        don_vi_id: createForm.don_vi_id,
        hieu_luc_tu: createForm.hieu_luc_tu,
        hieu_luc_den: createForm.hieu_luc_den || null,
        ghi_chu: createForm.ghi_chu || null,
      });
      setShowCreate(false);
      setCreateForm({
        lanh_dao_id: '',
        don_vi_id: '',
        hieu_luc_tu: todayStr(),
        hieu_luc_den: '',
        ghi_chu: '',
      });
      await loadList(filterNgay || undefined);
    } catch (err) {
      setErrorMsg(getApiErrorMessage(err, 'Tạo phân công thất bại'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleEndAssignment = async () => {
    if (!endTarget) return;
    if (!endDate) {
      setErrorMsg('Vui lòng chọn ngày kết thúc');
      return;
    }
    setSubmitting(true);
    setErrorMsg(null);
    try {
      await phanCongPhuTrachService.ketThuc(endTarget.id, { hieu_luc_den: endDate });
      setEndTarget(null);
      await loadList(filterNgay || undefined);
    } catch (err) {
      setErrorMsg(getApiErrorMessage(err, 'Kết thúc phân công thất bại'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Xóa phân công này? Hành động không thể hoàn tác.')) return;
    setErrorMsg(null);
    try {
      await phanCongPhuTrachService.remove(id);
      await loadList(filterNgay || undefined);
    } catch (err) {
      setErrorMsg(getApiErrorMessage(err, 'Xóa thất bại'));
    }
  };

  // ---------------------------------------------------------------------------
  // RENDER
  // ---------------------------------------------------------------------------

  const isActiveAt = (pc: IPhanCongPhuTrach, ngay: string): boolean => {
    if (pc.is_deleted) return false;
    if (pc.hieu_luc_tu > ngay) return false;
    if (pc.hieu_luc_den && pc.hieu_luc_den < ngay) return false;
    return true;
  };

  const sortedItems = useMemo(() => {
    return [...items].sort((a, b) => {
      // Theo cấp bậc LĐ rồi theo ngày
      const aIsCCT = a.lanh_dao && lanhDaoOptions.find((l) => l.id === a.lanh_dao_id)?.ma_vai_tro === 'CCT';
      const bIsCCT = b.lanh_dao && lanhDaoOptions.find((l) => l.id === b.lanh_dao_id)?.ma_vai_tro === 'CCT';
      if (aIsCCT && !bIsCCT) return -1;
      if (!aIsCCT && bIsCCT) return 1;
      return b.hieu_luc_tu.localeCompare(a.hieu_luc_tu);
    });
  }, [items, lanhDaoOptions]);

  if (isLoading || !authChecked) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-3 text-gray-500">Đang kiểm tra quyền...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Phân công phụ trách đơn vị</h1>
          <p className="text-sm text-gray-600 mt-1">
            Quản lý CCT/PCCT phụ trách đơn vị (versioned theo thời gian) — phục vụ tính KPI lãnh đạo từ tháng 4/2026.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          + Tạo phân công
        </button>
      </div>

      {/* Filter */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4 flex items-end gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Hiển thị có hiệu lực tại ngày</label>
          <input
            type="date"
            value={filterNgay}
            onChange={(e) => setFilterNgay(e.target.value)}
            className="border border-gray-300 rounded px-3 py-1.5 text-sm"
          />
        </div>
        <button
          onClick={() => loadList(filterNgay || undefined)}
          className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded text-sm"
        >
          Lọc
        </button>
        <button
          onClick={() => {
            setFilterNgay('');
            void loadList();
          }}
          className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900"
        >
          Xem tất cả
        </button>
      </div>

      {/* Error */}
      {errorMsg && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          {errorMsg}
        </div>
      )}

      {/* Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-700">
            <tr>
              <th className="px-4 py-2 text-left font-medium">Lãnh đạo</th>
              <th className="px-4 py-2 text-left font-medium">Cấp</th>
              <th className="px-4 py-2 text-left font-medium">Đơn vị phụ trách</th>
              <th className="px-4 py-2 text-left font-medium">Hiệu lực từ</th>
              <th className="px-4 py-2 text-left font-medium">Hiệu lực đến</th>
              <th className="px-4 py-2 text-left font-medium">Trạng thái</th>
              <th className="px-4 py-2 text-right font-medium">Hành động</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={7} className="px-4 py-6 text-center text-gray-500">Đang tải...</td></tr>
            )}
            {!loading && sortedItems.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                Chưa có phân công nào. Bấm <b>+ Tạo phân công</b> để thêm.
              </td></tr>
            )}
            {!loading && sortedItems.map((pc) => {
              const ldInfo = lanhDaoOptions.find((l) => l.id === pc.lanh_dao_id);
              const active = isActiveAt(pc, todayStr());
              return (
                <tr key={pc.id} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-2">
                    <div className="font-medium text-gray-900">{pc.lanh_dao?.ho_ten || '?'}</div>
                    <div className="text-xs text-gray-500">{pc.lanh_dao?.ma_cc}</div>
                  </td>
                  <td className="px-4 py-2">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                      ldInfo?.ma_vai_tro === 'CCT' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'
                    }`}>
                      {ldInfo?.ma_vai_tro || '?'}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    <div className="font-medium">{pc.don_vi?.ten_don_vi}</div>
                    <div className="text-xs text-gray-500">{pc.don_vi?.ma_don_vi}</div>
                  </td>
                  <td className="px-4 py-2">{fmtDate(pc.hieu_luc_tu)}</td>
                  <td className="px-4 py-2">{pc.hieu_luc_den ? fmtDate(pc.hieu_luc_den) : <span className="text-gray-400">—</span>}</td>
                  <td className="px-4 py-2">
                    {active ? (
                      <span className="inline-block px-2 py-0.5 rounded text-xs bg-green-100 text-green-800">Đang hiệu lực</span>
                    ) : (
                      <span className="inline-block px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-700">Đã kết thúc</span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-right space-x-2">
                    {active && !pc.hieu_luc_den && (
                      <button
                        onClick={() => { setEndTarget(pc); setEndDate(todayStr()); }}
                        className="text-orange-600 hover:text-orange-800 text-xs font-medium"
                      >
                        Kết thúc
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(pc.id)}
                      className="text-red-600 hover:text-red-800 text-xs font-medium"
                    >
                      Xóa
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Modal: Create */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
            <form onSubmit={handleCreate}>
              <div className="px-5 py-3 border-b border-gray-200">
                <h3 className="font-semibold text-lg">Tạo phân công mới</h3>
              </div>
              <div className="p-5 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Lãnh đạo phụ trách *</label>
                  <select
                    value={createForm.lanh_dao_id}
                    onChange={(e) => setCreateForm({ ...createForm, lanh_dao_id: e.target.value })}
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                    required
                  >
                    <option value="">— Chọn LĐ —</option>
                    {lanhDaoOptions.map((ld) => (
                      <option key={ld.id} value={ld.id}>
                        [{ld.ma_vai_tro}] {ld.ho_ten} ({ld.ma_cc})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Đơn vị được phụ trách *</label>
                  <select
                    value={createForm.don_vi_id}
                    onChange={(e) => setCreateForm({ ...createForm, don_vi_id: e.target.value })}
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                    required
                  >
                    <option value="">— Chọn đơn vị —</option>
                    {donViOptions.map((dv) => (
                      <option key={dv.id} value={dv.id}>
                        {dv.ten_don_vi} ({dv.ma_don_vi})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Hiệu lực từ *</label>
                    <input
                      type="date"
                      value={createForm.hieu_luc_tu}
                      onChange={(e) => setCreateForm({ ...createForm, hieu_luc_tu: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Hiệu lực đến (tùy chọn)</label>
                    <input
                      type="date"
                      value={createForm.hieu_luc_den}
                      onChange={(e) => setCreateForm({ ...createForm, hieu_luc_den: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ghi chú</label>
                  <textarea
                    value={createForm.ghi_chu}
                    onChange={(e) => setCreateForm({ ...createForm, ghi_chu: e.target.value })}
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                    rows={2}
                  />
                </div>
              </div>
              <div className="px-5 py-3 border-t border-gray-200 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded"
                  disabled={submitting}
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm bg-blue-600 text-white hover:bg-blue-700 rounded disabled:opacity-50"
                  disabled={submitting}
                >
                  {submitting ? 'Đang tạo...' : 'Tạo'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Kết thúc */}
      {endTarget && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="px-5 py-3 border-b border-gray-200">
              <h3 className="font-semibold text-lg">Kết thúc phân công</h3>
            </div>
            <div className="p-5 space-y-3">
              <p className="text-sm text-gray-700">
                Kết thúc phân công <b>{endTarget.lanh_dao?.ho_ten}</b> phụ trách đơn vị <b>{endTarget.don_vi?.ten_don_vi}</b>?
              </p>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ngày kết thúc *</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  min={endTarget.hieu_luc_tu}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                />
                <p className="text-xs text-gray-500 mt-1">Phải ≥ ngày bắt đầu ({fmtDate(endTarget.hieu_luc_tu)})</p>
              </div>
            </div>
            <div className="px-5 py-3 border-t border-gray-200 flex justify-end gap-2">
              <button
                onClick={() => setEndTarget(null)}
                className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded"
                disabled={submitting}
              >
                Hủy
              </button>
              <button
                onClick={handleEndAssignment}
                className="px-4 py-2 text-sm bg-orange-600 text-white hover:bg-orange-700 rounded disabled:opacity-50"
                disabled={submitting}
              >
                {submitting ? 'Đang xử lý...' : 'Kết thúc'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
