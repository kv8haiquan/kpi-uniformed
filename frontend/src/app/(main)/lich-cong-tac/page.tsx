/**
 * /lich-cong-tac/ — màn hình trung tâm của module Lịch công tác.
 *
 * Bốn chế độ xem: lưới THÁNG, lưới TUẦN, chương trình một NGÀY và DANH SÁCH.
 * lichkv8 chỉ có tháng và danh sách; tuần/ngày thêm vào vì Văn phòng đọc
 * chương trình công tác theo tuần, còn lãnh đạo hỏi "hôm nay có gì" theo ngày.
 * Bấm vào một ngày ở lưới tháng hoặc lưới tuần là mở thẳng lịch ngày đó.
 *
 * Sự kiện nguồn HKG có nhãn riêng và bấm được sang chi tiết cuộc họp trong
 * Họp Không Giấy — đó là tiêu chí 8.3 của yêu cầu chuyển đổi.
 *
 * Lọc và phân trang chạy phía máy chủ; hệ cũ tải hết vào bộ nhớ trình duyệt
 * nên chậm dần theo số lượng lịch.
 */

'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import {
  CalendarClock,
  CalendarDays,
  CalendarRange,
  ChevronLeft,
  ChevronRight,
  Download,
  ExternalLink,
  FileText,
  List,
  Loader2,
  MapPin,
  Pencil,
  Plus,
  Search,
  Star,
  Users,
} from 'lucide-react';

import { lichCongTacApi } from '@/services/lich-cong-tac';
import FormLich from './components/FormLich';
import LichNgay from './components/LichNgay';
import LichTuan from './components/LichTuan';
import {
  MAU_TRANG_THAI,
  chuTri,
  mauLoai,
  suaDuocLich,
} from './components/lich-mau';
import { errMsg } from '@/lib/hkg-error';
import {
  dauTuan,
  gioNgan,
  homNayKhoa,
  ngayThangVN,
  ngayVN,
  nhanThu,
  themNgay,
  thuTrongTuan,
} from '@/lib/lich-ngay';
import {
  NHAN_LOAI_LICH,
  NHAN_TRANG_THAI,
  type ILichThang,
  type IQuyenLich,
  type ISuKienChiTiet,
  type ISuKienLich,
  type LoaiLich,
} from '@/types/lich-cong-tac';

const THU_NGAN = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];

type CheDo = 'thang' | 'tuan' | 'ngay' | 'danh-sach';

const CHE_DO_HOP_LE: CheDo[] = ['thang', 'tuan', 'ngay', 'danh-sach'];

