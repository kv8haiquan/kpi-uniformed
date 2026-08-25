/**
 * Kiểm thử hai chế độ xem mới của Lịch công tác: lưới TUẦN và màn hình một
 * NGÀY.
 *
 * Điều cần chắc:
 *  - bấm vào một ngày ở lưới tuần thì mở đúng ngày đó;
 *  - sự kiện nhiều ngày hiện ở mọi ngày nó kéo dài, không chỉ ngày bắt đầu —
 *    dữ liệu di trú từ lichkv8 có nhiều lịch dài ngày;
 *  - màn hình một ngày hiện ĐỦ mọi cuộc họp của ngày đó với chi tiết đầy đủ
 *    (thành phần, ghi chú, số văn bản), đúng như xem từng cuộc một.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { ISuKienChiTiet, ISuKienLich } from '@/types/lich-cong-tac';

import LichNgay from '../LichNgay';
import LichTuan from '../LichTuan';

// Thẻ chi tiết kéo theo Tài liệu và Chấm sao — hai khối tự gọi API riêng.
// Chặn ở tầng service để bài test nói về màn hình lịch, không về mạng.
vi.mock('@/services/lich-cong-tac', () => ({
  lichCongTacApi: {
    chiTiet: vi.fn(),
    huy: vi.fn(),
    xoa: vi.fn(),
    nhatKy: vi.fn(),
    quyenCuaToi: vi.fn(),
  },
}));
vi.mock('@/services/hkg', () => ({
  taiLieuApi: {
    listByCuocHop: vi.fn().mockResolvedValue([]),
    mucPhanQuyen: vi.fn().mockResolvedValue([]),
  },
}));
vi.mock('@/services/danh-gia-chuan-bi', () => ({
  danhGiaChuanBiApi: {
    cuaCuocHop: vi.fn().mockResolvedValue({
      diem_trung_binh: null,
      so_luot: 0,
      cham_duoc: false,
      diem_cua_toi: null,
      ghi_chu_cua_toi: null,
    }),
    cham: vi.fn(),
  },
}));
vi.mock('@/services/danh-muc-lich', () => ({
  danhMucLichApi: {
    danhSach: vi.fn().mockResolvedValue([]),
    nhom: vi.fn().mockResolvedValue({ duoc_sua: false }),
  },
}));

import { lichCongTacApi } from '@/services/lich-cong-tac';

function suKien(
  p: Partial<ISuKienLich> & { id: string; tieu_de: string },
): ISuKienLich {
  return {
    nguon: 'LICH_CONG_TAC',
    loai_lich: 'HOP',
    loai_lich_nhan: 'Họp',
    ngay_hop: '2026-08-25',
    ngay_hien_thi: '2026-08-25',
    ngay_ket_thuc: null,
    gio_bat_dau: '08:00:00',
    gio_ket_thuc: null,
    trang_thai: 'DA_THONG_BAO',
    lanh_dao_lien_quan: [],
    so_tai_lieu: 0,
    co_the_mo_hkg: false,
    ...p,
  } as ISuKienLich;
}

function chiTiet(
  p: Partial<ISuKienChiTiet> & { id: string; tieu_de: string },
): ISuKienChiTiet {
  return { ...suKien(p), ...p } as ISuKienChiTiet;
}

describe('LichTuan', () => {
  const tuan = [
    suKien({ id: '1', tieu_de: 'Giao ban đầu tuần' }),
    suKien({
      id: '2',
      tieu_de: 'Kiểm tra kho ngoại quan',
      ngay_hop: '2026-08-26',
      ngay_hien_thi: '2026-08-26',
      ngay_ket_thuc: '2026-08-28',
      gio_bat_dau: '13:30:00',
    }),
  ];

  it('hiện đủ 7 ngày thứ Hai → Chủ nhật của tuần chứa ngày đang xem', () => {
    render(
      <LichTuan
        ngay="2026-08-27"
        suKien={tuan}
        homNay="2026-08-25"
        onChonNgay={() => {}}
      />,
    );
    for (const t of ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']) {
      expect(screen.getByText(t)).toBeInTheDocument();
    }
    expect(screen.getByText('24/08')).toBeInTheDocument();
    expect(screen.getByText('30/08')).toBeInTheDocument();
  });

  it('sự kiện nhiều ngày hiện ở mọi ngày nó kéo dài', () => {
    render(
      <LichTuan
        ngay="2026-08-27"
        suKien={tuan}
        homNay="2026-08-25"
        onChonNgay={() => {}}
      />,
    );
    // 26, 27, 28/08 — ba ngày, nên ba lần xuất hiện.
    expect(screen.getAllByText('Kiểm tra kho ngoại quan')).toHaveLength(3);
    expect(screen.getAllByText('Giao ban đầu tuần')).toHaveLength(1);
  });

  it('bấm đầu cột một ngày thì báo đúng ngày đó lên trang cha', async () => {
    const onChonNgay = vi.fn();
    render(
      <LichTuan
        ngay="2026-08-27"
        suKien={tuan}
        homNay="2026-08-25"
        onChonNgay={onChonNgay}
      />,
    );
    await userEvent.click(screen.getByText('26/08'));
    expect(onChonNgay).toHaveBeenCalledWith('2026-08-26');
  });

  it('ngày trống ghi rõ là trống', () => {
    render(
      <LichTuan
        ngay="2026-08-27"
        suKien={[]}
        homNay="2026-08-25"
        onChonNgay={() => {}}
      />,
    );
    expect(screen.getAllByText('trống')).toHaveLength(7);
  });
});

describe('LichNgay — xem toàn bộ cuộc họp của một ngày', () => {
  const quyen = { la_quan_tri_lich: false, cong_chuc_id: 'toi' };

  beforeEach(() => {
    vi.mocked(lichCongTacApi.chiTiet).mockReset();
  });

  it('hiện đủ mọi cuộc họp trong ngày, tách buổi sáng và buổi chiều', async () => {
    vi.mocked(lichCongTacApi.chiTiet).mockImplementation(async (id: string) =>
      ({
        '1': chiTiet({ id: '1', tieu_de: 'Giao ban', gio_bat_dau: '08:00:00' }),
        '2': chiTiet({
          id: '2',
          tieu_de: 'Tiếp doanh nghiệp',
          gio_bat_dau: '14:00:00',
        }),
        '3': chiTiet({
          id: '3',
          tieu_de: 'Kiểm tra sau thông quan',
          gio_bat_dau: '15:30:00',
        }),
      })[id]!,
    );

    render(
      <LichNgay
        ngay="2026-08-25"
        suKien={[
          suKien({ id: '1', tieu_de: 'Giao ban', gio_bat_dau: '08:00:00' }),
          suKien({
            id: '2',
            tieu_de: 'Tiếp doanh nghiệp',
            gio_bat_dau: '14:00:00',
          }),
          suKien({
            id: '3',
            tieu_de: 'Kiểm tra sau thông quan',
            gio_bat_dau: '15:30:00',
          }),
        ]}
        homNay="2026-08-25"
        quyen={quyen}
        onLamMoi={() => {}}
      />,
    );

    expect(screen.getByText('3 cuộc họp / sự kiện')).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText('Giao ban')).toBeInTheDocument(),
    );
    expect(screen.getByText('Tiếp doanh nghiệp')).toBeInTheDocument();
    expect(screen.getByText('Kiểm tra sau thông quan')).toBeInTheDocument();
    expect(screen.getByText('Buổi sáng')).toBeInTheDocument();
    expect(screen.getByText('Buổi chiều')).toBeInTheDocument();
  });

  it('mỗi cuộc họp hiện chi tiết đầy đủ như khi xem riêng từng cuộc', async () => {
    vi.mocked(lichCongTacApi.chiTiet).mockResolvedValue(
      chiTiet({
        id: '1',
        tieu_de: 'Họp giao ban tháng 8',
        dia_diem: 'Phòng họp số 1',
        chu_tri_text: 'Đồng chí Chi cục trưởng',
        don_vi_chuan_bi: 'Văn phòng',
        so_van_ban: '123/TB-HQKV8',
        mo_ta: 'Chuẩn bị báo cáo số liệu tháng 8',
        thanh_phan_text: 'Lãnh đạo các Đội',
      }),
    );

    render(
      <LichNgay
        ngay="2026-08-25"
        suKien={[suKien({ id: '1', tieu_de: 'Họp giao ban tháng 8' })]}
        homNay="2026-08-25"
        quyen={quyen}
        onLamMoi={() => {}}
      />,
    );

    await waitFor(() =>
      expect(screen.getByText('Họp giao ban tháng 8')).toBeInTheDocument(),
    );
    // Đúng những trường mà danh sách rút gọn KHÔNG có — bằng chứng thẻ này
    // dùng bản chi tiết chứ không phải bản tóm tắt.
    expect(screen.getByText('Chuẩn bị báo cáo số liệu tháng 8')).toBeInTheDocument();
    expect(screen.getByText('Lãnh đạo các Đội')).toBeInTheDocument();
    expect(screen.getByText('123/TB-HQKV8')).toBeInTheDocument();
    expect(screen.getByText('Phòng họp số 1')).toBeInTheDocument();
    expect(screen.getByText('Đồng chí Chi cục trưởng')).toBeInTheDocument();
    expect(screen.getByText('Văn phòng')).toBeInTheDocument();
  });

  it('thu gọn được từng cuộc để lướt khi ngày có nhiều cuộc họp', async () => {
    vi.mocked(lichCongTacApi.chiTiet).mockResolvedValue(
      chiTiet({
        id: '1',
        tieu_de: 'Họp giao ban',
        mo_ta: 'Nội dung chi tiết',
        dia_diem: 'Phòng họp số 1',
      }),
    );

    render(
      <LichNgay
        ngay="2026-08-25"
        suKien={[suKien({ id: '1', tieu_de: 'Họp giao ban' })]}
        homNay="2026-08-25"
        quyen={quyen}
        onLamMoi={() => {}}
      />,
    );

    await waitFor(() =>
      expect(screen.getByText('Nội dung chi tiết')).toBeInTheDocument(),
    );
    await userEvent.click(screen.getByRole('button', { name: /Thu gọn/ }));
    expect(screen.queryByText('Nội dung chi tiết')).not.toBeInTheDocument();
    // Thu gọn vẫn phải trả lời được "họp ở đâu".
    expect(screen.getByText('Phòng họp số 1')).toBeInTheDocument();
  });

  it('huỷ một cuộc thì thẻ đó đổi ngay, không chờ nạp lại cả ngày', async () => {
    vi.mocked(lichCongTacApi.chiTiet).mockResolvedValue(
      chiTiet({ id: '1', tieu_de: 'Giao ban', created_by: 'toi' }),
    );
    vi.mocked(lichCongTacApi.huy).mockResolvedValue(
      chiTiet({
        id: '1',
        tieu_de: 'Giao ban',
        created_by: 'toi',
        trang_thai: 'HUY',
        ly_do_huy: 'Lãnh đạo đi công tác đột xuất',
      }),
    );
    vi.spyOn(window, 'prompt').mockReturnValue('Lãnh đạo đi công tác đột xuất');

    // Danh sách id của ngày không đổi khi huỷ, nên nạp lại cả ngày sẽ KHÔNG
    // gọi lại chi tiết — thẻ phải tự đổi bằng bản vừa nhận về.
    const onLamMoi = vi.fn();
    render(
      <LichNgay
        ngay="2026-08-25"
        suKien={[suKien({ id: '1', tieu_de: 'Giao ban', created_by: 'toi' })]}
        homNay="2026-08-25"
        quyen={quyen}
        onLamMoi={onLamMoi}
      />,
    );

    await waitFor(() =>
      expect(screen.getByRole('button', { name: /Huỷ lịch/ })).toBeInTheDocument(),
    );
    await userEvent.click(screen.getByRole('button', { name: /Huỷ lịch/ }));

    await waitFor(() =>
      expect(screen.getByText('Đã hủy')).toBeInTheDocument(),
    );
    expect(
      screen.getByText('Lãnh đạo đi công tác đột xuất'),
    ).toBeInTheDocument();
    expect(onLamMoi).toHaveBeenCalled();
    vi.mocked(window.prompt).mockRestore();
  });

  it('sự kiện bắt đầu từ hôm trước vẫn được tính vào ngày này', async () => {
    vi.mocked(lichCongTacApi.chiTiet).mockResolvedValue(
      chiTiet({
        id: '1',
        tieu_de: 'Hội nghị tập huấn',
        ngay_hop: '2026-08-26',
        ngay_hien_thi: '2026-08-26',
        ngay_ket_thuc: '2026-08-28',
      }),
    );

    render(
      <LichNgay
        ngay="2026-08-27"
        suKien={[
          suKien({
            id: '1',
            tieu_de: 'Hội nghị tập huấn',
            ngay_hop: '2026-08-26',
            ngay_hien_thi: '2026-08-26',
            ngay_ket_thuc: '2026-08-28',
          }),
        ]}
        homNay="2026-08-25"
        quyen={quyen}
        onLamMoi={() => {}}
      />,
    );

    await waitFor(() =>
      expect(screen.getByText('Hội nghị tập huấn')).toBeInTheDocument(),
    );
    expect(screen.getByText('Thứ Năm, 27/08/2026')).toBeInTheDocument();
  });

  it('ngày không có sự kiện nói rõ chứ không để trắng, và không gọi API', () => {
    render(
      <LichNgay
        ngay="2026-08-29"
        suKien={[]}
        homNay="2026-08-25"
        quyen={quyen}
        onLamMoi={() => {}}
      />,
    );
    expect(
      screen.getByText('Ngày này chưa có sự kiện nào trên lịch.'),
    ).toBeInTheDocument();
    expect(screen.getByText('Thứ Bảy, 29/08/2026')).toBeInTheDocument();
    expect(lichCongTacApi.chiTiet).not.toHaveBeenCalled();
  });

  it('chỉ hiện nút Sửa/Xoá với người được sửa sự kiện đó', async () => {
    vi.mocked(lichCongTacApi.chiTiet).mockResolvedValue(
      chiTiet({ id: '1', tieu_de: 'Giao ban', created_by: 'toi' }),
    );

    const { unmount } = render(
      <LichNgay
        ngay="2026-08-25"
        suKien={[suKien({ id: '1', tieu_de: 'Giao ban', created_by: 'toi' })]}
        homNay="2026-08-25"
        quyen={quyen}
        onLamMoi={() => {}}
      />,
    );
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Sửa' })).toBeInTheDocument(),
    );
    unmount();

    // Cùng sự kiện đó nhưng người khác tạo → không có nút Sửa.
    vi.mocked(lichCongTacApi.chiTiet).mockResolvedValue(
      chiTiet({ id: '1', tieu_de: 'Giao ban', created_by: 'nguoi-khac' }),
    );
    render(
      <LichNgay
        ngay="2026-08-25"
        suKien={[suKien({ id: '1', tieu_de: 'Giao ban', created_by: 'nguoi-khac' })]}
        homNay="2026-08-25"
        quyen={{ la_quan_tri_lich: false, cong_chuc_id: 'toi' }}
        onLamMoi={() => {}}
      />,
    );
    await waitFor(() =>
      expect(screen.getByText('Giao ban')).toBeInTheDocument(),
    );
    expect(screen.queryByRole('button', { name: 'Sửa' })).not.toBeInTheDocument();
  });
});
