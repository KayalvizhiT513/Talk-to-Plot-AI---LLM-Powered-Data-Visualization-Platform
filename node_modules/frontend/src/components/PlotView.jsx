import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function PlotView({ plot }) {
  const { name, data, config } = plot;

  if (!data?.length) {
    return (
      <div className="plot-card">
        <h2>{name}</h2>
        <div className="plot-placeholder">No data available.</div>
      </div>
    );
  }

  const xKey = config.xKey;
  const yKey = config.yKey;

  const chartProps = (
    <ResponsiveContainer width="100%" height={320}>
      {config.type === "bar" ? (
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey={xKey} stroke="#cbd5f5" />
          <YAxis stroke="#cbd5f5" allowDecimals={false} />
          <Tooltip labelStyle={{ color: "#0f172a" }} />
          <Legend />
          <Bar dataKey={yKey} fill="#6366f1" radius={[6, 6, 0, 0]} />
        </BarChart>
      ) : config.type === "area" ? (
        <AreaChart data={data}>
          <defs>
            <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey={xKey} stroke="#cbd5f5" />
          <YAxis stroke="#cbd5f5" allowDecimals={false} />
          <Tooltip labelStyle={{ color: "#0f172a" }} />
          <Legend />
          <Area type="monotone" dataKey={yKey} stroke="#8b5cf6" fill="url(#areaFill)" />
        </AreaChart>
      ) : (
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey={xKey} stroke="#cbd5f5" />
          <YAxis stroke="#cbd5f5" allowDecimals={false} />
          <Tooltip labelStyle={{ color: "#0f172a" }} />
          <Legend />
          <Line type="monotone" dataKey={yKey} stroke="#22d3ee" strokeWidth={2} dot={false} />
        </LineChart>
      )}
    </ResponsiveContainer>
  );

  return (
    <div className="plot-card">
      <h2>{name}</h2>
      {chartProps}
    </div>
  );
}
