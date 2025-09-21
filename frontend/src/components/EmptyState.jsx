export default function EmptyState({ title, subtitle, action }) {
  return (
    <div className="card card-pad text-center">
      <div className="text-lg font-semibold">{title}</div>
      <div className="text-sm text-gray-500 mt-1">{subtitle}</div>
      {action}
    </div>
  );
}
