'use client';

/**
 * ToggleModeButton — đại biểu bấm để vào/ra chế độ xem độc lập.
 *
 * Phase 4.1 FE_P3. Vào độc lập: tách khỏi sync, viewer tự navigate.
 * Ra: parent show ConfirmReturnDialog trước khi gọi onReturnToSync.
 */

import { Eye, EyeOff } from 'lucide-react';

interface Props {
  independentMode: boolean;
  onToggle: () => void;
  disabled?: boolean;
}

export function ToggleModeButton({ independentMode, onToggle, disabled = false }: Props) {
  return (
    <button
      onClick={onToggle}
      disabled={disabled}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium border disabled:opacity-50 ${
        independentMode
          ? 'bg-blue-600 text-white border-blue-600 hover:bg-blue-700'
          : 'bg-white text-purple-700 border-purple-300 hover:bg-purple-50'
      }`}
      title={
        independentMode
          ? 'Quay về xem theo chủ tọa'
          : 'Tách khỏi đồng bộ, tự xem trang'
      }
    >
      {independentMode ? (
        <>
          <EyeOff className="w-4 h-4" />
          Quay về đồng bộ
        </>
      ) : (
        <>
          <Eye className="w-4 h-4" />
          Xem độc lập
        </>
      )}
    </button>
  );
}

export default ToggleModeButton;
