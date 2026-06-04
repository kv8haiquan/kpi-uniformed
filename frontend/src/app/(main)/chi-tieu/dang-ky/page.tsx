/**
 * src/app/(main)/chi-tieu/dang-ky/page.tsx
 * ========================================
 * Đăng ký chỉ tiêu đầu tháng + nhập kết quả cuối tháng (THEO_DOI_CHI_TIEU).
 * State-driven: mỗi chỉ tiêu hiển thị hành động theo trạng thái bản ghi.
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { dangKyApi, danhMucApi } from '@/services/chi-tieu';
import { adminService } from '@/services/admin.service';
import type { IChiTieu, IDongDangKy } from '@/types/chi-tieu';
import { TRANG_THAI_LABEL } from '@/types/chi-tieu';
import type { IDonViOption } from '@/types/admin';
import { useAuthStore } from '@/stores/useAuthStore';

const NAM_HIEN_TAI = new Date().getFullYear();
const THANG_HIEN_TAI = new Date().getMonth() + 1;

export default function DangKyPage() {
  const user = useAuthStore((s) => s.user);
  const [donVis, setDonVis] = useState<IDonViOption[]>([]);
  const [chiTieuMap, setChiTieuMap] = useState<Record<string, IChiTieu>>({});
  const [rows, setRows] = useState<IDongDangKy[]>([]);
  const [donViId, setDonViId] = useState('');
  const [thang, setThang] = useState(THANG_HIEN_TAI);
  const [nam, setNam] = useState(NAM_HIEN_TAI);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');
  const [msg, setMsg] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const [dvs, ctRes] = await Promise.all([adminService.getDonViList(), danhMucApi.danhSach()]);
        setDonVis(dvs);
        const map: Record<string, IChiTieu> = {};
        (ctRes.data.data || []).forEach((c: IChiTieu) => { map[c.id] = c; });
        setChiTieuMap(map);
        // mặc định đơn vị của user
        if (user?.don_vi?.id) setDonViId(user.don_vi.id);
      } catch (e: any) {
        setErr(e?.response?.data?.error?.message || 'Lỗi tải danh mục');
      }
    })();
  }, []);

  const load = async () => {
    if (!donViId) { setRows([]); return; }
    setLoading(true); setErr(''); setMsg('');
    try {
      const res = await dangKyApi.canDangKy({ don_vi_id: donViId, thang, nam });
      setRows(res.data.data || []);
    } catch (e: any) {
      setErr(e?.response?.data?.error?.message || 'Lỗi tải danh sách');
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [donViId, thang, nam]);

  const flash = (m: string) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };
  const onErr = (e: any) => setErr(e?.response?.data?.error?.message || 'Có lỗi xảy ra');

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6">
          <Link href="/chi-tieu" className="text-sm text-blue-600 hover:underline">← Chỉ tiêu đơn vị</Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">Đăng ký & kết quả tháng</h1>
        </div>

        {err && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{err}</div>}
        {msg && <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm">{msg}</div>}

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
            <label className="block text-xs text-gray-500 mb-1">Tháng</label>
            <select className="border rounded-lg px-3 py-2 text-sm w-24" value={thang} onChange={(e) => setThang(Number(e.target.value))}>
              {Array.from({ length: 12 }, (_, i) => i + 1).map((t) => <option key={t} value={t}>Tháng {t}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Năm</label>
            <input type="number" className="border rounded-lg px-3 py-2 text-sm w-28" value={nam} onChange={(e) => setNam(Number(e.target.value))} />
          </div>
        </div>

        {!donViId ? (
          <div className="text-center py-12 text-gray-500 text-sm">Chọn đơn vị để xem chỉ tiêu cần đăng ký.</div>
        ) : loading ? (
          <div className="p-8 text-center"><div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto" /></div>
        ) : rows.length === 0 ? (
          <div className="text-center py-12 text-gray-500 text-sm">
            Đơn vị chưa được giao chỉ tiêu năm {nam}. Liên hệ Quản trị chỉ tiêu.
          </div>
        ) : (
          <div className="space-y-3">
            {rows.map((row) => (
              <DongChiTieu key={`${row.chi_tieu_id}-${row.dang_ky?.trang_thai ?? 'none'}`} row={row} chiTieu={chiTieuMap[row.chi_tieu_id]}
                donViId={donViId} thang={thang} nam={nam}
                onReload={load} onFlash={flash} onErr={onErr} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// 1 dòng chỉ tiêu — state machine UI
// =============================================================================
function DongChiTieu({ row, chiTieu, donViId, thang, nam, onReload, onFlash, onErr }: {
  row: IDongDangKy; chiTieu?: IChiTieu; donViId: string; thang: number; nam: number;
  onReload: () => void; onFlash: (m: string) => void; onErr: (e: any) => void;
}) {
  const dk = row.dang_ky;
  const tt = dk?.trang_thai;
  const st = tt ? TRANG_THAI_LABEL[tt] : null;
  const [dangKy, setDangKy] = useState(dk?.gia_tri_dang_ky ?? '');
  const [khongDangKy, setKhongDangKy] = useState(dk?.khong_dang_ky ?? false);
  const [ketQua, setKetQua] = useState(dk?.gia_tri_ket_qua ?? '');
  const [ghiChu, setGhiChu] = useState(dk?.danh_gia_ghi_chu ?? '');
  const [busy, setBusy] = useState(false);

  const run = async (fn: () => Promise<any>, ok: string) => {
    setBusy(true);
    try { await fn(); onFlash(ok); onReload(); }
    catch (e) { onErr(e); } finally { setBusy(false); }
  };

  const luuDangKy = () => run(async () => {
    const payload = { khong_dang_ky: khongDangKy, gia_tri_dang_ky: khongDangKy ? null : Number(dangKy) };
    if (dk) await dangKyApi.capNhat(dk.id, payload);
    else await dangKyApi.taoMoi({ don_vi_id: donViId, chi_tieu_id: row.chi_tieu_id, thang, nam, ...payload });
  }, 'Đã lưu đăng ký');

  const editable = !dk || tt === 'NHAP';
  const choNhapKetQua = tt === 'DA_DUYET_DANG_KY';

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <div className="font-medium text-gray-900">{chiTieu?.ten_chi_tieu || row.chi_tieu_id}</div>
          <div className="text-xs text-gray-500 mt-0.5">
            {chiTieu && <span className="font-mono">{chiTieu.ma_chi_tieu}</span>}
            {chiTieu && <span> · ĐVT: {chiTieu.don_vi_tinh}</span>}
            {row.muc_giao.map((m) => (
              <span key={m.loai_muc} className="ml-2">
                {m.loai_muc === 'PHAP_LENH' ? 'PL' : 'PĐ'}: <b>{m.gia_tri_giao}</b>
              </span>
            ))}
          </div>
        </div>
        {st && <span className={`text-xs px-2 py-1 rounded-full ${st.bg} ${st.text} whitespace-nowrap`}>{st.label}</span>}
      </div>

      {dk?.ly_do_tu_choi && (
        <div className="mb-2 text-xs text-red-600 bg-red-50 rounded px-2 py-1">Bị từ chối: {dk.ly_do_tu_choi}</div>
      )}

      {/* Khối đăng ký */}
      <div className="flex flex-wrap items-end gap-2">
        <label className="flex items-center gap-1.5 text-sm text-gray-700">
          <input type="checkbox" disabled={!editable} checked={khongDangKy}
            onChange={(e) => setKhongDangKy(e.target.checked)} />
          Không đăng ký
        </label>
        {!khongDangKy && (
          <div>
            <label className="block text-xs text-gray-500 mb-0.5">Giá trị đăng ký</label>
            <input type="number" step="0.001" disabled={!editable}
              className="border rounded-lg px-3 py-1.5 text-sm w-36 disabled:bg-gray-50"
              value={dangKy} onChange={(e) => setDangKy(e.target.value)} />
          </div>
        )}
        {editable && (
          <>
            <button disabled={busy} onClick={luuDangKy}
              className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm">Lưu</button>
            {dk && (
              <button disabled={busy} onClick={() => run(() => dangKyApi.guiDuyet(dk.id), 'Đã gửi duyệt đăng ký')}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm">Gửi duyệt</button>
            )}
          </>
        )}
      </div>

      {/* Khối kết quả — khi đăng ký đã duyệt */}
      {choNhapKetQua && (
        <div className="mt-3 pt-3 border-t border-gray-100 flex flex-wrap items-end gap-2">
          <div>
            <label className="block text-xs text-gray-500 mb-0.5">Kết quả thực hiện</label>
            <input type="number" step="0.001" className="border rounded-lg px-3 py-1.5 text-sm w-36"
              value={ketQua} onChange={(e) => setKetQua(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-0.5">Ghi chú đánh giá</label>
            <input className="border rounded-lg px-3 py-1.5 text-sm w-48" placeholder='vd "Vượt chỉ tiêu"'
              value={ghiChu} onChange={(e) => setGhiChu(e.target.value)} />
          </div>
          <button disabled={busy} onClick={() => run(
            () => dangKyApi.nhapKetQua(dk!.id, { gia_tri_ket_qua: Number(ketQua), danh_gia_ghi_chu: ghiChu || undefined }),
            'Đã lưu kết quả')}
            className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm">Lưu KQ</button>
          <button disabled={busy || !ketQua} onClick={() => run(() => dangKyApi.guiKetQua(dk!.id), 'Đã gửi duyệt kết quả')}
            className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm">Gửi kết quả</button>
        </div>
      )}

      {/* Hiển thị khi đã chốt */}
      {tt === 'DA_DUYET_KET_QUA' && (
        <div className="mt-2 text-sm text-gray-700">
          Kết quả: <b>{dk?.gia_tri_ket_qua}</b>
          {dk?.danh_gia_tu_dong && <span className="ml-2 text-green-700">· {dk.danh_gia_tu_dong}</span>}
          {dk?.danh_gia_ghi_chu && <span className="ml-2 text-gray-500">({dk.danh_gia_ghi_chu})</span>}
        </div>
      )}
    </div>
  );
}
