'use client';

/**
 * MauCauTrucDeManager
 * ===================
 * Tab "Mẫu cấu trúc đề" — quản lý thư viện mẫu cấu trúc đề thi ĐGNL.
 *
 * Trước đây mẫu chỉ tạo được bằng cách dựng cấu trúc trên 1 kỳ thi rồi "Lưu
 * thành mẫu"; muốn sửa 1 con số phải áp mẫu vào kỳ thi, sửa, rồi lưu thành mẫu
 * MỚI (trùng tên chồng chất). Tab này cho sửa trực tiếp trên lưới rồi lưu 1 phát
 * bằng PUT /cau-truc-de-template/{id}.
 *
 * Ngoài ra export dùng chung cho modal cấu trúc đề của kỳ thi:
 *   - useTonKhoNganHang(): tồn kho câu hỏi theo lĩnh vực × độ khó
 *   - SoCauInput: ô nhập số câu có hiện tồn kho + cảnh báo vượt
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { cauTrucDeTemplateApi, kyThiApi, nganHangDgnlApi } from '@/services/lms';
import type {
  ICauTrucDeTemplate,
  IKyThi,
  ILinhVuc,
  IThongKeNganHang,
  IViTriViecLam,
} from '@/types/lms';

// =============================================================================
// TỒN KHO NGÂN HÀNG CÂU HỎI — dùng chung
// =============================================================================

export type DoKho = 'de' | 'trung_binh' | 'kho';

export interface TonKho {
  /** Số câu sẵn có trong ngân hàng theo lĩnh vực × độ khó. */
  lay: (linhVucId: string, doKho: DoKho) => number | null;
  daTai: boolean;
}

/** Nạp GET /dgnl/ngan-hang/thong-ke một lần, tra cứu theo lĩnh vực. */
export function useTonKhoNganHang(): TonKho {
  const [map, setMap] = useState<Record<string, IThongKeNganHang> | null>(null);

  useEffect(() => {
    let huy = false;
    nganHangDgnlApi
      .thongKe()
      .then(res => {
        if (huy) return;
        const list: IThongKeNganHang[] = res.data.data || [];
        setMap(Object.fromEntries(list.map(tk => [tk.linh_vuc_id, tk])));
      })
      .catch(() => { if (!huy) setMap({}); });
    return () => { huy = true; };
  }, []);

  const lay = useCallback(
    (linhVucId: string, doKho: DoKho): number | null => {
      if (!map) return null;
      const tk = map[linhVucId];
      if (!tk) return null;
      if (doKho === 'de') return tk.so_cau_de;
      if (doKho === 'trung_binh') return tk.so_cau_trung_binh;
      return tk.so_cau_kho;
    },
    [map],
  );

  return { lay, daTai: map !== null };
}

/** Ô nhập số câu — hiện "/ N" tồn kho, tô đỏ khi nhập vượt ngân hàng. */
export function SoCauInput({
  value, onChange, tonKho, nhan, disabled,
}: {
  value: number;
  onChange: (v: number) => void;
  /** Số câu sẵn có; null = chưa biết (chưa tải xong / lĩnh vực không có trong thống kê). */
  tonKho: number | null;
  nhan?: string;
  disabled?: boolean;
}) {
  const vuot = tonKho !== null && value > tonKho;
  return (
    <div>
      {nhan && <label className="text-xs text-gray-500">{nhan}</label>}
      <div className="flex items-center gap-1">
        <input
          type="number"
          min={0}
          value={value}
          disabled={disabled}
          onChange={e => onChange(Math.max(0, +e.target.value || 0))}
          title={vuot ? `Ngân hàng chỉ có ${tonKho} câu` : undefined}
          className={`w-full border rounded px-2 py-1 text-sm disabled:bg-gray-100 ${
            vuot ? 'border-red-400 bg-red-50 text-red-700 font-medium' : ''
          }`}
        />
        <span
          className={`text-[11px] whitespace-nowrap ${vuot ? 'text-red-600 font-medium' : 'text-gray-400'}`}
          title="Số câu sẵn có trong ngân hàng"
        >
          /{tonKho === null ? '—' : tonKho}
        </span>
      </div>
    </div>
  );
}

