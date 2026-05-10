'use client';

/**
 * components/common/MauSoDisplay.tsx
 * ==================================
 * Helper component hiển thị "mẫu số" theo phiên bản KPI (V1 hoặc V2_PL3).
 *
 * V1: ngày làm việc × 96 SP/ngày (hardcode V1 cũ).
 * V2_PL3: tổng SP công chức kê khai (đã duyệt).
 *
 * Default fallback V1 nếu version không được truyền.
 */

import { Info } from 'lucide-react';

import { formatScore } from '@/lib/format';
type KpiVersion = 'V1' | 'V2_PL3' | undefined | null;

interface Props {
  version?: KpiVersion;
  /**
   * V1 inputs.
   */
  soNgayLamViec?: number | null;
  /**
   * V2 input — tổng SP CC đã kê khai (mẫu số V2).
   */
  tongSpKeKhai?: number | null;

  className?: string;
  showLabel?: boolean;
}

export function MauSoDisplay({
  version,
  soNgayLamViec,
  tongSpKeKhai,
  className,
  showLabel = true,
}: Props) {
  const isV2 = version === 'V2_PL3';

  if (isV2) {
    const tong = tongSpKeKhai ?? 0;
    return (
      <div className={className}>
        {showLabel && (
          <span className="text-xs text-gray-500">Tổng điểm kê khai:</span>
        )}{' '}
        <strong className="text-blue-700">{formatScore(tong)}</strong>
        <span className="ml-1 text-xs text-gray-500">điểm</span>
      </div>
    );
  }

  // V1 (default fallback)
  const ngay = Number(soNgayLamViec ?? 0);
  const target = ngay * 96;
  return (
    <div className={className}>
      {showLabel && <span className="text-xs text-gray-500">Điểm được giao:</span>}{' '}
      <strong>{target}</strong>
      <span className="ml-1 text-xs text-gray-500">
        ({ngay} ngày × 96)
      </span>
    </div>
  );
}

interface VersionBadgeProps {
  version?: KpiVersion;
  className?: string;
}

/**
 * Badge nhỏ để hiển thị phiên bản KPI ở header trang đánh giá / xếp loại.
 */
export function KpiVersionBadge({ version, className }: VersionBadgeProps) {
  const v = version ?? 'V1';
  const isV2 = v === 'V2_PL3';
  return (
    <span
      className={[
        'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium',
        isV2 ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-700',
        className ?? '',
      ].join(' ')}
      title={
        isV2
          ? 'Mẫu số = tổng điểm công chức kê khai (đã duyệt)'
          : 'Mẫu số = số ngày làm việc × 96'
      }
    >
      <Info className="h-3 w-3" />
      KPI {v}
    </span>
  );
}
