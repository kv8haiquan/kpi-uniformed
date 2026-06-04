/**
 * src/components/lms/KetQuaKhoaHocPanel.tsx
 * ==========================================
 * Panel kết quả thi của MỘT khóa học cụ thể (đã fix khoaHocId).
 * Dùng trong:
 *   - Tab "Kết quả" của trang chi tiết khóa học (/dao-tao/khoa-hoc/[id])
 *   - Sub-tab "Theo khóa học" của KetQuaBaoCaoPanel (sau khi user chọn khóa từ dropdown)
 *
 * Props:
 *   - khoaHocId: id khóa học đã chọn
 *
 * Chức năng:
 *   - Hiển thị summary của khóa (tổng học viên, hoàn thành, ...)
 *   - Chọn BKT → xem KQ tất cả học viên
 *   - Chấm bài thực hành (modal)
 *   - Xem chi tiết bài trắc nghiệm (modal)
 */

'use client';

import { useEffect, useState } from 'react';
import { baoCaoApi, baiKiemTraApi } from '@/services/lms';

interface Props {
  khoaHocId: string;
}

export default function KetQuaKhoaHocPanel({ khoaHocId }: Props) {
  const [selBktId, setSelBktId] = useState('');
  const [bktList, setBktList] = useState<any[]>([]);
  const [ketQuaList, setKetQuaList] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [bcKH, setBcKH] = useState<any>(null);

  // Cham bai thuc hanh — state modal
  const [chamModal, setChamModal] = useState<any | null>(null);
  const [chamDiem, setChamDiem] = useState<string>('');
  const [chamNhanXet, setChamNhanXet] = useState<string>('');
  const [chamLoading, setChamLoading] = useState(false);

  // Xem chi tiet bai trac nghiem — state modal
  const [chiTietModal, setChiTietModal] = useState<any | null>(null);
  const [chiTietData, setChiTietData] = useState<any | null>(null);
  const [chiTietLoading, setChiTietLoading] = useState(false);
  const [chiTietErr, setChiTietErr] = useState<string>('');

  const selectedBkt = bktList.find((b) => b.id === selBktId);
  const laThucHanh = selectedBkt?.loai_bai_kiem_tra === 'THUC_HANH';

  // Load BKT + báo cáo khóa khi khoaHocId đổi
  useEffect(() => {
    if (!khoaHocId) return;
    setSelBktId('');
    setKetQuaList([]);
    baiKiemTraApi
      .danhSach(khoaHocId)
      .then((r) => setBktList(r.data.data || []))
      .catch(() => setBktList([]));
    baoCaoApi
      .khoaHoc(khoaHocId)
      .then((r) => setBcKH(r.data.data ?? r.data))
      .catch(() => setBcKH(null));
  }, [khoaHocId]);

  const loadKetQua = async () => {
    if (!selBktId) return;
    setLoading(true);
    try {
      const r = await baiKiemTraApi.ketQuaTatCa(selBktId);
      setKetQuaList(r.data.data || []);
    } catch {
      setKetQuaList([]);
    } finally {
      setLoading(false);
    }
  };

  const openChamModal = (kq: any) => {
    setChamModal(kq);
    setChamDiem(kq.diem != null ? String(kq.diem) : '');
    setChamNhanXet(kq.nhan_xet || '');
  };

  const openChiTietModal = async (kq: any) => {
    setChiTietModal(kq);
    setChiTietData(null);
    setChiTietErr('');
    setChiTietLoading(true);
    try {
      const r = await baiKiemTraApi.ketQua(kq.id);
      setChiTietData(r.data.data ?? r.data);
    } catch (err: any) {
      setChiTietErr(err?.response?.data?.detail?.error?.message || 'Không thể tải chi tiết bài làm');
    } finally {
      setChiTietLoading(false);
    }
  };

  const handleSaveCham = async () => {
    if (!chamModal) return;
    const diemNum = Number(chamDiem);
    if (Number.isNaN(diemNum) || diemNum < 0 || diemNum > 100) {
      alert('Điểm phải trong khoảng 0 - 100');
      return;
    }
    setChamLoading(true);
    try {
      await baiKiemTraApi.chamTay(chamModal.id, {
        diem: diemNum,
        nhan_xet: chamNhanXet.trim() || undefined,
      });
      setChamModal(null);
      await loadKetQua();
    } catch (err: any) {
      alert(err?.response?.data?.detail?.error?.message || 'Lỗi lưu chấm bài');
    } finally {
      setChamLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Bộ lọc: chọn BKT + nút Xem (đã fix khóa) */}
      <div className="flex flex-wrap gap-3">
        <select
          value={selBktId}
          onChange={(e) => setSelBktId(e.target.value)}
          className="flex-1 min-w-[200px] px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
          disabled={!khoaHocId || bktList.length === 0}
        >
          <option value="">-- Chọn bài kiểm tra --</option>
          {bktList.map((bkt) => (
            <option key={bkt.id} value={bkt.id}>
              {bkt.tieu_de} ({bkt.so_cau_hoi} câu)
            </option>
          ))}
        </select>
        <button
          onClick={loadKetQua}
          disabled={!selBktId || loading}
          className="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-blue-700"
        >
          {loading ? 'Đang tải...' : 'Xem kết quả'}
        </button>
      </div>

      {bktList.length === 0 && (
        <div className="text-center py-6 bg-gray-50 rounded-lg text-gray-500 text-sm">
          Khóa học này chưa có bài kiểm tra nào
        </div>
      )}

      {/* Course summary cards */}
      {bcKH && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white border rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-gray-900">
              {bcKH.tong_hoc_vien ?? bcKH.so_hoc_vien ?? 0}
            </div>
            <div className="text-xs text-gray-500">Tổng học viên</div>
          </div>
          <div className="bg-white border rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{bcKH.dang_hoc ?? 0}</div>
            <div className="text-xs text-gray-500">Đang học</div>
          </div>
          <div className="bg-white border rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{bcKH.hoan_thanh ?? 0}</div>
            <div className="text-xs text-gray-500">Hoàn thành</div>
          </div>
          <div className="bg-white border rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">
              {bcKH.ty_le_hoan_thanh != null ? `${bcKH.ty_le_hoan_thanh}%` : '—'}
            </div>
            <div className="text-xs text-gray-500">Tỷ lệ HT</div>
          </div>
        </div>
      )}

      {/* Results table */}
      {ketQuaList.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b bg-gray-50 flex items-center justify-between gap-2 flex-wrap">
            <h4 className="font-medium text-sm text-gray-700">
              Kết quả {laThucHanh ? 'nộp bài thực hành' : 'thi'} ({ketQuaList.length} lượt)
            </h4>
            <div className="flex items-center gap-2">
              {laThucHanh && ketQuaList.some((kq) => kq.trang_thai_cham === 'CHO_CHAM') && (
                <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full text-xs font-medium">
                  ⏳ {ketQuaList.filter((kq) => kq.trang_thai_cham === 'CHO_CHAM').length} bài chờ chấm
                </span>
              )}
              {!laThucHanh && ketQuaList.some((kq) => (kq.so_lan_vi_pham || 0) > 0) && (
                <span
                  className="px-2 py-1 bg-amber-50 text-amber-700 rounded-full text-xs font-medium"
                  title="Dấu hiệu tham khảo (số lần thoát toàn màn hình / chuyển tab) — không có ý nghĩa kỷ luật."
                >
                  🔍 {ketQuaList.filter((kq) => (kq.so_lan_vi_pham || 0) > 0).length} bài có dấu hiệu tham khảo
                </span>
              )}
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Họ tên</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Mã CC</th>
                  <th className="px-4 py-3 text-center font-medium text-gray-500">Lần</th>
                  <th className="px-4 py-3 text-center font-medium text-gray-500">Điểm</th>
                  <th className="px-4 py-3 text-center font-medium text-gray-500">
                    {laThucHanh ? 'Trạng thái' : 'Kết quả'}
                  </th>
                  {laThucHanh ? (
                    <th className="px-4 py-3 text-center font-medium text-gray-500">Bài nộp</th>
                  ) : (
                    <th
                      className="px-4 py-3 text-center font-medium text-gray-500"
                      title="Số lần thoát toàn màn hình / chuyển tab trong khi làm bài — chỉ mang tính tham khảo, không có ý nghĩa kỷ luật."
                    >
                      Tham khảo
                    </th>
                  )}
                  <th className="px-4 py-3 text-left font-medium text-gray-500">
                    {laThucHanh ? 'Ngày nộp' : 'Ngày thi'}
                  </th>
                  {laThucHanh ? (
                    <th className="px-4 py-3 text-center font-medium text-gray-500">Chấm</th>
                  ) : (
                    <th className="px-4 py-3 text-center font-medium text-gray-500">Chi tiết</th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {ketQuaList.map((kq, i) => {
                  const hasViolation = (kq.so_lan_vi_pham || 0) > 0;
                  const daCham = kq.trang_thai_cham === 'DA_CHAM';
                  const choCham = kq.trang_thai_cham === 'CHO_CHAM';
                  return (
                    <tr
                      key={i}
                      className={`hover:bg-gray-50 ${choCham ? 'bg-yellow-50' : ''}`}
                    >
                      <td className="px-4 py-3 font-medium text-gray-900">{kq.ho_ten || '—'}</td>
                      <td className="px-4 py-3 text-gray-600">{kq.ma_cc || '—'}</td>
                      <td className="px-4 py-3 text-center">{kq.lan_thu}</td>
                      <td className="px-4 py-3 text-center font-semibold">{kq.diem ?? '—'}</td>
                      <td className="px-4 py-3 text-center">
                        {laThucHanh ? (
                          daCham ? (
                            <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs">
                              Đã chấm
                            </span>
                          ) : choCham ? (
                            <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full text-xs">
                              Chờ chấm
                            </span>
                          ) : (
                            <span className="text-gray-400 text-xs">—</span>
                          )
                        ) : (
                          <>
                            {kq.dat_yeu_cau === true && (
                              <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs">
                                Đạt
                              </span>
                            )}
                            {kq.dat_yeu_cau === false && (
                              <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs">
                                Chưa đạt
                              </span>
                            )}
                            {kq.dat_yeu_cau == null && (
                              <span className="text-gray-400 text-xs">Đang thi</span>
                            )}
                          </>
                        )}
                      </td>
                      {laThucHanh ? (
                        <td className="px-4 py-3 text-center">
                          {kq.bai_nop_url ? (
                            <a
                              href={kq.bai_nop_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-blue-600 hover:underline text-xs"
                              title={kq.bai_nop_ten_file || ''}
                            >
                              🎬 Xem video
                            </a>
                          ) : (
                            <span className="text-gray-400 text-xs">—</span>
                          )}
                        </td>
                      ) : (
                        <td className="px-4 py-3 text-center">
                          {hasViolation ? (
                            <span
                              className="px-2 py-0.5 bg-amber-50 text-amber-700 rounded-full text-xs font-medium"
                              title="Số lần thoát toàn màn hình / chuyển tab — chỉ tham khảo, không có ý nghĩa kỷ luật."
                            >
                              🔍 {kq.so_lan_vi_pham}
                            </span>
                          ) : (
                            <span className="text-gray-400 text-xs">—</span>
                          )}
                        </td>
                      )}
                      <td className="px-4 py-3 text-gray-500 text-xs">
                        {laThucHanh
                          ? kq.ngay_nop
                            ? new Date(kq.ngay_nop).toLocaleString('vi-VN')
                            : '—'
                          : kq.ngay_lam
                          ? new Date(kq.ngay_lam).toLocaleString('vi-VN')
                          : '—'}
                      </td>
                      {laThucHanh ? (
                        <td className="px-4 py-3 text-center">
                          {kq.bai_nop_url ? (
                            <button
                              onClick={() => openChamModal(kq)}
                              className={`px-2 py-1 rounded text-xs font-medium ${
                                daCham
                                  ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                  : 'bg-orange-600 text-white hover:bg-orange-700'
                              }`}
                            >
                              {daCham ? '✏️ Sửa' : '📝 Chấm'}
                            </button>
                          ) : (
                            <span className="text-gray-400 text-xs">Chưa nộp</span>
                          )}
                        </td>
                      ) : (
                        <td className="px-4 py-3 text-center">
                          {kq.dat_yeu_cau != null ? (
                            <button
                              onClick={() => openChiTietModal(kq)}
                              className="px-2 py-1 rounded text-xs font-medium bg-blue-600 text-white hover:bg-blue-700"
                            >
                              👁 Xem bài
                            </button>
                          ) : (
                            <span className="text-gray-400 text-xs">Đang thi</span>
                          )}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty state */}
      {selBktId && !loading && ketQuaList.length === 0 && (
        <div className="text-center py-10 bg-gray-50 rounded-lg text-gray-500 text-sm">
          Chưa có kết quả thi nào cho bài kiểm tra này
        </div>
      )}

      {/* Modal xem chi tiết bài trắc nghiệm */}
      {chiTietModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setChiTietModal(null)}
          />
          <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col">
            <div className="px-6 py-4 border-b flex items-center justify-between shrink-0">
              <div>
                <h3 className="font-semibold text-gray-900">Chi tiết bài làm</h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  {chiTietModal.ho_ten} · {chiTietModal.ma_cc} · Lần {chiTietModal.lan_thu}
                </p>
              </div>
              <button
                onClick={() => setChiTietModal(null)}
                className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
              >
                ×
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {chiTietLoading && (
                <div className="text-center py-10 text-sm text-gray-500">Đang tải chi tiết...</div>
              )}

              {chiTietErr && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                  {chiTietErr}
                </div>
              )}

              {chiTietData && (
                <>
                  <div className="grid grid-cols-4 gap-3">
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <div className="text-xl font-bold text-gray-900">
                        {chiTietData.diem ?? '—'}
                      </div>
                      <div className="text-xs text-gray-500">Điểm</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <div className="text-xl font-bold text-green-600">
                        {chiTietData.so_cau_dung ?? 0}
                      </div>
                      <div className="text-xs text-gray-500">Câu đúng</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <div className="text-xl font-bold text-red-600">
                        {chiTietData.so_cau_sai ?? 0}
                      </div>
                      <div className="text-xs text-gray-500">Câu sai</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <div
                        className={`text-sm font-bold ${
                          chiTietData.dat_yeu_cau ? 'text-green-700' : 'text-red-700'
                        }`}
                      >
                        {chiTietData.dat_yeu_cau ? 'ĐẠT' : 'CHƯA ĐẠT'}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">Kết quả</div>
                    </div>
                  </div>

                  {Array.isArray(chiTietData.chi_tiet) && chiTietData.chi_tiet.length > 0 ? (
                    <div className="space-y-3">
                      {chiTietData.chi_tiet.map((ct: any, i: number) => {
                        const isCorrect = ct.dung === true;
                        const isWrong = ct.dung === false;
                        return (
                          <div
                            key={i}
                            className={`rounded-lg border p-4 ${
                              isCorrect
                                ? 'bg-green-50 border-green-200'
                                : isWrong
                                ? 'bg-red-50 border-red-200'
                                : 'bg-yellow-50 border-yellow-200'
                            }`}
                          >
                            <div className="flex items-start gap-2 mb-2">
                              <span className="text-lg shrink-0">
                                {isCorrect ? '✅' : isWrong ? '❌' : '⏳'}
                              </span>
                              <div className="flex-1 min-w-0">
                                <span className="text-xs font-medium text-gray-500">
                                  Câu {i + 1}
                                </span>
                                {ct.noi_dung && (
                                  <p className="text-sm text-gray-900 mt-0.5 whitespace-pre-wrap">
                                    {ct.noi_dung}
                                  </p>
                                )}
                              </div>
                              <span
                                className={`text-sm font-bold shrink-0 ${
                                  isCorrect
                                    ? 'text-green-700'
                                    : isWrong
                                    ? 'text-red-700'
                                    : 'text-yellow-700'
                                }`}
                              >
                                {ct.diem_dat}/{ct.diem_toi_da}đ
                              </span>
                            </div>

                            {ct.tra_loi !== undefined && ct.tra_loi !== null && (
                              <div
                                className={`mt-2 px-3 py-1.5 rounded text-xs ${
                                  isCorrect
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-red-100 text-red-800'
                                }`}
                              >
                                <span className="font-medium">Học viên chọn:</span>{' '}
                                {Array.isArray(ct.tra_loi)
                                  ? ct.tra_loi.join(', ')
                                  : typeof ct.tra_loi === 'boolean'
                                  ? ct.tra_loi
                                    ? 'Đúng'
                                    : 'Sai'
                                  : String(ct.tra_loi)}
                              </div>
                            )}

                            {(ct.tra_loi === undefined ||
                              ct.tra_loi === null ||
                              ct.tra_loi === '') && (
                              <div className="mt-2 px-3 py-1.5 rounded text-xs bg-gray-100 text-gray-600 italic">
                                Học viên không trả lời câu này
                              </div>
                            )}

                            {ct.dap_an_dung !== undefined &&
                              ct.dap_an_dung !== null &&
                              !isCorrect && (
                                <div className="mt-1.5 px-3 py-1.5 rounded text-xs bg-green-100 text-green-800">
                                  <span className="font-medium">Đáp án đúng:</span>{' '}
                                  {Array.isArray(ct.dap_an_dung)
                                    ? ct.dap_an_dung.join(', ')
                                    : typeof ct.dap_an_dung === 'boolean'
                                    ? ct.dap_an_dung
                                      ? 'Đúng'
                                      : 'Sai'
                                    : String(ct.dap_an_dung)}
                                </div>
                              )}

                            {ct.giai_thich && (
                              <div className="mt-2 px-3 py-2 bg-blue-50 border border-blue-100 rounded text-xs text-blue-800">
                                <span className="font-medium">Giải thích:</span> {ct.giai_thich}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-sm text-gray-500 bg-gray-50 rounded-lg">
                      Bài làm này không có dữ liệu chi tiết từng câu.
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="px-6 py-4 border-t flex justify-end shrink-0">
              <button
                onClick={() => setChiTietModal(null)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal chấm bài thực hành */}
      {chamModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => !chamLoading && setChamModal(null)}
          />
          <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col">
            <div className="px-6 py-4 border-b flex items-center justify-between shrink-0">
              <div>
                <h3 className="font-semibold text-gray-900">Chấm bài thực hành</h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  {chamModal.ho_ten} · {chamModal.ma_cc} · Lần {chamModal.lan_thu}
                </p>
              </div>
              <button
                onClick={() => !chamLoading && setChamModal(null)}
                className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
              >
                ×
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {chamModal.bai_nop_url && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Video bài làm
                  </label>
                  <div className="bg-black rounded-lg overflow-hidden">
                    <video
                      src={chamModal.bai_nop_url}
                      controls
                      className="w-full max-h-[50vh]"
                      preload="metadata"
                    >
                      Trình duyệt không hỗ trợ phát video.
                    </video>
                  </div>
                  <div className="mt-1 flex items-center gap-3 text-xs text-gray-500">
                    {chamModal.bai_nop_ten_file && <span>📄 {chamModal.bai_nop_ten_file}</span>}
                    {chamModal.bai_nop_size_bytes && (
                      <span>{(chamModal.bai_nop_size_bytes / (1024 * 1024)).toFixed(2)} MB</span>
                    )}
                    {chamModal.bai_nop_url && (
                      <a
                        href={chamModal.bai_nop_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-blue-600 hover:underline ml-auto"
                      >
                        Mở tab mới ↗
                      </a>
                    )}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Điểm (0-100) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    step={0.5}
                    value={chamDiem}
                    onChange={(e) => setChamDiem(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nhận xét</label>
                <textarea
                  rows={4}
                  value={chamNhanXet}
                  onChange={(e) => setChamNhanXet(e.target.value)}
                  placeholder="Phản hồi cho học viên về bài làm..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-y"
                />
              </div>

              {chamModal.trang_thai_cham === 'DA_CHAM' && (
                <p className="text-xs text-gray-500">
                  Bài này đã được chấm. Lưu sẽ cập nhật điểm và nhận xét mới.
                </p>
              )}
            </div>

            <div className="px-6 py-4 border-t flex justify-end gap-3 shrink-0">
              <button
                onClick={() => setChamModal(null)}
                disabled={chamLoading}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50"
              >
                Hủy
              </button>
              <button
                onClick={handleSaveCham}
                disabled={chamLoading || !chamDiem}
                className="px-4 py-2 bg-orange-600 text-white rounded-lg text-sm font-medium hover:bg-orange-700 disabled:opacity-50"
              >
                {chamLoading ? 'Đang lưu...' : 'Lưu chấm bài'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
