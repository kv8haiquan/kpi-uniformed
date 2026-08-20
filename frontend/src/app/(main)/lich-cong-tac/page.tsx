/**
 * /lich-cong-tac/ — màn hình trung tâm của module Lịch công tác.
 *
 * Hai chế độ xem như lichkv8: lưới tháng và danh sách. Sự kiện nguồn HKG có
 * nhãn riêng và bấm được sang chi tiết cuộc họp trong Họp Không Giấy — đó là
 * tiêu chí 8.3 của yêu cầu chuyển đổi.
 *
 * Lọc và phân trang chạy phía máy chủ; hệ cũ tải hết vào bộ nhớ trình duyệt
 * nên chậm dần theo số lượng lịch.
 */

'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Download,
  ExternalLink,
  FileText,
  List,
  Loader2,
  MapPin,
  Plus,
  Search,
  Star,
  Users,
} from 'lucide-react';

import { lichCongTacApi } from '@/services/lich-cong-tac';
import FormLich from './components/FormLich';
import { errMsg } from '@/lib/hkg-error';
import {
  NHAN_LOAI_LICH,
  NHAN_TRANG_THAI,
  type ILichThang,
  type ISuKienLich,
  type LoaiLich,
  type TrangThaiLich,
} from '@/types/lich-cong-tac';

const MAU_LOAI: Record<LoaiLich, string> = {
  HOP: 'bg-blue-100 text-blue-800 border-blue-200',
  TRUC_BAN: 'bg-amber-100 text-amber-800 border-amber-200',
  HOI_NGHI: 'bg-purple-100 text-purple-800 border-purple-200',
  LAM_VIEC: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  CONG_TAC: 'bg-cyan-100 text-cyan-800 border-cyan-200',
  LICH_KHAC: 'bg-gray-100 text-gray-700 border-gray-200',
};

const MAU_TRANG_THAI: Record<TrangThaiLich, string> = {
  LEN_KE_HOACH: 'bg-gray-100 text-gray-700',
  DA_THONG_BAO: 'bg-blue-100 text-blue-800',
  DANG_DIEN_RA: 'bg-yellow-100 text-yellow-800',
  HOAN_THANH: 'bg-green-100 text-green-800',
  HUY: 'bg-red-100 text-red-800',
};

const THU_NGAN = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];

/** Thứ Hai đầu tuần — lịch Việt Nam, khác mặc định của Date (Chủ nhật). */
function thuTrongTuan(d: Date): number {
  return (d.getDay() + 6) % 7;
}

function gioNgan(gio?: string | null): string {
  return gio ? gio.slice(0, 5) : '';
}

function chuTri(sk: ISuKienLich): string {
  return sk.chu_toa?.ho_ten || sk.chu_tri_text || '';
}

