/**
 * src/components/lms/CauHoiManager.tsx
 * =======================================
 * Quản lý ngân hàng câu hỏi:
 *   - Danh sách với filter (loại, độ khó, khóa học)
 *   - Form tạo/sửa với đáp án động tuỳ theo loại câu hỏi
 *   - Xóa câu hỏi với xác nhận
 *
 * Quyền: GIANG_VIEN, QT_DAO_TAO, ADMIN (backend kiểm tra).
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { cauHoiApi, khoaHocApi, baiKiemTraApi } from '@/services/lms';
import type { ICauHoi, ICauHoiCreate, IPagination, IKhoaHoc, IBaiKiemTra } from '@/types/lms';
import ImportCauHoiDialog from '@/components/lms/ImportCauHoiDialog';

// =============================================================================
// CONSTANTS
// =============================================================================

const LOAI_CAU_HOI = [
  { value: 'TRAC_NGHIEM_1',    label: 'Trắc nghiệm 1 đáp án' },
  { value: 'TRAC_NGHIEM_NHIEU', label: 'Trắc nghiệm nhiều đáp án' },
  { value: 'DUNG_SAI',         label: 'Đúng / Sai' },
  { value: 'TU_LUAN',          label: 'Tự luận' },
];

const DO_KHO = [
  { value: 'DE',       label: 'Dễ',       color: 'bg-green-100 text-green-700' },
  { value: 'TRUNG_BINH', label: 'Trung bình', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'KHO',      label: 'Khó',      color: 'bg-red-100 text-red-700' },
];

const LOAI_LABEL: Record<string, string> = {
  TRAC_NGHIEM_1:    'TN-1',
  TRAC_NGHIEM_NHIEU: 'TN-N',
  DUNG_SAI:         'Đ/S',
  TU_LUAN:          'TL',
};

// =============================================================================
// HELPER: build/parse đáp án
// =============================================================================

interface FormState {
  noi_dung:       string;
  loai:           string;
  do_kho:         string;
  diem:           string;
  khoa_hoc_id:    string;
  bai_kiem_tra_id: string;
  giai_thich:     string;
  // TRAC_NGHIEM_1 / TRAC_NGHIEM_NHIEU
  options:        string[];
  correctSingle:  number;
  correctMultiple: number[];
  // DUNG_SAI
  dungSai:        boolean;
  // TU_LUAN
  goiY:           string;
}

const DEFAULT_FORM: FormState = {
  noi_dung: '',
  loai: 'TRAC_NGHIEM_1',
  do_kho: 'TRUNG_BINH',
  diem: '1',
  khoa_hoc_id: '',
  bai_kiem_tra_id: '',
  giai_thich: '',
  options: ['', ''],
  correctSingle: 0,
  correctMultiple: [],
  dungSai: true,
  goiY: '',
};

function buildDapAn(form: FormState): Record<string, unknown> {
  switch (form.loai) {
    case 'TRAC_NGHIEM_1':
      return { options: form.options, correct: form.correctSingle };
    case 'TRAC_NGHIEM_NHIEU':
      return { options: form.options, correct: form.correctMultiple };
    case 'DUNG_SAI':
      return { correct: form.dungSai };
    case 'TU_LUAN':
      return form.goiY.trim() ? { goi_y: form.goiY.trim() } : {};
    default:
      return {};
  }
}

function parseDapAn(loai: string, dap_an: Record<string, unknown>): Partial<FormState> {
  switch (loai) {
    case 'TRAC_NGHIEM_1':
      return {
        options:       (dap_an.options as string[]) || ['', ''],
        correctSingle: (dap_an.correct as number) ?? 0,
      };
    case 'TRAC_NGHIEM_NHIEU':
      return {
        options:         (dap_an.options as string[]) || ['', ''],
        correctMultiple: (dap_an.correct as number[]) || [],
      };
    case 'DUNG_SAI':
      return { dungSai: (dap_an.correct as boolean) ?? true };
    case 'TU_LUAN':
      return { goiY: (dap_an.goi_y as string) ?? '' };
    default:
      return {};
  }
}

// =============================================================================
// SUB: Form đáp án động
// =============================================================================

function DapAnForm({ form, setForm }: { form: FormState; setForm: (f: FormState) => void }) {
  const addOption = () => setForm({ ...form, options: [...form.options, ''] });
  const removeOption = (i: number) => {
    const opts = form.options.filter((_, idx) => idx !== i);
    // Điều chỉnh correctSingle nếu cần
    const cs = form.correctSingle >= opts.length ? 0 : form.correctSingle;
    // Loại correctMultiple chứa index > opts.length
    const cm = form.correctMultiple.filter((c) => c < opts.length);
    setForm({ ...form, options: opts, correctSingle: cs, correctMultiple: cm });
  };
  const updateOption = (i: number, val: string) => {
    const opts = [...form.options];
    opts[i] = val;
    setForm({ ...form, options: opts });
  };
  const toggleMultiple = (i: number) => {
    const cm = form.correctMultiple.includes(i)
      ? form.correctMultiple.filter((c) => c !== i)
      : [...form.correctMultiple, i];
    setForm({ ...form, correctMultiple: cm });
  };

  // TRAC_NGHIEM_1 và TRAC_NGHIEM_NHIEU
  if (form.loai === 'TRAC_NGHIEM_1' || form.loai === 'TRAC_NGHIEM_NHIEU') {
    const isMulti = form.loai === 'TRAC_NGHIEM_NHIEU';
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Các lựa chọn{' '}
          <span className="text-gray-400 font-normal">
            ({isMulti ? 'Checkbox nhiều đáp án đúng' : 'Radio 1 đáp án đúng'})
          </span>
        </label>
        <div className="space-y-2">
          {form.options.map((opt, i) => (
            <div key={i} className="flex items-center gap-2">
              {/* Radio/Checkbox chọn đúng */}
              {isMulti ? (
                <input
                  type="checkbox"
                  checked={form.correctMultiple.includes(i)}
                  onChange={() => toggleMultiple(i)}
                  className="w-4 h-4 accent-blue-600 shrink-0"
                  title="Đáp án đúng"
                />
              ) : (
                <input
                  type="radio"
                  name="correct_single"
                  checked={form.correctSingle === i}
                  onChange={() => setForm({ ...form, correctSingle: i })}
                  className="w-4 h-4 accent-blue-600 shrink-0"
                  title="Đáp án đúng"
                />
              )}
              {/* Input nội dung lựa chọn */}
              <input
                type="text"
                value={opt}
                onChange={(e) => updateOption(i, e.target.value)}
                placeholder={`Lựa chọn ${String.fromCharCode(65 + i)}`}
                className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              {/* Nút xóa (chỉ khi còn > 2 lựa chọn) */}
              {form.options.length > 2 && (
                <button
                  type="button"
                  onClick={() => removeOption(i)}
                  className="text-red-400 hover:text-red-600 px-1 text-lg leading-none shrink-0"
                  title="Xóa lựa chọn"
                >×</button>
              )}
            </div>
          ))}
        </div>
        {/* Nút thêm lựa chọn (tối đa 6) */}
        {form.options.length < 6 && (
          <button
            type="button"
            onClick={addOption}
            className="mt-2 text-sm text-blue-600 hover:underline flex items-center gap-1"
          >
            <span>+</span> Thêm lựa chọn
          </button>
        )}
        <p className="text-xs text-gray-400 mt-1">
          {isMulti
            ? 'Tích vào checkbox bên trái để đánh dấu đáp án đúng (có thể chọn nhiều)'
            : 'Click radio bên trái để chọn đáp án đúng (chỉ 1 đáp án)'}
        </p>
      </div>
    );
  }

  // DUNG_SAI
  if (form.loai === 'DUNG_SAI') {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Đáp án đúng</label>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => setForm({ ...form, dungSai: true })}
            className={`px-5 py-2 rounded-lg text-sm font-medium border-2 transition-colors ${
              form.dungSai
                ? 'bg-green-500 border-green-500 text-white'
                : 'border-gray-300 text-gray-600 hover:border-green-400'
            }`}
          >✓ Đúng</button>
          <button
            type="button"
            onClick={() => setForm({ ...form, dungSai: false })}
            className={`px-5 py-2 rounded-lg text-sm font-medium border-2 transition-colors ${
              !form.dungSai
                ? 'bg-red-500 border-red-500 text-white'
                : 'border-gray-300 text-gray-600 hover:border-red-400'
            }`}
          >✗ Sai</button>
        </div>
      </div>
    );
  }

  // TU_LUAN
  if (form.loai === 'TU_LUAN') {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Gợi ý đáp án <span className="text-gray-400 font-normal">(tham khảo khi chấm tay)</span>
        </label>
        <textarea
          rows={3}
          value={form.goiY}
          onChange={(e) => setForm({ ...form, goiY: e.target.value })}
          placeholder="Nhập gợi ý đáp án để hỗ trợ giảng viên chấm bài..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <p className="text-xs text-gray-400 mt-1">
          Câu tự luận không chấm tự động. Giảng viên sẽ chấm và nhập điểm thủ công.
        </p>
      </div>
    );
  }

  return null;
}