export default function LichCongTacPage() {
  // Khoá ngày `YYYY-MM-DD` chứ không phải Date: chế độ tuần/ngày so sánh và
  // cộng ngày trên chuỗi, giữ nguyên một kiểu dữ liệu cho cả trang.
  const homNay = useMemo(() => homNayKhoa(), []);

  // Trang Tổng quan trỏ về đây kèm khoảng ngày trên URL ("hôm nay", "trong
  // tuần"…). Đọc một lần lúc mở trang; sau đó người dùng đổi bộ lọc thì URL
  // không đổi theo — giữ URL đồng bộ hai chiều chỉ thêm phức tạp mà không ai
  // cần chia sẻ đường dẫn đã lọc.
  const qs = useSearchParams();
  const qsTuNgay = qs.get('tu-ngay') ?? '';
  const qsDenNgay = qs.get('den-ngay') ?? '';
  const qsCheDo = qs.get('che-do') as CheDo | null;
  const qsNgay = qs.get('ngay') ?? '';

  const [cheDo, setCheDo] = useState<CheDo>(
    qsCheDo && CHE_DO_HOP_LE.includes(qsCheDo) ? qsCheDo : 'thang',
  );

  /** Ngày đang xem ở chế độ tuần/ngày — tuần lấy trọn tuần chứa ngày này. */
  const [ngayChon, setNgayChon] = useState(
    /^\d{4}-\d{2}-\d{2}$/.test(qsNgay) ? qsNgay : homNay,
  );

  const [nam, setNam] = useState(Number(homNay.slice(0, 4)));
  const [thang, setThang] = useState(Number(homNay.slice(5, 7)));

  const [lichThang, setLichThang] = useState<ILichThang | null>(null);
  const [danhSach, setDanhSach] = useState<ISuKienLich[]>([]);
  /** Sự kiện thô của khoảng đang xem ở chế độ tuần/ngày. */
  const [suKienKhoang, setSuKienKhoang] = useState<ISuKienLich[]>([]);
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

  // Sửa ngay trên danh sách. Mở form cần bản CHI TIẾT (ghi chú, thành phần
  // ghi tay không có trong danh sách), nên bấm Sửa thì nạp chi tiết trước —
  // mở bằng dữ liệu danh sách sẽ hiện ô Ghi chú trống trong khi thực tế có
  // nội dung, người dùng gõ đè lên là mất.
  const [quyen, setQuyen] = useState<IQuyenLich | null>(null);
  const [dangSua, setDangSua] = useState<ISuKienChiTiet | null>(null);
  const [dangMoSua, setDangMoSua] = useState<string | null>(null);

  const suaDuoc = (sk: ISuKienLich) => suaDuocLich(sk, quyen);

  const moSua = async (sk: ISuKienLich) => {
    setDangMoSua(sk.id);
    setLoi(null);
    try {
      setDangSua(await lichCongTacApi.chiTiet(sk.id));
      setMoForm(true);
    } catch (e) {
      setLoi(errMsg(e, 'Không mở được sự kiện để sửa'));
    } finally {
      setDangMoSua(null);
    }
  };

  const soDong = 30;

  /** Khoảng ngày của chế độ tuần/ngày — cũng là phạm vi xuất Excel. */
  const khoangDangXem = useMemo(() => {
    if (cheDo === 'tuan') {
      const bd = dauTuan(ngayChon);
      return { tu: bd, den: themNgay(bd, 6) };
    }
    return { tu: ngayChon, den: ngayChon };
  }, [cheDo, ngayChon]);

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
      } else if (cheDo === 'tuan' || cheDo === 'ngay') {
        // Một tuần nhiều nhất vài chục sự kiện — lấy trọn một lần rồi gom
        // theo ngày phía trình duyệt, không phân trang cho khỏi vỡ lưới.
        const resp = await lichCongTacApi.danhSach({
          'loai-lich': locLoai || undefined,
          'tu-ngay': khoangDangXem.tu,
          'den-ngay': khoangDangXem.den,
          trang: 1,
          'so-dong': 500,
        });
        setSuKienKhoang(resp.data.data);
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
  }, [cheDo, nam, thang, locLoai, tuKhoaGui, tuNgay, denNgay, trang,
      khoangDangXem]);

  useEffect(() => {
    void tai();
  }, [tai]);

  useEffect(() => {
    lichCongTacApi.quyenCuaToi().then(setQuyen).catch(() => setQuyen(null));
  }, []);

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

  /** Lùi/tiến một tuần (chế độ tuần) hoặc một ngày (chế độ ngày). */
  const doiNgay = (buoc: number) =>
    setNgayChon(themNgay(ngayChon, cheDo === 'tuan' ? buoc * 7 : buoc));

  /**
   * Bấm một ngày ở lưới tháng hoặc lưới tuần → mở lịch ngày đó. Đồng thời kéo
   * tháng đang xem theo, để bấm "Lịch tháng" quay lại là thấy đúng tháng chứa
   * ngày vừa xem chứ không nhảy về tháng cũ.
   */
  const moNgay = (khoa: string) => {
    setNgayChon(khoa);
    setNam(Number(khoa.slice(0, 4)));
    setThang(Number(khoa.slice(5, 7)));
    setCheDo('ngay');
  };

  /** Lưới tháng luôn bắt đầu từ thứ Hai của tuần chứa ngày 1. */
  const oLich = useMemo(() => {
    const dau = `${nam}-${String(thang).padStart(2, '0')}-01`;
    const batDau = themNgay(dau, -thuTrongTuan(dau));
    return Array.from({ length: 42 }, (_, i) => themNgay(batDau, i));
  }, [nam, thang]);

  /** Xuất đúng phạm vi đang xem: tháng/tuần/ngày thì theo khoảng ngày tương
   *  ứng, danh sách thì theo bộ lọc và từ khoá hiện tại. */
  const xuatExcel = async () => {
    setDangXuat(true);
    setLoi(null);
    try {
      const cuoiThang = new Date(nam, thang, 0).getDate();
      const dauThang = `${nam}-${String(thang).padStart(2, '0')}-01`;
      await lichCongTacApi.xuatExcel(
        cheDo === 'thang'
          ? {
              'tu-ngay': dauThang,
              'den-ngay': `${nam}-${String(thang).padStart(2, '0')}-${cuoiThang}`,
              'loai-lich': locLoai || undefined,
            }
          : cheDo === 'tuan' || cheDo === 'ngay'
            ? {
                'tu-ngay': khoangDangXem.tu,
                'den-ngay': khoangDangXem.den,
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
            {(
              [
                { ma: 'thang', nhan: 'Lịch tháng', Icon: CalendarDays },
                { ma: 'tuan', nhan: 'Lịch tuần', Icon: CalendarRange },
                { ma: 'ngay', nhan: 'Lịch ngày', Icon: CalendarClock },
                { ma: 'danh-sach', nhan: 'Danh sách', Icon: List },
              ] as { ma: CheDo; nhan: string; Icon: typeof CalendarDays }[]
            ).map(({ ma, nhan, Icon }) => (
              <button
                key={ma}
                type="button"
                onClick={() => setCheDo(ma)}
                className={`flex items-center gap-1.5 border-l border-gray-300 px-3 py-1.5 text-sm first:border-l-0 ${
                  cheDo === ma
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {nhan}
              </button>
            ))}
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
            onClick={() => {
              setDangSua(null);
              setMoForm(true);
            }}
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
                setNam(Number(homNay.slice(0, 4)));
                setThang(Number(homNay.slice(5, 7)));
              }}
              className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 hover:bg-gray-50"
            >
              Hôm nay
            </button>
          </div>
        ) : cheDo === 'tuan' || cheDo === 'ngay' ? (
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => doiNgay(-1)}
              aria-label={cheDo === 'tuan' ? 'Tuần trước' : 'Ngày trước'}
              className="p-1.5 rounded-lg border border-gray-300 hover:bg-gray-50"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="min-w-[15rem] text-center font-semibold">
              {cheDo === 'tuan'
                ? `Tuần ${ngayThangVN(khoangDangXem.tu)} – ${ngayVN(
                    khoangDangXem.den,
                  )}`
                : `${nhanThu(ngayChon)}, ${ngayVN(ngayChon)}`}
            </span>
            <button
              type="button"
              onClick={() => doiNgay(1)}
              aria-label={cheDo === 'tuan' ? 'Tuần sau' : 'Ngày sau'}
              className="p-1.5 rounded-lg border border-gray-300 hover:bg-gray-50"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => setNgayChon(homNay)}
              className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 hover:bg-gray-50"
            >
              Hôm nay
            </button>
            {/* Nhảy thẳng tới một ngày bất kỳ — nhanh hơn bấm mũi tên hàng
                chục lần khi cần xem lịch tháng sau. */}
            <input
              type="date"
              value={ngayChon}
              onChange={(e) => e.target.value && setNgayChon(e.target.value)}
              aria-label="Chọn ngày"
              className="rounded-lg border border-gray-300 px-2 py-1.5 text-sm"
            />
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
              const trongThang = Number(d.slice(5, 7)) === thang;
              const laHomNay = d === homNay;
              const suKien = lichThang?.theo_ngay[d] ?? [];
              return (
                <div
                  key={d}
                  className={`group relative min-h-[7rem] border-b border-r border-gray-100 p-1.5 ${
                    trongThang ? 'bg-white' : 'bg-gray-50/60'
                  }`}
                >
                  {/*
                    Cả ô ngày bấm được để xem lịch ngày đó. Nút phủ kín ô nằm
                    DƯỚI phần nội dung: lồng link sự kiện vào trong một nút là
                    sai ngữ nghĩa và bàn phím không đi qua được, còn để nút phủ
                    lên trên thì lại chặn mất link. Cách này giữ cả hai — bấm
                    chỗ trống mở cả ngày, bấm đúng sự kiện sang chi tiết.
                  */}
                  <button
                    type="button"
                    onClick={() => moNgay(d)}
                    aria-label={`Xem lịch ngày ${ngayVN(d)}`}
                    title={`Xem lịch ngày ${ngayVN(d)}`}
                    className="absolute inset-0 z-0 w-full cursor-pointer hover:bg-blue-50/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500"
                  />
                  <div
                    className={`pointer-events-none relative z-10 text-xs mb-1 inline-flex items-center justify-center w-6 h-6 rounded-full ${
                      laHomNay
                        ? 'bg-blue-600 text-white font-semibold'
                        : trongThang
                          ? 'text-gray-700 group-hover:text-blue-700'
                          : 'text-gray-400 group-hover:text-blue-700'
                    }`}
                  >
                    {Number(d.slice(8, 10))}
                  </div>
                  <div className="pointer-events-none relative z-10 space-y-1">
                    {suKien.slice(0, 3).map((sk) => (
                      <Link
                        key={`${sk.id}-${d}`}
                        href={`/lich-cong-tac/${sk.id}`}
                        title={sk.tieu_de}
                        className={`pointer-events-auto block truncate rounded border px-1.5 py-0.5 text-[11px] leading-tight hover:brightness-95 ${mauLoai(
                          sk.loai_lich,
                        )}`}
                      >
                        <span className="font-medium">
                          {gioNgan(sk.gio_bat_dau)}
                        </span>{' '}
                        {sk.tieu_de}
                      </Link>
                    ))}
                    {suKien.length > 3 && (
                      <div className="pl-1 text-[11px] text-gray-500 group-hover:text-blue-700 group-hover:underline">
                        +{suKien.length - 3} nữa — xem cả ngày
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : cheDo === 'tuan' ? (
        <LichTuan
          ngay={ngayChon}
          suKien={suKienKhoang}
          homNay={homNay}
          onChonNgay={moNgay}
        />
      ) : cheDo === 'ngay' ? (
        <LichNgay
          ngay={ngayChon}
          suKien={suKienKhoang}
          homNay={homNay}
          quyen={quyen}
          onLamMoi={() => void tai()}
        />
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
                            className={`rounded border px-1.5 py-0.5 text-[11px] ${mauLoai(
                              sk.loai_lich,
                            )}`}
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

                      {suaDuoc(sk) && (
                        <button
                          type="button"
                          title="Sửa sự kiện"
                          disabled={dangMoSua === sk.id}
                          onClick={() => void moSua(sk)}
                          className="shrink-0 rounded-lg border border-gray-300 p-1.5 text-gray-600 hover:bg-white hover:text-blue-700 disabled:opacity-40"
                        >
                          {dangMoSua === sk.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Pencil className="w-4 h-4" />
                          )}
                        </button>
                      )}
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
          banGhi={dangSua}
          onDong={() => {
            setMoForm(false);
            setDangSua(null);
          }}
          onXong={() => {
            setMoForm(false);
            setDangSua(null);
            void tai();
          }}
        />
      )}
    </div>
  );
}
