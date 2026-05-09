/**
 * Tab Tài liệu — Phase 4.1 page-sync.
 *
 * - Khi cuộc họp DA_THONG_BAO/DANG_DIEN_RA: hook usePresentationSync mở WS
 *   để host trình chiếu + đại biểu xem theo trang chủ tọa.
 * - !is_active → list tài liệu + host bấm "Trình chiếu" để start.
 * - is_active  → PresentationViewer khớp trang theo state WS (đại biểu sync).
 *   Đại biểu có thể bấm "Xem độc lập" để tách khỏi sync (local FE state).
 */

'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { Upload, Eye, Download, Trash2, Loader2, Play, StopCircle, RefreshCw } from 'lucide-react';

import { taiLieuApi } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import type { ITaiLieuListItem } from '@/types/hkg';
import { useMeeting } from '@/components/hkg/MeetingContext';
import { usePresentationSync } from '@/hooks/usePresentationSync';
import PresentationViewerLazy from '@/components/hkg/presentation/PresentationViewerLazy';
import { MeetingLifecycleButton } from '@/components/hkg/presentation/MeetingLifecycleButton';
import { SyncStatusBadge } from '@/components/hkg/presentation/SyncStatusBadge';
import { IndependentViewBanner } from '@/components/hkg/presentation/IndependentViewBanner';
import { ConfirmReturnDialog } from '@/components/hkg/presentation/ConfirmReturnDialog';
import { ToggleModeButton } from '@/components/hkg/presentation/ToggleModeButton';

// Trạng thái cuộc họp mà WS endpoint chấp nhận token (khớp BE
// _VALID_STATES_FOR_TOKEN ở presentation_rest.py).
const SYNC_ENABLED_STATES = ['DA_THONG_BAO', 'DANG_DIEN_RA'] as const;

