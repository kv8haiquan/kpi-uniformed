/**
 * Tab Tài liệu — upload + list + xem/tải.
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Upload, Eye, Download, Trash2, Loader2 } from 'lucide-react';
import { taiLieuApi } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import type { ITaiLieuListItem } from '@/types/hkg';
import { useMeeting } from '@/components/hkg/MeetingContext';

export default function TaiLieuTabPage() {
  const { id } = useParams<{ id: string }>();
  const { isLocked, canEdit } = useMeeting();
  const [items, setItems] = useState<ITaiLieuListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const handleView = async (taiLieuId: string, ten: string) => {
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

  return (
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
            {items.map((tl) => (
              <tr key={tl.id} className="hover:bg-gray-50">
                <td className="px-3 py-2">{tl.ten_tai_lieu}</td>
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
                <td className="px-3 py-2 flex gap-2">
                  <button onClick={() => handleView(tl.id, tl.ten_tai_lieu)} className="p-1 hover:bg-gray-100 rounded" title="Xem">
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
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
