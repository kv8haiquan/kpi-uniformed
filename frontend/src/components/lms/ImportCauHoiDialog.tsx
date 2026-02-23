/**
 * src/components/lms/ImportCauHoiDialog.tsx
 * ==========================================
 * Dialog import câu hỏi hàng loạt từ file Excel/CSV.
 *
 * Props:
 *   open            — hiển thị/ẩn dialog
 *   onOpenChange    — callback đóng/mở
 *   khoaHocId       — UUID khóa học để gắn câu hỏi (tuỳ chọn)
 *   baiKiemTraId    — UUID bài kiểm tra (tự resolve khoa_hoc_id từ backend)
 *   onImportSuccess — callback khi import thành công ≥1 câu
 */

'use client';

import { useRef, useState } from 'react';
import { cauHoiApi } from '@/services/lms';

// =============================================================================
// TYPES
// =============================================================================

interface ImportResult {
  thanh_cong: number;
  that_bai: number;
  tong: number;
  loi_chi_tiet: Array<{ dong: number; loi: string }>;
  cau_hoi_ids?: string[];  // IDs câu hỏi vừa import thành công
}

interface ImportCauHoiDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  khoaHocId?: string;
  baiKiemTraId?: string;
  onImportSuccess: (result: ImportResult) => void;
}

// =============================================================================
// COMPONENT
// =============================================================================

