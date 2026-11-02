/**
 * src/lib/so-tay-nhung.ts
 * ========================
 * Chuẩn bị tệp HTML của Sổ tay số trước khi nhúng vào iframe trên nền tảng.
 *
 * Tệp do phòng nghiệp vụ biên soạn và thay bản mới định kỳ, nên mọi điều chỉnh
 * của nền tảng làm TẠI ĐÂY (lúc hiển thị), không sửa tay vào tệp — sửa tay sẽ
 * mất ngay ở lần TCCB gửi bản cập nhật kế tiếp.
 *
 * Hai việc:
 *  1. Chặn tải NGUYÊN TỆP sổ (.html) về máy — quyết định 02/11/2026: chỉ dùng
 *     trực tuyến. Biểu mẫu .docx/.pdf, Xuất Excel, ghi chú .md... vẫn tải bình
 *     thường. Cả hai sổ đều tải qua <a download>.click(), nên chặn ở
 *     HTMLAnchorElement.prototype.click theo đuôi tệp là đủ, không cần biết tên
 *     hàm bên trong (tên hàm đổi theo phiên bản).
 *     Đây là rào chắn chống tải thông thường, KHÔNG phải bảo vệ tuyệt đối:
 *     nội dung đã về trình duyệt thì người cố ý vẫn lấy được.
 *  2. Ép thư viện SheetJS về 0.20.3 — bản 0.18.5 trên jsdelivr dính
 *     CVE-2023-30533 / CVE-2024-22363 (đã gỡ khỏi nền tảng trong đợt vá 31/07/2026).
 */

const XLSX_AN_TOAN = 'https://cdn.sheetjs.com/xlsx-0.20.3/package/dist/xlsx.full.min.js';
// Mọi bản xlsx tải từ jsdelivr/unpkg (npm chỉ có tới 0.18.5 — đều dính lỗi)
const RE_XLSX_CU = /https:\/\/(?:cdn\.jsdelivr\.net\/npm|unpkg\.com)\/xlsx@[^"'\s]+?\/dist\/xlsx\.full\.min\.js/g;

// Chạy TRƯỚC mọi mã của sổ (chèn ngay sau <head>)
const MA_CHAN = `<script>(function(){
  var laTepSo = function (ten) { return /\\.html?$/i.test(String(ten || '')); };
  var baoChan = function () {
    try { window.parent.postMessage({ type: 'KPI_SO_TAY_CHAN_TAI' }, location.origin); } catch (e) {}
  };
  var goc = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function () {
    if (this.download && laTepSo(this.download)) { baoChan(); return; }
    return goc.apply(this, arguments);
  };
  // Phòng khi sổ đặt sẵn <a download="...html"> trong giao diện cho người bấm
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[download]') : null;
    if (a && laTepSo(a.getAttribute('download'))) { e.preventDefault(); e.stopImmediatePropagation(); baoChan(); }
  }, true);
})();</script>
<style id="kpi-so-tay-nhung">
  /* Nút tải nguyên tệp: #btn-tai-sotay + #nk-tai (Sổ tay KTNB, Sổ nhật ký Đoàn), #dlBtn + #admBuild (Sổ tra cứu lỗi) */
  #btn-tai-sotay, #nk-tai, #dlBtn, #admBuild { display: none !important; }
</style>`;

export function chuanBiHtmlSoTay(html: string): string {
  const daVa = html.replace(RE_XLSX_CU, XLSX_AN_TOAN);
  // Chèn sau thẻ <head> đầu tiên; tệp không có <head> thì chèn lên đầu
  return /<head(\s[^>]*)?>/i.test(daVa)
    ? daVa.replace(/<head(\s[^>]*)?>/i, (m) => m + MA_CHAN)
    : MA_CHAN + daVa;
}
