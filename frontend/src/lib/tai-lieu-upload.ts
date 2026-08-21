/**
 * Tải nhiều tài liệu lên một cuộc họp / sự kiện lịch.
 *
 * Dùng chung cho modal Thêm lịch và khung tài liệu ở trang chi tiết — hai chỗ
 * này trước đây mỗi chỗ tự viết một kiểu, nên một chỗ nhận nhiều file còn chỗ
 * kia chỉ nhận đúng một.
 *
 * Backend chỉ có endpoint upload TỪNG file (`POST /tai-lieu/upload`, một
 * `UploadFile` mỗi lần), nên "chọn nhiều file" ở giao diện là nhiều lượt gọi.
 * Gọi tuần tự thì 10 file là 10 lần chờ nối đuôi nhau; gọi hết một lượt thì
 * đụng rate-limit (60 lượt / 5 phút) và nghẽn đường truyền. Vì vậy chạy tối đa
 * `SO_SONG_SONG` file một lúc.
 */

import { taiLieuApi } from '@/services/hkg';
import { errApi } from '@/lib/hkg-error';
import type { PhanQuyenTaiLieu } from '@/types/hkg';

/** Khớp `ALLOWED_EXTENSIONS` trong `meeting_service/config.py`. */
export const DUOI_CHO_PHEP = [
  '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
  '.jpg', '.jpeg', '.png', '.gif', '.webp', '.txt',
] as const;

/** Giá trị cho thuộc tính `accept` của ô chọn file. */
export const ACCEPT_FILE = DUOI_CHO_PHEP.join(',');

/** Khớp `max_file_size_mb` trong `meeting_service/config.py`. */
export const CO_TOI_DA_MB = 100;

const SO_SONG_SONG = 3;

/**
 * Loại tài liệu — nhãn dự phòng.
 *
 * Từ G4.11 danh sách thật nằm ở `meeting.danh_muc` nhóm `LOAI_TAI_LIEU` để
 * đơn vị tự quản trị (yêu cầu chuyển đổi mục II.15); gọi
 * `danhMucLichApi.danhSach({ nhom: 'LOAI_TAI_LIEU' })`. Danh sách dưới đây
 * chỉ dùng khi chưa gọi được máy chủ, giữ đúng 7 mục FILE_TYPE của hệ cũ.
 *
 * Nhãn được lưu vào `mo_ta` của tài liệu vì `meeting.tai_lieu` chưa có cột
 * riêng. Đây là NHÃN để người đọc nhận ra nhanh, KHÔNG phải căn cứ phân loại:
 * báo cáo Thống kê tài liệu vẫn nhận giấy mời theo tên file như trước.
 */
export const LOAI_TAI_LIEU = [
  'Giấy mời',
  'Tài liệu họp',
  'Báo cáo',
  'Chương trình',
  'Biên bản',
  'Kết luận',
  'Tài liệu khác',
];

/**
 * Một file đang chờ tải lên, kèm loại tài liệu của RIÊNG nó.
 *
 * Trước G4.11 cả hàng đợi dùng chung một loại — nộp giấy mời và báo cáo trong
 * cùng một lượt thì phải tải hai lần. Nay mỗi file mang loại riêng, và loại
 * đó hiện ngay cạnh tên file.
 */
export interface FileCho {
  file: File;
  loai: string;
}

