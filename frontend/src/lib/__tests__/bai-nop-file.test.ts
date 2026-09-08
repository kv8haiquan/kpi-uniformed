/**
 * Test cho lib/bai-nop-file.ts — nhận diện loại file bài nộp thực hành.
 */

import { describe, it, expect } from 'vitest';
import {
  layExtension,
  loaiFileBaiNop,
  iconBaiNop,
  nhanBaiNop,
  moTaDinhDang,
} from '../bai-nop-file';

describe('layExtension', () => {
  it('lấy đuôi từ tên file thường', () => {
    expect(layExtension('bao-cao.PDF')).toBe('pdf');
    expect(layExtension('bai lam.docx')).toBe('docx');
  });

  it('bỏ query string và đường dẫn', () => {
    expect(layExtension('/uploads/lms/bai-thuc-hanh/abc_bao-cao.pdf?v=2')).toBe('pdf');
    expect(layExtension('/uploads/lms/a/b.docx#page=1')).toBe('docx');
  });

  it('trả chuỗi rỗng khi không có đuôi hoặc không có giá trị', () => {
    expect(layExtension('README')).toBe('');
    expect(layExtension(null)).toBe('');
    expect(layExtension(undefined)).toBe('');
  });
});

describe('loaiFileBaiNop', () => {
  it('phân biệt PDF, Word, video, ảnh', () => {
    expect(loaiFileBaiNop('a.pdf')).toBe('PDF');
    expect(loaiFileBaiNop('a.doc')).toBe('WORD');
    expect(loaiFileBaiNop('a.docx')).toBe('WORD');
    expect(loaiFileBaiNop('a.mp4')).toBe('VIDEO');
    expect(loaiFileBaiNop('a.png')).toBe('ANH');
  });

  it('Excel/PowerPoint xếp vào tài liệu, còn lại là khác', () => {
    expect(loaiFileBaiNop('a.xlsx')).toBe('TAI_LIEU');
    expect(loaiFileBaiNop('a.pptx')).toBe('TAI_LIEU');
    expect(loaiFileBaiNop('a.zip')).toBe('KHAC');
  });
});

describe('iconBaiNop / nhanBaiNop', () => {
  it('Word có icon và nhãn riêng, không lẫn với PDF', () => {
    expect(iconBaiNop('bai.docx')).toBe('📘');
    expect(nhanBaiNop('bai.docx')).toBe('Word');
    expect(iconBaiNop('bai.pdf')).toBe('📕');
    expect(nhanBaiNop('bai.pdf')).toBe('PDF');
  });
});

describe('moTaDinhDang', () => {
  it('một loại duy nhất → dùng đúng icon/nhãn của loại đó', () => {
    expect(moTaDinhDang('pdf')).toEqual({ icon: '📕', nhan: 'PDF' });
    expect(moTaDinhDang('doc,docx')).toEqual({ icon: '📘', nhan: 'Word' });
    expect(moTaDinhDang('mp4,mov,webm')).toEqual({ icon: '🎬', nhan: 'video' });
  });

  it('trộn PDF + Word → gọi chung là tài liệu', () => {
    expect(moTaDinhDang('pdf,doc,docx')).toEqual({ icon: '📄', nhan: 'tài liệu' });
  });

  it('trộn văn bản với video → nhãn chung chung', () => {
    expect(moTaDinhDang('pdf,doc,docx,mp4,mov,webm')).toEqual({ icon: '📎', nhan: 'file bài làm' });
  });

  it('chấp nhận CSV có dấu chấm, khoảng trắng, chữ hoa', () => {
    expect(moTaDinhDang(' .PDF , pdf ')).toEqual({ icon: '📕', nhan: 'PDF' });
  });

  it('rỗng hoặc null → mặc định file', () => {
    expect(moTaDinhDang('')).toEqual({ icon: '📎', nhan: 'file' });
    expect(moTaDinhDang(null)).toEqual({ icon: '📎', nhan: 'file' });
  });
});
