/**
 * /lich-cong-tac/thong-ke-tai-lieu — theo dõi đơn vị được giao chuẩn bị đã nộp
 * tài liệu hay chưa.
 *
 * Đây là công cụ thay cho việc Văn phòng rà từng lịch hoặc hỏi từng đơn vị.
 * Báo sai là đơn vị bị nhắc oan, nên hai điểm dưới đây phải hiện rõ trên màn
 * hình chứ không giấu trong logic:
 *
 *   - Cột "Tài liệu" đếm tài liệu CHUẨN BỊ, không đếm giấy mời. Cuộc họp chỉ
 *     nộp mỗi giấy mời vẫn là "Thiếu tài liệu".
 *   - "Chưa giao chuẩn bị" KHÁC "Thiếu tài liệu": chưa giao thì không có ai để
 *     nhắc, đó là việc của Văn phòng chứ không phải lỗi đơn vị.
 */

'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  AlertTriangle,
  Download,
  FileSpreadsheet,
  Loader2,
  Search,
} from 'lucide-react';

import { thongKeTaiLieuApi } from '@/services/lich-cong-tac';
import { errMsg } from '@/lib/hkg-error';
import type {
  IBaoCaoTaiLieu,
  TinhTrangTaiLieu,
} from '@/types/lich-cong-tac';

/** Ngày đầu và cuối tháng hiện tại — phạm vi mặc định khi mở trang. */
function thangNay(): { dau: string; cuoi: string } {
  const d = new Date();
  const iso = (x: Date) =>
    `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, '0')}-${String(
      x.getDate(),
    ).padStart(2, '0')}`;
  return {
    dau: iso(new Date(d.getFullYear(), d.getMonth(), 1)),
    cuoi: iso(new Date(d.getFullYear(), d.getMonth() + 1, 0)),
  };
}

const MAU_TINH_TRANG: Record<string, string> = {
  DA_GAN_TAI_LIEU: 'bg-green-100 text-green-800 border-green-200',
  THIEU_TAI_LIEU: 'bg-red-100 text-red-800 border-red-200',
  CHUA_GIAO_CHUAN_BI: 'bg-amber-100 text-amber-800 border-amber-200',
};

/** Thẻ tổng hợp, bấm vào là lọc luôn theo tình trạng đó. */
function TheTongHop({
  nhan,
  so,
  ma,
  dangChon,
  onChon,
  mau,
  ghiChu,
}: {
  nhan: string;
  so: number;
  ma: TinhTrangTaiLieu;
  dangChon: boolean;
  onChon: (ma: TinhTrangTaiLieu) => void;
  mau: string;
  ghiChu?: string;
}) {
  return (
    <button
      type="button"
      onClick={() => onChon(ma)}
      title={ghiChu}
      className={`flex-1 min-w-[150px] rounded-lg border px-4 py-3 text-left transition ${mau} ${
        dangChon ? 'ring-2 ring-blue-500 ring-offset-1' : 'hover:brightness-95'
      }`}
    >
      <div className="text-2xl font-bold tabular-nums">{so}</div>
      <div className="text-xs mt-0.5">{nhan}</div>
    </button>
  );
}

