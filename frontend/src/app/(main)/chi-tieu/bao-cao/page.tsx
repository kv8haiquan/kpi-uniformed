/**
 * src/app/(main)/chi-tieu/bao-cao/page.tsx
 * ========================================
 * Báo cáo rà soát theo tháng — lĩnh vực → chỉ tiêu → đơn vị.
 * Lũy kế cắt theo tháng đang xem.
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { baoCaoApi } from '@/services/chi-tieu';
import { adminService } from '@/services/admin.service';
import type { ILinhVucBaoCao } from '@/types/chi-tieu';
import { TRANG_THAI_LABEL } from '@/types/chi-tieu';
import type { IDonViOption } from '@/types/admin';

const NAM_HIEN_TAI = new Date().getFullYear();
const THANG_HIEN_TAI = new Date().getMonth() + 1;

export default function BaoCaoPage() {
  const [donVis, setDonVis] = useState<IDonViOption[]>([]);
  const [data, setData] = useState<ILinhVucBaoCao[]>([]);
  const [thang, setThang] = useState(THANG_HIEN_TAI);
  const [nam, setNam] = useState(NAM_HIEN_TAI);
  const [donViId, setDonViId] = useState('');
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');

  useEffect(() => {
    (async () => {
      try { setDonVis(await adminService.getDonViList()); } catch { /* ignore */ }
    })();
  }, []);

  const load = async () => {
    setLoading(true); setErr('');
    try {
      const res = await baoCaoApi.raSoat({ thang, nam, don_vi_id: donViId || undefined });
      setData(res.data.data || []);
    } catch (e: any) {
      setErr(e?.response?.data?.error?.message || 'Lỗi tải báo cáo');
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [thang, nam, donViId]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6">
          <Link href="/chi-tieu" className="text-sm text-blue-600 hover:underline">← Chỉ tiêu đơn vị</Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">Báo cáo rà soát</h1>
          <p className="text-sm text-gray-500 mt-1">Lũy kế năm cắt theo tháng đang xem</p>
        </div>

        {err && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{err}</div>}

        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4 flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Tháng</label>
            <select className="border rounded-lg px-3 py-2 text-sm w-24" value={thang} onChange={(e) => setThang(Number(e.target.value))}>
              {Array.from({ length: 12 }, (_, i) => i + 1).map((t) => <option key={t} value={t}>Tháng {t}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Năm</label>
            <input type="number" className="border rounded-lg px-3 py-2 text-sm w-28" value={nam} onChange={(e) => setNam(Number(e.target.value))} />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Đơn vị</label>
            <select className="border rounded-lg px-3 py-2 text-sm min-w-[220px]" value={donViId} onChange={(e) => setDonViId(e.target.value)}>
              <option value="">Tất cả đơn vị</option>
              {donVis.map((dv) => <option key={dv.id} value={dv.id}>{dv.ma_don_vi} — {dv.ten_don_vi}</option>)}
            </select>
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center"><div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto" /></div>
        ) : data.every((lv) => lv.chi_tieu.every((c) => c.dong_don_vi.length === 0)) ? (
          <div className="text-center py-12 text-gray-500 text-sm">Chưa có dữ liệu đăng ký/kết quả cho kỳ này.</div>
        ) : (
          <div className="space-y-5">
            {data.map((lv) => {
              const coData = lv.chi_tieu.some((c) => c.dong_don_vi.length > 0);
              if (!coData) return null;
              return (
                <div key={lv.linh_vuc_id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                  <div className="px-5 py-3 bg-gray-50 border-b border-gray-100">
                    <span className="font-semibold text-gray-900">{lv.ma_linh_vuc} — {lv.ten_linh_vuc}</span>
                    {lv.van_ban_ke_hoach && <span className="text-xs text-gray-400 ml-2">({lv.van_ban_ke_hoach})</span>}
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-xs text-gray-500 border-b">
                          <th className="py-2 px-4">Chỉ tiêu / Đơn vị</th>
                          <th className="py-2 px-3 text-right">Đăng ký</th>
                          <th className="py-2 px-3 text-right">Kết quả</th>
                          <th className="py-2 px-3">Đánh giá</th>
                          <th className="py-2 px-3 text-right">Lũy kế năm (Đạt%)</th>
                          <th className="py-2 px-3">Trạng thái</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lv.chi_tieu.filter((c) => c.dong_don_vi.length > 0).map((ct) => (
                          <ChiTieuRows key={ct.chi_tieu_id} ct={ct} />
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function ChiTieuRows({ ct }: { ct: ILinhVucBaoCao['chi_tieu'][number] }) {
  return (
    <>
      <tr className="bg-blue-50/40">
        <td colSpan={6} className="py-1.5 px-4 font-medium text-gray-800">
          {ct.ma_chi_tieu} — {ct.ten_chi_tieu} <span className="text-xs text-gray-400 font-normal">({ct.don_vi_tinh})</span>
        </td>
      </tr>
      {ct.dong_don_vi.map((d) => {
        const st = TRANG_THAI_LABEL[d.trang_thai];
        const mucs = Object.entries(d.luy_ke_nam);
        return (
          <tr key={d.don_vi_id} className="border-b border-gray-50 last:border-0">
            <td className="py-2 px-4 pl-8 text-gray-700">{d.ma_don_vi} — {d.ten_don_vi}</td>
            <td className="py-2 px-3 text-right">{d.khong_dang_ky ? <span className="text-gray-400 italic">Không ĐK</span> : (d.gia_tri_dang_ky ?? '—')}</td>
            <td className="py-2 px-3 text-right">{d.gia_tri_ket_qua ?? '—'}</td>
            <td className="py-2 px-3 text-gray-600">{d.danh_gia ?? '—'}</td>
            <td className="py-2 px-3 text-right">
              {mucs.length === 0 ? '—' : mucs.map(([muc, v]) => (
                <div key={muc} className="text-xs">
                  <span className="text-gray-400">{muc === 'PHAP_LENH' ? 'PL' : 'PĐ'}:</span> {v.luy_ke}
                  {v.dat_phan_tram != null && <span className="text-blue-600 font-medium"> ({v.dat_phan_tram}%)</span>}
                </div>
              ))}
            </td>
            <td className="py-2 px-3"><span className={`text-xs px-1.5 py-0.5 rounded-full ${st.bg} ${st.text}`}>{st.label}</span></td>
          </tr>
        );
      })}
    </>
  );
}
