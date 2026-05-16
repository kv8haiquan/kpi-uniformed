/**
 * components/portal/UploadModal.tsx
 * ====================================
 * Modal upload tài liệu mới vào thư viện ECM.
 *
 * Flow 2-bước:
 *   1. Kéo & thả file → FileUploader gọi POST /portal/upload/file
 *      → nhận { file_name, file_url, file_size, content_type }
 *   2. Submit form → POST /portal/tai-lieu với metadata + thông tin file
 *
 * Quyền: mọi công chức đã login đều upload được (không giới hạn role).
 */

'use client';

import { useState } from 'react';
import FileUploader, { type UploadResult } from '@/components/lms/FileUploader';
import { taiLieuApi } from '@/services/portal';
import type { ITaiLieuCreate } from '@/types/tai-lieu';

// =============================================================================
// COMPONENT
// =============================================================================

interface UploadModalProps {
  open: boolean;
  thuMucId: string;
  onClose: () => void;
  onSuccess: () => void;
}

interface FormState {
  ten_tai_lieu: string;
  mo_ta: string;
  tags_input: string;
}

const INITIAL_FORM: FormState = {
  ten_tai_lieu: '',
  mo_ta: '',
  tags_input: '',
};

// Định dạng file được chấp nhận (đồng bộ với backend ALLOWED_DOCUMENT_EXTENSIONS)
const ACCEPT_EXTENSIONS =
  '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.csv,.rtf,' +
  '.jpg,.jpeg,.png,.webp,.gif,' +
  '.zip,.rar,.7z';

export default function UploadModal({
  open,
  thuMucId,
  onClose,
  onSuccess,
}: UploadModalProps) {
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [uploaded, setUploaded] = useState<UploadResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  if (!open) return null;

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleUploadDone = (result: UploadResult) => {
    setUploaded(result);
    setError('');
    // Auto-fill tên tài liệu từ tên file nếu user chưa nhập
    if (!form.ten_tai_lieu.trim()) {
      // Bỏ đuôi file để làm tên gợi ý
      const nameWithoutExt = result.file_name.replace(/\.[^/.]+$/, '');
      setForm((prev) => ({ ...prev, ten_tai_lieu: nameWithoutExt }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploaded) {
      setError('Vui lòng tải lên file trước khi lưu tài liệu.');
      return;
    }
    if (!form.ten_tai_lieu.trim()) {
      setError('Vui lòng nhập tên tài liệu.');
      return;
    }
    if (!thuMucId) {
      setError('Vui lòng chọn thư mục trước khi upload.');
      return;
    }

    const tags = form.tags_input
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

    const payload: ITaiLieuCreate = {
      thu_muc_id: thuMucId,
      ten_tai_lieu: form.ten_tai_lieu.trim(),
      mo_ta: form.mo_ta.trim() || undefined,
      file_name: uploaded.file_name,
      file_url: uploaded.file_url,
      file_size_bytes: uploaded.file_size,
      file_type: uploaded.content_type,
      tags,
    };

    setSubmitting(true);
    setError('');
    try {
      await taiLieuApi.taoMoi(payload);
      // Reset state
      setForm(INITIAL_FORM);
      setUploaded(null);
      onSuccess();
    } catch (err: unknown) {
      const e = err as {
        response?: { data?: { detail?: { error?: { message?: string } } | string } };
        message?: string;
      };
      const msg =
        (typeof e?.response?.data?.detail === 'object'
          ? e?.response?.data?.detail?.error?.message
          : e?.response?.data?.detail) ||
        e?.message ||
        'Có lỗi xảy ra. Vui lòng thử lại.';
      setError(String(msg));
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    setForm(INITIAL_FORM);
    setUploaded(null);
    setError('');
    onClose();
  };

  return (
    /* Overlay */
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">Upload tài liệu</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-700 text-xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          {/* File upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              File tài liệu <span className="text-red-500">*</span>
            </label>
            <FileUploader
              accept={ACCEPT_EXTENSIONS}
              maxSizeMB={50}
              folder="tai-lieu"
              label="Kéo & thả file vào đây, hoặc nhấn để chọn"
              uploadFn={taiLieuApi.uploadFile}
              onUploadDone={handleUploadDone}
            />
            <p className="text-xs text-gray-400 mt-1">
              Hỗ trợ PDF, Word, Excel, PowerPoint, ảnh, ZIP. Tối đa 50 MB.
            </p>
          </div>

          {/* Tên tài liệu */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tên tài liệu <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="ten_tai_lieu"
              value={form.ten_tai_lieu}
              onChange={handleChange}
              placeholder="VD: Mẫu tờ khai hải quan XNK"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tags (phân cách bằng dấu phẩy)
            </label>
            <input
              type="text"
              name="tags_input"
              value={form.tags_input}
              onChange={handleChange}
              placeholder="biểu mẫu, XNK, 2026"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
          </div>

          {/* Mô tả */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mô tả
            </label>
            <textarea
              name="mo_ta"
              value={form.mo_ta}
              onChange={handleChange}
              rows={2}
              placeholder="Mô tả ngắn về tài liệu..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
            />
          </div>

          {/* Error */}
          {error && (
            <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
          )}

          {/* Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 border border-gray-300 text-gray-700 rounded-lg py-2 text-sm hover:bg-gray-50 transition-colors"
            >
              Hủy
            </button>
            <button
              type="submit"
              disabled={submitting || !uploaded}
              className="flex-1 bg-blue-600 text-white rounded-lg py-2 text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {submitting ? 'Đang lưu...' : 'Lưu tài liệu'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
