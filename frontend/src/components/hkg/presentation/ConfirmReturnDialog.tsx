'use client';

/**
 * ConfirmReturnDialog — xác nhận quay về chế độ đồng bộ.
 *
 * Phase 4.1 FE_P3. Đại biểu khi quay về sync sẽ jump trang tới host. Dialog
 * confirm để tránh người dùng vô tình mất vị trí đang đọc.
 */

import { AlertTriangle } from 'lucide-react';

interface Props {
  open: boolean;
  hostPage: number;
  localPage: number;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmReturnDialog({
  open,
  hostPage,
  localPage,
  onConfirm,
  onCancel,
}: Props) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={onCancel}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-6 h-6 text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900">Quay về đồng bộ?</h3>
            <p className="text-sm text-gray-600 mt-2">
              Bạn đang ở trang <strong>{localPage}</strong>. Chế độ đồng bộ sẽ
              chuyển ngay tới trang <strong>{hostPage}</strong> (chủ tọa).
            </p>
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-6">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
          >
            Hủy
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Quay về đồng bộ
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmReturnDialog;
