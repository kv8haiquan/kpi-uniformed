'use client';

/**
 * components/kpi-v2/DanhMucPickerTabs.tsx
 * =======================================
 * Wrapper picker với 3 tab cho modal kê khai V2:
 *   ⭐ Yêu thích   → favorites do user mark thủ công
 *   🕐 Tháng trước → mục đã dùng trong 3 tháng có data gần nhất (auto)
 *   📋 Tất cả      → search 2.812 mục PL3 (LinhVucNhomFilter + Combobox)
 *
 * Default tab khi mở modal:
 *   - favorites ≥ 1 → "⭐ Yêu thích"
 *   - else recent ≥ 1 → "🕐 Tháng trước"
 *   - else → "📋 Tất cả"
 *   - Edit mode (initialTab='all'): luôn nhảy thẳng "Tất cả".
 *
 * Mọi tab đều có icon ⭐ trên row để toggle favorite tại chỗ.
 * Cảnh báo khi favorites > 30.
 */

import { useEffect, useMemo, useState } from 'react';
import { Check, Loader2, Star, StarOff, AlertTriangle } from 'lucide-react';

import { kpiV2Service } from '@/services/kpi-v2.service';
import { IDanhMucPL3, IFavoriteItem, IRecentItem } from '@/types/kpi-v2';

import { DanhMucSearchCombobox } from './DanhMucSearchCombobox';
import { LinhVucNhomFilter, ILinhVucNhomValue } from './LinhVucNhomFilter';

export type PickerTabKey = 'favorites' | 'recent' | 'all';

interface Props {
  thang: number;
  nam: number;
  selectedId?: string;
  onSelect: (item: IDanhMucPL3) => void;
  /** Edit mode: ép default tab = 'all' để user thấy mục đang chọn. */
  initialTab?: PickerTabKey;
  /**
   * Edit mode: prefill filter (lĩnh vực + nhiệm vụ) để user thấy mục đang chọn
   * nằm ở nhánh nào của cây PL3.
   */
  initialFilters?: ILinhVucNhomValue;
}

const FAVORITE_WARN_THRESHOLD = 30;

