/**
 * Test đối chứng với docx-preview THẬT (không thay bằng bản giả) trên một file
 * .docx thật ở `fixtures/bao-cao-mau.docx`.
 *
 * Vì sao cần: XemTruocWord.test.tsx thay thư viện bằng bản giả nên chỉ chứng
 * minh phần nối dây của mình đúng, không chứng minh docx-preview đọc nổi file
 * Word do hệ thống nhận vào. Test này bù đúng chỗ đó — nếu nâng cấp thư viện
 * làm hỏng việc đọc file, nó đỏ ngay.
 */

import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import { readFileSync } from 'fs';
import { join } from 'path';
import XemTruocWord from '../XemTruocWord';

const DUONG_DAN = join(__dirname, 'fixtures', 'bao-cao-mau.docx');
const URL_BAI_NOP = '/uploads/lms/bai-thuc-hanh/abc_bao-cao-mau.docx';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('XemTruocWord — dựng file .docx thật', () => {
  it('đọc được nội dung và bảng trong file Word', async () => {
    const buf = readFileSync(DUONG_DAN);
    const blob = new Blob([new Uint8Array(buf)]);
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      blob: async () => blob,
    } as Response));

    const { container } = render(<XemTruocWord url={URL_BAI_NOP} />);

    // Dựng xong thì chỉ báo "đang tải" biến mất
    await waitFor(
      () => expect(screen.queryByText(/Đang dựng nội dung Word/)).not.toBeInTheDocument(),
      { timeout: 15000 },
    );

    // Không rơi vào nhánh lỗi
    expect(screen.queryByText(/Không hiển thị được nội dung Word/)).not.toBeInTheDocument();

    // Chữ trong file phải có mặt trong DOM đã dựng
    const chu = container.textContent || '';
    expect(chu).toContain('Bao cao thuc hanh');
    expect(chu).toContain('Nguyen Van A');
    expect(chu).toContain('Noi dung bai lam mau');

    // Bảng 2x2 phải ra đúng thẻ <table>, không bị bỏ mất
    expect(container.querySelector('table')).not.toBeNull();
    expect(chu).toContain('Tieu chi');
    expect(chu).toContain('Dat');
  }, 20000);
});
