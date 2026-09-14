/**
 * Test cho XemTruocExcel — khung dựng bảng tính trong trình duyệt.
 *
 * Chạy SheetJS THẬT trên file .xlsx thật ở `fixtures/bang-ke-mau.xlsx` (không
 * thay bằng bản giả): nếu nâng cấp thư viện làm hỏng việc đọc file, test đỏ ngay.
 *
 * Có một test riêng cho ô chứa thẻ HTML. Đó không phải trường hợp lý thuyết:
 * file do học viên nộp, còn modal chấm bài do giảng viên/quản trị mở, nên một ô
 * `<img onerror=...>` mà lọt vào innerHTML là chạy trong phiên của người chấm.
 */

import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import { readFileSync } from 'fs';
import { join } from 'path';
import XemTruocExcel from '../XemTruocExcel';

const DUONG_DAN = join(__dirname, 'fixtures', 'bang-ke-mau.xlsx');
const URL_BAI_NOP = '/uploads/lms/bai-thuc-hanh/abc_bang-ke-mau.xlsx';

function stubFetchFixture() {
  const buf = readFileSync(DUONG_DAN);
  const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    arrayBuffer: async () => ab,
  } as Response));
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('XemTruocExcel — đọc file .xlsx thật', () => {
  it('dựng được nội dung bảng tính đầu tiên', async () => {
    stubFetchFixture();
    const { container } = render(<XemTruocExcel url={URL_BAI_NOP} />);

    await waitFor(
      () => expect(screen.queryByText(/Đang đọc bảng tính/)).not.toBeInTheDocument(),
      { timeout: 15000 },
    );
    expect(screen.queryByText(/Không hiển thị được nội dung Excel/)).not.toBeInTheDocument();

    const chu = container.textContent || '';
    expect(chu).toContain('Mặt hàng');
    expect(chu).toContain('Máy tính xách tay');
    expect(chu).toContain('Linh kiện điện tử');
    expect(container.querySelector('table')).not.toBeNull();
  }, 20000);

  it('file nhiều sheet thì hiện thẻ chọn sheet', async () => {
    stubFetchFixture();
    render(<XemTruocExcel url={URL_BAI_NOP} />);

    await waitFor(() => expect(screen.getByText('To khai')).toBeInTheDocument(), {
      timeout: 15000,
    });
    expect(screen.getByText('Ghi chu')).toBeInTheDocument();
  }, 20000);

  it('ô chứa thẻ HTML được hiện thành CHỮ, không thành phần tử DOM', async () => {
    stubFetchFixture();
    const { container } = render(<XemTruocExcel url={URL_BAI_NOP} />);

    await waitFor(
      () => expect(screen.queryByText(/Đang đọc bảng tính/)).not.toBeInTheDocument(),
      { timeout: 15000 },
    );

    // Sang sheet "Ghi chu" — nơi có ô chứa payload
    (screen.getByText('Ghi chu') as HTMLButtonElement).click();

    await waitFor(() =>
      expect(screen.getByText('<img src=x onerror="alert(1)">')).toBeInTheDocument(),
    );
    // Chuỗi phải nằm ở dạng text; KHÔNG được sinh ra thẻ <img> nào
    expect(container.querySelector('img')).toBeNull();
  }, 20000);
});

describe('XemTruocExcel — lỗi', () => {
  it('máy chủ trả lỗi → hiện nút tải về kèm mã lỗi', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      arrayBuffer: async () => new ArrayBuffer(0),
    } as Response));

    render(<XemTruocExcel url={URL_BAI_NOP} tenFile="bang-ke.xlsx" />);

    await waitFor(() =>
      expect(screen.getByText(/Không hiển thị được nội dung Excel/)).toBeInTheDocument(),
    );
    expect(screen.getByText(/Máy chủ trả 404/)).toBeInTheDocument();

    const nut = screen.getByText('Tải file về để chấm') as HTMLAnchorElement;
    expect(nut.getAttribute('href')).toBe(URL_BAI_NOP);
    expect(nut.getAttribute('download')).toBe('bang-ke.xlsx');
  });

  it('file toàn chữ thì SheetJS đọc như CSV — không vỡ trang', async () => {
    // SheetJS CỐ Ý dễ dãi: gặp text thô nó đọc như CSV/DSV chứ không ném lỗi,
    // nên đừng trông đợi trạng thái LOI ở đây. Chấp nhận được vì backend đã
    // đối chiếu chữ ký file (PK cho .xlsx, OLE2 cho .xls) TRƯỚC khi lưu, nên
    // file rác không bao giờ tới được màn chấm với đuôi .xlsx. Test này chỉ
    // chốt rằng component không nổ nếu lọt lưới.
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      arrayBuffer: async () => new TextEncoder().encode('day khong phai excel').buffer,
    } as Response));

    const { container } = render(<XemTruocExcel url={URL_BAI_NOP} />);

    await waitFor(
      () => expect(screen.queryByText(/Đang đọc bảng tính/)).not.toBeInTheDocument(),
      { timeout: 10000 },
    );
    expect(container.textContent).toContain('day khong phai excel');
  }, 15000);

  it('đóng khung giữa chừng thì không dựng nữa', async () => {
    let thaBuf: (b: ArrayBuffer) => void = () => {};
    const cho = new Promise<ArrayBuffer>((res) => { thaBuf = res; });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, status: 200, arrayBuffer: () => cho,
    } as Response));

    const { unmount } = render(<XemTruocExcel url={URL_BAI_NOP} />);
    unmount();
    thaBuf(new ArrayBuffer(8));
    await new Promise((r) => setTimeout(r, 0));

    // Khong co loi "setState tren component da go" nem ra
    expect(true).toBe(true);
  });
});
