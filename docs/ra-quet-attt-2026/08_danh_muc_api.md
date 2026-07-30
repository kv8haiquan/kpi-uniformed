# Mục 8 — Danh mục API các dịch vụ phần mềm KPI & Digital Learning

> Sinh tự động từ đặc tả OpenAPI của từng service, ngày 30/07/2026.
**Tổng cộng: 555 endpoints / 8 services.**
> Toàn bộ API đều đặt sau nginx reverse proxy (HTTPS, kpihaiquan.vn); xác thực JWT Bearer trừ endpoint đăng nhập/health.

## KPI Backend — port 8000 (239 endpoints)
- Phiên bản: `0.4.0-alpha` — Tiêu đề: Hải quan KV8 - KPI System
- Base URL public: `https://kpihaiquan.vn/api`

| Method | Path | Chức năng |
|---|---|---|
| GET | `/` | API Health Check |
| GET | `/api/v1/admin/cap-do` | Danh sách Cấp độ phức tạp |
| POST | `/api/v1/admin/cap-do` | Tạo mới Cấp độ |
| GET | `/api/v1/admin/cap-do/{cap_do_id}` | Chi tiết Cấp độ |
| PUT | `/api/v1/admin/cap-do/{cap_do_id}` | Cập nhật Cấp độ |
| DELETE | `/api/v1/admin/cap-do/{cap_do_id}` | Vô hiệu hóa Cấp độ |
| PUT | `/api/v1/admin/cong-chuc/{cc_id}/kpi-version` | Pin KPI version cho 1 CC |
| GET | `/api/v1/admin/danh-muc-cv` | Danh sách Danh mục công việc |
| POST | `/api/v1/admin/danh-muc-cv` | Tạo mới Danh mục công việc |
| GET | `/api/v1/admin/danh-muc-cv/{dm_id}` | Chi tiết Danh mục công việc |
| PUT | `/api/v1/admin/danh-muc-cv/{dm_id}` | Cập nhật Danh mục công việc |
| DELETE | `/api/v1/admin/danh-muc-cv/{dm_id}` | Vô hiệu hóa Danh mục công việc |
| GET | `/api/v1/admin/danh-muc-pl3` | List danh mục PL3 với filter (admin) |
| POST | `/api/v1/admin/danh-muc-pl3` | Tạo mục PL3 |
| POST | `/api/v1/admin/danh-muc-pl3/import/commit` | Commit import Excel PL3 (insert/update atomic) |
| POST | `/api/v1/admin/danh-muc-pl3/import/dry-run` | Dry-run import Excel PL3 (KHÔNG insert) |
| GET | `/api/v1/admin/danh-muc-pl3/{dm_id}` | Detail mục PL3 |
| PUT | `/api/v1/admin/danh-muc-pl3/{dm_id}` | Sửa mục PL3 |
| DELETE | `/api/v1/admin/danh-muc-pl3/{dm_id}` | Soft delete (is_active=FALSE) |
| GET | `/api/v1/admin/danh-muc-v1` | List V1 (legacy, read-only sau cutover) |
| PUT | `/api/v1/admin/danh-muc-v1/{dm_id}/deactivate` | Deactivate V1 mục |
| PUT | `/api/v1/admin/don-vi/{dv_id}/kpi-version` | Pin KPI version cho cả đơn vị (bulk) |
| GET | `/api/v1/admin/lich-su-dieu-chuyen` | Lịch sử điều chuyển & thay đổi trạng thái toàn cơ quan (phân trang) |
| GET | `/api/v1/admin/sp-chuan` | Danh sách SP Chuẩn |
| POST | `/api/v1/admin/sp-chuan` | Tạo mới SP Chuẩn |
| GET | `/api/v1/admin/sp-chuan/{sp_id}` | Chi tiết SP Chuẩn |
| PUT | `/api/v1/admin/sp-chuan/{sp_id}` | Cập nhật SP Chuẩn |
| DELETE | `/api/v1/admin/sp-chuan/{sp_id}` | Vô hiệu hóa SP Chuẩn |
| GET | `/api/v1/admin/stats` | Thống kê tổng quan Admin |
| GET | `/api/v1/admin/users` | Danh sách tất cả người dùng |
| POST | `/api/v1/admin/users` | Tạo mới tài khoản |
| GET | `/api/v1/admin/users/{user_id}` | Chi tiết người dùng |
| PUT | `/api/v1/admin/users/{user_id}` | Cập nhật thông tin người dùng |
| DELETE | `/api/v1/admin/users/{user_id}` | Xóa hoàn toàn người dùng |
| PUT | `/api/v1/admin/users/{user_id}/reset-password` | Đặt lại mật khẩu về mặc định |
| PUT | `/api/v1/admin/users/{user_id}/status` | Kích hoạt/Vô hiệu hóa tài khoản |
| PUT | `/api/v1/admin/users/{user_id}/transfer` | Điều chuyển nhân sự |
| GET | `/api/v1/admin/users/{user_id}/transfer-history` | Lịch sử điều chuyển của nhân sự |
| PUT | `/api/v1/admin/users/{user_id}/transfer-history/{history_id}` | Điều chỉnh một bản ghi lịch sử điều chuyển/trạng thái |
| DELETE | `/api/v1/admin/users/{user_id}/transfer-history/{history_id}` | Xóa một bản ghi lịch sử điều chuyển/trạng thái |
| GET | `/api/v1/admin/vai-tro` | Danh sách tất cả vai trò |
| POST | `/api/v1/auth/change-password` | Change Password |
| POST | `/api/v1/auth/login` | Đăng nhập hệ thống |
| GET | `/api/v1/auth/me` | Lấy thông tin user hiện tại |
| PUT | `/api/v1/auth/update-profile` | Update Profile |
| PUT | `/api/v1/bao-cao-xep-loai-quy/chi-tiet/{chi_tiet_id}/de-xuat` | Dieu Chinh De Xuat Quy |
| GET | `/api/v1/bao-cao-xep-loai-quy/cho-phe-duyet` | Get Danh Sach Cho Phe Duyet Quy |
| GET | `/api/v1/bao-cao-xep-loai-quy/danh-sach` | Get Danh Sach Bao Cao Quy |
| GET | `/api/v1/bao-cao-xep-loai-quy/don-vi/quy/{quy}/nam/{nam}` | Get Or Create Bao Cao Quy Don Vi |
| GET | `/api/v1/bao-cao-xep-loai-quy/{bao_cao_id}` | Get Chi Tiet Bao Cao Quy |
| POST | `/api/v1/bao-cao-xep-loai-quy/{bao_cao_id}/gui-duyet` | Gui Duyet Bao Cao Quy |
| POST | `/api/v1/bao-cao-xep-loai-quy/{bao_cao_id}/phe-duyet` | Phe Duyet Bao Cao Quy |
| POST | `/api/v1/bao-cao-xep-loai-quy/{bao_cao_id}/tinh-lai` | Tinh Lai Bao Cao Quy |
| PUT | `/api/v1/bao-cao-xep-loai/chi-tiet/{chi_tiet_id}/de-xuat` | De Xuat Xep Loai |
| PUT | `/api/v1/bao-cao-xep-loai/chi-tiet/{chi_tiet_id}/quyet-dinh` | Quyet Dinh Xep Loai |
| GET | `/api/v1/bao-cao-xep-loai/cho-phe-duyet` | Get Bao Cao Cho Phe Duyet |
| GET | `/api/v1/bao-cao-xep-loai/danh-sach/thang/{thang}/nam/{nam}` | Get Danh Sach Bao Cao |
| GET | `/api/v1/bao-cao-xep-loai/don-vi/thang/{thang}/nam/{nam}` | Get Bao Cao Don Vi |
| GET | `/api/v1/bao-cao-xep-loai/thong-ke/thang/{thang}/nam/{nam}` | Get Thong Ke Chi Cuc |
| GET | `/api/v1/bao-cao-xep-loai/{bao_cao_id}` | Get Bao Cao Chi Tiet |
| POST | `/api/v1/bao-cao-xep-loai/{bao_cao_id}/gui-duyet` | Gui Duyet Bao Cao |
| POST | `/api/v1/bao-cao-xep-loai/{bao_cao_id}/phe-duyet` | Phe Duyet Bao Cao |
| POST | `/api/v1/bao-cao-xep-loai/{bao_cao_id}/tra-lai` | Tra Lai Bao Cao |
| GET | `/api/v1/cong-chuc` | Lấy danh sách công chức |
| GET | `/api/v1/cong-chuc/don-vi/current` | Lấy danh sách CC cùng đơn vị |
| GET | `/api/v1/cong-chuc/pho-don-vi/{don_vi_id}` | Lấy danh sách Phó đơn vị |
| GET | `/api/v1/cong-chuc/{cong_chuc_id}` | Lấy chi tiết công chức |
| POST | `/api/v1/danh-gia-lanh-dao/dde` | Create Or Update Dde |
| GET | `/api/v1/danh-gia-lanh-dao/dde/cho-phe-duyet` | Get Dde Cho Phe Duyet |
| GET | `/api/v1/danh-gia-lanh-dao/dde/cong-chuc/{cong_chuc_id}/thang/{thang}/nam/{nam}` | Get Dde Cong Chuc |
| GET | `/api/v1/danh-gia-lanh-dao/dde/lich-su` | Lấy lịch sử phê duyệt đánh giá d,đ,e |
| GET | `/api/v1/danh-gia-lanh-dao/dde/nguoi-phe-duyet` | Get Nguoi Phe Duyet Dde Api |
| GET | `/api/v1/danh-gia-lanh-dao/dde/thang/{thang}/nam/{nam}` | Get Danh Gia Dde |
| POST | `/api/v1/danh-gia-lanh-dao/dde/thang/{thang}/nam/{nam}/gui-duyet` | Gui Duyet Dde |
| POST | `/api/v1/danh-gia-lanh-dao/dde/{dde_id}/phe-duyet` | Phe Duyet Dde |
| POST | `/api/v1/danh-gia-lanh-dao/dde/{dde_id}/tra-lai` | Tra Lai Dde |
| GET | `/api/v1/danh-gia/kpi/thang/{thang}/nam/{nam}` | Get Kpi Summary |
| GET | `/api/v1/danh-gia/nguoi-phe-duyet` | Get Nguoi Phe Duyet |
| POST | `/api/v1/danh-gia/phe-duyet-tieu-chi-bulk` | Phe Duyet Tieu Chi Bulk |
| GET | `/api/v1/danh-gia/tieu-chi-chung` | Get Danh Muc Tieu Chi Chung |
| GET | `/api/v1/danh-gia/tieu-chi/cho-phe-duyet` | Get Danh Sach Cho Phe Duyet |
| GET | `/api/v1/danh-gia/tieu-chi/cong-chuc/{cong_chuc_id}/thang/{thang}/nam/{nam}` | Get Tieu Chi Cong Chuc |
| GET | `/api/v1/danh-gia/tieu-chi/lich-su` | Lấy lịch sử phê duyệt tiêu chí chung |
| GET | `/api/v1/danh-gia/tieu-chi/thang/{thang}/nam/{nam}` | Get Tu Danh Gia Tieu Chi |
| GET | `/api/v1/danh-gia/tieu-chi/{danh_gia_thang_id}/chi-tiet` | Get Chi Tiet Phe Duyet |
| POST | `/api/v1/danh-gia/tu-danh-gia` | Tu Danh Gia Tieu Chi |
| POST | `/api/v1/danh-gia/{danh_gia_thang_id}/dieu-chinh-danh-gia-thang` | Dieu Chinh Danh Gia Thang |
| POST | `/api/v1/danh-gia/{danh_gia_thang_id}/phe-duyet-tieu-chi` | Phe Duyet Tieu Chi Chung |
| POST | `/api/v1/danh-gia/{danh_gia_thang_id}/tra-lai-tieu-chi` | Tra Lai Tieu Chi Da Duyet |
| POST | `/api/v1/danh-gia/{danh_gia_thang_id}/tu-choi-tieu-chi` | Tu Choi Tieu Chi Chung |
| GET | `/api/v1/danh-muc/cap-do-phuc-tap` | Lấy danh sách cấp độ phức tạp |
| GET | `/api/v1/danh-muc/cong-tac` | Danh sách công tác PL3 (V2) — distinct theo lĩnh vực |
| GET | `/api/v1/danh-muc/danh-muc-sp` | Lấy danh sách công việc |
| GET | `/api/v1/danh-muc/danh-muc-sp/{danh_muc_id}` | Lấy chi tiết công việc |
| GET | `/api/v1/danh-muc/linh-vuc` | Danh sách 15 lĩnh vực PL3 (V2) |
| GET | `/api/v1/danh-muc/nhiem-vu` | Danh sách nhiệm vụ PL3 (V2) — distinct theo lĩnh vực + công tác |
| GET | `/api/v1/danh-muc/nhom-cong-viec` | Lấy danh sách nhóm công việc |
| GET | `/api/v1/danh-muc/sp-chuan` | Lấy danh sách SP chuẩn |
| GET | `/api/v1/danh-muc/sp-cong-viec/pl3` | Danh sách mục PL3 — search/filter/pagination cho UI V2 |
| POST | `/api/v1/dieu-chinh-kqcv` | LĐ tạo bản đề xuất điều chỉnh CV |
| GET | `/api/v1/dieu-chinh-kqcv/cho-toi-duyet` | List bản điều chỉnh tôi là người duyệt |
| GET | `/api/v1/dieu-chinh-kqcv/lich-su-cv/{ke_khai_id}` | Lịch sử mọi lần điều chỉnh của 1 CV |
| GET | `/api/v1/dieu-chinh-kqcv/me` | List bản điều chỉnh tôi đề xuất |
| PUT | `/api/v1/dieu-chinh-kqcv/{dc_id}` | Sửa bản điều chỉnh khi còn NHAP |
| DELETE | `/api/v1/dieu-chinh-kqcv/{dc_id}` | Xóa bản điều chỉnh NHAP |
| POST | `/api/v1/dieu-chinh-kqcv/{dc_id}/gui-duyet` | LĐ gửi điều chỉnh lên cấp trên duyệt |
| POST | `/api/v1/dieu-chinh-kqcv/{dc_id}/phe-duyet` | Cấp trên duyệt + áp dụng vào kpi_submission |
| POST | `/api/v1/dieu-chinh-kqcv/{dc_id}/tra-lai` | Trả lại bản điều chỉnh đã duyệt nhầm về NHAP |
| POST | `/api/v1/dieu-chinh-kqcv/{dc_id}/tu-choi` | Cấp trên từ chối điều chỉnh |
| GET | `/api/v1/doi-soat-danh-gia/thang/{thang}/nam/{nam}` | Get Doi Soat |
| GET | `/api/v1/doi-soat-danh-gia/thang/{thang}/nam/{nam}/export` | Export Doi Soat |
| GET | `/api/v1/don-vi` | Lấy danh sách đơn vị |
| GET | `/api/v1/don-vi/tree/all` | Lấy cây đơn vị |
| GET | `/api/v1/don-vi/{don_vi_id}` | Lấy chi tiết đơn vị |
| GET | `/api/v1/export/bao-cao-tong-hop/quy/{quy}/nam/{nam}` | Export Bao Cao Tong Hop Quy |
| GET | `/api/v1/export/bao-cao-tong-hop/thang/{thang}/nam/{nam}` | Export Bao Cao Tong Hop |
| GET | `/api/v1/export/ca-nhan/thang/{thang}/nam/{nam}` | Export Ca Nhan |
| GET | `/api/v1/export/don-vi-tong-hop/quy/{quy}/nam/{nam}` | Export Don Vi Tong Hop Quy |
| GET | `/api/v1/export/don-vi-tong-hop/thang/{thang}/nam/{nam}` | Export Don Vi Tong Hop |
| GET | `/api/v1/export/don-vi/quy/{quy}/nam/{nam}` | Export Don Vi Quy |
| GET | `/api/v1/export/don-vi/thang/{thang}/nam/{nam}` | Export Don Vi |
| GET | `/api/v1/export/mau05-doi-moi/thang/{thang}/nam/{nam}` | Export Mau05 Doi Moi |
| GET | `/api/v1/export/tong-hop/thang/{thang}/nam/{nam}` | Export Tong Hop |
| GET | `/api/v1/hdld/cho-duyet` | List Cho Duyet |
| GET | `/api/v1/hdld/da-duyet` | List Da Duyet |
| GET | `/api/v1/hdld/danh-gia` | Get Danh Gia |
| GET | `/api/v1/hdld/danh-gia/lich-su` | Lich Su |
| POST | `/api/v1/hdld/danh-gia/{dg_id}/duyet` | Duyet Danh Gia |
| POST | `/api/v1/hdld/danh-gia/{dg_id}/nop` | Nop Danh Gia |
| POST | `/api/v1/hdld/danh-gia/{dg_id}/tra-lai` | Tra Lai Danh Gia |
| PUT | `/api/v1/hdld/danh-gia/{dg_id}/tu-danh-gia` | Tu Danh Gia |
| GET | `/api/v1/hdld/nguoi-duyet` | List Nguoi Duyet |
| GET | `/api/v1/hdld/tieu-chi` | List Tieu Chi |
| GET | `/api/v1/in-bang-ke/bang-ke-cong-viec-quy/{quy}/{nam}` | Export Bang Ke Cong Viec Quy |
| GET | `/api/v1/in-bang-ke/bang-ke-cong-viec-quy/{quy}/{nam}/cua-cc/{cong_chuc_id}` | Export Bang Ke Cong Viec Quy Cua Cc |
| GET | `/api/v1/in-bang-ke/bang-ke-cong-viec/{thang}/{nam}` | Export Bang Ke Cong Viec |
| GET | `/api/v1/in-bang-ke/bang-ke-cong-viec/{thang}/{nam}/cua-cc/{cong_chuc_id}` | Export Bang Ke Cong Viec Thang Cua Cc |
| GET | `/api/v1/in-bang-ke/phieu-danh-gia-quy/{quy}/{nam}` | Export Phieu Danh Gia Quy |
| GET | `/api/v1/in-bang-ke/phieu-danh-gia-quy/{quy}/{nam}/cua-cc/{cong_chuc_id}` | Export Phieu Danh Gia Quy Cua Cc |
| GET | `/api/v1/in-bang-ke/phieu-danh-gia/{thang}/{nam}` | Export Phieu Danh Gia |
| GET | `/api/v1/in-bang-ke/phieu-danh-gia/{thang}/{nam}/cua-cc/{cong_chuc_id}` | Export Phieu Danh Gia Thang Cua Cc |
| GET | `/api/v1/ke-khai` | Lấy danh sách kê khai của bản thân |
| POST | `/api/v1/ke-khai` | Tạo kê khai mới |
| GET | `/api/v1/ke-khai-lanh-dao` | Get Ke Khai Lanh Dao |
| POST | `/api/v1/ke-khai-lanh-dao` | Create Ke Khai Lanh Dao |
| GET | `/api/v1/ke-khai-lanh-dao/cho-phe-duyet` | Get Ke Khai Cho Phe Duyet |
| GET | `/api/v1/ke-khai-lanh-dao/cong-chuc/{cong_chuc_id}` | Get Ke Khai Ld Cong Chuc |
| GET | `/api/v1/ke-khai-lanh-dao/lich-su` | Lấy lịch sử phê duyệt kê khai lãnh đạo |
| GET | `/api/v1/ke-khai-lanh-dao/nguoi-phe-duyet` | Get Nguoi Phe Duyet |
| GET | `/api/v1/ke-khai-lanh-dao/thong-ke/thang` | Get Thong Ke |
| PUT | `/api/v1/ke-khai-lanh-dao/{ke_khai_id}` | Update Ke Khai Lanh Dao |
| DELETE | `/api/v1/ke-khai-lanh-dao/{ke_khai_id}` | Delete Ke Khai Lanh Dao |
| POST | `/api/v1/ke-khai-lanh-dao/{ke_khai_id}/gui-duyet` | Gui Duyet Ke Khai |
| POST | `/api/v1/ke-khai-lanh-dao/{ke_khai_id}/phe-duyet` | Phe Duyet Ke Khai Lanh Dao |
| POST | `/api/v1/ke-khai-lanh-dao/{ke_khai_id}/tra-lai` | Tra Lai Ke Khai Lanh Dao |
| POST | `/api/v1/ke-khai-v2` | Tạo kê khai V2 |
| GET | `/api/v1/ke-khai-v2/favorites` | Danh sách công việc yêu thích của bản thân |
| POST | `/api/v1/ke-khai-v2/favorites` | Đánh dấu 1 mục PL3 là yêu thích (idempotent) |
| DELETE | `/api/v1/ke-khai-v2/favorites/{danh_muc_sp_id}` | Bỏ yêu thích 1 mục PL3 |
| GET | `/api/v1/ke-khai-v2/me` | Danh sách kê khai V2 của bản thân |
| POST | `/api/v1/ke-khai-v2/nhieu-ngay` | Tạo kê khai V2 cho nhiều ngày |
| GET | `/api/v1/ke-khai-v2/recent` | Danh sách công việc đã dùng gần đây (look-back tối đa 3 tháng) |
| GET | `/api/v1/ke-khai-v2/thong-ke/thang` | Thống kê tổng SP V2 trong tháng (banner UI) |
| GET | `/api/v1/ke-khai-v2/{ke_khai_id}` | Chi tiết kê khai V2 |
| PUT | `/api/v1/ke-khai-v2/{ke_khai_id}` | Sửa kê khai V2 (NHAP/TU_CHOI) |
| DELETE | `/api/v1/ke-khai-v2/{ke_khai_id}` | Xoá kê khai V2 (soft delete, NHAP/TU_CHOI) |
| GET | `/api/v1/ke-khai/cong-chuc/{cong_chuc_id}` | Xem kê khai của công chức (dành cho Lãnh đạo/Admin) |
| POST | `/api/v1/ke-khai/gui-duyet-bulk` | Gửi duyệt nhiều kê khai cùng lúc |
| GET | `/api/v1/ke-khai/nguoi-phe-duyet` | Lấy danh sách người phê duyệt phù hợp |
| POST | `/api/v1/ke-khai/nhieu-ngay` | Tạo kê khai cho nhiều ngày cùng lúc |
| GET | `/api/v1/ke-khai/thong-ke/thang` | Thống kê kê khai theo tháng |
| GET | `/api/v1/ke-khai/{ke_khai_id}` | Lấy chi tiết kê khai |
| PUT | `/api/v1/ke-khai/{ke_khai_id}` | Cập nhật kê khai |
| DELETE | `/api/v1/ke-khai/{ke_khai_id}` | Xóa kê khai |
| POST | `/api/v1/ke-khai/{ke_khai_id}/gui-duyet` | Gửi kê khai đi phê duyệt |
| GET | `/api/v1/kpi-lanh-dao-v2/feature-flag` | Cấu hình áp dụng công thức KPI lãnh đạo mới |
| GET | `/api/v1/kpi-lanh-dao-v2/me` | Tự xem KPI lãnh đạo của mình (công thức mới) |
| GET | `/api/v1/kpi-lanh-dao-v2/me/cong-viec` | List chi tiết CV trong scope KPI của LĐ (yêu cầu 1 - 06/05/2026) |
| GET | `/api/v1/kpi-lanh-dao-v2/{cong_chuc_id}` | Xem KPI lãnh đạo của người khác (CCT + Admin) |
| GET | `/api/v1/nghi-phep` | Get Nghi Phep List |
| POST | `/api/v1/nghi-phep` | Create Nghi Phep |
| POST | `/api/v1/nghi-phep/bulk` | Create Nghi Phep Bulk |
| GET | `/api/v1/nghi-phep/cho-phe-duyet` | Get Cho Phe Duyet |
| GET | `/api/v1/nghi-phep/cong-chuc/{cong_chuc_id}` | Get Nghi Phep Cong Chuc |
| GET | `/api/v1/nghi-phep/lich-su` | Get Lich Su Phe Duyet |
| GET | `/api/v1/nghi-phep/nguoi-phe-duyet` | Get Nguoi Phe Duyet |
| GET | `/api/v1/nghi-phep/thong-ke` | Get Thong Ke Ca Nhan |
| GET | `/api/v1/nghi-phep/thong-ke/don-vi/{don_vi_id}` | Get Thong Ke Don Vi |
| GET | `/api/v1/nghi-phep/tong-ngay-nghi` | Get Tong Ngay Nghi Thang |
| GET | `/api/v1/nghi-phep/{nghi_phep_id}` | Get Nghi Phep Detail |
| PUT | `/api/v1/nghi-phep/{nghi_phep_id}` | Update Nghi Phep |
| DELETE | `/api/v1/nghi-phep/{nghi_phep_id}` | Delete Nghi Phep |
| POST | `/api/v1/nghi-phep/{nghi_phep_id}/phe-duyet` | Phe Duyet Nghi Phep |
| POST | `/api/v1/nghi-phep/{nghi_phep_id}/tra-lai` | Tra Lai Nghi Phep |
| POST | `/api/v1/nghi-phep/{nghi_phep_id}/tu-choi` | Tu Choi Nghi Phep |
| GET | `/api/v1/phan-cong-phu-trach` | Danh sách phân công phụ trách |
| POST | `/api/v1/phan-cong-phu-trach` | Tạo phân công mới |
| GET | `/api/v1/phan-cong-phu-trach/_meta/don-vi-kha-dung` | Danh sách đơn vị có thể được phân công phụ trách |
| GET | `/api/v1/phan-cong-phu-trach/_meta/don-vi-with-current` | Danh sách đơn vị + LĐ đang phụ trách hiện tại (cho UI checkbox) |
| GET | `/api/v1/phan-cong-phu-trach/_meta/lanh-dao-kha-dung` | Danh sách CCT/PCCT có thể được phân công |
| GET | `/api/v1/phan-cong-phu-trach/me/active` | Lấy danh sách đơn vị mà PCCT/CCT đang phụ trách (active hôm nay) |
| PUT | `/api/v1/phan-cong-phu-trach/me/replace` | PCCT/CCT thay thế toàn bộ phân công đang active của chính mình |
| GET | `/api/v1/phan-cong-phu-trach/{pc_id}` | Xem chi tiết 1 phân công |
| PUT | `/api/v1/phan-cong-phu-trach/{pc_id}` | Cập nhật phân công (chỉ hieu_luc_den + ghi_chu) |
| DELETE | `/api/v1/phan-cong-phu-trach/{pc_id}` | Xóa phân công (soft delete) |
| POST | `/api/v1/phan-cong-phu-trach/{pc_id}/ket-thuc` | Kết thúc phân công tại 1 ngày |
| GET | `/api/v1/phe-duyet/lich-su` | Lấy lịch sử phê duyệt kê khai |
| GET | `/api/v1/phe-duyet/pending` | Lấy danh sách kê khai chờ phê duyệt |
| GET | `/api/v1/phe-duyet/thong-ke` | Thống kê kê khai chờ phê duyệt |
| POST | `/api/v1/phe-duyet/tra-lai-bulk` | Trả lại nhiều kê khai đã phê duyệt |
| POST | `/api/v1/phe-duyet/xu-ly` | Phê duyệt hoặc từ chối kê khai |
| POST | `/api/v1/phe-duyet/{ke_khai_id}` | Phê duyệt/từ chối một kê khai |
| POST | `/api/v1/phe-duyet/{ke_khai_id}/tra-lai` | Trả lại kê khai đã phê duyệt |
| POST | `/api/v1/phieu-danh-gia-quy/` | Upsert Phieu Nhap |
| GET | `/api/v1/phieu-danh-gia-quy/cho-duyet` | List Phieu Cho Duyet |
| GET | `/api/v1/phieu-danh-gia-quy/cua-toi` | Get Phieu Cua Toi |
| GET | `/api/v1/phieu-danh-gia-quy/kiem-tra-du-dieu-kien` | Kiem Tra Du Dieu Kien |
| POST | `/api/v1/phieu-danh-gia-quy/{phieu_id}/gui-duyet` | Gui Duyet Phieu |
| POST | `/api/v1/phieu-danh-gia-quy/{phieu_id}/phe-duyet` | Phe Duyet Phieu |
| POST | `/api/v1/phieu-danh-gia-quy/{phieu_id}/tra-lai` | Tra Lai Phieu |
| POST | `/api/v1/phieu-danh-gia-quy/{phieu_id}/tu-choi` | Tu Choi Phieu |
| POST | `/api/v1/phieu-danh-gia-thang/` | Upsert Phieu Nhap |
| GET | `/api/v1/phieu-danh-gia-thang/cho-duyet` | List Phieu Cho Duyet |
| GET | `/api/v1/phieu-danh-gia-thang/cua-toi` | Get Phieu Cua Toi |
| GET | `/api/v1/phieu-danh-gia-thang/kiem-tra-du-dieu-kien` | Kiem Tra Du Dieu Kien |
| POST | `/api/v1/phieu-danh-gia-thang/{phieu_id}/gui-duyet` | Gui Duyet Phieu |
| POST | `/api/v1/phieu-danh-gia-thang/{phieu_id}/phe-duyet` | Phe Duyet Phieu |
| POST | `/api/v1/phieu-danh-gia-thang/{phieu_id}/tra-lai` | Tra Lai Phieu |
| POST | `/api/v1/phieu-danh-gia-thang/{phieu_id}/tu-choi` | Tu Choi Phieu |
| GET | `/api/v1/sp-cong-viec-chuan` | Get Sp Chuan List |
| GET | `/api/v1/xep-loai-quy/chi-tiet/{cong_chuc_id}` | Get Chi Tiet Quy |
| POST | `/api/v1/xep-loai-quy/tinh-lai` | Tinh Lai Quy |
| GET | `/api/v1/xep-loai-quy/tong-hop` | Get Tong Hop Quy |
| GET | `/api/v1/xep-loai/chi-tiet/{cong_chuc_id}` | Get Chi Tiet Xep Loai |
| GET | `/api/v1/xep-loai/danh-sach-don-vi` | Get Danh Sach Don Vi |
| POST | `/api/v1/xep-loai/khoa-du-lieu` | Khoa Du Lieu |
| POST | `/api/v1/xep-loai/mo-khoa-du-lieu` | Mo Khoa Du Lieu |
| GET | `/api/v1/xep-loai/tong-hop` | Get Tong Hop Xep Loai |
| GET | `/health` | Health Check |

