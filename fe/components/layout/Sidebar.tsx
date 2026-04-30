"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUIStore } from "@/lib/stores/uiStore";
import { LayoutDashboard, Globe2, AlertTriangle, PieChart, BarChart3, MessageSquare, X } from "lucide-react";
import { cn } from "@/lib/utils/cn";

const navItems = [
  { name: "Dashboard", path: "/", icon: LayoutDashboard },
  { name: "Quốc gia", path: "/countries", icon: Globe2 },
  { name: "Bất thường", path: "/anomalies", icon: AlertTriangle },
  { name: "Nhóm nước", path: "/clusters", icon: PieChart },
  { name: "So sánh", path: "/compare", icon: BarChart3 },
  { name: "AI Chat", path: "/chat", icon: MessageSquare },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { isSidebarOpen, setSidebarOpen } = useUIStore();

  return (
    <>
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}
      <aside
        role="navigation"
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 lg:translate-x-0",
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
          <h1 className="text-lg font-bold text-slate-900">Gov AI Agent</h1>
          <button onClick={() => setSidebarOpen(false)} className="lg:hidden p-1.5 text-gray-500 hover:text-gray-900 rounded-md">
            <X className="w-5 h-5" />
          </button>
        </div>
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.path || (item.path !== "/" && pathname.startsWith(item.path));
            return (
              <Link
                key={item.path}
                href={item.path}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 text-sm font-medium rounded-md transition-colors",
                  isActive
                    ? "bg-blue-50 text-blue-700 border-l-[3px] border-blue-600"
                    : "text-gray-600 hover:bg-gray-100 border-l-[3px] border-transparent"
                )}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </aside>
    </>
  );
}