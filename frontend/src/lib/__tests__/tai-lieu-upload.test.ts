/**
 * Kiểm thử helper tải tài liệu — chủ yếu là chốt lại lỗi "bấm chọn file không
 * thêm được gì" để nó không quay lại.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest';

import {
  coDaiFile,
  gopFile,
  loiFile,
  moTaFileHong,
  taiNhieuFile,
} from '../tai-lieu-upload';

vi.mock('@/services/hkg', () => ({
  taiLieuApi: { upload: vi.fn() },
}));

import { taiLieuApi } from '@/services/hkg';

const upload = vi.mocked(taiLieuApi.upload);

function taoFile(ten: string, co = 10): File {
  return new File([new Uint8Array(co)], ten, { type: 'application/pdf' });
}

/**
 * Giả lập `input.files` của trình duyệt: danh sách SỐNG, đặt lại `value` là
 * rỗng theo. Đây chính là chỗ lỗi cũ nằm.
 */
function fileListSong(files: File[]) {
  let hienTai = files;
  const ds = {
    get length() {
      return hienTai.length;
    },
    item: (i: number) => hienTai[i] ?? null,
    [Symbol.iterator]: function* () {
      yield* hienTai;
    },
  };
  files.forEach((f, i) => Object.defineProperty(ds, i, { get: () => hienTai[i], enumerable: true }));
  return { ds: ds as unknown as FileList, donDep: () => { hienTai = []; } };
}

describe('gopFile', () => {
  it('chụp FileList ngay, không phụ thuộc danh sách sống', () => {
    // Lỗi cũ: gộp file nằm trong setState(prev => …), React gọi lúc vẽ lại,
    // tức là SAU khi ô chọn file đã bị dọn → không thêm được file nào.
    const { ds, donDep } = fileListSong([taoFile('a.pdf'), taoFile('b.pdf')]);
    const ketQua = gopFile([], ds);
    donDep(); // trình duyệt dọn `input.value = ''`

    expect(ketQua.map((f) => f.name)).toEqual(['a.pdf', 'b.pdf']);
  });

  it('nhận nhiều file một lượt', () => {
    const ds = [taoFile('1.pdf'), taoFile('2.docx'), taoFile('3.xlsx')];
    expect(gopFile([], ds)).toHaveLength(3);
  });

  it('bỏ trùng theo tên + cỡ, kể cả trùng trong cùng một lượt chọn', () => {
    const cu = [taoFile('a.pdf', 10)];
    const moi = [taoFile('a.pdf', 10), taoFile('a.pdf', 10), taoFile('a.pdf', 99)];
    const ketQua = gopFile(cu, moi);

    // Giữ bản cũ, bỏ hai bản trùng hệt, nhận bản khác cỡ.
    expect(ketQua).toHaveLength(2);
    expect(ketQua[1].size).toBe(99);
  });

  it('trả về đúng mảng cũ khi không có gì để thêm', () => {
    const cu = [taoFile('a.pdf')];
    expect(gopFile(cu, null)).toBe(cu);
    expect(gopFile(cu, [])).toBe(cu);
  });
});

describe('loiFile', () => {
  it('cho qua đuôi hợp lệ', () => {
    expect(loiFile(taoFile('bao-cao.PDF'))).toBeNull();
    expect(loiFile(taoFile('bang-ke.xlsx'))).toBeNull();
  });

  it('chặn đuôi lạ và file không có đuôi', () => {
    expect(loiFile(taoFile('virus.exe'))).toMatch(/không được phép/);
    expect(loiFile(taoFile('khongduoi'))).toMatch(/trống/);
  });

  it('chặn file rỗng và file quá nặng', () => {
    expect(loiFile(taoFile('rong.pdf', 0))).toBe('file rỗng');

    const nang = taoFile('to.pdf', 1);
    Object.defineProperty(nang, 'size', { value: 101 * 1024 * 1024 });
    expect(loiFile(nang)).toMatch(/vượt mức 100MB/);
  });
});