export function coDaiFile(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${Math.round(n / 1024)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

/**
 * Lý do một file không nộp được, hoặc `null` nếu hợp lệ.
 *
 * Kiểm ngay trên máy người dùng để khỏi tải hết 120MB lên rồi mới bị chối —
 * backend vẫn kiểm lại y hệt, đây chỉ là để báo sớm.
 */
export function loiFile(f: File): string | null {
  const cham = f.name.lastIndexOf('.');
  const duoi = cham < 0 ? '' : f.name.slice(cham).toLowerCase();
  if (!DUOI_CHO_PHEP.includes(duoi as (typeof DUOI_CHO_PHEP)[number])) {
    return `đuôi ${duoi || 'trống'} không được phép`;
  }
  if (f.size > CO_TOI_DA_MB * 1024 * 1024) {
    return `nặng ${coDaiFile(f.size)}, vượt mức ${CO_TOI_DA_MB}MB`;
  }
  if (f.size === 0) return 'file rỗng';
  return null;
}

/**
 * Gộp file mới chọn vào hàng đợi, bỏ trùng theo tên + cỡ.
 *
 * QUAN TRỌNG — phải chụp `FileList` thành mảng NGAY tại đây, đồng bộ. `FileList`
 * lấy từ `input.files` là danh sách SỐNG: ô chọn file bị đặt lại `value = ''`
 * (để chọn lại đúng file đó vẫn nổ `change`) là danh sách rỗng theo. Trước đây
 * hàm gộp nằm trong `setState(prev => …)` — React gọi hàm đó lúc vẽ lại, tức là
 * SAU khi `value` đã bị xoá — nên bấm chọn file không thêm được gì, còn kéo thả
 * vẫn chạy vì `dataTransfer.files` không bị đụng tới.
 */
export function gopFile(
  dsCu: FileCho[],
  them: FileList | File[] | null,
  loai: string,
): FileCho[] {
  if (!them) return dsCu;
  const moi = Array.from(them);
  if (moi.length === 0) return dsCu;
  const daCo = new Set(dsCu.map((x) => `${x.file.name}|${x.file.size}`));
  const themVao: FileCho[] = [];
  for (const f of moi) {
    const khoa = `${f.name}|${f.size}`;
    if (daCo.has(khoa)) continue;
    daCo.add(khoa); // chống trùng ngay trong chính lượt chọn này
    themVao.push({ file: f, loai });
  }
  return themVao.length === 0 ? dsCu : [...dsCu, ...themVao];
}

export interface FileHong {
  ten: string;
  loi: string;
}

export interface ThamSoTaiNhieu {
  cuocHopId: string;
  /**
   * Hàng đợi. Nhận `File[]` thuần thì cả lượt dùng chung `moTa`; nhận
   * `FileCho[]` thì mỗi file mang loại riêng của nó.
   */
  files: Array<File | FileCho>;
  /** Loại tài liệu dùng chung, cho những file không mang loại riêng. */
  moTa?: string;
  phanQuyen?: PhanQuyenTaiLieu;
  /** Gọi khi một file bắt đầu / kết thúc, để giao diện hiện vòng quay. */
  onDoiDangTai?: (dangTai: string[]) => void;
}

/** Tách một phần tử hàng đợi thành (file, loại) dù nó ở dạng nào. */
function tach(x: File | FileCho, macDinh?: string): { f: File; loai?: string } {
  return x instanceof File
    ? { f: x, loai: macDinh }
    : { f: x.file, loai: x.loai || macDinh };
}

/**
 * Tải cả hàng đợi lên. Trả về danh sách file hỏng theo đúng thứ tự đã chọn —
 * file chạy song song nên thứ tự hoàn thành không đoán được, phải sắp lại.
 */
export async function taiNhieuFile({
  cuocHopId,
  files,
  moTa,
  phanQuyen,
  onDoiDangTai,
}: ThamSoTaiNhieu): Promise<FileHong[]> {
  const hong: Array<FileHong & { thuTu: number }> = [];
  const dangTai = new Set<string>();
  const bao = () => onDoiDangTai?.([...dangTai]);

  let ke = 0;
  const tho = async () => {
    for (;;) {
      const i = ke++;
      if (i >= files.length) return;
      const { f, loai } = tach(files[i], moTa);

      const loiSom = loiFile(f);
      if (loiSom) {
        hong.push({ thuTu: i, ten: f.name, loi: loiSom });
        continue;
      }

      dangTai.add(f.name);
      bao();
      try {
        await taiLieuApi.upload({
          cuoc_hop_id: cuocHopId,
          file: f,
          mo_ta: loai,
          phan_quyen: phanQuyen,
        });
      } catch (e) {
        hong.push({ thuTu: i, ten: f.name, loi: errApi(e, 'không rõ lỗi') });
      } finally {
        dangTai.delete(f.name);
        bao();
      }
    }
  };

  await Promise.all(
    Array.from({ length: Math.min(SO_SONG_SONG, files.length) }, tho),
  );

  return hong
    .sort((a, b) => a.thuTu - b.thuTu)
    .map(({ ten, loi }) => ({ ten, loi }));
}

/** Câu thông báo gọn cho danh sách file hỏng. */
export function moTaFileHong(hong: FileHong[]): string {
  return hong.map((h) => `${h.ten} (${h.loi})`).join('; ');
}
