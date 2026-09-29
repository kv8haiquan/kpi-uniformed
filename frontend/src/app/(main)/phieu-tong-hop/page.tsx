/**
 * src/app/(main)/phieu-tong-hop/page.tsx
 * =======================================
 * TỔNG HỢP PHIẾU ĐÁNH GIÁ, XẾP LOẠI QUÝ (Mẫu 02A/02B) — TOÀN CHI CỤC, CHỈ ĐỌC.
 *
 * Trước 29/09/2026, phiếu chỉ nhìn được trong phạm vi DUYỆT: 439/450 phiếu quý III
 * chỉ mỗi Trưởng đơn vị của người đó thấy, còn TCCB — nơi phải tổng hợp hồ sơ nộp
 * ngày 23 tháng cuối quý — không xem được phiếu nào. Trang này lấp chỗ đó.
 *
 * Quyền: CCT / PCCT / TCCB / cờ `can_view_all_units`. Backend chặn bằng PHIEU_010;
 * phía này chỉ ẩn giao diện cho gọn. Trang KHÔNG có thao tác ghi — không duyệt,
 * không sửa; muốn duyệt vẫn vào trang Phiếu & bảng kê như cũ.
 */

'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ClipboardList,
  Download,
  FileDown,
  RefreshCw,
  Search,
  X,
} from 'lucide-react';

import { useAuthStore } from '@/stores/useAuthStore';
import { adminService } from '@/services/admin.service';
import { phieuDanhGiaService } from '@/services/phieu-danh-gia.service';
import { phieuTongHopService } from '@/services/phieu-tong-hop.service';
import { IDonViOption } from '@/types/admin';
import {
  IPhieuTongHopData,
  IPhieuTongHopItem,
  MaXepLoai,
  NHAN_TRANG_THAI_PHIEU,
  NHAN_XEP_LOAI,
  NHAN_XEP_LOAI_NGAN,
  TrangThaiPhieu,
} from '@/types/phieu-tong-hop';

const PAGE_SIZE = 50;

const STYLE_TRANG_THAI: Record<TrangThaiPhieu, string> = {
  NHAP: 'bg-gray-100 text-gray-700 border-gray-200',
  CHO_PHE_DUYET: 'bg-amber-50 text-amber-700 border-amber-200',
  DA_PHE_DUYET: 'bg-green-50 text-green-700 border-green-200',
  BI_TU_CHOI: 'bg-red-50 text-red-700 border-red-200',
};

const STYLE_XEP_LOAI: Record<MaXepLoai, string> = {
  HTXSNV: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  HTTNV: 'bg-blue-50 text-blue-700 border-blue-200',
  HTNV: 'bg-amber-50 text-amber-700 border-amber-200',
  KHTNV: 'bg-red-50 text-red-700 border-red-200',
};

function ngayGon(v: string | null): string {
  if (!v) return '—';
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('vi-VN');
}