## LMS - Đào tạo — port 8001 (111 endpoints)
- Phiên bản: `0.1.0` — Tiêu đề: HQKV8 Dao tao
- Base URL public: `https://kpihaiquan.vn/api/v1/lms`

| Method | Path | Chức năng |
|---|---|---|
| GET | `/api/v1/lms/bai-hoc/{id}` | Chi Tiet Bai Hoc |
| PUT | `/api/v1/lms/bai-hoc/{id}` | Cap Nhat Bai Hoc |
| PATCH | `/api/v1/lms/bai-hoc/{id}/tien-do` | Cap Nhat Tien Do |
| GET | `/api/v1/lms/bai-kiem-tra/{id}` | Chi Tiet Bkt |
| PUT | `/api/v1/lms/bai-kiem-tra/{id}` | Cap Nhat Bkt |
| DELETE | `/api/v1/lms/bai-kiem-tra/{id}` | Xoa Bkt |
| POST | `/api/v1/lms/bai-kiem-tra/{id}/bat-dau` | Bat Dau Thi |
| GET | `/api/v1/lms/bai-kiem-tra/{id}/cau-hoi` | Danh Sach Cau Hoi Bkt |
| GET | `/api/v1/lms/bai-kiem-tra/{id}/ket-qua` | Lich Su Thi Bkt |
| GET | `/api/v1/lms/bai-kiem-tra/{id}/ket-qua-tat-ca` | Ket Qua Tat Ca |
| POST | `/api/v1/lms/bai-kiem-tra/{id}/luu-nhap` | Luu Nhap |
| POST | `/api/v1/lms/bai-kiem-tra/{id}/nop-bai` | Nop Bai |
| POST | `/api/v1/lms/bai-kiem-tra/{id}/nop-video` | Nop Video |
| GET | `/api/v1/lms/bao-cao/ca-nhan` | Bao Cao Ca Nhan |
| GET | `/api/v1/lms/bao-cao/don-vi/{don_vi_id}` | Bao Cao Don Vi |
| GET | `/api/v1/lms/bao-cao/khoa-hoc/{khoa_hoc_id}` | Bao Cao Khoa Hoc |
| GET | `/api/v1/lms/cau-hoi` | Danh Sach Cau Hoi |
| POST | `/api/v1/lms/cau-hoi` | Tao Cau Hoi |
| POST | `/api/v1/lms/cau-hoi/import` | Import Cau Hoi |
| GET | `/api/v1/lms/cau-hoi/import/mau` | Download Mau Import |
| GET | `/api/v1/lms/cau-hoi/{id}` | Chi Tiet Cau Hoi |
| PUT | `/api/v1/lms/cau-hoi/{id}` | Cap Nhat Cau Hoi |
| DELETE | `/api/v1/lms/cau-hoi/{id}` | Xoa Cau Hoi |
| GET | `/api/v1/lms/cau-truc-de-template` | Danh Sach Template |
| POST | `/api/v1/lms/cau-truc-de-template` | Tao Template |
| GET | `/api/v1/lms/cau-truc-de-template/{template_id}` | Chi Tiet Template |
| DELETE | `/api/v1/lms/cau-truc-de-template/{template_id}` | Xoa Template |
| GET | `/api/v1/lms/cbcc/search` | Search Cbcc |
| GET | `/api/v1/lms/chung-chi/cua-toi` | Chung Chi Cua Toi |
| GET | `/api/v1/lms/chung-chi/xac-minh/{ma_chung_chi}` | Xac Minh Chung Chi |
| GET | `/api/v1/lms/chung-chi/{id}/tai` | Tai Chung Chi |
| GET | `/api/v1/lms/chuyen-de` | Danh Sach Chuyen De |
| POST | `/api/v1/lms/chuyen-de` | Tao Chuyen De |
| GET | `/api/v1/lms/chuyen-de/{id}` | Chi Tiet Chuyen De |
| PUT | `/api/v1/lms/chuyen-de/{id}` | Cap Nhat Chuyen De |
| DELETE | `/api/v1/lms/chuyen-de/{id}` | Xoa Chuyen De |
| GET | `/api/v1/lms/dang-ky/cho-phe-duyet` | Danh Sach Cho Phe Duyet |
| GET | `/api/v1/lms/dang-ky/cua-toi` | Khoa Hoc Cua Toi |
| DELETE | `/api/v1/lms/dang-ky/{dang_ky_id}/loai-hoc-vien` | Loai Hoc Vien |
| POST | `/api/v1/lms/dang-ky/{dang_ky_id}/phe-duyet` | Phe Duyet Dang Ky |
| GET | `/api/v1/lms/dashboard/summary` | Dashboard Summary |
| GET | `/api/v1/lms/dgnl/ngan-hang` | Danh Sach |
| POST | `/api/v1/lms/dgnl/ngan-hang` | Tao Cau Hoi |
| POST | `/api/v1/lms/dgnl/ngan-hang/import` | Import Cau Hoi |
| GET | `/api/v1/lms/dgnl/ngan-hang/import/mau` | Download Template |
| GET | `/api/v1/lms/dgnl/ngan-hang/thong-ke` | Thong Ke Ngan Hang |
| POST | `/api/v1/lms/dgnl/ngan-hang/xoa-nhieu` | Xoa Nhieu |
| GET | `/api/v1/lms/dgnl/ngan-hang/{id}` | Chi Tiet |
| PUT | `/api/v1/lms/dgnl/ngan-hang/{id}` | Cap Nhat |
| DELETE | `/api/v1/lms/dgnl/ngan-hang/{id}` | Xoa |
| GET | `/api/v1/lms/don-vi` | Danh Sach Don Vi |
| GET | `/api/v1/lms/don-vi/{don_vi_id}/cong-chuc` | Cong Chuc Theo Don Vi |
| GET | `/api/v1/lms/ket-qua/{id}` | Ket Qua Chi Tiet |
| POST | `/api/v1/lms/ket-qua/{ket_qua_id}/cham-tay` | Cham Tay |
| POST | `/api/v1/lms/khao-sat` | Gui Khao Sat |
| GET | `/api/v1/lms/khoa-hoc` | Danh Sach Khoa Hoc |
| POST | `/api/v1/lms/khoa-hoc` | Tao Khoa Hoc |
| GET | `/api/v1/lms/khoa-hoc/quan-ly` | Danh Sach Quan Ly |
| GET | `/api/v1/lms/khoa-hoc/{id}` | Chi Tiet Khoa Hoc |
| PUT | `/api/v1/lms/khoa-hoc/{id}` | Cap Nhat Khoa Hoc |
| DELETE | `/api/v1/lms/khoa-hoc/{id}` | Xoa Khoa Hoc |
| PATCH | `/api/v1/lms/khoa-hoc/{id}/trang-thai` | Chuyen Trang Thai |
| GET | `/api/v1/lms/khoa-hoc/{khoa_hoc_id}/bai-hoc` | Danh Sach Bai Hoc |
| POST | `/api/v1/lms/khoa-hoc/{khoa_hoc_id}/bai-hoc` | Tao Bai Hoc |
| PATCH | `/api/v1/lms/khoa-hoc/{khoa_hoc_id}/bai-hoc/sap-xep` | Sap Xep Bai Hoc |
| GET | `/api/v1/lms/khoa-hoc/{khoa_hoc_id}/bai-kiem-tra` | Danh Sach Bkt |
| POST | `/api/v1/lms/khoa-hoc/{khoa_hoc_id}/bai-kiem-tra` | Tao Bkt |
| POST | `/api/v1/lms/khoa-hoc/{khoa_hoc_id}/dang-ky` | Dang Ky Tu Nguyen |
| DELETE | `/api/v1/lms/khoa-hoc/{khoa_hoc_id}/dang-ky` | Huy Dang Ky |
| POST | `/api/v1/lms/khoa-hoc/{khoa_hoc_id}/giao-bai` | Giao Bai |
| GET | `/api/v1/lms/khoa-hoc/{khoa_hoc_id}/hoc-vien` | Danh Sach Hoc Vien |
| GET | `/api/v1/lms/khoa-hoc/{khoa_hoc_id}/khao-sat/thong-ke` | Thong Ke Khao Sat |
| GET | `/api/v1/lms/ky-thi` | Danh Sach Ky Thi |
| POST | `/api/v1/lms/ky-thi` | Tao Ky Thi |
| GET | `/api/v1/lms/ky-thi/{ky_thi_id}` | Chi Tiet Ky Thi |
| PUT | `/api/v1/lms/ky-thi/{ky_thi_id}` | Cap Nhat Ky Thi |
| DELETE | `/api/v1/lms/ky-thi/{ky_thi_id}` | Xoa Ky Thi |
| POST | `/api/v1/lms/ky-thi/{ky_thi_id}/bat-dau` | Bat Dau Thi |
| GET | `/api/v1/lms/ky-thi/{ky_thi_id}/cau-truc-de` | Lay Cau Truc De |
| POST | `/api/v1/lms/ky-thi/{ky_thi_id}/cau-truc-de` | Upsert Cau Truc De |
| DELETE | `/api/v1/lms/ky-thi/{ky_thi_id}/cau-truc-de/{vi_tri_id}` | Xoa Cau Truc De Vi Tri |
| GET | `/api/v1/lms/ky-thi/{ky_thi_id}/export` | Export Ket Qua |
| GET | `/api/v1/lms/ky-thi/{ky_thi_id}/giam-sat` | Giam Sat Ky Thi |
| GET | `/api/v1/lms/ky-thi/{ky_thi_id}/ket-qua` | Ket Qua Ca Nhan |
| GET | `/api/v1/lms/ky-thi/{ky_thi_id}/ket-qua/{cong_chuc_id}` | Ket Qua Cbcc |
| POST | `/api/v1/lms/ky-thi/{ky_thi_id}/luu-nhap` | Luu Nhap |
| POST | `/api/v1/lms/ky-thi/{ky_thi_id}/nop-bai` | Nop Bai |
| POST | `/api/v1/lms/ky-thi/{ky_thi_id}/thi-sinh` | Giao Thi Sinh |
| GET | `/api/v1/lms/ky-thi/{ky_thi_id}/thi-sinh` | Danh Sach Thi Sinh |
| POST | `/api/v1/lms/ky-thi/{ky_thi_id}/thi-sinh/import-excel` | Import Thi Sinh Excel |
| GET | `/api/v1/lms/ky-thi/{ky_thi_id}/thi-sinh/import/mau` | Download Mau Import Thi Sinh |
| DELETE | `/api/v1/lms/ky-thi/{ky_thi_id}/thi-sinh/{cong_chuc_id}` | Xoa Thi Sinh |
| GET | `/api/v1/lms/ky-thi/{ky_thi_id}/thi-sinh/{cong_chuc_id}/ket-qua/{lan}` | Ket Qua Lan Thi |
| GET | `/api/v1/lms/ky-thi/{ky_thi_id}/thi-sinh/{cong_chuc_id}/vi-pham` | Danh Sach Vi Pham |
| GET | `/api/v1/lms/ky-thi/{ky_thi_id}/thong-ke` | Thong Ke Ky Thi |
| PATCH | `/api/v1/lms/ky-thi/{ky_thi_id}/trang-thai` | Chuyen Trang Thai Ky Thi |
| POST | `/api/v1/lms/ky-thi/{ky_thi_id}/validate` | Validate Ngan Hang |
| POST | `/api/v1/lms/ky-thi/{ky_thi_id}/vi-pham` | Ghi Vi Pham |
| PATCH | `/api/v1/lms/ky-thi/{ky_thi_id}/vi-pham/{vp_id}/ly-do` | Cap Nhat Ly Do Vi Pham |
| POST | `/api/v1/lms/ky-thi/{ky_thi_id}/xac-nhan` | Xac Nhan Ca Thi |
| GET | `/api/v1/lms/linh-vuc` | Danh Sach Linh Vuc |
| POST | `/api/v1/lms/linh-vuc` | Tao Linh Vuc |
| PUT | `/api/v1/lms/linh-vuc/{linh_vuc_id}` | Cap Nhat Linh Vuc |
| DELETE | `/api/v1/lms/linh-vuc/{linh_vuc_id}` | Xoa Linh Vuc |
| POST | `/api/v1/lms/upload/file` | Upload File |
| POST | `/api/v1/lms/upload/files` | Upload Multiple Files |
| GET | `/api/v1/lms/vi-tri-viec-lam` | Danh Sach Vi Tri |
| POST | `/api/v1/lms/vi-tri-viec-lam` | Tao Vi Tri |
| PUT | `/api/v1/lms/vi-tri-viec-lam/{vi_tri_id}` | Cap Nhat Vi Tri |
| DELETE | `/api/v1/lms/vi-tri-viec-lam/{vi_tri_id}` | Xoa Vi Tri |
| GET | `/health` | Health Check |

