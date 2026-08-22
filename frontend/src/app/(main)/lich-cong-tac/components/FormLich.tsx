/**
 * Form tạo / sửa một sự kiện lịch công tác — G4.3.
 *
 * Dùng chung cho cả hai việc: truyền `banGhi` thì là sửa, không truyền là tạo.
 *
 * Khi sửa, chỉ gửi lên những trường thật sự đổi. Backend dùng PATCH và ghi
 * nhật ký từng trường, nên gửi thừa sẽ đẻ ra nhật ký rác — người đọc không
 * phân biệt được lần nào sửa thật.
 */

'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { FileText, Loader2, Paperclip, Trash2, X } from 'lucide-react';

import { lichCongTacApi } from '@/services/lich-cong-tac';
import { taiLieuApi } from '@/services/hkg';
import { errApi, errMsg } from '@/lib/hkg-error';
import { danhMucLichApi } from '@/services/danh-muc-lich';
import {
  ACCEPT_FILE,
  LOAI_TAI_LIEU,
  coDaiFile,
  gopFile,
  loiFile,
  moTaFileHong,
  taiNhieuFile,
  type FileCho,
} from '@/lib/tai-lieu-upload';
import type {
  IMucPhanQuyen,
  ITaiLieuListItem,
  PhanQuyenTaiLieu,
} from '@/types/hkg';
import type {
  IDanhMucLoai,
  IDonVi,
  ILanhDaoChon,
  ILichCongTacGhi,
  ISuKienChiTiet,
  LoaiLich,
} from '@/types/lich-cong-tac';
import ChonLanhDao from './ChonLanhDao';

interface Props {
  /** Có giá trị là đang sửa; bỏ trống là tạo mới. */
  banGhi?: ISuKienChiTiet | null;
  /** Ngày điền sẵn khi tạo mới từ ô ngày trên lịch tháng. */
  ngayMacDinh?: string;
  onDong: () => void;
  onXong: (sk: ISuKienChiTiet) => void;
}

type Truong = keyof ILichCongTacGhi;

const oCss =
  'w-full rounded-lg border border-gray-300 px-3 py-1.5 focus:border-blue-500 focus:outline-none';

/**
 * Một ô nhập kèm nhãn.
 *
 * Phải khai báo NGOÀI component cha: khai báo bên trong thì mỗi lần vẽ lại là
 * một kiểu component mới, React tháo input cũ và gắn input mới, gõ được một ký
 * tự là mất con trỏ.
 */
function O({
  nhan,
  children,
  rong,
}: {
  nhan: string;
  children: React.ReactNode;
  rong?: boolean;
}) {
  return (
    <label className={`text-sm ${rong ? 'sm:col-span-2' : ''}`}>
      <span className="block text-gray-600 mb-1">{nhan}</span>
      {children}
    </label>
  );
}

/** Giá trị rỗng trên form về `null` — để xoá được nội dung đã nhập trước đó. */
function chuanHoa(v: string): string | null {
  const t = v.trim();
  return t === '' ? null : t;
}

