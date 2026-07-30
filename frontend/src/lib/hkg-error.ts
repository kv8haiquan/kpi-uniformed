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

/**
 * Lấy HTTP status từ axios error (không có response interceptor nên
 * `.response.status` còn nguyên). Trả null nếu là lỗi mạng / không phải axios.
 */
export function errStatus(e: unknown): number | null {
  if (e === null || typeof e !== 'object') return null;
  const resp = (e as { response?: { status?: unknown } }).response;
  if (resp && typeof resp.status === 'number') return resp.status;
  return null;
}
