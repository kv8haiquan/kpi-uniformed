/**
 * src/lib/so-tay-nhung.ts
 * ========================
 * Chuẩn bị tệp HTML của Sổ tay số trước khi nhúng vào iframe trên nền tảng.
 *
 * Tệp do phòng nghiệp vụ biên soạn và thay bản mới định kỳ, nên mọi điều chỉnh
 * của nền tảng làm TẠI ĐÂY (lúc hiển thị), không sửa tay vào tệp — sửa tay sẽ
 * mất ngay ở lần TCCB gửi bản cập nhật kế tiếp.
 *
 * Việc duy nhất: ép thư viện SheetJS về 0.20.3 — bản 0.18.5 trên jsdelivr dính
 * CVE-2023-30533 / CVE-2024-22363 (đã gỡ khỏi nền tảng trong đợt vá 31/07/2026).
 *
 * Tải nguyên tệp sổ về máy: ĐƯỢC PHÉP (đổi quyết định ngày 02/11/2026 — bản đầu
 * chặn tải). Các nút tải sẵn có của sổ tự lo việc này; khi chạy từ blob URL, sổ
 * dựng lại tệp từ bản chụp DOM lúc nạp trang, nên MỌI thứ chèn vào đây sẽ đi theo
 * bản tải về — đừng chèn mã chỉ có nghĩa trên nền tảng (chặn tải, postMessage...).
 */

const XLSX_AN_TOAN = 'https://cdn.sheetjs.com/xlsx-0.20.3/package/dist/xlsx.full.min.js';
// Mọi bản xlsx tải từ jsdelivr/unpkg (npm chỉ có tới 0.18.5 — đều dính lỗi)
const RE_XLSX_CU = /https:\/\/(?:cdn\.jsdelivr\.net\/npm|unpkg\.com)\/xlsx@[^"'\s]+?\/dist\/xlsx\.full\.min\.js/g;

export function chuanBiHtmlSoTay(html: string): string {
  return html.replace(RE_XLSX_CU, XLSX_AN_TOAN);
}
