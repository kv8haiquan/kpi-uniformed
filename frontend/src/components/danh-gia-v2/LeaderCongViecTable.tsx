/**
 * src/components/danh-gia-v2/LeaderCongViecTable.tsx
 * ==================================================
 * Bảng chi tiết CV trong scope KPI của LĐ (Yêu cầu 1, 06/05/2026).
 *
 * Hiển thị toàn bộ CV trong scope (LĐ tự kê + CV cấp dưới do mình duyệt /
 * thuộc đơn vị mình phụ trách). Có filter "Tất cả / Tự làm / Cấp dưới".
 */

'use client';

import { useEffect, useMemo, useState } from 'react';
import { kpiLanhDaoV2Service } from '@/services/kpiLanhDaoV2.service';
import { ICongViecLanhDaoV2 } from '@/types/kpiLanhDaoV2';
import DieuChinhKqcvModal from './DieuChinhKqcvModal';

interface Props {
  thang: number;
  nam: number;
  tamTinh: boolean;
}

const LOAI_LABEL: Record<string, string> = {
  TU_LAM: 'Tự làm',
  CAP_DUOI: 'Cấp dưới',
};

const TRANG_THAI_BADGE: Record<string, string> = {
  NHAP: 'bg-gray-100 text-gray-700',
  CHO_PHE_DUYET: 'bg-yellow-100 text-yellow-800',
  DA_PHE_DUYET: 'bg-green-100 text-green-800',
  TU_CHOI: 'bg-red-100 text-red-800',
  HUY: 'bg-gray-200 text-gray-500',
};
const TRANG_THAI_LABEL: Record<string, string> = {
  NHAP: 'Nháp',
  CHO_PHE_DUYET: 'Chờ duyệt',
  DA_PHE_DUYET: 'Đã duyệt',
  TU_CHOI: 'Từ chối',
  HUY: 'Hủy',
};

