/**
 * SuaThanhPhanModal — modal sửa thành phần cuộc họp.
 *
 * G4-fix-6.1 (01/05/2026):
 * - Load thành phần hiện tại
 * - Cho phép thêm/bớt qua CongChucCheckboxList (theo đơn vị) + CongChucPicker (cross-unit)
 * - Submit gọi PUT /cuoc-hop/{id}/thanh-phan (BE tự diff + notify)
 * - Block bỏ chu_toa/thu_ky (BE 409 nếu cố)
 *
 * G4-fix-7 (03/05/2026):
 * - BE list /thanh-phan trả kèm ho_ten/ma_cc/đơn vị → tách:
 *   • inDonViIds (cùng đơn vị tổ chức)
 *   • outsideEntries (đơn vị khác, hydrated)
 * - Dùng CrossUnitPicker (dropdown đơn vị + search + checkbox) cho phần ngoài
 *   đơn vị → không còn hiện UUID.
 */

'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';
import { Loader2, Save, UsersRound, X } from 'lucide-react';
import { cuocHopApi, nhomThanhPhanApi, type ICongChucSearchItem } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import type { ICuocHop } from '@/types/hkg';
import CongChucCheckboxList from './CongChucCheckboxList';
import CrossUnitPicker from './CrossUnitPicker';
import ChonNhomModal from './ChonNhomModal';

const LMS_API = process.env.NEXT_PUBLIC_LMS_API_URL || '/api/v1/lms';

interface IDonVi {
  id: string;
  ma_don_vi: string;
  ten_don_vi: string;
}

interface IProps {
  ch: ICuocHop;
  onClose: () => void;
  onSaved: () => void;
}

