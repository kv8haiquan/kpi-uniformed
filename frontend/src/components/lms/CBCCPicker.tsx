/**
 * src/components/lms/CBCCPicker.tsx
 * ================================
 * Chọn CBCC cụ thể bằng autocomplete search (debounce 400ms).
 * Tách riêng để dùng chung cho giao bài khóa học (mode "Theo CBCC cụ thể").
 */

'use client';

import { useEffect, useState, useRef } from 'react';
import { cbccApi } from '@/services/lms';

export interface ICBCCItem {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string | null;
  don_vi_ten: string | null;
}

interface CBCCPickerProps {
  selected: ICBCCItem[];
  onAdd: (cc: ICBCCItem) => void;
  onRemove: (id: string) => void;
}

export default function CBCCPicker({ selected, onAdd, onRemove }: CBCCPickerProps) {
  const [query, setQuery]     = useState('');
  const [results, setResults] = useState<ICBCCItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen]       = useState(false);
  const debounceRef           = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef              = useRef<HTMLInputElement>(null);

  // Tìm kiếm CBCC với debounce 400ms
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!query.trim() || query.length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await cbccApi.searchCBCC({ q: query, page_size: 12 });
        setResults(res.data.data || []);
        setOpen(true);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 400);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  const handleAdd = (cc: ICBCCItem) => {
    onAdd(cc);
    setQuery('');
    setOpen(false);
    setResults([]);
    inputRef.current?.focus();
  };

  const showDropdown = open && query.length >= 2;

  return (
    <div>
      {/* Chips CBCC đã chọn */}
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {selected.map((cc) => (
            <span
              key={cc.id}
              className="inline-flex items-center gap-1.5 pl-2.5 pr-1.5 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium border border-green-200"
            >
              <span>👤</span>
              <span>{cc.ho_ten}</span>
              <span className="font-mono text-[10px] text-green-600">({cc.ma_cc})</span>
              <button
                onClick={() => onRemove(cc.id)}
                className="ml-0.5 w-4 h-4 flex items-center justify-center rounded-full hover:bg-green-200 text-green-700 font-bold text-sm leading-none"
                title="Xóa"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Input tìm kiếm */}
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Tìm theo tên hoặc mã công chức (VD: Nguyễn, HQ001)..."
          className={`w-full px-3 py-2 pr-9 border rounded-lg text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            showDropdown ? 'border-blue-400' : 'border-gray-300'
          }`}
        />
        {/* Spinner */}
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Overlay đóng dropdown */}
        {showDropdown && (
          <div className="fixed inset-0 z-20" onClick={() => setOpen(false)} />
        )}

        {/* Dropdown kết quả */}
        {showDropdown && (
          <div className="absolute z-30 top-full mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-xl max-h-56 overflow-y-auto py-1">
            {results.length === 0 && !loading ? (
              <p className="px-3 py-3 text-sm text-gray-400 text-center">
                Không tìm thấy CBCC phù hợp
              </p>
            ) : (
              results.map((cc) => {
                const daChon = selected.some((s) => s.id === cc.id);
                return (
                  <div
                    key={cc.id}
                    onClick={() => !daChon && handleAdd(cc)}
                    className={`px-3 py-2.5 flex items-start gap-3 ${
                      daChon
                        ? 'opacity-50 cursor-not-allowed bg-gray-50'
                        : 'cursor-pointer hover:bg-blue-50'
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">
                        {cc.ho_ten}
                        {daChon && (
                          <span className="ml-1.5 text-xs text-gray-400 font-normal">(đã chọn)</span>
                        )}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        <span className="font-mono">{cc.ma_cc}</span>
                        {cc.chuc_vu && <span> · {cc.chuc_vu}</span>}
                        {cc.don_vi_ten && <span> · {cc.don_vi_ten}</span>}
                      </p>
                    </div>
                    {!daChon && (
                      <span className="text-blue-500 text-xs shrink-0 pt-0.5">+ Thêm</span>
                    )}
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>

      {selected.length === 0 && (
        <p className="text-xs text-gray-400 mt-2">
          Nhập ít nhất 2 ký tự để tìm kiếm · Nhấn vào tên để thêm vào danh sách
        </p>
      )}
    </div>
  );
}
