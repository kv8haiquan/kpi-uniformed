'use client';

// =============================================================================
// TRANG: Điều chỉnh điểm tiêu chí chung (Chi cục trưởng / LĐ Chi cục)
// -----------------------------------------------------------------------------
// CCT chọn tháng + đơn vị → xem danh sách công chức → sửa điểm tiêu chí chung
// (điểm "Đánh giá tháng") của từng người. Chỉ sửa được khi báo cáo xếp loại
// của đơn vị đó CHƯA chốt (NHAP/TU_CHOI).
// =============================================================================

import { useState, useEffect, useCallback, useMemo } from 'react';
import { SlidersHorizontal, Search } from 'lucide-react';
import { useAuthStore } from '@/stores/useAuthStore';
import { baoCaoXepLoaiService } from '@/services/bao-cao-xep-loai.service';
import SuaDiemTieuChiModal from '@/components/xep-loai/modals/SuaDiemTieuChiModal';
import type { IBaoCaoXepLoai, IChiTietXepLoai } from '@/types/bao-cao-xep-loai';
import { formatScore } from '@/lib/format';

const THANG_HIEN_TAI = new Date().getMonth() + 1;
const NAM_HIEN_TAI = new Date().getFullYear();

// Báo cáo được sửa điểm khi CHƯA chốt (khớp guard backend).
const TRANG_THAI_SUA_DUOC = ['NHAP', 'TU_CHOI', 'TRA_LAI'];