export default function SuaThanhPhanModal({ ch, onClose, onSaved }: IProps) {
  const [inDonViIds, setInDonViIds] = useState<string[]>([]);
  const [outsideEntries, setOutsideEntries] = useState<ICongChucSearchItem[]>([]);
  const [donViList, setDonViList] = useState<IDonVi[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showNhomPicker, setShowNhomPicker] = useState(false);
  const [mergingNhom, setMergingNhom] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  // Load donViList song song để CrossUnitPicker có dropdown
  useEffect(() => {
    const load = async () => {
      try {
        const token =
          typeof window !== 'undefined' ? localStorage.getItem('kpi_access_token') : null;
        const resp = await axios.get(`${LMS_API}/don-vi`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        setDonViList(resp.data?.data || []);
      } catch {
        // Silent — picker vẫn hoạt động (chỉ không có dropdown lựa chọn)
      }
    };
    load();
  }, []);

  // Load list thành phần hiện tại + tách theo đơn vị
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const list = await cuocHopApi.listThanhPhan(ch.id);
        const inHome: string[] = [];
        const outside: ICongChucSearchItem[] = [];
        for (const tp of list) {
          if (tp.don_vi_id === ch.don_vi_to_chuc_id) {
            inHome.push(tp.cong_chuc_id);
          } else {
            outside.push({
              id: tp.cong_chuc_id,
              ho_ten: tp.ho_ten || '(Không rõ tên)',
              ma_cc: tp.ma_cc || '',
              email: null,
              chuc_vu: tp.chuc_vu || null,
              don_vi_id: tp.don_vi_id || null,
              ten_don_vi: tp.ten_don_vi || null,
              ma_vai_tro: null,
              is_lanh_dao: false,
            });
          }
        }
        setInDonViIds(inHome);
        setOutsideEntries(outside);
      } catch (e: unknown) {
        setError(errMsg(e, 'Lỗi tải thành phần'));
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [ch.id, ch.don_vi_to_chuc_id, reloadKey]);

  const handleMergeNhom = async (nhomIds: string[]) => {
    setMergingNhom(true);
    try {
      const result = await nhomThanhPhanApi.themTuNhomVaoCuocHop(ch.id, nhomIds);
      setShowNhomPicker(false);
      // Reload thanh-phan list để hiển thị thành viên mới
      setReloadKey((k) => k + 1);
      const messages: string[] = [`Đã thêm ${result.so_them} thành viên`];
      if (result.so_bo_qua_trung > 0) {
        messages.push(`Bỏ qua ${result.so_bo_qua_trung} người đã có sẵn`);
      }
      if (result.thu_ky_auto_filled) {
        messages.push('Tự động điền Thư ký từ nhóm');
      }
      alert(messages.join('. '));
    } catch (e: unknown) {
      alert(errMsg(e, 'Thêm từ nhóm thất bại'));
    } finally {
      setMergingNhom(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      // Gộp ID + đảm bảo chu_toa/thu_ky luôn còn (BE block 409 nếu thiếu)
      const ids = new Set<string>(inDonViIds);
      outsideEntries.forEach((e) => ids.add(e.id));
      ids.add(ch.chu_toa_id);
      if (ch.thu_ky_id) ids.add(ch.thu_ky_id);

      const result = await cuocHopApi.suaThanhPhan(
        ch.id,
        Array.from(ids).map((cong_chuc_id) => ({
          cong_chuc_id,
          loai_tham_du: 'BAT_BUOC',
        })),
      );
      onSaved();
      onClose();
      // Toast handled by caller via onSaved
      console.log('Đã lưu', result);
    } catch (e: unknown) {
      setError(errMsg(e, 'Lỗi lưu thành phần'));
    } finally {
      setSaving(false);
    }
  };

  const totalCount = (() => {
    const s = new Set<string>(inDonViIds);
    outsideEntries.forEach((e) => s.add(e.id));
    s.add(ch.chu_toa_id);
    if (ch.thu_ky_id) s.add(ch.thu_ky_id);
    return s.size;
  })();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] flex flex-col">
        <div className="flex justify-between items-center p-4 border-b">
          <h3 className="text-lg font-semibold">Sửa thành phần tham dự</h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {loading ? (
            <div className="flex items-center gap-2 text-gray-500">
              <Loader2 className="w-4 h-4 animate-spin" /> Đang tải...
            </div>
          ) : (
            <>
              <div className="text-xs text-gray-600 bg-blue-50 border border-blue-200 rounded p-2">
                💡 Chủ tọa và thư ký được tự động giữ trong danh sách. Người được
                <strong> thêm mới</strong> sẽ nhận giấy mời (nếu cuộc họp đã thông báo).
              </div>

              <div>
                <button
                  type="button"
                  onClick={() => setShowNhomPicker(true)}
                  className="inline-flex items-center gap-2 px-3 py-2 text-sm border border-blue-300 text-blue-700 bg-white rounded hover:bg-blue-50"
                >
                  <UsersRound className="w-4 h-4" />
                  Thêm từ nhóm
                </button>
                <span className="text-xs text-gray-500 ml-2">
                  Gộp thành viên từ 1+ nhóm có sẵn (tự bỏ qua người đã có).
                </span>
              </div>

              <CongChucCheckboxList
                donViId={ch.don_vi_to_chuc_id}
                value={inDonViIds}
                onChange={setInDonViIds}
                chuToaId={ch.chu_toa_id}
                thuKyId={ch.thu_ky_id}
              />

              <div>
                <p className="text-xs font-medium text-gray-700 mb-1">
                  Thêm CBCC từ đơn vị khác
                </p>
                <CrossUnitPicker
                  donViList={donViList}
                  excludeDonViId={ch.don_vi_to_chuc_id}
                  entries={outsideEntries}
                  onChange={setOutsideEntries}
                />
              </div>

              <p className="text-xs text-gray-500">Tổng: {totalCount} CBCC</p>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
                  {error}
                </div>
              )}
            </>
          )}
        </div>

        <div className="flex justify-end gap-2 p-4 border-t">
          <button
            onClick={onClose}
            disabled={saving}
            className="px-4 py-2 border rounded text-sm"
          >
            Hủy
          </button>
          <button
            onClick={handleSave}
            disabled={saving || loading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Lưu thay đổi
          </button>
        </div>
      </div>

      {showNhomPicker && (
        <ChonNhomModal
          title="Thêm thành viên từ nhóm có sẵn"
          confirmLabel="Thêm vào cuộc họp"
          busy={mergingNhom}
          onConfirm={handleMergeNhom}
          onClose={() => setShowNhomPicker(false)}
        />
      )}
    </div>
  );
}
