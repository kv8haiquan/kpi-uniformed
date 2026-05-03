'use client';

/**
 * components/admin/ImportPL3Modal.tsx
 * ===================================
 * Modal admin import Excel PL3 (Phase E — 29/04/2026).
 *
 * Flow 3 bước:
 *   1. Upload file .xlsx (≤10MB)
 *   2. Dry-run preview: summary + errors + 10 row đầu
 *   3. Commit: insert/update atomic, hiển thị kết quả
 *
 * Reject commit nếu dry-run còn errors → user phải sửa Excel.
 */

import { useState } from 'react';
import {
  X,
  Upload,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Download,
} from 'lucide-react';

import { isApiError } from '@/lib/axios';
import { adminPL3Service } from '@/services/admin-pl3.service';
import {
  IExcelImportError,
  IExcelImportPreviewRow,
  IExcelImportResponse,
} from '@/types/admin-pl3';

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

type Step = 'upload' | 'preview' | 'result';

const MAX_SIZE_MB = 10;

export function ImportPL3Modal({ open, onClose, onSuccess }: Props) {
  const [step, setStep] = useState<Step>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [dryRunData, setDryRunData] = useState<IExcelImportResponse | null>(null);
  const [commitData, setCommitData] = useState<IExcelImportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const reset = () => {
    setStep('upload');
    setFile(null);
    setDryRunData(null);
    setCommitData(null);
    setLoading(false);
    setErrorMsg(null);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMsg(null);
    const selected = e.target.files?.[0];
    if (!selected) return;
    if (!selected.name.toLowerCase().endsWith('.xlsx')) {
      setErrorMsg('Chỉ chấp nhận file .xlsx');
      return;
    }
    if (selected.size > MAX_SIZE_MB * 1024 * 1024) {
      setErrorMsg(`File quá lớn (${(selected.size / 1024 / 1024).toFixed(1)} MB > ${MAX_SIZE_MB} MB)`);
      return;
    }
    setFile(selected);
  };

  const goToPreview = async () => {
    if (!file) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await adminPL3Service.importDryRun(file);
      setDryRunData(res);
      setStep('preview');
    } catch (err: unknown) {
      console.error(err);
      setErrorMsg(isApiError(err) ? err.message : 'Lỗi parse file');
    } finally {
      setLoading(false);
    }
  };

  const handleCommit = async () => {
    if (!file) return;
    if (dryRunData && dryRunData.errors.length > 0) {
      setErrorMsg('Còn lỗi trong dry-run. Sửa Excel rồi upload lại.');
      return;
    }
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await adminPL3Service.importCommit(file);
      setCommitData(res);
      setStep('result');
      onSuccess(); // reload list ở parent
    } catch (err: unknown) {
      console.error(err);
      setErrorMsg(isApiError(err) ? err.message : 'Lỗi commit');
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Import danh mục PL3 từ Excel
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Bước {step === 'upload' ? 1 : step === 'preview' ? 2 : 3}/3 •{' '}
              {step === 'upload' && 'Upload file'}
              {step === 'preview' && 'Xem trước'}
              {step === 'result' && 'Hoàn tất'}
            </p>
          </div>
          <button onClick={handleClose} className="p-1 rounded hover:bg-gray-100">
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5">
          {/* STEP 1 — UPLOAD */}
          {step === 'upload' && (
            <UploadStep
              file={file}
              onFileSelect={handleFileSelect}
              errorMsg={errorMsg}
              loading={loading}
            />
          )}

          {/* STEP 2 — PREVIEW */}
          {step === 'preview' && dryRunData && (
            <PreviewStep data={dryRunData} errorMsg={errorMsg} />
          )}

          {/* STEP 3 — RESULT */}
          {step === 'result' && commitData && <ResultStep data={commitData} />}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 px-6 py-3 border-t border-gray-200 flex justify-between items-center">
          <div>
            {step === 'preview' && (
              <button
                type="button"
                onClick={() => setStep('upload')}
                disabled={loading}
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                ← Lùi
              </button>
            )}
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-60"
            >
              {step === 'result' ? 'Đóng' : 'Hủy'}
            </button>

            {step === 'upload' && (
              <button
                type="button"
                onClick={goToPreview}
                disabled={!file || loading}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-60"
              >
                {loading ? (
                  <span className="inline-flex items-center gap-1">
                    <Loader2 className="h-4 w-4 animate-spin" /> Đang parse…
                  </span>
                ) : (
                  'Tiếp →'
                )}
              </button>
            )}

            {step === 'preview' && (
              <button
                type="button"
                onClick={handleCommit}
                disabled={loading || (dryRunData?.errors.length ?? 0) > 0}
                className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-60"
              >
                {loading ? (
                  <span className="inline-flex items-center gap-1">
                    <Loader2 className="h-4 w-4 animate-spin" /> Đang commit…
                  </span>
                ) : (
                  'Commit ✓'
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// SUBCOMPONENTS
// =============================================================================

function UploadStep({
  file,
  onFileSelect,
  errorMsg,
  loading,
}: {
  file: File | null;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  errorMsg: string | null;
  loading: boolean;
}) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-700">
        Chọn file Excel (.xlsx) chứa danh mục PL3 với sheet tên <strong>PL3</strong>.
        Tối đa <strong>{MAX_SIZE_MB}MB</strong>.
      </p>

      <label
        className={[
          'block w-full border-2 border-dashed rounded-lg px-6 py-12 text-center cursor-pointer transition',
          file ? 'border-green-300 bg-green-50' : 'border-gray-300 hover:border-blue-400',
        ].join(' ')}
      >
        <Upload
          className={`h-10 w-10 mx-auto ${file ? 'text-green-600' : 'text-gray-400'}`}
        />
        <p className="mt-2 text-sm text-gray-700">
          {file ? (
            <>
              <strong>{file.name}</strong>{' '}
              <span className="text-gray-500">
                ({(file.size / 1024 / 1024).toFixed(2)} MB)
              </span>
            </>
          ) : (
            <>Click để chọn hoặc kéo thả file vào đây</>
          )}
        </p>
        <input
          type="file"
          accept=".xlsx"
          className="hidden"
          onChange={onFileSelect}
          disabled={loading}
        />
      </label>

      {errorMsg && (
        <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 flex items-start gap-2 text-sm text-red-800">
          <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      <div className="rounded-md bg-blue-50 border border-blue-200 px-4 py-3 text-xs text-blue-900">
        💡 Gợi ý: File Excel phải có sheet <code className="bg-white px-1 rounded">PL3</code>{' '}
        với cột Stt, Nhiệm vụ, Công việc chi tiết, Sản phẩm đầu ra, Phân nhóm,
        Khung điểm tối đa, Điểm chấm, Hệ số quy đổi.
      </div>
    </div>
  );
}

function PreviewStep({
  data,
  errorMsg,
}: {
  data: IExcelImportResponse;
  errorMsg: string | null;
}) {
  const { summary, errors, preview } = data;
  const hasErrors = errors.length > 0;
  return (
    <div className="space-y-5">
      {/* Summary */}
      <div className="grid grid-cols-3 gap-3">
        <SummaryCard label="Tổng dòng" value={summary.total_rows_in_file} />
        <SummaryCard label="Hợp lệ" value={summary.valid} color="text-green-700" />
        <SummaryCard
          label="Lỗi"
          value={summary.invalid}
          color={hasErrors ? 'text-red-700' : 'text-green-700'}
        />
        <SummaryCard label="Sẽ insert" value={summary.will_insert} color="text-blue-700" />
        <SummaryCard
          label="Sẽ update"
          value={summary.will_update}
          color="text-yellow-700"
        />
        <SummaryCard label="Bỏ qua" value={summary.skipped} />
      </div>

      {hasErrors && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3">
          <h3 className="text-sm font-medium text-red-900 mb-2 flex items-center gap-1">
            <AlertTriangle className="h-4 w-4" />
            Có {errors.length} lỗi — không thể commit
          </h3>
          <div className="max-h-48 overflow-y-auto text-xs space-y-1">
            {errors.slice(0, 30).map((e: IExcelImportError, idx: number) => (
              <div key={idx} className="flex gap-2">
                <span className="text-red-600 font-mono whitespace-nowrap">
                  Row {e.row}
                </span>
                {e.ma_danh_muc && (
                  <span className="text-gray-600 whitespace-nowrap">
                    [{e.ma_danh_muc}]
                  </span>
                )}
                <span className="text-red-800">{e.error}</span>
              </div>
            ))}
            {errors.length > 30 && (
              <div className="text-gray-500 italic">
                ... và {errors.length - 30} lỗi khác
              </div>
            )}
          </div>
        </div>
      )}

      {!hasErrors && (
        <div className="rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-900 flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4" />
          File hợp lệ. Sẵn sàng commit {summary.will_insert + summary.will_update} mục.
        </div>
      )}

      {/* Preview 10 rows */}
      <div>
        <h3 className="text-sm font-medium text-gray-900 mb-2">
          Preview 10 dòng đầu
        </h3>
        <div className="border border-gray-200 rounded-md overflow-x-auto">
          <table className="min-w-full text-xs">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-2 py-1 text-left">Mã</th>
                <th className="px-2 py-1 text-left">Tên</th>
                <th className="px-2 py-1 text-center">LV</th>
                <th className="px-2 py-1 text-center">Nhóm</th>
                <th className="px-2 py-1 text-right">Điểm</th>
                <th className="px-2 py-1 text-right">Hệ số</th>
                <th className="px-2 py-1 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {preview.map((r: IExcelImportPreviewRow, idx: number) => (
                <tr key={idx}>
                  <td className="px-2 py-1 font-mono text-gray-700">{r.ma_danh_muc}</td>
                  <td className="px-2 py-1 max-w-xs truncate" title={r.ten_cong_viec}>
                    {r.ten_cong_viec}
                  </td>
                  <td className="px-2 py-1 text-center">{r.linh_vuc}</td>
                  <td className="px-2 py-1 text-center">{r.nhom_pl3}</td>
                  <td className="px-2 py-1 text-right">{r.diem_cham}</td>
                  <td className="px-2 py-1 text-right font-mono">
                    {r.he_so_quy_doi.toFixed(2)}
                  </td>
                  <td className="px-2 py-1 text-center">
                    <span
                      className={
                        r.action === 'insert'
                          ? 'text-blue-700 font-medium'
                          : 'text-yellow-700'
                      }
                    >
                      {r.action}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {errorMsg && (
        <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-800">
          {errorMsg}
        </div>
      )}
    </div>
  );
}

function ResultStep({ data }: { data: IExcelImportResponse }) {
  const { summary } = data;
  return (
    <div className="space-y-5">
      <div className="rounded-md bg-green-50 border border-green-300 px-5 py-4 flex items-start gap-3">
        <CheckCircle2 className="h-6 w-6 text-green-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-green-900">Import thành công</p>
          <div className="mt-1 text-sm text-gray-700 space-y-0.5">
            <div>
              Đã insert: <strong>{summary.actually_inserted ?? summary.will_insert}</strong>
            </div>
            <div>
              Đã update: <strong>{summary.actually_updated ?? summary.will_update}</strong>
            </div>
            <div>Lỗi: <strong>0</strong></div>
          </div>
        </div>
      </div>

      <p className="text-xs text-gray-500">
        File hash: <code className="text-[10px] bg-gray-100 px-1">{data.file_hash}</code>
      </p>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color?: string;
}) {
  return (
    <div className="border border-gray-200 rounded-md px-4 py-2">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`text-xl font-bold mt-0.5 ${color ?? 'text-gray-900'}`}>{value}</p>
    </div>
  );
}