export default function LichCongTacPage() {
  const homNay = useMemo(() => new Date(), []);

  // Trang Tổng quan trỏ về đây kèm khoảng ngày trên URL ("hôm nay", "trong
  // tuần"…). Đọc một lần lúc mở trang; sau đó người dùng đổi bộ lọc thì URL
  // không đổi theo — giữ URL đồng bộ hai chiều chỉ thêm phức tạp mà không ai
  // cần chia sẻ đường dẫn đã lọc.
  const qs = useSearchParams();
  const qsTuNgay = qs.get('tu-ngay') ?? '';
  const qsDenNgay = qs.get('den-ngay') ?? '';

  const [cheDo, setCheDo] = useState<'thang' | 'danh-sach'>(
    qs.get('che-do') === 'danh-sach' ? 'danh-sach' : 'thang',
  );
  const [nam, setNam] = useState(homNay.getFullYear());
  const [thang, setThang] = useState(homNay.getMonth() + 1);

  const [lichThang, setLichThang] = useState<ILichThang | null>(null);
  const [danhSach, setDanhSach] = useState<ISuKienLich[]>([]);
  const [tong, setTong] = useState(0);
  const [trang, setTrang] = useState(1);

  const [dangTai, setDangTai] = useState(true);
  const [loi, setLoi] = useState<string | null>(null);
  const [locLoai, setLocLoai] = useState<LoaiLich | ''>(
    (qs.get('loai-lich') as LoaiLich | null) ?? '',
  );
  const [tuNgay, setTuNgay] = useState(qsTuNgay);
  const [denNgay, setDenNgay] = useState(qsDenNgay);
  const [tuKhoa, setTuKhoa] = useState('');
  const [tuKhoaGui, setTuKhoaGui] = useState('');

  const [moForm, setMoForm] = useState(false);
  const [dangXuat, setDangXuat] = useState(false);

  const soDong = 30;

  const tai = useCallback(async () => {
    setDangTai(true);
    setLoi(null);
    try {
      if (cheDo === 'thang') {
        setLichThang(
          await lichCongTacApi.theoThang(nam, thang, {
            'loai-lich': locLoai || undefined,
          }),
        );
      } else {
        const resp = await lichCongTacApi.danhSach({
          'loai-lich': locLoai || undefined,
          'tim-kiem': tuKhoaGui || undefined,
          'tu-ngay': tuNgay || undefined,
          'den-ngay': denNgay || undefined,
          // Danh sách xếp ngày gần nhất lên đầu. Tăng dần là mở ra thấy tháng
          // 3 — dữ liệu cũ nhất — trong khi việc cần xem nằm quanh hôm nay.
          'moi-truoc': true,
          trang,
          'so-dong': soDong,
        });
        setDanhSach(resp.data.data);
        setTong(resp.data.pagination?.total_items ?? 0);
      }
    } catch (e) {
      setLoi(errMsg(e, 'Không tải được lịch công tác'));
    } finally {
      setDangTai(false);
    }
  }, [cheDo, nam, thang, locLoai, tuKhoaGui, tuNgay, denNgay, trang]);

  useEffect(() => {
    void tai();
  }, [tai]);

  const doiThang = (buoc: number) => {
    const m = thang + buoc;
    if (m < 1) {
      setThang(12);
      setNam(nam - 1);
    } else if (m > 12) {
      setThang(1);
      setNam(nam + 1);
    } else {
      setThang(m);
    }
  };

  /** Lưới tháng luôn bắt đầu từ thứ Hai của tuần chứa ngày 1. */
  const oLich = useMemo(() => {
    const dau = new Date(nam, thang - 1, 1);
    const lui = thuTrongTuan(dau);
    const batDau = new Date(nam, thang - 1, 1 - lui);
    return Array.from({ length: 42 }, (_, i) => {
      const d = new Date(batDau);
      d.setDate(batDau.getDate() + i);
      return d;
    });
  }, [nam, thang]);

  const khoaNgay = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
      d.getDate(),
    ).padStart(2, '0')}`;

  /** Xuất đúng phạm vi đang xem: chế độ tháng thì cả tháng, danh sách thì
   *  theo bộ lọc và từ khoá hiện tại. */
  const xuatExcel = async () => {
    setDangXuat(true);
    setLoi(null);
    try {
      const cuoiThang = new Date(nam, thang, 0).getDate();
      await lichCongTacApi.xuatExcel(
        cheDo === 'thang'
          ? {
              'tu-ngay': `${nam}-${String(thang).padStart(2, '0')}-01`,
              'den-ngay': `${nam}-${String(thang).padStart(2, '0')}-${cuoiThang}`,
              'loai-lich': locLoai || undefined,
            }
          : {
              'loai-lich': locLoai || undefined,
              'tim-kiem': tuKhoaGui || undefined,
            },
      );
    } catch (e) {
      setLoi(errMsg(e, 'Không xuất được Excel'));
    } finally {
      setDangXuat(false);
    }
  };

  const tongTrang = Math.max(1, Math.ceil(tong / soDong));

  return (
    <div className="space-y-4">
      {/* Thanh công cụ */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-lg border border-gray-300 overflow-hidden">
            <button
              type="button"
              onClick={() => setCheDo('thang')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-sm ${
                cheDo === 'thang'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              <CalendarDays className="w-4 h-4" />
              Lịch tháng
            </button>
            <button
              type="button"
              onClick={() => setCheDo('danh-sach')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-sm ${
                cheDo === 'danh-sach'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              <List className="w-4 h-4" />
              Danh sách
            </button>
          </div>

          <select
            value={locLoai}
            onChange={(e) => {
              setLocLoai(e.target.value as LoaiLich | '');
              setTrang(1);
            }}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm"
          >
            <option value="">Tất cả loại lịch</option>
            {(Object.keys(NHAN_LOAI_LICH) as LoaiLich[]).map((k) => (
              <option key={k} value={k}>
                {NHAN_LOAI_LICH[k]}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={() => setMoForm(true)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            Thêm lịch
          </button>

          <button
            type="button"
            onClick={xuatExcel}
            disabled={dangXuat}
            className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-40"
            title="Xuất đúng phạm vi đang xem"
          >
            {dangXuat ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            Xuất Excel
          </button>
        </div>

        {cheDo === 'thang' ? (
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => doiThang(-1)}
              aria-label="Tháng trước"
              className="p-1.5 rounded-lg border border-gray-300 hover:bg-gray-50"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="min-w-[9rem] text-center font-semibold">
              Tháng {thang} / {nam}
            </span>
            <button
              type="button"
              onClick={() => doiThang(1)}
              aria-label="Tháng sau"
              className="p-1.5 rounded-lg border border-gray-300 hover:bg-gray-50"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => {
                setNam(homNay.getFullYear());
                setThang(homNay.getMonth() + 1);
              }}
              className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 hover:bg-gray-50"
            >
              Hôm nay
            </button>
          </div>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              setTrang(1);
              setTuKhoaGui(tuKhoa);
            }}
            className="flex items-center gap-2"
          >
            <div className="relative">
              <Search className="w-4 h-4 absolute left-2.5 top-2.5 text-gray-400" />
              <input
                value={tuKhoa}
                onChange={(e) => setTuKhoa(e.target.value)}
                placeholder="Tìm nội dung, địa điểm, mã lịch…"
                className="w-72 rounded-lg border border-gray-300 pl-8 pr-3 py-1.5 text-sm"
              />
            </div>
            <button
              type="submit"
              className="px-3 py-1.5 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700"
            >
              Tìm
            </button>
          </form>
        )}
      </div>

      {cheDo === 'danh-sach' && (tuNgay || denNgay) && (
        <div className="rounded-lg bg-blue-50 border border-blue-200 px-4 py-2 text-sm text-blue-900">
          Đang xem lịch từ <b>{tuNgay || '…'}</b> đến <b>{denNgay || '…'}</b>
          <button
            type="button"
            onClick={() => {
              setTuNgay('');
              setDenNgay('');
              setTrang(1);
            }}
            className="ml-3 text-blue-700 hover:underline"
          >
            bỏ lọc khoảng ngày
          </button>
        </div>
      )}

      {loi && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {loi}
        </div>
      )}

      {dangTai ? (
        <div className="flex items-center justify-center py-16 text-gray-500">
          <Loader2 className="w-5 h-5 animate-spin mr-2" />
          Đang tải…
        </div>
      ) : cheDo === 'thang' ? (
        <div className="rounded-lg border border-gray-200 overflow-hidden bg-white">
          <div className="grid grid-cols-7 bg-gray-50 border-b border-gray-200">
            {THU_NGAN.map((t) => (
              <div
                key={t}
                className="px-2 py-2 text-center text-xs font-semibold text-gray-600"
              >
                {t}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-7">
            {oLich.map((d) => {
              const trongThang = d.getMonth() + 1 === thang;
              const laHomNay = khoaNgay(d) === khoaNgay(homNay);
              const suKien = lichThang?.theo_ngay[khoaNgay(d)] ?? [];
              return (
                <div
                  key={d.toISOString()}
                  className={`min-h-[7rem] border-b border-r border-gray-100 p-1.5 ${
                    trongThang ? 'bg-white' : 'bg-gray-50/60'
                  }`}
                >
                  <div
                    className={`text-xs mb-1 inline-flex items-center justify-center w-6 h-6 rounded-full ${
                      laHomNay
                        ? 'bg-blue-600 text-white font-semibold'
                        : trongThang
                          ? 'text-gray-700'
                          : 'text-gray-400'
                    }`}
                  >
                    {d.getDate()}
                  </div>
                  <div className="space-y-1">
                    {suKien.slice(0, 3).map((sk) => (
                      <Link
                        key={`${sk.id}-${khoaNgay(d)}`}
                        href={`/lich-cong-tac/${sk.id}`}
                        title={sk.tieu_de}
                        className={`block truncate rounded border px-1.5 py-0.5 text-[11px] leading-tight hover:brightness-95 ${
                          MAU_LOAI[sk.loai_lich ?? 'LICH_KHAC']
                        }`}
                      >
                        <span className="font-medium">
                          {gioNgan(sk.gio_bat_dau)}
                        </span>{' '}
                        {sk.tieu_de}
                      </Link>
                    ))}
                    {suKien.length > 3 && (
                      <div className="text-[11px] text-gray-500 pl-1">
                        +{suKien.length - 3} nữa
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <>
          <div className="rounded-lg border border-gray-200 overflow-hidden bg-white">
            {danhSach.length === 0 ? (
              <div className="py-16 text-center text-gray-500">
                Không có sự kiện nào khớp điều kiện lọc.
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {danhSach.map((sk) => (
                  <li key={sk.id} className="p-3 hover:bg-gray-50">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2 mb-1">
                          <span
                            className={`rounded border px-1.5 py-0.5 text-[11px] ${
                              MAU_LOAI[sk.loai_lich ?? 'LICH_KHAC']
                            }`}
                          >
                            {sk.loai_lich_nhan ?? 'Lịch khác'}
                          </span>
                          <span
                            className={`rounded px-1.5 py-0.5 text-[11px] ${
                              MAU_TRANG_THAI[sk.trang_thai]
                            }`}
                          >
                            {NHAN_TRANG_THAI[sk.trang_thai]}
                          </span>
                          {sk.ma_lich && (
                            <span className="text-[11px] font-mono text-gray-500">
                              {sk.ma_lich}
                            </span>
                          )}
                          {sk.co_the_mo_hkg && (
                            <span className="inline-flex items-center gap-1 rounded bg-indigo-50 px-1.5 py-0.5 text-[11px] text-indigo-700">
                              <ExternalLink className="w-3 h-3" />
                              Họp Không Giấy
                            </span>
                          )}
                        </div>

                        <Link
                          href={`/lich-cong-tac/${sk.id}`}
                          className="font-medium text-gray-900 hover:text-blue-700"
                        >
                          {sk.tieu_de}
                        </Link>

                        <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600">
                          <span>
                            {sk.ngay_hien_thi}
                            {sk.ngay_ket_thuc &&
                              sk.ngay_ket_thuc !== sk.ngay_hien_thi &&
                              ` → ${sk.ngay_ket_thuc}`}{' '}
                            · {gioNgan(sk.gio_bat_dau)}
                            {sk.gio_ket_thuc && `–${gioNgan(sk.gio_ket_thuc)}`}
                          </span>
                          {sk.dia_diem && (
                            <span className="inline-flex items-center gap-1">
                              <MapPin className="w-3 h-3" />
                              {sk.dia_diem}
                            </span>
                          )}
                          {chuTri(sk) && (
                            <span className="inline-flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              {chuTri(sk)}
                            </span>
                          )}
                          {sk.so_tai_lieu > 0 && (
                            <span className="inline-flex items-center gap-1">
                              <FileText className="w-3 h-3" />
                              {sk.so_tai_lieu} tài liệu
                            </span>
                          )}
                          {(sk.so_luot_cham ?? 0) > 0 && (
                            <span
                              className="inline-flex items-center gap-1 text-amber-700"
                              title={`Điểm công tác chuẩn bị — ${sk.so_luot_cham} lượt chấm`}
                            >
                              <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                              {sk.diem_chuan_bi?.toFixed(1)}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {tongTrang > 1 && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">
                {tong} sự kiện · trang {trang}/{tongTrang}
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={trang <= 1}
                  onClick={() => setTrang(trang - 1)}
                  className="px-3 py-1.5 rounded-lg border border-gray-300 disabled:opacity-40 hover:bg-gray-50"
                >
                  Trước
                </button>
                <button
                  type="button"
                  disabled={trang >= tongTrang}
                  onClick={() => setTrang(trang + 1)}
                  className="px-3 py-1.5 rounded-lg border border-gray-300 disabled:opacity-40 hover:bg-gray-50"
                >
                  Sau
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {moForm && (
        <FormLich
          onDong={() => setMoForm(false)}
          onXong={() => {
            setMoForm(false);
            void tai();
          }}
        />
      )}
    </div>
  );
}