## Forum - Diễn đàn — port 8002 (27 endpoints)
- Phiên bản: `0.1.0` — Tiêu đề: HQKV8 Dien dan
- Base URL public: `https://kpihaiquan.vn/api/forum/v1`

| Method | Path | Chức năng |
|---|---|---|
| GET | `/api/forum/v1/bao-cao/ca-nhan` | Bao Cao Ca Nhan |
| GET | `/api/forum/v1/bao-cao/don-vi/{don_vi_id}` | Bao Cao Don Vi |
| GET | `/api/forum/v1/bao-cao/top` | Bao Cao Top Contributors |
| POST | `/api/forum/v1/bieu-quyet` | Vote |
| DELETE | `/api/forum/v1/bieu-quyet` | Xoa Vote |
| GET | `/api/forum/v1/chu-de` | Danh Sach Chu De |
| POST | `/api/forum/v1/chu-de` | Tao Chu De |
| GET | `/api/forum/v1/chu-de/{chu_de_id}` | Chi Tiet Chu De |
| PUT | `/api/forum/v1/chu-de/{chu_de_id}` | Sua Chu De |
| DELETE | `/api/forum/v1/chu-de/{chu_de_id}` | Xoa Chu De |
| PATCH | `/api/forum/v1/chu-de/{chu_de_id}/dap-an-chuan` | Chon Dap An Chuan |
| PATCH | `/api/forum/v1/chu-de/{chu_de_id}/hanh-dong` | Hanh Dong Chu De |
| POST | `/api/forum/v1/chu-de/{chu_de_id}/theo-doi` | Theo Doi Chu De |
| DELETE | `/api/forum/v1/chu-de/{chu_de_id}/theo-doi` | Bo Theo Doi Chu De |
| POST | `/api/forum/v1/chu-de/{chu_de_id}/tra-loi` | Tao Tra Loi |
| GET | `/api/forum/v1/chuyen-muc` | Danh Sach Chuyen Muc |
| POST | `/api/forum/v1/chuyen-muc` | Tao Chuyen Muc |
| PUT | `/api/forum/v1/chuyen-muc/{chuyen_muc_id}` | Sua Chuyen Muc |
| DELETE | `/api/forum/v1/chuyen-muc/{chuyen_muc_id}` | Xoa Chuyen Muc |
| GET | `/api/forum/v1/dashboard/summary` | Dashboard Summary |
| GET | `/api/forum/v1/tags/goi-y` | Tag Suggestions |
| GET | `/api/forum/v1/theo-doi/cua-toi` | Danh Sach Theo Doi Cua Toi |
| GET | `/api/forum/v1/tim-kiem` | Tim Kiem Chu De |
| PUT | `/api/forum/v1/tra-loi/{tra_loi_id}` | Sua Tra Loi |
| DELETE | `/api/forum/v1/tra-loi/{tra_loi_id}` | Xoa Tra Loi |
| PATCH | `/api/forum/v1/tra-loi/{tra_loi_id}/an` | An Tra Loi |
| GET | `/health` | Health Check |

