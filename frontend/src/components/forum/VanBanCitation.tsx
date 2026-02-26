'use client';

/**
 * VanBanCitation.tsx
 * ==================
 * Component quan ly can cu phap ly (van ban/SOP) cho chu de hoac tra loi.
 * Cho phep them/xoa can cu phap ly thong qua form input don gian.
 */

import { Plus, Trash2 } from 'lucide-react';
import type { ICanCuPhapLy } from '@/types/forum';

interface VanBanCitationProps {
  citations: ICanCuPhapLy[];
  onChange: (citations: ICanCuPhapLy[]) => void;
}

export default function VanBanCitation({
  citations,
  onChange,
}: VanBanCitationProps) {
  // Them can cu phap ly moi
  const handleAddCitation = () => {
    const newCitation: ICanCuPhapLy = {
      loai: 'VAN_BAN',
      id: `temp-${Date.now()}`, // Temporary ID, backend se generate ID moi
      trich_dan: '',
    };

    onChange([...citations, newCitation]);
  };

  // Cap nhat loai (VAN_BAN/SOP)
  const handleUpdateType = (index: number, loai: 'VAN_BAN' | 'SOP') => {
    const updated = [...citations];
    updated[index] = { ...updated[index], loai };
    onChange(updated);
  };

  // Cap nhat trich dan
  const handleUpdateTrichDan = (index: number, trich_dan: string) => {
    const updated = [...citations];
    updated[index] = { ...updated[index], trich_dan };
    onChange(updated);
  };

  // Xoa can cu phap ly
  const handleRemoveCitation = (index: number) => {
    const updated = citations.filter((_, i) => i !== index);
    onChange(updated);
  };

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700">
          Can cu phap ly
        </label>
        <button
          onClick={handleAddCitation}
          className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md transition-colors"
        >
          <Plus className="w-4 h-4" />
          Them can cu phap ly
        </button>
      </div>

      {/* Danh sach can cu phap ly */}
      {citations.length === 0 ? (
        <div className="text-sm text-gray-500 text-center py-4 border border-dashed border-gray-300 rounded-md">
          Chua co can cu phap ly nao. Nhan "Them can cu phap ly" de them.
        </div>
      ) : (
        <div className="space-y-3">
          {citations.map((citation, index) => (
            <div
              key={`${citation.id}-${index}`}
              className="flex gap-3 items-start p-3 bg-gray-50 border border-gray-200 rounded-md"
            >
              {/* Select loai */}
              <select
                value={citation.loai}
                onChange={(e) =>
                  handleUpdateType(index, e.target.value as 'VAN_BAN' | 'SOP')
                }
                className="flex-shrink-0 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="VAN_BAN">Van ban</option>
                <option value="SOP">SOP</option>
              </select>

              {/* Input trich dan */}
              <input
                type="text"
                value={citation.trich_dan}
                onChange={(e) => handleUpdateTrichDan(index, e.target.value)}
                placeholder="Nhap trich dan (VD: Thong tu 38/2015/TT-BTC dieu 5 khoan 2)"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />

              {/* Nut xoa */}
              <button
                onClick={() => handleRemoveCitation(index)}
                className="flex-shrink-0 p-2 text-red-600 hover:bg-red-50 rounded-md transition-colors"
                aria-label="Xoa can cu phap ly"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Badges hien thi danh sach */}
      {citations.length > 0 && citations.some((c) => c.trich_dan.trim()) && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
          <div className="text-sm font-medium text-blue-900 mb-2">
            Can cu phap ly da nhap:
          </div>
          <div className="flex flex-wrap gap-2">
            {citations
              .filter((c) => c.trich_dan.trim())
              .map((citation, index) => (
                <span
                  key={`badge-${citation.id}-${index}`}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium"
                >
                  <span className="font-semibold">
                    [{citation.loai === 'VAN_BAN' ? 'VB' : 'SOP'}]
                  </span>
                  {citation.trich_dan}
                </span>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
