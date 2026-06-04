/**
 * src/app/(main)/chi-tieu/danh-muc/page.tsx
 * =========================================
 * Quản lý danh mục: lĩnh vực + chỉ tiêu (QT_CHI_TIEU).
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { linhVucApi, danhMucApi } from '@/services/chi-tieu';
import type { IChiTieu, ILinhVuc, KieuDuLieu } from '@/types/chi-tieu';

const KIEU_LABEL: Record<KieuDuLieu, string> = {
  SO_NGUYEN: 'Số nguyên', THAP_PHAN: 'Thập phân', PHAN_TRAM: 'Phần trăm',
};

export default function DanhMucPage() {
  const [linhVucs, setLinhVucs] = useState<ILinhVuc[]>([]);
  const [chiTieus, setChiTieus] = useState<IChiTieu[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');

  // Form lĩnh vực
  const [lvForm, setLvForm] = useState({ ma_linh_vuc: '', ten_linh_vuc: '', van_ban_ke_hoach: '' });
  // Form chỉ tiêu
  const [ctForm, setCtForm] = useState({
    linh_vuc_id: '', ma_chi_tieu: '', ten_chi_tieu: '', don_vi_tinh: '',
    kieu_du_lieu: 'THAP_PHAN' as KieuDuLieu, co_phan_dau: false,
  });

  const load = async () => {
    setLoading(true);
    try {
      const [lvRes, ctRes] = await Promise.all([linhVucApi.danhSach(), danhMucApi.danhSach()]);
      setLinhVucs(lvRes.data.data || []);
      setChiTieus(ctRes.data.data || []);
    } catch (e: any) {
      setErr(e?.response?.data?.error?.message || 'Lỗi tải dữ liệu');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleErr = (e: any) => setErr(e?.response?.data?.error?.message || 'Có lỗi xảy ra');

  const taoLinhVuc = async () => {
    setErr('');
    if (!lvForm.ma_linh_vuc || !lvForm.ten_linh_vuc) { setErr('Nhập mã và tên lĩnh vực'); return; }
    try {
      await linhVucApi.taoMoi(lvForm);
      setLvForm({ ma_linh_vuc: '', ten_linh_vuc: '', van_ban_ke_hoach: '' });
      await load();
    } catch (e) { handleErr(e); }
  };

  const taoChiTieu = async () => {
    setErr('');
    if (!ctForm.linh_vuc_id || !ctForm.ma_chi_tieu || !ctForm.ten_chi_tieu || !ctForm.don_vi_tinh) {
      setErr('Điền đủ lĩnh vực, mã, tên, đơn vị tính'); return;
    }
    try {
      await danhMucApi.taoMoi(ctForm);
      setCtForm({ ...ctForm, ma_chi_tieu: '', ten_chi_tieu: '', don_vi_tinh: '', co_phan_dau: false });
      await load();
    } catch (e) { handleErr(e); }
  };

  const xoaChiTieu = async (id: string) => {
    if (!confirm('Xóa chỉ tiêu này?')) return;
    try { await danhMucApi.xoa(id); await load(); } catch (e) { handleErr(e); }
  };
  const xoaLinhVuc = async (id: string) => {
    if (!confirm('Xóa lĩnh vực này?')) return;
    try { await linhVucApi.xoa(id); await load(); } catch (e) { handleErr(e); }
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <Link href="/chi-tieu" className="text-sm text-blue-600 hover:underline">← Chỉ tiêu đơn vị</Link>
            <h1 className="text-2xl font-bold text-gray-900 mt-1">Danh mục chỉ tiêu</h1>
          </div>
        </div>

        {err && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{err}</div>}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Cột trái: tạo lĩnh vực + chỉ tiêu */}
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h2 className="font-semibold text-gray-900 mb-3">➕ Thêm lĩnh vực</h2>
              <div className="space-y-2">
                <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="Mã (vd GSQL)"
                  value={lvForm.ma_linh_vuc} onChange={(e) => setLvForm({ ...lvForm, ma_linh_vuc: e.target.value })} />
                <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="Tên lĩnh vực"
                  value={lvForm.ten_linh_vuc} onChange={(e) => setLvForm({ ...lvForm, ten_linh_vuc: e.target.value })} />
                <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="Văn bản kế hoạch (tùy chọn)"
                  value={lvForm.van_ban_ke_hoach} onChange={(e) => setLvForm({ ...lvForm, van_ban_ke_hoach: e.target.value })} />
                <button onClick={taoLinhVuc} className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2 text-sm font-medium">
                  Tạo lĩnh vực
                </button>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h2 className="font-semibold text-gray-900 mb-3">➕ Thêm chỉ tiêu</h2>
              <div className="space-y-2">
                <select className="w-full border rounded-lg px-3 py-2 text-sm"
                  value={ctForm.linh_vuc_id} onChange={(e) => setCtForm({ ...ctForm, linh_vuc_id: e.target.value })}>
                  <option value="">-- Chọn lĩnh vực --</option>
                  {linhVucs.map((lv) => <option key={lv.id} value={lv.id}>{lv.ma_linh_vuc} — {lv.ten_linh_vuc}</option>)}
                </select>
                <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="Mã (vd GSQL_01)"
                  value={ctForm.ma_chi_tieu} onChange={(e) => setCtForm({ ...ctForm, ma_chi_tieu: e.target.value })} />
                <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="Tên chỉ tiêu"
                  value={ctForm.ten_chi_tieu} onChange={(e) => setCtForm({ ...ctForm, ten_chi_tieu: e.target.value })} />
                <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="Đơn vị tính (vd triệu USD)"
                  value={ctForm.don_vi_tinh} onChange={(e) => setCtForm({ ...ctForm, don_vi_tinh: e.target.value })} />
                <select className="w-full border rounded-lg px-3 py-2 text-sm"
                  value={ctForm.kieu_du_lieu} onChange={(e) => setCtForm({ ...ctForm, kieu_du_lieu: e.target.value as KieuDuLieu })}>
                  {(Object.keys(KIEU_LABEL) as KieuDuLieu[]).map((k) => <option key={k} value={k}>{KIEU_LABEL[k]}</option>)}
                </select>
                <label className="flex items-center gap-2 text-sm text-gray-700">
                  <input type="checkbox" checked={ctForm.co_phan_dau}
                    onChange={(e) => setCtForm({ ...ctForm, co_phan_dau: e.target.checked })} />
                  Có mức phấn đấu (2 mức)
                </label>
                <button onClick={taoChiTieu} className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2 text-sm font-medium">
                  Tạo chỉ tiêu
                </button>
              </div>
            </div>
          </div>

          {/* Cột phải: danh sách theo lĩnh vực */}
          <div className="lg:col-span-2 space-y-4">
            {linhVucs.length === 0 && <div className="text-gray-500 text-sm">Chưa có lĩnh vực nào.</div>}
            {linhVucs.map((lv) => {
              const cts = chiTieus.filter((c) => c.linh_vuc_id === lv.id);
              return (
                <div key={lv.id} className="bg-white rounded-xl border border-gray-200">
                  <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-gray-900">{lv.ma_linh_vuc}</span>
                      <span className="text-gray-700"> — {lv.ten_linh_vuc}</span>
                      {lv.van_ban_ke_hoach && <span className="text-xs text-gray-400 ml-2">({lv.van_ban_ke_hoach})</span>}
                    </div>
                    <button onClick={() => xoaLinhVuc(lv.id)} className="text-xs text-red-500 hover:underline">Xóa</button>
                  </div>
                  <div className="p-3">
                    {cts.length === 0 ? (
                      <div className="text-xs text-gray-400 px-2 py-1">Chưa có chỉ tiêu</div>
                    ) : (
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-left text-xs text-gray-500 border-b">
                            <th className="py-1.5 px-2">Mã</th>
                            <th className="py-1.5 px-2">Tên</th>
                            <th className="py-1.5 px-2">ĐVT</th>
                            <th className="py-1.5 px-2">Mức</th>
                            <th className="py-1.5 px-2"></th>
                          </tr>
                        </thead>
                        <tbody>
                          {cts.map((c) => (
                            <tr key={c.id} className="border-b border-gray-50 last:border-0">
                              <td className="py-1.5 px-2 font-mono text-xs">{c.ma_chi_tieu}</td>
                              <td className="py-1.5 px-2">{c.ten_chi_tieu}</td>
                              <td className="py-1.5 px-2 text-gray-500">{c.don_vi_tinh}</td>
                              <td className="py-1.5 px-2">
                                {c.co_phan_dau
                                  ? <span className="text-xs px-1.5 py-0.5 bg-cyan-100 text-cyan-700 rounded">2 mức</span>
                                  : <span className="text-xs text-gray-400">1 mức</span>}
                              </td>
                              <td className="py-1.5 px-2 text-right">
                                <button onClick={() => xoaChiTieu(c.id)} className="text-xs text-red-500 hover:underline">Xóa</button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
