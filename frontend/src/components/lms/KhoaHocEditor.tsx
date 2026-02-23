/**
 * src/components/lms/KhoaHocEditor.tsx
 * =======================================
 * Multi-step editor cho Khóa học:
 *   Bước 1 — Thông tin cơ bản (tạo mới hoặc sửa)
 *   Bước 2 — Quản lý bài học (thêm / sửa / xóa / sắp xếp)
 *
 * Dùng trong tab "Tạo / Sửa" của trang /dao-tao/quan-ly.
 * Quyền: GIANG_VIEN (khóa của mình), QT_DAO_TAO, ADMIN.
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { khoaHocApi, baiHocApi } from '@/services/lms';
import type { IKhoaHoc, IBaiHoc, IChuyenDe, IBaiHocCreate } from '@/types/lms';
import BaiKiemTraManager from '@/components/lms/BaiKiemTraManager';
import FileUploader, { type UploadResult } from '@/components/lms/FileUploader';

// =============================================================================
// CONSTANTS
// =============================================================================

const LOAI_OPTIONS = [
  { value: 'TU_HOC',    label: 'Tự học' },
  { value: 'BAT_BUOC',  label: 'Bắt buộc' },
  { value: 'TRUC_TUYEN', label: 'Trực tuyến' },
  { value: 'KET_HOP',   label: 'Kết hợp' },
];

const LOAI_NOI_DUNG_OPTIONS = [
  { value: 'HTML',  label: '📝 HTML / Văn bản' },
  { value: 'VIDEO', label: '🎬 Video' },
  { value: 'PDF',   label: '📄 PDF' },
  { value: 'SLIDE', label: '📊 Slide / Trình chiếu' },
];

const LOAI_NOI_DUNG_ICON: Record<string, string> = {
  HTML: '📝', VIDEO: '🎬', PDF: '📄', SLIDE: '📊',
};

// =============================================================================
// FORM STATE TYPES
// =============================================================================

interface KhoaHocForm {
  ma_khoa_hoc:       string;
  ten_khoa_hoc:      string;
  mo_ta:             string;
  chuyen_de_id:      string;
  loai:              string;
  thoi_luong_phut:   string;
  diem_dat_yeu_cau:  string;
  ngay_bat_dau:      string;
  ngay_ket_thuc:     string;
}

const KHOA_HOC_DEFAULT: KhoaHocForm = {
  ma_khoa_hoc: '',
  ten_khoa_hoc: '',
  mo_ta: '',
  chuyen_de_id: '',
  loai: 'TU_HOC',
  thoi_luong_phut: '',
  diem_dat_yeu_cau: '70',
  ngay_bat_dau: '',
  ngay_ket_thuc: '',
};

interface BaiHocForm {
  tieu_de:         string;
  thu_tu:          string;
  loai_noi_dung:   string;
  noi_dung:        string;    // HTML content hoặc URL (khi dùng chế độ "nhập URL")
  file_url:        string;    // URL file đã upload (khi dùng chế độ "upload file")
  thoi_luong_phut: string;
  phai_xem_het:    boolean;
}

// =============================================================================
// SUB-COMPONENT: Modal thêm / sửa Bài học
// =============================================================================

interface BaiHocModalProps {
  mode:        'tao' | 'sua';
  init?:       IBaiHoc | null;
  khoaHocId:   string;
  nextThuTu:   number;
  onClose:     () => void;
  onSuccess:   () => void;
}

function BaiHocModal({ mode, init, khoaHocId, nextThuTu, onClose, onSuccess }: BaiHocModalProps) {
  const [form, setForm] = useState<BaiHocForm>(
    init
      ? {
          tieu_de:         init.tieu_de,
          thu_tu:          String(init.thu_tu),
          loai_noi_dung:   init.loai_noi_dung,
          noi_dung:        init.noi_dung ?? '',
          file_url:        init.file_url ?? '',
          thoi_luong_phut: init.thoi_luong_phut ? String(init.thoi_luong_phut) : '',
          phai_xem_het:    init.phai_xem_het,
        }
      : {
          tieu_de: '',
          thu_tu: String(nextThuTu),
          loai_noi_dung: 'HTML',
          noi_dung: '',
          file_url: '',
          thoi_luong_phut: '',
          phai_xem_het: false,
        }
  );
  // Chế độ nhập nội dung: 'upload' (kéo thả file) hoặc 'url' (nhập tay)
  // Default 'upload' cho bài học mới; 'url' nếu đang sửa và chỉ có noi_dung (URL)
  const [inputMode, setInputMode] = useState<'upload' | 'url'>(
    init?.file_url ? 'upload' : (init?.noi_dung ? 'url' : 'upload')
  );
  const [submitting, setSubmitting] = useState(false);
  const [errMsg, setErrMsg] = useState('');

  // Đóng bằng phím Escape
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const handleSubmit = async () => {
    if (!form.tieu_de.trim()) { setErrMsg('Tiêu đề bài học là bắt buộc'); return; }
    setSubmitting(true);
    setErrMsg('');
    try {
      // file_url: ưu tiên file đã upload; nếu nhập URL thủ công thì lấy noi_dung
      const resolvedFileUrl =
        form.loai_noi_dung !== 'HTML' && inputMode === 'upload'
          ? form.file_url.trim()
          : form.loai_noi_dung !== 'HTML' && inputMode === 'url'
          ? form.noi_dung.trim()
          : undefined;

      const payload: IBaiHocCreate = {
        tieu_de:       form.tieu_de.trim(),
        thu_tu:        Number(form.thu_tu) || nextThuTu,
        loai_noi_dung: form.loai_noi_dung,
        phai_xem_het:  form.phai_xem_het,
        // Với HTML: lưu nội dung vào noi_dung
        ...(form.loai_noi_dung === 'HTML' && form.noi_dung.trim() && { noi_dung: form.noi_dung.trim() }),
        // Với file: lưu URL vào file_url
        ...(resolvedFileUrl             && { file_url:        resolvedFileUrl }),
        ...(form.thoi_luong_phut        && { thoi_luong_phut: Number(form.thoi_luong_phut) }),
      };
      if (mode === 'tao') {
        await baiHocApi.taoMoi(khoaHocId, payload);
      } else {
        await baiHocApi.capNhat(init!.id, payload);
      }
      onSuccess();
    } catch (err: any) {
      setErrMsg(err?.response?.data?.detail?.error?.message || 'Lỗi lưu bài học. Thử lại sau.');
    } finally {
      setSubmitting(false);
    }
  };

  // Placeholder URL (chế độ "nhập URL")
  const noiDungPlaceholder =
    form.loai_noi_dung === 'VIDEO' ? 'https://youtube.com/watch?v=... hoặc /uploads/lms/video/abc.mp4' :
    form.loai_noi_dung === 'PDF'   ? 'https://example.com/file.pdf hoặc /uploads/lms/tai-lieu/abc.pdf' :
    'https://example.com/slide.pptx hoặc /uploads/lms/bai-hoc/abc.pptx';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 max-h-[92vh] overflow-y-auto p-6">
        {/* Tiêu đề modal */}
        <h3 className="text-lg font-semibold text-gray-900 mb-5">
          {mode === 'tao' ? '➕ Thêm bài học' : '✏️ Sửa bài học'}
        </h3>

        <div className="space-y-4">
          {/* Tiêu đề */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tiêu đề <span className="text-red-500">*</span>
            </label>
            <input
              autoFocus
              type="text"
              value={form.tieu_de}
              onChange={(e) => setForm({ ...form, tieu_de: e.target.value })}
              placeholder="VD: Bài 1: Giới thiệu tổng quan"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Loại nội dung + Thứ tự */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Loại nội dung</label>
              <select
                value={form.loai_noi_dung}
                onChange={(e) => setForm({ ...form, loai_noi_dung: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {LOAI_NOI_DUNG_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Thứ tự</label>
              <input
                type="number" min={1}
                value={form.thu_tu}
                onChange={(e) => setForm({ ...form, thu_tu: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Thời lượng + Phải xem hết */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Thời lượng (phút)</label>
              <input
                type="number" min={0}
                value={form.thoi_luong_phut}
                onChange={(e) => setForm({ ...form, thoi_luong_phut: e.target.value })}
                placeholder="VD: 15"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-end pb-2.5">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={form.phai_xem_het}
                  onChange={(e) => setForm({ ...form, phai_xem_het: e.target.checked })}
                  className="w-4 h-4 accent-blue-600"
                />
                <span className="text-sm text-gray-700">Phải xem hết</span>
              </label>
            </div>
          </div>

          {/* Nội dung */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Nội dung</label>

            {form.loai_noi_dung === 'HTML' ? (
              /* HTML: textarea soạn nội dung */
              <textarea
                rows={5}
                value={form.noi_dung}
                onChange={(e) => setForm({ ...form, noi_dung: e.target.value })}
                placeholder='<p>Nội dung HTML của bài học...</p>'
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            ) : (
              /* VIDEO / PDF / SLIDE: toggle upload vs URL */
              <>
                {/* Toggle */}
                <div className="flex gap-1 mb-3 bg-gray-100 rounded-lg p-1">
                  {(['upload', 'url'] as const).map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setInputMode(m)}
                      className={`flex-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                        inputMode === m
                          ? 'bg-white shadow-sm text-gray-900'
                          : 'text-gray-500 hover:text-gray-700'
                      }`}
                    >
                      {m === 'upload' ? '📂 Upload file từ máy' : '🔗 Nhập URL có sẵn'}
                    </button>
                  ))}
                </div>

                {inputMode === 'upload' ? (
                  <FileUploader
                    accept={
                      form.loai_noi_dung === 'PDF'   ? '.pdf' :
                      form.loai_noi_dung === 'VIDEO' ? '.mp4,.webm,.avi,.mov' :
                      form.loai_noi_dung === 'SLIDE' ? '.pptx,.ppt,.pdf' :
                      undefined
                    }
                    folder={
                      form.loai_noi_dung === 'VIDEO' ? 'video' :
                      form.loai_noi_dung === 'PDF'   ? 'tai-lieu' :
                      'bai-hoc'
                    }
                    currentFileUrl={form.file_url || null}
                    onUploadDone={(result: UploadResult) =>
                      setForm((prev) => ({ ...prev, file_url: result.file_url }))
                    }
                  />
                ) : (
                  <input
                    type="url"
                    value={form.noi_dung}
                    onChange={(e) => setForm({ ...form, noi_dung: e.target.value })}
                    placeholder={noiDungPlaceholder}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                )}
              </>
            )}
          </div>

          {/* Lỗi */}
          {errMsg && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              <p className="text-sm text-red-600">{errMsg}</p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
          <button
            onClick={onClose} disabled={submitting}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            Hủy
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || !form.tieu_de.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? 'Đang lưu...' : mode === 'tao' ? 'Thêm bài học' : 'Lưu thay đổi'}
          </button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN: KhoaHocEditor
// =============================================================================

export interface KhoaHocEditorProps {
  /** UUID khóa học khi sửa; undefined/null = tạo mới */
  khoaHocId?: string | null;
  /** Danh sách chuyên đề để render dropdown — đã load từ parent */
  chuyenDes:  IChuyenDe[];
  /** Gọi sau khi hoàn tất (tạo hoặc sửa xong) */
  onSuccess:  () => void;
  /** Gọi khi user huỷ bỏ */
  onBack:     () => void;
}

export default function KhoaHocEditor({ khoaHocId, chuyenDes, onSuccess, onBack }: KhoaHocEditorProps) {
  const isEditMode = !!khoaHocId;

  // Bước hiện tại (1 hoặc 2)
  const [step, setStep] = useState<1 | 2>(1);
  // ID khóa học đã lưu (sau khi POST thành công, hoặc = khoaHocId khi edit)
  const [savedId, setSavedId] = useState<string | null>(khoaHocId ?? null);

  // --- State bước 1: form thông tin ---
  const [form, setForm]               = useState<KhoaHocForm>(KHOA_HOC_DEFAULT);
  const [initLoading, setInitLoading] = useState(isEditMode);
  const [s1Submitting, setS1Submitting] = useState(false);
  const [s1Error, setS1Error]         = useState('');

  // --- State bước 2: sub-tab ---
  const [step2Tab, setStep2Tab]         = useState<'bai-hoc' | 'bai-kiem-tra'>('bai-hoc');

  // --- State bước 2: bài học ---
  const [baiHocs, setBaiHocs]           = useState<IBaiHoc[]>([]);
  const [bhLoading, setBhLoading]       = useState(false);
  const [showBhModal, setShowBhModal]   = useState(false);
  const [editBh, setEditBh]             = useState<IBaiHoc | null>(null);
  const [deleteBhId, setDeleteBhId]     = useState<string | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [reordering, setReordering]     = useState(false);

  // Load thông tin khóa học khi edit mode
  useEffect(() => {
    if (!khoaHocId) return;
    const loadCourse = async () => {
      setInitLoading(true);
      try {
        const res = await khoaHocApi.chiTiet(khoaHocId);
        const kh: IKhoaHoc = res.data.data;
        setForm({
          ma_khoa_hoc:      kh.ma_khoa_hoc,
          ten_khoa_hoc:     kh.ten_khoa_hoc,
          mo_ta:            kh.mo_ta ?? '',
          chuyen_de_id:     kh.chuyen_de_id ?? '',
          loai:             kh.loai,
          thoi_luong_phut:  kh.thoi_luong_phut ? String(kh.thoi_luong_phut) : '',
          diem_dat_yeu_cau: String(kh.diem_dat_yeu_cau),
          ngay_bat_dau:     kh.ngay_bat_dau ?? '',
          ngay_ket_thuc:    kh.ngay_ket_thuc ?? '',
        });
      } catch {
        setS1Error('Không thể tải thông tin khóa học. Kiểm tra LMS backend (port 8001).');
      } finally {
        setInitLoading(false);
      }
    };
    loadCourse();
  }, [khoaHocId]);

  // Load danh sách bài học
  const loadBaiHocs = useCallback(async (id: string) => {
    setBhLoading(true);
    try {
      const res = await baiHocApi.danhSach(id);
      const data: IBaiHoc[] = res.data.data || [];
      setBaiHocs([...data].sort((a, b) => a.thu_tu - b.thu_tu));
    } catch {
      // Bỏ qua lỗi load bài học
    } finally {
      setBhLoading(false);
    }
  }, []);

  // Khi chuyển sang bước 2 → load bài học
  useEffect(() => {
    if (step === 2 && savedId) loadBaiHocs(savedId);
  }, [step, savedId, loadBaiHocs]);

  // Submit bước 1: Tạo mới hoặc cập nhật khóa học
  const handleStep1Submit = async () => {
    if (!form.ma_khoa_hoc.trim() || !form.ten_khoa_hoc.trim()) {
      setS1Error('Mã và Tên khóa học là bắt buộc');
      return;
    }
    setS1Submitting(true);
    setS1Error('');
    try {
      // Chỉ gửi các field có giá trị để tránh ghi đè null không cần thiết
      const payload: Record<string, unknown> = {
        ma_khoa_hoc:      form.ma_khoa_hoc.trim(),
        ten_khoa_hoc:     form.ten_khoa_hoc.trim(),
        loai:             form.loai,
        diem_dat_yeu_cau: form.diem_dat_yeu_cau ? Number(form.diem_dat_yeu_cau) : 70,
        ...(form.mo_ta.trim()       && { mo_ta:           form.mo_ta.trim() }),
        ...(form.chuyen_de_id       && { chuyen_de_id:    form.chuyen_de_id }),
        ...(form.thoi_luong_phut    && { thoi_luong_phut: Number(form.thoi_luong_phut) }),
        ...(form.ngay_bat_dau       && { ngay_bat_dau:    form.ngay_bat_dau }),
        ...(form.ngay_ket_thuc      && { ngay_ket_thuc:   form.ngay_ket_thuc }),
      };

      if (savedId) {
        // Chế độ sửa: PUT
        await khoaHocApi.capNhat(savedId, payload);
      } else {
        // Chế độ tạo: POST → lấy ID mới
        const res = await khoaHocApi.taoMoi(payload);
        setSavedId(res.data.data.id);
      }
      setStep(2);
    } catch (err: any) {
      setS1Error(err?.response?.data?.detail?.error?.message || 'Lỗi lưu khóa học. Thử lại sau.');
    } finally {
      setS1Submitting(false);
    }
  };

  // Di chuyển bài học lên hoặc xuống (optimistic update + gọi API)
  const handleMove = async (index: number, dir: 'up' | 'down') => {
    if (!savedId) return;
    const target = dir === 'up' ? index - 1 : index + 1;
    if (target < 0 || target >= baiHocs.length) return;

    // Swap và reindex
    const updated = [...baiHocs];
    [updated[index], updated[target]] = [updated[target], updated[index]];
    const reindexed = updated.map((b, i) => ({ ...b, thu_tu: i + 1 }));
    setBaiHocs(reindexed);

    setReordering(true);
    try {
      await baiHocApi.sapXep(savedId, {
        thu_tu: reindexed.map((b) => ({ bai_hoc_id: b.id, thu_tu: b.thu_tu })),
      });
    } catch {
      // Hoàn tác nếu API lỗi
      loadBaiHocs(savedId);
    } finally {
      setReordering(false);
    }
  };

  // Xóa bài học sau xác nhận
  const handleDeleteBaiHoc = async () => {
    if (!deleteBhId || !savedId) return;
    setDeleteLoading(true);
    try {
      await baiHocApi.xoa(deleteBhId);
      setDeleteBhId(null);
      loadBaiHocs(savedId);
    } catch (err: any) {
      alert(err?.response?.data?.detail?.error?.message || 'Không thể xóa bài học.');
    } finally {
      setDeleteLoading(false);
    }
  };

  // Skeleton loading khi đang load thông tin khóa học (edit mode)
  if (initLoading) {
    return (
      <div className="max-w-3xl space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-12 bg-gray-100 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  // ==========================================================================
  // RENDER
  // ==========================================================================
  return (
    <div className="max-w-3xl">
      {/* ── Thanh chỉ báo bước ── */}
      <div className="flex items-center mb-6">
        {/* Bước 1 */}
        <div className="flex items-center gap-2 shrink-0">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-colors ${
            step === 1
              ? 'bg-blue-600 border-blue-600 text-white'
              : 'bg-green-500 border-green-500 text-white'
          }`}>
            {step > 1 ? '✓' : '1'}
          </div>
          <span className={`text-sm font-medium ${step === 1 ? 'text-blue-700' : 'text-green-600'}`}>
            Thông tin cơ bản
          </span>
        </div>

        {/* Connector */}
        <div className="flex-1 mx-3 h-0.5 bg-gray-200 overflow-hidden">
          <div className={`h-full bg-blue-500 transition-all duration-300 ${step >= 2 ? 'w-full' : 'w-0'}`} />
        </div>

        {/* Bước 2 */}
        <div className="flex items-center gap-2 shrink-0">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-colors ${
            step === 2
              ? 'bg-blue-600 border-blue-600 text-white'
              : !savedId
              ? 'border-gray-200 text-gray-300'
              : 'border-gray-300 text-gray-500'
          }`}>
            2
          </div>
          <span className={`text-sm font-medium ${
            step === 2 ? 'text-blue-700' : !savedId ? 'text-gray-300' : 'text-gray-500'
          }`}>
            Nội dung bài học
          </span>
        </div>
      </div>

      {/* ================================================================== */}
      {/* BƯỚC 1 — Thông tin cơ bản                                          */}
      {/* ================================================================== */}
      {step === 1 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-5">
            {isEditMode ? 'Chỉnh sửa thông tin khóa học' : 'Thông tin khóa học mới'}
          </h2>

          <div className="space-y-4">
            {/* Mã + Tên */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mã khóa học <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.ma_khoa_hoc}
                  onChange={(e) => setForm({ ...form, ma_khoa_hoc: e.target.value })}
                  placeholder="VD: KH-2026-001"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tên khóa học <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.ten_khoa_hoc}
                  onChange={(e) => setForm({ ...form, ten_khoa_hoc: e.target.value })}
                  placeholder="VD: Luật Hải quan 2024"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Chuyên đề + Loại */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Chuyên đề</label>
                <select
                  value={form.chuyen_de_id}
                  onChange={(e) => setForm({ ...form, chuyen_de_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">— Không thuộc chuyên đề nào —</option>
                  {chuyenDes.map((cd) => (
                    <option key={cd.id} value={cd.id}>{cd.ten_chuyen_de}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Loại khóa học</label>
                <select
                  value={form.loai}
                  onChange={(e) => setForm({ ...form, loai: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {LOAI_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Mô tả */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Mô tả</label>
              <textarea
                rows={3}
                value={form.mo_ta}
                onChange={(e) => setForm({ ...form, mo_ta: e.target.value })}
                placeholder="Mô tả nội dung và mục tiêu khóa học..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Thời lượng + Điểm đạt */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Thời lượng (phút)
                </label>
                <input
                  type="number" min={0}
                  value={form.thoi_luong_phut}
                  onChange={(e) => setForm({ ...form, thoi_luong_phut: e.target.value })}
                  placeholder="VD: 120"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Điểm đạt yêu cầu (%)
                </label>
                <input
                  type="number" min={0} max={100}
                  value={form.diem_dat_yeu_cau}
                  onChange={(e) => setForm({ ...form, diem_dat_yeu_cau: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Ngày bắt đầu + Ngày kết thúc */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Ngày bắt đầu
                </label>
                <input
                  type="date"
                  value={form.ngay_bat_dau}
                  onChange={(e) => setForm({ ...form, ngay_bat_dau: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Ngày kết thúc
                </label>
                <input
                  type="date"
                  value={form.ngay_ket_thuc}
                  onChange={(e) => setForm({ ...form, ngay_ket_thuc: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Lỗi bước 1 */}
            {s1Error && (
              <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                <p className="text-sm text-red-600">{s1Error}</p>
              </div>
            )}
          </div>

          {/* Action buttons bước 1 */}
          <div className="flex justify-between mt-6 pt-4 border-t border-gray-100">
            <button
              onClick={onBack}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Hủy
            </button>
            <div className="flex gap-2">
              {/* Khi edit mode: cho phép nhảy thẳng sang xem bài học */}
              {isEditMode && savedId && (
                <button
                  onClick={() => setStep(2)}
                  className="px-4 py-2 border border-blue-300 text-blue-700 rounded-lg text-sm hover:bg-blue-50"
                >
                  Xem bài học →
                </button>
              )}
              <button
                onClick={handleStep1Submit}
                disabled={s1Submitting || !form.ma_khoa_hoc.trim() || !form.ten_khoa_hoc.trim()}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {s1Submitting
                  ? 'Đang lưu...'
                  : savedId
                  ? 'Lưu & Tiếp theo →'
                  : 'Tạo & Tiếp theo →'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ================================================================== */}
      {/* BƯỚC 2 — Quản lý bài học                                          */}
      {/* ================================================================== */}
      {step === 2 && savedId && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          {/* Header bước 2 */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-900">Nội dung khóa học</h2>
            {/* Nút thêm — chỉ hiển thị cho bài học */}
            {step2Tab === 'bai-hoc' && (
              <button
                onClick={() => { setEditBh(null); setShowBhModal(true); }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 flex items-center gap-1.5"
              >
                <span>➕</span> Thêm bài học
              </button>
            )}
          </div>

          {/* Sub-tabs: Bài học | Bài kiểm tra */}
          <div className="flex gap-1 mb-4 bg-gray-100 rounded-lg p-1">
            {([
              ['bai-hoc',      `📚 Bài học (${baiHocs.length})`],
              ['bai-kiem-tra', '📝 Bài kiểm tra'],
            ] as ['bai-hoc' | 'bai-kiem-tra', string][]).map(([k, label]) => (
              <button
                key={k}
                onClick={() => setStep2Tab(k)}
                className={`flex-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  step2Tab === k
                    ? 'bg-white shadow-sm text-gray-900'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* ── Sub-tab: Bài học ── */}
          {step2Tab === 'bai-hoc' && (
            <>
              <p className="text-xs text-gray-400 mb-3">Dùng ↑↓ để sắp xếp thứ tự hiển thị</p>
              {bhLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-14 bg-gray-100 rounded-lg animate-pulse" />
                  ))}
                </div>
              ) : baiHocs.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200 text-gray-500">
                  <span className="text-4xl block mb-2">📚</span>
                  <p className="font-medium">Chưa có bài học nào</p>
                  <p className="text-sm mt-1">Nhấn "Thêm bài học" để xây dựng nội dung</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {baiHocs.map((bh, idx) => (
                    <div
                      key={bh.id}
                      className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <span className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center text-xs font-bold text-gray-600 shrink-0">
                        {bh.thu_tu}
                      </span>
                      <span className="text-lg shrink-0">
                        {LOAI_NOI_DUNG_ICON[bh.loai_noi_dung] ?? '📄'}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{bh.tieu_de}</p>
                        <p className="text-xs text-gray-500">
                          {bh.loai_noi_dung}
                          {bh.thoi_luong_phut ? ` · ${bh.thoi_luong_phut} phút` : ''}
                          {bh.phai_xem_het ? ' · Phải xem hết' : ''}
                        </p>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <button
                          onClick={() => handleMove(idx, 'up')}
                          disabled={idx === 0 || reordering}
                          title="Lên"
                          className="px-1.5 py-1 text-gray-400 hover:text-gray-700 disabled:opacity-30 disabled:cursor-not-allowed text-base leading-none"
                        >↑</button>
                        <button
                          onClick={() => handleMove(idx, 'down')}
                          disabled={idx === baiHocs.length - 1 || reordering}
                          title="Xuống"
                          className="px-1.5 py-1 text-gray-400 hover:text-gray-700 disabled:opacity-30 disabled:cursor-not-allowed text-base leading-none"
                        >↓</button>
                        <button
                          onClick={() => { setEditBh(bh); setShowBhModal(true); }}
                          className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs hover:bg-yellow-200 ml-1"
                        >Sửa</button>
                        <button
                          onClick={() => setDeleteBhId(bh.id)}
                          className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs hover:bg-red-200"
                        >Xóa</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {/* ── Sub-tab: Bài kiểm tra ── */}
          {step2Tab === 'bai-kiem-tra' && (
            <BaiKiemTraManager khoaHocId={savedId} />
          )}

          {/* Footer bước 2 */}
          <div className="flex justify-between mt-6 pt-4 border-t border-gray-100">
            <button
              onClick={() => setStep(1)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              ← Quay lại
            </button>
            <button
              onClick={onSuccess}
              className="px-6 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700"
            >
              ✓ Hoàn tất
            </button>
          </div>
        </div>
      )}

      {/* Modal thêm / sửa bài học */}
      {showBhModal && savedId && (
        <BaiHocModal
          mode={editBh ? 'sua' : 'tao'}
          init={editBh}
          khoaHocId={savedId}
          nextThuTu={baiHocs.length + 1}
          onClose={() => { setShowBhModal(false); setEditBh(null); }}
          onSuccess={() => {
            setShowBhModal(false);
            setEditBh(null);
            loadBaiHocs(savedId);
          }}
        />
      )}

      {/* Dialog xác nhận xóa bài học */}
      {deleteBhId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setDeleteBhId(null)} />
          <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-sm mx-4 p-6">
            <h3 className="text-lg font-semibold mb-2">Xóa bài học</h3>
            <p className="text-sm text-gray-600 mb-5">
              Bạn có chắc muốn xóa bài học này không? Hành động không thể hoàn tác.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteBhId(null)} disabled={deleteLoading}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
              >Hủy</button>
              <button
                onClick={handleDeleteBaiHoc} disabled={deleteLoading}
                className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50"
              >
                {deleteLoading ? 'Đang xóa...' : 'Xóa'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
