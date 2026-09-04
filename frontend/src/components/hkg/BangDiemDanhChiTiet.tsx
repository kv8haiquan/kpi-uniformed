/**
 * BangDiemDanhChiTiet — bảng điểm danh từng thành phần cuộc họp.
 *
 * Thêm 04/09/2026. Trước đó tab Điểm danh chỉ có 6 ô số tổng hợp: ban tổ chức
 * biết BAO NHIÊU người có mặt nhưng không biết là AI. Màn hình bấm điểm danh
 * tay cho thư ký cũng là nợ đã ghi trong HUONG_DAN_SU_DUNG_HKG.md §18/§25
 * ("chức năng phía máy chủ đã có" nhưng thiếu giao diện).
 *
 * Quyền: chỉ ban tổ chức + lãnh đạo xem-toàn-Chi-cục gọi được endpoint
 * /diem-danh/chi-tiet. Riêng quyền CHẤM TAY hẹp hơn quyền xem, nên dùng cờ
 * `co_the_bam_tay` do máy chủ trả về thay vì tự suy ở giao diện.
 */

'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Download, Loader2, Search } from 'lucide-react';

import { diemDanhApi } from '@/services/hkg';
// errApi (không phải errMsg) để lấy đúng câu tiếng Việt máy chủ soạn —
// errMsg với lỗi axios chỉ cho "Request failed with status code 403".
import { errApi } from '@/lib/hkg-error';
import { useMeeting } from '@/components/hkg/MeetingContext';
import {
  HINH_THUC_DIEM_DANH_LABELS,
  LOAI_THAM_DU_LABELS,
  NHAN_O_SO_DIEM_DANH,
  TRANG_THAI_DIEM_DANH_BADGE,
  TRANG_THAI_DIEM_DANH_LABELS,
  type IDiemDanhChiTiet,
  type IDiemDanhChiTietRow,
  type TrangThaiDiemDanh,
} from '@/types/hkg';

/** 'CHUA' là bộ lọc riêng cho người chưa có bản ghi điểm danh (trang_thai null). */
type BoLoc = TrangThaiDiemDanh | 'CHUA' | null;

const KHOA_O_SO: Array<{ khoa: keyof typeof NHAN_O_SO_DIEM_DANH; loc: BoLoc; mau: string }> = [
  { khoa: 'tong_so', loc: null, mau: 'text-gray-900' },
  { khoa: 'co_mat', loc: 'CO_MAT', mau: 'text-green-700' },
  { khoa: 'den_muon', loc: 'DEN_MUON', mau: 'text-yellow-700' },
  { khoa: 'vang_co_phep', loc: 'VANG_CO_PHEP', mau: 'text-blue-700' },
  { khoa: 'vang_khong_phep', loc: 'VANG_KHONG_PHEP', mau: 'text-red-700' },
  { khoa: 'chua_diem_danh', loc: 'CHUA', mau: 'text-gray-700' },
];

const TRANG_THAI_CHON: TrangThaiDiemDanh[] = [
  'CO_MAT', 'DEN_MUON', 'VANG_CO_PHEP', 'VANG_KHONG_PHEP',
];

/** Giờ lưu là mốc tuyệt đối — để trình duyệt tự đổi về giờ máy người xem. */
function gioNgan(iso: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
}

