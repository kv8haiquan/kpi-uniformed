/**
 * app/(main)/tai-lieu/page.tsx
 * ==============================
 * Thư viện tài liệu — tree navigation + file browser + upload.
 *
 * Layout desktop: sidebar (thư mục) + main (tài liệu)
 * Layout mobile: sidebar ẩn, toggle bằng nút hamburger
 */

'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { thuMucApi, taiLieuApi } from '@/services/portal';
import { taiLieuApi as taiLieuHopApi } from '@/services/hkg';
import { useCurrentUser } from '@/stores/useAuthStore';
import type { IThuMucTree, ITaiLieuItem } from '@/types/tai-lieu';
import type { NguonKhoTaiLieu } from '@/types/hkg';
import FolderTree from '@/components/portal/FolderTree';
import FileCard from '@/components/portal/FileCard';
import FileListItem from '@/components/portal/FileListItem';
import KhoTaiLieuHop from '@/components/portal/KhoTaiLieuHop';
import UploadModal from '@/components/portal/UploadModal';

// =============================================================================
// THƯ MỤC ẢO — kho tài liệu họp
// =============================================================================
// Tài liệu họp nằm ở `meeting.tai_lieu`, KHÔNG sao chép sang `portal.tai_lieu`.
// Ba lý do: nhân đôi 1,6 GB, hai bên lệch nhau khi có tài liệu mới, và portal
// có mô hình quyền riêng nên sao chép sang là bỏ qua phân quyền G5.4.
//
// Nên cây thư mục có thêm ba nút "ảo": khi chọn, trang gọi thẳng meeting_service
// thay vì portal_service. Id đặt tiền tố `kho:` để không lẫn với UUID thật.
const KHO_GOC = 'kho:tat-ca';
const KHO_HKG = 'kho:HKG';
const KHO_LICH = 'kho:LICH_CONG_TAC';

/** Id thư mục này có phải kho tài liệu họp không. */
const laKhoHop = (id: string | null) => Boolean(id?.startsWith('kho:'));

