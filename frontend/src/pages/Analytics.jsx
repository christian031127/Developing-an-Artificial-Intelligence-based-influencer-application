import { useEffect, useState } from "react";
import { api } from "../lib/api";
import ChartCard from "../components/ChartCard";
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts";

const COLORS = ["#6366F1","#22C55E","#F59E0B","#EF4444","#06B6D4","#A855F7"];

export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      setData(await api.getAnalytics());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) return <div className="card card-pad">Loading analytics…</div>;
  if (!data) return <div className="card card-pad">No analytics available.</div>;

  const cat = data.byCategory || [];
  const stat = data.byStatus || [];
  const perDay = data.perDay || [];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Analytics</h1>
          <p className="text-sm text-gray-500">Total drafts: {data.total}</p>
        </div>
        <button className="btn btn-sm btn-ghost" onClick={load}>Refresh</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* By Category – Pie */}
        <ChartCard title="Drafts by category" subtitle="workout / meal / lifestyle">
          <div style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={cat} dataKey="count" nameKey="category" innerRadius={40} outerRadius={80} paddingAngle={3}>
                  {cat.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        {/* By Status – Pie (donut) */}
        <ChartCard title="Drafts by status" subtitle="draft vs approved">
          <div style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={stat} dataKey="count" nameKey="status" innerRadius={55} outerRadius={85} paddingAngle={2}>
                  {stat.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
      </div>

      {/* Per day – Bar */}
      <ChartCard title="Drafts per day (last 7 days)">
        <div style={{ width: "100%", height: 320 }}>
          <ResponsiveContainer>
            <BarChart data={perDay}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count">
                {perDay.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </ChartCard>
    </div>
  );
}
