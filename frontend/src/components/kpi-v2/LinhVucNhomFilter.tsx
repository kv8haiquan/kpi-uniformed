'use client';

/**
 * components/kpi-v2/LinhVucNhomFilter.tsx
 * =======================================
 * Filter combo cho V2_PL3: chọn lĩnh vực + nhóm + keyword search.
 *
 * Decision Phase D câu 2: SKIP "lĩnh vực gợi ý" (chưa có endpoint
 * don-vi/{id}/linh-vuc-mac-dinh) — chỉ hiển thị 15 lĩnh vực thông thường.
 */

import { useEffect, useState } from 'react';
import { Search } from 'lucide-react';

import { kpiV2Service } from '@/services/kpi-v2.service';
import { ILinhVuc } from '@/types/kpi-v2';

import { NhiemVuCombobox } from './NhiemVuCombobox';

export interface ILinhVucNhomValue {
  linh_vuc?: string;
  nhiem_vu?: string;
  nhom_pl3?: number;
  search?: string;
}

interface Props {
  value: ILinhVucNhomValue;
  onChange: (value: ILinhVucNhomValue) => void;
  className?: string;
}

const NHOM_OPTIONS = [
  { value: undefined, label: 'Tất cả' },
  { value: 1, label: 'Nhóm 1' },
  { value: 2, label: 'Nhóm 2' },
  { value: 3, label: 'Nhóm 3' },
  { value: 4, label: 'Nhóm 4' },
  { value: 5, label: 'Nhóm 5' },
];

export function LinhVucNhomFilter({ value, onChange, className }: Props) {
  const [linhVucList, setLinhVucList] = useState<ILinhVuc[]>([]);
  const [loadingLV, setLoadingLV] = useState(true);

  useEffect(() => {
    let mounted = true;
    setLoadingLV(true);
    kpiV2Service
      .getLinhVuc()
      .then((data) => {
        if (mounted) setLinhVucList(data);
      })
      .catch((err) => console.error('Error loading lĩnh vực', err))
      .finally(() => {
        if (mounted) setLoadingLV(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className={`space-y-3 ${className ?? ''}`}>
      {/* Lĩnh vực */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Lĩnh vực
        </label>
        <select
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none disabled:bg-gray-100"
          value={value.linh_vuc ?? ''}
          onChange={(e) => {
            const next = e.target.value || undefined;
            // Đổi lĩnh vực → reset nhiem_vu (mục cũ không còn hợp lệ)
            onChange({ ...value, linh_vuc: next, nhiem_vu: undefined });
          }}
          disabled={loadingLV}
        >
          <option value="">— Tất cả 15 lĩnh vực —</option>
          {linhVucList.map((lv) => (
            <option key={lv.ma} value={lv.ma}>
              {lv.ma}. {lv.ten}
            </option>
          ))}
        </select>
      </div>

      {/* Nhiệm vụ — combobox có search, disable nếu chưa chọn lĩnh vực */}
      <NhiemVuCombobox
        linhVuc={value.linh_vuc}
        value={value.nhiem_vu}
        onChange={(nv) => onChange({ ...value, nhiem_vu: nv })}
      />

      {/* Nhóm chip filter */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Nhóm</label>
        <div className="flex flex-wrap gap-2">
          {NHOM_OPTIONS.map((opt) => {
            const active = value.nhom_pl3 === opt.value;
            return (
              <button
                key={String(opt.value)}
                type="button"
                onClick={() => onChange({ ...value, nhom_pl3: opt.value })}
                className={[
                  'px-3 py-1.5 rounded-full text-xs font-medium border transition',
                  active
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50',
                ].join(' ')}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Search keyword */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Tìm kiếm
        </label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Gõ để tìm trong tên / chi tiết / sản phẩm…"
            className="w-full rounded-md border border-gray-300 pl-9 pr-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            value={value.search ?? ''}
            onChange={(e) =>
              onChange({ ...value, search: e.target.value || undefined })
            }
          />
        </div>
      </div>
    </div>
  );
}
