/**
 * src/app/(main)/dao-tao/ky-thi/[id]/thong-ke/page.tsx
 * =====================================================
 * Trang thong ke ket qua ky thi — QT_DAO_TAO / Lanh dao.
 */

'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { kyThiApi } from '@/services/lms';
import type { IKyThi, IDgnlThongKe, IThiSinh, ILichSuThiSummary } from '@/types/lms';

/**
 * Kết quả 1 lần thi cụ thể của thí sinh để hiển thị ở cột Điểm/Xếp loại.
 * viewLan='all' -> lần mới nhất; viewLan=N -> lần N (lấy từ lich_su_thi hoặc ts.* nếu là lần hiện tại).
 */
function resolveKetQuaLan(
  ts: IThiSinh,
  viewLan: number | 'all',
): { diem: number | null; xepLoai: string | null; lan: number | null; hasData: boolean; hasChiTiet: boolean } {
  if (viewLan === 'all') {
    const ok = ts.trang_thai === 'DA_NOP';
    return { diem: ts.diem_tong, xepLoai: ts.xep_loai, lan: ts.lan_thi_hien_tai || null, hasData: ok, hasChiTiet: ok };
  }
  // Lần hiện tại (đã nộp) -> lấy từ ts.* trực tiếp, luôn xem được chi tiết
  if (viewLan === ts.lan_thi_hien_tai && ts.trang_thai === 'DA_NOP') {
    return { diem: ts.diem_tong, xepLoai: ts.xep_loai, lan: viewLan, hasData: true, hasChiTiet: true };
  }
  // Lần cũ -> tra trong lich_su_thi (chi tiết chỉ có nếu has_chi_tiet)
  const entry = (ts.lich_su_thi || []).find((e) => e.lan === viewLan);
  if (entry) {
    return { diem: entry.diem, xepLoai: entry.xep_loai, lan: viewLan, hasData: true, hasChiTiet: !!entry.has_chi_tiet };
  }
  return { diem: null, xepLoai: null, lan: viewLan, hasData: false, hasChiTiet: false };
}

