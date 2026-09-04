import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import BangDiemDanhChiTiet from '../BangDiemDanhChiTiet';
import type { IDiemDanhChiTiet, IDiemDanhChiTietRow } from '@/types/hkg';

// Bảng gọi máy chủ qua diemDanhApi — thay bằng mock để test thuần giao diện.
const chiTiet = vi.fn();
const bamTay = vi.fn();
const xuatExcel = vi.fn();

vi.mock('@/services/hkg', () => ({
  diemDanhApi: {
    chiTiet: (...a: unknown[]) => chiTiet(...a),
    bamTay: (...a: unknown[]) => bamTay(...a),
    xuatExcel: (...a: unknown[]) => xuatExcel(...a),
  },
}));

// isLocked lấy từ MeetingContext — cho phép từng test đặt lại.
let ctxIsLocked = false;
vi.mock('@/components/hkg/MeetingContext', () => ({
  useMeeting: () => ({
    ch: null,
    isCancelled: false,
    isLocked: ctxIsLocked,
    canEdit: true,
    currentUserId: null,
    refresh: async () => {},
  }),
}));

function dong(over: Partial<IDiemDanhChiTietRow> = {}): IDiemDanhChiTietRow {
  return {
    cong_chuc_id: 'cc-1',
    ho_ten: 'Nguyễn Văn A',
    ma_cc: '20ZZ-0224',
    chuc_vu: 'Đội trưởng',
    don_vi_id: 'dv-1',
    ten_don_vi: 'Đội Nghiệp vụ 1',
    loai_tham_du: 'BAT_BUOC',
    xac_nhan: 'THAM_DU',
    trang_thai: 'CO_MAT',
    hinh_thuc: 'TU_DIEM_DANH',
    gio_diem_danh: '2026-09-04T07:58:00+07:00',
    ghi_chu: null,
    nguoi_diem_danh_id: null,
    nguoi_diem_danh_ho_ten: null,
    ly_do_vang: null,
    nguon_ly_do: null,
    xin_phep_trang_thai: null,
    xin_phep_auto_duyet: null,
    nguoi_du_thay_ho_ten: null,
    ...over,
  };
}

const BA_NGUOI: IDiemDanhChiTietRow[] = [
  dong(),
  dong({
    cong_chuc_id: 'cc-2', ho_ten: 'Trần Thị B', ma_cc: '20ZZ-0300',
    ten_don_vi: 'Phòng Tổng hợp', don_vi_id: 'dv-2',
    trang_thai: 'VANG_CO_PHEP', hinh_thuc: 'BAM_TAY',
    ly_do_vang: 'đi công tác Hà Nội', nguon_ly_do: 'DON_XIN_PHEP',
    xin_phep_trang_thai: 'DA_DUYET',
  }),
  // Người CHƯA điểm danh — vẫn phải có dòng
  dong({
    cong_chuc_id: 'cc-3', ho_ten: 'Lê Văn C', ma_cc: '20ZZ-0400',
    trang_thai: null, hinh_thuc: null, gio_diem_danh: null,
  }),
];

function kq(over: Partial<IDiemDanhChiTiet> = {}): IDiemDanhChiTiet {
  return {
    tong_hop: {
      tong_so: 3, co_mat: 1, den_muon: 0,
      vang_co_phep: 1, vang_khong_phep: 0, chua_diem_danh: 1,
    },
    co_the_bam_tay: true,
    danh_sach: BA_NGUOI,
    ...over,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  ctxIsLocked = false;
  chiTiet.mockResolvedValue(kq());
});

