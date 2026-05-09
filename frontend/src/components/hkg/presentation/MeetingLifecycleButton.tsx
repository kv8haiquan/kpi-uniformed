'use client';

/**
 * MeetingLifecycleButton — chuyển trạng thái cuộc họp.
 *
 * Phase 4.1 FE_P3.
 *
 * Hiển thị nút theo trang_thai hiện tại:
 *  - LEN_KE_HOACH / DA_THONG_BAO → "Bắt đầu họp" (POST /bat-dau)
 *  - DANG_DIEN_RA               → "Kết thúc họp" (POST /ket-thuc)
 *  - HOAN_THANH / HUY           → ẩn
 *
 * Chỉ hiện cho host (canEdit). Confirm trước khi gọi vì action mutating
 * sẽ broadcast meeting_ended cho tất cả WS đang mở.
 */

import { useState } from 'react';
import { Loader2, Play, StopCircle } from 'lucide-react';

import { cuocHopApi } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import type { TrangThaiCuocHop } from '@/types/hkg';

interface Props {
  cuocHopId: string;
  trangThai: TrangThaiCuocHop;
  canEdit: boolean;
  /** Callback gọi sau khi action thành công để refresh layout context. */
  onChanged: () => void;
  onError?: (msg: string) => void;
}

export function MeetingLifecycleButton({
  cuocHopId,
  trangThai,
  canEdit,
  onChanged,
  onError,
}: Props) {
  const [busy, setBusy] = useState(false);

  if (!canEdit) return null;
  if (trangThai === 'HOAN_THANH' || trangThai === 'HUY') return null;

  const isStartable = trangThai === 'LEN_KE_HOACH' || trangThai === 'DA_THONG_BAO';
  const isEndable = trangThai === 'DANG_DIEN_RA';
  if (!isStartable && !isEndable) return null;

  const handleClick = async () => {
    const confirmMsg = isStartable
      ? 'Bắt đầu cuộc họp ngay bây giờ?'
      : 'Kết thúc cuộc họp? Phiên trình chiếu (nếu có) sẽ tự đóng.';
    if (!window.confirm(confirmMsg)) return;

    setBusy(true);
    try {
      if (isStartable) await cuocHopApi.batDau(cuocHopId);
      else await cuocHopApi.ketThuc(cuocHopId);
      onChanged();
    } catch (e: unknown) {
      onError?.(errMsg(e, 'Lỗi chuyển trạng thái cuộc họp'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={busy}
      className={`inline-flex items-center gap-2 px-4 py-2 rounded text-sm font-medium text-white disabled:opacity-50 ${
        isStartable ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
      }`}
    >
      {busy ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : isStartable ? (
        <Play className="w-4 h-4" />
      ) : (
        <StopCircle className="w-4 h-4" />
      )}
      {isStartable ? 'Bắt đầu họp' : 'Kết thúc họp'}
    </button>
  );
}

export default MeetingLifecycleButton;
