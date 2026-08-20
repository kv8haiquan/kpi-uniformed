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
 * Thông điệp do backend soạn, lấy từ `detail.error.message` của response.
 *
 * `errMsg` chỉ đọc `Error.message` nên với lỗi axios sẽ ra "Request failed
 * with status code 403" — đúng kỹ thuật nhưng vô nghĩa với người dùng. Hàm
 * này ưu tiên câu tiếng Việt backend trả về, không có thì lùi về `errMsg`.
 */
export function errApi(e: unknown, fallback = 'Đã có lỗi'): string {
  if (e !== null && typeof e === 'object') {
    const data = (e as { response?: { data?: unknown } }).response?.data;
    if (data && typeof data === 'object') {
      const detail = (data as { detail?: unknown }).detail;
      if (detail && typeof detail === 'object') {
        const loi = (detail as { error?: unknown }).error;
        if (loi && typeof loi === 'object') {
          const m = (loi as { message?: unknown }).message;
          if (typeof m === 'string' && m) return m;
        }
      }
      if (typeof detail === 'string' && detail) return detail;
    }
  }
  return errMsg(e, fallback);
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
