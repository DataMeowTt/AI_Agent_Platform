'use client';
import { useParams } from 'next/navigation';
import { useCountryAnalytics } from '@/lib/hooks/useCountries';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine } from 'recharts';
import { CardSkeleton } from '@/components/ui/Skeletons';
import Tabs from '@/components/ui/Tabs';
import { CountryAnalyticsRow } from '@/lib/types';

const prepareChartData = (data: CountryAnalyticsRow[], keys: string[]) => {
  return data
    .filter(d => keys.some(k => d[k as keyof CountryAnalyticsRow] != null))
    .map(d => {
      const point: Record<string, number | undefined> = { year: d.year };
      keys.forEach(k => {
        const val = d[k as keyof CountryAnalyticsRow];
        point[k] = val != null ? Number(val) : undefined;
      });
      return point;
    });
};

export default function CountryDetailPage() {
  const { code } = useParams();
  const { data, isLoading, isError, error } = useCountryAnalytics(code as string);

  if (isLoading) return <div className="p-6"><CardSkeleton /></div>;
  if (isError) return <div className="p-6 bg-red-50 text-red-700 rounded border border-red-200">Lỗi tải dữ liệu: {error?.message}</div>;
  if (!data || data.length === 0) return <div className="text-center py-12 text-gray-500 bg-white rounded shadow">Không có dữ liệu cho quốc gia này.</div>;

  const tabs = [
    { id: 'growth', label: 'Tăng trưởng & Xu hướng', content: <GrowthTab data={data} /> },
    { id: 'fiscal', label: 'Tài khóa & Tiền tệ', content: <FiscalMonetaryTab data={data} /> },
    { id: 'social', label: 'Xã hội', content: <SocialTab data={data} /> },
    { id: 'risk', label: 'Rủi ro & Bất thường', content: <RiskTab data={data} /> },
  ];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-800">Phân tích: {data[0]?.country_code || code}</h1>
      <Tabs tabs={tabs} />
    </div>
  );
}

function GrowthTab({ data }: { data: CountryAnalyticsRow[] }) {
  const chartData = data.map(d => ({
    year: d.year,
    actual: d.actual_growth,
    trend: d.trend_growth,
    isAnomaly: d.anomaly_growth != null && d.anomaly_growth >= 0.75,
  }));

  if (!data.some(d => d.actual_growth != null)) return <EmptyState indicator="Tăng trưởng GDP thực tế" />;

  return (
    <div className="bg-white p-4 rounded shadow">
      <h3 className="font-semibold mb-4 text-gray-700">Diễn biến Tăng trưởng GDP (%)</h3>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis />
          <Tooltip formatter={(v: any) => v != null ? `${Number(v).toFixed(2)}%` : 'N/A'} />
          <Legend />
          <Line type="monotone" dataKey="actual" stroke="#3b82f6" name="Thực tế" dot={{ r: 3 }} />
          <Line type="monotone" dataKey="trend" stroke="#10b981" strokeDasharray="5 5" name="Xu hướng" dot={false} />
          {chartData.filter(d => d.isAnomaly).map((p, i) => (
            <ReferenceLine key={i} x={p.year} stroke="#ef4444" strokeDasharray="3 3" label="Bất thường" />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function FiscalMonetaryTab({ data }: { data: CountryAnalyticsRow[] }) {
  if (!data.some(d => d.actual_debt != null || d.actual_inflation != null)) return <EmptyState indicator="Nợ công & Lạm phát" />;
  
  const chartData = prepareChartData(data, ['actual_debt', 'actual_inflation']);
  return (
    <div className="bg-white p-4 rounded shadow">
      <h3 className="font-semibold mb-4 text-gray-700">Nợ công (%GDP) & Lạm phát CPI (%)</h3>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis />
          <Tooltip formatter={(v: any) => v != null ? `${Number(v).toFixed(2)}%` : 'N/A'} />
          <Legend />
          <Line type="monotone" dataKey="actual_debt" stroke="#f59e0b" name="Nợ công" dot={{ r: 3 }} />
          <Line type="monotone" dataKey="actual_inflation" stroke="#8b5cf6" name="Lạm phát CPI" dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function SocialTab({ data }: { data: CountryAnalyticsRow[] }) {
  if (!data.some(d => d.actual_poverty != null || d.actual_unemployment != null)) return <EmptyState indicator="Nghèo đói & Thất nghiệp" />;

  const chartData = prepareChartData(data, ['actual_poverty', 'actual_unemployment']);
  return (
    <div className="bg-white p-4 rounded shadow">
      <h3 className="font-semibold mb-4 text-gray-700">Tỷ lệ Nghèo (%) & Thất nghiệp (%)</h3>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis />
          <Tooltip formatter={(v: any) => v != null ? `${Number(v).toFixed(2)}%` : 'N/A'} />
          <Legend />
          <Line type="monotone" dataKey="actual_poverty" stroke="#ef4444" name="Nghèo đói" dot={{ r: 3 }} />
          <Line type="monotone" dataKey="actual_unemployment" stroke="#06b6d4" name="Thất nghiệp" dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function RiskTab({ data }: { data: CountryAnalyticsRow[] }) {
  if (!data.some(d => d.actual_reer_deviation != null)) return <EmptyState indicator="Lệch giá REER & Rủi ro" />;

  const chartData = data.map(d => ({
    year: d.year,
    reer: d.actual_reer_deviation,
    isAnomaly: d.anomaly_reer_deviation != null && d.anomaly_reer_deviation >= 0.75,
  }));

  return (
    <div className="bg-white p-4 rounded shadow">
      <h3 className="font-semibold mb-4 text-gray-700">Lệch giá REER (%) & Cảnh báo Rủi ro</h3>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis />
          <Tooltip formatter={(v: any) => v != null ? `${Number(v).toFixed(2)}%` : 'N/A'} />
          <Legend />
          <Line type="monotone" dataKey="reer" stroke="#dc2626" name="REER Deviation" dot={{ r: 3 }} />
          {chartData.filter(d => d.isAnomaly).map((p, i) => (
            <ReferenceLine key={i} x={p.year} stroke="#dc2626" strokeDasharray="3 3" label="Rủi ro cao" />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function EmptyState({ indicator }: { indicator: string }) {
  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
      <p className="text-yellow-800 font-medium">Chưa có dữ liệu cho chỉ số: <span className="font-bold">{indicator}</span></p>
      <p className="text-sm text-yellow-600 mt-2">Dữ liệu sẽ hiển thị sau khi pipeline analytics hoàn tất xử lý.</p>
    </div>
  );
}