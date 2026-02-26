/**
 * src/app/(main)/admin/users/page.tsx
 * ====================================
 * Trang Quản lý Người dùng (Admin Module).
 * 
 * Chức năng:
 * - Danh sách users với phân trang, filter
 * - Tạo mới, sửa, vô hiệu hóa user
 * - Reset password
 * - Điều chuyển nhân sự
 * 
 * Version: 1.1.0 (03/02/2026)
 * - Fix: Thêm render Edit/Transfer Modal
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { adminService, isApiError } from '@/services/admin.service';
import { 
  IUserResponse, 
  IUserCreateRequest, 
  IUserUpdateRequest,
  IUserTransferRequest,
  IDonViOption, 
  IVaiTroOption,
  IPagination,
} from '@/types/admin';
import { UserCreateModal, UserEditModal, UserTransferModal } from '@/components/admin/UserModals';

// =============================================================================
// SUB COMPONENTS
// =============================================================================

/**
 * Thứ tự sắp xếp chức vụ:
 * 0 - Chi cục trưởng
 * 1 - Phó Chi cục trưởng
 * 2 - Trưởng (đội/phòng): Đội trưởng, Trưởng phòng, Chánh Văn phòng...
 * 3 - Phó (đội/phòng): Phó Đội trưởng, Phó trưởng phòng, Phó Văn phòng...
 * 4 - Công chức
 * 5 - Hợp đồng 111
 * 
 * LƯU Ý: Check từ cụ thể → chung. "Phó chi cục trưởng" chứa cả
 * "phó", "chi cục", "trưởng" nên phải match riêng trước.
 */
function getChucVuPriority(user: IUserResponse): number {
  const cv = (user.chuc_vu || '').toLowerCase();
  const vt = (user.vai_tro_ten || '').toLowerCase();
  const text = `${cv} | ${vt}`;
  
  // 1) Phó Chi cục trưởng (check TRƯỚC "chi cục" vì chứa cả 2)
  if (text.includes('phó chi cục') || text.includes('phó cục')) return 1;
  // 2) Chi cục trưởng
  if (text.includes('chi cục trưởng') || text.includes('cục trưởng')) return 0;
  // 3) Phó đội/phòng (check TRƯỚC "trưởng" vì "Phó Đội trưởng" chứa cả 2)
  if (text.includes('phó')) return 3;
  // 4) Trưởng đội/phòng (Đội trưởng, Trưởng phòng, Chánh Văn phòng...)
  if (text.includes('trưởng') || text.includes('chánh')) return 2;
  // 5) Hợp đồng 111
  if (text.includes('hợp đồng') || text.includes('hđ') || text.includes('111')) return 5;
  // 6) Công chức (mặc định)
  return 4;
}

function sortUsersByChucVu(users: IUserResponse[]): IUserResponse[] {
  return [...users].sort((a, b) => {
    const priorityA = getChucVuPriority(a);
    const priorityB = getChucVuPriority(b);
    if (priorityA !== priorityB) return priorityA - priorityB;
    // Cùng chức vụ → sắp xếp theo họ tên
    return (a.ho_ten || '').localeCompare(b.ho_ten || '', 'vi');
  });
}

interface UserTableProps {
  users: IUserResponse[];
  isLoading: boolean;
  onEdit: (user: IUserResponse) => void;
  onToggleStatus: (user: IUserResponse) => void;
  onResetPassword: (user: IUserResponse) => void;
  onTransfer: (user: IUserResponse) => void;
  onDelete: (user: IUserResponse) => void;
}

