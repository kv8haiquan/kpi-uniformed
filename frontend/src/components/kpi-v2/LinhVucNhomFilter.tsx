'use client';

/**
 * components/kpi-v2/LinhVucNhomFilter.tsx
 * =======================================
 * Filter combo cho V2_PL3: chọn lĩnh vực + công tác + nhiệm vụ + keyword search.
 *
 * Decision Phase D câu 2: SKIP "lĩnh vực gợi ý" (chưa có endpoint
 * don-vi/{id}/linh-vuc-mac-dinh) — chỉ hiển thị 15 lĩnh vực thông thường.
 */

import { useEffect, useState } from 'react';
import { Search } from 'lucide-react';

import { kpiV2Service } from '@/services/kpi-v2.service';
import { ICongTac, ILinhVuc } from '@/types/kpi-v2';

import { NhiemVuCombobox } from './NhiemVuCombobox';

/**
 * cong_tac value semantics:
 *   - undefined → không filter công tác (lấy toàn bộ lĩnh vực)
 *   - "__null__" → chỉ lấy nhóm "Chung" (cong_tac IS NULL trong DB)
 *   - tên cụ thể → exact match
 */
export interface ILinhVucNhomValue {
  linh_vuc?: string;
  cong_tac?: string;
  nhiem_vu?: string;
  search?: string;
}

interface Props {
  value: ILinhVucNhomValue;
  onChange: (value: ILinhVucNhomValue) => void;
  className?: string;
}

export function LinhVucNhomFilter({ value, onChange, className }: Props) {
  const [linhVucList, setLinhVucList] = useState<ILinhVuc[]>([]);
  const [loadingLV, setLoadingLV] = useState(true);
  const [congTacList, setCongTacList] = useState<ICongTac[]>([]);
  const [loadingCT, setLoadingCT] = useState(false);

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

  // Load công tác mỗi khi đổi lĩnh vực
  useEffect(() => {
    if (!value.linh_vuc) {
      setCongTacList([]);
      return;
    }
    let mounted = true;
    setLoadingCT(true);
    kpiV2Service
      .getCongTac(value.linh_vuc)
      .then((data) => {
        if (mounted) setCongTacList(data);
      })
      .catch(() => {
        if (mounted) setCongTacList([]);
      })
      .finally(() => {
        if (mounted) setLoadingCT(false);
      });
    return () => {
      mounted = false;
    };
  }, [value.linh_vuc]);

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
            // Đổi lĩnh vực → reset cong_tac + nhiem_vu (mục cũ không còn hợp lệ)
            onChange({
              ...value,
              linh_vuc: next,
              cong_tac: undefined,
              nhiem_vu: undefined,
            });
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

      {/* Công tác — sub-heading giữa Lĩnh vực và Nhiệm vụ */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Công tác
          {value.linh_vuc && !loadingCT && (
            <span className="ml-1 text-xs font-normal text-gray-500">
              ({congTacList.length} công tác)
            </span>
          )}
        </label>
        <select
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none disabled:bg-gray-100"
          value={value.cong_tac ?? ''}
          onChange={(e) => {
            const raw = e.target.value;
            // '' → undefined (Tất cả công tác); '__null__' giữ nguyên (nhóm Chung)
            const next = raw === '' ? undefined : raw;
            onChange({ ...value, cong_tac: next, nhiem_vu: undefined });
          }}
          disabled={!value.linh_vuc || loadingCT}
        >
          <option value="">
            {!value.linh_vuc
              ? '— Chọn lĩnh vực trước —'
              : '— Tất cả công tác —'}
          </option>
          {value.linh_vuc && (
            <option value="__null__">(Chung — chưa phân công tác)</option>
          )}
          {congTacList.map((ct) => (
            <option key={ct.cong_tac} value={ct.cong_tac}>
              {ct.thu_tu ? `${ct.thu_tu}. ` : ''}
              {ct.cong_tac}
            </option>
          ))}
        </select>
      </div>

      {/* Nhiệm vụ — combobox có search, disable nếu chưa chọn lĩnh vực */}
      <NhiemVuCombobox
        linhVuc={value.linh_vuc}
        congTac={value.cong_tac}
        value={value.nhiem_vu}
        onChange={(nv) => onChange({ ...value, nhiem_vu: nv })}
      />

      {/* Search keyword */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Tìm kiếm
        </label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Gõ để tìm trong tên / chi tiết / đầu ra…"
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
