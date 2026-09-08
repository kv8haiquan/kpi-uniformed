/**
 * src/components/lms/XemTruocWord.tsx
 * ===================================
 * Dựng nội dung file Word (.docx) ngay trong trình duyệt để giảng viên đọc bài
 * nộp mà không phải tải về.
 *
 * Vì sao dựng ở trình duyệt chứ không chuyển sang PDF ở máy chủ:
 * `FileService.convert_to_pdf` gọi LibreOffice qua `subprocess.run` đồng bộ,
 * chẹn event loop tới 60 giây mỗi file — không an toàn khi nhiều học viên nộp
 * cùng lúc. Dựng ở máy người chấm thì máy chủ không tốn gì.
 *
 * Giới hạn đã biết:
 *   - Chỉ đọc được .docx (Office 2007+). File .doc nhị phân cũ không thư viện
 *     JS nào đọc được → nơi gọi phải tự lo nhánh tải về.
 *   - Bố cục phức tạp (header/footer, ảnh nổi, bảng lồng nhau) có thể lệch so
 *     với Word. Luôn kèm nút tải bản gốc để đối chiếu khi cần.
 */

'use client';

import { useEffect, useRef, useState } from 'react';

interface Props {
  /**
   * URL bài nộp, ví dụ /uploads/lms/bai-thuc-hanh/abc_bao-cao.docx
   *
   * Nơi gọi PHẢI truyền `key={url}` để đổi bài nộp là dựng lại từ đầu. Component
   * cố ý không tự đặt lại trạng thái trong effect — làm vậy sinh một lượt render
   * thừa và bị `react-hooks/set-state-in-effect` bắt; để React thay mới cả
   * component theo key thì trạng thái ban đầu tự đúng.
   */
  url: string;
  /** Tên file gốc — dùng cho nút tải về */
  tenFile?: string | null;
  /** Chiều cao khung xem, mặc định 50vh */
  chieuCao?: string;
}

type TrangThai = 'DANG_TAI' | 'XONG' | 'LOI';

export default function XemTruocWord({ url, tenFile, chieuCao = '50vh' }: Props) {
  const khungRef = useRef<HTMLDivElement>(null);
  const [trangThai, setTrangThai] = useState<TrangThai>('DANG_TAI');
  const [loi, setLoi] = useState<string>('');

  useEffect(() => {
    // Cờ huỷ: người chấm có thể đóng modal giữa chừng, không ghi vào DOM đã gỡ
    let daHuy = false;

    (async () => {
      try {
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`Máy chủ trả ${resp.status}`);
        const blob = await resp.blob();
        if (daHuy) return;

        // Nạp thư viện theo yêu cầu — người chấm bài trắc nghiệm không phải tải
        const { renderAsync } = await import('docx-preview');
        if (daHuy || !khungRef.current) return;

        khungRef.current.innerHTML = '';
        await renderAsync(blob, khungRef.current, undefined, {
          className: 'docx',
          inWrapper: true,
          ignoreWidth: false,
          ignoreHeight: true,      // để nội dung chảy tự do, không cắt theo khổ giấy
          breakPages: true,
          experimental: true,      // hỗ trợ thêm bảng / tab stops
        });
        if (!daHuy) setTrangThai('XONG');
      } catch (e) {
        if (daHuy) return;
        setLoi(e instanceof Error ? e.message : 'Không đọc được file');
        setTrangThai('LOI');
      }
    })();

    return () => { daHuy = true; };
  }, [url]);

  if (trangThai === 'LOI') {
    return (
      <div className="border border-dashed border-gray-300 rounded-lg p-6 text-center bg-gray-50">
        <div className="text-3xl mb-1">📘</div>
        <p className="text-sm text-gray-700">Không hiển thị được nội dung Word</p>
        <p className="text-xs text-gray-500 mt-0.5">{loi}</p>
        <a
          href={url}
          download={tenFile || undefined}
          className="inline-block mt-2 px-3 py-1.5 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
        >
          Tải file về để chấm
        </a>
      </div>
    );
  }

  return (
    <div className="relative">
      {trangThai === 'DANG_TAI' && (
        <div
          className="absolute inset-0 flex flex-col items-center justify-center bg-gray-50 rounded-lg z-10"
          style={{ height: chieuCao }}
        >
          <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mb-2" />
          <p className="text-xs text-gray-500">Đang dựng nội dung Word…</p>
        </div>
      )}
      <div
        ref={khungRef}
        className="overflow-auto border border-gray-200 rounded-lg bg-white"
        style={{ height: chieuCao }}
      />
    </div>
  );
}
