/**
 * components/portal/FileCard.tsx
 * ================================
 * Card hiển thị tài liệu ở dạng grid view.
 *
 * Nếu callback onDelete được truyền → hiển thị nút xóa ở góc trên-phải.
 * Page parent quyết định ai được xóa (owner hoặc admin).
 */

import Link from 'next/link';
import type { ITaiLieuItem } from '@/types/tai-lieu';
import { getFileIcon, formatFileSize } from '@/types/tai-lieu';

// =============================================================================
// COMPONENT
// =============================================================================

interface FileCardProps {
  file: ITaiLieuItem;
  onDelete?: (id: string) => void;
}

export default function FileCard({ file, onDelete }: FileCardProps) {
  const icon = getFileIcon(file.file_type);
  const size = formatFileSize(file.file_size_bytes);
  const date = new Date(file.created_at).toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (onDelete) onDelete(file.id);
  };

  return (
    <div className="relative group">
      <Link
        href={`/tai-lieu/${file.id}`}
        className="flex flex-col bg-white border border-gray-200 rounded-xl p-4 hover:border-blue-300 hover:shadow-md transition-all"
      >
        {/* Icon */}
        <div className="flex items-center justify-center w-12 h-12 bg-gray-50 rounded-xl mb-3 text-2xl group-hover:bg-blue-50 transition-colors">
          {icon}
        </div>

        {/* Tên tài liệu.
            `line-clamp-3` + `break-words`: tên tài liệu tiếng Việt thường rất
            dài (có file 130 ký tự). Trước đây kẹp 2 dòng và KHÔNG có tooltip
            nên phần đuôi biến mất hẳn — người dùng không đọc được tên file
            mình đang mở. Nay ba dòng, tự xuống dòng giữa từ dài, và luôn có
            `title` để rê chuột đọc đủ. */}
        <p
          className="text-sm font-semibold text-gray-800 line-clamp-3 break-words mb-auto leading-snug group-hover:text-blue-700 transition-colors"
          title={file.ten_tai_lieu}
        >
          {file.ten_tai_lieu}
        </p>

        {/* Tags */}
        {file.tags && file.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {file.tags.slice(0, 2).map((tag) => (
              <span
                key={tag}
                className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded-full"
              >
                {tag}
              </span>
            ))}
            {file.tags.length > 2 && (
              <span className="text-xs text-gray-400">+{file.tags.length - 2}</span>
            )}
          </div>
        )}

        {/* Meta */}
        <div className="mt-3 pt-3 border-t border-gray-100 space-y-1">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="uppercase tracking-wide">{file.file_type.split('/').pop()}</span>
            <span>{size}</span>
          </div>
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="truncate" title={file.nguoi_tai_len.ho_ten}>
              {file.nguoi_tai_len.ho_ten}
            </span>
            <span className="flex-shrink-0 ml-1">v{file.phien_ban}</span>
          </div>
          <div className="text-xs text-gray-300">{date}</div>
        </div>
      </Link>

      {/* Nút xóa — chỉ hiện khi onDelete được truyền (owner / admin) */}
      {onDelete && (
        <button
          onClick={handleDeleteClick}
          title="Xóa tài liệu"
          className="absolute top-2 right-2 w-7 h-7 flex items-center justify-center rounded-full bg-white border border-gray-200 text-gray-400 opacity-0 group-hover:opacity-100 hover:text-red-600 hover:border-red-300 hover:bg-red-50 transition-all"
        >
          ✕
        </button>
      )}
    </div>
  );
}
