/**
 * CongChucCheckboxList — checkbox grid của CBCC trong 1 đơn vị.
 *
 * G4-fix-3 (01/05/2026): cho form tạo cuộc họp pick thành phần nhanh trong
 * đơn vị tổ chức. Auto-disable + auto-check chu_toa_id và thu_ky_id (props).
 *
 * UX:
 * - Đổi `donViId` → re-fetch list
 * - "Chọn tất cả" toggle
 * - chu_toa/thu_ky luôn check + disable (không bỏ được — tránh lỡ tay)
 * - Scrollable container max-h-80 cho đơn vị lớn
 */

'use client';

import { useEffect, useMemo, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { congChucApi, type ICongChucSearchItem } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';

export interface ICongChucCheckboxListProps {
  /** UUID đơn vị — null/empty thì hiển thị placeholder. */
  donViId?: string | null;
  /** UUIDs đã được tick. */
  value: string[];
  onChange: (ids: string[]) => void;
  /** UUID chu_toa — auto check + disable nếu trùng. */
  chuToaId?: string | null;
  /** UUID thu_ky — auto check + disable nếu trùng. */
  thuKyId?: string | null;
  /** Disable toàn bộ. */
  disabled?: boolean;
  /**
   * UUIDs đã "khóa" — hiển thị tick + disabled, KHÔNG nằm trong `value`
   * và không bị thêm vào khi "Chọn tất cả". Dùng cho case CBCC đã có trong
   * nhóm thành phần — báo hiệu cho user biết khỏi tick lại.
   */
  lockedIds?: Set<string>;
  /** Suffix hiển thị cạnh entry locked (vd: "(đã trong nhóm)"). */
  lockedLabel?: string;
}

export default function CongChucCheckboxList({
  donViId,
  value,
  onChange,
  chuToaId,
  thuKyId,
  disabled,
  lockedIds,
  lockedLabel,
}: ICongChucCheckboxListProps) {
  const [items, setItems] = useState<ICongChucSearchItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Set của UUIDs auto (chu_toa + thu_ky) — luôn check, disable
  const autoIds = useMemo(() => {
    const s = new Set<string>();
    if (chuToaId) s.add(chuToaId);
    if (thuKyId) s.add(thuKyId);
    return s;
  }, [chuToaId, thuKyId]);

  // Auto-include chu_toa + thu_ky vào value (đảm bảo state nhất quán)
  useEffect(() => {
    const merged = new Set(value);
    let changed = false;
    if (chuToaId && !merged.has(chuToaId)) {
      merged.add(chuToaId);
      changed = true;
    }
    if (thuKyId && !merged.has(thuKyId)) {
      merged.add(thuKyId);
      changed = true;
    }
    if (changed) onChange(Array.from(merged));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chuToaId, thuKyId]);

  // Load CBCC theo đơn vị
  useEffect(() => {
    if (!donViId) {
      setItems([]);
      return;
    }
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await congChucApi.search({ don_vi_id: donViId, limit: 200 });
        if (!cancelled) setItems(data);
      } catch (e: unknown) {
        if (!cancelled) setError(errMsg(e, 'Lỗi tải CBCC đơn vị'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [donViId]);

  if (!donViId) {
    return (
      <div className="p-4 border-2 border-dashed rounded text-sm text-gray-500 text-center bg-gray-50">
        Chọn đơn vị tổ chức trước để hiển thị danh sách CBCC.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-4 flex items-center gap-2 text-gray-600 text-sm border rounded bg-white">
        <Loader2 className="w-4 h-4 animate-spin" /> Đang tải CBCC đơn vị...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-3 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
        {error}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500 text-sm border rounded bg-white">
        Đơn vị này chưa có CBCC active.
      </div>
    );
  }

  const valueSet = new Set(value);
  const lockSet = lockedIds ?? new Set<string>();

  // Items có thể tick (loại trừ locked); dùng để tính allSelected
  const togglableItems = items.filter((it) => !lockSet.has(it.id));
  const allSelected =
    togglableItems.length > 0 && togglableItems.every((it) => valueSet.has(it.id));
  const someSelected = togglableItems.some((it) => valueSet.has(it.id));

  const toggleAll = () => {
    if (allSelected) {
      // Bỏ tất cả TRỪ auto (chu_toa/thu_ky); locked không trong value nên skip
      const kept = value.filter(
        (id) => autoIds.has(id) || !togglableItems.find((it) => it.id === id),
      );
      onChange(kept);
    } else {
      // Tick tất cả togglable + giữ value cũ ngoài đơn vị
      const merged = new Set(value);
      togglableItems.forEach((it) => merged.add(it.id));
      onChange(Array.from(merged));
    }
  };

  const toggleOne = (id: string) => {
    if (autoIds.has(id) || lockSet.has(id)) return; // disabled
    const next = new Set(value);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onChange(Array.from(next));
  };

  return (
    <div className="border rounded bg-white">
      {/* Header với select all */}
      <div className="flex items-center justify-between px-3 py-2 border-b bg-gray-50">
        <label className="inline-flex items-center gap-2 text-sm font-medium cursor-pointer">
          <input
            type="checkbox"
            checked={allSelected}
            ref={(el) => {
              if (el) el.indeterminate = !allSelected && someSelected;
            }}
            onChange={toggleAll}
            disabled={disabled || togglableItems.length === 0}
            className="w-4 h-4"
          />
          Chọn tất cả ({togglableItems.length} CBCC{lockSet.size > 0 ? ` · ${lockSet.size} đã có` : ''})
        </label>
        <span className="text-xs text-gray-500">
          Đã chọn {togglableItems.filter((it) => valueSet.has(it.id)).length}/{togglableItems.length}
        </span>
      </div>

      {/* Grid checkbox */}
      <div className="max-h-80 overflow-y-auto p-2 space-y-1">
        {items.map((it) => {
          const isLocked = lockSet.has(it.id);
          const isAuto = autoIds.has(it.id);
          const checked = valueSet.has(it.id) || isLocked;
          const autoLabel =
            it.id === chuToaId
              ? ' (Chủ tọa)'
              : it.id === thuKyId
                ? ' (Thư ký)'
                : isLocked && lockedLabel
                  ? ` ${lockedLabel}`
                  : '';
          return (
            <label
              key={it.id}
              className={`flex items-center gap-2 px-2 py-1.5 rounded text-sm cursor-pointer ${
                isAuto ? 'bg-blue-50' : isLocked ? 'bg-gray-100' : 'hover:bg-gray-50'
              } ${disabled || isLocked ? 'opacity-70 cursor-not-allowed' : ''}`}
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={() => toggleOne(it.id)}
                disabled={disabled || isAuto || isLocked}
                className="w-4 h-4"
              />
              <span className={`flex-1 ${it.is_lanh_dao ? 'font-medium' : ''}`}>
                {it.ho_ten}{' '}
                <span className="text-xs text-gray-500">
                  ({it.ma_cc}{it.chuc_vu ? ` · ${it.chuc_vu}` : ''}){autoLabel}
                </span>
              </span>
            </label>
          );
        })}
      </div>
    </div>
  );
}
