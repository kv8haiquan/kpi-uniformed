/**
 * lib/bai-nop-file.ts
 * ===================
 * Tiện ích nhận diện loại file bài nộp thực hành (LMS).
 *
 * Bài tập thực hành chấp nhận nhiều loại file tuỳ cấu hình `dinh_dang_cho_phep`
 * của giảng viên: PDF (bài viết / báo cáo), video (thao tác nghiệp vụ),
 * ảnh, hoặc tài liệu Office. Mỗi loại hiển thị bằng icon và trình xem khác nhau.
 */

export type LoaiFileBaiNop = 'PDF' | 'VIDEO' | 'ANH' | 'TAI_LIEU' | 'KHAC';

const EXT_VIDEO = ['mp4', 'mov', 'webm', 'avi'];
const EXT_ANH = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
const EXT_TAI_LIEU = ['doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx'];

/** Lấy phần mở rộng (không dấu chấm, chữ thường) từ tên file hoặc URL. */
export function layExtension(tenFileHoacUrl?: string | null): string {
  if (!tenFileHoacUrl) return '';
  // Bỏ query string / hash trước khi tách đuôi
  const sach = tenFileHoacUrl.split(/[?#]/)[0];
  const ten = sach.split('/').pop() || '';
  return ten.includes('.') ? (ten.split('.').pop() || '').toLowerCase() : '';
}

/** Phân loại file bài nộp để chọn icon / trình xem phù hợp. */
export function loaiFileBaiNop(tenFileHoacUrl?: string | null): LoaiFileBaiNop {
  const ext = layExtension(tenFileHoacUrl);
  if (ext === 'pdf') return 'PDF';
  if (EXT_VIDEO.includes(ext)) return 'VIDEO';
  if (EXT_ANH.includes(ext)) return 'ANH';
  if (EXT_TAI_LIEU.includes(ext)) return 'TAI_LIEU';
  return 'KHAC';
}

const ICON: Record<LoaiFileBaiNop, string> = {
  PDF: '📕',
  VIDEO: '🎬',
  ANH: '🖼️',
  TAI_LIEU: '📄',
  KHAC: '📎',
};

const NHAN: Record<LoaiFileBaiNop, string> = {
  PDF: 'PDF',
  VIDEO: 'video',
  ANH: 'ảnh',
  TAI_LIEU: 'tài liệu',
  KHAC: 'file',
};

/** Icon emoji tương ứng loại file. */
export function iconBaiNop(tenFileHoacUrl?: string | null): string {
  return ICON[loaiFileBaiNop(tenFileHoacUrl)];
}

/** Nhãn tiếng Việt ngắn ("PDF", "video", "tài liệu"...). */
export function nhanBaiNop(tenFileHoacUrl?: string | null): string {
  return NHAN[loaiFileBaiNop(tenFileHoacUrl)];
}

/**
 * Icon + nhãn cho một cấu hình định dạng (CSV, ví dụ "pdf" hoặc "mp4,mov").
 * Dùng ở màn cấu hình / danh sách bài kiểm tra khi chưa có file cụ thể.
 */
export function moTaDinhDang(csv?: string | null): { icon: string; nhan: string } {
  const exts = (csv || '')
    .split(',')
    .map((e) => e.trim().replace(/^\./, '').toLowerCase())
    .filter(Boolean);
  if (exts.length === 0) return { icon: '📎', nhan: 'file' };

  const loai = new Set(exts.map((e) => loaiFileBaiNop(`x.${e}`)));
  if (loai.size === 1) {
    const only = [...loai][0];
    return { icon: ICON[only], nhan: NHAN[only] };
  }
  return { icon: '📎', nhan: 'file bài làm' };
}
