export default function TrendChips({ trends = [], selected = [], onToggle }) {
  if (!trends || trends.length === 0) {
    return (
      <div className="text-sm text-gray-500">
        No trends found. Try again later or type your own keyword below.
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {trends.map((t) => {
        const isOn = selected.includes(t);
        return (
          <button
            key={t}
            type="button"
            onClick={() => onToggle(t)}
            className={
              (isOn
                ? "bg-indigo-600 text-white border-indigo-600"
                : "bg-white text-gray-800 border-gray-300 hover:border-gray-400") +
              " px-3 py-1 rounded-full text-xs border transition"
            }
            title={t}
          >
            {t}
          </button>
        );
      })}
    </div>
  );
}