export default function FormLich({
  banGhi,
  ngayMacDinh,
  onDong,
  onXong,
}: Props) {
  const dangSua = Boolean(banGhi);

  const [loai, setLoai] = useState<IDanhMucLoai[]>([]);
  const [donVi, setDonVi] = useState<IDonVi[]>([]);
  const [lanhDao, setLanhDao] = useState<ILanhDaoChon[]>([]);
  const [phongHop, setPhongHop] = useState<string[]>([]);
  const [dangLuu, setDangLuu] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);

  // Chủ trì và Thành phần đều chọn từ danh mục lãnh đạo (55 người), không gõ
  // tay: chọn thì nối được sang chương trình công tác của từng lãnh đạo, gõ
  // tay thì không. Vẫn giữ hai ô ghi tay bên cạnh cho hai trường hợp danh mục
  // không diễn đạt được: người ngoài Chi cục (8/498 sự kiện di trú) và thành
  // phần theo nhóm ("Các đ/c UV BTV, BCH Đảng ủy").
  const thanhPhanBanDau = useMemo(
    () => (banGhi?.lanh_dao_lien_quan ?? []).map((x) => x.id),
    [banGhi],
  );
  const [thanhPhanIds, setThanhPhanIds] = useState<string[]>(thanhPhanBanDau);

  // ── tài liệu đính kèm ───────────────────────────────────────────────
  // Lúc TẠO MỚI chưa có id cuộc họp để tải file lên, nên file đứng xếp hàng ở
  // đây rồi tải lên ngay sau khi lưu xong. Lúc SỬA cũng xếp hàng cho giống
  // nhau — một đường đi duy nhất, dễ đoán hơn là tải ngay khi chọn.
  // Mỗi file mang LOẠI RIÊNG của nó (G4.11). Ô chọn phía trên chỉ là loại
  // mặc định gán cho file mới thả vào — chọn xong vẫn sửa lại từng dòng được,
  // nên nộp giấy mời và báo cáo trong cùng một lượt là chuyện bình thường.
  const [fileCho, setFileCho] = useState<FileCho[]>([]);
  const [daCo, setDaCo] = useState<ITaiLieuListItem[]>([]);
  const [dsLoai, setDsLoai] =
    useState<Array<{ ma: string; nhan: string }>>(LOAI_TAI_LIEU);
  // Giữ MÃ, không giữ nhãn — nhãn đổi được nên lưu nhãn là mất liên kết.
  const [loaiTaiLieu, setLoaiTaiLieu] = useState(LOAI_TAI_LIEU[0].ma);
  const [mucList, setMucList] = useState<IMucPhanQuyen[]>([]);
  const [mucTaiLieu, setMucTaiLieu] = useState<PhanQuyenTaiLieu>('CONG_KHAI');
  const [dangTaiFile, setDangTaiFile] = useState<string[]>([]);
  const [keoVao, setKeoVao] = useState(false);
  const oFile = useRef<HTMLInputElement>(null);

  // Sự kiện đã tạo xong nhưng còn file hỏng: giữ lại để bấm Lưu lần nữa là
  // tải nốt file, KHÔNG đẻ thêm một lịch trùng. Trước đây form vẫn ở chế độ
  // "tạo mới" sau khi lịch đã lưu, nên thử lại là tạo ra lịch thứ hai.
  // Để ở state chứ không phải ref vì nhãn nút Lưu đọc giá trị này lúc vẽ.
  const [daTao, setDaTao] = useState<ISuKienChiTiet | null>(null);
  /** Ảnh chụp form lúc lịch được tạo xong — mốc so sánh cho lần thử lại. */
  const mocSoSanh = useRef<Record<Truong, string> | null>(null);
  const thanhPhanDaLuu = useRef<string[] | null>(null);

  const banDau = useMemo<Record<Truong, string>>(
    () => ({
      tieu_de: banGhi?.tieu_de ?? '',
      loai_lich: (banGhi?.loai_lich as LoaiLich) ?? 'HOP',
      ngay_hop: banGhi?.ngay_hop ?? ngayMacDinh ?? '',
      ngay_ket_thuc: banGhi?.ngay_ket_thuc ?? '',
      ngay_hien_thi: banGhi?.ngay_hien_thi ?? '',
      gio_bat_dau: (banGhi?.gio_bat_dau ?? '08:00:00').slice(0, 5),
      gio_ket_thuc: (banGhi?.gio_ket_thuc ?? '').slice(0, 5),
      dia_diem: banGhi?.dia_diem ?? '',
      mo_ta: banGhi?.mo_ta ?? '',
      chu_tri_text: banGhi?.chu_tri_text ?? '',
      thanh_phan_text: banGhi?.thanh_phan_text ?? '',
      don_vi_chuan_bi: banGhi?.don_vi_chuan_bi ?? '',
      so_van_ban: banGhi?.so_van_ban ?? '',
      trang_thai: banGhi?.trang_thai ?? 'LEN_KE_HOACH',
      chu_toa_id: banGhi?.chu_toa?.id ?? '',
      lanh_dao_lien_quan_ids: '',
    }),
    [banGhi, ngayMacDinh],
  );

  // Form được gắn mới mỗi lần mở (cha bật/tắt bằng cờ) nên lấy giá trị đầu
  // một lần là đủ — không cần useEffect đồng bộ lại.
  const [form, setForm] = useState(banDau);

  useEffect(() => {
    lichCongTacApi.danhMuc().then(setLoai).catch(() => setLoai([]));
    lichCongTacApi.danhMucDonVi().then(setDonVi).catch(() => setDonVi([]));
    lichCongTacApi.danhMucLanhDao().then(setLanhDao).catch(() => setLanhDao([]));
    lichCongTacApi
      .danhMucPhongHop()
      .then(setPhongHop)
      .catch(() => setPhongHop([]));
    taiLieuApi.mucPhanQuyen().then(setMucList).catch(() => setMucList([]));
    // Loại tài liệu nay do đơn vị tự quản trị (G4.11). Gọi hỏng thì giữ 7 mục
    // gieo sẵn — thà chọn được loại cũ còn hơn ô chọn rỗng.
    danhMucLichApi
      .danhSach({ nhom: 'LOAI_TAI_LIEU' })
      .then((ds) => {
        if (ds.length === 0) return;
        const muc = ds.map((m) => ({ ma: m.ma, nhan: m.nhan }));
        setDsLoai(muc);
        setLoaiTaiLieu(muc[0].ma);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!banGhi) return;
    taiLieuApi.listByCuocHop(banGhi.id).then(setDaCo).catch(() => setDaCo([]));
  }, [banGhi]);

  const dat = (k: Truong, v: string) => setForm((f) => ({ ...f, [k]: v }));

  /**
   * Nhận file từ ô chọn hoặc từ kéo thả.
   *
   * Chụp `FileList` thành mảng ngay trong `gopFile`, đồng bộ — xem ghi chú ở
   * `lib/tai-lieu-upload.ts`: chậm một nhịp là ô chọn file đã tự dọn sạch.
   */
  const themFile = (ds: FileList | File[] | null) => {
    const moi = Array.from(ds ?? []);
    if (moi.length === 0) return;

    // Báo ngay file nào không nhận, chứ không để người dùng bấm Lưu rồi mới
    // biết — lúc đó lịch đã tạo, sửa lại phiền hơn nhiều.
    const hong = moi
      .map((f) => ({ ten: f.name, loi: loiFile(f) }))
      .filter((x): x is { ten: string; loi: string } => x.loi !== null);
    setLoi(
      hong.length > 0
        ? `Không nhận ${hong.length} file: ${moTaFileHong(hong)}`
        : null,
    );

    const dung = moi.filter((f) => loiFile(f) === null);
    setFileCho((truoc) => gopFile(truoc, dung, loaiTaiLieu));
  };

  const xoaFileCho = (i: number) =>
    setFileCho((truoc) => truoc.filter((_, j) => j !== i));

  /** Đổi loại của riêng một file trong hàng đợi. */
  const doiLoaiFile = (i: number, loai: string) =>
    setFileCho((truoc) =>
      truoc.map((x, j) => (j === i ? { ...x, loai } : x)),
    );

  const xoaFileDaCo = async (tl: ITaiLieuListItem) => {
    if (!window.confirm(`Xoá tài liệu "${tl.ten_tai_lieu}"?`)) return;
    try {
      await taiLieuApi.xoa(tl.id);
      setDaCo((truoc) => truoc.filter((x) => x.id !== tl.id));
    } catch (e) {
      setLoi(errApi(e, 'Không xoá được tài liệu'));
    }
  };

  const luu = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoi(null);

    if (!form.tieu_de.trim()) return setLoi('Chưa nhập nội dung');
    if (!form.ngay_hop) return setLoi('Chưa chọn ngày');
    if (
      form.ngay_ket_thuc &&
      form.ngay_ket_thuc < form.ngay_hop
    ) {
      return setLoi('Ngày kết thúc không được trước ngày bắt đầu');
    }

    // Chỉ những trường đổi so với mốc: lúc mở form nếu đang sửa, hoặc lúc lịch
    // được tạo xong nếu đang thử lại file hỏng. Tạo mới lần đầu thì gửi tất.
    const moc = dangSua ? banDau : mocSoSanh.current;
    const goi: ILichCongTacGhi = {};
    (Object.keys(form) as Truong[]).forEach((k) => {
      if (k === 'lanh_dao_lien_quan_ids') return;
      if (moc && form[k] === moc[k]) return;
      const v = form[k];
      if (k === 'tieu_de' || k === 'loai_lich' || k === 'ngay_hop') {
        (goi as Record<string, unknown>)[k] = v;
      } else if (k === 'gio_bat_dau') {
        goi.gio_bat_dau = `${v}:00`;
      } else if (k === 'gio_ket_thuc') {
        goi.gio_ket_thuc = v ? `${v}:00` : null;
      } else if (k === 'trang_thai') {
        (goi as Record<string, unknown>)[k] = v;
      } else if (k === 'chu_toa_id') {
        goi.chu_toa_id = v || null;
      } else {
        (goi as Record<string, unknown>)[k] = chuanHoa(v);
      }
    });

    // Danh sách lãnh đạo tham dự nằm ở bảng riêng nên so sánh riêng: chỉ gửi
    // khi thật sự đổi, kể cả đổi thứ tự — backend ghi đè cả danh sách và giữ
    // đúng thứ tự người dùng chọn.
    const mocThanhPhan = dangSua ? thanhPhanBanDau : thanhPhanDaLuu.current;
    const doiThanhPhan =
      mocThanhPhan === null
        ? thanhPhanIds.length > 0
        : thanhPhanIds.length !== mocThanhPhan.length ||
          thanhPhanIds.some((id, i) => id !== mocThanhPhan[i]);
    if (doiThanhPhan) goi.lanh_dao_lien_quan_ids = thanhPhanIds;

    if (dangSua && Object.keys(goi).length === 0 && fileCho.length === 0) {
      onDong();
      return;
    }

    setDangLuu(true);
    try {
      // Ba đường: sửa bản có sẵn, thử lại trên lịch vừa tạo ở lần bấm trước,
      // hoặc tạo mới. Hai đường đầu đều là PATCH nên gộp chung id.
      const idCoSan = dangSua ? banGhi!.id : daTao?.id;
      let sk: ISuKienChiTiet;
      if (idCoSan) {
        // Vẫn gửi thay đổi nếu người dùng sửa gì đó trước khi thử lại —
        // bỏ qua thì sửa xong bấm Lưu lại thấy như không có gì xảy ra.
        sk =
          Object.keys(goi).length === 0
            ? ((dangSua ? banGhi : daTao) as ISuKienChiTiet)
            : await lichCongTacApi.capNhat(idCoSan, goi);
      } else {
        sk = await lichCongTacApi.tao(goi);
      }
      if (!dangSua) {
        setDaTao(sk);
        mocSoSanh.current = { ...form };
        thanhPhanDaLuu.current = [...thanhPhanIds];
      }

      // Tải file SAU khi đã lưu: lúc tạo mới chưa có id cuộc họp để gắn vào.
      // Lịch đã lưu rồi thì file hỏng cũng không được nuốt lịch — báo đúng
      // file nào hỏng và giữ form mở để người dùng thử lại.
      if (fileCho.length > 0) {
        const hong = await taiNhieuFile({
          cuocHopId: sk.id,
          files: fileCho,
          phanQuyen: mucTaiLieu,
          onDoiDangTai: setDangTaiFile,
        });
        if (hong.length > 0) {
          const tenHong = new Set(hong.map((h) => h.ten));
          setLoi(
            `Đã lưu lịch, nhưng ${hong.length}/${fileCho.length} file không ` +
              `tải lên được: ${moTaFileHong(hong)}. Bấm Lưu lần nữa để thử lại ` +
              '— lịch sẽ không bị tạo trùng.',
          );
          setFileCho((truoc) => truoc.filter((x) => tenHong.has(x.file.name)));
          setDangLuu(false);
          return;
        }
        setFileCho([]);
      }
      onXong(sk);
    } catch (e2) {
      setLoi(errMsg(e2, 'Không lưu được lịch'));
    } finally {
      setDangLuu(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 p-4 overflow-y-auto">
      <form
        onSubmit={luu}
        className="w-full max-w-4xl rounded-xl bg-white shadow-xl my-8"
      >
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-3">
          <h2 className="font-semibold text-gray-900">
            {dangSua
              ? `Sửa lịch ${banGhi?.ma_lich ?? ''}`
              : 'Thêm lịch công tác'}
          </h2>
          <button
            type="button"
            onClick={onDong}
            className="rounded p-1 text-gray-500 hover:bg-gray-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="grid gap-3 px-5 py-4 sm:grid-cols-2">
          <O nhan="Nội dung cuộc họp *" rong>
            <input
              className={oCss}
              value={form.tieu_de}
              onChange={(e) => dat('tieu_de', e.target.value)}
              maxLength={500}
              autoFocus
            />
          </O>

          <O nhan="Loại lịch">
            <select
              className={oCss}
              value={form.loai_lich}
              onChange={(e) => dat('loai_lich', e.target.value)}
            >
              {loai.map((l) => (
                <option key={l.ma} value={l.ma}>
                  {l.ten}
                </option>
              ))}
            </select>
          </O>

          <O nhan="Trạng thái">
            <select
              className={oCss}
              value={form.trang_thai}
              onChange={(e) => dat('trang_thai', e.target.value)}
            >
              <option value="LEN_KE_HOACH">Dự kiến (chưa đăng)</option>
              <option value="DA_THONG_BAO">Đã đăng</option>
              <option value="HOAN_THANH">Đã diễn ra</option>
            </select>
          </O>

          <O nhan="Ngày *">
            <input
              type="date"
              className={oCss}
              value={form.ngay_hop}
              onChange={(e) => dat('ngay_hop', e.target.value)}
            />
          </O>

          <O nhan="Ngày kết thúc (nếu kéo dài nhiều ngày)">
            <input
              type="date"
              className={oCss}
              value={form.ngay_ket_thuc}
              onChange={(e) => dat('ngay_ket_thuc', e.target.value)}
            />
          </O>

          <O nhan="Giờ bắt đầu">
            <input
              type="time"
              className={oCss}
              value={form.gio_bat_dau}
              onChange={(e) => dat('gio_bat_dau', e.target.value)}
            />
          </O>

          <O nhan="Giờ kết thúc">
            <input
              type="time"
              className={oCss}
              value={form.gio_ket_thuc}
              onChange={(e) => dat('gio_ket_thuc', e.target.value)}
            />
          </O>

          <O nhan="Địa điểm" rong>
            {/* Danh mục phòng họp (G4.11) chỉ GỢI Ý, không ràng buộc:
                `dia_diem` là chuỗi tự do và đã có 6 tháng dữ liệu gõ tay.
                Dùng datalist để vẫn gõ được địa điểm ngoài danh mục. */}
            <input
              className={oCss}
              list="dm-phong-hop"
              value={form.dia_diem}
              onChange={(e) => dat('dia_diem', e.target.value)}
              maxLength={300}
              placeholder="Gõ hoặc chọn từ danh mục phòng họp"
            />
            <datalist id="dm-phong-hop">
              {phongHop.map((p) => (
                <option key={p} value={p} />
              ))}
            </datalist>
          </O>

          <O nhan="Chủ trì" rong>
            <ChonLanhDao
              ds={lanhDao}
              chon={form.chu_toa_id ? [form.chu_toa_id] : []}
              onDoi={(ids) => {
                dat('chu_toa_id', ids[0] ?? '');
                if (ids[0]) dat('chu_tri_text', '');
              }}
              tenDuPhong={
                banGhi?.chu_toa
                  ? { [banGhi.chu_toa.id]: banGhi.chu_toa.ho_ten }
                  : {}
              }
              placeholder="Tìm lãnh đạo chủ trì…"
            />
          </O>

          <O nhan="Hoặc ghi tay người chủ trì" rong>
            <input
              className={oCss}
              value={form.chu_tri_text}
              onChange={(e) => dat('chu_tri_text', e.target.value)}
              maxLength={300}
              disabled={Boolean(form.chu_toa_id)}
              placeholder="Dùng khi người chủ trì ngoài Chi cục — vd: đ/c Phó Chủ tịch UBND tỉnh"
            />
          </O>

          <O nhan="Đơn vị chuẩn bị" rong>
            <select
              className={oCss}
              value={
                donVi.some((d) => d.ten_don_vi === form.don_vi_chuan_bi)
                  ? form.don_vi_chuan_bi
                  : '__khac__'
              }
              onChange={(e) =>
                dat(
                  'don_vi_chuan_bi',
                  e.target.value === '__khac__' ? '' : e.target.value,
                )
              }
            >
              <option value="">— Chưa giao đơn vị nào —</option>
              {donVi.map((d) => (
                <option key={d.id} value={d.ten_don_vi}>
                  {d.ten_don_vi}
                </option>
              ))}
              <option value="__khac__">Khác (tự nhập bên dưới)…</option>
            </select>
            {!donVi.some((d) => d.ten_don_vi === form.don_vi_chuan_bi) && (
              <input
                className={`${oCss} mt-1.5`}
                value={form.don_vi_chuan_bi}
                onChange={(e) => dat('don_vi_chuan_bi', e.target.value)}
                maxLength={200}
                placeholder="Nhiều đơn vị hoặc tên khác — vd: Văn phòng, Đội NV1"
              />
            )}
          </O>

          <O nhan="Thành phần tham dự" rong>
            <ChonLanhDao
              ds={lanhDao}
              chon={thanhPhanIds}
              onDoi={setThanhPhanIds}
              nhieu
              tenDuPhong={Object.fromEntries(
                (banGhi?.lanh_dao_lien_quan ?? []).map((x) => [x.id, x.ho_ten]),
              )}
              placeholder="Thêm lãnh đạo tham dự…"
            />
          </O>

          <O nhan="Thành phần khác (ghi tay)" rong>
            <textarea
              className={oCss}
              rows={2}
              value={form.thanh_phan_text}
              onChange={(e) => dat('thanh_phan_text', e.target.value)}
              placeholder="Dùng cho thành phần theo nhóm — vd: Các đ/c UV BTV, BCH Đảng uỷ; toàn thể công chức Đội Kiểm soát"
            />
          </O>

          <O nhan="Số văn bản / giấy mời">
            <input
              className={oCss}
              value={form.so_van_ban}
              onChange={(e) => dat('so_van_ban', e.target.value)}
              maxLength={100}
            />
          </O>

          <O nhan="Ngày hiển thị trên lịch">
            <input
              type="date"
              className={oCss}
              value={form.ngay_hien_thi}
              onChange={(e) => dat('ngay_hien_thi', e.target.value)}
              placeholder="mặc định lấy ngày bắt đầu"
            />
          </O>

          <O nhan="Ghi chú" rong>
            <textarea
              className={oCss}
              rows={2}
              value={form.mo_ta}
              onChange={(e) => dat('mo_ta', e.target.value)}
            />
          </O>
        </div>

        {/* ── Tài liệu đính kèm ─────────────────────────────────────
            Bản lichkv8 có mục này ngay trong form thêm lịch; thiếu nó thì
            Văn phòng phải lưu lịch xong, mở lại trang chi tiết rồi mới nộp
            được tài liệu — hai bước cho một việc.                        */}
        <div className="border-t border-gray-200 px-5 py-4">
          <div className="mb-2 flex items-center gap-2">
            <Paperclip className="h-4 w-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">
              Tài liệu đính kèm
            </span>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-sm">
              <span className="mb-1 block text-gray-600">
                Loại tài liệu <span className="text-gray-400">(mặc định)</span>
              </span>
              <select
                className={oCss}
                value={loaiTaiLieu}
                onChange={(e) => setLoaiTaiLieu(e.target.value)}
              >
                {dsLoai.map((l) => (
                  <option key={l.ma} value={l.ma}>
                    {l.nhan}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-sm">
              <span className="mb-1 block text-gray-600">Ai được xem</span>
              <select
                className={oCss}
                value={mucTaiLieu}
                onChange={(e) =>
                  setMucTaiLieu(e.target.value as PhanQuyenTaiLieu)
                }
                title={mucList.find((m) => m.ma === mucTaiLieu)?.mo_ta}
              >
                {mucList.map((m) => (
                  <option key={m.ma} value={m.ma} disabled={!m.dat_duoc}>
                    {m.ten}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <p className="mt-1 text-xs text-gray-500">
            Hai ô trên áp cho file thả vào tiếp theo — mỗi file rồi vẫn đổi
            riêng được loại ở danh sách bên dưới. Mặc định công khai nội bộ;
            người tải lên luôn xem lại được file của chính mình, kể cả khi mức
            hạn chế được nâng sau đó.
          </p>

          {/* Ô chọn file nằm TRONG nhãn, không dùng nút bấm rồi gọi .click():
              bấm nhãn là trình duyệt tự mở hộp thoại, khỏi phụ thuộc ref. */}
          <label
            onDragOver={(e) => {
              e.preventDefault();
              setKeoVao(true);
            }}
            onDragLeave={() => setKeoVao(false)}
            onDrop={(e) => {
              e.preventDefault();
              setKeoVao(false);
              themFile(e.dataTransfer.files);
            }}
            className={`mt-2 block w-full cursor-pointer rounded-lg border-2 border-dashed px-3 py-5 text-center text-sm ${
              keoVao
                ? 'border-blue-400 bg-blue-50 text-blue-700'
                : 'border-gray-300 text-gray-600 hover:border-blue-400 hover:bg-gray-50'
            }`}
          >
            <input
              ref={oFile}
              type="file"
              multiple
              accept={ACCEPT_FILE}
              className="hidden"
              onChange={(e) => {
                themFile(e.target.files);
                // Dọn ô chọn để chọn LẠI đúng file vừa bỏ ra vẫn nổ `change`.
                // Phải đứng sau `themFile` — hàm đó đã chụp danh sách file
                // thành mảng rồi, xoá bây giờ không mất gì.
                e.target.value = '';
              }}
            />
            <span className="block font-medium">
              Kéo thả file vào đây hoặc bấm để chọn
            </span>
            <span className="block text-xs text-gray-500">
              Chọn được nhiều file một lúc · PDF, Word, Excel, PowerPoint, ảnh…
              tối đa 100MB mỗi file
            </span>
          </label>

          {fileCho.length > 0 && (
            <div className="mt-2 flex items-center justify-between">
              <span className="text-xs text-gray-500">
                Chờ tải lên ({fileCho.length})
              </span>
              {!dangLuu && (
                <button
                  type="button"
                  onClick={() => setFileCho([])}
                  className="text-xs text-gray-500 hover:text-red-600"
                >
                  Bỏ hết
                </button>
              )}
            </div>
          )}

          {fileCho.length > 0 && (
            <ul className="mt-1 divide-y divide-gray-100 rounded-lg border border-gray-200">
              {fileCho.map((x, i) => (
                <li
                  key={`${x.file.name}-${x.file.size}-${i}`}
                  className="flex flex-wrap items-center gap-2 px-3 py-2 text-sm"
                >
                  <FileText className="h-4 w-4 shrink-0 text-gray-400" />
                  <span className="min-w-0 flex-1 truncate">
                    {x.file.name}
                    <span className="ml-1.5 text-xs text-gray-500">
                      {coDaiFile(x.file.size)}
                    </span>
                  </span>
                  {/* Loại của RIÊNG file này, ngay cạnh tên nó. */}
                  <select
                    value={x.loai}
                    disabled={dangLuu}
                    onChange={(e) => doiLoaiFile(i, e.target.value)}
                    className="rounded border border-gray-300 bg-white px-1.5 py-0.5 text-xs text-gray-700 focus:border-blue-500 focus:outline-none disabled:opacity-40"
                  >
                    {/* Loại đã gán có thể không còn trong danh mục (đơn vị vừa
                        tắt nó) — vẫn phải hiện, nếu không ô chọn nhảy sang
                        loại khác mà người dùng không hề bấm. Tra không ra nhãn
                        thì hiện mã trần, vẫn hơn là biến mất. */}
                    {(dsLoai.some((l) => l.ma === x.loai)
                      ? dsLoai
                      : [{ ma: x.loai, nhan: x.loai }, ...dsLoai]
                    ).map((l) => (
                      <option key={l.ma} value={l.ma}>
                        {l.nhan}
                      </option>
                    ))}
                  </select>
                  {dangTaiFile.includes(x.file.name) ? (
                    <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                  ) : (
                    <button
                      type="button"
                      title="Bỏ khỏi danh sách"
                      disabled={dangLuu}
                      onClick={() => xoaFileCho(i)}
                      className="rounded p-1 text-gray-500 hover:bg-gray-100 disabled:opacity-40"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}

          {!dangSua && fileCho.length > 0 && (
            <p className="mt-1 text-xs text-gray-500">
              File được tải lên ngay sau khi lịch lưu xong.
            </p>
          )}

          {dangSua && daCo.length > 0 && (
            <>
              <span className="mt-3 mb-1 block text-xs text-gray-500">
                Đã đính kèm ({daCo.length})
              </span>
              <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200">
                {daCo.map((t) => (
                  <li
                    key={t.id}
                    className="flex items-center gap-2 px-3 py-2 text-sm"
                  >
                    <FileText className="h-4 w-4 shrink-0 text-gray-400" />
                    <span className="min-w-0 flex-1 truncate">
                      {t.ten_tai_lieu}
                      <span className="ml-1.5 text-xs text-gray-500">
                        {coDaiFile(t.file_size)}
                        {t.mo_ta ? ` · ${t.mo_ta}` : ''}
                      </span>
                    </span>
                    <button
                      type="button"
                      title="Xoá tài liệu"
                      onClick={() => void xoaFileDaCo(t)}
                      className="rounded p-1 text-red-600 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>

        {loi && (
          <div className="mx-5 mb-3 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
            {loi}
          </div>
        )}

        <div className="flex justify-end gap-2 border-t border-gray-200 px-5 py-3">
          <button
            type="button"
            onClick={onDong}
            className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm hover:bg-gray-50"
          >
            Đóng
          </button>
          <button
            type="submit"
            disabled={dangLuu}
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-40"
          >
            {dangLuu && <Loader2 className="w-4 h-4 animate-spin" />}
            {dangTaiFile.length > 0
              ? `Đang tải ${dangTaiFile.length} file…`
              : dangSua
                ? 'Lưu thay đổi'
                : daTao
                  ? 'Tải lại file'
                  : 'Tạo lịch'}
          </button>
        </div>
      </form>
    </div>
  );
}
