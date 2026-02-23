/**
 * src/components/lms/BaiKiemTraManager.tsx
 * ==========================================
 * Quản lý Bài kiểm tra trong một Khóa học.
 * Tích hợp tạo câu hỏi NGAY TRONG BKT editor (inline).
 * Có thể chọn thêm từ Ngân hàng đề (dialog).
 *
 * Props: khoaHocId (string)
 * Quyền: GIANG_VIEN (khóa của mình), QT_DAO_TAO, ADMIN.
 */

'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { baiKiemTraApi, cauHoiApi } from '@/services/lms';
import type { IBaiKiemTra, IBaiKiemTraCreate, ICauHoi, ICauHoiInline } from '@/types/lms';
import ImportCauHoiDialog from '@/components/lms/ImportCauHoiDialog';

// =============================================================================
// CONSTANTS
// =============================================================================

const LOAI_LABEL: Record<string, string> = {
  TRAC_NGHIEM_1:     'TN 1 đáp án',
  TRAC_NGHIEM_NHIEU: 'TN nhiều đáp án',
  DUNG_SAI:          'Đúng / Sai',
  GHEP_DOI:          'Ghép đôi',
  TU_LUAN:           'Tự luận',
};

const DO_KHO_LABEL: Record<string, string> = { DE: 'Dễ', TRUNG_BINH: 'TB', KHO: 'Khó' };
const DO_KHO_COLOR: Record<string, string> = {
  DE: 'text-green-600', TRUNG_BINH: 'text-yellow-600', KHO: 'text-red-600',
};

const LOAI_OPTIONS = [
  { value: 'TRAC_NGHIEM_1',    label: 'Trắc nghiệm 1 đáp án' },
  { value: 'TRAC_NGHIEM_NHIEU', label: 'Trắc nghiệm nhiều đáp án' },
  { value: 'DUNG_SAI',         label: 'Đúng / Sai' },
  { value: 'TU_LUAN',          label: 'Tự luận' },
];
const DO_KHO_OPTIONS = [
  { value: 'DE', label: 'Dễ' },
  { value: 'TRUNG_BINH', label: 'Trung bình' },
  { value: 'KHO', label: 'Khó' },
];

// =============================================================================
// TYPES
// =============================================================================

/** Một dòng câu hỏi trong danh sách của BKT Editor */
type CauHoiItem =
  | { source: 'bank';   data: ICauHoi }     // từ ngân hàng (ID có sẵn)
  | { source: 'inline'; data: ICauHoiInline; tempId: string }; // tạo mới inline

interface BktFormBase {
  tieu_de:               string;
  thoi_gian_lam_bai_phut: string;
  so_lan_lam_toi_da:     string;
  diem_dat:              string;
  tron_de:               boolean;
  che_do_xem_ket_qua:   string;
  hien_giai_thich:       boolean;
}

const BKT_BASE_DEFAULT: BktFormBase = {
  tieu_de:               '',
  thoi_gian_lam_bai_phut: '',
  so_lan_lam_toi_da:     '3',
  diem_dat:              '70',
  tron_de:               true,
  che_do_xem_ket_qua:   'XEM_DIEM_VA_DAP_AN',
  hien_giai_thich:       true,
};

// Inline câu hỏi form state
interface InlineForm {
  noi_dung:      string;
  loai:          string;
  do_kho:        string;
  diem:          string;
  giai_thich:    string;
  // TRAC_NGHIEM_1 / TRAC_NGHIEM_NHIEU
  options:       string[];
  correctSingle: number;
  correctMulti:  number[];
  // DUNG_SAI
  dungSai:       boolean;
  // TU_LUAN
  goiY:          string;
}

const INLINE_DEFAULT: InlineForm = {
  noi_dung:      '',
  loai:          'TRAC_NGHIEM_1',
  do_kho:        'TRUNG_BINH',
  diem:          '1',
  giai_thich:    '',
  options:       ['', '', '', ''],
  correctSingle: 0,
  correctMulti:  [],
  dungSai:       true,
  goiY:          '',
};

// =============================================================================
// HELPER: build đáp án từ inline form
// =============================================================================

function buildDapAn(form: InlineForm): Record<string, unknown> {
  switch (form.loai) {
    case 'TRAC_NGHIEM_1':
      return { options: form.options, correct: form.correctSingle };
    case 'TRAC_NGHIEM_NHIEU':
      return { options: form.options, correct: form.correctMulti };
    case 'DUNG_SAI':
      return { correct: form.dungSai };
    case 'TU_LUAN':
      return form.goiY.trim() ? { goi_y: form.goiY.trim() } : {};
    default:
      return {};
  }
}

