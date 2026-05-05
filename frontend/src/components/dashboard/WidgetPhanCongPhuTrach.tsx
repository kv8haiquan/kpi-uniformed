/**
 * src/components/dashboard/WidgetPhanCongPhuTrach.tsx
 * ===================================================
 * Widget cho PCCT/CCT tự cập nhật danh sách đơn vị mình phụ trách.
 *
 * Hiển thị: card list đơn vị đang phụ trách + nút "Cập nhật".
 * Click → modal checkbox đa lựa chọn, có cảnh báo đơn vị đã có LĐ khác phụ trách.
 *
 * Phiên bản: 1.0 (05/05/2026)
 */

'use client';

import { useEffect, useState } from 'react';
import { phanCongPhuTrachService } from '@/services/phanCongPhuTrach.service';
import {
  IDonViWithCurrent,
  IMyActiveAssignment,
  IPhanCongConflict,
} from '@/types/phanCongPhuTrach';

interface Props {
  /** Cần render hay không (chỉ render cho PCCT/CCT) */
  visible: boolean;
}

function getApiErrorMessage(err: unknown, fallback: string): string {
  const e = err as { response?: { data?: { detail?: { error?: { message?: string; conflicts?: IPhanCongConflict[] } } } } };
  return e?.response?.data?.detail?.error?.message ?? fallback;
}

function getApiConflicts(err: unknown): IPhanCongConflict[] {
  const e = err as { response?: { data?: { detail?: { error?: { conflicts?: IPhanCongConflict[] } } } } };
  return e?.response?.data?.detail?.error?.conflicts ?? [];
}

export default function WidgetPhanCongPhuTrach({ visible }: Props) {
  const [active, setActive] = useState<IMyActiveAssignment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [donViList, setDonViList] = useState<IDonViWithCurrent[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [submitting, setSubmitting] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);
  const [conflicts, setConflicts] = useState<IPhanCongConflict[]>([]);

  const loadActive = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await phanCongPhuTrachService.getMyActiveAssignments();
      setActive(data);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Không tải được phân công'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (visible) {
      void loadActive();
    }
  }, [visible]);

  const openModal = async () => {
    setModalError(null);
    setConflicts([]);
    try {
      const dv = await phanCongPhuTrachService.getDonViWithCurrent();
      setDonViList(dv);
      // Pre-select những đơn vị mình đang phụ trách
      setSelected(new Set(dv.filter((d) => d.is_mine).map((d) => d.id)));
      setShowModal(true);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Không tải được danh mục đơn vị'));
    }
  };

  const toggle = (donViId: string) => {
    const next = new Set(selected);
    if (next.has(donViId)) next.delete(donViId);
    else next.add(donViId);
    setSelected(next);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setModalError(null);
    setConflicts([]);
    try {
      await phanCongPhuTrachService.replaceMyAssignments(Array.from(selected));
      setShowModal(false);
      await loadActive();
    } catch (err) {
      setModalError(getApiErrorMessage(err, 'Cập nhật thất bại'));
      setConflicts(getApiConflicts(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (!visible) return null;

  return (
    <>
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-base font-semibold text-gray-900 flex items-center gap-2">
              <span>🎯</span>
              Đơn vị tôi phụ trách{' '}
              <span className="text-sm font-normal text-gray-500">({active.length})</span>
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">
              KPI của bạn được tính trên scope các đơn vị này
            </p>
          </div>
          <button
            onClick={openModal}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            Cập nhật
          </button>
        </div>

        {error && (
          <div className="p-2.5 bg-red-50 border border-red-200 rounded text-sm text-red-700 mb-3">
            {error}
          </div>
        )}

        {loading ? (
          <p className="text-sm text-gray-500">Đang tải...</p>
        ) : active.length === 0 ? (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
            <p className="font-medium">Chưa có đơn vị phụ trách</p>
            <p className="text-xs mt-1 text-amber-700">
              KPI của bạn hiện chỉ tính d/đ/e (= 0.5). Bấm <b>Cập nhật</b> để chọn đơn vị.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {active.map((a) => (
              <div
                key={a.phan_cong_id}
                className="border border-gray-200 rounded-lg p-2.5 bg-gray-50"
              >
                <div className="text-xs text-gray-500">{a.ma_don_vi}</div>
                <div className="text-sm font-medium text-gray-900 truncate" title={a.ten_don_vi}>
                  {a.ten_don_vi}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal chọn đơn vị */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
            <div className="px-5 py-3 border-b border-gray-200 flex items-center justify-between">
              <h3 className="font-semibold text-lg">Chọn đơn vị phụ trách</h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-gray-600"
                disabled={submitting}
              >
                ✕
              </button>
            </div>

            <div className="p-5 overflow-y-auto flex-1">
              <p className="text-xs text-gray-500 mb-3">
                Tích vào đơn vị bạn muốn phụ trách. Đơn vị đã có lãnh đạo khác phụ trách
                sẽ được cảnh báo và phải nhường lại trước khi bạn chọn.
              </p>

              {modalError && (
                <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded">
                  <p className="text-sm text-red-700 font-medium">{modalError}</p>
                  {conflicts.length > 0 && (
                    <ul className="text-xs text-red-700 mt-2 space-y-1 list-disc pl-5">
                      {conflicts.map((c) => (
                        <li key={c.don_vi_id}>
                          <b>{c.ma_don_vi}</b> — đang được {c.lanh_dao_ho_ten} ({c.lanh_dao_ma_cc}) phụ trách
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              <div className="space-y-2">
                {donViList.map((dv) => {
                  const isSelected = selected.has(dv.id);
                  const hasOtherOwner =
                    dv.current_lanh_dao_id !== null && !dv.is_mine;
                  return (
                    <label
                      key={dv.id}
                      className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                        isSelected
                          ? 'border-blue-300 bg-blue-50'
                          : hasOtherOwner
                            ? 'border-amber-200 bg-amber-50/50 hover:bg-amber-50'
                            : 'border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggle(dv.id)}
                        className="mt-1 w-4 h-4 text-blue-600 rounded"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-500 font-mono">{dv.ma_don_vi}</span>
                          {dv.is_mine && (
                            <span className="text-[10px] px-1.5 py-0.5 bg-green-100 text-green-700 rounded font-medium">
                              Đang phụ trách
                            </span>
                          )}
                          {hasOtherOwner && (
                            <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded font-medium">
                              ⚠️ Đã có chủ
                            </span>
                          )}
                        </div>
                        <div className="text-sm font-medium text-gray-900 mt-0.5">
                          {dv.ten_don_vi}
                        </div>
                        {hasOtherOwner && (
                          <div className="text-xs text-amber-700 mt-1">
                            Đang được{' '}
                            <b>
                              {dv.current_lanh_dao_ho_ten} ({dv.current_lanh_dao_ma_cc})
                            </b>{' '}
                            phụ trách
                          </div>
                        )}
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>

            <div className="px-5 py-3 border-t border-gray-200 flex items-center justify-between">
              <span className="text-sm text-gray-600">Đã chọn: <b>{selected.size}</b></span>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded"
                  disabled={submitting}
                >
                  Hủy
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded disabled:opacity-50"
                >
                  {submitting ? 'Đang lưu...' : 'Lưu phân công'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
