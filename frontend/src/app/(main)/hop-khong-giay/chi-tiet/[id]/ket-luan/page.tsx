/**
 * Tab Kết luận — list + tạo + cập nhật tiến độ.
 *
 * G4-fix-4 (01/05/2026):
 * - Replace UUID plain input bằng CongChucPicker (single mode, search)
 * - Hide "Thêm nhiệm vụ" + "Cập nhật" khi cuộc họp HUY (isLocked)
 *   (Lưu ý: HOAN_THANH vẫn cho cập nhật tiến độ — quan trọng cho tracking)
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Plus, Loader2 } from 'lucide-react';
import { ketLuanApi } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import type { IKetLuan, MucUuTien } from '@/types/hkg';
import { useMeeting } from '@/components/hkg/MeetingContext';
import CongChucPicker from '@/components/hkg/CongChucPicker';

const UU_TIEN_BADGE: Record<MucUuTien, string> = {
  CAO: 'bg-red-100 text-red-800',
  TRUNG_BINH: 'bg-yellow-100 text-yellow-800',
  THAP: 'bg-gray-100 text-gray-700',
};

export default function KetLuanTabPage() {
  const { id } = useParams<{ id: string }>();
  const { ch, isCancelled, canEdit, currentUserId } = useMeeting();
  const [items, setItems] = useState<IKetLuan[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    noi_dung: '',
    nguoi_phu_trach_id: '',
    han_hoan_thanh: '',
    muc_uu_tien: 'TRUNG_BINH' as MucUuTien,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = async () => {
    try {
      setItems(await ketLuanApi.listByCuocHop(id));
    } catch (e: unknown) { setError(errMsg(e)); }
  };

  useEffect(() => { fetch(); }, [id]);

  const handleCreate = async () => {
    setBusy(true);
    setError(null);
    try {
      await ketLuanApi.tao(id, {
        noi_dung: form.noi_dung,
        nguoi_phu_trach_id: form.nguoi_phu_trach_id,
        han_hoan_thanh: form.han_hoan_thanh || null,
        muc_uu_tien: form.muc_uu_tien,
      });
      setForm({ noi_dung: '', nguoi_phu_trach_id: '', han_hoan_thanh: '', muc_uu_tien: 'TRUNG_BINH' });
      setShowForm(false);
      await fetch();
    } catch (e: unknown) { setError(errMsg(e)); }
    finally { setBusy(false); }
  };

  const handleUpdateProgress = async (klId: string) => {
    const v = window.prompt('Tiến độ % mới (0-100)?');
    if (!v) return;
    const n = parseInt(v, 10);
    if (isNaN(n) || n < 0 || n > 100) return;
    try {
      await ketLuanApi.capNhatTienDo(klId, { phan_tram_sau: n, mo_ta: `Cập nhật tiến độ ${n}%` });
      await fetch();
    } catch (e: unknown) { setError(errMsg(e)); }
  };

  // Filter scope của picker theo đơn vị tổ chức (UX nhanh)
  const donViScope = ch?.don_vi_to_chuc_id || null;

  return (
    <div className="bg-white border rounded p-6 space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Kết luận / Nhiệm vụ</h3>
        {/* G4-fix-7: ẨN "Thêm nhiệm vụ" cho CBCC thường */}
        {canEdit && !isCancelled && (
          <button
            onClick={() => setShowForm(!showForm)}
            className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" /> Thêm nhiệm vụ
          </button>
        )}
      </div>

      {error && <div className="p-3 bg-red-50 border border-red-200 rounded text-red-800 text-sm">{error}</div>}

      {showForm && canEdit && !isCancelled && (
        <div className="p-4 border-2 border-dashed rounded space-y-3 bg-gray-50">
          <textarea
            placeholder="Nội dung nhiệm vụ"
            value={form.noi_dung}
            onChange={(e) => setForm({ ...form, noi_dung: e.target.value })}
            className="w-full px-3 py-2 border rounded text-sm"
            rows={2}
          />

          <div>
            <label className="block text-xs font-medium mb-1 text-gray-700">
              Người phụ trách *
            </label>
            <CongChucPicker
              multiple={false}
              value={form.nguoi_phu_trach_id || null}
              onChange={(id) => setForm({ ...form, nguoi_phu_trach_id: id || '' })}
              donViId={donViScope}
              placeholder="Tìm CBCC theo tên hoặc mã..."
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium mb-1 text-gray-700">Hạn hoàn thành</label>
              <input
                type="date"
                value={form.han_hoan_thanh}
                onChange={(e) => setForm({ ...form, han_hoan_thanh: e.target.value })}
                className="w-full px-3 py-2 border rounded text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1 text-gray-700">Mức ưu tiên</label>
              <select
                value={form.muc_uu_tien}
                onChange={(e) => setForm({ ...form, muc_uu_tien: e.target.value as MucUuTien })}
                className="w-full px-3 py-2 border rounded text-sm"
              >
                <option value="CAO">Cao</option>
                <option value="TRUNG_BINH">Trung bình</option>
                <option value="THAP">Thấp</option>
              </select>
            </div>
          </div>

          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-4 py-2 border rounded text-sm"
            >
              Hủy
            </button>
            <button
              onClick={handleCreate}
              disabled={busy || !form.noi_dung || !form.nguoi_phu_trach_id}
              className="inline-flex items-center gap-1 px-4 py-2 bg-green-600 text-white rounded text-sm disabled:opacity-50"
            >
              {busy && <Loader2 className="w-4 h-4 animate-spin" />}
              Tạo nhiệm vụ
            </button>
          </div>
        </div>
      )}

      {items.length === 0 ? (
        <div className="text-center py-8 text-gray-500">Chưa có kết luận nào.</div>
      ) : (
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left">Nội dung</th>
              <th className="px-3 py-2 text-left">Hạn</th>
              <th className="px-3 py-2 text-left">Ưu tiên</th>
              <th className="px-3 py-2 text-left">Tiến độ</th>
              <th className="px-3 py-2 text-left">Trạng thái</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {items.map((kl) => (
              <tr key={kl.id} className="hover:bg-gray-50">
                <td className="px-3 py-2 max-w-md">{kl.noi_dung}</td>
                <td className="px-3 py-2">{kl.han_hoan_thanh || '—'}</td>
                <td className="px-3 py-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${UU_TIEN_BADGE[kl.muc_uu_tien]}`}>
                    {kl.muc_uu_tien}
                  </span>
                </td>
                <td className="px-3 py-2">
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-600" style={{ width: `${kl.tien_do_phan_tram}%` }} />
                    </div>
                    <span className="text-xs">{kl.tien_do_phan_tram}%</span>
                  </div>
                </td>
                <td className="px-3 py-2 text-xs">{kl.trang_thai}</td>
                <td className="px-3 py-2">
                  {/* "Cập nhật" chỉ cho người phụ trách hoặc admin/canEdit */}
                  {!isCancelled
                    && kl.trang_thai !== 'HOAN_THANH'
                    && (canEdit || kl.nguoi_phu_trach_id === currentUserId) && (
                    <button onClick={() => handleUpdateProgress(kl.id)} className="text-blue-600 text-xs hover:underline">
                      Cập nhật
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
