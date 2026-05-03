/**
 * SuaThanhPhanModalById — wrapper fetch ICuocHop theo id rồi render
 * SuaThanhPhanModal. Cho phép mở từ list view (chỉ có id, không có ch).
 */

'use client';

import { useEffect, useState } from 'react';
import { Loader2, X } from 'lucide-react';
import { cuocHopApi } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import type { ICuocHop } from '@/types/hkg';
import SuaThanhPhanModal from './SuaThanhPhanModal';

interface IProps {
  cuocHopId: string;
  onClose: () => void;
  onSaved: () => void;
}

export default function SuaThanhPhanModalById({ cuocHopId, onClose, onSaved }: IProps) {
  const [ch, setCh] = useState<ICuocHop | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const data = await cuocHopApi.chiTiet(cuocHopId);
        if (!cancelled) setCh(data);
      } catch (e: unknown) {
        if (!cancelled) setError(errMsg(e, 'Lỗi tải cuộc họp'));
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [cuocHopId]);

  if (ch) {
    return <SuaThanhPhanModal ch={ch} onClose={onClose} onSaved={onSaved} />;
  }

  // Loading / error state — overlay nhỏ
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-4">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-base font-semibold">
            {error ? 'Không tải được cuộc họp' : 'Đang tải cuộc họp...'}
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded" aria-label="Đóng">
            <X className="w-5 h-5" />
          </button>
        </div>
        {error ? (
          <p className="p-3 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
            {error}
          </p>
        ) : (
          <div className="flex items-center gap-2 text-gray-500 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" /> Đang tải...
          </div>
        )}
      </div>
    </div>
  );
}