export default function DieuChinhTieuChiPage() {
  const { user } = useAuthStore();
  const maVaiTro = user?.vai_tro?.ma_vai_tro ?? '';
  // Trang dành cho LĐ Chi cục (CCT/PCCT) và admin.
  const canAccess =
    user?.is_system_admin === true || ['CCT', 'PCCT'].includes(maVaiTro);

  const [thang, setThang] = useState(THANG_HIEN_TAI);
  const [nam, setNam] = useState(NAM_HIEN_TAI);
  const [danhSach, setDanhSach] = useState<IBaoCaoXepLoai[]>([]);
  const [selectedBaoCaoId, setSelectedBaoCaoId] = useState<string>('');
  const [baoCao, setBaoCao] = useState<IBaoCaoXepLoai | null>(null);
  const [loadingList, setLoadingList] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedCC, setSelectedCC] = useState<IChiTietXepLoai | null>(null);

  // Tải danh sách báo cáo toàn Chi cục theo tháng
  const loadDanhSach = useCallback(async () => {
    if (!canAccess) return;
    setLoadingList(true);
    setBaoCao(null);
    setSelectedBaoCaoId('');
    try {
      const items = await baoCaoXepLoaiService.getDanhSach(thang, nam);
      setDanhSach(items);
      if (items.length > 0) setSelectedBaoCaoId(items[0].id);
    } finally {
      setLoadingList(false);
    }
  }, [thang, nam, canAccess]);

  useEffect(() => { loadDanhSach(); }, [loadDanhSach]);

  // Tải chi tiết 1 báo cáo (danh sách công chức)
  const loadDetail = useCallback(async (baoCaoId: string) => {
    if (!baoCaoId) { setBaoCao(null); return; }
    setLoadingDetail(true);
    try {
      const detail = await baoCaoXepLoaiService.getBaoCaoChiTiet(baoCaoId);
      setBaoCao(detail);
    } finally {
      setLoadingDetail(false);
    }
  }, []);

  useEffect(() => { loadDetail(selectedBaoCaoId); }, [selectedBaoCaoId, loadDetail]);

  const editable = useMemo(
    () => !!baoCao && TRANG_THAI_SUA_DUOC.includes(String(baoCao.trang_thai)),
    [baoCao]
  );

  const chiTietList = useMemo(() => {
    const list = baoCao?.chi_tiet ?? [];
    const q = search.trim().toLowerCase();
    const filtered = q
      ? list.filter((ct) =>
          (ct.cong_chuc?.ho_ten ?? '').toLowerCase().includes(q) ||
          (ct.cong_chuc?.ma_cc ?? '').toLowerCase().includes(q))
      : list;
    return [...filtered].sort((a, b) => (b.diem_tong ?? 0) - (a.diem_tong ?? 0));
  }, [baoCao, search]);

  if (!canAccess) {
    return (
      <div className="p-6">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800">
          Chức năng điều chỉnh điểm tiêu chí chung chỉ dành cho Chi cục trưởng / Phó Chi cục trưởng.
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-5">
        <div className="p-2.5 bg-emerald-50 rounded-xl">
          <SlidersHorizontal className="w-6 h-6 text-emerald-600" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-gray-900">Điều chỉnh điểm tiêu chí chung</h1>
          <p className="text-sm text-gray-500">
            Sửa trực tiếp điểm tiêu chí chung (Đánh giá tháng) của công chức. Điểm tổng và xếp loại tự cập nhật.
          </p>
        </div>
      </div>

      {/* Bộ lọc */}
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <select
          value={thang}
          onChange={(e) => setThang(Number(e.target.value))}
          className="px-4 py-2.5 border border-gray-300 rounded-lg text-sm bg-white"
        >
          {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
            <option key={m} value={m}>Tháng {m}</option>
          ))}
        </select>
        <select
          value={nam}
          onChange={(e) => setNam(Number(e.target.value))}
          className="px-4 py-2.5 border border-gray-300 rounded-lg text-sm bg-white"
        >
          {[NAM_HIEN_TAI - 1, NAM_HIEN_TAI, NAM_HIEN_TAI + 1].map((y) => (
            <option key={y} value={y}>Năm {y}</option>
          ))}
        </select>

        <select
          value={selectedBaoCaoId}
          onChange={(e) => setSelectedBaoCaoId(e.target.value)}
          disabled={loadingList || danhSach.length === 0}
          className="px-4 py-2.5 border border-gray-300 rounded-lg text-sm bg-white min-w-[220px]"
        >
          {danhSach.length === 0 && <option value="">— Không có báo cáo —</option>}
          {danhSach.map((bc) => (
            <option key={bc.id} value={bc.id}>
              {bc.don_vi?.ten_don_vi ?? 'Đơn vị'}
              {TRANG_THAI_SUA_DUOC.includes(String(bc.trang_thai)) ? '' : ' (đã chốt)'}
            </option>
          ))}
        </select>

        <div className="relative">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm mã CC / họ tên..."
            className="pl-9 pr-3 py-2.5 border border-gray-300 rounded-lg text-sm w-56"
          />
        </div>
      </div>

      {/* Trạng thái báo cáo */}
      {baoCao && (
        <div className="mb-3 text-sm">
          {editable ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-medium">
              ● Báo cáo chưa chốt — sửa điểm được
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gray-100 text-gray-600 text-xs font-medium">
              ● Báo cáo đã chốt — chỉ xem
            </span>
          )}
        </div>
      )}

      {/* Bảng công chức */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {loadingList || loadingDetail ? (
          <div className="py-16 text-center text-gray-500">Đang tải...</div>
        ) : !baoCao ? (
          <div className="py-16 text-center text-gray-500">
            {danhSach.length === 0 ? `Chưa có báo cáo xếp loại tháng ${thang}/${nam}.` : 'Chọn một đơn vị để xem danh sách công chức.'}
          </div>
        ) : chiTietList.length === 0 ? (
          <div className="py-16 text-center text-gray-500">Không có công chức phù hợp.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-gray-700">
                  <th className="px-3 py-2.5 text-left font-semibold w-12">STT</th>
                  <th className="px-3 py-2.5 text-left font-semibold">Công chức</th>
                  <th className="px-3 py-2.5 text-center font-semibold w-28">Điểm TC chung</th>
                  <th className="px-3 py-2.5 text-center font-semibold w-24">Điểm KPI</th>
                  <th className="px-3 py-2.5 text-center font-semibold w-24">Điểm tổng</th>
                  <th className="px-3 py-2.5 text-center font-semibold w-20">Xếp loại</th>
                  <th className="px-3 py-2.5 text-center font-semibold w-28">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {chiTietList.map((ct, idx) => (
                  <tr key={ct.id} className="hover:bg-gray-50">
                    <td className="px-3 py-2 text-gray-500">{idx + 1}</td>
                    <td className="px-3 py-2">
                      <div className="font-medium text-gray-900">{ct.cong_chuc?.ho_ten}</div>
                      <div className="text-xs text-gray-500">{ct.cong_chuc?.ma_cc}</div>
                    </td>
                    <td className="px-3 py-2 text-center font-medium text-emerald-700">{formatScore(ct.diem_tieu_chi_chung)}</td>
                    <td className="px-3 py-2 text-center text-gray-600">{formatScore(ct.diem_kpi)}</td>
                    <td className="px-3 py-2 text-center font-semibold text-gray-900">{formatScore(ct.diem_tong)}</td>
                    <td className="px-3 py-2 text-center">
                      <span className="inline-block px-2 py-0.5 rounded bg-gray-100 text-gray-700 text-xs font-semibold">
                        {ct.xep_loai_quyet_dinh || ct.xep_loai_de_xuat || ct.xep_loai_he_thong || '-'}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-center">
                      <button
                        onClick={() => setSelectedCC(ct)}
                        className={`px-3 py-1 text-xs rounded border transition-colors ${
                          editable
                            ? 'text-emerald-700 border-emerald-200 hover:bg-emerald-50'
                            : 'text-gray-600 border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        {editable ? 'Sửa điểm' : 'Xem'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal sửa điểm */}
      {selectedCC && (
        <SuaDiemTieuChiModal
          congChuc={selectedCC}
          thang={thang}
          nam={nam}
          readOnly={!editable}
          onClose={() => setSelectedCC(null)}
          onSaved={async () => {
            setSelectedCC(null);
            await loadDetail(selectedBaoCaoId);
          }}
        />
      )}
    </div>
  );
}
