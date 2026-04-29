'use client';
import { useCountries } from '@/lib/hooks/useCountries';
import { useClusters } from '@/lib/hooks/useClusters';
import { CardSkeleton } from '@/components/ui/Skeletons';

export default function DashboardPage() {
  const { data: countries, isLoading: l1 } = useCountries();
  const { data: clusters, isLoading: l2 } = useClusters(2022);

  if (l1 || l2) return <div className="grid grid-cols-3 gap-4"><CardSkeleton /><CardSkeleton /><CardSkeleton /></div>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-4 rounded shadow">
          <h2 className="font-semibold text-gray-600">Total Countries</h2>
          <p className="text-3xl font-bold">{countries?.length || 0}</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <h2 className="font-semibold text-gray-600">Clusters (2022)</h2>
          <p className="text-3xl font-bold">{clusters ? new Set(clusters.map(c => c.cluster_id)).size : 0}</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <h2 className="font-semibold text-gray-600">Anomalies</h2>
          <p className="text-3xl font-bold">-</p>
        </div>
      </div>
    </div>
  );
}