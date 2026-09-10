/**
 * src/app/(main)/admin/dieu-chuyen-hang-loat/page.tsx
 * ===================================================
 * Điều chuyển nhân sự HÀNG LOẠT theo quyết định, bằng file Excel. Chỉ Admin.
 *
 * Một quyết định điều động là MỘT sự kiện — một ngày hiệu lực, một danh sách
 * người. Nhập lẻ từng người qua modal đã dẫn tới: đợt 04/02/2026 bỏ quên trọn
 * 62 người, đợt 03/7 nhập được 1/3, và một đợt có ngày hiệu lực rải ra 6 ngày
 * vì nhập nhiều buổi.
 *
 * Ba bước: tải mẫu → xem trước → xác nhận ghi. Bước xem trước là bắt buộc và là
 * chỗ DUY NHẤT phát hiện được gõ nhầm mã CC — bảng dội lại họ tên + đơn vị hiện
 * tại của từng mã.
 */
'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';

import { isApiError } from '@/services/admin.service';
import {
  dieuChuyenHangLoatService,
  type IDongDieuChuyen,
  type IKetQuaGhiDieuChuyen,
  type IXemTruocDieuChuyen,
  type TrangThaiDongDieuChuyen,
} from '@/services/dieu-chuyen-hang-loat.service';
import { useAuthStore, useCurrentUser } from '@/stores/useAuthStore';

const TRANG_THAI_META: Record<
  TrangThaiDongDieuChuyen,
  { nhan: string; cls: string; icon: string }
> = {
  GHI_MOI: { nhan: 'Sẽ ghi', cls: 'bg-green-100 text-green-700', icon: '✓' },
  BO_QUA: { nhan: 'Bỏ qua', cls: 'bg-gray-100 text-gray-600', icon: '⏭' },
  LOI: { nhan: 'Lỗi', cls: 'bg-red-100 text-red-700', icon: '✕' },
};

function fmtNgay(s: string | null): string {
  return s ? new Date(s).toLocaleDateString('vi-VN') : '—';
}

export default function DieuChuyenHangLoatPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const user = useCurrentUser();
  const inputFileRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [xemTruoc, setXemTruoc] = useState<IXemTruocDieuChuyen | null>(null);
  const [ketQua, setKetQua] = useState<IKetQuaGhiDieuChuyen | null>(null);
  const [dangTaiMau, setDangTaiMau] = useState(false);
  const [dangDoc, setDangDoc] = useState(false);
  const [dangGhi, setDangGhi] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);
  const [chiHienLoi, setChiHienLoi] = useState(false);

  // Guard: chỉ admin
  useEffect(() => {
    if (!isAuthenticated) { router.replace('/login'); return; }
    if (user && !user.is_system_admin) { router.replace('/dashboard'); }
  }, [isAuthenticated, user, router]);

  const datLai = useCallback(() => {
    setFile(null);
    setXemTruoc(null);
    setKetQua(null);
    setLoi(null);
    setChiHienLoi(false);
    if (inputFileRef.current) inputFileRef.current.value = '';
  }, []);

  const handleTaiMau = async () => {
    setDangTaiMau(true);
    setLoi(null);
    try {
      await dieuChuyenHangLoatService.taiMauExcel();
    } catch (err) {
      setLoi(isApiError(err) ? err.message : 'Không tải được file mẫu');
    } finally {
      setDangTaiMau(false);
    }
  };

  const handleChonFile = async (f: File | null) => {
    setFile(f);
    setXemTruoc(null);
    setKetQua(null);
    setLoi(null);
    if (!f) return;

    setDangDoc(true);
    try {
      setXemTruoc(await dieuChuyenHangLoatService.xemTruoc(f));
    } catch (err) {
      setLoi(isApiError(err) ? err.message : 'Không đọc được file');
    } finally {
      setDangDoc(false);
    }
  };

  const handleGhi = async () => {
    if (!file || !xemTruoc) return;
    const dot = xemTruoc.tom_tat.cac_dot.map((d) => fmtNgay(d)).join(', ');
    const xacNhan = window.confirm(
      `Điều chuyển ${xemTruoc.tom_tat.se_ghi} công chức?\n\n` +
      `Ngày hiệu lực: ${dot}\n\n` +
      `Hãy chắc chắn bạn đã đối chiếu HỌ TÊN trong bảng xem trước.`
    );
    if (!xacNhan) return;

    setDangGhi(true);
    setLoi(null);
    try {
      const kq = await dieuChuyenHangLoatService.ghi(file);
      setKetQua(kq);
      setXemTruoc(null);
      setFile(null);
      if (inputFileRef.current) inputFileRef.current.value = '';
    } catch (err) {
      setLoi(isApiError(err) ? err.message : 'Có lỗi khi ghi');
    } finally {
      setDangGhi(false);
    }
  };

  const tomTat = xemTruoc?.tom_tat;
  const dongHienThi: IDongDieuChuyen[] = (xemTruoc?.cac_dong ?? []).filter(
    (d) => !chiHienLoi || d.trang_thai === 'LOI'
  );

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">
          🔄 Điều chuyển hàng loạt theo quyết định
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Một lần nhập cho cả đợt, thay vì mở modal từng người.
        </p>
      </div>

      {/* Bước 1 — tải mẫu */}
      <section className="bg-white border border-gray-200 rounded-xl p-5">
        <h2 className="font-medium text-gray-900 mb-1">Bước 1 — Tải file mẫu</h2>
        <p className="text-sm text-gray-600 mb-3">
          Mẫu có sẵn sheet <b>Danh sach cong chuc</b> để copy mã CC (đừng gõ tay)
          và sheet <b>Huong dan</b>. Chỉ điền vào sheet <b>Nhap lieu</b>.
        </p>
        <button
          onClick={handleTaiMau}
          disabled={dangTaiMau}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {dangTaiMau ? 'Đang tạo...' : '⬇ Tải file mẫu'}
        </button>
      </section>

      {/* Bước 2 — chọn file */}
      <section className="bg-white border border-gray-200 rounded-xl p-5">
        <h2 className="font-medium text-gray-900 mb-1">Bước 2 — Tải file đã điền lên</h2>
        <p className="text-sm text-gray-600 mb-3">
          Hệ thống đọc và đối chiếu, <b>chưa ghi gì</b> vào dữ liệu.
        </p>
        <div className="flex items-center gap-3 flex-wrap">
          <input
            ref={inputFileRef}
            type="file"
            accept=".xlsx"
            onChange={(e) => handleChonFile(e.target.files?.[0] ?? null)}
            className="text-sm file:mr-3 file:px-4 file:py-2 file:rounded-lg file:border-0
                       file:bg-gray-100 file:text-gray-700 hover:file:bg-gray-200"
          />
          {dangDoc && <span className="text-sm text-gray-500">Đang đọc file...</span>}
          {(file || xemTruoc || ketQua) && (
            <button onClick={datLai} className="text-sm text-gray-500 hover:text-gray-700 underline">
              Bắt đầu lại
            </button>
          )}
        </div>
      </section>

      {loi && (
        <div className="bg-red-50 border border-red-300 text-red-800 rounded-lg px-4 py-3 text-sm">
          {loi}
        </div>
      )}

      {ketQua && (
        <div className="bg-green-50 border border-green-300 text-green-900 rounded-lg px-4 py-3">
          <p className="font-medium">
            ✓ Đã điều chuyển {ketQua.so_da_ghi} công chức
            {ketQua.bo_qua > 0 && ` (bỏ qua ${ketQua.bo_qua} người đã ở đúng đơn vị)`}
          </p>
          <ul className="mt-2 text-sm space-y-0.5 max-h-60 overflow-y-auto">
            {ketQua.danh_sach.map((d) => (
              <li key={d.ma_cc}>
                {d.ma_cc} — {d.ho_ten} → {d.don_vi_den} ({fmtNgay(d.ngay_hieu_luc)})
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Bước 3 — xem trước */}
      {tomTat && (
        <section className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="p-5 border-b border-gray-200">
            <h2 className="font-medium text-gray-900 mb-3">Bước 3 — Đối chiếu rồi xác nhận</h2>

            {tomTat.loi_chung.length > 0 && (
              <div className="bg-red-50 border border-red-300 text-red-800 rounded-lg px-4 py-3 text-sm mb-3">
                {tomTat.loi_chung.map((x, i) => <p key={i}>{x}</p>)}
              </div>
            )}

            <div className="flex gap-4 flex-wrap text-sm">
              <span className="px-3 py-1.5 rounded-lg bg-green-100 text-green-800">
                Sẽ ghi: <b>{tomTat.se_ghi}</b>
              </span>
              <span className="px-3 py-1.5 rounded-lg bg-gray-100 text-gray-700">
                Bỏ qua: <b>{tomTat.bo_qua}</b>
              </span>
              <span className={`px-3 py-1.5 rounded-lg ${tomTat.loi > 0 ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-500'}`}>
                Lỗi: <b>{tomTat.loi}</b>
              </span>
              {tomTat.cac_dot.length > 0 && (
                <span className="px-3 py-1.5 rounded-lg bg-blue-50 text-blue-800">
                  Đợt: <b>{tomTat.cac_dot.map(fmtNgay).join(' · ')}</b>
                </span>
              )}
            </div>

            <div className="mt-3 bg-amber-50 border border-amber-300 text-amber-900 rounded-lg px-4 py-2 text-sm">
              ⚠️ <b>Đối chiếu cột Họ tên</b> trước khi xác nhận. Gõ nhầm một chữ số
              trong mã CC sẽ trỏ sang người khác, và đây là chỗ duy nhất phát hiện được.
            </div>

            {tomTat.loi > 0 && (
              <label className="flex items-center gap-2 mt-3 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={chiHienLoi}
                  onChange={(e) => setChiHienLoi(e.target.checked)}
                />
                Chỉ hiện dòng lỗi
              </label>
            )}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">Dòng</th>
                  <th className="px-3 py-2 text-left font-medium">Mã CC</th>
                  <th className="px-3 py-2 text-left font-medium">Họ tên</th>
                  <th className="px-3 py-2 text-left font-medium">Đơn vị hiện tại</th>
                  <th className="px-3 py-2 text-left font-medium">→ Đơn vị đến</th>
                  <th className="px-3 py-2 text-left font-medium">Ngày hiệu lực</th>
                  <th className="px-3 py-2 text-left font-medium">Trạng thái</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {dongHienThi.map((d) => {
                  const meta = TRANG_THAI_META[d.trang_thai];
                  return (
                    <tr key={d.dong_excel} className={d.trang_thai === 'LOI' ? 'bg-red-50/50' : ''}>
                      <td className="px-3 py-2 text-gray-400">{d.dong_excel}</td>
                      <td className="px-3 py-2 font-mono text-xs">{d.ma_cc || '—'}</td>
                      <td className="px-3 py-2 font-medium">{d.ho_ten || '—'}</td>
                      <td className="px-3 py-2 text-gray-600">{d.don_vi_hien_tai || '—'}</td>
                      <td className="px-3 py-2 text-blue-700">{d.don_vi_den || '—'}</td>
                      <td className="px-3 py-2">{fmtNgay(d.ngay_hieu_luc)}</td>
                      <td className="px-3 py-2">
                        <span className={`px-2 py-0.5 rounded text-xs ${meta.cls}`}>
                          {meta.icon} {meta.nhan}
                        </span>
                        {(d.loi.length > 0 || d.canh_bao.length > 0) && (
                          <div className="mt-1 space-y-0.5">
                            {d.loi.map((x, i) => (
                              <p key={`l${i}`} className="text-xs text-red-700">{x}</p>
                            ))}
                            {d.canh_bao.map((x, i) => (
                              <p key={`c${i}`} className="text-xs text-amber-700">{x}</p>
                            ))}
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {dongHienThi.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-3 py-6 text-center text-gray-400">
                      Không có dòng nào
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="p-5 border-t border-gray-200 flex items-center gap-3 flex-wrap">
            <button
              onClick={handleGhi}
              disabled={!tomTat.ghi_duoc || dangGhi}
              className="px-5 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700
                         disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {dangGhi ? 'Đang ghi...' : `Xác nhận điều chuyển ${tomTat.se_ghi} người`}
            </button>
            {!tomTat.ghi_duoc && tomTat.loi > 0 && (
              <span className="text-sm text-red-700">
                Còn {tomTat.loi} dòng lỗi — sửa file rồi tải lại. Hệ thống không ghi
                một phần.
              </span>
            )}
            {!tomTat.ghi_duoc && tomTat.loi === 0 && tomTat.se_ghi === 0 && (
              <span className="text-sm text-gray-500">Không có dòng nào cần ghi.</span>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
