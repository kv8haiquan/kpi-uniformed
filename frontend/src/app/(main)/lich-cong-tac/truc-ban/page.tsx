/**
 * /lich-cong-tac/truc-ban — bảng ma trận lịch trực ban.
 *
 * Hàng là ngày, cột là trụ sở, ô là người trực. Đây là cách Văn phòng vẫn đọc
 * nên giữ nguyên hình dạng đó.
 *
 * Ô trống KHÔNG bị ẩn đi: đó chính là chỗ chưa có ai trực, tức là chỗ Văn
 * phòng phải đi hỏi. Ẩn đi thì bảng nhìn đẹp mà mất đúng thông tin cần nhất.
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  Check,
  ClipboardCopy,
  Download,
  FileUp,
  Loader2,
  Lock,
  LockOpen,
  Plus,
  Printer,
  Trash2,
  Upload,
} from 'lucide-react';

import { trucBanApi, type Tuan } from '@/services/truc-ban';
import { errMsg } from '@/lib/hkg-error';
import type { IMaTranTruc, IOTruc } from '@/types/lich-cong-tac';
import FormNguoiTruc from '../components/FormNguoiTruc';
import NhapTrucBanExcel from '../components/NhapTrucBanExcel';

const NHAN_TUAN: Record<Tuan, string> = {
  truoc: 'Tuần trước',
  nay: 'Tuần này',
  sau: 'Tuần sau',
};

export default function TrucBanPage() {
  const [tuan, setTuan] = useState<Tuan>('nay');
  const [tuNgay, setTuNgay] = useState('');
  const [denNgay, setDenNgay] = useState('');
  const [tuChon, setTuChon] = useState(false);

  const [dl, setDl] = useState<IMaTranTruc | null>(null);
  const [dangTai, setDangTai] = useState(true);
  const [loi, setLoi] = useState<string | null>(null);
  const [daChep, setDaChep] = useState(false);
  const [dangXuat, setDangXuat] = useState(false);

  const [moNhap, setMoNhap] = useState(false);
  const [oDangThem, setODangThem] = useState<{
    ngay: string;
    tru_so_id: string;
    ten_tru_so: string;
  } | null>(null);

  const thamSo = useCallback(
    () =>
      tuChon && tuNgay && denNgay
        ? { 'tu-ngay': tuNgay, 'den-ngay': denNgay }
        : { tuan },
    [tuChon, tuNgay, denNgay, tuan],
  );

  const tai = useCallback(async () => {
    setDangTai(true);
    setLoi(null);
    try {
      setDl(await trucBanApi.maTran(thamSo()));
    } catch (e) {
      setLoi(errMsg(e, 'Không tải được bảng trực ban'));
    } finally {
      setDangTai(false);
    }
  }, [thamSo]);

  useEffect(() => {
    void tai();
  }, [tai]);

  const chep = async () => {
    try {
      const { van_ban } = await trucBanApi.vanBan(thamSo());
      if (!van_ban) {
        setLoi('Khoảng ngày này chưa có lịch trực để sao chép');
        return;
      }
      await navigator.clipboard.writeText(van_ban);
      setDaChep(true);
      setTimeout(() => setDaChep(false), 2000);
    } catch (e) {
      setLoi(errMsg(e, 'Không sao chép được'));
    }
  };

  const xuat = async () => {
    setDangXuat(true);
    try {
      await trucBanApi.xuatExcel(thamSo());
    } catch (e) {
      setLoi(errMsg(e, 'Không xuất được Excel'));
    } finally {
      setDangXuat(false);
    }
  };

  const nop = async (ngay: string, tru_so_id: string) => {
    if (
      !window.confirm(
        'Nộp chính thức lịch trực của ô này?\n\n' +
          'Sau khi nộp, đơn vị không tự sửa được nữa — muốn sửa phải nhờ Văn ' +
          'phòng mở khoá.',
      )
    ) {
      return;
    }
    try {
      await trucBanApi.nop(ngay, tru_so_id);
      void tai();
    } catch (e) {
      setLoi(errMsg(e, 'Không nộp được'));
    }
  };

  const moKhoa = async (ngay: string, tru_so_id: string) => {
    try {
      await trucBanApi.moKhoa(ngay, tru_so_id);
      void tai();
    } catch (e) {
      setLoi(errMsg(e, 'Không mở khoá được'));
    }
  };

  const xoaNguoi = async (id: string) => {
    if (!window.confirm('Xoá người trực này?')) return;
    try {
      await trucBanApi.xoa(id);
      void tai();
    } catch (e) {
      setLoi(errMsg(e, 'Không xoá được'));
    }
  };

  const nut =
    'inline-flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-40';

  return (
    <div className="space-y-4">
      {/* ── Thanh công cụ ─────────────────────────────────────────── */}
      <div className="flex flex-wrap items-end gap-3 print:hidden">
        <div className="inline-flex rounded-lg border border-gray-300 overflow-hidden">
          {(Object.keys(NHAN_TUAN) as Tuan[]).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => {
                setTuan(t);
                setTuChon(false);
              }}
              className={`px-3 py-1.5 text-sm ${
                !tuChon && tuan === t
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              {NHAN_TUAN[t]}
            </button>
          ))}
        </div>

        <label className="text-sm">
          <span className="block text-gray-600 mb-1">Từ ngày</span>
          <input
            type="date"
            value={tuNgay}
            onChange={(e) => {
              setTuNgay(e.target.value);
              setTuChon(true);
            }}
            className="rounded-lg border border-gray-300 px-3 py-1.5"
          />
        </label>

        <label className="text-sm">
          <span className="block text-gray-600 mb-1">Đến ngày</span>
          <input
            type="date"
            value={denNgay}
            onChange={(e) => {
              setDenNgay(e.target.value);
              setTuChon(true);
            }}
            className="rounded-lg border border-gray-300 px-3 py-1.5"
          />
        </label>

        <div className="ml-auto flex flex-wrap gap-2">
          <button type="button" onClick={chep} className={nut}>
            {daChep ? (
              <>
                <Check className="w-4 h-4" />
                Đã chép
              </>
            ) : (
              <>
                <ClipboardCopy className="w-4 h-4" />
                Sao chép
              </>
            )}
          </button>

          <button
            type="button"
            onClick={() => window.print()}
            className={nut}
          >
            <Printer className="w-4 h-4" />
            In
          </button>

          <button
            type="button"
            onClick={xuat}
            disabled={dangXuat}
            className={nut}
          >
            {dangXuat ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            Xuất Excel
          </button>

          <button
            type="button"
            onClick={() => trucBanApi.taiFileMau()}
            className={nut}
            title="File mẫu giữ nguyên như phần mềm lịch cũ"
          >
            <FileUp className="w-4 h-4" />
            File mẫu
          </button>

          <button
            type="button"
            onClick={() => setMoNhap(true)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700"
          >
            <Upload className="w-4 h-4" />
            Nhập Excel
          </button>
        </div>
      </div>

      {loi && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {loi}
        </div>
      )}

      {/* ── Bảng ma trận ──────────────────────────────────────────── */}
      {dangTai ? (
        <div className="flex items-center justify-center py-16 text-gray-500">
          <Loader2 className="w-5 h-5 animate-spin mr-2" />
          Đang tải…
        </div>
      ) : !dl ? null : (
        <div className="rounded-lg border border-gray-200 bg-white overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead className="bg-gray-50">
              <tr>
                <th className="sticky left-0 z-10 bg-gray-50 border border-gray-200 px-3 py-2 text-left font-medium w-32">
                  Ngày
                </th>
                {dl.tru_so.map((t) => (
                  <th
                    key={t.id}
                    className="border border-gray-200 px-3 py-2 text-left font-medium min-w-[200px]"
                  >
                    {t.ten_tru_so}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {dl.hang.map((h) => (
                <tr key={h.ngay} className={h.cuoi_tuan ? 'bg-amber-50/60' : ''}>
                  <td className="sticky left-0 z-10 border border-gray-200 px-3 py-2 align-top bg-inherit">
                    <div className="font-medium tabular-nums">
                      {h.ngay.split('-').reverse().join('/')}
                    </div>
                    <div className="text-xs text-gray-500">{h.thu}</div>
                  </td>

                  {h.o.map((o) => (
                    <OTruc
                      key={o.tru_so_id}
                      o={o}
                      ngay={h.ngay}
                      tenTruSo={
                        dl.tru_so.find((t) => t.id === o.tru_so_id)
                          ?.ten_tru_so ?? ''
                      }
                      laQuanTri={dl.la_quan_tri}
                      onThem={setODangThem}
                      onXoa={xoaNguoi}
                      onNop={nop}
                      onMoKhoa={moKhoa}
                    />
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-gray-500 print:hidden">
        Ô nền vàng là ngày cuối tuần. Ô có biểu tượng khoá là đã nộp chính thức
        — đơn vị không sửa được nữa, cần Văn phòng mở khoá.
      </p>

      {oDangThem && (
        <FormNguoiTruc
          ngay={oDangThem.ngay}
          truSoId={oDangThem.tru_so_id}
          tenTruSo={oDangThem.ten_tru_so}
          onDong={() => setODangThem(null)}
          onXong={() => {
            setODangThem(null);
            void tai();
          }}
        />
      )}

      {moNhap && (
        <NhapTrucBanExcel
          onDong={() => setMoNhap(false)}
          onXong={() => {
            setMoNhap(false);
            void tai();
          }}
        />
      )}
    </div>
  );
}

/** Một ô của ma trận: danh sách người trực + các nút thao tác. */
function OTruc({
  o,
  ngay,
  tenTruSo,
  laQuanTri,
  onThem,
  onXoa,
  onNop,
  onMoKhoa,
}: {
  o: IOTruc;
  ngay: string;
  tenTruSo: string;
  laQuanTri: boolean;
  onThem: (x: { ngay: string; tru_so_id: string; ten_tru_so: string }) => void;
  onXoa: (id: string) => void;
  onNop: (ngay: string, tru_so_id: string) => void;
  onMoKhoa: (ngay: string, tru_so_id: string) => void;
}) {
  const suaDuoc = o.sua_duoc && !o.is_locked;

  return (
    <td className="border border-gray-200 px-2 py-1.5 align-top">
      {o.nguoi.length === 0 ? (
        <span className="text-xs text-gray-400 italic">chưa phân công</span>
      ) : (
        <ul className="space-y-1">
          {o.nguoi.map((n) => (
            <li key={n.id} className="group flex items-start gap-1">
              <div className="flex-1">
                <div className="font-medium">{n.ho_ten}</div>
                <div className="text-xs text-gray-500">
                  {[n.chuc_vu, n.so_dien_thoai].filter(Boolean).join(' · ')}
                </div>
              </div>
              {suaDuoc && (
                <button
                  type="button"
                  onClick={() => onXoa(n.id)}
                  title="Xoá"
                  className="opacity-0 group-hover:opacity-100 text-red-600 p-0.5 print:hidden"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </li>
          ))}
        </ul>
      )}

      <div className="mt-1 flex items-center gap-2 print:hidden">
        {suaDuoc && (
          <button
            type="button"
            onClick={() => onThem({ ngay, tru_so_id: o.tru_so_id, ten_tru_so: tenTruSo })}
            className="inline-flex items-center gap-1 text-xs text-blue-700 hover:underline"
          >
            <Plus className="w-3.5 h-3.5" />
            Thêm
          </button>
        )}

        {o.is_locked ? (
          <span className="inline-flex items-center gap-1 text-xs text-gray-500">
            <Lock className="w-3.5 h-3.5" />
            Đã nộp
            {laQuanTri && (
              <button
                type="button"
                onClick={() => onMoKhoa(ngay, o.tru_so_id)}
                className="ml-1 inline-flex items-center gap-1 text-amber-700 hover:underline"
              >
                <LockOpen className="w-3.5 h-3.5" />
                Mở khoá
              </button>
            )}
          </span>
        ) : (
          o.sua_duoc &&
          o.nguoi.length > 0 && (
            <button
              type="button"
              onClick={() => onNop(ngay, o.tru_so_id)}
              className="text-xs text-green-700 hover:underline"
            >
              Nộp
            </button>
          )
        )}
      </div>
    </td>
  );
}