export default function LeaderCongViecTable({ thang, nam, tamTinh }: Props) {
  const [items, setItems] = useState<ICongViecLanhDaoV2[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'tu_lam' | 'cap_duoi'>('all');
  const [filterCcId, setFilterCcId] = useState<string>(''); // '' = tất cả
  const [editing, setEditing] = useState<ICongViecLanhDaoV2 | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    kpiLanhDaoV2Service
      .getMyCongViec(thang, nam, tamTinh, filter)
      .then((d) => { if (!cancelled) setItems(d); })
      .catch((e) => {
        if (cancelled) return;
        const msg = e?.response?.data?.detail?.error?.message ?? 'Không tải được danh sách';
        setError(msg);
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [thang, nam, tamTinh, filter, reloadKey]);

  // Danh sách CC distinct trong items (cho dropdown filter)
  const ccOptions = useMemo(() => {
    const map = new Map<string, { id: string; ho_ten: string; ma_cc: string; count: number }>();
    for (const it of items) {
      const ex = map.get(it.cong_chuc_id);
      if (ex) ex.count += 1;
      else map.set(it.cong_chuc_id, { id: it.cong_chuc_id, ho_ten: it.ho_ten, ma_cc: it.ma_cc, count: 1 });
    }
    return Array.from(map.values()).sort((a, b) => a.ho_ten.localeCompare(b.ho_ten, 'vi'));
  }, [items]);

  // Items sau khi filter theo CC (client-side)
  const displayItems = useMemo(() => {
    if (!filterCcId) return items;
    return items.filter((it) => it.cong_chuc_id === filterCcId);
  }, [items, filterCcId]);

  const totals = useMemo(() => {
    const t = { sp_goc: 0, sp_cl: 0, sp_td: 0 };
    for (const it of displayItems) {
      t.sp_goc += it.so_sp_goc_quy_doi;
      t.sp_cl += it.sp_chat_luong;
      t.sp_td += it.sp_tien_do;
    }
    return t;
  }, [displayItems]);

  const fmt = (n: number) => n.toFixed(6).replace(/\.?0+$/, '');

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200 space-y-3">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <h2 className="text-base font-medium text-gray-900">
              Chi tiết công việc trong scope KPI{' '}
              <span className="text-sm font-normal text-gray-500">
                ({displayItems.length}
                {filterCcId && items.length !== displayItems.length ? ` / ${items.length}` : ''})
              </span>
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Tổng điểm gốc: <b>{fmt(totals.sp_goc)}</b> · CL: <b>{fmt(totals.sp_cl)}</b> · TĐ: <b>{fmt(totals.sp_td)}</b>
            </p>
          </div>

          {/* Filter Loại */}
          <div className="flex gap-1 bg-gray-100 rounded-lg p-1 text-sm">
            {(['all', 'tu_lam', 'cap_duoi'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                  filter === f ? 'bg-white shadow text-gray-900' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {f === 'all' ? 'Tất cả' : f === 'tu_lam' ? 'Tự làm' : 'Cấp dưới'}
              </button>
            ))}
          </div>
        </div>

        {/* Filter Công chức (chỉ hiển thị khi có ≥ 2 CC khác nhau) */}
        {ccOptions.length >= 2 && (
          <div className="flex items-center gap-2 text-sm">
            <label className="text-xs font-medium text-gray-600 whitespace-nowrap">
              Lọc theo công chức:
            </label>
            <select
              value={filterCcId}
              onChange={(e) => setFilterCcId(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1 text-sm flex-1 max-w-md"
            >
              <option value="">— Tất cả ({ccOptions.length} người · {items.length} CV) —</option>
              {ccOptions.map((cc) => (
                <option key={cc.id} value={cc.id}>
                  {cc.ho_ten} ({cc.ma_cc}) — {cc.count} CV
                </option>
              ))}
            </select>
            {filterCcId && (
              <button
                onClick={() => setFilterCcId('')}
                className="text-xs text-blue-600 hover:text-blue-800 hover:underline whitespace-nowrap"
              >
                Bỏ lọc
              </button>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="m-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="p-8 text-center text-sm text-gray-500">Đang tải...</div>
      ) : displayItems.length === 0 ? (
        <div className="p-8 text-center text-sm text-gray-500">
          {items.length === 0 ? 'Không có công việc trong scope' : 'Không có CV cho công chức đã chọn'}
        </div>
      ) : (
        <div className="overflow-x-auto max-h-[600px]">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Loại</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Người kê khai</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Mã CV</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Công việc</th>
                <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Ngày</th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">SL</th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Điểm gốc</th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Điểm CL</th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Điểm TĐ</th>
                <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Lỗi</th>
                <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Trạng thái</th>
                <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Hành động</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {displayItems.map((it) => {
                const loiCl = (it.trang_thai === 'DA_PHE_DUYET' ? it.so_loi_chat_luong : it.tu_danh_gia_chat_luong) || 0;
                const loiTd = (it.trang_thai === 'DA_PHE_DUYET' ? it.so_loi_tien_do : it.tu_danh_gia_tien_do) || 0;
                const hasErr = loiCl > 0 || loiTd > 0;
                return (
                  <tr key={it.ke_khai_id} className="hover:bg-gray-50">
                    <td className="px-3 py-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        it.loai === 'TU_LAM' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'
                      }`}>
                        {LOAI_LABEL[it.loai]}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <div className="text-gray-900 flex items-center gap-1.5">
                        {it.ho_ten}
                        {it.co_dieu_chinh && (
                          <span
                            className="text-[10px] px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded font-medium"
                            title={`LĐ đã điều chỉnh — giá trị gốc của CC: CL ${it.so_loi_chat_luong_goc} / TĐ ${it.so_loi_tien_do_goc}. Chỉ ảnh hưởng KPI LĐ, KHÔNG đụng KPI CC.`}
                          >
                            ✎ Đã ĐC
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-gray-500">{it.ma_cc}</div>
                    </td>
                    <td className="px-3 py-2 text-xs font-mono text-gray-600">{it.ma_danh_muc || '—'}</td>
                    <td className="px-3 py-2 max-w-md">
                      <div className="text-sm text-gray-900 truncate" title={it.ten_cong_viec ?? ''}>
                        {it.ten_cong_viec || '—'}
                      </div>
                      {(it.linh_vuc || it.nhom_pl3) && (
                        <div className="text-xs text-gray-500">
                          {it.linh_vuc && `${it.linh_vuc} · `}
                          {it.nhom_pl3 && `Nhóm ${it.nhom_pl3}`}
                        </div>
                      )}
                    </td>
                    <td className="px-3 py-2 text-center text-xs whitespace-nowrap">
                      {it.ngay_thuc_hien
                        ? it.ngay_thuc_hien.split('-').reverse().join('/')
                        : '—'}
                    </td>
                    <td className="px-3 py-2 text-right">{it.so_luong}</td>
                    <td className="px-3 py-2 text-right font-medium">{fmt(it.so_sp_goc_quy_doi)}</td>
                    <td className="px-3 py-2 text-right">{fmt(it.sp_chat_luong)}</td>
                    <td className="px-3 py-2 text-right">{fmt(it.sp_tien_do)}</td>
                    <td className="px-3 py-2 text-center">
                      {hasErr ? (
                        <span className="inline-flex items-center gap-0.5 text-xs">
                          {loiCl > 0 && <span className="bg-red-100 text-red-700 px-1.5 py-0.5 rounded">CL:{loiCl}</span>}
                          {loiTd > 0 && <span className="bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded">TĐ:{loiTd}</span>}
                        </span>
                      ) : (
                        <span className="text-gray-300 text-xs">—</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-center">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${TRANG_THAI_BADGE[it.trang_thai] ?? 'bg-gray-100'}`}>
                        {TRANG_THAI_LABEL[it.trang_thai] ?? it.trang_thai}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-center">
                      {it.trang_thai === 'DA_PHE_DUYET' && it.loai === 'CAP_DUOI' ? (
                        <button
                          onClick={() => setEditing(it)}
                          className="text-blue-600 hover:text-blue-800 text-xs font-medium"
                        >
                          Sửa
                        </button>
                      ) : (
                        <span className="text-gray-300 text-xs">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <DieuChinhKqcvModal
        open={editing !== null}
        cv={editing}
        onClose={() => setEditing(null)}
        onSuccess={() => setReloadKey((k) => k + 1)}
      />
    </div>
  );
}