function UserTable({ users, isLoading, onEdit, onToggleStatus, onResetPassword, onTransfer, onDelete }: UserTableProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (users.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-3xl">👥</span>
        </div>
        <p className="text-gray-500">Không có người dùng nào</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Mã CC</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Họ tên</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Đơn vị</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Vai trò</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Chức vụ</th>
            <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Trạng thái</th>
            <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Thao tác</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {users.map((user) => (
            <tr key={user.id} className="hover:bg-gray-50">
              <td className="px-4 py-3">
                <span className="font-mono text-sm font-medium text-gray-900">{user.ma_cc}</span>
              </td>
              <td className="px-4 py-3">
                <div>
                  <p className="font-medium text-gray-900">{user.ho_ten}</p>
                  {user.email && <p className="text-xs text-gray-500">{user.email}</p>}
                </div>
              </td>
              <td className="px-4 py-3">
                <span className="text-sm text-gray-700">{user.don_vi_ten || '-'}</span>
              </td>
              <td className="px-4 py-3">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  user.is_lanh_dao 
                    ? 'bg-purple-100 text-purple-700' 
                    : 'bg-gray-100 text-gray-700'
                }`}>
                  {user.vai_tro_ten || '-'}
                </span>
              </td>
              <td className="px-4 py-3">
                <span className="text-sm text-gray-700">{user.chuc_vu || '-'}</span>
              </td>
              <td className="px-4 py-3 text-center">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  user.is_active 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-red-100 text-red-700'
                }`}>
                  {user.is_active ? 'Hoạt động' : 'Vô hiệu'}
                </span>
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center justify-center gap-1">
                  <button
                    onClick={() => onEdit(user)}
                    className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    title="Sửa thông tin"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => onTransfer(user)}
                    className="p-1.5 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                    title="Điều chuyển"
                    disabled={user.ma_cc === 'ADMIN-001'}
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                    </svg>
                  </button>
                  <button
                    onClick={() => onResetPassword(user)}
                    className="p-1.5 text-orange-600 hover:bg-orange-50 rounded-lg transition-colors"
                    title="Reset mật khẩu"
                    disabled={user.ma_cc === 'ADMIN-001'}
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => onToggleStatus(user)}
                    className={`p-1.5 rounded-lg transition-colors ${
                      user.is_active 
                        ? 'text-red-600 hover:bg-red-50' 
                        : 'text-green-600 hover:bg-green-50'
                    }`}
                    title={user.is_active ? 'Vô hiệu hóa' : 'Kích hoạt'}
                    disabled={user.ma_cc === 'ADMIN-001'}
                  >
                    {user.is_active ? (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                      </svg>
                    ) : (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    )}
                  </button>
                  {/* Nút xóa - chỉ hiện khi user đã bị vô hiệu hóa */}
                  {!user.is_active && user.ma_cc !== 'ADMIN-001' && (
                    <button
                      onClick={() => onDelete(user)}
                      className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Xóa hoàn toàn"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// =============================================================================
// PAGINATION
// =============================================================================

interface PaginationProps {
  pagination: IPagination;
  onPageChange: (page: number) => void;
}

function Pagination({ pagination, onPageChange }: PaginationProps) {
  const { page, total_pages } = pagination;

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
      <div className="text-sm text-gray-500">
        {total_pages > 1 
          ? `Trang ${page} / ${total_pages} • Tổng ${pagination.total_items} người dùng`
          : `Tổng ${pagination.total_items} người dùng`
        }
      </div>
      {total_pages > 1 && (
        <div className="flex gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Trước
          </button>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= total_pages}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Sau
          </button>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function AdminUsersPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // Data states
  const [allUsers, setAllUsers] = useState<IUserResponse[]>([]);  // Toàn bộ data đã sort
  const [clientPage, setClientPage] = useState(1);                // Trang hiện tại (client-side)
  const PAGE_SIZE = 20;
  const [donViList, setDonViList] = useState<IDonViOption[]>([]);
  const [vaiTroList, setVaiTroList] = useState<IVaiTroOption[]>([]);
  
  // Phân trang client-side: sort trước → chia trang sau
  const sortedUsers = sortUsersByChucVu(allUsers);
  const totalItems = sortedUsers.length;
  const totalPages = Math.ceil(totalItems / PAGE_SIZE);
  const users = sortedUsers.slice((clientPage - 1) * PAGE_SIZE, clientPage * PAGE_SIZE);
  const pagination: IPagination = {
    page: clientPage,
    page_size: PAGE_SIZE,
    total_items: totalItems,
    total_pages: totalPages,
  };

  // Filter states
  const [search, setSearch] = useState('');
  const [filterDonVi, setFilterDonVi] = useState('');
  const [filterVaiTro, setFilterVaiTro] = useState('');
  const [filterActive, setFilterActive] = useState<string>('');
  
  // UI states
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<IUserResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load danh sách đơn vị và vai trò
  useEffect(() => {
    const loadOptions = async () => {
      try {
        const [donVi, vaiTro] = await Promise.all([
          adminService.getDonViList(),
          adminService.getVaiTroList(),
        ]);
        setDonViList(donVi);
        setVaiTroList(vaiTro);
      } catch (err) {
        console.error('Error loading options:', err);
      }
    };
    loadOptions();
  }, []);

  // Load ALL users: gọi API nhiều trang (page_size=100) → gom hết → sort client-side
  const loadUsers = useCallback(async (resetPage: boolean = true) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const baseParams: any = {};
      if (search) baseParams.search = search;
      if (filterDonVi) baseParams.don_vi_id = filterDonVi;
      if (filterVaiTro) baseParams.vai_tro_id = filterVaiTro;
      if (filterActive !== '') baseParams.is_active = filterActive === 'true';
      
      // Gọi trang đầu để biết tổng số trang
      const firstPage = await adminService.getUsers({ ...baseParams, page: 1, page_size: 100 });
      let all: IUserResponse[] = [...firstPage.data];
      
      // Load các trang còn lại (nếu có)
      const totalApiPages = firstPage.pagination.total_pages;
      if (totalApiPages > 1) {
        const remaining = await Promise.all(
          Array.from({ length: totalApiPages - 1 }, (_, i) =>
            adminService.getUsers({ ...baseParams, page: i + 2, page_size: 100 })
          )
        );
        for (const res of remaining) {
          all = all.concat(res.data);
        }
      }
      
      setAllUsers(all);
      if (resetPage) setClientPage(1);
    } catch (err) {
      setError(isApiError(err) ? err.message : 'Có lỗi xảy ra');
    } finally {
      setIsLoading(false);
    }
  }, [search, filterDonVi, filterVaiTro, filterActive]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  // Handlers
  const handleSearch = () => {
    loadUsers();
  };

  const handlePageChange = (page: number) => {
    setClientPage(page);
  };

  const handleEdit = (user: IUserResponse) => {
    setSelectedUser(user);
    setShowEditModal(true);
  };

  const handleTransfer = (user: IUserResponse) => {
    if (user.ma_cc === 'ADMIN-001') {
      alert('Không thể điều chuyển tài khoản ADMIN-001');
      return;
    }
    setSelectedUser(user);
    setShowTransferModal(true);
  };

  const handleResetPassword = (user: IUserResponse) => {
    if (user.ma_cc === 'ADMIN-001') {
      alert('Không thể reset mật khẩu tài khoản ADMIN-001');
      return;
    }
    setSelectedUser(user);
    setShowResetPasswordModal(true);
  };

  const handleToggleStatus = (user: IUserResponse) => {
    if (user.ma_cc === 'ADMIN-001') {
      alert('Không thể thay đổi trạng thái tài khoản ADMIN-001');
      return;
    }
    setSelectedUser(user);
    setShowStatusModal(true);
  };

  const handleDelete = (user: IUserResponse) => {
    if (user.ma_cc === 'ADMIN-001') {
      alert('Không thể xóa tài khoản ADMIN-001');
      return;
    }
    if (user.is_active) {
      alert('Chỉ có thể xóa user đã bị vô hiệu hóa');
      return;
    }
    setSelectedUser(user);
    setShowDeleteModal(true);
  };

  const confirmResetPassword = async () => {
    if (!selectedUser) return;
    
    setIsSubmitting(true);
    try {
      await adminService.resetUserPassword(selectedUser.id);
      alert(`Đã reset mật khẩu cho ${selectedUser.ma_cc} về 123456`);
      setShowResetPasswordModal(false);
      setSelectedUser(null);
    } catch (err) {
      alert(isApiError(err) ? err.message : 'Có lỗi xảy ra');
    } finally {
      setIsSubmitting(false);
    }
  };

  const confirmToggleStatus = async () => {
    if (!selectedUser) return;
    
    setIsSubmitting(true);
    try {
      await adminService.updateUserStatus(selectedUser.id, { 
        is_active: !selectedUser.is_active 
      });
      loadUsers(false);
      setShowStatusModal(false);
      setSelectedUser(null);
    } catch (err) {
      alert(isApiError(err) ? err.message : 'Có lỗi xảy ra');
    } finally {
      setIsSubmitting(false);
    }
  };

  const confirmDelete = async () => {
    if (!selectedUser) return;
    
    setIsSubmitting(true);
    try {
      await adminService.deleteUser(selectedUser.id);
      alert(`Đã xóa hoàn toàn tài khoản ${selectedUser.ma_cc}`);
      loadUsers(false);
      setShowDeleteModal(false);
      setSelectedUser(null);
    } catch (err) {
      alert(isApiError(err) ? err.message : 'Có lỗi xảy ra');
    } finally {
      setIsSubmitting(false);
    }
  };

  // ===== EXPORT EXCEL =====
  const handleExport = async () => {
    if (sortedUsers.length === 0) {
      alert('Không có dữ liệu để xuất');
      return;
    }

    try {
      const XLSX = await import('xlsx');

      const exportData = sortedUsers.map((user, index) => ({
        'STT': index + 1,
        'Mã CC': user.ma_cc,
        'Họ tên': user.ho_ten,
        'Đơn vị': user.don_vi_ten || '',
        'Vai trò': user.vai_tro_ten || '',
        'Chức vụ': user.chuc_vu || '',
        'Email': user.email || '',
        'Trạng thái': user.is_active ? 'Hoạt động' : 'Vô hiệu',
      }));

      const ws = XLSX.utils.json_to_sheet(exportData);
      
      // Đặt độ rộng cột
      ws['!cols'] = [
        { wch: 5 },   // STT
        { wch: 14 },  // Mã CC
        { wch: 28 },  // Họ tên
        { wch: 28 },  // Đơn vị
        { wch: 16 },  // Vai trò
        { wch: 20 },  // Chức vụ
        { wch: 28 },  // Email
        { wch: 12 },  // Trạng thái
      ];

      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Danh sách công chức');

      // Tên file theo đơn vị (nếu đang lọc)
      const donViName = filterDonVi 
        ? donViList.find(d => d.id === filterDonVi)?.ten_don_vi || 'don-vi'
        : 'tat-ca';
      const date = new Date().toISOString().slice(0, 10);
      XLSX.writeFile(wb, `danh-sach-cong-chuc_${donViName}_${date}.xlsx`);
    } catch {
      alert('Lỗi xuất file. Hãy đảm bảo đã cài thư viện: npm install xlsx');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push('/admin')}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">👥 Quản lý Người dùng</h1>
              <p className="text-gray-600">Tạo, sửa, điều chuyển và quản lý tài khoản</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleExport}
              disabled={isLoading || sortedUsers.length === 0}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Xuất Excel
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Tạo mới
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="md:col-span-2">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Tìm theo mã CC hoặc họ tên..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <select
              value={filterDonVi}
              onChange={(e) => setFilterDonVi(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Tất cả đơn vị</option>
              {donViList.filter(d => d.ma_don_vi !== 'DEPT-ADMIN').map((dv) => (
                <option key={dv.id} value={dv.id}>{dv.ten_don_vi}</option>
              ))}
            </select>
            <select
              value={filterActive}
              onChange={(e) => setFilterActive(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Tất cả trạng thái</option>
              <option value="true">Đang hoạt động</option>
              <option value="false">Vô hiệu hóa</option>
            </select>
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Tìm kiếm
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <UserTable
            users={users}
            isLoading={isLoading}
            onEdit={handleEdit}
            onToggleStatus={handleToggleStatus}
            onResetPassword={handleResetPassword}
            onTransfer={handleTransfer}
            onDelete={handleDelete}
          />
          <Pagination pagination={pagination} onPageChange={handlePageChange} />
        </div>
      </main>

      {/* Reset Password Modal */}
      {showResetPasswordModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">🔑 Reset mật khẩu</h3>
            <p className="text-gray-600 mb-4">
              Bạn có chắc muốn reset mật khẩu cho <strong>{selectedUser.ho_ten}</strong> ({selectedUser.ma_cc}) về <strong>123456</strong>?
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => { setShowResetPasswordModal(false); setSelectedUser(null); }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                disabled={isSubmitting}
              >
                Hủy
              </button>
              <button
                onClick={confirmResetPassword}
                className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Đang xử lý...' : 'Xác nhận'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toggle Status Modal */}
      {showStatusModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {selectedUser.is_active ? '🚫 Vô hiệu hóa tài khoản' : '✅ Kích hoạt tài khoản'}
            </h3>
            <p className="text-gray-600 mb-4">
              Bạn có chắc muốn {selectedUser.is_active ? 'vô hiệu hóa' : 'kích hoạt'} tài khoản <strong>{selectedUser.ho_ten}</strong> ({selectedUser.ma_cc})?
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => { setShowStatusModal(false); setSelectedUser(null); }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                disabled={isSubmitting}
              >
                Hủy
              </button>
              <button
                onClick={confirmToggleStatus}
                className={`px-4 py-2 text-white rounded-lg disabled:opacity-50 ${
                  selectedUser.is_active 
                    ? 'bg-red-600 hover:bg-red-700' 
                    : 'bg-green-600 hover:bg-green-700'
                }`}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Đang xử lý...' : 'Xác nhận'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateModal && (
        <UserCreateModal
          donViList={donViList}
          vaiTroList={vaiTroList}
          onSuccess={() => loadUsers()}
          onClose={() => setShowCreateModal(false)}
        />
      )}

      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
        <UserEditModal
          user={selectedUser}
          onSuccess={() => loadUsers(false)}
          onClose={() => { setShowEditModal(false); setSelectedUser(null); }}
        />
      )}

      {/* Transfer User Modal */}
      {showTransferModal && selectedUser && (
        <UserTransferModal
          user={selectedUser}
          donViList={donViList}
          vaiTroList={vaiTroList}
          onSuccess={() => loadUsers(false)}
          onClose={() => { setShowTransferModal(false); setSelectedUser(null); }}
        />
      )}

      {/* Delete User Modal */}
      {showDeleteModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-red-600 mb-2">🗑️ Xóa hoàn toàn tài khoản</h3>
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <p className="text-red-700 text-sm font-medium">⚠️ Cảnh báo: Thao tác này KHÔNG THỂ HOÀN TÁC!</p>
            </div>
            <p className="text-gray-600 mb-4">
              Bạn có chắc muốn xóa hoàn toàn tài khoản <strong>{selectedUser.ho_ten}</strong> ({selectedUser.ma_cc})?
            </p>
            <p className="text-gray-500 text-sm mb-4">
              Tất cả dữ liệu liên quan đến user này sẽ bị xóa vĩnh viễn.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => { setShowDeleteModal(false); setSelectedUser(null); }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                disabled={isSubmitting}
              >
                Hủy
              </button>
              <button
                onClick={confirmDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Đang xóa...' : 'Xóa hoàn toàn'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}