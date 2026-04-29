'use client';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface Props {
  data: Record<string, { year: number; value: number | null }[]>;
  indicatorName: string;
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088fe'];

export default function CompareLineChart({ data, indicatorName }: Props) {
  if (!data || Object.keys(data).length === 0) {
    return <div className="h-64 flex items-center justify-center bg-gray-50 rounded text-gray-500">Chưa có dữ liệu để hiển thị</div>;
  }

  const allYears = new Set<number>();
  Object.values(data).forEach(countryData => {
    countryData.forEach(point => allYears.add(point.year));
  });
  const years = Array.from(allYears).sort();

  const chartData = years.map(year => {
    const point: Record<string, number | null | undefined> = { year };
    Object.entries(data).forEach(([countryCode, countryData]) => {
      const found = countryData.find(d => d.year === year);
      point[countryCode] = found?.value ?? null;
    });
    return point;
  });

  return (
    <div>
      <h3 className="text-sm font-medium text-gray-600 mb-2">{indicatorName}</h3>
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip formatter={(value: any) => `${value != null ? Number(value).toFixed(2) : 'N/A'}`} />
          <Legend />
          {Object.keys(data).map((countryCode, idx) => (
            <Line
              key={countryCode}
              type="monotone"
              dataKey={countryCode}
              stroke={COLORS[idx % COLORS.length]}
              name={countryCode}
              dot={{ r: 3 }}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}