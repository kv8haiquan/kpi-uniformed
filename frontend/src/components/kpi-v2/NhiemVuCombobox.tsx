'use client';

/**
 * components/kpi-v2/NhiemVuCombobox.tsx
 * =====================================
 * Combobox có search cho cấp filter "Nhiệm vụ" (cột B Excel PL3).
 *
 * Hành vi:
 * - Bắt buộc có `linhVuc`. Nếu thiếu → render disabled với hint.
 * - Khi mount/đổi `linhVuc`: gọi GET /danh-muc/nhiem-vu?linh_vuc=...
 *   load toàn bộ list 1 lần, sau đó filter local theo keyword.
 * - Click input → mở dropdown; gõ → filter; chọn item → đóng + emit value.
 * - Có nút (x) để xoá lựa chọn.
 *
 * Tại sao không debounce server-side? Mỗi lĩnh vực thường có 5-50 nhiệm vụ
 * → fetch 1 lần rồi filter trong RAM nhanh và mượt hơn nhiều.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { Check, ChevronDown, Loader2, Search, X } from 'lucide-react';

import { kpiV2Service } from '@/services/kpi-v2.service';
import { INhiemVu } from '@/types/kpi-v2';

interface Props {
  /** Mã lĩnh vực (I-XV). Bắt buộc — nếu null → combobox disabled. */
  linhVuc?: string;
  /** Giá trị nhiệm vụ đang chọn (exact string từ DB). */
  value?: string;
  onChange: (nhiemVu: string | undefined) => void;
  className?: string;
}

export function NhiemVuCombobox({ linhVuc, value, onChange, className }: Props) {
  const [items, setItems] = useState<INhiemVu[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [keyword, setKeyword] = useState('');
  const wrapRef = useRef<HTMLDivElement>(null);
  const requestSeq = useRef(0);

  // Load nhiệm vụ khi đổi lĩnh vực
  useEffect(() => {
    if (!linhVuc) {
      setItems([]);
      return;
    }
    const seq = ++requestSeq.current;
    setLoading(true);
    kpiV2Service
      .getNhiemVu(linhVuc)
      .then((data) => {
        if (seq !== requestSeq.current) return;
        setItems(data);
      })
      .catch(() => {
        if (seq !== requestSeq.current) return;
        setItems([]);
      })
      .finally(() => {
        if (seq !== requestSeq.current) return;
        setLoading(false);
      });
  }, [linhVuc]);

  // Đóng dropdown khi click ngoài
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
        setKeyword('');
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  const filtered = useMemo(() => {
    const kw = keyword.trim().toLowerCase();
    if (!kw) return items;
    return items.filter((it) => it.nhiem_vu.toLowerCase().includes(kw));
  }, [items, keyword]);

  const disabled = !linhVuc;

  return (
    <div className={className}>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Nhiệm vụ
        {linhVuc && !loading && (
          <span className="ml-1 text-xs font-normal text-gray-500">
            ({items.length} nhiệm vụ)
          </span>
        )}
      </label>

      <div ref={wrapRef} className="relative">
        {/* Trigger: hiển thị giá trị đã chọn hoặc placeholder */}
        {!open ? (
          <button
            type="button"
            onClick={() => !disabled && setOpen(true)}
            disabled={disabled}
            className={[
              'w-full flex items-center justify-between gap-2 rounded-md border px-3 py-2 text-sm text-left transition',
              disabled
                ? 'border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'border-gray-300 bg-white hover:border-gray-400',
            ].join(' ')}
          >
            <span className={value ? 'text-gray-900 line-clamp-1' : 'text-gray-500'}>
              {disabled
                ? '— Chọn lĩnh vực trước —'
                : value
                  ? value
                  : '— Tất cả nhiệm vụ —'}
            </span>
            <span className="flex items-center gap-1 flex-shrink-0">
              {value && !disabled && (
                <X
                  className="h-4 w-4 text-gray-400 hover:text-gray-700"
                  onClick={(e) => {
                    e.stopPropagation();
                    onChange(undefined);
                  }}
                />
              )}
              <ChevronDown className="h-4 w-4 text-gray-400" />
            </span>
          </button>
        ) : (
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              autoFocus
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="Gõ để tìm nhiệm vụ…"
              className="w-full rounded-md border border-blue-500 pl-9 pr-3 py-2 text-sm focus:outline-none"
            />
          </div>
        )}

        {/* Dropdown */}
        {open && (
          <div className="absolute z-20 mt-1 w-full rounded-md border border-gray-200 bg-white shadow-lg max-h-72 overflow-y-auto">
            {/* Item "Tất cả" để clear filter */}
            <button
              type="button"
              onClick={() => {
                onChange(undefined);
                setOpen(false);
                setKeyword('');
              }}
              className={[
                'w-full text-left px-3 py-2 text-sm flex items-center gap-2 border-b border-gray-100',
                !value ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-700',
              ].join(' ')}
            >
              <span className="w-4 flex-shrink-0">
                {!value && <Check className="h-4 w-4 text-blue-600" />}
              </span>
              <span className="italic">Tất cả nhiệm vụ</span>
            </button>

            {loading && (
              <div className="px-3 py-4 text-sm text-gray-500 flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Đang tải…
              </div>
            )}

            {!loading && filtered.length === 0 && (
              <div className="px-3 py-4 text-sm text-gray-500 text-center">
                {keyword
                  ? 'Không có nhiệm vụ khớp từ khoá.'
                  : 'Lĩnh vực này chưa có nhiệm vụ.'}
              </div>
            )}

            {!loading &&
              filtered.map((it) => {
                const selected = it.nhiem_vu === value;
                return (
                  <button
                    key={it.nhiem_vu}
                    type="button"
                    onClick={() => {
                      onChange(it.nhiem_vu);
                      setOpen(false);
                      setKeyword('');
                    }}
                    className={[
                      'w-full text-left px-3 py-2 text-sm flex items-start gap-2 transition',
                      selected ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-700',
                    ].join(' ')}
                  >
                    <span className="w-4 flex-shrink-0 mt-0.5">
                      {selected && <Check className="h-4 w-4 text-blue-600" />}
                    </span>
                    <span className="line-clamp-2">{it.nhiem_vu}</span>
                  </button>
                );
              })}
          </div>
        )}
      </div>
    </div>
  );
}