## Legal - Pháp luật — port 8003 (29 endpoints)
- Phiên bản: `1.0.0` — Tiêu đề: HQKV8 Phap luat
- Base URL public: `https://kpihaiquan.vn/api/legal/v1`

| Method | Path | Chức năng |
|---|---|---|
| GET | `/api/legal/v1/bao-cao/ca-nhan` | Bao Cao Ca Nhan |
| GET | `/api/legal/v1/bao-cao/don-vi/{don_vi_id}` | Bao Cao Don Vi |
| GET | `/api/legal/v1/cong-chuc` | Danh Sach Cong Chuc |
| GET | `/api/legal/v1/dashboard/summary` | Dashboard Summary |
| GET | `/api/legal/v1/don-vi` | Danh Sach Don Vi |
| GET | `/api/legal/v1/loai-van-ban` | Lay Danh Sach Loai Van Ban |
| POST | `/api/legal/v1/loai-van-ban` | Tao Loai Van Ban |
| PUT | `/api/legal/v1/loai-van-ban/{loai_vb_id}` | Cap Nhat Loai Van Ban |
| DELETE | `/api/legal/v1/loai-van-ban/{loai_vb_id}` | Xoa Loai Van Ban |
| GET | `/api/legal/v1/quiz/{quiz_id}/ket-qua` | Xem Ket Qua Quiz |
| POST | `/api/legal/v1/quiz/{quiz_id}/lam-bai` | Lam Bai Quiz |
| GET | `/api/legal/v1/van-ban` | Lay Danh Sach Van Ban |
| POST | `/api/legal/v1/van-ban` | Tao Van Ban |
| GET | `/api/legal/v1/van-ban/chua-doc` | Lay Van Ban Chua Doc |
| GET | `/api/legal/v1/van-ban/quan-ly` | Lay Danh Sach Quan Ly |
| GET | `/api/legal/v1/van-ban/{van_ban_id}` | Lay Chi Tiet Van Ban |
| PUT | `/api/legal/v1/van-ban/{van_ban_id}` | Sua Van Ban |
| DELETE | `/api/legal/v1/van-ban/{van_ban_id}` | Xoa Van Ban |
| GET | `/api/legal/v1/van-ban/{van_ban_id}/bao-cao-doc` | Bao Cao Doc Van Ban |
| GET | `/api/legal/v1/van-ban/{van_ban_id}/download` | Tai Van Ban |
| GET | `/api/legal/v1/van-ban/{van_ban_id}/quiz` | Lay Danh Sach Quiz |
| POST | `/api/legal/v1/van-ban/{van_ban_id}/quiz` | Tao Quiz |
| PATCH | `/api/legal/v1/van-ban/{van_ban_id}/tracking` | Tracking Thoi Gian Doc |
| PATCH | `/api/legal/v1/van-ban/{van_ban_id}/trang-thai` | Cap Nhat Trang Thai Van Ban |
| POST | `/api/legal/v1/van-ban/{van_ban_id}/upload-file` | Upload File Van Ban |
| POST | `/api/legal/v1/van-ban/{van_ban_id}/xac-nhan` | Xac Nhan Da Doc |
| GET | `/health` | Health Check |
| GET | `/internal/v1/legal/van-ban/search` | Tim Kiem Van Ban |
| GET | `/internal/v1/legal/van-ban/{van_ban_id}/summary` | Lay Tom Tat Van Ban |

