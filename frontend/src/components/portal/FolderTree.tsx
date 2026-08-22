/**
 * components/portal/FolderTree.tsx
 * ==================================
 * Tree navigation cho thư mục tài liệu.
 * Recursive component với expand/collapse.
 */

'use client';

import { useEffect, useState } from 'react';
import type { IThuMucTree } from '@/types/tai-lieu';

// =============================================================================
// TYPES
// =============================================================================

interface FolderTreeProps {
  folders: IThuMucTree[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  /** Thêm nút "Thư mục mới" cho admin */
  onAdd?: (parentId?: string) => void;
}

interface FolderNodeProps {
  node: IThuMucTree;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onAdd?: (parentId?: string) => void;
  expandedIds: Set<string>;
  onToggle: (id: string) => void;
  depth: number;
}

// =============================================================================
// FOLDER NODE (recursive)
// =============================================================================

function FolderNode({
  node,
  selectedId,
  onSelect,
  onAdd,
  expandedIds,
  onToggle,
  depth,
}: FolderNodeProps) {
  const isExpanded = expandedIds.has(node.id);
  const isSelected = selectedId === node.id;
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div>
      <div
        className={`flex items-center gap-1 rounded-lg px-2 py-1.5 cursor-pointer group transition-colors ${
          isSelected
            ? 'bg-blue-100 text-blue-800'
            : 'hover:bg-gray-100 text-gray-700'
        }`}
        style={{ paddingLeft: `${8 + depth * 16}px` }}
        onClick={() => onSelect(node.id)}
      >
        {/* Expand/collapse toggle */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (hasChildren) onToggle(node.id);
          }}
          className={`w-4 h-4 flex items-center justify-center flex-shrink-0 ${
            hasChildren ? 'text-gray-400 hover:text-gray-700' : 'opacity-0'
          }`}
        >
          {hasChildren ? (isExpanded ? '▾' : '▸') : null}
        </button>

        {/* Icon */}
        <span className="text-sm flex-shrink-0">
          {isExpanded && hasChildren ? '📂' : '📁'}
        </span>

        {/* Tên thư mục */}
        <span className="text-sm font-medium truncate flex-1" title={node.ten}>
          {node.ten}
        </span>

        {/* Nút thêm con */}
        {onAdd && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onAdd(node.id);
            }}
            className="opacity-0 group-hover:opacity-100 text-xs text-blue-500 hover:text-blue-700 px-1 flex-shrink-0"
            title="Thêm thư mục con"
          >
            +
          </button>
        )}
      </div>

      {/* Children */}
      {isExpanded && hasChildren && (
        <div>
          {node.children.map((child) => (
            <FolderNode
              key={child.id}
              node={child}
              selectedId={selectedId}
              onSelect={onSelect}
              onAdd={onAdd}
              expandedIds={expandedIds}
              onToggle={onToggle}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// FOLDER TREE (main)
// =============================================================================

export default function FolderTree({
  folders,
  selectedId,
  onSelect,
  onAdd,
}: FolderTreeProps) {
  // Mở rộng tất cả thư mục cấp 1 mặc định.
  //
  // Phải theo dõi `folders` bằng useEffect: hàm khởi tạo của useState chỉ chạy
  // MỘT LẦN, mà lúc đó danh sách còn rỗng (cây tải bất đồng bộ) — nên trước
  // đây không thư mục nào tự mở, người dùng phải tự bấm từng mũi tên mới thấy
  // thư mục con. Chỉ THÊM vào tập đang mở, không ghi đè, để lần vẽ lại không
  // đóng sập những nhánh người dùng vừa mở tay.
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (folders.length === 0) return;
    setExpandedIds((truoc) => {
      const moi = new Set(truoc);
      folders.forEach((f) => moi.add(f.id));
      return moi;
    });
  }, [folders]);

  const handleToggle = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  if (folders.length === 0) {
    return (
      <div className="text-center py-6">
        <span className="text-2xl">📁</span>
        <p className="text-xs text-gray-400 mt-2">Chưa có thư mục</p>
        {onAdd && (
          <button
            onClick={() => onAdd()}
            className="mt-2 text-xs text-blue-600 hover:underline"
          >
            + Tạo thư mục đầu tiên
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-0.5">
      {/* "Tất cả" node */}
      <div
        className={`flex items-center gap-2 rounded-lg px-3 py-1.5 cursor-pointer transition-colors ${
          selectedId === null
            ? 'bg-blue-100 text-blue-800'
            : 'hover:bg-gray-100 text-gray-700'
        }`}
        onClick={() => onSelect('')}
      >
        <span className="text-sm">🗂️</span>
        <span className="text-sm font-medium">Tất cả tài liệu</span>
      </div>

      {/* Folder tree */}
      {folders.map((node) => (
        <FolderNode
          key={node.id}
          node={node}
          selectedId={selectedId}
          onSelect={onSelect}
          onAdd={onAdd}
          expandedIds={expandedIds}
          onToggle={handleToggle}
          depth={0}
        />
      ))}

      {/* Nút thêm thư mục gốc */}
      {onAdd && (
        <button
          onClick={() => onAdd()}
          className="w-full text-left px-3 py-1.5 text-xs text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
        >
          + Thêm thư mục
        </button>
      )}
    </div>
  );
}
