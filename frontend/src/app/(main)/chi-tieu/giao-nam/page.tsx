/**
 * src/app/(main)/chi-tieu/giao-nam/page.tsx
 * =========================================
 * Giao chỉ tiêu năm cho đơn vị (QT_CHI_TIEU).
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { giaoNamApi, danhMucApi } from '@/services/chi-tieu';
import { adminService } from '@/services/admin.service';
import type { IChiTieu, IGiaoNam, LoaiMuc } from '@/types/chi-tieu';
import { LOAI_MUC_LABEL } from '@/types/chi-tieu';
import type { IDonViOption } from '@/types/admin';

const NAM_HIEN_TAI = new Date().getFullYear();

export default function GiaoNamPage() {
  const [donVis, setDonVis] = useState<IDonViOption[]>([]);
  const [chiTieus, setChiTieus] = useState<IChiTieu[]>([]);
  const [giaoNams, setGiaoNams] = useState<IGiaoNam[]>([]);
  const [donViId, setDonViId] = useState('');
  const [nam, setNam] = useState(NAM_HIEN_TAI);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');

  const [form, setForm] = useState({
    chi_tieu_id: '', loai_muc: 'PHAP_LENH' as LoaiMuc, gia_tri_giao: '', luy_ke_dau_ky: '0',
  });

  useEffect(() => {
    (async () => {
      try {
        const [dvs, ctRes] = await Promise.all([adminService.getDonViList(), danhMucApi.danhSach()]);
        setDonVis(dvs);
        setChiTieus(ctRes.data.data || []);
      } catch (e: any) {
        setErr(e?.response?.data?.error?.message || 'Lỗi tải danh mục');
      }
    })();
  }, []);

  const loadGiaoNam = async () => {
    if (!donViId) { setGiaoNams([]); return; }
    setLoading(true);
    try {
      const res = await giaoNamApi.danhSach({ nam, don_vi_id: donViId });
      setGiaoNams(res.data.data || []);
    } catch (e: any) {
      setErr(e?.response?.data?.error?.message || 'Lỗi tải giao năm');
    } finally { setLoading(false); }
  };

  useEffect(() => { loadGiaoNam(); }, [donViId, nam]);

  const tenChiTieu = (id: string) => {
    const c = chiTieus.find((x) => x.id === id);
    return c ? `${c.ma_chi_tieu} — ${c.ten_chi_tieu} (${c.don_vi_tinh})` : id;
  };

  const themGiao = async () => {
    setErr('');
    if (!donViId || !form.chi_tieu_id || !form.gia_tri_giao) { setErr('Chọn đơn vị, chỉ tiêu và nhập giá trị giao'); return; }
    try {
      await giaoNamApi.taoMoi({
        don_vi_id: donViId, chi_tieu_id: form.chi_tieu_id, nam, loai_muc: form.loai_muc,
        gia_tri_giao: form.gia_tri_giao, luy_ke_dau_ky: form.luy_ke_dau_ky || '0',
      });
      setForm({ ...form, chi_tieu_id: '', gia_tri_giao: '', luy_ke_dau_ky: '0' });
      await loadGiaoNam();
    } catch (e: any) {
      setErr(e?.response?.data?.error?.message || 'Lỗi tạo giao năm');
    }
  };

  const xoaGiao = async (id: string) => {
    if (!confirm('Xóa bản ghi giao năm này?')) return;
    try { await giaoNamApi.xoa(id); await loadGiaoNam(); }
    catch (e: any) { setErr(e?.response?.data?.error?.message || 'Lỗi xóa'); }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6">
          <Link href="/chi-tieu" className="text-sm text-blue-600 hover:underline">← Chỉ tiêu đơn vị</Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">Giao chỉ tiêu năm</h1>
        </div>

        {err && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{err}</div>}

        {/* Bộ lọc */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4 flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Đơn vị</label>
            <select className="border rounded-lg px-3 py-2 text-sm min-w-[260px]"
              value={donViId} onChange={(e) => setDonViId(e.target.value)}>
              <option value="">-- Chọn đơn vị --</option>
              {donVis.map((dv) => <option key={dv.id} value={dv.id}>{dv.ma_don_vi} — {dv.ten_don_vi}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Năm</label>
            <input type="number" className="border rounded-lg px-3 py-2 text-sm w-28"
              value={nam} onChange={(e) => setNam(Number(e.target.value))} />
          </div>
        </div>

        {donViId && (
          <>
            {/* Form thêm */}
            <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4">
              <h2 className="font-semibold text-gray-900 mb-3 text-sm">➕ Giao chỉ tiêu cho đơn vị</h2>
              <div className="grid grid-cols-1 md:grid-cols-12 gap-2 items-end">
                <div className="md:col-span-5">
                  <label className="block text-xs text-gray-500 mb-1">Chỉ tiêu</label>
                  <select className="w-full border rounded-lg px-3 py-2 text-sm"
                    value={form.chi_tieu_id} onChange={(e) => setForm({ ...form, chi_tieu_id: e.target.value })}>
                    <option value="">-- Chọn chỉ tiêu --</option>
                    {chiTieus.map((c) => <option key={c.id} value={c.id}>{c.ma_chi_tieu} — {c.ten_chi_tieu}</option>)}
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-xs text-gray-500 mb-1">Mức</label>
                  <select className="w-full border rounded-lg px-3 py-2 text-sm"
                    value={form.loai_muc} onChange={(e) => setForm({ ...form, loai_muc: e.target.value as LoaiMuc })}>
                    <option value="PHAP_LENH">Pháp lệnh</option>
                    <option value="PHAN_DAU">Phấn đấu</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-xs text-gray-500 mb-1">Giá trị giao</label>
                  <input type="number" step="0.001" className="w-full border rounded-lg px-3 py-2 text-sm"
                    value={form.gia_tri_giao} onChange={(e) => setForm({ ...form, gia_tri_giao: e.target.value })} />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-xs text-gray-500 mb-1">Lũy kế đầu kỳ</label>
                  <input type="number" step="0.001" className="w-full border rounded-lg px-3 py-2 text-sm"
                    value={form.luy_ke_dau_ky} onChange={(e) => setForm({ ...form, luy_ke_dau_ky: e.target.value })} />
                </div>
                <div className="md:col-span-1">
                  <button onClick={themGiao} className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2 text-sm font-medium">
                    Giao
                  </button>
                </div>
              </div>
            </div>

            {/* Danh sách */}
            <div className="bg-white rounded-xl border border-gray-200">
              <div className="px-5 py-3 border-b border-gray-100 font-semibold text-gray-900 text-sm">
                Chỉ tiêu đã giao năm {nam}
              </div>
              {loading ? (
                <div className="p-8 text-center"><div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto" /></div>
              ) : giaoNams.length === 0 ? (
                <div className="p-6 text-center text-gray-500 text-sm">Chưa giao chỉ tiêu nào cho đơn vị này.</div>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-gray-500 border-b">
                      <th className="py-2 px-4">Chỉ tiêu</th>
                      <th className="py-2 px-4">Mức</th>
                      <th className="py-2 px-4 text-right">Giá trị giao</th>
                      <th className="py-2 px-4 text-right">Lũy kế đầu kỳ</th>
                      <th className="py-2 px-4"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {giaoNams.map((g) => (
                      <tr key={g.id} className="border-b border-gray-50 last:border-0">
                        <td className="py-2 px-4">{tenChiTieu(g.chi_tieu_id)}</td>
                        <td className="py-2 px-4">
                          <span className={`text-xs px-1.5 py-0.5 rounded ${g.loai_muc === 'PHAP_LENH' ? 'bg-blue-100 text-blue-700' : 'bg-cyan-100 text-cyan-700'}`}>
                            {LOAI_MUC_LABEL[g.loai_muc]}
                          </span>
                        </td>
                        <td className="py-2 px-4 text-right font-medium">{g.gia_tri_giao}</td>
                        <td className="py-2 px-4 text-right text-gray-500">{g.luy_ke_dau_ky}</td>
                        <td className="py-2 px-4 text-right">
                          <button onClick={() => xoaGiao(g.id)} className="text-xs text-red-500 hover:underline">Xóa</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
