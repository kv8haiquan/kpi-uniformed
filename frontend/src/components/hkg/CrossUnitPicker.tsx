/**
 * CrossUnitPicker — thêm CBCC từ đơn vị KHÁC (không phải đơn vị tổ chức).
 *
 * 03/05/2026: bỏ rào "phải chọn đơn vị trước".
 * - Search box LUÔN hiển thị: gõ ≥ 2 ký tự → server search (q toàn Chi cục).
 * - Đơn vị dropdown trở thành filter tuỳ chọn — chọn để browse 200 CBCC đơn vị.
 * - CBCC thuộc đơn vị tổ chức (`excludeDonViId`) bị loại tại client (đã có
 *   ở CongChucCheckboxList rồi).
 *
 * State được quản lý dưới dạng `entries: ICongChucSearchItem[]` (hydrated)
 * thay vì chỉ ID → parent display thoải mái không cần cache riêng.
 */

'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Loader2, Search, X } from 'lucide-react';
import { congChucApi, type ICongChucSearchItem } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';

const SEARCH_DEBOUNCE_MS = 300;
const MIN_SEARCH_CHARS = 2;

interface IDonVi {
  id: string;
  ma_don_vi: string;
  ten_don_vi: string;
}

export interface ICrossUnitPickerProps {
  /** Danh sách đơn vị (đã load ở parent từ /lms/don-vi). */
  donViList: IDonVi[];
  /** UUID đơn vị tổ chức — sẽ ẩn khỏi dropdown + loại khỏi kết quả search. */
  excludeDonViId?: string | null;
  /** CBCC đã chọn — entries hydrated. */
  entries: ICongChucSearchItem[];
  /** Callback khi list thay đổi. */
  onChange: (entries: ICongChucSearchItem[]) => void;
  /** Disable toàn bộ. */
  disabled?: boolean;
}

