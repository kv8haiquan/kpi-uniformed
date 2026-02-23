/**
 * components/portal/UploadModal.tsx
 * ====================================
 * Modal upload tài liệu mới hoặc phiên bản mới.
 *
 * Note: Khi Common file storage API sẵn sàng, thay thế URL input
 * bằng file upload thực sự.
 */

'use client';

import { useState } from 'react';
import { taiLieuApi } from '@/services/portal';
import type { ITaiLieuCreate } from '@/types/tai-lieu';

// =============================================================================
// FILE TYPE OPTIONS
// =============================================================================

const FILE_TYPES = [
  { value: 'application/pdf', label: 'PDF' },
  { value: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', label: 'DOCX (Word)' },
  { value: 'application/msword', label: 'DOC (Word cũ)' },
  { value: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', label: 'XLSX (Excel)' },
  { value: 'application/vnd.openxmlformats-officedocument.presentationml.presentation', label: 'PPTX (PowerPoint)' },
  { value: 'image/jpeg', label: 'JPEG (Ảnh)' },
  { value: 'image/png', label: 'PNG (Ảnh)' },
  { value: 'application/zip', label: 'ZIP (Nén)' },
];

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
  file_url: string;
  file_name: string;
  file_type: string;
  file_size_bytes: string;
  tags_input: string;
}

const INITIAL_FORM: FormState = {
  ten_tai_lieu: '',
  mo_ta: '',
  file_url: '',
  file_name: '',
  file_type: 'application/pdf',
  file_size_bytes: '0',
  tags_input: '',
};

export default function UploadModal({
  open,
  thuMucId,
  onClose,
  onSuccess,
}: UploadModalProps) {
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  if (!open) return null;

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  // Tự động lấy file_name từ URL
  const handleUrlBlur = () => {
    if (form.file_url && !form.file_name) {
      const parts = form.file_url.split('/');
      const name = parts[parts.length - 1].split('?')[0];
      if (name) setForm((prev) => ({ ...prev, file_name: name }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.ten_tai_lieu.trim() || !form.file_url.trim() || !form.file_name.trim()) {
      setError('Vui lòng điền đầy đủ tên tài liệu, URL và tên file.');
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
      file_name: form.file_name.trim(),
      file_url: form.file_url.trim(),
      file_size_bytes: parseInt(form.file_size_bytes) || 0,
      file_type: form.file_type,
      tags,
    };

    setSubmitting(true);
    setError('');
    try {
      await taiLieuApi.taoMoi(payload);
      setForm(INITIAL_FORM);
      onSuccess();
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e?.message || 'Có lỗi xảy ra. Vui lòng thử lại.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    /* Overlay */
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">Upload tài liệu</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-700 text-xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
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

          {/* URL tài liệu */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              URL tài liệu <span className="text-red-500">*</span>
            </label>
            <input
              type="url"
              name="file_url"
              value={form.file_url}
              onChange={handleChange}
              onBlur={handleUrlBlur}
              placeholder="https://..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
            <p className="text-xs text-gray-400 mt-1">
              Nhập URL trực tiếp. Upload file thực sẽ hỗ trợ trong phiên bản sau.
            </p>
          </div>

          {/* Tên file + loại file */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tên file <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="file_name"
                value={form.file_name}
                onChange={handleChange}
                placeholder="ten-file.pdf"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Loại file
              </label>
              <select
                name="file_type"
                value={form.file_type}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white"
              >
                {FILE_TYPES.map((ft) => (
                  <option key={ft.value} value={ft.value}>
                    {ft.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Kích thước + mô tả */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Kích thước (bytes)
              </label>
              <input
                type="number"
                name="file_size_bytes"
                value={form.file_size_bytes}
                onChange={handleChange}
                min="0"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              />
            </div>
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
              onClick={onClose}
              className="flex-1 border border-gray-300 text-gray-700 rounded-lg py-2 text-sm hover:bg-gray-50 transition-colors"
            >
              Hủy
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 bg-blue-600 text-white rounded-lg py-2 text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {submitting ? 'Đang upload...' : 'Upload tài liệu'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
