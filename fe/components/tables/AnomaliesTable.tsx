'use client';
import { formatNumber } from '@/lib/utils/format';
import AnomalyBadge from '@/components/ui/Badge';
import { AnomalyItem } from '@/lib/types';

interface Props {
  data: AnomalyItem[];
}

export default function AnomaliesTable({ data }: Props) {
  if (!data?.length) return <div className="text-center py-6 text-gray-500 bg-white rounded shadow">Không tìm thấy bất thường nào phù hợp.</div>;

  return (
    <div className="bg-white rounded shadow overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quốc gia</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Năm</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Chỉ số</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Giá trị thực</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Điểm bất thường</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((item, idx) => (
            <tr key={`${item.country_code}-${item.year}-${idx}`} className="hover:bg-gray-50 transition-colors">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.country_name}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.year}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.indicator}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatNumber(item.actual_value)}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm"><AnomalyBadge score={item.anomaly_score} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}