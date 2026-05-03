/**
 * TipTapEditor — basic rich-text editor cho biên bản HKG.
 *
 * Toolbar: Bold / Italic / H2 / H3 / Bullet list / Ordered list / Quote / Undo/Redo.
 * Output: TipTap JSON (`editor.getJSON()`) + HTML (`editor.getHTML()`).
 *
 * Vietnamese Unicode hoạt động native trong contenteditable HTML element.
 */

'use client';

import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { useEffect } from 'react';
import {
  Bold,
  Italic,
  List,
  ListOrdered,
  Heading2,
  Heading3,
  Quote,
  Undo,
  Redo,
} from 'lucide-react';

export interface ITipTapEditorProps {
  /** TipTap JSON content. Khi đổi prop, editor sẽ reset về content mới. */
  initialContent?: Record<string, unknown> | null;
  /** Disable mọi sửa đổi (vd: biên bản đã ký). */
  readOnly?: boolean;
  /** Gọi mỗi khi nội dung đổi. Caller chịu trách nhiệm debounce nếu cần. */
  onChange?: (json: Record<string, unknown>, html: string) => void;
}

export default function TipTapEditor({
  initialContent,
  readOnly = false,
  onChange,
}: ITipTapEditorProps) {
  const editor = useEditor({
    extensions: [StarterKit],
    content: initialContent || '',
    editable: !readOnly,
    immediatelyRender: false, // tránh hydration mismatch trong Next.js
    onUpdate: ({ editor }) => {
      if (onChange) {
        onChange(editor.getJSON() as Record<string, unknown>, editor.getHTML());
      }
    },
    editorProps: {
      attributes: {
        class:
          'prose prose-sm max-w-none p-4 min-h-[300px] focus:outline-none',
      },
    },
  });

  // Khi initialContent thay đổi từ ngoài (vd: load lại sau ký) → reset editor.
  useEffect(() => {
    if (editor && initialContent && !editor.isFocused) {
      const current = JSON.stringify(editor.getJSON());
      const incoming = JSON.stringify(initialContent);
      if (current !== incoming) {
        editor.commands.setContent(initialContent);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialContent, editor]);

  // Toggle readOnly khi prop đổi.
  useEffect(() => {
    editor?.setEditable(!readOnly);
  }, [readOnly, editor]);

  if (!editor) return null;

  return (
    <div className="border border-gray-300 rounded bg-white">
      {!readOnly && (
        <div className="flex flex-wrap gap-1 p-2 border-b bg-gray-50">
          <ToolbarButton
            active={editor.isActive('bold')}
            onClick={() => editor.chain().focus().toggleBold().run()}
            title="Đậm (Ctrl+B)"
          >
            <Bold className="w-4 h-4" />
          </ToolbarButton>
          <ToolbarButton
            active={editor.isActive('italic')}
            onClick={() => editor.chain().focus().toggleItalic().run()}
            title="Nghiêng (Ctrl+I)"
          >
            <Italic className="w-4 h-4" />
          </ToolbarButton>

          <Divider />

          <ToolbarButton
            active={editor.isActive('heading', { level: 2 })}
            onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
            title="Tiêu đề 2"
          >
            <Heading2 className="w-4 h-4" />
          </ToolbarButton>
          <ToolbarButton
            active={editor.isActive('heading', { level: 3 })}
            onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
            title="Tiêu đề 3"
          >
            <Heading3 className="w-4 h-4" />
          </ToolbarButton>

          <Divider />

          <ToolbarButton
            active={editor.isActive('bulletList')}
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            title="Danh sách"
          >
            <List className="w-4 h-4" />
          </ToolbarButton>
          <ToolbarButton
            active={editor.isActive('orderedList')}
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
            title="Đánh số"
          >
            <ListOrdered className="w-4 h-4" />
          </ToolbarButton>
          <ToolbarButton
            active={editor.isActive('blockquote')}
            onClick={() => editor.chain().focus().toggleBlockquote().run()}
            title="Trích dẫn"
          >
            <Quote className="w-4 h-4" />
          </ToolbarButton>

          <Divider />

          <ToolbarButton
            onClick={() => editor.chain().focus().undo().run()}
            disabled={!editor.can().undo()}
            title="Hoàn tác"
          >
            <Undo className="w-4 h-4" />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().redo().run()}
            disabled={!editor.can().redo()}
            title="Làm lại"
          >
            <Redo className="w-4 h-4" />
          </ToolbarButton>
        </div>
      )}

      <EditorContent editor={editor} />
    </div>
  );
}

function ToolbarButton({
  active,
  onClick,
  disabled,
  title,
  children,
}: {
  active?: boolean;
  onClick: () => void;
  disabled?: boolean;
  title?: string;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={`p-1.5 rounded text-gray-700 hover:bg-gray-200 disabled:opacity-30 disabled:hover:bg-transparent ${
        active ? 'bg-blue-100 text-blue-700' : ''
      }`}
    >
      {children}
    </button>
  );
}

function Divider() {
  return <div className="w-px bg-gray-300 mx-1" />;
}