## Portal/CMS — port 8004 (38 endpoints)
- Phiên bản: `0.1.0` — Tiêu đề: HQKV8 Portal
- Base URL public: `https://kpihaiquan.vn/api/portal/v1`

| Method | Path | Chức năng |
|---|---|---|
| GET | `/api/v1/bai-viet` | Danh sách bài viết công khai |
| POST | `/api/v1/bai-viet` | Tạo bài viết |
| GET | `/api/v1/bai-viet/quan-ly` | Danh sách bài viết quản lý |
| GET | `/api/v1/bai-viet/{bai_viet_id}` | Chi tiết bài viết |
| PUT | `/api/v1/bai-viet/{bai_viet_id}` | Sửa bài viết |
| DELETE | `/api/v1/bai-viet/{bai_viet_id}` | Xóa bài viết |
| PATCH | `/api/v1/bai-viet/{bai_viet_id}/ghim` | Ghim/bỏ ghim bài viết |
| PATCH | `/api/v1/bai-viet/{bai_viet_id}/trang-thai` | Đổi trạng thái workflow |
| GET | `/api/v1/chuyen-muc` | Danh sách chuyên mục |
| POST | `/api/v1/chuyen-muc` | Tạo chuyên mục |
| PUT | `/api/v1/chuyen-muc/{chuyen_muc_id}` | Sửa chuyên mục |
| DELETE | `/api/v1/chuyen-muc/{chuyen_muc_id}` | Xóa chuyên mục |
| GET | `/api/v1/dashboard/lanh-dao` | Dashboard thống kê Lãnh đạo |
| GET | `/api/v1/dashboard/summary` | Dashboard trang chủ Portal |
| GET | `/api/v1/tai-lieu` | Danh sách tài liệu |
| POST | `/api/v1/tai-lieu` | Upload tài liệu mới |
| GET | `/api/v1/tai-lieu/{tai_lieu_id}` | Chi tiết tài liệu |
| PUT | `/api/v1/tai-lieu/{tai_lieu_id}` | Sửa metadata tài liệu |
| DELETE | `/api/v1/tai-lieu/{tai_lieu_id}` | Xóa tài liệu |
| GET | `/api/v1/tai-lieu/{tai_lieu_id}/download` | Download tài liệu |
| GET | `/api/v1/tai-lieu/{tai_lieu_id}/lich-su` | Lịch sử phiên bản |
| POST | `/api/v1/tai-lieu/{tai_lieu_id}/phien-ban-moi` | Upload phiên bản mới |
| GET | `/api/v1/thu-muc` | Danh sách thư mục |
| POST | `/api/v1/thu-muc` | Tạo thư mục |
| GET | `/api/v1/thu-muc/tree` | Cây thư mục đầy đủ |
| PUT | `/api/v1/thu-muc/{thu_muc_id}` | Sửa thư mục |
| DELETE | `/api/v1/thu-muc/{thu_muc_id}` | Xóa thư mục |
| POST | `/api/v1/upload/file` | Upload 1 file tai lieu |
| GET | `/api/v1/vinh-danh` | Danh sach vinh danh |
| POST | `/api/v1/vinh-danh` | Tao moi vinh danh (DRAFT) |
| GET | `/api/v1/vinh-danh/current` | Vinh danh PUBLISHED cua thang hien tai |
| POST | `/api/v1/vinh-danh/upload-anh` | Upload anh chan dung |
| GET | `/api/v1/vinh-danh/{vd_id}` | Chi tiet ban ghi vinh danh |
| PUT | `/api/v1/vinh-danh/{vd_id}` | Cap nhat vinh danh |
| DELETE | `/api/v1/vinh-danh/{vd_id}` | Xoa ban ghi vinh danh (chi DRAFT) |
| POST | `/api/v1/vinh-danh/{vd_id}/cong-bo` | Cong bo (DRAFT -> PUBLISHED) |
| POST | `/api/v1/vinh-danh/{vd_id}/go-cong-bo` | Go cong bo (PUBLISHED -> DRAFT) |
| GET | `/health` | Health Check |