/** Nguồn tương ứng; `undefined` nghĩa là cả hai. */
function nguonCuaKho(id: string | null): NguonKhoTaiLieu | undefined {
  if (id === KHO_HKG) return 'HKG';
  if (id === KHO_LICH) return 'LICH_CONG_TAC';
  return undefined;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const PAGE_SIZE = 20;

const FILE_TYPE_OPTIONS = [
  { value: '', label: 'Tất cả loại file' },
  { value: 'application/pdf', label: 'PDF' },
  { value: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', label: 'Word (DOCX)' },
  { value: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', label: 'Excel (XLSX)' },
  { value: 'application/vnd.openxmlformats-officedocument.presentationml.presentation', label: 'PowerPoint (PPTX)' },
  { value: 'image/', label: 'Ảnh' },
  { value: 'application/zip', label: 'ZIP' },
];

// =============================================================================
// PAGE
// =============================================================================

export default function TaiLieuPage() {
  const user = useCurrentUser();
  const isAdmin = user?.is_system_admin ?? false;
  // Người có quyền quản trị tài liệu (xóa của người khác): admin hoặc platform role
  const isQuanTriTaiLieu =
    isAdmin ||
    (user?.platform_roles ?? []).some((r) => r === 'QT_NOI_DUNG' || r === 'BIEN_TAP');

  /** True nếu current user được xóa file này (owner hoặc quản trị) */
  const canDelete = (file: ITaiLieuItem) => {
    if (isQuanTriTaiLieu) return true;
    return user?.id === file.nguoi_tai_len?.id;
  };

  const [folders, setFolders] = useState<IThuMucTree[]>([]);
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);
  const [files, setFiles] = useState<ITaiLieuItem[]>([]);
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total_items: 0 });
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [loadingFolders, setLoadingFolders] = useState(true);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [filterType, setFilterType] = useState('');
  const [page, setPage] = useState(1);

  // ---------------------------------------------------------------------------
  // Fetch folders tree
  // ---------------------------------------------------------------------------

  useEffect(() => {
    const load = async () => {
      try {
        const res = await thuMucApi.tree();
        const data = res.data?.data ?? res.data;
        setFolders(Array.isArray(data) ? data : []);
      } catch {
        setFolders([]);
      } finally {
        setLoadingFolders(false);
      }
    };
    load();
  }, []);

  // ---------------------------------------------------------------------------
  // Fetch files
  // ---------------------------------------------------------------------------

  const fetchFiles = useCallback(async () => {
    // Kho tài liệu họp do KhoTaiLieuHop tự tải từ meeting_service — gọi
    // portal_service ở đây chỉ tổ nhấp nháy một danh sách rồi bỏ đi.
    if (laKhoHop(selectedFolderId)) {
      setFiles([]);
      setPagination({ page: 1, total_pages: 1, total_items: 0 });
      setLoadingFiles(false);
      return;
    }
    setLoadingFiles(true);
    try {
      const res = await taiLieuApi.danhSach({
        thu_muc_id: selectedFolderId || undefined,
        file_type: filterType || undefined,
        search: searchText || undefined,
        page,
        page_size: PAGE_SIZE,
      });
      const raw = res.data?.data ?? res.data;
      setFiles(raw?.items ?? []);
      setPagination({
        page: raw?.pagination?.page ?? 1,
        total_pages: raw?.pagination?.total_pages ?? 1,
        total_items: raw?.pagination?.total_items ?? 0,
      });
    } catch {
      setFiles([]);
    } finally {
      setLoadingFiles(false);
    }
  }, [selectedFolderId, filterType, searchText, page]);

  useEffect(() => { fetchFiles(); }, [fetchFiles]);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const handleFolderSelect = (id: string) => {
    setSelectedFolderId(id || null);
    setPage(1);
    setSidebarOpen(false);
  };

  const handleSearchChange = (val: string) => {
    setSearchText(val);
    setPage(1);
  };

  const handleFilterType = (val: string) => {
    setFilterType(val);
    setPage(1);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Bạn có chắc muốn xóa tài liệu này? Thao tác này không thể hoàn tác.')) return;
    try {
      await taiLieuApi.xoa(id);
      fetchFiles();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: { error?: { message?: string } } | string } } };
      const msg =
        (typeof e?.response?.data?.detail === 'object'
          ? e?.response?.data?.detail?.error?.message
          : e?.response?.data?.detail) ||
        'Xóa tài liệu thất bại. Vui lòng thử lại.';
      alert(String(msg));
    }
  };

  // Số tài liệu mỗi nguồn, để gắn vào nhãn thư mục ảo.
  const [khoDem, setKhoDem] = useState<{ HKG: number; LICH_CONG_TAC: number; tong: number } | null>(null);
  useEffect(() => {
    taiLieuHopApi.khoThongKe().then(setKhoDem).catch(() => setKhoDem(null));
  }, []);

  /** Cây hiển thị = thư mục thật + nhánh ảo "HKG + Lịch công tác". */
  const cayHienThi = useMemo<IThuMucTree[]>(() => {
    const soLuong = (n: number | undefined) => (n ? ` (${n})` : '');
    const nhanhKho: IThuMucTree = {
      id: KHO_GOC,
      ten: `HKG + Lịch công tác${soLuong(khoDem?.tong)}`,
      parent_id: null,
      thu_tu: -1,
      children: [
        {
          id: KHO_HKG,
          ten: `Họp Không Giấy${soLuong(khoDem?.HKG)}`,
          parent_id: KHO_GOC,
          thu_tu: 0,
          children: [],
          quyen_truy_cap: 'TAT_CA',
        },
        {
          id: KHO_LICH,
          ten: `Lịch công tác${soLuong(khoDem?.LICH_CONG_TAC)}`,
          parent_id: KHO_GOC,
          thu_tu: 1,
          children: [],
          quyen_truy_cap: 'TAT_CA',
        },
      ],
      // `quyen_truy_cap` chỉ có nghĩa với thư mục thật của portal. Nhánh này
      // là ảo: quyền do meeting_service quyết theo từng cuộc họp và từng tài
      // liệu (G5.4), không phải theo thư mục.
      quyen_truy_cap: 'TAT_CA',
    } as unknown as IThuMucTree;
    // Đặt lên đầu: đây là kho có dữ liệu thật (866 file), còn thư viện văn
    // bản pháp quy mới có 22 file.
    return [nhanhKho, ...folders];
  }, [folders, khoDem]);

  const selectedFolderName = (() => {
    if (!selectedFolderId) return 'Tất cả tài liệu';
    const findNode = (nodes: IThuMucTree[]): string | null => {
      for (const n of nodes) {
        if (n.id === selectedFolderId) return n.ten;
        const r = findNode(n.children);
        if (r) return r;
      }
      return null;
    };
    return findNode(cayHienThi) ?? 'Thư mục';
  })();

  // ---------------------------------------------------------------------------
  // RENDER
  // ---------------------------------------------------------------------------

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6">

        {/* Page header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <button
              className="lg:hidden p-2 rounded-lg border border-gray-200 bg-white hover:bg-gray-50"
              onClick={() => setSidebarOpen((v) => !v)}
            >
              ☰
            </button>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Thư viện tài liệu</h1>
              <p className="text-xs text-gray-400 mt-0.5 hidden sm:block">
                {selectedFolderName} · {pagination.total_items} tài liệu
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              if (laKhoHop(selectedFolderId)) {
                alert(
                  'Tài liệu họp được nộp ngay trong màn hình cuộc họp hoặc ' +
                  'lịch công tác, để gắn đúng vào cuộc họp. Mục này chỉ để tra cứu.',
                );
                return;
              }
              if (!selectedFolderId) {
                alert('Vui lòng chọn thư mục trước khi upload.');
                return;
              }
              setUploadOpen(true);
            }}
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            ↑ Upload
          </button>
        </div>

        {/* Main layout */}
        <div className="flex gap-4">

          {/* Mobile overlay */}
          {sidebarOpen && (
            <div
              className="fixed inset-0 bg-black/30 z-20 lg:hidden"
              onClick={() => setSidebarOpen(false)}
            />
          )}

          {/* Sidebar */}
          <aside
            className={[
              'fixed top-0 left-0 h-full z-30 bg-white shadow-xl w-72 p-4 overflow-y-auto transition-transform',
              'lg:static lg:shadow-none lg:z-auto lg:w-64 lg:translate-x-0',
              'lg:rounded-xl lg:border lg:border-gray-200 lg:self-start lg:sticky lg:top-4 lg:h-auto lg:min-h-96',
              sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
            ].join(' ')}
          >
            <div className="flex items-center justify-between mb-4 lg:hidden">
              <span className="font-semibold text-gray-800">Thư mục</span>
              <button onClick={() => setSidebarOpen(false)} className="text-gray-400 hover:text-gray-700 text-xl">×</button>
            </div>

            <h2 className="hidden lg:block text-sm font-semibold text-gray-700 mb-3">Thư mục</h2>

            {loadingFolders ? (
              <div className="space-y-2 animate-pulse">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="h-7 bg-gray-100 rounded-lg" />
                ))}
              </div>
            ) : (
              <FolderTree
                folders={cayHienThi}
                selectedId={selectedFolderId}
                onSelect={handleFolderSelect}
                onAdd={isAdmin ? () => alert('Tính năng tạo thư mục sẽ được thêm sau.') : undefined}
              />
            )}
          </aside>

          {/* Main content */}
          <div className="flex-1 min-w-0">

            {/* Controls */}
            <div className="bg-white rounded-xl border border-gray-200 p-3 mb-3 flex flex-wrap gap-3 items-center">
              <div className="relative flex-1 min-w-48">
                <input
                  type="text"
                  value={searchText}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  placeholder="Tìm tài liệu..."
                  className="w-full border border-gray-300 rounded-lg pl-9 pr-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                />
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">🔍</span>
              </div>

              <select
                value={filterType}
                onChange={(e) => handleFilterType(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              >
                {FILE_TYPE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>

              <div className="flex border border-gray-200 rounded-lg overflow-hidden">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`px-3 py-2 text-sm transition-colors ${viewMode === 'grid' ? 'bg-blue-600 text-white' : 'bg-white text-gray-500 hover:bg-gray-50'}`}
                  title="Grid"
                >
                  ⊞
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`px-3 py-2 text-sm transition-colors ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'bg-white text-gray-500 hover:bg-gray-50'}`}
                  title="List"
                >
                  ≡
                </button>
              </div>
            </div>

            {/* Files */}
            {laKhoHop(selectedFolderId) ? (
              <KhoTaiLieuHop
                nguon={nguonCuaKho(selectedFolderId)}
                timKiem={searchText}
              />
            ) : loadingFiles ? (
              viewMode === 'grid' ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} className="animate-pulse bg-white rounded-xl border border-gray-200 p-4">
                      <div className="w-12 h-12 bg-gray-200 rounded-xl mb-3" />
                      <div className="h-3 bg-gray-200 rounded w-4/5 mb-2" />
                      <div className="h-3 bg-gray-100 rounded w-3/5" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className="animate-pulse flex items-center gap-3 px-4 py-3 border-b border-gray-100">
                      <div className="w-8 h-8 bg-gray-200 rounded-lg flex-shrink-0" />
                      <div className="flex-1 h-4 bg-gray-200 rounded w-2/5" />
                    </div>
                  ))}
                </div>
              )
            ) : files.length === 0 ? (
              <div className="bg-white rounded-xl border border-gray-200 flex flex-col items-center justify-center py-16 text-center">
                <span className="text-4xl mb-3">📂</span>
                <p className="text-sm font-medium text-gray-600">
                  {selectedFolderId ? 'Thư mục này chưa có tài liệu' : 'Chưa có tài liệu nào'}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {selectedFolderId ? 'Nhấn "Upload" để thêm tài liệu đầu tiên' : 'Chọn thư mục để xem tài liệu'}
                </p>
              </div>
            ) : viewMode === 'grid' ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3">
                {files.map((f) => (
                  <FileCard
                    key={f.id}
                    file={f}
                    onDelete={canDelete(f) ? handleDelete : undefined}
                  />
                ))}
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                {files.map((f) => (
                  <FileListItem
                    key={f.id}
                    file={f}
                    onDelete={canDelete(f) ? handleDelete : undefined}
                  />
                ))}
              </div>
            )}

            {/* Pagination */}
            {pagination.total_pages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-4">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-colors"
                >
                  ← Trước
                </button>
                <span className="text-sm text-gray-500">{page} / {pagination.total_pages}</span>
                <button
                  disabled={page >= pagination.total_pages}
                  onClick={() => setPage((p) => p + 1)}
                  className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-colors"
                >
                  Sau →
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      <UploadModal
        open={uploadOpen}
        thuMucId={selectedFolderId ?? ''}
        onClose={() => setUploadOpen(false)}
        onSuccess={() => {
          setUploadOpen(false);
          fetchFiles();
        }}
      />
    </div>
  );
}
