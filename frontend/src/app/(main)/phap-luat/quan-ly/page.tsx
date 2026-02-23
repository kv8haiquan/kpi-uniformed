/**
 * src/app/(main)/phap-luat/quan-ly/page.tsx
 * ============================================
 * Trang quản trị văn bản pháp luật.
 * Chỉ hiển thị cho: BIEN_TAP, QT_NOI_DUNG, ADMIN.
 *
 * Gồm:
 *   - Tabs: Nháp | Chờ duyệt | Đã duyệt | Đã xuất bản
 *   - Table VB với workflow actions
 *   - Dialog tạo VB mới (form đơn giản)
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useAuthStore } from '@/stores/useAuthStore';
import { legalService } from '@/services/legal';
import type { IVanBanListItem, IVanBanDetail, ILoaiVanBan, IDonVi, ICongChuc } from '@/types/legal';

// =============================================================================
// TYPES
// =============================================================================
type TrangThaiDuyet = 'NHAP' | 'CHO_DUYET' | 'DA_DUYET' | 'DA_XUAT_BAN';

// =============================================================================
// HELPERS
// =============================================================================
const TRANG_THAI_TABS: { key: TrangThaiDuyet; label: string; color: string }[] = [
  { key: 'NHAP',        label: '✏️ Nháp',         color: 'text-gray-600' },
  { key: 'CHO_DUYET',   label: '⏳ Chờ duyệt',    color: 'text-yellow-600' },
  { key: 'DA_DUYET',    label: '✅ Đã duyệt',     color: 'text-blue-600' },
  { key: 'DA_XUAT_BAN', label: '📢 Đã xuất bản',  color: 'text-green-600' },
];

// =============================================================================
// FORM TẠO VĂN BẢN MỚI
// =============================================================================
function TaoVanBanForm({
  loaiVanBans,
  donVis,
  onSuccess,
  onClose,
}: {
  loaiVanBans: ILoaiVanBan[];
  donVis: IDonVi[];
  onSuccess: () => void;
  onClose: () => void;
}) {
  const [form, setForm] = useState({
    so_hieu: '',
    trich_yeu: '',
    loai_van_ban_id: '',
    co_quan_ban_hanh: '',
    ngay_ban_hanh: '',
    ngay_hieu_luc: '',
    trang_thai_hieu_luc: 'CON_HIEU_LUC',
    muc_do: 'BINH_THUONG',
    bat_buoc_doc: false,
    han_xac_nhan: '',
    tom_tat: '',
    diem_moi: '',
    viec_can_lam: '',
  });

  // ----- Đối tượng áp dụng -----
  const [doiTuongMode, setDoiTuongMode] = useState<'TAT_CA' | 'CHON_DON_VI' | 'CHON_CONG_CHUC'>('TAT_CA');
  const [selectedDonViIds, setSelectedDonViIds] = useState<string[]>([]);

  // Chọn công chức cụ thể
  const [selectedCCIds, setSelectedCCIds] = useState<string[]>([]);
  const [selectedCCMap, setSelectedCCMap] = useState<Record<string, ICongChuc>>({});
  const [ccSearch, setCcSearch] = useState('');
  const [ccDonViFilter, setCcDonViFilter] = useState('');
  const [ccPage, setCcPage] = useState(1);
  const [ccResults, setCcResults] = useState<ICongChuc[]>([]);
  const [ccTotalPages, setCcTotalPages] = useState(0);
  const [ccLoading, setCcLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounce search công chức khi ở mode CHON_CONG_CHUC
  useEffect(() => {
    if (doiTuongMode !== 'CHON_CONG_CHUC') return;
    setCcLoading(true);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      legalService
        .getCongChuc({
          search: ccSearch || undefined,
          don_vi_id: ccDonViFilter || undefined,
          page: ccPage,
          page_size: 10,
        })
        .then(res => {
          if (res.data?.success) {
            setCcResults(res.data.data ?? []);
            setCcTotalPages(res.data.pagination?.total_pages ?? 0);
          }
        })
        .catch(() => {})
        .finally(() => setCcLoading(false));
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doiTuongMode, ccSearch, ccDonViFilter, ccPage]);

  // Reset page về 1 khi đổi search/filter
  useEffect(() => { setCcPage(1); }, [ccSearch, ccDonViFilter]);

  const update = (k: string, v: string | boolean) => setForm(f => ({ ...f, [k]: v }));

  const changeMode = (mode: 'TAT_CA' | 'CHON_DON_VI' | 'CHON_CONG_CHUC') => {
    setDoiTuongMode(mode);
    if (mode !== 'CHON_DON_VI') setSelectedDonViIds([]);
    if (mode !== 'CHON_CONG_CHUC') {
      setSelectedCCIds([]);
      setSelectedCCMap({});
    }
  };

  const toggleDonVi = (id: string) =>
    setSelectedDonViIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );

  const toggleCC = (cc: ICongChuc) => {
    if (selectedCCIds.includes(cc.id)) {
      setSelectedCCIds(prev => prev.filter(id => id !== cc.id));
      setSelectedCCMap(prev => {
        const next = { ...prev };
        delete next[cc.id];
        return next;
      });
    } else {
      setSelectedCCIds(prev => [...prev, cc.id]);
      setSelectedCCMap(prev => ({ ...prev, [cc.id]: cc }));
    }
  };

  const removeCC = (id: string) => {
    setSelectedCCIds(prev => prev.filter(x => x !== id));
    setSelectedCCMap(prev => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
  };

  // Tổng CBCC theo mode
  const tongCBCC =
    doiTuongMode === 'TAT_CA'
      ? donVis.reduce((s, dv) => s + dv.so_cbcc, 0)
      : doiTuongMode === 'CHON_DON_VI'
      ? donVis.filter(dv => selectedDonViIds.includes(dv.id)).reduce((s, dv) => s + dv.so_cbcc, 0)
      : selectedCCIds.length;

  // doi_tuong_ap_dung gửi lên backend
  const doiTuongApDung =
    doiTuongMode === 'TAT_CA'
      ? ['TAT_CA']
      : doiTuongMode === 'CHON_DON_VI'
      ? selectedDonViIds
      : selectedCCIds.map(id => `cc:${id}`);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!form.so_hieu || !form.trich_yeu || !form.loai_van_ban_id || !form.co_quan_ban_hanh || !form.ngay_ban_hanh || !form.ngay_hieu_luc) {
      setError('Vui lòng điền đầy đủ thông tin bắt buộc (*)');
      return;
    }
    if (doiTuongMode === 'CHON_DON_VI' && selectedDonViIds.length === 0) {
      setError('Vui lòng chọn ít nhất 1 đơn vị áp dụng');
      return;
    }
    if (doiTuongMode === 'CHON_CONG_CHUC' && selectedCCIds.length === 0) {
      setError('Vui lòng chọn ít nhất 1 công chức áp dụng');
      return;
    }
    setLoading(true);
    setError('');
    try {
      // Bước 1: Tạo văn bản (trạng thái NHAP)
      const createRes = await legalService.createVanBan({
        so_hieu: form.so_hieu,
        trich_yeu: form.trich_yeu,
        loai_van_ban_id: form.loai_van_ban_id,
        co_quan_ban_hanh: form.co_quan_ban_hanh,
        ngay_ban_hanh: form.ngay_ban_hanh,
        ngay_hieu_luc: form.ngay_hieu_luc,
        trang_thai_hieu_luc: form.trang_thai_hieu_luc,
        muc_do: form.muc_do,
        bat_buoc_doc: form.bat_buoc_doc,
        han_xac_nhan: form.han_xac_nhan || undefined,
        tom_tat: form.tom_tat || undefined,
        diem_moi: form.diem_moi || undefined,
        viec_can_lam: form.viec_can_lam || undefined,
        doi_tuong_ap_dung: doiTuongApDung,
      });

      // Bước 2: Upload file nếu có chọn
      if (selectedFile && createRes.data?.data?.id) {
        try {
          await legalService.uploadFile(createRes.data.data.id, selectedFile);
        } catch {
          // VB đã tạo thành công — chỉ cảnh báo lỗi upload, không block
          setError('Văn bản đã lưu nhưng không thể upload file. Thử upload lại sau.');
          onSuccess();
          return;
        }
      }

      onSuccess();
      onClose();
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e?.message || 'Không thể tạo văn bản');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between shrink-0">
          <h2 className="text-lg font-bold text-gray-900">➕ Tạo văn bản mới</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700 text-xl">✕</button>
        </div>

        {/* Form */}
        <div className="p-6 overflow-y-auto space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Số hiệu *</label>
              <input
                type="text"
                placeholder="335/2025/NĐ-CP"
                value={form.so_hieu}
                onChange={e => update('so_hieu', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Loại văn bản *</label>
              <select
                value={form.loai_van_ban_id}
                onChange={e => update('loai_van_ban_id', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 bg-white"
              >
                <option value="">-- Chọn loại --</option>
                {loaiVanBans.map(l => (
                  <option key={l.id} value={l.id}>{l.ten}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Trích yếu *</label>
            <textarea
              rows={2}
              placeholder="Quy định về xử phạt vi phạm hành chính..."
              value={form.trich_yeu}
              onChange={e => update('trich_yeu', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Cơ quan ban hành *</label>
              <input
                type="text"
                placeholder="Chính phủ, Bộ Tài chính..."
                value={form.co_quan_ban_hanh}
                onChange={e => update('co_quan_ban_hanh', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Mức độ</label>
              <select
                value={form.muc_do}
                onChange={e => update('muc_do', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 bg-white"
              >
                <option value="BINH_THUONG">Bình thường</option>
                <option value="QUAN_TRONG">Quan trọng</option>
                <option value="KHAN">Khẩn</option>
                <option value="RAT_KHAN">Rất khẩn</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Ngày ban hành *</label>
              <input
                type="date"
                value={form.ngay_ban_hanh}
                onChange={e => update('ngay_ban_hanh', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Ngày hiệu lực *</label>
              <input
                type="date"
                value={form.ngay_hieu_luc}
                onChange={e => update('ngay_hieu_luc', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={form.bat_buoc_doc}
                onChange={e => update('bat_buoc_doc', e.target.checked)}
                className="accent-purple-600 w-4 h-4"
              />
              <span className="text-sm text-gray-700">Bắt buộc đọc và xác nhận</span>
            </label>
            {form.bat_buoc_doc && (
              <div className="flex-1">
                <input
                  type="date"
                  value={form.han_xac_nhan}
                  onChange={e => update('han_xac_nhan', e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400"
                  placeholder="Hạn xác nhận"
                />
              </div>
            )}
          </div>

          {/* Đối tượng áp dụng */}
          <div className="border border-gray-200 rounded-lg p-3">
            <label className="block text-xs font-medium text-gray-600 mb-2">Đối tượng áp dụng *</label>

            {/* 3 Radio options */}
            <div className="flex flex-wrap items-center gap-4 mb-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="doiTuongMode"
                  checked={doiTuongMode === 'TAT_CA'}
                  onChange={() => changeMode('TAT_CA')}
                  className="accent-purple-600"
                />
                <span className="text-sm text-gray-700">Toàn đơn vị</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="doiTuongMode"
                  checked={doiTuongMode === 'CHON_DON_VI'}
                  onChange={() => changeMode('CHON_DON_VI')}
                  className="accent-purple-600"
                />
                <span className="text-sm text-gray-700">Chọn đơn vị cụ thể</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="doiTuongMode"
                  checked={doiTuongMode === 'CHON_CONG_CHUC'}
                  onChange={() => changeMode('CHON_CONG_CHUC')}
                  className="accent-purple-600"
                />
                <span className="text-sm text-gray-700">Chọn công chức cụ thể</span>
              </label>
            </div>

            {/* Panel: Chọn đơn vị */}
            {doiTuongMode === 'CHON_DON_VI' && donVis.length > 0 && (
              <div className="max-h-44 overflow-y-auto border border-gray-100 rounded-lg divide-y divide-gray-50">
                {donVis.map(dv => (
                  <label
                    key={dv.id}
                    className="flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-purple-50 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={selectedDonViIds.includes(dv.id)}
                        onChange={() => toggleDonVi(dv.id)}
                        className="accent-purple-600 w-4 h-4"
                      />
                      <span className="text-sm text-gray-800">{dv.ten_don_vi}</span>
                    </div>
                    <span className="text-xs text-gray-400 shrink-0 ml-2">{dv.so_cbcc} CBCC</span>
                  </label>
                ))}
              </div>
            )}

            {/* Panel: Chọn công chức cụ thể */}
            {doiTuongMode === 'CHON_CONG_CHUC' && (
              <div className="space-y-2">
                {/* Search + filter row */}
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Tìm theo tên hoặc mã CC..."
                    value={ccSearch}
                    onChange={e => setCcSearch(e.target.value)}
                    className="flex-1 px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400"
                  />
                  <select
                    value={ccDonViFilter}
                    onChange={e => setCcDonViFilter(e.target.value)}
                    className="px-2 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 bg-white max-w-[140px]"
                  >
                    <option value="">-- Tất cả đơn vị --</option>
                    {donVis.map(dv => (
                      <option key={dv.id} value={dv.id}>{dv.ten_don_vi}</option>
                    ))}
                  </select>
                </div>

                {/* Chip tags cho CBCC đã chọn */}
                {selectedCCIds.length > 0 && (
                  <div className="flex flex-wrap gap-1 p-2 bg-purple-50 rounded-lg border border-purple-100">
                    {selectedCCIds.map(id => {
                      const cc = selectedCCMap[id];
                      return cc ? (
                        <span
                          key={id}
                          className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-100 text-purple-800 text-xs rounded-full"
                        >
                          {cc.ho_ten}
                          <button
                            type="button"
                            onClick={() => removeCC(id)}
                            className="text-purple-500 hover:text-purple-900 leading-none ml-0.5"
                          >
                            ×
                          </button>
                        </span>
                      ) : null;
                    })}
                  </div>
                )}

                {/* Danh sách kết quả tìm kiếm */}
                <div className="max-h-40 overflow-y-auto border border-gray-100 rounded-lg divide-y divide-gray-50">
                  {ccLoading ? (
                    <div className="flex items-center justify-center py-4">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600" />
                    </div>
                  ) : ccResults.length === 0 ? (
                    <p className="text-center text-xs text-gray-400 py-4">Không tìm thấy công chức</p>
                  ) : (
                    ccResults.map(cc => (
                      <label
                        key={cc.id}
                        className="flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-purple-50 transition-colors"
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <input
                            type="checkbox"
                            checked={selectedCCIds.includes(cc.id)}
                            onChange={() => toggleCC(cc)}
                            className="accent-purple-600 w-4 h-4 shrink-0"
                          />
                          <span className="text-sm text-gray-800 truncate">{cc.ho_ten}</span>
                        </div>
                        <span className="text-xs text-gray-400 shrink-0 ml-2">
                          {cc.ma_cc}
                          {cc.don_vi ? ` · ${cc.don_vi.ten_don_vi.split(' ').slice(-2).join(' ')}` : ''}
                        </span>
                      </label>
                    ))
                  )}
                </div>

                {/* Phân trang kết quả */}
                {ccTotalPages > 1 && (
                  <div className="flex items-center justify-center gap-2 text-xs">
                    <button
                      type="button"
                      onClick={() => setCcPage(p => Math.max(1, p - 1))}
                      disabled={ccPage === 1}
                      className="px-2 py-0.5 border border-gray-200 rounded disabled:opacity-40 hover:bg-gray-50"
                    >
                      ‹
                    </button>
                    <span className="text-gray-500">{ccPage} / {ccTotalPages}</span>
                    <button
                      type="button"
                      onClick={() => setCcPage(p => Math.min(ccTotalPages, p + 1))}
                      disabled={ccPage === ccTotalPages}
                      className="px-2 py-0.5 border border-gray-200 rounded disabled:opacity-40 hover:bg-gray-50"
                    >
                      ›
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Tổng CBCC sẽ nhận */}
            <p className="text-xs text-purple-600 mt-2 font-medium">
              {doiTuongMode === 'TAT_CA'
                ? `Tổng: ${tongCBCC} CBCC sẽ nhận văn bản`
                : doiTuongMode === 'CHON_DON_VI'
                ? selectedDonViIds.length === 0
                  ? 'Chưa chọn đơn vị nào'
                  : `Tổng: ${tongCBCC} CBCC từ ${selectedDonViIds.length} đơn vị`
                : selectedCCIds.length === 0
                ? 'Chưa chọn công chức nào'
                : `Đã chọn: ${selectedCCIds.length} công chức`}
            </p>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Điểm mới (tóm tắt)</label>
            <textarea
              rows={2}
              placeholder="1. Bổ sung hành vi vi phạm mới&#10;2. Tăng mức phạt..."
              value={form.diem_moi}
              onChange={e => update('diem_moi', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 resize-none"
            />
          </div>

          {/* File đính kèm (tuỳ chọn) */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              File đính kèm (PDF/DOCX, tối đa 50 MB)
            </label>
            <input
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={e => setSelectedFile(e.target.files?.[0] ?? null)}
              className="w-full text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-medium file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100 cursor-pointer"
            />
            {selectedFile && (
              <p className="text-xs text-gray-400 mt-1">
                Đã chọn: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            )}
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex gap-3 shrink-0">
          <button
            onClick={onClose}
            className="flex-1 py-2 border border-gray-200 text-gray-600 rounded-lg text-sm hover:bg-gray-50 transition-colors"
          >
            Hủy
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="flex-1 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
          >
            {loading ? 'Đang lưu...' : 'Lưu nháp'}
          </button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// FORM SỬA VĂN BẢN
// =============================================================================
/**
 * Dialog chỉnh sửa nội dung văn bản.
 * Tự fetch VB detail khi mở (để có đủ các field như viec_can_lam, tom_tat).
 * Khi VB ở trạng thái DA_XUAT_BAN: sửa sẽ tăng phien_ban (logic trong backend).
 */
function SuaVanBanForm({
  vbId,
  loaiVanBans,
  onSuccess,
  onClose,
}: {
  vbId: string;
  loaiVanBans: ILoaiVanBan[];
  onSuccess: () => void;
  onClose: () => void;
}) {
  const [vb, setVb] = useState<IVanBanDetail | null>(null);
  const [fetching, setFetching] = useState(true);
  const [form, setForm] = useState({
    trich_yeu: '',
    muc_do: 'BINH_THUONG',
    trang_thai_hieu_luc: 'CON_HIEU_LUC',
    bat_buoc_doc: false,
    han_xac_nhan: '',
    tom_tat: '',
    diem_moi: '',
    viec_can_lam: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch VB detail để pre-populate form
  useEffect(() => {
    setFetching(true);
    legalService.getVanBanById(vbId)
      .then(res => {
        if (res.data?.success) {
          const d: IVanBanDetail = res.data.data;
          setVb(d);
          setForm({
            trich_yeu: d.trich_yeu ?? '',
            muc_do: d.muc_do ?? 'BINH_THUONG',
            trang_thai_hieu_luc: d.trang_thai_hieu_luc ?? 'CON_HIEU_LUC',
            bat_buoc_doc: d.bat_buoc_doc ?? false,
            han_xac_nhan: d.han_xac_nhan ? String(d.han_xac_nhan).slice(0, 10) : '',
            tom_tat: d.tom_tat ?? '',
            diem_moi: d.diem_moi ?? '',
            viec_can_lam: d.viec_can_lam ?? '',
          });
        }
      })
      .catch(() => setError('Không thể tải thông tin văn bản.'))
      .finally(() => setFetching(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vbId]);

  const update = (k: string, v: string | boolean) => setForm(f => ({ ...f, [k]: v }));

  const handleSubmit = async () => {
    if (!form.trich_yeu.trim()) {
      setError('Trích yếu không được để trống');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await legalService.updateVanBan(vbId, {
        trich_yeu: form.trich_yeu,
        muc_do: form.muc_do,
        trang_thai_hieu_luc: form.trang_thai_hieu_luc,
        bat_buoc_doc: form.bat_buoc_doc,
        han_xac_nhan: form.han_xac_nhan || undefined,
        tom_tat: form.tom_tat || undefined,
        diem_moi: form.diem_moi || undefined,
        viec_can_lam: form.viec_can_lam || undefined,
      });
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e?.message || 'Không thể cập nhật văn bản');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between shrink-0">
          <div>
            <h2 className="text-lg font-bold text-gray-900">✏️ Chỉnh sửa văn bản</h2>
            {vb && (
              <p className="text-xs text-gray-500 mt-0.5 font-mono">{vb.so_hieu}</p>
            )}
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700 text-xl">✕</button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {fetching ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
            </div>
          ) : (
            <>
              {/* Cảnh báo khi sửa VB đã xuất bản */}
              {vb?.trang_thai_duyet === 'DA_XUAT_BAN' && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700 flex items-start gap-2">
                  <span className="shrink-0">⚠️</span>
                  <span>
                    Văn bản đã xuất bản. Lưu chỉnh sửa sẽ tự động tăng lên{' '}
                    <strong>Phiên bản {(vb.phien_ban ?? 1) + 1}</strong>.
                  </span>
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Trích yếu *</label>
                <textarea
                  rows={3}
                  value={form.trich_yeu}
                  onChange={e => update('trich_yeu', e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Mức độ</label>
                  <select
                    value={form.muc_do}
                    onChange={e => update('muc_do', e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 bg-white"
                  >
                    <option value="BINH_THUONG">Bình thường</option>
                    <option value="QUAN_TRONG">Quan trọng</option>
                    <option value="KHAN">Khẩn</option>
                    <option value="RAT_KHAN">Rất khẩn</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Tình trạng hiệu lực</label>
                  <select
                    value={form.trang_thai_hieu_luc}
                    onChange={e => update('trang_thai_hieu_luc', e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 bg-white"
                  >
                    <option value="CON_HIEU_LUC">Còn hiệu lực</option>
                    <option value="HET_HIEU_LUC">Hết hiệu lực</option>
                    <option value="CHUA_HIEU_LUC">Chưa hiệu lực</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.bat_buoc_doc}
                    onChange={e => update('bat_buoc_doc', e.target.checked)}
                    className="accent-purple-600 w-4 h-4"
                  />
                  <span className="text-sm text-gray-700">Bắt buộc đọc và xác nhận</span>
                </label>
                {form.bat_buoc_doc && (
                  <div className="flex-1">
                    <input
                      type="date"
                      value={form.han_xac_nhan}
                      onChange={e => update('han_xac_nhan', e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400"
                    />
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Tóm tắt</label>
                <textarea
                  rows={2}
                  value={form.tom_tat}
                  onChange={e => update('tom_tat', e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 resize-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Điểm mới</label>
                <textarea
                  rows={2}
                  value={form.diem_moi}
                  onChange={e => update('diem_moi', e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 resize-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Việc cần làm</label>
                <textarea
                  rows={2}
                  value={form.viec_can_lam}
                  onChange={e => update('viec_can_lam', e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 resize-none"
                />
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                  {error}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex gap-3 shrink-0">
          <button
            onClick={onClose}
            className="flex-1 py-2 border border-gray-200 text-gray-600 rounded-lg text-sm hover:bg-gray-50 transition-colors"
          >
            Hủy
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || fetching}
            className="flex-1 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
          >
            {loading ? 'Đang lưu...' : 'Lưu chỉnh sửa'}
          </button>
        </div>
      </div>
    </div>
  );
}


// =============================================================================
// MAIN PAGE
// =============================================================================
export default function QuanLyVanBanPage() {
  const user = useAuthStore(s => s.user);
  const platformRoles: string[] = (user as unknown as { platform_roles?: string[] })?.platform_roles ?? [];

  const coQuyenQuanLy =
    user?.is_system_admin === true ||
    platformRoles.includes('BIEN_TAP') ||
    platformRoles.includes('QT_NOI_DUNG');

  const coQuyenDuyet =
    user?.is_system_admin === true ||
    platformRoles.includes('QT_NOI_DUNG');

  const [activeTab, setActiveTab] = useState<TrangThaiDuyet>('NHAP');
  const [vanBans, setVanBans] = useState<IVanBanListItem[]>([]);
  const [loaiVanBans, setLoaiVanBans] = useState<ILoaiVanBan[]>([]);
  const [donVis, setDonVis] = useState<IDonVi[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingVbId, setEditingVbId] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Điều kiện hiển thị nút Sửa theo tab + role
  // QT_NOI_DUNG: sửa được mọi trạng thái
  // BIEN_TAP: chỉ sửa được NHAP và CHO_DUYET (VB của mình, backend đã kiểm tra)
  const canEditInTab =
    coQuyenDuyet ||  // QT_NOI_DUNG
    activeTab === 'NHAP' ||
    activeTab === 'CHO_DUYET';

  // Load danh sách đơn vị 1 lần khi mount (để chọn doi_tuong_ap_dung)
  useEffect(() => {
    legalService.getDonVi().then(res => {
      if (res.data?.success) setDonVis(res.data.data ?? []);
    }).catch(() => {});
  }, []);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [vbRes, loaiRes] = await Promise.all([
        // Endpoint quản lý — trả về tất cả VB theo trang_thai_duyet (không chỉ DA_XUAT_BAN)
        legalService.getVanBanQuanLy({ trang_thai_duyet: activeTab, page_size: 50 }),
        legalService.getLoaiVanBan(),
      ]);
      if (vbRes.data?.success) {
        setVanBans(vbRes.data.data ?? []);
      } else {
        console.warn('[Legal] getVanBanQuanLy:', vbRes.data?.error?.code, vbRes.data?.error?.message);
      }
      if (loaiRes.data?.success) {
        setLoaiVanBans(loaiRes.data.data ?? []);
      } else {
        console.warn('[Legal] getLoaiVanBan:', loaiRes.data?.error?.code, loaiRes.data?.error?.message);
      }
    } catch {
      // silent — lỗi auth/network đã được interceptor xử lý
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => { loadData(); }, [loadData]);

  // Không có quyền
  if (!coQuyenQuanLy) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
        <div className="bg-white rounded-xl border border-red-200 p-8 text-center max-w-md">
          <span className="text-4xl block mb-3">🔒</span>
          <p className="font-medium text-gray-700 mb-2">Không có quyền truy cập</p>
          <p className="text-sm text-gray-500 mb-4">
            Trang này chỉ dành cho BIÊN TẬP viên, Quản trị nội dung, và Admin.
          </p>
          <Link href="/phap-luat" className="text-sm text-purple-600 hover:underline">
            ← Về trang pháp luật
          </Link>
        </div>
      </div>
    );
  }

  const handleAction = async (vbId: string, action: string, ghiChu?: string) => {
    setActionLoading(vbId);
    try {
      const trangThaiMap: Record<string, string> = {
        'gui-duyet':  'CHO_DUYET',
        'duyet':      'DA_DUYET',
        'xuat-ban':   'DA_XUAT_BAN',
        'tu-choi':    'NHAP',
      };
      await legalService.updateTrangThai(vbId, {
        trang_thai_duyet: trangThaiMap[action],
        ghi_chu: ghiChu,
      });
      await loadData();
    } catch (err: unknown) {
      const e = err as { message?: string };
      alert(e?.message || 'Thao tác thất bại');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (vbId: string) => {
    if (!confirm('Xác nhận xóa văn bản này?')) return;
    try {
      await legalService.deleteVanBan(vbId);
      await loadData();
    } catch {
      alert('Không thể xóa văn bản');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <nav className="flex items-center gap-2 text-sm text-gray-400 mb-1">
              <Link href="/phap-luat" className="hover:text-purple-600 transition-colors">⚖️ Pháp luật</Link>
              <span>›</span>
              <span className="text-gray-700">Quản lý</span>
            </nav>
            <h1 className="text-2xl font-bold text-gray-900">⚙️ Quản lý văn bản</h1>
          </div>
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-sm font-medium transition-colors"
          >
            <span>➕</span> Tạo văn bản mới
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-100 rounded-xl p-1 mb-5 w-fit">
          {TRANG_THAI_TABS.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'bg-white shadow-sm text-purple-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
            </div>
          ) : vanBans.length === 0 ? (
            <div className="text-center py-16 text-gray-400">
              <span className="block text-4xl mb-3">📭</span>
              <p>Chưa có văn bản nào</p>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Số hiệu</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Trích yếu</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Loại</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Mức độ</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {vanBans.map(vb => (
                  <tr key={vb.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <Link
                        href={`/phap-luat/${vb.id}`}
                        className="text-sm font-mono text-purple-700 hover:underline"
                      >
                        {vb.so_hieu}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm text-gray-800 line-clamp-1 max-w-xs">{vb.trich_yeu}</p>
                      {(vb.phien_ban ?? 1) > 1 && (
                        <span className="text-xs text-blue-500">Phiên bản {vb.phien_ban}</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-gray-500">{vb.loai_van_ban.ten}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        vb.muc_do === 'RAT_KHAN' ? 'bg-red-100 text-red-700' :
                        vb.muc_do === 'KHAN' ? 'bg-orange-100 text-orange-700' :
                        vb.muc_do === 'QUAN_TRONG' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 text-gray-500'
                      }`}>
                        {vb.muc_do}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        {/* Gửi duyệt (NHAP) */}
                        {activeTab === 'NHAP' && (
                          <button
                            onClick={() => handleAction(vb.id, 'gui-duyet')}
                            disabled={actionLoading === vb.id}
                            className="text-xs px-2 py-1 bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 transition-colors"
                          >
                            Gửi duyệt
                          </button>
                        )}
                        {/* Duyệt + Từ chối (CHO_DUYET) */}
                        {activeTab === 'CHO_DUYET' && coQuyenDuyet && (
                          <>
                            <button
                              onClick={() => handleAction(vb.id, 'duyet')}
                              disabled={actionLoading === vb.id}
                              className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                            >
                              Duyệt
                            </button>
                            <button
                              onClick={() => handleAction(vb.id, 'tu-choi', 'Cần chỉnh sửa')}
                              disabled={actionLoading === vb.id}
                              className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                            >
                              Từ chối
                            </button>
                          </>
                        )}
                        {/* Xuất bản (DA_DUYET) */}
                        {activeTab === 'DA_DUYET' && coQuyenDuyet && (
                          <button
                            onClick={() => handleAction(vb.id, 'xuat-ban')}
                            disabled={actionLoading === vb.id}
                            className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                          >
                            Xuất bản
                          </button>
                        )}
                        {/* Xóa (chỉ NHAP) */}
                        {activeTab === 'NHAP' && (
                          <button
                            onClick={() => handleDelete(vb.id)}
                            className="text-xs px-2 py-1 bg-red-50 text-red-600 rounded hover:bg-red-100 transition-colors"
                          >
                            Xóa
                          </button>
                        )}
                        {/* Sửa */}
                        {canEditInTab && (
                          <button
                            onClick={() => setEditingVbId(vb.id)}
                            className="text-xs px-2 py-1 bg-indigo-50 text-indigo-600 rounded hover:bg-indigo-100 transition-colors"
                          >
                            ✏️ Sửa
                          </button>
                        )}
                        {/* Xem */}
                        <Link
                          href={`/phap-luat/${vb.id}`}
                          className="text-xs px-2 py-1 border border-gray-200 text-gray-600 rounded hover:bg-gray-50 transition-colors"
                        >
                          Xem
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Dialog tạo VB */}
        {showForm && (
          <TaoVanBanForm
            loaiVanBans={loaiVanBans}
            donVis={donVis}
            onSuccess={loadData}
            onClose={() => setShowForm(false)}
          />
        )}

        {/* Dialog sửa VB */}
        {editingVbId && (
          <SuaVanBanForm
            vbId={editingVbId}
            loaiVanBans={loaiVanBans}
            onSuccess={loadData}
            onClose={() => setEditingVbId(null)}
          />
        )}

      </div>
    </div>
  );
}