## Common Service — port 8005 (23 endpoints)
- Phiên bản: `0.1.0` — Tiêu đề: HQKV8 Common Service
- Base URL public: `https://kpihaiquan.vn/api/common`

| Method | Path | Chức năng |
|---|---|---|
| POST | `/api/common/v1/file/upload` | Upload File |
| GET | `/api/common/v1/file/{file_id}` | Get File Info |
| DELETE | `/api/common/v1/file/{file_id}` | Delete File |
| GET | `/api/common/v1/knowledge-base` | Danh Sach |
| POST | `/api/common/v1/knowledge-base` | Tao |
| GET | `/api/common/v1/knowledge-base/{kb_id}` | Chi Tiet |
| PUT | `/api/common/v1/knowledge-base/{kb_id}` | Sua |
| DELETE | `/api/common/v1/knowledge-base/{kb_id}` | Xoa |
| PATCH | `/api/common/v1/knowledge-base/{kb_id}/trang-thai` | Doi Trang Thai |
| GET | `/api/common/v1/kpi-log/don-vi/{don_vi_id}` | Doc Theo Don Vi |
| GET | `/api/common/v1/kpi-log/{cong_chuc_id}` | Doc Kpi Log |
| GET | `/api/common/v1/search` | Tim Kiem |
| GET | `/api/common/v1/search/suggest` | Goi Y |
| GET | `/api/common/v1/thong-bao` | Danh Sach Thong Bao |
| GET | `/api/common/v1/thong-bao/count` | Dem Chua Doc |
| PATCH | `/api/common/v1/thong-bao/doc-tat-ca` | Danh Dau Tat Ca Da Doc |
| PATCH | `/api/common/v1/thong-bao/{thong_bao_id}/doc` | Danh Dau Da Doc |
| GET | `/health` | Health Check |
| POST | `/internal/v1/knowledge-base/cap-nhat-van-ban` | Cap Nhat Van Ban |
| POST | `/internal/v1/kpi-log` | Ghi Log |
| POST | `/internal/v1/kpi-log/bulk` | Ghi Log Hang Loat |
| POST | `/internal/v1/thong-bao` | Tao Thong Bao |
| POST | `/internal/v1/thong-bao/bulk` | Tao Thong Bao Hang Loat |