export default function ThongKeKyThiPage() {
  const params = useParams();
  const kyThiId = params.id as string;

  const [kyThi, setKyThi] = useState<IKyThi | null>(null);
  const [thongKe, setThongKe] = useState<IDgnlThongKe | null>(null);
  const [thiSinh, setThiSinh] = useState<IThiSinh[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  // ID thi_sinh dang mo expand panel (xem lich su cac lan thi)
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  // Filter "xem theo lan": 'all' = lan moi nhat, hoac so lan cu the (1,2,3...)
  const [viewLan, setViewLan] = useState<number | 'all'>('all');

  // So lan thi toi da trong ky -> dung de render options dropdown
  const maxLan = useMemo(() => {
    let m = 0;
    for (const ts of thiSinh) {
      m = Math.max(m, ts.lan_thi_hien_tai || 0, ...(ts.lich_su_thi || []).map((e) => e.lan));
    }
    return m;
  }, [thiSinh]);

  const toggleExpand = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  useEffect(() => {
    const load = async () => {
      try {
        // Lấy toàn bộ thí sinh (tự phân trang hết) — bỏ giới hạn 200 cũ.
        const [ktRes, tkRes, allTs] = await Promise.all([
          kyThiApi.chiTiet(kyThiId),
          kyThiApi.thongKe(kyThiId),
          kyThiApi.danhSachThiSinhTatCa(kyThiId),
        ]);
        setKyThi(ktRes.data.data);
        setThongKe(tkRes.data.data);
        setThiSinh(allTs);
      } catch (err: any) {
        setError(err?.response?.data?.detail?.error?.message || 'Không thể tải thống kê');
      } finally {
        setLoading(false);
      }
    };
    if (kyThiId) load();
  }, [kyThiId]);

  const handleExport = async () => {
    setExporting(true);
    try {
      const res = await kyThiApi.exportExcel(kyThiId);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `ket_qua_${kyThi?.ma_ky_thi || kyThiId}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      alert('Lỗi khi export file');
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>
      </div>
    );
  }

  const tq = thongKe?.tong_quan;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Thống kê kỳ thi</h1>
          <p className="text-sm text-gray-500">{kyThi?.ten_ky_thi} ({kyThi?.ma_ky_thi})</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleExport}
            disabled={exporting}
            className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {exporting ? 'Đang xuất...' : 'Xuất Excel'}
          </button>
          <Link
            href="/dao-tao/ky-thi/quan-ly"
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Quay lại
          </Link>
        </div>
      </div>

      {/* Stat cards */}
      {tq && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 mb-6">
          <StatCard label="Tổng thí sinh" value={tq.tong_thi_sinh} color="blue" />
          <StatCard label="Đã thi" value={tq.da_thi} color="green" />
          <StatCard label="Chưa thi" value={tq.chua_thi} color="gray" />
          <StatCard label="Đạt" value={tq.dat} color="green" />
          <StatCard label="Không đạt" value={tq.khong_dat} color="red" />
          <StatCard label="Tỷ lệ đạt" value={`${tq.ti_le_dat}%`} color="purple" />
        </div>
      )}

      {/* Diem */}
      {tq && (
        <div className="grid grid-cols-3 gap-3 mb-6">
          <div className="bg-white border rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{tq.diem_trung_binh}</div>
            <div className="text-xs text-gray-500">Điểm trung bình</div>
          </div>
          <div className="bg-white border rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{tq.diem_cao_nhat}</div>
            <div className="text-xs text-gray-500">Điểm cao nhất</div>
          </div>
          <div className="bg-white border rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-red-600">{tq.diem_thap_nhat}</div>
            <div className="text-xs text-gray-500">Điểm thấp nhất</div>
          </div>
        </div>
      )}

      {/* Theo vi tri */}
      {thongKe?.theo_vi_tri && thongKe.theo_vi_tri.length > 0 && (
        <div className="bg-white rounded-xl border p-4 mb-6">
          <h3 className="font-semibold text-gray-700 mb-3">Theo vị trí</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="py-2 px-3">Vị trí</th>
                  <th className="py-2 px-3 text-center">Tổng</th>
                  <th className="py-2 px-3 text-center">Đạt</th>
                  <th className="py-2 px-3 text-center">Không đạt</th>
                  <th className="py-2 px-3 text-center">Điểm TB</th>
                </tr>
              </thead>
              <tbody>
                {thongKe.theo_vi_tri.map((vt, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="py-2 px-3 font-medium">{vt.vi_tri}</td>
                    <td className="py-2 px-3 text-center">{vt.tong}</td>
                    <td className="py-2 px-3 text-center text-green-600">{vt.dat}</td>
                    <td className="py-2 px-3 text-center text-red-600">{vt.khong_dat}</td>
                    <td className="py-2 px-3 text-center font-medium">{vt.diem_tb}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Theo don vi */}
      {thongKe?.theo_don_vi && thongKe.theo_don_vi.length > 0 && (
        <div className="bg-white rounded-xl border p-4 mb-6">
          <h3 className="font-semibold text-gray-700 mb-3">Theo đơn vị</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="py-2 px-3">Đơn vị</th>
                  <th className="py-2 px-3 text-center">Tổng</th>
                  <th className="py-2 px-3 text-center">Đạt</th>
                  <th className="py-2 px-3 text-center">Tỷ lệ đạt</th>
                  <th className="py-2 px-3 text-center">Điểm TB</th>
                </tr>
              </thead>
              <tbody>
                {thongKe.theo_don_vi.map((dv, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="py-2 px-3 font-medium">{dv.don_vi}</td>
                    <td className="py-2 px-3 text-center">{dv.tong}</td>
                    <td className="py-2 px-3 text-center text-green-600">{dv.dat}</td>
                    <td className="py-2 px-3 text-center">{dv.ti_le_dat}%</td>
                    <td className="py-2 px-3 text-center font-medium">{dv.diem_tb}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Danh sach thi sinh */}
      <div className="bg-white rounded-xl border p-4">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <h3 className="font-semibold text-gray-700">Danh sách thí sinh ({thiSinh.length})</h3>
          {maxLan > 1 && (
            <label className="flex items-center gap-2 text-sm text-gray-600">
              <span>Xem điểm theo:</span>
              <select
                value={viewLan}
                onChange={(e) => setViewLan(e.target.value === 'all' ? 'all' : Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-2 py-1 text-sm bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="all">Lần mới nhất</option>
                {Array.from({ length: maxLan }, (_, i) => i + 1).map((n) => (
                  <option key={n} value={n}>Lần {n}</option>
                ))}
              </select>
            </label>
          )}
        </div>
        {viewLan !== 'all' && (
          <div className="mb-3 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
            Đang xem điểm <strong>Lần {viewLan}</strong> của từng thí sinh. Ai chưa thi đến lần này hiển thị
            &ldquo;—&rdquo;. (Các thẻ thống kê phía trên vẫn tính theo lần mới nhất.)
          </div>
        )}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="py-2 px-2 w-8"></th>
                <th className="py-2 px-3">STT</th>
                <th className="py-2 px-3">Mã CC</th>
                <th className="py-2 px-3">Họ tên</th>
                <th className="py-2 px-3">Đơn vị</th>
                <th className="py-2 px-3">Vị trí</th>
                <th className="py-2 px-3 text-center">Trạng thái</th>
                <th className="py-2 px-3 text-center">Số lần</th>
                <th className="py-2 px-3 text-center">
                  {viewLan === 'all' ? 'Điểm' : `Điểm (Lần ${viewLan})`}
                </th>
                <th className="py-2 px-3 text-center">Xếp loại</th>
                <th className="py-2 px-3 text-center">Hành động</th>
              </tr>
            </thead>
            <tbody>
              {thiSinh.map((ts, idx) => {
                const lichSu = ts.lich_su_thi || [];
                const soLan = ts.trang_thai === 'DA_NOP'
                  ? Math.max(ts.lan_thi_hien_tai || 0, lichSu.length)
                  : lichSu.length;
                const coTheExpand = ts.trang_thai === 'DA_NOP' || lichSu.length > 0;
                const isOpen = expanded.has(ts.id);
                return (
                  <FragmentRow
                    key={ts.id}
                    ts={ts}
                    idx={idx}
                    kyThiId={kyThiId}
                    lichSu={lichSu}
                    soLan={soLan}
                    coTheExpand={coTheExpand}
                    isOpen={isOpen}
                    onToggle={() => toggleExpand(ts.id)}
                    viewLan={viewLan}
                  />
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function FragmentRow({
  ts, idx, kyThiId, lichSu, soLan, coTheExpand, isOpen, onToggle, viewLan,
}: {
  ts: IThiSinh;
  idx: number;
  kyThiId: string;
  lichSu: ILichSuThiSummary[];
  soLan: number;
  coTheExpand: boolean;
  isOpen: boolean;
  onToggle: () => void;
  viewLan: number | 'all';
}) {
  // Ket qua hien thi theo lan da chon (hoac lan moi nhat)
  const kq = resolveKetQuaLan(ts, viewLan);
  // Link "Xem bai lam": khi loc theo lan cu thi tro toi dung lan do
  const baiLamHref = viewLan === 'all' || viewLan === ts.lan_thi_hien_tai
    ? `/dao-tao/ky-thi/${kyThiId}/thi-sinh/${ts.cong_chuc_id}/bai-lam`
    : `/dao-tao/ky-thi/${kyThiId}/thi-sinh/${ts.cong_chuc_id}/bai-lam?lan=${viewLan}`;
  return (
    <>
      <tr className="border-b hover:bg-gray-50">
        <td className="py-2 px-2 text-center">
          {coTheExpand ? (
            <button
              type="button"
              onClick={onToggle}
              className="w-6 h-6 inline-flex items-center justify-center text-gray-500 hover:bg-gray-200 rounded"
              aria-label={isOpen ? 'Thu gọn' : 'Mở rộng lịch sử lần thi'}
              title={isOpen ? 'Thu gọn' : 'Xem các lần thi'}
            >
              <svg
                className={`w-3.5 h-3.5 transition-transform ${isOpen ? 'rotate-90' : ''}`}
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          ) : (
            <span className="text-gray-200">·</span>
          )}
        </td>
        <td className="py-2 px-3 text-gray-400">{idx + 1}</td>
        <td className="py-2 px-3 font-mono text-xs">{ts.ma_cc}</td>
        <td className="py-2 px-3 font-medium">{ts.ho_ten}</td>
        <td className="py-2 px-3 text-gray-600">{ts.don_vi_ten}</td>
        <td className="py-2 px-3">{ts.vi_tri_ten}</td>
        <td className="py-2 px-3 text-center">
          <TrangThaiBadge trangThai={ts.trang_thai} />
        </td>
        <td className="py-2 px-3 text-center text-xs text-gray-600">
          {soLan > 0 ? soLan : '-'}
        </td>
        <td className="py-2 px-3 text-center font-medium">
          {kq.hasData && kq.diem !== null ? `${kq.diem}%` : <span className="text-gray-300">—</span>}
        </td>
        <td className="py-2 px-3 text-center">
          {kq.hasData && kq.xepLoai ? (
            <span className={`px-2 py-0.5 rounded-full text-xs ${
              kq.xepLoai === 'DAT' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
            }`}>
              {kq.xepLoai === 'DAT' ? 'Đạt' : 'Không đạt'}
            </span>
          ) : (
            viewLan !== 'all' && <span className="text-gray-300 text-xs">chưa thi</span>
          )}
        </td>
        <td className="py-2 px-3 text-center">
          {kq.hasData && kq.hasChiTiet ? (
            <Link
              href={baiLamHref}
              className="text-blue-600 hover:text-blue-800 hover:underline text-xs font-medium inline-flex items-center gap-1"
              title={viewLan === 'all' ? 'Xem bài làm lần mới nhất' : `Xem bài làm lần ${viewLan}`}
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              Xem bài làm
            </Link>
          ) : kq.hasData && !kq.hasChiTiet ? (
            <span className="text-gray-400 text-xs" title="Lần thi cũ không lưu chi tiết câu trả lời">
              Không có chi tiết
            </span>
          ) : (
            <span className="text-gray-300 text-xs">—</span>
          )}
        </td>
      </tr>
      {isOpen && (
        <tr className="bg-gray-50/60 border-b">
          <td></td>
          <td colSpan={10} className="py-3 px-4">
            <LichSuLanThiPanel ts={ts} kyThiId={kyThiId} lichSu={lichSu} />
          </td>
        </tr>
      )}
    </>
  );
}

function LichSuLanThiPanel({
  ts, kyThiId, lichSu,
}: {
  ts: IThiSinh;
  kyThiId: string;
  lichSu: ILichSuThiSummary[];
}) {
  // Hop nhat lich su (lan cu) voi lan hien tai (neu da nop va chua co trong lich su).
  // Backend snapshot tai nop_bai -> luon co entry cho lan hien tai. Nhung guard de
  // backward-compat voi data cu khong co snapshot lan moi nhat.
  const rows: Array<{ lan: number; diem: number | null; xep_loai: string | null;
    so_cau_dung: number | null; tong_so_cau: number | null;
    thoi_gian_nop: string | null; has_chi_tiet: boolean; isCurrent: boolean; }> = [];

  const lanHienTai = ts.lan_thi_hien_tai || 0;
  const cuExistsInLichSu = lichSu.some((e) => e.lan === lanHienTai);

  // Cac lan cu tu lich_su_thi
  for (const e of lichSu) {
    rows.push({
      lan: e.lan,
      diem: e.diem,
      xep_loai: e.xep_loai,
      so_cau_dung: e.so_cau_dung,
      tong_so_cau: e.tong_so_cau,
      thoi_gian_nop: e.thoi_gian_nop,
      has_chi_tiet: e.has_chi_tiet,
      isCurrent: e.lan === lanHienTai,
    });
  }
  // Nếu chưa có entry cho lần hiện tại trong lich_su_thi (data cũ trước 30/05),
  // bổ sung 1 row "hiện tại" từ field ts.* trực tiếp.
  if (ts.trang_thai === 'DA_NOP' && lanHienTai > 0 && !cuExistsInLichSu) {
    rows.push({
      lan: lanHienTai,
      diem: ts.diem_tong,
      xep_loai: ts.xep_loai,
      so_cau_dung: ts.so_cau_dung,
      tong_so_cau: ts.tong_so_cau,
      thoi_gian_nop: ts.thoi_gian_nop,
      has_chi_tiet: false,  // entry chưa đc snapshot -> chi tiết chỉ ở ts.chi_tiet_tra_loi (latest endpoint vẫn lấy được)
      isCurrent: true,
    });
  }
  rows.sort((a, b) => b.lan - a.lan); // moi nhat truoc

  if (rows.length === 0) {
    return <div className="text-xs text-gray-500 italic">Chưa có dữ liệu lần thi.</div>;
  }

  return (
    <div>
      <div className="text-xs font-semibold text-gray-600 mb-2">Lịch sử các lần thi:</div>
      <table className="w-full text-xs">
        <thead>
          <tr className="text-left text-gray-500">
            <th className="py-1 px-2 w-16">Lần</th>
            <th className="py-1 px-2 text-center">Điểm</th>
            <th className="py-1 px-2 text-center">Xếp loại</th>
            <th className="py-1 px-2 text-center">Câu đúng</th>
            <th className="py-1 px-2">Thời gian nộp</th>
            <th className="py-1 px-2 text-center">Bài làm</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            // Lan hien tai luon co the xem qua endpoint /ket-qua/{ccId} hoac /ket-qua/{lan}.
            // Lan cu chi xem duoc khi has_chi_tiet=true.
            const xemDuoc = r.isCurrent || r.has_chi_tiet;
            const href = r.isCurrent
              ? `/dao-tao/ky-thi/${kyThiId}/thi-sinh/${ts.cong_chuc_id}/bai-lam`
              : `/dao-tao/ky-thi/${kyThiId}/thi-sinh/${ts.cong_chuc_id}/bai-lam?lan=${r.lan}`;
            return (
              <tr key={r.lan} className="border-t border-gray-200">
                <td className="py-1 px-2 font-semibold">
                  Lần {r.lan}
                  {r.isCurrent && (
                    <span className="ml-1 text-[10px] text-blue-600 font-normal">(mới nhất)</span>
                  )}
                </td>
                <td className="py-1 px-2 text-center font-medium">
                  {r.diem !== null && r.diem !== undefined ? `${r.diem}%` : '-'}
                </td>
                <td className="py-1 px-2 text-center">
                  {r.xep_loai && (
                    <span className={`px-1.5 py-0.5 rounded-full ${
                      r.xep_loai === 'DAT' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
                    }`}>
                      {r.xep_loai === 'DAT' ? 'Đạt' : 'Không đạt'}
                    </span>
                  )}
                </td>
                <td className="py-1 px-2 text-center text-gray-600">
                  {r.so_cau_dung ?? '-'}{r.tong_so_cau ? `/${r.tong_so_cau}` : ''}
                </td>
                <td className="py-1 px-2 text-gray-600">
                  {r.thoi_gian_nop
                    ? new Date(r.thoi_gian_nop).toLocaleString('vi-VN')
                    : '-'}
                </td>
                <td className="py-1 px-2 text-center">
                  {xemDuoc ? (
                    <Link
                      href={href}
                      className="text-blue-600 hover:text-blue-800 hover:underline"
                    >
                      Xem
                    </Link>
                  ) : (
                    <span className="text-gray-400" title="Lần thi cũ chưa lưu chi tiết câu trả lời">
                      Không có
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: number | string; color: string }) {
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    green: 'bg-green-50 text-green-700 border-green-200',
    red: 'bg-red-50 text-red-700 border-red-200',
    gray: 'bg-gray-50 text-gray-700 border-gray-200',
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
  };
  return (
    <div className={`${colorMap[color] || colorMap.blue} rounded-xl border p-3 text-center`}>
      <div className="text-xl font-bold">{value}</div>
      <div className="text-xs opacity-80">{label}</div>
    </div>
  );
}

function TrangThaiBadge({ trangThai }: { trangThai: string }) {
  const cfg: Record<string, { label: string; cls: string }> = {
    CHUA_THI: { label: 'Chưa thi', cls: 'bg-gray-100 text-gray-600' },
    DANG_THI: { label: 'Đang thi', cls: 'bg-blue-100 text-blue-700' },
    DA_NOP: { label: 'Đã nộp', cls: 'bg-green-100 text-green-700' },
    VANG: { label: 'Vắng', cls: 'bg-red-100 text-red-600' },
  };
  const c = cfg[trangThai] || cfg.CHUA_THI;
  return <span className={`${c.cls} px-2 py-0.5 rounded-full text-xs`}>{c.label}</span>;
}
