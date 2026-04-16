'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { User, Lock, Building2, BadgeCheck, Shield, Eye, EyeOff, ArrowLeft, Pencil, Save, X } from 'lucide-react';

import { useCurrentUser, useAuthStore } from '@/stores/useAuthStore';
import { authService } from '@/services/auth.service';
import { changePasswordSchema, type ChangePasswordFormData } from '@/lib/validations/auth';
import { isApiError } from '@/lib/axios';

export default function HoSoPage() {
  const router = useRouter();
  const user = useCurrentUser();
  const { setUser } = useAuthStore();

  // Chỉnh sửa thông tin liên hệ
  const [isEditingContact, setIsEditingContact] = useState(false);
  const [editEmail, setEditEmail] = useState(user?.email || '');
  const [editPhone, setEditPhone] = useState(user?.so_dien_thoai || '');
  const [contactSaving, setContactSaving] = useState(false);
  const [contactStatus, setContactStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Đổi mật khẩu
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordStatus, setPasswordStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
  });

  const handleStartEdit = () => {
    setEditEmail(user?.email || '');
    setEditPhone(user?.so_dien_thoai || '');
    setIsEditingContact(true);
    setContactStatus(null);
  };

  const handleCancelEdit = () => {
    setIsEditingContact(false);
    setContactStatus(null);
  };

  const handleSaveContact = async () => {
    setContactSaving(true);
    setContactStatus(null);
    try {
      const result = await authService.updateProfile({
        email: editEmail,
        so_dien_thoai: editPhone,
      });
      // Cập nhật store để reflect ngay
      if (user) {
        setUser({
          ...user,
          email: result.data.email,
          so_dien_thoai: result.data.so_dien_thoai,
        });
      }
      setIsEditingContact(false);
      setContactStatus({ type: 'success', message: result.message || 'Cập nhật thành công' });
    } catch (error: unknown) {
      if (isApiError(error)) {
        setContactStatus({ type: 'error', message: error.message });
      } else {
        setContactStatus({ type: 'error', message: 'Cập nhật thất bại. Vui lòng thử lại.' });
      }
    } finally {
      setContactSaving(false);
    }
  };

  const onSubmitPassword = async (data: ChangePasswordFormData) => {
    setPasswordStatus(null);
    try {
      const result = await authService.changePassword(data);
      setPasswordStatus({ type: 'success', message: result.message || 'Đổi mật khẩu thành công' });
      reset();
    } catch (error: unknown) {
      if (isApiError(error)) {
        setPasswordStatus({ type: 'error', message: error.message });
      } else {
        setPasswordStatus({ type: 'error', message: 'Đổi mật khẩu thất bại. Vui lòng thử lại.' });
      }
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="p-4 md:p-6 max-w-3xl mx-auto space-y-6">
        {/* Header với nút quay lại */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-white rounded-lg transition-colors border border-gray-200 bg-white"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-xl font-bold text-gray-900">Hồ sơ cá nhân</h1>
        </div>

        {/* Thông tin cá nhân */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-800 flex items-center gap-2">
              <User className="w-5 h-5 text-blue-600" />
              Thông tin cá nhân
            </h2>
            {!isEditingContact && (
              <button
                onClick={handleStartEdit}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors border border-blue-200"
              >
                <Pencil className="w-3.5 h-3.5" />
                Chỉnh sửa
              </button>
            )}
          </div>

          {contactStatus && (
            <div
              className={`mb-4 px-4 py-3 rounded-lg text-sm ${
                contactStatus.type === 'success'
                  ? 'bg-green-50 text-green-700 border border-green-200'
                  : 'bg-red-50 text-red-700 border border-red-200'
              }`}
            >
              {contactStatus.message}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <InfoRow label="Họ tên" value={user.ho_ten} />
            <InfoRow label="Mã công chức" value={user.ma_cc} />
            <InfoRow
              label="Đơn vị"
              value={user.don_vi?.ten_don_vi || '—'}
              icon={<Building2 className="w-4 h-4 text-gray-400" />}
            />
            <InfoRow
              label="Chức vụ"
              value={user.chuc_vu || '—'}
              icon={<BadgeCheck className="w-4 h-4 text-gray-400" />}
            />
            <InfoRow
              label="Vai trò"
              value={user.vai_tro?.ten_vai_tro || '—'}
              icon={<Shield className="w-4 h-4 text-gray-400" />}
            />

            {/* Email - editable */}
            {isEditingContact ? (
              <div>
                <label className="block text-gray-500 text-xs mb-1">Email</label>
                <input
                  type="email"
                  value={editEmail}
                  onChange={(e) => setEditEmail(e.target.value)}
                  placeholder="Nhập email..."
                  className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            ) : (
              <InfoRow label="Email" value={user.email || '—'} />
            )}

            {/* Số điện thoại - editable */}
            {isEditingContact ? (
              <div>
                <label className="block text-gray-500 text-xs mb-1">Số điện thoại</label>
                <input
                  type="tel"
                  value={editPhone}
                  onChange={(e) => setEditPhone(e.target.value)}
                  placeholder="Nhập số điện thoại..."
                  className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            ) : (
              <InfoRow label="Số điện thoại" value={user.so_dien_thoai || '—'} />
            )}
          </div>

          {/* Nút Lưu / Hủy khi đang edit */}
          {isEditingContact && (
            <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-100">
              <button
                onClick={handleSaveContact}
                disabled={contactSaving}
                className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Save className="w-4 h-4" />
                {contactSaving ? 'Đang lưu...' : 'Lưu thay đổi'}
              </button>
              <button
                onClick={handleCancelEdit}
                disabled={contactSaving}
                className="flex items-center gap-1.5 px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
                Hủy
              </button>
            </div>
          )}
        </div>

        {/* Form đổi mật khẩu */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-base font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Lock className="w-5 h-5 text-blue-600" />
            Đổi mật khẩu
          </h2>

          {passwordStatus && (
            <div
              className={`mb-4 px-4 py-3 rounded-lg text-sm ${
                passwordStatus.type === 'success'
                  ? 'bg-green-50 text-green-700 border border-green-200'
                  : 'bg-red-50 text-red-700 border border-red-200'
              }`}
            >
              {passwordStatus.message}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmitPassword)} className="space-y-4 max-w-md">
            <PasswordField
              label="Mật khẩu hiện tại"
              registration={register('currentPassword')}
              error={errors.currentPassword?.message}
              show={showCurrentPassword}
              onToggle={() => setShowCurrentPassword(!showCurrentPassword)}
            />
            <PasswordField
              label="Mật khẩu mới"
              registration={register('newPassword')}
              error={errors.newPassword?.message}
              show={showNewPassword}
              onToggle={() => setShowNewPassword(!showNewPassword)}
            />
            <PasswordField
              label="Xác nhận mật khẩu mới"
              registration={register('confirmPassword')}
              error={errors.confirmPassword?.message}
              show={showConfirmPassword}
              onToggle={() => setShowConfirmPassword(!showConfirmPassword)}
            />

            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? 'Đang xử lý...' : 'Đổi mật khẩu'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

function InfoRow({ label, value, icon }: { label: string; value: string; icon?: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2">
      {icon}
      <div>
        <p className="text-gray-500 text-xs">{label}</p>
        <p className="text-gray-900 font-medium">{value}</p>
      </div>
    </div>
  );
}

function PasswordField({
  label,
  registration,
  error,
  show,
  onToggle,
}: {
  label: string;
  registration: ReturnType<typeof Object>;
  error?: string;
  show: boolean;
  onToggle: () => void;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <div className="relative">
        <input
          type={show ? 'text' : 'password'}
          {...(registration as Record<string, unknown>)}
          className={`w-full px-3 py-2 pr-10 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            error ? 'border-red-300' : 'border-gray-300'
          }`}
        />
        <button
          type="button"
          onClick={onToggle}
          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
        >
          {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
        </button>
      </div>
      {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
    </div>
  );
}
