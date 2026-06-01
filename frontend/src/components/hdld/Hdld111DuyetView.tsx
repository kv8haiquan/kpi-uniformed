/**
 * src/components/hdld/Hdld111DuyetView.tsx
 * ========================================
 * View cấp quản lý (TDV/PDV) duyệt đánh giá HĐLĐ 111 theo VB714.
 *
 * Hiển thị 2 cột điểm (tự đánh giá / cấp quản lý). Cấp quản lý nhập cột của mình;
 * nếu sửa khác điểm tự chấm phải ghi lý do. Có nút Duyệt và Trả lại.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import hdldService from '@/services/hdld.service';
import {
  IHdldDanhGia,
  HDLD_NHOM_LABEL,
  HdldNhom,
  getHdldErrorMessage,
} from '@/types/hdld';

interface Props {
  thang: number;
  nam: number;
}

interface DuyetInput {
  so_tt: number;
  diem_ql: string;
  ghi_chu_ql: string;
  ly_do_sua: string;
}

export default function Hdld111DuyetView({ thang, nam }: Props) {
  const [loading, setLoading] = useState(true);
  const [list, setList] = useState<IHdldDanhGia[]>([]);
  const [selected, setSelected] = useState<IHdldDanhGia | null>(null);
  const [inputs, setInputs] = useState<DuyetInput[]>([]);
  const [ghiChu, setGhiChu] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await hdldService.getChoDuyet(thang, nam);
      setList(data);
    } catch {
      setList([]);
    } finally {
      setLoading(false);
    }
  }, [thang, nam]);

  useEffect(() => { load(); }, [load]);

  const openDetail = (dg: IHdldDanhGia) => {
    setSelected(dg);
    setError(null);
    setGhiChu(dg.ghi_chu || '');
    setInputs(
      [...dg.chi_tiets]
        .sort((a, b) => a.so_tt - b.so_tt)
        .map((ct) => ({
          so_tt: ct.so_tt,
          // mặc định lấy điểm tự chấm để cấp QL chỉnh
          diem_ql: ct.diem_ql != null ? String(ct.diem_ql) : (ct.diem_tu != null ? String(ct.diem_tu) : ''),
          ghi_chu_ql: ct.ghi_chu_ql || '',
          ly_do_sua: ct.ly_do_sua || '',
        }))
    );
  };

  const updateInput = (so_tt: number, field: keyof DuyetInput, val: string) => {
    setInputs((prev) => prev.map((p) => (p.so_tt === so_tt ? { ...p, [field]: val } : p)));
  };

  const tbQl = (() => {
    const vals = inputs.map((i) => parseFloat(i.diem_ql)).filter((v) => !isNaN(v));
    if (vals.length !== 3) return null;
    return (vals.reduce((a, b) => a + b, 0) / 3).toFixed(2);
  })();

  const validate = (): string | null => {
    if (!selected) return 'Chưa chọn bản đánh giá';
    if (inputs.length !== 3) return 'Phải chấm đủ 3 tiêu chí';
    for (const i of inputs) {
      const d = parseFloat(i.diem_ql);
      if (isNaN(d) || d < 0 || d > 100) return `Tiêu chí ${i.so_tt}: điểm phải 0–100`;
      const ctTu = selected.chi_tiets.find((c) => c.so_tt === i.so_tt)?.diem_tu;
      if (ctTu != null && d !== Number(ctTu) && !i.ly_do_sua.trim()) {
        return `Tiêu chí ${i.so_tt}: sửa khác điểm tự chấm (${ctTu}%) phải ghi lý do`;
      }
    }
    return null;
  };

  const handleDuyet = async () => {
    const err = validate();
    if (err) { setError(err); return; }
    if (!selected) return;
    if (!confirm('Xác nhận duyệt đánh giá này?')) return;
    setSaving(true);
    setError(null);
    try {
      await hdldService.duyet(selected.id, {
        chi_tiets: inputs.map((i) => ({
          so_tt: i.so_tt,
          diem_ql: parseFloat(i.diem_ql),
          ghi_chu_ql: i.ghi_chu_ql.trim() || null,
          ly_do_sua: i.ly_do_sua.trim() || null,
        })),
        ghi_chu: ghiChu.trim() || null,
      });
      alert('✅ Đã duyệt');
      setSelected(null);
      await load();
    } catch (e: unknown) {
      setError(getHdldErrorMessage(e, 'Lỗi duyệt'));
    } finally {
      setSaving(false);
    }
  };

  const handleTraLai = async () => {
    if (!selected) return;
    const lyDo = prompt('Nhập lý do trả lại:');
    if (lyDo == null) return;
    if (!lyDo.trim()) { setError('Lý do trả lại không được trống'); return; }
    setSaving(true);
    setError(null);
    try {
      await hdldService.traLai(selected.id, { ly_do: lyDo.trim() });
      alert('✅ Đã trả lại cho HĐLĐ');
      setSelected(null);
      await load();
    } catch (e: unknown) {
      setError(getHdldErrorMessage(e, 'Lỗi trả lại'));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Đang tải…</div>;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* Danh sách chờ duyệt */}
      <div className="lg:col-span-1 bg-white rounded-xl border border-gray-200 p-4">
        <h3 className="font-semibold text-gray-800 mb-3">
          Chờ duyệt tháng {thang}/{nam} ({list.length})
        </h3>
        {list.length === 0 ? (
          <p className="text-sm text-gray-500">Không có bản nào chờ duyệt.</p>
        ) : (
          <ul className="space-y-2">
            {list.map((dg) => (
              <li key={dg.id}>
                <button
                  onClick={() => openDetail(dg)}
                  className={`w-full text-left px-3 py-2 rounded-lg border text-sm ${
                    selected?.id === dg.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <div className="font-medium text-gray-800">{dg.cong_chuc?.ho_ten}</div>
                  <div className="text-xs text-gray-500">
                    {dg.nhom_nghe ? `Nhóm ${dg.nhom_nghe} · ${HDLD_NHOM_LABEL[dg.nhom_nghe as HdldNhom]}` : ''}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Chi tiết duyệt */}
      <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-4">
        {!selected ? (
          <div className="p-8 text-center text-gray-400">Chọn 1 bản để duyệt</div>
        ) : (
          <>
            <div className="mb-3">
              <h3 className="font-semibold text-gray-800">{selected.cong_chuc?.ho_ten}</h3>
              <p className="text-sm text-gray-500">
                {selected.nhom_nghe ? `${selected.nhom_nghe}. ${HDLD_NHOM_LABEL[selected.nhom_nghe as HdldNhom]}` : ''}
              </p>
            </div>

            {error && (
              <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="w-full text-sm border border-gray-200">
                <thead>
                  <tr className="bg-gray-50 text-gray-600">
                    <th className="border px-2 py-2 w-10">STT</th>
                    <th className="border px-2 py-2 text-left">Tiêu chí</th>
                    <th className="border px-2 py-2 w-24">Tự ĐG (%)</th>
                    <th className="border px-2 py-2 w-28">Cấp QL (%)</th>
                  </tr>
                </thead>
                <tbody>
                  {[...selected.chi_tiets].sort((a, b) => a.so_tt - b.so_tt).map((ct) => {
                    const inp = inputs.find((i) => i.so_tt === ct.so_tt);
                    const diemQl = parseFloat(inp?.diem_ql || '');
                    const khacTuCham = ct.diem_tu != null && !isNaN(diemQl) && diemQl !== Number(ct.diem_tu);
                    return (
                      <tr key={ct.so_tt} className="align-top">
                        <td className="border px-2 py-2 text-center font-medium">{ct.so_tt}</td>
                        <td className="border px-2 py-2">
                          <div className="font-medium text-gray-800">{ct.ten_tieu_chi}</div>
                          <div className="text-gray-500 text-xs mt-1 whitespace-pre-line">{ct.mo_ta_chi_tiet}</div>
                          {ct.ghi_chu_tu && (
                            <div className="mt-1 text-xs text-gray-600">
                              <strong>HĐLĐ ghi chú:</strong> {ct.ghi_chu_tu}
                            </div>
                          )}
                          {/* Nhận xét cấp QL */}
                          <input
                            className="mt-2 w-full border border-gray-300 rounded px-2 py-1 text-xs"
                            placeholder="Nhận xét của cấp quản lý (tuỳ chọn)"
                            value={inp?.ghi_chu_ql || ''}
                            onChange={(e) => updateInput(ct.so_tt, 'ghi_chu_ql', e.target.value)}
                          />
                          {khacTuCham && (
                            <input
                              className="mt-1 w-full border border-amber-300 bg-amber-50 rounded px-2 py-1 text-xs"
                              placeholder="Lý do sửa khác điểm tự chấm (bắt buộc)"
                              value={inp?.ly_do_sua || ''}
                              onChange={(e) => updateInput(ct.so_tt, 'ly_do_sua', e.target.value)}
                            />
                          )}
                        </td>
                        <td className="border px-2 py-2 text-center text-gray-700">
                          {ct.diem_tu != null ? ct.diem_tu : '—'}
                        </td>
                        <td className="border px-2 py-2 text-center">
                          <input
                            type="number" min={0} max={100} step="0.5"
                            className="w-20 border border-gray-300 rounded px-2 py-1 text-center"
                            value={inp?.diem_ql || ''}
                            onChange={(e) => updateInput(ct.so_tt, 'diem_ql', e.target.value)}
                          />
                        </td>
                      </tr>
                    );
                  })}
                  <tr className="bg-gray-50 font-medium">
                    <td className="border px-2 py-2" colSpan={2}>Điểm trung bình</td>
                    <td className="border px-2 py-2 text-center">
                      {selected.diem_tc_tb_tu != null ? selected.diem_tc_tb_tu : '—'}
                    </td>
                    <td className="border px-2 py-2 text-center">{tbQl ?? '—'}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="mt-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">Ghi chú chung</label>
              <textarea
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                rows={2}
                value={ghiChu}
                onChange={(e) => setGhiChu(e.target.value)}
              />
            </div>

            {tbQl && (
              <div className="mt-2 text-sm text-gray-600">
                KPI dự kiến: <strong>{(parseFloat(tbQl) / 100 * 70).toFixed(2)}</strong> / 70
              </div>
            )}

            <div className="mt-4 flex gap-2 justify-end">
              <button
                onClick={handleTraLai}
                disabled={saving}
                className="px-4 py-2 bg-red-50 text-red-700 rounded-lg text-sm font-medium hover:bg-red-100 disabled:opacity-50"
              >
                Trả lại
              </button>
              <button
                onClick={handleDuyet}
                disabled={saving}
                className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50"
              >
                {saving ? 'Đang xử lý…' : 'Duyệt'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
