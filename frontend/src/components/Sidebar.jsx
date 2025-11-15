export default function Sidebar({ current = "dashboard", onNavigate = () => {} }) {
  const Item = ({ id, label, badge }) => (
    <button
      onClick={() => onNavigate(id)}
      className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium
        ${current === id ? "bg-gray-100" : "hover:bg-gray-50"}`}
    >
      <span>{label}</span>
      {badge ? <span className="text-xs text-gray-500">{badge}</span> : null}
    </button>
  );

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b">
        <div className="text-lg font-bold">AI Influencer</div>
        <div className="text-xs text-gray-500">Studio</div>
      </div>

      <nav className="p-3 space-y-1">
        <Item id="dashboard" label="Dashboard" badge="IG" />
        <Item id="feed" label="Feed" badge="Simulate" />
        <Item id="analytics" label="Analytics" badge="Overall" />
        <Item id="personas" label="Personas" />
      </nav>

      <div className="mt-auto p-4 text-xs text-gray-500">
        © {new Date().getFullYear()} Spertli Krisztián
      </div>
    </div>
  );
}
