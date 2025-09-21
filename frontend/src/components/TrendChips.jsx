export default function TrendChips({ trends = [], selected = [], onToggle }) {
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
              "chip " + (isOn ? "chip-on" : "chip-off")
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
