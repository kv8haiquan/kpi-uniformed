/**
 * src/app/(main)/phap-luat/[id]/page.tsx
 * =========================================
 * Chi tiết văn bản pháp luật.
 *
 * Gồm:
 *   - Header: số hiệu, trích yếu, badges hiệu lực + mức độ
 *   - Thông tin meta: cơ quan, ngày ban hành, ngày hiệu lực
 *   - Nút xác nhận đọc (XacNhanButton)
 *   - Tabs: Nội dung | Điểm mới | VB liên quan | Quiz
 *   - Reading Tracker: tự động gửi thời gian đọc mỗi 30s
 *
 * Side effect của API: GET /van-ban/{id} tự động mark da_doc=TRUE.
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { legalService } from '@/services/legal';
import { useReadingTracker } from '@/components/legal/ReadingTracker';
import { XacNhanButton } from '@/components/legal/XacNhanButton';
import { QuizForm } from '@/components/legal/QuizForm';
import { PdfViewer } from '@/components/legal/PdfViewer';
import type { IVanBanDetail, IQuizVanBan } from '@/types/legal';

// =============================================================================
// HELPERS
// =============================================================================

function MucDoBadge({ mucDo }: { mucDo: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    RAT_KHAN:    { label: '🔴 Rất khẩn',   cls: 'bg-red-100 text-red-700 border-red-300' },
    KHAN:        { label: '🟠 Khẩn',        cls: 'bg-orange-100 text-orange-700 border-orange-300' },
    QUAN_TRONG:  { label: '🟡 Quan trọng',  cls: 'bg-yellow-100 text-yellow-700 border-yellow-300' },
    BINH_THUONG: { label: 'Bình thường',    cls: 'bg-gray-100 text-gray-500 border-gray-200' },
  };
  const info = map[mucDo] ?? { label: mucDo, cls: 'bg-gray-100 text-gray-500 border-gray-200' };
  return (
    <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${info.cls}`}>
      {info.label}
    </span>
  );
}

function HieuLucBadge({ trangThai }: { trangThai: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    CON_HIEU_LUC:  { label: '✅ Còn hiệu lực',  cls: 'bg-green-100 text-green-700 border-green-200' },
    HET_HIEU_LUC:  { label: '⛔ Hết hiệu lực',  cls: 'bg-gray-100 text-gray-400 border-gray-200' },
    CHUA_HIEU_LUC: { label: '⏳ Chưa hiệu lực', cls: 'bg-blue-100 text-blue-600 border-blue-200' },
  };
  const info = map[trangThai] ?? { label: trangThai, cls: 'bg-gray-100 text-gray-400 border-gray-200' };
  return (
    <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${info.cls}`}>
      {info.label}
    </span>
  );
}

// =============================================================================
// MAIN PAGE
// =============================================================================
export default function VanBanDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [vb, setVb] = useState<IVanBanDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'noidung' | 'diemmoi' | 'lienket' | 'quiz'>('noidung');

  // Quiz state
  const [selectedQuiz, setSelectedQuiz] = useState<IQuizVanBan | null>(null);
  const [quizLoading, setQuizLoading] = useState(false);

  // Reading tracker — tự động gửi mỗi 30s
  useReadingTracker(id ?? '');

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      setLoading(true);
      try {
        const res = await legalService.getVanBanById(id);
        // Kiểm tra success field theo SHARED_CODING_STANDARDS §5.1
        if (res.data?.success) {
          setVb(res.data.data);
        } else {
          const msg = res.data?.error?.message || 'Không thể tải văn bản.';
          console.warn('[Legal] getVanBanById:', res.data?.error?.code, msg);
          setError(msg);
        }
      } catch (err: unknown) {
        const e = err as { response?: { status?: number } };
        if (e?.response?.status === 404) {
          setError('Không tìm thấy văn bản này.');
        } else {
          setError('Không thể tải văn bản. Vui lòng thử lại.');
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  const handleLamQuiz = async (quizId: string) => {
    if (!id) return;
    setQuizLoading(true);
    try {
      const res = await legalService.getQuiz(id);
      // Kiểm tra success field theo SHARED_CODING_STANDARDS §5.1
      if (res.data?.success) {
        const quizzes: IQuizVanBan[] = res.data.data ?? [];
        const found = quizzes.find(q => q.id === quizId);
        if (found) setSelectedQuiz(found);
      } else {
        console.warn('[Legal] getQuiz:', res.data?.error?.code, res.data?.error?.message);
      }
    } catch {
      // Nếu không load được quiz
    } finally {
      setQuizLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!id) return;
    try {
      const res = await legalService.downloadVanBan(id);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `${vb?.so_hieu ?? 'van-ban'}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      alert('Không thể tải file PDF');
    }
  };

  // Loading
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600 mx-auto mb-3" />
          <p className="text-gray-500 text-sm">Đang tải văn bản...</p>
        </div>
      </div>
    );
  }

  // Error
  if (error || !vb) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
        <div className="bg-white rounded-xl border border-red-200 p-8 text-center max-w-md">
          <span className="text-4xl block mb-3">⚠️</span>
          <p className="text-red-700 font-medium">{error || 'Không tìm thấy văn bản'}</p>
          <button
            onClick={() => router.push('/phap-luat')}
            className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 transition-colors"
          >
            ← Quay lại danh sách
          </button>
        </div>
      </div>
    );
  }

  const tabs = [
    { key: 'noidung', label: '📄 Nội dung' },
    { key: 'diemmoi', label: '✨ Điểm mới', hidden: !vb.diem_moi && !vb.viec_can_lam },
    { key: 'lienket', label: '🔗 VB liên quan', hidden: (vb.van_ban_lien_ket?.length ?? 0) === 0 },
    { key: 'quiz',    label: `📝 Quiz (${vb.quizzes?.length ?? 0})`, hidden: (vb.quizzes?.length ?? 0) === 0 },
  ].filter(t => !t.hidden);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-gray-500 mb-4">
          <Link href="/phap-luat" className="hover:text-purple-600 transition-colors">⚖️ Pháp luật</Link>
          <span>›</span>
          <span className="text-gray-800 font-medium truncate max-w-xs">{vb.so_hieu}</span>
        </nav>

        {/* Header card */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 mb-4">
          {/* Badges */}
          <div className="flex flex-wrap gap-2 mb-3">
            <MucDoBadge mucDo={vb.muc_do} />
            <HieuLucBadge trangThai={vb.trang_thai_hieu_luc} />
            {vb.bat_buoc_doc && (
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-blue-100 text-blue-700 border border-blue-200">
                📌 Bắt buộc đọc
              </span>
            )}
            {vb.co_diem_moi && (
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-orange-100 text-orange-700 border border-orange-200">
                ✨ Có điểm mới
              </span>
            )}
          </div>

          {/* Số hiệu + loại + phiên bản */}
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="font-mono text-sm text-purple-700 bg-purple-50 px-2 py-0.5 rounded">
              {vb.so_hieu}
            </span>
            <span className="text-sm text-gray-400">•</span>
            <span className="text-sm text-gray-500">{vb.loai_van_ban.ten}</span>
            {(vb.phien_ban ?? 1) > 1 && (
              <span className="text-xs font-medium px-2 py-0.5 bg-blue-50 text-blue-600 border border-blue-200 rounded-full">
                Phiên bản {vb.phien_ban}
              </span>
            )}
          </div>

          {/* Trích yếu */}
          <h1 className="text-xl font-bold text-gray-900 mb-4 leading-relaxed">
            {vb.trich_yeu}
          </h1>

          {/* Thông tin meta */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm py-3 border-t border-gray-100 mb-4">
            <div>
              <p className="text-xs text-gray-400 mb-0.5">Cơ quan ban hành</p>
              <p className="font-medium text-gray-800">{vb.co_quan_ban_hanh}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-0.5">Ngày ban hành</p>
              <p className="font-medium text-gray-800">
                {new Date(vb.ngay_ban_hanh).toLocaleDateString('vi-VN')}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-0.5">Ngày hiệu lực</p>
              <p className="font-medium text-gray-800">
                {new Date(vb.ngay_hieu_luc).toLocaleDateString('vi-VN')}
              </p>
            </div>
            {vb.han_xac_nhan && (
              <div>
                <p className="text-xs text-gray-400 mb-0.5">Hạn xác nhận</p>
                <p className="font-medium text-red-600">
                  {new Date(vb.han_xac_nhan).toLocaleDateString('vi-VN')}
                </p>
              </div>
            )}
          </div>

          {/* Nút xác nhận + Download */}
          <div className="flex flex-wrap items-center gap-3 pt-3 border-t border-gray-100">
            {vb.bat_buoc_doc && (
              <XacNhanButton
                vanBanId={id}
                daXacNhan={vb.xac_nhan?.da_xac_nhan ?? false}
                onSuccess={() => setVb(prev => prev
                  ? { ...prev, xac_nhan: {
                      da_doc: prev.xac_nhan?.da_doc ?? true,
                      ngay_doc: prev.xac_nhan?.ngay_doc ?? null,
                      da_xac_nhan: true,
                      ngay_xac_nhan: new Date().toISOString(),
                      thoi_gian_doc_giay: prev.xac_nhan?.thoi_gian_doc_giay ?? 0,
                    } }
                  : prev
                )}
              />
            )}
            {vb.file_goc_url && (
              <button
                onClick={handleDownload}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-xl text-sm hover:bg-gray-50 transition-colors"
              >
                <span>📥</span> Tải file PDF gốc
              </button>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          {/* Tab headers */}
          <div className="flex border-b border-gray-200 overflow-x-auto">
            {tabs.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as typeof activeTab)}
                className={`shrink-0 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.key
                    ? 'border-purple-600 text-purple-700 bg-purple-50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="p-5">

            {/* Tab: Nội dung */}
            {activeTab === 'noidung' && (
              <div>
                {vb.tom_tat && (
                  <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 mb-4">
                    <h3 className="text-sm font-semibold text-purple-800 mb-2">📋 Tóm tắt</h3>
                    <p className="text-sm text-gray-700 leading-relaxed">{vb.tom_tat}</p>
                  </div>
                )}

                {/* Nội dung HTML */}
                {vb.noi_dung_html && (
                  <div
                    className="prose prose-sm max-w-none text-gray-800 leading-relaxed mb-6"
                    dangerouslySetInnerHTML={{ __html: vb.noi_dung_html }}
                  />
                )}

                {/* PDF Viewer inline */}
                {vb.file_goc_url && (
                  <div className={vb.noi_dung_html ? 'border-t border-gray-200 pt-5' : ''}>
                    {vb.noi_dung_html && (
                      <h3 className="text-sm font-semibold text-gray-700 mb-3">📄 File văn bản gốc</h3>
                    )}
                    <PdfViewer
                      url={vb.file_goc_url}
                      filename={`${vb.so_hieu}.pdf`}
                    />
                  </div>
                )}

                {/* Trạng thái trống — không có cả HTML lẫn file */}
                {!vb.noi_dung_html && !vb.file_goc_url && (
                  <div className="text-center py-8 text-gray-400">
                    <span className="block text-4xl mb-2">📄</span>
                    <p>Chưa có nội dung. Vui lòng liên hệ người quản lý để cập nhật.</p>
                  </div>
                )}
              </div>
            )}

            {/* Tab: Điểm mới */}
            {activeTab === 'diemmoi' && (
              <div className="space-y-4">
                {vb.diem_moi && (
                  <div className="bg-orange-50 border-l-4 border-orange-400 rounded-r-xl p-5">
                    <h3 className="text-base font-bold text-orange-800 mb-3 flex items-center gap-2">
                      <span>📌</span> ĐIỂM MỚI
                    </h3>
                    <div className="text-sm text-gray-800 leading-relaxed whitespace-pre-line">
                      {vb.diem_moi}
                    </div>
                  </div>
                )}
                {vb.viec_can_lam && (
                  <div className="bg-green-50 border-l-4 border-green-400 rounded-r-xl p-5">
                    <h3 className="text-base font-bold text-green-800 mb-3 flex items-center gap-2">
                      <span>✅</span> VIỆC CẦN LÀM
                    </h3>
                    <div className="text-sm text-gray-800 leading-relaxed whitespace-pre-line">
                      {vb.viec_can_lam}
                    </div>
                  </div>
                )}
                {!vb.diem_moi && !vb.viec_can_lam && (
                  <div className="text-center py-8 text-gray-400">Chưa có điểm mới</div>
                )}
              </div>
            )}

            {/* Tab: VB liên quan */}
            {activeTab === 'lienket' && (
              <div>
                {(vb.van_ban_lien_ket?.length ?? 0) === 0 ? (
                  <div className="text-center py-8 text-gray-400">Không có văn bản liên quan</div>
                ) : (
                  <div className="space-y-3">
                    {vb.van_ban_lien_ket?.map(lk => {
                      const loaiLabel: Record<string, string> = {
                        THAY_THE: '🔄 Thay thế',
                        BO_SUNG: '➕ Bổ sung',
                        HUONG_DAN: '📖 Hướng dẫn',
                        LIEN_QUAN: '🔗 Liên quan',
                      };
                      return (
                        <Link
                          key={lk.id}
                          href={`/phap-luat/${lk.id}`}
                          className="flex items-start gap-3 p-4 bg-gray-50 rounded-xl border border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition-colors"
                        >
                          <span className="text-xs font-semibold px-2 py-1 bg-purple-100 text-purple-700 rounded shrink-0 mt-0.5">
                            {loaiLabel[lk.loai_lien_ket] ?? lk.loai_lien_ket}
                          </span>
                          <div>
                            <p className="text-sm font-medium text-purple-700">{lk.so_hieu}</p>
                            <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{lk.trich_yeu}</p>
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {/* Tab: Quiz */}
            {activeTab === 'quiz' && (
              <div>
                {selectedQuiz ? (
                  <div>
                    <button
                      onClick={() => setSelectedQuiz(null)}
                      className="text-sm text-gray-500 hover:text-purple-600 mb-4 flex items-center gap-1 transition-colors"
                    >
                      ← Quay lại danh sách quiz
                    </button>
                    <QuizForm quiz={selectedQuiz} onClose={() => setSelectedQuiz(null)} />
                  </div>
                ) : (
                  <div>
                    {(vb.quizzes?.length ?? 0) === 0 ? (
                      <div className="text-center py-8 text-gray-400">
                        <span className="block text-4xl mb-2">📝</span>
                        <p>Chưa có quiz cho văn bản này</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {vb.quizzes?.map(q => (
                          <div
                            key={q.id}
                            className="flex items-center justify-between p-4 bg-purple-50 border border-purple-200 rounded-xl"
                          >
                            <div>
                              <p className="font-medium text-gray-900">{q.tieu_de}</p>
                              <p className="text-xs text-gray-500 mt-1">{q.so_cau_hoi} câu hỏi</p>
                            </div>
                            <button
                              onClick={() => handleLamQuiz(q.id)}
                              disabled={quizLoading}
                              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
                            >
                              {quizLoading ? '...' : 'Làm bài →'}
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

          </div>
        </div>

        {/* Tags */}
        {(vb.tags?.length ?? 0) > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {vb.tags?.map((tag, i) => (
              <span key={i} className="text-xs bg-purple-50 text-purple-600 border border-purple-200 px-2 py-1 rounded-full">
                #{tag}
              </span>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
