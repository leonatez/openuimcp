"use client";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar,
} from "recharts";

export interface SalesChartData {
  title: string;
  type: "line" | "bar";
  x_key: string;
  y_key: string;
  y_label: string;
  rows: Record<string, number | string>[];
}

const fmt = (v: number) =>
  v >= 1_000_000
    ? `${(v / 1_000_000).toFixed(1)}M`
    : v >= 1_000
    ? `${(v / 1_000).toFixed(0)}K`
    : String(v);

export default function SalesChart({ data }: { data: SalesChartData }) {
  const ChartComponent = data.type === "bar" ? BarChart : LineChart;
  const DataMark =
    data.type === "bar" ? (
      <Bar dataKey={data.y_key} fill="#6366f1" radius={[3, 3, 0, 0]} />
    ) : (
      <Line
        type="monotone"
        dataKey={data.y_key}
        stroke="#6366f1"
        dot={false}
        strokeWidth={2}
      />
    );

  return (
    <div className="flex flex-col gap-2">
      <p className="text-xs font-semibold text-neutral-300">{data.title}</p>
      <ResponsiveContainer width="100%" height={280}>
        <ChartComponent data={data.rows} margin={{ top: 4, right: 16, left: 8, bottom: 40 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
          <XAxis
            dataKey={data.x_key}
            tick={{ fill: "#737373", fontSize: 10 }}
            angle={-45}
            textAnchor="end"
            interval={3}
          />
          <YAxis
            tick={{ fill: "#737373", fontSize: 10 }}
            tickFormatter={fmt}
            label={{
              value: data.y_label,
              angle: -90,
              position: "insideLeft",
              fill: "#525252",
              fontSize: 10,
            }}
          />
          <Tooltip
            contentStyle={{ background: "#171717", border: "1px solid #404040", fontSize: 11 }}
            formatter={(v: number) => [fmt(v), data.y_label]}
          />
          <Legend wrapperStyle={{ fontSize: 11, color: "#737373" }} />
          {DataMark}
        </ChartComponent>
      </ResponsiveContainer>
    </div>
  );
}
