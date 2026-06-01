/**
 * src/components/hdld/Hdld111View.tsx
 * ===================================
 * View kê khai HĐLĐ 111 theo Bộ tiêu chí VB714 (từ T5/2026).
 *
 * HĐLĐ: chọn nhóm nghề I..VI → nhập % cho 3 tiêu chí (tiêu chí < 100% bắt buộc
 * ghi chú) → chọn người duyệt (TDV/PDV) → nộp.
 * Trạng thái: NHAP / CHO_DUYET / DA_DUYET / TRA_LAI.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import hdldService from '@/services/hdld.service';
import {
  IHdldDanhGia,
  IHdldTieuChi,
  INguoiDuyetOption,
  HdldNhom,
  HDLD_NHOM_LABEL,
  HDLD_TRANG_THAI_LABEL,
  getHdldErrorMessage,
} from '@/types/hdld';

interface Hdld111ViewProps {
  thang: number;
  nam: number;
}

interface ChiTietInput {
  so_tt: number;
  diem_tu: string; // giữ string để nhập liệu
  ghi_chu_tu: string;
}

const NHOM_LIST: HdldNhom[] = ['I', 'II', 'III', 'IV', 'V', 'VI'];

function badgeColor(tt: string): string {
  switch (tt) {
    case 'DA_DUYET': return 'bg-green-100 text-green-700';
    case 'CHO_DUYET': return 'bg-amber-100 text-amber-700';
    case 'TRA_LAI': return 'bg-red-100 text-red-700';
    default: return 'bg-gray-100 text-gray-600';
  }
}

export default function Hdld111View({ thang, nam }: Hdld111ViewProps) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [danhGia, setDanhGia] = useState<IHdldDanhGia | null>(null);
  const [nhom, setNhom] = useState<HdldNhom | ''>('');
  const [tieuChi, setTieuChi] = useState<IHdldTieuChi[]>([]);
  const [inputs, setInputs] = useState<ChiTietInput[]>([]);
  const [ghiChu, setGhiChu] = useState('');

  const [nguoiDuyetList, setNguoiDuyetList] = useState<INguoiDuyetOption[]>([]);
  const [nguoiDuyetId, setNguoiDuyetId] = useState('');

  const editable = danhGia
    ? danhGia.trang_thai === 'NHAP' || danhGia.trang_thai === 'TRA_LAI'
    : true;

  // ---- Load bản đánh giá của tháng ----
  const loadDanhGia = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const dg = await hdldService.getDanhGia(thang, nam);
      setDanhGia(dg);
      if (dg) {
        setGhiChu(dg.ghi_chu || '');
        setNguoiDuyetId(dg.nguoi_duyet_id || '');
        if (dg.nhom_nghe) {
          setNhom(dg.nhom_nghe as HdldNhom);
        }
        if (dg.chi_tiets && dg.chi_tiets.length > 0) {
          setInputs(dg.chi_tiets.map((ct) => ({
            so_tt: ct.so_tt,
            diem_tu: ct.diem_tu != null ? String(ct.diem_tu) : '',
            ghi_chu_tu: ct.ghi_chu_tu || '',
          })));
        }
      }
    } catch (err: unknown) {
      setError(getHdldErrorMessage(err, 'Không tải được dữ liệu'));
    } finally {
      setLoading(false);
    }
  }, [thang, nam]);

  useEffect(() => { loadDanhGia(); }, [loadDanhGia]);

  // ---- Load người duyệt 1 lần ----
  useEffect(() => {
    hdldService.getNguoiDuyet().then(setNguoiDuyetList).catch(() => setNguoiDuyetList([]));
  }, []);

  // ---- Khi chọn nhóm nghề → load 3 tiêu chí ----
  const handleSelectNhom = useCallback(async (value: HdldNhom) => {
    setNhom(value);
    const res = await hdldService.getTieuChi(value);
    if (res) {
      setTieuChi(res.tieu_chi);
      setInputs((prev) => {
        // giữ điểm cũ nếu cùng so_tt
        const byId = new Map(prev.map((p) => [p.so_tt, p]));
        return res.tieu_chi.map((tc) => byId.get(tc.so_tt) || {
          so_tt: tc.so_tt, diem_tu: '', ghi_chu_tu: '',
        });
      });
    }
  }, []);

  // Tự load tiêu chí khi đã có nhom_nghe từ server
  useEffect(() => {
    if (nhom && tieuChi.length === 0) {
      hdldService.getTieuChi(nhom).then((res) => res && setTieuChi(res.tieu_chi));
    }
  }, [nhom, tieuChi.length]);

  const updateInput = (so_tt: number, field: 'diem_tu' | 'ghi_chu_tu', val: string) => {
    setInputs((prev) => prev.map((p) => (p.so_tt === so_tt ? { ...p, [field]: val } : p)));
  };

  const tbTuDanhGia = (() => {
    const vals = inputs.map((i) => parseFloat(i.diem_tu)).filter((v) => !isNaN(v));
    if (vals.length !== 3) return null;
    return (vals.reduce((a, b) => a + b, 0) / 3).toFixed(2);
  })();

  // ---- Validate client trước khi lưu ----
  const validate = (): string | null => {
    if (!nhom) return 'Vui lòng chọn nhóm nghề';
    if (inputs.length !== 3) return 'Phải có đủ 3 tiêu chí';
    for (const i of inputs) {
      const d = parseFloat(i.diem_tu);
      if (isNaN(d) || d < 0 || d > 100) return `Tiêu chí ${i.so_tt}: điểm phải trong khoảng 0–100`;
      if (d < 100 && !i.ghi_chu_tu.trim()) return `Tiêu chí ${i.so_tt}: điểm < 100% bắt buộc ghi chú lý do`;
    }
    return null;
  };

  const ensureDanhGiaId = async (): Promise<string> => {
    if (danhGia?.id) return danhGia.id;
    const dg = await hdldService.getDanhGia(thang, nam);
    if (!dg) throw new Error('Không khởi tạo được bản đánh giá');
    setDanhGia(dg);
    return dg.id;
  };

  const handleSave = async () => {
    const err = validate();
    if (err) { setError(err); return; }
    setSaving(true);
    setError(null);
    try {
      const id = await ensureDanhGiaId();
      const dg = await hdldService.luuTuDanhGia(id, {
        nhom_nghe: nhom as string,
        chi_tiets: inputs.map((i) => ({
          so_tt: i.so_tt,
          diem_tu: parseFloat(i.diem_tu),
          ghi_chu_tu: i.ghi_chu_tu.trim() || null,
        })),
        ghi_chu: ghiChu.trim() || null,
      });
      setDanhGia(dg);
      alert('✅ Đã lưu tự đánh giá');
    } catch (e: unknown) {
      setError(getHdldErrorMessage(e, 'Lỗi lưu'));
    } finally {
      setSaving(false);
    }
  };

  const handleNop = async () => {
    const err = validate();
    if (err) { setError(err); return; }
    if (!nguoiDuyetId) { setError('Vui lòng chọn người duyệt (Trưởng/Phó đơn vị)'); return; }
    if (!confirm('Xác nhận nộp đánh giá? Sau khi nộp bạn không sửa được cho đến khi được trả lại.')) return;
    setSaving(true);
    setError(null);
    try {
      const id = await ensureDanhGiaId();
      // Lưu trước rồi nộp (đảm bảo dữ liệu mới nhất)
      await hdldService.luuTuDanhGia(id, {
        nhom_nghe: nhom as string,
        chi_tiets: inputs.map((i) => ({
          so_tt: i.so_tt,
          diem_tu: parseFloat(i.diem_tu),
          ghi_chu_tu: i.ghi_chu_tu.trim() || null,
        })),
        ghi_chu: ghiChu.trim() || null,
      });
      const dg = await hdldService.nop(id, { nguoi_duyet_id: nguoiDuyetId });
      setDanhGia(dg);
      alert('✅ Đã nộp, chờ cấp quản lý duyệt');
    } catch (e: unknown) {
      setError(getHdldErrorMessage(e, 'Lỗi nộp'));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Đang tải…</div>;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      {/* Header trạng thái */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">
            Tự đánh giá HĐLĐ tháng {thang}/{nam}
          </h2>
          <p className="text-sm text-gray-500">Bộ tiêu chí theo QĐ 714/QĐ-CHQ</p>
        </div>
        {danhGia && (
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${badgeColor(danhGia.trang_thai)}`}>
            {HDLD_TRANG_THAI_LABEL[danhGia.trang_thai]}
          </span>
        )}
      </div>

      {danhGia?.trang_thai === 'TRA_LAI' && danhGia.ly_do_tra_lai && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <strong>Bị trả lại:</strong> {danhGia.ly_do_tra_lai}
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Chọn nhóm nghề */}
      <div className="mb-5">
        <label className="block text-sm font-medium text-gray-700 mb-1">Nhóm nghề</label>
        <select
          className="w-full md:w-2/3 border border-gray-300 rounded-lg px-3 py-2 text-sm disabled:bg-gray-100"
          value={nhom}
          disabled={!editable}
          onChange={(e) => handleSelectNhom(e.target.value as HdldNhom)}
        >
          <option value="">— Chọn nhóm nghề —</option>
          {NHOM_LIST.map((n) => (
            <option key={n} value={n}>{n}. {HDLD_NHOM_LABEL[n]}</option>
          ))}
        </select>
      </div>

      {/* Bảng 3 tiêu chí */}
      {nhom && tieuChi.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border border-gray-200">
            <thead>
              <tr className="bg-gray-50 text-gray-600">
                <th className="border px-2 py-2 w-10">STT</th>
                <th className="border px-2 py-2 text-left">Tiêu chí</th>
                <th className="border px-2 py-2 w-28">Tự đánh giá (%)</th>
                <th className="border px-2 py-2 w-28">Cấp QL (%)</th>
              </tr>
            </thead>
            <tbody>
              {tieuChi.map((tc) => {
                const inp = inputs.find((i) => i.so_tt === tc.so_tt);
                const ctServer = danhGia?.chi_tiets?.find((c) => c.so_tt === tc.so_tt);
                const diemTu = parseFloat(inp?.diem_tu || '');
                const needNote = !isNaN(diemTu) && diemTu < 100;
                return (
                  <tr key={tc.id} className="align-top">
                    <td className="border px-2 py-2 text-center font-medium">{tc.so_tt}</td>
                    <td className="border px-2 py-2">
                      <div className="font-medium text-gray-800">{tc.ten_tieu_chi}</div>
                      <div className="text-gray-500 text-xs mt-1 whitespace-pre-line">{tc.mo_ta_chi_tiet}</div>
                      {(needNote || (inp?.ghi_chu_tu)) && (
                        <textarea
                          className="mt-2 w-full border border-gray-300 rounded px-2 py-1 text-xs disabled:bg-gray-100"
                          placeholder="Ghi chú lý do (bắt buộc khi < 100%)"
                          rows={2}
                          value={inp?.ghi_chu_tu || ''}
                          disabled={!editable}
                          onChange={(e) => updateInput(tc.so_tt, 'ghi_chu_tu', e.target.value)}
                        />
                      )}
                      {ctServer?.ghi_chu_ql && (
                        <div className="mt-1 text-xs text-blue-600">
                          <strong>Nhận xét cấp QL:</strong> {ctServer.ghi_chu_ql}
                        </div>
                      )}
                      {ctServer?.ly_do_sua && (
                        <div className="mt-1 text-xs text-amber-600">
                          <strong>Lý do cấp QL sửa điểm:</strong> {ctServer.ly_do_sua}
                        </div>
                      )}
                    </td>
                    <td className="border px-2 py-2 text-center">
                      <input
                        type="number" min={0} max={100} step="0.5"
                        className="w-20 border border-gray-300 rounded px-2 py-1 text-center disabled:bg-gray-100"
                        value={inp?.diem_tu || ''}
                        disabled={!editable}
                        onChange={(e) => updateInput(tc.so_tt, 'diem_tu', e.target.value)}
                      />
                    </td>
                    <td className="border px-2 py-2 text-center text-gray-700">
                      {ctServer?.diem_ql != null ? ctServer.diem_ql : '—'}
                    </td>
                  </tr>
                );
              })}
              <tr className="bg-gray-50 font-medium">
                <td className="border px-2 py-2" colSpan={2}>Điểm trung bình</td>
                <td className="border px-2 py-2 text-center">{tbTuDanhGia ?? '—'}</td>
                <td className="border px-2 py-2 text-center">
                  {danhGia?.diem_tc_tb_ql != null ? danhGia.diem_tc_tb_ql : '—'}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {/* Điểm KPI sau duyệt */}
      {danhGia?.diem_kpi_70 != null && (
        <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-800">
          Điểm KPI (70): <strong>{danhGia.diem_kpi_70}</strong> / 70
        </div>
      )}

      {/* Ghi chú chung */}
      {nhom && (
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Ghi chú chung</label>
          <textarea
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm disabled:bg-gray-100"
            rows={2}
            value={ghiChu}
            disabled={!editable}
            onChange={(e) => setGhiChu(e.target.value)}
          />
        </div>
      )}

      {/* Người duyệt + actions */}
      {editable && nhom && (
        <div className="mt-5 flex flex-col md:flex-row md:items-end gap-3">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Người duyệt (Trưởng/Phó đơn vị)
            </label>
            <select
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
              value={nguoiDuyetId}
              onChange={(e) => setNguoiDuyetId(e.target.value)}
            >
              <option value="">— Chọn người duyệt —</option>
              {nguoiDuyetList.map((nd) => (
                <option key={nd.id} value={nd.id}>
                  {nd.ho_ten} {nd.chuc_vu ? `(${nd.chuc_vu})` : ''}
                </option>
              ))}
            </select>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 disabled:opacity-50"
            >
              {saving ? 'Đang lưu…' : 'Lưu nháp'}
            </button>
            <button
              onClick={handleNop}
              disabled={saving}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              Nộp đánh giá
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
