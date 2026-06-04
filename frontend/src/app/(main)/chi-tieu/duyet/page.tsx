/**
 * src/app/(main)/chi-tieu/duyet/page.tsx
 * ======================================
 * Hàng chờ duyệt của Trưởng đơn vị: đăng ký / sửa / kết quả.
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { duyetApi, danhMucApi } from '@/services/chi-tieu';
import type { IChiTieu, IDangKy, LoaiChoDuyet } from '@/types/chi-tieu';

const TABS: { key: LoaiChoDuyet; label: string }[] = [
  { key: 'DANG_KY', label: 'Đăng ký' },
  { key: 'SUA', label: 'Yêu cầu sửa' },
  { key: 'KET_QUA', label: 'Kết quả' },
];

export default function DuyetPage() {
  const [tab, setTab] = useState<LoaiChoDuyet>('DANG_KY');
  const [items, setItems] = useState<IDangKy[]>([]);
  const [ctMap, setCtMap] = useState<Record<string, IChiTieu>>({});
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');
  const [msg, setMsg] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const ctRes = await danhMucApi.danhSach();
        const map: Record<string, IChiTieu> = {};
        (ctRes.data.data || []).forEach((c: IChiTieu) => { map[c.id] = c; });
        setCtMap(map);
      } catch { /* ignore */ }
    })();
  }, []);

  const load = async () => {
    setLoading(true); setErr('');
    try {
      const res = await duyetApi.choXuLy({ loai: tab });
      setItems(res.data.data || []);
    } catch (e: any) {
      setErr(e?.response?.data?.error?.message || 'Lỗi tải hàng chờ');
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [tab]);

  const flash = (m: string) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  const duyet = async (id: string) => {
    try { await duyetApi.duyet(id); flash('Đã duyệt'); load(); }
    catch (e: any) { setErr(e?.response?.data?.error?.message || 'Lỗi duyệt'); }
  };
  const tuChoi = async (id: string) => {
    const ly_do = prompt('Lý do từ chối:');
    if (!ly_do) return;
    try { await duyetApi.tuChoi(id, ly_do); flash('Đã từ chối'); load(); }
    catch (e: any) { setErr(e?.response?.data?.error?.message || 'Lỗi từ chối'); }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6">
          <Link href="/chi-tieu" className="text-sm text-blue-600 hover:underline">← Chỉ tiêu đơn vị</Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">Duyệt chỉ tiêu</h1>
          <p className="text-sm text-gray-500 mt-1">Hàng chờ duyệt của đơn vị bạn phụ trách</p>
        </div>

        {err && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{err}</div>}
        {msg && <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm">{msg}</div>}

        <div className="flex gap-2 mb-4">
          {TABS.map((t) => (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${tab === t.key ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'}`}>
              {t.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="p-8 text-center"><div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto" /></div>
        ) : items.length === 0 ? (
          <div className="text-center py-12 text-gray-500 text-sm">Không có bản ghi nào chờ duyệt.</div>
        ) : (
          <div className="space-y-3">
            {items.map((it) => {
              const ct = ctMap[it.chi_tieu_id];
              return (
                <div key={it.id} className="bg-white rounded-xl border border-gray-200 p-4 flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="font-medium text-gray-900">{ct?.ten_chi_tieu || it.chi_tieu_id}</div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      Tháng {it.thang}/{it.nam}
                      {ct && <span> · ĐVT: {ct.don_vi_tinh}</span>}
                    </div>
                    <div className="text-sm text-gray-700 mt-1">
                      {it.khong_dang_ky
                        ? <span className="text-gray-400 italic">Không đăng ký</span>
                        : <>Đăng ký: <b>{it.gia_tri_dang_ky ?? '—'}</b></>}
                      {tab === 'KET_QUA' && <span className="ml-3">Kết quả: <b>{it.gia_tri_ket_qua ?? '—'}</b>
                        {it.danh_gia_tu_dong && <span className="ml-1 text-green-700">({it.danh_gia_tu_dong})</span>}</span>}
                    </div>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <button onClick={() => duyet(it.id)}
                      className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm">Duyệt</button>
                    <button onClick={() => tuChoi(it.id)}
                      className="px-3 py-1.5 bg-white border border-red-300 text-red-600 hover:bg-red-50 rounded-lg text-sm">Từ chối</button>
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