export default function CrossUnitPicker({
  donViList,
  excludeDonViId,
  entries,
  onChange,
  disabled,
}: ICrossUnitPickerProps) {
  const [selectedDonViId, setSelectedDonViId] = useState<string>('');
  const [items, setItems] = useState<ICongChucSearchItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  // Đơn vị dropdown (loại trừ đơn vị tổ chức)
  const dvOptions = useMemo(
    () => donViList.filter((dv) => dv.id !== excludeDonViId),
    [donViList, excludeDonViId],
  );

  // Khi đổi excludeDonViId, nếu đang chọn đơn vị bị exclude → reset
  useEffect(() => {
    if (selectedDonViId && selectedDonViId === excludeDonViId) {
      setSelectedDonViId('');
      setItems([]);
    }
  }, [excludeDonViId, selectedDonViId]);

  // Server fetch — debounced. Chạy khi:
  //  - query >= MIN_SEARCH_CHARS (server search, optional filter đơn vị)
  //  - hoặc đơn vị được chọn nhưng query < MIN (browse list đơn vị)
  // Còn lại → clear list.
  useEffect(() => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current);

    const trimmed = query.trim();
    const useQuery = trimmed.length >= MIN_SEARCH_CHARS;
    const browseDonVi = !useQuery && !!selectedDonViId;

    if (!useQuery && !browseDonVi) {
      setItems([]);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    debounceTimer.current = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await congChucApi.search({
          q: useQuery ? trimmed : undefined,
          don_vi_id: selectedDonViId || undefined,
          limit: browseDonVi ? 200 : 50,
        });
        if (cancelled) return;
        // Loại CBCC thuộc đơn vị tổ chức — đã có ở CongChucCheckboxList
        const filtered = excludeDonViId
          ? data.filter((it) => it.don_vi_id !== excludeDonViId)
          : data;
        setItems(filtered);
      } catch (e: unknown) {
        if (!cancelled) setError(errMsg(e, 'Lỗi tìm CBCC'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, useQuery ? SEARCH_DEBOUNCE_MS : 0);

    return () => {
      cancelled = true;
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
    };
  }, [query, selectedDonViId, excludeDonViId]);

  const selectedIds = useMemo(() => new Set(entries.map((e) => e.id)), [entries]);

  const toggleOne = (it: ICongChucSearchItem) => {
    if (disabled) return;
    if (selectedIds.has(it.id)) {
      onChange(entries.filter((e) => e.id !== it.id));
    } else {
      onChange([...entries, it]);
    }
  };

  const removeOne = (id: string) => {
    if (disabled) return;
    onChange(entries.filter((e) => e.id !== id));
  };

  const allShownSelected =
    items.length > 0 && items.every((it) => selectedIds.has(it.id));
  const someShownSelected = items.some((it) => selectedIds.has(it.id));

  const toggleAllShown = () => {
    if (disabled || items.length === 0) return;
    if (allShownSelected) {
      const ids = new Set(items.map((it) => it.id));
      onChange(entries.filter((e) => !ids.has(e.id)));
    } else {
      const map = new Map(entries.map((e) => [e.id, e] as const));
      items.forEach((it) => map.set(it.id, it));
      onChange(Array.from(map.values()));
    }
  };

  const trimmed = query.trim();
  const queryActive = trimmed.length >= MIN_SEARCH_CHARS;
  const browseMode = !queryActive && !!selectedDonViId;
  const needsMoreChars = trimmed.length > 0 && !queryActive;
  const idleEmpty = !queryActive && !selectedDonViId;

  return (
    <div className="space-y-2 border rounded p-3 bg-gray-50">
      {/* Tags row — luôn hiển thị (không phụ thuộc đơn vị đang chọn) */}
      {entries.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {entries.map((e) => (
            <span
              key={e.id}
              className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
            >
              {e.ho_ten} ({e.ma_cc})
              {e.ten_don_vi ? <span className="text-blue-600"> · {e.ten_don_vi}</span> : null}
              <button
                type="button"
                onClick={() => removeOne(e.id)}
                className="hover:text-blue-900"
                disabled={disabled}
                aria-label={`Bỏ ${e.ho_ten}`}
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Search box — luôn hiển thị, server search khi >=2 ký tự */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={query}
          onChange={(ev) => setQuery(ev.target.value)}
          placeholder="Tìm CBCC theo tên hoặc mã (mọi đơn vị)..."
          disabled={disabled}
          className="w-full pl-9 pr-3 py-2 border rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white"
        />
        {loading && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-gray-400" />
        )}
      </div>

      {/* Đơn vị dropdown — filter tuỳ chọn */}
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Lọc theo đơn vị (tuỳ chọn)
        </label>
        <select
          value={selectedDonViId}
          onChange={(ev) => setSelectedDonViId(ev.target.value)}
          disabled={disabled}
          className="w-full px-3 py-2 border rounded text-sm bg-white"
        >
          <option value="">— Mọi đơn vị —</option>
          {dvOptions.map((dv) => (
            <option key={dv.id} value={dv.id}>
              {dv.ma_don_vi} — {dv.ten_don_vi}
            </option>
          ))}
        </select>
      </div>

      {/* Result list */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
          {error}
        </div>
      )}

      {!error && idleEmpty && (
        <div className="p-3 text-center text-gray-500 text-sm bg-white border rounded">
          Gõ ≥ {MIN_SEARCH_CHARS} ký tự (tên / mã CBCC) hoặc chọn đơn vị để xem danh sách.
        </div>
      )}

      {!error && needsMoreChars && !selectedDonViId && (
        <div className="p-3 text-center text-gray-500 text-sm bg-white border rounded">
          Gõ thêm để tìm (ít nhất {MIN_SEARCH_CHARS} ký tự).
        </div>
      )}

      {!error && (queryActive || browseMode) && !loading && items.length === 0 && (
        <div className="p-3 text-center text-gray-500 text-sm bg-white border rounded">
          {queryActive ? 'Không có CBCC khớp tìm kiếm.' : 'Đơn vị này chưa có CBCC active.'}
        </div>
      )}

      {!error && items.length > 0 && (
        <div className="border rounded bg-white">
          <div className="flex items-center justify-between px-3 py-2 border-b bg-gray-50">
            <label className="inline-flex items-center gap-2 text-xs font-medium cursor-pointer">
              <input
                type="checkbox"
                checked={allShownSelected}
                ref={(el) => {
                  if (el) el.indeterminate = !allShownSelected && someShownSelected;
                }}
                onChange={toggleAllShown}
                disabled={disabled}
                className="w-4 h-4"
              />
              Chọn tất cả ({items.length})
            </label>
            <span className="text-xs text-gray-500">
              Đã chọn {items.filter((it) => selectedIds.has(it.id)).length}/{items.length}
            </span>
          </div>
          <div className="max-h-64 overflow-y-auto p-2 space-y-1">
            {items.map((it) => {
              const checked = selectedIds.has(it.id);
              return (
                <label
                  key={it.id}
                  className={`flex items-center gap-2 px-2 py-1.5 rounded text-sm cursor-pointer ${
                    checked ? 'bg-blue-50' : 'hover:bg-gray-50'
                  } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleOne(it)}
                    disabled={disabled}
                    className="w-4 h-4"
                  />
                  <span className={`flex-1 ${it.is_lanh_dao ? 'font-medium' : ''}`}>
                    {it.ho_ten}{' '}
                    <span className="text-xs text-gray-500">
                      ({it.ma_cc}
                      {it.chuc_vu ? ` · ${it.chuc_vu}` : ''})
                    </span>
                    {it.ten_don_vi && (
                      <span className="ml-1 text-xs text-gray-500">· {it.ten_don_vi}</span>
                    )}
                  </span>
                </label>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
