'use client';

/**
 * SyncStatusBadge — hiển thị trạng thái đồng bộ trình chiếu.
 *
 * Phase 4.1 FE_P3.
 *
 * Map ConnectionStatus + independentMode + hostDisconnected → badge UI:
 *  - independent  → tím (đại biểu đang xem độc lập)
 *  - error/closed → đỏ (mất kết nối, người dùng cần reload)
 *  - reconnecting → vàng nhấp nháy
 *  - connected + hostOffline → xám (chờ host)
 *  - connected + hostOnline  → xanh (đang đồng bộ)
 *  - connecting/idle         → xám (đang khởi tạo)
 */

import { Wifi, WifiOff, RefreshCw, Eye, AlertTriangle } from 'lucide-react';
import type { ConnectionStatus } from '@/types/hkg-presentation';

interface Props {
  status: ConnectionStatus;
  hostOnline: boolean;
  /** True khi đại biểu đã chuyển sang chế độ độc lập (local FE state). */
  independentMode?: boolean;
  className?: string;
}

export function SyncStatusBadge({
  status,
  hostOnline,
  independentMode = false,
  className = '',
}: Props) {
  let label: string;
  let color: string;
  let Icon: React.ComponentType<{ className?: string }>;
  let pulse = false;

  if (independentMode) {
    label = 'Đang xem độc lập';
    color = 'bg-purple-100 text-purple-800 border-purple-300';
    Icon = Eye;
  } else if (status === 'error') {
    label = 'Mất kết nối';
    color = 'bg-red-100 text-red-800 border-red-300';
    Icon = AlertTriangle;
  } else if (status === 'closed') {
    label = 'Đã đóng';
    color = 'bg-gray-100 text-gray-700 border-gray-300';
    Icon = WifiOff;
  } else if (status === 'reconnecting') {
    label = 'Đang kết nối lại...';
    color = 'bg-yellow-100 text-yellow-800 border-yellow-300';
    Icon = RefreshCw;
    pulse = true;
  } else if (status === 'connecting' || status === 'idle') {
    label = 'Đang kết nối...';
    color = 'bg-gray-100 text-gray-600 border-gray-300';
    Icon = RefreshCw;
    pulse = true;
  } else if (!hostOnline) {
    label = 'Chờ chủ tọa';
    color = 'bg-amber-50 text-amber-700 border-amber-300';
    Icon = WifiOff;
  } else {
    label = 'Đang đồng bộ';
    color = 'bg-green-100 text-green-800 border-green-300';
    Icon = Wifi;
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 border rounded-full text-xs font-medium ${color} ${className}`}
    >
      <Icon className={`w-3.5 h-3.5 ${pulse ? 'animate-spin' : ''}`} />
      {label}
    </span>
  );
}

export default SyncStatusBadge;
