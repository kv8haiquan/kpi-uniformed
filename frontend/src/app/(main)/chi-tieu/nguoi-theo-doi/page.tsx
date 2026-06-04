/**
 * src/app/(main)/chi-tieu/nguoi-theo-doi/page.tsx
 * ===============================================
 * Quản lý người theo dõi chỉ tiêu — đơn-vị-centric:
 * chọn đơn vị → xem/thêm người theo dõi đơn vị đó (dropdown người trong đơn vị).
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

  // Luồng gán: chọn đơn vị → chọn người trong đơn vị
  const [donViId, setDonViId] = useState('');
  const [nguoiTrongDonVi, setNguoiTrongDonVi] = useState<ICongChucSearch[]>([]);
  const [loadingNguoi, setLoadingNguoi] = useState(false);
  const [chonNguoiId, setChonNguoiId] = useState('');
  const [nguoiSearch, setNguoiSearch] = useState('');
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

  // Khi chọn đơn vị → load người trong đơn vị đó
  useEffect(() => {
    if (!donViId) { setNguoiTrongDonVi([]); setChonNguoiId(''); setNguoiSearch(''); return; }
    (async () => {
      setLoadingNguoi(true); setChonNguoiId(''); setNguoiSearch('');
      try {
        const res = await nguoiTheoDoiApi.timCongChuc({ don_vi_id: donViId });
        setNguoiTrongDonVi(res.data.data || []);
      } catch (e: any) {
        setErr(e?.response?.data?.error?.message || 'Lỗi tải danh sách công chức');
      } finally { setLoadingNguoi(false); }
    })();
  }, [donViId]);

  const flash = (m: string) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };
  const onErr = (e: any) => setErr(e?.response?.data?.error?.message || 'Có lỗi xảy ra');

  // Người đang theo dõi đơn vị đang chọn
  const nguoiDangTheoDoi = useMemo(
    () => list.filter((p) => p.don_vi_ids.includes(donViId)),
    [list, donViId],
  );
  const dangTheoDoiIds = new Set(nguoiDangTheoDoi.map((p) => p.cong_chuc_id));

  // Thêm 1 người theo dõi đơn vị đang chọn (append vào phạm vi hiện có của họ)
  const themNguoi = async () => {
    if (!donViId || !chonNguoiId) { setErr('Chọn đơn vị và người'); return; }
    setSaving(true); setErr('');
    try {
      const existing = list.find((p) => p.cong_chuc_id === chonNguoiId)?.don_vi_ids ?? [];
      const don_vi_ids = Array.from(new Set([...existing, donViId]));
      await nguoiTheoDoiApi.gan({ cong_chuc_id: chonNguoiId, don_vi_ids });
      const ten = nguoiTrongDonVi.find((c) => c.id === chonNguoiId)?.ho_ten || '';
      flash(`Đã gán ${ten} theo dõi ${donViMap[donViId]?.ten_don_vi || ''}`);
      setChonNguoiId(''); setNguoiSearch('');
      await load();
    } catch (e) { onErr(e); } finally { setSaving(false); }
  };

  // Gỡ 1 người khỏi đơn vị đang chọn (nếu hết đơn vị → gỡ hẳn role)
  const goKhoiDonVi = async (p: INguoiTheoDoi) => {
    if (!confirm(`Gỡ ${p.ho_ten} khỏi việc theo dõi ${donViMap[donViId]?.ten_don_vi || 'đơn vị này'}?`)) return;
    try {
      const conLai = p.don_vi_ids.filter((id) => id !== donViId);
      if (conLai.length > 0) await nguoiTheoDoiApi.capNhat(p.cong_chuc_id, { don_vi_ids: conLai });
      else await nguoiTheoDoiApi.go(p.cong_chuc_id);
      flash('Đã gỡ'); await load();
    } catch (e) { onErr(e); }
  };

  const goHan = async (p: INguoiTheoDoi) => {
    if (!confirm(`Gỡ ${p.ho_ten} khỏi vai trò theo dõi chỉ tiêu (tất cả đơn vị)?`)) return;
    try { await nguoiTheoDoiApi.go(p.cong_chuc_id); flash('Đã gỡ'); await load(); }
    catch (e) { onErr(e); }
  };

  // Người có thể thêm: chưa theo dõi đơn vị này, + lọc theo từ khóa tìm
  const optionNguoi = useMemo(() => {
    const q = nguoiSearch.trim().toLowerCase();
    return nguoiTrongDonVi
      .filter((c) => !dangTheoDoiIds.has(c.id))
      .filter((c) => !q || (c.ho_ten || '').toLowerCase().includes(q) || (c.ma_cc || '').toLowerCase().includes(q));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nguoiTrongDonVi, nguoiSearch, list, donViId]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6">
          <Link href="/chi-tieu" className="text-sm text-blue-600 hover:underline">← Chỉ tiêu đơn vị</Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">Quản lý người theo dõi</h1>
          <p className="text-sm text-gray-500 mt-1">Chọn đơn vị, rồi gán người theo dõi chỉ tiêu cho đơn vị đó</p>
        </div>

        {err && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{err}</div>}
        {msg && <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm">{msg}</div>}

        {/* Bước 1: chọn đơn vị */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          <label className="block text-sm font-semibold text-gray-900 mb-2">1. Chọn đơn vị</label>
          <select className="w-full sm:w-[420px] border rounded-lg px-3 py-2 text-sm"
            value={donViId} onChange={(e) => setDonViId(e.target.value)}>
            <option value="">-- Chọn đơn vị cần gán người theo dõi --</option>
            {donVis.map((dv) => <option key={dv.id} value={dv.id}>{dv.ma_don_vi} — {dv.ten_don_vi}</option>)}
          </select>

          {donViId && (
            <div className="mt-5 space-y-5">
              {/* Người đang theo dõi đơn vị này */}
              <div>
                <div className="text-sm font-semibold text-gray-900 mb-2">Người đang theo dõi đơn vị này</div>
                {nguoiDangTheoDoi.length === 0 ? (
                  <div className="text-sm text-gray-400 italic">Chưa có ai theo dõi đơn vị này.</div>
                ) : (
                  <div className="space-y-2">
                    {nguoiDangTheoDoi.map((p) => (
                      <div key={p.cong_chuc_id} className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
                        <div className="text-sm">
                          <b>{p.ho_ten}</b> <span className="text-gray-400">({p.ma_cc})</span>
                          {p.don_vi_cong_chuc && <span className="text-gray-400"> · {p.don_vi_cong_chuc}</span>}
                          {p.don_vi_ids.length > 1 && (
                            <span className="text-xs text-blue-500 ml-2">+{p.don_vi_ids.length - 1} đơn vị khác</span>
                          )}
                        </div>
                        <button onClick={() => goKhoiDonVi(p)} className="text-xs text-red-500 hover:underline">Gỡ khỏi đơn vị</button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Bước 2: thêm người trong đơn vị */}
              <div className="pt-4 border-t border-gray-100">
                <label className="block text-sm font-semibold text-gray-900 mb-2">2. Thêm người theo dõi (chọn người trong đơn vị)</label>
                {loadingNguoi ? (
                  <div className="text-sm text-gray-400">Đang tải danh sách công chức...</div>
                ) : (
                  <>
                    <div className="flex gap-2 items-center mb-2">
                      <input className="flex-1 min-w-[220px] border rounded-lg px-3 py-2 text-sm"
                        placeholder="🔍 Tìm theo tên hoặc mã công chức..."
                        value={nguoiSearch} onChange={(e) => setNguoiSearch(e.target.value)} />
                      <button onClick={themNguoi} disabled={saving || !chonNguoiId}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium whitespace-nowrap">
                        {saving ? 'Đang lưu...' : 'Thêm'}
                      </button>
                    </div>
                    {nguoiTrongDonVi.filter((c) => !dangTheoDoiIds.has(c.id)).length === 0 ? (
                      <div className="text-xs text-gray-400">Tất cả công chức trong đơn vị đã được gán.</div>
                    ) : optionNguoi.length === 0 ? (
                      <div className="text-xs text-gray-400">Không tìm thấy công chức khớp “{nguoiSearch}”.</div>
                    ) : (
                      <div className="border rounded-lg divide-y max-h-60 overflow-y-auto">
                        {optionNguoi.map((c) => (
                          <button key={c.id} type="button" onClick={() => setChonNguoiId(c.id)}
                            className={`w-full text-left px-3 py-2 text-sm flex justify-between items-center ${chonNguoiId === c.id ? 'bg-blue-50' : 'hover:bg-gray-50'}`}>
                            <span>
                              <b>{c.ho_ten}</b> <span className="text-gray-400">({c.ma_cc})</span>
                              {c.chuc_vu ? <span className="text-gray-400"> — {c.chuc_vu}</span> : null}
                            </span>
                            {chonNguoiId === c.id && <span className="text-blue-600 text-xs font-medium">✓ Đã chọn</span>}
                          </button>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Tổng quan tất cả người theo dõi */}
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="px-5 py-3 border-b border-gray-100 font-semibold text-gray-900 text-sm">
            Tất cả người theo dõi {list.length > 0 && <span className="text-gray-400 font-normal">({list.length})</span>}
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
                    <td className="py-2 px-4 text-right">
                      <button onClick={() => goHan(it)} className="text-xs text-red-500 hover:underline">Gỡ hẳn</button>
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
