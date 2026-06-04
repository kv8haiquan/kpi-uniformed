/**
 * src/app/(main)/chi-tieu/nguoi-theo-doi/page.tsx
 * ===============================================
 * Quản lý người theo dõi chỉ tiêu (gán role THEO_DOI_CHI_TIEU theo đơn vị).
 * Quyền: QT_CHI_TIEU / admin.
 */

'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { nguoiTheoDoiApi } from '@/services/chi-tieu';
import { adminService } from '@/services/admin.service';
import type { ICongChucSearch, INguoiTheoDoi } from '@/types/chi-tieu';
import type { IDonViOption } from '@/types/admin';

export default function NguoiTheoDoiPage() {
  const [list, setList] = useState<INguoiTheoDoi[]>([]);
  const [donVis, setDonVis] = useState<IDonViOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const [msg, setMsg] = useState('');

  // Form gán
  const [search, setSearch] = useState('');
  const [ketQuaTim, setKetQuaTim] = useState<ICongChucSearch[]>([]);
  const [chon, setChon] = useState<ICongChucSearch | null>(null);
  const [donViIds, setDonViIds] = useState<Set<string>>(new Set());
  const [dangTim, setDangTim] = useState(false);
  const [saving, setSaving] = useState(false);

  const donViMap = useMemo(() => {
    const m: Record<string, IDonViOption> = {};
    donVis.forEach((d) => { m[d.id] = d; });
    return m;
  }, [donVis]);

  const load = async () => {
    setLoading(true);
    try {
      const [ntdRes, dvs] = await Promise.all([nguoiTheoDoiApi.danhSach(), adminService.getDonViList()]);
      setList(ntdRes.data.data || []);
      setDonVis(dvs);
    } catch (e: any) {
      setErr(e?.response?.data?.error?.message || 'Lỗi tải dữ liệu');
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const flash = (m: string) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };
  const onErr = (e: any) => setErr(e?.response?.data?.error?.message || 'Có lỗi xảy ra');

  const timCongChuc = async () => {
    if (!search.trim()) return;
    setDangTim(true); setErr('');
    try {
      const res = await nguoiTheoDoiApi.timCongChuc({ search: search.trim() });
      setKetQuaTim(res.data.data || []);
    } catch (e) { onErr(e); } finally { setDangTim(false); }
  };

  const toggleDonVi = (id: string) => {
    setDonViIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const batDauSua = (item: INguoiTheoDoi) => {
    setChon({ id: item.cong_chuc_id, ma_cc: item.ma_cc, ho_ten: item.ho_ten, chuc_vu: item.chuc_vu, ten_don_vi: item.don_vi_cong_chuc });
    setDonViIds(new Set(item.don_vi_ids));
    setKetQuaTim([]);
    setSearch('');
    if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const huyChon = () => { setChon(null); setDonViIds(new Set()); };

  const luuGan = async () => {
    if (!chon) { setErr('Chọn công chức trước'); return; }
    if (donViIds.size === 0) { setErr('Chọn ít nhất 1 đơn vị theo dõi'); return; }
    setSaving(true); setErr('');
    try {
      await nguoiTheoDoiApi.gan({ cong_chuc_id: chon.id, don_vi_ids: Array.from(donViIds) });
      flash(`Đã gán ${chon.ho_ten} theo dõi ${donViIds.size} đơn vị`);
      huyChon();
      await load();
    } catch (e) { onErr(e); } finally { setSaving(false); }
  };

  const go = async (item: INguoiTheoDoi) => {
    if (!confirm(`Gỡ ${item.ho_ten} khỏi vai trò theo dõi chỉ tiêu?`)) return;
    try { await nguoiTheoDoiApi.go(item.cong_chuc_id); flash('Đã gỡ'); await load(); }
    catch (e) { onErr(e); }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6">
          <Link href="/chi-tieu" className="text-sm text-blue-600 hover:underline">← Chỉ tiêu đơn vị</Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">Quản lý người theo dõi</h1>
          <p className="text-sm text-gray-500 mt-1">Gán công chức theo dõi chỉ tiêu cho từng đơn vị</p>
        </div>

        {err && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{err}</div>}
        {msg && <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm">{msg}</div>}

        {/* Form gán */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          <h2 className="font-semibold text-gray-900 mb-3">
            {chon ? '✏️ Cập nhật phạm vi' : '➕ Gán người theo dõi mới'}
          </h2>

          {!chon ? (
            <div className="flex gap-2 mb-3">
              <input className="flex-1 border rounded-lg px-3 py-2 text-sm" placeholder="Tìm theo tên hoặc mã công chức..."
                value={search} onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && timCongChuc()} />
              <button onClick={timCongChuc} disabled={dangTim}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm">
                {dangTim ? 'Đang tìm...' : 'Tìm'}
              </button>
            </div>
          ) : (
            <div className="flex items-center justify-between mb-3 p-2 bg-blue-50 rounded-lg">
              <div className="text-sm">
                <b>{chon.ho_ten}</b> <span className="text-gray-500">({chon.ma_cc})</span>
                {chon.ten_don_vi && <span className="text-gray-500"> · {chon.ten_don_vi}</span>}
              </div>
              <button onClick={huyChon} className="text-xs text-gray-500 hover:underline">Hủy</button>
            </div>
          )}

          {/* Kết quả tìm */}
          {!chon && ketQuaTim.length > 0 && (
            <div className="border rounded-lg divide-y mb-3 max-h-52 overflow-y-auto">
              {ketQuaTim.map((cc) => (
                <button key={cc.id} onClick={() => { setChon(cc); setKetQuaTim([]); setDonViIds(cc.don_vi_id ? new Set([cc.don_vi_id]) : new Set()); }}
                  className="w-full text-left px-3 py-2 hover:bg-gray-50 text-sm flex justify-between">
                  <span><b>{cc.ho_ten}</b> <span className="text-gray-400">({cc.ma_cc})</span></span>
                  <span className="text-gray-400">{cc.ten_don_vi}</span>
                </button>
              ))}
            </div>
          )}

          {/* Chọn đơn vị theo dõi */}
          {chon && (
            <>
              <div className="text-xs text-gray-500 mb-2">Chọn đơn vị mà người này theo dõi:</div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-4 max-h-60 overflow-y-auto">
                {donVis.map((dv) => (
                  <label key={dv.id} className={`flex items-center gap-2 text-sm border rounded-lg px-3 py-2 cursor-pointer ${donViIds.has(dv.id) ? 'border-blue-400 bg-blue-50' : 'border-gray-200'}`}>
                    <input type="checkbox" checked={donViIds.has(dv.id)} onChange={() => toggleDonVi(dv.id)} />
                    <span className="truncate">{dv.ma_don_vi} — {dv.ten_don_vi}</span>
                  </label>
                ))}
              </div>
              <button onClick={luuGan} disabled={saving}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium">
                {saving ? 'Đang lưu...' : `Lưu (${donViIds.size} đơn vị)`}
              </button>
            </>
          )}
        </div>

        {/* Danh sách hiện tại */}
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="px-5 py-3 border-b border-gray-100 font-semibold text-gray-900 text-sm">
            Người theo dõi hiện tại {list.length > 0 && <span className="text-gray-400 font-normal">({list.length})</span>}
          </div>
          {loading ? (
            <div className="p-8 text-center"><div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto" /></div>
          ) : list.length === 0 ? (
            <div className="p-6 text-center text-gray-500 text-sm">Chưa có người theo dõi nào.</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-500 border-b">
                  <th className="py-2 px-4">Họ tên</th>
                  <th className="py-2 px-4">Đơn vị công tác</th>
                  <th className="py-2 px-4">Theo dõi đơn vị</th>
                  <th className="py-2 px-4"></th>
                </tr>
              </thead>
              <tbody>
                {list.map((it) => (
                  <tr key={it.cong_chuc_id} className="border-b border-gray-50 last:border-0">
                    <td className="py-2 px-4">
                      <div className="font-medium text-gray-900">{it.ho_ten}</div>
                      <div className="text-xs text-gray-400">{it.ma_cc}{it.chuc_vu ? ` · ${it.chuc_vu}` : ''}</div>
                    </td>
                    <td className="py-2 px-4 text-gray-600">{it.don_vi_cong_chuc || '—'}</td>
                    <td className="py-2 px-4">
                      <div className="flex flex-wrap gap-1">
                        {it.don_vi_ids.length === 0 ? <span className="text-gray-400 text-xs italic">Chưa gán đơn vị</span> :
                          it.don_vi_ids.map((id) => (
                            <span key={id} className="text-xs px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">
                              {donViMap[id]?.ma_don_vi || id.slice(0, 8)}
                            </span>
                          ))}
                      </div>
                    </td>
                    <td className="py-2 px-4 text-right whitespace-nowrap">
                      <button onClick={() => batDauSua(it)} className="text-xs text-blue-600 hover:underline mr-3">Sửa</button>
                      <button onClick={() => go(it)} className="text-xs text-red-500 hover:underline">Gỡ</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <p className="text-xs text-gray-400 mt-4">
          ⓘ Sau khi gán, người theo dõi cần <b>đăng xuất và đăng nhập lại</b> để quyền (trong token) có hiệu lực.
        </p>
      </div>
    </div>
  );
}
