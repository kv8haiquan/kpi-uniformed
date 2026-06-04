/**
 * src/components/lms/GiaoBaiModal.tsx
 * ==================================
 * Modal giao bài cho MỘT khóa học cụ thể — bố cục giống modal giao thí sinh ĐGNL.
 *
 * - Mở từ nút "Giao bài" trên mỗi dòng khóa học (khóa đã xuất bản).
 * - Hiển thị "Học viên hiện tại" (có nút Xóa/loại học viên).
 * - Chuyển mode kiểu pill: Giao theo đơn vị (accordion bỏ chọn) / Giao từng người.
 * - Loại đăng ký + Hạn hoàn thành.
 * - Submit: gửi cong_chuc_ids cuối cùng → POST /khoa-hoc/{id}/giao-bai.
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import { dangKyApi, cbccApi } from '@/services/lms';
import DonViCongChucPicker from './DonViCongChucPicker';
import CBCCPicker, { type ICBCCItem } from './CBCCPicker';

// =============================================================================
// TYPES & HELPERS
// =============================================================================

interface IHocVien {
  dang_ky_id: string;
  cong_chuc_id: string;
  ho_ten: string | null;
  ma_cc: string | null;
  don_vi_ten: string | null;
  trang_thai: string;
}

interface GiaoBaiModalProps {
  khoaHoc: { id: string; ma_khoa_hoc: string; ten_khoa_hoc: string };
  onClose: () => void;
}

const TT_HV: Record<string, { label: string; cls: string }> = {
  CHUA_BAT_DAU:  { label: 'Chưa bắt đầu', cls: 'bg-gray-100 text-gray-600' },
  CHO_PHE_DUYET: { label: 'Chờ duyệt',    cls: 'bg-yellow-100 text-yellow-700' },
  DANG_HOC:      { label: 'Đang học',     cls: 'bg-blue-100 text-blue-700' },
  HOAN_THANH:    { label: 'Hoàn thành',   cls: 'bg-green-100 text-green-700' },
  TU_CHOI:       { label: 'Từ chối',      cls: 'bg-red-100 text-red-700' },
};

function errMsg(err: unknown, fallback: string): string {
  return (
    (err as { response?: { data?: { detail?: { error?: { message?: string } } } } })
      ?.response?.data?.detail?.error?.message || fallback
  );
}

// =============================================================================
// COMPONENT
// =============================================================================

export default function GiaoBaiModal({ khoaHoc, onClose }: GiaoBaiModalProps) {
  const [mode, setMode] = useState<'don-vi' | 'ca-nhan'>('don-vi');

  // Đơn vị
  const [donViList, setDonViList] = useState<{ id: string; ten_don_vi: string }[]>([]);
  const [donViLoading, setDonViLoading] = useState(true);

  // Lựa chọn người nhận
  const [donViCongChucIds, setDonViCongChucIds] = useState<string[]>([]);
  const [donViPickerKey, setDonViPickerKey] = useState(0);
  const handleDonViChange = useCallback((ids: string[]) => setDonViCongChucIds(ids), []);
  const [selectedCbccs, setSelectedCbccs] = useState<ICBCCItem[]>([]);

  // Cấu hình
  const [loaiDangKy, setLoaiDangKy] = useState('BAT_BUOC');
  const [hanHoanThanh, setHanHoanThanh] = useState('');

  // Submit
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ da_giao: number; da_co: number; tong: number } | null>(null);

  // Học viên hiện tại
  const [existingHV, setExistingHV] = useState<IHocVien[]>([]);
  const [loadingHV, setLoadingHV] = useState(true);

  const loadHocVien = useCallback(async () => {
    try {
      const res = await dangKyApi.hocVien(khoaHoc.id, { page_size: 200 });
      setExistingHV(res.data.data || []);
    } catch {
      // Chỉ GIANG_VIEN/QT_DAO_TAO xem được — bỏ qua nếu không có quyền
      setExistingHV([]);
    } finally {
      setLoadingHV(false);
    }
  }, [khoaHoc.id]);

  // Load đơn vị + học viên hiện tại
  useEffect(() => {
    (async () => {
      try {
        const res = await cbccApi.getDonVi();
        setDonViList(res.data.data || []);
      } catch {
        // bỏ qua
      } finally {
        setDonViLoading(false);
      }
    })();
    loadHocVien();
  }, [loadHocVien]);

  const handleAddCBCC = useCallback((cc: ICBCCItem) => {
    setSelectedCbccs((prev) => (prev.some((c) => c.id === cc.id) ? prev : [...prev, cc]));
  }, []);
  const handleRemoveCBCC = useCallback((id: string) => {
    setSelectedCbccs((prev) => prev.filter((c) => c.id !== id));
  }, []);

  const handleDeleteHV = async (hv: IHocVien) => {
    if (!confirm(`Loại "${hv.ho_ten}" khỏi khóa học này?`)) return;
    try {
      await dangKyApi.loaiHocVien(hv.dang_ky_id);
      setExistingHV((prev) => prev.filter((x) => x.dang_ky_id !== hv.dang_ky_id));
    } catch (err) {
      setError(errMsg(err, 'Không thể loại học viên'));
    }
  };

  const soChon = mode === 'don-vi' ? donViCongChucIds.length : selectedCbccs.length;
  const canSubmit = soChon > 0;

  const handleSubmit = async () => {
    if (!canSubmit || saving) return;
    setSaving(true); setError(null); setResult(null);
    try {
      const body: Record<string, unknown> = {
        loai_dang_ky: loaiDangKy,
        ...(hanHoanThanh && { han_hoan_thanh: hanHoanThanh }),
        cong_chuc_ids: mode === 'don-vi' ? donViCongChucIds : selectedCbccs.map((c) => c.id),
      };
      const res = await dangKyApi.giaoBai(khoaHoc.id, body);
      const d = res.data.data;
      setResult({ da_giao: d.da_giao, da_co: d.da_co, tong: d.tong });
      // Reset lựa chọn + reload danh sách học viên
      setDonViCongChucIds([]);
      setDonViPickerKey((k) => k + 1);
      setSelectedCbccs([]);
      loadHocVien();
    } catch (err) {
      setError(errMsg(err, 'Lỗi giao bài. Thử lại sau.'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-lg">📋 Giao bài — {khoaHoc.ten_khoa_hoc}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
        </div>

        {error && <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">{error}</div>}
        {result && (
          <div className="mb-3 p-2 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
            Đã giao mới: {result.da_giao} | Bỏ qua (trùng): {result.da_co} | Tổng: {result.tong}
          </div>
        )}

        {/* Học viên hiện tại */}
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Học viên hiện tại ({existingHV.length})</h4>
          {loadingHV ? (
            <div className="text-xs text-gray-400">Đang tải...</div>
          ) : existingHV.length === 0 ? (
            <div className="text-xs text-gray-400 py-2">Chưa có học viên nào</div>
          ) : (
            <div className="max-h-40 overflow-y-auto border rounded-lg">
              <table className="w-full text-xs">
                <thead className="bg-gray-50 sticky top-0">
                  <tr className="text-gray-500">
                    <th className="py-1 px-2 text-left">Mã CC</th>
                    <th className="py-1 px-2 text-left">Họ tên</th>
                    <th className="py-1 px-2 text-left">Đơn vị</th>
                    <th className="py-1 px-2 text-center">Trạng thái</th>
                    <th className="py-1 px-2 w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {existingHV.map((hv) => {
                    const tt = TT_HV[hv.trang_thai] || { label: hv.trang_thai, cls: 'bg-gray-100 text-gray-600' };
                    return (
                      <tr key={hv.dang_ky_id} className="border-t">
                        <td className="py-1 px-2 font-mono">{hv.ma_cc}</td>
                        <td className="py-1 px-2">{hv.ho_ten}</td>
                        <td className="py-1 px-2 text-gray-500">{hv.don_vi_ten}</td>
                        <td className="py-1 px-2 text-center">
                          <span className={`px-1.5 py-0.5 rounded-full ${tt.cls}`}>{tt.label}</span>
                        </td>
                        <td className="py-1 px-2 text-center">
                          {hv.trang_thai !== 'HOAN_THANH' && (
                            <button onClick={() => handleDeleteHV(hv)} className="text-red-500 hover:underline">Xóa</button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <hr className="mb-4" />

        {/* Mode switch */}
        <div className="flex gap-2 mb-4">
          <button onClick={() => { setMode('don-vi'); setResult(null); }}
            className={`px-4 py-2 text-sm rounded-lg ${mode === 'don-vi' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}`}>
            Giao theo đơn vị
          </button>
          <button onClick={() => { setMode('ca-nhan'); setResult(null); }}
            className={`px-4 py-2 text-sm rounded-lg ${mode === 'ca-nhan' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}`}>
            Giao từng người
          </button>
        </div>

        {/* Mode: đơn vị (accordion — bỏ chọn từng người) */}
        {mode === 'don-vi' && (
          <div className="mb-4">
            <label className="text-xs font-medium text-gray-600 block mb-1">
              Chọn đơn vị — tick để chọn sẵn toàn bộ, mở rộng để bỏ chọn từng người
            </label>
            <DonViCongChucPicker
              key={donViPickerKey}
              donVis={donViList}
              donViLoading={donViLoading}
              onChange={handleDonViChange}
            />
          </div>
        )}

        {/* Mode: cá nhân */}
        {mode === 'ca-nhan' && (
          <div className="mb-4">
            <CBCCPicker selected={selectedCbccs} onAdd={handleAddCBCC} onRemove={handleRemoveCBCC} />
          </div>
        )}

        {/* Cấu hình */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Loại đăng ký</label>
            <select value={loaiDangKy} onChange={(e) => setLoaiDangKy(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm bg-white">
              <option value="BAT_BUOC">🔴 Bắt buộc</option>
              <option value="GIAO_VIEC">📋 Giao việc</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Hạn hoàn thành <span className="text-gray-400 font-normal">(tuỳ chọn)</span>
            </label>
            <input type="date" value={hanHoanThanh} onChange={(e) => setHanHoanThanh(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2 border-t">
          <button onClick={handleSubmit} disabled={saving || !canSubmit}
            className="px-6 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 text-sm">
            {saving ? 'Đang giao...' : canSubmit ? `Giao cho ${soChon} CBCC` : 'Giao bài'}
          </button>
          <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm">Đóng</button>
        </div>
      </div>
    </div>
  );
}
