export default function ChartCard({ title, subtitle, children }) {
  return (
    <div className="card">
      <div className="card-pad">
        <div className="font-semibold">{title}</div>
        {subtitle ? <div className="text-xs text-gray-500 mt-0.5">{subtitle}</div> : null}
      </div>
      <div className="px-2 pb-4">{children}</div>
    </div>
  );
}
