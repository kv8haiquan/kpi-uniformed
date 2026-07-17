'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuthStore } from '@/stores/useAuthStore';
import { doiSoatService } from '@/services/doi-soat.service';
import { IDoiSoatData, IDoiSoatNhomMeta, MucDo } from '@/types/doi-soat';
import { ClipboardCheck, Download, RefreshCw, ChevronDown, ChevronRight } from 'lucide-react';

const MUC_DO_STYLE: Record<MucDo, { chip: string; dot: string; label: string }> = {
  cao: { chip: 'bg-red-50 text-red-700 border-red-200', dot: 'bg-red-500', label: 'Cao' },
  trung_binh: { chip: 'bg-amber-50 text-amber-700 border-amber-200', dot: 'bg-amber-500', label: 'Trung bình' },
  thap: { chip: 'bg-gray-50 text-gray-600 border-gray-200', dot: 'bg-gray-400', label: 'Thấp' },
};

export default function DoiSoatPage() {
  const { user } = useAuthStore();
  const now = new Date();

  // Mặc định soi tháng TRƯỚC (kỳ vừa chốt) cho tiện đối soát.
  const [thang, setThang] = useState(now.getMonth() === 0 ? 12 : now.getMonth());
  const [nam, setNam] = useState(now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear());

  const [data, setData] = useState<IDoiSoatData | null>(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const canView =
    user?.is_system_admin === true ||
    user?.can_view_all_units === true ||
    ['CCT', 'PCCT', 'TCCB'].includes(user?.vai_tro?.ma_vai_tro ?? '');

  const load = useCallback(async () => {
    if (!canView) return;
    try {
      setLoading(true);
      setError(null);
      const res = await doiSoatService.getDoiSoat(thang, nam);
      setData(res);
      // Mở sẵn các nhóm có dữ liệu
      if (res) {
        const init: Record<string, boolean> = {};
        res.meta.forEach((m) => { init[m.key] = (res.tong_hop[m.key] ?? 0) > 0; });
        setExpanded(init);
      }
    } catch {
      setError('Không tải được dữ liệu đối soát. Vui lòng thử lại.');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [thang, nam, canView]);

  useEffect(() => { load(); }, [load]);

  const handleExport = async () => {
    try {
      setDownloading(true);
      await doiSoatService.exportDoiSoat(thang, nam);
    } catch {
      alert('Không thể tải file Excel. Vui lòng thử lại.');
    } finally {
      setDownloading(false);
    }
  };

  const metaByKey = useMemo(() => {
    const m: Record<string, IDoiSoatNhomMeta> = {};
    data?.meta.forEach((x) => { m[x.key] = x; });
    return m;
  }, [data]);

  if (!canView) {
    return (
      <div className="p-6">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800">
          Chức năng đối soát chỉ dành cho TCCB và Lãnh đạo Chi cục.
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-50 rounded-xl">
            <ClipboardCheck className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Đối soát hoàn thành đánh giá tháng</h1>
            <p className="text-sm text-gray-500">
              Danh sách công chức chưa hoàn tất kê khai / duyệt — để nhắc đơn vị xử lý trước khi chốt.
            </p>
          </div>
        </div>
      </div>

      {/* Bộ lọc */}
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <select
          value={thang}
          onChange={(e) => setThang(Number(e.target.value))}
          className="px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
        >
          {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
            <option key={m} value={m}>Tháng {m}</option>
          ))}
        </select>
        <select
          value={nam}
          onChange={(e) => setNam(Number(e.target.value))}
          className="px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
        >
          {Array.from({ length: 6 }, (_, i) => now.getFullYear() - 4 + i).map((y) => (
            <option key={y} value={y}>Năm {y}</option>
          ))}
        </select>
        <button
          onClick={load}
          disabled={loading}
          className="px-4 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 inline-flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Tải lại
        </button>
        <button
          onClick={handleExport}
          disabled={downloading || !data || data.tong_so_ca === 0}
          className="px-4 py-2.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 inline-flex items-center gap-2"
        >
          <Download className="w-4 h-4" /> {downloading ? 'Đang tải…' : 'Xuất Excel'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700 mb-4">{error}</div>
      )}

      {loading ? (
        <p className="text-sm text-gray-500">Đang tải dữ liệu…</p>
      ) : !data ? null : (
        <>
          {/* Tổng hợp */}
          <div className="mb-4 text-sm text-gray-600">
            Tháng {data.thang}/{data.nam}:{' '}
            <span className="font-semibold text-gray-900">{data.tong_so_ca}</span> trường hợp cần xử lý.{' '}
            <span className="text-gray-400">(Một người có thể xuất hiện ở nhiều nhóm.)</span>
          </div>

          {/* Thẻ tóm tắt mỗi nhóm */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
            {data.meta.map((m) => {
              const count = data.tong_hop[m.key] ?? 0;
              const st = MUC_DO_STYLE[m.muc_do];
              return (
                <button
                  key={m.key}
                  onClick={() => setExpanded((p) => ({ ...p, [m.key]: !p[m.key] }))}
                  className={`text-left p-3 rounded-xl border ${count > 0 ? 'border-gray-200 bg-white' : 'border-gray-100 bg-gray-50'} hover:shadow-sm transition`}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className={`w-2 h-2 rounded-full ${st.dot}`} />
                    <span className="text-2xl font-bold text-gray-900">{count}</span>
                  </div>
                  <div className="text-xs text-gray-600 leading-snug line-clamp-2">{m.ten}</div>
                </button>
              );
            })}
          </div>

          {data.tong_so_ca === 0 ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-sm text-green-800">
              ✅ Tất cả công chức đã hoàn tất — không có trường hợp nào cần xử lý trong tháng này.
            </div>
          ) : (
            <div className="space-y-3">
              {data.meta.map((m) => {
                const rows = data.nhom[m.key] ?? [];
                if (rows.length === 0) return null;
                const st = MUC_DO_STYLE[m.muc_do];
                const open = expanded[m.key];
                return (
                  <div key={m.key} className="border border-gray-200 rounded-xl overflow-hidden">
                    <button
                      onClick={() => setExpanded((p) => ({ ...p, [m.key]: !p[m.key] }))}
                      className="w-full flex items-center gap-3 px-4 py-3 bg-gray-50 hover:bg-gray-100 text-left"
                    >
                      {open ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${st.chip}`}>{st.label}</span>
                      <span className="font-semibold text-gray-900">{m.ten}</span>
                      <span className="text-sm text-gray-500">({rows.length})</span>
                    </button>
                    {open && (
                      <div>
                        <p className="px-4 py-2 text-xs text-gray-500 bg-white border-t border-gray-100">
                          {metaByKey[m.key]?.mo_ta}
                        </p>
                        <div className="overflow-x-auto">
                          <table className="min-w-full text-sm">
                            <thead className="bg-white border-y border-gray-100">
                              <tr className="text-xs text-gray-500">
                                <th className="px-3 py-2 text-left font-semibold">Mã CC</th>
                                <th className="px-3 py-2 text-left font-semibold">Họ tên</th>
                                <th className="px-3 py-2 text-left font-semibold">Đơn vị</th>
                                <th className="px-3 py-2 text-left font-semibold">Vai trò</th>
                                <th className="px-3 py-2 text-left font-semibold">Chi tiết</th>
                                <th className="px-3 py-2 text-left font-semibold">Người cần xử lý</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                              {rows.map((it) => (
                                <tr key={`${m.key}-${it.cong_chuc_id}`} className="hover:bg-gray-50">
                                  <td className="px-3 py-2 font-mono text-xs text-gray-700 whitespace-nowrap">{it.ma_cc}</td>
                                  <td className="px-3 py-2 text-gray-900 whitespace-nowrap">{it.ho_ten}</td>
                                  <td className="px-3 py-2 text-gray-600">{it.don_vi_ten ?? '—'}</td>
                                  <td className="px-3 py-2 text-gray-500 text-xs">{it.vai_tro ?? '—'}</td>
                                  <td className="px-3 py-2 text-gray-600">{it.chi_tiet}</td>
                                  <td className="px-3 py-2 text-gray-700">{it.nguoi_xu_ly ?? '—'}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}