export default function PhieuTongHopPage() {
  const { user } = useAuthStore();
  const now = new Date();

  const [quy, setQuy] = useState(Math.ceil((now.getMonth() + 1) / 3));
  const [nam, setNam] = useState(now.getFullYear());
  const [donViId, setDonViId] = useState('');
  const [trangThai, setTrangThai] = useState<TrangThaiPhieu | ''>('');
  const [xepLoai, setXepLoai] = useState<MaXepLoai | ''>('');
  const [timNhap, setTimNhap] = useState('');
  const [tim, setTim] = useState('');
  const [page, setPage] = useState(1);

  const [donViList, setDonViList] = useState<IDonViOption[]>([]);
  const [data, setData] = useState<IPhieuTongHopData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dangXuat, setDangXuat] = useState(false);
  const [dangTai, setDangTai] = useState<string | null>(null);
  const [chiTiet, setChiTiet] = useState<IPhieuTongHopItem | null>(null);

  const canView =
    user?.is_system_admin === true ||
    user?.can_view_all_units === true ||
    ['CCT', 'PCCT', 'TCCB'].includes(user?.vai_tro?.ma_vai_tro ?? '');

  const filter = useMemo(
    () => ({
      quy,
      nam,
      don_vi_id: donViId || undefined,
      trang_thai: (trangThai || undefined) as TrangThaiPhieu | undefined,
      xep_loai: (xepLoai || undefined) as MaXepLoai | undefined,
      tim: tim || undefined,
    }),
    [quy, nam, donViId, trangThai, xepLoai, tim],
  );

  const load = useCallback(async () => {
    if (!canView) return;
    try {
      setLoading(true);
      setError(null);
      const res = await phieuTongHopService.getTongHop({
        ...filter,
        page,
        page_size: PAGE_SIZE,
      });
      setData(res);
    } catch {
      setError('Không tải được tổng hợp phiếu. Vui lòng thử lại.');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [filter, page, canView]);

  useEffect(() => {
    if (!canView) return;
    adminService.getDonViList().then(setDonViList).catch(() => setDonViList([]));
  }, [canView]);

  useEffect(() => {
    load();
  }, [load]);

  // Đổi bộ lọc thì quay về trang 1, nếu không sẽ rơi vào trang trống.
  useEffect(() => {
    setPage(1);
  }, [quy, nam, donViId, trangThai, xepLoai, tim]);

  const handleExport = async () => {
    try {
      setDangXuat(true);
      await phieuTongHopService.exportExcel(filter);
    } catch {
      alert('Không tải được file Excel. Vui lòng thử lại.');
    } finally {
      setDangXuat(false);
    }
  };

  const taiBanIn = async (it: IPhieuTongHopItem, loai: 'phieu' | 'bang_ke') => {
    try {
      setDangTai(`${it.cong_chuc_id}-${loai}`);
      const blob =
        loai === 'phieu'
          ? await phieuDanhGiaService.downloadPhieuCuaCC(it.cong_chuc_id, quy, nam)
          : await phieuDanhGiaService.downloadBangKeCuaCC(it.cong_chuc_id, quy, nam);
      const maAnToan = it.ma_cc.replace('/', '-');
      const ten =
        loai === 'phieu'
          ? `PhieuDanhGia_${maAnToan}_Q${quy}_${nam}.docx`
          : `BangKeCongViec_${maAnToan}_Q${quy}_${nam}.docx`;
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = ten;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch {
      alert('Không tải được bản in của công chức này.');
    } finally {
      setDangTai(null);
    }
  };

  if (!canView) {
    return (
      <div className="min-h-screen bg-gray-50 py-10 px-4">
        <div className="max-w-2xl mx-auto bg-white border border-gray-200 rounded-xl p-8 text-center">
          <h1 className="text-lg font-semibold text-gray-900">Không có quyền truy cập</h1>
          <p className="text-gray-600 mt-2">
            Tổng hợp phiếu toàn Chi cục chỉ dành cho Chi cục trưởng, Phó Chi cục trưởng
            và TCCB. Trưởng đơn vị xem phiếu của đơn vị mình tại trang Phiếu &amp; bảng kê.
          </p>
        </div>
      </div>
    );
  }

  const th = data?.tong_hop;

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-[1400px] mx-auto space-y-5">
        {/* Header */}
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <ClipboardList className="w-6 h-6 text-indigo-600" />
              Tổng hợp phiếu đánh giá, xếp loại quý
            </h1>
            <p className="text-gray-600 text-sm mt-1">
              Mẫu 02A (công chức) / 02B (lãnh đạo) — toàn Chi cục, chỉ xem.
              Việc duyệt phiếu vẫn thực hiện ở trang Phiếu &amp; bảng kê.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={load}
              disabled={loading}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white hover:bg-gray-50 disabled:opacity-50 flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Tải lại
            </button>
            <button
              onClick={handleExport}
              disabled={dangXuat || !data?.items.length}
              className="px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              {dangXuat ? 'Đang xuất…' : 'Xuất Excel'}
            </button>
          </div>
        </div>

        {/* Bộ lọc */}
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <div className="grid grid-cols-1 md:grid-cols-6 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Quý</label>
              <select
                value={quy}
                onChange={(e) => setQuy(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                {[1, 2, 3, 4].map((q) => (
                  <option key={q} value={q}>Quý {q}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Năm</label>
              <select
                value={nam}
                onChange={(e) => setNam(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                {[now.getFullYear() - 1, now.getFullYear(), now.getFullYear() + 1].map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Đơn vị</label>
              <select
                value={donViId}
                onChange={(e) => setDonViId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value="">Tất cả đơn vị</option>
                {donViList.map((dv) => (
                  <option key={dv.id} value={dv.id}>{dv.ten_don_vi}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Trạng thái</label>
              <select
                value={trangThai}
                onChange={(e) => setTrangThai(e.target.value as TrangThaiPhieu | '')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value="">Tất cả</option>
                {(Object.keys(NHAN_TRANG_THAI_PHIEU) as TrangThaiPhieu[]).map((t) => (
                  <option key={t} value={t}>{NHAN_TRANG_THAI_PHIEU[t]}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Xếp loại</label>
              <select
                value={xepLoai}
                onChange={(e) => setXepLoai(e.target.value as MaXepLoai | '')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value="">Tất cả</option>
                {(Object.keys(NHAN_XEP_LOAI) as MaXepLoai[]).map((x) => (
                  <option key={x} value={x}>{NHAN_XEP_LOAI[x]}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Tìm</label>
              <div className="flex gap-1">
                <input
                  value={timNhap}
                  onChange={(e) => setTimNhap(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') setTim(timNhap); }}
                  placeholder="Họ tên hoặc mã CC"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
                <button
                  onClick={() => setTim(timNhap)}
                  className="px-3 py-2 border border-gray-300 rounded-lg bg-white hover:bg-gray-50"
                >
                  <Search className="w-4 h-4 text-gray-600" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Thống kê */}
        {th && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <The nhan="Tổng số" so={th.tong_so} mau="bg-white" />
            {(Object.keys(NHAN_TRANG_THAI_PHIEU) as TrangThaiPhieu[]).map((t) => (
              <The
                key={t}
                nhan={NHAN_TRANG_THAI_PHIEU[t]}
                so={th.theo_trang_thai[t] ?? 0}
                mau={STYLE_TRANG_THAI[t]}
              />
            ))}
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Bảng */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-3 py-3 text-left font-semibold text-gray-700 w-12">#</th>
                  <th className="px-3 py-3 text-left font-semibold text-gray-700">Mã CC</th>
                  <th className="px-3 py-3 text-left font-semibold text-gray-700">Họ tên</th>
                  <th className="px-3 py-3 text-left font-semibold text-gray-700">Đơn vị</th>
                  <th className="px-3 py-3 text-center font-semibold text-gray-700">Trạng thái</th>
                  <th className="px-3 py-3 text-center font-semibold text-gray-700">Xếp loại</th>
                  <th className="px-3 py-3 text-center font-semibold text-gray-700">Ngày duyệt</th>
                  <th className="px-3 py-3 text-center font-semibold text-gray-700 w-52">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {loading && (
                  <tr><td colSpan={8} className="px-3 py-10 text-center text-gray-500">Đang tải…</td></tr>
                )}
                {!loading && !data?.items.length && (
                  <tr><td colSpan={8} className="px-3 py-10 text-center text-gray-500">Không có dữ liệu</td></tr>
                )}
                {!loading && data?.items.map((it, i) => (
                  <tr key={it.cong_chuc_id} className="hover:bg-gray-50">
                    <td className="px-3 py-2 text-gray-500">
                      {(data.pagination.page - 1) * data.pagination.page_size + i + 1}
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">{it.ma_cc}</td>
                    <td className="px-3 py-2">
                      <div className="font-medium text-gray-900">{it.ho_ten}</div>
                      <div className="text-xs text-gray-500">{it.chuc_vu || '—'}</div>
                    </td>
                    <td className="px-3 py-2 text-gray-700">{it.don_vi_ten || '—'}</td>
                    <td className="px-3 py-2 text-center">
                      <span className={`inline-block px-2 py-0.5 rounded-full border text-xs ${STYLE_TRANG_THAI[it.trang_thai]}`}>
                        {NHAN_TRANG_THAI_PHIEU[it.trang_thai]}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-center">
                      {it.quyet_dinh_xep_loai ? (
                        <span
                          title={NHAN_XEP_LOAI[it.quyet_dinh_xep_loai]}
                          className={`inline-block px-2 py-0.5 rounded-full border text-xs ${STYLE_XEP_LOAI[it.quyet_dinh_xep_loai]}`}
                        >
                          {NHAN_XEP_LOAI_NGAN[it.quyet_dinh_xep_loai]}
                        </span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-center text-gray-600">{ngayGon(it.ngay_phe_duyet)}</td>
                    <td className="px-3 py-2">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => setChiTiet(it)}
                          disabled={!it.id}
                          className="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-40"
                          title={it.id ? 'Xem nội dung phiếu' : 'Công chức chưa soạn phiếu'}
                        >
                          Xem
                        </button>
                        <button
                          onClick={() => taiBanIn(it, 'phieu')}
                          disabled={dangTai !== null}
                          className="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-40 flex items-center gap-1"
                          title="Tải phiếu Mẫu 02"
                        >
                          <FileDown className="w-3 h-3" /> Phiếu
                        </button>
                        <button
                          onClick={() => taiBanIn(it, 'bang_ke')}
                          disabled={dangTai !== null}
                          className="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-40 flex items-center gap-1"
                          title="Tải bảng kê công việc"
                        >
                          <FileDown className="w-3 h-3" /> Bảng kê
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Phân trang */}
          {data && data.pagination.total_pages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 text-sm">
              <span className="text-gray-600">
                Trang {data.pagination.page}/{data.pagination.total_pages} ·{' '}
                {data.pagination.total_items} người
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={data.pagination.page <= 1}
                  className="px-3 py-1.5 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 disabled:opacity-40"
                >
                  Trước
                </button>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={data.pagination.page >= data.pagination.total_pages}
                  className="px-3 py-1.5 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 disabled:opacity-40"
                >
                  Sau
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modal xem nội dung phiếu */}
      {chiTiet && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-3xl w-full max-h-[85vh] overflow-y-auto">
            <div className="flex items-start justify-between px-6 py-4 border-b border-gray-200 sticky top-0 bg-white">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {chiTiet.ho_ten} <span className="text-gray-400 font-normal">· {chiTiet.ma_cc}</span>
                </h3>
                <p className="text-sm text-gray-500">
                  {chiTiet.chuc_vu || '—'} · {chiTiet.don_vi_ten || '—'} · Quý {chiTiet.quy}/{chiTiet.nam}
                  {' · '}Mẫu {chiTiet.is_lanh_dao ? '02B' : '02A'}
                </p>
              </div>
              <button onClick={() => setChiTiet(null)} className="p-1 hover:bg-gray-100 rounded">
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="px-6 py-4 space-y-4">
              <Muc nhan="Ưu điểm" noiDung={chiTiet.uu_diem} />
              <Muc nhan="Hạn chế, khuyết điểm" noiDung={chiTiet.han_che} />
              <Muc
                nhan="Cá nhân tự đề xuất xếp loại"
                noiDung={chiTiet.tu_de_xuat_xep_loai ? NHAN_XEP_LOAI[chiTiet.tu_de_xuat_xep_loai] : null}
              />
              <Muc nhan="Ý kiến người trực tiếp sử dụng" noiDung={chiTiet.y_kien_lanh_dao} />
              <Muc
                nhan="Người trực tiếp sử dụng đề xuất xếp loại"
                noiDung={chiTiet.de_xuat_xep_loai ? NHAN_XEP_LOAI[chiTiet.de_xuat_xep_loai] : null}
              />
              <Muc nhan="Ý kiến cấp có thẩm quyền" noiDung={chiTiet.y_kien_cap_tham_quyen} />
              <Muc
                nhan="Quyết định xếp loại"
                noiDung={chiTiet.quyet_dinh_xep_loai ? NHAN_XEP_LOAI[chiTiet.quyet_dinh_xep_loai] : null}
              />
              {chiTiet.is_lanh_dao && chiTiet.dd_quy_ke_khai != null && (
                <Muc
                  nhan="Kê khai lại chỉ số đ cấp quý (số liệu cũ, đã bỏ)"
                  noiDung={`${chiTiet.dd_quy_ke_khai}%${chiTiet.dd_quy_ghi_chu ? ` — ${chiTiet.dd_quy_ghi_chu}` : ''}`}
                />
              )}

              <div className="text-xs text-gray-500 border-t border-gray-100 pt-3">
                Gửi duyệt: {ngayGon(chiTiet.ngay_gui_duyet)} · Duyệt:{' '}
                {ngayGon(chiTiet.ngay_phe_duyet)}
                {chiTiet.nguoi_phe_duyet_ten ? ` bởi ${chiTiet.nguoi_phe_duyet_ten}` : ''}
              </div>
            </div>

            <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-2 sticky bottom-0 bg-white">
              <button
                onClick={() => taiBanIn(chiTiet, 'phieu')}
                className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
              >
                <FileDown className="w-4 h-4" /> Tải phiếu Mẫu 02
              </button>
              <button
                onClick={() => setChiTiet(null)}
                className="px-4 py-2 text-sm bg-gray-900 text-white rounded-lg hover:bg-gray-800"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function The({ nhan, so, mau }: { nhan: string; so: number; mau: string }) {
  return (
    <div className={`border rounded-xl px-4 py-3 ${mau}`}>
      <div className="text-xs opacity-80">{nhan}</div>
      <div className="text-2xl font-bold">{so}</div>
    </div>
  );
}

function Muc({ nhan, noiDung }: { nhan: string; noiDung: string | null }) {
  return (
    <div>
      <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
        {nhan}
      </div>
      <div className="text-sm text-gray-900 whitespace-pre-wrap bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 min-h-[38px]">
        {noiDung?.trim() || <span className="text-gray-400">Chưa có</span>}
      </div>
    </div>
  );
}
