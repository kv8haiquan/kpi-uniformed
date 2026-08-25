/**
 * Kiểm thử hai chế độ xem mới của Lịch công tác: lưới TUẦN và chương trình
 * một NGÀY.
 *
 * Điều cần chắc: bấm vào một ngày ở lưới tuần thì mở đúng ngày đó, và sự kiện
 * nhiều ngày phải hiện ở mọi ngày nó kéo dài chứ không chỉ ngày bắt đầu — đây
 * là chỗ dễ sót nhất vì dữ liệu di trú từ lichkv8 có nhiều lịch dài ngày.
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import type { ISuKienLich } from '@/types/lich-cong-tac';

import LichNgay from '../LichNgay';
import LichTuan from '../LichTuan';

function suKien(p: Partial<ISuKienLich> & { id: string; tieu_de: string }): ISuKienLich {
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

describe('LichNgay', () => {
  const chung = {
    homNay: '2026-08-25',
    suaDuoc: () => false,
    onSua: () => {},
    dangMoSua: null,
  };

  it('tách buổi sáng và buổi chiều theo mốc 12:00', () => {
    render(
      <LichNgay
        ngay="2026-08-25"
        suKien={[
          suKien({ id: '1', tieu_de: 'Giao ban', gio_bat_dau: '08:00:00' }),
          suKien({ id: '2', tieu_de: 'Tiếp doanh nghiệp', gio_bat_dau: '14:00:00' }),
        ]}
        {...chung}
      />,
    );
    expect(screen.getByText('Buổi sáng')).toBeInTheDocument();
    expect(screen.getByText('Buổi chiều')).toBeInTheDocument();
    expect(screen.getByText('Giao ban')).toBeInTheDocument();
    expect(screen.getByText('Tiếp doanh nghiệp')).toBeInTheDocument();
  });

  it('sự kiện bắt đầu từ hôm trước vẫn hiện, kèm khoảng ngày', () => {
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
        {...chung}
      />,
    );
    expect(screen.getByText('Hội nghị tập huấn')).toBeInTheDocument();
    expect(screen.getByText('26/08/2026 → 28/08/2026')).toBeInTheDocument();
  });

  it('ngày không có sự kiện nói rõ chứ không để trắng', () => {
    render(<LichNgay ngay="2026-08-29" suKien={[]} {...chung} />);
    expect(
      screen.getByText('Ngày này chưa có sự kiện nào trên lịch.'),
    ).toBeInTheDocument();
    expect(screen.getByText('Thứ Bảy, 29/08/2026')).toBeInTheDocument();
  });

  it('chỉ hiện nút Sửa với sự kiện người dùng được sửa', async () => {
    const onSua = vi.fn();
    render(
      <LichNgay
        ngay="2026-08-25"
        suKien={[suKien({ id: '1', tieu_de: 'Giao ban' })]}
        homNay="2026-08-25"
        suaDuoc={() => true}
        onSua={onSua}
        dangMoSua={null}
      />,
    );
    await userEvent.click(screen.getByTitle('Sửa sự kiện'));
    expect(onSua).toHaveBeenCalledTimes(1);
  });
});
