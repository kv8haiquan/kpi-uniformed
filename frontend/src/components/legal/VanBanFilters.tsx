/**
 * src/components/legal/VanBanFilters.tsx
 * =========================================
 * Bộ lọc danh sách văn bản pháp luật.
 *
 * Fields:
 *   - search: Tìm kiếm toàn văn (số hiệu, trích yếu)
 *   - loaiVanBanId: Lọc theo loại VB (dropdown)
 *   - trangThaiHieuLuc: Lọc theo hiệu lực
 *   - mucDo: Lọc theo mức độ khẩn
 *   - sapXep: Sắp xếp mới nhất / quan trọng nhất
 */

'use client';

import type { ILoaiVanBan } from '@/types/legal';

export interface LegalFilterState {
  search: string;
  loaiVanBanId: string;
  trangThaiHieuLuc: string;
  mucDo: string;
  sapXep: string;
}

interface VanBanFiltersProps {
  loaiVanBans: ILoaiVanBan[];
  filters: LegalFilterState;
  onFilterChange: (filters: LegalFilterState) => void;
}

export const DEFAULT_FILTERS: LegalFilterState = {
  search: '',
  loaiVanBanId: '',
  trangThaiHieuLuc: '',
  mucDo: '',
  sapXep: 'moi_nhat',
};

export function VanBanFilters({ loaiVanBans, filters, onFilterChange }: VanBanFiltersProps) {
  const update = (key: keyof LegalFilterState, value: string) => {
    onFilterChange({ ...filters, [key]: value });
  };

  const hasFilter =
    filters.search ||
    filters.loaiVanBanId ||
    filters.trangThaiHieuLuc ||
    filters.mucDo ||
    filters.sapXep !== 'moi_nhat';

  const clearAll = () => onFilterChange(DEFAULT_FILTERS);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {/* Tìm kiếm — chiếm 2 cột */}
        <div className="sm:col-span-2">
          <input
            type="text"
            placeholder="🔍 Tìm số hiệu, trích yếu, nội dung..."
            value={filters.search}
            onChange={e => update('search', e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent"
          />
        </div>

        {/* Loại VB */}
        <select
          value={filters.loaiVanBanId}
          onChange={e => update('loaiVanBanId', e.target.value)}
          className="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 bg-white"
        >
          <option value="">📋 Loại văn bản</option>
          {loaiVanBans.map(l => (
            <option key={l.id} value={l.id}>{l.ten}</option>
          ))}
        </select>

        {/* Hiệu lực */}
        <select
          value={filters.trangThaiHieuLuc}
          onChange={e => update('trangThaiHieuLuc', e.target.value)}
          className="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 bg-white"
        >
          <option value="">⚖️ Hiệu lực</option>
          <option value="CON_HIEU_LUC">✅ Còn hiệu lực</option>
          <option value="HET_HIEU_LUC">⛔ Hết hiệu lực</option>
          <option value="CHUA_HIEU_LUC">⏳ Chưa hiệu lực</option>
        </select>

        {/* Mức độ */}
        <select
          value={filters.mucDo}
          onChange={e => update('mucDo', e.target.value)}
          className="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 bg-white"
        >
          <option value="">🎯 Mức độ</option>
          <option value="RAT_KHAN">🔴 Rất khẩn</option>
          <option value="KHAN">🟠 Khẩn</option>
          <option value="QUAN_TRONG">🟡 Quan trọng</option>
          <option value="BINH_THUONG">Bình thường</option>
        </select>
      </div>

      {/* Row 2: sắp xếp + xóa bộ lọc */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Sắp xếp:</span>
          <button
            onClick={() => update('sapXep', 'moi_nhat')}
            className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
              filters.sapXep === 'moi_nhat'
                ? 'bg-purple-100 text-purple-700 border-purple-200'
                : 'bg-white text-gray-500 border-gray-200 hover:border-purple-200'
            }`}
          >
            🕐 Mới nhất
          </button>
          <button
            onClick={() => update('sapXep', 'quan_trong')}
            className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
              filters.sapXep === 'quan_trong'
                ? 'bg-purple-100 text-purple-700 border-purple-200'
                : 'bg-white text-gray-500 border-gray-200 hover:border-purple-200'
            }`}
          >
            🎯 Quan trọng
          </button>
        </div>

        {hasFilter && (
          <button
            onClick={clearAll}
            className="text-xs text-gray-400 hover:text-red-600 underline transition-colors"
          >
            ✕ Xóa bộ lọc
          </button>
        )}
      </div>
    </div>
  );
}
