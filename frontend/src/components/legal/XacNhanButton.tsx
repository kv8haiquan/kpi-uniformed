/**
 * src/components/legal/XacNhanButton.tsx
 * =========================================
 * Nút "Xác nhận đã đọc và hiểu" cho văn bản pháp luật.
 * - Disable và hiển thị badge ✅ khi đã xác nhận
 * - Loading spinner khi đang gửi
 * - Gọi callback onSuccess khi xác nhận thành công
 */

'use client';

import { useState } from 'react';
import { legalService } from '@/services/legal';

interface XacNhanButtonProps {
  vanBanId: string;
  daXacNhan: boolean;
  onSuccess?: () => void;
}

export function XacNhanButton({ vanBanId, daXacNhan, onSuccess }: XacNhanButtonProps) {
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(daXacNhan);
  const [error, setError] = useState('');

  const handleXacNhan = async () => {
    if (done || loading) return;
    setLoading(true);
    setError('');
    try {
      await legalService.xacNhanDoc(vanBanId, { da_xac_nhan: true });
      setDone(true);
      onSuccess?.();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: { error?: { message?: string } } } } };
      setError(e?.response?.data?.detail?.error?.message || 'Không thể xác nhận. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };

  // Đã xác nhận — hiển thị badge thành công
  if (done) {
    return (
      <div className="flex items-center gap-2 px-5 py-3 bg-green-50 text-green-700 border border-green-200 rounded-xl">
        <span className="text-xl">✅</span>
        <div>
          <div className="font-semibold">Đã xác nhận đã đọc và hiểu</div>
          <div className="text-xs text-green-600 mt-0.5">Cảm ơn bạn đã hoàn thành xác nhận</div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <button
        onClick={handleXacNhan}
        disabled={loading}
        className="flex items-center gap-2 px-5 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed text-white rounded-xl font-medium transition-colors shadow-sm"
      >
        {loading ? (
          <>
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            <span>Đang xác nhận...</span>
          </>
        ) : (
          <>
            <span className="text-lg">✅</span>
            <span>Xác nhận đã đọc và hiểu</span>
          </>
        )}
      </button>
      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
