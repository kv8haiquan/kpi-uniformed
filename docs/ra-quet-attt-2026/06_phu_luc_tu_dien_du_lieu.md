# Mục 6 (Phụ lục) — Từ điển dữ liệu database `kpi_haiquan`

> Sinh tự động từ `information_schema` ngày 30/07/2026. DB: PostgreSQL 15, kích thước ~170 MB, 96 bảng / 8 schema.

## Schema `public` — KPI (production) + bảng platform dùng chung (37 bảng)

### `public.alembic_version` (1 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| version_num | character varying(32) |  | PK |

### `public.audit_log` (5 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| table_name | character varying(100) |  |  |
| record_id | uuid |  |  |
| action | USER-DEFINED |  |  |
| old_value | jsonb | ✓ |  |
| new_value | jsonb | ✓ |  |
| user_id | uuid | ✓ |  |
| ip_address | character varying(50) | ✓ |  |
| user_agent | text | ✓ |  |
| created_at | timestamp with time zone |  |  |

### `public.bao_cao_xep_loai` (94 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| don_vi_id | uuid |  | FK→public.don_vi(id) |
| thang | integer |  |  |
| nam | integer |  |  |
| nguoi_lap_id | uuid |  | FK→public.cong_chuc(id) |
| ngay_lap | timestamp with time zone | ✓ |  |
| trang_thai | character varying(20) |  |  |
| nguoi_phe_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| ngay_phe_duyet | timestamp with time zone | ✓ |  |
| y_kien_phe_duyet | text | ✓ |  |
| tong_cong_chuc | integer | ✓ |  |
| so_loai_a | integer | ✓ |  |
| so_loai_b | integer | ✓ |  |
| so_loai_c | integer | ✓ |  |
| so_loai_d | integer | ✓ |  |
| so_loai_e | integer | ✓ |  |
| canh_bao_ty_le_a | boolean | ✓ |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| is_deleted | boolean |  |  |
| ngay_gui_duyet | timestamp with time zone | ✓ |  |

### `public.bao_cao_xep_loai_quy` (37 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| don_vi_id | uuid |  | FK→public.don_vi(id) |
| quy | integer |  |  |
| nam | integer |  |  |
| nguoi_lap_id | uuid |  | FK→public.cong_chuc(id) |
| ngay_lap | timestamp with time zone | ✓ |  |
| ngay_gui_duyet | timestamp with time zone | ✓ |  |
| trang_thai | character varying(20) |  |  |
| nguoi_phe_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| ngay_phe_duyet | timestamp with time zone | ✓ |  |
| y_kien_phe_duyet | text | ✓ |  |
| tong_cong_chuc | integer |  |  |
| so_loai_a | integer |  |  |
| so_loai_b | integer |  |  |
| so_loai_c | integer |  |  |
| so_loai_d | integer |  |  |
| so_loai_e | integer |  |  |
| canh_bao_ty_le_a | boolean |  |  |
| id | uuid |  | PK |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| is_deleted | boolean |  |  |
| last_recalculated_at | timestamp with time zone | ✓ |  |