// =============================================================================
// Kiểu dữ liệu editor
// =============================================================================

interface DongCauTruc {
  linh_vuc_id: string;
  so_cau_de: number;
  so_cau_trung_binh: number;
  so_cau_kho: number;
}

interface KhoiViTri {
  vi_tri_id: string;
  rows: DongCauTruc[];
}

/** Gom `cau_truc` phẳng của mẫu thành các khối theo vị trí (giữ thứ tự xuất hiện). */
function gomTheoViTri(cauTruc: ICauTrucDeTemplate['cau_truc']): KhoiViTri[] {
  const khoi: KhoiViTri[] = [];
  for (const row of cauTruc || []) {
    let k = khoi.find(x => x.vi_tri_id === row.vi_tri_id);
    if (!k) { k = { vi_tri_id: row.vi_tri_id, rows: [] }; khoi.push(k); }
    k.rows.push({
      linh_vuc_id: row.linh_vuc_id,
      so_cau_de: row.so_cau_de || 0,
      so_cau_trung_binh: row.so_cau_trung_binh || 0,
      so_cau_kho: row.so_cau_kho || 0,
    });
  }
  return khoi;
}

function tongCauKhoi(k: KhoiViTri): number {
  return k.rows.reduce((s, r) => s + r.so_cau_de + r.so_cau_trung_binh + r.so_cau_kho, 0);
}

function tongCauMau(tpl: ICauTrucDeTemplate): number {
  return (tpl.cau_truc || []).reduce(
    (s, r) => s + (r.so_cau_de || 0) + (r.so_cau_trung_binh || 0) + (r.so_cau_kho || 0), 0);
}

function loiApi(err: any, macDinh: string): string {
  return err?.response?.data?.detail?.error?.message
    || err?.response?.data?.error?.message
    || macDinh;
}

// =============================================================================
// Component chính
// =============================================================================

