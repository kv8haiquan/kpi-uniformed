/**
 * src/components/dashboard/LaurelWreath.tsx
 * ==========================================
 * Vòng nguyệt quế trang trí quanh ảnh công chức tiêu biểu.
 *
 * SVG thuần — không cần asset ngoài, co giãn mượt theo kích thước khung.
 * Hai nhánh lá đối xứng (nhánh phải là ảnh phản chiếu của nhánh trái qua
 * trục đứng x=50), kèm ngôi sao trên đỉnh và nút ruy băng dưới đáy.
 *
 * Dùng làm lớp phủ tuyệt đối quanh ảnh tròn (xem VinhDanhWidget).
 */

interface LaurelWreathProps {
  className?: string;
}

const CX = 50;
const CY = 50;

// Góc đặt lá (hệ toạ độ SVG, y hướng xuống: đáy = 90°, trái = 180°, đỉnh = 270°).
// Nhánh trái quét từ gần đáy lên gần đỉnh, chừa khoảng trống ở đỉnh cho ngôi sao.
const OUTER_ANGLES = [112, 130, 148, 166, 184, 202, 220, 236];
const INNER_ANGLES = [122, 140, 158, 176, 194, 212, 230];

function leaf(deg: number, r: number, rx: number, ry: number, key: string) {
  const a = (deg * Math.PI) / 180;
  const x = CX + r * Math.cos(a);
  const y = CY + r * Math.sin(a);
  // Xoay theo tiếp tuyến vòng tròn + hơi xoè ra ngoài cho dáng lá tự nhiên
  const rot = deg + 90 + 15;
  return (
    <ellipse
      key={key}
      cx={x}
      cy={y}
      rx={rx}
      ry={ry}
      transform={`rotate(${rot} ${x} ${y})`}
      fill="url(#laurelGold)"
      stroke="#b45309"
      strokeWidth={0.4}
    />
  );
}

export default function LaurelWreath({ className = '' }: LaurelWreathProps) {
  // Một nhánh (trái) — nhánh phải tái sử dụng bằng phép phản chiếu
  const branch = (
    <g>
      {OUTER_ANGLES.map((d, i) => leaf(d, 44, 6.5, 3, `o${i}`))}
      {INNER_ANGLES.map((d, i) => leaf(d, 38, 5, 2.4, `i${i}`))}
    </g>
  );

  return (
    <svg viewBox="0 0 100 100" className={className} aria-hidden="true">
      <defs>
        <linearGradient id="laurelGold" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#fcd34d" />
          <stop offset="55%" stopColor="#f59e0b" />
          <stop offset="100%" stopColor="#b45309" />
        </linearGradient>
      </defs>

      {/* Nhánh trái */}
      {branch}
      {/* Nhánh phải — phản chiếu qua trục đứng x = 50 */}
      <g transform="translate(100,0) scale(-1,1)">{branch}</g>

      {/* Ngôi sao 5 cánh trên đỉnh (giữa khoảng trống của hai nhánh) */}
      <path
        d="M50 3 L51.8 8.2 L57.3 8.2 L52.9 11.6 L54.6 16.8 L50 13.6 L45.4 16.8 L47.1 11.6 L42.7 8.2 L48.2 8.2 Z"
        fill="url(#laurelGold)"
        stroke="#b45309"
        strokeWidth={0.4}
      />

      {/* Nút thắt + dải ruy băng dưới đáy (nơi hai nhánh giao nhau) */}
      <path d="M50 94 Q45 99 41 98 Q44.5 95.8 47.5 95.2 Z" fill="#d97706" />
      <path d="M50 94 Q55 99 59 98 Q55.5 95.8 52.5 95.2 Z" fill="#d97706" />
      <circle cx={50} cy={93.5} r={2.6} fill="url(#laurelGold)" stroke="#b45309" strokeWidth={0.4} />
    </svg>
  );
}
