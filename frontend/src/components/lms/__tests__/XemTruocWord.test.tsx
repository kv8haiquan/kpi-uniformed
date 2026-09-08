/**
 * Test cho XemTruocWord — khung dựng .docx trong trình duyệt.
 *
 * Kiểm phần NỐI DÂY của mình (tải file → giao cho thư viện → trạng thái hiển
 * thị), không kiểm chất lượng dựng của docx-preview: thư viện được thay bằng
 * bản giả để test chạy nhanh và không phụ thuộc file .docx thật.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import XemTruocWord from '../XemTruocWord';

const renderAsyncGia = vi.fn();
vi.mock('docx-preview', () => ({
  renderAsync: (...args: unknown[]) => renderAsyncGia(...args),
}));

const URL_BAI_NOP = '/uploads/lms/bai-thuc-hanh/abc_bao-cao.docx';

beforeEach(() => {
  renderAsyncGia.mockReset();
  renderAsyncGia.mockResolvedValue(undefined);
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function stubFetch(resp: Partial<Response> & { ok: boolean }) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(resp as Response));
}

describe('XemTruocWord', () => {
  it('tải file rồi giao blob cho docx-preview', async () => {
    const blob = new Blob(['noi dung docx']);
    stubFetch({ ok: true, status: 200, blob: async () => blob });

    render(<XemTruocWord url={URL_BAI_NOP} tenFile="bao-cao.docx" />);

    await waitFor(() => expect(renderAsyncGia).toHaveBeenCalledTimes(1));
    const [blobDaGui, khung] = renderAsyncGia.mock.calls[0];
    expect(blobDaGui).toBe(blob);
    expect(khung).toBeInstanceOf(HTMLElement);
    expect(fetch).toHaveBeenCalledWith(URL_BAI_NOP);
  });

  it('dựng xong thì tắt chỉ báo đang tải', async () => {
    stubFetch({ ok: true, status: 200, blob: async () => new Blob(['x']) });

    render(<XemTruocWord url={URL_BAI_NOP} />);
    expect(screen.getByText(/Đang dựng nội dung Word/)).toBeInTheDocument();

    await waitFor(() =>
      expect(screen.queryByText(/Đang dựng nội dung Word/)).not.toBeInTheDocument(),
    );
  });

  it('máy chủ trả lỗi → hiện nút tải về kèm mã lỗi', async () => {
    stubFetch({ ok: false, status: 404, blob: async () => new Blob([]) });

    render(<XemTruocWord url={URL_BAI_NOP} tenFile="bao-cao.docx" />);

    await waitFor(() =>
      expect(screen.getByText(/Không hiển thị được nội dung Word/)).toBeInTheDocument(),
    );
    expect(screen.getByText(/Máy chủ trả 404/)).toBeInTheDocument();

    const nut = screen.getByText('Tải file về để chấm') as HTMLAnchorElement;
    expect(nut.getAttribute('href')).toBe(URL_BAI_NOP);
    expect(nut.getAttribute('download')).toBe('bao-cao.docx');
    // Không được gọi thư viện khi file còn chưa tải về được
    expect(renderAsyncGia).not.toHaveBeenCalled();
  });

  it('file hỏng khiến thư viện ném lỗi → vẫn về trạng thái lỗi, không vỡ trang', async () => {
    stubFetch({ ok: true, status: 200, blob: async () => new Blob(['rac']) });
    renderAsyncGia.mockRejectedValue(new Error('Can not read docx'));

    render(<XemTruocWord url={URL_BAI_NOP} />);

    await waitFor(() =>
      expect(screen.getByText(/Không hiển thị được nội dung Word/)).toBeInTheDocument(),
    );
    expect(screen.getByText(/Can not read docx/)).toBeInTheDocument();
  });

  it('đóng khung giữa chừng thì không dựng nữa', async () => {
    let thaBlob: (b: Blob) => void = () => {};
    const choBlob = new Promise<Blob>((res) => { thaBlob = res; });
    stubFetch({ ok: true, status: 200, blob: () => choBlob });

    const { unmount } = render(<XemTruocWord url={URL_BAI_NOP} />);
    unmount();                       // người chấm đóng modal khi file chưa về
    thaBlob(new Blob(['x']));
    await new Promise((r) => setTimeout(r, 0));

    expect(renderAsyncGia).not.toHaveBeenCalled();
  });
});
