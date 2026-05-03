/**
 * /hop-khong-giay/xin-phep-vang — 2 tab: Đơn của tôi (TODO), Chờ duyệt (chu_toa).
 * MVP: chỉ tab Chờ duyệt.
 */

'use client';

import { useEffect, useState } from 'react';
import { Loader2, Check, X } from 'lucide-react';
import { xinPhepApi } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import type { IXinPhepVang } from '@/types/hkg';

export default function XinPhepVangPage() {
  const [items, setItems] = useState<IXinPhepVang[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = async () => {
    setLoading(true);
    try {
      setItems(await xinPhepApi.choDuyet());
    } catch (e: unknown) { setError(errMsg(e)); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetch(); }, []);

  const handleDuyet = async (id: string, quyet_dinh: 'DA_DUYET' | 'TU_CHOI') => {
    let ly_do: string | undefined;
    if (quyet_dinh === 'TU_CHOI') {
      ly_do = window.prompt('Lý do từ chối?') || 'Không nhập';
    }
    try {
      await xinPhepApi.duyet(id, quyet_dinh, ly_do);
      await fetch();
    } catch (e: unknown) { setError(errMsg(e)); }
  };

  return (
    <div>
      <h2 className="text-lg font-medium mb-4">Đơn xin vắng chờ duyệt</h2>

      {error && <div className="p-3 bg-red-50 border rounded text-red-800 text-sm mb-4">{error}</div>}

      {loading ? (
        <div className="flex items-center gap-2 text-gray-500">
          <Loader2 className="w-4 h-4 animate-spin" /> Đang tải...
        </div>
      ) : items.length === 0 ? (
        <div className="bg-white border rounded p-8 text-center text-gray-500">
          Không có đơn nào chờ duyệt.
        </div>
      ) : (
        <div className="bg-white border rounded">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left">CBCC</th>
                <th className="px-3 py-2 text-left">Lý do</th>
                <th className="px-3 py-2 text-left">Ngày gửi</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {items.map((x) => (
                <tr key={x.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2 font-mono text-xs">{x.cong_chuc_id.substring(0, 8)}...</td>
                  <td className="px-3 py-2">{x.ly_do}</td>
                  <td className="px-3 py-2">{x.created_at}</td>
                  <td className="px-3 py-2 flex gap-2">
                    <button
                      onClick={() => handleDuyet(x.id, 'DA_DUYET')}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                    >
                      <Check className="w-3 h-3" /> Duyệt
                    </button>
                    <button
                      onClick={() => handleDuyet(x.id, 'TU_CHOI')}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
                    >
                      <X className="w-3 h-3" /> Từ chối
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