export default function ImportCauHoiDialog({
  open,
  onOpenChange,
  khoaHocId,
  baiKiemTraId,
  onImportSuccess,
}: ImportCauHoiDialogProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importing, setImporting]       = useState(false);
  const [downloading, setDownloading]   = useState(false);
  const [errMsg, setErrMsg]             = useState('');
  const [result, setResult]             = useState<ImportResult | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!open) return null;

  // ---------------------------------------------------------------------------
  // Tải file mẫu
  // ---------------------------------------------------------------------------
  const handleDownloadMau = async () => {
    setDownloading(true);
    try {
      const res = await cauHoiApi.downloadMauImport();
      const blob = new Blob([res.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.document',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'mau_import_cau_hoi.xlsx';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      setErrMsg('Không thể tải file mẫu. Kiểm tra LMS backend.');
    } finally {
      setDownloading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Chọn file
  // ---------------------------------------------------------------------------
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    if (!file) return;
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'xlsx' && ext !== 'csv') {
      setErrMsg('Chỉ chấp nhận file .xlsx hoặc .csv');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setErrMsg('File không được vượt quá 5MB');
      return;
    }
    setSelectedFile(file);
    setErrMsg('');
    setResult(null);
  };

  // ---------------------------------------------------------------------------
  // Thực hiện import
  // ---------------------------------------------------------------------------
  const handleImport = async () => {
    if (!selectedFile) { setErrMsg('Vui lòng chọn file trước khi import'); return; }
    setImporting(true);
    setErrMsg('');
    setResult(null);
    try {
      const res = await cauHoiApi.importFile(selectedFile, {
        khoa_hoc_id: khoaHocId,
        bai_kiem_tra_id: baiKiemTraId,
      });
      const data: ImportResult = res.data?.data;
      setResult(data);
      if (data.thanh_cong > 0) {
        onImportSuccess(data);
      }
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail?.error?.message ||
        err?.response?.data?.detail ||
        'Lỗi import. Kiểm tra LMS backend (port 8001).';
      setErrMsg(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setImporting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Đóng dialog
  // ---------------------------------------------------------------------------
  const handleClose = () => {
    if (!importing) {
      setSelectedFile(null);
      setResult(null);
      setErrMsg('');
      if (fileInputRef.current) fileInputRef.current.value = '';
      onOpenChange(false);
    }
  };

  // ---------------------------------------------------------------------------
  // RENDER
  // ---------------------------------------------------------------------------
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/40" onClick={handleClose} />

      {/* Dialog box */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">

        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            📁 Import câu hỏi từ file
          </h3>
          <button
            onClick={handleClose}
            disabled={importing}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-40 text-xl leading-none"
          >×</button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5 max-h-[75vh] overflow-y-auto">

          {/* Hướng dẫn + tải file mẫu */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
            <p className="font-medium mb-1">Hướng dẫn format file:</p>
            <ul className="list-disc list-inside space-y-0.5 text-xs text-blue-700">
              <li><span className="font-mono">noi_dung</span> — Nội dung câu hỏi (bắt buộc)</li>
              <li><span className="font-mono">loai</span> — TRAC_NGHIEM_1 | TRAC_NGHIEM_NHIEU | DUNG_SAI | TU_LUAN</li>
              <li><span className="font-mono">dap_an_a/b/c/d</span> — Nội dung các phương án</li>
              <li><span className="font-mono">dap_an_dung</span> — A/B/C/D (nhiều đáp án: "A,C")</li>
              <li><span className="font-mono">do_kho</span> — DE | TRUNG_BINH | KHO (mặc định: TRUNG_BINH)</li>
              <li><span className="font-mono">diem</span> — Số điểm (mặc định: 1.0)</li>
              <li><span className="font-mono">giai_thich</span> — Giải thích đáp án (tuỳ chọn)</li>
            </ul>
            <button
              onClick={handleDownloadMau}
              disabled={downloading}
              className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-700 disabled:opacity-60"
            >
              {downloading ? (
                <><span className="inline-block w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin" />Đang tải...</>
              ) : '📥 Tải file mẫu (.xlsx)'}
            </button>
          </div>

          {/* Context hiển thị khi có baiKiemTraId */}
          {baiKiemTraId && (
            <div className="bg-green-50 border border-green-200 rounded-lg px-3 py-2 text-xs text-green-700">
              ✅ Câu hỏi sẽ được gắn trực tiếp vào bài kiểm tra này
            </div>
          )}

          {/* Chọn file */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Chọn file <span className="text-red-500">*</span>
              <span className="text-gray-400 font-normal ml-1">(.xlsx hoặc .csv, tối đa 5MB)</span>
            </label>
            <div
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-lg p-5 text-center cursor-pointer transition-colors ${
                selectedFile
                  ? 'border-green-400 bg-green-50'
                  : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
              }`}
            >
              {selectedFile ? (
                <div>
                  <p className="text-green-700 font-medium">
                    {selectedFile.name.endsWith('.xlsx') ? '📊' : '📄'} {selectedFile.name}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {(selectedFile.size / 1024).toFixed(1)} KB — Click để đổi file
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-gray-500 text-sm">🔗 Kéo thả hoặc click để chọn file</p>
                  <p className="text-xs text-gray-400 mt-1">Hỗ trợ: .xlsx, .csv</p>
                </div>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.csv"
              className="hidden"
              onChange={handleFileChange}
            />
          </div>

          {/* Thông báo lỗi chung */}
          {errMsg && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              <p className="text-sm text-red-700">⛔ {errMsg}</p>
            </div>
          )}

          {/* Kết quả import */}
          {result && (
            <div className="rounded-lg border overflow-hidden">
              {/* Summary */}
              <div className={`px-4 py-3 flex items-center gap-4 ${result.that_bai === 0 ? 'bg-green-50' : 'bg-yellow-50'}`}>
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-700">{result.thanh_cong}</p>
                  <p className="text-xs text-gray-500">thành công</p>
                </div>
                <div className="text-gray-300">|</div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-red-600">{result.that_bai}</p>
                  <p className="text-xs text-gray-500">lỗi</p>
                </div>
                <div className="text-gray-300">|</div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-700">{result.tong}</p>
                  <p className="text-xs text-gray-500">tổng</p>
                </div>
                <div className="flex-1 text-right">
                  {result.thanh_cong > 0 && (
                    <span className="text-sm font-medium text-green-700">✅ {result.thanh_cong}/{result.tong} câu OK</span>
                  )}
                  {result.thanh_cong === 0 && (
                    <span className="text-sm font-medium text-red-600">❌ Không import được câu nào</span>
                  )}
                </div>
              </div>

              {/* Chi tiết lỗi */}
              {result.loi_chi_tiet.length > 0 && (
                <div className="border-t border-gray-200">
                  <div className="px-4 py-2 bg-gray-50 border-b border-gray-200">
                    <p className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                      Chi tiết {result.that_bai} dòng lỗi
                    </p>
                  </div>
                  <div className="max-h-40 overflow-y-auto divide-y divide-gray-100">
                    {result.loi_chi_tiet.map((item, idx) => (
                      <div key={idx} className="px-4 py-2 flex gap-3 text-xs">
                        <span className="shrink-0 font-mono text-gray-400 w-12">Dòng {item.dong}</span>
                        <span className="text-red-600">{item.loi}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
          <button
            onClick={handleClose}
            disabled={importing}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            {result ? 'Đóng' : 'Hủy'}
          </button>
          {!result && (
            <button
              onClick={handleImport}
              disabled={importing || !selectedFile}
              className="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {importing ? (
                <><span className="inline-block w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />Đang import...</>
              ) : '📤 Import câu hỏi'}
            </button>
          )}
          {result && result.thanh_cong > 0 && (
            <button
              onClick={() => { setSelectedFile(null); setResult(null); setErrMsg(''); if (fileInputRef.current) fileInputRef.current.value = ''; }}
              className="px-4 py-2 bg-blue-50 text-blue-700 border border-blue-200 rounded-lg text-sm font-medium hover:bg-blue-100"
            >
              Import thêm
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
