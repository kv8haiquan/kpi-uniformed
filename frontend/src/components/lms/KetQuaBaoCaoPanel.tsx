/**
 * src/components/lms/KetQuaBaoCaoPanel.tsx
 * ==========================================
 * Panel kết quả thi & báo cáo — 3 sub-tabs:
 *   1. Theo khóa học — Xem điểm thi, cờ vi phạm
 *   2. Theo đơn vị    — Báo cáo đơn vị (copy từ BaoCaoPanel)
 *   3. Khảo sát       — Thống kê khảo sát (copy từ BaoCaoPanel)
 */

'use client';

import { useEffect, useState } from 'react';
import { baoCaoApi, khaoSatApi, cbccApi, khoaHocApi, baiKiemTraApi } from '@/services/lms';

type SubTab = 'theo-khoa-hoc' | 'don-vi' | 'khao-sat';

interface DonViItem { id: string; ma_don_vi: string; ten_don_vi: string }
interface KhoaHocItem { id: string; ma_khoa_hoc: string; ten_khoa_hoc: string }

export default function KetQuaBaoCaoPanel() {
  const [tab, setTab] = useState<SubTab>('theo-khoa-hoc');

  // Danh sách tra cứu (load 1 lần)
  const [donVis, setDonVis] = useState<DonViItem[]>([]);
  const [khoaHocs, setKhoaHocs] = useState<KhoaHocItem[]>([]);

  useEffect(() => {
    cbccApi.getDonVi().then((r) => setDonVis(r.data.data || [])).catch(() => {});
    khoaHocApi.quanLy({ page_size: 100 }).then((r) => setKhoaHocs(r.data.data || [])).catch(() => {});
  }, []);

  // ─── Sub-tab 1: Theo khóa học ───────────────────────────────────
  const [selKhoaHocId, setSelKhoaHocId] = useState('');
  const [selBktId, setSelBktId] = useState('');
  const [bktList, setBktList] = useState<any[]>([]);
  const [ketQuaList, setKetQuaList] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [bcKH, setBcKH] = useState<any>(null);

  // Load bai_kiem_tra khi chọn khóa học
  useEffect(() => {
    if (!selKhoaHocId) { setBktList([]); setSelBktId(''); setKetQuaList([]); setBcKH(null); return; }
    baiKiemTraApi.danhSach(selKhoaHocId).then(r => setBktList(r.data.data || [])).catch(() => setBktList([]));
    // Load course report
    baoCaoApi.khoaHoc(selKhoaHocId).then(r => setBcKH(r.data.data ?? r.data)).catch(() => setBcKH(null));
  }, [selKhoaHocId]);

  // Load kết quả thi khi chọn BKT
  const loadKetQua = async () => {
    if (!selBktId) return;
    setLoading(true);
    try {
      const r = await baiKiemTraApi.ketQuaTatCa(selBktId);
      setKetQuaList(r.data.data || []);
    } catch {
      setKetQuaList([]);
    } finally {
      setLoading(false);
    }
  };

  // ─── Sub-tab 2: Báo cáo đơn vị ──────────────────────────────────
  const [selDonVi, setSelDonVi] = useState('');
  const now = new Date();
  const [thang, setThang] = useState(now.getMonth() + 1);
  const [nam, setNam] = useState(now.getFullYear());
  const [bcDonVi, setBcDonVi] = useState<any>(null);
  const [loadingDV, setLoadingDV] = useState(false);
  const [errDV, setErrDV] = useState('');

  const loadBcDonVi = async () => {
    if (!selDonVi) return;
    setLoadingDV(true);
    setErrDV('');
    setBcDonVi(null);
    try {
      const r = await baoCaoApi.donVi(selDonVi, { thang, nam });
      setBcDonVi(r.data.data ?? r.data);
    } catch (err: any) {
      setErrDV(err?.response?.data?.detail?.error?.message || 'Không thể tải báo cáo');
    } finally {
      setLoadingDV(false);
    }
  };

  // ─── Sub-tab 3: Thống kê khảo sát ───────────────────────────────
  const [selKHKS, setSelKHKS] = useState('');
  const [bcKS, setBcKS] = useState<any>(null);
  const [loadingKS, setLoadingKS] = useState(false);
  const [errKS, setErrKS] = useState('');

  const loadBcKS = async () => {
    if (!selKHKS) return;
    setLoadingKS(true);
    setErrKS('');
    setBcKS(null);
    try {
      const r = await khaoSatApi.thongKe(selKHKS);
      setBcKS(r.data.data ?? r.data);
    } catch (err: any) {
      setErrKS(err?.response?.data?.detail?.error?.message || 'Không thể tải thống kê');
    } finally {
      setLoadingKS(false);
    }
  };

  // ─── Render ─────────────────────────────────────────────────────
  return (
    <div>
      {/* Sub-tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1">
        {([
          ['theo-khoa-hoc', '📊 Theo khóa học'],
          ['don-vi',        '🏢 Theo đơn vị'],
          ['khao-sat',      '⭐ Khảo sát'],
        ] as [SubTab, string][]).map(([k, label]) => (
          <button key={k} onClick={() => setTab(k)}
            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              tab === k ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'
            }`}>
            {label}
          </button>
        ))}
      </div>

      {/* ── Tab: Theo khóa học ──────────────────────────────── */}
      {tab === 'theo-khoa-hoc' && (
        <div className="space-y-4">
          {/* Bộ lọc */}
          <div className="flex flex-wrap gap-3">
            <select value={selKhoaHocId} onChange={(e) => { setSelKhoaHocId(e.target.value); setSelBktId(''); setKetQuaList([]); }}
              className="flex-1 min-w-[200px] px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white">
              <option value="">-- Chọn khóa học --</option>
              {khoaHocs.map(kh => <option key={kh.id} value={kh.id}>[{kh.ma_khoa_hoc}] {kh.ten_khoa_hoc}</option>)}
            </select>
            <select value={selBktId} onChange={(e) => setSelBktId(e.target.value)}
              className="flex-1 min-w-[200px] px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
              disabled={!selKhoaHocId}>
              <option value="">-- Chọn bài kiểm tra --</option>
              {bktList.map(bkt => <option key={bkt.id} value={bkt.id}>{bkt.tieu_de} ({bkt.so_cau_hoi} câu)</option>)}
            </select>
            <button onClick={loadKetQua} disabled={!selBktId || loading}
              className="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-blue-700">
              {loading ? 'Đang tải...' : 'Xem kết quả'}
            </button>
          </div>

          {/* Course summary cards (if course selected) */}
          {bcKH && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-white border rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-gray-900">{bcKH.tong_hoc_vien ?? bcKH.so_hoc_vien ?? 0}</div>
                <div className="text-xs text-gray-500">Tổng học viên</div>
              </div>
              <div className="bg-white border rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-blue-600">{bcKH.dang_hoc ?? 0}</div>
                <div className="text-xs text-gray-500">Đang học</div>
              </div>
              <div className="bg-white border rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-green-600">{bcKH.hoan_thanh ?? 0}</div>
                <div className="text-xs text-gray-500">Hoàn thành</div>
              </div>
              <div className="bg-white border rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-purple-600">{bcKH.ty_le_hoan_thanh != null ? `${bcKH.ty_le_hoan_thanh}%` : '—'}</div>
                <div className="text-xs text-gray-500">Tỷ lệ HT</div>
              </div>
            </div>
          )}

          {/* Results table */}
          {ketQuaList.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b bg-gray-50 flex items-center justify-between">
                <h4 className="font-medium text-sm text-gray-700">Kết quả thi ({ketQuaList.length} lượt)</h4>
                {ketQuaList.some(kq => (kq.so_lan_vi_pham || 0) > 0) && (
                  <span className="px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium">
                    🚩 {ketQuaList.filter(kq => (kq.so_lan_vi_pham || 0) > 0).length} bài bị gắn cờ
                  </span>
                )}
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium text-gray-500">Họ tên</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-500">Mã CC</th>
                      <th className="px-4 py-3 text-center font-medium text-gray-500">Lần thi</th>
                      <th className="px-4 py-3 text-center font-medium text-gray-500">Điểm</th>
                      <th className="px-4 py-3 text-center font-medium text-gray-500">Kết quả</th>
                      <th className="px-4 py-3 text-center font-medium text-gray-500">Vi phạm</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-500">Ngày thi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {ketQuaList.map((kq, i) => {
                      const hasViolation = (kq.so_lan_vi_pham || 0) > 0;
                      return (
                        <tr key={i} className={`hover:bg-gray-50 ${hasViolation ? 'bg-red-50' : ''}`}>
                          <td className="px-4 py-3 font-medium text-gray-900">{kq.ho_ten || '—'}</td>
                          <td className="px-4 py-3 text-gray-600">{kq.ma_cc || '—'}</td>
                          <td className="px-4 py-3 text-center">{kq.lan_thu}</td>
                          <td className="px-4 py-3 text-center font-semibold">{kq.diem ?? '—'}</td>
                          <td className="px-4 py-3 text-center">
                            {kq.dat_yeu_cau === true && <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs">Đạt</span>}
                            {kq.dat_yeu_cau === false && <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs">Chưa đạt</span>}
                            {kq.dat_yeu_cau == null && <span className="text-gray-400 text-xs">Đang thi</span>}
                          </td>
                          <td className="px-4 py-3 text-center">
                            {hasViolation ? (
                              <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs font-medium">
                                🚩 {kq.so_lan_vi_pham}
                              </span>
                            ) : (
                              <span className="text-green-600 text-xs">✓</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-gray-500 text-xs">
                            {kq.ngay_lam ? new Date(kq.ngay_lam).toLocaleString('vi-VN') : '—'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Empty state */}
          {selBktId && !loading && ketQuaList.length === 0 && (
            <div className="text-center py-10 bg-gray-50 rounded-lg text-gray-500 text-sm">
              Chưa có kết quả thi nào cho bài kiểm tra này
            </div>
          )}
        </div>
      )}

      {/* ── Tab: Báo cáo đơn vị ─────────────────────────────── */}
      {tab === 'don-vi' && (
        <div className="space-y-4">
          {/* Bộ lọc */}
          <div className="flex flex-wrap gap-3">
            <select value={selDonVi} onChange={(e) => setSelDonVi(e.target.value)}
              className="flex-1 min-w-[220px] px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white">
              <option value="">-- Chọn đơn vị --</option>
              {donVis.map((dv) => (
                <option key={dv.id} value={dv.id}>{dv.ten_don_vi}</option>
              ))}
            </select>
            <select value={thang} onChange={(e) => setThang(+e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white">
              {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                <option key={m} value={m}>Tháng {m}</option>
              ))}
            </select>
            <input type="number" value={nam} onChange={(e) => setNam(+e.target.value)}
              min={2024} max={2030}
              className="w-24 px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            <button onClick={loadBcDonVi} disabled={!selDonVi || loadingDV}
              className="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-blue-700">
              {loadingDV ? 'Đang tải...' : 'Xem báo cáo'}
            </button>
          </div>

          {errDV && <p className="text-sm text-red-600">{errDV}</p>}

          {bcDonVi && (
            <div className="space-y-4">
              {/* Stat cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: 'Tổng CBCC',     value: bcDonVi.tong_cbcc,                    color: 'text-gray-900' },
                  { label: 'Đang học',       value: bcDonVi.thong_ke?.dang_hoc,           color: 'text-blue-600' },
                  { label: 'Hoàn thành',     value: bcDonVi.thong_ke?.hoan_thanh_thang,   color: 'text-green-600' },
                  { label: 'Quá hạn',        value: bcDonVi.thong_ke?.qua_han,            color: 'text-red-600' },
                ].map((s, i) => (
                  <div key={i} className="bg-white border border-gray-200 rounded-lg p-4 text-center">
                    <div className={`text-3xl font-bold ${s.color}`}>{s.value ?? 0}</div>
                    <div className="text-xs text-gray-500 mt-1">{s.label}</div>
                  </div>
                ))}
              </div>

              {/* Bảng chi tiết CBCC */}
              {Array.isArray(bcDonVi.chi_tiet_cbcc) && bcDonVi.chi_tiet_cbcc.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                  <div className="px-4 py-3 border-b bg-gray-50">
                    <h4 className="font-medium text-sm text-gray-700">Chi tiết từng CBCC</h4>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="border-b">
                        <tr>
                          <th className="px-4 py-3 text-left font-medium text-gray-500">Họ tên</th>
                          <th className="px-4 py-3 text-center font-medium text-gray-500">Đang học</th>
                          <th className="px-4 py-3 text-center font-medium text-gray-500">Hoàn thành</th>
                          <th className="px-4 py-3 text-center font-medium text-gray-500">Điểm TB</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {bcDonVi.chi_tiet_cbcc.map((row: any, i: number) => (
                          <tr key={i} className="hover:bg-gray-50">
                            <td className="px-4 py-3 font-medium text-gray-900">
                              {row.cong_chuc?.ho_ten ?? row.ho_ten ?? '—'}
                            </td>
                            <td className="px-4 py-3 text-center text-gray-600">{row.khoa_dang_hoc ?? 0}</td>
                            <td className="px-4 py-3 text-center text-gray-600">{row.khoa_hoan_thanh ?? 0}</td>
                            <td className="px-4 py-3 text-center">
                              {row.diem_tb != null ? `${row.diem_tb}%` : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Tab: Thống kê khảo sát ──────────────────────────── */}
      {tab === 'khao-sat' && (
        <div className="space-y-4">
          <div className="flex gap-3">
            <select value={selKHKS} onChange={(e) => setSelKHKS(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white">
              <option value="">-- Chọn khóa học --</option>
              {khoaHocs.map((kh) => (
                <option key={kh.id} value={kh.id}>[{kh.ma_khoa_hoc}] {kh.ten_khoa_hoc}</option>
              ))}
            </select>
            <button onClick={loadBcKS} disabled={!selKHKS || loadingKS}
              className="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-blue-700">
              {loadingKS ? 'Đang tải...' : 'Xem'}
            </button>
          </div>

          {errKS && <p className="text-sm text-red-600">{errKS}</p>}

          {bcKS && (
            <div className="space-y-4">
              {/* Tổng quan */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white border border-gray-200 rounded-lg p-5 text-center">
                  <div className="text-4xl font-bold text-yellow-500">
                    {bcKS.rating_trung_binh != null ? Number(bcKS.rating_trung_binh).toFixed(1) : '—'}
                  </div>
                  <div className="flex justify-center gap-0.5 mt-2">
                    {[1, 2, 3, 4, 5].map((s) => (
                      <span key={s} className={
                        s <= Math.round(bcKS.rating_trung_binh || 0) ? 'text-yellow-400 text-lg' : 'text-gray-200 text-lg'
                      }>⭐</span>
                    ))}
                  </div>
                  <div className="text-xs text-gray-500 mt-2">Điểm trung bình</div>
                </div>
                <div className="bg-white border border-gray-200 rounded-lg p-5 text-center">
                  <div className="text-4xl font-bold text-gray-900">{bcKS.tong_phan_hoi ?? 0}</div>
                  <div className="text-xs text-gray-500 mt-2">Tổng phản hồi</div>
                </div>
              </div>

              {/* Phân bố đánh giá */}
              {bcKS.phan_bo_rating && (
                <div className="bg-white border border-gray-200 rounded-xl p-5">
                  <h4 className="text-sm font-semibold text-gray-700 mb-4">Phân bố đánh giá</h4>
                  {[5, 4, 3, 2, 1].map((s) => {
                    const count = bcKS.phan_bo_rating[s] ?? bcKS.phan_bo_rating[String(s)] ?? 0;
                    const total = bcKS.tong_phan_hoi || 1;
                    const pct = Math.round((count / total) * 100);
                    return (
                      <div key={s} className="flex items-center gap-3 mb-2">
                        <span className="text-xs text-gray-500 w-8 text-right">{s} ⭐</span>
                        <div className="flex-1 bg-gray-100 rounded-full h-2.5">
                          <div
                            className="bg-yellow-400 h-2.5 rounded-full transition-all"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500 w-8">{count}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
