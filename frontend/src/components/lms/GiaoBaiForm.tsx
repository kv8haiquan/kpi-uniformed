/**
 * src/components/lms/GiaoBaiForm.tsx
 * =====================================
 * Form giao khóa học bắt buộc — thân thiện, không nhập UUID tay.
 *
 * A. Chọn khóa học: Combobox tìm kiếm từ GET /khoa-hoc/quan-ly?trang_thai=DA_XUAT_BAN
 * B. Chọn đối tượng:
 *    - Mode "Theo đơn vị": checkbox multi-select từ GET /don-vi
 *    - Mode "Theo CBCC cụ thể": autocomplete search từ GET /cbcc/search (debounced 400ms)
 * C. Loại đăng ký + Hạn hoàn thành
 * D. Submit → POST /khoa-hoc/{id}/giao-bai → hiển thị kết quả da_giao / da_co
 */

'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { khoaHocApi, dangKyApi, cbccApi } from '@/services/lms';
import type { IKhoaHoc } from '@/types/lms';

// =============================================================================
// TYPES
// =============================================================================

interface IDonVi {
  id: string;
  ma_don_vi: string;
  ten_don_vi: string;
}

interface ICBCCItem {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string | null;
  don_vi_ten: string | null;
}

type GiaoMode = 'don-vi' | 'ca-nhan';

// =============================================================================
// SUB-COMPONENT: Combobox chọn khóa học
// =============================================================================

interface KhoaHocComboboxProps {
  khoaHocs:      IKhoaHoc[];
  loading:       boolean;
  value:         string;
  onChange:      (id: string) => void;
}