export default function MauCauTrucDeManager({ linhVucList, viTriList }: {
  linhVucList: ILinhVuc[];
  viTriList: IViTriViecLam[];
}) {
  const [templates, setTemplates] = useState<ICauTrucDeTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  /** id mẫu đang sửa, hoặc 'MOI' khi đang tạo mẫu trống. */
  const [dangSua, setDangSua] = useState<string | null>(null);

  const tonKho = useTonKhoNganHang();

  const loadTemplates = useCallback(async () => {
    setLoading(true);
    try {
      const res = await cauTrucDeTemplateApi.danhSach({ page_size: 100 });
      setTemplates(res.data.data || []);
    } catch (err: any) {
      setError(loiApi(err, 'Không tải được danh sách mẫu cấu trúc đề'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadTemplates(); }, [loadTemplates]);

  const mauDangSua = dangSua && dangSua !== 'MOI'
    ? templates.find(t => t.id === dangSua) || null
    : null;

  const handleNhanBan = async (tpl: ICauTrucDeTemplate) => {
    const ten = prompt(`Tên cho bản sao của "${tpl.ten_template}":`, `${tpl.ten_template} (bản sao)`);
    if (!ten?.trim()) return;
    setError(null); setSuccess(null);
    try {
      await cauTrucDeTemplateApi.nhanBan(tpl.id, { ten_template: ten.trim() });
      setSuccess(`Đã nhân bản thành mẫu "${ten.trim()}"`);
      await loadTemplates();
    } catch (err: any) {
      setError(loiApi(err, 'Lỗi nhân bản mẫu'));
    }
  };

  const handleXoa = async (tpl: ICauTrucDeTemplate) => {
    if (!confirm(`Xóa mẫu "${tpl.ten_template}"?\n\nCác kỳ thi đã áp dụng mẫu này KHÔNG bị ảnh hưởng.`)) return;
    setError(null); setSuccess(null);
    try {
      await cauTrucDeTemplateApi.xoa(tpl.id);
      setSuccess(`Đã xóa mẫu "${tpl.ten_template}"`);
      if (dangSua === tpl.id) setDangSua(null);
      await loadTemplates();
    } catch (err: any) {
      setError(loiApi(err, 'Lỗi xóa mẫu'));
    }
  };

  if (dangSua) {
    return (
      <MauCauTrucDeEditor
        mau={mauDangSua}
        linhVucList={linhVucList}
        viTriList={viTriList}
        tonKho={tonKho}
        onXong={async (msg) => {
          setDangSua(null);
          if (msg) setSuccess(msg);
          await loadTemplates();
        }}
        onHuy={() => setDangSua(null)}
      />
    );
  }

  return (
    <div className="space-y-4">
      {error && <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      {success && <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">{success}</div>}

      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">
          Mẫu cấu trúc đề dùng để áp nhanh vào kỳ thi mới. Sửa trực tiếp tại đây — không cần áp vào kỳ thi rồi lưu lại.
        </p>
        <button
          onClick={() => { setError(null); setSuccess(null); setDangSua('MOI'); }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 whitespace-nowrap"
        >
          + Tạo mẫu mới
        </button>
      </div>

      <div className="bg-white rounded-xl border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b text-left text-gray-500">
                <th className="py-3 px-4">Tên mẫu</th>
                <th className="py-3 px-4">Mô tả</th>
                <th className="py-3 px-4 text-center">Vị trí</th>
                <th className="py-3 px-4 text-center">Tổng câu</th>
                <th className="py-3 px-4">Người tạo</th>
                <th className="py-3 px-4">Cập nhật</th>
                <th className="py-3 px-4 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan={7} className="py-8 text-center text-gray-400">Đang tải...</td></tr>
              )}
              {!loading && templates.length === 0 && (
                <tr><td colSpan={7} className="py-8 text-center text-gray-400">
                  Chưa có mẫu cấu trúc đề nào. Bấm "Tạo mẫu mới" để bắt đầu.
                </td></tr>
              )}
              {!loading && templates.map(tpl => {
                const soViTri = new Set((tpl.cau_truc || []).map(r => r.vi_tri_id)).size;
                return (
                  <tr key={tpl.id} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium">{tpl.ten_template}</td>
                    <td className="py-3 px-4 text-gray-500 max-w-xs truncate" title={tpl.mo_ta || ''}>
                      {tpl.mo_ta || '—'}
                    </td>
                    <td className="py-3 px-4 text-center">{soViTri}</td>
                    <td className="py-3 px-4 text-center font-medium">{tongCauMau(tpl)}</td>
                    <td className="py-3 px-4 text-gray-500">{tpl.nguoi_tao_ho_ten || '—'}</td>
                    <td className="py-3 px-4 text-gray-500 whitespace-nowrap">
                      {tpl.updated_at ? new Date(tpl.updated_at).toLocaleDateString('vi-VN') : '—'}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex gap-1 justify-end">
                        <button
                          onClick={() => { setError(null); setSuccess(null); setDangSua(tpl.id); }}
                          className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                        >
                          Sửa
                        </button>
                        <button
                          onClick={() => handleNhanBan(tpl)}
                          className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                        >
                          Nhân bản
                        </button>
                        <button
                          onClick={() => handleXoa(tpl)}
                          className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
                        >
                          Xóa
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Editor — sửa trực tiếp trên lưới
// =============================================================================

function MauCauTrucDeEditor({ mau, linhVucList, viTriList, tonKho, onXong, onHuy }: {
  /** null = tạo mẫu mới. */
  mau: ICauTrucDeTemplate | null;
  linhVucList: ILinhVuc[];
  viTriList: IViTriViecLam[];
  tonKho: TonKho;
  onXong: (msg?: string) => void | Promise<void>;
  onHuy: () => void;
}) {
  const [ten, setTen] = useState(mau?.ten_template || '');
  const [moTa, setMoTa] = useState(mau?.mo_ta || '');
  const [khoi, setKhoi] = useState<KhoiViTri[]>(() => gomTheoViTri(mau?.cau_truc || []));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Áp dụng vào kỳ thi
  const [kyThiList, setKyThiList] = useState<IKyThi[]>([]);
  const [kyThiChon, setKyThiChon] = useState('');
  const [ghiDeToanBo, setGhiDeToanBo] = useState(false);
  const [apDungBusy, setApDungBusy] = useState(false);
  const [apDungMsg, setApDungMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!mau) return; // mẫu chưa lưu thì chưa áp dụng được
    kyThiApi.danhSach({ page_size: 100 })
      .then(res => setKyThiList((res.data.data || []).filter(
        (kt: IKyThi) => kt.trang_thai !== 'DA_DONG')))
      .catch(() => { /* không có quyền / lỗi mạng — ẩn phần áp dụng */ });
  }, [mau]);

  const viTriMap = useMemo(
    () => Object.fromEntries(viTriList.map(vt => [vt.id, vt])), [viTriList]);
  const linhVucMap = useMemo(
    () => Object.fromEntries(linhVucList.map(lv => [lv.id, lv])), [linhVucList]);

  const viTriChuaDung = viTriList.filter(vt => !khoi.some(k => k.vi_tri_id === vt.id));

  /** Đếm số ô vượt tồn kho ngân hàng — chỉ cảnh báo, không chặn lưu. */
  const soOVuot = useMemo(() => {
    let n = 0;
    for (const k of khoi) {
      for (const r of k.rows) {
        const cap: [DoKho, number][] = [
          ['de', r.so_cau_de], ['trung_binh', r.so_cau_trung_binh], ['kho', r.so_cau_kho],
        ];
        for (const [dk, v] of cap) {
          const co = tonKho.lay(r.linh_vuc_id, dk);
          if (co !== null && v > co) n++;
        }
      }
    }
    return n;
  }, [khoi, tonKho]);

  /** Dòng trỏ tới vị trí/lĩnh vực đã bị xóa khỏi danh mục — mẫu lưu id trần (JSONB, không FK). */
  const soDongChet = useMemo(() => {
    let n = 0;
    for (const k of khoi) {
      if (!viTriMap[k.vi_tri_id]) { n += k.rows.length; continue; }
      n += k.rows.filter(r => r.linh_vuc_id && !linhVucMap[r.linh_vuc_id]).length;
    }
    return n;
  }, [khoi, viTriMap, linhVucMap]);

  const capNhatRow = (ki: number, ri: number, patch: Partial<DongCauTruc>) => {
    setKhoi(prev => prev.map((k, i) => i !== ki ? k : {
      ...k, rows: k.rows.map((r, j) => j !== ri ? r : { ...r, ...patch }),
    }));
  };

  const themDong = (ki: number) => {
    setKhoi(prev => prev.map((k, i) => i !== ki ? k : {
      ...k, rows: [...k.rows, { linh_vuc_id: '', so_cau_de: 0, so_cau_trung_binh: 0, so_cau_kho: 0 }],
    }));
  };

  const xoaDong = (ki: number, ri: number) => {
    setKhoi(prev => prev.map((k, i) => i !== ki ? k : {
      ...k, rows: k.rows.filter((_, j) => j !== ri),
    }));
  };

  const themViTri = (viTriId: string) => {
    if (!viTriId || khoi.some(k => k.vi_tri_id === viTriId)) return;
    setKhoi(prev => [...prev, {
      vi_tri_id: viTriId,
      rows: [{ linh_vuc_id: '', so_cau_de: 0, so_cau_trung_binh: 0, so_cau_kho: 0 }],
    }]);
  };

  const xoaViTri = (ki: number) => {
    const k = khoi[ki];
    const ten = viTriMap[k.vi_tri_id]?.ten_vi_tri || 'vị trí không còn tồn tại';
    if (!confirm(`Xóa toàn bộ ${k.rows.length} dòng của "${ten}" khỏi mẫu?`)) return;
    setKhoi(prev => prev.filter((_, i) => i !== ki));
  };

  const handleLuu = async () => {
    setError(null);
    if (!ten.trim()) { setError('Vui lòng nhập tên mẫu'); return; }

    // Bỏ dòng chưa chọn lĩnh vực, bỏ khối rỗng
    const cauTruc = khoi.flatMap(k => k.rows
      .filter(r => r.linh_vuc_id)
      .map(r => ({
        vi_tri_id: k.vi_tri_id,
        linh_vuc_id: r.linh_vuc_id,
        so_cau_de: r.so_cau_de,
        so_cau_trung_binh: r.so_cau_trung_binh,
        so_cau_kho: r.so_cau_kho,
      })));

    if (cauTruc.length === 0) {
      setError('Mẫu phải có ít nhất 1 dòng (vị trí + lĩnh vực)');
      return;
    }
    // Trùng vị trí × lĩnh vực sẽ khiến kỳ thi nhận 2 dòng cùng khóa — chặn sớm
    const khoa = cauTruc.map(r => `${r.vi_tri_id}|${r.linh_vuc_id}`);
    if (new Set(khoa).size !== khoa.length) {
      setError('Có lĩnh vực bị lặp trong cùng một vị trí — vui lòng gộp lại thành 1 dòng');
      return;
    }

    setSaving(true);
    try {
      if (mau) {
        await cauTrucDeTemplateApi.capNhat(mau.id, {
          ten_template: ten.trim(), mo_ta: moTa, cau_truc: cauTruc,
        });
        await onXong(`Đã cập nhật mẫu "${ten.trim()}"`);
      } else {
        await cauTrucDeTemplateApi.taoMoi({
          ten_template: ten.trim(), mo_ta: moTa || undefined, cau_truc: cauTruc,
        });
        await onXong(`Đã tạo mẫu "${ten.trim()}"`);
      }
    } catch (err: any) {
      setError(loiApi(err, 'Lỗi lưu mẫu cấu trúc đề'));
    } finally {
      setSaving(false);
    }
  };

  const handleApDung = async () => {
    const kt = kyThiList.find(k => k.id === kyThiChon);
    if (!mau || !kt) return;
    const canhBao = ghiDeToanBo
      ? `Áp dụng mẫu "${mau.ten_template}" vào kỳ thi ${kt.ma_ky_thi}?\n\nTOÀN BỘ cấu trúc đề hiện có của kỳ thi sẽ bị XÓA và thay bằng mẫu.`
      : `Áp dụng mẫu "${mau.ten_template}" vào kỳ thi ${kt.ma_ky_thi}?\n\nCấu trúc của các vị trí có trong mẫu sẽ bị GHI ĐÈ. Các vị trí khác giữ nguyên.`;
    if (!confirm(canhBao)) return;

    setApDungBusy(true); setApDungMsg(null); setError(null);
    try {
      const res = await kyThiApi.apDungMauCauTruc(kt.id, {
        template_id: mau.id, ghi_de_toan_bo: ghiDeToanBo,
      });
      const soViTri = (res.data.data || []).length;
      setApDungMsg(`✅ Đã áp dụng vào kỳ thi ${kt.ma_ky_thi} — hiện có ${soViTri} vị trí`);
    } catch (err: any) {
      setError(loiApi(err, 'Lỗi áp dụng mẫu vào kỳ thi'));
    } finally {
      setApDungBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      {error && <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      {apDungMsg && <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">{apDungMsg}</div>}

      <div className="flex items-center justify-between">
        <h3 className="font-bold text-lg">
          {mau ? `Sửa mẫu — ${mau.ten_template}` : 'Tạo mẫu cấu trúc đề mới'}
        </h3>
        <div className="flex gap-2">
          <button onClick={onHuy} className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50">
            ← Quay lại danh sách
          </button>
          <button
            onClick={handleLuu}
            disabled={saving}
            className="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Đang lưu...' : '💾 Lưu mẫu'}
          </button>
        </div>
      </div>

      {/* Thông tin mẫu */}
      <div className="bg-white rounded-xl border p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Tên mẫu *</label>
          <input
            value={ten}
            onChange={e => setTen(e.target.value)}
            placeholder="VD: Cấu trúc chuẩn Quý 3/2026"
            className="w-full border rounded-lg px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Mô tả</label>
          <input
            value={moTa}
            onChange={e => setMoTa(e.target.value)}
            placeholder="Ghi chú ngắn về mẫu này"
            className="w-full border rounded-lg px-3 py-2 text-sm"
          />
        </div>
      </div>

      {/* Cảnh báo */}
      {soOVuot > 0 && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm">
          ⚠️ Có <strong>{soOVuot}</strong> ô vượt quá số câu sẵn có trong ngân hàng (các ô tô đỏ).
          Vẫn lưu mẫu được, nhưng kỳ thi áp dụng mẫu này sẽ báo lỗi khi thí sinh bấm "Bắt đầu thi"
          nếu chưa bổ sung câu hỏi.
        </div>
      )}
      {soDongChet > 0 && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          ⚠️ Có <strong>{soDongChet}</strong> dòng trỏ tới vị trí/lĩnh vực đã bị xóa khỏi danh mục.
          Phải gỡ các dòng này thì mới áp dụng mẫu vào kỳ thi được.
        </div>
      )}

      {/* Lưới cấu trúc */}
      {khoi.length === 0 && (
        <div className="bg-white rounded-xl border p-8 text-center text-gray-400 text-sm">
          Mẫu chưa có vị trí nào. Chọn vị trí việc làm bên dưới để bắt đầu.
        </div>
      )}

      {khoi.map((k, ki) => {
        const vt = viTriMap[k.vi_tri_id];
        return (
          <div key={k.vi_tri_id} className={`bg-white rounded-xl border p-4 ${vt ? '' : 'border-red-300'}`}>
            <div className="flex items-center justify-between mb-3">
              <div className="font-medium text-sm">
                {vt ? vt.ten_vi_tri : <span className="text-red-600">⚠️ Vị trí đã bị xóa ({k.vi_tri_id.slice(0, 8)}…)</span>}
                <span className="ml-2 text-gray-400 font-normal">— tổng {tongCauKhoi(k)} câu</span>
              </div>
              <button onClick={() => xoaViTri(ki)} className="text-red-500 text-xs hover:underline">
                Xóa vị trí
              </button>
            </div>

            <div className="space-y-2">
              {k.rows.map((r, ri) => {
                const lvChet = !!r.linh_vuc_id && !linhVucMap[r.linh_vuc_id];
                return (
                  <div key={ri} className="grid grid-cols-12 gap-2 items-end">
                    <div className="col-span-5">
                      {ri === 0 && <label className="text-xs text-gray-500">Lĩnh vực</label>}
                      {lvChet ? (
                        <div className="border border-red-300 bg-red-50 rounded px-2 py-1 text-sm text-red-600">
                          ⚠️ Lĩnh vực đã bị xóa ({r.linh_vuc_id.slice(0, 8)}…)
                        </div>
                      ) : (
                        <select
                          value={r.linh_vuc_id}
                          onChange={e => capNhatRow(ki, ri, { linh_vuc_id: e.target.value })}
                          className="w-full border rounded px-2 py-1 text-sm"
                        >
                          <option value="">-- Chọn lĩnh vực --</option>
                          {linhVucList.map(lv => (
                            <option
                              key={lv.id}
                              value={lv.id}
                              disabled={lv.id !== r.linh_vuc_id && k.rows.some(x => x.linh_vuc_id === lv.id)}
                            >
                              {lv.ten_linh_vuc}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                    <div className="col-span-2">
                      <SoCauInput
                        nhan={ri === 0 ? 'Dễ' : undefined}
                        value={r.so_cau_de}
                        onChange={v => capNhatRow(ki, ri, { so_cau_de: v })}
                        tonKho={tonKho.lay(r.linh_vuc_id, 'de')}
                      />
                    </div>
                    <div className="col-span-2">
                      <SoCauInput
                        nhan={ri === 0 ? 'TB' : undefined}
                        value={r.so_cau_trung_binh}
                        onChange={v => capNhatRow(ki, ri, { so_cau_trung_binh: v })}
                        tonKho={tonKho.lay(r.linh_vuc_id, 'trung_binh')}
                      />
                    </div>
                    <div className="col-span-2">
                      <SoCauInput
                        nhan={ri === 0 ? 'Khó' : undefined}
                        value={r.so_cau_kho}
                        onChange={v => capNhatRow(ki, ri, { so_cau_kho: v })}
                        tonKho={tonKho.lay(r.linh_vuc_id, 'kho')}
                      />
                    </div>
                    <div className="col-span-1 pb-1">
                      <button onClick={() => xoaDong(ki, ri)} className="text-red-500 text-xs hover:underline">
                        Xóa
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            <button
              onClick={() => themDong(ki)}
              className="mt-3 px-3 py-1.5 text-xs border border-dashed border-gray-300 rounded-lg hover:bg-gray-50"
            >
              + Thêm lĩnh vực
            </button>
          </div>
        );
      })}

      {/* Thêm vị trí */}
      <div className="bg-white rounded-xl border p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Thêm vị trí việc làm vào mẫu</label>
        <select
          value=""
          onChange={e => themViTri(e.target.value)}
          disabled={viTriChuaDung.length === 0}
          className="border rounded-lg px-3 py-2 text-sm min-w-[280px] disabled:bg-gray-100"
        >
          <option value="">
            {viTriChuaDung.length === 0 ? '-- Đã dùng hết vị trí --' : '-- Chọn vị trí để thêm --'}
          </option>
          {viTriChuaDung.map(vt => (
            <option key={vt.id} value={vt.id}>{vt.ten_vi_tri}</option>
          ))}
        </select>
      </div>

      {/* Áp dụng vào kỳ thi */}
      {mau && (
        <div className="bg-indigo-50/60 border border-indigo-100 rounded-xl p-4">
          <div className="text-sm font-semibold text-gray-700 mb-2">📤 Áp dụng mẫu vào kỳ thi</div>
          <p className="text-xs text-gray-500 mb-3">
            Áp dụng bản đã LƯU của mẫu. Nếu vừa sửa ở trên, hãy bấm "Lưu mẫu" trước.
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={kyThiChon}
              onChange={e => setKyThiChon(e.target.value)}
              className="border rounded-lg px-2 py-1.5 text-sm min-w-[280px]"
            >
              <option value="">-- Chọn kỳ thi --</option>
              {kyThiList.map(kt => (
                <option key={kt.id} value={kt.id}>
                  {kt.ma_ky_thi} — {kt.ten_ky_thi} ({kt.trang_thai})
                </option>
              ))}
            </select>
            <label className="flex items-center gap-1.5 text-xs text-gray-600 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={ghiDeToanBo}
                onChange={e => setGhiDeToanBo(e.target.checked)}
                className="w-3.5 h-3.5"
              />
              Xóa sạch cấu trúc cũ của kỳ thi
            </label>
            <button
              onClick={handleApDung}
              disabled={!kyThiChon || apDungBusy}
              className="px-4 py-1.5 text-xs bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {apDungBusy ? 'Đang áp dụng...' : 'Áp dụng'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
