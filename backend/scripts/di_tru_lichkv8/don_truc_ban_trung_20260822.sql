-- Dọn hậu quả lượt chạy lại 03_truc_ban.py — 22/08/2026
--
--   1. 333 ca trực bị ghi hai lần, mỗi nhóm ĐÚNG 2 dòng và ĐÚNG 1 dòng sạch.
--      Xoá MỀM dòng xấu (giữ lại để hoàn tác được), giữ dòng sạch.
--   2. 15 ca trực KHÔNG có bản sao sạch — sửa tại chỗ. 14 dòng dạng khoa học
--      (ca trực 23/08) và 1 dòng người dùng gõ tay có dấu cách `034 3468299`.
--   3. Trỏ lại 317 ánh xạ di trú đang chỉ vào dòng sắp bị xoá mềm.
--
-- Mọi bước đều có chốt kiểm tra; lệch một con số là RAISE EXCEPTION và cả
-- giao dịch tự huỷ, không để lại nửa vời.

\set ON_ERROR_STOP on

BEGIN;

DO $$
DECLARE
    truoc_tong    int;
    truoc_hong    int;
    truoc_trung   int;
    n_xoa         int;
    n_sua         int;
    n_tro_lai     int;
    sau_tong      int;
    sau_hong      int;
    sau_trung     int;
BEGIN
    SELECT count(*),
           count(*) FILTER (WHERE so_dien_thoai !~ '^0[0-9]{9}$')
      INTO truoc_tong, truoc_hong
      FROM meeting.truc_ban WHERE is_deleted = false;

    SELECT coalesce(sum(n - 1), 0) INTO truoc_trung FROM (
        SELECT count(*) n FROM meeting.truc_ban WHERE is_deleted = false
         GROUP BY ngay_truc, tru_so_id, ho_ten HAVING count(*) > 1) x;

    RAISE NOTICE 'TRƯỚC: % dòng, % số sai khuôn, % dòng thừa',
                 truoc_tong, truoc_hong, truoc_trung;

    IF truoc_tong <> 681 OR truoc_hong <> 348 OR truoc_trung <> 333 THEN
        RAISE EXCEPTION 'Số liệu đầu vào lệch với lúc khảo sát (681/348/333) '
                        '— dừng lại, phải khảo sát lại trước khi dọn';
    END IF;

    -- ── 1. Trỏ lại ánh xạ TRƯỚC khi xoá mềm ──────────────────────────
    -- Lượt chạy thứ hai đã ghi đè `id_dich` sang dòng mới; giờ dòng mới sắp
    -- bị xoá mềm nên phải trỏ về dòng sạch, nếu không bảng đối soát chỉ vào
    -- bản ghi đã xoá.
    WITH cap AS (
        SELECT xau.id AS id_xau, sach.id AS id_sach
          FROM meeting.truc_ban xau
          JOIN meeting.truc_ban sach
            ON sach.ngay_truc = xau.ngay_truc
           AND sach.tru_so_id = xau.tru_so_id
           AND sach.ho_ten    = xau.ho_ten
           AND sach.is_deleted = false
           AND sach.so_dien_thoai ~ '^0[0-9]{9}$'
         WHERE xau.is_deleted = false
           AND xau.so_dien_thoai !~ '^0[0-9]{9}$'
    )
    UPDATE meeting.di_tru_nguon d
       SET id_dich = c.id_sach
      FROM cap c
     WHERE d.bang_dich = 'meeting.truc_ban' AND d.id_dich = c.id_xau;
    GET DIAGNOSTICS n_tro_lai = ROW_COUNT;
    RAISE NOTICE 'Đã trỏ lại % ánh xạ di trú', n_tro_lai;

    -- ── 2. Xoá mềm dòng xấu trong nhóm trùng ─────────────────────────
    WITH nhom AS (
        SELECT ngay_truc, tru_so_id, ho_ten
          FROM meeting.truc_ban WHERE is_deleted = false
         GROUP BY 1, 2, 3
        HAVING count(*) = 2
           AND count(*) FILTER (WHERE so_dien_thoai ~ '^0[0-9]{9}$') = 1
    )
    UPDATE meeting.truc_ban t
       SET is_deleted = true, updated_at = NOW()
      FROM nhom n
     WHERE t.ngay_truc = n.ngay_truc AND t.tru_so_id = n.tru_so_id
       AND t.ho_ten = n.ho_ten AND t.is_deleted = false
       AND t.so_dien_thoai !~ '^0[0-9]{9}$';
    GET DIAGNOSTICS n_xoa = ROW_COUNT;

    IF n_xoa <> 333 THEN
        RAISE EXCEPTION 'Xoá mềm % dòng, chờ đúng 333 — huỷ giao dịch', n_xoa;
    END IF;
    RAISE NOTICE 'Đã xoá mềm % dòng trùng', n_xoa;

    -- ── 3. Sửa 15 số hỏng không có bản sao sạch ──────────────────────
    -- Cùng phép biến đổi với `chuan_hoa_sdt` phía ứng dụng: dạng khoa học thì
    -- đổi qua số nguyên, còn lại thì bỏ mọi ký tự không phải chữ số; ra 9 chữ
    -- số nghĩa là đã rụng số 0 đứng đầu.
    WITH sach AS (
        SELECT id, CASE WHEN length(so) = 9 THEN '0' || so ELSE so END AS so
          FROM (
            SELECT id,
                   CASE WHEN so_dien_thoai ~ '[Ee]'
                        THEN (round(so_dien_thoai::numeric))::bigint::text
                        ELSE regexp_replace(so_dien_thoai, '[^0-9]', '', 'g')
                   END AS so
              FROM meeting.truc_ban
             WHERE is_deleted = false
               AND so_dien_thoai !~ '^0[0-9]{9}$') x
    )
    UPDATE meeting.truc_ban t
       SET so_dien_thoai = s.so, updated_at = NOW()
      FROM sach s WHERE t.id = s.id;
    GET DIAGNOSTICS n_sua = ROW_COUNT;

    IF n_sua <> 15 THEN
        RAISE EXCEPTION 'Sửa % số, chờ đúng 15 — huỷ giao dịch', n_sua;
    END IF;
    RAISE NOTICE 'Đã sửa % số điện thoại', n_sua;

    -- ── 4. Chốt kết quả ──────────────────────────────────────────────
    SELECT count(*),
           count(*) FILTER (WHERE so_dien_thoai !~ '^0[0-9]{9}$')
      INTO sau_tong, sau_hong
      FROM meeting.truc_ban WHERE is_deleted = false;

    SELECT coalesce(sum(n - 1), 0) INTO sau_trung FROM (
        SELECT count(*) n FROM meeting.truc_ban WHERE is_deleted = false
         GROUP BY ngay_truc, tru_so_id, ho_ten HAVING count(*) > 1) x;

    RAISE NOTICE 'SAU: % dòng, % số sai khuôn, % dòng thừa',
                 sau_tong, sau_hong, sau_trung;

    IF sau_tong <> 348 OR sau_hong <> 0 OR sau_trung <> 0 THEN
        RAISE EXCEPTION 'Kết quả không đạt (chờ 348/0/0) — huỷ giao dịch';
    END IF;

    -- Không được mất ca trực nào: mỗi khoá (ngày, trụ sở, họ tên) còn hiệu
    -- lực trước khi dọn đều phải còn đúng một dòng sau khi dọn.
    IF truoc_tong - n_xoa <> sau_tong THEN
        RAISE EXCEPTION 'Số dòng không khớp phép trừ — huỷ giao dịch';
    END IF;
END $$;

COMMIT;