function KhoaHocCombobox({ khoaHocs, loading, value, onChange }: KhoaHocComboboxProps) {
  const [open, setOpen]       = useState(false);
  const [search, setSearch]   = useState('');
  const inputRef              = useRef<HTMLInputElement>(null);

  const selected = khoaHocs.find((kh) => kh.id === value);

  // Lọc theo mã hoặc tên
  const filtered = khoaHocs.filter((kh) =>
    !search ||
    kh.ma_khoa_hoc.toLowerCase().includes(search.toLowerCase()) ||
    kh.ten_khoa_hoc.toLowerCase().includes(search.toLowerCase())
  );

  // Focus vào ô search khi mở
  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 50);
  }, [open]);

  const handleSelect = (kh: IKhoaHoc) => {
    onChange(kh.id);
    setOpen(false);
    setSearch('');
  };

  return (
    <div className="relative">
      {/* Trigger */}
      <button
        type="button"
        onClick={() => !loading && setOpen((v) => !v)}
        className={`w-full flex items-center justify-between px-3 py-2 border rounded-lg text-sm text-left transition-colors ${
          open
            ? 'border-blue-500 ring-2 ring-blue-100'
            : 'border-gray-300 hover:border-gray-400'
        } ${loading ? 'cursor-not-allowed bg-gray-50' : 'bg-white cursor-pointer'}`}
      >
        {loading ? (
          <span className="text-gray-400">Đang tải danh sách khóa học...</span>
        ) : selected ? (
          <span className="flex items-center gap-2 truncate">
            <span className="font-mono text-xs bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded shrink-0">
              {selected.ma_khoa_hoc}
            </span>
            <span className="text-gray-900 truncate">{selected.ten_khoa_hoc}</span>
          </span>
        ) : (
          <span className="text-gray-400">— Chọn khóa học đã xuất bản —</span>
        )}
        <span className="text-gray-400 text-xs ml-2 shrink-0">{open ? '▲' : '▼'}</span>
      </button>

      {/* Overlay đóng dropdown khi click ngoài */}
      {open && (
        <div className="fixed inset-0 z-20" onClick={() => { setOpen(false); setSearch(''); }} />
      )}

      {/* Dropdown */}
      {open && (
        <div className="absolute z-30 top-full mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-xl">
          {/* Ô tìm kiếm */}
          <div className="p-2 border-b border-gray-100">
            <input
              ref={inputRef}
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Tìm theo mã hoặc tên khóa..."
              className="w-full px-2.5 py-1.5 text-sm border border-gray-200 rounded-md focus:outline-none focus:border-blue-400"
            />
          </div>

          {/* Danh sách */}
          <div className="max-h-60 overflow-y-auto py-1">
            {filtered.length === 0 ? (
              <p className="px-3 py-4 text-sm text-gray-400 text-center">
                {khoaHocs.length === 0
                  ? 'Không có khóa học nào đã xuất bản'
                  : 'Không tìm thấy kết quả'}
              </p>
            ) : (
              filtered.map((kh) => (
                <div
                  key={kh.id}
                  onClick={() => handleSelect(kh)}
                  className={`px-3 py-2.5 cursor-pointer flex items-center gap-2.5 hover:bg-blue-50 transition-colors ${
                    kh.id === value ? 'bg-blue-50' : ''
                  }`}
                >
                  <span className="font-mono text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded shrink-0">
                    {kh.ma_khoa_hoc}
                  </span>
                  <span className="text-sm text-gray-900 truncate flex-1">{kh.ten_khoa_hoc}</span>
                  {kh.id === value && (
                    <span className="text-blue-600 text-sm shrink-0">✓</span>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// SUB-COMPONENT: Chọn CBCC bằng autocomplete search
// =============================================================================

interface CBCCPickerProps {
  selected:   ICBCCItem[];
  onAdd:      (cc: ICBCCItem) => void;
  onRemove:   (id: string) => void;
}

function CBCCPicker({ selected, onAdd, onRemove }: CBCCPickerProps) {
  const [query, setQuery]         = useState('');
  const [results, setResults]     = useState<ICBCCItem[]>([]);
  const [loading, setLoading]     = useState(false);
  const [open, setOpen]           = useState(false);
  const debounceRef               = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef                  = useRef<HTMLInputElement>(null);

  // Tìm kiếm CBCC với debounce 400ms
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!query.trim() || query.length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await cbccApi.searchCBCC({ q: query, page_size: 12 });
        setResults(res.data.data || []);
        setOpen(true);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 400);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  const handleAdd = (cc: ICBCCItem) => {
    onAdd(cc);
    setQuery('');
    setOpen(false);
    setResults([]);
    inputRef.current?.focus();
  };

  const showDropdown = open && query.length >= 2;

  return (
    <div>
      {/* Chips CBCC đã chọn */}
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {selected.map((cc) => (
            <span
              key={cc.id}
              className="inline-flex items-center gap-1.5 pl-2.5 pr-1.5 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium border border-green-200"
            >
              <span>👤</span>
              <span>{cc.ho_ten}</span>
              <span className="font-mono text-[10px] text-green-600">({cc.ma_cc})</span>
              <button
                onClick={() => onRemove(cc.id)}
                className="ml-0.5 w-4 h-4 flex items-center justify-center rounded-full hover:bg-green-200 text-green-700 font-bold text-sm leading-none"
                title="Xóa"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Input tìm kiếm */}
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Tìm theo tên hoặc mã công chức (VD: Nguyễn, HQ001)..."
          className={`w-full px-3 py-2 pr-9 border rounded-lg text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            showDropdown ? 'border-blue-400' : 'border-gray-300'
          }`}
        />
        {/* Spinner */}
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Overlay đóng dropdown */}
        {showDropdown && (
          <div className="fixed inset-0 z-20" onClick={() => setOpen(false)} />
        )}

        {/* Dropdown kết quả */}
        {showDropdown && (
          <div className="absolute z-30 top-full mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-xl max-h-56 overflow-y-auto py-1">
            {results.length === 0 && !loading ? (
              <p className="px-3 py-3 text-sm text-gray-400 text-center">
                Không tìm thấy CBCC phù hợp
              </p>
            ) : (
              results.map((cc) => {
                const daChon = selected.some((s) => s.id === cc.id);
                return (
                  <div
                    key={cc.id}
                    onClick={() => !daChon && handleAdd(cc)}
                    className={`px-3 py-2.5 flex items-start gap-3 ${
                      daChon
                        ? 'opacity-50 cursor-not-allowed bg-gray-50'
                        : 'cursor-pointer hover:bg-blue-50'
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">
                        {cc.ho_ten}
                        {daChon && (
                          <span className="ml-1.5 text-xs text-gray-400 font-normal">(đã chọn)</span>
                        )}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        <span className="font-mono">{cc.ma_cc}</span>
                        {cc.chuc_vu && <span> · {cc.chuc_vu}</span>}
                        {cc.don_vi_ten && <span> · {cc.don_vi_ten}</span>}
                      </p>
                    </div>
                    {!daChon && (
                      <span className="text-blue-500 text-xs shrink-0 pt-0.5">+ Thêm</span>
                    )}
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>

      {selected.length === 0 && (
        <p className="text-xs text-gray-400 mt-2">
          Nhập ít nhất 2 ký tự để tìm kiếm · Nhấn vào tên để thêm vào danh sách
        </p>
      )}
    </div>
  );
}

// =============================================================================
// MAIN: GiaoBaiForm
// =============================================================================

export default function GiaoBaiForm() {
  // ── Danh sách khóa học đã xuất bản ──
  const [khoaHocs, setKhoaHocs]           = useState<IKhoaHoc[]>([]);
  const [khoaHocLoading, setKhoaHocLoading] = useState(true);
  const [khoaHocError, setKhoaHocError]   = useState('');
  const [selectedKhoaHocId, setSelectedKhoaHocId] = useState('');

  // ── Danh sách đơn vị ──
  const [donVis, setDonVis]               = useState<IDonVi[]>([]);
  const [donViLoading, setDonViLoading]   = useState(true);

  // ── Mode giao ──
  const [mode, setMode]                   = useState<GiaoMode>('don-vi');

  // ── Đối tượng đã chọn ──
  const [selectedDonViIds, setSelectedDonViIds] = useState<string[]>([]);
  const [selectedCbccs, setSelectedCbccs]       = useState<ICBCCItem[]>([]);

  // ── Cấu hình ──
  const [loaiDangKy, setLoaiDangKy]       = useState('BAT_BUOC');
  const [hanHoanThanh, setHanHoanThanh]   = useState('');

  // ── Submit ──
  const [submitting, setSubmitting]       = useState(false);
  const [result, setResult]               = useState<{
    type: 'success' | 'error';
    text: string;
    da_giao?: number;
    da_co?: number;
  } | null>(null);

  // Load khóa học DA_XUAT_BAN — dùng public endpoint /khoa-hoc để thấy TẤT CẢ
  // khóa đã xuất bản, không bị giới hạn bởi giang_vien_id như /khoa-hoc/quan-ly
  useEffect(() => {
    const load = async () => {
      setKhoaHocLoading(true);
      setKhoaHocError('');
      try {
        const res = await khoaHocApi.danhSach({ trang_thai: 'DA_XUAT_BAN', page_size: 100 });
        setKhoaHocs(res.data.data || []);
      } catch (err: any) {
        const msg =
          err?.response?.data?.detail?.error?.message ||
          `Không thể tải danh sách khóa học (HTTP ${err?.response?.status ?? 'network error'})`;
        setKhoaHocError(msg);
      } finally {
        setKhoaHocLoading(false);
      }
    };
    load();
  }, []);

  // Load danh sách đơn vị
  useEffect(() => {
    const load = async () => {
      setDonViLoading(true);
      try {
        const res = await cbccApi.getDonVi();
        setDonVis(res.data.data || []);
      } catch {
        // Bỏ qua lỗi
      } finally {
        setDonViLoading(false);
      }
    };
    load();
  }, []);

  // Toggle đơn vị
  const toggleDonVi = useCallback((id: string) => {
    setSelectedDonViIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }, []);

  // Thêm CBCC vào danh sách đã chọn
  const handleAddCBCC = useCallback((cc: ICBCCItem) => {
    setSelectedCbccs((prev) =>
      prev.some((c) => c.id === cc.id) ? prev : [...prev, cc]
    );
  }, []);

  // Xóa CBCC khỏi danh sách
  const handleRemoveCBCC = useCallback((id: string) => {
    setSelectedCbccs((prev) => prev.filter((c) => c.id !== id));
  }, []);

  // Kiểm tra có thể submit chưa
  const canSubmit = () => {
    if (!selectedKhoaHocId) return false;
    if (mode === 'don-vi') return selectedDonViIds.length > 0;
    return selectedCbccs.length > 0;
  };

  // Submit giao bài
  const handleSubmit = async () => {
    if (!canSubmit() || submitting) return;
    setSubmitting(true);
    setResult(null);
    try {
      const body: Record<string, unknown> = {
        loai_dang_ky: loaiDangKy,
        ...(hanHoanThanh && { han_hoan_thanh: hanHoanThanh }),
      };

      if (mode === 'don-vi') {
        body.don_vi_ids = selectedDonViIds;
      } else {
        body.cong_chuc_ids = selectedCbccs.map((c) => c.id);
      }

      const res = await dangKyApi.giaoBai(selectedKhoaHocId, body);
      const d = res.data.data;

      setResult({
        type: 'success',
        text: `Giao thành công!`,
        da_giao: d.da_giao,
        da_co: d.da_co,
      });

      // Reset lựa chọn người nhận sau khi giao xong
      setSelectedDonViIds([]);
      setSelectedCbccs([]);
    } catch (err: any) {
      setResult({
        type: 'error',
        text: err?.response?.data?.detail?.error?.message || 'Lỗi giao bài. Thử lại sau.',
      });
    } finally {
      setSubmitting(false);
    }
  };

  // Nhãn nút submit tuỳ mode
  const submitLabel = () => {
    if (submitting) return 'Đang giao...';
    if (mode === 'don-vi') {
      if (selectedDonViIds.length === 0) return 'Giao bài';
      const tenDvs = selectedDonViIds
        .slice(0, 2)
        .map((id) => donVis.find((d) => d.id === id)?.ten_don_vi ?? '...')
        .join(', ');
      return `Giao cho ${selectedDonViIds.length} đơn vị${selectedDonViIds.length > 2 ? '...' : `: ${tenDvs}`}`;
    }
    return selectedCbccs.length > 0
      ? `Giao cho ${selectedCbccs.length} CBCC`
      : 'Giao bài';
  };

  return (
    <div className="max-w-2xl">
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Giao khóa học bắt buộc</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            Giao cho toàn đơn vị hoặc từng CBCC cụ thể
          </p>
        </div>

        {/* ── A. Chọn khóa học ── */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Khóa học <span className="text-red-500">*</span>
          </label>
          <KhoaHocCombobox
            khoaHocs={khoaHocs}
            loading={khoaHocLoading}
            value={selectedKhoaHocId}
            onChange={setSelectedKhoaHocId}
          />
          {khoaHocError && (
            <p className="text-xs text-red-600 mt-1">⛔ {khoaHocError}</p>
          )}
          {!khoaHocLoading && !khoaHocError && khoaHocs.length === 0 && (
            <p className="text-xs text-amber-600 mt-1">
              ⚠ Không có khóa học nào đang mở. Cần xuất bản khóa trước.
            </p>
          )}
        </div>

        {/* ── B. Chọn đối tượng ── */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Đối tượng giao <span className="text-red-500">*</span>
          </label>

          {/* Toggle mode */}
          <div className="flex gap-1 bg-gray-100 rounded-lg p-1 mb-4">
            {([
              ['don-vi',   '🏢 Theo đơn vị'],
              ['ca-nhan',  '👤 Theo CBCC cụ thể'],
            ] as [GiaoMode, string][]).map(([m, label]) => (
              <button
                key={m}
                type="button"
                onClick={() => {
                  setMode(m);
                  setResult(null);
                }}
                className={`flex-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  mode === m
                    ? 'bg-white shadow-sm text-gray-900'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* ── Mode: Theo đơn vị ── */}
          {mode === 'don-vi' && (
            <div>
              {donViLoading ? (
                <div className="grid grid-cols-2 gap-2">
                  {[1, 2, 3, 4, 5, 6].map((i) => (
                    <div key={i} className="h-10 bg-gray-100 rounded-lg animate-pulse" />
                  ))}
                </div>
              ) : donVis.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-6">
                  Không thể tải danh sách đơn vị (kiểm tra LMS backend port 8001)
                </p>
              ) : (
                <>
                  {/* Checkbox lưới đơn vị */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {donVis.map((dv) => {
                      const checked = selectedDonViIds.includes(dv.id);
                      return (
                        <label
                          key={dv.id}
                          className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg border cursor-pointer transition-all select-none ${
                            checked
                              ? 'border-blue-400 bg-blue-50 text-blue-900 shadow-sm'
                              : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-700'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => toggleDonVi(dv.id)}
                            className="w-4 h-4 accent-blue-600 shrink-0"
                          />
                          <span className="text-sm font-medium truncate">{dv.ten_don_vi}</span>
                        </label>
                      );
                    })}
                  </div>

                  {/* Tóm tắt đơn vị đã chọn */}
                  {selectedDonViIds.length > 0 && (
                    <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <p className="text-xs font-medium text-blue-700 mb-1.5">
                        Sẽ giao cho toàn bộ CBCC của {selectedDonViIds.length} đơn vị:
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedDonViIds.map((id) => {
                          const dv = donVis.find((d) => d.id === id);
                          return (
                            <span
                              key={id}
                              className="inline-flex items-center gap-1 pl-2 pr-1 py-0.5 bg-white border border-blue-300 text-blue-800 rounded-full text-xs"
                            >
                              🏢 {dv?.ten_don_vi ?? '...'}
                              <button
                                onClick={() => toggleDonVi(id)}
                                className="w-4 h-4 flex items-center justify-center rounded-full hover:bg-blue-100 text-blue-600 font-bold"
                              >
                                ×
                              </button>
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* ── Mode: Theo CBCC cụ thể ── */}
          {mode === 'ca-nhan' && (
            <CBCCPicker
              selected={selectedCbccs}
              onAdd={handleAddCBCC}
              onRemove={handleRemoveCBCC}
            />
          )}
        </div>

        {/* ── C. Loại đăng ký + Hạn hoàn thành ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Loại đăng ký</label>
            <select
              value={loaiDangKy}
              onChange={(e) => setLoaiDangKy(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="BAT_BUOC">🔴 Bắt buộc</option>
              <option value="GIAO_VIEC">📋 Giao việc</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Hạn hoàn thành
              <span className="text-gray-400 font-normal ml-1">(tuỳ chọn)</span>
            </label>
            <input
              type="date"
              value={hanHoanThanh}
              onChange={(e) => setHanHoanThanh(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* ── D. Kết quả giao bài ── */}
        {result && (
          <div className={`rounded-lg px-4 py-3 border ${
            result.type === 'success'
              ? 'bg-green-50 border-green-200'
              : 'bg-red-50 border-red-200'
          }`}>
            {result.type === 'success' ? (
              <div>
                <p className="text-sm font-semibold text-green-800">✅ {result.text}</p>
                <div className="flex gap-4 mt-1.5">
                  <span className="text-sm text-green-700">
                    Đã giao mới: <strong>{result.da_giao}</strong> CBCC
                  </span>
                  {(result.da_co ?? 0) > 0 && (
                    <span className="text-sm text-gray-500">
                      Bỏ qua: <strong>{result.da_co}</strong> đã có
                    </span>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-sm text-red-700">❌ {result.text}</p>
            )}
          </div>
        )}

        {/* ── E. Submit ── */}
        <div className="flex items-center gap-3 pt-2 border-t border-gray-100">
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting || !canSubmit()}
            className="px-6 py-2.5 bg-orange-600 text-white rounded-lg text-sm font-medium hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {submitLabel()}
          </button>
          {!selectedKhoaHocId && (
            <p className="text-xs text-gray-400">Chọn khóa học trước</p>
          )}
          {selectedKhoaHocId && mode === 'don-vi' && selectedDonViIds.length === 0 && (
            <p className="text-xs text-gray-400">Chọn ít nhất 1 đơn vị</p>
          )}
          {selectedKhoaHocId && mode === 'ca-nhan' && selectedCbccs.length === 0 && (
            <p className="text-xs text-gray-400">Thêm ít nhất 1 CBCC</p>
          )}
        </div>
      </div>
    </div>
  );
}
