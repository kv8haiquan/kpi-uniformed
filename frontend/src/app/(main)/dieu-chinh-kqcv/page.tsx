/**
 * src/app/(main)/dieu-chinh-kqcv/page.tsx
 * =======================================
 * Trang quản lý điều chỉnh KQCV (Yêu cầu 2 — 06/05/2026).
 *
 * 2 tab: "Của tôi" (đã đề xuất) + "Chờ tôi duyệt" (LĐ cấp trên).
 * Chỉ LĐ truy cập được.
 */

'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/useAuthStore';
import { dieuChinhKqcvService } from '@/services/dieuChinhKqcv.service';
import { IDieuChinhKqcv } from '@/types/dieuChinhKqcv';

const LANH_DAO_CAP_BAC = new Set(['PHO_DON_VI', 'TRUONG_DON_VI', 'PHO_CHI_CUC_TRUONG', 'CHI_CUC_TRUONG']);

const TT_LABEL: Record<string, string> = {
  NHAP: 'Nháp',
  CHO_PHE_DUYET: 'Chờ duyệt',
  DA_PHE_DUYET: 'Đã duyệt',
  TU_CHOI: 'Từ chối',
};

const TT_COLOR: Record<string, string> = {
  NHAP: 'bg-gray-100 text-gray-700',
  CHO_PHE_DUYET: 'bg-yellow-100 text-yellow-800',
  DA_PHE_DUYET: 'bg-green-100 text-green-800',
  TU_CHOI: 'bg-red-100 text-red-800',
};

function getApiErrorMessage(err: unknown, fallback: string): string {
  const e = err as { response?: { data?: { detail?: { error?: { message?: string } } } } };
  return e?.response?.data?.detail?.error?.message ?? fallback;
}

