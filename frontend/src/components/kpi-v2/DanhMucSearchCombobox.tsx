'use client';

/**
 * components/kpi-v2/DanhMucSearchCombobox.tsx
 * ===========================================
 * List view 2.812 mục PL3 với debounced search server-side.
 *
 * UX:
 * - User chọn lĩnh vực + nhóm + keyword (qua LinhVucNhomFilter ở parent).
 * - Component này chỉ render danh sách kết quả + chọn mục.
 * - Pagination "Tải thêm" thay vì page numbers.
 * - Empty state hướng dẫn nới filter.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { Loader2, Check } from 'lucide-react';

import { kpiV2Service } from '@/services/kpi-v2.service';
import { IDanhMucPL3 } from '@/types/kpi-v2';
import { ILinhVucNhomValue } from './LinhVucNhomFilter';

interface Props {
  filters: ILinhVucNhomValue;
  selectedId?: string;
  onSelect: (item: IDanhMucPL3) => void;
  pageSize?: number;
  /** Slot render thêm action ở góc phải mỗi row (vd: icon ⭐ favorite). */
  renderRowAction?: (item: IDanhMucPL3) => React.ReactNode;
}

const DEBOUNCE_MS = 300;

export function DanhMucSearchCombobox({
  filters,
  selectedId,
  onSelect,
  pageSize = 50,
  renderRowAction,
}: Props) {
  const [items, setItems] = useState<IDanhMucPL3[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const filterKey = useMemo(
    () =>
      `${filters.linh_vuc ?? ''}|${filters.cong_tac ?? ''}|${filters.nhiem_vu ?? ''}|${(filters.search ?? '').trim()}`,
    [filters.linh_vuc, filters.cong_tac, filters.nhiem_vu, filters.search]
  );
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);
  const requestSeq = useRef(0);

  // Reset page về 1 khi filter đổi
  useEffect(() => {
    setPage(1);
  }, [filterKey]);

  // Load + debounce
  useEffect(() => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current);

    const seq = ++requestSeq.current;
    setLoading(true);
    setError(null);

    debounceTimer.current = setTimeout(() => {
      kpiV2Service
        .searchDanhMucPL3({
          linh_vuc: filters.linh_vuc,
          cong_tac: filters.cong_tac,
          nhiem_vu: filters.nhiem_vu,
          search: filters.search?.trim() || undefined,
          page,
          size: pageSize,
        })
        .then((res) => {
          // Ignore stale responses
          if (seq !== requestSeq.current) return;
          if (page === 1) {
            setItems(res.data);
          } else {
            setItems((prev) => [...prev, ...res.data]);
          }
          setTotal(res.pagination?.total_items ?? res.data.length);
        })
        .catch((err) => {
          if (seq !== requestSeq.current) return;
          setError(err?.message ?? 'Lỗi tải danh mục');
        })
        .finally(() => {
          if (seq !== requestSeq.current) return;
          setLoading(false);
        });
    }, DEBOUNCE_MS);

    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
    };
  }, [filterKey, page, pageSize, filters.linh_vuc, filters.cong_tac, filters.nhiem_vu, filters.search]);

  const hasMore = items.length < total;

  return (
    <div className="border border-gray-200 rounded-md bg-white">
      <div className="px-3 py-2 border-b border-gray-100 flex items-center justify-between text-xs text-gray-600">
        <span>
          Hiển thị <strong>{items.length}</strong> / {total} mục
        </span>
        {loading && (
          <span className="flex items-center gap-1">
            <Loader2 className="h-3 w-3 animate-spin" />
            Đang tải…
          </span>
        )}
      </div>

      {error && (
        <div className="px-3 py-2 text-sm text-red-600 bg-red-50 border-b border-red-200">
          {error}
        </div>
      )}

      <div className="max-h-80 overflow-y-auto divide-y divide-gray-100">
        {items.length === 0 && !loading && !error && (
          <div className="px-4 py-6 text-center text-sm text-gray-500">
            Không tìm thấy mục công việc phù hợp.
            <br />
            Thử bỏ filter nhóm hoặc đổi từ khóa tìm kiếm.
          </div>
        )}

        {items.map((item) => {
          const selected = item.id === selectedId;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelect(item)}
              className={[
                'w-full text-left px-4 py-3 transition flex gap-3',
                selected ? 'bg-blue-50' : 'hover:bg-gray-50',
              ].join(' ')}
            >
              <div className="flex-shrink-0 mt-0.5">
                {selected ? (
                  <Check className="h-4 w-4 text-blue-600" />
                ) : (
                  <div className="h-4 w-4 rounded border border-gray-300" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-medium text-sm text-gray-900 line-clamp-2">
                    {item.ten_cong_viec}
                  </p>
                  <span className="flex-shrink-0 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                    Nhóm {item.nhom_pl3}
                  </span>
                </div>
                <div className="mt-1 text-xs text-gray-600 space-y-0.5">
                  {item.cong_tac && (
                    <div className="whitespace-pre-line">
                      <span className="text-gray-500">Công tác:</span>{' '}
                      <span className="text-gray-700">{item.cong_tac}</span>
                    </div>
                  )}
                  {item.nhiem_vu && (
                    <div className="whitespace-pre-line">
                      <span className="text-gray-500">Nhiệm vụ:</span>{' '}
                      <span className="text-gray-700">{item.nhiem_vu}</span>
                    </div>
                  )}
                  <div>
                    <span className="text-gray-500">Đầu ra:</span>{' '}
                    {item.san_pham_dau_ra ?? '—'}
                  </div>
                  <div className="flex flex-wrap gap-3">
                    <span>
                      <span className="text-gray-500">Lĩnh vực:</span> {item.linh_vuc}
                    </span>
                    <span>
                      <span className="text-gray-500">Hệ số:</span>{' '}
                      <strong className="text-blue-700">
                        {item.he_so_quy_doi.toFixed(6).replace(/\.?0+$/, '')}
                      </strong>
                    </span>
                    <span>
                      <span className="text-gray-500">Khung max:</span>{' '}
                      {item.khung_diem_toi_da}
                    </span>
                  </div>
                </div>
              </div>
              {renderRowAction && (
                <div className="flex-shrink-0">{renderRowAction(item)}</div>
              )}
            </button>
          );
        })}
      </div>

      {hasMore && (
        <div className="px-3 py-2 border-t border-gray-100 text-center">
          <button
            type="button"
            onClick={() => setPage((p) => p + 1)}
            disabled={loading}
            className="text-sm text-blue-600 hover:text-blue-800 disabled:text-gray-400"
          >
            {loading ? 'Đang tải…' : `Tải thêm (${total - items.length} còn lại)`}
          </button>
        </div>
      )}
    </div>
  );
}