export default function TaiLieuTabPage() {
  const { id } = useParams<{ id: string }>();
  const { ch, isLocked, canEdit, refresh } = useMeeting();

  const [items, setItems] = useState<ITaiLieuListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Phase 4.1: WS sync
  const syncEnabled = !!ch && (SYNC_ENABLED_STATES as readonly string[]).includes(ch.trang_thai);
  const sync = usePresentationSync({ cuocHopId: id, enabled: syncEnabled });

  // Local FE state cho đại biểu xem độc lập
  const [independentMode, setIndependentMode] = useState(false);
  const [localPage, setLocalPage] = useState<number>(1);
  const [showReturnDialog, setShowReturnDialog] = useState(false);

  // Signed URL của tài liệu đang trình chiếu (re-fetch khi taiLieuId đổi)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfUrlLoading, setPdfUrlLoading] = useState(false);

  // ────────────────────────────────────────────────────────────
  // Fetch list documents
  // ────────────────────────────────────────────────────────────
  const fetchList = async () => {
    setLoading(true);
    try {
      const list = await taiLieuApi.listByCuocHop(id);
      setItems(list);
    } catch (e: unknown) {
      setError(errMsg(e, 'Lỗi tải'));
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { fetchList(); }, [id]);

  // ────────────────────────────────────────────────────────────
  // Re-fetch signed URL khi tài liệu trình chiếu đổi
  // ────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!sync.state.taiLieuId) {
      setPdfUrl(null);
      return;
    }
    let cancelled = false;
    setPdfUrlLoading(true);
    taiLieuApi
      .xemUrl(sync.state.taiLieuId)
      .then((r) => { if (!cancelled) setPdfUrl(r.url); })
      .catch((e: unknown) => { if (!cancelled) setError(errMsg(e, 'Lỗi tải URL tài liệu')); })
      .finally(() => { if (!cancelled) setPdfUrlLoading(false); });
    return () => { cancelled = true; };
  }, [sync.state.taiLieuId]);

  // ────────────────────────────────────────────────────────────
  // Page hiệu lực cho viewer (sync hay độc lập)
  // ────────────────────────────────────────────────────────────
  const viewerPage = useMemo(
    () => (independentMode ? localPage : sync.state.page),
    [independentMode, localPage, sync.state.page],
  );

  // ────────────────────────────────────────────────────────────
  // Document actions (upload/delete vẫn như cũ)
  // ────────────────────────────────────────────────────────────
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await taiLieuApi.upload({ cuoc_hop_id: id, file });
      await fetchList();
    } catch (err: unknown) {
      setError(errMsg(err, 'Upload lỗi'));
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  // Đại biểu xem doc cũ ở tab mới (khi !is_active hoặc preview riêng)
  const handleOpenInTab = async (taiLieuId: string, ten: string) => {
    try {
      const r = await taiLieuApi.xemUrl(taiLieuId);
      const previewUrl = `/hop-khong-giay/xem-tai-lieu?url=${encodeURIComponent(r.url)}&ten=${encodeURIComponent(ten)}`;
      window.open(previewUrl, '_blank');
    } catch (e: unknown) { setError(errMsg(e)); }
  };

  const handleDownload = async (taiLieuId: string) => {
    try {
      const r = await taiLieuApi.taiUrl(taiLieuId);
      window.open(r.url, '_blank');
    } catch (e: unknown) { setError(errMsg(e)); }
  };

  const handleDelete = async (taiLieuId: string) => {
    if (!confirm('Xóa tài liệu này?')) return;
    try {
      await taiLieuApi.xoa(taiLieuId);
      await fetchList();
    } catch (e: unknown) { setError(errMsg(e)); }
  };

  // ────────────────────────────────────────────────────────────
  // Presentation actions (host)
  // ────────────────────────────────────────────────────────────
  const handleStartPresent = (taiLieuId: string) => {
    if (!sync.isHost) return;
    if (!sync.state.isActive) sync.startPresentation(taiLieuId, 1);
    else sync.changeDocument(taiLieuId, 1);
  };

  const handleEndPresent = () => sync.endPresentation();

  const handleHostPageChange = (page: number) => {
    if (sync.isHost && !independentMode) sync.changePage(page);
  };

  // ────────────────────────────────────────────────────────────
  // Đại biểu independent mode
  // ────────────────────────────────────────────────────────────
  const handleEnterIndependent = () => {
    setLocalPage(sync.state.page); // start tại trang host
    setIndependentMode(true);
  };
  const handleAskReturn = () => setShowReturnDialog(true);
  const handleConfirmReturn = () => {
    setIndependentMode(false);
    setShowReturnDialog(false);
  };
  const handleLocalPageChange = (page: number) => setLocalPage(page);

  // Khi viewer có cả hai role: host (gửi page_change) hoặc đại biểu độc lập
  // (chỉ update local). Đại biểu sync thì không có nút Prev/Next.
  const viewerIsControllable = sync.isHost || independentMode;
  const onViewerPageChange = sync.isHost
    ? handleHostPageChange
    : independentMode
      ? handleLocalPageChange
      : undefined;

  // ────────────────────────────────────────────────────────────
  // Render
  // ────────────────────────────────────────────────────────────
  return (
    <div className="space-y-4">
      {/* Toolbar trên cùng: Lifecycle + sync status */}
      {ch && (
        <div className="bg-white border rounded p-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3 flex-wrap">
            <MeetingLifecycleButton
              cuocHopId={id}
              trangThai={ch.trang_thai}
              canEdit={canEdit}
              onChanged={refresh}
              onError={setError}
            />
            {syncEnabled && (
              <SyncStatusBadge
                status={sync.status}
                hostOnline={sync.state.hostOnline}
                independentMode={independentMode}
              />
            )}
          </div>

          {syncEnabled && sync.state.isActive && sync.isHost && (
            <button
              onClick={handleEndPresent}
              className="inline-flex items-center gap-2 px-3 py-1.5 bg-red-600 text-white rounded text-sm hover:bg-red-700"
            >
              <StopCircle className="w-4 h-4" />
              Kết thúc trình chiếu
            </button>
          )}

          {syncEnabled && sync.state.isActive && !sync.isHost && (
            <ToggleModeButton
              independentMode={independentMode}
              onToggle={independentMode ? handleAskReturn : handleEnterIndependent}
              disabled={sync.status === 'closed' || sync.status === 'error'}
            />
          )}
        </div>
      )}

      {/* Banner khi đại biểu xem độc lập */}
      {independentMode && sync.state.isActive && !sync.isHost && (
        <IndependentViewBanner
          localPage={localPage}
          hostPage={sync.state.page}
          totalPages={0 /* viewer tự biết, banner hiển thị ước lượng */}
          onReturnToSync={handleAskReturn}
        />
      )}

      {/* Lỗi WS */}
      {sync.lastError && (
        <div className="p-3 bg-amber-50 border border-amber-300 rounded text-amber-800 text-sm">
          {sync.lastError}
        </div>
      )}

      {/* Viewer khi đang trình chiếu */}
      {sync.state.isActive && (
        <div className="bg-white border rounded p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Play className="w-4 h-4 text-green-600" />
            Đang trình chiếu
            {pdfUrlLoading && <Loader2 className="w-3.5 h-3.5 animate-spin text-gray-400" />}
          </h3>
          {pdfUrl ? (
            <PresentationViewerLazy
              url={pdfUrl}
              currentPage={viewerPage}
              isHost={viewerIsControllable}
              onPageChange={onViewerPageChange}
            />
          ) : pdfUrlLoading ? (
            <div className="h-64 flex items-center justify-center text-gray-500">
              <Loader2 className="w-5 h-5 animate-spin mr-2" /> Đang tải tài liệu...
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              Không có tài liệu để hiển thị
            </div>
          )}
        </div>
      )}

      {/* List tài liệu — luôn hiển thị để upload/quản lý */}
      <div className="bg-white border rounded p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium">Tài liệu cuộc họp</h3>
          {canEdit && !isLocked && (
            <label className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded text-sm cursor-pointer hover:bg-blue-700">
              {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
              Upload tài liệu
              <input type="file" className="hidden" onChange={handleUpload} disabled={uploading} />
            </label>
          )}
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-gray-500">Đang tải...</div>
        ) : items.length === 0 ? (
          <div className="text-gray-500 text-center py-8">Chưa có tài liệu nào.</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left">Tên file</th>
                <th className="px-3 py-2 text-left">Loại</th>
                <th className="px-3 py-2 text-left">Kích thước</th>
                <th className="px-3 py-2 text-left">Phân quyền</th>
                <th className="px-3 py-2 text-left">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {items.map((tl) => {
                const isCurrent = sync.state.taiLieuId === tl.id;
                const canPresent =
                  syncEnabled &&
                  sync.isHost &&
                  // chỉ PDF mới render được trong PresentationViewer
                  tl.extension?.toLowerCase() === 'pdf';
                return (
                  <tr key={tl.id} className={`hover:bg-gray-50 ${isCurrent ? 'bg-green-50/50' : ''}`}>
                    <td className="px-3 py-2">
                      {tl.ten_tai_lieu}
                      {isCurrent && (
                        <span className="ml-2 px-1.5 py-0.5 bg-green-600 text-white text-[10px] rounded">
                          ĐANG CHIẾU
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 uppercase text-xs">{tl.extension}</td>
                    <td className="px-3 py-2">{(tl.file_size / 1024).toFixed(1)} KB</td>
                    <td className="px-3 py-2">
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        tl.phan_quyen === 'CONG_KHAI'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {tl.phan_quyen}
                      </span>
                    </td>
                    <td className="px-3 py-2 flex flex-wrap gap-2">
                      {canPresent && (
                        <button
                          onClick={() => handleStartPresent(tl.id)}
                          className="inline-flex items-center gap-1 px-2 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700"
                          title={sync.state.isActive ? 'Chuyển sang tài liệu này' : 'Bắt đầu trình chiếu'}
                        >
                          {sync.state.isActive ? <RefreshCw className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                          {sync.state.isActive ? 'Đổi' : 'Trình chiếu'}
                        </button>
                      )}
                      <button onClick={() => handleOpenInTab(tl.id, tl.ten_tai_lieu)} className="p-1 hover:bg-gray-100 rounded" title="Xem ở tab mới">
                        <Eye className="w-4 h-4 text-blue-600" />
                      </button>
                      {tl.cho_phep_tai && (
                        <button onClick={() => handleDownload(tl.id)} className="p-1 hover:bg-gray-100 rounded" title="Tải">
                          <Download className="w-4 h-4 text-green-600" />
                        </button>
                      )}
                      {canEdit && !isLocked && (
                        <button onClick={() => handleDelete(tl.id)} className="p-1 hover:bg-gray-100 rounded" title="Xóa">
                          <Trash2 className="w-4 h-4 text-red-600" />
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <ConfirmReturnDialog
        open={showReturnDialog}
        hostPage={sync.state.page}
        localPage={localPage}
        onConfirm={handleConfirmReturn}
        onCancel={() => setShowReturnDialog(false)}
      />
    </div>
  );
}