## HKG - Họp Không Giấy — port 8006 (55 endpoints)
- Phiên bản: `0.1.0-G3b` — Tiêu đề: HQKV8 HKG (Họp Không Giấy)
- Base URL public: `https://kpihaiquan.vn/api/v1/hop-khong-giay`

| Method | Path | Chức năng |
|---|---|---|
| GET | `/api/v1/hop-khong-giay/bien-ban/{bien_ban_id}/file` | Tải file biên bản đã xuất |
| POST | `/api/v1/hop-khong-giay/bien-ban/{bien_ban_id}/ky` | Chủ tọa ký biên bản (Mock CKS) |
| POST | `/api/v1/hop-khong-giay/bien-ban/{bien_ban_id}/trinh-ky` | Thư ký trình biên bản chờ ký |
| POST | `/api/v1/hop-khong-giay/bien-ban/{bien_ban_id}/xuat` | Xuất biên bản DOCX/PDF |
| GET | `/api/v1/hop-khong-giay/cong-chuc/search` | Tìm/list CBCC theo q hoặc don_vi_id |
| GET | `/api/v1/hop-khong-giay/cong-chuc/{cong_chuc_id}` | Lấy thông tin 1 CBCC theo id |
| POST | `/api/v1/hop-khong-giay/cuoc-hop/` | Tạo cuộc họp mới |
| GET | `/api/v1/hop-khong-giay/cuoc-hop/` | Danh sách cuộc họp (filter + phân trang) |
| GET | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}` | Chi tiết cuộc họp |
| PATCH | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}` | Cập nhật cuộc họp |
| POST | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/bat-dau` | Bắt đầu cuộc họp |
| GET | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/bien-ban` | Đọc biên bản (auto-fill nếu chưa có) |
| PUT | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/bien-ban` | Lưu nội dung biên bản (Thư ký) |
| GET | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/diem-danh` | Tổng hợp điểm danh cuộc họp |
| GET | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/diem-danh-cua-toi` | Trạng thái điểm danh của user hiện tại |
| POST | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/gui-giay-moi` | Gửi giấy mời |
| POST | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/huy` | Hủy cuộc họp |
| POST | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/ket-luan` | Giao nhiệm vụ (kết luận họp) |
| GET | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/ket-luan` | Danh sách kết luận của cuộc họp |
| POST | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/ket-thuc` | Kết thúc cuộc họp |
| GET | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/presentation/state` | State hiện tại của phiên trình chiếu + WS token |
| GET | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/tai-lieu` | Danh sách tài liệu của cuộc họp |
| GET | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/thanh-phan` | Lấy danh sách thành phần cuộc họp |
| PUT | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/thanh-phan` | Sửa thành phần (replace list, diff add/remove) |
| POST | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/thanh-phan/them-tu-nhom` | Gộp thành viên từ 1+ nhóm vào cuộc họp |
| POST | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/tu-diem-danh` | CBCC tự điểm danh (không cần QR) |
| POST | `/api/v1/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/xac-nhan` | CBCC xác nhận tham dự |
| POST | `/api/v1/hop-khong-giay/diem-danh/bam-tay` | Thư ký bấm tay điểm danh nhiều CBCC |
| POST | `/api/v1/hop-khong-giay/diem-danh/qr-token/{cuoc_hop_id}` | Sinh QR token cho cuộc họp (chu_toa/thu_ky) |
| POST | `/api/v1/hop-khong-giay/diem-danh/quet` | CBCC quét QR submit token |
| GET | `/api/v1/hop-khong-giay/ket-luan/cua-don-vi/{don_vi_id}` | Nhiệm vụ của đơn vị (LĐ ĐV/CHANH_VP) |
| GET | `/api/v1/hop-khong-giay/ket-luan/cua-toi` | Nhiệm vụ tôi phụ trách |
| PATCH | `/api/v1/hop-khong-giay/ket-luan/{kl_id}` | Cập nhật metadata kết luận |
| POST | `/api/v1/hop-khong-giay/ket-luan/{kl_id}/tien-do` | Cập nhật tiến độ |
| GET | `/api/v1/hop-khong-giay/nhom-thanh-phan/` | Danh sách nhóm thành phần |
| POST | `/api/v1/hop-khong-giay/nhom-thanh-phan/` | Tạo nhóm thành phần |
| GET | `/api/v1/hop-khong-giay/nhom-thanh-phan/{nhom_id}` | Chi tiết nhóm + danh sách thành viên |
| PATCH | `/api/v1/hop-khong-giay/nhom-thanh-phan/{nhom_id}` | Cập nhật metadata nhóm |
| DELETE | `/api/v1/hop-khong-giay/nhom-thanh-phan/{nhom_id}` | Xoá nhóm (hard delete) |
| POST | `/api/v1/hop-khong-giay/nhom-thanh-phan/{nhom_id}/thanh-vien` | Thêm 1 thành viên vào nhóm |
| POST | `/api/v1/hop-khong-giay/nhom-thanh-phan/{nhom_id}/thanh-vien/batch` | Thêm nhiều thành viên 1 lần (skip trùng, không 409) |
| PUT | `/api/v1/hop-khong-giay/nhom-thanh-phan/{nhom_id}/thanh-vien/{cong_chuc_id}` | Sửa vai_tro / loai_tham_du của thành viên |
| DELETE | `/api/v1/hop-khong-giay/nhom-thanh-phan/{nhom_id}/thanh-vien/{cong_chuc_id}` | Gỡ 1 thành viên khỏi nhóm |
| POST | `/api/v1/hop-khong-giay/tai-lieu/upload` | Upload tài liệu họp |
| DELETE | `/api/v1/hop-khong-giay/tai-lieu/{tai_lieu_id}` | Xóa tài liệu (soft delete) |
| GET | `/api/v1/hop-khong-giay/tai-lieu/{tai_lieu_id}/tai` | Sinh URL tải tài liệu |
| GET | `/api/v1/hop-khong-giay/tai-lieu/{tai_lieu_id}/tai-noi-dung` | Serve file để tải xuống — yêu cầu short-lived token |
| GET | `/api/v1/hop-khong-giay/tai-lieu/{tai_lieu_id}/xem` | Sinh URL xem tài liệu (1h) |
| GET | `/api/v1/hop-khong-giay/tai-lieu/{tai_lieu_id}/xem-noi-dung` | Serve file nội dung — yêu cầu short-lived token |
| GET | `/api/v1/hop-khong-giay/thong-ke/ca-nhan` | Dashboard cá nhân |
| GET | `/api/v1/hop-khong-giay/thong-ke/don-vi/{don_vi_id}` | Dashboard đơn vị (LĐ ĐV/CHANH_VP/TRUONG_CNTT/CCT/PCCT) |
| POST | `/api/v1/hop-khong-giay/xin-phep-vang/` | CBCC gửi đơn xin vắng |
| GET | `/api/v1/hop-khong-giay/xin-phep-vang/cho-duyet` | Chủ tọa xem các đơn chờ duyệt |
| POST | `/api/v1/hop-khong-giay/xin-phep-vang/{xpv_id}/duyet` | Chủ tọa duyệt / từ chối đơn |
| GET | `/health` | Health Check |

