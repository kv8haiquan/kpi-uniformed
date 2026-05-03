/**
 * Helper extract message từ unknown error (axios reject hoặc Error).
 */

export function errMsg(e: unknown, fallback = 'Đã có lỗi'): string {
  if (e === null || e === undefined) return fallback;
  if (typeof e === 'string') return e;
  if (typeof e === 'object') {
    const obj = e as { message?: unknown };
    if (typeof obj.message === 'string') return obj.message;
  }
  return fallback;
}