// =============================================================================
// SUB: Modal tạo / sửa câu hỏi
// =============================================================================

interface CauHoiModalProps {
  mode:     'tao' | 'sua';
  init?:    ICauHoi | null;
  khoaHocs: IKhoaHoc[];
  onClose:  () => void;
  onSuccess: () => void;
}

function CauHoiModal({ mode, init, khoaHocs, onClose, onSuccess }: CauHoiModalProps) {
  const [form, setForm] = useState<FormState>(() => {
    if (init) {
      const parsed = parseDapAn(init.loai, init.dap_an);
      return {
        ...DEFAULT_FORM,
        noi_dung:    init.noi_dung,
        loai:        init.loai,
        do_kho:      init.do_kho,
        diem:        String(init.diem),
        khoa_hoc_id: init.khoa_hoc_id ?? '',
        bai_kiem_tra_id: init.bai_kiem_tra_id ?? '',
        giai_thich:  init.giai_thich ?? '',
        ...parsed,
      };
    }
    return DEFAULT_FORM;
  });
  const [submitting, setSubmitting] = useState(false);
  const [errMsg, setErrMsg]         = useState('');
  const [baiKiemTras, setBaiKiemTras] = useState<IBaiKiemTra[]>([]);
  const [loadingBkt, setLoadingBkt] = useState(false);

  // Khi đổi loại câu hỏi → reset phần đáp án về mặc định
  const handleLoaiChange = (loai: string) => {
    setForm({
      ...form,
      loai,
      options:         ['', ''],
      correctSingle:   0,
      correctMultiple: [],
      dungSai:         true,
      goiY:            '',
    });
  };

  // Load bai_kiem_tra when khoa_hoc_id changes
  useEffect(() => {
    if (!form.khoa_hoc_id) {
      setBaiKiemTras([]);
      setForm(prev => ({ ...prev, bai_kiem_tra_id: '' }));
      return;
    }
    const loadBkt = async () => {
      setLoadingBkt(true);
      try {
        const res = await baiKiemTraApi.danhSach(form.khoa_hoc_id);
        setBaiKiemTras(res.data.data || []);
      } catch {
        setBaiKiemTras([]);
      } finally {
        setLoadingBkt(false);
      }
    };
    loadBkt();
  }, [form.khoa_hoc_id]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const handleSubmit = async () => {
    if (!form.noi_dung.trim()) { setErrMsg('Nội dung câu hỏi là bắt buộc'); return; }
    if (!form.khoa_hoc_id) { setErrMsg('Vui lòng chọn khóa học'); return; }
    if (!form.bai_kiem_tra_id) { setErrMsg('Vui lòng chọn bài kiểm tra'); return; }
    // Validate lựa chọn trắc nghiệm
    if ((form.loai === 'TRAC_NGHIEM_1' || form.loai === 'TRAC_NGHIEM_NHIEU')
        && form.options.some((o) => !o.trim())) {
      setErrMsg('Vui lòng điền đầy đủ nội dung các lựa chọn');
      return;
    }
    if (form.loai === 'TRAC_NGHIEM_NHIEU' && form.correctMultiple.length === 0) {
      setErrMsg('Vui lòng chọn ít nhất 1 đáp án đúng');
      return;
    }
    setSubmitting(true);
    setErrMsg('');
    try {
      const payload: ICauHoiCreate = {
        noi_dung:    form.noi_dung.trim(),
        loai:        form.loai,
        do_kho:      form.do_kho,
        diem:        Number(form.diem) || 1,
        dap_an:      buildDapAn(form),
        khoa_hoc_id: form.khoa_hoc_id || null,
        bai_kiem_tra_id: form.bai_kiem_tra_id,
        ...(form.giai_thich.trim() && { giai_thich: form.giai_thich.trim() }),
      };
      if (mode === 'tao') {
        await cauHoiApi.taoMoi(payload);
      } else {
        await cauHoiApi.capNhat(init!.id, payload);
      }
      onSuccess();
    } catch (err: any) {
      setErrMsg(err?.response?.data?.detail?.error?.message || 'Lỗi lưu câu hỏi. Thử lại sau.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-2xl mx-4 max-h-[92vh] overflow-y-auto p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-5">
          {mode === 'tao' ? '➕ Tạo câu hỏi mới' : '✏️ Sửa câu hỏi'}
        </h3>

        <div className="space-y-4">
          {/* Nội dung câu hỏi */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nội dung câu hỏi <span className="text-red-500">*</span>
            </label>
            <textarea
              autoFocus rows={3}
              value={form.noi_dung}
              onChange={(e) => setForm({ ...form, noi_dung: e.target.value })}
              placeholder="Nhập nội dung câu hỏi..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Loại + Độ khó + Điểm */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Loại câu hỏi</label>
              <select
                value={form.loai}
                onChange={(e) => handleLoaiChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {LOAI_CAU_HOI.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Độ khó</label>
              <select
                value={form.do_kho}
                onChange={(e) => setForm({ ...form, do_kho: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {DO_KHO.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Điểm</label>
              <input
                type="number" min={0.5} step={0.5}
                value={form.diem}
                onChange={(e) => setForm({ ...form, diem: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Khóa học */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Thuộc khóa học <span className="text-red-500">*</span>
            </label>
            <select
              value={form.khoa_hoc_id}
              onChange={(e) => setForm({ ...form, khoa_hoc_id: e.target.value, bai_kiem_tra_id: '' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">— Chọn khóa học —</option>
              {khoaHocs.map((kh) => (
                <option key={kh.id} value={kh.id}>[{kh.ma_khoa_hoc}] {kh.ten_khoa_hoc}</option>
              ))}
            </select>
          </div>

          {/* Bài kiểm tra */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Thuộc bài kiểm tra <span className="text-red-500">*</span>
            </label>
            <select
              value={form.bai_kiem_tra_id}
              onChange={(e) => setForm({ ...form, bai_kiem_tra_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={!form.khoa_hoc_id || loadingBkt}
            >
              <option value="">— Chọn bài kiểm tra —</option>
              {baiKiemTras.map((bkt) => (
                <option key={bkt.id} value={bkt.id}>{bkt.tieu_de}</option>
              ))}
            </select>
            {!form.khoa_hoc_id && <p className="text-xs text-gray-400 mt-1">Chọn khóa học trước</p>}
            {loadingBkt && <p className="text-xs text-gray-400 mt-1">Đang tải danh sách bài kiểm tra...</p>}
          </div>

          {/* Phần đáp án động */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <DapAnForm form={form} setForm={setForm} />
          </div>

          {/* Giải thích */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Giải thích đáp án <span className="text-gray-400 font-normal">(hiển thị sau khi nộp bài)</span>
            </label>
            <textarea
              rows={2}
              value={form.giai_thich}
              onChange={(e) => setForm({ ...form, giai_thich: e.target.value })}
              placeholder="Giải thích tại sao đáp án này đúng..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
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
          >Hủy</button>
          <button
            onClick={handleSubmit}
            disabled={submitting || !form.noi_dung.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? 'Đang lưu...' : mode === 'tao' ? 'Tạo câu hỏi' : 'Lưu thay đổi'}
          </button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN: CauHoiManager
// =============================================================================

export default function CauHoiManager() {
  const [list, setList]           = useState<ICauHoi[]>([]);
  const [khoaHocs, setKhoaHocs]   = useState<IKhoaHoc[]>([]);
  const [baiKiemTras, setBaiKiemTras] = useState<IBaiKiemTra[]>([]);
  const [pagination, setPagination] = useState<IPagination | null>(null);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState<string | null>(null);
  const [page, setPage]           = useState(1);

  // Filters
  const [filterLoai, setFilterLoai]   = useState('');
  const [filterDoKho, setFilterDoKho] = useState('');
  const [filterKhoaHocId, setFilterKhoaHocId] = useState('');
  const [filterBaiKiemTraId, setFilterBaiKiemTraId] = useState('');

  // Modals
  const [showCreate, setShowCreate]   = useState(false);
  const [showImport, setShowImport]   = useState(false);
  const [editItem, setEditItem]       = useState<ICauHoi | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ICauHoi | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Load bai_kiem_tra when filterKhoaHocId changes
  useEffect(() => {
    if (!filterKhoaHocId) {
      setBaiKiemTras([]);
      setFilterBaiKiemTraId('');
      return;
    }
    const loadBkt = async () => {
      try {
        const res = await baiKiemTraApi.danhSach(filterKhoaHocId);
        setBaiKiemTras(res.data.data || []);
      } catch {
        setBaiKiemTras([]);
      }
    };
    loadBkt();
  }, [filterKhoaHocId]);

  // Load danh sách câu hỏi
  const loadList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, unknown> = { page, page_size: 15 };
      if (filterLoai)      params.loai          = filterLoai;
      if (filterDoKho)     params.do_kho        = filterDoKho;
      if (filterKhoaHocId) params.khoa_hoc_id   = filterKhoaHocId;
      if (filterBaiKiemTraId) params.bai_kiem_tra_id = filterBaiKiemTraId;

      const [chRes, khRes] = await Promise.all([
        cauHoiApi.danhSach(params as any),
        khoaHocs.length === 0 ? khoaHocApi.quanLy({ page_size: 100 }) : null,
      ]);
      setList(chRes.data.data || []);
      setPagination(chRes.data.pagination || null);
      if (khRes) setKhoaHocs(khRes.data.data || []);
    } catch (err: any) {
      const status = err?.response?.status;
      if (status === 403) {
        setError('Bạn không có quyền truy cập ngân hàng câu hỏi. Cần vai trò GIANG_VIEN hoặc QT_DAO_TAO.');
      } else {
        setError('Không thể tải câu hỏi. Kiểm tra LMS backend (port 8001).');
      }
    } finally {
      setLoading(false);
    }
  }, [page, filterLoai, filterDoKho, filterKhoaHocId, filterBaiKiemTraId]);

  useEffect(() => { loadList(); }, [loadList]);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      await cauHoiApi.xoa(deleteTarget.id);
      setDeleteTarget(null);
      loadList();
    } catch (err: any) {
      alert(err?.response?.data?.detail?.error?.message || 'Không thể xóa câu hỏi.');
    } finally {
      setDeleteLoading(false);
    }
  };

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <span className="text-3xl block mb-2">🔒</span>
        <p className="text-red-700 text-sm font-medium">{error}</p>
      </div>
    );
  }

  const doKhoMap = Object.fromEntries(DO_KHO.map((d) => [d.value, d]));

  return (
    <>
      {/* Toolbar filter */}
      <div className="flex flex-wrap gap-3 mb-4">
        <select
          value={filterLoai}
          onChange={(e) => { setFilterLoai(e.target.value); setPage(1); }}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
        >
          <option value="">Tất cả loại</option>
          {LOAI_CAU_HOI.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>

        <select
          value={filterDoKho}
          onChange={(e) => { setFilterDoKho(e.target.value); setPage(1); }}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
        >
          <option value="">Tất cả độ khó</option>
          {DO_KHO.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>

        <select
          value={filterKhoaHocId}
          onChange={(e) => { setFilterKhoaHocId(e.target.value); setFilterBaiKiemTraId(''); setPage(1); }}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
        >
          <option value="">Tất cả khóa học</option>
          {khoaHocs.map((kh) => (
            <option key={kh.id} value={kh.id}>[{kh.ma_khoa_hoc}] {kh.ten_khoa_hoc}</option>
          ))}
        </select>

        <select
          value={filterBaiKiemTraId}
          onChange={(e) => { setFilterBaiKiemTraId(e.target.value); setPage(1); }}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
          disabled={!filterKhoaHocId}
        >
          <option value="">Tất cả bài kiểm tra</option>
          {baiKiemTras.map((bkt) => (
            <option key={bkt.id} value={bkt.id}>{bkt.tieu_de}</option>
          ))}
        </select>

        <div className="flex-1" />
        {/* Nút Import từ file Excel/CSV */}
        <button
          onClick={() => setShowImport(true)}
          className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 flex items-center gap-1.5"
        >
          <span>📥</span> Import từ file
        </button>
        {/* Nút Tạo câu hỏi đơn lẻ */}
        <button
          onClick={() => { setEditItem(null); setShowCreate(true); }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 flex items-center gap-1.5"
        >
          <span>➕</span> Tạo câu hỏi
        </button>
      </div>

      {/* Danh sách */}
      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4].map((i) => <div key={i} className="h-12 bg-gray-100 rounded-lg animate-pulse" />)}
        </div>
      ) : list.length === 0 ? (
        <div className="text-center py-14 bg-white rounded-xl border border-gray-200 text-gray-500">
          <span className="text-5xl block mb-3">❓</span>
          <p className="font-medium">Chưa có câu hỏi nào</p>
          <p className="text-sm mt-1">Nhấn "Tạo câu hỏi" để bắt đầu xây dựng ngân hàng</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Câu hỏi</th>
                <th className="px-4 py-3 text-center font-medium text-gray-500 w-24">Loại</th>
                <th className="px-4 py-3 text-center font-medium text-gray-500 w-28">Độ khó</th>
                <th className="px-4 py-3 text-center font-medium text-gray-500 w-16">Điểm</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Khóa học</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Bài KT</th>
                <th className="px-4 py-3 text-right font-medium text-gray-500 w-24">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {list.map((cq) => {
                const dk = doKhoMap[cq.do_kho];
                return (
                  <tr key={cq.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <p className="text-sm text-gray-900 line-clamp-2">{cq.noi_dung}</p>
                      {cq.giai_thich && (
                        <p className="text-xs text-gray-400 mt-0.5 truncate">💡 {cq.giai_thich}</p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-mono font-medium">
                        {LOAI_LABEL[cq.loai] ?? cq.loai}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {dk && (
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${dk.color}`}>
                          {dk.label}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center font-semibold text-gray-700">{cq.diem}</td>
                    <td className="px-4 py-3 text-sm text-gray-500 max-w-xs">
                      <p className="truncate">{cq.khoa_hoc_ten ?? <span className="text-gray-300">—</span>}</p>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 max-w-xs">
                      {cq.bai_kiem_tra_ten ? (
                        <p className="truncate text-purple-600 text-xs">{cq.bai_kiem_tra_ten}</p>
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-1">
                        <button
                          onClick={() => setEditItem(cq)}
                          className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs hover:bg-yellow-200"
                        >Sửa</button>
                        <button
                          onClick={() => setDeleteTarget(cq)}
                          className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs hover:bg-red-200"
                        >Xóa</button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Phân trang */}
      {pagination && pagination.total_pages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-4">
          <button
            onClick={() => setPage(Math.max(1, page - 1))} disabled={page <= 1}
            className="px-3 py-1 border rounded text-sm disabled:opacity-50"
          >Trước</button>
          <span className="text-sm text-gray-500">{page} / {pagination.total_pages}</span>
          <button
            onClick={() => setPage(Math.min(pagination.total_pages, page + 1))}
            disabled={page >= pagination.total_pages}
            className="px-3 py-1 border rounded text-sm disabled:opacity-50"
          >Sau</button>
        </div>
      )}

      {/* Dialog import câu hỏi hàng loạt từ Excel/CSV */}
      <ImportCauHoiDialog
        open={showImport}
        onOpenChange={(open) => { if (!open) setShowImport(false); }}
        onImportSuccess={() => { setShowImport(false); loadList(); }}
      />

      {/* Modal tạo */}
      {showCreate && (
        <CauHoiModal
          mode="tao" khoaHocs={khoaHocs}
          onClose={() => setShowCreate(false)}
          onSuccess={() => { setShowCreate(false); loadList(); }}
        />
      )}

      {/* Modal sửa */}
      {editItem && (
        <CauHoiModal
          mode="sua" init={editItem} khoaHocs={khoaHocs}
          onClose={() => setEditItem(null)}
          onSuccess={() => { setEditItem(null); loadList(); }}
        />
      )}

      {/* Dialog xác nhận xóa */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setDeleteTarget(null)} />
          <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-sm mx-4 p-6">
            <h3 className="text-lg font-semibold mb-2">Xóa câu hỏi</h3>
            <p className="text-sm text-gray-600 mb-1">Câu hỏi:</p>
            <p className="text-sm font-medium text-gray-900 line-clamp-2 mb-5">
              "{deleteTarget.noi_dung}"
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteTarget(null)} disabled={deleteLoading}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
              >Hủy</button>
              <button
                onClick={handleDelete} disabled={deleteLoading}
                className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50"
              >
                {deleteLoading ? 'Đang xóa...' : 'Xóa'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
