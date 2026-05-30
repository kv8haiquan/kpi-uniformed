/**
 * src/components/lms/DonViCongChucPicker.tsx
 * =========================================
 * Chọn CBCC "Theo đơn vị" kiểu ACCORDION (giống module HKG).
 * Dùng chung: giao bài (khóa học) + giao thí sinh (kỳ thi ĐGNL).
 *
 * - Tick nhiều đơn vị để chọn.
 * - Tick đơn vị nào → mặc định CHỌN SẴN toàn bộ CBCC của đơn vị đó.
 * - Mở rộng (accordion, chỉ 1 đơn vị mở tại một lúc) để BỎ CHỌN từng người.
 * - Có ô lọc + khung cuộn cho đơn vị lớn (đơn vị tới 135 người).
 *
 * Component tự quản lý state, báo ra ngoài danh sách cong_chuc_ids cuối cùng
 * (union các đơn vị đang tick, đã trừ người bỏ chọn) qua onChange.
 *
 * Reset: parent bump `key` để remount component (xoá sạch state nội bộ).
 */

'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { cbccApi } from '@/services/lms';

// =============================================================================
// TYPES
// =============================================================================

interface IDonVi {
  id: string;
  ma_don_vi?: string;
  ten_don_vi: string;
}

interface ICongChuc {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string | null;
  is_lanh_dao: boolean;
}

interface DonViCongChucPickerProps {
  donVis: IDonVi[];
  donViLoading: boolean;
  /** Báo ra danh sách cong_chuc_ids cuối cùng mỗi khi lựa chọn thay đổi. */
  onChange: (congChucIds: string[]) => void;
}

// =============================================================================
// COMPONENT
// =============================================================================