### `public.cap_do_phuc_tap` (6 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ma_cap_do | character varying(10) |  |  |
| ten_cap_do | character varying(100) |  |  |
| mo_ta | text | ✓ |  |
| he_so_sp1 | numeric |  |  |
| he_so_sp2 | numeric |  |  |
| is_theo_thuc_te | boolean |  |  |
| thu_tu | integer |  |  |
| is_active | boolean |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `public.chi_tiet_xep_loai` (4058 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| bao_cao_id | uuid |  | FK→public.bao_cao_xep_loai(id) |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| is_lanh_dao | boolean |  |  |
| diem_tieu_chi_chung | numeric | ✓ |  |
| diem_kpi | numeric | ✓ |  |
| diem_tong | numeric | ✓ |  |
| xep_loai_he_thong | character varying(1) |  |  |
| xep_loai_de_xuat | character varying(1) | ✓ |  |
| ly_do_dieu_chinh_dt | text | ✓ |  |
| xep_loai_quyet_dinh | character varying(1) | ✓ |  |
| ly_do_dieu_chinh_cct | text | ✓ |  |
| bi_tu_choi | boolean | ✓ |  |
| ly_do_tu_choi | text | ✓ |  |
| ghi_chu | text | ✓ |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| so_ngay_lam_viec | numeric | ✓ |  |
| so_ngay_nghi | numeric | ✓ |  |

### `public.chi_tiet_xep_loai_quy` (1416 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| bao_cao_quy_id | uuid |  | FK→public.bao_cao_xep_loai_quy(id) |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| is_lanh_dao | boolean |  |  |
| diem_tieu_chi_chung | numeric |  |  |
| diem_kpi | numeric |  |  |
| diem_tong | numeric |  |  |
| xep_loai_he_thong | character varying(1) |  |  |
| xep_loai_de_xuat | character varying(1) | ✓ |  |
| ly_do_dieu_chinh_dt | text | ✓ |  |
| xep_loai_quyet_dinh | character varying(1) | ✓ |  |
| ly_do_dieu_chinh_cct | text | ✓ |  |
| bi_tu_choi | boolean |  |  |
| ly_do_tu_choi | text | ✓ |  |
| ghi_chu | text | ✓ |  |
| id | uuid |  | PK |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `public.cong_chuc` (558 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ma_cc | character varying(20) |  |  |
| ho_ten | character varying(100) |  |  |
| ngay_sinh | date | ✓ |  |
| gioi_tinh | USER-DEFINED | ✓ |  |
| so_dien_thoai | character varying(20) | ✓ |  |
| email | character varying(100) | ✓ |  |
| don_vi_id | uuid |  | FK→public.don_vi(id) |
| vai_tro_id | uuid |  | FK→public.vai_tro(id) |
| chuc_vu | character varying(100) | ✓ |  |
| ngay_vao_nganh | date | ✓ |  |
| ngay_vao_chi_cuc | date | ✓ |  |
| is_lanh_dao | boolean |  |  |
| is_active | boolean |  |  |
| is_deleted | boolean |  |  |
| username | character varying(50) | ✓ |  |
| password_hash | character varying(255) | ✓ |  |
| last_login | timestamp without time zone | ✓ |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| can_view_all_units | boolean | ✓ |  |
| kpi_version_pinned | character varying(10) | ✓ |  |

### `public.cong_chuc_platform_role` (4 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| platform_role_id | uuid |  | FK→public.platform_role(id) |
| pham_vi | jsonb | ✓ |  |
| assigned_by | uuid | ✓ | FK→public.cong_chuc(id) |
| assigned_at | timestamp without time zone |  |  |
| is_active | boolean |  |  |

### `public.cong_viec_yeu_thich` (940 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| danh_muc_sp_id | uuid |  | FK→public.danh_muc_sp_cong_viec(id) |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `public.dang_ky_nghi` (16448 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| loai_nghi | USER-DEFINED |  |  |
| tu_ngay | date |  |  |
| den_ngay | date |  |  |
| so_ngay | numeric |  |  |
| ly_do | text | ✓ |  |
| tai_lieu_dinh_kem | character varying(500) | ✓ |  |
| nguoi_phe_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| trang_thai | USER-DEFINED |  |  |
| ly_do_tu_choi | text | ✓ |  |
| ngay_phe_duyet | timestamp with time zone | ✓ |  |
| ghi_chu_phe_duyet | text | ✓ |  |
| thang_ap_dung | integer | ✓ |  |
| nam_ap_dung | integer | ✓ |  |
| da_tinh_kpi | boolean |  |  |
| id | uuid |  | PK |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| is_deleted | boolean |  |  |
| is_khoa | boolean |  |  |
| nguoi_phe_duyet_cap2_id | uuid | ✓ | FK→public.cong_chuc(id) |
| trang_thai_cap1 | USER-DEFINED | ✓ |  |
| ngay_phe_duyet_cap1 | timestamp with time zone | ✓ |  |
| ly_do_tu_choi_cap1 | text | ✓ |  |

### `public.danh_gia_dde` (140 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| thang | integer |  |  |
| nam | integer |  |  |
| d_ket_qua_don_vi | integer |  |  |
| d_ghi_chu | text | ✓ |  |
| dd_to_chuc_trien_khai | integer |  |  |
| dd_ghi_chu | text | ✓ |  |
| e_doan_ket_noi_bo | integer |  |  |
| e_ghi_chu | text | ✓ |  |
| trang_thai | character varying(20) |  |  |
| nguoi_phe_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| y_kien_phe_duyet | text | ✓ |  |
| ngay_phe_duyet | timestamp with time zone | ✓ |  |
| d_phe_duyet | integer | ✓ |  |
| dd_phe_duyet | integer | ✓ |  |
| e_phe_duyet | integer | ✓ |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `public.danh_gia_quy` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| don_vi_id_snapshot | uuid | ✓ | FK→public.don_vi(id) |
| quy | integer |  |  |
| nam | integer |  |  |
| diem_kpi_quy | numeric | ✓ |  |
| diem_tc_quy | numeric | ✓ |  |
| diem_tong_quy | numeric | ✓ |  |
| xep_loai_quy | character varying(1) | ✓ |  |
| ghi_chu | text | ✓ |  |
| co_chuyen_don_vi | boolean |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `public.danh_gia_thang` (2614 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| thang | integer |  |  |
| nam | integer |  |  |
| so_sp_goc_duoc_giao | numeric | ✓ |  |
| so_ngay_lam_viec | integer | ✓ |  |
| so_ngay_nghi_phep | integer |  |  |
| diem_tieu_chi_chung | numeric | ✓ |  |
| diem_kpi | numeric | ✓ |  |
| diem_so_luong | numeric | ✓ |  |
| diem_chat_luong | numeric | ✓ |  |
| diem_tien_do | numeric | ✓ |  |
| diem_tong | numeric | ✓ |  |
| muc_xep_loai_tu_dong | USER-DEFINED | ✓ |  |
| muc_xep_loai_de_xuat | USER-DEFINED | ✓ |  |
| muc_xep_loai_chinh_thuc | USER-DEFINED | ✓ |  |
| ly_do_dieu_chinh | text | ✓ |  |
| nguoi_de_xuat_id | uuid | ✓ | FK→public.cong_chuc(id) |
| nguoi_phe_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| trang_thai | USER-DEFINED |  |  |
| ngay_tong_hop | timestamp with time zone | ✓ |  |
| ngay_de_xuat | timestamp with time zone | ✓ |  |
| ngay_phe_duyet | timestamp with time zone | ✓ |  |
| uu_diem | text | ✓ |  |
| han_che | text | ✓ |  |
| ghi_chu | text | ✓ |  |
| is_deleted | boolean |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| is_khoa | boolean |  |  |
| nguoi_phe_duyet_tc_cap1_id | uuid | ✓ | FK→public.cong_chuc(id) |
| nguoi_phe_duyet_tc_cap2_id | uuid | ✓ | FK→public.cong_chuc(id) |
| trang_thai_tc | USER-DEFINED | ✓ |  |
| ngay_phe_duyet_tc_cap1 | timestamp with time zone | ✓ |  |
| ngay_phe_duyet_tc_cap2 | timestamp with time zone | ✓ |  |
| diem_tc_cap1 | numeric | ✓ |  |
| diem_tc_cap2 | numeric | ✓ |  |
| ly_do_tu_choi_tc | text | ✓ |  |
| nguoi_tu_choi_tc_id | uuid | ✓ | FK→public.cong_chuc(id) |
| ngay_tu_choi_tc | timestamp with time zone | ✓ |  |
| don_vi_id_snapshot | uuid | ✓ | FK→public.don_vi(id) |
| tong_sp_ke_khai | numeric | ✓ |  |
| version_tinh_diem | character varying(10) |  |  |

### `public.danh_muc_sp_cong_viec` (2867 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ma_danh_muc | character varying(30) |  |  |
| ten_cong_viec | character varying(500) |  |  |
| mo_ta | text | ✓ |  |
| sp_chuan_id | uuid | ✓ | FK→public.sp_cong_viec_chuan(id) |
| don_vi_ap_dung_id | uuid | ✓ | FK→public.don_vi(id) |
| nhom_cong_viec | character varying(100) | ✓ |  |
| is_active | boolean |  |  |
| is_deleted | boolean |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| linh_vuc | character varying(10) | ✓ |  |
| ten_linh_vuc | character varying(200) | ✓ |  |
| nhiem_vu | character varying(500) | ✓ |  |
| cong_viec_chi_tiet | text | ✓ |  |
| san_pham_dau_ra | text | ✓ |  |
| nhom_pl3 | smallint | ✓ |  |
| khung_diem_toi_da | smallint | ✓ |  |
| diem_cham | smallint | ✓ |  |
| he_so_quy_doi | numeric | ✓ |  |
| nguon_du_lieu | character varying(20) |  |  |
| cong_tac | character varying(500) | ✓ |  |
| cong_tac_thu_tu | smallint | ✓ |  |

### `public.dieu_chinh_kqcv` (157 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ke_khai_id | uuid |  | FK→public.ke_khai_cong_viec(id) |
| nguoi_dieu_chinh_id | uuid |  | FK→public.cong_chuc(id) |
| nguoi_phe_duyet_id | uuid |  | FK→public.cong_chuc(id) |
| gia_tri_cu | jsonb |  |  |
| gia_tri_moi | jsonb |  |  |
| ly_do | text |  |  |
| trang_thai | character varying(20) |  |  |
| y_kien_phe_duyet | text | ✓ |  |
| ngay_phe_duyet | timestamp with time zone | ✓ |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| is_deleted | boolean |  |  |

### `public.don_vi` (15 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ma_don_vi | character varying(20) |  |  |
| ten_don_vi | character varying(200) |  |  |
| ten_viet_tat | character varying(50) | ✓ |  |
| loai_don_vi | USER-DEFINED |  |  |
| parent_id | uuid | ✓ | FK→public.don_vi(id) |
| thu_tu_hien_thi | integer |  |  |
| is_active | boolean |  |  |
| is_deleted | boolean |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `public.hdld_danh_gia` (627 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| thang | integer |  |  |
| nam | integer |  |  |
| nhom_nghe | character varying(5) | ✓ |  |
| trang_thai | character varying(50) |  |  |
| nguoi_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| diem_tc_tb_tu | numeric | ✓ |  |
| diem_tc_tb_ql | numeric | ✓ |  |
| diem_kpi_70 | numeric | ✓ |  |
| ghi_chu | text | ✓ |  |
| ly_do_tra_lai | text | ✓ |  |
| ngay_nop | timestamp with time zone | ✓ |  |
| ngay_duyet | timestamp with time zone | ✓ |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `public.hdld_danh_gia_chi_tiet` (1629 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| danh_gia_id | uuid |  | FK→public.hdld_danh_gia(id) |
| so_tt | integer |  |  |
| diem_tu | numeric | ✓ |  |
| ghi_chu_tu | text | ✓ |  |
| diem_ql | numeric | ✓ |  |
| ghi_chu_ql | text | ✓ |  |
| ly_do_sua | text | ✓ |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `public.hdld_tieu_chi` (18 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| nhom | character varying(5) |  |  |
| ten_nhom | character varying(200) |  |  |
| so_tt | integer |  |  |
| ten_tieu_chi | character varying(200) |  |  |
| mo_ta_chi_tiet | text |  |  |
| diem_toi_da | integer |  |  |
| is_active | boolean |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `public.ke_khai_cong_viec` (44552 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| thang | integer |  |  |
| nam | integer |  |  |
| ngay_thuc_hien | date | ✓ |  |
| danh_muc_sp_id | uuid |  | FK→public.danh_muc_sp_cong_viec(id) |
| cap_do_id | uuid | ✓ | FK→public.cap_do_phuc_tap(id) |
| so_luong | integer |  |  |
| he_so_thuc_te | numeric | ✓ |  |
| nguoi_phe_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| mo_ta_cong_viec | text | ✓ |  |
| is_doi_moi_sang_tao | boolean |  |  |
| ngay_deadline | date | ✓ |  |
| ngay_hoan_thanh | date | ✓ |  |
| trang_thai | USER-DEFINED |  |  |
| so_sp_goc_quy_doi | numeric | ✓ |  |
| so_sp_chat_luong | numeric | ✓ |  |
| so_sp_tien_do | numeric | ✓ |  |
| is_deleted | boolean |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| tu_danh_gia_chat_luong | integer |  |  |
| tu_danh_gia_tien_do | integer |  |  |
| ghi_chu_tu_danh_gia | text | ✓ |  |
| so_loi_chat_luong | integer |  |  |
| so_loi_tien_do | integer |  |  |
| y_kien_lanh_dao | text | ✓ |  |
| is_khoa | boolean |  |  |
| ghi_chu_tu_dg_chat_luong | text | ✓ |  |
| ghi_chu_tu_dg_tien_do | text | ✓ |  |
| ghi_chu_loi_chat_luong | text | ✓ |  |
| ghi_chu_loi_tien_do | text | ✓ |  |
| don_vi_id_snapshot | uuid | ✓ | FK→public.don_vi(id) |
| version_kekhai | character varying(10) |  |  |
| he_so_quy_doi_snapshot | numeric | ✓ |  |
| nhom_pl3_snapshot | smallint | ✓ |  |
| linh_vuc_snapshot | character varying(10) | ✓ |  |

### `public.ke_khai_lanh_dao` (971 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| thang | integer |  |  |
| nam | integer |  |  |
| ten_cong_viec | character varying(500) |  |  |
| mo_ta | text | ✓ |  |
| ngay_thuc_hien | date |  |  |
| trang_thai_hoan_thanh | USER-DEFINED |  |  |
| so_luong | integer |  |  |
| nguoi_phe_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| trang_thai | character varying(20) |  |  |
| so_loi_chat_luong | integer |  |  |
| so_loi_tien_do | integer |  |  |
| y_kien_lanh_dao | text | ✓ |  |
| is_deleted | boolean |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| ghi_chu_loi_chat_luong | text | ✓ |  |
| ghi_chu_loi_tien_do | text | ✓ |  |

### `public.lanh_dao_chi_so` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| danh_gia_thang_id | uuid |  | FK→public.danh_gia_thang(id) |
| chi_so_d | numeric |  |  |
| ghi_chu_d | text | ✓ |  |
| co_cc_khong_hoan_thanh | boolean |  |  |
| chi_so_dd | numeric |  |  |
| ghi_chu_dd | text | ✓ |  |
| co_ton_tai_cham_tre | boolean |  |  |
| chi_so_e | numeric |  |  |
| ghi_chu_e | text | ✓ |  |
| co_mau_thuan_noi_bo | boolean |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `public.lich_su_dieu_chinh` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| loai_doi_tuong | character varying(50) |  |  |
| doi_tuong_id | uuid |  |  |
| nguoi_dieu_chinh_id | uuid |  | FK→public.cong_chuc(id) |
| truong_du_lieu | character varying(100) |  |  |
| gia_tri_cu | text | ✓ |  |
| gia_tri_moi | text | ✓ |  |
| ly_do | text | ✓ |  |
| ngay_dieu_chinh | timestamp with time zone |  |  |
| created_at | timestamp with time zone | ✓ |  |

### `public.lich_su_dieu_chuyen` (108 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| don_vi_cu_id | uuid | ✓ | FK→public.don_vi(id) |
| don_vi_moi_id | uuid | ✓ | FK→public.don_vi(id) |
| vai_tro_cu_id | uuid | ✓ | FK→public.vai_tro(id) |
| vai_tro_moi_id | uuid | ✓ | FK→public.vai_tro(id) |
| chuc_vu_cu | character varying(100) | ✓ |  |
| chuc_vu_moi | character varying(100) | ✓ |  |
| ly_do | text | ✓ |  |
| ngay_hieu_luc | date | ✓ |  |
| nguoi_thuc_hien_id | uuid | ✓ | FK→public.cong_chuc(id) |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| loai | character varying(20) |  |  |

### `public.nhom_cong_viec_pl3` (5 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| nhom | smallint |  |  |
| ten_nhom | character varying(200) |  |  |
| diem_toi_da | smallint |  |  |
| mo_ta | text | ✓ |  |
| is_active | boolean |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `public.phan_cong_phu_trach` (65 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| lanh_dao_id | uuid |  | FK→public.cong_chuc(id) |
| don_vi_id | uuid |  | FK→public.don_vi(id) |
| hieu_luc_tu | date |  |  |
| hieu_luc_den | date | ✓ |  |
| ghi_chu | text | ✓ |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| is_deleted | boolean |  |  |

### `public.phe_duyet_sp` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ke_khai_id | uuid |  | FK→public.ke_khai_cong_viec(id) |
| nguoi_phe_duyet_id | uuid |  | FK→public.cong_chuc(id) |
| trang_thai | USER-DEFINED |  |  |
| lan_loi_chat_luong | integer |  |  |
| lan_loi_tien_do | integer |  |  |
| ghi_chu | text | ✓ |  |
| ly_do_tu_choi | text | ✓ |  |
| ngay_phe_duyet | timestamp with time zone |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `public.phe_duyet_sp_backup_2026_04_v1` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ke_khai_id | uuid |  |  |
| nguoi_phe_duyet_id | uuid |  |  |
| trang_thai | USER-DEFINED |  |  |
| lan_loi_chat_luong | integer |  |  |
| lan_loi_tien_do | integer |  |  |
| ghi_chu | text | ✓ |  |
| ly_do_tu_choi | text | ✓ |  |
| ngay_phe_duyet | timestamp with time zone |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `public.phieu_danh_gia_quy` (302 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| quy | smallint |  |  |
| nam | smallint |  |  |
| uu_diem | text | ✓ |  |
| han_che | text | ✓ |  |
| y_kien_lanh_dao | text | ✓ |  |
| trang_thai | character varying(20) |  |  |
| ngay_gui_duyet | timestamp with time zone | ✓ |  |
| nguoi_phe_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| ngay_phe_duyet | timestamp with time zone | ✓ |  |
| ly_do_tu_choi | text | ✓ |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| tu_de_xuat_xep_loai | character varying(20) | ✓ |  |
| de_xuat_xep_loai | character varying(20) | ✓ |  |
| quyet_dinh_xep_loai | character varying(20) | ✓ |  |
| y_kien_cap_tham_quyen | text | ✓ |  |
| dd_quy_ke_khai | smallint | ✓ |  |
| dd_quy_ghi_chu | text | ✓ |  |
| dd_quy_phe_duyet | smallint | ✓ |  |

### `public.phieu_danh_gia_thang` (361 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| thang | smallint |  |  |
| nam | smallint |  |  |
| uu_diem | text | ✓ |  |
| han_che | text | ✓ |  |
| y_kien_lanh_dao | text | ✓ |  |
| trang_thai | character varying(20) |  |  |
| ngay_gui_duyet | timestamp with time zone | ✓ |  |
| nguoi_phe_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| ngay_phe_duyet | timestamp with time zone | ✓ |  |
| ly_do_tu_choi | text | ✓ |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `public.platform_config` (1 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| key | character varying(100) |  | PK |
| value | jsonb |  |  |
| mo_ta | text | ✓ |  |
| updated_by | uuid | ✓ | FK→public.cong_chuc(id) |
| updated_at | timestamp without time zone |  |  |

### `public.platform_role` (15 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ma_role | character varying(50) |  |  |
| ten_role | character varying(100) |  |  |
| mo_ta | text | ✓ |  |
| quyen_han | jsonb | ✓ |  |
| is_active | boolean |  |  |
| created_at | timestamp without time zone |  |  |

### `public.sp_cong_viec_chuan` (6 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ma_sp | character varying(10) |  |  |
| ten_sp | character varying(200) |  |  |
| mo_ta | text | ✓ |  |
| thoi_gian_phut | integer |  |  |
| he_so_quy_doi_sp1 | numeric |  |  |
| is_sp_goc | boolean |  |  |
| is_active | boolean |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `public.tieu_chi_chung` (31 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ma_tieu_chi | character varying(10) |  |  |
| ma_tieu_chi_con | character varying(10) | ✓ |  |
| nhom_tieu_chi | integer |  |  |
| ten_tieu_chi | text |  |  |
| mo_ta | text | ✓ |  |
| diem_toi_da | numeric |  |  |
| gia_tri_mac_dinh | boolean |  |  |
| loai_logic | character varying(20) |  |  |
| parent_ma_tieu_chi | character varying(10) | ✓ |  |
| thu_tu | integer |  |  |
| is_active | boolean |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `public.tieu_chi_chung_danh_gia` (26020 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| danh_gia_thang_id | uuid |  | FK→public.danh_gia_thang(id) |
| tieu_chi_id | uuid |  | FK→public.tieu_chi_chung(id) |
| is_achieved_cc | boolean |  |  |
| is_achieved_ld | boolean | ✓ |  |
| diem_tu_cham | numeric |  |  |
| diem_phe_duyet | numeric | ✓ |  |
| trang_thai | USER-DEFINED |  |  |
| nguoi_phe_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| ngay_gui | timestamp with time zone | ✓ |  |
| ngay_phe_duyet | timestamp with time zone | ✓ |  |
| ghi_chu_cc | text | ✓ |  |
| ghi_chu_ld | text | ✓ |  |
| ly_do_dieu_chinh | text | ✓ |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| diem_danh_gia_thang | numeric | ✓ |  |

### `public.vai_tro` (9 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ma_vai_tro | character varying(50) |  |  |
| ten_vai_tro | character varying(100) |  |  |
| cap_bac | USER-DEFINED |  |  |
| mo_ta | text | ✓ |  |
| is_lanh_dao | boolean |  |  |
| quyen_han | jsonb | ✓ |  |
| is_active | boolean |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| is_system_admin | boolean |  |  |

## Schema `lms` — Đào tạo trực tuyến (LMS) (20 bảng)

### `lms.bai_hoc` (31 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| khoa_hoc_id | uuid |  | FK→lms.khoa_hoc(id) |
| thu_tu | integer |  |  |
| tieu_de | character varying(300) |  |  |
| loai_noi_dung | character varying(50) |  |  |
| noi_dung | text | ✓ |  |
| file_url | text | ✓ |  |
| file_size_mb | numeric | ✓ |  |
| thoi_luong_phut | integer | ✓ |  |
| phai_xem_het | boolean | ✓ |  |
| thoi_gian_toi_thieu_giay | integer | ✓ |  |
| is_active | boolean | ✓ |  |
| created_at | timestamp with time zone | ✓ |  |
| pdf_url | character varying(500) | ✓ |  |

### `lms.bai_kiem_tra` (26 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| khoa_hoc_id | uuid | ✓ | FK→lms.khoa_hoc(id) |
| tieu_de | character varying(300) |  |  |
| mo_ta | text | ✓ |  |
| so_cau_hoi | integer |  |  |
| thoi_gian_lam_bai_phut | integer | ✓ |  |
| so_lan_lam_toi_da | integer | ✓ |  |
| diem_dat | numeric | ✓ |  |
| tron_de | boolean | ✓ |  |
| tron_dap_an | boolean | ✓ |  |
| ngay_mo | date | ✓ |  |
| ngay_dong | date | ✓ |  |
| nguoi_tao_id | uuid | ✓ | FK→public.cong_chuc(id) |
| is_active | boolean | ✓ |  |
| created_at | timestamp with time zone | ✓ |  |
| che_do_xem_ket_qua | character varying(50) |  |  |
| hien_giai_thich | boolean |  |  |
| gio_mo | character varying(5) | ✓ |  |
| gio_dong | character varying(5) | ✓ |  |
| loai_bai_kiem_tra | character varying(50) |  |  |
| yeu_cau_bai_lam | text | ✓ |  |
| dung_luong_toi_da_mb | integer | ✓ |  |
| dinh_dang_cho_phep | character varying(200) | ✓ |  |

### `lms.bai_kiem_tra_cau_hoi` (591 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| bai_kiem_tra_id | uuid |  | FK→lms.bai_kiem_tra(id); PK |
| cau_hoi_id | uuid |  | FK→lms.cau_hoi(id); PK |
| thu_tu | integer | ✓ |  |

### `lms.cau_hoi` (651 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| khoa_hoc_id | uuid | ✓ | FK→lms.khoa_hoc(id) |
| chuyen_de_id | uuid | ✓ | FK→lms.chuyen_de(id) |
| noi_dung | text |  |  |
| loai | character varying(50) |  |  |
| dap_an | jsonb |  |  |
| diem | numeric | ✓ |  |
| do_kho | character varying(20) | ✓ |  |
| van_ban_lien_quan_ids | jsonb | ✓ |  |
| nguoi_tao_id | uuid | ✓ | FK→public.cong_chuc(id) |
| is_active | boolean | ✓ |  |
| created_at | timestamp with time zone | ✓ |  |
| giai_thich | text | ✓ |  |
| bai_kiem_tra_id | uuid | ✓ | FK→lms.bai_kiem_tra(id) |
| linh_vuc_id | uuid | ✓ | FK→lms.linh_vuc(id) |

### `lms.cau_hoi_dgnl` (3039 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| linh_vuc_id | uuid |  | FK→lms.linh_vuc(id) |
| noi_dung | text |  |  |
| giai_thich | text | ✓ |  |
| loai | character varying(50) |  |  |
| dap_an | jsonb |  |  |
| diem | numeric | ✓ |  |
| do_kho | character varying(20) | ✓ |  |
| nguoi_tao_id | uuid | ✓ | FK→public.cong_chuc(id) |
| is_active | boolean | ✓ |  |
| created_at | timestamp with time zone | ✓ |  |
| updated_at | timestamp with time zone | ✓ |  |

### `lms.cau_truc_de` (74 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ky_thi_id | uuid |  | FK→lms.ky_thi(id) |
| vi_tri_id | uuid |  | FK→lms.vi_tri_viec_lam(id) |
| linh_vuc_id | uuid |  | FK→lms.linh_vuc(id) |
| so_cau_de | integer | ✓ |  |
| so_cau_trung_binh | integer | ✓ |  |
| so_cau_kho | integer | ✓ |  |
| created_at | timestamp with time zone | ✓ |  |

### `lms.cau_truc_de_template` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ten_template | character varying(200) |  |  |
| mo_ta | text | ✓ |  |
| nguoi_tao_id | uuid |  | FK→public.cong_chuc(id) |
| cau_truc | jsonb |  |  |
| is_active | boolean |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `lms.chung_chi` (325 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| khoa_hoc_id | uuid |  | FK→lms.khoa_hoc(id) |
| ma_chung_chi | character varying(50) |  |  |
| ten_chung_chi | character varying(300) | ✓ |  |
| diem_dat | numeric | ✓ |  |
| ngay_cap | timestamp with time zone | ✓ |  |
| nguoi_cap_id | uuid | ✓ | FK→public.cong_chuc(id) |
| file_url | text | ✓ |  |

### `lms.chuyen_de` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ma_chuyen_de | character varying(50) |  |  |
| ten_chuyen_de | character varying(200) |  |  |
| mo_ta | text | ✓ |  |
| anh_dai_dien | text | ✓ |  |
| thu_tu | integer | ✓ |  |
| is_active | boolean | ✓ |  |
| created_by | uuid | ✓ | FK→public.cong_chuc(id) |
| created_at | timestamp with time zone | ✓ |  |

### `lms.dang_ky_khoa_hoc` (2014 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| khoa_hoc_id | uuid |  | FK→lms.khoa_hoc(id) |
| loai_dang_ky | character varying(50) | ✓ |  |
| nguoi_giao_id | uuid | ✓ | FK→public.cong_chuc(id) |
| han_hoan_thanh | date | ✓ |  |
| trang_thai | character varying(50) | ✓ |  |
| phan_tram_hoan_thanh | numeric | ✓ |  |
| ngay_bat_dau_hoc | timestamp with time zone | ✓ |  |
| ngay_hoan_thanh | timestamp with time zone | ✓ |  |
| diem_cao_nhat | numeric | ✓ |  |
| so_lan_lam_bai | integer | ✓ |  |
| created_at | timestamp with time zone | ✓ |  |
| updated_at | timestamp with time zone | ✓ |  |
| nguoi_phe_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| ngay_phe_duyet | timestamp with time zone | ✓ |  |
| ly_do_tu_choi | text | ✓ |  |

### `lms.ket_qua_bai_kiem_tra` (7378 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| bai_kiem_tra_id | uuid |  | FK→lms.bai_kiem_tra(id) |
| lan_thu | integer |  |  |
| diem | numeric | ✓ |  |
| so_cau_dung | integer | ✓ |  |
| so_cau_sai | integer | ✓ |  |
| thoi_gian_lam_giay | integer | ✓ |  |
| chi_tiet_tra_loi | jsonb | ✓ |  |
| dat_yeu_cau | boolean | ✓ |  |
| ngay_lam | timestamp with time zone | ✓ |  |
| chi_tiet_nhap | jsonb | ✓ |  |
| so_lan_vi_pham | integer | ✓ |  |
| bai_nop_url | character varying(500) | ✓ |  |
| bai_nop_ten_file | character varying(255) | ✓ |  |
| bai_nop_size_bytes | bigint | ✓ |  |
| bai_nop_content_type | character varying(100) | ✓ |  |
| ngay_nop | timestamp with time zone | ✓ |  |
| nguoi_cham_id | uuid | ✓ | FK→public.cong_chuc(id) |
| diem_cham_tay | numeric | ✓ |  |
| nhan_xet | text | ✓ |  |
| trang_thai_cham | character varying(50) | ✓ |  |
| ngay_cham | timestamp with time zone | ✓ |  |

### `lms.khao_sat` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| khoa_hoc_id | uuid |  | FK→lms.khoa_hoc(id) |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| noi_dung | jsonb |  |  |
| created_at | timestamp with time zone | ✓ |  |

### `lms.khoa_hoc` (18 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ma_khoa_hoc | character varying(50) |  |  |
| ten_khoa_hoc | character varying(300) |  |  |
| mo_ta | text | ✓ |  |
| chuyen_de_id | uuid | ✓ | FK→lms.chuyen_de(id) |
| loai | character varying(50) |  |  |
| anh_dai_dien | text | ✓ |  |
| thoi_luong_phut | integer | ✓ |  |
| so_bai_hoc | integer | ✓ |  |
| dieu_kien_tien_quyet | jsonb | ✓ |  |
| diem_dat_yeu_cau | numeric | ✓ |  |
| ngay_bat_dau | date | ✓ |  |
| ngay_ket_thuc | date | ✓ |  |
| giang_vien_id | uuid | ✓ | FK→public.cong_chuc(id) |
| trang_thai | character varying(50) | ✓ |  |
| nguoi_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| ngay_duyet | timestamp with time zone | ✓ |  |
| is_active | boolean | ✓ |  |
| created_at | timestamp with time zone | ✓ |  |
| updated_at | timestamp with time zone | ✓ |  |
| search_vector | tsvector | ✓ |  |

### `lms.ky_thi` (15 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ma_ky_thi | character varying(50) |  |  |
| ten_ky_thi | character varying(300) |  |  |
| mo_ta | text | ✓ |  |
| ngay_bat_dau | timestamp with time zone |  |  |
| ngay_ket_thuc | timestamp with time zone |  |  |
| thoi_gian_lam_bai_phut | integer |  |  |
| diem_dat | numeric | ✓ |  |
| so_lan_thi_toi_da | integer | ✓ |  |
| tron_cau_hoi | boolean | ✓ |  |
| tron_dap_an | boolean | ✓ |  |
| hien_ket_qua | boolean | ✓ |  |
| hien_dap_an | boolean | ✓ |  |
| trang_thai | character varying(50) | ✓ |  |
| nguoi_tao_id | uuid |  | FK→public.cong_chuc(id) |
| nguoi_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| ngay_duyet | timestamp with time zone | ✓ |  |
| is_active | boolean | ✓ |  |
| created_at | timestamp with time zone | ✓ |  |
| updated_at | timestamp with time zone | ✓ |  |
| yeu_cau_toan_man_hinh | boolean |  |  |

### `lms.linh_vuc` (26 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ma_linh_vuc | character varying(50) |  |  |
| ten_linh_vuc | character varying(200) |  |  |
| mo_ta | text | ✓ |  |
| thu_tu | integer | ✓ |  |
| is_active | boolean | ✓ |  |
| created_at | timestamp with time zone | ✓ |  |
| updated_at | timestamp with time zone | ✓ |  |

### `lms.phien_thi` (415 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| phien_token | character varying(64) |  |  |
| ky_thi_id | uuid | ✓ | FK→lms.ky_thi(id) |
| thi_sinh_id | uuid | ✓ | FK→lms.thi_sinh(id) |
| thiet_bi | character varying(255) | ✓ |  |
| last_seen | timestamp with time zone | ✓ |  |
| created_at | timestamp with time zone | ✓ |  |

### `lms.thi_sinh` (1406 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ky_thi_id | uuid |  | FK→lms.ky_thi(id) |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| vi_tri_id | uuid |  | FK→lms.vi_tri_viec_lam(id) |
| trang_thai | character varying(50) | ✓ |  |
| lan_thi_hien_tai | integer | ✓ |  |
| diem_tong | numeric | ✓ |  |
| xep_loai | character varying(50) | ✓ |  |
| so_cau_dung | integer | ✓ |  |
| so_cau_sai | integer | ✓ |  |
| tong_so_cau | integer | ✓ |  |
| diem_theo_linh_vuc | jsonb | ✓ |  |
| thoi_gian_bat_dau | timestamp with time zone | ✓ |  |
| thoi_gian_nop | timestamp with time zone | ✓ |  |
| thoi_gian_lam_giay | integer | ✓ |  |
| de_thi_ids | jsonb | ✓ |  |
| chi_tiet_tra_loi | jsonb | ✓ |  |
| lich_su_thi | jsonb | ✓ |  |
| created_at | timestamp with time zone | ✓ |  |
| updated_at | timestamp with time zone | ✓ |  |
| chi_tiet_nhap | jsonb | ✓ |  |
| so_lan_vi_pham | integer | ✓ |  |
| da_xac_nhan | boolean |  |  |
| thoi_gian_xac_nhan | timestamp with time zone | ✓ |  |

### `lms.tien_do_bai_hoc` (1001 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| bai_hoc_id | uuid |  | FK→lms.bai_hoc(id) |
| trang_thai | character varying(50) | ✓ |  |
| thoi_gian_xem_giay | integer | ✓ |  |
| lan_xem_cuoi | timestamp with time zone | ✓ |  |
| ngay_hoan_thanh | timestamp with time zone | ✓ |  |

### `lms.vi_pham_thi` (2 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| thi_sinh_id | uuid |  | FK→lms.thi_sinh(id) |
| ky_thi_id | uuid |  | FK→lms.ky_thi(id) |
| lan_thi | integer |  |  |
| loai_vi_pham | character varying(50) |  |  |
| thoi_gian | timestamp with time zone |  |  |
| ly_do | text | ✓ |  |
| created_at | timestamp with time zone |  |  |

### `lms.vi_tri_viec_lam` (5 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ma_vi_tri | character varying(50) |  |  |
| ten_vi_tri | character varying(200) |  |  |
| mo_ta | text | ✓ |  |
| linh_vuc_ids | jsonb | ✓ |  |
| thu_tu | integer | ✓ |  |
| is_active | boolean | ✓ |  |
| created_at | timestamp with time zone | ✓ |  |
| updated_at | timestamp with time zone | ✓ |  |

## Schema `forum` — Diễn đàn nghiệp vụ (5 bảng)

### `forum.bieu_quyet` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| doi_tuong_type | character varying(20) |  |  |
| doi_tuong_id | uuid |  |  |
| loai | character varying(10) |  |  |
| created_at | timestamp without time zone |  |  |

### `forum.chu_de` (2 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| chuyen_muc_id | uuid |  | FK→forum.chuyen_muc(id) |
| tieu_de | character varying(500) |  |  |
| noi_dung | text |  |  |
| tags | jsonb |  |  |
| tac_gia_id | uuid |  | FK→public.cong_chuc(id) |
| trang_thai | character varying(50) |  |  |
| is_ghim | boolean |  |  |
| is_khoa | boolean |  |  |
| so_luot_xem | integer |  |  |
| so_tra_loi | integer |  |  |
| so_upvote | integer |  |  |
| tra_loi_chuan_id | uuid | ✓ | FK→forum.tra_loi(id) |
| van_ban_lien_quan | jsonb | ✓ |  |
| sop_lien_quan | jsonb | ✓ |  |
| nguoi_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| ngay_duyet | timestamp without time zone | ✓ |  |
| created_at | timestamp without time zone |  |  |
| updated_at | timestamp without time zone |  |  |
| is_deleted | boolean |  |  |
| search_vector | tsvector | ✓ |  |

### `forum.chuyen_muc` (9 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ten_chuyen_muc | character varying(200) |  |  |
| mo_ta | text | ✓ |  |
| icon | character varying(50) | ✓ |  |
| thu_tu | integer | ✓ |  |
| parent_id | uuid | ✓ | FK→forum.chuyen_muc(id) |
| chi_doc | boolean |  |  |
| yeu_cau_duyet | boolean |  |  |
| is_active | boolean |  |  |
| created_at | timestamp without time zone |  |  |

### `forum.theo_doi` (8 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id); PK |
| chu_de_id | uuid |  | FK→forum.chu_de(id); PK |
| created_at | timestamp without time zone |  |  |

### `forum.tra_loi` (13 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| chu_de_id | uuid |  | FK→forum.chu_de(id) |
| parent_id | uuid | ✓ | FK→forum.tra_loi(id) |
| noi_dung | text |  |  |
| tac_gia_id | uuid |  | FK→public.cong_chuc(id) |
| is_dap_an_chuan | boolean |  |  |
| is_an | boolean |  |  |
| so_upvote | integer |  |  |
| can_cu_phap_ly | jsonb | ✓ |  |
| created_at | timestamp without time zone |  |  |
| updated_at | timestamp without time zone |  |  |
| is_deleted | boolean |  |  |

## Schema `legal` — Pháp luật (6 bảng)

### `legal.ket_qua_quiz` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| quiz_id | uuid |  | FK→legal.quiz_van_ban(id) |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| diem | numeric | ✓ |  |
| so_cau_dung | integer | ✓ |  |
| dat_yeu_cau | boolean | ✓ |  |
| chi_tiet | jsonb | ✓ |  |
| created_at | timestamp without time zone |  |  |

### `legal.loai_van_ban` (8 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ma | character varying(50) |  |  |
| ten | character varying(200) |  |  |
| thu_tu | integer | ✓ |  |

### `legal.quiz_van_ban` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| van_ban_id | uuid |  | FK→legal.van_ban(id) |
| tieu_de | character varying(300) |  |  |
| so_cau_hoi | integer |  |  |
| thoi_gian_phut | integer | ✓ |  |
| diem_dat | numeric |  |  |
| cau_hoi | jsonb |  |  |
| nguoi_tao_id | uuid | ✓ | FK→public.cong_chuc(id) |
| is_active | boolean |  |  |
| created_at | timestamp without time zone |  |  |

### `legal.van_ban` (2 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| so_hieu | character varying(100) |  |  |
| trich_yeu | character varying(500) |  |  |
| loai_van_ban_id | uuid | ✓ | FK→legal.loai_van_ban(id) |
| co_quan_ban_hanh | character varying(200) | ✓ |  |
| ngay_ban_hanh | date | ✓ |  |
| ngay_hieu_luc | date | ✓ |  |
| ngay_het_hieu_luc | date | ✓ |  |
| trang_thai_hieu_luc | character varying(50) |  |  |
| van_ban_thay_the_id | uuid | ✓ | FK→legal.van_ban(id) |
| tom_tat | text | ✓ |  |
| noi_dung_html | text | ✓ |  |
| file_goc_url | text | ✓ |  |
| chuyen_de | jsonb |  |  |
| doi_tuong_ap_dung | jsonb |  |  |
| tags | jsonb |  |  |
| diem_moi | text | ✓ |  |
| viec_can_lam | text | ✓ |  |
| muc_do | character varying(50) |  |  |
| bat_buoc_doc | boolean |  |  |
| han_xac_nhan | date | ✓ |  |
| nguoi_nhap_id | uuid | ✓ | FK→public.cong_chuc(id) |
| nguoi_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| trang_thai_duyet | character varying(50) |  |  |
| ngay_xuat_ban | timestamp without time zone | ✓ |  |
| phien_ban | integer |  |  |
| created_at | timestamp without time zone |  |  |
| updated_at | timestamp without time zone |  |  |
| is_deleted | boolean |  |  |
| search_vector | tsvector | ✓ |  |

### `legal.van_ban_lien_ket` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| van_ban_id | uuid |  | FK→legal.van_ban(id); PK |
| van_ban_lien_quan_id | uuid |  | FK→legal.van_ban(id); PK |
| loai_lien_ket | character varying(50) | ✓ |  |

### `legal.xac_nhan_doc` (611 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| van_ban_id | uuid |  | FK→legal.van_ban(id) |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| da_doc | boolean |  |  |
| ngay_doc | timestamp without time zone | ✓ |  |
| thoi_gian_doc_giay | integer | ✓ |  |
| da_xac_nhan | boolean |  |  |
| ngay_xac_nhan | timestamp without time zone | ✓ |  |
| ghi_chu | text | ✓ |  |
| created_at | timestamp without time zone |  |  |

## Schema `portal` — Portal/CMS (5 bảng)

### `portal.bai_viet` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| chuyen_muc_id | uuid | ✓ | FK→portal.chuyen_muc(id) |
| tieu_de | character varying(500) |  |  |
| tom_tat | text | ✓ |  |
| noi_dung | text |  |  |
| anh_dai_dien | text | ✓ |  |
| trang_thai | character varying(50) |  |  |
| nguoi_soan_id | uuid | ✓ | FK→public.cong_chuc(id) |
| nguoi_kiem_tra_id | uuid | ✓ | FK→public.cong_chuc(id) |
| nguoi_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| ngay_xuat_ban | timestamp without time zone | ✓ |  |
| is_ghim | boolean |  |  |
| so_luot_xem | integer | ✓ |  |
| created_at | timestamp without time zone |  |  |
| updated_at | timestamp without time zone |  |  |
| is_deleted | boolean |  |  |

### `portal.chuyen_muc` (4 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ten | character varying(200) |  |  |
| slug | character varying(200) |  |  |
| mo_ta | text | ✓ |  |
| thu_tu | integer | ✓ |  |
| loai | character varying(50) |  |  |
| is_active | boolean |  |  |
| created_at | timestamp without time zone |  |  |

### `portal.tai_lieu` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ten_tai_lieu | character varying(300) |  |  |
| mo_ta | text | ✓ |  |
| thu_muc_id | uuid | ✓ | FK→portal.thu_muc(id) |
| file_url | text |  |  |
| file_name | character varying(300) | ✓ |  |
| file_size_bytes | bigint | ✓ |  |
| file_type | character varying(50) | ✓ |  |
| phien_ban | integer |  |  |
| phien_ban_truoc_id | uuid | ✓ | FK→portal.tai_lieu(id) |
| tags | jsonb |  |  |
| metadata | jsonb |  |  |
| quyen_truy_cap | character varying(50) |  |  |
| don_vi_ids | jsonb | ✓ |  |
| nguoi_tai_len_id | uuid | ✓ | FK→public.cong_chuc(id) |
| created_at | timestamp without time zone |  |  |
| is_deleted | boolean |  |  |

### `portal.thu_muc` (5 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ten | character varying(200) |  |  |
| parent_id | uuid | ✓ | FK→portal.thu_muc(id) |
| thu_tu | integer | ✓ |  |
| quyen_truy_cap | character varying(50) |  |  |
| don_vi_ids | jsonb | ✓ |  |
| created_by | uuid | ✓ | FK→public.cong_chuc(id) |
| created_at | timestamp without time zone |  |  |

### `portal.vinh_danh_thang` (1 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| thang | integer |  |  |
| nam | integer |  |  |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| tieu_de | character varying(200) |  |  |
| ly_do | text |  |  |
| anh_chan_dung | character varying(500) | ✓ |  |
| loi_tuyen_duong | text | ✓ |  |
| trang_thai | character varying(50) |  |  |
| nguoi_tao_id | uuid | ✓ | FK→public.cong_chuc(id) |
| ngay_cong_bo | timestamp without time zone | ✓ |  |
| created_at | timestamp without time zone |  |  |
| updated_at | timestamp without time zone |  |  |
| anh_vi_tri | character varying(20) | ✓ |  |

## Schema `common` — Dịch vụ dùng chung (thông báo, file...) (5 bảng)

### `common.audit_log` (683 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| module | character varying(20) |  |  |
| hanh_dong | character varying(50) |  |  |
| doi_tuong_loai | character varying(50) | ✓ |  |
| doi_tuong_id | uuid | ✓ |  |
| nguoi_thuc_hien_id | uuid |  | FK→public.cong_chuc(id) |
| ip_address | inet | ✓ |  |
| user_agent | text | ✓ |  |
| chi_tiet | jsonb | ✓ |  |
| created_at | timestamp with time zone |  |  |

### `common.file_storage` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| file_name | character varying(500) |  |  |
| file_path | text |  |  |
| file_size_bytes | bigint | ✓ |  |
| mime_type | character varying(100) | ✓ |  |
| module | character varying(50) |  |  |
| doi_tuong_type | character varying(50) | ✓ |  |
| doi_tuong_id | uuid | ✓ |  |
| nguoi_tai_len_id | uuid | ✓ | FK→public.cong_chuc(id) |
| created_at | timestamp without time zone |  |  |
| is_deleted | boolean |  |  |

### `common.knowledge_base` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| loai | character varying(20) |  |  |
| tieu_de | character varying(500) |  |  |
| noi_dung | text |  |  |
| chuyen_de | jsonb |  |  |
| tags | jsonb |  |  |
| chu_so_huu_id | uuid | ✓ | FK→public.cong_chuc(id) |
| trang_thai | character varying(50) |  |  |
| van_ban_lien_quan | jsonb | ✓ |  |
| chu_de_forum_lien_quan | jsonb | ✓ |  |
| phien_ban | integer |  |  |
| ngay_cap_nhat_cuoi | timestamp without time zone | ✓ |  |
| search_vector | tsvector | ✓ |  |
| created_at | timestamp without time zone |  |  |
| updated_at | timestamp without time zone |  |  |
| is_deleted | boolean |  |  |

### `common.kpi_integration_log` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| thang | integer |  |  |
| nam | integer |  |  |
| module | character varying(50) |  |  |
| metrics | jsonb |  |  |
| diem_quy_doi | numeric | ✓ |  |
| synced_at | timestamp without time zone |  |  |

### `common.thong_bao` (8540 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| nguoi_nhan_id | uuid |  | FK→public.cong_chuc(id) |
| tieu_de | character varying(300) |  |  |
| noi_dung | text | ✓ |  |
| loai | character varying(50) |  |  |
| link_url | text | ✓ |  |
| doi_tuong_type | character varying(50) | ✓ |  |
| doi_tuong_id | uuid | ✓ |  |
| da_doc | boolean |  |  |
| ngay_doc | timestamp without time zone | ✓ |  |
| muc_do | character varying(20) |  |  |
| created_at | timestamp without time zone |  |  |

## Schema `meeting` — Họp Không Giấy (HKG) (13 bảng)

### `meeting.bien_ban` (7 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cuoc_hop_id | uuid |  | FK→meeting.cuoc_hop(id) |
| noi_dung_json | jsonb | ✓ |  |
| noi_dung_html | text | ✓ |  |
| trang_thai | character varying(30) |  |  |
| file_pdf_minio_key | character varying(500) | ✓ |  |
| file_docx_minio_key | character varying(500) | ✓ |  |
| is_mock_signed | boolean |  |  |
| qr_xac_thuc | character varying(500) | ✓ |  |
| hash_noi_dung | character varying(64) | ✓ |  |
| nguoi_soan_id | uuid |  | FK→public.cong_chuc(id) |
| nguoi_ky_id | uuid | ✓ | FK→public.cong_chuc(id) |
| thoi_gian_ky | timestamp with time zone | ✓ |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `meeting.cuoc_hop` (8 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| tieu_de | character varying(500) |  |  |
| mo_ta | text | ✓ |  |
| khoi | character varying(20) |  |  |
| hinh_thuc | character varying(20) |  |  |
| ngay_hop | date |  |  |
| gio_bat_dau | time without time zone |  |  |
| gio_ket_thuc | time without time zone | ✓ |  |
| dia_diem | character varying(300) | ✓ |  |
| don_vi_to_chuc_id | uuid |  | FK→public.don_vi(id) |
| chu_toa_id | uuid |  | FK→public.cong_chuc(id) |
| thu_ky_id | uuid | ✓ | FK→public.cong_chuc(id) |
| trang_thai | character varying(30) |  |  |
| la_dinh_ky | boolean | ✓ |  |
| chu_ky | character varying(20) | ✓ |  |
| chi_bo_id | uuid | ✓ |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| created_by | uuid |  | FK→public.cong_chuc(id) |
| is_deleted | boolean |  |  |

### `meeting.diem_danh` (28 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cuoc_hop_id | uuid |  | FK→meeting.cuoc_hop(id) |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| hinh_thuc | character varying(20) |  |  |
| trang_thai | character varying(20) |  |  |
| gio_diem_danh | timestamp with time zone | ✓ |  |
| ghi_chu | text | ✓ |  |
| nguoi_diem_danh_id | uuid | ✓ | FK→public.cong_chuc(id) |
| created_at | timestamp with time zone |  |  |

### `meeting.ket_luan` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cuoc_hop_id | uuid |  | FK→meeting.cuoc_hop(id) |
| noi_dung | text |  |  |
| nguoi_phu_trach_id | uuid |  | FK→public.cong_chuc(id) |
| don_vi_phu_trach_id | uuid | ✓ | FK→public.don_vi(id) |
| han_hoan_thanh | date | ✓ |  |
| muc_uu_tien | character varying(10) |  |  |
| tien_do_phan_tram | integer |  |  |
| trang_thai | character varying(30) |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| is_deleted | boolean |  |  |

### `meeting.mau_bieu` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| loai | character varying(30) |  |  |
| ten_mau | character varying(200) |  |  |
| mo_ta | text | ✓ |  |
| ap_dung_cho | character varying(50) |  |  |
| minio_key | character varying(500) |  |  |
| phien_ban | integer |  |  |
| la_mac_dinh | boolean |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| created_by | uuid |  | FK→public.cong_chuc(id) |
| is_deleted | boolean |  |  |

### `meeting.nhom_thanh_phan` (1 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ten_nhom | character varying(200) |  |  |
| mo_ta | text | ✓ |  |
| loai_nhom | character varying(100) | ✓ |  |
| nguoi_tao_id | uuid |  | FK→public.cong_chuc(id) |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `meeting.nhom_thanh_phan_chi_tiet` (34 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| nhom_id | uuid |  | FK→meeting.nhom_thanh_phan(id) |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| vai_tro | character varying(20) |  |  |
| loai_tham_du | character varying(20) |  |  |
| created_at | timestamp with time zone |  |  |

### `meeting.tai_lieu` (37 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cuoc_hop_id | uuid |  | FK→meeting.cuoc_hop(id) |
| ten_tai_lieu | character varying(500) |  |  |
| mo_ta | text | ✓ |  |
| minio_bucket | character varying(100) |  |  |
| minio_key | character varying(500) |  |  |
| file_size | bigint |  |  |
| mime_type | character varying(100) | ✓ |  |
| extension | character varying(10) | ✓ |  |
| phan_quyen | character varying(20) |  |  |
| cho_phep_tai | boolean |  |  |
| cho_phep_in | boolean |  |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |
| created_by | uuid |  | FK→public.cong_chuc(id) |
| is_deleted | boolean |  |  |

### `meeting.thanh_phan` (159 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cuoc_hop_id | uuid |  | FK→meeting.cuoc_hop(id) |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| loai_tham_du | character varying(20) |  |  |
| xac_nhan | character varying(20) | ✓ |  |
| nguoi_uy_quyen_id | uuid | ✓ | FK→public.cong_chuc(id) |
| ghi_chu_xac_nhan | text | ✓ |  |
| thoi_gian_xac_nhan | timestamp with time zone | ✓ |  |
| created_at | timestamp with time zone |  |  |

### `meeting.tien_do` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ket_luan_id | uuid |  | FK→meeting.ket_luan(id) |
| mo_ta | text |  |  |
| phan_tram_truoc | integer | ✓ |  |
| phan_tram_sau | integer |  |  |
| file_minh_chung_minio_key | character varying(500) | ✓ |  |
| nguoi_cap_nhat_id | uuid |  | FK→public.cong_chuc(id) |
| created_at | timestamp with time zone |  |  |

### `meeting.trang_thai_trinh_chieu` (3 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cuoc_hop_id | uuid |  | FK→meeting.cuoc_hop(id) |
| tai_lieu_hien_tai_id | uuid | ✓ | FK→meeting.tai_lieu(id) |
| trang_hien_tai | integer |  |  |
| zoom_level | numeric |  |  |
| is_active | boolean |  |  |
| bat_dau_luc | timestamp with time zone | ✓ |  |
| ket_thuc_luc | timestamp with time zone | ✓ |  |
| cap_nhat_luc | timestamp with time zone |  |  |
| cap_nhat_boi_id | uuid | ✓ | FK→public.cong_chuc(id) |

### `meeting.xin_phep_vang` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cuoc_hop_id | uuid |  | FK→meeting.cuoc_hop(id) |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| ly_do | text |  |  |
| nguoi_du_thay_id | uuid | ✓ | FK→public.cong_chuc(id) |
| minio_key | character varying(500) | ✓ |  |
| trang_thai | character varying(30) |  |  |
| auto_approved | boolean |  |  |
| nguoi_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| thoi_gian_duyet | timestamp with time zone | ✓ |  |
| ly_do_tu_choi | text | ✓ |  |
| created_at | timestamp with time zone |  |  |
| updated_at | timestamp with time zone |  |  |

### `meeting.y_kien` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| cuoc_hop_id | uuid |  | FK→meeting.cuoc_hop(id) |
| cong_chuc_id | uuid |  | FK→public.cong_chuc(id) |
| noi_dung | text |  |  |
| loai | character varying(20) |  |  |
| minio_key | character varying(500) | ✓ |  |
| created_at | timestamp with time zone |  |  |
| is_deleted | boolean |  |  |

## Schema `chi_tieu` — Chỉ tiêu đơn vị (5 bảng)

### `chi_tieu.dang_ky_thang` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| don_vi_id | uuid |  | FK→public.don_vi(id) |
| chi_tieu_id | uuid |  | FK→chi_tieu.danh_muc_chi_tieu(id) |
| thang | integer |  |  |
| nam | integer |  |  |
| khong_dang_ky | boolean | ✓ |  |
| gia_tri_dang_ky | numeric | ✓ |  |
| gia_tri_ket_qua | numeric | ✓ |  |
| danh_gia_tu_dong | character varying(100) | ✓ |  |
| danh_gia_ghi_chu | character varying(200) | ✓ |  |
| trang_thai | character varying(30) |  |  |
| nguoi_theo_doi_id | uuid |  | FK→public.cong_chuc(id) |
| nguoi_duyet_id | uuid | ✓ | FK→public.cong_chuc(id) |
| ngay_gui_dang_ky | timestamp without time zone | ✓ |  |
| ngay_duyet_dang_ky | timestamp without time zone | ✓ |  |
| ngay_gui_ket_qua | timestamp without time zone | ✓ |  |
| ngay_duyet_ket_qua | timestamp without time zone | ✓ |  |
| ly_do_tu_choi | text | ✓ |  |
| is_khoa | boolean | ✓ |  |
| created_at | timestamp without time zone | ✓ |  |
| updated_at | timestamp without time zone | ✓ |  |
| is_deleted | boolean | ✓ |  |

### `chi_tieu.danh_muc_chi_tieu` (38 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| linh_vuc_id | uuid |  | FK→chi_tieu.linh_vuc(id) |
| ma_chi_tieu | character varying(30) |  |  |
| ten_chi_tieu | character varying(500) |  |  |
| don_vi_tinh | character varying(50) |  |  |
| kieu_du_lieu | character varying(20) |  |  |
| co_phan_dau | boolean | ✓ |  |
| van_ban_giao | character varying(300) | ✓ |  |
| mo_ta | text | ✓ |  |
| thu_tu | integer | ✓ |  |
| is_active | boolean | ✓ |  |
| created_at | timestamp without time zone | ✓ |  |
| updated_at | timestamp without time zone | ✓ |  |

### `chi_tieu.giao_nam` (190 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| don_vi_id | uuid |  | FK→public.don_vi(id) |
| chi_tieu_id | uuid |  | FK→chi_tieu.danh_muc_chi_tieu(id) |
| nam | integer |  |  |
| loai_muc | character varying(20) |  |  |
| gia_tri_giao | numeric |  |  |
| luy_ke_dau_ky | numeric | ✓ |  |
| nguoi_giao_id | uuid | ✓ | FK→public.cong_chuc(id) |
| ghi_chu | text | ✓ |  |
| created_at | timestamp without time zone | ✓ |  |
| updated_at | timestamp without time zone | ✓ |  |
| is_deleted | boolean | ✓ |  |

### `chi_tieu.lich_su_duyet` (0 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| dang_ky_thang_id | uuid |  | FK→chi_tieu.dang_ky_thang(id) |
| hanh_dong | character varying(30) |  |  |
| nguoi_thuc_hien_id | uuid |  | FK→public.cong_chuc(id) |
| noi_dung_truoc | jsonb | ✓ |  |
| noi_dung_sau | jsonb | ✓ |  |
| ghi_chu | text | ✓ |  |
| created_at | timestamp without time zone | ✓ |  |

### `chi_tieu.linh_vuc` (7 dòng)
| Cột | Kiểu | Null | Khóa / FK |
|---|---|---|---|
| id | uuid |  | PK |
| ma_linh_vuc | character varying(30) |  |  |
| ten_linh_vuc | character varying(200) |  |  |
| van_ban_ke_hoach | character varying(300) | ✓ |  |
| thu_tu | integer | ✓ |  |
| is_active | boolean | ✓ |  |
| created_at | timestamp without time zone | ✓ |  |
| updated_at | timestamp without time zone | ✓ |  |
