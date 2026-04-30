import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 lg:ml-64 min-h-screen transition-all duration-300">
        <Header />
        <div className="p-6 lg:p-8">{children}</div>
      </main>
    </div>
  );
}