export default function DonViCongChucPicker({
  donVis,
  donViLoading,
  onChange,
}: DonViCongChucPickerProps) {
  // Đơn vị được tick để giao
  const [selectedDonViIds, setSelectedDonViIds] = useState<string[]>([]);
  // Danh sách người theo đơn vị (lazy-fetch, cache)
  const [membersByDv, setMembersByDv] = useState<Record<string, ICongChuc[]>>({});
  // Người được chọn trong từng đơn vị (Set cong_chuc_id)
  const [selectedByDv, setSelectedByDv] = useState<Record<string, Set<string>>>({});
  // Đơn vị đang mở accordion (chỉ 1)
  const [openDvId, setOpenDvId] = useState<string | null>(null);
  // Trạng thái tải / lỗi theo đơn vị
  const [loadingByDv, setLoadingByDv] = useState<Record<string, boolean>>({});
  const [errorByDv, setErrorByDv] = useState<Record<string, string>>({});
  // Ô lọc cho đơn vị đang mở
  const [filter, setFilter] = useState('');

  // Tránh fetch trùng cho cùng 1 đơn vị
  const fetchingRef = useRef<Set<string>>(new Set());

  // ── Tải danh sách người của 1 đơn vị (chỉ lần đầu) ──
  const fetchMembers = useCallback(
    async (dvId: string) => {
      if (membersByDv[dvId] || fetchingRef.current.has(dvId)) return;
      fetchingRef.current.add(dvId);
      setLoadingByDv((p) => ({ ...p, [dvId]: true }));
      setErrorByDv((p) => ({ ...p, [dvId]: '' }));
      try {
        const res = await cbccApi.congChucTheoDonVi(dvId);
        const list: ICongChuc[] = res.data.data || [];
        setMembersByDv((p) => ({ ...p, [dvId]: list }));
        // Mặc định CHỌN SẴN tất cả (chỉ set nếu chưa có)
        setSelectedByDv((p) =>
          p[dvId] ? p : { ...p, [dvId]: new Set(list.map((c) => c.id)) },
        );
      } catch (err: unknown) {
        const resp = (err as {
          response?: { data?: { detail?: { error?: { message?: string } }; error?: { message?: string } } };
        })?.response?.data;
        const msg =
          resp?.detail?.error?.message ||
          resp?.error?.message ||
          'Không tải được danh sách CBCC của đơn vị';
        setErrorByDv((p) => ({ ...p, [dvId]: msg }));
      } finally {
        setLoadingByDv((p) => ({ ...p, [dvId]: false }));
        fetchingRef.current.delete(dvId);
      }
    },
    [membersByDv],
  );

  // ── Tick / bỏ tick đơn vị ──
  const toggleDonVi = useCallback(
    (dvId: string) => {
      setSelectedDonViIds((prev) => {
        if (prev.includes(dvId)) {
          // Bỏ tick → đóng accordion nếu đang mở đơn vị này
          setOpenDvId((o) => (o === dvId ? null : o));
          return prev.filter((x) => x !== dvId);
        }
        // Tick → mở accordion + tải người (mặc định chọn tất cả)
        setOpenDvId(dvId);
        setFilter('');
        void fetchMembers(dvId);
        return [...prev, dvId];
      });
    },
    [fetchMembers],
  );

  // ── Mở / đóng accordion (chỉ 1 đơn vị mở) ──
  const toggleOpen = useCallback(
    (dvId: string) => {
      setOpenDvId((o) => {
        if (o === dvId) return null;
        setFilter('');
        void fetchMembers(dvId);
        return dvId;
      });
    },
    [fetchMembers],
  );

  // ── Bỏ chọn / chọn 1 người ──
  const toggleOne = useCallback((dvId: string, ccId: string) => {
    setSelectedByDv((prev) => {
      const cur = new Set(prev[dvId] ?? []);
      if (cur.has(ccId)) cur.delete(ccId);
      else cur.add(ccId);
      return { ...prev, [dvId]: cur };
    });
  }, []);

  // ── Chọn tất cả / bỏ tất cả người trong 1 đơn vị (toàn bộ, không theo filter) ──
  const toggleAll = useCallback(
    (dvId: string) => {
      const members = membersByDv[dvId] ?? [];
      setSelectedByDv((prev) => {
        const cur = prev[dvId] ?? new Set<string>();
        const allSelected = members.length > 0 && members.every((m) => cur.has(m.id));
        return {
          ...prev,
          [dvId]: allSelected ? new Set<string>() : new Set(members.map((m) => m.id)),
        };
      });
    },
    [membersByDv],
  );

  // ── Tính danh sách cong_chuc_ids cuối cùng & báo ra ngoài ──
  const finalIds = useMemo(() => {
    const ids = new Set<string>();
    selectedDonViIds.forEach((dv) => {
      (selectedByDv[dv] ?? new Set<string>()).forEach((id) => ids.add(id));
    });
    return Array.from(ids);
  }, [selectedDonViIds, selectedByDv]);

  useEffect(() => {
    onChange(finalIds);
  }, [finalIds, onChange]);

  const soDonViCoChon = selectedDonViIds.filter(
    (dv) => (selectedByDv[dv]?.size ?? 0) > 0,
  ).length;

  // ── Render ──
  if (donViLoading) {
    return (
      <div className="grid grid-cols-1 gap-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-11 bg-gray-100 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (donVis.length === 0) {
    return (
      <p className="text-sm text-gray-400 text-center py-6">
        Không thể tải danh sách đơn vị (kiểm tra LMS backend port 8001)
      </p>
    );
  }

  return (
    <div>
      <div className="space-y-2">
        {donVis.map((dv) => {
          const isSel = selectedDonViIds.includes(dv.id);
          const isOpen = openDvId === dv.id;
          const members = membersByDv[dv.id];
          const selSet = selectedByDv[dv.id];
          const selCount = selSet?.size ?? 0;
          const total = members?.length;
          const loading = loadingByDv[dv.id];
          const error = errorByDv[dv.id];

          return (
            <div
              key={dv.id}
              className={`rounded-lg border transition-colors ${
                isSel ? 'border-blue-400 bg-blue-50/40' : 'border-gray-200'
              }`}
            >
              {/* Hàng header đơn vị */}
              <div className="flex items-center gap-2 px-3 py-2.5">
                <label className="flex items-center gap-2.5 cursor-pointer select-none flex-1 min-w-0">
                  <input
                    type="checkbox"
                    checked={isSel}
                    onChange={() => toggleDonVi(dv.id)}
                    className="w-4 h-4 accent-blue-600 shrink-0"
                  />
                  <span
                    className={`text-sm font-medium truncate ${
                      isSel ? 'text-blue-900' : 'text-gray-700'
                    }`}
                  >
                    {dv.ten_don_vi}
                  </span>
                </label>

                {/* Nút mở rộng + đếm (chỉ khi đã tick) */}
                {isSel && (
                  <button
                    type="button"
                    onClick={() => toggleOpen(dv.id)}
                    className="flex items-center gap-1.5 shrink-0 text-xs text-blue-700 hover:text-blue-900 px-2 py-1 rounded-md hover:bg-blue-100/60"
                  >
                    <span className="font-medium tabular-nums">
                      {loading && total === undefined
                        ? 'đang tải…'
                        : `${selCount}/${total ?? '?'}`}
                    </span>
                    <span className="text-[10px]">{isOpen ? '▲ thu gọn' : '▼ chỉnh người'}</span>
                  </button>
                )}
              </div>

              {/* Thân accordion */}
              {isSel && isOpen && (
                <div className="border-t border-blue-200 px-3 py-2.5 space-y-2">
                  {error ? (
                    <p className="text-xs text-red-600 py-2">⛔ {error}</p>
                  ) : loading && !members ? (
                    <p className="text-xs text-gray-400 py-3 text-center">Đang tải danh sách CBCC…</p>
                  ) : members && members.length === 0 ? (
                    <p className="text-xs text-gray-400 py-3 text-center">
                      Đơn vị này chưa có CBCC active.
                    </p>
                  ) : members ? (
                    <MemberCheckboxList
                      members={members}
                      selected={selSet ?? new Set()}
                      filter={filter}
                      onFilterChange={setFilter}
                      onToggleOne={(id) => toggleOne(dv.id, id)}
                      onToggleAll={() => toggleAll(dv.id)}
                    />
                  ) : null}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Tóm tắt */}
      {finalIds.length > 0 && (
        <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-xs font-medium text-blue-700">
            Sẽ giao cho <strong>{finalIds.length}</strong> CBCC từ{' '}
            <strong>{soDonViCoChon}</strong> đơn vị.
          </p>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// SUB-COMPONENT: Danh sách checkbox người trong 1 đơn vị
// =============================================================================

interface MemberCheckboxListProps {
  members: ICongChuc[];
  selected: Set<string>;
  filter: string;
  onFilterChange: (v: string) => void;
  onToggleOne: (id: string) => void;
  onToggleAll: () => void;
}

function MemberCheckboxList({
  members,
  selected,
  filter,
  onFilterChange,
  onToggleOne,
  onToggleAll,
}: MemberCheckboxListProps) {
  const allSelected = members.length > 0 && members.every((m) => selected.has(m.id));
  const someSelected = members.some((m) => selected.has(m.id));

  const kw = filter.trim().toLowerCase();
  const visible = kw
    ? members.filter(
        (m) =>
          m.ho_ten.toLowerCase().includes(kw) || m.ma_cc.toLowerCase().includes(kw),
      )
    : members;

  return (
    <div>
      {/* Header: chọn tất cả + ô lọc */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <label className="inline-flex items-center gap-2 text-xs font-medium text-gray-700 cursor-pointer">
          <input
            type="checkbox"
            checked={allSelected}
            ref={(el) => {
              if (el) el.indeterminate = !allSelected && someSelected;
            }}
            onChange={onToggleAll}
            className="w-4 h-4 accent-blue-600"
          />
          Chọn tất cả ({members.length})
        </label>
        <span className="text-xs text-gray-500 tabular-nums">
          Đã chọn {members.filter((m) => selected.has(m.id)).length}/{members.length}
        </span>
      </div>

      {members.length > 8 && (
        <input
          type="text"
          value={filter}
          onChange={(e) => onFilterChange(e.target.value)}
          placeholder="Lọc theo tên hoặc mã CBCC…"
          className="w-full mb-2 px-2.5 py-1.5 text-sm border border-gray-200 rounded-md focus:outline-none focus:border-blue-400"
        />
      )}

      {/* Danh sách cuộn */}
      <div className="max-h-72 overflow-y-auto pr-0.5 space-y-0.5">
        {visible.length === 0 ? (
          <p className="text-xs text-gray-400 py-3 text-center">Không có CBCC khớp bộ lọc.</p>
        ) : (
          visible.map((m) => {
            const checked = selected.has(m.id);
            return (
              <label
                key={m.id}
                className={`flex items-center gap-2 px-2 py-1.5 rounded text-sm cursor-pointer ${
                  checked ? 'hover:bg-blue-50' : 'hover:bg-gray-50 opacity-90'
                }`}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => onToggleOne(m.id)}
                  className="w-4 h-4 accent-blue-600 shrink-0"
                />
                <span className={`flex-1 truncate ${m.is_lanh_dao ? 'font-medium' : ''}`}>
                  {m.ho_ten}{' '}
                  <span className="text-xs text-gray-500">
                    ({m.ma_cc}
                    {m.chuc_vu ? ` · ${m.chuc_vu}` : ''})
                  </span>
                </span>
              </label>
            );
          })
        )}
      </div>
    </div>
  );
}