export default function BangDiemDanhChiTiet({
  cuocHopId,
  onSaved,
}: {
  cuocHopId: string;
  onSaved?: () => void;
}) {
  const { isLocked } = useMeeting();
  const [kq, setKq] = useState<IDiemDanhChiTiet | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState('');
  const [loc, setLoc] = useState<BoLoc>(null);
  const [donVi, setDonVi] = useState<string>('');
  const [dongBusy, setDongBusy] = useState<string | null>(null);
  const [dangXuat, setDangXuat] = useState(false);

  const reload = useCallback(async () => {
    try {
      setKq(await diemDanhApi.chiTiet(cuocHopId));
      setError(null);
    } catch (e: unknown) {
      setError(errApi(e, 'Không tải được bảng điểm danh'));
    } finally {
      setLoading(false);
    }
  }, [cuocHopId]);

  useEffect(() => {
    reload();
  }, [reload]);

  const danhSachLoc = useMemo(() => {
    const rows = kq?.danh_sach ?? [];
    const tu = q.trim().toLowerCase();
    return rows.filter((r) => {
      if (loc === 'CHUA' ? r.trang_thai !== null : loc && r.trang_thai !== loc) {
        return false;
      }
      if (donVi && r.don_vi_id !== donVi) return false;
      if (!tu) return true;
      return (
        (r.ho_ten ?? '').toLowerCase().includes(tu) ||
        (r.ma_cc ?? '').toLowerCase().includes(tu)
      );
    });
  }, [kq, q, loc, donVi]);

  /** Đơn vị có mặt trong thành phần — dựng từ dữ liệu, không gọi API riêng. */
  const dsDonVi = useMemo(() => {
    const m = new Map<string, string>();
    (kq?.danh_sach ?? []).forEach((r) => {
      if (r.don_vi_id) m.set(r.don_vi_id, r.ten_don_vi ?? r.don_vi_id);
    });
    return [...m.entries()].sort((a, b) => a[1].localeCompare(b[1], 'vi'));
  }, [kq]);

  const choChamTay = !!kq?.co_the_bam_tay && !isLocked;

  const handleCham = async (r: IDiemDanhChiTietRow, tt: TrangThaiDiemDanh) => {
    // Vắng thì phải có lý do — đây chính là thứ sẽ hiện ở cột "Lý do vắng",
    // vì luồng đơn xin phép vắng trên thực tế chưa được dùng.
    let ghi_chu: string | undefined;
    if (tt === 'VANG_CO_PHEP' || tt === 'VANG_KHONG_PHEP') {
      const nhap = window.prompt(
        `Lý do vắng của ${r.ho_ten ?? 'công chức'} (để trống nếu chưa rõ):`,
        r.ly_do_vang ?? '',
      );
      if (nhap === null) return; // bấm Cancel → không đổi gì
      ghi_chu = nhap;
    }

    setDongBusy(r.cong_chuc_id);
    setError(null);
    try {
      await diemDanhApi.bamTay(cuocHopId, [
        { cong_chuc_id: r.cong_chuc_id, trang_thai: tt, ghi_chu },
      ]);
      await reload();
      onSaved?.();
    } catch (e: unknown) {
      setError(errApi(e, 'Không thể chấm điểm danh'));
    } finally {
      setDongBusy(null);
    }
  };

  const handleXuatExcel = async () => {
    setDangXuat(true);
    setError(null);
    try {
      await diemDanhApi.xuatExcel(cuocHopId);
    } catch (e: unknown) {
      setError(errApi(e, 'Không xuất được Excel'));
    } finally {
      setDangXuat(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500 py-4">
        <Loader2 className="w-4 h-4 animate-spin" />
        Đang tải bảng điểm danh...
      </div>
    );
  }

  if (!kq) {
    return (
      <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
        {error ?? 'Không tải được bảng điểm danh'}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* 6 ô số — bấm để lọc bảng bên dưới */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        {KHOA_O_SO.map(({ khoa, loc: locO, mau }) => {
          const dangChon = loc === locO;
          return (
            <button
              key={khoa}
              type="button"
              onClick={() => setLoc(dangChon ? null : locO)}
              aria-pressed={dangChon}
              className={`rounded border p-3 text-center transition ${
                dangChon
                  ? 'bg-blue-50 border-blue-400 ring-1 ring-blue-400'
                  : 'bg-gray-50 hover:bg-gray-100'
              }`}
            >
              <div className={`text-2xl font-bold ${mau}`}>
                {kq.tong_hop[khoa]}
              </div>
              <div className="text-xs text-gray-600 mt-1">
                {NHAN_O_SO_DIEM_DANH[khoa]}
              </div>
            </button>
          );
        })}
      </div>

      {/* Thanh lọc */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <Search className="w-4 h-4 text-gray-400 absolute left-2 top-2.5" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Tìm theo họ tên hoặc mã CC"
            className="pl-8 pr-3 py-2 border rounded text-sm w-64"
          />
        </div>
        {dsDonVi.length > 1 && (
          <select
            value={donVi}
            onChange={(e) => setDonVi(e.target.value)}
            className="px-2 py-2 border rounded text-sm"
          >
            <option value="">Tất cả đơn vị</option>
            {dsDonVi.map(([id, ten]) => (
              <option key={id} value={id}>{ten}</option>
            ))}
          </select>
        )}
        {(loc || q || donVi) && (
          <button
            type="button"
            onClick={() => { setLoc(null); setQ(''); setDonVi(''); }}
            className="px-3 py-2 text-sm text-gray-600 border rounded hover:bg-gray-50"
          >
            Bỏ lọc
          </button>
        )}
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs text-gray-500">
            {danhSachLoc.length}/{kq.danh_sach.length} người
          </span>
          <button
            type="button"
            onClick={handleXuatExcel}
            disabled={dangXuat}
            className="inline-flex items-center gap-2 px-3 py-2 border rounded text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            {dangXuat
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Download className="w-4 h-4" />}
            Xuất Excel
          </button>
        </div>
      </div>

      {/* Bảng — cuộn ngang riêng để thân trang không bao giờ trôi ngang */}
      <div className="border border-gray-200 rounded overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-700 text-left">
            <tr>
              <th className="px-3 py-2 font-medium w-10">#</th>
              <th className="px-3 py-2 font-medium">Họ tên</th>
              <th className="px-3 py-2 font-medium">Đơn vị</th>
              <th className="px-3 py-2 font-medium">Tham dự</th>
              <th className="px-3 py-2 font-medium">Trạng thái</th>
              <th className="px-3 py-2 font-medium">Giờ</th>
              <th className="px-3 py-2 font-medium">Hình thức</th>
              {choChamTay && <th className="px-3 py-2 font-medium">Chấm</th>}
            </tr>
          </thead>
          <tbody>
            {danhSachLoc.length === 0 && (
              <tr>
                <td
                  colSpan={choChamTay ? 8 : 7}
                  className="px-3 py-6 text-center text-gray-500"
                >
                  {kq.danh_sach.length === 0
                    ? 'Cuộc họp chưa có thành phần nào.'
                    : 'Không có ai khớp bộ lọc hiện tại.'}
                </td>
              </tr>
            )}
            {danhSachLoc.map((r, i) => (
              <tr key={r.cong_chuc_id} className="border-t border-gray-100 align-top">
                <td className="px-3 py-2 text-gray-500">{i + 1}</td>
                <td className="px-3 py-2">
                  <div className="font-medium text-gray-900">{r.ho_ten ?? '—'}</div>
                  <div className="text-xs text-gray-500">
                    {r.ma_cc ?? ''}{r.chuc_vu ? ` · ${r.chuc_vu}` : ''}
                  </div>
                </td>
                <td className="px-3 py-2 text-gray-700">{r.ten_don_vi ?? '—'}</td>
                <td className="px-3 py-2 text-gray-600 text-xs">
                  {LOAI_THAM_DU_LABELS[r.loai_tham_du] ?? r.loai_tham_du}
                </td>
                <td className="px-3 py-2">
                  {r.trang_thai ? (
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                        TRANG_THAI_DIEM_DANH_BADGE[r.trang_thai]
                      }`}
                    >
                      {TRANG_THAI_DIEM_DANH_LABELS[r.trang_thai]}
                    </span>
                  ) : (
                    <span className="inline-block px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600">
                      Chưa điểm danh
                    </span>
                  )}
                  {r.ly_do_vang && (
                    <div className="text-xs text-gray-500 mt-1 max-w-xs">
                      ↳ {r.ly_do_vang}
                      {r.nguon_ly_do === 'DON_XIN_PHEP' && (
                        <span className="text-blue-600"> (đơn xin phép)</span>
                      )}
                    </div>
                  )}
                </td>
                <td className="px-3 py-2 text-gray-700 whitespace-nowrap">
                  {gioNgan(r.gio_diem_danh)}
                </td>
                <td className="px-3 py-2 text-gray-600 text-xs">
                  {r.hinh_thuc ? HINH_THUC_DIEM_DANH_LABELS[r.hinh_thuc] : '—'}
                  {r.nguoi_diem_danh_ho_ten && (
                    <div className="text-gray-400">
                      bởi {r.nguoi_diem_danh_ho_ten}
                    </div>
                  )}
                </td>
                {choChamTay && (
                  <td className="px-3 py-2">
                    {dongBusy === r.cong_chuc_id ? (
                      <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
                    ) : (
                      <select
                        aria-label={`Chấm điểm danh cho ${r.ho_ten ?? r.ma_cc ?? ''}`}
                        value={r.trang_thai ?? ''}
                        onChange={(e) =>
                          handleCham(r, e.target.value as TrangThaiDiemDanh)
                        }
                        className="px-2 py-1 border rounded text-xs"
                      >
                        <option value="" disabled>Chọn…</option>
                        {TRANG_THAI_CHON.map((tt) => (
                          <option key={tt} value={tt}>
                            {TRANG_THAI_DIEM_DANH_LABELS[tt]}
                          </option>
                        ))}
                      </select>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
