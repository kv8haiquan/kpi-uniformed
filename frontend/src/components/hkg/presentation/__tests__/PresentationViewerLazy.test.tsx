import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import PresentationViewerLazy from '../PresentationViewerLazy';

// Next.js dynamic loading hiển thị fallback "Đang tải trình xem tài liệu..."
// trong jsdom (vì lazy load không resolve sync). Chúng ta chỉ verify
// fallback render đúng — pdfjs-dist không chạy trong jsdom được.
describe('PresentationViewerLazy', () => {
  it('hiển thị fallback loading khi component đang lazy-load', () => {
    render(
      <PresentationViewerLazy url="/fake.pdf" currentPage={1} isHost={false} />,
    );
    expect(
      screen.getByText(/Đang tải trình xem tài liệu/i),
    ).toBeInTheDocument();
  });
});