## Chỉ tiêu Đơn vị — port 8007 (33 endpoints)
- Phiên bản: `0.1.0` — Tiêu đề: HQKV8 Chi tieu Don vi
- Base URL public: `https://kpihaiquan.vn/api/v1/chi-tieu`

| Method | Path | Chức năng |
|---|---|---|
| GET | `/api/v1/chi-tieu/bao-cao/luy-ke` | Luy Ke |
| GET | `/api/v1/chi-tieu/bao-cao/pham-vi-cua-toi` | Pham Vi Cua Toi |
| GET | `/api/v1/chi-tieu/bao-cao/ra-soat` | Ra Soat |
| GET | `/api/v1/chi-tieu/dang-ky` | Danh Sach Can Dang Ky |
| POST | `/api/v1/chi-tieu/dang-ky` | Tao |
| PUT | `/api/v1/chi-tieu/dang-ky/{dk_id}` | Cap Nhat |
| POST | `/api/v1/chi-tieu/dang-ky/{dk_id}/gui-duyet` | Gui Duyet |
| POST | `/api/v1/chi-tieu/dang-ky/{dk_id}/gui-ket-qua` | Gui Ket Qua |
| GET | `/api/v1/chi-tieu/dang-ky/{dk_id}/lich-su` | Lich Su |
| POST | `/api/v1/chi-tieu/dang-ky/{dk_id}/mo-khoa` | Mo Khoa |
| POST | `/api/v1/chi-tieu/dang-ky/{dk_id}/nhap-ket-qua` | Nhap Ket Qua |
| POST | `/api/v1/chi-tieu/dang-ky/{dk_id}/yeu-cau-sua` | Yeu Cau Sua |
| GET | `/api/v1/chi-tieu/danh-muc` | Danh Sach |
| POST | `/api/v1/chi-tieu/danh-muc` | Tao |
| PUT | `/api/v1/chi-tieu/danh-muc/{ct_id}` | Cap Nhat |
| DELETE | `/api/v1/chi-tieu/danh-muc/{ct_id}` | Xoa |
| GET | `/api/v1/chi-tieu/duyet/cho-xu-ly` | Cho Xu Ly |
| POST | `/api/v1/chi-tieu/duyet/{dk_id}/duyet` | Duyet |
| POST | `/api/v1/chi-tieu/duyet/{dk_id}/tu-choi` | Tu Choi |
| GET | `/api/v1/chi-tieu/giao-nam` | Danh Sach |
| POST | `/api/v1/chi-tieu/giao-nam` | Tao |
| PUT | `/api/v1/chi-tieu/giao-nam/{gn_id}` | Cap Nhat |
| DELETE | `/api/v1/chi-tieu/giao-nam/{gn_id}` | Xoa |
| GET | `/api/v1/chi-tieu/linh-vuc` | Danh Sach |
| POST | `/api/v1/chi-tieu/linh-vuc` | Tao |
| PUT | `/api/v1/chi-tieu/linh-vuc/{linh_vuc_id}` | Cap Nhat |
| DELETE | `/api/v1/chi-tieu/linh-vuc/{linh_vuc_id}` | Xoa |
| GET | `/api/v1/chi-tieu/nguoi-theo-doi` | Danh Sach |
| POST | `/api/v1/chi-tieu/nguoi-theo-doi` | Gan |
| GET | `/api/v1/chi-tieu/nguoi-theo-doi/cong-chuc` | Tim Cong Chuc |
| PUT | `/api/v1/chi-tieu/nguoi-theo-doi/{cong_chuc_id}` | Cap Nhat |
| DELETE | `/api/v1/chi-tieu/nguoi-theo-doi/{cong_chuc_id}` | Go |
| GET | `/health` | Health Check |
