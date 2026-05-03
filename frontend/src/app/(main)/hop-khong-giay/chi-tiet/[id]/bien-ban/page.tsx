/**
 * Tab Biên bản — TipTap rich-text editor + sign flow + xuất DOCX/PDF.
 *
 * G4-fix (01/05/2026): thay textarea plain bằng TipTap editor.
 * Editor produces TipTap JSON → lưu vào noi_dung_json + cache HTML vào noi_dung_html.
 * Auto-save debounce 30s khi editor thay đổi.
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams } from 'next/navigation';
import { Save, Send, FileSignature, FileDown, Loader2 } from 'lucide-react';
import { bienBanApi } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import type { IBienBan } from '@/types/hkg';
import TipTapEditor from '@/components/editor/TipTapEditor';
import { useMeeting } from '@/components/hkg/MeetingContext';

const AUTO_SAVE_DEBOUNCE_MS = 30_000;

export default function BienBanTabPage() {
  const { id } = useParams<{ id: string }>();
  const { isLocked: meetingLocked, canEdit } = useMeeting();
  const [bb, setBb] = useState<IBienBan | null>(null);
  // Editor state độc lập — TipTap dùng JSON (không phải string nữa)
  const [editorJson, setEditorJson] = useState<Record<string, unknown> | null>(null);
  const [editorHtml, setEditorHtml] = useState<string>('');
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);
  const autoSaveTimer = useRef<NodeJS.Timeout | null>(null);
  const dirtyRef = useRef(false);

  const fetchBienBan = useCallback(async () => {
    try {
      const data = await bienBanApi.get(id);
      setBb(data);
      // TipTap content có thể là JSON object đầy đủ hoặc fallback từ noi_dung_thao_luan
      if (data.noi_dung_json && typeof data.noi_dung_json === 'object') {
        const json = data.noi_dung_json as Record<string, unknown>;
        // Nếu là TipTap document (có "type":"doc") → dùng trực tiếp
        if (json.type === 'doc' && Array.isArray(json.content)) {
          setEditorJson(json);
        } else {
          // Legacy: convert từ noi_dung_thao_luan plain text
          const text = typeof json.noi_dung_thao_luan === 'string' ? json.noi_dung_thao_luan : '';
          setEditorJson({
            type: 'doc',
            content: [{ type: 'paragraph', content: text ? [{ type: 'text', text }] : [] }],
          });
        }
      }
      dirtyRef.current = false;
    } catch (e: unknown) {
      setMsg({ type: 'err', text: errMsg(e, 'Lỗi tải biên bản') });
    }
  }, [id]);

  useEffect(() => { fetchBienBan(); }, [fetchBienBan]);

  // Cleanup auto-save timer khi unmount
  useEffect(() => {
    return () => {
      if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
    };
  }, []);

  const persistContent = useCallback(
    async (json: Record<string, unknown>, html: string) => {
      try {
        await bienBanApi.put(id, json, html);
        dirtyRef.current = false;
      } catch (e: unknown) {
        setMsg({ type: 'err', text: errMsg(e, 'Auto-save lỗi') });
      }
    },
    [id],
  );

  const handleEditorChange = useCallback(
    (json: Record<string, unknown>, html: string) => {
      setEditorJson(json);
      setEditorHtml(html);
      dirtyRef.current = true;
      // Reset debounce timer
      if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
      autoSaveTimer.current = setTimeout(() => {
        if (dirtyRef.current) persistContent(json, html);
      }, AUTO_SAVE_DEBOUNCE_MS);
    },
    [persistContent],
  );

  const handleSave = async () => {
    if (!bb || !editorJson) return;
    setBusy('save');
    try {
      await bienBanApi.put(id, editorJson, editorHtml);
      setMsg({ type: 'ok', text: 'Đã lưu' });
      dirtyRef.current = false;
      await fetchBienBan();
    } catch (e: unknown) { setMsg({ type: 'err', text: errMsg(e) }); }
    finally { setBusy(null); }
  };

  const handleAction = async (action: 'trinh-ky' | 'ky') => {
    if (!bb) return;
    // Lưu nội dung pending trước khi đổi trạng thái
    if (dirtyRef.current && editorJson) {
      await persistContent(editorJson, editorHtml);
    }
    setBusy(action);
    try {
      if (action === 'trinh-ky') await bienBanApi.trinhKy(bb.id);
      else await bienBanApi.ky(bb.id);
      setMsg({ type: 'ok', text: action === 'ky' ? 'Đã ký Mock CKS' : 'Đã trình ký' });
      await fetchBienBan();
    } catch (e: unknown) { setMsg({ type: 'err', text: errMsg(e) }); }
    finally { setBusy(null); }
  };

  const handleXuat = async (dinh_dang: 'docx' | 'pdf') => {
    if (!bb) return;
    setBusy(`xuat-${dinh_dang}`);
    try {
      await bienBanApi.xuat(bb.id, dinh_dang);
      const fileUrl = bienBanApi.fileUrl(bb.id, dinh_dang);
      window.open(fileUrl, '_blank');
      setMsg({ type: 'ok', text: `Đã xuất ${dinh_dang.toUpperCase()}` });
    } catch (e: unknown) { setMsg({ type: 'err', text: errMsg(e) }); }
    finally { setBusy(null); }
  };

  if (!bb) return <div className="bg-white border rounded p-6 text-gray-500">Đang tải...</div>;

  // Locked nếu cuộc họp HUY/HOAN_THANH HOẶC biên bản đã ký/công bố HOẶC user
  // không phải organizer (CBCC chỉ xem readonly).
  const isLocked = meetingLocked || bb.trang_thai === 'DA_KY' || bb.trang_thai === 'CONG_BO' || !canEdit;

  return (
    <div className="bg-white border rounded p-6 space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">
          Biên bản — <span className="text-sm font-normal text-gray-600">{bb.trang_thai}</span>
        </h3>
        <div className="flex gap-2">
          {!isLocked && (
            <>
              <button
                onClick={handleSave}
                disabled={busy !== null}
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-gray-100 border rounded text-sm hover:bg-gray-200"
              >
                {busy === 'save' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                Lưu
              </button>
              {bb.trang_thai === 'DANG_SOAN' && (
                <button
                  onClick={() => handleAction('trinh-ky')}
                  disabled={busy !== null}
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                >
                  <Send className="w-3.5 h-3.5" />
                  Trình ký
                </button>
              )}
              {bb.trang_thai === 'TRINH_KY' && (
                <button
                  onClick={() => handleAction('ky')}
                  disabled={busy !== null}
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                >
                  <FileSignature className="w-3.5 h-3.5" />
                  Ký (Mock CKS)
                </button>
              )}
            </>
          )}
          <button
            onClick={() => handleXuat('docx')}
            disabled={busy !== null}
            className="inline-flex items-center gap-1 px-3 py-1.5 border rounded text-sm hover:bg-gray-50"
          >
            <FileDown className="w-3.5 h-3.5" />
            DOCX
          </button>
          <button
            onClick={() => handleXuat('pdf')}
            disabled={busy !== null}
            className="inline-flex items-center gap-1 px-3 py-1.5 border rounded text-sm hover:bg-gray-50"
          >
            <FileDown className="w-3.5 h-3.5" />
            PDF
          </button>
        </div>
      </div>

      {msg && (
        <div className={`p-3 rounded text-sm ${msg.type === 'ok' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'} border`}>
          {msg.text}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium mb-2">Nội dung biên bản</label>
        <TipTapEditor
          initialContent={editorJson}
          readOnly={isLocked}
          onChange={handleEditorChange}
        />
        <p className="text-xs text-gray-500 mt-2">
          Auto-save mỗi {AUTO_SAVE_DEBOUNCE_MS / 1000}s khi có thay đổi.
          Nhấn "Lưu" để lưu ngay.
        </p>
      </div>

      {bb.is_mock_signed && (
        <div className="p-4 bg-green-50 border border-green-200 rounded text-sm">
          <p className="font-medium mb-1">✓ Mock CKS</p>
          <p className="text-xs">Hash: <code className="break-all">{bb.hash_noi_dung}</code></p>
          <p className="text-xs">QR: <a href={bb.qr_xac_thuc!} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">{bb.qr_xac_thuc}</a></p>
          <p className="text-xs">Ký lúc: {bb.thoi_gian_ky}</p>
        </div>
      )}
    </div>
  );
}
