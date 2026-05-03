/**
 * CongChucPicker — type-ahead search picker.
 *
 * G4-fix-2 (01/05/2026): backend dùng endpoint HKG riêng
 * `GET /api/v1/hop-khong-giay/cong-chuc/search` thay LMS endpoint.
 * ACL HKG bao gồm THU_KY_HOP/CHANH_VP/TRUONG_CNTT/BI_THU_CHI_BO + lãnh đạo
 * + admin → đủ cover form-creators HKG.
 *
 * UX:
 * - Type ≥ 2 ký tự → debounce 300ms → query
 * - Single mode: chọn 1 CBCC, hiển thị "Họ tên — Mã — Đơn vị"
 * - Multi mode: tag list, click X để xóa
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import { Search, X, Loader2 } from 'lucide-react';
import { congChucApi, type ICongChucSearchItem } from '@/services/hkg';

const DEBOUNCE_MS = 300;

interface ICongChucResult {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string | null;
  don_vi_id: string | null;
  don_vi_ten: string | null;
}

interface IBaseProps {
  /** Placeholder cho input */
  placeholder?: string;
  /** Disable */
  disabled?: boolean;
  /** Filter kết quả search theo đơn vị (UUID). Bỏ trống = toàn Chi cục. */
  donViId?: string | null;
  /**
   * Seed cache hiển thị cho các id đã chọn nhưng chưa search.
   * Form sửa pass vào để picker hiện "Họ tên (mã)" thay vì UUID.
   */
  initialItems?: ICongChucResult[];
}

interface ISinglePickerProps extends IBaseProps {
  multiple?: false;
  value: string | null;
  onChange: (id: string | null, item?: ICongChucResult) => void;
}

interface IMultiPickerProps extends IBaseProps {
  multiple: true;
  value: string[];
  onChange: (ids: string[]) => void;
}

export type CongChucPickerProps = ISinglePickerProps | IMultiPickerProps;

// Cache module-level cho selected items (id → ICongChucResult), tránh re-fetch chỉ để hiện tên.
const selectedCache = new Map<string, ICongChucResult>();

export default function CongChucPicker(props: CongChucPickerProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<ICongChucResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  // Re-render trigger khi cache được seed sau mount (form sửa fetch async)
  const [, setCacheVersion] = useState(0);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Seed cache từ initialItems để hiện "Họ tên (mã)" thay vì UUID
  useEffect(() => {
    if (!props.initialItems?.length) return;
    let added = false;
    props.initialItems.forEach((it) => {
      if (!selectedCache.has(it.id)) {
        selectedCache.set(it.id, it);
        added = true;
      }
    });
    if (added) setCacheVersion((v) => v + 1);
  }, [props.initialItems]);

  // Selected items hiển thị (multiple)
  const selectedIds = props.multiple ? props.value : props.value ? [props.value] : [];

  // Click outside → close dropdown
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  // Debounce search
  useEffect(() => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    if (query.trim().length < 2) {
      setResults([]);
      return;
    }
    debounceTimer.current = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await congChucApi.search({
          q: query.trim(),
          don_vi_id: props.donViId || undefined,
          limit: 20,
        });
        // BE HKG trả {id, ho_ten, ma_cc, don_vi_id, ten_don_vi, ...} — map sang shape picker
        const items: ICongChucResult[] = data.map((it: ICongChucSearchItem) => ({
          id: it.id,
          ma_cc: it.ma_cc,
          ho_ten: it.ho_ten,
          chuc_vu: it.chuc_vu,
          don_vi_id: it.don_vi_id,
          don_vi_ten: it.ten_don_vi,
        }));
        setResults(items);
        items.forEach((it) => selectedCache.set(it.id, it));
        setOpen(true);
      } catch (e: unknown) {
        const status = (e as { response?: { status?: number } })?.response?.status;
        if (status === 403) {
          setError('Bạn không có quyền tìm CBCC');
        } else {
          setError('Lỗi tìm kiếm');
        }
      } finally {
        setLoading(false);
      }
    }, DEBOUNCE_MS);

    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
    };
    // donViId change re-trigger search với scope mới
  }, [query, props.donViId]);

  const handleSelect = (item: ICongChucResult) => {
    selectedCache.set(item.id, item);
    if (props.multiple) {
      if (!props.value.includes(item.id)) {
        props.onChange([...props.value, item.id]);
      }
    } else {
      props.onChange(item.id, item);
      setQuery('');
      setOpen(false);
    }
  };

  const handleRemove = (id: string) => {
    if (props.multiple) {
      props.onChange(props.value.filter((v) => v !== id));
    } else {
      props.onChange(null);
    }
  };

  return (
    <div ref={containerRef} className="relative">
      {/* Selected tags */}
      {props.multiple && selectedIds.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {selectedIds.map((id) => {
            const item = selectedCache.get(id);
            return (
              <span
                key={id}
                className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
              >
                {item ? `${item.ho_ten} (${item.ma_cc})` : id.substring(0, 8) + '...'}
                <button
                  type="button"
                  onClick={() => handleRemove(id)}
                  className="hover:text-blue-900"
                  disabled={props.disabled}
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            );
          })}
        </div>
      )}

      {/* Single selected display */}
      {!props.multiple && props.value && (
        <div className="flex items-center justify-between p-2 mb-2 bg-blue-50 border border-blue-200 rounded text-sm">
          <span>
            {(() => {
              const item = selectedCache.get(props.value);
              return item ? `${item.ho_ten} (${item.ma_cc}) — ${item.don_vi_ten || ''}` : props.value;
            })()}
          </span>
          <button
            type="button"
            onClick={() => handleRemove(props.value!)}
            className="text-blue-700 hover:text-blue-900"
            disabled={props.disabled}
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
          placeholder={props.placeholder || 'Gõ tên hoặc mã CBCC...'}
          disabled={props.disabled}
          className="w-full pl-9 pr-3 py-2 border rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {loading && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-gray-400" />
        )}
      </div>

      {error && <div className="mt-1 text-xs text-red-600">{error}</div>}

      {/* Dropdown */}
      {open && results.length > 0 && (
        <div className="absolute z-10 mt-1 w-full bg-white border rounded shadow-lg max-h-64 overflow-y-auto">
          {results.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => handleSelect(item)}
              className="w-full text-left px-3 py-2 hover:bg-blue-50 text-sm border-b last:border-b-0"
            >
              <div className="font-medium">{item.ho_ten} <span className="text-xs text-gray-500">({item.ma_cc})</span></div>
              <div className="text-xs text-gray-600">
                {item.chuc_vu || '—'} · {item.don_vi_ten || '—'}
              </div>
            </button>
          ))}
        </div>
      )}

      {open && results.length === 0 && query.trim().length >= 2 && !loading && !error && (
        <div className="absolute z-10 mt-1 w-full bg-white border rounded shadow-lg p-3 text-sm text-gray-500">
          Không tìm thấy CBCC khớp.
        </div>
      )}
    </div>
  );
}