describe('BangDiemDanhChiTiet', () => {
  it('liệt kê đủ mọi thành phần, kể cả người chưa điểm danh', async () => {
    render(<BangDiemDanhChiTiet cuocHopId="ch-1" />);

    expect(await screen.findByText('Nguyễn Văn A')).toBeInTheDocument();
    // Khoanh vùng vào bảng: "Chưa điểm danh" cũng là nhãn của một ô số.
    const bang = within(screen.getByRole('table'));
    expect(bang.getByText('Trần Thị B')).toBeInTheDocument();
    expect(bang.getByText('Lê Văn C')).toBeInTheDocument();
    expect(bang.getByText('Chưa điểm danh')).toBeInTheDocument();
    expect(bang.getAllByRole('row')).toHaveLength(4); // 1 header + 3 người
  });

  it('nhãn TU_DIEM_DANH hiện "Tự điểm danh", không rơi về "Bấm tay"', async () => {
    render(<BangDiemDanhChiTiet cuocHopId="ch-1" />);
    expect(await screen.findByText('Tự điểm danh')).toBeInTheDocument();
    expect(screen.getByText('Thư ký bấm tay')).toBeInTheDocument();
  });

  it('hiện lý do vắng kèm ghi rõ nguồn là đơn xin phép', async () => {
    render(<BangDiemDanhChiTiet cuocHopId="ch-1" />);
    expect(await screen.findByText(/đi công tác Hà Nội/)).toBeInTheDocument();
    expect(screen.getByText(/\(đơn xin phép\)/)).toBeInTheDocument();
  });

  it('bấm ô số lọc bảng, bấm lại thì bỏ lọc', async () => {
    const u = userEvent.setup();
    render(<BangDiemDanhChiTiet cuocHopId="ch-1" />);
    await screen.findByText('Nguyễn Văn A');

    await u.click(screen.getByRole('button', { name: /Có mặt/ }));
    expect(screen.getByText('Nguyễn Văn A')).toBeInTheDocument();
    expect(screen.queryByText('Trần Thị B')).not.toBeInTheDocument();

    await u.click(screen.getByRole('button', { name: /Có mặt/ }));
    expect(screen.getByText('Trần Thị B')).toBeInTheDocument();
  });

  it('ô "Chưa điểm danh" lọc đúng người không có bản ghi', async () => {
    const u = userEvent.setup();
    render(<BangDiemDanhChiTiet cuocHopId="ch-1" />);
    await screen.findByText('Nguyễn Văn A');

    await u.click(screen.getByRole('button', { name: /Chưa điểm danh/ }));
    expect(screen.getByText('Lê Văn C')).toBeInTheDocument();
    expect(screen.queryByText('Nguyễn Văn A')).not.toBeInTheDocument();
  });

  it('tìm được theo họ tên và theo mã công chức', async () => {
    const u = userEvent.setup();
    render(<BangDiemDanhChiTiet cuocHopId="ch-1" />);
    await screen.findByText('Nguyễn Văn A');
    const o = screen.getByPlaceholderText(/Tìm theo họ tên hoặc mã CC/);

    await u.type(o, 'Trần');
    expect(screen.getByText('Trần Thị B')).toBeInTheDocument();
    expect(screen.queryByText('Nguyễn Văn A')).not.toBeInTheDocument();

    await u.clear(o);
    await u.type(o, '20ZZ-0400');
    expect(screen.getByText('Lê Văn C')).toBeInTheDocument();
    expect(screen.queryByText('Trần Thị B')).not.toBeInTheDocument();
  });

  it('ẩn cột Chấm khi máy chủ nói không được bấm tay', async () => {
    chiTiet.mockResolvedValue(kq({ co_the_bam_tay: false }));
    render(<BangDiemDanhChiTiet cuocHopId="ch-1" />);
    await screen.findByText('Nguyễn Văn A');

    expect(screen.queryByText('Chấm')).not.toBeInTheDocument();
    expect(screen.queryByRole('combobox', { name: /Chấm điểm danh/ }))
      .not.toBeInTheDocument();
  });

  it('ẩn cột Chấm khi cuộc họp đã chốt, nhưng vẫn xem được bảng', async () => {
    ctxIsLocked = true;
    render(<BangDiemDanhChiTiet cuocHopId="ch-1" />);
    await screen.findByText('Nguyễn Văn A');

    expect(screen.queryByText('Chấm')).not.toBeInTheDocument();
    expect(screen.getByText('Trần Thị B')).toBeInTheDocument();
  });

  it('chấm "Có mặt" gọi bấm tay rồi nạp lại bảng', async () => {
    const u = userEvent.setup();
    bamTay.mockResolvedValue({ so_diem_danh: 1, chi_tiet: [] });
    const onSaved = vi.fn();
    render(<BangDiemDanhChiTiet cuocHopId="ch-1" onSaved={onSaved} />);
    await screen.findByText('Lê Văn C');

    await u.selectOptions(
      screen.getByRole('combobox', { name: /Chấm điểm danh cho Lê Văn C/ }),
      'CO_MAT',
    );

    await waitFor(() => expect(bamTay).toHaveBeenCalledWith('ch-1', [
      { cong_chuc_id: 'cc-3', trang_thai: 'CO_MAT', ghi_chu: undefined },
    ]));
    // Nạp lại: 1 lần khi mở + 1 lần sau khi chấm
    await waitFor(() => expect(chiTiet).toHaveBeenCalledTimes(2));
    expect(onSaved).toHaveBeenCalled();
  });

  it('chấm trạng thái vắng thì hỏi lý do và gửi kèm', async () => {
    const u = userEvent.setup();
    bamTay.mockResolvedValue({ so_diem_danh: 1, chi_tiet: [] });
    vi.spyOn(window, 'prompt').mockReturnValue('họp ngành ở Hà Nội');
    render(<BangDiemDanhChiTiet cuocHopId="ch-1" />);
    await screen.findByText('Lê Văn C');

    await u.selectOptions(
      screen.getByRole('combobox', { name: /Chấm điểm danh cho Lê Văn C/ }),
      'VANG_CO_PHEP',
    );

    await waitFor(() => expect(bamTay).toHaveBeenCalledWith('ch-1', [
      {
        cong_chuc_id: 'cc-3',
        trang_thai: 'VANG_CO_PHEP',
        ghi_chu: 'họp ngành ở Hà Nội',
      },
    ]));
  });

  it('bấm Cancel ở hộp hỏi lý do thì không đổi gì', async () => {
    const u = userEvent.setup();
    vi.spyOn(window, 'prompt').mockReturnValue(null);
    render(<BangDiemDanhChiTiet cuocHopId="ch-1" />);
    await screen.findByText('Lê Văn C');

    await u.selectOptions(
      screen.getByRole('combobox', { name: /Chấm điểm danh cho Lê Văn C/ }),
      'VANG_KHONG_PHEP',
    );

    expect(bamTay).not.toHaveBeenCalled();
  });

  it('hiện đúng câu tiếng Việt của máy chủ khi bị chặn 403', async () => {
    // Hình dạng thật của lỗi axios từ backend HKG
    chiTiet.mockRejectedValue({
      message: 'Request failed with status code 403',
      response: {
        status: 403,
        data: {
          detail: {
            success: false,
            error: {
              code: 'NO_PERMISSION',
              message: 'Chỉ ban tổ chức cuộc họp mới xem được bảng điểm danh',
            },
          },
        },
      },
    });
    render(<BangDiemDanhChiTiet cuocHopId="ch-1" />);

    expect(
      await screen.findByText(/Chỉ ban tổ chức cuộc họp mới xem được/),
    ).toBeInTheDocument();
    // Không được để lọt câu kỹ thuật ra trước mặt người dùng
    expect(screen.queryByText(/Request failed/)).not.toBeInTheDocument();
  });

  it('lùi về câu dự phòng khi lỗi không có thông điệp máy chủ', async () => {
    chiTiet.mockRejectedValue({});
    render(<BangDiemDanhChiTiet cuocHopId="ch-1" />);
    expect(
      await screen.findByText(/Không tải được bảng điểm danh/),
    ).toBeInTheDocument();
  });
});
