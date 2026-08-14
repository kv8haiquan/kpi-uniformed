/**
 * ecosystem.config.js — PM2 process manager config cho Nền tảng Số HQKV8.
 *
 * TẠO MỚI 2026-05-01 (G4-deploy): trước đây 6 service được start qua CLI
 * thủ công rồi `pm2 save` vào dump.pm2. File này document hoá cấu hình thật
 * đang chạy + thêm `meeting_service` (HKG, port 8006).
 *
 * Sử dụng:
 *   pm2 start ecosystem.config.js --only meeting_service   # CHỈ start service mới
 *   pm2 reload ecosystem.config.js --only meeting_service  # Reload chỉ entry này
 *
 * ⚠️ KHÔNG chạy `pm2 reload ecosystem.config.js` (không --only) trên production
 * vì sẽ restart cả 6 service đang chạy.
 *
 * Pattern: 6 backend service dùng `bash -c 'venv/bin/python -m uvicorn ...'`
 * với cwd=backend/. Frontend dùng npm start.
 *
 * Verify cấu hình thực tế:
 *   pm2 jlist | python3 -c "import sys,json; ..."
 */

const REPO_ROOT = '/root/kpi-haiquan';
const BACKEND_CWD = `${REPO_ROOT}/backend`;
const FRONTEND_CWD = `${REPO_ROOT}/frontend`;

/** Helper tạo entry FastAPI service (bash + uvicorn). */
function fastapiService(name, module, port, { host = '0.0.0.0' } = {}) {
  return {
    name,
    cwd: BACKEND_CWD,
    script: '/usr/bin/bash',
    args: ['-c', `venv/bin/python -m uvicorn ${module}.main:app --host ${host} --port ${port}`],
    interpreter: 'none',
    exec_mode: 'fork',
    autorestart: true,
    max_restarts: 10,
    out_file: `/root/.pm2/logs/${name}-out.log`,
    error_file: `/root/.pm2/logs/${name}-error.log`,
    merge_logs: true,
    time: true,
  };
}

module.exports = {
  apps: [
    // ════════════════════════════════════════════════════════════════
    // 6 SERVICE HIỆN ĐANG CHẠY — recreate từ pm2 jlist (giữ nguyên cấu hình)
    // ════════════════════════════════════════════════════════════════
    fastapiService('kpi-backend',    'app',             8000),
    fastapiService('lms-backend',    'lms_service',     8001),
    fastapiService('forum-backend',  'forum_service',   8002),
    fastapiService('legal-backend',  'legal_service',   8003),
    fastapiService('portal-backend', 'portal_service',  8004),
    fastapiService('common-backend', 'common_service',  8005),
    {
      name: 'kpi-frontend',
      cwd: FRONTEND_CWD,
      script: '/usr/bin/npm',
      args: ['start', '--', '-p', '3000'],
      interpreter: '/usr/bin/node',
      exec_mode: 'fork',
      autorestart: true,
      max_restarts: 10,
      out_file: '/root/.pm2/logs/kpi-frontend-out.log',
      error_file: '/root/.pm2/logs/kpi-frontend-error.log',
      merge_logs: true,
      time: true,
    },

    // ════════════════════════════════════════════════════════════════
    // MEETING SERVICE (HKG) — MỚI 2026-05-01
    // Internal-only — bind 127.0.0.1 cho tới khi UAT pass + Nginx route mở
    // (xem README backend/meeting_service/)
    // ════════════════════════════════════════════════════════════════
    fastapiService('meeting-backend', 'meeting_service', 8006, { host: '127.0.0.1' }),

    // ════════════════════════════════════════════════════════════════
    // CHI TIEU SERVICE (Chỉ tiêu đơn vị) — MỚI 2026-06-04
    // Internal-only (bind 127.0.0.1) — Nginx/dev-rewrite đã trỏ localhost:8007.
    // ⚠️ Migration `create_chi_tieu_schema_20260604` CHƯA apply lên DB.
    //    Start service trước khi migrate → endpoint nghiệp vụ sẽ lỗi (chưa có
    //    schema chi_tieu). Chỉ start sau khi đã `alembic upgrade head`.
    // ════════════════════════════════════════════════════════════════
    fastapiService('chi-tieu-backend', 'chi_tieu_service', 8007, { host: '127.0.0.1' }),

    // ════════════════════════════════════════════════════════════════
    // ZALO WORKER — MỚI 2026-08-14
    // Không phải web service: không mở port, chỉ quét common.thong_bao theo
    // nhịp ZALO_CHU_KY_GIAY rồi gửi ZNS. Chạy tiến trình RIÊNG (không nhét vào
    // common-backend) để restart/tắt kênh Zalo không đụng tới API đang phục vụ.
    //
    // ⚠️ CHẠY DUY NHẤT 1 INSTANCE. Bảng common.zalo_outbox có UNIQUE trên
    //    thong_bao_id nên chạy 2 tiến trình không gửi trùng, nhưng sẽ tranh
    //    nhau và đẩy lỗi vào log vô ích.
    // ⚠️ Tắt kênh Zalo: `pm2 stop zalo-worker` là đủ và tức thì. Cờ
    //    ZALO_ENABLED/ZALO_DRY_RUN trong backend/.env chỉ đọc lúc khởi động.
    // ════════════════════════════════════════════════════════════════
    {
      name: 'zalo-worker',
      cwd: BACKEND_CWD,
      script: '/usr/bin/bash',
      args: ['-c', 'venv/bin/python -m common_service.workers.zalo_worker'],
      interpreter: 'none',
      exec_mode: 'fork',
      instances: 1,
      autorestart: true,
      max_restarts: 10,
      out_file: '/root/.pm2/logs/zalo-worker-out.log',
      error_file: '/root/.pm2/logs/zalo-worker-error.log',
      merge_logs: true,
      time: true,
    },
  ],
};