export default function DieuChinhKqcvPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuthStore();

  const [tab, setTab] = useState<'me' | 'cho_duyet'>('me');
  const [items, setItems] = useState<IDieuChinhKqcv[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  // Filter cho tab "Phê duyệt"
  const [filterTrangThai, setFilterTrangThai] = useState<string>('CHO_PHE_DUYET');
  const [filterNguoiDC, setFilterNguoiDC] = useState<string>('');

  // Modal phê duyệt / từ chối / trả lại
  const [actionTarget, setActionTarget] = useState<IDieuChinhKqcv | null>(null);
  const [actionType, setActionType] = useState<'phe_duyet' | 'tu_choi' | 'tra_lai' | null>(null);
  const [yKien, setYKien] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Auth gate
  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }
    const cap = user?.vai_tro?.cap_bac;
    if (!cap || !LANH_DAO_CAP_BAC.has(cap)) {
      router.replace('/dashboard');
      return;
    }
    setAuthChecked(true);
  }, [isAuthenticated, isLoading, user, router]);

  // Load list — tab "Phê duyệt" gọi với trang_thai=ALL rồi filter phía FE
  useEffect(() => {
    if (!authChecked) return;
    setLoading(true);
    setError(null);
    const promise = tab === 'me'
      ? dieuChinhKqcvService.listMe()
      : dieuChinhKqcvService.listChoToiDuyet({ trang_thai: 'ALL' });
    promise
      .then(setItems)
      .catch((e) => setError(getApiErrorMessage(e, 'Không tải được danh sách')))
      .finally(() => setLoading(false));
  }, [authChecked, tab, reloadKey]);

  // Danh sách người đề xuất distinct (cho dropdown filter)
  const dsNguoiDeXuat = useMemo(() => {
    if (tab !== 'cho_duyet') return [];
    const seen = new Set<string>();
    const list: { id: string; label: string }[] = [];
    for (const it of items) {
      const nd = it.nguoi_dieu_chinh;
      if (!nd || seen.has(nd.id)) continue;
      seen.add(nd.id);
      list.push({ id: nd.id, label: `${nd.ho_ten} (${nd.ma_cc})` });
    }
    list.sort((a, b) => a.label.localeCompare(b.label, 'vi'));
    return list;
  }, [items, tab]);

  // Filtered items khi tab = "Phê duyệt"
  const displayedItems = useMemo(() => {
    if (tab !== 'cho_duyet') return items;
    return items.filter((it) => {
      if (filterTrangThai !== 'ALL' && it.trang_thai !== filterTrangThai) return false;
      if (filterNguoiDC && it.nguoi_dieu_chinh_id !== filterNguoiDC) return false;
      return true;
    });
  }, [items, tab, filterTrangThai, filterNguoiDC]);

  const openAction = (dc: IDieuChinhKqcv, type: 'phe_duyet' | 'tu_choi' | 'tra_lai') => {
    setActionTarget(dc);
    setActionType(type);
    setYKien('');
  };

  const handleSubmit = async () => {
    if (!actionTarget || !actionType) return;
    if ((actionType === 'tu_choi' || actionType === 'tra_lai') && !yKien.trim()) {
      alert(actionType === 'tu_choi' ? 'Phải nhập lý do từ chối' : 'Phải nhập lý do trả lại');
      return;
    }
    setSubmitting(true);
    try {
      if (actionType === 'phe_duyet') {
        await dieuChinhKqcvService.pheDuyet(actionTarget.id, yKien || undefined);
      } else if (actionType === 'tu_choi') {
        await dieuChinhKqcvService.tuChoi(actionTarget.id, yKien.trim());
      } else {
        await dieuChinhKqcvService.traLai(actionTarget.id, yKien.trim());
      }
      setActionTarget(null);
      setActionType(null);
      setReloadKey((k) => k + 1);
    } catch (e) {
      alert(getApiErrorMessage(e, 'Thao tác thất bại'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Xóa bản điều chỉnh này?')) return;
    try {
      await dieuChinhKqcvService.remove(id);
      setReloadKey((k) => k + 1);
    } catch (e) {
      alert(getApiErrorMessage(e, 'Xóa thất bại'));
    }
  };

  const handleSubmitToReview = async (id: string) => {
    try {
      await dieuChinhKqcvService.guiDuyet(id);
      setReloadKey((k) => k + 1);
    } catch (e) {
      alert(getApiErrorMessage(e, 'Gửi duyệt thất bại'));
    }
  };

  if (!authChecked) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Điều chỉnh KQCV</h1>
        <p className="text-sm text-gray-600 mt-1">
          Quản lý các bản điều chỉnh kết quả công việc của cấp dưới (Yêu cầu 2 — 06/05/2026).
        </p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-1.5 mb-6 flex gap-2">
        <button
          onClick={() => setTab('me')}
          className={`flex-1 px-4 py-3 rounded-lg text-sm font-semibold transition-all ${
            tab === 'me'
              ? 'bg-blue-50 text-blue-700 border-2 border-blue-300'
              : 'text-gray-500 border-2 border-transparent hover:bg-gray-50'
          }`}
        >
          Bản tôi đề xuất
        </button>
        <button
          onClick={() => setTab('cho_duyet')}
          className={`flex-1 px-4 py-3 rounded-lg text-sm font-semibold transition-all ${
            tab === 'cho_duyet'
              ? 'bg-orange-50 text-orange-700 border-2 border-orange-300'
              : 'text-gray-500 border-2 border-transparent hover:bg-gray-50'
          }`}
        >
          Phê duyệt
        </button>
      </div>

      {/* Filter bar (chỉ hiện ở tab Phê duyệt) */}
      {tab === 'cho_duyet' && (
        <div className="mb-4 bg-white border border-gray-200 rounded-lg p-3 flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Trạng thái</label>
            <select
              value={filterTrangThai}
              onChange={(e) => setFilterTrangThai(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm min-w-[160px]"
            >
              <option value="ALL">Tất cả</option>
              <option value="NHAP">Nháp</option>
              <option value="CHO_PHE_DUYET">Chờ duyệt</option>
              <option value="DA_PHE_DUYET">Đã duyệt</option>
              <option value="TU_CHOI">Từ chối</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Người đề xuất</label>
            <select
              value={filterNguoiDC}
              onChange={(e) => setFilterNguoiDC(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm min-w-[220px]"
            >
              <option value="">Tất cả</option>
              {dsNguoiDeXuat.map((p) => (
                <option key={p.id} value={p.id}>{p.label}</option>
              ))}
            </select>
          </div>
          {(filterTrangThai !== 'CHO_PHE_DUYET' || filterNguoiDC) && (
            <button
              onClick={() => { setFilterTrangThai('CHO_PHE_DUYET'); setFilterNguoiDC(''); }}
              className="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded border border-gray-200"
            >
              ↻ Reset
            </button>
          )}
          <div className="ml-auto text-xs text-gray-500 self-center">
            Hiển thị {displayedItems.length}/{items.length}
          </div>
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-700">
            <tr>
              <th className="px-4 py-2 text-left font-medium">Người đề xuất</th>
              <th className="px-4 py-2 text-left font-medium">Người duyệt</th>
              <th className="px-4 py-2 text-left font-medium">Giá trị cũ → mới</th>
              <th className="px-4 py-2 text-left font-medium">Lý do</th>
              <th className="px-4 py-2 text-center font-medium">Trạng thái</th>
              <th className="px-4 py-2 text-center font-medium">Hành động</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={6} className="px-4 py-6 text-center text-gray-500">Đang tải...</td></tr>
            )}
            {!loading && displayedItems.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  {tab === 'me'
                    ? 'Bạn chưa đề xuất điều chỉnh nào'
                    : items.length === 0
                      ? 'Không có bản điều chỉnh nào cần bạn duyệt'
                      : 'Không có bản điều chỉnh nào khớp filter'}
                </td>
              </tr>
            )}
            {!loading && displayedItems.map((dc) => {
              const old = dc.gia_tri_cu;
              const neu = dc.gia_tri_moi;
              const change: string[] = [];
              if (old.so_loi_chat_luong !== neu.so_loi_chat_luong) {
                change.push(`CL: ${old.so_loi_chat_luong} → ${neu.so_loi_chat_luong}`);
              }
              if (old.so_loi_tien_do !== neu.so_loi_tien_do) {
                change.push(`TĐ: ${old.so_loi_tien_do} → ${neu.so_loi_tien_do}`);
              }
              if (old.is_chua_hoan_thanh !== neu.is_chua_hoan_thanh) {
                change.push(neu.is_chua_hoan_thanh ? '⏳ Đánh dấu CHƯA HOÀN THÀNH' : '✓ Đã hoàn thành');
              }
              return (
                <tr key={dc.id} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-2">
                    <div className="font-medium">{dc.nguoi_dieu_chinh?.ho_ten}</div>
                    <div className="text-xs text-gray-500">{dc.nguoi_dieu_chinh?.ma_cc}</div>
                  </td>
                  <td className="px-4 py-2">
                    <div className="font-medium">{dc.nguoi_phe_duyet?.ho_ten}</div>
                    <div className="text-xs text-gray-500">{dc.nguoi_phe_duyet?.ma_cc}</div>
                  </td>
                  <td className="px-4 py-2 text-xs">
                    {change.length === 0 ? <span className="text-gray-400">(không đổi)</span> : (
                      <ul className="space-y-0.5">
                        {change.map((c, i) => <li key={i} className="font-mono">{c}</li>)}
                      </ul>
                    )}
                  </td>
                  <td className="px-4 py-2 max-w-md">
                    <p className="text-xs text-gray-600 truncate" title={dc.ly_do}>{dc.ly_do}</p>
                    {dc.y_kien_phe_duyet && (
                      <p className="text-xs text-blue-600 mt-1 italic">↳ {dc.y_kien_phe_duyet}</p>
                    )}
                  </td>
                  <td className="px-4 py-2 text-center">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${TT_COLOR[dc.trang_thai]}`}>
                      {TT_LABEL[dc.trang_thai]}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-center text-xs space-x-2 whitespace-nowrap">
                    {tab === 'me' && dc.trang_thai === 'NHAP' && (
                      <>
                        <button
                          onClick={() => handleSubmitToReview(dc.id)}
                          className="text-blue-600 hover:text-blue-800 font-medium"
                        >
                          Gửi duyệt
                        </button>
                        <button
                          onClick={() => handleDelete(dc.id)}
                          className="text-red-600 hover:text-red-800 font-medium"
                        >
                          Xóa
                        </button>
                      </>
                    )}
                    {tab === 'cho_duyet' && dc.trang_thai === 'CHO_PHE_DUYET' && (
                      <>
                        <button
                          onClick={() => openAction(dc, 'phe_duyet')}
                          className="text-green-600 hover:text-green-800 font-medium"
                        >
                          Phê duyệt
                        </button>
                        <button
                          onClick={() => openAction(dc, 'tu_choi')}
                          className="text-red-600 hover:text-red-800 font-medium"
                        >
                          Từ chối
                        </button>
                      </>
                    )}
                    {tab === 'cho_duyet' && dc.trang_thai === 'DA_PHE_DUYET' && (
                      <button
                        onClick={() => openAction(dc, 'tra_lai')}
                        className="text-orange-600 hover:text-orange-800 font-medium"
                        title="Trả lại bản đã duyệt nhầm về Nháp để LĐ đề xuất sửa lại"
                      >
                        ↩ Trả lại
                      </button>
                    )}
                    {((tab === 'me' && dc.trang_thai !== 'NHAP') ||
                      (tab === 'cho_duyet' &&
                        dc.trang_thai !== 'CHO_PHE_DUYET' &&
                        dc.trang_thai !== 'DA_PHE_DUYET')) && (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Modal phê duyệt / từ chối / trả lại */}
      {actionTarget && actionType && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
            <div className="px-5 py-3 border-b border-gray-200">
              <h3 className="font-semibold text-lg">
                {actionType === 'phe_duyet' && '✓ Phê duyệt điều chỉnh'}
                {actionType === 'tu_choi' && '✕ Từ chối điều chỉnh'}
                {actionType === 'tra_lai' && '↩ Trả lại bản đã duyệt'}
              </h3>
            </div>
            <div className="p-5 space-y-3">
              <div className="text-sm">
                <p>Người đề xuất: <b>{actionTarget.nguoi_dieu_chinh?.ho_ten}</b></p>
                <p className="text-xs text-gray-600 mt-1">Lý do: <em>{actionTarget.ly_do}</em></p>
                {actionType === 'tra_lai' && (
                  <p className="text-xs text-orange-700 mt-2 bg-orange-50 border border-orange-200 rounded p-2">
                    ⚠️ Bản điều chỉnh sẽ chuyển về <b>Nháp</b> để LĐ đề xuất chỉnh sửa và gửi duyệt lại.
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {actionType === 'tra_lai' ? 'Lý do trả lại' : 'Ý kiến'}
                  {(actionType === 'tu_choi' || actionType === 'tra_lai') ? (
                    <span className="text-red-500"> *</span>
                  ) : (
                    <span className="text-gray-400"> (tùy chọn)</span>
                  )}
                </label>
                <textarea
                  value={yKien}
                  onChange={(e) => setYKien(e.target.value)}
                  rows={3}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                  placeholder={
                    actionType === 'tu_choi'
                      ? 'Vui lòng nhập lý do từ chối...'
                      : actionType === 'tra_lai'
                        ? 'Vui lòng nhập lý do trả lại...'
                        : ''
                  }
                />
              </div>
            </div>
            <div className="px-5 py-3 border-t border-gray-200 flex justify-end gap-2">
              <button
                onClick={() => { setActionTarget(null); setActionType(null); }}
                className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded"
                disabled={submitting}
              >
                Hủy
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className={`px-4 py-2 text-sm text-white rounded disabled:opacity-50 ${
                  actionType === 'phe_duyet'
                    ? 'bg-green-600 hover:bg-green-700'
                    : actionType === 'tu_choi'
                      ? 'bg-red-600 hover:bg-red-700'
                      : 'bg-orange-600 hover:bg-orange-700'
                }`}
              >
                {submitting
                  ? 'Đang xử lý...'
                  : actionType === 'phe_duyet'
                    ? 'Phê duyệt + Áp dụng'
                    : actionType === 'tu_choi'
                      ? 'Từ chối'
                      : 'Trả lại'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
