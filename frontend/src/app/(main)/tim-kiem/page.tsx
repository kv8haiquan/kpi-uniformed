/**
 * src/app/(main)/tim-kiem/page.tsx
 * ==================================
 * Trang tìm kiếm hợp nhất — kết quả từ nhiều module, tab lọc theo module.
 */

'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { searchApi } from '@/services/common';
import type {
  ISearchResultItem,
  ISearchResponse,
  ISearchParams,
  SearchModule,
} from '@/types/common';
import { SEARCH_MODULE_LABELS } from '@/types/common';

// =============================================================================
// CONSTANTS
// =============================================================================

const MODULE_ICON: Record<string, string> = {
  LEGAL: '⚖️',
  FORUM: '💬',
  LMS: '📚',
  PORTAL: '📰',
  COMMON: '📖',
};

const ALL_MODULES: (SearchModule | '')[] = ['', 'COMMON', 'LEGAL', 'LMS', 'PORTAL', 'FORUM'];

// =============================================================================
// MAIN
// =============================================================================

export default function TimKiemPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const inputRef = useRef<HTMLInputElement>(null);

  // State
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [results, setResults] = useState<ISearchResponse | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [activeModule, setActiveModule] = useState<SearchModule | ''>('');

  // Search
  const doSearch = useCallback(async (q: string, p: number, mod: string) => {
    if (!q || q.length < 2) return;
    setLoading(true);
    setError(null);
    try {
      const searchParams: ISearchParams = { q, page: p, page_size: 20 };
      if (mod) searchParams.modules = mod.toLowerCase();
      const res = await searchApi.timKiem(searchParams);
      setResults(res.data.data);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Không thể tìm kiếm');
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-search on mount if query in URL
  useEffect(() => {
    const q = searchParams.get('q');
    if (q && q.length >= 2) {
      setQuery(q);
      doSearch(q, 1, activeModule);
    }
    // Focus input
    inputRef.current?.focus();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Suggestions
  useEffect(() => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await searchApi.goiY(query);
        setSuggestions(res.data.data?.suggestions || []);
      } catch {
        // ignore
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  // Submit search
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.length < 2) return;
    setShowSuggestions(false);
    setPage(1);
    doSearch(query, 1, activeModule);
    // Update URL
    router.replace(`/tim-kiem?q=${encodeURIComponent(query)}`);
  };

  // Tab change
  const handleModuleChange = (mod: SearchModule | '') => {
    setActiveModule(mod);
    setPage(1);
    if (query.length >= 2) doSearch(query, 1, mod);
  };

  // Pagination
  const handlePageChange = (p: number) => {
    setPage(p);
    doSearch(query, p, activeModule);
  };

  const totalPages = results ? Math.ceil(results.total / results.page_size) : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Tìm kiếm</h1>
          <p className="text-sm text-gray-500 mt-1">Tìm kiếm trên toàn bộ nền tảng</p>
        </div>

        {/* Search box */}
        <form onSubmit={handleSubmit} className="relative mb-6">
          <div className="relative">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setShowSuggestions(true);
              }}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              placeholder="Nhập từ khóa tìm kiếm (tối thiểu 2 ký tự)..."
              className="w-full border border-gray-300 rounded-xl pl-12 pr-4 py-3 text-base focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm"
            />
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 text-lg">
              🔍
            </span>
            <button
              type="submit"
              className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
            >
              Tìm
            </button>
          </div>

          {/* Suggestions dropdown */}
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden">
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  type="button"
                  className="w-full text-left px-4 py-2.5 text-sm hover:bg-gray-50 transition-colors"
                  onMouseDown={() => {
                    setQuery(s);
                    setShowSuggestions(false);
                    setPage(1);
                    doSearch(s, 1, activeModule);
                    router.replace(`/tim-kiem?q=${encodeURIComponent(s)}`);
                  }}
                >
                  <span className="text-gray-400 mr-2">🔍</span>
                  {s}
                </button>
              ))}
            </div>
          )}
        </form>

        {/* Module tabs */}
        {results && (
          <div className="flex flex-wrap gap-2 mb-4">
            {ALL_MODULES.map((mod) => {
              const cnt = mod
                ? results.total_by_module[mod] || 0
                : results.total;
              return (
                <button
                  key={mod || 'all'}
                  onClick={() => handleModuleChange(mod)}
                  className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
                    activeModule === mod
                      ? 'bg-blue-600 text-white'
                      : 'bg-white border border-gray-300 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {mod ? (
                    <>
                      <span className="mr-1">{MODULE_ICON[mod]}</span>
                      {SEARCH_MODULE_LABELS[mod]}
                    </>
                  ) : (
                    'Tất cả'
                  )}
                  <span className="ml-1 opacity-70">({cnt})</span>
                </button>
              );
            })}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4 text-center">
            <p className="text-red-700">{error}</p>
            <p className="text-sm text-red-500 mt-1">Hãy đảm bảo Common backend đang chạy trên port 8005</p>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        )}

        {/* Results */}
        {!loading && results && (
          <>
            {results.results.length === 0 ? (
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm text-center py-16 text-gray-500">
                <span className="text-4xl block mb-2">🔍</span>
                Không tìm thấy kết quả nào cho &ldquo;{query}&rdquo;
              </div>
            ) : (
              <div className="space-y-3">
                {results.results.map((item) => (
                  <SearchResultCard key={`${item.module}-${item.id}`} item={item} />
                ))}
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-6">
                <button
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page <= 1}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Trước
                </button>
                <span className="text-sm text-gray-600">
                  Trang {page} / {totalPages}
                </span>
                <button
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page >= totalPages}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Tiếp
                </button>
              </div>
            )}
          </>
        )}

        {/* No search yet */}
        {!loading && !results && !error && (
          <div className="text-center py-20 text-gray-500">
            <span className="text-5xl block mb-3">🔍</span>
            <p className="text-lg font-medium text-gray-700">Tìm kiếm trên toàn nền tảng</p>
            <p className="text-sm mt-1">Pháp luật, Đào tạo, Diễn đàn, Tin tức, Kho tri thức</p>
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// SEARCH RESULT CARD
// =============================================================================

function SearchResultCard({ item }: { item: ISearchResultItem }) {
  return (
    <a
      href={item.link}
      className="block bg-white rounded-xl border border-gray-200 shadow-sm p-4 hover:border-blue-300 hover:shadow-md transition-all"
    >
      <div className="flex items-start gap-3">
        {/* Module icon */}
        <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-gray-100 shrink-0 mt-0.5">
          <span className="text-lg">{MODULE_ICON[item.module] || '📄'}</span>
        </div>

        <div className="flex-1 min-w-0">
          {/* Title */}
          <h3 className="font-medium text-gray-900 mb-1">{item.title}</h3>

          {/* Snippet */}
          <p className="text-sm text-gray-600 line-clamp-2">{item.snippet}</p>

          {/* Meta */}
          <div className="flex items-center gap-2 mt-2">
            <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">
              {SEARCH_MODULE_LABELS[item.module as SearchModule] || item.module}
            </span>
            <span className="text-xs text-gray-400">{item.type}</span>
          </div>
        </div>
      </div>
    </a>
  );
}