export default function ThongKeTaiLieuPage() {
  const mac = useMemo(thangNay, []);

  const [tuNgay, setTuNgay] = useState(mac.dau);
  const [denNgay, setDenNgay] = useState(mac.cuoi);
  const [tuKhoaNhap, setTuKhoaNhap] = useState('');
  const [tuKhoa, setTuKhoa] = useState('');
  const [tinhTrang, setTinhTrang] = useState<TinhTrangTaiLieu>('TAT_CA');
  const [tinhLichHuy, setTinhLichHuy] = useState(false);

  const [dl, setDl] = useState<IBaoCaoTaiLieu | null>(null);
  const [dangTai, setDangTai] = useState(true);
  const [dangXuat, setDangXuat] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);

  const thamSo = useCallback(
    () => ({
      'tu-ngay': tuNgay || undefined,
      'den-ngay': denNgay || undefined,
      'tu-khoa': tuKhoa || undefined,
      'tinh-trang': tinhTrang,
      'tinh-lich-huy': tinhLichHuy,
      'gioi-han': 2000,
    }),
    [tuNgay, denNgay, tuKhoa, tinhTrang, tinhLichHuy],
  );

  const tai = useCallback(async () => {
    setDangTai(true);
    setLoi(null);
    try {
      setDl(await thongKeTaiLieuApi.baoCao(thamSo()));
    } catch (e) {
      setLoi(errMsg(e, 'Không tải được báo cáo tài liệu'));
    } finally {
      setDangTai(false);
    }
  }, [thamSo]);

  useEffect(() => {
    void tai();
  }, [tai]);

  const xuatExcel = async () => {
    setDangXuat(true);
    setLoi(null);
    try {
      await thongKeTaiLieuApi.xuatExcel(thamSo());
    } catch (e) {
      setLoi(errMsg(e, 'Không xuất được Excel'));
    } finally {
      setDangXuat(false);
    }
  };

  const chonTinhTrang = (ma: TinhTrangTaiLieu) =>
    setTinhTrang((cu) => (cu === ma ? 'TAT_CA' : ma));

  const th = dl?.tong_hop;

  return (
    <div className="space-y-4">
      {/* ── Bộ lọc ─────────────────────────────────────────────────── */}
      <div className="rounded-lg border border-gray-200 bg-white p-4 print:hidden">
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-sm">
            <span className="block text-gray-600 mb-1">Từ ngày</span>
            <input
              type="date"
              value={tuNgay}
              onChange={(e) => setTuNgay(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-1.5"
            />
          </label>

          <label className="text-sm">
            <span className="block text-gray-600 mb-1">Đến ngày</span>
            <input
              type="date"
              value={denNgay}
              onChange={(e) => setDenNgay(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-1.5"
            />
          </label>

          <label className="text-sm flex-1 min-w-[220px]">
            <span className="block text-gray-600 mb-1">
              Tìm nội dung, mã lịch, đơn vị chuẩn bị, số văn bản
            </span>
            <div className="flex gap-2">
              <input
                type="text"
                value={tuKhoaNhap}
                onChange={(e) => setTuKhoaNhap(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') setTuKhoa(tuKhoaNhap.trim());
                }}
                placeholder="Gõ rồi Enter…"
                className="flex-1 rounded-lg border border-gray-300 px-3 py-1.5"
              />
              <button
                type="button"
                onClick={() => setTuKhoa(tuKhoaNhap.trim())}
                className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
              >
                <Search className="w-4 h-4" />
                Tìm
              </button>
            </div>
          </label>

          <label className="flex items-center gap-2 text-sm pb-1.5">
            <input
              type="checkbox"
              checked={tinhLichHuy}
              onChange={(e) => setTinhLichHuy(e.target.checked)}
            />
            Tính cả lịch đã huỷ
          </label>

          <button
            type="button"
            onClick={xuatExcel}
            disabled={dangXuat || !dl?.dong.length}
            className="ml-auto inline-flex items-center gap-1.5 rounded-lg bg-green-700 px-3 py-1.5 text-sm text-white hover:bg-green-800 disabled:opacity-40"
          >
            {dangXuat ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            Xuất Excel
          </button>
        </div>

        {tuKhoa && (
          <div className="mt-2 text-sm text-gray-600">
            Đang lọc theo từ khoá <b>{tuKhoa}</b>
            <button
              type="button"
              onClick={() => {
                setTuKhoa('');
                setTuKhoaNhap('');
              }}
              className="ml-2 text-blue-600 hover:underline"
            >
              bỏ lọc
            </button>
          </div>
        )}
      </div>

      {/* ── Tổng hợp ───────────────────────────────────────────────── */}
      {th && (
        <div className="flex flex-wrap gap-3">
          <TheTongHop
            nhan="Tất cả cuộc họp"
            so={th.tong}
            ma="TAT_CA"
            dangChon={tinhTrang === 'TAT_CA'}
            onChon={chonTinhTrang}
            mau="bg-gray-50 text-gray-800 border-gray-200"
            ghiChu="Đã loại lịch trực ban — trực ban không có nghĩa vụ chuẩn bị tài liệu"
          />
          <TheTongHop
            nhan="Đã gắn tài liệu"
            so={th.DA_GAN_TAI_LIEU}
            ma="DA_GAN_TAI_LIEU"
            dangChon={tinhTrang === 'DA_GAN_TAI_LIEU'}
            onChon={chonTinhTrang}
            mau={MAU_TINH_TRANG.DA_GAN_TAI_LIEU}
            ghiChu="Có đơn vị được giao và đã nộp ít nhất một tài liệu chuẩn bị"
          />
          <TheTongHop
            nhan="Thiếu tài liệu"
            so={th.THIEU_TAI_LIEU}
            ma="THIEU_TAI_LIEU"
            dangChon={tinhTrang === 'THIEU_TAI_LIEU'}
            onChon={chonTinhTrang}
            mau={MAU_TINH_TRANG.THIEU_TAI_LIEU}
            ghiChu="Đã giao đơn vị chuẩn bị nhưng chưa có tài liệu — đây là nhóm cần nhắc"
          />
          <TheTongHop
            nhan="Chưa giao chuẩn bị"
            so={th.CHUA_GIAO_CHUAN_BI}
            ma="CHUA_GIAO_CHUAN_BI"
            dangChon={tinhTrang === 'CHUA_GIAO_CHUAN_BI'}
            onChon={chonTinhTrang}
            mau={MAU_TINH_TRANG.CHUA_GIAO_CHUAN_BI}
            ghiChu="Chưa ghi đơn vị chuẩn bị — không có ai để nhắc, việc của Văn phòng"
          />
        </div>
      )}

      {loi && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {loi}
        </div>
      )}

      {/* ── Bảng ───────────────────────────────────────────────────── */}
      {dangTai ? (
        <div className="flex items-center justify-center py-16 text-gray-500">
          <Loader2 className="w-5 h-5 animate-spin mr-2" />
          Đang tải…
        </div>
      ) : !dl || dl.dong.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white py-16 text-center text-gray-500">
          Không có cuộc họp nào khớp bộ lọc.
        </div>
      ) : (
        <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-700">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">Mã lịch</th>
                  <th className="px-3 py-2 text-left font-medium">Ngày</th>
                  <th className="px-3 py-2 text-left font-medium">Nội dung</th>
                  <th className="px-3 py-2 text-left font-medium">Lãnh đạo</th>
                  <th className="px-3 py-2 text-left font-medium">
                    Đơn vị chuẩn bị
                  </th>
                  <th
                    className="px-3 py-2 text-right font-medium"
                    title="Chỉ đếm tài liệu chuẩn bị — giấy mời không tính"
                  >
                    Tài liệu
                  </th>
                  <th
                    className="px-3 py-2 text-right font-medium"
                    title="Số file được xếp là giấy mời"
                  >
                    Giấy mời
                  </th>
                  <th className="px-3 py-2 text-left font-medium">Tình trạng</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {dl.dong.map((d) => (
                  <tr key={d.id} className="hover:bg-gray-50">
                    <td className="px-3 py-2 whitespace-nowrap text-gray-500 tabular-nums">
                      {d.ma_lich || '—'}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap tabular-nums">
                      {d.ngay ? d.ngay.split('-').reverse().join('/') : '—'}
                      {d.gio_bat_dau && (
                        <span className="text-gray-500">
                          {' '}
                          {d.gio_bat_dau.slice(0, 5)}
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 max-w-md">
                      <Link
                        href={`/lich-cong-tac/${d.id}`}
                        className="text-blue-700 hover:underline"
                      >
                        {d.tieu_de}
                      </Link>
                      {d.trang_thai === 'HUY' && (
                        <span className="ml-2 text-xs text-red-600">(đã huỷ)</span>
                      )}
                      {d.so_van_ban && (
                        <div className="text-xs text-gray-500">
                          Số VB: {d.so_van_ban}
                        </div>
                      )}
                    </td>
                    <td className="px-3 py-2 text-gray-700">
                      {d.lanh_dao.length ? d.lanh_dao.join(', ') : d.chu_tri || '—'}
                    </td>
                    <td className="px-3 py-2 text-gray-700">
                      {d.don_vi_chuan_bi || (
                        <span className="text-gray-400 italic">chưa giao</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums font-medium">
                      {d.so_tai_lieu_chuan_bi}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums text-gray-500">
                      {d.so_giay_moi || ''}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap">
                      <span
                        className={`inline-block rounded border px-2 py-0.5 text-xs ${
                          MAU_TINH_TRANG[d.tinh_trang] ?? ''
                        }`}
                      >
                        {d.tinh_trang_nhan}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="border-t border-gray-200 bg-gray-50 px-4 py-2 text-xs text-gray-600">
            Hiện {dl.dong.length} dòng
            {dl.dong.length >= 2000 && (
              <span className="text-amber-700">
                {' '}
                — đã chạm mức 2000, thu hẹp khoảng ngày để xem đủ
              </span>
            )}
          </div>
        </div>
      )}

      {/* ── Chú thích quy tắc ──────────────────────────────────────── */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900 print:hidden">
        <div className="flex gap-2">
          <FileSpreadsheet className="w-4 h-4 mt-0.5 shrink-0" />
          <div>
            <b>Cột &ldquo;Tài liệu&rdquo; không đếm giấy mời.</b> Cuộc họp chỉ
            nộp mỗi giấy mời vẫn xếp là <i>Thiếu tài liệu</i>, vì nghĩa vụ của
            đơn vị được giao là nộp tài liệu chuẩn bị. Cách nhận biết giấy mời
            giữ nguyên như phần mềm lịch cũ.
          </div>
        </div>
        <div className="flex gap-2 mt-2">
          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
          <div>
            File đặt tên quá tắt có thể bị xếp nhầm. Gặp trường hợp đó thì mở
            cuộc họp và sửa trực tiếp — đừng nhắc đơn vị trước khi kiểm lại.
          </div>
        </div>
      </div>
    </div>
  );
}
