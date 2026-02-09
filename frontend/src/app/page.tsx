import { redirect } from 'next/navigation';

export default function RootPage() {
  // Tự động chuyển hướng về trang login khi vào địa chỉ gốc
  redirect('/login');
}