/**
 * components/portal/FileListItem.tsx
 * =====================================
 * Row hiển thị tài liệu ở dạng list view.
 */

import Link from 'next/link';
import type { ITaiLieuItem } from '@/types/tai-lieu';
import { getFileIcon, formatFileSize } from '@/types/tai-lieu';

// =============================================================================
// COMPONENT
// =============================================================================

interface FileListItemProps {
  file: ITaiLieuItem;
}

export default function FileListItem({ file }: FileListItemProps) {
  const icon = getFileIcon(file.file_type);
  const size = formatFileSize(file.file_size_bytes);
  const date = new Date(file.created_at).toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });

  return (
    <Link
      href={`/tai-lieu/${file.id}`}
      className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-0 group transition-colors"
    >
      {/* Icon */}
      <span className="text-xl flex-shrink-0 w-8 text-center">{icon}</span>

      {/* Tên + tags */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-800 truncate group-hover:text-blue-700 transition-colors">
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
      <div className="hidden md:block text-xs text-gray-500 w-32 truncate flex-shrink-0">
        {file.nguoi_tai_len.ho_ten}
      </div>

      {/* Ngày + phiên bản */}
      <div className="hidden lg:flex flex-col items-end flex-shrink-0 w-28">
        <span className="text-xs text-gray-400">{date}</span>
        <span className="text-xs text-gray-300">v{file.phien_ban}</span>
      </div>
    </Link>
  );
}
