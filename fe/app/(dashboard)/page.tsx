'use client';
import { useCountries } from '@/lib/hooks/useCountries';
import { useClusters } from '@/lib/hooks/useClusters';
import { useAnomalies } from '@/lib/hooks/useAnomalies';
import { CardSkeleton } from '@/components/ui/Skeletons';
import Link from 'next/link';

export default function DashboardPage() {
  const { data: countries, isLoading: l1 } = useCountries();
  const { data: clusters, isLoading: l2 } = useClusters(2022);
  const { data: anomalies, isLoading: l3 } = useAnomalies({ limit: 50 });

  if (l1 || l2 || l3) {
    return <div className="grid grid-cols-1 md:grid-cols-3 gap-4"><CardSkeleton /><CardSkeleton /><CardSkeleton /></div>;
  }

  const totalCountries = countries?.length || 0;
  const clusterCount = clusters ? new Set(clusters.map(c => c.cluster_id)).size : 0;
  const totalAnomalies = anomalies?.length || 0;

  const quickLinks = [
    { title: "Phân tích Quốc gia", desc: "Xem chi tiết tăng trưởng & xu hướng", href: "/countries", color: "bg-blue-50 hover:bg-blue-100 border border-blue-200" },
    { title: "Phát hiện Bất thường", desc: "Giám sát rủi ro & chỉ số vượt ngưỡng", href: "/anomalies", color: "bg-orange-50 hover:bg-orange-100 border border-orange-200" },
    { title: "Nhóm Quốc gia (Clusters)", desc: "Phân loại theo cấu trúc kinh tế", href: "/clusters", color: "bg-green-50 hover:bg-green-100 border border-green-200" },
    { title: "So sánh Chỉ số", desc: "Đánh giá đa chiều giữa các quốc gia", href: "/compare", color: "bg-purple-50 hover:bg-purple-100 border border-purple-200" },
  ];

  return (
    <div className="space-y-6">
      {/* 1. Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-100">
          <h2 className="font-medium text-gray-500 text-sm uppercase tracking-wider">Total Countries</h2>
          <p className="text-3xl font-bold mt-2 text-gray-800">{totalCountries}</p>
          <Link href="/countries" className="text-sm text-blue-600 hover:underline mt-2 inline-block">View Details &rarr;</Link>
        </div>
        <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-100">
          <h2 className="font-medium text-gray-500 text-sm uppercase tracking-wider">Clusters (2022)</h2>
          <p className="text-3xl font-bold mt-2 text-gray-800">{clusterCount}</p>
          <Link href="/clusters" className="text-sm text-blue-600 hover:underline mt-2 inline-block">View Distribution &rarr;</Link>
        </div>
        <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-100">
          <h2 className="font-medium text-gray-500 text-sm uppercase tracking-wider">Active Anomalies</h2>
          <p className="text-3xl font-bold mt-2 text-red-600">{totalAnomalies}</p>
          <Link href="/anomalies" className="text-sm text-blue-600 hover:underline mt-2 inline-block">Review Alerts &rarr;</Link>
        </div>
      </div>

      {/* 2. Quick Navigation */}
      <div>
        <h2 className="text-xl font-bold mb-4 text-gray-800">Quick Navigation</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickLinks.map((link) => (
            <Link key={link.href} href={link.href} className={`p-4 rounded-lg transition-colors ${link.color}`}>
              <h3 className="font-semibold text-gray-800">{link.title}</h3>
              <p className="text-sm text-gray-600 mt-1">{link.desc}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}