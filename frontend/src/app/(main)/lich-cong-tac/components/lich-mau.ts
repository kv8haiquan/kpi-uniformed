/**
 * Bảng màu và vài phép rút gọn dùng chung cho các chế độ xem lịch (tháng,
 * tuần, ngày). Tách ra khỏi page.tsx để ba màn hình tô cùng một màu — trước
 * đây chỉ có lưới tháng nên bảng màu nằm ngay trong trang.
 */

import type {
  IQuyenLich,
  ISuKienLich,
  LoaiLich,
  TrangThaiLich,
} from '@/types/lich-cong-tac';

export const MAU_LOAI: Record<LoaiLich, string> = {
  HOP: 'bg-blue-100 text-blue-800 border-blue-200',
  TRUC_BAN: 'bg-amber-100 text-amber-800 border-amber-200',
  HOI_NGHI: 'bg-purple-100 text-purple-800 border-purple-200',
  LAM_VIEC: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  CONG_TAC: 'bg-cyan-100 text-cyan-800 border-cyan-200',
  LICH_KHAC: 'bg-gray-100 text-gray-700 border-gray-200',
};

export const MAU_TRANG_THAI: Record<TrangThaiLich, string> = {
  LEN_KE_HOACH: 'bg-gray-100 text-gray-700',
  DA_THONG_BAO: 'bg-blue-100 text-blue-800',
  DANG_DIEN_RA: 'bg-yellow-100 text-yellow-800',
  HOAN_THANH: 'bg-green-100 text-green-800',
  HUY: 'bg-red-100 text-red-800',
};

/** Danh mục loại lịch thêm mới không có trong bảng màu — dùng màu trung tính. */
export function mauLoai(loai?: string | null): string {
  return MAU_LOAI[(loai as LoaiLich) ?? 'LICH_KHAC'] ?? MAU_LOAI.LICH_KHAC;
}

/** Khớp được công chức thì lấy họ tên, không thì đọc phần ghi tay. */
export function chuTri(sk: ISuKienLich): string {
  return sk.chu_toa?.ho_ten || sk.chu_tri_text || '';
}

/**
 * Người đang xem có được sửa sự kiện này không: quản trị lịch sửa được tất cả,
 * người thường chỉ sửa lịch mình tạo, và cuộc họp nguồn HKG thì sửa bên đó.
 *
 * Backend mới là nơi quyết định — hàm này chỉ để ẩn nút cho đỡ rối. Gom về một
 * chỗ vì trước đây luật này chép ở ba màn hình, sửa một chỗ là lệch.
 */
export function suaDuocLich(
  sk: Pick<ISuKienLich, 'nguon' | 'created_by'>,
  quyen: IQuyenLich | null,
): boolean {
  if (sk.nguon !== 'LICH_CONG_TAC' || !quyen) return false;
  return quyen.la_quan_tri_lich || quyen.cong_chuc_id === sk.created_by;
}