describe('taiNhieuFile', () => {
  beforeEach(() => upload.mockReset());

  it('tải hết mọi file, mỗi file một lượt gọi', async () => {
    upload.mockResolvedValue({} as never);
    const files = [taoFile('a.pdf'), taoFile('b.pdf'), taoFile('c.pdf'), taoFile('d.pdf')];

    const hong = await taiNhieuFile({ cuocHopId: 'ch-1', files, moTa: 'Giấy mời' });

    expect(hong).toEqual([]);
    expect(upload).toHaveBeenCalledTimes(4);
    expect(upload.mock.calls.map((c) => c[0].file.name).sort()).toEqual([
      'a.pdf', 'b.pdf', 'c.pdf', 'd.pdf',
    ]);
    expect(upload.mock.calls[0][0].mo_ta).toBe('Giấy mời');
  });

  it('chạy tối đa 3 file cùng lúc', async () => {
    let dangChay = 0;
    let dinhCao = 0;
    upload.mockImplementation(async () => {
      dangChay += 1;
      dinhCao = Math.max(dinhCao, dangChay);
      await new Promise((r) => setTimeout(r, 5));
      dangChay -= 1;
      return {} as never;
    });

    await taiNhieuFile({
      cuocHopId: 'ch-1',
      files: Array.from({ length: 9 }, (_, i) => taoFile(`f${i}.pdf`)),
    });

    expect(dinhCao).toBe(3);
  });

  it('một file hỏng không kéo theo file khác, và báo theo đúng thứ tự đã chọn', async () => {
    // Nhận tham số phòng hờ: vitest còn gọi lại mock một lượt không tham số
    // lúc dọn dẹp sau test, destructure thẳng là nổ ngay ở đó.
    upload.mockImplementation(async (input) => {
      if (input?.file?.name === 'b.pdf') throw new Error('nổ');
      return {} as never;
    });
    const files = [taoFile('a.pdf'), taoFile('b.pdf'), taoFile('c.pdf')];

    const hong = await taiNhieuFile({ cuocHopId: 'ch-1', files });

    expect(hong.map((h) => h.ten)).toEqual(['b.pdf']);
    expect(upload).toHaveBeenCalledTimes(3); // a và c vẫn được nộp
  });

  it('file sai đuôi bị chặn tại chỗ, không gọi lên máy chủ', async () => {
    upload.mockResolvedValue({} as never);
    const files = [taoFile('a.pdf'), taoFile('virus.exe')];

    const hong = await taiNhieuFile({ cuocHopId: 'ch-1', files });

    expect(hong.map((h) => h.ten)).toEqual(['virus.exe']);
    expect(upload).toHaveBeenCalledTimes(1);
  });

  it('báo file đang tải để giao diện hiện vòng quay, và dọn sạch khi xong', async () => {
    upload.mockResolvedValue({} as never);
    const moc: string[][] = [];

    await taiNhieuFile({
      cuocHopId: 'ch-1',
      files: [taoFile('a.pdf'), taoFile('b.pdf')],
      onDoiDangTai: (ds) => moc.push(ds),
    });

    expect(moc.some((m) => m.includes('a.pdf'))).toBe(true);
    expect(moc.some((m) => m.includes('b.pdf'))).toBe(true);
    expect(moc.at(-1)).toEqual([]);
  });
});

describe('phụ trợ', () => {
  it('coDaiFile đọc được cho người dùng', () => {
    expect(coDaiFile(512)).toBe('512 B');
    expect(coDaiFile(2048)).toBe('2 KB');
    expect(coDaiFile(5 * 1024 * 1024)).toBe('5.0 MB');
  });

  it('moTaFileHong ghép tên kèm lý do', () => {
    expect(moTaFileHong([{ ten: 'a.pdf', loi: 'quá nặng' }])).toBe('a.pdf (quá nặng)');
  });
});
