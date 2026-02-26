/**
 * src/app/(main)/dien-dan/quan-ly/page.tsx
 * Trang quan ly Dien dan (danh cho DIEU_PHOI_FORUM hoac SUPER_ADMIN).
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ChevronRight, Check, X, Edit2, Trash2, Plus, Loader2, BarChart3 } from 'lucide-react';
import { useAuthStore } from '@/stores/useAuthStore';
import { chuDeApi, chuyenMucApi, dashboardApi } from '@/services/forum';
import type { IChuDeListItem, IChuyenMuc, IDashboardSummary, IChuyenMucCreate } from '@/types/forum';
import { TRANG_THAI_LABEL, TRANG_THAI_COLOR } from '@/types/forum';

type Tab = 'cho-duyet' | 'da-an' | 'chuyen-muc' | 'thong-ke';

export default function QuanLyPage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);

  // Permission check
  const platformRoles: string[] = (user as any)?.platform_roles ?? [];
  const coQuyenQuanLy = user?.is_system_admin === true || platformRoles.includes('DIEU_PHOI_FORUM');

  const [activeTab, setActiveTab] = useState<Tab>('cho-duyet');

  // Tab 1: Cho duyet
  const [chuDeChoDuyet, setChuDeChoDuyet] = useState<IChuDeListItem[]>([]);
  const [isLoadingChoDuyet, setIsLoadingChoDuyet] = useState(false);

  // Tab 2: Da an
  const [chuDeDaAn, setChuDeDaAn] = useState<IChuDeListItem[]>([]);
  const [isLoadingDaAn, setIsLoadingDaAn] = useState(false);

  // Tab 3: Quan ly chuyen muc
  const [chuyenMucs, setChuyenMucs] = useState<IChuyenMuc[]>([]);
  const [isLoadingChuyenMuc, setIsLoadingChuyenMuc] = useState(false);
  const [showAddChuyenMucForm, setShowAddChuyenMucForm] = useState(false);
  const [newChuyenMuc, setNewChuyenMuc] = useState<Partial<IChuyenMucCreate>>({
    ten_chuyen_muc: '',
    mo_ta: '',
    chi_doc: false,
    yeu_cau_duyet: false,
  });

  // Tab 4: Thong ke
  const [dashboardSummary, setDashboardSummary] = useState<IDashboardSummary | null>(null);
  const [isLoadingDashboard, setIsLoadingDashboard] = useState(false);

  // Load cho duyet
  useEffect(() => {
    if (activeTab === 'cho-duyet' && coQuyenQuanLy) {
      const load = async () => {
        setIsLoadingChoDuyet(true);
        try {
          const result = await chuDeApi.danhSach({ trang_thai: 'CHO_DUYET', page_size: 100 });
          setChuDeChoDuyet(result.items);
        } catch (err) {
          console.error('Load cho duyet error:', err);
        } finally {
          setIsLoadingChoDuyet(false);
        }
      };
      load();
    }
  }, [activeTab, coQuyenQuanLy]);

  // Load da an
  useEffect(() => {
    if (activeTab === 'da-an' && coQuyenQuanLy) {
      const load = async () => {
        setIsLoadingDaAn(true);
        try {
          const result = await chuDeApi.danhSach({ trang_thai: 'AN', page_size: 100 });
          setChuDeDaAn(result.items);
        } catch (err) {
          console.error('Load da an error:', err);
        } finally {
          setIsLoadingDaAn(false);
        }
      };
      load();
    }
  }, [activeTab, coQuyenQuanLy]);

  // Load chuyen muc
  useEffect(() => {
    if (activeTab === 'chuyen-muc' && coQuyenQuanLy) {
      const load = async () => {
        setIsLoadingChuyenMuc(true);
        try {
          const result = await chuyenMucApi.danhSach();
          setChuyenMucs(result);
        } catch (err) {
          console.error('Load chuyen muc error:', err);
        } finally {
          setIsLoadingChuyenMuc(false);
        }
      };
      load();
    }
  }, [activeTab, coQuyenQuanLy]);

  // Load thong ke
  useEffect(() => {
    if (activeTab === 'thong-ke' && coQuyenQuanLy) {
      const load = async () => {
        setIsLoadingDashboard(true);
        try {
          const result = await dashboardApi.summary();
          setDashboardSummary(result);
        } catch (err) {
          console.error('Load dashboard error:', err);
        } finally {
          setIsLoadingDashboard(false);
        }
      };
      load();
    }
  }, [activeTab, coQuyenQuanLy]);

  // Duyet chu de
  const handleDuyet = async (id: string) => {
    try {
      await chuDeApi.hanhDong(id, { hanh_dong: 'DUYET' });
      setChuDeChoDuyet((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      console.error('Duyet error:', err);
      alert('Khong the duyet chu de. Vui long thu lai.');
    }
  };

  // An chu de
  const handleAn = async (id: string) => {
    try {
      await chuDeApi.hanhDong(id, { hanh_dong: 'AN' });
      setChuDeChoDuyet((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      console.error('An error:', err);
      alert('Khong the an chu de. Vui long thu lai.');
    }
  };

  // Them chuyen muc
  const handleAddChuyenMuc = async () => {
    if (!newChuyenMuc.ten_chuyen_muc?.trim()) {
      alert('Vui long nhap ten chuyen muc');
      return;
    }

    try {
      await chuyenMucApi.taoMoi(newChuyenMuc as IChuyenMucCreate);
      setShowAddChuyenMucForm(false);
      setNewChuyenMuc({ ten_chuyen_muc: '', mo_ta: '', chi_doc: false, yeu_cau_duyet: false });
      // Reload chuyen muc
      const result = await chuyenMucApi.danhSach();
      setChuyenMucs(result);
    } catch (err) {
      console.error('Add chuyen muc error:', err);
      alert('Khong the them chuyen muc. Vui long thu lai.');
    }
  };

  // Xoa chuyen muc
  const handleDeleteChuyenMuc = async (id: string) => {
    if (!confirm('Ban co chac muon xoa chuyen muc nay?')) return;

    try {
      await chuyenMucApi.xoa(id);
      const result = await chuyenMucApi.danhSach();
      setChuyenMucs(result);
    } catch (err) {
      console.error('Delete chuyen muc error:', err);
      alert('Khong the xoa chuyen muc. Vui long thu lai.');
    }
  };

  // No permission
  if (!coQuyenQuanLy) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center max-w-md">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <X className="w-8 h-8 text-red-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Khong co quyen truy cap</h2>
          <p className="text-gray-600 mb-6">Ban khong co quyen truy cap trang nay</p>
          <button
            onClick={() => router.push('/dien-dan')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Quay lai Dien dan
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-gray-600 mb-6">
          <button onClick={() => router.push('/dien-dan')} className="hover:text-blue-600">
            Dien dan
          </button>
          <ChevronRight className="w-4 h-4" />
          <span className="text-gray-900 font-medium">Quan ly</span>
        </div>

        {/* Title */}
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Quan ly Dien dan</h1>

        {/* Tabs */}
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          <div className="flex border-b border-gray-200 overflow-x-auto">
            {[
              { key: 'cho-duyet' as Tab, label: 'Cho duyet' },
              { key: 'da-an' as Tab, label: 'Da an' },
              { key: 'chuyen-muc' as Tab, label: 'Quan ly chuyen muc' },
              { key: 'thong-ke' as Tab, label: 'Thong ke' },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex-shrink-0 px-6 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab.key
                    ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="p-6">
            {/* Tab 1: Cho duyet */}
            {activeTab === 'cho-duyet' && (
              <>
                {isLoadingChoDuyet ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                  </div>
                ) : chuDeChoDuyet.length === 0 ? (
                  <div className="text-center py-12">
                    <p className="text-gray-500">Khong co chu de nao cho duyet</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {chuDeChoDuyet.map((item) => (
                      <div key={item.id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <h3 className="font-medium text-gray-900 mb-2">{item.tieu_de}</h3>
                            <p className="text-sm text-gray-600 mb-2">{item.noi_dung_tom_tat}</p>
                            <p className="text-xs text-gray-500">
                              Tac gia: {item.tac_gia?.ho_ten || 'Khong ro'}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleDuyet(item.id)}
                              className="p-2 bg-green-600 text-white rounded hover:bg-green-700"
                              title="Duyet"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleAn(item.id)}
                              className="p-2 bg-red-600 text-white rounded hover:bg-red-700"
                              title="An"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {/* Tab 2: Da an */}
            {activeTab === 'da-an' && (
              <>
                {isLoadingDaAn ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                  </div>
                ) : chuDeDaAn.length === 0 ? (
                  <div className="text-center py-12">
                    <p className="text-gray-500">Khong co chu de nao da an</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {chuDeDaAn.map((item) => (
                      <div key={item.id} className="border border-gray-200 rounded-lg p-4">
                        <h3 className="font-medium text-gray-900 mb-2">{item.tieu_de}</h3>
                        <p className="text-sm text-gray-600 mb-2">{item.noi_dung_tom_tat}</p>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${TRANG_THAI_COLOR[item.trang_thai]}`}>
                          {TRANG_THAI_LABEL[item.trang_thai]}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {/* Tab 3: Quan ly chuyen muc */}
            {activeTab === 'chuyen-muc' && (
              <>
                <div className="mb-4">
                  <button
                    onClick={() => setShowAddChuyenMucForm(!showAddChuyenMucForm)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    <Plus className="w-4 h-4" />
                    Them chuyen muc
                  </button>
                </div>

                {showAddChuyenMucForm && (
                  <div className="mb-6 p-4 border border-gray-200 rounded-lg bg-gray-50">
                    <div className="space-y-3">
                      <input
                        type="text"
                        value={newChuyenMuc.ten_chuyen_muc || ''}
                        onChange={(e) => setNewChuyenMuc({ ...newChuyenMuc, ten_chuyen_muc: e.target.value })}
                        placeholder="Ten chuyen muc"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                      <textarea
                        value={newChuyenMuc.mo_ta || ''}
                        onChange={(e) => setNewChuyenMuc({ ...newChuyenMuc, mo_ta: e.target.value })}
                        placeholder="Mo ta"
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                      <div className="flex gap-4">
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={newChuyenMuc.chi_doc || false}
                            onChange={(e) => setNewChuyenMuc({ ...newChuyenMuc, chi_doc: e.target.checked })}
                          />
                          <span className="text-sm">Chi doc</span>
                        </label>
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={newChuyenMuc.yeu_cau_duyet || false}
                            onChange={(e) => setNewChuyenMuc({ ...newChuyenMuc, yeu_cau_duyet: e.target.checked })}
                          />
                          <span className="text-sm">Yeu cau duyet</span>
                        </label>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={handleAddChuyenMuc}
                          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                        >
                          Them
                        </button>
                        <button
                          onClick={() => setShowAddChuyenMucForm(false)}
                          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                        >
                          Huy
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {isLoadingChuyenMuc ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                  </div>
                ) : (
                  <div className="space-y-2">
                    {chuyenMucs.map((cm) => (
                      <div key={cm.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                        <div>
                          <h4 className="font-medium text-gray-900">{cm.ten_chuyen_muc}</h4>
                          {cm.mo_ta && <p className="text-sm text-gray-600">{cm.mo_ta}</p>}
                        </div>
                        <button
                          onClick={() => handleDeleteChuyenMuc(cm.id)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {/* Tab 4: Thong ke */}
            {activeTab === 'thong-ke' && (
              <>
                {isLoadingDashboard ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                  </div>
                ) : dashboardSummary ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                      { label: 'Chu de moi tuan', value: dashboardSummary.chu_de_moi_tuan, color: 'blue' },
                      { label: 'Tra loi chua doc', value: dashboardSummary.tra_loi_chua_doc, color: 'yellow' },
                      { label: 'Upvote tuan', value: dashboardSummary.upvote_tuan, color: 'green' },
                      { label: 'Chu de chua tra loi', value: dashboardSummary.chu_de_cua_toi_chua_tra_loi, color: 'red' },
                    ].map((stat) => (
                      <div key={stat.label} className={`p-6 bg-${stat.color}-50 border border-${stat.color}-200 rounded-lg`}>
                        <div className="flex items-center gap-3">
                          <BarChart3 className={`w-8 h-8 text-${stat.color}-600`} />
                          <div>
                            <p className={`text-3xl font-bold text-${stat.color}-700`}>{stat.value}</p>
                            <p className={`text-sm text-${stat.color}-600`}>{stat.label}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <p className="text-gray-500">Khong co du lieu thong ke</p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