export function DanhMucPickerTabs({
  thang,
  nam,
  selectedId,
  onSelect,
  initialTab,
  initialFilters,
}: Props) {
  const [favorites, setFavorites] = useState<IFavoriteItem[]>([]);
  const [recent, setRecent] = useState<IRecentItem[]>([]);
  const [favSet, setFavSet] = useState<Set<string>>(new Set());
  const [loadingFav, setLoadingFav] = useState(true);
  const [loadingRecent, setLoadingRecent] = useState(true);
  const [activeTab, setActiveTab] = useState<PickerTabKey | null>(null);
  const [filters, setFilters] = useState<ILinhVucNhomValue>(initialFilters ?? {});

  // Load favorites + recent song song khi mount
  useEffect(() => {
    let cancelled = false;
    setLoadingFav(true);
    setLoadingRecent(true);

    kpiV2Service
      .getFavorites()
      .then((data) => {
        if (cancelled) return;
        setFavorites(data);
        setFavSet(new Set(data.map((f) => f.danh_muc_sp_id)));
      })
      .catch(() => {
        if (cancelled) return;
        setFavorites([]);
        setFavSet(new Set());
      })
      .finally(() => {
        if (!cancelled) setLoadingFav(false);
      });

    kpiV2Service
      .getRecent(thang, nam)
      .then((data) => {
        if (!cancelled) setRecent(data);
      })
      .catch(() => {
        if (!cancelled) setRecent([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingRecent(false);
      });

    return () => {
      cancelled = true;
    };
  }, [thang, nam]);

  // Default tab logic — chỉ chạy 1 lần sau khi load xong
  useEffect(() => {
    if (activeTab !== null) return;
    if (loadingFav || loadingRecent) return;

    if (initialTab) {
      setActiveTab(initialTab);
      return;
    }
    if (favorites.length > 0) setActiveTab('favorites');
    else if (recent.length > 0) setActiveTab('recent');
    else setActiveTab('all');
  }, [loadingFav, loadingRecent, favorites.length, recent.length, initialTab, activeTab]);

  const handleToggleFavorite = async (dm: IDanhMucPL3) => {
    const isFav = favSet.has(dm.id);
    // Optimistic update
    if (isFav) {
      setFavSet((s) => {
        const next = new Set(s);
        next.delete(dm.id);
        return next;
      });
      setFavorites((list) => list.filter((f) => f.danh_muc_sp_id !== dm.id));
      try {
        await kpiV2Service.removeFavorite(dm.id);
      } catch {
        // Rollback nếu lỗi
        setFavSet((s) => {
          const next = new Set(s);
          next.add(dm.id);
          return next;
        });
        // Reload toàn bộ favorites cho an toàn
        const fresh = await kpiV2Service.getFavorites().catch(() => []);
        setFavorites(fresh);
        setFavSet(new Set(fresh.map((f) => f.danh_muc_sp_id)));
      }
    } else {
      setFavSet((s) => new Set(s).add(dm.id));
      try {
        const created = await kpiV2Service.addFavorite(dm.id);
        setFavorites((list) => [created, ...list.filter((f) => f.danh_muc_sp_id !== dm.id)]);
      } catch {
        setFavSet((s) => {
          const next = new Set(s);
          next.delete(dm.id);
          return next;
        });
      }
    }
  };

  const tabs: Array<{ key: PickerTabKey; label: string; count: number | null }> = useMemo(
    () => [
      { key: 'favorites', label: '⭐ Yêu thích', count: loadingFav ? null : favorites.length },
      { key: 'recent', label: '🕐 Tháng trước', count: loadingRecent ? null : recent.length },
      { key: 'all', label: '📋 Tất cả', count: null },
    ],
    [favorites.length, recent.length, loadingFav, loadingRecent]
  );

  if (activeTab === null) {
    return (
      <div className="border border-gray-200 rounded-md bg-white p-6 flex items-center justify-center text-sm text-gray-500">
        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
        Đang tải danh sách công việc…
      </div>
    );
  }

  return (
    <div className="border border-gray-200 rounded-md bg-white">
      {/* Tab bar */}
      <div className="flex border-b border-gray-200 bg-gray-50 rounded-t-md">
        {tabs.map((tab) => {
          const active = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              className={[
                'flex-1 px-4 py-2.5 text-sm font-medium transition border-b-2',
                active
                  ? 'border-blue-600 text-blue-700 bg-white'
                  : 'border-transparent text-gray-600 hover:bg-gray-100',
              ].join(' ')}
            >
              {tab.label}
              {tab.count !== null && (
                <span
                  className={[
                    'ml-1.5 inline-flex items-center justify-center min-w-[20px] px-1.5 rounded-full text-xs',
                    active ? 'bg-blue-100 text-blue-700' : 'bg-gray-200 text-gray-700',
                  ].join(' ')}
                >
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Cảnh báo > 30 favorites — chỉ hiện trong tab "Yêu thích" */}
      {activeTab === 'favorites' && favorites.length > FAVORITE_WARN_THRESHOLD && (
        <div className="px-4 py-2 bg-amber-50 border-b border-amber-200 text-xs text-amber-800 flex items-start gap-2">
          <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" />
          <span>
            Bạn đã đánh dấu <strong>{favorites.length}</strong> mục yêu thích. Cân nhắc bỏ
            bớt các mục ít dùng để danh sách dễ quản lý.
          </span>
        </div>
      )}

      {/* Content theo tab */}
      <div className="p-3">
        {activeTab === 'favorites' && (
          <SimpleList
            items={favorites.map((f) => ({
              key: f.id,
              dm: f.danh_muc_sp,
              meta: null,
            }))}
            loading={loadingFav}
            emptyMessage={
              <>
                Chưa có mục công việc yêu thích.
                <br />
                Mở tab <strong>📋 Tất cả</strong> và nhấn ⭐ trên mục bạn hay dùng.
              </>
            }
            selectedId={selectedId}
            favSet={favSet}
            onSelect={onSelect}
            onToggleFavorite={handleToggleFavorite}
          />
        )}

        {activeTab === 'recent' && (
          <SimpleList
            items={recent.map((r) => ({
              key: r.danh_muc_sp_id,
              dm: r.danh_muc_sp,
              meta: `Dùng gần nhất: ${r.last_used_thang}/${r.last_used_nam} • ${r.used_count_3m} lần`,
            }))}
            loading={loadingRecent}
            emptyMessage="Chưa có dữ liệu kê khai trong 3 tháng gần đây."
            selectedId={selectedId}
            favSet={favSet}
            onSelect={onSelect}
            onToggleFavorite={handleToggleFavorite}
          />
        )}

        {activeTab === 'all' && (
          <div className="space-y-3">
            <LinhVucNhomFilter value={filters} onChange={setFilters} />
            <DanhMucSearchCombobox
              filters={filters}
              selectedId={selectedId}
              onSelect={onSelect}
              renderRowAction={(dm) => (
                <FavoriteToggle
                  isFavorite={favSet.has(dm.id)}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleToggleFavorite(dm);
                  }}
                />
              )}
            />
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

interface SimpleListProps {
  items: Array<{ key: string; dm: IDanhMucPL3; meta: string | null }>;
  loading: boolean;
  emptyMessage: React.ReactNode;
  selectedId?: string;
  favSet: Set<string>;
  onSelect: (dm: IDanhMucPL3) => void;
  onToggleFavorite: (dm: IDanhMucPL3) => void;
}

function SimpleList({
  items,
  loading,
  emptyMessage,
  selectedId,
  favSet,
  onSelect,
  onToggleFavorite,
}: SimpleListProps) {
  if (loading) {
    return (
      <div className="px-4 py-6 text-center text-sm text-gray-500 flex items-center justify-center">
        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
        Đang tải…
      </div>
    );
  }
  if (items.length === 0) {
    return <div className="px-4 py-6 text-center text-sm text-gray-500">{emptyMessage}</div>;
  }
  return (
    <div className="max-h-80 overflow-y-auto divide-y divide-gray-100 border border-gray-200 rounded-md">
      {items.map(({ key, dm, meta }) => {
        const selected = dm.id === selectedId;
        return (
          <button
            key={key}
            type="button"
            onClick={() => onSelect(dm)}
            className={[
              'w-full text-left px-4 py-3 transition flex gap-3 items-start',
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
                  {dm.ten_cong_viec}
                </p>
                <span className="flex-shrink-0 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                  Nhóm {dm.nhom_pl3}
                </span>
              </div>
              <div className="mt-1 text-xs text-gray-600 space-y-0.5">
                {dm.cong_tac && (
                  <div className="whitespace-pre-line">
                    <span className="text-gray-500">Công tác:</span>{' '}
                    <span className="text-gray-700">{dm.cong_tac}</span>
                  </div>
                )}
                {dm.nhiem_vu && (
                  <div className="whitespace-pre-line">
                    <span className="text-gray-500">Nhiệm vụ:</span>{' '}
                    <span className="text-gray-700">{dm.nhiem_vu}</span>
                  </div>
                )}
                <div>
                  <span className="text-gray-500">Sản phẩm:</span>{' '}
                  {dm.san_pham_dau_ra ?? '—'}
                </div>
                <div className="flex flex-wrap gap-3">
                  <span>
                    <span className="text-gray-500">Lĩnh vực:</span> {dm.linh_vuc}
                  </span>
                  <span>
                    <span className="text-gray-500">Hệ số:</span>{' '}
                    <strong className="text-blue-700">
                      {dm.he_so_quy_doi.toFixed(2)}
                    </strong>
                  </span>
                  <span>
                    <span className="text-gray-500">Khung max:</span>{' '}
                    {dm.khung_diem_toi_da}
                  </span>
                </div>
                {meta && <div className="text-gray-500 italic">{meta}</div>}
              </div>
            </div>
            <FavoriteToggle
              isFavorite={favSet.has(dm.id)}
              onClick={(e) => {
                e.stopPropagation();
                onToggleFavorite(dm);
              }}
            />
          </button>
        );
      })}
    </div>
  );
}

interface FavoriteToggleProps {
  isFavorite: boolean;
  onClick: (e: React.MouseEvent) => void;
}

function FavoriteToggle({ isFavorite, onClick }: FavoriteToggleProps) {
  return (
    <span
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick(e as unknown as React.MouseEvent);
        }
      }}
      title={isFavorite ? 'Bỏ yêu thích' : 'Đánh dấu yêu thích'}
      className={[
        'flex-shrink-0 mt-0.5 p-1 rounded cursor-pointer transition',
        isFavorite
          ? 'text-amber-500 hover:bg-amber-50'
          : 'text-gray-300 hover:text-amber-500 hover:bg-amber-50',
      ].join(' ')}
    >
      {isFavorite ? (
        <Star className="h-4 w-4 fill-current" />
      ) : (
        <StarOff className="h-4 w-4" />
      )}
    </span>
  );
}
