/**
 * src/components/lms/FileUploader.tsx
 * =====================================
 * Drag-and-drop file uploader tích hợp với LMS upload endpoint.
 * Hỗ trợ: progress bar, client-side validation, file type icons, replace/delete.
 *
 * Props:
 *   accept         — Các MIME / extension hợp lệ (VD: ".pdf,.doc")
 *   maxSizeMB      — Giới hạn dung lượng (default 100)
 *   folder         — Sub-folder lưu trữ trên server (default "bai-hoc")
 *   label          — Nhãn hiển thị trong vùng kéo thả
 *   onUploadDone   — Callback khi upload thành công, nhận { file_name, file_url, file_size, content_type }
 *   currentFileUrl — URL file hiện tại (khi edit), để hiển thị trạng thái "đã có file"
 */

'use client';

import { useRef, useState, useCallback } from 'react';
import { uploadApi } from '@/services/lms';

// =============================================================================
// TYPES
// =============================================================================

export interface UploadResult {
  file_name:    string;
  file_url:     string;
  file_size:    number;
  content_type: string;
}

interface FileUploaderProps {
  accept?:        string;             // VD: ".pdf,.docx"
  maxSizeMB?:     number;
  folder?:        string;
  label?:         string;
  onUploadDone:   (result: UploadResult) => void;
  currentFileUrl?: string | null;
}

// =============================================================================
// HELPERS
// =============================================================================

/** Định dạng dung lượng file */
function fmtSize(bytes: number): string {
  if (bytes < 1024)       return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

/** Icon theo extension */
function fileIcon(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase() ?? '';
  if (['mp4', 'webm', 'avi', 'mov'].includes(ext)) return '🎬';
  if (['pdf'].includes(ext))                         return '📄';
  if (['ppt', 'pptx'].includes(ext))                return '📊';
  if (['doc', 'docx'].includes(ext))                return '📝';
  if (['xls', 'xlsx'].includes(ext))                return '📋';
  if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) return '🖼';
  if (['html', 'htm'].includes(ext))                return '🌐';
  return '📎';
}

/** Lấy tên file từ URL */
function nameFromUrl(url: string): string {
  return url.split('/').pop() ?? url;
}

// =============================================================================
// COMPONENT
// =============================================================================

export default function FileUploader({
  accept,
  maxSizeMB = 100,
  folder = 'bai-hoc',
  label,
  onUploadDone,
  currentFileUrl,
}: FileUploaderProps) {
  const inputRef    = useRef<HTMLInputElement>(null);
  const [dragging,  setDragging]  = useState(false);
  const [progress,  setProgress]  = useState<number | null>(null);  // null = idle
  const [errMsg,    setErrMsg]    = useState('');
  const [uploaded,  setUploaded]  = useState<UploadResult | null>(null);

  // File đang hiển thị (ưu tiên kết quả vừa upload, rồi đến currentFileUrl)
  const displayUrl  = uploaded?.file_url ?? currentFileUrl ?? null;
  const displayName = uploaded?.file_name ?? (currentFileUrl ? nameFromUrl(currentFileUrl) : null);

  // --------------------------------------------------------------------------
  // Upload logic
  // --------------------------------------------------------------------------

  const doUpload = useCallback(async (file: File) => {
    setErrMsg('');

    // Client-side size check
    if (file.size > maxSizeMB * 1024 * 1024) {
      setErrMsg(`File vượt quá ${maxSizeMB} MB. Vui lòng chọn file nhỏ hơn.`);
      return;
    }

    setProgress(0);
    try {
      const res = await uploadApi.uploadFile(file, folder, (pct) => setProgress(pct));
      const result: UploadResult = res.data.data;
      setUploaded(result);
      setProgress(null);
      onUploadDone(result);
    } catch (err: any) {
      setProgress(null);
      const msg =
        err?.response?.data?.detail?.error?.message ||
        err?.response?.data?.detail ||
        'Upload thất bại. Kiểm tra kết nối LMS (port 8001).';
      setErrMsg(String(msg));
    }
  }, [folder, maxSizeMB, onUploadDone]);

  // --------------------------------------------------------------------------
  // Drag & Drop handlers
  // --------------------------------------------------------------------------

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) doUpload(file);
  }, [doUpload]);

  const onDragOver = (e: React.DragEvent) => { e.preventDefault(); setDragging(true); };
  const onDragLeave = () => setDragging(false);

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) doUpload(file);
    // Reset value để cho phép chọn cùng file lần nữa
    e.target.value = '';
  };

  // --------------------------------------------------------------------------
  // Render: trạng thái đã có file
  // --------------------------------------------------------------------------

  if (displayUrl && progress === null) {
    return (
      <div className="border border-green-200 bg-green-50 rounded-lg px-4 py-3 flex items-center gap-3">
        <span className="text-2xl shrink-0">{fileIcon(displayName ?? '')}</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-800 truncate">{displayName}</p>
          {uploaded && (
            <p className="text-xs text-gray-500">{fmtSize(uploaded.file_size)} · {uploaded.content_type}</p>
          )}
          <p className="text-xs text-green-700 truncate">{displayUrl}</p>
        </div>
        <button
          type="button"
          onClick={() => { setUploaded(null); inputRef.current?.click(); }}
          className="shrink-0 px-3 py-1.5 border border-gray-300 rounded-lg text-xs text-gray-600 hover:bg-white bg-white"
        >
          Đổi file
        </button>
        <input ref={inputRef} type="file" accept={accept} className="hidden" onChange={onInputChange} />
      </div>
    );
  }

  // --------------------------------------------------------------------------
  // Render: đang upload
  // --------------------------------------------------------------------------

  if (progress !== null) {
    return (
      <div className="border border-blue-200 bg-blue-50 rounded-lg px-4 py-4">
        <p className="text-sm text-blue-700 mb-2">Đang tải lên... {progress}%</p>
        <div className="w-full bg-blue-100 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-200"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    );
  }

  // --------------------------------------------------------------------------
  // Render: vùng kéo thả
  // --------------------------------------------------------------------------

  return (
    <div>
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg px-4 py-6 flex flex-col items-center justify-center cursor-pointer transition-colors ${
          dragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50'
        }`}
      >
        <span className="text-3xl mb-2">📂</span>
        <p className="text-sm font-medium text-gray-700">
          {label ?? 'Kéo & thả file vào đây, hoặc nhấn để chọn'}
        </p>
        {accept && (
          <p className="text-xs text-gray-400 mt-1">Chấp nhận: {accept}</p>
        )}
        <p className="text-xs text-gray-400">Tối đa {maxSizeMB} MB</p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={onInputChange}
      />

      {errMsg && (
        <p className="text-xs text-red-600 mt-1.5">{errMsg}</p>
      )}
    </div>
  );
}
