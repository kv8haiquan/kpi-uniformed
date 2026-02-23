/**
 * DashboardWidget.tsx
 * ====================
 * Wrapper chung cho tất cả widget trên trang Tổng quan.
 *
 * States: loading (skeleton) → loaded (children) → error (fallback)
 * Mỗi widget là một card với header (icon + title + link) và body content.
 */

import Link from 'next/link';

// =============================================================================
// TYPES
// =============================================================================

interface DashboardWidgetProps {
  title: string;
  icon: string;
  href?: string;          // Link "xem thêm" ở header
  hrefLabel?: string;     // Label cho link (default "Xem thêm")
  loading?: boolean;
  error?: boolean;
  fallbackMessage?: string;
  children?: React.ReactNode;
  colorClass?: string;    // Tailwind bg class cho icon bg
  className?: string;     // Extra class cho card
}

// =============================================================================
// SKELETON
// =============================================================================

export function WidgetSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="animate-pulse space-y-3">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-gray-200 flex-shrink-0" />
          <div className="flex-1 space-y-1">
            <div className="h-3 bg-gray-200 rounded w-3/4" />
            <div className="h-2 bg-gray-100 rounded w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

// =============================================================================
// MAIN WIDGET WRAPPER
// =============================================================================

export default function DashboardWidget({
  title,
  icon,
  href,
  hrefLabel = 'Xem thêm',
  loading = false,
  error = false,
  fallbackMessage,
  children,
  colorClass = 'bg-blue-100',
  className = '',
}: DashboardWidgetProps) {
  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <span className={`${colorClass} rounded-lg w-8 h-8 flex items-center justify-center text-base flex-shrink-0`}>
            {icon}
          </span>
          <span className="font-semibold text-gray-800 text-sm">{title}</span>
        </div>
        {href && (
          <Link
            href={href}
            className="text-xs text-blue-600 hover:text-blue-800 hover:underline transition-colors"
          >
            {hrefLabel} &rarr;
          </Link>
        )}
      </div>

      {/* Body */}
      <div className="p-4 flex-1">
        {loading ? (
          <WidgetSkeleton />
        ) : error || fallbackMessage ? (
          <div className="flex flex-col items-center justify-center py-4 text-center">
            <span className="text-2xl mb-2">🚧</span>
            <p className="text-xs text-gray-400">
              {fallbackMessage ?? 'Đang phát triển'}
            </p>
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  );
}