// =============================================================================
// SUB: Form đáp án động (inline)
// =============================================================================

function DapAnFormInline({ form, setForm }: { form: InlineForm; setForm: (f: InlineForm) => void }) {
  if (form.loai === 'TRAC_NGHIEM_1' || form.loai === 'TRAC_NGHIEM_NHIEU') {
    const isMulti = form.loai === 'TRAC_NGHIEM_NHIEU';
    return (
      <div className="space-y-1.5">
        {form.options.map((opt, i) => (
          <div key={i} className="flex items-center gap-2">
            {isMulti ? (
              <input type="checkbox"
                checked={form.correctMulti.includes(i)}
                onChange={() => {
                  const cm = form.correctMulti.includes(i)
                    ? form.correctMulti.filter((c) => c !== i)
                    : [...form.correctMulti, i];
                  setForm({ ...form, correctMulti: cm });
                }}
                className="w-4 h-4 accent-blue-600 shrink-0"
              />
            ) : (
              <input type="radio" name={`cs_${i}`}
                checked={form.correctSingle === i}
                onChange={() => setForm({ ...form, correctSingle: i })}
                className="w-4 h-4 accent-blue-600 shrink-0"
              />
            )}
            <input type="text"
              value={opt}
              onChange={(e) => {
                const opts = [...form.options];
                opts[i] = e.target.value;
                setForm({ ...form, options: opts });
              }}
              placeholder={`Lựa chọn ${String.fromCharCode(65 + i)}`}
              className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
            />
            {form.options.length > 2 && (
              <button type="button"
                onClick={() => {
                  const opts = form.options.filter((_, idx) => idx !== i);
                  const cs = form.correctSingle >= opts.length ? 0 : form.correctSingle;
                  const cm = form.correctMulti.filter((c) => c < opts.length);
                  setForm({ ...form, options: opts, correctSingle: cs, correctMulti: cm });
                }}
                className="text-red-400 hover:text-red-600 text-lg leading-none"
              >×</button>
            )}
          </div>
        ))}
        {form.options.length < 6 && (
          <button type="button"
            onClick={() => setForm({ ...form, options: [...form.options, ''] })}
            className="text-xs text-blue-600 hover:underline mt-1"
          >+ Thêm lựa chọn</button>
        )}
        <p className="text-xs text-gray-400">
          {isMulti ? 'Tích checkbox để chọn đáp án đúng (nhiều)' : 'Click radio để chọn 1 đáp án đúng'}
        </p>
      </div>
    );
  }
  if (form.loai === 'DUNG_SAI') {
    return (
      <div className="flex gap-3">
        {[true, false].map((v) => (
          <button key={String(v)} type="button"
            onClick={() => setForm({ ...form, dungSai: v })}
            className={`px-4 py-1.5 rounded text-sm font-medium border-2 transition-colors ${
              form.dungSai === v
                ? v ? 'bg-green-500 border-green-500 text-white' : 'bg-red-500 border-red-500 text-white'
                : 'border-gray-300 text-gray-600 hover:border-gray-400'
            }`}
          >{v ? '✓ Đúng' : '✗ Sai'}</button>
        ))}
      </div>
    );
  }
  if (form.loai === 'TU_LUAN') {
    return (
      <textarea rows={2} value={form.goiY}
        onChange={(e) => setForm({ ...form, goiY: e.target.value })}
        placeholder="Gợi ý đáp án (để hỗ trợ chấm tay)..."
        className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-400"
      />
    );
  }
  return null;
}

// =============================================================================
// SUB: Form tạo câu hỏi inline
// =============================================================================

interface InlineFormPanelProps {
  onAdd:    (ch: ICauHoiInline) => void;
  onCancel: () => void;
}

