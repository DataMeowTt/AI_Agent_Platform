'use client';

import { useCountries } from '@/lib/hooks/useCountries';
import { useClusters } from '@/lib/hooks/useClusters';

export default function DashboardPage() {
  const { data: countries, isLoading: loadingCountries } = useCountries();
  const { data: clusters, isLoading: loadingClusters } = useClusters(2022);

  if (loadingCountries || loadingClusters) return <div>Loading dashboard...</div>;

  const totalCountries = countries?.length || 0;
  const clusterCount = clusters ? new Set(clusters.map((c: any) => c.cluster_id)).size : 0;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-4 rounded shadow">
          <h2 className="font-semibold text-gray-600">Total Countries</h2>
          <p className="text-3xl font-bold">{totalCountries}</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <h2 className="font-semibold text-gray-600">Clusters (2022)</h2>
          <p className="text-3xl font-bold">{clusterCount}</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <h2 className="font-semibold text-gray-600">Anomalies</h2>
          <p className="text-3xl font-bold">-</p>
        </div>
      </div>
    </div>
  );
}