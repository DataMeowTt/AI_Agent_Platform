'use client';
import { useUrlState } from '@/lib/hooks/useUrlState';
import { useClusters } from '@/lib/hooks/useClusters';
import { useDataState } from '@/lib/hooks/useDataState';
import dynamic from 'next/dynamic';
import { ChartSkeleton } from '@/components/ui/Skeletons';
import { useMemo } from 'react';

const ClusterPieChart = dynamic(() => import('@/components/charts/PieChart'), {
  ssr: false,
  loading: () => <ChartSkeleton />
});

export default function ClustersPage() {
  const [year, setYear] = useUrlState<number>('year', 2022);
  const { data: clusters, isLoading, isEmpty, isError, error } = useDataState(useClusters(year));

  if (isError) return <div className="p-4 bg-red-50 text-red-700 rounded">Lỗi: {error?.message}</div>;

  const { clusterCounts, grouped } = useMemo(() => {
    const counts: Record<number, number> = {};
    const grp: Record<number, string[]> = {};
    if (!isEmpty && clusters) {
      clusters.forEach(item => {
        const id = item.cluster_id;
        counts[id] = (counts[id] || 0) + 1;
        if (!grp[id]) grp[id] = [];
        grp[id].push(item.country_code);
      });
    }
    return { clusterCounts: counts, grouped: grp };
  }, [clusters, isEmpty]);

  const pieData = Object.entries(clusterCounts).map(([id, count]) => ({
    cluster_id: parseInt(id),
    count,
  }));

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Clusters</h1>
      <div className="mb-4 flex items-center gap-2">
        <label className="font-medium">Năm:</label>
        <select value={year} onChange={(e) => setYear(parseInt(e.target.value))} className="border rounded p-2 bg-white">
          {[2000, 2010, 2020, 2022].map(y => <option key={y} value={y}>{y}</option>)}
        </select>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-4 rounded shadow min-h-[300px]">
          <h2 className="text-lg font-semibold mb-2">Phân bố</h2>
          {isLoading ? <ChartSkeleton /> : isEmpty ? (
            <div className="flex items-center justify-center h-48 text-gray-500">Chưa có dữ liệu cluster.</div>
          ) : <ClusterPieChart data={pieData} groupedCountries={grouped} />}
        </div>
        <div className="bg-white p-4 rounded shadow max-h-[450px] overflow-y-auto">
          <h2 className="text-lg font-semibold mb-2">Quốc gia theo Cluster</h2>
          {Object.keys(grouped).sort().map(id => (
            <div key={id} className="mb-4 last:mb-0">
              <h3 className="font-medium text-blue-600 mb-2">Cluster {id}</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {grouped[parseInt(id)].map(code => (
                  <div key={code} className="bg-gray-50 border border-gray-200 rounded px-3 py-2 text-sm hover:bg-gray-100 transition-colors cursor-default">
                    <span className="font-medium text-gray-800">{code}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}