function InlineFormPanel({ onAdd, onCancel }: InlineFormPanelProps) {
  const [form, setForm] = useState<InlineForm>({ ...INLINE_DEFAULT });
  const [errMsg, setErrMsg] = useState('');

  const handleAdd = () => {
    if (!form.noi_dung.trim()) { setErrMsg('Nội dung câu hỏi là bắt buộc'); return; }
    if ((form.loai === 'TRAC_NGHIEM_1' || form.loai === 'TRAC_NGHIEM_NHIEU')
        && form.options.some((o) => !o.trim())) {
      setErrMsg('Vui lòng điền đầy đủ nội dung các lựa chọn'); return;
    }
    if (form.loai === 'TRAC_NGHIEM_NHIEU' && form.correctMulti.length === 0) {
      setErrMsg('Vui lòng chọn ít nhất 1 đáp án đúng'); return;
    }
    const inline: ICauHoiInline = {
      noi_dung:   form.noi_dung.trim(),
      loai:       form.loai,
      do_kho:     form.do_kho,
      diem:       Number(form.diem) || 1,
      dap_an:     buildDapAn(form),
      ...(form.giai_thich.trim() && { giai_thich: form.giai_thich.trim() }),
    };
    onAdd(inline);
  };

  return (
    <div className="border border-blue-200 rounded-lg bg-blue-50 p-4 space-y-3">
      <p className="text-xs font-semibold text-blue-700 uppercase tracking-wide">Thêm câu hỏi mới</p>

      {/* Nội dung */}
      <div>
        <textarea rows={2} autoFocus
          value={form.noi_dung}
          onChange={(e) => setForm({ ...form, noi_dung: e.target.value })}
          placeholder="Nội dung câu hỏi..."
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white"
        />
      </div>

      {/* Loại + Độ khó + Điểm */}
      <div className="grid grid-cols-3 gap-2">
        <select value={form.loai}
          onChange={(e) => setForm({ ...INLINE_DEFAULT, noi_dung: form.noi_dung, loai: e.target.value, giai_thich: form.giai_thich })}
          className="px-2 py-1.5 border border-gray-300 rounded text-sm bg-white focus:outline-none focus:ring-1 focus:ring-blue-400"
        >
          {LOAI_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <select value={form.do_kho}
          onChange={(e) => setForm({ ...form, do_kho: e.target.value })}
          className="px-2 py-1.5 border border-gray-300 rounded text-sm bg-white focus:outline-none focus:ring-1 focus:ring-blue-400"
        >
          {DO_KHO_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <div className="flex items-center gap-1">
          <input type="number" min={0.5} step={0.5}
            value={form.diem}
            onChange={(e) => setForm({ ...form, diem: e.target.value })}
            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
            placeholder="Điểm"
          />
        </div>
      </div>

      {/* Đáp án */}
      <div className="bg-white rounded border border-gray-200 p-3">
        <DapAnFormInline form={form} setForm={setForm} />
      </div>

      {/* Giải thích (optional) */}
      <input type="text"
        value={form.giai_thich}
        onChange={(e) => setForm({ ...form, giai_thich: e.target.value })}
        placeholder="Giải thích đáp án (tùy chọn)"
        className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm bg-white focus:outline-none focus:ring-1 focus:ring-blue-400"
      />

      {errMsg && <p className="text-xs text-red-600">{errMsg}</p>}

      {/* Actions */}
      <div className="flex gap-2 justify-end">
        <button onClick={onCancel}
          className="px-3 py-1.5 border border-gray-300 rounded text-xs hover:bg-gray-50"
        >Hủy</button>
        <button onClick={handleAdd}
          className="px-3 py-1.5 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700"
        >Thêm câu hỏi</button>
      </div>
    </div>
  );
}

// =============================================================================
// SUB: Dialog chọn từ Ngân hàng đề
// =============================================================================

interface BankDialogProps {
  khoaHocId:        string;
  excludeIds:       Set<string>;  // đã chọn, ẩn đi
  onSelect:         (ch: ICauHoi) => void;
  onClose:          () => void;
}

function BankDialog({ khoaHocId, excludeIds, onSelect, onClose }: BankDialogProps) {
  const [list, setList]             = useState<ICauHoi[]>([]);
  const [loading, setLoading]       = useState(true);
  const [filterLoai, setFilterLoai] = useState('');
  const [filterDoKho, setFilterDoKho] = useState('');
  const [filterKhoa, setFilterKhoa] = useState('');  // '' | 'khoa_nay' | 'cau_chung'

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        // Fetch TẤT CẢ câu hỏi (không filter khoa_hoc_id) — page_size max 100 theo backend
        const res = await cauHoiApi.danhSach({ page_size: 100 });
        setList(res.data.data || []);
      } catch { /* bỏ qua */ }
      finally { setLoading(false); }
    };
    load();
  }, []);  // chỉ load 1 lần khi mở dialog

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const filtered = list.filter((ch) => {
    if (excludeIds.has(ch.id)) return false;
    if (filterLoai && ch.loai !== filterLoai) return false;
    if (filterDoKho && ch.do_kho !== filterDoKho) return false;
    if (filterKhoa === 'khoa_nay' && ch.khoa_hoc_id !== khoaHocId) return false;
    if (filterKhoa === 'cau_chung' && ch.khoa_hoc_id !== null) return false;
    return true;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 max-h-[85vh] flex flex-col">
        <div className="px-5 py-4 border-b shrink-0">
          <h3 className="text-base font-semibold text-gray-900">Chọn từ Ngân hàng đề</h3>
          <div className="grid grid-cols-3 gap-2 mt-2">
            {/* Filter theo nguồn câu hỏi */}
            <select value={filterKhoa} onChange={(e) => setFilterKhoa(e.target.value)}
              className="px-2 py-1.5 border border-gray-300 rounded text-xs bg-white"
            >
              <option value="">Tất cả nguồn</option>
              <option value="khoa_nay">Khóa này</option>
              <option value="cau_chung">Câu chung</option>
            </select>
            <select value={filterLoai} onChange={(e) => setFilterLoai(e.target.value)}
              className="px-2 py-1.5 border border-gray-300 rounded text-xs bg-white"
            >
              <option value="">Tất cả loại</option>
              {Object.entries(LOAI_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
            <select value={filterDoKho} onChange={(e) => setFilterDoKho(e.target.value)}
              className="px-2 py-1.5 border border-gray-300 rounded text-xs bg-white"
            >
              <option value="">Tất cả độ khó</option>
              {Object.entries(DO_KHO_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          {!loading && (
            <p className="text-xs text-gray-400 mt-1.5">
              Hiển thị {filtered.length}/{list.length} câu hỏi khả dụng
            </p>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {loading ? (
            <p className="text-center py-8 text-sm text-gray-400">Đang tải...</p>
          ) : filtered.length === 0 ? (
            <p className="text-center py-8 text-sm text-gray-400">
              {list.length === 0 ? 'Ngân hàng câu hỏi trống' : 'Không có câu hỏi phù hợp với bộ lọc'}
            </p>
          ) : (
            <div className="space-y-1">
              {filtered.map((ch) => (
                <button key={ch.id}
                  onClick={() => { onSelect(ch); }}
                  className="w-full text-left flex items-start gap-3 p-3 rounded-lg border border-gray-200 hover:bg-blue-50 hover:border-blue-300 transition-colors"
                >
                  <span className="text-lg shrink-0 mt-0.5">📄</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 line-clamp-2">{ch.noi_dung}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {LOAI_LABEL[ch.loai] ?? ch.loai}
                      <span className="mx-1">·</span>
                      <span className={DO_KHO_COLOR[ch.do_kho] ?? ''}>{DO_KHO_LABEL[ch.do_kho] ?? ch.do_kho}</span>
                      <span className="mx-1">·</span>
                      <span className="font-medium text-blue-600">{ch.diem} điểm</span>
                      {ch.khoa_hoc_ten && (
                        <>
                          <span className="mx-1">·</span>
                          <span className="text-gray-400 truncate">{ch.khoa_hoc_ten}</span>
                        </>
                      )}
                      {!ch.khoa_hoc_id && (
                        <>
                          <span className="mx-1">·</span>
                          <span className="text-purple-500">Câu chung</span>
                        </>
                      )}
                    </p>
                  </div>
                  <span className="text-xs text-blue-500 font-medium shrink-0 mt-1">Thêm</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="px-5 py-3 border-t shrink-0 text-right">
          <button onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
          >Đóng</button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// SUB: BaiKiemTraEditor — Panel tạo / sửa BKT với danh sách câu hỏi
// =============================================================================

interface BktEditorProps {
  mode:      'tao' | 'sua';
  init?:     IBaiKiemTra | null;
  khoaHocId: string;
  onClose:   () => void;
  onSuccess: () => void;
}

function BktEditor({ mode, init, khoaHocId, onClose, onSuccess }: BktEditorProps) {
  const [base, setBase] = useState<BktFormBase>(() =>
    init
      ? {
          tieu_de:               init.tieu_de,
          thoi_gian_lam_bai_phut: init.thoi_gian_lam_bai_phut ? String(init.thoi_gian_lam_bai_phut) : '',
          so_lan_lam_toi_da:     String(init.so_lan_lam_toi_da ?? 3),
          diem_dat:              String(init.diem_dat ?? 70),
          tron_de:               init.tron_de ?? true,
          che_do_xem_ket_qua:   init.che_do_xem_ket_qua ?? 'XEM_DIEM_VA_DAP_AN',
          hien_giai_thich:       init.hien_giai_thich ?? true,
        }
      : { ...BKT_BASE_DEFAULT }
  );

  // Danh sách câu hỏi trong BKT (đã sắp xếp)
  const [cauHoiList, setCauHoiList] = useState<CauHoiItem[]>([]);
  const [loadingInit, setLoadingInit] = useState(mode === 'sua');

  // UI state
  const [showInlineForm, setShowInlineForm] = useState(false);
  const [showBankDialog, setShowBankDialog] = useState(false);
  const [showImport, setShowImport]         = useState(false);
  const [submitting, setSubmitting]         = useState(false);
  const [errMsg, setErrMsg]                 = useState('');

  // Khi sửa: load câu hỏi hiện tại của BKT
  useEffect(() => {
    if (mode === 'sua' && init) {
      const load = async () => {
        setLoadingInit(true);
        try {
          const res = await baiKiemTraApi.danhSachCauHoi(init.id);
          const items: CauHoiItem[] = (res.data.data || []).map((ch: any) => ({
            source: 'bank' as const,
            data: ch as ICauHoi,
          }));
          setCauHoiList(items);
        } catch { /* bỏ qua */ }
        finally { setLoadingInit(false); }
      };
      load();
    }
  }, [mode, init]);

  const handleAddInline = (ch: ICauHoiInline) => {
    const tempId = `inline_${Date.now()}_${Math.random()}`;
    setCauHoiList((prev) => [...prev, { source: 'inline', data: ch, tempId }]);
    setShowInlineForm(false);
  };

  const handleAddFromBank = (ch: ICauHoi) => {
    setCauHoiList((prev) => [...prev, { source: 'bank', data: ch }]);
    // Đóng dialog sau khi chọn 1 câu
    setShowBankDialog(false);
  };

  const handleRemove = (index: number) => {
    setCauHoiList((prev) => prev.filter((_, i) => i !== index));
  };

  // IDs câu hỏi bank đã chọn (để ẩn trong bank dialog)
  const selectedBankIds = new Set<string>(
    cauHoiList
      .filter((item): item is Extract<CauHoiItem, { source: 'bank' }> => item.source === 'bank')
      .map((item) => item.data.id)
  );

  const tongDiem = cauHoiList.reduce((sum, item) => sum + Number(item.data.diem ?? 0), 0);

  const handleSubmit = async () => {
    if (!base.tieu_de.trim()) { setErrMsg('Tiêu đề bài kiểm tra là bắt buộc'); return; }
    if (cauHoiList.length === 0) { setErrMsg('Phải có ít nhất 1 câu hỏi'); return; }

    setSubmitting(true);
    setErrMsg('');

    try {
      const cau_hoi_ids = cauHoiList
        .filter((item): item is Extract<CauHoiItem, { source: 'bank' }> => item.source === 'bank')
        .map((item) => item.data.id);
      const cau_hoi_moi = cauHoiList
        .filter((item): item is Extract<CauHoiItem, { source: 'inline' }> => item.source === 'inline')
        .map((item) => item.data);

      const payload: IBaiKiemTraCreate = {
        tieu_de:              base.tieu_de.trim(),
        diem_dat:             base.diem_dat ? Number(base.diem_dat) : 70,
        tron_de:              base.tron_de,
        che_do_xem_ket_qua:  base.che_do_xem_ket_qua,
        hien_giai_thich:     base.hien_giai_thich,
        ...(base.thoi_gian_lam_bai_phut && { thoi_gian_lam_bai_phut: Number(base.thoi_gian_lam_bai_phut) }),
        ...(base.so_lan_lam_toi_da      && { so_lan_lam_toi_da:      Number(base.so_lan_lam_toi_da) }),
        ...(cau_hoi_ids.length > 0      && { cau_hoi_ids }),
        ...(cau_hoi_moi.length > 0      && { cau_hoi_moi }),
      };

      if (mode === 'sua' && init) {
        await baiKiemTraApi.capNhat(init.id, payload);
      } else {
        await baiKiemTraApi.taoMoi(khoaHocId, payload);
      }
      onSuccess();
    } catch (err: any) {
      setErrMsg(err?.response?.data?.detail?.error?.message || 'Lỗi lưu bài kiểm tra. Thử lại sau.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-2xl mx-4 max-h-[94vh] flex flex-col">

        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 shrink-0">
          <h3 className="text-lg font-semibold text-gray-900">
            {mode === 'tao' ? '➕ Tạo bài kiểm tra' : '✏️ Sửa bài kiểm tra'}
          </h3>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">

          {/* Tiêu đề */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tiêu đề <span className="text-red-500">*</span>
            </label>
            <input autoFocus type="text"
              value={base.tieu_de}
              onChange={(e) => setBase({ ...base, tieu_de: e.target.value })}
              placeholder="VD: Kiểm tra cuối kỳ Luật Hải quan"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Cấu hình */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Thời gian làm bài (phút)</label>
              <input type="number" min={1}
                value={base.thoi_gian_lam_bai_phut}
                onChange={(e) => setBase({ ...base, thoi_gian_lam_bai_phut: e.target.value })}
                placeholder="Để trống = không giới hạn"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Số lần làm tối đa</label>
              <input type="number" min={1}
                value={base.so_lan_lam_toi_da}
                onChange={(e) => setBase({ ...base, so_lan_lam_toi_da: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Điểm đạt yêu cầu (%)</label>
              <input type="number" min={0} max={100}
                value={base.diem_dat}
                onChange={(e) => setBase({ ...base, diem_dat: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-end pb-2.5">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input type="checkbox"
                  checked={base.tron_de}
                  onChange={(e) => setBase({ ...base, tron_de: e.target.checked })}
                  className="w-4 h-4 accent-blue-600"
                />
                <span className="text-sm text-gray-700">Trộn đề (ngẫu nhiên)</span>
              </label>
            </div>
          </div>

          {/* Cấu hình hiển thị kết quả */}
          <div className="space-y-3 pt-3 border-t border-gray-200">
            <p className="text-sm font-medium text-gray-700">Cấu hình hiển thị kết quả</p>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Chế độ sau khi nộp bài</label>
              <select
                value={base.che_do_xem_ket_qua}
                onChange={(e) => setBase({ ...base, che_do_xem_ket_qua: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="XEM_DIEM_VA_DAP_AN">Xem điểm + đáp án đúng (đầy đủ)</option>
                <option value="CHI_XEM_DIEM">Chỉ xem điểm tổng</option>
                <option value="CHI_XEM_CAU_SAI">Xem điểm + highlight câu sai (không hiện đáp án đúng)</option>
                <option value="XEM_KHI_LAN_CUOI">Xem đáp án khi dùng hết lượt làm bài</option>
                <option value="KHONG_CHO_XEM">Không cho xem (chỉ biết đạt/không đạt)</option>
              </select>
              {base.che_do_xem_ket_qua === 'CHI_XEM_CAU_SAI' && (
                <p className="text-xs text-gray-400 mt-1">Học viên biết câu nào sai nhưng không thấy đáp án đúng</p>
              )}
              {base.che_do_xem_ket_qua === 'KHONG_CHO_XEM' && (
                <p className="text-xs text-gray-400 mt-1">Phù hợp cho thi chính thức</p>
              )}
              {base.che_do_xem_ket_qua === 'XEM_KHI_LAN_CUOI' && (
                <p className="text-xs text-gray-400 mt-1">
                  Đáp án hiển thị sau lần làm cuối ({base.so_lan_lam_toi_da || '∞'} lượt)
                </p>
              )}
            </div>
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input type="checkbox"
                checked={base.hien_giai_thich}
                onChange={(e) => setBase({ ...base, hien_giai_thich: e.target.checked })}
                className="w-4 h-4 accent-blue-600"
              />
              <span className="text-sm text-gray-700">Hiển thị giải thích đáp án</span>
            </label>
          </div>

          {/* Danh sách câu hỏi */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">
                Câu hỏi <span className="text-red-500">*</span>
                {cauHoiList.length > 0 && (
                  <span className="ml-2 text-blue-600 font-semibold">
                    ({cauHoiList.length} câu · Tổng: {tongDiem.toFixed(1)} điểm)
                  </span>
                )}
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => { setShowBankDialog(true); setShowInlineForm(false); }}
                  className="px-2.5 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium hover:bg-purple-200"
                >📚 Chọn từ ngân hàng</button>
                <button
                  onClick={() => { setShowInlineForm(true); setShowBankDialog(false); }}
                  className="px-2.5 py-1 bg-green-100 text-green-700 rounded text-xs font-medium hover:bg-green-200"
                >➕ Thêm câu hỏi mới</button>
                <button
                  onClick={() => { setShowImport(true); setShowInlineForm(false); setShowBankDialog(false); }}
                  className="px-2.5 py-1 bg-orange-100 text-orange-700 rounded text-xs font-medium hover:bg-orange-200"
                >📁 Import từ file</button>
              </div>
            </div>

            {/* Form inline thêm câu hỏi */}
            {showInlineForm && (
              <div className="mb-3">
                <InlineFormPanel
                  onAdd={handleAddInline}
                  onCancel={() => setShowInlineForm(false)}
                />
              </div>
            )}

            {/* Loading khi sửa */}
            {loadingInit ? (
              <div className="h-16 bg-gray-100 rounded-lg animate-pulse" />
            ) : cauHoiList.length === 0 ? (
              <div className="border-2 border-dashed border-gray-200 rounded-lg py-8 text-center text-sm text-gray-400">
                Chưa có câu hỏi nào. Thêm câu hỏi mới hoặc chọn từ ngân hàng.
              </div>
            ) : (
              <div className="border border-gray-200 rounded-lg overflow-hidden max-h-60 overflow-y-auto">
                {cauHoiList.map((item, index) => (
                  <div key={item.source === 'bank' ? item.data.id : (item as any).tempId}
                    className="flex items-start gap-3 px-3 py-2.5 border-b border-gray-100 last:border-b-0 hover:bg-gray-50"
                  >
                    <span className="text-gray-400 text-xs font-mono mt-0.5 shrink-0 w-5 text-right">{index + 1}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 line-clamp-2">{item.data.noi_dung}</p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        <span>{LOAI_LABEL[item.data.loai] ?? item.data.loai}</span>
                        <span className="mx-1">·</span>
                        <span className={DO_KHO_COLOR[item.data.do_kho] ?? ''}>
                          {DO_KHO_LABEL[item.data.do_kho] ?? item.data.do_kho}
                        </span>
                        <span className="mx-1">·</span>
                        <span className="font-medium text-blue-600">{item.data.diem} điểm</span>
                        {item.source === 'inline' && (
                          <span className="ml-1.5 px-1.5 py-0.5 bg-green-100 text-green-700 rounded-full text-xs">mới</span>
                        )}
                      </p>
                    </div>
                    <button onClick={() => handleRemove(index)}
                      className="text-red-400 hover:text-red-600 text-lg leading-none shrink-0 mt-0.5"
                      title="Xóa khỏi bài"
                    >×</button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {errMsg && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              <p className="text-sm text-red-600">{errMsg}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-3 shrink-0">
          <button onClick={onClose} disabled={submitting}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50"
          >Hủy</button>
          <button onClick={handleSubmit}
            disabled={submitting || !base.tieu_de.trim() || cauHoiList.length === 0}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting
              ? 'Đang lưu...'
              : mode === 'tao'
              ? `Tạo (${cauHoiList.length} câu)`
              : 'Lưu thay đổi'}
          </button>
        </div>
      </div>

      {/* Dialog chọn từ ngân hàng */}
      {showBankDialog && (
        <BankDialog
          khoaHocId={khoaHocId}
          excludeIds={selectedBankIds}
          onSelect={handleAddFromBank}
          onClose={() => setShowBankDialog(false)}
        />
      )}

      {/* Dialog import câu hỏi từ file */}
      <ImportCauHoiDialog
        open={showImport}
        onOpenChange={setShowImport}
        khoaHocId={khoaHocId}
        baiKiemTraId={mode === 'sua' && init ? init.id : undefined}
        onImportSuccess={async (result) => {
          setShowImport(false);

          if (mode === 'sua' && init) {
            // Mode SỬA: reload toàn bộ danh sách câu hỏi của BKT từ server
            try {
              const res = await baiKiemTraApi.danhSachCauHoi(init.id);
              const items: CauHoiItem[] = (res.data.data || []).map((ch: any) => ({
                source: 'bank' as const,
                data: ch as ICauHoi,
              }));
              setCauHoiList(items);
            } catch { /* bỏ qua */ }

          } else if (mode === 'tao' && result.cau_hoi_ids?.length) {
            // Mode TẠO: fetch chi tiết câu hỏi theo ID rồi thêm vào local state
            try {
              const res = await cauHoiApi.danhSach({ page_size: 100 });
              const allList: ICauHoi[] = res.data.data || [];
              const importedSet = new Set(result.cau_hoi_ids);

              // Chống trùng: lọc ra câu chưa có trong danh sách hiện tại
              setCauHoiList((prev) => {
                const existingIds = new Set(
                  prev
                    .filter((item): item is Extract<CauHoiItem, { source: 'bank' }> => item.source === 'bank')
                    .map((item) => item.data.id)
                );
                const newItems = allList
                  .filter((ch) => importedSet.has(ch.id) && !existingIds.has(ch.id))
                  .map((ch) => ({ source: 'bank' as const, data: ch }));
                return [...prev, ...newItems];
              });
            } catch { /* bỏ qua */ }
          }
        }}
      />
    </div>
  );
}

// =============================================================================
// MAIN: BaiKiemTraManager
// =============================================================================

export interface BaiKiemTraManagerProps {
  khoaHocId: string;
}

export default function BaiKiemTraManager({ khoaHocId }: BaiKiemTraManagerProps) {
  const [bkts, setBkts]               = useState<IBaiKiemTra[]>([]);
  const [loading, setLoading]         = useState(true);
  const [showEditor, setShowEditor]   = useState(false);
  const [editBkt, setEditBkt]         = useState<IBaiKiemTra | null>(null);
  const [deleteBktId, setDeleteBktId] = useState<string | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const loadBkts = useCallback(async () => {
    setLoading(true);
    try {
      const res = await baiKiemTraApi.danhSach(khoaHocId);
      setBkts(res.data.data || []);
    } catch { /* bỏ qua */ }
    finally { setLoading(false); }
  }, [khoaHocId]);

  useEffect(() => { loadBkts(); }, [loadBkts]);

  const handleDelete = async () => {
    if (!deleteBktId) return;
    setDeleteLoading(true);
    try {
      await baiKiemTraApi.xoa(deleteBktId);
      setDeleteBktId(null);
      loadBkts();
    } catch (err: any) {
      alert(err?.response?.data?.detail?.error?.message || 'Không thể xóa bài kiểm tra.');
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div>
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm text-gray-500">
          {bkts.length === 0 ? 'Chưa có bài kiểm tra nào' : `${bkts.length} bài kiểm tra`}
        </p>
        <button
          onClick={() => { setEditBkt(null); setShowEditor(true); }}
          className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700 flex items-center gap-1.5"
        >
          <span>➕</span> Tạo bài kiểm tra
        </button>
      </div>

      {/* Danh sách */}
      {loading ? (
        <div className="space-y-2">
          {[1, 2].map((i) => <div key={i} className="h-14 bg-gray-100 rounded-lg animate-pulse" />)}
        </div>
      ) : bkts.length === 0 ? (
        <div className="text-center py-10 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200 text-gray-500">
          <span className="text-3xl block mb-2">📝</span>
          <p className="font-medium text-sm">Chưa có bài kiểm tra nào</p>
          <p className="text-xs mt-1">Nhấn "Tạo bài kiểm tra" để thêm đề thi / kiểm tra</p>
        </div>
      ) : (
        <div className="space-y-2">
          {bkts.map((bkt) => (
            <div key={bkt.id}
              className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <span className="text-2xl shrink-0">📝</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">{bkt.tieu_de}</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {bkt.so_cau_hoi} câu
                  {bkt.thoi_gian_lam_bai_phut
                    ? ` · ${bkt.thoi_gian_lam_bai_phut} phút`
                    : ' · Không giới hạn thời gian'}
                  {' · Điểm đạt: '}{bkt.diem_dat}%
                  {!bkt.is_active && (
                    <span className="ml-2 px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded text-xs">Ẩn</span>
                  )}
                </p>
              </div>
              <div className="flex gap-1 shrink-0">
                <button
                  onClick={() => { setEditBkt(bkt); setShowEditor(true); }}
                  className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs hover:bg-yellow-200"
                >Sửa</button>
                <button
                  onClick={() => setDeleteBktId(bkt.id)}
                  className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs hover:bg-red-200"
                >Xóa</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Editor modal */}
      {showEditor && (
        <BktEditor
          mode={editBkt ? 'sua' : 'tao'}
          init={editBkt}
          khoaHocId={khoaHocId}
          onClose={() => { setShowEditor(false); setEditBkt(null); }}
          onSuccess={() => {
            setShowEditor(false);
            setEditBkt(null);
            loadBkts();
          }}
        />
      )}

      {/* Dialog xác nhận xóa */}
      {deleteBktId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setDeleteBktId(null)} />
          <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-sm mx-4 p-6">
            <h3 className="text-lg font-semibold mb-2">Xóa bài kiểm tra</h3>
            <p className="text-sm text-gray-600 mb-5">
              Bạn có chắc muốn xóa bài kiểm tra này? Hành động không thể hoàn tác.
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteBktId(null)} disabled={deleteLoading}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50"
              >Hủy</button>
              <button onClick={handleDelete} disabled={deleteLoading}
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
