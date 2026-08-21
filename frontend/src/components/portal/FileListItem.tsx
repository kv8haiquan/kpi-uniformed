/**
 * components/portal/FileListItem.tsx
 * =====================================
 * Row hiển thị tài liệu ở dạng list view.
 *
 * Nếu callback onDelete được truyền → hiển thị nút xóa cuối row.
 */

import Link from 'next/link';
import type { ITaiLieuItem } from '@/types/tai-lieu';
import { getFileIcon, formatFileSize } from '@/types/tai-lieu';

// =============================================================================
// COMPONENT
// =============================================================================

interface FileListItemProps {
  file: ITaiLieuItem;
  onDelete?: (id: string) => void;
}

export default function FileListItem({ file, onDelete }: FileListItemProps) {
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
    <div className="flex items-center gap-3 hover:bg-gray-50 border-b border-gray-100 last:border-0 group transition-colors">
      <Link
        href={`/tai-lieu/${file.id}`}
        className="flex-1 flex items-center gap-3 px-4 py-3 min-w-0"
      >
        {/* Icon */}
        <span className="text-xl flex-shrink-0 w-8 text-center">{icon}</span>

        {/* Tên + tags */}
        <div className="flex-1 min-w-0">
          {/* `title` để rê chuột đọc đủ tên khi bị cắt — trước đây không có,
              tên dài là mất hẳn phần đuôi mà không có cách nào xem. */}
          <p
            className="text-sm font-medium text-gray-800 truncate group-hover:text-blue-700 transition-colors"
            title={file.ten_tai_lieu}
          >
            {file.ten_tai_lieu}
          </p>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-xs text-gray-400 uppercase">{file.file_type.split('/').pop()}</span>
            {file.tags && file.tags.slice(0, 2).map((tag) => (
              <span
                key={tag}
                className="text-xs bg-blue-50 text-blue-600 px-1.5 rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* Kích thước */}
        <div className="hidden sm:block text-xs text-gray-400 w-16 text-right flex-shrink-0">
          {size}
        </div>

        {/* Người upload */}
        <div
          className="hidden md:block text-xs text-gray-500 w-32 truncate flex-shrink-0"
          title={file.nguoi_tai_len.ho_ten}
        >
          {file.nguoi_tai_len.ho_ten}
        </div>

        {/* Ngày + phiên bản */}
        <div className="hidden lg:flex flex-col items-end flex-shrink-0 w-28">
          <span className="text-xs text-gray-400">{date}</span>
          <span className="text-xs text-gray-300">v{file.phien_ban}</span>
        </div>
      </Link>

      {/* Nút xóa */}
      {onDelete && (
        <button
          onClick={handleDeleteClick}
          title="Xóa tài liệu"
          className="mr-3 w-7 h-7 flex items-center justify-center rounded-full text-gray-400 opacity-0 group-hover:opacity-100 hover:text-red-600 hover:bg-red-50 transition-all"
        >
          🗑
        </button>
      )}
    </div>
  );
}
