'use client';
import { useUIStore } from "@/lib/stores/uiStore";
import Breadcrumbs from "@/components/ui/Breadcrumbs";
import { Menu } from "lucide-react";

export default function Header() {
  const { isSidebarOpen, setSidebarOpen } = useUIStore();

  return (
    <header className="sticky top-0 z-30 h-16 bg-white border-b border-gray-200 px-6 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <button
          onClick={() => setSidebarOpen(!isSidebarOpen)}
          className="lg:hidden p-2 text-gray-600 hover:bg-gray-100 rounded-md"
        >
          <Menu className="w-5 h-5" />
        </button>
        <Breadcrumbs />
      </div>
      <div className="flex items-center gap-3">
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-green-50 text-green-700 text-xs font-medium rounded-full border border-green-200">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          Dữ liệu cập nhật
        </div>
      </div>
    </header>
  );
}