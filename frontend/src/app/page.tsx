import { redirect } from 'next/navigation';

export default function RootPage() {
  // Tự động chuyển hướng về tổng quan nền tảng
  redirect('/tong-quan');
}
