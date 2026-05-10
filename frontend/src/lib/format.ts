/**
 * Format số điểm KPI: cắt bỏ (truncate) phần thập phân, chỉ hiện 1 chữ số.
 * KHÔNG làm tròn — 28.49 → "28.4", 28.99 → "28.9", 99.99 → "99.9".
 *
 * Trả về fallback nếu giá trị null/undefined/NaN.
 */
export function formatScore(
  value: number | null | undefined,
  fallback: string = '',
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return fallback;
  }
  const truncated = Math.trunc(value * 10) / 10;
  return truncated.toFixed(1);
}
